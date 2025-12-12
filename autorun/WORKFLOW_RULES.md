# Orchestrator + Cursor Worker 工作流行为规范

> 量化、可落地的流程规则和标准，作为系统行为规范

**版本：** 1.0  
**制定日期：** 2025-12-11  
**适用范围：** Orchestrator、Cursor Worker、任务管理

---

## 0. 核心原则

### 0.1 状态定义标准（强制执行）

**任务状态必须严格区分：**

| 状态 | 定义 | 量化标准 | 使用场景 |
|------|------|---------|---------|
| `pending` | 待处理 | 任务已创建，未开始处理 | 初始状态、回滚后状态 |
| `in_progress` | 处理中 | 已写入input文件，等待Worker处理 | Orchestrator写入批次后 |
| `partial` | 部分完成 | 已处理但未完全完成 | Worker输出partial状态 |
| `done` | 已完成 | **所有验证通过** | 内容完整且已验证 |
| `failed` | 失败 | 处理失败或超时 | 明确失败的情况 |
| `skipped` | 已跳过 | 需要特殊权限，暂时跳过 | 需要GDC Vault等权限 |

**关键规则：**
- ✅ `done` 状态必须通过验证（见1.3节）
- ❌ 不能仅因为输出文件存在就标记为 `done`
- ✅ `partial` 状态必须继续处理，不能标记为 `done`

### 0.2 任务设计原则

**可执行性要求：**
1. **任务必须包含可执行信息**
   - ❌ 错误："收集GDC 2025更多演讲（还需44个）"
   - ✅ 正确："收集GDC 2025编程技术类演讲 - [具体演讲标题]"

2. **任务粒度要求**
   - 单个任务最多处理 **5个文档**
   - 超过5个必须拆分为多个任务
   - 每个文档一个任务为最佳实践

3. **资源要求明确**
   - 如果任务需要特殊权限（GDC Vault），必须标记为 `skipped`
   - 如果任务需要外部资源，必须提供资源清单或获取方法

---

## 1. Orchestrator 行为规范

### 1.1 任务挑选规则

**量化标准：**

```python
# 规则1：只挑选 pending 状态的任务
pending_tasks = [t for t in tasks if t.get("status") == "pending"]

# 规则2：按优先级排序（数字越小优先级越高）
pending_tasks.sort(key=lambda x: x.get("priority", 999))

# 规则3：批次大小限制
BATCH_SIZE = 20  # 默认值，可配置
batch = pending_tasks[:BATCH_SIZE]

# 规则4：跳过需要特殊权限的任务
batch = [t for t in batch if t.get("requires_permission") != True]
```

**验证检查：**
- [ ] 任务状态必须是 `pending`
- [ ] 任务必须包含可执行信息（见0.2节）
- [ ] 任务不依赖特殊权限（除非标记为 `skipped`）

### 1.2 状态更新规则

**写入批次后：**
```python
# 规则：标记为 in_progress
for task in batch:
    task["status"] = "in_progress"
    task["started_at"] = datetime.now().isoformat()
```

**检测到输出后：**
```python
# 规则：必须检查输出文件中的实际状态
output_data = parse_output(output_file)

for result in output_data.get("results", []):
    task_id = result.get("id")
    actual_status = result.get("status")  # success/partial/pending/failed
    
    if actual_status == "success":
        # 规则：只有 success 且通过验证才标记为 done
        if verify_task_completion(task_id, result):
            mark_done(task_id)
        else:
            mark_partial(task_id)  # 验证失败，标记为 partial
    elif actual_status == "partial":
        # 规则：partial 必须保持 in_progress 或标记为 partial
        mark_partial(task_id)
    elif actual_status == "pending":
        # 规则：pending 回滚为 pending
        rollback_to_pending(task_id)
    elif actual_status == "failed":
        # 规则：failed 标记为 failed
        mark_failed(task_id, result.get("error"))
```

**关键规则：**
- ❌ **禁止**：仅因为输出文件存在就标记为 `done`
- ✅ **必须**：检查输出文件中的 `status` 字段
- ✅ **必须**：根据实际状态更新任务状态

### 1.3 任务完成验证规则

**验证标准（量化）：**

