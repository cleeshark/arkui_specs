# 特性规格

> Func-04-06-01-Feat-01 占位组件交叉引用：04-06-01「占位组件」无独立实现，实际能力由 05-16-01 NodeContainer + 05-16-02 ContentSlot 实现。本规格仅作 SDD 路由引用，不重复 AC/规则。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 占位组件交叉引用 |
| 特性编号 | Func-04-06-01-Feat-01 |
| 优先级 | P2 |
| 目标版本 | 引用 05-16-01（NodeContainer dyn `@since11`）+ 05-16-02（ContentSlot dyn `@since12`） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单（交叉引用） |

## 本次变更范围（Delta）

无新增变更。本特性为**交叉引用域**——04-06-01「占位组件」在代码库中无独立实现，实际规格在 05-16-01（NodeContainer）和 05-16-02（ContentSlot）。本规格不重复 AC/规则/数据模型，仅提供 SDD 路由转跳。

## 引用规格

### 05-16-01 NodeContainer

| 属性 | 值 |
|------|-----|
| FuncID | 05-16-01 |
| Spec 域 | `specs/05-ui-components/16-custom-placeholder-components/01-node-container/` |
| Feat 数 | 3 |
| 覆盖 | `NodeContainer(controller)` + `NodeController.makeNode` + `nodePtr_` 桥接 + IsArkTsFrameNode 守卫 + rebuild + 自定义 layout + 生命周期回调（bind/unbind 状态机）+ 复用 + 纹理导出 |
| 架构特征 | `NodeContainerNode : FrameNode`（有 Pattern/Layout/EventHub，单根，controller 驱动） |
| 入口 | [design.md](../../../05-ui-components/16-custom-placeholder-components/01-node-container/design.md) / [Feat-01](../../../05-ui-components/16-custom-placeholder-components/01-node-container/Feat-01-node-container-render-host-and-framenode-bridge-spec.md) |

### 05-16-02 ContentSlot

| 属性 | 值 |
|------|-----|
| FuncID | 05-16-02 |
| Spec 域 | `specs/05-ui-components/16-custom-placeholder-components/02-content-slot/` |
| Feat 数 | 1 |
| 覆盖 | `ContentSlot(content)` + `NodeContent` 多子节点管理 + UINode 语法节点（非 FrameNode）+ IsAdopted 守卫 + dirty 上传父链 + `XComponentType.NODE` 废弃继任 |
| 架构特征 | `ContentSlotNode : UINode`（无 Pattern/Layout，多子，命令式内容管理） |
| 入口 | [design.md](../../../05-ui-components/16-custom-placeholder-components/02-content-slot/design.md) / [Feat-01](../../../05-ui-components/16-custom-placeholder-components/02-content-slot/Feat-01-contentslot-syntax-node-and-nodecontent-management-spec.md) |

## NodeContainer vs ContentSlot 对比（引用）

| 维度 | NodeContainer（05-16-01） | ContentSlot（05-16-02） |
|------|--------------------------|----------------------|
| 节点基类 | `FrameNode`（有 Pattern/Layout/EventHub） | `UINode`（无 Pattern/Layout，纯语法节点） |
| 子节点模型 | 单根（`makeNode` 返回 1 个 FrameNode） | 多子（`NodeContent.addFrameNode`/`removeFrameNode`） |
| 绑定对象 | `NodeController`（TS，`nodePtr_` 跨界） | `Content`/`NodeContent`（多子管理器） |
| 生命周期 | `onWillBind/Bind/WillUnbind/Unbind` + `onAttach/Detach` + `aboutTo*` | attach/detach-to-main-tree callbacks |
| 尺寸/布局 | 自带 `NodeContainerLayoutAlgorithm`（MeasureContent nullopt） | 无布局——经 `PROPERTY_UPDATE_BY_CHILD_REQUEST` 上传父链 |
| `@since` | dynamic `@since11` / static `@since23` | dynamic `@since12` / static `@since23` |
| 继任 | — | `XComponentType.NODE @deprecated since 20` → ContentSlot |

## 用户故事

### US-1: 占位组件交叉引用

**作为** SDD 流程消费者,
**我想要** 查 04-06-01 时转跳到 05-16-01/02,
**以便** 找到占位组件的实际规格。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 查 04-06-01 占位组件 THEN 本规格引用 05-16-01（NodeContainer）+ 05-16-02（ContentSlot）作为实际实现 | 正常 |
| AC-1.2 | WHEN 查 05-16-01 THEN 3 个 Feat（渲染宿主/生命周期/复用+纹理导出）均 Baselined | 边界 |
| AC-1.3 | WHEN 查 05-16-02 THEN 1 个 Feat（ContentSlot 语法节点+NodeContent 管理）Baselined | 边界 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 查 04-06-01 | 转跳 05-16-01/02 规格 | 不重复规格 | AC-1.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | 交叉引用完整性 | 人工检查 + validate_specs | 05-16-01/02 spec 路径有效、链接可达 |
| VM-2 | 引用域 Feat Baselined | validate_specs | 05-16-01 3 Feat + 05-16-02 1 Feat 均 Baselined |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 范围边界明确（交叉引用，不重复规格）
- [x] 引用域规格完整（05-16-01 3 Feat + 05-16-02 1 Feat 均 Baselined）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContainer NodeController makeNode 占位组件（详见 05-16-01）"
  - repo: "openharmony/arkui_ace_engine"
    query: "ContentSlot NodeContent 占位组件（详见 05-16-02）"
```

**关键文档：** [05-16-01 design.md](../../../05-ui-components/16-custom-placeholder-components/01-node-container/design.md)、[05-16-02 design.md](../../../05-ui-components/16-custom-placeholder-components/02-content-slot/design.md)
