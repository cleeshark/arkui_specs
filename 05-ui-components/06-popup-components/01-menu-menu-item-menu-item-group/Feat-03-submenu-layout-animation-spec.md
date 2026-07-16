# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Menu 子菜单展开、布局避让、动画与预览 |
| 特性编号 | Func-05-06-01-Feat-03 |
| FuncID | 05-06-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 9 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ContextMenuOptions.preview (MenuPreviewMode) 预览图 | @since 11 |
| ADDED | ContextMenuOptions.aboutToAppear/aboutToDisappear 回调 | @since 11 |
| ADDED | ContextMenuOptions.previewAnimationOptions 预览动画 | @since 11 |
| ADDED | ContextMenuOptions.layoutRegionMargin 属性 | @since 13 |
| ADDED | ContextMenuOptions.previewBorderRadius 属性 | @since 19 |
| ADDED | ContextMenuOptions.gridStyle (MenuGridStyleOptions) 属性 | @since 26 |
| ADDED | C API: modifier-based (menu_modifier.cpp/menu_item_modifier.cpp/menu_item_group_modifier.cpp) | NDK 属性，无 NODE 枚举 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/design.md`
- **KB 路由**: `docs/kb/components/overlay/menu.md`
- **SDK 类型定义**:
  - Dynamic (ContextMenuOptions): `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`
  - Modifier (Menu): `<OH_ROOT>/interface/sdk-js/api/arkui/MenuModifier.d.ts`
  - Modifier (MenuItem): `<OH_ROOT>/interface/sdk-js/api/arkui/MenuItemModifier.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 子菜单展开模式

**角色**: 终端用户
**期望**: 我想要通过不同模式展开子菜单（侧面/内嵌/堆叠）
**价值**: 以便在不同设备尺寸下获得最佳的子菜单展示效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN subMenuExpandingMode = SIDE_EXPAND THEN 子菜单在主菜单侧面平面展开，不显示展开符号（`menu.d.ts:92`，`menu_layout_property.h:30` SubMenuExpandingMode::SIDE） | 正常 |
| AC-1.2 | WHEN subMenuExpandingMode = EMBEDDED_EXPAND THEN 子菜单内嵌展开，展开符号旋转 180°，默认 chevron_down（`menu.d.ts:102`，SubMenuExpandingMode::EMBEDDED） | 正常 |
| AC-1.3 | WHEN subMenuExpandingMode = STACK_EXPAND THEN 子菜单堆叠展开在主菜单上方，展开符号旋转 90°，默认 chevron_forward（`menu.d.ts:112`，SubMenuExpandingMode::STACK） | 正常 |
| AC-1.4 | WHEN STACK 模式展开子菜单 THEN 主菜单缩放至 0.6（MENU_ORIGINAL_SCALE），透明度降为 0.4（MAIN_MENU_OPACITY），子菜单使用 InterpolatingSpring(0, 1, 228, 26) 动画曲线（`menu_pattern.cpp:65-66,76-77`，`MenuItemPattern::ShowSubMenuWithAnimation` at `menu_item_pattern.cpp:774`） | 正常 |
| AC-1.5 | WHEN 子菜单展开时点击主菜单区域或按返回键 THEN 子菜单收起，主菜单恢复（`MenuWrapperPattern::HideSubMenu` at `menu_wrapper_pattern.cpp:474`） | 正常 |
| AC-1.6 | WHEN 多级子菜单展开 THEN HideSubMenuByDepth 递归关闭所有层级子菜单（`menu_wrapper_pattern.cpp:425`），DoCloseSubMenus 清理 showedSubMenu_（`menu_pattern.cpp:1110`） | 边界 |

### US-2: 菜单显示/隐藏动画

