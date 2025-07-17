from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Customer, Payment, ServicePlan
from .forms import CustomerForm, PaymentForm, ServicePlanForm
from django.views.generic import FormView
from django.urls import reverse_lazy
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from django.contrib import messages
from .forms import BulkStatusUpdateForm
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import *
from .forms import *
from django.db.models import Sum  # Add this import
from django.views.generic import CreateView
from django.urls import reverse
from django_filters.views import FilterView
from .filters import *
import phonenumbers
from phonenumbers import PhoneNumberFormat


class ServicePlanListView(LoginRequiredMixin, FilterView):
    model = ServicePlan
    template_name = 'customers/serviceplan_list.html'
    context_object_name = 'serviceplans'
    paginate_by = 20
    filterset_class = ServicePlanFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = context['filter'].form
        return context
    
    
class ServicePlanDetailView(LoginRequiredMixin, DetailView):
    model = ServicePlan
    template_name = 'customers/serviceplan_detail.html'
    context_object_name = 'serviceplan'

class ServicePlanCreateView(LoginRequiredMixin, CreateView):
    model = ServicePlan
    form_class = ServicePlanForm
    template_name = 'customers/serviceplan_form.html'
    success_url = reverse_lazy('service_plan_list')

class ServicePlanUpdateView(LoginRequiredMixin, UpdateView):
    model = ServicePlan
    form_class = ServicePlanForm
    template_name = 'customers/serviceplan_form.html'
    success_url = reverse_lazy('service_plan_list')

class ServicePlanDeleteView(LoginRequiredMixin, DeleteView):
    model = ServicePlan
    template_name = 'customers/serviceplan_confirm_delete.html'
    success_url = reverse_lazy('service_plan_list')



class PaymentListView(LoginRequiredMixin, FilterView):
    model = Payment
    template_name = 'customers/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    filterset_class = PaymentFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('-payment_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = context['filter'].form
        return context
    
    
class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'customers/payment_detail.html'
    context_object_name = 'payment'

class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'customers/payment_form.html'
    success_url = reverse_lazy('payment_list')

    def form_valid(self, form):
        form.instance.received_by = self.request.user
        return super().form_valid(form)

from django.urls import reverse_lazy

class PaymentUpdateView(UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'customers/payment_form.html'

    def get_success_url(self):
        return reverse_lazy('payment_status')
    
class PaymentDeleteView(LoginRequiredMixin, DeleteView):
    model = Payment
    template_name = 'customers/payment_confirm_delete.html'
    success_url = reverse_lazy('payment_list')


class BulkStatusUpdateView(LoginRequiredMixin, FormView):
    template_name = 'customers/bulk_status_update.html'
    form_class = BulkStatusUpdateForm
    success_url = reverse_lazy('customer_list')
    
    def form_valid(self, form):
        customers = form.cleaned_data['customers']
        new_status = form.cleaned_data['new_status']
        
        updated_count = customers.update(status=new_status)
        
        messages.success(
            self.request,
            f'Successfully updated status for {updated_count} customers to {new_status}.'
        )
        return super().form_valid(form)

import django_filters
from django.db.models import Q
from .models import Customer

class CustomerFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Search')

    class Meta:
        model = Customer
        fields = []  # We won't use the default fields

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(email__icontains=value) |
            Q(phone__icontains=value)
        )


