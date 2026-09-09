from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Mantém a proteção contra meses nulos
old_guard = "s.months=(s.months||[]).map(m=>{m.transactions=m.transactions||[];m.categories=m.categories||[];m.summary=m.summary||{};return m});"
new_guard = "s.months=(s.months||[]).filter(m=>m&&typeof m==='object').map(m=>{m.transactions=Array.isArray(m.transactions)?m.transactions:[];m.categories=Array.isArray(m.categories)?m.categories:[];m.summary=m.summary&&typeof m.summary==='object'?m.summary:{};return m});"
if old_guard in s:
    s = s.replace(old_guard, new_guard, 1)

# Estilos do filtro e cards clicáveis
if '/* === filtro pagamentos === */' not in s:
    css = '''\n/* === filtro pagamentos === */\n.payment-summary-card{cursor:pointer;transition:transform .15s ease,box-shadow .15s ease}.payment-summary-card:hover{transform:translateY(-1px)}.payment-filter-bar{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 14px;background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}.payment-filter-bar .filter-label{font-size:11px;color:var(--muted)}.payment-filter-bar select{min-width:190px;padding:8px 10px;font-size:11px}@media(max-width:620px){.payment-filter-bar{align-items:flex-start;flex-direction:column}.payment-filter-bar select{width:100%}}\n'''
    s = s.replace('</style>', css + '</style>', 1)

# Inclui o filtro visual antes da tabela de contas gerais
needle = '<div class="payments-grid section" id="creditCardPayments"></div><div class="section card"><div class="section-head"><h2>Contas gerais e receitas</h2>'
replace = '<div class="payments-grid section" id="creditCardPayments"></div><div class="payment-filter-bar section"><div><b>Filtrar pagamentos</b><div class="filter-label">Veja rapidamente apenas o que ainda falta pagar ou o que já foi quitado.</div></div><select id="paymentFilter" onchange="setPaymentFilter(this.value)"><option value="all">Todos</option><option value="pending">Ainda não pagos</option><option value="paid">Pagos</option><option value="partial">Parciais</option><option value="receipts">Recebimentos</option></select></div><div class="section card"><div class="section-head"><h2>Contas gerais e receitas</h2>'
if 'id="paymentFilter"' not in s:
    if needle not in s:
        raise SystemExit('Área do filtro de pagamentos não encontrada')
    s = s.replace(needle, replace, 1)

# Atualização visual imediata ao dar baixa ou alterar valor final
s = s.replace("async function setPaymentStatus(label,name,status){S.settings=S.settings||{};S.settings.paymentStatuses=S.settings.paymentStatuses||{};S.settings.paymentStatuses[paymentKey(label,name)]=status;await save();renderPayments()}",
              "async function setPaymentStatus(label,name,status){S.settings=S.settings||{};S.settings.paymentStatuses=S.settings.paymentStatuses||{};S.settings.paymentStatuses[paymentKey(label,name)]=status;renderPayments();await save()}")
s = s.replace("async function setPaymentActual(label,name,value){S.settings=S.settings||{};S.settings.paymentActuals=S.settings.paymentActuals||{};let key=paymentKey(label,name);if(value==='')delete S.settings.paymentActuals[key];else S.settings.paymentActuals[key]=Number(value);await save();renderPayments()}",
              "async function setPaymentActual(label,name,value){S.settings=S.settings||{};S.settings.paymentActuals=S.settings.paymentActuals||{};let key=paymentKey(label,name);if(value==='')delete S.settings.paymentActuals[key];else S.settings.paymentActuals[key]=Number(value);renderPayments();await save()}")

