"""
Problem Set 1 (PSID version): Panel Study of Income Dynamics, family-level long panel.

Part A: summary statistics, group comparisons, and LaTeX tables.
Part B: life-cycle profiles by age, quartic age regressions, and fitted profiles.
Part C: Euler equation regressions of household consumption growth on the US real
        interest rate, realized and AR(2)-fitted.

All parts share one data pipeline (load_psid / load_all): missing-value codes set to NaN,
dollar variables deflated to base-year dollars with the CPI-U, harmonized race and tenure
coding, and a pooled sample of the biennial waves. Cells are delimited by "# %%".

Weights: every statistic, profile median, and regression is weighted by the PSID family
weight (weight_col). The weight exists from 1997, so all analysis years must be 1997 or later.
"""

# %% Imports and paths
import re
from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.iolib.summary2 import summary_col

# locate the workspace root (folder containing .workspace-root); override with ECON_ROOT
import os
ROOT = Path(os.environ.get("ECON_ROOT") or next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / ".workspace-root").exists()))
data_path = (ROOT / "data/psid/panel_output/psid_family_panel_long.csv")
figs_dir = (ROOT / "problem-sets/ps1/figs")
figs_dir.mkdir(parents=True, exist_ok=True)

macro_data_path = (ROOT / "data/world_dev_index")

# %% Loading macro data (source: world development indicator, in the folder I mispelled it as world development index, lazy to change)
# real interest rate (%)
rdata = pd.read_excel(
    macro_data_path / "rdata.xls",
    skiprows=3,
)

rdata = rdata.melt(
    id_vars=["Country Name", "Country Code"],
    value_vars=[r for r in rdata.columns if str(r).isdigit()],
    var_name="year",
    value_name="interest_rate",
)

# Convert interest rates from percentages to decimals
rdata["interest_rate"] = rdata["interest_rate"] / 100
rdata["year"] = rdata["year"].astype(int)

# Replace missing US observations with FRED annual averages
fred_us_rates = {
    2022: 1.0594 / 100,
    2023: 1.6575 / 100,
}

for year, rate in fred_us_rates.items():
    mask = (
        (rdata["Country Code"] == "USA")
        & (rdata["year"] == year)
    )

    if mask.any():
        rdata.loc[mask, "interest_rate"] = rate
    else:
        rdata = pd.concat(
            [
                rdata,
                pd.DataFrame({
                    "Country Name": ["United States"],
                    "Country Code": ["USA"],
                    "year": [year],
                    "interest_rate": [rate],
                }),
            ],
            ignore_index=True,
        )

# Sort and extract US observations
rdata = rdata.sort_values(["Country Code", "year"])
rdata_us = rdata.query("`Country Code` == 'USA'").copy()

# %% Settings and shared library
# ---------------------------------------------------------------- settings
# Wealth exists only for 1984, 1989, 1994 and every wave from 1999; expenditure only from
# 1999. All four dollar variables are therefore jointly available for biennial waves 1999-2023.
table_years = [1999, 2011, 2023]                  # waves reported individually
pooled_years = list(range(1999, 2024, 2))         # waves stacked into the pooled sample
age_range = (25, 80)                              # head's age, inclusive; None keeps all ages
# PSID family weight, pooled across waves in the panel (family_weight_variable gives the source
# variable of each wave). Available from 1997 only; blank or zero weights are dropped in
# load_psid. The concept changes by wave (e.g. 2003 is the longitudinal weight), so check the
# codebook before relying on pooled weighted statistics. None gives unweighted results.
weight_col = "family_weight"
# Head's highest year of college completed: 0 = no college (or under one year), 1-4 = years
# completed, 5 = five or more, 9 = NA/DK. It measures college only, so heads without college
# are one group (high school dropouts and graduates cannot be separated). None drops EDUC.
educ_col = "head_highest_year_college_completed"

if weight_col:
    assert min(table_years + pooled_years) >= 1997, \
        "family_weight starts in 1997; move table_years and pooled_years to 1997 or later"

dollar_vars = ["LABINC", "WEALTH", "WEALTH_XH", "EXPEND"]
demo_vars = ["HHSEX", "AGE", "RACE", "TENURE"]          # EDUC and MARRIED enter as regression controls
continuous_demo = ["AGE"]
categorical_vars = [v for v in demo_vars if v not in continuous_demo]
continuous_vars = dollar_vars + continuous_demo

pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
scale = 1_000
base_year = 2023

# CPI-U, U.S. city average, annual average, 1982-84 = 100 (BLS). Spot-check before submission.
CPI = {1967: 33.4, 1968: 34.8, 1969: 36.7, 1970: 38.8, 1971: 40.5, 1972: 41.8, 1973: 44.4,
       1974: 49.3, 1975: 53.8, 1976: 56.9, 1977: 60.6, 1978: 65.2, 1979: 72.6, 1980: 82.4,
       1981: 90.9, 1982: 96.5, 1983: 99.6, 1984: 103.9, 1985: 107.6, 1986: 109.6, 1987: 113.6,
       1988: 118.3, 1989: 124.0, 1990: 130.7, 1991: 136.2, 1992: 140.3, 1993: 144.5,
       1994: 148.2, 1995: 152.4, 1996: 156.9, 1997: 160.5, 1998: 163.0, 1999: 166.6,
       2000: 172.2, 2001: 177.1, 2002: 179.9, 2003: 184.0, 2004: 188.9, 2005: 195.3,
       2006: 201.6, 2007: 207.342, 2008: 215.303, 2009: 214.537, 2010: 218.056,
       2011: 224.939, 2012: 229.594, 2013: 232.957, 2014: 236.736, 2015: 237.017,
       2016: 240.007, 2017: 245.120, 2018: 251.107, 2019: 255.657, 2020: 258.811,
       2021: 270.970, 2022: 292.655, 2023: 304.702}

# Race: head_race_code changes meaning across waves and cannot isolate Hispanic origin, so the
# only comparable split is White (1), Black (2), and everything else (3-7).
labels = {"HHSEX": {1: "Male", 2: "Female"},
          "RACE": {1: "White", 2: "Black", 3: "Other (incl. Hispanic, Asian)"},
          "TENURE": {1: "Owner", 2: "Renter", 3: "Neither"},
          "MARRIED": {0: "Not married", 1: "Married"},
          "EDUC": {1: "No college", 2: "1-3 years of college", 3: "4+ years of college"}}
race_note = ("Race is the race code of the head; the PSID coding changed across waves and "
             "does not separate Hispanic origin, so Hispanic, Asian, and all other heads are "
             "grouped in Other.")