class CustomerListView(LoginRequiredMixin, FilterView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20
    filterset_class = CustomerFilter  # Add this line

    def get_queryset(self):
        # Sort by latest created (assuming higher ID means newer)
        queryset = super().get_queryset()
        return queryset.order_by('-id')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = context['filter'].form  # Pass the filter form to template
        return context
    
    

from dateutil.relativedelta import relativedelta
from django.views.generic.detail import DetailView
    
from datetime import date, timedelta
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from dateutil.relativedelta import relativedelta
from .models import Customer, Payment

class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object
        today = date.today()

        if customer.service_plan and customer.service_installation_date:
            start_date = customer.service_installation_date.replace(day=1)
            months_passed = (today.year - start_date.year) * 12 + (today.month - start_date.month) + 1

            # Payments mapped by month
            payments_by_month = {
                p.month_for.replace(day=1): p for p in customer.payments.all()
            }

            history = []
            paid_payments = []
            unpaid_payments = []
            upcoming_payments = []
            total_paid = 0

            for i in range(months_passed):
                month = (start_date + relativedelta(months=i)).replace(day=1)
                payment = payments_by_month.get(month)

                if payment:
                    status = 'Paid'
                    payment_date = payment.payment_date
                    action_url = reverse('payment_update', kwargs={'pk': payment.pk})
                    paid_payments.append(payment)
                    total_paid += payment.amount
                else:
                    status = 'Unpaid'
                    payment_date = None
                    action_url = reverse('payment_add_prefilled', kwargs={
                        'customer_id': customer.pk,
                        'year': month.year,
                        'month': month.month
                    })
                    # Check if upcoming (within next 7 days)
                    days_until_due = (month - today).days
                    if 0 <= days_until_due <= 7:
                        upcoming_payments.append({
                            'month': month,
                            'days_left': days_until_due
                        })

                    unpaid_payments.append(month)

                history.append({
                    'month': month,
                    'due_date': month,
                    'status': status,
                    'amount': customer.service_plan.price,
                    'payment_date': payment_date,
                    'action_url': action_url,
                })

            context.update({
                'payment_history': history,
                'paid_payments': paid_payments,
                'unpaid_payments': unpaid_payments,
                'upcoming_payments': upcoming_payments,
                'total_paid': total_paid,
            })

        return context

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customer_list')

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customer_list')

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')

# Similar views for Payment, ServicePlan, and CustomerService would follow
# Implement List, Detail, Create, Update, Delete views for each model

# views.py
from django.shortcuts import render
from datetime import date
from .models import Customer



@login_required
def payment_status_view(request):
    today = date.today()
    selected_month = request.GET.get('month')

    if selected_month:
        year, month = map(int, selected_month.split('-'))
    else:
        year = today.year
        month = today.month

    payments_done = Payment.objects.filter(month_for__year=year, month_for__month=month)
    payments_done_customers = payments_done.values_list('customer_id', flat=True)

    unpaid_customers = Customer.objects.exclude(id__in=payments_done_customers).filter(service_plan__isnull=False)

    unpaid_prepared = []
    for customer in unpaid_customers:
        unpaid_prepared.append({
            'customer': customer,
            'amount': customer.service_plan.price,
            'month_for': date(year, month, 1)
        })

    return render(request, 'customers/payment_status.html', {
        'payments_done': payments_done,
        'unpaid_data': unpaid_prepared,
        'month': date(year, month, 1),
        'year': year
    })

from django.db.models.functions import TruncMonth, TruncDate
from django.db.models import Sum
from datetime import date, datetime
from calendar import month_name
import json

@login_required
def expense_monthly_report_view(request):
    print("🔥 ENTERED expense_monthly_report_view")
    year = int(request.GET.get('year', date.today().year))
    month = request.GET.get('month')  # optional

    expenses = Expense.objects.filter(date__year=year)

    if month:
        month = int(month)
        expenses = expenses.filter(date__month=month)
        daily_data = (
            expenses.values('date')
            .annotate(total=Sum('amount'))
            .order_by('date')
        )
        labels = [entry['date'].strftime('%b %d') for entry in daily_data]
        values = [float(entry['total']) for entry in daily_data]
        graph_label = f'Daily Expenses for {month_name[month]} {year}'
        summary_data = [(entry['date'].strftime('%b %d'), entry['total']) for entry in daily_data]
    else:
        monthly_data = (
            expenses.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )
        labels = [entry['month'].strftime('%b') for entry in monthly_data]
        values = [float(entry['total']) for entry in monthly_data]
        graph_label = f'Monthly Expenses for {year}'
        summary_data = [(entry['month'].strftime('%B'), entry['total']) for entry in monthly_data]


        # ✅ DEBUG
    print("Expenses Count:", expenses.count())
    print("Labels:", labels)
    print("Values:", values)
    year_range = range(2022, date.today().year + 1)
    print("Year Range:", list(year_range))

    total_year = sum(values)
    year_range = range(2022, date.today().year + 1)  # Example: 2022 to 2025
    context = {
        'year': year,
        'month': month,
        'months': json.dumps(labels),               # for chart.js
        'monthly_totals': json.dumps(values),
        'graph_label': graph_label,
        'total_year': total_year,
        'monthly_data': summary_data,
        'year_range': year_range,
    }
    return render(request, 'expenses/expense_report.html', context)


from django.db.models.functions import TruncMonth
from django.db.models import Sum
from datetime import date, timedelta
import calendar
import json

def prefilled_payment_form(request, customer_id, year, month):
    customer = get_object_or_404(Customer, pk=customer_id)
    initial_data = {
        'customer': customer,
        'amount': customer.service_plan.price,
        'month_for': date(year, month, 1),
        'payment_date': date.today(),
    }

    form = PaymentForm(initial=initial_data)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            if not payment.invoice_number:
                import uuid
                payment.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
            payment.save()
            return redirect('payment_status')


    return render(request, 'customers/payment_form.html', {'form': form})

from django.shortcuts import render, redirect
from .models import Expense, ExpenseCategory
from .forms import ExpenseForm
from django.db.models import Sum

@login_required
def expense_dashboard(request):
    form = ExpenseForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('expense_dashboard')

    expenses = Expense.objects.select_related('category').order_by('-date')
    total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    category_totals = (
        Expense.objects.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    context = {
        'form': form,
        'expenses': expenses,
        'total_expense': total_expense,
        'category_totals': category_totals,
    }
    return render(request, 'expenses/expense_dashboard.html', context)



from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from .models import Customer, Payment
from dateutil.relativedelta import relativedelta
from datetime import timedelta

@login_required
def dashboard(request):
    today = timezone.now().date()
    year = today.year
    month = today.month

    # Calculate metrics
    total_customers = Customer.objects.count()
    
    # Current month payments
    current_month_payments = Payment.objects.filter(
        payment_date__year=year,
        payment_date__month=month
    )
    total_payments = current_month_payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Expected payments calculation
    active_customers = Customer.objects.filter(
        service_plan__isnull=False,
        status='active'
    )
    expected_payments = sum(
        customer.service_plan.price 
        for customer in active_customers 
        if customer.service_plan
    ) or 0
    
    # Collection percentage
    payment_collection_percentage = 0
    if expected_payments > 0:
        payment_collection_percentage = min(round((total_payments / expected_payments) * 100, 1), 100)

    # Recent payments
    recent_payments = Payment.objects.order_by('-payment_date')[:5]

    # Payment status
    paid_customers = []
    unpaid_customers = []
    for customer in Customer.objects.filter(service_plan__isnull=False):
        if customer.is_payment_done_for_month(year, month):
            paid_customers.append(customer)
        else:
            unpaid_customers.append(customer)

    # Upcoming due customers
    due_soon = []
    reminder_window = 7  # Show payments due within next 7 days

    for customer in Customer.objects.filter(
        service_plan__isnull=False,
        service_installation_date__isnull=False
    ).select_related('service_plan'):
        installation_date = customer.service_installation_date
        
        months_since = (today.year - installation_date.year) * 12 + \
                      (today.month - installation_date.month)
        next_due_date = installation_date + relativedelta(months=months_since)
        
        if next_due_date < today:
            next_due_date += relativedelta(months=1)
        
        show_from_date = next_due_date - timedelta(days=reminder_window)
        
        if show_from_date <= today <= next_due_date:
            if not customer.payments.filter(
                month_for__year=next_due_date.year,
                month_for__month=next_due_date.month
            ).exists():
                days_left = (next_due_date - today).days
                
                due_soon.append({
                    'customer': customer,
                    'due_date': next_due_date,
                    'due_month': next_due_date.strftime('%B %Y'),
                    'amount': customer.service_plan.price,
                    'days_left': days_left
                })

    context = {
        'upcoming_due_customers': due_soon,
        'total_customers': total_customers,
        'total_payments': total_payments,
        'expected_payments': expected_payments,
        'payment_collection_percentage': payment_collection_percentage,
        'recent_payments': recent_payments,
        'paid_count': len(paid_customers),
        'unpaid_count': len(unpaid_customers),
        'current_month': today.strftime('%B %Y')
    }

    return render(request, 'customers/dashboard.html', context)

import logging
import phonenumbers
from phonenumbers import PhoneNumberFormat
from datetime import datetime, timedelta
import time
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from urllib.parse import quote
import os
if os.environ.get("DISPLAY"):
    import pywhatkit


logger = logging.getLogger(__name__)

def format_phone(phone_raw, default_region="PK"):
    try:
        # First clean the phone number
        phone_clean = ''.join(filter(str.isdigit, str(phone_raw)))
        
        # Parse with phonenumbers library
        phone_obj = phonenumbers.parse(phone_clean, default_region)
        
        if not phonenumbers.is_valid_number(phone_obj):
            raise ValueError("Invalid phone number after parsing")
            
        # Format in E.164 format (e.g. +923001234567)
        formatted = phonenumbers.format_number(phone_obj, PhoneNumberFormat.E164)
        
        # Additional validation for Pakistani numbers
        if default_region == "PK" and not formatted.startswith('+92'):
            raise ValueError("Pakistani numbers must start with +92")
            
        return formatted
        
    except Exception as e:
        logger.error(f"Phone format error for {phone_raw}: {str(e)}")
        return None

@require_POST
@login_required
def ajax_send_reminder(request):  # This is the view function that receives request
    customer_id = request.POST.get("customer_id")
    due_date_str = request.POST.get("due_date")
    action_type = request.POST.get("action_type", "instant")
    send_time = request.POST.get("send_time")
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id)
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        
        if not customer.service_plan:
            return JsonResponse({'success': False, 'msg': 'Customer has no service plan'})
            
        # Call the utility function without request parameter
        result = send_whatsapp_reminder(
            customer=customer, 
            due_date=due_date, 
            amount=customer.service_plan.price,
            action_type=action_type,
            send_time=send_time
        )
        
        if result["status"] == "success":
            # Save to reminders
            reminder = Reminder.objects.create(
                customer=customer,
                due_date=due_date,
                reminder_type='whatsapp',
                scheduled_time=timezone.now() if action_type != "schedule" else datetime.strptime(send_time, "%Y-%m-%d %H:%M"),
                status='sent' if action_type != "schedule" else 'pending',
                message=result["message"]
            )
            
            response_data = {
                'success': True,
                'msg': 'WhatsApp message sent!' if action_type != "schedule" else f'Reminder scheduled for {send_time}',
                'scheduled': action_type == "schedule"
            }
            
            if action_type == "instant":
                response_data['url'] = result['url']
            elif action_type == "schedule":
                response_data['scheduled_time'] = result['scheduled_time']
                
            return JsonResponse(response_data)
        else:
            return JsonResponse({'success': False, 'msg': result["message"]})
            
    except Exception as e:
        return JsonResponse({'success': False, 'msg': str(e)})


# This is a utility function, not a view - no request parameter needed
def send_whatsapp_reminder(customer, due_date, amount, action_type="instant", send_time=None):
    try:
        # Validate and format phone number
        phone = format_phone(customer.phone, "PK")
        if not phone:
            raise ValueError("Invalid phone number format. Must be a valid Pakistani number starting with +92")
        
        # Prepare message
        message = (
            f"Dear {customer.first_name},\n\n"
            f"Your payment of ₹{amount} for {due_date.strftime('%B %Y')} is due.\n"
            f"Please make the payment at your earliest convenience.\n\n"
            f"Thank you!"
        )

        if action_type == "instant":
            encoded_message = quote(message)
            whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
            
            if len(whatsapp_url) > 2000:
                raise ValueError("Generated URL is too long")
                
            return {
                "status": "success",
                "url": whatsapp_url,
                "message": message
            }

        elif action_type == "automatic":
            now = datetime.now()
            send_time = now + timedelta(minutes=3)
            
            try:
                pywhatkit.close_tab(wait_time=2)
                time.sleep(2)
                pywhatkit.sendwhatmsg(
                    phone_no=phone,
                    message=message,
                    time_hour=send_time.hour,
                    time_min=send_time.minute,
                    wait_time=45,
                    tab_close=True,
                    close_time=5
                )
                time.sleep(10)
                return {"status": "success", "message": message}
            except Exception as e:
                raise ValueError(f"Automatic send failed: {str(e)}")

        elif action_type == "schedule":
            if isinstance(send_time, str):
                send_datetime = datetime.strptime(send_time, "%Y-%m-%d %H:%M")
            else:
                send_datetime = send_time
                
            if send_datetime <= datetime.now() + timedelta(minutes=30):
                raise ValueError("Scheduled time must be at least 30 minutes in future")
                
            pywhatkit.sendwhatmsg(
                phone_no=phone,
                message=message,
                time_hour=send_datetime.hour,
                time_min=send_datetime.minute,
                wait_time=30,
                tab_close=True,
                close_time=5
            )
            return {
                "status": "success",
                "scheduled_time": send_datetime.strftime("%Y-%m-%d %H:%M"),
                "message": message
            }

    except Exception as e:
        logger.error(f"WhatsApp send failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
@login_required
def payment_challan_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'customers/challan.html', {'payment': payment})



@require_POST
def ajax_schedule_reminder(request):
    customer_id = request.POST.get("customer_id")
    due_date_str = request.POST.get("due_date")
    time_str = request.POST.get("send_time")
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id)
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        send_time = datetime.strptime(time_str, "%H:%M").time()
        
        # Combine with today's date (or could use due_date)
        scheduled_datetime = datetime.combine(due_date, send_time)
        if timezone.is_naive(scheduled_datetime):
            scheduled_datetime = timezone.make_aware(scheduled_datetime)
            
        if not customer.service_plan:
            return JsonResponse({
                "success": False, 
                "msg": "Customer has no service plan"
            })
            
        Reminder.objects.create(
            customer=customer,
            due_date=due_date,
            reminder_type='whatsapp',
            scheduled_time=scheduled_datetime,
            status='pending',
            message=f"Scheduled payment reminder for {due_date.strftime('%B %Y')}"
        )
        
        return JsonResponse({
            "success": True, 
            "msg": f"Reminder scheduled for {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}"
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "msg": str(e)})

