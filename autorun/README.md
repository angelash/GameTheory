# Orchestrator + Cursor Worker 工作流系统

这是一个用于自动化技术资料收集和整理的工作流系统，通过外部 Orchestrator 和 Cursor Worker 的协作，实现"少人值守"的大规模资料收集任务。

## 系统架构

```
┌─────────────────┐
│  Orchestrator   │  ← 外部 Python 程序
│  (任务队列管理)  │
└────────┬────────┘
         │
         │ 写入批次文件
         ↓
┌─────────────────┐
│ cursor_workspace│
│   /input/       │  ← 任务输入目录
└────────┬────────┘
         │
         │ Cursor Worker 处理
         ↓
┌─────────────────┐
│ cursor_workspace│
│   /output/      │  ← 结果输出目录
└────────┬────────┘
         │
         │ Orchestrator 读取
         ↓
┌─────────────────┐
│  任务状态更新    │
│  tasks.json     │
└─────────────────┘
```

## 快速开始

### 1. 准备任务列表

编辑 `autorun/tasks.json`，添加你要收集的任务：

```json
[
  {
    "id": 1,
    "type": "topic",
    "title": "WebGPU 在浏览器中的实现原理",
    "status": "pending",
    "priority": 1,
    "description": "收集和整理 WebGPU 相关资料"
  },
  {
    "id": 2,
    "type": "url",
    "url": "https://developer.chrome.com/docs/webgpu",
    "status": "pending",
    "priority": 2,
    "title": "Chrome WebGPU 文档"
  }
]
```

**任务类型：**
- `topic`: 主题搜索（需要网络搜索收集资料）
- `url`: URL 直接访问（直接读取指定网页）
- `paper`: 学术论文（查找和整理论文内容）
- `standard`: 标准文档（处理技术标准文档）

**状态：**
- `pending`: 待处理
- `in_progress`: 处理中
- `done`: 已完成
- `failed`: 失败

### 2. 启动 Orchestrator

```bash
cd autorun
python orchestrator.py
```

Orchestrator 会：
1. 从 `tasks.json` 读取任务
2. 挑选一批待处理任务（默认 20 个）
3. 写入 `cursor_workspace/input/batch_*.json`
4. 等待 Cursor Worker 处理
5. 检测到输出后更新任务状态
6. 循环处理下一批

### 3. 在 Cursor 中处理任务

当 Orchestrator 写入输入文件后，在 Cursor 中：

**方式1：使用 @ 符号激活角色**
```
@cursor-worker 请处理 input 目录中的最新批次任务
```

**方式2：使用 PromptX action**
```
激活 cursor-worker 角色，处理当前批次任务
```

Worker 会：
1. 读取 `cursor_workspace/input/batch_*.json`
2. 逐条处理任务（搜索、阅读、整理）
3. 写入结果到 `cursor_workspace/output/batch_*.json`
4. 完成当前批次后结束

### 4. 查看结果

处理完成后：
- 结果文件：`cursor_workspace/output/batch_*.json`
- 归档文件：`cursor_workspace/archive/batch_*.json`
- 任务状态：`autorun/tasks.json`

## 配置说明

### Orchestrator 配置

编辑 `autorun/config.json`：

```json
{
  "orchestrator": {
    "task_file": "autorun/tasks.json",
    "input_dir": "cursor_workspace/input",
    "output_dir": "cursor_workspace/output",
    "archive_dir": "cursor_workspace/archive",
    "batch_size": 20,          // 每批处理的任务数
    "poll_interval": 10,        // 轮询间隔（秒）
    "output_timeout": 3600     // 输出超时（秒）
  }
}
```

### 任务优先级

- `priority: 1` - 最高优先级
- `priority: 2` - 高优先级
- `priority: 3` - 普通优先级
- 数字越小，优先级越高

## 工作流详解

### Orchestrator 工作流

