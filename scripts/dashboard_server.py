"""
2046 孟之秘书团 — 本地 HTML Dashboard
运行后访问 http://localhost:8080
"""
import sys, os, json, re, socket, datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.stdout.reconfigure(encoding='utf-8')

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT  = 8080
AGENTS = [
    {"key": "xinwen",   "label": "📰 新闻z",  "folder": "新闻z",  "color": "#5aafff"},
    {"key": "touzi",    "label": "📈 投资z",  "folder": "投资z",  "color": "#ffa502"},
    {"key": "jiankang", "label": "💪 健康z",  "folder": "健康z",  "color": "#2ed573"},
    {"key": "niuma",    "label": "✅ 牛马z",  "folder": "牛马z",  "color": "#ff6b81"},
    {"key": "pnl",      "label": "💰 盈亏",   "folder": "",        "color": "#ffd700"},
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

        # Code fence
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

        # Headings
        m = re.match(r'^(#{1,4})\s+(.*)', line)
        if m:
            close_list(); close_table()
            lvl = len(m.group(1))
            html_parts.append(f'<h{lvl}>{inline(m.group(2))}</h{lvl}>')
            i += 1; continue

        # HR
        if re.match(r'^[-*_]{3,}$', line):
            close_list(); close_table()
            html_parts.append('<hr>')
            i += 1; continue

        # Table
        if '|' in line and line.startswith('|'):
            close_list()
            if not in_table:
                html_parts.append('<div class="table-wrap"><table><tbody>')
                in_table = True
            cells = [c.strip() for c in line.strip('|').split('|')]
            if all(re.match(r'^[-:]+$', c.replace(' ','')) for c in cells if c):
                i += 1; continue  # separator row
            tag = 'th' if not any('<td>' in p for p in html_parts[-5:] if p) else 'td'
            row = ''.join(f'<{tag}>{inline(c)}</{tag}>' for c in cells)
            html_parts.append(f'<tr>{row}</tr>')
            i += 1; continue

        close_table()

        # Todo checkboxes (niuma only)
        if agent_key == 'niuma' and re.match(r'^- \[[ x]\]', line):
            if not in_list:
                html_parts.append('<ul class="todo-list">')
                in_list = True
            checked = 'x' in line[3]
            task_text = inline(line[6:].strip())
            idx = sum(1 for p in html_parts if 'todo-item' in p)
            checked_attr = 'checked' if checked else ''
            done_class = ' done' if checked else ''
            html_parts.append(
                f'<li class="todo-item{done_class}" data-idx="{idx}" data-date="{date_str}">'
                f'<label><input type="checkbox" {checked_attr} onchange="toggleTask(this,{idx},\'{date_str}\')">'
                f'<span>{task_text}</span></label></li>'
            )
            i += 1; continue

        # Regular list item
        if re.match(r'^[-*+]\s', line):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f'<li>{inline(line[2:].strip())}</li>')
            i += 1; continue

        # Numbered list
        if re.match(r'^\d+\.\s', line):
            close_list()
            html_parts.append(f'<p>{inline(line)}</p>')
            i += 1; continue

        close_list()

        # Blank line
        if not line:
            html_parts.append('')
            i += 1; continue

        # Paragraph
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

