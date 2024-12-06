from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.exceptions import PermissionDenied
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

logger = logging.getLogger(__name__)

from .models import (
    State, Department, Organisation, Scheme, Beneficiary, SchemeBeneficiary, Benefit, 
    Criteria, Procedure, Document, SchemeDocument, Sponsor, SchemeSponsor, CustomUser,
    Banner, SavedFilter
)
from .serializers import (
    StateSerializer, DepartmentSerializer, OrganisationSerializer, SchemeSerializer, 
    BeneficiarySerializer, SchemeBeneficiarySerializer, BenefitSerializer, 
    CriteriaSerializer, ProcedureSerializer, DocumentSerializer, 
    SchemeDocumentSerializer, SponsorSerializer, SchemeSponsorSerializer, UserRegistrationSerializer,
    SaveSchemeSerializer, UserProfileSerializer, LoginSerializer, BannerSerializer, SavedFilterSerializer,
    PasswordResetConfirmSerializer, PasswordResetRequestSerializer
)

from rest_framework.exceptions import NotFound
from .filters import CustomOrderingFilter
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class SchemePagination(PageNumberPagination):
    page_size_query_param = 'limit'


class StateListAPIView(generics.ListAPIView):
    queryset = State.objects.all()
    serializer_class = StateSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'state_name']
    ordering = ['-created_at']

