# 特性规格

> Func-04-06-02-Feat-01 FrameNode 节点创建、身份与内省：固化 FrameNode 类构造/工厂/身份查询/状态查询/释放/内省/自定义属性共 16 个公开 API 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FrameNode 节点创建、身份与内省 |
| 特性编号 | Func-04-06-02-Feat-01 |
| 所属 Epic | 自定义节点能力 / FrameNode |
| 优先级 | P1 |
| 目标版本 | API 11 (dynamic 起始) — API 26.0.0 (最新扩展) |
| SIG 归属 | ArkUI |
| 状态 | Baselined |
| 复杂度 | L2（16 个公开 API，跨 9 个 API 版本，动态/静态双形式，含错误码） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | constructor / getId / getUniqueId / getNodeType / dispose / disposeTree / getInspectorInfo / getCustomProperty | API 11–12 起始能力，首次补录 |
| ADDED | isModifiable | API 12 |
| ADDED | isDisposed | API 20 |
| ADDED | isTransferred / isOnMainTree | API 23 |
| ADDED | isMinimized | API 26.0.0 staticonly |
| ADDED | createFrameNodes / getFrameNodeById / getFrameNodeByUniqueId | API 26.0.0 |

## 输入文档

| 文档 | 路径 |
|------|------|
| 设计文档 | `04-common-capability/06-custom-node/02-frame-node/design.md` |
| 功能域注册 | `specs/registry/functions.yaml` (id: 04-06-02) |
| 特性注册 | `specs/registry/features.yaml` (func_id: 04-06-02, Feat-01) |
| SDK 动态定义 | `interface/sdk-js/api/arkui/FrameNode.d.ts` |
| SDK 静态定义 | `interface/sdk-js/api/arkui/FrameNode.static.d.ets` |
| 模块入口(动态) | `interface/sdk-js/api/@ohos.arkui.node.d.ts` |
| 模块入口(静态) | `interface/sdk-js/api/@ohos.arkui.node.static.d.ets` |

> 需求基线、不涉及项、受影响子系统与仓库详见 design.md，本文档不重复摘录。

## 用户故事

### US-1: 创建自定义节点实例

**作为** 应用开发者，**我想要** 通过 UIContext 创建一个可承载自定义绘制/度量的 FrameNode 实例，**以便** 以编程方式构建节点树。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 调用 `new FrameNode(uiContext)` 且 uiContext 为有效 UIContext THEN 返回一个 FrameNode 实例，其 `getNodeType()` 返回 `"CustomFrameNode"`，`isModifiable()` 返回 `true` | 正常 |
| AC-1.2 | WHEN `new FrameNode(uiContext)` 的 uiContext 为 undefined 或非 UIContext 对象 THEN 抛出 BusinessError(401, "Node constructor error, param uiContext ...") | 异常 |
| AC-1.3 | WHEN 构造成功 THEN 实例持有强引用 NativeStrongRef(RefPtr\<FrameNode\>)，并在 `FrameNodeFinalizationRegisterProxy.ElementIdToOwningFrameNode_` 中按 `_nodeId` 注册 | 正常 |
| AC-1.4 | WHEN 使用静态形式 `new FrameNode(uiContext, { supportMultiThread: true })`（options @since 26.0.0 staticonly）THEN 节点支持多线程场景操作 | 边界 |

### US-2: 批量创建节点

**作为** 应用开发者，**我想要** 一次性创建指定数量的 FrameNode，**以便** 减少跨语言调用开销。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `FrameNode.createFrameNodes(uiContext, count)` 且 count 为正整数 N THEN 返回长度为 N 的 FrameNode 数组，每个元素 `getNodeType()` 为 `"CustomFrameNode"` | 正常 |
| AC-2.2 | WHEN count <= 0（含 0 与负数）THEN 返回空数组 `[]`，不抛异常 | 边界 |
| AC-2.3 | WHEN count 非整数（如浮点、字符串）THEN 抛出 BusinessError(401, "The parameter count is invalid.") | 异常 |
| AC-2.4 | WHEN 批量创建 THEN 每个节点走与单次构造相同的 C++ 路径（MakeUniqueId + GetOrCreateCustomFrameNode），无池化复用 | 正常 |

### US-3: 在子树中按 ID 查找节点

**作为** 应用开发者，**我想要** 从当前节点出发查找指定 ID 的后代节点，**以便** 定位节点树中的目标。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 `node.getFrameNodeById(id)` 且子树中存在 `propInspectorId_` 等于 id 的 FrameNode THEN 返回首个匹配节点（BFS 含 this 自身） | 正常 |
| AC-3.2 | WHEN 子树中无匹配 THEN 返回 `null` | 正常 |
| AC-3.3 | WHEN id 为空字符串 THEN 返回 `null` | 边界 |
| AC-3.4 | WHEN 调用 `node.getFrameNodeByUniqueId(uniqueId)` 且 uniqueId 为正整数且子树存在 `GetId()==uniqueId` 的节点 THEN 返回该节点 | 正常 |
| AC-3.5 | WHEN uniqueId 为负数、NaN 或 Inf THEN 返回 `null` | 边界 |
| AC-3.6 | WHEN 匹配节点为不可改节点（tag != "CustomFrameNode"）THEN 以 ProxyFrameNode（弱引用）形式返回 | 正常 |

