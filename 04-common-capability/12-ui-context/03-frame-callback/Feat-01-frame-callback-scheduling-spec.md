# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Frame回调与动画调度 |
| 特性编号 | Func-04-12-03-Feat-01 |
| 所属 Epic | UI上下文 (04-12) |
| 优先级 | P1 |
| 目标版本 | API 12+ (动态版), API 23+ (静态版), API 16+ (C-API) |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | postFrameCallback | UIContext 方法，注册一次性帧回调（onFrame）与帧空闲回调（onIdle） |
| ADDED | postDelayedFrameCallback | UIContext 方法，注册延迟帧回调，延迟毫秒数后注册到下一帧 |
| ADDED | FrameCallback | 抽象类，包含 onFrame 与 onIdle 两个可选回调方法 |
| ADDED | OH_ArkUI_PostFrameCallback | C-API，注册一次性帧回调（API 16+） |
| ADDED | OH_ArkUI_PostIdleCallback | C-API，注册帧空闲回调（API 20+） |
| ADDED | PipelineContext::AddFrameCallback | 内部实现，将回调加入 frameCallbackFuncs_ / idleCallbackFuncs_ 列表 |
| ADDED | PipelineContext::FlushFrameCallback | 内部实现，在 VSync 帧调度阶段 drain 回调列表 |
| ADDED | PipelineContext::AddCAPIFrameCallback | 内部实现，将 C-API 回调加入 frameCallbackFuncsFromCAPI_ 列表 |
| ADDED | PipelineContext::FlushFrameCallbackFromCAPI | 内部实现，在 VSync 帧调度后 drain C-API 回调列表 |

## 输入文档

