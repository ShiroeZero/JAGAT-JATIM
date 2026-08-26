import json, re, time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

OUT='data/news.json'
QUERIES=[
    '"oknum polisi"', '"anggota polisi" pelanggaran', '"anggota Polri" kasus',
    'polisi ditangkap', 'polisi tersangka', 'polisi ditetapkan tersangka',
    'polisi narkoba', 'polisi pungli', 'polisi korupsi', 'polisi kekerasan',
    'polisi penembakan', 'polisi penganiayaan', 'polisi pemerasan',
    'polisi pelanggaran etik', 'polisi disersi', 'polisi perkelahian'
]
JATIM_TERMS=['jawa timur','jatim','surabaya','sidoarjo','gresik','malang','batu','pasuruan','probolinggo','situbondo','bondowoso','jember','banyuwangi','kediri','blitar','tulungagung','madiun','mojokerto','jombang','nganjuk','magetan','ponorogo','pacitan','trenggalek','ngawi','bojonegoro','tuban','lamongan','bangkalan','sampang','pamekasan','sumenep','sumenep']
HIGH=['ditangkap','tersangka','tewas','menembak','penembakan','narkoba','korupsi','pemerasan','pungli','penganiayaan','pemerkosaan','pembunuhan','sabu','ganja','senjata','suap']
MED=['pelanggaran etik','disersi','disiplin','viral','diamankan','diperiksa','dilaporkan','dugaan','kasus']
CATS={'narkoba':['narkoba','sabu','ganja','obat terlarang'],'kekerasan':['penganiayaan','penembakan','pemukulan','kekerasan','tewas','pembunuhan','pemerkosaan'],'korupsi':['korupsi','pungli','pemerasan','suap','gratifikasi'],'etik':['etik','disiplin','disersi','pelanggaran'],'pidana':['tersangka','ditangkap','kriminal','pidana']}

def clean(s): return re.sub(r'\\s+',' ',s or '').strip()
def parse_date(s):
    try:return parsedate_to_datetime(s).astimezone(timezone.utc).isoformat()
    except:return datetime.now(timezone.utc).isoformat()
def classify(title,desc):
    t=(title+' '+desc).lower()
    sev='high' if any(x in t for x in HIGH) else ('medium' if any(x in t for x in MED) else 'low')
    cat='lainnya'
    for k,terms in CATS.items():
        if any(x in t for x in terms): cat=k; break
    jatim=any(x in t for x in JATIM_TERMS)
    return sev,cat,jatim

def fetch(q):
    url='https://news.google.com/rss/search?q='+quote_plus(q)+'&hl=id&gl=ID&ceid=ID:id'
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 PNM-monitor/1.0'})
    with urlopen(req,timeout=20) as r: root=ET.fromstring(r.read())
    out=[]
    for item in root.findall('./channel/item'):
        title=clean(item.findtext('title'))
        link=clean(item.findtext('link'))
        desc=clean(re.sub('<[^>]+>',' ',item.findtext('description') or ''))
        pub=parse_date(item.findtext('pubDate'))
        source=item.findtext('source') or 'Google News'
        sev,cat,jatim=classify(title,desc)
        if not (('polisi' in (title+' '+desc).lower()) or ('polri' in (title+' '+desc).lower())): continue
        out.append({'id':link or title,'title':title,'summary':desc[:280],'link':link,'published_at':pub,'source':clean(source),'severity':sev,'category':cat,'jatim':jatim,'region':'Jawa Timur' if jatim else 'Indonesia'})
    return out

items=[]
for q in QUERIES:
    try: items.extend(fetch(q)); time.sleep(.2)
    except Exception as e: print('WARN',q,e)
# Deduplicate by URL/title
seen=set(); unique=[]
for x in items:
    key=x['link'] or x['title']
    if key in seen: continue
    seen.add(key); unique.append(x)
unique.sort(key=lambda x:x['published_at'],reverse=True)
# Keep a rolling dataset of recent items (30 days) to keep Pages lightweight.
now=time.time(); cutoff=now-30*86400
recent=[x for x in unique if _ts(x['published_at'])>=cutoff]
with open(OUT,'w',encoding='utf-8') as f: json.dump({'generated_at':datetime.now(timezone.utc).isoformat(),'items':recent[:2000]},f,ensure_ascii=False,indent=2)
print('Saved',len(recent),'items')
