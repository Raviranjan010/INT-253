# INT-253: Live School for World-Class Free Education

> **Problem Statement:**  
> *"Live School for World-Class Free Education: Creation of an online platform providing free access to world-class education for students across various demographics."*

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Platform-Production--Ready-brightgreen.svg)]()

---

## 🌟 Vision & Overview
**Live School** is a fully functional web platform built with Django to provide 100% free, high-quality, open-access education to students across diverse demographics—including rural learners, economically disadvantaged students, women in STEM, first-generation learners, and working adults.

Unlike traditional static course repositories, **Live School integrates synchronous real-time WebRTC live video classrooms**, self-paced modular video/reading courses, instant quizzes, an interactive doubt community, and cryptographically verifiable digital certificates of completion.

---

## 🚀 Key Features

### 1. 🎓 Free World-Class Courses
- Multi-tier curriculum: STEM, Computer Science, Web Development, Mathematics, and Global Languages.
- Modular syllabus (Modules & Lessons) with embedded HD video lectures, markdown study notes, and downloadable cheat sheets.
- Interactive course player with progress tracking and sequential navigation.

### 2. 🔴 Synchronous WebRTC Live Classrooms ("Live School")
- Open-access virtual video rooms powered by Jitsi Meet / WebRTC (no API keys required, 100% free).
- Live audio/video, screen sharing, tile view, whiteboard, and hand raising.
- Real-time in-class doubt submission board where instructors answer student questions during live sessions.

### 3. ♿ Inclusive Demographics & Accessibility Toolbar
- Built-in **Text Resizer** (`A-`, `A`, `A+`) for visually impaired and mobile learners.
- **High-Contrast Mode** for outdoor/sunlight readability and low-vision accessibility.
- **Dark / Light Theme** toggle with persistent `localStorage`.
- **Text-to-Speech (TTS) Lesson Reader**: Browser speech synthesis for listening to notes on the go.
- Low-bandwidth optimization for rural 2G/3G connectivity.

### 4. 📝 Assessments & Graded Quizzes
- Automated quiz scoring with configurable pass percentages.
- Detailed question-by-question explanations upon test submission to reinforce learning.

### 5. 🏆 Verifiable Digital Certificates
- Automatically awarded upon 100% lesson completion.
- Printable, high-resolution certificate canvas with honors grading, gold seal, and digital signatures.
- **Public Certificate Verification Portal**: Employers and universities can verify authentic certificate IDs (e.g. `LS-2026-DEMO8942`).

### 6. 💬 Collaborative Q&A Community
- Peer-to-peer discussion forum for doubt clearing across demographics.
- Upvoting system for helpful answers and solution-marking by question authors.

### 7. ⚡ Gamification
- Learning Experience Points (XP) awarded for completing lessons, passing quizzes, and helping peers.
- Daily learning streak counters to foster consistent study habits.

---

## 👥 Demo Accounts (Pre-Seeded)

The project includes pre-seeded demo accounts for quick localhost evaluation:

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full Django admin access & platform controls |
| **Instructor** | `teacher_demo` | `teacher123` | Schedule live classes, author courses & answer doubts |
| **Student** | `student_demo` | `student123` | Enrolled in Python course (100% completed), earned certificate |

*(You can also use the **"Demo Login"** dropdown directly in the top navigation bar for 1-click instant login without typing passwords).*

---

## 💻 Quickstart (Running on Localhost)

### 1. Clone & Navigate
```bash
git clone <repo-url>
cd INT-253
```

### 2. Activate Virtual Environment
On Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Migrations & Seed Demo Data
```bash
python manage.py migrate
python manage.py seed_data
```

### 5. Start the Local Server
```bash
python manage.py runserver
```

Open your browser and navigate to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🧪 Running Automated Tests

Run the full automated test suite (5 tests covering all apps and flows):
```bash
python manage.py test
```

---

## 🐳 Deployment Readiness

### Docker & Docker Compose
To run via Docker:
```bash
docker-compose up --build
```

### Production Deployment (Render, Heroku, Railway, Cloud Run)
1. Set `DEBUG=False` and supply a secure `SECRET_KEY` in environment variables.
2. `whitenoise` is configured for static asset serving.
3. `Procfile` is pre-configured with `gunicorn`.

---

## 📂 Project Architecture

```
INT-253/
├── liveschool_project/       # Root project configuration (settings, urls, wsgi)
├── accounts/                 # Custom User model, auth, profiles & role dashboards
├── core/                     # Landing pages, accessibility context, contact & seeders
├── courses/                  # Categories, Courses, Modules, Lessons, Reviews & Player
├── live_classes/             # WebRTC / Jitsi live video rooms & doubt boards
├── quizzes/                  # Interactive assessments, questions, choices & attempts
├── community/                # Discussion threads, peer replies & upvoting
├── certificates/             # Certificate issuance, printable canvas & public verification
├── static/                   # Custom CSS, JavaScript (accessibility, theme, AJAX)
├── templates/                # Responsive HTML5 templates (Bootstrap 5.3)
├── Dockerfile                # Container deployment definition
├── docker-compose.yml        # Docker compose specification
├── Procfile                  # PaaS deployment specification
├── requirements.txt          # Python dependencies
└── manage.py                 # Django command-line utility
```
