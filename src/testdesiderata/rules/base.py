import ast


def test_functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    assert tree is not None, "AST tree must not be None"
    assert isinstance(tree, ast.AST), "Tree must be an AST instance"
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    ]
