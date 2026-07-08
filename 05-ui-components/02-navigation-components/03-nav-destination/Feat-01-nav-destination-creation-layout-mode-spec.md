# 特性规格

## 概述

本规格定义 NavDestination 组件的创建与布局模式特性，涵盖 NavDestination 页面的三种创建方式（无参、builder、builder+navPathInfo）、NavDestinationMode 模式选择（STANDARD/DIALOG）、安全区与系统控制属性（ignoreLayoutSafeArea、preferredOrientation、enableStatusBar、enableNavigationIndicator、fullScreenOverlay）、滚动绑定（bindToScrollable、bindToNestedScrollable）以及 NavDestinationContext 上下文获取（onReady 回调及 NavDestinationContext 属性）。

注册表标识：Func-05-02-01-Feat-08（目录内使用 Feat-01）。

## 本次变更范围（Delta）

| Delta 编号 | 描述 | API 版本 |
|---|---|---|
| D-1 | NavDestination() 无参创建 | @since 9 |
| D-2 | NavDestination(builder) 带 builder 创建 | @since 10 |
| D-3 | NavDestination(builder, navPathInfo) 带 builder+navPathInfo 创建 | @since 11 |
| D-4 | mode(NavDestinationMode) STANDARD/DIALOG 模式选择 | @since 11（STANDARD），DIALOG @since 12 |
| D-5 | ignoreLayoutSafeArea(types, edges) 安全区忽略 | @since 12 |
| D-6 | fullScreenOverlay(Optional\<boolean\>) 全屏覆盖 | @since 26 |
| D-7 | preferredOrientation(Optional\<Orientation\>) 页面方向 | @since 19 |
| D-8 | enableStatusBar(Optional\<boolean\>, animated?: boolean) 状态栏控制 | @since 19 |
| D-9 | enableNavigationIndicator(Optional\<boolean\>) 导航指示器控制 | @since 19 |
| D-10 | bindToScrollable(Array\<Scroller\>) 滚动绑定 | @since 14 |
| D-11 | bindToNestedScrollable(Array\<NestedScrollInfo\>) 嵌套滚动绑定 | @since 14 |
| D-12 | NavDestinationContext 属性（pathInfo, pathStack, navDestinationId, mode, getConfigInRouteMap） | @since 11/12 |
| D-13 | onReady(Callback\<NavDestinationContext\>) 上下文就绪回调 | @since 11 |

## 输入文档

| 文档 | 版本/日期 |
|---|---|
| OpenHarmony ArkUI NavDestination API 参考文档 | API Version 12+ |
| NavDestinationPattern 源码 | `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.h/.cpp` |
| NavDestinationModelNG 源码 | `frameworks/core/components_ng/pattern/navrouter/navdestination_model_ng.h/.cpp` |
| NavDestinationModelStatic 源码 | `frameworks/core/components_ng/pattern/navrouter/navdestination_model_static.h/.cpp` |
| NavDestinationLayoutProperty 源码 | `frameworks/core/components_ng/pattern/navrouter/navdestination_layout_property.h` |
| NavDestinationLayoutPropertyBase 源码 | `frameworks/core/components_ng/pattern/navigation/navdestination_layout_property_base.h` |
| NavDestinationGroupNode 源码 | `frameworks/core/components_ng/pattern/navrouter/navdestination_group_node.h` |
| NavDestinationContext 源码 | `frameworks/core/components_ng/pattern/navrouter/navdestination_context.h` |
| JSNavDestination 源码 | `frameworks/bridge/declarative_frontend/jsview/js_navdestination.cpp/.h` |
| nav_destination_modifier.cpp 源码 | `frameworks/core/interfaces/native/node/nav_destination_modifier.cpp` |

## 用户故事

### US-1: 创建 NavDestination 页面

| 字段 | 内容 |
|---|---|
| 用户故事 | 作为应用开发者，我希望通过三种创建方式创建 NavDestination 页面，以灵活支持简单页面、带延迟渲染的页面和带路由信息的页面 |
| AC-1 | NavDestination() 无参调用时，NavDestinationModelNG::Create() 创建 NavDestinationGroupNode 节点并压入 ViewStackProcessor（源码 `navdestination_model_ng.cpp:257-291`） |
| AC-2 | NavDestination(builder) 单参调用时，JSNavDestination::Create(info) 检测 info[0]->IsFunction()，创建 ShallowBuilder 并传入 NavDestinationModelNG::Create(deepRenderFunc, context)（源码 `js_navdestination.cpp:320-341`） |
| AC-3 | NavDestination(builder, navPathInfo) 双参调用时，JSNavDestination::Create(info) 检测 info[0]->IsFunction() && info[1]->IsObject()，提取 moduleName/pagePath 并设置到 NavDestinationGroupNode（源码 `js_navdestination.cpp:360-382`） |
| AC-4 | NavDestinationModelStatic::CreateFrameNode 创建静态版本 NavDestination，pattern 设置 isStatic=true（源码 `navdestination_model_static.cpp:334-389`） |
| AC-5 | NavDestination 构造完成后自动生成 navDestinationId（通过 g_navDestinationPatternNextAutoGenId 自增，源码 `navdestination_pattern.cpp:34,105,110`） |
| AC-6 | NavDestination 构造完成后 API >= VERSION_ELEVEN 时自动设置安全区展开（SAFE_AREA_TYPE_SYSTEM | SAFE_AREA_TYPE_CUTOUT, SAFE_AREA_EDGE_ALL，源码 `navdestination_pattern.cpp:437-441`） |

### US-2: NavDestination 模式选择

