from django.db import models
from django.utils import timezone
import pytz
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
import uuid
from datetime import timedelta



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
    
# Existing models
class State(TimeStampedModel):
    state_name = models.CharField(max_length=255, null=True, blank=True)

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
    
    def get_group(self):
        department_name = self.department_name.lower()
        
        
        EDUCATION_KEYWORDS = [
            'education',
            'scholarship',
            'training',
            'student',
            'care and protection',
            'vocational'
        ]
        AGRICULTURE_KEYWORDS = [
            'agriculture',
            'farmer',
            'soil',
            'water',
            'conservation'
        ]
        HEALTH_KEYWORDS = [
            'health',
            'medical',
            'family welfare'
        ]
        SOCIAL_WELFARE_KEYWORDS = [
            'social welfare',
            'women and child development',
            'child development',
            'welfare of sc/st/obc & minority',
            'social'
        ]
        INFRASTRUCTURE_KEYWORDS = [
            'public works',
            'urban development',
            'housing',
            'rural development'
        ]
        EMPLOYMENT_KEYWORDS = [
            'employment',
            'labour',
            'skill development',
            'entrepreneurship'
        ]
        OTHER_KEYWORDS = [
            'tourism',
            'culture',
            'information technology',
            'science and technology'
        ]

        # Check for each group and return the appropriate classification
        if any(keyword in department_name for keyword in HEALTH_KEYWORDS):
            return "Health"
        elif any(keyword in department_name for keyword in SOCIAL_WELFARE_KEYWORDS):
            return "Social Welfare"
        elif any(keyword in department_name for keyword in INFRASTRUCTURE_KEYWORDS):
            return "Infrastructure"
        elif any(keyword in department_name for keyword in EMPLOYMENT_KEYWORDS):
            return "Employment"
        elif any(keyword in department_name for keyword in AGRICULTURE_KEYWORDS):
            return "Agriculture"
        elif any(keyword in department_name for keyword in EDUCATION_KEYWORDS):
            return "Education"
        elif any(keyword in department_name for keyword in OTHER_KEYWORDS):
            return "Other"
        else:
            return "Unclassified"

class Organisation(TimeStampedModel):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='organisations', null=True, blank=True)
    organisation_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        ordering = ['organisation_name']
    
    def __str__(self):
        return self.organisation_name
    
