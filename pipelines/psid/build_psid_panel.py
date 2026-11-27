#!/usr/bin/env python3
"""Build a long family-wave panel from the PSID Data Center multi-wave extract J366613.

The script uses the selected variables in J366613.sas/J366613.txt (or the wide CSV
already produced by psid_import.py). It deliberately preserves numeric special
codes rather than guessing which codes mean missing; consult the PSID codebook and
format statements before econometric use.

Extract J366613: 718 variables, 33,440 records, 43 interview waves (1968-1997
annual, 1999-2023 biennial). Every one of the 718 variables is mapped to exactly
one wave and field in WAVES below, and the mapping was generated and checked
against the variable labels in J366613.sas (wave year, income reference year,
and field type).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import Any

import pandas as pd

# PSID files live in <workspace>/data/psid (override with PSID_DIR)
SCRIPT_DIR = Path(os.environ.get("PSID_DIR") or Path(__file__).resolve().parents[2] / "data" / "psid")
JOB = "J366613"

# Explicit wave-by-wave mapping. Keys are field codes (see FIELD_LABELS); values are
# PSID variable names present in the extract. A key is omitted in a wave when the
# extract has no matching variable for that wave. `labor` refers to the calendar year
# before the interview year, as indicated by the variable labels (e.g. the 2023
# interview reports 2022 income). From 2017 the PSID labels the head the "reference
# person"; the head_* columns hold the reference person in those waves.
WAVES: list[dict[str, Any]] = [
    dict(year=1968, release="V1", id="V3", family_size="V115", age="V117", sex="V119", race="V181", marital="V239", housing="V103", labor="V74"),
    dict(year=1969, release="V441", id="V442", family_size="V549", age="V1008", sex="V1010", race="V801", marital="V607", housing="V593", labor="V514"),
    dict(year=1970, release="V1101", id="V1102", family_size="V1238", age="V1239", sex="V1240", race="V1490", marital="V1365", housing="V1264", labor="V1196"),
    dict(year=1971, release="V1801", id="V1802", family_size="V1941", age="V1942", sex="V1943", race="V2202", marital="V2072", housing="V1967", labor="V1897"),
    dict(year=1972, release="V2401", id="V2402", family_size="V2541", age="V2542", sex="V2543", race="V2828", marital="V2670", housing="V2566", labor="V2498"),
    dict(year=1973, release="V3001", id="V3002", family_size="V3094", age="V3095", sex="V3096", race="V3300", marital="V3181", housing="V3108", labor="V3051"),
    dict(year=1974, release="V3401", id="V3402", family_size="V3507", age="V3508", sex="V3509", race="V3720", marital="V3598", housing="V3522", labor="V3463"),
    dict(year=1975, release="V3801", id="V3802", family_size="V3920", age="V3921", sex="V3922", race="V4204", marital="V4053", housing="V3939", labor="V3863", head_education_years="V4093", head_ba_degree="V4099"),
    dict(year=1976, release="V4301", id="V4302", family_size="V4435", age="V4436", sex="V4437", race="V5096", marital="V4603", housing="V4450", labor="V5031", head_education_years="V4684", head_ba_degree="V4690"),
    dict(year=1977, release="V5201", id="V5202", family_size="V5349", age="V5350", sex="V5351", race="V5662", marital="V5502", marital_generated="V5650", housing="V5364", labor="V5627", head_education_years="V5608", head_ba_degree="V5614"),
    dict(year=1978, release="V5701", id="V5702", family_size="V5849", age="V5850", sex="V5851", race="V6209", marital="V6034", marital_generated="V6197", housing="V5864", labor="V6174", head_education_years="V6157", head_ba_degree="V6163"),
    dict(year=1979, release="V6301", id="V6302", family_size="V6461", age="V6462", sex="V6463", race="V6802", marital="V6659", marital_generated="V6790", housing="V6479", labor="V6767", head_education_years="V6754", head_ba_degree="V6760"),
    dict(year=1980, release="V6901", id="V6902", family_size="V7066", age="V7067", sex="V7068", race="V7447", marital="V7261", marital_generated="V7435", housing="V7084", labor="V7413", head_education_years="V7387", head_ba_degree="V7393"),
    dict(year=1981, release="V7501", id="V7502", family_size="V7657", age="V7658", sex="V7659", race="V8099", marital="V7952", marital_generated="V8087", housing="V7675", labor="V8066", head_education_years="V8039", head_ba_degree="V8045"),
    dict(year=1982, release="V8201", id="V8202", family_size="V8351", age="V8352", sex="V8353", race="V8723", marital="V8603", marital_generated="V8711", housing="V8364", labor="V8690", head_education_years="V8663", head_ba_degree="V8669"),
    dict(year=1983, release="V8801", id="V8802", family_size="V8960", age="V8961", sex="V8962", race="V9408", marital="V9276", marital_generated="V9419", couple="V9421", housing="V8974", labor="V9376", head_education_years="V9349", head_ba_degree="V9355"),
    dict(year=1984, release="V10001", id="V10002", family_size="V10418", age="V10419", sex="V10420", race="V11055", marital="V10426", marital_generated="V11065", couple="V11067", housing="V10437", labor="V11023", wealth_no_home="S116", wealth_with_home="S117", head_education_years="V10996", head_ba_degree="V11002"),
    dict(year=1985, release="V11101", id="V11102", family_size="V11605", age="V11606", sex="V11607", race="V11938", race2="V11939", marital="V11612", marital_generated="V12426", couple="V12428", housing="V11618", labor="V12372", head_hs_graduate="V11945", head_ged_grade="V11948", head_attend_college="V11956", head_college_years="V11959", head_college_degree="V11960"),
    dict(year=1986, release="V12501", id="V12502", family_size="V13010", age="V13011", sex="V13012", race="V13565", race2="V13566", marital="V13017", marital_generated="V13665", couple="V13667", housing="V13023", labor="V13624", head_hs_graduate="V13568", head_ged_grade="V13571", head_attend_college="V13579", head_college_years="V13582", head_college_degree="V13583"),
    dict(year=1987, release="V13701", id="V13702", family_size="V14113", age="V14114", sex="V14115", race="V14612", race2="V14613", marital="V14120", marital_generated="V14712", couple="V14714", housing="V14126", labor="V14671", head_hs_graduate="V14615", head_ged_grade="V14618", head_attend_college="V14626", head_college_years="V14629", head_college_degree="V14630"),
    dict(year=1988, release="V14801", id="V14802", family_size="V15129", age="V15130", sex="V15131", race="V16086", race2="V16087", marital="V15136", marital_generated="V16187", couple="V16189", housing="V15140", labor="V16145", head_hs_graduate="V16089", head_ged_grade="V16092", head_attend_college="V16100", head_college_years="V16103", head_college_degree="V16104"),
    dict(year=1989, release="V16301", id="V16302", family_size="V16630", age="V16631", sex="V16632", race="V17483", race2="V17484", marital="V16637", marital_generated="V17565", couple="V17567", housing="V16641", labor="V17534", wealth_no_home="S216", wealth_with_home="S217", head_hs_graduate="V17486", head_ged_grade="V17489", head_attend_college="V17497", head_college_years="V17500", head_college_degree="V17501"),
    dict(year=1990, release="V17701", id="V17702", family_size="V18048", age="V18049", sex="V18050", race="V18814", race2="V18815", marital="V18055", marital_generated="V18916", couple="V18918", housing="V18072", labor="V18878", head_hs_graduate="V18817", head_ged_grade="V18820", head_attend_college="V18828", head_college_years="V18831", head_college_degree="V18832"),
    dict(year=1991, release="V19001", id="V19002", family_size="V19348", age="V19349", sex="V19350", race="V20114", race2="V20115", marital="V19355", marital_generated="V20216", couple="V20218", housing="V19372", labor="V20178", head_education_years="V20198", head_hs_graduate="V20117", head_ged_grade="V20120", head_attend_college="V20128", head_college_years="V20131", head_college_degree="V20132"),
    dict(year=1992, release="V20301", id="V20302", family_size="V20650", age="V20651", sex="V20652", race="V21420", race2="V21421", marital="V20657", marital_generated="V21522", couple="V21524", housing="V20672", labor="V21484", head_education_years="V21504", head_hs_graduate="V21423", head_ged_grade="V21426", head_attend_college="V21434", head_college_years="V21437", head_college_degree="V21438"),
    dict(year=1993, release="V21601", id="V21602", family_size="V22405", age="V22406", sex="V22407", race="V23276", race2="V23277", marital="V22412", marital_generated="V23336", couple="V23338", housing="V22427", labor="V23323", head_education_years="V23333", head_hs_graduate="V23279", head_ged_grade="V23282", head_attend_college="V23290", head_college_years="V23293", head_college_degree="V23294"),
    dict(year=1994, release="ER2001", id="ER2002", family_size="ER2006", age="ER2007", sex="ER2008", race="ER3944", race2="ER3945", marital="ER2014", marital_generated="ER4159A", couple="ER4159C", housing="ER2032", labor="ER4140", wealth_no_home="S316", wealth_with_home="S317", head_education_years="ER4158", head_hs_graduate="ER3948", head_ged_grade="ER3951", head_attend_college="ER3959", head_college_years="ER3962", head_college_degree="ER3963"),
    dict(year=1995, release="ER5001", id="ER5002", family_size="ER5005", age="ER5006", sex="ER5007", race="ER6814", race2="ER6815", marital="ER5013", marital_generated="ER6999A", couple="ER6999C", housing="ER5031", labor="ER6980", head_education_years="ER6998", head_hs_graduate="ER6818", head_ged_grade="ER6821", head_attend_college="ER6829", head_college_years="ER6832", head_college_degree="ER6833"),
    dict(year=1996, release="ER7001", id="ER7002", family_size="ER7005", age="ER7006", sex="ER7007", race="ER9060", race2="ER9061", marital="ER7013", marital_generated="ER9250A", couple="ER9250C", housing="ER7031", labor="ER9231", head_education_years="ER9249", head_hs_graduate="ER9064", head_ged_grade="ER9067", head_attend_college="ER9075", head_college_years="ER9078", head_college_degree="ER9079"),
    dict(year=1997, release="ER10001", id="ER10002", family_size="ER10008", age="ER10009", sex="ER10010", race="ER11848", race2="ER11849", ethnic="ER12165", marital="ER10016", marital_generated="ER12223A", couple="ER12223C", housing="ER10035", labor="ER12080", weight="ER12084", head_education_years="ER12222", head_hs_graduate="ER11854", head_ged_grade="ER11857", head_attend_college="ER11865", head_college_years="ER11868", head_college_degree="ER11869"),
    dict(year=1999, release="ER13001", id="ER13002", family_size="ER13009", age="ER13010", sex="ER13011", race="ER15928", race2="ER15929", ethnic="ER15932", marital="ER13021", marital_generated="ER16423", couple="ER16425", housing="ER13040", labor="ER16463", expenditure="ER16515D7", wealth_no_home="S416", wealth_with_home="S417", weight="ER16518", head_education_years="ER16516", head_hs_graduate="ER15937", head_ged_grade="ER15940", head_attend_college="ER15948", head_college_years="ER15951", head_college_degree="ER15952"),
    dict(year=2001, release="ER17001", id="ER17002", family_size="ER17012", age="ER17013", sex="ER17014", race="ER19989", race2="ER19990", ethnic="ER19993", marital="ER17024", marital_generated="ER20369", couple="ER20371", housing="ER17043", labor="ER20443", expenditure="ER20456D7", wealth_no_home="S516", wealth_with_home="S517", weight="ER20394", head_education_years="ER20457", head_hs_graduate="ER19998", head_ged_grade="ER20001", head_attend_college="ER20009", head_college_years="ER20012", head_college_degree="ER20013"),
    dict(year=2003, release="ER21001", id="ER21002", family_size="ER21016", age="ER21017", sex="ER21018", race="ER23426", race2="ER23427", ethnic="ER23430", marital="ER21023", marital_generated="ER24150", couple="ER24152", housing="ER21042", labor="ER24116", expenditure="ER24138D7", wealth_no_home="S616", wealth_with_home="S617", weight="ER24179", head_education_years="ER24148", head_hs_graduate="ER23435", head_ged_grade="ER23438", head_attend_college="ER23446", head_college_years="ER23449", head_college_degree="ER23450"),
    dict(year=2005, release="ER25001", id="ER25002", family_size="ER25016", age="ER25017", sex="ER25018", race="ER27393", race2="ER27394", ethnic="ER27397", marital="ER25023", marital_generated="ER28049", couple="ER28051", housing="ER25028", labor="ER27931", expenditure="ER28037E4", wealth_no_home="S716", wealth_with_home="S717", weight="ER28078", head_education_years="ER28047", head_hs_graduate="ER27402", head_ged_grade="ER27405", head_attend_college="ER27413", head_college_years="ER27416", head_college_degree="ER27417"),
    dict(year=2007, release="ER36001", id="ER36002", family_size="ER36016", age="ER36017", sex="ER36018", race="ER40565", race2="ER40566", ethnic="ER40569", marital="ER36023", marital_generated="ER41039", couple="ER41041", housing="ER36028", labor="ER40921", expenditure="ER41027E4", wealth_no_home="S816", wealth_with_home="S817", weight="ER41069", head_education_years="ER41037", head_hs_graduate="ER40574", head_ged_grade="ER40577", head_attend_college="ER40585", head_college_years="ER40588", head_college_degree="ER40589"),
    dict(year=2009, release="ER42001", id="ER42002", family_size="ER42016", age="ER42017", sex="ER42018", race="ER46543", race2="ER46544", ethnic="ER46547", marital="ER42023", marital_generated="ER46983", couple="ER46985", housing="ER42029", labor="ER46829", expenditure="ER46971E4", wealth_no_home="ER46968", wealth_with_home="ER46970", weight="ER47012", head_education_years="ER46981", head_hs_graduate="ER46552", head_ged_grade="ER46555", head_attend_college="ER46563", head_college_years="ER46566", head_college_degree="ER46567"),
    dict(year=2011, release="ER47301", id="ER47302", family_size="ER47316", age="ER47317", sex="ER47318", race="ER51904", race2="ER51905", ethnic="ER51908", marital="ER47323", marital_generated="ER52407", couple="ER52409", housing="ER47329", labor="ER52237", expenditure="ER52395E4", wealth_no_home="ER52392", wealth_with_home="ER52394", weight="ER52436", head_education_years="ER52405", head_hs_graduate="ER51913", head_ged_grade="ER51916", head_attend_college="ER51924", head_college_years="ER51927", head_college_degree="ER51928"),
    dict(year=2013, release="ER53001", id="ER53002", family_size="ER53016", age="ER53017", sex="ER53018", race="ER57659", race2="ER57660", ethnic="ER57663", marital="ER53023", marital_generated="ER58225", couple="ER58227", housing="ER53029", labor="ER58038", expenditure="ER58212E4", wealth_no_home="ER58209", wealth_with_home="ER58211", weight="ER58257", head_education_years="ER58223", head_hs_graduate="ER57669", head_ged_grade="ER57672", head_attend_college="ER57680", head_college_years="ER57683", head_college_degree="ER57684"),
    dict(year=2015, release="ER60001", id="ER60002", family_size="ER60016", age="ER60017", sex="ER60018", race="ER64810", race2="ER64811", ethnic="ER64815", marital="ER60024", marital_generated="ER65461", couple="ER65463", housing="ER60030", labor="ER65216", expenditure="ER65448B", wealth_no_home="ER65406", wealth_with_home="ER65408", weight="ER65492", head_education_years="ER65459", head_hs_graduate="ER64821", head_ged_grade="ER64824", head_attend_college="ER64832", head_college_years="ER64835", head_college_degree="ER64836"),
    dict(year=2017, release="ER66001", id="ER66002", family_size="ER66016", age="ER66017", sex="ER66018", race="ER70882", race2="ER70883", ethnic="ER70887", marital="ER66024", marital_generated="ER71540", couple="ER71542", housing="ER66030", labor="ER71293", expenditure="ER71527B", wealth_no_home="ER71483", wealth_with_home="ER71485", weight="ER71570", head_education_years="ER71538", head_hs_graduate="ER70893", head_ged_grade="ER70896", head_attend_college="ER70904", head_college_years="ER70907", head_college_degree="ER70908"),
    dict(year=2019, release="ER72001", id="ER72002", family_size="ER72016", age="ER72017", sex="ER72018", race="ER76897", race2="ER76898", ethnic="ER76902", marital="ER72024", marital_generated="ER77601", couple="ER77603", housing="ER72030", labor="ER77315", expenditure="ER77587", wealth_no_home="ER77509", wealth_with_home="ER77511", weight="ER77631", head_education_years="ER77599", head_hs_graduate="ER76908", head_ged_grade="ER76911", head_attend_college="ER76919", head_college_years="ER76922", head_college_degree="ER76923"),
    dict(year=2021, release="ER78001", id="ER78002", family_size="ER78016", age="ER78017", sex="ER78018", race="ER81144", race2="ER81145", ethnic="ER81149", marital="ER78025", marital_generated="ER81928", couple="ER81930", housing="ER78031", labor="ER81642", expenditure="ER81914", wealth_no_home="ER81836", wealth_with_home="ER81838", weight="ER81958", head_education_years="ER81926", head_hs_graduate="ER81155", head_ged_grade="ER81158", head_attend_college="ER81166", head_college_years="ER81169", head_college_degree="ER81170"),
    dict(year=2023, release="ER82001", id="ER82002", family_size="ER82017", age="ER82018", sex="ER82019", race="ER85121", race2="ER85122", ethnic="ER85126", marital="ER82026", marital_generated="ER85782", couple="ER85784", housing="ER82032", labor="ER85496", expenditure="ER85768", wealth_no_home="ER85690", wealth_with_home="ER85692", weight="ER85812", head_education_years="ER85780", head_hs_graduate="ER85132", head_ged_grade="ER85135", head_attend_college="ER85143", head_college_years="ER85146", head_college_degree="ER85147"),
]

FIELD_LABELS = {
    "release": "release_number",
    "id": "family_interview_id",
    "family_size": "family_unit_size_raw",
    "age": "head_age",
    "sex": "head_sex_code",
    "race": "head_race_code",
    "race2": "head_race_mention2_code",
    "ethnic": "head_ethnic_group_code",
    "marital": "head_marital_status_code",
    "marital_generated": "marital_status_generated_code",
    "couple": "couple_status_code",
    "housing": "housing_tenure_code",
    "labor": "head_labor_income_raw",
    "expenditure": "total_family_expenditure_raw",
    "wealth_no_home": "family_wealth_ex_home_equity_raw",
    "wealth_with_home": "family_wealth_in_home_equity_raw",
    "weight": "family_weight_raw",
    "head_education_years": "head_education_years_raw",
    "head_ba_degree": "head_ba_degree_raw",
    "head_hs_graduate": "head_hs_graduate_code",
    "head_ged_grade": "head_grade_level_if_GED_raw",
    "head_attend_college": "head_attend_college_code",
    "head_college_years": "head_highest_year_college_completed_raw",
    "head_college_degree": "head_college_degree_code",
}

# Raw text column -> numeric column. Special codes (e.g. 99, 999) are NOT recoded.
NUMERIC = {
    "head_age": "head_age_num",
    "family_unit_size_raw": "family_unit_size",
    "head_labor_income_raw": "head_labor_income",
    "total_family_expenditure_raw": "total_family_expenditure",
    "family_wealth_ex_home_equity_raw": "family_wealth_ex_home_equity",
    "family_wealth_in_home_equity_raw": "family_wealth_in_home_equity",
    "family_weight_raw": "family_weight",
    "head_education_years_raw": "head_education_years",
    "head_grade_level_if_GED_raw": "head_grade_level_if_GED",
    "head_highest_year_college_completed_raw": "head_highest_year_college_completed",
}

EDUCATION_KEYS = (
    "head_education_years", "head_ba_degree", "head_hs_graduate", "head_ged_grade",
    "head_attend_college", "head_college_years", "head_college_degree",
)


def is_present(series: pd.Series) -> pd.Series:
    """True where a raw field is nonblank and not an all-zero fill (e.g. '0', '0000')."""
    s = series.astype("string").str.strip()
    return s.notna() & s.ne("") & ~s.str.fullmatch(r"0+").fillna(False)


def mapped_variables() -> list[str]:
    return sorted({col for wave in WAVES for key, col in wave.items() if key != "year"})


def locate_wide(args: argparse.Namespace) -> Path:
    if args.wide:
        return Path(args.wide).expanduser().resolve()
    candidates = [SCRIPT_DIR / "psid_output" / "psid_family_wide.csv", SCRIPT_DIR / "output" / "psid_family_wide.csv"]
    for p in candidates:
        if p.exists():
            return p
    # Build the wide import using the companion importer if needed.
    importer = SCRIPT_DIR / "psid_import.py"
    sas = Path(args.sas).expanduser().resolve() if args.sas else SCRIPT_DIR / f"{JOB}.sas"
    data = Path(args.data).expanduser().resolve() if args.data else SCRIPT_DIR / f"{JOB}.txt"
    if not importer.exists():
        raise FileNotFoundError(f"Wide CSV not found and importer missing: {importer}")
    if not sas.exists():
        raise FileNotFoundError(f"SAS setup file not found: {sas}")
    if not data.exists():
        raise FileNotFoundError(f"ASCII data file not found: {data}")
    outdir = SCRIPT_DIR / "psid_output"
    subprocess.run([sys.executable, str(importer), "--sas", str(sas), "--data", str(data), "--outdir", str(outdir)], check=True)
    return outdir / "psid_family_wide.csv"


def build_panel(wide: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    # Each source record carries every selected interview year side by side. This
    # synthetic ID is stable only within this particular extract, and is not an
    # official PSID identifier.
    source_id = pd.Series(range(1, len(wide) + 1), index=wide.index, name="source_record_id")
    family_number_1968 = wide["V3"] if "V3" in wide.columns else pd.Series(pd.NA, index=wide.index, dtype="string")
    for wave in WAVES:
        year = wave["year"]
        for key, col in wave.items():
            if key != "year" and col not in wide.columns:
                raise KeyError(f"Expected variable {col} for {year} is absent from the imported data.")
        # A record participates in a wave when its family interview number is
        # nonblank and not an all-zero fill.
        present = is_present(wide[wave["id"]])
        out = pd.DataFrame(
            {"source_record_id": source_id[present], "panel_id": source_id[present], "interview_year": year, "year": year},
            index=wide.index[present],
        )
        out["income_reference_year"] = year - 1
        out["family_number_1968_raw"] = family_number_1968[present]
        for key, col in wave.items():
            if key == "year":
                continue
            out[FIELD_LABELS[key]] = wide.loc[present, col].astype("string").str.strip().replace("", pd.NA)
        # Education: components differ by period. 1975-84 carry a single grade-completed
        # item and a BA/BS degree item; 1985+ carry HS graduation, GED grade, college
        # attendance, highest college year, and degree; 1991+ add a completed-education
        # item. head_education_years pools the 1975-84 and 1991+ grade-completed items
        # (no data for 1985-90); head_education_series records which item it is.
        out["education_components_available"] = int(any(key in wave for key in EDUCATION_KEYS))
        if "weight" in wave:
            out["family_weight_variable"] = wave["weight"]
        if "head_education_years" in wave:
            out["head_education_series"] = "education_hd_1975_84" if year <= 1984 else "completed_ed_1991_on"
        for raw_name, num_name in NUMERIC.items():
            if raw_name in out:
                out[num_name] = pd.to_numeric(out[raw_name], errors="coerce")
        rows.append(out)
    panel = pd.concat(rows, ignore_index=True)
    # Canonical column order (concat otherwise orders columns by first appearance).
    leading = ["source_record_id", "panel_id", "interview_year", "year", "income_reference_year", "family_number_1968_raw"]
    ordered = leading + [c for raw, num in [(FIELD_LABELS[k], NUMERIC.get(FIELD_LABELS[k])) for k in FIELD_LABELS] for c in (raw, num) if c]
    ordered += ["family_weight_variable", "head_education_series", "education_components_available"]
    panel = panel[[c for c in ordered if c in panel.columns]]
    panel = panel.sort_values(["source_record_id", "interview_year"], kind="stable").reset_index(drop=True)
    return panel


def main() -> None:
    parser = argparse.ArgumentParser(description=f"Build a long PSID family-wave panel from the {JOB} multi-wave family extract.")
    parser.add_argument("--wide", help="Path to psid_family_wide.csv; if omitted, look beside this script and import raw data if needed.")
    parser.add_argument("--dictionary", help="Optional variable_dictionary.csv path for validation/documentation.")
    parser.add_argument("--sas", help="SAS setup file path (used only if the wide CSV needs to be generated).")
    parser.add_argument("--data", help="Fixed-width ASCII data path (used only if the wide CSV needs to be generated).")
    parser.add_argument("--outdir", default=str(SCRIPT_DIR / "panel_output"), help="Output directory (default: panel_output beside this script).")
    args = parser.parse_args()

    wide_path = locate_wide(args)
    if not wide_path.exists():
        raise FileNotFoundError(f"Imported wide CSV not found: {wide_path}")
    needed = mapped_variables() + ["V3"]
    header = pd.read_csv(wide_path, nrows=0, dtype="string").columns
    absent = sorted(set(needed) - set(header))
    if absent:
        raise ValueError(
            f"{wide_path} is missing {len(absent)} mapped variables (first few: {', '.join(absent[:8])}). "
            f"It was probably produced from a different PSID job than {JOB}; re-run psid_import.py on {JOB}."
        )
    wide = pd.read_csv(wide_path, dtype="string", usecols=sorted(set(needed)), low_memory=False)
    if args.dictionary:
        dictionary_path = Path(args.dictionary).expanduser().resolve()
    else:
        dictionary_path = wide_path.parent / "variable_dictionary.csv"
    if dictionary_path.exists():
        dictionary = pd.read_csv(dictionary_path, dtype=str)
        available = set(dictionary["variable"].dropna())
        missing = sorted(set(needed) - available)
        if missing:
            raise ValueError("The variable dictionary is missing mapped variables: " + ", ".join(missing))

    panel = build_panel(wide)
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    panel_path = outdir / "psid_family_panel_long.csv"
    panel.to_csv(panel_path, index=False)

    # A wave-level audit makes it easy to spot missing/incorrect year mappings.
    numeric_cols = [c for c in NUMERIC.values() if c in panel.columns]
    audit = panel.groupby("interview_year").agg(
        panel_rows=("source_record_id", "size"),
        unique_source_records=("source_record_id", "nunique"),
    )
    audit = audit.join(panel.groupby("interview_year")[numeric_cols].count().add_prefix("nonmissing_")).reset_index()
    audit_path = outdir / "psid_panel_wave_audit.csv"
    audit.to_csv(audit_path, index=False)

    notes_path = outdir / "README_panel.txt"
    notes_path.write_text(
        f"PSID family-wave panel from {JOB}\n"
        "=================================\n\n"
        "psid_family_panel_long.csv has one row per source record and interview wave in which the\n"
        "record has a nonblank, non-zero family interview number.\n"
        "source_record_id is a synthetic row index for this exact wide extract; it is NOT an official PSID ID.\n"
        "family_interview_id is the wave-specific family interview number from the selected extract.\n"
        "family_number_1968_raw preserves V3 when available.\n"
        "release_number is the PSID release number of each wave's family file.\n\n"
        "Waves: 1968-1997 annual, 1999-2023 biennial (43 waves). From 2017 the PSID labels the head the\n"
        "reference person; head_* columns hold the reference person in those waves.\n\n"
        "Timing: interview_year is the family interview wave. head_labor_income refers to the prior\n"
        "calendar year (income_reference_year = interview_year - 1), following the variable labels.\n"
        "Expenditure and wealth variables are assigned to the interview/wealth year in their labels.\n\n"
        "Field coverage in this extract:\n"
        "- All waves: interview number, family unit size, head age, sex, race (first mention), marital\n"
        "  status (interview item), housing tenure, head labor income.\n"
        "- marital_status_generated_code: 1977 onward. couple_status_code: 1983 onward.\n"
        "- head_race_mention2_code: 1985 onward. head_ethnic_group_code: 1997 onward.\n"
        "- Education: head_education_years pools the 1975-84 grade-completed item (EDUCATION-HD,\n"
        "  # YRS HD SCHOOLING) and the 1991+ COMPLETED ED item; head_education_series identifies the\n"
        "  item and 1985-90 have no such item. head_ba_degree_raw covers 1975-84 only. HS graduation,\n"
        "  GED grade, college attendance, highest college year, and college degree cover 1985 onward.\n"
        "- family_weight: 1997 onward. The weight concept changes across waves (e.g. the 2003 weight is\n"
        "  the core/immigrant longitudinal weight); check the codebook before pooling.\n"
        "- Total expenditure: 1999 onward. Wealth (with and without home equity): 1984, 1989, 1994, 1999,\n"
        "  then every wave from 2001. Do not interpolate missing waves automatically.\n"
        "- family_weight_variable records the source PSID variable of each wave's weight.\n\n"
        "Important limitations:\n"
        "- Numeric columns are parsed from the raw fields, but special missing codes (e.g. 99, 999) are NOT\n"
        "  guessed or recoded, and 0 is preserved as a value.\n"
        "- Categorical fields (sex, race, ethnicity, marital status, housing tenure, education items)\n"
        "  remain raw codes. Consult the codebook/formats file; coding differs across periods.\n"
        "- The source row index is not an official longitudinal PSID identifier. Verify row-to-family\n"
        "  linkage and use official PSID family/person IDs for rigorous longitudinal inference.\n"
        f"- Check all wave mappings against {JOB}_codebook.pdf before publication-quality analysis.\n"
    )
    print(f"Wide rows: {len(wide):,}")
    print(f"Panel rows: {len(panel):,}")
    print(f"Source records: {panel['source_record_id'].nunique():,}")
    print(f"Interview waves: {panel['interview_year'].nunique()}")
    print(f"Panel CSV: {panel_path}")
    print(f"Wave audit: {audit_path}")
    print(f"Notes: {notes_path}")


if __name__ == "__main__":
    main()