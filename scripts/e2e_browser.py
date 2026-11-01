"""Local, opt-in browser smoke test. Requires a running app and isolated disposable DB.
See TESTING.md. This test creates projects and deletes its temporary dataset/action.
"""
import io, os, uuid
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from openpyxl import load_workbook
from reportlab.pdfgen import canvas

URL=os.environ.get('AEGIS_E2E_URL')
if not URL: raise SystemExit('Set AEGIS_E2E_URL only after starting the app with an isolated disposable database.')
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    context=browser.new_context(accept_downloads=True,viewport={'width':1280,'height':900})
    page=context.new_page(); errors=[]
    page.on('pageerror',lambda err: errors.append(str(err)))
    page.goto(URL,wait_until='domcontentloaded',timeout=90000)
    expect(page.get_by_text('Campaign intelligence, under your control.')).to_be_visible(timeout=60000)
    project='E2E '+uuid.uuid4().hex[:8]
    page.get_by_placeholder('New project name').fill(project)
    page.get_by_role('button',name='Create project').click()
    expect(page.get_by_text('Project created.')).to_be_visible()
    expect(page.get_by_text('Active project: '+project)).to_be_visible()
    page.get_by_role('button',name='Load sample',exact=True).click()
    expect(page.get_by_text('Synthetic sample loaded and saved.')).to_be_visible()
    expect(page.get_by_text('38.17%',exact=True)).to_be_visible()
    expect(page.get_by_text('Spring B: bounce rate exceeds 5% threshold',exact=False)).to_be_visible()
    expect(page.get_by_text('Summer B: bounce rate exceeds 5% threshold',exact=False)).to_be_visible()
    page.get_by_label('Market filter').click()
    page.get_by_role('option',name='Coast').click()
    expect(page.get_by_text('Applied range: All dates · Rows: 2')).to_be_visible()
    page.get_by_label('Market filter').click()
    page.get_by_role('option',name='All markets').click()
    page.get_by_role('button',name='Try sample 2025 vs 2024').click()
    expect(page.get_by_text('Applied range: 2025-01-01 to 2025-08-31 · Rows: 3')).to_be_visible()
    expect(page.get_by_text('Open rate: 39.07% vs 37.23%',exact=False)).to_be_visible()
    with page.expect_download() as downloaded: page.get_by_role('button',name='Export Excel').click()
    download=downloaded.value
    with download.path().open('rb') as f:
        wb=load_workbook(io.BytesIO(f.read()),read_only=True,data_only=True)
        assert wb.sheetnames==['Campaign Data','Market Summary','Type Summary','Year Summary','KPI Summary','Insights']
        assert wb['Campaign Data'].max_row==4
    # Import validation and dataset selection/deletion.
    page.locator('input[type=file]').nth(0).set_input_files({'name':'bad.csv','mimeType':'text/csv','buffer':b'bad,columns\n1,2'})
    page.get_by_role('button',name='Upload campaign').click()
    expect(page.get_by_text('Campaign upload failed:',exact=False)).to_be_visible()
    page.locator('input[type=file]').nth(0).set_input_files({'name':'synthetic-upload.csv','mimeType':'text/csv','buffer':(root/'data/sample_campaigns.csv').read_bytes()})
    page.get_by_role('button',name='Upload campaign').click()
    expect(page.get_by_text('Saved synthetic-upload.csv.')).to_be_visible()
    page.locator('p').filter(has_text='synthetic-upload.csv · ID').locator('xpath=..').get_by_role('button',name='Delete').click()
    expect(page.get_by_text('Dataset deleted.')).to_be_visible()
    # Upload a synthetic TXT and a real generated text PDF, then retrieve by keyword.
    page.locator('input[type=file]').nth(1).set_input_files({'name':'brief.txt','mimeType':'text/plain','buffer':b'Aegis marmalade campaign source passage.'})
    page.get_by_role('button',name='Add document').click()
    expect(page.get_by_text('Document saved: brief.txt.')).to_be_visible(timeout=30000)
    pdf=io.BytesIO(); cv=canvas.Canvas(pdf); cv.drawString(50,750,'Orchard PDF source evidence'); cv.save()
    page.locator('input[type=file]').nth(1).set_input_files({'name':'evidence.pdf','mimeType':'application/pdf','buffer':pdf.getvalue()})
    page.get_by_role('button',name='Add document').click()
    expect(page.get_by_text('Document saved: evidence.pdf.')).to_be_visible(timeout=30000)
    page.get_by_placeholder('Ask about markets or search document keywords…').fill('orchard')
    page.get_by_role('button',name='Find evidence').click()
    expect(page.get_by_text('Orchard PDF source evidence',exact=False)).to_be_visible()
    page.get_by_placeholder('Ask about markets or search document keywords…').fill('Spring')
    page.get_by_role('button',name='Find evidence').click()
    expect(page.get_by_text('Matching campaign names: Spring B',exact=False)).to_be_visible()
    page.get_by_placeholder('Paste email HTML here').fill('<html><body><img src="x"><a href="http://example.com">hi</a></body></html>')
    page.get_by_role('button',name='Check HTML').click()
    expect(page.get_by_text('Image missing non-empty alt text',exact=False)).to_be_visible()
    expect(page.get_by_text('Not HTTPS',exact=False)).to_be_visible()
    page.locator('input[type=file]').nth(2).set_input_files({'name':'audience.csv','mimeType':'text/csv','buffer':b'email\na@example.com\na@example.com\n'})
    page.get_by_role('button',name='Run checks').click()
    expect(page.get_by_text('Duplicate email values: 1',exact=False)).to_be_visible()
    check=page.get_by_role('checkbox').first; check.click(); expect(check).to_be_checked()
    page.get_by_placeholder('Action',exact=True).fill('Review synthetic campaign')
    page.get_by_placeholder('Owner',exact=True).fill('Tester')
    page.get_by_role('button',name='Add',exact=True).click()
    expect(page.get_by_text('Review synthetic campaign',exact=False)).to_be_visible()
    page.reload(wait_until='domcontentloaded')
    expect(page.get_by_role('checkbox').first).to_be_checked(timeout=30000)
    expect(page.get_by_text('Review synthetic campaign',exact=False)).to_be_visible()
    # Switching projects is session-only; locate and reopen the project after reload.
    expect(page.get_by_text(project,exact=True)).to_be_visible()
    assert not errors, f'Browser page errors: {errors}'
    print('PASS: projects, import validation, dataset deletion, market filters, analytics, year comparison, Excel export, TXT/PDF upload and retrieval, campaign search, HTML/URL QA, audience checks, checklist and action persistence')
    context.close();browser.close()
