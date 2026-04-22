"""
2046 孟之秘书团 — 本地 HTML Dashboard
运行后访问 http://localhost:8080
"""
import sys, os, json, re, socket, datetime, subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.stdout.reconfigure(encoding='utf-8')

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT  = 8080
AGENTS = [
    {"key": "chenbaoz", "label": "📋 晨报z",   "folder": "晨报z",  "color": "#5aafff"},
    {"key": "live",     "label": "📊 实时行情", "folder": "",       "color": "#ffa502"},
    {"key": "pnl",      "label": "💰 盈亏",     "folder": "",       "color": "#ffd700"},
]

# ─── Markdown → HTML ──────────────────────────────────────────────────────────

def md_to_html(text, agent_key="", date_str=""):
    if not text:
        return '<p class="empty">（今日报告尚未生成）</p>'

    lines = text.splitlines()
    html_parts = []
    in_table = False
    in_list = False
    in_code = False
    i = 0

    def inline(s):
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'\*(.+?)\*',     r'<em>\1</em>', s)
        s = re.sub(r'`(.+?)`',       r'<code>\1</code>', s)
        s = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', s)
        s = re.sub(r'~~(.+?)~~',     r'<del>\1</del>', s)
        return s

    def close_list():
        nonlocal in_list
        if in_list:
            html_parts.append('</ul>')
            in_list = False

    def close_table():
        nonlocal in_table
        if in_table:
            html_parts.append('</tbody></table></div>')
            in_table = False

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        if line.startswith('```'):
            close_list(); close_table()
            in_code = not in_code
            if in_code:
                html_parts.append('<pre><code>')
            else:
                html_parts.append('</code></pre>')
            i += 1; continue

        if in_code:
            html_parts.append(raw.replace('&','&amp;').replace('<','&lt;'))
            i += 1; continue

        m = re.match(r'^(#{1,4})\s+(.*)', line)
        if m:
            close_list(); close_table()
            lvl = len(m.group(1))
            html_parts.append(f'<h{lvl}>{inline(m.group(2))}</h{lvl}>')
            i += 1; continue

        if re.match(r'^[-*_]{3,}$', line):
            close_list(); close_table()
            html_parts.append('<hr>')
            i += 1; continue

        if '|' in line and line.startswith('|'):
            close_list()
            if not in_table:
                html_parts.append('<div class="table-wrap"><table><tbody>')
                in_table = True
            cells = [c.strip() for c in line.strip('|').split('|')]
            if all(re.match(r'^[-:]+$', c.replace(' ','')) for c in cells if c):
                i += 1; continue
            tag = 'th' if not any('<td>' in p for p in html_parts[-5:] if p) else 'td'
            row = ''.join(f'<{tag}>{inline(c)}</{tag}>' for c in cells)
            html_parts.append(f'<tr>{row}</tr>')
            i += 1; continue

        close_table()

        if re.match(r'^[-*+]\s', line):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f'<li>{inline(line[2:].strip())}</li>')
            i += 1; continue

        if re.match(r'^\d+\.\s', line):
            close_list()
            html_parts.append(f'<p>{inline(line)}</p>')
            i += 1; continue

        close_list()

        if not line:
            html_parts.append('')
            i += 1; continue

        html_parts.append(f'<p>{inline(line)}</p>')
        i += 1

    close_list()
    close_table()
    return '\n'.join(html_parts)

# ─── Data helpers ─────────────────────────────────────────────────────────────

def read_md(folder, date_str):
    path = os.path.join(ROOT, folder, f'{date_str}.md')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return f.read()

def read_pnl():
    path = os.path.join(ROOT, 'pnl_log.json')
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f).get('entries', [])
    except:
        return []

def write_pnl(entries):
    path = os.path.join(ROOT, 'pnl_log.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'entries': sorted(entries, key=lambda x: x['date'])}, f, ensure_ascii=False, indent=2)

def available_dates():
    dates = set()
    for ag in AGENTS:
        if not ag['folder']:
            continue
        folder = os.path.join(ROOT, ag['folder'])
        if os.path.isdir(folder):
            for fn in os.listdir(folder):
                m = re.match(r'^(\d{4}-\d{2}-\d{2})\.md$', fn)
                if m:
                    dates.add(m.group(1))
    return sorted(dates, reverse=True)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]; s.close(); return ip
    except:
        return 'localhost'

# ─── Stock output parser ──────────────────────────────────────────────────────

