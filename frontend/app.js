const $ = id => document.getElementById(id);
let currentProjectId = null;
let csrf = '';
let currentState = null;
let poller = null;

async function api(url, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (!(opts.body instanceof FormData) && opts.body !== undefined) headers['Content-Type'] = 'application/json';
  if (csrf) headers['X-CSRF-Token'] = csrf;
  const r = await fetch(url, { ...opts, headers });
  let d = {};
  try { d = await r.json(); } catch (_) {}
  if (!r.ok) throw new Error(d.error || `Request failed (${r.status})`);
  return d;
}

function esc(x) {
  return String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
}
function toast(t) { const e=$('toast'); e.textContent=t; e.style.display='block'; clearTimeout(window.__toast); window.__toast=setTimeout(()=>e.style.display='none',2800); }
function isLoggedIn() { return $('userName').textContent !== 'Guest'; }
function requireProject() { if (!currentProjectId) { toast('Open or create a project first.'); return false; } return true; }

function tab(name) {
  document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active', x.id===name));
  document.querySelectorAll('#nav [data-tab]').forEach(x=>x.classList.toggle('active', x.dataset.tab===name));
  $('nav').classList.remove('open');
  if (currentProjectId) loadAll();
}
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>tab(b.dataset.tab)));
$('mobileMenu').addEventListener('click',()=>$('nav').classList.toggle('open'));

async function login() {
  try {
    const d=await api('/api/login',{method:'POST',body:JSON.stringify({email:$('loginEmail').value.trim(),password:$('loginPassword').value})});
    csrf=d.csrf||''; setUser(d.user); $('loginModal').classList.add('hidden'); toast('Workspace ready'); await loadProjects();
    if (!currentProjectId) await loadDemo();
  } catch(e){toast(e.message)}
}
async function signup() {
  try {
    const d=await api('/api/signup',{method:'POST',body:JSON.stringify({name:$('signupName').value.trim(),email:$('signupEmail').value.trim(),password:$('signupPassword').value})});
    csrf=d.csrf||''; setUser(d.user); $('loginModal').classList.add('hidden'); toast('Account created'); await loadProjects();
  } catch(e){toast(e.message)}
}
function setUser(u) {
  $('userName').textContent=`${u.name} · ${u.role}`; $('loginBtn').classList.add('hidden'); $('logoutBtn').classList.remove('hidden');
}
$('loginBtn').addEventListener('click',()=>$('loginModal').classList.remove('hidden'));
$('closeLogin').addEventListener('click',()=>$('loginModal').classList.add('hidden'));
$('doLogin').addEventListener('click',login); $('doSignup').addEventListener('click',signup);
$('showLogin').addEventListener('click',()=>{$('loginForm').classList.remove('hidden');$('signupForm').classList.add('hidden')});
$('showSignup').addEventListener('click',()=>{$('signupForm').classList.remove('hidden');$('loginForm').classList.add('hidden')});
$('logoutBtn').addEventListener('click',async()=>{try{await api('/api/logout',{method:'POST'});csrf='';currentProjectId=null;currentState=null;localStorage.removeItem('nexusProject');$('userName').textContent='Guest';$('loginBtn').classList.remove('hidden');$('logoutBtn').classList.add('hidden');if(poller)clearInterval(poller);toast('Logged out')}catch(e){toast(e.message)}});

