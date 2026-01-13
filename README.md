<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>MANUTRIX OMNI • LOGIN INDUSTRIAL</title>

<script src="https://cdn.jsdelivr.net/npm/idb@8/build/umd.js"></script>

<style>
:root{
 --bg:#020617;--card:#0f172a;--accent:#10b981;--danger:#ef4444;
 --muted:#64748b;--border:#1e293b
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:#fff;font-family:system-ui}
.hidden{display:none}
.container{max-width:900px;margin:auto;padding:16px 16px 110px}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px;margin-bottom:16px}
input,select,textarea,button{
 width:100%;padding:14px;border-radius:12px;border:1px solid var(--border);
 background:#000;color:#fff;font-size:16px;margin-bottom:12px
}
button{background:var(--accent);color:#000;font-weight:800;border:none;cursor:pointer}
.btn-sec{background:var(--border);color:#fff}
.btn-danger{background:rgba(239,68,68,.15);color:var(--danger);border:1px solid var(--danger)}
nav{position:fixed;bottom:0;left:0;right:0;display:flex;gap:8px;
 padding:12px;background:rgba(15,23,42,.95);border-top:1px solid var(--border)}
.badge{font-size:10px;padding:4px 8px;border-radius:6px;background:var(--border)}
</style>
</head>

<body>
<div class="container">

<!-- LOGIN -->
<section id="auth">
 <div class="card" style="margin-top:28vh;text-align:center">
  <h2>MANUTRIX OMNI</h2>
  <input id="login-user" placeholder="Usuário (ex: admin)">
  <input id="login-pass" type="password" placeholder="Senha">
  <button onclick="Auth.login()">ENTRAR</button>
 </div>
</section>

<!-- DASH -->
<section id="dash" class="hidden">
 <div class="card">
  <b>Usuário:</b> <span id="u-name"></span>
  <span class="badge" id="u-role"></span>
 </div>

 <button onclick="UI.nav('os')">➕ NOVA OS</button>
 <button class="btn-sec" onclick="UI.nav('hist')">📋 HISTÓRICO</button>
 <button class="btn-sec hidden" id="btn-setup" onclick="UI.nav('setup')">⚙️ SETUP (ADMIN)</button>
</section>

<!-- OS -->
<section id="os" class="hidden">
 <h3>NOVA ORDEM DE SERVIÇO</h3>
 <select id="os-asset"></select>
 <select id="os-type">
  <option>Preventiva</option>
  <option>Corretiva</option>
  <option>Inspeção</option>
 </select>
 <select id="os-exec" multiple style="height:100px"></select>
 <textarea id="os-desc" placeholder="Descrição obrigatória"></textarea>
 <button onclick="App.commitOS()">REGISTRAR</button>
 <button class="btn-sec" onclick="UI.nav('dash')">CANCELAR</button>
</section>

<!-- HIST -->
<section id="hist" class="hidden">
 <h3>HISTÓRICO</h3>
 <div id="list"></div>
</section>

<!-- SETUP ADMIN -->
<section id="setup" class="hidden">
 <h3>ADMIN • USUÁRIOS</h3>
 <input id="u-new" placeholder="Usuário (ex: mecanico1)">
 <input id="p-new" placeholder="Senha">
 <select id="r-new">
  <option value="user">Usuário</option>
  <option value="admin">Admin</option>
 </select>
 <button onclick="Admin.addUser()">Adicionar Usuário</button>
 <div id="user-list"></div>

 <h3>ATIVOS</h3>
 <input id="a-tag" placeholder="TAG">
 <button onclick="Admin.addAsset()">Adicionar Ativo</button>
 <div id="asset-list"></div>

 <h3>EXECUTANTES</h3>
 <input id="e-name" placeholder="Nome">
 <button onclick="Admin.addExec()">Adicionar Executante</button>
 <div id="exec-list"></div>
</section>

</div>

<nav id="nav" class="hidden">
 <button onclick="UI.nav('dash')">🏠</button>
 <button onclick="UI.nav('hist')">📋</button>
 <button class="btn-danger" onclick="Auth.logout()">🚪</button>
</nav>

<script>
/* ===== CORE ===== */
const $=i=>document.getElementById(i)
const uuid=()=>crypto.randomUUID()

let State={user:null,users:[],assets:[],execs:[],os:[]}

/* ===== DB ===== */
const DB={
 db:null,
 async init(){
  this.db=await idb.openDB('omni_login_fixed',1,{
   upgrade(db){db.createObjectStore('state')}
  })
 },
 async load(){
  const s=await this.db.get('state','root')
  if(s) State=s
  if(!State.users.length){
   State.users.push({id:uuid(),user:'admin',pass:'9937',role:'admin'})
   await this.save()
  }
 },
 async save(){
  await this.db.put('state',structuredClone(State),'root')
 }
}

/* ===== AUTH ===== */
const Auth={
 async login(){
  const u=$('login-user').value.trim()
  const p=$('login-pass').value.trim()
  const found=State.users.find(x=>x.user===u&&x.pass===p)
  if(!found) return alert('Credenciais inválidas')
  State.user={id:found.id,user:found.user,role:found.role}
  await DB.save()
  UI.boot()
 },
 logout(){
  State.user=null
  DB.save().then(()=>location.reload())
 }
}

/* ===== UI ===== */
const UI={
 nav(id){
  document.querySelectorAll('section').forEach(s=>s.classList.add('hidden'))
  $(id).classList.remove('hidden')
  $('nav').classList.toggle('hidden',id==='auth')
  if(id==='dash'){
   $('u-name').innerText=State.user.user
   $('u-role').innerText=State.user.role
   $('btn-setup').classList.toggle('hidden',State.user.role!=='admin')
  }
  if(id==='os') App.prepareOS()
  if(id==='hist') App.renderHist()
  if(id==='setup') Admin.render()
 },
 boot(){
  $('auth').classList.add('hidden')
  this.nav('dash')
 }
}

/* ===== ADMIN ===== */
const Admin={
 async addUser(){
  if(!$('u-new').value||!$('p-new').value) return
  State.users.push({id:uuid(),user:$('u-new').value,pass:$('p-new').value,role:$('r-new').value})
  await DB.save();this.render()
 },
 async addAsset(){
  if(!$('a-tag').value) return
  State.assets.push({id:uuid(),tag:$('a-tag').value})
  await DB.save();this.render()
 },
 async addExec(){
  if(!$('e-name').value) return
  State.execs.push({id:uuid(),name:$('e-name').value})
  await DB.save();this.render()
 },
 render(){
  $('user-list').innerHTML=State.users.map(u=>`<div class="card">${u.user} (${u.role})</div>`).join('')
  $('asset-list').innerHTML=State.assets.map(a=>`<div class="card">${a.tag}</div>`).join('')
  $('exec-list').innerHTML=State.execs.map(e=>`<div class="card">${e.name}</div>`).join('')
 }
}

/* ===== APP ===== */
const App={
 prepareOS(){
  $('os-asset').innerHTML=State.assets.map(a=>`<option value="${a.id}">${a.tag}</option>`).join('')
  $('os-exec').innerHTML=State.execs.map(e=>`<option value="${e.id}">${e.name}</option>`).join('')
 },
 async commitOS(){
  State.os.push({
   id:uuid(),
   asset:$('os-asset').value,
   type:$('os-type').value,
   execs:[...$('os-exec').selectedOptions].map(o=>o.value),
   desc:$('os-desc').value,
   user:State.user.user,
   ts:new Date().toISOString()
  })
  await DB.save()
  UI.nav('dash')
 },
 renderHist(){
  $('list').innerHTML=State.os.map(o=>`
   <div class="card">
    <b>${State.assets.find(a=>a.id===o.asset)?.tag}</b>
    <small>${o.user} • ${new Date(o.ts).toLocaleString()}</small>
    <p>${o.desc}</p>
   </div>
  `).join('')
 }
}

/* ===== BOOT ===== */
(async()=>{
 await DB.init()
 await DB.load()
 if(State.user) UI.boot()
})();
</script>
</body>
</html>
