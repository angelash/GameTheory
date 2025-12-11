# 快速开始指南

## 5 分钟上手

### 步骤 1：准备任务（1分钟）

编辑 `autorun/tasks.json`，添加你的任务：

```json
[
  {
    "id": 1,
    "type": "topic",
    "title": "你的主题",
    "status": "pending",
    "priority": 1
  }
]
```

### 步骤 2：启动 Orchestrator（1分钟）

**Windows:**
```bash
cd autorun
run.bat
```

**Linux/Mac:**
```bash
cd autorun
chmod +x run.sh
./run.sh
```

或直接运行：
```bash
python autorun/orchestrator.py
```

### 步骤 3：在 Cursor 中处理（2分钟）

当看到提示 "请在 Cursor 中运行 Worker 角色处理这一批任务..." 时：

在 Cursor 中输入：
```
@cursor-worker 请处理 input 目录中的最新批次任务
```

Worker 会自动：
- 读取批次文件
- 处理所有任务
- 写入结果文件

### 步骤 4：查看结果（1分钟）

- 结果文件：`cursor_workspace/output/batch_*.json`
- 任务状态：`autorun/tasks.json`（已更新为 done）

Orchestrator 会自动检测输出，更新状态，继续下一批。

## 完整工作流示例

```
1. 你：编辑 tasks.json，添加 100 个任务
2. 你：运行 python orchestrator.py
3. Orchestrator：挑选 20 个任务，写入 input/batch_xxx.json
4. 你：在 Cursor 中输入 @cursor-worker 处理任务
5. Worker：处理 20 个任务，写入 output/batch_xxx.json
6. Orchestrator：检测到输出，更新状态，继续下一批
7. 重复步骤 4-6，直到所有任务完成
```

## 常见场景

### 场景1：收集 GDC 资料

```json
{
  "id": 1,
  "type": "url",
  "url": "https://www.gdcvault.com/play/...",
  "title": "GDC 2024: 游戏数值设计",
  "status": "pending",
  "priority": 1
}
```

### 场景2：研究技术主题

```json
{
  "id": 2,
  "type": "topic",
  "title": "WebGPU 渲染管线优化",
  "status": "pending",
  "priority": 1
}
```

### 场景3：整理论文

```json
{
  "id": 3,
  "type": "paper",
  "title": "Game Balance Analysis",
  "status": "pending",
  "priority": 2
}
```

## 提示

- ✅ 一次添加多个任务，让系统自动分批处理
- ✅ 使用 priority 控制处理顺序
- ✅ 定期检查 output/ 目录查看结果
- ✅ 失败的任务可以改回 pending 重新处理

## 需要帮助？

查看完整文档：`autorun/README.md`

