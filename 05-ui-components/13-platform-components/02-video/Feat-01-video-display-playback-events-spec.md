# 特性规格

## 概述

| 字段 | 值 |
|------|-----|
| 特性名称 | Video 显示、播放与事件 |
| 特性编号 | Func-05-13-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7（基线）～ API 22（PlaybackSpeed 新枚举） |
| SIG 归属 | ArkUI SIG · Media/Video |
| 状态 | Baselined |
| 复杂度 | 关键 |

Video 组件的显示与播放基础能力：构造参数（`src`、`previewUri`、`controller`、`currentProgressRate`）、9 个显示/播放属性（`muted`、`autoPlay`、`controls`、`loop`、`objectFit`、`surfaceBackgroundColor`）与 10 个事件回调（`onStart`、`onPause`、`onFinish`、`onFullscreenChange`、`onPrepared`、`onSeeking`、`onSeeked`、`onUpdate`、`onError`、`onStop`）。本 Feat 覆盖同步 `VideoController` 路径下的默认行为；异步 Controller 与全屏行为在 Feat-02 承接，高级能力（AI/Poster/快捷键）在 Feat-03 承接。

## 本次变更范围（Delta）

> 存量特性补录，lineage: new-on-legacy。仅对源代码事实做规格化写入，不引入任何行为变更。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Feat-01 规格文档 | 首次为 Video 组件建立显示/播放/事件规格 |
| MODIFIED | 无 | 未修改任何源码或 SDK 声明 |
| REMOVED | 无 | 未废弃任何 API |

## 输入文档

- SDK 声明：`interface/sdk-js/api/@internal/component/ets/video.d.ts`
- SDK 静态版本：`interface/sdk-js/api/arkui/component/video.static.d.ets`
- SDK Modifier：`interface/sdk-js/api/arkui/VideoModifier.d.ts`
- 源码定位：`frameworks/core/components_ng/pattern/video/`（`video_pattern.h`、`video_layout_property.h`、`video_event_hub.h`、`video_model_ng.{h,cpp}`）
- JS 桥定位：`frameworks/bridge/declarative_frontend/jsview/js_video.{h,cpp}`
- 设计文档：`specs/05-ui-components/13-platform-components/02-video/design.md`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 通过属性配置播放源与显示效果

**As a** ArkTS 应用开发者
**I want** 通过 `Video({src, previewUri, controller})` 配置视频源 + 预览图 + 控制器，并链式设置 `objectFit / muted / autoPlay / loop / controls`
**So that** 我能声明式地把一段视频嵌入到 UI 中，无需手写 MediaPlayer

| AC 编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | **WHEN** 声明 `Video({src: 'http://a.mp4'})` **THEN** Video FrameNode 加载完成后，`VideoLayoutProperty::VideoStyle::VideoSource` 中 `src_` 等于 `'http://a.mp4'`，`bundleName_`、`moduleName_` 均为空串 | 正常 |
| AC-1.2 | **WHEN** 声明 `Video({src: $r('app.media.demo')})` **THEN** `VideoSourceInfo` 会包含 Resource 解析后的 bundleName 与 moduleName（非空） | 正常 |
| AC-1.3 | **WHEN** 只声明 `Video({})`（src 为 undefined） **THEN** `videoSrcInfo_.src_` 保持空串，`PrepareMediaPlayer` 早退不初始化 MediaPlayer | 边界 |
| AC-1.4 | **WHEN** 链式调用 `.objectFit(ImageFit.Fill)` **THEN** `VideoLayoutProperty::VideoStyle::ObjectFit` 被写为 `ImageFit::FILL`，下一帧 Measure 触发（`PROPERTY_UPDATE_MEASURE`） | 正常 |
| AC-1.5 | **WHEN** 未显式设置 `objectFit` **THEN** 默认取值为 `ImageFit::COVER`（`video_layout_property.h:53` 与 `fullScreenReset()` 一致） | 边界 |
| AC-1.6 | **WHEN** 链式调用 `.muted(true)` **THEN** `VideoPattern::muted_` 更新为 `true`，`UpdateMuted()` 将音量传给 `mediaPlayer_->SetVolume(0.0f)` 效果 | 正常 |
| AC-1.7 | **WHEN** 链式调用 `.loop(true)` **THEN** `VideoPattern::loop_` 为 `true`；播放到末尾时 `OnCompletion` 判断 `loop_` 后自动 `Start()` 重播（`video_pattern.cpp:927` `mediaPlayer->SetLooping(loop)` 生效） | 正常 |
| AC-1.8 | **WHEN** 链式调用 `.controls(true)` **THEN** Video FrameNode 下挂载 `controlBar_` 子节点（`VideoPattern::CreateControlBar` 生成的 SVG 按钮 + Slider + 时间文本 + 全屏按钮） | 正常 |
| AC-1.9 | **WHEN** `.controls(false)` **THEN** 已有 `controlBar_` 从 FrameNode 中移除；控制条不再显示 | 正常 |

