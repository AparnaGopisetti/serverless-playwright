import asyncio
import boto3
import json
from urllib.parse import urlparse
from playwright.async_api import async_playwright

URLS_FILE = "urls.json"

async def scroll_to_bottom(page):
    try:
        previous_height = await page.evaluate('document.body.scrollHeight')
        while True:
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(3)
            current_height = await page.evaluate('document.body.scrollHeight')
            if current_height == previous_height:
                break
            previous_height = current_height
    except Exception as e:
        print(f"Error during scrolling: {e}")
        raise

async def download_page_content(browser, url):
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    page = await context.new_page()
    try:
        print(f"Navigating to URL: {url}")
        await page.goto(url, timeout=60000)
        try:
            await page.wait_for_load_state('networkidle', timeout=60000)
        except Exception as e:
            print(f"Network idle state timed out: {e}")
        await scroll_to_bottom(page)
        await page.wait_for_timeout(50000)
        content = await page.content()
        print("Page content obtained.")
        return content
    except Exception as e:
        print(f"Failed to load page: {e}")
        raise
    finally:
        await context.close()

async def main(event=None):
    print("Loading URLs from JSON file...")
    with open(URLS_FILE, 'r') as f:
        data = json.load(f)

    bucket_name = data.get("bucket") or "playwright-scraper-bucket"
    urls = data.get("urls", [])

    s3_client = boto3.client('s3')
    results = []

    async with async_playwright() as p:
        print("Launching Chromium browser...")
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ]
        )

        for url in urls:
            try:
                content = await download_page_content(browser, url)
                path = urlparse(url).path
                filename = (path.rstrip('/').split('/')[-1] or "index") + ".html"
                print(f"Uploading scraped data to S3 bucket '{bucket_name}' as: {filename}")
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=filename,
                    Body=content,
                    ContentType='text/html; charset=utf-8'
                )
                print(f"Uploaded {filename} successfully.")
                results.append({"url": url, "s3_key": filename, "status": "success"})
            except Exception as e:
                print(f"Error processing '{url}': {e}")
                results.append({"url": url, "error": str(e), "status": "failed"})

        await browser.close()

    print("Scraping complete for all URLs.")
    return {
        "statusCode": 200,
        "message": "Scraping completed successfully",
        "bucket_name": bucket_name,
        "results": results,
    }

def handler(event, context):
    return asyncio.run(main(event))
