#!/usr/bin/env bash
# =====================================================================
# run_pipeline.sh — drive the OA pipeline end to end.
#
# Stage QC and Stages 1A to 4 run in process through `roap run`
# (roap.pipeline.run_pipeline). Only the optional notebooks 01 and 03 run
# through papermill.
#
# Usage:
#     ./run_pipeline.sh INPUT_XLSX OUTPUT_ROOT [options]
#
# Required arguments:
#     INPUT_XLSX     Path to the input Excel workbook.
#     OUTPUT_ROOT    Directory where every stage output will be written.
#
# Options:
#     --sheet N           Zero based Excel sheet index to process.
#                         Default: 0.
#     --config-dir DIR    Directory containing optional per stage YAML, YML,
#                         or JSON config overrides.
#
#                         The runner looks for these filenames:
#                             02_ta_ph_qc.yaml, 02_ta_ph_qc.yml, or 02_ta_ph_qc.json
#                             04_stage1a.yaml, 04_stage1a.yml, or 04_stage1a.json
#                             05_stage1b.yaml, 05_stage1b.yml, or 05_stage1b.json
#                             06_stage2.yaml, 06_stage2.yml, or 06_stage2.json
#                             07_stage3.yaml, 07_stage3.yml, or 07_stage3.json
#                             08_stage4.yaml, 08_stage4.yml, or 08_stage4.json
#
#                         Files such as cruise_grade_thresholds.yaml and
#                         regional.yaml are not automatically loaded by this
#                         runner unless the notebooks load them internally.
#                         The simplest current pattern is to create per stage
#                         config files that include or duplicate those settings.
#     --no-parquet        Write CSV only for stages 04 to 08.
#     --include-viewer    Also run Notebook 01.
#     --include-review    Also run Notebook 03.
#     --start-from STAGE  Skip stages before STAGE. STAGE must be one of:
#                         02, 04, 05, 06, 07, 08.
#     --dry-run           Print the commands but do not run them.
#                         In dry run mode, required output files,
#                         Papermill, and roap import checks are skipped.
#     -h, --help          Show this help and exit.
#
# Environment:
#     PYTHON_BIN          Optional Python executable to use. Defaults to python.
#                         Example:
#                             PYTHON_BIN=.venv/Scripts/python.exe ./run_pipeline.sh ...
#
# Examples:
#     ./run_pipeline.sh data/oa_prelim_data.xlsx outputs/real
#
#     ./run_pipeline.sh data/oa_prelim_data.xlsx outputs/real \
#         --include-viewer --include-review
#
#     ./run_pipeline.sh data/oa_prelim_data.xlsx outputs/real \
#         --start-from 06
#
#     ./run_pipeline.sh data/oa_prelim_data.xlsx outputs/real \
#         --config-dir configs
# =====================================================================

set -euo pipefail

# ---------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------

SHEET=0
CONFIG_DIR=""
NO_PARQUET="False"
INCLUDE_VIEWER=0
INCLUDE_REVIEW=0
START_FROM="02"
DRY_RUN=0
INPUT_XLSX=""
OUTPUT_ROOT=""
PYTHON_BIN="${PYTHON_BIN:-python}"

# ---------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------

usage() {
    awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"
}

need_value() {
    local opt="$1"
    local val="${2:-}"

    if [[ -z "$val" || "$val" == -* ]]; then
        echo "ERROR: $opt requires a value." >&2
        usage
        exit 2
    fi
}

stage_index() {
    case "$1" in
        02) echo 2 ;;
        04) echo 4 ;;
        05) echo 5 ;;
        06) echo 6 ;;
        07) echo 7 ;;
        08) echo 8 ;;
        *)
            echo "ERROR: --start-from must be one of 02, 04, 05, 06, 07, or 08. Got: $1" >&2
            exit 2
            ;;
    esac
}

# ---------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --sheet)
            need_value "$1" "${2:-}"
            SHEET="$2"
            shift 2
            ;;
        --config-dir)
            need_value "$1" "${2:-}"
            CONFIG_DIR="$2"
            shift 2
            ;;
        --no-parquet)
            NO_PARQUET="True"
            shift
            ;;
        --include-viewer)
            INCLUDE_VIEWER=1
            shift
            ;;
        --include-review)
            INCLUDE_REVIEW=1
            shift
            ;;
        --start-from)
            need_value "$1" "${2:-}"
            START_FROM="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -*)
            echo "ERROR: unknown option: $1" >&2
            usage
            exit 2
            ;;
        *)
            if [[ -z "$INPUT_XLSX" ]]; then
                INPUT_XLSX="$1"
            elif [[ -z "$OUTPUT_ROOT" ]]; then
                OUTPUT_ROOT="$1"
            else
                echo "ERROR: unexpected extra argument: $1" >&2
                usage
                exit 2
            fi
            shift
            ;;
    esac