- SDK 类型定义（动态版）: `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`
- SDK 类型定义（静态版）: `interface/sdk-js/api/@ohos.arkui.UIContext.static.d.ets`
- C-API 头文件: `interfaces/native/native_node_napi.h`
- 动态前端桥接: `frameworks/bridge/declarative_frontend/engine/jsUIContext.js`
- 静态前端桥接: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.UIContext.ts`
- 帧回调核心实现: `frameworks/core/pipeline_ng/pipeline_context.cpp`
- 帧回调核心声明: `frameworks/core/pipeline_ng/pipeline_context.h`
- C-API 实现: `frameworks/core/interfaces/native/node/node_api.cpp`
- C-API 外部声明: `interfaces/native/node/native_node_napi.cpp`
- JSI 桥接: `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_common_bridge.cpp`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 应用开发者需要在下一帧渲染前执行自定义逻辑

**作为** 应用开发者
**我想要** 通过 UIContext.postFrameCallback 在下一帧的渲染阶段开始前执行自定义逻辑（如读取布局结果、修改属性）
**以便** 确保我的逻辑在帧渲染管线中正确的时序位置执行，避免布局/渲染不一致

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 postFrameCallback(frameCallback) 且 frameCallback.onFrame 已定义 THEN 回调在下一个 VSync 帧的 FlushAnimation 之后、FlushBuild 之前被调用，参数 frameTimeInNano 为该帧的纳秒级时间戳 | 正常 |
| AC-1.2 | WHEN 调用 postFrameCallback(frameCallback) 且 frameCallback.onFrame 为 undefined/null THEN 不注册帧回调，不触发 RequestFrame | 边界 |
| AC-1.3 | WHEN 同一帧内多次调用 postFrameCallback 注册多个 onFrame THEN 所有回调按注册顺序在同一帧内被依次执行 | 正常 |
| AC-1.4 | WHEN onFrame 回调执行完毕后 THEN 该回调从 frameCallbackFuncs_ 列表中移除，下一帧不会自动再次执行（一次性语义） | 正常 |
| AC-1.5 | WHEN postFrameCallback 在非 UI 线程调用（C-API 场景） THEN 返回 ARKUI_ERROR_CODE_UI_CONTEXT_INVALID 或触发线程安全检查 | 异常 |

### US-2: 应用开发者需要在帧空闲时间执行低优先级任务

**作为** 应用开发者
**我想要** 通过 UIContext.postFrameCallback 的 onIdle 回调在帧渲染完成后的空闲时间执行低优先级任务（如预计算、资源预加载）
**以便** 不影响帧渲染性能，充分利用帧间空闲时间

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 postFrameCallback(frameCallback) 且 frameCallback.onIdle 已定义 THEN 回调在帧渲染完成后的空闲阶段被调用，参数 timeLeftInNano 为剩余空闲时间纳秒值 | 正常 |
| AC-2.2 | WHEN onIdle 回调触发时剩余空闲时间 < MIN_IDLE_TIME（1ms）THEN 回调执行推迟到下一帧，并触发 RequestFrame | 边界 |
| AC-2.3 | WHEN onIdle 回调执行完毕后 THEN 该回调从 idleCallbackFuncs_ 列表中移除，下一帧不会自动再次执行（一次性语义） | 正常 |

### US-3: 应用开发者需要在延迟后注册帧回调

**作为** 应用开发者
**我想要** 通过 UIContext.postDelayedFrameCallback 在指定延迟毫秒数后注册帧回调
**以便** 在特定时间间隔后的帧中执行逻辑，如延迟动画触发、定时状态更新

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 调用 postDelayedFrameCallback(frameCallback, delayTime) 且 delayTime > 0 THEN 回调在 delayTime 毫秒后的下一个 VSync 帧中被执行 | 正常 |
| AC-3.2 | WHEN 调用 postDelayedFrameCallback(frameCallback, delayTime) 且 delayTime <= 0 THEN 行为等同于 postFrameCallback，回调在下一个 VSync 帧中执行 | 边界 |
| AC-3.3 | WHEN 延迟帧回调到期 THEN 回调通过 PostDelayedTask 被加入 frameCallbackFuncs_，并触发 RequestFrame | 正常 |

### US-4: C-API 开发者需要在下一帧执行自定义逻辑

**作为** NDK/C-API 开发者
**我想要** 通过 OH_ArkUI_PostFrameCallback 在下一帧执行自定义逻辑
**以便** 在 C 代码层面实现与 ArkTS postFrameCallback 相同的帧调度能力

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 调用 OH_ArkUI_PostFrameCallback(uiContext, userData, callback) 且参数有效 THEN 回调在下一帧的 FlushBuild 之后、FlushTouchEvents 之前被调用，参数为 nanoTimestamp、frameCount、userData | 正常 |
| AC-4.2 | WHEN 调用 OH_ArkUI_PostFrameCallback 且 uiContext 为 nullptr THEN 返回 ARKUI_ERROR_CODE_UI_CONTEXT_INVALID | 异常 |
| AC-4.3 | WHEN 调用 OH_ArkUI_PostFrameCallback 且 callback 为 nullptr THEN 返回 ARKUI_ERROR_CODE_CALLBACK_INVALID | 异常 |
| AC-4.4 | WHEN C-API 帧回调执行完毕后 THEN 该回调从 frameCallbackFuncsFromCAPI_ 列表中移除（一次性语义） | 正常 |
| AC-4.5 | WHEN OH_ArkUI_PostFrameCallback 在非 UI 线程调用 THEN 返回 ERROR_CODE_NATIVE_IMPL_NOT_MAIN_THREAD 或触发 LOGF_ABORT | 异常 |

### US-5: C-API 开发者需要在帧空闲时间执行低优先级任务

**作为** NDK/C-API 开发者
**我想要** 通过 OH_ArkUI_PostIdleCallback 在帧空闲时间执行低优先级任务
**以便** 在 C 代码层面实现与 ArkTS onIdle 相同的帧空闲回调能力

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 调用 OH_ArkUI_PostIdleCallback(uiContext, userData, callback) 且参数有效 THEN 回调在帧渲染完成后的空闲阶段被调用，参数为 nanoTimeLeft、frameCount、userData | 正常 |
| AC-5.2 | WHEN 调用 OH_ArkUI_PostIdleCallback 且 uiContext 为 nullptr THEN 返回 ARKUI_ERROR_CODE_UI_CONTEXT_INVALID | 异常 |
| AC-5.3 | WHEN 调用 OH_ArkUI_PostIdleCallback 且 callback 为 nullptr THEN 返回 ARKUI_ERROR_CODE_CALLBACK_INVALID | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1, R-5 | — | 单元测试 + 时序验证 | pipeline_context.cpp:7177-7191, pipeline_context.cpp:1214-1215 |
| AC-1.2 | R-2 | — | 单元测试 | arkts_native_common_bridge.cpp:10907-10909 |
| AC-1.3 | R-3 | — | 单元测试 | pipeline_context.cpp:7185-7189 |
| AC-1.4 | R-1 | — | 单元测试 | pipeline_context.cpp:7185-7186 std::swap |
| AC-1.5 | R-7 | — | C-API 单元测试 | node_api.cpp:2047-2051 |
| AC-2.1 | R-4, R-6 | — | 单元测试 + 时序验证 | pipeline_context.cpp:6386-6401 |
| AC-2.2 | R-8 | — | 单元测试 | pipeline_context.cpp:6392-6394 |
| AC-2.3 | R-4 | — | 单元测试 | pipeline_context.cpp:6396 std::move |
| AC-3.1 | R-9 | — | 单元测试 | pipeline_context.cpp:6353-6364 |
| AC-3.2 | R-10 | — | 单元测试 | pipeline_context.cpp:6343-6351 |
| AC-3.3 | R-9 | — | 单元测试 | pipeline_context.cpp:6356-6363 |
| AC-4.1 | R-5, R-11 | — | C-API 单元测试 | native_node_napi.cpp:684-707, pipeline_context.cpp:1242 |
| AC-4.2 | R-12 | — | C-API 单元测试 | native_node_napi_test.cpp:642 |
| AC-4.3 | R-13 | — | C-API 单元测试 | native_node_napi_test.cpp:630 |
| AC-4.4 | R-11 | — | 单元测试 | pipeline_context.cpp:7200-7202 std::swap |
| AC-4.5 | R-14 | — | C-API 单元测试 | native_node_napi.cpp:700-702 |
| AC-5.1 | R-6, R-15 | — | C-API 单元测试 | pipeline_context.cpp:6386-6401 |
| AC-5.2 | R-12 | — | C-API 单元测试 | native_node_napi.cpp:712-713 |
| AC-5.3 | R-13 | — | C-API 单元测试 | native_node_napi.cpp:714-715 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 postFrameCallback 并提供 onFrame 回调 | 回调被加入 frameCallbackFuncs_ 列表，在下一次 VSync 帧调度时被 drain 执行 | 回调参数为 uint64_t nanoTimestamp（帧时间戳纳秒） | AC-1.1, AC-1.4 |
| R-2 | 边界 | 调用 postFrameCallback 且 frameCallback 对象为 null/undefined | 桥接层直接返回 undefined，不注册回调，不触发 RequestFrame | JSI 层在 firstArg->IsNull() 或 firstArg->IsUndefined() 时短路返回 | AC-1.2 |
| R-3 | 行为 | 同一帧内多次调用 postFrameCallback 注册 N 个 onFrame 回调 | 所有回调按 emplace_back 顺序在同一帧 FlushFrameCallback 中被依次执行 | std::swap 后遍历 tasks 列表，tasks 是 std::list 保持插入顺序 | AC-1.3 |
| R-4 | 行为 | 调用 postFrameCallback 并提供 onIdle 回调 | 回调被加入 idleCallbackFuncs_ 列表，在帧空闲阶段 TriggerIdleCallback 中被 drain 执行 | 回调参数为 uint64_t deadline-time（剩余空闲纳秒），uint32_t frameCount | AC-2.1, AC-2.3 |
| R-5 | 行为 | ArkTS postFrameCallback 注册的帧回调在 VSync 帧调度中被执行 | FlushFrameCallback 在 FlushAnimation 之后、FlushBuild 之前被调用（pipeline_context.cpp:1214-1215） | ArkTS 帧回调在渲染管线中动画之后执行 | AC-1.1 |
| R-6 | 行为 | ArkTS onIdle 回调在帧空闲阶段被执行 | TriggerIdleCallback 在 OnIdle 中被调用，参数为 deadline 与 currentTime 的差值 | deadline - currentTime < MIN_IDLE_TIME 时推迟执行 | AC-2.1 |
| R-7 | 异常 | C-API OH_ArkUI_PostFrameCallback 在非 UI 线程调用 | pipeline->CheckThreadSafe() 返回 false 时，返回 ERROR_CODE_NATIVE_IMPL_NOT_MAIN_THREAD | LOGF_ABORT 在 node_api.cpp:701 触发 | AC-1.5 |
| R-8 | 边界 | onIdle 回调触发时剩余空闲时间 < 1ms（MIN_IDLE_TIME） | 回调执行推迟到下一帧，调用 RequestFrame 请求新帧 | pipeline_context.cpp:6392-6394, MIN_IDLE_TIME 常量 | AC-2.2 |
| R-9 | 行为 | 调用 postDelayedFrameCallback 且 delayMillis > 0 | frameCallbackFunc 和 idleCallbackFunc 通过 PostDelayedTask 延迟 delayMillis 毫秒后加入列表 | 延迟到期后加入 frameCallbackFuncs_/idleCallbackFuncs_ 并调用 RequestFrame | AC-3.1, AC-3.3 |
| R-10 | 边界 | 调用 postDelayedFrameCallback 且 delayMillis <= 0 | 行为等同于 postFrameCallback：回调直接加入列表，立即 RequestFrame | pipeline_context.cpp:6343-6351 | AC-3.2 |
| R-11 | 行为 | C-API 帧回调在 VSync 帧调度中被执行 | FlushFrameCallbackFromCAPI 在 FlushBuild 之前、FlushTouchEvents 之前被调用（pipeline_context.cpp:1242） | C-API 帧回调在渲染管线中动画之后、构建之前执行 | AC-4.1, AC-4.4 |
| R-12 | 异常 | C-API 调用时 uiContext 为 nullptr | 返回 ARKUI_ERROR_CODE_UI_CONTEXT_INVALID | CHECK_NULL_RETURN_WITH_MESSAGE 宏 | AC-4.2, AC-5.2 |
| R-13 | 异常 | C-API 调用时 callback 为 nullptr | 返回 ARKUI_ERROR_CODE_CALLBACK_INVALID | CHECK_NULL_RETURN_WITH_MESSAGE 宏 | AC-4.3, AC-5.3 |
| R-14 | 异常 | OH_ArkUI_PostFrameCallback 在非 UI 线程调用 | 返回 ERROR_CODE_NATIVE_IMPL_NOT_MAIN_THREAD，严重时 LOGF_ABORT | node_api.cpp:700-702 | AC-4.5 |
| R-15 | 行为 | OH_ArkUI_PostIdleCallback 注册的回调在帧空闲阶段被执行 | 回调被加入 idleCallbackFuncs_ 列表，在 TriggerIdleCallback 中被 drain | 参数为 nanoTimeLeft、frameCount、userData | AC-5.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 (一次性帧回调语义) | 单元测试 + 源码审查 | std::swap drain 行为，回调不自动重注册 |
| VM-2 | R-2 (null/undefined frameCallback) | 单元测试 | JSI 层短路返回 undefined |
| VM-3 | R-3 (多回调顺序) | 单元测试 | 同帧多回调按注册顺序执行 |
| VM-4 | R-4 (onIdle 一次性语义) | 单元测试 | std::move drain 行为 |
| VM-5 | R-5/R-11 (帧回调执行时序) | 时序追踪 | FlushAnimation < FlushFrameCallback < FlushFrameCallbackFromCAPI < FlushBuild |
| VM-6 | R-8 (MIN_IDLE_TIME 推迟) | 单元测试 | deadline - currentTime < 1ms 时推迟并 RequestFrame |
| VM-7 | R-9/R-10 (延迟帧回调) | 单元测试 | delayMillis <= 0 直接加入，> 0 PostDelayedTask |
| VM-8 | R-12/R-13 (C-API null 参数) | C-API 单元测试 | nullptr uiContext/callback 返回对应错误码 |
| VM-9 | R-14 (C-API 线程安全) | C-API 单元测试 | 非 UI 线程调用返回 NOT_MAIN_THREAD |
| VM-10 | R-15 (C-API 空闲回调) | C-API 单元测试 | idleCallbackFuncs_ drain |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| UIContext.postFrameCallback | Public | frameCallback: FrameCallback | void | N/A | 注册一次性帧回调（onFrame + onIdle） | AC-1.1–1.4, AC-2.1–2.3 |
| UIContext.postDelayedFrameCallback | Public | frameCallback: FrameCallback, delayTime: number/long | void | N/A | 注册延迟帧回调 | AC-3.1–3.3 |
| FrameCallback (abstract class) | Public | onFrame(frameTimeInNano: number/long), onIdle(timeLeftInNano: number/long) | void | N/A | 帧回调抽象类 | AC-1.1, AC-2.1 |
| OH_ArkUI_PostFrameCallback | Public (C-API) | uiContext: ArkUI_ContextHandle, userData: void*, callback: void(*)(uint64_t, uint32_t, void*) | ArkUI_ErrorCode | ARKUI_ERROR_CODE_NO_ERROR, ARKUI_ERROR_CODE_CAPI_INIT_ERROR, ARKUI_ERROR_CODE_UI_CONTEXT_INVALID, ARKUI_ERROR_CODE_CALLBACK_INVALID | C-API 注册一次性帧回调 | AC-4.1–4.5 |
| OH_ArkUI_PostIdleCallback | Public (C-API) | uiContext: ArkUI_ContextHandle, userData: void*, callback: void(*)(uint64_t, uint32_t, void*) | ArkUI_ErrorCode | 同上 | C-API 注册帧空闲回调 | AC-5.1–5.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| N/A | — | — | — | — |

## 接口规格

### 接口定义

**UIContext.postFrameCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `postFrameCallback(frameCallback: FrameCallback): void` |
| 返回值 | `void` — 无返回值 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| frameCallback | FrameCallback | 是 | 无 | 必须为 FrameCallback 实例或其子类；onFrame/onIdle 至少有一个已定义，否则不注册回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 FrameCallback，onFrame 已定义 | onFrame 回调在下一帧 FlushAnimation 后被执行，参数为帧时间戳纳秒值 | AC-1.1 |
| 2 | 传入有效 FrameCallback，仅 onIdle 已定义 | onIdle 回调在帧空闲阶段被执行 | AC-2.1 |
| 3 | 传入 null/undefined frameCallback | JSI 层短路返回 undefined，不注册 | AC-1.2 |
| 4 | onFrame 回调执行后 | 回调从列表中移除，不会在后续帧自动执行 | AC-1.4 |
| 5 | 同帧多次注册 | 所有回调按注册顺序依次执行 | AC-1.3 |

---

**UIContext.postDelayedFrameCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `postDelayedFrameCallback(frameCallback: FrameCallback, delayTime: number): void` (动态版) / `postDelayedFrameCallback(frameCallback: FrameCallback, delayTime: long): void` (静态版) |
| 返回值 | `void` — 无返回值 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| frameCallback | FrameCallback | 是 | 无 | 同 postFrameCallback |
| delayTime | number (动态) / long (静态) | 是 | 无 | 延迟毫秒数；<=0 时等同于 postFrameCallback；>0 时通过 PostDelayedTask 延迟 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | delayTime > 0 | 回调在 delayTime 毫秒后的下一帧执行 | AC-3.1 |
| 2 | delayTime <= 0 | 等同于 postFrameCallback，回调在下一帧执行 | AC-3.2 |

---

**FrameCallback (abstract class)**

| 属性 | 值 |
|------|-----|
| 类型 | `abstract class FrameCallback` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-2.1 |

**参数约束**

| 方法 | 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|------|--------|---------|
| onFrame | frameTimeInNano | number (动态) / long (静态) | 否 | 无实现 | 帧时间戳纳秒值；范围 [0, +∞)；需与 postFrameCallback 配合使用 |
| onIdle | timeLeftInNano | number (动态) / long (静态) | 否 | 无实现 | 剩余空闲时间纳秒值；范围 [0, +∞)；需与 postFrameCallback/postDelayedFrameCallback 配合使用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | onFrame 已定义 | 在帧渲染阶段 FlushAnimation 后被调用 | AC-1.1 |
| 2 | onIdle 已定义 | 在帧空闲阶段被调用，剩余时间 > MIN_IDLE_TIME | AC-2.1 |
| 3 | onFrame 和 onIdle 都未定义 | 桥接层不注册任何回调 | AC-1.2 |

---

**OH_ArkUI_PostFrameCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_PostFrameCallback(ArkUI_ContextHandle uiContext, void* userData, void (*callback)(uint64_t nanoTimestamp, uint32_t frameCount, void* userData))` |
| 返回值 | `ArkUI_ErrorCode` — 操作结果码 |
| 开放范围 | Public (C-API) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR / ARKUI_ERROR_CODE_CAPI_INIT_ERROR / ARKUI_ERROR_CODE_UI_CONTEXT_INVALID / ARKUI_ERROR_CODE_CALLBACK_INVALID |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 必须为有效的 UI 上下文句柄；nullptr 返回 ARKUI_ERROR_CODE_UI_CONTEXT_INVALID |
| userData | void* | 是 | 无 | 用户自定义数据指针，传递给回调；可为任意值 |
| callback | void(*)(uint64_t, uint32_t, void*) | 是 | 无 | 必须为有效函数指针；nullptr 返回 ARKUI_ERROR_CODE_CALLBACK_INVALID；必须在 UI 线程调用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 uiContext、callback | 回调在下一帧 FlushBuild 前执行 | AC-4.1 |
| 2 | uiContext 为 nullptr | 返回 ARKUI_ERROR_CODE_UI_CONTEXT_INVALID | AC-4.2 |
| 3 | callback 为 nullptr | 返回 ARKUI_ERROR_CODE_CALLBACK_INVALID | AC-4.3 |
| 4 | 非 UI 线程调用 | 返回 ERROR_CODE_NATIVE_IMPL_NOT_MAIN_THREAD | AC-4.5 |
| 5 | 回调执行后 | 从 frameCallbackFuncsFromCAPI_ 移除，不自动重注册 | AC-4.4 |