**角色**: 终端用户
**期望**: 我想要菜单显示和隐藏时有流畅的动画过渡
**价值**: 以便获得自然的交互体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 菜单显示 THEN MenuStatus 从 INIT 转为 ON_SHOW_ANIMATION，播放 ShowMenuAppearAnimation（`menu_pattern.h:926`），使用 InterpolatingSpring(0, 1, 528, 35) 主菜单动画曲线（`menu_pattern.cpp:74-75`） | 正常 |
| AC-2.2 | WHEN 显示动画完成 THEN MenuStatus 从 ON_SHOW_ANIMATION 转为 SHOW，触发 onAppear 回调（`common.d.ts:17148`） | 正常 |
| AC-2.3 | WHEN 菜单隐藏 THEN MenuStatus 从 SHOW 转为 ON_HIDE_ANIMATION，播放隐藏动画，完成后转为 HIDE，触发 onDisappear 回调（`common.d.ts:17159`，`MenuWrapperPattern::HideMenu` at `menu_wrapper_pattern.cpp:394`） | 正常 |
| AC-2.4 | WHEN 设置 aboutToAppear/aboutToDisappear 回调 THEN 在菜单即将显示/消失前触发（`common.d.ts:17170,17181`） | 正常 |

### US-3: 预览图（Preview）

**角色**: 终端用户
**期望**: 我想要在长按触发上下文菜单时看到组件预览图
**价值**: 以便在菜单展开前预览操作目标

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 ContextMenuOptions.preview = MenuPreviewMode.IMAGE THEN 长按触发时显示组件截图预览（`common.d.ts:16452,17090`，`MenuView::Create` 创建 MENU_PREVIEW_ETS_TAG 节点 at `menu_view.cpp:1499`） | 正常 |
| AC-3.2 | WHEN 设置 preview = CustomBuilder THEN 显示自定义预览内容（`common.d.ts:17090`） | 正常 |
| AC-3.3 | WHEN preview 设置为 IMAGE 或 CustomBuilder THEN enableArrow 不生效，不显示箭头（`common.d.ts:17079-17080`） | 边界 |
| AC-3.4 | WHEN preview = MenuPreviewMode.NONE 或未设置 THEN enableArrow 生效，可显示箭头（`common.d.ts:17079`） | 正常 |
| AC-3.5 | WHEN responseType = RIGHT_CLICK THEN preview 参数无效（`common.d.ts:17078`） | 边界 |
| AC-3.6 | WHEN 设置 previewAnimationOptions.scale THEN 预览图按 [from, to] 缩放，默认 [0.95, 1.1]（`common.d.ts:17224`，MenuPreviewPattern Hover 动画） | 正常 |
| AC-3.7 | WHEN 设置 previewBorderRadius THEN 预览图圆角为指定值，默认 16vp（`common.d.ts:17095,17112`）；水平两圆角之和超过宽度时使用最大允许半径 | 正常 |
| AC-3.8 | WHEN previewAnimationOptions.scale 值 ≤ 0 THEN 参数不生效（`common.d.ts:17222`） | 边界 |

### US-4: 菜单布局与避让

**角色**: 应用开发者
**期望**: 我想要了解菜单在不同位置和屏幕尺寸下的布局和避让行为
**价值**: 以便预判菜单在边界情况下的位置调整

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 菜单显示位置超出屏幕 THEN FitToScreen 将菜单限制在屏幕范围内（`menu_layout_algorithm.cpp:3107`） | 正常 |
| AC-4.2 | WHEN 菜单位置超出可用区域 THEN MenuLayoutAvoidAlgorithm 对 x/y 进行 clamp：x = clamp(x, paddingStart, wrapperRect.Right() - size.Width() - paddingEnd)，y = clamp(y, yMinAvoid, yMaxAvoid)（`menu_layout_algorithm.cpp:2515-2519`） | 正常 |
| AC-4.3 | WHEN 设置 placement 但位置不足 THEN 按 PLACEMENT_STATES 策略表尝试备选位置（`menu_avoid_algorithm.cpp:33`，定义每种 Placement 的备选顺序） | 正常 |
| AC-4.4 | WHEN 设置 enableArrow=true 且位置足够 THEN 显示箭头，箭头位置由 placement 和 arrowOffset 决定（`common.d.ts:17031,17067`，箭头参数 ARROW_RADIUS 等 at `menu_layout_algorithm.cpp:53-63`） | 正常 |
| AC-4.5 | WHEN enableArrow=true 但位置不足 THEN 不显示箭头（`common.d.ts:17010-17011`） | 边界 |
| AC-4.6 | WHEN 设置 offset={x,y} THEN 菜单按 offset 偏移，超出屏幕自动 clamp（`common.d.ts:16986,16972-16973`）；若菜单位置被调整（不同于 placement 主方向）则 offset 失效 | 正常 |
| AC-4.7 | WHEN Menu 未设置 width THEN 子组件 MenuItem/MenuItemGroup 使用默认两列宽度，内容超出时自动扩展；最小宽度 64vp（`menu.d.ts:51-58`，`menu_model_ng.cpp:271` MIN_MENU_WIDTH） | 正常 |
| AC-4.8 | WHEN Menu 设置显式 width THEN 子组件 MenuItem/MenuItemGroup 使用固定宽度（= Menu width - padding）（`menu.d.ts:55-56`） | 正常 |

