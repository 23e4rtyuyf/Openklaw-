import httpx


async def get_weather(location: str, api_key: str, units: str = "metric") -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get("https://api.openweathermap.org/data/2.5/weather",
                        params={"q": location, "appid": api_key, "units": units})
        if r.status_code != 200:
            return {"error": r.json().get("message", "Unknown error")}
        d = r.json()
        unit_symbol = "°C" if units == "metric" else "°F"
        return {
            "location": d["name"],
            "country": d["sys"]["country"],
            "temperature": f"{d['main']['temp']}{unit_symbol}",
            "feels_like": f"{d['main']['feels_like']}{unit_symbol}",
            "condition": d["weather"][0]["description"],
            "humidity": f"{d['main']['humidity']}%",
            "wind_speed": f"{d['wind']['speed']} {'m/s' if units == 'metric' else 'mph'}",
        }


async def get_forecast(location: str, days: int = 5, api_key: str = "", units: str = "metric") -> list:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get("https://api.openweathermap.org/data/2.5/forecast",
                        params={"q": location, "appid": api_key, "units": units, "cnt": days * 8})
        if r.status_code != 200:
            return [{"error": r.json().get("message")}]
        items = r.json().get("list", [])
        # One entry per day (every 8 entries = 24h)
        daily = items[::8][:days]
        unit_symbol = "°C" if units == "metric" else "°F"
        return [{"date": item["dt_txt"][:10],
                 "temperature": f"{item['main']['temp']}{unit_symbol}",
                 "condition": item["weather"][0]["description"],
                 "humidity": f"{item['main']['humidity']}%"} for item in daily]
