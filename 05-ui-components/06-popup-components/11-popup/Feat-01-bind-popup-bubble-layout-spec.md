# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | bindPopup 属性绑定与气泡布局（PopupOptions / CustomPopupOptions + BubblePattern + 动画 / 布局 / 交互 / 样式 / C API） |
| 特性编号 | Func-05-06-11-Feat-01 |
| FuncID | 05-06-11 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 7 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | bindPopup(show, popup) 属性 | @since 7，声明式气泡属性 |
| ADDED | PopupOptions（message / placementOnTop / primaryButton / secondaryButton / onStateChange） | @since 7 |
| ADDED | CustomPopupOptions（builder） | @since 8 |
| ADDED | arrowOffset 属性 | @since 9 |
| ADDED | showInSubWindow 属性 | @since 9 |
| MODIFIED | placementOnTop | @since 10 标记废弃，建议使用 placement |
| ADDED | placement / mask / messageOptions / targetSpace / enableArrow / offset 属性 | @since 10 |
| ADDED | popupColor / autoCancel / width / arrowPointPosition / arrowWidth / arrowHeight / radius / shadow / backgroundBlurStyle / focusable 属性 | @since 11 |
| ADDED | transition 属性 | @since 12 |
| MODIFIED | focusable 默认值变更为 false | @since 12 |
| ADDED | C API: bubble_modifier（动态模块加载） | 组件化 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/06-popup-components/11-popup/design.md`
- **KB 路由**: `docs/kb/components/overlay/bind_popup.md`
- **SDK 类型定义**:
  - Dynamic (属性): `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础气泡显示（PopupOptions）

**角色**: 应用开发者
**期望**: 我想要通过 bindPopup 属性为组件绑定内置消息气泡
**价值**: 以便在组件附近显示提示信息

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `bindPopup(true, { message: 'Hello' })` THEN 创建 Bubble FrameNode 并挂载到 overlay 层，显示消息气泡（`overlay_manager.cpp:944, 1253`） | 正常 |
| AC-1.2 | WHEN bindPopup show=false THEN 关闭已显示的气泡（`overlay_manager.cpp:1367`） | 正常 |
| AC-1.3 | WHEN 设置 `placement: Placement.BOTTOM` THEN 气泡显示在宿主节点底部（默认值 Bottom，`bubble_layout_algorithm.cpp:143`） | 正常 |
| AC-1.4 | WHEN 未设置 enableArrow THEN 默认显示箭头（enableArrow=true，SDK 默认值） | 正常 |
| AC-1.5 | WHEN 设置 `enableArrow: false` THEN 隐藏箭头（`bubble_layout_property.h:79`） | 正常 |

### US-2: 自定义气泡（CustomPopupOptions）

**角色**: 应用开发者
**期望**: 我想要使用自定义 Builder 内容作为气泡
**价值**: 以便实现超出标准消息气泡的定制化需求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `bindPopup(true, { builder: this.customBuilder })` THEN 使用 CustomBuilder 创建气泡内容（`bubble_view.cpp:462`） | 正常 |
| AC-2.2 | WHEN CustomPopupOptions 设置 THEN `UseCustom=true` 标记到 BubbleLayoutProperty（`bubble_layout_property.h:80`） | 正常 |
| AC-2.3 | WHEN 使用 CustomPopupOptions THEN 不创建默认 message 和 button 子节点，仅挂载 Builder 内容 | 正常 |

### US-3: 气泡动画

