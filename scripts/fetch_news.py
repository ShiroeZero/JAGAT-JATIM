import csv, datetime as dt, hashlib, html, json, os, re, time
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

OUT="data/news.json"
USER_AGENT="PNM-Polri-Negative-News-Monitor/1.0"
QUERIES=[
    '"oknum polisi" Indonesia','"anggota polisi" ditangkap','"anggota Polri" tersangka',
    'polisi terlibat kasus','polisi diduga melakukan','polisi ditahan','polisi ditangkap',
    'polisi narkoba','polisi korupsi','polisi pungli','polisi pemerasan','polisi penganiayaan',
    'polisi penembakan','polisi kekerasan','polisi pelanggaran etik','polisi disiplin',
    'polisi suap','polisi penyalahgunaan wewenang','polisi viral Indonesia',
    # Jawa Timur
    '"oknum polisi" "Jawa Timur"','"anggota polisi" "Jawa Timur"','polisi Surabaya ditangkap',
    'polisi Sidoarjo ditangkap','polisi Malang ditangkap','polisi Jember ditangkap',
    'polisi Banyuwangi ditangkap','polisi Kediri ditangkap','polisi Pasuruan ditangkap',
    'polisi Probolinggo ditangkap','polisi Situbondo ditangkap','polisi Mojokerto ditangkap',
    'polisi Gresik ditangkap','polisi Lamongan ditangkap','polisi Madiun ditangkap',
    'polisi Tuban ditangkap','polisi Bojonegoro ditangkap','polisi Bangkalan ditangkap',
    'polisi Pamekasan ditangkap','polisi Sampang ditangkap','polisi Sumenep ditangkap',
    'polisi Blitar ditangkap','polisi Tulungagung ditangkap','polisi Trenggalek ditangkap',
]
JATIM=["surabaya","sidoarjo","gresik","lamongan","tuban","bojonegoro","ngawi","magetan","madiun",
"ponorogo","pacitan","nganjuk","kediri","tulungagung","blitar","trenggalek","malang","batu",
"pasuruan","probolinggo","lumajang","jember","bondowoso","situbondo","banyuwangi","mojokerto",
"jombang","sampang","pamekasan","sumenep","bangkalan","madura","jawa timur","jatim","polda jatim"]
CATS={
"Pidana/Narkoba":["narkoba","sabu","ganja","ekstasi","narkotika","obat terlarang"],
"Pidana/Kekerasan":["penganiayaan","kekerasan","penembakan","menembak","pemukulan","pengeroyokan"],
"Pidana/Korupsi":["korupsi","suap","gratifikasi","pungli","pemerasan","pungutan liar"],
"Etik/Disiplin":["etik","kode etik","disiplin","pelanggaran disiplin","propam","pelanggaran anggota"],
"Penyalahgunaan Wewenang":["salah gunakan","penyalahgunaan wewenang","wewenang","peras","pemerasan"],
"Kasus Hukum Lainnya":["tersangka","ditangkap","ditahan","diperiksa","kasus","dugaan"]
}
HIGH=["tersangka","ditangkap","ditahan","narkoba","sabu","penembakan","penganiayaan","korupsi","suap","pungli","pemerasan","tewas","meninggal"]
MED=["diperiksa","diselidiki","pelanggaran","etik","disiplin","diduga","viral","diamankan"]

def parse_date(s):
    try:return parsedate_to_datetime(s).astimezone(dt.timezone.utc).isoformat()
    except:return dt.datetime.now(dt.timezone.utc).isoformat()

def clean(s):
    return re.sub(r"\s+"," ",html.unescape(s or "")).strip()

def get(url):
    req=Request(url,headers={"User-Agent":USER_AGENT})
    with urlopen(req,timeout=20) as r:return r.read()

def classify(title,desc):
    t=(title+" "+desc).lower()
    is_jatim=any(x in t for x in JATIM)
    cat="Lainnya"
    for c,words in CATS.items():
        if any(w in t for w in words):cat=c;break
    score=sum(2 for w in HIGH if w in t)+sum(1 for w in MED if w in t)
    priority="high" if score>=4 else "medium" if score>=2 else "low"
    return is_jatim,cat,priority

def main():
    old={"items":[]}
    if os.path.exists(OUT):
        try:
            with open(OUT,encoding="utf-8") as f:old=json.load(f)
        except:pass
    items=old.get("items",[])
    seen={x.get("id") or x.get("url") for x in items}
    collected=dt.datetime.now(dt.timezone.utc).isoformat()
    added=0
    for q in QUERIES:
        try:
            url="https://news.google.com/rss/search?q="+quote(q)+"&hl=id&gl=ID&ceid=ID:id"
            root=ET.fromstring(get(url))
            for it in root.findall("./channel/item"):
                title=clean(it.findtext("title"))
                link=clean(it.findtext("link"))
                desc=clean(it.findtext("description"))
                pub=parse_date(it.findtext("pubDate"))
                source=clean(it.findtext("source")) or "Google News"
                if not title or not link:continue
                ident=hashlib.sha1((title+"|"+link).encode()).hexdigest()
                if ident in seen:continue
                # Keep articles that have a police-related signal.
                blob=(title+" "+desc).lower()
                if not any(k in blob for k in ["polisi","polri","oknum"]):continue
                jatim,cat,priority=classify(title,desc)
                items.append({"id":ident,"title":title,"url":link,"source":source,
                              "published_at":pub,"collected_at":collected,"region":"Jawa Timur" if jatim else "Indonesia",
                              "is_jatim":jatim,"category":cat,"priority":priority,"summary":re.sub("<.*?>","",desc)[:500]})
                seen.add(ident);added+=1
        except Exception as e:
            print("WARN",q,e)
        time.sleep(.15)
    # Keep 500 latest records.
    items.sort(key=lambda x:x.get("published_at",""),reverse=True)
    items=items[:500]
    with open(OUT,"w",encoding="utf-8") as f:json.dump({"generated_at":collected,"items":items},f,ensure_ascii=False,indent=2)
    print(f"Added {added}; total {len(items)}")

if __name__=="__main__":main()