| 字段 | 内容 |
|---|---|
| 用户故事 | 作为应用开发者，我希望选择 NavDestination 的显示模式为 STANDARD（全屏宽度）或 DIALOG（弹窗样式），以适配不同页面展示需求 |
| AC-1 | mode(NavDestinationMode.STANDARD) 时 NavDestinationGroupNode 默认 mode_ = NavDestinationMode::STANDARD（源码 `navdestination_group_node.h:333`） |
| AC-2 | mode(NavDestinationMode.DIALOG) 时 backgroundColor 默认为 Color::TRANSPARENT（源码 `navdestination_pattern.cpp:288-290`） |
| AC-3 | NavDestinationModelNG::SetNavDestinationMode(frameNode, mode) 调用 navDestinationNode->SetNavDestinationMode(mode)（源码 `navdestination_model_ng.cpp:1108-1113`） |
| AC-4 | NavDestinationModelStatic::SetNavDestinationMode(frameNode, mode) 调用 navDestinationNode->SetNavDestinationMode(mode.value_or(NavDestinationMode::STANDARD))（源码 `navdestination_model_static.cpp:421-427`） |
| AC-5 | JSNavDestination::SetMode(info) 中非数字参数时默认设为 NavDestinationMode::STANDARD（源码 `js_navdestination.cpp:576-583`） |
| AC-6 | C API SetNavDestinationMode 重置时默认 NavDestinationMode::STANDARD（源码 `nav_destination_modifier.cpp:126-131`） |
| AC-7 | NavDestinationMode.DIALOG 模式下 preferredOrientation 不生效（源码 `navdestination_pattern.cpp:993-996`） |
| AC-8 | NavDestinationMode.DIALOG 模式下 enableStatusBar 不生效（源码 `navdestination_pattern.cpp:1043-1046`） |
| AC-9 | NavDestinationMode.DIALOG 模式下 enableNavigationIndicator 不生效（源码 `navdestination_pattern.cpp:1086-1088`） |

### US-3: NavDestination 安全区与系统控制

| 字段 | 内容 |
|---|---|
| 用户故事 | 作为应用开发者，我希望通过 ignoreLayoutSafeArea、preferredOrientation、enableStatusBar、enableNavigationIndicator、fullScreenOverlay 属性控制 NavDestination 的安全区、页面方向、状态栏、导航指示器和全屏覆盖行为 |
| AC-1 | ignoreLayoutSafeArea(types, edges) 设置内容节点的 IgnoreLayoutSafeAreaOpts，作用于 contentNode 的 LayoutProperty（源码 `navdestination_model_ng.cpp:1400-1411`） |
| AC-2 | NavDestinationLayoutPropertyBase 中 IgnoreLayoutSafeArea 属性声明为 PROPERTY_UPDATE_MEASURE（源码 `navdestination_layout_property_base.h:100`） |
| AC-3 | C API SetIgnoreLayoutSafeArea 空字符串时设为 SAFE_AREA_TYPE_NONE/SAFE_AREA_EDGE_NONE（源码 `nav_destination_modifier.cpp:156-159`） |
| AC-4 | C API ResetIgnoreLayoutSafeArea 恢复默认值 SAFE_AREA_TYPE_SYSTEM(0b1)/SAFE_AREA_EDGE_ALL(0b1111)（源码 `nav_destination_modifier.cpp:22-23,187-195`） |
| AC-5 | preferredOrientation 设置 NavDestinationGroupNode->SetOrientation(ori)（源码 `navdestination_model_ng.cpp:2072-2087`） |
| AC-6 | preferredOrientation 仅在 IsPageLevelConfigEnabled() && IsFullPageNavigation() 条件下生效（源码 `navdestination_pattern.cpp:1014-1017`） |
| AC-7 | enableStatusBar(enable, animated) 存储 pair\<bool,bool\> 到 NavDestinationGroupNode->SetStatusBarConfig（源码 `navdestination_model_ng.cpp:2089-2105`） |
| AC-8 | enableStatusBar 仅在 IsPageLevelConfigEnabled() && IsFullPageNavigation() 条件下生效（源码 `navdestination_pattern.cpp:1064-1067`） |
| AC-9 | enableStatusBar 调用 WindowManager->SetWindowSystemBarEnabled(SystemBarType::STATUS, enable, animated)（源码 `navdestination_pattern.cpp:1079`） |
| AC-10 | enableNavigationIndicator 存储 optional\<bool\> 到 NavDestinationGroupNode->SetNavigationIndicatorConfig（源码 `navdestination_model_ng.cpp:2107-2123`） |
| AC-11 | enableNavigationIndicator 仅在 IsPageLevelConfigEnabled() && IsFullPageNavigation() 条件下生效（源码 `navdestination_pattern.cpp:1107-1109`） |
| AC-12 | enableNavigationIndicator 调用 WindowManager->SetWindowSystemBarEnabled(SystemBarType::NAVIGATION_INDICATOR, enable, nullopt)（源码 `navdestination_pattern.cpp:1120`） |
| AC-13 | fullScreenOverlay 设置 NavDestinationLayoutProperty->UpdateFullScreenOverlay/ResetFullScreenOverlay，并调用 NotifyFullScreenOverlayRequestChange 重新排列 Navigation 内容/覆盖容器（源码 `navdestination_model_ng.cpp:1635-1653`） |
| AC-14 | fullScreenOverlay=true 时 NavDestination 被移动到 Navigation 的 overlay 容器中，覆盖下层页面（源码 `navdestination_pattern.cpp:196-231`） |
| AC-15 | NavDestinationLayoutPropertyBase 中 FullScreenOverlay 属性声明为 PROPERTY_UPDATE_MEASURE（源码 `navdestination_layout_property_base.h:105`） |
| AC-16 | C API SetFullScreenOverlay 将 ArkUIOptionalBool 转为 optional\<bool\> 调用 NavDestinationModelNG::SetFullScreenOverlay（源码 `nav_destination_modifier.cpp:691-707`） |

### US-4: NavDestination 滚动绑定

| 字段 | 内容 |
|---|---|
| 用户故事 | 作为应用开发者，我希望通过 bindToScrollable/bindToNestedScrollable 将 NavDestination 内部滚动组件与外部 Scroller/NestedScrollInfo 关联，以实现联动滚动和 titleBar/toolBar 的自动隐藏/显示 |
| AC-1 | bindToScrollable(scrollers) 调用 NavDestinationModelNG::UpdateBindingWithScrollable 传入绑定回调，JSNavDestinationScrollableProcessor::BindToScrollable 处理 Scroller 数组（源码 `js_navdestination.cpp:842-854`） |
| AC-2 | bindToNestedScrollable(infos) 调用 NavDestinationModelNG::UpdateBindingWithScrollable 传入绑定回调，JSNavDestinationScrollableProcessor::BindToNestedScrollable 处理 NestedScrollInfo 数组（源码 `js_navdestination.cpp:856-868`） |
| AC-3 | NavDestinationModelNG::SetScrollableProcessor 创建 NavDestinationScrollableProcessor 并设置 nodeId 和 navDestinationPattern（源码 `navdestination_model_ng.cpp:1827-1845`） |
| AC-4 | C API ResetBindToScrollable 调用 UnbindScrollable 解绑（源码 `nav_destination_modifier.cpp:1019-1028`） |
| AC-5 | C API ResetBindToNestedScrollable 调用 UnbindNestedScrollable 解绑（源码 `nav_destination_modifier.cpp:1040-1049`） |
| AC-6 | NavDestinationPattern 析构时 scrollableProcessor_->UnbindAllScrollers()（源码 `navdestination_pattern.cpp:116-118`） |
| AC-7 | NavDestinationPattern::OnModifyDone 中 scrollableProcessor_->UpdateBindingRelation() 更新绑定关系（源码 `navdestination_pattern.cpp:184-186`） |

