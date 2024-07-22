from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import (
    State, Department, Organisation, Scheme, Beneficiary, SchemeBeneficiary,
    Benefit, Criteria, Procedure, Document, SchemeDocument, Sponsor,
    SchemeSponsor, CustomUser, Banner
)

admin.site.site_header = "Community Empowerment Portal Admin Panel"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to your Admin Panel"

admin.site.register(State)
admin.site.register(Department)
admin.site.register(Organisation)
admin.site.register(Beneficiary)
admin.site.register(SchemeBeneficiary)
admin.site.register(Benefit)
admin.site.register(Criteria)
admin.site.register(Procedure)
admin.site.register(Document)
admin.site.register(SchemeDocument)
admin.site.register(Sponsor)
admin.site.register(SchemeSponsor)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    readonly_fields = ('date_joined',)
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Banner)
class BannerAdmin(ImportExportModelAdmin):
    list_display = ['title', 'is_active']
    search_fields = ['title']

class SchemeResource(resources.ModelResource):
    class Meta:
        model = Scheme
        fields = ('id', 'title', 'department__department_name', 'introduced_on', 'valid_upto', 'funding_pattern', 'description', 'scheme_link')
        export_order = ('id', 'title', 'department__department_name', 'introduced_on', 'valid_upto', 'funding_pattern', 'description', 'scheme_link')

@admin.register(Scheme)
class SchemeAdmin(ImportExportModelAdmin):
    resource_class = SchemeResource
    list_display = ('title', 'department', 'introduced_on', 'valid_upto', 'funding_pattern')
    search_fields = ('title', 'description')
    list_filter = ('department', 'introduced_on', 'valid_upto', 'funding_pattern')
