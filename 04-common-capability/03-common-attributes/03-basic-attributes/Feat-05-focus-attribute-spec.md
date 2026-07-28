# 特性规格

> Func-04-03-03-Feat-05 焦点属性：固化 focusable/tabIndex/defaultFocus/groupDefaultFocus/focusOnTouch/tabStop/focusBox/nextFocus/focusScopeId/focusScopePriority 及 onFocus/onBlur/onKeyEvent 焦点事件的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 焦点属性 (Focus Attributes) |
| 特性编号 | Func-04-03-03-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起支持，API 9/14/23 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性覆盖焦点可达性（focusable/tabIndex/tabStop/focusOnTouch/defaultFocus/groupDefaultFocus）、焦点导航（nextFocus/focusScopeId/focusScopePriority）、焦点样式（focusBox）及焦点事件（onFocus/onBlur/onKeyEvent）等基础通用属性。上述属性均为所有组件的公共属性，通过 ViewAbstract / CommonMethod 统一提供。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | focusable(bool) | @since 7，控制组件是否可接收焦点 |
| ADDED | tabIndex(number) | @since 7，Tab 键遍历顺序 |
| ADDED | defaultFocus(bool) | @since 7，标记为容器默认焦点节点 |
| ADDED | groupDefaultFocus(bool) | @since 7，标记为焦点组默认焦点节点 |
| ADDED | focusOnTouch(bool) | @since 8，触摸时自动获焦 |
| ADDED | tabStop(bool) | @since 9，Tab 键是否停在此节点 |
| ADDED | focusBox(FocusBoxStyle) | @since 7，焦点框样式（strokeColor/strokeWidth/margin） |
| ADDED | nextFocus({forward?, backward?, up?, down?, left?, right?}) | @since 9，指定方向键下一个焦点目标 |
| ADDED | focusScopeId(string, isGroup?, arrowKeyStepOut?) | @since 23，焦点域标识与分组 |
| ADDED | focusScopePriority(string, priority?) | @since 23，焦点域优先级 |
| ADDED | onFocus(callback) | @since 7，获焦回调 |
| ADDED | onBlur(callback) | @since 7，失焦回调 |
| ADDED | onKeyEvent(callback) | @since 7，按键事件回调 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/03-basic-attributes/design.md` | Baselined |
| ArkTS static bridge (ANI) | `frameworks/core/interfaces/native/implementation/common_method_modifier.cpp` (SetFocusableImpl:3707, SetTabIndexImpl:3809, SetDefaultFocusImpl:3822, SetGroupDefaultFocusImpl:3834, SetFocusOnTouchImpl:3846, SetTabStopImpl:3757, SetFocusBoxImpl:3858, SetNextFocusImpl:3722, SetFocusScopeIdImpl:6080, SetFocusScopePriorityImpl:6092, SetOnFocusImpl:3765, SetOnBlurImpl:3796, SetOnKeyEventImpl:3575) | 已核验 |
| ArkTS static ETS entry | `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/framework/arkts/ArkUIGeneratedNativeModule.ets` (_CommonMethod_setFocusable:312, _CommonMethod_setTabIndex:322, _CommonMethod_setDefaultFocus:324, _CommonMethod_setGroupDefaultFocus:326, _CommonMethod_setFocusOnTouch:328, _CommonMethod_setTabStop:316, _CommonMethod_setFocusBox:330, _CommonMethod_setNextFocus:314, _CommonMethod_setFocusScopeId:568, _CommonMethod_setFocusScopePriority:570, _CommonMethod_setOnFocus:318, _CommonMethod_setOnBlur:320, _CommonMethod_setOnKeyEvent:300) | 已核验 |

---

## 用户故事

### US-1: 设置组件焦点可达性

**作为** 应用开发者,
**我想要** 通过 `.focusable(bool)` / `.tabIndex(number)` / `.tabStop(bool)` / `.focusOnTouch(bool)` 控制组件是否可接收焦点及 Tab 键遍历行为,
**以便** 实现自定义的焦点可达性和 Tab 遍历顺序。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.focusable(true)` THEN FocusHub::focusable_ 设为 true，组件可接收焦点 | 正常 |
| AC-1.2 | WHEN 调用 `.focusable(false)` THEN FocusHub::focusable_ 设为 false，组件不可接收焦点 | 正常 |
| AC-1.3 | WHEN focusable 未设置 THEN 默认值取决于组件类型（FocusType::NODE 可聚焦，FocusType::DISABLE 不可聚焦） | 边界 |
| AC-1.4 | WHEN 调用 `.tabIndex(1)` THEN FocusCallbackEvents::tabIndex_ 设为 1，Tab 遍历时按 tabIndex 升序排列 | 正常 |
| AC-1.5 | WHEN 多个组件设置相同 tabIndex THEN 同一 tabIndex 的组件按组件树顺序遍历 | 边界 |
| AC-1.6 | WHEN tabIndex 为 0 或未设置 THEN 按 DOM 顺序遍历（默认行为） | 正常 |
| AC-1.7 | WHEN 调用 `.tabStop(true)` THEN FocusState::tabStop_ 设为 true，Tab 键停在此节点 | 正常 |
| AC-1.8 | WHEN 调用 `.tabStop(false)` THEN FocusState::tabStop_ 设为 false，Tab 键跳过此节点 | 正常 |
| AC-1.9 | WHEN 调用 `.focusOnTouch(true)` THEN 触摸组件时自动获焦（FocusCallbackEvents::isFocusOnTouch_ = true） | 正常 |
| AC-1.10 | WHEN focusOnTouch 未设置 THEN FocusCallbackEvents::isFocusOnTouch_ 为 std::nullopt，不触发触摸获焦 | 边界 |