### US-5: NavDestinationContext 上下文获取

| 字段 | 内容 |
|---|---|
| 用户故事 | 作为应用开发者，我希望通过 onReady 回调获取 NavDestinationContext 对象，从中读取 pathInfo、pathStack、navDestinationId、mode 等属性 |
| AC-1 | onReady(callback) 注册回调到 NavDestinationEventHub::SetOnReady（源码 `navdestination_model_ng.cpp:974-991`） |
| AC-2 | NavDestinationContext 包含 pathInfo_(RefPtr\<NavPathInfo\>)，可通过 GetNavPathInfo() 获取（源码 `navdestination_context.h:98-106`） |
| AC-3 | NavDestinationContext 包含 navigationStack_(WeakPtr\<NavigationStack\>)，可通过 GetNavigationStack() 获取（源码 `navdestination_context.h:108-116`） |
| AC-4 | NavDestinationContext 包含 navDestinationId_(uint64_t)，可通过 GetNavDestinationId() 获取（源码 `navdestination_context.h:138-146`） |
| AC-5 | NavDestinationContext 包含 mode_(NavDestinationMode)，可通过 GetMode()/SetMode() 读写（源码 `navdestination_context.h:158-166`） |
| AC-6 | NavDestinationContext 包含 index_(int32_t) 和 preIndex_(int32_t)，可通过 GetIndex()/GetPreIndex() 获取（源码 `navdestination_context.h:118-136`） |
| AC-7 | NavDestinationContext 包含 uniqueId_(int32_t)，由 NavDestinationGroupNode->GetId() 设置（源码 `navdestination_context.h:168-176`） |
| AC-8 | NavDestinationContext 包含 curSize_(optional\<SizeF\>)，跟踪当前 NavDestination 尺寸（源码 `navdestination_context.h:178-185`） |
| AC-9 | NavDestinationContext 与 NavDestinationPattern 双向关联：context->SetNavDestinationPattern(WeakClaim(pattern))，pattern->SetNavDestinationContext(context)（源码 `navdestination_pattern.h:128-135`） |

## 验收追溯

| Delta | US | AC | 规则 | 验证方式 |
|---|---|---|---|---|
| D-1 | US-1 | AC-1 | R-1 | UT: NavDestinationModelNG::Create 无参路径 |
| D-2 | US-1 | AC-2 | R-2 | UT: JSNavDestination::Create 单参 builder 路径 |
| D-3 | US-1 | AC-3 | R-3 | UT: JSNavDestination::Create 双参 builder+navPathInfo 路径 |
| D-4 | US-2 | AC-1~AC-9 | R-4~R-12 | UT: NavDestinationMode 设置与 DIALOG 限制路径 |
| D-5 | US-3 | AC-1~AC-4 | R-13~R-16 | UT: ignoreLayoutSafeArea 作用于 contentNode |
| D-6 | US-3 | AC-13~AC-16 | R-17~R-20 | UT: fullScreenOverlay 容器重排列 |
| D-7 | US-3 | AC-5~AC-6 | R-21~R-22 | UT: preferredOrientation 限制条件 |
| D-8 | US-3 | AC-7~AC-9 | R-23~R-25 | UT: enableStatusBar 限制条件与 WindowManager 调用 |
| D-9 | US-3 | AC-10~AC-12 | R-26~R-28 | UT: enableNavigationIndicator 限制条件与 WindowManager 调用 |
| D-10 | US-4 | AC-1~AC-7 | R-29~R-35 | UT: bindToScrollable/bindToNestedScrollable 绑定与解绑 |
| D-11 | US-4 | AC-1~AC-7 | R-29~R-35 | UT: 同 D-10 |
| D-12 | US-5 | AC-2~AC-9 | R-36~R-43 | UT: NavDestinationContext 属性读写 |
| D-13 | US-5 | AC-1 | R-44 | UT: onReady 回调注册 |

## 规则定义

