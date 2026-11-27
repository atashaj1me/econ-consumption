# Workspace instructions for Claude

This file works for Claude Code, and can be pasted into a Claude Science project's
custom instructions.

ECON 312, Economics of Consumption (Fulbright University Vietnam). It's a single
workspace holding many small projects: labs, problem sets, papers and presentations.

## Layout
- `labs/<labN>/`, `problem-sets/<psN>/`, `papers/<slug>/`, `presentations/<slug>/`: one self-contained folder per project, each with a `README.md`. Start new ones from `templates/project/README.md`.
- `data/`: shared raw and processed datasets (CE Interview 2024, PSID, SCF, WDI). **Local only, never commit.**
- `pipelines/`: scripts that build shared data (for example `pipelines/psid/` writes to `data/psid/`).
- `course-materials/`: files from the instructor. Treat them as read-only.
- `**/archive/`: old submission packages. Local only.
- `.workspace-root`: a marker file at the root, used for path resolution.

## Conventions
- **Paths:** never use `../`-relative paths. Notebooks and scripts resolve the root like this:
  ```python
  ROOT = Path(os.environ.get("ECON_ROOT") or next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / ".workspace-root").exists()))
  ```
  then read `ROOT / "data/..."` and write figures to `ROOT / "<project>/figs"`. When code runs on a copy outside the repo (as in a Claude Science session workspace), set `ECON_ROOT` to this folder.
- Figures go in the project's own `figs/` as PDF, named `<project>_<variable>_by_<group>_<source>.pdf`.
- **Environment:** `environment.yml` / `requirements.txt` (Python 3.13: numpy, pandas, scipy, statsmodels, linearmodels, matplotlib, seaborn). The Claude Science starter environment lacks statsmodels and linearmodels, so use this environment.
- **LaTeX:** each paper or talk has a `Makefile` and a `.latexmkrc` (xelatex, aux files in `build/`). Run `make` in its folder. Only the `.tex`, `.bib`, `style/`, `graphs/` and the final PDF are committed.
- **Git:** the user commits and pushes from a terminal. Never add `data/`, `archive/`, zips or LaTeX build files.
- Write math in plain notation in chat. Use LaTeX only inside `.tex` files.
