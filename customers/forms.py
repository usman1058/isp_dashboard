from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User 
from django.contrib.auth import get_user_model


from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'description', 'amount']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Optional notes'}),
            'amount': forms.NumberInput(attrs={'min': '0'}),
        }
from django import forms
from .models import Customer, ServicePlan
from django.core.validators import FileExtensionValidator

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'join_date': forms.DateInput(attrs={'type': 'date'}),
            'service_installation_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'username': forms.TextInput(attrs={'placeholder': 'Will be generated from email if blank'}),
            'id_card_front': forms.ClearableFileInput(attrs={
                'accept': 'image/jpeg, image/png',
                'class': 'file-upload'
            }),
            'id_card_back': forms.ClearableFileInput(attrs={
                'accept': 'image/jpeg, image/png',
                'class': 'file-upload'
            }),
        }
        help_texts = {
            'username': 'Leave blank to auto-generate from email',
            'id_card_front': 'Upload front side of ID card (JPEG/PNG)',
            'id_card_back': 'Upload back side of ID card (JPEG/PNG)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service_plan'].queryset = ServicePlan.objects.filter(is_active=True)
        
        # Make ID card fields optional
        self.fields['id_card_front'].required = False
        self.fields['id_card_back'].required = False
        
        # Set up file validation
        self.fields['id_card_front'].validators = [
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ]
        self.fields['id_card_back'].validators = [
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ]
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            email = self.cleaned_data.get('email', '')
            username = email.split('@')[0] if email else ''
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')
        
        # Ensure username is unique
        if username and Customer.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            self.add_error('username', 'This username is already taken')
        
        return cleaned_data  
        
# forms.py
from django import forms
from .models import ReminderSchedule
from .models import Reminder

class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ['customer', 'due_date', 'scheduled_time', 'message']
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'message': forms.Textarea(attrs={'rows': 3}),
        }



class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['customer', 'payment_date', 'month_for', 'amount', 'method', 'received_by']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'month_for': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        customer = None

        if 'customer' in self.initial:
            customer = self.initial['customer']
            # Convert int to object if needed
            if isinstance(customer, int):
                customer = Customer.objects.filter(pk=customer).first()

        elif self.instance and self.instance.customer_id:
            customer = self.instance.customer

        if customer and customer.service_plan:
            self.fields['amount'].initial = customer.service_plan.price

class ServicePlanForm(forms.ModelForm):
    class Meta:
        model = ServicePlan
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


from django import forms
from .models import Customer

class BulkStatusUpdateForm(forms.Form):
    customers = forms.ModelMultipleChoiceField(
        queryset=Customer.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=True
    )
    new_status = forms.ChoiceField(
        choices=Customer.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customers'].queryset = Customer.objects.order_by('last_name', 'first_name')