import json
from datetime import datetime, timezone
import re
import os
from django.core.management.base import BaseCommand
from datetime import datetime
import pytz
base_file_path = os.path.join(os.path.dirname(__file__), '..','scrapedData')

class Command(BaseCommand):
    help = 'Converts and combines data into a JSON file'

    def handle(self, *args, **kwargs):
        # Your logic for combining data goes here
        with open('combined_schemes_data.json', 'w') as outfile:
            json.dump(combined_data, outfile, indent=4)
        self.stdout.write(self.style.SUCCESS('Combined data has been successfully saved to combined_schemes_data.json'))

def remove_leading_numbers(title):
    # Use a regular expression to remove leading numbers followed by a dot and whitespace
    if title is not None:
        return re.sub(r'^\d+\.\s*', '', title)
    return title
# Helper function to convert date format
def convert_date_format(date_str):
    if date_str:
        try:
            return datetime.strptime(date_str, "%d %b %Y").strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return None
    return None

# Helper function to determine tags based on scheme title and description
def determine_tags(title, description):
    tags = []
    text = f"{title} {description}".lower()
    if "scholarship" in text:
        tags.append("scholarship")
    if "job" in text or "employment" in text:
        tags.append("job")

    community_keywords = {
        "sc": ["scheduled caste", "sc"],
        "st": ["scheduled tribe", "st"],
        "obc": ["other backward class", "obc"],
        "general": ["general category"]
    }

    minority_keywords = {
        "muslim": ["muslim"],
        "christian": ["christian"],
        "sikh": ["sikh"],
        "buddhist": ["buddhist"],
        "parsi": ["parsi"],
        "jain": ["jain"],
    }

    education_keywords = {
        "undergraduate": ["ug", "undergraduate", "bachelor"],
        "postgraduate": ["pg", "postgraduate", "master"],
        "phd": ["phd", "doctoral"],
        "school": ["school", "high school", "10th", "12th"]
    }
    disability_keywords = {
        "physical": ["physically disabled", "orthopedic"],
        "visual": ["blind", "low vision"],
        "hearing": ["hearing impaired", "deaf"],
        "intellectual": ["intellectual disability", "autism"]
    }

    occupation_keywords = {
        "farmer": ["farmer", "agriculture"],
        "student": ["student"],
        "teacher": ["teacher", "professor"],
        "entrepreneur": ["entrepreneur", "business owner"],
        "laborer": ["labor", "worker"]
    }

    income_keywords = {
        "bpl": ["below poverty line", "bpl"],
        "middle": ["middle class", "lower middle"],
        "high": ["high income", "wealthy"]
    }
    def check_and_add_tags(keywords_dict, text, tags):
        for tag, keywords in keywords_dict.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)

    check_and_add_tags(community_keywords, text, tags)
    check_and_add_tags(minority_keywords, text, tags)
    check_and_add_tags(education_keywords, text, tags)
    check_and_add_tags(disability_keywords, text, tags)
    check_and_add_tags(occupation_keywords, text, tags)
    check_and_add_tags(income_keywords, text, tags)

    return tags

def clean_field(field):
    if isinstance(field, str):
        return field.replace("\\n", "").replace("\\", "").strip()
    elif isinstance(field, list):
        return [clean_field(item) for item in field]
    elif isinstance(field, dict):
        return {key: clean_field(value) for key, value in field.items()}
    return field 

def transform_and_add_state_data(state_name, original_data, combined_data):
    ist = pytz.timezone('Asia/Kolkata')
    created_at = datetime.now(ist).replace(microsecond=0).isoformat()

    for item in original_data:
        item = clean_field(item)
        department_name = item.get("department_name")

        # Find or create state
        state = next((s for s in combined_data["states"] if s["state_name"] == state_name), None)
        if not state:
            state = {
                "state_name": state_name,
                "created_at": created_at,
                "departments": []
            }
            combined_data["states"].append(state)

        # Find or create department
        department = next((d for d in state["departments"] if d["department_name"] == department_name), None)
        if not department:
            department = {
                "department_name": department_name,
                "created_at": created_at,
                "organisations": [
                    {
                        "organisation_name": department_name,
                        "created_at": created_at,
                        "schemes": []
                    }
                ]
            }
            state["departments"].append(department)

        # Add scheme to organisation
        organisation = department["organisations"][0]
        title = remove_leading_numbers(item.get("title"))
        description = item.get("description")
        scheme = {
            "title": title,
            "introduced_on": convert_date_format(item.get("introduced_on")),
            "valid_upto": item.get("valid_upto"),
            "funding_pattern": item.get("funding_pattern"),
            "description": description,
            "scheme_link": item.get("scheme_link"),
            "pdf_url": item.get("pdfUrl"),
            "beneficiaries": [
                beneficiary_type["beneficiary_type"] for beneficiary_type in item.get("beneficiaries", [])
            ],
            "documents": item.get("documents", []),
            "sponsors": [
                sponsor_type["sponsor_type"] for sponsor_type in item.get("sponsors", [])
            ],
            "criteria": [
                criteria_description["description"] for criteria_description in item.get("criteria", [])
            ],
            "procedures": [
                step_description["step_description"] for step_description in item.get("procedures", [])
            ],
            "tags": determine_tags(title, description) + item.get("tags", [])
        }
        organisation["schemes"].append(scheme)

