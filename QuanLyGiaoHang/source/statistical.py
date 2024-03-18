from django.http import HttpResponse
from django.template import loader
from .models import *
from django.db.models import Count,Sum
from django.db.models.functions import ExtractMonth, ExtractDay


def statistical(request):
    revenues_by_month = [0] * 12
    orders_by_month = [0] * 12
    revenues_by_day = [0] * 31
    orders_by_day = [0] * 31
    orders = Post.objects.annotate(month=ExtractMonth('created_date')).values('month').annotate(
        total_orders=Count('id'))
    revenues = Post.objects.annotate(month=ExtractMonth('created_date')).values('month').annotate(
        total_revenues=Sum("price"))
    ordersDay = Post.objects.annotate(day=ExtractDay('created_date')).values('day').annotate(
        total_orders=Count('id'))
    revenuesDay = Post.objects.annotate(day=ExtractDay('created_date')).values('day').annotate(
        total_revenues=Sum("price"))
    for item in orders:
        orders_by_month[item['month'] - 1] = item['total_orders']
    for item in revenues:
        revenues_by_month[item['month'] - 1] = item['total_revenues']
    for item in ordersDay:
        orders_by_day[item['day'] - 1] = item['total_orders']
    for item in revenuesDay:
        revenues_by_day[item['day'] - 1] = item['total_revenues']
    template = loader.get_template('statistical.html')
    context = {
      'orders_by_month': orders_by_month,
      'orders_by_day': orders_by_day,
      'revenues_by_day': revenues_by_day,
      'revenues_by_month': revenues_by_month
    }
    return HttpResponse(template.render(context, request))
