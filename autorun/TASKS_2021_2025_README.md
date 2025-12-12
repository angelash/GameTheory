# 近五年（2021-2025）会议资料收集任务说明

> 按照新规范生成的近五年任务规划

**生成日期：** 2025-12-11  
**规范版本：** 1.0  
**任务总数：** 179个新任务 + 34个现有任务 = 213个任务

---

## 任务统计

### 按会议类型

| 会议 | 任务数 | 说明 |
|------|-------|------|
| GDC | 98 | 94个内容补充 + 4个新建文档（skipped） |
| Unreal Fest | 39 | 15个内容补充 + 24个新建文档 |
| Unite | 21 | 5个内容补充 + 16个新建文档 |
| UWA Day | 21 | 9个内容补充 + 12个新建文档 |
| **总计** | **179** | **123个内容补充 + 56个新建文档** |

### 按状态

| 状态 | 数量 | 说明 |
|------|------|------|
| pending | 175 | 待处理任务 |
| skipped | 4 | 需要GDC Vault权限（GDC 2021-2024） |
| **总计** | **179** | |

### 按优先级

| 优先级 | 数量 | 说明 |
|--------|------|------|
| 1 | 94 | GDC 2025内容补充（最高优先级） |
| 2 | 29 | 2025年其他会议内容补充 |
| 3 | 19 | 2024年新建文档 |
| 4 | 33 | 2021-2023年新建文档 |
| 5 | 4 | 需要特殊权限的任务 |
| **总计** | **179** | |

---

## 任务类型说明

### 1. 内容补充任务（content_supplement）

**数量：** 123个  
**优先级：** 1-2  
**说明：** 补充已有文档框架的内容

**特点：**
- 每个任务包含1个文档（推荐粒度）
- 必须提供 `target_files` 列表
- 任务ID范围：1000-1122（GDC 2025）

**示例：**
```json
{
  "id": 1000,
  "type": "content_supplement",
  "title": "补充GDC 2025演讲内容 - gdc-2025-ai-animation",
  "status": "pending",
  "priority": 1,
  "target_files": [
    "docs/gdc/talks/2025/gdc-2025-ai-animation.md"
  ]
}
```

### 2. 新建文档任务（create_document）

**数量：** 52个（不含skipped）  
**优先级：** 2-4  
**说明：** 创建新文档

**特点：**
- 每个任务最多5个文档
- 必须提供 `schedule_url` 或 `search_keywords`
- 包含 `target_count` 字段

**示例：**
```json
{
  "id": 1215,
  "type": "create_document",
  "title": "收集UNREAL-FEST 2024演讲（1-5/30）",
  "status": "pending",
  "priority": 3,
  "target_count": 5,
  "schedule_url": "https://www.unrealengine.com/en-US/events/unreal-fest-2024",
  "search_keywords": "UNREAL-FEST 2024 schedule talks"
}
```

### 3. 已跳过任务（skipped）

**数量：** 4个  
**优先级：** 5  
**说明：** 需要GDC Vault权限的任务

**特点：**
- 标记为 `status: "skipped"`
- 标记为 `requires_permission: true`
- 包含 `reason` 说明

**示例：**
```json
{
  "id": 1094,
  "type": "create_document",
  "title": "收集GDC 2024演讲（需要GDC Vault权限）",
  "status": "skipped",
  "priority": 5,
  "requires_permission": true,
  "reason": "需要GDC Vault账号访问完整视频和PPT"
}
```

---

## 执行计划

### 第一阶段：内容补充（优先级1-2）

**目标：** 补充已有框架文档的内容  
**任务数：** 123个  
**预计时间：** 2-3周

**任务分布：**
- GDC 2025：94个任务（优先级1）
- Unreal Fest 2025：15个任务（优先级2）
- Unite 2025：5个任务（优先级2）
- UWA Day 2025：9个任务（优先级2）

### 第二阶段：新建文档（优先级2-3）

**目标：** 创建2024-2025年新文档  
**任务数：** 约40个  
**预计时间：** 4-6周

**任务分布：**
- Unreal Fest 2024：6个任务（优先级3）
- Unite 2024：4个任务（优先级3）
- UWA Day 2024：3个任务（优先级3）
- 其他2024-2025年任务

### 第三阶段：历史收集（优先级4）

**目标：** 收集2021-2023年历史文档  
**任务数：** 约30个  
**预计时间：** 6-8周

**任务分布：**
- Unreal Fest 2021-2023：18个任务
- Unite 2021-2023：12个任务
- UWA Day 2021-2023：12个任务

---

## 使用说明

### 1. 启动 Orchestrator

```bash
python autorun/orchestrator.py
```

Orchestrator 会自动：
- 按优先级挑选任务
- 跳过需要特殊权限的任务（skipped）
- 写入批次文件到 `cursor_workspace/input/`
- 等待 Worker 处理
- 更新任务状态

### 2. 处理任务

在 Cursor 中：
```
@cursor-worker 请处理 input 目录中的最新批次任务
```

Worker 会：
- 读取批次文件
- 处理每个任务
- 写入结果到 `cursor_workspace/output/`

### 3. 验证任务

```bash
# 验证任务文件
python autorun/task_validator.py

# 检查状态
python autorun/check_status.py
```

---

## 注意事项

### 1. 任务粒度

- ✅ 每个任务最多5个文档
- ✅ 推荐每个文档一个任务（最佳实践）
- ✅ 内容补充任务已按推荐粒度拆分

### 2. 特殊权限

- ⚠️ GDC 2021-2024年任务需要GDC Vault权限
- ⚠️ 这些任务已标记为 `skipped`
- ⚠️ 等待人工获取资源后，创建新的资源补充任务

### 3. 任务可执行性

- ✅ 所有任务都包含可执行信息（`target_files`、`schedule_url`、`search_keywords`）
- ✅ 已通过验证工具检查
- ✅ 符合新规范要求

---

## 文件清单

- `autorun/tasks.json` - 主任务文件（包含所有任务）
- `autorun/tasks_2021_2025.json` - 近五年任务文件（仅新任务）
- `docs/collection-plan-2021-2025.md` - 任务规划文档
- `autorun/generate_tasks_2021_2025.py` - 任务生成脚本
- `autorun/merge_tasks.py` - 任务合并脚本

---

**状态：** ✅ 任务已生成并合并  
**下一步：** 启动 Orchestrator 开始处理