age_bins = [0, 35, 45, 55, 65, 75, 200]
age_labels = ["Under 35", "35-44", "45-54", "55-64", "65-74", "75 and over"]
group_order = {"Age of head": age_labels,
               "Education of head": list(labels["EDUC"].values()),
               "Race/ethnicity": list(labels["RACE"].values()),
               "Housing tenure": list(labels["TENURE"].values()),
               "Sex of head": list(labels["HHSEX"].values())}

if not educ_col:
    group_order.pop("Education of head")

POOLED = "Pooled"

# ---------------------------------------------------------------- small helpers
def _ysort(ys):
    """Numeric years ascending, Pooled last (mixed int/str labels cannot be sorted directly)."""
    ys = list(ys)
    return sorted(y for y in ys if y != POOLED) + ([POOLED] if POOLED in ys else [])


def _slug_label(x):
    """Safe LaTeX label fragment."""
    return re.sub(r"[^a-z0-9]+", "_", str(x).lower()).strip("_")


# ---------------------------------------------------------------- weighted moments
def wquantile(x, w, q):
    """Weighted quantile (inverse weighted CDF), q in [0, 1]."""
    idx = np.argsort(x, kind="mergesort")
    x, w = x[idx], w[idx]
    cw = np.cumsum(w) / w.sum()
    return x[np.minimum(np.searchsorted(cw, q), len(x) - 1)]


def wstats(x, w):
    """All statistics for one sample; x, w are 1-d float arrays without NaN."""
    sw = w.sum()
    mu = (w * x).sum() / sw
    d = x - mu
    m2, m3, m4 = [(w * d**k).sum() / sw for k in (2, 3, 4)]
    out = {"Mean": mu, "Variance": m2, "Std. dev.": np.sqrt(m2),
           "Skewness": m3 / m2**1.5, "Kurtosis": m4 / m2**2,
           "Min": x.min(), "Max": x.max()}
    for p in pcts:
        out[f"P{p}"] = wquantile(x, w, p / 100)
    return out


def cell_stats(x, w):
    """Mean, median, variance, std. dev. of one cell."""
    mu = np.average(x, weights=w)
    var = np.average((x - mu) ** 2, weights=w)
    return mu, wquantile(x, w, 0.5), var, np.sqrt(var)


# ---------------------------------------------------------------- data pipeline
RAW = {"panel_id": "ID", "year": "YEAR", "income_reference_year": "INCYEAR",
       "head_age": "AGE", "head_sex_code": "HHSEX", "head_race_code": "RACE_CODE",
       "housing_tenure_code": "TENURE_CODE", "marital_status_generated_code": "MARITAL_CODE",
       "head_labor_income": "LABINC", "family_wealth_in_home_equity": "WEALTH",
       "family_wealth_ex_home_equity": "WEALTH_XH", "total_family_expenditure": "EXPEND"}


def load_psid(path=data_path, require_weight=True):
    """Clean household-wave records for all years, in base-year dollars.

    Missing-value codes: age 0 and 999, labor income 9,999,999 (all of 1994 and 1995 are
    affected), non-positive expenditure. LABINC refers to the prior calendar year
    (INCYEAR) and is deflated with that year's CPI; wealth and expenditure use the
    interview-year CPI.

    With weight_col set, W is the family weight and, if require_weight, records with a blank
    or zero weight are dropped (blank = outside the weighted sample or pre-1997). The Euler
    panel passes require_weight=False so that the earlier wave of a pair is not screened on
    its own weight."""
    cols = list(RAW) + ([weight_col] if weight_col else []) + ([educ_col] if educ_col else [])
    d = pd.read_csv(path, usecols=cols, low_memory=False).rename(columns=RAW)

    d["AGE"] = d["AGE"].where(d["AGE"].between(1, 998))
    d["LABINC"] = d["LABINC"].where(d["LABINC"] < 9_999_999)
    d["EXPEND"] = d["EXPEND"].where(d["EXPEND"] > 0)
    d["HHSEX"] = d["HHSEX"].where(d["HHSEX"].isin([1, 2]))
    d["RACE"] = d["RACE_CODE"].map({1: 1, 2: 2, **{k: 3 for k in range(3, 8)}})
    d["TENURE"] = d["TENURE_CODE"].map({1: 1, 5: 2, 8: 3})
    # MARRIED: generated marital status 1 = married or permanently cohabiting (spouse or
    # partner present); 2-5 = never married, widowed, divorced, separated; 8, 9, blank = missing.
    # Verify these codes against the codebook for the marital-status-generated variables.
    m = d["MARITAL_CODE"].where(d["MARITAL_CODE"].between(1, 5))
    d["MARRIED"] = (m == 1).astype(float).where(m.notna())
    if educ_col:                                   # 9 and blanks -> NaN, then group the codes
        d["EDUC"] = d[educ_col].where(d[educ_col].between(0, 5)).map(
            {0: 1, 1: 2, 2: 2, 3: 2, 4: 3, 5: 3})

    base = CPI[base_year]
    d["LABINC"] = d["LABINC"] * base / d["INCYEAR"].map(CPI)
    for v in ("WEALTH", "WEALTH_XH", "EXPEND"):
        d[v] = d[v] * base / d["YEAR"].map(CPI)

    d["W"] = d[weight_col].astype(float) if weight_col else 1.0
    if weight_col and require_weight:
        d = d[d["W"] > 0]                          # NaN fails the comparison, so blanks drop too
    if age_range is not None:
        d = d[d["AGE"].between(*age_range)]
    d = d.dropna(subset=["AGE"]).copy()
    d["AGE"] = d["AGE"].astype(int)
    return d


def load_all(path=data_path, pooled=True):
    """{year: frame} for table_years plus a Pooled frame (all pooled_years stacked)."""
    d = load_psid(path)
    waves = {yr: d[d["YEAR"] == yr].copy() for yr in table_years}
    if pooled:
        p = d[d["YEAR"].isin(pooled_years)].copy()
        p["W"] = p["W"] / p["YEAR"].nunique()
        waves[POOLED] = p
    return waves


# ---------------------------------------------------------------- summaries
def summarize_continuous(d, variables=continuous_vars):
    """Rows = variables, columns = statistics. Dollars in thousands of base-year dollars."""
    rows = {}
    for v in variables:
        ok = d[v].notna()
        s = pd.Series(wstats(d.loc[ok, v].to_numpy(float), d.loc[ok, "W"].to_numpy(float)))
        if v in dollar_vars:
            for k in s.index:
                if k == "Variance":
                    s[k] /= scale**2
                elif k not in ("Skewness", "Kurtosis"):
                    s[k] /= scale
        s["N"] = ok.sum()
        rows[v] = s
    return pd.DataFrame(rows).T


