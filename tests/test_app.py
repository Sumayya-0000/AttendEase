import os
import tempfile
import pytest
from app import app as flask_app

@pytest.fixture()
def client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    monkeypatch.setenv('DATABASE_PATH', path)
    flask_app.config.update(TESTING=True)
    # app module reads DATABASE_PATH at import time, so patch its constant for each test.
    import app as app_module
    original = app_module.DATABASE
    app_module.DATABASE = path
    with flask_app.test_client() as client:
        yield client
    app_module.DATABASE = original
    os.unlink(path)

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'healthy'

def test_dashboard_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Attendance Dashboard' in response.data

def test_students_page_and_add_student(client):
    response = client.get('/students')
    assert response.status_code == 200
    response = client.post('/students', data={'name': 'Test Student', 'roll_number': 'T001', 'course': 'IT'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Test Student' in response.data
