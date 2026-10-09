from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class FlowTest(APITestCase):
    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_full_flow(self):
        r = self.client.post('/api/register/employer/', dict(username='emp', email='e@x.com', password='pass12345', company_name='Acme'))
        self.assertEqual(r.status_code, 201); emp = r.data['token']
        r = self.client.post('/api/register/candidate/', dict(username='can', email='c@x.com', password='pass12345', skills='django'))
        self.assertEqual(r.status_code, 201); can = r.data['token']

        self.auth(emp)
        r = self.client.post('/api/jobs/', dict(title='Django Dev', description='Build APIs', location='Kathmandu', job_type='full_time', salary_min=50000, salary_max=90000))
        self.assertEqual(r.status_code, 201); job = r.data['id']

        self.auth(can)  # candidate cannot post
        self.assertEqual(self.client.post('/api/jobs/', dict(title='x', description='x', location='x')).status_code, 403)
        self.client.credentials()  # public search
        r = self.client.get('/api/jobs/?search=django&location=kath&min_salary=60000&job_type=full_time')
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(self.client.get('/api/jobs/?location=pokhara').data['count'], 0)

        self.auth(can)
        f = SimpleUploadedFile('cv.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        r = self.client.post('/api/resumes/', dict(title='My CV', file=f), format='multipart')
        self.assertEqual(r.status_code, 201); rid = r.data['id']
        bad = SimpleUploadedFile('cv.exe', b'x')
        self.assertEqual(self.client.post('/api/resumes/', dict(title='bad', file=bad), format='multipart').status_code, 400)

        r = self.client.post('/api/applications/', dict(job=job, resume=rid, cover_letter='Hi'))
        self.assertEqual(r.status_code, 201); app = r.data['id']
        self.assertEqual(self.client.post('/api/applications/', dict(job=job, resume=rid)).status_code, 400)  # duplicate

        self.auth(emp)
        self.assertEqual(self.client.get('/api/notifications/').data['count'], 1)
        r = self.client.patch(f'/api/applications/{app}/status/', dict(status='shortlisted'))
        self.assertEqual(r.data['status'], 'shortlisted')

        self.auth(can)
        self.assertEqual(self.client.get('/api/notifications/').data['count'], 1)
        self.assertEqual(self.client.patch(f'/api/applications/{app}/status/', dict(status='accepted')).status_code, 403)

        get_user_model().objects.create_superuser('admin', 'a@x.com', 'adminpass1')
        self.client.login(username='admin', password='adminpass1'); self.client.credentials()
        r = self.client.get('/api/admin/stats/')
        self.assertEqual(r.data['applications'], 1)