### US-4: 查询节点身份标识

**作为** 应用开发者，**我想要** 获取节点的用户标识、系统唯一 ID 与类型，**以便** 区分与引用节点。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 调用 `getId()` THEN 返回用户通过 `.id()` 设置的 inspector id 字符串（propInspectorId_）；未设置时返回 `""` | 正常 |
| AC-4.2 | WHEN 调用 `getUniqueId()` THEN 返回系统分配的 elementId（MakeUniqueId 单调递增整数）；无效节点返回 `-1` | 正常 |
| AC-4.3 | WHEN 调用 `getNodeType()` THEN 返回节点 tag 字符串：自定义节点为 `"CustomFrameNode"`，内置组件为组件名（如 `"Text"`/`"Button"`），渲染型自定义组件为 `"__Common__"`；无效节点返回 `""` | 正常 |
| AC-4.4 | WHEN 节点未设置 `.id()` THEN `getId()` 与 `getUniqueId()` 返回值类型不同（字符串 `""` vs 整数），二者不可互换 | 边界 |

### US-5: 判定节点可修改性

**作为** 应用开发者，**我想要** 判断节点是否允许执行子树/动画操作，**以便** 避免对不可改节点调用受限 API。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 节点为用户创建的自定义节点（tag=="CustomFrameNode"）且 ArkTS 包装持有强引用 THEN `isModifiable()` 返回 `true` | 正常 |
| AC-5.2 | WHEN 节点为框架构建节点从树中取回（ProxyFrameNode/ImmutableFrameNode）THEN `isModifiable()` 返回 `false` | 正常 |
| AC-5.3 | WHEN `isModifiable()` 返回 `false` THEN 对该节点调用 appendChild/insertChildAfter/removeChild/clearChildren/createAnimation/cancelAnimations 抛出 BusinessError(100021, "The FrameNode is not modifiable.") | 异常 |
| AC-5.4 | WHEN 节点已 dispose THEN `isModifiable()` 返回 `false` | 边界 |

### US-6: 查询节点生命周期状态

**作为** 应用开发者，**我想要** 查询节点是否已释放、是否挂载于主树、是否经过动态静态转换，**以便** 在操作前验证节点有效性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN 节点已调用 dispose() 且 nodePtr 已置空 THEN `isDisposed()` 返回 `true`；否则返回 `false` | 正常 |
| AC-6.2 | WHEN 节点当前挂载于主渲染树（onMainTree_==true）THEN `isOnMainTree()` 返回 `true`；未挂载返回 `false` | 正常 |
| AC-6.3 | WHEN 节点已 dispose 时调用 `isOnMainTree()` THEN 抛出 BusinessError(100026, "The current FrameNode has been disposed.") | 异常 |
| AC-6.4 | WHEN 调用 `isTransferred()` THEN 当前实现恒返回 `false`（桩函数，动态静态转换逻辑位于 ComponentContent/trans_frame_node） | 边界 |
| AC-6.5 | WHEN 静态形式调用 `isMinimized()` THEN 当前实现恒返回 `false`（staticonly，运行时未实现最小化状态机） | 边界 |

### US-7: 释放节点引用

**作为** 应用开发者，**我想要** 释放单个节点或整棵子树的引用，**以便** 回收资源。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-7.1 | WHEN 调用 `dispose()` THEN 幂等：重复调用直接返回；置 `_isDisposed=true`、清空 `_nativeRef`/`nodePtr_`、从 ElementIdToOwningFrameNode_ 移除 | 正常 |
| AC-7.2 | WHEN 调用 `dispose()` THEN 不主动从父节点子列表移除；若父节点持有 C++ RefPtr 则引擎侧节点可能继续存活 | 边界 |
| AC-7.3 | WHEN 调用 `disposeTree()` THEN 先将 this 从父节点脱离（父为 NodeContainer 时调 clean，否则 removeChild），再 DFS 递归 dispose 整棵子树（firstChild + nextSibling 链） | 正常 |
| AC-7.4 | WHEN TypedFrameNode 调用 `dispose()` THEN 额外显式调用 `_nativeRef.dispose()` 主动释放强引用 | 正常 |
| AC-7.5 | WHEN dispose 后调用 getMeasuredSize/getLayoutPosition 等查询 THEN 可能触发 JS 崩溃（SDK NOTE 明示） | 异常 |

### US-8: 内省节点结构信息

**作为** 应用开发者/调试者，**我想要** 获取节点的完整结构信息 JSON，**以便** 与 DevEco Studio Inspector 对齐排查。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-8.1 | WHEN 调用 `getInspectorInfo()` THEN 返回 JSON.parse 后的对象，结构含 type/id/attrs（renderContext/accessibility/layout/paint/pattern/eventHub/geometryNode）及 isLayoutDirtyMarked/isMeasureBoundary 等 | 正常 |
| AC-8.2 | WHEN 节点无效或无 PipelineContext THEN 返回 `{}` | 边界 |
| AC-8.3 | WHEN 高频调用 `getInspectorInfo()` THEN 性能下降（SDK NOTE 明示为调试用途） | 边界 |