**角色**: 终端用户
**期望**: 我想要气泡显示/隐藏时有平滑的过渡动画
**价值**: 以便获得自然的视觉过渡体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 气泡进入 THEN 使用 250ms 动画，FRICTION 曲线 offset 从 8px 到 0，SHARP 曲线 alpha 0→1（`bubble_pattern.cpp:42, 645, 663`） | 正常 |
| AC-3.2 | WHEN 气泡退出 THEN 使用 100ms 动画，FRICTION 曲线 offset 从 0 到 8px，SHARP 曲线 alpha 1→0（`bubble_pattern.cpp:43, 724, 745`） | 正常 |
| AC-3.3 | WHEN 气泡进入 THEN TransitionStatus 从 INVISIABLE 转为 ENTERING，动画完成后转为 NORMAL（`bubble_pattern.h:42-46`） | 正常 |
| AC-3.4 | WHEN 气泡退出 THEN TransitionStatus 从 NORMAL 转为 EXITING，动画完成后转为 INVISIABLE（`bubble_pattern.h:42-46`） | 正常 |
| AC-3.5 | WHEN 设置 `transition` 属性（@since 12） THEN 使用自定义过渡动画替代默认进入/退出动画 | 正常 |

### US-4: 12 方位布局与避让

**角色**: 应用开发者
**期望**: 我想要控制气泡相对于宿主节点的显示方位
**价值**: 以便在不同布局场景下选择最佳显示位置

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 placement 为 TOP / TOP_LEFT / TOP_RIGHT THEN 气泡显示在宿主节点上方，通过 placementFuncMap_ 映射对应位置计算函数（`bubble_layout_algorithm.cpp:279-281`） | 正常 |
| AC-4.2 | WHEN 设置 placement 为 BOTTOM / BOTTOM_LEFT / BOTTOM_RIGHT THEN 气泡显示在宿主节点下方（`:282-284`） | 正常 |
| AC-4.3 | WHEN 设置 placement 为 LEFT / LEFT_TOP / LEFT_BOTTOM THEN 气泡显示在宿主节点左侧（`:285-287`） | 正常 |
| AC-4.4 | WHEN 设置 placement 为 RIGHT / RIGHT_TOP / RIGHT_BOTTOM THEN 气泡显示在宿主节点右侧（`:288-290`） | 正常 |
| AC-4.5 | WHEN 气泡超出屏幕边界 THEN FitToScreenNew 自动调整位置确保气泡可见 | 正常 |
| AC-4.6 | WHEN 气泡与目标节点重叠 THEN AvoidToTarget* 策略避免遮挡目标节点 | 正常 |
| AC-4.7 | WHEN 设置 `arrowOffset` THEN 箭头沿气泡边偏移指定距离（@since 9） | 正常 |
| AC-4.8 | WHEN 设置 `arrowPointPosition` THEN 箭头位置按指定位置对齐（@since 11） | 正常 |
| AC-4.9 | WHEN 设置 `arrowWidth: 20vp, arrowHeight: 10vp` THEN 箭头宽度和高度按指定值渲染（默认 16vp / 8vp，@since 11） | 正常 |

### US-5: 子窗口显示

**角色**: 应用开发者
**期望**: 我想要控制气泡是否在子窗口中显示
**价值**: 以便避免气泡被宿主节点的父容器裁剪

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 设置 `showInSubWindow: true`（默认）THEN 气泡在子窗口中创建和显示（`bubble_layout_property.h:83`） | 正常 |
| AC-5.2 | WHEN 设置 `showInSubWindow: false` THEN 气泡在当前 overlay 层显示，不创建子窗口 | 正常 |
| AC-5.3 | WHEN showInSubWindow=true 且气泡关闭 THEN 子窗口正确销毁，无资源泄漏 | 异常 |

### US-6: 交互行为

**角色**: 终端用户
**期望**: 我想要通过点击遮罩或按钮关闭气泡
**价值**: 以便获得符合预期的交互反馈

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `autoCancel: true`（默认，@since 11）且点击气泡外部遮罩区域 THEN 气泡关闭（`bubble_render_property.h:68`） | 正常 |
| AC-6.2 | WHEN `autoCancel: false` 且点击遮罩区域 THEN 气泡不关闭 | 正常 |
| AC-6.3 | WHEN 点击 primaryButton THEN 执行 action 回调并关闭气泡（`bubble_view.cpp:1091`） | 正常 |
| AC-6.4 | WHEN 点击 secondaryButton THEN 执行 action 回调并关闭气泡 | 正常 |
| AC-6.5 | WHEN 气泡关闭 THEN onStateChange 回调触发，携带 isVisible=false 和 reason（DismissReason） | 正常 |
| AC-6.6 | WHEN 设置 `mask: false` THEN 不显示遮罩 | 正常 |
| AC-6.7 | WHEN 设置 `mask: ResourceColor` THEN 遮罩使用指定颜色 | 正常 |

