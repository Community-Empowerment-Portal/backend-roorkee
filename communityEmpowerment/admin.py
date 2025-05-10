from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django_celery_beat.models import (ClockedSchedule, CrontabSchedule, 
IntervalSchedule, PeriodicTask, SolarSchedule)
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken, OutstandingToken)
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group, Permission
import json
from django.urls import reverse
from django.utils.timezone import localtime
import pytz
from .models import (

    State, Department, Organisation, Scheme, Beneficiary, SchemeBeneficiary, FAQ, Resource, CompanyMeta, Organization,
    Benefit, Criteria, Procedure, Document, SchemeDocument, Sponsor, ProfileField, ProfileFieldChoice, ProfileFieldValue, CustomUser,
    SchemeSponsor, CustomUser, Banner, Tag, SchemeReport, WebsiteFeedback, SchemeFeedback, LayoutItem, UserEvents, Announcement, UserPrivacySettings
)
from django.db.models import Count
from django.db.models import Min
from orderable.admin import OrderableAdmin
from django.utils.html import format_html

from django.contrib.admin import SimpleListFilter



class OrganizationScopedRelatedFilter(SimpleListFilter):
    title = 'Department'
    parameter_name = 'department'

    def lookups(self, request, model_admin):
        org = request.user.organization
        return [(d.id, d.department_name) for d in Department.objects.filter(organization=org)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(department__id=self.value())
        return queryset



class OrganizationScopedAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organization=request.user.organization)

    def save_model(self, request, obj, form, change):
        if not obj.organization_id:
            obj.organization = request.user.organization
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "department":
                kwargs["queryset"] = Department.objects.filter(organization=request.user.organization)
            elif db_field.name == "state":
                kwargs["queryset"] = State.objects.filter(organization=request.user.organization)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            org = request.user.organization
            if db_field.name == "tags":
                kwargs["queryset"] = Tag.objects.filter(organization=org)
            elif db_field.name == "benefits":
                kwargs["queryset"] = Benefit.objects.filter(organization=org)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

        
