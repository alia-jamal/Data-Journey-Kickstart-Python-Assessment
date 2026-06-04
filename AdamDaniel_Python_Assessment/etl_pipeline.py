"""
etl_pipeline.py
===============
Task 3 – ETL Pipeline Implementation  (Refactored: Dynamic Normalisation)
Assessment: Python Training Task Assessment

Key improvements over v1
------------------------
  • Static RigType dict replaced with a generic fuzzy-matching normaliser that
    works across ALL categorical lookup fields (RigType, WellType, ReportType,
    RegionName).  New source variants are handled automatically — no code edits
    required.
  • CONFIGURATION block at the top is the single place to update when:
      - A CSV column is renamed       → update C (column map)
      - A new date column is added    → update DATE_COLS
      - A new canonical value exists  → update CANONICAL list for that field
      - A default assumption changes  → update DEFAULTS
  • Proper-noun columns (RigName, PacName) are checked for intra-column
    similarity and flagged for human review — but never auto-modified.
  • Every hardcoded assumption (rig_role, performance_scope, etc.) lives in
    DEFAULTS so intent is visible and auditable.

Normalisation logic  (per lookup field)
----------------------------------------
  1. Exact match (case-insensitive)  → score 100, action 'exact_match'
  2. Short-code guard: if ALL canonical values are ≤ 4 chars (e.g. RegionName
     "PM", "SK") skip fuzzy — single-char differences are too ambiguous.
  3. Fuzzy match (token_sort_ratio scorer):
       score >= FUZZY_AUTO_ACCEPT  → auto-normalise, log INFO
       score >= FUZZY_FLAG_REVIEW  → use best guess, log WARNING for review
       score <  FUZZY_FLAG_REVIEW  → load raw (uppercased), log WARNING UNRESOLVED

Usage
-----
  pip install rapidfuzz
  python etl_pipeline.py

Dependencies
------------
  pandas    >= 1.3
  rapidfuzz >= 3.0
  sqlite3   (stdlib)
"""

import logging
import os
import sqlite3
from datetime import datetime, timezone

import pandas as pd
from rapidfuzz import fuzz, process as fz_process


# =============================================================================
# CONFIGURATION  ← update here; no other code changes needed for most changes
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(SCRIPT_DIR, "drilling_operations.db")

# Resolve CSV in either the flat layout (same folder as this script) or the
# brief's suggested layout (sibling `data/` directory). Whichever exists wins.
_CSV_CANDIDATES = [
    os.path.join(SCRIPT_DIR, "DataForAssessment.csv"),
    os.path.normpath(os.path.join(SCRIPT_DIR, "data", "DataForAssessment.csv")),
    os.path.normpath(os.path.join(SCRIPT_DIR, "..", "data", "DataForAssessment.csv")),
]
CSV_PATH = next((p for p in _CSV_CANDIDATES if os.path.exists(p)), _CSV_CANDIDATES[0])

# ── 1. CSV column map: logical name → actual CSV header
#       If the source file renames a column, change the VALUE here only.
C = {
    "pac_name":               "PacName",
    "region_name":            "RegionName",
    "field_name":             "FieldName",
    "well_name":              "WellName",
    "well_type":              "WellType",
    "rig_name":               "RigName",
    "rig_type":               "RigType",
    "water_depth":            "WaterDepth",
    "year":                   "Year",
    "report_type":            "ReportType",
    "document_name":          "DocumentName",
    "document_date":          "DocumentDate",
    "submitted_at":           "SubmittedAt",
    "submitted_by":           "SubmittedBy",
    "afe_cost":               "AfeCost",
    "afe_days":               "AfeDays",
    "spud_date":              "SpudDate",
    "well_start_dt":          "WellStartDateTime",
    "well_end_dt":            "WellEndDateTime",
    "final_cost":             "FinalCost",
    "final_days":             "FinalDays",
    "npt_pct_wow":            "WellNptPercentageWow",
    "npt_pct":                "WellNptPercentage",
    "completion_cost_plan":   "CompletionCostPlan",
    "completion_cost_actual": "CompletionCostActual",
    "drilling_plan_wcpf":     "DrillingPlanWcpf",
    "drilling_actual_wcpf":   "DrillingActualWcpf",
}

# ── 2. Date columns to parse to ISO 8601 UTC
#       Add new date columns here — nothing else needs changing.
DATE_COLS = [
    C["spud_date"], C["well_start_dt"], C["well_end_dt"],
    C["document_date"], C["submitted_at"],
]

# ── 3. Operation deduplication key
#       Rows sharing ALL these values represent the same WellOperation.
#       If the source gains a finer-grained identifier, add it here.
OP_KEY = [
    C["pac_name"], C["region_name"], C["field_name"],
    C["well_name"], C["rig_name"],
    C["well_start_dt"], C["well_end_dt"],
]

