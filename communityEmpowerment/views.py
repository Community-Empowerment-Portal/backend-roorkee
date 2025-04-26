from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework import serializers
from django.db.models import Count, F
from django.utils.dateparse import parse_date
from django.db.models.functions import TruncDate, TruncMonth, TruncDay, TruncWeek
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.generics import ListAPIView
from django.shortcuts import get_object_or_404
from django.db.models import OuterRef, Subquery, IntegerField
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from django.db.models import Count
from django.utils.timezone import now
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets
from django.utils.html import strip_tags
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q
import logging
from django.utils.timezone import now, timedelta
from communityEmpowerment.utils.utils import recommend_schemes, load_cosine_similarity, collaborative_recommendations, extract_keywords_from_feedback
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
import json
from django.core.mail import EmailMessage
import requests
from calendar import monthrange
from datetime import date



logger = logging.getLogger(__name__)

from .models import (
    State, Resource, Department, Organisation, Scheme, Beneficiary, SchemeBeneficiary, Benefit, LayoutItem, FAQ, CompanyMeta,
    Criteria, Procedure, Document, SchemeDocument, Sponsor, SchemeSponsor, CustomUser, ProfileField,
    Banner, SavedFilter, SchemeReport, WebsiteFeedback, UserInteraction, SchemeFeedback, UserEvent,UserEvents, ProfileFieldValue, Announcement
    
)
from .serializers import (
    StateSerializer, DepartmentSerializer, OrganisationSerializer, SchemeSerializer,ResourceSerializer ,
    BeneficiarySerializer, SchemeBeneficiarySerializer, BenefitSerializer, FAQSerializer,
    CriteriaSerializer, ProcedureSerializer, DocumentSerializer, LayoutItemSerializer, CompanyMetaSerializer,
    SchemeDocumentSerializer, SponsorSerializer, SchemeSponsorSerializer, UserRegistrationSerializer,
    SaveSchemeSerializer,  LoginSerializer, BannerSerializer, SavedFilterSerializer, SchemeLinkSerializer, ProfileFieldValueSerializer,
    PasswordResetConfirmSerializer, PasswordResetRequestSerializer, SchemeReportSerializer, WebsiteFeedbackSerializer,
    UserInteractionSerializer, SchemeFeedbackSerializer, UserEventSerializer, UserProfileSerializer, UserEventsSerializer, AnnouncementSerializer
)

from rest_framework.exceptions import NotFound
from .filters import CustomOrderingFilter
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def health_check(request):
    return JsonResponse({"status": "healthy"}, status=200)

class SchemePagination(PageNumberPagination):
    page_size_query_param = 'limit'


class StateListAPIView(generics.ListAPIView):
    queryset = State.objects.filter(is_active=True)
    serializer_class = StateSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'state_name']
    ordering = ['state_name']

class StateSchemesListAPIView(generics.ListAPIView):
    serializer_class = SchemeSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['introduced_on', 'title']
    ordering = ['-introduced_on']
    pagination_class = SchemePagination

    def get_queryset(self):
        state_id = self.kwargs.get('state_id')
        
        if state_id:
            return Scheme.objects.filter(
                is_active=True,
                department__state_id=state_id,
                department__is_active=True, 
                department__state__is_active=True 
            )

        return Scheme.objects.none()
    
class StateDetailAPIView(generics.RetrieveAPIView):
    queryset = State.objects.all()
    serializer_class = StateSerializer

class DepartmentListAPIView(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'department_name']
    ordering = ['-created_at']

class OrganisationListAPIView(generics.ListAPIView):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'organisation_name']
    ordering = ['-created_at']



class SchemeListAPIView(generics.ListAPIView):
    serializer_class = SchemeSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['introduced_on', 'title']
    ordering = ['-introduced_on']
    pagination_class = SchemePagination

    def get_queryset(self):
        department_id = self.request.query_params.get('department_id')
        queryset = Scheme.objects.filter(
            is_active=True,
            department__is_active=True,
            department__state__is_active=True
        )
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        return queryset

class SchemeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer

class BeneficiaryListAPIView(generics.ListAPIView):
    queryset = Beneficiary.objects.all()
    serializer_class = BeneficiarySerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'beneficiary_type']
    ordering = ['-created_at']

class SchemeBeneficiaryListAPIView(generics.ListAPIView):
    queryset = SchemeBeneficiary.objects.all()
    serializer_class = SchemeBeneficiarySerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

class SchemeBenefitListAPIView(generics.ListAPIView):
    serializer_class = BenefitSerializer

    def get_queryset(self):
        scheme_id = self.kwargs.get('scheme_id')
        try:
            # Ensure the Scheme exists before filtering Benefits
            Scheme.objects.get(id=scheme_id)
            return Benefit.objects.filter(schemes__id=scheme_id)
        except Scheme.DoesNotExist:
            return Benefit.objects.none()

class CriteriaListAPIView(generics.ListAPIView):
    queryset = Criteria.objects.all()
    serializer_class = CriteriaSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'description']
    ordering = ['-created_at']

    def get_queryset(self):
        scheme_id = self.request.query_params.get('scheme_id')
        if scheme_id:
            return self.queryset.filter(scheme_id=scheme_id)
        return self.queryset.all()

class ProcedureListAPIView(generics.ListAPIView):
    queryset = Procedure.objects.all()
    serializer_class = ProcedureSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        scheme_id = self.request.query_params.get('scheme_id')
        if scheme_id:
            return self.queryset.filter(scheme_id=scheme_id)
        return self.queryset.all()

class DocumentListAPIView(generics.ListAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'document_name']
    ordering = ['-created_at']

class SchemeDocumentListAPIView(generics.ListAPIView):
    serializer_class = SchemeDocumentSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        scheme_id = self.kwargs['scheme_id']
        return SchemeDocument.objects.filter(scheme__id=scheme_id)

    

class SponsorListAPIView(generics.ListAPIView):
    queryset = Sponsor.objects.all()
    serializer_class = SponsorSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'sponsor_type']
    ordering = ['-created_at']

class SchemeSponsorListAPIView(generics.ListAPIView):
    queryset = SchemeSponsor.objects.all()
    serializer_class = SchemeSponsorSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

class StateDepartmentsListAPIView(generics.ListAPIView):
    serializer_class = DepartmentSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'department_name']
    ordering = ['-created_at']

    def get_queryset(self):
        state_id = self.kwargs.get('state_id')
        if not state_id:
            raise NotFound("State ID not provided.")
        return Department.objects.filter(state_id=state_id)

class DepartmentSchemesListAPIView(generics.ListAPIView):
    serializer_class = SchemeSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['introduced_on', 'title']
    ordering = ['-introduced_on']

    def get_queryset(self):
        department_id = self.kwargs.get('department_id')
        if not department_id:
            raise NotFound("Department ID not provided.")
        return Scheme.objects.filter(department_id=department_id)

class SchemeBeneficiariesListAPIView(generics.ListAPIView):
    serializer_class = SchemeBeneficiarySerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        scheme_id = self.kwargs.get('scheme_id')
        if not scheme_id:
            raise NotFound("Scheme ID not provided.")
        return SchemeBeneficiary.objects.filter(scheme_id=scheme_id)

