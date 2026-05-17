import math


def _nums(data: list[dict], column: str) -> list[float]:
    result = []
    for row in data:
        v = row.get(column)
        if v is not None and v != "":
            try:
                result.append(float(v))
            except (ValueError, TypeError):
                pass
    return result


async def summarize_data(data: list, columns: list = None) -> dict:
    try:
        if not data:
            return {}
        cols = columns or list(data[0].keys())
        out = {}
        for col in cols:
            all_vals = [row.get(col) for row in data]
            non_null = [v for v in all_vals if v is not None and v != ""]
            nums = _nums(data, col)
            if nums:
                mean = sum(nums) / len(nums)
                variance = sum((x - mean) ** 2 for x in nums) / len(nums)
                sorted_nums = sorted(nums)
                n = len(sorted_nums)
                median = (sorted_nums[n // 2] if n % 2 else (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2)
                out[col] = {
                    "type": "numeric", "count": len(non_null), "nulls": len(all_vals) - len(non_null),
                    "min": min(nums), "max": max(nums),
                    "mean": round(mean, 4), "median": round(median, 4),
                    "std_dev": round(math.sqrt(variance), 4),
                }
            else:
                unique = list(set(str(v) for v in non_null))
                out[col] = {
                    "type": "text", "count": len(non_null), "nulls": len(all_vals) - len(non_null),
                    "unique": len(unique), "sample": unique[:5],
                }
        return out
    except Exception as e:
        return {"error": str(e)}


async def detect_anomalies(data: list, column: str, threshold: float = 2.5) -> list:
    try:
        nums = _nums(data, column)
        if len(nums) < 3:
            return []
        mean = sum(nums) / len(nums)
        std = math.sqrt(sum((x - mean) ** 2 for x in nums) / len(nums))
        if std == 0:
            return []
        anomalies = []
        for i, row in enumerate(data):
            v = row.get(column)
            if v is None or v == "":
                continue
            try:
                n = float(v)
                z = abs(n - mean) / std
                if z > threshold:
                    anomalies.append({"row": i, "value": n, "z_score": round(z, 3), **row})
            except (ValueError, TypeError):
                pass
        return anomalies
    except Exception as e:
        return [{"error": str(e)}]


async def pivot_table(data: list, index: str, columns: str, values: str,
                      aggfunc: str = "sum") -> list:
    try:
        col_values = sorted(set(str(row.get(columns, "")) for row in data))
        groups: dict = {}
        for row in data:
            idx = str(row.get(index, ""))
            col = str(row.get(columns, ""))
            try:
                val = float(row.get(values, 0) or 0)
            except (ValueError, TypeError):
                val = 0.0
            groups.setdefault(idx, {}).setdefault(col, []).append(val)

        result = []
        for idx, col_data in sorted(groups.items()):
            r: dict = {index: idx}
            for cv in col_values:
                vals = col_data.get(cv, [])
                if not vals:
                    r[cv] = None
                elif aggfunc == "sum":
                    r[cv] = round(sum(vals), 4)
                elif aggfunc == "mean":
                    r[cv] = round(sum(vals) / len(vals), 4)
                elif aggfunc == "count":
                    r[cv] = len(vals)
                elif aggfunc == "min":
                    r[cv] = min(vals)
                elif aggfunc == "max":
                    r[cv] = max(vals)
                else:
                    r[cv] = round(sum(vals), 4)
            result.append(r)
        return result
    except Exception as e:
        return [{"error": str(e)}]
