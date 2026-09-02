# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Render 阶段与渲染树同步 |
| 特性编号 | Func-03-01-01-Feat-04 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | ace_engine `a1d59fe7ee39`；nodeRenderState dynamic API 20+、static API 26+；sdk-js `f99d19c530d8` |
| SIG 归属 | ArkUI SIG / 渲染管线团队 |
| 状态 | Draft |
| 复杂度 | 复杂 |

> 本 Feat 覆盖渲染树同步、`isPendingState_` 生命周期，以及 Render 阶段的 dirty 调度、PaintWrapper Modifier/Draw 分流和 RS 录制边界。Feat-01 仅负责一帧总编排；本 Feat 负责 Render 阶段内部行为，不重复定义 VSync、Build 或 Layout 的主流程。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 渲染树同步链路规格 | 补录已有实现的行为规格 |
| ADDED | isPendingState_ 生命周期约束 | 明确状态标记的语义、配对规则和时序约束 |
| ADDED | ProcessRenderTreeDiff 语义 | 明确 Attach/Detach 的调用时序和参数传递规则 |
| ADDED | 可见子节点收集规格 | 明确 GenerateOneDepthVisibleFrameWithTransition 的收集规则 |
| ADDED | Z 序排序与 RS 节点树重建规格 | 明确 frameChildren_ 排序和 RebuildFrame diff 机制 |
| ADDED | 渲染状态监控规格 | 明确 NodeRenderStatusMonitor 的状态判断和回调机制 |
| ADDED | Render dirty 节点调度规格 | 明确 CreateRenderTask、FlushRenderTask 的入队、排空和幂等约束 |
| ADDED | PaintWrapper 绘制分流规格 | 明确 Content/Overlay/Foreground Modifier 优先及 Draw fallback |

## 输入文档