### US-9: 获取自定义属性

**作为** 应用开发者，**我想要** 按名称获取节点的自定义属性，**以便** 读取跨语言或装饰器设置的值。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-9.1 | WHEN 调用 `getCustomProperty(name)` 且 name 有效 THEN 先查 ArkTS 侧 `__getCustomProperty__(nodeId, name)`（带 COMMON_VIEW 父节点间接寻址），未命中再 fallback 到 native `GetCapiCustomProperty`（customPropertyMap_） | 正常 |
| AC-9.2 | WHEN name 为 undefined THEN 直接返回 `undefined` | 边界 |
| AC-9.3 | WHEN name 在两层存储均未找到 THEN 返回 `undefined`（动态）或 CustomProperty 默认值（静态） | 边界 |
| AC-9.4 | WHEN native 命中 THEN 值以 char* 返回并拷贝为 JS 字符串，调用后 `FreeCustomPropertyCharPtr` 释放；非字符串对象仅存在于 ArkTS 侧 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1,R-5 | — | 单测 | `frame_node_test_ng.cpp` / `arkts_native_frame_node_bridge.cpp:292` |
| AC-1.2 | R-12 | — | 单测 | `frame_node.ts:116-122` |
| AC-2.1 | R-2 | — | 单测 | `arkts_native_frame_node_bridge.cpp:703` |
| AC-2.2 | R-13 | — | 单测 | `frame_node.ts:283` |
| AC-2.3 | R-12 | — | 单测 | `frame_node.ts:283` |
| AC-3.1 | R-3 | — | 单测 | `ui_node.cpp:2027` |
| AC-3.2 | R-14 | — | 单测 | `ui_node.cpp:2027` |
| AC-3.3 | R-14 | — | 单测 | `ui_node.cpp:2027` |
| AC-3.4 | R-4 | — | 单测 | `ui_node.cpp:2039` |
| AC-3.5 | R-15 | — | 单测 | `ui_node.cpp:2041` |
| AC-3.6 | R-16 | — | 单测 | `frame_node.ts:372` |
| AC-4.1 | R-5 | — | 单测 | `frame_node_modifier.cpp:563` |
| AC-4.2 | R-6 | — | 单测 | `frame_node_modifier.cpp:434` |
| AC-4.3 | R-7 | — | 单测 | `frame_node_modifier.cpp:577` |
| AC-4.4 | R-6,R-5 | — | 单测 | 同上 |
| AC-5.1 | R-8 | — | 单测 | `frame_node_modifier.cpp:66` |
| AC-5.2 | R-9 | — | 单测 | `frame_node.ts:353` |
| AC-5.3 | R-17 | — | 单测 | `frame_node.ts:350` |
| AC-5.4 | R-9 | — | 单测 | 同 AC-5.2 |
| AC-6.1 | R-10 | — | 单测 | `frame_node.ts:257` |
| AC-6.2 | R-11 | — | 单测 | `ui_node.h:1361` |
| AC-6.3 | R-18 | — | 单测 | `frame_node.ts:753` |
| AC-6.4 | R-19 | — | 单测 | `frame_node.ts:1053` |
| AC-6.5 | R-20 | — | 单测 | `FrameNode.ets:325` |
| AC-7.1 | R-21 | — | 单测 | `frame_node.ts:241` |
| AC-7.2 | R-22 | — | 单测 | `frame_node.ts:241` |
| AC-7.3 | R-23 | — | 单测 | `frame_node.ts:273` |
| AC-7.4 | R-24 | — | 单测 | `frame_node.ts:1292` |
| AC-7.5 | R-25 | — | 单测 | `FrameNode.d.ts:751` NOTE |
| AC-8.1 | R-26 | — | 单测 | `inspector.cpp:834`,`frame_node.cpp:1737` |
| AC-8.2 | R-27 | — | 单测 | `frame_node_modifier.cpp:611` |
| AC-8.3 | R-28 | — | 单测 | `FrameNode.d.ts:978` NOTE |
| AC-9.1 | R-29 | — | 单测 | `frame_node.ts:770`,`frame_node.cpp:8403` |
| AC-9.2 | R-30 | — | 单测 | `frame_node.ts:770` |
| AC-9.3 | R-31 | — | 单测 | `frame_node_modifier.cpp:898` |
| AC-9.4 | R-32 | — | 单测 | `arkts_native_frame_node_bridge.cpp:2240` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `new FrameNode(validUiContext)` | 返回实例，`getNodeType()=="CustomFrameNode"`、`getUniqueId()>0`、`isModifiable()==true`；实例持有对底层节点的强引用 | uiContext 须为有效 UIContext | AC-1.1 |
| R-2 | 行为 | `createFrameNodes(uiContext, N)`，N 为正整数 | 返回 N 元素 FrameNode 数组，每元素可观测特征同 R-1 | N<=0 返回 []; 非整数抛 401 | AC-2.1,AC-2.4 |
| R-3 | 行为 | `node.getFrameNodeById(id)`，id 非空字符串 | 返回子树（含 this）中首个 id 匹配的 FrameNode | 查找范围为子树非全局；无匹配返 null | AC-3.1 |
| R-4 | 行为 | `node.getFrameNodeByUniqueId(uid)`，uid 为正整数 | 返回子树中首个 uniqueId 匹配的 FrameNode | uid<0/NaN/Inf 返回 null | AC-3.4 |
| R-5 | 行为 | `getId()` | 返回用户 `.id()` 设置的 id 字符串；未设置返回 `""` | 返回字符串非 tag；tag 用 getNodeType() | AC-4.1,AC-4.4 |
| R-6 | 行为 | `getUniqueId()` | 返回系统分配的唯一整数 ID，稳定于节点生命周期；无效节点返回 -1 | 返回数值非字符串 | AC-4.2,AC-4.4 |
| R-7 | 行为 | `getNodeType()` | 返回节点类型字符串：自定义节点 `"CustomFrameNode"`、内置组件名、渲染型自定义 `"__Common__"`；无效返回 `""` | 与 getId 返回不同的身份维度 | AC-4.3 |
| R-8 | 行为 | `isModifiable()`，用户创建的自定义节点 | 返回 `true` | ArkTS 判据：持有强引用；native 判据：tag=="CustomFrameNode" | AC-5.1 |
| R-9 | 行为 | `isModifiable()`，框架树取回节点/已 dispose | 返回 `false` | 不可改节点受限 API 抛 100021 | AC-5.2,AC-5.4 |
| R-10 | 行为 | `isDisposed()` | 返回是否已释放（dispose 后且底层引用已清空时为 true） | ArkTS 层状态 | AC-6.1 |
| R-11 | 行为 | `isOnMainTree()`，节点未 dispose | 返回是否挂载于主节点树 | 默认 false | AC-6.2 |
| R-12 | 异常 | 构造/createFrameNodes 参数无效（uiContext 非 UIContext / count 非整数） | 抛 BusinessError(401) | 401 为参数校验 | AC-1.2,AC-2.3 |
| R-13 | 边界 | `createFrameNodes` count<=0（0 或负数） | 返回空数组 `[]`，不抛异常 | 与非整数(401)区分 | AC-2.2 |
| R-14 | 边界 | `getFrameNodeById` 子树无匹配 或 id 为空串 | 返回 null | 空串 → null | AC-3.2,AC-3.3 |
| R-15 | 边界 | `getFrameNodeByUniqueId` uid 为负数/NaN/Inf | 返回 null | — | AC-3.5 |
| R-16 | 行为 | 查找命中的节点非用户自定义 | 以 ProxyFrameNode（弱引用）包装返回 | 全局 int-id 查找仅 C-API 层 | AC-3.6 |
| R-17 | 异常 | 不可改节点调用 appendChild/insertChildAfter/removeChild/clearChildren/createAnimation/cancelAnimations | 抛 BusinessError(100021, "The FrameNode is not modifiable.") | checkType() 守卫 | AC-5.3 |
| R-18 | 异常 | 已 dispose 节点调用 isOnMainTree() | 抛 BusinessError(100026, "The current FrameNode has been disposed.") | 100026 仅 ArkTS 层守卫抛出 | AC-6.3 |
| R-19 | 边界 | `isTransferred()` | 当前实现恒返回 false（桩函数） | API23 声明但未实现——风险项 | AC-6.4 |
| R-20 | 边界 | `isMinimized()`（staticonly） | 当前实现恒返回 false（桩函数），运行时无此方法 | API26 staticonly 声明但未实现——风险项 | AC-6.5 |
| R-21 | 行为 | `dispose()` | 幂等；置 isDisposed()=true、释放对底层节点的强引用（此后 getUniqueId() 返回 -1）；不脱离父节点 | 底层节点引用计数回收 | AC-7.1 |
| R-22 | 边界 | `dispose()` 对已挂载节点 | 不从父节点子列表移除 | 与 disposeTree 行为不同 | AC-7.2 |
| R-23 | 行为 | `disposeTree()` | 先脱离父节点，再递归释放整棵子树后释放自身 | 空节点直接返回 | AC-7.3 |
| R-24 | 行为 | TypedFrameNode.dispose() | 额外主动释放底层强引用 | 比基类 dispose 更主动 | AC-7.4 |
| R-25 | 异常 | dispose 后调用 getMeasuredSize/getLayoutPosition 等查询 | 可能触发 JS 崩溃（SDK NOTE 明示） | 用 getUniqueId()>0 判实体对应 | AC-7.5 |
| R-26 | 行为 | `getInspectorInfo()` | 返回 JSON 对象：节点结构信息（type/id/attrs/状态标志），与 DevEco Studio Inspector 对齐 | 无效节点返回 "{}" | AC-8.1 |
| R-27 | 边界 | `getInspectorInfo()` 节点无效或无上下文 | 返回 "{}" | 防御性默认 | AC-8.2 |
| R-28 | 边界 | 高频调用 `getInspectorInfo()` | 性能下降 | SDK NOTE：调试用途 | AC-8.3 |
| R-29 | 行为 | `getCustomProperty(name)`，name 有效 | 先查 ArkTS 层自定义属性（带 COMMON_VIEW 父节点间接寻址），未命中 fallback 到 native 层 | 两层存储 | AC-9.1 |
| R-30 | 边界 | `getCustomProperty(undefined)` | 直接返回 undefined | name 未传 | AC-9.2 |
| R-31 | 边界 | `getCustomProperty(name)` 两层均未命中 | 返回 undefined（动态）/ CustomProperty 默认（静态） | — | AC-9.3 |
| R-32 | 行为 | native 层命中 | 返回字符串值 | C-API 值恒为字符串 | AC-9.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1,R-2 构造/批量构造 | 单测 frame_node_test_ng | tag=="CustomFrameNode"、nodeId 单调递增、强引用非空 |
| VM-2 | R-3,R-4 子树查找 | 单测 ui_node_test | BFS 含 this、空串/负数返回 null、Proxy 包装 |
| VM-3 | R-5,R-6,R-7 身份三元组 | 单测 frame_node_test_ng | getId 默认""、getUniqueId>-1、getNodeType=tag |
| VM-4 | R-8,R-9,R-17 可改性 | 单测 frame_node_test_ng | 自定义 true、Proxy false、100021 守卫 |
| VM-5 | R-10,R-11,R-18,R-19,R-20 状态 | 单测 frame_node_test_ng | isDisposed 双条件、100026、stub 恒 false |
| VM-6 | R-21..R-25 释放 | 单测 frame_node_test_ng | 幂等、不脱离父、disposeTree 递归、TypedFrameNode 显式释放 |
| VM-7 | R-26,R-27,R-28 内省 | 单测 frame_node_test_ng_dump | JSON 结构、{} 默认、性能 NOTE |
| VM-8 | R-29..R-32 自定义属性 | 单测 frame_node_test_ng | 两层查找、undefined、char* 拷贝释放 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| constructor(uiContext) | Public | uiContext: UIContext | FrameNode 实例 | 401 | 创建自定义 FrameNode | AC-1.1,1.2 |
| constructor(uiContext, options?) [static] | Public | uiContext; options?: FrameNodeOptions(@since 26.0.0 staticonly) | FrameNode | 401 | 静态构造，支持多线程选项 | AC-1.1,1.4 |
| createFrameNodes(uiContext, count) [static] | Public | uiContext; count: number(dyn)/int(static) | FrameNode[] | 401 | 批量创建 | AC-2.1..2.4 |
| getFrameNodeById(id) | Public | id: string | FrameNode\|null | — | 子树按 inspector id 查找 | AC-3.1..3.3 |
| getFrameNodeByUniqueId(id) | Public | id: int | FrameNode\|null | — | 子树按 uniqueId 查找 | AC-3.4..3.6 |
| getId() | Public | — | string | — | 用户 inspector id | AC-4.1,4.4 |
| getUniqueId() | Public | — | number(dyn)/int(static) | — | 系统 elementId | AC-4.2,4.4 |
| getNodeType() | Public | — | string | — | 节点 tag | AC-4.3 |
| isModifiable() | Public | — | boolean | — | 可改性判定 | AC-5.1..5.4 |
| isDisposed() | Public | — | boolean | — | 释放状态 | AC-6.1 |
| isTransferred() | Public | — | boolean | — | 动静转换标记(桩) | AC-6.4 |
| isOnMainTree() | Public | — | boolean | 100026 | 主树挂载状态 | AC-6.2,6.3 |
| isMinimized() [staticonly] | Public | — | boolean | — | 最小化标记(桩) | AC-6.5 |
| dispose() | Public | — | void | — | 释放单节点引用 | AC-7.1,7.2,7.5 |
| disposeTree() | Public | — | void | — | 释放整子树 | AC-7.3 |
| getInspectorInfo() | Public | — | Object | — | 结构信息 JSON | AC-8.1..8.3 |
| getCustomProperty(name) | Public | name: string | Object\|undefined(dyn)/CustomProperty(static) | — | 自定义属性 | AC-9.1..9.4 |

