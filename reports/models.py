from django.db import models
from django.contrib.auth.models import User

class SavedReport(models.Model):
    REPORT_TYPES = [
        ('monthly_payments', 'Monthly Payments'),
        ('customer_growth', 'Customer Growth'),
        ('revenue_analysis', 'Revenue Analysis'),
    ]
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    parameters = models.JSONField()  # Store report filters/parameters
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    
    def __str__(self):
        return self.name