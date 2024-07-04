from django.db import models
from django.utils import timezone
import pytz

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set on creation
            tz = pytz.timezone('Asia/Kolkata')
            now = timezone.now()
            now = timezone.localtime(now, tz)
            self.created_at = now
        super().save(*args, **kwargs)

class State(TimeStampedModel):
    state_name = models.CharField(max_length=255, default="Tamil Nadu")

    class Meta:
        verbose_name = "State"
        verbose_name_plural = "States"
        ordering = ['state_name']
    def __str__(self):
        return self.state_name

class Department(TimeStampedModel):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='departments', null=True, blank=True)
    department_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ['department_name']

    def __str__(self):
        return self.department_name

class Organisation(TimeStampedModel):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='organisations', null=True, blank=True)
    organisation_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        ordering = ['organisation_name']
    
    def __str__(self):
        return self.organisation_name

class Scheme(TimeStampedModel):
    title = models.TextField(null = True, blank = True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='schemes', null=True, blank=True)
    introduced_on = models.DateTimeField(null = True, blank = True)
    valid_upto = models.DateTimeField(null = True, blank = True)
    funding_pattern = models.CharField(max_length=255, default="State")
    description = models.TextField(null = True, blank = True)
    scheme_link = models.URLField(null = True, blank = True)
    beneficiaries = models.ManyToManyField('Beneficiary', related_name='schemes', through='SchemeBeneficiary')
    documents = models.ManyToManyField('Document', related_name='schemes', through='SchemeDocument')
    sponsors = models.ManyToManyField('Sponsor', related_name='schemes', through='SchemeSponsor')

    class Meta:
        verbose_name = "Scheme"
        verbose_name_plural = "Schemes"
        ordering = ['introduced_on']

    def __str__(self):
        return self.title

class Beneficiary(TimeStampedModel):
    beneficiary_type = models.CharField(max_length=255, default="SC/ST")

    class Meta:
        verbose_name = "Beneficiary"
        verbose_name_plural = "Beneficiaries"
        ordering = ['beneficiary_type']
    
    def __str__(self):
        return self.beneficiary_type

class SchemeBeneficiary(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='scheme_beneficiaries')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='beneficiary_schemes')

    class Meta:
        verbose_name = "Scheme Beneficiary"
        verbose_name_plural = "Scheme Beneficiaries"
        ordering = ['scheme', 'beneficiary']

    

class Benefit(TimeStampedModel):
    benefit_type = models.CharField(max_length=255, default="Grant")

    class Meta:
        verbose_name = "Benefit"
        verbose_name_plural = "Benefits"
        ordering = ['benefit_type']

    def __str__(self):
        return self.benefit_type


# DOUBT BELOW
class Criteria(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='criteria', null=True, blank=True)
    description = models.TextField(null = True, blank = True)
    value = models.TextField(null = True, blank = True)

    class Meta:
        verbose_name = "Criteria"
        verbose_name_plural = "Criteria"
        ordering = ['description']

    def __str__(self):
        return self.description

class Procedure(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='procedures', null=True, blank=True)
    step_description = models.TextField(null = True, blank = True)

    class Meta:
        verbose_name = "Procedure"
        verbose_name_plural = "Procedures"
        ordering = ['scheme']

    def __str__(self):
        return self.step_description

class Document(TimeStampedModel):
    document_name = models.CharField(max_length=255, default="Aadhar Card")

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['document_name']

    def __str__(self):
        return self.document_name

class SchemeDocument(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='scheme_documents')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='document_schemes')

    class Meta:
        verbose_name = "Scheme Document"
        verbose_name_plural = "Scheme Documents"
        ordering = ['scheme', 'document']

class Sponsor(TimeStampedModel):
    sponsor_type = models.CharField(max_length=255, default="State")

    class Meta:
        verbose_name = "Sponsor"
        verbose_name_plural = "Sponsors"
        ordering = ['sponsor_type']

    def __str__(self):
        return self.sponsor_type

class SchemeSponsor(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='scheme_sponsors')
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name='sponsor_schemes')

    class Meta:
        verbose_name = "Scheme Sponsor"
        verbose_name_plural = "Scheme Sponsors"
        ordering = ['scheme', 'sponsor']


# Temporary models for new data

    
class TempState(TimeStampedModel):
    state_name = models.CharField(max_length=255, default="Tamil Nadu")

    class Meta:
        abstract = True

    def __str__(self):
        return self.state_name

class TempDepartment(TimeStampedModel):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='temp_departments', null=True, blank=True)
    department_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.department_name

class TempOrganisation(TimeStampedModel):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='temp_organisations', null=True, blank=True)
    organisation_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.organisation_name

class TempScheme(TimeStampedModel):
    title = models.TextField(null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='temp_schemes', null=True, blank=True)
    introduced_on = models.DateTimeField(null=True, blank=True)
    valid_upto = models.DateTimeField(null=True, blank=True)
    funding_pattern = models.CharField(max_length=255, default="State")
    description = models.TextField(null=True, blank=True)
    scheme_link = models.URLField(null=True, blank=True)
    beneficiaries = models.ManyToManyField('Beneficiary', related_name='temp_schemes', through='TempSchemeBeneficiary')
    documents = models.ManyToManyField('Document', related_name='temp_schemes', through='TempSchemeDocument')
    sponsors = models.ManyToManyField('Sponsor', related_name='temp_schemes', through='TempSchemeSponsor')

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

class TempSchemeBeneficiary(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='temp_scheme_beneficiaries')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='temp_beneficiary_schemes')

    class Meta:
        abstract = True

class TempBenefit(TimeStampedModel):
    benefit_type = models.CharField(max_length=255, default="Grant")

    class Meta:
        abstract = True

    def __str__(self):
        return self.benefit_type

class TempCriteria(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='temp_criteria', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    value = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.description

class TempProcedure(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='temp_procedures', null=True, blank=True)
    step_description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.step_description

class TempDocument(TimeStampedModel):
    document_name = models.CharField(max_length=255, default="Aadhar Card")

    class Meta:
        abstract = True

    def __str__(self):
        return self.document_name

class TempSchemeDocument(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='temp_scheme_documents')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='temp_document_schemes')

    class Meta:
        abstract = True

class TempSponsor(TimeStampedModel):
    sponsor_type = models.CharField(max_length=255, default="State")

    class Meta:
        abstract = True

    def __str__(self):
        return self.sponsor_type

class TempSchemeSponsor(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='temp_scheme_sponsors')
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name='temp_sponsor_schemes')

    class Meta:
        abstract = True



# USER REGISTRATION START
        

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username