async function loadProjects(){
  try {
    const d=await api('/api/projects');
    $('projectList').innerHTML=d.projects.length?d.projects.map(p=>`<div class="card"><span class="pill blue">PROJECT #${p.id}</span><h3>${esc(p.name)}</h3><p>${esc(p.description)}</p><p class="muted">${p.deadline_days} days · team ${p.team_size} · budget ₹${Number(p.budget||0).toLocaleString('en-IN')}</p><button class="secondary project-open" data-id="${p.id}">Open project</button></div>`).join(''):'<div class="panel">No projects yet. Create one or load the demo.</div>';
    document.querySelectorAll('.project-open').forEach(b=>b.addEventListener('click',()=>selectProject(+b.dataset.id)));
  } catch(e) { $('projectList').innerHTML='<div class="panel">Please login to view projects.</div>'; }
}
async function selectProject(id){currentProjectId=id;localStorage.setItem('nexusProject',id);await loadAll();tab('dashboard');}
async function loadDemo(){try{if(!isLoggedIn()){ $('loginModal').classList.remove('hidden'); return; } const d=await api('/api/projects/demo',{method:'POST',body:'{}'});currentProjectId=d.project.id;localStorage.setItem('nexusProject',currentProjectId);toast('Live demo loaded');await loadAll();tab('dashboard')}catch(e){toast(e.message)}}
$('homeDemo').addEventListener('click',loadDemo);$('demoBtn').addEventListener('click',loadDemo);

