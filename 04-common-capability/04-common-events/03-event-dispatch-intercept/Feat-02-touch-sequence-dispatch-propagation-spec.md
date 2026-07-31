# 特性规格

> Func-04-04-03-Feat-02 触摸事件序列分发与传播控制：固化 NG 目标链的两阶段分发、`stopPropagation`/`preventDefault` 边界、VSync MOVE 批处理与历史点，以及真实/伪造 CANCEL 的清理语义。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 触摸事件序列分发与传播控制 |
| 特性编号 | Func-04-04-03-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7–26，Static API 23 起，C API 12 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 两阶段分发规格 | 补录逆序 Dispatch 与正序 Handle 的调用及中止语义 |
| ADDED | 传播控制规格 | 补录普通触摸、识别器、Interaction Event 的差异 |
| ADDED | MOVE 批处理与历史点规格 | 补录 VSync 消费、重采样、回退和 flush 行为 |
| ADDED | 序列恢复与清理规格 | 补录失败重发、真实/伪造 CANCEL 和局部目标移除 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/03-event-dispatch-intercept/design.md` | Baselined |
| Feat-01 | `Feat-01-hit-test-intercept-response-chain-spec.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核验 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets` | 已核验 |
| 核心实现 | `frameworks/core/common/event_manager.cpp`, `frameworks/core/components_ng/event/touch_event.cpp`, `frameworks/core/pipeline_ng/pipeline_context.cpp` | 已核验 |
| Native API | `interfaces/native/ui_input_event.h`, `interfaces/native/event/ui_input_event.cpp` | 已核验 |

---

## 用户故事

### US-1: 按两阶段顺序分发目标链

**作为** ArkUI 事件框架,
**我想要** 对已命中的目标链执行预分发和冒泡处理,
**以便** 扩展目标、原始触摸回调和手势识别器遵循确定的调用顺序。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 当前指针 ID 存在 `TouchTestResult` THEN 先按目标链逆序调用 `DispatchEvent` | 正常 |
| AC-1.2 | WHEN 全部 `DispatchEvent` 返回 true THEN 再按目标链正序调用 `HandleEvent` | 正常 |
| AC-1.3 | WHEN 任一 `DispatchEvent` 返回 false THEN 立即停止剩余预分发，并跳过整个 Handle 阶段 | 异常 |
| AC-1.4 | WHEN 使用内建 `TouchEventActuator` 或 `NGGestureRecognizer` THEN 其默认 `DispatchEvent` 返回 true，业务处理发生在 Handle 阶段 | 正常 |
| AC-1.5 | WHEN 当前指针 ID 不存在命中结果 THEN `DispatchTouchEvent` 返回 false，但仍检查 UP/CANCEL 的异常序列状态 | 异常 |

### US-2: 精确控制普通触摸传播

**作为** 应用开发者,
**我想要** 在 `onTouch` 中停止普通触摸冒泡或阻止组件默认行为,
**以便** 控制应用回调而不误伤手势识别器和其他事件通道。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `TouchEvent.stopPropagation()` 被调用 THEN 当前 `TouchEventActuator::HandleEvent` 返回 false，后续非识别器普通触摸 Handle 被跳过 | 正常 |
| AC-2.2 | WHEN普通触摸已经停止传播 THEN 所有命中的 `NGGestureRecognizer` 仍接收该事件并自行过滤 | 正常 |
| AC-2.3 | WHEN普通 Handle 已返回 false THEN 当前/后续目标的 Interaction Event 仍按独立的“一次成功回调”规则处理 | 边界 |
| AC-2.4 | WHEN `sendOnTouch=false` THEN 跳过所有非识别器普通 Handle 和 Interaction Event，但识别器继续处理 | 边界 |
| AC-2.5 | WHEN `TouchEvent.preventDefault()` 在支持组件 Hyperlink 的同步回调中调用 THEN 设置默认行为阻止状态，但不改变 `stopPropagation` 的冒泡判定 | 正常 |
| AC-2.6 | WHEN在不支持组件、异步调用或 Modifier 场景使用 Dynamic `preventDefault` THEN 按 SDK 契约抛 BusinessError 100017 或不支持该集成 | 异常 |

### US-3: 维持触摸序列和识别器恢复

**作为** ArkUI 事件框架,
**我想要** 对 DOWN/MOVE/UP/CANCEL 和异常序列维护一致状态,
**以便** 识别器失败、重复 DOWN 或缺失 DOWN 时能够恢复而不重复应用回调。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN分发 DOWN THEN 在正式处理前清理该 touch ID 的旧 GestureReferee 状态 | 正常 |
| AC-3.2 | WHEN单指 DOWN 首轮前无失败识别器、首轮后新出现失败且 Referee 未全部完成 THEN 强制清理识别器状态并以 `sendOnTouch=false` 重发一次 DOWN | 异常 |
| AC-3.3 | WHEN执行上述第二轮 DOWN THEN 不重复触发 ArkTS `onTouch` 或 Interaction Event | 正常 |
| AC-3.4 | WHEN同一 touch ID 重复收到真实 DOWN THEN 向旧链发送伪造 CANCEL，清理旧目标与仲裁状态后登记新 DOWN | 异常 |
| AC-3.5 | WHEN收到没有对应 DOWN 的真实 UP/CANCEL THEN 发送伪造 CANCEL 并强制清理 Referee/按下指针记录 | 异常 |

### US-4: 在 VSync 中批处理 MOVE 与历史点

**作为** 应用开发者,
**我想要** MOVE 回调与屏幕刷新节奏对齐并能够读取原始历史点,
**以便** 在平滑交互中兼顾最新位置和设备原始采样信息。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN VSync flush 开始 THEN 只消费时间戳不晚于 `vsyncTime - compensationValue` 的排队 MOVE，未来点保留在队列 | 边界 |
| AC-4.2 | WHEN同一批次包含同一指针的多个 MOVE THEN 最终每个指针 ID 生成一条待分发事件，其余原始点进入 history | 正常 |
| AC-4.3 | WHEN满足插值开关、目标时间和 display ID 一致等条件 THEN 分发重采样点并设置 `isInterpolated=true` | 正常 |
| AC-4.4 | WHEN重采样条件不满足或计算失败 THEN 分发本批该指针的最新原始点 | 异常 |
| AC-4.5 | WHEN回调事件为非注入场景的重采样 MOVE THEN `changedTouches` 可表示屏幕刷新率点，`touches` 保留设备上报率点，二者允许不同 | 边界 |
| AC-4.6 | WHEN调用 `getHistoricalPoints()` THEN 仅在 `onTouch` 同步回调的 TouchEvent 中读取历史点；单帧最后一点进入 onTouch，其余点作为历史点 | 边界 |
| AC-4.7 | WHEN收到任意非 MOVE 事件 THEN 清除该指针的跨帧 MOVE 历史缓存 | 正常 |

### US-5: 区分真实结束和内部取消

**作为** ArkUI 事件框架,
**我想要** 区分真实 UP/CANCEL 与内部伪造 CANCEL,
**以便** 在通知目标的同时避免提前终结仍在进行的真实序列。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN收到非伪造 UP/CANCEL THEN 清理 NG/旧 Referee scope、识别器状态、按下指针；`sendOnTouch=true` 时删除该 ID 的目标链 | 正常 |
| AC-5.2 | WHEN `isFalsified=true` 的 CANCEL/UP 被分发 THEN 跳过正式序列终结和 down-finger 删除 | 边界 |
| AC-5.3 | WHEN只移除一个目标 THEN 仅向该目标发送清空 history 的伪造 CANCEL，并从各 touch ID 的结果链删除该目标 | 正常 |
| AC-5.4 | WHEN拖拽 PULL_MOVE 转换为 CANCEL THEN 向相关目标分发取消并整体清理对应目标链和指针状态 | 正常 |
| AC-5.5 | WHEN触控笔策略拦截当前触摸 THEN 先清理当前 touch ID 的目标和 scope，再按现有按下指针执行内部取消通知 | 正常 |

### US-6: 保持 Dynamic、Static 与 Native 契约可追溯

**作为** 多范式 ArkUI 开发者,
**我想要** 传播控制和触摸数据字段遵循各通道真实版本与限制,
**以便** 跨版本迁移时识别实现差异和验证缺口。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN使用 Dynamic TouchEvent THEN `touches`、`changedTouches`、`stopPropagation` 自 API 7，timestamp 自 API 8，`getHistoricalPoints` 自 API 10，`preventDefault` 自 API 12 | 边界 |
| AC-6.2 | WHEN使用 Static TouchEvent THEN基础字段和方法自 API 23 开放，`getHistoricalPoints()` 在内部环境损坏时允许返回 undefined | 边界 |
| AC-6.3 | WHEN Dynamic Bridge 的 `changedTouches` 为空 THEN 当前实现可能不写 SDK 必填的 `type` 字段，规格将其声明为实现偏差 | 异常 |
| AC-6.4 | WHEN Static `TouchEventHandwritten` 构造事件 THEN 当前实现不承载 API 24 的 `eventHandleId`，不推断其存在 | 边界 |
| AC-6.5 | WHEN Native Node onTouch 回调结束 THEN当前路径只回写 `stopPropagation`，未回写 `preventDefault`；公开 PointerEvent SetPreventDefault 在 ace_engine 中未找到 | 边界 |
| AC-6.6 | WHEN调用 `OH_ArkUI_PointerEvent_SetStopPropagation` THEN touch/mouse/hover 事件写入布尔值；空 event 返回参数错误，其他事件类型返回不支持错误 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-5 | 已有实现 | EventManager 单测 | `event_manager.cpp:1121,1208,1528` |
| AC-2.1~2.6 | R-6~R-11 | 已有实现 | TouchEvent/Hyperlink 单测 + SDK 审查 | `touch_event.cpp:88`, `common.d.ts:11028` |
| AC-3.1~3.5 | R-12~R-16 | 已有实现 | EventManager 异常路径单测 | `event_manager.cpp:1024,1069,1381` |
| AC-4.1~4.7 | R-17~R-23 | 已有实现 | Pipeline/重采样单测 | `pipeline_context.cpp:4779`, `event_manager.cpp:2809` |
| AC-5.1~5.5 | R-24~R-28 | 已有实现 | EventManager 清理单测 | `event_manager.cpp:1263,1416,1559` |
| AC-6.1~6.6 | R-29~R-34 | 已有实现 | SDK/Bridge/C API 审查 | canonical SDK 与 Native 实现 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 目标链存在 | 逆序调用 DispatchEvent | 预分发方向与 Handle 相反 | AC-1.1 |
| R-2 | 行为 | 全部 DispatchEvent=true | 正序调用 HandleEvent | 进入业务处理阶段 | AC-1.2 |
| R-3 | 异常 | 任一 DispatchEvent=false | 中止预分发并跳过 Handle | 扩展目标协议能力 | AC-1.3 |
| R-4 | 行为 | 内建 TouchEventActuator/Recognizer | 默认 DispatchEvent=true | 普通业务不在预分发执行 | AC-1.4 |
| R-5 | 异常 | 当前 ID 无命中结果 | 返回 false，并调用 CheckUpEvent 修复状态 | 不调用任意目标 | AC-1.5 |
| R-6 | 行为 | onTouch 调用 stopPropagation | 当前普通 Handle 返回 false | 后续普通目标停止 | AC-2.1 |
| R-7 | 行为 | 普通传播已停止 | 识别器仍无条件 Handle | 识别器自行过滤额外事件 | AC-2.2 |
| R-8 | 边界 | 普通 Handle 返回 false | Interaction Event 独立寻找首个成功回调 | 不由 isStopTouchEvent 控制 | AC-2.3 |
| R-9 | 边界 | sendOnTouch=false | 仅识别器接收事件 | 原始与 Interaction 回调均跳过 | AC-2.4 |
| R-10 | 行为 | Hyperlink 同步 TouchEvent 调用 preventDefault | 仅设置默认行为阻止状态 | 不改变 stopPropagation | AC-2.5 |
| R-11 | 异常 | 非支持组件/异步/Modifier 调用 preventDefault | 按 SDK 抛 100017 或不提供集成 | Dynamic 契约 | AC-2.6 |
| R-12 | 行为 | DOWN 正式分发 | 清理该 ID 的旧 Referee 状态 | 不清理其他 ID | AC-3.1 |
| R-13 | 恢复 | 单指首轮 DOWN 新产生失败识别器 | 清理后以 sendOnTouch=false 重发一次 | 不适用于多指或已失败状态 | AC-3.2 |
| R-14 | 行为 | DOWN 恢复重发 | 不重复应用回调 | 识别器仍处理 | AC-3.3 |
| R-15 | 恢复 | 同 ID 重复 DOWN | CANCEL 旧链、强清并接受新 DOWN | 上报异常诊断 | AC-3.4 |
| R-16 | 恢复 | UP/CANCEL 无对应 DOWN | 伪造 CANCEL 并强清状态 | 上报异常诊断 | AC-3.5 |
| R-17 | 边界 | 点时间 <= vsync-compensation | 移入当前 flush 批次 | 未来点保留 | AC-4.1 |
| R-18 | 行为 | 同 ID 多个 MOVE | 压缩为一条分发事件，其余进 history | 每 ID 一条 | AC-4.2 |
| R-19 | 行为 | 插值条件全部满足 | 生成 isInterpolated 点 | display ID 必须一致 | AC-4.3 |
| R-20 | 恢复 | 插值不可用/失败 | 使用本批最新原始点 | 不丢失该 ID 的 MOVE | AC-4.4 |
| R-21 | 边界 | 非注入重采样事件 | changedTouches 与 touches 允许不同 | 两数组使用前判空 | AC-4.5 |
| R-22 | 边界 | onTouch 同步调用历史接口 | 返回本帧除最后回调点外的历史点 | API 10 起 | AC-4.6 |
| R-23 | 行为 | DOWN/UP/CANCEL 等非 MOVE 到达 | 清除跨帧 historyPointsById | 防止跨序列污染 | AC-4.7 |
| R-24 | 行为 | 非伪造 UP/CANCEL | 清理 scope、状态和指针；按 sendOnTouch 决定删链 | 正式序列结束 | AC-5.1 |
| R-25 | 边界 | isFalsified=true | 跳过正式终结 | 仅内部通知 | AC-5.2 |
| R-26 | 行为 | 删除单个 target | 向该 target 发无 history 的伪造 CANCEL 并删除 iterator | 其他目标和序列保留 | AC-5.3 |
| R-27 | 行为 | 拖拽 PULL_MOVE 触发取消 | 分发取消并整体清理相关链 | 粒度大于单目标移除 | AC-5.4 |
| R-28 | 行为 | Pen 策略拦截 | 清理当前 ID 后执行内部取消通知 | 受现有 downFinger 集合约束 | AC-5.5 |
| R-29 | 边界 | Dynamic API 版本检查 | 按 7/8/10/12 开放字段和方法 | 不提前暴露 | AC-6.1 |
| R-30 | 边界 | Static API 版本检查 | API 23 起开放，历史接口可返回 undefined | 静态类型契约 | AC-6.2 |
| R-31 | 异常 | Dynamic changedTouches 为空 | 当前 Bridge 可能缺少 type | 标记 SDK/实现偏差 | AC-6.3 |
| R-32 | 边界 | Static 事件构造 | 当前 TouchEventHandwritten 无 eventHandleId | 归 Feat-03 跟踪 handle 策略 | AC-6.4 |
| R-33 | 边界 | Native onTouch 回调结束 | 仅回写 stopPropagation | Pointer SetPreventDefault 未找到 | AC-6.5 |
| R-34 | 异常 | Native SetStopPropagation 参数/类型非法 | 返回 PARAM_INVALID 或 TYPE_NOT_SUPPORT | touch/mouse/hover 支持 | AC-6.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.5, R-1~R-5 | EventManager 单测/Mock Target | 两阶段方向、预分发中止、无链 |
| VM-2 | AC-2.1~2.6, R-6~R-11 | TouchEventActuator/Hyperlink 测试 | stopPropagation、Recognizer、preventDefault |
| VM-3 | AC-3.1~3.5, R-12~R-16 | 异常序列测试 | 单次重发、重复 DOWN、缺失 DOWN |
| VM-4 | AC-4.1~4.7, R-17~R-23 | Pipeline/Resample 测试 | VSync 截止、压缩、插值回退、history |
| VM-5 | AC-5.1~5.5, R-24~R-28 | 清理/拖拽/Pen/目标移除测试 | 真实与伪造取消粒度 |
| VM-6 | AC-6.1~6.6, R-29~R-34 | SDK/Bridge/C API 审查 | 版本和通道偏差 |

## API 变更分析

> 本次为已有能力补录，不新增或修改产品 API。下表记录现存接口契约。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|--------|
| `TouchEvent.stopPropagation` | Public | 无 | void | N/A | 停止后续普通触摸冒泡 | AC-2.1~2.4 |
| `TouchEvent.getHistoricalPoints` | Public | 无 | HistoricalPoint[] / Static 可 undefined | N/A | 获取当前帧历史触点 | AC-4.5~4.6 |
| `TouchEvent.preventDefault` | Public | 无 | void | BusinessError 100017 | 阻止 Hyperlink 默认行为 | AC-2.5~2.6 |
| `OH_ArkUI_PointerEvent_SetStopPropagation` | Public C API | event, bool | int32_t | PARAM_INVALID/TYPE_NOT_SUPPORT | 设置 PointerEvent 传播结果 | AC-6.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|--------|
| — | 无变更 | 本次仅补录存量行为 | 无需迁移 | 全部 |

## 接口规格

### 接口定义

**TouchEvent.stopPropagation**

| 属性 | 值 |
|------|-----|
| 函数签名 | `stopPropagation(): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 无 | — | — | 未停止 | 仅影响当前事件的后续普通触摸 Handle |

