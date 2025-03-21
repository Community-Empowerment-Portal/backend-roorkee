import json
import os
import requests
import logging
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

def check_urls_in_json(json_file):
    """Read JSON file and check all URLs inside."""
    if not os.path.exists(json_file):
        logging.error("❌ ERROR: File %s not found.", json_file)
        return
    
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    urls = []
    for schemes in data:
        urls.append(schemes.get("scheme_link", "") or schemes.get("schemeUrl", ""))
        urls.append(schemes.get("pdfUrl", ""))

    # Use ThreadPoolExecutor to check multiple URLs concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(check_url, urls)

class Command(BaseCommand):
    help = "Check URLs in all JSON files"

    def handle(self, *args, **kwargs):
        states_and_ut = [
            "punjab", "andhraPradesh", "gujarat", "haryana", "Uttar Pradesh", "assam",
            "maharashtra", "manipur", "meghalaya", "kerala", "tamilnadu", "jammuAndKashmir",
            "puducherry", "odisha", "himachalPradesh", "madhyaPradesh", "uttarakhand",
            "sikkim", "telangana", "chhattisgarh", "arunachalpradesh", "delhi", "ladakh",
            "dadraAndNagarHaveli", "nagaland", "chandigarh", "andamanAndNicobar"
        ]

        base_dir = os.path.join(os.path.dirname(__file__), '..', 'scrapedData')

        for state_name in states_and_ut:
            file_path = os.path.join(base_dir, f"{state_name}.json")
            logging.info("\n🔍 Checking URLs in %s...", file_path)
            check_urls_in_json(file_path)

        self.stdout.write(self.style.SUCCESS("✅ URL Checking Completed!"))