# ── 4. Fuzzy matching thresholds  (0–100, token_sort_ratio scorer)
#
#   token_sort_ratio sorts the words in both strings alphabetically before
#   comparing, so word-order differences don't reduce the score.
#   Examples at current thresholds:
#     "JACK UP"      vs "JACK-UP"                             → 86  → AUTO
#     "SEMI-SUB"     vs "SEMI-SUBMERSIBLE"                    → 90  → AUTO
#     "PLATFORM TENDER-ASSISTED BARGE TYPE"
#                    vs "PLATFORM TENDER-ASSISTED BARGE"      → 95  → AUTO
#
FUZZY_AUTO_ACCEPT  = 85   # >= 85 : auto-normalise to canonical, log INFO
FUZZY_FLAG_REVIEW  = 60   # 60-84 : use best guess, emit WARNING for human review
                           # < 60  : load raw (uppercased), emit WARNING UNRESOLVED

# ── 5. Canonical value lists for each lookup field
#
#   These are the agreed standard values.  When a new raw value arrives:
#     • UNRESOLVED  → decide: is it a genuinely new category (add to list)?
#                             or is it a typo/variant (correct at source)?
#     • FLAG_REVIEW → confirm the auto-mapping is correct; if so, no action
#                     needed (it will auto-accept next run too).
#
#   IMPORTANT: short-code fields (all values ≤ 4 chars, e.g. RegionName)
#   skip fuzzy matching because single-character differences are ambiguous.
#   Only exact (case-insensitive) matches are accepted for those fields.
CANONICAL = {
    C["rig_type"]: [
        "JACK-UP",
        "SEMI-SUBMERSIBLE",
        "DRILL SHIP",
        "RIGLESS",
        "TENDER ASSISTED DRILLING RIG (TADR)",
        "PLATFORM TENDER-ASSISTED SEMI-SUB",
        "PLATFORM TENDER-ASSISTED BARGE",
        "SUPER B CLASS",
    ],
    C["well_type"]: [
        "APPRAISAL CUM DEV/DEVELOPMENT",
        "EXPLORATION/APPRAISAL",
    ],
    C["report_type"]: [
        "NOOP",
        "FWR",
    ],
    # Short-code field — fuzzy skipped; exact match only
    C["region_name"]: [
        "PM", "SK", "SB",
    ],
}

# ── 6. Default values for schema columns absent from the source data
#
#   These are ASSUMPTIONS made because the CSV does not supply the value.
#   Each entry is labelled with which DB table/column it populates.
#   Review and update if the source data ever begins providing these fields.
DEFAULTS = {
    # WellOperationRigAssignment
    "rig_role":               "Primary Drilling Rig",
    "is_primary_rig":         1,
    # OperationPerformance
    "performance_scope":      "Operation",
    "performance_version":    1,
    "is_final":               1,
    # ReportWellOperation
    "relationship_type":      "Primary Subject",
    # Region fallback for null RegionName
    "missing_region_sentinel": "UNKNOWN",
    # DocumentName fallback prefix when source value is null
    "doc_name_prefix":        "AUTO",
}

# ── 7. Proper-noun columns: check intra-column similarity, never auto-modify
#
#   These columns contain unique identifiers (rig names, company names).
#   We cannot normalise them without domain knowledge, but we flag pairs
#   that look suspiciously similar so a human can verify.
#   Example risk: "NAGA 4" and "NAGA 7" score 83 — similar but DIFFERENT rigs.
PROPER_NOUN_COLS            = [C["rig_name"], C["pac_name"]]
PROPER_NOUN_SIMILARITY_WARN = 85   # flag pairs scoring >= this


# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)
dq_issues: list[dict] = []   # accumulated for the summary report


# =============================================================================
# HELPERS
# =============================================================================

def _log_dq(issue_type: str, detail: str,
            affected_rows: int = 0, level: str = "info") -> None:
    """Record a data-quality issue and emit a log line at the given level."""
    msg = f"[DQ] {issue_type}: {detail}"
    if affected_rows:
        msg += f" ({affected_rows} row(s) affected)"
    getattr(log, level)(msg)
    dq_issues.append({
        "issue_type":    issue_type,
        "detail":        detail,
        "affected_rows": affected_rows,
        "level":         level,
    })


def _parse_date(value) -> str | None:
    """Parse any date/datetime string → ISO 8601 UTC string, or None."""
    if pd.isna(value) or value is None:
        return None
    try:
        return pd.to_datetime(value, utc=True).isoformat()
    except Exception:
        return None


def _get_or_insert(cursor, table, pk_col, lookup_col, value, cache):
    """Return surrogate PK for value, inserting a new row if absent."""
    if value in cache:
        return cache[value]
    cursor.execute(
        f"INSERT OR IGNORE INTO {table} ({lookup_col}) VALUES (?)", (value,)
    )
    cursor.execute(
        f"SELECT {pk_col} FROM {table} WHERE {lookup_col} = ?", (value,)
    )
    pk = cursor.fetchone()[0]
    cache[value] = pk
    return pk


