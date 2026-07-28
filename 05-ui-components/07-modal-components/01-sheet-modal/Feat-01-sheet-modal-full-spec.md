# 特性规格

> Func-05-07-01-Feat-01 bindSheet 半模态弹窗：固化绑定与双向 isShow、height 模式（MEDIUM/LARGE/FIT_CONTENT）、detents 档位、dragBar/showClose、preferType（bottom/center/popup/side/content_cover）、title、shouldDismiss/onWillDismiss/springBack、生命周期回调、mode OVERLAY/EMBEDDED、keyboardAvoid、blur/bg/mask、hoverMode、子窗口、attributeModifier 限制的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | bindSheet 半模态弹窗 (Sheet Modal) |
| 特性编号 | Func-05-07-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 10 起支持，API 11/12/13/14/15/18/19/20/23/26 持续演进 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 绑定与双向 isShow 行为规格 | bindSheet(isShow, builder, options?) @since 10，ParseSheetIsShow 双向绑定 |
| ADDED | height 模式行为规格 | SheetSize MEDIUM/LARGE/FIT_CONTENT，mediumSize 比例（API<=10 0.5 else ~0.6） |
| ADDED | detents 档位行为规格 | 最多 3 档升序排序去重，detentSelection 默认 detents[0] @since 15 |
| ADDED | dragBar/showClose 行为规格 | dragBar 默认 true（grabber），showClose 默认 true，enableFloatingDragBar 默认 false @since 20 |
| ADDED | preferType 行为规格 | SheetType SHEET_BOTTOM/CENTER/POPUP/SIDE/CONTENT_COVER，SheetObject 策略 |
| ADDED | title 行为规格 | SheetTitleOptions 或 CustomBuilder |
| ADDED | shouldDismiss/onWillDismiss/springBack 行为规格 | SheetInteractiveDismiss 渐进式拦截链 |
| ADDED | 生命周期回调行为规格 | onWillAppear/onAppear/onWillDisappear/onDisappear + onHeightDidChange/onDetentsDidChange/onWidthDidChange/onTypeDidChange |
| ADDED | mode/keyboardAvoid 行为规格 | mode OVERLAY/EMBEDDED，keyboardAvoidMode 默认 TRANSLATE_AND_SCROLL @since 13 |
| ADDED | blur/bg/mask 行为规格 | blurStyle 默认 NONE，backgroundColor 默认 White，maskColor |
| ADDED | hoverMode/子窗口/attributeModal 限制行为规格 | enableHoverMode 默认 false @since 14，showInSubWindow 默认 false @since 19，attributeModifier 限制 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/07-modal-components/01-sheet-modal/design.md` | Baselined |
| SDK API | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | — |

---

## 用户故事

### US-1: 绑定与双向 isShow

**作为** 应用开发者,
**我想要** 通过 `bindSheet(isShow, builder, options?)` 绑定半模态弹窗并通过状态变量控制显示,
**以便** 命令式管理 Sheet 的显示与隐藏。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `bindSheet(isShow, builder, options?)` THEN ParseSheetIsShow 检测 isShow 双向绑定 | 正常 |
| AC-1.2 | WHEN isShow=true THEN Sheet 创建并显示（FrameNode + SheetPresentationPattern 挂载） | 正常 |
| AC-1.3 | WHEN isShow=false THEN Sheet 移除 | 正常 |
| AC-1.4 | WHEN SheetStyle 默认值 L2530（sheetMode=LARGE/enableFloatingDragBar=false/showDragBar=true/showCloseIcon=true/showInPage=false）THEN 应用默认样式 | 边界 |

### US-2: height 模式

**作为** 应用开发者,
**我想要** 通过 `height` 设置 Sheet 高度模式,
**以便** 控制半模态弹窗的覆盖范围。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN height = SheetSize.MEDIUM THEN 高度 = pageHeight * mediumSize（API<=10: 0.5, else ~0.6） | 边界 |
| AC-2.2 | WHEN height = SheetSize.LARGE THEN 高度 = largeHeight（GetLargePercent） | 边界 |
| AC-2.3 | WHEN height = SheetSize.FIT_CONTENT THEN 高度 = fitContent，上限 largeHeight | 边界 |
| AC-2.4 | WHEN 未指定 height THEN 默认 LARGE | 边界 |

### US-3: detents 档位

**作为** 应用开发者,
**我想要** 通过 `detents` 设置拖拽高度档位,
**以便** 支持多档拖拽体验。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 detents THEN 最多 3 档，升序排序，去重 | 正常 |
| AC-3.2 | WHEN 拖拽 Sheet THEN 在 detents 档位间吸附 | 正常 |
| AC-3.3 | WHEN 设置 detentSelection THEN 初始档位为指定值（默认 detents[0]，@since 15） | 边界 |

### US-4: dragBar 与 showClose

**作为** 应用开发者,
**我想要** 通过 dragBar 显示拖拽条，通过 showClose 显示关闭按钮,
**以便** 提供拖拽与关闭交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN dragBar=true（默认）THEN 显示拖拽条（grabber） | 正常 |
| AC-4.2 | WHEN showClose=true（默认）THEN 显示关闭按钮（CLOSE_BUTTON L233） | 正常 |
| AC-4.3 | WHEN enableFloatingDragBar 设置（默认 false，@since 20）THEN 悬浮态独立控制拖拽条 | 边界 |

### US-5: preferType

**作为** 应用开发者,
**我想要** 通过 `preferType` 设置 Sheet 形态,
**以便** 支持底部/中心/弹窗/侧边/全屏覆盖等不同形态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN preferType=SheetType.SHEET_BOTTOM（默认）THEN 底部 Sheet | 边界 |
| AC-5.2 | WHEN preferType=SheetType.CENTER THEN 中心 Sheet | 正常 |
| AC-5.3 | WHEN preferType=SheetType.POPUP THEN 弹窗 Sheet | 正常 |
| AC-5.4 | WHEN preferType=SheetType.SIDE THEN 侧边 Sheet | 正常 |
| AC-5.5 | WHEN preferType=SheetType.CONTENT_COVER THEN 全屏覆盖，无 drag/scroll/keyboard avoid/shadow/border（SheetContentCoverObject） | 边界 |

### US-6: title

**作为** 应用开发者,
**我想要** 通过 `title` 设置 Sheet 标题,
**以便** 在 Sheet 顶部展示标题文本或自定义内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN title 为 SheetTitleOptions THEN 显示标题文本 | 正常 |
| AC-6.2 | WHEN title 为 CustomBuilder THEN 显示自定义标题内容 | 正常 |
| AC-6.3 | WHEN 未设置 title THEN 不显示标题区域 | 边界 |

### US-7: shouldDismiss / onWillDismiss / springBack

**作为** 应用开发者,
**我想要** 通过 shouldDismiss / onWillDismiss / onWillSpringBackWhenDismiss 拦截 Sheet 关闭,
**以便** 实现条件关闭或回弹交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 设置 shouldDismiss（bool 回调，@since 11）THEN CallShouldDismiss 返回 false 时不关闭 | 正常 |
| AC-7.2 | WHEN 设置 onWillDismiss（DismissSheetAction，@since 12）THEN CallOnWillDismiss 提供 DismissSheetAction（dismiss + reason） | 正常 |
| AC-7.3 | WHEN 设置 onWillSpringBackWhenDismiss（SpringBackAction，@since 12）THEN 提供 SpringBackAction（springBack + reason） | 正常 |
| AC-7.4 | WHEN 未设置 shouldDismiss/onWillDismiss THEN SheetInteractiveDismiss 直接 DismissTransition | 边界 |

### US-8: 生命周期回调

**作为** 应用开发者,
**我想要** 通过生命周期回调感知 Sheet 显示/隐藏/高度/档位/宽度/类型变化,
**以便** 在不同时机执行业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN Sheet 即将显示 THEN onWillAppear 触发（overlay_manager.cpp L4195） | 正常 |
| AC-8.2 | WHEN Sheet 已显示 THEN onAppear 触发（overlay_manager.cpp L4205） | 正常 |
| AC-8.3 | WHEN Sheet 即将隐藏 THEN onWillDisappear 触发（overlay_manager.cpp L4241） | 正常 |
| AC-8.4 | WHEN Sheet 已隐藏 THEN onDisappear 触发（overlay_manager.cpp L4263） | 正常 |
| AC-8.5 | WHEN Sheet 高度/detents/宽度/类型变化 THEN onHeightDidChange L3212/onDetentsDidChange L3227/onWidthDidChange L3240/onTypeDidChange L3254 触发 | 正常 |

### US-9: mode 与 keyboardAvoid

**作为** 应用开发者,
**我想要** 通过 mode 选择 overlay/embedded 挂载，通过 keyboardAvoidMode 控制键盘避让,
**以便** 适配不同场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN mode=SheetMode.OVERLAY（默认）THEN Sheet 挂载到 overlay 层 | 边界 |
| AC-9.2 | WHEN mode=SheetMode.EMBEDDED THEN Sheet 挂载到嵌入节点 | 正常 |
| AC-9.3 | WHEN keyboardAvoidMode 默认 TRANSLATE_AND_SCROLL（@since 13）THEN 键盘弹出时 Sheet 上移+内容滚动避让 | 边界 |
| AC-9.4 | WHEN scrollSizeMode 默认 FOLLOW_DETENT THEN 内容滚动跟随档位 | 边界 |

### US-10: blur / bg / mask

**作为** 应用开发者,
**我想要** 通过 blurStyle / backgroundColor / maskColor 配置 Sheet 外观,
**以便** 定制半模态弹窗视觉风格。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN blurStyle 默认 NONE（范围 NO_MATERIAL..COMPONENT_ULTRA_THICK）THEN 可设置模糊效果 | 边界 |
| AC-10.2 | WHEN backgroundColor 默认 White THEN 可设置背景颜色 | 边界 |
| AC-10.3 | WHEN 设置 maskColor THEN 遮罩使用指定颜色 | 正常 |
| AC-10.4 | WHEN 设置 radius（@since 15）THEN 应用指定圆角 | 正常 |

### US-11: hoverMode / 子窗口 / attributeModifier 限制

**作为** 应用开发者,
**我想要** 通过 hoverMode 支持悬浮态，通过 showInSubWindow 支持子窗口，并了解 attributeModifier 限制,
**以便** 适配复杂场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-11.1 | WHEN enableHoverMode=true（默认 false，@since 14）THEN 启用悬浮态，hoverModeArea 默认 BOTTOM_SCREEN | 正常 |
| AC-11.2 | WHEN showInSubWindow=true（默认 false，@since 19）THEN SubwindowManager::ShowBindSheetNG 创建子窗口 | 正常 |
| AC-11.3 | WHEN 在 attributeModifier 中调用 bindSheet THEN 抛出异常（不允许） | 异常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1, R-2 | 代码审查 js_popups.cpp:2491 ParseSheetIsShow |
| AC-1.2 | US-1 | R-3 | 单元测试 + 代码审查 overlay_manager.cpp:3963 OnBindSheet |
| AC-1.3 | US-1 | R-4 | 单元测试 |
| AC-1.4 | US-1 | R-5 | 代码审查 js_popups.cpp:2530 |
| AC-2.1 | US-2 | R-6, R-7 | 代码审查 sheet_style.h + sheet_theme.h |
| AC-2.2 | US-2 | R-8 | 代码审查 |
| AC-2.3 | US-2 | R-9 | 代码审查 |
| AC-2.4 | US-2 | R-10 | 代码审查 js_popups.cpp:2530 |
| AC-3.1 | US-3 | R-11 | 代码审查 js_popups.cpp:3002 ParseSheetDetents |
| AC-3.2 | US-3 | R-12 | 单元测试 |
| AC-3.3 | US-3 | R-13 | 代码审查 |
| AC-4.1 | US-4 | R-14 | 单元测试 |
| AC-4.2 | US-4 | R-15 | 代码审查 sheet_view.cpp:233 |
| AC-4.3 | US-4 | R-16 | 代码审查 |
| AC-5.1 | US-5 | R-17 | 单元测试 |
| AC-5.2 | US-5 | R-18 | 单元测试 |
| AC-5.3 | US-5 | R-19 | 单元测试 |
| AC-5.4 | US-5 | R-20 | 单元测试 |
| AC-5.5 | US-5 | R-21 | 代码审查 sheet_content_cover_object.h:23 |
| AC-6.1 | US-6 | R-22 | 单元测试 |
| AC-6.2 | US-6 | R-23 | 单元测试 |
| AC-6.3 | US-6 | R-24 | 代码审查 |
| AC-7.1 | US-7 | R-25 | 单元测试 |
| AC-7.2 | US-7 | R-26 | 单元测试 |
| AC-7.3 | US-7 | R-27 | 单元测试 |
| AC-7.4 | US-7 | R-28 | 代码审查 sheet_presentation_pattern.cpp:1414 |
| AC-8.1 | US-8 | R-29 | 代码审查 overlay_manager.cpp:4195 |
| AC-8.2 | US-8 | R-30 | 代码审查 overlay_manager.cpp:4205 |
| AC-8.3 | US-8 | R-31 | 代码审查 overlay_manager.cpp:4241 |
| AC-8.4 | US-8 | R-32 | 代码审查 overlay_manager.cpp:4263 |
| AC-8.5 | US-8 | R-33 | 代码审查 sheet_presentation_pattern.cpp:3212/3227/3240/3254 |
| AC-9.1 | US-9 | R-34 | 单元测试 |
| AC-9.2 | US-9 | R-35 | 单元测试 |
| AC-9.3 | US-9 | R-36 | 代码审查 |
| AC-9.4 | US-9 | R-37 | 代码审查 |
| AC-10.1 | US-10 | R-38 | 单元测试 |
| AC-10.2 | US-10 | R-39 | 单元测试 |
| AC-10.3 | US-10 | R-40 | 单元测试 |
| AC-10.4 | US-10 | R-41 | 代码审查 |
| AC-11.1 | US-11 | R-42 | 代码审查 |
| AC-11.2 | US-11 | R-43 | 代码审查 view_abstract_model_ng.cpp:1226-1283 |
| AC-11.3 | US-11 | R-44 | 代码审查 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `js_popups.cpp:2491` ParseSheetIsShow | 检测 isShow 双向绑定 | — | AC-1.1 |
| R-2 | 行为 | bindSheet isShow | isShow 为状态变量，双向绑定 | — | AC-1.1 |
| R-3 | 行为 | `overlay_manager.cpp:3963` OnBindSheet | isShow=true 创建 FrameNode + SheetPresentationPattern 挂载 | — | AC-1.2 |
| R-4 | 行为 | bindSheet isShow=false | isShow=false 移除 Sheet | — | AC-1.3 |
| R-5 | 边界 | `js_popups.cpp:2530` SheetStyle 默认值 | sheetMode=LARGE/enableFloatingDragBar=false/showDragBar=true/showCloseIcon=true/showInPage=false | — | AC-1.4 |
| R-6 | 边界 | height=MEDIUM | pageHeight * mediumSize (API<=10: 0.5, else ~0.6) | `sheet_style.h` + `sheet_theme.h` GetMediumPercent | AC-2.1 |
| R-7 | 边界 | mediumSize 比例 | API<=10: 0.5, API>=11: ~0.6 | — | AC-2.1 |
| R-8 | 边界 | height=LARGE | largeHeight (GetLargePercent) | — | AC-2.2 |
| R-9 | 边界 | height=FIT_CONTENT | fitContent, capped at largeHeight | — | AC-2.3 |
| R-10 | 边界 | height 未指定 | 默认 LARGE | — | AC-2.4 |
| R-11 | 行为 | `js_popups.cpp:3002` ParseSheetDetents | 最多 3 档，升序排序，去重 | — | AC-3.1 |
| R-12 | 行为 | detents 拖拽 | 在 detents 档位间吸附 | — | AC-3.2 |
| R-13 | 边界 | detentSelection | 默认 detents[0] @since 15 | — | AC-3.3 |
| R-14 | 行为 | dragBar | dragBar 默认 true，显示 grabber | — | AC-4.1 |
| R-15 | 行为 | showClose | showClose 默认 true，显示关闭按钮 | `sheet_view.cpp:233` CLOSE_BUTTON | AC-4.2 |
| R-16 | 边界 | enableFloatingDragBar | 默认 false @since 20，悬浮态独立控制 | — | AC-4.3 |
| R-17 | 边界 | preferType=SHEET_BOTTOM | 底部 Sheet（默认） | — | AC-5.1 |
| R-18 | 行为 | preferType=CENTER | 中心 Sheet | — | AC-5.2 |
| R-19 | 行为 | preferType=POPUP | 弹窗 Sheet | — | AC-5.3 |
| R-20 | 行为 | preferType=SIDE | 侧边 Sheet | — | AC-5.4 |
| R-21 | 边界 | preferType=CONTENT_COVER | 全屏覆盖，无 drag/scroll/keyboard avoid/shadow/border | `sheet_content_cover_object.h:23` | AC-5.5 |
| R-22 | 行为 | title=SheetTitleOptions | 显示标题文本 | — | AC-6.1 |
| R-23 | 行为 | title=CustomBuilder | 显示自定义标题内容 | — | AC-6.2 |
| R-24 | 边界 | title 未设置 | 不显示标题区域 | — | AC-6.3 |
| R-25 | 行为 | shouldDismiss @since 11 | CallShouldDismiss 返回 false 时不关闭 | bool 回调 | AC-7.1 |
| R-26 | 行为 | onWillDismiss @since 12 | CallOnWillDismiss 提供 DismissSheetAction（dismiss + reason） | — | AC-7.2 |
| R-27 | 行为 | onWillSpringBackWhenDismiss @since 12 | 提供 SpringBackAction（springBack + reason） | — | AC-7.3 |
| R-28 | 边界 | shouldDismiss/onWillDismiss 未设置 | SheetInteractiveDismiss 直接 DismissTransition | `sheet_presentation_pattern.cpp:1414` | AC-7.4 |
| R-29 | 行为 | onWillAppear | Sheet 即将显示前触发 | `overlay_manager.cpp:4195` | AC-8.1 |
| R-30 | 行为 | onAppear | Sheet 已显示触发 | `overlay_manager.cpp:4205` | AC-8.2 |
| R-31 | 行为 | onWillDisappear | Sheet 即将隐藏前触发 | `overlay_manager.cpp:4241` | AC-8.3 |
| R-32 | 行为 | onDisappear | Sheet 已隐藏触发 | `overlay_manager.cpp:4263` | AC-8.4 |
| R-33 | 行为 | 高度/档位/宽度/类型变化 | onHeightDidChange L3212/onDetentsDidChange L3227/onWidthDidChange L3240/onTypeDidChange L3254 | `sheet_presentation_pattern.cpp` | AC-8.5 |
| R-34 | 边界 | mode=OVERLAY | 默认挂载 overlay 层 | — | AC-9.1 |
| R-35 | 行为 | mode=EMBEDDED | 挂载嵌入节点 | — | AC-9.2 |
| R-36 | 边界 | keyboardAvoidMode | 默认 TRANSLATE_AND_SCROLL @since 13 | — | AC-9.3 |
| R-37 | 边界 | scrollSizeMode | 默认 FOLLOW_DETENT | — | AC-9.4 |
| R-38 | 边界 | blurStyle | 默认 NONE，范围 NO_MATERIAL..COMPONENT_ULTRA_THICK | — | AC-10.1 |
| R-39 | 边界 | backgroundColor | 默认 White | — | AC-10.2 |
| R-40 | 行为 | maskColor | 遮罩使用指定颜色 | — | AC-10.3 |
| R-41 | 行为 | radius @since 15 | 应用指定圆角 | — | AC-10.4 |
| R-42 | 行为 | enableHoverMode | 默认 false @since 14，hoverModeArea 默认 BOTTOM_SCREEN | — | AC-11.1 |
| R-43 | 行为 | showInSubWindow | 默认 false @since 19，SubwindowManager::ShowBindSheetNG | `view_abstract_model_ng.cpp:1226-1283` | AC-11.2 |
| R-44 | 异常 | attributeModifier 限制 | bindSheet 不允许在 attributeModifier 中调用，抛出异常 | — | AC-11.3 |
| R-45 | 行为 | placement | 默认 Bottom @since 18 | — | — |
| R-46 | 行为 | placementOnTarget | 默认 true | — | — |
| R-47 | 行为 | effectEdge | 默认 3 @since 18 | — | — |
| R-48 | 行为 | modalTransition | 默认 DEFAULT，仅 preferType==CONTENT_COVER 生效 @since 20 | — | — |
| R-49 | 行为 | radiusRenderStrategy | 默认 FAST @since 23 | — | — |
| R-50 | 恢复 | SheetManager 清理 | CleanBindSheetMap 清理 sheetMap_，RemoveSheetByESC ESC 移除，RegisterDestroyCallback 销毁回调 | `sheet_manager.cpp` | — |
| R-51 | 异常 | 命令式 API 错误码 | ERROR_CODE_BIND_SHEET_CONTENT_ERROR/_ALREADY_EXIST/_NOT_FOUND | `js_view_context.cpp:98-100` | — |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 绑定与 isShow (AC-1.1~1.4) | 单元测试 + 代码审查 | ParseSheetIsShow 双向；SheetStyle 默认值 |
| VM-2 | US-2 height 模式 (AC-2.1~2.4) | 代码审查 | MEDIUM/LARGE/FIT_CONTENT；mediumSize 比例 |
| VM-3 | US-3 detents (AC-3.1~3.3) | 单元测试 + 代码审查 | 3 档升序去重；detentSelection |
| VM-4 | US-4 dragBar/showClose (AC-4.1~4.3) | 单元测试 + 代码审查 | grabber；CLOSE_BUTTON；enableFloatingDragBar |
| VM-5 | US-5 preferType (AC-5.1~5.5) | 单元测试 + 代码审查 | SHEET_BOTTOM/CENTER/POPUP/SIDE/CONTENT_COVER；SheetObject 策略 |
| VM-6 | US-6 title (AC-6.1~6.3) | 单元测试 | SheetTitleOptions/CustomBuilder |
| VM-7 | US-7 shouldDismiss/onWillDismiss/springBack (AC-7.1~7.4) | 单元测试 | 渐进式拦截链；DismissSheetAction；SpringBackAction |
| VM-8 | US-8 生命周期 (AC-8.1~8.5) | 代码审查 | onWillAppear/onAppear/onWillDisappear/onDisappear + 变化回调 |
| VM-9 | US-9 mode/keyboardAvoid (AC-9.1~9.4) | 单元测试 + 代码审查 | OVERLAY/EMBEDDED；TRANSLATE_AND_SCROLL；FOLLOW_DETENT |
| VM-10 | US-10 blur/bg/mask (AC-10.1~10.4) | 单元测试 | blurStyle NONE；backgroundColor White；maskColor；radius |
| VM-11 | US-11 hoverMode/子窗口/限制 (AC-11.1~11.3) | 代码审查 | enableHoverMode；showInSubWindow；attributeModifier 限制 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2491` ParseSheetIsShow |
| AC-1.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3963` OnBindSheet |
| AC-1.3 | 单元测试 | `test/unittest/core/pattern/sheet/` sheet_presentation_pattern_test |
| AC-1.4 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2530` |
| AC-2.1 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_style.h` + `sheet_theme.h` GetMediumPercent |
| AC-2.2 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_theme.h` GetLargePercent |
| AC-2.3 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_presentation_layout_algorithm.cpp` |
| AC-2.4 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2530` |
| AC-3.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:3002` ParseSheetDetents |
| AC-3.2 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-3.3 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_presentation_pattern.cpp` |
| AC-4.1 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-4.2 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_view.cpp:233` CLOSE_BUTTON |
| AC-4.3 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_presentation_pattern.cpp` |
| AC-5.1 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-5.2 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-5.3 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-5.4 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-5.5 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/content_cover/sheet_content_cover_object.h:23` |
| AC-6.1 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-6.2 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-6.3 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_presentation_pattern.cpp` |
| AC-7.1 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-7.2 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-7.3 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-7.4 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_presentation_pattern.cpp:1414` SheetInteractiveDismiss |
| AC-8.1 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:4195` |
| AC-8.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:4205` |
| AC-8.3 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:4241` |
| AC-8.4 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:4263` |
| AC-8.5 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_presentation_pattern.cpp:3212/3227/3240/3254` |
| AC-9.1 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-9.2 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-9.3 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_presentation_pattern.cpp` |
| AC-9.4 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_style.h` ScrollSizeMode |
| AC-10.1 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-10.2 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-10.3 | 单元测试 | `test/unittest/core/pattern/sheet/` |
| AC-10.4 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_style.h` |
| AC-11.1 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_presentation_pattern.cpp` |
| AC-11.2 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:1226-1283` |
| AC-11.3 | 代码审查 | `frameworks/core/components_ng/pattern/sheet/sheet_presentation_pattern.cpp`（attributeModifier 限制） |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/common.d.ts`

