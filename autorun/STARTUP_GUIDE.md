# Orchestrator 启动指南

> 近五年（2021-2025）会议资料收集任务已准备就绪

**准备日期：** 2025-12-11  
**任务总数：** 571个  
**验证状态：** ✅ 全部通过

---

## 快速开始

### 1. 验证任务文件

```bash
python autorun/task_validator.py
```

**预期输出：**
```
[OK] 所有任务验证通过！
  总任务数: 571
  有效任务: 571
```

### 2. 启动 Orchestrator

```bash
python autorun/orchestrator.py
```

**Orchestrator 会自动：**
- 按优先级挑选任务（优先级1最高）
- 跳过需要特殊权限的任务（skipped）
- 写入批次文件到 `cursor_workspace/input/`
- 等待 Worker 处理
- 更新任务状态

### 3. 处理任务（在 Cursor 中）

```
@cursor-worker 请处理 input 目录中的最新批次任务
```

**Worker 会：**
- 读取批次文件
- 处理每个任务（内容补充或新建文档）
- 写入结果到 `cursor_workspace/output/`

---

## 任务统计

### 按状态

| 状态 | 数量 | 说明 |
|------|------|------|
| pending | 约540 | 待处理任务 |
| done | 34 | 已完成任务（2025年第一批） |
| skipped | 4 | 需要GDC Vault权限 |
| **总计** | **571** | |

### 按优先级

| 优先级 | 数量 | 说明 |
|--------|------|------|
| 1 | 94 | GDC 2025内容补充（最高优先级） |
| 2 | 29 | 2025年其他会议内容补充 |
| 3 | 19 | 2024年新建文档 |
| 4 | 33 | 2021-2023年新建文档 |
| 5 | 4 | 需要特殊权限的任务 |
| 其他 | 392 | 现有任务（已完成或待处理） |

### 按会议类型

| 会议 | 任务数 | 说明 |
|------|-------|------|
| GDC | 98 | 94个内容补充 + 4个新建文档（skipped） |
| Unreal Fest | 39 | 15个内容补充 + 24个新建文档 |
| Unite | 21 | 5个内容补充 + 16个新建文档 |
| UWA Day | 21 | 9个内容补充 + 12个新建文档 |
| 其他 | 392 | 现有任务 |
| **总计** | **571** | |

---

## 执行流程

### 标准流程

```
1. Orchestrator 启动
   → 加载 tasks.json
   → 统计任务状态

2. 挑选批次
   → 筛选 pending 状态
   → 跳过 requires_permission=True 的任务
   → 按优先级排序
   → 取前 20 个任务（BATCH_SIZE）

3. 写入批次文件
   → cursor_workspace/input/batch_xxx.json
   → 标记任务为 in_progress

4. 等待 Worker 处理
   → 超时1小时自动回滚

5. 处理输出
   → 读取 cursor_workspace/output/batch_xxx.json
   → 根据实际状态更新任务状态
   → 验证任务完成度

6. 继续下一批
   → 循环直到没有 pending 任务
```

### 状态更新规则

**Orchestrator 会根据输出文件中的实际状态更新：**
- `success` + 验证通过 → `done`
- `partial` → `partial`（保持 in_progress）
- `pending` → `pending`（回滚）
- `failed` → `failed`
- `skipped` → `skipped`

---

## 监控和检查

### 检查任务状态

```bash
python autorun/check_status.py
```

**显示：**
- 任务状态统计
- 进行中的任务
- 输入/输出目录状态
- 未匹配的批次

### 验证任务文件

```bash
python autorun/task_validator.py
```

**检查：**
- 任务格式是否正确
- 必填字段是否完整
- 任务粒度是否符合要求

---

## 注意事项

### 1. 任务粒度

- ✅ 每个任务最多5个文档
- ✅ 内容补充任务已按推荐粒度拆分（每个文档一个任务）
- ✅ 新建文档任务按批次拆分（每批最多5个）

### 2. 特殊权限

- ⚠️ GDC 2021-2024年任务需要GDC Vault权限
- ⚠️ 这些任务已标记为 `skipped`
- ⚠️ Orchestrator 会自动跳过这些任务
- ⚠️ 等待人工获取资源后，创建新的资源补充任务

### 3. 任务可执行性

- ✅ 所有任务都包含可执行信息
  - 内容补充任务：`target_files`
  - 新建文档任务：`schedule_url` + `search_keywords`
- ✅ 已通过验证工具检查
- ✅ 符合新规范要求

---

## 文件清单

### 核心文件

- `autorun/tasks.json` - 主任务文件（571个任务）
- `autorun/orchestrator.py` - Orchestrator 主程序
- `autorun/task_validator.py` - 任务验证工具
- `autorun/check_status.py` - 状态检查工具

### 规划文档

- `docs/collection-plan-2021-2025.md` - 近五年任务规划
- `autorun/TASKS_2021_2025_README.md` - 任务说明文档
- `autorun/WORKFLOW_RULES.md` - 工作流规范
- `autorun/BEHAVIOR_STANDARDS.md` - 行为规范

### 工具脚本

- `autorun/generate_tasks_2021_2025.py` - 任务生成脚本
- `autorun/merge_tasks.py` - 任务合并脚本
- `autorun/fix_tasks_schedule_url.py` - 修复脚本

---

## 预期执行时间

### 第一阶段：内容补充（优先级1-2）

**任务数：** 123个  
**预计时间：** 2-3周  
**说明：** 补充已有框架文档的内容

### 第二阶段：新建文档（优先级2-3）

**任务数：** 约40个  
**预计时间：** 4-6周  
**说明：** 创建2024-2025年新文档

### 第三阶段：历史收集（优先级4）

**任务数：** 约30个  
**预计时间：** 6-8周  
**说明：** 收集2021-2023年历史文档

---

## 故障排除

### 问题1：Orchestrator 没有反应

**检查：**
```bash
python autorun/check_status.py
```

**可能原因：**
- 所有任务已完成
- 任务卡在 in_progress
- 输出文件未生成

### 问题2：任务验证失败

**检查：**
```bash
python autorun/task_validator.py
```

**修复：**
- 查看错误详情
- 修复任务格式
- 重新验证

### 问题3：批次文件未处理

**检查：**
- `cursor_workspace/input/` 目录
- 批次文件是否存在
- Worker 是否正常运行

---

**状态：** ✅ 准备就绪  
**下一步：** 启动 Orchestrator 开始处理

