"""
Problem Set 1: Survey of Consumer Finances (SCF) 2016, 2019, and 2022.

Part A: weighted summary statistics, group comparisons, and LaTeX tables.
Part B: life-cycle profiles by age, quartic age regressions, and fitted profiles.

Both parts share one data pipeline (load_wave / load_all): dollar variables deflated
to 2022 dollars wave by wave, harmonized race coding, and a pooled 2016-2022 sample.
Cells are delimited by "# %%" for use in VS Code, Spyder, or PyCharm.
"""

# %% Imports and paths
import re
from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.iolib.summary2 import summary_col

# locate the workspace root (folder containing .workspace-root); override with ECON_ROOT
import os
ROOT = Path(os.environ.get("ECON_ROOT") or next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / ".workspace-root").exists()))
data_dir = (ROOT / "data/survey_of_consumer_finance")
figs_dir = (ROOT / "problem-sets/ps1/figs")
figs_dir.mkdir(parents=True, exist_ok=True)

files = {2016: data_dir / "SCFP2016.csv",
         2019: data_dir / "SCFP2019.csv",
         2022: data_dir / "SCFP2022.csv"}

# %% Settings and shared library
# ---------------------------------------------------------------- settings
dollar_vars = ["WAGEINC", "LIQ", "NETWORTH"]
demo_vars = ["HHSEX", "AGE", "EDUC", "RACE"]
continuous_demo = ["AGE"]                       # demo vars treated as continuous
categorical_vars = [v for v in demo_vars if v not in continuous_demo]
continuous_vars = dollar_vars + continuous_demo

pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
scale = 1_000
base_year = 2022

CPI = {2016: 240.007, 2019: 255.657, 2022: 292.655}
deflator = {y: CPI[base_year] / CPI[y] for y in CPI}

# The 2022 SCF split "Asian" (RACE code 4) out of "Other" (code 5); in 2016 and 2019 Asian
# households are inside "Other". True merges code 4 into code 5 so every wave is comparable;
# False shows Asian separately for 2022 only ("Other" is then not comparable across waves).
# The pooled sample requires True.
harmonize_race = True

race_labels = {1: "White non-Hispanic", 2: "Black/African American", 3: "Hispanic/Latino"}
race_labels.update({5: "Other (incl. Asian)"} if harmonize_race
                   else {4: "Asian", 5: "Other"})
race_note = ("Asian households are included in Other in all waves, since the 2022 survey "
             "first identified Asian separately." if harmonize_race else
             "Asian is identified separately only from the 2022 survey; in 2016 and 2019 "
             "Asian households are included in Other, so the Other category is not "
             "comparable across waves.")

# Optional labels; verify against each year's codebook. Unlisted codes print as numbers.
labels = {"HHSEX": {1: "Male", 2: "Female"}, "RACE": race_labels}

# ---------------------------------------------------------------- pooled sample
POOLED = "Pooled"


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
    """All statistics for one implicate; x, w are 1-d float arrays."""
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


# ---------------------------------------------------------------- one wave and pooled
def load_wave(path, year, harmonize=None):
    d = pd.read_csv(path)
    d.columns = d.columns.str.upper()
    d["YEAR"] = year
    d["IMP"] = d["Y1"] - 10 * d["YY1"]          # implicate 1..5
    d["W"] = d["WGT"] / 5                       # weights sum to population
    if harmonize_race if harmonize is None else harmonize:
        d["RACE"] = d["RACE"].replace(4, 5)     # fold Asian (2022 only) into Other
    for v in dollar_vars:
        d[v] = d[v] * deflator[year]
    return d


def load_all(files, pooled=True):
    """{year: frame} plus a Pooled frame (stacked waves, weights divided by number of waves).
    Dollar variables are deflated wave by wave before stacking."""
    waves = {yr: load_wave(p, yr) for yr, p in files.items()}
    if pooled:
        assert harmonize_race, ("Pooling requires harmonize_race = True "
                                "(Other is not comparable otherwise).")
        d = pd.concat(waves.values(), axis=0, ignore_index=True)   # unique index for add_groups
        d["W"] = d["W"] / len(waves)
        waves[POOLED] = d
    return waves


