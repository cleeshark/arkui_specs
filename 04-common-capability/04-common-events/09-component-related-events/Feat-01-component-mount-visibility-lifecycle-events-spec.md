# 特性规格

> Func-04-04-09-Feat-01 组件挂载与显隐生命周期事件：固化 `onAppear`、`onDisAppear`、`onAttach`、`onDetach` 在 ArkTS Dynamic、ArkTS Static 与 Native Node 通道中的既有行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组件挂载与显隐生命周期事件 |
| 特性编号 | Func-04-04-09-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | ArkTS API 7/12 起，Static API 23，Native API 12/21 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ArkTS 生命周期事件规格 | 补录 Dynamic/Static 的注册、覆盖、清理、触发条件与版本差异 |
| ADDED | Native Node 生命周期事件规格 | 补录 API 12 泛型事件入口与 API 21 CommonEvent 入口 |
| ADDED | 主树迁移时序规格 | 补录同步/异步回调顺序、幂等、重挂载与转场边界 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/09-component-related-events/design.md` | 本次生成 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:22222-22324` | 已核查，来源 checkout 与 ace_engine 版本不完全匹配 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets:12795-12834` | 已核查 |
| 核心实现 | `frameworks/core/components_ng/base/frame_node.cpp:1874-1900,2162-2183` | 已核查 |
| 事件存储与触发 | `frameworks/core/components_ng/event/event_hub.cpp:608-645,673-728,795-817` | 已核查 |
| Native API | `interfaces/native/native_node.h:10214-10384,13080-13107,14317-14346` | 已核查 |

> 本文档描述存量实现，不提出行为修正。源码与 SDK 声明不一致处按兼容性风险记录。

## 用户故事

### US-1: 注册和清理生命周期回调

**作为** ArkUI 应用开发者，

**我想要** 为组件注册或清理挂载与显隐生命周期回调，

**以便** 在组件进入或离开主树时执行与生命周期相关的业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN ArkTS 为 `onAppear`、`onDisAppear`、`onAttach` 或 `onDetach` 传入函数 THEN 当前组件对应事件槽保存该函数 | 正常 |
| AC-1.2 | WHEN 对同一组件的同一生命周期事件重复注册函数 THEN 后注册函数覆盖先注册函数，单次触发只调用当前事件槽中的函数 | 边界 |
| AC-1.3 | WHEN Dynamic ArkTS 在目标 API >= 11 时向任一生命周期事件传入 `undefined` THEN 清除该事件已有回调 | 正常 |
| AC-1.4 | WHEN Dynamic ArkTS 在目标 API < 11 时传入 `undefined`，或在任意版本传入 `null`/非函数值 THEN 本次调用被忽略且已有回调保持不变 | 边界 |
| AC-1.5 | WHEN Static ArkTS 向任一生命周期事件传入 `undefined` THEN 清除该事件已有回调 | 正常 |

### US-2: 感知组件进入和离开主树

**作为** ArkUI 应用开发者，

**我想要** 获得可预测的主树挂载和卸载通知，

**以便** 正确安排资源初始化、暂停和释放操作。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN FrameNode 从非主树状态进入主树 THEN 同步调用 `onAttach`，随后将 `onAppear` 投递到 UI 任务队列异步执行 | 正常 |
| AC-2.2 | WHEN FrameNode 从主树状态离开主树 THEN 同步按 `onDetach`、`onDisAppear` 的顺序调用已注册回调 | 正常 |
| AC-2.3 | WHEN 组件仅发生 `visibility` 或 active 状态变化而未发生主树迁移 THEN 不触发本特性的四个生命周期事件 | 边界 |
| AC-2.4 | WHEN 已在主树的节点再次执行 Attach，或已离树的节点再次执行 Detach THEN 状态守卫直接返回且不重复触发生命周期回调 | 边界 |
| AC-2.5 | WHEN 节点离树后再次进入主树且回调未被显式清理 THEN 原回调仍保留并再次触发 | 正常 |
| AC-2.6 | WHEN 节点带消失转场从父节点移除 THEN 在逻辑离树开始时触发 `onDetach` 和 `onDisAppear`，不等待消失动画结束 | 边界 |
| AC-2.7 | WHEN `onAppear` 已投递但尚未执行时节点快速离树 THEN `onDetach`/`onDisAppear` 可先被观察到，待执行的 `onAppear` 任务不因离树而显式取消 | 边界 |

### US-3: 通过 Native Node 订阅生命周期事件

**作为** Native UI 开发者，

**我想要** 通过 Native Node API 订阅同一组生命周期事件，

**以便** 在 C API 场景获得与 ArkTS 主树生命周期一致的通知。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 在主线程通过 NativeNodeAPI_1 `registerNodeEvent` 注册 `NODE_EVENT_ON_APPEAR`、`NODE_EVENT_ON_DISAPPEAR`、`NODE_EVENT_ON_ATTACH` 或 `NODE_EVENT_ON_DETACH` THEN API 12 泛型事件链路订阅对应 EventHub 事件 | 正常 |
| AC-3.2 | WHEN 四个 Native 生命周期事件被派发 THEN `ArkUI_NodeComponentEvent` 不携带业务参数，同时事件对象保留注册时的 `targetId` 和 `userData` | 正常 |
| AC-3.3 | WHEN 通过 API 12 泛型入口对同一节点和 eventType 重复注册 THEN 更新该 eventType 的 `targetId`/`userData`，并继续使用单个底层事件槽 | 边界 |
| AC-3.4 | WHEN 调用 `unregisterNodeEvent` 注销已注册生命周期事件 THEN 删除事件映射并重置对应底层事件槽，后续主树迁移不再派发该订阅 | 正常 |
| AC-3.5 | WHEN API 21 `OH_ArkUI_NativeModule_RegisterCommonEvent` 注册 appear/disappear THEN 注册成功；WHEN 传入 attach/detach THEN 返回 `ARKUI_ERROR_CODE_NODE_UNSUPPORTED_EVENT_TYPE` | 异常 |
| AC-3.6 | WHEN API 21 CommonEvent 对同一节点和 eventType 重复注册或注销后重注册 THEN 当前实现的 callback map 使用 `insert` 保留首次 callback，而 `userData` 更新；该行为作为实现风险记录 | 边界 |

### US-4: 识别 API 与旧管线兼容边界

**作为** 跨版本应用和框架维护者，

**我想要** 明确不同 API 版本和旧管线的支持范围，

**以便** 避免把新管线行为错误地外推到不支持的运行环境。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 使用 Dynamic ArkTS API THEN `onAppear`/`onDisAppear` 自 API 7 开放，`onAttach`/`onDetach` 自 API 12 开放 | 正常 |
| AC-4.2 | WHEN 使用 Static ArkTS API 23 THEN 四个接口均接收回调或 `undefined` | 正常 |
| AC-4.3 | WHEN 运行旧 Pipeline THEN `onAppear`/`onDisAppear` 使用旧 Component EventMarker 链路，而 `onAttach`/`onDetach` 和四项 Disable 接口为空实现 | 边界 |
| AC-4.4 | WHEN 使用 Native API THEN NativeNodeAPI_1 四事件枚举与泛型注册自 API 12 开放，CommonEvent 便捷入口自 API 21 开放且仅覆盖 appear/disappear | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-4 | 已有实现 | Host 单测/源码审查 | `event_hub_test_ng.cpp:515-600,2080-2098`; `view_abstract_test_six_ng.cpp:202-262` |
| AC-2.1~AC-2.7 | R-5~R-11 | 已有实现 | Host 单测/源码审查 | `event_hub_test_ng.cpp:2062-2077`; `frame_node.cpp:1874-1900,2162-2183`; `ui_node.cpp:373-412,1020-1119` |
| AC-3.1~AC-3.6 | R-12~R-16 | 已有实现 | C API 单测/源码审查 | `native_node_test.cpp:2759-2787,3054-3081,10165-10199`; `node_model.cpp:535-647,1779-1825` |
| AC-4.1~AC-4.4 | R-17~R-20 | 已有实现 | SDK/源码审查 | `common.d.ts:22222-22324`; `common.static.d.ets:12795-12834`; `view_abstract_model_impl.h:231-234,304-307` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ArkTS 传入有效函数 | 对应 EventHub 事件槽保存该回调 | 每个事件一个 `std::function` 槽 | AC-1.1 |
| R-2 | 边界 | 同一事件再次注册有效函数 | 后注册回调覆盖旧回调 | 不形成回调列表 | AC-1.2 |
| R-3 | 行为 | Dynamic ArkTS 传入 `undefined` 且目标 API >= 11 | 调用对应 Disable 接口清除回调 | API 11 为清理门槛 | AC-1.3 |
| R-4 | 边界 | Dynamic ArkTS 在 API < 11 传入 `undefined`，或传入 `null`/非函数；Static 传入 `undefined` | Dynamic 非清理条件保持旧值；Static 清除回调 | Dynamic SDK 声明未公开 `undefined` 参数 | AC-1.4, AC-1.5 |
| R-5 | 行为 | 节点执行非主树到主树迁移 | 先同步 `onAttach`，再投递异步 `onAppear` | `onAppear` 在 UI TaskExecutor 执行 | AC-2.1 |
| R-6 | 行为 | 节点执行主树到非主树迁移 | 同步依次调用 `onDetach`、`onDisAppear` | 两个回调都发生在 RenderContext 消失处理之前 | AC-2.2 |
| R-7 | 边界 | 仅修改 visibility 或 active | 不触发四个生命周期事件 | 本特性不等同于可见性属性或可见面积监听 | AC-2.3 |
| R-8 | 边界 | Attach 时 `onMainTree_ == true`，或 Detach 时 `onMainTree_ == false` | 直接返回，不触发回调 | 每次真实状态跃迁最多触发一轮 | AC-2.4 |
| R-9 | 恢复 | 节点离树后重新挂树且回调未清理 | 沿用原事件槽并再次触发 | 离树流程不自动注销用户回调 | AC-2.5 |
| R-10 | 边界 | 带消失转场的节点开始从父节点移除 | 先完成逻辑 Detach，再保留 disappearing child 用于动画 | 回调不等待动画完成 | AC-2.6 |
| R-11 | 边界 | `onAppear` UI 任务待执行期间节点离树 | 同步离树回调可能先执行；已投递任务无显式取消 | 任务执行时读取当前 `onAppear` 槽 | AC-2.7 |
| R-12 | 行为 | 主线程通过 NativeNodeAPI_1 注册四类事件 | 事件类型映射到对应 EventHub 回调 | Native API 版本 1，自 API 12 开放 | AC-3.1, AC-4.4 |
| R-13 | 行为 | Native 生命周期事件派发 | 事件类型为 `ArkUI_NodeComponentEvent`，无业务参数，保留 targetId/userData | 事件对象仅在回调期间有效 | AC-3.2 |
| R-14 | 边界 | API 12 泛型入口重复注册同一 eventType | 更新 targetId/userData 并覆盖底层单槽包装回调 | 同一 eventType 仅保留一项映射 | AC-3.3 |
| R-15 | 恢复 | API 12 泛型入口注销事件 | 删除映射并 Reset 底层事件 | 未注册、空节点等情况无派发 | AC-3.4 |
| R-16 | 异常 | API 21 CommonEvent 注册 attach/detach 或重复注册同一事件 | attach/detach 返回 106110；重复注册保留首次 callback 但更新 userData | CommonEvent 白名单仅含 appear/disappear | AC-3.5, AC-3.6 |
| R-17 | 行为 | Dynamic ArkTS 使用生命周期接口 | appear/disappear 自 API 7，attach/detach 自 API 12 | Form/Cross-platform/Atomic service 按 SDK 标注开放 | AC-4.1 |
| R-18 | 行为 | Static ArkTS API 23 调用生命周期接口 | 四接口接受 callback 或 `undefined` | `undefined` 走 Disable | AC-1.5, AC-4.2 |
| R-19 | 边界 | 旧 Pipeline 调用生命周期注册/Disable | 仅 appear/disappear 有旧 EventMarker 实现；attach/detach 和 Disable 为空实现 | 不得承诺与 NG 管线等价 | AC-4.3 |
| R-20 | 行为 | Native API 12/21 调用生命周期事件入口 | API 12 泛型入口覆盖四事件；API 21 CommonEvent 仅覆盖 appear/disappear | 两套入口使用不同事件数据存储 | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, AC-1.2, R-1, R-2 | Host 单测 | 单事件槽保存与重复注册覆盖 |
| VM-2 | AC-1.3~AC-1.5, R-3, R-4 | Bridge/Static 单测补充 + 源码审查 | Dynamic API 11 清理门槛与 Static `undefined` 清理 |
| VM-3 | AC-2.1, AC-2.2, R-5, R-6 | Host 单测 | Attach/Appear 与 Detach/Disappear 的顺序和同步性 |
| VM-4 | AC-2.3, AC-2.4, R-7, R-8 | Host 单测 | visibility/active 不触发及主树状态幂等 |
| VM-5 | AC-2.5, AC-2.6, R-9, R-10 | Host 集成测试 | 重挂载与消失转场边界 |
| VM-6 | AC-2.7, R-11 | 可控 TaskExecutor 单测 | 快速离树时待执行 `onAppear` 的时序 |
| VM-7 | AC-3.1~AC-3.5, R-12~R-16 | C API 单测 | 四事件映射、注销、错误码与 API 21 白名单 |
| VM-8 | AC-3.6, R-16 | C API 回归测试 | API 21 重复注册及注销后重注册的 callback/userData 组合 |
| VM-9 | AC-4.1~AC-4.4, R-17~R-20 | SDK 审查 + 双管线测试 | API 版本和 Legacy/NG 支持边界 |

## API 变更分析

> 本特性为已有 API 的规格补录，不引入新的 API 或 ABI 变更。下表记录纳入规格的现有接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `onAppear(event: () => void): T` | Public | 无参回调 | `T` | N/A | 订阅组件进入主树后的显现回调 | AC-1.1, AC-2.1 |
| `onDisAppear(event: () => void): T` | Public | 无参回调 | `T` | N/A | 订阅组件离开主树时的消失回调 | AC-1.1, AC-2.2 |
| `onAttach(callback: Callback<void>): T` | Public | 无参回调 | `T` | N/A | 订阅组件挂到主树事件 | AC-1.1, AC-2.1 |
| `onDetach(callback: Callback<void>): T` | Public | 无参回调 | `T` | N/A | 订阅组件从主树分离事件 | AC-1.1, AC-2.2 |
| `ArkUI_NativeNodeAPI_1::registerNodeEvent(...)` | Public C API | node、eventType、targetId、userData | `int32_t` | 0, 401, 106102, 106103 | 注册 API 12 Native 生命周期事件 | AC-3.1~AC-3.3 |
| `ArkUI_NativeNodeAPI_1::unregisterNodeEvent(...)` | Public C API | node、eventType | `void` | N/A | 注销 API 12 Native 生命周期事件 | AC-3.4 |
| `OH_ArkUI_NativeModule_RegisterCommonEvent(...)` | Public C API | node、eventType、userData、callback | `int32_t` | 0, 401, 500, 106110 | 注册 API 21 CommonEvent；本特性仅 appear/disappear | AC-3.5, AC-3.6 |
| `OH_ArkUI_NativeModule_UnregisterCommonEvent(...)` | Public C API | node、eventType | `int32_t` | 0, 401, 500, 106110 | 注销 API 21 CommonEvent | AC-3.5, AC-3.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | 本次仅补录规格，无接口变更或废弃 | — | — |

## 接口规格

### 接口定义

**ArkTS 生命周期事件组**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onAppear(event: () => void): T`; `onDisAppear(event: () => void): T`; `onAttach(callback: Callback<void>): T`; `onDetach(callback: Callback<void>): T` |
| 返回值 | `T` — 返回当前组件属性链对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.7, AC-4.1~AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event/callback | `() => void` / `Callback<void>` | Dynamic SDK 声明为是；Static 可为 `undefined` | 无 | Dynamic 实现仅接受函数；目标 API >= 11 的 `undefined` 执行清理；Static `undefined` 执行清理 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 注册后节点进入主树 | 见 Gherkin 场景“进入主树的同步与异步回调” | AC-2.1 |
| 2 | 节点离开主树 | 见 Gherkin 场景“离开主树的同步回调顺序” | AC-2.2 |
| 3 | 重复注册或清理 | 见 Gherkin 场景“覆盖与版本化清理” | AC-1.2~AC-1.5 |

