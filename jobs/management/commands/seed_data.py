from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from jobs.models import Application, Candidate, Employer, Job, Notification, Resume

User = get_user_model()
PASSWORD = 'pass12345'

EMPLOYERS = [
    ('techcorp', 'TechCorp Nepal', 'https://techcorp.example.com', 'Software company in Kathmandu.'),
    ('himalayadata', 'Himalaya Data Labs', 'https://himalayadata.example.com', 'Data and AI solutions.'),
    ('everestbank', 'Everest Digital Bank', 'https://everestbank.example.com', 'Fintech and banking.'),
]

CANDIDATES = [
    ('ram', 'Ram', 'Sharma', '9800000001', 'Python, Django, PostgreSQL'),
    ('sita', 'Sita', 'Thapa', '9800000002', 'React, JavaScript, CSS'),
    ('hari', 'Hari', 'Karki', '9800000003', 'Data analysis, SQL, Pandas'),
]

JOBS = [
    ('techcorp', 'Django Backend Developer', 'IT', 'Kathmandu', 'full_time', 60000, 90000),
    ('techcorp', 'React Frontend Developer', 'IT', 'Lalitpur', 'full_time', 55000, 85000),
    ('techcorp', 'Python Intern', 'IT', 'Kathmandu', 'internship', 10000, 15000),
    ('himalayadata', 'Data Analyst', 'Data', 'Pokhara', 'full_time', 50000, 75000),
    ('himalayadata', 'Machine Learning Engineer', 'Data', 'Remote', 'remote', 90000, 140000),
    ('himalayadata', 'Part-time SQL Tutor', 'Education', 'Lalitpur', 'part_time', 20000, 30000),
    ('everestbank', 'Mobile Banking QA Tester', 'Banking', 'Kathmandu', 'contract', 45000, 65000),
    ('everestbank', 'Cyber Security Analyst', 'Security', 'Kathmandu', 'full_time', 80000, 120000),
]


class Command(BaseCommand):
    help = 'Load sample employers, candidates, jobs, resumes and applications.'

    def handle(self, *args, **opts):
        employers = {}
        for uname, company, site, desc in EMPLOYERS:
            user, _ = User.objects.get_or_create(username=uname, defaults={'email': f'{uname}@example.com'})
            user.set_password(PASSWORD); user.save()
            employers[uname], _ = Employer.objects.get_or_create(
                user=user, defaults={'company_name': company, 'website': site, 'description': desc})

        candidates = {}
        for uname, first, last, phone, skills in CANDIDATES:
            user, _ = User.objects.get_or_create(
                username=uname, defaults={'email': f'{uname}@example.com', 'first_name': first, 'last_name': last})
            user.set_password(PASSWORD); user.save()
            cand, _ = Candidate.objects.get_or_create(user=user, defaults={'phone': phone, 'skills': skills})
            candidates[uname] = cand
            if not cand.resumes.exists():
                r = Resume(candidate=cand, title=f'{first} CV')
                r.file.save(f'{uname}_cv.pdf', ContentFile(b'%PDF-1.4 sample resume'), save=True)

        jobs = []
        for i, (emp, title, cat, loc, jtype, lo, hi) in enumerate(JOBS):
            job, _ = Job.objects.get_or_create(
                employer=employers[emp], title=title,
                defaults=dict(description=f'We are hiring a {title}. Join our team and grow with us.',
                              category=cat, location=loc, job_type=jtype, salary_min=lo, salary_max=hi,
                              deadline=date.today() + timedelta(days=15 + i * 3)))
            jobs.append(job)

        plan = [  # (candidate, job index, status)
            ('ram', 0, 'shortlisted'), ('ram', 2, 'applied'), ('ram', 4, 'reviewed'),
            ('sita', 1, 'interview'), ('sita', 0, 'rejected'),
            ('hari', 3, 'accepted'), ('hari', 4, 'applied'), ('hari', 7, 'applied'),
        ]
        for uname, idx, status in plan:
            cand, job = candidates[uname], jobs[idx]
            app, created = Application.objects.get_or_create(
                job=job, candidate=cand,
                defaults={'resume': cand.resumes.first(), 'cover_letter': 'I am very interested in this role.',
                          'status': status})
            if created:
                Notification.objects.create(user=job.employer.user,
                                            message=f'New application from {cand} for "{job.title}".')
                if status != 'applied':
                    Notification.objects.create(user=cand.user,
                                                message=f'Your application for "{job.title}" is now: {app.get_status_display()}.')

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {Employer.objects.count()} employers, {Candidate.objects.count()} candidates, '
            f'{Job.objects.count()} jobs, {Application.objects.count()} applications.'))
        self.stdout.write(f'Employers: techcorp / himalayadata / everestbank  |  Candidates: ram / sita / hari  |  Password: {PASSWORD}')
