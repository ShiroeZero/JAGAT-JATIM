import re

# JAGAT — canonical location/entity resolver
POLRES_MAP = {'POLRES PELABUHAN TANJUNG PERAK': ['polres pelabuhan tanjung perak', 'polres tanjung perak', 'kepolisian resor pelabuhan tanjung perak'], 'POLRES JEMBER': ['polres jember', 'kepolisian resor jember'], 'POLRES KEDIRI': ['polres kediri', 'kepolisian resor kediri'], 'POLRES BLITAR KOTA': ['polres blitar kota', 'polresta blitar', 'kepolisian resor blitar kota', 'kepolisian resor kota blitar'], 'POLRESTABES SURABAYA': ['polrestabes surabaya', 'polres kota besar surabaya', 'kepolisian resor kota besar surabaya'], 'POLRESTA MALANG KOTA': ['polresta malang kota', 'polresta malang', 'polres malang kota', 'kepolisian resor kota malang', 'kepolisian resor malang kota'], 'POLRESTA SIDOARJO': ['polresta sidoarjo', 'polres sidoarjo', 'kepolisian resor kota sidoarjo', 'kepolisian resor sidoarjo'], 'POLRESTA BANYUWANGI': ['polresta banyuwangi', 'polres banyuwangi', 'kepolisian resor kota banyuwangi', 'kepolisian resor banyuwangi'], 'POLRESTA TUBAN': ['polresta tuban', 'polres tuban', 'kepolisian resor tuban', 'kepolisian resor kota tuban'], 'POLRESTA SUMENEP': ['polresta sumenep', 'polres sumenep', 'kepolisian resor sumenep'], 'POLRES GRESIK': ['polres gresik', 'kepolisian resor gresik'], 'POLRES MALANG': ['polres malang', 'kepolisian resor malang'], 'POLRES PASURUAN': ['polres pasuruan', 'kepolisian resor pasuruan'], 'POLRES PASURUAN KOTA': ['polres pasuruan kota', 'polresta pasuruan', 'kepolisian resor kota pasuruan'], 'POLRES PROBOLINGGO': ['polres probolinggo', 'kepolisian resor probolinggo'], 'POLRES PROBOLINGGO KOTA': ['polres probolinggo kota', 'polresta probolinggo', 'kepolisian resor kota probolinggo'], 'POLRES LUMAJANG': ['polres lumajang', 'kepolisian resor lumajang'], 'POLRES BATU': ['polres batu', 'polresta batu', 'kepolisian resor batu'], 'POLRES BONDOWOSO': ['polres bondowoso', 'kepolisian resor bondowoso'], 'POLRES SITUBONDO': ['polres situbondo', 'kepolisian resor situbondo'], 'POLRES KEDIRI KOTA': ['polres kediri kota', 'polresta kediri', 'kepolisian resor kediri kota'], 'POLRES TULUNGAGUNG': ['polres tulungagung', 'kepolisian resor tulungagung'], 'POLRES NGANJUK': ['polres nganjuk', 'kepolisian resor nganjuk'], 'POLRES TRENGGALEK': ['polres trenggalek', 'kepolisian resor trenggalek'], 'POLRES BLITAR': ['polres blitar', 'kepolisian resor blitar'], 'POLRES MADIUN': ['polres madiun', 'kepolisian resor madiun'], 'POLRES MADIUN KOTA': ['polres madiun kota', 'polresta madiun', 'kepolisian resor kota madiun', 'kepolisian resor madiun kota'], 'POLRES NGAWI': ['polres ngawi', 'kepolisian resor ngawi'], 'POLRES MAGETAN': ['polres magetan', 'kepolisian resor magetan'], 'POLRES PONOROGO': ['polres ponorogo', 'kepolisian resor ponorogo'], 'POLRES PACITAN': ['polres pacitan', 'kepolisian resor pacitan'], 'POLRES BOJONEGORO': ['polres bojonegoro', 'kepolisian resor bojonegoro'], 'POLRES LAMONGAN': ['polres lamongan', 'kepolisian resor lamongan'], 'POLRES MOJOKERTO': ['polres mojokerto', 'kepolisian resor mojokerto'], 'POLRES MOJOKERTO KOTA': ['polres mojokerto kota', 'polresta mojokerto', 'kepolisian resor kota mojokerto'], 'POLRES JOMBANG': ['polres jombang', 'kepolisian resor jombang'], 'POLRES PAMEKASAN': ['polres pamekasan', 'kepolisian resor pamekasan'], 'POLRES BANGKALAN': ['polres bangkalan', 'kepolisian resor bangkalan'], 'POLRES SAMPANG': ['polres sampang', 'kepolisian resor sampang']}