def transform_and_add_uttar_pradesh_data(original_data, combined_data):
    for item in original_data:
        item = clean_field(item)
        state_name = "Uttar Pradesh"
        ist = pytz.timezone('Asia/Kolkata')
        created_at = datetime.now(ist).replace(microsecond=0).isoformat()
        department_name = "उत्तर प्रदेश सरकार"
        state = next((s for s in combined_data["states"] if s["state_name"] == state_name), None)

        if not state:
            state = {
                "state_name": state_name,
                "created_at": created_at,
                "departments": []
            }
            combined_data["states"].append(state)

        department = next((d for d in state["departments"] if d["department_name"] == department_name), None)

        if not department:
            department = {
                "department_name": department_name,
                "created_at": created_at,
                "organisations": [
                    {
                        "organisation_name": department_name,
                        "created_at": created_at,
                        "schemes": []
                    }
                ]
            }
            state["departments"].append(department)

        organisation = department["organisations"][0]
        if not item.get("title",""):
            continue
        title = remove_leading_numbers(item.get("title",""))
        scheme_link = item.get("scheme_link")
        description = item.get("description")
        scheme = {
            "title": title,
            "introduced_on": convert_date_format(item.get("introduced_on")),
            "valid_upto": convert_date_format(item.get("valid_upto")),
            "funding_pattern": item.get("funding_pattern"),
            "description": description,
            "scheme_link": scheme_link,
            
            "beneficiaries": [
                beneficiary_type["beneficiary_type"] for beneficiary_type in item.get("beneficiaries", [])
            ],
            "sponsors": [
                sponsor_type["sponsor_type"] for sponsor_type in item.get("sponsors", [])
            ],
            "tags": determine_tags(title, description),
            "benefits": [
                {"benefit_type": benefit} for benefit in item.get("benefits", [])
            ],
            "criteria": [
                criteria_description for criteria_description in item.get("eligibility", [])
            ],
            "procedures": [
                step_description for step_description in item.get("applicationProcess", [])
            ],
            "documents": [
                requirement for requirement in item.get("requirements", [])
            ]
        }
        organisation["schemes"].append(scheme)


def transform_and_add_goa_data(state_name, original_data, combined_data):
    ist = pytz.timezone('Asia/Kolkata')
    created_at = datetime.now(ist).replace(microsecond=0).isoformat()

    for item in original_data:
        item = clean_field(item)
        department_name = item.get("department_name")

        # Find or create state
        state = next((s for s in combined_data["states"] if s["state_name"] == state_name), None)
        if not state:
            state = {
                "state_name": state_name,
                "created_at": created_at,
                "departments": []
            }
            combined_data["states"].append(state)

        # Find or create department
        department = next((d for d in state["departments"] if d["department_name"] == department_name), None)
        if not department:
            department = {
                "department_name": department_name,
                "created_at": created_at,
                "organisations": [
                    {
                        "organisation_name": department_name,
                        "created_at": created_at,
                        "schemes": []
                    }
                ]
            }
            state["departments"].append(department)

        # Add scheme to organisation
        organisation = department["organisations"][0]
        title = remove_leading_numbers(item.get("title"))
        description = item.get("description")
        scheme = {
            "title": title,
            "introduced_on": convert_date_format(item.get("introduced_on")),
            "valid_upto": item.get("valid_upto"),
            "funding_pattern": item.get("funding_pattern"),
            "description": description,
            "scheme_link": item.get("schemeUrl"),
            "pdf_url": item.get("pdfUrl"),
            "beneficiaries": [
                beneficiary_type["beneficiary_type"] for beneficiary_type in item.get("beneficiaries", [])
            ],
            "documents": item.get("documents", []),
            "sponsors": [
                sponsor_type["sponsor_type"] for sponsor_type in item.get("sponsors", [])
            ],
            "criteria": [
                criteria_description["description"] for criteria_description in item.get("criteria", [])
            ],
            "procedures": [
                step_description["step_description"] for step_description in item.get("procedures", [])
            ],
            "tags": determine_tags(title, description) + item.get("tags", [])
        }
        organisation["schemes"].append(scheme)

