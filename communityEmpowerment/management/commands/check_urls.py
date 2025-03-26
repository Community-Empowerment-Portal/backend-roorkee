import os
import json
import logging
import asyncio
import httpx
from django.core.management.base import BaseCommand

TIMEOUT = 10
MAX_CONCURRENT_REQUESTS = 5  # Limit concurrent requests
FAILED_LOG_FILE = os.path.join(os.path.dirname(__file__), "failed_urls.log")
DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "scrapedData")

# Ensure log directory exists
os.makedirs(os.path.dirname(FAILED_LOG_FILE), exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(FAILED_LOG_FILE, mode="a", encoding="utf-8"),  # Append mode
        logging.StreamHandler()
    ],
     force=True 
)

unique_urls = set()  # Track unique URLs
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)  # Rate limiter


async def check_url(url):
    """Check if a URL is accessible and log failures."""
    if not url or not isinstance(url, str):
        return False

    if url in unique_urls:
        return False  # Skip duplicate checks

    unique_urls.add(url)

    async with semaphore:  # Enforce rate limit
        async with httpx.AsyncClient(verify=False, headers={"User-Agent": "Mozilla/5.0"}) as client:
            try:
                response = await client.head(url, timeout=TIMEOUT)
                if response.status_code not in (200, 301, 302):  # Log only failures
                    logging.error("❌ FAILED: %s (Status: %d)", url, response.status_code)
                    return False
                return True

            except httpx.HTTPStatusError as e:
                logging.error("❌ HTTP ERROR: %s (Status: %d)", url, e.response.status_code)
                return False
            except httpx.ConnectError:
                logging.error("❌ CONNECTION ERROR: %s", url)
                return False
            except httpx.TimeoutException:
                logging.error("⏳ TIMEOUT: %s", url)
                return False
            except httpx.RequestError as e:
                logging.error("❌ ERROR: %s (Reason: %s)", url, str(e))
                return False


def load_urls(file_path):
    """Load URLs from a JSON file and extract relevant links."""
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []

    urls = set()  # Use a set to avoid duplicates

    if isinstance(data, list):
        for entry in data:
            urls.add(entry.get("scheme_link", "") or entry.get("schemeUrl", ""))
            urls.add(entry.get("pdfUrl", ""))
    elif isinstance(data, dict) and "urls" in data:
        urls.update(data["urls"])  # Add all URLs from the dict

    return list(filter(None, urls))  # Convert set to list and remove empty entries


async def process_json_files():
    """Process all JSON files in the given directory."""
    if not os.path.isdir(DIRECTORY):
        return

    tasks = []
    for filename in os.listdir(DIRECTORY):
        if filename.endswith(".json"):
            file_path = os.path.join(DIRECTORY, filename)
            urls = load_urls(file_path)

            if not urls:
                continue

            for url in urls:
                tasks.append(check_url(url))

    # Run tasks with concurrency control
    await asyncio.gather(*tasks)


class Command(BaseCommand):
    help = "Check URLs from JSON files in the 'scrapedData' directory."

    def handle(self, *args, **options):
        if not os.path.isdir(DIRECTORY):
            self.stderr.write(self.style.ERROR(f"❌ Invalid directory: {DIRECTORY}"))
            return

        asyncio.run(process_json_files())
        self.stdout.write(self.style.SUCCESS("✅ URL Checking Completed!"))
