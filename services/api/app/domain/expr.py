"""Restricted arithmetic evaluator for verified numerical answers.

Whitelist: numbers, + - * / ** ( ) % //, unary +/-, and the names
sqrt exp log sin cos tan pi e plus caller-supplied variables.
No attribute access, no calls except the whitelisted functions, no imports.
Never use `eval`/`exec` on model-generated code — parse to AST and whitelist nodes.
"""

import ast
import math
from collections.abc import Callable

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv)
_ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)

_ALLOWED_FUNCS: dict[str, Callable[..., float]] = {
    "sqrt": math.sqrt,
    "exp": math.exp,
    "log": math.log,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
}

_ALLOWED_CONSTS = {"pi": math.pi, "e": math.e}


class UnsafeExpression(ValueError):
    pass


def _eval(node: ast.AST, variables: dict[str, float]) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body, variables)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise UnsafeExpression(f"constant not allowed: {node.value!r}")
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in variables:
            return float(variables[node.id])
        if node.id in _ALLOWED_CONSTS:
            return _ALLOWED_CONSTS[node.id]
        raise UnsafeExpression(f"unknown name: {node.id}")
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise UnsafeExpression(f"operator not allowed: {type(node.op).__name__}")
        left = _eval(node.left, variables)
        right = _eval(node.right, variables)
        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.Pow):
            return float(left**right)
        if isinstance(op, ast.Mod):
            return left % right
        return left // right
    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, _ALLOWED_UNARYOPS):
            raise UnsafeExpression(f"unary operator not allowed: {type(node.op).__name__}")
        value = _eval(node.operand, variables)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.keywords:
            raise UnsafeExpression("only plain whitelisted calls allowed")
        func = _ALLOWED_FUNCS.get(node.func.id)
        if func is None:
            raise UnsafeExpression(f"function not allowed: {node.func.id}")
        return float(func(*[_eval(a, variables) for a in node.args]))
    raise UnsafeExpression(f"node not allowed: {type(node).__name__}")


def evaluate(expression: str, variables: dict[str, float] | None = None) -> float:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpression(f"syntax error: {exc}") from exc
    return _eval(tree, variables or {})


def within_tolerance(actual: float, expected: float, tolerance_rel: float) -> bool:
    if tolerance_rel < 0:
        raise ValueError("tolerance_rel must be >= 0")
    denom = max(1.0, abs(expected))
    return abs(actual - expected) / denom <= tolerance_rel


def check_solution(
    solution_expression: str,
    variables: dict[str, float],
    expected: float,
    tolerance_rel: float,
) -> bool:
    return within_tolerance(evaluate(solution_expression, variables), expected, tolerance_rel)


def names_in(expression: str) -> set[str]:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpression(f"syntax error: {exc}") from exc
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} - set(
        list(_ALLOWED_FUNCS) + list(_ALLOWED_CONSTS)
    )
