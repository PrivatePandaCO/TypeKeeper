"""Examples 3 and 4: Mutable defaults and custom _validate calls."""
from typekeeper import validate_args

@validate_args(ignore_defaults=False)
def append_item(items: list[int] = []):
    items.append(1)
    return items

class Thing:
    def __init__(self, v: int):
        self.v = v
    def _validate(self) -> bool:
        return self.v >= 0

@validate_args()
def handle(things: list[Thing]):
    return [t.v for t in things]

if __name__ == "__main__":
    append_item()
    handle([Thing(1), Thing(-5), Thing(3)])
