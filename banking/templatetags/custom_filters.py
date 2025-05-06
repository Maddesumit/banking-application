from django import template
import locale

register = template.Library()

@register.filter(name='indian_currency')
def indian_currency(number):
    """Convert a number to Indian currency format (e.g., 10,00,000.00)"""
    s = str(number)
    if '.' in s:
        whole, decimal = s.split('.')
    else:
        whole, decimal = s, '00'
        
    result = ''
    
    # Handle the whole part with Indian thousand separators
    length = len(whole)
    if length <= 3:
        return '₹' + whole + '.' + decimal
    else:
        # Add commas for thousands
        first_part = whole[:-3]
        last_part = whole[-3:]
        
        # Add commas after every 2 digits for the first part
        while first_part:
            if len(first_part) <= 2:
                result += first_part
                break
            else:
                result += first_part[:-2] + ','
                first_part = first_part[-2:]
        
        return '₹' + result + ',' + last_part + '.' + decimal