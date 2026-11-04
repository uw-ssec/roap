# tests/test_stage_bundle.py
"""Run bundles written by stage notebooks run without run_pipeline.sh (#13)."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _verify(out_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["roap", "verify-bundle", str(out_dir), "--json"], capture_output=True, text=True, encoding="utf-8"
    )


def _statuses(result: subprocess.CompletedProcess) -> dict[str, str]:
    report = json.loads(result.stdout)
    return {Path(c["path"]).name: (c["kind"], c["status"]) for c in report["checks"]}


# A run that began well before _make_stage_out wrote its files.
STARTED = time.time() - 60


def _make_stage_out(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A stage OUT_DIR as a notebook leaves it; returns (out_dir, input_csv, config_yaml)."""
    input_csv = tmp_path / "staged.csv"
    input_csv.write_text("a,b\n1,2\n", encoding="utf-8")
    config_yaml = tmp_path / "08_stage4.yaml"
    config_yaml.write_text("compatible_pipeline_version: '>=0.2.0'\n", encoding="utf-8")
    out_dir = tmp_path / "oa_stage4_outputs"
    for sub, name, text in [
        ("data", "analysis_ready.csv", "a,b\n1,2\n"),
        ("tables", "range_check_summary.csv", "check,n\nx,0\n"),
        ("reports", "report.md", "# Stage 4\n"),
        ("logs", "manifest.json", "{}\n"),
        ("logs", "effective_config.json", '{"k": 1}\n'),
    ]:
        (out_dir / sub).mkdir(parents=True, exist_ok=True)
        (out_dir / sub / name).write_text(text, encoding="utf-8")
    return out_dir, input_csv, config_yaml


def test_stage_bundle_records_input_configs_and_outputs(tmp_path):
    from roap.bundle import generate_stage_bundle_manifest

    out_dir, input_csv, config_yaml = _make_stage_out(tmp_path)
    manifest = generate_stage_bundle_manifest(
        out_dir, notebook="08_stage4", input_file=input_csv, config_files=[config_yaml, None, "None"], run_started=STARTED
    )

    assert manifest["scope"] == "stage"
    assert manifest["notebook"] == "08_stage4"
    assert manifest["input_file"]["path"] == str(input_csv.resolve())
    assert [Path(c["path"]).name for c in manifest["config_files"]] == ["08_stage4.yaml", "effective_config.json"]
    # Every file the stage wrote, except the effective config (recorded as a
    # config) and the bundle manifest itself.
    assert sorted(Path(o["path"]).relative_to(out_dir.resolve()).as_posix() for o in manifest["output_files"]) == [
        "data/analysis_ready.csv",
        "logs/manifest.json",
        "reports/report.md",
        "tables/range_check_summary.csv",
    ]
    assert (out_dir / "run_bundle_manifest.json").is_file()

    result = _verify(out_dir)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["valid"] is True


def test_stage_bundle_detects_changed_and_missing_files(tmp_path):
    from roap.bundle import generate_stage_bundle_manifest

    out_dir, input_csv, config_yaml = _make_stage_out(tmp_path)
    generate_stage_bundle_manifest(
        out_dir, notebook="08_stage4", input_file=input_csv, config_files=[config_yaml], run_started=STARTED
    )

    with (out_dir / "tables" / "range_check_summary.csv").open("a", encoding="utf-8") as f:
        f.write("y,1\n")
    (out_dir / "reports" / "report.md").unlink()
    config_yaml.write_text("compatible_pipeline_version: '>=9999.0.0'\n", encoding="utf-8")

    result = _verify(out_dir)
    assert result.returncode == 1
    statuses = _statuses(result)
    assert statuses["range_check_summary.csv"] == ("output", "mismatch")
    assert statuses["report.md"] == ("output", "missing")
    assert statuses["08_stage4.yaml"] == ("config", "mismatch")
    assert statuses["analysis_ready.csv"] == ("output", "ok")
    assert statuses["staged.csv"] == ("input", "ok")


def test_stage_bundle_git_commit_from_env(tmp_path, monkeypatch):
    from roap.bundle import generate_stage_bundle_manifest

    out_dir, input_csv, _ = _make_stage_out(tmp_path)
    monkeypatch.setenv("GIT_COMMIT", "deadbeef")
    manifest = generate_stage_bundle_manifest(out_dir, notebook="08_stage4", input_file=input_csv, run_started=STARTED)
    assert manifest["git_commit"] == "deadbeef"


def test_stage_bundle_skips_notebooks_saved_in_out_dir(tmp_path):
    """The executed notebook and its checkpoints are not hashed as outputs."""
    from roap.bundle import generate_stage_bundle_manifest

    out_dir, input_csv, _ = _make_stage_out(tmp_path)
    (out_dir / "08_stage4.run.ipynb").write_text("{}", encoding="utf-8")
    (out_dir / ".ipynb_checkpoints").mkdir()
    (out_dir / ".ipynb_checkpoints" / "08_stage4-checkpoint.ipynb").write_text("{}", encoding="utf-8")
    manifest = generate_stage_bundle_manifest(out_dir, notebook="08_stage4", input_file=input_csv, run_started=STARTED)
    assert not [o for o in manifest["output_files"] if "ipynb" in o["path"]]


