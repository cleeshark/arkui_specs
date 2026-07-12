# 特性规格

## 概述

| 字段 | 值 |
|------|-----|
| 特性名称 | Video 控制器与全屏 |
| 特性编号 | Func-05-13-02-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7（同步 Controller）～ API 26（异步 Controller / 状态机） |
| SIG 归属 | ArkUI SIG · Media/Video |
| 状态 | Baselined |
| 复杂度 | 关键 |

Video 组件的播放控制与全屏能力：同步 `VideoController`（`start / pause / stop / setCurrentTime / requestFullscreen / exitFullscreen / reset`）、异步 `VideoControllerAsync`（Promise 版 4 方法 + 3 个 fire-and-forget 方法）、`SeekMode` 枚举、`VideoStateManager` 状态机（`VideoPlaybackState` × `VideoPlaybackCommand`）以及全屏切换机制（`VideoFullScreenPattern` + 独立 FrameNode）。事件与显示属性归 Feat-01；本 Feat 承接 `onFullscreenChange` 与 `requestFullscreen/exitFullscreen` 关联行为。

## 本次变更范围（Delta）

> 存量特性补录，lineage: new-on-legacy。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Feat-02 规格文档 | 建立同步 + 异步 Controller 与全屏机制的规格 |
| MODIFIED | 无 | 未修改任何源码或 SDK 声明 |
| REMOVED | 无 | 未废弃任何 API |

## 输入文档

- SDK 声明：`interface/sdk-js/api/@internal/component/ets/video.d.ts:491-711`（VideoController / VideoControllerAsync）
- SDK 静态版本：`interface/sdk-js/api/arkui/component/video.static.d.ets`
- 源码定位：`frameworks/core/components_ng/pattern/video/video_controller_v2.h`、`video_controller_async.{h,cpp}`、`video_state_manager.{h,cpp}`、`video_state_machine_pattern.{h,cpp}`、`video_full_screen_pattern.{h,cpp}`、`video_full_screen_node.{h,cpp}`
- JS 桥定位：`frameworks/bridge/declarative_frontend/jsview/js_video_controller.{h,cpp}`、`js_video_controller_async.{h,cpp}`
- 设计文档：`specs/05-ui-components/13-platform-components/02-video/design.md`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 通过同步 `VideoController` 播放控制视频

**As a** ArkTS 应用开发者
**I want** 通过 `VideoController.start()/pause()/stop()/setCurrentTime()/reset()` 命令式控制播放
**So that** 我能响应用户手势即时驱动视频

| AC 编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | **WHEN** 声明 `let ctrl = new VideoController(); Video({controller: ctrl})` **THEN** `JSVideo::Create` 内部创建 `RefPtr<VideoControllerV2>`，`VideoPattern` 通过 `videoControllerV2_` 持有；`ctrl` 通过 JS 桥挂到 `VideoControllerV2` 列表 | 正常 |
| AC-1.2 | **WHEN** `ctrl.start()` 被调用 **THEN** JS 桥调用 `VideoControllerV2::Start()`，遍历内部 `VideoController` 列表触发 `startImpl_()`；`VideoPattern::SetStartImpl` 注册的 UI Task 派发到 `VideoPattern::Start()` → `mediaPlayer_->Play()` | 正常 |
| AC-1.3 | **WHEN** `ctrl.pause()` 被调用 **THEN** 走 `pauseImpl_` → `VideoPattern::Pause` → `mediaPlayer_->Pause()`；随后触发 `onPause` | 正常 |
| AC-1.4 | **WHEN** `ctrl.stop()` 被调用 **THEN** 走 `stopImpl_` → `VideoPattern::Stop` → `mediaPlayer_->Stop()`；`isStop_` 置 true；触发 `onStop`（API 12+）；随后 `isInitialState_` 复位为 true | 正常 |
| AC-1.5 | **WHEN** `ctrl.setCurrentTime(30.5)` 被调用 **THEN** 走 `seekToImpl_` → `VideoPattern::SetCurrentTime(30.5, SeekMode::SEEK_PREVIOUS_SYNC)` → `mediaPlayer_->Seek(30500ms, SEEK_PREVIOUS_SYNC)`；触发 `onSeeking(30.5)` → 完成后 `onSeeked(30.5)` | 正常 |
| AC-1.6 | **WHEN** `ctrl.setCurrentTime(30.5, SeekMode.Accurate)` 被调用（API 8+） **THEN** SeekMode 传值 `SeekMode::SEEK_CLOSEST`（内部映射 `Accurate=3`）；`mediaPlayer_->Seek` 按精确模式定位 | 正常 |
| AC-1.7 | **WHEN** `ctrl.reset()` 被调用（API 12+） **THEN** 走 `resetImpl_` → `VideoPattern::ResetMediaPlayer()`；MediaPlayer 回到未 prepare 状态；`isInitialState_ = true`；后续调用 `start` 需重新 prepare | 正常 |
| AC-1.8 | **WHEN** 未挂载 Video 组件即调 `ctrl.start()` **THEN** `startImpl_` 未注册，`if (startImpl_)` 为 false，调用被忽略（`video_controller_v2.h:41-46`） | 边界 |
| AC-1.9 | **WHEN** 一个 `VideoController` 被复用到多个 Video 节点 **THEN** `VideoControllerV2::list<VideoController>` 广播到所有已注册 impl；所有节点同时 Start/Pause | 边界 |

