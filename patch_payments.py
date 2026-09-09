from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old_html = '''<section id="payments" class="page"><div class="section-head"><div><h2 style="margin:0">Pagamentos do mês</h2><span>Controle de quitação — não duplica despesas nos gráficos</span></div></div><div class="payments-grid section" id="creditCardPayments"></div><div class="section card"><div class="section-head"><h2>Contas gerais</h2><span>obrigações fora dos cartões</span></div><div class="table-wrap"><table class="general-pay-table"><thead><tr><th>Conta</th><th>Vencimento</th><th>Descrição</th><th>Valor</th><th>Status</th></tr></thead><tbody id="generalPaymentsRows"></tbody></table></div></div></section>'''
new_html = '''<section id="payments" class="page"><div class="section-head"><div><h2 style="margin:0">Pagamentos e recebimentos do mês</h2><span>Concilie o previsto com o valor final pago ou recebido, sem duplicar os lançamentos</span></div></div><div class="payments-grid section" id="creditCardPayments"></div><div class="section card"><div class="section-head"><h2>Contas gerais e receitas</h2><span>registre o valor efetivamente pago/recebido</span></div><div class="table-wrap"><table class="general-pay-table"><thead><tr><th>Tipo</th><th>Conta</th><th>Data</th><th>Descrição</th><th>Previsto</th><th>Final pago/recebido</th><th>Status</th></tr></thead><tbody id="generalPaymentsRows"></tbody></table></div></div></section>'''
if old_html not in s:
    raise SystemExit('Payments HTML block not found')
s = s.replace(old_html, new_html, 1)

replacement = r'''function cardIssuer(account){let a=(account||'').toLowerCase();if(a.includes('nubank'))return'Nubank';if(a.includes('santander'))return'Santander';if(a.includes('itaú')||a.includes('itau'))return'Itaú';return null}
function paymentKey(label,name){return `${label}::${name}`}
function getPaymentStatus(label,name,def='Aguardando'){S.settings=S.settings||{};S.settings.paymentStatuses=S.settings.paymentStatuses||{};return S.settings.paymentStatuses[paymentKey(label,name)]||def}
function getPaymentActual(label,name){S.settings=S.settings||{};S.settings.paymentActuals=S.settings.paymentActuals||{};let v=S.settings.paymentActuals[paymentKey(label,name)];return v===undefined||v===null?'':Number(v)}
async function setPaymentStatus(label,name,status){S.settings=S.settings||{};S.settings.paymentStatuses=S.settings.paymentStatuses||{};S.settings.paymentStatuses[paymentKey(label,name)]=status;await save();renderPayments()}
async function setPaymentActual(label,name,value){S.settings=S.settings||{};S.settings.paymentActuals=S.settings.paymentActuals||{};let key=paymentKey(label,name);if(value==='')delete S.settings.paymentActuals[key];else S.settings.paymentActuals[key]=Number(value);await save();renderPayments()}
window.setPaymentStatus=setPaymentStatus;window.setPaymentActual=setPaymentActual;
function paymentClass(st){return st==='Pago/Recebido'||st==='Pago'?'pay-paid':st==='Parcial'?'pay-partial':'pay-await'}
function paymentStatusOptions(st){return ['Aguardando','Parcial','Pago/Recebido'].map(x=>`<option ${x===st?'selected':''}>${x}</option>`).join('')}
function renderPayments(){
 let m=monthObj(),all=monthTx(m).filter(t=>t.status!=='Cancelado'),tx=all.filter(t=>t.type==='Despesa'),label=m.label||m.key;
 let groups={Santander:0,Nubank:0,'Itaú':0};tx.forEach(t=>{let issuer=cardIssuer(t.account);if(issuer)groups[issuer]+=t.value});
 if(label==='Set-26'){groups.Santander=12162.53;groups.Nubank=1121.54}
 let due={Santander:label==='Set-26'?'04/09/2026':'—',Nubank:label==='Set-26'?'11/09/2026':'—','Itaú':'—'};
 let defaults={Santander:label==='Set-26'?'Pago/Recebido':'Aguardando',Nubank:'Aguardando','Itaú':'Aguardando'};
 $('#creditCardPayments').innerHTML=Object.entries(groups).filter(([k,v])=>v>0||label==='Set-26').map(([name,value])=>{let key='card:'+name,st=getPaymentStatus(label,key,defaults[name]),actual=getPaymentActual(label,key);return `<div class="payment-card ${paymentClass(st)}"><div class="pay-head"><div><h3>${name}</h3><div class="payment-meta">Fatura do mês</div></div>${pill(st)}</div><div class="payment-meta">Previsto</div><div class="pay-value">${money(value)}</div><div class="payment-meta">Valor final pago</div><input class="inline-input" style="width:100%;margin:6px 0 10px" type="number" step="0.01" value="${actual}" placeholder="0,00" onchange='setPaymentActual(${JSON.stringify(label)},${JSON.stringify(key)},this.value)'><div class="payment-meta">Vencimento: <b>${due[name]}</b><br>O pagamento da fatura não entra novamente como despesa.</div><select style="margin-top:10px;width:100%" onchange='setPaymentStatus(${JSON.stringify(label)},${JSON.stringify(key)},this.value)'>${paymentStatusOptions(st)}</select></div>`}).join('');
 let general=all.filter(t=>!(t.type==='Despesa'&&cardIssuer(t.account))&&!['Previstos'].includes(t.account));
 $('#generalPaymentsRows').innerHTML=general.sort((a,b)=>String(a.date).localeCompare(String(b.date))).map((t,i)=>{let key=`geral:${t.type}:${t.description}:${t.date}:${i}`,def=t.status==='Pago'||t.status==='Pago/Recebido'?'Pago/Recebido':'Aguardando',st=getPaymentStatus(label,key,def),actual=getPaymentActual(label,key),finalLabel=t.type==='Receita'?'Recebido':'Pago';return `<tr><td>${t.type}</td><td>${t.account||'Conta geral'}</td><td>${fmtDate(t.date)}</td><td>${t.description}</td><td class="money">${money(t.value)}</td><td><input class="inline-input" type="number" step="0.01" value="${actual}" placeholder="${finalLabel}" onchange='setPaymentActual(${JSON.stringify(label)},${JSON.stringify(key)},this.value)'></td><td><select onchange='setPaymentStatus(${JSON.stringify(label)},${JSON.stringify(key)},this.value)'>${paymentStatusOptions(st)}</select></td></tr>`}).join('')||'<tr><td colspan="7" class="empty">Sem pagamentos ou recebimentos cadastrados para este mês.</td></tr>'
}

function monthIndexObj'''

pattern = r"function cardIssuer\(account\)\{.*?\nfunction monthIndexObj"
s2, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'Payments JS block not found: {n}')

p.write_text(s2, encoding='utf-8')
print('Payments page updated')
