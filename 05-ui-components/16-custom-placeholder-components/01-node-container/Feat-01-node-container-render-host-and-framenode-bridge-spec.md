# 特性规格

> Func-05-16-01-Feat-01 NodeContainer 渲染宿主与 FrameNode 桥接：固化 `NodeContainer(controller)`（dynamic `@since11` / static `@since23` + `@since26 staticonly` style-builder）、`NodeController.makeNode(uiContext): FrameNode|null`（必填 abstract，返回 null 则移除子节点）、declarative↔imperative 桥接（TS `__makeNode__` 暂存 FrameNode、C++ 经 `nodePtr_` 原生指针 `reinterpret_cast<NG::UINode*>` 跨界）、`IsArkTsFrameNode`/`GetIsRootBuilderNode` 准入守卫（拒绝声明式节点）、`AddBaseNode`/`CleanChild`/`RemakeNode`/`FireMakeNode`、`controller.rebuild()` 复用同一 `RemakeNode` 路径、自定义 `NodeContainerLayoutAlgorithm`（`MeasureContent` 返 `nullopt`、layoutPolicy 延迟、match-parent）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | NodeContainer 渲染宿主与 FrameNode 桥接 |
| 特性编号 | Func-05-16-01-Feat-01 |
| 优先级 | P1 |
| 目标版本 | dynamic `@since11`（NodeContainer/NodeController/makeNode/rebuild，`@atomicservice since12`）；static `@since23`（NodeContainer + NodeController 整套）+ `@since26 staticonly`（style-builder + `setNodeContainerOptions`） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。本特性为 Func-05-16-01（NodeContainer）首个 Feat，作为该功能域 design.md 基线。NodeController 生命周期回调（Feat-02）、复用与纹理导出（Feat-03）由后续 Feat 承接。FrameNode/BuilderNode/RenderNode（04-06）、UIContext 为独立 FuncID/模块，本规格仅作类型引用。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/16-custom-placeholder-components/01-node-container/design.md` | Baselined |
| Dynamic API（NodeContainer） | `interface/sdk-js/api/@internal/component/ets/node_container.d.ts` | — |
| Dynamic API（NodeController） | `interface/sdk-js/api/arkui/NodeController.d.ts` | — |
| Static API | `interface/sdk-js/api/arkui/component/nodeContainer.static.d.ets`、`interface/sdk-js/api/arkui/NodeController.static.d.ets` | — |
| TS NodeController | `frameworks/bridge/declarative_frontend/ark_node/src/node_controller.ts` | — |
| JS 桥接 | `frameworks/bridge/declarative_frontend/jsview/js_node_container.cpp` / `.h` | — |
| NG Pattern（渲染宿主） | `frameworks/core/components_ng/pattern/node_container/node_container_pattern.cpp` / `.h` | — |
| NG Model 工厂 | `frameworks/core/components_ng/pattern/node_container/node_container_model_ng.cpp` / `node_container_model.h` | — |
| NG Layout | `frameworks/core/components_ng/pattern/node_container/node_container_layout_algorithm.cpp` / `.h` | — |
| Native 模块/Modifier（rebuild/clean） | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_node_container_bridge.cpp`、`frameworks/core/interfaces/native/node/node_container_modifier.cpp` | — |
| UINode 守卫标志 | `frameworks/core/components_ng/base/ui_node.h`（IsArkTsFrameNode/GetIsRootBuilderNode） | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: NodeContainer 构造与 makeNode