| 规则 ID | 描述 | 类型 | 关联源码 |
|---|---|---|---|
| R-1 | NavDestination() 无参创建调用 NavDestinationModelNG::Create()，创建 NavDestinationGroupNode 并压入 ViewStackProcessor | 行为 | `navdestination_model_ng.cpp:257-291` |
| R-2 | NavDestination(builder) 创建时通过 ShallowBuilder 包装 deepRenderFunc，支持延迟内容渲染 | 行为 | `navdestination_model_ng.cpp:461-510` |
| R-3 | NavDestination(builder, navPathInfo) 创建时提取 moduleName/pagePath 设置到 NavDestinationGroupNode | 行为 | `js_navdestination.cpp:360-382` |
| R-4 | NavDestinationGroupNode 默认 mode_ = NavDestinationMode::STANDARD | 行为 | `navdestination_group_node.h:333` |
| R-5 | NavDestinationMode.DIALOG 时 backgroundColor 默认为 Color::TRANSPARENT | 行为 | `navdestination_pattern.cpp:288-290` |
| R-6 | NavDestinationMode.STANDARD 时 backgroundColor 默认为 AppTheme->GetBackgroundColor | 行为 | `navdestination_pattern.cpp:292-301` |
| R-7 | 用户自定义 backgroundColor 时不自动设置（IsUserDefinedBgColor=true 跳过自动设置） | 行为 | `navdestination_pattern.cpp:283-287` |
| R-8 | JSNavDestination::SetMode(info) 非数字参数时默认 STANDARD | 异常 | `js_navdestination.cpp:576-579` |
| R-9 | NavDestinationMode.DIALOG 时 preferredOrientation 不生效并打印日志 | 边界 | `navdestination_pattern.cpp:993-996` |
| R-10 | NavDestinationMode.DIALOG 时 enableStatusBar 不生效并打印日志 | 边界 | `navdestination_pattern.cpp:1043-1046` |
| R-11 | NavDestinationMode.DIALOG 时 enableNavigationIndicator 不生效并打印日志 | 边界 | `navdestination_pattern.cpp:1086-1088` |
| R-12 | C API ResetNavDestinationMode 重置为 STANDARD | 恢复 | `nav_destination_modifier.cpp:126-131` |
| R-13 | ignoreLayoutSafeArea 作用于 contentNode 的 LayoutProperty，而非 NavDestination 根节点 | 行为 | `navdestination_model_ng.cpp:1400-1411` |
| R-14 | NavDestinationLayoutProperty 中 IgnoreLayoutSafeArea 属性使用 PROPERTY_UPDATE_MEASURE 标志 | 行为 | `navdestination_layout_property_base.h:100` |
| R-15 | C API ignoreLayoutSafeArea 空字符串参数时设为 NONE/NONE（不做安全区忽略） | 异常 | `nav_destination_modifier.cpp:156-159` |
| R-16 | C API ResetIgnoreLayoutSafeArea 恢复默认 SAFE_AREA_TYPE_SYSTEM/SAFE_AREA_EDGE_ALL | 恢复 | `nav_destination_modifier.cpp:187-195` |
| R-17 | fullScreenOverlay 设置时先读取 previousRequest，再更新/重置 NavDestinationLayoutProperty 的 FullScreenOverlay 属性 | 行为 | `navdestination_model_ng.cpp:1644-1649` |
| R-18 | fullScreenOverlay 变化时调用 NotifyFullScreenOverlayRequestChange 触发 Navigation 重新排列 content/overlay 容器 | 行为 | `navdestination_pattern.cpp:196-231` |
| R-19 | fullScreenOverlay 变化时 Navigation 调用 UpdateNavDestinationNodeWithoutMarkDirty + MarkDirtyNode(PROPERTY_UPDATE_MEASURE_SELF_AND_CHILD) | 行为 | `navdestination_pattern.cpp:209-212` |
| R-20 | NavDestinationLayoutProperty 中 FullScreenOverlay 属性使用 PROPERTY_UPDATE_MEASURE 标志 | 行为 | `navdestination_layout_property_base.h:105` |
| R-21 | preferredOrientation 仅在 Navigation IsPageLevelConfigEnabled() && IsFullPageNavigation() 条件下生效 | 边界 | `navdestination_pattern.cpp:1014-1017` |
| R-22 | preferredOrientation 首次设置时仅记录 preOrientation 不执行方向变更 | 行为 | `navdestination_pattern.cpp:1000-1004` |
| R-23 | enableStatusBar 仅在 Navigation IsPageLevelConfigEnabled() && IsFullPageNavigation() 条件下生效 | 边界 | `navdestination_pattern.cpp:1064-1067` |
| R-24 | enableStatusBar 首次设置时仅记录 preStatusBarConfig 不执行状态栏变更 | 行为 | `navdestination_pattern.cpp:1050-1053` |
| R-25 | enableStatusBar 调用 WindowManager->SetWindowSystemBarEnabled(SystemBarType::STATUS, enable, animated) | 行为 | `navdestination_pattern.cpp:1079` |
| R-26 | enableNavigationIndicator 仅在 Navigation IsPageLevelConfigEnabled() && IsFullPageNavigation() 条件下生效 | 边界 | `navdestination_pattern.cpp:1107-1109` |
| R-27 | enableNavigationIndicator 首次设置时仅记录 preNavigationIndicatorConfig 不执行导航指示器变更 | 行为 | `navdestination_pattern.cpp:1093-1096` |
| R-28 | enableNavigationIndicator 调用 WindowManager->SetWindowSystemBarEnabled(SystemBarType::NAVIGATION_INDICATOR, enable, nullopt) | 行为 | `navdestination_pattern.cpp:1120` |
| R-29 | bindToScrollable 通过 NavDestinationScrollableProcessor 绑定 Scroller 数组 | 行为 | `js_navdestination.cpp:842-854` |
| R-30 | bindToNestedScrollable 通过 NavDestinationScrollableProcessor 绑定 NestedScrollInfo 数组 | 行为 | `js_navdestination.cpp:856-868` |
| R-31 | NavDestinationScrollableProcessor 创建时设置 nodeId 和 navDestinationPattern(WeakPtr) | 行为 | `navdestination_model_ng.cpp:1838-1842` |
| R-32 | NavDestinationPattern::OnModifyDone 中 scrollableProcessor_->UpdateBindingRelation() 更新绑定 | 行为 | `navdestination_pattern.cpp:184-186` |
| R-33 | C API ResetBindToScrollable 调用 processor->UnbindScrollable() | 恢复 | `nav_destination_modifier.cpp:1023-1027` |
| R-34 | C API ResetBindToNestedScrollable 调用 processor->UnbindNestedScrollable() | 恢复 | `nav_destination_modifier.cpp:1044-1048` |
| R-35 | NavDestinationPattern 析构时 scrollableProcessor_->UnbindAllScrollers() 清理所有绑定 | 恢复 | `navdestination_pattern.cpp:116-118` |
| R-36 | NavDestinationContext.pathInfo 为 RefPtr\<NavPathInfo\>，通过 GetNavPathInfo() 获取 | 行为 | `navdestination_context.h:98-106` |
| R-37 | NavDestinationContext.navigationStack 为 WeakPtr\<NavigationStack\>，通过 GetNavigationStack() 获取 | 行为 | `navdestination_context.h:108-116` |
| R-38 | NavDestinationContext.navDestinationId 为 uint64_t，通过 GetNavDestinationId() 获取 | 行为 | `navdestination_context.h:138-146` |
| R-39 | NavDestinationContext.mode 为 NavDestinationMode，通过 GetMode()/SetMode() 读写 | 行为 | `navdestination_context.h:158-166` |
| R-40 | NavDestinationContext.index/preIndex 为 int32_t，默认 -1 | 行为 | `navdestination_context.h:191-192` |
| R-41 | NavDestinationContext.uniqueId 由 navDestinationNode->GetId() 设置 | 行为 | `navdestination_model_ng.cpp:489` |
| R-42 | NavDestinationContext.curSize 为 optional\<SizeF\>，跟踪当前 NavDestination 尺寸 | 行为 | `navdestination_context.h:178-185` |
| R-43 | NavDestinationContext 与 NavDestinationPattern 双向关联，context->SetNavDestinationPattern(WeakClaim(this)) | 行为 | `navdestination_pattern.h:132` |
| R-44 | onReady 回调注册到 NavDestinationEventHub::SetOnReady | 行为 | `navdestination_model_ng.cpp:974-991` |
| R-45 | API >= VERSION_ELEVEN 时 NavDestination 自动设置安全区展开 SAFE_AREA_TYPE_SYSTEM | SAFE_AREA_TYPE_CUTOUT, SAFE_AREA_EDGE_ALL | 行为 | `navdestination_pattern.cpp:437-441` |
| R-46 | API >= VERSION_ELEVEN 时 contentNode 创建也自动设置安全区展开 | 行为 | `navdestination_model_ng.cpp:219-235` |
| R-47 | NavDestinationModelNG 使用 ViewStackProcessor + 单例模式获取实例 | 行为 | `js_navdestination.cpp:39-49` |
| R-48 | NavDestinationModelStatic 使用全静态方法，无实例，直接操作 FrameNode | 行为 | `navdestination_model_static.h:30-82` |
| R-49 | NavDestinationGroupNode 包含 titleBarNode、contentNode、toolBarNode 子节点槽位 | 行为 | NavDestinationNodeBase 继承 + `navdestination_group_node.h:37-38` |
| R-50 | navDestinationId 通过 g_navDestinationPatternNextAutoGenId.fetch_add(1) 自增 | 行为 | `navdestination_pattern.cpp:34,105,110` |
| R-51 | NavDestinationLayoutProperty 所有属性声明使用 PROPERTY_UPDATE_MEASURE 标志 | 行为 | `navdestination_layout_property.h:57-59, navdestination_layout_property_base.h:97-105` |
| R-52 | NavDestinationPattern::OnAttachToFrameNode 中为 VERSION_ELEVEN+ 自动安全区展开 | 行为 | `navdestination_pattern.cpp:437-441` |

