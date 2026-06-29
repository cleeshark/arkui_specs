# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| Feature ID | Feat-01（FuncID 03-01-01） |
| Linked Design | DESIGN-Func-03-01-01（specs/03-engine-framework/01-render-pipeline/01-basic-render-pipeline/design.md） |
| Linked Epic | 无 |
| Complexity | 复杂 |
| Target Version | API 9 及以后（以 master HEAD 实现为基线） |
| Owner | ArkUI SIG / 渲染管线团队 |
| Status | Baselined（已有实现补录） |

> 本 Feat 仅锁定 NG 框架（components_ng + pipeline_ng）渲染主流程编排，不涉及 Classic（components_v2 / pipeline）。覆盖 VSync 接收、Build、Measure/Layout、Render/Paint、RS 提交全链路的**顺序与边界**；各阶段内部算法细节由 Feat-02..05 拆分。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

- 关联设计：`specs/03-engine-framework/01-render-pipeline/01-basic-render-pipeline/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `frameworks/core/pipeline_ng/pipeline_context.cpp`
  - `frameworks/core/pipeline_ng/ui_task_scheduler.cpp`
  - `frameworks/core/components_ng/base/frame_node.cpp`
  - `frameworks/core/components_ng/render/paint_wrapper.cpp`
  - `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp`
  - `frameworks/core/components_ng/render/adapter/rosen_window.cpp`
  - `frameworks/core/common/window.cpp` / `frameworks/core/common/window.h`
  - `frameworks/core/components_ng/pattern/custom/custom_node_base.cpp`

## 用户故事

### US-1: VSync 单源触发一帧编排

- As a 渲染管线维护者
- I want 每次 RenderService 产生的 VSync 信号在每个 PipelineContext 上恰好触发一次 `FlushVsync`
- So that 多容器/多窗口下一帧内不会出现重复绘制或漏帧

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN RS 发出一次 VSync THEN RosenWindow 的 `vsyncCallback_->onCallback` 仅执行一次，并以 `(timeStampNanos, frameCount)` 透传至 `Window::OnVsync` → `PipelineBase::OnVsyncEvent` → `PipelineContext::FlushVsync`。来源：`rosen_window.cpp:63-106`、`window.cpp:48-58`、`pipeline_base.cpp:748-783`、`pipeline_context.cpp:936` | 正常 |
| AC-1.2 | WHEN 多容器场景下 THEN `Window::callbacks_` 列表中每个回调按注册顺序被调用一次；同一帧内同一 PipelineContext 不会被同源 VSync 重复触发。来源：`window.cpp:48-58`、`pipeline_base.cpp:62-70` | 正常 |
| AC-1.3 | WHEN `RosenWindow::ForceFlushVsync` 触发兜底路径 THEN 使用 `frameCount=UINT64_MAX` 哨兵，`FlushVsync` 跳过 `DispatchDisplaySync`，避免污染 DisplaySync 时间线。来源：`rosen_window.cpp:222-228`、`pipeline_context.cpp:972-974` | 异常 |
| AC-1.4 | WHEN `PipelineContext::FlushVsync` 起始 THEN 记录 `SetVsyncTime` 并发出 `ACE_SCOPED_TRACE_COMMERCIAL("UIVsyncTask[timestamp][vsyncID][instanceID]")` HiTrace。来源：`pipeline_context.cpp:943,948-949` | 边界 |

### US-2: 一帧子阶段顺序固定

- As a 渲染管线维护者
- I want `FlushVsync` 内部子阶段顺序固定（动画→事件→Build→Layout/Render→Modifier/FrameRate→Messages→收尾），不被绕过
- So that 上层能力依赖该序列推导自身时序正确性，新插入步骤必须显式定位

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN FlushVsync 执行 THEN 子阶段顺序为：`FlushZindexUpdate` → `FlushAnimation` → `FlushFrameCallback` → `FlushModifierAnimation` → `FlushTouchEvents/FlushCompatibleTouchEvents/FlushDragEvents` → `FlushFrameCallbackFromCAPI` → `FlushBuild` → `ReloadNodesResource` → `taskScheduler_->FlushTask` → `FlushPersistAfterLayoutTask` → `FlushNodeChangeFlag` → `FlushAnimationClosure` → `TryCallNextFrameLayoutCallback` → `window_->FlushModifier` → `FlushFrameRate` → `FlushAfterModifierTask` → `FlushMessages` → 焦点/可见性事件 → `FlushAfterRenderTask` → `window_->FlushLayoutSize` → `window_->FlushVsync` → `FireAccessibilityEvents`。来源：`pipeline_context.cpp:975-1123` | 正常 |
| AC-2.2 | WHEN Build 阶段执行 THEN `FlushBuild`（`:1006`）必须先于 `taskScheduler_->FlushTask`（`:1020`），即 Build 完毕后才进入 Layout/Render，否则新建节点不会进入当帧布局 | 正常 |
| AC-2.3 | WHEN Modifier 提交阶段执行 THEN `window_->FlushModifier`（`:1046`）必须先于 `FlushMessages`（`:1068/1074`）；后者为 RS 提交边界，之后产生的 RC 改动进入下一帧 | 边界 |
| AC-2.4 | WHEN `onShow_ && onFocus_ && isWindowHasFocused_` THEN 执行 `FlushFocusView/FlushFocus/FlushFocusScroll`（`:1080-1086`）；后台或失焦窗口跳过 | 正常 |

### US-3: Build 阶段 dirty 节点排空

- As a 状态管理消费者
- I want 一帧内状态变更产生的 dirtyPropertyNodes_ 与 dirtyNodes_（CustomNode）能在 `FlushBuild` 中被排空，且最多 3 次重入
- So that 状态→FrameNode 重建在当前帧完成，超额工作受控延后

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `FlushBuild` 执行 THEN 先 `FlushOnceVsyncTask`，再设 `isRebuildFinished_=false`，调用 `FlushDirtyNodeUpdate`，最后 `isRebuildFinished_=true` 并执行 `FlushBuildFinishCallbacks`。来源：`pipeline_context.cpp:1745-1783` | 正常 |
| AC-3.2 | WHEN `FlushDirtyNodeUpdate` 执行 THEN 顺序为：`FlushFreezeNode` → `FlushDirtyPropertyNodes`（排空 `dirtyPropertyNodes_`，对每个节点 `ProcessPropertyDiff`）→ `FlushPendingDeleteCustomNode` → 重入循环最多 3 次 `customNode->Update()` → `FlushTSUpdates`。来源：`pipeline_context.cpp:666-708` | 边界 |
| AC-3.3 | WHEN `CustomNodeBase::MarkNeedUpdate` 被调用且已 `needRebuild_=true` THEN 不重复入队；首次入队 `context->AddDirtyCustomNode(this)` 并 `RequestFrame()`。来源：`custom_node_base.cpp:283-296` | 正常 |
| AC-3.4 | WHEN 进入 `FlushDirtyNodeUpdate` 时 `ViewStackProcessor` 非空 THEN 发出告警但不阻塞执行。来源：`pipeline_context.cpp:684-687` | 正常 |

### US-4: Layout/Render 由 TaskScheduler 统一驱动

- As a 渲染管线维护者
- I want 同一个 `UITaskScheduler::FlushTask` 在一次调用内驱动 `FlushLayoutTask` 与 `FlushRenderTask`，支持最多 2 轮二次布局
- So that Layout 完成后立即 Render，geometryTransition 等需要二次布局的场景在当帧收敛

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `UITaskScheduler::FlushTask` 执行 THEN 在 `CHECK_RUN_ON(UI)` 前提下执行 do-while 循环；循环上限 `ENDORSE_LAYOUT_COUNT=2`。来源：`ui_task_scheduler.cpp:31,300-337` | 边界 |
| AC-4.2 | WHEN 每轮循环执行 THEN `FlushLayoutTask` → 若 `NeedAdditionalLayout()` 再次 `FlushLayoutTask` → `FlushAfterLayoutTask` → `FlushSafeAreaPaddingProcess` → `FlushAfterLayoutCallbackInImplicitAnimationTask`；循环结束后执行 `FlushAllSingleNodeTasks` 与 `FlushRenderTask`。来源：`ui_task_scheduler.cpp:300-337` | 正常 |
| AC-4.3 | WHEN `FlushLayoutTask` 执行 THEN 将 `dirtyLayoutNodes_` 移入局部副本并按页迭代；调用 `FrameNode::CreateLayoutTask` 进入 `Measure → Layout`。来源：`ui_task_scheduler.cpp:131-185`、`frame_node.cpp:2830-2869` | 正常 |
| AC-4.4 | WHEN `isLayouting_` 已为真时 `FlushTaskWithCheck` 再次被调用 THEN 自增 `multiLayoutCount_` 并返回，不进行嵌套 layout。来源：`ui_task_scheduler.cpp:290-298` | 正常 |
| AC-4.5 | WHEN 布局轮数超过 `ENDORSE_LAYOUT_COUNT` THEN 剩余工作通过 `RequestFrameOnLayoutCountExceeds` 延入下一帧。来源：`ui_task_scheduler.cpp:310,364` | 边界 |

### US-5: Paint 优先 Modifier 路径

- As a 组件作者
- I want `PaintWrapper::FlushRender` 在存在 Modifier 时仅走 Modifier 路径，无 Modifier 时回退到 Draw 录制
- So that 支持属性独立动画的同时保持旧组件可用

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `PaintWrapper::FlushRender` 被调用且存在 Modifier THEN 先尝试 `GetContentModifier/GetOverlayModifier/GetForegroundModifier`；任一存在则调用对应 `UpdateXxxModifier` 并返回，不再录制 draw。来源：`paint_wrapper.cpp:125-152` | 正常 |
| AC-5.2 | WHEN 全部 Modifier 缺失 THEN 调用 `renderContext->StartRecording`，依次执行 ContentDraw/ForegroundDraw/OverlayDraw 函数，再 `FinishRecording`。来源：`paint_wrapper.cpp:155-180`、`rosen_render_context.cpp:398/412` | 异常 |
| AC-5.3 | WHEN `FrameNode::CreateRenderTask` 被调用且 `!isRenderDirtyMarked_` THEN 直接返回空任务；在 `CreatePaintWrapper` 中清 `isRenderDirtyMarked_=false`。来源：`frame_node.cpp:3057-3093,3075-3098` | 正常 |

### US-6: RS 提交仅一处边界

- As a 渲染管线维护者
- I want 每帧仅在 `FlushMessages → SendMessages` 一处提交 RS，其后修改进入下一帧
- So that "帧完成"具备唯一可观察边界，避免无意识跨帧

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `PipelineContext::FlushMessages` 执行 THEN 通过 `window_->FlushTasks(callback)` 最终调用 `rsUIDirector_->SendMessages`。来源：`pipeline_context.cpp:1412`、`rosen_window.cpp:378-388` | 正常 |
| AC-6.2 | WHEN 同一帧内 THEN `FlushMessages` 仅被 `FlushVsync` 调用一次（在 `:1068` 或 `:1074` 分支二选一）；后台 + `backgroundColorModeUpdated_` 走 `:1066-1073` 的快照通知分支。来源：`pipeline_context.cpp:1066-1075` | 正常 |
| AC-6.3 | WHEN 旁路 `FlushImplicitTransaction` 被调用 THEN 仅在 OnShow 多实例、组件截图等枚举路径触发，不构成主流程提交点。来源：`rosen_window.cpp:309-322`、`rosen_render_context.cpp:8403-8443` | 正常 |
| AC-6.4 | WHEN `FlushMessages` 之后 THEN `FlushAfterRenderTask`、A11y 事件、`window_->FlushVsync()` 不再修改 RS Tree。来源：`pipeline_context.cpp:1111-1125` | 正常 |

### US-7: 帧请求合并与后台门控

- As a 性能维护者
- I want 同一帧内多次 `RequestFrame` 自动合并为一次 VSync 请求，且后台窗口默认不请求 VSync
- So that 减少 IPC 频次并避免后台无意义绘制

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `!forceVsync_ && !onShow_` THEN `RosenWindow::RequestFrame` 直接返回，不调用 `rsWindow_->RequestVsync`。来源：`rosen_window.cpp:258-263` | 正常 |
| AC-7.2 | WHEN `isRequestVsync_=true` THEN `RequestFrame` 直接返回；调用 `rsWindow_->RequestVsync` 后置 `isRequestVsync_=true`，在 `Window::OnVsync` 中清除。来源：`rosen_window.cpp:265-273`、`window.cpp:48-58` | 正常 |
| AC-7.3 | WHEN 成功调用 `rsWindow_->RequestVsync`（通过 `onShow_`/`forceVsync_` 门控且未命中 `isRequestVsync_` 合并） THEN `RequestFrame` 伴随注册 `PostVsyncTimeoutDFXTask`（500ms 兜底）与 `OnIdle` 延迟任务（IDLE_TASK_DELAY_MILLISECOND）。来源：`rosen_window.cpp:260-289` | 异常 |
| AC-7.4 | WHEN `SystemProperties::GetMultiInstanceEnabled()` 启用 THEN 子窗口的 `RequestVsync` 会经主窗口透传。来源：`rosen_window.cpp:147-178` | 正常 |

## 验收追溯

| AC编号 | US ID | 业务规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 || R-1 / R-7 | 代码评审 + pipeline ut | 正常 |
| AC-1.2 || R-1 | 代码评审 + 多容器集成测试 | 正常 |
| AC-1.3 || R-21 | 代码评审 + 模拟超时 ut | 边界 |
| AC-1.4 || R-8 | HiTrace 抓取 | 正常 |
| AC-2.1 || R-2 / R-9 | 代码评审 | 正常 |
| AC-2.2 || R-2 | 代码评审 + Build/Layout 顺序 ut | 正常 |
| AC-2.3 || R-2 / R-5 | 代码评审 | 正常 |
| AC-2.4 || R-10 | 焦点状态 ut | 正常 |
| AC-3.1 || R-11 | pipeline_context ut | 正常 |
| AC-3.2 || R-11 / R-12 | FlushDirtyNodeUpdate ut | 正常 |
| AC-3.3 || R-12 | custom_node ut | 正常 |
| AC-3.4 || R-22 | 代码评审 | 正常 |
| AC-4.1 || R-3 / R-13 | ui_task_scheduler ut | 正常 |
| AC-4.2 || R-13 | ui_task_scheduler ut | 正常 |
| AC-4.3 || R-14 | frame_node ut | 正常 |
| AC-4.4 || R-23 | 重入 ut | 边界 |
| AC-4.5 || R-28 | 二次布局 ut | 正常 |
| AC-5.1 || R-15 | paint_wrapper ut | 正常 |
| AC-5.2 || R-15 | paint_wrapper ut | 正常 |
| AC-5.3 || R-16 | frame_node ut | 正常 |
| AC-6.1 || R-5 | rosen_window ut | 正常 |
| AC-6.2 || R-5 | pipeline_context ut | 正常 |
| AC-6.3 || R-24 | 代码评审 | 正常 |
| AC-6.4 || R-5 | 代码评审 | 正常 |
| AC-7.1 || R-17 | rosen_window ut | 正常 |
| AC-7.2 || R-17 | rosen_window ut | 正常 |
| AC-7.3 || R-29 | DFX 抓取 | 正常 |
| AC-7.4 || R-18 | 多实例集成测试 | 正常 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | VSync 是 NG 主流程唯一节拍源；每个 PipelineContext 一帧仅一次 `FlushVsync`。 | — | — |
| R-2 | 行为 | — | 一帧内子阶段顺序硬绑定，不可绕过、不可重排；新阶段必须显式定位插入。 | — | — |
| R-3 | 行为 | — | Layout 与 Render 由同一个 `UITaskScheduler::FlushTask` 驱动，禁止外部独立调用 `FlushRenderTask` 跨越 Layout。 | — | — |
| R-4 | 行为 | — | dirty 节点分四条队列（property/custom/layout/render），各自带帧内幂等标志，禁止在其他位置重新实现 dirty 集合。 | — | — |
| R-5 | 行为 | — | RS 提交仅在 `FlushMessages → SendMessages` 一处；之后的修改进入下一帧。 | — | — |
| R-6 | 行为 | — | 后台（!onShow_）窗口默认不 `RequestFrame`，除非显式 `forceVsync_`。 | — | — |
| R-7 | 行为 | — | `vsyncCallback_->onCallback(timeStamp, frameCount)` 会先调用 `ArkUIPerfMonitor::StartPerf`、`FrameReport::FlushBegin`，再依次 `Window::OnVsync`、`PipelineBase::OnVsyncEvent`、`PipelineContext::FlushVsync`，结束后 `ArkUIPerfMonitor::FinishPerf`、`FrameReport::FlushEnd`、`JankFrameReport::JankFrameRecord`。来源：`rosen_window.cpp:63-106`。 | — | — |
| R-8 | 行为 | — | `FlushVsync` 入口发 HiTrace `UIVsyncTask`；`FlushBuild` 段内发 `BeginFlushBuild/End`（`pipeline_context.cpp:674,709`）；`FlushAnimation` 段内发 `BeginFlushAnimation/End`（`:1317,:1324`）。 | — | — |
| R-9 | 行为 | — | 在 `FlushVsync` 起始 `window_->Lock()`，末尾 `window_->Unlock()`（`:950, :1125`），保证一帧内 RS 操作的临界区。 | — | — |
| R-10 | 行为 | — | 焦点/区域变化事件 `HandleOnAreaChangeEvent`、`HandleVisibleAreaChangeEvent` 紧随 `FlushMessages` 之后但在 `FlushAfterRenderTask` 之前（`:1092-1099`），保证基于最新布局结果分发。 | — | — |
| R-11 | 行为 | — | `FlushBuild` 起：`vsyncListener_()` → `FlushOnceVsyncTask` → `isRebuildFinished_=false` → `FlushDirtyNodeUpdate` → `isRebuildFinished_=true` → `FlushBuildFinishCallbacks`。来源：`pipeline_context.cpp:1745-1783`。 | — | — |
| R-12 | 行为 | — | `FlushDirtyNodeUpdate` 主循环 `maxFlushTimes=3`；每轮 `decltype(dirtyNodes_) dirtyNodes(std::move(dirtyNodes_));` 然后遍历调用 `customNode->Update()`，剩余 dirty 留待下一轮或下一帧。来源：`pipeline_context.cpp:691-703`。 | — | — |
| R-13 | 行为 | — | `UITaskScheduler::FlushTask` do-while 循环上限 `ENDORSE_LAYOUT_COUNT=2`，循环结束执行 `FlushAllSingleNodeTasks` 与 `FlushRenderTask`。来源：`ui_task_scheduler.cpp:300-337`。 | — | — |
| R-14 | 行为 | — | `FrameNode::CreateLayoutTask` 在 `!isLayoutDirtyMarked_` 时直接返回；设置 `RootMeasureNode(true)`、`UpdateLayoutPropertyFlag()`，再 `Measure → Layout`。来源：`frame_node.cpp:2830-2869`。 | — | — |
| R-15 | 行为 | — | `PaintWrapper::FlushRender` 三类 Modifier 优先；缺失时 `StartRecording → DrawFunctions → FinishRecording`。来源：`paint_wrapper.cpp:125-180`。 | — | — |
| R-16 | 行为 | — | `FrameNode::MarkNeedRender` 标记 `PROPERTY_UPDATE_RENDER`，向父节点冒泡 `PROPERTY_UPDATE_RENDER_BY_CHILD_REQUEST`，并 `AddDirtyRenderNode`。来源：`frame_node.cpp:3430-3461`。 | — | — |
| R-17 | 行为 | — | `RosenWindow::RequestFrame` 路径：`onShow` 门控 → `isRequestVsync_` 合并 → `rsWindow_->RequestVsync(vsyncCallback_)` → `PostVsyncTimeoutDFXTask(500ms)` → `OnIdle` 延迟任务（IDLE_TASK_DELAY_MILLISECOND）。超时任务与 OnIdle 仅在成功发起 RequestVsync 的分支中注册。来源：`rosen_window.cpp:258-289`。 | — | — |
| R-18 | 行为 | — | 多实例：`RosenWindow::Init` 在 `rsUIDirector_->SetRequestVsyncCallback` 中检查 `SystemProperties::GetMultiInstanceEnabled()` 并向子窗口扇出。来源：`rosen_window.cpp:147-178`。 | — | — |
| R-19 | 行为 | — | `RecordFrameTime` 推送时间戳到 `RSUIDirector::SetTimeStamp`（`rosen_window.cpp:372-376`），保证 RS 端 jank 统计与 ArkUI 时间线一致。 | — | — |
| R-20 | 行为 | — | `window_->FlushFrameRate(rate, animatorExpectedFrameRate, rateType)` 在 Modifier 提交之后、`FlushMessages` 之前发出（`pipeline_context.cpp:1047`）；rate 由当前帧动画估算。 | — | — |
| R-21 | 异常 | — | 当 RS 在 500ms 内未送达 VSync，`PostVsyncTimeoutDFXTask` 触发，并通过 `EventReport::SendVsyncException(VsyncExcepType::UI_VSYNC_TIMEOUT, …)`（`rosen_window.cpp:237`）上报；同时 `ForceFlushVsync` 调用 `vsyncCallback_->onCallback(now, UINT64_MAX)` 兜底走一次 FlushVsync。 | — | — |
| R-22 | 异常 | — | 进入 `FlushDirtyNodeUpdate` 时若 `ViewStackProcessor` 非空，记录 warning 但不中断（`pipeline_context.cpp:684-687`）；表明上游存在 mount/build 未平衡。 | — | — |
| R-23 | 异常 | — | 嵌套调用 `UITaskScheduler::FlushTaskWithCheck`（已在 layouting）只增加 `multiLayoutCount_`，原次调用结束后再决定是否补一次（`ui_task_scheduler.cpp:290-298`）。 | — | — |
| R-24 | 异常 | — | `FlushImplicitTransaction` 是离帧旁路；仅在 OnShow 多实例（`rosen_window.cpp:291-298`）与组件截图等枚举路径调用，**不得**作为主流程提交点。 | — | — |
| R-25 | 异常 | — | `FlushDirtyNodeUpdate` while-loop 超 3 次仍有 dirtyNodes 时，剩余项保留至下一帧；不抛错。 | — | — |
| R-26 | 异常 | — | 当 `frameCount==UINT64_MAX`，`DispatchDisplaySync` 被跳过（`pipeline_context.cpp:972-974`），防止 DisplaySync 时间线被哨兵污染。 | — | — |
| R-27 | 异常 | — | 表单渲染（`isFormRender_ && drawDelegate_`）走一次 `drawDelegate_->DrawRSFrame(renderContext)` 后跳出主 build/layout/render 流程（`pipeline_context.cpp:1008-1012`），不视为常规 FlushVsync 路径。 | — | — |
| R-28 | 恢复 | — | 当 Layout 二次轮数超过 `ENDORSE_LAYOUT_COUNT=2`，调用 `RequestFrameOnLayoutCountExceeds()` 延入下一帧；不阻塞当前帧 Render。来源：`ui_task_scheduler.cpp:310,364`。 | — | — |
| R-29 | 恢复 | — | `RequestFrame` 已注册超时 DFX 任务，500ms 内未收到 VSync → `ForceFlushVsync` 触发一次合成 vsync 以保证不卡死；其后 `RequestFrame` 重新请求真实 VSync。来源：`rosen_window.cpp:222-256`。 | — | — |
| R-30 | 恢复 | — | 若 `HasUIRunningAnimation()` 在 FlushVsync 末尾仍为 true，自动 `RequestFrame()`（`pipeline_context.cpp:1043-1044`），保证动画连帧。 | — | — |
| R-31 | 恢复 | — | 布局过程中产生新 dirty 节点由 `AddSingleNodeToFlush` 收集，FlushTask 末尾 `FlushAllSingleNodeTasks` 统一处理；过期 dirty 留待下一帧（`ui_task_scheduler.cpp:334`、`pipeline_context.cpp:1451-1457`）。 | — | — |

---

## 验证映射

| AC编号 | 类型 | 位置 / 用例名 |
|-------|------|---------------|
| AC-1.1 / AC-1.2 | 单元测试 | test/unittest/core/pipeline/pipeline_context_test_ng.cpp（FlushVsync / OnVsyncEvent 系列） |
| AC-1.3 / R-29 | 单元测试 | 待补充 — 当前无 ForceFlushVsync 专用 ut；建议在 test/unittest/core/pipeline/ 下新增 `frameCount=UINT64_MAX` 场景 |
| AC-1.4 / R-8 | HiTrace 验证 | bytrace 抓取 `UIVsyncTask` / `BeginFlushBuild` |
| AC-2.1 / AC-2.2 / AC-2.3 | 代码评审 | pipeline_context.cpp 直接对照 |
| AC-2.4 | 单元测试 | test/unittest/core/pipeline/pipeline_context_test_ng.cpp 焦点相关用例 |
| AC-3.1..3.4 | 单元测试 | test/unittest/core/pipeline/pipeline_context_test_ng.cpp（FlushBuild / FlushDirtyNodeUpdate） |
| AC-4.1..4.5 | 单元测试 | 待补充 — 当前无 ui_task_scheduler 专用 ut；建议在 test/unittest/core/pipeline/ 下新增 |
| AC-5.1..5.3 | 单元测试 | test/unittest/core/base/frame_node_test_ng.cpp；paint_wrapper ut 待补充 |
| AC-6.1..6.4 | 单元测试 | 待补充 — 当前无 rosen_window 专用 ut；建议在 test/unittest/core/render/ 下新增 |
| AC-7.1..7.4 | 单元测试 | 待补充 — 同 AC-6.1..6.4，rosen_window ut 待补充 |

> 注：已标注路径为仓内现有测试文件；标记"待补充"的为当前不存在的测试，纳入后续 Feat 拆分的测试补录任务。

## API 变更分析

### 新增 API

无。Feat-01 为框架内部主流程编排，**不对外暴露 ArkTS 属性 / 装饰器**。

**C-API (NDK) 接口：**

无直接 C-API。注：`PipelineContext::FlushFrameCallbackFromCAPI`（`pipeline_context.cpp:1004`）是 C-API 子系统（`ArkUI_NativeAPI`）注入帧回调的通道，但属于其他 Feat 的接口契约。

**关联类型定义：**

仅框架内部类型（已在 design.md 数据模型章节列出）：
- `PipelineContext`（`frameworks/core/pipeline_ng/pipeline_context.h`）
- `UITaskScheduler`（`frameworks/core/pipeline_ng/ui_task_scheduler.h`）
- `FrameNode`（`frameworks/core/components_ng/base/frame_node.h`）
- `PaintWrapper`（`frameworks/core/components_ng/render/paint_wrapper.h`）
- `Window` / `RosenWindow`（`frameworks/core/common/window.h`、`frameworks/core/components_ng/render/adapter/rosen_window.h`）
- 标志位 `PropertyChangeFlag`（`frameworks/core/components_ng/property/property.h`）

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
| < API 10 | `LayoutWrapper::ApplyConstraint` 中的 aspect-ratio 早期路径不受 `GreatOrEqualAPITargetVersion(PlatformVersion::VERSION_TEN)` 门控（`layout_wrapper.cpp:804` 附近） | 中：旧应用在升级后 Aspect 行为可能与新应用不同 | 不修改，文档化；新应用应基于 ≥ API 10 行为开发 |
| 各版本 | `FeatureParam::IsPageOverflowEnabled` / `IsRnOverflowEnable` 影响根节点 measure 时是否允许溢出（`frame_node.cpp:5958-5961`） | 中：依产品配置而异 | 通过产品 FeatureParam 控制；本 Feat 不重定义 |
| 各版本 | `SystemProperties::GetLayoutDetectEnabled()` 启用时会在重入 layout 处抛断言（`ui_task_scheduler.cpp:138`） | 低（开发态）：未启用时为 no-op | 仅 dev 环境启用 |
| 各版本 | `SystemProperties::GetContainerDeleteFlag()` 改变 `HandleOnAreaChangeEvent`/`HandleVisibleAreaChangeEvent` 分支（`pipeline_context.cpp:1088-1100`） | 低：迁移期容器删除策略 | 文档化 |
| 各版本 | `dvsyncOn_` 决定 `OnIdle` 截止时间计算（`rosen_window.cpp:84-92,200-215`） | 低：DVSync 启用与否仅影响截止 | 不需迁移 |
| 各版本 | `SystemProperties::GetMultiInstanceEnabled()` 切换子窗口 VSync 扇出（`rosen_window.cpp:147-178`） | 中：多实例编译态决定 | 切换后行为按 R-18 |

> 本表仅记录与"主流程编排"直接相关的版本差异。子阶段内部差异（如 Layout/Build 算法）由对应子 Feat 维护。

## 架构约束

- 全程 `CHECK_RUN_ON(UI)`：`pipeline_context.cpp` 中 `AddDirtyCustomNode` (:485)、`ui_task_scheduler.cpp` 中 `FlushLayoutTask` (:133)、`FlushTask` (:302) 显式断言。
- 一帧主流程禁止跨线程调度；Render Task 可声明 `GetTaskThreadType()` 走 BACKGROUND，但 Layout 不允许。
- 与 RenderService 的通信全部通过 `rsUIDirector_->SendMessages`（同步提交点）与 `FlushImplicitTransaction`（离帧旁路），不允许直接调用 RS API 提交。
- VSync 接收路径全部经 `Window` 抽象，禁止旁路 `rsWindow_->RequestVsync` 调用。

## 非功能性需求

- 可观测：每帧产生 HiTrace `UIVsyncTask`、`BeginFlushBuild`、`BeginFlushAnimation` 等切片；`FrameReport::FlushBegin/FlushEnd`、`JankFrameReport::JankFrameRecord`、`ArkUIPerfMonitor::StartPerf/FinishPerf` 全程开启。
- 性能：单帧主流程主线程执行；耗时受 `maxFlushTimes=3` 与 `ENDORSE_LAYOUT_COUNT=2` 双重约束。
- 鲁棒性：VSync 超时由 500ms DFX 兜底；ViewStackProcessor 异常仅告警；嵌套 layout 自合并。
- 多容器：`Window::callbacks_` 列表保证每个 PipelineContext 各自接收 VSync；多实例下子窗口经主窗口扇出。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

- 状态管理（state_mgmt）：`NativeViewPartialUpdate::markNeedUpdate` 与 `CustomNodeBase::MarkNeedUpdate` 必须在主流程 Build 阶段消化。
- 动画：`FlushAnimation` 与 `FlushModifierAnimation` 是主流程一部分；若 `HasUIRunningAnimation()` 为 true，自动续帧。
- 焦点/无障碍：在 `FlushMessages` 之后才分发焦点和 A11y 事件，确保基于已布局结果。
- 多窗口/多实例：通过 `Window::callbacks_` 扇出与 `SystemProperties::GetMultiInstanceEnabled()` 控制子窗口 VSync 传播。
- C-API 帧回调：`FlushFrameCallbackFromCAPI` 是主流程内的稳定锚点（`pipeline_context.cpp:1004`）。

## 行为场景

```
场景 1: 单容器单 VSync 触发一次 FlushVsync (AC-1.1)
  Given 一个前台 NG PipelineContext，已正常完成 RosenWindow 初始化
  When RenderService 发出一次 VSync 信号 (timeStamp=T0, frameCount=N)
  Then RosenWindow::vsyncCallback_->onCallback 被调用一次
   And PipelineBase::OnVsyncEvent(T0, N) 被调用一次
   And PipelineContext::FlushVsync(T0, N) 被调用一次