**作为** 应用开发者,
**我想要** 用 `NodeContainer(controller)` 嵌入由 `NodeController.makeNode` 返回的 FrameNode,
**以便** 在声明式 UI 中承载命令式构建的自定义节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN dynamic 调用 `NodeContainer(controller: NodeController)`（`node_container.d.ts:36,51,96` `@since11`）THEN 返回 `NodeContainerAttribute`（空 `CommonMethod` 子类 `:66`，仅继承通用属性/事件） | 正常 |
| AC-1.2 | WHEN static 调用 `NodeContainer(controller)`（`nodeContainer.static.d.ets:74` `@since23` `@ComponentBuilder`）THEN 返回 `NodeContainerAttribute`（`:36` interface extends CommonMethod，含 `attributeModifier` `:48`） | 正常 |
| AC-1.3 | WHEN static 用 style-builder 形态 `NodeContainer(style)`（`:89` `@since26 staticonly` `@Builder`）THEN 须首调 `setNodeContainerOptions(controller)`（`:60` `@since26 staticonly`）末调 `applyAttributeFinish` | 边界 |
| AC-1.4 | WHEN 应用实现 `NodeController` 子类 THEN `makeNode(uiContext: UIContext): FrameNode\|null` 为 **abstract 必填**（`NodeController.d.ts:75` `@since11`；static `:57`）；未实现编译报错 | 正常 |
| AC-1.5 | WHEN `makeNode` 返回 `null` THEN 子节点被移除（按 doc `:66-68`），NodeContainer 无 base node | 边界 |

### US-2: declarative↔imperative 桥接

**作为** 框架维护者,
**我想要** 了解 TS NodeController 与 C++ NodeContainer 的跨界机制,
**以便** 理解命令式 FrameNode 如何挂到声明式宿主。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN NodeController 构造 THEN 持有 `_nodeContainerId: __InternalField__`（`_value=-1`+`__rootNodeOfNodeController__`，`node_controller.ts:16-29`） | 正常 |
| AC-2.2 | WHEN C++ 调 `__makeNode__` THEN TS `__makeNode__(uiContext)`（`:32-36`）调用户 `makeNode`、把返回 FrameNode 暂存 `_nodeContainerId.__rootNodeOfNodeController__` 并返回 | 正常 |
| AC-2.3 | WHEN `JSNodeContainer::SetNodeController`（`js_node_container.cpp:246-292`）THEN 读 controller 的 `__makeNode__` 属性（`:249-253`，非 function 则 `ResetNodeController` return），包成 `JsFunction`（`:257-259`） | 正常 |
| AC-2.4 | WHEN 注册的 C++ lambda 执行（`:261-280`）THEN `JAVASCRIPT_EXECUTION_SCOPE`+`ContainerScope`（`:262-263`）→`func->ExecuteJS` 调 JS `__makeNode__`（`:264-266`）→读返回 FrameNode 的 `nodePtr_` 原生指针（`:271`）→`reinterpret_cast<NG::UINode*>`+`AceType::Claim`（`:276-279`）返回 `RefPtr<NG::UINode>` | 正常 |
| AC-2.5 | WHEN 桥接跨界 THEN 经 `nodePtr_`（`NODEPTR_OF_UINODE` 常量 `:39`）原生指针 `reinterpret_cast`——**无 C++ NodeController 类**，C++ 对 controller 不透明（仅知 `__makeNode__` 函数属性 + `_nodeContainerId._value`） | 边界 |

### US-3: IsArkTsFrameNode 守卫与 AddBaseNode/CleanChild

**作为** 应用开发者,
**我想要** 只有命令式创建的节点能挂入 NodeContainer，声明式节点被拒绝,
**以便** 维护 declarative↔imperative 边界完整。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `FireMakeNode`（`node_container_model_ng.cpp:131-138`）THEN `pattern->RemakeNode()`（`:138`） | 正常 |
| AC-3.2 | WHEN `RemakeNode`（`node_container_pattern.cpp:46-52`）THEN `FireMakeFunction()`（返回 `makeFunc_()` 或 nullptr，`pattern.h:70-74`）→`AddBaseNode(newNode)` | 正常 |
| AC-3.3 | WHEN `AddBaseNode(newNode)`（`:54-72`）THEN 取旧 `GetChildAtIndex(0)`；旧==新或皆空则 return（`:57`）；否则 `RemoveChildAtIndex(0)`+`BuilderUtils::RemoveBuilderFromParent`（`:60-61`）；`newNode` 非空时 `CheckBeforeAddNode`→`host->AddChild(newNode,0)`+`AddBuilderToParent`+`UpdateGeometryTransition`（`:62-68`） | 正常 |
| AC-3.4 | WHEN `CheckBeforeAddNode`（`:26-43`）THEN 要求 `newNode->IsArkTsFrameNode()` **或** `GetIsRootBuilderNode()`（`:27-30`）；否则日志 `"Cannot return node created by declarative UI function"` 返回 false（节点被拒，不崩） | 异常 |
| AC-3.5 | WHEN 返回的节点已有父且父≠host THEN 父节点 reparent 警告（`:34-41`） | 边界 |
| AC-3.6 | WHEN `CleanChild`（`:74-80`）THEN `RemoveChildAtIndex(0)`+`MarkNeedFrameFlushDirty(PROPERTY_UPDATE_MEASURE)`（`:79`） | 正常 |
| AC-3.7 | WHEN AddBaseNode 完成 THEN `OnAddBaseNode()`+`host->MarkNeedFrameFlushDirty(PROPERTY_UPDATE_MEASURE)`（`:71`）——**仅 MEASURE 脏标记**，无 LAYOUT/RENDER | 边界 |

