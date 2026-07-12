import os
import httpx
from dotenv import load_dotenv

load_dotenv()

LOCATIONIQ_URL = "https://us1.locationiq.com/v1/search"
LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY")


async def geocode_address(address: str) -> dict | None:
    """
    Gọi LocationIQ (tương thích format Nominatim) để chuyển địa chỉ chữ -> tọa độ.
    Trả về {"lng": ..., "lat": ...} hoặc None nếu không tìm thấy.
    """
    params = {
        "key": LOCATIONIQ_API_KEY,
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "vn",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(LOCATIONIQ_URL, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json()

    if not results:
        return None

    return {
        "lng": float(results[0]["lon"]),
        "lat": float(results[0]["lat"]),
    }


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(geocode_address("Hồ Gươm, Hà Nội"))
    print(result)