done

if [[ -z "$INPUT_XLSX" || -z "$OUTPUT_ROOT" ]]; then
    echo "ERROR: INPUT_XLSX and OUTPUT_ROOT are required." >&2
    usage
    exit 2
fi

if ! [[ "$SHEET" =~ ^[0-9]+$ ]]; then
    echo "ERROR: --sheet must be a zero based integer such as 0, 1, or 2." >&2
    exit 2
fi

START_IDX="$(stage_index "$START_FROM")"

should_run() {
    local idx="$1"
    [[ "$idx" -ge "$START_IDX" ]]
}

# AUDIT FIX N-5: Warn when --start-from skips Stage 2 (06). Stage 4 (08)
# requires the depth_round_m key column, which is normally produced by Stage 2.
# A direct jump to Stage 4 relies on Stage 4's depth_round_m fallback (FIX 8-B),
# which derives a coarse key from depth_m. That fallback keeps the run from
# marking every row FAIL, but it is NOT a substitute for Stage 2's proper depth
# binning. Make this explicit so operators do not silently ship coarsely-keyed
# data. Stage 2 index is 6; warn if we start at or after Stage 3 (07).
STAGE2_IDX="$(stage_index 06)"
if [[ "$START_IDX" -gt "$STAGE2_IDX" ]]; then
    echo "WARNING: --start-from $START_FROM skips Stage 2 (06_stage2)." >&2
    echo "         Stage 4 needs depth_round_m, normally created by Stage 2." >&2
    echo "         Stage 4's depth_round_m fallback (derived from depth_m) will" >&2
    echo "         be used if the upstream input lacks it. This avoids a total" >&2
    echo "         FAIL but does not replace Stage 2's depth binning. Re-run" >&2
    echo "         from Stage 2 for proper depth keys before final delivery." >&2
fi

# ---------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------
# Resolve user supplied paths before changing into the project root. This
# allows the script to be launched from outside the repository while still
# accepting relative paths from the caller's current directory.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && { pwd -W 2>/dev/null || pwd; })"
NOTEBOOK_DIR="$SCRIPT_DIR/notebooks"

# win_pwd: print the current directory in a form that the *Windows* Python
# interpreter (run via papermill) can parse. Under Git Bash / MSYS2, plain
# `pwd` returns a mount path like /c/Users/... which Windows pathlib reads
# as \c\Users\... on the current drive — causing the notebooks to die with
# "File not found". `pwd -W` returns the Windows form (C:/Users/...) that
# both bash and Windows Python accept. On macOS/Linux there is no -W flag,
# so fall back to plain pwd.
win_pwd() {
    if pwd -W >/dev/null 2>&1; then
        pwd -W
    else
        pwd
    fi
}

abs_file() {
    local path="$1"

    if [[ ! -f "$path" ]]; then
        echo "ERROR: file not found: $path" >&2
        exit 2
    fi

    local dir
    local base
    dir="$(cd "$(dirname "$path")" && win_pwd)"
    base="$(basename "$path")"
    printf "%s/%s\n" "$dir" "$base"
}

abs_existing_dir() {
    local path="$1"

    if [[ ! -d "$path" ]]; then
        echo "ERROR: directory not found: $path" >&2
        exit 2
    fi

    (cd "$path" && win_pwd)
}

abs_dir_create() {
    local path="$1"
    mkdir -p "$path"
    (cd "$path" && win_pwd)
}

INPUT_XLSX="$(abs_file "$INPUT_XLSX")"
OUTPUT_ROOT="$(abs_dir_create "$OUTPUT_ROOT")"

if [[ -n "$CONFIG_DIR" ]]; then
    CONFIG_DIR="$(abs_existing_dir "$CONFIG_DIR")"
fi

cd "$SCRIPT_DIR"

