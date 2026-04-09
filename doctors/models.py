from django.db import models
from django.conf import settings


class Doctor(models.Model):
    SPECIALIZATION_CHOICES = [
        ('General Physician', 'General Physician'),
        ('Cardiologist', 'Cardiologist'),
        ('Pulmonologist', 'Pulmonologist'),
        ('Endocrinologist', 'Endocrinologist'),
        ('Neurologist', 'Neurologist'),
        ('Orthopedist', 'Orthopedist'),
        ('Dermatologist', 'Dermatologist'),
        ('Gastroenterologist', 'Gastroenterologist'),
        ('Nephrologist', 'Nephrologist'),
        ('Psychiatrist', 'Psychiatrist'),
    ]
    name = models.CharField(max_length=200)
    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES)
    hospital_name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    years_experience = models.PositiveIntegerField(default=0)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    city = models.CharField(max_length=100, default='')
    rating = models.FloatField(default=4.0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    is_available = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='doctors/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.name} - {self.specialization}"
