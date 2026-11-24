# ECON 312 - Economics of Consumption Workspace
This is the workspace for the course ECON 312 - Economics of Consumption at Fulbright University Vietnam, instructed by Dr. Xavier M. G. Bautista. It holds the lab sessions, worksheets, problem sets, and other materials for the quantitative analysis in the course.

Owner: Nguyen Chi Thang, Fulbright University Vietnam

Contact me: thang.nguyen.240184@student.fulbright.edu.vn

## Repository layout
| Folder | Contents |
| ------ | -------- |
| [projects](projects) | Notebooks for the labs and problem sets (see the [ledger](projects/ledger.md)) |
| [figs](figs) | Output figures; Problem Set 1 figures are in [figs/problemset1](figs/problemset1) |
| [xavier_gibberish](xavier_gibberish) | Worksheets and scripts provided by Dr. Xavier (Lab 1, life-cycle Euler equation, Lab 3 risk sharing) |
| `data/` | Datasets. **Not tracked on GitHub** because of their size; see below |

### Notebooks
* [lab1-eis.ipynb](projects/lab1-eis.ipynb): Lab 1, estimating the elasticity of intertemporal substitution
* [lab1-lcp.ipynb](projects/lab1-lcp.ipynb): Lab 1, life-cycle profiles
* [problemset1-p1.ipynb](projects/problemset1-p1.ipynb), [problemset1-p2.ipynb](projects/problemset1-p2.ipynb): Problem Set 1

## Data (local only)
`data/` is excluded through [.gitignore](.gitignore). To run the notebooks, download the datasets and place them as follows:

```
data/
├── intrvw24/                    # BLS Consumer Expenditure Survey, Interview 2024 (CSV)
├── psid/                        # Panel Study of Income Dynamics extracts (.txt + .sas), plus built outputs
├── survey_of_consumer_finance/  # Federal Reserve SCF summary extracts: SCFP2016/2019/2022.csv, scf2022.csv
└── world_dev_index/             # World Bank World Development Indicators (cdata.xls, rdata.xls)
```

The Problem Set 1 submission packages (`projects/problemset1_*`) and zip archives are also kept local only.

## Setup
The notebooks use Python 3 with `numpy`, `pandas`, `statsmodels`, `matplotlib`, and `seaborn`:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install numpy pandas statsmodels matplotlib seaborn jupyter
```
