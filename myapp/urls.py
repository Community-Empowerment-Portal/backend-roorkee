from django.urls import path
from .views import UserProfileAPIView
from .views import RecommendationsAPIView


from .views import (
    StateListAPIView,
    StateDetailAPIView,
    DepartmentListAPIView,
    OrganisationListAPIView,
    SchemeListAPIView,
    SchemeDetailAPIView,
    BeneficiaryListAPIView,
    SchemeBeneficiaryListAPIView,
    BenefitListAPIView,
    CriteriaListAPIView,
    ProcedureListAPIView,
    DocumentListAPIView,
    SchemeDocumentListAPIView,
    SponsorListAPIView,
    SchemeSponsorListAPIView,
    StateDepartmentsListAPIView,  
    DepartmentSchemesListAPIView, 
    SchemeBeneficiariesListAPIView, 
    SchemeCriteriaListAPIView,  
    SchemeProceduresListAPIView,  
    SchemeDocumentsListAPIView,  
    SchemeSponsorsListAPIView ,
    StateSchemesListAPIView
)

urlpatterns = [
    path('states/', StateListAPIView.as_view(), name='state-list'),
    path('states/<int:pk>/', StateDetailAPIView.as_view(), name='state-detail'),
    path('departments/', DepartmentListAPIView.as_view(), name='department-list'),
    path('organisations/', OrganisationListAPIView.as_view(), name='organisation-list'),
    path('schemes/', SchemeListAPIView.as_view(), name='scheme-list'),
    path('schemes/<int:pk>/', SchemeDetailAPIView.as_view(), name='scheme-detail'),
    path('beneficiaries/', BeneficiaryListAPIView.as_view(), name='beneficiary-list'),
    path('scheme-beneficiaries/', SchemeBeneficiaryListAPIView.as_view(), name='scheme-beneficiary-list'),
    path('benefits/', BenefitListAPIView.as_view(), name='benefit-list'),
    path('criteria/', CriteriaListAPIView.as_view(), name='criteria-list'),
    path('procedures/', ProcedureListAPIView.as_view(), name='procedure-list'),
    path('documents/', DocumentListAPIView.as_view(), name='document-list'),
    path('scheme-documents/', SchemeDocumentListAPIView.as_view(), name='scheme-document-list'),
    path('sponsors/', SponsorListAPIView.as_view(), name='sponsor-list'),
    path('scheme-sponsors/', SchemeSponsorListAPIView.as_view(), name='scheme-sponsor-list'),
    path('states/<int:state_id>/departments/', StateDepartmentsListAPIView.as_view(), name='state-departments-list'),  # Add the new URL pattern
    path('departments/<int:department_id>/schemes/', DepartmentSchemesListAPIView.as_view(), name='department-schemes-list'),  # Add the new URL pattern
    path('schemes/<int:scheme_id>/beneficiaries/', SchemeBeneficiariesListAPIView.as_view(), name='scheme-beneficiaries-list'),  # Add the new URL pattern
    path('schemes/<int:scheme_id>/criteria/', SchemeCriteriaListAPIView.as_view(), name='scheme-criteria-list'),  # Add the new URL pattern
    path('schemes/<int:scheme_id>/procedures/', SchemeProceduresListAPIView.as_view(), name='scheme-procedures-list'),  # Add the new URL pattern
    path('schemes/<int:scheme_id>/documents/', SchemeDocumentsListAPIView.as_view(), name='scheme-documents-list'),  # Add the new URL pattern
    path('schemes/<int:scheme_id>/sponsors/', SchemeSponsorsListAPIView.as_view(), name='scheme-sponsors-list'),  # Add the new URL pattern
    path('states/<int:state_id>/schemes/', StateSchemesListAPIView.as_view(), name='state-schemes-list'),  
    path('profile/', UserProfileAPIView.as_view(), name='profile_api'),
    path('recommendations/', RecommendationsAPIView.as_view(), name='recommendations'),

   
    # path('profile/', UserProfileDetail.as_view(), name='profile-detail'),
    # path('profile/update/', UserProfileUpdate.as_view(), name='profile-update'),

]

