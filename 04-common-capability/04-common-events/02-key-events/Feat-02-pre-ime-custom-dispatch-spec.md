# 特性规格

> Func-04-04-02-Feat-02 前置拦截与自定义分发：固化 ArkTS Dynamic/Static、Native 节点事件的 PreIME、自定义按键分发与主动重分发能力，以及消费、传播、焦点、事件来源和重入边界。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 前置拦截与自定义分发 |
| 特性编号 | Func-04-04-02-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 12~26、Native API 14~20+、Static API 23~26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | PreIME 规格基线 | 补录 `onKeyPreIme`、`NODE_ON_KEY_PRE_IME` 的前置执行顺序、消费聚合和祖先传播语义 |
| ADDED | 自定义分发规格基线 | 补录 `onKeyEventDispatch`、`NODE_DISPATCH_KEY_EVENT` 替代节点默认子分发路径的行为 |
| ADDED | 主动分发规格基线 | 补录 Dynamic/Static `UIContext.dispatchKeyEvent` 与 `OH_ArkUI_KeyEvent_Dispatch` 的目标、事件来源、返回值和错误边界 |
| ADDED | 跨通道风险基线 | 记录事件字段复制、时间戳单位、重入、Native scenario mask、文档与实现偏差，不修改产品代码 |

不包含：Feat-01 已固化的普通 `onKeyEvent`/`KeyEvent` 基础模型；`keyboardShortcut` 的匹配和注册实现（属于 Func-04-04-04），本文只记录其位于 PreIME 后续阶段；组件专有按键逻辑。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/02-key-events/design.md` | 增量合并 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:21153`、`api/@ohos.arkui.UIContext.d.ts:5533` | 已核验 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets:12145`、`api/@ohos.arkui.UIContext.static.d.ets:4010` | 已核验 |
| Native API | `interfaces/native/native_node.h:10233`、`:10259`、`interfaces/native/native_key_event.h:521`、`:560` | 已核验 |
| 核心实现 | `frameworks/core/common/key_event_manager.cpp:553`、`frameworks/core/components_ng/event/focus_event_handler.cpp:84` | 已核验 |
| Bridge 实现 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:9647`、`frameworks/core/interfaces/native/implementation/iui_context_accessor.cpp:533` | 已核验 |

## 用户故事

### US-1: 在输入法和普通按键处理前拦截事件

**作为** ArkUI 应用开发者，
**我想要** 在组件获得焦点后通过 PreIME 回调优先观察和消费按键，
**以便** 在输入法、组合快捷键和普通按键回调之前决定事件是否继续。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `KeyEvent.isPreIme` 为 true 且当前焦点链节点注册 `onKeyPreIme` THEN 回调在 `keyboardShortcut`、输入法事件、自定义 Dispatch 和普通 `onKeyEvent` 之前执行 | 正常 |
| AC-1.2 | WHEN 任一 PreIME 回调返回 true THEN 本次分发的全局消费状态变为 true 且保持 true，后续节点返回 false 不得清除 | 正常 |
| AC-1.3 | WHEN PreIME 回调返回 true 但未调用 `stopPropagation()` THEN 事件仍可沿 PreIME 焦点祖先链继续传播，最终整体结果为已消费 | 边界 |
| AC-1.4 | WHEN PreIME 回调返回 false 但调用 `stopPropagation()` THEN 停止向祖先传播，但全局消费状态不因该调用自动变为 true | 边界 |
| AC-1.5 | WHEN 所有 PreIME 回调均未消费且未停止传播 THEN 后续进入组件组合键阶段；若 Web 为当前焦点则当前实现跳过该阶段 | 边界 |

### US-2: 接管组件节点的子级按键分发

**作为** 组件或容器开发者，
**我想要** 通过 `onKeyEventDispatch` 自定义按键应发送给哪个子节点，
**以便** 替代框架默认的当前焦点子链分发策略。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 非 PreIME 按键到达当前焦点节点且已注册 `onKeyEventDispatch` THEN 框架只调用该回调，不再执行该节点默认 Scope 子分发、节点普通 handler 或默认焦点行为 | 正常 |
| AC-2.2 | WHEN 自定义 Dispatch 回调返回 false THEN 当前节点返回未消费，但仍不恢复本次节点的默认子分发路径 | 边界 |
| AC-2.3 | WHEN 自定义 Dispatch 回调返回 true THEN 当前节点返回已消费，并停止祖先焦点链继续处理 | 正常 |
| AC-2.4 | WHEN 自定义 Dispatch 回调调用 `stopPropagation()` 但返回 false THEN核心消费结果仍为 false，因为该路径只读取 callback boolean | 边界 |
| AC-2.5 | WHEN 事件 `isPreIme` 为 true THEN 即使节点注册了 `onKeyEventDispatch` 也不进入自定义 Dispatch，而按 PreIME 链处理 | 边界 |

