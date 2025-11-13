from django.db import models
import uuid

# Create your models here.

class User(models.Model):
    class roleType(models.TextChoices):
        GUEST = 'guest', 'Guest'
        HOST = 'host', 'Host'
        ADMIN = 'admin', 'Admin'

    user = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    first_name = models.CharField(max_length=128, null= False)
    last_name = models.CharField(max_length=128, null= False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(unique=True, max_length=128)
    role = models.CharField(choices=roleType, max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
class Listing(models.Model):
    listing = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=128)
    location = models.CharField(max_length=128)
    pricepernight = models.DecimalField(decimal_places=2, max_digits=8)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Booking(models.Model):
    class statusType(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELED = 'canceled', 'Canceled'

    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing_id = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True, null=False)
    end_date = models.DateTimeField(auto_created=True, null = False)
    status = models.CharField(choices=statusType, max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    STATUS_CHOICES = [
        ("Pending", "pending"),
        ("Completed", "completed"),
        ("Failed", "failed"),
    ]    

    reference = models.UUIDField(uuid=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(null=False, max_length=128)
    status = models.CharField(choices = STATUS_CHOICES, max_length=20, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"