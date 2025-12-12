# 工作流行为规范（正式版）

> 作为系统行为规范的量化、可落地规则

**版本：** 1.0  
**生效日期：** 2025-12-11  
**适用范围：** Orchestrator、Cursor Worker、任务管理

---

## 0. 规范说明

本规范是 Orchestrator + Cursor Worker 工作流系统的**行为准则**，所有组件必须严格遵守。

**规范特点：**
- ✅ **量化**：所有标准都有明确的数值要求
- ✅ **可落地**：所有规则都可以直接实施
- ✅ **可验证**：所有标准都可以自动检查
- ✅ **可追溯**：所有操作都有日志记录

---

## 1. 状态定义规范（强制执行）

### 1.1 任务状态定义

| 状态 | 完成度 | 定义 | 验证要求 | 操作 |
|------|-------|------|---------|------|
| `pending` | N/A | 待处理 | 任务已创建，未开始 | 可进入处理流程 |
| `in_progress` | N/A | 处理中 | 已写入input文件 | 等待Worker处理 |
| `partial` | 0.5-0.9 | 部分完成 | 部分要求满足 | 继续处理，不能标记为done |
| `done` | >= 0.9 | 已完成 | **所有验证通过** | 任务完成 |
| `failed` | N/A | 失败 | 明确失败 | 记录错误 |
| `skipped` | N/A | 已跳过 | 需要特殊权限 | 暂时跳过 |

### 1.2 状态转换规则

**允许的转换：**
```
pending → in_progress → done (success + 验证通过)
pending → in_progress → partial (需要继续处理)
pending → in_progress → pending (回滚)
pending → in_progress → failed (明确失败)
pending → skipped (需要特殊权限)
```

**禁止的转换：**
- ❌ `partial` → `done`（未通过验证）
- ❌ `pending` → `done`（未处理）
- ❌ `in_progress` → `done`（未检查输出状态）

### 1.3 状态验证规则

**Orchestrator 必须遵守：**
```python
# 规则1：不能仅因为输出文件存在就标记为 done
if output_file.exists():
    # ❌ 错误：直接标记为 done
    # ✅ 正确：检查输出文件中的实际状态
    
# 规则2：必须检查输出文件中的 status 字段
output_data = parse_output(output_file)
for result in output_data.get("results", []):
    actual_status = result.get("status")
    
    # 规则3：根据实际状态更新
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

---

## 2. 任务设计规范（强制执行）

### 2.1 任务粒度规则

**量化标准：**

| 任务类型 | 最大文档数 | 推荐文档数 | 超过限制的处理 |
|---------|-----------|-----------|--------------|
| content_supplement | 5 | 1 | 必须拆分 |
| create_document | 5 | 1 | 必须拆分 |
| url | 1 | 1 | 不允许超过 |
| topic | 1 | 1 | 不允许超过 |

**规则：**
- ✅ 单个任务最多5个文档
- ✅ 超过5个必须拆分为多个任务
- ✅ 推荐每个文档一个任务（最佳实践）

### 2.2 任务可执行性要求

**内容补充任务：**
```json
{
  "type": "content_supplement",
  "target_files": ["doc1.md", "doc2.md"],  // 必须：最多5个
  "target_file": "doc.md"  // 可选：单个文档
}
```

**新建文档任务：**
```json
{
  "type": "create_document",
  "document_list": [  // 必须：具体文档列表（至少一个）
    {"title": "...", "file": "..."}
  ],
  "schedule_url": "https://...",  // 可选：官方日程表
  "search_keywords": "..."  // 可选：搜索关键词
}
```

**需要特殊权限的任务：**
```json
{
  "type": "content_supplement",
  "requires_permission": true,  // 必须：标记需要权限
  "status": "skipped",  // 必须：标记为 skipped
  "reason": "需要GDC Vault账号"  // 必须：说明原因
}
```

### 2.3 任务验证规则

**创建任务时必须验证：**
- [ ] 任务类型明确
- [ ] 必填字段完整
- [ ] 任务粒度符合要求（<=5个文档）
- [ ] 包含可执行信息
- [ ] 如果需要特殊权限，标记为 skipped

**验证工具：**
```bash
python autorun/task_validator.py
```

---

## 3. 文档完整性规范（强制执行）

### 3.1 完整性检查项（量化）

| 检查项 | 最低要求 | 权重 | 计算公式 |
|--------|---------|------|---------|
| 元数据 | 5个字段 | 20% | min(实际字段数/5, 1.0) |
| 资源链接 | 1个 | 30% | min(实际链接数/1, 1.0) |
| 摘要 | 100字 | 20% | min(实际字数/100, 1.0) |
| 详细内容 | 200字 | 20% | min(实际字数/200, 1.0) |
| 关键要点 | 3个 | 10% | min(实际要点数/3, 1.0) |

### 3.2 完成度计算

```python
completion_rate = (
    metadata_score * 0.2 +
    resource_links_score * 0.3 +
    summary_score * 0.2 +
    content_score * 0.2 +
    key_points_score * 0.1
)
```

### 3.3 状态判断规则

| 完成度 | 状态 | 操作 |
|-------|------|------|
| >= 0.9 | `complete` | 可标记为 `done` |
| 0.5-0.9 | `partial` | 继续补充内容 |
| < 0.5 | `incomplete` | 需要重新处理 |

**规则：**
- ✅ 只有 `completion_rate >= 0.9` 才可标记为 `done`
- ✅ `completion_rate < 0.9` 必须标记为 `partial`
- ✅ 必须计算并记录 `completion_rate`

---

## 4. Orchestrator 行为规范（强制执行）

### 4.1 任务挑选规则

```python
# 规则1：只挑选 pending 状态
pending = [t for t in tasks if t.get("status") == "pending"]

