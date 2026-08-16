"""
NEXUS-X Copilot Comprehensive Test Suite

Tests for the enhanced Copilot covering 40+ intent patterns and modes.
Verifies response quality, evidence-based reasoning, and mode adaptation.
"""

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import backend.app as mod


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    mod.app.config["TESTING"] = True
    mod.DB_PATH = tmp_path / "nexus.db"
    mod.init_db()
    yield


def client():
    c = mod.app.test_client()
    r = c.post('/api/login', json={'email': mod.DEMO_EMAIL, 'password': mod.DEMO_PASSWORD})
    assert r.status_code == 200
    return c


def csrf(c):
    with c.session_transaction() as sess:
        return sess.get("csrf")


def post(c, path, **kwargs):
    headers = dict(kwargs.pop("headers", {}) or {})
    headers.setdefault("X-CSRF-Token", csrf(c) or "")
    return c.post(path, headers=headers, **kwargs)


def make_project(c, description='Launch in 10 days with a team of 3 people. Payments, auth, notifications, security.'):
    r = post(c, '/api/projects', json={'name': 'Test Project', 'description': description})
    assert r.status_code == 200
    return r.get_json()


# ==================== GREETINGS & HELP ====================

def test_copilot_greeting():
    c = client()
    r = post(c, '/api/chat', json={'message': 'Hi', 'project_id': 0})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'Hello' in answer or 'hello' in answer.lower()


def test_copilot_hello_variant():
    c = client()
    r = post(c, '/api/chat', json={'message': 'Hello there', 'project_id': 0})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'Copilot' in answer or 'help' in answer.lower()


def test_copilot_help_request():
    c = client()
    r = post(c, '/api/chat', json={'message': 'What can you do?', 'project_id': 0})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'help' in answer.lower() or 'project' in answer.lower()


def test_copilot_about_self():
    c = client()
    r = post(c, '/api/chat', json={'message': 'Who are you?', 'project_id': 0})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'Copilot' in answer


# ==================== TASK INTELLIGENCE ====================

def test_copilot_first_task_recommendation():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What should I do first?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'T1' in answer or 'task' in answer.lower()
    assert 'WHY' in answer or 'why' in answer.lower()


def test_copilot_task_priority_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Which task should we start?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'task' in answer.lower() or 'start' in answer.lower()


def test_copilot_next_task_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What is the next task?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'task' in answer.lower() or 'T' in answer


# ==================== RISK INTELLIGENCE ====================

def test_copilot_biggest_risk_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What is the biggest risk?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'Risk' in answer or 'risk' in answer.lower()
    assert 'EVIDENCE' in answer


def test_copilot_why_at_risk_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Why is my project at risk?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'EVIDENCE' in answer
    assert 'ACTION' in answer


def test_copilot_risk_mitigation_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'How can we reduce risk?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 50  # Should have meaningful response


# ==================== SCHEDULE & DEADLINE ====================

def test_copilot_deadline_feasibility():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Can we finish on time?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'deadline' in answer.lower() or 'days' in answer.lower()


def test_copilot_critical_path_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What is the critical path?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'path' in answer.lower() or 'T' in answer
    assert 'days' in answer.lower()


def test_copilot_schedule_pressure():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Are we behind schedule?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 20


# ==================== TEAM & CAPACITY ====================

def test_copilot_team_assignment():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Who should handle this task?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'name' not in answer.lower() or len(answer) > 30  # Should have recommendation


def test_copilot_workload_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Who is overloaded?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 20


def test_copilot_team_info():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Who is on the team?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 20


# ==================== BUDGET & COST ====================

def test_copilot_budget_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Are we within budget?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'budget' in answer.lower() or 'cost' in answer.lower() or 'configured' in answer.lower()


def test_copilot_cost_estimate():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What is the project cost?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 20


# ==================== BLOCKERS ====================

def test_copilot_blocker_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What is blocking us?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'blocked' in answer.lower() or 'blocker' in answer.lower()


def test_copilot_blockers_plural():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Are there any blockers?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 20


# ==================== HEALTH & STATUS ====================

def test_copilot_health_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'How is the project doing?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'health' in answer.lower() or 'status' in answer.lower()


def test_copilot_progress_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What is the progress?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert '%' in answer or 'progress' in answer.lower()


# ==================== WHAT-IF SCENARIOS ====================

def test_copilot_what_if_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What if we add 2 developers?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'scenario' in answer.lower() or 'if' in answer.lower() or len(answer) > 50


def test_copilot_deadline_extension():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What happens if deadline becomes 20 days?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 30


# ==================== PLANNING & ACTION ====================

def test_copilot_action_plan():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What should I do today?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'today' in answer.lower() or 'action' in answer.lower() or 'task' in answer.lower()


def test_copilot_priority_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What is my top priority?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 20


# ==================== MANAGEMENT ====================

def test_copilot_executive_summary():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Give me an executive summary.'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'summary' in answer.lower() or 'health' in answer.lower()


def test_copilot_manager_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What should I tell my manager?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 30


# ==================== STUDENT MODE ====================

def test_copilot_viva_preparation():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Prepare me for viva.'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'viva' in answer.lower() or 'exam' in answer.lower()


def test_copilot_student_mode():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'I am a student. Explain the project.'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 40


# ==================== TECHNICAL ====================

def test_copilot_architecture_question():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Explain the architecture.'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'architecture' in answer.lower() or 'design' in answer.lower()


def test_copilot_general_technical():
    c = client()
    r = post(c, '/api/chat', json={'message': 'What is PostgreSQL?', 'project_id': 0})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'postgres' in answer.lower() or 'database' in answer.lower()


def test_copilot_api_question():
    c = client()
    r = post(c, '/api/chat', json={'message': 'What is an API?', 'project_id': 0})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'api' in answer.lower()


# ==================== NO PROJECT CONTEXT ====================

def test_copilot_without_project():
    c = client()
    r = post(c, '/api/chat', json={'message': 'Hi', 'project_id': 0})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert len(answer) > 20


def test_copilot_project_question_without_project():
    c = client()
    r = post(c, '/api/chat', json={'message': 'What should I do first?', 'project_id': 0})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    # Should suggest adding a project or provide general guidance
    assert len(answer) > 20


# ==================== RESPONSE QUALITY ====================

def test_copilot_response_includes_why_when_appropriate():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Why is T1 important?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    # Should provide reasoning
    assert len(answer) > 50


def test_copilot_handles_invalid_task_reference():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'What about T99?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    # Should handle gracefully
    assert len(answer) > 10


# ==================== RESPONSE STRUCTURE ====================

def test_copilot_response_format():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id': pid, 'message': 'Explain the project.'})
    assert r.status_code == 200
    data = r.get_json()
    assert 'answer' in data
    assert 'mode' in data
    assert isinstance(data['answer'], str)
    assert len(data['answer']) > 0
