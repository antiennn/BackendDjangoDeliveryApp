from django.contrib import admin
from .models import *


class CouponAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'created_date', 'updated_date', 'start_date', 'expiration_date', 'percent_discount', 'Minimum_price']
    date_hierarchy = 'expiration_date'
    search_fields = ['name']


admin.site.register(Coupon,CouponAdmin)

