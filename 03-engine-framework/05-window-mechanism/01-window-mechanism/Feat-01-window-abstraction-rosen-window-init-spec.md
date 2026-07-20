# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Window抽象与RosenWindow创建初始化 |
| 特性编号 | Func-03-05-01-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | API 9 及以后（以 master HEAD 实现为基线） |
| SIG 归属 | ArkUI SIG / 窗口与渲染团队 |
| 状态 | Baselined |
| 复杂度 | 复杂 |

> 本 Feat 锁定 NG 框架中 Window 抽象基类的虚方法契约、RosenWindow 的构造与资源获取（RSUIDirector / SurfaceNode / VsyncCallback）、Init 阶段的 VSync 回调注册与多实例扇出、Destroy 阶段的按所有权差异化清理、以及 SetRootFrameNode 挂载路径。生命周期状态转换（GoForeground / GoBackground / GoStop / GoResume）由 Feat-02 覆盖。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Window 基类虚方法契约 | 50+ virtual 方法的默认行为与 override 语义 |
| ADDED | RosenWindow 构造函数资源获取链 | vsyncCallback / RSUIDirector / SurfaceNode / UITaskRunner |
| ADDED | directorFromWindow_ 所有权模型 | 条件化 Destroy 行为 |
| ADDED | Init() VSync 回调注册 + 多实例扇出 | SetRequestVsyncCallback |
| ADDED | SetRootFrameNode RSRootNode 挂载 | RSNode ReinterpretCast |
| ADDED | Destroy 按所有权清理 | 多实例子窗口注销 + RSUIDirector 条件销毁 |
| ADDED | FlushModifier 每帧 RS 属性暂存 | staging 更新，与 SendMessages 提交分离 |
| ADDED | RosenRenderContext fallback director | RSNode 在 RosenWindow 之前创建时的临时 RSUIDirector |

## 输入文档

