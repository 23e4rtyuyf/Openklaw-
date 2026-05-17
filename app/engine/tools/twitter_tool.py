import httpx


async def twitter_search_tweets(query: str, bearer_token: str, limit: int = 10) -> list:
    url = "https://api.twitter.com/2/tweets/search/recent"
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(url, headers={"Authorization": f"Bearer {bearer_token}"},
                        params={"query": query, "max_results": min(limit, 100),
                                "tweet.fields": "created_at,author_id,public_metrics"})
        data = r.json()
        if "errors" in data:
            return [{"error": data["errors"]}]
        return [{"id": t["id"], "text": t["text"],
                 "created_at": t.get("created_at"),
                 "likes": t.get("public_metrics", {}).get("like_count", 0)}
                for t in data.get("data", [])]


async def twitter_get_mentions(bearer_token: str, limit: int = 10,
                                api_key: str = "", api_secret: str = "",
                                access_token: str = "", access_secret: str = "") -> list:
    url = "https://api.twitter.com/2/tweets/search/recent"
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(url, headers={"Authorization": f"Bearer {bearer_token}"},
                        params={"query": "to:me", "max_results": min(limit, 100),
                                "tweet.fields": "created_at,author_id"})
        data = r.json()
        return data.get("data", [])


async def twitter_post_tweet(text: str, bearer_token: str, api_key: str,
                              api_secret: str, access_token: str, access_secret: str) -> dict:
    import time, hmac, hashlib, urllib.parse, base64, secrets
    url = "https://api.twitter.com/2/tweets"
    nonce = secrets.token_hex(16)
    ts = str(int(time.time()))
    params = {"oauth_consumer_key": api_key, "oauth_nonce": nonce,
               "oauth_signature_method": "HMAC-SHA1", "oauth_timestamp": ts,
               "oauth_token": access_token, "oauth_version": "1.0"}
    base_str = "&".join([
        "POST",
        urllib.parse.quote(url, safe=""),
        urllib.parse.quote("&".join(f"{k}={urllib.parse.quote(str(v), safe='')}"
                                    for k, v in sorted(params.items())), safe=""),
    ])
    signing_key = f"{urllib.parse.quote(api_secret, safe='')}&{urllib.parse.quote(access_secret, safe='')}"
    sig = base64.b64encode(hmac.new(signing_key.encode(), base_str.encode(), hashlib.sha1).digest()).decode()
    params["oauth_signature"] = sig
    auth_header = "OAuth " + ", ".join(f'{k}="{urllib.parse.quote(str(v), safe="")}"'
                                         for k, v in sorted(params.items()))
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(url, headers={"Authorization": auth_header,
                                        "Content-Type": "application/json"},
                         json={"text": text[:280]})
        d = r.json()
        return {"id": d.get("data", {}).get("id"), "text": d.get("data", {}).get("text"),
                "error": d.get("errors")}