class Tag(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']

    def __str__(self):
        return self.name


     

class Scheme(TimeStampedModel):
    title = models.TextField(null = True, blank = True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='schemes', null=True, blank=True)
    introduced_on = models.TextField(null = True, blank = True)
    valid_upto = models.TextField(null = True, blank = True)
    funding_pattern = models.CharField(max_length=255, null = True, blank = True)
    description = models.TextField(null = True, blank = True)
    scheme_link = models.URLField(null = True, blank = True)
    beneficiaries = models.ManyToManyField('Beneficiary', related_name='schemes', through='SchemeBeneficiary')
    documents = models.ManyToManyField('Document', related_name='schemes', through='SchemeDocument')
    sponsors = models.ManyToManyField('Sponsor', related_name='schemes', through='SchemeSponsor')
    tags = models.ManyToManyField('Tag', related_name='schemes', blank=True)  # Add this line
    benefits = models.ManyToManyField('Benefit', related_name='schemes', blank=True)

    class Meta:
        verbose_name = "Scheme"
        verbose_name_plural = "Schemes"
        ordering = ['introduced_on']

    def __str__(self):
        return self.title
    
class Benefit(TimeStampedModel):
    benefit_type = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Benefit"
        verbose_name_plural = "Benefits"
        ordering = ['benefit_type']

    def __str__(self):
        return self.benefit_type

class Beneficiary(TimeStampedModel):
    beneficiary_type = models.CharField(max_length=255, null=True, blank=True)

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



# DOUBT BELOW
class Criteria(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='criteria', null=True, blank=True)
    description = models.TextField(null = True, blank = True)
    value = models.TextField(null = True, blank = True)
    criteria_data = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Criteria"
        verbose_name_plural = "Criteria"
        ordering = ['description']

    def __str__(self):
        return self.description if self.description else "Unnamed Criteria"

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
    document_name = models.CharField(max_length=255, null=True, blank=True)
    requirements = models.TextField(null=True, blank=True)

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
    sponsor_type = models.CharField(max_length=255, null=True, blank=True)

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
    state_name = models.CharField(max_length=255, null=True, blank=True)

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
    funding_pattern = models.CharField(max_length=255, null=True, blank=True)
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
    benefit_type = models.CharField(max_length=255, null=True, blank=True)

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
    document_name = models.CharField(max_length=255, null=True, blank=True)

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
    sponsor_type = models.CharField(max_length=255, null=True, blank=True)

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

def default_verification_token_expiry():
    return timezone.now() + timedelta(days=1)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    CATEGORY_CHOICES = [
        ('General', 'General'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
        
    ]

    STATE_CHOICES = [
        ('Andhra Pradesh', 'Andhra Pradesh'),
        ('Arunachal Pradesh', 'Arunachal Pradesh'),
        ('Assam', 'Assam'),
        ('Bihar', 'Bihar'),
        ('Chhattisgarh', 'Chhattisgarh'),
        ('Goa', 'Goa'),
        ('Gujarat', 'Gujarat'),
        ('Haryana', 'Haryana'),
        ('Himachal Pradesh', 'Himachal Pradesh'),
        ('Jharkhand', 'Jharkhand'),
        ('Karnataka', 'Karnataka'),
        ('Kerala', 'Kerala'),
        ('Madhya Pradesh', 'Madhya Pradesh'),
        ('Maharashtra', 'Maharashtra'),
        ('Manipur', 'Manipur'),
        ('Meghalaya', 'Meghalaya'),
        ('Mizoram', 'Mizoram'),
        ('Nagaland', 'Nagaland'),
        ('Odisha', 'Odisha'),
        ('Punjab', 'Punjab'),
        ('Rajasthan', 'Rajasthan'),
        ('Sikkim', 'Sikkim'),
        ('Tamil Nadu', 'Tamil Nadu'),
        ('Telangana', 'Telangana'),
        ('Tripura', 'Tripura'),
        ('Uttar Pradesh', 'Uttar Pradesh'),
        ('Uttarakhand', 'Uttarakhand'),
        ('West Bengal', 'West Bengal'),
        
    ]
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    saved_schemes = models.ManyToManyField('Scheme', related_name='saved_by_users')
    # DETAILS BELOW
    name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    income = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    education = models.CharField(max_length=100, choices=[('None', 'None'), ('High School', 'High School'), ('Undergraduate', 'Undergraduate'), ('Postgraduate', 'Postgraduate'), ('Doctoral', 'Doctoral'),('Pre-primary', 'Pre-primary'), ('Secondary', 'Secondary'), ('Higher Secondary', 'Higher Secondary'), ('Diploma/Certification', 'Diploma/Certification')], blank=True, null=True)
    employment_status = models.CharField(max_length=100, choices=[('Employed', 'Employed'), ('Self-employed', 'Business'), ('Unemployed', 'Unemployed')], blank=True, null=True)
    government_employee = models.BooleanField(default=False)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)
    minority = models.BooleanField(default=False)
    state_of_residence = models.CharField(max_length=50, choices=STATE_CHOICES, blank=True, null=True)
    disability = models.BooleanField(default=False)
    bpl_card_holder = models.CharField(max_length=255, default = "NO")

    is_email_verified = models.BooleanField(default=False)
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username
    
# BANNER BELOW
    

class Banner(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='banners/',blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    

User = get_user_model()

class SavedFilter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    criteria = models.JSONField()  # Store filter criteria as JSON

    def __str__(self):
        return f"{self.name} ({self.user.username})"
