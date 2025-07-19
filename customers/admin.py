from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Customer

class CustomerResource(resources.ModelResource):
    class Meta:
        model = Customer
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ['username']  # Use email as unique identifier
        fields = ('first_name', 'last_name', 'username', 'phone', 'address', 'status')

@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):
    resource_class = CustomerResource
    list_display = ('first_name', 'last_name', 'username', 'phone', 'status')
    list_filter = ('status',)
    search_fields = ('first_name', 'last_name', 'username', 'phone')
    
    
    
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Permission
from django import forms

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
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': "Select multiple permissions using Ctrl/Cmd + Click"
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
from django.contrib import admin
from .models import Expense, ExpenseCategory

admin.site.register(Expense)
admin.site.register(ExpenseCategory)