### US-2: 通过 `currentProgressRate` 与 `previewUri` 控制播放体验

**As a** ArkTS 应用开发者
**I want** 通过 `currentProgressRate` 设置倍速播放，通过 `previewUri` 指定播放前的预览图，通过 `surfaceBackgroundColor` 控制视频画面之外的背景色（System API）
**So that** 我能在视频未就绪或未播放时给用户合适的视觉反馈

| AC 编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | **WHEN** 声明 `Video({currentProgressRate: PlaybackSpeed.Speed_Forward_1_25_X})` **THEN** `VideoPattern::progressRate_` 归一化为 `1.25`；`UpdateSpeed()` 通过 Background TaskExecutor 调 `mediaPlayer_->SetPlaybackRate(1.25, ...)` | 正常 |
| AC-2.2 | **WHEN** 设置 `currentProgressRate = 10.0`（越界 > SPEED_8_00_X） **THEN** `VIDEO_EXCEED_PROGRESS_RATE` 统计事件被记录（`video_pattern.cpp:958`）；仍尝试传给 MediaPlayer，最终由 `SetPlaybackRate` 返回值决定是否生效 | 异常 |
| AC-2.3 | **WHEN** 设置 `currentProgressRate = 0.05`（越界 < SPEED_0_125_X） **THEN** 同 AC-2.2，越界事件记录并透传 | 异常 |
| AC-2.4 | **WHEN** 连续两次设置相同 `currentProgressRate`（`NearEqual(lastSetSpeed, progress)`） **THEN** 第二次不再调 MediaPlayer（`video_pattern.cpp:981-983`），避免重复 IPC | 边界 |
| AC-2.5 | **WHEN** 声明 `Video({previewUri: 'poster.png'})` **THEN** `VideoLayoutProperty::VideoStyle::PosterImageInfo` 写入对应 `ImageSourceInfo`，`PROPERTY_UPDATE_LAYOUT` 触发；MediaPlayer 未 `OnPrepared` 前渲染 Poster 图 | 正常 |
| AC-2.6 | **WHEN** 应用未设置 `previewUri` 且视频未就绪 **THEN** 画面区域填充为 `surfaceBgColor_`（默认 `Color::BLACK`，`video_pattern.h:494`） | 边界 |
| AC-2.7 | **WHEN** System API `surfaceBackgroundColor(Color.WHITE)` 被调用 **THEN** `VideoPattern::surfaceBgColor_` 更新为白色，SurfaceNode 背景色随之刷新 | 正常 |

### US-3: 通过事件回调感知播放生命周期

**As a** ArkTS 应用开发者
**I want** 注册 10 个播放/错误/全屏事件回调（`onStart / onPause / onFinish / onPrepared / onSeeking / onSeeked / onUpdate / onStop / onError / onFullscreenChange`）
**So that** 我能对播放状态变化做出反应（更新 UI、埋点、错误处理）

