import pandas as pd
from .utils import fetch_slurm_jobs


def compute_metrics(df):
    df["CPU_Hours"] = df["ElapsedHours"] * df["AllocCPUS"]
    df["GPU_Hours"] = df["ElapsedHours"] * df["AllocGPUs"]
    df["RAM_Hours"] = df["ElapsedHours"] * df["AllocRAM_GB"]
    return df


def generate_report(user_ids, start, end):
    all_jobs = []
    for user in user_ids:
        jobs = fetch_slurm_jobs(user, start, end)
        all_jobs.append(jobs)
    df = pd.concat(all_jobs, ignore_index=True)

    # Convert elapsed to hours
    df["ElapsedHours"] = df["Elapsed"].dt.total_seconds() / 3600

    df = compute_metrics(df)

    # Aggregated totals across all partitions
    agg = (
        df.groupby("UserID")[["CPU_Hours", "GPU_Hours", "RAM_Hours"]]
        .sum()
        .reset_index()
    )
    agg["Partition"] = "Total"

    # Breakdown per partition
    part = (
        df.groupby(["UserID", "Partition"])[["CPU_Hours", "GPU_Hours", "RAM_Hours"]]
        .sum()
        .reset_index()
    )

    report_df = pd.concat([agg, part], ignore_index=True)
    return report_df
