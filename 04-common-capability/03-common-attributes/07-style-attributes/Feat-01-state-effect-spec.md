# 特性规格

> Func-04-03-07-Feat-01 状态效果：固化 stateStyles/hoverEffect/clickEffect 三个核心状态效果属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 状态效果 (State Effect) |
| 特性编号 | Func-04-03-07-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 8 起支持，API 12/14 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | stateStyles/hoverEffect/clickEffect 行为规格 | 已有实现，补录完整行为规格 |
| MODIFIED | stateStyles 从 4 状态扩展到 6 状态（增加 HOVERED/SELECTED） | 源码实际支持 6 种 UIState |
| MODIFIED | stateStyles 机制从「单一 API 调用」修正为「ViewStackProcessor 双阶段 VisualState」 | 源码使用 ViewStackProcessor::visualState 设置状态上下文，属性 setter 通过 IsCurrentVisualStateProcess() 判断 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/07-style-attributes/design.md` | Baselined |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 设置 stateStyles 实现多状态样式

**作为** 应用开发者,
**我想要** 通过 `.stateStyles(StateStyles)` 为组件在不同交互状态下定义不同样式,
**以便** 组件在 Normal/Pressed/Disabled/Focused/Selected/Hovered 状态下呈现不同的视觉表现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.stateStyles({ pressed: { ... } })` THEN ViewStackProcessor::SetVisualState(VisualState::PRESSED) 设置当前状态上下文为 PRESSED，后续属性 setter 通过 IsCurrentVisualStateProcess() 判断仅 Pressed 状态的属性生效；同时 EventHub::AddSupportedState(UI_STATE_PRESSED) 注册到 StateStyleManager::supportedStates_ | 正常 |
| AC-1.2 | WHEN 组件处于 Normal 状态（currentState_ == UI_STATE_NORMAL）THEN 应用 normal 中定义的属性 | 正常 |
| AC-1.3 | WHEN 组件进入 Pressed 状态（触摸按下）THEN StateStyleManager::UpdateCurrentUIState(UI_STATE_PRESSED) 使 currentState_ |= UI_STATE_PRESSED；CustomNodeBase::FireNodeUpdateFunc 触发 ArkTS 重新渲染，Pressed 状态属性覆盖 Normal 状态属性 | 正常 |
| AC-1.4 | WHEN 组件进入 Disabled 状态 THEN Disabled 状态属性覆盖 Normal 状态属性（currentState_ |= UI_STATE_DISABLED） | 正常 |
| AC-1.5 | WHEN 组件进入 Focused 状态 THEN FocusHub::CheckFocusStateStyle(true) 调用 EventHub::UpdateCurrentUIState(UI_STATE_FOCUSED)，Focused 状态属性覆盖 Normal 状态属性 | 正常 |
| AC-1.6 | WHEN 组件进入 Selected 状态 THEN Selected 状态属性覆盖 Normal 状态属性（currentState_ |= UI_STATE_SELECTED） | 正常 |
| AC-1.7 | WHEN 组件进入 Hovered 状态（鼠标悬停）THEN StateStyleManager hover listener 调用 UpdateCurrentUIState(UI_STATE_HOVERED)，Hovered 状态属性覆盖 Normal 状态属性 | 正常 |
| AC-1.8 | WHEN 多个状态同时激活（如 Pressed + Focused）THEN currentState_ 为两个状态的位掩码合并值；HandleStateChangeInternal 按 inner→frontend→user 优先级链执行状态回调；同一属性以最后应用的回调结果为准 | 边界 |
| AC-1.9 | WHEN stateStyles 中某状态未定义 THEN 该状态不注册到 supportedStates_（AddSupportedUIStateWithCallback 对 UI_STATE_NORMAL 返回 false），状态变化时不触发样式刷新 | 异常 |
| AC-1.10 | WHEN 组件在滚动容器内触摸按下 THEN Pressed 状态延迟 300ms（PRESS_STYLE_DELAY）触发；若 300ms 内开始滚动 THEN 取消 Pressed 状态挂起（scrollingEventCallback 重置 pending） | 边界 |
| AC-1.11 | WHEN 组件在滚动容器内触摸按下后 300ms 内触摸抬起 THEN Pressed 状态短暂闪烁后 64ms（PRESS_CANCEL_STYLE_DELAY）取消（UpdateCurrentUIState→PostPressCancelStyleTask） | 边界 |
| AC-1.12 | WHEN 触摸移动超出组件响应区域 THEN IsOutOfPressedRegion 返回 true，Pressed 状态取消（ResetPressedState） | 边界 |

