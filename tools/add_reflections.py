from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
if 'id="reflections"' in s:
    print('Reflexões já instaladas')
    raise SystemExit(0)

css='''
/* === Reflexões e decisões === */
.reflection-hero{background:linear-gradient(145deg,#143d59,#2d7484);color:#fff;border:none}.reflection-hero h2{color:#fff}.reflection-hero p{color:#d9e8ed;font-size:12px;line-height:1.55;margin:7px 0 0}.reflection-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.reflection-card{position:relative;overflow:hidden}.reflection-card .r-icon{font-size:28px}.reflection-card .r-label{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:800;margin-top:9px}.reflection-card .r-value{font-size:22px;font-weight:900;margin-top:5px}.reflection-card .r-text{font-size:11px;line-height:1.45;color:var(--muted);margin-top:6px}.goal-layout{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);gap:16px}.goal-form{display:grid;grid-template-columns:1fr 1fr;gap:11px}.goal-form .full{grid-column:1/-1}.goal-result{border-radius:16px;padding:18px;background:#f6f9f8;border:1px solid var(--line)}.goal-result .hero-number{font-size:31px;font-weight:900;margin:7px 0}.scenario-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}.scenario{padding:11px;border:1px solid var(--line);border-radius:11px;background:#fff;text-align:center}.scenario b{display:block;font-size:13px}.scenario span{font-size:9px;color:var(--muted)}.reflection-list{display:grid;gap:9px}.reflection-tip{padding:12px 13px;border-radius:12px;background:#f8faf9;border-left:4px solid var(--teal);font-size:11px;line-height:1.45}.reflection-tip.warn{border-left-color:var(--coral)}.reflection-tip.good{border-left-color:var(--ok)}.confidence{display:inline-block;padding:4px 7px;border-radius:99px;font-size:9px;font-weight:800;background:#fff3dc;color:#966200;margin-top:7px}
@media(max-width:920px){.reflection-grid{grid-template-columns:1fr 1fr}.goal-layout{grid-template-columns:1fr}}
@media(max-width:620px){.reflection-grid{grid-template-columns:1fr}.goal-form{grid-template-columns:1fr}.goal-form .full{grid-column:auto}.scenario-grid{grid-template-columns:1fr 1fr}}
'''
s=s.replace('</style>',css+'\n</style>',1)
s=s.replace('<button data-page="payments">✓ &nbsp;Pagamentos</button><button data-page="investments">◆ &nbsp;Investimentos</button>','<button data-page="payments">✓ &nbsp;Pagamentos</button><button data-page="reflections">✦ &nbsp;Reflexões</button><button data-page="investments">◆ &nbsp;Investimentos</button>',1)
s=s.replace('<button data-page="payments">Pagto.</button><button data-page="investments">Investir</button>','<button data-page="payments">Pagto.</button><button data-page="reflections">Refletir</button><button data-page="investments">Investir</button>',1)
s=s.replace('grid-template-columns:repeat(7,1fr)!important','grid-template-columns:repeat(8,1fr)!important',1)

section='''
<section id="reflections" class="page">
  <div class="section card reflection-hero">
    <div class="section-head"><h2>Reflexões financeiras</h2><span style="color:#d9e8ed">dados → decisões</span></div>
    <p>Use o que já está planejado para decidir quando investir, viajar ou assumir uma meta maior. As respostas mudam automaticamente conforme seus meses são atualizados.</p>
  </div>
  <div class="reflection-grid section" id="reflectionOpportunities"></div>
  <div class="goal-layout section">
    <div class="card">
      <div class="section-head"><h2>Simulador de meta</h2><span>planeje antes de gastar</span></div>
      <div class="goal-form">
        <div class="field full"><label>Objetivo</label><input id="goalName" value="Viagem"></div>
        <div class="field"><label>Mês da meta</label><select id="goalMonth"></select></div>
        <div class="field"><label>Quanto pretende gastar</label><input id="goalCost" type="number" step="100" value="5000"></div>
        <div class="field"><label>Quanto quer sobrar depois</label><input id="goalLeftover" type="number" step="100" value="5000"></div>
        <div class="field"><label>Margem de segurança extra</label><input id="goalSafety" type="number" step="100" value="1500"></div>
        <div class="field full"><button class="btn primary" id="simulateGoal">Calcular minha meta</button></div>
      </div>
    </div>
    <div class="goal-result" id="goalResult"></div>
  </div>
  <div class="dashboard-row section">
    <div class="card"><div class="section-head"><h2>Melhores meses</h2><span>comparação das projeções</span></div><div id="bestMonths" class="reflection-list"></div></div>
    <div class="card"><div class="section-head"><h2>O que fazer agora?</h2><span>recomendações automáticas</span></div><div id="reflectionActions" class="reflection-list"></div></div>
  </div>
</section>
'''
s=s.replace('<section id="investments" class="page">',section+'\n<section id="investments" class="page">',1)