### US-4: rebuild()（controller 发起）

**作为** 应用开发者,
**我想要** 在 controller 侧主动调 `rebuild()` 重新构建 base node,
**以便** 数据变化后刷新嵌入的 FrameNode。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN controller 调 `rebuild()`（`NodeController.d.ts:142` `@since11`）THEN TS（`node_controller.ts:37-41`）在 `_nodeContainerId._value>=0` 时调 `getUINativeModule().nodeContainer.rebuild(_value)` | 正常 |
| AC-4.2 | WHEN `_nodeContainerId._value<0`（未绑定）THEN `rebuild()` 静默不派发（`:37-38` 守卫） | 边界 |
| AC-4.3 | WHEN native `NodeContainerBridge::Rebuild`（`arkts_native_node_container_bridge.cpp:18-26`）THEN `GetArkUINodeModifiers()->getNodeContainerModifier()->rebuild(nodeId)` | 正常 |
| AC-4.4 | WHEN `node_container_modifier.cpp:rebuild`（`:20-28`）THEN 经 `ElementRegister::GetNodeById`→`DynamicCast<FrameNode>`→`DynamicCast<NodeContainerPattern>`→`pattern->RemakeNode()`——**复用与初始渲染相同的 `RemakeNode→FireMakeFunction→AddBaseNode` 路径，无分叉** | 正常 |
| AC-4.5 | WHEN native `Clean`（`node_container_modifier.cpp:30-37`）THEN `pattern->CleanChild()`（同 modifier 表注册 `:42-60`） | 正常 |

### US-5: 内置布局行为（layout）

