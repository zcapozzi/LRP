
from datetime import datetime
import json
from decimal import Decimal


ISO_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

from google.appengine.ext.webapp import template
# ...
register = template.create_template_register()
import datetime
from google.appengine._internal.django.utils.safestring import mark_safe

def json_handler(obj):
	if callable(getattr(obj, 'to_json', None)):
		return obj.to_json()
	elif isinstance(obj, datetime.datetime):
		return obj.strftime(ISO_DATETIME_FORMAT)
	elif isinstance(obj, datetime.date):
		return obj.isoformat()
	elif isinstance(obj, datetime.time):
		return obj.strftime('%H:%M:%S')
	elif isinstance(obj, Decimal):
		return float(obj)  # warning, potential loss of precision
	else:
		return json.JSONEncoder().default(obj)


def to_json2(obj):
	def escape_script_tags(unsafe_str):
		# seriously: http://stackoverflow.com/a/1068548/8207
		return unsafe_str.replace('</script>', '<" + "/script>')

	# apply formatting in debug mode for ease of development
	indent = 2
	#return mark_safe(escape_script_tags(json.dumps(obj, default=json_handler, indent=indent)))
	return mark_safe((json.dumps(obj, default=json_handler )))

register.filter(to_json2)