### 变更/废弃 API

无变更或废弃。本特性为存量补录，API 自 API 11 起增量新增（见兼容性声明版本演进），无破坏性变更。

## 接口规格

### 接口定义

**constructor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FrameNode::constructor(uiContext: UIContext)` (dyn @since 11); `constructor(uiContext: UIContext, options?: FrameNodeOptions)` (static @since 23) |
| 返回值 | FrameNode 实例 |
| 开放范围 | Public |
| 错误码 | 401 (uiContext 无效) |
| 关联 AC | AC-1.1, AC-1.2, AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | UIContext | 是 | — | 须为有效 UIContext（含 instanceId_），否则 401 |
| options | FrameNodeOptions | 否 | undefined | 仅静态形式；supportMultiThread?: boolean @since 26.0.0 staticonly |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | uiContext 有效 | MakeUniqueId + GetOrCreateCustomFrameNode，tag="CustomFrameNode"，注册 ElementIdToOwningFrameNode_ | AC-1.1 |
| 2 | uiContext undefined/非 UIContext | 抛 401 | AC-1.2 |
| 3 | 静态 options.supportMultiThread=true | 节点支持多线程操作 | AC-1.4 |

**createFrameNodes (static)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static FrameNode::createFrameNodes(uiContext: UIContext, count: number\|int): FrameNode[]` (@since 26.0.0) |
| 返回值 | FrameNode[] |
| 开放范围 | Public |
| 错误码 | 401 (count 非整数) |
| 关联 AC | AC-2.1..2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | UIContext | 是 | — | 须有效，否则 401 |
| count | number(dyn)/int(static) | 是 | — | 正整数；<=0 返回[]；非整数抛 401 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | count 为正整数 N | 返回 N 元素数组，每元素 tag="CustomFrameNode" | AC-2.1,2.4 |
| 2 | count<=0 | 返回 [] | AC-2.2 |
| 3 | count 非整数 | 抛 401 | AC-2.3 |

