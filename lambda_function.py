import json
import boto3
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def scrape_ssr_page(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--single-process'
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=20000)
            page.wait_for_selector("body", timeout=20000)
            full_html = page.content()
            return {
                "url": url,
                "html": full_html,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                "url": url,
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            browser.close()

def upload_to_s3(data, bucket, key):
    s3 = boto3.client('s3')
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        logger.info(f"Uploaded to s3://{bucket}/{key}")
        return True
    except ClientError as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        return False

def lambda_handler(event, context):
    # get bucket name and default url from environment
    bucket = os.environ.get('S3_BUCKET_NAME')
    default_url = os.environ.get('DEFAULT_URL', 'https://www.aa.com/i18n/travel-info/baggage/checked-baggage-policy.jsp')
    if not bucket:
        raise ValueError("S3_BUCKET_NAME environment variable is required")
    url_to_scrape = event.get('url', default_url)
    result = scrape_ssr_page(url_to_scrape)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    key = f"scraped_data/{timestamp}_{result['status']}.json"
    success = upload_to_s3(result, bucket, key)
    if success:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Scraping completed successfully',
                'url': url_to_scrape,
                'status': result['status'],
                's3_location': f"s3://{bucket}/{key}",
                'timestamp': result['timestamp']
            })
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Scraping completed but S3 upload failed',
                'url': url_to_scrape,
                'status': result['status']
            })
        }
