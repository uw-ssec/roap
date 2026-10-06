import importlib
import pytest

MODULES = [
    "oa_pipeline",
    "oa_pipeline.common",
    "oa_pipeline.schema",
    "oa_pipeline.qc_ta_ph",
    "oa_pipeline.policy",
    "oa_pipeline.stage1b",
    "oa_pipeline.stage2",
    "oa_pipeline.stage3",
    "oa_pipeline.stage4",
    "oa_pipeline.inspect",
    "oa_pipeline.carbonate_calc",
    "oa_pipeline.duplicate_precision",
]

@pytest.mark.parametrize("module_name", MODULES)
def test_module_imports(module_name):
    importlib.import_module(module_name)