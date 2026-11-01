"""Pure calculations and deterministic checks. Rates use summed counts, not averages."""
from __future__ import annotations
import io, re
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs
import pandas as pd

REQUIRED = ['campaign','date','market','type','sent','delivered','opens','clicks','conversions','bounces']
COUNTS = ['sent','delivered','opens','clicks','conversions','bounces']
MAX_BYTES = 10 * 1024 * 1024

def read_campaigns(data: bytes, name: str) -> pd.DataFrame:
    if len(data) > MAX_BYTES: raise ValueError('File exceeds the 10 MB limit.')
    if name.lower().endswith('.csv'): df = pd.read_csv(io.BytesIO(data))
    elif name.lower().endswith('.xlsx'): df = pd.read_excel(io.BytesIO(data), engine='openpyxl')
    else: raise ValueError('Use a CSV or XLSX file.')
    df.columns = [str(c).strip().lower() for c in df.columns]
    if df.columns.duplicated().any(): raise ValueError('Column names must be unique after normalization.')
    missing = set(REQUIRED) - set(df.columns)
    if missing: raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    df = df[REQUIRED].copy()
    if df.empty: raise ValueError('The file has no campaign rows.')
    for col in ['campaign','market','type']:
        if df[col].isna().any() or df[col].astype(str).str.strip().eq('').any(): raise ValueError(f'{col} cannot be blank.')
        df[col] = df[col].astype(str).str.strip()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if df['date'].isna().any(): raise ValueError('Every date must be valid.')
    for col in COUNTS:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        if df[col].isna().any() or (df[col] < 0).any() or (df[col] % 1 != 0).any(): raise ValueError(f'{col} must contain non-negative whole numbers.')
        df[col] = df[col].astype('int64')
    return df

def metrics(df):
    sums = df[COUNTS].sum()
    def ratio(a,b): return float(sums[a] / sums[b] * 100) if sums[b] else None
    return {'campaigns': len(df), **{k:int(sums[k]) for k in COUNTS}, 'open_rate':ratio('opens','delivered'), 'ctr':ratio('clicks','delivered'), 'ctor':ratio('clicks','opens'), 'conversion_rate':ratio('conversions','delivered'), 'bounce_rate':ratio('bounces','sent')}

def grouped(df, key):
    return pd.DataFrame([{key: str(k), **metrics(g)} for k,g in df.groupby(key, dropna=False, sort=True)])

def anomalies(df):
    out=[]
    for _,r in df.iterrows():
        problems=[]
        if r.delivered > r.sent: problems.append('delivered exceeds sent')
        if r.bounces > r.sent: problems.append('bounces exceeds sent')
        if r.delivered + r.bounces > r.sent: problems.append('delivered plus bounces exceeds sent')
        if r.opens > r.delivered: problems.append('opens exceeds delivered (may be repeat events)')
        if r.clicks > r.opens: problems.append('clicks exceeds opens (may be repeat events or tracking differences)')
        if r.conversions > r.clicks: problems.append('conversions exceeds clicks (check attribution)')
        if r.sent and r.bounces / r.sent > .05: problems.append('bounce rate above 5% review threshold')
        if problems: out.append(f"{r.campaign}: " + '; '.join(problems))
    return out

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.issues=[]; self.has_html=False; self.has_body=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag == 'html': self.has_html=True
        if tag == 'body': self.has_body=True
        if tag == 'script': self.issues.append('Script tag found; email clients commonly block scripts.')
        if tag == 'img' and not (a.get('alt') or '').strip(): self.issues.append('Image missing non-empty alt text (decorative images may intentionally use empty alt).')
        if tag == 'a':
            href=a.get('href','').strip()
            if not href: self.issues.append('Anchor missing href.')
            else: self.links.append(href)

def url_qa(urls):
    findings=[]; seen=set()
    for url in urls:
        url=url.strip()
        if not url: continue
        if url in seen: findings.append(f'Duplicate URL: {url}')
        seen.add(url); p=urlparse(url)
        if p.scheme not in ('http','https') or not p.hostname: findings.append(f'Not an absolute HTTP(S) URL: {url}'); continue
        if p.scheme != 'https': findings.append(f'Not HTTPS: {url}')
        q=parse_qs(p.query)
        missing=[x for x in ('utm_source','utm_medium','utm_campaign') if not q.get(x)]
        if missing: findings.append(f'Missing tracking parameters ({", ".join(missing)}): {url}')
    return findings

