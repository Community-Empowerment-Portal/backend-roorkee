from django.db import models
from django.utils import timezone
import pytz
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
import uuid
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
import re
from dirtyfields import DirtyFieldsMixin
from orderable.models import Orderable
from PIL import Image, UnidentifiedImageError
from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_MEDIA_STORAGE_BUCKET_NAME
    location = 'media'
    file_overwrite = False


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

class Organization(models.Model):
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tenant" 
        verbose_name_plural = "Tenants"

    def __str__(self):
        return self.name
    
# Existing models
class State(TimeStampedModel):
    state_name = models.CharField(max_length=255, null=False, blank=False, unique = True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    def clean(self):
        if not self.state_name.strip():  # Disallow empty or whitespace-only names
            raise ValidationError("State name cannot be empty or whitespace.")
        if re.search(r'\d', self.state_name):  # Check if state_name contains any digit
            raise ValidationError("State name cannot contain numeric characters.")
        
    def save(self, *args, **kwargs):
        # Strip whitespace before saving
        if self.state_name is not None:
            self.state_name = self.state_name.strip().title()
        super().save(*args, **kwargs)

        if self.is_active:
            self.departments.update(is_active=True)
            Scheme.objects.filter(department__state=self).update(is_active=True)

        if not self.is_active:
            self.departments.update(is_active=False)
            Scheme.objects.filter(department__state=self).update(is_active=False)

    class Meta:
        verbose_name = "State"
        verbose_name_plural = "States"
        ordering = ['state_name']
    def __str__(self):
        return self.state_name or "N/A"



class Department(TimeStampedModel):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='departments', null=False, blank=False)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    department_name = models.CharField(max_length=255, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    # def clean(self):
    #     if re.search(r'\d', self.department_name):
    #         raise ValidationError("Department name cannot contain numeric characters.")
    def save(self, *args, **kwargs):
        from communityEmpowerment.models import Scheme
        super().save(*args, **kwargs)
        if self.is_active:
            Scheme.objects.filter(department=self).update(is_active=True)

        if not self.is_active:
            from communityEmpowerment.models import Scheme
            Scheme.objects.filter(department=self).update(is_active=False)
    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ['department_name']

    def __str__(self):
        return self.department_name or "N/A"
    
    def get_group(self):
        department_name = self.department_name.lower() if self.department_name else ""

        
        
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
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    organisation_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        ordering = ['organisation_name']
    
    def __str__(self):
        return self.organisation_name or "N/A"
    
class Tag(DirtyFieldsMixin, TimeStampedModel):
    CATEGORY_CHOICES = [
    ("scholarship", "Scholarship"),
    ("job", "Job Opening"),
    ("govt_job", "Government Job"),
    ("private_job", "Private Job"),
    ("internship", "Internship"),
    ("skill_based_job", "Skill-Based Job"),
    ("defense_job", "Defense & Police Job"),
    ("sc", "Scheduled Caste (SC)"),
    ("st", "Scheduled Tribe (ST)"),
    ("obc", "Other Backward Classes (OBC)"),
    ("minority", "Minority Community"),
    ("general", "General"),
    ("financial_assistance", "Financial Assistance & Subsidies"),
    ("women", "Women-Centric Schemes"),
    ("agriculture", "Agriculture & Farmers"),
    ("senior_citizen", "Senior Citizens & Pension"),
    ("disability", "Disability & Special Needs"),
    ("business", "Startups & Business Development"),
    ("education", "Education & Training"),
    ("health", "Health & Insurance"),
    ("housing", "Housing & Infrastructure"),
    ("youth_skill", "Youth & Skill Development"),
    ("transportation", "Transportation & Connectivity"),
    ("environment", "Environment & Conservation"),
    ("digital_services", "Digital Services & E-Governance"),
    ("social_welfare", "Social Welfare & Community Support"),
    ("rural_development", "Rural Development"),
    ("urban_development", "Urban Development & Smart Cities"),
    ("international_relations", "International Relations & Aid"),
    ("technology_innovation", "Technology & Innovation"),
    ("legal", "Legal Aid & Rights"),
    ("food_security", "Food Security & Nutrition"),
    ("disaster_management", "Disaster Management & Relief"),
    ("climate_action", "Climate Action & Sustainability"),
    ("gender_equality", "Gender Equality & Inclusion"),
    ("child_welfare", "Child Welfare & Protection"),
    ("consumer_protection", "Consumer Protection & Rights"),
    ("cultural_preservation", "Cultural Preservation & Heritage"),
    ("research_and_development", "Research & Development"),
    ("tourism", "Tourism & Pilgrimage"),
    ("festival", "Festivals & Cultural Events"),
    ("administrative", "Administrative & Governance"),
    ("infrastructure", "Infrastructure Development"),
    ("religious", "Religious & Spiritual"),
    ("media", "Media & Publicity"),
    ("livestock", "Livestock & Animal Husbandry"),
    ("fisheries", "Fisheries & Aquaculture"),
    ("awards", "Awards & Recognition"),
    ("poverty_alleviation", "Poverty Alleviation"),
    ("water_management", "Water Management & Irrigation"),
    ("waste_management", "Waste Management & Sanitation"),
    ("energy", "Energy & Electrification"),
    ("land_management", "Land Management & Ownership"),
    ("sports", "Sports & Fitness"),
    ("skill_development", "Skill Development & Vocational Training"),
    ("public_services", "Public Services & Utilities"),
    ("crime_prevention", "Crime Prevention & Safety"),
    ("local_governance", "Local Governance & Panchayat"),
    ("manufacturing", "Manufacturing & Industries"),
    ("marketing", "Marketing & Trade"),
    ("education_infrastructure", "Education Infrastructure"),
    ("health_infrastructure", "Health Infrastructure"),
    ("social_reform", "Social Reform & Inclusion"),
    ("economic_development", "Economic Development"),
    ("emergency_services", "Emergency Services"),
    ("cultural_activities", "Cultural Activities & Arts"),
    ("training", "Training & Capacity Building"),
    ("compensation", "Compensation & Relief"),
    ("rehabilitation", "Rehabilitation & Resettlement"),
    ("public_distribution", "Public Distribution & Ration"),
    ("agricultural_inputs", "Agricultural Inputs & Support"),
    ("rural_infrastructure", "Rural Infrastructure"),
    ("urban_infrastructure", "Urban Infrastructure"),
    ("traditional_crafts", "Traditional Crafts & Handicrafts"),
    ("financial_inclusion", "Financial Inclusion"),
    ("digital_infrastructure", "Digital Infrastructure"),
    ("healthcare_services", "Healthcare Services"),
    ("education_support", "Education Support & Resources"),
    ("social_security", "Social Security & Pensions"),
    ("community_development", "Community Development"),
    ("cultural_heritage", "Cultural Heritage"),
    ("environmental_conservation", "Environmental Conservation"),
    ("disability_support", "Disability Support & Services"),
    ("agricultural_development", "Agricultural Development"),
    ("rural_livelihood", "Rural Livelihoods"),
    ("urban_livelihood", "Urban Livelihoods"),
    ("tourism_promotion", "Tourism Promotion"),
    ("festival_management", "Festival Management"),
    ("public_safety", "Public Safety"),
    ("health_promotion", "Health Promotion & Awareness"),
    ("education_promotion", "Education Promotion & Literacy"),
    ("social_inclusion", "Social Inclusion"),
    ("economic_empowerment", "Economic Empowerment"),
    ("disaster_relief", "Disaster Relief"),
    ("child_protection", "Child Protection"),
    ("women_empowerment", "Women Empowerment"),
    ("legal_support", "Legal Support & Services"),
    ("agricultural_marketing", "Agricultural Marketing"),
    ("rural_electrification", "Rural Electrification"),
    ("urban_electrification", "Urban Electrification"),
    ("livestock_development", "Livestock Development"),
    ("fisheries_development", "Fisheries Development"),
    ("cultural_promotion", "Cultural Promotion"),
    ("tourism_development", "Tourism Development"),
    ("public_health", "Public Health"),
    ("social_services", "Social Services"),
    ("infrastructure_development", "Infrastructure Development"),
    ("economic_support", "Economic Support"),
    ("community_welfare", "Community Welfare"),
    ("environmental_sustainability", "Environmental Sustainability"),
    ("agricultural_innovation", "Agricultural Innovation"),
    ("digital_governance", "Digital Governance"),
    ("public_welfare", "Public Welfare"),
    ("healthcare_infrastructure", "Healthcare Infrastructure"),
    ("education_institutions", "Education Institutions"),
    ("rural_welfare", "Rural Welfare"),
    ("urban_welfare", "Urban Welfare"),
    ("cultural_institutions", "Cultural Institutions"),
    ("disability_welfare", "Disability Welfare"),
    ("agriculture_support", "Agriculture Support"),
    ("livelihood_support", "Livelihood Support"),
    ("public_infrastructure", "Public Infrastructure"),
    ("social_development", "Social Development"),
    ("economic_inclusion", "Economic Inclusion"),
    ("healthcare_support", "Healthcare Support"),
    ("education_welfare", "Education Welfare"),
    ("community_support", "Community Support"),
    ("cultural_support", "Cultural Support"),
    ("environmental_support", "Environmental Support"),
    ("disability_services", "Disability Services"),
    ("agricultural_services", "Agricultural Services"),
    ("livelihood_services", "Livelihood Services"),
    ("infrastructure_services", "Infrastructure Services"),
    ("public_support", "Public Support"),
    ("healthcare_welfare", "Healthcare Welfare"),
    ("education_services", "Education Services"),
    ("community_services", "Community Services"),
    ("cultural_services", "Cultural Services"),
    ("environmental_services", "Environmental Services"),
    ("disability_inclusion", "Disability Inclusion"),
    ("agricultural_welfare", "Agricultural Welfare"),
    ("livelihood_welfare", "Livelihood Welfare"),
    ("infrastructure_welfare", "Infrastructure Welfare"),
    ("public_welfare_services", "Public Welfare Services"),
    ("healthcare_promotion", "Healthcare Promotion"),
    ("education_inclusion", "Education Inclusion"),
    ("community_inclusion", "Community Inclusion"),
    ("cultural_inclusion", "Cultural Inclusion"),
    ("environmental_inclusion", "Environmental Inclusion"),
    ("state_specific", "State-Specific Schemes"),
    ]

    name = models.CharField(max_length=255, unique=True)
    weight = models.FloatField(default=1.0)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="general")
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']

    def match_keywords(self, text, keywords):
        for kw in keywords:
            kw = kw.lower()
            if kw in ["sc", "st", "obc"]:
                if re.search(rf'\b{re.escape(kw)}\b', text):
                    return True
            else:
                if kw in text:
                    return True
        return False

    def save(self, *args, **kwargs):
        # Existing categories from the example
        scholarship_keywords = [
            "scholarship", "fellowship", "grant", "stipend", "tuition support", "fee waiver", "educational aid",
            "Bursary", "Compulsory Fee Reimbursement", "Fee Exemption", "Fee Reimbursement", "Merit-based",
            "Merit-cum-Means", "Post Matric", "Post-Matric", "Pre Matric", "Pre-Matric", "Pre-matric",
            "Prematric", "Tuition Fee", "Tuition Fees", "Means-cum-Merit", "Student Performance",
            "Meritorious Students", "Financial Aid", "Monetary Incentive"
        ]

        job_keywords = [
            "job", "employment", "recruitment", "vacancy", "career", "job fair", "placement", "hiring",
            "Civil Service", "Journalism", "Journalist", "Journalists", "Advocates", "Legal practice"
        ]

        govt_job_keywords = [
            "govt job", "government recruitment", "public sector", "sarkari naukri", "upsc", "ssc", "psu", "rrb",
            "IAS", "IPS", "IRS", "Government Service", "MPPSC"
        ]

        private_job_keywords = [
            "private job", "corporate hiring", "MNC recruitment", "industry placement"
        ]

        internship_keywords = [
            "internship", "apprentice", "trainee", "training program", "summer training", "industrial training"
        ]

        skill_job_keywords = [
            "freelance", "gig work", "self-employment", "contract job", "daily wage", "micro job",
            "Carpentry", "Electrician", "Fitting", "Masonry", "Motor Mechanic", "Plumbing", "Tailoring",
            "Turning", "Welding", "Craft", "Crafts", "Handicrafts", "Leather", "Embroidery"
        ]

        defense_job_keywords = [
            "army recruitment", "navy job", "air force", "police hiring", "defense", "paramilitary", "bsf", "cisf",
            "Military", "Ex-Servicemen", "Veterans"
        ]

        sc_keywords = [
            "sc", "scheduled caste", "dalit", "safai karamchari", "manual scavenger",
            "Scheduled Caste", "Adi Dravidar", "Charmakar", "Charmakar Community", "Valmiki Samaj",
            "Navbouddha", "SCSP", "SCs", "SCs/STs", "Caste Discrimination", "Untouchability",
            "Untouchability Eradication", "Prevention of Atrocities", "Prevention of Atrocities Act",
            "Atrocities", "Atrocity", "Victims of Atrocities"
        ]

        st_keywords = [
            "st", "scheduled tribe", "tribal", "vanvasi", "aadivasi",
            "Scheduled Tribe", "STs", "SCs/STs", "Vimukta Jatis", "Nomadic Tribes", "DNT", "Indigenous Population"
        ]

        obc_keywords = [
            "obc", "other backward class", "backward class", "bc", "most backward class",
            "OBC", "VJNT", "Backward Students", "OEC"
        ]

        minority_keywords = [
            "minority", "muslim", "christian", "sikh", "buddhist", "jain", "parsi", "zoroastrian",
            "Minorities", "National Minorities", "Hindu", "Hinduism"
        ]

        financial_keywords = [
            "loan", "subsidy", "financial assistance", "funding", "support", "pension", "microfinance", "credit",
            "Financial Incentive", "Monetary Relief", "Cash Prize", "Cash", "Assistance", "Financial Inclusion",
            "Financial Viability", "Financial boost", "Interest-Free", "Interest-free", "Margin Money",
            "Contributory Scheme", "Debt Relief Scheme", "One Time Settlement", "Deposit Accounts",
            "Share Capital", "Capital", "Institutional finance", "Incentive Scheme", "Incentives",
            "Central Assistance", "Special Assistance", "Financial Aid", "Compensation", "Relief",
            "Marriage Assistance", "Marriage Incentive", "Calf Incentive", "One-time Incentive",
            "One-time payment", "Maintenance Allowance", "Allowance", "Arrears", "Tax Reimbursement",
            "Stamp Duty", "50:50 Cost Sharing", "Budget allocation"
        ]

        women_keywords = [
            "women", "female", "girl child", "mahila", "nari", "pregnant", "lactating", "mother", "widow",
            "working women", "Adolescent Girls", "Adolescent girls", "Girls", "Daughters", "Housewives",
            "Maternity", "Maternity Benefit", "Deserted", "Destitute", "IGNWPS", "Marriage",
            "Inter-caste Marriage", "Intercaste Marriage", "Mass Marriage", "Collective Wedding",
            "Empowerment", "Economic empowerment", "Kishori Balika", "Pregnant Women", "Safe Motherhood"
        ]

        agriculture_keywords = [
            "farmer", "agriculture", "kisaan", "crop", "irrigation", "fertilizer", "soil", "farm",
            "Agricultural Marketing", "Agro-based industries", "Dairy", "Dairy Development",
            "Animal Husbandry", "Livestock", "Livestock Development", "Poultry", "Piggery", "Goatery",
            "Fisheries", "Fish Feed", "Fish Market", "Cattle rearing", "Cattle herders", "Milk Production",
            "Seed", "Seed Certification", "Seed Multiplication", "Seed Production", "Seed Testing",
            "Seeds", "Paddy Seeds", "Minikit", "Bio Agents", "Bio Pesticides", "Pesticides",
            "Plant Protection", "Plant Protection Equipment", "Planting Material", "Cultivation Methods",
            "Green Fodder Cultivation", "Fodder Development", "Compost", "Biogas", "Biomass Briquetting",
            "Organic Waste", "Kitchen Garden", "Land Development", "Land terracing", "Land Management",
            "Ponds", "Water Management", "Irrigation", "PMKSY", "PM-KISAN", "Pradhan Mantri Kisan Samman Nidhi",
            "Pradhan Mantri Fasal Bima Yojana", "PMFBY", "Paddy Reapers", "Power Tillers",
            "Mechanization", "Cold Storage", "Market Access", "Market Information", "Marketing",
            "Oilseeds", "Pulses", "Maize", "Rice", "Wheat", "Grafting", "Eri Silk", "Silk Reeling",
            "Rubber cultivation", "Tea cultivation", "Farm", "Farmers", "Fertilizer", "Rhizobium",
            "Iodized Salt Distribution", "Subsidized Salt", "Subsidized Food Grains", "Antyodaya Anna Yojana",
            "Food Grains", "Procurement", "Public Distribution System", "PDS", "RKVY", "Recommended Package of Practices"
        ]

        senior_keywords = [
            "senior citizen", "pension", "old age", "vridh", "elderly", "retirement", "superannuation",
            "IGNOAPS", "Old Age"
        ]

        disability_keywords = [
            "disability", "divyang", "handicapped", "pwd", "special needs", "differently abled", "blind",
            "hearing impaired", "Disabled", "Disabled Persons", "Disabled Students", "Differently-abled",
            "Cerebral Palsy", "Mentally Challenged", "Motorized Tricycle", "Assistive Devices",
            "Viklangta Praman Patra", "Dwarf", "NHFDC", "Persons with Disabilities", "Physical Disability",
            "Mental Disability", "Special Needs"
        ]

        business_keywords = [
            "startup", "business", "entrepreneur", "MSME", "enterprise", "self-employment", "new venture",
            "industrial unit", "Cottage Industries", "Cooperative Societies", "Handloom", "Handloom Weavers",
            "Textile", "Textiles", "Textile Parks", "Industrial Estates", "Industries", "Industry",
            "Manufacturing", "Manufacturing Industries", "Manufacturing Sector", "Agri-tech",
            "Meditech", "Self Help Group", "Self Help Groups", "Self Reliance", "Self-Sufficiency",
            "Self-reliance", "Micro", "Small", "Medium", "SIPCOT", "TANSidCO Industrial Estates",
            "TIIC", "UYEGP", "NEF scheme", "NSKFDC", "Stand-Up India", "Market", "Economic Development",
            "Economic Upliftment", "Economic growth", "Investment", "Financial Viability", "Industrial Workers"
        ]

        education_keywords = [
            "education", "training", "10+2", "coaching", "school", "college", "university", "exam",
            "online course", "learning", "Class 10", "Class 11", "Class 12", "Class 6 to 8", "Class 9",
            "Classes 6 to 8", "10th Standard", "11th Standard", "12th Standard", "12th pass",
            "Matriculation", "Higher Secondary", "Post Graduate", "Post-Matriculation", "Post-Matric Courses",
            "Pre-Matric Courses", "Diploma", "Certificate", "Certificate Programme", "Certification",
            "Professional Courses", "Technical Courses", "Short Term Courses", "Evening Courses",
            "Correspondence Courses", "Polytechnic", "ITI", "NCVT", "Engineering", "Engineering Entrance",
            "JEE", "GUJCET", "NEET", "Architecture", "PhD", "MPhil", "Study Abroad", "Foreign Study",
            "Coaching", "Free Textbooks", "Text Books", "Book Bank", "Book Distribution", "Book-bank Facilities",
            "Books", "Library", "Library Management", "Library Award Scheme", "Best Library Award",
            "Reference Books", "Stationary", "Stationery", "Drawing", "Drawing Materials", "Calculators",
            "Computer", "Laptop", "Bicycle Distribution", "Free Travel", "Hostel", "Hostel Facilities",
            "Hostels", "Girls Hostel", "Boarding", "Residential Facilities", "Residential Facility",
            "Merit", "Merit Awards", "Awards", "Awards and Recognition", "Competition", "Competitive Capacity",
            "Cultural Talent Search", "Essay writing", "Handwriting", "Poem Writing", "Science Seminars",
            "Study Tour", "Exposure Visit", "Sanskrit", "Hindi", "Konkani", "Konkani Language", "Marathi",
            "Language Skill Program", "Sarva Shiksha Abhiyan", "RTE", "RTE Act", "Mid Day Meal", "MDM",
            "POSHAN Abhiyaan", "Literacy", "Education", "Students", "Student", "Backward Students",
            "AICTE", "NIFT", "IIM", "NLU", "Gujarat Vidhyapeeth", "Universities", "Academic Excellence",
            "Concessions", "Admission", "Enrolment"
        ]

        health_keywords = [
            "health", "insurance", "medical", "ayushman", "treatment", "hospital", "disease", "wellness",
            "nutrition", "Anemia", "Cancer", "HIV/AIDS prevention", "Tuberculosis control", "TB",
            "TB patients", "Rabies", "Rabies Control", "Free diagnosis", "Free service", "Mediclaim Scheme",
            "Maternity", "Maternity Benefit", "Family Planning", "Sterilization", "IFA supplementation",
            "Childcare", "Children", "ICDS", "Anganwadi Workers", "Anganwadi Helpers", "ASHA",
            "AWC", "Day Care", "Daycare", "Crèche", "Vaccination", "Veterinary Services", "Health Services",
            "Emergency Services", "Ambulance service", "Fire Fighting Services", "Fire Safety",
            "Cleanliness", "Hygienic", "Sanitation", "Drinking Water", "Water & Sewage Management",
            "Sewerage", "Solid and Liquid Waste Management", "Waste Management", "Kitchen Waste",
            "Organic Waste", "Stray Dog Management", "Stray Dogs", "Nutrition", "Food", "Food Security",
            "Mid Day Meal", "Akshaya Patra", "Breakfast", "Subsidized Food Grains", "Antyodaya Anna Yojana",
            "Public Distribution System", "POSHAN Abhiyaan", "Health Awareness", "Awareness Campaign",
            "Awareness Programmes", "Awareness Programs", "Health Camps", "Camps"
        ]

        housing_keywords = [
            "housing", "home", "pradhan mantri awas", "rental", "urban housing", "slum", "shelter",
            "infrastructure", "PMAY", "House Site", "Construction of New Houses", "Repairs of Existing Houses",
            "Reconstruction of Existing Houses", "Building", "Building Construction", "Accommodation",
            "Government Buildings", "Guest House", "Community Halls", "Conference Hall", "Dr.Ambedkar Bhavan",
            "Ambedkar Bhavan", "Babu Jagjiban Ram Chatrabas Yojana", "Burial Ground", "Cremation Ground",
            "Funeral Expenses", "Funeral Rites", "Basic amenities", "Civic Amenities", "Roads-Plan",
            "Road Construction", "Road Connectivity", "Rural Roads", "PMGSY", "Drainage", "Sewerage",
            "Electricity", "Power Supply", "Power Tariff", "Broadband", "BharatNet", "City Wi-Fi",
            "CCTVs", "Public Works", "Land Purchase Assistance", "Land Ownership", "Residential certificates",
            "Economically Weaker Sections", "EWS", "Low Income", "LIG", "BPL", "Below Poverty Line",
            "BPL families", "Urban Areas", "Urban Development", "Infrastructure Development"
        ]

        youth_keywords = [
            "skill development", "training", "youth", "vocational", "NSDC", "kaushal", "apprenticeship",
            "capacity building", "Skill India", "Skill upgradation", "Skills Development", "SANKALP",
            "Yuva Srujan Puraskar", "Youth", "Cultural Talent Search", "Competitive Capacity",
            "Sports", "Games", "Creativity", "Cultural Activities", "Dance", "Drama", "Painting",
            "Cultural Shows", "Exhibition", "Exhibitions", "Festival/Exhibition", "Cultural Exchange",
            "Cultural Groups", "Cultural Institutions", "Talent Search", "Competitions", "Career Counseling",
            "Counseling", "Training Programs"
        ]

        transportation_keywords = [
            "transport", "transportation scheme", "road safety", "public transport", "metro", "bus service",
            "railway", "auto rickshaw", "Kadamba Buses", "Free Travel", "Bicycle Distribution",
            "Motorized Tricycle", "Electric Vehicles", "Road", "Road Construction", "Road Works",
            "Road Connectivity", "Rural Roads", "PMGSY", "State Plan Road Works", "Border Management",
            "Inter-State boundary", "Travel", "Tourism", "Pilgrimage", "Religious Tourism",
            "Directorate of Civil Aviation", "Air Hostess", "Logistics", "Transport Services"
        ]

        environment_keywords = [
            "environment", "climate change", "conservation", "pollution", "green energy", "eco-friendly",
            "sustainability", "carbon footprint", "Afforestation", "Forestry", "Public Forest",
            "Eco Tourism", "Green House Gas Emissions", "Green Investment", "Clean energy",
            "Renewable Energy", "Renewable Energy sources", "Biogas", "Biomass Briquetting",
            "Waste Management", "Solid and Liquid Waste Management", "Organic Waste", "Kitchen Waste",
            "Waste to Wealth", "Wastelands", "Water Management", "Watershed", "Desilting", "Ponds",
            "Ground Water Prospect Map", "Wildlife", "Wildlife damage", "Environmental Sustainability",
            "Ecological Balance", "Forest Produce", "Minor Forest Produce", "Forest Crimes", "Forest Officer",
            "Forest Department", "Wildlife Conservation", "Wild Animals", "National Park", "Tiger Foundation Society"
        ]

        digital_services_keywords = [
            "digital", "e-governance", "online services", "internet connectivity", "technology",
            "digital literacy", "digital payment", "smart city", "Aadhaar", "Aadhaar Based Attendance System",
            "Biometrics", "Online Portal", "Online submission of Application for Mobile Tower and OFC",
            "Electronic Service Delivery", "Digidhan Mission", "Common Service Centre (CSC)", "ICT",
            "IT", "ITES", "IT initiatives", "IT/ITeS Investment Promotion", "NKN", "JharNet",
            "SMS Gateway", "Video conferencing", "Geo Data base", "GIS", "WAMIS", "Digital Services",
            "BharatNet", "City Wi-Fi", "e-District", "e-MULAKAT", "e-Nagarik", "e-Office", "e-Procurement",
            "e-Service", "e-Service Platform", "eKalyan", "Payment Gateway", "UIDAI"
        ]

        social_welfare_keywords = [
            "social welfare", "welfare", "poverty alleviation", "social security", "NGO", "community service",
            "support program", "Social Development", "Social Inclusion", "Social Inequality", "Social Reform",
            "Social Remedies", "Social Upliftment", "Social incentive", "Socio-economic Development",
            "Poverty", "Poverty Line", "Poverty Upliftment", "Below Poverty Line", "BPL", "BPL families",
            "Economically Weaker Sections", "Marginalized", "Marginalized Communities", "Destitute",
            "Orphaned", "Care and Protection", "Family based care", "Foster Care", "Bonded Labour",
            "Unorganized Sector", "Unskilled Manual Work", "Cleaning Occupations", "Cleaning Workers",
            "Unclean Occupation", "Rehabilitation", "Relief and Rehabilitation", "NSAP", "National Social Assistance Programme",
            "IGNDPS", "IGNOAPS", "IGNWPS", "NFBS", "Community Development", "Advisory Committees",
            "Advisory Services", "Awareness", "Awareness Campaign", "Awareness Programmes", "Awareness Programs",
            "Social Service", "Human Resource Development", "Human resource development", "Social Assistance",
            "Special Component Plan", "Sub Plan", "TSP", "SCSP", "Social Capital", "Community Self-reliance",
            "Vulnerable Communities", "Victim Compensation", "Witness Protection"
        ]

        rural_development_keywords = [
            "rural development", "village", "panchayat", "rural infrastructure", "farmers' welfare",
            "water supply", "sanitation", "road development", "Rural", "Rural Labourers", "Rural Roads",
            "Rural Works Programme", "MGNREGA", "PMGSY", "Panchayat", "Panchayat Bhawan", "Local Area Development",
            "Community Development", "Rural Electrification", "Drinking Water", "Basic amenities",
            "Civic Amenities", "Drainage", "Sewerage", "Burial Ground", "Public Assets", "Land Development",
            "Land Management", "Desilting", "Ponds", "Water Management", "Watershed", "Area Development",
            "Village Development", "Gramin Vikas", "Sansad Adarsh Gram Yojana", "Rurban"
        ]

        urban_development_keywords = [
            "urban development", "city planning", "infrastructure", "housing for all", "urban slums",
            "urbanization", "smart cities", "metro development", "Urban", "Urban Areas", "City Wi-Fi",
            "Smart City", "Civic Amenities", "Public Works", "Sewerage", "Drainage", "Road Construction",
            "Urban Infrastructure", "Municipal Services"
        ]

        international_relations_keywords = [
            "international aid", "foreign scholarships", "diaspora", "NRIs", "global initiatives",
            "international collaboration", "International", "Overseas", "Foreign Study", "Study Abroad",
            "Cultural Exchange"
        ]

        technology_innovation_keywords = [
            "innovation", "tech innovation", "startups", "research and development", "artificial intelligence",
            "robotics", "machine learning", "Technology", "IT", "ITES", "IT initiatives", "IT/ITeS Investment Promotion",
            "STPI", "NSICTANSidCO Consortium", "Intellectual Property", "Modernisation", "Modernization",
            "Mechanization", "Agri-tech", "Meditech", "Electronic Service Delivery", "Digital Services",
            "Innovation", "Research", "ISO Certification"
        ]

        legal_keywords = [
            "legal aid", "free legal consultation", "law", "legal assistance", "human rights", "constitution",
            "rights", "justice", "Legal", "Special Courts", "Special Criminal Courts", "Judiciary",
            "Prevention of Atrocities Act", "Atrocities", "Atrocity", "Victims of Atrocities",
            "Witness Protection", "Legal Services", "Advocates", "Legal practice", "Regulation",
            "Policy", "Consumer Protection", "Consumer Rights"
        ]

        food_security_keywords = [
            "food security", "ration", "food assistance", "mid-day meal", "food subsidy", "PDS",
            "nutrition scheme", "food distribution", "Antyodaya Anna Yojana", "Subsidized Food Grains",
            "Subsidized Salt", "Public Distribution System", "Mid Day Meal", "Akshaya Patra",
            "Breakfast", "POSHAN Abhiyaan", "Food Grains", "Iodized Salt Distribution", "Food",
            "Nutrition", "Food Security"
        ]

        disaster_management_keywords = [
            "disaster relief", "disaster management", "flood relief", "earthquake aid", "cyclone relief",
            "drought relief", "natural calamities", "Disaster Mitigation", "Relief", "Relief and Rehabilitation",
            "Accident", "Injury", "Death Benefit", "Compensation", "Contingency scheme", "Emergency Services",
            "Fire Fighting Services", "Fire Safety", "Ambulance service", "Calamity Relief"
        ]

        climate_action_keywords = [
            "climate action", "carbon emissions", "global warming", "environmental protection",
            "green initiatives", "climate adaptation", "Green House Gas Emissions", "Green Investment",
            "Clean energy", "Renewable Energy", "Renewable Energy sources", "Afforestation", "Forestry",
            "Eco Tourism", "Waste Management", "Solid and Liquid Waste Management", "Waste to Wealth",
            "Environmental Sustainability", "Ecological Balance"
        ]

        gender_equality_keywords = [
            "gender equality", "equal pay", "women empowerment", "gender-based violence", "LGBTQ+",
            "diversity", "gender parity", "Women", "Female", "Girl child", "Mahila", "Nari", "Empowerment",
            "Economic empowerment", "Third Gender Community", "Eunuchs", "Social Inclusion",
            "Inter-caste Marriage", "Intercaste Marriage", "Equality"
        ]

        child_welfare_keywords = [
            "child welfare", "child protection", "child rights", "child labor", "nutrition for children",
            "angawadi", "child development", "Childcare", "Children", "Children's Festival", "ICDS",
            "Anganwadi Workers", "Anganwadi Helpers", "ASHA", "AWC", "Day Care", "Daycare", "Crèche",
            "POSHAN Abhiyaan", "Mid Day Meal", "Akshaya Patra", "Breakfast", "Care and Protection",
            "Family based care", "Foster Care", "Orphaned", "Child Development", "Nutrition for Children",
            "Child Rights", "Child Protection"
        ]

        consumer_protection_keywords = [
            "consumer rights", "consumer protection", "consumer complaints", "consumer helpline",
            "fraud prevention", "product safety", "Consumer Protection", "Consumer Rights", "Commercial taxes",
            "VAT", "Quality Control", "Quality Improvement"
        ]

        cultural_preservation_keywords = [
            "culture", "cultural heritage", "art", "music", "literature", "folklore", "museum", "archaeology",
            "traditional arts", "Cultural Activities", "Cultural Award", "State Cultural Award",
            "Cultural Exchange", "Cultural Groups", "Cultural Institutions", "Cultural Shows",
            "Cultural Talent Search", "Dance", "Drama", "Painting", "Handicrafts", "Traditional Products",
            "Traditional crafts", "Ethnic Foods", "Festivals", "Festival", "Annual Mela", "Annual Event",
            "Annual event", "One-day event", "Three-day event", "Exhibition", "Exhibitions",
            "Festival/Exhibition", "Folk Festival", "Religious Event", "Hindu", "Hinduism", "Sufi",
            "Christmas", "Anant Chaturdashi", "Ganesh Chaturthi", "Navratri", "Sharad Navratri",
            "Chaitra", "Ramnavmi", "Krishna Janmashtami", "Shivratri", "Maha Shivratri", "Religious Tourism",
            "Pilgrimage", "Teerth", "Temple", "Historical Place", "Chamunda Mata temple",
            "Mahakaleshwar temple", "Omkareshwar", "Jyotirlinga", "Chandraprabhu", "Khandwa", "Narwar",
            "Sonagiri", "Datia", "Nijampur", "Pitampara Peeth", "Harsiddhi temple", "Hanuman Dhara",
            "Sati Anusuiya Ashram", "Jatashankar Dham", "Gupta Godavari", "Caves", "Kamdagiri Parikrama",
            "Kanha", "Chitrakut", "Urs Mela", "Rang Panchmi", "Basant Panchmi Mela", "Deepawali Mela",
            "Navratri Mela", "Rahas Mela", "Makar Sankranti", "Magh Shukla Purnima", "Bhagwan Shankar",
            "Bhagwan ’Shiv ka vishal mandir", "Shani Dev", "Shiva", "Mahakal", "Cultural Preservation"
        ]

        research_and_development_keywords = [
            "R&D", "scientific research", "innovation", "technology", "patents", "research funding",
            "academic research", "university grants", "Research", "Evaluation", "Data Collection",
            "Survey", "Census", "Monitoring", "Jharkhand Space Application Center (JSAC)", "Geo Data base",
            "GIS", "WAMIS", "Ground Water Prospect Map", "Intellectual Property", "Innovation",
            "Modernisation", "Modernization", "Scientific Research"
        ]

        # New categories for additional keywords
        tourism_keywords = [
            "tourism", "religious tourism", "pilgrimage", "eco tourism", "travel", "tour operator",
            "teerth", "tirth yatra", "tirth sthal", "tirth sthan", "historical place", "temple",
            "chamunda mata temple", "mahakaleshwar mandir", "omkareshwar", "jyotirlinga", "chandraprabhu",
            "khandwa", "narwar", "sonagiri", "datia", "nijampur", "pitambara peeth", "harsiddhi mandir",
            "hanuman dhara", "sati anusuiya ashram", "jatashankar dham", "gupta godavari", "caves",
            "kamdagiri parikrama", "kanha", "chitrakut", "tourism promotion", "tourist destination"
        ]

        festival_keywords = [
            "festival", "mela", "annual mela", "annual event", "one-day event", "three-day event",
            "urs mela", "rang panchmi", "basant panchmi mela", "deepawali mela", "navratri mela",
            "rahas mela", "makar sankranti", "magh shukla purnima", "chaitra navratra", "navratri",
            "sharad navratri", "anant chaturdashi", "ganesh chaturthi", "ramnavmi", "krishna janmashtami",
            "shivratri", "maha shivratri", "christmas", "festival safety", "cultural festival",
            "folk festival", "religious event", "bhagoriya haat", "hat bazaar"
        ]

        administrative_keywords = [
            "administrative", "administrative machinery", "district offices", "government employees",
            "government scheme", "government schemes", "central government", "state governments",
            "state plan", "state plan scheme", "state resources", "revenue", "revenue department",
            "revenue land", "registration", "certified copy", "birth certificates", "death certificates",
            "income certificates", "residential certificates", "identity card", "identity cards",
            "identity proof", "license renewal", "tenders", "inspection", "regulation", "policy",
            "gazette", "departmental proceedings", "state scheme", "central sector scheme",
            "centrally sponsored scheme", "12 वीं पंचवर्षीय योजना", "12th five-year plan",
            "monitoring", "evaluation", "survey", "census", "data collection", "statistics",
            "contingency scheme", "advisory committees", "advisory services", "public services",
            "publicity", "information dissemination", "information services", "information related to schemes",
            "MLA", "MLA schemes", "sarpanch", "panch", "panchayat", "CDPO", "treasury offices",
            "publication", "publications", "official language", "government of india", "government of goa",
            "gujarat government", "madhya pradesh", "maharashtra", "himachal pradesh", "jharkhand",
            "kerala", "tamil nadu", "pondicherry", "assam", "goa", "punjab", "haryana", "bhopal",
            "indore", "ujjain", "sagar", "satna", "chhatarpur", "bijaipur", "alirajpur", "jhabua",
            "raipur", "revenue collection"
        ]

        infrastructure_keywords = [
            "infrastructure", "road construction", "roads-plan", "road connectivity", "rural roads",
            "pmgsy", "state plan road works", "building", "building construction", "government buildings",
            "community halls", "conference hall", "dr.ambedkar bhavan", "ambedkar bhavan",
            "babu jagjiban ram chatrabas yojana", "guest house", "burial ground", "cremation ground",
            "drainage", "sewerage", "water & sewage management", "drinking water", "water supply",
            "ponds", "desilting", "watershed", "land development", "land terracing", "land management",
            "public works", "public assets", "retaining wall", "electricity", "power supply", "power tariff",
            "electrification", "broadband", "bharatnet", "city wi-fi", "cctvs", "civic amenities",
            "basic amenities", "urban infrastructure", "rural infrastructure", "adhisanrachan",
            "boundary wall", "poly house/shadenet house", "shadenet", "low-tunnel", "plastic mulching",
            "godown-cum-office building"
        ]

        religious_keywords = [
            "religious", "religious event", "religious tourism", "pilgrimage", "teerth", "tirth yatra",
            "tirth sthal", "tirth sthan", "temple", "hindu", "hinduism", "sufi", "christianity",
            "saint", "chamunda mata temple", "mahakaleshwar mandir", "omkareshwar", "jyotirlinga",
            "chandraprabhu", "khandwa", "narwar", "sonagiri", "datia", "nijampur", "pitambara peeth",
            "harsiddhi mandir", "hanuman dhara", "sati anusuiya ashram", "jatashankar dham",
            "gupta godavari", "caves", "kamdagiri parikrama", "kanha", "chitrakut", "shiva", "mahakal",
            "bhagwan shankar", "bhagwan ’shiv ka vishal mandir", "shani dev", "anant chaturdashi",
            "ganesh chaturthi", "navratri", "sharad navratri", "chaitra navratra", "ramnavmi",
            "krishna janmashtami", "shivratri", "maha shivratri", "urs mela", "rang panchmi",
            "basant panchmi mela", "deepawali mela", "navratri mela", "rahas mela", "makar sankranti",
            "magh shukla purnima", "palanquin", "religious festivals", "nikah"
        ]

        media_keywords = [
            "mass media", "all india radio", "doordarshan", "radio broadcasting", "television",
            "publicity", "information dissemination", "advertisement campaign", "awareness campaign",
            "awareness programmes", "awareness programs", "journalism", "journalist", "journalists",
            "newspapers", "periodicals", "electronic media"
        ]

        livestock_keywords = [
            "animal husbandry", "livestock", "livestock development", "dairy", "dairy development",
            "poultry", "piggery", "goatery", "cattle rearing", "cattle herders", "milk production",
            "cattle breed improvement", "cattle breeding", "artificial insemination", "calf rearing",
            "calf incentive", "buffalo", "buffalo bull", "goat", "cow sheds", "veterinary services",
            "vaccination", "fodder development", "green fodder cultivation", "animal rescue",
            "stray cattle", "stray cattle management", "carcass processing", "rabies", "rabies control",
            "pashu palan", "pashudhan", "pashu chikitsa", "pashu utprerak", "gauvanshiya pashu",
            "japanese quail", "broiler", "layer"
        ]

        fisheries_keywords = [
            "fisheries", "fish", "fish production", "fish feed", "fish market", "matsya palan",
            "mahaseer", "fishermen", "frp boats", "aquatic fauna", "ponds", "community ponds"
        ]

        awards_keywords = [
            "award", "awards", "awards and recognition", "merit awards", "cultural award",
            "state cultural award", "gallantry award", "non gallantry award", "institution award",
            "best library award", "prize", "prizes", "cash prize", "recognition", "felicitation",
            "yuva srujan puraskar", "puraskar", "puraskar yojana"
        ]

        poverty_alleviation_keywords = [
            "poverty", "poverty line", "poverty upliftment", "below poverty line", "bpl",
            "bpl families", "economically weaker sections", "ews", "low income", "lig",
            "poverty alleviation", "poverty reduction", "garibi unmulan", "garibi rekha",
            "economic upliftment", "economic development", "economic empowerment", "economic growth",
            "socio-economic development", "income upliftment", "income generating opportunities",
            "destitute", "orphaned", "deserted", "marginalized", "marginalized communities",
            "vulnerable communities", "social inclusion", "social upliftment"
        ]

        water_management_keywords = [
            "water", "drinking water", "water supply", "water management", "water resources",
            "watershed", "ponds", "desilting", "irrigation", "ground water prospect map",
            "water & sewage management", "jal", "jal praday", "peyjala", "community ponds",
            "poly house/shadenet house", "shadenet", "low-tunnel", "plastic mulching"
        ]

        waste_management_keywords = [
            "waste management", "solid and liquid waste management", "organic waste", "kitchen waste",
            "waste to wealth", "open defecation", "sanitation", "cleanliness", "hygienic",
            "incinerators", "vermi composting", "biogas"
        ]

        energy_keywords = [
            "electricity", "power supply", "power tariff", "electrification", "renewable energy",
            "renewable energy sources", "clean energy", "green energy", "biogas", "biomass briquetting",
            "efficient lighting", "reduce electricity bills", "electricity bill waiver",
            "power distribution", "power generating", "generator"
        ]

        land_management_keywords = [
            "land", "land development", "land terracing", "land management", "land ownership",
            "land purchase", "land purchase assistance", "land records", "land reclamation",
            "landless labourers", "revenue land", "wastelands", "public forest", "minor forest produce",
            "nationalized timber", "timber harvesting", "kastha", "patta", "private land",
            "niji bhumi"
        ]

        sports_keywords = [
            "sports", "games", "cricket", "fitness", "gymnasium", "playground", "sports equipments",
            "olympic", "competitions", "games and sports"
        ]

        skill_development_keywords = [
            "skill development", "training", "vocational", "nsdc", "kaushal", "apprenticeship",
            "capacity building", "skill india", "skill upgradation", "skills development", "sankalp",
            "rseti", "iti", "ncvt", "technical courses", "short term courses", "evening courses",
            "diploma in computer application", "computer", "laptop", "computerisation",
            "computerization", "professional development", "career counseling", "counseling",
            "training programs", "master trainer", "mentoring", "employability"
        ]

        public_services_keywords = [
            "public services", "public distribution system", "pds", "ration", "food distribution",
            "subsidized food grains", "subsidized salt", "antyodaya anna yojana", "public works",
            "public assets", "public safety", "public libraries", "public forest", "publicity",
            "information dissemination", "information services", "information related to schemes",
            "civic amenities", "basic amenities", "common service centre (csc)", "e-service",
            "e-service platform", "e-district", "e-mulakat", "e-nagarik", "e-office", "e-procurement",
            "ekalyan", "payment gateway", "toll free number", "citizen", "citizen of india",
            "consumer rights", "consumer protection", "consumer complaints", "consumer helpline"
        ]

        crime_prevention_keywords = [
            "crime", "atrocities", "atrocity", "victims of atrocities", "prevention of atrocities",
            "prevention of atrocities act", "caste discrimination", "untouchability",
            "untouchability eradication", "aspashyata nirmulan", "aspashyata nirmulan",
            "atyachar nivaran", "special courts", "special criminal courts", "witness protection",
            "victim compensation", "police", "gupt suchna", "crime prevention", "acid attack victims",
            "dowry victims", "violence", "child marriage prevention", "human rights"
        ]

        local_governance_keywords = [
            "panchayat", "sarpanch", "panch", "local governance", "panchayat bhawan", "local area development",
            "community development", "community self-reliance", "village", "gramin", "gramin vikas",
            "sansad adarsh gram yojana", "mla", "mla schemes", "cdpo", "local development"
        ]

        manufacturing_keywords = [
            "manufacturing", "manufacturing industries", "manufacturing sector", "industries", "industry",
            "industrial estates", "sipcot", "tansidco industrial estates", "tiic", "industrial workers",
            "cottage industries", "handloom", "handloom weavers", "textile", "textiles", "textile parks",
            "spinning mills", "leather", "footwear", "blacksmith", "clay idol making",
            "production", "productivity", "quality control", "quality improvement"
        ]

        marketing_keywords = [
            "marketing", "market", "market access", "market information", "agricultural marketing",
            "trade fair", "exhibition", "exhibitions", "fair", "hat bazaar", "bhagoriya haat",
            "procurement", "purchase", "sales", "retail", "wholesale", "khudra", "thok",
            "vikray", "kharidi kendra", "samarthan mulya", "brand building"
        ]

        education_infrastructure_keywords = [
            "school", "college", "university", "hostel", "hostel facilities", "girls hostel",
            "boarding", "residential facilities", "library", "library management", "library books",
            "public libraries", "accessible library", "audio-visual room", "acoustic auditorium",
            "computer", "laptop", "computerisation", "computerization", "calculators", "science seminars",
            "study circle", "adarsh nivasi shala", "madarsas", "madrasa", "sanskrit", "education infrastructure"
        ]

        health_infrastructure_keywords = [
            "hospital", "healthcare", "ambulance service", "emergency services", "fire fighting services",
            "fire safety", "camps", "health camps", "testing laboratories", "free diagnosis",
            "free services", "mediclaim scheme", "anganwadi", "anganwadi bhawan", "anganwadi kendra",
            "awc", "day care", "daycare", "crèche", "health infrastructure"
        ]

        social_reform_keywords = [
            "social reform", "social remedies", "social inclusion", "social upliftment", "social incentive",
            "socio-economic development", "samajik sudharna", "untouchability eradication",
            "aspashyata nirmulan", "aspashyata nirmulan", "caste discrimination", "gender equality",
            "equality", "social ostracism", "social activities", "social mobilization", "social capital",
            "community development", "community self-reliance", "human rights", "child marriage prevention",
            "dowry victims", "acid attack victims", "violence", "prevention of atrocities",
            "prevention of atrocities act", "atyachar nivaran"
        ]

        economic_development_keywords = [
            "economic development", "economic upliftment", "economic empowerment", "economic growth",
            "socio-economic development", "income upliftment", "income generating opportunities",
            "financial inclusion", "financial viability", "financial boost", "investment",
            "industrial estates", "manufacturing", "manufacturing industries", "manufacturing sector",
            "agri-tech", "meditech", "msme", "startup", "business", "entrepreneur", "enterprise",
            "self-employment", "cooperative societies", "self help groups", "self reliance",
            "self-sufficiency", "north east industrial development", "stand-up india", "make in india",
            "market access", "market information", "marketing", "trade fair", "exhibition", "exhibitions"
        ]

        emergency_services_keywords = [
            "emergency services", "ambulance service", "fire fighting services", "fire safety",
            "disaster relief", "disaster management", "flood relief", "earthquake aid", "cyclone relief",
            "drought relief", "natural calamities", "accident", "injury", "death benefit",
            "compensation", "relief", "relief and rehabilitation", "calamity relief", "rescue",
            "trauma counselling", "crisis intervention", "public safety"
        ]

        cultural_activities_keywords = [
            "cultural activities", "dance", "drama", "painting", "cultural shows", "cultural talent search",
            "essay writing", "handwriting", "poem writing", "cultural exchange", "cultural groups",
            "cultural institutions", "exhibition", "exhibitions", "festival/exhibition", "folk festival",
            "cultural festival", "traditional products", "traditional crafts", "ethnic foods",
            "handicrafts", "chitrakari"
        ]

        training_keywords = [
            "training", "vocational training", "skill development", "skill upgradation", "skills development",
            "sankalp", "rseti", "iti", "ncvt", "technical courses", "short term courses", "evening courses",
            "diploma in computer application", "computer", "laptop", "computerisation", "computerization",
            "professional development", "career counseling", "counseling", "training programs",
            "master trainer", "mentoring", "apprenticeship", "capacity building", "prashikshan"
        ]

        compensation_keywords = [
            "compensation", "relief", "monetary relief", "victim compensation", "death benefit",
            "injury", "accident", "calamity relief", "financial incentive", "cash prize", "cash",
            "assistance", "special assistance", "marriage assistance", "marriage incentive",
            "calf incentive", "one-time incentive", "one-time payment", "pratikar", "rahata rashi"
        ]

        rehabilitation_keywords = [
            "rehabilitation", "relief and rehabilitation", "economic rehabilitation", "emotional rehabilitation",
            "resettlement", "care and protection", "family based care", "foster care", "destitute",
            "orphaned", "deserted", "bonded labour", "de-addiction", "drug de-addiction", "alcoholism",
            "drug and alcohol abuse", "trauma counselling", "crisis intervention", "re-vitalization",
            "recovery", "rehabilitative services"
        ]

        public_distribution_keywords = [
            "public distribution system", "pds", "ration", "food distribution", "subsidized food grains",
            "subsidized salt", "antyodaya anna yojana", "food security", "food assistance",
            "mid-day meal", "nutrition scheme", "akshaya patra", "breakfast", "poshan abhiyaan",
            "uchit mulya ki dukan", "khadya suraksha", "khadyanna", "khadyanna bhandaran",
            "vitaran"
        ]

        agricultural_inputs_keywords = [
            "seeds", "paddy seeds", "minikit", "bio agents", "bio pesticides", "pesticides",
            "plant protection", "plant protection equipment", "planting material", "fertilizer",
            "rhizobium", "green manure", "compost", "vermi composting", "irrigation", "paddy reapers",
            "power tillers", "mechanization", "poly house/shadenet house", "shadenet", "low-tunnel",
            "plastic mulching", "kitnashak", "urvarak", "bij utpadan", "farming inputs"
        ]

        rural_infrastructure_keywords = [
            "rural infrastructure", "rural roads", "pmgsy", "road connectivity", "drinking water",
            "water supply", "sanitation", "drainage", "sewerage", "ponds", "desilting", "watershed",
            "land development", "land terracing", "public works", "public assets", "retaining wall",
            "electrification", "rural electrification", "panchayat bhawan", "community halls",
            "burial ground", "cremation ground", "basic amenities", "civic amenities", "gramin adhisanrachan"
        ]

        urban_infrastructure_keywords = [
            "urban infrastructure", "city planning", "smart cities", "metro development", "urban housing",
            "urban slums", "road construction", "drainage", "sewerage", "water & sewage management",
            "electricity", "power supply", "broadband", "bharatnet", "city wi-fi", "cctvs",
            "public works", "civic amenities", "urban development", "shahari adhisanrachan"
        ]

        traditional_crafts_keywords = [
            "handicrafts", "handloom", "handloom weavers", "traditional products", "traditional crafts",
            "ethnic foods", "leather", "footwear", "embroidery", "clay idol making", "blacksmith",
            "chitrakari", "traditional arts", "silk reeling", "eri silk", "spinning mills",
            "craft", "crafts"
        ]

        financial_inclusion_keywords = [
            "financial inclusion", "financial assistance", "subsidy", "loan", "microfinance", "credit",
            "pension", "funding", "support", "financial viability", "financial boost", "banking",
            "deposit accounts", "jan suraksha schemes", "pmjjby", "pmsby", "apy", "digidhan mission",
            "payment gateway", "direct benefit transfer", "dbt", "financial security", "vittiya samaveshan"
        ]

        digital_infrastructure_keywords = [
            "digital infrastructure", "internet connectivity", "broadband", "bharatnet", "city wi-fi",
            "online services", "e-governance", "digital payment", "digital literacy", "smart city",
            "aadhaar", "aadhaar based attendance system", "biometrics", "online portal",
            "e-service", "e-service platform", "e-district", "e-mulakat", "e-nagarik", "e-office",
            "e-procurement", "ekalyan", "jharnet", "nkn", "sms gateway", "video conferencing",
            "digital services", "shahari wifi"
        ]

        healthcare_services_keywords = [
            "healthcare", "medical", "hospital", "treatment", "ayushman", "free diagnosis",
            "free services", "mediclaim scheme", "ambulance service", "emergency services",
            "health camps", "camps", "testing laboratories", "vaccination", "veterinary services",
            "maternity benefit", "family planning", "sterilization", "ifa supplementation",
            "tb patients", "tuberculosis control", "rabies control", "hiv/aids prevention",
            "anemia prevention", "child immunization", "shishu swasthya", "surakshit matritva",
            "swasthya seva"
        ]

        education_support_keywords = [
            "education support", "free textbooks", "text books", "book bank", "book distribution",
            "book-bank facilities", "books", "library books", "reference books", "stationary",
            "stationery", "drawing materials", "calculators", "computer", "laptop", "bicycle distribution",
            "free travel", "uniform allowance", "uniform assistance", "tuition fee", "tuition fees",
            "fee reimbursement", "compulsory fee reimbursement", "fee exemption", "scholarship",
            "stipend", "bursary", "merit awards", "shiksha", "shikshan", "shulka ki vapasi"
        ]

        social_security_keywords = [
            "social security", "pension", "old age", "senior citizen", "ignops", "ignwps", "igndps",
            "nfbs", "social assistance", "social welfare", "welfare", "poverty alleviation",
            "destitute", "orphaned", "deserted", "widow", "disabled", "divyang", "special needs",
            "financial assistance", "monetary relief", "death benefit", "funeral assistance",
            "funeral expenses", "funeral rites", "samajik suraksha", "kalyan"
        ]

        community_development_keywords = [
            "community development", "community halls", "community ponds", "community self-reliance",
            "local area development", "panchayat", "panchayat bhawan", "sarpanch", "panch",
            "local governance", "social capital", "social mobilization", "social inclusion",
            "samudayik bhawan", "samudayik vikas", "sabhayata", "samaj"
        ]

        cultural_heritage_keywords = [
            "cultural heritage", "historical place", "archaeology", "museum", "traditional arts",
            "folklore", "literature", "music", "art", "handicrafts", "traditional products",
            "traditional crafts", "ethnic foods", "cultural preservation", "cultural institutions",
            "sanskrutik virasat", "paramparik kala"
        ]

        environmental_conservation_keywords = [
            "environmental conservation", "afforestation", "forestry", "wildlife", "wildlife damage",
            "wildlife conservation", "national park", "tiger foundation society", "public forest",
            "minor forest produce", "nationalized timber", "timber harvesting", "wastelands",
            "eco tourism", "green investment", "clean energy", "renewable energy sources",
            "environmental sustainability", "ecological balance", "parayavarniya sanrakshan",
            "van", "vanya prani sanrakshan", "vanyajivi"
        ]

        disability_support_keywords = [
            "disability support", "disabled", "divyang", "handicapped", "pwd", "special needs",
            "differently abled", "cerebral palsy", "mentally challenged", "motorized tricycle",
            "assistive devices", "viklangta praman patra", "nhfdc", "persons with disabilities",
            "disabled students", "disabled children", "special assistance", "visual", "visually challenged",
            "hearing impaired", "physical therapy", "divyangjan sahayata"
        ]

        agricultural_development_keywords = [
            "agricultural development", "farmer", "agriculture", "kisaan", "crop", "irrigation",
            "fertilizer", "soil", "farm", "agricultural marketing", "agro-based industries",
            "dairy development", "livestock development", "poultry", "piggery", "goatery",
            "fisheries", "seed production", "seed certification", "seed multiplication",
            "paddy seeds", "minikit", "bio agents", "bio pesticides", "plant protection",
            "cultivation methods", "green fodder cultivation", "mechanization", "pm-kisan",
            "pradhan mantri fasal bima yojana", "pmksy", "rkvy", "krishi vikas", "krishak"
        ]

        rural_livelihood_keywords = [
            "rural livelihood", "livelihood", "livelihood intervention", "livelihood opportunities",
            "rural labourers", "self help groups", "self reliance", "self-sufficiency",
            "income generating opportunities", "cottage industries", "handloom weavers",
            "cooperative societies", "rural areas", "gramin ajivika", "swarojgar"
        ]

        urban_livelihood_keywords = [
            "urban livelihood", "street vendors", "unorganized sector", "unskilled manual work",
            "urban areas", "urban livelihoods", "shahari ajivika", "self-employed"
        ]

        tourism_promotion_keywords = [
            "tourism promotion", "tourism", "religious tourism", "eco tourism", "travel",
            "tour operator", "pilgrimage", "historical place", "tirth yatra", "tirth sthal",
            "tourist destination", "parayatan", "parayatan samvardhan"
        ]

        festival_management_keywords = [
            "festival management", "festival safety", "mela", "annual mela", "annual event",
            "one-day event", "three-day event", "urs mela", "navratri mela", "rahas mela",
            "deepawali mela", "basant panchmi mela", "makar sankranti", "festival organization",
            "mela prabandhan"
        ]

        public_safety_keywords = [
            "public safety", "road safety", "festival safety", "fire fighting services", "fire safety",
            "ambulance service", "emergency services", "police", "crime prevention", "witness protection",
            "victim compensation", "accident", "injury", "calamity relief", "sarvajanik suraksha"
        ]

        health_promotion_keywords = [
            "health promotion", "awareness campaign", "awareness programmes", "awareness programs",
            "health camps", "camps", "anemia prevention", "hiv/aids prevention", "tuberculosis control",
            "rabies control", "child immunization", "family planning", "sterilization",
            "swasthya samvardhan", "swasthya jagrukta"
        ]

        education_promotion_keywords = [
            "education promotion", "literacy", "sarva shiksha abhiyan", "rte", "rte act",
            "mid day meal", "poshan abhiyaan", "free textbooks", "bicycle distribution",
            "uniform allowance", "shiksha samvardhan", "saksharta"
        ]

        social_inclusion_keywords = [
            "social inclusion", "social equality", "social reform", "social remedies", "social upliftment",
            "caste discrimination", "untouchability eradication", "gender equality", "equality",
            "marginalized communities", "vulnerable communities", "samajik samaveshan",
            "samajik sudharna"
        ]

        economic_empowerment_keywords = [
            "economic empowerment", "economic upliftment", "income generating opportunities",
            "financial inclusion", "self reliance", "self-sufficiency", "msme", "startup",
            "entrepreneur", "cooperative societies", "self help groups", "north east industrial development",
            "stand-up india", "make in india", "arthik sashaktikaran"
        ]

        disaster_relief_keywords = [
            "disaster relief", "flood relief", "earthquake aid", "cyclone relief", "drought relief",
            "natural calamities", "calamity relief", "relief", "relief and rehabilitation",
            "accident", "injury", "death benefit", "compensation", "emergency services",
            "rescue", "rahata", "apada rahata"
        ]

        child_protection_keywords = [
            "child protection", "child welfare", "child rights", "child labor", "child marriage prevention",
            "nutrition for children", "anganwadi", "icds", "poshan abhiyaan", "care and protection",
            "family based care", "foster care", "orphaned", "bal sanrakshan", "bal kalyan"
        ]

        women_empowerment_keywords = [
            "women empowerment", "mahila", "nari", "girl child", "adolescent girls", "pregnant",
            "lactating", "mother", "widow", "maternity benefit", "marriage assistance", "inter-caste marriage",
            "economic empowerment", "mahila sashaktikaran", "kishori balika"
        ]

        legal_support_keywords = [
            "legal support", "legal aid", "free legal consultation", "legal assistance", "human rights",
            "special courts", "special criminal courts", "witness protection", "victim compensation",
            "prevention of atrocities act", "consumer protection", "consumer rights",
            "vidhik sahayata", "nyaya"
        ]

        agricultural_marketing_keywords = [
            "agricultural marketing", "market", "market access", "market information", "procurement",
            "purchase", "sales", "retail", "wholesale", "trade fair", "exhibition", "exhibitions",
            "fair", "hat bazaar", "bhagoriya haat", "mandi", "samarthan mulya", "krishi vipanan"
        ]

        rural_electrification_keywords = [
            "rural electrification", "electrification", "electricity", "power supply", "power distribution",
            "power generating", "efficient lighting", "reduce electricity bills", "electricity bill waiver",
            "gramin vidyutikaran"
        ]

        urban_electrification_keywords = [
            "urban electrification", "electricity", "power supply", "broadband", "bharatnet", "city wi-fi",
            "smart city", "shahari vidyutikaran"
        ]

        livestock_development_keywords = [
            "livestock development", "animal husbandry", "dairy development", "poultry", "piggery",
            "goatery", "cattle rearing", "cattle breed improvement", "artificial insemination",
            "calf rearing", "milk production", "fodder development", "green fodder cultivation",
            "veterinary services", "pashudhan vikas"
        ]

        fisheries_development_keywords = [
            "fisheries development", "fisheries", "fish production", "fish feed", "fish market",
            "frp boats", "mahaseer", "matsya vikas", "matsya palan"
        ]

        cultural_promotion_keywords = [
            "cultural promotion", "cultural activities", "cultural award", "state cultural award",
            "cultural exchange", "cultural shows", "cultural talent search", "exhibition", "exhibitions",
            "festival/exhibition", "folk festival", "traditional arts", "sanskrutik samvardhan"
        ]

        tourism_development_keywords = [
            "tourism development", "tourism", "religious tourism", "eco tourism", "travel",
            "tour operator", "pilgrimage", "historical place", "tourist destination", "parayatan vikas"
        ]

        public_health_keywords = [
            "public health", "healthcare", "hospital", "treatment", "ayushman", "free diagnosis",
            "free services", "health camps", "vaccination", "maternity benefit", "family planning",
            "anemia prevention", "tuberculosis control", "hiv/aids prevention", "rabies control",
            "child immunization", "sarvajanik swasthya", "swasthya seva"
        ]

        social_services_keywords = [
            "social services", "social welfare", "welfare", "poverty alleviation", "social security",
            "community service", "support program", "social assistance", "social development",
            "social inclusion", "samajik seva", "kalyan"
        ]

        infrastructure_development_keywords = [
            "infrastructure development", "road construction", "roads-plan", "road connectivity",
            "rural roads", "pmgsy", "building construction", "government buildings", "community halls",
            "guest house", "burial ground", "drainage", "sewerage", "water supply", "ponds",
            "electrification", "broadband", "bharatnet", "city wi-fi", "public works",
            "adhisanrachan vikas"
        ]

        economic_support_keywords = [
            "economic support", "financial assistance", "subsidy", "loan", "microfinance", "credit",
            "pension", "funding", "support", "financial incentive", "monetary relief", "cash prize",
            "assistance", "special assistance", "marriage assistance", "marriage incentive",
            "calf incentive", "one-time incentive", "one-time payment", "arthik sahayata"
        ]

        community_welfare_keywords = [
            "community welfare", "community development", "community halls", "community ponds",
            "community self-reliance", "social capital", "social mobilization", "local area development",
            "samudayik kalyan", "samajik vikas"
        ]

        environmental_sustainability_keywords = [
            "environmental sustainability", "afforestation", "forestry", "wildlife conservation",
            "clean energy", "renewable energy", "green investment", "eco tourism", "waste management",
            "watershed", "ecological balance", "parayavarniya sthirata", "hariyali"
        ]

        agricultural_innovation_keywords = [
            "agricultural innovation", "agri-tech", "mechanization", "poly house/shadenet house",
            "shadenet", "low-tunnel", "plastic mulching", "paddy reapers", "power tillers",
            "bio agents", "bio pesticides", "cultivation methods", "green fodder cultivation",
            "krishi navachar"
        ]

        digital_governance_keywords = [
            "digital governance", "e-governance", "online services", "e-service", "e-service platform",
            "e-district", "e-mulakat", "e-nagarik", "e-office", "e-procurement", "ekalyan",
            "digital payment", "digital literacy", "smart city", "digigov", "digital shasan"
        ]

        public_welfare_keywords = [
            "public welfare", "social welfare", "poverty alleviation", "social security", "public services",
            "public distribution system", "civic amenities", "basic amenities", "community service",
            "support program", "sarvajanik kalyan", "samajik kalyan"
        ]

        healthcare_infrastructure_keywords = [
            "healthcare infrastructure", "hospital", "testing laboratories", "ambulance service",
            "emergency services", "fire fighting services", "anganwadi bhawan", "anganwadi kendra",
            "healthcare facilities", "swasthya adhisanrachan"
        ]

        education_institutions_keywords = [
            "education institutions", "school", "college", "university", "madarsas", "madrasa",
            "adarsh nivasi shala", "hostel", "girls hostel", "library", "public libraries",
            "shiksha sansthan"
        ]

        rural_welfare_keywords = [
            "rural welfare", "rural development", "village", "panchayat", "rural infrastructure",
            "farmers' welfare", "rural electrification", "sanitation", "drinking water",
            "gramin kalyan", "gramin vikas"
        ]

        urban_welfare_keywords = [
            "urban welfare", "urban development", "smart cities", "urban housing", "urban slums",
            "city planning", "urban infrastructure", "shahari kalyan", "shahari vikas"
        ]

        cultural_institutions_keywords = [
            "cultural institutions", "museum", "cultural groups", "cultural exchange", "cultural shows",
            "cultural talent search", "sanskrutik sansthan"
        ]

        disability_welfare_keywords = [
            "disability welfare", "disabled", "divyang", "special needs", "differently abled",
            "assistive devices", "motorized tricycle", "viklangta praman patra", "nhfdc",
            "disabled students", "divyangjan kalyan"
        ]

        agriculture_support_keywords = [
            "agriculture support", "farmer", "kisaan", "crop", "irrigation", "fertilizer", "seeds",
            "paddy seeds", "minikit", "pesticides", "mechanization", "pm-kisan", "pmksy",
            "pradhan mantri fasal bima yojana", "rkvy", "krishi sahayata"
        ]

        livelihood_support_keywords = [
            "livelihood support", "livelihood", "livelihood intervention", "income generating opportunities",
            "self help groups", "self reliance", "self-sufficiency", "cottage industries",
            "cooperative societies", "ajivika sahayata"
        ]

        public_infrastructure_keywords = [
            "public infrastructure", "road construction", "roads-plan", "rural roads", "pmgsy",
            "building construction", "government buildings", "community halls", "public works",
            "drainage", "sewerage", "water supply", "electrification", "sarvajanik adhisanrachan"
        ]

        social_development_keywords = [
            "social development", "social inclusion", "social reform", "social remedies", "social upliftment",
            "socio-economic development", "social capital", "social mobilization", "samajik vikas"
        ]

        economic_inclusion_keywords = [
            "economic inclusion", "financial inclusion", "economic empowerment", "income generating opportunities",
            "self reliance", "self-sufficiency", "msme", "startup", "cooperative societies",
            "arthik samaveshan"
        ]

        healthcare_support_keywords = [
            "healthcare support", "free diagnosis", "free services", "mediclaim scheme", "health camps",
            "vaccination", "maternity benefit", "family planning", "anemia prevention", "swasthya sahayata"
        ]

        education_welfare_keywords = [
            "education welfare", "free textbooks", "bicycle distribution", "uniform allowance",
            "scholarship", "stipend", "bursary", "literacy", "sarva shiksha abhiyan", "rte",
            "shiksha kalyan"
        ]

        community_support_keywords = [
            "community support", "community development", "community halls", "community ponds",
            "local area development", "social capital", "samudayik sahayata"
        ]

        cultural_support_keywords = [
            "cultural support", "cultural activities", "cultural award", "cultural exchange",
            "cultural shows", "cultural talent search", "traditional arts", "sanskrutik sahayata"
        ]

        environmental_support_keywords = [
            "environmental support", "afforestation", "wildlife conservation", "clean energy",
            "renewable energy", "eco tourism", "waste management", "parayavarniya sahayata"
        ]

        disability_services_keywords = [
            "disability services", "assistive devices", "motorized tricycle", "viklangta praman patra",
            "nhfdc", "disabled students", "special needs", "divyangjan seva"
        ]

        agricultural_services_keywords = [
            "agricultural services", "seed certification", "seed multiplication", "pesticides",
            "plant protection", "cultivation methods", "mechanization", "krishi seva"
        ]

        livelihood_services_keywords = [
            "livelihood services", "livelihood intervention", "income generating opportunities",
            "self help groups", "cooperative societies", "ajivika seva"
        ]

        infrastructure_services_keywords = [
            "infrastructure services", "road construction", "building construction", "public works",
            "drainage", "sewerage", "water supply", "electrification", "adhisanrachan seva"
        ]

        public_support_keywords = [
            "public support", "public services", "public distribution system", "civic amenities",
            "basic amenities", "community service", "sarvajanik sahayata"
        ]

        healthcare_welfare_keywords = [
            "healthcare welfare", "ayushman", "free diagnosis", "free services", "mediclaim scheme",
            "health camps", "vaccination", "swasthya kalyan"
        ]

        education_services_keywords = [
            "education services", "free textbooks", "bicycle distribution", "uniform allowance",
            "scholarship", "literacy", "sarva shiksha abhiyan", "shiksha seva"
        ]

        community_services_keywords = [
            "community services", "community development", "community halls", "local area development",
            "samudayik seva"
        ]

        cultural_services_keywords = [
            "cultural services", "cultural activities", "cultural exchange", "cultural shows",
            "traditional arts", "sanskrutik seva"
        ]

        environmental_services_keywords = [
            "environmental services", "afforestation", "wildlife conservation", "clean energy",
            "waste management", "parayavarniya seva"
        ]

        disability_inclusion_keywords = [
            "disability inclusion", "disabled", "divyang", "special needs", "differently abled",
            "assistive devices", "divyangjan samaveshan"
        ]

        agricultural_welfare_keywords = [
            "agricultural welfare", "farmer", "kisaan", "pm-kisan", "pradhan mantri fasal bima yojana",
            "rkvy", "krishi kalyan"
        ]

        livelihood_welfare_keywords = [
            "livelihood welfare", "livelihood", "self help groups", "self reliance", "cooperative societies",
            "ajivika kalyan"
        ]

        infrastructure_welfare_keywords = [
            "infrastructure welfare", "road connectivity", "rural roads", "building construction",
            "public works", "adhisanrachan kalyan"
        ]

        public_welfare_services_keywords = [
            "public welfare services", "public services", "public distribution system", "civic amenities",
            "sarvajanik kalyan seva"
        ]

        healthcare_promotion_keywords = [
            "healthcare promotion", "health camps", "awareness campaign", "anemia prevention",
            "tuberculosis control", "swasthya samvardhan"
        ]

        education_inclusion_keywords = [
            "education inclusion", "literacy", "sarva shiksha abhiyan", "rte", "free textbooks",
            "shiksha samaveshan"
        ]

        community_inclusion_keywords = [
            "community inclusion", "community development", "social capital", "local area development",
            "samudayik samaveshan"
        ]

        cultural_inclusion_keywords = [
            "cultural inclusion", "cultural exchange", "cultural shows", "traditional arts",
            "sanskrutik samaveshan"
        ]

        environmental_inclusion_keywords = [
            "environmental inclusion", "afforestation", "wildlife conservation", "clean energy",
            "parayavarniya samaveshan"
        ]


        tag_lower = self.name.lower()
        if self.match_keywords(tag_lower, scholarship_keywords):
            self.category = "scholarship"
        elif self.match_keywords(tag_lower, govt_job_keywords):
            self.category = "govt_job"
        elif self.match_keywords(tag_lower, private_job_keywords):
            self.category = "private_job"
        elif self.match_keywords(tag_lower, internship_keywords):
            self.category = "internship"
        elif self.match_keywords(tag_lower, skill_job_keywords):
            self.category = "skill_based_job"
        elif self.match_keywords(tag_lower, defense_job_keywords):
            self.category = "defense_job"
        elif self.match_keywords(tag_lower, job_keywords):
            self.category = "job"
        elif self.match_keywords(tag_lower, sc_keywords):
            self.category = "sc"
        elif self.match_keywords(tag_lower, st_keywords):
            self.category = "st"
        elif self.match_keywords(tag_lower, obc_keywords):
            self.category = "obc"
        elif self.match_keywords(tag_lower, minority_keywords):
            self.category = "minority"
        elif self.match_keywords(tag_lower, financial_keywords):
            self.category = "financial_assistance"
        elif self.match_keywords(tag_lower, women_keywords):
            self.category = "women"
        elif self.match_keywords(tag_lower, agriculture_keywords):
            self.category = "agriculture"
        elif self.match_keywords(tag_lower, senior_keywords):
            self.category = "senior_citizen"
        elif self.match_keywords(tag_lower, disability_keywords):
            self.category = "disability"
        elif self.match_keywords(tag_lower, business_keywords):
            self.category = "business"
        elif self.match_keywords(tag_lower, education_keywords):
            self.category = "education"
        elif self.match_keywords(tag_lower, health_keywords):
            self.category = "health"
        elif self.match_keywords(tag_lower, housing_keywords):
            self.category = "housing"
        elif self.match_keywords(tag_lower, youth_keywords):
            self.category = "youth_skill"
        elif self.match_keywords(tag_lower, transportation_keywords):  # New category
            self.category = "transportation"
        elif self.match_keywords(tag_lower, environment_keywords):  # New category
            self.category = "environment"
        elif self.match_keywords(tag_lower, digital_services_keywords):  # New category
            self.category = "digital_services"
        elif self.match_keywords(tag_lower, social_welfare_keywords):  # New category
            self.category = "social_welfare"
        elif self.match_keywords(tag_lower, rural_development_keywords):  # New category
            self.category = "rural_development"
        elif self.match_keywords(tag_lower, urban_development_keywords):  # New category
            self.category = "urban_development"
        elif self.match_keywords(tag_lower, international_relations_keywords):  # New category
            self.category = "international_relations"
        elif self.match_keywords(tag_lower, technology_innovation_keywords):  # New category
            self.category = "technology_innovation"
        elif self.match_keywords(tag_lower, legal_keywords):  # New category
            self.category = "legal"
        elif self.match_keywords(tag_lower, food_security_keywords):  # New category
            self.category = "food_security"
        elif self.match_keywords(tag_lower, disaster_management_keywords):  # New category
            self.category = "disaster_management"
        elif self.match_keywords(tag_lower, climate_action_keywords):  # New category
            self.category = "climate_action"
        elif self.match_keywords(tag_lower, gender_equality_keywords):  # New category
            self.category = "gender_equality"
        elif self.match_keywords(tag_lower, child_welfare_keywords):  # New category
            self.category = "child_welfare"
        elif self.match_keywords(tag_lower, consumer_protection_keywords):  # New category
            self.category = "consumer_protection"
        elif self.match_keywords(tag_lower, cultural_preservation_keywords):  # New category
            self.category = "cultural_preservation"
        elif self.match_keywords(tag_lower, research_and_development_keywords):  # New category
            self.category = "research_and_development"
        else:
            self.category = "general"


        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or "N/A"

     