### US-2: 设置 hoverEffect 实现悬停反馈

**作为** 应用开发者,
**我想要** 通过 `.hoverEffect(HoverEffectType)` 设置组件悬停时的视觉反馈类型,
**以便** 用户在鼠标悬停时获得明确的交互提示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.hoverEffect(HoverEffectType.AUTO)` THEN InputEventHub::hoverEffectType_ 设为 AUTO；框架根据组件类型自动选择最佳悬停效果（hoverEffectAuto_ 由组件 Pattern 设置） | 正常 |
| AC-2.2 | WHEN 调用 `.hoverEffect(HoverEffectType.SCALE)` THEN 鼠标悬停时 FrameNode::AnimateHoverEffect(true) 调用 RosenRenderContext::AnimateHoverEffectScale，组件产生均匀缩放效果（scale 从 hoverScaleStart 到 hoverScaleEnd，cubic curve 0.2/0.0/0.2/1.0） | 正常 |
| AC-2.3 | WHEN 调用 `.hoverEffect(HoverEffectType.HIGHLIGHT)` THEN 鼠标悬停时 FrameNode::AnimateHoverEffect(true) 调用 RosenRenderContext::AnimateHoverEffectBoard，组件背景色 BlendColor 混合变化 + OnHoverWithHightLight | 正常 |
| AC-2.4 | WHEN 调用 `.hoverEffect(HoverEffectType.NONE)` THEN 鼠标悬停时 FrameNode::AnimateHoverEffect 不执行任何动画 | 正常 |
| AC-2.5 | WHEN hoverEffect 未设置 THEN hoverEffectType_ 默认为 HoverEffectType::UNKNOWN（无悬停效果） | 异常 |
| AC-2.6 | WHEN 同时设置 SetHoverEffect 和 SetHoverEffectAuto THEN SetHoverEffect 存储到 hoverEffectType_，SetHoverEffectAuto 存储到 hoverEffectAuto_，两者独立管理；AUTO/UNKNOWN 类型解析时使用 hoverEffectAuto_ | 边界 |
| AC-2.7 | WHEN 调用 `.hoverEffect(HoverEffectType.OPACITY)` THEN NG 管线中 FrameNode::AnimateHoverEffect 不处理 OPACITY 类型，无动画效果；OPACITY 仅在旧管线 RenderBox 中实现 | 边界 |
| AC-2.8 | WHEN Button 组件设置 hoverEffect(HIGHLIGHT) THEN ButtonPattern 内部将 HIGHLIGHT 转换为 AUTO（BOARD 类型被拒绝） | 边界 |

### US-3: 设置 clickEffect 实现点击反馈

**作为** 应用开发者,
**我想要** 通过 `.clickEffect(ClickEffect)` 设置组件点击时的视觉反馈,
**以便** 用户在点击组件时获得触觉级别的视觉确认。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.clickEffect({ level: ClickEffectLevel.LIGHT })` THEN RenderContext::propClickEffectLevel_ 存储 ClickEffectInfo{LIGHT, scaleNumber}；触摸按下时 ClickEffectPlayAnimation 执行 spring 缩放动画（velocity=10, mass=1, stiffness=410, damping=38），目标 scale = sqrt(userScale) | 正常 |
| AC-3.2 | WHEN 调用 `.clickEffect({ level: ClickEffectLevel.MIDDLE })` THEN spring 参数：velocity=10, mass=1, stiffness=350, damping=35 | 正常 |
| AC-3.3 | WHEN 调用 `.clickEffect({ level: ClickEffectLevel.HEAVY })` THEN spring 参数：velocity=velocity_heavy, mass=1, stiffness=240, damping=28 | 正常 |
| AC-3.4 | WHEN 调用 `.clickEffect({ level: ClickEffectLevel.UNDEFINED })` THEN clickEffect 重置为未定义（等同取消 clickEffect） | 异常 |
| AC-3.5 | WHEN clickEffect 的 level 值超出 LIGHT~HEAVY 范围 THEN level 被纠正为 0（LIGHT） | 异常 |
| AC-3.6 | WHEN clickEffect 中 scale 值在 [0, 1] 范围内 THEN scaleValue = sqrt(scale) 用于 spring 动画目标 | 正常 |
| AC-3.7 | WHEN clickEffect 中 scale 值不在 [0, 1] 范围内 THEN LIGHT 使用 DEFAULT_SCALE_LIGHT(0.9)，MIDDLE/HEAVY 使用 DEFAULT_SCALE_MIDDLE_OR_HEAVY(0.95) | 边界 |
| AC-3.8 | WHEN clickEffect 传入 null/undefined THEN level 重置为 UNDEFINED，scaleValue 重置为 DEFAULT_SCALE_LIGHT | 异常 |
| AC-3.9 | WHEN clickEffect 与 stateStyles pressed 同时设置 THEN clickEffect 操作 TransformScale（弹簧物理动画），stateStyles pressed 操作属性覆盖（CSS 状态样式），两者独立并存 | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|----------|------|
| AC-1.1~1.7 | R-1 | — | 单测 | StateStyleManager 状态注册与刷新 |
| AC-1.8 | R-1, R-9 | — | 单测 | 多状态合并覆盖 |
| AC-1.9 | R-1 | — | 单测 | 未注册状态不刷新 |
| AC-1.10~1.12 | R-2 | — | 单测 | 滚动延迟、取消延迟、超出区域 |
| AC-2.1~2.4 | R-3 | — | 单测 | InputEventHub hover 效果 |
| AC-2.5~2.8 | R-3, R-10 | — | 单测 | 默认值、OPACITY 无效、组件覆盖 |
| AC-3.1~3.3 | R-4 | — | 单测 | ClickEffect spring 参数 |
| AC-3.4~3.8 | R-4 | — | 单测 | 边界与异常处理 |
| AC-3.9 | R-4, R-1 | — | 单测 | clickEffect 与 stateStyles 并存 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | stateStyles 设置多状态样式 | ViewStackProcessor::SetVisualState 设置状态上下文，IsCurrentVisualStateProcess() 决定属性是否生效；状态激活时 CustomNodeBase::FireNodeUpdateFunc 触发 ArkTS 重新渲染 | UI_STATE 位掩码：NORMAL=0, PRESSED=1, FOCUSED=2, DISABLED=4, SELECTED=8, HOVERED=16, UNKNOWN=512；VisualState 字符串映射："normal"→NORMAL, "pressed"/"clicked"→PRESSED, "focused"→FOCUSED, "disabled"→DISABLED, "hover"→HOVERED, "selected"→SELECTED | AC-1.1~1.7 |
| R-2 | 行为 | Pressed 状态在滚动容器中延迟触发 | HandleScrollingParent 检查父级 ShouldDelayChildPressedState；有滚动父级时 PostPressStyleTask 延迟 300ms | PRESS_STYLE_DELAY=300ms, PRESS_CANCEL_STYLE_DELAY=64ms；ShouldPreventChildPressedState() 在快速滚动时完全阻止 Pressed | AC-1.10~1.12 |
| R-3 | 行为 | hoverEffect 设置悬停效果 | AUTO=框架决定(hoverEffectAuto_)；SCALE=缩放动画(AnimateHoverEffectScale)；HIGHLIGHT=背景色混合(AnimateHoverEffectBoard)；NONE=无效果 | 内部枚举：NONE=0, OPACITY=1, SCALE=2, BOARD=3, AUTO=4, UNKNOWN=5；C-API 映射：AUTO=0, SCALE=1, HIGHLIGHT=2, NONE=3；OPACITY 在 NG 管线不生效 | AC-2.1~2.4 |
| R-4 | 行为 | clickEffect 设置点击反馈 | ClickEffectInfo 存储在 RenderContext::propClickEffectLevel_；触摸 DOWN/UP 时 ClickEffectPlayAnimation 执行 spring 缩放动画；scale 值 = sqrt(userScale) 用于动画目标 | spring 参数固定不可自定义；UNDEFINED=-1 重置；scale 范围 [0,1]，超出用默认值 | AC-3.1~3.3 |
| R-5 | 边界 | stateStyles 中多个状态同时激活 | currentState_ 为多个 UI_STATE 位掩码合并值；HandleStateChangeInternal 按 inner→frontend→user 优先级链执行 | UI_STATE 使用 uint64_t 位掩码管理 | AC-1.8 |
| R-6 | 边界 | HoverEffectType.OPACITY 在 NG 管线无效 | FrameNode::AnimateHoverEffect 不处理 OPACITY 类型，仅 NONE/SCALE/BOARD(AUTO 解析后) 有动画 | OPACITY 仅旧管线 RenderBox 实现；NG 管线 fallthrough 无动画 | AC-2.7 |
| R-7 | 边界 | 部分组件覆盖 hoverEffect 行为 | Button/ToggleButton 拒绝 HIGHLIGHT(Board) 转为 AUTO；Progress(Capsule) 强制 SCALE；Progress(Linear/Moon) 强制 NONE | 组件 Pattern 通过 InputEventHub::SetHoverEffect 或自有 TouchHoverAnimationType 覆盖 | AC-2.8 |
| R-8 | 边界 | 触摸超出响应区域取消 Pressed | IsOutOfPressedRegion 检查 self+祖先 clip 茂围；触摸 MOVE 时 pointerId_ 清除导致 ResetPressedState | 祖先 clipEdge=true 时额外检查祖先区域 | AC-1.12 |
| R-9 | 异常 | stateStyles 中某状态未定义 | 该状态不注册到 supportedStates_，状态变化时 HasStateStyle 返回 false，不触发 FireStateFunc | AddSupportedUIStateWithCallback 对 UI_STATE_NORMAL 返回 false | AC-1.9 |
| R-10 | 异常 | hoverEffect 默认值 UNKNOWN | 未设置 hoverEffect 时 hoverEffectType_ = UNKNOWN，AnimateHoverEffect 无动画 | UNKNOWN=5 为内部哨兵值，非公开枚举 | AC-2.5 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1, AC-1.1~1.7 | 单测 | StateStyleManager 状态注册与 VisualState 刷新 |
| VM-2 | R-2, AC-1.10~1.12 | 单测 | 滚动延迟 300ms + 取消延迟 64ms + 超出区域 |
| VM-3 | R-3, AC-2.1~2.4 | 单测 | hoverEffect 四种效果类型行为 |
| VM-4 | R-6, AC-2.7 | 单测 | OPACITY 在 NG 管线无动画 |
| VM-5 | R-7, AC-2.8 | 单测 | Button 等组件覆盖 hoverEffect |
| VM-6 | R-4, AC-3.1~3.3 | 单测 | clickEffect spring 参数和 scale 计算 |
| VM-7 | R-4, AC-3.9 | 单测 | clickEffect 与 stateStyles 并存 |
| VM-8 | R-5, AC-1.8 | 单测 | 多状态合并覆盖行为 |
| VM-9 | 全量 | XTS/集成 | 端到端状态效果与交互反馈正确 |