def summarize_categorical(d, variables=categorical_vars):
    """Weighted population shares (percent) among non-missing records, in code order."""
    out = {}
    for v in variables:
        g = d.dropna(subset=[v])
        sh = g.groupby(v)["W"].sum() / g["W"].sum() * 100
        sh = sh.reindex(list(labels[v])).fillna(0)
        sh.index = list(labels[v].values())
        out[v] = sh
    return pd.concat(out, names=["Variable", "Category"])


def summarize_all(waves):
    """Returns (continuous, categorical) long frames; Pooled column last."""
    cont = pd.concat({yr: summarize_continuous(d) for yr, d in waves.items()},
                     names=["Year", "Variable"]).swaplevel().loc[continuous_vars]
    cat = pd.concat({yr: summarize_categorical(d) for yr, d in waves.items()}, axis=1)
    cat.columns.name = "Year"
    return cont, cat


# ---------------------------------------------------------------- group comparisons
def add_groups(d):
    g = pd.DataFrame(index=d.index)
    g["Age of head"] = pd.cut(d["AGE"], age_bins, labels=age_labels, right=False)
    if educ_col:
        g["Education of head"] = d["EDUC"].map(labels["EDUC"])
    g["Race/ethnicity"] = d["RACE"].map(labels["RACE"])
    g["Housing tenure"] = d["TENURE"].map(labels["TENURE"])
    g["Sex of head"] = d["HHSEX"].map(labels["HHSEX"])
    return g


def _finish(df, keys):
    cols = ["Mean", "Median", "Variance", "Std. dev."]
    out = df.set_index(keys)
    out[["Mean", "Median", "Std. dev."]] /= scale      # thousands of base-year dollars
    out["Variance"] /= scale**2                        # squared thousands
    return out


def group_stats(d, variables=dollar_vars):
    """Mean, median, variance, std. dev., and N by group; index (Dimension, Group, Variable)."""
    grp, w = add_groups(d), d["W"].to_numpy(float)
    cells = [("All households", "All households", np.ones(len(d), bool))]
    cells += [(dim, lab, (grp[dim] == lab).to_numpy())
              for dim, labs in group_order.items() for lab in labs]
    rec = []
    for dim, lab, mask in cells:
        for v in variables:
            x = d[v].to_numpy(float)
            ok = mask & ~np.isnan(x)
            if ok.any():
                rec.append((dim, lab, v, *cell_stats(x[ok], w[ok]), ok.sum()))
    df = pd.DataFrame(rec, columns=["Dimension", "Group", "Variable", "Mean", "Median",
                                    "Variance", "Std. dev.", "N"])
    return _finish(df, ["Dimension", "Group", "Variable"])


def group_stats_2way(d, panel, row, variables=dollar_vars):
    """Stats for each (panel group, row group) cell. N is the unweighted count of valid
    records; Share is the weighted percent of all records in d falling in the cell."""
    grp, w = add_groups(d), d["W"].to_numpy(float)
    rec = []
    for pl in group_order[panel]:
        for rl in group_order[row]:
            mask = ((grp[panel] == pl) & (grp[row] == rl)).to_numpy()
            share = 100 * w[mask].sum() / w.sum()
            for v in variables:
                x = d[v].to_numpy(float)
                ok = mask & ~np.isnan(x)
                if ok.any():
                    rec.append((pl, rl, v, *cell_stats(x[ok], w[ok]), ok.sum(), share))
    df = pd.DataFrame(rec, columns=["Panel", "Row", "Variable", "Mean", "Median", "Variance",
                                    "Std. dev.", "N", "Share"])
    return _finish(df, ["Panel", "Row", "Variable"])


def build_group_tables(waves):
    """Long frame indexed by (Year, Dimension, Group, Variable)."""
    return pd.concat({yr: group_stats(d) for yr, d in waves.items()}, names=["Year"])


# ---------------------------------------------------------------- LaTeX
def _tex(t, caption, label, notes, fmt="%.2f"):
    body = t.to_latex(float_format=fmt, na_rep="--", column_format="l" + "r" * t.shape[1])
    return (
        "\\begin{table}[htbp]\n\\centering\n"
        f"\\caption{{{caption}}}\n\\label{{{label}}}\n"
        "\\begin{threeparttable}\n"
        f"{body}"
        "\\begin{tablenotes}\n\\footnotesize\n"
        f"\\item \\textit{{Notes:}} {notes}\n"
        "\\end{tablenotes}\n\\end{threeparttable}\n\\end{table}\n"
    )


# Weighting sentence for LaTeX notes; silent when unweighted. No raw underscores (LaTeX-safe).
_wt = ("Statistics are weighted by the PSID family weight of each wave; records with a zero "
       "or missing weight are dropped. " if weight_col else "")
_wtag = "(Weighted) " if weight_col else ""                               # plot title prefix
_age = f" aged {age_range[0]} to {age_range[1]}" if age_range else ""
_src = ("Source: Panel Study of Income Dynamics, family-level panel. "
        f"{_wt}Observations are household-wave records of heads{_age}; waves are treated as "
        "independent cross-sections, so a household can appear in several waves. The pooled "
        f"sample stacks the biennial waves {min(pooled_years)} to {max(pooled_years)}. "
        f"Dollar values are in {base_year} dollars (CPI-U): labor income, which refers to the "
        "prior calendar year, is deflated with that year's CPI, and wealth and expenditure with "
        "the interview-year CPI. LABINC is the head's labor income, WEALTH is net worth "
        "including home equity, WEALTH_XH is net worth excluding home equity, and EXPEND is "
        "total family expenditure.")


def latex_by_variable(cont, var):
    """Rows = statistics, columns = years (Pooled last), for one continuous variable."""
    unit = (f"thousands of {base_year} dollars, except skewness and kurtosis"
            if var in dollar_vars else "years, except skewness and kurtosis")
    t = cont.loc[var].T.drop(index="N")
    return _tex(t, f"Summary statistics for {var} ({unit})", f"tab:psid_{var.lower()}",
                _src + " Kurtosis is the raw (non-excess) fourth standardized moment.")


def latex_shares(cat, var):
    """Population shares (percent) of a categorical variable, by year."""
    return _tex(cat.loc[var], f"Population shares of {var} (percent)",
                f"tab:psid_{var.lower()}_shares",
                _src + (" " + race_note if var == "RACE" else ""), fmt="%.1f")


