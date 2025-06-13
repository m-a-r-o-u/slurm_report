import argparse
import sys
from datetime import datetime
import calendar
from .report import generate_report


def parse_args():
    parser = argparse.ArgumentParser(description="Generate SLURM usage report.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--user", help="Single user ID")
    group.add_argument("--users", help="Comma-separated user IDs")
    group.add_argument("--userfile", help="File with one user ID per line")
    parser.add_argument(
        "--start",
        required=True,
        help="Start date (YYYY-MM or YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end",
        help="End date (YYYY-MM or YYYY-MM-DD)"
    )
    parser.add_argument(
        "--partitions",
        action="store_true",
        help="Include per-partition metrics in the output",
    )
    return parser.parse_args()


def parse_flexible_date(date_str):
    """Return (datetime, has_day) from a YYYY-MM or YYYY-MM-DD string."""
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt, fmt == "%Y-%m-%d"
        except ValueError:
            continue
    raise ValueError


def main():
    args = parse_args()

    try:
        start, start_has_day = parse_flexible_date(args.start)
    except ValueError:
        print("Error: --start must be YYYY-MM or YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    if args.end:
        try:
            end, end_has_day = parse_flexible_date(args.end)
        except ValueError:
            print("Error: --end must be YYYY-MM or YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

        if not end_has_day:
            last_day = calendar.monthrange(end.year, end.month)[1]
            end = end.replace(day=last_day)
    else:
        if start_has_day:
            end = datetime.now()
        else:
            last_day = calendar.monthrange(start.year, start.month)[1]
            end = start.replace(day=last_day)

    if start > end:
        print("Error: Start date must be earlier than or equal to end date.", file=sys.stderr)
        sys.exit(1)

    if args.user:
        user_ids = [args.user]
    elif args.users:
        user_ids = [u.strip() for u in args.users.split(",") if u.strip()]
    else:
        with open(args.userfile) as f:
            user_ids = [line.strip() for line in f if line.strip()]

    try:
        report_df = generate_report(user_ids, start, end, include_partitions=args.partitions)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    interval = f"Reporting period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
    explanation = (
        f"{interval}\n"
        "CPU_Hours = ElapsedHours * AllocCPUS\n"
        "GPU_Hours = ElapsedHours * AllocGPUs\n"
        "RAM_Hours(GB-h) = ElapsedHours * AllocRAM_GB"
    )

    if sys.stdout.isatty():
        from tabulate import tabulate
        print(explanation)
        print(tabulate(report_df, headers="keys", tablefmt="grid"))
    else:
        print(explanation)
        print(report_df.to_csv(index=False))