def summarize_continuous(d, variables=continuous_vars):
    """Statistics within each implicate, then averaged across the five implicates."""
    rows = {}
    for v in variables:
        per_imp = pd.DataFrame([wstats(g[v].to_numpy(float), g["W"].to_numpy(float))
                                for _, g in d.groupby("IMP")])
        s = per_imp.mean()
        if v in dollar_vars:                    # thousands of base-year dollars
            keep = ["Skewness", "Kurtosis"]
            s = s.copy()
            for k in s.index:
                if k == "Variance":
                    s[k] /= scale**2
                elif k not in keep:
                    s[k] /= scale
        rows[v] = s
    return pd.DataFrame(rows).T


def summarize_categorical(d, variables=categorical_vars):
    """Weighted population shares (percent) by category, averaged across implicates."""
    out = {}
    for v in variables:
        sh = pd.DataFrame({m: g.groupby(v)["W"].sum() / g["W"].sum() * 100
                           for m, g in d.groupby("IMP")}).fillna(0).mean(axis=1)
        sh.index = [labels.get(v, {}).get(int(c), int(c)) for c in sh.index]
        out[v] = sh
    return pd.concat(out, names=["Variable", "Category"])


def summarize_all(files, pooled=True):
    """files: {year: path}. Returns (continuous, categorical) long frames; Pooled column last."""
    cont, cat = {}, {}
    for yr, d in load_all(files, pooled).items():
        cont[yr] = summarize_continuous(d)
        cat[yr] = summarize_categorical(d)
    cont = pd.concat(cont, names=["Year", "Variable"]).swaplevel().loc[continuous_vars]
    latest = max(k for k in cat if k != POOLED)
    order = list(cat[latest].index)             # latest wave lists every category, in code order
    cat = pd.concat(cat, axis=1, sort=False)    # rows (Variable, Category); NaN = not in wave
    cat = cat.reindex(order + [i for i in cat.index if i not in order])
    cat.columns.name = "Year"
    return cont, cat


# ---------------------------------------------------------------- group comparisons
age_bins = [0, 35, 45, 55, 65, 75, 200]
age_labels = ["Under 35", "35-44", "45-54", "55-64", "65-74", "75 and over"]
edu_labels = ["Less than high school", "High school or GED",
              "Some college or associate", "Bachelor's degree or more"]
# EDUC codes 1-14 collapsed to four groups; verify against the codebook (cf. EDCL).
edu_map = {**{k: edu_labels[0] for k in range(1, 8)}, 8: edu_labels[1],
           **{k: edu_labels[2] for k in (9, 10, 11)},
           **{k: edu_labels[3] for k in (12, 13, 14)}}

group_order = {"Age of head": age_labels,
               "Education of head": edu_labels,
               "Race/ethnicity": list(labels["RACE"].values()),
               "Sex of head": list(labels["HHSEX"].values())}


def add_groups(d, race_map=None):
    g = pd.DataFrame(index=d.index)
    g["Age of head"] = pd.cut(d["AGE"], age_bins, labels=age_labels, right=False)
    g["Education of head"] = d["EDUC"].map(edu_map)
    g["Race/ethnicity"] = d["RACE"].map(race_map or labels["RACE"])
    g["Sex of head"] = d["HHSEX"].map(labels["HHSEX"])
    return g


def group_stats(d, variables=dollar_vars):
    """Weighted mean, median, variance, and std. dev. by group, averaged across implicates."""
    grp = add_groups(d)
    rec = []
    for m, g in d.groupby("IMP"):
        gg, w = grp.loc[g.index], g["W"].to_numpy(float)
        cells = [("All households", "All households", np.ones(len(g), bool))]
        cells += [(dim, lab, (gg[dim] == lab).to_numpy())
                  for dim, labs in group_order.items() for lab in labs]
        for dim, lab, mask in cells:
            if mask.sum() == 0:
                continue
            for v in variables:
                x, ww = g[v].to_numpy(float)[mask], w[mask]
                mu = np.average(x, weights=ww)
                var = np.average((x - mu) ** 2, weights=ww)
                rec.append((m, dim, lab, v, mu, wquantile(x, ww, 0.5), var, np.sqrt(var)))
    cols = ["Mean", "Median", "Variance", "Std. dev."]
    df = pd.DataFrame(rec, columns=["IMP", "Dimension", "Group", "Variable"] + cols)
    out = df.groupby(["Dimension", "Group", "Variable"])[cols].mean()
    out[["Mean", "Median", "Std. dev."]] /= scale      # thousands of base-year dollars
    out["Variance"] /= scale**2                        # squared thousands
    return out