场景 2: ForceFlushVsync 兜底 (AC-1.3, R-21, R-29)
  Given 上一次 RequestFrame 后 500ms 内未收到 VSync
  When PostVsyncTimeoutDFXTask 触发 ForceFlushVsync
  Then vsyncCallback_->onCallback(now, UINT64_MAX) 被调用
   And FlushVsync 内 DispatchDisplaySync 被跳过
   And EventReport::SendVsyncException(UI_VSYNC_TIMEOUT, ...) 被上报

场景 3: 子阶段顺序固定 (AC-2.1, AC-2.2, AC-2.3)
  Given 任意非空 dirty 集合
  When FlushVsync 执行完成
  Then FlushBuild 调用次序在 taskScheduler_->FlushTask 之前
   And window_->FlushModifier 在 FlushMessages 之前
   And FlushMessages 仅被调用一次
   And FlushAfterRenderTask 在 FlushMessages 之后

场景 4: 后台窗口不 RequestFrame (AC-7.1, R-6)
  Given onShow_==false 且 forceVsync_==false
  When 任意状态变化触发 RequestFrame
  Then RosenWindow::RequestFrame 直接返回，不调用 rsWindow_->RequestVsync

场景 5: 同帧多次 RequestFrame 合并 (AC-7.2, R-17)
  Given onShow_==true 且 isRequestVsync_==false
  When 同一帧内 RequestFrame 被调用三次
  Then 第一次设置 isRequestVsync_=true 并调用 rsWindow_->RequestVsync 一次
   And 第二、三次直接返回
   And Window::OnVsync 触发后 isRequestVsync_ 被清除