**作为** 框架维护者,
**我想要** NodeContainer 自身度量尺寸、子节点按约束/layoutPolicy 适配,
**以便** 嵌入节点正确布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN NodeContainer 布局 THEN `CreateLayoutAlgorithm`（`pattern.h:40-43`）返回 `NodeContainerLayoutAlgorithm`（extends `StackLayoutAlgorithm`）；`CreateLayoutProperty` 返回 `StackLayoutProperty`（`:35-38`） | 正常 |
| AC-5.2 | WHEN `MeasureContent`（`layout_algorithm.h:30-34`）THEN **返回 `std::nullopt`**——内容尺寸来自宿主自身 constraint/属性，非子节点测量 | 边界 |
| AC-5.3 | WHEN `Measure`（`layout_algorithm.cpp:24-59`）THEN `CreateChildConstraint`（`:28`）→遍历 `GetAllChildrenWithBuild`：`IsEnableChildrenMatchParent && layoutPolicy.has_value()` 且 width/height 非 NO_MATCH 则延迟入 `layoutPolicyChildren_`（`:38-47`） | 正常 |
| AC-5.4 | WHEN 子节点非延迟 THEN `RenderNode` tag 用 `Measure(std::nullopt)`、其余用 `Measure(layoutConstraint)`（`:48-52`）；后 `PerformMeasureSelf`（`:54`） | 正常 |
| AC-5.5 | WHEN 延迟子解析 THEN `IsEnableChildrenMatchParent` 时读 `frameSize` 调 `MeasureAdaptiveLayoutChildren(layoutWrapper,frameSize)`（`:55-58`） | 正常 |
| AC-5.6 | WHEN 匹配策略 THEN `IsEnableChildrenMatchParent`/`IsEnableMatchParent`/`IsEnableFix` 均 `true`（`pattern.h:118-131`），启用 match-parent/fix 尺寸策略 | 边界 |
| AC-5.7 | WHEN `Create`（`node_container_model_ng.cpp:22-30`）THEN 默认 `Alignment::TOP_LEFT`（`:29`）；C-API `CreateFrameNode` 同（`:140-145` 经 `ViewAbstract::SetAlign`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.5 | R-1,R-2,R-9 | T-1 | UT + SDK 比对 | `node_container.d.ts:36-108`、`NodeController.d.ts:47-142` |
| AC-2.1~2.5 | R-3,R-4 | T-1 | UT：JSNodeContainer 桥接 lambda | `node_controller.ts:16-41`、`js_node_container.cpp:246-292` |
| AC-3.1~3.7 | R-5,R-6,R-10 | T-1 | UT：RemakeNode/AddBaseNode/CheckBeforeAddNode | `node_container_pattern.cpp:26-80`、`ui_node.h:727-735` |
| AC-4.1~4.5 | R-7,R-8 | T-1 | UT + XTS：rebuild/Clean modifier | `node_controller.ts:37-41`、`node_container_modifier.cpp:20-37` |
| AC-5.1~5.7 | R-11,R-12 | T-1 | UT：NodeContainerLayoutAlgorithm | `node_container_layout_algorithm.cpp:24-59`、`pattern.h:35-43,118-131` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `NodeContainer(controller)` | 返回 NodeContainerAttribute；Create 设默认 TOP_LEFT | dyn @since11/static @since23 | AC-1.1,AC-1.2,AC-5.7 |
| R-2 | 行为 | NodeController.makeNode | abstract 必填；返回 FrameNode 挂为 base node；返回 null 移除子节点 | — | AC-1.4,AC-1.5 |
| R-3 | 行为 | TS __makeNode__ | 调用户 makeNode + 暂存 __rootNodeOfNodeController__ | — | AC-2.2 |
| R-4 | 行为 | C++ 桥接 lambda | ExecuteJS __makeNode__→读 nodePtr_→reinterpret_cast<NG::UINode*>→Claim | 无 C++ NodeController 类 | AC-2.3,AC-2.4,AC-2.5 |
| R-5 | 行为 | FireMakeNode/RemakeNode | RemakeNode→FireMakeFunction→AddBaseNode | — | AC-3.1,AC-3.2 |
| R-6 | 异常 | makeNode 返回非命令式节点 | CheckBeforeAddNode 拒绝（IsArkTsFrameNode 或 GetIsRootBuilderNode）+警告，不崩 | 仅命令式 ArkTsFrameNode/RootBuilderNode 准入 | AC-3.4 |
| R-7 | 行为 | controller.rebuild() | _value>=0 时 native rebuild→RemakeNode（复用初始路径） | 未绑定静默不派发 | AC-4.1~4.4 |
| R-8 | 行为 | native Clean | pattern->CleanChild | — | AC-4.5 |
| R-9 | 边界 | static style-builder | 须 setNodeContainerOptions+applyAttributeFinish | @since26 staticonly | AC-1.3 |
| R-10 | 行为 | AddBaseNode/CleanChild 脏标记 | 仅 PROPERTY_UPDATE_MEASURE（无 LAYOUT/RENDER） | — | AC-3.6,AC-3.7 |
| R-11 | 边界 | MeasureContent | 返 nullopt（尺寸来自宿主，非子节点） | extends StackLayoutAlgorithm | AC-5.2 |
| R-12 | 行为 | Measure | layoutPolicy 延迟 + RenderNode nullopt + MeasureAdaptiveLayoutChildren；match-parent/fix 启用 | IsEnable*均 true | AC-5.3~5.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 构造/makeNode | UT + SDK 比对 | NodeContainer/NodeController/makeNode、返回 null 移除、@since11/23/26 |
| VM-2 | AC-2.x 桥接 | UT | __makeNode__/nodePtr_ reinterpret_cast、无 C++ NodeController |
| VM-3 | AC-3.x 守卫/AddBaseNode | UT | IsArkTsFrameNode 准入、声明式节点拒绝、PROPERTY_UPDATE_MEASURE |
| VM-4 | AC-4.x rebuild | UT + XTS | rebuild 复用 RemakeNode 路径、未绑定静默 |
| VM-5 | AC-5.x layout | UT | MeasureContent nullopt、layoutPolicy 延迟、match-parent |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `NodeContainer(controller)`（dynamic `@since11`/static `@since23`） | 既有 | 渲染宿主 | — | AC-1.1,AC-1.2 |
| `NodeContainer(style)` + `setNodeContainerOptions`/`applyAttributesFinish`（static `@since26 staticonly`） | 既有 | 静态 style-builder | 须 setNodeContainerOptions+applyAttributesFinish | AC-1.3 |
| `NodeController.makeNode`（abstract `@since11`） | 既有 | 返回 FrameNode | 返回 null 移除子节点 | AC-1.4,AC-1.5 |
| `NodeController.rebuild()`（`@since11`） | 既有 | controller 发起重构 | 复用 RemakeNode 路径 | AC-4.1 |