- 关联设计：`specs/03-engine-framework/01-render-pipeline/01-basic-render-pipeline/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 已提交源码基线：ace_engine `a1d59fe7ee39b8d6e6ed8cceaa95358d6824f9aa`
- SDK 基线：sdk-js `f99d19c530d8cd7cad8fbcccf020970df03f7004`
- 源码定位（关键文件）：
  - `frameworks/core/components_ng/base/frame_node.cpp`
  - `frameworks/core/components_ng/base/frame_node.h`
  - `frameworks/core/components_ng/base/ui_node.cpp`
  - `frameworks/core/components_ng/base/ui_node.h`
  - `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp`
  - `frameworks/core/components_ng/render/adapter/rosen_render_context.h`
  - `frameworks/core/components_ng/pattern/pattern.h`
  - `frameworks/core/components_ng/pattern/image/image_pattern.cpp`
  - `frameworks/core/components_ng/base/node_render_status_monitor.cpp`
  - `frameworks/core/components_ng/base/node_render_status_monitor.h`
  - `frameworks/core/pipeline_ng/ui_task_scheduler.cpp`
  - `frameworks/core/components_ng/render/paint_wrapper.cpp`
  - `frameworks/core/components_ng/render/adapter/rosen_window.cpp`

## 用户故事

### US-1: 逻辑节点树变更同步到 RS 渲染节点树

**作为** 渲染管线维护者
**我想要** 子节点增删移、Z 序变化、可见性/转场状态变化能通过 MarkNeedSyncRenderTree → RebuildRenderContextTree 链路同步到 RS 渲染节点树
**以便** 渲染结果反映最新的逻辑节点树状态

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `AddChild`/`RemoveChild`/`MovePosition` 成功改变逻辑子树 THEN 调用 `MarkNeedSyncRenderTree`，并使目标 FrameNode 的 `needSyncRenderTree_` 置为 true；WHEN 操作因前置校验提前返回且未改变子树 THEN 不要求置位。来源：`frameworks/core/components_ng/base/ui_node.cpp:418,548,859,1215-1246`、`frameworks/core/components_ng/base/frame_node.cpp:6827-6836` | 正常 |
| AC-1.2 | WHEN `RebuildRenderContextTree` 执行且 `needSyncRenderTree_` 为 false THEN 提前返回，不执行任何同步。来源：`frameworks/core/components_ng/base/frame_node.cpp:3331-3337` | 正常 |
| AC-1.3 | WHEN `RebuildRenderContextTree` 执行 THEN 快照旧 `frameChildren_`，清空并按新可见子节点重建 `frameChildren_` multiset，通过 `ProcessRenderTreeDiff` 计算 Attach/Detach，调用 `renderContext_->RebuildFrame` 重建 RS 节点树，最后调用 `pattern_->OnRebuildFrame`。来源：`frameworks/core/components_ng/base/frame_node.cpp:3342-3363` | 正常 |
| AC-1.4 | WHEN `RebuildRenderContextTree` 执行完成 THEN `needSyncRenderTree_` 被设为 false。来源：`frameworks/core/components_ng/base/frame_node.cpp:3363` | 正常 |
| AC-1.5 | WHEN `isLayoutNode_` 节点调用 `MarkNeedSyncRenderTree` THEN 委托给父节点，同时设置自身 `needSyncRenderTree_=true`（`needRebuild=true` 时额外调用 `frameProxy_->ResetChildren(true)`）。来源：`frameworks/core/components_ng/base/frame_node.cpp:6827-6836` | 边界 |
| AC-1.6 | WHEN `isDeleteRsNode_` 为 true THEN 在 `RebuildRenderContextTree` 末尾触发父节点的 `MarkNeedSyncRenderTree` 和 `RebuildRenderContextTree`。来源：`frameworks/core/components_ng/base/frame_node.cpp:3356-3362` | 边界 |

### US-2: isPendingState_ 生命周期标记配对

**作为** 渲染管线维护者
**我想要** FrameNode 的 `isPendingState_` 标记按现有 Attach/Detach 调用规则配对
**以便** 依赖 `OnAttachToMainRenderTree`/`OnDetachFromMainRenderTree` 的功能获得一致的生命周期通知

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `AttachToRenderTree(isOnMainTree=true)` 被调用且 `isPendingState_` 为 false THEN `isPendingState_` 被设为 true，`OnAttachToMainRenderTree()` 被调用，子节点递归 Attach。来源：`frameworks/core/components_ng/base/frame_node.cpp:3434-3449` | 正常 |
| AC-2.2 | WHEN `AttachToRenderTree(isOnMainTree=false)` 被调用 THEN 提前返回，`isPendingState_` 不变，`OnAttachToMainRenderTree()` 不被调用。来源：`frameworks/core/components_ng/base/frame_node.cpp:3436` | 正常 |
| AC-2.3 | WHEN `AttachToRenderTree(isOnMainTree=true)` 被调用且 `isPendingState_` 已为 true THEN 提前返回，`OnAttachToMainRenderTree()` 不被调用。来源：`frameworks/core/components_ng/base/frame_node.cpp:3436` | 正常 |
| AC-2.4 | WHEN `DetachFromRenderTree(isOnMainTree=true)` 被调用且 `isPendingState_` 为 true THEN `isPendingState_` 被设为 false，子节点递归 Detach，`OnDetachFromMainRenderTree()` 被调用。来源：`frameworks/core/components_ng/base/frame_node.cpp:3417-3432` | 正常 |
| AC-2.5 | WHEN `DetachFromRenderTree(isOnMainTree=false)` 被调用 THEN 提前返回，`isPendingState_` 不变，`OnDetachFromMainRenderTree()` 不被调用。来源：`frameworks/core/components_ng/base/frame_node.cpp:3419` | 正常 |
| AC-2.6 | WHEN `DetachFromRenderTree(isOnMainTree=true)` 被调用且 `isPendingState_` 为 false THEN 提前返回，`OnDetachFromMainRenderTree()` 不被调用。来源：`frameworks/core/components_ng/base/frame_node.cpp:3419` | 正常 |
| AC-2.7 | WHEN 根节点 FrameNode 构造时 THEN `isPendingState_` 初始化为 true。来源：`frameworks/core/components_ng/base/frame_node.cpp:695-696` | 边界 |
| AC-2.8 | WHEN FrameNode 析构时且 `isPendingState_` 为 true THEN `CleanRenderTreeLifeCycle` 调用 `DetachFromRenderTree(true, true)` 进行清理。来源：`frameworks/core/components_ng/base/frame_node.cpp:786-806,3410-3415` | 边界 |

### US-3: ProcessRenderTreeDiff 的 Attach/Detach 时序

**作为** 渲染管线维护者
**我想要** 明确 ProcessRenderTreeDiff 中 Attach/Detach 的现有调用时序和参数传递
**以便** 下游变更能够识别同帧跨父节点重挂载时的已知状态偏差

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `ProcessRenderTreeDiff` 执行 THEN 先处理新增子节点（AttachToRenderTree），再处理移除子节点（DetachFromRenderTree）。来源：`frameworks/core/components_ng/base/frame_node.cpp:3395-3406` | 正常 |
| AC-3.2 | WHEN `ProcessRenderTreeDiff` 调用 `AttachToRenderTree`/`DetachFromRenderTree` THEN 传递父节点的 `isPendingState_` 作为 `isOnMainTree` 参数。来源：`frameworks/core/components_ng/base/frame_node.cpp:3398,3405` | 正常 |
| AC-3.3 | WHEN 节点在同一帧中从旧父节点下树、重新上树到新父节点，且新父节点 ProcessRenderTreeDiff 先于旧父节点执行 THEN `AttachToRenderTree` 因子节点 `isPendingState_=true` 而 early return，随后旧父节点 `DetachFromRenderTree` 错误地将 `isPendingState_` 设为 false。**此为已知缺陷**。来源：`frameworks/core/components_ng/base/frame_node.cpp:3395-3406,3417-3449` | 异常 |

### US-4: 可见子节点收集

**作为** 渲染管线维护者
**我想要** GenerateOneDepthVisibleFrameWithTransition 按现有规则收集可见子节点和转场中的子节点
**以便** 转出动画节点在动画完成前保留在渲染树中，其他不参与渲染的节点被排除

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN FrameNode 为 `isActive_` 且 `IsVisible()` 为 true THEN 该节点被加入可见子节点列表。来源：`frameworks/core/components_ng/base/frame_node.cpp:3771` | 正常 |
| AC-4.2 | WHEN FrameNode 为 `isActive_` 且 `IsVisible()` 为 false 但 `HasTransitionOutAnimation()` 为 true THEN 该节点仍被加入可见子节点列表。来源：`frameworks/core/components_ng/base/frame_node.cpp:3771` | 正常 |
| AC-4.3 | WHEN FrameNode 不为 `isActive_` 且无转出动画 THEN 该节点不被加入可见子节点列表。来源：`frameworks/core/components_ng/base/frame_node.cpp:3771` | 正常 |
| AC-4.4 | WHEN 父节点存在 `disappearingChildren_` THEN `MergeChildrenWithDisappearingChildren` 将消失子节点按原始位置合并回子节点列表。来源：`frameworks/core/components_ng/base/ui_node.cpp:1848-1867` | 正常 |
| AC-4.5 | WHEN `GenerateRenderTreeFrameChildren` 执行 THEN 在可见子节点列表后追加 `overlayNode_`（如可见）和 `accessibilityFocusPaintNode_`。来源：`frameworks/core/components_ng/base/frame_node.cpp:3366-3379` | 正常 |
| AC-4.6 | WHEN `isLayoutNode_` 节点执行 `OnGenerateOneDepthVisibleFrameWithTransition` THEN 递归收集子节点，不将自身加入列表。来源：`frameworks/core/components_ng/base/frame_node.cpp:3760-3765` | 边界 |

### US-5: Z 序排序与 RS 节点树重建

**作为** 渲染管线维护者
**我想要** frameChildren_ 按 ZIndex 排序，并由 RS 子树重建链路执行增量 diff
**以便** 子节点 Z 序变化反映到渲染结果，同时避免无条件全量重建

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `frameChildren_` 被重建 THEN 使用 `ZIndexComparator` 按 `GetZIndexValue` 升序排序，允许重复 ZIndex。来源：`frameworks/core/components_ng/base/frame_node.h:423-425`、`frameworks/core/components_ng/base/frame_node.cpp:729-742` | 正常 |
| AC-5.2 | WHEN `RebuildFrame` 被调用且宿主 FrameNode 的 `MountPolicy` 为 `MIXED` THEN 调用 `ReCreateMixedRsNodeTree`，并从宿主的 mixed render child list 构造目标 RS 节点列表；传入 `RebuildFrame` 的 `children` 参数在该分支不作为目标列表来源。来源：`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5266-5280,5479-5495` | 正常 |
| AC-5.3 | WHEN `RebuildFrame` 被调用且 `MountPolicy` 非 `MIXED` THEN 调用 `ReCreateRsNodeTree`，仅包含 FrameNode 子节点。来源：`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5459-5477` | 正常 |
| AC-5.4 | WHEN `ReCreateRsNodeTreeByTargetList` 执行 THEN 对比当前 RS 子节点列表与目标列表，移除不在目标中的节点，添加新节点，移动已有节点到正确位置。来源：`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5498-5552` | 正常 |
| AC-5.5 | WHEN `isNeedRebuildRSTree_` 为 false THEN `ReCreateRsNodeTree`/`ReCreateMixedRsNodeTree` 提前返回，不重建 RS 节点树。来源：`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5461,5481,5502`（行为）、`frameworks/core/components_ng/render/render_context.h:913`（成员声明） | 边界 |

### US-6: 渲染状态监控

**作为** 应用开发者
**我想要** 通过 UIContext 的 nodeRenderState API 监听指定节点的渲染状态变化
**以便** 在节点进入或离开当前实现判定的渲染状态时执行相应逻辑

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `UIContext.on('nodeRenderState', ...)`（API 20+）或 `onNodeRenderState(...)`（API 26+）注册成功 THEN 立即以当前状态执行一次回调；同一 FrameNode 上 `resourceId=0` 的 OBSERVER 监听最多一份，非零 resourceId 监听按 resourceId 去重。来源：`interfaces/napi/kits/observer/ui_observer.cpp:1747-1788`、`frameworks/core/components_ng/base/node_render_status_monitor.cpp:62-94` | 正常 |
| AC-6.2 | WHEN `WalkThroughAncestorForStateListener` 在 `UITaskScheduler::FlushTask` 和资源重载完成后执行且存在状态变化 THEN 先批量触发 `ABOUT_TO_RENDER_IN` 回调，再批量触发 `ABOUT_TO_RENDER_OUT` 回调。来源：`frameworks/core/pipeline_ng/pipeline_context.cpp:1294-1303`、`frameworks/core/components_ng/base/node_render_status_monitor.cpp:119-151` | 正常 |
| AC-6.3 | WHEN `GetNodeCurrentRenderState` 判断状态 THEN 先检查目标节点的 visible/active/on-main-tree；目标无 parent 时返回 OUT；向上遍历时，遇到非根 FrameNode 继续检查同三项，遇到 root FrameNode 直接返回 IN 而不检查 root 的三项；遍历未到达 root 时返回 OUT。该判定不读取 `isPendingState_` 或 RS 物理树状态。来源：`frameworks/core/components_ng/base/node_render_status_monitor.cpp:171-197` | 正常 |
| AC-6.4 | WHEN FrameNode 清理 Pipeline 资源且当前 PipelineContext 和该节点监听条目均存在 THEN `NotifyFrameNodeRelease` 触发 `ABOUT_TO_RENDER_OUT`（`NODE_RELEASE`）并移除该节点全部监听；条件不满足时不触发。来源：`frameworks/core/components_ng/base/frame_node.cpp:786-806,8677-8703`、`frameworks/core/components_ng/base/node_render_status_monitor.cpp:155-169` | 边界 |
| AC-6.5 | WHEN 当前 UI 实例的 Monitor 已占用 64 个 FrameNode 监听条目 THEN 公开 API 的后续注册请求在解析目标节点前被拒绝并报告错误码 161001。来源：`frameworks/core/components_ng/base/node_render_status_monitor.cpp:27-32,62-68`、`interfaces/napi/kits/observer/js_ui_observer.cpp:1503-1525` | 边界 |

### US-7: Render dirty 节点调度与 Paint 分流

**作为** 渲染管线维护者
**我想要** dirty render 节点在 `UITaskScheduler::FlushTask` 的 Render 阶段被一次性排空，并由 `PaintWrapper::FlushRender` 在 Modifier 与 Draw 之间选择路径
**以便** 布局完成后的绘制结果稳定提交到 RS，且属性动画不会重复录制 Draw

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `FrameNode::MarkNeedRender` 被调用 THEN 节点设置 `PROPERTY_UPDATE_RENDER`；已处于 Render/Layout dirty 状态时直接返回；Render boundary 节点加入 dirty render 队列，非 boundary 节点向父节点传播 `PROPERTY_UPDATE_RENDER_BY_CHILD_REQUEST`。来源：`frameworks/core/components_ng/base/frame_node.cpp:3668-3700` | 正常 |
| AC-7.2 | WHEN `UITaskScheduler::FlushTask` 完成布局轮次 THEN 执行 `FlushAllSingleNodeTasks` 后再执行 `FlushRenderTask`；Render 不得越过 Layout 独立提前执行。来源：`frameworks/core/pipeline_ng/ui_task_scheduler.cpp:300-337` | 正常 |
| AC-7.3 | WHEN `FrameNode::CreateRenderTask` 被调用且 `isRenderDirtyMarked_` 为 false THEN 返回空任务；创建 PaintWrapper 时清除该标记。来源：`frameworks/core/components_ng/base/frame_node.cpp:3109-3115,3308-3312` | 边界 |
| AC-7.4 | WHEN `PaintWrapper::FlushRender` 存在任一 Modifier THEN 先调用对应 `UpdateXxxModifier`；仅跳过同类型 Draw，其他未被 Modifier 覆盖的类型仍可执行 Draw；`StartRecording` 与 `StopRecordingIfNeeded` 不因 Modifier 存在而跳过。来源：`frameworks/core/components_ng/render/paint_wrapper.cpp:152-240` | 正常 |
| AC-7.5 | WHEN `PaintWrapper::FlushRender` 执行 THEN 无条件调用 `StartRecording`，未被 Modifier 覆盖的 ContentDraw/ForegroundDraw/OverlayDraw 按顺序经 `FlushXxxDrawFunction → RSNode::DrawOnNode` 独立录制，最后调用 `StopRecordingIfNeeded`；free RenderContext 延迟到挂载主树后执行，其他情况仅对 CanvasNode 生效并委托 `RSCanvasNode::FinishRecording`，无活动录制或空 command list 不产生新的 recording 更新。来源：`frameworks/core/components_ng/render/paint_wrapper.cpp:182-240`、`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:115-123,504-520,4989-5068`、跨仓 graphic_2d 的 RSCanvasNode 实现（BeginRecording / FinishRecording / DrawOnNode） | 边界 |
| AC-7.6 | WHEN Render 阶段产生 RS 修改 THEN 在 `FlushMessages` 调用 `window_->FlushTasks` 并由 `RosenWindow::FlushTasks` 调用 `SendMessages`；该边界之后产生的修改延至下一帧。来源：`frameworks/core/pipeline_ng/pipeline_context.cpp:1315-1325,1667-1685`、`frameworks/core/components_ng/render/adapter/rosen_window.cpp:405-413` | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|--------|----------|-----------|----------|------|
| AC-1.1 | R-1 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/ui_node.cpp:418,548,859,1215-1246` |
| AC-1.2 | R-2 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3331-3337` |
| AC-1.3 | R-3 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3342-3363` |
| AC-1.4 | R-2 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3363` |
| AC-1.5 | R-4 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:6827-6836` |
| AC-1.6 | R-5 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3356-3362` |
| AC-2.1 | R-6 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3434-3449` |
| AC-2.2 | R-7 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3436` |
| AC-2.3 | R-8 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3436` |
| AC-2.4 | R-6 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3417-3432` |
| AC-2.5 | R-7 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3419` |
| AC-2.6 | R-9 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3419` |
| AC-2.7 | R-10 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:695-696` |
| AC-2.8 | R-11 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:786-806,3410-3415` |
| AC-3.1 | R-12 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3395-3406` |
| AC-3.2 | R-13 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3398,3405` |
| AC-3.3 | R-14 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3395-3406,3417-3449` |
| AC-4.1 | R-15 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3771` |
| AC-4.2 | R-16 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3771` |
| AC-4.3 | R-15 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3771` |
| AC-4.4 | R-17 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/ui_node.cpp:1848-1867` |
| AC-4.5 | R-18 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3366-3379` |
| AC-4.6 | R-19 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3760-3765` |
| AC-5.1 | R-20 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.h:423-425`、`frameworks/core/components_ng/base/frame_node.cpp:729-742` |
| AC-5.2 | R-21 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5266-5280,5479-5495` |
| AC-5.3 | R-21 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5459-5477` |
| AC-5.4 | R-22 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5498-5552` |
| AC-5.5 | R-23 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5461,5481,5502` |
| AC-6.1 | R-24 | Feat-04 | SDK + 已提交源码核验 | `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts:2607-2635`、`interfaces/napi/kits/observer/ui_observer.cpp:1747-1788` |
| AC-6.2 | R-25 | Feat-04 | 已提交源码核验 | `frameworks/core/pipeline_ng/pipeline_context.cpp:1294-1303`、`frameworks/core/components_ng/base/node_render_status_monitor.cpp:119-151` |
| AC-6.3 | R-26 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/node_render_status_monitor.cpp:171-197` |
| AC-6.4 | R-27 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:786-806,8677-8703`、`frameworks/core/components_ng/base/node_render_status_monitor.cpp:155-169` |
| AC-6.5 | R-28 | Feat-04 | SDK + 已提交源码核验 | `interface/sdk-js/api/@ohos.arkui.UIContext.static.d.ets:2062-2082`、`interfaces/napi/kits/observer/js_ui_observer.cpp:1503-1525` |
| AC-7.1 | R-29 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3668-3700` |
| AC-7.2 | R-30 | Feat-04 | 已提交源码核验 | `frameworks/core/pipeline_ng/ui_task_scheduler.cpp:300-337` |
| AC-7.3 | R-31 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3109-3115,3308-3312` |
| AC-7.4 | R-32 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/render/paint_wrapper.cpp:152-240` |
| AC-7.5 | R-33 | Feat-04 | 已提交源码核验 | `frameworks/core/components_ng/render/paint_wrapper.cpp:182-240`、`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:115-123,504-520,4989-5068`、跨仓 graphic_2d 的 RSCanvasNode 实现（BeginRecording / FinishRecording / DrawOnNode） |
| AC-7.6 | R-34 | Feat-04 | 已提交源码核验 | `frameworks/core/pipeline_ng/pipeline_context.cpp:1315-1325,1667-1685`、`frameworks/core/components_ng/render/adapter/rosen_window.cpp:405-413` |

