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


@shared_task
def scrape_and_process_schemes():
    call_command('run_all_scripts_proxy')  
    print("Data loaded successfully.")

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

@shared_task
def send_monthly_analytics_report():
    """
    Generate and send a monthly analytics report via email.
    This task fetches analytics data as a CSV and sends it to configured recipients.
    """
    from django.core.mail import EmailMessage
    from django.conf import settings
    import requests
    import io
    import csv
    from datetime import datetime, timedelta

    # Calculate date range for the past month
    end_date = datetime.now().date()
    start_date = end_date.replace(day=1) - timedelta(days=1)  # Last day of previous month
    start_date = start_date.replace(day=1)  # First day of previous month
    
    month_name = start_date.strftime('%B %Y')
    
    try:
        # Use Django models directly instead of making an HTTP request
        from communityEmpowerment.models import CustomUser, UserEvents, Scheme, Tag
        from django.db.models import Count, Sum, Case, When, IntegerField 
        
        from django.db.models.functions import Coalesce
        
        # Create CSV content directly
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Write header row
        writer.writerow([
            'Analytics Report',
            f'Period: {month_name}'
        ])
        writer.writerow([])  # Empty row for spacing
        
        # User statistics
        user_count = CustomUser.objects.filter(date_joined__range=[start_date, end_date]).count()
        active_users = CustomUser.objects.filter(last_login__range=[start_date, end_date]).count()
        
        writer.writerow(['USER STATISTICS'])
        writer.writerow(['New Users', user_count])
        writer.writerow(['Active Users', active_users])
        writer.writerow([])  # Empty row for spacing
        
        # Event statistics
        writer.writerow(['EVENT STATISTICS'])
        writer.writerow(['Event Type', 'Count'])
        
        event_counts = UserEvents.objects.filter(
            timestamp__range=[start_date, end_date]
        ).values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for event in event_counts:
            writer.writerow([event['event_type'], event['count']])
        writer.writerow([])  # Empty row for spacing
        
        # Popular schemes
        writer.writerow(['POPULAR SCHEMES'])
        writer.writerow(['Scheme ID', 'Title', 'Views'])
        
        popular_schemes = UserEvents.objects.filter(
            event_type='view',
            timestamp__range=[start_date, end_date],
            scheme__isnull=False
        ).values('scheme').annotate(
            view_count=Count('id')
        ).order_by('-view_count')[:10]
        
        scheme_ids = [item['scheme'] for item in popular_schemes]
        schemes = Scheme.objects.filter(id__in=scheme_ids)
        
        for item in popular_schemes:
            scheme = schemes.filter(id=item['scheme']).first()
            if scheme:
                writer.writerow([scheme.id, scheme.title, item['view_count']])
        
        # Prepare email with CSV data
        subject = f"Monthly Analytics Report - {month_name}"
        message = f"""
        Dear Admin,

        Attached is the monthly analytics report for {month_name}.

        This report includes:
        - User statistics (new users, active users)
        - Event statistics
        - Popular schemes

        This is an automated message. Please do not reply.
        """
        
        recipients = ["karthikreddy0165@gmail.com", "karthik.r23csai@nst.rishihood.edu.in"]
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.EMAIL_FROM,
            to=recipients
        )
        
        # Attach the CSV file
        csv_buffer.seek(0)
        email.attach(f'analytics_report_{month_name}.csv', csv_buffer.getvalue(), 'text/csv')
        
        # Send the email
        email.send(fail_silently=False)
        
        return f"Monthly analytics report sent to {len(recipients)} recipients"
        
    except Exception as e:
        # Log error and return error message
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send monthly analytics report: {str(e)}")
        return f"Failed to send monthly analytics report: {str(e)}"