**getFrameNodeById / getFrameNodeByUniqueId**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getFrameNodeById(id: string): FrameNode\|null` / `getFrameNodeByUniqueId(id: int): FrameNode\|null` (@since 26.0.0) |
| 返回值 | FrameNode\|null |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-3.1..3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| id (byId) | string | 是 | — | 空串返回 null；匹配 propInspectorId_ |
| id (byUniqueId) | int | 是 | — | 负数/NaN/Inf 返回 null；匹配 GetId() |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | id 非空且子树有匹配 | 返回首个匹配（BFS 含 this） | AC-3.1,3.4 |
| 2 | 无匹配 / 空串 / 负数 | 返回 null | AC-3.2,3.3,3.5 |
| 3 | 命中节点不可改 | ProxyFrameNode 弱引用包装 | AC-3.6 |

**getId / getUniqueId / getNodeType**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getId(): string` / `getUniqueId(): number\|int` / `getNodeType(): string` (dyn @since 11-12; static @since 23) |
| 返回值 | string / number\|int / string |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-4.1..4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | — | — | — | 无参；无效节点 getId/getNodeType 返回""，getUniqueId 返回 -1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常节点 | getId=inspectorId(""/用户值)、getUniqueId=elementId(>-1)、getNodeType=tag | AC-4.1,4.2,4.3 |
| 2 | 未设 .id() | getId=""，getUniqueId 仍为有效整数 | AC-4.4 |

