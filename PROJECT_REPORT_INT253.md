# INT253 Project Report — LiveSchool

| Field | Value |
| --- | --- |
| Student | Ravi Ranjan |
| Registration number | 12312923 |
| Course | INT253 |
| Supervisor | [To be completed by the student] |
| Submission date | [To be completed by the student] |
| Signatures | [To be completed by the student and supervisor] |

## Scope

LiveSchool is a Django 6.1 application targeting Python 3.12. It provides free course enrollment, structured lessons, quizzes, live-class scheduling, community discussions, and public verification of application-issued certificates. The platform does not assert third-party accreditation. No external course or demonstration account is installed by the content bootstrap.

## System design

Django templates render the application, with PostgreSQL and private S3-compatible storage required in production. Local development can use SQLite and filesystem media. Gunicorn serves the Render Docker deployment. WhiteNoise uses a static manifest in production. Live classes use one of three paths: a host-provided meeting link, a configured self-hosted Jitsi instance, or JaaS with room-bound RS256 tokens.

The architecture, route inventory, and permission rules are documented in [docs/architecture.md](docs/architecture.md). Configuration, deployment, and backup instructions are in [README.md](README.md).

## Verification and limitations

Local verification exercised Django's application checks, migration drift checks, and the automated test suite. The latest results and acceptance gaps are reported with the implementation delivery. Provider integration tests using a real storage bucket, email sender, and video tenant require operator credentials. A Lighthouse or axe score is not asserted.

Course creation starts with a draft. Instructor approval and ownership govern access to the studio. Course deletion through the LMS preserves courses with learner records, and issued certificates prevent ORM deletion of their course. New certificate signatures cover the issuance record and are not regenerated on an ordinary save.