def html_qa(html):
    p=Parser(); p.feed(html)
    if not p.has_html: p.issues.append('No html tag found; fragments may be intentional.')
    if not p.has_body: p.issues.append('No body tag found; fragments may be intentional.')
    return p.issues + url_qa(p.links)

def audience_qa(data: bytes):
    if len(data)>MAX_BYTES: raise ValueError('File exceeds the 10 MB limit.')
    df=pd.read_csv(io.BytesIO(data)); df.columns=[str(c).strip().lower() for c in df.columns]
    findings=[f'{len(df)} rows; {len(df.columns)} columns.']
    if 'email' in df:
        count=int(df['email'].astype(str).str.strip().str.lower().duplicated().sum()); findings.append(f'Duplicate email values: {count}.')
    else: findings.append('No email column: duplicate identifier check skipped.')
    for col in ('consent','suppressed'):
        if col not in df: findings.append(f'No {col} column; {col} cannot be reviewed.')
        else: findings.append(f'{col}: {int(df[col].isna().sum())} missing values; verify values and rules manually.')
    findings.append('Heuristics only: consent, eligibility, suppression logic and segment definitions require human verification.')
    return findings

def find_passages(documents, query):
    terms=set(re.findall(r'\w+', query.lower()))
    if not terms: return []
    results=[]
    for doc in documents:
        for i, paragraph in enumerate(re.split(r'\n\s*\n',doc['content'])):
            paragraph=' '.join(paragraph.split())
            if not paragraph: continue
            tokens=set(re.findall(r'\w+',paragraph.lower())); score=len(terms & tokens)
            if score: results.append((score,doc['name'],i+1,paragraph[:500]))
    results.sort(key=lambda x:-x[0]); return results[:8]

def assistant_answer(question, df, docs):
    # A transparent retrieval coordinator, not a generative model.
    lines=['Local evidence coordinator (keyword retrieval; not an LLM).']
    if df is not None and not df.empty:
        m=metrics(df); lines.append(f"Campaign evidence: {m['campaigns']} campaigns; {m['sent']:,} sent; " + (f"conversion rate {m['conversion_rate']:.2f}%" if m['conversion_rate'] is not None else 'conversion rate unavailable') + '.')
        tokens=set(re.findall(r'\w+',question.lower()))
        matches=[str(n) for n in df['campaign'].unique() if tokens & set(re.findall(r'\w+',str(n).lower()))]
        if matches: lines.append('Matching campaign names: '+', '.join(matches[:10])+'.')
        for x in anomalies(df)[:3]: lines.append('Review: '+x)
        if 'market' in question.lower():
            for _,r in grouped(df,'market').iterrows(): lines.append(f"Market {r['market']}: {r['campaigns']} campaigns, {r['conversions']} conversions / {r['delivered']} delivered.")
    for _,name,n,passage in find_passages(docs, question): lines.append(f'[{name}, passage {n}] {passage}')
    if len(lines)==1: lines.append('No campaign data or matching document passages. Load data or try different keywords.')
    lines.append('These observations do not establish causes. Review source data and approve actions manually.')
    return '\n'.join(lines)

def workbook(df, findings):
    out=io.BytesIO()
    with pd.ExcelWriter(out,engine='openpyxl') as writer:
        df.to_excel(writer,sheet_name='Campaign Data',index=False)
        grouped(df,'market').to_excel(writer,sheet_name='Market Summary',index=False)
        grouped(df,'type').to_excel(writer,sheet_name='Type Summary',index=False)
        byyear=df.copy(); byyear['year']=byyear.date.dt.year
        grouped(byyear,'year').to_excel(writer,sheet_name='Year Summary',index=False)
        pd.DataFrame([metrics(df)]).to_excel(writer,sheet_name='KPI Summary',index=False)
        pd.DataFrame({'finding':findings or ['No issues flagged by current rules.']}).to_excel(writer,sheet_name='Insights',index=False)
        # Prevent spreadsheet formula injection from user supplied text.
        for ws in writer.book.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    if isinstance(cell.value,str) and cell.value.lstrip().startswith(('=','+','-','@')): cell.value="'"+cell.value
    return out.getvalue()