class Scheme(TimeStampedModel):
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.TextField(null = True, blank = True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='schemes', null=True, blank=True)
    introduced_on = models.TextField(null = True, blank = True)
    valid_upto = models.TextField(null = True, blank = True)
    funding_pattern = models.CharField(max_length=255, null = True, blank = True)
    description = models.TextField(null = True, blank = True)
    scheme_link = models.URLField(null = True, blank = True)
    beneficiaries = models.ManyToManyField('Beneficiary', related_name='schemes', through='SchemeBeneficiary')
    documents = models.ManyToManyField('Document', related_name='schemes', through='SchemeDocument')
    pdf_url = models.URLField(null=True, blank=True)
    sponsors = models.ManyToManyField('Sponsor', related_name='schemes', through='SchemeSponsor')
    tags = models.ManyToManyField('Tag', related_name='schemes', blank=True)  # Add this line
    benefits = models.ManyToManyField('Benefit', related_name='schemes', blank=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        if not self.title.strip():  # Disallow empty or whitespace-only names
            raise ValidationError("Title name cannot be empty or whitespace.")
        
    class Meta:
        verbose_name = "Scheme"
        verbose_name_plural = "Schemes"
        ordering = ['introduced_on']

    def __str__(self):
        return self.title or "N/A"
    
class Benefit(TimeStampedModel):
    benefit_type = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Benefit"
        verbose_name_plural = "Benefits"
        ordering = ['benefit_type']

    def __str__(self):
        return self.benefit_type or "N/A"

class Beneficiary(TimeStampedModel):
    beneficiary_type = models.CharField(max_length=255, null=True, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    def clean(self):
        if re.search(r'\d', self.beneficiary_type):
            raise ValidationError("Beneficiary cannot contain numeric characters.")
    class Meta:
        verbose_name = "Beneficiary"
        verbose_name_plural = "Beneficiaries"
        ordering = ['beneficiary_type']
    
    def __str__(self):
        return self.beneficiary_type or "N/A"

class SchemeBeneficiary(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='scheme_beneficiaries')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='beneficiary_schemes')
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Scheme Beneficiary"
        verbose_name_plural = "Scheme Beneficiaries"
        ordering = ['scheme', 'beneficiary']



# DOUBT BELOW
class Criteria(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='criteria', null=True, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
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
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    step_description = models.TextField(null = True, blank = True)

    class Meta:
        verbose_name = "Procedure"
        verbose_name_plural = "Procedures"
        ordering = ['scheme']

    def __str__(self):
        return self.step_description or "N/A"

class Document(TimeStampedModel):
    document_name = models.CharField(max_length=255, null=True, blank=True)
    requirements = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['document_name']

    def __str__(self):
        return self.document_name or "N/A"

class SchemeDocument(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='scheme_documents')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='document_schemes')

    class Meta:
        verbose_name = "Scheme Document"
        verbose_name_plural = "Scheme Documents"
        ordering = ['scheme', 'document']

class Sponsor(TimeStampedModel):
    sponsor_type = models.CharField(max_length=255, null=True, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Sponsor"
        verbose_name_plural = "Sponsors"
        ordering = ['sponsor_type']

    def __str__(self):
        return self.sponsor_type or "N/A"

class SchemeSponsor(TimeStampedModel):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='scheme_sponsors')
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name='sponsor_schemes')
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

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
        return self.state_name or "N/A"

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