class SchemeCriteriaListAPIView(generics.ListAPIView):
    serializer_class = CriteriaSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'description']
    ordering = ['-created_at']

    def get_queryset(self):
        scheme_id = self.kwargs.get('scheme_id')
        if not scheme_id:
            raise NotFound("Scheme ID not provided.")
        return Criteria.objects.filter(scheme_id=scheme_id)

class SchemeProceduresListAPIView(generics.ListAPIView):
    serializer_class = ProcedureSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        scheme_id = self.kwargs.get('scheme_id')
        if not scheme_id:
            raise NotFound("Scheme ID not provided.")
        return Procedure.objects.filter(scheme_id=scheme_id)

class SchemeDocumentsListAPIView(generics.ListAPIView):
    serializer_class = SchemeDocumentSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        scheme_id = self.kwargs.get('scheme_id')
        if not scheme_id:
            raise NotFound("Scheme ID not provided.")
        return SchemeDocument.objects.filter(scheme_id=scheme_id)

class SchemeSponsorsListAPIView(generics.ListAPIView):
    serializer_class = SchemeSponsorSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        scheme_id = self.kwargs.get('scheme_id')
        if not scheme_id:
            raise NotFound("Scheme ID not provided.")
        return SchemeSponsor.objects.filter(scheme_id=scheme_id)

from rest_framework import generics, permissions
from django.contrib.auth.models import User
# from .models import UserProfile


# from .serializers import UserSerializer
# from .serializers import UserPreferencesSerializer

from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

# class UserProfileAPIView(generics.RetrieveUpdateAPIView):
#     serializer_class = UserSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_object(self):
#         user = self.request.user
#         # Ensure user has a profile
#         UserProfile.objects.get_or_create(user=user)
#         return user

#     def put(self, request, *args, **kwargs):
#         return self.update(request, *args, **kwargs)


# class RecommendationsAPIView(generics.ListAPIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         return UserPreferences.objects.filter(user=self.request.user)

#     def get(self, request, *args, **kwargs):
#         user_preferences, created = UserPreferences.objects.get_or_create(user=self.request.user)
#         recommendations = generate_recommendations(user_preferences)
#         return Response({'recommendations': recommendations})