#### bindSheet

```typescript
// common.d.ts:23239 @since 10
bindSheet(isShow: boolean, builder: CustomBuilder, options?: SheetOptions): T;
```

#### 枚举与类型

```typescript
// common.d.ts:7842 @since 10
declare enum ModalTransition { DEFAULT = 0, NONE = 1, ALPHA = 2 }

// common.d.ts:8865 @since 10/11
declare enum SheetSize { MEDIUM, LARGE, FIT_CONTENT }

// common.d.ts:12403 @since 11
declare interface BindOptions {
    backgroundColor?: ResourceColor;
    onAppear?: () => void;
    onDisappear?: () => void;
    onWillAppear?: () => void;
    onWillDisappear?: () => void;
}

// common.d.ts:12844 @since 12
declare interface DismissSheetAction {
    dismiss(): void;
    reason: DismissReason;
}

// common.d.ts:12875 @since 12
declare interface SpringBackAction {
    springBack(): void;
    reason: DismissReason;
}

// common.d.ts:12918 @since 10
declare interface SheetOptions {
    height?: SheetSize | Dimension;              // default LARGE
    dragBar?: boolean;                           // default true
    maskColor?: ResourceColor;
    detents?: SheetSize[];                        // @since 11
    blurStyle?: BlurStyle;                        // default NONE
    showClose?: boolean;                          // default true
    preferType?: SheetType;                       // @since 11
    title?: SheetTitleOptions | CustomBuilder;
    shouldDismiss?: () => boolean;                // @since 11
    onWillDismiss?: (action: DismissSheetAction) => void;  // @since 12
    onWillSpringBackWhenDismiss?: (action: SpringBackAction) => void;  // @since 12
    enableOutsideInteractive?: boolean;           // default false
    width?: Dimension;                            // @since 12
    border?: ...;                                  // @since 12
    shadow?: Shadow | ShadowStyle;                 // @since 12
    onHeightDidChange?: ...;                      // @since 12
    onDetentsDidChange?: ...;                      // @since 12
    onWidthDidChange?: ...;                        // @since 12
    onTypeDidChange?: ...;                         // @since 12
    mode?: SheetMode;                              // default OVERLAY
    scrollSizeMode?: ScrollSizeMode;              // default FOLLOW_DETENT
    uiContext?: UIContext;
    keyboardAvoidMode?: SheetKeyboardAvoidMode;   // default TRANSLATE_AND_SCROLL @since 13
    enableHoverMode?: boolean;                     // default false @since 14
    hoverModeArea?: HoverModeArea;                 // default BOTTOM_SCREEN @since 14
    offset?: ...;                                  // systemapi @since 14
    effectEdge?: ...;                              // default 3 @since 18
    radius?: Dimension;                            // @since 15
    detentSelection?: ...;                         // default detents[0] @since 15
    placement?: Placement;                         // default Bottom @since 18
    placementOnTarget?: boolean;                    // default true
    showInSubWindow?: boolean;                     // default false @since 19
    enableFloatingDragBar?: boolean;               // default false @since 20
    modalTransition?: ModalTransition;             // default DEFAULT, only CONTENT_COVER @since 20
    radiusRenderStrategy?: ...;                    // default FAST @since 23
    systemMaterial?: ...;                          // @since 26
    edgeLightMode?: ...;                           // @since 26
    blurSnapshot?: ...;                            // systemapi @since 26
}

// common.d.ts:13487 @since 12/20
declare enum DismissReason {
    PRESS_BACK,     // @since 12
    TOUCH_OUTSIDE,  // @since 12
    CLOSE_BUTTON,   // @since 12
    SLIDE_DOWN,     // @since 12
    SLIDE           // @since 20
}
```

