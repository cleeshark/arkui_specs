# 特性规格

> Func-04-03-07-Feat-01 多态样式：固化 `stateStyles` 多状态样式能力的行为规格；`hoverEffect` 与 `clickEffect` 由 Func-04-03-04 承接。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 多态样式 (Polymorphic Style) |
| 特性编号 | Func-04-03-07-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 8 起支持 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `stateStyles` 行为规格 | 已有实现，补录完整行为规格 |
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

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|----------|------|
| AC-1.1~1.7 | R-1 | — | 单测 | StateStyleManager 状态注册与刷新 |
| AC-1.8 | R-3 | — | 单测 | 多状态合并覆盖 |
| AC-1.9 | R-5 | — | 单测 | 未注册状态不刷新 |
| AC-1.10~1.12 | R-2 | — | 单测 | 滚动延迟、取消延迟、超出区域 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | stateStyles 设置多状态样式 | ViewStackProcessor::SetVisualState 设置状态上下文，IsCurrentVisualStateProcess() 决定属性是否生效；状态激活时 CustomNodeBase::FireNodeUpdateFunc 触发 ArkTS 重新渲染 | UI_STATE 位掩码：NORMAL=0, PRESSED=1, FOCUSED=2, DISABLED=4, SELECTED=8, HOVERED=16, UNKNOWN=512；VisualState 字符串映射："normal"→NORMAL, "pressed"/"clicked"→PRESSED, "focused"→FOCUSED, "disabled"→DISABLED, "hover"→HOVERED, "selected"→SELECTED | AC-1.1~1.7 |
| R-2 | 行为 | Pressed 状态在滚动容器中延迟触发 | HandleScrollingParent 检查父级 ShouldDelayChildPressedState；有滚动父级时 PostPressStyleTask 延迟 300ms | PRESS_STYLE_DELAY=300ms, PRESS_CANCEL_STYLE_DELAY=64ms；ShouldPreventChildPressedState() 在快速滚动时完全阻止 Pressed | AC-1.10~1.12 |
| R-3 | 边界 | stateStyles 中多个状态同时激活 | currentState_ 为多个 UI_STATE 位掩码合并值；HandleStateChangeInternal 按 inner→frontend→user 优先级链执行 | UI_STATE 使用 uint64_t 位掩码管理 | AC-1.8 |
| R-4 | 边界 | 触摸超出响应区域取消 Pressed | IsOutOfPressedRegion 检查自身及祖先裁剪区域；触摸 MOVE 超出后 ResetPressedState 取消 Pressed | 祖先 clipEdge=true 时额外检查祖先区域 | AC-1.12 |
| R-5 | 异常 | stateStyles 中某状态未定义 | 该状态不注册到 supportedStates_，状态变化时 HasStateStyle 返回 false，不触发 FireStateFunc | AddSupportedUIStateWithCallback 对 UI_STATE_NORMAL 返回 false | AC-1.9 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1, AC-1.1~1.7 | 单测 | StateStyleManager 状态注册与 VisualState 刷新 |
| VM-2 | R-2, AC-1.10~1.12 | 单测 | 滚动延迟 300ms + 取消延迟 64ms + 超出区域 |
| VM-3 | R-3, AC-1.8 | 单测 | 多状态合并覆盖行为 |
| VM-4 | R-4, AC-1.12 | 单测 | 超出响应区域取消 Pressed |
| VM-5 | R-5, AC-1.9 | 单测 | 未定义状态不注册、不刷新 |
| VM-6 | 全量 | XTS/集成 | 端到端多态样式切换正确 |

---

## API 变更分析

### 新增 API

| API 签名 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| `stateStyles(value: StateStyles): T` | Public | StateStyles{normal?, pressed?, disabled?, focused?, clicked?, selected?, hover?} | T | — | 多状态样式定义 | AC-1.1~1.9 |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `StateStyles` | `{ normal?: any; pressed?: any; disabled?: any; focused?: any; clicked?: any; selected?: object }` | index.d.ts:990 |
| `UIState` (uint64_t) | NORMAL=0, PRESSED=1, FOCUSED=2, DISABLED=4, SELECTED=8, HOVERED=16, UNKNOWN=512 | state_style_manager.h:35-43 |

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

## 兼容性声明

- **已有 API 行为变更:** 否，本规格仅补录 `stateStyles` 已有行为
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** `stateStyles` 自 API 8；本规格不承接 `hoverEffect`、`clickEffect` 或 attributeModifier 的版本差异

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| UI_STATE 位掩码管理 | StateStyleManager 使用 uint64_t 位掩码管理多状态，通过 |= 和 ^= 操作合并/移除状态 | AC-1.3~1.8 |
| ViewStackProcessor 双阶段 VisualState | stateStyles 通过 ViewStackProcessor::visualState 设置状态上下文，属性 setter 通过 IsCurrentVisualStateProcess() 过滤 | AC-1.1 |
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
| 手机 | `stateStyles` 的 Pressed/Disabled/Focused/Selected 状态按输入与组件状态切换；无鼠标输入时 Hovered 状态不触发 | 状态来源由设备输入能力决定 | 交互测试 | — |
| 平板 | 外接鼠标时可触发 `stateStyles` Hovered 状态；Pressed 状态在 List 等滚动容器中仍遵循 300ms 延迟 | 外接鼠标与滚动容器行为均需覆盖 | 交互测试 | — |
| 折叠屏 | 与手机一致 | 无额外差异 | 交互测试 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | stateStyles focused 状态样式可增强焦点可见性 | AC-1.5 |
| 大字体 | 是 | stateStyles 中文本属性受大字体缩放影响 | AC-1.1 |
| 深色模式 | 是 | stateStyles 中的颜色属性需适配深色模式 | AC-1.1 |
| 多窗口/分屏 | 否 | 多态样式状态切换与窗口模式无关 | — |
| 多用户 | 否 | 无用户级别差异 | — |
| 版本升级 | 否 | 本规格仅补录 API 8 起已有的 `stateStyles` 行为 | — |
| 生态兼容 | 否 | 未引入新的公开接口或数据格式 | — |

---

## 风险 / Risks

| 风险ID | 类型 | 描述 | 影响AC | 缓解策略 |
|--------|------|------|--------|----------|
| RK-1 | 行为 | 滚动容器内 Pressed 状态 300ms 延迟可能导致交互感知延迟 | AC-1.10 | 标注为已有行为，ShouldDelayChildPressedState 由组件 Pattern 控制 |

---

## 行为场景（可选，Gherkin）

Feature: 多态样式
  作为 应用开发者
  我想要 通过 stateStyles 为组件设置多状态样式
  以便 组件状态变化时呈现对应的属性组合

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
```

**关键文档：**
- ViewStackProcessor VisualState: `frameworks/core/components_ng/base/view_stack_processor.cpp:226-251`
- StateStyleManager: `frameworks/core/components_ng/event/state_style_manager.h:48`