### US-2: 设置默认焦点节点

**作为** 应用开发者,
**我想要** 通过 `.defaultFocus(bool)` / `.groupDefaultFocus(bool)` 指定容器或焦点组的默认焦点节点,
**以便** 当容器首次获焦或焦点组切换时自动聚焦到指定组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.defaultFocus(true)` THEN FocusCallbackEvents::isDefaultFocus_ 设为 true，标记为容器默认焦点 | 正常 |
| AC-2.2 | WHEN 容器首次获焦 THEN 焦点自动落到 defaultFocus=true 的子节点 | 正常 |
| AC-2.3 | WHEN 同一容器内多个子节点设置 defaultFocus THEN 最后一个设置生效 | 边界 |
| AC-2.4 | WHEN 调用 `.groupDefaultFocus(true)` THEN FocusCallbackEvents::isDefaultGroupFocus_ 设为 true，标记为焦点组默认焦点 | 正常 |
| AC-2.5 | WHEN 焦点组获焦 THEN 焦点自动落到 groupDefaultFocus=true 的子节点 | 正常 |

### US-3: 设置焦点导航

**作为** 应用开发者,
**我想要** 通过 `.nextFocus()` / `.focusScopeId()` / `.focusScopePriority()` 控制方向键和 Tab 键的焦点跳转路径及焦点域分组,
**以便** 实现自定义焦点导航逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.nextFocus({ forward: "nextId" })` THEN FocusState::nextStep_[FocusIntension::TAB] 设为 "nextId"，Tab 向前跳转到 id="nextId" 的组件 | 正常 |
| AC-3.2 | WHEN 调用 `.nextFocus({ down: "downId" })` THEN 方向键向下跳转到 id="downId" 的组件 | 正常 |
| AC-3.3 | WHEN nextFocus 指定的目标 id 不存在 THEN 焦点跳转失败，焦点停留在当前组件 | 异常 |
| AC-3.4 | WHEN 调用 `.focusScopeId("scopeA")` THEN FocusHub::focusScopeId_ 设为 "scopeA"，FocusHub::isFocusScope_ 设为 true | 正常 |
| AC-3.5 | WHEN 调用 `.focusScopeId("scopeA", { isGroup: true })` THEN FocusHub::isGroup_ 设为 true，焦点域为焦点组 | 正常 |
| AC-3.6 | WHEN 调用 `.focusScopeId("scopeA", false, false)` THEN isGroup=false，FocusHub::arrowKeyStepOut_ 设为 false，方向键不跳出焦点域 | 正常 |
| AC-3.7 | WHEN 调用 `.focusScopePriority("scopeA", FocusPriority.PRIOR)` THEN FocusHub::focusPriority_ 设为 PRIOR (2000)，该域优先获焦 | 正常 |
| AC-3.8 | WHEN FocusPriority 为 AUTO THEN 焦点域按组件树顺序获焦（默认行为） | 边界 |

