# INT-253: Live School for World-Class Free Education

> **Academic Problem Statement:**  
> *"Live School for World-Class Free Education: Creation of an online platform providing free access to world-class education for students across various demographics."*

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1-green.svg)](https://www.djangoproject.com/)
[![Tests](https://img.shields.io/badge/Automated%20Tests-38%20Passed%20(100%25)-brightgreen.svg)]()
[![Security](https://img.shields.io/badge/Security-Hardened%20(HMAC--SHA256)-blueviolet.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 🌟 Vision & Overview

**Live School** is a production-grade, accessible web platform built with Django 6.1 designed to eliminate financial, geographic, and demographic barriers to world-class higher education. It caters to rural learners, economically disadvantaged students, women in STEM, first-generation scholars, and neurodiverse learners.

The platform unites **synchronous WebRTC live classrooms**, modular curricula, interactive assessments, collaborative peer study circles, gamified learning incentives, and **cryptographically verifiable digital credentials**.

---

## 🛡️ Production Readiness & Security Remediation Summary

Following a comprehensive architectural audit, the following security and integrity controls are strictly enforced:

| Vulnerability / Flaw | Original Risk | Hardened Implementation & Verification |
| :--- | :--- | :--- |
| **Instructor Role Escalation** | Public registration granted immediate teacher privileges | Added `is_instructor_approved` field (`default=False`). Unapproved instructors retain student privileges until staff review. |
| **Demo Login Exposure** | Direct 1-click login allowed session bypass | Restricted strictly to `DEBUG=True`. Production (`DEBUG=False`) returns `403 Forbidden`. |
| **State-Changing GET Endpoints** | Logout, enrollment, completion, reviews, doubts, and upvotes triggered via GET | Converted all state-changing endpoints to **POST-only** with strict CSRF token validation and HTTP 405 guards. |
| **XP Farming Exploits** | Repeatedly toggling completion, upvotes, or refreshing live classes farmed XP | Introduced atomic `XPLedger` with `unique_together = ('user', 'action', 'reference_id')`. Duplicate rewards are atomically blocked. |
| **Misleading Certificate Hash** | Client-side integer hash labeled as "SHA-256 VERIFIED" | Replaced with genuine **server-side HMAC-SHA256 digital signatures** (`compute_digital_signature`) verified against `SECRET_KEY` with tamper detection. |
| **Fabricated Metrics** | Context processors reported fake static 12,500 students and 85 countries | Replaced entirely with **real database queries** (`CustomUser.objects.filter(...)`) accurately reflecting actual learners. |
| **Client-Only Quiz Limits** | Quiz timers and attempts relied solely on browser JavaScript | Implemented **server-side session timestamps**, max attempt limits (`max_attempts`), course enrollment checks, and single-correct-answer validation (`Choice.clean`). |
| **Classroom Access** | Unenrolled students could access course live rooms | Enforced course enrollment verification and instructor authorization before granting entry to live WebRTC sessions. |
| **Deployment & Settings** | Wildcard `ALLOWED_HOSTS`, insecure default secret key, missing Gunicorn | Configured environment-driven settings, modern `STORAGES` dictionary with Whitenoise, Gunicorn in `requirements.txt`, and production headers. |

---

## 🚀 Key Functional Modules

### 1. 🎓 Courses & Player
- Modular curriculum breakdown: Categories -> Courses -> Modules -> Lessons.
- Video lectures, study notes, and downloadable cheat sheets.
- Sequential navigation with progress percentage calculation.
- Course reviews with verified average ratings (returns `None` without reviews, eliminating synthetic 5.0 defaults).
- Complete instructor authoring lifecycle: Create, Edit, and Delete courses with ownership authorization.

### 2. 🔴 Synchronous WebRTC Live Classrooms
- Open-access live video classrooms powered by WebRTC / Jitsi Meet (no API keys required).
- Live video/audio, screen sharing, whiteboard, and hand raising.
- Enrolled-student access gating.
- Interactive doubt board with POST-only question posting and instructor answer workflow.
- Attendance XP granted once per session via atomic ledger.

### 3. ♿ Inclusive Demographics & Accessibility Toolbar
- Persistent text resizer (`A-`, `A`, `A+`).
- High-contrast toggle for low-vision and direct-sunlight readability.
- Dyslexia-friendly typography toggle.
- Reading focus ruler guide for ADHD and neurodiverse learners.
- Text-to-Speech (TTS) lecture reader.
- Low-bandwidth optimization for 2G/3G connectivity.

### 4. 📝 Assessments & Quizzes
- Pass percentage threshold validation.
- Configurable maximum attempt limits per student.
- Server-side time tracking preventing client-side timer manipulation.
- Model-level validation guaranteeing exactly one correct choice per question.

### 5. 🏆 Cryptographically Verifiable Digital Certificates
- Automatically awarded upon authentic 100% curriculum completion.
- Server computes HMAC-SHA256 digital signature over `student_id:course_id:certificate_id:issued_at`.
- Tamper detection verifies signature validity against server secret key.
- Public verification portal allows employers and academic institutions to verify authenticity by Certificate ID or Verification Hash.

### 6. 💬 Collaborative Q&A Community
- Peer study circle forums with search and resolution filtering.
- Thread authoring and reply workflows with gamified XP rewards.
- POST-only upvoting with self-vote prevention.
- Solution marking restricted to thread author or staff.

---

## 🧪 Automated Testing Suite

The project includes **38 comprehensive automated test methods** covering all 7 applications:

```bash
python manage.py test
```

### Coverage Breakdown:
1. **`accounts` (5 tests)**:
   - Student registration and welcome XP allocation.
   - Instructor registration requiring administrative approval.
   - Login streak tracking and date mathematics.
   - POST enforcement on logout route.
   - Atomic `XPLedger` prevention of duplicate reward farming.
2. **`core` (7 tests)**:
   - Accurate database statistics calculation without synthetic numbers.
   - Demographics impact view.
   - About page and problem statement verification.
   - Demo login disabled when `DEBUG=False` (returns 403).
   - Demo login functional during development (`DEBUG=True`).
   - Contact educator volunteer submission.
   - Newsletter subscription workflow.
3. **`courses` (5 tests)**:
   - Rating calculations and database sorting.
   - Unpublished course access permissions (student blocked, instructor permitted).
   - Enrollment POST enforcement and XP ledger recording.
   - Lesson completion progress tracking and automatic certificate trigger.
   - Instructor course editing and deletion permission checks.
4. **`live_classes` (5 tests)**:
   - Live session directory view.
   - Enrolled student classroom access control.
   - Attendance XP farming prevention.
   - Doubt submission POST enforcement.
   - Instructor doubt resolution workflow.
5. **`quizzes` (6 tests)**:
   - Unenrolled student quiz block.
   - Unpublished course quiz permission enforcement.
   - Question single-correct-answer model validation (`Choice.clean`).
   - Maximum attempt enforcement (`max_attempts`).
   - Successful quiz pass, scoring, and one-time XP allocation.
   - Server-side quiz time limit expiration rejection.
6. **`certificates` (6 tests)**:
   - Certificate generation and HMAC-SHA256 digital signature computation.
   - Cryptographic tamper detection (`verify_signature`).
   - Certificate view rendering with signature validation.
   - Public verification lookup by Certificate ID.
   - Public verification lookup by Hash Code.
   - Graceful handling of invalid or forged certificate queries.
7. **`community` (4 tests)**:
   - Thread creation and XP allocation.
   - Reply creation and XP allocation.
   - POST-only upvoting and toggle abuse prevention.
   - Solution marking authorization and helper XP award.

**Result: 38 passed, 0 failures, 0 errors.**

---

## 💻 Local Setup & Execution

### 1. Environment Preparation
```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Copy `.env.example` to `.env`:
```env
DEBUG=True
SECRET_KEY=django-insecure-dev-key-liveschool-int253-local-development-only
ALLOWED_HOSTS=127.0.0.1,localhost,testserver
JITSI_DOMAIN=meet.jit.si
```

### 4. Database Initialization
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run Verification & Tests
```bash
python manage.py check
python manage.py test
```

### 6. Start Development Server
```bash
python manage.py runserver
```
Visit: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**  
Admin Panel: **[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)**

---

## 🐳 Production Deployment

### Local Docker preview
```bash
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```
Copy `.env.example` to `.env` before starting Compose. The preview listens on loopback and uses separate volumes for its SQLite database and uploads.

### Public deployment

#### Single Linux server with Docker Compose

1. Install Docker Engine with the Compose plugin on your server and copy or clone this repository there. In your DNS provider's dashboard, point your chosen hostname to the server's public IP. Open inbound TCP ports 80 and 443. Publish an AAAA record only if IPv6 reaches this server.
2. Run the following commands on a machine with Python 3 to generate two separate secrets.

   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

3. In the repository root **on the server**, create `.env.production` with a text editor. Use the first output for `SECRET_KEY` and the second for `POSTGRES_PASSWORD`. Keep the PostgreSQL password in hexadecimal because Compose inserts it into a connection URL. Save both values in your password manager. The Compose database hostname, database name, and username are already configured. Keep these credentials stable across restarts. Changing the environment file alone does not rotate an existing PostgreSQL role's password.

   ```dotenv
   SITE_DOMAIN=school.example.com
   SECRET_KEY=replace_with_first_generated_value
   POSTGRES_PASSWORD=replace_with_second_generated_value
   JITSI_DOMAIN=meet.jit.si
   ```

4. Validate the configuration, start the stack, and check the startup logs.

   ```bash
   chmod 600 .env.production
   docker compose --env-file .env.production -f compose.production.yml config --quiet
   docker compose --env-file .env.production -f compose.production.yml up -d --build
   docker compose --env-file .env.production -f compose.production.yml ps
   docker compose --env-file .env.production -f compose.production.yml logs --tail=100 db web proxy
   ```

5. Once the web service has applied migrations, create the first administrator and run the production check.

   ```bash
   docker compose --env-file .env.production -f compose.production.yml exec web python manage.py createsuperuser
   docker compose --env-file .env.production -f compose.production.yml exec web python manage.py check --deploy
   curl -fsS https://school.example.com/health/
   ```

   Replace the hostname in the curl command. The health endpoint checks Django HTTP availability. Applying migrations and saving records in admin verify the database connection. HSTS subdomain coverage and preload are optional and can produce deployment warnings.

6. Sign in at `/admin/` using the credentials you just created. Create a real category, approve a registered instructor, and create a course with modules, lessons, and a quiz. Test as a separate learner. Verify a course certificate, post and answer a classroom question, submit a contact message, and confirm newsletter signup appears in admin. Join a scheduled video session from two devices. Test an upload, restart the stack, and confirm the file and records persist. Uploaded files served through `/media/` are public to anyone with their URL.
7. Back up PostgreSQL and the media volume separately and test restoring them. Preserve the named volumes during upgrades. Use a backup of real production data when restoring a deployment.

For startup failures, inspect the relevant service logs. For database authentication errors, verify the password matches the existing PostgreSQL role. For TLS errors, check public DNS and ports 80 and 443. For form CSRF errors, make sure the browser hostname matches `SITE_DOMAIN`. For video failures, confirm the conferencing host permits embedding and that the instructor can start meetings there. Public Jitsi rooms need provider-side controls for restricted attendance. Outbound newsletter delivery requires a mailing service.

#### Managed hosting alternative

1. Provision a fresh PostgreSQL database and a Docker-capable host with an HTTPS domain. Do not import the workspace SQLite database or local uploads for a clean launch. If you already have production records, back them up and review existing accounts and content before migrating.
2. Set `DEBUG=False`, `DATABASE_URL`, `ALLOWED_HOSTS` (hostnames), and `CSRF_TRUSTED_ORIGINS` (HTTPS origins). Generate a persistent `SECRET_KEY` with `python -c "import secrets; print(secrets.token_urlsafe(50))"` and store it in the hosting platform's secrets. The HTTPS proxy must overwrite `X-Forwarded-Proto` and prevent direct public access to Gunicorn.
3. Build from `Dockerfile`. Run `python manage.py migrate --noinput` as a release command with the production environment before routing traffic to the new version. Use the image's default Gunicorn command. The image collects static files at build time.
4. Mount persistent storage at `/app/media` and serve `/media/` through a web server without executing uploaded files. Django only serves uploads in development. Configure database and upload backups.
5. Run `python manage.py createsuperuser` in the production environment. In Django admin, add real categories and approve instructor accounts. Create courses, modules, lessons, and quizzes using real course material.
6. Configure `JITSI_DOMAIN` for your conferencing service. For restricted classes, enforce participant access on the conferencing service itself. Test hosting and joining from two accounts with camera and microphone permissions.
7. Run `python manage.py check --deploy`. On the deployed HTTPS site, verify `/health/`, sign-in, static assets, uploads, course enrollment, quiz submission, and video. Contact and newsletter submissions are stored in Django admin. Set up a separate sender if you want outbound newsletter delivery.
