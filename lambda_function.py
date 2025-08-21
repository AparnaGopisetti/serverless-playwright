import os
import json
import asyncio
import boto3
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Error as PWError

# ---- Config ----
URLS_FILE = "urls.json"
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "2"))  # tune for Lambda memory
NAV_TIMEOUT_MS = int(os.getenv("NAV_TIMEOUT_MS", "60000"))  # 1 min

LAUNCH_ARGS = [
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-setuid-sandbox",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-client-side-phishing-detection",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-domain-reliability",
    "--disable-features=AudioServiceOutOfProcess",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--disable-sync",
    "--metrics-recording-only",
    "--mute-audio",
    "--no-pings",
    "--force-color-profile=srgb",
    "--window-size=1280,1696",
]

async def scroll_to_bottom(page):
    previous_height = await page.evaluate('document.body.scrollHeight')
    while True:
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)
        current_height = await page.evaluate('document.body.scrollHeight')
        if current_height == previous_height:
            break
        previous_height = current_height

def _load_config_from_event_or_file(event):
    urls = []
    bucket_name = None

    if isinstance(event, dict):
        urls = event.get("urls") or urls
        bucket_name = event.get("bucket") or bucket_name

    if not urls or not bucket_name:
        if not os.path.exists(URLS_FILE):
            raise FileNotFoundError(
                f"Config file not found at '{URLS_FILE}', and event did not include 'urls'/'bucket'."
            )
        with open(URLS_FILE, "r") as f:
            data = json.load(f)
        bucket_name = bucket_name or data.get("bucket") or "playwright-scraper-bucket"
        urls = urls or data.get("urls", [])

    if not urls:
        raise ValueError("No URLs provided. Supply 'urls' in event or urls.json.")
    if not bucket_name:
        raise ValueError("No bucket provided. Supply 'bucket' in event or urls.json.")

    return bucket_name, urls

async def _fetch_once(p, url):
    # Launch a new browser per attempt for isolation
    browser = await p.chromium.launch(headless=True, args=LAUNCH_ARGS)
    context = await browser.new_context(
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/114.0.0.0 Safari/537.36"),
        bypass_csp=True,
        java_script_enabled=True,
    )

    # Block heavy resources to reduce crashes/timeouts
    async def block_heavy(route, request):
        if request.resource_type in {"image", "media", "font"}:
            return await route.abort()
        return await route.continue_()
    await context.route("**/*", block_heavy)

    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
        # Best-effort: try to reach network idle, but don't die if it doesn't
        try:
            await page.wait_for_load_state("networkidle", timeout=30_000)
        except Exception:
            pass

        await scroll_to_bottom(page)
        await page.wait_for_timeout(2_000)
        content = await page.content()
        return content
    finally:
        try:
            await context.close()
        finally:
            await browser.close()

async def download_page_content(url):
    # Retry once on TargetClosedError or similar Playwright errors
    async with async_playwright() as p:
        try:
            return await _fetch_once(p, url)
        except PWError as e:
            if "Target page, context or browser has been closed" in str(e):
                print(f"[Retry] TargetClosedError for {url}. Retrying once...")
                return await _fetch_once(p, url)
            raise

def url_to_filename(url: str) -> str:
    path = urlparse(url).path
    base = path.rstrip("/").split("/")[-1] or "index"
    return f"{base}.html"

async def process_one(s3_client, bucket_name, url, sem):
    async with sem:
        result = {"url": url}
        try:
            content = await download_page_content(url)
            key = url_to_filename(url)
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=content.encode("utf-8") if isinstance(content, str) else content,
                ContentType="text/html; charset=utf-8",
            )
            result.update({"s3_key": key, "status": "ok"})
        except Exception as e:
            # Capture error but don't fail the whole batch
            result.update({"status": "error", "error": str(e)})
        return result

async def main(event=None):
    bucket_name, urls = _load_config_from_event_or_file(event or {})
    s3_client = boto3.client("s3")

    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [process_one(s3_client, bucket_name, url, sem) for url in urls]
    results = await asyncio.gather(*tasks)

    # If all failed, raise to surface a failure; otherwise return partial success
    ok_count = sum(1 for r in results if r.get("status") == "ok")
    if ok_count == 0:
        # Raise first error to help debugging
        first_err = next((r.get("error") for r in results if r.get("status") == "error"), "Unknown")
        raise RuntimeError(f"All URLs failed. First error: {first_err}")

    return {
        "statusCode": 207 if ok_count < len(urls) else 200,  # 207 = multi-status
        "message": f"Processed {ok_count}/{len(urls)} successfully",
        "bucket_name": bucket_name,
        "results": results,
    }

def handler(event, context):
    return asyncio.run(main(event))
