"""Initial NEXUS-X PostgreSQL schema"""
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'TEAM MEMBER',plan TEXT NOT NULL DEFAULT 'FREE',created_at TEXT NOT NULL)""")
    op.execute("""CREATE TABLE IF NOT EXISTS projects(id SERIAL PRIMARY KEY,name TEXT NOT NULL,description TEXT NOT NULL,deadline_days INTEGER NOT NULL DEFAULT 14,team_size INTEGER NOT NULL DEFAULT 3,budget DOUBLE PRECISION NOT NULL DEFAULT 0,infrastructure_cost DOUBLE PRECISION NOT NULL DEFAULT 0,ai_cost DOUBLE PRECISION NOT NULL DEFAULT 0,created_at TEXT NOT NULL,owner_id INTEGER REFERENCES users(id))""")
    op.execute("""CREATE TABLE IF NOT EXISTS tasks(id SERIAL PRIMARY KEY,project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,task_key TEXT NOT NULL,name TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',priority TEXT NOT NULL DEFAULT 'MEDIUM',effort DOUBLE PRECISION NOT NULL DEFAULT 1,risk_level TEXT NOT NULL DEFAULT 'MEDIUM',status TEXT NOT NULL DEFAULT 'NOT STARTED',owner TEXT NOT NULL DEFAULT 'Unassigned',due_date TEXT)""")
    op.execute("""CREATE TABLE IF NOT EXISTS dependencies(id SERIAL PRIMARY KEY,project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,from_task INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,to_task INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE)""")
    op.execute("""CREATE TABLE IF NOT EXISTS risks(id SERIAL PRIMARY KEY,project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,name TEXT NOT NULL,severity TEXT NOT NULL,score INTEGER NOT NULL,explanation TEXT NOT NULL,probability INTEGER NOT NULL,impact INTEGER NOT NULL,mitigation TEXT NOT NULL,affected_tasks TEXT NOT NULL DEFAULT '')""")
    op.execute("""CREATE TABLE IF NOT EXISTS team_members(id SERIAL PRIMARY KEY,project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,name TEXT NOT NULL,role TEXT NOT NULL,skills TEXT NOT NULL,availability INTEGER NOT NULL DEFAULT 80,workload INTEGER NOT NULL DEFAULT 0,daily_rate DOUBLE PRECISION NOT NULL DEFAULT 0,user_id INTEGER REFERENCES users(id) ON DELETE SET NULL)""")
    op.execute("""CREATE TABLE IF NOT EXISTS project_members(id SERIAL PRIMARY KEY,project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,role TEXT NOT NULL DEFAULT 'MEMBER',created_at TEXT NOT NULL,UNIQUE(project_id,user_id))""")
    op.execute("""CREATE TABLE IF NOT EXISTS analyses(id SERIAL PRIMARY KEY,project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,payload TEXT NOT NULL,created_at TEXT NOT NULL)""")
    op.execute("""CREATE TABLE IF NOT EXISTS scenarios(id SERIAL PRIMARY KEY,project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,team_size INTEGER NOT NULL,deadline_days INTEGER NOT NULL,budget DOUBLE PRECISION NOT NULL,scope_factor DOUBLE PRECISION NOT NULL,result TEXT NOT NULL,created_at TEXT NOT NULL)""")
    op.execute("""CREATE TABLE IF NOT EXISTS notifications(id SERIAL PRIMARY KEY,project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,type TEXT NOT NULL,title TEXT NOT NULL,message TEXT NOT NULL,read INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL)""")
    op.execute("""CREATE TABLE IF NOT EXISTS activity(id SERIAL PRIMARY KEY,project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,title TEXT NOT NULL,detail TEXT NOT NULL,created_at TEXT NOT NULL)""")
    op.execute("""CREATE TABLE IF NOT EXISTS analytics_snapshots(id SERIAL PRIMARY KEY,project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,health INTEGER NOT NULL,progress INTEGER NOT NULL,risk_score DOUBLE PRECISION NOT NULL,workload DOUBLE PRECISION NOT NULL,critical_path_days DOUBLE PRECISION NOT NULL,created_at TEXT NOT NULL)""")
    op.execute("CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_dependencies_project ON dependencies(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_risks_project ON risks(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_team_project ON team_members(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_activity_project_created ON activity(project_id,created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_project_created ON analytics_snapshots(project_id,created_at)")

def downgrade():
    for table in ["analytics_snapshots","activity","notifications","scenarios","analyses","project_members","team_members","risks","dependencies","tasks","projects","users"]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
