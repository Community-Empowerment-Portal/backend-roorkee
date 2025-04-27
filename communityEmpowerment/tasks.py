# # tasks.py

# import os
# import json
# import google.generativeai as genai
# from dotenv import load_dotenv
# from celery import Celery
# from celery import shared_task
# from django.core.management import call_command

# load_dotenv()

# app = Celery('mysite')
# app.config_from_object('django.conf:settings')

# @app.task
# def run_processing_task():
#     file_path = 'communityEmpowerment/management/commands/mappedSchemesData.json'

#     data = None

#     try:
#         with open(file_path, 'rb') as f:
#             content = f.read()
#             data = json.loads(content.decode('utf-8', errors='replace'))
#     except UnicodeDecodeError:
#         print("Error: Could not decode JSON file.")
#         return
#     except FileNotFoundError:
#         print("Error: File not found.")
#         return

#     if data is None:
#         print("Error: Could not read JSON file.")
#         return

#     if isinstance(data, list) and len(data) > 0:
#         raw_json = data
#     else:
#         print("Error: JSON data does not contain a list or is empty.")
#         return

#     formatted_data_template = {
#         "states": [
#             {
#                 "state_name": "Tamil Nadu",
#                 
#                 "departments": [
#                     {
#                         "department_name": "Department of Education",
#                         
#                         "organisations": [
#                             {
#                                 "organisation_name": "Educational Board",
#                                 
#                                 "schemes": []
#                             }
#                         ]
#                     }
#                 ]
#             }
#         ]
#     }

#     GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

#     genai.configure(api_key=GEMINI_API_KEY)
#     model = genai.GenerativeModel('gemini-1.5-flash')

#     def process_chunk(chunk):
#         formatted_data = formatted_data_template.copy()

#         prompt = f"""
#         Given a JSON array {json.dumps(chunk)}, referred to as rawjson, and a JSON object {json.dumps(formatted_data)}, referred to as formattedjson, your task is to populate the values in formattedjson based on the data in rawjson for each JSON object individually. Return the resulting JSON object in the formattedjson JSON format. Ensure that the output consists solely of JSON and nothing else. Consider the state as Tamil Nadu.
#         """

#         response = model.generate_content(prompt)

#         if not response or not response.candidates:
#             print("Error: No valid response received from the model.")
#             return None

#         response_text = response.text.strip("```json\n").strip("```")

#         response_json = None
#         try:
#             response_json = json.loads(response_text)
#         except json.JSONDecodeError as e:
#             print(f"Error: Could not decode the response as JSON. {e}")
#             print(response_text)
#             return None

#         return response_json

#     chunk_size = 10
#     processed_chunks = []

#     for i in range(0, len(raw_json), chunk_size):
#         chunk = raw_json[i:i + chunk_size]
#         result = process_chunk(chunk)
#         if result:
#             processed_chunks.append(result)

#     final_result = formatted_data_template.copy()

#     for chunk in processed_chunks:
#         final_result['states'][0]['departments'][0]['organisations'][0]['schemes'].extend(
#             chunk['states'][0]['departments'][0]['organisations'][0]['schemes']
#         )

#     output_file_path = './formattedSchemesData.json'
#     try:
#         with open(output_file_path, 'w', encoding='utf-8') as f:
#             json.dump(final_result, f, ensure_ascii=False, indent=2)
#         print(f"Data successfully saved to {output_file_path}")
#     except Exception as e:
#         print(f"Error: Could not save data to file. {e}")


# @shared_task
# def load_data_task():
#     call_command('load_data')
#     print("Data loaded successfully.")


# communityEmpowerment/tasks.py
from celery import shared_task
from django.core.management import call_command
from django.core.mail import send_mail
from django.conf import settings


# @shared_task
# def scrape_and_process_schemes():
#     call_command('run_all_scripts_proxy')  
    # print("Data loaded successfully.")

@shared_task
def check_urls_task():
    call_command('check_urls')  # Calls the check_urls.py command



@shared_task
def send_weekly_email():
    recipients = ["karthikreddy0165@gmail.com", "karthik.r23csai@nst.rishihood.edu.in"]  
    subject = "Weekly Update"
    message = "Analytics report"

    for recipient in recipients:
        send_mail(subject, message, settings.EMAIL_FROM, [recipient], fail_silently=False)

    return f"Weekly emails sent to {len(recipients)} users"

@shared_task
def send_expiry_email_task():
    call_command("send_expiry_mails")