| AC 编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | **WHEN** 播放开始（`OnPlayerStatus(STARTED)`） **THEN** `VideoEventHub::FireStartEvent()` 触发，`onStart` 回调收到 JSON `{"start":""}`；`Recorder::EventType::VIDEO_START` 埋点记录（`video_event_hub.h:52`） | 正常 |
| AC-3.2 | **WHEN** MediaPlayer 完成 prepare（`OnPrepared(duration, currentPos, needFireEvent=true)`） **THEN** `FirePreparedEvent(duration)` 触发，`onPrepared` 收到 `{"duration":<秒>}` JSON | 正常 |
| AC-3.3 | **WHEN** 播放中每次 `OnCurrentTimeChange(pos)` **THEN** `FireUpdateEvent(pos)` 触发，`onUpdate` 收到 `{"time":<秒>}` JSON（未额外记录埋点） | 正常 |
| AC-3.4 | **WHEN** 用户调 `controller.setCurrentTime(t)` **THEN** 先触发 `FireSeekingEvent(t)`（`{"time":t}`）；MediaPlayer 完成 seek 后触发 `FireSeekedEvent(t)`（`{"time":t}` + `VIDEO_SEEKED` 埋点） | 正常 |
| AC-3.5 | **WHEN** MediaPlayer 播放到末尾（`OnCompletion`） **THEN** `FireFinishEvent()` 触发，`onFinish` 收到 `{"finish":""}` JSON；如果 `loop_ = true`，同一帧内会再次 `Start()` | 正常 |
| AC-3.6 | **WHEN** `VideoPattern::OnError(errorId: string)` 触发（老式空参分支） **THEN** `FireErrorEvent()` 生成 `{"error":""}`；`onError` 回调按 API 7 的 `VoidCallback` 语义收到无字段的 JSON | 边界 |
| AC-3.7 | **WHEN** `VideoPattern::OnError(int32_t code, const std::string& message)` 触发（API 20 新分支） **THEN** `FireErrorEvent(code, message)` 生成 `{"code":<code>, "name":"BusinessError", "message":<msg>}`；`onError` 回调按 `ErrorCallback` 语义解包 | 正常 |
| AC-3.8 | **WHEN** `VideoController::Stop()` 触发（API 12） **THEN** MediaPlayer 停止后 `FireStopEvent()` 生成 `{"stop":""}`；`onStop` 回调收到；`VIDEO_STOP` 埋点记录 | 正常 |
| AC-3.9 | **WHEN** `autoPlay` 为 true 且 `showFirstFrame_` 为 false **THEN** `OnPrepared` 中 `checkNeedAutoPlay()` 判定 `autoPlay_ && !isPlaying_` 为 true → 自动调用 `Start()`，随后触发 `onStart` | 正常 |
| AC-3.10 | **WHEN** 回调中对 `onXxx` 重新赋值 **THEN** 由于 hub 在 Fire 内先拷贝再调用（`video_event_hub.h:49-50`），当前回调不会被打断 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|----------|------|
| AC-1.1 | R-1 | TASK-VIDEO-BASELINE-01 | 单测 + 源码引用 | `video_styles.h:25-38`；`video_model_ng.cpp:197-204` |
| AC-1.2 | R-1 | TASK-VIDEO-BASELINE-01 | 单测 + 源码引用 | `video_model_ng.cpp:197-204`；bundle/module 参数注入 |
| AC-1.3 | R-2 | TASK-VIDEO-BASELINE-01 | 单测 | `video_pattern.cpp:PrepareMediaPlayer` 中 `videoSrcInfo_.src_.empty()` 早退 |
| AC-1.4 | R-3 | TASK-VIDEO-BASELINE-01 | 单测 | `video_model_ng.cpp:307-309` |
| AC-1.5 | R-3 | TASK-VIDEO-BASELINE-01 | 源码引用 | `video_layout_property.h:53` |
| AC-1.6 | R-4 | TASK-VIDEO-BASELINE-01 | 单测 | `video_model_ng.cpp:271-284`；`UpdateMuted()` 转发音量 |
| AC-1.7 | R-5 | TASK-VIDEO-BASELINE-01 | 单测 | `video_model_ng.cpp:312-325`；`video_pattern.cpp:927` |
| AC-1.8 | R-6 | TASK-VIDEO-BASELINE-01 | 集成测试 | `video_pattern.h:133`；`video_model_ng.cpp:301-305` |
| AC-1.9 | R-6 | TASK-VIDEO-BASELINE-01 | 集成测试 | `UpdateControllerBar(frameNode, false)` 逻辑分支 |
| AC-2.1 | R-7 | TASK-VIDEO-BASELINE-01 | 单测 | `video_pattern.cpp:945-987`；`video_model_ng.cpp:221` |
| AC-2.2 | R-8 | TASK-VIDEO-BASELINE-01 | 单测 | `video_pattern.cpp:958-960` |
| AC-2.3 | R-8 | TASK-VIDEO-BASELINE-01 | 单测 | `video_pattern.cpp:958-960` |
| AC-2.4 | R-9 | TASK-VIDEO-BASELINE-01 | 单测 | `video_pattern.cpp:981-983` |
| AC-2.5 | R-10 | TASK-VIDEO-BASELINE-01 | 集成测试 | `video_layout_property.h:68`；`video_model_ng.cpp:236-252` |
| AC-2.6 | R-11 | TASK-VIDEO-BASELINE-01 | 源码引用 | `video_pattern.h:494` |
| AC-2.7 | R-11 | TASK-VIDEO-BASELINE-01 | 单测 | `video_model_ng.cpp:327-340` |
| AC-3.1 | R-12 | TASK-VIDEO-BASELINE-01 | 事件测试 | `video_event_hub.h:42-53` |
| AC-3.2 | R-12 | TASK-VIDEO-BASELINE-01 | 事件测试 | `video_event_hub.h:126-137` |
| AC-3.3 | R-12 | TASK-VIDEO-BASELINE-01 | 事件测试 | `video_event_hub.h:176-186` |
| AC-3.4 | R-13 | TASK-VIDEO-BASELINE-01 | 事件测试 | `video_event_hub.h:143-170` |
| AC-3.5 | R-14 | TASK-VIDEO-BASELINE-01 | 集成测试 | `video_event_hub.h:76-87`；`video_pattern.cpp` OnCompletion |
| AC-3.6 | R-15 | TASK-VIDEO-BASELINE-01 | 事件测试 | `video_event_hub.h:93-104` |
| AC-3.7 | R-15 | TASK-VIDEO-BASELINE-01 | 事件测试 | `video_event_hub.h:105-120` |
| AC-3.8 | R-16 | TASK-VIDEO-BASELINE-01 | 事件测试 | `video_event_hub.h:192-203` |
| AC-3.9 | R-17 | TASK-VIDEO-BASELINE-01 | 集成测试 | `video_pattern.h:79-87`；`checkNeedAutoPlay` |
| AC-3.10 | R-18 | TASK-VIDEO-BASELINE-01 | 单测 | `video_event_hub.h:49-50` 注释与拷贝逻辑 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 声明 `Video({src})`，src 为 string 或 Resource | `VideoModelNG::SetSrc(src, bundleName, moduleName)` 将三段写入 `VideoStyle::VideoSource`；`PROPERTY_UPDATE_MEASURE` 触发 | string 分支 bundleName/moduleName 为空串；Resource 分支填入解析值 | AC-1.1, AC-1.2 |
| R-2 | 边界 | `VideoOptions.src` 为 undefined 或空串 | `videoSrcInfo_.src_` 保持空串；`OnModifyDone` → `PrepareMediaPlayer` 早退，不初始化 MediaPlayer | 空串与 undefined 效果等价 | AC-1.3 |
| R-3 | 行为 | 链式 `.objectFit(fit)` 调用 | `ACE_UPDATE_LAYOUT_PROPERTY(VideoLayoutProperty, ObjectFit, fit)`，`PROPERTY_UPDATE_MEASURE` 标记 | 未设置时默认 `ImageFit::COVER` | AC-1.4, AC-1.5 |
| R-4 | 行为 | 链式 `.muted(true/false)` | `VideoPattern::muted_` 更新；`UpdateMuted()` 转发到 MediaPlayer volume | 静音等价 volume=0；恢复时 volume=`currentVolume_` | AC-1.6 |
| R-5 | 行为 | 链式 `.loop(true/false)` | Pattern `loop_` 更新；`UpdateLooping` → `mediaPlayer->SetLooping(loop)` 同步生效 | 与 `OnCompletion` 组合决定是否自动重播 | AC-1.7 |
| R-6 | 行为 | 链式 `.controls(true/false)` | 通过 `UpdateControllerBar(frameNode, controls)` 挂载或移除内置 `controlBar_` 子节点 | `controls: false` 只隐藏控制条，不影响其它属性 | AC-1.8, AC-1.9 |
| R-7 | 行为 | 设置 `currentProgressRate = rate`（number/string/PlaybackSpeed） | Pattern `progressRate_` 归一化为 `double`；`UpdateSpeed()` 通过 BG TaskExecutor 调 `mediaPlayer_->SetPlaybackRate` | 提交到 `TaskType::BACKGROUND`；结果回到 UI 线程 | AC-2.1 |
| R-8 | 异常 | `progressRate ∉ [0.125, 8.00]` | `SendStatisticEvent(VIDEO_EXCEED_PROGRESS_RATE)` 记录（`video_pattern.cpp:958-960`）；仍调 MediaPlayer，返回值决定成败 | 上界 8.00，下界 0.125，均取自 `SPEED_0_125_X` 与 `SPEED_8_00_X` 常量 | AC-2.2, AC-2.3 |
| R-9 | 边界 | `NearEqual(lastSetSpeed, progress)` 为真 | 跳过 `mediaPlayer_->SetPlaybackRate` 二次调用；仍在 `HandleSetPlaybackRateResult` 中记录一次 | 判等使用 `NearEqual`，浮点容差由 base 层实现 | AC-2.4 |
| R-10 | 行为 | 设置 `previewUri = value`（string/PixelMap/Resource） | `VideoStyle::PosterImageInfo` 写入 `ImageSourceInfo`；`PROPERTY_UPDATE_LAYOUT` 触发；MediaPlayer 未 prepare 时展示 poster | Poster 属于 `PROPERTY_UPDATE_LAYOUT`（比 objectFit 弱）；显示优先于 `surfaceBgColor_` | AC-2.5 |
| R-11 | 行为 | System API `surfaceBackgroundColor(color)` | `VideoPattern::surfaceBgColor_` 更新；SurfaceNode 背景色刷新；缺省背景色为 `Color::BLACK` | 未设置 `previewUri` 且未 prepare 时可见 | AC-2.6, AC-2.7 |
| R-12 | 行为 | MediaPlayer 触发 `OnPlayerStatus(STARTED)` / `OnPrepared` / `OnCurrentTimeChange` | 依次 `FireStartEvent()` / `FirePreparedEvent(duration)` / `FireUpdateEvent(pos)`；start/prepared 事件写 `EventRecorder` 埋点 | JSON 字段固定为 `start` / `duration` / `time` | AC-3.1, AC-3.2, AC-3.3 |
| R-13 | 行为 | `VideoController::SeekTo(t, mode)` 或异步 `SeekTo` | 先 `FireSeekingEvent(t)`；MediaPlayer 完成后 `FireSeekedEvent(t)`（Seeked 写 `VIDEO_SEEKED` 埋点） | JSON 字段 `time`（秒） | AC-3.4 |
| R-14 | 行为 | `OnCompletion` 播放结束 | `FireFinishEvent()` 生成 `{"finish":""}`；若 `loop_==true`，同帧内再 `Start()` | 与 R-5 组合 | AC-3.5 |
| R-15 | 异常 | MediaPlayer 错误或 src 无效 | `FireErrorEvent()`（空参）→ `{"error":""}`；或 `FireErrorEvent(code, msg)` → `{"code","name":"BusinessError","message"}` | API 20 新增 `ErrorCallback` 分支；两种分支互不干扰 | AC-3.6, AC-3.7 |
| R-16 | 行为 | `VideoController::Stop()` 触发（API 12） | `FireStopEvent()` 生成 `{"stop":""}`；写 `VIDEO_STOP` 埋点 | 与 `onFinish` 互斥：Stop 由用户触发，Finish 由播放到末尾触发 | AC-3.8 |
| R-17 | 行为 | `OnPrepared` 完成，`autoPlay_ && !isPlaying_` 为真 | `checkNeedAutoPlay()` 判定 → 自动 `Start()` → 触发 `onStart` | `showFirstFrame_ == true` 时逻辑不受此规则约束（Feat-03 详解） | AC-3.9 |
| R-18 | 恢复 | 事件回调内 setter 重赋值 `onXxx` | Fire 时先拷贝原回调再调（`auto onStart = onStart_;`），当前回调不被打断 | 拷贝语义仅适用于回调本身，不适用于 param JSON | AC-3.10 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1, R-2 | 单测 `video_property_test.cpp` | `VideoSourceInfo` 字段与更新标记 |
| VM-2 | R-3 | 单测 | `objectFit` 默认值与更新标记 |
| VM-3 | R-4, R-5, R-6 | 单测 + 集成 | `muted/loop/controls` 三态切换后的 Pattern 状态 |
| VM-4 | R-7, R-8, R-9 | 单测 `video_speed_test.cpp` | 越界统计事件与去重逻辑 |
| VM-5 | R-10, R-11 | 集成测试 | Poster 显示优先级、背景色透传到 SurfaceNode |
| VM-6 | R-12, R-13, R-14, R-15, R-16 | 事件回调测试 | JSON 字段格式、埋点触发条件 |
| VM-7 | R-17 | 集成测试 | `autoPlay + OnPrepared` 时序 |
| VM-8 | R-18 | 单测 | 回调重入不打断当前调用 |

