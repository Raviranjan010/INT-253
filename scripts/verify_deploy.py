import argparse
from urllib.error import URLError
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description='Check the public LiveSchool deployment.')
    parser.add_argument('base_url')
    args = parser.parse_args()
    failed = False
    for path in ('health/', '', 'courses/', 'live/', 'community/', 'about/', 'accounts/login/',
                 'certificates/verify/', 'robots.txt', 'sitemap.xml'):
        try:
            with urlopen(f"{args.base_url.rstrip('/')}/{path}", timeout=75) as response:
                status = response.status
                print(f'/{path}: {status}')
                failed |= status != 200
        except (URLError, TimeoutError) as exc:
            print(f'/{path}: {exc}')
            failed = True
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
