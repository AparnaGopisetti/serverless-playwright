# lambda_function.py
import asyncio
import boto3
from playwright.async_api import async_playwright

async def scroll_to_bottom(page):
    """Scroll to the bottom of a page to load dynamic content."""
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

async def download_page_content(url):
    """Launch Chromium, navigate to URL, scroll, and get page content."""
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--single-process",
                "--disable-dev-shm-usage",
                "--no-zygote",
                "--disable-setuid-sandbox",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-default-browser-check",
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
                "--force-color-profile=srgb",
                "--metrics-recording-only",
                "--mute-audio",
                "--no-pings",
                "--use-gl=swiftshader",
                "--window-size=1280,1696"
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()

        # Navigate to URL
        print(f"Navigating to URL: {url}")
        try:
            await page.goto(url, timeout=60000)
            try:
                await page.wait_for_load_state('networkidle', timeout=60000)
            except Exception as e:
                print(f"Network idle state timed out: {e}")
            print("Page loaded successfully.")

            # Scroll to bottom
            await scroll_to_bottom(page)
            await page.wait_for_timeout(5000)
            print("Scrolled to the bottom.")

            # Get the page content
            content = await page.content()
        except Exception as e:
            print(f"Failed to load page: {e}")
            raise
        finally:
            await browser.close()
            print("Browser closed.")

        return content

async def main(event):
    """Main async function for Lambda."""
    # Extract parameters from event payload
    url = event.get('url') or "https://www.aa.com/i18n/travel-info/baggage/checked-baggage-policy.jsp"
    bucket_name = event.get('bucket') or "playwright-scraper-bucket"
    output_key = event.get('output_key') or "output.html"
    
    # Download page content
    content = await download_page_content(url)

    # Upload content to S3
    try:
        print("Uploading content to S3...")
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Bucket=bucket_name,
            Key=output_key,
            Body=content,
            ContentType='text/html; charset=utf-8'
        )
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        raise

    print("Source code uploaded successfully")
    return {
        'statusCode': 200,
        'message': 'Source code uploaded successfully',
        'bucket_name': bucket_name,
        'source_code_key': output_key
    }

def handler(event, context):
    """Lambda handler wrapping the async main function."""
    return asyncio.run(main(event))