def transform_and_add_jharkhand_data(original_data, combined_data):
    for item in original_data:
        item = clean_field(item)
        state_name = "Jharkhand"
        ist = pytz.timezone('Asia/Kolkata')
        created_at = datetime.now(ist).replace(microsecond=0).isoformat()
        department_name = item.get("department_name")
        state = next((s for s in combined_data["states"] if s["state_name"] == state_name), None)

        if not state:
            state = {
                "state_name": state_name,
                "created_at": created_at,
                "departments": []
            }
            combined_data["states"].append(state)

        department = next((d for d in state["departments"] if d["department_name"] == department_name), None)

        if not department:
            department = {
                "department_name": department_name,
                "created_at": created_at,
                "organisations": [
                    {
                        "organisation_name": department_name,
                        "created_at": created_at,
                        "schemes": []
                    }
                ]
            }
            state["departments"].append(department)

        organisation = department["organisations"][0]
        title = remove_leading_numbers(item.get("title",""))
        description = item.get("description")
        scheme = {
            "title": title,
            "introduced_on": convert_date_format(item.get("introduced_on")),
            "valid_upto": item.get("valid_upto"),
            "funding_pattern": item.get("funding_pattern"),
            "description": description,
            "scheme_link": item.get("schemeUrl"),
            "pdf_url": item.get("pdfUrl"),
            "beneficiaries": [
                beneficiary_type["beneficiary_type"] for beneficiary_type in item.get("beneficiaries",[])
            ],
            "documents": item.get("documents",[]),
            "sponsors": [
                sponsor_type["sponsor_type"] for sponsor_type in item.get("sponsors",[])
            ],
            "criteria": [
                criteria_description["description"] for criteria_description in item.get("criteria",[])
            ],
            "procedures": [
                step_description["step_description"] for step_description in item.get("procedures",[])
            ],
            "tags": determine_tags(title, description) + item.get("tags",[])
        }
        organisation["schemes"].append(scheme)




state_data_files = {
    "Meghalaya": "meghalaya.json",
    "Puducherry": "puducherry.json",
    "Jammu and Kashmir": "jammuAndKashmir.json",
    "Gujarat": "gujarat.json",
    "Maharashtra": "maharashtra.json",
    "Himachal Pradesh": "himachalPradesh.json",
    "Madhya Pradesh": "madhyaPradesh.json",
    "Kerala": "kerala.json",
    "Manipur": "manipur.json",
    "Tripura": "tripura.json",
    "Sikkim": "sikkim.json",
    "Telangana": "telangana.json",
    "Uttarakhand": "uttarakhand.json",
    "Delhi": "delhi.json",
    "Ladakh": "ladakh.json",
    "Andhra Pradesh": "andhraPradesh.json",
    "Assam": "assam.json",
    "Haryana": "haryana.json",
    "Punjab": "punjab.json",
    "Odisha": "odisha.json",
    "Arunachal Pradesh": "arunachalPradesh.json",
    "Dadra and Nagar Haveli": "dadraAndNagarHaveli.json",
    "Andaman and Nicobar": "andamanAndNicobar.json",
    "Chandigarh": "chandigarh.json",
    "Chhattisgarh": "chhattisgarh.json",
    "Rajasthan": "rajasthan.json",
    "Tamilnadu": "tamilnadu.json",
    "Nagaland": "nagaland.json",
    "West Bengal": "westBengal.json",
}

# Initialize the combined data structure
combined_data = {
    "states": []
}

# Process each state
for state_name, file_path in state_data_files.items():
    with open(base_file_path + "/" + file_path, "r") as file:
        state_data = json.load(file)
        transform_and_add_state_data(state_name, state_data, combined_data)

with open(base_file_path+"/up/up_youth_welfare.json", "r") as file:
    up_data = json.load(file)

with open(base_file_path+"/goa.json", "r") as file:
    goa_data = json.load(file)

with open(base_file_path+"/jharkhand.json", "r") as file:
    jharkhand_data = json.load(file)

transform_and_add_uttar_pradesh_data(up_data,combined_data)
transform_and_add_goa_data("Goa",goa_data,combined_data)
transform_and_add_jharkhand_data(jharkhand_data, combined_data)

# Save the combined data to a new JSON file
with open(base_file_path + "/combined_schemes_data.json", "w", encoding="utf-8") as file:
    json.dump(combined_data, file, ensure_ascii=False, indent=4)

# print("Combined data has been successfully saved to combined_schemes_data.json")
# print("Combined data has been successfully saved to combined_schemes_data.json")