def read_aboutme():
    path = os.path.join(ROOT, 'aboutme.json')
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def write_aboutme(data):
    path = os.path.join(ROOT, 'aboutme.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
    """Return sorted list of dates that have at least one agent report."""
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

# ─── HTML Template ────────────────────────────────────────────────────────────

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
.content{padding:20px;max-width:900px;margin:0 auto}
.panel{display:none}.panel.active{display:block}

/* Health */
.health-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:20px}
.hcard{background:#1a1a30;border-radius:12px;padding:14px;text-align:center;border:1px solid #2a2a40}
.hcard .val{font-size:1.8em;font-weight:700;color:#2ed573}
.hcard .lbl{font-size:.75em;color:#778;margin-top:4px}
.chart-wrap{background:#1a1a30;border-radius:12px;padding:16px;margin-bottom:20px}
.weight-form{background:#1a1a30;border-radius:12px;padding:16px;
  border:1px dashed #3a3a55;margin-bottom:20px}
.weight-form h3{color:#2ed573;margin-bottom:12px}
.weight-form input[type=number]{background:#0d0d1a;border:1px solid #3a3a55;
  border-radius:8px;color:#fff;font-size:1em;padding:10px 14px;width:140px;outline:none}
.weight-form input:focus{border-color:#2ed573}
.weight-form button{background:#2ed573;color:#0d2a1a;border:none;border-radius:8px;
  padding:10px 20px;font-size:.95em;font-weight:600;cursor:pointer;margin-left:10px}

/* Todo */
.todo-list{list-style:none;padding:0;margin:8px 0}
.todo-item{background:#1a1a30;border-radius:10px;padding:10px 14px;
  margin-bottom:6px;border-left:3px solid #ff6b81;transition:all .2s}
.todo-item.done{opacity:.5;border-left-color:#444}
.todo-item label{display:flex;align-items:flex-start;gap:10px;cursor:pointer}
.todo-item input[type=checkbox]{width:16px;height:16px;margin-top:2px;flex-shrink:0;cursor:pointer}
.todo-item.done span{text-decoration:line-through;color:#666}
.add-task-form{margin-top:20px;background:#1a1a30;border-radius:12px;padding:16px}
.add-task-form h3{color:#ff6b81;margin-bottom:12px}
.priority-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}
.pbtn{background:#0d0d1a;border:1px solid #2a2a40;border-radius:8px;
  color:#778;font-size:.85em;padding:8px;cursor:pointer;text-align:center;user-select:none;transition:all .2s}
.pbtn.sel{border-color:#7c5cbf;color:#fff;background:#1e1040}
.pbtn.p1.sel{border-color:#ff4757;background:#2a1010;color:#ff6b7a}
.pbtn.p2.sel{border-color:#ffa502;background:#2a2010;color:#ffbe57}
.pbtn.p3.sel{border-color:#1e90ff;background:#101a2a;color:#5aafff}
.pbtn.p4.sel{border-color:#2ed573;background:#0f2a1a;color:#5af0a0}
.text-input{width:100%;background:#0d0d1a;border:1px solid #2a2a40;border-radius:8px;
  color:#fff;font-size:.95em;padding:10px 14px;margin-bottom:10px;outline:none;font-family:inherit}
.text-input:focus{border-color:#7c5cbf}
.submit-btn{width:100%;background:linear-gradient(135deg,#7c5cbf,#5c3d9e);
  border:none;border-radius:10px;color:#fff;font-size:.95em;font-weight:600;
  padding:12px;cursor:pointer;letter-spacing:1px}
.submit-btn:active{opacity:.8}

/* Toast */
.toast{position:fixed;top:20px;left:50%;transform:translateX(-50%);
  background:#2ed573;color:#0f2a1a;font-weight:600;padding:10px 24px;
  border-radius:20px;font-size:.9em;opacity:0;transition:opacity .3s;z-index:999;pointer-events:none}
.toast.show{opacity:1}

/* News cards */
.news-section{margin-bottom:24px}
.news-section h2{border-left:3px solid #5aafff;padding-left:10px;margin-bottom:12px}
.news-item{background:#1a1a30;border-radius:10px;padding:14px;margin-bottom:10px}
.news-item h3{font-size:.95em;color:#dde;margin-bottom:6px}
.news-item p{font-size:.88em;color:#99a;line-height:1.6}
.news-item a{font-size:.8em;color:#5aafff;display:block;margin-top:6px}

/* Invest */
.stock-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-bottom:20px}
.stock-card{background:#1a1a30;border-radius:10px;padding:12px;border:1px solid #2a2a40}
.stock-card .sym{font-weight:700;color:#ffa502;font-size:.95em}
.stock-card .price{font-size:1.3em;font-weight:700;color:#fff;margin:4px 0}
.stock-card .chg.up{color:#2ed573}.stock-card .chg.dn{color:#ff4757}
.stock-card .rsi{font-size:.8em;color:#778}

/* No-report */
.no-report{text-align:center;padding:60px 20px;color:#445}
.no-report .icon{font-size:3em;margin-bottom:16px}
.no-report p{font-size:.9em}

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
// Restore last tab
const lastTab = localStorage.getItem('activeTab');
if (lastTab && document.querySelector('.tab[data-key="'+lastTab+'"]')) {
  showTab(lastTab);
}

// Toggle todo
function toggleTask(cb, idx, date) {
  fetch('/task/toggle', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'idx='+idx+'&date='+date+'&checked='+(cb.checked?'1':'0')
  }).then(() => {
    const li = cb.closest('li');
    li.classList.toggle('done', cb.checked);
    li.querySelector('span').style.textDecoration = cb.checked ? 'line-through' : '';
  });
}

// Add task
let addPriority = '普通';
function selectPriority(el) {
  document.querySelectorAll('.pbtn').forEach(b => b.classList.remove('sel'));
  el.classList.add('sel');
  addPriority = el.dataset.val;
}
function addTask() {
  const name = document.getElementById('taskInput').value.trim();
  if (!name) { document.getElementById('taskInput').focus(); return; }
  fetch('/add-task', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'name='+encodeURIComponent(name)+'&priority='+encodeURIComponent(addPriority)
  }).then(() => {
    document.getElementById('taskInput').value = '';
    showToast('任务已添加！明早 8:30 自动整理');
  });
}
document.getElementById('taskInput') && document.getElementById('taskInput')
  .addEventListener('keydown', e => { if(e.key==='Enter') addTask(); });

// Toast
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}
"""

def render_health_panel(date_str, aboutme):
    health = aboutme.get('health', {})
    weight_log = health.get('weight_log', [])
    today_rec = next((w for w in weight_log if w.get('date') == date_str), None)
    goal = health.get('goal_weight_kg', 65)
    height = health.get('height_cm', 174) / 100

    # Chart data (last 14 days)
    recent = sorted(weight_log, key=lambda x: x.get('date',''))[-14:]
    chart_labels = json.dumps([w['date'][-5:] for w in recent])
    chart_data   = json.dumps([w['kg'] for w in recent])
    goal_line    = json.dumps([goal] * len(recent))

    cards_html = ''
    if today_rec:
        w = today_rec['kg']
        bmi = round(w / (height ** 2), 1)
        diff = round(w - goal, 1)
        diff_str = ('+' if diff > 0 else '') + str(diff)
        if bmi < 18.5:   bmi_label = '偏轻'
        elif bmi < 24:   bmi_label = '正常'
        elif bmi < 28:   bmi_label = '偏重'
        else:            bmi_label = '肥胖'
        cards_html = f'''
<div class="health-cards">
  <div class="hcard"><div class="val">{w}</div><div class="lbl">今日体重 kg</div></div>
  <div class="hcard"><div class="val">{bmi}</div><div class="lbl">BMI ({bmi_label})</div></div>
  <div class="hcard"><div class="val" style="color:#ffa502">{diff_str}</div><div class="lbl">距目标 kg</div></div>
  <div class="hcard"><div class="val" style="color:#5aafff">{goal}</div><div class="lbl">目标体重</div></div>
</div>'''
        weight_form = ''
    else:
        cards_html = '<p style="color:#ffa502;margin-bottom:16px">⚠️ 今日体重未记录</p>'
        weight_form = f'''
<div class="weight-form">
  <h3>记录今日体重</h3>
  <form method="post" action="/weight">
    <input type="hidden" name="date" value="{date_str}">
    <input type="number" name="kg" step="0.1" min="30" max="200" placeholder="体重 kg" required>
    <button type="submit">记录</button>
  </form>
</div>'''

    # Markdown content
    md_text = read_md('健康z', date_str)
    md_html = ''
    if md_text:
        md_html = f'<div class="md-content">{md_to_html(md_text, "jiankang", date_str)}</div>'

    chart_html = ''
    if recent:
        chart_html = f'''
<div class="chart-wrap">
  <canvas id="wChart" height="120"></canvas>
</div>
<script>
(function(){{
  const ctx = document.getElementById('wChart');
  if(!ctx) return;
  new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: {chart_labels},
      datasets: [
        {{ label: '体重 kg', data: {chart_data}, borderColor: '#2ed573',
           backgroundColor: 'rgba(46,213,115,0.1)', tension: 0.3, pointRadius: 4 }},
        {{ label: '目标 {goal}kg', data: {goal_line}, borderColor: '#ffa502',
           borderDash: [5,5], pointRadius: 0, borderWidth: 1.5 }}
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ labels: {{ color: '#aac', font: {{ size: 11 }} }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#668' }}, grid: {{ color: '#1e1e32' }} }},
        y: {{ ticks: {{ color: '#668' }}, grid: {{ color: '#1e1e32' }}, suggestedMin: {goal-10}, suggestedMax: {goal+20} }}
      }}
    }}
  }});
}})();
</script>'''

    return f'{cards_html}{weight_form}{chart_html}{md_html}'


def render_niuma_panel(date_str):
    md_text = read_md('牛马z', date_str)
    md_html = md_to_html(md_text, 'niuma', date_str) if md_text else '<p class="empty">（今日任务清单尚未生成）</p>'

    add_form = f'''
<div class="add-task-form">
  <h3>添加新任务</h3>
  <input class="text-input" id="taskInput" type="text" placeholder="任务名称..." autocomplete="off">
  <div class="priority-row">
    <div class="pbtn p1" data-val="紧急重要" onclick="selectPriority(this)">🔥 紧急重要</div>
    <div class="pbtn p2" data-val="重要" onclick="selectPriority(this)">📌 重要不紧急</div>
    <div class="pbtn p3" data-val="紧急" onclick="selectPriority(this)">⚡ 紧急不重要</div>
    <div class="pbtn p4 sel" data-val="普通" onclick="selectPriority(this)">🗑️ 普通</div>
  </div>
  <button class="submit-btn" onclick="addTask()">+ 添加到明日清单</button>
</div>'''

    return f'<div class="md-content">{md_html}</div>{add_form}'


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


def render_panel(agent, date_str, aboutme):
    key = agent['key']
    if key == 'jiankang':
        return render_health_panel(date_str, aboutme)
    if key == 'niuma':
        return render_niuma_panel(date_str)
    if key == 'pnl':
        return render_pnl_panel(date_str)

    md_text = read_md(agent['folder'], date_str)
    if not md_text:
        return f'''<div class="no-report">
  <div class="icon">{agent["label"][0]}</div>
  <p>今日报告尚未生成</p>
  <p style="margin-top:8px;font-size:.8em">运行 scripts/agent_{key}z.bat 生成报告</p>
</div>'''
    return f'<div class="md-content">{md_to_html(md_text, key, date_str)}</div>'


def build_page(date_str):
    today = str(datetime.date.today())
    dates = available_dates()

    # Prev / next
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

    aboutme = read_aboutme()

    # Build tabs + panels
    tabs_html = ''
    panels_html = ''
    for ag in AGENTS:
        is_active = ag == AGENTS[0]
        tabs_html += f'<div class="tab{" active" if is_active else ""}" data-key="{ag["key"]}" style="--tc:{ag["color"]}" onclick="showTab(\'{ag["key"]}\')">{ag["label"]}</div>'
        panel_content = render_panel(ag, date_str, aboutme)
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


# ─── Toggle todo task ─────────────────────────────────────────────────────────

def toggle_todo(date_str, idx, checked):
    path = os.path.join(ROOT, '牛马z', f'{date_str}.md')
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()

    todo_count = 0
    for i, line in enumerate(lines):
        if re.match(r'^- \[[ x]\]', line.strip()):
            if todo_count == int(idx):
                if checked == '1':
                    lines[i] = re.sub(r'^(\s*- )\[ \]', r'\1[x]', line)
                else:
                    lines[i] = re.sub(r'^(\s*- )\[x\]', r'\1[ ]', line)
                break
            todo_count += 1

    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


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
        b = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
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

        if path == '/weight':
            date_str = params.get('date', [''])[0]
            kg_str   = params.get('kg',   [''])[0]
            try:
                kg = float(kg_str)
                height = 1.74
                bmi = round(kg / (height ** 2), 1)
                data = read_aboutme()
                wlog = data.setdefault('health', {}).setdefault('weight_log', [])
                bmih = data['health'].setdefault('bmi_history', [])
                wlog = [w for w in wlog if w.get('date') != date_str]
                bmih = [b for b in bmih if b.get('date') != date_str]
                wlog.append({'date': date_str, 'kg': kg})
                bmih.append({'date': date_str, 'bmi': bmi})
                data['health']['weight_log'] = sorted(wlog, key=lambda x: x['date'])
                data['health']['bmi_history'] = sorted(bmih, key=lambda x: x['date'])
                write_aboutme(data)
            except:
                pass
            self.redirect(f'/{date_str}#panel-jiankang')
            return

        if path == '/task/toggle':
            date_str = params.get('date', [''])[0]
            idx      = params.get('idx',  ['0'])[0]
            checked  = params.get('checked', ['0'])[0]
            toggle_todo(date_str, idx, checked)
            self.send_json({'ok': True})
            return

        if path == '/add-task':
            name     = params.get('name',     [''])[0].strip()
            priority = params.get('priority', ['普通'])[0].strip()
            if name:
                fpath = os.path.join(ROOT, 'new_tasks.txt')
                with open(fpath, 'a', encoding='utf-8') as f:
                    f.write(f'{name}|{priority}\n')
            self.send_json({'ok': True})
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