---

**OH_ArkUI_PostIdleCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_PostIdleCallback(ArkUI_ContextHandle uiContext, void* userData, void (*callback)(uint64_t nanoTimeLeft, uint32_t frameCount, void* userData))` |
| 返回值 | `ArkUI_ErrorCode` — 操作结果码 |
| 开放范围 | Public (C-API) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR / ARKUI_ERROR_CODE_CAPI_INIT_ERROR / ARKUI_ERROR_CODE_UI_CONTEXT_INVALID / ARKUI_ERROR_CODE_CALLBACK_INVALID |
| 关联 AC | AC-5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 同 OH_ArkUI_PostFrameCallback |
| userData | void* | 是 | 无 | 用户自定义数据指针 |
| callback | void(*)(uint64_t, uint32_t, void*) | 是 | 无 | 同 OH_ArkUI_PostFrameCallback |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效参数 | 回调在帧空闲阶段执行，参数为剩余时间纳秒值、帧计数、userData | AC-5.1 |
| 2 | uiContext nullptr | 返回 ARKUI_ERROR_CODE_UI_CONTEXT_INVALID | AC-5.2 |
| 3 | callback nullptr | 返回 ARKUI_ERROR_CODE_CALLBACK_INVALID | AC-5.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。postFrameCallback、postDelayedFrameCallback、FrameCallback 为新增 API，不影响已有 API 行为。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 动态版 API 12+，静态版 API 23+，C-API OH_ArkUI_PostFrameCallback API 16+，C-API OH_ArkUI_PostIdleCallback API 20+
- **API 版本号策略:** 动态版 API 使用 `@since 12 dynamic` 标注；静态版 API 使用 `@since 23 static` 标注；C-API 使用 `@since 16` / `@since 20` 标注。FrameCallback.onFrame 的 timeLeftInNano 参数在动态版为 `number` 类型，静态版为 `long` 类型。

**版本行为差异：**

| 版本 | 行为差异 | 来源 |
|------|----------|------|
| API 12 (动态) | FrameCallback 参数类型为 number | UIContext.d.ts:3772 |
| API 23 (静态) | FrameCallback 参数类型为 long；postDelayedFrameCallback delayTime 类型为 long | UIContext.static.d.ets:2856, 4278 |
| API 16 (C-API) | OH_ArkUI_PostFrameCallback 仅提供帧回调，不含空闲回调 | native_node_napi.h:375 |
| API 20 (C-API) | OH_ArkUI_PostIdleCallback 新增帧空闲回调 | native_node_napi.h:394 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 一次性回调语义 | postFrameCallback 注册的回调在每帧被 drain（std::swap 移出列表后遍历执行），不会自动重注册。开发者需要每帧重新调用 postFrameCallback 以实现持续帧回调 | AC-1.4, AC-2.3, AC-4.4 |
| ArkTS vs C-API 回调列表隔离 | ArkTS 帧回调存储在 frameCallbackFuncs_（std::list<FrameCallbackFunc>），C-API 帧回调存储在 frameCallbackFuncsFromCAPI_（std::list<FrameCallbackFuncFromCAPI>），两个列表独立 drain | AC-4.1 vs AC-1.1 |
| ArkTS vs C-API 执行时序差异 | ArkTS 帧回调在 FlushAnimation 后执行（pipeline_context.cpp:1215），C-API 帧回调在 FlushBuild 前、FlushTouchEvents 前执行（pipeline_context.cpp:1242）。两者不在同一 drain 阶段 | AC-1.1 vs AC-4.1 |
| 延迟回调使用 PostDelayedTask | postDelayedFrameCallback 的延迟机制基于 TaskExecutor::PostDelayedTask，延迟到期后回调被加入 frameCallbackFuncs_ 并 RequestFrame，而非直接在延迟时间点执行 | AC-3.1 |
| 空闲回调 MIN_IDLE_TIME 门槛 | onIdle 回调仅在剩余空闲时间 >= MIN_IDLE_TIME（1ms）时执行，否则推迟到下一帧 | AC-2.2 |
| C-API 必须在 UI 线程调用 | OH_ArkUI_PostFrameCallback 通过 pipeline->CheckThreadSafe() 检查线程安全性，非 UI 线程调用返回错误或触发 LOGF_ABORT | AC-4.5, AC-1.5 |
| frameCount == UINT64_MAX 语义 | FlushFrameCallback/FlushFrameCallbackFromCAPI 在 frameCount == UINT64_MAX 时仅 RequestFrame，不执行回调（用于 recover vsync 场景） | R-1, R-11 |
| PipelineContext 生命周期 | 延迟回调通过 WeakClaim(this) 持有 PipelineContext 弱引用，PipelineContext 已销毁时不执行回调 | R-9 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 帧回调执行不增加帧延迟 > 1ms | 帧时间追踪 | FlushVsync 中 FlushFrameCallback 执行时间度量 |
| 功耗 | 无额外功耗 | 代码审查 | 回调仅在 VSync 帧内执行，无后台轮询 |
| 内存 | 每个回调对象占用 ≤ 函数对象 + 闭包大小 | 代码审查 | std::list<std::function> 存储 |
| 安全 | C-API 参数校验防止 null 指针崩溃 | C-API 单元测试 | native_node_napi_test.cpp:613-643 |
| 可靠性 | PipelineContext 销毁时延迟回调不执行 | 代码审查 | WeakClaim(Upgrade) 检查 |
| 可测试性 | 支持 Mock VSync 时间戳进行单测 | 单测框架 | FlushFrameCallback 参数可控 |
| 自动化维测 | 帧回调注册/执行数量可通过 Dump 查看 | hilog/Dump | PipelineContext Dump 输出 |
| 定界定位 | 非线程安全调用触发 LOGF_ABORT | LOGF | native_node_napi.cpp:701 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

帧回调机制基于 PipelineContext VSync 调度，与设备类型无关。不同设备的 VSync 频率可能不同（60Hz/90Hz/120Hz），帧回调的 nanoTimestamp 由系统 VSync 提供，无需适配逻辑。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 帧回调不涉及无障碍属性 | — |
| 大字体 | 否 | 帧回调不涉及 UI 尺寸 | — |
| 深色模式 | 否 | 帧回调不涉及颜色/主题 | — |
| 多窗口/分屏 | 是 | 每个窗口有独立的 PipelineContext，帧回调在各自 PipelineContext 中独立调度 | 多窗口场景下各窗口帧回调独立执行 |
| 多用户 | 否 | 帧回调不涉及用户隔离 | — |
| 版本升级 | 是 | 动态版 API 12+，静态版 API 23+，C-API API 16+/20+，需注意版本差异 | FrameCallback 参数类型差异 (number vs long) |
| 生态兼容 | 是 | postFrameCallback 类似 Web requestAnimationFrame 的一次性语义，开发者需注意非自动重注册 | 开发者可能误用为持续回调 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Frame回调与帧调度
  作为一个应用开发者
  我想要通过 UIContext 注册帧回调
  以便在正确的帧渲染时序位置执行自定义逻辑

  Scenario: 注册一次性帧回调并在下一帧执行
    Given 一个有效的 UIContext 实例
    And 一个 FrameCallback 实例，onFrame 已定义
    When 调用 postFrameCallback(frameCallback)
    Then 回调被加入 frameCallbackFuncs_ 列表
    And 下一帧 VSync 到达时 FlushFrameCallback 执行回调
    And 回调参数 frameTimeInNano 为帧时间戳纳秒值
    And 回调执行后从列表中移除
    And 下一帧不会自动再次执行该回调

  Scenario: 注册多个帧回调按顺序执行
    Given 一个有效的 UIContext 实例
    And 三个 FrameCallback 实例 CB1, CB2, CB3，onFrame 均已定义
    When 先调用 postFrameCallback(CB1)
    And 再调用 postFrameCallback(CB2)
    And 再调用 postFrameCallback(CB3)
    Then 下一帧中 CB1.onFrame → CB2.onFrame → CB3.onFrame 按注册顺序执行
    And 所有回调执行后被 drain 移除

  Scenario: 传入 null frameCallback 不注册回调
    Given 一个有效的 UIContext 实例
    When 调用 postFrameCallback(null) 或 postFrameCallback(undefined)
    Then 桥接层不注册任何回调
    And 不触发 RequestFrame

  Scenario: 帧空闲回调在剩余时间充足时执行
    Given 一个有效的 UIContext 实例
    And 一个 FrameCallback 实例，onIdle 已定义
    When 调用 postFrameCallback(frameCallback)
    And 帧渲染完成后剩余空闲时间 >= 1ms
    Then TriggerIdleCallback 执行 onIdle 回调
    And 回调参数 timeLeftInNano 为剩余空闲纳秒值
    And 回调执行后从列表中移除

  Scenario: 帧空闲回调在剩余时间不足时推迟
    Given 一个有效的 UIContext 实例
    And 一个 FrameCallback 实例，onIdle 已定义
    When 调用 postFrameCallback(frameCallback)
    And 帧渲染完成后剩余空闲时间 < 1ms
    Then 回调执行被推迟到下一帧
    And 调用 RequestFrame 请求新帧

  Scenario Outline: 延迟帧回调在指定延迟后执行
    Given 一个有效的 UIContext 实例
    And 一个 FrameCallback 实例，onFrame 已定义
    When 调用 postDelayedFrameCallback(frameCallback, <delayTime>)
    Then 回调在 <实际延迟> 后的下一帧执行

    Examples:
      | delayTime | 实际延迟 |
      | 100       | 100ms 后的下一帧 |
      | 0         | 下一帧（等同于 postFrameCallback） |
      | -1        | 下一帧（等同于 postFrameCallback） |

  Scenario: C-API 注册帧回调
    Given 一个有效的 ArkUI_ContextHandle
    And 一个有效的回调函数指针
    When 调用 OH_ArkUI_PostFrameCallback(uiContext, userData, callback)
    Then 回调被加入 frameCallbackFuncsFromCAPI_ 列表
    And 下一帧 FlushFrameCallbackFromCAPI 执行回调
    And 回调参数为 nanoTimestamp, frameCount, userData
    And 回调执行后从列表中移除

  Scenario: C-API 传入 null uiContext
    When 调用 OH_ArkUI_PostFrameCallback(nullptr, userData, callback)
    Then 返回 ARKUI_ERROR_CODE_UI_CONTEXT_INVALID

  Scenario: C-API 传入 null callback
    When 调用 OH_ArkUI_PostFrameCallback(uiContext, userData, nullptr)
    Then 返回 ARKUI_ERROR_CODE_CALLBACK_INVALID

  Scenario: C-API 非线程安全调用
    Given 非 UI 线程
    When 调用 OH_ArkUI_PostFrameCallback(uiContext, userData, callback)
    Then 返回 ERROR_CODE_NATIVE_IMPL_NOT_MAIN_THREAD

  Scenario: PipelineContext 销毁后延迟回调不执行
    Given 一个有效的 UIContext 实例
    And 一个 FrameCallback 实例，onFrame 已定义
    When 调用 postDelayedFrameCallback(frameCallback, 100)
    And PipelineContext 在 100ms 内被销毁
    Then 延迟到期时 pipeline.Upgrade() 返回 nullptr
    And 回调不执行
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）—— 本 Feat 仅覆盖帧回调与调度，不包含动画 API（animateTo/animateToImmediately/keyframeAnimateTo/createAnimator，属于 04-12-01 Feat-04）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "PipelineContext FlushVsync 调用链中 FlushFrameCallback 与 FlushFrameCallbackFromCAPI 的执行顺序与时序约束"
  - repo: "openharmony/ace_engine"
    query: "postFrameCallback 一次性语义实现细节：std::swap drain 机制与 RequestFrame 触发条件"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_PostFrameCallback C-API 线程安全检查与错误码处理"
  - repo: "openharmony/ace_engine"
    query: "TriggerIdleCallback MIN_IDLE_TIME 门槛与推迟执行机制"
  - repo: "openharmony/ace_engine"
    query: "postDelayedFrameCallback PostDelayedTask 延迟机制与 PipelineContext WeakClaim 生命周期绑定"
```

