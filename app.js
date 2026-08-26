const cfg = window.PNM_CONFIG || {};
const supabaseReady = cfg.SUPABASE_URL && !cfg.SUPABASE_URL.includes('YOUR-') && cfg.SUPABASE_PUBLISHABLE_KEY && !cfg.SUPABASE_PUBLISHABLE_KEY.includes('YOUR_');
const supabase = supabaseReady ? window.supabase.createClient(cfg.SUPABASE_URL, cfg.SUPABASE_PUBLISHABLE_KEY) : null;
let allNews = [];
const $ = (id) => document.getElementById(id);

function esc(s=''){ return s.replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c])); }
function relativeDate(iso){ const d=new Date(iso), diff=Date.now()-d.getTime(); if(!Number.isFinite(diff)) return ''; const h=Math.floor(diff/36e5); if(h<1) return 'baru saja'; if(h<24) return `${h} jam lalu`; const days=Math.floor(h/24); return `${days} hari lalu`; }
function severityLabel(s){ return s==='high'?'TINGGI':s==='medium'?'SEDANG':'RENDAH'; }
function newsCard(n){ return `<article class="news-card"><div class="card-main"><div class="meta"><span class="badge ${esc(n.severity)}">${severityLabel(n.severity)}</span><span>${esc(n.category||'lainnya')}</span><span>${esc(n.region||'Indonesia')}</span><span>${relativeDate(n.published_at)}</span></div><h3>${esc(n.title)}</h3><p>${esc(n.summary||'')}</p><div class="source">${esc(n.source||'Sumber')} · <a href="${esc(n.link)}" target="_blank" rel="noopener noreferrer">Buka berita ↗</a></div></div></article>`; }
function isJatim(n){ return n.region==='Jawa Timur' || n.jatim===true; }
function render(list, el){ el.innerHTML=list.length?list.map(newsCard).join(''):'<div class="empty">Tidak ada berita yang sesuai filter.</div>'; }
function filtered(){ const q=($('q')?.value||'').toLowerCase().trim(), r=$('region')?.value||'all', s=$('severity')?.value||'all', c=$('category')?.value||'all'; let out=allNews.filter(n=>(!q || `${n.title} ${n.summary} ${n.source} ${n.city||''}`.toLowerCase().includes(q)) && (r==='all'||(r==='jatim'&&isJatim(n))) && (s==='all'||n.severity===s) && (c==='all'||n.category===c)); const sort=$('sort')?.value||'new'; if(sort==='old') out.sort((a,b)=>new Date(a.published_at)-new Date(b.published_at)); else if(sort==='severity'){const rank={high:0,medium:1,low:2};out.sort((a,b)=>(rank[a.severity]??9)-(rank[b.severity]??9)||new Date(b.published_at)-new Date(a.published_at));} else out.sort((a,b)=>new Date(b.published_at)-new Date(a.published_at)); return out; }
function updateLists(){ const f=filtered(); $('resultCount').textContent=`${f.length} berita`; render(f,$('newsList')); const j=allNews.filter(isJatim).sort((a,b)=>new Date(b.published_at)-new Date(a.published_at)); render(j,$('jatimList')); }
async function loadNews(){ try{const r=await fetch(`data/news.json?ts=${Date.now()}`); if(!r.ok) throw new Error('Gagal mengambil data'); const data=await r.json(); allNews=data.items||[]; const stamp=data.generated_at?new Date(data.generated_at).toLocaleString('id-ID'):'belum tersedia'; $('lastUpdated').textContent=`Data: ${stamp}`; const now=Date.now(), day=allNews.filter(n=>now-new Date(n.published_at).getTime()<=864e5); const j=allNews.filter(isJatim); $('statTotal').textContent=allNews.length; $('statJatim').textContent=j.length; $('stat24').textContent=day.length; $('statHigh').textContent=allNews.filter(n=>n.severity==='high').length; $('jatimTotal').textContent=j.length; $('jatim24').textContent=j.filter(n=>now-new Date(n.published_at).getTime()<=864e5).length; $('jatimHigh').textContent=j.filter(n=>n.severity==='high').length; render(allNews.slice().sort((a,b)=>new Date(b.published_at)-new Date(a.published_at)).slice(0,8),$('recentList')); updateLists(); }catch(e){ $('lastUpdated').textContent='Data gagal dimuat'; console.error(e); } }
function showPage(page){document.querySelectorAll('.page').forEach(x=>x.classList.add('hidden')); $(page+'Page').classList.remove('hidden'); document.querySelectorAll('.nav-item').forEach(x=>x.classList.toggle('active',x.dataset.page===page)); $('pageTitle').textContent={dashboard:'Dashboard',news:'Berita',jatim:'Jawa Timur',settings:'Pengaturan'}[page]||'Dashboard'; if(page==='news'||page==='jatim') updateLists();}
function setup(){document.querySelectorAll('[data-page]').forEach(b=>b.addEventListener('click',()=>showPage(b.dataset.page))); ['q','region','severity','category','sort'].forEach(id=>$(id)?.addEventListener('input',updateLists)); $('refreshBtn').addEventListener('click',()=>loadNews()); $('configStatus').innerHTML=supabaseReady?'<span class="ok">● Supabase terkonfigurasi</span>':'<span class="warn">● Supabase belum dikonfigurasi — edit config.js</span>';}
function initAuth(){
  setup();
  const DEMO_EMAIL = 'admin@propam-jatim.go.id';
  const DEMO_PASSWORD = 'PropamJatim2026!';

  // Demo/static login for GitHub Pages.
  // IMPORTANT: because this is a frontend-only app, these credentials are visible
  // to anyone who can inspect the deployed JavaScript. Use Supabase/Auth backend
  // before deploying sensitive/internal data to production.
  $('loginForm').addEventListener('submit', e => {
    e.preventDefault();
    const email = $('email').value.trim().toLowerCase();
    const password = $('password').value;
    $('loginMsg').textContent = 'Memeriksa…';
    if (email === DEMO_EMAIL && password === DEMO_PASSWORD) {
      sessionStorage.setItem('pnm_logged_in', '1');
      sessionStorage.setItem('pnm_user_email', DEMO_EMAIL);
      enter({email: DEMO_EMAIL});
    } else {
      $('loginMsg').textContent = 'Email atau password salah.';
    }
  });

  $('logoutBtn').addEventListener('click', () => {
    sessionStorage.removeItem('pnm_logged_in');
    sessionStorage.removeItem('pnm_user_email');
    leave();
  });

  if (sessionStorage.getItem('pnm_logged_in') === '1') {
    enter({email: sessionStorage.getItem('pnm_user_email') || DEMO_EMAIL});
  }
}
function enter(user){$('loginView').classList.add('hidden');$('appView').classList.remove('hidden');$('userEmail').textContent=user.email||'';loadNews();}
function leave(){ $('appView').classList.add('hidden'); $('loginView').classList.remove('hidden'); $('email').value=''; $('password').value=''; $('loginMsg').textContent=''; }
initAuth();