async function loadAll(){
  if(!currentProjectId)return;
  try{
    const s=await api(`/api/projects/${currentProjectId}`); currentState=s;
    renderDashboard(s);renderTasks(s);renderTeam(s);renderRisks(s);renderMonitor(s);renderSignals(s);renderMetrics(s);await loadActivity(s);await loadNotifications();await loadAnalytics();
    $('wfTeam').value=s.project.team_size;$('wfDeadline').value=s.project.deadline_days;$('wfBudget').value=s.project.budget||0;$('dashTitle').textContent=s.project.name;
    $('costSummary').innerHTML=`Estimated current cost: <b>₹${Number(s.cost_estimate?.total||0).toLocaleString('en-IN')}</b> · labor ₹${Number(s.cost_estimate?.labor||0).toLocaleString('en-IN')} · infrastructure ₹${Number(s.cost_estimate?.infrastructure||0).toLocaleString('en-IN')} · AI ₹${Number(s.cost_estimate?.ai||0).toLocaleString('en-IN')}`;
  }catch(e){toast(e.message)}
}
function renderMetrics(s){$('metrics').innerHTML=[['Health',s.health+'%'],['Progress',s.progress+'%'],['High risks',s.high_risks],['Blocked',s.blocked]].map(x=>`<div class="metric"><b>${esc(x[1])}</b><span>${esc(x[0])}</span></div>`).join('')}
function renderDashboard(s){
  const hc=s.health>=75?'health-ok':s.health>=50?'health-warn':'health-bad';
  $('dash').innerHTML=`<div class="panel"><div class="two-col"><div><div class="eyebrow">PROJECT HEALTH</div><div class="health-ring ${hc}">${s.health}%</div><p class="muted">${esc(s.health_status)}. ${esc((s.explanation||[]).join(' '))}</p></div><div><div class="kpi-grid"><div class="kpi"><strong>${s.progress}%</strong><small>progress</small></div><div class="kpi"><strong>${s.tasks.length}</strong><small>tasks</small></div><div class="kpi"><strong>${s.high_risks}</strong><small>high risks</small></div><div class="kpi"><strong>${s.team.length}</strong><small>team members</small></div></div><div class="list-item"><b>Decision summary</b><p class="muted">Top risk: ${esc(s.risks?.[0]?.name||'None')} · Next action: ${esc(s.tasks.find(t=>t.status!=='COMPLETED')?.name||'None')} · Unread alerts: ${s.unread_notifications||0}</p></div><div class="panel"><b>Critical path</b><p class="muted">${(s.critical_path_details||[]).map(t=>esc(t.task_key+' '+t.name)+' ('+t.effort+'d)').join(' → ') || 'No critical path detected'}</p><small class="muted">Duration: ${s.critical_path_duration} days · Slack: ${s.critical_path_slack} days · ${s.dependency_cycle?'Dependency cycle detected':''}</small></div></div></div></div><div class="result-grid"><div class="panel"><h2>What needs attention</h2>${s.risks.slice(0,4).map(r=>`<div class="list-item risk-${r.severity==='LOW'?'low':'high'}"><b>${esc(r.name)} — ${esc(r.severity)} ${r.score}/10</b><p>${esc(r.explanation)}</p><small class="muted">Action: ${esc(r.mitigation)}</small></div>`).join('')}</div><div class="panel"><h2>Next actions</h2>${s.tasks.filter(t=>t.status!=='COMPLETED').slice(0,5).map(t=>`<div class="list-item"><b>${esc(t.task_key)} · ${esc(t.name)}</b><p class="muted">${esc(t.priority)} · ${t.effort} effort · ${esc(t.owner)}</p></div>`).join('')}</div></div>`;
}
function renderTasks(s){
  $('tasksTable').innerHTML=`<table class="table"><thead><tr><th>ID</th><th>Task</th><th>Priority</th><th>Effort</th><th>Status</th><th>Owner</th><th>Risk</th><th>Actions</th></tr></thead><tbody>${s.tasks.map(t=>`<tr><td>${esc(t.task_key)}</td><td><b>${esc(t.name)}</b><br><small class="muted">${esc(t.description)}</small></td><td>${esc(t.priority)}</td><td>${t.effort}</td><td><select class="task-status" data-id="${t.id}">${['NOT STARTED','IN PROGRESS','BLOCKED','COMPLETED'].map(v=>`<option ${v===t.status?'selected':''}>${v}</option>`).join('')}</select></td><td>${esc(t.owner)}</td><td>${esc(t.risk_level)}</td><td><div class="card-actions"><button class="ghost task-edit" data-id="${t.id}">Edit</button><button class="secondary team-recommend" data-id="${t.id}">AI Recommend</button><button class="ghost task-delete" data-id="${t.id}">Delete</button></div></td></tr>`).join('')}</tbody></table>`;
  document.querySelectorAll('.task-status').forEach(e=>e.addEventListener('change',()=>changeTask(+e.dataset.id,'status',e.value)));
  document.querySelectorAll('.task-edit').forEach(e=>e.addEventListener('click',()=>openTaskEditor(+e.dataset.id)));
  document.querySelectorAll('.task-delete').forEach(e=>e.addEventListener('click',()=>deleteTask(+e.dataset.id)));
  document.querySelectorAll('.team-recommend').forEach(e=>e.addEventListener('click',()=>recommendTeam(+e.dataset.id)));
  renderDependencyManager(s);
}
function renderDependencyManager(s){
  const from=$('depFrom'), to=$('depTo');
  if(!from||!to)return;
  const opts=s.tasks.map(t=>`<option value="${t.id}">${esc(t.task_key)} · ${esc(t.name)}</option>`).join('');
  from.innerHTML=opts; to.innerHTML=opts;
  if(s.tasks.length>1)to.value=s.tasks[1].id;
  $('dependencyGraph').innerHTML=s.dependencies.length?`<div class="dependency-list">${s.dependencies.map(d=>`<div class="list-item"><b>${esc(d.from_task)} → ${esc(d.to_task)}</b><button class="ghost dependency-delete" data-id="${d.id}">Remove</button></div>`).join('')}</div>`:'<p class="muted">No dependencies yet. Add a dependency to make scheduling and critical-path relationships explicit.</p>';
  document.querySelectorAll('.dependency-delete').forEach(b=>b.addEventListener('click',async()=>{try{await api(`/api/dependencies/${b.dataset.id}`,{method:'DELETE'});await loadAll();toast('Dependency removed')}catch(e){toast(e.message)}}));
}
$('addDependency').addEventListener('click',async()=>{if(!requireProject())return;const from=+$('depFrom').value,to=+$('depTo').value;if(!from||!to||from===to){toast('Choose two different tasks');return}try{await api('/api/dependencies',{method:'POST',body:JSON.stringify({project_id:currentProjectId,from_task_id:from,to_task_id:to})});await loadAll();toast('Dependency added')}catch(e){toast(e.message)}});