# class Choice(models.Model):
#     CATEGORY_CHOICES = [
#         ('education', 'Education'),
#         ('disability', 'Disability'),
#         ('employment', 'Employment'),
#     ]

#     category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
#     name = models.CharField(max_length=100)  # The actual choice value
#     description = models.TextField(blank=True, null=True)  # Optional field for additional details
#     is_active = models.BooleanField(default=True)  # To allow enabling/disabling specific choices

#     def __str__(self):
#         return f"{self.category} - {self.name}"


class ProfileField(models.Model):
    FIELD_TYPE_CHOICES = [
        ('char', 'Text'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('decimal', 'Decimal'),
        ('date', 'Date'),
        ('choice', 'Choice'),
    ]

    name = models.CharField(max_length=100, unique=True)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPE_CHOICES)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    min_value = models.IntegerField(blank=True, null=True, help_text="Minimum value for integer fields.")
    max_value = models.IntegerField(blank=True, null=True, help_text="Maximum value for integer fields.")
    position = models.IntegerField(default=1)
    is_fixed = models.BooleanField(default=False)

    def clean(self):
        # Ensure min_value is less than max_value if both are set
        if self.field_type == 'integer' and self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValidationError("Minimum value cannot be greater than the maximum value.")
        
    def save(self, *args, **kwargs):
        if self.pk:
            original_field = ProfileField.objects.get(pk=self.pk)
            if original_field.position != self.position:
                self.shift_positions(original_field.position, self.position)

        super(ProfileField, self).save(*args, **kwargs)
    
    def shift_positions(self, old_position, new_position):
        if old_position < new_position:
            ProfileField.objects.filter(
                position__gt=old_position, position__lte=new_position
            ).update(position=models.F('position') - 1)
        elif old_position > new_position:
            ProfileField.objects.filter(
                position__gte=new_position, position__lt=old_position
            ).update(position=models.F('position') + 1)

        self.position = new_position

    def __str__(self):
        return self.name