def latex_group_table(big, var, stats=("Mean", "Median", "Variance"), min_n=30):
    """Group statistics of `var`, one column block per year (Pooled last), panels by dimension."""
    t = big.xs(var, level="Variable")
    years = _ysort(t.index.get_level_values("Year").unique())
    k = len(stats)
    ncol = 1 + k * len(years)

    def cells(dim, lab):
        out = []
        for y in years:
            try:
                r = t.loc[(y, dim, lab)]
                out += [f"{r[c]:,.1f}" for c in stats] if r["N"] >= min_n else ["--"] * k
            except KeyError:
                out += ["--"] * k
        return " & ".join(out)

    unit = (f"thousands of {base_year} dollars; variance in squared thousands"
            if "Variance" in stats else f"thousands of {base_year} dollars")
    L = ["\\begin{table}[htbp]", "\\centering",
         f"\\caption{{{var} by household characteristics ({unit})}}",
         f"\\label{{tab:psid_{var.lower()}_groups}}", "\\begin{threeparttable}",
         "\\begin{tabular}{l" + "r" * (k * len(years)) + "}", "\\toprule",
         " & " + " & ".join(f"\\multicolumn{{{k}}}{{c}}{{{y}}}" for y in years) + " \\\\"]
    L.append(" ".join(f"\\cmidrule(lr){{{2 + k*i}-{1 + k*(i+1)}}}" for i in range(len(years))))
    L.append("Group & " + " & ".join([" & ".join(stats)] * len(years)) + " \\\\")
    L += ["\\midrule", "All households & " + cells("All households", "All households") + " \\\\"]
    for dim, labs in group_order.items():
        L += ["\\midrule", f"\\multicolumn{{{ncol}}}{{l}}{{\\textit{{{dim}}}}} \\\\"]
        L += [f"\\hspace{{1em}}{lab} & " + cells(dim, lab) + " \\\\" for lab in labs]
    L += ["\\bottomrule", "\\end{tabular}", "\\begin{tablenotes}\\footnotesize",
          f"\\item \\textit{{Notes:}} {_src} Variance is the population variance within the "
          f"group. Cells with fewer than {min_n} observations are suppressed (--). "
          "Characteristics refer to the head of the household. " + race_note,
          "\\end{tablenotes}", "\\end{threeparttable}", "\\end{table}"]
    return "\n".join(L) + "\n"


def latex_cross_section_table(tab, panel, row, year, variables=dollar_vars,
                              stats=("Mean", "Median", "Variance"), show_share=True, min_n=30):
    """Single-sample table: `row` groups within each `panel` group, one column block per
    variable. `year` is a wave or POOLED. Cells with fewer than min_n observations are
    suppressed."""
    k, nv = len(stats), len(variables)
    sh = 1 if show_share else 0
    ncol = 1 + sh + k * nv

    def cells(pl, rl):
        try:
            r0 = tab.loc[(pl, rl, variables[0])]
            if r0["N"] < min_n:
                raise KeyError
            out = [f"{r0['Share']:.1f}"] if show_share else []
            for v in variables:
                r = tab.loc[(pl, rl, v)]
                out += [f"{r[c]:,.1f}" for c in stats]
            return " & ".join(out)
        except KeyError:
            return " & ".join(["--"] * (sh + k * nv))

    sample = (f"PSID {min(pooled_years)} to {max(pooled_years)} pooled" if year == POOLED
              else f"PSID {year}")
    slug = lambda z: z.split("/")[0].split()[0].lower()
    unit = (f"thousands of {base_year} dollars; variance in squared thousands"
            if "Variance" in stats else f"thousands of {base_year} dollars")
    L = ["\\begin{table}[htbp]", "\\centering",
         f"\\caption{{Statistics by {panel.lower()} and {row.lower()}, {sample} ({unit})}}",
         f"\\label{{tab:psid_{_slug_label(year)}_{slug(panel)}_{slug(row)}}}",
         "\\begin{threeparttable}",
         "\\setlength{\\tabcolsep}{4pt}", "\\resizebox{\\textwidth}{!}{%",
         "\\begin{tabular}{l" + "r" * (sh + k * nv) + "}", "\\toprule",
         " & ".join([""] + [""] * sh + [f"\\multicolumn{{{k}}}{{c}}{{{v}}}" for v in variables])
         + " \\\\"]
    L.append(" ".join(f"\\cmidrule(lr){{{2 + sh + k*i}-{1 + sh + k*(i+1)}}}" for i in range(nv)))
    L.append(" & ".join([row] + (["Share (\\%)"] if show_share else []) + list(stats) * nv)
             + " \\\\")
    for pl in group_order[panel]:
        L += ["\\midrule", f"\\multicolumn{{{ncol}}}{{l}}{{\\textit{{{pl}}}}} \\\\"]
        L += [f"\\hspace{{1em}}{rl} & " + cells(pl, rl) + " \\\\" for rl in group_order[row]]
    L += ["\\bottomrule", "\\end{tabular}}", "\\begin{tablenotes}\\footnotesize",
          f"\\item \\textit{{Notes:}} {_src} Share is the percentage of all records in the "
          "sample falling in the cell. Variance is the population variance within the cell. "
          f"Cells with fewer than {min_n} observations are suppressed (--). "
          "Characteristics refer to the head of the household. " + race_note,
          "\\end{tablenotes}", "\\end{threeparttable}", "\\end{table}"]
    return "\n".join(L) + "\n"


# %% ======================= PART A: SUMMARY STATISTICS AND LATEX TABLES =======================
waves = load_all()
print(waves[POOLED].groupby("YEAR")[dollar_vars].count())     # valid observations per variable
if weight_col:                                                # records kept and weighted population
    print(waves[POOLED].groupby("YEAR")["W"].agg(records="size", total_weight="sum")
          .assign(total_weight=lambda t: t["total_weight"] * waves[POOLED]["YEAR"].nunique()))
if educ_col:                                                  # share of records with EDUC observed
    print(waves[POOLED].groupby("YEAR")["EDUC"].apply(lambda s: s.notna().mean()).round(3))

cont, cat = summarize_all(waves)
print(cont.loc["LABINC"].T)         # moments and percentiles by year
print(cat.loc["RACE"])

# Combine all wave-specific DataFrames into one DataFrame
waves_df = pd.concat(
    waves,
    names=["SAMPLE", "ROW_ID"]
).reset_index(level="SAMPLE").reset_index(drop=True)

# Inspect the combined dataset
print(waves_df.shape)
print(waves_df.head())
print(waves_df.info())