```
1. 加载 tasks.json
2. 找出 status="pending" 的任务
3. 按 priority 排序，取前 batch_size 个
4. 标记为 in_progress
5. 写入 input/batch_*.json
6. 等待 output/batch_*.json 出现
7. 解析输出，归档结果
8. 标记为 done
9. 循环到步骤 2
```

### Cursor Worker 工作流

```
1. 检查 input/ 目录
2. 找到最新的 batch_*.json
3. 读取批次任务列表
4. 对每个任务：
   a. 收集资料（搜索/访问URL）
   b. 深度阅读
   c. 结构化整理
5. 写入 output/batch_*.json
6. 完成，结束本次执行
```

## 输出格式

### JSON 格式（推荐）

```json
{
  "batch_name": "batch_1234567890",
  "processed_at": "2025-12-11T10:00:00",
  "results": [
    {
      "id": 1,
      "status": "success",
      "result": {
        "title": "任务标题",
        "background": "背景信息",
        "core_concepts": "核心概念",
        "key_apis": "关键API/实现",
        "common_pitfalls": "常见问题",
        "references": [
          {"url": "https://...", "description": "..."}
        ]
      }
    }
  ],
  "summary": {
    "total": 3,
    "success": 3,
    "failed": 0
  }
}
```

## 常见问题

### Q: Orchestrator 一直等待输出怎么办？

A: 检查：
1. Cursor Worker 是否已激活并处理任务
2. 输出文件名是否与批次名称匹配
3. 输出文件是否在正确的目录（`cursor_workspace/output/`）

如果超时，可以选择：
- 回滚任务状态为 pending（重新处理）
- 标记为 failed（跳过）
- 继续等待（手动检查）

### Q: 如何暂停和恢复？

A: 
- 暂停：Ctrl+C 停止 Orchestrator
- 恢复：重新运行 `python orchestrator.py`，会从上次状态继续

### Q: 如何重新处理失败的任务？

A: 编辑 `tasks.json`，将失败任务的 `status` 改为 `pending`，然后重新运行 Orchestrator。

### Q: 可以调整批次大小吗？

A: 可以，编辑 `autorun/config.json` 中的 `batch_size`，或直接修改 `orchestrator.py` 中的 `BATCH_SIZE` 常量。

## 扩展功能

### 1. Git 集成

可以让 Orchestrator 在写入输入文件后自动 commit 和 push：

```python
import subprocess

def git_commit_and_push(file_path):
    subprocess.run(["git", "add", str(file_path)])
    subprocess.run(["git", "commit", "-m", f"Add batch: {file_path.name}"])
    subprocess.run(["git", "push"])
```

### 2. 质量评估

可以在 Worker 输出后，再用一个模型复查结果质量。

### 3. 自动归档到知识库

解析输出后，自动写入到项目的知识库目录（如 `docs/`）。

## 文件结构

```
autorun/
├── orchestrator.py      # Orchestrator 主程序
├── tasks.json           # 任务列表
├── config.json          # 配置文件
└── README.md           # 本文档

cursor_workspace/
├── input/              # 任务输入目录
├── output/             # 结果输出目录
└── archive/            # 归档目录

.promptx/resource/role/cursor-worker/
└── cursor-worker.role.md  # Worker 角色定义
```

## 注意事项

⚠️ **重要约束：**
- Cursor Worker **不要自己循环任务列表**
- Worker **不要修改 tasks.json**
- Worker **只处理当前批次，不要查找下一批**
- 输出文件名必须与批次名称匹配

✅ **最佳实践：**
- 定期备份 `tasks.json`
- 检查输出文件格式是否正确
- 失败的任务及时回滚或标记
- 保持目录结构清晰

## 技术支持

如有问题，请检查：
1. Python 版本（建议 3.8+）
2. 文件路径是否正确
3. 目录权限是否足够
4. Cursor Worker 角色是否正确激活

---

**开始使用：**
1. 编辑 `tasks.json` 添加任务
2. 运行 `python orchestrator.py`
3. 在 Cursor 中激活 `@cursor-worker` 处理任务
4. 查看结果并继续下一批