> SDK：dynamic `node_container.d.ts:36-108`、`NodeController.d.ts:47-142`；static `nodeContainer.static.d.ets:36-91`、`NodeController.static.d.ets:42-184`。

## 接口规格

### 接口定义

**NodeContainer（dynamic，`node_container.d.ts:96`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `declare const NodeContainer: NodeContainerInterface`（`(controller: NodeController): NodeContainerAttribute`） |
| 返回值 | `NodeContainerAttribute`（空 CommonMethod 子类） |
| 开放范围 | Public（`@since11`，`@atomicservice since12`） |
| 错误码 | N/A（非命令式节点仅警告日志，不抛错） |
| 关联 AC | AC-1.1,AC-1.4 |

**NodeController.makeNode / rebuild（`NodeController.d.ts:75,142`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `abstract makeNode(uiContext: UIContext): FrameNode \| null`；`rebuild(): void` |
| 返回值 | makeNode 返回 FrameNode 或 null（null→移除子节点）；rebuild void |
| 开放范围 | Public（`@since11`） |
| 错误码 | N/A |
| 关联 AC | AC-1.4,AC-1.5,AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| controller | NodeController | 是 | — | 须实现 makeNode；makeNode 返回须为命令式 ArkTsFrameNode/RootBuilderNode |
| uiContext（makeNode 入参） | UIContext | 是 | — | 当前 UIContext |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | makeNode 返回声明式节点 | CheckBeforeAddNode 拒绝+警告，不崩 | AC-3.4 |
| 2 | makeNode 返回 null | 子节点移除 | AC-1.5 |
| 3 | controller.rebuild() | 复用 RemakeNode→AddBaseNode | AC-4.4 |
| 4 | rebuild 未绑定（_value<0） | 静默不派发 | AC-4.2 |
| 5 | layoutPolicy 子节点 | 延迟到 MeasureAdaptiveLayoutChildren | AC-5.3,AC-5.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意既有行为：**无 C++ NodeController**（纯 TS，C++ 经 `nodePtr_` reinterpret_cast 跨界）；makeNode 返回节点须为命令式 `IsArkTsFrameNode`/`GetIsRootBuilderNode`，声明式节点被拒。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic `@since11`；static `@since23`。
- **API 版本号策略:** 按 SDK `@since11/23/26` 标注。