| 方法签名 | 返回类型 | 说明 | @since |
|----------|----------|------|--------|
| `bindSheet(isShow, builder, options?)` | T | 半模态弹窗绑定 | 10 |
| `UIContext.openBindSheet/updateBindSheet/closeBindSheet` | — | 命令式 API | — |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无废弃 API，SheetOptions 字段随版本增量扩展 |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 10 | bindSheet 基础 API，mediumSize=0.5 | — | 无需迁移 |
| API 11 | mediumSize 变更为 ~0.6；新增 detents/preferType/shouldDismiss | MEDIUM 高度比例变更 | 如需保持 0.5 显式设置 height |
| API 12 | 新增 onWillDismiss/onWillSpringBackWhenDismiss/width/border/shadow/变化回调 | 渐进式拦截链 | 如需拦截关闭迁移到 onWillDismiss |
| API 13 | keyboardAvoidMode 默认 TRANSLATE_AND_SCROLL | — | 如需其他避让显式设置 |
| API 14 | enableHoverMode 默认 false，hoverModeArea 默认 BOTTOM_SCREEN | — | 悬浮态需显式启用 |
| API 15 | radius/detentSelection | detentSelection 默认 detents[0] | 如需指定初始档位 |
| API 18 | placement 默认 Bottom，effectEdge 默认 3 | — | — |
| API 19 | showInSubWindow 默认 false | 子窗口分发 | 跨窗口场景显式启用 |
| API 20 | enableFloatingDragBar 默认 false，modalTransition 仅 CONTENT_COVER 生效，SLIDE dismiss reason | 悬浮态独立控制拖拽条 | 非 CONTENT_COVER 不应设置 modalTransition |
| API 23 | radiusRenderStrategy 默认 FAST | — | — |
| API 26 | systemMaterial/edgeLightMode/blurSnapshot | — | — |
| attributeModifier | bindSheet 不允许在 attributeModifier 中调用 | 抛出异常 | 使用正常属性链 |
| CONTENT_COVER | 无 drag/scroll/keyboard avoid/shadow/border | 行为差异 | 如需这些能力使用其他 preferType |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 多继承架构 | SheetPresentationPattern 继承 LinearLayoutPattern, PopupBasePattern, FocusView, NestableScrollContainer, AutoFillTriggerStateHolder, IAvoidInfoListener |
| SheetObject 策略模式 | SheetType 由 SheetObject 策略派生（SheetContentCoverObject/SheetSideObject/SheetMinimizeObject） |
| 双向 isShow | ParseSheetIsShow 检测 isShow 双向绑定 |
| 双分发路径 | showInSubWindow=true → SubwindowManager::ShowBindSheetNG；否则 overlayManager->BindSheet |
| 渐进式拦截链 | shouldDismiss→onWillDismiss→springBack，无则 DismissTransition |
| CONTENT_COVER 限制 | 无 drag/scroll/keyboard avoid/shadow/border |
| modalTransition 限制 | 仅 preferType==CONTENT_COVER 生效 |
| attributeModifier 限制 | bindSheet 不允许在 attributeModifier 中调用 |
| SheetManager 单例 | sheetMap_ 管理，OpenBindSheetByUIContext/Update/Close/CleanBindSheetMap/SetDismissSheet/RemoveSheetByESC/RegisterDestroyCallback |
| 命令式错误码 | ERROR_CODE_BIND_SHEET_CONTENT_ERROR/_ALREADY_EXIST/_NOT_FOUND |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | Sheet 为按需创建的浮层，拖拽/动画帧率 ≥ 60fps |
| 可调试性 | 提供 DumpInfo 用于 Inspector 诊断 Sheet 状态 |
| 可靠性 | SheetManager 正确清理 sheetMap_，子窗口正确销毁 |
| 问题定位 | hilog 标签 ACE_OVERLAY / ACE_SHEET 覆盖关键路径 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 默认底部 Sheet，键盘避让 TRANSLATE_AND_SCROLL | — | 手工 | — |
| 平板 | 同手机，宽度可定制（width @since 12） | — | 手工 | — |
| 折叠屏 | enableHoverMode 支持悬浮态，hoverModeArea 适配折叠态/展开态 | @since 14 | 手工 | — |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 无障碍 | Sheet 内容支持无障碍读取，显示时获取焦点（FocusView） |
| 大字体 | Sheet 文字跟随系统字体缩放 |
| 深色模式 | backgroundColor/maskColor 通过 ResourceColor 支持主题跟随，SheetTheme 适配 |
| 多窗口/分屏 | showInSubWindow 支持子窗口，modalMode 控制模态行为 |
| 多用户 | 无用户相关状态 |
| 版本升级 | API 10/11/12/13/14/15/18/19/20/23/26 持续演进，mediumSize 比例、detents、preferType、mode、keyboardAvoid、hoverMode 等变更 |
| 生态兼容 | 命令式 API（openBindSheet/updateBindSheet/closeBindSheet）支持 UIContext 调用 |

