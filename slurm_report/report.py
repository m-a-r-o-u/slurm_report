import pandas as pd
from .utils import fetch_slurm_jobs


def compute_metrics(df):
    df["CPU_Hours"] = df["ElapsedHours"] * df["AllocCPUS"]
    df["GPU_Hours"] = df["ElapsedHours"] * df["AllocGPUs"]
    df["RAM_Hours"] = df["ElapsedHours"] * df["AllocRAM_GB"]
    return df


CPU_POWER_W = 150
GPU_POWER_W = 400
PRICE_PER_KWH = 0.40


def generate_report(user_ids, start, end, include_partitions=False, include_cost=False):
    """Return a DataFrame summarising usage per user and totals.

    Parameters
    ----------
    user_ids : list[str]
        User IDs to include in the report.
    start, end : datetime
        Date range for the report.
    include_partitions : bool, optional
        If True, include per-partition metrics in the returned DataFrame.
    include_cost : bool, optional
        If True, add a column with total energy usage and cost.
    """
    all_jobs = []
    for user in user_ids:
        jobs = fetch_slurm_jobs(user, start, end)
        all_jobs.append(jobs)

    if not all_jobs:
        return pd.DataFrame(columns=["UserID"])

    df = pd.concat(all_jobs, ignore_index=True)

    # Convert elapsed to hours
    df["ElapsedHours"] = df["Elapsed"].dt.total_seconds() / 3600

    df = compute_metrics(df)

    # Duplicate rows with a UserID="All" to compute aggregated totals
    df_all = pd.concat([df, df.assign(UserID="All")])

    totals = df_all.groupby("UserID")[["CPU_Hours", "GPU_Hours", "RAM_Hours"]].sum()
    if include_cost:
        totals["Energy_Wh"] = (
            totals["CPU_Hours"] * CPU_POWER_W + totals["GPU_Hours"] * GPU_POWER_W
        )
        totals["Cost_EUR"] = totals["Energy_Wh"] / 1000 * PRICE_PER_KWH

    if include_partitions:
        part = df_all.pivot_table(
            index="UserID",
            columns="Partition",
            values=["CPU_Hours", "GPU_Hours", "RAM_Hours"],
            aggfunc="sum",
            fill_value=0,
        )

        # Sort partitions and ensure metric order
        part = part.reindex(["CPU_Hours", "GPU_Hours", "RAM_Hours"], level=0)
        part = part.sort_index(axis=1, level=1)

        report_df = pd.concat([totals, part], axis=1).reset_index()

        # Flatten column MultiIndex: (Metric, Partition) -> Metric\nPartition
        keep_cols = ["UserID"]
        new_names = ["UserID"]
        for col in report_df.columns[1:]:
            if isinstance(col, tuple):
                metric, part_name = col
                if part_name:
                    keep_cols.append(col)
                    new_names.append(f"{metric}\n{part_name}")
            else:
                keep_cols.append(col)
                new_names.append(col)

        report_df = report_df[keep_cols]
        report_df.columns = new_names
    else:
        report_df = totals.reset_index()

    # Add unit to RAM hours column names
    report_df.rename(columns=lambda c: c.replace("RAM_Hours", "RAM_Hours(GB-h)"), inplace=True)

    # Order rows: aggregate "All" row first, then individual users
    unique_users = sorted(df["UserID"].unique())
    order = ["All"] + unique_users
    report_df = report_df.set_index("UserID").loc[order].reset_index()

    # Round all numeric columns to one decimal place for cleaner output
    numeric_cols = report_df.select_dtypes(include="number").columns
    report_df[numeric_cols] = report_df[numeric_cols].round(1)

    if include_cost:
        energy_values = report_df["Energy_Wh"]
        cost_values = report_df["Cost_EUR"]
        report_df["Energy_Wh"] = [
            f"{e:.1f} ({c:.2f}€)" for e, c in zip(energy_values, cost_values)
        ]
        report_df.drop(columns=["Cost_EUR"], inplace=True)
        cols = list(report_df.columns)
        ram_idx = cols.index("RAM_Hours(GB-h)")
        energy_idx = cols.index("Energy_Wh")
        cols.insert(ram_idx + 1, cols.pop(energy_idx))
        report_df = report_df[cols]

    return report_df
