"""Severity ordering helpers."""

from spec_eval.models.finding import Severity


GATE_ORDER = {"pass": 0, "warn": 1, "fail": 2, "error": 3}


def max_gate(left: str, right: str) -> str:
    return left if GATE_ORDER.get(left, 0) >= GATE_ORDER.get(right, 0) else right


def default_gate(severity: Severity) -> str:
    if severity >= Severity.MAJOR:
        return "fail"
    if severity == Severity.MINOR:
        return "warn"
    return "pass"

