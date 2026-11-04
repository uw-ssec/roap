import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from importlib.metadata import version as _pkg_version
from pathlib import Path
from .common import write_manifest, ensure_dir
from typing import Any, Dict, Iterable, Optional, Union


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# Keys in a stage's logs/manifest.json "config" block that name a config file
# the stage loaded.
_STAGE_CONFIG_PATH_KEYS = ("config_path", "crm_values_path")


def _stage_config_files(search_root: Path) -> list[Path]:
    """Config files the pipeline stages under ``search_root`` actually used.

    Each stage's ``logs/effective_config.json`` (the resolved settings), and
    any file a stage's ``logs/manifest.json`` records under ``config`` (for
    example the CRM certified-values YAML that notebook 02 loads by default).
    """
    found: list[Path] = []
    for logs in sorted(search_root.glob("oa_*_outputs/logs")):
        effective = logs / "effective_config.json"
        if effective.is_file():
            found.append(effective)
        stage_manifest = logs / "manifest.json"
        if not stage_manifest.is_file():
            continue
        try:
            config = json.loads(stage_manifest.read_text(encoding="utf-8")).get("config") or {}
        except (ValueError, OSError, AttributeError):
            continue
        for key in _STAGE_CONFIG_PATH_KEYS:
            value = config.get(key) if isinstance(config, dict) else None
            if isinstance(value, str) and Path(value).is_file():
                found.append(Path(value))
    return found


