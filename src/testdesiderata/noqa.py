import io
import re
import tokenize

from testdesiderata.models import Violation

_NOQA_PATTERN = r"noqa\b(?::\s*(?P<codes>[\w, ]+))?"


def _comments_by_line(source: str) -> dict[int, str]:
    assert source is not None, "Source must not be None"
    assert isinstance(source, str), "Source must be a str"
    comments: dict[int, str] = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                comments[tok.start[0]] = tok.string
    except (tokenize.TokenError, SyntaxError, IndentationError):
        return {}
    return comments


def _suppressed_codes(comment: str) -> set[str] | None:
    assert comment is not None, "Comment must not be None"
    assert isinstance(comment, str), "Comment must be a str"
    match = re.search(_NOQA_PATTERN, comment, re.IGNORECASE)
    if not match:
        return None
    codes = match.group("codes")
    if not codes:
        return {"*"}
    return {c.strip().upper() for c in codes.split(",") if c.strip()}


def _code_matches(rule_id: str, code: str) -> bool:
    assert rule_id, "Rule ID must not be empty"
    assert code, "Code must not be empty"
    return code == "*" or rule_id == code or rule_id.startswith(code)


def filter_noqa(violations: list[Violation], source: str) -> list[Violation]:
    """Drop violations whose line carries a `# noqa` / `# noqa: CODE` comment."""
    assert violations is not None, "Violations must not be None"
    assert source is not None, "Source must not be None"
    comments = _comments_by_line(source)
    if not comments:
        return violations
    kept: list[Violation] = []
    for v in violations:
        codes = _suppressed_codes(comments.get(v.line, ""))
        if codes and any(_code_matches(v.rule_id, code) for code in codes):
            continue
        kept.append(v)
    return kept