def _normalise_field(raw_value, field_name: str) -> tuple:
    """
    Normalise a raw categorical value against the canonical list for field_name.

    Returns (resolved_value, score, action) where action is one of:
      'null'           – input was null/NaN
      'exact_match'    – case-insensitive exact match, no change needed
      'auto_accept'    – fuzzy score >= FUZZY_AUTO_ACCEPT, auto-normalised
      'flagged_review' – fuzzy score in [FUZZY_FLAG_REVIEW, FUZZY_AUTO_ACCEPT)
                         best-guess canonical used; human should verify
      'unresolved'     – score too low, short-code field, or no canonical list;
                         raw value uppercased and loaded as-is
    """
    canonical_list = CANONICAL.get(field_name, [])

    if pd.isna(raw_value) or raw_value is None:
        return None, 0, "null"

    cleaned = str(raw_value).strip()
    cleaned_upper = cleaned.upper()

    if not canonical_list:
        # No canonical list defined — uppercase and flag
        return cleaned_upper, 0, "unresolved"

    # ── Step 1: Exact match (case-insensitive) ───────────────────────────────
    for canon in canonical_list:
        if cleaned_upper == canon.upper():
            return canon, 100, "exact_match"

    # ── Step 2: Short-code guard ─────────────────────────────────────────────
    # Fields like RegionName ("PM", "SK") have very short canonical values.
    # Fuzzy matching is unreliable at this length — a one-char typo would
    # match a completely different code.  Skip fuzzy; flag as unresolved.
    if all(len(c) <= 4 for c in canonical_list):
        return cleaned_upper, 0, "unresolved"

    # ── Step 3: Fuzzy match ──────────────────────────────────────────────────
    # token_sort_ratio alphabetises tokens before comparing, so
    # "BARGE TYPE PLATFORM" matches "PLATFORM BARGE" at a high score.
    result = fz_process.extractOne(
        cleaned_upper,
        canonical_list,
        scorer=fuzz.token_sort_ratio,
        processor=str.upper,
    )

    if result is None:
        return cleaned_upper, 0, "unresolved"

    best_match, score, _ = result

    if score >= FUZZY_AUTO_ACCEPT:
        return best_match, score, "auto_accept"
    elif score >= FUZZY_FLAG_REVIEW:
        return best_match, score, "flagged_review"
    else:
        return cleaned_upper, score, "unresolved"


def _flag_similar_proper_nouns(series: pd.Series, field_name: str) -> None:
    """
    Scan a proper-noun column for pairs of values that look suspiciously
    similar (score >= PROPER_NOUN_SIMILARITY_WARN).

    This does NOT modify data — it is purely a DQ warning for human review.
    The risk of auto-normalising proper nouns is illustrated by the dataset:
    'NAGA 4' vs 'NAGA 7' score 83 — similar but they are DIFFERENT rigs.
    Only a human (or domain-specific SLM) can safely resolve these.
    """
    values = series.dropna().unique().tolist()
    flagged = []
    for i, v1 in enumerate(values):
        for v2 in values[i + 1:]:
            score = fuzz.token_sort_ratio(v1.upper(), v2.upper())
            if score >= PROPER_NOUN_SIMILARITY_WARN:
                flagged.append((v1, v2, int(score)))

    if flagged:
        pairs = "; ".join(
            f"'{a}' ~ '{b}' (score {s})" for a, b, s in sorted(flagged, key=lambda x: -x[2])
        )
        _log_dq(
            f"Potential duplicates in {field_name}",
            f"These may refer to the same entity — verify before trusting groupings. {pairs}",
            len(flagged),
            level="warning",
        )


# =============================================================================
# STAGE 1: EXTRACT
# =============================================================================

def extract(csv_path: str) -> pd.DataFrame:
    """Read the CSV and run data-quality audits before any transformation."""
    log.info("=" * 60)
    log.info("EXTRACT – Reading %s", csv_path)
    log.info("=" * 60)

    df = pd.read_csv(csv_path)
    log.info("Loaded %d rows x %d columns", *df.shape)

    # ── Schema check: expected columns present? ──────────────────────────────
    expected_cols = set(C.values())
    actual_cols   = set(df.columns)
    missing_cols  = expected_cols - actual_cols
    extra_cols    = actual_cols   - expected_cols
    if missing_cols:
        _log_dq("Missing expected columns",
                f"In config but not in CSV: {sorted(missing_cols)}",
                level="warning")
    if extra_cols:
        _log_dq("Unexpected columns",
                f"In CSV but not in config (will be ignored): {sorted(extra_cols)}")

    # ── Null audit ───────────────────────────────────────────────────────────
    null_counts = df.isnull().sum()
    for col, cnt in null_counts[null_counts > 0].items():
        tag = "All-null column" if cnt == len(df) else "Partial nulls"
        _log_dq(tag, f"'{col}' has {cnt} NULL value(s)", cnt)

    # ── Duplicate operation row audit ─────────────────────────────────────────
    valid_op_key = [k for k in OP_KEY if k in df.columns]
    dup_mask = df.duplicated(subset=valid_op_key, keep=False)
    if dup_mask.any():
        _log_dq("Duplicate operation rows",
                "Will be collapsed to one WellOperation (first occurrence kept)",
                int(dup_mask.sum()))

    # ── Canonical field audit ─────────────────────────────────────────────────
    # Report raw values that are not in the canonical list — these will go
    # through fuzzy matching in Transform.
    for field_col, canon_list in CANONICAL.items():
        if field_col not in df.columns:
            continue
        raw_vals     = df[field_col].dropna().unique().tolist()
        non_canon    = [v for v in raw_vals
                        if v.strip().upper() not in {c.upper() for c in canon_list}]
        if non_canon:
            _log_dq(f"Non-canonical values in {field_col}",
                    f"Will be resolved via fuzzy matching: {non_canon}",
                    len(non_canon))

    # ── Proper-noun similarity check ─────────────────────────────────────────
    for col in PROPER_NOUN_COLS:
        if col in df.columns:
            _flag_similar_proper_nouns(df[col], col)

    log.info("EXTRACT complete – %d rows", len(df))
    return df