# Custom Admin Site
class CustomAdminSite(admin.AdminSite):
    site_header = "Community Empowerment Portal Admin Panel"
    site_title = "Admin Portal"
    index_title = "Welcome to your Admin Panel"
    def get_app_list(self, request,app_label="None"):
        app_dict = self._build_app_dict(request)
        app_list = [
            {
                'name': 'Access Management',
                'app_label': 'auth',
                'models': [
                    {'name': 'Users', 'object_name': 'CustomUser', 'admin_url': '/admin/communityEmpowerment/customuser/'},
                    {'name': 'Groups', 'object_name': 'Group', 'admin_url': '/admin/auth/group/'},
                    {'name': 'Permissions', 'object_name': 'Permission', 'admin_url': '/admin/auth/permission/'},
                    {'name': 'Tenants', 'object_name': 'Organization', 'admin_url': '/admin/communityEmpowerment/organization/'},
                    {'name': 'User Privacy Setting', 'object_name': 'UserPrivacySettings', 'admin_url': '/admin/communityEmpowerment/userprivacysettings/'},
                ]
            },
            {
                'name': 'Layouts',
                'app_label': 'layouts',
                'models': [
                    {'name': 'Profile Fields', 'object_name': 'ProfileField', 'admin_url': '/admin/communityEmpowerment/profilefield/'},
                    {'name': 'Profile Field Values', 'object_name': 'ProfileFieldValue', 'admin_url': '/admin/communityEmpowerment/profilefieldvalue/'},
                    {'name': 'Layout items', 'object_name':'LayoutItem','admin_url': '/admin/communityEmpowerment/layoutitem/' },
                    {'name': 'FAQs', 'object_name': 'FAQ', 'admin_url': '/admin/communityEmpowerment/faq/'},
                ]
            },
            {
                'name': 'All Schemes',
                'app_label': 'schemes',
                'models': [
                    {'name': 'Schemes', 'object_name': 'Scheme', 'admin_url': '/admin/communityEmpowerment/scheme/'},
                    {'name': 'Benefits', 'object_name': 'Benefit', 'admin_url': '/admin/communityEmpowerment/benefit/'},
                    {'name': 'Criteria', 'object_name': 'Criteria', 'admin_url': '/admin/communityEmpowerment/criteria/'},
                    {'name': 'Departments', 'object_name': 'Department', 'admin_url': '/admin/communityEmpowerment/department/'},
                    {'name': 'Organizations', 'object_name': 'Organisation', 'admin_url': '/admin/communityEmpowerment/organisation/'},
                    {'name': 'Procedures', 'object_name': 'Procedure', 'admin_url': '/admin/communityEmpowerment/procedure/'},
                    {'name': 'Scheme Beneficiaries', 'object_name': 'SchemeBeneficiary', 'admin_url': '/admin/communityEmpowerment/schemebeneficiary/'},
                    {'name': 'Documents', 'object_name': 'Document', 'admin_url': '/admin/communityEmpowerment/document/'},
                    {'name': 'Scheme Sponsors', 'object_name': 'SchemeSponsor', 'admin_url': '/admin/communityEmpowerment/schemesponsor/'},
                    {'name': 'States', 'object_name': 'State', 'admin_url': '/admin/communityEmpowerment/state/'},
                    {'name': 'Tags', 'object_name': 'Tag', 'admin_url': '/admin/communityEmpowerment/tag/'},
                    {'name': 'Resources', 'object_name': 'Resource', 'admin_url': '/admin/communityEmpowerment/resource/'},
                

                ]
            },
            {
                'name': 'Feedback & Reports',
                'app_label': 'feedback',
                'models': [
                    {'name': 'Scheme Feedbacks', 'object_name': 'SchemeFeedback', 'admin_url': '/admin/communityEmpowerment/schemefeedback/'},
                    {'name': 'Scheme Reports', 'object_name': 'SchemeReport', 'admin_url': '/admin/communityEmpowerment/schemereport/'},
                    {'name': 'Website Feedbacks', 'object_name': 'WebsiteFeedback', 'admin_url': '/admin/communityEmpowerment/websitefeedback/'},
                ]
            },
            {
                'name': 'User Events',
                'app_label': 'analytics',
                'models': [
                    {'name': 'User Events', 'object_name': 'UserEvents', 'admin_url': '/admin/communityEmpowerment/userevents/'},
                ]
            },
            {
                'name': 'Assets',
                'app_label': 'assets',
                'models': [
                    {'name': 'Banners', 'object_name': 'Banner', 'admin_url': '/admin/communityEmpowerment/banner/'},
                    {'name': 'Announcements', 'object_name': 'Announcement', 'admin_url': '/admin/communityEmpowerment/announcement/'},
                    {'name': 'Company Meta', 'object_name': 'CompanyMeta', 'admin_url': '/admin/communityEmpowerment/companymeta/'},
                ]
            },
            {
                'name': 'Periodic Tasks',
                'app_label': 'Periodic Tasks',
                'models': [
                    {'name': 'Clocked', 'object_name': 'Clocked', 'admin_url': '/admin/django_celery_beat/clockedschedule/'},
                    {'name': 'Crontabs', 'object_name': 'Crontabs', 'admin_url': '/admin/django_celery_beat/crontabschedule/'},
                    {'name': 'Intervals', 'object_name': 'Intervals', 'admin_url': '/admin/django_celery_beat/intervalschedule/'},
                    {'name': 'Periodic tasks', 'object_name': 'Periodic tasks', 'admin_url': '/admin/django_celery_beat/periodictask/'},
                    {'name': 'Solar events', 'object_name': 'Solar events', 'admin_url': '/admin/django_celery_beat/solarschedule/'}
                ]
            },
            {
                'name': 'Token Blacklist',
                'app_label': 'Token Blacklist',
                'models': [
                    {'name': 'Blacklisted tokens', 'object_name': 'Blacklisted tokens', 'admin_url': '/admin/token_blacklist/blacklistedtoken/'},
                    {'name': 'Outstanding tokens', 'object_name': 'Outstanding tokens', 'admin_url': '/admin/token_blacklist/outstandingtoken/'}
                ]
            },
        ]

        # Sort the models inside each app by 'name'
        for app in app_list:
            app['models'] = sorted(app['models'], key=lambda model: model['name'])

        # Sort the app list by 'name'
        sorted_app_list = sorted(app_list, key=lambda app: app['name'])

        return sorted_app_list
        
# Create custom admin instance
admin_site = CustomAdminSite(name='admin')