**行为场景索引**：SC-1、SC-2。

**TouchEvent.getHistoricalPoints**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `getHistoricalPoints(): Array<HistoricalPoint>`; Static: `getHistoricalPoints(): Array<HistoricalPoint> \| undefined` |
| 返回值 | 当前帧历史触点 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.5~4.7, AC-6.1~6.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 调用上下文 | onTouch 同步 TouchEvent | 是 | 空数组/Static 可 undefined | 不支持异步保存事件后调用 |

**行为场景索引**：SC-4。

**TouchEvent.preventDefault**

| 属性 | 值 |
|------|-----|
| 函数签名 | `preventDefault(): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | BusinessError 100017 |
| 关联 AC | AC-2.5~2.6, AC-6.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 调用组件 | Hyperlink | 是 | 未阻止 | Dynamic SDK 不支持其他组件、异步或 Modifier；Native Pointer setter 此代码在 ace_engine 中未找到 |

**行为场景索引**：SC-3。

**OH_ArkUI_PointerEvent_SetStopPropagation**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_PointerEvent_SetStopPropagation(const ArkUI_UIInputEvent* event, bool stopPropagation)` |
| 返回值 | 0 或 ArkUI 错误码 |
| 开放范围 | Public C API |
| 错误码 | PARAM_INVALID, INPUT_EVENT_TYPE_NOT_SUPPORT |
| 关联 AC | AC-6.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| event | ArkUI_UIInputEvent* | 是 | 无 | 支持 touch/mouse/hover；不能为空 |
| stopPropagation | bool | 是 | false | true 停止对应事件传播 |