replacement = r'''let paymentViewFilter='all';
function setPaymentFilter(v){paymentViewFilter=v||'all';renderPayments()}window.setPaymentFilter=setPaymentFilter;
function paymentMatchesFilter(st,type){if(paymentViewFilter==='all')return true;if(paymentViewFilter==='receipts')return type==='Receita';if(type!=='Despesa')return false;if(paymentViewFilter==='paid')return st==='Pago/Recebido'||st==='Pago';if(paymentViewFilter==='partial')return st==='Parcial';if(paymentViewFilter==='pending')return !(st==='Pago/Recebido'||st==='Pago');return true}
function renderPayments(){
 let m=monthObj();if(!m)return;let all=monthTx(m).filter(t=>t.status!=='Cancelado'),tx=all.filter(t=>t.type==='Despesa'),label=m.label||m.key;
 let groups={Santander:0,Nubank:0,'Itaú':0};tx.forEach(t=>{let issuer=cardIssuer(t.account);if(issuer)groups[issuer]+=t.value});
 if(label==='Set-26'){groups.Santander=12162.53;groups.Nubank=1121.54}
 let due={Santander:label==='Set-26'?'04/09/2026':'—',Nubank:label==='Set-26'?'11/09/2026':'—','Itaú':'—'};
 let defaults={Santander:label==='Set-26'?'Pago/Recebido':'Aguardando',Nubank:'Aguardando','Itaú':'Aguardando'};
 let general=all.filter(t=>!(t.type==='Despesa'&&cardIssuer(t.account))&&!['Previstos'].includes(t.account));
 let paidTotal=0,pendingTotal=0,totalToPay=0;
 Object.entries(groups).forEach(([name,value])=>{
   if(value<=0)return;
   let key='card:'+name,st=getPaymentStatus(label,key,defaults[name]),actual=getPaymentActual(label,key),paid=0;
   if(st==='Pago/Recebido'||st==='Pago')paid=actual!==''?Number(actual):Number(value);
   else if(st==='Parcial')paid=actual!==''?Math.min(Number(value),Number(actual)):0;
   totalToPay+=Number(value);paidTotal+=Math.max(0,paid);pendingTotal+=Math.max(0,Number(value)-paid);
 });
 general.forEach((t,i)=>{
   if(t.type!=='Despesa')return;
   let key=`geral:${t.type}:${t.description}:${t.date}:${i}`,def=t.status==='Pago'||t.status==='Pago/Recebido'?'Pago/Recebido':'Aguardando',st=getPaymentStatus(label,key,def),actual=getPaymentActual(label,key),paid=0;
   if(st==='Pago/Recebido'||st==='Pago')paid=actual!==''?Number(actual):Number(t.value);
   else if(st==='Parcial')paid=actual!==''?Math.min(Number(t.value),Number(actual)):0;
   totalToPay+=Number(t.value);paidTotal+=Math.max(0,paid);pendingTotal+=Math.max(0,Number(t.value)-paid);
 });
 let paidPct=totalToPay?Math.min(1,paidTotal/totalToPay):0;
 $('#paymentSummaryCards').innerHTML=`<div class="payment-summary-card paid" onclick="setPaymentFilter('paid')" title="Clique para ver apenas os pagos"><div class="ps-label">✓ Pago no mês</div><div class="ps-value">${money(paidTotal)}</div><div class="ps-note">${pct(paidPct)} do total de despesas previstas já foi quitado.</div><div class="payment-summary-progress"><i style="width:${paidPct*100}%"></i></div></div><div class="payment-summary-card pending" onclick="setPaymentFilter('pending')" title="Clique para ver apenas o que falta pagar"><div class="ps-label">⏳ Ainda não pago</div><div class="ps-value">${money(pendingTotal)}</div><div class="ps-note">Valor que ainda falta quitar entre cartões e contas gerais deste mês. Clique para filtrar.</div></div>`;
 let pf=$('#paymentFilter');if(pf)pf.value=paymentViewFilter;
 $('#creditCardPayments').innerHTML=Object.entries(groups).filter(([name,value])=>{if(!(value>0||label==='Set-26'))return false;let st=getPaymentStatus(label,'card:'+name,defaults[name]);return paymentMatchesFilter(st,'Despesa')}).map(([name,value])=>{let key='card:'+name,st=getPaymentStatus(label,key,defaults[name]),actual=getPaymentActual(label,key);return `<div class="payment-card ${paymentClass(st)}"><div class="pay-head"><div><h3>${name}</h3><div class="payment-meta">Fatura do mês</div></div>${pill(st)}</div><div class="payment-meta">Previsto</div><div class="pay-value">${money(value)}</div><div class="payment-meta">Valor final pago</div><input class="inline-input" style="width:100%;margin:6px 0 10px" type="number" step="0.01" value="${actual}" placeholder="0,00" onchange='setPaymentActual(${JSON.stringify(label)},${JSON.stringify(key)},this.value)'><div class="payment-meta">Vencimento: <b>${due[name]}</b><br>O pagamento da fatura não entra novamente como despesa.</div><select style="margin-top:10px;width:100%" onchange='setPaymentStatus(${JSON.stringify(label)},${JSON.stringify(key)},this.value)'>${paymentStatusOptions(st)}</select></div>`}).join('') || (paymentViewFilter==='receipts'?'':'<div class="empty">Nenhuma fatura neste filtro.</div>');
 let rows=general.map((t,i)=>{let key=`geral:${t.type}:${t.description}:${t.date}:${i}`,def=t.status==='Pago'||t.status==='Pago/Recebido'?'Pago/Recebido':'Aguardando',st=getPaymentStatus(label,key,def),actual=getPaymentActual(label,key);return{t,i,key,st,actual}}).filter(x=>paymentMatchesFilter(x.st,x.t.type));
 $('#generalPaymentsRows').innerHTML=rows.sort((a,b)=>String(a.t.date).localeCompare(String(b.t.date))).map(x=>{let t=x.t,key=x.key,st=x.st,actual=x.actual,finalLabel=t.type==='Receita'?'Recebido':'Pago';return `<tr><td>${t.type}</td><td>${t.account||'Conta geral'}</td><td>${fmtDate(t.date)}</td><td>${t.description}</td><td class="money">${money(t.value)}</td><td><input class="inline-input" type="number" step="0.01" value="${actual}" placeholder="${finalLabel}" onchange='setPaymentActual(${JSON.stringify(label)},${JSON.stringify(key)},this.value)'></td><td><select onchange='setPaymentStatus(${JSON.stringify(label)},${JSON.stringify(key)},this.value)'>${paymentStatusOptions(st)}</select></td></tr>`}).join('')||'<tr><td colspan="7" class="empty">Nenhum item encontrado neste filtro.</td></tr>'
}

function monthIndexObj'''

pattern = r"(?:let paymentViewFilter='all';\nfunction setPaymentFilter.*?\n)?function renderPayments\(\)\{.*?\n\}\n\nfunction monthIndexObj"
s2,n = re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit(f'Função renderPayments não encontrada: {n}')
s=s2

p.write_text(s,encoding='utf-8')
print('Pagamentos com atualização imediata e filtro aplicados')