POLSEK_BINDINGS = {'POLSEK BANDARKEDUNGMULYO': 'POLRES JOMBANG', 'POLSEK BARENG': 'POLRES JOMBANG', 'POLSEK KABUH': 'POLRES JOMBANG', 'POLSEK KUDU': 'POLRES JOMBANG', 'POLSEK MEGALUH': 'POLRES JOMBANG', 'POLSEK MOJOAGUNG': 'POLRES JOMBANG', 'POLSEK MOJOWARNO': 'POLRES JOMBANG', 'POLSEK NGUSIKAN': 'POLRES JOMBANG', 'POLSEK PERAK': 'POLRES JOMBANG', 'POLSEK PLANDAAN': 'POLRES JOMBANG', 'POLSEK PLOSO': 'POLRES JOMBANG', 'POLSEK TEMBELANG': 'POLRES JOMBANG', 'POLSEK KESAMBEN': 'POLRES JOMBANG', 'POLSEK NGORO': 'POLRES JOMBANG', 'POLSEK GUDO': 'POLRES JOMBANG', 'POLSEK SUMOBITO': 'POLRES JOMBANG', 'POLSEK JOMBANG': 'POLRES JOMBANG', 'POLSEK PETERONGAN': 'POLRES JOMBANG', 'POLSEK WONOSALAM': 'POLRES JOMBANG', 'POLSEK JOGOROTO': 'POLRES JOMBANG', 'POLSEK DIWEK': 'POLRES JOMBANG'}

JATIM_LOCATIONS = ['surabaya', 'sidoarjo', 'gresik', 'lamongan', 'tuban', 'bojonegoro', 'ngawi', 'magetan', 'madiun', 'ponorogo', 'pacitan', 'nganjuk', 'kediri', 'tulungagung', 'trenggalek', 'blitar', 'malang', 'batu', 'pasuruan', 'probolinggo', 'lumajang', 'jember', 'bondowoso', 'situbondo', 'banyuwangi', 'mojokerto', 'jombang', 'pamekasan', 'bangkalan', 'sampang', 'sumenep', 'madura']

NON_JATIM_TERMS = ['batu bara', 'polres batu bara', 'kepolisian resor batu bara', 'sumatera utara', 'sumatera barat', 'sumatera selatan', 'lampung', 'jambi', 'riau', 'kepulauan riau', 'bengkulu', 'kalimantan', 'sulawesi', 'papua', 'maluku', 'bali', 'ntb', 'ntt', 'jawa tengah', 'jateng', 'jawa barat', 'jabar', 'banten', 'dki jakarta', 'jakarta', 'yogyakarta', 'sulawesi selatan', 'sulsel', 'polda sulsel', 'polda sumsel']

POLRES_TO_LOCALITY = {'POLRES PELABUHAN TANJUNG PERAK': 'Surabaya', 'POLRES JEMBER': 'Jember', 'POLRES KEDIRI': 'Kediri', 'POLRES BLITAR KOTA': 'Blitar', 'POLRESTABES SURABAYA': 'Surabaya', 'POLRESTA MALANG KOTA': 'Malang', 'POLRESTA SIDOARJO': 'Sidoarjo', 'POLRESTA BANYUWANGI': 'Banyuwangi', 'POLRESTA TUBAN': 'Tuban', 'POLRESTA SUMENEP': 'Sumenep', 'POLRES GRESIK': 'Gresik', 'POLRES MALANG': 'Malang', 'POLRES PASURUAN': 'Pasuruan', 'POLRES PASURUAN KOTA': 'Pasuruan', 'POLRES PROBOLINGGO': 'Probolinggo', 'POLRES PROBOLINGGO KOTA': 'Probolinggo', 'POLRES LUMAJANG': 'Lumajang', 'POLRES BATU': 'Batu', 'POLRES BONDOWOSO': 'Bondowoso', 'POLRES SITUBONDO': 'Situbondo', 'POLRES KEDIRI KOTA': 'Kediri', 'POLRES TULUNGAGUNG': 'Tulungagung', 'POLRES NGANJUK': 'Nganjuk', 'POLRES TRENGGALEK': 'Trenggalek', 'POLRES BLITAR': 'Blitar', 'POLRES MADIUN': 'Madiun', 'POLRES MADIUN KOTA': 'Madiun', 'POLRES NGAWI': 'Ngawi', 'POLRES MAGETAN': 'Magetan', 'POLRES PONOROGO': 'Ponorogo', 'POLRES PACITAN': 'Pacitan', 'POLRES BOJONEGORO': 'Bojonegoro', 'POLRES LAMONGAN': 'Lamongan', 'POLRES MOJOKERTO': 'Mojokerto', 'POLRES MOJOKERTO KOTA': 'Mojokerto', 'POLRES JOMBANG': 'Jombang', 'POLRES PAMEKASAN': 'Pamekasan', 'POLRES BANGKALAN': 'Bangkalan', 'POLRES SAMPANG': 'Sampang'}