def parse_stock_output_to_html(output):
    if not output:
        return '<p class="empty">无数据</p>'

    blocks = re.split(r'(?=^=== )', output, flags=re.MULTILINE)
    cards = []
    for block in blocks:
        block = block.strip()
        if not block or not block.startswith('==='):
            continue

        sym_m = re.match(r'^=== (\w+) ===', block)
        sym = sym_m.group(1) if sym_m else '?'

        price_m = re.search(r'当前价格：\$([0-9.]+)\s+\(([+-][0-9.]+)\s*/\s*([+-][0-9.]+%)\)', block)
        if price_m:
            price = price_m.group(1)
            chg   = price_m.group(2)
            pct   = price_m.group(3)
            is_up = not chg.startswith('-')
            chg_cls = 'up' if is_up else 'dn'
            chg_arrow = '▲' if is_up else '▼'
        else:
            price = '—'; chg = ''; pct = ''; chg_cls = ''; chg_arrow = ''

        # Pre/post market
        pre_m  = re.search(r'盘前价格：(.+)', block)
        post_m = re.search(r'盘后价格：(.+)', block)
        pre_raw  = pre_m.group(1).strip()  if pre_m  else 'N/A'
        post_raw = post_m.group(1).strip() if post_m else 'N/A'

        def ext_cls(s):
            if '(+' in s: return 'up'
            if '(-' in s: return 'dn'
            return ''

        pre_cls  = ext_cls(pre_raw)
        post_cls = ext_cls(post_raw)

        ma5_m   = re.search(r'MA5：\$([0-9.]+)', block)
        ma20_m  = re.search(r'MA20：\$([0-9.]+)', block)
        trend_m = re.search(r'→ (.+)', block)
        rsi_m   = re.search(r'RSI\(14\)：([0-9.]+)\s+([^\n]*)', block)
        vol_m   = re.search(r'成交量：([0-9,]+)（均量的 ([0-9.]+)x）', block)
        exp_m   = re.search(r'期权（最近到期 ([^）]+)）', block)
        call_m  = re.search(r'ATM Call：(.+)', block)
        put_m   = re.search(r'ATM Put\s*：(.+)', block)

        ma5    = ma5_m.group(1)  if ma5_m  else '—'
        ma20   = ma20_m.group(1) if ma20_m else '—'
        trend  = trend_m.group(1).strip() if trend_m else '—'
        trend_color = '#2ed573' if '看涨' in trend else '#ff4757' if '看跌' in trend else '#aaa'

        rsi_val  = float(rsi_m.group(1)) if rsi_m else 0
        rsi_str  = rsi_m.group(1) if rsi_m else '—'
        rsi_note = rsi_m.group(2).strip() if rsi_m else ''
        if rsi_val > 70:   rsi_color = '#ffa502'
        elif rsi_val < 30: rsi_color = '#5aafff'
        else:              rsi_color = '#aaa'

        vol_str   = vol_m.group(1) if vol_m else '—'
        vol_ratio = vol_m.group(2) if vol_m else ''
        exp_str   = exp_m.group(1) if exp_m else '—'
        call_str  = call_m.group(1).strip() if call_m else '—'
        put_str   = put_m.group(1).strip()  if put_m  else '—'

        card = f'''<div class="stock-card-big" id="card-{sym}">
  <div class="sc-header">
    <span class="sc-sym">{sym}</span>
    <span class="sc-exp">{exp_str}</span>
  </div>
  <div class="sc-price-row">
    <span class="sc-price">${price}</span>
    <span class="sc-chg {chg_cls}">{chg_arrow} {chg} ({pct})</span>
  </div>
  <div class="sc-ext-row">
    <span class="sc-lbl">盘前</span><span class="sc-ext {pre_cls}">{pre_raw}</span>
  </div>
  <div class="sc-ext-row">
    <span class="sc-lbl">盘后</span><span class="sc-ext {post_cls}">{post_raw}</span>
  </div>
  <div class="sc-divider"></div>
  <div class="sc-row">
    <span class="sc-lbl">MA5</span><span class="sc-val">${ma5}</span>
    <span class="sc-lbl">MA20</span><span class="sc-val">${ma20}</span>
    <span class="sc-trend" style="color:{trend_color}">{trend}</span>
  </div>
  <div class="sc-row">
    <span class="sc-lbl">RSI(14)</span>
    <span class="sc-val" style="color:{rsi_color}">{rsi_str}</span>
    <span class="sc-note">{rsi_note}</span>
  </div>
  <div class="sc-row">
    <span class="sc-lbl">成交量</span>
    <span class="sc-val">{vol_str}</span>
    <span class="sc-note">{vol_ratio}x 均量</span>
  </div>
  <div class="sc-opts">
    <div class="sc-opt call"><span class="opt-lbl">📈 ATM Call</span><span>{call_str}</span></div>
    <div class="sc-opt put"><span class="opt-lbl">📉 ATM Put</span><span>{put_str}</span></div>
  </div>
  <button class="ai-btn" onclick="aiAnalyze('{sym}', this)">🎯 AI深度分析</button>
  <div class="ai-result" id="ai-{sym}"></div>
</div>'''
        cards.append(card)

    if not cards:
        return '<p class="empty">无法解析数据</p>'
    return '<div class="stock-grid-big">' + ''.join(cards) + '</div>'