### US-3: 将已有 KeyEvent 主动发送到指定节点

**作为** ArkUI 应用开发者，
**我想要** 通过 `UIContext.dispatchKeyEvent` 将正在处理的 KeyEvent 发送给指定 FrameNode，
**以便** 在自定义 Dispatch 回调中构建明确的同步转发链。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN node id 或 inspector key 可解析为 FrameNode、目标存在 FocusHub 且目标为当前焦点 THEN 主动分发同步调用目标 `FocusHub::HandleEvent` 并返回 boolean 消费结果 | 正常 |
| AC-3.2 | WHEN 目标节点不存在、没有可用 FocusHub、事件无效或目标不是当前焦点 THEN Dynamic/Static 主动分发返回 false 或 Dynamic Bridge 在无返回值路径结束，且不进入全局事件预处理 | 异常 |
| AC-3.3 | WHEN Dynamic 传入由现有回调产生并绑定 `KeyEventInfo` 的对象 THEN 从该对象复制公开按键字段后分发 | 正常 |
| AC-3.4 | WHEN Dynamic 传入普通对象且字段类型可解析 THEN 当前实现仍按属性构造内部 KeyEvent；其中 `timestamp` 数值按毫秒构造，而 SDK KeyEvent 将 Dynamic 时间戳声明为纳秒 | 边界 |
| AC-3.5 | WHEN Static 传入没有底层 `EventInfo` 的新建事件对象 THEN accessor 返回 false，不支持将该对象作为可分发 KeyEvent | 异常 |
| AC-3.6 | WHEN 主动分发已有 KeyEvent THEN复制字段不包含 `isPreIme`、`isRedispatch`、已消费或传播状态；Static/Native 还不保证复制 Dynamic 普通对象可填写的全部字段 | 边界 |
| AC-3.7 | WHEN 主动分发目标与当前自定义 Dispatch 节点形成同步回路 THEN 当前实现没有递归保护，允许同步重入，调用方必须避免同节点或环形转发 | 边界 |

### US-4: 在 Native 节点使用 PreIME 和自定义分发

**作为** Native ArkUI 开发者，
**我想要** 注册 Native PreIME/Dispatch 事件并转发已有按键事件，
**以便** 在 C API 组件中实现与 ArkTS 对应的处理链。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API 14+ 聚焦节点注册 `NODE_ON_KEY_PRE_IME` THEN通过 `OH_ArkUI_NodeEvent_GetInputEvent` 获取 C key event，并用 `OH_ArkUI_KeyEvent_SetConsumed` 与 `StopPropagation` 分别控制消费和祖先传播 | 正常 |
| AC-4.2 | WHEN API 15+ 聚焦节点注册 `NODE_DISPATCH_KEY_EVENT` THEN callback 替代该节点默认子分发，并以 `isConsumed` 作为核心返回结果 | 正常 |
| AC-4.3 | WHEN Native Dispatch callback 设置 `stopPropagation` 但未设置 `isConsumed` THEN Bridge 会回写传播字段，但自定义 Dispatch 核心仍忽略该字段 | 边界 |
| AC-4.4 | WHEN API 15+ 调用 `OH_ArkUI_KeyEvent_Dispatch` 且 node/event/inner event 有效 THEN同步把复制后的 KeyEvent 发送给目标节点，公开 API 返回类型为 void | 正常 |
| AC-4.5 | WHEN Native 主动分发的 node、event、inner event 或 event type 无效 THEN latest status 报告参数错误，且不触发目标回调 | 异常 |
| AC-4.6 | WHEN Native 调用方持有的事件不是从现有 NodeEvent callback 获得 THEN公共 API 没有 KeyEvent 构造或克隆接口可建立等价合法事件，规格不保证该调用成功 | 边界 |
| AC-4.7 | WHEN Native callback 通过文档声明的 `ArkUI_NodeComponentEvent` 路径读取 PreIME/Dispatch 数据 THEN无法获得真实 key input；实际实现要求 `OH_ArkUI_NodeEvent_GetInputEvent` | 异常 |