async function changeTask(id,k,v){try{await api(`/api/tasks/${id}`,{method:'PATCH',body:JSON.stringify({[k]:v})});toast('Task updated');await loadAll()}catch(e){toast(e.message)}}
async function deleteTask(id){if(!confirm('Delete this task?'))return;try{await api(`/api/tasks/${id}`,{method:'DELETE'});toast('Task deleted');await loadAll()}catch(e){toast(e.message)}}
$('addTask').addEventListener('click',async()=>{if(!requireProject())return;const name=prompt('Task name');if(!name)return;try{await api('/api/tasks',{method:'POST',body:JSON.stringify({project_id:currentProjectId,name})});await loadAll();toast('Task created')}catch(e){toast(e.message)}});

function openTaskEditor(id){const t=currentState?.tasks.find(x=>x.id===id);if(!t)return; $('editTaskId').value=id;$('editTaskName').value=t.name;$('editTaskDescription').value=t.description||'';$('editTaskOwner').value=t.owner||'';$('editTaskPriority').value=t.priority;$('editTaskEffort').value=t.effort;$('editTaskDue').value=t.due_date||'';$('editTaskStatus').value=t.status;$('taskModal').classList.remove('hidden')}
$('closeTaskModal').addEventListener('click',()=>$('taskModal').classList.add('hidden'));
$('cancelTaskEdit').addEventListener('click',()=>$('taskModal').classList.add('hidden'));
$('saveTaskEdit').addEventListener('click',async()=>{try{const id=+$('editTaskId').value;await api(`/api/tasks/${id}`,{method:'PATCH',body:JSON.stringify({name:$('editTaskName').value.trim(),description:$('editTaskDescription').value,owner:$('editTaskOwner').value.trim(),priority:$('editTaskPriority').value,effort:+$('editTaskEffort').value,due_date:$('editTaskDue').value||null,status:$('editTaskStatus').value})});$('taskModal').classList.add('hidden');await loadAll();toast('Task saved')}catch(e){toast(e.message)}});

function renderTeam(s){
  $('teamGrid').innerHTML=s.team.length?s.team.map(m=>`<div class="card"><span class="pill blue">${esc(m.role)}</span><h3>${esc(m.name)}</h3><p>${esc(m.skills)}</p><p>Availability <b>${m.availability}%</b></p><p>Workload <b>${m.workload}%</b></p><p>Daily rate <b>₹${Number(m.daily_rate||0).toLocaleString('en-IN')}</b></p><div class="bar"><span style="width:${Math.min(100,m.workload)}%"></span></div><div class="card-actions"><button class="secondary member-edit" data-id="${m.id}">Edit</button><button class="ghost member-delete" data-id="${m.id}">Remove</button></div></div>`).join(''):'<div class="panel">No team members. Add the people who will execute this project.</div>';
  document.querySelectorAll('.member-edit').forEach(e=>e.addEventListener('click',()=>editMember(+e.dataset.id)));document.querySelectorAll('.member-delete').forEach(e=>e.addEventListener('click',()=>deleteMember(+e.dataset.id)));
}
async function editMember(id){const m=currentState.team.find(x=>x.id===id);if(!m)return;const n=prompt('Name',m.name);if(n===null)return;const r=prompt('Role',m.role);if(r===null)return;const sk=prompt('Skills',m.skills);if(sk===null)return;const av=prompt('Availability %',m.availability);if(av===null)return;const wl=prompt('Current workload %',m.workload);if(wl===null)return;const rate=prompt('Daily cost ₹',m.daily_rate||2000);if(rate===null)return;try{await api(`/api/team/${id}`,{method:'PATCH',body:JSON.stringify({name:n,role:r,skills:sk,availability:+av,workload:+wl,daily_rate:+rate})});await loadAll();toast('Team member updated')}catch(e){toast(e.message)}}
async function deleteMember(id){if(!confirm('Remove this team member?'))return;try{await api(`/api/team/${id}`,{method:'DELETE'});await loadAll();toast('Team member removed')}catch(e){toast(e.message)}}
$('addMember').addEventListener('click',async()=>{if(!requireProject())return;const name=prompt('Member name');if(!name)return;const role=prompt('Role','TEAM MEMBER')||'TEAM MEMBER';const skills=prompt('Skills','Python, SQL')||'General';const availability=+(prompt('Availability %','80')||80);const daily_rate=+(prompt('Daily cost ₹','2000')||2000);try{await api('/api/team',{method:'POST',body:JSON.stringify({project_id:currentProjectId,name,role,skills,availability,daily_rate,workload:0})});await loadAll();toast('Team member added')}catch(e){toast(e.message)}});
async function recommendTeam(taskId){try{const d=await api('/api/team/recommend',{method:'POST',body:JSON.stringify({project_id:currentProjectId,task_id:taskId})});const m=d.recommended_member;$('recommendResult').innerHTML=`<div class="panel"><div class="eyebrow">AI TEAM RECOMMENDATION</div><h2>${esc(m.name)} · ${m.match_score}% match</h2><p>${esc(m.reason)}</p><p class="muted">Estimated workload after assignment: ${m.workload_after}%</p><div>${(d.alternatives||[]).map(x=>`<div class="list-item"><b>${esc(x.name)} · ${x.match_score}%</b><span class="muted">${esc(x.reason)}</span></div>`).join('')}</div></div>`;toast(`Recommended ${m.name}`);tab('team')}catch(e){toast(e.message)}}