## 验证映射

| 规则 | UT 测试点 | 测试路径 |
|---|---|---|
| R-1 | Create() 无参路径创建 NavDestinationGroupNode | `test/unittest/components_ng/navdestination/navdestination_model_ng_test.cpp` |
| R-2 | Create(deepRenderFunc) 带 ShallowBuilder 创建 | 同上 |
| R-3 | Create(builder, navPathInfo) 双参创建并设置 pathInfo | 同上 |
| R-4 | 默认 mode 为 STANDARD | `test/unittest/components_ng/navdestination/navdestination_group_node_test.cpp` |
| R-5 | DIALOG 模式 backgroundColor 为 TRANSPARENT | `test/unittest/components_ng/navdestination/navdestination_pattern_test.cpp` |
| R-6 | STANDARD 模式 backgroundColor 为 theme 默认 | 同上 |
| R-7 | 用户自定义 backgroundColor 不被覆盖 | 同上 |
| R-8 | 非数字 mode 参数默认 STANDARD | JS UT |
| R-9~R-11 | DIALOG 模式系统控制不生效 | `test/unittest/components_ng/navdestination/navdestination_pattern_test.cpp` |
| R-13 | ignoreLayoutSafeArea 作用于 contentNode | C API UT: `capi_all_modifiers_test` |
| R-17~R-19 | fullScreenOverlay 触发容器重排列 | `test/unittest/components_ng/navdestination/navdestination_pattern_test.cpp` |
| R-21~R-28 | preferredOrientation/enableStatusBar/enableNavigationIndicator 条件限制 | 同上 |
| R-29~R-35 | 滚动绑定与解绑 | `test/unittest/components_ng/navdestination/navdestination_scrollable_processor_test.cpp` |
| R-36~R-44 | NavDestinationContext 属性与 onReady | JS UT + C API UT |

## API 变更分析

### 新增 API

| API | 签名 | 版本 | 备注 |
|---|---|---|---|
| NavDestination() | NavDestination() | @since 9 | 无参创建 |
| NavDestination(builder) | NavDestination(builder: VoidCallback) | @since 10 | 带延迟渲染 builder |
| NavDestination(builder, navPathInfo) | NavDestination(builder: VoidCallback, info: NavPathInfo) | @since 11 | 带 builder+路由信息 |
| mode | mode(mode: NavDestinationMode) | @since 11(STANDARD)/12(DIALOG) | STANDARD/DIALOG 模式 |
| ignoreLayoutSafeArea | ignoreLayoutSafeArea(types: Array\<SafeAreaType\>, edges: Array\<SafeAreaEdge\>) | @since 12 | 安全区忽略 |
| fullScreenOverlay | fullScreenOverlay(fullScreenOverlay?: boolean) | @since 26 | 全屏覆盖 |
| preferredOrientation | preferredOrientation(orientation?: Orientation) | @since 19 | 页面方向 |
| enableStatusBar | enableStatusBar(enable?: boolean, animated?: boolean) | @since 19 | 状态栏控制 |
| enableNavigationIndicator | enableNavigationIndicator(enable?: boolean) | @since 19 | 导航指示器控制 |
| bindToScrollable | bindToScrollable(scrollers: Array\<Scroller\>) | @since 14 | 滚动绑定 |
| bindToNestedScrollable | bindToNestedScrollable(infos: Array\<NestedScrollInfo\>) | @since 14 | 嵌套滚动绑定 |
| onReady | onReady(callback: Callback\<NavDestinationContext\>) | @since 11 | 上下文就绪回调 |
| NavDestinationContext.pathInfo | pathInfo: NavPathInfo | @since 11 | 路由信息 |
| NavDestinationContext.pathStack | pathStack: NavigationStack | @since 11 | 路由栈 |
| NavDestinationContext.navDestinationId | navDestinationId: string | @since 11 | 目标 ID |
| NavDestinationContext.mode | mode: NavDestinationMode | @since 12 | 模式属性 |
| NavDestinationContext.getConfigInRouteMap | getConfigInRouteMap(name: string): RouteMapInfo | @since 12 | 路由配置获取 |

### 变更/废弃 API

无变更或废弃 API。所有 API 为新增。

## 接口规格

### NavDestination() — 无参创建