```python
def verify_task_completion(task_id, result):
    """验证任务是否真正完成"""
    
    # 规则1：检查状态
    if result.get("status") != "success":
        return False
    
    # 规则2：内容补充任务验证
    if task.type == "content_supplement":
        # 必须检查所有目标文档
        for target_file in task.get("target_files", []):
            if not verify_document_completeness(target_file):
                return False
    
    # 规则3：新建文档任务验证
    if task.type == "create_document":
        # 必须检查是否创建了目标数量的文档
        created_count = result.get("created_count", 0)
        target_count = task.get("target_count", 0)
        if created_count < target_count:
            return False
    
    return True

def verify_document_completeness(file_path):
    """验证文档内容完整性"""
    doc = read_document(file_path)
    
    # 检查项（量化标准）
    checks = {
        "has_metadata": len(doc.metadata) >= 5,  # 至少5个元数据字段
        "has_resource_links": len(doc.resource_links) >= 1,  # 至少1个资源链接
        "has_summary": len(doc.summary) > 100,  # 摘要至少100字
        "has_key_points": len(doc.key_points) >= 3,  # 至少3个关键要点
        "has_content": len(doc.detailed_content) > 200  # 详细内容至少200字
    }
    
    # 规则：所有检查项必须通过
    return all(checks.values())
```

**验证规则总结：**
- ✅ 状态必须是 `success`
- ✅ 内容补充任务：所有目标文档必须通过完整性检查
- ✅ 新建文档任务：必须创建目标数量的文档
- ✅ 文档完整性：必须满足所有检查项

### 1.4 超时处理规则

**量化标准：**

```python
OUTPUT_TIMEOUT = 3600  # 1小时（秒）
POLL_INTERVAL = 10    # 每10秒检查一次

# 规则：超时后自动回滚
if wait_time > OUTPUT_TIMEOUT:
    # 自动回滚，不等待用户输入
    rollback_to_pending(batch)
    log_timeout(batch_name, OUTPUT_TIMEOUT)
```

**规则：**
- ✅ 超时后自动回滚为 `pending`
- ❌ 不等待用户输入（非交互模式）
- ✅ 记录超时日志

### 1.5 错误处理规则

**量化标准：**

```python
# 规则1：输出文件解析失败
if output_data is None:
    mark_failed(batch, "输出文件解析失败")
    log_error("parse_output_failed", batch_name)

# 规则2：任务验证失败
if not verify_task_completion(task, result):
    mark_partial(task, "验证未通过")
    log_warning("verification_failed", task_id)

# 规则3：文件操作失败
try:
    save_tasks(tasks)
except Exception as e:
    log_error("save_tasks_failed", str(e))
    # 不中断流程，记录错误后继续
```

---

## 2. Cursor Worker 行为规范

### 2.1 任务处理状态定义

**Worker输出状态标准：**

| 状态 | 定义 | 量化标准 | 使用场景 |
|------|------|---------|---------|
| `success` | 成功完成 | 所有要求都满足 | 内容完整补充、文档成功创建 |
| `partial` | 部分完成 | 部分要求满足 | 文档框架存在但内容未补充 |
| `pending` | 无法执行 | 缺少必要信息 | 任务描述不明确、缺少资源 |
| `failed` | 执行失败 | 明确失败 | 文件操作失败、网络错误 |
| `skipped` | 已跳过 | 需要特殊权限 | 需要GDC Vault等权限 |

### 2.2 内容补充任务处理规则

**量化标准：**