---

## 行为场景

### 场景 1: 显示 Sheet

```
Given 组件调用 bindSheet(isShow, builder, options?)
When isShow 设置为 true
Then ParseSheetIsShow 检测双向绑定
And OnBindSheet 创建 FrameNode + SheetPresentationPattern 挂载
And SheetStyle 默认值（sheetMode=LARGE/showDragBar=true/showCloseIcon=true）应用
And onWillAppear 触发，Sheet 显示后 onAppear 触发
```

### 场景 2: MEDIUM 高度模式

```
Given 组件设置 height = SheetSize.MEDIUM
When Sheet 布局
Then 高度 = pageHeight * mediumSize
And API<=10: mediumSize=0.5, API>=11: mediumSize~0.6
```

### 场景 3: detents 多档拖拽

```
Given 组件设置 detents = [MEDIUM, LARGE]
When 用户拖拽 Sheet
Then detents 升序排序去重
And Sheet 在 MEDIUM/LARGE 档位间吸附
And detentSelection 默认 detents[0]
```

### 场景 4: CONTENT_COVER 全屏覆盖

```
Given 组件设置 preferType = SheetType.CONTENT_COVER
When Sheet 显示
Then SheetContentCoverObject 策略生效
And 无 drag/scroll/keyboard avoid/shadow/border
And modalTransition 生效（默认 DEFAULT）
```

