import argparse
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from channels_config import CHANNELS
from m3u_parser import replace_channel_urls


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class ScrapeResult:
    tvg_id: str
    origin_url: str
    stream_url: Optional[str] = None
    error: Optional[str] = None


def is_m3u8_candidate(url: str) -> bool:
    return ".m3u8" in url.lower()


def score_candidate(url: str, preferred_hosts: tuple[str, ...], expected_hosts: tuple[str, ...]) -> tuple[int, int, int]:
    host = urlparse(url).netloc.lower()
    preferred_score = sum(1 for item in preferred_hosts if item.lower() in host or item.lower() in url.lower())
    expected_score = sum(1 for item in expected_hosts if item.lower() in host or item.lower() in url.lower())
    token_score = 1 if any(token in url.lower() for token in ("token=", "hdnts=", "expires=", "signature=")) else 0
    return preferred_score, expected_score, token_score


def capture_channel_stream(page, channel) -> Optional[str]:
    candidates: List[str] = []

    def collect(url: str) -> None:
        if is_m3u8_candidate(url) and url not in candidates:
            candidates.append(url)

    page.on("request", lambda request: collect(request.url))
    page.on("response", lambda response: collect(response.url))

    page.goto(channel.origin_url, wait_until="domcontentloaded", timeout=channel.navigation_timeout_ms)
    page.wait_for_timeout(channel.wait_after_load_ms)

    if not candidates and hasattr(channel, "embed_urls") and channel.embed_urls:
        for embed_url in channel.embed_urls:
            embed_page = page.context.new_page()
            try:
                embed_page.on("request", lambda request: collect(request.url))
                embed_page.on("response", lambda response: collect(response.url))
                embed_page.goto(embed_url, wait_until="domcontentloaded", timeout=channel.navigation_timeout_ms)
                embed_page.wait_for_timeout(channel.wait_after_load_ms)
                if candidates:
                    break
            finally:
                embed_page.close()

    if not candidates:
        return None

    ranked = sorted(
        candidates,
        key=lambda url: score_candidate(url, channel.preferred_hosts, channel.expected_hosts),
        reverse=True,
    )
    return ranked[0]


def scrape_channels() -> List[ScrapeResult]:
    results: List[ScrapeResult] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        for channel in CHANNELS:
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()
            try:
                stream_url = capture_channel_stream(page, channel)
                if stream_url:
                    results.append(ScrapeResult(tvg_id=channel.tvg_id, origin_url=channel.origin_url, stream_url=stream_url))
                else:
                    results.append(ScrapeResult(tvg_id=channel.tvg_id, origin_url=channel.origin_url, error="No se capturó ninguna URL .m3u8"))
            except PlaywrightTimeoutError:
                results.append(ScrapeResult(tvg_id=channel.tvg_id, origin_url=channel.origin_url, error="Timeout al cargar el origen"))
            except Exception as exc:
                results.append(ScrapeResult(tvg_id=channel.tvg_id, origin_url=channel.origin_url, error=str(exc)))
            finally:
                context.close()

        browser.close()

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Scraper IPTV con Playwright")
    parser.add_argument("--m3u-file", default="prueba.m3u", help="Ruta al archivo M3U a actualizar")
    args = parser.parse_args()

    results = scrape_channels()
    updates: Dict[str, str] = {result.tvg_id: result.stream_url for result in results if result.stream_url}
    changed_channels = replace_channel_urls(args.m3u_file, updates)

    print("--- Resumen ---")
    for result in results:
        if result.stream_url:
            status = "actualizado" if result.tvg_id in changed_channels else "sin cambios"
            print(f"{result.tvg_id}: {status}")
        else:
            print(f"{result.tvg_id}: error -> {result.error}")

    print(f"CAMBIOS_REALIZADOS={'true' if bool(changed_channels) else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())