"""Tests for roap CLI (typer-based entry point)."""

import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_roap_cli_exists() -> None:
    """roap console script is installed and runnable."""
    result = subprocess.run(
        ["roap", "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower() or "commands" in result.stdout.lower()


def test_roap_validate_help() -> None:
    """roap validate --help works."""
    result = subprocess.run(
        ["roap", "validate", "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "validate" in result.stdout.lower()


def test_roap_verify_bundle_help() -> None:
    """roap verify-bundle --help works."""
    result = subprocess.run(
        ["roap", "verify-bundle", "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "verify" in result.stdout.lower()


def test_roap_validate_missing_input() -> None:
    """roap validate fails cleanly on missing input file."""
    result = subprocess.run(
        ["roap", "validate", "nonexistent.xlsx"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode != 0
    assert "error" in result.stderr.lower() or "error" in result.stdout.lower()


def test_roap_verify_bundle_missing_dir() -> None:
    """roap verify-bundle fails cleanly on missing directory."""
    result = subprocess.run(
        ["roap", "verify-bundle", "nonexistent_dir"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode != 0
    assert "error" in result.stderr.lower() or "error" in result.stdout.lower()