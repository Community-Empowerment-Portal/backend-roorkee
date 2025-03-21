import os
import json
import logging
import requests
import concurrent.futures
from django.core.management.base import BaseCommand

TIMEOUT = 10
LOG_FILE = "url_check.log"

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def check_url(url):
    """Check if a URL is accessible."""
    if not url or not isinstance(url, str):
        logging.warning("Skipping invalid URL: %s", url)
        return False
    
    try:
        response = requests.head(url, timeout=TIMEOUT)
        if response.status_code == 200:
            logging.info("✅ SUCCESS: %s", url)
            return True
        else:
            logging.warning("⚠️ WARNING: %s returned status %d", url, response.status_code)
            return False
    except requests.RequestException as e:
        logging.error("❌ ERROR: %s is not accessible. Reason: %s", url, e)
        return False


def load_urls(file_path):
    """Load URLs from a JSON file and extract relevant links."""
    if not os.path.exists(file_path):
        logging.error("❌ ERROR: File %s not found.", file_path)
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            logging.error("❌ ERROR: Failed to parse JSON in %s. Reason: %s", file_path, e)
            return []

    urls = []
    if isinstance(data, list):
        for entry in data:
            urls.append(entry.get("scheme_link", "") or entry.get("schemeUrl", ""))
            urls.append(entry.get("pdfUrl", ""))
    elif isinstance(data, dict) and "urls" in data:
        urls.extend(data["urls"])
    else:
        logging.warning("⚠️ Unexpected format in %s", file_path)

    return list(filter(None, urls))  # Remove empty strings


def process_json_files(directory):
    """Process all JSON files in the given directory."""
    if not os.path.isdir(directory):
        logging.error("❌ ERROR: Invalid directory %s", directory)
        return

    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            logging.info("\n📂 Processing file: %s", file_path)
            urls = load_urls(file_path)

            if not urls:
                logging.warning("⚠️ No valid URLs found in %s", filename)
                continue

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(check_url, urls)


class Command(BaseCommand):
    help = "Check URLs from JSON files in a given directory."

    def add_arguments(self, parser):
        parser.add_argument(
            "--directory",
            type=str,
            help="Path to the directory containing JSON files. Defaults to 'scrapedData'."
        )

    def handle(self, *args, **options):
        directory = os.path.join(os.path.dirname(__file__), "..", "scrapedData")

        if not os.path.isdir(directory):
            self.stderr.write(self.style.ERROR(f"❌ Invalid directory: {directory}"))
            return

        logging.info("🚀 Starting URL checks in directory: %s", directory)
        process_json_files(directory)
        self.stdout.write(self.style.SUCCESS("✅ URL Checking Completed!"))