### 场景 5: shouldDismiss 拦截关闭

```
Given 组件设置 shouldDismiss = () => false
When 用户尝试关闭 Sheet
Then CallShouldDismiss 返回 false
Then Sheet 不关闭
```

### 场景 6: onWillDismiss 渐进式拦截

```
Given 组件设置 onWillDismiss
When 用户尝试关闭 Sheet
Then CallOnWillDismiss 触发
And 提供 DismissSheetAction（dismiss + reason）
And 开发者按 reason 决定是否调用 dismiss()
```

### 场景 7: 未设置拦截直接关闭

```
Given 组件未设置 shouldDismiss/onWillDismiss
When 用户尝试关闭 Sheet
Then SheetInteractiveDismiss 直接 DismissTransition
And onWillDisappear 触发，关闭后 onDisappear 触发
```

### 场景 8: 键盘避让

```
Given 组件 keyboardAvoidMode = TRANSLATE_AND_SCROLL（默认）
When 键盘弹出
Then Sheet 上移避让键盘
And 内容滚动避让
```

### 场景 9: 子窗口显示 Sheet

```
Given 组件设置 showInSubWindow = true
When bindSheet 执行
Then SubwindowManager::ShowBindSheetNG 创建子窗口
And Sheet 在子窗口显示
```