# =============================================================================
# STAGE 2: TRANSFORM
# =============================================================================

def transform(df: pd.DataFrame) -> dict:
    """Normalise flat CSV into table-ready collections."""
    log.info("=" * 60)
    log.info("TRANSFORM – Normalising into relational tables")
    log.info("=" * 60)

    df = df.copy()

    # ── 1. Fuzzy-normalise all canonical lookup fields ────────────────────────
    # For each field with a canonical list, create three new columns:
    #   {col}_clean   – the resolved value to be loaded into the DB
    #   {col}_score   – fuzzy match score (100 = exact)
    #   {col}_action  – what happened: exact_match / auto_accept /
    #                   flagged_review / unresolved / null
    #
    # The original column is preserved untouched for auditing.

    for field_col in CANONICAL:
        if field_col not in df.columns:
            log.warning("Canonical field '%s' not found in CSV — skipping", field_col)
            continue

        results = df[field_col].apply(lambda v: _normalise_field(v, field_col))
        df[field_col + "_clean"]  = results.apply(lambda r: r[0])
        df[field_col + "_score"]  = results.apply(lambda r: r[1])
        df[field_col + "_action"] = results.apply(lambda r: r[2])

        # Log one entry per unique (raw, resolved, action) combination
        detail_df = (
            df[[field_col, field_col + "_clean",
                field_col + "_score", field_col + "_action"]]
            .drop_duplicates()
        )
        action_counts = df[field_col + "_action"].value_counts().to_dict()
        log.info("  %s normalisation: %s", field_col, action_counts)

        for _, row in detail_df.iterrows():
            action = row[field_col + "_action"]
            if action in ("null", "exact_match"):
                continue   # nothing interesting to log per-value
            raw    = row[field_col]
            clean  = row[field_col + "_clean"]
            score  = int(row[field_col + "_score"])
            lvl    = "info" if action == "auto_accept" else "warning"
            _log_dq(
                f"{field_col} [{action.upper()}]",
                f"'{raw}'  ->  '{clean}'  (score {score})",
                level=lvl,
            )

    # Helper: return the _clean column name if it was created, else the raw
    def cc(key: str) -> str:
        raw = C[key]
        return raw + "_clean" if (raw + "_clean") in df.columns else raw

    # ── 2. Handle missing RegionName ──────────────────────────────────────────
    sentinel    = DEFAULTS["missing_region_sentinel"]
    region_col  = cc("region_name")
    missing_rgn = df[region_col].isna()
    if missing_rgn.any():
        _log_dq("Missing RegionName",
                f"Sentinel '{sentinel}' assigned — correct at source",
                int(missing_rgn.sum()), level="warning")
        df.loc[missing_rgn, region_col] = sentinel

    # ── 3. Parse date columns ─────────────────────────────────────────────────
    for col in DATE_COLS:
        if col not in df.columns:
            continue
        df[col + "_iso"] = df[col].apply(_parse_date)
        n_failed = int(df[col].notna().sum() - df[col + "_iso"].notna().sum())
        if n_failed:
            _log_dq("Unparseable dates",
                    f"'{col}' had {n_failed} value(s) that could not be parsed",
                    n_failed, level="warning")

    # ── 4. Deduplicate at operation level ──────────────────────────────────────
    valid_op_key = [k for k in OP_KEY if k in df.columns]
    ops_df = (df.drop_duplicates(subset=valid_op_key, keep="first")
                .reset_index(drop=True))
    log.info("Unique WellOperations after dedup: %d (from %d rows)",
             len(ops_df), len(df))

    # ── 5. Collect unique lookup values for Load stage ────────────────────────
    pac_names     = sorted(df[C["pac_name"]].dropna().unique().tolist())
    region_pairs  = (df[[C["pac_name"], cc("region_name")]]
                     .drop_duplicates().dropna().values.tolist())
    field_triples = (df[[C["pac_name"], cc("region_name"), C["field_name"]]]
                     .drop_duplicates().dropna(subset=[C["field_name"]]).values.tolist())
    well_types    = sorted(ops_df[cc("well_type")].dropna().unique().tolist())
    rig_types     = sorted(ops_df[cc("rig_type")].dropna().unique().tolist())
    report_types  = sorted(df[cc("report_type")].dropna().unique().tolist())

    log.info("Lookup sizes — PAC: %d, Region: %d, Field: %d, "
             "WellType: %d, RigType: %d, ReportType: %d",
             len(pac_names), len(region_pairs), len(field_triples),
             len(well_types), len(rig_types), len(report_types))

    return {
        "_raw_df":       df,
        "_ops_df":       ops_df,
        "_cc":           cc,          # column-name resolver, used in Load
        "pac_names":     pac_names,
        "region_pairs":  region_pairs,
        "field_triples": field_triples,
        "well_types":    well_types,
        "rig_types":     rig_types,
        "report_types":  report_types,
    }


