from typing import Any


def store(memory: dict, key: str, value: Any) -> str:
    memory[key] = value
    return f"Stored '{key}'"


def retrieve(memory: dict, key: str) -> Any:
    return memory.get(key, None)


def compare_with_last(memory: dict, key: str, value: Any) -> dict:
    last = memory.get(key)
    changed = last != value
    memory[key] = value
    return {
        "changed": changed,
        "previous": last,
        "current": value,
    }
