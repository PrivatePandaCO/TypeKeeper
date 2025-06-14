"""Example 2: Numeric-range and length-range constraints."""
from typekeeper import validate_args

@validate_args(lengths="x=1-3; data=2-4")
def process(x: int, data: list[int]):
    return data * x

if __name__ == "__main__":
    print(process(2, [10, 20, 30]))
    process(0, [1, 2])
    process(2, [1])