function renderRisks(s){$('riskGrid').innerHTML=s.risks.map(r=>`<div class="card risk-${r.severity==='LOW'?'low':r.severity==='MEDIUM'?'medium':'high'}"><span class="pill">${esc(r.severity)}</span><h3>${esc(r.name)} <span class="muted">${r.score}/10</span></h3><p><b>WHY:</b> ${esc(r.explanation)}</p><p><b>EVIDENCE:</b> Probability ${r.probability}% · Impact ${r.impact}%</p><p><b>ACTION:</b> ${esc(r.mitigation)}</p></div>`).join('')}
async function loadActivity(s){const d=await api(`/api/activity/${currentProjectId}`);$('activity').innerHTML=d.activity?.length?d.activity.slice(0,6).map(x=>`<div class="list-item"><b>${esc(x.title)}</b><p class="muted">${esc(x.detail)}</p></div>`).join(''):'<p class="muted">No activity yet.</p>'; $('history').innerHTML=d.activity?.map(x=>`<div class="list-item"><b>${esc(x.title)}</b><p class="muted">${esc(x.detail)} · ${esc(x.created_at)}</p></div>`).join('')||''}
async function loadNotifications(){try{const d=await api(`/api/notifications/${currentProjectId}`);$('notifications').innerHTML=d.notifications.length?d.notifications.map(n=>`<div class="list-item ${n.read?'':'notification-unread'}"><b>${esc(n.title)}</b><p>${esc(n.message)}</p><small class="muted">${esc(n.type)} · ${esc(n.created_at)}</small>${n.read?'':' <button class="ghost notification-read" data-id="'+n.id+'">Mark read</button>'}</div>`).join(''):'<p class="muted">No active notifications.</p>';document.querySelectorAll('.notification-read').forEach(b=>b.addEventListener('click',async()=>{await api(`/api/notifications/${b.dataset.id}/read`,{method:'PATCH',body:'{}'});await loadNotifications();await loadAll() }))}catch(e){}}
$('readAllNotifications').addEventListener('click',async()=>{if(!requireProject())return;try{await api(`/api/notifications/${currentProjectId}/read-all`,{method:'POST',body:'{}'});await loadAll();toast('Notifications marked read')}catch(e){toast(e.message)}});
function renderMonitor(s){$('monitorGrid').innerHTML=`<div class="signal-grid"><div class="signal"><b>HEALTH</b><div class="value">${s.health}%</div><div class="bar"><span style="width:${s.health}%"></span></div></div><div class="signal"><b>PROGRESS</b><div class="value">${s.progress}%</div><div class="bar"><span style="width:${s.progress}%"></span></div></div><div class="signal"><b>UTILIZATION</b><div class="value">${Math.round(s.utilization)}%</div><div class="bar"><span style="width:${Math.min(100,s.utilization)}%"></span></div></div></div>`}
function renderSignals(s){$('sigHealth').textContent=s.health+'%';$('sigRisk').textContent=s.high_risks+' high';$('sigWork').textContent=Math.round(s.team.length?s.team.reduce((a,x)=>a+x.workload,0)/s.team.length:0)+'%';}
async function loadAnalytics(){try{const d=await api(`/api/analytics/${currentProjectId}`);const rows=d.snapshots||[];$('analyticsPanel').innerHTML=`<div class="panel"><h2>Historical intelligence</h2><p class="muted">Snapshots are stored whenever project intelligence materially changes. ${rows.length} snapshot(s).</p><div class="analytics-grid">${rows.slice(-12).map(x=>`<div class="analytics-point"><b>${x.health}%</b><span>Health</span><small>${new Date(x.created_at).toLocaleTimeString()}</small><div class="bar"><span style="width:${x.health}%"></span></div></div>`).join('')||'<p class="muted">Interact with the project to build historical snapshots.</p>'}</div></div>`}catch(e){}}