**关键文档：**

- SDK 动态版类型定义: `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts:3760-3788, 5868-5891`
- SDK 静态版类型定义: `interface/sdk-js/api/@ohos.arkui.UIContext.static.d.ets:2847-2867, 4259-4278`
- C-API 声明: `interfaces/native/native_node_napi.h:375-395`
- PipelineContext 帧回调实现: `frameworks/core/pipeline_ng/pipeline_context.cpp:6340-6377 (AddFrameCallback), 7177-7191 (FlushFrameCallback), 7193-7207 (FlushFrameCallbackFromCAPI), 6386-6401 (TriggerIdleCallback)`
- PipelineContext 帧回调声明: `frameworks/core/pipeline_ng/pipeline_context.h:70-72 (类型定义), 971-978 (方法声明), 1633-1635 (存储成员)`
- VSync 帧调度顺序: `frameworks/core/pipeline_ng/pipeline_context.cpp:1214-1215 (ArkTS), 1242 (C-API)`
- C-API 实现: `interfaces/native/node/native_node_napi.cpp:684-707, frameworks/core/interfaces/native/node/node_api.cpp:2038-2058`
- JSI 桥接实现: `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_common_bridge.cpp:10901-10957`
- 动态前端桥接: `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:966-976`
- 静态前端桥接: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.UIContext.ts:1083-1095`
- C-API 单元测试: `test/unittest/interfaces/native_node_napi_test.cpp:613-643`

## 附录：PipelineContext 帧回调 drain 实现分析

### 核心数据结构

PipelineContext 维护三个独立的回调列表（pipeline_context.h:1633-1635）：

```cpp
std::list<FrameCallbackFuncFromCAPI> frameCallbackFuncsFromCAPI_;  // C-API 帧回调
std::list<IdleCallbackFunc> idleCallbackFuncs_;                    // 空闲回调
std::list<FrameCallbackFunc> frameCallbackFuncs_;                  // ArkTS 帧回调
```

类型定义（pipeline_context.h:70-72）：

```cpp
using FrameCallbackFunc = std::function<void(uint64_t nanoTimestamp)>;
using FrameCallbackFuncFromCAPI = std::function<void(uint64_t nanoTimestamp, uint32_t frameCount)>;
using IdleCallbackFunc = std::function<void(uint64_t nanoTimestamp, uint32_t frameCount)>;
```

### AddFrameCallback 注册逻辑 (pipeline_context.cpp:6340-6377)

注册分两路：

1. **delayMillis <= 0**（立即注册）：
   - frameCallbackFunc 非空 → `frameCallbackFuncs_.emplace_back(std::move(frameCallbackFunc))`
   - idleCallbackFunc 非空 → `idleCallbackFuncs_.emplace_back(std::move(idleCallbackFunc))`
   - 调用 `RequestFrame()` 请求下一帧

2. **delayMillis > 0**（延迟注册）：
   - frameCallbackFunc 非空 → `PostDelayedTask` 延迟 delayMillis 后：
     - `pipeline->frameCallbackFuncs_.emplace_back(std::move(callback))`
     - `pipeline->RequestFrame()`
   - idleCallbackFunc 非空 → 类似逻辑加入 `idleCallbackFuncs_`
   - 持有 `WeakClaim(this)` 弱引用，pipeline 销毁时不执行

### FlushFrameCallback drain 逻辑 (pipeline_context.cpp:7177-7191)

```cpp
void PipelineContext::FlushFrameCallback(uint64_t nanoTimestamp, uint64_t frameCount)
{
    // UINT64_MAX 表示恢复 vsync，仅请求帧
    if (frameCount == UINT64_MAX) {
        RequestFrame();
        return;
    }
    if (!frameCallbackFuncs_.empty()) {
        decltype(frameCallbackFuncs_) tasks;
        std::swap(tasks, frameCallbackFuncs_);  // ← 一次性语义的关键：swap 移出
        for (const auto& frameCallbackFunc : tasks) {
            frameCallbackFunc(nanoTimestamp);
        }
    }
}
```

**关键设计决策：std::swap drain**

`std::swap(tasks, frameCallbackFuncs_)` 将当前所有回调移到临时 `tasks` 列表，原 `frameCallbackFuncs_` 变为空列表。这意味着：

- 当前帧注册的所有回调在本帧被执行
- 执行完毕后 `tasks` 临时对象析构，回调被销毁
- 下一帧 `frameCallbackFuncs_` 为空，不会自动再次执行
- **开发者必须每帧重新调用 postFrameCallback 以实现持续帧回调**

这是与 Web `requestAnimationFrame` 类似的一次性语义，但与某些持续回调注册机制不同。

### FlushFrameCallbackFromCAPI drain 逻辑 (pipeline_context.cpp:7193-7207)

与 FlushFrameCallback 完全相同的 drain 机制，但操作 `frameCallbackFuncsFromCAPI_` 列表，回调签名额外包含 `frameCount` 参数。

### VSync 帧调度中的回调执行时序 (pipeline_context.cpp:1172-1289)

在 `PipelineContext::FlushVsync` 中，帧回调执行时序如下：

```
FlushVsync(nanoTimestamp, frameCount):
  1. DispatchDisplaySync(nanoTimestamp)          // DisplaySync 分发
  2. FlushZindexUpdate()                          // Z 序更新
  3. FlushAnimation(nanoTimestamp)                 // 动画刷新
  4. FlushFrameCallback(nanoTimestamp, frameCount) // ← ArkTS 帧回调在此执行
  5. FlushModifierAnimation(nanoTimestamp)         // Modifier 动画刷新
  6. FlushTouchEvents()                            // 触摸事件分发
  ...
  7. FlushFrameCallbackFromCAPI(nanoTimestamp, frameCount) // ← C-API 帧回调在此执行
  8. FlushBuild()                                  // 组件树构建
  9. FlushTask()                                   // 布局任务
  ...
  10. TryCallNextFrameLayoutCallback()             // 布局完成回调
  11. FlushModifier()                              // Modifier 渲染
  ...
```

ArkTS 帧回调在第 4 步（动画刷新后）执行；C-API 帧回调在第 7 步（构建前）执行。两者不在同一 drain 阶段。

### TriggerIdleCallback drain 逻辑 (pipeline_context.cpp:6386-6401)

```cpp
void PipelineContext::TriggerIdleCallback(int64_t deadline)
{
    if (idleCallbackFuncs_.empty()) { return; }
    int64_t currentTime = GetSysTimestamp();
    if (deadline - currentTime < MIN_IDLE_TIME) {  // MIN_IDLE_TIME = 1ms
        RequestFrame();
        return;
    }
    decltype(idleCallbackFuncs_) tasks(std::move(idleCallbackFuncs_));  // ← 一次性语义
    for (const auto& IdleCallbackFunc : tasks) {
        IdleCallbackFunc(deadline - currentTime, GetFrameCount());
        currentTime = GetSysTimestamp();  // ← 每次回调后更新时间
    }
}
```

空闲回调也使用一次性语义（`std::move` drain），并有 MIN_IDLE_TIME（1ms）门槛保护。每执行一个回调后重新获取当前时间，以判断是否还有足够的空闲时间继续执行后续回调。
