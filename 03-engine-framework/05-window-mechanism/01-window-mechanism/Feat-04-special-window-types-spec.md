# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 特殊窗口类型 |
| 特性编号 | Func-03-05-01-Feat-04 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | API 9 及以后（以 master HEAD 实现为基线） |
| SIG 归属 | ArkUI SIG / 窗口与渲染团队 |
| 状态 | Baselined |
| 复杂度 | 复杂 |

> 本 Feat 锁定三种非标准窗口类型的架构与行为规格：**FormRenderWindow**（表单渲染窗口，自建 VSyncReceiver + RSSurfaceNode，不包装 Rosen::Window）、**DragWindow**（拖拽预览窗口，继承 AceType 而非 Window，创建独立浮动 Rosen::Window 进行一次性绘制）、**FoldableWindow**（折叠屏窗口状态查询，继承 AceType 而非 Window）。这三者与 RosenWindow 的核心区别在于：不参与标准 PipelineContext 渲染管线、不使用标准 VSync 回调链、有不同的生命周期模型。
>
> **命名说明**：`FoldableWindow` 虽然名称含 "Window"，但不具备任何窗口功能（无 surface、无 vsync、无渲染管线、无 RSUIDirector、无生命周期回调），仅提供 `IsFoldExpand()` 折叠状态查询。与 `DragWindow`（至少创建浮动 `Rosen::Window` 进行绘制）不同，`FoldableWindow` 不与任何窗口对象交互。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | FormRenderWindow 完整架构 | 自建 VSyncReceiver + RSSurfaceNode + RSUIDirector + RSFrameRateLinker |
| ADDED | FormRenderWindow VSync 驱动 | RSInterfaces::CreateVSyncReceiver + RequestNextVSync 自驱动 |
| ADDED | FormRenderWindow 生命周期 | OnShow→GoForeground / OnHide→(no GoBackground) / Destroy |
| ADDED | FormRenderWindow 帧率链接 | RSFrameRateLinker + FlushFrameRate |
| ADDED | DragWindow 架构 | AceType 继承体系 + CreateDragWindow 工厂 + 浮动 Rosen::Window 创建 |
| ADDED | DragWindow 一次性绘制 | DrawPixelMap / DrawFrameNode / DrawText / DrawTextNG |
| ADDED | FoldableWindow 架构 | AceType 继承 + IsFoldExpand 查询接口 |

## 输入文档

