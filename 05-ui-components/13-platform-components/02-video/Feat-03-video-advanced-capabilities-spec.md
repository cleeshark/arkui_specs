# 特性规格

## 概述

| 字段 | 值 |
|------|-----|
| 特性名称 | Video 高级能力（AI 分析 / Poster / 快捷键） |
| 特性编号 | Func-05-13-02-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 12（enableAnalyzer/analyzerConfig/imageAIOptions）～ API 21（PosterOptions.contentTransitionEffect） |
| SIG 归属 | ArkUI SIG · Media/Video |
| 状态 | Baselined |
| 复杂度 | 标准 |

Video 组件的三类增量能力：（1）AI 图像分析（`enableAnalyzer`、`analyzerConfig`、`VideoOptions.imageAIOptions`），叠加基于 `ImageAnalyzerManager` 的悬浮层；（2）Poster 高级配置（`PosterOptions.showFirstFrame`、`PosterOptions.contentTransitionEffect`），控制预览图到视频画面的过渡；（3）键盘快捷键（`enableShortcutKey`），空格键切播、方向键 seek / 调音量。

## 本次变更范围（Delta）

> 存量特性补录，lineage: new-on-legacy。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Feat-03 规格文档 | 建立 AI/Poster/快捷键三类能力的规格 |
| MODIFIED | 无 | 未修改任何源码或 SDK 声明 |
| REMOVED | 无 | 未废弃任何 API |

## 输入文档

- SDK 声明：`interface/sdk-js/api/@internal/component/ets/video.d.ts:966-1048`（enableAnalyzer / analyzerConfig / enableShortcutKey）、`video.d.ts:411 / 428`（VideoOptions.imageAIOptions / posterOptions）、`video.d.ts:308-329`（PosterOptions）
- 源码定位：`frameworks/core/components_ng/pattern/video/video_pattern.{h,cpp}`（`EnableAnalyzer` / `CreateAnalyzerOverlay` / `OnKeyEvent` / `MoveByStep` / `AdjustVolume` / `SetContentTransition` 等）
- ImageAnalyzer：`frameworks/core/components_ng/pattern/image/image_analyzer_manager.{h,cpp}`
- 设计文档：`specs/05-ui-components/13-platform-components/02-video/design.md`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 通过 `enableAnalyzer` 让视频画面识别文字/物体

**As a** ArkTS 应用开发者
**I want** 打开 `enableAnalyzer(true)` 并通过 `analyzerConfig` 配置识别类型，或在 `VideoOptions.imageAIOptions` 中预置 AI 参数
**So that** 用户可以在视频中长按识别文字、物体（复用 ImageAnalyzer 能力）

| AC 编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | **WHEN** 链式调用 `.enableAnalyzer(true)` **THEN** `VideoPattern::isEnableAnalyzer_ = true`；调用 `EnableAnalyzer(true)`（`video_pattern.cpp:2366`），创建 `ImageAnalyzerManager(host, ImageAnalyzerHolder::VIDEO_CUSTOM)` 实例存到 `imageAnalyzerManager_` | 正常 |
| AC-1.2 | **WHEN** `enableAnalyzer(false)` **THEN** `isEnableAnalyzer_ = false`；后续画面渲染不再调用 `CreateAnalyzerOverlay`；已挂载 overlay 由 `DestroyAnalyzerOverlay` 移除 | 正常 |
| AC-1.3 | **WHEN** `enableAnalyzer(true)` + `IsSupportImageAnalyzer()` 判定支持（`video_pattern.cpp:2428`：需 `isEnableAnalyzer_ && !needControlBar && imageAnalyzerManager_->IsSupportImageAnalyzerFeature()`） **THEN** 首帧渲染后延迟 `ANALYZER_DELAY_TIME` 触发 `CreateAnalyzerOverlay`（`video_pattern.cpp:2469-2470`） | 正常 |
| AC-1.4 | **WHEN** `enableAnalyzer(true)` 但 `controls: true`（控制条挂载） **THEN** `IsSupportImageAnalyzer()` 返回 false（因 `needControlBar == true`）；overlay 不创建 | 边界 |
| AC-1.5 | **WHEN** 链式调用 `.analyzerConfig(cfg)` **THEN** `VideoModelNG::SetImageAnalyzerConfig(void* cfg)` 转发到 Pattern；`imageAnalyzerManager_->SetImageAnalyzerConfig(cfg)` | 正常 |
| AC-1.6 | **WHEN** 声明 `Video({imageAIOptions})` **THEN** `VideoModelNG::SetImageAIOptions(void* options)` 转发到 Pattern（`video_model.h:59`）；构造阶段即写入 Analyzer 配置 | 正常 |
| AC-1.7 | **WHEN** seek 或播放结束触发 `UpdateOverlayVisibility` **THEN** overlay 隐藏或显示由 `VisibleType` 参数决定；避免 seek 过程中 overlay 位置错位 | 边界 |
| AC-1.8 | **WHEN** 视频画面尺寸变化（`isContentSizeChanged_ = true`） **THEN** 触发 `UpdateAnalyzerOverlay`（`video_pattern.cpp:2473 内部路径`）与 `UpdateAnalyzerUIConfig`（同步几何信息） | 边界 |