## 规则定义

> **统一规则表。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `AddChild`/`RemoveChild`/`MovePosition` 成功改变子树 | 调用 `MarkNeedSyncRenderTree`，目标 FrameNode 的 `needSyncRenderTree_` 置 true；未改变子树的提前返回路径不置位。来源：`frameworks/core/components_ng/base/ui_node.cpp:418,548,859,1215-1246`、`frameworks/core/components_ng/base/frame_node.cpp:6827-6836` | 操作必须成功改变树结构 | AC-1.1 |
| R-2 | 行为 | `RebuildRenderContextTree` 执行 | `needSyncRenderTree_` 为 false 时提前返回；执行完成后设为 false。来源：`frameworks/core/components_ng/base/frame_node.cpp:3335-3337,3363` | — | AC-1.2, AC-1.4 |
| R-3 | 行为 | `RebuildRenderContextTree` 执行 | 快照旧 `frameChildren_` → 清空并重建 `frameChildren_` multiset → `ProcessRenderTreeDiff` → `renderContext_->RebuildFrame` → `pattern_->OnRebuildFrame`。来源：`frameworks/core/components_ng/base/frame_node.cpp:3342-3363` | — | AC-1.3 |
| R-4 | 行为 | `isLayoutNode_` 节点调用 `MarkNeedSyncRenderTree` | 委托给父节点，同时设置自身 `needSyncRenderTree_=true`（`needRebuild=true` 时额外调用 `frameProxy_->ResetChildren(true)`）。来源：`frameworks/core/components_ng/base/frame_node.cpp:6827-6836` | — | AC-1.5 |
| R-5 | 行为 | `isDeleteRsNode_` 为 true | 触发父节点的 `MarkNeedSyncRenderTree` 和 `RebuildRenderContextTree`。来源：`frameworks/core/components_ng/base/frame_node.cpp:3356-3362` | — | AC-1.6 |
| R-6 | 行为 | `AttachToRenderTree`/`DetachFromRenderTree` 被调用 | `isOnMainTree=true` 且 `isPendingState_` 未匹配时执行：Attach 设 true 并调用 `OnAttachToMainRenderTree`；Detach 设 false 并调用 `OnDetachFromMainRenderTree`。来源：`frameworks/core/components_ng/base/frame_node.cpp:3417-3449` | — | AC-2.1, AC-2.4 |
| R-7 | 行为 | `isOnMainTree=false` | `AttachToRenderTree`/`DetachFromRenderTree` 提前返回，`isPendingState_` 不变。来源：`frameworks/core/components_ng/base/frame_node.cpp:3419,3436` | — | AC-2.2, AC-2.5 |
| R-8 | 行为 | `AttachToRenderTree(isOnMainTree=true)` 且 `isPendingState_` 已为 true | 提前返回，`OnAttachToMainRenderTree` 不被调用。来源：`frameworks/core/components_ng/base/frame_node.cpp:3436` | — | AC-2.3 |
| R-9 | 行为 | `DetachFromRenderTree(isOnMainTree=true)` 且 `isPendingState_` 为 false | 提前返回，`OnDetachFromMainRenderTree` 不被调用。来源：`frameworks/core/components_ng/base/frame_node.cpp:3419` | — | AC-2.6 |
| R-10 | 边界 | 根节点 FrameNode 构造 | `isPendingState_` 初始化为 true。来源：`frameworks/core/components_ng/base/frame_node.cpp:695-696` | — | AC-2.7 |
| R-11 | 恢复 | FrameNode 析构且 `isPendingState_=true` | `CleanRenderTreeLifeCycle` 调用 `DetachFromRenderTree(true, true)` 进行清理。来源：`frameworks/core/components_ng/base/frame_node.cpp:799,3410-3415` | — | AC-2.8 |
| R-12 | 行为 | `ProcessRenderTreeDiff` 执行 | 先处理新增子节点（AttachToRenderTree），再处理移除子节点（DetachFromRenderTree）。来源：`frameworks/core/components_ng/base/frame_node.cpp:3395-3406` | — | AC-3.1 |
| R-13 | 行为 | `ProcessRenderTreeDiff` 调用 Attach/Detach | 传递父节点的 `isPendingState_` 作为 `isOnMainTree` 参数。来源：`frameworks/core/components_ng/base/frame_node.cpp:3398,3405` | — | AC-3.2 |
| R-14 | 异常 | 同帧下树重新上树 | 新父节点 AttachToRenderTree 因子节点 `isPendingState_=true` 而 early return，旧父节点 DetachFromRenderTree 错误地将 `isPendingState_` 设为 false。**此为已知缺陷**，实际影响为 `OnAttachToMainRenderTree`/`OnDetachFromMainRenderTree` 回调错乱（经 `AttachToRenderTree`/`DetachFromRenderTree` 触发）；`ImagePattern::OnWindowHide` 的回收判定走 `renderContext->IsOnRenderTree()`（`rsNode_->GetIsOnTheTree()`，RS 物理层），不直接受 `isPendingState_` 影响。来源：`frameworks/core/components_ng/base/frame_node.cpp:3398,3405`、`frameworks/core/components_ng/pattern/image/image_pattern.cpp:1787-1797`、`frameworks/core/components_ng/render/adapter/rosen_render_context.h:621-627` | 跨父节点时序不保证 | AC-3.3 |
| R-15 | 行为 | `OnGenerateOneDepthVisibleFrameWithTransition` 判断 | `isActive_` 且 `IsVisible()` 的节点加入可见列表；`isActive_` 且不可见但 `HasTransitionOutAnimation()` 的节点仍加入；不 active 且无转出动画的节点排除。来源：`frameworks/core/components_ng/base/frame_node.cpp:3771` | — | AC-4.1, AC-4.3 |
| R-16 | 行为 | FrameNode 不可见但有转出动画 | 仍被加入可见子节点列表，保证转出动画在渲染树中完成。来源：`frameworks/core/components_ng/base/frame_node.cpp:3771` | — | AC-4.2 |
| R-17 | 行为 | 父节点存在 `disappearingChildren_` | `MergeChildrenWithDisappearingChildren` 将消失子节点按原始位置合并回子节点列表。来源：`frameworks/core/components_ng/base/ui_node.cpp:1848-1867` | — | AC-4.4 |
| R-18 | 行为 | `GenerateRenderTreeFrameChildren` 执行 | 在可见子节点列表后追加 `overlayNode_`（如可见）和 `accessibilityFocusPaintNode_`。来源：`frameworks/core/components_ng/base/frame_node.cpp:3366-3379` | — | AC-4.5 |
| R-19 | 边界 | `isLayoutNode_` 节点执行 `OnGenerateOneDepthVisibleFrameWithTransition` | 递归收集子节点，不将自身加入列表；追加 `overlayNode_`。来源：`frameworks/core/components_ng/base/frame_node.cpp:3760-3765` | — | AC-4.6 |
| R-20 | 行为 | `frameChildren_` 重建 | 使用 `ZIndexComparator` 按 `GetZIndexValue` 升序排序，允许重复 ZIndex。来源：`frameworks/core/components_ng/base/frame_node.h:423-425`、`frameworks/core/components_ng/base/frame_node.cpp:729-742` | — | AC-5.1 |
| R-21 | 行为 | `RebuildFrame` 被调用 | `MountPolicy::MIXED` 调用 `ReCreateMixedRsNodeTree`，目标仅来自宿主 mixed render child list，忽略传入的 `children`；非 MIXED 调用 `ReCreateRsNodeTree` 并使用 `children`。来源：`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5107-5115,5266-5280,5459-5495` | MIXED 用例必须预先构造 mixed render child list | AC-5.2, AC-5.3 |
| R-22 | 行为 | `ReCreateRsNodeTreeByTargetList` 执行 | 对比当前 RS 子节点列表与目标列表，移除不在目标中的节点，添加新节点，移动已有节点到正确位置。来源：`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5498-5552` | — | AC-5.4 |
| R-23 | 边界 | `isNeedRebuildRSTree_` 为 false | `ReCreateRsNodeTree`/`ReCreateMixedRsNodeTree` 提前返回，不重建 RS 节点树。来源：`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5461,5481,5502`（行为）、`frameworks/core/components_ng/render/render_context.h:913`（成员声明） | — | AC-5.5 |
| R-24 | 行为 | nodeRenderState 外部 API 注册 | 成功注册后立即回调当前状态；`resourceId=0` 的 OBSERVER 每节点最多一份，非零 resourceId 按 resourceId 去重。来源：`interfaces/napi/kits/observer/ui_observer.cpp:1747-1788`、`frameworks/core/components_ng/base/node_render_status_monitor.cpp:62-94` | 不等同于“每节点只能一个 callback” | AC-6.1 |
| R-25 | 行为 | `WalkThroughAncestorForStateListener` 在帧 flush 中执行 | 在 `FlushTask` 与资源重载之后检查状态变化，先触发 IN 组，再触发 OUT 组；不是 `FlushAfterRenderTask` 阶段。来源：`frameworks/core/pipeline_ng/pipeline_context.cpp:1294-1303`、`frameworks/core/components_ng/base/node_render_status_monitor.cpp:119-151` | 仅状态发生变化时入回调队列 | AC-6.2 |
| R-26 | 行为 | `GetNodeCurrentRenderState` 判断节点状态 | 检查目标节点及到 root 之前的非根 FrameNode；目标无 parent 返回 OUT，遇到 root 直接返回 IN且不检查 root 状态。只读 visible/active/on-main-tree，不读 `isPendingState_` 或 RS 物理树。来源：`frameworks/core/components_ng/base/node_render_status_monitor.cpp:171-197` | SDK 的“参与渲染”表述与源码的可见性判定存在语义偏差 | AC-6.3 |
| R-27 | 边界 | FrameNode 清理 Pipeline 资源 | 仅当 PipelineContext 与监听条目存在时，触发 `ABOUT_TO_RENDER_OUT(NODE_RELEASE)` 并移除监听。来源：`frameworks/core/components_ng/base/frame_node.cpp:786-806,8677-8703`、`frameworks/core/components_ng/base/node_render_status_monitor.cpp:155-169` | 非无条件析构通知 | AC-6.4 |
| R-28 | 边界 | Monitor 的 FrameNode 监听条目达到 64 | 公开 API 的后续注册请求在解析目标节点前被拒绝并报告 161001。来源：`frameworks/core/components_ng/base/node_render_status_monitor.cpp:27-32,62-68`、`interfaces/napi/kits/observer/js_ui_observer.cpp:1503-1525` | `MAX_NODE_RENDER_STATE_LISTENERS=64` 统计 map key；公开入口先执行上限检查 | AC-6.5 |

