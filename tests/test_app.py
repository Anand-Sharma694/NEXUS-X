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

def patch(c, path, **kwargs):
    headers = dict(kwargs.pop("headers", {}) or {})
    headers.setdefault("X-CSRF-Token", csrf(c) or "")
    return c.patch(path, headers=headers, **kwargs)

def delete(c, path, **kwargs):
    headers = dict(kwargs.pop("headers", {}) or {})
    headers.setdefault("X-CSRF-Token", csrf(c) or "")
    return c.delete(path, headers=headers, **kwargs)


def make_project(c, description='Launch payments and security in 10 days with a team of 3 people.'):
    r = post(c, '/api/projects', json={'name': 'Test Project', 'description': description})
    assert r.status_code == 200
    return r.get_json()


def test_analyzer_extracts_numbers_and_risks():
    a, mode = mod.analyze_description('Launch in 10 days with a team of 3 people and payments')
    assert mode == 'heuristic'
    assert a['deadline_days'] == 10
    assert a['team_size'] == 3
    assert any(r['name'] == 'Payment' for r in a['risks'])
    assert a['dependencies']


def test_critical_path_uses_duration_and_dependencies():
    tasks = [
        {'task_key': 'T1', 'name': 'A', 'effort': 2},
        {'task_key': 'T2', 'name': 'B', 'effort': 5},
        {'task_key': 'T3', 'name': 'C', 'effort': 1},
        {'task_key': 'T4', 'name': 'D', 'effort': 2},
    ]
    deps = [
        {'from_task': 'T1', 'to_task': 'T2'},
        {'from_task': 'T2', 'to_task': 'T4'},
        {'from_task': 'T1', 'to_task': 'T3'},
        {'from_task': 'T3', 'to_task': 'T4'},
    ]
    cp = mod.critical_path(tasks, deps)
    assert cp['has_cycle'] is False
    assert cp['path'] == ['T1', 'T2', 'T4']
    assert cp['duration'] == 9
    assert cp['slack']['T3'] == 4


def test_critical_path_detects_cycle():
    tasks = [{'task_key':'T1','name':'A','effort':1},{'task_key':'T2','name':'B','effort':1}]
    cp = mod.critical_path(tasks, [{'from_task':'T1','to_task':'T2'},{'from_task':'T2','to_task':'T1'}])
    assert cp['has_cycle'] is True


def test_health_engine_changes_with_blockers_and_risk():
    project = {'deadline_days': 10, 'team_size': 3}
    tasks = [
        {'task_key':'T1','effort':5,'status':'COMPLETED','owner':'A'},
        {'task_key':'T2','effort':5,'status':'BLOCKED','owner':'B'},
    ]
    risks = [{'severity':'HIGH','score':9}]
    team = [{'workload':95,'availability':80}]
    cp = mod.critical_path(tasks, [])
    h = mod.health_engine(project, tasks, risks, team, cp)
    assert 0 <= h['health'] <= 100
    assert h['progress'] == 50
    assert h['blocked'] == 1
    assert h['high_risks'] == 1
    assert h['health_status'] in ('HEALTHY','NEEDS ATTENTION','AT RISK')


def test_project_lifecycle_persists_calculated_state():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    assert p['tasks'] and p['risks'] and p['dependencies']
    assert p['critical_path']
    assert 'components' in p and 'explanation' in p
    r = c.get(f'/api/projects/{pid}')
    assert r.status_code == 200
    assert r.get_json()['project']['id'] == pid


def test_task_update_recalculates_progress_and_health():
    c = client(); p = make_project(c)
    pid = p['project']['id']; task = p['tasks'][0]
    r = patch(c, f"/api/tasks/{task['id']}", json={'status':'COMPLETED'})
    assert r.status_code == 200
    state = r.get_json()
    assert state['progress'] > 0
    assert state['completed_effort'] > 0


def test_dependency_api_rejects_cycles():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    tasks = p['tasks']
    # Existing chain includes T1 -> T2; adding reverse should be rejected.
    a = next(x for x in tasks if x['task_key'] == 'T1')
    b = next(x for x in tasks if x['task_key'] == 'T2')
    r = post(c, '/api/dependencies', json={'project_id':pid,'from_task_id':b['id'],'to_task_id':a['id']})
    assert r.status_code == 400
    assert 'cycle' in r.get_json()['error'].lower()


def test_what_if_recalculates_critical_path():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/what-if', json={'project_id':pid,'team':1,'deadline':5,'scope_factor':1.2,'budget':0})
    assert r.status_code == 200
    d = r.get_json()
    assert d['estimated_effort'] > 0
    assert d['critical_path_duration'] > 0
    assert d['verdict'] in ('NOT FEASIBLE','IMPROVES','STABLE','RISKIER')