### US-4: 设置焦点框样式

**作为** 应用开发者,
**我想要** 通过 `.focusBox(FocusBoxStyle)` 自定义焦点框的颜色、宽度和间距,
**以便** 组件获焦时显示符合设计规范的焦点指示框。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.focusBox({ strokeColor: Color.Blue, strokeWidth: 2, margin: 4 })` THEN FocusBox::paintStyle_ 存储 FocusBoxStyle{strokeColor=Blue, strokeWidth=2vp, margin=4vp} | 正常 |
| AC-4.2 | WHEN focusBox 未设置 THEN 使用默认焦点框样式（系统主题色） | 边界 |
| AC-4.3 | WHEN focusBox 的 strokeWidth 为 0 THEN 不绘制焦点框边线 | 边界 |
| AC-4.4 | WHEN 组件获焦 THEN 焦点框按 FocusBoxStyle 绘制在组件外围 | 正常 |

### US-5: 监听焦点事件

**作为** 应用开发者,
**我想要** 通过 `.onFocus()` / `.onBlur()` / `.onKeyEvent()` 监听组件获焦、失焦和按键事件,
**以便** 在焦点状态变化时执行相应的业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 组件获焦 THEN onFocus 回调被触发 | 正常 |
| AC-5.2 | WHEN 组件失焦 THEN onBlur 回调被触发 | 正常 |
| AC-5.3 | WHEN 调用 `.onKeyEvent(callback)` 且组件有焦点 THEN 按键事件通过 callback 回调，返回 true 消费事件、false 不消费 | 正常 |
| AC-5.4 | WHEN onKeyEvent callback 返回 true THEN 按键事件不再向下传播 | 正常 |
| AC-5.5 | WHEN onKeyEvent callback 返回 false THEN 按键事件继续向下传播 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.3 | R-1 | — | UT | FocusHub focusable |
| AC-1.4~1.6 | R-2 | — | UT | tabIndex 遍历 |
| AC-1.7~1.8 | R-3 | — | UT | tabStop |
| AC-1.9~1.10 | R-4 | — | UT | focusOnTouch |
| AC-2.1~2.3 | R-5 | — | UT | defaultFocus |
| AC-2.4~2.5 | R-6 | — | UT | groupDefaultFocus |
| AC-3.1~3.3 | R-7 | — | UT | nextFocus 导航 |
| AC-3.4~3.8 | R-8 | — | UT | focusScopeId/Priority |
| AC-4.1~4.4 | R-9 | — | UT | focusBox 样式 |
| AC-5.1~5.2 | R-10 | — | UT | onFocus/onBlur |
| AC-5.3~5.5 | R-11 | — | UT | onKeyEvent 消费 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | focusable 设置焦点可达性 | FocusHub::focusable_ 控制组件是否可接收焦点；true 可获焦，false 不可获焦（动态前端: `js_view_abstract.cpp JsFocusable`; 静态前端: `ArkUIGeneratedNativeModule.ets:312 _CommonMethod_setFocusable` → `common_method_modifier.cpp:3707 SetFocusableImpl`; C-API: `node_common_modifier.cpp NODE_FOCUSABLE`） | FocusHub::focusable_ 构造函数默认为 false；各组件 Pattern 通过 FocusPattern 覆盖默认值（NODE 类型组件默认可聚焦，DISABLE 类型默认不可聚焦） | AC-1.1~1.3 |
| R-2 | 行为 | tabIndex 设置 Tab 遍历顺序 | Tab 键按 tabIndex 升序遍历可聚焦组件；0 或未设置按 DOM 顺序（动态前端: `js_view_abstract.cpp JsTabIndex`; 静态前端: `ArkUIGeneratedNativeModule.ets:322 _CommonMethod_setTabIndex` → `common_method_modifier.cpp:3809 SetTabIndexImpl`; C-API: 无独立 NDK 枚举） | 同 tabIndex 按 DOM 顺序；负数 tabIndex 不参与 Tab 遍历 | AC-1.4~1.6 |
| R-3 | 行为 | tabStop 控制 Tab 停留 | tabStop=true 时 Tab 键停在此节点；tabStop=false 时 Tab 键跳过 | 默认 false | AC-1.7~1.8 |
| R-4 | 行为 | focusOnTouch 触摸获焦 | focusOnTouch=true 时触摸组件自动获焦；未设置时不触发 | FocusCallbackEvents::isFocusOnTouch_ 为 std::optional<bool>，默认 nullopt | AC-1.9~1.10 |
| R-5 | 行为 | defaultFocus 容器默认焦点 | 容器首次获焦时焦点落到 defaultFocus=true 的子节点 | 同容器内多个 defaultFocus 只最后一个生效 | AC-2.1~2.3 |
| R-6 | 行为 | groupDefaultFocus 焦点组默认焦点 | 焦点组获焦时焦点落到 groupDefaultFocus=true 的子节点 | 与 defaultFocus 作用范围不同：groupDefaultFocus 在焦点组切换时生效 | AC-2.4~2.5 |
| R-7 | 行为 | nextFocus 方向键焦点跳转 | nextStep_ 为 map&lt;int32_t, variant&lt;WeakPtr&lt;AceType&gt;, string&gt;&gt;，按 FocusIntension 键值映射到目标组件 id 或节点引用，方向键按下时跳转到指定组件（动态前端: `js_view_abstract.cpp JsNextFocus`; 静态前端: `ArkUIGeneratedNativeModule.ets:314 _CommonMethod_setNextFocus` → `common_method_modifier.cpp:3722 SetNextFocusImpl`; C-API: `node_common_modifier.cpp NODE_NEXT_FOCUS`） | 目标 id 不存在时跳转失败，焦点停留；FocusIntension 值：TAB/SHIFT_TAB/LEFT/UP/RIGHT/DOWN/HOME/END | AC-3.1~3.3 |
| R-8 | 行为 | focusScopeId/focusScopePriority 焦点域 | focusScopeId 创建焦点域（isFocusScope_=true）；isGroup 标记焦点组；arrowKeyStepOut 控制方向键是否跳出域；focusScopePriority 设置域优先级（AUTO/PRIOR/PREVIOUS）（动态前端: `js_view_abstract.cpp JsFocusScopeId/JsFocusScopePriority`; 静态前端: `ArkUIGeneratedNativeModule.ets:568/570 _CommonMethod_setFocusScopeId/_CommonMethod_setFocusScopePriority` → `common_method_modifier.cpp:6080/6092`; C-API: `node_common_modifier.cpp NODE_FOCUS_SCOPE_ID/NODE_FOCUS_SCOPE_PRIORITY`） | FocusPriority::AUTO=0, PRIOR=2000, PREVIOUS=3000；arrowKeyStepOut 默认 true | AC-3.4~3.8 |
| R-9 | 行为 | focusBox 焦点框样式 | FocusBoxStyle{strokeColor?, strokeWidth?, margin?} 存储在 FocusBox::paintStyle_（std::optional&lt;FocusBoxStyle&gt;），获焦时绘制焦点框；未设置时 paintStyle_ 为 nullopt，使用系统默认样式 | strokeWidth=0 不绘制；未设置使用系统默认样式 | AC-4.1~4.4 |
| R-10 | 行为 | onFocus/onBlur 焦点事件 | 获焦触发 onFocusCallback_，失焦触发 onBlurCallback_ | 两者为独立回调，不互斥 | AC-5.1~5.2 |
| R-11 | 行为 | onKeyEvent 按键事件消费 | callback 接收 KeyEvent 参数，返回 true 消费事件（停止传播），返回 false 不消费（继续传播）（动态前端: `js_view_abstract.cpp JsOnKeyEvent`; 静态前端: `ArkUIGeneratedNativeModule.ets:300 _CommonMethod_setOnKeyEvent` → `common_method_modifier.cpp:3575 SetOnKeyEventImpl`; C-API: `node_common_modifier.cpp NODE_ON_KEY_EVENT`） | 消费链：onKeyPreIme → onKeyEvent → 系统处理（但 onKeyPreIme 不在本规格范围） | AC-5.3~5.5 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | R-1, AC-1.1~1.3 | UT | FocusHub focusable 开关 |
| VM-2 | R-2, AC-1.4~1.6 | UT | tabIndex 遍历排序 |
| VM-3 | R-3, AC-1.7~1.8 | UT | tabStop 停留/跳过 |
| VM-4 | R-4, AC-1.9~1.10 | UT | focusOnTouch 触摸获焦 |
| VM-5 | R-5, R-6, AC-2.1~2.5 | UT | defaultFocus/groupDefaultFocus |
| VM-6 | R-7, AC-3.1~3.3 | UT | nextFocus 方向键跳转 |
| VM-7 | R-8, AC-3.4~3.8 | UT | focusScopeId/Priority 焦点域 |
| VM-8 | R-9, AC-4.1~4.4 | UT | focusBox 样式绘制 |
| VM-9 | R-10, AC-5.1~5.2 | UT | onFocus/onBlur 回调 |
| VM-10 | R-11, AC-5.3~5.5 | UT | onKeyEvent 消费/传播 |
| VM-11 | 全量 | XTS/集成 | 端到端焦点属性行为正确 |

---

## API 变更分析

### 新增 API

| API 签名 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| `focusable(value: boolean): T` | Public | bool | T | — | 焦点可达性 | AC-1.1~1.3 |
| `tabIndex(value: number): T` | Public | int32_t | T | — | Tab 遍历顺序 | AC-1.4~1.6 |
| `tabStop(value: boolean): T` | Public | bool | T | — | Tab 停留控制 | AC-1.7~1.8 |
| `focusOnTouch(value: boolean): T` | Public | bool | T | — | 触摸获焦 | AC-1.9~1.10 |
| `defaultFocus(value: boolean): T` | Public | bool | T | — | 容器默认焦点 | AC-2.1~2.3 |
| `groupDefaultFocus(value: boolean): T` | Public | bool | T | — | 焦点组默认焦点 | AC-2.4~2.5 |
| `nextFocus(value: { forward?, backward?, up?, down?, left?, right? }): T` | Public | string map | T | — | 方向键焦点跳转 | AC-3.1~3.3 |
| `focusScopeId(value: string, options?: { isGroup?, arrowKeyStepOut? }): T` | Public | string+bool+bool | T | — | 焦点域标识 | AC-3.4~3.8 |
| `focusScopePriority(value: string, priority?: FocusPriority): T` | Public | string+FocusPriority | T | — | 焦点域优先级 | AC-3.7~3.8 |
| `focusBox(value: FocusBoxStyle): T` | Public | FocusBoxStyle{strokeColor?, strokeWidth?, margin?} | T | — | 焦点框样式 | AC-4.1~4.4 |
| `onFocus(callback: () => void): T` | Public | callback | T | — | 获焦回调 | AC-5.1 |
| `onBlur(callback: () => void): T` | Public | callback | T | — | 失焦回调 | AC-5.2 |
| `onKeyEvent(callback: (KeyEvent) => boolean): T` | Public | callback | T | — | 按键事件回调 | AC-5.3~5.5 |

> **Native C-API 属性枚举**：

| 属性枚举 | 值格式 | 功能 | @since |
|----------|--------|------|--------|
| `NODE_FOCUSABLE` | `.value[0].i32` (1 或 0) | 焦点可达性 | 12 |
| `NODE_DEFAULT_FOCUS` | `.value[0].i32` (1 或 0) | 容器默认焦点 | 12 |
| `NODE_FOCUS_ON_TOUCH` | `.value[0].i32` (1 或 0) | 触摸获焦 | 12 |
| `NODE_FOCUS_BOX` | `.value[0].f32`(margin), `.value[1].f32`(strokeWidth), `.value[2].u32`(strokeColor) | 焦点框样式 | 12 |
| `NODE_NEXT_FOCUS` | `.value[0].i32`(ArkUI_FocusMove 方向), `.object`(目标节点) | 方向键焦点跳转 | — |
| `NODE_FOCUS_SCOPE_ID` | `.string`(scopeId), `.value[0].i32`(isGroup), `.value[1].i32`(arrowKeyStepOut) | 焦点域标识 | 23 |
| `NODE_FOCUS_SCOPE_PRIORITY` | `.string`(scopeId), `.value[0].i32`(ArkUI_FocusPriority) | 焦点域优先级 | 23 |
| `NODE_ON_FOCUS` | event callback | 获焦事件 | — |
| `NODE_ON_BLUR` | event callback | 失焦事件 | — |
| `NODE_ON_KEY_EVENT` | event callback | 按键事件 | 14 |

> 无 C-API 对应的属性：tabIndex、groupDefaultFocus
> tabStop 有 C-API 对应：NODE_TAB_STOP (=98)，`.value[0].i32` (1 或 0)

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `FocusBoxStyle` | `{ strokeColor?: Color, strokeWidth?: CalcDimension, margin?: CalcDimension }` | focus_box.h:67 |
| `FocusPriority` | AUTO=0, PRIOR=2000, PREVIOUS=3000 | focus_hub.h:85 |
| `ArkUI_FocusPriority` | AUTO=0, PRIOR=2000, PREVIOUS=3000 | native_type.h:1344 |
| `ArkUI_FocusMove` | FORWARD/BACKWARD/UP/DOWN/LEFT/RIGHT | native_type.h:1687 |

### 变更/废弃 API

N/A，已有能力补录，API 行为无变化。

---

## 接口规格

### 接口定义

**focusable**

| 属性 | 值 |
|------|-----|
| 函数签名 | `focusable(value: boolean): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | — | true 可获焦，false 不可获焦 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | focusable(true) | FocusHub::focusable_=true，组件可接收焦点 | AC-1.1 |
| 2 | focusable(false) | FocusHub::focusable_=false，组件不可接收焦点 | AC-1.2 |
| 3 | focusable 未设置 | 按 FocusType 默认值：NODE 可聚焦，DISABLE 不可 | AC-1.3 |

