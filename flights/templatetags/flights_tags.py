from django import template


register = template.Library()


@register.filter
def duration_format(hours):
    try:
        h = int(hours)
        minutes = int(round((hours - h) * 60))
        if h > 0 and minutes > 0:
            return '%dh %dmin' % (h, minutes)
        elif h > 0:
            return '%dh' % h
        else:
            return '%dmin' % minutes
    except (ValueError, TypeError):
        return str(hours)