```python
def process_content_supplement_task(task):
    """处理内容补充任务"""
    
    target_files = task.get("target_files", [])
    results = []
    
    for target_file in target_files:
        doc = read_document(target_file)
        
        # 检查当前状态
        checks = {
            "file_exists": doc.exists(),
            "has_metadata": len(doc.metadata) >= 5,
            "has_resource_links": len(doc.resource_links) >= 1,
            "has_summary": len(doc.summary) > 100,
            "has_key_points": len(doc.key_points) >= 3,
            "has_content": len(doc.detailed_content) > 200
        }
        
        # 规则1：如果文件不存在，标记为 failed
        if not checks["file_exists"]:
            results.append({
                "file": target_file,
                "status": "failed",
                "error": "文档文件不存在"
            })
            continue
        
        # 规则2：检查内容完整性
        completed_checks = sum(checks.values())
        total_checks = len(checks)
        completion_rate = completed_checks / total_checks
        
        if completion_rate == 1.0:
            # 所有检查通过，标记为 success
            results.append({
                "file": target_file,
                "status": "success",
                "completion_rate": 1.0
            })
        elif completion_rate >= 0.5:
            # 部分完成，标记为 partial
            results.append({
                "file": target_file,
                "status": "partial",
                "completion_rate": completion_rate,
                "missing_items": [k for k, v in checks.items() if not v]
            })
        else:
            # 完成度太低，标记为 partial
            results.append({
                "file": target_file,
                "status": "partial",
                "completion_rate": completion_rate,
                "missing_items": [k for k, v in checks.items() if not v]
            })
    
    # 规则3：整体状态判断
    success_count = len([r for r in results if r["status"] == "success"])
    total_count = len(results)
    
    if success_count == total_count:
        return {"status": "success", "results": results}
    elif success_count > 0:
        return {"status": "partial", "results": results}
    else:
        return {"status": "partial", "results": results}
```

**关键规则：**
- ✅ 必须检查每个目标文档的完整性
- ✅ 使用量化标准判断完成度（completion_rate）
- ✅ 只有所有文档都完整才返回 `success`
- ✅ 部分完成必须返回 `partial`

### 2.3 新建文档任务处理规则

**量化标准：**

```python
def process_create_document_task(task):
    """处理新建文档任务"""
    
    # 规则1：检查任务是否包含可执行信息
    if not has_executable_info(task):
        return {
            "status": "pending",
            "reason": "任务描述不明确，缺少具体文档列表",
            "suggestion": "需要提供：1) 官方日程表链接；2) 具体演讲列表；3) 或拆分为具体任务"
        }
    
    # 规则2：检查是否需要特殊权限
    if requires_special_permission(task):
        return {
            "status": "skipped",
            "reason": "需要特殊权限（如GDC Vault账号）",
            "suggestion": "需要人工获取资源后，创建新的资源补充任务"
        }
    
    # 规则3：执行文档创建
    target_count = task.get("target_count", 0)
    created_documents = []
    
    for doc_info in task.get("document_list", []):
        doc = create_document(doc_info)
        if doc:
            created_documents.append(doc)
    
    created_count = len(created_documents)
    
    # 规则4：判断完成状态
    if created_count == target_count:
        return {
            "status": "success",
            "created_count": created_count,
            "target_count": target_count
        }
    elif created_count > 0:
        return {
            "status": "partial",
            "created_count": created_count,
            "target_count": target_count,
            "remaining": target_count - created_count
        }
    else:
        return {
            "status": "pending",
            "reason": "无法创建文档，缺少必要信息",
            "created_count": 0,
            "target_count": target_count
        }

def has_executable_info(task):
    """检查任务是否包含可执行信息"""
    # 规则：必须包含以下之一
    # 1. document_list: 具体文档列表
    # 2. schedule_url: 官方日程表链接
    # 3. search_keywords: 可搜索的关键词
    return (
        task.get("document_list") or
        task.get("schedule_url") or
        task.get("search_keywords")
    )

def requires_special_permission(task):
    """检查是否需要特殊权限"""
    # 规则：如果任务明确标记需要权限，返回 True
    return task.get("requires_permission") == True
```

**关键规则：**
- ✅ 必须检查任务是否包含可执行信息
- ✅ 如果缺少信息，返回 `pending` 并提供建议
- ✅ 如果需要特殊权限，返回 `skipped`
- ✅ 只有创建了目标数量的文档才返回 `success`

### 2.4 输出文件格式规范

**必须包含的字段（量化）：**