---

**tabIndex**

| 属性 | 值 |
|------|-----|
| 函数签名 | `tabIndex(value: number): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.4~1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | — | int32_t；0 或未设置按 DOM 顺序；升序排列 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | tabIndex(1) | Tab 遍历按升序排列（仅 tabIndex>0 参与排序） | AC-1.4 |
| 2 | 多个组件 tabIndex 相同 | 按 DOM 顺序遍历 | AC-1.5 |
| 3 | tabIndex=0 或未设置 | 按 DOM 顺序（默认） | AC-1.6 |

---

**defaultFocus**

| 属性 | 值 |
|------|-----|
| 函数签名 | `defaultFocus(value: boolean): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | — | true 标记为容器默认焦点 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | defaultFocus(true) | 容器首次获焦时焦点落到此节点 | AC-2.1, AC-2.2 |
| 2 | 多个子节点 defaultFocus(true) | 最后一个生效 | AC-2.3 |

---

**groupDefaultFocus**

| 属性 | 值 |
|------|-----|
| 函数签名 | `groupDefaultFocus(value: boolean): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.4~2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | — | true 标记为焦点组默认焦点 |

---

**focusOnTouch**

| 属性 | 值 |
|------|-----|
| 函数签名 | `focusOnTouch(value: boolean): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.9~1.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | — | true 触摸时自动获焦 |

