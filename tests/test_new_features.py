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
    res = client.get('/admin/blog/settings')
    assert res.status_code == 200
    assert res.json().get('ok') is True