def generate_run_bundle_manifest(
    run_dir: Path,
    input_xlsx: Path,
    config_dir: Optional[Path],
    git_commit: str,
    pipeline_version: str,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Generate a run bundle manifest with hashes and metadata.

    Produces a manifest dict written to ``run_dir / "run_bundle_manifest.json"``.
    All paths in the manifest are absolute.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

    # Input file hash
    input_sha256 = compute_file_hash(input_xlsx)

    search_root = output_root if output_root is not None else run_dir

    # Config files hashes: the --config-dir files, plus what the stages
    # actually used (see _stage_config_files), so a default run with no
    # --config-dir still records its configuration.
    config_paths: list[Path] = []
    if config_dir is not None and config_dir.is_dir():
        config_paths += [p for p in sorted(config_dir.iterdir()) if p.is_file()]
    config_paths += _stage_config_files(search_root)
    config_files: list[Dict[str, str]] = []
    seen: set[Path] = set()
    for cfg_path in config_paths:
        resolved = cfg_path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            config_files.append({"path": str(resolved), "sha256": compute_file_hash(cfg_path)})

    # Output files hashes (from output_root/oa_stage*_outputs/data/ if provided, else run_dir)
    output_files: list[Dict[str, str]] = []
    for stage_dir in sorted(search_root.glob("oa_stage*_outputs/data")):
        for out_file in sorted(stage_dir.iterdir()):
            if out_file.is_file():
                output_files.append({"path": str(out_file.resolve()), "sha256": compute_file_hash(out_file)})

    # Package versions
    package_versions: Dict[str, str] = {"roap": pipeline_version}
    try:
        package_versions["pyco2sys"] = _pkg_version("pyco2sys")
    except Exception:
        package_versions["pyco2sys"] = "unknown"

    manifest: Dict[str, Any] = {
        "schema_version": "1.0",
        "timestamp": timestamp,
        "git_commit": git_commit,
        "pipeline_version": pipeline_version,
        "input_file": {"path": str(input_xlsx.resolve()), "sha256": input_sha256},
        "config_files": config_files,
        "output_files": output_files,
        "package_versions": package_versions,
    }

    manifest_path = run_dir / "run_bundle_manifest.json"
    write_manifest(manifest_path, manifest)

    return manifest


def _current_git_commit() -> str:
    """The commit of the roap checkout, for notebook runs outside the runner.

    ``GIT_COMMIT`` wins when set (run_pipeline.sh exports it). Otherwise ask
    git about the directory holding this module, which is the repository for
    an editable install; an installed wheel has no repository and gets
    ``unknown``.
    """
    env = os.environ.get("GIT_COMMIT")
    if env:
        return env
    try:
        result = subprocess.run(
            ["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "unknown"


def _is_notebook_file(rel_path: Path) -> bool:
    """A Jupyter notebook or checkpoint under a stage OUT_DIR.

    No stage writes notebooks as outputs. One found there is the running
    notebook itself (Papermill or JupyterLab saved it into OUT_DIR), which is
    saved again after the bundle cell runs, so hashing it would make every
    such bundle fail verification.
    """
    return rel_path.suffix == ".ipynb" or ".ipynb_checkpoints" in rel_path.parts


# A file's identity for snapshot_out_dir: inode, size and mtime in nanoseconds.
_FileState = tuple[int, int, int]


def _file_state(path: Path) -> _FileState:
    st = path.stat()
    return (st.st_ino, st.st_size, st.st_mtime_ns)


def snapshot_out_dir(out_dir: Union[str, Path]) -> Dict[str, _FileState]:
    """Record the files already under ``out_dir`` before a stage notebook writes.

    Pass the result to ``generate_stage_bundle_manifest(before=...)``. A file
    that is new, or whose inode, size or nanosecond mtime differs from this
    snapshot, was written by the current run; one that is unchanged was left
    by an earlier run. Comparing states rather than a wall-clock cutoff keeps
    this correct when two runs happen within the same second (for example
    rerunning cells in a warm Jupyter kernel).
    """
    out_dir = Path(out_dir).resolve()
    if not out_dir.is_dir():
        return {}
    return {str(p.resolve()): _file_state(p) for p in out_dir.rglob("*") if p.is_file()}


def generate_stage_bundle_manifest(
    out_dir: Path,
    notebook: str,
    input_file: Path,
    config_files: Iterable[Optional[Union[str, Path]]] = (),
    *,
    before: Dict[str, _FileState],
) -> Dict[str, Any]:
    """Write a run bundle for one stage notebook run, into ``out_dir``.

    Lets a stage notebook run by hand (without run_pipeline.sh) be checked
    with ``roap verify-bundle <out_dir>``. Records the stage's input file,
    its configuration (each config file it loaded, plus
    ``logs/effective_config.json``) and every file it wrote under
    ``out_dir``. ``logs/`` holds the run's own provenance (the stage
    manifest and audit logs) and is hashed as output too, except the
    effective config, which is recorded as config, and notebooks (see
    ``_is_notebook_file``). ``None`` entries in
    ``config_files`` (no config file used) are skipped.

    ``before`` is the ``snapshot_out_dir(out_dir)`` taken at the start of the
    run, before it wrote anything. Only files this run created or rewrote
    are hashed; files left unchanged from an earlier run (say Parquet from a
    run before ``NO_PARQUET=True``) are listed under ``stale_files`` instead
    so the analyst can see what was left out.
    """
    from roap import __version__

    out_dir = Path(out_dir).resolve()
    manifest_path = out_dir / "run_bundle_manifest.json"

    config_paths = [Path(p) for p in config_files if p is not None and str(p).strip().lower() not in ("", "none", "null")]

    def _from_this_run(path: Path) -> bool:
        return before.get(str(path.resolve())) != _file_state(path)

    effective = out_dir / "logs" / "effective_config.json"
    stale_files: list[str] = []
    if effective.is_file():
        if _from_this_run(effective):
            config_paths.append(effective)
        else:
            stale_files.append(str(effective))
    recorded_configs: list[Dict[str, str]] = []
    seen: set[Path] = set()
    for cfg_path in config_paths:
        resolved = cfg_path.expanduser().resolve()
        if resolved.is_file() and resolved not in seen:
            seen.add(resolved)
            recorded_configs.append({"path": str(resolved), "sha256": compute_file_hash(resolved)})

    output_files: list[Dict[str, str]] = []
    for out_file in sorted(out_dir.rglob("*")):
        resolved = out_file.resolve()
        if _is_notebook_file(out_file.relative_to(out_dir)):
            continue
        if not out_file.is_file() or resolved == manifest_path or resolved in seen or resolved == effective:
            continue
        if _from_this_run(out_file):
            output_files.append({"path": str(resolved), "sha256": compute_file_hash(out_file)})
        else:
            stale_files.append(str(resolved))

    package_versions: Dict[str, str] = {"roap": __version__}
    try:
        package_versions["pyco2sys"] = _pkg_version("pyco2sys")
    except Exception:
        package_versions["pyco2sys"] = "unknown"

    input_path = Path(input_file).expanduser().resolve()
    manifest: Dict[str, Any] = {
        "schema_version": "1.0",
        "scope": "stage",
        "notebook": notebook,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ"),
        "git_commit": _current_git_commit(),
        "pipeline_version": __version__,
        "input_file": {"path": str(input_path), "sha256": compute_file_hash(input_path)},
        "config_files": recorded_configs,
        "output_files": output_files,
        "stale_files": sorted(stale_files),
        "package_versions": package_versions,
    }
    write_manifest(manifest_path, manifest)
    return manifest


def check_bundle(run_dir: Path) -> Dict[str, Any]:
    """Check every hash recorded in a run bundle manifest.

    Returns a report dict: ``valid`` (bool), ``manifest`` (path), ``error``
    (str or None, set when the manifest itself is missing or unreadable) and
    ``checks``, one entry per recorded file with ``kind`` (input, config or
    output), ``path``, ``expected``, ``actual``, ``status`` (ok, mismatch,
    missing or unreadable) and ``reason`` (the read error for unreadable
    files). Every file is checked, so the report lists all problems.
    """
    manifest_path = run_dir / "run_bundle_manifest.json"
    report: Dict[str, Any] = {"valid": False, "manifest": str(manifest_path), "error": None, "checks": []}

    try:
        if not manifest_path.is_file():
            report["error"] = f"Manifest not found: {manifest_path}"
            return report
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = [("input", manifest["input_file"])]
        entries += [("config", cfg) for cfg in manifest.get("config_files", [])]
        entries += [("output", out) for out in manifest.get("output_files", [])]
        records = [(kind, Path(entry["path"]), entry["sha256"]) for kind, entry in entries]
    except (ValueError, OSError, KeyError, TypeError) as e:  # ValueError covers JSON and UTF-8 decode errors
        report["error"] = f"Unreadable manifest {manifest_path}: {e!r}"
        return report

    for kind, path, expected in records:
        actual: Optional[str] = None
        reason: Optional[str] = None
        # is_file() can raise too (e.g. PermissionError on an inaccessible
        # parent directory), so it sits inside the handler with the read.
        try:
            if not path.is_file():
                status = "missing"
            else:
                actual = compute_file_hash(path)
                status = "ok" if actual == expected else "mismatch"
        except OSError as e:
            actual, status, reason = None, "unreadable", repr(e)
        report["checks"].append(
            {
                "kind": kind,
                "path": str(path),
                "expected": expected,
                "actual": actual,
                "status": status,
                "reason": reason,
            }
        )

    report["valid"] = all(c["status"] == "ok" for c in report["checks"])
    return report


def verify_bundle(run_dir: Path, output_root: Optional[Path] = None) -> bool:
    """Verify a run bundle's integrity.

    Returns True if all hashes match the manifest, False otherwise.
    ``output_root`` is accepted for compatibility; the manifest records
    absolute paths, so it is not needed.
    """
    return bool(check_bundle(run_dir)["valid"])
