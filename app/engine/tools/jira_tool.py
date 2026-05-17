import httpx
import base64


def _headers(email: str, api_token: str) -> dict:
    creds = base64.b64encode(f"{email}:{api_token}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json",
            "Accept": "application/json"}


async def jira_list_issues(jql: str, base_url: str, email: str, api_token: str) -> list:
    url = f"{base_url.rstrip('/')}/rest/api/3/search"
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(url, headers=_headers(email, api_token),
                        params={"jql": jql, "maxResults": 30,
                                "fields": "summary,status,assignee,priority,created"})
        issues = r.json().get("issues", [])
        return [{"key": i["key"], "summary": i["fields"]["summary"],
                 "status": i["fields"]["status"]["name"],
                 "assignee": (i["fields"].get("assignee") or {}).get("displayName"),
                 "priority": (i["fields"].get("priority") or {}).get("name")} for i in issues]


async def jira_create_issue(project_key: str, summary: str, description: str,
                             issue_type: str, base_url: str, email: str, api_token: str) -> dict:
    url = f"{base_url.rstrip('/')}/rest/api/3/issue"
    body = {"fields": {"project": {"key": project_key}, "summary": summary,
                        "issuetype": {"name": issue_type},
                        "description": {"type": "doc", "version": 1,
                                        "content": [{"type": "paragraph", "content":
                                                     [{"type": "text", "text": description}]}]}}}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(url, headers=_headers(email, api_token), json=body)
        d = r.json()
        return {"key": d.get("key"), "id": d.get("id"),
                "url": f"{base_url}/browse/{d.get('key')}"}


async def jira_update_issue(issue_key: str, fields: dict, base_url: str,
                             email: str, api_token: str) -> str:
    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}"
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.put(url, headers=_headers(email, api_token), json={"fields": fields})
        return "Updated" if r.status_code == 204 else f"Error: {r.text}"


async def jira_add_comment(issue_key: str, comment: str, base_url: str,
                            email: str, api_token: str) -> dict:
    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}/comment"
    body = {"body": {"type": "doc", "version": 1,
                      "content": [{"type": "paragraph",
                                   "content": [{"type": "text", "text": comment}]}]}}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(url, headers=_headers(email, api_token), json=body)
        d = r.json()
        return {"id": d.get("id")}


async def jira_transition_issue(issue_key: str, transition_name: str, base_url: str,
                                 email: str, api_token: str) -> str:
    trans_url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}/transitions"
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(trans_url, headers=_headers(email, api_token))
        transitions = r.json().get("transitions", [])
        match = next((t for t in transitions if transition_name.lower() in t["name"].lower()), None)
        if not match:
            return f"Transition '{transition_name}' not found. Available: {[t['name'] for t in transitions]}"
        await c.post(trans_url, headers=_headers(email, api_token),
                     json={"transition": {"id": match["id"]}})
        return f"Issue {issue_key} transitioned to {match['name']}"
