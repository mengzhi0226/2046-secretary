# 2046 孟之 AI Secretary Team

## Project Owner
- Name: 孟之
- Email: mengzhi0226@gmail.com
- Timezone: Asia/Shanghai (UTC+8)

## Directory Layout
```
2046孟之CC/
├── aboutme.json        # 用户画像（每次先读）
├── 新闻z/              # 新闻z 历史报告（YYYY-MM-DD.md）
├── 投资z/              # 投资z 历史报告（YYYY-MM-DD.md）
├── 健康z/              # 健康z 历史报告（YYYY-MM-DD.md）
├── 牛马z/              # 牛马z 历史任务清单（YYYY-MM-DD.md）
├── new_tasks.txt       # 用户手动添加的新任务（任务名|优先级）
├── 问新闻z.bat         # 随时提问新闻z
├── 问投资z.bat         # 随时提问投资z
├── 问健康z.bat         # 随时提问健康z
├── 问牛马z.bat         # 随时提问牛马z
└── scripts/
    ├── agent_*.bat/ps1 # 定时自动运行脚本
    ├── send_email.py   # Gmail SMTP 发件
    ├── get_stock_data.py
    ├── task_server.py  # 手机任务输入服务器
    └── start_task_server.bat
```

## Agent Roster
| Agent | 定时 | 输出目录 | 随时提问 |
|---|---|---|---|
| 新闻z | 07:00 SGT | `新闻z/` | 双击 `问新闻z.bat` |
| 投资z | 07:30 SGT | `投资z/` | 双击 `问投资z.bat` |
| 健康z | 08:00 SGT | `健康z/` | 双击 `问健康z.bat` |
| 牛马z | 08:30 SGT | `牛马z/` | 双击 `问牛马z.bat` |

## 规则
- 每次启动先读 `aboutme.json`
- 全文简体中文
- 报告写入对应 agent 文件夹，文件名为 `YYYY-MM-DD.md`
- Email: `python scripts/send_email.py --subject "标题" --body-file 路径`