def test_project_copilot_returns_project_evidence():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    r = post(c, '/api/chat', json={'project_id':pid,'message':'Why is my project at risk?'})
    assert r.status_code == 200
    answer = r.get_json()['answer']
    assert 'EVIDENCE' in answer
    assert 'ACTION' in answer


def test_general_copilot_has_non_project_fallback():
    c = client()
    r = post(c, '/api/chat', json={'message':'Explain what an API is.'})
    assert r.status_code == 200
    assert r.get_json()['answer']


def test_health_endpoint_identifies_phase():
    r = mod.app.test_client().get('/api/health')
    assert r.status_code == 200
    assert r.get_json()['phase'] == '5-verification'


def test_project_isolation():
    c = client(); p = make_project(c)
    pid = p['project']['id']
    # Simulate another user.
    conn = mod.db()
    from werkzeug.security import generate_password_hash
    conn.execute('INSERT INTO users(name,email,password_hash,role,plan,created_at) VALUES(?,?,?,?,?,?)', ('Other','other@nexus.local',generate_password_hash('pass'),'TEAM MEMBER','FREE',mod.now()))
    conn.commit(); conn.close()
    other = mod.app.test_client(); assert other.post('/api/login', json={'email':'other@nexus.local','password':'pass'}).status_code == 200
    assert other.get(f'/api/projects/{pid}').status_code == 404


def test_csv_and_pdf_exports():
    c = client(); p = make_project(c); pid = p['project']['id']
    assert c.get(f'/api/export/tasks.csv/{pid}').status_code == 200
    assert c.get(f'/api/export/report.pdf/{pid}').status_code == 200


def test_live_risk_engine_reacts_to_blocker():
    project={'deadline_days':10,'team_size':2}
    tasks=[{'task_key':'T1','name':'Core','description':'','effort':8,'status':'BLOCKED'},{'task_key':'T2','name':'Testing','description':'','effort':3,'status':'NOT STARTED'}]
    deps=[{'from_task':'T1','to_task':'T2'}]
    cp=mod.critical_path(tasks,deps)
    risks=mod.live_risk_engine(project,tasks,deps,[],cp)
    assert risks[0]['score'] >= 7
    assert any(r['name']=='Blocked Work' for r in risks)


def test_live_risk_engine_adds_dependency_pressure():
    project={'deadline_days':30,'team_size':5}
    tasks=[{'task_key':f'T{i}','name':f'T{i}','description':'','effort':1,'status':'NOT STARTED'} for i in range(1,6)]
    deps=[{'from_task':'T1','to_task':'T5'},{'from_task':'T2','to_task':'T5'},{'from_task':'T3','to_task':'T5'}]
    cp=mod.critical_path(tasks,deps)
    risks=mod.live_risk_engine(project,tasks,deps,[],cp)
    assert any(r['name']=='Dependency Pressure' for r in risks)


def test_what_if_changes_risk_and_health_from_baseline():
    c=client(); p=make_project(c); pid=p['project']['id']
    base=c.get(f'/api/projects/{pid}').get_json()
    r=post(c, '/api/what-if',json={'project_id':pid,'team':1,'deadline':3,'scope_factor':1.5,'budget':0})
    assert r.status_code==200
    d=r.get_json()
    assert d['health_delta'] != 0 or d['verdict']=='NOT FEASIBLE'
    assert d['risks']


def test_dependency_impact_endpoint():
    c=client(); p=make_project(c); pid=p['project']['id']
    r=c.get(f'/api/dependencies/{pid}/impact')
    assert r.status_code==200
    assert 'impact' in r.get_json()


def test_scenarios_are_persisted():
    c=client(); p=make_project(c); pid=p['project']['id']
    assert post(c, '/api/what-if',json={'project_id':pid,'team':4,'deadline':12,'scope_factor':.9}).status_code==200
    r=c.get(f'/api/scenarios/{pid}')
    assert r.status_code==200 and r.get_json()['scenarios']

def test_signup_creates_hashed_account_and_session():
    c = mod.app.test_client()
    r = c.post('/api/signup', json={'name':'Sana','email':'sana@example.com','password':'strongpass1'})
    assert r.status_code == 200
    assert r.get_json()['user']['plan'] == 'FREE'
    conn=mod.db(); row=conn.execute('SELECT password_hash FROM users WHERE email=?',('sana@example.com',)).fetchone(); conn.close()
    assert row and row['password_hash'] != 'strongpass1'
    assert c.get('/api/me').get_json()['user']['email'] == 'sana@example.com'