# =============================================================================
# STAGE 3: LOAD
# =============================================================================

def load(payload: dict, db_path: str) -> dict:
    """Insert all transformed data into the SQLite database in FK-safe order."""
    log.info("=" * 60)
    log.info("LOAD – Inserting into %s", db_path)
    log.info("=" * 60)

    df     = payload["_raw_df"]
    ops_df = payload["_ops_df"]
    cc     = payload["_cc"]         # maps logical key -> clean col name

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # In-memory caches  {business_key: surrogate_pk}
    pac_cache        : dict = {}
    region_cache     : dict = {}   # (pac_name, region_name) → region_id
    field_cache      : dict = {}   # (region_id, field_name) → field_id
    well_type_cache  : dict = {}
    well_cache       : dict = {}   # (field_id, well_name)   → well_id
    rig_type_cache   : dict = {}
    rig_cache        : dict = {}   # (rig_name, rig_type)    → rig_id
    op_cache         : dict = {}   # tuple(OP_KEY values)    → well_operation_id
    report_type_cache: dict = {}

    def row_get(row, key: str):
        """Read a value from an itertuples row using the column config key."""
        return getattr(row, C[key])

    def row_get_clean(row, key: str):
        """Read the _clean version of a column, falling back to raw."""
        return getattr(row, cc(key))

    try:
        # ── A. ProductionAssetCompany ─────────────────────────────────────────
        log.info("Loading ProductionAssetCompany ...")
        for name in payload["pac_names"]:
            _get_or_insert(cursor, "ProductionAssetCompany",
                           "pac_id", "pac_name", name, pac_cache)
        log.info("  -> %d rows", len(pac_cache))

        # ── B. Region ─────────────────────────────────────────────────────────
        log.info("Loading Region ...")
        for pac_name, region_name in payload["region_pairs"]:
            pac_id    = pac_cache[pac_name]
            cache_key = (pac_name, region_name)
            if cache_key not in region_cache:
                cursor.execute(
                    "INSERT OR IGNORE INTO Region (pac_id, region_name) VALUES (?, ?)",
                    (pac_id, region_name)
                )
                cursor.execute(
                    "SELECT region_id FROM Region WHERE pac_id=? AND region_name=?",
                    (pac_id, region_name)
                )
                region_cache[cache_key] = cursor.fetchone()[0]
        log.info("  -> %d rows", len(region_cache))

        # ── C. Field ──────────────────────────────────────────────────────────
        log.info("Loading Field ...")
        for pac_name, region_name, field_name in payload["field_triples"]:
            region_id = region_cache[(pac_name, region_name)]
            cache_key = (region_id, field_name)
            if cache_key not in field_cache:
                cursor.execute(
                    "INSERT OR IGNORE INTO Field (region_id, field_name) VALUES (?, ?)",
                    (region_id, field_name)
                )
                cursor.execute(
                    "SELECT field_id FROM Field WHERE region_id=? AND field_name=?",
                    (region_id, field_name)
                )
                field_cache[cache_key] = cursor.fetchone()[0]
        log.info("  -> %d rows", len(field_cache))

        # ── D. WellType ───────────────────────────────────────────────────────
        log.info("Loading WellType ...")
        for wt in payload["well_types"]:
            _get_or_insert(cursor, "WellType",
                           "well_type_id", "well_type_name", wt, well_type_cache)
        log.info("  -> %d rows", len(well_type_cache))

        # ── E. Well ───────────────────────────────────────────────────────────
        log.info("Loading Well ...")
        well_src = (
            ops_df[[C["pac_name"], cc("region_name"), C["field_name"],
                    C["well_name"], cc("well_type"), C["water_depth"]]]
            .drop_duplicates(subset=[C["pac_name"], cc("region_name"),
                                     C["field_name"], C["well_name"]])
            .itertuples(index=False)
        )
        for row in well_src:
            region_id    = region_cache[(getattr(row, C["pac_name"]),
                                         getattr(row, cc("region_name")))]
            field_id     = field_cache[(region_id, getattr(row, C["field_name"]))]
            wt_val       = getattr(row, cc("well_type"))
            well_type_id = well_type_cache.get(wt_val)
            water_depth  = getattr(row, C["water_depth"])
            water_depth  = None if pd.isna(water_depth) else float(water_depth)
            cache_key    = (field_id, getattr(row, C["well_name"]))
            if cache_key not in well_cache:
                cursor.execute(
                    "INSERT INTO Well (field_id, well_type_id, well_name, water_depth)"
                    " VALUES (?, ?, ?, ?)",
                    (field_id, well_type_id, getattr(row, C["well_name"]), water_depth)
                )
                well_cache[cache_key] = cursor.lastrowid
        log.info("  -> %d rows", len(well_cache))

        # ── F. RigType ────────────────────────────────────────────────────────
        log.info("Loading RigType ...")
        for rt in payload["rig_types"]:
            _get_or_insert(cursor, "RigType",
                           "rig_type_id", "rig_type_name", rt, rig_type_cache)
        log.info("  -> %d rows", len(rig_type_cache))

        # ── G. Rig ────────────────────────────────────────────────────────────
        log.info("Loading Rig ...")
        rig_src = (
            ops_df[[C["rig_name"], cc("rig_type")]]
            .drop_duplicates()
            .itertuples(index=False)
        )
        for row in rig_src:
            rig_name    = getattr(row, C["rig_name"])
            rig_type_v  = getattr(row, cc("rig_type"))
            rig_type_id = rig_type_cache.get(rig_type_v)
            cache_key   = (rig_name, rig_type_v)
            if cache_key not in rig_cache:
                cursor.execute(
                    "INSERT INTO Rig (rig_type_id, rig_name) VALUES (?, ?)",
                    (rig_type_id, rig_name)
                )
                rig_cache[cache_key] = cursor.lastrowid
        log.info("  -> %d rows", len(rig_cache))

        # ── H. WellOperation ──────────────────────────────────────────────────
        log.info("Loading WellOperation ...")
        for row in ops_df.itertuples(index=False):
            pac_name    = getattr(row, C["pac_name"])
            region_name = getattr(row, cc("region_name"))
            field_name  = getattr(row, C["field_name"])
            well_name   = getattr(row, C["well_name"])

            region_id = region_cache[(pac_name, region_name)]
            field_id  = field_cache[(region_id, field_name)]
            well_id   = well_cache[(field_id, well_name)]
            op_key    = tuple(getattr(row, k) for k in OP_KEY if k in ops_df.columns)

            if op_key not in op_cache:
                year_val = getattr(row, C["year"])
                year     = int(year_val) if not pd.isna(year_val) else None

                spud  = getattr(row, C["spud_date"]    + "_iso", None)
                w_st  = getattr(row, C["well_start_dt"]+ "_iso", None)
                w_end = getattr(row, C["well_end_dt"]  + "_iso", None)

                cursor.execute(
                    "INSERT INTO WellOperation"
                    " (well_id, operation_year, spud_date,"
                    "  well_start_datetime, well_end_datetime)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (well_id, year, spud, w_st, w_end)
                )
                op_cache[op_key] = cursor.lastrowid
        log.info("  -> %d rows", len(op_cache))

        # ── I. WellOperationRigAssignment ─────────────────────────────────────
        log.info("Loading WellOperationRigAssignment ...")
        seen_assignments: set = set()
        assign_count = 0
        for row in ops_df.itertuples(index=False):
            op_key   = tuple(getattr(row, k) for k in OP_KEY if k in ops_df.columns)
            wop_id   = op_cache[op_key]
            rig_name = getattr(row, C["rig_name"])
            rig_type = getattr(row, cc("rig_type"))
            rig_id   = rig_cache[(rig_name, rig_type)]
            akey     = (wop_id, rig_id)
            if akey not in seen_assignments:
                cursor.execute(
                    "INSERT INTO WellOperationRigAssignment"
                    " (well_operation_id, rig_id, is_primary_rig, rig_role)"
                    " VALUES (?, ?, ?, ?)",
                    (wop_id, rig_id,
                     DEFAULTS["is_primary_rig"],
                     DEFAULTS["rig_role"])
                )
                seen_assignments.add(akey)
                assign_count += 1
        log.info("  -> %d rows", assign_count)

        # ── J. OperationPerformance ───────────────────────────────────────────
        log.info("Loading OperationPerformance ...")

        def _f(val):
            return None if pd.isna(val) else float(val)

        perf_count = 0
        for row in ops_df.itertuples(index=False):
            op_key = tuple(getattr(row, k) for k in OP_KEY if k in ops_df.columns)
            wop_id = op_cache[op_key]
            cursor.execute(
                "INSERT INTO OperationPerformance"
                " (well_operation_id, performance_scope, performance_version,"
                "  is_final, afe_cost, afe_days, final_cost, final_days,"
                "  well_npt_percentage_wow, well_npt_percentage,"
                "  completion_cost_plan, completion_cost_actual,"
                "  drilling_plan_wcpf, drilling_actual_wcpf)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (wop_id,
                 DEFAULTS["performance_scope"],
                 DEFAULTS["performance_version"],
                 DEFAULTS["is_final"],
                 _f(getattr(row, C["afe_cost"])),
                 _f(getattr(row, C["afe_days"])),
                 _f(getattr(row, C["final_cost"])),
                 _f(getattr(row, C["final_days"])),
                 _f(getattr(row, C["npt_pct_wow"])),
                 _f(getattr(row, C["npt_pct"])),
                 _f(getattr(row, C["completion_cost_plan"])),
                 _f(getattr(row, C["completion_cost_actual"])),
                 _f(getattr(row, C["drilling_plan_wcpf"])),
                 _f(getattr(row, C["drilling_actual_wcpf"])))
            )
            perf_count += 1
        log.info("  -> %d rows", perf_count)

        # ── K. ReportType ─────────────────────────────────────────────────────
        log.info("Loading ReportType ...")
        for rt in payload["report_types"]:
            _get_or_insert(cursor, "ReportType",
                           "report_type_id", "report_type_name", rt, report_type_cache)
        log.info("  -> %d rows", len(report_type_cache))

        # ── L. Report + ReportWellOperation ───────────────────────────────────
        log.info("Loading Report + ReportWellOperation ...")
        report_count   = 0
        rwo_count      = 0
        skipped        = 0
        seen_reports   : set = set()

        for row in df.itertuples(index=False):
            op_key = tuple(getattr(row, k) for k in OP_KEY if k in df.columns)
            wop_id = op_cache.get(op_key)
            if wop_id is None:
                _log_dq("Orphaned report row",
                        f"No matching WellOperation for key {op_key}",
                        level="warning")
                skipped += 1
                continue

            rt_raw    = getattr(row, cc("report_type"))
            rt_id     = report_type_cache.get(rt_raw)
            doc_name  = getattr(row, C["document_name"])
            if pd.isna(doc_name):
                doc_name = f"{DEFAULTS['doc_name_prefix']}_{rt_raw}_{wop_id}"
            doc_date  = getattr(row, C["document_date"] + "_iso", None)
            sub_at    = getattr(row, C["submitted_at"]  + "_iso", None)
            sub_by    = getattr(row, C["submitted_by"])

            rpt_key = (wop_id, rt_raw, doc_date, sub_at)
            if rpt_key in seen_reports:
                skipped += 1
                continue
            seen_reports.add(rpt_key)

            cursor.execute(
                "INSERT INTO Report"
                " (report_type_id, document_name, document_date,"
                "  submitted_at, submitted_by)"
                " VALUES (?, ?, ?, ?, ?)",
                (rt_id, doc_name, doc_date, sub_at, sub_by)
            )
            report_id = cursor.lastrowid
            report_count += 1

            cursor.execute(
                "INSERT INTO ReportWellOperation"
                " (report_id, well_operation_id, relationship_type)"
                " VALUES (?, ?, ?)",
                (report_id, wop_id, DEFAULTS["relationship_type"])
            )
            rwo_count += 1

        if skipped:
            _log_dq("Skipped report rows",
                    "Duplicate or orphaned rows not inserted", skipped)
        log.info("  Report -> %d rows", report_count)
        log.info("  ReportWellOperation -> %d rows", rwo_count)

        # ── Commit ─────────────────────────────────────────────────────────────
        conn.commit()
        log.info("Transaction committed successfully.")

        # ── Row-count summary ──────────────────────────────────────────────────
        counts = {}
        cursor.execute(
            "SELECT name FROM sqlite_master"
            " WHERE type='table' AND name!='sqlite_sequence' ORDER BY name;"
        )
        for (tbl,) in cursor.fetchall():
            cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
            counts[tbl] = cursor.fetchone()[0]
        log.info("Row counts: %s", counts)
        return counts

    except sqlite3.Error as exc:
        log.error("SQLite error — rolling back: %s", exc)
        conn.rollback()
        raise
    finally:
        conn.close()
        log.info("Database connection closed.")


