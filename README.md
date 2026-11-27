# LiveSchool

LiveSchool is a Django learning platform with free course enrollment, lessons, progress, quizzes, live-class scheduling, discussions, and public certificate verification. A new database starts empty. The content bootstrap creates a subject taxonomy and can create an administrator using credentials you supply.

## Local setup

Use Python 3.12 and a virtual environment. Copy `.env.example` to `.env`, then run:

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py bootstrap_content --dry-run
python manage.py bootstrap_content
python manage.py createsuperuser
python manage.py runserver
```

Local development uses SQLite and local media by default. Override a system-provided `DEBUG` variable in your terminal if necessary. On PowerShell, use `$env:DEBUG = 'True'`.

## Configure Render

1. Back up the existing PostgreSQL database before deploying the migrations. Run the email-uniqueness preflight migration in staging if available. It stops with the conflicting account IDs instead of merging users.
2. Use an external PostgreSQL database. For Neon, open your project, choose **Connect**, and copy the connection URI into Render as `DATABASE_URL`. Keep SSL enabled. Neon has a free plan with usage limits. Render free web services idle, can take about a minute to wake, and have ephemeral disks. Render's free database is time-limited. [Render free limits](https://render.com/docs/free) · [Neon plans](https://neon.com/docs/introduction/plans)
3. Create a private S3-compatible bucket. In your storage provider's dashboard, create a key with access scoped to that bucket. Copy the access key ID, secret, region, and HTTPS endpoint into Render. AWS S3 can use its default endpoint. The app uses signed media URLs. [Storage backend options](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html)
4. On the **existing** Render Docker service, use the root Dockerfile and clear **Docker Command**. Set **Health Check Path** to `/health/`. Set the variables below before deploying the new commit. `render.yaml` describes equivalent settings for a new Blueprint service. The Docker build runs `build.sh`, and the container runs migrations before Gunicorn when enabled.
5. For first-time admin setup without a Render shell, set all three `ADMIN_*` variables and set `RUN_BOOTSTRAP=1` for the first deploy. After signing in to `/admin/`, remove the bootstrap password and the other two bootstrap credentials together. Leave `RUN_BOOTSTRAP=1` if you want idempotent category initialization.
6. Configure email if users should receive password resets. Verify your sending domain in Resend, generate a sending API key, and set `RESEND_API_KEY` and `DEFAULT_FROM_EMAIL` in Render. Set `CONTACT_NOTIFICATION_EMAIL` to receive contact-message alerts. Development uses the console backend. Without an API key, production has no outbound delivery. [Resend API](https://resend.com/docs/api-reference/emails/send-email)
7. For live video, paste an HTTPS meeting link when scheduling, or configure JaaS or a self-hosted Jitsi instance. For JaaS, create an API key in the JaaS console and enter its app ID, full key ID, and private PEM. Enable provider-side access controls on external meetings and self-hosted Jitsi. There is no embedded public `meet.jit.si` default. Confirm the provider's current quota before using it for classes. [JaaS API keys](https://developer.8x8.com/jaas/docs/jaas-console-api-keys/)
8. Deploy the latest commit and run `python scripts/verify_deploy.py https://YOUR-HOST`. Then test a learner login, an upload across restart, certificate issuance, email delivery, and a two-account video call. HTTP 200 alone does not verify those workflows.

| Variable | Production value |
| --- | --- |
| `DEBUG` | `False` |
| `SECRET_KEY` | Independent random secret, at least 50 characters |
| `CERTIFICATE_SIGNING_KEY` | Separate random key, at least 50 characters. Persist it across deploys. |
| `CERTIFICATE_LEGACY_SIGNING_KEY` | Original Django signing secret only if previously issued v1 certificates need verification |
| `DATABASE_URL` | PostgreSQL URI from your provider |
| `DATABASE_SSL_REQUIRE` | Defaults to `True` in production |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Exact public hostname and corresponding HTTPS origin |
| `MEDIA_BUCKET`, `MEDIA_ACCESS_KEY_ID`, `MEDIA_SECRET_ACCESS_KEY` | Private bucket and scoped credentials |
| `MEDIA_ENDPOINT_URL`, `MEDIA_REGION` | Provider endpoint and region |
| `RUN_MIGRATIONS`, `RUN_BOOTSTRAP` | `1` enables the corresponding startup operation |
| `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | First administrator credentials, used together only |
| `RESEND_API_KEY`, `DEFAULT_FROM_EMAIL`, `CONTACT_NOTIFICATION_EMAIL` | HTTPS email API key, verified sender, and optional notification recipient |
| `JAAS_APP_ID`, `JAAS_KID`, `JAAS_PRIVATE_KEY` | Optional JaaS credentials, supplied together |
| `JITSI_DOMAIN` | Optional hostname for a self-hosted conferencing service |
| `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` | Defaults to HTTPS redirect and one-year HSTS |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` | Opt in only after reviewing HTTPS coverage and preload implications |

Generate each secret separately with `python -c "import secrets; print(secrets.token_urlsafe(50))"`. Keep these values and database backups out of Git. To back up PostgreSQL, use a direct PostgreSQL connection URL with `pg_dump --format=custom --file=liveschool.dump "$DATABASE_URL"` in a secure shell. Test `pg_restore` into a separate database. Back up the object storage bucket separately.

The Compose files provide a local preview and an alternate Linux/Caddy setup. Use the Render path above for the hosted service.

## Administration and authoring

- In Django admin, approve an instructor application in **Users**. The bulk actions record approval changes in Django's admin history. Revoked instructors lose studio access.
- As an approved instructor, create a draft and open **Course studio**. Add modules and lessons, set their order, optionally add supported media, and publish when at least one lesson exists.
- Create a quiz and add questions with two to six choices and exactly one correct answer. Quizzes with recorded attempts are protected against studio edits and deletes.
- Schedule a class in IST. Open its room to start, end, cancel, or add a recording link after completing it. If your host supports scheduled tasks, run `python manage.py close_expired_classes` periodically.
- Run `python manage.py check_content_links` to check published lesson endpoints. An HTTP success is independent of playback availability or licensing. The bootstrap ships no externally sourced lessons.

## Checks and current limitations

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
coverage run --source=accounts,certificates,community,core,courses,live_classes,quizzes manage.py test
coverage report --omit='*/migrations/*,*/tests.py,*/test_*.py'
python manage.py check --deploy
```

The production check uses the actual environment. Opting out of HSTS subdomain coverage or preload can produce framework warnings. CSP is report-only while provider compatibility is tested. Quiz preview is pending. Newsletter email confirmation and unsubscribe work with a configured sender. Campaign delivery is separate. The room visit count measures learners opening an active classroom page. It does not measure attendance inside the video provider. Shared rate limiting across workers requires a shared cache and verified proxy IP handling. Production accessibility and performance scores have not been measured. See [project report](PROJECT_REPORT_INT253.md) and [architecture and permissions](docs/architecture.md).
