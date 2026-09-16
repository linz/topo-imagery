def charcodeat(string: str, index: int) -> int:
    if isinstance(string, str) and isinstance(index, int):
        return ord(string[index])
    raise Exception(f"Error: charcodeat takes a str and an int, received {type(string)} and {type(int)}.")