def test_team_crud_and_role_permission():
    c=client(); p=make_project(c); pid=p['project']['id']
    r=post(c, '/api/team',json={'project_id':pid,'name':'Maya','role':'Data Engineer','skills':'Python, SQL','availability':75})
    assert r.status_code==200
    member=next(x for x in r.get_json()['team'] if x['name']=='Maya')
    r=patch(c, f"/api/team/{member['id']}",json={'workload':55})
    assert r.status_code==200 and any(x['workload']==55 for x in r.get_json()['team'] if x['id']==member['id'])
    r=delete(c, f"/api/team/{member['id']}")
    assert r.status_code==200 and not any(x['id']==member['id'] for x in r.get_json()['team'])


def test_project_member_can_access_project_but_cannot_manage_team():
    c=client(); p=make_project(c); pid=p['project']['id']
    conn=mod.db(); from werkzeug.security import generate_password_hash
    uid=conn.execute('INSERT INTO users(name,email,password_hash,role,plan,created_at) VALUES(?,?,?,?,?,?)',('Member','member@example.com',generate_password_hash('memberpass'),'TEAM MEMBER','FREE',mod.now())).lastrowid
    conn.execute('INSERT INTO project_members(project_id,user_id,role,created_at) VALUES(?,?,?,?)',(pid,uid,'MEMBER',mod.now())); conn.commit(); conn.close()
    other=mod.app.test_client(); assert other.post('/api/login',json={'email':'member@example.com','password':'memberpass'}).status_code==200
    assert other.get(f'/api/projects/{pid}').status_code==200
    assert post(other, '/api/team',json={'project_id':pid,'name':'Nope'}).status_code==403


def test_notification_read_and_read_all():
    c=client(); p=make_project(c); pid=p['project']['id']
    rows=c.get(f'/api/notifications/{pid}').get_json()['notifications']
    if rows:
        assert patch(c, f"/api/notifications/{rows[0]['id']}/read",json={}).status_code==200
    assert post(c, f'/api/notifications/{pid}/read-all',json={}).status_code==200
    rows=c.get(f'/api/notifications/{pid}').get_json()['notifications']
    assert all(r['read']==1 for r in rows)


def test_admin_can_update_user_plan_and_role():
    c=client(); c.post('/api/signup',json={'name':'Temp','email':'temp@example.com','password':'strongpass1'})
    # signup changes session, log back into demo admin
    assert c.post('/api/login',json={'email':mod.DEMO_EMAIL,'password':mod.DEMO_PASSWORD}).status_code==200
    conn=mod.db(); uid=conn.execute('SELECT id FROM users WHERE email=?',('temp@example.com',)).fetchone()['id']; conn.close()
    r=patch(c, f'/api/users/{uid}',json={'role':'MANAGER','plan':'PRO'})
    assert r.status_code==200
    conn=mod.db(); row=conn.execute('SELECT role,plan FROM users WHERE id=?',(uid,)).fetchone(); conn.close()
    assert row['role']=='MANAGER' and row['plan']=='PRO'


def test_dashboard_has_decision_summary_and_unread_count():
    c=client(); p=make_project(c); pid=p['project']['id']
    r=c.get(f'/api/dashboard/{pid}')
    assert r.status_code==200
    d=r.get_json(); assert 'decision_summary' in d and 'unread_notifications' in d


def test_csrf_blocks_authenticated_write_without_token():
    c = client()
    with c.session_transaction() as sess:
        sess.pop('csrf', None)
    r = c.post('/api/projects', json={'name':'Blocked','description':'Should fail without csrf'})
    assert r.status_code == 403


def test_logout_clears_session_and_blocks_private_routes():
    c = client()
    assert c.post('/api/logout').status_code == 200
    assert c.get('/api/projects').status_code == 401


def test_duplicate_signup_is_rejected():
    c = mod.app.test_client()
    payload = {'name':'Sana','email':'duplicate@example.com','password':'strongpass1'}
    assert c.post('/api/signup', json=payload).status_code == 200
    assert c.post('/api/signup', json=payload).status_code == 409


def test_password_change_requires_current_password():
    c = client()
    assert post(c, '/api/me/password', json={'old_password':'wrong','new_password':'newstrong1'}).status_code == 400
    assert post(c, '/api/me/password', json={'old_password':mod.DEMO_PASSWORD,'new_password':'newstrong1'}).status_code == 200
    assert c.post('/api/login', json={'email':mod.DEMO_EMAIL,'password':'newstrong1'}).status_code == 200