def test_stage_bundle_leaves_out_files_from_an_earlier_run(tmp_path):
    """Files under OUT_DIR older than this run are listed as stale, not hashed."""
    from roap.bundle import generate_stage_bundle_manifest

    out_dir, input_csv, _ = _make_stage_out(tmp_path)
    old_parquet = out_dir / "data" / "analysis_ready.parquet"
    old_parquet.write_bytes(b"from an earlier run")
    old_effective = out_dir / "logs" / "effective_config.json"
    earlier = STARTED - 3600
    for path in (old_parquet, old_effective):
        os.utime(path, (earlier, earlier))

    manifest = generate_stage_bundle_manifest(out_dir, notebook="08_stage4", input_file=input_csv, run_started=STARTED)
    recorded = [o["path"] for o in manifest["output_files"]] + [c["path"] for c in manifest["config_files"]]
    assert str(old_parquet.resolve()) not in recorded
    assert str(old_effective.resolve()) not in recorded
    assert manifest["stale_files"] == sorted([str(old_parquet.resolve()), str(old_effective.resolve())])
    assert str((out_dir / "data" / "analysis_ready.csv").resolve()) in recorded

    result = _verify(out_dir)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "analysis_ready.parquet" not in _statuses(result)


def _papermill(notebook: str, executed: Path, *params: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "GIT_COMMIT"}
    args = [sys.executable, "-m", "papermill", notebook, str(executed)]
    for i in range(0, len(params), 2):
        args += ["-p", params[i], params[i + 1]]
    return subprocess.run(args, cwd=REPO_ROOT / "notebooks", capture_output=True, text=True, env=env, timeout=300)


@pytest.mark.slow
def test_notebook_04_rerun_without_parquet_leaves_old_parquet_out(tmp_path):
    """Rerunning a stage into the same OUT_DIR does not claim the earlier run's files.

    Run 04 with Parquet, change the input, rerun with NO_PARQUET=True: the
    retained Parquet came from the old input, so the new bundle must not
    hash it.
    """
    input_csv = tmp_path / "derived.csv"
    input_csv.write_text(
        "sample_id,sample_date,station_id,ta,ph\nS001,2024-01-01,ST1,2200,8.0\n", encoding="utf-8"
    )
    out_dir = tmp_path / "oa_stage1a_outputs"
    first = _papermill("04_stage1a.ipynb", tmp_path / "04.first.ipynb", "INPUT_CSV", str(input_csv), "OUT_DIR", str(out_dir))
    assert first.returncode == 0, first.stderr[-2000:]
    parquets = sorted(out_dir.rglob("*.parquet"))
    assert parquets, "first run should write Parquet"

    time.sleep(1.1)  # the second run starts in a later second than the first run's files
    input_csv.write_text(
        "sample_id,sample_date,station_id,ta,ph\nNEW_RUN_ONLY,2024-01-01,ST1,2200,8.0\n", encoding="utf-8"
    )
    second = _papermill(
        "04_stage1a.ipynb", out_dir / "04.second.ipynb",
        "INPUT_CSV", str(input_csv), "OUT_DIR", str(out_dir), "NO_PARQUET", "True",
    )
    assert second.returncode == 0, second.stderr[-2000:]

    manifest = json.loads((out_dir / "run_bundle_manifest.json").read_text(encoding="utf-8"))
    hashed = {o["path"] for o in manifest["output_files"]}
    for parquet in parquets:
        assert str(parquet.resolve()) not in hashed
        assert str(parquet.resolve()) in manifest["stale_files"]
    assert any(p.endswith(".csv") for p in hashed)
    assert not [p for p in hashed if p.endswith(".ipynb")]

    result = _verify(out_dir)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.slow
@pytest.mark.parametrize("save_inside_out_dir", [False, True], ids=["notebook-outside", "notebook-inside-out-dir"])
def test_notebook_02_run_directly_writes_verifiable_bundle(tmp_path, save_inside_out_dir):
    """Notebook 02 run by hand from notebooks/ (as JupyterLab does), no runner.

    Covers the default CRM certified-values path resolving from notebooks/,
    the stage bundle passing verify-bundle, and a changed or missing output
    failing it.
    """
    out_dir = tmp_path / "qc"
    # Papermill saves the executed notebook again after the bundle cell; when
    # it is saved inside OUT_DIR the bundle must still verify.
    executed = (out_dir if save_inside_out_dir else tmp_path) / "02.run.ipynb"
    out_dir.mkdir()
    env = {k: v for k, v in os.environ.items() if k != "GIT_COMMIT"}
    result = subprocess.run(
        [
            sys.executable, "-m", "papermill", "02_ta_ph_qc.ipynb", str(executed),
            "-p", "OUT_DIR", str(out_dir),
        ],
        cwd=REPO_ROOT / "notebooks", capture_output=True, text=True, env=env, timeout=300,
    )
    assert result.returncode == 0, result.stderr[-2000:]

    manifest = json.loads((out_dir / "run_bundle_manifest.json").read_text(encoding="utf-8"))
    assert manifest["notebook"] == "02_ta_ph_qc"
    assert Path(manifest["input_file"]["path"]) == (REPO_ROOT / "examples" / "example_data.xlsx").resolve()
    assert [Path(c["path"]).name for c in manifest["config_files"]] == ["crm_certified_values.yaml"]
    derived = [Path(o["path"]) for o in manifest["output_files"] if Path(o["path"]).name == "derived.csv"]
    assert len(derived) == 1
    assert executed.is_file()
    assert not [o for o in manifest["output_files"] if o["path"].endswith(".ipynb")]

    ok = _verify(out_dir)
    assert ok.returncode == 0, ok.stdout + ok.stderr

    with derived[0].open("a", encoding="utf-8") as f:
        f.write("\n")
    (out_dir / "logs" / "manifest.json").unlink()
    bad = _verify(out_dir)
    assert bad.returncode == 1
    statuses = _statuses(bad)
    assert statuses["derived.csv"] == ("output", "mismatch")
    assert statuses["manifest.json"] == ("output", "missing")