场景 6: dirty CustomNode 三轮重入收敛 (AC-3.2, R-12)
  Given dirtyNodes_ 中存在自我注入新 dirty 的 CustomNode
  When FlushDirtyNodeUpdate 开始执行
  Then 重入循环最多执行 3 次
   And 若第 3 次结束后仍有 dirty 留存，则等到下一帧

场景 7: Layout 二次布局触发 (AC-4.2, AC-4.5, R-28)
  Given geometryTransition 需要二次布局
  When UITaskScheduler::FlushTask 第一轮完成
  Then NeedAdditionalLayout 返回 true，再次 FlushLayoutTask
   And do-while 最多 2 轮，超出后 RequestFrameOnLayoutCountExceeds 延入下一帧

场景 8: 嵌套 layout 自合并 (AC-4.4, R-23)
  Given isLayouting_==true 时 FlushTaskWithCheck 再次被调用
  When 调用入口检测
  Then multiLayoutCount_++ 并立即返回，不进行嵌套 layout

场景 9: Modifier 优先 Paint 路径 (AC-5.1)
  Given FrameNode 的 NodePaintMethod 提供 ContentModifier
  When PaintWrapper::FlushRender 被调用
  Then UpdateContentModifier 被调用
   And StartRecording / DrawFunction / FinishRecording 不被调用

