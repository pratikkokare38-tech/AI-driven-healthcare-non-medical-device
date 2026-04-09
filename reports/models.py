from django.db import models
from django.conf import settings
from doctors.models import Doctor


class ReportCard(models.Model):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('pdf', 'PDF'),
        ('other', 'Other'),
    ]
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=200, default='Medical Report')
    file = models.FileField(upload_to='reports/%Y/%m/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='pdf')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.patient.username} - {self.title} ({self.uploaded_at.strftime('%Y-%m-%d')})"

    def save(self, *args, **kwargs):
        if self.file:
            name = self.file.name.lower()
            if name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                self.file_type = 'image'
            elif name.endswith('.pdf'):
                self.file_type = 'pdf'
            else:
                self.file_type = 'other'
        super().save(*args, **kwargs)


class DoctorRecommendation(models.Model):
    report = models.ForeignKey(ReportCard, on_delete=models.CASCADE, related_name='recommendations')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    reason = models.TextField()
    match_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-match_score']

    def __str__(self):
        return f"Recommend Dr.{self.doctor.name} for {self.report.patient.username}"