class CustomGroupAdmin(GroupAdmin):
    fieldsets = (
        (None, {'fields': ('name','permissions')}),
    )
    list_display = ('name',) 
    search_fields = ('name',) 
    list_filter = ('name',) 

admin_site.register(Group, CustomGroupAdmin)



class BannerAdmin(ImportExportModelAdmin):
    list_display = ['title', 'is_active']
    search_fields = ['title']
admin_site.register(Banner)

class SchemeResource(resources.ModelResource):
    class Meta:
        model = Scheme
        fields = ('id', 'title', 'department__department_name', 'introduced_on', 'valid_upto', 'funding_pattern', 'description', 'scheme_link')
        export_order = ('id', 'title', 'department__department_name', 'introduced_on', 'valid_upto', 'funding_pattern', 'description', 'scheme_link')



class ProcedureInline(admin.TabularInline):
    model = Procedure
    extra = 1


class SchemeAdmin(ImportExportModelAdmin, OrganizationScopedAdmin):
    resource_class = SchemeResource
    list_display = ('title', 'department','is_active', 'introduced_on', 'valid_upto', 'funding_pattern', 'view_count', 'apply_count')
    readonly_fields = ('view_count', 'apply_count') 
    list_editable = ('is_active',) 
    search_fields = ('title', 'description','is_active')
    list_filter = (OrganizationScopedRelatedFilter, 'introduced_on', 'valid_upto', 'funding_pattern','is_active')
    inlines = [ProcedureInline]

    def is_active_toggle(self, obj):
        """ Show 'Active' / 'Inactive' with color styling """
        color = "green" if obj.is_active else "red"
        status = "Active" if obj.is_active else "Inactive"
        return format_html(f'<span style="color: {color}; font-weight: bold;">{status}</span>')
    is_active_toggle.short_description = "Status"
admin_site.register(Scheme, SchemeAdmin)

class SchemeReportAdmin(OrganizationScopedAdmin):
    list_display = ['id', 'linked_user', 'scheme_id', 'created_at'] 
    list_filter = ['created_at'] 

    def linked_user(self, obj):
        url = reverse('admin:communityEmpowerment_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    
    linked_user.short_description = "User"
admin_site.register(SchemeReport, SchemeReportAdmin)

class WebsiteFeedbackAdmin(OrganizationScopedAdmin):
    list_display = ['id', 'user', 'description', 'created_at'] 
    list_filter = ['created_at']
admin_site.register(WebsiteFeedback)

class SchemeFeedbackAdmin(OrganizationScopedAdmin):
    list_display = ('user', 'scheme', 'feedback', 'rating', 'created_at')
    search_fields = ('user__username', 'scheme__title', 'feedback')
    list_filter = ('created_at', 'rating')
admin_site.register(SchemeFeedback)


admin_site.register(Permission)
    
class ProfileFieldChoiceInline(admin.TabularInline):
    model = ProfileFieldChoice
    extra = 0
    fields = ('value', 'is_active')
    # readonly_fields = ('value',)
    can_delete = True
    def has_add_permission(self, request, obj=None):
        """Prevent adding new choices inline."""
        return True

class ProfileFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'field_type', 'is_active','position', 'is_fixed')
    list_filter = ['is_active', 'field_type', 'is_fixed']
    list_editable = ['is_active', 'position']
    # readonly_fields = ['name', 'field_type', 'placeholder', 'min_value', 'max_value']
    inlines = [ProfileFieldChoiceInline]
    def has_add_permission(self, request):
        """Disallow adding new fields."""
        return True

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_fixed:
            return False
        return True
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_fixed:
            return ['name', 'field_type', 'placeholder', 'min_value', 'max_value', 'is_fixed']
        return []
    

admin_site.register(ProfileField, ProfileFieldAdmin)

class ProfileFieldValueAdmin(admin.ModelAdmin):
    list_display = ('user', 'field', 'value')

admin_site.register(ProfileFieldValue)

class ProfileFieldInline(admin.TabularInline):
    model = ProfileFieldValue
    extra = 0
    # readonly_fields = ('field', 'value') 

    def has_add_permission(self, request, obj):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