---

## API 变更分析

### 新增 API

| API 签名 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| `stateStyles(value: StateStyles): T` | Public | StateStyles{normal?, pressed?, disabled?, focused?, clicked?, selected?, hover?} | T | — | 多状态样式定义 | AC-1.1~1.9 |
| `hoverEffect(value: HoverEffectType): T` | Public | HoverEffectType(Auto/Scale/Highlight/None) | T | — | 悬停效果类型 | AC-2.1~2.8 |
| `clickEffect(value: ClickEffect \| null): T` | Public | ClickEffect{level: ClickEffectLevel, scale?: number} | T | — | 点击反馈效果 | AC-3.1~3.9 |

> **Native C-API 属性枚举**：

| 属性枚举 | 值格式 | 功能 | @since |
|----------|--------|------|--------|
| `NODE_HOVER_EFFECT` | `.value[0].i32` (ArkUI_HoverEffect) | 设置悬停效果 | 12 |
| clickEffect (函数指针式) | `SetClickEffect(node, level, scale)` / `ResetClickEffect(node)` | 设置点击效果（node_common_modifier.cpp:6014-6027） | 12 |
| `OH_ArkUI_AddSupportedUIStates` | 函数指针式 + excludeInner 参数 | 注册 C-API 状态回调 | 20 |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `StateStyles` | `{ normal?: any; pressed?: any; disabled?: any; focused?: any; clicked?: any; selected?: object }` | index.d.ts:990 |
| `HoverEffectType` | Auto/Scale/Highlight/None | native_type.h:1328 (C-API) |
| `ClickEffect` | `{ level: number; scale?: number }` | index.d.ts:782 |
| `ClickEffectLevel` | UNDEFINED=-1, LIGHT=0, MIDDLE=1, HEAVY=2 | effect_option.h:28 |
| `UIState` (uint64_t) | NORMAL=0, PRESSED=1, FOCUSED=2, DISABLED=4, SELECTED=8, HOVERED=16, UNKNOWN=512 | state_style_manager.h:35-43 |
| `ArkUI_UIState` | NORMAL=0, PRESSED=1, FOCUSED=2, DISABLED=4, SELECTED=8, HOVERED=16 | native_type.h:1664 |