# Central Jatim police units. These belong to the JAWA TIMUR area but are
# not Polres and therefore use a locality-like area label: "Polda Jatim".
JATIM_PUSAT_TERMS = [
    'polda jawa timur', 'polda jatim', 'kapolda jawa timur', 'kapolda jatim',
    'satbrimob polda jatim', 'satbrimob polda jawa timur',
    'propam polda jatim', 'bidpropam polda jatim',
    'ditreskrimum polda jatim', 'ditreskrimsus polda jatim',
    'ditresnarkoba polda jatim', 'ditres siber polda jatim', 'ditressiber polda jatim',
    'ditres ppa polda jatim', 'ditres ppa', 'ditreskrimsus', 'ditreskrimum',
    'ditresnarkoba', 'ditres siber', 'ditressiber', 'satbrimob', 'bidpropam',
]

def normalize(text):
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()

def contains_word(text, term):
    text, term = normalize(text), normalize(term)
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None

def strip_publisher_suffix(title, source=""):
    title=str(title or "").strip(); source=str(source or "").strip()
    if source:
        title=re.sub(r"\s+(?:-|–|—|\|)\s*"+re.escape(source)+r"\s*$","",title,flags=re.I)
    return title.strip()

def detect_polsek(title):
    t=normalize(title)
    for alias,parent in sorted(POLSEK_BINDINGS.items(),key=lambda x:len(x[0]),reverse=True):
        if contains_word(t,alias): return alias,parent,"master_polsek_binding"
    m=re.search(r"\bpolsek\s+([a-z0-9-]+(?:\s+[a-z0-9-]+){0,2})\b",t,re.I)
    if m: return "POLSEK "+" ".join(m.group(1).split()).upper(),None,"title_polsek_unbound"
    return None,None,None

def detect_polres(title):
    t=normalize(title)
    if contains_word(t,"batu bara") or contains_word(t,"polres batu bara"): return None,None
    found=[]
    for canonical,aliases in POLRES_MAP.items():
        for alias in aliases:
            if contains_word(t,alias): found.append((len(alias),canonical,alias))
    if not found: return None,None
    found.sort(key=lambda x:(-x[0],x[1])); return found[0][1],found[0][2]

def locality_from_polres(polres): return POLRES_TO_LOCALITY.get(str(polres or ""),"")

def detect_locality(title):
    t=normalize(title)
    if contains_word(t,"batu bara"): return ""
    found=[x for x in JATIM_LOCATIONS if contains_word(t,x)]
    found.sort(key=len,reverse=True)
    return found[0].title() if found else ""

def detect_polda_unit(title):
    t=normalize(title)
    return any(contains_word(t, term) for term in JATIM_PUSAT_TERMS)

def detect_location(title, description="", source=""):
    t=normalize(strip_publisher_suffix(title,source))
    outside=[x for x in NON_JATIM_TERMS if contains_word(t,x)]
    if outside:
        return {"is_jatim":False,"region":"LUAR JATIM","locality":"","area_label":"LUAR JATIM","polres":None,"polsek":None,"confidence":100,"evidence":outside[:6],"source":"title","location_status":"LUAR_JATIM"}

    # Polda/central Jatim units are an explicit JAWA TIMUR area entry,
    # alongside the 39 Polres, but are not forced into any Polres.
    if detect_polda_unit(t):
        return {"is_jatim":True,"region":"Jawa Timur","locality":"Polda Jatim","area_label":"Polda Jatim","polres":None,"polsek":None,"confidence":100,"evidence":[x for x in JATIM_PUSAT_TERMS if contains_word(t,x)][:6],"source":"master_jatim_unit","location_status":"JAWA_TIMUR"}

    polres,pev=detect_polres(t); polsek,pp,ps=detect_polsek(t)
    if not polres and pp: polres,pev=pp,polsek
    locality=locality_from_polres(polres) if polres else detect_locality(t)
    explicit=any(contains_word(t,x) for x in ["jawa timur","jatim"])
    if polres or pp or locality or explicit:
        ev=[x for x in [pev,polsek,locality,"Jawa Timur/Jatim" if explicit else None] if x]
        return {"is_jatim":True,"region":"Jawa Timur","locality":locality,"area_label":locality or "Jawa Timur (Umum)","polres":polres,"polsek":polsek,"confidence":100 if polres else 96 if pp else 95 if locality else 90,"evidence":list(dict.fromkeys(ev))[:6],"source":"master_entity" if pp else "title","location_status":"JAWA_TIMUR"}
    return {"is_jatim":None,"region":"BELUM TERPETAKAN","locality":"","area_label":"BELUM TERPETAKAN","polres":None,"polsek":polsek,"confidence":0,"evidence":[polsek] if polsek else [],"source":"title","location_status":"BELUM_TERPETAKAN"}
