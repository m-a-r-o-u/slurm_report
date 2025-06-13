import subprocess
import pandas as pd


def fetch_slurm_jobs(user, start, end):
    """
    Query SLURM accounting via sacct and return a DataFrame of jobs for the given user
    between start and end (inclusive).
    """
    start_str = start.strftime("%Y-%m-%d")
    end_str = (end + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    cmd = [
        "sacct", "-u", user,
        "--starttime", start_str,
        "--endtime", end_str,
        "--format=User,Partition,Elapsed,AllocCPUS,AllocTRES",
        "--parsable2", "--noheader"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else ""
        raise RuntimeError(f"SLURM query failed (exit {e.returncode}): {stderr}")

    lines = [l for l in result.stdout.splitlines() if l]
    rows = []
    for line in lines:
        user_id, partition, elapsed, alloc_cpus, alloc_tres = line.split("|")
        elapsed_hours = parse_elapsed(elapsed)
        gpus = parse_gres(alloc_tres)
        ram = parse_ram(alloc_tres)
        rows.append({
            "UserID": user_id,
            "Partition": partition,
            "Elapsed": pd.Timedelta(hours=elapsed_hours),
            "AllocCPUS": int(alloc_cpus),
            "AllocGPUs": gpus,
            "AllocRAM_GB": ram,
        })
    return pd.DataFrame(rows)


def parse_elapsed(elapsed_str):
    parts = elapsed_str.split("-")
    if len(parts) == 2:
        days, rest = parts
        h, m, s = rest.split(":")
        total = int(days) * 24 + int(h) + int(m) / 60 + int(s) / 3600
    else:
        h, m, s = elapsed_str.split(":")
        total = int(h) + int(m) / 60 + int(s) / 3600
    return total


def parse_gres(tres_str):
    """
    Extract GPU count from AllocTRES string, e.g. 'cpu=30,gres/gpu=1,mem=200G,...'
    """
    for part in tres_str.split(","):
        if part.startswith("gres/gpu"):
            _, val = part.split("=", 1)
            return int(val)
    return 0


def parse_ram(tres_str):
    """
    Extract memory in GB from AllocTRES string (mem=200G or mem=102400M).
    """
    for part in tres_str.split(","):
        if part.startswith("mem"):
            _, val = part.split("=", 1)
            if val.lower().endswith("g"):
                return float(val[:-1])
            if val.lower().endswith("m"):
                return float(val[:-1]) / 1024
    return 0
