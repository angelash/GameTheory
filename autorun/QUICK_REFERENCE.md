# 工作流规范快速参考

> 量化、可落地的规则速查表

---

## 状态定义（必须遵守）

| 状态 | 完成度 | 定义 | 操作 |
|------|-------|------|------|
| `done` | >= 0.9 | 所有验证通过 | 可标记为完成 |
| `partial` | 0.5-0.9 | 部分完成 | 继续处理 |
| `pending` | N/A | 无法执行 | 回滚或跳过 |
| `failed` | N/A | 明确失败 | 记录错误 |
| `skipped` | N/A | 需要特殊权限 | 暂时跳过 |

**关键规则：**
- ❌ 不能仅因为输出文件存在就标记为 `done`
- ✅ 必须检查输出文件中的 `status` 字段
- ✅ `partial` 状态必须继续处理，不能标记为 `done`

---

## 任务粒度规则

| 类型 | 最大文档数 | 推荐文档数 |
|------|-----------|-----------|
| content_supplement | 5 | 1 |
| create_document | 5 | 1 |
| url | 1 | 1 |
| topic | 1 | 1 |

**规则：**
- ✅ 单个任务最多5个文档
- ✅ 超过5个必须拆分
- ✅ 推荐每个文档一个任务

---

## 文档完整性标准

| 检查项 | 最低要求 | 权重 |
|--------|---------|------|
| 元数据 | 5个字段 | 20% |
| 资源链接 | 1个 | 30% |
| 摘要 | 100字 | 20% |
| 详细内容 | 200字 | 20% |
| 关键要点 | 3个 | 10% |

**完成度计算：**
```
completion_rate = (
    元数据完整度 * 0.2 +
    资源链接完整度 * 0.3 +
    摘要完整度 * 0.2 +
    内容完整度 * 0.2 +
    关键要点完整度 * 0.1
)
```

**状态判断：**
- `completion_rate >= 0.9` → `success`
- `completion_rate >= 0.5` → `partial`
- `completion_rate < 0.5` → `partial`（需要重新处理）

---

## Orchestrator 行为规则

### 状态更新规则（关键）

```python
# 错误做法（禁止）
if output_file.exists():
    mark_done(tasks, batch)  # ❌ 错误

# 正确做法（必须）
output_data = parse_output(output_file)
for result in output_data.get("results", []):
    actual_status = result.get("status")
    if actual_status == "success":
        if verify_completion(result):  # 验证通过
            mark_done(task)
        else:
            mark_partial(task)  # 验证失败
    elif actual_status == "partial":
        mark_partial(task)  # 保持 in_progress
    elif actual_status == "pending":
        rollback_to_pending(task)  # 回滚
```

### 任务挑选规则

```python
# 1. 只挑选 pending 状态
pending = [t for t in tasks if t["status"] == "pending"]

# 2. 跳过需要特殊权限的任务
pending = [t for t in pending if not t.get("requires_permission")]

# 3. 按优先级排序
pending.sort(key=lambda x: x.get("priority", 999))

# 4. 取前 BATCH_SIZE 个
batch = pending[:BATCH_SIZE]
```

---

## Worker 行为规则

### 状态判断规则

```python
# 内容补充任务
if completion_rate >= 0.9:
    status = "success"
elif completion_rate >= 0.5:
    status = "partial"
else:
    status = "partial"  # 需要重新处理

# 新建文档任务
if created_count == target_count:
    status = "success"
elif created_count > 0:
    status = "partial"
else:
    status = "pending"  # 无法执行

# 需要特殊权限
if requires_permission:
    status = "skipped"
```

### 输出格式要求

**必须包含：**
- `batch_name`: 与输入批次名称匹配
- `status`: success/partial/pending/failed/skipped
- `completion_rate`: 完成度（0-1）
- `summary`: 批次总结（数字必须匹配）

---

## 任务设计规则

### 可执行性要求

**内容补充任务：**
```json
{
  "type": "content_supplement",
  "target_files": ["doc1.md", "doc2.md"],  // 必须：最多5个
  "resource_list": "resources.json"  // 可选：资源清单
}
```

**新建文档任务：**
```json
{
  "type": "create_document",
  "document_list": [  // 必须：具体文档列表
    {"title": "...", "file": "..."}
  ],
  "target_count": 5  // 可选：目标数量
}
```

**需要特殊权限：**
```json
{
  "type": "content_supplement",
  "requires_permission": true,  // 标记需要权限
  "status": "skipped",  // 必须标记为 skipped
  "reason": "需要GDC Vault账号"
}
```

---

## 验证工具使用

```bash
# 验证任务文件
python autorun/task_validator.py

# 检查状态
python autorun/check_status.py

# 检查2025年任务
python autorun/check_2025_tasks.py
```

---

## 常见错误和修正

### 错误1：状态标记错误

**错误：**
```python
if output_file.exists():
    mark_done(tasks, batch)  # ❌
```

**修正：**
```python
output_data = parse_output(output_file)
for result in output_data.get("results", []):
    if result.get("status") == "success":
        mark_done(task)  # ✅
```

### 错误2：任务粒度太大

**错误：**
```json
{
  "target_files": ["doc1.md", ..., "doc10.md"]  // ❌ 10个文档
}
```

**修正：**
```json
// 拆分为多个任务，每个最多5个
{
  "target_files": ["doc1.md", "doc2.md", "doc3.md", "doc4.md", "doc5.md"]
}
{
  "target_files": ["doc6.md", "doc7.md", "doc8.md", "doc9.md", "doc10.md"]
}
```

### 错误3：缺少可执行信息

**错误：**
```json
{
  "type": "create_document",
  "target_count": 44  // ❌ 缺少具体文档列表
}
```

**修正：**
```json
{
  "type": "create_document",
  "document_list": [  // ✅ 提供具体列表
    {"title": "GDC 2025: ...", "file": "..."}
  ]
}
```

---

**详细规范：** 查看 `autorun/WORKFLOW_RULES.md`

