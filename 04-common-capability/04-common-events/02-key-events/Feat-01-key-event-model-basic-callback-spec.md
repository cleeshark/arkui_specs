# 特性规格

> Func-04-04-02-Feat-01 按键事件模型与基础回调：固化 ArkTS 动态/静态 `onKeyEvent`、`KeyEvent` 数据模型、焦点链分发与消费语义，以及 Native `NODE_ON_KEY_EVENT` 和事件读取接口的现有行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 按键事件模型与基础回调 |
| 特性编号 | Func-04-04-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7~26、Native API 14~20+、Static API 23~26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 存量规格基线 | 补录 `onKeyEvent`、`KeyEvent`、焦点链传播、消费控制和 Native 基础按键事件接口 |
| ADDED | 版本与通道差异 | 记录 Dynamic、Static 与 Native API 的开放版本、字段差异和枚举差异 |
| ADDED | 风险基线 | 记录 SDK 契约与实现偏差，不改变当前产品实现 |

不包含：`onKeyPreIme`、`onKeyEventDispatch`、`NODE_ON_KEY_PRE_IME`、`NODE_DISPATCH_KEY_EVENT`、`OH_ArkUI_KeyEvent_Dispatch`（由 Feat-02 承接）；`keyboardShortcut`（由 Func-04-04-04 承接）。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/02-key-events/design.md` | 与本规格并行生成 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:12700`、`:21111` | 已核验 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets:6720`、`:12124` | 已核验 |
| Native API | `interfaces/native/native_node.h:10223`、`interfaces/native/native_key_event.h:387` | 已核验 |
| 分发实现 | `frameworks/core/common/key_event_manager.cpp:553`、`frameworks/core/components_ng/event/focus_event_handler.cpp:107` | 已核验 |

## 用户故事

### US-1: 聚焦组件接收按键事件

**作为** ArkUI 应用开发者，
**我想要** 在组件获得当前焦点后接收按键事件，
**以便** 实现键盘、遥控器或手柄输入交互。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 当前焦点节点注册 `onKeyEvent` 且收到 DOWN、UP 或可公开映射的 CANCEL 事件 THEN 用户回调收到对应 `KeyEvent` | 正常 |
| AC-1.2 | WHEN 节点不是当前焦点，或不存在 last FocusView、entry FrameNode、FocusHub THEN 按键事件不触发该节点用户回调且分发结果为未消费 | 边界 |
| AC-1.3 | WHEN 当前焦点 Scope 的最深焦点子节点消费事件 THEN 父 Scope 不再执行自身按键处理 | 正常 |
| AC-1.4 | WHEN 最深焦点子节点未消费事件 THEN 事件沿当前焦点链逐级回退到父 Scope 处理 | 正常 |
| AC-1.5 | WHEN 同一节点同时注册内部按键 handler 和用户 `onKeyEvent` THEN 两类 handler 均被执行，最终消费结果为两者结果的逻辑 OR | 边界 |
| AC-1.6 | WHEN 节点具有当前焦点但 Pipeline 焦点激活态为 false THEN 用户 `onKeyEvent` 仍先执行；焦点激活态仅影响其后的默认 click/焦点导航路径 | 边界 |

### US-2: 获取完整 KeyEvent 数据

**作为** ArkUI 应用开发者，
**我想要** 从回调中获取按键类型、键值、来源、时间、修饰键、Unicode 和锁定键状态，
**以便** 根据输入设备和按键状态做精确处理。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Dynamic API 7+ 触发 `onKeyEvent` THEN `KeyEvent` 提供 `type/keyCode/keyText/keySource/deviceId/metaKey/timestamp/stopPropagation` | 正常 |
| AC-2.2 | WHEN Dynamic API 10+/12+/14+/19+ 分别触发事件 THEN 依次可使用 `intentionCode`、`getModifierKeyState`、`unicode`、三个 Lock 状态字段 | 正常 |
| AC-2.3 | WHEN Static API 23+ 触发事件 THEN 提供基础字段、`intentionCode/getModifierKeyState/unicode`；WHEN Static API 26+ THEN 提供三个 Lock 状态字段和 `KeyType.CANCEL` | 正常 |
| AC-2.4 | WHEN Dynamic `getModifierKeyState(keys)` 的参数不是 SDK 允许的 `Ctrl/Alt/Shift` 组合 THEN 按 SDK 契约抛出 401 参数错误 | 异常 |
| AC-2.5 | WHEN OHOS MMI 事件来源为 joystick THEN `keySource` 为 JOYSTICK；WHEN 来源为其他非 joystick 类型 THEN 当前转换链映射为 KEYBOARD | 边界 |
| AC-2.6 | WHEN MMI action 为 UP 或 DOWN THEN 映射为对应公开动作；WHEN 为其他原始 action THEN 主转换链先映射为内部 UNKNOWN | 边界 |
| AC-2.7 | WHEN DOWN 已投递而对应 UP 被输入监控拦截 THEN 框架构造内部 CANCEL 并重新投递，以结束已开始的按键交互 | 恢复 |

### US-3: 控制消费和冒泡

**作为** ArkUI 应用开发者，
**我想要** 通过回调返回值或 `stopPropagation()` 控制按键事件传播，
**以便** 避免父级组件重复响应。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API 15+ `onKeyEvent` 回调返回 true THEN 当前节点消费事件，祖先焦点 Scope 不再处理 | 正常 |
| AC-3.2 | WHEN 用户回调调用 `stopPropagation()` 且返回 false 或无 boolean 返回值 THEN 当前节点仍消费事件并停止向祖先传播 | 正常 |
| AC-3.3 | WHEN 回调返回 false 且未调用 `stopPropagation()`，内部 handler 也返回 false THEN 当前节点不消费事件，允许父 Scope 或默认焦点行为继续处理 | 正常 |
| AC-3.4 | WHEN Dynamic API 7 的 void 回调未调用 `stopPropagation()` THEN 其返回值按 false 处理 | 边界 |
| AC-3.5 | WHEN JS 回调返回非 boolean 值 THEN Bridge 将回调消费结果按 false 处理，但独立保留 `stopPropagation()` 的传播控制结果 | 异常 |

### US-4: Native 节点读取和控制按键事件

**作为** Native ArkUI 开发者，
**我想要** 通过 `NODE_ON_KEY_EVENT` 获取 `ArkUI_UIInputEvent` 并读取或控制事件，
**以便** 在 C API 组件中实现与 ArkTS 一致的基础按键交互。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API 14+ 在聚焦节点注册 `NODE_ON_KEY_EVENT` 并收到按键 THEN `OH_ArkUI_NodeEvent_GetInputEvent` 返回 C key input event | 正常 |
| AC-4.2 | WHEN Native getter 接收有效 C key event THEN 可读取 type、keyCode、keyText、keySource、deviceId、timestamp、pressed keys、intention、Unicode、modifier 和 Lock 状态 | 正常 |
| AC-4.3 | WHEN 调用 `OH_ArkUI_KeyEvent_StopPropagation(event, true)` THEN Native Bridge 将 `stopPropagation` 回写到 `KeyEventInfo` | 正常 |
| AC-4.4 | WHEN 调用 `OH_ArkUI_KeyEvent_SetConsumed(event, true)` THEN Native 回调向焦点系统返回已消费 | 正常 |
| AC-4.5 | WHEN专用 Native getter 接收 null、空 inner event 或非 C key event THEN 返回对应 sentinel，并通过 latest status 报告参数错误 | 异常 |
| AC-4.6 | WHEN Lock getter 的 event 或 state 指针无效 THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`；WHEN 有效 THEN 返回 `ARKUI_ERROR_CODE_NO_ERROR` 并写入状态 | 异常 |
| AC-4.7 | WHEN `OH_ArkUI_UIInputEvent_GetPressedKeys` 的调用方缓冲区小于 pressed key 数量 THEN 返回 `ARKUI_ERROR_CODE_BUFFER_SIZE_NOT_ENOUGH` | 边界 |

