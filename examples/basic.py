"""Example 1: Basic type and default validation."""
from typekeeper import validate_args

@validate_args()
def greet(name: str, times: int = 1):
    return " ".join([name] * times)

if __name__ == "__main__":
    print(greet("Alice"))
    greet(42)
