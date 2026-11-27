import re
from urllib.parse import parse_qs, urlsplit


def embed_url(value: str) -> str:
    """Build an HTTPS embed URL from supported video identifiers only."""
    try:
        parsed = urlsplit(value)
        if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port:
            return ''
        host = parsed.hostname
    except ValueError:
        return ''
    path = parsed.path.strip('/').split('/')
    if host in {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be',
                'youtube-nocookie.com', 'www.youtube-nocookie.com'}:
        video_id = ''
        if host == 'youtu.be' and len(path) == 1:
            video_id = path[0]
        elif path == ['watch']:
            video_id = parse_qs(parsed.query).get('v', [''])[0]
        elif len(path) == 2 and path[0] in {'embed', 'shorts'}:
            video_id = path[1]
        if re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
            return f'https://www.youtube-nocookie.com/embed/{video_id}'
    if host in {'vimeo.com', 'www.vimeo.com', 'player.vimeo.com'}:
        if (len(path) == 1 or (len(path) == 2 and path[0] == 'video')) and re.fullmatch(r'[0-9]{1,16}', path[-1]):
            return f'https://player.vimeo.com/video/{path[-1]}'
    return ''