js='''
function monthIndexObj(m){return Number(m.year||0)*12+Number(m.month||0)}
function futureMonths(){let cur=monthObj(),ci=monthIndexObj(cur);return (S.months||[]).filter(m=>monthIndexObj(m)>=ci).sort((a,b)=>monthIndexObj(a)-monthIndexObj(b))}
function catBy(m,name){return (m.categories||[]).find(c=>c.name===name)||{used:0,budget:0,available:0}}
function projectedBalance(m){return Number(m.summary?.saldoProjetado??((m.summary?.receitaLancada||0)-(m.summary?.comprometido||0)))||0}
function investmentPlan(m){return Number(catBy(m,'Objetivos e investimentos').budget||catBy(m,'Objetivos e investimentos').used||0)}
function dataConfidence(m){let tx=(m.transactions||[]).filter(t=>t.tipo==='Despesa');let vars=tx.filter(t=>t.natureza==='Variável'&&!String(t.observacao||'').toLowerCase().includes('projet')).length;if(m.year===2026&&m.month<=9)return'Alta';return vars>=8?'Média':'Baixa'}
function renderReflections(){
 let fut=futureMonths();if(!fut.length)return;
 let maxInv=[...fut].sort((a,b)=>investmentPlan(b)-investmentPlan(a))[0],bestCash=[...fut].sort((a,b)=>projectedBalance(b)-projectedBalance(a))[0];
 let safest=[...fut].filter(m=>dataConfidence(m)!=='Baixa').sort((a,b)=>projectedBalance(b)-projectedBalance(a))[0]||bestCash;
 $('#reflectionOpportunities').innerHTML=`<div class="card reflection-card"><div class="r-icon">📈</div><div class="r-label">Maior investimento planejado</div><div class="r-value">${maxInv.label}</div><div class="r-text">${money(investmentPlan(maxInv))} previstos para Objetivos e investimentos.</div></div><div class="card reflection-card"><div class="r-icon">✈️</div><div class="r-label">Maior folga projetada</div><div class="r-value">${bestCash.label}</div><div class="r-text">Saldo projetado de ${money(projectedBalance(bestCash))} antes de uma nova meta.</div><span class="confidence">Confiança ${dataConfidence(bestCash).toLowerCase()}</span></div><div class="card reflection-card"><div class="r-icon">🛡️</div><div class="r-label">Melhor combinação folga + confiança</div><div class="r-value">${safest.label}</div><div class="r-text">Hoje é o mês mais confortável entre os que possuem projeção mais confiável.</div></div>`;
 $('#goalMonth').innerHTML=fut.map(m=>`<option value="${m.label}" ${m.label==='Dez-26'?'selected':''}>${m.label}</option>`).join('');
 let ranked=[...fut].sort((a,b)=>projectedBalance(b)-projectedBalance(a)).slice(0,4);
 $('#bestMonths').innerHTML=ranked.map((m,i)=>`<div class="reflection-tip ${i===0?'good':''}"><b>${i===0?'🥇 ':''}${m.label}</b> — saldo projetado ${money(projectedBalance(m))}. Investimento planejado ${money(investmentPlan(m))}. <span class="confidence">confiança ${dataConfidence(m).toLowerCase()}</span></div>`).join('');
 let cur=monthObj(),overs=(cur.categories||[]).filter(c=>c.used>c.budget&&c.budget>0).sort((a,b)=>(b.used-b.budget)-(a.used-a.budget)).slice(0,3);
 let tips=[];if(overs.length)tips.push(`<div class="reflection-tip warn"><b>Reduza os maiores desvios atuais</b><br>${overs.map(c=>`${c.name}: ${money(c.used-c.budget)} acima`).join(' • ')}</div>`);
 tips.push(`<div class="reflection-tip"><b>Proteja metas antes do gasto</b><br>Quando decidir viajar ou comprar algo maior, reserve o valor mensalmente antes de considerar a sobra como disponível.</div>`);
 tips.push(`<div class="reflection-tip"><b>Projeções futuras exigem cautela</b><br>Meses distantes podem não conter todos os gastos variáveis. Use a margem de segurança do simulador.</div>`);
 $('#reflectionActions').innerHTML=tips.join('');simulateGoal();
}
function simulateGoal(){
 let label=$('#goalMonth').value,m=(S.months||[]).find(x=>x.label===label);if(!m)return;
 let name=$('#goalName').value||'Meta',cost=Number($('#goalCost').value||0),left=Number($('#goalLeftover').value||0),safety=Number($('#goalSafety').value||0),bal=projectedBalance(m);
 let need=cost+left+safety,gap=Math.max(0,need-bal),cur=monthObj(),monthsTo=Math.max(1,monthIndexObj(m)-monthIndexObj(cur)),per=gap/monthsTo;
 let maxSafe=Math.max(0,bal-left-safety),withoutSafety=Math.max(0,bal-left),scenarios=[3000,5000,7000,10000].map(v=>({v,left:bal-v}));
 $('#goalResult').innerHTML=`<div class="r-label">${name} em ${m.label}</div><div class="hero-number ${gap>0?'bad':'good'}">${gap>0?money(gap)+' faltando':'Meta viável'}</div><div class="r-text">Saldo projetado antes da meta: <b>${money(bal)}</b>.<br>Para gastar ${money(cost)}, terminar com ${money(left)} e ainda preservar ${money(safety)} de segurança, você precisa de ${money(need)}.</div>${gap>0?`<div class="reflection-tip warn" style="margin-top:12px"><b>Plano até ${m.label}</b><br>Reserve aproximadamente <b>${money(per)} por mês</b> durante ${monthsTo} mês(es).</div>`:`<div class="reflection-tip good" style="margin-top:12px"><b>Você já está dentro da projeção.</b><br>Orçamento recomendado para a meta: até <b>${money(maxSafe)}</b>. Sem margem extra, o teto seria ${money(withoutSafety)}.</div>`}<div class="scenario-grid">${scenarios.map(x=>`<div class="scenario"><b>${money(x.v)}</b><span>sobra ${money(x.left)}</span></div>`).join('')}</div><span class="confidence">Confiança ${dataConfidence(m).toLowerCase()}</span>`;
}
'''
s=s.replace('function renderSettings(){',js+'\nfunction renderSettings(){',1)
s=s.replace('function renderAll(){renderDashboard();renderMonth();renderTransactions();renderPayments();renderInvestments();renderSettings()}','function renderAll(){renderDashboard();renderMonth();renderTransactions();renderPayments();renderReflections();renderInvestments();renderSettings()}',1)
s=s.replace("payments:['Pagamentos','Acompanhe cartões e contas gerais sem duplicar as despesas.'],investments:","payments:['Pagamentos','Acompanhe cartões e contas gerais sem duplicar as despesas.'],reflections:['Reflexões','Transforme projeções em decisões, metas e cenários.'],investments:",1)
s=s.replace("$('#saveInvest').onclick=async()=>","$('#simulateGoal').onclick=simulateGoal;$('#goalMonth').onchange=simulateGoal;$('#goalCost').oninput=simulateGoal;$('#goalLeftover').oninput=simulateGoal;$('#goalSafety').oninput=simulateGoal;$('#saveInvest').onclick=async()=>",1)

p.write_text(s,encoding='utf-8')
print('Reflexões instaladas')
