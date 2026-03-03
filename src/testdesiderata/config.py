import tomllib
from pathlib import Path
from typing import cast


def load_config(start: Path) -> dict[str, object]:
    assert start is not None, "Start path must not be None"
    assert isinstance(start, Path), "Start must be a Path instance"
    for directory in [start, *start.parents]:
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            with candidate.open("rb") as f:
                raw = cast(dict[str, object], tomllib.load(f))
            tool = raw.get("tool")
            if not isinstance(tool, dict):
                return {}
            tool_section = cast(dict[str, object], tool)
            td = tool_section.get("testdesiderata")
            if not isinstance(td, dict):
                return {}
            return cast(dict[str, object], td)
    return {}


def config_to_csv(cfg: dict[str, object], key: str) -> str | None:
    assert cfg is not None, "Config must not be None"
    assert key, "Key must not be empty"
    val = cfg.get(key)
    if isinstance(val, list):
        items = cast(list[object], val)
        return ",".join(str(v) for v in items)
    return str(val) if isinstance(val, str) else None