class ProfileFieldChoice(models.Model):
    field = models.ForeignKey(ProfileField, on_delete=models.CASCADE, related_name='choices')
    value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.field.name} - {self.value}"


class ProfileFieldValue(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='profile_field_values')
    field = models.ForeignKey(ProfileField, on_delete=models.CASCADE)
    value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.field.name}: {self.value}"
    

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
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    saved_schemes = models.ManyToManyField('Scheme', related_name='saved_by_users')
    # DETAILS BELOW
    name = models.CharField(max_length=100, blank=True, null=True)
    profile_field_value = models.JSONField(blank=True, null=True)
    # gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True, null=True)
    # age = models.PositiveIntegerField(blank=True, null=True)
    # occupation = models.CharField(max_length=100, blank=True, null=True)
    # income = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    # education = models.CharField(max_length=100, choices=[('None', 'None'), ('High School', 'High School'), ('Undergraduate', 'Undergraduate'), ('Postgraduate', 'Postgraduate'), ('Doctoral', 'Doctoral'),('Pre-primary', 'Pre-primary'), ('Secondary', 'Secondary'), ('Higher Secondary', 'Higher Secondary'), ('Diploma/Certification', 'Diploma/Certification')], blank=True, null=True)
    # education = models.ForeignKey(EducationChoice, on_delete=models.SET_NULL, blank=True, null=True)
    # employment_status = models.CharField(max_length=100, choices=[('Employed', 'Employed'), ('Self-employed', 'Business'), ('Unemployed', 'Unemployed')], blank=True, null=True)
    # education = models.ForeignKey(
    #     Choice,
    #     on_delete=models.SET_NULL,
    #     limit_choices_to={'category': 'education'},
    #     null=True,
    #     blank=True,
    #     related_name='education_choices'
    # )
    # disability = models.ForeignKey(
    #     Choice,
    #     on_delete=models.SET_NULL,
    #     limit_choices_to={'category': 'disability'},
    #     null=True,
    #     blank=True,
    #     related_name='disability_choices'
    # )
    # employment_status = models.ForeignKey(
    #     Choice,
    #     on_delete=models.SET_NULL,
    #     limit_choices_to={'category': 'employment'},
    #     null=True,
    #     blank=True,
    #     related_name='employment_choices'
    # )
    # government_employee = models.BooleanField(default=False)
    # category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)
    # minority = models.BooleanField(default=False)
    # state_of_residence = models.CharField(max_length=50, choices=STATE_CHOICES, blank=True, null=True)
    # disability = models.ForeignKey(DisabilityChoice, on_delete=models.SET_NULL, blank=True, null=True)
    # bpl_card_holder = models.CharField(max_length=255, default = "NO")

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
    image = models.ImageField(storage=MediaStorage(), upload_to='banners/', blank=True, null=True)
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


