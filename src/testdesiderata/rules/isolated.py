import ast

from testdesiderata.models import Violation
from testdesiderata.rules.base import test_functions

_FILE_IO_ATTRS = {"read_text", "read_bytes", "write_text", "write_bytes"}
_TMP_FIXTURE_NAMES = {"tmp_path", "tmp_path_factory", "tmpdir"}
_NETWORK_MODULES: dict[str, set[str]] = {
    "requests": {"get", "post", "put", "delete", "patch", "head", "request"},
    "httpx": {"get", "post", "put", "delete", "patch", "head", "request"},
    "aiohttp": {"ClientSession"},
    "urllib": {"urlopen"},
}
_DB_MODULES: dict[str, set[str]] = {
    "sqlite3": {"connect"},
    "psycopg2": {"connect"},
    "pymysql": {"connect"},
    "asyncpg": {"connect", "create_pool"},
}
_DB_FACTORIES = {"create_engine", "MongoClient"}
_TEMPFILE_MODULES: dict[str, set[str]] = {
    "tempfile": {
        "mkstemp",
        "mkdtemp",
        "TemporaryFile",
        "NamedTemporaryFile",
        "TemporaryDirectory",
        "SpooledTemporaryFile",
    }
}
_SHUTIL_MODULES: dict[str, set[str]] = {
    "shutil": {
        "copy",
        "copy2",
        "copyfile",
        "copytree",
        "move",
        "rmtree",
        "make_archive",
    }
}
_SUBPROCESS_MODULES: dict[str, set[str]] = {
    "subprocess": {"run", "Popen", "call", "check_call", "check_output"},
    "os": {"system", "popen"},
}
_MAX_ROOT_NAME_DEPTH = 10


def _root_name(expr: ast.expr) -> str | None:
    assert expr is not None, "Expression node must not be None"
    assert isinstance(expr, ast.expr), "Expression must be an ast.expr"
    for _ in range(_MAX_ROOT_NAME_DEPTH):
        if isinstance(expr, ast.Name):
            return expr.id
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Div):
            expr = expr.left
            continue
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute):
            expr = expr.func.value
            continue
        if isinstance(expr, ast.Attribute):
            expr = expr.value
            continue
        return None
    return None


def _module_call_name(node: ast.Call, modules: dict[str, set[str]]) -> str | None:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    func = node.func
    if not isinstance(func, ast.Attribute) or not isinstance(func.value, ast.Name):
        return None
    module, attr = func.value.id, func.attr
    if module in modules and attr in modules[module]:
        return f"{module}.{attr}()"
    return None


def _file_io_name(node: ast.Call) -> str | None:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    func = node.func
    if isinstance(func, ast.Name) and func.id == "open":
        if node.args and _root_name(node.args[0]) in _TMP_FIXTURE_NAMES:
            return None
        return "open()"
    if isinstance(func, ast.Attribute) and func.attr in _FILE_IO_ATTRS:
        if _root_name(func.value) in _TMP_FIXTURE_NAMES:
            return None
        return f".{func.attr}()"
    return None


def _network_name(node: ast.Call) -> str | None:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    return _module_call_name(node, _NETWORK_MODULES)


def _db_name(node: ast.Call) -> str | None:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        if func.value.id in _DB_MODULES and func.attr in _DB_MODULES[func.value.id]:
            return f"{func.value.id}.{func.attr}()"
    if isinstance(func, ast.Name) and func.id in _DB_FACTORIES:
        return f"{func.id}()"
    return None


def _iso(filename: str, node: ast.expr | ast.stmt, rule_id: str, msg: str) -> Violation:
    assert filename, "Filename must not be empty"
    assert isinstance(node, (ast.expr, ast.stmt)), "Node must be an expr or stmt"
    return Violation(filename, node.lineno, node.col_offset, rule_id, "Isolated", msg)


def _is_environ_subscript_assign(target: ast.expr) -> bool:
    assert target is not None, "Target node must not be None"
    assert isinstance(target, ast.AST), "Target must be an AST node"
    return (
        isinstance(target, ast.Subscript)
        and isinstance(target.value, ast.Attribute)
        and isinstance(target.value.value, ast.Name)
        and target.value.value.id == "os"
        and target.value.attr == "environ"
    )


def _is_mutation_call(node: ast.Call, obj: str, attr: str, methods: set[str]) -> bool:
    assert node is not None, "Call node must not be None"
    assert isinstance(node, ast.Call), "Node must be an ast.Call"
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr in methods
        and isinstance(func.value, ast.Attribute)
        and func.value.attr == attr
        and isinstance(func.value.value, ast.Name)
        and func.value.value.id == obj
    )


class IsolatedRule:
    rule_id: str = "ISO"
    desideratum: str = "Isolated"

    def check(self, tree: ast.AST, filename: str) -> list[Violation]:
        assert tree is not None, "AST tree must not be None"
        assert filename, "Filename must not be empty"
        violations: list[Violation] = []
        for func in test_functions(tree):
            for node in ast.walk(func):
                if isinstance(node, ast.Global):
                    names = ", ".join(node.names)
                    violations.append(
                        Violation(
                            filename,
                            node.lineno,
                            node.col_offset,
                            "ISO001",
                            "Isolated",
                            f"global {names}: global state mutation can cause test ordering dependencies",
                        )
                    )
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if _is_environ_subscript_assign(target):
                            violations.append(
                                Violation(
                                    filename,
                                    node.lineno,
                                    node.col_offset,
                                    "ISO002",
                                    "Isolated",
                                    "os.environ assignment changes process-wide state shared between tests",
                                )
                            )
                elif isinstance(node, ast.Call):
                    violations.extend(self._check_call(node, filename))
        return violations

    def _check_call(self, node: ast.Call, filename: str) -> list[Violation]:
        assert node is not None, "Call node must not be None"
        assert filename, "Filename must not be empty"
        violations = self._check_mutation(node, filename)
        checks: list[tuple[str | None, str, str]] = [
            (
                _file_io_name(node),
                "ISO003",
                "in tests creates file system dependencies that can break in CI",
            ),
            (
                _network_name(node),
                "ISO004",
                "makes a real network request — tests become dependent on external services",
            ),
            (
                _db_name(node),
                "ISO005",
                "creates a real database connection — tests may share state or require infrastructure",
            ),
            (
                _module_call_name(node, _TEMPFILE_MODULES),
                "ISO006",
                "creates a real file system entry — prefer the tmp_path fixture",
            ),
            (
                _module_call_name(node, _SHUTIL_MODULES),
                "ISO007",
                "mutates the file system outside the test's control",
            ),
            (
                _module_call_name(node, _SUBPROCESS_MODULES),
                "ISO008",
                "spawns a real process — tests depend on the host environment",
            ),
        ]
        for name, rule_id, suffix in checks:
            if name:
                violations.append(_iso(filename, node, rule_id, f"{name} {suffix}"))
        return violations

    def _check_mutation(self, node: ast.Call, filename: str) -> list[Violation]:
        assert node is not None, "Call node must not be None"
        assert filename, "Filename must not be empty"
        if _is_mutation_call(node, "sys", "path", {"append", "insert", "remove"}):
            return [
                _iso(
                    filename,
                    node,
                    "ISO002",
                    "sys.path mutation affects import resolution globally",
                )
            ]
        if _is_mutation_call(
            node, "os", "environ", {"update", "pop", "clear", "setdefault"}
        ):
            return [
                _iso(
                    filename,
                    node,
                    "ISO002",
                    "os.environ mutation changes process-wide state shared between tests",
                )
            ]
        return []