### US-5: 保持跨通道行为可解释且可定界

**作为** 框架维护者，
**我想要** 明确 Dynamic、Static、Native 的版本、字段和风险差异，
**以便** 防止应用依赖未承诺的重分发状态或未初始化控制字段。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 比较版本开放范围 THEN Dynamic PreIME 自 API 12、Dynamic Dispatch 自 API 15、Native PreIME 自 API 14、Native Dispatch 自 API 15、Static 三项能力自 API 23 可用 | 正常 |
| AC-5.2 | WHEN `OH_ArkUI_KeyEvent_SetConsumed` 用于 PreIME 或 Dispatch callback 事件 THEN字段可能被修改，但其 scenario mask 仅声明 `NODE_ON_KEY_EVENT`，latest status 可报告不支持 | 边界 |
| AC-5.3 | WHEN Native PreIME/Dispatch Bridge 构造栈事件 THEN `isConsumed` 和 `stopPropagation` 未显式初始化却在 callback 后读取，规格不得声明默认 false | 边界 |
| AC-5.4 | WHEN Web 重分发事件进入 `KeyEventManager::ReDispatch` THEN `isRedispatch` 被设置但后续仍可进入目标节点自定义 Dispatch，当前实现不提供防环保证 | 边界 |
| AC-5.5 | WHEN评估现有测试 THEN核心自定义 Dispatch 有 true/false/手工转发覆盖，Native 主动 Dispatch 主要覆盖空指针和错误事件，合法成功链覆盖不足 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-5 | 已有实现 | 核心源码/焦点单测 | `key_event_manager.cpp:607`；`focus_event_handler.cpp:278` |
| AC-2.1~2.5 | R-6~R-10 | 已有实现 | focus_core UT/源码审查 | `focus_event_handler.cpp:84`、`:107`；`focus_hub_test_ng_new_two.cpp:862` |
| AC-3.1~3.7 | R-11~R-17 | 已有实现 | Dynamic/Static Bridge 审查 | `js_view_abstract.cpp:9766`；`iui_context_accessor.cpp:533`；`key_event.cpp:202` |
| AC-4.1~4.7 | R-18~R-24 | 已有实现 | Native UT/头文件审查 | `native_node.h:10233`、`:10259`；`key_event_impl.cpp:216` |
| AC-5.1~5.5 | R-25~R-29 | 已有实现 | 版本/风险/测试审查 | `common.d.ts:21153`；`ui_input_event_impl.h:58`；`native_key_event_test.cpp:469` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `event.isPreIme == true` | `KeyEventManager` 先将事件发送到当前 entry FocusView 的焦点链 | 后续普通按键管线暂不执行 | AC-1.1 |
| R-2 | 行为 | PreIME callback 返回 true | 调用 `SetIsKeyConsumed(true)`，本次分发消费状态保持 true | 后续 false 不清除 sticky 状态 | AC-1.2 |
| R-3 | 边界 | PreIME callback 返回 true，`stopPropagation == false` | 继续向焦点祖先传播 PreIME | 最终 `DispatchKeyEventNG` 仍返回已消费 | AC-1.3 |
| R-4 | 边界 | PreIME callback 返回 false，`stopPropagation == true` | 当前焦点链停止向祖先传播 | 不等同于设置全局消费 true | AC-1.4 |
| R-5 | 行为 | PreIME 焦点链未处理且未消费 | 进入 `DispatchKeyboardShortcut`；Web 当前焦点时跳过 | 组合键详细语义不在本 FuncID | AC-1.5 |
| R-6 | 行为 | 非 PreIME 事件、当前焦点节点存在 Dispatch callback | 在 Scope/NODE 默认处理前调用自定义 Dispatch | 回调存在即替代当前节点默认路径 | AC-2.1 |
| R-7 | 边界 | Dispatch callback 返回 false | 当前节点返回 false | 不回退执行该节点默认子分发 | AC-2.2 |
| R-8 | 行为 | Dispatch callback 返回 true | 当前节点消费事件 | 祖先焦点链停止 | AC-2.3 |
| R-9 | 边界 | Dispatch callback 仅调用 `stopPropagation()` | Bridge 可回写字段，核心仍仅返回 callback boolean | 与普通 `onKeyEvent` 语义不同 | AC-2.4, AC-4.3 |
| R-10 | 边界 | `event.isPreIme == true` | `HasCustomKeyEventDispatch` 返回 false | 由 PreIME 专用路径处理 | AC-2.5 |
| R-11 | 行为 | node 可解析、FocusHub 存在、事件有效且目标当前聚焦 | 直接同步调用目标 `FocusHub::HandleEvent` | 不经 EventManager/KeyEventManager | AC-3.1 |
| R-12 | 异常 | node 无法解析、FocusHub/事件为空或目标未聚焦 | 返回 false或结束调用，不触发有效分发 | Dynamic void 早退路径不统一设置返回值 | AC-3.2 |
| R-13 | 行为 | Dynamic event 对象绑定现有 `KeyEventInfo` | `ParseKeyEvent` 复制公开字段到新内部 KeyEvent | 不复制内部 flags | AC-3.3, AC-3.6 |
| R-14 | 边界 | Dynamic event 是未绑定 `KeyEventInfo` 的普通对象 | 按属性解析数字/字符串/数组字段 | 当前实现接受 SDK 未承诺的新对象 | AC-3.4 |
| R-15 | 边界 | Dynamic 普通对象含 `timestamp = N` | 以 `milliseconds(N)` 构造内部时间点 | SDK Dynamic 契约声明纳秒 | AC-3.4 |
| R-16 | 异常 | Static event 没有底层 `EventInfo` | accessor 返回 false | 仅既有回调事件可转发 | AC-3.5 |
| R-17 | 边界 | 主动分发到当前 Dispatch 回调节点或形成环 | 同步再次进入 callback | 无递归深度/visited-node 保护 | AC-3.7 |
| R-18 | 行为 | Native 注册 `NODE_ON_KEY_PRE_IME` | 生成 `KEY_INPUT_EVENT/ON_KEY_PREIME`，同步发送并回写控制字段 | API 14+ | AC-4.1 |
| R-19 | 行为 | Native 注册 `NODE_DISPATCH_KEY_EVENT` | 生成 `KEY_INPUT_EVENT/ON_KEY_DISPATCH`，`isConsumed` 成为 callback 返回值 | API 15+ | AC-4.2 |
| R-20 | 行为 | Native 调用 `OH_ArkUI_KeyEvent_Dispatch` 且参数有效 | 转为内部 KeyEvent 并直接调用目标节点 `HandleEvent` | API 返回 void，状态从 latest status 获取 | AC-4.4 |
| R-21 | 异常 | Native Dispatch node/event/inner event 无效或类型非 C key event | latest status 为参数错误 | 不调用目标 FocusHub | AC-4.5 |
| R-22 | 边界 | Native 调用方需要创建可分发 KeyEvent | 公共头文件没有 constructor/clone | 实际来源应为同步 NodeEvent callback | AC-4.6 |
| R-23 | 异常 | 按 Native NodeEvent 注释读取 `ArkUI_NodeComponentEvent` | 该路径与真实 key input union 不一致 | 应改用 `OH_ArkUI_NodeEvent_GetInputEvent` | AC-4.7 |
| R-24 | 边界 | Native 主动 Dispatch 复制 ArkUIKeyEvent | 仅复制 type/code/text/device/timestamp/pressed/intention/lock 等实现字段 | 不复制 `isPreIme`、modifier/source/消费传播等全部状态 | AC-3.6, AC-4.4 |
| R-25 | 行为 | API level 达到各通道 `@since` | 按 Dynamic 12/15、Native 14/15、Static 23 开放能力 | 不向低版本推导可用性 | AC-5.1 |
| R-26 | 边界 | PreIME/Dispatch 事件调用 `SetConsumed` | 写入 `isConsumed` 后，status 宏仍可能覆盖为 scenario 不支持 | scenario 检查只传 `S_NODE_ON_KEY_EVENT` | AC-5.2 |
| R-27 | 边界 | Native Bridge 创建 `ArkUINodeEvent event;` | 回调后读取 `isConsumed/stopPropagation` | 两字段未显式初始化，默认值不形成契约 | AC-5.3 |
| R-28 | 边界 | Web `ReDispatch` 设置 `isRedispatch = true` | 重分发仍进入焦点/自定义 Dispatch | 主动复制又会丢失 `isRedispatch` | AC-5.4 |
| R-29 | 边界 | 评估现有测试集合 | 核心分发语义有 UT，Native 合法主动分发需补强 | 文档任务不新增产品测试 | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.5, R-1~R-5 | `key_event_manager.cpp`、PreIME focus_core UT | 顺序、sticky 消费、祖先传播、组合键边界 |
| VM-2 | AC-2.1~2.5, R-6~R-10 | `focus_hub_test_ng_new_two.cpp:862` | callback true/false、替代默认路径、PreIME 排除 |
| VM-3 | AC-3.1~3.7, R-11~R-17 | Dynamic/Static accessor 审查与定向 UT | 目标焦点、普通对象、已有事件、字段复制和重入 |
| VM-4 | AC-4.1~4.7, R-18~R-24 | `native_key_event_test.cpp`、Level0 C API UT | NodeEvent 获取、void Dispatch、错误状态、字段缺失 |
| VM-5 | AC-5.1~5.5, R-25~R-29 | SDK/头文件/实现差异审查 | `@since`、scenario mask、未初始化字段、覆盖缺口 |