# 规则2：跳过需要特殊权限的任务
pending = [t for t in pending if not (t.get("requires_permission") and t.get("status") != "skipped")]

# 规则3：按优先级排序
pending.sort(key=lambda x: x.get("priority", 999))

# 规则4：批次大小限制
BATCH_SIZE = 20  # 可配置
batch = pending[:BATCH_SIZE]
```

### 4.2 状态更新规则（关键）

**必须遵守的流程：**

```python
# 步骤1：解析输出文件
output_data = parse_output(output_file)

# 步骤2：检查每个任务的实际状态
for result in output_data.get("results", []):
    task_id = result.get("id")
    actual_status = result.get("status")
    
    # 步骤3：根据实际状态更新
    if actual_status == "success":
        # 规则：只有 success + 验证通过才标记为 done
        if verify_task_completion(task_id, result):
            mark_done(task_id)
        else:
            mark_partial(task_id)  # 验证失败
    elif actual_status == "partial":
        mark_partial(task_id)  # 保持 in_progress
    elif actual_status == "pending":
        rollback_to_pending(task_id)  # 回滚
    elif actual_status == "failed":
        mark_failed(task_id, result.get("error"))
    elif actual_status == "skipped":
        mark_skipped(task_id, result.get("reason"))
```

### 4.3 任务完成验证规则

**验证标准：**

```python
def verify_task_completion(task_id, result):
    """验证任务是否真正完成"""
    
    # 规则1：状态必须是 success
    if result.get("status") != "success":
        return False
    
    # 规则2：内容补充任务验证
    if task.type == "content_supplement":
        for target_file in task.get("target_files", []):
            doc = read_document(target_file)
            completion_rate = calculate_completion_rate(doc)
            if completion_rate < 0.9:  # 完成度不足
                return False
    
    # 规则3：新建文档任务验证
    if task.type == "create_document":
        created_count = result.get("created_count", 0)
        target_count = task.get("target_count", 0)
        if created_count < target_count:  # 未达到目标
            return False
    
    return True
```

---

## 5. Worker 行为规范（强制执行）

### 5.1 状态判断规则

**内容补充任务：**
```python
# 计算完成度
completion_rate = calculate_completion_rate(doc)

# 判断状态
if completion_rate >= 0.9:
    status = "success"
elif completion_rate >= 0.5:
    status = "partial"
else:
    status = "partial"  # 需要重新处理
```

**新建文档任务：**
```python
# 检查可执行性
if not has_executable_info(task):
    status = "pending"
    reason = "任务描述不明确，缺少具体文档列表"

# 检查特殊权限
elif requires_special_permission(task):
    status = "skipped"
    reason = "需要特殊权限（如GDC Vault账号）"

# 执行创建
else:
    created_count = create_documents(task)
    if created_count == target_count:
        status = "success"
    elif created_count > 0:
        status = "partial"
    else:
        status = "pending"
```

### 5.2 输出格式规范

**必须包含的字段：**

```json
{
  "batch_name": "batch_1234567890",  // 必须：与输入匹配
  "processed_at": "2025-12-11T...",  // 必须：ISO时间戳
  "results": [  // 必须：每个任务一个结果
    {
      "id": 1,  // 必须：任务ID
      "status": "success",  // 必须：状态
      "result": {  // 必须：结果
        "completion_rate": 0.95,  // 可选：完成度
        "created_count": 5,  // 可选：创建的文档数
        "target_count": 5,  // 可选：目标文档数
        "missing_items": []  // 可选：缺失项
      }
    }
  ],
  "summary": {  // 必须：批次总结
    "total": 20,  // 必须：总任务数
    "success": 15,  // 必须：成功数
    "partial": 3,  // 必须：部分完成数
    "pending": 2,  // 必须：待处理数
    "failed": 0,  // 必须：失败数
    "skipped": 0  // 必须：跳过数
  }
}
```

**验证规则：**
- ✅ `batch_name` 必须与输入批次名称完全匹配
- ✅ `status` 必须是预定义的状态之一
- ✅ `summary` 中的数字必须与 `results` 中的状态匹配

---

## 6. 特殊权限处理规范

### 6.1 需要特殊权限的任务

**定义：**
- 需要GDC Vault账号的任务
- 需要付费内容的任务
- 需要人工审核的任务

**处理规则：**
1. ✅ 任务必须标记 `requires_permission: true`
2. ✅ 任务状态必须标记为 `skipped`
3. ✅ 必须说明需要什么权限（reason字段）
4. ✅ Orchestrator 自动跳过这些任务
5. ✅ 等待人工获取资源后，创建新的资源补充任务

### 6.2 资源获取工作流

**标准流程：**
```
1. 人工获取资源
   → 访问GDC Vault
   → 获取视频和PPT链接
   → 整理成资源清单文件

