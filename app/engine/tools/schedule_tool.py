from typing import Optional


def get_last_result(runs: list) -> Optional[str]:
    completed = [r for r in runs if r.get("status") in ("success", "failed")]
    if not completed:
        return None
    return completed[-1].get("result")