### US-2: 通过异步 `VideoControllerAsync` 获取控制结果

**As a** ArkTS 应用开发者
**I want** 通过 `VideoControllerAsync.start()/pause()/stop()/reset()` 拿到 `Promise<void>`
**So that** 我能在播放动作真正完成后再继续下一步（例如切换到暂停后再截图）

| AC 编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | **WHEN** 声明 `Video({controllerAsync: new VideoControllerAsync()})` **THEN** `VideoModelNG::Create(RefPtr<VideoControllerAsync>)` 创建 `VideoStateMachinePattern`（而不是 `VideoPattern`）；`VideoControllerAsync::pattern_` 通过 `WeakPtr` 指向该 Pattern | 正常 |
| AC-2.2 | **WHEN** `await ctrl.start()` **THEN** `VideoStateManager::HandleStateTransition(PLAY, callback)` 走状态机：如 `CanPlay(state_) == true` → 设置 pending `PLAY`，调 `mediaPlayer_->Play()`，等待 `PlaybackStatus::STARTED` → 触发回调 `callback(true, "")` → Promise resolve | 正常 |
| AC-2.3 | **WHEN** 状态为 `CREATED` 时调 `await ctrl.start()` **THEN** `CanPlay(CREATED) == false`，状态机拒绝，callback 收到 `(false, "invalid state")` → Promise reject（或按实现约定 resolve 但携带失败原因） | 异常 |
| AC-2.4 | **WHEN** 已有 pending `PLAY`，再次调 `await ctrl.start()` **THEN** `CanOverridePendingCommand` 判定同命令不可自覆写（`video_state_manager.h:236-244`），第二次调用被拒 | 异常 |
| AC-2.5 | **WHEN** 已有 pending `PLAY`，调 `await ctrl.stop()` **THEN** STOP 可覆写任意 pending → 原 pending 命令被清除，STOP 成为新的 pending 命令 | 恢复 |
| AC-2.6 | **WHEN** 已有 pending `PAUSE`，调 `await ctrl.start()` **THEN** PLAY 与 PAUSE 可互相覆写；原 PAUSE pending 被替换为 PLAY pending | 恢复 |
| AC-2.7 | **WHEN** `ctrl.setCurrentTime(t, mode?)` 被调用（无 Promise 版本） **THEN** 立即返回 void；`VideoControllerAsync::SeekTo` 内部调用状态机检查 `CanSeek(state_)`，允许时透传给 MediaPlayer | 正常 |
| AC-2.8 | **WHEN** `ctrl.requestFullscreen(true)` / `ctrl.exitFullscreen()` **THEN** 无 Promise 语义，直接触发全屏切换；不进入状态机 | 正常 |
| AC-2.9 | **WHEN** `await ctrl.reset()` **THEN** 状态机接受 RESET 命令；异步等待 MediaPlayer Reset 完成后回调 resolve；状态回到 `CREATED` | 正常 |
| AC-2.10 | **WHEN** Video 组件被销毁 **THEN** `VideoControllerAsync::ClearPattern()` 被调用，`pattern_.Reset()`（`video_controller_async.h:54-57`）；后续 `start/pause/...` 调用不会再触发状态机 | 恢复 |

### US-3: 全屏切换与事件

**As a** ArkTS 应用开发者
**I want** 通过 `requestFullscreen(true) / exitFullscreen()` 切换全屏，并通过 `onFullscreenChange` 感知切换
**So that** 我能在全屏切换时联动 UI（隐藏系统栏、锁定横屏等）