class CustomUserAdmin(UserAdmin, OrganizationScopedAdmin, ImportExportModelAdmin):
    model = CustomUser
    list_display = ("username", "email", "is_active", "is_staff", "is_email_verified")
    list_filter = ("is_active", "is_staff", "is_email_verified", "groups")
    search_fields = ("username", "email")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal Info", {"fields": ["name", "organization"]}),
        ("Important Dates", {"fields": ["last_login"]}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "organization",
                ),
            },
        ),
    )
    inlines = [ProfileFieldInline]

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))

        # Show permissions section only if the user is marked as staff
        if obj and obj.is_staff:
            fieldsets.append(
                (
                    "Permissions",
                    {
                        "fields": (
                            "groups",
                            "user_permissions",
                            'is_email_verified',
                        )
                    },
                )
            )

        return fieldsets


admin_site.register(CustomUser, CustomUserAdmin)


class TagAdmin(OrganizationScopedAdmin):
    list_display = ('category_display', 'tag_count', 'weight', 'tag_names_preview')
    # list_filter = ('category',)
    search_fields = ('category',)
    ordering = ["category"]
    readonly_fields = ("tag_names",)
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by('category').distinct('category')

    def category_display(self, obj):
        return obj.category

    category_display.admin_order_field = 'category'
    category_display.short_description = 'Category'

    def tag_count(self, obj):
        return obj.__class__.objects.filter(category=obj.category).count()
    
    tag_count.short_description = "Tag Count"

    def tag_names(self, obj):
        """ Show first 5 tags in detail view, with 'Show All' button """
        tags = list(Tag.objects.filter(category=obj.category).values_list('name', flat=True))
        
        if not tags:
            return "No Tags"
        
        preview_tags = tags[:5]
        preview_text = ", ".join(preview_tags)
        
        if len(tags) > 5:
            full_text = ", ".join(tags)
            return format_html(
                f'<span class="tag-preview">{preview_text}</span>'
                f'<span class="tag-full" style="display:none;">{full_text}</span> '
                f'<a href="#" class="show-all-btn" onclick="showFullTags(this); return false;">Show All</a>'
            )
        else:
            return preview_text

    tag_names.short_description = "Tag Names"

    def tag_names_preview(self, obj):
        """ Show first 5 tags in list view with 'Show All' button """
        return self.tag_names(obj)

    tag_names_preview.short_description = "Tag Names Preview"

    class Media:
        """ Inject JavaScript for 'Show All' functionality """
        js = ('admin/js/show_tags.js',)

admin_site.register(Tag, TagAdmin)


