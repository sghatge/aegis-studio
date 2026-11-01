import sqlite3
import pytest
from aegis import core, storage
from test_core import SAMPLE

def test_date_filter_and_comparison():
    df=core.read_campaigns(SAMPLE,'test.csv')
    selected=core.filter_dates(df,'2025-01-01','2025-08-31')
    assert len(selected)==3
    result=core.year_comparison(df,'2025-01-01','2025-08-31')
    assert '2024-01-01–2024-08-31' in result and 'percentage points' in result
    assert 'Both periods need data' in core.year_comparison(df,'2023-01-01','2023-08-31')
    with pytest.raises(ValueError): core.filter_dates(df,'2025-12-31','2025-01-01')
    with pytest.raises(ValueError): core.filter_dates(df,'01/01/2025','')

def test_zero_denominator_leap_and_rules():
    df=core.read_campaigns(b'campaign,date,market,type,sent,delivered,opens,clicks,conversions,bounces\nx,2024-02-29,A,T,0,0,0,0,0,0\nx,2023-02-28,A,T,0,0,0,0,0,0','x.csv')
    assert 'N/A (zero denominator)' in core.year_comparison(df,'2024-02-29','2024-02-29')
    assert '2023-02-28' in core.year_comparison(df,'2024-02-29','2024-02-29')
    assert any('below' in s for s in core.quality_findings(df,min_delivered=10))
    assert any('share campaign' in s for s in core.quality_findings(__import__('pandas').concat([df,df])))
    with pytest.raises(ValueError): core.quality_findings(df,bounce_threshold=101)

def test_project_isolation_and_deletion(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'db.sqlite3')
    other=storage.add_project('Other')
    id=storage.insert_campaign('x.csv',SAMPLE,other)
    storage.add_document('a','text',other); storage.add_action('Test','Owner',other)
    assert not storage.campaigns(1) and storage.campaign(id,1) is None
    assert len(storage.checklist(other))==6 and not storage.documents(1)
    storage.toggle_check(storage.checklist(other)[0]['id'],1)
    assert storage.checklist(other)[0]['done']==0
    storage.delete_project(other)
    assert len(storage.projects())==1 and not storage.campaigns(other)
    with pytest.raises(ValueError): storage.delete_project(1)

def test_migrate_v06(tmp_path,monkeypatch):
    path=tmp_path/'legacy.db'; monkeypatch.setattr(storage,'DB',path)
    c=sqlite3.connect(path)
    c.executescript("""CREATE TABLE campaigns(id INTEGER PRIMARY KEY,filename TEXT NOT NULL,content BLOB NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE documents(id INTEGER PRIMARY KEY,name TEXT NOT NULL,content TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE actions(id INTEGER PRIMARY KEY,title TEXT NOT NULL,owner TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'Open',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE checklist(id INTEGER PRIMARY KEY,title TEXT UNIQUE NOT NULL,done INTEGER NOT NULL DEFAULT 0);
    INSERT INTO checklist(title,done) VALUES ('Test send reviewed',1);
    INSERT INTO actions(title,owner) VALUES ('Legacy action','Alex');"""); c.commit(); c.close()
    assert storage.actions()[0]['title']=='Legacy action'
    assert next(x for x in storage.checklist() if x['title']=='Test send reviewed')['done']==1
    p=storage.add_project('New'); assert len(storage.checklist(p))==6
    with storage.connect() as c: assert c.execute('PRAGMA user_version').fetchone()[0]==7