### 变更/废弃 API

N/A，已有能力补录，API 行为无变化。

---

## 接口规格

### 接口定义

**stateStyles**

| 属性 | 值 |
|------|-----|
| 函数签名 | `stateStyles(value: StateStyles): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.normal | StateStyleAttribute | 否 | undefined | 未定义则不注册对应 UIState |
| value.pressed | StateStyleAttribute | 否 | undefined | 设置时注册 UI_STATE_PRESSED |
| value.disabled | StateStyleAttribute | 否 | undefined | 设置时注册 UI_STATE_DISABLED |
| value.focused | StateStyleAttribute | 否 | undefined | 设置时注册 UI_STATE_FOCUSED |
| value.selected | StateStyleAttribute | 否 | undefined | 设置时注册 UI_STATE_SELECTED |
| value.clicked | StateStyleAttribute | 否 | undefined | 映射到 VisualState::PRESSED |
| value.hover | StateStyleAttribute | 否 | undefined | 设置时注册 UI_STATE_HOVERED |

> **内部机制**：stateStyles 不是单一 API 调用，而是通过 ViewStackProcessor 双阶段机制实现——先通过 `ViewStackProcessor::visualState(stateString)` 设置当前状态上下文，属性 setter 在头部调用 `IsCurrentVisualStateProcess()` 判断是否仅对当前状态生效。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 stateStyles 且所有状态均已定义 | 所有状态注册到 supportedStates_，状态变化时触发样式刷新 | AC-1.1 |
| 2 | 组件从 Normal 进入 Pressed 状态 | currentState_ |= UI_STATE_PRESSED，Pressed 属性覆盖 Normal | AC-1.3 |
| 3 | Pressed + Focused 同时激活 | currentState_ 为位掩码合并值，属性按 inner→frontend→user 优先级链覆盖 | AC-1.8 |
| 4 | stateStyles 中某状态为 undefined | 该状态不注册，HasStateStyle 返回 false，不触发刷新 | AC-1.9 |
| 5 | 滚动容器内 Pressed 延迟 300ms | PostPressStyleTask 延迟触发；滚动开始时取消挂起 | AC-1.10 |
| 6 | 滚动容器内 Pressed 后快速抬起 | 短暂闪烁后 64ms 取消 | AC-1.11 |
| 7 | 触摸超出响应区域 | ResetPressedState 取消 Pressed | AC-1.12 |

---

**hoverEffect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `hoverEffect(value: HoverEffectType): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | HoverEffectType | 是 | — | 内部枚举：NONE=0, OPACITY=1, SCALE=2, BOARD=3, AUTO=4, UNKNOWN=5；C-API：AUTO=0, SCALE=1, HIGHLIGHT=2, NONE=3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | hoverEffect(AUTO) | 框架根据组件类型选择最佳悬停效果（hoverEffectAuto_） | AC-2.1 |
| 2 | hoverEffect(SCALE) | AnimateHoverEffectScale 缩放动画 | AC-2.2 |
| 3 | hoverEffect(HIGHLIGHT) | AnimateHoverEffectBoard 背景色混合 + OnHoverWithHightLight | AC-2.3 |
| 4 | hoverEffect(NONE) | 无悬停视觉效果 | AC-2.4 |
| 5 | hoverEffect(OPACITY) | NG 管线无动画（仅旧管线 RenderBox 实现） | AC-2.7 |
| 6 | Button 设置 HIGHLIGHT | Pattern 内部转为 AUTO | AC-2.8 |

