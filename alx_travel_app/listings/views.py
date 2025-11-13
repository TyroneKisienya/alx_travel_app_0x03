from django.shortcuts import render
from .models import Listing, Booking, Payment
from .serializers import ListingSerializers, BookingSerializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
import requests
import os
from rest_framework.decorators import api_view
from django.conf import settings
from dotenv import load_dotenv
from .tasks import send_booking_confirmation_email

load_dotenv()

# Create your views here.

class Listingview(APIView):
    def get(self, request, pk=None):
        if pk:
            try:
                listing = Listing.objects.get(pk=pk)
                serializer = ListingSerializers(listing)
                return Response(serializer.data)
            except Listing.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            
        listing = Listing.objects.all()
        serializer = ListingSerializers(listing, many = True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ListingSerializers(data=request.data)
        if serializer.is_valid:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        try:
            listing = Listing.objects.get(pk=pk)
        except Listing.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = ListingSerializers(data = request.data)
        if serializer.is_valid:
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            listing = Listing.objects.get(pk=pk)
            listing.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except listing.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)     

@api_view(["POST"])
def initiate_payment(request):
    amount = request.data.get("amount")
    user = request.user

    payment = Payment.objects.create(
        user = user,
        amount = amount,
        status = "Pending"
    )
    url = f"{os.getenv('CHAPA_BASE_URL')}/initialize"

    payload = {
        "amount": str(amount),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "tx_ref": str(payment.reference),
        "currency": "KES",
        "callback_url": "https://alxprodev.com/api//payments/verify/",
        "return_url": "https://alxprodev/payment-success",
    }

    headers = {
        "Authorization": f"Bearer{os.getenv('CHAPA_SECRET_KEY')}",
    }

    response = requests.post(url, json=payload, headers=headers)
    chapa_respone = response.json()

    if "Status" in chapa_respone and chapa_respone["status"] == "success":
        payment.transaction_id = chapa_respone["data"]["tx_ref"]
        payment.save()

        return Response({
            "payment_url": chapa_respone["data"]["checkout_url"],
            "reference": payment.reference
        })
    return Response({"error": "Failed to initiate"}, status=400)

@api_view(["GET"])
def verify_payment(request, reference):
    url = f"{os.getenv('CHAPA_BASE_URL')}/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {os.getenv('CHAPA_SECRET_KEY')}",
    }

    response = requests.get(url, headers=headers)
    chapa_response = response.json()

    try:
        payment = Payment.objects.get(reference=reference)
    except Payment.DoesNotExist:
        return Response ({"error": "Payment not found"}, status=404)
    
    if chapa_response["status"] =="success":
        payment.status = "Completed"
        payment.save()

        return Response ({"message": "Payment verified successfully!"})
    payment.status = "Failed"
    payment.save()

    return Response({"error": "Payment verification failed"}, status=400)

class BookingViewset(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializers

    def perform_create(self, serializer):
        booking = serializer.save()

        customer_email = booking.user.email
        booking_details = (
            f"Booking ID: {booking.id}\n"
            f"Listing: {booking.listing.name}\n"
            f"Check-in: {booking.check_in}\n"
            f"Check-out: {booking.check_out}\n"
            f"Total: KES {booking.total_amount}"
        )

        send_booking_confirmation_email.delay(customer_email, booking_details)