from pathlib import Path

from testdesiderata.config import config_to_csv, load_config


def test_load_config_returns_empty_when_not_found(tmp_path: Path):
    result = load_config(tmp_path / "nonexistent")
    assert result == {}


def test_load_config_reads_testdesiderata_section(tmp_path: Path):
    _ = (tmp_path / "pyproject.toml").write_text(
        '[tool.testdesiderata]\nselect = ["DET"]\n'
    )
    result = load_config(tmp_path)
    assert result == {"select": ["DET"]}


def test_load_config_returns_empty_for_missing_section(tmp_path: Path):
    _ = (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
    result = load_config(tmp_path)
    assert result == {}


def test_config_to_csv_handles_list():
    assert config_to_csv({"select": ["DET", "FST"]}, "select") == "DET,FST"


def test_config_to_csv_handles_string():
    assert config_to_csv({"ignore": "BHV"}, "ignore") == "BHV"


def test_config_to_csv_returns_none_when_absent():
    assert config_to_csv({}, "select") is None
