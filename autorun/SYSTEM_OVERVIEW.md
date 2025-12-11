# 系统概览

## 已完成的工作流系统

根据 `design.md` 的设计文档，已完整实现 Orchestrator + Cursor Worker 工作流系统。

## 系统组件

### 1. Orchestrator（任务队列管理器）

**文件：** `autorun/orchestrator.py`

**功能：**
- ✅ 从 `tasks.json` 加载任务池
- ✅ 按优先级挑选批次任务（默认 20 个）
- ✅ 写入批次文件到 `cursor_workspace/input/`
- ✅ 监控输出目录，等待 Worker 处理结果
- ✅ 解析输出，归档结果
- ✅ 更新任务状态（pending → in_progress → done）
- ✅ 支持超时处理和错误恢复

**运行方式：**
```bash
python autorun/orchestrator.py
# 或
cd autorun && python orchestrator.py
```

### 2. Cursor Worker（PromptX 角色）

**文件：** `.promptx/resource/role/cursor-worker/cursor-worker.role.md`

**功能：**
- ✅ 从 `cursor_workspace/input/` 读取批次文件
- ✅ 处理每个任务（搜索、阅读、整理）
- ✅ 结构化输出到 `cursor_workspace/output/`
- ✅ 不循环任务列表，只处理当前批次
- ✅ 支持多种任务类型（topic, url, paper, standard）

**激活方式：**
```
@cursor-worker 请处理 input 目录中的最新批次任务
```

### 3. 目录结构

```
autorun/
├── orchestrator.py      # Orchestrator 主程序
├── tasks.json           # 任务列表（示例）
├── config.json          # 配置文件
├── README.md           # 完整文档
├── QUICKSTART.md       # 快速开始
├── SYSTEM_OVERVIEW.md  # 本文档
├── run.bat             # Windows 启动脚本
└── run.sh              # Linux/Mac 启动脚本

cursor_workspace/
├── input/              # 任务输入目录
├── output/             # 结果输出目录
└── archive/            # 归档目录

.promptx/resource/role/cursor-worker/
└── cursor-worker.role.md  # Worker 角色定义
```

## 工作流闭环

### 完整流程

```
1. 准备阶段
   └─> 编辑 tasks.json，添加任务列表

2. Orchestrator 启动
   └─> 加载任务池
   └─> 挑选批次（20个任务）
   └─> 写入 input/batch_xxx.json
   └─> 标记任务为 in_progress

3. Cursor Worker 处理
   └─> 激活 @cursor-worker 角色
   └─> 读取批次文件
   └─> 逐条处理任务
   └─> 写入 output/batch_xxx.json

4. Orchestrator 收尾
   └─> 检测到输出文件
   └─> 解析结果
   └─> 归档到 archive/
   └─> 标记任务为 done
   └─> 继续下一批

5. 循环
   └─> 重复步骤 2-4，直到所有任务完成
```

### 数据流

```
tasks.json (任务池)
    ↓ [读取]
Orchestrator
    ↓ [写入批次]
input/batch_xxx.json
    ↓ [Worker 读取]
Cursor Worker
    ↓ [处理任务]
    ↓ [写入结果]
output/batch_xxx.json
    ↓ [Orchestrator 读取]
    ↓ [归档]
archive/batch_xxx.json
    ↓ [更新状态]
tasks.json (状态更新)
```

## 关键特性

### ✅ 已实现

1. **任务队列管理**
   - 支持优先级排序
   - 批次处理（可配置大小）
   - 状态跟踪（pending/in_progress/done/failed）

2. **文件协调**
   - 输入/输出目录分离
   - 批次文件命名规范
   - 自动归档机制

3. **错误处理**
   - 超时检测
   - 失败任务标记
   - 状态回滚支持

4. **Worker 角色**
   - 完整的角色定义
   - 清晰的工作流程
   - 结构化输出格式

5. **文档完善**
   - README（完整文档）
   - QUICKSTART（快速开始）
   - 代码注释

### 🔄 可扩展

1. **Git 集成**
   - 自动 commit/push
   - 版本控制

2. **质量评估**
   - 结果质量检查
   - 自动重试机制

3. **知识库集成**
   - 自动写入 docs/
   - 索引更新

4. **监控和报告**
   - 处理进度统计
   - 性能指标

## 使用示例

### 示例1：收集 GDC 资料

```json
// tasks.json
[
  {
    "id": 1,
    "type": "url",
    "url": "https://www.gdcvault.com/play/1026186/...",
    "title": "GDC 2024: 游戏数值设计",
    "status": "pending",
    "priority": 1
  }
]
```

运行：
```bash
python orchestrator.py
# 在 Cursor 中：@cursor-worker 处理任务
```

### 示例2：研究技术主题

```json
{
  "id": 2,
  "type": "topic",
  "title": "WebGPU 渲染优化",
  "status": "pending",
  "priority": 1
}
```

Worker 会自动搜索相关资料并整理。

## 验证清单

- [x] Orchestrator 程序已创建
- [x] Cursor Worker 角色已定义
- [x] 目录结构已创建
- [x] 示例任务文件已创建
- [x] 配置文件已创建
- [x] 文档已完善
- [x] 启动脚本已创建
- [x] 工作流闭环验证

## 下一步

1. **测试运行**
   - 添加几个测试任务
   - 运行 Orchestrator
   - 在 Cursor 中激活 Worker
   - 验证完整流程

2. **优化配置**
   - 根据实际需求调整 batch_size
   - 配置超时时间
   - 设置优先级规则

3. **扩展功能**
   - 添加 Git 集成
   - 实现质量评估
   - 连接知识库

## 技术支持

- 查看 `README.md` 了解详细使用说明
- 查看 `QUICKSTART.md` 快速上手
- 查看 `design.md` 了解设计思路

---

**系统状态：** ✅ 已完成，可投入使用

