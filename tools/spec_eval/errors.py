"""Domain-specific errors raised by the evaluator infrastructure."""


class SpecEvalError(Exception):
    """Base error for evaluator failures."""


class ConfigurationError(SpecEvalError):
    """Raised when required evaluator configuration is invalid."""


class FunctionNotFoundError(SpecEvalError):
    """Raised when a FuncID or function path cannot be resolved."""


class ParseError(SpecEvalError):
    """Raised when a document cannot be parsed safely."""

