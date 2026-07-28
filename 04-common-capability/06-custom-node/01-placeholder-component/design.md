# 架构设计

> 确认目标仓和模块的架构约束、关键设计决策、Spec 拆分方向。

## 设计元数据

| Field | Content |
|-------|---------|
| Design ID | `DESIGN-Func-04-06-01` |
| 关联需求 | 已有能力补录——交叉引用域 |
| 关联 Epic | 无 |
| 目标 Feature | Feat-01 占位组件交叉引用（基线） |
| 复杂度 | 简单 |
| 目标版本 | 引用目标：05-16-01 NodeContainer（dynamic `@since11`）、05-16-02 ContentSlot（dynamic `@since12`） |
| Owner | ArkUI SIG |
| 状态 | Baselined（交叉引用域，不重复规格） |

## 需求基线

> 本功能域（04-06-01 占位组件）在代码库中**无独立实现**。占位组件的实际能力由组件层的两个功能域实现：

| 实现域 | 功能域 | 覆盖 |
|--------|--------|------|
| **05-16-01 NodeContainer** | `specs/05-ui-components/16-custom-placeholder-components/01-node-container/` | `NodeContainer(controller: NodeController)` + `NodeController.makeNode` + 声明式↔命令式 FrameNode 桥接 + 生命周期回调 + 复用与纹理导出（3 Feat） |
| **05-16-02 ContentSlot** | `specs/05-ui-components/16-custom-placeholder-components/02-content-slot/` | `ContentSlot(content: Content)` + `NodeContent` 多子节点管理 + UINode 语法节点（非 FrameNode）+ IsAdopted 守卫（1 Feat） |

**不重复规格**：本域仅作为 04-06 自定义节点族的概念入口（占位组件 = 在声明式树中为命令式/custom 节点提供挂载位置的组件），具体规格详见上述两个引用域。

## 上下文和现状

### 涉及仓和模块

| 仓库 | 补充架构说明 |
|------|-------------|
| `arkui_ace_engine` | 占位组件无独立 04-06 模块；实现分别在 `pattern/node_container/`（05-16-01）和 `syntax/content_slot_node.*`（05-16-02） |

### 调用链层级分析

> 占位组件的调用链详见引用域：

| 层 | 模块 | 职责 | 修改类型 | 引用域 |
|----|------|------|---------|--------|
| 1–12 | NodeContainer 全链 | `NodeContainerNode`（FrameNode 子类）+ `NodeContainerPattern`（渲染宿主+layout）+ `NodeContainerEventHub`（生命周期）+ `nodePtr_` 桥接 + IsArkTsFrameNode 守卫 | 现状 | [05-16-01 design.md](../../05-ui-components/16-custom-placeholder-components/01-node-container/design.md) |
| 1–9 | ContentSlot 全链 | `ContentSlotNode`（UINode 非 FrameNode）+ `NodeContent`（多子节点管理）+ IsAdopted 守卫 + dirty 上传父链 | 现状 | [05-16-02 design.md](../../05-ui-components/16-custom-placeholder-components/02-content-slot/design.md) |

## 不涉及项承接

| 维度 | 设计结论 |
|------|---------|
| 独立实现 | 不涉及——04-06-01 无独立代码，详见 05-16-01/02 |
| 重复规格 | 不涉及——本域仅交叉引用，不重复 AC/规则/数据模型 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|--------|------|---------|----------------|---------|------|
| ADR-1 | 04-06-01 与 05-16 的关系 | 04-06-01「占位组件」为**概念入口**，实际规格在 05-16-01（NodeContainer）+ 05-16-02（ContentSlot） | (a) 在 04-06-01 重复规格；(b) 删除 04-06-01 FuncID | 避免重复维护两份规格；04-06 保留概念入口供 SDD 路由 | 下游 SDD 查 04-06-01 时应转跳 05-16 |

## 设计骨架

### 骨架范围

| 骨架项 | 目标 | 不包含 | 验证方式 |
|--------|------|--------|---------|
| 交叉引用 | 链接 05-16-01/02 规格 | 重复 AC/规则/数据模型 | 人工检查链接有效 |

## 后续 Task 拆分

| Task ID | 目标 | 受影响文件 | 依赖 |
|---------|------|----------|------|
| T-1 | Feat-01 占位组件交叉引用（基线） | 本 design.md + Feat-01 引用规格 | 05-16-01 + 05-16-02 已 Baselined |

## 构建系统影响

无变更（交叉引用域，无代码）。

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|---------|-------|
| FuncID 04-06-01 与 05-16-01/02 概念重叠 | 架构 | 低 | 本 design.md 交叉引用标注；SDD 查 04-06-01 转跳 05-16 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认（交叉引用域）
- [x] 不涉及项已承接（无独立实现）
- [x] 引用域规格完整（05-16-01 3 Feat + 05-16-02 1 Feat 均 Baselined）
- [x] 关键设计决策有理由和影响说明
- [x] 风险和开放问题有 Owner

**结论:** 通过（交叉引用域，不重复规格）