## Render 阶段规则补充

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-29 | 行为 | `FrameNode::MarkNeedRender` 成功标记 | 设置 Render dirty 标志；已处于 Render/Layout dirty 状态时返回；Render boundary 节点入队，非 boundary 节点向父级传播 child-request。来源：`frameworks/core/components_ng/base/frame_node.cpp:3668-3700` | — | AC-7.1 |
| R-30 | 行为 | `UITaskScheduler::FlushTask` 完成布局轮次 | 先执行 `FlushAllSingleNodeTasks`，再执行 `FlushRenderTask`。来源：`frameworks/core/pipeline_ng/ui_task_scheduler.cpp:300-337` | Render 不得跨越 Layout 提前执行 | AC-7.2 |
| R-31 | 边界 | `CreateRenderTask` 的 `isRenderDirtyMarked_` 为 false | 返回空任务；创建 PaintWrapper 时清除该标志。来源：`frameworks/core/components_ng/base/frame_node.cpp:3109-3115,3308-3312` | — | AC-7.3 |
| R-32 | 行为 | PaintWrapper 存在任一 Modifier | 更新对应 Modifier，并跳过同类型 Draw；其他未被覆盖的类型仍可 Draw，StartRecording/StopRecordingIfNeeded 仍执行。来源：`frameworks/core/components_ng/render/paint_wrapper.cpp:152-240` | Modifier 按类型优先，不是整条 Paint 路径互斥 | AC-7.4 |
| R-33 | 边界 | `PaintWrapper::FlushRender` 执行 | 无条件 StartRecording；未被 Modifier 覆盖的 Content/Foreground/Overlay Draw 经 DrawOnNode 独立录制；末尾 StopRecordingIfNeeded 在 free RenderContext 上延迟到挂载主树后执行，其他情况仅对 CanvasNode 生效并委托 FinishRecording，后者在无活动录制或空 command list 时不生成 recording 更新。来源：`frameworks/core/components_ng/render/paint_wrapper.cpp:182-240`、`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:115-123,504-520,4989-5068`、跨仓 graphic_2d 的 RSCanvasNode 实现（BeginRecording / FinishRecording / DrawOnNode） | Start/Stop 维护主 recording 生命周期，三类 Draw 使用各自 DrawOnNode recording | AC-7.5 |
| R-34 | 边界 | Render 产生 RS 修改 | `FlushMessages` 经 `RosenWindow::FlushTasks` 调用 `SendMessages`；该边界之后的修改延至下一帧。来源：`frameworks/core/pipeline_ng/pipeline_context.cpp:1315-1325,1667-1685`、`frameworks/core/components_ng/render/adapter/rosen_window.cpp:405-413` | 单帧唯一 RS 提交边界 | AC-7.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, AC-1.5, AC-1.6 / R-1, R-4, R-5 | 已提交源码核验 | 核对树操作成功路径、layout-node 委托与 isDeleteRsNode_ 父级上推 |
| VM-2 | AC-1.2, AC-1.4 / R-2 | 已提交源码核验 | 核对 early-return 与同步完成后的 flag 复位 |
| VM-3 | AC-1.3 / R-3 | 已提交源码核验 | 核对旧子集快照、diff、RebuildFrame 与 OnRebuildFrame 顺序 |
| VM-4 | AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6 / R-6, R-7, R-8, R-9 | 已提交源码核验 | 核对 Attach/Detach guard、状态翻转和递归调用 |
| VM-5 | AC-2.7 / R-10 | 已提交源码核验 | 核对根节点构造时的 pending 初值 |
| VM-6 | AC-2.8 / R-11 | 已提交源码核验 | 核对资源清理入口与生命周期 Detach 条件 |
| VM-7 | AC-3.1, AC-3.2 / R-12, R-13 | 已提交源码核验 | 核对 Attach-before-Detach 顺序及父节点状态参数传递 |
| VM-8 | AC-3.3 / R-14 | 已提交源码核验 | 由现有调用顺序与 guard 推导同帧跨父节点状态偏差，不引用工作树测试 |
| VM-9 | AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 / R-15, R-16, R-17, R-18, R-19 | 已提交源码核验 | 核对可见性、转场、消失节点、overlay/a11y 与 layout-node 收集规则 |
| VM-10 | AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5 / R-20, R-21, R-22, R-23 | 已提交源码核验 | 核对 ZIndex multiset、MIXED/普通目标来源、RS diff 与 rebuild guard |
| VM-11 | AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5 / R-24, R-25, R-26, R-27, R-28 | SDK + 已提交源码核验 | 核对公开 API、立即回调、resourceId、64 个 FrameNode 监听条目上限、FlushTask 后时序及 release 条件 |
| VM-12 | AC-7.1, AC-7.2, AC-7.3, AC-7.4, AC-7.5, AC-7.6 / R-29, R-30, R-31, R-32, R-33, R-34 | 已提交源码核验 | 核对 dirtyRenderNodes_ 入队幂等、Layout→Render 顺序、PaintWrapper Modifier/Draw 分流及 RS 提交边界 |