### US-5: 保持跨版本和跨通道可解释性

**作为** 框架维护者，
**我想要** 明确 Dynamic、Static、Native 与内部枚举的差异，
**以便** 防止下游实现按数值错误映射或依赖未承诺行为。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 比较 ArkTS、Native 与内部动作类型 THEN 不按裸数值直接互转 CANCEL/CLICK，而使用各通道显式转换规则 | 边界 |
| AC-5.2 | WHEN SDK 将 Unicode 或 Lock 字段声明为 optional 而当前实现输出 `0/false` THEN 规格以 SDK optional 契约为准，并将实现行为记录为兼容性风险 | 边界 |
| AC-5.3 | WHEN 实现接受 SDK 未声明的 `Fn` 修饰键 THEN 不将 `Fn` 写成公共 SDK 保证，仅记录为实现扩展风险 | 边界 |
| AC-5.4 | WHEN Native Unicode getter 收到超出头文件声明的 Basic Latin 范围值 THEN 规格保留头文件约束，并记录实现未校验该范围的偏差 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1~R-6 | 已有实现 | 单测/源码审查 | `focus_event_handler.cpp:107`；`focus_hub_test_ng_two.cpp:193` |
| AC-2.1~2.7 | R-7~R-13 | 已有实现 | SDK 审查/单测 | `common.d.ts:12700`；`mmi_event_convertor.cpp:867`；`input_event_monitor_manager_test_ng.cpp:988` |
| AC-3.1~3.5 | R-14~R-18 | 已有实现 | 单测/桥接审查 | `js_view_abstract.cpp:9628`；`focus_event_handler.cpp:372` |
| AC-4.1~4.7 | R-19~R-25 | 已有实现 | C API 单测 | `native_key_event_test.cpp:139`；`oh_arkui_keyevent_gettype_test.cpp:24` |
| AC-5.1~5.4 | R-26~R-29 | 已有实现 | 契约/源码差异审查 | `native_key_event.h:387`；`key_code.h:442` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 当前 entry FocusView 的 FocusHub 收到普通按键事件 | 仅当前焦点链参与处理 | 不是 DOM 子树广播 | AC-1.1, AC-1.2 |
| R-2 | 行为 | 当前 FocusHub 类型为 SCOPE | 先递归 `lastWeakFocusNode_`，子节点未消费时再处理 Scope 自身 | 子消费后立即停止回退 | AC-1.3, AC-1.4 |
| R-3 | 边界 | `IsCurrentFocus() == false` | 当前 FocusHub 直接返回 false | 不触发内部或用户回调 | AC-1.2 |
| R-4 | 行为 | 同一节点存在内部 handler 与用户 callback | 内部 handler 先执行，用户 callback 随后仍执行，结果取 OR | 内部 handler 间遍历无公开顺序保证 | AC-1.5 |
| R-5 | 边界 | 当前节点聚焦但 Pipeline focus active 为 false | 用户 callback 正常执行 | 仅未消费后的默认 click/导航受 focus active 约束 | AC-1.6 |
| R-6 | 恢复 | last FocusView、entry FrameNode 或 FocusHub 不存在 | 返回未消费并等待后续焦点建立 | 不访问已失效 WeakPtr | AC-1.2 |
| R-7 | 行为 | Dynamic API 7+ | 输出 8 个基础字段和 `stopPropagation` | Full SysCap；跨平台自 API 10；原子服务自 API 11 | AC-2.1 |
| R-8 | 行为 | Dynamic API 分别达到 10/12/14/19 | 增加 intention/modifier/unicode/Lock 能力 | optional 字段按 SDK 声明解释 | AC-2.2 |
| R-9 | 行为 | Static API 23+/26+ | API 23 提供基础与扩展字段；API 26 增加 Lock 与 CANCEL | Stage model only | AC-2.3 |
| R-10 | 异常 | `getModifierKeyState` 参数不符合 `Ctrl/Alt/Shift` SDK 约束 | 抛出 BusinessError 401 | Stylus 场景不支持 | AC-2.4 |
| R-11 | 行为 | MMI source 为 joystick | 映射为 JOYSTICK；其他来源在当前主链映射为 KEYBOARD | Dynamic API 15+ 才公开 JOYSTICK | AC-2.5 |
| R-12 | 边界 | MMI action 非 UP/DOWN | `ConvertKeyEvent` 先映射为内部 UNKNOWN | 公开 CANCEL 可能由后续监控逻辑构造 | AC-2.6 |
| R-13 | 恢复 | DOWN 已送达且 UP 被监控链阻断 | 将事件动作改为内部 CANCEL 并结束 tracker 交互 | `isFalsifyCancel=true` | AC-2.7 |
| R-14 | 行为 | API 15+ callback 返回 true | 当前节点消费事件 | 阻止父 Scope 继续处理 | AC-3.1 |
| R-15 | 行为 | callback 调用 `stopPropagation()` | 即使 callback 返回 false，也消费事件 | Dynamic void callback 同样适用 | AC-3.2, AC-3.4 |
| R-16 | 行为 | callback 返回 false且未停止传播 | 用户 callback 不消费 | 仍需与内部 handler 结果 OR | AC-3.3 |
| R-17 | 异常 | JS callback 返回非 boolean | Bridge 将返回值按 false 处理 | `stopPropagation` 独立回写 | AC-3.5 |
| R-18 | 行为 | 用户与内部 handler 均未消费 | 进入默认 click 或焦点导航处理 | 仅 DOWN 生成常规焦点 intention，UP 仍可进入用户 callback | AC-3.3 |
| R-19 | 行为 | API 14+ `NODE_ON_KEY_EVENT` 回调 | 通过 NodeEvent 获取 `ArkUI_UIInputEvent` | 合法场景为 C key event | AC-4.1 |
| R-20 | 行为 | Native event 有效 | getter 返回桥接复制的按键字段 | `keyText` 内部缓冲最多 127 字节加终止符 | AC-4.2 |
| R-21 | 行为 | Native 调用 StopPropagation | 将 bool 写入事件并在 Bridge 回写 `KeyEventInfo` | false 可清除当前字段值 | AC-4.3 |
| R-22 | 行为 | Native 调用 SetConsumed | `isConsumed` 成为 Native callback 返回值 | 公共合法场景仅 `NODE_ON_KEY_EVENT` | AC-4.4 |
| R-23 | 异常 | Native getter 收到 null/错误 event type/空 inner event | 返回 -1、nullptr、0 等 API 指定 sentinel 并设置错误状态 | sentinel 依 getter 类型不同 | AC-4.5 |
| R-24 | 异常 | Lock getter 参数无效 | 返回 `ARKUI_ERROR_CODE_PARAM_INVALID` | state 指针必须非空 | AC-4.6 |
| R-25 | 边界 | pressed keys 输出缓冲区容量不足 | 返回 `ARKUI_ERROR_CODE_BUFFER_SIZE_NOT_ENOUGH` | 当前实现返回前不回填所需长度 | AC-4.7 |
| R-26 | 边界 | 处理 CANCEL/CLICK 跨通道转换 | ArkTS CANCEL=3、C CLICK=3、内部 CANCEL=4，必须使用显式映射 | 禁止按裸数值等同 | AC-5.1 |
| R-27 | 边界 | SDK optional 字段在实现中总被创建 | 公共契约仍允许字段缺失 | 当前 Dynamic/Static 常输出 `0/false` | AC-5.2 |
| R-28 | 边界 | 实现识别 `Fn` 修饰键 | 作为源码扩展风险记录 | SDK 仅保证 Ctrl/Alt/Shift | AC-5.3 |
| R-29 | 边界 | Native Unicode 超出 0x21~0x7E | 公共契约不承诺该值有效 | 当前实现原样返回且测试接受更大 Unicode | AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.6, R-1~R-6 | `focus_hub_test_ng_two.cpp`、`focus_hub_test_ng_three.cpp` | 当前焦点、Scope 子到父顺序、失焦、focus active |
| VM-2 | AC-2.1~2.4, R-7~R-10 | Canonical SDK 审查、Static accessor UT | 字段与 API 版本演进、参数错误 |
| VM-3 | AC-2.5~2.7, R-11~R-13 | `mmi_event_convertor.cpp`、input monitor UT | 来源、动作映射、伪 CANCEL |
| VM-4 | AC-3.1~3.5, R-14~R-18 | `focus_hub_test_ng_two.cpp:193`、Bridge 源码审查 | boolean、void、非 boolean、`stopPropagation` |
| VM-5 | AC-4.1~4.4, R-19~R-22 | `native_key_event_test.cpp:139`、SetConsumed/StopPropagation Level0 UT | Native 事件获取与回写 |
| VM-6 | AC-4.5~4.7, R-23~R-25 | Native getter/pressed keys/Lock Level0 UT | null、类型错误、buffer 不足 |
| VM-7 | AC-5.1~5.4, R-26~R-29 | SDK/头文件/Bridge 差异审查 | 枚举、optional、Fn、Unicode 偏差 |

