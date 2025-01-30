import json
import os
import requests

TIMEOUT = 10  

def check_url(url):
    """Check if a URL is accessible."""
    try:
        response = requests.head(url, timeout=TIMEOUT)  # Using HEAD for efficiency
        if response.status_code == 200:
            print("Success")
            return True
        else:
            print(f"⚠️ WARNING: {url} returned status {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ ERROR: {url} is not accessible. Reason: {e}")
        return False

def check_urls_in_json(json_file):
    """Read JSON file and check all URLs inside."""
    if not os.path.exists(json_file):
        print(f"❌ ERROR: File {json_file} not found.")
        return
    
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for schemes in data:
        all_urls = []
        scheme_urls = schemes.get("scheme_link", "")
        all_urls.append(scheme_urls)
        # pdf_urls = schemes.get("pdfUrl", "")
        # all_urls.append(pdf_urls)

        for url in all_urls:
            check_url(url)


def main(input_file_path):
    """Check URLs in all JSON files."""
    print(f"\n🔍 Checking URLs in {input_file_path}...\n")
    check_urls_in_json(input_file_path)


states_and_ut = [
    "punjab",
    "andhraPradesh",
    "gujarat",
    "haryana",
    "Uttar Pradesh",
    "assam",
    "maharashtra",
    "manipur",
    "meghalaya",
    "kerala",
    "tamilnadu",
    "jammuAndKashmir",
    "puducherry",
    "odisha",
    "himachalPradesh",
    "madhyaPradesh",
    "uttarakhand",
    "sikkim",
    "telangana",
    "chhattisgarh",
    "arunachalpradesh",
    "delhi",
    "ladakh",
    "dadraAndNagarHaveli",
    "nagaland",
    "chandigarh",
    "andamanAndNicobar"
]

for state_name in states_and_ut:
    base_file_path = os.path.join(os.path.dirname(__file__),'..', 'scrapedData',f'{state_name}.json')
    input_file_path = os.path.abspath(base_file_path)
    main(input_file_path)





# if __name__ == "__main__":
#     main()
