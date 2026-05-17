import csv
import os


def _read_rows(file_path: str, delimiter: str = ",", encoding: str = "utf-8-sig") -> tuple[list[str], list[dict]]:
    with open(file_path, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)
        headers = list(reader.fieldnames or [])
    return headers, rows


async def read_csv(file_path: str, delimiter: str = ",", encoding: str = "utf-8-sig",
                   max_rows: int = 10000) -> list:
    try:
        _, rows = _read_rows(file_path, delimiter, encoding)
        return rows[:max_rows]
    except Exception as e:
        return [{"error": str(e)}]


async def write_csv(file_path: str, data: list, headers: list = None) -> dict:
    try:
        if not data:
            return {"rows_written": 0}
        fieldnames = headers or list(data[0].keys())
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        return {"rows_written": len(data), "file": file_path}
    except Exception as e:
        return {"error": str(e)}


async def filter_csv(file_path: str, column: str, value: str, operator: str = "eq") -> list:
    try:
        _, rows = _read_rows(file_path)
        ops = {
            "eq": lambda a, b: a == b,
            "ne": lambda a, b: a != b,
            "contains": lambda a, b: b.lower() in a.lower(),
            "gt": lambda a, b: float(a) > float(b),
            "lt": lambda a, b: float(a) < float(b),
            "gte": lambda a, b: float(a) >= float(b),
            "lte": lambda a, b: float(a) <= float(b),
        }
        fn = ops.get(operator, ops["eq"])
        return [r for r in rows if column in r and fn(r[column], value)]
    except Exception as e:
        return [{"error": str(e)}]


async def sort_csv(file_path: str, column: str, ascending: bool = True) -> list:
    try:
        _, rows = _read_rows(file_path)
        def _key(r):
            v = r.get(column, "")
            try:
                return (0, float(v))
            except ValueError:
                return (1, v.lower())
        return sorted(rows, key=_key, reverse=not ascending)
    except Exception as e:
        return [{"error": str(e)}]


async def aggregate_csv(file_path: str, group_by: str, agg_column: str,
                        func: str = "sum") -> list:
    try:
        _, rows = _read_rows(file_path)
        groups: dict[str, list[float]] = {}
        for r in rows:
            key = r.get(group_by, "")
            try:
                val = float(r.get(agg_column, 0))
            except ValueError:
                val = 0.0
            groups.setdefault(key, []).append(val)

        result = []
        for key, vals in groups.items():
            if func == "sum":
                agg = sum(vals)
            elif func == "mean":
                agg = sum(vals) / len(vals)
            elif func == "count":
                agg = len(vals)
            elif func == "min":
                agg = min(vals)
            elif func == "max":
                agg = max(vals)
            else:
                agg = sum(vals)
            result.append({group_by: key, f"{func}_{agg_column}": round(agg, 4)})
        return sorted(result, key=lambda x: -list(x.values())[1])
    except Exception as e:
        return [{"error": str(e)}]


async def join_csv(file1: str, file2: str, on_column: str) -> list:
    try:
        _, rows1 = _read_rows(file1)
        _, rows2 = _read_rows(file2)
        lookup = {r[on_column]: r for r in rows2 if on_column in r}
        result = []
        for r in rows1:
            key = r.get(on_column)
            merged = {**r, **{f"b_{k}": v for k, v in (lookup.get(key) or {}).items() if k != on_column}}
            result.append(merged)
        return result
    except Exception as e:
        return [{"error": str(e)}]
