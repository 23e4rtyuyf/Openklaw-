import httpx

_URL = "https://api.linear.app/graphql"


def _headers(token: str) -> dict:
    return {"Authorization": token, "Content-Type": "application/json"}


async def _gql(query: str, variables: dict, token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(_URL, headers=_headers(token), json={"query": query, "variables": variables})
        return r.json()


async def linear_list_issues(team_id: str, state: str = "started", token: str = "") -> list:
    q = """
    query($teamId: String!, $state: String) {
      team(id: $teamId) {
        issues(filter: {state: {name: {eq: $state}}}) {
          nodes { id title priority state { name } assignee { name } createdAt }
        }
      }
    }"""
    data = await _gql(q, {"teamId": team_id, "state": state}, token)
    issues = data.get("data", {}).get("team", {}).get("issues", {}).get("nodes", [])
    return [{"id": i["id"], "title": i["title"], "priority": i["priority"],
             "state": i.get("state", {}).get("name"), "assignee": (i.get("assignee") or {}).get("name")}
            for i in issues]


async def linear_get_issue(issue_id: str, token: str) -> dict:
    q = """query($id: String!) { issue(id: $id) { id title description state { name } assignee { name } priority } }"""
    data = await _gql(q, {"id": issue_id}, token)
    i = data.get("data", {}).get("issue", {})
    return {"id": i.get("id"), "title": i.get("title"), "description": i.get("description"),
            "state": (i.get("state") or {}).get("name"), "priority": i.get("priority")}


async def linear_create_issue(team_id: str, title: str, description: str = "",
                               priority: int = 0, token: str = "") -> dict:
    q = """mutation($input: IssueCreateInput!) { issueCreate(input: $input) { issue { id title url } } }"""
    data = await _gql(q, {"input": {"teamId": team_id, "title": title,
                                     "description": description, "priority": priority}}, token)
    issue = data.get("data", {}).get("issueCreate", {}).get("issue", {})
    return {"id": issue.get("id"), "title": issue.get("title"), "url": issue.get("url")}


async def linear_update_issue(issue_id: str, updates: dict, token: str) -> dict:
    q = """mutation($id: String!, $input: IssueUpdateInput!) { issueUpdate(id: $id, input: $input) { issue { id title } } }"""
    data = await _gql(q, {"id": issue_id, "input": updates}, token)
    issue = data.get("data", {}).get("issueUpdate", {}).get("issue", {})
    return {"id": issue.get("id"), "title": issue.get("title")}