### US-2: 通过 `PosterOptions` 精细控制预览图行为

**As a** ArkTS 应用开发者
**I want** 使用 `PosterOptions.showFirstFrame` 让预览图停留到首帧渲染，用 `PosterOptions.contentTransitionEffect` 定义预览图到视频画面的过渡
**So that** 视频开始播放的视觉体验更平滑

| AC 编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | **WHEN** `Video({posterOptions: {showFirstFrame: true}})` **THEN** `VideoPattern::showFirstFrame_ = true`；`SetRenderFirstFrame(true)` 传给 MediaPlayer（`video_pattern.cpp:488, 518`），保证首帧渲染前预览图不消失 | 正常 |
| AC-2.2 | **WHEN** `showFirstFrame_ == true` 且 `autoPlay_ == true` **THEN** `checkNeedAutoPlay` 仍会触发 auto Start（Feat-01 R-17），但视觉上"预览图 → 首帧"由 `SetRenderFirstFrame` 保证一次切换 | 边界 |
| AC-2.3 | **WHEN** 未设置 `posterOptions` 或 `showFirstFrame` 缺省 **THEN** `showFirstFrame_ = false`，`SetRenderFirstFrame(false)`；MediaPlayer 就绪后立即切换到解码画面 | 边界 |
| AC-2.4 | **WHEN** `Video({posterOptions: {contentTransitionEffect}})`（API 21+） **THEN** `SetContentTransition(contentTransition)`（`video_pattern.cpp:2790`）设置 `contentTransition_`；`UpdatePreviewImage` 中 `imageRenderProperty->UpdateContentTransition(contentTransition_)`（`video_pattern.cpp:1445`）；效果为 `IDENTITY` 时不启动动画 | 正常 |
| AC-2.5 | **WHEN** `contentTransitionEffect` 非 `IDENTITY` **THEN** `video_pattern.cpp:1446` 进入过渡分支，Poster ImageNode 应用 `ContentTransitionType` 语义（如淡入/移动） | 正常 |
| AC-2.6 | **WHEN** 应用未设置 `posterOptions` 而设置了老 `previewUri` **THEN** `showFirstFrame_ = false`；`contentTransition_ = ContentTransitionType::IDENTITY`；仍走 Feat-01 R-10 的 poster 展示路径 | 兼容 |
| AC-2.7 | **WHEN** Poster 图像加载失败 **THEN** SurfaceNode 背景色（默认 `Color::BLACK`）暴露，直到 MediaPlayer 完成 prepare | 异常 |

### US-3: 通过 `enableShortcutKey` 支持键盘快捷键播放控制

