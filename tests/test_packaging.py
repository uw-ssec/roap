# tests/test_packaging.py
import tomllib


def test_pyproject_toml_exists_and_valid():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["name"] == "roap"
    assert data["project"]["dynamic"] == ["version"]
    assert data["build-system"]["build-backend"] == "hatchling.build"
    assert data["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["src/roap"]