$('refreshDash').addEventListener('click',loadAll);
$('analyzeBtn').addEventListener('click',async()=>{const btn=$('analyzeBtn');btn.disabled=true;btn.textContent='Analyzing…';try{const d=await api('/api/analyze',{method:'POST',body:JSON.stringify({description:$('problem').value})});const a=d.analysis;$('analysisResult').innerHTML=`<div class="analysis-head">${[['Deadline',a.deadline_days+' days'],['Team',a.team_size],['Health',a.health+'%'],['Effort',a.total_effort]].map(x=>`<div class="analysis-card"><strong>${esc(x[1])}</strong><small>${esc(x[0])}</small></div>`).join('')}</div><div class="result-grid"><div class="panel"><h2>Generated work · ${a.tasks.length} tasks</h2>${a.tasks.map(t=>`<div class="list-item"><b>${esc(t.task_key)} · ${esc(t.name)}</b><p class="muted">${esc(t.description)} · ${t.effort} person-days · ${esc(t.risk_level)} · ${esc(t.owner)}</p></div>`).join('')}</div><div class="panel"><h2>Risks + actions</h2>${a.risks.map(r=>`<div class="list-item"><b>${esc(r.name)} — ${esc(r.severity)} ${r.score}/10</b><p>${esc(r.explanation)}</p><small class="muted">${esc(r.mitigation)}</small></div>`).join('')}</div></div><div class="panel"><h2>Critical path</h2><p>${esc((a.critical_path||[]).join(' → '))}</p><p class="muted">Duration ${a.critical_path_duration} days · dependency cycle ${a.dependency_cycle?'YES':'NO'}</p><button class="primary" id="createAnalysisProject">Create this as a project →</button></div>`;window.lastAnalysis=a;$('createAnalysisProject').addEventListener('click',createFromAnalysis);toast(`Analysis complete · ${a.tasks.length} project-specific tasks`)}catch(e){toast(e.message)}finally{btn.disabled=false;btn.textContent='Analyze →'}});
async function createFromAnalysis(){try{if(!isLoggedIn()){$('loginModal').classList.remove('hidden');return}const d=await api('/api/projects',{method:'POST',body:JSON.stringify({name:window.lastAnalysis.project_name,description:$('problem').value})});currentProjectId=d.project.id;await loadProjects();await loadAll();tab('dashboard');toast('Project created')}catch(e){toast(e.message)}}
$('wfBtn').addEventListener('click',async()=>{try{const d=await api('/api/what-if',{method:'POST',body:JSON.stringify({project_id:currentProjectId,team:+$('wfTeam').value,deadline:+$('wfDeadline').value,budget:+$('wfBudget').value,scope_factor:+$('wfScope').value})});$('wfResult').innerHTML=`<div class="panel"><div class="analysis-head">${[['Verdict',d.verdict],['Health',d.health+'%'],['Health Δ',(d.health_delta>=0?'+':'')+d.health_delta],['Capacity',d.capacity],['Utilization',d.team_utilization+'%'],['Cost','₹'+Number(d.estimated_cost||0).toLocaleString('en-IN')]].map(x=>`<div class="analysis-card"><strong>${esc(x[1])}</strong><small>${esc(x[0])}</small></div>`).join('')}</div><h2>Decision explanation</h2><p><b>Recommendation:</b> ${esc(d.recommendation)}</p><p class="muted">Effort ${d.estimated_effort} · labor ₹${Number(d.labor_cost||0).toLocaleString('en-IN')} · budget feasible: ${d.budget_feasible?'YES':'NO'} · deadline feasible: ${d.deadline_feasible?'YES':'NO'} · slack ${d.critical_path_slack} days.</p><h3>Why?</h3><ul>${(d.explanation||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul><h3>Task cost breakdown</h3>${(d.task_costs||[]).slice(0,8).map(t=>`<div class="list-item"><b>${esc(t.task_key)} · ${esc(t.name)}</b><span>₹${Number(t.labor_cost||0).toLocaleString('en-IN')}</span></div>`).join('')}<h3>Scenario risks</h3>${(d.risks||[]).slice(0,5).map(r=>`<div class="list-item"><b>${esc(r.name)} — ${esc(r.severity)} ${r.score}/10</b><p>${esc(r.explanation)}</p><small class="muted">Action: ${esc(r.mitigation)}</small></div>`).join('')}</div>`;await loadAll();toast('Scenario calculated with cost + capacity + risk')}catch(e){toast(e.message)}});
$('chatBtn').addEventListener('click',async()=>{const msg=$('chatInput').value.trim();if(!msg)return;appendMsg('user',msg);$('chatInput').value='';try{const d=await api('/api/chat',{method:'POST',body:JSON.stringify({message:msg,project_id:currentProjectId})});appendMsg('assistant',d.answer)}catch(e){toast(e.message)}});
function appendMsg(role,text){const wrap=document.createElement('div');wrap.className=`msg ${role}`;const b=document.createElement('b');b.textContent=role==='user'?'YOU':'NEXUS-X';const d=document.createElement('div');d.textContent=text;wrap.append(b,d);$('chatLog').appendChild(wrap);$('chatLog').scrollTop=$('chatLog').scrollHeight}
$('newProject').addEventListener('click',async()=>{if(!isLoggedIn()){$('loginModal').classList.remove('hidden');return}const name=prompt('Project name');if(!name)return;const desc=prompt('Describe the project in plain language');if(!desc)return;try{const d=await api('/api/projects',{method:'POST',body:JSON.stringify({name,description:desc})});currentProjectId=d.project.id;await loadProjects();await loadAll();tab('dashboard')}catch(e){toast(e.message)}});
$('pdfBtn').addEventListener('click',()=>{if(currentProjectId)window.location=`/api/export/report.pdf/${currentProjectId}`;else toast('Open a project first')});$('csvBtn').addEventListener('click',()=>{if(currentProjectId)window.location=`/api/export/tasks.csv/${currentProjectId}`;else toast('Open a project first')});
$('buildBtn').addEventListener('click',async()=>{try{if(!isLoggedIn()){$('loginModal').classList.remove('hidden');return}const r=await fetch('/api/generate-project.zip',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({prompt:$('buildPrompt').value,project_id:currentProjectId||0})});if(!r.ok){const d=await r.json();throw new Error(d.error||'Generation failed')}const blob=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='nexus-x-generated-complete.zip';a.click();URL.revokeObjectURL(a.href);toast('Complete NEXUS-X project generated')}catch(e){toast(e.message)}});

(async()=>{try{const d=await api('/api/me');if(d.user){csrf=d.csrf||'';setUser(d.user);const saved=localStorage.getItem('nexusProject');if(saved)currentProjectId=+saved;await loadProjects();if(currentProjectId)await loadAll();else await loadDemo();poller=setInterval(()=>{if(currentProjectId)loadAll()},15000)}else{await loadProjects()}}catch(e){}})();
