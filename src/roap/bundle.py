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


def verify_bundle(run_dir: Path, output_root: Optional[Path] = None) -> bool:
    """Verify a run bundle's integrity.

    Returns True if all hashes match the manifest, False otherwise.
    """
    manifest_path = run_dir / "run_bundle_manifest.json"
    if not manifest_path.exists():
        return False

    try:
        manifest = json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError):
        return False

    # Verify input file hash
    input_path = Path(manifest["input_file"]["path"])
    if not input_path.is_file():
        return False
    if compute_file_hash(input_path) != manifest["input_file"]["sha256"]:
        return False

    # Verify config file hashes
    for cfg in manifest.get("config_files", []):
        cfg_path = Path(cfg["path"])
        if not cfg_path.is_file():
            return False
        if compute_file_hash(cfg_path) != cfg["sha256"]:
            return False

    # Verify output file hashes
    for out in manifest.get("output_files", []):
        out_path = Path(out["path"])
        if not out_path.is_file():
            return False
        if compute_file_hash(out_path) != out["sha256"]:
            return False

    return True