class StateAdmin(OrganizationScopedAdmin):
    list_display = ('state_name', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('state_name',)
    actions = ['activate_states', 'deactivate_states']

    def activate_states(self, request, queryset):
        queryset.update(is_active=True)
    activate_states.short_description = "Activate selected states"

    def deactivate_states(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_states.short_description = "Deactivate selected states"

    def is_active_checkbox(self, obj):
        """ Show 'Active' / 'Inactive' with color styling """
        color = "green" if obj.is_active else "red"
        status = "Active" if obj.is_active else "Inactive"
        return format_html(f'<span style="color: {color}; font-weight: bold;">{status}</span>')

    is_active_checkbox.short_description = "Status"

    def save_model(self, request, obj, form, change):
        """Override save_model to handle state deactivation"""
        super().save_model(request, obj, form, change)
        if not obj.is_active:
            Department.objects.filter(state=obj).update(is_active=False)
            Scheme.objects.filter(department__state=obj).update(is_active=False)

admin_site.register(State, StateAdmin)

@admin.register(Department)
class DepartmentAdmin(OrganizationScopedAdmin):
    list_display = ('department_name', 'state', 'is_active')
    list_editable = ('is_active',)
    # list_filter = (OrganizationScopedRelatedFilter, 'state', 'is_active')
    search_fields = ('department_name',)
    actions = ['activate_departments', 'deactivate_departments']

    def activate_departments(self, request, queryset):
        queryset.update(is_active=True)
    activate_departments.short_description = "Activate selected departments"

    def deactivate_departments(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_departments.short_description = "Deactivate selected departments"

admin_site.register(Department, DepartmentAdmin)
admin_site.register(Organisation, OrganizationScopedAdmin)
admin_site.register(SchemeBeneficiary, OrganizationScopedAdmin)
admin_site.register(Benefit, OrganizationScopedAdmin)
admin_site.register(Criteria, OrganizationScopedAdmin)
admin_site.register(Procedure, OrganizationScopedAdmin)
admin_site.register(Document, OrganizationScopedAdmin)
admin_site.register(SchemeSponsor, OrganizationScopedAdmin)

admin_site.register(ClockedSchedule, OrganizationScopedAdmin)
admin_site.register(CrontabSchedule, OrganizationScopedAdmin)
admin_site.register(IntervalSchedule, OrganizationScopedAdmin)
admin_site.register(PeriodicTask, OrganizationScopedAdmin)
admin_site.register(SolarSchedule, OrganizationScopedAdmin)

admin_site.register(BlacklistedToken, OrganizationScopedAdmin)
admin_site.register(OutstandingToken, OrganizationScopedAdmin)
admin.site.register(CustomUser, CustomUserAdmin)


class LayoutItemAdmin(OrganizationScopedAdmin):
    list_display = ("column_name", "order", 'is_active')
    list_editable = ("order",'is_active')
    ordering = ("order",)
    readonly_fields = ("column_name",)
    def has_add_permission(self, request):
        """Disallow adding new fields."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disallow deleting fields."""
        return False

admin_site.register(LayoutItem, LayoutItemAdmin)

class FAQAdmin(OrganizationScopedAdmin):
    list_display = ('question', 'is_active', "order")
    list_filter = ('is_active',)
    ordering = ("order",)
    search_fields = ('question', 'answer')
    list_editable = ('is_active', "order",)

admin_site.register(FAQ, FAQAdmin)
admin_site.register(Resource, OrganizationScopedAdmin)
admin_site.register(CompanyMeta, OrganizationScopedAdmin)

class UserEventsAdmin(OrganizationScopedAdmin, ImportExportModelAdmin):
    list_display = ('id', "get_scheme_title", 'user', 'event_type', 'get_watch_time', 'details', 'get_timestamp_ist')
    search_fields = ('user__username', 'event_type')
    list_filter = ('event_type', 'timestamp')

    @admin.display(description='Timestamp (IST)')
    def get_timestamp_ist(self, obj):
        ist_timezone = pytz.timezone('Asia/Kolkata')
        local_timestamp = localtime(obj.timestamp, ist_timezone)
        return local_timestamp.strftime('%Y-%m-%d %H:%M:%S')

    def get_scheme_title(self, obj):
        """ Fetch scheme title and link using scheme_id """
        try:
            scheme = Scheme.objects.get(id=obj.scheme_id)
            return format_html('<a href="{}" target="_blank">{}</a>', scheme.scheme_link or '#', scheme.title)
        except Scheme.DoesNotExist:
            return "Scheme Not Found"
        except Exception as e:
            return f"Error: {str(e)}"

    get_scheme_title.short_description = "Scheme Title"

    @admin.display(description="Event Type")
    def get_event_type(self, obj):
        try:
            return obj.get_event_type_display()
        except AttributeError:
            return "Error: Invalid Event Type"
        
    def get_watch_time(self, obj):
        """ Extracts watch_time separately for better display """
        try:
            details = obj.details if isinstance(obj.details, dict) else json.loads(obj.details)
            return details.get('watch_time', 'N/A') 
        except (json.JSONDecodeError, TypeError, KeyError):
            return "N/A"


    get_watch_time.short_description = "Watch Time"
    def formatted_details(self, obj):
        try:
            if not obj.details:
                return "-"

            details = obj.details if isinstance(obj.details, dict) else json.loads(obj.details)
            
            formatted_json = json.dumps(details, indent=2)
            formatted_json = formatted_json.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            formatted_json = formatted_json.replace("\n", "<br>").replace(" ", "&nbsp;")

            return format_html(f"<pre>{formatted_json}</pre>")
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            return format_html(f"<pre>Error: {str(e)}</pre>")

    formatted_details.allow_tags = True
    formatted_details.short_description = "Event Details"

admin_site.register(UserEvents, UserEventsAdmin)


class AnnouncementAdmin(OrganizationScopedAdmin):
    list_display = ('title', 'created_at', 'is_active')
    search_fields = ('title',)

admin_site.register(Announcement, AnnouncementAdmin)
admin_site.register(Organization)


class UserPrivacySettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'allow_information_usage', 'allow_information_sharing')
    list_filter = ('allow_information_usage', 'allow_information_sharing')
    search_fields = ('user__username', 'user__email')

admin_site.register(UserPrivacySettings, UserPrivacySettingsAdmin)