### US-7: 焦点管理

**角色**: 应用开发者
**期望**: 我想要控制气泡是否可获取焦点
**价值**: 以便支持键盘导航和辅助功能场景

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `focusable: false`（默认 @since 12+）THEN 气泡不获取键盘焦点 | 正常 |
| AC-7.2 | WHEN `focusable: true` THEN 气泡可获取键盘焦点，支持 Tab 导航 | 正常 |
| AC-7.3 | WHEN BubblePattern 继承 FocusView THEN 焦点管理通过 FocusView 接口实现 | 正常 |

### US-8: 样式属性

**角色**: 应用开发者
**期望**: 我想要自定义气泡的颜色、圆角、阴影和模糊效果
**价值**: 以便匹配应用的设计语言

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 设置 `popupColor: Color.Red` THEN 气泡背景色为红色（`bubble_render_property.h:70`） | 正常 |
| AC-8.2 | WHEN 未设置 popupColor THEN 默认 TRANSPARENT + COMPONENT_ULTRA_THICK 模糊 | 正常 |
| AC-8.3 | WHEN 设置 `radius: 16vp` THEN 气泡圆角半径为 16vp（默认 20vp，@since 11） | 正常 |
| AC-8.4 | WHEN 设置 `shadow: ShadowStyle.OUTER_DEFAULT_MD` THEN 气泡阴影使用指定样式（@since 11） | 正常 |
| AC-8.5 | WHEN 设置 `backgroundBlurStyle: BlurStyle.COMPONENT_ULTRA_THICK` THEN 气泡背景使用指定模糊效果（@since 11） | 正常 |
| AC-8.6 | WHEN 设置 `targetSpace: 10vp` THEN 气泡与宿主节点间距为 10vp（默认 8vp，@since 10，`bubble_layout_property.h:85`） | 正常 |
| AC-8.7 | WHEN 设置 `width: 200vp` THEN 气泡宽度为 200vp（@since 11） | 正常 |
| AC-8.8 | WHEN 设置 `offset: { dx: 10, dy: 20 }` THEN 气泡在 placement 基础上叠加偏移（@since 10） | 正常 |

### US-9: C API 与组件化

