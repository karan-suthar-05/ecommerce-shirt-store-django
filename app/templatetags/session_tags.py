from django import template
from ..models import Company

register = template.Library()

@register.simple_tag(takes_context=True)
def display_and_flush_message(context):
    request = context['request']
    if 'msg' in request.session:
        message = request.session['msg']
        del request.session['msg']
        request.session.modified = True
        return message
    return ''

@register.simple_tag(takes_context=True)
def company_info(context):
    try:
        company = Company.objects.first()  # Assuming there is only one company instance
    except Company.DoesNotExist:
        company = None
    return company