# ─── Panel renderers ──────────────────────────────────────────────────────────

def render_live_panel():
    return '''
<div class="live-query-box">
  <div class="live-title">实时行情查询</div>
  <div class="live-input-row">
    <input id="tickerInput" class="ticker-input" type="text"
           placeholder="输入股票代码，逗号分隔（如 MU, NVDA, TSLA）"
           autocomplete="off" autocapitalize="characters">
    <button class="query-btn" onclick="queryStock()">查询</button>
  </div>
  <div class="live-presets">
    <span class="preset-lbl">快捷：</span>
    <button class="preset-btn" onclick="setTicker(\'MU\')">MU</button>
    <button class="preset-btn" onclick="setTicker(\'NVDA\')">NVDA</button>
    <button class="preset-btn" onclick="setTicker(\'TSLA\')">TSLA</button>
    <button class="preset-btn" onclick="setTicker(\'AAPL\')">AAPL</button>
    <button class="preset-btn" onclick="setTicker(\'META\')">META</button>
    <button class="preset-btn" onclick="setTicker(\'MSFT\')">MSFT</button>
    <button class="preset-btn" onclick="setTicker(\'MU,NVDA,TSLA\')">全家桶</button>
  </div>
</div>
<div id="stockResults" class="stock-results">
  <p class="empty">输入股票代码后点击查询</p>
</div>'''


def render_pnl_panel(date_str):
    import calendar as cal_mod
    entries = read_pnl()
    pnl_map = {e['date']: e for e in entries}
    today = str(datetime.date.today())

    try:
        display_month = datetime.date.fromisoformat(date_str).replace(day=1)
    except Exception:
        display_month = datetime.date.today().replace(day=1)

    prev_month = (display_month - datetime.timedelta(days=1)).replace(day=1)
    next_month = (display_month.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)

    prev_link = f'<a class="mnav" href="/{prev_month}#panel-pnl">&#9664;</a>'
    if next_month > datetime.date.today():
        next_link = '<span class="mnav" style="opacity:.3;pointer-events:none">&#9654;</span>'
    else:
        next_link = f'<a class="mnav" href="/{next_month}#panel-pnl">&#9654;</a>'

    year, month = display_month.year, display_month.month
    month_entries = [e for e in entries if e['date'].startswith(f'{year:04d}-{month:02d}')]
    month_total = sum(e['pnl'] for e in month_entries)
    win_days  = sum(1 for e in month_entries if e['pnl'] > 0)
    loss_days = sum(1 for e in month_entries if e['pnl'] < 0)
    trade_days = len(month_entries)
    win_rate = round(win_days / trade_days * 100) if trade_days else 0
    total_color = '#2ed573' if month_total >= 0 else '#ff4757'
    sign = '+' if month_total > 0 else ''
    stats_html = f'''
<div class="pnl-stats">
  <div class="pnl-card"><div class="val" style="color:{total_color}">{sign}{month_total:,.0f}</div><div class="lbl">月度盈亏 SGD</div></div>
  <div class="pnl-card"><div class="val">{trade_days}</div><div class="lbl">交易天数</div></div>
  <div class="pnl-card"><div class="val" style="color:#2ed573">{win_rate}%</div><div class="lbl">月度胜率</div></div>
  <div class="pnl-card"><div class="val" style="color:#2ed573">{win_days}盈 / <span style="color:#ff4757">{loss_days}亏</span></div><div class="lbl">盈亏天数</div></div>
</div>'''

    weekdays = '<tr>' + ''.join(f'<th class="cal-wday">{d}</th>' for d in ['一','二','三','四','五','六','日']) + '</tr>'
    cal_rows = ''
    for week in cal_mod.monthcalendar(year, month):
        row = '<tr>'
        for i, day in enumerate(week):
            is_weekend = i >= 5
            if day == 0:
                row += '<td class="cal-day cal-empty"></td>'
            else:
                dk = f'{year:04d}-{month:02d}-{day:02d}'
                entry = pnl_map.get(dk)
                today_cls = ' cal-today' if dk == today else ''
                wknd_cls  = ' cal-weekend' if is_weekend else ''
                if entry:
                    v = entry['pnl']
                    if v > 0:   c, vs = 'cal-win',  f'+{v:,.0f}'
                    elif v < 0: c, vs = 'cal-loss', f'{v:,.0f}'
                    else:       c, vs = 'cal-zero', '0'
                    note_attr = f' title="{entry.get("note","")}"' if entry.get('note') else ''
                    row += (f'<td class="cal-day {c}{today_cls}{wknd_cls}"{note_attr}>'
                            f'<div class="cal-num">{day}</div>'
                            f'<div class="cal-pnl">{vs}</div></td>')
                else:
                    row += (f'<td class="cal-day cal-nodata{today_cls}{wknd_cls}">'
                            f'<div class="cal-num">{day}</div></td>')
        row += '</tr>'
        cal_rows += row

    calendar_html = f'''
<div class="pnl-cal-wrap">
  <div class="pnl-cal-nav">{prev_link}<span class="pnl-month">{display_month.strftime("%Y年%m月")}</span>{next_link}</div>
  <table class="pnl-cal"><thead>{weekdays}</thead><tbody>{cal_rows}</tbody></table>
</div>'''

    sorted_entries = sorted(entries, key=lambda e: e['date'])
    cumulative, cum_dates, cum_vals = 0, [], []
    for e in sorted_entries:
        cumulative += e['pnl']
        cum_dates.append(e['date'][5:])
        cum_vals.append(round(cumulative, 2))
    total_pnl = cumulative
    tc2 = '#2ed573' if total_pnl >= 0 else '#ff4757'
    ts = '+' if total_pnl > 0 else ''

    chart_html = ''
    if cum_vals:
        chart_html = f'''
<div class="pnl-chart-wrap">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
    <span style="color:#aac;font-size:.9em">累计盈亏走势</span>
    <span style="font-size:1.1em;font-weight:700;color:{tc2}">{ts}{total_pnl:,.2f} SGD</span>
  </div>
  <canvas id="pnlChart" height="120"></canvas>
</div>
<script>
(function(){{
  const ctx = document.getElementById('pnlChart');
  if (!ctx) return;
  new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: {json.dumps(cum_dates)},
      datasets: [{{
        label: '累计 SGD', data: {json.dumps(cum_vals)},
        borderColor: '{tc2}',
        backgroundColor: '{tc2}22',
        tension: 0.3, pointRadius: 2, fill: true
      }}]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: '#668', maxTicksLimit: 12 }}, grid: {{ color: '#1e1e32' }} }},
        y: {{ ticks: {{ color: '#668',
              callback: function(v) {{ return Math.abs(v)>=1000 ? (v/1000).toFixed(1)+'k' : v; }}
             }}, grid: {{ color: '#1e1e32' }} }}
      }}
    }}
  }});
}})();
</script>'''

    today_entry = pnl_map.get(today, {})
    form_html = f'''
<div class="pnl-form">
  <h3>记录盈亏</h3>
  <form method="post" action="/pnl">
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
      <input type="date" name="date" value="{today}" class="pnl-input" style="width:150px">
      <input type="number" name="pnl" step="0.01" placeholder="盈亏金额（亏损填负数）"
             value="{today_entry.get('pnl','')}" class="pnl-input" style="width:220px">
      <input type="text" name="note" placeholder="备注（可选）"
             value="{today_entry.get('note','')}" class="pnl-input" style="flex:1;min-width:120px">
      <button type="submit" class="pnl-btn">记录</button>
    </div>
  </form>
</div>'''

    return f'{stats_html}{calendar_html}{chart_html}{form_html}'


