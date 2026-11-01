import io
from pathlib import Path
import pandas as pd
import pytest
from aegis import core, documents, storage

SAMPLE=Path('data/sample_campaigns.csv').read_bytes()
def test_weighted_rates_and_years():
    df=core.read_campaigns(SAMPLE,'sample.csv'); m=core.metrics(df)
    assert m['campaigns']==6 and m['sent']==62500
    assert m['open_rate']==pytest.approx(23050/60380*100)
    assert len(core.grouped(df,'market'))==3
    assert df.date.dt.year.nunique()==2

def test_bad_input_and_zero():
    with pytest.raises(ValueError,match='Missing columns'): core.read_campaigns(b'a,b\n1,2','x.csv')
    df=core.read_campaigns(b'campaign,date,market,type,sent,delivered,opens,clicks,conversions,bounces\nx,2025-01-01,A,B,0,0,0,0,0,0','x.csv')
    assert core.metrics(df)['open_rate'] is None

def test_qa():
    result=core.html_qa('<html><body><img src="a"><a href="http://example.com">hi</a><script></script></body></html>')
    assert any('alt' in x for x in result) and any('HTTPS' in x for x in result) and any('Script' in x for x in result)
    assert any('Duplicate' in x for x in core.url_qa(['https://example.com','https://example.com']))
    assert any('consent' in x for x in core.audience_qa(b'email\na@example.com\na@example.com'))

def test_search_and_export():
    docs=[{'name':'report.txt','content':'Revenue rose.\n\nConversion fell in North.'}]
    assert core.find_passages(docs,'conversion')[0][1:3]==('report.txt',2)
    data=core.workbook(core.read_campaigns(SAMPLE,'sample.csv'),['=unsafe'])
    book=pd.ExcelFile(io.BytesIO(data)); assert len(book.sheet_names)==6
    assert pd.read_excel(io.BytesIO(data),sheet_name='Insights').iloc[0,0]=="'=unsafe"

def test_storage_roundtrip(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'aegis.db')
    storage.insert_campaign('test.csv',SAMPLE); assert storage.latest_campaign()['filename']=='test.csv'
    storage.add_document('a.txt','hello'); assert storage.documents()[0]['content']=='hello'
    storage.add_action('Review','A'); action=storage.actions()[0]; storage.toggle_action(action['id']); assert storage.actions()[0]['status']=='Done'
    check=storage.checklist()[0]; storage.toggle_check(check['id']); assert storage.checklist()[0]['done']==1
    storage.delete_document(storage.documents()[0]['id']); assert storage.documents()==[]

def test_document_text():
    assert documents.convert('test.txt',b'Hello')=='Hello'
    with pytest.raises(ValueError): documents.convert('bad.exe',b'bad')

def test_sample_bounce_flags_and_campaign_search():
    df=core.read_campaigns(SAMPLE,'sample.csv')
    findings=core.quality_findings(df)
    assert any('Spring B' in line and '5%' in line for line in findings)
    assert any('Summer B' in line and '5%' in line for line in findings)
    assert 'Matching campaign names: Spring A, Spring B' in core.assistant_answer('Spring',df,[])
