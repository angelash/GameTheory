按「**真的要落地一个外部 Orchestrator + Cursor Worker 系统**」来讲，尽量说到能开工那种程度。

------

## 0. 先定清楚目标

你的硬约束：

- 大模型调用质量 → **必须通过 Cursor**（内置模型 + IDE 语境）。
- 任务 → **大量网络资料收集 + 阅读 + 结构化整理**，高度依赖 LLM。
- 希望 → **无人值守 / 至少“少人值守”，能把几百个任务慢慢跑完**。

因为 Cursor 本身没有“后台守护进程 + API”，所以我们只能做：

> **外部程序负责：排队、记录、喂任务、收结果。 Cursor 负责：把当前这一批任务做精做透。**

所以 Orchestrator 的角色就是：
 **一个任务队列管理 + 文件/仓库读写的小服务**。

------

## 1. 整体架构怎么划分？

建议你用一个非常简单的三层划分：

1. **任务层（Task Layer）**
   - 存所有「要收集整理的目标」：每个目标可以是一个技术关键词、一个 URL、一个主题。
   - 持久化：`tasks.json` / `tasks.csv` / 数据库都行。
2. **Orchestrator（外部程序）**
   - 负责：
     - 从任务池里找“未完成”的任务
     - 把任务写到 Cursor 工程里的某个目录（`/cursor_workspace/input/xxx`）
     - 监控 Cursor 输出目录（`/cursor_workspace/output/xxx`）
     - 更新任务状态（pending / running / done / failed）
   - 本质就是一个循环：
      **「挑任务 → 写输入 → 等输出 → 标记完成」**
3. **Cursor Worker（PromptX PM 工作流）**
   - 只负责：
     - 从 `input/` 目录读任务内容
     - 调用大模型/浏览器能力，上网搜、整理
     - 写结构化结果到 `output/`
     - 更新一个进度文件（可选）
   - **不负责循环**，每次只处理“当前一批”。

------

## 2. 任务数据结构怎么设计？

举个最实用的 `tasks.json` 例子（放在 AI Studio / Orchestrator 那边）：

```
[
  {
    "id": 1,
    "type": "topic",
    "title": "WebGPU 在浏览器中的实现原理",
    "status": "pending",
    "priority": 1
  },
  {
    "id": 2,
    "type": "url",
    "url": "https://developer.chrome.com/docs/webgpu",
    "status": "pending",
    "priority": 2
  }
]
```

字段建议：

- `id`: 唯一标识。
- `type`: `topic` / `url` / `paper` / `standard`…
- `title` / `url`: 具体任务内容。
- `status`: `pending` / `in_progress` / `done` / `failed`。
- `priority`: 方便以后做优先级调度。

------

## 3. Orchestrator 负责做什么？（流程拆开说）

最小闭环可以这样：

1. **加载任务池（tasks.json）**
2. 找出 `status == "pending"` 的任务，按 priority 截一段（比如一次 20 条）
3. 把这 20 条写到 Cursor 工程里的一个输入文件，例如：
    `cursor_workspace/input/batch_2025_12_11_01.json`
4. 顺便在 tasks.json 里把这 20 条的状态改成：`in_progress`
5. 暂停/等待 → 等 Cursor 处理完：
   - Cursor Worker 会把结果写到：
      `cursor_workspace/output/batch_2025_12_11_01.md` 或 `.json`
6. Orchestrator 检测到这个输出文件：
   - 解析结果，存档（比如 AI Studio 自己的知识库）
   - 把这 20 条任务状态改为：`done`
7. 回到第 2 步，继续下一批，直到没有 `pending`

> 注意：这整个循环 **不需要操控 Cursor 内部**，只是在搞文件/任务状态而已。

------

## 4. 和 Cursor 的集成方式：两条路

### 4.1 最现实的方案：**共享目录 + 人手点一下**

- Orchestrator 和 Cursor **共享同一个工程目录**（本地或通过 git）。
- Orchestrator 写入/更新 `input/batch_xxx.json`。
- 你空了就打开 Cursor，对着该工程运行一次 PM 工作流：
  - 工作流逻辑：
    - 找最新的 `input/batch_xxx.json`
    - 逐条处理任务（上网搜、阅读、多轮对话都在这轮里做完）
    - 写结果到 `output/batch_xxx.md`（按统一格式）
    - 结束
- 随后 Orchestrator 读输出、更新状态。

优点：

- 不用 hack Cursor，不用等官方 API。
- 一次点一下按钮，就能让 Cursor 做几十条任务。
- 你只在“按开始”上投入人工，其他环节全自动。

------

### 4.2 稍微更自动一点：**Git + Cursor Auto Sync**

如果你愿意多走一步，可以改为：

- Orchestrator 不直接写到本地，而是：
  - 更新 `input/batch_xxx.json`
  - `git commit + git push`