**isModifiable**

| 属性 | 值 |
|------|-----|
| 函数签名 | `isModifiable(): boolean` (dyn @since 12; static @since 23) |
| 返回值 | boolean |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-5.1..5.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | — | — | — | native 判据 GetTag()=="CustomFrameNode"；ArkTS 判据 _nativeRef 非空 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | CustomFrameNode 且强引用 | true | AC-5.1 |
| 2 | Proxy/Immutable/disposed | false | AC-5.2,5.4 |
| 3 | false 时调受限 API | 抛 100021 | AC-5.3 |

**isDisposed / isTransferred / isOnMainTree / isMinimized**

| 属性 | 值 |
|------|-----|
| 函数签名 | `isDisposed(): boolean`(@since 20 dyn/23 static); `isTransferred(): boolean`(@since 23); `isOnMainTree(): boolean`(@since 23); `isMinimized(): boolean`(@since 26.0.0 staticonly) |
| 返回值 | boolean |
| 开放范围 | Public |
| 错误码 | isOnMainTree: 100026 (disposed) |
| 关联 AC | AC-6.1..6.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | — | — | — | isOnMainTree 须节点未 dispose；isTransferred/isMinimized 当前恒 false |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | dispose 后 nodePtr 空 | isDisposed=true | AC-6.1 |
| 2 | 挂载主树 | isOnMainTree=true | AC-6.2 |
| 3 | disposed 调 isOnMainTree | 抛 100026 | AC-6.3 |
| 4 | 任意状态调 isTransferred/isMinimized | 恒 false（桩） | AC-6.4,6.5 |

**dispose / disposeTree**

| 属性 | 值 |
|------|-----|
| 函数签名 | `dispose(): void`(@since 12); `disposeTree(): void`(@since 12) |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-7.1..7.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | — | — | — | dispose 幂等；disposeTree 先脱离父节点；dispose 后查询可能崩溃 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | dispose 首次 | _isDisposed=true、清引用、移除注册 | AC-7.1 |
| 2 | dispose 已挂载节点 | 不脱离父；引擎侧可能存活 | AC-7.2 |
| 3 | disposeTree | 脱离父 + DFS 递归 dispose 子树 | AC-7.3 |
| 4 | TypedFrameNode.dispose | 额外显式释放强引用 | AC-7.4 |
| 5 | dispose 后查 getMeasuredSize 等 | 可能 JS 崩溃 | AC-7.5 |