class SchemeReport(models.Model):
    REPORT_CATEGORIES = [
        ('incorrect_info', 'Incorrect Information'),
        ('outdated_info', 'Outdated Information'),
        ('other', 'Other'),
    ]

    scheme_id = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    report_category = models.CharField(max_length=50, choices=REPORT_CATEGORIES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Report for Scheme {self.scheme_id} - {self.report_category}"

class WebsiteFeedback(models.Model):
    FEEDBACK_CATEGORIES = [
        ('bug', 'Bug Report'),
        ('improvement', 'Improvement Suggestion'),
        ('general', 'General Feedback'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=50, choices=FEEDBACK_CATEGORIES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Feedback - {self.category}"
    
class UserInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE)
    interaction_value = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

class SchemeFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scheme_feedbacks")
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name="feedbacks")
    feedback = models.TextField()
    rating = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Feedback by {self.user.username} on {self.scheme.title}"
    
class UserEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.event_type} - {self.scheme.title}"


class LayoutItem(models.Model):
    COLUMN_CHOICES = [
        ("schemes", "Schemes"),
        ("scholarships", "Scholarships"),
        ("jobs", "Jobs"),
    ]
    
    column_name = models.CharField(max_length=20, choices=COLUMN_CHOICES, unique=True)
    is_active = models.BooleanField(default=False)
    order = models.IntegerField(default=0)  

    class Meta:
        ordering = ["order"] 

    def save(self, *args, **kwargs):
        if self.pk:
            original_field = LayoutItem.objects.get(pk=self.pk)
            if original_field.order != self.order:
                self.shift_orders(original_field.order, self.order)

        super(LayoutItem, self).save(*args, **kwargs)
    
    def shift_orders(self, old_order, new_order):
        if old_order < new_order:
            LayoutItem.objects.filter(
                order__gt=old_order, order__lte=new_order
            ).update(order=models.F('order') - 1)
        elif old_order > new_order:
            LayoutItem.objects.filter(
                order__gte=new_order, order__lt=old_order
            ).update(order=models.F('order') + 1)

        self.order = new_order

    def __str__(self):
        return self.get_column_name_display()