class StateSchemesListAPIView(generics.ListAPIView):
    serializer_class = SchemeSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['introduced_on', 'title']
    ordering = ['-introduced_on']
    pagination_class = SchemePagination

    def get_queryset(self):
        state_id = self.kwargs.get('state_id')
        if state_id:
            return Scheme.objects.filter(department__state_id=state_id)
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
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer 
    filter_backends = [OrderingFilter]
    ordering_fields = ['introduced_on', 'title']
    ordering = ['-introduced_on']
    pagination_class = SchemePagination

    def get_queryset(self):
        department_id = self.request.query_params.get('department_id')
        if department_id:
            return self.queryset.filter(department_id=department_id)
        return self.queryset.all()

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
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


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
                print(f"Scheme with id {scheme_id} does not exist")
                return Response({'error': f'Scheme with id {scheme_id} does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        user.save()
        print(f"User {user.username} unsaved schemes: {[scheme.id for scheme in removed_schemes]}")
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

class EducationChoicesView(APIView):
    def get(self, request):
        return Response(CustomUser._meta.get_field('education').choices, status=status.HTTP_200_OK)

class CategoryChoicesView(APIView):
    def get(self, request):
        return Response(CustomUser._meta.get_field('category').choices, status=status.HTTP_200_OK)

class EmploymentChoicesView(APIView):
    def get(self, request):
        return Response(CustomUser._meta.get_field('employment_status').choices, status=status.HTTP_200_OK)


def verify_email(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.save()
        return render(request, 'email_verified.html')
    else:
        return render(request, 'email_verification_failed.html')
    
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
        queryset = Scheme.objects.filter(tags__name__icontains='scholarship')
        state_ids_param = self.request.query_params.get('state_ids', '[]')

        try:
            # Remove square brackets and split by commas
            state_ids = state_ids_param.strip('[]').split(',')
            state_ids = [int(id.strip()) for id in state_ids if id.strip().isdigit()]
        except ValueError:
            state_ids = []

        if state_ids:
            queryset = queryset.filter(department__state_id__in=state_ids)

        return queryset

class JobSchemesListView(generics.ListAPIView):
    serializer_class = SchemeSerializer
    pagination_class = SchemePagination

    def get_queryset(self):
        queryset = Scheme.objects.filter(Q(tags__name__icontains='job') | Q(tags__name__icontains='employment'))
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


class SchemesByStatesAPIView(APIView):
    def post(self, request, *args, **kwargs):
        state_ids = request.data.get('state_ids', [])

        if not isinstance(state_ids, list):
            return Response({'error': 'state_ids must be a list'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch schemes associated with the provided state IDs
        schemes = Scheme.objects.filter(department__state__id__in=state_ids)

        # Serialize the schemes data
        serializer = SchemeSerializer(schemes, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class SchemesByStateAndDepartmentAPIView(APIView):
    def post(self, request, *args, **kwargs):
        state_id = request.data.get('state_id')
        department_name = request.data.get('department')

        if not state_id or not department_name:
            return Response({'error': 'state_id and department are required fields'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the state and department objects
            state = State.objects.get(id=state_id)
            department = Department.objects.get(state=state, department_name__iexact=department_name)

            # Fetch schemes associated with the department
            schemes = Scheme.objects.filter(department=department)

            # Serialize the schemes data
            serializer = SchemeSerializer(schemes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except State.DoesNotExist:
            return Response({'error': 'State not found'}, status=status.HTTP_404_NOT_FOUND)
        except Department.DoesNotExist:
            return Response({'error': 'Department not found in the given state'}, status=status.HTTP_404_NOT_FOUND)

# class SchemesByMultipleStatesAndDepartmentsAPIView(APIView):
#     pagination_class = SchemePagination

#     def post(self, request, *args, **kwargs):
#         # Combine data from both request.data (POST body) and query_params (GET query)
#         state_ids = request.data.get('state_ids', request.query_params.getlist('state_ids', []))
#         department_ids = request.data.get('department_ids', request.query_params.getlist('department_ids', []))
#         beneficiary_keywords = request.data.get('beneficiary_keywords', request.query_params.getlist('beneficiary_keywords', []))
#         sponsor_ids = request.data.get('sponsor_ids', request.query_params.getlist('sponsor_ids', []))
#         funding_pattern = request.data.get('funding_pattern', request.query_params.get('funding_pattern', None))
#         search_query = request.data.get('search_query', request.query_params.get('q', None))

#         scheme_filters = Q()

#         if state_ids:
#             scheme_filters &= Q(department__state_id__in=state_ids)
#         if department_ids:
#             scheme_filters &= Q(department_id__in=department_ids)
#         if beneficiary_keywords:
#             beneficiary_filters = Q()
#             for keyword in beneficiary_keywords:
#                 beneficiary_filters |= Q(beneficiaries__beneficiary_type__icontains=keyword)
#             scheme_filters &= beneficiary_filters
#         if sponsor_ids:
#             scheme_filters &= Q(sponsors__id__in=sponsor_ids)
#         if funding_pattern:
#             scheme_filters &= Q(funding_pattern__icontains=funding_pattern)
#         if search_query:
#             search_filters = Q(title__icontains=search_query) | Q(description__icontains=search_query)
#             scheme_filters &= search_filters

#         schemes = Scheme.objects.filter(scheme_filters).distinct()

#         # Paginate the queryset
#         paginator = self.pagination_class()
#         page = paginator.paginate_queryset(schemes, request)
#         if page is not None:
#             serializer = SchemeSerializer(page, many=True)
#             return paginator.get_paginated_response(serializer.data)

#         # Fallback if pagination is not applied
#         serializer = SchemeSerializer(schemes, many=True)
#         return Response(serializer.data)
        
class SchemesByMultipleStatesAndDepartmentsAPIView(APIView):
    pagination_class = SchemePagination
    ordering_fields = ['title']
    # ordering = ['-introduced_on']

    def post(self, request, *args, **kwargs):
        state_ids = request.data.get('state_ids', [])
        department_ids = request.data.get('department_ids', [])
        beneficiary_keywords = request.data.get('beneficiary_keywords', [])
        sponsor_ids = request.data.get('sponsor_ids', [])
        funding_pattern = request.data.get('funding_pattern', None)
        search_query = request.data.get('search_query', None)
        tag = request.data.get('tag', None)
        ordering = request.data.get('ordering', self.ordering_fields)  # Get ordering from request or use default

        scheme_filters = Q()

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

        schemes = Scheme.objects.filter(scheme_filters).distinct()

        # Apply ordering
        if ordering:
            schemes = schemes.order_by(*ordering)

        # Paginate the queryset
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(schemes, request)
        if page is not None:
            serializer = SchemeSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback if pagination is not applied
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