## API 变更分析

> 本次为存量能力规格补录，不新增、变更或废弃公开 API。下表记录当前公开 API 基线和完整开放版本。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `onKeyPreIme(Callback<KeyEvent, boolean>)` | Public, Dynamic API 12+ | PreIME callback | 当前组件 | N/A | 输入法和后续按键回调前拦截 | AC-1.1~1.5 |
| `onKeyEventDispatch(Callback<KeyEvent, boolean>)` | Public, Dynamic API 15+ | 自定义分发 callback | 当前组件 | N/A | 替代节点默认子分发 | AC-2.1~2.5 |
| `UIContext.dispatchKeyEvent(number \| string, KeyEvent)` | Public, Dynamic API 15+ | 节点标识、已有事件 | boolean | N/A | 主动同步分发 | AC-3.1~3.7 |
| `onKeyPreIme(... \| undefined)` | Public, Static API 23+ | callback 或 undefined | 当前组件 | N/A | 静态 ArkTS PreIME | AC-1.1~1.5 |
| `onKeyEventDispatch(... \| undefined)` | Public, Static API 23+ | callback 或 undefined | 当前组件 | N/A | 静态 ArkTS 自定义分发 | AC-2.1~2.5 |
| `UIContext.dispatchKeyEvent(int \| string, KeyEvent)` | Public, Static API 23+ | 节点标识、已有事件 | boolean | N/A | 静态 ArkTS 主动同步分发 | AC-3.1, AC-3.5~3.7 |
| `NODE_ON_KEY_PRE_IME` | Public, Native API 14+ | Node event listener | 同步事件回调 | latest status | Native PreIME | AC-4.1 |
| `NODE_DISPATCH_KEY_EVENT` | Public, Native API 15+ | Node event listener | 同步事件回调 | latest status | Native 自定义分发 | AC-4.2, AC-4.3 |
| `OH_ArkUI_KeyEvent_Dispatch` | Public, Native API 15+ | node、已有 C key event | void | latest status | Native 主动分发 | AC-4.4~4.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| N/A | 无 | 本次仅补录现有能力 | 无迁移要求 | 全部 |

