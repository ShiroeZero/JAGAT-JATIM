import datetime as dt, hashlib, html, json, os, re, time
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from urllib.request import Request,urlopen
import xml.etree.ElementTree as ET

OUT="data/news.json"; USER_AGENT="PNM-Polri-Negative-News-Monitor/3.0"

QUERIES=[
'"oknum polisi" Indonesia','"anggota polisi" ditangkap','"anggota Polri" tersangka',
'polisi terlibat kasus','polisi diduga melakukan','polisi ditahan','polisi ditangkap',
'polisi narkoba','polisi korupsi','polisi pungli','polisi pemerasan','polisi penganiayaan',
'polisi penembakan','polisi kekerasan','polisi pelanggaran etik','polisi disiplin',
'polisi suap','polisi penyalahgunaan wewenang','polisi viral Indonesia',
'polisi ungkap kasus','polisi tangkap pelaku','polisi amankan tersangka',
'polisi Jawa Timur','oknum polisi Jawa Timur'
]

POLRES={
"POLRES PELABUHAN TANJUNG PERAK":["polres pelabuhan tanjung perak","pelabuhan tanjung perak"],
"POLRES JEMBER":["polres jember","jember"],"POLRES KEDIRI":["polres kediri"],
"POLRES BLITAR KOTA":["polres blitar kota","blitar kota"],"POLRESTABES SURABAYA":["polrestabes surabaya","surabaya"],
"POLRESTA MALANG KOTA":["polresta malang kota","polres malang kota","malang kota"],
"POLRESTA SIDOARJO":["polresta sidoarjo","polres sidoarjo","sidoarjo"],
"POLRESTA BANYUWANGI":["polresta banyuwangi","polres banyuwangi","banyuwangi"],
"POLRESTA TUBAN":["polresta tuban","polres tuban","tuban"],
"POLRESTA SUMENEP":["polresta sumenep","polres sumenep","sumenep"],
"POLRES GRESIK":["polres gresik","gresik"],"POLRES MALANG":["polres malang"],
"POLRES PASURUAN":["polres pasuruan"],"POLRES PASURUAN KOTA":["polres pasuruan kota","pasuruan kota"],
"POLRES PROBOLINGGO":["polres probolinggo","kabupaten probolinggo"],
"POLRES PROBOLINGGO KOTA":["polres probolinggo kota","probolinggo kota"],
"POLRES LUMAJANG":["polres lumajang","lumajang"],"POLRES BATU":["polres batu","kota batu"],
"POLRES BONDOWOSO":["polres bondowoso","bondowoso"],"POLRES SITUBONDO":["polres situbondo","situbondo"],
"POLRES KEDIRI KOTA":["polres kediri kota","kediri kota"],"POLRES TULUNGAGUNG":["polres tulungagung","tulungagung"],
"POLRES NGANJUK":["polres nganjuk","nganjuk"],"POLRES TRENGGALEK":["polres trenggalek","trenggalek"],
"POLRES BLITAR":["polres blitar"],"POLRES MADIUN":["polres madiun"],"POLRES MADIUN KOTA":["polres madiun kota","madiun kota"],
"POLRES NGAWI":["polres ngawi","ngawi"],"POLRES MAGETAN":["polres magetan","magetan"],
"POLRES PONOROGO":["polres ponorogo","ponorogo"],"POLRES PACITAN":["polres pacitan","pacitan"],
"POLRES BOJONEGORO":["polres bojonegoro","bojonegoro"],"POLRES LAMONGAN":["polres lamongan","lamongan"],
"POLRES MOJOKERTO":["polres mojokerto"],"POLRES MOJOKERTO KOTA":["polres mojokerto kota","mojokerto kota"],
"POLRES JOMBANG":["polres jombang","jombang"],"POLRES PAMEKASAN":["polres pamekasan","pamekasan"],
"POLRES BANGKALAN":["polres bangkalan","bangkalan"],"POLRES SAMPANG":["polres sampang","sampang"]
}
JATIM=["jawa timur","jatim","polda jatim","polda jawa timur"]
NON_JATIM=["riau","pekanbaru","dumai","bengkalis","siak","kampar","pelalawan","indragiri",
"kuantan singingi","rokan hilir","rokan hulu","meranti","kepulauan riau","batam","tanjungpinang",
"jambi","sumatera barat","sumatera utara","sumatera selatan","lampung","bengkulu","kalimantan",
"sulawesi","papua","maluku","bali","ntb","ntt","jawa tengah","jateng","jawa barat","jabar",
"banten","dki jakarta","jakarta"]