场景 10: 无 Modifier 时回退 Draw 录制 (AC-5.2)
  Given FrameNode 的 NodePaintMethod 三类 Modifier 均为空
  When PaintWrapper::FlushRender 被调用
  Then renderContext->StartRecording 被调用
   And ContentDraw / ForegroundDraw / OverlayDraw 函数依序执行
   And renderContext->FinishRecording 收尾

场景 11: RS 仅一次提交 (AC-6.1, AC-6.2, AC-6.4, R-5)
  Given 任意非空 dirty 集合
  When FlushVsync 执行完成
  Then rsUIDirector_->SendMessages 被调用且仅被调用一次
   And SendMessages 之后的 FlushAfterRenderTask、A11y 事件不再修改 RS Tree

场景 12: 多实例子窗口 VSync 扇出 (AC-7.4, R-18)
  Given SystemProperties::GetMultiInstanceEnabled()==true 且子窗口已附着
  When 主窗口在 SetRequestVsyncCallback 中接收到子窗口 RequestVsync
  Then 子窗口的请求被透传到主窗口的 rsWindow_->RequestVsync

场景 13: 焦点事件后置于 FlushMessages (AC-2.4, R-10)
  Given onShow_ && onFocus_ && isWindowHasFocused_ 均为 true
  When FlushVsync 进行到 FlushMessages 之后
  Then FlushFocusView / FlushFocus / FlushFocusScroll 被调用
   And 之后才进入 HandleOnAreaChangeEvent / HandleVisibleAreaChangeEvent