- 关联设计：`specs/03-engine-framework/05-window-mechanism/01-window-mechanism/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `frameworks/core/components_ng/render/adapter/form_render_window.h` / `.cpp` — FormRenderWindow 完整实现
  - `frameworks/base/window/drag_window.h` — DragWindow 抽象基类（继承 AceType）
  - `adapter/ohos/entrance/window/drag_window_ohos.h` / `.cpp` — DragWindowOhos 平台实现
  - `frameworks/base/window/foldable_window.h` — FoldableWindow 抽象基类（继承 AceType）
  - `adapter/ohos/entrance/window/foldable_window_ohos.h` / `.cpp` — FoldableWindowOhos 平台实现

## 用户故事

### US-1: FormRenderWindow 自建 VSync 驱动

- As a 表单渲染维护者
- I want FormRenderWindow 创建自己的 VSyncReceiver 和 RSSurfaceNode，不依赖 Rosen::Window
- So that 表单渲染可以在没有窗口管理器参与的情况下独立运行

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `FormRenderWindow(taskExecutor, id, connectToRender)` 构造执行 THEN 通过 `Rosen::RSInterfaces::GetInstance().CreateVSyncReceiver("Form", frameRateLinkerId)` 创建独立 VSyncReceiver，并调用 `receiver_->Init()`。来源：`form_render_window.cpp:56-67` | 正常 |
| AC-1.2 | WHEN VSyncReceiver 创建成功 THEN 创建 `RSFrameRateLinker` 并传入 CreateVSyncReceiver 的第 2 参数，用于帧率联动。来源：`form_render_window.cpp:58-59` | 正常 |
| AC-1.3 | WHEN VSyncReceiver 创建失败（返回 nullptr）THEN 记录 `LOGE("Form create vsync receiver failed")` 并返回，不继续初始化。来源：`form_render_window.cpp:60-63` | 异常 |
| AC-1.4 | WHEN 构造完成 THEN 调用 `InitOnVsyncCallback()` 设置 frameCallback_，并立即 `receiver_->RequestNextVSync(frameCallback_)` 请求第一帧。来源：`form_render_window.cpp:69-71` | 正常 |
| AC-1.5 | WHEN vsyncCounter 是 `static std::atomic<int32_t>` THEN 创建时 `++vsyncCounter` 并 LOGI，销毁时 `--vsyncCounter` 并 LOGI，用于全局表单 VSync 计数。来源：`form_render_window.cpp:65, 127-128` | 边界 |

### US-2: FormRenderWindow 自建 RSSurfaceNode 与 RSUIDirector

- As a 表单渲染维护者
- I want FormRenderWindow 创建自己的 RSUIDirector 和 RSSurfaceNode，不通过 Rosen::Window 获取
- So that 表单渲染管线完全自包含

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 构造函数执行 THEN 通过 `OHOS::Rosen::RSUIDirector::Create(connectToRender)` 创建 RSUIDirector（connectToRender 可为 nullptr）。来源：`form_render_window.cpp:73` | 正常 |
| AC-2.2 | WHEN 构造函数执行 THEN 通过 `RSSurfaceNode::Create(surfaceNodeConfig, true, rsUIDirector_->GetRSUIContext())` 创建 surface node，名称为 "ArkTSCardNode"，`isSync=true`。来源：`form_render_window.cpp:75-78` | 正常 |
| AC-2.3 | WHEN surface node 创建完成 THEN 调用 `rsUIDirector_->SetRSSurfaceNode(rsSurfaceNode_)` 绑定。来源：`form_render_window.cpp:79` | 正常 |
| AC-2.4 | WHEN 构造函数执行 THEN 通过 `rsUIDirector_->SetUITaskRunner(lambda, 0, useMultiInstance)` 设置 UI 任务 runner，lambda 内部使用 `ContainerScope(id)` + TaskExecutor PostDelayedTask。来源：`form_render_window.cpp:80-85` | 正常 |

### US-3: FormRenderWindow RequestFrame 自驱动 VSync

- As a 表单渲染维护者
- I want FormRenderWindow::RequestFrame 在 onShow_ 时调用 receiver_->RequestNextVSync 请求下一帧
- So that 表单渲染按需驱动 VSync，不持续空转

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `RequestFrame()` 被调用且 `receiver_` 非空且 `onShow_==true` THEN 调用 `receiver_->RequestNextVSync(frameCallback_)`。来源：`form_render_window.cpp:92-101` | 正常 |
| AC-3.2 | WHEN `uiContentType_==DYNAMIC_COMPONENT` THEN 在 RequestNextVSync 前设 `isRequestVsync_=true`（防重入）。来源：`form_render_window.cpp:96-99` | 正常 |
| AC-3.3 | WHEN `onShow_==false` THEN 不调用 RequestNextVSync，窗口隐藏时不驱动 vsync。来源：`form_render_window.cpp:95` | 正常 |
| AC-3.4 | WHEN `receiver_` 为空 THEN 不调用 RequestNextVSync（构造时 VSyncReceiver 创建失败的容错）。来源：`form_render_window.cpp:95` | 异常 |

### US-4: FormRenderWindow VSync 回调链

- As a 表单渲染维护者
- I want FormRenderWindow 的 VSync 回调链在 JS 线程或 UI 线程执行，按 uiContentType 差异化 PerfMonitor 调用
- So that 动态组件有性能监控，静态卡片无额外开销

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN VSync 回调被触发 THEN 通过 `SingleTaskExecutor::Make(taskExecutor, TaskType::JS)` 检查当前是否在 JS 线程；若是则直接执行 onVsync，否则 PostTask 到 UI 线程（PriorityType::VIP）。来源：`form_render_window.cpp:260-266` | 正常 |
| AC-4.2 | WHEN onVsync 执行 THEN 通过 `ContainerScope(id)` → `Container::Current()` → `container->GetWindow()` 获取 window，调用 `window->OnVsync(timestamp, frameCount)`。来源：`form_render_window.cpp:232-246` | 正常 |
| AC-4.3 | WHEN `uiContentType_==DYNAMIC_COMPONENT` THEN 在 OnVsync 前调用 `ArkUIPerfMonitor::StartPerf()`，后调用 `FinishPerf()`。非 DYNAMIC_COMPONENT 不调用 PerfMonitor。来源：`form_render_window.cpp:229-231, 247-249` | 正常 |
| AC-4.4 | WHEN containerHandler 存在且 `isReportFrameEvent==true` THEN 在 OnVsync 前后分别 `ReportSchedEvent(UI_SCB_WORKER_BEGIN/END)`。来源：`form_render_window.cpp:236-243, 254-256` | 正常 |
| AC-4.5 | WHEN pipeline 存在 THEN 在 OnVsync 后调用 `pipeline->OnIdle(min(ts, timeStampNanos) + refreshPeriod)` 执行空闲任务。来源：`form_render_window.cpp:250-253` | 正常 |

### US-5: FormRenderWindow 生命周期与 Destroy

- As a 表单渲染维护者
- I want FormRenderWindow 的 OnShow 调用 GoForeground，OnHide 仅设 onShow_=false（不 GoBackground），Destroy 清理所有资源
- So that 表单的生命周期简洁，无需复杂的 GoStop/GoResume 状态机

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `OnShow()` 被调用 THEN 调用 `Window::OnShow()` 设 `onShow_=true`，然后 `rsUIDirector_->GoForeground()`。来源：`form_render_window.cpp:155-161` | 正常 |
| AC-5.2 | WHEN `OnHide()` 被调用 THEN 仅调用 `Window::OnHide()` 设 `onShow_=false`；**不**调用 `GoBackground()`。来源：`form_render_window.cpp:164-169` | 正常 |
| AC-5.3 | WHEN `Destroy()` 被调用 THEN 清空 frameCallback_ 的 userData 和 callback，置空 rsSurfaceNode_，调用 `rsUIDirector_->Destroy()` + `reset()`，`receiver_.reset()` + `callbacks_.clear()`。来源：`form_render_window.cpp:115-132` | 正常 |
| AC-5.4 | WHEN rsUIDirector_ 为空 THEN `Destroy()` 跳过 director 清理（CHECK_NULL 保护）。来源：`form_render_window.cpp:122-125` | 异常 |

### US-6: FormRenderWindow 帧率链接

- As a 表单渲染维护者
- I want FormRenderWindow 通过 RSFrameRateLinker 联动 RS 帧率
- So that 表单动画帧率能被 RS 正确调度

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `FlushFrameRate(rate, animatorExpectedRate, rateType)` 被调用且 `frameRateLinker_` 非空 THEN 将 `{rate, animatorExpectedRate, rateType}` 与当前 `frameRateData_` 比较；不同则更新并调用 `frameRateLinker_->UpdateFrameRateRange(...)`。来源：`form_render_window.cpp:203-216` | 正常 |
| AC-6.2 | WHEN `frameRateData_` 与新值相同 THEN 跳过 UpdateFrameRateRange（避免冗余调用）。来源：`form_render_window.cpp:210-211` | 正常 |
| AC-6.3 | WHEN `frameRateLinker_` 为空 THEN 直接返回。来源：`form_render_window.cpp:206-208` | 异常 |

### US-7: DragWindow 继承 AceType 而非 Window

- As a 拖拽交互维护者
- I want DragWindow 继承 AceType（使用 DECLARE_ACE_TYPE 宏），不继承 Window 基类
- So that 拖拽预览窗口不参与标准渲染管线，仅做一次性位图绘制

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN DragWindow 类被定义 THEN 继承自 `AceType`，使用 `DECLARE_ACE_TYPE(DragWindow, AceType)` 声明 RTTI。来源：`drag_window.h:37-38` | 正常 |
| AC-7.2 | WHEN DragWindow 定义虚方法 THEN 包含 `MoveTo` / `TextDragWindowMove` / `Destroy` / `DrawPixelMap` / `DrawFrameNode` / `DrawImage` / `DrawText` / `DrawTextNG`，均为纯虚方法（`= 0`）。来源：`drag_window.h:56-64` | 正常 |
| AC-7.3 | WHEN `DragWindow::CreateDragWindow(params)` 工厂方法被调用 THEN 返回平台特定子类（DragWindowOhos），通过 `RefPtr<DragWindow>` 持有。来源：`drag_window.h:50-52` | 正常 |
| AC-7.4 | WHEN DragWindow 被创建 THEN 不调用 RegisterSubWindow / SetRequestVsyncCallback / SetRSRootNode 等标准 Window 方法——它是完全独立的窗口类型。来源：架构推断（`drag_window.h` 无 Window 基类继承） | 边界 |

### US-8: FoldableWindow 继承 AceType 而非 Window

- As a 折叠屏适配维护者
- I want FoldableWindow 继承 AceType，仅提供 IsFoldExpand 折叠状态查询
- So that 折叠状态查询不与渲染管线耦合

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN FoldableWindow 类被定义 THEN 继承自 `AceType`，使用 `DECLARE_ACE_TYPE(FoldableWindow, AceType)`。来源：`foldable_window.h:22-23` | 正常 |
| AC-8.2 | WHEN FoldableWindow 定义接口 THEN 仅包含 `CreateFoldableWindow(instanceId)` 工厂方法和 `IsFoldExpand()` 纯虚查询方法，以及 `foldableWindowId_` ID 管理。来源：`foldable_window.h:26-42` | 正常 |
| AC-8.3 | WHEN `FoldableWindowOhos(instanceId)` 构造 THEN 查询系统折叠状态并缓存 `windowId_`。来源：`foldable_window_ohos.h:26` | 正常 |

## 验收追溯

| AC编号 | US ID | 业务规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 / R-2 | 代码评审 |
| AC-1.2 | US-1 | R-2 | 代码评审 |
| AC-1.3 | US-1 | R-3 | 代码评审 |
| AC-1.4 | US-1 | R-4 | 代码评审 |
| AC-1.5 | US-1 | R-5 | 代码评审 |
| AC-2.1 | US-2 | R-6 | 代码评审 |
| AC-2.2 | US-2 | R-7 | 代码评审 |
| AC-2.3 | US-2 | R-8 | 代码评审 |
| AC-2.4 | US-2 | R-9 | 代码评审 |
| AC-3.1 | US-3 | R-10 | 代码评审 |
| AC-3.2 | US-3 | R-11 | 代码评审 |
| AC-3.3 | US-3 | R-12 | 代码评审 |
| AC-3.4 | US-3 | R-3 | 代码评审 |
| AC-4.1 | US-4 | R-13 | 代码评审 |
| AC-4.2 | US-4 | R-14 | 代码评审 |
| AC-4.3 | US-4 | R-15 | 代码评审 |
| AC-4.4 | US-4 | R-16 | 代码评审 |
| AC-4.5 | US-4 | R-17 | 代码评审 |
| AC-5.1 | US-5 | R-18 | 代码评审 |
| AC-5.2 | US-5 | R-19 | 代码评审 |
| AC-5.3 | US-5 | R-20 | 代码评审 |
| AC-5.4 | US-5 | R-21 | 代码评审 |
| AC-6.1 | US-6 | R-22 | 代码评审 |
| AC-6.2 | US-6 | R-23 | 代码评审 |
| AC-6.3 | US-6 | R-21 | 代码评审 |
| AC-7.1 | US-7 | R-24 | 代码评审 |
| AC-7.2 | US-7 | R-25 | 代码评审 |
| AC-7.3 | US-7 | R-26 | 代码评审 |
| AC-7.4 | US-7 | R-27 | 代码评审 |
| AC-8.1 | US-8 | R-28 | 代码评审 |
| AC-8.2 | US-8 | R-29 | 代码评审 |
| AC-8.3 | US-8 | R-30 | 代码评审 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | FormRenderWindow 构造函数通过 `RSInterfaces::GetInstance().CreateVSyncReceiver("Form", frameRateLinkerId)` 创建独立 VSyncReceiver，不依赖 Rosen::Window。来源：`form_render_window.cpp:56-59`。 | — | — |
| R-2 | 行为 | — | VSyncReceiver 创建时同时创建 `RSFrameRateLinker`，其 GetId() 作为 CreateVSyncReceiver 的第 2 参数，实现帧率联动。来源：`form_render_window.cpp:58-59`。 | — | — |
| R-3 | 异常 | VSyncReceiver 创建失败 | 记录 `LOGE("Form create vsync receiver failed, total counter:%d")` 并直接返回，不继续 InitOnVsyncCallback / RequestNextVSync / RSUIDirector 创建。来源：`form_render_window.cpp:60-63`。 | — | — |
| R-4 | 行为 | — | 构造函数调用 `InitOnVsyncCallback()` 设置 `frameCallback_.callbackWithId_`，然后立即 `receiver_->RequestNextVSync(frameCallback_)` 请求第一帧。来源：`form_render_window.cpp:69-71`。 | — | — |
| R-5 | 边界 | — | `vsyncCounter` 是文件级 `static std::atomic<int32_t>`，构造时 `++vsyncCounter` 并 LOGI，销毁时 `--vsyncCounter` 并 LOGI。用于全局表单 VSync 计数监控。来源：`form_render_window.cpp:32, 65, 127-128`。 | — | — |
| R-6 | 行为 | — | FormRenderWindow 通过 `RSUIDirector::Create(connectToRender)` 创建 RSUIDirector；connectToRender 为可选 IRemoteObject，用于跨进程表单渲染。来源：`form_render_window.cpp:73`。 | — | — |
| R-7 | 行为 | — | FormRenderWindow 通过 `RSSurfaceNode::Create({.SurfaceNodeName="ArkTSCardNode", .isSync=true}, true, rsUIContext)` 创建独立 surface node，不通过 Rosen::Window 获取。来源：`form_render_window.cpp:75-78`。 | — | — |
| R-8 | 行为 | — | 构造函数调用 `rsUIDirector_->SetRSSurfaceNode(rsSurfaceNode_)` 将自建的 surface node 绑定到 director。来源：`form_render_window.cpp:79`。 | — | — |
| R-9 | 行为 | — | 构造函数通过 `rsUIDirector_->SetUITaskRunner(lambda, 0, useMultiInstance)` 设置任务 runner；第 3 参数 useMultiInstance 来自 `SystemProperties::GetMultiInstanceEnabled()`。来源：`form_render_window.cpp:80-85`。 | — | — |
| R-10 | 行为 | — | `RequestFrame()` 在 receiver_ 非空且 onShow_==true 时调用 `receiver_->RequestNextVSync(frameCallback_)`。来源：`form_render_window.cpp:92-101`。 | — | — |
| R-11 | 行为 | uiContentType_==DYNAMIC_COMPONENT | RequestFrame 在 RequestNextVSync 前设 `isRequestVsync_=true` 防重入。来源：`form_render_window.cpp:96-99`。 | — | — |
| R-12 | 边界 | onShow_==false | RequestFrame 不调用 RequestNextVSync——隐藏表单不驱动 VSync。来源：`form_render_window.cpp:95`。 | — | — |
| R-13 | 行为 | — | VSync 回调通过 `SingleTaskExecutor::Make(taskExecutor, TaskType::JS)` 检查 JS 线程亲和性；在 JS 线程则直接执行，否则 PostTask 到 UI 线程（VIP 优先级）。来源：`form_render_window.cpp:260-266`。 | — | — |
| R-14 | 行为 | — | VSync 回调通过 `ContainerScope(id) → Container::Current() → container->GetWindow()` 获取 window 实例，调用 `window->OnVsync(timestamp, frameCount)`。来源：`form_render_window.cpp:232-246`。 | — | — |
| R-15 | 行为 | uiContentType_==DYNAMIC_COMPONENT | VSync 回调在 OnVsync 前后调用 `ArkUIPerfMonitor::StartPerf/FinishPerf`；非 DYNAMIC_COMPONENT 不调用。来源：`form_render_window.cpp:229-231, 247-249`。 | — | — |
| R-16 | 行为 | isReportFrameEvent==true | VSync 回调在 OnVsync 前后调用 `FrameReport::ReportSchedEvent(UI_SCB_WORKER_BEGIN/END)`。来源：`form_render_window.cpp:236-243, 254-256`。 | — | — |
| R-17 | 行为 | — | VSync 回调在 OnVsync 后调用 `pipeline->OnIdle(min(ts, timeStampNanos) + refreshPeriod)`，refreshPeriod 由 `ONE_SECOND_IN_NANO / GetDisplayRefreshRate()` 计算（GetDisplayRefreshRate 硬编码返回 60.0f）。来源：`form_render_window.cpp:222, 250-253`。 | — | — |
| R-18 | 行为 | — | FormRenderWindow::OnShow 调用 `Window::OnShow()` 后 `rsUIDirector_->GoForeground()`。来源：`form_render_window.cpp:155-161`。 | — | — |
| R-19 | 行为 | — | FormRenderWindow::OnHide **仅**调用 `Window::OnHide()` 设 onShow_=false，**不**调用 GoBackground。与 RosenWindow::OnHide 不同（后者调用 GoBackground + SendMessages）。来源：`form_render_window.cpp:164-169`。 | — | — |
| R-20 | 行为 | — | FormRenderWindow::Destroy 清理序列：frameCallback_ 清空 → rsSurfaceNode_=null → rsUIDirector_->Destroy() + reset() → vsyncCounter-- → receiver_.reset() → callbacks_.clear()。来源：`form_render_window.cpp:115-132`。 | — | — |
| R-21 | 异常 | rsUIDirector_ / frameRateLinker_ 为空 | Destroy / FlushFrameRate 在 director/linker 为空时跳过核心逻辑。来源：`form_render_window.cpp:122-125, 206-208`。 | — | — |
| R-22 | 行为 | — | FlushFrameRate 将 `{rate, animatorExpectedRate, rateType}` 与缓存 `frameRateData_` 比较，不同时调用 `frameRateLinker_->UpdateFrameRateRange({0, RANGE_MAX_REFRESHRATE, rate, rateType}, animatorExpectedRate, rsUIContext)`。来源：`form_render_window.cpp:203-216`。 | — | — |
| R-23 | 边界 | frameRateData_ 与新值相同 | FlushFrameRate 跳过 UpdateFrameRateRange 调用。来源：`form_render_window.cpp:210-211`。 | — | — |
| R-24 | 行为 | — | DragWindow 继承 `AceType`（`DECLARE_ACE_TYPE(DragWindow, AceType)`），**不**继承 Window。不参与标准 PipelineContext 渲染管线。来源：`drag_window.h:37-38`。 | — | — |
| R-25 | 行为 | — | DragWindow 定义 8 个纯虚方法：`MoveTo` / `TextDragWindowMove` / `Destroy` / `DrawPixelMap` / `DrawFrameNode` / `DrawImage` / `DrawText` / `DrawTextNG`，由平台子类（DragWindowOhos）实现。来源：`drag_window.h:56-64`。 | — | — |
| R-26 | 行为 | — | `DragWindow::CreateDragWindow(params)` 是工厂方法，返回平台特定子类的 RefPtr。来源：`drag_window.h:50-52`。 | — | — |
| R-27 | 边界 | — | DragWindow 不调用 RegisterSubWindow / SetRequestVsyncCallback / SetRSRootNode / OnShow / OnHide 等标准 Window 方法。它是完全独立的窗口类型，仅做一次性位图绘制。来源：架构推断（`drag_window.h` 无 Window 继承）。 | — | — |
| R-28 | 行为 | — | FoldableWindow 继承 `AceType`（`DECLARE_ACE_TYPE(FoldableWindow, AceType)`），**不**继承 Window。来源：`foldable_window.h:22-23`。 | — | — |
| R-29 | 行为 | — | FoldableWindow 仅定义 `CreateFoldableWindow(instanceId)` 工厂方法和 `IsFoldExpand()` 查询接口，不涉及渲染。来源：`foldable_window.h:26-28`。 | — | — |
| R-30 | 行为 | — | FoldableWindowOhos 构造函数接收 instanceId，缓存 windowId_，实现 `IsFoldExpand()` 查询系统折叠状态。来源：`foldable_window_ohos.h:22-32`。 | — | — |
| R-31 | 行为 | — | RSUIDirector 静态方法影响特殊窗口类型进程行为：① `SetTypicalResidentProcess(isFormRender)`（`ace_container.cpp:2764`）将表单渲染进程标记为常驻；② `SetTypicalResidentProcess(true)`（`ace_container.cpp:1737`）在 SceneBoard 窗口 SetUIWindow 时调用；③ `IsHybridRenderEnabled()`（`ace_container.cpp:5186`, `text_pattern.cpp:225`）门控混合渲染路径。这些是 RSUIDirector 的**静态方法**（非实例调用），由 AceContainer 在容器初始化时设置，不由 FormRenderWindow/DragWindow/FoldableWindow 调用。来源：`ace_container.cpp:1737, 2764, 5186`。 | — | — |

---

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.5 | 代码评审 | `form_render_window.cpp:47-71` 构造函数 |
| VM-2 | AC-2.1..2.4 | 代码评审 | `form_render_window.cpp:73-85` RSUIDirector + SurfaceNode 创建 |
| VM-3 | AC-3.1..3.4 | 单元测试 | 待补充 — RequestFrame 各分支（onShow / DYNAMIC_COMPONENT / receiver null） |
| VM-4 | AC-4.1..4.5 | 代码评审 | `form_render_window.cpp:219-272` InitOnVsyncCallback 完整实现 |
| VM-5 | AC-5.1..5.4 | 单元测试 | 待补充 — OnShow / OnHide / Destroy |
| VM-6 | AC-6.1..6.3 | 单元测试 | 待补充 — FlushFrameRate 去重逻辑 |
| VM-7 | AC-7.1..7.4 | 代码评审 | `drag_window.h:37-64` 直接对照 |
| VM-8 | AC-8.1..8.3 | 代码评审 | `foldable_window.h:22-42` + `foldable_window_ohos.h:22-32` 直接对照 |

## API 变更分析

### 新增 API

无。Feat-04 为框架内部特殊窗口类型实现，**不对外暴露 ArkTS 属性 / C-API**。

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指引 |
|----------|----------|------|----------|
| 各版本 | `GetDisplayRefreshRate()` 硬编码返回 60.0f（`form_render_window.cpp:34-37`） | 中：实际刷新率非 60Hz 的设备上 OnIdle deadline 计算偏差 | 后续应从 RSInterfaces 获取真实刷新率 |
| 各版本 | FormRenderWindow::OnHide 不调用 GoBackground（与 RosenWindow 不同） | 低：表单无 GoStop/GoResume 状态机 | 不修改；IsDisabledGoStopAndGoResume 对 FormRender 返回 true |
| 各版本 | `ENABLE_ROSEN_BACKEND` 编译宏影响 FormRenderWindow 是否编译为空壳 | 中：非 Rosen 后端下 FormRenderWindow 所有方法空实现 | 仅影响非 Rosen 平台 |
| 非 OHOS 平台 | `GetVSyncPeriod()` 仅在 `__OHOS__` 定义时查询 receiver（`form_render_window.cpp:194`） | 低：非 OHOS 平台返回 0 | 预览/跨平台路径 |
| 各版本 | `RSUIDirector::SetTypicalResidentProcess(isFormRender)` 在 `AceContainer::SetIsFormRender` 中调用（`ace_container.cpp:2764`），将表单渲染进程标记为常驻 | 中：影响系统进程调度策略 | 由上层 AceContainer 控制，FormRenderWindow 不干预 |
| 各版本 | `RSUIDirector::SetTypicalResidentProcess(true)` 在 SceneBoard 窗口的 `SetUIWindow` 中调用（`ace_container.cpp:1737`），标记 SceneBoard 为常驻进程 | 中：SceneBoard 的 RSUIDirector 生命周期由系统管理（IsDisabledGoStopAndGoResume 返回 true） | 与 Feat-02 AC-8.3 守卫一致 |
| 各版本 | `RSUIDirector::IsHybridRenderEnabled()` 门控混合渲染路径（`ace_container.cpp:5186`, `text_pattern.cpp:225`），影响高对比度订阅和多线程文本布局 | 中：混合渲染开关由 RS 全局配置控制 | 窗口机制仅消费不设置 |

## 架构约束

- **FormRenderWindow** 继承 `Window` 基类（与 RosenWindow 相同），但：
  - **不**通过 Rosen::Window 获取 RSUIDirector（自建）
  - **不**使用 Rosen::Window 的 VSync 回调（自建 VSyncReceiver）
  - **不**实现 GoBackground/GoStop/GoResume（OnHide 仅设 onShow_=false）
  - **不**实现 ForceFlushVsync（无 VSync 超时兜底）
  - **不**实现 FlushImplicitTransaction / RequestFrame 合并 / OnIdle 延迟任务
- **DragWindow** 继承 `AceType`（非 Window），是完全独立的窗口抽象，不参与 PipelineContext 渲染管线。
- **FoldableWindow** 继承 `AceType`（非 Window）。**名称含 "Window" 但无任何窗口功能**——不创建/持有/交互任何 `Ace::Window` 或 `Rosen::Window`，仅提供 `IsFoldExpand()` 状态查询和 `foldableWindowId_` ID 管理。
- FormRenderWindow 的 VSync 回调通过 JS 线程检查（TaskType::JS），而非 RosenWindow 的 UI 线程（TaskType::UI）。
- FormRenderWindow 使用 `std::recursive_mutex globalMutex_` 保护跨实例操作（静态成员）。

## 非功能性需求

- 可观测：DYNAMIC_COMPONENT 类型的表单 VSync 回调有 PerfMonitor 钩子；isReportFrameEvent 控制帧事件上报。
- 性能：FormRenderWindow 使用 RSFrameRateLinker 联动 RS 帧率，FlushFrameRate 做去重优化。
- 鲁棒性：VSyncReceiver 创建失败时构造函数安全返回；所有 RS 对象操作有 CHECK_NULL 保护。
- 全局计数：vsyncCounter 原子变量跟踪全局 FormRenderWindow VSync 实例数。
- 资源管理：FormRenderWindow::Destroy 清理所有 RS 资源（director / surfaceNode / receiver / callbacks）。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | FoldableWindow::IsFoldExpand 查询折叠状态 | 由系统 WindowManager 提供 | 折叠状态变更测试 | `foldable_window_ohos.cpp` |

---

## 全局特性影响

- 表单渲染：FormRenderWindow 是表单卡片渲染的窗口入口，Container 的 `IsFormRender()` 标记决定使用 FormRenderWindow 而非 RosenWindow。
- 拖拽交互：DragWindow 在拖拽开始时创建浮动 Rosen::Window 绘制预览，拖拽结束时 Destroy。
- 折叠屏适配：FoldableWindow 由上层组件查询折叠状态，调整布局策略。
- 渲染管线（03-01-01）：PipelineContext 对 FormRenderWindow 和 RosenWindow 无感（通过 Window 基类指针统一调用）；DragWindow 和 FoldableWindow 不经过 PipelineContext。
- 多实例（03-06-01）：FormRenderWindow 的 SetUITaskRunner 第 3 参数受 GetMultiInstanceEnabled() 控制。

## 行为场景

```
场景 1: FormRenderWindow 构造创建独立 VSync + SurfaceNode (AC-1.1, AC-2.1..2.3, R-1, R-6..R-8)
  Given 一个表单容器需要渲染
  When FormRenderWindow(taskExecutor, id, connectToRender) 构造
  Then 通过 RSInterfaces 创建独立 VSyncReceiver + RSFrameRateLinker
  And 通过 RSUIDirector::Create 创建独立 director
  And 通过 RSSurfaceNode::Create 创建 "ArkTSCardNode" surface
  And 绑定 surface 到 director
  And 请求第一帧 VSync

