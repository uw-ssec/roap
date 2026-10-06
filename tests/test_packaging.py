# tests/test_packaging.py
import tomllib


def test_pyproject_toml_exists_and_valid():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["name"] == "oa-pipeline"
    assert data["project"]["version"] == "0.2.0"
    assert data["build-system"]["build-backend"] == "setuptools.build_meta"
    assert "src" in data["tool"]["setuptools"]["packages"]["find"]["where"]