# Negative subject signals: police/member is the subject of wrongdoing.
NEGATIVE=[
"oknum polisi","oknum polri","anggota polisi ditangkap","anggota polri ditangkap",
"anggota polisi tersangka","anggota polri tersangka","polisi ditetapkan sebagai tersangka",
"polisi menjadi tersangka","polisi terlibat","polisi diduga","polisi ditahan",
"polisi diperiksa","polisi dipecat","polisi diberhentikan","polisi melakukan penganiayaan",
"polisi melakukan kekerasan","polisi menembak","polisi terlibat narkoba","polisi konsumsi narkoba",
"polisi positif narkoba","polisi korupsi","polisi menerima suap","polisi menerima uang",
"polisi pungli","polisi memeras","polisi melakukan pemerasan","polisi menyalahgunakan wewenang",
"pelanggaran etik polisi","pelanggaran disiplin polisi","anggota polisi melakukan"
]
ETHIC=["kode etik","etik","disiplin","propam","pelanggaran disiplin","pelanggaran etik","dipecat","ptdh","pemberhentian"]
CRIME=["narkoba","sabu","ganja","ekstasi","narkotika","korupsi","suap","gratifikasi","pungli","pemerasan",
"penganiayaan","kekerasan","penembakan","menembak","pemukulan","pengeroyokan"]
PERF=["prestasi","penghargaan","berhasil","apresiasi","pelayanan","bakti sosial","pengamanan","patroli","imbauan","sosialisasi"]
CASE=["ungkap kasus","mengungkap","ungkap","tangkap pelaku","amankan tersangka","mengamankan tersangka",
"berhasil menangkap","berhasil mengamankan","pengungkapan kasus","gelar perkara","sita","menyita","gagalkan",
"menggagalkan","razia","operasi","penindakan"]
CATEGORIES={
"OKNUM - PIDANA":["oknum polisi","anggota polisi ditangkap","anggota polri ditangkap","polisi menjadi tersangka","polisi ditetapkan sebagai tersangka","polisi terlibat narkoba","polisi korupsi","polisi memeras","polisi melakukan penganiayaan","polisi melakukan kekerasan"],
"OKNUM - ETIK/DISIPLIN":ETHIC,
"OKNUM - PENYALAHGUNAAN WEWENANG":["penyalahgunaan wewenang","salahgunakan wewenang","polisi memeras","polisi pungli","polisi menerima suap"],
"KINERJA/LAYANAN POLRI":["pelayanan buruk","keluhan polisi","protes terhadap polisi","polisi dilaporkan","polisi diduga lalai","kelalaian polisi","kritik polisi"],
"UNGKAP KASUS / PENINDAKAN":["ungkap kasus","mengungkap","tangkap pelaku","amankan tersangka","pengungkapan kasus","gagalkan","menggagalkan","sita","operasi"],
"PRESTASI / KEGIATAN POSITIF":PERF,
"NETRAL / LAINNYA":[]
}

def parse_date(s):
    try:return parsedate_to_datetime(s).astimezone(dt.timezone.utc).isoformat()
    except:return dt.datetime.now(dt.timezone.utc).isoformat()
def clean(s):return re.sub(r"\s+"," ",html.unescape(s or "")).strip()
def get(url):
    req=Request(url,headers={"User-Agent":USER_AGENT})
    with urlopen(req,timeout=20) as r:return r.read()

