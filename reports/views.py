from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from customers.models import Payment, Customer
import calendar
from openpyxl import Workbook
from django.db.models.functions import TruncMonth
from dateutil.relativedelta import relativedelta
from django.db.models.functions import TruncMonth
import io
from collections import defaultdict
from django.db.models import Sum
from django.utils import timezone
from django.shortcuts import render
from customers.models import Payment
from collections import defaultdict

@login_required
def monthly_payment_report(request):
    # Default to current year if not specified
    year = int(request.GET.get('year', timezone.now().year))
    
    # Get monthly totals
    monthly_data = (
        Payment.objects
        .filter(payment_date__year=year)
        .values('payment_date__month')
        .annotate(total=Sum('amount'))
        .order_by('payment_date__month')
    )
    
    # Format data for chart
    months = [calendar.month_name[i] for i in range(1, 13)]
    monthly_totals = [0] * 12
    for data in monthly_data:
        monthly_totals[data['payment_date__month'] - 1] = float(data['total'])
    
    year_range = list(range(2020, timezone.now().year + 1))  # or any range you want

    context = {
        'year': year,
        'months': months,
        'monthly_totals': monthly_totals,
        'monthly_data': zip(months, monthly_totals),
        'total_year': sum(monthly_totals),
        'year_range': year_range,  # add this
    }


    
    if request.GET.get('export') == 'excel':
        return generate_monthly_payment_excel(year, monthly_totals, months)
    
    return render(request, 'reports/monthly_payments.html', context)

def generate_monthly_payment_excel(year, monthly_totals, months):
    output = io.BytesIO()
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = f"Monthly Payments {year}"
    
    # Add headers
    worksheet.append(['Month', 'Amount'])
    
    # Add data
    for month, amount in zip(months, monthly_totals):
        worksheet.append([month, amount])
    
    # Add total
    worksheet.append(['TOTAL', sum(monthly_totals)])
    
    workbook.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=monthly_payments_{year}.xlsx'
    return response



@login_required
def customer_growth_report(request):
    months_back = int(request.GET.get('months', 12))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30 * months_back)

    growth_data = (
        Customer.objects
        .filter(service_installation_date__range=[start_date, end_date])
        .annotate(month=TruncMonth('service_installation_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    months = []
    counts = []
    current = start_date.replace(day=1)

    while current <= end_date:
        label = current.strftime('%b %Y')
        months.append(label)
        count = next((d['count'] for d in growth_data if d['month'] == current), 0)
        counts.append(count)
        current += relativedelta(months=1)

    total_customers = Customer.objects.filter(service_installation_date__lte=end_date).count()

    return render(request, 'reports/customer_growth.html', {
        'months': months,
        'counts': counts,
        'selected_months': months_back,
        'total_customers': total_customers,
    })

@login_required
def revenue_analysis_report(request):
    year = int(request.GET.get('year', timezone.now().year))

    payments = Payment.objects.filter(payment_date__year=year).select_related('customer__service_plan')

    revenue_by_plan = defaultdict(float)
    for payment in payments:
        plan = payment.customer.service_plan
        if plan:
            revenue_by_plan[plan.name] += float(payment.amount)

    revenue_by_method = (
        payments
        .values('method')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    context = {
        'year': year,
        'revenue_by_plan': revenue_by_plan.items(),
        'revenue_by_method': revenue_by_method,
        'total_revenue': sum(revenue_by_plan.values()),
    }

    return render(request, 'reports/revenue_analysis.html', context)



from django.http import JsonResponse
from customers.models import ReminderSchedule
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime

@login_required
def list_reminders_view(request):
    reminders = ReminderSchedule.objects.filter(sent=False).select_related('customer')
    data = [{
        "id": r.id,
        "customer": str(r.customer),
        "due_date": r.due_date.strftime("%Y-%m-%d"),
        "send_time": localtime(r.send_time).strftime("%H:%M %d %b"),
        "message": r.message
    } for r in reminders]
    return JsonResponse({"reminders": data})

@csrf_exempt
@login_required
def delete_reminder_view(request, reminder_id):
    try:
        ReminderSchedule.objects.get(id=reminder_id, sent=False).delete()
        return JsonResponse({"success": True})
    except ReminderSchedule.DoesNotExist:
        return JsonResponse({"success": False, "error": "Reminder not found"})
