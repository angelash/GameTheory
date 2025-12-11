# PromptX 项目资源

本目录包含 GameTheory 项目的 PromptX 角色资源。

## 已创建的角色

### 1. game-numeric-designer（游戏数值设计师）
- 文件：`role/game-numeric-designer/game-numeric-designer.role.md`
- 专注：六维体验模型、数值平衡设计
- 记忆：已保存项目中的六维模型知识和设计原则

### 2. game-narrative-designer（游戏叙事设计师）
- 文件：`role/game-narrative-designer/game-narrative-designer.role.md`
- 专注：Film Noir叙事框架、故事结构设计
- 记忆：已保存项目中的Noir知识和叙事设计原则

### 3. game-system-designer（游戏系统设计师）
- 文件：`role/game-system-designer/game-system-designer.role.md`
- 专注：系统架构、机制设计
- 记忆：已保存项目中的系统设计原则和方法

### 4. game-balance-analyst（游戏平衡分析师）
- 文件：`role/game-balance-analyst/game-balance-analyst.role.md`
- 专注：数据驱动的平衡分析
- 记忆：已保存项目中的平衡分析方法和工作流

### 5. game-research-archivist（游戏资料研究归档师）
- 文件：`role/game-research-archivist/game-research-archivist.role.md`
- 专注：游戏开发资料的自动化收集、提炼与归档
- 能力：GDC资料收集、内容提炼、知识库维护

## 使用方法

### 在 Cursor 中使用

1. 使用 `@角色名` 激活角色：
   ```
   @game-numeric-designer 请帮我分析这个数值设计
   ```

2. 使用 PromptX action 激活：
   ```
   激活 game-numeric-designer
   ```

### 使用 PromptX 功能

- **recall**：检索角色的记忆
  ```
  recall(game-numeric-designer, "六维模型")
  ```

- **remember**：保存新的设计经验
  ```
  remember(game-numeric-designer, [记忆内容])
  ```

## 角色记忆系统

每个角色都已经保存了项目中的核心知识：

- **game-numeric-designer**：六维模型、体验时间线、数值设计checklist
- **game-narrative-designer**：Film Noir框架、城市系统、真相曲线
- **game-system-designer**：系统化思维、机制联动、健康度管理
- **game-balance-analyst**：不平衡识别、数据分析、修复策略
- **game-research-archivist**：资料收集方法、内容提炼技巧、归档规范

这些记忆会随着使用不断积累，让角色越来越智能。

## 查看所有可用角色

使用 PromptX discover 功能：
```
discover(focus: "roles")
```

## 修改角色

如需修改角色定义，可以使用 role-creator 工具：
```
toolx(tool: "tool://role-creator", mode: "execute", parameters: {
  role: "game-numeric-designer",
  action: "edit",
  file: "game-numeric-designer.role.md",
  edits: [...]
})
```

或直接编辑对应的 `.role.md` 文件。