## API 变更分析

> Video 组件已交付多年，本节按"补录"视角列出 Feat-01 覆盖的 API。

### 新增 API

（补录，非真实新增；均以 `.d.ts` 声明为契约。）

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---------|---------|----------|--------|-----------|----------|---------|
| `Video(value: VideoOptions)` | Public | `VideoOptions` 见构造字段 | Video 组件实例 | N/A | 构造 Video 组件 | AC-1.1, AC-1.2, AC-1.3 |
| `muted(value: boolean)` | Public | `value: boolean` | `VideoAttribute` | N/A | 是否静音播放 | AC-1.6 |
| `autoPlay(value: boolean)` | Public | `value: boolean` | `VideoAttribute` | N/A | 是否自动播放（结合 `OnPrepared`） | AC-3.9 |
| `controls(value: boolean)` | Public | `value: boolean` | `VideoAttribute` | N/A | 是否显示内置控制条 | AC-1.8, AC-1.9 |
| `loop(value: boolean)` | Public | `value: boolean` | `VideoAttribute` | N/A | 播放到末尾是否自动重播 | AC-1.7, AC-3.5 |
| `objectFit(value: ImageFit)` | Public | `ImageFit` 枚举 | `VideoAttribute` | N/A | 视频画面在组件区域内的填充方式，默认 `Cover` | AC-1.4, AC-1.5 |
| `surfaceBackgroundColor(color: ColorMetrics)` | System | `ColorMetrics` | `VideoAttribute` | N/A | Surface 背景色（视频画面之外区域） | AC-2.7 |
| `onStart(event)` / `onPause(event)` / `onFinish(event)` / `onStop(event)` | Public | `VoidCallback` / `Callback<void>` | `VideoAttribute` | N/A | 播放生命周期事件 | AC-3.1, AC-3.5, AC-3.8 |
| `onPrepared(callback)` | Public | `Callback<PreparedInfo>` | `VideoAttribute` | N/A | Media 准备完成（含 duration） | AC-3.2 |
| `onSeeking(callback)` / `onSeeked(callback)` / `onUpdate(callback)` | Public | `Callback<PlaybackInfo>` | `VideoAttribute` | N/A | 时间进度类事件（含 time 秒） | AC-3.3, AC-3.4 |
| `onError(event)` | Public | `VoidCallback \| ErrorCallback` | `VideoAttribute` | `BusinessError`（API 20 分支携带 code/message） | 播放错误事件 | AC-3.6, AC-3.7 |
| `PlaybackSpeed` 枚举 | Public | 10 个枚举值（API 8 与 API 22 两批） | N/A | N/A | 倍速常量集合 | AC-2.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---------|---------|---------|----------|---------|
| `onError` | 变更（联合类型扩展） | API 20 新增 `ErrorCallback` 分支，回调可能收到含 `code/name/message` 的 JSON | 老 API 7 用户无需迁移；API 20+ 用户改用 `ErrorCallback` 签名解包 | AC-3.6, AC-3.7 |

