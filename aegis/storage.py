"""SQLite single-user storage with migration from v0.6. No security boundary."""
import os, sqlite3
from pathlib import Path
def database_path():
    # Preserve access to existing workspaces. New explicit setting takes precedence.
    configured = os.getenv('AEGIS_DB_PATH') or os.getenv('FABLE_DB_PATH')
    if configured: return Path(configured)
    new = Path('workspace/aegis.sqlite3'); legacy = Path('workspace/fable.sqlite3')
    return new if new.exists() or not legacy.exists() else legacy
DB = database_path()
CHECKS=['Audience and suppression rules reviewed','Consent and eligibility confirmed','Links, tracking and rendering reviewed','Content and approvals complete','Test send reviewed','Deployment approved']

def connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    try:
        c.execute('BEGIN IMMEDIATE')
        c.execute('CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)')
        c.execute("INSERT OR IGNORE INTO projects(id,name) VALUES (1,'Default')")
        for table, fields in {
            'campaigns':'filename TEXT NOT NULL, content BLOB NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP',
            'documents':'name TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP',
            'actions':"title TEXT NOT NULL, owner TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Open', created_at TEXT DEFAULT CURRENT_TIMESTAMP"
        }.items():
            c.execute(f'CREATE TABLE IF NOT EXISTS {table}(id INTEGER PRIMARY KEY, {fields}, project_id INTEGER NOT NULL DEFAULT 1)')
            cols={r['name'] for r in c.execute(f'PRAGMA table_info({table})')}
            if 'project_id' not in cols: c.execute(f'ALTER TABLE {table} ADD COLUMN project_id INTEGER NOT NULL DEFAULT 1')
        # v0.6 checklist had UNIQUE(title), incompatible with per-project checklists.
        old=c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checklist'").fetchone()
        if old and 'project_id' not in {r['name'] for r in c.execute('PRAGMA table_info(checklist)')}:
            c.execute('ALTER TABLE checklist RENAME TO checklist_v06')
            c.execute('CREATE TABLE checklist(id INTEGER PRIMARY KEY, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, project_id INTEGER NOT NULL DEFAULT 1, UNIQUE(project_id,title))')
            c.execute('INSERT INTO checklist(id,title,done,project_id) SELECT id,title,done,1 FROM checklist_v06')
            c.execute('DROP TABLE checklist_v06')
        else:
            c.execute('CREATE TABLE IF NOT EXISTS checklist(id INTEGER PRIMARY KEY, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, project_id INTEGER NOT NULL DEFAULT 1, UNIQUE(project_id,title))')
        c.executemany('INSERT OR IGNORE INTO checklist(title,project_id) VALUES (?,1)',[(x,) for x in CHECKS])
        c.execute('PRAGMA user_version=7'); c.commit()
    except Exception: c.rollback(); c.close(); raise
    return c

def projects():
    with connect() as c: return [dict(r) for r in c.execute('SELECT * FROM projects ORDER BY id')]
def add_project(name):
    name=name.strip()
    if not name or len(name)>100: raise ValueError('Project name must be 1–100 characters.')
    with connect() as c:
        id=c.execute('INSERT INTO projects(name) VALUES (?)',(name,)).lastrowid
        c.executemany('INSERT INTO checklist(title,project_id) VALUES (?,?)',[(x,id) for x in CHECKS]); return id
def delete_project(id):
    id=int(id)
    if id==1: raise ValueError('The default project cannot be deleted.')
    with connect() as c:
        for table in ('campaigns','documents','actions','checklist'): c.execute(f'DELETE FROM {table} WHERE project_id=?',(id,))
        c.execute('DELETE FROM projects WHERE id=?',(id,))
def insert_campaign(name,data,project_id=1):
    with connect() as c: return c.execute('INSERT INTO campaigns(filename,content,project_id) VALUES (?,?,?)',(name,data,project_id)).lastrowid
def campaigns(project_id=1):
    with connect() as c: return [dict(r) for r in c.execute('SELECT id,filename,created_at FROM campaigns WHERE project_id=? ORDER BY id DESC',(project_id,))]
def campaign(id,project_id=1):
    with connect() as c: return c.execute('SELECT id,filename,content FROM campaigns WHERE id=? AND project_id=?',(int(id),project_id)).fetchone()
def delete_campaign(id,project_id=1):
    with connect() as c: c.execute('DELETE FROM campaigns WHERE id=? AND project_id=?',(int(id),project_id))
def latest_campaign(project_id=1):
    with connect() as c: return c.execute('SELECT id,filename,content FROM campaigns WHERE project_id=? ORDER BY id DESC LIMIT 1',(project_id,)).fetchone()
def add_document(name,content,project_id=1):
    with connect() as c: c.execute('INSERT INTO documents(name,content,project_id) VALUES (?,?,?)',(name,content,project_id))
def documents(project_id=1):
    with connect() as c: return [dict(r) for r in c.execute('SELECT id,name,content FROM documents WHERE project_id=? ORDER BY id DESC',(project_id,))]
def add_action(title,owner,project_id=1):
    with connect() as c: c.execute('INSERT INTO actions(title,owner,project_id) VALUES (?,?,?)',(title,owner,project_id))
def actions(project_id=1):
    with connect() as c: return [dict(r) for r in c.execute('SELECT id,title,owner,status FROM actions WHERE project_id=? ORDER BY id DESC',(project_id,))]
def toggle_action(id,project_id=1):
    with connect() as c: c.execute("UPDATE actions SET status=CASE WHEN status='Open' THEN 'Done' ELSE 'Open' END WHERE id=? AND project_id=?",(int(id),project_id))
def checklist(project_id=1):
    with connect() as c: return [dict(r) for r in c.execute('SELECT id,title,done FROM checklist WHERE project_id=? ORDER BY id',(project_id,))]
def toggle_check(id,project_id=1):
    with connect() as c: c.execute('UPDATE checklist SET done=1-done WHERE id=? AND project_id=?',(int(id),project_id))
def delete_document(id,project_id=1):
    with connect() as c: c.execute('DELETE FROM documents WHERE id=? AND project_id=?',(int(id),project_id))
def delete_action(id,project_id=1):
    with connect() as c: c.execute('DELETE FROM actions WHERE id=? AND project_id=?',(int(id),project_id))