**As a** ArkTS 应用开发者
**I want** 打开 `enableShortcutKey(true)`，用户按空格键切换播放/暂停，方向键 seek/调音量
**So that** 键盘用户与外接设备用户能便捷操作视频

| AC 编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | **WHEN** 链式调用 `.enableShortcutKey(true)`（API 15+） **THEN** `VideoPattern::isEnableShortcutKey_ = true`（`video_pattern.cpp:2383`）；`InitKeyEvent()`（`video_pattern.cpp:1306`）将 `OnKeyEvent` 注册到 focusHub | 正常 |
| AC-3.2 | **WHEN** `isEnableShortcutKey_ == true` 且用户按下空格键 **THEN** `OnKeyEvent`（`video_pattern.cpp:1320`）识别 `KEY_SPACE` → 调 `OnKeySpaceEvent()`（`video_pattern.cpp:1352`）：若 `isPlaying_` 为 true → `Pause()`；否则 `Start()` | 正常 |
| AC-3.3 | **WHEN** 按下 `KEY_DPAD_LEFT` **THEN** `MoveByStep(-1)`（`video_pattern.cpp:1361-1367`）：`targetTime = currentPos_ - 1s`；若 `0 <= targetTime <= duration_` → `SetCurrentTime(targetTime, SeekMode::SEEK_CLOSEST)` | 正常 |
| AC-3.4 | **WHEN** 按下 `KEY_DPAD_RIGHT` **THEN** `MoveByStep(+1)`：`targetTime = currentPos_ + 1s`；越界（`< 0` 或 `> duration_`）时静默返回 | 边界 |
| AC-3.5 | **WHEN** 按下 `KEY_DPAD_UP` **THEN** `AdjustVolume(+1)`（`video_pattern.cpp:1369-1384`）：`targetVolume = currentVolume_ + VOLUME_STEP(0.05)`；若 ∈ (0, 1] 内则更新音量，写回 `currentVolume_` | 正常 |
| AC-3.6 | **WHEN** 按下 `KEY_DPAD_DOWN` **THEN** `AdjustVolume(-1)`；`targetVolume` 若 `≥ 1.0` 或 `< 0.0` 则拒绝，否则更新 | 正常 |
| AC-3.7 | **WHEN** 目标音量 `NearZero(targetVolume)` **THEN** `mediaPlayer_->SetMediaMuted(MEDIA_TYPE_AUD, true)`（`video_pattern.cpp:1377-1378`）；否则 `SetMediaMuted(..., false)` | 边界 |
| AC-3.8 | **WHEN** `isEnableShortcutKey_ == false` **THEN** `OnKeyEvent` 早退（`video_pattern.cpp:1322` if 判空），任何按键不影响播放 | 边界 |
| AC-3.9 | **WHEN** Video 组件失去焦点 **THEN** focusHub 不再分发按键事件，快捷键自动失效 | 边界 |
| AC-3.10 | **WHEN** `enableShortcutKey(true)` 但 `controls: false` **THEN** 快捷键仍可用（不依赖控制条子节点，只依赖 focusHub） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|----------|------|
| AC-1.1 | R-1 | TASK-VIDEO-BASELINE-03 | 单测 | `video_pattern.cpp:2366-2378` |
| AC-1.2 | R-1 | TASK-VIDEO-BASELINE-03 | 集成测试 | `video_pattern.cpp:2369`（disable 分支） |
| AC-1.3 | R-2 | TASK-VIDEO-BASELINE-03 | 集成测试 | `video_pattern.cpp:2428`；`2469-2470` |
| AC-1.4 | R-2 | TASK-VIDEO-BASELINE-03 | 单测 | `IsSupportImageAnalyzer` 返回 false 条件 |
| AC-1.5 | R-3 | TASK-VIDEO-BASELINE-03 | 单测 | `video_pattern.h:238`；`video_model_ng.cpp:542-554` |
| AC-1.6 | R-3 | TASK-VIDEO-BASELINE-03 | 单测 | `video_pattern.h:240`；`video_model.h:59` |
| AC-1.7 | R-4 | TASK-VIDEO-BASELINE-03 | 集成测试 | `video_pattern.h:425`；`UpdateOverlayVisibility` |
| AC-1.8 | R-4 | TASK-VIDEO-BASELINE-03 | 集成测试 | `video_pattern.h:423-424`；`isContentSizeChanged_` |
| AC-2.1 | R-5 | TASK-VIDEO-BASELINE-03 | 集成测试 | `video_pattern.cpp:488, 518`；`video_pattern.h:112` |
| AC-2.2 | R-5 | TASK-VIDEO-BASELINE-03 | 集成测试 | 与 Feat-01 R-17 组合 |
| AC-2.3 | R-6 | TASK-VIDEO-BASELINE-03 | 单测 | `showFirstFrame_ = false` 默认路径 |
| AC-2.4 | R-7 | TASK-VIDEO-BASELINE-03 | 集成测试 | `video_pattern.cpp:2790-2792`；`1445-1446` |
| AC-2.5 | R-7 | TASK-VIDEO-BASELINE-03 | 集成测试 | `contentTransition_ != IDENTITY` 分支 |
| AC-2.6 | R-8 | TASK-VIDEO-BASELINE-03 | 兼容测试 | 未设置 posterOptions 时的默认值 |
| AC-2.7 | R-9 | TASK-VIDEO-BASELINE-03 | 异常测试 | Poster 加载失败 → 背景色暴露 |
| AC-3.1 | R-10 | TASK-VIDEO-BASELINE-03 | 单测 | `video_pattern.cpp:2381-2384`；`InitKeyEvent` |
| AC-3.2 | R-11 | TASK-VIDEO-BASELINE-03 | 集成测试 | `video_pattern.cpp:1332-1333, 1352-1359` |
| AC-3.3 | R-12 | TASK-VIDEO-BASELINE-03 | 集成测试 | `video_pattern.cpp:1324-1326, 1361-1367` |
| AC-3.4 | R-12 | TASK-VIDEO-BASELINE-03 | 集成测试 | `MoveByStep` 边界 if |
| AC-3.5 | R-13 | TASK-VIDEO-BASELINE-03 | 集成测试 | `video_pattern.cpp:1328-1330, 1369-1384`；`VOLUME_STEP=0.05` |
| AC-3.6 | R-13 | TASK-VIDEO-BASELINE-03 | 集成测试 | `AdjustVolume(-1)` 分支 |
| AC-3.7 | R-14 | TASK-VIDEO-BASELINE-03 | 集成测试 | `video_pattern.cpp:1377-1381`；`SetMediaMuted` |
| AC-3.8 | R-15 | TASK-VIDEO-BASELINE-03 | 单测 | `video_pattern.cpp:1322` if 判空 |
| AC-3.9 | R-15 | TASK-VIDEO-BASELINE-03 | 集成测试 | focusHub 分发依赖焦点态 |
| AC-3.10 | R-16 | TASK-VIDEO-BASELINE-03 | 集成测试 | 快捷键不依赖控制条 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `.enableAnalyzer(true/false)` | 更新 `isEnableAnalyzer_`；true 时创建 `ImageAnalyzerManager(host, ImageAnalyzerHolder::VIDEO_CUSTOM)`；false 时销毁 overlay | 双入口：实例 setter + 静态 `FrameNode*` setter | AC-1.1, AC-1.2 |
| R-2 | 边界 | 是否创建 AnalyzerOverlay | `IsSupportImageAnalyzer()` 判定：`isEnableAnalyzer_ && !needControlBar && imageAnalyzerManager_->IsSupportImageAnalyzerFeature()` 全部为 true | `controls: true` 会禁用 Analyzer（互斥） | AC-1.3, AC-1.4 |
| R-3 | 行为 | `.analyzerConfig(cfg)` / `VideoOptions.imageAIOptions` | 转发到 `imageAnalyzerManager_` 的对应 setter；配置在 overlay 创建时生效 | 配置类型为不透明 `void*`，由 ImageAnalyzer 内部解析 | AC-1.5, AC-1.6 |
| R-4 | 边界 | Seek 或尺寸变化 | 通过 `UpdateOverlayVisibility(VisibleType)` 与 `UpdateAnalyzerOverlay` 保持 overlay 与画面同步 | seek 时短暂隐藏防错位；尺寸变化重新计算几何 | AC-1.7, AC-1.8 |
| R-5 | 行为 | `PosterOptions.showFirstFrame = true` | Pattern `showFirstFrame_ = true`；`mediaPlayer_->SetRenderFirstFrame(true)` | 影响 `checkNeedAutoPlay` 之外的 preview 显示时机 | AC-2.1, AC-2.2 |
| R-6 | 边界 | `showFirstFrame` 缺省或 false | `showFirstFrame_ = false`；MediaPlayer prepare 后立即切换到解码画面 | 兼容 API 18 之前的默认行为 | AC-2.3 |
| R-7 | 行为 | `PosterOptions.contentTransitionEffect` 非 IDENTITY | `SetContentTransition(effect)` 写 `contentTransition_`；`UpdatePreviewImage` 中传给 ImageRenderProperty；`contentTransition_ != IDENTITY` 触发过渡分支 | 默认 `ContentTransitionType::IDENTITY`，无过渡 | AC-2.4, AC-2.5 |
| R-8 | 兼容 | 老 API 只有 `previewUri`，未设 `posterOptions` | `showFirstFrame_` 与 `contentTransition_` 保留默认值；Poster 走 Feat-01 R-10 路径 | 与老代码 100% 行为一致 | AC-2.6 |
| R-9 | 异常 | Poster 图像加载失败 | 背景色 `surfaceBgColor_` 暴露；MediaPlayer 就绪后覆盖 | 不阻塞视频播放 | AC-2.7 |
| R-10 | 行为 | `.enableShortcutKey(true/false)`（API 15+） | 写 `isEnableShortcutKey_`；`InitKeyEvent` 只挂一次监听，enable 状态在 `OnKeyEvent` 内判断 | 状态机路径同样支持（`VideoStateMachinePattern::SetShortcutKeyEnabled`） | AC-3.1 |
| R-11 | 行为 | 空格键按下 + `isEnableShortcutKey_` | `OnKeySpaceEvent`：`isPlaying_ ? Pause() : Start()` | 通过 `KeyAction::DOWN` 触发；释放不响应 | AC-3.2 |
| R-12 | 行为 | 方向键左/右 + `isEnableShortcutKey_` | `MoveByStep(±1)`：目标时间 `currentPos_ ± 1s`；若 `[0, duration_]` 内则 seek `SeekMode::SEEK_CLOSEST` | 步长固定 1 秒；越界静默 | AC-3.3, AC-3.4 |
| R-13 | 行为 | 方向键上/下 + `isEnableShortcutKey_` | `AdjustVolume(±1)`：目标音量 `currentVolume_ ± 0.05`；若 ∈ [0, 1] 内则更新 | `VOLUME_STEP = 0.05`；越界静默 | AC-3.5, AC-3.6 |
| R-14 | 边界 | 目标音量趋近 0（`NearZero`） | `mediaPlayer_->SetMediaMuted(MEDIA_TYPE_AUD, true)`；否则解静音；同时调 `SetVolume(targetVolume, targetVolume)` | 与 Feat-01 R-4 的 `muted()` 属性不冲突（`muted()` 单独控制静音开关） | AC-3.7 |
| R-15 | 边界 | 快捷键关闭或未获焦点 | `OnKeyEvent` if 判空早退；focusHub 不分发 | 与 R-11/R-12/R-13 前置条件互斥 | AC-3.8, AC-3.9 |
| R-16 | 边界 | 控制条是否显示 | 快捷键与控制条正交：无控制条也能用快捷键 | 与 R-2（Analyzer 与控制条互斥）形成对照 | AC-3.10 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1, R-3 | 单测 `video_analyzer_test.cpp` | Analyzer 开关与配置转发 |
| VM-2 | R-2 | 集成测试 | `controls + enableAnalyzer` 互斥 |
| VM-3 | R-4 | 集成测试 | Seek/Resize 期间 overlay 位置正确 |
| VM-4 | R-5, R-6 | 集成测试 | `showFirstFrame` 时序 |
| VM-5 | R-7, R-8, R-9 | 集成测试 | `contentTransitionEffect` 过渡与降级路径 |
| VM-6 | R-10 ~ R-16 | 集成测试 `video_shortcut_test.cpp` | 按键分发与音量/seek 边界 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---------|---------|----------|--------|-----------|----------|---------|
| `enableAnalyzer(enable: boolean)` | Public | `enable: boolean` | `VideoAttribute` | 无 | 打开/关闭 AI 图像分析（API 12+） | AC-1.1, AC-1.2 |
| `analyzerConfig(config: ImageAnalyzerConfig)` | Public | `config: ImageAnalyzerConfig` | `VideoAttribute` | 无 | 配置 Analyzer 识别类型（API 12+） | AC-1.5 |
| `VideoOptions.imageAIOptions?: ImageAIOptions` | Public | `ImageAIOptions` | N/A | 无 | 构造阶段传入 AI 参数（API 12+） | AC-1.6 |
| `PosterOptions.showFirstFrame?: boolean` | Public | boolean | N/A | 无 | 是否保留预览图直到首帧渲染（API 18+） | AC-2.1, AC-2.3 |
| `PosterOptions.contentTransitionEffect?: ContentTransitionEffect` | Public | ContentTransitionEffect | N/A | 无 | 预览图到视频画面的过渡效果（API 21+） | AC-2.4, AC-2.5 |
| `enableShortcutKey(enabled: boolean)` | Public | boolean | `VideoAttribute` | 无 | 打开/关闭键盘快捷键（API 15+） | AC-3.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---------|---------|---------|----------|---------|
| （无） | | | | |

