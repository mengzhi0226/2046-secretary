"""
本地任务输入服务器
运行后在浏览器或手机打开 http://<本机IP>:8080 即可添加任务
"""
import sys
import os
import json
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

TASKS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "new_tasks.txt")
PORT = 8080

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>牛马z 任务输入</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: #0f0f1a;
    color: #e0e0e0;
    min-height: 100vh;
    padding: 20px;
  }
  .container { max-width: 480px; margin: 0 auto; }
  h1 {
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 4px;
    letter-spacing: 1px;
  }
  .subtitle { font-size: 13px; color: #666; margin-bottom: 24px; }
  .card {
    background: #1a1a2e;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid #2a2a40;
  }
  label { font-size: 13px; color: #888; display: block; margin-bottom: 8px; }
  input[type=text], textarea, select {
    width: 100%;
    background: #0f0f1a;
    border: 1px solid #2a2a40;
    border-radius: 10px;
    color: #fff;
    font-size: 16px;
    padding: 12px 14px;
    outline: none;
    transition: border 0.2s;
    font-family: inherit;
  }
  input[type=text]:focus, textarea:focus, select:focus {
    border-color: #7c5cbf;
  }
  textarea { resize: none; height: 80px; }
  select option { background: #1a1a2e; }
  .priority-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 14px;
  }
  .priority-btn {
    background: #0f0f1a;
    border: 1px solid #2a2a40;
    border-radius: 10px;
    color: #888;
    font-size: 13px;
    padding: 10px 8px;
    cursor: pointer;
    text-align: center;
    transition: all 0.2s;
    user-select: none;
  }
  .priority-btn.selected {
    border-color: #7c5cbf;
    color: #fff;
    background: #2a1a4a;
  }
  .priority-btn.p1.selected { border-color: #ff4757; background: #2a1010; color: #ff6b7a; }
  .priority-btn.p2.selected { border-color: #ffa502; background: #2a2010; color: #ffbe57; }
  .priority-btn.p3.selected { border-color: #1e90ff; background: #101a2a; color: #5aafff; }
  .priority-btn.p4.selected { border-color: #2ed573; background: #0f2a1a; color: #5af0a0; }
  .submit-btn {
    width: 100%;
    background: linear-gradient(135deg, #7c5cbf, #5c3d9e);
    border: none;
    border-radius: 12px;
    color: #fff;
    font-size: 16px;
    font-weight: 600;
    padding: 14px;
    cursor: pointer;
    margin-top: 8px;
    transition: opacity 0.2s;
    letter-spacing: 1px;
  }
  .submit-btn:active { opacity: 0.8; }
  .tasks-section { margin-top: 24px; }
  .tasks-title { font-size: 14px; color: #666; margin-bottom: 12px; }
  .task-item {
    background: #1a1a2e;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 8px;
    border-left: 3px solid #7c5cbf;
    font-size: 14px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 8px;
  }
  .task-text { flex: 1; word-break: break-all; }
  .task-tag {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 6px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .tag-p1 { background: #2a1010; color: #ff6b7a; }
  .tag-p2 { background: #2a2010; color: #ffbe57; }
  .tag-p3 { background: #101a2a; color: #5aafff; }
  .tag-p4 { background: #0f2a1a; color: #5af0a0; }
  .toast {
    position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
    background: #2ed573; color: #0f2a1a; font-weight: 600;
    padding: 10px 24px; border-radius: 20px; font-size: 14px;
    opacity: 0; transition: opacity 0.3s; z-index: 999;
    pointer-events: none;
  }
  .toast.show { opacity: 1; }
  .empty { text-align: center; color: #444; font-size: 13px; padding: 20px; }
</style>
</head>
<body>
<div class="container">
  <h1>牛马z 任务输入</h1>
  <p class="subtitle">明早 8:30 牛马z 会自动整理到日程</p>

  <div class="card">
    <label>任务名称</label>
    <input type="text" id="taskName" placeholder="输入任务..." autocomplete="off">

    <div style="margin-top:14px">
      <label>优先级</label>
      <div class="priority-row">
        <div class="priority-btn p1" data-val="紧急重要" onclick="selectPriority(this)">🔥 紧急重要</div>
        <div class="priority-btn p2" data-val="重要" onclick="selectPriority(this)">📌 重要不紧急</div>
        <div class="priority-btn p3" data-val="紧急" onclick="selectPriority(this)">⚡ 紧急不重要</div>
        <div class="priority-btn p4 selected" data-val="普通" onclick="selectPriority(this)">🗑️ 普通</div>
      </div>
    </div>
  </div>

  <button class="submit-btn" onclick="addTask()">+ 添加任务</button>

  <div class="tasks-section">
    <div class="tasks-title">待处理任务（明早自动处理）</div>
    <div id="taskList">TASK_LIST_PLACEHOLDER</div>
  </div>
</div>

<div class="toast" id="toast">已添加！</div>

<script>
  let priority = '普通';
  function selectPriority(el) {
    document.querySelectorAll('.priority-btn').forEach(b => b.classList.remove('selected'));
    el.classList.add('selected');
    priority = el.dataset.val;
  }
  function addTask() {
    const name = document.getElementById('taskName').value.trim();
    if (!name) { document.getElementById('taskName').focus(); return; }
    fetch('/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'name=' + encodeURIComponent(name) + '&priority=' + encodeURIComponent(priority)
    }).then(r => r.json()).then(d => {
      if (d.ok) {
        document.getElementById('taskName').value = '';
        showToast('已添加！');
        setTimeout(() => location.reload(), 800);
      }
    });
  }
  document.getElementById('taskName').addEventListener('keydown', e => {
    if (e.key === 'Enter') addTask();
  });
  function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2000);
  }
</script>
</body>
</html>"""

TAG_MAP = {"紧急重要": "tag-p1", "重要": "tag-p2", "紧急": "tag-p3", "普通": "tag-p4"}
LABEL_MAP = {"紧急重要": "🔥 紧急重要", "重要": "📌 重要", "紧急": "⚡ 紧急", "普通": "🗑️ 普通"}

def read_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    tasks = []
    with open(TASKS_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if '|' in line:
                parts = line.split('|', 1)
                tasks.append({"name": parts[0].strip(), "priority": parts[1].strip()})
            else:
                tasks.append({"name": line, "priority": "普通"})
    return tasks

def render_tasks(tasks):
    if not tasks:
        return '<div class="empty">暂无待处理任务</div>'
    html = ""
    for t in tasks:
        p = t.get("priority", "普通")
        tag = TAG_MAP.get(p, "tag-p4")
        label = LABEL_MAP.get(p, p)
        html += f'<div class="task-item"><span class="task-text">{t["name"]}</span><span class="task-tag {tag}">{label}</span></div>'
    return html

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs

    def do_GET(self):
        tasks = read_tasks()
        task_html = render_tasks(tasks)
        page = HTML.replace("TASK_LIST_PLACEHOLDER", task_html)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode('utf-8'))

    def do_POST(self):
        if self.path == '/add':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            params = parse_qs(body)
            name = params.get('name', [''])[0].strip()
            priority = params.get('priority', ['普通'])[0].strip()
            if name:
                with open(TASKS_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{name}|{priority}\n")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

if __name__ == "__main__":
    ip = get_local_ip()
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[牛马z 任务服务器]")
    print(f"  电脑访问: http://localhost:{PORT}")
    print(f"  手机访问: http://{ip}:{PORT}  (需同一 WiFi)")
    print(f"  按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