## API 变更分析

> 本次为存量能力规格补录，不新增、变更或废弃公开 API。下表记录当前公开 API 基线。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `onKeyEvent((event: KeyEvent) => void)` | Public, Dynamic | KeyEvent callback | 当前组件 | N/A | API 7 void 回调 | AC-1.1, AC-3.4 |
| `onKeyEvent(Callback<KeyEvent, boolean>)` | Public, Dynamic | 返回消费结果的 callback | 当前组件 | N/A | API 15+ 可返回消费结果 | AC-3.1~3.3 |
| `onKeyEvent(Callback<KeyEvent, boolean> \| undefined)` | Public, Static | callback 或 undefined | 当前组件 | N/A | API 23+ 静态 ArkTS 按键回调 | AC-2.3 |
| `KeyEvent.getModifierKeyState(keys)` | Public | Ctrl/Alt/Shift 数组 | boolean | 401 | 查询修饰键组合状态 | AC-2.4 |
| `NODE_ON_KEY_EVENT` | Public, Native | Node event listener | 同步事件回调 | latest status | API 14+ Native 节点按键事件 | AC-4.1 |
| `OH_ArkUI_KeyEvent_Get*` | Public, Native | ArkUI_UIInputEvent 指针 | 字段值或 sentinel | latest status | 读取按键事件字段 | AC-4.2, AC-4.5 |
| `OH_ArkUI_KeyEvent_StopPropagation` | Public, Native | event, bool | void | latest status | 设置停止传播 | AC-4.3 |
| `OH_ArkUI_KeyEvent_SetConsumed` | Public, Native | event, bool | void | latest status | 设置消费结果 | AC-4.4 |
| `OH_ArkUI_KeyEvent_Is*LockOn` | Public, Native | event, bool* | ArkUI_ErrorCode | 0/401 | 查询锁定键状态 | AC-4.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| N/A | 无 | 本次仅补录现有能力 | 无迁移要求 | 全部 |