if [[ ! -d "$NOTEBOOK_DIR" ]]; then
    echo "ERROR: notebook directory not found: $NOTEBOOK_DIR" >&2
    exit 2
fi

TIMESTAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
RUNS_DIR="$SCRIPT_DIR/runs/${TIMESTAMP}_pid$$"
mkdir -p "$RUNS_DIR"

# ---------------------------------------------------------------------
# Dependency and file checks
# ---------------------------------------------------------------------

if [[ "$DRY_RUN" -eq 0 ]]; then
    "$PYTHON_BIN" -c "import roap" >/dev/null 2>&1 || {
        echo "ERROR: roap is not importable in this Python environment." >&2
        echo "Install with: pixi install (then use the pixi environment's python)" >&2
        exit 2
    }

    # Only the optional notebooks 01 and 03 still run through papermill.
    if [[ "$INCLUDE_VIEWER" -eq 1 || "$INCLUDE_REVIEW" -eq 1 ]]; then
        "$PYTHON_BIN" -c "import papermill" >/dev/null 2>&1 || {
            echo "ERROR: papermill is not installed in this Python environment." >&2
            echo "It is needed for --include-viewer and --include-review." >&2
            exit 2
        }
    fi
fi

require_file() {
    local path="$1"
    local label="$2"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        return 0
    fi

    if [[ ! -f "$path" ]]; then
        echo "ERROR: missing required input for $label:" >&2
        echo "  $path" >&2
        echo "Run earlier stages first or use the correct OUTPUT_ROOT." >&2
        exit 2
    fi
}

require_notebook() {
    local path="$1"

    if [[ ! -f "$path" ]]; then
        echo "ERROR: notebook not found: $path" >&2
        exit 2
    fi
}

if [[ "$INCLUDE_VIEWER" -eq 1 ]]; then
    require_notebook "$NOTEBOOK_DIR/01_excel_viewer.ipynb"
fi
if [[ "$INCLUDE_REVIEW" -eq 1 ]]; then
    require_notebook "$NOTEBOOK_DIR/03_qc_output_review.ipynb"
fi

# ---------------------------------------------------------------------
# Per stage output directories
# ---------------------------------------------------------------------

QC_OUT="$OUTPUT_ROOT/oa_prelim_data__qc_outputs"
S4_OUT="$OUTPUT_ROOT/oa_stage4_outputs"
VIEWER_OUT="$OUTPUT_ROOT/oa_viewer_outputs"

# ---------------------------------------------------------------------
# Runtime helpers
# ---------------------------------------------------------------------

resolve_qc_sheet_folder() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "sheet_$SHEET"
        return 0
    fi

    "$PYTHON_BIN" - "$INPUT_XLSX" "$SHEET" <<'PY'
from pathlib import Path
import sys

import pandas as pd

from roap.common import safe_sheet_name

xlsx = Path(sys.argv[1])
sheet_index = int(sys.argv[2])

excel = pd.ExcelFile(xlsx, engine="openpyxl")

if sheet_index < 0 or sheet_index >= len(excel.sheet_names):
    raise SystemExit(
        f"Sheet index {sheet_index} is out of range. "
        f"Workbook has {len(excel.sheet_names)} sheets."
    )

print("sheet_" + safe_sheet_name(excel.sheet_names[sheet_index]))
PY
}

resolve_qc_derived_csv() {
    local sheet_folder
    sheet_folder="$(resolve_qc_sheet_folder)"
    local expected="$QC_OUT/$sheet_folder/data/derived.csv"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "$expected"
        return 0
    fi

    if [[ -f "$expected" ]]; then
        echo "$expected"
        return 0
    fi

    if [[ ! -d "$QC_OUT" ]]; then
        echo "ERROR: could not find Notebook 02 output folder:" >&2
        echo "  $QC_OUT" >&2
        echo "Run Notebook 02 first or use the correct OUTPUT_ROOT." >&2
        exit 2
    fi

    mapfile -t matches < <(find "$QC_OUT" -type f -path "*/data/derived.csv" | sort)

    if [[ "${#matches[@]}" -eq 1 ]]; then
        echo "${matches[0]}"
        return 0
    fi

    if [[ "${#matches[@]}" -eq 0 ]]; then
        echo "ERROR: could not find Notebook 02 derived.csv under:" >&2
        echo "  $QC_OUT" >&2
        exit 2
    fi

    echo "ERROR: multiple derived.csv files found under $QC_OUT:" >&2
    printf '  %s\n' "${matches[@]}" >&2
    echo "Use --sheet or clean OUTPUT_ROOT so only one sheet output is present." >&2
    exit 2
}