# %% Summary statistics by variable
for v in continuous_vars:
    print(latex_by_variable(cont, v))

# %% Population shares
for v in categorical_vars:
    print(latex_shares(cat, v))

# %% Group comparisons (age, race, tenure, sex of head)
big = build_group_tables(waves)
for v in dollar_vars:
    print(latex_group_table(big, v))

# %% Male-headed households, pooled sample
def pooled_subsample(waves, col="HHSEX", value=1):
    """Pooled sample (deflated, weights / number of waves) restricted to col == value."""
    d = waves[POOLED]
    return d[d[col] == value].copy()


def _tag(tex, who):
    """Add the subsample to the caption and notes of a generated table."""
    tex = tex.replace("\\caption{", f"\\caption{{{who}: ", 1)
    return tex.replace("\\item \\textit{Notes:} ",
                       f"\\item \\textit{{Notes:}} Sample restricted to {who}. ", 1)


who = f"male-headed households (HHSEX = 1), PSID {min(pooled_years)} to {max(pooled_years)} pooled"
dm = pooled_subsample(waves)

# Table 1: full distribution statistics, one column per variable
cont_m = summarize_continuous(dm, dollar_vars)          # rows = variables, cols = statistics
print(_tag(_tex(cont_m.T.drop(index="N"),
                f"Summary statistics (thousands of {base_year} dollars, "
                "except skewness and kurtosis)",
                "tab:psid_pooled_male_summary",
                _src + " Kurtosis is the raw (non-excess) fourth standardized moment."), who))

# Tables 2-5: mean, median, variance by household characteristics, one table per variable
big_m = pd.concat({POOLED: group_stats(dm)}, names=["Year"])
for v in dollar_vars:
    print(_tag(latex_group_table(big_m, v), who))

# %% Male-headed households: housing tenure by race, pooled sample
tab_m = group_stats_2way(dm, "Race/ethnicity", "Housing tenure")
tex = latex_cross_section_table(tab_m, "Race/ethnicity", "Housing tenure", POOLED)
tex = tex.replace("\\caption{", "\\caption{Male-headed households (HHSEX = 1): ", 1)
tex = tex.replace("\\item \\textit{Notes:} ",
                  "\\item \\textit{Notes:} Sample restricted to male-headed households "
                  "(HHSEX = 1). Share is the percentage of all male-headed records in the "
                  "cell. ", 1)
print(tex)


# %% ======================= PART B: LIFE-CYCLE PROFILES AND QUARTIC REGRESSIONS =======================
outcomes = {"labor_income": ("Labor Income", "LABINC"),
            "wealth": ("Wealth", "WEALTH"),
            "wealth_xh": ("Wealth excl. Home Equity", "WEALTH_XH"),
            "expenditure": ("Expenditure", "EXPEND")}


def weighted_median(group, variable):
    d = group[[variable, "W"]].dropna()
    return wquantile(d[variable].to_numpy(float), d["W"].to_numpy(float), 0.5) if len(d) else np.nan


def create_profile(df, sample, group_variable=None):
    """Weighted medians of each outcome by age (and group), with valid-observation counts."""
    group_cols = ["AGE"] if group_variable is None else ["AGE", group_variable]
    rows = []
    for key, g in df.groupby(group_cols, observed=True):
        rec = dict(zip(group_cols, key if isinstance(key, tuple) else (key,)))
        for col, (_, var) in outcomes.items():
            rec[col] = weighted_median(g, var)
            rec[f"n_{col}"] = int(g[var].notna().sum())
        rows.append(rec)
    out = pd.DataFrame(rows)
    out["SAMPLE"] = sample
    return out


def add_profile_groups(df):
    """Race, tenure, and sex group labels (ordered categoricals) for the profile plots."""
    df = df.copy()
    pairs = [("RACE_GROUP", "RACE"), ("TENURE_GROUP", "TENURE"), ("HHSEX_GROUP", "HHSEX")]
    if educ_col:
        pairs.append(("EDUC_GROUP", "EDUC"))
    for new, src in pairs:
        df[new] = pd.Categorical(df[src].map(labels[src]), categories=list(labels[src].values()),
                                 ordered=True)
    return df


samples = {str(y): waves[y] for y in table_years}
samples["All Pooled"] = waves[POOLED]
samples = {k: add_profile_groups(d) for k, d in samples.items()}


def build_profiles(group_variable=None):
    return pd.concat([create_profile(d, s, group_variable) for s, d in samples.items()],
                     ignore_index=True)


profile_age = {s: create_profile(d, s) for s, d in samples.items()}     # one frame per sample
profile_race = build_profiles("RACE_GROUP")
profile_tenure = build_profiles("TENURE_GROUP")
profile_sex = build_profiles("HHSEX_GROUP")
profile_educ = build_profiles("EDUC_GROUP") if educ_col else None
profile_all = pd.concat(profile_age.values(), ignore_index=True)

# %% Profile plots
sns.set_theme(style="whitegrid", font="Latin Modern Roman")