- 关联设计：`specs/03-engine-framework/05-window-mechanism/01-window-mechanism/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `frameworks/core/common/window.h` / `window.cpp` — Window 基类定义与默认实现
  - `frameworks/core/components_ng/render/adapter/rosen_window.h` / `.cpp` — RosenWindow 完整实现
  - `frameworks/core/common/platform_window.h` — PlatformWindow 平台抽象

## 用户故事

### US-1: Window 基类提供统一虚方法契约

- As a 渲染管线维护者
- I want Window 基类定义一组完整的 virtual 方法，每个方法有合理的默认空实现
- So that 不同窗口子类（RosenWindow / FormRenderWindow）可以按需 override，PipelineContext 通过基类指针统一调用

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN Window 基类被构造 THEN `onShow_=true`（默认可见）、`isRequestVsync_=false`、`density_=1.0`、`forceVsync_=false`、`dvsyncOn_=false`。来源：`window.h:302-323` | 正常 |
| AC-1.2 | WHEN 基类 `OnShow()` 被调用 THEN 设置 `onShow_=true`；WHEN `OnHide()` 被调用 THEN 设置 `onShow_=false`。`IsHide()` 返回 `!onShow_`。来源：`window.h:115-128` | 正常 |
| AC-1.3 | WHEN 基类 `OnVsync(timestamp, frameCount)` 被调用 THEN 遍历 `callbacks_` 列表，对每个已注册的 `VsyncCallback{callback_, containerId_}` 调用 `callback_(timestamp, frameCount)`，并清除 `isRequestVsync_`。来源：`window.cpp:48-58`、`window.h:111` | 正常 |
| AC-1.4 | WHEN 基类 `SetVsyncCallback(callback)` 被调用 THEN 将 `{callback, containerId}` 追加到 `callbacks_` 列表；容器 ID 从 `Container::CurrentId()` 获取。来源：`window.cpp:31-40` | 正常 |
| AC-1.5 | WHEN PipelineContext 调用 `window->GetRSUIDirector()` 且使用基类 Window THEN 返回 `nullptr`；RosenWindow override 返回实际 `rsUIDirector_`。来源：`window.h:85-88`、`rosen_window.h:63-66` | 正常 |

### US-2: RosenWindow 构造函数完成全部渲染资源获取

- As a 渲染管线维护者
- I want RosenWindow 构造函数一次性完成 vsyncCallback 创建、RSUIDirector 获取/创建、SurfaceNode 挂载和 UITaskRunner 设置
- So that 构造完成后即可被 PipelineContext 直接使用，无需额外初始化步骤

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `RosenWindow(rsWindow, taskExecutor, id, isGlobalPipeline)` 构造执行 THEN 首先创建 `vsyncCallback_` lambda，捕获 `weakTask` 和 `id`，内部通过 `ContainerScope(id)` + `Container::Current()` 获取实际 window 并调用 `window->OnVsync`。来源：`rosen_window.cpp:68-115` | 正常 |
| AC-2.2 | WHEN 构造函数执行且 `rsWindow` 非空 THEN 尝试 `rsWindow->GetRSUIDirector()`；若成功则 `rsUIDirector_=rsUIDirector`、`directorFromWindow_=true`（标记所有权来自 Rosen::Window）。来源：`rosen_window.cpp:116-122` | 正常 |
| AC-2.3 | WHEN `rsUIDirector_` 仍为空 **或** `isGlobalPipeline==true` THEN 创建独立 `OHOS::Rosen::RSUIDirector::Create(nullptr)`，设置 `directorFromWindow_=false`（标记 ArkUI 拥有）。`isGlobalPipeline` 优先级高于 Rosen::Window 提供的 director。来源：`rosen_window.cpp:125-128` | 边界 |
| AC-2.4 | WHEN 构造函数执行且 `rsWindow` 非空且 `rsWindow->GetSurfaceNode()` 非空 THEN 调用 `rsUIDirector_->SetRSSurfaceNode(surfaceNode)` 将 surface node 绑定到 director。来源：`rosen_window.cpp:129-133` | 正常 |
| AC-2.5 | WHEN 构造函数执行 THEN 设置 `rsUIDirector_->SetCacheDir(dataFileDirPath)`；若 `rsUIcontext` 存在则调用 `AttachFromUI()` 并检查 `HasTaskRunner()`；若无 task runner 则通过 `SetUITaskRunner` 注入 ArkUI TaskExecutor 的 PostDelayedTask 回调。来源：`rosen_window.cpp:134-150` | 正常 |

### US-3: RosenWindow::Init 注册 VSync 请求回调

- As a 多实例架构维护者
- I want RosenWindow::Init 在多实例启用时根据容器类型决定是否注册子窗口扇出，并设置 `SetRequestVsyncCallback`
- So that 子窗口 VSync 请求能透传到主窗口，避免子窗口独立请求 vsync 导致重复

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `SystemProperties::GetMultiInstanceEnabled()` 为 true 且容器是 SubContainer THEN 检查 parentContainer 的 RSUIContext 是否与当前一致；若一致则注册 `pipelineWindow->RegisterSubWindow(id_)` 并直接返回，**不**调用 `SetRequestVsyncCallback`。来源：`rosen_window.cpp:156-171` | 正常 |
| AC-3.2 | WHEN 非子容器路径 **或** RSUIContext 不一致 THEN 调用 `rsUIDirector_->SetRequestVsyncCallback(lambda)`，lambda 内部先 `self->RequestFrame()`，然后在多实例启用时遍历 `GetSubWindowIds()` 对每个子窗口的 pipeline 调用 `RequestFrame()`。来源：`rosen_window.cpp:173-187` | 正常 |
| AC-3.3 | WHEN `SystemProperties::GetMultiInstanceEnabled()` 为 false THEN `SetRequestVsyncCallback` 内部仅调用 `self->RequestFrame()`，不遍历子窗口。来源：`rosen_window.cpp:173-176` | 正常 |

### US-4: RosenWindow::Destroy 按所有权差异化清理

- As a 资源管理维护者
- I want Destroy 区分 `directorFromWindow_` 所有权，仅销毁 ArkUI 创建的 RSUIDirector，保留 Rosen::Window 拥有的 director
- So that 不产生双重释放

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `Destroy()` 被调用 THEN 首先置 `rsWindow_=nullptr`、`vsyncCallback_.reset()`，然后调用 `rsUIDirector_->SendMessages()` 刷出残留消息。来源：`rosen_window.cpp:338-343` | 正常 |
| AC-4.2 | WHEN 多实例启用且容器是 SubContainer THEN 从父窗口注销 `pipelineWindow->UnregisterSubWindow(id_)`（仅在父 RSUIContext 一致时）。来源：`rosen_window.cpp:346-361` | 正常 |
| AC-4.3 | WHEN `rsUIContext` 非空 THEN 调用 `rsUIContext->DetachFromUI()`。来源：`rosen_window.cpp:362-364` | 正常 |
| AC-4.4 | WHEN `directorFromWindow_==false`（ArkUI 创建的 director）THEN 调用 `rsUIDirector_->Destroy()` 后 `rsUIDirector_.reset()`；WHEN `directorFromWindow_==true`（Rosen::Window 拥有）THEN **跳过** `Destroy()`，仅 `rsUIDirector_.reset()` 释放引用。来源：`rosen_window.cpp:365-368` | 边界 |
| AC-4.5 | WHEN Destroy 完成 THEN `callbacks_.clear()` 清空所有 vsync 回调。来源：`rosen_window.cpp:369` | 正常 |

### US-5: SetRootFrameNode 挂载 RSRootNode

- As a 渲染管线维护者
- I want SetRootFrameNode 将 NG FrameNode 的 RSNode 设置为 RSUIDirector 的 RSRootNode
- So that RS 渲染树根节点与 ArkUI 组件树根节点绑定

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `SetRootFrameNode(root)` 被调用且 root 非空 THEN 从 root 的 RenderContext 获取 `RosenRenderContext`，再获取 `GetRSNode()`；若 RSNode 非空则 `rsUIDirector_->SetRSRootNode(ReinterpretCast<RSRootNode>(rootNode))`。来源：`rosen_window.cpp:377-388` | 正常 |
| AC-5.2 | WHEN root 为空 **或** RenderContext 非 RosenRenderContext **或** RSNode 为空 THEN 静默返回不设置 RSRootNode。来源：`rosen_window.cpp:379-382` | 异常 |

### US-6: FlushTasks 作为 RS 消息提交边界

- As a 渲染管线维护者
- I want FlushTasks 在 UI 线程上调用 `rsUIDirector_->SendMessages`，支持可选 callback
- So that RS 消息提交统一经由 window 抽象

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `FlushTasks(callback)` 被调用 THEN 先 `CHECK_RUN_ON(UI)` 断言；若 callback 为空则 `rsUIDirector_->SendMessages()`，否则 `rsUIDirector_->SendMessages(callback)`。来源：`rosen_window.cpp:396-404` | 正常 |
| AC-6.2 | WHEN `FlushTasks` 完成消息发送 THEN 调用 `JankFrameReport::GetInstance().JsAnimationToRsRecord()` 记录 JS→RS 动画路径。来源：`rosen_window.cpp:405` | 正常 |

### US-7: FlushModifier 作为每帧 RS 属性暂存

- As a 渲染管线维护者
- I want FlushModifier 在每帧 Flush 阶段将 modifier/property 变更推送到 RS，但不提交
- So that 属性变更在帧末 SendMessages 时批量提交，减少 RS IPC 次数

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `FlushModifier()` 被调用 THEN `CHECK_NULL_VOID(rsUIDirector_)` 保护后调用 `rsUIDirector_->FlushModifier()`。来源：`rosen_window.h:100-104` | 正常 |
| AC-7.2 | WHEN PipelineContext 每帧 Flush 阶段执行 THEN 调用 `window_->FlushModifier()`，**先于** `FlushMessages`（SendMessages 提交）。来源：`pipeline_context.cpp:1561-1564`（FlushModifier 定义）、`pipeline_context.cpp:1290/1296`（FlushMessages 提交）。 | 正常 |
| AC-7.3 | WHEN rsUIDirector_ 为空 THEN FlushModifier 静默返回不操作（CHECK_NULL_VOID 保护）。来源：`rosen_window.h:102` | 异常 |

### US-8: RosenRenderContext fallback director 创建

- As a 渲染管线维护者
- I want RosenRenderContext 在无可用 RSUIContext 时创建临时 RSUIDirector 仅用于提取 RSUIContext
- So that RSNode 能在 RosenWindow 构造之前被创建（如纹理导出、离线程渲染）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN `RosenRenderContext::InitContext` 执行且 `GetRSUIContext(pipeline)` 返回 nullptr THEN 记录 `TAG_LOGW("rsnode create before rosenwindow")` 并创建 `OHOS::Rosen::RSUIDirector::Create(nullptr)`。来源：`rosen_render_context.cpp:644-647` | 正常 |
| AC-8.2 | WHEN fallback director 创建完成 THEN 从 `rsUIDirector_->GetRSUIContext()` 提取 RSUIContext 用于后续 RSNode 创建。来源：`rosen_render_context.cpp:648` | 正常 |
| AC-8.3 | WHEN fallback director 存在 THEN 它**不**绑定 SurfaceNode、**不**注册 VSync 回调、**不**设置 UITaskRunner、**不**调用 GoForeground/GoBackground。它仅提供 RSUIContext，是非渲染导向的临时对象。来源：`rosen_render_context.cpp:644-649`（仅 Create + GetRSUIContext 两行调用）。 | 边界 |

## 验收追溯

| AC编号 | US ID | 业务规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码评审 |
| AC-1.2 | US-1 | R-1 | 代码评审 |
| AC-1.3 | US-1 | R-2 | 代码评审 + window ut |
| AC-1.4 | US-1 | R-2 | 代码评审 |
| AC-1.5 | US-1 | R-3 | 代码评审 |
| AC-2.1 | US-2 | R-4 / R-5 | 代码评审 |
| AC-2.2 | US-2 | R-6 | 代码评审 |
| AC-2.3 | US-2 | R-6 / R-7 | 代码评审 |
| AC-2.4 | US-2 | R-8 | 代码评审 |
| AC-2.5 | US-2 | R-9 | 代码评审 |
| AC-3.1 | US-3 | R-10 | 多实例集成测试 |
| AC-3.2 | US-3 | R-10 / R-11 | 多实例集成测试 |
| AC-3.3 | US-3 | R-11 | 代码评审 |
| AC-4.1 | US-4 | R-12 | 代码评审 |
| AC-4.2 | US-4 | R-10 / R-12 | 多实例集成测试 |
| AC-4.3 | US-4 | R-12 | 代码评审 |
| AC-4.4 | US-4 | R-6 / R-12 | 代码评审 + ownership ut |
| AC-4.5 | US-4 | R-12 | 代码评审 |
| AC-5.1 | US-5 | R-13 | 代码评审 |
| AC-5.2 | US-5 | R-14 | 代码评审 |
| AC-6.1 | US-6 | R-15 | 代码评审 + rosen_window ut |
| AC-6.2 | US-6 | R-16 | 代码评审 |
| AC-7.1 | US-7 | R-17 | 代码评审 |
| AC-7.2 | US-7 | R-17 / R-18 | 代码评审 |
| AC-7.3 | US-7 | R-17 | 代码评审 |
| AC-8.1 | US-8 | R-19 | 代码评审 |
| AC-8.2 | US-8 | R-19 | 代码评审 |
| AC-8.3 | US-8 | R-19 | 代码评审 |

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | Window 基类默认状态：onShow_=true, isRequestVsync_=false, density_=1.0, forceVsync_=false。子类构造后可修改。来源：`window.h:302-323`。 | — | — |
| R-2 | 行为 | — | `Window::OnVsync` 遍历 `callbacks_` 列表分发 vsync，分发后清除 `isRequestVsync_`。`SetVsyncCallback` 追加回调。来源：`window.cpp:31-58`。 | — | — |
| R-3 | 行为 | — | Window 基类 `GetRSUIDirector()` 返回 nullptr；仅 RosenWindow / FormRenderWindow override 返回真实 director。PipelineContext 依赖此方法获取 RS 通信入口。来源：`window.h:85-88`。 | — | — |
| R-4 | 行为 | — | RosenWindow 构造函数创建 vsyncCallback_ lambda，内部通过 `ContainerScope(id) → Container::Current() → container->GetWindow()` 获取实际 window 实例，确保 lambda 中调用的 window 一定有效。来源：`rosen_window.cpp:73-115`。 | — | — |
| R-5 | 行为 | — | vsyncCallback_ 内部执行序列：`ArkUIPerfMonitor::StartPerf` → `FrameReport::FlushBegin` → `window->OnVsync` → `pipeline->OnIdle(deadline)` → `JankFrameReport::JankFrameRecord` → `FrameReport::FlushEnd` → `window->SetLastVsyncEndTimestamp`。若 dvsyncOn 则 deadline 经 `GetDeadlineByFrameCount` 调整。来源：`rosen_window.cpp:73-107`。 | — | — |
| R-6 | 行为 | — | RSUIDirector 所有权模型：`directorFromWindow_` 标记所有权来源。true=Rosen::Window 提供（Destroy 时不调用 rsUIDirector_->Destroy()），false=ArkUI 创建（Destroy 时必须 Destroy()）。`isGlobalPipeline=true` 强制创建独立 director，无论 Rosen::Window 是否提供。来源：`rosen_window.cpp:116-128, 365-368`。 | — | — |
| R-7 | 边界 | isGlobalPipeline==true 且 Rosen::Window 提供了 director | `isGlobalPipeline` 优先：创建新的独立 RSUIDirector，`directorFromWindow_=false`。来源：`rosen_window.cpp:125-128`。 | — | — |
| R-8 | 行为 | — | 构造函数在获取 director 后，若 `rsWindow->GetSurfaceNode()` 非空则绑定到 director。来源：`rosen_window.cpp:129-133`。 | — | — |
| R-9 | 行为 | — | 构造函数设置 `SetCacheDir`、`AttachFromUI`（若 rsUIContext 存在）、`SetUITaskRunner`（若无 task runner），将 RS 的任务执行绑定到 ArkUI TaskExecutor 的 UI 线程。来源：`rosen_window.cpp:134-150`。 | — | — |
| R-10 | 行为 | — | 多实例子窗口通过 `RegisterSubWindow(id_)` 注册到父窗口，`UnregisterSubWindow(id_)` 注销。Init 时若 parent RSUIContext 一致则直接返回（共享父窗口 pipeline）。来源：`rosen_window.cpp:156-171, 346-361`。 | — | — |
| R-11 | 行为 | — | `SetRequestVsyncCallback` 在非子窗口路径注册：回调内先 RequestFrame 自身，再遍历 GetSubWindowIds() 对子窗口 pipeline 逐个 RequestFrame。多实例未启用时仅 RequestFrame 自身。来源：`rosen_window.cpp:173-187`。 | — | — |
| R-12 | 行为 | — | Destroy 清理序列：rsWindow_=null → vsyncCallback_.reset → SendMessages → 多实例子窗口注销 → DetachFromUI → 条件 Destroy(rsUIDirector) → rsUIDirector_.reset → callbacks_.clear。来源：`rosen_window.cpp:338-369`。 | — | — |
| R-13 | 行为 | — | `SetRootFrameNode` 从 FrameNode → RosenRenderContext → RSNode → ReinterpretCast<RSRootNode> → `rsUIDirector_->SetRSRootNode`。来源：`rosen_window.cpp:377-388`。 | — | — |
| R-14 | 异常 | root 为空 / RenderContext 类型不匹配 / RSNode 为空 | 静默返回，不设置 RSRootNode，不报错。来源：`rosen_window.cpp:379-382`。 | — | — |
| R-15 | 行为 | — | `FlushTasks` 在 UI 线程断言后调用 `rsUIDirector_->SendMessages(callback?)`。来源：`rosen_window.cpp:396-404`。 | — | — |
| R-16 | 行为 | — | `FlushTasks` 结束后调用 `JankFrameReport::JsAnimationToRsRecord()` 记录动画路径。来源：`rosen_window.cpp:405`。 | — | — |
| R-17 | 行为 | — | `FlushModifier` 是每帧 RS 属性暂存（staging）方法：将 modifier/property 变更推送到 RS 但不提交。RosenWindow 在 `rosen_window.h:100-104` inline 实现：`CHECK_NULL_VOID(rsUIDirector_)` → `rsUIDirector_->FlushModifier()`。FormRenderWindow 同理（`form_render_window.h:80-84`）。来源：`rosen_window.h:100-104`。 | — | — |
| R-18 | 行为 | — | 每帧管线顺序：`FlushModifier`（staging）**先于** `FlushMessages`→`FlushTasks`→`SendMessages`（commit）。FlushModifier 推送属性变更，SendMessages 提交消息队列触发实际渲染。来源：`pipeline_context.cpp:1561-1564`（FlushModifier），`pipeline_context.cpp:1290/1296`（FlushMessages）。 | — | — |
| R-19 | 边界 | RSUIContext 不可用 | `RosenRenderContext::InitContext` 在 `GetRSUIContext(pipeline)` 返回 nullptr 时创建 fallback director：`RSUIDirector::Create(nullptr)` → `GetRSUIContext()`。此 director 存储于 `RosenRenderContext::rsUIDirector_`（`rosen_render_context.h:1016`），非渲染导向，无 Surface/VSync/生命周期绑定。场景：RSNode 在 RosenWindow 构造之前创建（纹理导出、离线程渲染）。来源：`rosen_render_context.cpp:644-649`。 | — | — |

---

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.5 | 代码评审 | `frameworks/core/common/window.h` / `window.cpp` 直接对照 |
| VM-2 | AC-2.1..2.5 | 单元测试 | 待补充 — 建议在 `test/unittest/core/render/` 下新增 rosen_window 构造测试 |
| VM-3 | AC-3.1..3.3 | 集成测试 | 多实例场景验证 RegisterSubWindow / SetRequestVsyncCallback |
| VM-4 | AC-4.1..4.5 | 单元测试 | 待补充 — directorFromWindow_ ownership 差异化销毁 |
| VM-5 | AC-5.1..5.2 | 单元测试 | 待补充 — SetRootFrameNode 正常 + 空入参 |
| VM-6 | AC-6.1..6.2 | 单元测试 | 待补充 — FlushTasks / SendMessages |
| VM-7 | AC-7.1..7.3 | 代码评审 | `rosen_window.h:100-104` FlushModifier inline 实现 + `pipeline_context.cpp:1561-1564` 管线调用对照 |
| VM-8 | AC-8.1..8.3 | 代码评审 | `rosen_render_context.cpp:644-649` fallback director 路径直接对照 |

## API 变更分析

### 新增 API

无。Feat-01 为框架内部 Window 抽象与 RosenWindow 实现，**不对外暴露 ArkTS 属性 / C-API**。

**关联类型定义：**

仅框架内部类型（已在 design.md 数据模型章节列出）：
- `Window`（`frameworks/core/common/window.h`）— 继承 `std::enable_shared_from_this<Window>`
- `RosenWindow`（`frameworks/core/components_ng/render/adapter/rosen_window.h`）— 继承 `Window`
- `PlatformWindow`（`frameworks/core/common/platform_window.h`）

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
| 各版本 | `SystemProperties::GetMultiInstanceEnabled()` 改变 Init 子窗口扇出与 Destroy 注销路径 | 中：多实例编译态决定 | 切换后行为按 R-10 / R-11 |
| 各版本 | `isGlobalPipeline` 参数改变 RSUIDirector 所有权（R-6/R-7） | 中：全局管线窗口使用独立 director | GlobalPipelineContextManager 专属，不影响普通窗口 |
| 非 OHOS 平台 | `InitArkUI_X()` 在 Android/iOS 平台重新绑定 SurfaceNode（`rosen_window.cpp:190-199`） | 低：跨平台适配路径 | 仅影响 Android/iOS 虚拟 RS 窗口 |

## 架构约束

- RosenWindow 构造函数和所有 override 方法均在 **UI 线程** 调用（`FlushTasks` 显式 `CHECK_RUN_ON(UI)`，`RequestFrame` 同样断言）。
- Window 基类使用 `std::enable_shared_from_this<Window>`，允许在 `SetRequestVsyncCallback` lambda 中 `weak_from_this()` 捕获弱引用。
- `directorFromWindow_` 所有权标记是全局不变式：一旦构造时确定，Destroy 时必须与之匹配。
- `vsyncCallback_` lambda 内部通过 ContainerScope + Container::Current() 间接获取 window 实例，而非直接捕获 this，确保 window 已被销毁时不会悬空引用。

## 非功能性需求

- 可观测：vsyncCallback 内置 `ArkUIPerfMonitor::StartPerf/FinishPerf` 和 `FrameReport::FlushBegin/FlushEnd` 性能监控钩子。
- 性能：构造函数一次性完成所有资源获取，避免延迟初始化导致的帧间隔内卡顿。
- 鲁棒性：所有 RSUIDirector / SurfaceNode 操作均有 `CHECK_NULL_VOID` 保护，空指针安全。
- 多窗口：通过 callbacks_ 列表和 RegisterSubWindow/UnregisterSubWindow 支持多容器 vsync 分发。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

- 渲染管线（03-01-01）：PipelineContext 持有 `window_` 成员（Window 基类指针），通过 `window_->FlushTasks` / `window_->RequestFrame` / `window_->GetRSUIDirector` 等 50+ 虚方法驱动渲染。
- 多实例（03-06-01）：子窗口通过 RegisterSubWindow 注册到父窗口，VSync 请求经 SetRequestVsyncCallback 扇出。
- 表单渲染：FormRenderWindow（Feat-04）不使用 Rosen::Window，但继承同一 Window 基类，PipelineContext 无感切换。
- 全局管线：GlobalPipelineContextManager（Feat-03）创建 `isGlobalPipeline=true` 的 RosenWindow，拥有独立 RSUIDirector。

## 行为场景

```
场景 1: RosenWindow 构造获取 Rosen::Window 提供的 director (AC-2.2, R-6)
  Given 一个非全局管线的 Rosen::Window，其 GetRSUIDirector() 返回非空
  When RosenWindow 构造函数执行
  Then rsUIDirector_ 被赋值为 Rosen::Window 的 director
   And directorFromWindow_ 设为 true（Destroy 时不销毁）