## API 变更分析

### 新增 API

N/A。本 Feat 为既有能力补录，不新增 Public/System/InnerApi。

**关联类型定义：**

公开接口使用 `NodeIdentity`、`NodeRenderStateChangeCallback` 和 `NodeRenderState`；内部实现还涉及：
- `FrameNode`（`frameworks/core/components_ng/base/frame_node.h`）
- `UINode`（`frameworks/core/components_ng/base/ui_node.h`）
- `RosenRenderContext`（`frameworks/core/components_ng/render/adapter/rosen_render_context.h`）
- `NodeRenderStatusMonitor`（`frameworks/core/components_ng/base/node_render_status_monitor.h`）

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

## 接口规格

> 本特性包含公开 ArkTS 监听接口和 FrameNode 私有实现方法。以下内部方法均位于 `FrameNode` 的 `private:` 区域，不属于 InnerApi，也不能由外部模块直接调用。

### 接口定义

#### 关联既有 Public API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `UIContext.on('nodeRenderState', nodeIdentity, callback)` | Public ArkTS dynamic，API 20+ | 固定事件名、NodeIdentity、NodeRenderStateChangeCallback | void | 161001 | 注册节点渲染状态监听，成功后立即回调当前状态 | AC-6.1, AC-6.5 |
| `UIContext.off('nodeRenderState', nodeIdentity, callback?)` | Public ArkTS dynamic，API 20+ | 固定事件名、NodeIdentity、可选 callback | void | 无声明 | 注销指定 callback；省略 callback 时注销该节点全部监听 | AC-6.1 |
| `UIContext.onNodeRenderState(nodeIdentity, callback)` | Public ArkTS static，API 26+ | NodeIdentity、NodeRenderStateChangeCallback | void | 161001 | 注册节点渲染状态监听，成功后立即回调当前状态 | AC-6.1, AC-6.5 |
| `UIContext.offNodeRenderState(nodeIdentity, callback?)` | Public ArkTS static，API 26+ | NodeIdentity、可选 callback | void | 无声明 | 注销指定 callback；省略 callback 时注销该节点全部监听 | AC-6.1 |

