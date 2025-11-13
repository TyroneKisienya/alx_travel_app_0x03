from django.urls import path
from .views import Listingview, initiate_payment, verify_payment

urlpatterns = [
    path('listing/',Listingview.as_view(), name='listing'),
    path('payments/initiate/', initiate_payment, name= "initiate_payment"),
    path('payment/verify/<str:reference>/', verify_payment, name= "verify_payment")
]