### US-5: C API / NDK 支持

**角色**: NDK 开发者
**期望**: 我想要通过 C API 控制 Menu/MenuItem/MenuItemGroup 属性
**价值**: 以便在 Native 层集成菜单组件

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 C API Menu 属性 THEN 通过 `GetMenuModifier()` (`menu_modifier.cpp:25`) 使用 `DynamicModuleHelper::GetDynamicModule("Menu")` 加载 libarkui_menu.z.so，获取 ArkUIMenuModifier 函数表转发属性操作 | 正常 |
| AC-5.2 | WHEN 调用 C API MenuItem 属性 THEN 通过 `menu_item_modifier.cpp` 委托层转发到动态模块 | 正常 |
| AC-5.3 | WHEN 调用 C API MenuItemGroup 属性 THEN 通过 `menu_item_group_modifier.cpp` 委托层转发到动态模块 | 正常 |
| AC-5.4 | WHEN Menu C API 无独立 NODE 枚举 THEN 使用 modifier-based 架构，不走 FrameNode 节点类型枚举（`menu_modifier.cpp` 通过 DynamicModuleHelper 转发） | 边界 |

### US-6: 多设备与子窗口适配

**角色**: 应用开发者
**期望**: 我想要了解 Menu 在不同设备上的行为差异
**价值**: 以便在多设备适配时预判行为变化

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 在 2-in-1 设备上未设置 showInSubWindow THEN 默认 true，菜单在独立子窗口中显示（`common.d.ts:17718,17722-17723`，`SubwindowManager::ShowMenuNG` at `menu_pattern.cpp:1084`） | 正常 |
| AC-6.2 | WHEN 在非 2-in-1 设备上未设置 showInSubWindow THEN 默认 false，菜单在 overlay 树中显示 | 正常 |
| AC-6.3 | WHEN showInSubWindow=true 且仅 2-in-1 设备生效 THEN 其他设备该参数无效（`common.d.ts:17722`） | 边界 |
| AC-6.4 | WHEN Menu 圆角未设置 THEN 2-in-1 默认 8vp，其他设备默认 20vp（`menu.d.ts:169`，`common.d.ts:17115`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-MENU-01 | UT | `menu_layout_property.h:30` |
| AC-1.2 | R-1 | TASK-MENU-01 | UT | `menu.d.ts:102` |
| AC-1.3 | R-1 | TASK-MENU-01 | UT | `menu.d.ts:112` |
| AC-1.4 | R-2 | TASK-MENU-01 | UT | `menu_pattern.cpp:65-66,76-77` |
| AC-1.5 | R-3 | TASK-MENU-01 | UT | `menu_wrapper_pattern.cpp:474` |
| AC-1.6 | R-3 | TASK-MENU-01 | UT | `menu_wrapper_pattern.cpp:425` |
| AC-2.1 | R-4 | TASK-MENU-01 | UT | `menu_pattern.h:926` |
| AC-2.2 | R-4 | TASK-MENU-01 | UT | `common.d.ts:17148` |
| AC-2.3 | R-4 | TASK-MENU-01 | UT | `menu_wrapper_pattern.cpp:394` |
| AC-2.4 | R-4 | TASK-MENU-01 | UT | `common.d.ts:17170,17181` |
| AC-3.1 | R-5 | TASK-MENU-01 | UT | `menu_view.cpp:1499` |
| AC-3.2 | R-5 | TASK-MENU-01 | UT | `common.d.ts:17090` |
| AC-3.3 | R-6 | TASK-MENU-01 | UT | `common.d.ts:17079-17080` |
| AC-3.4 | R-6 | TASK-MENU-01 | UT | `common.d.ts:17079` |
| AC-3.5 | R-6 | TASK-MENU-01 | UT | `common.d.ts:17078` |
| AC-3.6 | R-5 | TASK-MENU-01 | UT | `common.d.ts:17224` |
| AC-3.7 | R-5 | TASK-MENU-01 | UT | `common.d.ts:17095,17112` |
| AC-3.8 | R-5 | TASK-MENU-01 | UT | `common.d.ts:17222` |
| AC-4.1 | R-7 | TASK-MENU-01 | UT | `menu_layout_algorithm.cpp:3107` |
| AC-4.2 | R-7 | TASK-MENU-01 | UT | `menu_layout_algorithm.cpp:2515-2519` |
| AC-4.3 | R-8 | TASK-MENU-01 | UT | `menu_avoid_algorithm.cpp:33` |
| AC-4.4 | R-8 | TASK-MENU-01 | UT | `menu_layout_algorithm.cpp:53-63` |
| AC-4.5 | R-7 | TASK-MENU-01 | UT | `common.d.ts:17010-17011` |
| AC-4.6 | R-7 | TASK-MENU-01 | UT | `common.d.ts:16986,16972-16973` |
| AC-4.7 | R-7 | TASK-MENU-01 | UT | `menu.d.ts:51-58` |
| AC-4.8 | R-7 | TASK-MENU-01 | UT | `menu.d.ts:55-56` |
| AC-5.1 | R-9 | TASK-MENU-01 | C API UT | `menu_modifier.cpp:25` |
| AC-5.2 | R-9 | TASK-MENU-01 | C API UT | `menu_item_modifier.cpp` |
| AC-5.3 | R-9 | TASK-MENU-01 | C API UT | `menu_item_group_modifier.cpp` |
| AC-5.4 | R-9 | TASK-MENU-01 | C API UT | `menu_modifier.cpp` |
| AC-6.1 | R-10 | TASK-MENU-01 | 手工 | `common.d.ts:17718` |
| AC-6.2 | R-10 | TASK-MENU-01 | 手工 | — |
| AC-6.3 | R-10 | TASK-MENU-01 | 手工 | `common.d.ts:17722` |
| AC-6.4 | R-10 | TASK-MENU-01 | 手工 | `menu.d.ts:169` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | subMenuExpandingMode = SIDE/EMBEDDED/STACK | 分别对应侧面/内嵌/堆叠展开 | 枚举值 SIDE=0, EMBEDDED=1, STACK=2 | AC-1.1, AC-1.2, AC-1.3 |
| R-2 | 行为 | STACK 模式展开子菜单 | 主菜单缩放 0.6，透明度 0.4，子菜单 InterpolatingSpring(0,1,228,26) | MENU_ORIGINAL_SCALE=0.6f, MAIN_MENU_OPACITY=0.4f | AC-1.4 |
| R-3 | 恢复 | 子菜单展开时关闭/多级子菜单展开时关闭 | 点击主菜单或返回键收起；HideSubMenuByDepth 递归关闭，DoCloseSubMenus 清理 showedSubMenu_ | — | AC-1.5, AC-1.6 |
| R-4 | 行为 | 菜单显示/隐藏 | MenuStatus: INIT → ON_SHOW_ANIMATION → SHOW → ON_HIDE_ANIMATION → HIDE → INIT | onAppear/onDisappear/aboutToAppear/aboutToDisappear 回调 | AC-2.1, AC-2.2, AC-2.3, AC-2.4 |
| R-5 | 行为 | 设置 preview = IMAGE/CustomBuilder | 长按触发时显示预览图 | previewBorderRadius 默认 16vp，previewAnimationOptions.scale 默认 [0.95, 1.1]，scale ≤ 0 不生效 | AC-3.1, AC-3.2, AC-3.6, AC-3.7, AC-3.8 |
| R-6 | 边界 | preview 设置为 IMAGE/CustomBuilder | enableArrow 不生效，不显示箭头 | preview=NONE 时 enableArrow 生效；RIGHT_CLICK 时 preview 无效 | AC-3.3, AC-3.4, AC-3.5 |
| R-7 | 边界 | 菜单位置超出屏幕/可用区域 | FitToScreen 限制在屏幕内，MenuLayoutAvoidAlgorithm clamp x/y；enableArrow 位置不足时不显示；offset 超屏 clamp，位置调整后失效；宽度未设置默认两列最小 64vp | x=clamp(x, paddingStart, wrapperRect.Right()-size.Width()-paddingEnd) | AC-4.1, AC-4.2, AC-4.5, AC-4.6, AC-4.7, AC-4.8 |
| R-8 | 行为 | 设置 placement 但位置不足/enableArrow 且位置足够 | 按 PLACEMENT_STATES 策略表尝试备选位置；箭头位置由 placement 和 arrowOffset 决定 | 每种 Placement 有定义的备选顺序 | AC-4.3, AC-4.4 |
| R-9 | 行为 | 调用 C API Menu/MenuItem/MenuItemGroup 属性 | 通过 DynamicModuleHelper 加载 libarkui_menu.z.so 转发 | 无独立 NODE 枚举，modifier-based | AC-5.1, AC-5.2, AC-5.3, AC-5.4 |
| R-10 | 行为 | 2-in-1 设备未设置 showInSubWindow | 默认 true，在子窗口中显示 | 其他设备默认 false；圆角 2-in-1 默认 8vp，其他 20vp | AC-6.1, AC-6.2, AC-6.3, AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.6 | UT + 手工 | 子菜单三模式展开/收起、多级递归关闭 |
| VM-2 | AC-2.1 ~ AC-2.4 | UT | MenuStatus 状态机转换和动画回调 |
| VM-3 | AC-3.1 ~ AC-3.8 | UT + 手工 | 预览图 IMAGE/CustomBuilder/NONE、previewBorderRadius、previewAnimationOptions |
| VM-4 | AC-4.1 ~ AC-4.8 | UT | 布局避让三层算法、箭头、offset、宽度计算 |
| VM-5 | AC-5.1 ~ AC-5.4 | C API UT | modifier-based C API 委托转发 |
| VM-6 | AC-6.1 ~ AC-6.4 | 手工 | 多设备 showInSubWindow/圆角默认值差异 |

