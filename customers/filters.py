# customers/filters.py
import django_filters
from .models import Customer
from django import forms

class CustomerFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Customer.STATUS_CHOICES)
    
    join_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Customer
        fields = ['status', 'join_date']
        
        
        # customers/filters.py
import django_filters
from django import forms
from django.db import models
from .models import Payment, Customer

class PaymentFilter(django_filters.FilterSet):
    payment_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Payment Date Range'
    )
    
    amount = django_filters.RangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control',
            'placeholder': 'Amount'
        })
    )
    
    method = django_filters.ChoiceFilter(
        choices=Payment.PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Custom customer filter that searches both first and last names
    customer = django_filters.CharFilter(
        method='filter_customer',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Customer name...'
        })
    )
    
    def filter_customer(self, queryset, name, value):
        return queryset.filter(
            models.Q(customer__first_name__icontains=value) |
            models.Q(customer__last_name__icontains=value)
        )
    
    received_by = django_filters.CharFilter(
        field_name='received_by__username',
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Received by...'
        })
    )
    
    invoice_number = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Invoice number...'
        })
    )

    class Meta:
        model = Payment
        fields = ['payment_date', 'amount', 'method', 'customer', 'received_by', 'invoice_number']
        
        
        
# customers/filters.py
import django_filters
from django import forms
from .models import ServicePlan

class ServicePlanFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Plan name...'
        })
    )
    
    speed = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Speed...'
        })
    )
    
    price = django_filters.RangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control',
            'placeholder': 'Price'
        })
    )
    
    is_active = django_filters.BooleanFilter(
        widget=forms.Select(choices=[(True, 'Active'), (False, 'Inactive')],
                          attrs={'class': 'form-select'})
    )

    class Meta:
        model = ServicePlan
        fields = ['name', 'speed', 'price', 'is_active']