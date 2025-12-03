from django.urls import path
from .views import TermsContentAPIView

urlpatterns = [
    path('', TermsContentAPIView.as_view(), name='terms-content'),
]