class UserEvents(models.Model):
    EVENT_TYPES = [
        ('view', 'Scheme View'),
        ('filter', 'Filter Applied'),
        ('search', 'Search Query'),
        ('sort', 'Sorting Action'),
        ('apply', 'External Apply'),
        ('save', 'Save'),
        ('download', 'Download'),
        ('share', 'Share'),
        ('error', 'Error Event'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    scheme = models.ForeignKey(Scheme, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(blank=True, null=True) 
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.event_type} - {self.timestamp}"

class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)  
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        if self.pk:
            original_field = FAQ.objects.get(pk=self.pk)
            if original_field.order != self.order:
                self.shift_orders(original_field.order, self.order)

        super(FAQ, self).save(*args, **kwargs)
    
    def shift_orders(self, old_order, new_order):
        if old_order < new_order:
            FAQ.objects.filter(
                order__gt=old_order, order__lte=new_order
            ).update(order=models.F('order') - 1)
        elif old_order > new_order:
            FAQ.objects.filter(
                order__gte=new_order, order__lt=old_order
            ).update(order=models.F('order') + 1)

        self.order = new_order
    class Meta:
        ordering = ["order"] 

    def __str__(self):
        return self.question
    

from django.db import models

class CompanyMeta(models.Model):
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=255)
    tagline = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    support_email = models.EmailField(blank=True, null=True)

    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)

    business_hours = models.JSONField(blank=True, null=True)

    logo = models.ImageField(upload_to="company_meta/", blank=True, null=True)
    favicon = models.ImageField(upload_to="company_meta/", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Company Meta"
        verbose_name_plural = "Company Meta"


class Resource(models.Model):
    state_name = models.ForeignKey(State, on_delete=models.CASCADE, related_name="resources", null=True, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    resource_link = models.URLField()

    def get_queryset(self):
        state_id = self.kwargs.get("state_id")
        
        if state_id:
            state = State.objects.filter(id=state_id, is_active=True).first()

            if state:
                return Resource.objects.filter(state_name=state)
            return Resource.objects.none()

        return Resource.objects.filter(state_name__is_active=True)

    def __str__(self):
        return f"{self.state_name.state_name} - {self.resource_link}"


class Announcement(models.Model):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    view_link = models.URLField(blank=True, null=True)
    apply_link = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)

    def clean(self):
        # Validate max 4 active announcements
        if self.is_active:
            active_count = Announcement.objects.filter(is_active=True).exclude(pk=self.pk).count()
            if active_count >= 4:
                raise ValidationError("You can have a maximum of 4 active announcements.")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
class UserPrivacySettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    allow_information_usage = models.BooleanField(default=False)
    allow_information_sharing = models.BooleanField(default=False)
    allow_cookies_tracking = models.BooleanField(default=False)


class MissingSchemeReport(models.Model):
    scheme_name = models.CharField(max_length=255)
    scheme_link = models.URLField(blank=True, null=True)
    description = models.TextField()
    supporting_document = models.FileField(upload_to='missing_scheme_docs/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.scheme_name