| 字段 | 内容 |
|---|---|
| 接口名 | NavDestination() |
| 版本 | @since 9 |
| 参数约束 | 无参数 |
| 行为场景 | 调用 NavDestinationModelNG::Create() 创建 NavDestinationGroupNode（tag=NAVDESTINATION_VIEW_ETS_TAG），内部创建 titleBarNode（含 backButton）、contentNode、toolBarNode。API >= VERSION_ELEVEN 时自动安全区展开。节点压入 ViewStackProcessor |
| 源码引用 | `navdestination_model_ng.cpp:257-291` |
| C API 对应 | 无直接 C API 创建入口，由 Navigation 内部路由机制创建 |

### NavDestination(builder) — 带 builder 创建

| 字段 | 内容 |
|---|---|
| 接口名 | NavDestination(builder: VoidCallback) |
| 版本 | @since 10 |
| 参数约束 | builder: 必须为函数类型（info[0]->IsFunction()） |
| 行为场景 | 创建 ShallowBuilder 包装 deepRenderFunc，NavDestinationModelNG::Create(deepRenderFunc, context) 创建 NavDestinationGroupNode。context 为新建 NavDestinationContext 且关联 JSNavPathInfo。API >= VERSION_ELEVEN 时 contentNode 自动安全区展开 |
| 异常处理 | builder 为空时 deepRenderFunc 返回 nullptr，ShallowBuilder 不执行渲染 |
| 源码引用 | `js_navdestination.cpp:330-341`, `navdestination_model_ng.cpp:461-510` |

### NavDestination(builder, navPathInfo) — 带 builder+navPathInfo 创建

| 字段 | 内容 |
|---|---|
| 接口名 | NavDestination(builder: VoidCallback, info: NavPathInfo) |
| 版本 | @since 11 |
| 参数约束 | builder: 必须为函数类型；info: 必须为对象且包含 moduleName(string) 和 pagePath(string) |
| 行为场景 | 与单参 builder 相同的创建流程，额外提取 info 对象的 moduleName/pagePath 属性设置到 NavDestinationGroupNode->SetNavDestinationPathInfo(moduleName, pagePath) |
| 异常处理 | info 对象缺少 moduleName/pagePath 字符串属性时打印错误日志并 return（不创建） |
| 源码引用 | `js_navdestination.cpp:360-382` |

### mode(NavDestinationMode) — 模式选择

| 字段 | 内容 |
|---|---|
| 接口名 | mode(mode: NavDestinationMode) |
| 版本 | @since 11（STANDARD），@since 12（DIALOG） |
| 参数约束 | mode: NavDestinationMode 枚举值（STANDARD=0, DIALOG=1） |
| 行为场景 | STANDARD: NavDestination 在 Navigation Content 区域全屏宽度显示，backgroundColor 默认为 AppTheme->GetBackgroundColor；DIALOG: NavDestination 弹窗样式显示，backgroundColor 默认为 Color::TRANSPARENT |
| 异常处理 | 非数字参数时默认设为 STANDARD；DIALOG 模式下 preferredOrientation/enableStatusBar/enableNavigationIndicator 不生效 |
| 源码引用 | `js_navdestination.cpp:574-583`, `navdestination_model_ng.cpp:1108-1113`, `navdestination_pattern.cpp:288-301` |

### ignoreLayoutSafeArea(types, edges) — 安全区忽略

| 字段 | 内容 |
|---|---|
| 接口名 | ignoreLayoutSafeArea(types: Array\<SafeAreaType\>, edges: Array\<SafeAreaEdge\>) |
| 版本 | @since 12 |
| 参数约束 | types: SafeAreaType 数组（SYSTEM=0, CUTOUT=1）；edges: SafeAreaEdge 数组（TOP=0, BOTTOM=1, START=2, END=3） |
| 行为场景 | 作用于 contentNode 的 LayoutProperty->UpdateIgnoreLayoutSafeAreaOpts(opts)，使内容区忽略指定类型和方向的系统安全区 |
| 异常处理 | 空字符串/空数组时设为 SAFE_AREA_TYPE_NONE/SAFE_AREA_EDGE_NONE |
| 恢复行为 | C API Reset 默认恢复 SAFE_AREA_TYPE_SYSTEM/SAFE_AREA_EDGE_ALL |
| 源码引用 | `navdestination_model_ng.cpp:1400-1411`, `navdestination_modifier.cpp:147-195` |

### fullScreenOverlay(Optional\<boolean\>) — 全屏覆盖

| 字段 | 内容 |
|---|---|
| 接口名 | fullScreenOverlay(fullScreenOverlay?: boolean) |
| 版本 | @since 26 |
| 参数约束 | fullScreenOverlay: Optional\<boolean\>，默认 std::nullopt |
| 行为场景 | 设置时更新 NavDestinationLayoutProperty 的 FullScreenOverlay 属性，调用 NotifyFullScreenOverlayRequestChange 触发 Navigation 重排 content/overlay 容器。fullScreenOverlay=true 时 NavDestination 被移入 overlay 容器覆盖下层页面 |
| 恢复行为 | C API Reset 设置 std::nullopt |
| 源码引用 | `navdestination_model_ng.cpp:1618-1653`, `navdestination_pattern.cpp:196-231` |

### preferredOrientation(Optional\<Orientation\>) — 页面方向

| 字段 | 内容 |
|---|---|
| 接口名 | preferredOrientation(orientation?: Orientation) |
| 版本 | @since 19 |
| 参数约束 | orientation: Orientation 枚举（UNSPECIFIED~FOLLOW_DESKTOP，共18种） |
| 行为场景 | 设置 NavDestinationGroupNode->SetOrientation(ori)。生效条件：Navigation IsPageLevelConfigEnabled() && IsFullPageNavigation()。首次设置仅记录 preOrientation 不执行方向变更。非 DIALOG 模式时调用 WindowManager->SetRequestedOrientation |
| 异常处理 | DIALOG 模式下不生效 |
| 恢复行为 | C API Reset 设置 std::nullopt |
| 源码引用 | `navdestination_model_ng.cpp:2072-2087`, `navdestination_pattern.cpp:989-1028` |

### enableStatusBar(Optional\<boolean\>, animated?: boolean) — 状态栏控制

| 字段 | 内容 |
|---|---|
| 接口名 | enableStatusBar(enable?: boolean, animated?: boolean) |
| 版本 | @since 19 |
| 参数约束 | enable: Optional\<boolean\>；animated: Optional\<boolean\>，默认 false |
| 行为场景 | 存储 pair\<enable, animated\> 到 NavDestinationGroupNode->SetStatusBarConfig。生效条件同 preferredOrientation。调用 WindowManager->SetWindowSystemBarEnabled(SystemBarType::STATUS, enable, animated) |
| 异常处理 | DIALOG 模式下不生效 |
| 源码引用 | `navdestination_model_ng.cpp:2089-2105`, `navdestination_pattern.cpp:1039-1080` |

