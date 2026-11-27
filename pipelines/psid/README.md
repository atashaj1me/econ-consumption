# PSID pipeline

Builds the PSID family panel in `data/psid/` from a PSID data-center extract (fixed-width `.txt` + `.sas` setup file).

```bash
python pipelines/psid/psid_import.py
```

```bash
python pipelines/psid/build_psid_panel.py
```

1. `psid_import.py` parses the SAS setup and writes `data/psid/psid_output/` (wide CSV, variable dictionary, import report).
2. `build_psid_panel.py` reshapes the wide file into `data/psid/panel_output/psid_family_panel_long.csv`.

The default extract is `J366613` (override with `--sas`). Set `PSID_DIR` to use a data folder other than `data/psid/`.