# =============================================================================
# STAGE 4: VALIDATE
# =============================================================================

def validate(db_path: str) -> list:
    """Run post-load referential integrity checks."""
    log.info("=" * 60)
    log.info("VALIDATE – Post-load integrity checks")
    log.info("=" * 60)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    checks = [
        ("WellOperations without Rig assignment",
         "SELECT COUNT(*) FROM WellOperation wo WHERE NOT EXISTS"
         " (SELECT 1 FROM WellOperationRigAssignment a"
         "  WHERE a.well_operation_id=wo.well_operation_id)", True),
        ("WellOperations without OperationPerformance",
         "SELECT COUNT(*) FROM WellOperation wo WHERE NOT EXISTS"
         " (SELECT 1 FROM OperationPerformance p"
         "  WHERE p.well_operation_id=wo.well_operation_id)", True),
        ("Reports not linked to WellOperation",
         "SELECT COUNT(*) FROM Report r WHERE NOT EXISTS"
         " (SELECT 1 FROM ReportWellOperation rwo"
         "  WHERE rwo.report_id=r.report_id)", True),
        ("WellOperations with invalid well_id",
         "SELECT COUNT(*) FROM WellOperation wo"
         " WHERE wo.well_id NOT IN (SELECT well_id FROM Well)", True),
        ("Fields with invalid region_id",
         "SELECT COUNT(*) FROM Field f"
         " WHERE f.region_id NOT IN (SELECT region_id FROM Region)", True),
    ]

    results = []
    all_pass = True
    for name, sql, expect_zero in checks:
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        passed = (count == 0) if expect_zero else None
        status = "PASS" if passed else ("INFO" if passed is None else "FAIL")
        if passed is False:
            all_pass = False
        log.info("  [%s] %s -> %d", status, name, count)
        results.append({"name": name, "result": count, "status": status})

    log.info("All integrity checks %s.", "PASSED" if all_pass else "FAILED — review log")
    conn.close()
    return results