## 接口规格

### 接口定义

**enableAnalyzer**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableAnalyzer(enable: boolean): VideoAttribute` |
| 返回值 | `VideoAttribute` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1, AC-1.2, AC-1.3, AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `enable` | boolean | 是 | false | true 打开，false 关闭；与 `controls` 互斥 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `enableAnalyzer(true)` + `controls(false)` | 首帧后创建 Analyzer overlay | AC-1.3 |
| 2 | `enableAnalyzer(true)` + `controls(true)` | overlay 不创建（互斥） | AC-1.4 |
| 3 | `enableAnalyzer(false)` | 已挂载 overlay 销毁 | AC-1.2 |

**enableShortcutKey**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableShortcutKey(enabled: boolean): VideoAttribute` |
| 返回值 | `VideoAttribute` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-3.1, AC-3.8, AC-3.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `enabled` | boolean | 是 | false | true 打开快捷键；需要节点获取焦点才生效 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `enableShortcutKey(true)` + 空格键 | `isPlaying_` ? Pause : Start | AC-3.2 |
| 2 | `enableShortcutKey(true)` + 左右方向键 | seek ±1 秒（SEEK_CLOSEST） | AC-3.3, AC-3.4 |
| 3 | `enableShortcutKey(true)` + 上下方向键 | volume ±0.05 | AC-3.5, AC-3.6 |
| 4 | 目标音量 = 0 | 触发 `SetMediaMuted(true)` | AC-3.7 |
| 5 | `enableShortcutKey(false)` | 按键静默；焦点行为不变 | AC-3.8 |
| 6 | 组件失焦 | focusHub 不分发按键 | AC-3.9 |

