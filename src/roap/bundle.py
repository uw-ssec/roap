import hashlib
import json
from datetime import datetime, timezone
from importlib.metadata import version as _pkg_version
from pathlib import Path
from .common import write_manifest, ensure_dir
from typing import Any, Dict, Optional


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


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

    # Config files hashes
    config_files: list[Dict[str, str]] = []
    if config_dir is not None and config_dir.is_dir():
        for cfg_path in sorted(config_dir.iterdir()):
            if cfg_path.is_file():
                config_files.append({"path": str(cfg_path.resolve()), "sha256": compute_file_hash(cfg_path)})

    # Output files hashes (from output_root/oa_stage*_outputs/data/ if provided, else run_dir)
    output_files: list[Dict[str, str]] = []
    search_root = output_root if output_root is not None else run_dir
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


def check_bundle(run_dir: Path) -> Dict[str, Any]:
    """Check every hash recorded in a run bundle manifest.

    Returns a report dict: ``valid`` (bool), ``manifest`` (path), ``error``
    (str or None, set when the manifest itself is missing or unreadable) and
    ``checks``, one entry per recorded file with ``kind`` (input, config or
    output), ``path``, ``expected``, ``actual`` and ``status`` (ok, mismatch
    or missing). Every file is checked, so the report lists all problems.
    """
    manifest_path = run_dir / "run_bundle_manifest.json"
    report: Dict[str, Any] = {"valid": False, "manifest": str(manifest_path), "error": None, "checks": []}

    if not manifest_path.is_file():
        report["error"] = f"Manifest not found: {manifest_path}"
        return report
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = [("input", manifest["input_file"])]
        entries += [("config", cfg) for cfg in manifest.get("config_files", [])]
        entries += [("output", out) for out in manifest.get("output_files", [])]
        records = [(kind, Path(entry["path"]), entry["sha256"]) for kind, entry in entries]
    except (json.JSONDecodeError, OSError, KeyError, TypeError) as e:
        report["error"] = f"Unreadable manifest {manifest_path}: {e!r}"
        return report

    for kind, path, expected in records:
        actual = compute_file_hash(path) if path.is_file() else None
        if actual is None:
            status = "missing"
        elif actual == expected:
            status = "ok"
        else:
            status = "mismatch"
        report["checks"].append(
            {"kind": kind, "path": str(path), "expected": expected, "actual": actual, "status": status}
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
