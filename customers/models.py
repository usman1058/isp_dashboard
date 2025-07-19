from datetime import date, timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

# customers/models.py
class ServicePlan(models.Model):
    name = models.CharField(max_length=100)
    speed = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_limit = models.PositiveIntegerField()  # GB
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import os

def customer_id_upload_path(instance, filename):
    # Uploads to: MEDRA_ROOT/customers/id_cards/<customer_id>/<filename>
    return os.path.join('customers', 'id_cards', str(instance.id), filename)

class Customer(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    # Basic Information
    username = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique username for customer login"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    join_date = models.DateField(default=timezone.now)
    
    # Contact Information
    phone = models.CharField(max_length=20)
    
    # Service Information
    service_plan = models.ForeignKey(
        'ServicePlan', 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True
    )
    service_installation_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    
    # ID Card Images
    id_card_front = models.ImageField(
        upload_to=customer_id_upload_path,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        verbose_name="ID Card Front",
        blank=True,
        null=True
    )
    id_card_back = models.ImageField(
        upload_to=customer_id_upload_path,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        verbose_name="ID Card Back",
        blank=True,
        null=True
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-join_date']
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        # Set username to email prefix if not provided
        if not self.username and self.first_name:
            self.username = self.first_name
        
        # Ensure username is unique
        if Customer.objects.filter(username=self.username).exclude(pk=self.pk).exists():
            raise ValueError("Username already exists")
            
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete associated ID card images when customer is deleted"""
        from django.core.files.storage import default_storage
        if self.id_card_front:
            default_storage.delete(self.id_card_front.path)
        if self.id_card_back:
            default_storage.delete(self.id_card_back.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def is_payment_done_for_month(self, year, month):
        return self.payments.filter(month_for__year=year, month_for__month=month).exists()
    
    def get_upcoming_due_dates(self, start_date, end_date):
        due_dates = []
        if self.service_installation_date:
            current_due = self.service_installation_date
            while current_due <= end_date:
                if current_due >= start_date:
                    due_dates.append(current_due)
                current_due += relativedelta(months=1)
        return due_dates

class Reminder(models.Model):
    REMINDER_TYPES = [
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    due_date = models.DateField()
    reminder_type = models.CharField(max_length=10, choices=REMINDER_TYPES, default='whatsapp')
    scheduled_time = models.DateTimeField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    is_bulk = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_time']
    
    def __str__(self):
        return f"Reminder for {self.customer} ({self.get_reminder_type_display()})"
    
class ReminderSchedule(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    due_date = models.DateField()
    send_time = models.DateTimeField()
    message = models.TextField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scheduled for {self.customer} at {self.send_time.strftime('%d %b %Y %H:%M')} (sent: {self.sent})"

class PaymentDue(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('customer', 'due_date')
        ordering = ['due_date']
        
    def __str__(self):
        return f"{self.customer} - {self.due_date} (₹{self.amount})"

class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('card', 'Credit Card'),
        ('mobile', 'Mobile Payment'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    month_for = models.DateField(default=date.today)  # month being paid for
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    received_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('customer', 'month_for')

    def __str__(self):
        return f"{self.customer} - {self.month_for.strftime('%B %Y')}"

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('card', 'Credit Card'),
        ('mobile', 'Mobile Payment'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_date = models.DateField()
    method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    received_by = models.ForeignKey(User, on_delete=models.PROTECT)
    notes = models.TextField(blank=True, null=True)
    invoice_number = models.CharField(max_length=20, unique=True)
    
    def save(self, *args, **kwargs):
        if not self.amount and self.customer.service_plan:
            self.amount = self.customer.service_plan.price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Payment #{self.invoice_number} - {self.customer}"
    
    
    
    
class PaymentReminder(models.Model):
        REMINDER_TYPES = [
            ('sms', 'SMS'),
        ]
        
        customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
        due_date = models.DateField()
        reminder_type = models.CharField(max_length=10, choices=REMINDER_TYPES)
        sent_at = models.DateTimeField(null=True, blank=True)
        is_sent = models.BooleanField(default=False)
        notes = models.TextField(blank=True)
        
        def __str__(self):
            return f"Reminder for {self.customer} - Due {self.due_date}"
        
        
        
from django.db import models

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - ₹{self.amount}"



class WhatsAppMessage(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    whatsapp_id = models.CharField(max_length=100, blank=True, null=True)  # WhatsApp's message ID
    error = models.TextField(blank=True, null=True)
