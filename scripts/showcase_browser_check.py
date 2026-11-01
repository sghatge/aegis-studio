"""Browser smoke test for the standalone showcase; uses isolated browser context."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    context=browser.new_context()
    page=context.new_page(); errors=[]; network=[]
    page.on('pageerror',lambda err: errors.append(str(err)))
    page.on('request',lambda request: network.append(request.url) if request.url.startswith(('http://','https://')) else None)
    page.goto((Path(__file__).resolve().parents[1]/'docs'/'index.html').as_uri())
    expect(page.get_by_text('38.17%',exact=True)).to_be_visible()
    page.locator('#market').select_option(label='Coast')
    expect(page.locator('#count')).to_have_text('(2)')
    expect(page.locator('#insights')).to_contain_text('Summer B')
    page.locator('#demo-query').fill('delivery')
    page.locator('#demo-search').click()
    expect(page.locator('#demo-answer')).to_contain_text('Spring B')
    check=page.locator('#demo-checks input').first
    check.check(); page.reload(); expect(check).to_be_checked()
    page.get_by_role('tab',name='Operations').click()
    expect(page.locator('#features')).to_contain_text('Campaign QA')
    assert not errors, errors
    assert not network, network
    print('PASS: showcase filters, sample findings, search, local checklist persistence, tabs, and no external HTTP requests')
    context.close();browser.close()
