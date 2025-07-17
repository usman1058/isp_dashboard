# templatetags/month_filters.py
from django import template
import calendar

register = template.Library()

@register.filter
def get_month_name(month_number):
    return calendar.month_name[int(month_number)]

@register.filter
def to_range(start, end):
    return range(start, end + 1)
