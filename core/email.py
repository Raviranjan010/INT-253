import json
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        delivered = 0
        for message in email_messages:
            payload = {
                'from': message.from_email, 'to': message.to,
                'subject': message.subject, 'text': message.body,
            }
            if message.reply_to:
                payload['reply_to'] = message.reply_to
            request = Request(
                'https://api.resend.com/emails', data=json.dumps(payload).encode(),
                headers={'Authorization': f'Bearer {settings.RESEND_API_KEY}', 'Content-Type': 'application/json'},
            )
            try:
                with urlopen(request, timeout=8):
                    delivered += 1
            except (URLError, TimeoutError):
                logger.warning('Resend delivery failed.')
                if not self.fail_silently:
                    raise
        return delivered
