from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'country', 'city')
    search_fields = ('name', 'phone_number', 'email')
    list_filter = ('country', 'city')