## 接口规格

### 接口定义

**ArkTS `onKeyPreIme`**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `onKeyPreIme(event: Callback<KeyEvent, boolean>): T`；Static: `onKeyPreIme(event: Callback<KeyEvent, boolean> \| undefined): this` |
| 返回值 | 当前组件，用于链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | Callback/undefined | Dynamic 是；Static 可 undefined | 无 | 仅 `isPreIme` 事件进入该路径 |
| callback return | boolean | 是 | false | true 写入 sticky 消费状态；与 `stopPropagation` 独立 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | return true，未 stop | 继续祖先 PreIME，整体已消费 | AC-1.2, AC-1.3 |
| 2 | return false，stop | 停止祖先 PreIME，整体不因 stop 自动消费 | AC-1.4 |
| 3 | 全链未处理 | 进入后续组合键阶段 | AC-1.5 |

**ArkTS `onKeyEventDispatch`**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `onKeyEventDispatch(event: Callback<KeyEvent, boolean>): T`；Static: `onKeyEventDispatch(event: Callback<KeyEvent, boolean> \| undefined): this` |
| 返回值 | 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | Callback/undefined | Dynamic 是；Static 可 undefined | 无 | 仅非 PreIME 且当前节点当前聚焦时触发 |
| callback return | boolean | 是 | false | 是本路径唯一核心消费结果 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | callback 已注册 | 替代当前节点默认分发 | AC-2.1 |
| 2 | callback false | 返回未消费，不恢复默认分发 | AC-2.2 |
| 3 | callback 内主动发往子节点 | 子节点结果可作为 callback 返回值 | AC-2.3 |