def render_panel(agent, date_str):
    key = agent['key']
    if key == 'live':
        return render_live_panel()
    if key == 'pnl':
        return render_pnl_panel(date_str)

    md_text = read_md(agent['folder'], date_str)
    if not md_text:
        return f'''<div class="no-report">
  <div class="icon">{agent["label"][0]}</div>
  <p>今日报告尚未生成</p>
  <p style="margin-top:8px;font-size:.8em">等待 07:00 SGT 晨报z 自动生成</p>
</div>'''
    return f'<div class="md-content">{md_to_html(md_text, key, date_str)}</div>'

# ─── CSS ──────────────────────────────────────────────────────────────────────

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;
  background:#0d0d1a;color:#d0d0e8;min-height:100vh}
a{color:#7c8eff;text-decoration:none}
a:hover{text-decoration:underline}
code{background:#1e1e32;padding:2px 6px;border-radius:4px;font-size:0.88em}
pre{background:#1e1e32;padding:14px;border-radius:10px;overflow-x:auto;margin:12px 0}
pre code{background:none;padding:0}
h1{font-size:1.4em;margin:18px 0 10px;color:#fff}
h2{font-size:1.15em;margin:16px 0 8px;color:#ccd}
h3{font-size:1em;margin:12px 0 6px;color:#aab}
h4{font-size:.95em;margin:10px 0 5px;color:#99a}
p{margin:6px 0;line-height:1.65}
hr{border:none;border-top:1px solid #2a2a40;margin:16px 0}
strong{color:#fff}
del{color:#666}
.table-wrap{overflow-x:auto;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:.88em}
th,td{padding:7px 12px;border:1px solid #2a2a40;text-align:left}
th{background:#1a1a30;color:#aad}
tr:nth-child(even) td{background:#131325}
ul{padding-left:18px;margin:6px 0}
li{margin:4px 0;line-height:1.6}
.empty{color:#555;font-style:italic;padding:20px 0}

/* Header */
.header{background:#12122a;border-bottom:1px solid #2a2a40;
  padding:12px 20px;display:flex;align-items:center;gap:16px;
  position:sticky;top:0;z-index:100}
.brand{font-size:1.1em;font-weight:700;color:#fff;white-space:nowrap}
.brand span{color:#7c8eff}
.date-nav{display:flex;align-items:center;gap:8px;margin:0 auto}
.date-nav a{background:#1e1e35;border:1px solid #3a3a55;border-radius:8px;
  color:#aad;padding:5px 12px;font-size:.9em;cursor:pointer}
.date-nav a:hover{background:#2a2a45;text-decoration:none}
.date-display{font-size:1em;font-weight:600;color:#fff;min-width:110px;text-align:center}
.today-btn{background:#2a2a45;border:1px solid #5a5a80;border-radius:8px;
  color:#aaf;padding:5px 12px;font-size:.85em;cursor:pointer}

/* Tabs */
.tabs{display:flex;border-bottom:1px solid #2a2a40;background:#0f0f1f;
  overflow-x:auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{padding:12px 20px;cursor:pointer;font-size:.9em;white-space:nowrap;
  border-bottom:2px solid transparent;color:#778;transition:all .2s}
.tab:hover{color:#aac;background:#1a1a30}
.tab.active{color:#fff;border-bottom-color:var(--tc)}

/* Content */
.content{padding:20px;max-width:960px;margin:0 auto}
.panel{display:none}.panel.active{display:block}

/* No-report */
.no-report{text-align:center;padding:60px 20px;color:#445}
.no-report .icon{font-size:3em;margin-bottom:16px}
.no-report p{font-size:.9em}

/* Toast */
.toast{position:fixed;top:20px;left:50%;transform:translateX(-50%);
  background:#2ed573;color:#0f2a1a;font-weight:600;padding:10px 24px;
  border-radius:20px;font-size:.9em;opacity:0;transition:opacity .3s;z-index:999;pointer-events:none}
.toast.show{opacity:1}

/* Live panel */
.live-query-box{background:#1a1a30;border-radius:14px;padding:20px;margin-bottom:20px}
.live-title{font-size:1em;font-weight:700;color:#ffa502;margin-bottom:14px}
.live-input-row{display:flex;gap:10px;margin-bottom:12px}
.ticker-input{flex:1;background:#0d0d1a;border:1px solid #3a3a55;border-radius:10px;
  color:#fff;font-size:1em;padding:10px 14px;outline:none;letter-spacing:1px;text-transform:uppercase}
.ticker-input:focus{border-color:#ffa502}
.query-btn{background:#ffa502;color:#1a0d00;border:none;border-radius:10px;
  padding:10px 24px;font-size:.95em;font-weight:700;cursor:pointer;white-space:nowrap}
.query-btn:hover{background:#ffb830}
.query-btn:active{opacity:.8}
.live-presets{display:flex;align-items:center;flex-wrap:wrap;gap:6px}
.preset-lbl{color:#556;font-size:.82em}
.preset-btn{background:#1e1e35;border:1px solid #3a3a55;border-radius:6px;
  color:#aad;font-size:.82em;padding:4px 10px;cursor:pointer}
.preset-btn:hover{background:#2a2a45;color:#fff}
.stock-results{min-height:60px}
.loading-msg{color:#ffa502;padding:20px 0;text-align:center;font-size:.9em}

/* Big stock cards */
.stock-grid-big{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.stock-card-big{background:#1a1a30;border-radius:14px;padding:16px;border:1px solid #2a2a40}
.sc-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.sc-sym{font-size:1.2em;font-weight:800;color:#ffa502;letter-spacing:1px}
.sc-exp{font-size:.75em;color:#556;background:#0d0d1a;padding:3px 8px;border-radius:6px}
.sc-price-row{display:flex;align-items:baseline;gap:10px;margin-bottom:12px}
.sc-price{font-size:1.8em;font-weight:700;color:#fff}
.sc-chg{font-size:.9em;font-weight:600}
.sc-chg.up{color:#2ed573}.sc-chg.dn{color:#ff4757}
.sc-row{display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:.85em}
.sc-lbl{color:#556;min-width:56px}
.sc-val{color:#ccd;font-weight:600}
.sc-trend{font-size:.8em;margin-left:auto}
.sc-note{color:#778;font-size:.8em}
.sc-ext-row{display:flex;align-items:center;gap:8px;margin-bottom:4px;font-size:.82em}
.sc-ext{font-weight:600;color:#aab}
.sc-ext.up{color:#2ed573}.sc-ext.dn{color:#ff4757}
.sc-divider{border-top:1px solid #2a2a40;margin:10px 0}
.sc-opts{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;border-top:1px solid #2a2a40;padding-top:12px}
.sc-opt{background:#0d0d1a;border-radius:8px;padding:8px 10px;font-size:.8em;color:#aab}
.sc-opt.call{border-left:3px solid #2ed573}
.sc-opt.put{border-left:3px solid #ff4757}
.opt-lbl{display:block;color:#778;font-size:.75em;margin-bottom:4px}
.ai-btn{width:100%;margin-top:12px;background:linear-gradient(135deg,#2a1a50,#1a2a50);
  border:1px solid #4a3a80;border-radius:8px;color:#aac;font-size:.85em;
  padding:8px;cursor:pointer;transition:all .2s}
.ai-btn:hover{background:linear-gradient(135deg,#3a2a70,#2a3a70);color:#fff}
.ai-btn:disabled{opacity:.5;cursor:not-allowed}
.ai-result{margin-top:12px;font-size:.85em;line-height:1.6;color:#ccd}
.ai-result h3{font-size:.9em;color:#ffa502;margin:10px 0 4px}
.ai-result h4{font-size:.85em;color:#aad;margin:8px 0 3px}
.ai-result strong{color:#fff}
.ai-result table{width:100%;font-size:.8em;margin:6px 0}
.ai-result th{background:#1a1a2a;color:#889;font-weight:normal}
.ai-result td,.ai-result th{padding:5px 8px;border:1px solid #2a2a40}
.ai-loading{color:#ffa502;text-align:center;padding:12px;font-size:.85em}

/* PnL Calendar */
.pnl-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:20px}
.pnl-card{background:#1a1a30;border-radius:12px;padding:12px;text-align:center}
.pnl-card .val{font-size:1.5em;font-weight:700;color:#ffd700}
.pnl-card .lbl{font-size:.75em;color:#778;margin-top:4px}
.pnl-cal-wrap{background:#1a1a30;border-radius:12px;padding:16px;margin-bottom:20px}
.pnl-cal-nav{display:flex;align-items:center;justify-content:center;gap:16px;margin-bottom:14px}
.pnl-month{font-size:1em;font-weight:600;color:#fff}
.mnav{background:#1e1e35;border:1px solid #3a3a55;border-radius:8px;color:#aad;padding:5px 12px;font-size:.9em;cursor:pointer}
.mnav:hover{background:#2a2a45;text-decoration:none}
.pnl-cal{border-collapse:collapse;width:100%;table-layout:fixed}
.pnl-cal thead th,.pnl-cal tbody td{padding:4px 2px;text-align:center;border:none}
.cal-wday{color:#556;font-size:.78em;padding-bottom:6px}
.cal-day{border-radius:8px;padding:4px !important;cursor:default;min-height:48px;vertical-align:top}
.cal-empty{background:none !important;border:none !important}
.cal-num{font-size:.78em;color:#778;text-align:right;padding-right:4px}
.cal-pnl{font-size:.82em;font-weight:600;margin-top:2px}
.cal-win{background:#0d2a18;border:1px solid #1a5c32}
.cal-win .cal-pnl{color:#2ed573}
.cal-loss{background:#2a0d10;border:1px solid #5c1a1a}
.cal-loss .cal-pnl{color:#ff4757}
.cal-zero{background:#1a1a25;border:1px solid #2a2a40}
.cal-zero .cal-pnl{color:#556}
.cal-nodata{background:#111120;border:1px solid #1e1e30}
.cal-today .cal-num{color:#ffd700;font-weight:700}
.cal-weekend .cal-num{color:#445}
.pnl-chart-wrap{background:#1a1a30;border-radius:12px;padding:16px;margin-bottom:20px}
.pnl-form{background:#1a1a30;border-radius:12px;padding:16px;border:1px dashed #3a3a55;margin-bottom:20px}
.pnl-form h3{color:#ffd700;margin-bottom:12px}
.pnl-input{background:#0d0d1a;border:1px solid #3a3a55;border-radius:8px;color:#fff;font-size:.9em;padding:9px 12px;outline:none}
.pnl-input:focus{border-color:#ffd700}
.pnl-btn{background:#ffd700;color:#1a1200;border:none;border-radius:8px;padding:9px 20px;font-size:.9em;font-weight:700;cursor:pointer}
"""

JS = """
// Tab switching
function showTab(key) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelector('.tab[data-key="'+key+'"]').classList.add('active');
  document.getElementById('panel-'+key).classList.add('active');
  localStorage.setItem('activeTab', key);
}
const lastTab = localStorage.getItem('activeTab');
if (lastTab && document.querySelector('.tab[data-key="'+lastTab+'"]')) {
  showTab(lastTab);
}

// Stock query
function setTicker(sym) {
  const inp = document.getElementById('tickerInput');
  if (inp) { inp.value = sym; inp.focus(); }
}
function queryStock() {
  const inp = document.getElementById('tickerInput');
  if (!inp) return;
  const val = inp.value.trim();
  if (!val) { inp.focus(); return; }
  const res = document.getElementById('stockResults');
  res.innerHTML = '<p class="loading-msg">⏳ 正在获取实时数据...</p>';
  fetch('/stock-query', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'tickers=' + encodeURIComponent(val)
  })
  .then(r => r.json())
  .then(d => {
    res.innerHTML = d.ok ? d.html : '<p class="empty">查询失败，请检查股票代码</p>';
  })
  .catch(() => { res.innerHTML = '<p class="empty">网络错误</p>'; });
}
const tickerInp = document.getElementById('tickerInput');
if (tickerInp) {
  tickerInp.addEventListener('keydown', e => { if(e.key==='Enter') queryStock(); });
}

// AI deep analysis
function aiAnalyze(sym, btn) {
  const res = document.getElementById('ai-' + sym);
  btn.disabled = true;
  btn.textContent = '⏳ AI分析中（约30秒）…';
  res.innerHTML = '<div class="ai-loading">🔍 正在搜索盘前新闻 + 期权异动 + 生成建议…</div>';
  fetch('/stock-ai-analyze', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'ticker=' + encodeURIComponent(sym)
  })
  .then(r => r.json())
  .then(d => {
    btn.disabled = false;
    btn.textContent = '🔄 重新分析';
    res.innerHTML = d.ok ? d.html : '<p style="color:#ff4757">' + d.error + '</p>';
  })
  .catch(() => {
    btn.disabled = false;
    btn.textContent = '🎯 AI深度分析';
    res.innerHTML = '<p style="color:#ff4757">请求失败</p>';
  });
}

// Toast
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}
"""

# ─── Page builder ─────────────────────────────────────────────────────────────

def build_page(date_str):
    today = str(datetime.date.today())
    dates = available_dates()

    if date_str in dates:
        idx = dates.index(date_str)
        prev_date = dates[idx + 1] if idx + 1 < len(dates) else None
        next_date = dates[idx - 1] if idx - 1 >= 0 else None
    else:
        prev_date = dates[0] if dates else None
        next_date = None

    prev_link = f'<a href="/{prev_date}">◀</a>' if prev_date else '<a style="opacity:.3;pointer-events:none">◀</a>'
    next_link = f'<a href="/{next_date}">▶</a>' if next_date else '<a style="opacity:.3;pointer-events:none">▶</a>'
    today_link = f'<a href="/{today}" class="today-btn">今天</a>' if date_str != today else ''

    tabs_html = ''
    panels_html = ''
    for ag in AGENTS:
        is_active = ag == AGENTS[0]
        tabs_html += (f'<div class="tab{" active" if is_active else ""}" '
                      f'data-key="{ag["key"]}" style="--tc:{ag["color"]}" '
                      f'onclick="showTab(\'{ag["key"]}\')">{ag["label"]}</div>')
        panel_content = render_panel(ag, date_str)
        panels_html += f'<div class="panel{" active" if is_active else ""}" id="panel-{ag["key"]}">{panel_content}</div>'

    local_ip = get_local_ip()

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>孟之秘书团 · {date_str}</title>
<style>{CSS}</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>

<div class="header">
  <div class="brand">2046 <span>孟之</span></div>
  <div class="date-nav">
    {prev_link}
    <span class="date-display">{date_str}</span>
    {next_link}
    {today_link}
  </div>
  <div style="font-size:.75em;color:#445">{local_ip}:8080</div>
</div>

<div class="tabs">{tabs_html}</div>
<div class="content">{panels_html}</div>

<div class="toast" id="toast"></div>
<script>{JS}</script>
</body>
</html>'''

# ─── HTTP Handler ─────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_html(self, html, code=200):
        b = html.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def redirect(self, url):
        self.send_response(302)
        self.send_header('Location', url)
        self.end_headers()

    def send_json(self, obj):
        b = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return parse_qs(self.rfile.read(length).decode('utf-8'))

    def do_GET(self):
        path = urlparse(self.path).path.strip('/')
        today = str(datetime.date.today())

        if not path:
            self.redirect(f'/{today}')
            return

        if re.match(r'^\d{4}-\d{2}-\d{2}$', path):
            self.send_html(build_page(path))
            return

        self.send_html('<h1>404</h1>', 404)

    def do_POST(self):
        path = urlparse(self.path).path
        params = self.read_body()

        if path == '/stock-query':
            tickers_raw = params.get('tickers', [''])[0].upper()
            ticker_list = [t.strip() for t in re.split(r'[,\s]+', tickers_raw) if t.strip()]
            if ticker_list:
                cmd = [sys.executable, os.path.join(ROOT, 'scripts', 'get_stock_data.py')] + ticker_list[:5]
                try:
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, encoding='utf-8',
                        cwd=ROOT, timeout=45
                    )
                    cards_html = parse_stock_output_to_html(result.stdout)
                    self.send_json({'ok': True, 'html': cards_html})
                except subprocess.TimeoutExpired:
                    self.send_json({'ok': False, 'html': '<p class="empty">查询超时，请稍后重试</p>'})
                except Exception as e:
                    self.send_json({'ok': False, 'html': f'<p class="empty">错误：{e}</p>'})
            else:
                self.send_json({'ok': False, 'html': '<p class="empty">请输入股票代码</p>'})
            return

        if path == '/stock-ai-analyze':
            ticker = params.get('ticker', [''])[0].upper().strip()
            if not ticker:
                self.send_json({'ok': False, 'error': '未提供股票代码', 'html': ''})
                return
            # Step 1: get real-time data
            data_cmd = [sys.executable, os.path.join(ROOT, 'scripts', 'get_stock_data.py'), ticker]
            try:
                data_result = subprocess.run(
                    data_cmd, capture_output=True, text=True, encoding='utf-8',
                    cwd=ROOT, timeout=45
                )
                stock_data = data_result.stdout.strip()
            except Exception as e:
                self.send_json({'ok': False, 'error': f'行情数据获取失败: {e}', 'html': ''})
                return

            today = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d')
            prompt = f"""你是孟之的盘前投资顾问。交易风格：开盘30分钟内完成，目标每日$500，主要策略 Buy Call + Sell Put。

以下是 {ticker} 的实时数据（用作事实基准，不要质疑这些数字）：
{stock_data}

请立即执行以下分析（中文，简洁专业，全程用 Markdown）：

### 🚀 盘前/盘后异动
WebSearch "{ticker} premarket news today {today}"
- 价格变动核心原因（1-2句）

### 🌐 大盘背景
WebSearch "US stock market futures premarket {today}"
- 大盘环境一句话判断（风险偏好 on/off）

### 🐋 大单期权异动
WebSearch "{ticker} unusual options activity {today}"
- 有无异常大单，方向偏多还是空（1句）

### 🎯 今日操作建议
基于上述分析和实时数据，给出具体建议：

**Buy Call**
| 项目 | 详情 |
|------|------|
| 合约 | ${ticker} $XXX Call MM-DD |
| 入场区间 | $X.XX – $X.XX |
| 止盈/止损 | +50% / -30% |
| 入场时机 | 开盘后X分钟 |

**Sell Put**
| 项目 | 详情 |
|------|------|
| 合约 | ${ticker} $XXX Put MM-DD |
| 权利金 | $X.XX |
| 支撑位/止损 | 跌破$XXX则平仓 |

### ⚠️ 关键风险
- （1-2条，简洁）

只输出分析结果，不要任何前言或总结。"""

            try:
                ai_cmd = ['claude', '--dangerously-skip-permissions', '-p', prompt]
                ai_result = subprocess.run(
                    ai_cmd, capture_output=True, text=True, encoding='utf-8',
                    cwd=ROOT, timeout=120
                )
                md_text = ai_result.stdout.strip()
                if not md_text:
                    md_text = ai_result.stderr.strip() or '分析未返回结果'
                html_out = f'<div class="ai-result">{md_to_html(md_text)}</div>'
                self.send_json({'ok': True, 'html': html_out})
            except subprocess.TimeoutExpired:
                self.send_json({'ok': False, 'error': 'AI分析超时（>120秒），请重试', 'html': ''})
            except Exception as e:
                self.send_json({'ok': False, 'error': f'AI调用失败: {e}', 'html': ''})
            return

        if path == '/pnl':
            date_str = params.get('date', [''])[0].strip()
            pnl_str  = params.get('pnl',  [''])[0].strip()
            note     = params.get('note', [''])[0].strip()
            if date_str and pnl_str:
                try:
                    pnl_val = float(pnl_str)
                    entries = read_pnl()
                    entries = [e for e in entries if e.get('date') != date_str]
                    entries.append({'date': date_str, 'pnl': pnl_val, 'currency': 'SGD', 'note': note})
                    write_pnl(entries)
                except Exception:
                    pass
            self.redirect(f'/{date_str}#panel-pnl')
            return

        self.send_html('<h1>404</h1>', 404)

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    ip = get_local_ip()
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'[孟之秘书团 Dashboard]')
    print(f'  电脑: http://localhost:{PORT}')
    print(f'  手机: http://{ip}:{PORT}  (同一 WiFi)')
    print(f'  Ctrl+C 停止')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止')
