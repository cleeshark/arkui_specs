# 特性规格

> Func-04-04-01-Feat-01 触摸回调与传播控制：固化 ArkTS 动态/静态接口、Modifier/FrameNode 接口与 Native Node 触摸回调的注册、替换、注销、冒泡、默认行为控制和鼠标兼容规则。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 触摸回调与传播控制 (Touch Callback and Propagation Control) |
| 特性编号 | Func-04-04-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 ArkTS API 7 起；Native API 12 起；API 11/12/21/23 存在能力边界 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 触摸回调注册、替换与注销规格 | 补录动态 ArkTS、静态 ArkTS、UICommonEvent、Modifier/FrameNode 和 Native Node 已有行为 |
| ADDED | 触摸事件传播与默认行为控制规格 | 补录 `stopPropagation()`、`preventDefault()`、同节点回调顺序和异常边界 |
| ADDED | 鼠标左键兼容规格 | 补录鼠标事件转换为触摸事件并进入 `onTouch` 管线的已有行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| 功能域设计 | `specs/04-common-capability/04-common-events/01-touch-events/design.md` | 与本 Spec 同步生成 |
| 动态 SDK 契约 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:10983`、`:21096`、`:30240` | 已核验 |
| 静态 SDK 契约 | `interface/sdk-js/api/arkui/component/common.static.d.ets:5536`、`:12114`、`:16394` | 已核验 |
| Native SDK 契约 | `interfaces/native/native_node.h:9978`、`:12679`、`:14065`；`interfaces/native/ui_input_event.h:1145` | 已核验 |
| 动态前端实现 | `frameworks/bridge/declarative_frontend/jsview/js_interactable_view.cpp:75` | 已核验 |
| NG 触摸事件实现 | `frameworks/core/components_ng/event/touch_event.cpp:88`、`:334` | 已核验 |

## 用户故事

### US-1: 注册、替换和注销触摸回调

**作为** ArkUI 应用开发者，
**我想要** 为组件注册或注销触摸回调，
**以便** 处理触摸生命周期并在组件状态变化时安全移除监听。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 动态 ArkTS 在组件上调用 `onTouch(callback)` 且 `callback` 为函数 THEN 后续命中该组件的 DOWN、MOVE、UP、CANCEL 触摸事件调用该回调 | 正常 |
| AC-1.2 | WHEN 同一组件再次调用 `onTouch(newCallback)` THEN `newCallback` 替换旧的用户回调，后续事件不再调用旧回调 | 正常 |
| AC-1.3 | WHEN 目标 API 版本大于等于 11 且动态 ArkTS 调用 `onTouch(undefined)` THEN 清除该组件的用户触摸回调 | 边界 |
| AC-1.4 | WHEN 目标 API 版本小于 11 且动态 ArkTS 调用 `onTouch(undefined)` THEN 调用被忽略，原用户回调保持不变 | 边界 |
| AC-1.5 | WHEN 静态 ArkTS `onTouch(undefined)` 或 `UICommonEvent.setOnTouch(undefined)` 被调用 THEN 清除对应用户触摸回调 | 正常 |
| AC-1.6 | WHEN 清除用户触摸回调 THEN 组件内部触摸监听、touch-after 监听和 Native 公共事件回调不因该操作被一并清除 | 边界 |

### US-2: 控制触摸事件冒泡

**作为** ArkUI 应用开发者，
**我想要** 在触摸回调内决定事件是否继续向其他命中节点传播，
**以便** 避免父子组件重复响应同一次触摸。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `onTouch` 回调不调用 `stopPropagation()` THEN `TouchEventActuator::HandleEvent()` 返回继续传播，后续命中节点仍可收到触摸事件 | 正常 |
| AC-2.2 | WHEN `onTouch` 回调同步调用 `stopPropagation()` THEN 当前节点完成自身回调序列后，后续非手势触摸目标不再执行用户触摸回调 | 正常 |
| AC-2.3 | WHEN 当前节点存在内部监听、用户回调、touch-after、FrameNode 回调和 Native 公共回调 THEN 按“内部监听 → 用户回调 → touch-after → FrameNode 回调 → Native 公共回调”顺序执行 | 正常 |
| AC-2.4 | WHEN 当前节点的用户回调调用 `stopPropagation()` THEN 已进入当前节点回调序列的 touch-after、FrameNode 和 Native 公共回调仍会执行 | 边界 |
| AC-2.5 | WHEN Native `OH_ArkUI_PointerEvent_SetStopPropagation(event, true)` 接收有效触摸事件 THEN 返回成功并阻止事件继续冒泡 | 正常 |
| AC-2.6 | WHEN Native `OH_ArkUI_PointerEvent_SetStopPropagation` 的 `event` 为空或不是受支持的触摸/鼠标/悬停事件 THEN 返回参数错误或输入事件类型不支持错误 | 异常 |

### US-3: 使用鼠标左键触发触摸回调

**作为** 桌面设备或多输入设备应用开发者，
**我想要** 鼠标左键操作复用触摸回调，
**以便** 同一套交互逻辑同时适配触摸屏和鼠标。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 鼠标左键产生 PRESS、MOVE、RELEASE THEN 分别转换为 TouchType.DOWN、MOVE、UP 并进入触摸管线 | 正常 |
| AC-3.2 | WHEN 鼠标事件产生 CANCEL THEN 转换为 TouchType.CANCEL 并进入触摸管线 | 恢复 |
| AC-3.3 | WHEN 鼠标右键或中键执行 PRESS、MOVE、RELEASE 且不满足左键按下条件 THEN 不作为普通 `onTouch` 事件进入触摸回调 | 边界 |
| AC-3.4 | WHEN 鼠标事件转换为触摸事件 THEN 事件保留 `SourceType::MOUSE` 和鼠标 `SourceTool`，而不是伪装为触摸屏来源 | 正常 |

### US-4: 阻止 Hyperlink 默认跳转

**作为** Hyperlink 组件开发者，
**我想要** 在触摸回调内阻止默认跳转，
**以便** 根据业务条件接管链接激活行为。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN Hyperlink 的触摸回调同步调用 `preventDefault()` THEN 当前触摸序列的默认链接跳转被阻止 | 正常 |
| AC-4.2 | WHEN 非 Hyperlink 组件的触摸回调调用 `preventDefault()` THEN 抛出 BusinessError 100017，且不设置 prevent-default 状态 | 异常 |
| AC-4.3 | WHEN `preventDefault()` 成功执行 THEN 仅改变默认行为标记，不自动设置 stop-propagation 标记 | 边界 |
| AC-4.4 | WHEN 回调返回后才异步调用 `stopPropagation()` 或 `preventDefault()` THEN 该调用不能改变已经完成回写的当前触摸事件传播或默认行为 | 边界 |
| AC-4.5 | WHEN 通过 Modifier 路径处理触摸事件 THEN `preventDefault()` 不作为 SDK 保证能力，应用不得依赖其结果 | 异常 |

### US-5: 通过 Native Node 注册触摸事件

**作为** Native ArkUI 开发者，
**我想要** 通过 Native Node API 注册和注销触摸事件，
**以便** 在 C/C++ 业务中处理触摸回调并控制传播。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN API 12+ 使用 `ArkUI_NativeNodeAPI_1::registerNodeEvent(node, NODE_TOUCH_EVENT, targetId, userData)` 且 node 为有效 CNode THEN 注册触摸事件并在统一事件接收器中回调 | 正常 |
| AC-5.2 | WHEN API 12+ 的 `registerNodeEvent` 接收空节点、非 CNode、BuilderNode 禁止修改节点或不支持的事件类型 THEN 返回对应参数或能力错误码 | 异常 |
| AC-5.3 | WHEN API 21+ 在主线程调用 `OH_ArkUI_NativeModule_RegisterCommonEvent` 注册 `NODE_TOUCH_EVENT` 且 node、callback 有效 THEN 返回 `ARKUI_ERROR_CODE_NO_ERROR` | 正常 |
| AC-5.4 | WHEN API 21+ 直接注册接口接收空 node、空 callback 或不支持的 eventType THEN 分别返回 `ARKUI_ERROR_CODE_PARAM_INVALID` 或 `ARKUI_ERROR_CODE_NODE_UNSUPPORTED_EVENT_TYPE` | 异常 |
| AC-5.5 | WHEN Native 注销 `NODE_TOUCH_EVENT` THEN 仅注销对应 Native 触摸回调，不清除 ArkTS 用户回调或组件内部触摸监听 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.6 | R-1~R-5 | 已有实现 | 单测 + 源码审查 | `js_interactable_view.cpp:75-110`；`touch_event.h:46-75`；`gesture_event_hub.cpp:1266-1270` |
| AC-2.1~AC-2.4 | R-6~R-8 | 已有实现 | NG 单测 | `test/unittest/core/event/touch_event_test_ng.cpp:186-267` |
| AC-2.5~AC-2.6 | R-9 | 已有实现 | C API 单测 | `test/unittest/interfaces/ace_ui_input_event/oh_arkui_pointerevent_setstoppropagation_test.cpp:24-109` |
| AC-3.1~AC-3.4 | R-10~R-11 | 已有实现 | 管线单测/源码审查 | `pipeline_context.cpp:5175-5186`；`mouse_event.cpp:440-486` |
| AC-4.1~AC-4.5 | R-12~R-14 | 已有实现 | Hyperlink 单测 + SDK 契约 | `hyperlink_test_ng.cpp:538-622`；`common.d.ts:11055-11070` |
| AC-5.1~AC-5.5 | R-15~R-17 | 已有实现 | Native Node 单测 | `test/unittest/interfaces/native_node_test.cpp:10144-10157`；`node_model.cpp:535-563` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `onTouch` 接收有效函数 | 通过 `ViewAbstract::SetOnTouch` 将函数保存为 `TouchEventActuator::userCallback_` | 每个节点仅保留一个用户回调 | AC-1.1, AC-1.2 |
| R-2 | 行为 | 同一节点重复设置 `onTouch` | 先释放旧 `userCallback_`，再保存新回调 | 内部 `touchEvents_`、`touchAfterEvents_` 和 `commonTouchEventCallback_` 不受影响 | AC-1.2, AC-1.6 |
| R-3 | 边界 | 动态前端参数为 `undefined` | target API ≥ 11 时调用 `DisableOnTouch()`；target API < 11 时因参数不是函数而直接返回 | 版本边界为 API 11 | AC-1.3, AC-1.4 |
| R-4 | 行为 | 静态 `onTouch(undefined)` 或 `setOnTouch(undefined)` | 清除用户回调 | 静态接口从 API 23 开放 | AC-1.5 |
| R-5 | 恢复 | 用户回调被注销 | 后续触摸不再调用用户回调，事件执行器和其他监听保持可用 | 注销不销毁 `TouchEventActuator` | AC-1.5, AC-1.6 |
| R-6 | 行为 | 一个触摸事件命中当前节点 | 依次执行内部监听、用户回调、touch-after、FrameNode 回调、Native 公共回调 | 当前节点回调列表按固定顺序串行执行 | AC-2.3 |
| R-7 | 行为 | 任一当前节点回调设置 stop-propagation | 全部当前节点回调执行结束后，`HandleEvent()` 返回 false | 不回滚已经执行的当前节点回调 | AC-2.2, AC-2.4 |
| R-8 | 行为 | stop-propagation 未设置 | `HandleEvent()` 返回 true，事件管理器继续调用后续非手势触摸目标 | 手势识别器仍按自身仲裁规则处理事件 | AC-2.1 |
| R-9 | 异常 | C API 设置 stop-propagation | 有效 C_TOUCH_EVENT 写入布尔标记并返回成功；空指针或不支持场景返回错误 | API 12 起；错误返回不修改有效事件状态 | AC-2.5, AC-2.6 |
| R-10 | 行为 | 鼠标左键 PRESS/MOVE/RELEASE 或 CANCEL | `MouseEvent::CreateTouchPoint()` 映射为 DOWN/MOVE/UP/CANCEL，随后调用 `OnTouchEvent()` | MOVE 需左键处于按下状态；右键/中键不满足转换条件 | AC-3.1~AC-3.3 |
| R-11 | 行为 | 鼠标转触摸 | 坐标、时间、deviceId、sourceType、sourceTool 和 pointerEvent 被复制到 TouchEvent | sourceType 保持 MOUSE | AC-3.4 |
| R-12 | 行为 | Hyperlink 同步调用 `preventDefault()` | 设置 prevent-default 标志；Hyperlink touch-after 保存该标志，click-after 不执行 `LinkToAddress()` | 仅 Hyperlink 在触摸事件中受支持 | AC-4.1 |
| R-13 | 异常 | 非 Hyperlink 调用 `preventDefault()` | 抛出错误码 100017 并立即返回，不设置 prevent-default 标志 | 允许列表仅包含 `Hyperlink` | AC-4.2 |
| R-14 | 边界 | 回调已返回或使用未承诺的 Modifier prevent-default 路径 | 当前事件已完成标志回写，异步调用不能改变当前传播；Modifier prevent-default 不属于 SDK 保证范围 | `preventDefault` 与 `stopPropagation` 为两个独立标志 | AC-4.3~AC-4.5 |
| R-15 | 行为 | API 12+ 通过 `ArkUI_NativeNodeAPI_1` 注册 `NODE_TOUCH_EVENT` | 为 CNode 保存 targetId/userData 并安装 Native 触摸回调 | 空节点、非 CNode、受限 BuilderNode 和不支持事件返回错误 | AC-5.1, AC-5.2 |
| R-16 | 行为 | API 21+ 直接注册 Native 公共触摸事件 | 建立 node/eventType 到 callback/userData 的映射并安装 `commonTouchEventCallback_` | 必须在主线程调用 | AC-5.3, AC-5.4 |
| R-17 | 恢复 | 注销 Native 触摸事件 | 清除对应 Native 事件映射和 Native 公共回调 | 不清除 ArkTS `userCallback_`、内部监听和 touch-after | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, AC-1.2, R-1, R-2 | Host 单测 | 注册后触发、重复注册只调用新回调 |
| VM-2 | AC-1.3, AC-1.4, R-3 | target API 参数化单测 | API 10 与 API 11 的 `undefined` 注销差异 |
| VM-3 | AC-1.5, AC-1.6, R-4, R-5 | 静态前端/Modifier 单测 | `undefined` 清除范围不越界 |
| VM-4 | AC-2.1~AC-2.4, R-6~R-8 | `touch_event_test_ng` | 回调顺序与 stop-propagation 生效时点 |
| VM-5 | AC-2.5, AC-2.6, R-9 | C API 单测 | true/false 写入、空指针和不支持事件错误码 |
| VM-6 | AC-3.1~AC-3.4, R-10, R-11 | Pipeline 单测 | 鼠标动作映射、非左键过滤、来源字段保留 |
| VM-7 | AC-4.1~AC-4.3, R-12, R-13 | Hyperlink 单测 | 默认跳转抑制、100017 异常、传播标志独立 |
| VM-8 | AC-4.4, AC-4.5, R-14 | ArkTS 集成测试 | 同步生命周期和 Modifier 契约边界 |
| VM-9 | AC-5.1, AC-5.2, R-15 | Native Node 单测 | API 12 注册、CNode/BuilderNode 参数边界 |
| VM-10 | AC-5.3~AC-5.5, R-16, R-17 | Native 公共事件单测 | API 21 注册/注销、主线程约束、错误码和隔离性 |

## API 变更分析

> 本文为已有能力补录，不修改公开 API；下表列出纳入基线的既有 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `CommonMethod<T>.onTouch(event: (event: TouchEvent) => void): T` | Public | 触摸回调 | 当前组件 | N/A | 动态 ArkTS 注册触摸回调，API 7 起 | AC-1.1~AC-1.4 |
| `CommonMethod.onTouch(event: ((event: TouchEvent) => void) \| undefined): this` | Public | 回调或 undefined | 当前组件 | N/A | 静态 ArkTS 注册或重置触摸回调，API 23 起 | AC-1.5 |
| `UICommonEvent.setOnTouch(callback: Callback<TouchEvent> \| undefined): void` | Public | 回调或 undefined | void | N/A | FrameNode/UICommonEvent 注册或重置，动态 API 12、静态 API 23 起 | AC-1.5, AC-1.6 |
| `TouchEvent.stopPropagation(): void` | Public | 无 | void | N/A | 阻止事件继续冒泡 | AC-2.1~AC-2.4 |
| `TouchEvent.preventDefault(): void` | Public | 无 | void | BusinessError 100017 | 阻止 Hyperlink 默认跳转，动态 API 12、静态 API 23 起 | AC-4.1~AC-4.5 |
| `ArkUI_NativeNodeAPI_1::registerNodeEvent(...)` | Public C API | node、NODE_TOUCH_EVENT、targetId、userData | int32_t | 401、106102、106103 | API 12+ 注册 Native Node 触摸事件 | AC-5.1, AC-5.2 |
| `OH_ArkUI_NativeModule_RegisterCommonEvent(...)` | Public C API | node、eventType、userData、callback | int32_t | 0、401、106110 | API 21+ 直接注册 Native 公共事件 | AC-5.3, AC-5.4 |
| `OH_ArkUI_PointerEvent_SetStopPropagation(...)` | Public C API | 输入事件和布尔标记 | int32_t | 0、401、输入事件类型不支持 | API 12+ 设置 Native 事件冒泡状态 | AC-2.5, AC-2.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录已有行为 | 无需迁移 | 全部 |

## 接口规格

### 接口定义

**`CommonMethod.onTouch`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onTouch(event: (event: TouchEvent) => void): T`；静态版本允许 `undefined` |
| 返回值 | 当前组件，用于链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.6、AC-2.1~AC-2.4、AC-3.1~AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | `(event: TouchEvent) => void` | 动态 API 7~10 是 | 无 | 非函数参数被忽略；target API ≥ 11 的 undefined 用于注销 |
| event | `((event: TouchEvent) => void) \| undefined` | 静态否 | undefined | undefined 清除用户回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效回调、重复注册、undefined 或鼠标左键输入 | 见 Gherkin 场景 1~5 | AC-1.1~AC-3.4 |