- Cursor 端设置成：
  - 打开这个 repo
  - 启用 Auto Sync（或你偶尔手动 sync）
  - PM 提示词里写：
    - 当发现有新的 `input/*.json` 时自动开始工作流

结合 Cursor 的“有改动就建议你处理”的特性，你可以做到：

- 外部一更新任务，Cursor 这边很容易就被“提醒”，基本做到半自动。

------

## 5. Orchestrator 极简实现示例（Python 伪代码）

下面是一个能跑的思路（真实项目可以丢到你 AI Studio 里做成一个服务）：

```
import json
import time
from pathlib import Path

TASK_FILE = Path("tasks.json")
CURSOR_INPUT_DIR = Path("cursor_workspace/input")
CURSOR_OUTPUT_DIR = Path("cursor_workspace/output")

BATCH_SIZE = 20

def load_tasks():
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def pick_batch(tasks, batch_size):
    pending = [t for t in tasks if t["status"] == "pending"]
    return pending[:batch_size]

def mark_in_progress(tasks, batch):
    ids = {t["id"] for t in batch}
    for t in tasks:
        if t["id"] in ids:
            t["status"] = "in_progress"

def mark_done(tasks, batch):
    ids = {t["id"] for t in batch}
    for t in tasks:
        if t["id"] in ids:
            t["status"] = "done"

def write_input_file(batch, batch_name):
    CURSOR_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    input_path = CURSOR_INPUT_DIR / f"{batch_name}.json"
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
    return input_path

def wait_for_output(batch_name, timeout=3600):
    CURSOR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CURSOR_OUTPUT_DIR / f"{batch_name}.json"
    start = time.time()
    while time.time() - start < timeout:
        if output_path.exists():
            return output_path
        time.sleep(10)  # 每 10 秒轮询一次
    return None

def main_loop():
    while True:
        tasks = load_tasks()
        batch = pick_batch(tasks, BATCH_SIZE)
        if not batch:
            print("All tasks done.")
            break

        batch_name = f"batch_{int(time.time())}"
        mark_in_progress(tasks, batch)
        save_tasks(tasks)

        input_file = write_input_file(batch, batch_name)
        print(f"Written input for {len(batch)} tasks to {input_file}")
        print("请在 Cursor 中运行 PM Workflow 处理这一批任务...")

        output_file = wait_for_output(batch_name)
        if output_file is None:
            print("等待输出超时，可以人工检查。")
            # 这里你可以选择把这批任务回滚为 pending
            continue

        # TODO: 解析 output_file，按需写入知识库 / Markdown / DB
        print(f"Got output from {output_file}")
        mark_done(tasks, batch)
        save_tasks(tasks)

        # 可以选择短暂休息，防止一直顶满
        time.sleep(5)

if __name__ == "__main__":
    main_loop()
```

这个脚本的核心逻辑就是：

- 找 `pending`
- 写 `input/`
- 等 `output/`
- 标记 `done`
- 循环

你后面再把：

- `main_loop()` 变成一个 AI Studio 里的“周期任务”
- 输出解析部分接到你们的知识库 / 向量库 / 文档系统

就能完整变成一个「自动资料收集和归档流水线」。

------

## 6. Cursor 侧 PM / Worker 要怎么写？

重点是两句话：

1. **不要自己循环任务列表**（那又会撞迭代上限）
2. **专注把当前这批 input 文件做完**

一个典型 PM 提示词结构：

```
你是“技术资料整理 Worker”。

输入：
- 工程目录中存在一个 JSON 文件：/input/{batch_name}.json
- 其中是若干个任务，每个任务包含 id、type、title/url 等字段。

你的职责：
1. 逐条读取任务（顺序处理即可，不要自己去找下一批任务）。
2. 对于每条任务：
   - 上网搜索（使用 Cursor 提供的浏览能力）
   - 阅读若干权威资料
   - 整理成统一结构：
     - 背景
     - 核心概念
     - 关键 API / 实现思路
     - 常见坑
     - 参考链接（带一句话说明）
3. 将所有任务的结果写入 /output/{batch_name}.json，结构为：
   - 每个任务一项，包含 id 与 result 字段。
4. 不要尝试自己继续下一批任务，也不要试图修改 tasks.json。
5. 完成后只需要简单总结一下这一批的情况，然后结束本次执行。
```

实际落地时，你可以结合 PromptX 的 `role + tools + plan` 模板，再包一层“对接 input/output 文件”的习惯句式。

------

## 7. 整体现实度总结

- **技术上可行**：你现有的技术栈（AI Studio + MCP + LangGraph + Node/Python）完全够用。
- **成本可控**：最小版 orchestrator 就是一个读写 JSON + 文件轮询的小脚本。
- **扩展空间大**：
  - 后面可以把“等待输出”改成：
    - 监听 git hook
    - 或者用 MCP 的文件系统工具，让别的 Agent 也能用这套工作流
  - 还可以加：
    - 重试策略
    - 质量评估（再用一个模型复查）
    - 自动写知识库 Wiki / notion / Confluence