| AC 编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | **WHEN** `ctrl.requestFullscreen(true)` 被调用 **THEN** `VideoPattern::FullScreen()` 创建 `VideoFullScreenNode`（tag `V2::VIDEO_ETS_TAG`，Pattern 为 `VideoFullScreenPattern`）；`fullScreenNodeId_` 记录节点 id；节点挂到 OverlayManager 顶层 | 正常 |
| AC-3.2 | **WHEN** 全屏 Pattern 创建 **THEN** `CreateLayoutProperty()` 克隆源 Pattern 的 `VideoLayoutProperty`，随后调 `fullScreenReset()`（`video_layout_property.h:50`）：Reset 后重放 `VideoSource / ObjectFit / Controls / PosterImageInfo / VideoSize` 5 项，其余 LayoutProperty 项（如 padding/margin）被清零 | 边界 |
| AC-3.3 | **WHEN** 全屏节点挂载完成 **THEN** `VideoEventHub::FireFullScreenChangeEvent(true)` 触发 → `onFullscreenChange` 回调收到 `{"fullscreen": true}` JSON；`Recorder::EventType::VIDEO_SCREEN_CHANGE` 埋点记录（`video_event_hub.h:219`） | 正常 |
| AC-3.4 | **WHEN** `ctrl.exitFullscreen()` 或用户在全屏态按后退键 **THEN** `VideoFullScreenPattern::ExitFullScreen()` 或 `OnBackPressed()`（`video_full_screen_pattern.h:39-43`）被触发；全屏节点从 OverlayManager 移除；`FireFullScreenChangeEvent(false)` 触发 | 正常 |
| AC-3.5 | **WHEN** 全屏切换过程中 **THEN** 原 Pattern 与全屏 Pattern 共享同一 `MediaPlayer`、`RenderSurface`、`RenderContext`（通过 `InitFullScreenParam` 传入，`video_full_screen_pattern.h:33-34`）；播放不中断 | 边界 |
| AC-3.6 | **WHEN** 已在全屏态再次调 `requestFullscreen(true)` **THEN** `IsFullScreen()` 返回 true（`video_full_screen_pattern.h:75-81` 委托源 Pattern 的 `fullScreenNodeId_` 判定），Impl 不再创建重复节点 | 边界 |
| AC-3.7 | **WHEN** 未全屏时调 `exitFullscreen()` **THEN** `fullScreenNodeId_` 为空，`GetFullScreenNode()` 返回 nullptr（`video_pattern.h:211-217`）；调用被安全忽略 | 边界 |
| AC-3.8 | **WHEN** 全屏态下调 `ctrl.stop()` **THEN** MediaPlayer 停止，但全屏节点仍在（stop 不隐含 exit fullscreen）；应用需显式 `exitFullscreen()` | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|----------|------|
| AC-1.1 | R-1 | TASK-VIDEO-BASELINE-02 | 单测 | `video_controller_v2.h:134`；`js_video_controller.cpp` 绑定 |
| AC-1.2 | R-2 | TASK-VIDEO-BASELINE-02 | 集成测试 | `video_controller_v2.h:41-46`；`video_pattern.h:342-343` |
| AC-1.3 | R-2 | TASK-VIDEO-BASELINE-02 | 集成测试 | `video_pattern.h:344-345` |
| AC-1.4 | R-2 | TASK-VIDEO-BASELINE-02 | 集成测试 | `video_pattern.h:346-347`；`isStop_` 更新 |
| AC-1.5 | R-3 | TASK-VIDEO-BASELINE-02 | 集成测试 | `video_pattern.h:348-349`；`SetCurrentTime` 默认 mode |
| AC-1.6 | R-4 | TASK-VIDEO-BASELINE-02 | 单测 | `video_utils.h:21-30`；`video_pattern.h:374` |
| AC-1.7 | R-5 | TASK-VIDEO-BASELINE-02 | 集成测试 | `video_pattern.h:354-355`；`ResetMediaPlayer` |
| AC-1.8 | R-6 | TASK-VIDEO-BASELINE-02 | 单测 | `video_controller_v2.h:41-46` if 判空 |
| AC-1.9 | R-7 | TASK-VIDEO-BASELINE-02 | 集成测试 | `video_controller_v2.h:134` list 多播 |
| AC-2.1 | R-8 | TASK-VIDEO-BASELINE-02 | 单测 | `video_controller_async.h:40`；`video_model_ng.h:27` |
| AC-2.2 | R-9 | TASK-VIDEO-BASELINE-02 | 状态机测试 | `video_state_manager.h:50-73`；`HandleStateTransition` |
| AC-2.3 | R-10 | TASK-VIDEO-BASELINE-02 | 状态机测试 | `CanPlay(CREATED)==false` |
| AC-2.4 | R-11 | TASK-VIDEO-BASELINE-02 | 状态机测试 | `CanOverridePendingCommand` 同命令拒绝 |
| AC-2.5 | R-11 | TASK-VIDEO-BASELINE-02 | 状态机测试 | STOP 可覆写规则 |
| AC-2.6 | R-11 | TASK-VIDEO-BASELINE-02 | 状态机测试 | PLAY/PAUSE 互覆写规则 |
| AC-2.7 | R-12 | TASK-VIDEO-BASELINE-02 | 单测 | `video_controller_async.h:48`（无 callback） |
| AC-2.8 | R-13 | TASK-VIDEO-BASELINE-02 | 集成测试 | `video_controller_async.h:49-50` |
| AC-2.9 | R-14 | TASK-VIDEO-BASELINE-02 | 状态机测试 | RESET 命令；状态回 `CREATED` |
| AC-2.10 | R-15 | TASK-VIDEO-BASELINE-02 | 单测 | `video_controller_async.h:54-57` |
| AC-3.1 | R-16 | TASK-VIDEO-BASELINE-02 | 集成测试 | `video_full_screen_node.h:25-36`；`fullScreenNodeId_` |
| AC-3.2 | R-17 | TASK-VIDEO-BASELINE-02 | 单测 | `video_layout_property.h:50-63`；`video_full_screen_pattern.h:64-73` |
| AC-3.3 | R-18 | TASK-VIDEO-BASELINE-02 | 事件测试 | `video_event_hub.h:205-220` |
| AC-3.4 | R-18 | TASK-VIDEO-BASELINE-02 | 集成测试 | `video_full_screen_pattern.h:37-43`；`ExitFullScreen` |
| AC-3.5 | R-19 | TASK-VIDEO-BASELINE-02 | 集成测试 | `video_full_screen_pattern.h:33-34` `InitFullScreenParam` |
| AC-3.6 | R-20 | TASK-VIDEO-BASELINE-02 | 单测 | `video_full_screen_pattern.h:75-81` `IsFullScreen` |
| AC-3.7 | R-20 | TASK-VIDEO-BASELINE-02 | 单测 | `video_pattern.h:211-217` `GetFullScreenNode` 空指针 |
| AC-3.8 | R-21 | TASK-VIDEO-BASELINE-02 | 集成测试 | stop 与 exit fullscreen 无耦合 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 声明 `new VideoController()` 并传入 `Video({controller})` | JS 桥创建 `VideoController` 实例；`VideoControllerV2` 将其加入 `list<VideoController>` 多播列表；`VideoPattern` 持 `videoControllerV2_` | 一个 controller 可对应多个 Pattern，多播语义 | AC-1.1 |
| R-2 | 行为 | 调 `VideoControllerV2::Start/Pause/Stop` | 广播到列表内所有 `VideoController` 的 impl 回调；每个 impl 派发 UI Task 到对应 `VideoPattern` | 若 impl 未注册（`startImpl_ == nullptr`），if 判空直接返回 | AC-1.2, AC-1.3, AC-1.4 |
| R-3 | 行为 | 调 `setCurrentTime(t)`（单参重载） | 走 `SeekTo(t, SeekMode::SEEK_PREVIOUS_SYNC)`（默认 mode）；先触发 `onSeeking(t)`；Media 完成后触发 `onSeeked(t)` | 时间单位秒；负值/超出 duration 交给 MediaPlayer | AC-1.5 |
| R-4 | 行为 | 调 `setCurrentTime(t, seekMode)`（API 8+） | 按 SeekMode 映射：PreviousKeyframe=0, NextKeyframe=1, ClosestKeyframe=2, Accurate=3；对应 `SEEK_PREVIOUS_SYNC/SEEK_NEXT_SYNC/SEEK_CLOSEST_SYNC/SEEK_CLOSEST` | Accurate 精度最高，耗时最长；老代码未指定 mode 时使用默认值 | AC-1.6 |
| R-5 | 行为 | 调 `reset()`（API 12+） | `VideoPattern::ResetMediaPlayer()` 将 MediaPlayer 重置到 CREATED；`isInitialState_ = true`；后续 `start()` 需重新经过 Prepare | 与 `stop()` 差异：stop 保留 MediaPlayer 已 prepare 状态，reset 完全重建 | AC-1.7 |
| R-6 | 边界 | 组件未挂载或 impl 未注册 | 同步 Controller 的所有方法均 if 判空后 return，不抛异常 | 静默失败；应用层无回调告知 | AC-1.8 |
| R-7 | 边界 | 一个 controller 对应多个 Video | 多播 impl 列表，所有 Pattern 同步收到指令 | 用户需自行处理"多个视频要求不同状态"的场景 | AC-1.9 |
| R-8 | 行为 | 声明 `Video({controllerAsync})` | `VideoModelNG::Create(RefPtr<VideoControllerAsync>)` 创建 `VideoStateMachinePattern`，与同步路径的 `VideoPattern` 互斥 | 一个节点只能选一种 controller 类型 | AC-2.1 |
| R-9 | 行为 | 状态允许（`CanPlay(state)==true`）时 `await ctrl.start()` | `HandleStateTransition(PLAY, cb)` 设置 pending PLAY → `mediaPlayer_->Play()` → 收到 `STARTED` 后回调；Promise resolve | 状态机允许集见 `video_state_manager.h:50-73` | AC-2.2 |
| R-10 | 异常 | 状态不允许（如 `CREATED` 时 PLAY） | `ValidateStateTransition` 返回 false；命令被拒绝，callback 报错 | 应用需在 `onPrepared` 后再触发首次 PLAY | AC-2.3 |
| R-11 | 恢复 | 有 pending 命令时新命令到达 | 按 `CanOverridePendingCommand`（`video_state_manager.h:236-244`）判断：STOP/RESET 可覆写任意；PLAY↔PAUSE 可互相覆写；同命令不能自覆写；其它组合拒绝 | 被覆写的 pending 的 callback 会以 `(false, "overridden")` 语义结束（约定） | AC-2.4, AC-2.5, AC-2.6 |
| R-12 | 行为 | 异步 `setCurrentTime(t, mode?)` | fire-and-forget，无 Promise；内部检查 `CanSeek(state_)`；允许时透传给 MediaPlayer | 与同步版本相同的 seek 语义 | AC-2.7 |
| R-13 | 行为 | 异步 `requestFullscreen(v)` / `exitFullscreen()` | 直接触发全屏切换，不经状态机 | 与同步版本行为一致 | AC-2.8 |
| R-14 | 行为 | `await ctrl.reset()` | 状态机接受 RESET；异步等待 Media Reset；完成后状态回 `CREATED`；callback resolve | RESET 可覆写任意 pending 命令 | AC-2.9 |
| R-15 | 恢复 | Video 节点销毁 | `VideoControllerAsync::ClearPattern()` 被调用，`pattern_.Reset()`；后续方法调用因 `WeakPtr` upgrade 失败而 no-op | 与同步 Controller 的行为一致 | AC-2.10 |
| R-16 | 行为 | 调 `requestFullscreen(true)` 且未在全屏态 | `VideoFullScreenNode::CreateFullScreenNode(V2::VIDEO_ETS_TAG, id, ...)` 创建新节点；Pattern 为 `VideoFullScreenPattern`；`fullScreenNodeId_` 记录 id | 全屏节点挂到 OverlayManager 顶层，避开父容器 clip | AC-3.1 |
| R-17 | 边界 | 全屏 Pattern 创建其 LayoutProperty | Clone 源 LayoutProperty → `fullScreenReset()`：先 Reset 所有 property，再重放 `VideoSource / ObjectFit / Controls / PosterImageInfo / VideoSize` 5 项 | padding/margin/border 等非 Video 专属属性被清零 | AC-3.2 |
| R-18 | 行为 | 进入或退出全屏 | `VideoEventHub::FireFullScreenChangeEvent(isFullScreen)` 触发；`onFullscreenChange` 收到 `{"fullscreen": bool}`；写 `VIDEO_SCREEN_CHANGE` 埋点 | 进入与退出使用同一事件，靠 bool 区分 | AC-3.3, AC-3.4 |
| R-19 | 边界 | 全屏切换过程中 | 原 Pattern 与全屏 Pattern 共享 `MediaPlayer` / `RenderSurface` / `RenderContext`（通过 `InitFullScreenParam` 传入） | MediaPlayer 不重建，播放不中断；只是 Surface 挂载点变化 | AC-3.5 |
| R-20 | 边界 | 重复请求全屏 / 未全屏调 exit | `IsFullScreen()` 通过 `fullScreenNodeId_` 是否有值判定；重复请求不创建新节点；未全屏 exit 静默返回 | 幂等：多次 requestFullscreen(true) 效果等价一次 | AC-3.6, AC-3.7 |
| R-21 | 行为 | 全屏态下 `stop()` | Stop 只影响 MediaPlayer 播放状态，不触发全屏退出；`isStop_ = true` 但 `fullScreenNodeId_` 保留 | 应用需显式 `exitFullscreen()` | AC-3.8 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1, R-2, R-6, R-7 | 单测 `video_controller_sync_test.cpp` | 多播列表与 impl 判空 |
| VM-2 | R-3, R-4 | 单测 | SeekMode 枚举映射与默认值 |
| VM-3 | R-5 | 集成测试 | reset 后 MediaPlayer 状态复位 |
| VM-4 | R-8, R-9, R-14 | 状态机测试 `video_state_manager_test.cpp` | 允许集覆盖 |
| VM-5 | R-10 | 状态机测试 | 拒绝路径的错误信息 |
| VM-6 | R-11 | 状态机测试 | 覆写规则 6 组组合矩阵 |
| VM-7 | R-12, R-13 | 单测 | 异步 seek/fullscreen 的 fire-and-forget 语义 |
| VM-8 | R-15 | 单测 | 节点销毁后 controller 方法 no-op |
| VM-9 | R-16, R-17, R-19, R-20 | 集成测试 `video_full_screen_test.cpp` | 全屏节点生命周期与状态克隆 |
| VM-10 | R-18 | 事件测试 | JSON 字段与埋点 |
| VM-11 | R-21 | 集成测试 | stop 与全屏正交性 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---------|---------|----------|--------|-----------|----------|---------|
| `class VideoController { constructor() }` | Public | 无 | `VideoController` 实例 | 无 | 同步播放控制器 | AC-1.1 |
| `VideoController.start()` | Public | 无 | void | 无 | 开始/恢复播放 | AC-1.2 |
| `VideoController.pause()` | Public | 无 | void | 无 | 暂停 | AC-1.3 |
| `VideoController.stop()` | Public | 无 | void | 无 | 停止（MediaPlayer 保留 prepare） | AC-1.4 |
| `VideoController.setCurrentTime(value: number)` | Public | `value: number` (秒) | void | 无 | 跳转到指定时间（默认 PreviousKeyframe） | AC-1.5 |
| `VideoController.setCurrentTime(value: number, seekMode: SeekMode)` | Public | `value: number`, `seekMode: SeekMode` | void | 无 | 跳转到指定时间 + Seek 模式（API 8+） | AC-1.6 |
| `VideoController.requestFullscreen(value: boolean)` | Public | `value: boolean` | void | 无 | 进入/退出全屏 | AC-3.1 |
| `VideoController.exitFullscreen()` | Public | 无 | void | 无 | 退出全屏 | AC-3.4 |
| `VideoController.reset()` | Public | 无 | void | 无 | 完全重置 MediaPlayer（API 12+） | AC-1.7 |
| `class VideoControllerAsync { constructor() }` | Public | 无 | `VideoControllerAsync` 实例 | 无 | 异步播放控制器（API 26+） | AC-2.1 |
| `VideoControllerAsync.start()` | Public | 无 | `Promise<void>` | 状态非法时 reject | 异步播放（API 26+） | AC-2.2, AC-2.3 |
| `VideoControllerAsync.pause()` | Public | 无 | `Promise<void>` | 同上 | 异步暂停（API 26+） | AC-2.6 |
| `VideoControllerAsync.stop()` | Public | 无 | `Promise<void>` | 同上 | 异步停止（API 26+） | AC-2.5 |
| `VideoControllerAsync.setCurrentTime(value: double, seekMode?: SeekMode)` | Public | 同同步版 | void | 无 | fire-and-forget seek（API 26+） | AC-2.7 |
| `VideoControllerAsync.requestFullscreen(value: boolean)` | Public | 同同步版 | void | 无 | fire-and-forget 全屏（API 26+） | AC-2.8 |
| `VideoControllerAsync.exitFullscreen()` | Public | 无 | void | 无 | fire-and-forget 退出全屏（API 26+） | AC-2.8 |
| `VideoControllerAsync.reset()` | Public | 无 | `Promise<void>` | 无 | 异步 reset（API 26+） | AC-2.9 |
| `enum SeekMode` | Public | 4 个枚举值 | N/A | N/A | Seek 精度控制（API 8+） | AC-1.6 |
| `onFullscreenChange(callback: Callback<FullscreenInfo>)` | Public | `Callback<FullscreenInfo>` | `VideoAttribute` | N/A | 全屏切换事件 | AC-3.3, AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---------|---------|---------|----------|---------|
| （无） | | | | |