**PosterOptions**

| 属性 | 值 |
|------|-----|
| 类型定义 | `interface PosterOptions { showFirstFrame?: boolean; contentTransitionEffect?: ContentTransitionEffect; }` |
| 位置 | `interface/sdk-js/api/@internal/component/ets/video.d.ts:308-329` |
| 开放范围 | Public |
| 关联 AC | AC-2.1, AC-2.4, AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `showFirstFrame` | boolean | 否 | false | true → `SetRenderFirstFrame(true)` |
| `contentTransitionEffect` | `ContentTransitionEffect` | 否 | `IDENTITY` | 非 IDENTITY 才启用过渡 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 未设置 `posterOptions` | `showFirstFrame_ = false`，`contentTransition_ = IDENTITY`；走老 poster 路径 | AC-2.6 |
| 2 | `showFirstFrame: true` + `contentTransitionEffect: SLIDE`（示例） | 预览图保留至首帧；过渡效果生效 | AC-2.1, AC-2.5 |
| 3 | Poster 加载失败 | 背景色暴露；MediaPlayer prepare 后自然覆盖 | AC-2.7 |

**C-API 补充**

Video 组件当前无 C-API 表面；AI 分析、Poster 过渡、快捷键均无 NDK 消费入口。

## 兼容性声明