run_papermill() {
    local notebook="$1"
    local out_ipynb="$2"
    shift 2
    local -a args=("$@")

    echo "----------------------------------------------------------------------"
    echo "$PYTHON_BIN -m papermill $notebook"
    for arg in "${args[@]}"; do
        echo "    $arg"
    done
    echo "  -> $out_ipynb"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        return 0
    fi

    "$PYTHON_BIN" -m papermill "$notebook" "$out_ipynb" "${args[@]}"
}

# ---------------------------------------------------------------------
# Run chain header
# ---------------------------------------------------------------------

echo "======================================================================"
echo "OA pipeline run"
echo "  input xlsx   : $INPUT_XLSX"
echo "  output root  : $OUTPUT_ROOT"
echo "  notebook dir : $NOTEBOOK_DIR"
echo "  python bin   : $PYTHON_BIN"
echo "  sheet        : $SHEET"
echo "  start from   : Stage $START_FROM"
echo "  config dir   : ${CONFIG_DIR:-(none)}"
echo "  engine       : roap run (in process)"
echo "  parquet      : $( [[ "$NO_PARQUET" == "True" ]] && echo disabled || echo enabled )"
echo "  dry run      : $( [[ "$DRY_RUN" -eq 1 ]] && echo yes || echo no )"
echo "  runs dir     : $RUNS_DIR"
echo "======================================================================"

# ---------------------------------------------------------------------
# Notebook 01: Optional Excel viewer
# ---------------------------------------------------------------------

if [[ "$INCLUDE_VIEWER" -eq 1 ]] && should_run 2; then
    run_papermill "$NOTEBOOK_DIR/01_excel_viewer.ipynb" "$RUNS_DIR/01_excel_viewer.run.ipynb" \
        -p XLSX_PATH "$INPUT_XLSX" \
        -p OUT_DIR "$VIEWER_OUT" \
        -p SHEET "$SHEET"
fi

# ---------------------------------------------------------------------
# Stage QC and Stages 1A to 4, plus the run bundle: roap run (ADR-0011)
# ---------------------------------------------------------------------
# roap run resolves each Stage's config in CONFIG_DIR, writes every Stage
# under OUTPUT_ROOT and writes run_bundle_manifest.json into RUNS_DIR.

ROAP_ARGS=(-m roap run "$INPUT_XLSX" "$OUTPUT_ROOT"
    --sheet "$SHEET"
    --start-from "$START_FROM"
    --runs-dir "$RUNS_DIR")
if [[ -n "$CONFIG_DIR" ]]; then
    ROAP_ARGS+=(--config-dir "$CONFIG_DIR")
fi
if [[ "$NO_PARQUET" == "True" ]]; then
    ROAP_ARGS+=(--no-parquet)
fi

echo "----------------------------------------------------------------------"
echo "$PYTHON_BIN ${ROAP_ARGS[*]}"
if [[ "$DRY_RUN" -eq 0 ]]; then
    export GIT_COMMIT="${GIT_COMMIT:-$(git rev-parse HEAD 2>/dev/null || echo unknown)}"
    "$PYTHON_BIN" "${ROAP_ARGS[@]}"
fi

# ---------------------------------------------------------------------
# Notebook 03: Optional QC output review
# ---------------------------------------------------------------------

if [[ "$INCLUDE_REVIEW" -eq 1 ]] && should_run 2; then
    QC_DERIVED_CSV="$(resolve_qc_derived_csv)"
    require_file "$QC_DERIVED_CSV" "Notebook 03 review"

    run_papermill "$NOTEBOOK_DIR/03_qc_output_review.ipynb" "$RUNS_DIR/03_qc_output_review.run.ipynb" \
        -p OUTPUT_ROOT "$QC_OUT"
fi

# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------

echo "======================================================================"
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Dry run complete. Re run without --dry-run to execute."
else
    echo "Pipeline complete."
    echo "  Final deliverable : $S4_OUT/data/analysis_ready.csv"
    echo "  Per stage reports : $OUTPUT_ROOT/<stage>/reports/report.md"
    echo "  Run bundle        : $RUNS_DIR/run_bundle_manifest.json"
fi
echo "======================================================================"
