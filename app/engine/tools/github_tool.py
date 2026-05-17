import httpx

_BASE = "https://api.github.com"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}


async def github_get_repo(owner: str, repo: str, token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{_BASE}/repos/{owner}/{repo}", headers=_headers(token))
        d = r.json()
        return {"name": d.get("full_name"), "description": d.get("description"),
                "stars": d.get("stargazers_count"), "open_issues": d.get("open_issues_count"),
                "default_branch": d.get("default_branch"), "url": d.get("html_url")}


async def github_list_issues(owner: str, repo: str, token: str, state: str = "open") -> list:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{_BASE}/repos/{owner}/{repo}/issues",
                        headers=_headers(token), params={"state": state, "per_page": 30})
        return [{"number": i["number"], "title": i["title"], "state": i["state"],
                 "user": i["user"]["login"], "created_at": i["created_at"],
                 "url": i["html_url"]} for i in r.json() if "pull_request" not in i]


async def github_create_issue(owner: str, repo: str, title: str, body: str, token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{_BASE}/repos/{owner}/{repo}/issues",
                         headers=_headers(token), json={"title": title, "body": body})
        d = r.json()
        return {"number": d.get("number"), "url": d.get("html_url")}


async def github_comment_issue(owner: str, repo: str, issue_number: int, body: str, token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{_BASE}/repos/{owner}/{repo}/issues/{issue_number}/comments",
                         headers=_headers(token), json={"body": body})
        d = r.json()
        return {"id": d.get("id"), "url": d.get("html_url")}


async def github_get_commits(owner: str, repo: str, token: str, limit: int = 10) -> list:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{_BASE}/repos/{owner}/{repo}/commits",
                        headers=_headers(token), params={"per_page": limit})
        return [{"sha": c_["sha"][:7], "message": c_["commit"]["message"].split("\n")[0],
                 "author": c_["commit"]["author"]["name"], "date": c_["commit"]["author"]["date"]}
                for c_ in r.json()]


async def github_list_prs(owner: str, repo: str, token: str, state: str = "open") -> list:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{_BASE}/repos/{owner}/{repo}/pulls",
                        headers=_headers(token), params={"state": state, "per_page": 30})
        return [{"number": p["number"], "title": p["title"], "state": p["state"],
                 "user": p["user"]["login"], "url": p["html_url"]} for p in r.json()]


async def github_get_pr(owner: str, repo: str, pr_number: int, token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{_BASE}/repos/{owner}/{repo}/pulls/{pr_number}", headers=_headers(token))
        d = r.json()
        return {"number": d.get("number"), "title": d.get("title"), "state": d.get("state"),
                "merged": d.get("merged"), "url": d.get("html_url"),
                "head": d.get("head", {}).get("ref"), "base": d.get("base", {}).get("ref")}


async def github_get_pr_status(owner: str, repo: str, pr_number: int, token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        pr = await c.get(f"{_BASE}/repos/{owner}/{repo}/pulls/{pr_number}", headers=_headers(token))
        sha = pr.json().get("head", {}).get("sha", "")
        r = await c.get(f"{_BASE}/repos/{owner}/{repo}/commits/{sha}/check-runs", headers=_headers(token))
        checks = r.json().get("check_runs", [])
        return {"sha": sha[:7], "checks": [{"name": ch["name"], "status": ch["status"],
                "conclusion": ch["conclusion"]} for ch in checks]}
