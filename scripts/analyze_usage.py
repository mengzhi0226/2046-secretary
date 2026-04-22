"""
财务z — Claude Code 本地会话用量分析
扫描 .claude/projects/ JSONL 文件，估算 token 用量和成本
"""
import sys, os, json, re, datetime, glob

sys.stdout.reconfigure(encoding='utf-8')

HOME = os.path.expanduser('~')
PROJECTS_DIR = os.path.join(HOME, '.claude', 'projects')
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Sonnet 4.x pricing (USD per million tokens, approximate)
INPUT_COST_PER_M  = 3.0
OUTPUT_COST_PER_M = 15.0

def estimate_tokens(text):
    return max(1, len(str(text)) // 4)

def analyze_jsonl(path):
    input_tokens = 0
    output_tokens = 0
    message_count = 0
    tool_calls = {}
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                msg = obj.get('message', {})
                role = msg.get('role', '')
                content = msg.get('content', '')
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            btype = block.get('type', '')
                            if btype == 'tool_use':
                                name = block.get('name', 'unknown')
                                tool_calls[name] = tool_calls.get(name, 0) + 1
                            text = block.get('text', '') or block.get('input', '') or ''
                            toks = estimate_tokens(str(text))
                            if role == 'user':
                                input_tokens += toks
                            else:
                                output_tokens += toks
                elif isinstance(content, str):
                    toks = estimate_tokens(content)
                    if role == 'user':
                        input_tokens += toks
                    else:
                        output_tokens += toks
                message_count += 1
    except Exception:
        pass
    return input_tokens, output_tokens, message_count, tool_calls

def get_file_month(path):
    try:
        mtime = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m')
    except Exception:
        return 'unknown'

def main():
    now = datetime.datetime.now()
    target_month = now.strftime('%Y-%m')
    if len(sys.argv) > 1:
        target_month = sys.argv[1]

    print(f'[财务z] 扫描 {PROJECTS_DIR}')
    print(f'[财务z] 分析月份：{target_month}')

    if not os.path.isdir(PROJECTS_DIR):
        print(f'[财务z] 错误：找不到 {PROJECTS_DIR}')
        sys.exit(1)

    # Find all JSONL files
    all_files = glob.glob(os.path.join(PROJECTS_DIR, '**', '*.jsonl'), recursive=True)
    month_files = [f for f in all_files if get_file_month(f) == target_month]
    all_month_files = [f for f in all_files]  # for total stats

    print(f'[财务z] 找到 {len(month_files)} 个本月会话文件（共 {len(all_files)} 个）')

    # Analyze month files
    total_in, total_out, total_msgs = 0, 0, 0
    all_tool_calls = {}
    session_stats = []

    for fpath in month_files:
        inp, out, msgs, tools = analyze_jsonl(fpath)
        total_in  += inp
        total_out += out
        total_msgs += msgs
        for k, v in tools.items():
            all_tool_calls[k] = all_tool_calls.get(k, 0) + v
        size = os.path.getsize(fpath)
        session_stats.append({
            'path': fpath,
            'name': os.path.basename(fpath)[:40],
            'input': inp, 'output': out,
            'msgs': msgs, 'size': size
        })

    total_tokens = total_in + total_out
    cost_usd = (total_in / 1_000_000 * INPUT_COST_PER_M +
                total_out / 1_000_000 * OUTPUT_COST_PER_M)

    # Read Memory stats
    memory_dir = os.path.join(HOME, '.claude', 'projects',
                              os.path.basename(os.path.normpath(REPO_ROOT)).replace(' ', '-').replace('\\', '-'))
    memory_md = os.path.join(REPO_ROOT, 'MEMORY.md')
    memory_files = glob.glob(os.path.join(REPO_ROOT, 'memory', '*.md')) if os.path.isdir(os.path.join(REPO_ROOT, 'memory')) else []

    memory_entries = 0
    memory_last_update = None
    if os.path.exists(memory_md):
        with open(memory_md, encoding='utf-8', errors='ignore') as f:
            lines = [l for l in f.readlines() if l.strip().startswith('-')]
            memory_entries = len(lines)
        memory_last_update = datetime.datetime.fromtimestamp(os.path.getmtime(memory_md))

    # Read CLAUDE.md stats
    claude_md = os.path.join(REPO_ROOT, 'CLAUDE.md')
    claude_md_lines = 0
    if os.path.exists(claude_md):
        with open(claude_md, encoding='utf-8', errors='ignore') as f:
            claude_md_lines = sum(1 for _ in f)

    # Top 5 sessions by token count
    top5 = sorted(session_stats, key=lambda x: x['input'] + x['output'], reverse=True)[:5]

    # Top tools
    top_tools = sorted(all_tool_calls.items(), key=lambda x: x[1], reverse=True)[:8]

    # Build report
    days_since_mem = (now - memory_last_update).days if memory_last_update else '?'
    mem_update_str = memory_last_update.strftime('%Y-%m-%d') if memory_last_update else '未知'

    top5_rows = '\n'.join(
        f'| {i+1} | {s["name"]} | {(s["input"]+s["output"]):,} | ${((s["input"]/1e6*INPUT_COST_PER_M)+(s["output"]/1e6*OUTPUT_COST_PER_M)):.2f} | {s["msgs"]} |'
        for i, s in enumerate(top5)
    )
    tool_rows = '\n'.join(
        f'| {name} | {cnt} |' for name, cnt in top_tools
    )

    suggestions = []
    if memory_entries > 30:
        suggestions.append(f'- [ ] Memory 共 {memory_entries} 条，建议清理过期条目（目标 <20 条）')
    if claude_md_lines > 150:
        suggestions.append(f'- [ ] CLAUDE.md 已 {claude_md_lines} 行，建议精简至 <100 行')
    heavy = [s for s in session_stats if (s['input'] + s['output']) > 100_000]
    if heavy:
        suggestions.append(f'- [ ] {len(heavy)} 个会话超过 100k tokens，下次使用前考虑 /compact')
    if cost_usd > 50:
        suggestions.append(f'- [ ] 本月成本 ${cost_usd:.2f} 偏高，检查是否有可批处理的重复任务')
    if not suggestions:
        suggestions.append('- ✅ 用量健康，无明显优化点')

    report = f"""# 💰 财务z — Claude 用量报告 {target_month}

## 用量概览

| 指标 | 数值 |
|------|------|
| 本月会话数 | {len(month_files)} |
| 本月消息数 | {total_msgs:,} |
| 估算输入 token | {total_in:,} |
| 估算输出 token | {total_out:,} |
| 估算总 token | {total_tokens:,} |
| 估算成本（USD）| ${cost_usd:.2f} |

> 成本基于 Sonnet 4.x 定价估算：输入 $3/M token，输出 $15/M token。实际以 Anthropic 账单为准。

## 最活跃会话 Top 5

| # | 文件名 | 估算 token | 估算成本 | 消息数 |
|---|--------|-----------|---------|--------|
{top5_rows if top5_rows else '| — | 暂无数据 | — | — | — |'}

## 最常用工具 Top 8

| 工具 | 调用次数 |
|------|---------|
{tool_rows if tool_rows else '| 暂无数据 | — |'}

## Memory 健康度

| 项目 | 状态 |
|------|------|
| MEMORY.md 条目数 | {memory_entries} |
| 最近更新 | {mem_update_str}（{days_since_mem} 天前）|
| memory/ 文件数 | {len(memory_files)} |
| CLAUDE.md 行数 | {claude_md_lines} |

## 优化建议

{chr(10).join(suggestions)}

---
*分析时间：{now.strftime('%Y-%m-%d %H:%M')} | 财务z*
"""

    # Write report
    out_dir = os.path.join(REPO_ROOT, '财务z')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{target_month}.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f'[财务z] 报告已生成：{out_path}')
    print(f'[财务z] 本月估算用量：{total_tokens:,} tokens ≈ ${cost_usd:.2f} USD')
    return out_path

if __name__ == '__main__':
    main()
