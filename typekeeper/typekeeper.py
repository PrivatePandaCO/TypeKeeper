"""
Argument Checker Library
Provides a decorator to validate function parameters against type annotations,
default values, and numeric or length specifications.
"""

import inspect
import re
import warnings
from collections.abc import Iterable
from contextlib import contextmanager
from functools import lru_cache, wraps
from typing import Annotated, Any, Callable, Union, get_args, get_origin, Tuple, Dict, Generator

# Global flag to enable/disable all checks
RUN_CHECKS: bool = True


def set_arg_checks(enabled: bool) -> None:
    """
    Globally enable or disable argument checking for decorated functions.

    :param enabled: True to enable checks, False to disable.
    """
    global RUN_CHECKS
    RUN_CHECKS = enabled


@contextmanager
def suspend_arg_checks() -> Generator[None, Any, None]:
    """
    Temporarily disable argument checking within a with-block.

    Usage:
        with suspended_arg_checks():
            # checks are disabled here
            foo(...)
        # checks are restored here
    """
    global RUN_CHECKS
    original = RUN_CHECKS
    RUN_CHECKS = False
    try:
        yield
    finally:
        RUN_CHECKS = original


def _emit_warning(message: str, filename: str, lineno: int) -> None:
    """
    Emit a standardized warning at a given file and line number.

    :param message: Warning message content.
    :param filename: File path to attribute the warning to.
    :param lineno: Line number in the file for the warning.
    """
    warnings.warn_explicit(message, UserWarning, filename, lineno)


@lru_cache(maxsize=None)
def _get_source_lines(func):
    """
    Retrieve the source code lines and starting line number for a function.

    :param func: Function object to inspect.
    :return: Tuple of (list of source lines, starting line number).
    """
    return inspect.getsourcelines(func)


def _parse_specs(lengths: str) -> dict[str, list[tuple[float, float]]]:
    """
    Convert a spec string into a mapping of parameter names to numeric ranges.

    :param lengths: Specification string, e.g. "x=1,3-5; y=0-2".
    :return: Dict mapping each parameter to a list of (min, max) tuples.
    """
    spec_map: dict[str, list[tuple[float, float]]] = {}
    if not lengths:
        return spec_map
    for token in lengths.split(";"):
        token = token.strip()
        if not token or "=" not in token:
            warnings.warn(f"Invalid spec format '{token}'", UserWarning)
            continue
        name, spec_text = map(str.strip, token.split("=", 1))
        for tok in spec_text.split(","):
            tok = tok.strip()
            if not tok:
                continue
            m_range = re.fullmatch(r"(-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?)", tok)
            m_single = re.fullmatch(r"(-?\d+(?:\.\d+)?)", tok)
            if m_range:
                lo, hi = float(m_range.group(1)), float(m_range.group(2))
                if lo > hi:
                    warnings.warn(
                        f"Invalid range for '{name}': {lo} > {hi}", UserWarning
                    )
                    continue
                spec_map.setdefault(name, []).append((lo, hi))
            elif m_single:
                n = float(m_single.group(1))
                spec_map.setdefault(name, []).append((n, n))
            else:
                warnings.warn(
                    f"Invalid spec token '{tok}' for parameter '{name}'", UserWarning
                )
    return spec_map


def is_immutable(obj) -> bool:
    """
    Determine if an object is deeply immutable.

    :param obj: Any object to check.
    :return: True if object is immutable, False otherwise.
    """
    im_types = (type(None), bool, int, float, complex, str, bytes, range)
    if isinstance(obj, im_types):
        return True
    if isinstance(obj, tuple):
        return all(is_immutable(item) for item in obj)
    if isinstance(obj, frozenset):
        return all(is_immutable(item) for item in obj)
    return False


def _check_type(value, annotation) -> bool:
    """
    Recursively check if a value conforms to a typing annotation.
    Supports Union, Annotated, built-in generics, and Callable.

    :param value: Any value to check.
    :param annotation: Expected Type.
    :return: True if value conforms to a typing annotation, False otherwise.
    """
    if annotation is Any:
        return True
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Union:
        return any(_check_type(value, arg) for arg in args)
    if origin is Annotated:
        return _check_type(value, args[0])
    if origin is list:
        if not isinstance(value, list):
            return False
        return (not args) or all(_check_type(v, args[0]) for v in value)
    if origin is tuple:
        if not isinstance(value, tuple):
            return False
        if not args:
            return True
        if len(args) == 2 and args[1] is Ellipsis:
            return all(_check_type(v, args[0]) for v in value)
        if len(args) == len(value):
            return all(_check_type(v, a) for v, a in zip(value, args))
        return False
    if origin is dict:
        if not isinstance(value, dict):
            return False
        if args:
            kt, vt = args
            return all(
                _check_type(k, kt) and _check_type(v, vt) for k, v in value.items()
            )
        return True
    if origin in (set, frozenset):
        if origin is set and not isinstance(value, set):
            return False
        if origin is frozenset and not isinstance(value, frozenset):
            return False
        return (not args) or all(_check_type(v, args[0]) for v in value)
    if origin is Iterable:
        try:
            it = iter(value)
        except TypeError:
            return False
        return (not args) or all(_check_type(v, args[0]) for v in it)
    if origin is Callable:
        return callable(value)
    if inspect.isclass(annotation):
        return isinstance(value, annotation)
    return False