---

**tabStop**

| 属性 | 值 |
|------|-----|
| 函数签名 | `tabStop(value: boolean): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.7~1.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | false | true Tab 停留，false Tab 跳过 |

---

**nextFocus**

| 属性 | 值 |
|------|-----|
| 函数签名 | `nextFocus(value: { forward?: string, backward?: string, up?: string, down?: string, left?: string, right?: string }): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.forward | string | 否 | — | Tab 向前目标组件 id |
| value.backward | string | 否 | — | Tab 向后目标组件 id |
| value.up | string | 否 | — | 上方向键目标组件 id |
| value.down | string | 否 | — | 下方向键目标组件 id |
| value.left | string | 否 | — | 左方向键目标组件 id |
| value.right | string | 否 | — | 右方向键目标组件 id |

---

**focusBox**

| 属性 | 值 |
|------|-----|
| 函数签名 | `focusBox(value: FocusBoxStyle): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.strokeColor | Color | 否 | 系统默认色 | 焦点框边线颜色 |
| value.strokeWidth | CalcDimension | 否 | 系统默认宽度 | 边线宽度；0 不绘制 |
| value.margin | CalcDimension | 否 | 系统默认间距 | 焦点框与组件边缘间距 |

---

**focusScopeId**

| 属性 | 值 |
|------|-----|
| 函数签名 | `focusScopeId(value: string, isGroup?: boolean, arrowStepOut?: boolean): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.4~3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | — | 焦点域标识 |
| isGroup | boolean | 否 | false | 是否为焦点组 |
| arrowStepOut | boolean | 否 | true | 方向键是否可跳出焦点域（底层字段 arrowKeyStepOut_） |

