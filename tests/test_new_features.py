import os
import pytest
from starlette.testclient import TestClient
from backend.main import app

def test_contact_submission():
    client = TestClient(app)
    res = client.post('/api/contact', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'subject': 'Support Request',
        'message': 'Hello from automated test'
    })
    assert res.status_code == 200
    assert res.json().get('ok') is True

def test_blogs_list():
    client = TestClient(app)
    res = client.get('/api/blogs')
    assert res.status_code == 200
    data = res.json()
    assert data.get('ok') is True
    assert isinstance(data.get('articles'), list)

def test_blog_settings():
    client = TestClient(app)
    # Unauthenticated must be blocked (S3 fix)
    res_unauth = client.get('/admin/blog/settings')
    assert res_unauth.status_code == 401

    # Authenticated with admin key must succeed
    res = client.get('/admin/blog/settings', headers={'X-Admin-Key': os.environ.get('WPB_ADMIN_KEY', 'admin_key_for_tests_' + 'y' * 30)})
    assert res.status_code == 200
    assert res.json().get('ok') is True