**ArkTS `UIContext.dispatchKeyEvent`**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `dispatchKeyEvent(node: number \| string, event: KeyEvent): boolean`；Static: `dispatchKeyEvent(node: int \| string, event: KeyEvent): boolean` |
| 返回值 | boolean — 目标 FocusHub 的同步消费结果 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | number/int/string | 是 | 无 | 必须解析为当前聚焦 FrameNode |
| event | KeyEvent | 是 | 无 | SDK 仅承诺已有 KeyEvent；Static 必须带底层 EventInfo |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效目标和已有事件 | 同步调用目标 FocusHub | AC-3.1, AC-3.3 |
| 2 | Dynamic 普通对象 | 当前实现按属性解析，属于契约外扩展 | AC-3.4 |
| 3 | Static 新建事件/目标失焦 | 返回 false | AC-3.2, AC-3.5 |
| 4 | 同节点或环形转发 | 同步重入，无递归保护 | AC-3.7 |

**Native PreIME、Dispatch 与主动分发**

| 属性 | 值 |
|------|-----|
| 函数签名 | `NODE_ON_KEY_PRE_IME`；`NODE_DISPATCH_KEY_EVENT`；`void OH_ArkUI_KeyEvent_Dispatch(ArkUI_NodeHandle, const ArkUI_UIInputEvent*)` |
| 返回值 | NodeEvent 同步回调；主动 Dispatch 为 void |
| 开放范围 | Public |
| 错误码 | latest status：`ARKUI_ERROR_CODE_NO_ERROR`、`ARKUI_ERROR_CODE_PARAM_INVALID`、`ARKUI_ERROR_INPUT_EVENT_TYPE_NOT_SUPPORT` |
| 关联 AC | AC-4.1~4.7, AC-5.2~5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | ArkUI_NodeHandle | Dispatch 必填 | 无 | 必须指向有效且当前聚焦节点 |
| event | ArkUI_UIInputEvent* | 是 | 无 | 必须为 C key event 且 inner event 非空，实际来自同步 NodeEvent callback |
| isConsumed | bool | callback 可设置 | 未保证 | PreIME/Dispatch 使用时存在 scenario status 偏差 |
| stopPropagation | bool | callback 可设置 | 未保证 | PreIME 核心使用；Dispatch 核心忽略 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 PreIME callback | 分别回写消费与传播 | AC-4.1 |
| 2 | 有效 Dispatch callback | `isConsumed` 决定返回 | AC-4.2, AC-4.3 |
| 3 | 主动 Dispatch 无效参数 | latest status 参数错误 | AC-4.5 |
| 4 | 按 NodeComponentEvent 注释取值 | 与实现不符，应走 InputEvent getter | AC-4.7 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文固化现有实现，不改变 PreIME、Dispatch 或组合键顺序。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic PreIME API 12，Dynamic Dispatch API 15，Native PreIME API 14，Native Dispatch API 15，Static API 23。
- **API 版本号策略:** 严格按 canonical SDK 和 Native 头文件 `@since`；API 26 未发现本 Feature 签名变更。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 焦点约束 | PreIME、Custom Dispatch、Active Dispatch 均依赖当前焦点节点，不是任意节点广播 | AC-1.1, AC-2.1, AC-3.1~3.2 |
| 分层约束 | 平台输入 PreIME 经 KeyEventManager；主动 Dispatch 直接进入 FocusHub，不得混写为同一入口 | AC-1.1, AC-3.1 |
| 消费/传播分离 | PreIME 的 boolean 与 stopPropagation 不得合并描述；Custom Dispatch 只以 boolean 为核心结果 | AC-1.2~1.4, AC-2.3~2.4 |
| 事件来源约束 | 公共契约只保证转发已有 KeyEvent，禁止把 Dynamic 普通对象解析写成跨通道保证 | AC-3.3~3.6, AC-4.6 |
| Native ABI 约束 | 不修改公开 enum、函数签名、返回类型或 struct layout | AC-4.1~4.7 |
| 重入约束 | 当前实现无递归保护，规格必须显式要求调用方避免环形转发 | AC-3.7, AC-5.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次处理为 UI 线程同步链，不新增异步排队；callback 不应执行阻塞操作 | 调用链审查/集成测试 | `focus_event_handler.cpp:107` |
| 功耗 | 无新增轮询、定时器或后台任务 | 源码审查 | 本次仅补录已有同步路径 |
| 内存 | 事件对象仅在同步回调期有效，不得跨回调保存 Native inner pointer | ASan/生命周期审查 | `node_common_modifier.cpp:12729` |
| 安全 | Native 空指针、错误事件类型必须定界；未初始化控制字段列为高风险 | 故障注入/Level0 UT | `key_event_impl.cpp:216` |
| 可靠性 | sticky consumed 不得由后续 false 清除；避免环形主动分发 | focus_core UT/重入测试 | `key_event_manager.cpp:581` |
| 可测试性 | 覆盖 PreIME 四组合、Dispatch true/false/stop、主动分发有效/无效/重入 | 单元测试矩阵 | `focus_hub_test_ng_new_two.cpp:862` |
| 自动化维测 | 无新增 telemetry | N/A | 本 Feature 无自动上报 |
| 定界定位 | 使用 ACE_FOCUS 日志区分 PreIME、Custom Dispatch、非当前焦点 | hilog 审查 | `focus_event_handler.cpp:107`、`:278` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 外接键盘或输入法场景触发 | 同一焦点和消费规则 | 真机键盘/输入法测试 | SDK SysCap |
| 平板 | 无框架语义差异 | 同一焦点和消费规则 | 外接键盘测试 | 共享实现 |
| 折叠屏 | 折叠状态不改变按键链 | 多窗口焦点仍按当前实例选择 | 折叠/分屏测试 | 共享 FocusManager |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 自定义分发可能改变默认焦点/激活行为，应用需保证替代逻辑可访问 | AC-2.1~2.3 |
| 大字体 | 否 | 无布局和字体处理 | N/A |
| 深色模式 | 否 | 无颜色和主题处理 | N/A |
| 多窗口/分屏 | 是 | node 必须属于当前 UI 实例并处于当前焦点 | AC-3.1~3.2 |
| 多用户 | 否 | 无用户数据和跨用户状态 | N/A |
| 版本升级 | 是 | 按各通道 `@since` 保持兼容，不向低版本回填 | AC-5.1 |
| 生态兼容 | 是 | Dynamic 普通对象解析、timestamp 单位和 Native status 偏差不可作为公共保证 | AC-3.4, AC-5.2~5.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 前置拦截与自定义分发
  作为 ArkUI 输入事件开发者
  我想要控制 PreIME、自定义分发和主动转发
  以便构建可预测的焦点按键链

  Scenario Outline: PreIME 消费与祖先传播相互独立
    Given 当前焦点子节点注册 onKeyPreIme
    And 父节点也注册 onKeyPreIme
    When 子节点回调返回 <ret> 并设置 stopPropagation 为 <stop>
    Then 父节点是否执行为 <parentCalled>
    And 本次 sticky 消费状态为 <consumed>

    Examples:
      | ret | stop | parentCalled | consumed |
      | true | false | true | true |
      | false | true | false | false |

  Scenario: 自定义 Dispatch 返回 false 不恢复默认子分发
    Given 当前焦点 Scope 注册 onKeyEventDispatch
    And 其焦点子节点注册 onKeyEvent
    When Dispatch callback 返回 false且不主动转发
    Then Scope 返回未消费
    And 子节点 onKeyEvent 不执行

  Scenario: 主动分发形成同步环
    Given 节点 A 与节点 B 的 Dispatch callback 互相调用 dispatchKeyEvent
    When A 收到一个非 PreIME KeyEvent
    Then 当前实现同步重入且没有递归保护
    And 应用必须移除环形转发才能恢复正常处理
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（“快速”“稳定”“尽可能”等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "onKeyPreIme sticky consumed stopPropagation FocusEventHandler KeyEventManager"
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "onKeyEventDispatch UIContext dispatchKeyEvent Native NODE_DISPATCH_KEY_EVENT"
  - repo: "OpenHarmony/interface_sdk-js"
    query: "KeyEvent onKeyPreIme onKeyEventDispatch dispatchKeyEvent API since"
```

**关键文档：** `specs/04-common-capability/04-common-events/02-key-events/design.md`；`interface/sdk-js/api/@internal/component/ets/common.d.ts`；`interfaces/native/native_key_event.h`。