def filter_dates(df, start='', end=''):
    """Inclusive calendar dates. Empty boundaries are open-ended."""
    from datetime import date
    def parse(value):
        if not value: return None
        try:
            d=date.fromisoformat(value)
            if d.isoformat()!=value: raise ValueError()
            return pd.Timestamp(d)
        except ValueError: raise ValueError('Dates must use YYYY-MM-DD.')
    a,b=parse(start),parse(end)
    if a is not None and b is not None and a>b: raise ValueError('Start date must not be after end date.')
    mask=pd.Series(True,index=df.index)
    if a is not None: mask &= df.date >= a
    if b is not None: mask &= df.date < b + pd.Timedelta(days=1)
    return df.loc[mask].copy()

def year_comparison(df,start,end,min_delivered=100):
    """Compare inclusive range to its same calendar dates one year earlier.
    A Feb 29 endpoint is clipped to Feb 28 in a non-leap comparison year.
    """
    if not start or not end: raise ValueError('Both start and end dates are required for year comparison.')
    current=filter_dates(df,start,end)
    from datetime import date
    def previous(s):
        d=date.fromisoformat(s)
        try: return d.replace(year=d.year-1).isoformat()
        except ValueError: return d.replace(year=d.year-1,day=28).isoformat()
    ps,pe=previous(start),previous(end); prior=filter_dates(df,ps,pe)
    if current.empty or prior.empty: return f'Current {start}–{end}: {len(current)} rows; prior {ps}–{pe}: {len(prior)} rows. Both periods need data to compare.'
    a,b=metrics(current),metrics(prior)
    result=[f'Current {start}–{end}: {a["campaigns"]} campaigns, {a["delivered"]:,} delivered. Prior {ps}–{pe}: {b["campaigns"]} campaigns, {b["delivered"]:,} delivered.']
    for k,label in [('open_rate','Open rate'),('ctr','CTR'),('ctor','CTOR'),('conversion_rate','Conversion rate'),('bounce_rate','Bounce rate')]:
        x,y=a[k],b[k]
        if x is None or y is None: result.append(f'{label}: N/A (zero denominator).')
        else: result.append(f'{label}: {x:.2f}% vs {y:.2f}%; {x-y:+.2f} percentage points.')
    if min(a['delivered'],b['delivered']) < min_delivered: result.append(f'Caution: a period has fewer than {min_delivered} delivered; interpret rates cautiously.')
    result.append('Different campaign mixes, uneven coverage or repeat event counts may affect comparisons; no causal inference. Feb 29 boundaries clip to Feb 28 in non-leap years.')
    return '\n'.join(result)

def quality_findings(df,bounce_threshold=5.0,min_delivered=100):
    if not 0 <= bounce_threshold <= 100: raise ValueError('Bounce threshold must be between 0 and 100.')
    if min_delivered < 0: raise ValueError('Minimum delivered must be non-negative.')
    findings=[]
    duplicates=int(df.duplicated(subset=['campaign','date','market','type'],keep=False).sum())
    if duplicates: findings.append(f'{duplicates} rows share campaign, date, market and type; check whether duplicates or legitimate splits.')
    for _,r in df.iterrows():
        issues=[]
        if r.delivered>r.sent: issues.append('delivered exceeds sent')
        if r.delivered+r.bounces>r.sent: issues.append('delivered plus bounces exceeds sent')
        if r.opens>r.delivered: issues.append('opens exceed delivered; may be repeat events')
        if r.clicks>r.opens: issues.append('clicks exceed opens; may be repeat events or tracking differences')
        if r.conversions>r.clicks: issues.append('conversions exceed clicks; check attribution')
        if r.sent and r.bounces/r.sent*100 > bounce_threshold: issues.append(f'bounce rate exceeds {bounce_threshold:g}% threshold')
        if r.delivered < min_delivered: issues.append(f'delivered is below {min_delivered}; rates may be unstable')
        if issues: findings.append(f'{r.campaign}: ' + '; '.join(issues))
    return findings