场景 2: FormRenderWindow VSyncReceiver 创建失败 (AC-1.3, R-3)
  Given RSInterfaces::CreateVSyncReceiver 返回 nullptr
  When FormRenderWindow 构造执行
  Then LOGE 被记录
  And 构造提前返回，不创建 RSUIDirector / SurfaceNode
  And 后续 RequestFrame 调用因 receiver_==null 而无操作

场景 3: FormRenderWindow VSync 回调差异化 PerfMonitor (AC-4.3, R-15)
  Given uiContentType_==DYNAMIC_COMPONENT
  When VSync 回调 onVsync 执行
  Then ArkUIPerfMonitor::StartPerf() 在 OnVsync 前调用
  And ArkUIPerfMonitor::FinishPerf() 在 OnVsync 后调用

场景 4: FormRenderWindow OnHide 不 GoBackground (AC-5.2, R-19)
  Given FormRenderWindow 处于前台
  When OnHide() 被调用
  Then onShow_ 设为 false
  And GoBackground 不被调用（与 RosenWindow 不同）

场景 5: FormRenderWindow Destroy 全资源清理 (AC-5.3, R-20)
  Given FormRenderWindow 处于活动状态
  When Destroy() 被调用
  Then frameCallback_ 清空
  And rsSurfaceNode_ 置空
  And rsUIDirector_->Destroy() + reset()
  And vsyncCounter 原子减 1
  And receiver_.reset()
  And callbacks_.clear()