**角色**: NDK 开发者
**期望**: 我想要通过 C API 设置气泡属性
**价值**: 以便在 Native 层集成气泡功能

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 通过 C API 访问 bubble_modifier THEN 通过 DynamicModuleHelper 转发到 libarkui_bubble.z.so 动态模块（`bubble_modifier.cpp`） | 正常 |
| AC-9.2 | WHEN BubbleDynamicModule 注册 THEN libarkui_bubble.z.so 作为独立 SO 按需加载 | 正常 |
| AC-9.3 | WHEN 使用 inner_modifier THEN 通过 bubble_inner_modifier.cpp 委托属性设置 | 正常 |
| AC-9.4 | WHEN C API 设置 Bubble 属性 THEN 不暴露独立 ARKUI_NODE_* 枚举，使用 modifier-based 方式 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1, R-2, R-3 | TASK-BIND-POPUP-01 | UT | `test/unittest/core/pattern/bubble/` |
| AC-2.1 ~ AC-2.3 | R-4 | TASK-BIND-POPUP-01 | UT | BubbleView 自定义气泡测试 |
| AC-3.1 ~ AC-3.5 | R-5, R-6, R-7, R-20 | TASK-BIND-POPUP-01 | UT + 手工 | 动画和状态机测试 |
| AC-4.1 ~ AC-4.9 | R-8, R-9, R-10, R-19 | TASK-BIND-POPUP-01 | UT | 12 方位和避让测试 |
| AC-5.1 ~ AC-5.3 | R-11, R-18 | TASK-BIND-POPUP-01 | UT | 子窗口测试 |
| AC-6.1 ~ AC-6.7 | R-12, R-13 | TASK-BIND-POPUP-01 | UT | autoCancel 和交互测试 |
| AC-7.1 ~ AC-7.3 | R-14 | TASK-BIND-POPUP-01 | UT | 焦点管理测试 |
| AC-8.1 ~ AC-8.8 | R-15, R-16, R-19 | TASK-BIND-POPUP-01 | UT | 样式属性测试 |
| AC-9.1 ~ AC-9.4 | R-17 | TASK-BIND-POPUP-01 | C API UT | bubble_modifier 测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `overlay_manager.cpp:944, 1253` | ShowPopup 创建 Bubble FrameNode，popupMap_[targetId] = popupInfo，挂载到 overlay 层 | — | AC-1.1 |
| R-2 | 行为 | `overlay_manager.cpp:1367` | show=false 时 HidePopup 执行退出动画并清理 popupMap_ | — | AC-1.2 |
| R-3 | 行为 | `bubble_layout_algorithm.cpp:143` | placement 默认 Placement::Bottom | 12 方位 + NONE | AC-1.3 |
| R-4 | 行为 | `bubble_view.cpp:462, bubble_layout_property.h:80` | CustomPopupOptions 设置 UseCustom=true，使用 CreateCustomBubbleNode 创建气泡 | — | AC-2.1 ~ AC-2.3 |
| R-5 | 行为 | `bubble_pattern.cpp:42, 645, 663` | 进入动画 250ms，FRICTION 曲线 offset 8px→0，SHARP 曲线 alpha 0→1 | ENTRY_ANIMATION_DURATION=250 | AC-3.1 |
| R-6 | 行为 | `bubble_pattern.cpp:43, 724, 745` | 退出动画 100ms，FRICTION 曲线 offset 0→8px，SHARP 曲线 alpha 1→0 | EXIT_ANIMATION_DURATION=100 | AC-3.2 |
| R-7 | 行为 | `bubble_pattern.h:42-46` | TransitionStatus 状态机：INVISIABLE→ENTERING→NORMAL→EXITING→INVISIABLE | — | AC-3.3, AC-3.4 |
| R-8 | 行为 | `bubble_layout_algorithm.cpp:279-290` | placementFuncMap_ 映射 12 种 Placement 到位置计算函数 | 12 方位 | AC-4.1 ~ AC-4.4 |
| R-9 | 行为 | `bubble_layout_algorithm.cpp` FitToScreenNew | 气泡超出屏幕时自动调整位置 | — | AC-4.5 |
| R-10 | 行为 | `bubble_layout_algorithm.cpp` AvoidToTarget* | 气泡避免遮挡目标节点 | — | AC-4.6 |
| R-11 | 行为 | `bubble_layout_property.h:83` | showInSubWindow=true 时在子窗口创建气泡 | 默认 true | AC-5.1, AC-5.2 |
| R-12 | 行为 | `bubble_render_property.h:68` | autoCancel=true 时点击遮罩区域关闭气泡 | 默认 true (@since 11) | AC-6.1, AC-6.2 |
| R-13 | 行为 | `bubble_view.cpp:1091` | primaryButton/secondaryButton 点击执行 action 并关闭气泡 | — | AC-6.3, AC-6.4 |
| R-14 | 行为 | `bubble_pattern.cpp` FocusView 继承 | focusable=true 时气泡可获取键盘焦点 | 默认 false (@since 12) | AC-7.1 ~ AC-7.3 |
| R-15 | 行为 | `bubble_render_property.h:70` | popupColor 设置气泡背景色，默认 TRANSPARENT + COMPONENT_ULTRA_THICK | — | AC-8.1, AC-8.2 |
| R-16 | 行为 | `bubble_layout_property.h:85` | targetSpace 设置气泡与宿主间距，默认 8vp | ≥ 0 | AC-8.6 |
| R-17 | 行为 | `bubble_modifier.cpp` | C API 通过 DynamicModuleHelper 转发到 libarkui_bubble.z.so 动态模块 | 无独立 NODE 枚举 | AC-9.1 ~ AC-9.4 |
| R-18 | 异常 | `overlay_manager.cpp` | showInSubWindow=true 且气泡关闭时，子窗口正确销毁，无资源泄漏 | — | AC-5.3 |
| R-19 | 边界 | SDK common.d.ts | arrowWidth 默认 16vp，arrowHeight 默认 8vp，radius 默认 20vp | ≥ 0 | AC-4.9, AC-8.3 |
| R-20 | 边界 | `bubble_pattern.cpp:44` | InvisibleOffset = 8.0_px，进入/退出动画的位移偏移 | — | AC-3.1, AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | PopupOptions 基础属性和默认值 |
| VM-2 | AC-2.1 ~ AC-2.3 | UT | CustomPopupOptions 和 Builder 创建 |
| VM-3 | AC-3.1 ~ AC-3.5 | UT + 手工 | 进入/退出动画参数和状态机 |
| VM-4 | AC-4.1 ~ AC-4.9 | UT | 12 方位布局和避让策略 |
| VM-5 | AC-5.1 ~ AC-5.3 | UT | 子窗口创建和销毁 |
| VM-6 | AC-6.1 ~ AC-6.7 | UT | autoCancel 和交互行为 |
| VM-7 | AC-7.1 ~ AC-7.3 | UT | 焦点管理 |
| VM-8 | AC-8.1 ~ AC-8.8 | UT | 样式属性和默认值 |
| VM-9 | AC-9.1 ~ AC-9.4 | C API UT | 组件化和 C API 委托 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `bindPopup(show, popup: PopupOptions)` | Public | show: boolean, popup: PopupOptions | T | N/A | 绑定内置消息气泡 | AC-1.1 ~ AC-1.5 | @since 7 |
| `bindPopup(show, popup: CustomPopupOptions)` | Public | show: boolean, popup: CustomPopupOptions | T | N/A | 绑定自定义气泡 | AC-2.1 ~ AC-2.3 | @since 8 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `PopupOptions.placementOnTop` | 废弃 | @since 7, @deprecated 10 | 使用 `placement: Placement` 替代 | AC-1.3 |
| `PopupOptions.focusable` 默认值变更 | 变更 | @since 11 默认 true → @since 12 默认 false | 显式设置 focusable 以明确意图 | AC-7.1 |

