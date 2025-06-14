"""Examples 2b and 2c: Nested path constraints and overriding wildcards."""
from typekeeper import validate_args

@validate_args(lengths="users:tables:headers=100")
def check(users: list[dict]):
    return users

@validate_args(lengths="var::=2; var::a=1")
def merge(var: dict[str, dict[str, int]]):
    return var

if __name__ == "__main__":
    check([{"tables": [{"headers": 100}]}])
    check([{"tables": [{"headers": 5}]}])
    merge({"x": {"a": 1}, "y": {"b": 2}})
    merge({"x": {"a": 2}, "y": {"b": 2}})
