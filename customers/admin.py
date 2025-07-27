from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Permission
from django import forms
from .models import Customer, Expense, ExpenseCategory, Payment, ServicePlan, Reminder

# Customer Admin with Permissions
class CustomerResource(resources.ModelResource):
    class Meta:
        model = Customer
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ['username']
        fields = ('first_name', 'last_name', 'username', 'phone', 'address', 'status')

@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):
    resource_class = CustomerResource
    list_display = ('first_name', 'last_name', 'username', 'phone', 'status')
    list_filter = ('status',)
    search_fields = ('first_name', 'last_name', 'username', 'phone')
    
    def has_add_permission(self, request):
        return request.user.has_perm('customers.add_customer')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('customers.change_customer')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('customers.delete_customer')
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('customers.view_customer')

# Payment Admin with Permissions
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'payment_date', 'month_for')
    list_filter = ('payment_date', 'method')
    search_fields = ('customer__first_name', 'customer__last_name', 'invoice_number')
    
    def has_add_permission(self, request):
        return request.user.has_perm('customers.add_payment')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('customers.change_payment')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('customers.delete_payment')
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('customers.view_payment')

# ServicePlan Admin with Permissions
@admin.register(ServicePlan)
class ServicePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'speed', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'speed')
    
    def has_add_permission(self, request):
        return request.user.has_perm('customers.add_serviceplan')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('customers.change_serviceplan')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('customers.delete_serviceplan')
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('customers.view_serviceplan')

# Expense Admin with Permissions
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'description', 'amount', 'date')
    list_filter = ('category', 'date')
    search_fields = ('description',)
    
    def has_add_permission(self, request):
        return request.user.has_perm('customers.add_expense')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('customers.change_expense')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('customers.delete_expense')
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('customers.view_expense')

# ExpenseCategory Admin
@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    
    def has_add_permission(self, request):
        return request.user.has_perm('customers.add_expensecategory')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('customers.change_expensecategory')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('customers.delete_expensecategory')
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('customers.view_expensecategory')

# Reminder Admin with Permissions
@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'due_date', 'reminder_type', 'status')
    list_filter = ('reminder_type', 'status', 'due_date')
    search_fields = ('customer__first_name', 'customer__last_name')
    
    def has_add_permission(self, request):
        return request.user.has_perm('customers.add_reminder')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('customers.change_reminder')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('customers.delete_reminder')
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('customers.view_reminder')

# Custom User Admin with Improved Permission Display
class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        permissions = Permission.objects.select_related('content_type')
        grouped_permissions = {}

        for perm in permissions:
            app_label = perm.content_type.app_label
            grouped_permissions.setdefault(app_label, []).append(perm)

        grouped_choices = [
            (app_label, [(perm.id, f"{perm.content_type.model} | {perm.name}") for perm in perms])
            for app_label, perms in grouped_permissions.items()
        ]

        self.fields['user_permissions'].widget = forms.SelectMultiple(choices=grouped_choices)

class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    filter_horizontal = ('groups', 'user_permissions')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': "Select multiple permissions using Ctrl/Cmd + Click"
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')

# Unregister and re-register User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)