from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView,
    UserLoginView,
    CustomerViewSet,
    LedgerEntryViewSet
)


router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'ledger-entries', LedgerEntryViewSet, basename='ledger-entry')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', UserLoginView.as_view(), name='login'),

    # Router URLs (ViewSets থেকে generate হয়েছে)
    path('', include(router.urls)),
]