def build_group_tables(files, pooled=True):
    """Long frame indexed by (Year, Dimension, Group, Variable); thousands of base-year $."""
    return pd.concat({yr: group_stats(d) for yr, d in load_all(files, pooled).items()},
                     names=["Year"])


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


_src = ("Source: Federal Reserve Board, Survey of Consumer Finances Summary Extract. "
        "Statistics are weighted by the sampling weight, computed within each of the five "
        "implicates and averaged across implicates. Waves are independent cross-sections. "
        "The pooled sample stacks the 2016, 2019, and 2022 waves, with dollar values "
        "deflated wave by wave before stacking and weights divided by the number of waves.")


def latex_by_variable(cont, var):
    """Rows = statistics, columns = years (Pooled last), for one continuous variable."""
    if var in dollar_vars:
        unit = f"thousands of {base_year} dollars, except skewness and kurtosis"
        extra = (f" Dollar values are deflated to {base_year} dollars. Kurtosis is the "
                 "raw (non-excess) fourth standardized moment.")
    else:
        unit = "years, except skewness and kurtosis"
        extra = " Kurtosis is the raw (non-excess) fourth standardized moment."
    return _tex(cont.loc[var].T, f"Weighted summary statistics for {var} ({unit})",
                f"tab:scf_{var.lower()}", _src + extra)


def latex_by_year(cont, year):
    """Rows = variables, columns = statistics, for one year (or POOLED)."""
    cap = ("Weighted summary statistics, SCF 2016, 2019, and 2022 pooled" if year == POOLED
           else f"Weighted summary statistics, SCF {year}")
    return _tex(cont.xs(year, level="Year"), cap,
                f"tab:scf_{_slug_label(year)}",
                _src + f" Dollar variables are in thousands of {base_year} dollars; "
                "AGE is in years. Kurtosis is the raw fourth standardized moment.")


def latex_shares(cat, var):
    """Weighted population shares (percent) of a categorical variable, by year."""
    return _tex(cat.loc[var], f"Weighted population shares of {var} (percent)",
                f"tab:scf_{var.lower()}_shares",
                _src + (" " + race_note if var == "RACE" else ""), fmt="%.1f")


