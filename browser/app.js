(()=>{
'use strict';
const API=location.origin;
const PAGE_SIZE=120;
const REQUIRED_API_REVISION=3;
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const migratedFavorites=(()=>{const current=readArray('omniFavorites');if(current.length)return current;const legacy=readArray('omniIconFavorites');if(legacy.length)saveArray('omniFavorites',legacy);return legacy})();
const state={
  source:'all',format:'all',sort:localStorage.getItem('omniSort')||'relevance',density:localStorage.getItem('omniDensity')||'comfortable',copyMode:localStorage.getItem('omniCopyMode')||'smart',
  query:'',offset:0,total:0,items:[],current:null,loading:false,request:0,
  favorites:new Set(migratedFavorites),recent:readArray('omniRecent').slice(0,60),
  sources:[],stats:null,theme:localStorage.getItem('omniTheme')||'dark'
};
const previewCache=new Map();
let toastTimer=0,searchTimer=0;

function readArray(key){try{const v=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(v)?v:[]}catch{return[]}}
function saveArray(key,v){localStorage.setItem(key,JSON.stringify(v))}
function esc(s=''){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function human(n){return Number(n||0).toLocaleString()}
function key(i){return i?.id||''}
function formatOf(i){if(i?.svg||i?.figmaType==='svg')return'svg';if(i?.raster||i?.figmaType==='raster')return'raster';return'font'}
function labelFormat(i){return formatOf(i)==='svg'?'SVG':formatOf(i)==='raster'?'IMG':'FONT'}
function smart(i){return i?.svg?'svg':i?.raster?'asset':i?.char?'glyph':'id'}
function supportsCopy(i,mode){if(!i||!mode||mode==='smart'||mode==='all')return true;if(Array.isArray(i.capabilities))return i.capabilities.includes(mode);if(mode==='id'||mode==='manifest')return !!key(i);if(mode==='svg')return !!i.svg;if(mode==='glyph')return !!i.char;if(mode==='html')return !!i.html;if(mode==='css')return !!i.css;if(mode==='asset')return !!i.raster;return false}
function copyModeLabel(mode){return ({svg:'SVG',glyph:'Glyph',html:'HTML',css:'CSS',id:'ID',manifest:'Manifest'})[mode]||''}
function capabilityList(i){const xs=Array.isArray(i?.capabilities)?i.capabilities.filter(x=>['svg','glyph','html','css'].includes(x)):['svg','glyph','html','css'].filter(x=>supportsCopy(i,x));return [...new Set(xs)]}
function cardCopyLabel(i){const mode=state.copyMode==='smart'?smart(i):state.copyMode;return mode==='asset'?'COPY ASSET':`COPY ${copyModeLabel(mode)||String(mode).toUpperCase()}`}
function capabilityBadges(i){return capabilityList(i).map(c=>`<span class="capability-badge ${state.copyMode===c?'active':''}">${esc(copyModeLabel(c))}</span>`).join('')}
function manifestValue(i){return JSON.stringify({id:key(i),as:pascal(i?.name||i?.label||'Icon')},null,2)}
function pascal(s){return String(s||'Icon').replace(/[^a-zA-Z0-9]+(.)?/g,(_,c)=>c?c.toUpperCase():'').replace(/^./,c=>c.toUpperCase())||'Icon'}
function value(i,mode){if(!i)return'';if(mode==='smart')mode=smart(i);if(mode==='id')return key(i);if(mode==='manifest')return manifestValue(i);if(mode==='svg')return i.svg||'';if(mode==='glyph')return i.char||'';if(mode==='html')return i.html||'';if(mode==='css')return i.css||'';if(mode==='asset')return i.raster||'';return''}
function toast(text){const el=$('#toast');el.textContent=text;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),1500)}
async function copy(text,label='Copied'){if(!text){toast('That format is not available');return false}try{await navigator.clipboard.writeText(text)}catch{const t=document.createElement('textarea');t.value=text;t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();document.execCommand('copy');t.remove()}toast(label);return true}
function setOnline(ok,text){$('#statusDot').classList.toggle('online',!!ok);$('#statusDot').classList.toggle('offline',!ok);$('#serverStatus').textContent=text|| (ok?'Local server connected':'Local server offline')}
function sourceLabel(source){return state.sources.find(x=>x.source===source)?.label||source}

function navSvg(body){return `<svg viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`}
const PACK_NAV_ICONS={
  simpleicons:navSvg('<path d="m12 3 7.5 4.5v9L12 21l-7.5-4.5v-9L12 3Z"/><path d="M8.5 10h7M8.5 14h5"/>'),
  devicon:navSvg('<path d="m8 8-4 4 4 4M16 8l4 4-4 4M14.5 5l-5 14"/>'),
  nerdfonts:navSvg('<rect x="3.5" y="5" width="17" height="14" rx="2.5"/><path d="m7 10 2.5 2L7 14.5M12.5 15H17"/>'),
  bootstrap:navSvg('<rect x="4" y="4" width="16" height="16" rx="4"/><path d="M9 7.5h4a3 3 0 0 1 0 6H9m0-6v9m0-4h4.7a2 2 0 0 1 0 4H9"/>'),
  fluent:navSvg('<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/>'),
  fontawesome:navSvg('<path d="m12 3 2.6 5.3 5.9.9-4.3 4.2 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.2 5.9-.9L12 3Z"/>'),
  heroicons:navSvg('<path d="M12 3 19 6v5c0 4.5-2.8 8-7 10-4.2-2-7-5.5-7-10V6l7-3Z"/><path d="m9.5 12 1.7 1.7 3.6-4"/>'),
  iconoir:navSvg('<circle cx="12" cy="12" r="8"/><path d="m12 7 5 5-5 5-5-5 5-5Z"/>'),
  ionicons:navSvg('<path d="m13.5 3-7 10h5L10.5 21l7-11h-5l1-7Z"/>'),
  lucide:navSvg('<path d="m12 3 1.4 4.1 4.1 1.4-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4L12 3Z"/><path d="m18 14 .8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14Z"/>'),
  material:navSvg('<path d="M5 5h6v6H5zM13 5h6v6h-6zM5 13h6v6H5zM13 13h6v6h-6z"/>'),
  octicons:navSvg('<path d="m12 3 6.5 3.8v7.5L12 21l-6.5-6.7V6.8L12 3Z"/><circle cx="12" cy="12" r="2.5"/>'),
  phosphor:navSvg('<circle cx="12" cy="12" r="2"/><ellipse cx="12" cy="12" rx="9" ry="3.8"/><ellipse cx="12" cy="12" rx="3.8" ry="9" transform="rotate(45 12 12)"/>'),
  tabler:navSvg('<rect x="4" y="5" width="16" height="14" rx="2"/><path d="M4 10h16M10 5v14M15 10v9"/>'),
  favicons:navSvg('<circle cx="12" cy="12" r="8"/><path d="M4 12h16M12 4c2.2 2.3 3.3 5 3.3 8S14.2 17.7 12 20M12 4c-2.2 2.3-3.3 5-3.3 8S9.8 17.7 12 20"/>'),
  custom:navSvg('<path d="M4 7.5 8 4h8l4 3.5V18a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7.5Z"/><path d="M8 4v5h8V4"/>')
};
function packIcon(source,label){
  const normalized=String(source||'').toLowerCase().replace(/[^a-z0-9]/g,'');
  const icon=PACK_NAV_ICONS[normalized]||navSvg('<circle cx="12" cy="12" r="7"/><path d="M9 12h6M12 9v6"/>');
  return `<span class="nav-icon nav-icon-pack" aria-hidden="true">${icon}</span>`
}
function titleFor(){if(state.source==='all')return'All icons';if(state.source==='favorites')return'Favorites';if(state.source==='recent')return'Recently used';if(state.source==='kind:ui')return'UI icons';if(state.source==='kind:brand')return'Brands + favicons';if(state.source==='kind:developer')return'Developer icons';return sourceLabel(state.source)}
function setTheme(theme){state.theme=theme;document.documentElement.dataset.theme=theme==='system'?(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'):theme;localStorage.setItem('omniTheme',theme);$('#themeButton').textContent=theme==='dark'?'◐':theme==='light'?'☀':'◒'}
function cycleTheme(){setTheme(state.theme==='dark'?'light':state.theme==='light'?'system':'dark');toast(`Theme: ${state.theme}`)}
function applyDensity(){const g=$('#grid');g.dataset.density=state.density;$$('[data-density]').forEach(b=>b.classList.toggle('active',b.dataset.density===state.density))}
function updateUrl(){const u=new URL(location.href);state.query?u.searchParams.set('q',state.query):u.searchParams.delete('q');state.source!=='all'?u.searchParams.set('source',state.source):u.searchParams.delete('source');state.copyMode!=='smart'?u.searchParams.set('copy',state.copyMode):u.searchParams.delete('copy');history.replaceState(null,'',u)}
function initFromUrl(){const u=new URL(location.href);state.query=u.searchParams.get('q')||'';state.source=u.searchParams.get('source')||'all';const copy=u.searchParams.get('copy');if(['smart','svg','glyph','html','css','id','manifest'].includes(copy))state.copyMode=copy;$('#search').value=state.query}

async function fetchJson(url){const r=await fetch(url,{cache:'no-store'});const d=await r.json();if(!r.ok||d.ok===false)throw new Error(d.error||`HTTP ${r.status}`);return d}
async function loadBootstrap(){
  try{
    const [health,sources,stats]=await Promise.all([fetchJson(`${API}/api/health`),fetchJson(`${API}/api/sources`),fetchJson(`${API}/api/stats`)]);
    if(Number(health.apiRevision||0)<REQUIRED_API_REVISION){
      setOnline(false,'Outdated local API');
      $('#resultText').textContent='The browser was updated but the local API is still old. Run: omni-icons open';
      $('#grid').innerHTML='<article class="icon-card" style="grid-column:1/-1;min-height:190px"><div class="card-icon">↻</div><div class="card-name">Restart Omni once</div><div class="card-meta">Run <code>omni-icons open</code>. Omni will now detect and replace the stale API automatically.</div></article>';
      return false;
    }
    setOnline(true,`Omni ${health.version}`);$('#versionLabel').textContent=`v${health.version} · local workspace`;state.sources=sources.sources||[];state.stats=stats;
    buildSources();renderStats();syncCounts();$('#footerMeta').textContent=`v${health.version} · ${human(health.icons)} indexed`;
  }catch(err){
    setOnline(false,'Server unavailable');$('#resultText').textContent='Could not reach the local API. Run: omni-icons start';$('#grid').innerHTML=offlineCard(err);return false;
  }
  return true;
}
function offlineCard(err){return `<article class="icon-card" style="grid-column:1/-1;min-height:190px"><div class="card-icon">!</div><div class="card-name">Local server is not running</div><div class="card-meta">Run <code>omni-icons start</code> then refresh · ${esc(err?.message||'')}</div></article>`}
function buildSources(){
  const root=$('#packSources');
  root.innerHTML=state.sources.map(m=>`<button class="nav-item pack-item" data-source="${esc(m.source)}">${packIcon(m.source,m.label)}<span>${esc(m.label)}</span><b>${human(m.count)}</b></button>`).join('');
  syncActiveNav();
}
function renderStats(){const s=state.stats||{};$('#statUi').textContent=human(s.kinds?.ui);$('#statBrand').textContent=human((s.kinds?.brand||0)+(s.kinds?.favicon||0));$('#statDeveloper').textContent=human(s.kinds?.developer);$('#statSources').textContent=human(s.sourceCount||state.sources.length);$('#statTotal').textContent=human(s.total)}
function syncCounts(){const k=state.stats?.kinds||{};$('#count-all').textContent=human(state.stats?.total);$('#count-ui').textContent=human(k.ui);$('#count-brand').textContent=human((k.brand||0)+(k.favicon||0));$('#count-developer').textContent=human(k.developer);$('#count-favorites').textContent=human(state.favorites.size);$('#count-recent').textContent=human(state.recent.length)}
function syncActiveNav(){$$('#sourceList [data-source]').forEach(b=>b.classList.toggle('active',b.dataset.source===state.source))}
function syncCapabilityUi(){const active=!['smart','id','manifest'].includes(state.copyMode);$('#capabilityPill').classList.toggle('hidden',!active);$('#capabilityText').textContent=active?`${copyModeLabel(state.copyMode)} capable only`:'';$('#copyMode').classList.toggle('capability-active',active)}
function renderSkeletons(){const count=state.density==='compact'?28:state.density==='large'?12:18;$('#grid').innerHTML=Array.from({length:count},()=>'<article class="icon-card skeleton-card" aria-hidden="true"><div class="skeleton-icon"></div><div class="skeleton-line wide"></div><div class="skeleton-line"></div></article>').join('')}

async function loadSpecialIds(ids){
  const filtered=ids.filter(Boolean).slice(0,1000);if(!filtered.length)return[];const out=[];
  for(let n=0;n<filtered.length;n+=100){const chunk=filtered.slice(n,n+100);const d=await fetchJson(`${API}/api/batch?ids=${encodeURIComponent(chunk.join(','))}&include=preview`);out.push(...(d.items||[]))}
  const by=new Map(out.map(i=>[i.id,i]));return filtered.map(id=>by.get(id)).filter(Boolean);
}
function clientSpecialFilter(items){
  const q=state.query.trim().toLowerCase();let xs=items;
  if(state.format!=='all')xs=xs.filter(i=>formatOf(i)===state.format);
  if(state.copyMode!=='smart')xs=xs.filter(i=>supportsCopy(i,state.copyMode));
  if(q){const toks=q.split(/\s+/).filter(Boolean);xs=xs.filter(i=>{const h=[i.id,i.name,i.label,i.source,i.sourceLabel,i.style,i.kind,...(i.terms||[])].join(' ').toLowerCase();return toks.every(t=>h.includes(t))})}
  if(state.sort==='name')xs.sort((a,b)=>(a.label||a.name||'').localeCompare(b.label||b.name||''));
  if(state.sort==='pack')xs.sort((a,b)=>(a.sourceLabel||a.source||'').localeCompare(b.sourceLabel||b.source||'')||(a.label||'').localeCompare(b.label||''));
  return xs;
}
async function search(reset=true){
  if(state.loading&&reset)state.request++;
  const request=++state.request;state.loading=true;$('#loadingRow').classList.remove('hidden');$('#loadMore').classList.add('hidden');
  if(reset){state.offset=0;state.items=[];renderSkeletons()}
  state.query=$('#search').value.trim();updateUrl();$('#clearSearch').classList.toggle('hidden',!state.query);$('#viewTitle').textContent=titleFor();$('#viewEyebrow').textContent=state.source==='favorites'?'YOUR COLLECTION':state.source==='recent'?'RECENT ACTIVITY':'LOCAL LIBRARY';
  try{
    let page=[],total=0;
    if(state.source==='favorites'||state.source==='recent'){
      const ids=state.source==='favorites'?[...state.favorites]:state.recent;let xs=clientSpecialFilter(await loadSpecialIds(ids));total=xs.length;page=xs.slice(state.offset,state.offset+PAGE_SIZE);
    }else{
      const p=new URLSearchParams({q:state.query,source:state.source,format:state.format,capability:state.copyMode,sort:state.sort,offset:String(state.offset),limit:String(PAGE_SIZE),include:'preview'});
      const d=await fetchJson(`${API}/api/search?${p}`);
      if(state.copyMode!=='smart' && d.appliedFilters?.capability!==state.copyMode){
        throw new Error(`The running API did not apply the ${state.copyMode} capability filter. Run: omni-icons open`);
      }
      page=d.items||[];total=d.total??page.length;
      // Defense in depth: never render a card that contradicts the selected copy capability.
      if(state.copyMode!=='smart') page=page.filter(i=>supportsCopy(i,state.copyMode));
    }
    if(request!==state.request)return;
    state.items=reset?page:[...state.items,...page];state.total=total;renderGrid();state.offset=state.items.length;
    const cap=state.copyMode==='smart'?'':` · ${copyModeLabel(state.copyMode)} copy ready`;$('#resultText').textContent=`${human(total)} icon${total===1?'':'s'}${state.query?` matching “${state.query}”`:''}${cap}`;
    $('#loadMore').classList.toggle('hidden',state.items.length>=total||!total);$('#empty').classList.toggle('hidden',!!total);setOnline(true);
  }catch(err){if(request===state.request){setOnline(false,'Search API error');$('#resultText').textContent=err.message;toast('Search failed')}}
  finally{if(request===state.request){state.loading=false;$('#loadingRow').classList.add('hidden')}}
}
function cardPreview(i){
  if(i.svg)return `<span class="card-icon render-${esc(i.render||'auto')}">${i.svg}</span>`;
  if(i.raster)return `<span class="card-icon"><img class="raster-icon" src="${esc(i.raster)}" alt=""></span>`;
  if(i.source==='material')return `<span class="card-icon material-icon">${esc(i.char||'')}</span>`;
  if(i.source==='nerdfonts')return `<span class="card-icon nerd-icon">${esc(i.char||'')}</span>`;
  return `<span class="card-icon">${esc(i.char||'◇')}</span>`;
}
function renderGrid(){
  const g=$('#grid');
  g.innerHTML=state.items.map((i,idx)=>{
    const fav=state.favorites.has(key(i));
    const copyLabel=cardCopyLabel(i);
    return `<article class="icon-card" data-index="${idx}" tabindex="0" title="${esc(copyLabel)} · Enter for details" aria-label="${esc(i.label||i.name)} — ${esc(copyLabel)}">
      <span class="card-kind">${esc(i.kind||'icon')}</span>
      <div class="card-actions"><button data-action="favorite" class="${fav?'favorite-on':''}" title="Favorite" aria-label="${fav?'Remove favorite':'Add favorite'}">${fav?'★':'☆'}</button><button data-action="detail" title="Details" aria-label="Open details">•••</button></div>
      ${cardPreview(i)}
      <div class="card-name">${esc(i.label||i.name)}</div>
      <div class="card-meta">${esc(i.sourceLabel||sourceLabel(i.source))}${i.style?` · ${esc(i.style)}`:''}</div>
      <div class="card-capabilities">${capabilityBadges(i)}</div>
      <span class="card-copy-hint">${esc(copyLabel)}</span>
    </article>`
  }).join('');
}

async function ensureFull(i){if(!i)return null;if(i.svg!==undefined&&i.html!==undefined)return i;if(previewCache.has(key(i)))return previewCache.get(key(i));const d=await fetchJson(`${API}/api/icon?id=${encodeURIComponent(key(i))}`);previewCache.set(key(i),d.icon);return d.icon}
function remember(i){const id=key(i);if(!id)return;state.recent=[id,...state.recent.filter(x=>x!==id)].slice(0,60);saveArray('omniRecent',state.recent);syncCounts()}
async function openDetails(item){
  try{const i=await ensureFull(item);state.current=i;remember(i);$('#detailSource').textContent=`${i.kind||'icon'} · ${i.sourceLabel||sourceLabel(i.source)}`.toUpperCase();$('#detailName').textContent=i.label||i.name;$('#detailPack').textContent=i.sourceLabel||sourceLabel(i.source);$('#detailStyle').textContent=i.style||'Default';$('#detailType').textContent=formatOf(i)==='svg'?'Editable SVG':formatOf(i)==='raster'?'Raster image':'Font glyph';$('#detailCode').textContent=i.code?`U+${String(i.code).toUpperCase()}`:'—';$('#idValue').textContent=key(i);$('#htmlValue').textContent=i.html||'Not available';$('#cssValue').textContent=i.css||'Not available';$('#glyphValue').textContent=i.char||'Not available';$('#urlValue').textContent=i.url||'—';$('#smartFormatLabel').textContent=(state.copyMode==='smart'?smart(i):state.copyMode).toUpperCase();$('#detailCapabilities').innerHTML=capabilityList(i).map(c=>`<span class="detail-capability ${state.copyMode===c?'active':''}">${esc(copyModeLabel(c))}</span>`).join('')||'<span class="detail-capability muted">Canonical ID only</span>';renderDetailPreview();syncDetailButtons();$('#details').classList.add('open');$('#details').setAttribute('aria-hidden','false');$('#sidebarScrim').classList.remove('hidden') }catch(err){toast(`Could not open icon: ${err.message}`)}
}
function renderDetailPreview(){const i=state.current;if(!i)return;let html;if(i.svg)html=`<span class="render-${esc(i.render||'auto')}">${i.svg}</span>`;else if(i.raster)html=`<img class="raster-icon" src="${esc(i.raster)}" alt="">`;else if(i.source==='material')html=`<span class="material-icon">${esc(i.char||'')}</span>`;else if(i.source==='nerdfonts')html=`<span class="nerd-icon">${esc(i.char||'')}</span>`;else html=esc(i.char||'◇');$('#detailPreview').innerHTML=html;applyPreviewControls()}
const PREVIEW_SIZE_MIN=24,PREVIEW_SIZE_MAX=180,PREVIEW_SIZE_DEFAULT=96;
function normalizedPreviewSize(value,fallback=PREVIEW_SIZE_DEFAULT){const n=Math.round(Number(value));if(!Number.isFinite(n))return fallback;return Math.min(PREVIEW_SIZE_MAX,Math.max(PREVIEW_SIZE_MIN,n))}
function applyPreviewVisual(size){const color=$('#previewColor').value;$('#detailPreview').style.fontSize=`${size}px`;$('#detailPreview').style.color=color}
function applyPreviewControls(source='range'){const range=$('#previewSize'),exact=$('#previewSizeInput');let size=source==='exact'?normalizedPreviewSize(exact.value,normalizedPreviewSize(range.value)):normalizedPreviewSize(range.value);range.value=String(size);exact.value=String(size);localStorage.setItem('omniPreviewSize',String(size));applyPreviewVisual(size)}
function previewExactWhileTyping(){const range=$('#previewSize'),exact=$('#previewSizeInput');const raw=exact.value.trim();if(raw==='')return;const n=Math.round(Number(raw));if(!Number.isFinite(n)||n<PREVIEW_SIZE_MIN||n>PREVIEW_SIZE_MAX)return;range.value=String(n);applyPreviewVisual(n)}
function commitExactPreviewSize(){applyPreviewControls('exact')}
function restorePreviewSize(){const saved=normalizedPreviewSize(localStorage.getItem('omniPreviewSize')||PREVIEW_SIZE_DEFAULT);$('#previewSize').value=String(saved);$('#previewSizeInput').value=String(saved)}
function syncDetailButtons(){const i=state.current;$('#svgCopyButton').disabled=!i?.svg;$('#htmlCopyButton').disabled=!i?.html;$('#cssCopyButton').disabled=!i?.css;$('#glyphCopyButton').disabled=!i?.char;const chosen=state.copyMode==='smart'?'smart':state.copyMode;const primary=$('#primaryCopyButton');primary.dataset.copy=chosen;$('#primaryCopyLabel').textContent=chosen==='smart'?'Copy best format':`Copy ${copyModeLabel(chosen)}`;primary.disabled=!supportsCopy(i,chosen);$('#smartFormatLabel').textContent=(chosen==='smart'?smart(i):chosen).toUpperCase();const fav=state.favorites.has(key(i));$('#favoriteButton').textContent=fav?'★ Remove favorite':'☆ Add to favorites';$('#favoriteButton').classList.toggle('favorite-on',fav);$('#downloadButton').disabled=!(i?.svg||i?.raster)}
function closeDetails(){state.current=null;$('#details').classList.remove('open');$('#details').setAttribute('aria-hidden','true');if(!$('#sidebar').classList.contains('open'))$('#sidebarScrim').classList.add('hidden')}
async function copyFromItem(item,mode){const full=await ensureFull(item);const actual=mode==='smart'?smart(full):mode;const ok=await copy(value(full,mode),`Copied ${actual==='asset'?'asset path':actual}`);if(ok)remember(full)}
function toggleFavorite(i){const id=key(i);if(!id)return;if(state.favorites.has(id))state.favorites.delete(id);else state.favorites.add(id);saveArray('omniFavorites',[...state.favorites]);syncCounts();if(state.current&&key(state.current)===id)syncDetailButtons();if(state.source==='favorites')search(true);else renderGrid()}
async function downloadCurrent(){const i=state.current;if(!i)return;if(i.svg){const blob=new Blob([i.svg],{type:'image/svg+xml'});downloadBlob(blob,`${safeFile(i.name||'icon')}.svg`);return}if(i.raster){try{const r=await fetch(i.raster);downloadBlob(await r.blob(),`${safeFile(i.name||'icon')}${extensionFrom(i.raster)}`)}catch{toast('Could not download asset')}}}
function safeFile(s){return String(s||'icon').replace(/[^a-z0-9._-]+/gi,'-').replace(/^-+|-+$/g,'')||'icon'}
function extensionFrom(path){const m=String(path).match(/\.(svg|png|webp|jpg|jpeg|ico)(?:\?|$)/i);return m?'.'+m[1].toLowerCase():''}
function downloadBlob(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);toast(`Downloaded ${name}`)}

function setSource(source){state.source=source;state.offset=0;syncActiveNav();closeMobileSidebar();search(true)}
function setFormat(fmt){state.format=fmt;$$('[data-format]').forEach(b=>b.classList.toggle('active',b.dataset.format===fmt));search(true)}
function setCopyMode(mode){state.copyMode=mode;localStorage.setItem('omniCopyMode',mode);updateUrl();syncCapabilityUi();if(state.current)syncDetailButtons();search(true);if(!['smart','id','manifest'].includes(mode))toast(`Showing only ${copyModeLabel(mode)}-capable icons`)}
function resetFilters(){state.source='all';state.format='all';state.sort='relevance';state.copyMode='smart';$('#sortMode').value='relevance';$('#copyMode').value='smart';$('#search').value='';localStorage.setItem('omniCopyMode','smart');syncActiveNav();syncCapabilityUi();$$('[data-format]').forEach(b=>b.classList.toggle('active',b.dataset.format==='all'));search(true)}
function openMobileSidebar(){$('#sidebar').classList.add('open');$('#sidebarScrim').classList.remove('hidden')}
function closeMobileSidebar(){$('#sidebar').classList.remove('open');if(!$('#details').classList.contains('open'))$('#sidebarScrim').classList.add('hidden')}

$('#sourceList').addEventListener('click',e=>{const b=e.target.closest('[data-source]');if(b)setSource(b.dataset.source)});
$('#statStrip').addEventListener('click',e=>{const b=e.target.closest('[data-source]');if(b)setSource(b.dataset.source)});
$('#grid').addEventListener('click',async e=>{const card=e.target.closest('.icon-card');if(!card)return;const i=state.items[+card.dataset.index];const a=e.target.closest('[data-action]');if(a){e.stopPropagation();if(a.dataset.action==='favorite')toggleFavorite(i);else openDetails(i);return}await copyFromItem(i,$('#copyMode').value)});
$('#grid').addEventListener('keydown',e=>{const card=e.target.closest('.icon-card');if(!card)return;const idx=+card.dataset.index;if(e.key==='Enter'){e.preventDefault();openDetails(state.items[idx])}if(e.key.toLowerCase()==='c'){e.preventDefault();copyFromItem(state.items[idx],$('#copyMode').value)}});
$('#search').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>search(true),130)});
$('#search').addEventListener('keydown',e=>{if(e.key==='Enter'&&state.items[0])openDetails(state.items[0])});
$('#clearSearch').onclick=()=>{$('#search').value='';search(true);$('#search').focus()};
$('#randomIcon').onclick=async()=>{try{const source=['favorites','recent'].includes(state.source)?'all':state.source;const d=await fetchJson(`${API}/api/random?source=${encodeURIComponent(source)}&format=${encodeURIComponent(state.format)}&capability=${encodeURIComponent(state.copyMode)}`);openDetails(d.icon)}catch{toast('No icon available')}};
$('#themeButton').onclick=cycleTheme;
$('#copyMode').onchange=e=>setCopyMode(e.target.value);
$('#clearCapability').onclick=()=>{$('#copyMode').value='smart';setCopyMode('smart')};
$('#sortMode').onchange=e=>{state.sort=e.target.value;localStorage.setItem('omniSort',state.sort);search(true)};
$('#formatFilters').onclick=e=>{const b=e.target.closest('[data-format]');if(b)setFormat(b.dataset.format)};
$('#loadMore').onclick=()=>search(false);
$('#resetFilters').onclick=resetFilters;
$('#homeButton').onclick=()=>setSource('all');
$('#copyFaviconCommand').onclick=()=>copy('omni-icons favicon add example.com','Copied favicon command');
$('#collapsePacks').onclick=()=>{const p=$('#packSources');p.classList.toggle('collapsed');$('#collapsePacks').textContent=p.classList.contains('collapsed')?'+':'−'};
$$('[data-density]').forEach(b=>b.onclick=()=>{state.density=b.dataset.density;localStorage.setItem('omniDensity',state.density);applyDensity()});
$('#closeDetails').onclick=closeDetails;$('#sidebarScrim').onclick=()=>{closeDetails();closeMobileSidebar()};$('#openSidebar').onclick=openMobileSidebar;$('#closeSidebar').onclick=closeMobileSidebar;
$('#previewSize').oninput=()=>applyPreviewControls('range');
$('#previewSizeInput').onfocus=e=>setTimeout(()=>e.currentTarget.select(),0);
$('#previewSizeInput').oninput=()=>previewExactWhileTyping();
$('#previewSizeInput').onchange=()=>commitExactPreviewSize();
$('#previewSizeInput').onblur=()=>commitExactPreviewSize();
$('#previewSizeInput').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();commitExactPreviewSize();e.currentTarget.blur()}if(e.key==='Escape'){e.preventDefault();$('#previewSizeInput').value=$('#previewSize').value;e.currentTarget.blur()}};
$('#previewColor').oninput=()=>applyPreviewControls('range');
$('#previewBackgrounds').onclick=e=>{const b=e.target.closest('[data-bg]');if(!b)return;$$('#previewBackgrounds button').forEach(x=>x.classList.toggle('active',x===b));$('#previewStage').className='preview-stage'+(b.dataset.bg==='light'?' light':b.dataset.bg==='transparent'?' transparent':'')};
$('#details').addEventListener('click',e=>{const b=e.target.closest('[data-copy]');if(b&&state.current)copyFromItem(state.current,b.dataset.copy)});
$('#favoriteButton').onclick=()=>state.current&&toggleFavorite(state.current);$('#downloadButton').onclick=downloadCurrent;
matchMedia('(prefers-color-scheme: light)').addEventListener?.('change',()=>{if(state.theme==='system')setTheme('system')});
document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('#search').focus();$('#search').select()}if(e.key==='Escape'){if($('#details').classList.contains('open'))closeDetails();else closeMobileSidebar()}if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('#search').focus();$('#search').select()}});

async function boot(){initFromUrl();restorePreviewSize();setTheme(state.theme);$('#sortMode').value=['relevance','name','pack'].includes(state.sort)?state.sort:'relevance';$('#copyMode').value=['smart','svg','glyph','html','css','id','manifest'].includes(state.copyMode)?state.copyMode:'smart';syncCapabilityUi();applyDensity();const ok=await loadBootstrap();if(!ok)return;syncActiveNav();await search(true)}
boot();
})();
