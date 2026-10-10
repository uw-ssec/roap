"""Migration gate: every module in the package must import.

Two layers:

1. ``CORE_MODULES`` — the 12 modules named in the P-1 migration plan. Kept as
   an explicit list so the gate still fails loudly if one is deleted or
   renamed, rather than silently shrinking.

2. ``test_every_module_in_package_imports`` — walks the package and imports
   EVERYTHING, including subpackages. This exists because the explicit
   12-module list did not cover ``roap.alka.*``, which allowed two modules to
   sit broken (``ModuleNotFoundError: oa_pipeline_app_core``) through a full
   green test run. Discovery-based, so new modules are covered automatically.
"""

import importlib
import pkgutil

import pytest

CORE_MODULES = [
    "roap",
    "roap.common",
    "roap.schema",
    "roap.qc_ta_ph",
    "roap.policy",
    "roap.stage1b",
    "roap.stage2",
    "roap.stage3",
    "roap.stage4",
    "roap.inspect",
    "roap.carbonate_calc",
    "roap.duplicate_precision",
]


def _discover_modules() -> list[str]:
    """Every importable module name in the roap package, recursively."""
    import roap

    found = ["roap"]
    for info in pkgutil.walk_packages(roap.__path__, prefix="roap."):
        found.append(info.name)
    return sorted(found)


@pytest.mark.parametrize("module_name", CORE_MODULES)
def test_core_module_imports(module_name: str) -> None:
    """The 12 modules required by the P-1 migration plan import cleanly."""
    importlib.import_module(module_name)


def test_core_modules_still_present() -> None:
    """Guard the list above against silent shrinkage."""
    assert len(CORE_MODULES) == 12, (
        f"Expected the 12 planned modules, found {len(CORE_MODULES)}. "
        "If a module was intentionally added/removed, update the plan too."
    )


@pytest.mark.parametrize("module_name", _discover_modules())
def test_every_module_in_package_imports(module_name: str) -> None:
    """Every module in the package imports — including GUI subpackages.

    Regression guard: ``roap.alka.runner`` and ``roap.alka.app`` were broken by
    the oa_pipeline->roap rename and no test caught it, because the migration
    gate only imported the 12 core modules.
    """
    importlib.import_module(module_name)