**UIContext nodeRenderState 注册接口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `on(type: 'nodeRenderState', nodeIdentity: NodeIdentity, callback: NodeRenderStateChangeCallback): void`；`onNodeRenderState(nodeIdentity: NodeIdentity, callback: NodeRenderStateChangeCallback): void` |
| 返回值 | `void` |
| 开放范围 | ArkTS public；动态接口 API 20+，静态接口 API 26+ |
| Kit / SysCap | ArkUI / `SystemCapability.ArkUI.ArkUI.Full` |
| 错误码 | 161001：单 UI 实例监控的不同节点数超过限制 |
| 关联 AC | AC-6.1, AC-6.5 |

**场景索引**

| 场景 | 关联 AC |
|------|---------|
| 注册成功后立即回调当前状态 | AC-6.1 |
| 64 个 FrameNode 监听条目后的超限拒绝 | AC-6.5 |
| off 省略 callback 时注销该节点全部监听 | AC-6.1 |

**FrameNode::AttachToRenderTree**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void FrameNode::AttachToRenderTree(bool isOnMainTree, bool recursive = true)` |
| 返回值 | `void` |
| 开放范围 | FrameNode private 实现方法 |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2, AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| isOnMainTree | bool | 是 | — | false 时立即 early-return，`isPendingState_` 不变 |
| recursive | bool | 否 | true | false 时仅处理当前节点，不递归 `frameChildren_` |

**场景索引：** 场景 4、5；关联 AC-2.1、AC-2.2、AC-2.3。

**FrameNode::DetachFromRenderTree**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void FrameNode::DetachFromRenderTree(bool isOnMainTree, bool recursive = true)` |
| 返回值 | `void` |
| 开放范围 | FrameNode private 实现方法 |
| 错误码 | N/A |
| 关联 AC | AC-2.4, AC-2.5, AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| isOnMainTree | bool | 是 | — | false 时立即 early-return；来源为父节点 isPendingState_（ProcessRenderTreeDiff 传递） |
| recursive | bool | 否 | true | CleanRenderTreeLifeCycle 析构路径传 true |

**场景索引：** 场景 6；关联 AC-2.4、AC-2.5、AC-2.6。

