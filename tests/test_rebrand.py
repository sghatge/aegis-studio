from aegis import storage

def test_database_path_prefers_aegis(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path); monkeypatch.delenv('AEGIS_DB_PATH',raising=False); monkeypatch.delenv('FABLE_DB_PATH',raising=False)
    assert str(storage.database_path())=='workspace/aegis.sqlite3'
    (tmp_path/'workspace').mkdir(); (tmp_path/'workspace'/'fable.sqlite3').touch()
    assert str(storage.database_path())=='workspace/fable.sqlite3'
    (tmp_path/'workspace'/'aegis.sqlite3').touch()
    assert str(storage.database_path())=='workspace/aegis.sqlite3'

def test_database_env_precedence(tmp_path,monkeypatch):
    monkeypatch.setenv('FABLE_DB_PATH',str(tmp_path/'legacy.db'))
    assert storage.database_path()==tmp_path/'legacy.db'
    monkeypatch.setenv('AEGIS_DB_PATH',str(tmp_path/'new.db'))
    assert storage.database_path()==tmp_path/'new.db'
