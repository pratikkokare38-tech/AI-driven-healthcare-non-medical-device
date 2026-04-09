from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random


class CustomUser(AbstractUser):
    role = models.CharField(max_length=10, default='patient', editable=False)
    phone = models.CharField(max_length=15, blank=True, unique=True, null=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male','Male'),('female','Female'),('other','Other')], blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    def is_patient(self):
        return True  # All users are patients


class PhoneVerification(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='phone_verification')
    phone = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        """Check if OTP is expired (valid for 10 minutes)"""
        expiry_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiry_time
    
    def generate_otp(self):
        """Generate a random 6-digit OTP"""
        self.otp = str(random.randint(100000, 999999))
        self.attempts = 0
        self.save()
        return self.otp
    
    def verify_otp(self, otp_input):
        """Verify the OTP"""
        if self.is_expired():
            return False, "OTP has expired"
        
        if self.attempts >= 3:
            return False, "Too many attempts"
        
        self.attempts += 1
        self.save()
        
        if self.otp == otp_input:
            self.is_verified = True
            self.save()
            self.user.phone_verified = True
            self.user.save()
            return True, "Phone verified successfully"
        
        return False, f"Invalid OTP. Attempts remaining: {3 - self.attempts}"
    
    def __str__(self):
        return f"Phone Verification for {self.user.username}"

