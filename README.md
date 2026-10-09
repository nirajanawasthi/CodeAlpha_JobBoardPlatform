# Job Board Platform (Django + DRF)

## Setup (PowerShell)
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

Admin panel: /admin/   |   Stats (admin only): GET /api/admin/stats/

## API (header `Authorization: Token <your-token>`)
| Method | URL | Who | Purpose |
|---|---|---|---|
| POST | /api/register/employer/ | public | register employer |
| POST | /api/register/candidate/ | public | register candidate |
| POST | /api/login/ | public | get token (username, password) |
| GET | /api/me/ | logged-in user | current user and role |
| GET | /api/jobs/ | public | search jobs |
| POST | /api/jobs/ | employer | post job |
| PUT/PATCH/DELETE | /api/jobs/{id}/ | owner employer | edit/delete job |
| GET | /api/jobs/my_jobs/ | employer | own jobs |
| GET | /api/jobs/{id}/applications/ | owner employer | applicants of a job |
| POST/GET | /api/resumes/ | candidate | upload (multipart: title, file) / list |
| POST | /api/applications/ | candidate | apply (job, resume, cover_letter) |
| GET | /api/applications/ | employer/candidate | track applications |
| PATCH | /api/applications/{id}/status/ | employer | update status |
| GET | /api/notifications/ | any user | notifications |
| POST | /api/notifications/mark_all_read/ | any user | mark read |

Job search params: `?search=django&location=kathmandu&job_type=full_time&category=IT&min_salary=50000&max_salary=100000&ordering=-created_at`

Statuses: applied, reviewed, shortlisted, interview, accepted, rejected

## Frontend & Demo
- Frontend: http://127.0.0.1:8000/  |  API: http://127.0.0.1:8000/api/  |  Admin: /admin/
- Load sample data: `python manage.py seed_data`
- Demo login (password `pass12345`): employer `techcorp`, candidate `ram`
