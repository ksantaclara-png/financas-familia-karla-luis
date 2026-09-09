from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old = "s.months=(s.months||[]).map(m=>{m.transactions=m.transactions||[];m.categories=m.categories||[];m.summary=m.summary||{};return m});"
new = "s.months=(s.months||[]).filter(m=>m&&typeof m==='object').map(m=>{m.transactions=Array.isArray(m.transactions)?m.transactions:[];m.categories=Array.isArray(m.categories)?m.categories:[];m.summary=m.summary&&typeof m.summary==='object'?m.summary:{};return m});"

if old not in s:
    if new in s:
        print('Guard already applied')
    else:
        raise SystemExit('normState months block not found')
else:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding='utf-8')
    print('Null-month guard applied')