> SDK 声明见 `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`。

## 接口规格

### 接口定义

**bindPopup**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bindPopup(show: boolean, popup: PopupOptions \| CustomPopupOptions): T` |
| 返回值 | `T` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-2.3 |

**参数约束（PopupOptions 关键参数）**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| message | string | 是 | — | 气泡消息内容 |
| placement | Placement | 否 | Bottom | 12 方位 + NONE |
| enableArrow | boolean | 否 | true | 是否显示箭头 |
| arrowOffset | Length | 否 | 0 | 箭头偏移 |
| arrowWidth | Dimension | 否 | 16vp | 箭头宽度 |
| arrowHeight | Dimension | 否 | 8vp | 箭头高度 |
| arrowPointPosition | ArrowPointPosition | 否 | — | 箭头位置 |
| showInSubWindow | boolean | 否 | true | 是否在子窗口显示 |
| mask | boolean \| ResourceColor | 否 | true | 遮罩 |
| autoCancel | boolean | 否 | true | 点击遮罩关闭 |
| targetSpace | Length | 否 | 8vp | 与宿主间距 |
| offset | Position | 否 | {0,0} | 偏移 |
| popupColor | ResourceColor | 否 | TRANSPARENT+ULTRA_THICK | 背景色 |
| width | Dimension | 否 | 自适应 | 气泡宽度 |
| radius | Dimension | 否 | 20vp | 圆角半径 |
| shadow | Shadow \| ShadowStyle | 否 | OUTER_DEFAULT_MD | 阴影 |
| backgroundBlurStyle | BlurStyle | 否 | COMPONENT_ULTRA_THICK | 背景模糊 |
| focusable | boolean | 否 | false (@since 12) | 焦点 |
| transition | Transition | 否 | — | 自定义过渡 (@since 12) |
| onStateChange | callback | 否 | — | 状态变化回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | bindPopup(true, { message: 'Hello' }) | 创建气泡并显示，使用默认 placement=Bottom | AC-1.1, AC-1.3 |
| 2 | bindPopup(false, _) | 关闭气泡 | AC-1.2 |
| 3 | bindPopup(true, { enableArrow: false }) | 隐藏箭头 | AC-1.5 |
| 4 | bindPopup(true, { autoCancel: false }) | 点击遮罩不关闭 | AC-6.2 |

## 兼容性声明

- **已有 API 行为变更:** 是
  - API 10: `placementOnTop` 废弃，引入 `placement`
  - API 12: `focusable` 默认值从 true 变更为 false
  - API 12: 引入 `transition` 自定义过渡动画
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 基础 API @since 7，CustomPopupOptions @since 8，arrowOffset/showInSubWindow @since 9，placement/mask/enableArrow/targetSpace/offset @since 10，popupColor/autoCancel/width/arrow*/radius/shadow/backgroundBlurStyle/focusable @since 11，transition @since 12

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双 Pattern 架构 | BubblePattern 继承 PopupBasePattern，声明式和命令式共用渲染层 | AC-1.1 |
| 组件化 | Bubble Pattern 输出独立 SO libarkui_bubble.z.so，通过 DynamicModule 注册 | AC-9.1 ~ AC-9.4 |
| 12 方位布局 | placementFuncMap_ 映射 12 种 Placement 到位置计算函数 | AC-4.1 ~ AC-4.4 |
| 避让策略 | FitToScreenNew + AvoidToTarget* 确保气泡可见 | AC-4.5, AC-4.6 |
| 子窗口 | showInSubWindow=true 时通过 SubwindowManager 创建子窗口 | AC-5.1 ~ AC-5.3 |
| 状态机 | TransitionStatus 四态管理气泡生命周期 | AC-3.3, AC-3.4 |
| C API modifier-based | 无独立 NODE 枚举，通过 bubble_modifier 委托 | AC-9.4 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 气泡进入/退出动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | 气泡关闭后 popupMap_ 正确清理，子窗口正确销毁 | UT | popupMap_ size + 子窗口计数 |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | 12 方位布局各场景下气泡不超出屏幕 | UT | 布局边界测试 |
| 问题定位 | hilog 标签 ACE_OVERLAY / ACE_DIALOG 覆盖关键路径 | 代码审查 | — |
| 自动化维测 | DumpTree 支持气泡节点树导出 | UT + Dump | 节点树 Dump |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 气泡避让策略需考虑折叠态/展开态屏幕尺寸变化 | FitToScreenNew 适配 | 手工 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | BubblePattern 实现 BubbleAccessibilityProperty，支持气泡内容无障碍读取 | AC-7.1 ~ AC-7.3 |
| 大字体 | 是 | 气泡消息文字跟随系统字体缩放 | AC-1.1 |
| 深色模式 | 是 | 颜色属性通过 ResourceColor 支持主题跟随，PopupThemeWrapper 适配 | AC-8.1, AC-8.2 |
| 多窗口/分屏 | 是 | showInSubWindow 控制是否在子窗口中显示 | AC-5.1 ~ AC-5.3 |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 7~26 大量版本演进，placementOnTop 废弃、focusable 默认值变更 | AC-1.3, AC-7.1 |
| 生态兼容 | 是 | C API 通过 modifier-based 方式委托，无独立 NODE 枚举 | AC-9.4 |

## 行为场景（Gherkin）

```gherkin
Feature: bindPopup 属性绑定与气泡布局
  作为应用开发者
  我想要通过 bindPopup 属性为组件绑定气泡弹窗
  以便在组件附近显示提示信息或自定义内容

  Scenario: 基础消息气泡显示
    Given 组件调用 bindPopup(true, { message: 'Hello', placement: Placement.BOTTOM })
    When OverlayManager::ShowPopup 执行
    Then 创建 Bubble FrameNode 并挂载到 overlay 层
    And 气泡显示在宿主节点底部
    And 显示箭头指向宿主节点
    And 使用 250ms FRICTION offset + SHARP alpha 进入动画
    And TransitionStatus 从 INVISIABLE 转为 ENTERING 再转为 NORMAL

  Scenario: 自定义气泡显示
    Given 组件调用 bindPopup(true, { builder: this.customBuilder })
    When BubbleView::CreateCustomBubbleNode 执行
    Then UseCustom=true 标记到 BubbleLayoutProperty
    And 使用 CustomBuilder 内容创建气泡
    And 不创建默认 message 和 button 子节点

  Scenario: 气泡退出动画
    Given 气泡处于 NORMAL 状态
    When bindPopup(false) 触发关闭
    Then HidePopupAnimation 执行
    And 使用 100ms FRICTION offset + SHARP alpha 退出动画
    And TransitionStatus 从 NORMAL 转为 EXITING 再转为 INVISIABLE
    And popupMap_.erase(targetId)

  Scenario: autoCancel 点击遮罩关闭
    Given 气泡显示中且 autoCancel=true
    When 用户点击气泡外部遮罩区域
    Then 气泡关闭
    And onStateChange 回调触发，isVisible=false

  Scenario: autoCancel=false 不关闭
    Given 气泡显示中且 autoCancel=false
    When 用户点击气泡外部遮罩区域
    Then 气泡不关闭

  Scenario: 气泡避让屏幕边界
    Given 气泡 placement=TOP 且宿主节点在屏幕顶部
    When BubbleLayoutAlgorithm::Layout 执行
    Then FitToScreenNew 检测到气泡超出屏幕顶部
    And 自动调整气泡位置到宿主节点下方

  Scenario Outline: 12 方位布局
    Given 组件调用 bindPopup(true, { message: 'test', placement: <placement> })
    When BubbleLayoutAlgorithm 通过 placementFuncMap_ 映射
    Then 气泡显示在宿主节点 <position>

    Examples:
      | placement    | position     |
      | TOP          | 上方         |
      | BOTTOM       | 下方         |
      | LEFT         | 左侧         |
      | RIGHT        | 右侧         |
      | TOP_LEFT     | 上左         |
      | TOP_RIGHT    | 上右         |
      | BOTTOM_LEFT  | 下左         |
      | BOTTOM_RIGHT | 下右         |
      | LEFT_TOP     | 左上         |
      | LEFT_BOTTOM  | 左下         |
      | RIGHT_TOP    | 右上         |
      | RIGHT_BOTTOM | 右下         |

  Scenario: focusable 焦点获取
    Given 气泡显示中且 focusable=true
    When 用户按 Tab 键
    Then 气泡获取键盘焦点
    And 支持键盘导航

  Scenario: C API 属性委托
    Given NDK 开发者通过 bubble_modifier 设置属性
    When DynamicModuleHelper 转发
    Then 属性委托到 libarkui_bubble.z.so 动态模块
    And 通过 bubble_inner_modifier 设置属性
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "BubblePattern 状态机 TransitionStatus 和 DismissReason"
  - repo: "openharmony/ace_engine"
    query: "BubbleLayoutAlgorithm placementFuncMap_ 12 方位布局和 FitToScreenNew 避让策略"
  - repo: "openharmony/ace_engine"
    query: "OverlayManager ShowPopup/HidePopup popupMap_ 管理和动画"
  - repo: "openharmony/ace_engine"
    query: "libarkui_bubble.z.so 组件化 BubbleDynamicModule 和 bubble_modifier 委托"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/common.d.ts`
- KB 路由: `docs/kb/components/overlay/bind_popup.md`
- 源码入口: `frameworks/core/components_ng/pattern/bubble/bubble_pattern.cpp`, `frameworks/core/components_ng/pattern/bubble/bubble_layout_algorithm.cpp`, `frameworks/core/components_ng/pattern/bubble/bubble_modifier.cpp`
