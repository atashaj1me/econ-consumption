# ECON 312 - Economics of Consumption Workspace
This is the workspace for the course ECON 312 - Economics of Consumption at Fulbright University Vietnam, instructed by Dr. Xavier M. G. Bautista. It holds the lab sessions, problem sets, papers, presentations, and other materials for the quantitative analysis in the course.

Owner: Nguyen Chi Thang, Fulbright University Vietnam

Contact me: thang.nguyen.240184@student.fulbright.edu.vn

## Layout
```
econ-consumption/
├── labs/                 # lab sessions, one folder per lab
├── problem-sets/         # problem sets, one folder per set
├── papers/               # paper and proposal writing (LaTeX)
├── presentations/        # slide decks (LaTeX Beamer)
├── course-materials/     # files provided by Dr. Xavier (read-only)
├── pipelines/            # scripts that build shared datasets in data/
├── templates/            # starter README for new projects
├── data/                 # shared datasets, local only (not on GitHub)
├── CLAUDE.md             # instructions for Claude Code / Claude Science
├── environment.yml       # conda environment (or requirements.txt for pip)
└── .workspace-root       # marker used by notebooks to find this folder
```

## Projects
| Type | Project | Contents |
| ---- | ------- | -------- |
| Lab | [Lab 1](labs/lab1) | Estimating the EIS (WDI); life-cycle profiles (SCF 2022) |
| Problem set | [Problem Set 1](problem-sets/ps1) | Income, wealth and expenditure profiles by age (SCF, PSID) |
| Paper | [Shaky Houses](papers/shaky-houses) | Research proposal: housing choice, house prices and aggregate fluctuations |
| Presentation | [2026 Presentations](presentations/2026-presentations) | Beamer talk |

To start a new project, create a folder under the matching type and copy [templates/project/README.md](templates/project/README.md) into it.

## Data (local only)
`data/` is excluded through [.gitignore](.gitignore). To run the notebooks, download the datasets into:

```
data/
├── intrvw24/                    # BLS Consumer Expenditure Survey, Interview 2024 (CSV)
├── psid/                        # PSID extracts (.txt + .sas); built by pipelines/psid
├── survey_of_consumer_finance/  # SCF summary extracts: SCFP2016/2019/2022.csv, scf2022.csv
└── world_dev_index/             # World Bank WDI (cdata.xls, rdata.xls)
```

## Setup
```bash
conda env create -f environment.yml
```

```bash
conda activate econ-consumption
```

Or, using the existing venv: `pip install -r requirements.txt`.

Notebooks find the data through the `.workspace-root` marker, so they run from any subfolder. If you run them from a copy elsewhere (for example in a Claude Science session), set `ECON_ROOT=/path/to/econ-consumption`.

## Using with Claude Science
Grant this folder **Read & write** access and paste [CLAUDE.md](CLAUDE.md) into the project's custom instructions. Claude Science can't commit inside granted folders, so run `git` from your own terminal.
