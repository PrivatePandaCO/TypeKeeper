## [0.0.3b1] – 2025-06-14
### Added
- Support colon-delimited path specs with `:` and `\` escapes.
- Wildcard `*` segments and trailing colon shorthand.
- Later path specs override earlier ones; duplicate primitives handled correctly.
- Recursively calls `_validate()` on nested objects.
- Fixed "int" not being matched to <class 'int'> while using future annotations
- Global `set_stop_on_error()` toggle to raise a `ValueError` on the first validation failure.

### Removed
- Attribute-based traversal in spec paths. Only keys and indexes are followed.

## [0.0.2] – 2025-04-29
### Features
- Add support for `*args` and `**kwargs` type hints while keeping standard IDE checkers happy.

### Refactoring
- Update type hint for `suspended_arg_checks()` to match new annotation behavior.

### Documentation
- Simplify `_recursive_validate` docstring to concise Sphinx‐style format.