- **已有 API 行为变更:** 否。三类能力都是新增开关，默认关闭（`enableAnalyzer: false`、`enableShortcutKey: false`、`showFirstFrame: false`、`contentTransitionEffect: IDENTITY`）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** `enableAnalyzer` / `analyzerConfig` / `imageAIOptions` 起自 API 12；`enableShortcutKey` 起自 API 15；`PosterOptions.showFirstFrame` 起自 API 18；`PosterOptions.contentTransitionEffect` 起自 API 21。
- **API 版本号策略:** 三类能力均是加性扩展；旧应用无需变更。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|---------|
| Analyzer 与 controls 互斥 | `IsSupportImageAnalyzer()` 内 `!needControlBar` 强制；两者不可同时启用 | AC-1.3, AC-1.4 |
| Analyzer 依赖 `ImageAnalyzerManager` 单例 | 每个 Video 节点持有独立 `imageAnalyzerManager_`，Holder 类型固定为 `VIDEO_CUSTOM` | AC-1.1 |
| ShortcutKey 依赖 focusHub 与 KeyAction::DOWN | 只在按下瞬间响应；持续按下不重复触发 | AC-3.1, AC-3.2 |
| 音量步长与 seek 步长硬编码 | `VOLUME_STEP = 0.05`；seek 步长 1 秒；应用无法定制 | AC-3.3, AC-3.5 |
| `showFirstFrame` 需要 MediaPlayer 支持 `SetRenderFirstFrame` | 平台层未支持时降级到默认行为（无差异） | AC-2.1 |
| `contentTransitionEffect` 需要 Image 渲染层支持 | 通过 `ImageRenderProperty::UpdateContentTransition` 落地 | AC-2.4, AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Analyzer overlay 创建延迟 `ANALYZER_DELAY_TIME` | 集成测试 | `video_pattern.cpp:2470` |
| 功耗 | Analyzer 关闭时不占用推理算力 | 集成测试 | `enableAnalyzer(false)` 路径 |
| 内存 | overlay 销毁后 `imageAnalyzerManager_` 引用释放 | LeakSanitizer | `DestroyAnalyzerOverlay` 路径 |
| 安全 | 快捷键不越权触发音量最大化 | 集成测试 | `AdjustVolume` clamp 到 [0,1] |
| 可靠性 | seek 越界时 `MoveByStep` 静默返回 | 单测 | `video_pattern.cpp:1364` if 判空 |
| 可测试性 | 状态字段有 dump 支撑 | dump 测试 | `enableAnalyzer` 与 `enableShortcutKey` 均写入 dump JSON |
| 自动化维测 | `TAG_LOGD(ACE_VIDEO, ...)` 覆盖 Analyzer 与快捷键路径 | hilog 抽样 | `video_pattern.cpp` 内 |
| 定界定位 | `DumpInfo` 输出 `enableAnalyzer / enableShortcutKey` 当前值（`video_pattern.cpp:2597, 2604`） | dump 测试 | 同上 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|-----------|----------|------|
| 手机 | 快捷键效果同键盘（外接） | 触摸交互不受影响 | 集成测试 | `OnKeyEvent` 通用 |
| 平板 | 与手机一致 | 外接键盘广泛可用 | 集成测试 | 同上 |
| 折叠屏 | 与手机一致 | 屏幕切换不影响快捷键 | 集成测试 | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Analyzer overlay 使用独立无障碍节点；快捷键不影响 accessibility 焦点顺序 | AC-1.1, AC-3.1 |
| 大字体 | 否 | 三类能力无文本渲染 | N/A |
| 深色模式 | 是 | Analyzer overlay 使用 ImageAnalyzer 自身主题；不由 Video 控制 | AC-1.1 |
| 多窗口/分屏 | 是 | Analyzer overlay 随窗口尺寸变化 → `UpdateAnalyzerOverlay` | AC-1.8 |
| 多用户 | 否 | 无用户身份差异 | N/A |
| 版本升级 | 是 | API 12/15/18/21 分阶段增量；老应用不受影响 | 全部 AC |
| 生态兼容 | 是 | Static (`.d.ets`) 版本已同步；`VideoOptions.imageAIOptions` 在两版本均可用 | AC-1.6 |