### enableNavigationIndicator(Optional\<boolean\>) — 导航指示器控制

| 字段 | 内容 |
|---|---|
| 接口名 | enableNavigationIndicator(enable?: boolean) |
| 版本 | @since 19 |
| 参数约束 | enable: Optional\<boolean\> |
| 行为场景 | 存储 optional\<enable\> 到 NavDestinationGroupNode->SetNavigationIndicatorConfig。生效条件同 preferredOrientation。调用 WindowManager->SetWindowSystemBarEnabled(SystemBarType::NAVIGATION_INDICATOR, enable, nullopt) |
| 异常处理 | DIALOG 模式下不生效 |
| 源码引用 | `navdestination_model_ng.cpp:2107-2123`, `navdestination_pattern.cpp:1082-1121` |

### bindToScrollable(Array\<Scroller\>) — 滚动绑定

| 字段 | 内容 |
|---|---|
| 接口名 | bindToScrollable(scrollers: Array\<Scroller\>) |
| 版本 | @since 14 |
| 参数约束 | scrollers: Scroller 对象数组 |
| 行为场景 | 通过 NavDestinationModelNG::UpdateBindingWithScrollable 传入回调，JSNavDestinationScrollableProcessor::BindToScrollable 处理 Scroller 数组绑定 |
| 恢复行为 | C API Reset 调用 processor->UnbindScrollable()；空参数时 JS 调用 jsProcessor->UnbindScrollable() |
| 源码引用 | `js_navdestination.cpp:842-854`, `navdestination_modifier.cpp:1009-1028` |

### bindToNestedScrollable(Array\<NestedScrollInfo\>) — 嵌套滚动绑定

| 字段 | 内容 |
|---|---|
| 接口名 | bindToNestedScrollable(infos: Array\<NestedScrollInfo\>) |
| 版本 | @since 14 |
| 参数约束 | infos: NestedScrollInfo 对象数组 |
| 行为场景 | 通过 NavDestinationModelNG::UpdateBindingWithScrollable 传入回调，JSNavDestinationScrollableProcessor::BindToNestedScrollable 处理 NestedScrollInfo 数组绑定 |
| 恢复行为 | C API Reset 调用 processor->UnbindNestedScrollable()；空参数时 JS 调用 jsProcessor->UnbindNestedScrollable() |
| 源码引用 | `js_navdestination.cpp:856-868`, `navdestination_modifier.cpp:1030-1049` |

### onReady(Callback\<NavDestinationContext\>) — 上下文就绪回调

| 字段 | 内容 |
|---|---|
| 接口名 | onReady(callback: Callback\<NavDestinationContext\>) |
| 版本 | @since 11 |
| 参数约束 | callback: 必须为函数类型 |
| 行为场景 | 注册回调到 NavDestinationEventHub::SetOnReady。回调触发时创建 JSNavDestinationContext 实例并传入 context 对象 |
| 异常处理 | 非函数参数时不注册 |
| 源码引用 | `js_navdestination.cpp:552-572`, `navdestination_model_ng.cpp:974-991` |

### NavDestinationContext — 上下文对象

| 字段 | 内容 |
|---|---|
| 接口名 | NavDestinationContext |
| 版本 | @since 11（pathInfo/pathStack/navDestinationId），@since 12（mode） |
| 属性 | pathInfo: RefPtr\<NavPathInfo\>；navigationStack: WeakPtr\<NavigationStack\>；navDestinationId: uint64_t；mode: NavDestinationMode；index: int32_t（默认-1）；preIndex: int32_t（默认-1）；uniqueId: int32_t；curSize: optional\<SizeF\>；isEmpty: bool |
| 行为场景 | NavDestinationContext 由 NavDestinationPattern 创建和管理，与 Pattern 双向关联。context->SetNavDestinationPattern(WeakClaim(pattern)) 确保上下文可回溯到 Pattern |
| 源码引用 | `navdestination_context.h:92-201` |

## 兼容性声明

| API 版本 | 兼容性影响 | 说明 |
|---|---|---|
| VERSION_NINE | NavDestination() 无参创建可用 | 创建时无安全区自动展开 |
| VERSION_TEN | NavDestination(builder) 可用 | 同 VERSION_NINE 安全区行为 |
| VERSION_ELEVEN | NavDestination(builder, navPathInfo) 可用；自动安全区展开生效 | OnAttachToFrameNode 中自动设置 SAFE_AREA_TYPE_SYSTEM | SAFE_AREA_TYPE_CUTOUT, SAFE_AREA_EDGE_ALL |
| VERSION_TWELVE | DIALOG 模式可用；ignoreLayoutSafeArea 可用 | DIALOG 模式 backgroundColor 默认 TRANSPARENT |
| VERSION_FOURTEEN | bindToScrollable/bindToNestedScrollable 可用 | 滚动绑定机制 |
| VERSION_NINETEEN | preferredOrientation/enableStatusBar/enableNavigationIndicator 可用 | 仅在 IsPageLevelConfigEnabled && IsFullPageNavigation 下生效 |
| VERSION_TWENTY_SIX | fullScreenOverlay 可用 | 触发 Navigation content/overlay 容器重排 |

向下兼容：所有早期版本 API 在后续版本中保持行为不变，新属性仅对满足条件的 Navigation 配置生效。

## 架构约束