## 接口规格

### 接口定义

**ArkTS `onKeyEvent`**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic API 7: `onKeyEvent(event: (event: KeyEvent) => void): T`；Dynamic API 15: `onKeyEvent(event: Callback<KeyEvent, boolean>): T`；Static API 23: `onKeyEvent(event: Callback<KeyEvent, boolean> \| undefined): this` |
| 返回值 | 当前组件，用于链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.6, AC-3.1~3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | callback | Dynamic API 7/15 是；Static 可传 undefined | 无 | 仅当前焦点链触发；Dynamic 非函数参数不注册回调 |
| callback return | void/boolean | 否 | false | 仅 boolean true 表示消费；非 boolean 按 false |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 当前焦点节点收到 DOWN/UP | 触发 callback | AC-1.1 |
| 2 | callback true 或 stopPropagation | 当前节点消费并停止父级处理 | AC-3.1, AC-3.2 |
| 3 | 非当前焦点 | 不触发 callback | AC-1.2 |

**ArkTS `KeyEvent`**

| 属性 | 值 |
|------|-----|
| 接口定义 | `type/keyCode/keyText/keySource/deviceId/metaKey/timestamp/stopPropagation/intentionCode/getModifierKeyState/unicode/isNumLockOn/isCapsLockOn/isScrollLockOn` |
| 返回值 | 事件字段与查询结果 |
| 开放范围 | Public |
| 错误码 | `getModifierKeyState` 可抛 401 |
| 关联 AC | AC-2.1~2.7, AC-5.1~5.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| keys | Array<string> | 是 | 无 | SDK 保证 Ctrl/Alt/Shift；非法类型或校验失败抛 401 |
| unicode | number/long optional | 否 | 未规定 | SDK 仅保证非空格 Basic Latin 0x21~0x7E 且非 0 |
| Lock fields | boolean optional | 否 | 未规定 | Dynamic API 19+；Static API 26+ |