def _recursive_validate(obj, path=None) -> list[tuple[list, object]]:
    """
    Recursively validate an object and its nested elements.

    :param obj: The object to validate
    :param path: Current traversal path (for internal recursion).
    :returns: List of `(path, bad_value)` tuples for each validation failure.
    """
    path = [] if path is None else path.copy()
    failures: list[tuple[list, object]] = []

    # 1) run the object’s own _validate()
    validator = getattr(obj, "_validate", None)
    if callable(validator):
        try:
            ok = validator()
        except Exception:
            ok = False
        if not ok:
            failures.append((path, obj))

    # 2) recurse into mappings
    if isinstance(obj, dict):
        for key, val in obj.items():
            failures.extend(_recursive_validate(key, path + [f"[{key!r}]"]))
            failures.extend(_recursive_validate(val, path + [f"[{key!r}]"]))
    # 3) recurse into sequences/iterables
    elif isinstance(obj, Iterable) and not isinstance(obj, (str, bytes, bytearray)):
        for idx, item in enumerate(obj):
            failures.extend(_recursive_validate(item, path + [f"[{idx}]"]))

    return failures


def validate_args(_func=None, lengths: str = None, *, ignore_defaults: bool = False):
    """
    Decorator to validate function parameters against type hints,
    default values, and numeric or length specifications.

    :param _func: Function object to inspect.
    :param lengths: Specification string for ranges, e.g. "x=1-5; y=3".
    :param ignore_defaults: If True, skip mutable default argument warnings.
    :return: Decorated function with validation logic applied on call.
    """
    if not RUN_CHECKS:
        return _func if _func is not None else (lambda f: f)

    spec_map = _parse_specs(lengths)

    def decorator(func):
        sig = inspect.signature(func)
        params = []
        for name, param in sig.parameters.items():
            if param.kind is inspect.Parameter.VAR_POSITIONAL:
                ann = param.annotation
                # if user wrote *args: T, wrap to Tuple[T, ...]
                if isinstance(ann, type):
                    param = param.replace(annotation=Tuple[ann, ...])
            elif param.kind is inspect.Parameter.VAR_KEYWORD:
                ann = param.annotation
                # if user wrote **kwargs: T, wrap to Dict[str, T]
                if isinstance(ann, type):
                    param = param.replace(annotation=Dict[str, ann])
            params.append(param)
        sig = sig.replace(parameters=params)

        # Use cached source lookup
        src_lines, start = _get_source_lines(func)
        def_filename = func.__code__.co_filename
        decorator_lineno = None
        def_lineno = func.__code__.co_firstlineno

        # locate decorator and def lines
        for idx, line in enumerate(src_lines):
            stripped = line.lstrip()
            if stripped.startswith("@validate_args") and decorator_lineno is None:
                decorator_lineno = start + idx
            if stripped.startswith("def "):
                def_lineno = start + idx
                break

        # Decoration-time checks
        for pname, param in sig.parameters.items():
            default = param.default
            ann = param.annotation
            if (
                not ignore_defaults
                and default is not inspect._empty
                and not is_immutable(default)
            ):
                _emit_warning(
                    f"Mutable default for '{pname}' in '{func}': {default!r}",
                    def_filename,
                    decorator_lineno or def_lineno,
                )
            if (
                default is not inspect._empty
                and ann is not inspect._empty
                and not _check_type(default, ann)
            ):
                _emit_warning(
                    f"Default for '{pname}' in '{func}' does not match annotation {ann!r}; expected {ann!r}, got {type(default)!r}",
                    def_filename,
                    decorator_lineno or def_lineno,
                )

        @wraps(func)
        def wrapper(*args, **kwargs):
            frame = inspect.currentframe().f_back
            call_filename = frame.f_code.co_filename
            call_lineno = frame.f_lineno

            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()

            for pname, val in bound.arguments.items():
                bads = _recursive_validate(val)
                for path, bad in bads:
                    loc = "".join(path) or "[self]"
                    _emit_warning(
                        f"Recursed value of parameter '{pname}' at depth {loc} failed _validate in '{func}' (defined at {def_filename}:{def_lineno})",
                        call_filename,
                        call_lineno,
                    )

            # Call-time checks: numeric ranges & lengths
            for pname, ranges in spec_map.items():
                if pname not in bound.arguments:
                    continue
                val = bound.arguments[pname]
                if isinstance(val, (int, float)):
                    if not any(lo <= val <= hi for lo, hi in ranges):
                        _emit_warning(
                            f"Param '{pname}'={val} not in ranges {ranges} (defined at {def_filename}:{def_lineno})",
                            call_filename,
                            call_lineno,
                        )
                else:
                    try:
                        length = len(val)
                    except Exception:
                        _emit_warning(
                            f"Cannot determine length of '{pname}' for spec {ranges} (defined at {def_filename}:{def_lineno})",
                            call_filename,
                            call_lineno,
                        )
                        continue
                    if not any(lo <= length <= hi for lo, hi in ranges):
                        _emit_warning(
                            f"Length of '{pname}'={length} not in ranges {ranges} (defined at {def_filename}:{def_lineno})",
                            call_filename,
                            call_lineno,
                        )

            # Call-time checks: types
            for name, val in bound.arguments.items():
                annt = sig.parameters[name].annotation
                if annt is not inspect._empty and not _check_type(val, annt):
                    _emit_warning(
                        f"Arg '{name}' to '{func}' mismatches {annt!r}; expected {annt!r}, got {type(bound.arguments[name])!r} (defined at {def_filename}:{def_lineno})",
                        call_filename,
                        call_lineno,
                    )

            return func(*bound.args, **bound.kwargs)

        return wrapper

    return (lambda f: decorator if f is None else decorator(f))(_func)