---

**clickEffect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `clickEffect(value: ClickEffect \| null): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.level | ClickEffectLevel | 是 | — | LIGHT=0, MIDDLE=1, HEAVY=2, UNDEFINED=-1 |
| value.scale | number | 否 | LIGHT→0.9, MIDDLE/HEAVY→0.95 | 范围 [0, 1]；超出范围使用默认值 |

> **存储位置**：ClickEffectInfo 存储在 RenderContext::propClickEffectLevel_（不同于 stateStyles 存储在 StateStyleManager/EventHub）。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | clickEffect({ level: LIGHT }) | spring 缩放动画（stiffness=410, damping=38） | AC-3.1 |
| 2 | clickEffect({ level: MIDDLE }) | spring 缩放动画（stiffness=350, damping=35） | AC-3.2 |
| 3 | clickEffect({ level: HEAVY }) | spring 缩放动画（stiffness=240, damping=28） | AC-3.3 |
| 4 | clickEffect(null) | 重置 clickEffect 为 UNDEFINED | AC-3.4 |
| 5 | scale 值超出 [0,1] 范围 | 使用默认值 | AC-3.7 |
| 6 | clickEffect + stateStyles pressed 并存 | clickEffect 操作 TransformScale，stateStyles 操作属性覆盖，两者独立生效 | AC-3.9 |

---

## 兼容性声明

- **已有 API 行为变更:**
  - **API 12**: ClickEffect 新增 MIDDLE 等级（ClickEffectLevel::MIDDLE = 1）
  - HoverEffectType.OPACITY 在 NG 管线不生效（仅旧管线支持）
  - HoverEffectType 内部枚举映射差异：内部 NONE=0/OPACITY=1/SCALE=2/BOARD=3/AUTO=4/UNKNOWN=5，C-API AUTO=0/SCALE=1/HIGHLIGHT=2/NONE=3
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 8 为 stateStyles/hoverEffect 基础，@since 12 为 clickEffect，@since 20 为 OH_ArkUI_AddSupportedUIStates

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| UI_STATE 位掩码管理 | StateStyleManager 使用 uint64_t 位掩码管理多状态，通过 |= 和 ^= 操作合并/移除状态 | AC-1.3~1.8 |
| ViewStackProcessor 双阶段 VisualState | stateStyles 通过 ViewStackProcessor::visualState 设置状态上下文，属性 setter 通过 IsCurrentVisualStateProcess() 过滤 | AC-1.1 |
| Spring 动画参数固化 | clickEffect 的 spring 参数为引擎内部常量，不可由开发者自定义 | AC-3.1~3.3 |
| clickEffect 存储在 RenderContext | ClickEffectInfo 存储 propClickEffectLevel_，独立于 StateStyleManager 状态系统 | AC-3.1 |
| HandleStateChangeInternal 优先级链 | inner→frontend→user 三级回调，inner 可被 excludeInner 跳过 | AC-1.8 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | stateStyles 状态切换（FireStateFunc）< 1ms | benchmark | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | hoverEffect 在触屏设备上无鼠标悬停事件，不触发；clickEffect 和 stateStyles pressed 正常生效 | 鼠标类设备才触发 hover | 交互测试 | — |
| 平板 | hoverEffect 在鼠标连接时触发；Pressed 状态 300ms 延迟对 List 等滚动组件生效 | 外接鼠标支持 | 交互测试 | — |
| 折叠屏 | 行为与手机一致 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | stateStyles focused 状态样式增强焦点可见性；clickEffect 缩放动画不影响无障碍语义 | AC-1.5, AC-3.1 |
| 大字体 | 是 | stateStyles 中文本属性受大字体缩放影响 | AC-1.1 |
| 深色模式 | 是 | stateStyles 中颜色属性需适配深色模式；hoverEffect(HIGHLIGHT) 的 hoverColor 受深色模式影响 | AC-1.1, AC-2.3 |
| 多窗口/分屏 | 否 | 状态效果与窗口无关 | — |
| 多用户 | 否 | 无用户级别差异 | — |
| 版本升级 | 是 | API 12 ClickEffect 新增 MIDDLE 等级；API 20 C-API AddSupportedUIStates 新增 | AC-3.2 |
| 生态兼容 | 是 | HoverEffectType 内部枚举与 C-API 枚举映射不同（值不同但语义一致），OPACITY 在 NG 管线不生效 | AC-2.1~2.4, AC-2.7 |

---

## 风险 / Risks

| 风险ID | 类型 | 描述 | 影响AC | 缓解策略 |
|--------|------|------|--------|----------|
| RK-1 | 版本 | HoverEffectType.OPACITY 在 NG 管线不生效（FrameNode::AnimateHoverEffect 未处理 OPACITY 类型），仅旧管线 RenderBox 实现 | AC-2.7 | 标注为已知行为差异，建议文档同步 |
| RK-2 | 版本 | HoverEffectType 内部枚举(NONE=0/OPACITY=1/SCALE=2/BOARD=3/AUTO=4)与 C-API 枚举(AUTO=0/SCALE=1/HIGHLIGHT=2/NONE=3)值不同但语义一致 | AC-2.1~2.4 | C-API 使用 ConvertToHoverEffectType 映射表，行为一致但值域不同 |
| RK-3 | 版本 | ClickEffectLevel MIDDLE=1 为 API 12 新增，旧版本应用不暴露 MIDDLE | AC-3.2 | @since 12 版本守护 |
| RK-4 | 行为 | Button/ToggleButton 等组件内部覆盖 hoverEffect 设置（拒绝 HIGHLIGHT→转为 AUTO），开发者设置的值可能不生效 | AC-2.8 | 标注为组件级覆盖行为，各组件 spec 单独说明 |
| RK-5 | 行为 | 滚动容器内 Pressed 状态 300ms 延迟可能导致交互感知延迟 | AC-1.10 | 标注为已知行为，ShouldDelayChildPressedState 由组件 Pattern 控制 |

---

## 行为场景（可选，Gherkin）

Feature: 状态效果与交互反馈
  作为 应用开发者
  我想要 为组件设置多状态样式和交互反馈效果
  以便 实现丰富的交互视觉反馈

  Scenario: stateStyles 多状态样式切换
    Given 组件设置了 stateStyles({ normal: { backgroundColor: '#FFFFFF' }, pressed: { backgroundColor: '#DDDDDD' } })
    When 用户触摸按下该组件
    Then ViewStackProcessor::SetVisualState(PRESSED) 设置状态上下文
    And currentState_ |= UI_STATE_PRESSED
    And CustomNodeBase::FireNodeUpdateFunc 触发 ArkTS 重新渲染
    And 组件背景色变为 '#DDDDDD'（Pressed 覆盖 Normal）
    When 用户触摸抬起
    Then ResetCurrentUIState(UI_STATE_PRESSED)
    And 组件背景色恢复为 '#FFFFFF'（回退到 Normal）

  Scenario: stateStyles 在滚动容器中 Pressed 延迟
    Given 组件设置了 stateStyles({ pressed: { backgroundColor: '#DDDDDD' } })
    And 组件位于 List 滚动容器内
    When 用户触摸按下但未滚动
    Then Pressed 状态延迟 300ms 触发
    When 300ms 内开始滚动
    Then scrollingEventCallback 取消 Pressed 挂起

  Scenario: hoverEffect 悬停反馈类型
    Given 组件设置了 hoverEffect(HoverEffectType.SCALE)
    When 用户鼠标悬停到该组件
    Then AnimateHoverEffectScale 执行缩放动画
    When 用户鼠标离开该组件
    Then 缩放效果取消

  Scenario: hoverEffect OPACITY 在 NG 管线无效
    Given 组件设置了 hoverEffect(HoverEffectType.OPACITY)
    When 用户鼠标悬停到该组件
    Then FrameNode::AnimateHoverEffect 不处理 OPACITY
    And 无任何悬停视觉效果

  Scenario: clickEffect 点击反馈
    Given 组件设置了 clickEffect({ level: ClickEffectLevel.LIGHT, scale: 0.9 })
    When 用户点击该组件（触摸按下）
    Then ClickEffectPlayAnimation 执行 spring 缩放动画（target = sqrt(0.9)）
    When 用户触摸抬起
    Then spring 动画恢复原始 scale

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "ViewStackProcessor::SetVisualState 双阶段机制 (view_stack_processor.cpp:226-251)"
  - repo: "openharmony/ace_engine"
    query: "StateStyleManager UI_STATE 位掩码管理与 HandleStateChangeInternal 优先级链 (state_style_manager.h:35-43, state_style_manager.cpp:234-278)"
  - repo: "openharmony/ace_engine"
    query: "Pressed 状态 300ms/64ms 延迟 (state_style_manager.cpp:29-31, 103-150)"
  - repo: "openharmony/ace_engine"
    query: "HoverEffectType OPACITY 在 NG 管线无动画 (frame_node.cpp:4594-4613)"
  - repo: "openharmony/ace_engine"
    query: "ClickEffectInfo 存储在 RenderContext + spring 参数 (render_context.h:561, rosen_render_context.cpp:7587-7623)"
  - repo: "openharmony/ace_engine"
    query: "HoverEffectType 内部枚举与 C-API 枚举映射 (mouse_constants.h:48, native_type.h:1328)"
```

**关键文档：**
- ViewStackProcessor VisualState: `frameworks/core/components_ng/base/view_stack_processor.cpp:226-251`
- StateStyleManager: `frameworks/core/components_ng/event/state_style_manager.h:48`
- InputEventHub hoverEffect: `frameworks/core/components_ng/event/input_event_hub.h:358-359`
- HoverEffectType 枚举: `frameworks/core/event/mouse_constants.h:48-55`
- ClickEffectLevel: `frameworks/core/components/common/properties/effect_option.h:28-42`
- FrameNode::AnimateHoverEffect: `frameworks/core/components_ng/base/frame_node.cpp:4594-4613`
- C-API HoverEffect: `interfaces/native/native_type.h:1326-1335`
- C-API UIState: `interfaces/native/native_type.h:1664-1680`
