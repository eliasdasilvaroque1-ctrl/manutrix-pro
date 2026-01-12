<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MANUTRIX PRO – ENTERPRISE</title>

<style>
:root{
 --bg:#0f172a;--card:#1e293b;--input:#0f172a;
 --primary:#10b981;--danger:#ef4444;--warning:#f59e0b;
 --text:#f8fafc;--muted:#94a3b8;--border:#334155;
}
body{margin:0;background:var(--bg);color:var(--text);font-family:Segoe UI}
.container{max-width:720px;margin:auto;padding:10px}
.card{background:var(--card);padding:18px;border-radius:14px;border:1px solid var(--border);margin-bottom:14px}
h3{margin:0 0 12px}
label{font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase}
input,select,textarea,button{
 width:100%;margin:8px 0 14px;padding:12px;
 background:var(--input);color:#fff;border:1px solid var(--border);
 border-radius:10px;font-size:14px
}
button{background:var(--primary);border:none;font-weight:bold;cursor:pointer}
.hidden{display:none}
.row{display:flex;gap:10px}
.item{display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid var(--border)}
.badge{font-size:10px;padding:3px 8px;border-radius:50px;background:var(--border)}
.bg-danger{background:var(--danger)}
.bg-warning{background:var(--warning);color:#000}
</style>
</head>
<body>

<div class="container">

<!-- LOGIN -->
<section id="screen-login" class="card">
<h3>🔐 Login</h3>
<input id="loginUser" placeholder="Usuário">
<input id="loginPin" type="password" inputmode="numeric" placeholder="PIN">
<button onclick="Auth.login()">Entrar</button>
</section>

<!-- MENU -->
<section id="screen-menu" class="card hidden">
<h3>🛠 Painel</h3>
<button onclick="App.showOS()">Registrar OS / Inspeção</button>
<button class="bg-warning" onclick="App.showNC()">Pendências NC <span id="ncCount" class="badge">0</span></button>
<button id="btnConfig" onclick="App.showConfig()">Configurações</button>
<button class="bg-danger" onclick="Auth.logout()">Sair</button>
</section>

<!-- OS -->
<section id="screen-os" class="card hidden">
<h3>📋 Ordem de Serviço</h3>

<label>Técnico</label>
<input id="osUser" disabled>

<label>Área</label>
<select id="area" onchange="App.fillEquip()"></select>

<label>Equipamento</label>
<select id="equip"></select>

<label>Tipo</label>
<select id="tipo" onchange="UI.toggleInspecao()">
<option>Preventiva</option>
<option>Corretiva</option>
<option>Inspeção</option>
</select>

<div id="inspBox" class="hidden">
<label>Status Inspeção</label>
<select id="inspStatus">
<option value="OK">Conforme</option>
<option value="NC">Não Conforme</option>
</select>
<textarea id="inspDesc" placeholder="Descrever não conformidade"></textarea>
</div>

<div class="row">
<input type="time" id="ini">
<input type="time" id="fim">
</div>

<textarea id="obs" placeholder="Observações"></textarea>

<button onclick="App.save()">Salvar</button>
<button onclick="App.back()">Voltar</button>
</section>

<!-- NC -->
<section id="screen-nc" class="card hidden">
<h3>⚠️ Pendências</h3>
<div id="ncList"></div>
<button onclick="App.back()">Voltar</button>
</section>

<!-- CONFIG -->
<section id="screen-config" class="card hidden">
<h3>⚙️ Configurações (ADM)</h3>

<label>Novo Usuário</label>
<input id="cfgUser" placeholder="Nome">
<input id="cfgPin" placeholder="PIN (mín. 4)">
<select id="cfgRole">
<option value="operador">Operador</option>
<option value="admin">Administrador</option>
</select>
<button onclick="Cfg.addUser()">Adicionar Usuário</button>

<div id="userList"></div>

<hr>

<label>Ativos</label>
<input id="cfgArea" placeholder="Área">
<input id="cfgTipo" placeholder="Tipo">
<input id="cfgTag" placeholder="TAG">
<button onclick="Cfg.addEquip()">Adicionar Ativo</button>
<div id="equipList"></div>

<hr>
<button onclick="Cfg.exportCSV()">Exportar CSV</button>
<button onclick="App.back()">Voltar</button>
</section>

</div>

<script>
/* ===== DB ===== */
const DB={
 g:k=>JSON.parse(localStorage.getItem('mx_'+k)||'[]'),
 s:(k,v)=>localStorage.setItem('mx_'+k,JSON.stringify(v))
};

/* ===== BOOTSTRAP ADMIN ===== */
(function(){
 const users=DB.g('users');
 if(!users.some(u=>u.nome==="ADMIN")){
  users.push({nome:"ADMIN",pin:"9937",role:"admin"});
  DB.s('users',users);
 }
})();

/* ===== AUTH ===== */
const Auth={
 current:null,
 login(){
  const nome=loginUser.value.trim();
  const pin=loginPin.value.trim();
  const user=DB.g('users').find(u=>u.nome===nome&&u.pin===pin);
  if(!user) return alert("Usuário ou PIN inválido");
  this.current=user;
  DB.s('session',user);
  screen-login.classList.add('hidden');
  screen-menu.classList.remove('hidden');
  if(user.role!=="admin") btnConfig.classList.add('hidden');
 },
 logout(){localStorage.removeItem('mx_session');location.reload();}
};

/* ===== APP ===== */
const App={
 showOS(){
  screen-menu.classList.add('hidden');
  screen-os.classList.remove('hidden');
  osUser.value=Auth.current.nome;
  const equips=DB.g('equips');
  area.innerHTML=[...new Set(equips.map(e=>e.area))].map(a=>`<option>${a}</option>`).join('');
  this.fillEquip();
 },
 fillEquip(){
  equip.innerHTML=DB.g('equips')
   .filter(e=>e.area===area.value)
   .map(e=>`${e.tipo} | ${e.tag}`)
   .map(e=>`<option>${e}</option>`).join('');
 },
 save(){
  if(!ini.value||!fim.value) return alert("Horários obrigatórios");
  const a=ini.value.split(':'),b=fim.value.split(':');
  let dur=(+b[0]*60+ +b[1])-(+a[0]*60+ +a[1]);
  if(dur<0) dur+=1440;
  const rec={
   usuario:Auth.current.nome,
   area:area.value,
   equipamento:equip.value,
   tipo:tipo.value,
   duracaoMin:dur,
   obs:obs.value.replace(/[,;]/g,'.'),
   ts:Date.now()
  };
  const os=DB.g('os'); os.unshift(rec); DB.s('os',os);
  if(tipo.value==="Inspeção"&&inspStatus.value==="NC"){
   const nc=DB.g('nc');
   nc.unshift({ativo:rec.equipamento,desc:inspDesc.value,ts:Date.now(),status:"Aberto"});
   DB.s('nc',nc);
  }
  alert("OS registrada com sucesso");
  location.reload();
 },
 showNC(){
  screen-menu.classList.add('hidden');
  screen-nc.classList.remove('hidden');
  ncList.innerHTML=DB.g('nc').map(n=>`<div class="item">${n.ativo}<span class="badge bg-warning">ABERTO</span></div>`).join('');
 },
 showConfig(){screen-menu.classList.add('hidden');screen-config.classList.remove('hidden');Cfg.render()},
 back(){location.reload()}
};

/* ===== CONFIG ===== */
const Cfg={
 render(){
  userList.innerHTML=DB.g('users').map(u=>`<div class="item">${u.nome} (${u.role})</div>`).join('');
  equipList.innerHTML=DB.g('equips').map(e=>`<div class="item">${e.area} | ${e.tipo} | ${e.tag}</div>`).join('');
 },
 addUser(){
  if(cfgUser.value===""||cfgPin.value.length<4) return alert("Dados inválidos");
  const users=DB.g('users');
  users.push({nome:cfgUser.value,pin:cfgPin.value,role:cfgRole.value});
  DB.s('users',users);
  cfgUser.value=cfgPin.value="";
  this.render();
 },
 addEquip(){
  const d=DB.g('equips');
  d.push({area:cfgArea.value,tipo:cfgTipo.value,tag:cfgTag.value});
  DB.s('equips',d);
  cfgArea.value=cfgTipo.value=cfgTag.value="";
  this.render();
 },
 exportCSV(){
  const o=DB.g('os');
  let c="Data,Usuario,Area,Equipamento,Tipo,Duracao,Obs\n";
  o.forEach(r=>c+=`${new Date(r.ts).toLocaleString()},${r.usuario},${r.area},${r.equipamento},${r.tipo},${r.duracaoMin},${r.obs}\n`);
  const b=new Blob([c]);const a=document.createElement('a');
  a.href=URL.createObjectURL(b);a.download="manutrix.csv";a.click();
 }
};

/* UI */
const UI={toggleInspecao:()=>inspBox.classList.toggle('hidden',tipo.value!=="Inspeção")};
ncCount.innerText=DB.g('nc').length;
</script>
</body>
</html>