```json
{
  "batch_name": "batch_1234567890",  // 必须：与输入批次名称匹配
  "processed_at": "2025-12-11T...",  // 必须：ISO格式时间戳
  "results": [                        // 必须：每个任务一个结果
    {
      "id": 1,                        // 必须：任务ID
      "status": "success",            // 必须：success/partial/pending/failed/skipped
      "result": {                     // 必须：任务结果
        "title": "...",
        "completion_rate": 1.0,      // 可选：完成度（0-1）
        "created_count": 5,           // 可选：创建的文档数
        "target_count": 5,            // 可选：目标文档数
        "missing_items": [],          // 可选：缺失的项目
        "notes": "..."                // 可选：备注
      },
      "error": "..."                  // 可选：错误信息（如果failed）
    }
  ],
  "summary": {                        // 必须：批次总结
    "total": 20,                      // 必须：总任务数
    "success": 15,                    // 必须：成功数
    "partial": 3,                     // 必须：部分完成数
    "pending": 2,                     // 必须：待处理数
    "failed": 0,                      // 必须：失败数
    "skipped": 0,                     // 必须：跳过数
    "processing_time": "5分钟"        // 必须：处理时间
  }
}
```

**验证规则：**
- ✅ `batch_name` 必须与输入批次名称完全匹配
- ✅ `status` 必须是预定义的状态之一
- ✅ `summary` 中的数字必须与 `results` 中的状态匹配
- ✅ 所有必填字段必须存在

---

## 3. 任务设计规范

### 3.1 任务类型定义

**标准任务类型：**

| 类型 | 定义 | 必填字段 | 可选字段 |
|------|------|---------|---------|
| `content_supplement` | 内容补充 | `target_files` | `resource_list` |
| `create_document` | 新建文档 | `document_list` 或 `schedule_url` | `target_count` |
| `url` | URL处理 | `url` | `extract_fields` |
| `topic` | 主题搜索 | `title`, `search_keywords` | `max_results` |
| `skipped` | 已跳过 | `reason` | `requires_permission` |

### 3.2 任务粒度规则

**量化标准：**

```python
# 规则1：单个任务最多处理5个文档
MAX_DOCUMENTS_PER_TASK = 5

# 规则2：如果超过5个，必须拆分
if len(target_files) > MAX_DOCUMENTS_PER_TASK:
    # 必须拆分为多个任务
    split_task(task, MAX_DOCUMENTS_PER_TASK)

# 规则3：最佳实践是每个文档一个任务
RECOMMENDED_DOCUMENTS_PER_TASK = 1
```

**规则：**
- ✅ 单个任务最多5个文档
- ✅ 超过5个必须拆分
- ✅ 推荐每个文档一个任务

### 3.3 任务可执行性检查

**量化标准：**

```python
def validate_task_executability(task):
    """验证任务是否可执行"""
    
    errors = []
    
    # 规则1：检查必填字段
    if task.type == "content_supplement":
        if not task.get("target_files"):
            errors.append("缺少 target_files 字段")
    
    elif task.type == "create_document":
        if not (task.get("document_list") or task.get("schedule_url")):
            errors.append("缺少 document_list 或 schedule_url")
    
    elif task.type == "url":
        if not task.get("url"):
            errors.append("缺少 url 字段")
    
    elif task.type == "topic":
        if not (task.get("title") or task.get("search_keywords")):
            errors.append("缺少 title 或 search_keywords")
    
    # 规则2：检查任务粒度
    if task.type == "content_supplement":
        if len(task.get("target_files", [])) > MAX_DOCUMENTS_PER_TASK:
            errors.append(f"任务包含超过{MAX_DOCUMENTS_PER_TASK}个文档，必须拆分")
    
    # 规则3：检查是否需要特殊权限
    if task.get("requires_permission"):
        if task.get("status") != "skipped":
            errors.append("需要特殊权限的任务必须标记为 skipped")
    
    return {
        "executable": len(errors) == 0,
        "errors": errors
    }
```

**规则：**
- ✅ 任务创建时必须通过可执行性检查
- ✅ 不通过检查的任务不能进入处理流程
- ✅ 需要特殊权限的任务必须标记为 `skipped`

### 3.4 任务优先级规则

**量化标准：**

```python
# 优先级定义
PRIORITY_LEVELS = {
    1: "最高优先级",  # 立即处理
    2: "高优先级",    # 优先处理
    3: "中优先级",    # 正常处理
    4: "低优先级",    # 最后处理
    5: "最低优先级"   # 可延后处理
}

# 规则：优先级数字越小，优先级越高
# 排序规则：priority ASC
```