场景 14: 表单一次性绘制旁路 (R-27)
  Given isFormRender_==true 且 drawDelegate_ 非空
  When FlushVsync 进入 :1008-1012 分支
  Then drawDelegate_->DrawRSFrame(renderContext) 被调用
   And 跳过常规 FlushBuild / taskScheduler_->FlushTask 流程
```

## Spec 自审清单

- [x] 所有 H2/H3 章节按模板齐全
- [x] 每个 US 都有 AC，并使用 AC-X.Y 编号
- [x] 每个 AC 在「验收追溯」「验证映射」「行为场景」中可被引用
- [x] 业务规则 / 功能规则 / 异常规则 / 恢复契约 编号齐全
- [x] 所有源码引用均给出 file:line
- [x] API 变更分析已说明本 Feat 不暴露 ArkTS / C-API
- [x] 兼容性声明覆盖当前已识别的版本差异
- [x] Gherkin 场景覆盖每个 AC
- [x] 与 design.md 章节标题、ID（DESIGN-Func-03-01-01）对齐

## context-references

- `frameworks/core/pipeline_ng/pipeline_context.cpp:475-597`（AddDirty* 入口）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:666-708`（FlushDirtyNodeUpdate）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:742-753`（AddScheduleTask）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:936-1125`（FlushVsync 主体）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:1335-1343`（FlushAnimation）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:1412`（FlushMessages）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:1433-1457`（FlushUITasks / FlushUITaskWithSingleDirtyNode）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:1681-1731`（FlushPipelineImmediately / FlushFrameRate）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:1745-1783`（FlushBuild）
- `frameworks/core/pipeline_ng/pipeline_context.cpp:7466-7477`（FlushModifierAnimation）
- `frameworks/core/pipeline_ng/ui_task_scheduler.cpp:31`（ENDORSE_LAYOUT_COUNT=2）
- `frameworks/core/pipeline_ng/ui_task_scheduler.cpp:99-185`（AddDirty*、FlushLayoutTask）
- `frameworks/core/pipeline_ng/ui_task_scheduler.cpp:230-260`（FlushRenderTask）
- `frameworks/core/pipeline_ng/ui_task_scheduler.cpp:290-340`（FlushTaskWithCheck / FlushTask）
- `frameworks/core/components_ng/base/frame_node.cpp:2830-2869`（CreateLayoutTask / Measure / Layout 入口）
- `frameworks/core/components_ng/base/frame_node.cpp:3057-3098`（CreateRenderTask / CreatePaintWrapper）
- `frameworks/core/components_ng/base/frame_node.cpp:3321-3499`（MarkDirtyNode 系列、MarkNeedRender）
- `frameworks/core/components_ng/base/frame_node.cpp:5895-6042`（Measure 完整实现）
- `frameworks/core/components_ng/base/frame_node.cpp:6042-6236`（Layout 完整实现）
- `frameworks/core/components_ng/property/property.h:45-74`（PROPERTY_UPDATE_* 标志）
- `frameworks/core/components_ng/pattern/custom/custom_node_base.cpp:283-305`（MarkNeedUpdate / FireRecycleSelf）
- `frameworks/core/components_ng/pattern/custom/custom_node.cpp:34-126`（Build / Render / FlushReload）
- `frameworks/core/components_ng/render/paint_wrapper.cpp:125-180`（FlushRender Modifier vs Draw）
- `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:398-412`（StartRecording / FinishRecording）
- `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:817-867`（SyncGeometryProperties）
- `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:8403-8443`（FlushImplicitTransaction 旁路）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:63-106`（vsyncCallback_->onCallback）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:147-178`（Init / 多实例扇出）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:192-228`（FlushFrameRate / ForceFlushVsync）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:258-289`（RequestFrame 合并 / 后台门控）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:291-322`（OnShow / FlushImplicitTransaction 旁路）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:378-388`（FlushTasks → SendMessages）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:459-503`（OnVsync / FlushVsync）
- `frameworks/core/common/window.cpp:31-66`（RequestFrame / OnVsync / SetVsyncCallback）
- `frameworks/core/pipeline/pipeline_base.cpp:62-96`（PipelineBase 构造期注册 vsync callback）
- `frameworks/core/pipeline/pipeline_base.cpp:240-245`（RequestFrame proxy）
- `frameworks/core/pipeline/pipeline_base.cpp:748-783`（OnVsyncEvent）