# =============================================================================
# SAMPLE QUERIES
# =============================================================================

def run_sample_queries(db_path: str) -> list:
    """Run demonstration queries and return results for the summary report."""
    log.info("=" * 60)
    log.info("SAMPLE QUERIES")
    log.info("=" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    queries = [
        ("Top 5 Wells by AFE Cost",
         "SELECT w.well_name, f.field_name, ROUND(p.afe_cost/1e6,2) AS afe_mUSD"
         " FROM OperationPerformance p"
         " JOIN WellOperation wo ON wo.well_operation_id=p.well_operation_id"
         " JOIN Well w ON w.well_id=wo.well_id"
         " JOIN Field f ON f.field_id=w.field_id"
         " ORDER BY p.afe_cost DESC LIMIT 5"),
        ("Reports per ReportType",
         "SELECT rt.report_type_name, COUNT(*) AS n"
         " FROM Report r JOIN ReportType rt ON rt.report_type_id=r.report_type_id"
         " GROUP BY rt.report_type_name"),
        ("Average NPT% by RigType",
         "SELECT rt.rig_type_name, ROUND(AVG(p.well_npt_percentage),2) AS avg_npt"
         " FROM OperationPerformance p"
         " JOIN WellOperationRigAssignment a ON a.well_operation_id=p.well_operation_id"
         " JOIN Rig rig ON rig.rig_id=a.rig_id"
         " JOIN RigType rt ON rt.rig_type_id=rig.rig_type_id"
         " GROUP BY rt.rig_type_name ORDER BY avg_npt DESC"),
    ]

    results = []
    for title, sql in queries:
        cursor.execute(sql)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        log.info("  %s: %s", title, rows)
        results.append({"title": title, "columns": cols, "rows": rows})

    conn.close()
    return results


# =============================================================================
# SUMMARY REPORT
# =============================================================================


def write_summary(counts, validation, sample_queries, report_path):
    """Write a clean Markdown summary report.

    Uses bullet/key-value formatting throughout so the report reads well in
    any Markdown viewer (including plain-text previewers that do not render
    GFM tables). Sample-query results are emitted as fixed-width text blocks
    inside a code fence for the same reason.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# ETL Pipeline - Summary Report",
        "",
        f"- **Run date:** {now}",
        "- **Source:** DataForAssessment.csv",
        "- **Target:** drilling_operations.db",
        "",
        "---",
        "",
        "## 1. Records Loaded per Table",
        "",
    ]
    total_rows = 0
    for tbl, cnt in sorted(counts.items()):
        total_rows += cnt
        lines.append(f"- `{tbl}` - {cnt}")
    lines.append("")
    lines.append(f"**Total:** {total_rows} rows across {len(counts)} tables.")

    # Section 2 - Data Quality Issues
    lines += ["", "---", "", "## 2. Data Quality Issues", ""]
    if not dq_issues:
        lines.append("_No data-quality issues recorded during this run._")
    else:
        for i, iss in enumerate(dq_issues, 1):
            level = iss["level"].upper()
            rows  = iss["affected_rows"]
            rows_note = f" - affected rows: {rows}" if rows else ""
            lines.append(f"{i}. **[{level}] {iss['issue_type']}**{rows_note}")
            lines.append(f"   {iss['detail']}")
            lines.append("")

    # Section 3 - Validation
    lines += ["---", "", "## 3. Validation", ""]
    for chk in validation:
        status = chk["status"]
        marker = "PASS" if status == "PASS" else ("INFO" if status == "INFO" else "FAIL")
        lines.append(
            f"- **{chk['name']}** - result: {chk['result']} - **{marker}**"
        )

    # Section 4 - Sample Queries
    lines += ["", "---", "", "## 4. Sample Queries", ""]
    for q in sample_queries:
        lines.append(f"### {q['title']}")
        lines.append("")
        cols = q["columns"]
        all_rows = [cols] + [[str(v) for v in row] for row in q["rows"]]
        widths = [max(len(r[i]) for r in all_rows) for i in range(len(cols))]
        def _fmt(values):
            return "  ".join(str(v).ljust(widths[i]) for i, v in enumerate(values))
        lines.append("```")
        lines.append(_fmt(cols))
        lines.append("  ".join("-" * widths[i] for i in range(len(cols))))
        for row in q["rows"]:
            lines.append(_fmt(row))
        lines.append("```")
        lines.append("")

    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    log.info("Summary report -> %s", report_path)


# =============================================================================
# MAIN
# =============================================================================

def main():
    log.info("ETL Pipeline - Drilling Operations (Dynamic Normalisation)")
    log.info("CSV : %s", CSV_PATH)
    log.info("DB  : %s", DB_PATH)

    raw_df         = extract(CSV_PATH)
    payload        = transform(raw_df)
    counts         = load(payload, DB_PATH)
    validation     = validate(DB_PATH)
    sample_queries = run_sample_queries(DB_PATH)

    report_path = os.path.join(SCRIPT_DIR, "etl_summary_report.md")
    write_summary(counts, validation, sample_queries, report_path)
    log.info("Done.")


if __name__ == "__main__":
    main()
