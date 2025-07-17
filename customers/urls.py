from django.urls import path
from .views import (
    CustomerListView, CustomerDetailView, CustomerCreateView, CustomerUpdateView, CustomerDeleteView,
    PaymentListView, PaymentDetailView, PaymentCreateView, PaymentUpdateView, PaymentDeleteView,
    ServicePlanListView, ServicePlanDetailView, ServicePlanCreateView, ServicePlanUpdateView, ServicePlanDeleteView,
    dashboard
)
from reports.views import *
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('expenses/', expense_dashboard, name='expense_dashboard'),
    path('reports/expenses/', expense_monthly_report_view, name='expense_report'),
    path('payments/<int:pk>/challan/', payment_challan_view, name='payment_challan'),
    path('ajax_send_reminder/', ajax_send_reminder, name='ajax_send_reminder'),
    # Customer URLs
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/new/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer_delete'),
    path("ajax/send-reminder/", ajax_send_reminder, name="ajax_send_reminder"),
    path("reminders/list/", list_reminders_view, name="reminder_list"),
    path("reminders/delete/<int:reminder_id>/", delete_reminder_view, name="reminder_delete"),
    path('send_whatsapp_reminder/', send_whatsapp_reminder, name='send_whatsapp_reminder'),






    # Payment URLs
    path('payments/', PaymentListView.as_view(), name='payment_list'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/new/', PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/edit/', PaymentUpdateView.as_view(), name='payment_update'),
    path('payments/<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),
    path('payments/status/', payment_status_view, name='payment_status'),
     
    # ServicePlan URLs
    path('service-plans/', ServicePlanListView.as_view(), name='service_plan_list'),
    path('service-plans/<int:pk>/', ServicePlanDetailView.as_view(), name='service_plan_detail'),
    path('service-plans/new/', ServicePlanCreateView.as_view(), name='service_plan_create'),
    path('service-plans/<int:pk>/edit/', ServicePlanUpdateView.as_view(), name='service_plan_update'),
    path('service-plans/<int:pk>/delete/', ServicePlanDeleteView.as_view(), name='service_plan_delete'),
    path('payments/add/<int:customer_id>/<int:year>/<int:month>/', prefilled_payment_form, name='payment_add_prefilled'),


    
     # Reports
    path('reports/monthly-payments/', monthly_payment_report, name='monthly_payment_report'),
    path('reports/customer-growth/', customer_growth_report, name='customer_growth_report'),
    path('reports/revenue-analysis/', revenue_analysis_report, name='revenue_analysis_report'),
    
    # Bulk operations
    path('customers/bulk-status/', BulkStatusUpdateView.as_view(), name='bulk_status_update'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
