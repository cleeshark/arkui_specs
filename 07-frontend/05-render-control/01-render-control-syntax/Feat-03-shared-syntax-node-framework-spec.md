# 特性规格

> Func-07-05-01-Feat-03 渲染控制语法共享框架：固化 `ForEachBaseNode` 共享契约（`IsSyntaxNode()=true`、`MoveData`/`GetFrameNode` 纯虚、onMove/drag virtuals + `FireOn*` 默认实现、`DisableRecycle`/`DisableChildrenAndCachesRecycle`/`SetEnableSyncLoad`/`SetIsSyncLoad`）、`UINode::IsSyntaxNode` 标记与继承体系（ForEach/LazyForEach/Repeat/RepeatVirtualScroll(2)/ArkoalaForEachNode 均 `: public ForEachBaseNode`；IfElseNode 直接继承 UINode）、节点生命周期（`GetOrCreate*Node` via ElementRegister + ViewStackProcessor Push/PopContainer）、NG/legacy 管线选择（`IsCurrentUseNewPipeline`/`NG_BUILD`）、C-API `ArkoalaForEachNode` 行为规格。本特性为 framework-internal，源码即规格，无 SDK 契约交叉校验。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 渲染控制语法共享框架 |
| 特性编号 | Func-07-05-01-Feat-03 |
| 优先级 | P2 |
| 目标版本 | framework-internal（随 NG 渲染管线，无独立 `@since`；NG/legacy 管线运行时切换） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01（if/else）/Feat-02（ForEach）；本特性聚焦 ForEach/LazyForEach/Repeat 等循环节点共享的 `ForEachBaseNode` 契约、`IsSyntaxNode` 标记、生命周期与管线选择。LazyForEach（07-05-02）/Repeat（07-05-03）的具体 diff/缓存语义见各自功能域。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/01-render-control-syntax/design.md` | Baselined |
| 共享循环节点基类 | `frameworks/core/components_ng/syntax/for_each_base_node.h` | — |
| UINode 基类（IsSyntaxNode 标记） | `frameworks/core/components_ng/base/ui_node.h` | — |
| C-API ForEach 节点 | `frameworks/core/components_ng/syntax/arkoala_for_each_node.h` / `.cpp` | — |
| 子类节点（继承关系证据） | `for_each_node.h`/`lazy_for_each_node.h`/`repeat_node.h`/`repeat_virtual_scroll_node.h`（v1，已废弃）/`repeat_virtual_scroll_2_node.h` | — |
| Model 工厂管线选择 | `for_each_model_ng.cpp`/`if_else_model_ng.cpp`/`js_foreach.cpp`/`js_if_else.cpp` | — |

> 需求基线详见 proposal.md。本特性 framework-internal，源码即规格。

---

## 用户故事

### US-1: ForEachBaseNode 共享契约

**作为** 框架维护者,
**我想要** 循环节点（ForEach/LazyForEach/Repeat 等）共享统一基类契约,
**以便** 复用 onMove/drag、回收、sync-load 等通用能力。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 循环节点继承 THEN `ForEachBaseNode : public UINode`（`for_each_base_node.h:23`），为所有循环节点共享基类 | 正常 |
| AC-1.2 | WHEN 子类须实现 diff/数据移动 THEN `ForEachBaseNode` 声明纯虚 `MoveData(int32_t from,int32_t to,bool isNeedUpdate)`（`:28`）、`GetFrameNode(int32_t index)`（`:29`），子类各自覆写 | 正常 |
| AC-1.3 | WHEN `ForEachBaseNode::IsSyntaxNode()` THEN 覆写返回 `true`（`:66-69`），所有循环节点子类自动为语法节点 | 正常 |
| AC-1.4 | WHEN onMove/drag 回调 THEN 基类提供虚 hook + 默认实现：`RecycleItems`（`:30`）、`FireOnMove`（`:31-36`，仅 from!=to 触发 `onMoveEvent_`）、`FireOnLongPress`（`:38`）、`FireOnDragStart`（`:45`）、`FireOnMoveThrough`（`:52`）、`FireOnDrop`（`:59`） | 正常 |
| AC-1.5 | WHEN 回调存储 THEN 基类持有 `onMoveEvent_`/`onLongPressEvent_`/`onDragStartEvent_`/`onMoveThroughEvent_`/`onDropEvent_`（`:101-105`） | 正常 |
| AC-1.6 | WHEN 回收控制 THEN 基类提供 `static DisableRecycle(RefPtr<UINode>)`（`:71-88`，递归处理 `RecycleDummyNode`/`ForEachBaseNode`）、`DisableChildrenAndCachesRecycle`（`:90`）、`SetEnableSyncLoad`/`SetIsSyncLoad`（`:97-98`，默认 no-op 由子类覆写） | 正常 |

### US-2: 语法节点标记与继承体系

**作为** 框架维护者,
**我想要** 统一的 `IsSyntaxNode` 标记与清晰的继承体系,
**以便** 渲染管线识别语法节点、区分循环与分支。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `UINode::IsSyntaxNode()` THEN 基类默认 `false`（`ui_node.h:240`），由 `ForEachBaseNode`/`IfElseNode`/`ConditionScopeNode` 等覆写为 `true` | 正常 |
| AC-2.2 | WHEN 循环节点继承 THEN `ForEachNode`/`LazyForEachNode`/`RepeatNode`/`RepeatVirtualScrollNode`（v1，已废弃）/`RepeatVirtualScroll2Node`/`ArkoalaForEachNode` 均 `: public ForEachBaseNode`（各 `*_node.h`） | 正常 |
| AC-2.3 | WHEN if/else 节点 THEN `IfElseNode : public UINode`（`if_else_node.h`，**直接继承 UINode，不继承 ForEachBaseNode**），仅共享 `IsSyntaxNode` 标记 | 边界 |

### US-3: 节点生命周期

**作为** 框架维护者,
**我想要** 语法节点经统一的 Create/Pop 生命周期管理,
**以便** 节点正确挂载到 ElementRegister 与 ViewStackProcessor。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN Model `Create()` THEN 经 `ViewStackProcessor::ClaimNodeId()`→`*Node::GetOrCreate*Node(nodeId)`（经 `ElementRegister` 复用/创建）→`Push` 入栈（如 `if_else_model_ng.cpp:23-29`、`for_each_model_ng.cpp:36-46`） | 正常 |
| AC-3.2 | WHEN Model `Pop()` THEN `ViewStackProcessor::PopContainer()`（如 `if_else_model_ng.cpp:31-34`、`for_each_model_ng.cpp:25-29`） | 正常 |
| AC-3.3 | WHEN `GetOrCreate*Node` THEN 经 `ElementRegister::GetInstance()->GetItemById(nodeId)` 复用既有节点或 `MakeRefPtr` 新建并 `AddUINode`（如 `lazy_for_each_node.cpp:37-60`） | 正常 |

### US-4: NG/legacy 管线选择 + C-API

**作为** 框架维护者,
**我想要** Model 工厂按管线选 NG/legacy、C-API 有独立节点,
**以便** 多范式/多管线兼容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `*Model::GetInstance()` THEN `NG_BUILD` 编译时直接返回 NG `*ModelNG`；否则运行时 `Container::IsCurrentUseNewPipeline()` 选 NG 或 legacy `*ModelImpl`（如 `js_if_else.cpp:24-38`、`js_foreach.cpp:32-46`） | 正常 |
| AC-4.2 | WHEN C-API（Arkoala）路径 THEN `ArkoalaForEachNode : public ForEachBaseNode`（`arkoala_for_each_node.h:28`）为 ForEach 的 C-API 对应节点；if/else 对应 `ConditionScopeNode`（`arkoala_condition_scope.h:27`，详见 Feat-01） | 正常 |
| AC-4.3 | WHEN legacy（非 NG）管线 THEN 走 `frameworks/bridge/declarative_frontend/jsview/models/*_model_impl.*` 的 legacy Model 实现（如 `for_each_model_impl`/`if_else_model_impl`） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.6 | R-1,R-2 | T-3 | UT：ForEachBaseNode 契约 | `for_each_base_node.h:23-105` |
| AC-2.1~2.3 | R-3,R-4 | T-3 | UT：IsSyntaxNode 标记 + 继承体系 | `ui_node.h:240`、各 `*_node.h` |
| AC-3.1~3.3 | R-5 | T-3 | UT：Create/Pop/GetOrCreate 生命周期 | `if_else_model_ng.cpp:23-34`、`for_each_model_ng.cpp:25-46` |
| AC-4.1~4.3 | R-6,R-7 | T-3 | UT：NG/legacy 选择 + C-API 节点 | `js_if_else.cpp:24-38`、`arkoala_for_each_node.h:28` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 循环节点继承 | 均 `: public ForEachBaseNode`，共享 IsSyntaxNode/onMove/drag/回收契约 | IfElseNode 例外 | AC-1.1,AC-2.2 |
| R-2 | 行为 | ForEachBaseNode 契约 | 纯虚 MoveData/GetFrameNode；虚 onMove/drag hook+默认实现；DisableRecycle/SetEnableSyncLoad 等 | FireOnMove 仅 from!=to | AC-1.2,AC-1.4,AC-1.6 |
| R-3 | 行为 | IsSyntaxNode 标记 | UINode 默认 false；ForEachBaseNode/IfElseNode/ConditionScopeNode 覆写 true | — | AC-1.3,AC-2.1 |
| R-4 | 边界 | IfElseNode 继承 | 直接继承 UINode（非 ForEachBaseNode），仅共享 IsSyntaxNode | 与循环节点不同 | AC-2.3 |
| R-5 | 行为 | 节点生命周期 | Create→ClaimNodeId+GetOrCreate(via ElementRegister)+Push；Pop→PopContainer | GetOrCreate 复用优先 | AC-3.1~3.3 |
| R-6 | 行为 | Model 管线选择 | NG_BUILD 或 IsCurrentUseNewPipeline 选 NG，否则 legacy | — | AC-4.1,AC-4.3 |
| R-7 | 行为 | C-API 节点 | ArkoalaForEachNode(:ForEachBaseNode) 对应 ForEach；ConditionScopeNode 对应 if/else | 共用 tag（Feat-01） | AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 共享契约 | UT | ForEachBaseNode 纯虚/hook/DisableRecycle |
| VM-2 | AC-2.x 继承体系 | UT | IsSyntaxNode 标记、子类继承、IfElseNode 例外 |
| VM-3 | AC-3.x 生命周期 | UT | Create/Pop/GetOrCreate |
| VM-4 | AC-4.x 管线/C-API | UT | NG/legacy 选择、ArkoalaForEachNode |

## API 变更分析

> 本特性 framework-internal，无公开 API 变更（ForEachBaseNode 等为内部基类，非 SDK 契约）。

### 新增 API

N/A（framework-internal）。

### 变更/废弃 API

N/A。

## 接口规格

> framework-internal，无公开接口规格（内部 C++ 基类契约）。核心内部契约见「规则定义」与各 `*_node.h`/`for_each_base_node.h`。

## 兼容性声明

- **已有 API 行为变更:** 否（framework-internal 存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** framework-internal（随 NG 管线，无独立版本）。
- **API 版本号策略:** N/A（内部基类）。

> **继承体系风险（F-base）：** `IfElseNode` 直接继承 `UINode`（非 `ForEachBaseNode`），仅共享 `IsSyntaxNode` 标记，与循环节点继承路径不同；下游勿假设所有语法节点共享 ForEachBaseNode（风险 RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| ForEachBaseNode 共享契约 | 循环节点共享 IsSyntaxNode/onMove/drag/回收 | AC-1.1,AC-1.4 |
| IfElseNode 例外 | 直接继承 UINode，非 ForEachBaseNode | AC-2.3 |
| IsSyntaxNode 标记 | UINode 默认 false，语法节点覆写 true | AC-2.1 |
| NG/legacy 双管线 | Model 工厂运行时/编译时选择 | AC-4.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可维护性 | 循环节点共享基类减少重复（onMove/drag/回收） | 架构评审 | `for_each_base_node.h:23-105` |
| 可靠性 | NG/legacy 双管线 + C-API 独立节点保证多范式兼容 | UT | `js_if_else.cpp:24-38`、`arkoala_for_each_node.h:28` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | framework-internal 一致 | UT | — |
| 平板 | 无差异 | 同上 | UT | — |
| 折叠屏 | 无差异 | 同上 | UT | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | framework-internal | — |
| 大字体 | 否 | 无直接关联 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 否 | framework-internal，随管线演进 | — |
| 生态兼容 | 是 | NG/legacy + C-API 多范式兼容 | AC-4.1,AC-4.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 渲染控制语法共享框架
  作为 框架维护者
  我想要 循环节点共享 ForEachBaseNode 契约
  以便 复用 onMove/drag/回收等通用能力

  Scenario Outline: 继承体系
    Given 一个语法节点 <节点>
    When 检查继承
    Then <基类>

    Examples:
      | 节点 | 基类 |
      | ForEachNode | ForEachBaseNode |
      | LazyForEachNode | ForEachBaseNode |
      | RepeatNode | ForEachBaseNode |
      | ArkoalaForEachNode | ForEachBaseNode |
      | IfElseNode | UINode（直接，非 ForEachBaseNode） |

  Scenario: 管线选择
    Given Model::GetInstance()
    When NG_BUILD 或 IsCurrentUseNewPipeline()
    Then 返回 NG ModelNG，否则 legacy ModelImpl

  Scenario: 节点生命周期
    Given Model Create()
    When ClaimNodeId→GetOrCreate(via ElementRegister)+Push
    Then 节点挂载；Pop→PopContainer 出栈
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做共享框架；if/else 见 Feat-01、ForEach 见 Feat-02；LazyForEach/Repeat 具体语义见 07-05-02/03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ForEachBaseNode 共享契约 IsSyntaxNode MoveData GetFrameNode onMove/drag virtuals DisableRecycle"
  - repo: "openharmony/arkui_ace_engine"
    query: "UINode IsSyntaxNode 标记 语法节点继承体系 IfElseNode 直接继承 UINode"
  - repo: "openharmony/arkui_ace_engine"
    query: "语法节点 GetOrCreate ElementRegister ViewStackProcessor Create/Pop 生命周期"
  - repo: "openharmony/arkui_ace_engine"
    query: "Model GetInstance IsCurrentUseNewPipeline NG/legacy ArkoalaForEachNode C-API"
```

**关键文档：** `frameworks/core/components_ng/syntax/for_each_base_node.h`、`frameworks/core/components_ng/base/ui_node.h`、`frameworks/core/components_ng/syntax/arkoala_for_each_node.h`、`frameworks/core/components_ng/syntax/for_each_model_ng.cpp`
