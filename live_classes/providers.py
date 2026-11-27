from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone


@dataclass(frozen=True)
class Conference:
    join_url: str = ''
    script_url: str = ''
    domain: str = ''
    room: str = ''
    token: str = ''


class ExternalLinkProvider:
    def conference(self, session, user) -> Conference:
        return Conference(join_url=session.meeting_url if session.meeting_url.startswith('https://') else '')


class SelfHostedJitsiProvider:
    def conference(self, session, user) -> Conference:
        domain = settings.JITSI_DOMAIN
        if not domain or domain.lower() == 'meet.jit.si':
            return Conference()
        room = f'liveschool-{session.pk.hex}'
        return Conference(script_url=f'https://{domain}/external_api.js', domain=domain, room=room)


class JaaSProvider:
    def conference(self, session, user) -> Conference:
        import jwt

        room = f'liveschool-{session.pk.hex}'
        app_id = settings.JAAS_APP_ID
        now = timezone.now()
        token = jwt.encode({
            'aud': 'jitsi', 'iss': 'chat', 'sub': app_id, 'room': room,
            'nbf': now - timedelta(seconds=30), 'exp': now + timedelta(minutes=10),
            'context': {
                'user': {
                    'id': str(user.pk), 'name': user.get_full_name() or user.username,
                    'moderator': user.pk == session.instructor_id and (user.is_instructor or user.is_staff),
                },
                'features': {'livestreaming': False, 'recording': False, 'transcription': False},
            },
        }, settings.JAAS_PRIVATE_KEY, algorithm='RS256', headers={'kid': settings.JAAS_KID})
        return Conference(script_url=f'https://8x8.vc/{app_id}/external_api.js',
                          domain='8x8.vc', room=f'{app_id}/{room}', token=token)


def get_conference(session, user) -> Conference:
    if not session.is_live_now:
        return Conference()
    if session.meeting_url:
        return ExternalLinkProvider().conference(session, user)
    if settings.JAAS_APP_ID:
        return JaaSProvider().conference(session, user)
    return SelfHostedJitsiProvider().conference(session, user)