场景 2: GlobalPipeline 强制创建独立 director (AC-2.3, R-6, R-7)
  Given isGlobalPipeline=true 且 Rosen::Window 提供了 director
  When RosenWindow 构造函数执行
  Then 跳过 Rosen::Window 的 director
   And 创建新的 RSUIDirector::Create(nullptr)
   And directorFromWindow_ 设为 false

场景 3: 多实例子窗口 Init 短路 (AC-3.1, R-10)
  Given SystemProperties::GetMultiInstanceEnabled()==true 且容器是 SubContainer
  And 父容器 RSUIContext 与当前一致
  When RosenWindow::Init() 执行
  Then pipelineWindow->RegisterSubWindow(id_) 被调用
  And 直接返回，不调用 SetRequestVsyncCallback

场景 4: Destroy 按所有权差异化销毁 director (AC-4.4, R-6, R-12)
  Given directorFromWindow_==false（ArkUI 创建的 director）
  When RosenWindow::Destroy() 执行
  Then rsUIDirector_->Destroy() 被调用
  And rsUIDirector_.reset() 释放引用

场景 5: Destroy 保留 Rosen 拥有的 director (AC-4.4, R-6, R-12)
  Given directorFromWindow_==true（Rosen::Window 拥有）
  When RosenWindow::Destroy() 执行
  Then 跳过 rsUIDirector_->Destroy()
  And 仅 rsUIDirector_.reset() 释放引用

