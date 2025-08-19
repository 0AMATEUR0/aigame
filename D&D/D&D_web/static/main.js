// static/main.js
async function api(path, method='GET', body=null){
  const opts={method, headers:{}};
  if(body){ opts.headers['Content-Type']='application/json'; opts.body=JSON.stringify(body); }
  const res = await fetch(path, opts);
  return await res.json();
}

function typeText(el, text, speed=16){
  el.innerText=''; let i=0;
  (function step(){ if(i<text.length){ el.innerText+=text[i++]; setTimeout(step, speed);} })();
}

async function loadScene(){
  const data = await api('/api/scene');
  renderScene(data.scene, data.player, data.turn, data.history);
}

function renderScene(scene, player, turn, history){
  const sceneEl=document.getElementById('sceneText');
  const choicesEl=document.getElementById('choices');
  const narrationEl=document.getElementById('narration');
  const logEl=document.getElementById('log');

  if(!scene || !scene.scene){
    sceneEl.innerText = "当前场景无效（检查后端日志或 API Key）。";
    choicesEl.innerHTML='';
    return;
  }

  typeText(sceneEl, scene.scene);
  narrationEl.innerText='';
  choicesEl.innerHTML='';
  (scene.choices || []).forEach((ch, idx)=>{
    const btn=document.createElement('button');
    btn.innerText = ch.action + (ch.hint ? ` — ${ch.hint}` : '');
    btn.onclick = ()=> onChoose(idx);
    choicesEl.appendChild(btn);
  });

  document.getElementById('playerName').value = player.name || '侠客';
  logEl.innerHTML = '';
  (history || []).slice(-30).reverse().forEach(h=>{
    const d=document.createElement('div');
    d.innerText = `回合${h ? h.split && typeof h === 'string' ? '' : '' : ''}${h || ''}`;
    // h can be strings (log_entry), so print as-is
    d.innerText = h;
    logEl.appendChild(d);
  });
}

async function onChoose(choice_idx){
  // disable buttons
  const btns=document.querySelectorAll('#choices button'); btns.forEach(b=>b.disabled=true);
  const resp = await api('/api/choose','POST',{choice_idx});
  if(resp.error){ alert('错误：'+resp.error); btns.forEach(b=>b.disabled=false); return; }
  const narr = (resp.resolution && resp.resolution.narration) ? resp.resolution.narration : `d20=${resp.roll} → ${resp.outcome}`;
  const narrationEl=document.getElementById('narration');
  typeText(narrationEl, narr, 12);
  // prepend log
  const logEl=document.getElementById('log');
  const e=document.createElement('div');
  e.innerText = `回合 ${resp.turn-1}｜掷骰 ${resp.roll} (${resp.mode}) → ${resp.outcome} ｜ ${resp.resolution.log_entry||''}`;
  logEl.prepend(e);
  // after short delay, render next scene
  setTimeout(()=>{
    renderScene(resp.next_scene, resp.player, resp.turn, resp.history);
    btns.forEach(b=>b.disabled=false);
  }, 900);
}

document.getElementById('btnSetName').onclick = async ()=>{
  const name=document.getElementById('playerName').value || '侠客';
  await api('/api/set_name','POST',{name});
  loadScene();
};
document.getElementById('btnReset').onclick = async ()=>{
  if(!confirm('确定重置游戏？')) return;
  await api('/api/reset','POST',{});
  loadScene();
};

window.onload = ()=>{ loadScene(); };
