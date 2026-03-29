from typing import Any
import asyncio
from playwright.async_api import async_playwright

async def fetch_with_playwright(url: str) -> str:
    """Local Playwright fallback for hotel scraping"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        if page.url.startswith("https://consent.google.com"):
            await page.click('text="Accept all"')
            await page.wait_for_load_state("networkidle")
        # Wait for at least one hotel card to appear
        await page.locator('div.uaTTDe').first.wait_for(timeout=15000)
        body = await page.content()
        await browser.close()
    return body

def local_playwright_fetch(params: dict, location: str = "") -> Any:
    """Local Playwright fallback function"""
    from .utils import get_city_from_iata
    city = get_city_from_iata(location) if location else ""
    location_url = city.strip().replace(' ', '+').lower() if city else ""
    base = f"https://www.google.com/travel/hotels/{location_url}" if location_url else "https://www.google.com/travel/hotels"
    url = base + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    body = asyncio.run(fetch_with_playwright(url))

    class DummyResponse:
        status_code = 200
        text = body
        text_markdown = body

    return DummyResponse 