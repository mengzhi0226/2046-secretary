"""
Notion 任务库读写脚本
用法：
  python scripts/notion_tasks.py read        # 读取所有待办任务，输出给 agent
  python scripts/notion_tasks.py add "任务名"  # 添加新任务
  python scripts/notion_tasks.py done "任务名" # 标记任务为完成

环境变量：
  NOTION_TOKEN       — Integration Secret
  NOTION_DATABASE_ID — 数据库 ID
"""
import sys
import os
import json
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')

TOKEN = os.environ.get("NOTION_TOKEN", "")
DB_ID = os.environ.get("NOTION_DATABASE_ID", "")
BASE  = "https://api.notion.com/v1"

def headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def request(method, path, data=None):
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers(), method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR {e.code}: {e.read().decode()}")
        return None

def read_tasks():
    """读取所有未完成任务，按优先级分组输出"""
    result = request("POST", f"/databases/{DB_ID}/query", {
        "filter": {
            "property": "状态",
            "select": {"does_not_equal": "完成"}
        },
        "sorts": [{"property": "优先级", "direction": "ascending"}]
    })
    if not result:
        return

    tasks = result.get("results", [])
    if not tasks:
        print("（暂无待办任务）")
        return

    by_priority = {}
    for t in tasks:
        props = t["properties"]
        name = ""
        if props.get("名称", {}).get("title"):
            name = props["名称"]["title"][0]["plain_text"]
        status = props.get("状态", {}).get("select", {})
        status = status.get("name", "待办") if status else "待办"
        priority = props.get("优先级", {}).get("select", {})
        priority = priority.get("name", "普通") if priority else "普通"
        due = props.get("截止日期", {}).get("date", {})
        due = due.get("start", "") if due else ""
        page_id = t["id"]

        if priority not in by_priority:
            by_priority[priority] = []
        by_priority[priority].append({
            "id": page_id,
            "name": name,
            "status": status,
            "due": due
        })

    print("=== NOTION 任务库（未完成）===\n")
    for priority in ["紧急重要", "重要", "紧急", "普通"]:
        items = by_priority.get(priority, [])
        if items:
            print(f"[{priority}]")
            for t in items:
                due_str = f"  截止:{t['due']}" if t['due'] else ""
                print(f"  - {t['name']} ({t['status']}){due_str}")
            print()

def add_task(name, priority="普通", due=None):
    """添加新任务"""
    props = {
        "名称": {"title": [{"text": {"content": name}}]},
        "状态": {"select": {"name": "待办"}},
        "优先级": {"select": {"name": priority}}
    }
    if due:
        props["截止日期"] = {"date": {"start": due}}

    result = request("POST", "/pages", {
        "parent": {"database_id": DB_ID},
        "properties": props
    })
    if result:
        print(f"[OK] 已添加任务：{name}")

def mark_done(name):
    """将匹配名称的任务标记为完成"""
    result = request("POST", f"/databases/{DB_ID}/query", {
        "filter": {
            "property": "名称",
            "title": {"contains": name}
        }
    })
    if not result or not result.get("results"):
        print(f"未找到任务：{name}")
        return
    for t in result["results"]:
        request("PATCH", f"/pages/{t['id']}", {
            "properties": {
                "状态": {"select": {"name": "完成"}}
            }
        })
        task_name = t["properties"]["名称"]["title"][0]["plain_text"]
        print(f"[OK] 已完成：{task_name}")

if __name__ == "__main__":
    if not TOKEN or not DB_ID:
        print("ERROR: 请设置 NOTION_TOKEN 和 NOTION_DATABASE_ID 环境变量")
        sys.exit(1)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "read"
    if cmd == "read":
        read_tasks()
    elif cmd == "add" and len(sys.argv) > 2:
        priority = sys.argv[3] if len(sys.argv) > 3 else "普通"
        add_task(sys.argv[2], priority)
    elif cmd == "done" and len(sys.argv) > 2:
        mark_done(sys.argv[2])
    else:
        print("用法: python notion_tasks.py [read|add <名称> [优先级]|done <名称>]")