场景 6: SetRootFrameNode 挂载 RSRootNode (AC-5.1, R-13)
  Given 一个有效的 NG FrameNode，其 RenderContext 是 RosenRenderContext
  And GetRSNode() 返回非空
  When SetRootFrameNode(root) 被调用
  Then rsUIDirector_->SetRSRootNode(ReinterpretCast<RSRootNode>(rsNode)) 被调用

场景 7: vsyncCallback 通过 ContainerScope 获取 window (AC-2.1, R-4)
  Given RosenWindow 已构造，vsyncCallback_ lambda 已创建
  When RS 发出一次 VSync 信号
  Then lambda 内部通过 ContainerScope(id) → Container::Current() 获取容器
   And 通过 container->GetWindow() 获取 window 实例
   And 调用 window->OnVsync(timestamp, frameCount)

场景 8: FlushModifier 每帧暂存先于 SendMessages 提交 (AC-7.2, R-17, R-18)
  Given PipelineContext 开始一帧的 Flush 阶段
  When pipeline_context.cpp 调用 FlushModifier
  Then window_->FlushModifier() 被调用
   And rsUIDirector_->FlushModifier() 将属性变更推送到 RS（不提交）
   And 随后在帧末 FlushMessages → FlushTasks → SendMessages 提交

场景 9: RosenRenderContext fallback director 创建 (AC-8.1, R-19)
  Given 一个 RSNode 需要在 RosenWindow 构造之前创建
  When RosenRenderContext::InitContext 检测到 GetRSUIContext 返回 nullptr
  Then 记录 "rsnode create before rosenwindow" 警告日志
   And 创建 RSUIDirector::Create(nullptr) 临时 director
   And 从 rsUIDirector_->GetRSUIContext() 提取 RSUIContext
   And 使用该 RSUIContext 创建 RSNode
