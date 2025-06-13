import pandas as pd
from .utils import fetch_slurm_jobs


def compute_metrics(df):
    df["CPU_Hours"] = df["ElapsedHours"] * df["AllocCPUS"]
    df["GPU_Hours"] = df["ElapsedHours"] * df["AllocGPUs"]
    df["RAM_Hours"] = df["ElapsedHours"] * df["AllocRAM_GB"]
    return df


def generate_report(user_ids, start, end):
    """Return a DataFrame summarising usage per user and totals."""
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

    part = df_all.pivot_table(
        index="UserID",
        columns="Partition",
        values=["CPU_Hours", "GPU_Hours", "RAM_Hours"],
        aggfunc="sum",
        fill_value=0,
    )

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

    # Add unit to RAM hours column names
    report_df.rename(columns=lambda c: c.replace("RAM_Hours", "RAM_Hours(GB-h)"), inplace=True)

    # Order rows: aggregate "All" row first, then individual users
    unique_users = sorted(df["UserID"].unique())
    order = ["All"] + unique_users
    report_df = report_df.set_index("UserID").loc[order].reset_index()

    return report_df