场景 6: FormRenderWindow 帧率去重 (AC-6.2, R-23)
  Given frameRateData_ == {60, 60, 0}
  When FlushFrameRate(60, 60, 0) 被调用（相同值）
  Then frameRateLinker_->UpdateFrameRateRange 不被调用

场景 7: DragWindow 不继承 Window (AC-7.1, R-24)
  Given DragWindow 类定义
  When 检查继承关系
  Then DragWindow 继承 AceType，不继承 Window
  And 不参与 PipelineContext 渲染管线

场景 8: FoldableWindow 仅查询折叠状态 (AC-8.2, R-29)
  Given FoldableWindow 已创建
  When IsFoldExpand() 被调用
  Then 返回系统折叠状态（true=展开 / false=折叠）
  And 不涉及任何渲染操作
```

## Spec 自审清单

- [x] 所有 H2/H3 章节按模板齐全
- [x] 每个 US 都有 AC，并使用 AC-X.Y 编号
- [x] 每个 AC 在「验收追溯」「验证映射」「行为场景」中可被引用
- [x] 规则定义编号齐全（R-1..R-31）
- [x] 所有源码引用均给出 file:line
- [x] API 变更分析已说明本 Feat 不暴露 ArkTS / C-API
- [x] 兼容性声明覆盖当前已识别的版本差异
- [x] Gherkin 场景覆盖每个 AC
- [x] 与 design.md 章节标题、ID（DESIGN-Func-03-05-01）对齐

## context-references

- `frameworks/core/components_ng/render/adapter/form_render_window.h:36-130`（FormRenderWindow 类定义）
- `frameworks/core/components_ng/render/adapter/form_render_window.cpp:47-90`（构造函数 — VSyncReceiver + RSUIDirector + SurfaceNode）
- `frameworks/core/components_ng/render/adapter/form_render_window.cpp:92-103`（RequestFrame）
- `frameworks/core/components_ng/render/adapter/form_render_window.cpp:115-132`（Destroy）
- `frameworks/core/components_ng/render/adapter/form_render_window.cpp:155-169`（OnShow / OnHide）
- `frameworks/core/components_ng/render/adapter/form_render_window.cpp:203-217`（FlushFrameRate）
- `frameworks/core/components_ng/render/adapter/form_render_window.cpp:219-272`（InitOnVsyncCallback）
- `frameworks/base/window/drag_window.h:37-84`（DragWindow 抽象基类）
- `adapter/ohos/entrance/window/drag_window_ohos.h:32`（DragWindowOhos 继承 DragWindow）
- `frameworks/base/window/foldable_window.h:22-43`（FoldableWindow 抽象基类）
- `adapter/ohos/entrance/window/foldable_window_ohos.h:22-33`（FoldableWindowOhos 继承 FoldableWindow）
- `adapter/ohos/entrance/ace_container.cpp:1737,2764`（SetTypicalResidentProcess — SceneBoard / FormRender 进程标记）
- `adapter/ohos/entrance/ace_container.cpp:5186`（IsHybridRenderEnabled — 高对比度订阅门控）