**FrameNode::ProcessRenderTreeDiff**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void FrameNode::ProcessRenderTreeDiff(const std::vector<RefPtr<FrameNode>>& newChildren, const std::multiset<WeakPtr<FrameNode>, ZIndexComparator>& oldChildren)` |
| 返回值 | `void` |
| 开放范围 | FrameNode private 实现方法 |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.2, AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| newChildren | vector<RefPtr<FrameNode>> | 是 | — | `GenerateRenderTreeFrameChildren` 生成的遍历顺序列表；不是 ZIndex 排序后的 `frameChildren_` |
| oldChildren | multiset<WeakPtr, ZIndexComparator> | 是 | — | 上一帧的 frameChildren_ 快照 |

**场景索引：** 场景 7；关联 AC-3.1、AC-3.2、AC-3.3。

---

## 兼容性声明

- **已有 API 行为变更:** 否；本 Feat 仅补录已提交实现与既有 SDK 契约。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** nodeRenderState dynamic API 20+；static API 26+；内部渲染树同步以已提交 ace_engine 基线为准。
- **API 版本号策略:** 沿用 canonical SDK 的 `@since` 标注，不新增版本门控。

### 已知兼容性说明

| 范围 | 行为差异 | 影响 | 迁移指引 |
|------|----------|------|----------|
| 内部实现 | `ProcessRenderTreeDiff` 中 `isPendingState_` 作为 `isOnMainTree` 传递（R-14 已知缺陷） | 同帧跨父节点重挂载时生命周期回调可能错乱 | 后续修复需验证所有重写 Attach/Detach 生命周期回调的 Pattern |
| API 20+ dynamic / API 26+ static | 动态与静态接口签名不同，但共享监控语义 | 调用方式和最低 API 版本不同 | 按目标 SDK 版本选择 `on/off` 或 `onNodeRenderState/offNodeRenderState` |
| SDK 与当前源码 | SDK 以“参与渲染/移出渲染树”描述状态；源码同时用 visible/active/on-main-tree 判定，遇到 root 时不检查 root 状态 | 应用观察结果可能与仅按 RS 物理树理解的结果不同 | 以 SDK 契约编程，源码偏差作为兼容风险保留 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| UI 线程执行 | `RebuildRenderContextTree` 在 UI 线程执行；多线程变体通过 `PostAfterAttachMainTreeTask` 投递 | AC-1.2, AC-1.3, AC-1.4 |
| 生命周期参数来源 | `ProcessRenderTreeDiff` 将父节点 `isPendingState_` 作为子节点 `isOnMainTree` 参数，跨父节点时序不保证 | AC-3.1, AC-3.2, AC-3.3 |
| RS 重建链路边界 | 本 Feat 的普通与 MIXED 重建目标最终交给 `ReCreateRsNodeTreeByTargetList`；不扩展为其他 RS 操作路径的全局禁令 | AC-5.2, AC-5.3, AC-5.4, AC-5.5 |
| Monitor 执行时序 | `WalkThroughAncestorForStateListener` 在 `FlushTask` 与资源重载后、`FlushAfterRenderTask` 前执行 | AC-6.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | N/A；本 Feat 不新增性能指标 | N/A | 已有能力补录 |
| 功耗 | N/A；不新增功耗行为 | N/A | 已有能力补录 |
| 内存 | N/A；不新增存储结构 | N/A | 已有能力补录 |
| 安全 | N/A；不新增权限、敏感数据或信任边界 | SDK/源码核验 | Public API 无权限声明 |
| 可靠性 | FrameNode 监听条目上限为 64；析构路径在 pending 状态下执行生命周期 Detach | 已提交源码核验 | `frameworks/core/components_ng/base/node_render_status_monitor.cpp:27-32,62-94`；`frameworks/core/components_ng/base/frame_node.cpp:786-806,3410-3415` |
| 可测试性 | 仅使用已提交生产源码与 canonical SDK；工作树未提交源码/测试不作为证据 | revision 与路径核验 | ace_engine `a1d59fe7ee39`；sdk-js `f99d19c530d8` |
| 自动化维测 | N/A；本 Feat 不新增自动化维测接口 | N/A | 已有能力补录 |
| 定界定位 | `ProcessRenderTreeDiff` 提供 `ACE_LAYOUT_SCOPED_TRACE` | 已提交源码核验 | `frameworks/core/components_ng/base/frame_node.cpp:3381-3387` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | `accessibilityFocusPaintNode_` 追加到渲染子节点列表 | AC-4.5 |
| 大字体 | 否 | 本 Feat 不处理字体度量或缩放 | N/A |
| 深色模式 | 否 | 本 Feat 不读取颜色模式或主题 | N/A |
| 多窗口/分屏 | 是 | 公开注册入口从当前容器取得 PipelineContext 及其 Monitor；本 Feat 不定义额外的跨窗口共享行为 | AC-6.2, AC-6.5 |
| 多用户 | 否 | 不涉及用户态数据或用户切换 | N/A |
| 版本升级 | 是 | dynamic API 20+、static API 26+，按目标 SDK 选择调用形式 | AC-6.1, AC-6.5 |
| 生态兼容 | 是 | SDK 与源码的 nodeRenderState 语义偏差需保留兼容风险 | AC-6.3 |

### 其他组件影响

- Image：Attach 生命周期回调用于重新加载；`OnWindowHide` 回收依据 RS 物理树状态，不直接依赖 `isPendingState_`。
- 动画/转场：`HasTransitionOutAnimation` 与 `disappearingChildren_` 决定转场节点是否继续参与渲染树收集。

## 行为场景

```gherkin
Feature: 渲染树同步与 isPendingState_ 生命周期
  As a 渲染管线维护者
  I want 逻辑节点树和渲染状态按已提交实现同步
  So that 下游行为能够基于可验证的现有契约演进

  Scenario: 子节点树成功变更触发 MarkNeedSyncRenderTree (AC-1.1, R-1)
  Given 一个 FrameNode 父节点，needSyncRenderTree_==false
  When AddChild、RemoveChild 或 MovePosition 成功改变子树
  Then MarkNeedSyncRenderTree 被调用
   And needSyncRenderTree_==true

  Scenario: needSyncRenderTree_ 为 false 时 RebuildRenderContextTree 提前返回 (AC-1.2, R-2)
  Given 一个 FrameNode，needSyncRenderTree_==false
  When 调用 RebuildRenderContextTree
  Then 直接返回，不执行任何同步操作

  Scenario: RebuildRenderContextTree 完整链路执行 (AC-1.3, AC-1.4, R-3)
  Given 一个 FrameNode，needSyncRenderTree_==true
  When 调用 RebuildRenderContextTree
  Then 旧 frameChildren_ 被快照
   And 新子节点列表被生成
   And ProcessRenderTreeDiff 计算差异
   And renderContext_->RebuildFrame 被调用
   And needSyncRenderTree_==false

  Scenario: AttachToRenderTree 正常执行 (AC-2.1, R-6)
  Given 一个 FrameNode，isPendingState_==false
  When 调用 AttachToRenderTree(isOnMainTree=true)
  Then isPendingState_==true
   And OnAttachToMainRenderTree() 被调用
   And 子节点递归 Attach

  Scenario: AttachToRenderTree 因 isPendingState_=true 而 early return (AC-2.3, R-8)
  Given 一个 FrameNode，isPendingState_==true
  When 调用 AttachToRenderTree(isOnMainTree=true)
  Then 直接返回
   And OnAttachToMainRenderTree() 不被调用

  Scenario: AttachToRenderTree 非主树调用提前返回 (AC-2.2, R-7)
  Given 一个 FrameNode，isPendingState_==false
  When 调用 AttachToRenderTree(isOnMainTree=false)
  Then 直接返回且 isPendingState_ 保持 false
   And OnAttachToMainRenderTree() 不被调用

  Scenario: DetachFromRenderTree 正常执行 (AC-2.4, R-6)
  Given 一个 FrameNode，isPendingState_==true
  When 调用 DetachFromRenderTree(isOnMainTree=true)
  Then isPendingState_==false
   And 子节点递归 Detach
   And OnDetachFromMainRenderTree() 被调用

  Scenario: DetachFromRenderTree 非主树调用提前返回 (AC-2.5, R-7)
  Given 一个 FrameNode，isPendingState_==true
  When 调用 DetachFromRenderTree(isOnMainTree=false)
  Then 直接返回且 isPendingState_ 保持 true
   And OnDetachFromMainRenderTree() 不被调用

  Scenario: DetachFromRenderTree 已脱离时提前返回 (AC-2.6, R-9)
  Given 一个 FrameNode，isPendingState_==false
  When 调用 DetachFromRenderTree(isOnMainTree=true)
  Then 直接返回且 OnDetachFromMainRenderTree() 不被调用

  Scenario: 根节点构造初始化 pending 状态 (AC-2.7, R-10)
  Given 创建根 FrameNode
  When FrameNode 构造完成
  Then isPendingState_==true

  Scenario: 同帧下树重新上树 isPendingState_ 错乱 (AC-3.1, AC-3.2, AC-3.3, R-12, R-13, R-14)
  Given 节点 C 在旧父节点 A 下，isPendingState_==true
   And 新父节点 B 的 RebuildRenderContextTree 先于旧父节点 A 执行
  When B 的 ProcessRenderTreeDiff 调用 C->AttachToRenderTree(B_isPendingState_)
  Then C->AttachToRenderTree 因 isPendingState_==true 而 early return
  When A 的 ProcessRenderTreeDiff 调用 C->DetachFromRenderTree(A_isPendingState_)
  Then C->isPendingState_==false
   And C 实际仍在新父节点 B 的渲染树上，但 isPendingState_ 状态错误

  Scenario: active 节点有转出动画时仍被保留 (AC-4.1, AC-4.2, R-15, R-16)
  Given 一个 FrameNode，isActive_==true, IsVisible()==false, HasTransitionOutAnimation()==true
  When OnGenerateOneDepthVisibleFrameWithTransition 被调用
  Then 该节点被加入可见子节点列表

  Scenario: 不可见节点无转出动画被排除 (AC-4.3, R-15)
  Given 一个 FrameNode，isActive_==true, IsVisible()==false, HasTransitionOutAnimation()==false
  When OnGenerateOneDepthVisibleFrameWithTransition 被调用
  Then 该节点不被加入可见子节点列表

  Scenario: disappearingChildren_ 按原始位置合并 (AC-4.4, R-17)
  Given 父节点存在 disappearingChildren_
  When MergeChildrenWithDisappearingChildren 被调用
  Then 消失子节点按原始位置合并回子节点列表

  Scenario: overlay 与 accessibility 节点追加 (AC-4.5, R-18)
  Given overlayNode_ 可见或 accessibilityFocusPaintNode_ 存在
  When GenerateRenderTreeFrameChildren 被调用
  Then 对应节点追加到可见子节点列表之后

  Scenario: layout node 仅递归收集子节点 (AC-4.6, R-19)
  Given 一个 isLayoutNode_==true 的 FrameNode
  When OnGenerateOneDepthVisibleFrameWithTransition 被调用
  Then 递归收集子节点且不将自身加入列表

  Scenario: frameChildren_ 使用 ZIndexComparator 排序 (AC-5.1, R-20)
  Given 多个可见 FrameNode，包含重复 ZIndex
  When frameChildren_ 被重建
  Then 按 ZIndex 升序保存且允许重复值

  Scenario: MIXED MountPolicy 选择 mixed 重建路径 (AC-5.2, R-21)
  Given 一个 FrameNode，MountPolicy==MIXED
  When RebuildFrame 被调用
  Then ReCreateMixedRsNodeTree 被调用

  Scenario: 非 MIXED MountPolicy 选择普通重建路径 (AC-5.3, R-21)
  Given 一个 FrameNode，MountPolicy!=MIXED
  When RebuildFrame 被调用
  Then ReCreateRsNodeTree 被调用

  Scenario: RS 目标列表执行增量 diff (AC-5.4, R-22)
  Given 当前 RS 子节点列表与目标列表存在增删移差异
  When ReCreateRsNodeTreeByTargetList 被调用
  Then 移除多余节点、添加新节点并移动已有节点到目标位置

  Scenario: RS 重建标志关闭时跳过重建 (AC-5.5, R-23)
  Given isNeedRebuildRSTree_==false
  When ReCreateRsNodeTree 或 ReCreateMixedRsNodeTree 被调用
  Then 直接返回且不重建 RS 子节点树

  Scenario: NodeRenderStatusMonitor 到达 root 时返回 IN (AC-6.3, R-26)
  Given 一个 FrameNode，自身可见/active/on-tree
   And 到 root 之前的非根 FrameNode 祖先均可见/active/on-tree
  When GetNodeCurrentRenderState 被调用
  Then 遇到 root FrameNode 时返回 ABOUT_TO_RENDER_IN
   And 不检查 root 自身的 visible/active/on-tree

  Scenario: FrameNode 析构时清理 isPendingState_ (AC-2.8, R-11)
  Given 一个 FrameNode，isPendingState_==true
  When FrameNode 析构
  Then CleanRenderTreeLifeCycle 被调用
   And DetachFromRenderTree(true, true) 被调用
   And isPendingState_==false

  Scenario: isLayoutNode_ 节点 MarkNeedSyncRenderTree 委托父级并置自身 (AC-1.5, R-4)
  Given 一个 isLayoutNode_==true 的 FrameNode 且存在父节点
   And 自身 needSyncRenderTree_==false 且父级 needSyncRenderTree_==false
  When 调用 MarkNeedSyncRenderTree(true)
  Then 父级 needSyncRenderTree_==true
   And 自身 needSyncRenderTree_==true
   And frameProxy_->ResetChildren(true) 被调用

  Scenario: isDeleteRsNode_ 为 true 时上推父级 (AC-1.6, R-5)
  Given 一个 FrameNode，RebuildRenderContextTree 执行中，isDeleteRsNode_==true 且存在父 FrameNode
  When RebuildRenderContextTree 到末尾 isDeleteRsNode_ 分支
  Then 父级 MarkNeedSyncRenderTree 被调用
   And 父级 RebuildRenderContextTree 被调用

  Scenario: NodeRenderStatusMonitor 注册超限拒绝 (AC-6.5, R-28)
  Given NodeRenderStatusMonitor 已占用 64 个 FrameNode 监听条目
  When 公开 API 发起新的 nodeRenderState 注册
  Then 注册入口报告错误码 161001
   And 新监听未加入 nodeRenderStatusListeners_

  Scenario: nodeRenderState 注册成功后立即回调 (AC-6.1, R-24)
  Given 目标 FrameNode 可注册 nodeRenderState 监听
  When UIContext.on 或 UIContext.onNodeRenderState 注册成功
  Then callback 立即收到目标节点的当前 NodeRenderState

  Scenario: FlushTask 后按顺序触发状态变化回调 (AC-6.2, R-25)
  Given 监听节点状态发生变化
  When FlushTask 与资源重载完成后的监控遍历执行
  Then 先触发 ABOUT_TO_RENDER_IN 回调，再触发 ABOUT_TO_RENDER_OUT 回调

  Scenario: off 省略 callback 时注销节点全部监听 (AC-6.1, R-24)
  Given 一个 nodeIdentity 已注册一个或多个 nodeRenderState callback
  When UIContext.off 或 UIContext.offNodeRenderState 省略 callback
  Then 该 nodeIdentity 对应的全部公开监听被注销

  Scenario: FrameNode 释放时触发 NODE_RELEASE (AC-6.4, R-27)
  Given FrameNode 存在 PipelineContext 且有监听条目
  When FrameNode 清理 Pipeline 资源
  Then 触发 ABOUT_TO_RENDER_OUT(NODE_RELEASE) 并移除该节点监听
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（逻辑树同步、生命周期、RS diff、状态监控）
- [x] 无“快速”“稳定”“尽可能”等语义模糊表述
- [x] AC 与规则表交叉一致，每个 AC 至少关联一条规则
- [x] 规则表通过可复现、可观测、边界值、关联 AC、无冲突检查