**规则：**
- ✅ 优先级1-2的任务优先处理
- ✅ 优先级3的任务正常处理
- ✅ 优先级4-5的任务最后处理

---

## 4. 文档完整性验证规范

### 4.1 文档完整性检查项（量化）

**必须检查的项目：**

```python
DOCUMENT_COMPLETENESS_CHECKS = {
    "metadata": {
        "required_fields": ["年份", "会议", "日期", "演讲者", "分类"],
        "min_fields": 5,
        "weight": 0.2  # 权重20%
    },
    "resource_links": {
        "required_types": ["GDC Vault", "视频", "PPT/PDF", "官方摘要"],
        "min_count": 1,  # 至少1个资源链接
        "weight": 0.3    # 权重30%
    },
    "summary": {
        "min_length": 100,  # 摘要至少100字
        "weight": 0.2       # 权重20%
    },
    "detailed_content": {
        "min_length": 200,  # 详细内容至少200字
        "required_sections": ["核心观点", "主要内容", "关键数据"],
        "weight": 0.2       # 权重20%
    },
    "key_points": {
        "min_count": 3,  # 至少3个关键要点
        "weight": 0.1    # 权重10%
    }
}

def calculate_completion_rate(doc):
    """计算文档完成度"""
    scores = {}
    
    # 检查元数据
    metadata_score = min(len(doc.metadata) / DOCUMENT_COMPLETENESS_CHECKS["metadata"]["min_fields"], 1.0)
    scores["metadata"] = metadata_score * DOCUMENT_COMPLETENESS_CHECKS["metadata"]["weight"]
    
    # 检查资源链接
    resource_score = min(len(doc.resource_links) / DOCUMENT_COMPLETENESS_CHECKS["resource_links"]["min_count"], 1.0)
    scores["resource_links"] = resource_score * DOCUMENT_COMPLETENESS_CHECKS["resource_links"]["weight"]
    
    # 检查摘要
    summary_score = min(len(doc.summary) / DOCUMENT_COMPLETENESS_CHECKS["summary"]["min_length"], 1.0)
    scores["summary"] = summary_score * DOCUMENT_COMPLETENESS_CHECKS["summary"]["weight"]
    
    # 检查详细内容
    content_score = min(len(doc.detailed_content) / DOCUMENT_COMPLETENESS_CHECKS["detailed_content"]["min_length"], 1.0)
    scores["detailed_content"] = content_score * DOCUMENT_COMPLETENESS_CHECKS["detailed_content"]["weight"]
    
    # 检查关键要点
    points_score = min(len(doc.key_points) / DOCUMENT_COMPLETENESS_CHECKS["key_points"]["min_count"], 1.0)
    scores["key_points"] = points_score * DOCUMENT_COMPLETENESS_CHECKS["key_points"]["weight"]
    
    # 计算总分
    total_score = sum(scores.values())
    
    return {
        "completion_rate": total_score,
        "scores": scores,
        "status": "complete" if total_score >= 0.9 else "partial" if total_score >= 0.5 else "incomplete"
    }
```

**验证规则：**
- ✅ 完成度 >= 0.9：标记为 `complete`（可标记为 done）
- ✅ 完成度 >= 0.5：标记为 `partial`（需要继续处理）
- ✅ 完成度 < 0.5：标记为 `incomplete`（需要重新处理）

### 4.2 文档状态定义

**量化标准：**

| 状态 | 完成度 | 定义 | 操作 |
|------|-------|------|------|
| `complete` | >= 0.9 | 内容完整 | 可标记为 done |
| `partial` | 0.5-0.9 | 部分完成 | 继续补充内容 |
| `incomplete` | < 0.5 | 未完成 | 需要重新处理 |

---

## 5. 工作流执行规范

### 5.1 Orchestrator 执行流程（量化）

**标准流程：**