**Native `NODE_ON_KEY_EVENT` 与 KeyEvent API**

| 属性 | 值 |
|------|-----|
| 函数签名 | `NODE_ON_KEY_EVENT` + `OH_ArkUI_NodeEvent_GetInputEvent` + `OH_ArkUI_KeyEvent_Get*`/`StopPropagation`/`SetConsumed`/`Is*LockOn` |
| 返回值 | ArkUI_UIInputEvent、字段值、void 或 ArkUI_ErrorCode |
| 开放范围 | Public |
| 错误码 | `ARKUI_ERROR_CODE_NO_ERROR`、`ARKUI_ERROR_CODE_PARAM_INVALID`、`ARKUI_ERROR_CODE_BUFFER_SIZE_NOT_ENOUGH`、latest status |
| 关联 AC | AC-4.1~4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | const ArkUI_UIInputEvent* | 是 | 无 | 必须为 `C_KEY_EVENT_ID` 且 inner event 非空 |
| state | bool* | Lock getter 必填 | 无 | 必须非空 |
| pressedKeyCodes | int32_t* | GetPressedKeys 必填 | 无 | 调用方分配，容量由 `*length` 给出 |
| length | int32_t* | GetPressedKeys 必填 | 无 | 容量不足返回 buffer error |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 NODE_ON_KEY_EVENT | 可读取完整字段并设置消费/传播 | AC-4.1~4.4 |
| 2 | null/错误事件类型 | 返回 sentinel 或参数错误 | AC-4.5, AC-4.6 |
| 3 | pressed key 缓冲不足 | 返回 BUFFER_SIZE_NOT_ENOUGH | AC-4.7 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文固化当前实现，不修改公开行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic API 7；Native KeyEvent API 14；Static API 23。
- **API 版本号策略:** 按 canonical SDK 的 `@since` 记录字段和签名演进；当前仓库最高观察到 API 26 的 CANCEL/Static Lock 扩展。

