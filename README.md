# typekeeper

## Overview
typekeeper is a lightweight Python library that injects comprehensive runtime validation into your functions with a single decorator. It automatically:

- Verifies that arguments conform to their type annotations (including nested generics).  
- Warns when default values don’t match annotations or use mutable defaults.  
- Enforces numeric ranges and sequence-length constraints via an easy spec string.  
- Captures both the function definition and call site in all warnings for precise diagnostics.

Simply decorate your function with `@validate_args(...)` to gain these safeguards during development, without changing your function signature.

## Features
- **Type validation**: Recursively checks simple and generic types (`List[int]`, `Dict[str, float]`, `Optional[...]`, `Union[...]`, `Callable`, etc.).  
- **Default‐value checks**: Detects mismatches between annotated types and default values, plus the classic mutable‐default gotcha.  
- **Range & length specs**: Specify numeric or length constraints in one string (e.g. `"x=1-5; tags=2-4"`).
- **Context‐aware warnings**: All warnings include file paths and line numbers of both the decorator and the call site.  
- **Global control**: Enable or disable checks at runtime with `set_arg_checks()` or temporarily within `suspended_arg_checks()`.
- **Recursive _validate() Invocation**: Recursively calls _validate() on variable if defined. Gives metadata of location of object in recursion path which fails _validate().


## Installation
```bash
pip install typekeeper
```

## Configuration
### Global Toggle
Argument checks are controlled by an internal flag; direct access is not required.  Use the provided APIs:
- `set_arg_checks(enabled: bool)`: Turn all checks on or off globally.  
- `suspended_arg_checks()`: Context manager to disable checks within a `with` block.

## API Reference

### `validate_args`
```python
def validate_args(*, lengths: Optional[str] = None, ignore_defaults: bool = False) -> Callable
```
- **lengths**: Optional specification string for constraining numeric values or sequence lengths. It uses a semicolon-separated list of parameter specifications in the form:
  ```text
  name=token1,token2,...
  ```
  where each `token` is either:
  - A single number `N`, enforcing an exact value (for numeric arguments) or exact length (for sequences).
  - A range `min-max`, enforcing inclusive bounds (both endpoints inclusive).
  For example:
  ```python
  lengths="x=1,3-5; y=2"
  ```
  enforces:
  - `x` must be either exactly `1` or between `3` and `5`.
  - `y` must be exactly `2`.  
  If omitted, no range or length constraints are applied.  
- **ignore_defaults**: Skip warnings for mutable default arguments if set to `True`.

### `set_arg_checks`
```python
def set_arg_checks(enabled: bool) -> None
```
Globally enable or disable all argument validation.

### `suspended_arg_checks`
```python
@contextmanager
def suspended_arg_checks() -> None
```
Temporarily suspend argument checks within a `with` block.


## Examples
```python
# Example 1: Basic type‐and‐default validation
from typekeeper import validate_args

@validate_args()
def greet(name: str, times: int = 1):
    return " ".join([name] * times)

# Valid call:
greet("Alice")         # → "Alice"
# Invalid call (wrong type):
greet(42)              
#  UserWarning: Arg 'name' mismatches <class 'str'>; expected <class 'str'>, got <class 'int'>
```
```python
# Example 2: Numeric‐range and length‐range constraints
from typekeeper import validate_args

@validate_args(lengths="x=1-3; data=2-4")
def process(x: int, data: list[int]):
    return data * x

# Valid:
process(2, [10, 20, 30])   
# Invalid x:
process(0, [1, 2])         
#  UserWarning: Param 'x'=0 not in ranges [(1.0, 3.0)]
# Invalid data length:
process(2, [1])            
#  UserWarning: Length of 'data'=1 not in ranges [(2.0, 4.0)]
```
```python
# Example 3: Mutable‐default detection
from typekeeper import validate_args

@validate_args(ignore_defaults=False)
def append_item(items: list[int] = []):
    items.append(1)
    return items

# Decoration‐time warning:
#  UserWarning: Mutable default for 'items' in '<function append_item>' : []
```
```python
# Example 4: Custom _validate() on nested items
from typekeeper import validate_args

class Thing:
    def __init__(self, v: int):
        self.v = v
    def _validate(self) -> bool:
        return self.v >= 0

@validate_args()
def handle(things: list[Thing]):
    return [t.v for t in things]

# Call with one bad element:
handle([Thing(1), Thing(-5), Thing(3)])
#  UserWarning: Parameter 'things' failed at [1] in 'handle'; offending value: Thing(v=-5)
```


## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.  
2. Create a feature branch.  
3. Submit a pull request.

## License
MIT License

## Author
**Parth Mittal**  
Email: parth@privatepanda.co
