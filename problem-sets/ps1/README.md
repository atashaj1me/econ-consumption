# Problem Set 1

Life-cycle profiles of labor income, wealth and expenditure by age, education, race, sex and tenure, using the SCF and the PSID.

| File | Covers | Data |
| ---- | ------ | ---- |
| [problemset1-p1.ipynb](problemset1-p1.ipynb), [problemset1-p2.ipynb](problemset1-p2.ipynb) | Exploratory notebooks | SCF 2016/2019/2022 |
| [src/problemset1.py](src/problemset1.py) | Question 3 tables and graphs (run all cells) | SCF |
| [src/problemset1-cont.py](src/problemset1-cont.py) | Question 4 tables and graphs (run all cells) | PSID panel, WDI |

**PSID panel:** build it first with [pipelines/psid](../../pipelines/psid). That step creates `data/psid/panel_output/psid_family_panel_long.csv`.

Figures are written to [figs/](figs). The submitted packages (with data and PDF) are kept locally in `archive/` and are not on GitHub.
