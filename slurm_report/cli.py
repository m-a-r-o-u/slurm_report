import argparse
import sys
from datetime import datetime
from .report import generate_report


def parse_args():
    parser = argparse.ArgumentParser(description="Generate SLURM usage report.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--user", help="Single user ID")
    group.add_argument("--users", help="Comma-separated user IDs")
    group.add_argument("--userfile", help="File with one user ID per line")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        start = datetime.strptime(args.start, "%Y-%m-%d")
        end = datetime.strptime(args.end, "%Y-%m-%d")
    except ValueError:
        print("Error: Dates must be in YYYY-MM-DD format.", file=sys.stderr)
        sys.exit(1)

    if start > end:
        print("Error: Start date must be earlier than or equal to end date.", file=sys.stderr)
        sys.exit(1)

    if (end - start).days > 31:
        print("Error: Date range must be within a month.", file=sys.stderr)
        sys.exit(1)

    if args.user:
        user_ids = [args.user]
    elif args.users:
        user_ids = [u.strip() for u in args.users.split(",") if u.strip()]
    else:
        with open(args.userfile) as f:
            user_ids = [line.strip() for line in f if line.strip()]

    try:
        report_df = generate_report(user_ids, start, end)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    explanation = (
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