## 接口规格

### 接口定义

**VideoController.start()（同步）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `VideoController::start(): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.2, AC-1.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| （无） | | | | |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 组件已挂载，`startImpl_` 已注册 | 派发 UI Task → `VideoPattern::Start()` → MediaPlayer.Play() → 触发 onStart | AC-1.2 |
| 2 | 组件未挂载 | `if (startImpl_)` 为 false，静默返回 | AC-1.8 |

**VideoController.setCurrentTime(value, seekMode?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `VideoController::setCurrentTime(value: number, seekMode?: SeekMode): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.5, AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `value` | number（秒） | 是 | 无 | ≥ 0；越界由 MediaPlayer clamp |
| `seekMode` | `SeekMode` | 否 | `SeekMode.PreviousKeyframe` | 4 个枚举值合法 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `setCurrentTime(30.5)` | 走默认 PreviousKeyframe seek | AC-1.5 |
| 2 | `setCurrentTime(30.5, SeekMode.Accurate)` | 精确 seek | AC-1.6 |
| 3 | `setCurrentTime(-1)` | 交给 MediaPlayer 处理（通常 clamp 到 0） | 边界（不属于 AC） |

**VideoControllerAsync.start()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `VideoControllerAsync::start(): Promise<void>` |
| 返回值 | `Promise<void>` — resolve 表示 MediaPlayer 已进入 PLAYING；reject 表示状态机拒绝或 MediaPlayer 报错 |
| 开放范围 | Public |
| 错误码 | `BusinessError`（状态非法或覆写失败） |
| 关联 AC | AC-2.2, AC-2.3, AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| （无） | | | | |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 状态 `PREPARED`/`PAUSED`/`COMPLETED`/`STOPPED` | pending PLAY → MediaPlayer.Play() → STARTED 回调 → Promise resolve | AC-2.2 |
| 2 | 状态 `CREATED` | `CanPlay(CREATED)==false`，Promise reject | AC-2.3 |
| 3 | 已有 pending PLAY | `CanOverridePendingCommand` 拒绝，Promise reject | AC-2.4 |
| 4 | 已有 pending PAUSE，调 start | PLAY 覆写 PAUSE，原 PAUSE Promise 结束（约定），新 PLAY Promise 继续 | AC-2.6 |