## 接口规格

> 供 code-gen 直接消费的接口行为定义。与 API 变更分析（声明层）互补，本节定义接口的调用语义、参数约束和行为场景。

### 接口定义

**Video 构造函数**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Video(value: VideoOptions): VideoAttribute` |
| 返回值 | `VideoAttribute` — 供链式调用 |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1, AC-1.2, AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `value.src` | `string \| Resource` | 否 | undefined | undefined/空串 → 不初始化 MediaPlayer |
| `value.previewUri` | `string \| PixelMap \| Resource` | 否 | undefined | 未 prepare 时优先展示 |
| `value.controller` | `VideoController` | 否 | undefined | 与 `controllerAsync` 二选一 |
| `value.currentProgressRate` | `number \| string \| PlaybackSpeed` | 否 | `Speed_Forward_1_00_X` (1.0) | 有效区间 `[0.125, 8.0]`，越界发统计事件 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | src 为字符串 URL | 装填 `videoSrcInfo_.src_ = url`；`bundleName_/moduleName_` 为空 | AC-1.1 |
| 2 | src 为 `$r('app.media.demo')` | 装填 src + 解析后的 bundleName/moduleName | AC-1.2 |
| 3 | src 缺省 | 早退不启动 MediaPlayer；`onPrepared` 不触发 | AC-1.3 |
| 4 | `currentProgressRate = 1.25` | Background 提交 `SetPlaybackRate(1.25)` | AC-2.1 |
| 5 | `currentProgressRate = 10.0` | 记录越界事件，仍尝试设置 | AC-2.2 |

**objectFit**

| 属性 | 值 |
|------|-----|
| 函数签名 | `objectFit(value: ImageFit): VideoAttribute` |
| 返回值 | `VideoAttribute` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.4, AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `value` | `ImageFit` | 是 | `ImageFit.Cover` | 8 个 ImageFit 枚举值均合法 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.objectFit(ImageFit.Fill)` | `VideoStyle::ObjectFit = FILL`；`PROPERTY_UPDATE_MEASURE` 触发 | AC-1.4 |
| 2 | 未调用 `.objectFit(...)` | `GetObjectFitValue(ImageFit::COVER)` 返回 COVER | AC-1.5 |