## 行为场景（可选，Gherkin）

```
Feature: Video 快捷键交互
  作为 使用外接键盘的用户
  我想要 空格键切播、方向键 seek/调音量
  以便 不用触摸也能操作视频

  Scenario: 空格键切换播放
    Given enableShortcutKey 为 true
    And Video 组件已获得焦点
    And 当前正在播放
    When 用户按下空格键
    Then Video 触发 Pause
    And 触发 onPause 事件

  Scenario Outline: 方向键 seek
    Given enableShortcutKey 为 true
    And 当前时间为 5 秒
    And 总时长 10 秒
    When 用户按下 <key>
    Then 目标时间为 <target>
    And seek 结果为 <result>

    Examples:
      | key             | target | result           |
      | KEY_DPAD_RIGHT  | 6      | 走 SeekMode.SEEK_CLOSEST |
      | KEY_DPAD_LEFT   | 4      | 走 SeekMode.SEEK_CLOSEST |
      | KEY_DPAD_LEFT (当前=0) | -1  | 越界，不 seek |
      | KEY_DPAD_RIGHT (当前=10) | 11 | 越界，不 seek |

  Scenario Outline: 音量调节与静音
    Given enableShortcutKey 为 true
    And 当前音量为 <current>
    When 用户按下 <key>
    Then 目标音量为 <target>
    And 是否设置静音为 <muted>

    Examples:
      | current | key           | target | muted |
      | 0.5     | KEY_DPAD_UP   | 0.55   | false |
      | 0.05    | KEY_DPAD_DOWN | 0.0    | true  |
      | 1.0     | KEY_DPAD_UP   | 1.05 (越界) | 拒绝 |
      | 0.0     | KEY_DPAD_DOWN | -0.05 (越界) | 拒绝 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（AI 分析 + Poster + 快捷键 vs Feat-01 显示/播放/事件 vs Feat-02 Controller/全屏）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ImageAnalyzerManager 的 Holder 分类与 Video 组件的接入方式"
  - repo: "openharmony/arkui_ace_engine"
    query: "Video enableShortcutKey 与状态机 Pattern（VideoStateMachinePattern）的组合行为"
  - repo: "openharmony/interface_sdk-js"
    query: "PosterOptions.contentTransitionEffect 完整枚举列表与 IDENTITY 语义"
```

**关键文档：**
- 设计文档：`specs/05-ui-components/13-platform-components/02-video/design.md`
- 上游声明：`interface/sdk-js/api/@internal/component/ets/video.d.ts:308-329`（PosterOptions）、`video.d.ts:966-1048`（Analyzer / shortcut key）
