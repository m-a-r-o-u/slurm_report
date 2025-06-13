# slurm_report

`slurm_report` is a command line tool that summarises usage from a SLURM
accounting database. It runs the `sacct` command for one or more users and
produces a table of CPU, GPU and memory consumption. Job step entries such as
`JOBID.batch` or `JOBID.0` are skipped so each job is counted only once.

## Features

- Accept a single user (`--user`), comma separated list (`--users`) or a file
  of user names (`--userfile`).
- Start and end dates can be provided as `YYYY-MM` or `YYYY-MM-DD`.
- Calculates `CPU_Hours`, `GPU_Hours` and `RAM_Hours(GB-h)` for the selected
  users and time range.
- Optional per-partition metrics with `--partitions`.
- Optional energy and cost estimate with `--cost` (150 W per CPU hour,
  400 W per GPU hour at 0.40 €/kWh).
- Prints a nicely formatted table to the terminal or CSV when redirected.

## Installation

```bash
pip install -e .
```

The package requires Python >=3.7 with `pandas` and `tabulate` installed and
must be run on a system where the `sacct` command is available.

## Usage

```bash
slurm_report --user alice --start 2025-06        # whole month of June 2025
slurm_report --user alice --start 2025-06-01     # from 2025-06-01 until today
slurm_report --users alice,bob --start 2025-06-01 --end 2025-06-13
slurm_report --userfile users.txt --start 2025-06-01 --end 2025-06-13 > output.csv
slurm_report --user alice --start 2025-06-01 --end 2025-06-13 --partitions
slurm_report --user alice --start 2025-06-01 --cost   # include energy usage and cost
```

If `--end` is omitted and a day is present in `--start`, the report covers the
period up to today. Providing only `YYYY-MM` for `--start` generates a report
for the entire month.

## Dependencies

- Python >=3.7
- pandas
- tabulate
- access to a SLURM installation with the `sacct` command

## License

MIT
