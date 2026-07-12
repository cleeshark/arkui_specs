# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | NavDestination 标题栏与工具栏配置 |
| 特性编号 | Func-05-02-03-Feat-02 |
| FuncID | 05-02-03 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 9 ~ API 19+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | title(string) 标题栏文本标题 | @since 9 |
| ADDED | hideTitleBar(hide: boolean) 标题栏显隐 | @since 9 |
| ADDED | hideTitleBar(hide: boolean, animated?: boolean) 标题栏动画显隐 | @since 10 |
| ADDED | title(CustomBuilder) 自定义标题 | @since 12 |
| ADDED | title(NavDestinationCommonTitle) 主+副标题结构 | @since 12 |
| ADDED | title(NavDestinationCustomTitle) 自定义标题+高度 | @since 14 |
| ADDED | backButtonIcon(value, accessibilityText?) 返回按钮图标 | @since 11，accessibilityText @since 12 |
| ADDED | backButtonIcon(SymbolGlyphModifier) 符号图标 | @since 12 |
| MODIFIED | hideTitleBar animated 参数扩展 | @since 10/11/13 递进 |
| ADDED | menus(Array\<NavigationMenuItem\>) 菜单项 | @since 12 |
| ADDED | menus(CustomBuilder) 自定义菜单 | @since 12 |
| ADDED | menus(options: NavigationMenuOptions) 菜单更多按钮选项 | @since 19 |
| ADDED | toolbarConfiguration(Array\<ToolbarItem\>) 工具栏项 | @since 13 |
| ADDED | toolbarConfiguration(CustomBuilder) 自定义工具栏 | @since 13 |
| ADDED | toolbarConfiguration(options: NavigationToolbarOptions) 工具栏选项 | @since 13 |
| ADDED | hideToolBar(hide: boolean, animated?: boolean) 工具栏动画显隐 | @since 13 |
| ADDED | hideBackButton(hide: Optional\<boolean\>) 返回按钮显隐 | @since 15 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/02-navigation-components/03-nav-destination/design.md`
- **KB 路由**: `docs/kb/components/navigation/navdestination.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/nav_destination.d.ts`
  - Static: `<OH_ROOT>/interface/sdk-js/api/arkui/component/nav_destination.static.d.ets`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: NavDestination 标题栏标题配置

**角色**: 应用开发者
**期望**: 我想要通过多种类型配置 NavDestination 的标题栏标题（文本/结构化/自定义）
**价值**: 以便在不同场景下灵活展示标题内容

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 设置 `title("页面标题")` THEN 标题栏显示纯文本标题，TitleBarNode.title 节点为 TextPattern FrameNode（`navdestination_model_ng.cpp:532-534`，ParseCommonTitle `hasSubTitle=false, hasMainTitle=true`） | 正常 |
| AC-1.2 | WHEN 设置 `title({ main: "主标题", sub: "副标题" })` (NavDestinationCommonTitle) THEN 标题栏同时显示主标题和副标题，主标题 maxLines=1，副标题 maxLines=1（`navdestination_model_ng.cpp:80, 46-128`） | 正常 |
| AC-1.3 | WHEN 设置 `title($r('app.string.title'))` (Resource) THEN 标题栏显示资源字符串标题，通过 ResourceParseUtils 解析（`navdestination_model_ng.cpp:130-151`） | 正常 |
| AC-1.4 | WHEN 设置 `title(() => { Row() { ... } })` (CustomBuilder) THEN 标题栏使用自定义节点渲染，navDestinationNode.UpdatePrevTitleIsCustom(true)，titleBarNode.SetTitle(customTitle)（`navdestination_model_ng.cpp:797-824`） | 正常 |
| AC-1.5 | WHEN 设置 `title({ builder: () => {...}, height: 100 })` (NavDestinationCustomTitle) THEN 标题栏使用自定义 Builder 渲染，同时设置 titleHeight=100（`navdestination_model_ng.cpp:827-843`） | 正常 |
| AC-1.6 | WHEN 先设置 CustomBuilder 标题后设置 string 标题 THEN 移除 customTitle 子节点并创建 TextPattern 标题节点，navDestinationNode.UpdatePrevTitleIsCustom(false)（`navdestination_model_ng.cpp:60-71`） | 边界 |
| AC-1.7 | WHEN NavDestinationCommonTitle 仅设 main 不设 sub THEN 副标题节点不存在，主标题 maxLines=TITLEBAR_MAX_LINES（`navdestination_model_ng.cpp:98-102`） | 正常 |

### US-2: NavDestination 标题栏显隐与动画

**角色**: 应用开发者
**期望**: 我想要控制 NavDestination 标题栏的显隐，支持动画和非动画两种方式
**价值**: 以便在页面切换或内容滚动时平滑过渡标题栏

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 设置 `hideTitleBar(true)` THEN 标题栏立即隐藏，titleBarLayoutProperty.UpdateVisibility(VisibleType::GONE)，titleBarNode.SetJSViewActive(false)（`navdestination_pattern_base.cpp:211-213`） | 正常 |
| AC-2.2 | WHEN 设置 `hideTitleBar(false)` THEN 标题栏立即显示，titleBarLayoutProperty.UpdateVisibility(VisibleType::VISIBLE)，titleBarNode.SetJSViewActive(true)（`navdestination_pattern_base.cpp:215-217`） | 正常 |
| AC-2.3 | WHEN 设置 `hideTitleBar(true, animated: true)` THEN 标题栏播放 translate+opacity 动画隐藏，动画从 TRANSLATE_ZERO 到 TRANSLATE_HEIGHT，duration=500ms，curve=FAST_OUT_SLOW_IN（`navdestination_pattern_base.cpp:365-396`，DEFAULT_ANIMATION_DURATION `navdestination_pattern_base.cpp:32`） | 正常 |
| AC-2.4 | WHEN 设置 `hideTitleBar(false, animated: true)` THEN 标题栏播放 translate+opacity 动画显示，动画从 TRANSLATE_HEIGHT 到 TRANSLATE_ZERO，先更新 translate 到 TRANSLATE_HEIGHT 起点（`navdestination_pattern_base.cpp:139-141, 189-191`） | 正常 |
| AC-2.5 | WHEN 标题栏动画正在进行 THEN BarTranslateState 为 TRANSLATE_ZERO 或 TRANSLATE_HEIGHT（非 NONE），titleBarAnimationCount_ > 0（`navdestination_layout_property_base.h:56-60`，`navdestination_pattern_base.h:207-213`） | 正常 |
| AC-2.6 | WHEN 标题栏动画完成 THEN BarTranslateState 恢复为 NONE，调用 HideOrShowTitleBarImmediately 将标题栏设为最终显隐状态（`navdestination_pattern_base.cpp:398-411`） | 正常 |
| AC-2.7 | WHEN 设置 `hideTitleBar(true, animated: false)` THEN 标题栏立即隐藏（等同 AC-2.1），IsAnimatedTitleBar=false，currHideTitleBar_ 无值时走 HideOrShowTitleBarImmediately（`navdestination_pattern.cpp:346-349`） | 正常 |
| AC-2.8 | WHEN 标题栏从显示切换到隐藏（animated=true）THEN 先将 translate 和 opacity 重置到 0（即显示态起点），再播放动画（`navdestination_pattern.cpp:339-344`） | 正常 |
| AC-2.9 | WHEN TitleBar zIndex THEN 标题栏浮动在内容之上，zIndex=DEFAULT_TITLEBAR_ZINDEX=2（`navdestination_pattern.cpp:36, 153`） | 正常 |

### US-3: NavDestination 返回按钮

**角色**: 应用开发者
**期望**: 我想要控制 NavDestination 返回按钮的显隐和图标样式
**价值**: 以便定制返回按钮的外观和行为

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `hideBackButton(true)` THEN 返回按钮立即隐藏，backButtonLayoutProperty.UpdateVisibility(VisibleType::GONE)（`navdestination_pattern.cpp:318-319`） | 正常 |
| AC-3.2 | WHEN 设置 `hideBackButton(false)` THEN 返回按钮显示，backButtonLayoutProperty.UpdateVisibility(VisibleType::VISIBLE)（`navdestination_pattern.cpp:318-319`） | 正常 |
| AC-3.3 | WHEN hideTitleBar=true 且 TitleBarTranslateState=NONE THEN 返回按钮不可见，GetBackButtonState() 返回 false（`navdestination_pattern.cpp:367-369`） | 边界 |
| AC-3.4 | WHEN NavigationMode=SPLIT 且 NavDestination index=0（非 FullScreenOverlay）THEN 返回按钮不可见，showBackButton=false（`navdestination_pattern.cpp:396-398`） | 边界 |
| AC-3.5 | WHEN hideNavBar=true THEN index==0 的 NavDestination 返回按钮不可见（`navdestination_pattern.cpp:397`） | 边界 |
| AC-3.6 | WHEN hideBackButton=true THEN 返回按钮始终隐藏，无论其他条件（navDestinationLayoutProperty->GetHideBackButtonValue(false) 为 true 时 showBackButton=false）（`navdestination_pattern.cpp:393-394`） | 正常 |
| AC-3.7 | WHEN 设置 `backButtonIcon(src)` (ResourceStr) THEN 返回按钮图标替换为指定图片，titleBarLayoutProperty.UpdateImageSource(ImageSourceInfo(src))（`navdestination_model_ng.cpp:596-597`） | 正常 |
| AC-3.8 | WHEN 设置 `backButtonIcon(SymbolGlyphModifier)` THEN 返回按钮图标替换为符号图标，titleBarLayoutProperty.SetBackIconSymbol(symbolApply)（`navdestination_model_ng.cpp:600`） | 正常 |
| AC-3.9 | WHEN 设置 `backButtonIcon(value, accessibilityText)` THEN 返回按钮设置无障碍文本，NavigationTitleUtil::SetAccessibility(backButtonNode, accessibilityText)（`navdestination_model_ng.cpp:604-609`） | 正常 |
| AC-3.10 | WHEN backButtonIcon 使用 PixelMap THEN NavDestinationLayoutProperty.UpdatePixelMap(pixMap) 且 UpdateNoPixMap(false)（`navdestination_layout_property.h:57-59`，`navdestination_model_ng.cpp:598-599`） | 正常 |
| AC-3.11 | WHEN NavDestination 为 forceSplitUseNavBar 首页 THEN 返回按钮隐藏（`navdestination_pattern.cpp:404-406`） | 边界 |
| AC-3.12 | WHEN backButtonIcon 设置改变 THEN 触发 SetNeedResetTitleProperty 以更新标题栏属性（`navdestination_model_ng.cpp:527`） | 正常 |

### US-4: NavDestination 菜单项配置

**角色**: 应用开发者
**期望**: 我想要在 NavDestination 标题栏右侧配置菜单项（数组或自定义）
**价值**: 以便提供操作入口或功能按钮

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 `menus([NavigationMenuItem{...}])` THEN 标题栏右侧创建菜单项，navDestinationPattern.SetTitleBarMenuItems(menuItems)，navDestinationPattern.SetMenuNodeId(newId)（`navdestination_model_ng.cpp:1139-1160`） | 正常 |
| AC-4.2 | WHEN 设置 `menus(() => { Row() { ... } })` (CustomBuilder) THEN 标题栏右侧使用自定义菜单节点，navDestinationGroupNode.UpdatePrevMenuIsCustom(true)，ChildNodeOperation=ADD（`navdestination_model_ng.cpp:1187-1210`） | 正常 |
| AC-4.3 | WHEN 先设置 CustomBuilder 菜单后设置 NavigationMenuItem 数组 THEN 旧自定义菜单节点被标记为 ChildNodeOperation::REPLACE，新菜单项创建（`navdestination_model_ng.cpp:1146-1154`） | 边界 |
| AC-4.4 | WHEN 菜单项数量超过 MAXIMUM_TOOLBAR_ITEMS_IN_BAR(5) THEN 创建"更多"按钮菜单（`navigation_toolbar_util.cpp:667, 113`） | 边界 |
| AC-4.5 | WHEN 设置 `menus(value, { MoreButtonOptions })` (NavigationMenuOptions) THEN navDestinationPattern.SetMenuOptions(opt)，MoreButtonOptions 配置更多按钮背景样式（`navdestination_model_ng.cpp:1212-1250`） | 正常 |
| AC-4.6 | WHEN BuildMenu 执行 THEN 菜单节点根据 prevMenuIsCustom 和 menuNodeOperation 分发：REPLACE 时移除旧菜单并添加新菜单，NONE 时保持不变（`navdestination_pattern.cpp:40-87`） | 正常 |
| AC-4.7 | WHEN 菜单项 BuildMenu 且 prevMenuIsCustom=false THEN 从 navDestinationPattern.GetTitleBarMenuItems() 和 GetToolBarMenuItems() 构建 menu 和 landscapeMenu（`navdestination_pattern.cpp:56-87`） | 正常 |

### US-5: NavDestination 工具栏配置

**角色**: 应用开发者
**期望**: 我想要在 NavDestination 底部配置工具栏项和显隐
**价值**: 以便提供底部操作按钮和工具区域

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 设置 `toolbarConfiguration([ToolbarItem{...}])` THEN 底部创建工具栏项，NavigationToolbarUtil::SetToolbarConfiguration(navDestinationGroupNode, toolBarItems, enabled, fieldProperty)（`navdestination_model_ng.cpp:1655-1724`） | 正常 |
| AC-5.2 | WHEN 设置 `toolbarConfiguration(() => { Row() { ... } })` (CustomBuilder) THEN 底部使用自定义工具栏节点，NavigationToolbarUtil::SetCustomToolBar(navDestinationGroupNode, customNode)（`navdestination_model_ng.cpp:1726-1732`） | 正常 |
| AC-5.3 | WHEN 设置 `toolbarConfiguration(toolbarParam, { NavigationToolbarOptions })` THEN NavigationToolbarUtil::SetToolbarOptions 和 SetToolbarMoreButtonOptions 分别设置 barStyle 和更多按钮选项（`navigation_toolbar_util.cpp:718-772`） | 正常 |
| AC-5.4 | WHEN 设置 `hideToolBar(true)` THEN 工具栏立即隐藏，toolBarLayoutProperty.UpdateVisibility(VisibleType::GONE)，toolBarNode.SetActive(false)（`navdestination_pattern_base.cpp:250-252`） | 正常 |
| AC-5.5 | WHEN 设置 `hideToolBar(false)` THEN 工具栏立即显示，toolBarLayoutProperty.UpdateVisibility(VisibleType::VISIBLE)，toolBarNode.SetActive(true)（`navdestination_pattern_base.cpp:256-261`） | 正常 |
| AC-5.6 | WHEN 设置 `hideToolBar(true, animated: true)` THEN 工具栏播放 translate+opacity 动画隐藏，ToolBarTranslateState 从 TRANSLATE_ZERO 到 TRANSLATE_HEIGHT，duration=500ms，curve=FAST_OUT_SLOW_IN（`navdestination_pattern_base.cpp:365-396`） | 正常 |
| AC-5.7 | WHEN 设置 `hideToolBar(false, animated: true)` THEN 工具栏播放动画显示，ToolBarTranslateState 从 TRANSLATE_HEIGHT 到 TRANSLATE_ZERO（`navdestination_pattern_base.cpp:146-149`） | 正常 |
| AC-5.8 | WHEN 工具栏动画完成 THEN ToolBarTranslateState 恢复为 NONE，调用 HideOrShowToolBarImmediately 设置最终状态（`navdestination_pattern_base.cpp:413-426`） | 正常 |
| AC-5.9 | WHEN 工具栏无有效内容(toolBarNode.HasValidContent()=false) THEN 工具栏隐藏，VisibleType::GONE（`navdestination_pattern_base.cpp:250`） | 边界 |
| AC-5.10 | WHEN 工具栏因 NavWidth 不足而需隐藏 THEN IsNeedHideToolBarForNavWidth()=true，ToolBarTranslateState 重置为 NONE，跳过动画（`navdestination_pattern_base.cpp:180-183`） | 边界 |
| AC-5.11 | WHEN 工具栏 dividerNode 存在 THEN dividerNode 与 toolBarNode 同步显隐和动画（`navdestination_pattern_base.cpp:245-267, 270-290`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.7 | R-1, R-2, R-3 | TASK-NAVDEST-02 | UT | navdestination title 单测 |
| AC-2.1 ~ AC-2.9 | R-4, R-5, R-6, R-7, R-8 | TASK-NAVDEST-02 | UT + 手工 | titleBar 动画和显隐测试 |
| AC-3.1 ~ AC-3.12 | R-9, R-10, R-11, R-12 | TASK-NAVDEST-02 | UT | backButton 显隐和图标测试 |
| AC-4.1 ~ AC-4.7 | R-13, R-14, R-15 | TASK-NAVDEST-02 | UT | menus 配置测试 |
| AC-5.1 ~ AC-5.11 | R-16, R-17, R-18, R-19 | TASK-NAVDEST-02 | UT + 手工 | toolbar 配置和动画测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `navdestination_model_ng.cpp:532-534` | title(string) 通过 ParseCommonTitle(hasSubTitle=false, hasMainTitle=true) 创建纯文本标题 | — | AC-1.1 |
| R-2 | 行为 | `navdestination_model_ng.cpp:46-128` | NavDestinationCommonTitle 分发：hasMainTitle 创建/更新主标题节点，hasSubTitle 创建/更新副标题节点，互不设时移除对应节点 | — | AC-1.2, AC-1.7 |
| R-3 | 行为 | `navdestination_model_ng.cpp:797-824` | title(CustomBuilder) 设置 customTitle 到 titleBarNode.SetTitle()，UpdatePrevTitleIsCustom(true)；切换回 string 时移除 custom 节点并 UpdatePrevTitleIsCustom(false) | — | AC-1.4, AC-1.6 |
| R-4 | 行为 | `navdestination_model_ng.cpp:512-515` | hideTitleBar(hide, animated) 写入 NavDestinationLayoutProperty.HideTitleBar 和 IsAnimatedTitleBar | — | AC-2.1, AC-2.3 |
| R-5 | 行为 | `navdestination_pattern.cpp:303-357` | MountTitleBar 分发：currHideTitleBar_ 无值或 IsAnimatedTitleBar=false → HideOrShowTitleBarImmediately；IsAnimatedTitleBar=true 且状态变化 → needRunTitleBarAnimation=true | — | AC-2.3, AC-2.7 |
| R-6 | 行为 | `navdestination_pattern_base.cpp:365-396` | StartAnimation: duration=DEFAULT_ANIMATION_DURATION=500ms, curve=FAST_OUT_SLOW_IN，titleBarAnimationCount_++/toolBarAnimationCount_++ | — | AC-2.3, AC-5.6 |
| R-7 | 行为 | `navdestination_layout_property_base.h:56-60` | BarTranslateState 枚举：NONE(0)=非动画态，TRANSLATE_ZERO(1)=显示态动画起点/终点，TRANSLATE_HEIGHT(2)=隐藏态动画起点/终点 | — | AC-2.5, AC-2.6 |
| R-8 | 行为 | `navdestination_pattern_base.cpp:139-153` | UpdateLayoutPropertyBeforeAnimation: hideTitleBar → TRANSLATE_ZERO → TRANSLATE_HEIGHT；showTitleBar → TRANSLATE_HEIGHT → TRANSLATE_ZERO | — | AC-2.4, AC-5.7 |
| R-9 | 行为 | `navdestination_pattern.cpp:360-429` | GetBackButtonState: hideTitleBar+TranslateState=NONE → false；SPLIT+index=0 → false；hideNavBar → false；hideBackButton=true → false；forceSplitUseNavBar+index=0 → false | — | AC-3.3 ~ AC-3.6, AC-3.11 |
| R-10 | 行为 | `navdestination_model_ng.cpp:582-611` | backButtonIcon 设置：ImageSourceInfo 写入 titleBarLayoutProperty.UpdateImageSource，Symbol 写入 SetBackIconSymbol，PixelMap 写入 UpdatePixelMap/UpdateNoPixMap | — | AC-3.7 ~ AC-3.10 |
| R-11 | 行为 | `navdestination_model_ng.cpp:604-609` | backButtonIcon accessibilityText: userDefined=true → SetAccessibility(backButtonNode, text)；userDefined=false → 使用 theme->GetNavigationBack() 默认文本 | — | AC-3.9 |
| R-12 | 行为 | `navdestination_model_ng.cpp:518-530` | hideBackButton 写入 NavDestinationLayoutProperty.HideBackButton，且触发 SetNeedResetTitleProperty 更新标题栏属性 | — | AC-3.1, AC-3.2, AC-3.12 |
| R-13 | 行为 | `navdestination_model_ng.cpp:1139-1185` | menus(NavigationMenuItem[]) 写入 titleBarMenuItems_，设置 menuNodeId 和 landscapeMenuNodeId，UpdatePrevMenuIsCustom(false) | — | AC-4.1 |
| R-14 | 行为 | `navdestination_model_ng.cpp:1187-1210` | menus(CustomBuilder) 设置自定义菜单节点到 navDestinationGroupNode.SetMenu()，UpdatePrevMenuIsCustom(true) | — | AC-4.2 |
| R-15 | 行为 | `navdestination_model_ng.cpp:1212-1250` | menus(NavigationMenuOptions) 通过 navDestinationPattern.SetMenuOptions(opt) 写入 MoreButtonOptions | — | AC-4.5 |
| R-16 | 行为 | `navdestination_model_ng.cpp:1607-1616` | hideToolBar(hide, animated) 写入 NavDestinationLayoutProperty.HideToolBar 和 IsAnimatedToolBar | — | AC-5.4, AC-5.6 |
| R-17 | 行为 | `navigation_toolbar_util.cpp:774-821` | MountToolBar 分发：currHideToolBar 无值或 IsAnimatedToolBar=false → HideOrShowToolBarImmediately；IsAnimatedToolBar=true 且状态变化 → needRunToolBarAnimation=true | — | AC-5.4, AC-5.6 |
| R-18 | 行为 | `navigation_toolbar_util.cpp:635-683` | SetToolbarConfiguration: 构建 toolBarItems，设置 dividerNode，>MAXIMUM_TOOLBAR_ITEMS_IN_BAR 时创建 moreButton | — | AC-5.1 |
| R-19 | 行为 | `navdestination_pattern_base.cpp:224-236` | UpdateTitleBarTranslateAndOpacity: hide → offsetY=-titleBarHeight, opacity=0.0f；show → offsetY=0, opacity=1.0f | — | AC-2.3, AC-2.4 |
| R-20 | 行为 | `navdestination_pattern_base.cpp:270-290` | UpdateToolBarAndDividerTranslateAndOpacity: hide → offsetY=toolBarHeight+dividerHeight, opacity=0.0f；show → offsetY=0, opacity=1.0f | — | AC-5.6, AC-5.7 |
| R-21 | 边界 | `navdestination_pattern_base.cpp:413-426` | ToolBar 动画完成回调：ResetToolBarTranslateState → NONE，调用 HideOrShowToolBarImmediately 设置最终显隐状态 | — | AC-5.8 |
| R-22 | 边界 | `navdestination_pattern_base.cpp:180-183` | IsNeedHideToolBarForNavWidth=true 时，ResetToolBarTranslateState，跳过动画 | — | AC-5.10 |
| R-23 | 边界 | `navigation_declaration.h:113` | MAXIMUM_TOOLBAR_ITEMS_IN_BAR=5，超过时创建 moreButton | — | AC-4.4 |
| R-24 | 异常 | — | backButtonIcon 设置 null/undefined 值时，不更新图标属性（CHECK_NULL_VOID 保护） | navdestination_model_ng.cpp:592-600 | — |
| R-25 | 异常 | — | menus 设置空数组时，不创建菜单节点（menuItems.size()==0） | navigation_toolbar_util.cpp:667 | — |
| R-26 | 恢复 | `navdestination_pattern_base.cpp:428-437` | AbortBarAnimation: 遍历 barAnimations_，StopAnimation 所有活跃动画 | — | — |
| R-27 | 恢复 | `navdestination_pattern_base.cpp:398-411, 413-426` | 动画完成后 ResetTitleBarTranslateState/ResetToolBarTranslateState 恢复为 NONE | — | AC-2.6, AC-5.8 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.7 | UT | title 四种类型分发和切换 |
| VM-2 | AC-2.1 ~ AC-2.9 | UT + 手工 | hideTitleBar 非动画/动画显隐 |
| VM-3 | AC-3.1 ~ AC-3.12 | UT | backButton 显隐规则和图标 |
| VM-4 | AC-4.1 ~ AC-4.7 | UT | menus 数组/自定义/选项 |
| VM-5 | AC-5.1 ~ AC-5.11 | UT + 手工 | toolbarConfiguration 和 hideToolBar |
| VM-6 | R-7, R-19, R-20 | UT | BarTranslateState 枚举和 translate/opacity 计算 |
| VM-7 | R-9 | UT | backButton 多条件隐藏优先级 |
| VM-8 | R-26, R-27 | UT | 动画中断和完成恢复 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC | @since |
|----------|------|----------|---------|--------|
| title(value: string, options?) | Public | 纯文本标题 | AC-1.1 | 9 |
| title(value: CustomBuilder, options?) | Public | 自定义标题 | AC-1.4 | 12 |
| title(value: NavDestinationCommonTitle, options?) | Public | 主+副标题 | AC-1.2 | 12 |
| title(value: NavDestinationCustomTitle, options?) | Public | 自定义标题+高度 | AC-1.5 | 14 |
| title(value: Resource, options?) | Public | 资源字符串标题 | AC-1.3 | 9 |
| hideTitleBar(hide: boolean) | Public | 非动画隐藏标题栏 | AC-2.1 | 9 |
| hideTitleBar(hide: boolean, animated?: boolean) | Public | 动画隐藏/显示标题栏 | AC-2.3 | 10 |
| hideBackButton(hide: Optional\<boolean\>) | Public | 隐藏返回按钮 | AC-3.1 | 15 |
| backButtonIcon(value: ResourceStr \| PixelMap, accessibilityText?) | Public | 返回按钮图标 | AC-3.7, AC-3.9 | 11 |
| backButtonIcon(value: SymbolGlyphModifier, accessibilityText?) | Public | 返回按钮符号图标 | AC-3.8 | 12 |
| menus(value: Array\<NavigationMenuItem\>) | Public | 菜单项数组 | AC-4.1 | 12 |
| menus(value: CustomBuilder) | Public | 自定义菜单 | AC-4.2 | 12 |
| menus(value, options: NavigationMenuOptions) | Public | 菜单项+更多按钮选项 | AC-4.5 | 19 |
| toolbarConfiguration(toolbarParam: Array\<ToolbarItem\>) | Public | 工具栏项数组 | AC-5.1 | 13 |
| toolbarConfiguration(toolbarParam: CustomBuilder) | Public | 自定义工具栏 | AC-5.2 | 13 |
| toolbarConfiguration(toolbarParam, options: NavigationToolbarOptions) | Public | 工具栏项+选项 | AC-5.3 | 13 |
| hideToolBar(hide: boolean, animated?: boolean) | Public | 动画隐藏/显示工具栏 | AC-5.6 | 13 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| hideTitleBar | 参数扩展 | @since 9 无 animated → @since 10 增加 animated 参数 |

> 截至当前版本，本 Feat 涉及的 API 无 @deprecated 或 @useinstead 标注。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

**title 类型分发规则：**

| title 类型 | 实现路径 | 说明 |
|------------|----------|------|
| string | ParseCommonTitle(hasSubTitle=false, hasMainTitle=true, "", title) | 纯文本标题，单行或多行 |
| Resource | ParseCommonTitle(hasSubTitle, hasMainTitle, subResObj, mainResObj) → ResourceParseUtils | 资源字符串标题 |
| NavDestinationCommonTitle | ParseCommonTitle(hasSubTitle=true, hasMainTitle=true, subtitle, title) | 主+副结构化标题 |
| NavDestinationCustomTitle | SetCustomTitle(customNode) + SetTitleHeight(height) | 自定义 Builder + 高度 |
| CustomBuilder | SetCustomTitle(customNode) → titleBarNode.SetTitle(customTitle) | 自定义标题节点 |

**BarTranslateState 动画状态机：**

| 场景 | 起始状态 | 目标状态 | 触发 |
|------|----------|----------|------|
| hideTitleBar(animated) | TRANSLATE_ZERO | TRANSLATE_HEIGHT | MountTitleBar 判定 needRunTitleBarAnimation |
| showTitleBar(animated) | TRANSLATE_HEIGHT | TRANSLATE_ZERO | MountTitleBar 判定 needRunTitleBarAnimation |
| 动画完成 | TRANSLATE_HEIGHT/TRANSLATE_ZERO | NONE | OnTitleBarAnimationFinish / OnToolBarAnimationFinish |
| 非动画/初始 | NONE | NONE | HideOrShowTitleBarImmediately / HideOrShowToolBarImmediately |

**返回按钮可见性优先级链：**

1. hideTitleBar=true + BarTranslateState=NONE → 不可见（最高优先级）
2. hideBackButton=true → 不可见
3. SPLIT mode + index=0（非 FullScreenOverlay） → 不可见
4. hideNavBar=true → index=0 不可见
5. forceSplitUseNavBar=true + index=0 → 不可见
6. 其他 → 可见

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - hideTitleBar: API 9 仅 (hide: boolean)，API 10+ 增加 (animated?: boolean)，默认 animated=false（行为兼容）
  - hideBackButton: API 15 新增，参数类型 Optional\<boolean\>（支持 undefined 恢复默认）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** title(string) @since 9，title(CustomBuilder/CommonTitle) @since 12，title(NavDestinationCustomTitle) @since 14，toolbarConfiguration/hideToolBar @since 13，menus(options) @since 19，hideBackButton @since 15

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| NavDestinationPattern 继承 NavDestinationPatternBase | titleBarStyle_/toolBarStyle_/menuOptions_/barAnimations_ 定义在 Base，MountTitleBar/MountToolBar 分发在 NavDestinationPattern | AC-2.1 ~ AC-2.9, AC-5.1 ~ AC-5.11 |
| MountTitleBar/MountToolBar 在 OnModifyDone 中串行执行 | OnModifyDone 调用顺序：UpdateHideBarProperty → MountTitleBar → NavigationToolbarUtil::MountToolBar → HandleTitleBarAndToolBarAnimation（`navdestination_pattern.cpp:166-174`） | AC-2.3, AC-5.6 |
| NavigationToolbarUtil 静态工具类 | SetToolbarConfiguration/SetCustomToolBar/SetToolbarOptions/SetToolbarMoreButtonOptions 为 static 方法，不持有状态 | AC-5.1 ~ AC-5.3 |
| BarTranslateState 仅用于动画 | NONE=非动画态，TRANSLATE_ZERO/TRANSLATE_HEIGHT 仅在 animated=true 时使用，动画完成重置为 NONE | AC-2.5, AC-5.8 |
| titleBar zIndex=2 | DEFAULT_TITLEBAR_ZINDEX=2 使标题栏浮动在内容之上（`navdestination_pattern.cpp:36`） | AC-2.9 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | titleBar/toolBar 动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 性能 | titleBar/toolBar 显隐动画 duration=500ms | UT | DEFAULT_ANIMATION_DURATION 常量 |
| 内存 | barAnimations_ 动画对象在完成/中断后释放 | UT | RemoveAnimation/AbortBarAnimation |
| 安全 | backButtonIcon 不泄露 PixelMap 引用 | 代码审查 | UpdateNoPixMap/UpdatePixelMap |
| 可靠性 | hideTitleBar/hideToolBar 动画可中断 | UT | AbortBarAnimation |
| 问题定位 | hilog 标签覆盖 titleBar/toolBar 显隐和动画关键路径 | 代码审查 | TAG_LOGI(ACE_NAVIGATION) |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | SPLIT mode 下 index=0 返回按钮隐藏 | R-9 | UT | backButton SPLIT 测试 |
| 折叠屏 | forceSplit 场景返回按钮特殊处理 | R-9 | 手工 | forceSplit 测试 |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | backButtonIcon 支持 accessibilityText，返回按钮无障碍文本默认使用 theme->GetNavigationBack() | AC-3.9 |
| 大字体 | 是 | 主标题 maxFontScale=STANDARD_FONT_SCALE=1.0，副标题 maxFontScale=1.0，标题栏字号随系统缩放 | AC-1.2 |
| 深色模式 | 是 | 颜色属性通过 Resource 支持 Theme 跟随 | AC-3.7 |
| 多窗口/分屏 | 是 | SPLIT mode 和 forceSplit 影响返回按钮可见性和 toolBar NavWidth 隐藏 | AC-3.4, AC-5.10 |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | hideTitleBar animated 参数 @since 10 扩展，hideBackButton @since 15 新增，toolbarConfiguration @since 13 新增 | AC-2.3, AC-3.1 |
| 生态兼容 | 是 | Dynamic API 和 Static API (NavDestinationModelStatic) 均实现本 Feat 接口 | — |

## 行为场景（Gherkin）

```gherkin
Feature: NavDestination 标题栏与工具栏配置
  作为应用开发者
  我想要配置 NavDestination 的标题栏标题、返回按钮、菜单、工具栏及显隐动画
  以便灵活定制导航页面的顶部和底部区域

  Scenario: 设置纯文本标题
    Given NavDestination 组件创建
    When 设置 title("页面标题")
    Then 标题栏显示 TextPattern 文本节点，hasMainTitle=true, hasSubTitle=false
    And 主标题 maxLines=TITLEBAR_MAX_LINES

  Scenario: 设置 NavDestinationCommonTitle 主+副标题
    Given NavDestination 组件创建
    When 设置 title({ main: "主标题", sub: "副标题" })
    Then 标题栏同时显示主标题和副标题
    And 主标题 maxLines=1，副标题 maxLines=1

  Scenario: 设置 CustomBuilder 标题
    Given NavDestination 组件创建
    When 设置 title(() => { Row() { ... } })
    Then 标题栏使用自定义节点渲染
    And prevTitleIsCustom=true

  Scenario: 从 CustomBuilder 切换到 string 标题
    Given NavDestination 已设置 CustomBuilder 标题
    When 设置 title("新标题")
    Then 移除 customTitle 子节点
    And 创建 TextPattern 标题节点
    And prevTitleIsCustom=false

  Scenario: hideTitleBar 非动画隐藏
    Given NavDestination 组件创建
    When 设置 hideTitleBar(true)
    Then 标题栏 visibility=GONE，JSViewActive=false
    And titleBarOffsetY=0, opacity=1.0（无动画残留）

  Scenario: hideTitleBar 动画隐藏
    Given NavDestination 标题栏当前为显示状态
    When 设置 hideTitleBar(true, animated: true)
    Then TitleBarTranslateState 从 TRANSLATE_ZERO 到 TRANSLATE_HEIGHT
    And 播放 translate+opacity 动画，duration=500ms，curve=FAST_OUT_SLOW_IN
    And titleBarAnimationCount_++

  Scenario: hideTitleBar 动画完成后
    Given NavDestination 标题栏动画隐藏正在进行
    When 动画完成
    Then TitleBarTranslateState 恢复为 NONE
    And 调用 HideOrShowTitleBarImmediately 设置最终隐藏状态

  Scenario: hideBackButton 始终隐藏返回按钮
    Given NavDestination 组件创建
    When 设置 hideBackButton(true)
    Then 返回按钮 visibility=GONE
    And GetBackButtonState() 返回 false，无论其他条件

  Scenario: SPLIT mode index=0 返回按钮隐藏
    Given Navigation 为 SPLIT mode
    And NavDestination 为栈中 index=0 且非 FullScreenOverlay
    Then GetBackButtonState() 返回 false，返回按钮不显示

  Scenario: backButtonIcon 设置图标和 accessibilityText
    Given NavDestination 组件创建
    When 设置 backButtonIcon("icon.png", "返回上一页")
    Then 返回按钮图标更新为 ImageSourceInfo("icon.png")
    And backButton 无障碍文本为 "返回上一页"

  Scenario: menus NavigationMenuItem 数组
    Given NavDestination 组件创建
    When 设置 menus([NavigationMenuItem{icon: "icon1", text: "菜单1"}])
    Then navDestinationPattern.titleBarMenuItems_ 包含该菜单项
    And prevMenuIsCustom=false

  Scenario: menus CustomBuilder 自定义菜单
    Given NavDestination 组件创建
    When 设置 menus(() => { Row() { ... } })
    Then 标题栏使用自定义菜单节点
    And prevMenuIsCustom=true

  Scenario: toolbarConfiguration ToolbarItem 数组
    Given NavDestination 组件创建
    When 设置 toolbarConfiguration([ToolbarItem{icon: "icon1", text: "操作1"}])
    Then 底部工具栏创建对应 BarItemNode

  Scenario: hideToolBar 动画隐藏
    Given NavDestination 工具栏当前为显示状态
    When 设置 hideToolBar(true, animated: true)
    Then ToolBarTranslateState 从 TRANSLATE_ZERO 到 TRANSLATE_HEIGHT
    And 播放 translate+opacity 动画，duration=500ms
    And dividerNode 同步动画

  Scenario: hideToolBar 动画完成后
    Given NavDestination 工具栏动画隐藏正在进行
    When 动画完成
    Then ToolBarTranslateState 恢复为 NONE
    And 调用 HideOrShowToolBarImmediately 设置最终隐藏状态

  Scenario: 工具栏因 NavWidth 不足而跳过动画
    Given NavDestination IsNeedHideToolBarForNavWidth()=true
    When 执行 MountToolBar
    Then ToolBarTranslateState 重置为 NONE
    And needRunToolBarAnimation=false，跳过动画
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "NavDestination title bar type dispatch ParseCommonTitle SetCustomTitle"
  - repo: "openharmony/ace_engine"
    query: "NavDestination hideTitleBar hideToolBar animated BarTranslateState animation"
  - repo: "openharmony/ace_engine"
    query: "NavDestination backButton visibility GetBackButtonState hideBackButton backButtonIcon"
  - repo: "openharmony/ace_engine"
    query: "NavDestination menus toolbarConfiguration NavigationToolbarUtil MountToolBar"
```

**关键文档:**
- 源码入口: `frameworks/core/components_ng/pattern/navrouter/navdestination_model_ng.cpp`
- 源码入口: `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.cpp`
- 源码入口: `frameworks/core/components_ng/pattern/navigation/navdestination_pattern_base.cpp`
- 源码入口: `frameworks/core/components_ng/pattern/navigation/navigation_toolbar_util.cpp`
- 布局属性: `frameworks/core/components_ng/pattern/navigation/navdestination_layout_property_base.h`
- 事件 Hub: `frameworks/core/components_ng/pattern/navrouter/navdestination_event_hub.h`
- 声明: `frameworks/core/components_ng/pattern/navigation/navigation_declaration.h`
- 选项: `frameworks/core/components_ng/pattern/navigation/navigation_options.h`