```
1. 加载任务池
   → 验证 tasks.json 格式
   → 统计任务状态

2. 挑选批次（量化规则）
   → 筛选 pending 状态
   → 按 priority 排序
   → 取前 BATCH_SIZE 个（默认20）
   → 跳过 requires_permission=True 的任务

3. 验证任务可执行性
   → 检查必填字段
   → 检查任务粒度（<=5个文档）
   → 验证通过才继续

4. 写入批次文件
   → 标记为 in_progress
   → 保存任务状态

5. 等待输出（超时1小时）
   → 每10秒检查一次
   → 超时自动回滚

6. 解析输出文件
   → 验证格式
   → 检查 batch_name 匹配

7. 更新任务状态（关键）
   → 检查每个 result 的 status
   → success + 验证通过 → done
   → partial → partial（保持 in_progress）
   → pending → pending（回滚）
   → failed → failed

8. 验证任务完成（量化）
   → 内容补充：所有文档 completion_rate >= 0.9
   → 新建文档：created_count == target_count

9. 归档输出文件
   → 复制到 archive/ 目录

10. 继续下一批
```

### 5.2 Worker 执行流程（量化）

**标准流程：**

```
1. 读取批次文件
   → 验证 JSON 格式
   → 检查 batch_name

2. 处理每个任务（顺序处理）
   → 根据任务类型选择处理函数
   → 执行处理逻辑
   → 记录处理结果

3. 生成结果（量化）
   → 计算 completion_rate
   → 判断 status（success/partial/pending/failed/skipped）
   → 记录详细信息

4. 写入输出文件
   → 验证格式
   → 确保 batch_name 匹配

5. 完成确认
   → 检查所有任务已处理
   → 检查输出文件格式
   → 结束本次执行
```

---

## 6. 量化指标和监控

### 6.1 任务处理指标

**必须跟踪的指标：**

```python
TASK_METRICS = {
    "total_tasks": 0,           # 总任务数
    "pending": 0,               # 待处理
    "in_progress": 0,           # 处理中
    "partial": 0,               # 部分完成
    "done": 0,                  # 已完成
    "failed": 0,                # 失败
    "skipped": 0,               # 已跳过
    
    "completion_rate": 0.0,     # 完成率（done / total）
    "partial_rate": 0.0,        # 部分完成率（partial / total）
    "failure_rate": 0.0,        # 失败率（failed / total）
    
    "avg_processing_time": 0.0, # 平均处理时间
    "timeout_count": 0,         # 超时次数
}
```

### 6.2 文档收集指标

**必须跟踪的指标：**

```python
DOCUMENT_METRICS = {
    "target_count": 0,          # 目标文档数
    "created_count": 0,         # 已创建文档数
    "complete_count": 0,        # 完整文档数（completion_rate >= 0.9）
    "partial_count": 0,         # 部分文档数（0.5 <= completion_rate < 0.9）
    "incomplete_count": 0,      # 未完成文档数（completion_rate < 0.5）
    
    "collection_rate": 0.0,     # 收集率（created_count / target_count）
    "completion_rate": 0.0,     # 完成率（complete_count / created_count）
    "avg_completion_rate": 0.0, # 平均完成度
}
```

### 6.3 质量指标

**必须跟踪的指标：**

```python
QUALITY_METRICS = {
    "avg_metadata_completeness": 0.0,  # 平均元数据完整度
    "avg_resource_links": 0.0,         # 平均资源链接数
    "avg_summary_length": 0.0,         # 平均摘要长度
    "avg_content_length": 0.0,         # 平均内容长度
    "avg_key_points": 0.0,              # 平均关键要点数
    
    "validation_pass_rate": 0.0,       # 验证通过率
    "error_rate": 0.0,                 # 错误率
}
```

---

## 7. 错误处理和日志规范

### 7.1 错误分类（量化）

**错误级别：**

| 级别 | 定义 | 处理方式 | 日志级别 |
|------|------|---------|---------|
| `critical` | 系统错误 | 停止处理 | ERROR |
| `warning` | 警告 | 记录后继续 | WARNING |
| `info` | 信息 | 记录 | INFO |
| `debug` | 调试 | 详细记录 | DEBUG |

### 7.2 日志格式规范

**标准格式：**

```python
LOG_FORMAT = {
    "timestamp": "2025-12-11T17:47:30.000000",
    "level": "INFO",
    "component": "orchestrator" | "worker",
    "action": "pick_batch" | "process_task" | "update_status",
    "task_id": 1,
    "batch_name": "batch_1234567890",
    "message": "...",
    "data": {}  # 可选：附加数据
}
```