| 通道 | 版本边界 | 行为差异 |
|------|----------|----------|
| Dynamic | API 7 | void `onKeyEvent` 与基础 KeyEvent |
| Dynamic | API 10/12/14/15/19/26 | intention/modifier/unicode/boolean callback/Lock/CANCEL 依次开放 |
| Native | API 14/17/19/20 | 基础 getter 与消费、modifier、Lock、latest status 依次开放 |
| Static | API 23/26 | API 23 提供 onKeyEvent 与主要字段，API 26 增加 Lock 与 CANCEL |

兼容性风险：

1. SDK optional Unicode/Lock 字段在当前 Dynamic/Static 实现中通常始终创建并填 `0/false`（`arkts_native_frame_node_bridge.cpp:1465`、`key_event_accessor.cpp:171`）。
2. 实现额外接受 `Fn` 修饰键，但 SDK 仅承诺 Ctrl/Alt/Shift（`arkts_utils.cpp:3889`；`common.d.ts:12810`）。
3. ArkTS CANCEL=3、C CLICK=3、内部 CANCEL=4，禁止裸数值互转（`native_key_event.h:387`；`key_code.h:442`）。
4. Native Unicode 头文件限制 0x21~0x7E，但实现直接返回任意 `uint32_t`（`native_key_event.h:539`；`key_event_impl.cpp:170`）。
5. `NODE_ON_KEY_EVENT` 头文件注释称 union 为 `ArkUI_NodeComponentEvent`，实际桥接与测试通过 `ArkUI_UIInputEvent` 获取（`native_node.h:10227`；`native_key_event_test.cpp:160`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 焦点链约束 | 普通按键事件从 last FocusView 的 entry FrameNode 进入，仅沿当前焦点链处理 | AC-1.1~1.4 |
| 同步消费约束 | 平台输入经 UI 线程同步返回 bool 消费结果 | AC-3.1~3.5 |
| 内外 handler 约束 | 内部和用户 handler 均执行，再合并结果 | AC-1.5 |
| SDK 契约优先 | 外部 API 以 canonical SDK/Native 头文件为契约，源码扩展仅记录风险 | AC-2.1~2.4, AC-5.2~5.4 |
| 显式枚举转换 | 跨 Dynamic/Static/Native/内部层必须显式转换动作类型 | AC-5.1 |
| Feat 边界 | PreIME、自定义 Dispatch 和 keyboardShortcut 不进入本 Feat | 全部 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 无新增公开性能指标；按键回调在现有同步输入链中完成 | 集成测试/Trace | `ace_container.cpp:1437` |
| 功耗 | 无新增后台任务、定时器或轮询 | 源码审查 | 主调用链 |
| 内存 | 回调不应持有 Bridge 创建的临时 KeyEventInfo 地址 | 源码审查 | `js_view_abstract.cpp:9634` |
| 安全 | Native getter 对 null/错误事件类型返回错误状态，不越过公开场景读取 | Level0 UT | `key_event_impl.cpp:27` |
| 可靠性 | Focus WeakPtr 失效或无 entry FrameNode 时返回未消费 | 单测/源码审查 | `key_event_manager.cpp:676` |
| 可测试性 | 每个消费、焦点、字段和 Native 错误边界均映射到 UT 或源码审查 | 追溯检查 | VM-1~VM-7 |
| 自动化维测 | 沿用 ACE_FOCUS 日志与 latest status | 日志/错误状态检查 | `focus_event_handler.cpp:109`、`ui_input_event.cpp` |
| 定界定位 | 通过 key code/action、节点 tag/id 和消费结果日志定位 | 日志检查 | `focus_event_handler.cpp:396` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 外接键盘事件进入相同焦点链 | 需要组件获得当前焦点 | 外接键盘集成测试 | `mmi_event_convertor.cpp:867` |
| 平板 | 与手机无框架语义差异 | 多窗口下按实例 last FocusView 分发 | 多窗口集成测试 | `key_event_manager.cpp:676` |
| 折叠屏 | 折叠状态不改变 KeyEvent 模型 | 焦点切换后使用新的 entry FocusView | 焦点切换测试 | `key_event_manager.cpp:678` |
| 手柄设备 | source 映射为 JOYSTICK | Dynamic API 15+ 才公开 JOYSTICK | 手柄集成测试 | `mmi_event_convertor.cpp:899` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本 Feat 不改变无障碍语义，但键盘焦点与无障碍焦点可能共享组件状态，需避免把二者等同 | 焦点链分发 |
| 大字体 | 否 | 事件模型不依赖字体缩放 | N/A |
| 深色模式 | 否 | 事件模型不依赖主题颜色；主题仅可能影响后续默认焦点 click 条件 | AC-1.6 |
| 多窗口/分屏 | 是 | 每个 Pipeline/实例按自身 FocusManager 的 last FocusView 分发 | AC-1.2 |
| 多用户 | 否 | 无用户级持久化状态 | N/A |
| 版本升级 | 是 | 按 API 7~26 字段与签名演进保持兼容 | AC-2.1~2.4 |
| 生态兼容 | 是 | ArkTS/C 枚举和 optional 字段差异不得被下游按实现细节固化 | AC-5.1~5.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 按键事件模型与基础回调

  Scenario: 当前焦点子节点消费事件
    Given 父 Scope 与当前焦点子节点均注册按键处理
    When 子节点收到按键并返回 true
    Then 子节点和其同节点用户回调按规则执行
    And 父 Scope 不再处理该事件

  Scenario: stopPropagation 独立消费
    Given 当前焦点节点注册 onKeyEvent
    When 回调调用 stopPropagation 并返回 false
    Then 当前节点返回已消费
    And 祖先焦点 Scope 不再收到该事件

  Scenario: 非 boolean 返回值
    Given Dynamic onKeyEvent 回调已注册
    When 回调返回非 boolean 且未调用 stopPropagation
    Then Bridge 将用户回调消费结果按 false 处理

  Scenario: 无当前焦点
    Given 节点未处于 currentFocus 或 entry FocusView 不存在
    When 系统分发普通按键事件
    Then 用户 onKeyEvent 不触发
    And 分发结果为未消费

  Scenario: Native 无效事件参数
    Given Native getter 收到 null 或非 C key event
    When 读取按键字段
    Then 返回该 getter 的 sentinel
    And latest status 为参数错误

  Scenario Outline: API 版本字段演进
    Given 使用 <通道> 的 <版本>
    When 接收 KeyEvent
    Then <字段能力> 可按 SDK 契约使用

    Examples:
      | 通道 | 版本 | 字段能力 |
      | Dynamic | API 7 | 基础字段 |
      | Dynamic | API 12 | getModifierKeyState |
      | Dynamic | API 19 | Lock 状态 |
      | Static | API 23 | 基础及主要扩展字段 |
      | Static | API 26 | Lock 状态和 CANCEL |
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则和验证方式
- [x] 每条规则通过可复现、可观测、边界值、关联 AC、无冲突检查
- [x] 外部 API 已与 canonical SDK 和 Native 头文件核对
- [x] SDK/源码偏差已显式进入兼容性风险

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "KeyEvent onKeyEvent FocusEventHandler KeyEventManager focus chain consumption"
  - repo: "openharmony/arkui_ace_engine"
    query: "NODE_ON_KEY_EVENT native_key_event stopPropagation isConsumed modifier lock"
  - repo: "openharmony/interface_sdk-js"
    query: "CommonMethod onKeyEvent KeyEvent KeyType KeySource API version"
```

**关键文档：** `specs/04-common-capability/04-common-events/02-key-events/design.md`、`interfaces/native/native_key_event.h`、`interface/sdk-js/api/@internal/component/ets/common.d.ts`
