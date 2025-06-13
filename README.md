Directory Structure

slurm_report/
├── pyproject.toml
├── README.md
└── slurm_report/
    ├── __init__.py
    ├── cli.py
    ├── report.py
    └── utils.py

pyproject.toml

[build-system]
requires = ["setuptools>=40.8.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "slurm_report"
version = "0.1.0"
description = "A CLI tool to generate SLURM usage reports"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.7"
dependencies = [
    "pandas",
    "tabulate",
]

[project.scripts]
slurm_report = "slurm_report.cli:main"

README.md

# slurm_report

A command-line tool to generate SLURM usage reports.

Job step entries such as `JOBID.batch` or `JOBID.0` are automatically ignored so
each job is counted only once.

## Installation

```bash
pip install -e .
```

Usage
```bash
slurm_report --user alice --start 2025-06-01 --end 2025-06-13
slurm_report --users alice,bob --start 2025-06-01 --end 2025-06-13
slurm_report --userfile users.txt --start 2025-06-01 --end 2025-06-13 > output.csv
slurm_report --user alice --start 2025-06-01 --end 2025-06-13 --partitions
```

Dependencies

Python >=3.7
pandas
tabulate

License
MIT
