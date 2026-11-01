import reflex as rx
from pathlib import Path
from . import core, storage, documents

class State(rx.State):
    message: str = 'Choose a project and load or upload campaign data.'
    project_id: int = 1
    project_name: str = 'Default'
    project_input: str = ''
    project_list: list[dict] = []
    dataset_list: list[dict] = []
    dataset_id: int = 0
    delete_confirm: bool = False
    start_date: str = ''
    end_date: str = ''
    active_start: str = ''
    active_end: str = ''
    bounce_input: str = '5'
    min_input: str = '100'
    bounce_threshold: float = 5.0
    min_delivered: int = 100
    comparison: str = 'Set both dates and apply the range to compare with the prior year.'
    open_label: str = '—'
    click_label: str = '—'
    conversion_label: str = '—'
    bounce_label: str = '—'
    open_bar: int = 0
    click_bar: int = 0
    conversion_bar: int = 0
    bounce_bar: int = 0
    active_range: str = 'All dates'
    selected_rows: int = 0
    market: str = 'All markets'
    market_options: list[str] = ['All markets']
    summary: str = 'No campaign data loaded.'
    markets: str = ''
    types: str = ''
    years: str = ''
    findings: str = ''
    doc_list: list[dict] = []
    action_list: list[dict] = []
    check_list: list[dict] = []
    question: str = ''
    answer: str = ''
    html: str = ''
    qa_result: str = ''
    urls: str = ''
    action_title: str = ''
    action_owner: str = ''
    audience_result: str = ''

    def current(self):
        if not self.dataset_id: return None
        return storage.campaign(self.dataset_id,self.project_id)
    def refresh(self):
        self.project_list=storage.projects()
        if not any(p['id']==self.project_id for p in self.project_list): self.project_id=1
        self.project_name=next(p['name'] for p in self.project_list if p['id']==self.project_id)
        self.doc_list=storage.documents(self.project_id); self.action_list=storage.actions(self.project_id); self.check_list=storage.checklist(self.project_id)
        self.dataset_list=storage.campaigns(self.project_id)
        if not any(d['id']==self.dataset_id for d in self.dataset_list): self.dataset_id=self.dataset_list[0]['id'] if self.dataset_list else 0
        self.open_label='—'; self.click_label='—'; self.conversion_label='—'; self.bounce_label='—'
        self.open_bar=0; self.click_bar=0; self.conversion_bar=0; self.bounce_bar=0; self.selected_rows=0
        self.active_range=f'{self.active_start or "Earliest"} to {self.active_end or "Latest"}' if self.active_start or self.active_end else 'All dates'
        self.summary='No campaign data loaded.'; self.markets=''; self.types=''; self.years=''; self.findings=''; self.comparison='Set both dates and apply the range to compare with the prior year.'
        row=self.current()
        self.market_options=['All markets']
        if row:
            try:
                all_df=core.read_campaigns(row['content'],row['filename'])
                self.market_options=['All markets'] + sorted(all_df['market'].unique().tolist())
                if self.market not in self.market_options: self.market='All markets'
                if self.market != 'All markets': all_df=all_df[all_df['market']==self.market]
                df=core.filter_dates(all_df,self.active_start,self.active_end)
                if self.active_start and self.active_end: self.comparison=core.year_comparison(all_df,self.active_start,self.active_end,self.min_delivered)
                if df.empty:
                    self.summary=f"{row['filename']}: no campaigns in the selected range."; return
                m=core.metrics(df); self.selected_rows=m['campaigns']
                def visual(v): return ('N/A',0) if v is None else (f'{v:.2f}%',round(max(0.0,min(100.0,v))))
                self.open_label,self.open_bar=visual(m['open_rate']); self.click_label,self.click_bar=visual(m['ctr']); self.conversion_label,self.conversion_bar=visual(m['conversion_rate']); self.bounce_label,self.bounce_bar=visual(m['bounce_rate'])
                def rate(v): return f'{v:.2f}%' if v is not None else 'N/A'
                self.summary=f"{row['filename']} • {m['campaigns']} campaigns • {m['sent']:,} sent • {m['delivered']:,} delivered\nOpen {rate(m['open_rate'])}  |  CTR {rate(m['ctr'])}  |  CTOR {rate(m['ctor'])}  |  Conversion {rate(m['conversion_rate'])}  |  Bounce {rate(m['bounce_rate'])}"
                def describe(frame, key):
                    return '\n'.join(f"{r[key]} — {r['campaigns']} campaigns; {r['conversions']} conversions; conversion {rate(r['conversion_rate'])}; bounce {rate(r['bounce_rate'])}" for _,r in frame.iterrows())
                self.markets=describe(core.grouped(df,'market'),'market'); self.types=describe(core.grouped(df,'type'),'type')
                yr=df.copy(); yr['year']=yr.date.dt.year
                self.years=describe(core.grouped(yr,'year'),'year')
                self.findings='\n'.join(core.quality_findings(df,self.bounce_threshold,self.min_delivered)) or 'No anomalies flagged by current rules.'
            except Exception as e: self.message=f'Could not read saved campaign data: {e}'
    def create_project(self):
        try:
            self.project_id=storage.add_project(self.project_input); self.project_input=''; self.dataset_id=0; self.answer=''; self.refresh(); self.message='Project created.'
        except Exception as e: self.message=f'Could not create project: {e}'
    def select_project(self,id: int):
        self.project_id=id; self.dataset_id=0; self.answer=''; self.delete_confirm=False; self.refresh(); self.message=f'Project: {self.project_name}.'
    def request_delete_project(self):
        if self.project_id==1: self.message='The Default project cannot be deleted.'; return
        self.delete_confirm=True
    def cancel_delete_project(self): self.delete_confirm=False
    def confirm_delete_project(self):
        if self.delete_confirm:
            storage.delete_project(self.project_id); self.project_id=1; self.dataset_id=0; self.delete_confirm=False; self.answer=''; self.refresh(); self.message='Project and its datasets, documents, checklist and actions deleted.'
    def select_dataset(self,id: int): self.dataset_id=id; self.answer=''; self.refresh(); self.message='Dataset selected.'
    def delete_dataset(self,id: int):
        storage.delete_campaign(id,self.project_id)
        if self.dataset_id==id: self.dataset_id=0
        self.answer=''; self.refresh(); self.message='Dataset deleted.'
    def change_market(self, value: str):
        self.market=value; self.answer=''; self.refresh(); self.message='Market filter applied.'
    def apply_filters(self):
        try:
            import pandas as pd
            core.filter_dates(pd.DataFrame({'date':pd.to_datetime([])}),self.start_date,self.end_date)
            bounce=float(self.bounce_input); minimum=int(self.min_input)
            if not 0<=bounce<=100 or minimum<0: raise ValueError('Threshold must be 0–100 and minimum non-negative.')
            self.active_start=self.start_date; self.active_end=self.end_date; self.bounce_threshold=bounce; self.min_delivered=minimum; self.refresh(); self.message='Date range and quality rules applied.'
        except Exception as e: self.message=f'Invalid filter: {e}'
    def sample_2025(self):
        self.start_date='2025-01-01'; self.end_date='2025-08-31'; self.apply_filters()
    def clear_filters(self):
        self.start_date=''; self.end_date=''; self.active_start=''; self.active_end=''; self.refresh(); self.message='Date range cleared.'
    def load_sample(self):
        data=Path('data/sample_campaigns.csv').read_bytes(); self.dataset_id=storage.insert_campaign('sample_campaigns.csv',data,self.project_id); self.refresh(); self.message='Synthetic sample loaded and saved.'
    async def upload_campaign(self, files: list[rx.UploadFile]):
        for file in files:
            try:
                data=await file.read(); core.read_campaigns(data,file.filename); self.dataset_id=storage.insert_campaign(file.filename,data,self.project_id); self.message=f'Saved {file.filename}.'
            except Exception as e: self.message=f'Campaign upload failed: {e}'
        self.refresh()
    async def upload_doc(self, files: list[rx.UploadFile]):
        for file in files:
            try:
                text=documents.convert(file.filename,await file.read()); storage.add_document(file.filename,text,self.project_id); self.message=f'Document saved: {file.filename}.'
            except Exception as e: self.message=f'Document upload failed: {e}'
        self.refresh()
    async def upload_audience(self, files: list[rx.UploadFile]):
        for file in files:
            try: self.audience_result='\n'.join(core.audience_qa(await file.read()))
            except Exception as e: self.audience_result=f'Audience check failed: {e}'
    def ask(self):
        row=self.current(); df=core.filter_dates(core.read_campaigns(row['content'],row['filename']),self.active_start,self.active_end) if row else None
        if df is not None and self.market != 'All markets': df=df[df.market==self.market]
        self.answer=core.assistant_answer(self.question,df,storage.documents(self.project_id))
    def check_html(self): self.qa_result='\n'.join(core.html_qa(self.html)) or 'No issues flagged by current rules.'
    def check_urls(self): self.qa_result='\n'.join(core.url_qa(self.urls.splitlines())) or 'No issues flagged by current rules.'
    def add_action(self):
        if not self.action_title.strip(): self.message='Enter an action title.'; return
        storage.add_action(self.action_title.strip(),self.action_owner.strip() or 'Unassigned',self.project_id); self.action_title=''; self.action_owner=''; self.refresh()
    def toggle_action(self, id: int): storage.toggle_action(id,self.project_id); self.refresh()
    def delete_action(self, id: int): storage.delete_action(id,self.project_id); self.refresh()
    def toggle_check(self, id: int): storage.toggle_check(id,self.project_id); self.refresh()
    def delete_doc(self, id: int): storage.delete_document(id,self.project_id); self.refresh()
    def export(self):
        row=self.current()
        if not row: self.message='Load campaign data before exporting.'; return
        df=core.filter_dates(core.read_campaigns(row['content'],row['filename']),self.active_start,self.active_end)
        if self.market != 'All markets': df=df[df.market==self.market]
        if df.empty: self.message='No rows in the selected date range.'; return
        return rx.download(data=core.workbook(df,core.quality_findings(df,self.bounce_threshold,self.min_delivered)),filename='aegis-report.xlsx',mime_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

def metric_card(title, label, bar):
    return rx.box(rx.text(title,size='2',color='#64748b'),rx.heading(label,size='6',margin_y='7px'),rx.progress(value=bar,max=100,color_scheme='teal',height='7px'),background='white',border='1px solid #e2e8f0',border_radius='14px',padding='18px',width='100%')
def panel(title, *children):
    return rx.box(rx.heading(title,size='5',margin_bottom='12px'),*children,background='white',border='1px solid #e2e8f0',border_radius='14px',padding='20px',width='100%')
def pre(value): return rx.text(value,white_space='pre-wrap',font_size='14px',color='#334155',line_height='1.7')
def upload_box(id, handler, label, accept):
    return rx.hstack(rx.upload(rx.button('Choose file',variant='soft'),rx.text(rx.selected_files(id),size='1'),id=id,accept=accept,max_files=1),rx.button(label,on_click=handler(rx.upload_files(upload_id=id)),size='2'),wrap='wrap')
def project_row(row):
    return rx.hstack(rx.text(row['name'],size='2'),rx.spacer(),rx.button('Open',on_click=State.select_project(row['id']),size='1',variant='soft'),width='100%')
def dataset_row(row):
    return rx.hstack(rx.text(row['filename'], ' · ID ', row['id'],size='2'),rx.spacer(),rx.button('Select',on_click=State.select_dataset(row['id']),size='1',variant='soft'),rx.button('Delete',on_click=State.delete_dataset(row['id']),size='1',variant='soft',color_scheme='red'),width='100%',wrap='wrap')
def doc_row(row):
    return rx.hstack(rx.text(row['name'],size='2'),rx.spacer(),rx.button('Delete',on_click=State.delete_doc(row['id']),size='1',variant='soft',color_scheme='red'),width='100%')
def action_row(row):
    return rx.hstack(rx.text(row['title'], ' · ', row['owner'], ' · ', row['status'],size='2'),rx.spacer(),rx.button('Toggle',on_click=State.toggle_action(row['id']),size='1',variant='soft'),rx.button('Delete',on_click=State.delete_action(row['id']),size='1',variant='soft',color_scheme='red'),width='100%',wrap='wrap')
def check_row(row):
    return rx.hstack(rx.checkbox(checked=row['done'] == 1,on_change=lambda _: State.toggle_check(row['id']),aria_label=row['title']),rx.text(row['title'],size='2'),width='100%')
def index():
    return rx.box(rx.box(rx.hstack(rx.box(rx.text('AEGIS / 0.7',font_weight='bold',color='#76dfc9',letter_spacing='0.14em',size='2'),rx.heading('Aegis Studio',size='8',color='white'),rx.text('Campaign intelligence, under your control.',color='#cbd5e1',margin_top='8px'),rx.text('LOCAL-FIRST  ·  NO EXTERNAL AI',color='#76dfc9',size='2',weight='bold',margin_top='10px')),rx.spacer(),rx.badge('PERSONAL EDITION',color_scheme='teal',variant='soft'),align='center',wrap='wrap'),background='#102b2e',padding='32px'),
      rx.container(rx.vstack(rx.callout(State.message,icon='info',width='100%',color_scheme='teal'),
      panel('Projects',rx.text('Active project: ',State.project_name,weight='bold'),rx.hstack(rx.input(placeholder='New project name',value=State.project_input,on_change=State.set_project_input),rx.button('Create project',on_click=State.create_project),width='100%',margin_y='10px'),rx.vstack(rx.foreach(State.project_list,project_row),width='100%'),rx.button('Delete current project',on_click=State.request_delete_project,color_scheme='red',variant='soft',margin_top='10px'),rx.cond(State.delete_confirm,rx.hstack(rx.text('Delete this project and ALL its data?'),rx.button('Confirm deletion',on_click=State.confirm_delete_project,color_scheme='red'),rx.button('Cancel',on_click=State.cancel_delete_project,variant='soft'),wrap='wrap'))),
      panel('Datasets',rx.text('Selected dataset ID: ',State.dataset_id,size='2',weight='bold'),rx.text('Select a dataset or delete it permanently. New uploads are selected automatically.',size='2',color='#64748b'),rx.vstack(rx.foreach(State.dataset_list,dataset_row),width='100%',margin_top='10px')),
      panel('Date range & quality rules',rx.text('Market',size='2',weight='bold'),rx.select.root(rx.select.trigger(aria_label='Market filter'),rx.select.content(rx.foreach(State.market_options,lambda option: rx.select.item(option,value=option))),value=State.market,on_change=State.change_market),rx.text('Dates inclusive, YYYY-MM-DD. Comparison uses the same calendar dates in the prior year.',size='2',color='#64748b'),rx.hstack(rx.input(placeholder='Start: 2025-01-01',value=State.start_date,on_change=State.set_start_date),rx.input(placeholder='End: 2025-08-31',value=State.end_date,on_change=State.set_end_date),wrap='wrap',margin_y='10px'),rx.hstack(rx.text('Bounce threshold %'),rx.input(value=State.bounce_input,on_change=State.set_bounce_input,width='90px'),rx.text('Min delivered'),rx.input(value=State.min_input,on_change=State.set_min_input,width='100px'),wrap='wrap'),rx.hstack(rx.button('Apply',on_click=State.apply_filters),rx.button('Clear dates',on_click=State.clear_filters,variant='soft'),rx.button('Try sample 2025 vs 2024',on_click=State.sample_2025,variant='soft'),wrap='wrap',margin_top='10px'),rx.text('Applied range: ',State.active_range,' · Rows: ',State.selected_rows,size='2',color='#64748b',margin_top='10px')),
      rx.grid(metric_card('Open rate',State.open_label,State.open_bar),metric_card('Click-through rate',State.click_label,State.click_bar),metric_card('Conversion rate',State.conversion_label,State.conversion_bar),metric_card('Bounce rate',State.bounce_label,State.bounce_bar),columns=rx.breakpoints(initial='2',md='4'),spacing='4',width='100%'),
      panel('Year-on-year comparison',pre(State.comparison)),
      panel('Campaign analytics',rx.hstack(rx.button('Load sample',on_click=State.load_sample),rx.button('Export Excel',on_click=State.export,variant='outline'),wrap='wrap'),rx.box(upload_box('campaign',State.upload_campaign,'Upload campaign', {'.csv':['text/csv'],'.xlsx':['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']}),margin_y='14px'),pre(State.summary)),
      rx.grid(panel('Markets',pre(State.markets)),panel('Campaign types',pre(State.types)),panel('Year summaries',pre(State.years)),columns=rx.breakpoints(initial='1',md='3'),spacing='4',width='100%'),
      panel('Data quality & anomalies',pre(State.findings)),
      panel('Document library',rx.text('Extract and search local documents. Text is stored in your workspace database.',size='2',color='#64748b'),upload_box('docs',State.upload_doc,'Add document',{'.pdf':['application/pdf'],'.docx':['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],'.pptx':['application/vnd.openxmlformats-officedocument.presentationml.presentation'],'.xlsx':['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],'.txt':['text/plain'],'.md':['text/markdown'],'.csv':['text/csv'],'.html':['text/html']}),rx.vstack(rx.foreach(State.doc_list,doc_row),width='100%',margin_top='12px')),
      panel('Ask Aegis',rx.text('Local, deterministic evidence retrieval — no external AI or generated causal claims.',size='2',color='#64748b'),rx.hstack(rx.input(placeholder='Ask about markets or search document keywords…',value=State.question,on_change=State.set_question,width='100%'),rx.button('Find evidence',on_click=State.ask),width='100%',margin_y='12px'),pre(State.answer)),
      panel('Email & URL QA',rx.text('Structural checks only; no links are visited.',size='2',color='#64748b'),rx.text_area(placeholder='Paste email HTML here',value=State.html,on_change=State.set_html,width='100%',height='140px',margin_y='10px'),rx.button('Check HTML',on_click=State.check_html),rx.text_area(placeholder='Or paste one URL per line',value=State.urls,on_change=State.set_urls,width='100%',height='100px',margin_y='10px'),rx.button('Check URLs',on_click=State.check_urls,variant='soft'),pre(State.qa_result)),
      panel('Audience data quality',rx.text('CSV only. Avoid personal data; findings are heuristics, not consent validation.',size='2',color='#64748b'),upload_box('audience',State.upload_audience,'Run checks',{'.csv':['text/csv']}),pre(State.audience_result)),
      rx.grid(panel('Deployment checklist',rx.vstack(rx.foreach(State.check_list,check_row),spacing='3',width='100%')),panel('Action tracker',rx.input(placeholder='Action',value=State.action_title,on_change=State.set_action_title,width='100%',margin_bottom='8px'),rx.hstack(rx.input(placeholder='Owner',value=State.action_owner,on_change=State.set_action_owner),rx.button('Add',on_click=State.add_action),width='100%'),rx.vstack(rx.foreach(State.action_list,action_row),width='100%',margin_top='12px')),columns=rx.breakpoints(initial='1',md='2'),spacing='4',width='100%'),
      rx.text('Local prototype • Human review required • No authentication or live sending',size='2',color='#64748b',padding_y='20px'),spacing='4',width='100%',padding_y='24px'),size='4'),background='#f4f6fb',min_height='100vh')
app=rx.App(theme=rx.theme(accent_color='teal',radius='large'))
app.add_page(index,on_load=State.refresh,title='Aegis Studio')
