from django.contrib import admin
from .models import Customer, LedgerEntry


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'user', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ['customer', 'type', 'amount', 'entry_date']
    list_filter = ['type', 'entry_date', 'customer']
    search_fields = ['customer__name', 'note']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'entry_date'