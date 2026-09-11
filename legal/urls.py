from django.urls import path
from .views import *

urlpatterns = [
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='PrivacyPolicyPage'),
    path('refund-policy/', RefundPolicyView.as_view(), name='RefundPolicyPage'),
    path('terms-condition/', TermsConditionView.as_view(), name='TermsConditionPage'),
    path('user-agreement/', UserAgreementView.as_view(), name='UserAgreementPage'),
]