> **桥接安全风险（F-bridge）：** NodeContainer 经 `nodePtr_` 原生指针 `reinterpret_cast<NG::UINode*>` 跨 declarative↔imperative 边界（`js_node_container.cpp:271-279`），**无 C++ NodeController 类**、C++ 对 controller 不透明；`IsArkTsFrameNode`/`GetIsRootBuilderNode` 守卫（`node_container_pattern.cpp:27-30`）是边界完整性的关键，下游勿绕过（风险 RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 无 C++ NodeController | 纯 TS，C++ 经 nodePtr_ 跨界 | AC-2.4,AC-2.5 |
| IsArkTsFrameNode 准入 | 仅命令式 ArkTsFrameNode/RootBuilderNode 可挂入 | AC-3.4 |
| rebuild 复用 RemakeNode | 无分叉，与初始渲染同路径 | AC-4.4 |
| MeasureContent nullopt | 尺寸来自宿主 constraint，非子节点 | AC-5.2 |
| 仅 PROPERTY_UPDATE_MEASURE | add/clean 不置 LAYOUT/RENDER | AC-3.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | rebuild 复用 RemakeNode 路径无额外开销 | UT + benchmark | `node_container_modifier.cpp:20-28` |
| 可靠性 | makeNode 返回声明式/null 节点不崩（拒绝/移除） | UT 异常 | `node_container_pattern.cpp:27-30,57` |
| 可测试性 | 暴露 native rebuild/clean modifier 供 controller 测试 | UT | `node_container_modifier.cpp:20-37` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 无差异 | 同上 | XTS | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | base node 子树随 NodeContainer 入无障碍树 | — |
| 大字体 | 否 | base node 自行处理 | — |
| 深色模式 | 否 | base node 自行处理 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | dyn `@since11`、static `@since23`、style-builder `@since26 staticonly` | AC-1.1~1.3 |
| 生态兼容 | 是 | dyn `@since11`、`@atomicservice since12` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: NodeContainer 渲染宿主与 FrameNode 桥接
  作为 应用开发者
  我想要 用 NodeContainer(controller) 嵌入命令式 FrameNode
  以便 声明式 UI 承载自定义节点

  Scenario: makeNode 返回命令式节点
    Given NodeController.makeNode 返回 ArkTsFrameNode
    When FireMakeNode
    Then CheckBeforeAddNode 通过，host->AddChild(newNode,0)

  Scenario: makeNode 返回声明式节点
    Given makeNode 返回声明式 UI 创建的节点（非 IsArkTsFrameNode/RootBuilderNode）
    When CheckBeforeAddNode
    Then 警告 "Cannot return node created by declarative UI function"，节点被拒，不崩

  Scenario: makeNode 返回 null
    Given makeNode 返回 null
    When AddBaseNode(nullptr)
    Then 移除旧 base node，无新子节点

  Scenario: rebuild 复用路径
    Given controller 已绑定（_value>=0）
    When controller.rebuild()
    Then native rebuild→RemakeNode→AddBaseNode（与初始渲染同路径）

  Scenario Outline: layout
    Given NodeContainer 布局
    When <子节点类型>
    Then <度量>

    Examples:
      | 子节点类型 | 度量 |
      | layoutPolicy 子 | 延迟到 MeasureAdaptiveLayoutChildren |
      | RenderNode 子 | Measure(std::nullopt) |
      | 普通子 | Measure(CreateChildConstraint) |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做渲染宿主+桥接+layout；生命周期见 Feat-02、复用+纹理导出见 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContainerPattern RemakeNode AddBaseNode CheckBeforeAddNode IsArkTsFrameNode 守卫"
  - repo: "openharmony/arkui_ace_engine"
    query: "JSNodeContainer SetNodeController nodePtr_ reinterpret_cast NG::UINode 桥接"
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeController rebuild node_container_modifier RemakeNode 复用路径"
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContainerLayoutAlgorithm MeasureContent nullopt layoutPolicy MeasureAdaptiveLayoutChildren"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/node_container.d.ts`、`interface/sdk-js/api/arkui/NodeController.d.ts`、`frameworks/core/components_ng/pattern/node_container/node_container_pattern.cpp`、`frameworks/bridge/declarative_frontend/jsview/js_node_container.cpp`
