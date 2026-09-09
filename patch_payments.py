from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Mantém a proteção contra meses nulos
old_guard = "s.months=(s.months||[]).map(m=>{m.transactions=m.transactions||[];m.categories=m.categories||[];m.summary=m.summary||{};return m});"
new_guard = "s.months=(s.months||[]).filter(m=>m&&typeof m==='object').map(m=>{m.transactions=Array.isArray(m.transactions)?m.transactions:[];m.categories=Array.isArray(m.categories)?m.categories:[];m.summary=m.summary&&typeof m.summary==='object'?m.summary:{};return m});"
if old_guard in s:
    s = s.replace(old_guard, new_guard, 1)

# CSS dos cards-resumo
css_marker = "/* === resumo pagamentos === */"
if css_marker not in s:
    css = '''\n/* === resumo pagamentos === */\n.payment-summary-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.payment-summary-card{padding:18px;border-radius:17px;border:1px solid var(--line);box-shadow:var(--shadow);background:#fff}.payment-summary-card.paid{background:#e9f5ee;border-color:#cfe6d8}.payment-summary-card.pending{background:#fff4df;border-color:#f0dfbd}.payment-summary-card .ps-label{font-size:10px;text-transform:uppercase;letter-spacing:.06em;font-weight:850;color:var(--muted)}.payment-summary-card .ps-value{font-size:27px;font-weight:900;margin:7px 0 4px}.payment-summary-card.paid .ps-value{color:var(--ok)}.payment-summary-card.pending .ps-value{color:#a86b00}.payment-summary-card .ps-note{font-size:11px;color:var(--muted);line-height:1.4}.payment-summary-progress{height:7px;background:rgba(0,0,0,.07);border-radius:99px;overflow:hidden;margin-top:10px}.payment-summary-progress i{display:block;height:100%;background:var(--ok);border-radius:99px}@media(max-width:620px){.payment-summary-grid{grid-template-columns:1fr}}\n'''
    s = s.replace('</style>', css + '</style>', 1)

# Área dos cards na aba Pagamentos
html_old = '<section id="payments" class="page"><div class="section-head"><div><h2 style="margin:0">Pagamentos e recebimentos do mês</h2><span>Concilie o previsto com o valor final pago ou recebido, sem duplicar os lançamentos</span></div></div><div class="payments-grid section" id="creditCardPayments"></div>'
html_new = '<section id="payments" class="page"><div class="section-head"><div><h2 style="margin:0">Pagamentos e recebimentos do mês</h2><span>Concilie o previsto com o valor final pago ou recebido, sem duplicar os lançamentos</span></div></div><div class="payment-summary-grid section" id="paymentSummaryCards"></div><div class="payments-grid section" id="creditCardPayments"></div>'
if 'id="paymentSummaryCards"' not in s:
    if html_old not in s:
        raise SystemExit('Bloco HTML de Pagamentos não encontrado')
    s = s.replace(html_old, html_new, 1)

# Cálculo e renderização do resumo: somente despesas do mês
anchor = "let defaults={Santander:label==='Set-26'?'Pago/Recebido':'Aguardando',Nubank:'Aguardando','Itaú':'Aguardando'};\n"
summary_js = r'''let defaults={Santander:label==='Set-26'?'Pago/Recebido':'Aguardando',Nubank:'Aguardando','Itaú':'Aguardando'};
 let paidTotal=0,pendingTotal=0,totalToPay=0;
 Object.entries(groups).forEach(([name,value])=>{
   if(value<=0)return;
   let key='card:'+name,st=getPaymentStatus(label,key,defaults[name]),actual=getPaymentActual(label,key),paid=0;
   if(st==='Pago/Recebido'||st==='Pago') paid=actual!==''?Number(actual):Number(value);
   else if(st==='Parcial') paid=actual!==''?Math.min(Number(value),Number(actual)):0;
   totalToPay+=Number(value);paidTotal+=Math.max(0,paid);pendingTotal+=Math.max(0,Number(value)-paid);
 });
 let summaryGeneral=all.filter(t=>t.type==='Despesa'&&!cardIssuer(t.account)&&!['Previstos'].includes(t.account));
 summaryGeneral.forEach((t,i)=>{
   let key=`geral:${t.type}:${t.description}:${t.date}:${i}`,def=t.status==='Pago'||t.status==='Pago/Recebido'?'Pago/Recebido':'Aguardando',st=getPaymentStatus(label,key,def),actual=getPaymentActual(label,key),paid=0;
   if(st==='Pago/Recebido'||st==='Pago') paid=actual!==''?Number(actual):Number(t.value);
   else if(st==='Parcial') paid=actual!==''?Math.min(Number(t.value),Number(actual)):0;
   totalToPay+=Number(t.value);paidTotal+=Math.max(0,paid);pendingTotal+=Math.max(0,Number(t.value)-paid);
 });
 let paidPct=totalToPay?Math.min(1,paidTotal/totalToPay):0;
 $('#paymentSummaryCards').innerHTML=`<div class="payment-summary-card paid"><div class="ps-label">✓ Pago no mês</div><div class="ps-value">${money(paidTotal)}</div><div class="ps-note">${pct(paidPct)} do total de despesas previstas já foi quitado.</div><div class="payment-summary-progress"><i style="width:${paidPct*100}%"></i></div></div><div class="payment-summary-card pending"><div class="ps-label">⏳ Ainda não pago</div><div class="ps-value">${money(pendingTotal)}</div><div class="ps-note">Valor que ainda falta quitar entre cartões e contas gerais deste mês.</div></div>`;
'''
if "$('#paymentSummaryCards').innerHTML=" not in s:
    if anchor not in s:
        raise SystemExit('Ponto de inserção do resumo não encontrado')
    s = s.replace(anchor, summary_js, 1)

p.write_text(s, encoding='utf-8')
print('Resumo de pagamentos aplicado')