def classify(title,desc):
    # IMPORTANT: source/media name is deliberately excluded from this text.
    text=(title+" "+re.sub(r"<[^>]+>"," ",desc)).lower()
    polres=None
    for name,aliases in POLRES.items():
        if any(re.search(r"(?<![a-z])"+re.escape(a)+r"(?![a-z])",text) for a in aliases):
            polres=name; break
    non=sum(1 for x in NON_JATIM if re.search(r"(?<![a-z])"+re.escape(x)+r"(?![a-z])",text))
    jat=sum(1 for x in JATIM if re.search(r"(?<![a-z])"+re.escape(x)+r"(?![a-z])",text))
    is_jatim=bool(polres or jat)
    if non and not polres:is_jatim=False

    # Priority first: if the police are the alleged wrongdoer, classify as negative.
    neg=any(x in text for x in NEGATIVE)
    if neg:
        if any(x in text for x in ["etik","disiplin","propam","dipecat","ptdh"]):
            category="OKNUM - ETIK/DISIPLIN"
        elif any(x in text for x in ["wewenang","pungli","memeras","suap"]):
            category="OKNUM - PENYALAHGUNAAN WEWENANG"
        else:
            category="OKNUM - PIDANA"
        scope="negative"; scope_label="NEGATIF / OKNUM"
    elif any(x in text for x in CASE):
        category="UNGKAP KASUS / PENINDAKAN"; scope="case"; scope_label="UNGKAP KASUS"
    elif any(x in text for x in PERF):
        category="PRESTASI / KEGIATAN POSITIF"; scope="positive"; scope_label="POSITIF / KEGIATAN"
    elif any(x in text for x in ["keluhan","protes","dilaporkan","lalai","kelalaian","pelayanan buruk","kritik polisi"]):
        category="KINERJA/LAYANAN POLRI"; scope="negative"; scope_label="NEGATIF / KINERJA"
    else:
        category="NETRAL / LAINNYA"; scope="neutral"; scope_label="NETRAL"

    score=sum(2 for x in NEGATIVE if x in text)+sum(1 for x in ETHIC+CRIME if x in text)
    priority="high" if neg and score>=3 else "medium" if neg or score>=2 else "low"
    return is_jatim,polres,category,scope,scope_label,priority

def main():
    old={"items":[]}
    if os.path.exists(OUT):
        try:
            with open(OUT,encoding="utf-8") as f:old=json.load(f)
        except:pass
    items=old.get("items",[]); seen={x.get("id") or x.get("url") for x in items}; collected=dt.datetime.now(dt.timezone.utc).isoformat()

    # Reclassify ALL existing records using title + description, so old Riau/Jatim mistakes get fixed.
    for n in items:
        n["is_jatim"],n["polres"],n["category"],n["scope"],n["scope_label"],n["priority"]=classify(n.get("title",""),n.get("summary",""))

    added=0
    for q in QUERIES:
        try:
            url="https://news.google.com/rss/search?q="+quote(q)+"&hl=id&gl=ID&ceid=ID:id"
            root=ET.fromstring(get(url))
            for it in root.findall("./channel/item"):
                title=clean(it.findtext("title"));link=clean(it.findtext("link"));desc=clean(it.findtext("description"))
                if not title or not link:continue
                ident=hashlib.sha1((title+"|"+link).encode()).hexdigest()
                if ident in seen:continue
                blob=(title+" "+desc).lower()
                if not any(k in blob for k in ["polisi","polri","oknum"]):continue
                pub=parse_date(it.findtext("pubDate"));source=clean(it.findtext("source")) or "Google News"
                jatim,polres,category,scope,scope_label,priority=classify(title,desc)
                items.append({"id":ident,"title":title,"url":link,"source":source,"published_at":pub,
                    "collected_at":collected,"region":"Jawa Timur" if jatim else "Indonesia","is_jatim":jatim,
                    "polres":polres,"category":category,"scope":scope,"scope_label":scope_label,
                    "priority":priority,"summary":re.sub("<.*?>","",desc)[:700]})
                seen.add(ident);added+=1
        except Exception as e:print("WARN",q,e)
        time.sleep(.15)
    items.sort(key=lambda x:x.get("published_at",""),reverse=True)
    items=items[:5000]
    with open(OUT,"w",encoding="utf-8") as f:json.dump({"generated_at":collected,"items":items},f,ensure_ascii=False,indent=2)
    print(f"Reclassified {len(items)-added}; added {added}; total {len(items)}")

if __name__=="__main__":main()