**NativeNodeAPI_1 生命周期事件注册**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t registerNodeEvent(ArkUI_NodeHandle node, ArkUI_NodeEventType eventType, int32_t targetId, void* userData)`; `void unregisterNodeEvent(ArkUI_NodeHandle node, ArkUI_NodeEventType eventType)` |
| 返回值 | 注册返回错误码；注销无返回值 |
| 开放范围 | Public C API |
| 错误码 | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID`, `ARKUI_ERROR_CODE_ATTRIBUTE_OR_EVENT_NOT_SUPPORTED`, `ARKUI_ERROR_CODE_NOT_SUPPROTED_FOR_ARKTS_NODE` |
| 关联 AC | AC-3.1~AC-3.4, AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | `ArkUI_NodeHandle` | 是 | 无 | 必须是支持 Native 事件的有效节点；API 必须在主线程调用 |
| eventType | `ArkUI_NodeEventType` | 是 | 无 | 本特性接受 APPEAR、DISAPPEAR、ATTACH、DETACH 四类事件 |
| targetId | `int32_t` | 是 | 无 | 原样传入 `ArkUI_NodeEvent` |
| userData | `void*` | 否 | `nullptr` | 原样传入 `ArkUI_NodeEvent`，生命周期由调用方管理 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效节点注册四类事件 | 建立 eventType 到底层 EventHub 的单项映射 | AC-3.1 |
| 2 | 相同 eventType 重复注册 | 更新 targetId/userData，不增加第二项映射 | AC-3.3 |
| 3 | 注销已注册事件 | 删除映射并重置底层事件槽 | AC-3.4 |