**getInspectorInfo**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getInspectorInfo(): Object` (dyn @since 12; static @since 23) |
| 返回值 | Object (JSON.parse 结果) |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-8.1..8.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | — | — | — | 无效节点/无 PipelineContext 返回 {}；高频调用性能下降 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常节点 | 返回 JSON 对象含 type/id/attrs/标志位 | AC-8.1 |
| 2 | 无效/无 context | 返回 {} | AC-8.2 |
| 3 | 高频调用 | 性能下降（调试用途） | AC-8.3 |

**getCustomProperty**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getCustomProperty(name: string): Object\|undefined` (dyn @since 12); `getCustomProperty(name: string): CustomProperty` (static @since 23) |
| 返回值 | Object\|undefined / CustomProperty |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-9.1..9.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| name | string | 是 | — | undefined 直接返回 undefined；未命中两层返回 undefined |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | name 有效且命中 | ArkTS 层优先，fallback native；char* 拷贝为字符串后释放 | AC-9.1,9.4 |
| 2 | name undefined | 返回 undefined | AC-9.2 |
| 3 | 两层未命中 | 返回 undefined/CustomProperty 默认 | AC-9.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。本特性为存量补录，各 API 自其 @since 版本起行为一致，无破坏性变更。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 11（dynamic constructor/getRenderNode 起）；静态形式最低 API 23。
- **API 版本号策略:** 逐 API 标注 @since；动态起始于 11/12/20/23/26.0.0，静态统一 @since 23（createFrameNodes/getFrameNodeById/getFrameNodeByUniqueId 为 26.0.0 static，isMinimized 为 26.0.0 staticonly）。options 参数本身 @since 26.0.0 staticonly。

**版本演进明细:**

| API | dynamic @since | static @since | 备注 |
|-----|---------------|---------------|------|
| constructor | 11 | 23 | 静态多 options 参数(@since 26.0.0 staticonly) |
| getId/getUniqueId/getNodeType/dispose/disposeTree/getInspectorInfo/getCustomProperty | 12 | 23 | — |
| isModifiable | 12 | 23 | — |
| isDisposed | 20 | 23 | — |
| isTransferred/isOnMainTree | 23 | 23 | isOnMainTree 抛 100026 |
| createFrameNodes/getFrameNodeById/getFrameNodeByUniqueId | 26.0.0 | 26.0.0 | — |
| isMinimized | —(无动态) | 26.0.0 staticonly | 桩实现 |

**风险项（实现 IS 规格，当前行为固化）:**

| 风险 | 说明 | 来源 |
|------|------|------|
| isTransferred() 恒 false | API23 声明动静转换标记，但 FrameNode 上为桩函数返回 false；真实转换逻辑在 ComponentContent/trans_frame_node | `frame_node.ts:1053` |
| isMinimized() 恒 false 且无动态形式 | API26 staticonly 声明，运行时 frame_node.ts 缺失该方法，仅 Koala FrameNode.ets 存根 return false；无 C++ 最小化状态机 | `FrameNode.ets:325` |
| 100026 仅 ArkTS 层抛出 | C++ 对 disposed 节点返回安全默认值(false/""/-1)，错误码归属为前端守卫非引擎抛出 | `frame_node.ts:753`,`error_code.h:159` |
| dispose 不脱离父节点 | 单 dispose 仅释放 JS 引用，引擎侧节点可能因父 RefPtr 存活；与用户直觉（dispose 即移除）可能不符 | `frame_node.ts:241` |
| getId≠tag 易混淆 | getId 返回 inspector id 字符串(默认"")，非节点类型；tag 需 getNodeType() | `frame_node_modifier.cpp:563,577` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 节点身份三元组 | getId(inspectorId 字符串) / getUniqueId(elementId 整数) / getNodeType(tag 字符串) 语义不可互换 | AC-4.1..4.4 |
| 可改性双判据 | native 层 tag=="CustomFrameNode"；ArkTS 层 _nativeRef 非空；二者同时为真才可改 | AC-5.1..5.4 |
| 子树查找非全局 | getFrameNodeById/ByUniqueId 为实例方法，BFS 范围为调用节点子树（含 this）；全局 int-id 查找仅 C-API 层 | AC-3.1..3.6 |
| dispose 幂等且不脱离父 | dispose() 幂等、不调原生 destroy、不脱离父；disposeTree() 才脱离+递归 | AC-7.1..7.5 |
| 自定义属性两层存储 | ArkTS __getCustomProperty__(带 COMMON_VIEW 间接寻址) 优先，native customPropertyMap_ fallback；C-API 值恒字符串 | AC-9.1..9.4 |
| 100026 前端守卫 | 错误码仅在 ArkTS 层 isDisposed 守卫抛出，C++ 防御性返回默认 | AC-6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | getInspectorInfo() 高频调用性能下降，SDK 标注为调试用途 | 单测/性能测试 | `FrameNode.d.ts:978` NOTE |
| 内存 | dispose 后引用释放，C++ 节点由 RefPtr 引用计数回收 | 单测 | `frame_node.cpp:786` 析构 |
| 可靠性 | dispose 幂等，重复调用不崩溃 | 单测 | `frame_node.ts:241` |
| 可测试性 | 各 API 在 frame_node_test_ng* 系列单测可覆盖 | 单测 | `test/unittest/core/base/frame_node_test_ng*.cpp` |
| 自动化维测 | getInspectorInfo 输出与 DevEco Studio Inspector 对齐 | 单测 | `inspector.cpp:834` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