def latex_group_table(big, var, stats=("Mean", "Median", "Variance")):
    """Group statistics of `var`, one column block per year (Pooled last), panels by dimension.
    stats may be any of "Mean", "Median", "Variance", "Std. dev."."""
    t = big.xs(var, level="Variable")
    years = _ysort(t.index.get_level_values("Year").unique())
    k = len(stats)
    ncol = 1 + k * len(years)

    def cells(dim, lab):
        out = []
        for y in years:
            try:
                r = t.loc[(y, dim, lab)]
                out += [f"{r[c]:,.1f}" for c in stats]
            except KeyError:
                out += ["--"] * k
        return " & ".join(out)

    unit = (f"thousands of {base_year} dollars; variance in squared thousands"
            if "Variance" in stats else f"thousands of {base_year} dollars")
    L = ["\\begin{table}[htbp]", "\\centering",
         f"\\caption{{{var} by household characteristics ({unit})}}",
         f"\\label{{tab:scf_{var.lower()}_groups}}", "\\begin{threeparttable}",
         "\\begin{tabular}{l" + "r" * (k * len(years)) + "}", "\\toprule",
         " & " + " & ".join(f"\\multicolumn{{{k}}}{{c}}{{{y}}}" for y in years) + " \\\\"]
    L.append(" ".join(f"\\cmidrule(lr){{{2 + k*i}-{1 + k*(i+1)}}}" for i in range(len(years))))
    L.append("Group & " + " & ".join([" & ".join(stats)] * len(years)) + " \\\\")
    L += ["\\midrule", "All households & " + cells("All households", "All households") + " \\\\"]
    for dim, labs in group_order.items():
        L += ["\\midrule", f"\\multicolumn{{{ncol}}}{{l}}{{\\textit{{{dim}}}}} \\\\"]
        L += [f"\\hspace{{1em}}{lab} & " + cells(dim, lab) + " \\\\" for lab in labs]
    L += ["\\bottomrule", "\\end{tabular}", "\\begin{tablenotes}\\footnotesize",
          f"\\item \\textit{{Notes:}} {_src} Dollar values are deflated to {base_year} dollars. "
          "Variance is the weighted population variance within the group. "
          "Age, education, race/ethnicity, and sex refer to the head of the primary economic unit. "
          + race_note,
          "\\end{tablenotes}", "\\end{threeparttable}", "\\end{table}"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- two-way comparisons
def group_stats_2way(d, panel, row, variables=dollar_vars, race_map=None):
    """Weighted stats for each (panel group, row group) cell, averaged across implicates.
    panel, row: keys of group_order, e.g. "Race/ethnicity", "Age of head"."""
    grp = add_groups(d, race_map)
    order = dict(group_order)
    if race_map:
        order["Race/ethnicity"] = list(race_map.values())
    rec = []
    for m, g in d.groupby("IMP"):
        gg, w = grp.loc[g.index], g["W"].to_numpy(float)
        for pl in order[panel]:
            for rl in order[row]:
                mask = ((gg[panel] == pl) & (gg[row] == rl)).to_numpy()
                if mask.sum() == 0:
                    continue
                for v in variables:
                    x, ww = g[v].to_numpy(float)[mask], w[mask]
                    mu = np.average(x, weights=ww)
                    var = np.average((x - mu) ** 2, weights=ww)
                    rec.append((m, pl, rl, v, mu, wquantile(x, ww, 0.5), var,
                                np.sqrt(var), mask.sum(), 100 * w[mask].sum() / w.sum()))
    cols = ["Mean", "Median", "Variance", "Std. dev.", "N", "Share"]
    df = pd.DataFrame(rec, columns=["IMP", "Panel", "Row", "Variable"] + cols)
    out = df.groupby(["Panel", "Row", "Variable"])[cols].mean()
    out[["Mean", "Median", "Std. dev."]] /= scale
    out["Variance"] /= scale**2
    return out


def build_two_way_tables(files, panel, row, pooled=True):
    """Long frame indexed by (Year, Panel, Row, Variable). N is the unweighted cell count."""
    return pd.concat({yr: group_stats_2way(d, panel, row)
                      for yr, d in load_all(files, pooled).items()}, names=["Year"])


def latex_two_way_table(big2, var, panel, row, stats=("Mean", "Median", "Variance"), min_n=30):
    """`var` by `row` groups within each `panel` group (Pooled last). Cells with fewer than
    min_n unweighted observations are suppressed."""
    t = big2.xs(var, level="Variable")
    years = _ysort(t.index.get_level_values("Year").unique())
    k = len(stats)
    ncol = 1 + k * len(years)

    def cells(pl, rl):
        out = []
        for y in years:
            try:
                r = t.loc[(y, pl, rl)]
                out += [f"{r[c]:,.1f}" for c in stats] if r["N"] >= min_n else ["--"] * k
            except KeyError:
                out += ["--"] * k
        return " & ".join(out)

    unit = (f"thousands of {base_year} dollars; variance in squared thousands"
            if "Variance" in stats else f"thousands of {base_year} dollars")
    slug = lambda z: z.split("/")[0].split()[0].lower()
    L = ["\\begin{table}[htbp]", "\\centering",
         f"\\caption{{{var} by {row.lower()} within {panel.lower()} groups ({unit})}}",
         f"\\label{{tab:scf_{var.lower()}_{slug(panel)}_{slug(row)}}}", "\\begin{threeparttable}",
         "\\begin{tabular}{l" + "r" * (k * len(years)) + "}", "\\toprule",
         " & " + " & ".join(f"\\multicolumn{{{k}}}{{c}}{{{y}}}" for y in years) + " \\\\"]
    L.append(" ".join(f"\\cmidrule(lr){{{2 + k*i}-{1 + k*(i+1)}}}" for i in range(len(years))))
    L.append(f"{row} & " + " & ".join([" & ".join(stats)] * len(years)) + " \\\\")
    for pl in group_order[panel]:
        L += ["\\midrule", f"\\multicolumn{{{ncol}}}{{l}}{{\\textit{{{pl}}}}} \\\\"]
        L += [f"\\hspace{{1em}}{rl} & " + cells(pl, rl) + " \\\\" for rl in group_order[row]]
    L += ["\\bottomrule", "\\end{tabular}", "\\begin{tablenotes}\\footnotesize",
          f"\\item \\textit{{Notes:}} {_src} Dollar values are deflated to {base_year} dollars. "
          "Variance is the weighted population variance within the cell. "
          f"Cells with fewer than {min_n} unweighted observations are suppressed (--). "
          "Characteristics refer to the head of the primary economic unit. " + race_note,
          "\\end{tablenotes}", "\\end{threeparttable}", "\\end{table}"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- single-wave cross-sections
race_order_all = ["White non-Hispanic", "Black/African American", "Hispanic/Latino",
                  "Asian", "Other", "Other (incl. Asian)"]


def build_cross_section(path, year, panel, row):
    """Two-way statistics for ONE wave, using that wave's own race coding: Asian is a
    separate category in 2022 and is inside Other in 2016 and 2019."""
    d = load_wave(path, year, harmonize=False)
    rm = {1: "White non-Hispanic", 2: "Black/African American", 3: "Hispanic/Latino"}
    if (d["RACE"] == 4).any():
        rm.update({4: "Asian", 5: "Other"})
    else:
        rm[5] = "Other (incl. Asian)"
    return group_stats_2way(d, panel, row, race_map=rm)


def build_pooled_cross_section(files, panel, row):
    """Two-way statistics on the pooled sample, with harmonized race coding."""
    d = load_all(files, pooled=True)[POOLED]
    return group_stats_2way(d, panel, row)


def latex_cross_section_table(tab, panel, row, year, variables=dollar_vars,
                              stats=("Mean", "Median", "Variance"), show_share=True, min_n=30):
    """Single-sample table: `row` groups within each `panel` group, one column block per
    variable. `year` is a wave (2016, 2019, 2022) or POOLED. Cells with fewer than min_n
    unweighted observations are suppressed."""
    k, nv = len(stats), len(variables)
    present = lambda lvl: set(tab.index.get_level_values(lvl))

    def order(dim, lvl):
        base = race_order_all if dim == "Race/ethnicity" else group_order[dim]
        return [x for x in base if x in present(lvl)]
    panels, rows = order(panel, "Panel"), order(row, "Row")
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

    pooled = year == POOLED
    asian = "Asian" in present("Panel") | present("Row")
    if pooled:
        note = ("Asian households are included in Other in all waves, since Asian was not "
                "identified separately before the 2022 survey.")
    elif asian:
        note = "Asian is identified separately beginning with the 2022 survey."
    else:
        note = ("Asian households are included in Other, since Asian was not identified "
                "separately before the 2022 survey.")
    sample = "SCF 2016, 2019, and 2022 pooled" if pooled else f"SCF {year}"
    slug = lambda z: z.split("/")[0].split()[0].lower()
    unit = (f"thousands of {base_year} dollars; variance in squared thousands"
            if "Variance" in stats else f"thousands of {base_year} dollars")
    L = ["\\begin{table}[htbp]", "\\centering",
         f"\\caption{{Weighted statistics by {panel.lower()} and {row.lower()}, {sample} ({unit})}}",
         f"\\label{{tab:scf_{_slug_label(year)}_{slug(panel)}_{slug(row)}}}",
         "\\begin{threeparttable}",
         "\\setlength{\\tabcolsep}{4pt}", "\\resizebox{\\textwidth}{!}{%",
         "\\begin{tabular}{l" + "r" * (sh + k * nv) + "}", "\\toprule",
         " & ".join([""] + [""] * sh + [f"\\multicolumn{{{k}}}{{c}}{{{v}}}" for v in variables]) + " \\\\"]
    L.append(" ".join(f"\\cmidrule(lr){{{2 + sh + k*i}-{1 + sh + k*(i+1)}}}" for i in range(nv)))
    L.append(" & ".join([row] + (["Share (\\%)"] if show_share else []) + list(stats) * nv) + " \\\\")
    for pl in panels:
        L += ["\\midrule", f"\\multicolumn{{{ncol}}}{{l}}{{\\textit{{{pl}}}}} \\\\"]
        L += [f"\\hspace{{1em}}{rl} & " + cells(pl, rl) + " \\\\" for rl in rows]
    L += ["\\bottomrule", "\\end{tabular}}", "\\begin{tablenotes}\\footnotesize",
          f"\\item \\textit{{Notes:}} {_src} Dollar values are deflated to {base_year} dollars. "
          "Share is the weighted percentage of all households in the cell. "
          "Variance is the weighted population variance within the cell. "
          f"Cells with fewer than {min_n} unweighted observations are suppressed (--). "
          "Characteristics refer to the head of the primary economic unit. " + note,
          "\\end{tablenotes}", "\\end{threeparttable}", "\\end{table}"]
    return "\n".join(L) + "\n"

# %% ======================= PART A: SUMMARY STATISTICS AND LATEX TABLES =======================
cont, cat = summarize_all(files)

print(cont.loc["WAGEINC"].T)        # moments and percentiles by year
print(cat.loc["RACE"])

# %% Summary statistics by variable
for v in ["NETWORTH", "WAGEINC", "LIQ", "AGE"]:
    print(latex_by_variable(cont, v))

# %% Population shares
for v in ["EDUC", "HHSEX", "RACE"]:
    print(latex_shares(cat, v))

# %% Group comparisons (age, education, race, sex of head)
big = build_group_tables(files)
for v in ["WAGEINC", "LIQ", "NETWORTH"]:
    print(latex_group_table(big, v))

# %% Male-headed households, pooled sample
def pooled_subsample(files, col="HHSEX", value=1):
    """Pooled sample (deflated, race harmonized, weights / 3) restricted to col == value."""
    d = load_all(files, pooled=True)[POOLED]
    return d[d[col] == value].copy()


def _tag(tex, who):
    """Add the subsample to the caption and notes of a generated table."""
    tex = tex.replace("\\caption{", f"\\caption{{{who}: ", 1)
    return tex.replace("\\item \\textit{Notes:} ",
                       f"\\item \\textit{{Notes:}} Sample restricted to {who}. ", 1)


who = "male-headed households (HHSEX = 1), SCF 2016, 2019, and 2022 pooled"
dm = pooled_subsample(files)

# Table 1: full distribution statistics, one column per variable
cont_m = summarize_continuous(dm, dollar_vars)          # rows = variables, cols = statistics
print(_tag(_tex(cont_m.T,
                f"Weighted summary statistics (thousands of {base_year} dollars, "
                "except skewness and kurtosis)",
                "tab:scf_pooled_male_summary",
                _src + f" Dollar values are deflated to {base_year} dollars. "
                "Kurtosis is the raw (non-excess) fourth standardized moment."), who))

# Tables 2-4: mean, median, variance by household characteristics, one table per variable
big_m = pd.concat({POOLED: group_stats(dm)}, names=["Year"])
for v in dollar_vars:
    print(_tag(latex_group_table(big_m, v), who))

# %% Male-headed households: education by race, pooled sample
dm = pooled_subsample(files)                       # pooled, HHSEX = 1 (defined earlier)
tab_m = group_stats_2way(dm, "Race/ethnicity", "Education of head")

tex = latex_cross_section_table(tab_m, "Race/ethnicity", "Education of head", POOLED)
tex = tex.replace("\\caption{", "\\caption{Male-headed households (HHSEX = 1): ", 1)
tex = tex.replace("\\item \\textit{Notes:} ",
                  "\\item \\textit{Notes:} Sample restricted to male-headed households "
                  "(HHSEX = 1). Share is the weighted percentage of all male-headed "
                  "households in the cell. ", 1)
print(tex)



# %% ======================= PART B: LIFE-CYCLE PROFILES AND QUARTIC REGRESSIONS =======================
# Data come from the same pipeline as Part A (deflated dollars, harmonized race).
# WGT is kept as the household weight; scaling by the number of implicates or waves
# does not affect weighted medians or WLS point estimates.
waves = load_all(files)
df2016, df2019, df2022, jointpooled = waves[2016], waves[2019], waves[2022], waves[POOLED]
POOLED_YEAR = 6057          # sentinel year used for the pooled sample in profile frames


def weighted_median(group, variable):
    d = group[[variable, "WGT"]].dropna()
    return wquantile(d[variable].to_numpy(float), d["WGT"].to_numpy(float), 0.5)


def create_profile(df, year, group_variable=None):
    """Weighted medians of labor income, wealth, and liquid wealth by age (and group)."""
    group_cols = ["AGE"] if group_variable is None else ["AGE", group_variable]
    profile = df.groupby(group_cols, observed=True).apply(
        lambda g: pd.Series({
            "labor_income": weighted_median(g, "WAGEINC"),
            "wealth": weighted_median(g, "NETWORTH"),
            "liquid_wealth": weighted_median(g, "LIQ"),
            "n_obs": g["LIQ"].notna().sum(),
            "weight": g.loc[g["LIQ"].notna(), "WGT"].sum()}),
        include_groups=False)
    profile["YEAR"] = year
    return profile.reset_index()


def add_profile_groups(df):
    """Education (shared edu_map), race, and sex group labels for the profile plots."""
    df = df.copy()
    df["EDUC_GROUP"] = pd.Categorical(df["EDUC"].clip(lower=1).map(edu_map),
                                      categories=edu_labels, ordered=True)
    df["RACE_GROUP"] = df["RACE"].map({1: "White non-Hispanic", 2: "Black",
                                       3: "Hispanic", 4: "Other", 5: "Other"})
    df["HHSEX_GROUP"] = df["HHSEX"].map(labels["HHSEX"])
    return df


samples = {"2016": (2016, df2016), "2019": (2019, df2019),
           "2022": (2022, df2022), "All Pooled": (POOLED_YEAR, jointpooled)}
samples = {k: (y, add_profile_groups(d)) for k, (y, d) in samples.items()}
df2016, df2019, df2022, jointpooled = (samples[k][1] for k in samples)


def build_profiles(group_variable):
    return pd.concat([create_profile(d, y, group_variable) for y, d in samples.values()],
                     ignore_index=True)


profile_educ = build_profiles("EDUC_GROUP")
profile_race = build_profiles("RACE_GROUP")
profile_frames = {k: create_profile(d, y, "HHSEX_GROUP") for k, (y, d) in samples.items()}
profile = pd.concat(profile_frames.values(), ignore_index=True)

# %% Profile plots
sns.set_theme(style="whitegrid", font="Latin Modern Roman")
year_label = {2016: "2016", 2019: "2019", 2022: "2022", POOLED_YEAR: "All Pooled"}
outcomes = {"labor_income": ("Labor Income", "WAGEINC"),
            "wealth": ("Wealth", "NETWORTH"),
            "liquid_wealth": ("Liquid Wealth", "LIQ")}


def plot_profile(data, col, hue, title, ylabel, fname, legend_title, min_n=None):
    d = data if min_n is None else data[data["n_obs"] >= min_n]
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.lineplot(data=d, x="AGE", y=col, hue=hue, marker="o", ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Age")
    ax.set_ylabel(ylabel)
    ax.legend(title=legend_title)
    fig.savefig(figs_dir / fname, format="pdf", bbox_inches="tight")
    plt.show()


by_year = profile.assign(SAMPLE=profile["YEAR"].map(year_label))
pooled_sex = profile[profile["YEAR"] == POOLED_YEAR]
pooled_race = profile_race[profile_race["YEAR"] == POOLED_YEAR]
pooled_educ = profile_educ[profile_educ["YEAR"] == POOLED_YEAR]

for col, (name, var) in outcomes.items():
    # Labor income plots were unfiltered by cell size except by sex; the filter is kept as in the originals.
    mn = None if col == "labor_income" else 20
    plot_profile(by_year, col, "SAMPLE", f"(Weighted) Median {name} by Age", var,
                 f"problemset1_{col}_by_age_sfc.pdf", "Survey year", mn)
    plot_profile(pooled_race, col, "RACE_GROUP",
                 f"(Weighted) Median {name} by Age and Race, All Pooled", var,
                 f"problemset1_{col}_by_age_race_pooled_sfc.pdf", "Race", mn)
    plot_profile(pooled_educ, col, "EDUC_GROUP",
                 f"(Weighted) Median {name} by Age and Education, All Pooled", var,
                 f"problemset1_{col}_by_age_education_pooled_sfc.pdf", "Education", mn)
    plot_profile(pooled_sex, col, "HHSEX_GROUP",
                 f"(Weighted) Median {name} by Age and Household Head's Sex, All Pooled", var,
                 f"problemset1_{col}_by_age_hhsex_sfc.pdf", "Sex of head", 20)


# %% Profile plots: male-headed households only (HHSEX = 1)
samples_m = {k: (y, d[d["HHSEX"] == 1].copy()) for k, (y, d) in samples.items()}


def build_profiles_m(group_variable=None):
    return pd.concat([create_profile(d, y, group_variable) for y, d in samples_m.values()],
                     ignore_index=True)


by_year_m = build_profiles_m().assign(SAMPLE=lambda p: p["YEAR"].map(year_label))
pooled_race_m = build_profiles_m("RACE_GROUP").query("YEAR == @POOLED_YEAR")
pooled_educ_m = build_profiles_m("EDUC_GROUP").query("YEAR == @POOLED_YEAR")

for col, (name, var) in outcomes.items():
    mn = None if col == "labor_income" else 20      # same cell-size convention as above
    plot_profile(by_year_m, col, "SAMPLE",
                 f"(Weighted) Median {name} by Age, Male Heads", var,
                 f"problemset1_{col}_by_age_male_sfc.pdf", "Survey year", mn)
    plot_profile(pooled_race_m, col, "RACE_GROUP",
                 f"(Weighted) Median {name} by Age and Race, Male Heads, All Pooled", var,
                 f"problemset1_{col}_by_age_race_pooled_male_sfc.pdf", "Race", mn)
    plot_profile(pooled_educ_m, col, "EDUC_GROUP",
                 f"(Weighted) Median {name} by Age and Education, Male Heads, All Pooled", var,
                 f"problemset1_{col}_by_age_education_pooled_male_sfc.pdf", "Education", mn)


# %% Quartic age regressions
power_cols = ["age_power1", "age_power2", "age_power3", "age_power4"]


def quartic_regression(data, outcome, male_only=True, controls=True,
                       year_fe=False, cov_type=None):
    """WLS of `outcome` on a quartic in age, restricted to male heads (HHSEX = 1),
    with education and race/ethnicity of the head as categorical controls."""
    d = data[data["HHSEX"] == 1].copy() if male_only else data.copy()

    for k in range(1, 5):                                    # build age powers if absent
        if f"age_power{k}" not in d:
            d[f"age_power{k}"] = d["AGE"].astype(float) ** k
    X = d[power_cols].astype(float)

    if controls:
        edu = pd.Categorical(d["EDUC"].clip(lower=1).map(edu_map), categories=edu_labels)
        race = pd.Categorical(d["RACE"].replace(4, 5).map(labels["RACE"]),
                              categories=list(labels["RACE"].values()))
        C = pd.get_dummies(pd.DataFrame({"EDU": edu, "RACE": race}, index=d.index),
                           drop_first=True, dtype=float)
        X = pd.concat([X, C], axis=1)

    if year_fe:                                              # wave dummies, for pooled samples
        X = pd.concat([X, pd.get_dummies(d["YEAR"], prefix="YEAR",
                                         drop_first=True, dtype=float)], axis=1)

    X = sm.add_constant(X)
    model = sm.WLS(d[outcome], X, weights=d["WGT"])
    return model.fit(cov_type=cov_type) if cov_type else model.fit()


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
        "\\item \\textit{Notes:} Standard errors in parentheses. "
        "$^{*}p<0.1$, $^{**}p<0.05$, $^{***}p<0.01$. "
        "The last column stacks the 2016, 2019, and 2022 waves.\n"
        "\\end{tablenotes}\n\\end{threeparttable}\n\\end{table}\n")


reg_samples = {"2022": df2022, "2019": df2019, "2016": df2016, "All Pooled": jointpooled}
reg_specs = {"WAGEINC": ("labor income (WAGEINC)", "tab:scf_wageinc_quartic"),
             "NETWORTH": ("wealth (NETWORTH)", "tab:scf_networth_quartic"),
             "LIQ": ("liquid wealth (LIQ)", "tab:scf_liq_quartic")}

model_map = {name: {var: quartic_regression(d, var) for var in reg_specs}
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


hat_names = {"WAGEINC": "labor_income_hat", "NETWORTH": "wealth_hat", "LIQ": "liquid_wealth_hat"}
age_grid = np.arange(jointpooled["AGE"].min(), jointpooled["AGE"].max() + 1)

for name, prof in profile_frames.items():
    for var, res in model_map[name].items():
        prof[hat_names[var]] = prof["AGE"].map(predict_profile(res, age_grid))   # align on age

print(profile_frames["2022"].head())

# %% Predicted profiles by sample (quartic fits, controls at weighted means)
fitted = {s: {v: predict_profile(res, age_grid) for v, res in m.items()}
          for s, m in model_map.items()}
order = ["2016", "2019", "2022", "All Pooled"]

for col, (name, var) in outcomes.items():
    fig, ax = plt.subplots(figsize=(9, 6))
    for s in order:
        ax.plot(age_grid, fitted[s][var] / scale, label=s,
                linestyle="--" if s == "All Pooled" else "-",
                color="black" if s == "All Pooled" else None)
    ax.set_title(f"Predicted {name} by Age (Quartic Fit, Male Heads)")
    ax.set_xlabel("Age")
    ax.set_ylabel(f"{var}, thousands of {base_year} dollars")
    ax.legend(title="Sample")
    fig.savefig(figs_dir / f"problemset1_{col}_predicted_by_age_sfc.pdf",
                format="pdf", bbox_inches="tight")
    plt.show()
# %%