### 7.3 错误处理规则

**量化标准：**

```python
# 规则1：文件操作错误
try:
    save_tasks(tasks)
except IOError as e:
    log_error("file_io_error", str(e))
    # 不中断流程，记录错误后继续

# 规则2：JSON解析错误
try:
    output_data = json.load(output_file)
except JSONDecodeError as e:
    log_error("json_parse_error", str(e))
    mark_failed(batch, "输出文件格式错误")

# 规则3：验证错误
if not verify_task_completion(task, result):
    log_warning("verification_failed", task_id)
    mark_partial(task)
    # 不标记为失败，继续处理其他任务
```

---

## 8. 配置和参数规范

### 8.1 可配置参数（量化）

```python
CONFIG = {
    "orchestrator": {
        "batch_size": 20,           # 批次大小（可配置）
        "poll_interval": 10,         # 轮询间隔（秒）
        "output_timeout": 3600,     # 输出超时（秒）
        "max_retries": 3,           # 最大重试次数
    },
    "worker": {
        "max_documents_per_task": 5,  # 单个任务最大文档数
        "min_completion_rate": 0.9,   # 最低完成度（标记为done）
        "partial_threshold": 0.5,     # 部分完成阈值
    },
    "validation": {
        "metadata_min_fields": 5,     # 元数据最少字段数
        "resource_links_min": 1,      # 资源链接最少数量
        "summary_min_length": 100,    # 摘要最少字数
        "content_min_length": 200,    # 内容最少字数
        "key_points_min": 3,          # 关键要点最少数量
    }
}
```

### 8.2 参数验证规则

**规则：**
- ✅ 所有参数必须有默认值
- ✅ 参数修改必须通过配置文件
- ✅ 参数验证必须在启动时进行

---

## 9. 行为规范检查清单

### 9.1 Orchestrator 检查清单

**每次执行前：**
- [ ] 任务状态统计正确
- [ ] 批次大小符合配置
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

## 10. 持续改进机制

### 10.1 定期检查

**量化标准：**

```python
# 每周检查一次
WEEKLY_CHECK = {
    "task_completion_rate": 0.0,    # 任务完成率
    "document_completion_rate": 0.0, # 文档完成率
    "partial_task_count": 0,        # 部分完成任务数
    "pending_task_count": 0,         # 待处理任务数
    "avg_processing_time": 0.0,     # 平均处理时间
}
```

### 10.2 问题识别

**自动识别：**
- 部分完成任务超过阈值（如 >10个）
- 待处理任务超过阈值（如 >20个）
- 平均处理时间超过阈值（如 >1小时）
- 失败率超过阈值（如 >5%）

### 10.3 规则更新

**规则版本管理：**
- 每次规则更新必须记录版本号
- 更新原因和影响范围
- 向后兼容性检查

---

## 11. 附录：量化标准速查表

### 11.1 状态定义

| 状态 | 完成度 | 验证要求 |
|------|-------|---------|
| done | >= 0.9 | 所有检查项通过 |
| partial | 0.5-0.9 | 部分检查项通过 |
| pending | N/A | 无法执行 |
| failed | N/A | 明确失败 |
| skipped | N/A | 需要特殊权限 |

### 11.2 任务粒度

| 类型 | 最大文档数 | 推荐文档数 |
|------|-----------|-----------|
| content_supplement | 5 | 1 |
| create_document | 5 | 1 |
| url | 1 | 1 |
| topic | 1 | 1 |

### 11.3 文档完整性

| 检查项 | 最低要求 | 权重 |
|--------|---------|------|
| 元数据 | 5个字段 | 20% |
| 资源链接 | 1个 | 30% |
| 摘要 | 100字 | 20% |
| 详细内容 | 200字 | 20% |
| 关键要点 | 3个 | 10% |

### 11.4 超时和重试

| 操作 | 超时时间 | 重试次数 |
|------|---------|---------|
| 等待输出 | 3600秒（1小时） | 0（自动回滚） |
| 文件操作 | 30秒 | 3次 |
| 网络请求 | 60秒 | 3次 |

---

**规范版本：** 1.0  
**最后更新：** 2025-12-11  
**维护者：** 系统管理员  
**状态：** 生效中