**`TouchEvent.stopPropagation` / `TouchEvent.preventDefault`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `stopPropagation(): void`；`preventDefault(): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | stopPropagation: N/A；preventDefault: BusinessError 100017 |
| 关联 AC | AC-2.1~AC-2.6、AC-4.1~AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| 无 | N/A | N/A | N/A | 必须在当前同步触摸回调期间调用；preventDefault 仅支持 Hyperlink |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 同步控制传播或默认行为 | 见 Gherkin 场景 6~8 | AC-2.1~AC-4.5 |

**Native Node 触摸注册与传播接口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `registerNodeEvent(node, NODE_TOUCH_EVENT, targetId, userData)`；`OH_ArkUI_NativeModule_RegisterCommonEvent(node, NODE_TOUCH_EVENT, userData, callback)`；`OH_ArkUI_PointerEvent_SetStopPropagation(event, flag)` |
| 返回值 | int32_t 状态码 |
| 开放范围 | Public C API |
| 错误码 | 0、401、106102、106103、106110、输入事件类型不支持 |
| 关联 AC | AC-2.5、AC-2.6、AC-5.1~AC-5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | `ArkUI_NodeHandle` | 是 | 无 | API 12 模块表路径要求有效 CNode；API 21 直接路径要求有效节点 |
| eventType | `ArkUI_NodeEventType` | 是 | 无 | 本特性限定 `NODE_TOUCH_EVENT` |
| callback | `void (*)(ArkUI_NodeEvent*)` | API 21 路径是 | 无 | 不得为空；接口要求主线程调用 |
| event | `ArkUI_UIInputEvent*` | 设置传播时是 | 无 | 必须来自受支持的触摸回调场景，不得传空指针 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 注册、传播控制、注销或非法参数 | 见 Gherkin 场景 9~11 | AC-2.5、AC-2.6、AC-5.1~AC-5.5 |

## 兼容性声明

- **已有 API 行为变更:** 是。动态 `onTouch(undefined)` 从 target API 11 起具备注销语义；API 10 及以下保持忽略非函数参数的旧行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 动态 ArkTS API 7；Native Node/输入事件 API 12；静态 ArkTS API 23。
- **API 版本号策略:** `onTouch`/`stopPropagation` 按 API 7 基线；UICommonEvent、`preventDefault` 和 Native 输入接口按 API 12；直接 Native 公共事件注册按 API 21；静态接口按 API 23。
- **SDK 与源码偏差:** 动态 SDK 的 `CommonMethod.onTouch` 未声明 `undefined`，源码仅在 target API ≥ 11 接受其作为注销信号；Modifier 路径存在事件对象实现，但 SDK 明确声明 `preventDefault` 不支持 Modifier 集成，因此 Spec 按 SDK 契约视为不保证能力。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 同步回调约束 | JS/ArkTS 回调返回后立即将 stop-propagation 和 prevent-default 标志回写到原始 `TouchEventInfo` | AC-2.2、AC-4.1、AC-4.4 |
| 单用户回调槽 | `onTouch` 对应 `userCallback_`，重复注册执行替换而非追加 | AC-1.2 |
| 回调通道隔离 | 用户、内部、touch-after、FrameNode 和 Native 公共回调使用不同存储槽，注销必须按通道隔离 | AC-1.6、AC-5.5 |
| 传播层级 | stop-propagation 在当前节点回调序列结束后由 `HandleEvent()` 返回值传给 EventManager | AC-2.2~AC-2.4 |
| 主线程约束 | Native 直接公共事件注册/注销接口只允许主线程调用 | AC-5.3~AC-5.5 |
| 公开契约优先 | SDK 声明与源码能力不一致时，以 SDK 为对外契约并在风险中记录实现偏差 | AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增事件调度或异步任务；每个命中节点按已有回调槽顺序同步执行 | NG 单测/Trace | `touch_event.cpp:334-359` |
| 功耗 | 不新增周期任务；仅在输入事件到达时执行 | 源码审查 | `event_manager.cpp:1208-1260` |
| 内存 | 重复注册先释放旧用户回调；事件对象仅在回调生命周期内绑定原生信息 | 泄漏检测/源码审查 | `touch_event.h:46-52`；`js_interactable_view.cpp:95-108` |
| 安全 | Native 接口拒绝空指针和不支持事件类型；不得跨回调保存事件指针 | C API 单测 | `node_utils.cpp:835-884`；`native_node.h:12858-12864` |
| 可靠性 | CANCEL 必须沿触摸管线到达，允许组件恢复按压态 | Pipeline 单测 | `pipeline_context.cpp:5175-5186` |
| 可测试性 | 所有版本边界、错误码和传播结果均可通过 Host/C API 单测观察 | 单测 | VM-1~VM-10 |
| 自动化维测 | 保留 ACE_SCORING_EVENT 和输入事件 Trace，不新增日志协议 | Trace 检查 | `js_interactable_view.cpp:93-104`；`touch_event.cpp:90-106` |
| 定界定位 | 可通过事件树、TouchEventActuator 类型和 stop-propagation 返回值定位传播停止节点 | Dump/Trace | `event_manager.cpp:1528-1555` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 触摸屏为主要输入；行为无额外差异 | DOWN/MOVE/UP/CANCEL 与传播规则一致 | 真机/XTS | AC-1.1、AC-2.1~AC-2.4 |
| 平板 | 可同时存在触摸屏和鼠标 | 鼠标左键转换后保留 MOUSE 来源 | 真机/模拟输入 | AC-3.1~AC-3.4 |
| 折叠屏 | 折叠切屏可能产生 CANCEL | CANCEL 必须进入触摸管线以恢复组件状态 | 折叠场景测试 | AC-3.2 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | TouchType 还包含无障碍悬停类型，但其数据模型归 Feat-02；本 Feat 仅固化普通触摸回调传播 | 范围隔离 |
| 大字体 | 否 | 触摸回调与字体缩放无关 | N/A |
| 深色模式 | 否 | 触摸回调与颜色主题无关 | N/A |
| 多窗口/分屏 | 是 | 事件仍按对应窗口 PipelineContext 分发，回调与传播语义不变 | AC-1.1、AC-2.1 |
| 多用户 | 否 | 不读取用户态数据 | N/A |
| 版本升级 | 是 | API 11 注销语义、API 12/21 Native 能力、API 23 静态接口需保持兼容 | AC-1.3~AC-1.5、AC-5.1~AC-5.4 |
| 生态兼容 | 是 | 鼠标左键复用触摸回调；Native 与 ArkTS 共享 TouchEventActuator 传播语义 | AC-3.1~AC-3.4、AC-5.1~AC-5.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 触摸回调与传播控制
  作为 ArkUI 应用或 Native 开发者
  我想要注册触摸回调并控制传播和默认行为
  以便在多输入设备上获得一致、可预测的交互

  Scenario: 注册并替换用户触摸回调
    Given 组件已通过 onTouch 注册 callbackA
    When 同一组件再次通过 onTouch 注册 callbackB 并触发一次 DOWN
    Then callbackA 不被调用
    And callbackB 被调用一次

  Scenario Outline: 动态 onTouch undefined 的版本行为
    Given 应用 target API 为 <版本>
    And 组件已注册用户触摸回调
    When 调用 onTouch(undefined)
    Then 后续触摸事件的用户回调状态为 <结果>

    Examples:
      | 版本 | 结果 |
      | 10 | 保留并继续调用 |
      | 11 | 清除且不再调用 |

  Scenario: 注销不清除其他触摸通道
    Given 组件同时存在用户回调、内部监听和 Native 公共回调
    When 注销用户 onTouch 回调
    Then 用户回调不再执行
    And 内部监听和 Native 公共回调继续执行

  Scenario Outline: 鼠标动作转换为触摸动作
    Given 输入来源为鼠标且左键满足按下条件
    When 收到鼠标动作 <鼠标动作>
    Then onTouch 收到 <触摸动作>
    And 事件来源仍为 MOUSE

    Examples:
      | 鼠标动作 | 触摸动作 |
      | PRESS | DOWN |
      | MOVE | MOVE |
      | RELEASE | UP |
      | CANCEL | CANCEL |

  Scenario: 非左键不触发普通触摸回调
    Given 输入为鼠标右键 PRESS
    When PipelineContext 分发鼠标事件
    Then 不通过普通 onTouch 路径回调该事件

  Scenario: stopPropagation 在当前节点回调序列结束后生效
    Given 当前节点具有用户回调和 touch-after 回调
    And 父节点也具有用户触摸回调
    When 当前节点用户回调调用 stopPropagation
    Then 当前节点 touch-after 回调仍执行
    And 父节点用户触摸回调不执行

  Scenario: Hyperlink 阻止默认跳转
    Given Hyperlink 已设置触摸回调
    When 回调同步调用 preventDefault
    Then 当前触摸序列完成后不执行 LinkToAddress
    And 事件冒泡状态不被自动改变

  Scenario: 非 Hyperlink 调用 preventDefault
    Given 普通组件已设置触摸回调
    When 回调调用 preventDefault
    Then 抛出 BusinessError 100017
    And prevent-default 标志保持 false

  Scenario: API 12 Native Node 注册触摸事件
    Given node 是有效 CNode
    When 调用 registerNodeEvent 注册 NODE_TOUCH_EVENT
    Then 返回 ARKUI_ERROR_CODE_NO_ERROR
    And 触摸发生时统一事件接收器收到 ArkUI_NodeEvent

  Scenario: API 21 直接注册公共触摸事件
    Given 在主线程传入有效 node 和 callback
    When 调用 OH_ArkUI_NativeModule_RegisterCommonEvent 注册 NODE_TOUCH_EVENT
    Then 返回 ARKUI_ERROR_CODE_NO_ERROR
    And callback 可通过输入事件设置 stopPropagation

  Scenario: Native 非法参数
    Given node 或 callback 为空
    When 调用直接公共事件注册接口
    Then 返回 ARKUI_ERROR_CODE_PARAM_INVALID
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：不包含 TouchObject 完整字段、历史采样、事件注入和触摸拦截
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 规则表每条满足可复现、可观测、边界值、关联 AC、无冲突要求
- [x] 动态/静态 SDK 与 Native C API 均已核验
- [x] SDK 与源码差异已显式记录

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "触摸事件 onTouch 从 ArkTS 动态/静态接口到 ViewAbstract、GestureEventHub、TouchEventActuator 和 EventManager 的注册与传播调用链"
  - repo: "openharmony/arkui_ace_engine"
    query: "Native Node NODE_TOUCH_EVENT 注册、注销、OH_ArkUI_PointerEvent_SetStopPropagation 错误码与回调生命周期"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/common.d.ts`、`interface/sdk-js/api/arkui/component/common.static.d.ets`、`interfaces/native/native_node.h`、`interfaces/native/ui_input_event.h`