**VideoControllerAsync 覆写矩阵（新命令 vs 现有 pending）**

| 现有 pending → \ 新命令 ↓ | PLAY | PAUSE | STOP | RESET |
|---|:-:|:-:|:-:|:-:|
| （无） | ✓ 允许 | ✓ | ✓ | ✓ |
| PLAY | ✗ 同命令 | ✓ 互覆写 | ✓ 覆写 | ✓ 覆写 |
| PAUSE | ✓ 互覆写 | ✗ 同命令 | ✓ 覆写 | ✓ 覆写 |
| STOP | ✗ | ✗ | ✗ 同命令 | ✓ 覆写 |
| RESET | ✗ | ✗ | ✗ | ✗ 同命令 |

**VideoController.requestFullscreen(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `VideoController::requestFullscreen(value: boolean): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-3.1, AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `value` | boolean | 是 | 无 | `true` 请求全屏，`false` 请求退出全屏 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 未全屏 + value=true | 创建全屏节点，挂 OverlayManager，fire `onFullscreenChange(true)` | AC-3.1, AC-3.3 |
| 2 | 已全屏 + value=true | `IsFullScreen()==true`，无操作 | AC-3.6 |
| 3 | 已全屏 + value=false | 退出全屏（等价 `exitFullscreen()`）；fire `onFullscreenChange(false)` | AC-3.4 |
| 4 | 未全屏 + value=false | 无操作 | AC-3.7 |

**C-API 补充**

Video 组件当前无 C-API 控制器（`interfaces/native/native_node.h` 中无 `ArkUI_Video*` 相关符号）；异步语义也未通过 NDK 暴露。若跨语言场景需要控制播放，需通过 XComponent 自行接入 MediaPlayer。

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** `VideoController` 全套同步方法起自 API 7；`SeekMode` 及带 seekMode 的 `setCurrentTime` 重载起自 API 8；`reset()` 起自 API 12；`VideoControllerAsync` 及全套异步方法起自 API 26。
- **API 版本号策略:** 同步 `VideoController` 与异步 `VideoControllerAsync` 长期共存，不废弃同步 API；应用可按需选择。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|---------|
| 同步/异步 Controller 与 Pattern 类型 1:1 绑定 | 同步 controller → `VideoPattern`；异步 controller → `VideoStateMachinePattern`；`VideoModelNG` 通过 `DynamicCast<VideoStateMachinePattern>` 判定分派 | AC-1.1, AC-2.1 |
| 同步 impl 判空静默失败 | `VideoController::Start` 等方法内部 `if (startImpl_)` 判空后 return，不抛异常也不回调 | AC-1.8 |
| 异步指令必经状态机 | `VideoControllerAsync::Start/Pause/Stop/Reset` 均经 `VideoStateManager::HandleStateTransition`；`SeekTo/RequestFullscreen/ExitFullscreen` 不经状态机 | AC-2.2, AC-2.7, AC-2.8 |
| 全屏节点独立 FrameNode | 全屏使用 `VideoFullScreenNode` + `VideoFullScreenPattern`，挂 OverlayManager；共享 MediaPlayer/RenderSurface/RenderContext | AC-3.1, AC-3.5 |
| 全屏 LayoutProperty 仅保留 5 项 | `fullScreenReset()` Reset 后仅重放 VideoSource / ObjectFit / Controls / PosterImageInfo / VideoSize | AC-3.2 |
| 覆写规则限定 pending 命令集合 | `CanOverridePendingCommand` 由代码实现枚举；应用无法自定义 | AC-2.4 ~ AC-2.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Controller 方法调用 ≤ 1ms 派发到 UI Task | 单测计时 | `SetStartImpl` 等 impl 只做派发 |
| 功耗 | Stop/Reset 后 MediaPlayer 停止解码，不产生功耗 | 集成测试 | `mediaPlayer_->Stop()`/`Reset()` |
| 内存 | 全屏节点使用完毕后释放 | 集成测试 + LeakSanitizer | `ExitFullScreen` 触发节点 detach |
| 安全 | 全屏节点独占触摸事件，不透传到底层 | 集成测试 | OverlayManager 顶层 |
| 可靠性 | 异步命令覆写不导致状态机漂移 | 状态机 fuzz | `CanOverridePendingCommand` 覆盖 |
| 可测试性 | 状态机可离线测试（无 MediaPlayer 依赖） | 单测 | `VideoStateMachine::CanX` 为静态方法 |
| 自动化维测 | Controller 方法调用写 `TAG_LOGD(ACE_VIDEO, ...)` | hilog 抽样 | `video_pattern.cpp`/`video_controller_async.cpp` 内 |
| 定界定位 | `DumpInfo` 输出当前 state / pending / originalIntent | dump 测试 | `VideoStateManager::GetStateInfo` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|-----------|----------|------|
| 手机 | 全屏切横屏（由应用/系统决定） | Video 不主动请求方向切换，交给业务 | 集成测试 | `RequestFullscreen` 不含方向控制 |
| 平板 | 全屏保持当前方向 | 与手机一致，Video 层无差异 | 集成测试 | 同上 |
| 折叠屏 | 全屏节点跨屏时会触发一次 `OnAreaChangedInner` | 视频画面按新尺寸重排 | 集成测试 | `video_pattern.h:162` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | `VideoFullScreenPattern` 继承 `FocusView`（`video_full_screen_pattern.h:26`），全屏态下焦点被限定在全屏节点内 | AC-3.1 |
| 大字体 | 否 | 控制器本身无文本 | N/A |
| 深色模式 | 是 | 全屏节点内的控制条随 `OnColorConfigurationUpdate` 刷新 | AC-3.1 |
| 多窗口/分屏 | 是 | 全屏节点挂 OverlayManager，随窗口区域移动；不主动铺满物理屏 | AC-3.1 |
| 多用户 | 否 | 与用户身份无关 | N/A |
| 版本升级 | 是 | API 8 追加 SeekMode；API 12 追加 reset/onStop；API 26 追加异步 Controller；老 API 保持不变 | AC-1.4, AC-1.6, AC-1.7, AC-2.* |
| 生态兼容 | 是 | Static (`.d.ets`) 版本与 Dynamic (`.d.ts`) 版本同步 + 异步 Controller 均对齐 | AC-1.*, AC-2.* |

## 行为场景（可选，Gherkin）

```
Feature: 异步 Controller 与状态机
  作为 ArkTS 应用开发者
  我想要 通过 Promise 感知 start/pause/stop/reset 的完成
  以便 精确编排媒体行为

  Scenario Outline: 状态机允许集
    Given 当前状态为 <state>
    When 调用 await ctrl.<command>()
    Then Promise 状态为 <promise>

    Examples:
      | state    | command | promise |
      | PREPARED | start   | resolve |
      | PAUSED   | start   | resolve |
      | CREATED  | start   | reject  |
      | PLAYING  | pause   | resolve |
      | PLAYING  | play    | reject (同命令) |
      | ERROR    | reset   | resolve → CREATED |

  Scenario: 覆写规则
    Given 已有 pending PLAY 未完成
    When 立即调用 await ctrl.stop()
    Then STOP 覆写 PLAY
    And 原 start 的 Promise 以 overridden 结束（约定）
    And stop 的 Promise 正常等待完成

  Scenario: 全屏切换事件
    Given 视频正在播放
    When 调用 ctrl.requestFullscreen(true)
    Then 触发 onFullscreenChange({fullscreen: true})
    And 记录 VIDEO_SCREEN_CHANGE 埋点
    And MediaPlayer 不重建

    When 调用 ctrl.exitFullscreen()
    Then 触发 onFullscreenChange({fullscreen: false})
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（同步/异步 Controller + 全屏 vs 显示/播放/事件 vs 高级能力）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "VideoStateManager 覆写规则 CanOverridePendingCommand 完整矩阵"
  - repo: "openharmony/arkui_ace_engine"
    query: "VideoFullScreenPattern.InitFullScreenParam 与 fullScreenReset 的字段列表"
  - repo: "openharmony/interface_sdk-js"
    query: "VideoControllerAsync 全部 8 个方法的 Promise 语义"
```

**关键文档：**
- 设计文档：`specs/05-ui-components/13-platform-components/02-video/design.md`（ADR-3 全屏节点替换、ADR-4 双 Controller 共存、ADR-6 onError 双签名——本 Feat 涉及后两项）
- 上游声明：`interface/sdk-js/api/@internal/component/ets/video.d.ts:491-711`
