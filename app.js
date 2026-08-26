const DEMO_EMAIL="admin@propam-jatim.go.id", DEMO_PASSWORD="PropamJatim2026!";
let allNews=[], currentView="dashboard";

const $=id=>document.getElementById(id);
function esc(s=""){return s.replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
function relDate(iso){if(!iso)return "-";const d=new Date(iso);return isNaN(d)?"-":d.toLocaleString("id-ID",{dateStyle:"medium",timeStyle:"short"})}
function card(n){const p=n.priority||"low";return `<article class="news-card"><div class="news-title"><a href="${esc(n.url||"#")}" target="_blank" rel="noopener">${esc(n.title)}</a></div><div class="meta"><span>${esc(n.source||"Unknown")}</span><span>${relDate(n.published_at)}</span><span class="pill ${p}">${p==="high"?"TINGGI":p==="medium"?"SEDANG":"RENDAH"}</span><span class="pill">${esc(n.region||"Indonesia")}</span><span class="pill">${esc(n.category||"Lainnya")}</span></div></article>`}

async function loadData(){
  $("statusText").textContent="Mengambil data...";
  try{
    const r=await fetch(`data/news.json?t=${Date.now()}`,{cache:"no-store"});
    if(!r.ok) throw new Error("HTTP "+r.status);
    const j=await r.json();
    allNews=Array.isArray(j)?j:(j.items||[]);
    allNews.sort((a,b)=>new Date(b.published_at||0)-new Date(a.published_at||0));
    render();
    const updated=allNews[0]?.collected_at||j.generated_at;
    $("lastUpdated").textContent=updated?`Update: ${relDate(updated)}`:"Data aktif";
    $("statusText").textContent="Collector aktif";
    $("statusDot").style.background="var(--ok)";
  }catch(e){
    $("statusText").textContent="Data gagal dimuat";
    $("statusDot").style.background="var(--danger)";
    console.error(e);
  }
}
function render(){
  const now=Date.now(), day=86400000;
  $("sTotal").textContent=allNews.length;
  $("sJatim").textContent=allNews.filter(n=>n.is_jatim).length;
  $("s24").textContent=allNews.filter(n=>now-new Date(n.published_at||0).getTime()<=day).length;
  $("sHigh").textContent=allNews.filter(n=>n.priority==="high").length;
  const cats={}; allNews.forEach(n=>cats[n.category||"Lainnya"]=(cats[n.category||"Lainnya"]||0)+1);
  const topCats=Object.entries(cats).sort((a,b)=>b[1]-a[1]).slice(0,8), max=topCats[0]?.[1]||1;
  $("categories").innerHTML=topCats.map(([k,v])=>`<div class="bar"><div class="bar-top"><span>${esc(k)}</span><b>${v}</b></div><div class="bar-bg"><div class="bar-fill" style="width:${v/max*100}%"></div></div></div>`).join("")||`<div class="empty">Belum ada data</div>`;
  $("latest").innerHTML=allNews.slice(0,8).map(card).join("")||`<div class="empty">Belum ada berita. Jalankan GitHub Actions.</div>`;
  const catsSorted=Object.keys(cats).sort();
  $("category").innerHTML=`<option value="all">Semua Kategori</option>`+catsSorted.map(c=>`<option>${esc(c)}</option>`).join("");
  applyFilters();
}
function applyFilters(){
  let x=[...allNews];
  const q=($("search").value||"").toLowerCase(), reg=$("region").value, pri=$("priority").value, cat=$("category").value;
  if(q)x=x.filter(n=>[n.title,n.source,n.region,n.category,n.summary].join(" ").toLowerCase().includes(q));
  if(reg==="jatim")x=x.filter(n=>n.is_jatim);
  if(reg==="outside")x=x.filter(n=>!n.is_jatim);
  if(pri!=="all")x=x.filter(n=>n.priority===pri);
  if(cat!=="all")x=x.filter(n=>n.category===cat);
  if(currentView==="jatim")x=x.filter(n=>n.is_jatim);
  if(currentView==="high")x=x.filter(n=>n.priority==="high");
  $("list").innerHTML=x.map(card).join("")||`<div class="empty">Tidak ada berita yang sesuai filter.</div>`;
}
function setView(v){
  currentView=v;
  document.querySelectorAll(".nav").forEach(b=>b.classList.toggle("active",b.dataset.view===v));
  $("dashboardView").classList.toggle("hidden",v!=="dashboard");
  $("listView").classList.toggle("hidden",v==="dashboard");
  $("pageTitle").textContent=v==="dashboard"?"Dashboard":v==="jatim"?"Jawa Timur":v==="high"?"Prioritas Tinggi":"Semua Berita";
  if(v!=="dashboard")applyFilters();
}
$("loginForm").addEventListener("submit",e=>{
  e.preventDefault();
  if($("email").value.trim()===DEMO_EMAIL && $("password").value===DEMO_PASSWORD){
    sessionStorage.setItem("pnm_auth","1"); $("login").classList.add("hidden"); $("app").classList.remove("hidden"); loadData();
  }else $("loginError").textContent="Email atau password salah.";
});
$("logout").onclick=()=>{sessionStorage.removeItem("pnm_auth");location.reload()};
document.querySelectorAll(".nav").forEach(b=>b.onclick=()=>setView(b.dataset.view));
document.querySelectorAll(".linkbtn").forEach(b=>b.onclick=()=>setView(b.dataset.view));
["search","region","priority","category"].forEach(id=>$(id).addEventListener("input",applyFilters));
$("refresh").onclick=loadData;
if(sessionStorage.getItem("pnm_auth")==="1"){$("login").classList.add("hidden");$("app").classList.remove("hidden");loadData()}