**controls**

| 属性 | 值 |
|------|-----|
| 函数签名 | `controls(value: boolean): VideoAttribute` |
| 返回值 | `VideoAttribute` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.8, AC-1.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `value` | `boolean` | 是 | `true`（`video_layout_property.h:55` `fullScreenReset()` 默认 true） | true 挂载控制条，false 移除 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.controls(true)` | 挂载 `controlBar_` 子节点 | AC-1.8 |
| 2 | `.controls(false)` | 移除已挂载的控制条 | AC-1.9 |

**onError（双签名）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onError(event: VoidCallback \| ErrorCallback): VideoAttribute` |
| 返回值 | `VideoAttribute` |
| 开放范围 | Public |
| 错误码 | `BusinessError`（`ErrorCallback` 分支） |
| 关联 AC | AC-3.6, AC-3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `event` | `VoidCallback \| ErrorCallback` | 是 | 无 | VoidCallback: `()=>void`；ErrorCallback: `(err: BusinessError)=>void` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `VoidCallback` + `FireErrorEvent()` | 回调不带参数（JSON 为 `{"error":""}`） | AC-3.6 |
| 2 | `ErrorCallback` + `FireErrorEvent(code, msg)` | 前端桥解包成 `{code, name:"BusinessError", message}` | AC-3.7 |
| 3 | `ErrorCallback` + `FireErrorEvent()`（老路径遇到新签名） | code 为 0，message 为空 | 边界（不属于既定行为，业务自防） |