## API 变更分析

> 涉及 API 变更时必填。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| ContextMenuOptions.preview | Public | MenuPreviewMode | — | 无 | 预览图模式 | AC-3.1, AC-3.2 |
| ContextMenuOptions.previewAnimationOptions | Public | { scale: [from, to] } | — | 无 | 预览动画 | AC-3.6 |
| ContextMenuOptions.previewBorderRadius | Public | Dimension | — | 无 | 预览图圆角 | AC-3.7 |
| ContextMenuOptions.layoutRegionMargin | Public | Margin | — | 无 | 布局避让区域边距 | AC-4.2 |
| ContextMenuOptions.gridStyle | Public | MenuGridStyleOptions | — | 无 | 网格样式 | AC-4.7 |
| ContextMenuOptions.aboutToAppear/aboutToDisappear | Public | Callback | — | 无 | 菜单显示/消失前回调 | AC-2.4 |
| C API: menu_modifier (Set/Reset/Get) | System | 属性名 + 值 | 无 | 无 | C API 属性委托 | AC-5.1 |
| C API: menu_item_modifier (Set/Reset/Get) | System | 属性名 + 值 | 无 | 无 | MenuItem C API 属性委托 | AC-5.2 |
| C API: menu_item_group_modifier (Set/Reset/Get) | System | 属性名 + 值 | 无 | 无 | MenuItemGroup C API 属性委托 | AC-5.3 |