# Views from origin/main branch
class UserRegistrationAPIView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user": UserRegistrationSerializer(user).data,
                "message": "User created successfully. Please check your email to verify your account.",
                "username": user.username
            }, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class UserProfileView(generics.GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        response_data = serializer.data
        dynamic_field_values = ProfileFieldValue.objects.filter(user=user, field__is_active=True)
        dynamic_fields = {
        value.field.name: value.value for value in dynamic_field_values
    }
        profile_fields = ProfileField.objects.all()
        ordered_profile_fields = sorted(profile_fields, key=lambda field: field.position)
        response_data["dynamic_fields"] = dynamic_fields
        response_data["ordered_profile_fields"] = [
            {"name": field.name, "field_type": field.field_type, "position": field.position}
            for field in ordered_profile_fields
        ]
        return Response(response_data)
    
    def update_dynamic_fields(self, user, dynamic_fields_data):
        """
        Handles updating dynamic field values for the user.
        """
        for field_name, field_value in dynamic_fields_data.items():
            try:
                field = ProfileField.objects.get(name=field_name, is_active=True)
                dynamic_field_value, _ = ProfileFieldValue.objects.get_or_create(
                    user=user, field=field
                )
                dynamic_field_value.value = field_value
                dynamic_field_value.save()
            except ProfileField.DoesNotExist:
                raise serializers.ValidationError(f"Invalid dynamic field: {field_name}")

    def put(self, request, *args, **kwargs):
        """
        Handles updating the user profile, including both static and dynamic fields.
        """
        user = self.get_object()
        static_data = {key: value for key, value in request.data.items() if key != "dynamic_fields"}
        dynamic_fields_data = request.data.get("dynamic_fields", {})

        # Validate and update static fields
        serializer = self.get_serializer(user, data=static_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Validate and update dynamic fields
        if isinstance(dynamic_fields_data, dict):
            self.update_dynamic_fields(user, dynamic_fields_data)

        # Return updated data
        response_data = self.get_serializer(user).data
        return Response(response_data)
    

class UserProfileFieldValuesView(generics.GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]
    def get_object(self):
        user_id = self.kwargs.get('user_id')
        return CustomUser.objects.get(id=user_id)

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        response_data = serializer.data
        dynamic_field_values = ProfileFieldValue.objects.filter(user=user, field__is_active=True)
        dynamic_fields = {
        value.field.name: value.value for value in dynamic_field_values
    }
        profile_fields = ProfileField.objects.all()
        ordered_profile_fields = sorted(profile_fields, key=lambda field: field.position)
        response_data["dynamic_fields"] = dynamic_fields
        response_data["ordered_profile_fields"] = [
            {"name": field.name, "field_type": field.field_type, "position": field.position}
            for field in ordered_profile_fields
        ]
        return Response(response_data)

class AllProfileFieldsView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        # Fetch all active dynamic fields
        dynamic_fields = ProfileField.objects.filter(is_active=True)
        ordered_profile_fields = sorted(dynamic_fields, key=lambda field: field.position-1)
        # Build the response data for each dynamic field
        dynamic_field_data = []
        for field in ordered_profile_fields:
            dynamic_field_info = {
                'id': field.id,
                'name': field.name,
                'type': field.field_type,
                'placeholder': field.placeholder,
                'is_required': field.is_required,
                'min_value': field.min_value,
                'max_value': field.max_value,
                'choices': [
                    choice.value for choice in field.choices.filter(is_active=True)
                ] if field.field_type == 'choice' else None,
            }
            dynamic_field_data.append(dynamic_field_info)

        return Response({
            "profile_fields": dynamic_field_data
        })

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            return Response(tokens, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Access the currently authenticated user
        user = request.user

        # Serialize the user data
        serializer = UserRegistrationSerializer(user)
        return Response(serializer.data)
    
class LogoutView(APIView):
    permission_classes = (IsAuthenticated)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=HTTP_200_OK)
        except KeyError:
            return Response({"error": "Refresh token not provided."}, status=HTTP_400_BAD_REQUEST)
        except TokenError as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)


class ProtectedView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(data={"message": "This is a protected view."}, status=HTTP_200_OK)


class SchemeSearchView(APIView):
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', None)
        if query:
            schemes = Scheme.objects.filter(title__icontains=query)
            serializer = SchemeSerializer(schemes, many=True)
            return Response(serializer.data, status= status.HTTP_200_OK)
        return Response({"detail": "Query parameter 'q' is required."}, status=HTTP_400_BAD_REQUEST)



class SaveSchemeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        user = request.user
        scheme_id = request.data.get('scheme_id', None)

        if scheme_id is None:
            return Response({"detail": "Scheme ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Add the scheme to the user's saved_schemes
        user.saved_schemes.add(scheme_id)
        user.save()

        return Response({'status': 'scheme saved'}, status=status.HTTP_200_OK)
    
class UserSavedSchemesView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = SchemePagination

    def get(self, request, *args, **kwargs):
        user = request.user
        saved_schemes = user.saved_schemes.all()
        search_query = request.query_params.get('q', None)
        state_ids = request.query_params.getlist('state_ids', [])
        department_ids = request.query_params.getlist('department_ids', [])
        sponsor_ids = request.query_params.getlist('sponsor_ids', [])
        beneficiary_keywords = request.query_params.getlist('beneficiary_keywords', [])

        # Convert state_ids and department_ids to integers if they are provided
        if state_ids:
            state_ids = [int(id) for id in state_ids]
        if department_ids:
            department_ids = [int(id) for id in department_ids]

        if search_query:
            saved_schemes = saved_schemes.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(sponsors__name__icontains=search_query)
            )

        if state_ids:
            saved_schemes = saved_schemes.filter(department__state_id__in=state_ids)

        if department_ids:
            saved_schemes = saved_schemes.filter(department_id__in=department_ids)
        
        if sponsor_ids:
            saved_schemes = saved_schemes.filter(sponsors__id__in=sponsor_ids)

        if beneficiary_keywords:
            beneficiary_filters = Q()
            for keyword in beneficiary_keywords:
                beneficiary_filters |= Q(beneficiaries__beneficiary_type__icontains=keyword)
            saved_schemes = saved_schemes.filter(beneficiary_filters)

        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(saved_schemes, request)
        
        if page is not None:
            serializer = SchemeSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback if pagination is not applied
        serializer = SchemeSerializer(saved_schemes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    

class UnsaveSchemeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        scheme_ids = request.data.get('scheme_ids', [])

        if not isinstance(scheme_ids, list):
            return Response({'error': 'scheme_ids must be a list'}, status=status.HTTP_400_BAD_REQUEST)

        removed_schemes = []
        for scheme_id in scheme_ids:
            try:
                scheme = Scheme.objects.get(id=scheme_id)
                if scheme in user.saved_schemes.all():
                    user.saved_schemes.remove(scheme)
                    removed_schemes.append(scheme)
                else:
                    print(f"Scheme with id {scheme_id} is not saved by user {user.username}")
            except Scheme.DoesNotExist:
                # print(f"Scheme with id {scheme_id} does not exist")
                return Response({'error': f'Scheme with id {scheme_id} does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        user.save()
        # print(f"User {user.username} unsaved schemes: {[scheme.id for scheme in removed_schemes]}")
        return Response({'status': 'Schemes unsaved successfully', 'removed_schemes': SchemeSerializer(removed_schemes, many=True).data}, status=status.HTTP_200_OK)
    
# BANNER VIEW BELOW
    
class BannerListCreateAPIView(generics.ListCreateAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer

    def post(self, request, *args, **kwargs):
        serializer = BannerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BannerDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer


class SavedFilterListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedFilterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedFilter.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SavedFilterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavedFilterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedFilter.objects.filter(user=self.request.user)
    

# choices views below
    

class GenderChoicesView(APIView):
    def get(self, request):
        return Response(CustomUser._meta.get_field('gender').choices, status=status.HTTP_200_OK)

class StateChoicesView(APIView):
    def get(self, request):
        return Response(CustomUser._meta.get_field('state_of_residence').choices, status=status.HTTP_200_OK)

# class EducationChoicesView(APIView):
#     def get(self, request):
#         active_choices = Choice.objects.filter(category='education', is_active=True).values('id', 'name')
#         return Response(active_choices, status=status.HTTP_200_OK)
    
# class DisabilityChoicesView(APIView):
#     def get(self, request):
#         active_choices = Choice.objects.filter(category='disability', is_active=True).values('id', 'name')
#         return Response(active_choices, status=status.HTTP_200_OK)

class CategoryChoicesView(APIView):
    def get(self, request):
        return Response(CustomUser._meta.get_field('category').choices, status=status.HTTP_200_OK)

# class EmploymentChoicesView(APIView):
#     def get(self, request):
#         active_choices = Choice.objects.filter(category='employment', is_active=True).values('id', 'name')
#         return Response(active_choices, status=status.HTTP_200_OK)


def verify_email(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    context = {
        'frontend_url': settings.FRONTEND_URL
    }
    if user is not None and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.save()
        return render(request, 'email_verified.html', context)
    else:
        return render(request, 'email_verification_failed.html', context)
    
class PasswordResetRequestView(APIView):
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = CustomUser.objects.get(email=serializer.validated_data['email'])
            except CustomUser.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)
            
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{settings.FRONTEND_URL}/reset-password-confirm/{uid}/{token}/"

            # Render the HTML content from your template
            html_content = render_to_string('password_reset_email.html', {
                'user': user,
                'reset_link': reset_link,
            })
            
            # Optionally, create a plain text alternative
            text_content = strip_tags(html_content)

            # Create the email with both plain text and HTML content
            email = EmailMultiAlternatives(
                subject='Password Reset Request',
                body=text_content,  # This can be the plain text version
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")  # Attach the HTML version
            email.send(fail_silently=False)

            return Response({"message": "Password reset link has been sent to your email."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PreferenceView(APIView):
    def get(self, request):
        try:
            user_state = request.user.state_of_residence
            state_instance = State.objects.get(state_name=user_state)
            schemes = Scheme.objects.filter(department__state=state_instance)
            serializer = SchemeSerializer(schemes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except State.DoesNotExist:
            return Response({"error": "State not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScholarshipSchemesListView(generics.ListAPIView):
    serializer_class = SchemeSerializer
    pagination_class = SchemePagination

    def get_queryset(self):
        queryset = Scheme.objects.filter(
            tags__name__icontains='scholarship',
            is_active=True,
            department__is_active=True,
            department__state__is_active=True
        )

        state_ids_param = self.request.query_params.get('state_ids', '[]')

        try:
            state_ids = [int(id.strip()) for id in state_ids_param.strip('[]').split(',') if id.strip().isdigit()]
        except ValueError:
            state_ids = []

        if state_ids:
            queryset = queryset.filter(department__state_id__in=state_ids)

        return queryset


class JobSchemesListView(generics.ListAPIView):
    serializer_class = SchemeSerializer
    pagination_class = SchemePagination

    def get_queryset(self):
        queryset = Scheme.objects.filter(
            Q(tags__name__icontains='job') | Q(tags__name__icontains='employment'),
            is_active=True,
            department__is_active=True,
            department__state__is_active=True
        )

        state_ids_param = self.request.query_params.get('state_ids', '[]')

        try:
            state_ids = [int(id.strip()) for id in state_ids_param.strip('[]').split(',') if id.strip().isdigit()]
        except ValueError:
            state_ids = []

        if state_ids:
            queryset = queryset.filter(department__state_id__in=state_ids)

        return queryset

    
class SchemeBenefitsView(generics.GenericAPIView):
    serializer_class = BenefitSerializer

    def get(self, request, scheme_id):
        # Get the scheme object or return 404 if not found
        try:
            scheme = Scheme.objects.get(id=scheme_id)
        except Scheme.DoesNotExist:
            return Response({'error': 'Scheme not found'}, status=404)

        # Get all benefits related to the scheme
        benefits = scheme.benefits.all()
        serializer = self.get_serializer(benefits, many=True)
        return Response(serializer.data)

        
class SchemesByMultipleStatesAndDepartmentsAPIView(APIView):
    pagination_class = SchemePagination
    ordering_fields = ['title']

    def post(self, request, *args, **kwargs):
        state_ids = request.data.get('state_ids', [])
        department_ids = request.data.get('department_ids', [])
        beneficiary_keywords = request.data.get('beneficiary_keywords', [])
        sponsor_ids = request.data.get('sponsor_ids', [])
        funding_pattern = request.data.get('funding_pattern', None)
        search_query = request.data.get('search_query', None)
        tag = request.data.get('tag', None)
        ordering = request.data.get('ordering', self.ordering_fields) 


        user_profile = request.data.get('user_profile', {})  # Dictionary containing profile data
        user_tags = []

        profile_field_mappings = {
            "community": ["sc", "st", "obc", "general"],
            "minority": ["muslim", "christian", "sikh", "buddhist", "parsi", "jain"],
            "education": ["undergraduate", "postgraduate", "phd", "school"],
            "disability": ["physical", "visual", "hearing", "intellectual"],
            "occupation": ["farmer", "student", "teacher", "entrepreneur", "laborer"],
            "income": ["bpl", "middle", "high"]
        }

        for field, possible_tags in profile_field_mappings.items():
            field_value = user_profile.get(field, "").lower()
            if field_value in possible_tags:
                user_tags.append(field_value)


        scheme_filters = Q()

        if tag:
            scheme_filters &= Q(tags__name__icontains=tag)

        if user_tags:
            tag_filters = Q()
            for user_tag in user_tags:
                tag_filters |= Q(tags__name__icontains=user_tag)
            scheme_filters &= tag_filters

        if tag == "job":
            scheme_filters &= Q(tags__name__icontains='job') | Q(tags__name__icontains='employment')
        if tag == "scholarship":
            scheme_filters &= Q(tags__name__icontains='scholarship')
        if state_ids:
            scheme_filters &= Q(department__state_id__in=state_ids)
        if department_ids:
            scheme_filters &= Q(department_id__in=department_ids)
        if beneficiary_keywords:
            beneficiary_filters = Q()
            for keyword in beneficiary_keywords:
                beneficiary_filters |= Q(beneficiaries__beneficiary_type__icontains=keyword)
            scheme_filters &= beneficiary_filters
        if sponsor_ids:
            scheme_filters &= Q(sponsors__id__in=sponsor_ids)
        if funding_pattern:
            scheme_filters &= Q(funding_pattern__icontains=funding_pattern)
        if search_query:
            search_filters = Q()
            search_filters |= Q(title__icontains=search_query) | Q(description__icontains=search_query)
            scheme_filters &= search_filters

        scheme_filters &= Q(department__is_active=True, department__state__is_active=True,is_active=True,)

        schemes = Scheme.objects.filter(scheme_filters).distinct()

        if ordering:
            schemes = schemes.order_by(*ordering)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(schemes, request)
        if page is not None:
            serializer = SchemeSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SchemeSerializer(schemes, many=True)
        return Response(serializer.data)
    
class ResendVerificationEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_email_verified:  # Check if the user's email is already verified
            return JsonResponse({"detail": "This email is already verified."}, status=400)
        
        # Send the verification email
        self.send_verification_email(user)
        return JsonResponse({"detail": "Verification email has been sent."}, status=200)
    
    def send_verification_email(self, user):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_link = f"{settings.SITE_URL}/verify-email/{uid}/{token}/"

        subject = 'Verify your email'
        
        html_content = render_to_string('email_verification.html', {
            'user': user,
            'verification_link': verification_link,
        })
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)


class UserSavedSchemesFilterView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = SchemePagination

    def post(self, request, *args, **kwargs):
        user = request.user
        saved_schemes = user.saved_schemes.all()

        logger.debug(f"User: {user}, Saved Schemes: {saved_schemes}")

        search_query = request.data.get('q', None)
        state_ids = request.data.get('state_ids', [])
        department_ids = request.data.get('department_ids', [])
        sponsor_ids = request.data.get('sponsor_ids', [])
        beneficiary_keywords = request.data.get('beneficiary_keywords', [])

        logger.debug(f"Search Query: {search_query}, State IDs: {state_ids}, Department IDs: {department_ids}, Sponsor IDs: {sponsor_ids}, Beneficiary Keywords: {beneficiary_keywords}")

        # Convert state_ids and department_ids to integers if they are provided
        if state_ids:
            state_ids = [int(id) for id in state_ids]
        if department_ids:
            department_ids = [int(id) for id in department_ids]

        # Filter by search query
        if search_query:
            saved_schemes = saved_schemes.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(sponsors__sponsor_type__icontains=search_query)
            )
            logger.debug(f"Filtered by Search Query: {saved_schemes}")

        # Filter by state IDs
        if state_ids:
            saved_schemes = saved_schemes.filter(department__state_id__in=state_ids)
            logger.debug(f"Filtered by State IDs: {saved_schemes}")

        # Filter by department IDs
        if department_ids:
            saved_schemes = saved_schemes.filter(department_id__in=department_ids)
            logger.debug(f"Filtered by Department IDs: {saved_schemes}")
        
        # Filter by sponsor IDs
        if sponsor_ids:
            saved_schemes = saved_schemes.filter(sponsors__id__in=sponsor_ids)
            logger.debug(f"Filtered by Sponsor IDs: {saved_schemes}")

        # Filter by beneficiary keywords
        if beneficiary_keywords:
            beneficiary_filters = Q()
            for keyword in beneficiary_keywords:
                beneficiary_filters |= Q(beneficiaries__beneficiary_type__icontains=keyword)
            saved_schemes = saved_schemes.filter(beneficiary_filters)
            logger.debug(f"Filtered by Beneficiary Keywords: {saved_schemes}")

        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(saved_schemes, request)
        
        if page is not None:
            serializer = SchemeSerializer(page, many=True)
            logger.debug(f"Paginated Data: {serializer.data}")
            return paginator.get_paginated_response(serializer.data)

        # Fallback if pagination is not applied
        serializer = SchemeSerializer(saved_schemes, many=True)
        logger.debug(f"Non-Paginated Data: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_200_OK)

class SchemeReportViewSet(viewsets.ModelViewSet):
    queryset = SchemeReport.objects.all()
    serializer_class = SchemeReportSerializer
    permission_classes = [permissions.IsAuthenticated]  # Ensure only authenticated users can access

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AllSchemeReportsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        reports = SchemeReport.objects.all()
        serializer = SchemeReportSerializer(reports, many=True)
        return Response(serializer.data)


class WebsiteFeedbackViewSet(viewsets.ModelViewSet):
    queryset = WebsiteFeedback.objects.all()
    serializer_class = WebsiteFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated] 

class AllWebsiteFeedbackView(APIView):
    permission_classes = [AllowAny] 

    def get(self, request):
        feedbacks = WebsiteFeedback.objects.all()
        serializer = WebsiteFeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)


class RecommendSchemesAPIView(APIView):
    def get(self, request, scheme_id):
        try:
            scheme = Scheme.objects.get(id=scheme_id)
        except Scheme.DoesNotExist:
            return Response({'detail': 'Scheme not found'}, status=404)

        cosine_sim = load_cosine_similarity()

        recommended = recommend_schemes(scheme.id, cosine_sim, top_n=10)

        response_data = []
        for item in recommended:
            scheme_data = SchemeSerializer(item['scheme']).data
            scheme_data['score'] = item['score']
            response_data.append(scheme_data)

        return Response({
            'scheme': SchemeSerializer(scheme).data,
            'recommended_schemes': response_data
        })

    

class HybridRecommendationView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = SchemePagination
    ordering_fields = ['title']

    def get(self, request, *args, **kwargs):
        user = request.user
        top_n = int(request.query_params.get('top_n', 10))

        state_ids = request.query_params.getlist('state_ids')
        department_ids = request.query_params.getlist('department_ids')
        beneficiary_keywords = request.query_params.getlist('beneficiary_keywords')
        sponsor_ids = request.query_params.getlist('sponsor_ids')
        funding_pattern = request.query_params.get('funding_pattern', None)
        search_query = request.query_params.get('search_query', None)
        tag = request.query_params.get('tag', None)
        ordering = request.query_params.getlist('ordering') or self.ordering_fields

        user_profile = request.query_params.get('user_profile', {})
        if isinstance(user_profile, str):
            import json
            try:
                user_profile = json.loads(user_profile)
            except:
                user_profile = {}

        user_tags = []

        profile_field_mappings = {
            "community": ["sc", "st", "obc", "general"],
            "minority": ["muslim", "christian", "sikh", "buddhist", "parsi", "jain"],
            "education": ["undergraduate", "postgraduate", "phd", "school"],
            "disability": ["physical", "visual", "hearing", "intellectual"],
            "occupation": ["farmer", "student", "teacher", "entrepreneur", "laborer"],
            "income": ["bpl", "middle", "high"]
        }

        for field, possible_tags in profile_field_mappings.items():
            field_value = user_profile.get(field, "").lower()
            if field_value in possible_tags:
                user_tags.append(field_value)

        scheme_filters = Q(department__is_active=True, department__state__is_active=True, is_active=True)

        if tag:
            scheme_filters &= Q(tags__name__icontains=tag)

        if user_tags:
            tag_filters = Q()
            for user_tag in user_tags:
                tag_filters |= Q(tags__name__icontains=user_tag)
            scheme_filters &= tag_filters

        if tag == "job":
            scheme_filters &= Q(tags__name__icontains='job') | Q(tags__name__icontains='employment')
        if tag == "scholarship":
            scheme_filters &= Q(tags__name__icontains='scholarship')
        if state_ids:
            scheme_filters &= Q(department__state_id__in=state_ids)
        if department_ids:
            scheme_filters &= Q(department_id__in=department_ids)
        if beneficiary_keywords:
            beneficiary_filters = Q()
            for keyword in beneficiary_keywords:
                beneficiary_filters |= Q(beneficiaries__beneficiary_type__icontains=keyword)
            scheme_filters &= beneficiary_filters
        if sponsor_ids:
            scheme_filters &= Q(sponsors__id__in=sponsor_ids)
        if funding_pattern:
            scheme_filters &= Q(funding_pattern__icontains=funding_pattern)
        if search_query:
            scheme_filters &= Q(title__icontains=search_query) | Q(description__icontains=search_query)

        feedback = WebsiteFeedback.objects.filter(user=user).order_by('-created_at').first()
        keywords = extract_keywords_from_feedback(feedback.description) if feedback else None

        recommended_schemes = collaborative_recommendations(user.id, top_n=top_n, keywords=keywords)
        state_based_schemes = Scheme.objects.filter(department__state=user.state_of_residence)
        all_recommendations = list(set(recommended_schemes) | set(state_based_schemes))

        recommended_filtered = Scheme.objects.filter(pk__in=[s.id for s in all_recommendations]).filter(scheme_filters).distinct()

        remaining_schemes = Scheme.objects.filter(scheme_filters).exclude(id__in=recommended_filtered.values_list('id', flat=True)).distinct()

        final_schemes = list(recommended_filtered) + list(remaining_schemes)

        if ordering:
            final_schemes.sort(key=lambda x: getattr(x, ordering[0].lstrip('-')), reverse=ordering[0].startswith('-'))

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(final_schemes, request)
        if page is not None:
            serializer = SchemeSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SchemeSerializer(final_schemes, many=True)
        return Response(serializer.data)

    

class UnifiedSchemesAPIView(APIView):
    pagination_class = SchemePagination
    ordering_fields = ['title']
    permission_classes = [AllowAny]

    def get_data_source(self, request):
        return request.data if request.method == "POST" else request.query_params

    def get_user_tags(self, user_profile):
        profile_field_mappings = {
            "community": ["sc", "st", "obc", "general"],
            "minority": ["muslim", "christian", "sikh", "buddhist", "parsi", "jain"],
            "education": ["undergraduate", "postgraduate", "phd", "school"],
            "disability": ["physical", "visual", "hearing", "intellectual"],
            "occupation": ["farmer", "student", "teacher", "entrepreneur", "laborer"],
            "income": ["bpl", "middle", "high"]
        }

        user_tags = []
        for field, tags in profile_field_mappings.items():
            value = user_profile.get(field, "").lower()
            if value in tags:
                user_tags.append(value)
        return user_tags

    def apply_filters(self, data, user_tags):
        from django.db.models import Q
        
        state_ids = data.get("state_ids", [])
        department_ids = data.get("department_ids", [])
        beneficiary_keywords = data.get("beneficiary_keywords", [])
        sponsor_ids = data.get("sponsor_ids", [])
        funding_pattern = data.get("funding_pattern")
        search_query = data.get("search_query")
        tag = data.get("tag")

        scheme_filters = Q(department__is_active=True, department__state__is_active=True, is_active=True)

        if tag:
            scheme_filters &= Q(tags__name__icontains=tag)

        if user_tags:
            tag_filters = Q()
            for user_tag in user_tags:
                tag_filters |= Q(tags__name__icontains=user_tag)
            scheme_filters &= tag_filters

        if tag == "job":
            scheme_filters &= Q(tags__name__icontains='job') | Q(tags__name__icontains='employment')
        if tag == "scholarship":
            scheme_filters &= Q(tags__name__icontains='scholarship')
        if state_ids:
            scheme_filters &= Q(department__state_id__in=state_ids)
        if department_ids:
            scheme_filters &= Q(department_id__in=department_ids)
        if beneficiary_keywords:
            bf_filter = Q()
            for keyword in beneficiary_keywords:
                bf_filter |= Q(beneficiaries__beneficiary_type__icontains=keyword)
            scheme_filters &= bf_filter
        if sponsor_ids:
            scheme_filters &= Q(sponsors__id__in=sponsor_ids)
        if funding_pattern:
            scheme_filters &= Q(funding_pattern__icontains=funding_pattern)
        if search_query:
            scheme_filters &= Q(title__icontains=search_query) | Q(description__icontains=search_query)

        return scheme_filters

    def handle_request(self, request):
        user = request.user if request.user.is_authenticated else None
        data = self.get_data_source(request)
        ordering = data.get("ordering", self.ordering_fields)
        top_n = int(data.get("top_n", 10))

        user_profile = data.get("user_profile", {})
        if isinstance(user_profile, str):
            import json
            try:
                user_profile = json.loads(user_profile)
            except:
                user_profile = {}

        user_tags = self.get_user_tags(user_profile)
        scheme_filters = self.apply_filters(data, user_tags)

        recommended_schemes = []
        if user:
            feedback = WebsiteFeedback.objects.filter(user=user).order_by('-created_at').first()
            keywords = extract_keywords_from_feedback(feedback.description) if feedback else None

            collaborative_schemes = collaborative_recommendations(user.id, top_n=top_n, keywords=keywords)
            state_based = Scheme.objects.filter(department__state=user.state_of_residence)
            all_recommended = list(set(collaborative_schemes) | set(state_based))

            recommended_schemes = Scheme.objects.filter(pk__in=[s.id for s in all_recommended]).filter(scheme_filters).distinct()

        excluded_ids = [s.id for s in recommended_schemes]
        other_schemes = Scheme.objects.filter(scheme_filters).exclude(id__in=excluded_ids).distinct()

        final_schemes = list(recommended_schemes) + list(other_schemes)

        if ordering:
            final_schemes.sort(key=lambda x: getattr(x, ordering[0].lstrip('-')), reverse=ordering[0].startswith('-'))

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(final_schemes, request)
        if page is not None:
            serializer = SchemeSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SchemeSerializer(final_schemes, many=True)
        return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        return self.handle_request(request)

    def post(self, request, *args, **kwargs):
        return self.handle_request(request)




class SaveSchemeInteractionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, scheme_id, *args, **kwargs):
        user = request.user
        scheme = Scheme.objects.get(id=scheme_id)
        
        interaction, created = UserInteraction.objects.get_or_create(
            user=user,
            scheme=scheme,
            defaults={'interaction_value': 2.0}
        )
        
        if not created:
            interaction.interaction_value = 2.0 if interaction.interaction_value != 2.0 else 0.0
            interaction.save()

        serializer = UserInteractionSerializer(interaction)
        
        return Response(
            {"message": "Scheme saved" if interaction.interaction_value == 2.0 else "Save removed", "interaction": serializer.data},
            status=status.HTTP_200_OK
        )
    

class ViewSchemeInteractionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, scheme_id, *args, **kwargs):
        user = request.user
        scheme = Scheme.objects.get(id=scheme_id)

        interaction, created = UserInteraction.objects.get_or_create(
            user=user,
            scheme=scheme,
            defaults={'interaction_value': 1.0}
        )

        if not created:
            interaction.interaction_value += 1.0
            interaction.save()

        serializer = UserInteractionSerializer(interaction)
        return Response(
            {"message": "Interaction recorded", "interaction": serializer.data},
            status=status.HTTP_200_OK
        )
    

class SchemeFeedbackCreateView(generics.CreateAPIView):
    queryset = SchemeFeedback.objects.all()
    serializer_class = SchemeFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SchemeFeedbackListView(generics.ListAPIView):
    serializer_class = SchemeFeedbackSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        scheme_id = self.kwargs['scheme_id']
        return SchemeFeedback.objects.filter(scheme_id=scheme_id)

class TrackEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        serializer = UserEventSerializer(data=data)
        if serializer.is_valid():
            UserEvent.objects.create(
                user=request.user,
                scheme_id=serializer.validated_data['scheme'].id,
                event_type=serializer.validated_data['event_type']
            )
            return Response({"message": "Event tracked successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LayoutItemViewSet(viewsets.ViewSet):

    def list(self, request):
        """Return the current layout order."""
        filteredItem = LayoutItem.objects.filter(is_active = True)
        layout_items = filteredItem.order_by("order")
        serializer = LayoutItemSerializer(layout_items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["POST"])
    def update_order(self, request):
        """Update the column order."""
        data = request.data 
        
        for item in data:
            try:
                layout_item = LayoutItem.objects.get(id=item["id"])
                layout_item.order = item["order"]
                layout_item.save()
            except LayoutItem.DoesNotExist:
                return Response({"error": f"LayoutItem with id {item['id']} not found"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Order updated successfully"})
    

class UserEventsViewSet(viewsets.ModelViewSet):
    queryset = UserEvents.objects.all().order_by('-timestamp')
    serializer_class = UserEventsSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def log_event(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        data['timestamp'] = now()
        data['ip_address'] = request.META.get('REMOTE_ADDR')
        data['user_agent'] = request.META.get('HTTP_USER_AGENT')

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Event logged successfully"}, status=201)
        return Response(serializer.errors, status=400)
    

@api_view(['GET'])
def get_event_stats(request):
    state = request.GET.get('state', None)
    events = UserEvents.objects.all()

    if state:
        events = events.filter(details__state=state)

    stats = (
        events.values("event_type")
        .annotate(count=Count("event_type"))
        .order_by("-count")
    )
    return Response(stats)

@api_view(["GET"])
def get_event_timeline(request):
    from_date = request.GET.get("from", None)
    to_date = request.GET.get("to", None)
    range_type = request.GET.get("range", None)
    state = request.GET.get("state", None)

    if from_date and to_date:
        from_date = parse_date(from_date)
        to_date = parse_date(to_date)
        if not from_date or not to_date:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)
    else:
        today = now().date()
        if range_type == "weekly":
            from_date = today - timedelta(weeks=4)
        elif range_type == "monthly":
            from_date = today - timedelta(days=90)
        elif range_type == "quarterly":
            from_date = today - timedelta(days=90)
        elif range_type == "halfyearly":
            from_date = today - timedelta(days=182)
        elif range_type == "annual":
            from_date = today - timedelta(days=365)
        else:
            from_date = today - timedelta(days=30)
        to_date = today

    timeline_query = UserEvents.objects.filter(timestamp__date__range=[from_date, to_date])

    if state:
        timeline_query = timeline_query.filter(details__state=state)

    if range_type == "weekly":
        trunc_func = TruncWeek("timestamp")
    elif range_type in ["monthly", "quarterly", "halfyearly", "annual"]:
        trunc_func = TruncMonth("timestamp")
    else:
        trunc_func = TruncDay("timestamp")

    timeline = (
        timeline_query.annotate(period=trunc_func)
        .values("period")
        .annotate(
            views=Count("id", filter=Q(event_type="view")),
            searches=Count("id", filter=Q(event_type="search")),
            downloads=Count("id", filter=Q(event_type="download")),
            filters=Count("id", filter=Q(event_type="filter")),
        )
        .order_by("period")
    )

    return Response(timeline)


@api_view(["GET"])
def get_event_by_range(request):
    range_type = request.GET.get("type")
    month = request.GET.get("month")
    year = request.GET.get("year")
    state = request.GET.get("state", None)

    today = now().date()

    if range_type not in ["weekly", "monthly", "quarterly", "halfyearly", "annual"]:
        return Response({"error": "Invalid or missing 'type'. Must be weekly, monthly, quarterly, halfyearly, annual."}, status=400)

    try:
        if range_type == "monthly":
            if not month or not year:
                return Response({"error": "Please provide 'month' and 'year' for monthly range."}, status=400)
            month = int(month)
            year = int(year)
            _, last_day = monthrange(year, month)
            from_date = date(year, month, 1)
            to_date = date(year, month, last_day)
        
        elif range_type == "weekly":
            if not year or not month:
                return Response({"error": "Please provide 'month' and 'year' for weekly range."}, status=400)
            month = int(month)
            year = int(year)
            from_date = date(year, month, 1)
            to_date = from_date + timedelta(weeks=1) - timedelta(days=1)
            if to_date.month != month:
                to_date = date(year, monthrange(year, month)[1])
        
        elif range_type == "quarterly":
            if not year or not month:
                return Response({"error": "Please provide 'month' and 'year' to identify quarter."}, status=400)
            month = int(month)
            year = int(year)
            quarter = ((month - 1) // 3) + 1
            start_month = 3 * (quarter - 1) + 1
            from_date = date(year, start_month, 1)
            _, last_day = monthrange(year, start_month + 2)
            to_date = date(year, start_month + 2, last_day)
        
        elif range_type == "halfyearly":
            if not year or not month:
                return Response({"error": "Please provide 'month' and 'year' to identify half year."}, status=400)
            month = int(month)
            year = int(year)
            if month <= 6:
                from_date = date(year, 1, 1)
                to_date = date(year, 6, 30)
            else:
                from_date = date(year, 7, 1)
                to_date = date(year, 12, 31)
        
        elif range_type == "annual":
            if not year:
                return Response({"error": "Please provide 'year' for annual range."}, status=400)
            year = int(year)
            from_date = date(year, 1, 1)
            to_date = date(year, 12, 31)

    except ValueError:
        return Response({"error": "Invalid month or year format."}, status=400)


    timeline_query = UserEvents.objects.filter(timestamp__date__range=[from_date, to_date])

    if state:
        timeline_query = timeline_query.filter(details__state=state)


    if range_type == "weekly":
        trunc_func = TruncDay("timestamp")
    elif range_type == "monthly":
        trunc_func = TruncDay("timestamp")
    else:
        trunc_func = TruncMonth("timestamp")

    timeline = (
        timeline_query.annotate(period=trunc_func)
        .values("period")
        .annotate(
            views=Count("id", filter=Q(event_type="view")),
            searches=Count("id", filter=Q(event_type="search")),
            downloads=Count("id", filter=Q(event_type="download")),
            filters=Count("id", filter=Q(event_type="filter")),
        )
        .order_by("period")
    )

    return Response(timeline)



@api_view(["GET"])
def get_popular_schemes(request):
    limit = int(request.GET.get("limit", 10))
    event_type = request.GET.get("event_type", "view")
    state = request.GET.get("state")

    schemes_query = UserEvents.objects.filter(event_type=event_type)
    if state:
        schemes_query = schemes_query.filter(details__state=state)

    schemes = (
        schemes_query.values("scheme_id")
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )

    scheme_ids = [s["scheme_id"] for s in schemes]
    scheme_map = {s.id: s.title for s in Scheme.objects.filter(id__in=scheme_ids)}

    scheme_details = [
        {
            "scheme_id": scheme["scheme_id"],
            "title": scheme_map.get(scheme["scheme_id"], "Unknown"),
            "count": scheme["count"],
        }
        for scheme in schemes
    ]

    return Response(scheme_details)



@api_view(["GET"])
def get_filter_usage(request):
    state = request.GET.get("state", None)

    filter_query = UserEvents.objects.filter(event_type="filter")
    
    if state:
        filter_query = filter_query.filter(details__state=state)

    filters = (
        filter_query.values("details__filter", "details__value")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    return Response(filters)


@api_view(["GET"])
def get_popular_searches(request):
    limit = int(request.GET.get("limit", 10))
    state = request.GET.get("state", None)

    search_query = UserEvents.objects.filter(event_type="search")

    if state:
        search_query = search_query.filter(details__state=state)

    searches = (
        search_query.values("details__query")
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )

    return Response(searches)




@api_view(["GET"])
def get_popular_clicks(request):
    limit = int(request.GET.get("limit", 5))
    state = request.GET.get("state", None)

    click_query = UserEvents.objects.filter(event_type="click")

    if state:
        click_query = click_query.filter(details__state=state)

    clicks = (
        click_query.values("details__url")
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )

    return Response(clicks)

@api_view(["GET"])
def get_user_summary(request):
    user_id = request.GET.get("user_id")

    if not user_id:
        return Response({"error": "User ID is required"}, status=400)

    if not CustomUser.objects.filter(id=user_id).exists():
        return Response({"error": "Invalid User ID"}, status=400)

    user_events = UserEvents.objects.filter(user_id=user_id)

    stats = (
        user_events.values("event_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    user_data = {
        "total_events": user_events.count(),
        "event_breakdown": stats,
    }

    return Response(user_data)



@api_view(["GET"])
def get_user_popular_schemes(request):
    user_id = request.GET.get("user_id")
    limit = int(request.GET.get("limit", 5))

    if not user_id:
        return Response({"error": "User ID is required"}, status=400)

    if not CustomUser.objects.filter(id=user_id).exists():
        return Response({"error": "Invalid User ID"}, status=400)

    scheme_interactions = (
        UserEvents.objects.filter(user_id=user_id, scheme__isnull=False) 
        .values("scheme_id")
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )

    scheme_ids = [entry["scheme_id"] for entry in scheme_interactions]
    schemes = {scheme.id: scheme.title for scheme in Scheme.objects.filter(id__in=scheme_ids)}

    scheme_details = [
        {
            "scheme_id": scheme["scheme_id"],
            "title": schemes.get(scheme["scheme_id"], "Unknown Scheme"),  
            "count": scheme["count"],
        }
        for scheme in scheme_interactions
    ]

    return Response(scheme_details)


@api_view(["GET"])
def get_user_event_timeline(request):
    user_id = request.GET.get("user_id", None)
    from_date = request.GET.get("from", None)
    to_date = request.GET.get("to", None)
    range_type = request.GET.get("range", None)

    if not user_id:
        return Response({"error": "user_id is required"}, status=400)

    if not CustomUser.objects.filter(id=user_id).exists():
        return Response({"error": "Invalid user_id"}, status=400)

    if from_date and to_date:
        from_date = parse_date(from_date)
        to_date = parse_date(to_date)
        if not from_date or not to_date:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)
    else:
        today = now().date()
        if range_type == "weekly":
            from_date = today - timedelta(weeks=4)
        elif range_type == "monthly":
            from_date = today - timedelta(days=90)
        elif range_type == "quarterly":
            from_date = today - timedelta(days=90)
        elif range_type == "halfyearly":
            from_date = today - timedelta(days=182)
        elif range_type == "annual":
            from_date = today - timedelta(days=365)
        else:
            from_date = today - timedelta(days=30)
        to_date = today

    if range_type == "weekly":
        trunc_func = TruncWeek("timestamp")
    elif range_type in ["monthly", "quarterly", "halfyearly", "annual"]:
        trunc_func = TruncMonth("timestamp")
    else:
        trunc_func = TruncDate("timestamp") 

    timeline_query = UserEvents.objects.filter(
        user_id=user_id,
        timestamp__date__range=[from_date, to_date]
    )

    timeline = (
        timeline_query.annotate(period=trunc_func)
        .values("period")
        .annotate(
            views=Count("id", filter=Q(event_type="view")),
            searches=Count("id", filter=Q(event_type="search")),
            downloads=Count("id", filter=Q(event_type="download")),
            clicks=Count("id", filter=Q(event_type="apply")),
        )
        .order_by("period")
    )

    return Response(timeline)



@api_view(["GET"])
def get_user_search_history(request):
    user_id = request.GET.get("user_id")
    limit = int(request.GET.get("limit", 10))

    if not user_id:
        return Response({"error": "User ID is required"}, status=400)

    if not CustomUser.objects.filter(id=user_id).exists():
        return Response({"error": "Invalid User ID"}, status=400)

    searches = (
        UserEvents.objects.filter(user_id=user_id, event_type="search")
        .values("details__query")
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )

    return Response(searches)



@api_view(["GET"])
def get_user_click_history(request):
    user_id = request.GET.get("user_id")
    limit = int(request.GET.get("limit", 5))

    if not user_id:
        return Response({"error": "User ID is required"}, status=400)

    if not CustomUser.objects.filter(id=user_id).exists():
        return Response({"error": "Invalid User ID"}, status=400)

    clicks = (
        UserEvents.objects.filter(user_id=user_id, event_type="click")
        .values("details__url")
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )

    return Response(clicks)


@api_view(["GET"])
def get_user_filter_usage(request):
    user_id = request.GET.get("user_id")

    if not user_id:
        return Response({"error": "User ID is required"}, status=400)

    if not CustomUser.objects.filter(id=user_id).exists():
        return Response({"error": "Invalid User ID"}, status=400)

    filters = (
        UserEvents.objects.filter(user_id=user_id, event_type="filter")
        .values("details__filter", "details__value")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    return Response(filters)



@api_view(["GET"])
def get_user_download_history(request):
    user_id = request.GET.get("user_id")
    limit = int(request.GET.get("limit", 5))

    if not user_id:
        return Response({"error": "User ID is required"}, status=400)

    if not CustomUser.objects.filter(id=user_id).exists():
        return Response({"error": "Invalid User ID"}, status=400)

    downloads = (
        UserEvents.objects.filter(user_id=user_id, event_type="download")
        .values("scheme_id", "timestamp")
        .order_by("-timestamp")[:limit]
    )

    scheme_details = [
        {
            "scheme_id": download["scheme_id"],
            "title": Scheme.objects.get(id=download["scheme_id"]).title,
            "download_time": download["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        }
        for download in downloads
    ]

    return Response(scheme_details)





class SchemeLinkListView(ListAPIView):
    serializer_class = SchemeLinkSerializer

    def get_queryset(self):
        subquery = Scheme.objects.filter(department__state=OuterRef('department__state')) \
                                .order_by('id') \
                                .values('id')[:1]

        return Scheme.objects.filter(id=Subquery(subquery, output_field=IntegerField())) \
                            .select_related('department__state')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = [
            {"state_name": scheme.department.state.state_name, "resource_url": scheme.scheme_link}
            for scheme in queryset
        ]
        return Response(data)
class SchemeLinkByStateView(ListAPIView):
    serializer_class = SchemeLinkSerializer

    def get_queryset(self):
        state_id = self.kwargs.get('state_id')
        state = get_object_or_404(State, id=state_id)
        return Scheme.objects.filter(department__state=state).select_related('department__state').only(
            'scheme_link', 'pdf_url', 'department__state__state_name'
        )
    
class SuperuserLoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(username=username)

            if not user.is_superuser:
                return Response({"error": "Only superusers can log in"}, status=status.HTTP_403_FORBIDDEN)

            if not user.check_password(password):
                return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)

            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                "access_token": str(access_token),
                "refresh_token": str(refresh),
                "user_id": user.id,
                "username": user.username
            })

        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class FAQViewSet(viewsets.ModelViewSet):
    serializer_class = FAQSerializer
    def get_queryset(self):
        if self.action == 'list':
            return FAQ.objects.filter(is_active=True).order_by("order")
        return FAQ.objects.all().order_by("order")
    
    def get_permissions(self):
        if self.action in ['list']:
            return [AllowAny()] 
        return [IsAdminUser()]

class CompanyMetaDetailView(generics.RetrieveUpdateAPIView):
    queryset = CompanyMeta.objects.all()
    serializer_class = CompanyMetaSerializer

    def get_object(self):
        return CompanyMeta.objects.first() 


class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        state_id = self.kwargs.get("state_id")
        
        if state_id:
            state = State.objects.filter(id=state_id, is_active=True).first()

            if state:
                return Resource.objects.filter(state_name=state)
            return Resource.objects.none()

        active_states = State.objects.filter(is_active=True)
        return Resource.objects.filter(state_name__in=active_states)

class AnnouncementListView(generics.ListAPIView):
    queryset = Announcement.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = AnnouncementSerializer


@api_view(['POST'])
def send_manual_email(request):
    try:
        data = json.loads(request.POST.get("data", "{}"))  # Parse JSON from form-data
    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=400)

    subject = data.get("subject")
    message = data.get("message")
    recipient_email = data.get("recipient_email")
    attachment = request.FILES.get("attachment")  # Get the uploaded file

    if not all([subject, message, recipient_email]):
        return Response({"error": "Missing fields"}, status=400)

    email = EmailMessage(subject, message, settings.EMAIL_FROM, [recipient_email])

    if attachment:
        email.attach(attachment.name, attachment.read(), attachment.content_type)  # Attach the file

    try:
        email.send(fail_silently=False)
        return Response({"message": "Email sent successfully"}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    

class UserListView(APIView):

    def get(self, request, format=None):
        users = CustomUser.objects.all().values('id', 'username', 'name', 'email')

        return Response(users, status=status.HTTP_200_OK)

@csrf_exempt
def proxy_view(request):
    target_url = request.GET.get('url')
    if not target_url:
        return JsonResponse({'error': 'No URL provided'}, status=400)

    try:
        response = requests.get(target_url)
        return HttpResponse(response.content, status=response.status_code, content_type=response.headers.get('Content-Type', 'text/html'))
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)