**C-API 补充**

Video 组件当前无 C-API 表面（`interfaces/native/native_node.h` 中无 `ARKUI_NODE_VIDEO`，无 `NODE_VIDEO_*` 枚举）。若跨语言场景需要消费 Video，需借助 XComponent + 自定义纹理路径，本 Feat 不覆盖。

## 兼容性声明

- **已有 API 行为变更:** 否。本 Feat 不改变任何 API 语义。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7（`Video` 基础表面及 10 事件回调）；`onStop` 起自 API 12；`onError(ErrorCallback)` 分支起自 API 20；`PlaybackSpeed` 追加 5 项起自 API 22。
- **API 版本号策略:** 保留每个 API 的原始 `@since` 标注；补录场景不因文档整理调整 `@since`。

## 架构约束

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|---------|
| 显示属性走 LayoutProperty | `objectFit / VideoSource / PosterImageInfo / Controls / VideoSize` 五项存放在 `VideoLayoutProperty::VideoStyle`，其余状态字段存放在 Pattern 成员 | AC-1.4, AC-1.5, AC-1.8, AC-2.5 |
| 事件 hub 只发 JSON 串 | `VideoEventCallback` 定义为 `std::function<void(const std::string&)>`，事件参数结构体在前端桥解包 | AC-3.1 ~ AC-3.8 |
| 越界倍速不阻断 | `progressRate` 越界仅记录统计事件（`VIDEO_EXCEED_PROGRESS_RATE`），不拒绝设置，最终以 MediaPlayer 返回值为准 | AC-2.2, AC-2.3 |
| `SetPlaybackRate` 在 Background TaskExecutor 提交 | `video_pattern.cpp:948-987` 提交到 `TaskType::BACKGROUND`，UI 线程只接收结果回调 | AC-2.1, AC-2.4 |
| `showFirstFrame_` 影响 autoPlay 判定 | `checkNeedAutoPlay` 组合 `autoPlay_ && !isPlaying_`；Feat-03 的 `showFirstFrame_ = true` 会改变初始渲染路径 | AC-3.9 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 属性 setter 单次调用 ≤ 1ms（不含 MediaPlayer 异步耗时） | 单测计时 | `video_model_ng.cpp` 各 setter 单一分派 |
| 功耗 | 静音状态不应发送音频到系统 mixer | 集成测试 | `UpdateMuted()` → volume=0 路径 |
| 内存 | 同一节点 setter 反复调用不新增分配 | Address/Leak sanitizer | Property 组用 CoW，Pattern 成员为值类型 |
| 安全 | src URL 校验交由 MediaPlayer 内部处理，ArkUI 不做白名单 | 代码评审 | `SetSourceForMediaPlayer` 只透传字符串 |
| 可靠性 | 事件回调重入不打断当前 Fire | 单测 | `video_event_hub.h:49-50` 拷贝再调 |
| 可测试性 | 每个 setter 均可通过 `FrameNode*` 静态入口调用 | 单测 | `video_model_ng.h:56-72` 双入口 |
| 自动化维测 | `TAG_LOGD(AceLogTag::ACE_VIDEO, ...)` 覆盖所有关键路径 | hilog 抽样 | grep `ACE_VIDEO` |
| 定界定位 | `DumpInfo` / `DumpSimplifyInfo` 输出全部关键属性 | dump 测试 | `video_pattern.h:442-446` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|-----------|----------|------|
| 手机 | 默认场景 | 全套属性/事件按上述规则 | 单测 + 集成 | 主实现 |
| 平板 | 无差异（同手机） | 控制条随尺寸自适应，不改变行为 | 集成测试 | `VideoLayoutAlgorithm` 无设备分支 |
| 折叠屏 | 无差异 | 折叠切换触发 `OnAreaChangedInner` → 布局重刷 | 集成测试 | `video_pattern.h:162` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | `VideoAccessibilityProperty` 承接；控制条按钮的 accessibilityText 由主题提供 | AC-1.8 |
| 大字体 | 是 | 控制条时间文本随系统字体缩放；视频画面不受影响 | AC-1.8 |
| 深色模式 | 是 | `OnColorConfigurationUpdate` 触发控制条 SVG 与文本颜色重取；视频画面不变 | AC-1.8, AC-2.7 |
| 多窗口/分屏 | 是 | 无独有逻辑；随 FrameNode 常规逻辑重排 | 全部 AC |
| 多用户 | 否 | 与用户身份无关 | N/A |
| 版本升级 | 是 | `PlaybackSpeed` 枚举 API 22 扩容；`onError` API 20 扩展；不影响旧 API | AC-2.1, AC-3.7 |
| 生态兼容 | 是 | Static (`.d.ets`) 版本与 Dynamic (`.d.ts`) 版本 API 一一对应，`PlaybackSpeed` 静态版是字符串枚举 | AC-2.1 |

