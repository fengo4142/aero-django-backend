from django.utils.translation import ugettext_lazy as _

def status_json(code, success, message, show_message=False):
    return {
            'status': {
                'code': code,
                'success': success,
                'message': _(message),
                'message_key': message.lower().replace(' ', '_'),
                'show_message': show_message
            }
        }
