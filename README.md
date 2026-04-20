# 2046 孟之 AI 秘书团队

一个由 4 个 AI Agent 组成的个人助理系统，每天自动执行、生成报告并发送到邮箱。

---

## 团队成员

| Agent | 运行时间 | 职责 | 输出文件 |
|---|---|---|---|
| 新闻z | 每天 07:00 SGT | 抓取 AI、烟草、工厂数字化新闻，生成简报 | `YYYY-MM-DD/news.md` |
| 投资z | 每天 07:30 SGT | 分析七巨头+MU股票，给出期权交易建议 | `YYYY-MM-DD/invest.md` |
| 健康z | 每天 08:00 SGT | 检查体重记录，计算 BMI，生成健康报告 | `YYYY-MM-DD/health.md` |
| 牛马z | 每天 08:30 SGT | 整理任务清单，按艾森豪威尔矩阵分类 | `YYYY-MM-DD/todo.md` |

所有报告自动发送至 **mengzhi0226@gmail.com**。

---

## 文件结构

```
2046孟之CC/
├── CLAUDE.md                  # 所有 Agent 的共享上下文（每次会话自动加载）
├── aboutme.json               # 个人数据中心（健康/财务/兴趣）
├── scripts/
│   ├── send_email_resend.py   # 邮件发送脚本（Resend API）
│   └── send_email.py          # 备用 SMTP 邮件脚本
├── .claude/
│   └── settings.json          # 权限配置 + 本地 SMTP 环境变量（不上传 GitHub）
├── new_tasks.txt              # 临时文件：在此写入新任务，牛马z 每天自动读取并删除
└── YYYY-MM-DD/                # 每天自动创建的日期目录
    ├── news.md
    ├── invest.md
    ├── health.md
    └── todo.md
```

---

## 如何修改与迭代

### 修改个人数据（最常用）

**文件：[aboutme.json](aboutme.json)**

| 想改什么 | 对应字段 |
|---|---|
| 增减自选股 | `finance.watchlist` |
| 修改目标体重 | `health.goal_weight_kg` |
| 添加周期性任务 | `todo.recurring` |
| 修改新闻关注主题 | `interests.news_topics` |
| 记录今日体重 | `health.weight_log`（或直接告诉 Claude「今天体重 XX kg」）|

修改后提交到 GitHub，Agent 下次运行时自动读取最新数据。

---

### 修改 Agent 的行为与报告格式

**入口：[claude.ai/code/scheduled](https://claude.ai/code/scheduled)**

每个 Agent 的完整指令（Prompt）存储在 RemoteTrigger 中。点击对应触发器即可编辑：

| 想改什么 | 操作 |
|---|---|
| 报告格式/章节结构 | 编辑对应触发器的 Prompt |
| 新闻搜索关键词 | 编辑 新闻z 的 Prompt |
| 增加/删除分析的股票 | 编辑 投资z 的 Prompt（或修改 `aboutme.json`）|
| 健康报告的建议内容 | 编辑 健康z 的 Prompt |
| 任务分类逻辑 | 编辑 牛马z 的 Prompt |
| 运行时间 | 修改触发器的 Cron 表达式（UTC 时间） |
| 暂停某个 Agent | 在触发器页面将其 Disable |

---

### 修改邮件主题/收件人

**文件：触发器 Prompt 中的 Bash 命令**

当前配置：
- 收件人：`mengzhi0226@gmail.com`（`EMAIL_TO`）
- 发件人：`onboarding@resend.dev`（Resend 免费测试地址）
- API Key：存储在各触发器 Prompt 中

> 如果 Resend API Key 需要更换，在 [resend.com/api-keys](https://resend.com/api-keys) 生成新 Key，然后逐一更新 4 个触发器的 Prompt。

---

### 添加新任务给牛马z

在项目根目录创建 `new_tasks.txt`，每行写一个任务：

```
明天下午开会准备PPT
回复李总的邮件
更新季度报告
```

牛马z 每天 08:30 自动读取、分类并删除该文件。

---

### 记录体重（触发健康z完整报告）

在 Claude Code 中直接说：

> 「今天体重 71.5 kg」

Claude 会更新 `aboutme.json` 中的 `weight_log`，健康z 第二天将自动生成含 BMI 和趋势的完整报告。

---

### 修改项目共享上下文

**文件：[CLAUDE.md](CLAUDE.md)**

所有 Agent 在每次运行时都会自动加载这个文件。适合存放：
- 用户偏好和背景信息
- Agent 之间共享的规则
- 项目目录结构说明

---

## 技术架构

- **运行环境**：Anthropic Cloud（RemoteTrigger）
- **代码仓库**：[github.com/mengzhi0226/2046-secretary](https://github.com/mengzhi0226/2046-secretary)（私有）
- **邮件服务**：[Resend](https://resend.com)（免费额度 100 封/天）
- **数据抓取**：Claude 内置 WebSearch + WebFetch
- **触发器管理**：[claude.ai/code/scheduled](https://claude.ai/code/scheduled)

---

## 快速索引

| 我想… | 去哪里 |
|---|---|
| 查看今天的报告 | 邮箱 / `YYYY-MM-DD/` 目录 |
| 增减自选股 | `aboutme.json` → `finance.watchlist` |
| 改变报告内容和格式 | claude.ai/code/scheduled → 编辑触发器 |
| 暂停某个 Agent | claude.ai/code/scheduled → Disable |
| 添加临时任务 | 创建 `new_tasks.txt` |
| 记录体重 | 告诉 Claude「今天体重 XX kg」|
| 更换邮件 API Key | 更新 4 个触发器 Prompt 中的 `RESEND_API_KEY` |