def plot_profile(data, col, hue, title, ylabel, fname, legend_title, min_n=20):
    d = data[data[f"n_{col}"] >= min_n].copy()
    d[col] = d[col] / scale
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.lineplot(data=d, x="AGE", y=col, hue=hue, marker="o", ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Age")
    ax.set_ylabel(ylabel)
    ax.legend(title=legend_title)
    fig.savefig(figs_dir / fname, format="pdf", bbox_inches="tight")
    plt.show()


pooled_only = lambda p: p[p["SAMPLE"] == "All Pooled"]

for col, (name, var) in outcomes.items():
    ylab = f"{var}, thousands of {base_year} dollars"
    plot_profile(profile_all, col, "SAMPLE", f"{_wtag}Median {name} by Age", ylab,
                 f"problemset1_{col}_by_age_psid.pdf", "Survey year")
    if educ_col:
        plot_profile(pooled_only(profile_educ), col, "EDUC_GROUP",
                     f"{_wtag}Median {name} by Age and Education, All Pooled", ylab,
                     f"problemset1_{col}_by_age_education_pooled_psid.pdf", "Education")
    plot_profile(pooled_only(profile_race), col, "RACE_GROUP",
                 f"{_wtag}Median {name} by Age and Race, All Pooled", ylab,
                 f"problemset1_{col}_by_age_race_pooled_psid.pdf", "Race")
    plot_profile(pooled_only(profile_tenure), col, "TENURE_GROUP",
                 f"{_wtag}Median {name} by Age and Housing Tenure, All Pooled", ylab,
                 f"problemset1_{col}_by_age_tenure_pooled_psid.pdf", "Tenure")
    plot_profile(pooled_only(profile_sex), col, "HHSEX_GROUP",
                 f"{_wtag}Median {name} by Age and Household Head's Sex, All Pooled", ylab,
                 f"problemset1_{col}_by_age_hhsex_psid.pdf", "Sex of head")


# %% Profile plots: male-headed households only (HHSEX = 1)
samples_m = {s: d[d["HHSEX"] == 1].copy() for s, d in samples.items()}
profile_all_m = pd.concat([create_profile(d, s) for s, d in samples_m.items()],
                          ignore_index=True)

# Group profiles use the pooled sample only, as in the full-sample plots
pooled_m = samples_m["All Pooled"]
group_specs = [("RACE_GROUP", "Race", "Race", "race"),
               ("TENURE_GROUP", "Housing Tenure", "Tenure", "tenure")]
if educ_col:
    group_specs.insert(0, ("EDUC_GROUP", "Education", "Education", "education"))
group_profiles_m = {g: create_profile(pooled_m, "All Pooled", g) for g, *_ in group_specs}

for col, (name, var) in outcomes.items():
    ylab = f"{var}, thousands of {base_year} dollars"
    plot_profile(profile_all_m, col, "SAMPLE",
                 f"{_wtag}Median {name} by Age, Male Heads", ylab,
                 f"problemset1_{col}_by_age_male_psid.pdf", "Survey year")
    for g, label, legend, slug in group_specs:
        plot_profile(group_profiles_m[g], col, g,
                     f"{_wtag}Median {name} by Age and {label}, Male Heads, All Pooled", ylab,
                     f"problemset1_{col}_by_age_{slug}_pooled_male_psid.pdf", legend)

# %% Quartic age regressions
def quartic_regression(data, outcome, male_only=True, controls=True, year_fe=False):
    """WLS of `outcome` on a quartic in age, weighted by the family weight W, restricted to
    male heads (HHSEX = 1), with education, marital status, and race of the head as categorical
    controls. Standard errors are clustered by panel_id because the same household appears in
    several waves. Tenure is left out because it is mechanically related to wealth (home
    equity)."""
    d = data[data["HHSEX"] == 1] if male_only else data
    ctrl = control_vars if controls else []
    d = d.dropna(subset=[outcome] + ctrl)

    X = pd.DataFrame({f"age_power{k}": d["AGE"].astype(float) ** k for k in range(1, 5)})
    if ctrl:
        C = pd.DataFrame({c: pd.Categorical(d[c].map(labels[c]),
                                            categories=list(labels[c].values()))
                          for c in ctrl}, index=d.index)
        X = pd.concat([X, pd.get_dummies(C, drop_first=True, dtype=float)], axis=1)
    if year_fe:                                              # wave dummies, for pooled samples
        X = pd.concat([X, pd.get_dummies(d["YEAR"], prefix="YEAR",
                                         drop_first=True, dtype=float)], axis=1)
    X = sm.add_constant(X)
    return sm.WLS(d[outcome], X, weights=d["W"]).fit(
        cov_type="cluster", cov_kwds={"groups": d["ID"].to_numpy()})


control_vars = ["EDUC", "MARRIED", "RACE"] if educ_col else ["MARRIED", "RACE"]
if not educ_col:
    print("WARNING: educ_col is None, so education is NOT a control. "
          "Set educ_col to the education column in the CSV.")
_ctrl_names = {"EDUC": "education", "MARRIED": "marital status", "RACE": "race"}
_ctrl_text = ", ".join(_ctrl_names[c] for c in control_vars)
_wreg = ("Weighted least squares with the PSID family weight. " if weight_col else "")


def regression_latex(results, caption, label):
    """booktabs LaTeX table from a statsmodels summary_col object."""
    tex = results.as_latex()
    tab = re.search(r"\\begin\{tabular\}.*?\\end\{tabular\}", tex, re.S).group(0)
    parts = tab.split("\\hline")                             # booktabs rules in place of \hline
    rules = ["\\toprule"] + ["\\midrule"] * (len(parts) - 3) + ["\\bottomrule"]
    tab = "".join(p + r for p, r in zip(parts, rules)) + parts[-1]
    return (
        "\\begin{table}[htbp]\n\\centering\n"
        f"\\caption{{{caption}}}\n\\label{{{label}}}\n"
        "\\begin{threeparttable}\n"
        f"{tab}\n"
        "\\begin{tablenotes}\n\\footnotesize\n"
        f"\\item \\textit{{Notes:}} {_wreg}Standard errors clustered by household (panel\\_id) in "
        "parentheses. $^{*}p<0.1$, $^{**}p<0.05$, $^{***}p<0.01$. Male heads only; controls "
        f"are {_ctrl_text} of the head (married means a spouse or partner is present). "
        "The last column stacks all biennial waves and adds wave "
        "fixed effects.\n"
        "\\end{tablenotes}\n\\end{threeparttable}\n\\end{table}\n")


reg_samples = samples                                        # keys: wave years, "All Pooled"
reg_specs = {"LABINC": ("labor income (LABINC)", "tab:psid_labinc_quartic"),
             "WEALTH": ("wealth (WEALTH)", "tab:psid_wealth_quartic"),
             "WEALTH_XH": ("wealth excluding home equity (WEALTH\\_XH)", "tab:psid_wealth_xh_quartic"),
             "EXPEND": ("expenditure (EXPEND)", "tab:psid_expend_quartic")}

model_map = {name: {var: quartic_regression(d, var, year_fe=(name == "All Pooled"))
                    for var in reg_specs}
             for name, d in reg_samples.items()}

for var, (desc, label) in reg_specs.items():
    results = summary_col([model_map[n][var] for n in reg_samples], stars=True,
                          model_names=list(reg_samples),
                          info_dict={"N": lambda x: f"{int(x.nobs)}"})
    print(results)
    print(regression_latex(results, f"Quartic regressions of {desc} on age", label))

# %% Fitted age profiles
def predict_profile(res, age_grid, controls_at="mean"):
    """Fitted values over an age grid from a quartic WLS result.
    controls_at = "mean": non-age regressors held at their weighted sample means.
    controls_at = "reference": non-age regressors set to 0 (omitted categories)."""
    names = res.model.exog_names
    exog = pd.DataFrame(res.model.exog, columns=names)
    w = np.asarray(res.model.weights)

    grid = pd.DataFrame(index=age_grid, columns=names, dtype=float)
    for c in names:
        grid[c] = np.average(exog[c], weights=w) if controls_at == "mean" else 0.0
    grid["const"] = 1.0
    for k in range(1, 5):
        grid[f"age_power{k}"] = age_grid.astype(float) ** k
    return pd.Series(res.predict(grid[names]).to_numpy(), index=age_grid)


hat_names = {"LABINC": "labor_income_hat", "WEALTH": "wealth_hat",
             "WEALTH_XH": "wealth_xh_hat", "EXPEND": "expenditure_hat"}
age_grid = np.arange(waves[POOLED]["AGE"].min(), waves[POOLED]["AGE"].max() + 1)

for name, prof in profile_age.items():
    for var, res in model_map[name].items():
        prof[hat_names[var]] = prof["AGE"].map(predict_profile(res, age_grid))   # align on age

print(profile_age[str(table_years[-1])].head())

# %% Predicted profiles by sample (quartic fits, controls at weighted means)
fitted = {s: {v: predict_profile(res, age_grid) for v, res in m.items()}
          for s, m in model_map.items()}

for col, (name, var) in outcomes.items():
    fig, ax = plt.subplots(figsize=(9, 6))
    for s in samples:
        ax.plot(age_grid, fitted[s][var] / scale, label=s,
                linestyle="--" if s == "All Pooled" else "-",
                color="black" if s == "All Pooled" else None)
    ax.set_title(f"Predicted {name} by Age (Quartic Fit, Male Heads)")
    ax.set_xlabel("Age")
    ax.set_ylabel(f"{var}, thousands of {base_year} dollars")
    ax.legend(title="Sample")
    fig.savefig(figs_dir / f"problemset1_{col}_predicted_by_age_psid.pdf",
                format="pdf", bbox_inches="tight")
    plt.show()

# %% ======================= PART C: EULER EQUATION REGRESSIONS =======================
# Log-linearized CRRA Euler equation:
#   ln(c_{t+1} / c_t) = sigma * ln(1 + r_{t+1}) + sigma * ln(beta) + e_{t+1},  sigma = 1 / gamma
# Slope in the third specification estimates the elasticity of intertemporal substitution.
# Each specification is estimated twice: on all households and on male-headed households.
euler_specs = ["c_growth ~ interest_rate",
               "c_growth ~ log_gross_r",
               "log_gross_c_growth ~ log_gross_r"]

euler_specs_hat = ["c_growth ~ interest_rate_hat",
                   "c_growth ~ log_gross_r_hat",
                   "log_gross_c_growth ~ log_gross_r_hat"]


def fit_rate_ar(lags=2):
    """AR(lags) for the annual US log gross real rate on its own calendar lags.
    Returns (fitted Series indexed by year, statsmodels result)."""
    lr = np.log1p(rdata_us.set_index("year")["interest_rate"]).sort_index().dropna()
    lr = lr.reindex(range(lr.index.min(), lr.index.max() + 1))      # gaps stay NaN so lags are calendar lags
    frame = pd.concat({"y": lr, **{f"lag{k}": lr.shift(k) for k in range(1, lags + 1)}}, axis=1)
    res = smf.ols("y ~ " + " + ".join(f"lag{k}" for k in range(1, lags + 1)),
                  data=frame.dropna()).fit()
    fitted_r = res.predict(frame.dropna(subset=[f"lag{k}" for k in range(1, lags + 1)]))
    return fitted_r, res


def build_euler_panel(rate_offsets=(-2, -1), trim=(1, 99), drop_intervals=()):
    """Household consumption growth between consecutive biennial waves (YEAR-2 -> YEAR),
    merged with the US real interest rate over the same interval.

    c_growth            annualized net growth of real EXPEND, exp(log_gross_c_growth) - 1
    log_gross_c_growth  annualized log growth, ln(c_t / c_{t-2}) / 2
    log_gross_r         average of ln(1 + r_s) over years s = YEAR + offsets
    interest_rate       exp(log_gross_r) - 1, the annualized net real rate
    log_gross_r_hat     same average, using the AR(2) fitted log gross real rate
    interest_rate_hat   exp(log_gross_r_hat) - 1
    MALE                True if the head is male in both waves t-2 and t (HHSEX = 1), which
                        also screens out a change of head between waves
    W                   family weight of the end wave t (equal to 1 if weight_col is None);
                        intervals whose end wave has a zero or missing weight are dropped

    rate_offsets=(-2, -1): the rate dated s is earned from s to s+1, so the return between
    waves t-2 and t uses r_{t-2} and r_{t-1}. Use (-1, 0) if you prefer the end-of-interval
    convention. trim: percentiles of log growth kept, applied once to the full panel so the
    male subsample is a strict subset of it. drop_intervals: YEAR values (end of interval)
    to exclude, e.g. (2005,)."""
    gap = 2
    d = load_psid(require_weight=False)        # the earlier wave is not screened on its weight
    d = d[d["YEAR"].isin(pooled_years)][["ID", "YEAR", "AGE", "HHSEX", "EXPEND", "W"]]
    assert not d.duplicated(["ID", "YEAR"]).any(), "ID-YEAR is not unique"

    lag = d[["ID", "YEAR", "AGE", "HHSEX", "EXPEND"]].rename(
        columns={"AGE": "AGE_L", "HHSEX": "HHSEX_L", "EXPEND": "EXPEND_L"})
    lag["YEAR"] += gap                                     # match wave t-2 to wave t
    cur = d[d["W"] > 0] if weight_col else d               # end wave must carry a positive weight
    p = cur.merge(lag, on=["ID", "YEAR"], how="inner").dropna(subset=["EXPEND", "EXPEND_L"])

    # Same head check: head's age should advance by about two years across the gap
    p = p[(p["AGE"] - p["AGE_L"]).between(1, 3)]
    p = p[~p["YEAR"].isin(drop_intervals)]

    p["log_gross_c_growth"] = np.log(p["EXPEND"] / p["EXPEND_L"]) / gap
    lo, hi = np.percentile(p["log_gross_c_growth"], trim)
    p = p[p["log_gross_c_growth"].between(lo, hi)].copy()
    p["c_growth"] = np.expm1(p["log_gross_c_growth"])
    p["MALE"] = (p["HHSEX"] == 1) & (p["HHSEX_L"] == 1)

    lr = np.log1p(rdata_us.set_index("year")["interest_rate"])
    p["log_gross_r"] = np.mean([p["YEAR"].add(o).map(lr) for o in rate_offsets], axis=0)
    p["interest_rate"] = np.expm1(p["log_gross_r"])

    fit, _ = fit_rate_ar()
    p["log_gross_r_hat"] = np.mean([p["YEAR"].add(o).map(fit) for o in rate_offsets], axis=0)
    p["interest_rate_hat"] = np.expm1(p["log_gross_r_hat"])
    return p.dropna(subset=["log_gross_r", "log_gross_r_hat"]).reset_index(drop=True)


def run_euler(panel, specs=euler_specs):
    """WLS on household-interval data, weighted by the end-wave family weight W. The regressor
    varies only by interval, so standard errors are clustered by YEAR (the common-shock level),
    not by household."""
    return {s: smf.wls(s, data=panel, weights=panel["W"]).fit(
                cov_type="cluster", cov_kwds={"groups": panel["YEAR"].to_numpy()})
            for s in specs}


euler = build_euler_panel()
ar_fit, ar_res = fit_rate_ar()
print(ar_res.params.round(4), f"R2 = {ar_res.rsquared:.3f}, N = {int(ar_res.nobs)}")

euler_samples = {"All households": euler,
                 "Male heads": euler[euler["MALE"]].copy()}

euler_results, euler_tabs = {}, {}
for name, panel in euler_samples.items():
    print(f"\n{name}")
    print(panel.groupby("YEAR")[["c_growth", "interest_rate", "interest_rate_hat"]]
          .agg(["mean", "count"]).round(4))

    euler_results[name] = {"realized": run_euler(panel),
                           "fitted": run_euler(panel, specs=euler_specs_hat)}
    euler_tabs[name] = summary_col(
        list(euler_results[name]["realized"].values())
        + list(euler_results[name]["fitted"].values()),
        stars=True,
        model_names=["(1)", "(2)", "(3)", "(1-hat)", "(2-hat)", "(3-hat)"],
        info_dict={"N": lambda x: f"{int(x.nobs)}"})
    print(euler_tabs[name])
    # print(euler_tabs[name].as_latex())


# %% Euler regressions: LaTeX table
def _star(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def _coef(res, terms, d=4):
    """(coefficient with stars, standard error) strings for the first of `terms` found in
    res; two blank strings if the model has none of them."""
    t = next((t for t in terms if t in res.params.index), None)
    if t is None:
        return "", ""
    s = _star(res.pvalues[t])
    return f"{res.params[t]:.{d}f}" + (f"$^{{{s}}}$" if s else ""), f"({res.bse[t]:.{d}f})"


def euler_latex(results, panels, d=4,
                caption="Euler equation regressions of household consumption growth "
                        "on the real interest rate",
                label="tab:psid_euler"):
    """booktabs/threeparttable table: one panel per sample, columns (1)-(3) with the realized
    rate and (4)-(6) with the AR(2) fitted rate. `results` is euler_results, `panels` is
    euler_samples (same keys); requires booktabs and threeparttable in the preamble."""
    rows = [("Net real rate", ("interest_rate", "interest_rate_hat")),
            ("Log gross real rate", ("log_gross_r", "log_gross_r_hat")),
            ("Constant", ("Intercept",))]
    k = 6
    first = min(p["YEAR"].min() for p in panels.values())
    last = max(p["YEAR"].max() for p in panels.values())
    ages = f"{age_range[0]} to {age_range[1]}" if age_range else "all ages"

    L = ["\\begin{table}[htbp]", "\\centering",
         f"\\caption{{{caption}}}", f"\\label{{{label}}}", "\\begin{threeparttable}",
         "\\begin{tabular}{l" + "c" * k + "}", "\\toprule",
         " & \\multicolumn{3}{c}{Realized rate} & \\multicolumn{3}{c}{AR(2) fitted rate} \\\\",
         "\\cmidrule(lr){2-4} \\cmidrule(lr){5-7}",
         " & " + " & ".join(f"({i})" for i in range(1, k + 1)) + " \\\\",
         "Dependent variable & Net growth & Net growth & Log growth & "
         "Net growth & Net growth & Log growth \\\\"]

    for i, (name, res) in enumerate(results.items()):
        models = list(res["realized"].values()) + list(res["fitted"].values())
        L += ["\\midrule",
              f"\\multicolumn{{{k + 1}}}{{l}}{{\\textit{{Panel {chr(65 + i)}: {name}}}}} \\\\"]
        for lab, terms in rows:
            cs = [_coef(m, terms, d) for m in models]
            L.append(f"{lab} & " + " & ".join(c for c, _ in cs) + " \\\\")
            L.append(" & " + " & ".join(s for _, s in cs) + " \\\\")
        L.append("Observations & " + " & ".join(f"{int(m.nobs):,}" for m in models) + " \\\\")
        L.append("$R^2$ & " + " & ".join(f"{m.rsquared:.3f}" for m in models) + " \\\\")
        L.append("Clusters (intervals) & "
                 + " & ".join([str(panels[name]["YEAR"].nunique())] * k) + " \\\\")

    wnote = ("Regressions are weighted by the PSID family weight of the wave that ends each "
             "interval. " if weight_col else "")
    notes = (
        "Source: Panel Study of Income Dynamics, family-level panel, heads aged "
        f"{ages}. The dependent variable is the annualized growth of real total family "
        f"expenditure ({base_year} dollars) between consecutive biennial waves, either the "
        "net rate (net growth) or the log change divided by two (log growth); intervals end "
        f"in {first} to {last}. {wnote}The regressor is the US real interest rate averaged "
        "over the years spanned by each interval, in net form or as the log gross rate "
        "$\\ln(1+r)$ (World Development Indicators, FRED for 2022 and 2023). In columns (4) "
        "to (6) it is replaced by the fitted value of an AR(2) in the annual log gross real "
        "rate. Panel B keeps households headed by a man in both waves. Standard errors "
        "clustered by interval in parentheses. $^{*}p<0.1$, $^{**}p<0.05$, $^{***}p<0.01$. "
        "The regressor varies only across intervals, so identification rests on a handful of "
        "values and the stars are likely overstated; standard errors for columns (4) to (6) "
        "ignore first-stage estimation error. Under CRRA preferences the slope in columns "
        "(3) and (6) estimates the elasticity of intertemporal substitution.")
    L += ["\\bottomrule", "\\end{tabular}", "\\begin{tablenotes}\\footnotesize",
          f"\\item \\textit{{Notes:}} {notes}", "\\end{tablenotes}",
          "\\end{threeparttable}", "\\end{table}"]
    return "\n".join(L) + "\n"


euler_tex = euler_latex(euler_results, euler_samples)
print(euler_tex)
# Path("../tables/euler_regressions.tex").write_text(euler_tex)
# %%