### 场景 10: attributeModifier 限制

```
Given 在 attributeModifier 中调用 bindSheet
When 执行
Then 抛出异常（不允许）
```

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 业务规则/功能规则/异常规则/恢复契约编号连续且可追溯到源码
- [x] API 变更分析基于真实 SDK 定义文件（common.d.ts）
- [x] 兼容性声明标注 API 版本差异
- [x] 行为场景使用 Gherkin Given/When/Then 格式，覆盖关键路径
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/pattern/sheet/sheet_presentation_pattern.h/.cpp` | SheetPresentationPattern 多继承架构（.cpp 5254 行） |
| `frameworks/core/components_ng/pattern/sheet/sheet_presentation_property.h` | SheetPresentationProperty（propSheetStyle_ PROPERTY_UPDATE_MEASURE） |
| `frameworks/core/components_ng/pattern/sheet/sheet_presentation_layout_algorithm.h/.cpp` | Sheet 布局算法 |
| `frameworks/core/components_ng/pattern/sheet/sheet_style.h` | SheetStyle 结构体、SheetMode/SheetType/BindSheetDismissReason/SheetLevel/ScrollSizeMode/SheetKeyboardAvoidMode/SheetHeight 枚举 |
| `frameworks/core/components_ng/pattern/sheet/sheet_manager.h/.cpp` | SheetManager 单例 |
| `frameworks/core/components_ng/pattern/sheet/sheet_object.h` | SheetObject 策略基类 + SheetContentCoverObject/SheetSideObject/SheetMinimizeObject |
| `frameworks/core/components_ng/pattern/sheet/sheet_view.cpp` | SheetView（CLOSE_BUTTON L233） |
| `frameworks/core/components_ng/pattern/sheet/sheet_drag_bar_*` | 拖拽条（grabber） |
| `frameworks/core/components_ng/pattern/sheet/sheet_mask_*` | 遮罩 |
| `frameworks/core/components_ng/pattern/sheet/sheet_theme.h` | SheetTheme |
| `frameworks/core/components_ng/pattern/sheet/content_cover/sheet_content_cover_object.h` | SheetContentCoverObject（L23，CONTENT_COVER） |
| `frameworks/core/components_ng/pattern/sheet/bridge/sheet_pattern_inner_modifier.h/.cpp` | sheetInteractiveDismiss（L29） |
| `frameworks/core/components_ng/pattern/sheet/bridge/sheet_manager_inner_modifier.h/.cpp` | open/update/closeBindSheetByUIContext |
| `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp` | BindSheet L3591 / OnBindSheet L3963 / OnBindSheetInner L4284 / OpenBindSheetByUIContext L4014 / Update L4039 / Close L4234 |
| `frameworks/core/components_ng/base/view_abstract_model_ng.cpp` | BindSheet L1226-1283 |
| `frameworks/core/components_ng/base/view_abstract_model_static.cpp` | 静态前端 BindSheet L873 |
| `frameworks/core/components_ng/base/view_context_model_ng.cpp` | OpenBindSheet L74 / Update L99 / Close L119 |
| `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp` | JsBindSheet L2512 + ParseSheetIsShow L2491 + ParseSheetStyle L2606 + ParseSheetHeight L3255 + ParseSheetDetents L3002 |
| `frameworks/bridge/declarative_frontend/jsview/js_view_context.cpp` | JSOpenBindSheet/JSUpdateBindSheet/JSCloseBindSheet 错误码 L98-100 |
| `adapter/ohos/window/subwindow_manager.h` | ShowBindSheetNG / ShowBindSheetByUIContext |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/sheet/` | Sheet NG 单元测试 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `interface/sdk-js/api/@internal/component/ets/common.d.ts` | ModalTransition/SheetSize/BindOptions/DismissSheetAction/SpringBackAction/SheetOptions/DismissReason/bindSheet 声明 |