def test_project_update_requires_manager_permission():
    c = client(); p = make_project(c); pid = p['project']['id']
    conn=mod.db(); from werkzeug.security import generate_password_hash
    uid=conn.execute('INSERT INTO users(name,email,password_hash,role,plan,created_at) VALUES(?,?,?,?,?,?)',('Viewer','viewer@example.com',generate_password_hash('viewerpass'),'TEAM MEMBER','FREE',mod.now())).lastrowid
    conn.execute('INSERT INTO project_members(project_id,user_id,role,created_at) VALUES(?,?,?,?)',(pid,uid,'MEMBER',mod.now())); conn.commit(); conn.close()
    other=mod.app.test_client(); assert other.post('/api/login',json={'email':'viewer@example.com','password':'viewerpass'}).status_code==200
    assert post(other, '/api/team',json={'project_id':pid,'name':'Blocked Member'}).status_code==403


def test_builder_requires_authentication_and_csrf():
    guest=mod.app.test_client()
    assert guest.post('/api/generate-project.zip',json={'prompt':'Build a small task app'}).status_code == 401
    c=client()
    with c.session_transaction() as sess:
        sess['csrf']='known-token'
    r=c.post('/api/generate-project.zip',json={'prompt':'Build a small task app'})
    assert r.status_code == 403


def test_builder_returns_zip_with_required_artifacts():
    c=client()
    with c.session_transaction() as sess:
        token=sess['csrf']
    r=c.post('/api/generate-project.zip',json={'prompt':'Build a student attendance system with login, dashboard and reports'},headers={'X-CSRF-Token':token})
    assert r.status_code == 200
    import zipfile, io
    z=zipfile.ZipFile(io.BytesIO(r.data))
    names=set(z.namelist())
    required={'README.md','requirements.txt','PROJECT_SPEC.json','backend/app.py','frontend/index.html','tests/test_app.py','tests/test_project_spec.py','docs/ARCHITECTURE.md','docs/IMPLEMENTATION_PLAN.md'}
    assert required.issubset(names)


def test_invalid_task_status_is_rejected():
    c=client(); p=make_project(c); task=p['tasks'][0]
    r=patch(c, f"/api/tasks/{task['id']}",json={'status':'NOT_A_STATUS'})
    assert r.status_code == 400


def test_security_headers_are_present():
    c=mod.app.test_client()
    r=c.get('/')
    assert r.status_code == 200
    assert r.headers['X-Content-Type-Options'] == 'nosniff'
    assert r.headers['X-Frame-Options'] == 'DENY'
    assert r.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'


def test_health_reports_verification_phase():
    r=mod.app.test_client().get('/api/health')
    assert r.status_code == 200
    assert r.get_json()['phase'] == '5-verification'


def test_team_recommendation_returns_ranked_member():
    c=client(); p=make_project(c); pid=p['project']['id']; task=p['tasks'][0]
    r=post(c,'/api/team/recommend',json={'project_id':pid,'task_id':task['id']})
    assert r.status_code==200
    d=r.get_json(); assert d['recommended_member']['name']; assert d['recommended_member']['match_score'] >= 0; assert 'alternatives' in d


def test_analytics_snapshots_endpoint():
    c=client(); p=make_project(c); pid=p['project']['id']
    r=c.get(f'/api/analytics/{pid}')
    assert r.status_code==200
    d=r.get_json(); assert 'snapshots' in d and 'current' in d


def test_budget_what_if_can_make_scenario_infeasible():
    c=client(); p=make_project(c); pid=p['project']['id']
    r=post(c,'/api/what-if',json={'project_id':pid,'team':2,'deadline':14,'budget':1,'scope_factor':1})
    assert r.status_code==200
    d=r.get_json(); assert d['budget_feasible'] is False; assert d['verdict']=='NOT FEASIBLE'; assert d['estimated_cost'] > 1


def test_task_planning_changes_require_manager():
    c=client(); p=make_project(c); pid=p['project']['id']; task=p['tasks'][0]
    conn=mod.db(); from werkzeug.security import generate_password_hash
    uid=conn.execute('INSERT INTO users(name,email,password_hash,role,plan,created_at) VALUES(?,?,?,?,?,?)',('Planner Viewer','planner-viewer@example.com',generate_password_hash('viewerpass'),'TEAM MEMBER','FREE',mod.now())).lastrowid
    conn.execute('INSERT INTO project_members(project_id,user_id,role,created_at) VALUES(?,?,?,?)',(pid,uid,'MEMBER',mod.now())); conn.commit(); conn.close()
    other=mod.app.test_client(); assert other.post('/api/login',json={'email':'planner-viewer@example.com','password':'viewerpass'}).status_code==200
    assert patch(other,f'/api/tasks/{task["id"]}',json={'name':'Unauthorized rename'}).status_code==403


def test_security_policy_header_is_present():
    r=mod.app.test_client().get('/')
    assert 'Content-Security-Policy' in r.headers
    assert "script-src 'self'" in r.headers['Content-Security-Policy']