## context-references

```yaml
context-queries:
  - repo: OpenHarmony/arkui_ace_engine
    query: "核对 FrameNode 的 RebuildRenderContextTree、ProcessRenderTreeDiff、AttachToRenderTree、DetachFromRenderTree、CleanRenderTreeLifeCycle 及可见子节点收集实现。"
  - repo: OpenHarmony/arkui_ace_engine
    query: "核对 RosenRenderContext 的 RebuildFrame、普通/MIXED RS 子树重建和 ReCreateRsNodeTreeByTargetList diff 实现。"
  - repo: OpenHarmony/arkui_ace_engine
    query: "核对 NodeRenderStatusMonitor 的注册上限、resourceId 去重、状态遍历、FlushTask 时序和节点释放回调。"
  - repo: OpenHarmony/arkui_ace_engine
    query: "核对 FrameNode 生命周期字段、ZIndexComparator、Pattern Attach/Detach 回调及 ImagePattern 依赖。"
  - repo: OpenHarmony/sdk-js
    query: "核对 UIContext nodeRenderState dynamic API 20+ 和 static API 26+ 的签名、@since、错误码及 callback 可选语义。"
  - repo: OpenHarmony/arkui_ace_engine
    query: "核对 UITaskScheduler 的 dirtyRenderNodes_ 收集、FlushTask 中 Layout 到 Render 的顺序、CreateRenderTask 的 dirty 标志门控。"
  - repo: OpenHarmony/arkui_ace_engine
    query: "核对 PaintWrapper::FlushRender 的 Modifier 更新、按类型 DrawOnNode 独立录制及 StartRecording/StopRecordingIfNeeded 生命周期。"
  - repo: OpenHarmony/graphic_graphic_2d
    query: "核对 RSCanvasNode 的 BeginRecording、FinishRecording、DrawOnNode 以及无活动录制/空 command list 的收尾语义。"
```

关键源码文件：

- `frameworks/core/components_ng/base/frame_node.cpp`
- `frameworks/core/components_ng/base/frame_node.h`
- `frameworks/core/components_ng/base/ui_node.cpp`
- `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp`
- `frameworks/core/components_ng/render/render_context.h`
- `foundation/graphic/graphic_2d/rosen/modules/render_service_client/core/ui/rs_canvas_node.cpp`
- `frameworks/core/components_ng/base/node_render_status_monitor.cpp`
- `interfaces/napi/kits/observer/ui_observer.cpp`
- `interfaces/napi/kits/observer/js_ui_observer.cpp`
- `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`
- `interface/sdk-js/api/@ohos.arkui.UIContext.static.d.ets`