**行为场景索引**：SC-2、SC-6。

## 兼容性声明

- **已有 API 行为变更:** 无本次代码变更；Dynamic `stopPropagation` 自 API 7，timestamp 自 8，历史点自 10，`preventDefault` 自 12；Static 对应能力自 API 23。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；history 和目标链为运行时临时数据。
- **最低支持版本:** Dynamic API 7；Native PointerEvent 传播设置自 API 12。
- **API 版本号策略:** 分通道记录真实 @since；`eventHandleId` 的后置分发策略由 Feat-03 承接。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 两阶段顺序固定 | 预分发逆序、Handle 正序，预分发失败禁止进入 Handle | AC-1.1~1.4 |
| 识别器不受普通 stopPropagation 截断 | 所有 Recognizer 接收事件并自行过滤 | AC-2.1~2.4 |
| 每指针每 VSync 最多一条聚合 MOVE | 原始批次作为 history 保留 | AC-4.1~4.4 |
| 真实/伪造终结分离 | 内部 CANCEL 不得提前清理真实序列 | AC-5.1~5.5 |
| Feat-03 边界 | 不展开跨 Container 坐标、PostEvent、handle 分组隔离 | 全部 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 同一 VSync 内同一指针最多分发一条聚合 MOVE；队列达到 40 条时输出过量诊断日志 | Pipeline 单测/Trace | `pipeline_context.cpp:4779` |
| 功耗 | MOVE 随 VSync 批处理，不为每个设备采样点单独请求业务回调 | 帧调度测试 | `FlushTouchEvents` |
| 内存 | history 仅保留批次/必要跨帧样本，非 MOVE 清理跨帧缓存 | 内存/单测 | `pipeline_context.cpp:3912` |
| 安全 | C API 空指针和不支持类型返回错误，不解引用无效 payload | C API 单测 | `ui_input_event.cpp:3119` |
| 可靠性 | 重复 DOWN、缺失 DOWN、失败识别器均有确定恢复分支 | 异常序列单测 | `event_manager.cpp:1024,1069,1381` |
| 可测试性 | 分发、传播、重采样、取消和通道差异均有 VM 映射 | 追溯审查 | VM-1~VM-6 |
| 自动化维测 | EventTree 记录目标处理与识别器状态；异常序列上报 GeneralInteractionError | Dump/错误上报测试 | EventManager |
| 定界定位 | 区分预分发失败、无目标链、重采样回退和伪造取消 | hilog/trace | EventManager/Pipeline |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无固定差异 | 按设备采样率与屏幕 VSync 生成 history/重采样点 | 实机滑动测试 | TouchEvent SDK 说明 |
| 平板 | 高刷新率/多窗口可能增加单帧原始点 | 仍按每指针一条聚合 MOVE | 高刷/分屏测试 | Pipeline 批处理 |
| 折叠屏 | 屏幕形态本身不改变传播规则 | display ID 变化时不得跨 display 重采样 | 折叠切屏测试 | 重采样条件 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|----------|
| 无障碍 | 否 | 本 Feat 不改变独立无障碍事件分发 | 全部 |
| 大字体 | 否 | 不影响序列分发和传播规则 | 全部 |
| 深色模式 | 否 | 不影响事件数据 | 全部 |
| 多窗口/分屏 | 是 | Feat-02 仅承接普通序列；跨容器坐标与 handle 隔离归 Feat-03 | SC-6 |
| 多用户 | 否 | 无持久化用户状态 | 全部 |
| 版本升级 | 是 | Dynamic/Static/C API 开放版本不同 | SC-3、SC-4 |
| 生态兼容 | 是 | stopPropagation 不阻止 Recognizer；多通道存在字段/错误类型偏差 | SC-2、SC-6 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 触摸事件序列分发与传播控制

  Scenario: SC-1 两阶段正常分发
    Given 当前指针具有深层目标到祖先排列的目标链
    When 分发一条触摸事件
    Then 先按逆序调用全部 DispatchEvent
    And 再按正序调用 HandleEvent

  Scenario: SC-2 普通触摸停止传播
    Given 目标链包含普通 TouchEventActuator 和手势识别器
    When 第一个普通 onTouch 调用 stopPropagation
    Then 后续普通 onTouch 被跳过
    And 所有手势识别器仍收到事件

  Scenario: SC-3 默认行为与传播相互独立
    Given Hyperlink 同步 onTouch 回调
    When 回调调用 preventDefault 但不调用 stopPropagation
    Then Hyperlink 默认行为被阻止
    And 普通触摸仍按原目标链传播

  Scenario: SC-4 单帧 MOVE 聚合
    Given 同一指针在一个 VSync 前产生多个 MOVE
    When Pipeline flush 触摸队列
    Then 每个指针只分发一条最新或重采样事件
    And 其余原始点可通过 history 获取

  Scenario: SC-5 识别器失败重发
    Given 单指 DOWN 首轮新产生失败识别器
    When Referee 未全部完成
    Then 强制清理识别器状态
    And 以 sendOnTouch=false 重发一次 DOWN
    And 不重复触发应用 onTouch

  Scenario: SC-6 伪造取消不终结真实序列
    Given 触摸序列仍在进行
    When 框架因内部恢复发送 isFalsified=true 的 CANCEL
    Then 当前目标收到取消通知
    And downFinger 与正式序列状态不按真实 CANCEL 清理
```

## Spec 自审清单

- [x] 无未决占位内容
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：跨容器坐标、PostEvent 和 eventHandleId 隔离归 Feat-03
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 规则表每条满足可复现、可观测、边界明确、关联 AC、无冲突
- [x] Dynamic/Static/Native 接口与核心实现均已交叉核验

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "DispatchTouchEvent DispatchEvent HandleEvent stopPropagation FlushTouchEvents resample falsified cancel"
  - repo: "openharmony/interface_sdk-js"
    query: "TouchEvent stopPropagation preventDefault getHistoricalPoints changedTouches API version"
```

**关键文档：** `design.md`、`Feat-01-hit-test-intercept-response-chain-spec.md`。
