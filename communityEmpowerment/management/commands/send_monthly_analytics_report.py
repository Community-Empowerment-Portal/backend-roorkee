from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'monthly analytics report'
    def handle(self, *args, **kwargs):
        """
        Generate and send a comprehensive monthly analytics report via email.
        This task collects all relevant analytics data and sends it in a CSV format
        that matches the analytics dashboard.
        """
        from django.core.mail import EmailMessage
        from django.conf import settings
        import io
        import csv
        from datetime import datetime, timedelta
        from calendar import monthrange
        import calendar

        # Calculate date range for the past month
        end_date = datetime.now().date()
        start_date = end_date.replace(day=1) - timedelta(days=1)  # Last day of previous month
        start_date = start_date.replace(day=1)  # First day of previous month
        
        month_name = start_date.strftime('%B %Y')
        
        try:
            # Import required models and functions
            from communityEmpowerment.models import CustomUser, UserEvents, Scheme, Tag
            from django.db.models import Count, Sum, Case, When, IntegerField, Q, F
            from django.db.models.functions import Coalesce, TruncDate, TruncWeek, TruncMonth
            from django.utils import timezone
            
            # Create CSV content directly
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            
            # Write report header
            writer.writerow([
                'COMPREHENSIVE ANALYTICS REPORT',
                f'Period: {month_name}'
            ])
            writer.writerow([])  # Empty row for spacing
            
            # =================== USER STATISTICS ===================
            writer.writerow(['1. USER STATISTICS'])
            writer.writerow(['Metric', 'Count'])
            
            # New user signups
            user_count = CustomUser.objects.filter(date_joined__range=[start_date, end_date]).count()
            writer.writerow(['New User Signups', user_count])
            
            # Active users
            active_users = CustomUser.objects.filter(last_login__range=[start_date, end_date]).count()
            writer.writerow(['Active Users', active_users])
            
            # Total users
            total_users = CustomUser.objects.count()
            writer.writerow(['Total Users (All-Time)', total_users])
            
            # Monthly breakdown
            writer.writerow([])
            writer.writerow(['Monthly User Trends'])
            writer.writerow(['Month', 'New Signups', 'Active Users'])
            
            # Get the last 6 months for trend analysis
            for i in range(5, -1, -1):
                trend_month = (end_date.replace(day=1) - timedelta(days=1)) - timedelta(days=30*i)
                trend_month_start = trend_month.replace(day=1)
                trend_month_end = (trend_month.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_signups = CustomUser.objects.filter(
                    date_joined__range=[trend_month_start, trend_month_end]
                ).count()
                
                month_active = CustomUser.objects.filter(
                    last_login__range=[trend_month_start, trend_month_end]
                ).count()
                
                writer.writerow([
                    trend_month.strftime('%B %Y'), 
                    month_signups,
                    month_active
                ])
            
            writer.writerow([])  # Empty row for spacing
            
            # =================== EVENT STATISTICS ===================
            writer.writerow(['2. EVENT STATISTICS'])
            writer.writerow(['Event Type', 'Count'])
            
            event_counts = UserEvents.objects.filter(
                timestamp__range=[start_date, end_date]
            ).values('event_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            for event in event_counts:
                writer.writerow([event['event_type'], event['count']])
            
            # Daily event trend
            writer.writerow([])
            writer.writerow(['Daily Event Trends'])
            writer.writerow(['Date', 'Views', 'Searches', 'Downloads', 'Filters', 'Applies', 'Saves'])
            
            daily_events = UserEvents.objects.filter(
                timestamp__range=[start_date, end_date]
            ).annotate(
                date=TruncDate('timestamp')
            ).values('date').annotate(
                views=Count('id', filter=Q(event_type='view')),
                searches=Count('id', filter=Q(event_type='search')),
                downloads=Count('id', filter=Q(event_type='download')),
                filters=Count('id', filter=Q(event_type='filter')),
                applies=Count('id', filter=Q(event_type='apply')),
                saves=Count('id', filter=Q(event_type='save'))
            ).order_by('date')
            
            for day in daily_events:
                writer.writerow([
                    day['date'].strftime('%Y-%m-%d'),
                    day['views'],
                    day['searches'],
                    day['downloads'],
                    day['filters'],
                    day['applies'],
                    day['saves']
                ])
            
            writer.writerow([])  # Empty row for spacing
            
            # =================== POPULAR SCHEMES ===================
            writer.writerow(['3. POPULAR SCHEMES'])
            writer.writerow(['Scheme ID', 'Title', 'Views', 'Applies', 'Saves'])
            
            popular_schemes = UserEvents.objects.filter(
                timestamp__range=[start_date, end_date],
                scheme__isnull=False
            ).values('scheme').annotate(
                view_count=Count('id', filter=Q(event_type='view')),
                apply_count=Count('id', filter=Q(event_type='apply')),
                save_count=Count('id', filter=Q(event_type='save'))
            ).order_by('-view_count')[:20]
            
            scheme_ids = [item['scheme'] for item in popular_schemes]
            schemes = Scheme.objects.filter(id__in=scheme_ids)
            
            for item in popular_schemes:
                scheme = schemes.filter(id=item['scheme']).first()
                if scheme:
                    writer.writerow([
                        scheme.id, 
                        scheme.title, 
                        item['view_count'],
                        item['apply_count'],
                        item['save_count']
                    ])
            
            writer.writerow([])  # Empty row for spacing
            
            # =================== POPULAR SCHEMES BY CATEGORY ===================
            writer.writerow(['4. POPULAR SCHEMES BY CATEGORY'])
            
            categories = ["sc", "st", "obc", "women", "students", "disability", "agriculture"]
            
            for category in categories:
                writer.writerow([f"Category: {category.upper()}"])
                writer.writerow(['Scheme ID', 'Title', 'Views'])
                
                schemes_in_category = []
                for entry in popular_schemes:
                    scheme = schemes.filter(id=entry['scheme']).first()
                    if not scheme:
                        continue
                    
                    # Check if the scheme has the category tag
                    if scheme.tags.filter(name__icontains=category).exists():
                        schemes_in_category.append({
                            'scheme_id': scheme.id,
                            'title': scheme.title,
                            'view_count': entry['view_count']
                        })
                
                # Sort by view count and take top 5
                schemes_in_category.sort(key=lambda x: x['view_count'], reverse=True)
                for scheme_data in schemes_in_category[:5]:
                    writer.writerow([
                        scheme_data['scheme_id'],
                        scheme_data['title'],
                        scheme_data['view_count']
                    ])
                
                writer.writerow([])  # Empty row for spacing
            
            # =================== TAG STATISTICS ===================
            writer.writerow(['5. TAG STATISTICS'])
            writer.writerow(['Tag Name', 'Category', 'Views', 'Applies', 'Saves'])
            
            tag_stats = Tag.objects.annotate(
                view_count=Coalesce(
                    Sum(
                        Case(
                            When(schemes__userevents__event_type='view', 
                                schemes__userevents__timestamp__range=[start_date, end_date], 
                                then=1),
                            output_field=IntegerField()
                        )
                    ), 0
                ),
                apply_count=Coalesce(
                    Sum(
                        Case(
                            When(schemes__userevents__event_type='apply', 
                                schemes__userevents__timestamp__range=[start_date, end_date], 
                                then=1),
                            output_field=IntegerField()
                        )
                    ), 0
                ),
                save_count=Coalesce(
                    Sum(
                        Case(
                            When(schemes__userevents__event_type='save', 
                                schemes__userevents__timestamp__range=[start_date, end_date], 
                                then=1),
                            output_field=IntegerField()
                        )
                    ), 0
                )
            ).order_by('-view_count')[:30]
            
            for tag in tag_stats:
                writer.writerow([
                    tag.name, 
                    tag.category, 
                    tag.view_count, 
                    tag.apply_count, 
                    tag.save_count
                ])
            
            writer.writerow([])  # Empty row for spacing
            
            # =================== FILTER USAGE ===================
            writer.writerow(['6. FILTER USAGE'])
            writer.writerow(['Filter', 'Value', 'Count'])
            
            filter_usage = UserEvents.objects.filter(
                event_type='filter',
                timestamp__range=[start_date, end_date]
            ).values('details__filter', 'details__value').annotate(
                count=Count('id')
            ).order_by('-count')[:20]
            
            for filter_item in filter_usage:
                filter_name = filter_item.get('details__filter', 'N/A')
                filter_value = filter_item.get('details__value', 'N/A')
                writer.writerow([filter_name, filter_value, filter_item['count']])
            
            writer.writerow([])  # Empty row for spacing
            
            # =================== POPULAR SEARCHES ===================
            writer.writerow(['7. POPULAR SEARCHES'])
            writer.writerow(['Search Query', 'Count'])
            
            searches = UserEvents.objects.filter(
                event_type='search',
                timestamp__range=[start_date, end_date]
            ).values('details__query').annotate(
                count=Count('id')
            ).order_by('-count')[:20]
            
            for search in searches:
                query = search.get('details__query', 'N/A')
                writer.writerow([query, search['count']])

            # Get the CSV content
            csv_content = csv_buffer.getvalue()
            csv_buffer.close()

            # Prepare email
            subject = f"Monthly Analytics Report - {month_name}"
            message = f"""
    Dear Admin,

    Please find attached the monthly analytics report for {month_name}.

    This report includes:
    - User Statistics
    - Event Statistics
    - Popular Schemes
    - Category-wise Popular Schemes
    - Tag Statistics
    - Filter Usage Statistics
    - Popular Searches


    This is an automated message. Please do not reply.
            """

            # Create email with attachment
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.EMAIL_FROM,
                to=["karthikreddy0165@gmail.com", "karthik.r23csai@nst.rishihood.edu.in"]
            )

            # Attach CSV file
            email.attach(
                f'analytics_report_{start_date.strftime("%Y_%m")}.csv',
                csv_content,
                'text/csv'
            )

            # Send email
            email.send(fail_silently=False)

            return f"Monthly analytics report for {month_name} sent successfully"

        except Exception as e:
            # Log the error and send notification
            import logging
            logger = logging.getLogger(__name__)
            error_message = f"Error generating monthly analytics report: {str(e)}"
            logger.error(error_message)
            
            send_mail(
                subject="Error: Monthly Analytics Report Generation",
                message=error_message,
                from_email=settings.EMAIL_FROM,
                recipient_list=["karthikreddy0165@gmail.com"],
                fail_silently=True
            )
            return f"Failed to generate monthly analytics report: {str(e)}"