> FrameNode 节点创建/身份/内省能力为设备无关的引擎层行为，跨设备一致。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 创建/身份 API 不直接影响无障碍；无障碍由独立 Feat 覆盖 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | uiContext 已隔离多实例，但本 Feat 不引入额外差异 | — |
| 多用户 | 否 | 不涉及 | — |
| 版本升级 | 是 | API 版本演进见兼容性声明；isTransferred/isMinimized 桩为版本风险 | AC-6.4,6.5 |
| 生态兼容 | 是 | 动态/静态双形式签名差异（number vs int、Object vs CustomProperty）需下游适配 | 接口规格 |

## 行为场景

```gherkin
Feature: FrameNode 节点创建、身份与内省
  作为 应用开发者
  我想要 以编程方式创建 FrameNode 并查询其身份与状态
  以便 构建与排查自定义节点树

  Scenario: 创建自定义节点
    Given 一个有效的 UIContext
    When 调用 new FrameNode(uiContext)
    Then 返回的实例 getNodeType() == "CustomFrameNode"
    And isModifiable() == true
    And getUniqueId() > 0

  Scenario: 无效 uiContext 构造
    Given uiContext 为 undefined
    When 调用 new FrameNode(uiContext)
    Then 抛出 BusinessError(401)

  Scenario Outline: 批量创建边界
    Given 有效的 UIContext
    When 调用 createFrameNodes(uiContext, <count>)
    Then <期望>

    Examples:
      | count | 期望 |
      | 5 | 返回 5 元素数组 |
      | 0 | 返回 [] |
      | -3 | 返回 [] |
      | 2.5 | 抛 401 |

  Scenario: 子树按 id 查找未命中
    Given 节点 A 的子树无 id=="foo" 的后代
    When 调用 A.getFrameNodeById("foo")
    Then 返回 null

  Scenario: isOnMainTree 在已 dispose 节点上
    Given 节点 N 已 dispose 且 nodePtr 为空
    When 调用 N.isOnMainTree()
    Then 抛出 BusinessError(100026, "The current FrameNode has been disposed.")

  Scenario: dispose 幂等且不脱离父
    Given 节点 N 已挂载于父 P
    When 调用 N.dispose()
    Then _isDisposed == true 且 nodePtr == null
    And P 的子列表仍可能包含 N（引擎侧 RefPtr 存活）

  Scenario: disposeTree 递归释放子树
    Given 节点 N 有子树 (child1 -> grandchild)
    When 调用 N.disposeTree()
    Then N 先脱离父节点
    And DFS 递归 dispose child1、grandchild 后 dispose N 自身

  Scenario: 自定义属性两层查找
    Given 节点 N 的 COMMON_VIEW 父 id 为 parentId
    When 调用 N.getCustomProperty("myKey")
    Then 先查 __getCustomProperty__(parentId, "myKey")
    And 未命中时 fallback native GetCapiCustomProperty("myKey")
    And 均未命中时返回 undefined
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（覆盖 16 个 API 的创建/身份/内省；不含树管理 Feat-02、布局 Feat-03 等）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode 构造链：arkts_native_frame_node_bridge.cpp CreateFrameNode → ElementRegister::MakeUniqueId → CustomFrameNode::GetOrCreateCustomFrameNode 的 nodeId 分配与 tag 设置"
  - repo: "openharmony/arkui_ace_engine"
    query: "UINode::GetFrameNodeByIdInSubTree / GetFrameNodeByUniqueIdInSubTree 的 BFS 实现与 propInspectorId_ 匹配"
  - repo: "openharmony/arkui_ace_engine"
    query: "frame_node_modifier.cpp GetInspectorId/GetIdByNodePtr/GetNodeType 三种身份的 native 读取路径"
  - repo: "openharmony/arkui_ace_engine"
    query: "frame_node.ts isTransferred/isMinimized 桩函数与 ComponentContent/trans_frame_node 真实转换逻辑的关系"
  - repo: "openharmony/arkui_ace_engine"
    query: "frame_node.cpp customPropertyMap_ 与 getCustomProperty_ 的两层存储与 COMMON_VIEW 父节点间接寻址"
```

**关键文档:** `interface/sdk-js/api/arkui/FrameNode.d.ts`、`interface/sdk-js/api/arkui/FrameNode.static.d.ets`、`frameworks/core/components_ng/base/frame_node.h`、`frameworks/bridge/declarative_frontend/ark_node/src/frame_node.ts`