## 行为场景（可选，Gherkin）

```
Feature: Video 显示与事件基线
  作为 ArkTS 应用开发者
  我想要 用 Video 组件声明式播放一段视频并感知生命周期
  以便 无需手写 MediaPlayer

  Scenario: 基础播放 + 自动开始
    Given src 指向一个合法的 mp4 URL
    And autoPlay 为 true
    When Video 组件挂载
    And MediaPlayer 完成 OnPrepared
    Then 触发 onPrepared 事件，参数含 duration
    And 自动调用 Start
    And 触发 onStart 事件

  Scenario Outline: 倍速播放越界处理
    Given 已存在合法 src
    When 应用设置 currentProgressRate = <rate>
    Then 是否记录 VIDEO_EXCEED_PROGRESS_RATE 统计事件为 <exceed>
    And 是否调用 mediaPlayer_->SetPlaybackRate 为 <call>

    Examples:
      | rate  | exceed | call |
      | 1.25  | 否     | 是   |
      | 0.05  | 是     | 是   |
      | 10.0  | 是     | 是   |
      | 1.25  | 否     | 否 (与上次相同) |

  Scenario: 错误事件双签名兼容
    Given onError 注册为 ErrorCallback
    When MediaPlayer 抛出 code=1001, message="src not found"
    Then onError 回调收到 { code: 1001, name: "BusinessError", message: "src not found" }
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（显示/播放/事件 vs 控制器/全屏/高级能力）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Video 组件属性存储位置：VideoLayoutProperty::VideoStyle 与 VideoPattern 成员的划分"
  - repo: "openharmony/arkui_ace_engine"
    query: "Video 事件 hub 的 JSON 序列化格式与 EventRecorder 埋点集"
  - repo: "openharmony/interface_sdk-js"
    query: "video.d.ts 的 @since 标注策略，尤其是 PlaybackSpeed 与 onError 的分批扩展"
```

**关键文档：**
- 设计文档：`specs/05-ui-components/13-platform-components/02-video/design.md`（Feat-01 属于基线 Feat，ADR-1/2/5/6 直接支撑本 Feat 的属性、事件与倍速行为）
- 上游声明：`interface/sdk-js/api/@internal/component/ets/video.d.ts`