| 约束 ID | 描述 | 源码依据 |
|---|---|---|
| AC-1 | NavDestinationPattern 继承 NavDestinationPatternBase + AutoFillTriggerStateHolder，使用 DECLARE_ACE_TYPE 多继承 | `navdestination_pattern.h:39-40` |
| AC-2 | NavDestinationGroupNode 继承 NavDestinationNodeBase（含 titleBarNode/contentNode/toolBarNode 槽位） | `navdestination_group_node.h:37-38` |
| AC-3 | NavDestinationModelNG 使用 ViewStackProcessor::GetInstance() + 单例模式（NavDestinationModel::GetInstance()） | `js_navdestination.cpp:39-49` |
| AC-4 | NavDestinationModelStatic 使用全静态方法模式，所有方法接收 FrameNode* 参数直接操作 | `navdestination_model_static.h:30-82` |
| AC-5 | NavDestinationLayoutProperty 继承 NavDestinationLayoutPropertyBase，所有属性使用 PROPERTY_UPDATE_MEASURE | `navdestination_layout_property.h:57-59, navdestination_layout_property_base.h:97-105` |
| AC-6 | NavDestinationLayoutProperty::Clone/Reset 调用 Base 版本后补充 NoPixMap/ImageSource/PixelMap | `navdestination_layout_property.h:37-54` |
| AC-7 | NavDestinationContext 与 NavDestinationPattern 通过 WeakPtr 双向关联 | `navdestination_pattern.h:128-135, navdestination_context.h:187-188` |
| AC-8 | C API 层通过 nav_destination_modifier.cpp 的 GetNavDestinationModifier() 函数表统一暴露 | `nav_destination_modifier.cpp:1066-1157` |
| AC-9 | 静态版本 NavDestination（isStatic=true）使用 ShallowBuilder 延迟渲染 | `navdestination_model_static.cpp:358-363` |
| AC-10 | fullScreenOverlay 变更触发 Navigation 容器重排，需 NavigationGroupNode 配合 | `navdestination_pattern.cpp:205-230` |

## 非功能性需求

| 需求 ID | 类型 | 描述 | 验证方式 |
|---|---|---|---|
| NFR-1 | 性能 | NavDestination 创建不应阻塞主线程超过 5ms | Benchmark 测试 |
| NFR-2 | 内存 | NavDestination 析构时清理 scrollableProcessor、customNode、overlayManager，避免泄漏 | UT 内存泄漏检测 |
| NFR-3 | 安全 | navDestinationId 使用 atomic 自增，保证多线程安全 | 源码审查 `navdestination_pattern.cpp:34` |
| NFR-4 | 可恢复性 | fullScreenOverlay/enableStatusBar/enableNavigationIndicator 均有 Reset 路径恢复默认值 | C API Reset 函数验证 |
| NFR-5 | 线程安全 | OnAttachToFrameNode/OnDetachFromFrameNode 使用 THREAD_SAFE_NODE_CHECK 宏 | `navdestination_pattern.cpp:435,458` |

## 多设备适配声明

| 设备类型 | 适配说明 |
|---|---|
| 手机 | STANDARD 模式全屏宽度显示，DIALOG 模式弹窗样式显示 |
| 平板 | STANDARD 模式在 Navigation Content 区域显示，SPLIT 模式下支持左右分栏 |
| 折叠屏 | 展开态支持 SPLIT 模式，preferredOrientation 自动适配 |
| 大屏/智慧屏 | enableStatusBar/enableNavigationIndicator 支持系统级控制 |

## 全局特性影响

| 影响范围 | 描述 |
|---|---|
| Navigation 组件 | fullScreenOverlay 变更触发 Navigation 容器重排（UpdateNavDestinationNodeWithoutMarkDirty + RebuildRenderContextTree） |
| WindowManager | enableStatusBar/enableNavigationIndicator 调用 SetWindowSystemBarEnabled |
| 安全区系统 | ignoreLayoutSafeArea 和自动安全区展开影响 SafeAreaExpandOpts |
| 内存管理 | NavDestination 注册到 MemoryManager 的回收页面列表 |
| 窗口回调 | OnAttachToFrameNode 注册 WindowStateChangedCallback/WindowSizeChangeCallback |

## Spec 自审清单

| 检查项 | 结果 |
|---|---|
| 所有断言是否有 file:line 引用 | 是 |
| 是否存在 TBD/placeholder | 否 |
| API 版本标注是否完整 | 是 |
| 异常/边界场景是否覆盖 | 是 |
| 恢复路径是否覆盖 | 是 |
| DIALOG 模式限制是否文档化 | 是 |
| 安全区自动展开行为是否文档化 | 是 |
| NavDestinationModelNG/Static 双路径是否文档化 | 是 |
| fullScreenOverlay 容器重排机制是否文档化 | 是 |

## context-references

| 源码路径 | 关键行号 | 用途 |
|---|---|---|
| `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.h` | 39-50, 128-135, 386-396 | Pattern 类定义、Context 关联、成员变量 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.cpp` | 34, 105-110, 142-194, 196-231, 279-301, 437-441, 989-1121 | autoGenId、OnModifyDone、fullScreenOverlay、backgroundColor、safeAreaExpand、orientation/statusBar/navigationIndicator |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_model_ng.h` | 23-181 | ModelNG 接口声明 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_model_ng.cpp` | 257-291, 461-510, 1108-1122, 1400-1422, 1618-1653, 1827-1872, 2072-2123 | Create、mode、ignoreLayoutSafeArea、fullScreenOverlay、scrollable、orientation/statusBar/navigationIndicator |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_model_static.h` | 30-82 | Static 接口声明 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_model_static.cpp` | 334-389, 421-427, 537-546, 688-704, 750-757 | CreateFrameNode、mode、ignoreLayoutSafeArea、enableStatusBar/navigationIndicator、orientation |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_layout_property.h` | 57-59 | PROPERTY_UPDATE_MEASURE 属性声明 |
| `frameworks/core/components_ng/pattern/navigation/navdestination_layout_property_base.h` | 97-105 | Base 属性 PROPERTY_UPDATE_MEASURE |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_group_node.h` | 37-38, 333, 81-89 | GroupNode 定义、mode_默认值、fullScreenOverlay |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_context.h` | 92-201 | Context 全属性定义 |
| `frameworks/bridge/declarative_frontend/jsview/js_navdestination.h` | 24-67 | JS 接口声明 |
| `frameworks/bridge/declarative_frontend/jsview/js_navdestination.cpp` | 39-49, 314-383, 574-583, 739-772, 842-868, 1047-1081 | 单例、Create 路径、mode、ignoreLayoutSafeArea、bindToScrollable/NestedScrollable、preferredOrientation/enableStatusBar/enableNavigationIndicator |
| `frameworks/core/interfaces/native/node/nav_destination_modifier.cpp` | 22-23, 119-131, 147-195, 629-689, 691-707, 1009-1049, 1066-1157 | C API 默认值、mode、ignoreLayoutSafeArea、orientation/statusBar/navigationIndicator、fullScreenOverlay、bindToScrollable/NestedScrollable、modifier 函数表 |