### 变更/废弃 API

> N/A，本特性不涉及已有 API 的废弃或签名变更。

> API 签名、d.ts 位置、权限要求等实现细节见 design.md "API 签名、Kit 与权限" 章节。

## 接口规格

### 接口定义

**ContextMenuOptions.preview (预览图)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `preview?: MenuPreviewMode` (ContextMenuOptions 属性) |
| 返回值 | — |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| preview | MenuPreviewMode | 否 | NONE | IMAGE/CustomBuilder 时 enableArrow 不生效；RIGHT_CLICK 时 preview 无效 |

---

**ContextMenuOptions.previewAnimationOptions (预览动画)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `previewAnimationOptions?: { scale: [from: number, to: number] }` (ContextMenuOptions 属性) |
| 返回值 | — |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.6, AC-3.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| scale.from | number | 否 | 0.95 | ≤ 0 时参数不生效 |
| scale.to | number | 否 | 1.1 | ≤ 0 时参数不生效 |

---

**ContextMenuOptions.previewBorderRadius (预览圆角)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `previewBorderRadius?: Dimension` (ContextMenuOptions 属性) |
| 返回值 | — |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| previewBorderRadius | Dimension | 否 | 16vp | 水平两圆角之和超过宽度时使用最大允许半径 |

---

**C API: menu_modifier**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUIMenuModifier::Set* / Reset* / Get* (属性名, 值)` |
| 返回值 | — |
| 开放范围 | System |
| 错误码 | N/A |
| 关联 AC | AC-5.1, AC-5.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | 属性名 + 值 | 是 | — | 通过 DynamicModuleHelper::GetDynamicModule("Menu") 加载 libarkui_menu.z.so 转发；无独立 NODE 枚举 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9（子菜单/布局/动画）、API 11（预览图/aboutToAppear）、API 13（layoutRegionMargin）
- **API 版本号策略:** 各 API 按 @since 标注版本引入，通过 Container::LessThanAPIVersion/GreatOrEqualAPIVersion 条件分支实现兼容

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| MenuWrapperPattern 继承 PopupBasePattern | 全屏容器模式，管理菜单生命周期、动画状态机和点击区域外消失 | AC-2.1, AC-2.3, AC-1.5 |
| 组件化独立 SO | libarkui_menu.z.so 通过 DynamicModuleHelper 加载，C API 走 modifier-based 架构 | AC-5.1 ~ AC-5.4 |
| 调用链自上而下 | SDK → JS Bridge → ViewAbstract → OverlayManager → Bridge → Model → View → Pattern → Layout → Paint | 全部 AC |
| 子窗口依赖隔离 | SubwindowManager 隔离 window_manager 跨子系统依赖 | AC-6.1 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 菜单显示响应时间 ≤ 100ms（从触发到 onAppear），动画帧率 ≥ 60fps | 手工测试 + trace | — |
| 内存 | 单个菜单节点树内存占用 ≤ 500KB（含预览图节点） | 内存分析 | — |
| 可靠性 | 子窗口加载失败时降级到 overlay 模式 | 集成测试 | `menu_pattern.cpp:1084` SubwindowManager 降级 |
| 可测试性 | UT 覆盖 MenuLayoutAlgorithm/MenuWrapperPattern/MenuPreviewPattern | UT | `test/unittest/core/pattern/menu/` |
| 自动化维测 | 支持 DumpLog 状态导出 | hilog | MenuWrapperPattern Dump |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | overlay 模式，圆角 20vp，showInSubWindow 默认 false | — | 手工 | `common.d.ts:17115,17718` |
| 平板 | overlay 模式，圆角 20vp，showInSubWindow 默认 false | — | 手工 | `common.d.ts:17115,17718` |
| 折叠屏 | 半折叠状态有 Hover 动画（HALF_FOLD_HOVER_DURATION=1000ms） | — | 手工 | `menu_pattern.cpp:64` |
| 2-in-1 | 子窗口模式，圆角 8vp，showInSubWindow 默认 true | 子窗口 IPC 依赖 | 手工 | `common.d.ts:17115,17718,17722` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 无差异 | — |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 是 | showInSubWindow 支持 2-in-1 子窗口显示，折叠屏分屏不影响 overlay 模式 | AC-6.1, AC-6.2 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 9~26 多版本兼容，各设备行为差异按 @since 标注 | AC-6.4 |
| 生态兼容 | 是 | 组件化 SO 独立维护，C API modifier-based 架构跨语言兼容 | AC-5.1 ~ AC-5.4 |

## 行为场景（可选，Gherkin）

> L2+（复杂）使用 Gherkin 场景表达。本特性为复杂变更，使用 Gherkin 场景补充接口规格行为表。

```gherkin
Feature: Menu 子菜单展开、布局避让、动画与预览
  作为应用开发者
  我想要控制子菜单展开模式、预览图、布局避让和 C API 集成
  以便在不同设备尺寸下获得最佳的菜单交互体验

  Scenario: bindContextMenu 长按触发显示预览图
    Given 组件绑定了 bindContextMenu(builder, ResponseType.LONG_PRESS, {preview: MenuPreviewMode.IMAGE})
    When 用户长按该组件
    Then 先显示组件截图预览图
    And 预览图按 [0.95, 1.1] 缩放动画过渡
    And 然后显示上下文菜单
    And 不显示箭头（preview 非 NONE）

  Scenario Outline: 子菜单展开模式
    Given Menu 设置 subMenuExpandingMode = <mode>
    When 点击有 builder 的 MenuItem
    Then 子菜单按 <mode> 模式展开
    And 主菜单 <mainBehavior>

    Examples:
      | mode | mainBehavior |
      | SIDE_EXPAND | 保持不变 |
      | EMBEDDED_EXPAND | 内嵌展开 |
      | STACK_EXPAND | 缩放至 0.6 透明度 0.4 |

  Scenario: STACK 模式子菜单动画
    Given Menu 设置 subMenuExpandingMode = STACK_EXPAND
    When 点击有 builder 的 MenuItem
    Then 主菜单缩放至 0.6 (MENU_ORIGINAL_SCALE)
    And 主菜单透明度降为 0.4 (MAIN_MENU_OPACITY)
    And 子菜单使用 InterpolatingSpring(0, 1, 228, 26) 动画曲线展开
    When 用户点击主菜单区域
    Then 子菜单收起，主菜单恢复

  Scenario: 多级子菜单关闭
    Given 多级子菜单已展开（3 层）
    When 用户点击最外层菜单区域或按返回键
    Then HideSubMenuByDepth 递归关闭所有层级子菜单
    And DoCloseSubMenus 清理 showedSubMenu_

  Scenario: 菜单显示/隐藏动画
    Given 菜单即将显示
    When 触发显示
    Then MenuStatus 从 INIT 转为 ON_SHOW_ANIMATION
    And 播放 ShowMenuAppearAnimation (InterpolatingSpring(0,1,528,35))
    When 显示动画完成
    Then MenuStatus 转为 SHOW
    And 触发 onAppear 回调

  Scenario: 菜单避让边界
    Given 菜单显示在屏幕边缘且 placement = Placement.BOTTOM_LEFT
    When 菜单底部超出屏幕可用区域
    Then MenuLayoutAvoidAlgorithm 对 y 进行 clamp
    And 菜单调整到屏幕内显示

  Scenario: 预览图圆角边界
    Given 设置 previewBorderRadius 且水平两圆角之和超过预览图宽度
    When 预览图显示
    Then 使用最大允许半径作为圆角

  Scenario: C API modifier 委托
    Given NDK 代码调用 Menu C API 属性设置
    When GetMenuModifier() 被调用
    Then DynamicModuleHelper::GetDynamicModule("Menu") 加载 libarkui_menu.z.so
    And 获取 ArkUIMenuModifier 函数表转发属性操作
    And 不走 FrameNode 节点类型枚举
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
  - repo: "openharmony/arkui_ace_engine"
    query: "MenuWrapperPattern MenuStatus 状态机转换条件和动画驱动"
  - repo: "openharmony/arkui_ace_engine"
    query: "MenuLayoutAlgorithm PLACEMENT_STATES 重定位策略和 FitToScreen 屏幕适配算法"
  - repo: "openharmony/arkui_ace_engine"
    query: "MenuItemPattern ShowSubMenu/HideSubMenu 三种 SubMenuExpandingMode 展开逻辑"
  - repo: "openharmony/arkui_ace_engine"
    query: "MenuPreviewPattern Hover 动画和 previewAnimationOptions 实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "libarkui_menu.z.so 组件化 DynamicModule 加载和 C API modifier 委托"
```

**关键文档：**
- 设计文档: `specs/05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/design.md`
- KB 路由: `docs/kb/components/overlay/menu.md`
- SDK (ContextMenuOptions): `interface/sdk-js/api/@internal/component/ets/common.d.ts`
- SDK (MenuModifier): `interface/sdk-js/api/arkui/MenuModifier.d.ts`
- SDK (MenuItemModifier): `interface/sdk-js/api/arkui/MenuItemModifier.d.ts`
