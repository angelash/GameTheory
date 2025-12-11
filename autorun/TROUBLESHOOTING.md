# Orchestrator 故障排除指南

## 问题：Orchestrator 没有反应

### 症状
- Orchestrator 启动后没有继续处理任务
- 任务卡在 `in_progress` 状态
- 输入目录有批次文件，但没有对应的输出文件

### 原因分析

1. **等待用户输入**（已修复）
   - 旧版本在输出超时时会调用 `input()` 等待用户输入
   - 如果不在交互式终端运行，程序会卡住
   - **解决方案**：已改为自动回滚，无需用户输入

2. **输出文件未生成**
   - Cursor Worker 尚未处理批次任务
   - 处理时间超过超时限制（默认1小时）
   - 输出文件名不匹配

3. **Orchestrator 未运行**
   - 程序已退出或崩溃
   - 需要重新启动

### 解决方案

#### 方案1：检查状态
```bash
python autorun/check_status.py
```

这会显示：
- 任务状态统计
- 输入/输出文件情况
- 未匹配的批次

#### 方案2：手动处理批次
如果发现有未处理的批次文件，在 Cursor 中运行：
```
@cursor-worker 请处理 input 目录中的最新批次任务
```

#### 方案3：重新启动 Orchestrator
```bash
python autorun/orchestrator.py
```

Orchestrator 会自动：
- 检测已完成的输出文件
- 更新任务状态
- 继续处理下一批任务

#### 方案4：手动更新任务状态
如果任务卡在 `in_progress`，可以手动编辑 `autorun/tasks.json`，将状态改为 `pending`。

### 优化说明

**已修复的问题：**
- ✅ 移除了 `input()` 调用，改为自动回滚
- ✅ Orchestrator 现在可以在非交互模式下运行
- ✅ 超时后自动回滚任务，无需人工干预

**工作流程：**
1. Orchestrator 创建批次文件 → `cursor_workspace/input/batch_*.json`
2. 等待 Cursor Worker 处理（最多1小时）
3. 如果超时：自动回滚任务状态为 `pending`，继续下一轮
4. 如果检测到输出：更新任务状态为 `done`，继续下一批

### 常见问题

**Q: Orchestrator 一直等待输出怎么办？**
A: 检查 `cursor_workspace/output/` 目录是否有对应的输出文件。如果没有，在 Cursor 中运行 Worker 处理。

**Q: 任务一直卡在 in_progress？**
A: 运行 `python autorun/check_status.py` 查看状态，然后手动处理批次或重新启动 Orchestrator。

**Q: 如何让 Orchestrator 在后台运行？**
A: 可以使用 `nohup` 或 `screen`/`tmux`：
```bash
# Linux/Mac
nohup python autorun/orchestrator.py > orchestrator.log 2>&1 &

# 或使用 screen
screen -S orchestrator
python autorun/orchestrator.py
# Ctrl+A, D 分离会话
```

**Q: 如何查看 Orchestrator 日志？**
A: 如果使用 `nohup`，日志在 `orchestrator.log`。或者直接运行查看控制台输出。

### 最佳实践

1. **定期检查状态**
   ```bash
   python autorun/check_status.py
   ```

2. **监控输出目录**
   - 确保 Worker 及时处理批次
   - 检查输出文件是否正确生成

3. **任务优先级**
   - 高优先级任务会优先处理
   - 可以调整 `priority` 字段控制顺序

4. **批次大小**
   - 默认每批20个任务
   - 可以在 `orchestrator.py` 中调整 `BATCH_SIZE`

---

**最后更新：** 2025-12-11  
**版本：** 已优化自动处理逻辑