---

**focusScopePriority**

| 属性 | 值 |
|------|-----|
| 函数签名 | `focusScopePriority(value: string, priority?: FocusPriority): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.7~3.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | — | 焦点域标识 |
| priority | FocusPriority | 否 | AUTO | AUTO=0/PRIOR=2000/PREVIOUS=3000 |

---

**onFocus**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onFocus(callback: () => void): T` |
| 返回值 | `T` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

---

**onBlur**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onBlur(callback: () => void): T` |
| 返回值 | `T` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.2 |

---

**onKeyEvent**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onKeyEvent(callback: (KeyEvent) => boolean): T` |
| 返回值 | `T` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.3~5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (KeyEvent) => boolean | 是 | — | 返回 true 消费事件，false 不消费 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:**
  - focusable/tabIndex/defaultFocus/groupDefaultFocus/focusBox/onFocus/onBlur/onKeyEvent: @since 7
  - focusOnTouch: @since 8
  - tabStop/nextFocus: @since 9
  - onKeyEvent C-API (NODE_ON_KEY_EVENT): @since 14
  - focusScopeId/focusScopePriority (C-API): @since 23

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| FocusHub 焦点可达性 | FocusHub::focusable_ 为 bool 单值字段，默认值取决于组件 FocusType | AC-1.1~1.3 |
| FocusType 决定默认焦点行为 | FocusType::NODE=可聚焦，DISABLE=不可聚焦，SCOPE=容器可聚焦 | AC-1.3 |
| nextStep_ 映射焦点跳转 | FocusState::nextStep_ 为 map<FocusIntension, string>，支持 6 个方向 | AC-3.1~3.3 |
| FocusPriority 枚举固定 | AUTO=0, PRIOR=2000, PREVIOUS=3000，不可扩展 | AC-3.7~3.8 |
| onKeyEvent 消费链 | callback 返回 true 消费事件停止传播，false 不消费继续传播 | AC-5.3~5.5 |
| 双前端汇合点 | 动态前端 (JSI/NAPI `js_view_abstract.cpp`) 和静态前端 (ANI `common_method_modifier.cpp`) 在 `ViewAbstract::SetXXX` 汇合；focusable/tabIndex/tabStop/defaultFocus/groupDefaultFocus/focusOnTouch/focusBox/nextFocus/focusScopeId/focusScopePriority/onFocus/onBlur/onKeyEvent 两路径行为一致 | 全部 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|---------|------|
| 性能 | focusable/focusScopeId 设置不引起额外帧延迟 | UT | — |
| 内存 | FocusHub 字段为 bool/int32_t/string，无额外内存池 | 代码检查 | focus_hub.h |
| 可测试性 | focusable/tabIndex/nextFocus 可独立验证 | UT | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | focusOnTouch 在触屏设备上触发 | 触摸获焦 | 交互测试 | — |
| 平板 | focusOnTouch 在触屏设备上触发；Tab 键需外接键盘 | 外接键盘支持 | 交互测试 | — |
| 折叠屏 | 行为与手机一致 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|---------|
| 无障碍 | 是 | focusable 控制焦点可达性影响无障碍导航；focusBox 焦点框增强焦点可见性 | AC-1.1, AC-4.1 |
| 大字体 | 否 | 焦点属性不受大字体影响 | — |
| 深色模式 | 是 | focusBox strokeColor 需适配深色模式 | AC-4.1 |
| 多窗口/分屏 | 否 | 焦点行为不受多窗口影响 | — |
| 多用户 | 否 | 焦点行为不受多用户影响 | — |
| 版本升级 | 是 | API 9 新增 tabStop/nextFocus；API 23 新增 focusScopeId/focusScopePriority | — |
| 生态兼容 | 是 | C-API NODE_FOCUSABLE 与 ArkTS focusable 行为一致 | — |