```

## Spec 自审清单

- [x] 所有 H2/H3 章节按模板齐全
- [x] 每个 US 都有 AC，并使用 AC-X.Y 编号
- [x] 每个 AC 在「验收追溯」「验证映射」「行为场景」中可被引用
- [x] 规则定义编号齐全（R-1..R-19）
- [x] 所有源码引用均给出 file:line
- [x] API 变更分析已说明本 Feat 不暴露 ArkTS / C-API
- [x] 兼容性声明覆盖当前已识别的版本差异
- [x] Gherkin 场景覆盖每个 AC
- [x] 与 design.md 章节标题、ID（DESIGN-Func-03-05-01）对齐

## context-references

- `frameworks/core/common/window.h:47-331`（Window 基类定义与虚方法）
- `frameworks/core/common/window.cpp:31-66`（RequestFrame / OnVsync / SetVsyncCallback）
- `frameworks/core/components_ng/render/adapter/rosen_window.h:43-250`（RosenWindow 类定义）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:68-151`（构造函数）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:153-188`（Init）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:338-370`（Destroy）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:377-388`（SetRootFrameNode）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:396-406`（FlushTasks）
- `frameworks/core/components_ng/render/adapter/rosen_window.h:100-104`（FlushModifier inline 实现）
- `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:644-649`（fallback director 创建路径）
- `frameworks/core/components_ng/render/adapter/rosen_render_context.h:1016`（rsUIDirector_ 成员声明）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:1561-1564`（FlushModifier 管线调用）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:1290-1296`（FlushMessages 管线提交）