2. 创建资源补充任务
   → 类型：content_supplement
   → 提供 resource_list 文件路径
   → Worker读取资源清单自动补充
```

---

## 7. 量化指标规范

### 7.1 必须跟踪的指标

**任务指标：**
- `total_tasks`: 总任务数
- `pending`: 待处理数
- `in_progress`: 处理中数
- `partial`: 部分完成数
- `done`: 已完成数
- `failed`: 失败数
- `skipped`: 跳过数
- `completion_rate`: 完成率（done / total）

**文档指标：**
- `target_count`: 目标文档数
- `created_count`: 已创建文档数
- `complete_count`: 完整文档数（completion_rate >= 0.9）
- `partial_count`: 部分文档数（0.5 <= completion_rate < 0.9）
- `collection_rate`: 收集率（created_count / target_count）
- `avg_completion_rate`: 平均完成度

### 7.2 监控阈值

**警告阈值：**
- 部分完成任务 > 10个 → 警告
- 待处理任务 > 20个 → 警告
- 平均处理时间 > 1小时 → 警告
- 失败率 > 5% → 警告

---

## 8. 错误处理规范

### 8.1 错误分类

| 级别 | 定义 | 处理方式 | 日志级别 |
|------|------|---------|---------|
| `critical` | 系统错误 | 停止处理 | ERROR |
| `warning` | 警告 | 记录后继续 | WARNING |
| `info` | 信息 | 记录 | INFO |

### 8.2 错误处理规则

**文件操作错误：**
```python
try:
    save_tasks(tasks)
except IOError as e:
    log_error("file_io_error", str(e))
    # 不中断流程，记录错误后继续
```

**JSON解析错误：**
```python
try:
    output_data = json.load(output_file)
except JSONDecodeError as e:
    log_error("json_parse_error", str(e))
    mark_failed(batch, "输出文件格式错误")
```

**验证错误：**
```python
if not verify_task_completion(task, result):
    log_warning("verification_failed", task_id)
    mark_partial(task)
    # 不标记为失败，继续处理其他任务
```

---

## 9. 检查清单

### 9.1 Orchestrator 检查清单

**每次执行前：**
- [ ] 任务状态统计正确
- [ ] 批次大小符合配置（<=20）
- [ ] 任务可执行性验证通过
- [ ] 不包含需要特殊权限的任务（除非标记为 skipped）

**处理输出后：**
- [ ] 检查输出文件中的实际状态
- [ ] 根据实际状态更新任务状态
- [ ] 验证任务完成度（completion_rate >= 0.9）
- [ ] 只有 success + 验证通过才标记为 done

### 9.2 Worker 检查清单

**处理任务前：**
- [ ] 验证任务可执行性
- [ ] 检查是否需要特殊权限
- [ ] 确认任务粒度符合要求（<=5个文档）

**处理任务后：**
- [ ] 计算完成度（completion_rate）
- [ ] 判断正确的状态（success/partial/pending/failed/skipped）
- [ ] 记录详细的处理结果
- [ ] 输出文件格式正确

### 9.3 任务设计检查清单

**创建任务时：**
- [ ] 任务类型明确
- [ ] 必填字段完整
- [ ] 任务粒度符合要求（<=5个文档）
- [ ] 包含可执行信息
- [ ] 如果需要特殊权限，标记为 skipped

---

## 10. 工具使用

### 10.1 验证工具

```bash
# 验证任务文件
python autorun/task_validator.py

# 检查系统状态
python autorun/check_status.py

# 检查2025年任务
python autorun/check_2025_tasks.py
```

### 10.2 规范文档

- `autorun/WORKFLOW_RULES.md` - 完整规范（详细版）
- `autorun/QUICK_REFERENCE.md` - 快速参考（速查表）
- `autorun/BEHAVIOR_STANDARDS.md` - 本文档（正式版）

---

## 11. 违规处理

### 11.1 违规识别

**自动识别：**
- 任务状态标记错误（partial标记为done）
- 任务粒度超过限制（>5个文档）
- 缺少必填字段
- 输出格式不符合规范

### 11.2 处理方式

**警告：**
- 记录警告日志
- 继续处理，但标记问题

**错误：**
- 记录错误日志
- 回滚操作
- 标记为失败

---

## 12. 版本管理

### 12.1 规范版本

- **当前版本：** 1.0
- **生效日期：** 2025-12-11
- **维护者：** 系统管理员

### 12.2 更新规则

- 每次更新必须记录版本号
- 更新原因和影响范围
- 向后兼容性检查
- 通知所有使用者

---

**规范状态：** ✅ 生效中  
**最后更新：** 2025-12-11  
**下次审查：** 2026-01-11