---

## 风险 / Risks

| 风险ID | 类型 | 描述 | 影响AC | 缓解策略 |
|--------|------|------|--------|----------|
| RK-1 | 认知 | defaultFocus 与 groupDefaultFocus 作用范围不同，开发者可能混淆 | AC-2.1~2.5 | SDK 文档应明确标注两者差异 |
| RK-2 | 版本 | focusScopeId/focusScopePriority 仅 API 23+ C-API 支持，早期版本无法使用 | AC-3.4~3.8 | @since 版本守护 |
| RK-3 | 认知 | tabIndex 相同值的遍历顺序为 DOM 顺序，开发者可能误认为随机 | AC-1.5 | SDK 文档应明确排序规则 |
| RK-4 | 边界 | nextFocus 目标 id 不存在时跳转失败但不报错 | AC-3.3 | 考虑增加日志警告 |

---

## 行为场景（可选，Gherkin）

Feature: 焦点属性
  作为 应用开发者
  我想要 控制组件的焦点可达性、导航和事件
  以便 实现自定义焦点交互逻辑

  Scenario: focusable 控制焦点可达性
    Given 组件设置了 focusable(true)
    When 用户通过 Tab 键或方向键导航
    Then 组件可接收焦点

  Scenario: defaultFocus 容器默认焦点
    Given 容器内子组件 A 设置了 defaultFocus(true)
    When 容器首次获焦
    Then 焦点自动落到子组件 A

  Scenario: nextFocus 方向键跳转
    Given 组件 X 设置了 nextFocus({ down: "componentY" })
    When 用户按下方向键↓
    Then 焦点从 X 跳转到 id="componentY" 的组件

  Scenario: onKeyEvent 消费按键事件
    Given 组件设置了 onKeyEvent((e) => e.keyCode === KeyCode.ENTER)
    When 用户按下 Enter 键且组件有焦点
    Then callback 返回 true，Enter 事件被消费不再传播

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（焦点可达性/导航/样式/事件均已覆盖）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "FocusHub 焦点可达性与默认焦点机制 (focus_hub.h:855, focus_hub.cpp)"
  - repo: "openharmony/ace_engine"
    query: "FocusCallbackEvents tabIndex/focusOnTouch/defaultFocus/groupDefaultFocus 存储 (focus_hub.h:542-574)"
  - repo: "openharmony/ace_engine"
    query: "FocusState nextFocus 方向键跳转 (focus_state.h:68-84)"
  - repo: "openharmony/ace_engine"
    query: "FocusBox 焦点框样式绘制 (focus_box.h:30-65)"
  - repo: "openharmony/ace_engine"
    query: "focusScopeId/focusScopePriority 焦点域 (focus_hub.h:667-881)"
  - repo: "openharmony/ace_engine"
    query: "NODE_FOCUSABLE/NODE_DEFAULT_FOCUS/NODE_FOCUS_BOX C-API (native_node.h:911-1969)"
```

**关键文档：**

- FocusHub: `frameworks/core/components_ng/event/focus_hub.h`
- FocusCallbackEvents: `frameworks/core/components_ng/event/focus_hub.h:542-574`
- FocusState: `frameworks/core/components_ng/event/focus_state.h`
- FocusBox: `frameworks/core/components_ng/event/focus_box.h`
- ViewAbstract focus 属性: `frameworks/core/components_ng/base/view_abstract.h:467-483`
- JS Bridge: `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:9514-13504`
- C-API: `interfaces/native/native_node.h`
- C-API style modifier: `interfaces/native/node/style_modifier.cpp`