**API 21 CommonEvent 生命周期注册**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_NativeModule_RegisterCommonEvent(ArkUI_NodeHandle node, ArkUI_NodeEventType eventType, void* userData, void (*callback)(ArkUI_NodeEvent* event))`; `int32_t OH_ArkUI_NativeModule_UnregisterCommonEvent(ArkUI_NodeHandle node, ArkUI_NodeEventType eventType)` |
| 返回值 | `int32_t` — 操作结果码 |
| 开放范围 | Public C API |
| 错误码 | 0, 401, 500（实现分支）, 106110 |
| 关联 AC | AC-3.5, AC-3.6, AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | `ArkUI_NodeHandle` | 是 | 无 | `nullptr` 返回 401；必须在主线程调用 |
| eventType | `ArkUI_NodeEventType` | 是 | 无 | 本特性仅支持 APPEAR、DISAPPEAR；ATTACH、DETACH 返回 106110 |
| userData | `void*` | 否 | `nullptr` | 当前实现重复注册时更新该值 |
| callback | `void (*)(ArkUI_NodeEvent*)` | 是 | 无 | `nullptr` 返回 401；当前实现重复注册不替换首次 callback |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 注册 APPEAR/DISAPPEAR | 使用独立 CommonEvent 槽订阅事件 | AC-3.5 |
| 2 | 注册 ATTACH/DETACH | 返回 106110，不建立订阅 | AC-3.5 |
| 3 | 对同一事件重复注册 | 保留首次 callback，更新 userData；作为实现风险验证 | AC-3.6 |

## 兼容性声明

- **已有 API 行为变更:** 否。本次仅补录当前实现；需注意以下既有版本差异：
  - Dynamic `onAppear`/`onDisAppear` 自 API 7 开放，Form 自 API 9、Cross-platform 自 API 10、Atomic service 自 API 11；`onAttach`/`onDetach` 自 API 12 开放。
  - Dynamic `undefined` 清理能力以目标 API 11 为门槛，但可用 Dynamic SDK 声明仍要求必传函数，属于 SDK 声明与实现能力差异。
  - Static 四接口自 API 23 static 开放并显式允许 `undefined`。
  - 旧 Pipeline 的 `onAttach`/`onDetach` 与四项 Disable 为空实现，不能承诺 NG 等价行为。
  - Native API 12 泛型入口支持四事件；API 21 CommonEvent 仅支持 appear/disappear，且重复注册存在 callback/userData 不一致风险。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic ArkTS API 7；完整四事件 ArkTS/Native 链路为 API 12；Static 为 API 23。
- **API 版本号策略:** 按 canonical SDK 和 Native 头文件的 `@since` 标注；Dynamic SDK 证据来自版本不完全匹配的 checkout，后续取得同版本 SDK 时需复核行号与声明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 主树状态驱动 | 四事件只能由 `onMainTree_` 状态迁移链路触发，不由 visibility、active 或可见面积变化替代 | AC-2.1~AC-2.4 |
| 同步/异步分离 | `onAttach`、`onDetach`、`onDisAppear` 同步；`onAppear` 通过 UI TaskExecutor 异步投递 | AC-2.1, AC-2.2, AC-2.7 |
| 单事件槽 | ArkTS 与 API 12 泛型 Native 事件最终写入 EventHub 用户事件槽，重复设置采用覆盖语义 | AC-1.2, AC-3.3 |
| 单向调用链 | SDK/Bridge/Native API → ViewAbstract/NodeModifier → EventHub → FrameNode/UINode 主树生命周期 | 全部 |
| 实现即规格 | API 21 CommonEvent 重复注册行为只记录为风险，不在本规格中提出修复方案 | AC-3.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 除 `onAppear` 外不新增任务投递；单次真实主树状态迁移每个已注册事件最多触发一次 | Host 单测/任务队列测试 | `ui_node.cpp:1020-1024,1077-1081`; `event_hub.cpp:608-645` |
| 功耗 | 无独立周期任务或轮询 | 源码审查 | 生命周期回调仅由主树迁移触发 |
| 内存 | 每个 EventHub 生命周期事件保持单个用户回调槽；Native API 12 每个 eventType 保持单项映射 | Host/C API 单测 | `event_hub.h:331-352`; `node_model.cpp:550-563` |
| 安全 | Native Node 入口校验 node、eventType 和线程；回调对象不得跨回调生命周期保存 | C API 错误路径测试 | `native_node.h:12931-12939,13080-13107` |
| 可靠性 | 重复 Attach/Detach 幂等；离树不自动清除用户注册 | Host 单测 | `ui_node.cpp:1020-1024,1077-1081`; `event_hub.cpp:723-728` |
| 可测试性 | EventHub/ViewAbstract 已有单测；Bridge、快速挂卸载与 API 21 重复注册需补充分层回归用例 | 测试覆盖审查 | `event_hub_test_ng.cpp:515-600,2057-2098`; `native_node_test.cpp:10165-10199` |
| 自动化维测 | 事件任务名固定为 `ArkUIFrameNodeAppearEvent`，可用于任务链路定位 | 日志/任务追踪 | `event_hub.cpp:615-630` |
| 定界定位 | 通过主树状态、事件类型、targetId/userData 和同步/异步边界区分问题层次 | 日志/断点 | `ui_node.cpp:1020-1119`; `node_model.cpp:535-647` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 由通用 FrameNode/UINode 主树生命周期实现 | Host/XTS | 通用核心实现 |
| 平板 | 无差异 | 同手机 | Host/XTS | 通用核心实现 |
| 折叠屏 | 无差异 | 折叠状态本身不改变本特性的触发定义 | Host/XTS | 通用核心实现 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不改变无障碍树、语义或焦点行为 | — |
| 大字体 | 否 | 不依赖字体度量 | — |
| 深色模式 | 否 | 不依赖颜色模式 | — |
| 多窗口/分屏 | 是 | 窗口引起的真实主树迁移按本规格触发；单纯可见性变化不触发 | AC-2.1~AC-2.3 |
| 多用户 | 否 | 无用户数据持久化 | — |
| 版本升级 | 是 | API 7/11/12/21/23 和旧 Pipeline 差异需保留 | AC-1.3~AC-1.5, AC-4.1~AC-4.4 |
| 生态兼容 | 是 | ArkTS 与两套 Native 注册入口的支持范围不同 | AC-3.1~AC-3.6 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 组件挂载与显隐生命周期事件
  作为 ArkUI 应用和 Native UI 开发者
  我想要订阅组件进入或离开主树的生命周期事件
  以便按明确的时序管理业务资源

  Scenario: 进入主树的同步与异步回调
    Given 节点不在主树且已注册 onAttach 和 onAppear
    When 节点执行 AttachToMainTree
    Then onAttach 在当前调用栈同步执行
    And onAppear 被投递到 UI 任务队列异步执行

  Scenario: 离开主树的同步回调顺序
    Given 节点在主树且已注册 onDetach 和 onDisAppear
    When 节点执行 DetachFromMainTree
    Then onDetach 先同步执行
    And onDisAppear 随后同步执行

  Scenario: 可见性变化不等于主树迁移
    Given 节点保持在主树
    When 仅修改 visibility 或 active 状态
    Then onAppear、onDisAppear、onAttach、onDetach 均不触发

  Scenario Outline: Dynamic 回调清理的版本边界
    Given 同一事件已注册回调
    When 目标 API 为 <目标版本> 且向事件传入 undefined
    Then <结果>

    Examples:
      | 目标版本 | 结果 |
      | 10 | 保留已有回调 |
      | 11 | 清除已有回调 |

  Scenario: API 21 不支持挂载事件
    Given 有效 Native Node 和有效 callback
    When CommonEvent 入口注册 NODE_EVENT_ON_ATTACH 或 NODE_EVENT_ON_DETACH
    Then 返回 ARKUI_ERROR_CODE_NODE_UNSUPPORTED_EVENT_TYPE
    And 不建立生命周期事件订阅
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：仅覆盖 onAppear/onDisAppear/onAttach/onDetach，不包含焦点、区域、尺寸或可见区域事件
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致，每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] ArkTS Public API 已与 SDK 类型声明交叉核查，版本不匹配风险已显式记录
- [x] Native API 已与 `native_node.h` 和真实实现交叉核查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode OnAttachToMainTree OnDetachFromMainTree EventHub FireOnAppear FireOnDetach lifecycle ordering"
  - repo: "openharmony/arkui_ace_engine"
    query: "NativeNode NODE_EVENT_ON_APPEAR NODE_EVENT_ON_DISAPPEAR NODE_EVENT_ON_ATTACH NODE_EVENT_ON_DETACH registration"
  - repo: "openharmony/interface_sdk-js"
    query: "CommonMethod onAppear onDisAppear onAttach onDetach API version static signature"
```

**关键文档：** `interfaces/native/native_node.h`; `frameworks/core/components_ng/event/event_hub.cpp`; `frameworks/core/components_ng/base/frame_node.cpp`
