# 特性规格

> Func-04-11-02-Feat-02 无感监听接口全覆盖：覆盖所有 observer on()/off() API 的完整接口规格，包括 NavDestinationState 10 值扩展、RouterPageState、ScrollEventType、TabContentState、NodeRenderState、GestureListenerType 等枚举行为定义。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无感监听接口全覆盖 (Observer API Full Coverage) |
| 特性编号 | Func-04-11-02-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 11 起支持，API 12/15/17/19/20/22/23 有接口扩展 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/11-component-info/02-observer/design.md` | Baselined |
| Feat-01 Spec | `04-common-capability/11-component-info/02-observer/Feat-01-observer-core-architecture-spec.md` | Draft |

---

## 用户故事

### US-1: NavDestinationUpdate 监听 Navigation 子页面状态

**作为** 应用开发者,
**我想要** 通过 navDestinationUpdate / navDestinationUpdateByUniqueId 监听 NavDestination 子页面的生命周期状态变化,
**以便** 在子页面显示/隐藏/出现/消失/返回等关键时机执行业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 uiObserver.on('navDestinationUpdate', callback) 注册 global scope THEN 回调接收所有 Navigation 容器的 NavDestinationInfo | 正常 |
| AC-1.2 | WHEN 调用 uiObserver.on('navDestinationUpdate', {navigationId: ResourceStr}, callback) THEN 回调仅接收指定 navigationId 的 NavDestinationInfo | 正常 |
| AC-1.3 | WHEN 调用 UIObserver.on('navDestinationUpdateByUniqueId', navigationUniqueId: number, callback)（直接 number 参数，非 options 对象）THEN 回调仅接收指定 navigationUniqueId 的 NavDestinationInfo（@since 20） | 正常 |
| AC-1.4 | WHEN NavDestination 状态变为 ON_SHOWN(0) THEN 回调参数 NavDestinationInfo.state = NavDestinationState.ON_SHOWN | 正常 |
| AC-1.5 | WHEN NavDestination 状态变为 ON_HIDDEN(1) THEN 回调参数 state = ON_HIDDEN | 正常 |
| AC-1.6 | WHEN NavDestination 状态变为 ON_APPEAR(2) THEN 回调参数 state = ON_APPEAR | 正常 |
| AC-1.7 | WHEN NavDestination 状态变为 ON_DISAPPEAR(3) THEN 回调参数 state = ON_DISAPPEAR | 正常 |
| AC-1.8 | WHEN NavDestination 状态变为 ON_WILL_SHOW(4) THEN 回调参数 state = ON_WILL_SHOW | 正常 |
| AC-1.9 | WHEN NavDestination 状态变为 ON_WILL_HIDE(5) THEN 回调参数 state = ON_WILL_HIDE | 正常 |
| AC-1.10 | WHEN NavDestination 状态变为 ON_WILL_APPEAR(6) THEN 回调参数 state = ON_WILL_APPEAR | 正常 |
| AC-1.11 | WHEN NavDestination 状态变为 ON_WILL_DISAPPEAR(7) THEN 回调参数 state = ON_WILL_DISAPPEAR | 正常 |
| AC-1.12 | WHEN NavDestination 状态变为 ON_BACKPRESS(100) THEN 回调参数 state = ON_BACKPRESS | 边界 |
| AC-1.13 | WHEN NavDestination 状态变为 ON_ACTIVE(8)（API 17+）THEN 回调参数 state = ON_ACTIVE | 正常 |
| AC-1.14 | WHEN NavDestination 状态变为 ON_INACTIVE(9)（API 17+）THEN 回调参数 state = ON_INACTIVE | 正常 |
| AC-1.15 | WHEN NavDestinationInfo 回调参数 THEN 包含 navigationId, name, state, index, param?, navDestinationId, uniqueId?, mode?, size? 字段 | 正常 |
| AC-1.16 | WHEN NavDestinationInfo.mode 字段（API 15+）THEN 值为 NavDestinationMode.DIALOG / STANDARD / STACK | 正常 |
| AC-1.17 | WHEN NavDestinationInfo.uniqueId 字段（API 15+）THEN 值为 NavDestination 组件的 number uniqueId（⚠️ d.ts 注释说"NavDestination 组件的 uniqueId"，不是 Navigation 容器的 uniqueId） | 边界 |
| AC-1.18 | WHEN NavDestinationInfo.size 字段（API 23+）THEN 值为 NavDestination 的布局尺寸信息 | 正常 |

### US-2: NavDestinationSwitch 监听 Navigation 子页面切换

**作为** 应用开发者,
**我想要** 通过 navDestinationSwitch 监听 Navigation 子页面切换（包括 NavBar 和 NavDestination 之间的切换）,
**以便** 追踪页面流转和执行切换相关逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 on('navDestinationSwitch', UIAbilityContext \| UIContext, callback) THEN 回调接收 NavDestinationSwitchInfo | 正常 |
| AC-2.2 | WHEN 调用 on('navDestinationSwitch', UIAbilityContext \| UIContext, NavDestinationSwitchObserverOptions, callback) THEN 回调仅接收指定 navigationId 的 NavDestinationSwitchInfo | 正常 |
| AC-2.3 | WHEN NavDestinationSwitchInfo 回调 THEN 包含 context, from(NavDestinationInfo \| NavBar), to(NavDestinationInfo \| NavBar), operation 字段 | 正常 |
| AC-2.4 | WHEN NavBar 出现 THEN from 或 to 的 type 为 NavBar（string literal 'navBar'，不是 NavDestinationInfo） | 边界 |

### US-3: RouterPageUpdate 监听路由页面状态

**作为** 应用开发者,
**我想要** 通过 routerPageUpdate 监听路由页面（RouterPage）的生命周期状态变化,
**以便** 在页面显示/隐藏/返回等关键时机执行业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 on('routerPageUpdate', UIAbilityContext, callback) THEN 回调仅接收该 UIAbility 实例的 RouterPageInfo | 正常 |
| AC-3.2 | WHEN 调用 on('routerPageUpdate', UIContext, callback) THEN 回调仅接收该 UIContext 实例的 RouterPageInfo | 正常 |
| AC-3.3 | WHEN RouterPage 状态变为 ABOUT_TO_APPEAR(0) THEN 回调参数 RouterPageInfo.state = RouterPageState.ABOUT_TO_APPEAR | 正常 |
| AC-3.4 | WHEN RouterPage 状态变为 ABOUT_TO_DISAPPEAR(1) THEN 回调参数 state = ABOUT_TO_DISAPPEAR | 正常 |
| AC-3.5 | WHEN RouterPage 状态变为 ON_PAGE_SHOW(2) THEN 回调参数 state = ON_PAGE_SHOW | 正常 |
| AC-3.6 | WHEN RouterPage 状态变为 ON_PAGE_HIDE(3) THEN 回调参数 state = ON_PAGE_HIDE | 正常 |
| AC-3.7 | WHEN RouterPage 状态变为 ON_BACK_PRESS(4) THEN 回调参数 state = ON_BACK_PRESS | 正常 |
| AC-3.8 | WHEN RouterPageInfo 回调参数 THEN 包含 context(UIAbilityContext \| UIContext), index, name, path, state, pageId, size?(API 23+) 字段 | 正常 |

### US-4: ScrollEvent 监听滚动状态

**作为** 应用开发者,
**我想要** 通过 scrollEvent 监听 Scroll/List/Grid 等可滚动组件的滚动状态变化（SCROLL_START/SCROLL_STOP）,
**以便** 在滚动开始/停止时执行业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 on('scrollEvent', callback) THEN 回调接收所有 Scrollable 组件的 ScrollEventInfo | 正常 |
| AC-4.2 | WHEN 调用 on('scrollEvent', {id: string}, callback) THEN 回调仅接收指定 id Scrollable 组件的 ScrollEventInfo | 正常 |
| AC-4.3 | WHEN Scrollable 组件开始滚动 THEN 回调参数 ScrollEventInfo.scrollEvent = ScrollEventType.SCROLL_START(0) | 正常 |
| AC-4.4 | WHEN Scrollable 组件停止滚动 THEN 回调参数 scrollEvent = ScrollEventType.SCROLL_STOP(1) | 正常 |
| AC-4.5 | WHEN ScrollEventInfo 回调参数 THEN 包含 id, uniqueId, scrollEvent, offset, axis?(API 20+) 字段 | 正常 |
| AC-4.6 | WHEN ScrollEventInfo.axis 字段（API 20+）THEN 值为 Axis.HORIZONTAL / Axis.VERTICAL | 正常 |

### US-5: DensityUpdate 监听屏幕密度变化

**作为** 应用开发者,
**我想要** 通过 densityUpdate 监听屏幕密度变化,
**以便** 在密度变化时动态调整布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 on('densityUpdate', UIContext, callback) THEN 回调仅接收该 UIContext 实例的 DensityInfo | 正常 |
| AC-5.2 | WHEN DensityInfo 回调 THEN 包含 context(UIContext) 和 density(number) 字段 | 正常 |
| AC-5.3 | WHEN densityUpdate 不传 UIContext THEN 使用当前 instanceId 隐式注册 | 边界 |

### US-6: WillDraw / DidLayout 监听渲染和布局管线

**作为** 应用开发者,
**我想要** 通过 willDraw / didLayout 监听渲染管线即将绘制和布局完成事件,
**以便** 在渲染/布局关键时机执行性能监控或 UI 更新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 on('willDraw', UIContext, callback) THEN PipelineContext 每次即将绘制前调用 callback（void 回调） | 正常 |
| AC-6.2 | WHEN 调用 on('didLayout', UIContext, callback) THEN PipelineContext 每次布局完成后调用 callback（void 回调） | 正常 |
| AC-6.3 | WHEN willDraw/didLayout 不传 UIContext THEN 使用当前 instanceId 隐式注册 | 边界 |

### US-7: TabContentUpdate / TabChange 监听 Tab 组件状态

**作为** 应用开发者,
**我想要** 通过 tabContentUpdate / tabChange 监听 Tab 组件的内容页状态变化和 Tab 切换事件,
**以便** 在 Tab 内容页显示/隐藏或 Tab 切换时执行业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 on('tabContentUpdate', callback) THEN 回调接收所有 Tab 组件的 TabContentInfo | 正常 |
| AC-7.2 | WHEN 调用 on('tabContentUpdate', {id: string}, callback) THEN 回调仅接收指定 id Tab 组件的 TabContentInfo | 正常 |
| AC-7.3 | WHEN TabContent 状态变为 ON_SHOW(0) THEN 回调参数 TabContentInfo.state = TabContentState.ON_SHOW | 正常 |
| AC-7.4 | WHEN TabContent 状态变为 ON_HIDE(1) THEN 回调参数 state = ON_HIDE | 正常 |
| AC-7.5 | WHEN TabContentInfo 回调参数 THEN 包含 tabContentId, tabContentUniqueId, state, index, id, uniqueId, lastIndex?(API 22+) 字段 | 正常 |
| AC-7.6 | WHEN 调用 on('tabChange', callback) THEN 回调接收所有 Tab 组件的 TabContentInfo（tabChange 回调类型为 Callback\<TabContentInfo\>，无单独 TabChangeInfo 类型） | 正常 |
| AC-7.7 | WHEN 调用 on('tabChange', {id: string}, callback) THEN 回调仅接收指定 id Tab 组件的 TabContentInfo | 正常 |
| AC-7.8 | WHEN Tab 切换 THEN 回调参数为 TabContentInfo，包含 index（当前选中 Tab 编号）和 lastIndex?（上一个 Tab 编号，API 22+），非 newIndex/oldIndex | 正常 |

### US-8: GestureObserver 监听手势事件（UIObserver 实例方法）

**作为** 应用开发者,
**我想要** 通过 UIObserver 实例方法（getUIContext().getUIObserver()）监听点击和手势事件,
**以便** 在点击/手势关键时机执行拦截或监控逻辑。

> ⚠️ 注意：willClick/didClick/beforePanStart/beforePanEnd/afterPanStart/afterPanEnd 是 UIObserver 实例方法，已通过 getUIContext() 限定 scope，不需要传入 context 参数。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 UIObserver.on('willClick', callback: ClickEventListenerCallback) THEN 点击事件即将触发时回调（无 context 参数） | 正常 |
| AC-8.2 | WHEN 调用 UIObserver.on('didClick', callback: ClickEventListenerCallback) THEN 点击事件完成后回调（无 context 参数） | 正常 |
| AC-8.3 | WHEN willClick/didClick ClickEventListenerCallback 回调 THEN 参数为 (event: ClickEvent, node?: FrameNode) | 正常 |
| AC-8.4 | WHEN 调用 UIObserver.on('willClick', callback: GestureEventListenerCallback)（第二重载）THEN Tap 手势事件即将触发时回调 | 正常 |
| AC-8.5 | WHEN willClick GestureEventListenerCallback 回调 THEN 参数为 (event: GestureEvent, node?: FrameNode) | 正常 |
| AC-8.6 | WHEN 调用 UIObserver.on('beforePanStart', callback: PanListenerCallback) THEN Pan 手势即将开始时回调（@since 19） | 正常 |
| AC-8.7 | WHEN 调用 UIObserver.on('beforePanEnd', callback: PanListenerCallback) THEN Pan 手势即将结束时回调（@since 19） | 正常 |
| AC-8.8 | WHEN 调用 UIObserver.on('afterPanStart', callback: PanListenerCallback) THEN Pan 手势已开始后回调（@since 19） | 正常 |
| AC-8.9 | WHEN 调用 UIObserver.on('afterPanEnd', callback: PanListenerCallback) THEN Pan 手势已结束后回调（@since 19） | 正常 |
| AC-8.10 | WHEN PanListenerCallback 回调 THEN 参数为 (event: GestureEvent, current: GestureRecognizer, node?: FrameNode)（三参数） | 正常 |
| AC-8.11 | WHEN UIObserver 使用全局手势监听（addGlobalGestureListener）THEN 通过 GestureListenerType 枚举指定手势类型（@since 20） | 正常 |

### US-9: NodeRenderState 监听节点渲染可见性（@since 20）

**作为** 应用开发者,
**我想要** 通过 nodeRenderState 监听指定节点的渲染可见性状态（ABOUT_TO_RENDER_IN/ABOUT_TO_RENDER_OUT）,
**以便** 感知节点是否在可视区域内。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 调用 UIObserver.on('nodeRenderState', nodeIdentity: NodeIdentity, callback: NodeRenderStateChangeCallback) THEN 回调接收该节点的 NodeRenderState（直接 NodeIdentity 参数，类型 string \| number，非 options 对象） | 正常 |
| AC-9.2 | WHEN 节点可见 THEN 回调参数 state = NodeRenderState.ABOUT_TO_RENDER_IN(0) | 正常 |
| AC-9.3 | WHEN 节点不可见 THEN 回调参数 state = NodeRenderState.ABOUT_TO_RENDER_OUT(1) | 正常 |
| AC-9.4 | WHEN NodeIdentity 为 number THEN 按 FrameNode 的 uniqueId 查找节点 | 正常 |
| AC-9.5 | WHEN NodeIdentity 为 string THEN 按 FrameNode 的 inspectorId 查找节点 | 正常 |
| AC-9.6 | WHEN nodeRenderState 回调 THEN NodeRenderStateChangeCallback 参数为 (state: NodeRenderState, node?: FrameNode)，非单参数 Callback | 边界 |

### US-10: 其他监听类型（命名方法与 on() 混合）

**作为** 应用开发者,
**我想要** 通过各种 observer API 监听文本变化、Swiper 内容更新、页面/NavDestination 尺寸变化和窗口布局断点变化,
**以便** 在这些关键事件时执行业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 调用 UIObserver.on('textChange', {id: string}, callback) THEN 回调仅接收指定 id 组件的 TextChangeEventInfo（API 22+） | 正常 |
| AC-10.2 | WHEN TextChangeEventInfo 回调 THEN 包含 id, uniqueId, content 字段 | 正常 |
| AC-10.3 | WHEN 调用 UIObserver.onSwiperContentUpdate(callback) THEN 回调接收 Swiper 组件内容更新事件（命名方法，非 on(type) 模式，API 22+） | 正常 |
| AC-10.4 | WHEN 调用 UIObserver.onSwiperContentUpdate({id}, callback) THEN 回调仅接收指定 id Swiper 的内容更新事件 | 正常 |
| AC-10.5 | WHEN 调用 UIObserver.onRouterPageSizeChange(callback) THEN 回调接收路由页面尺寸变化事件（命名方法，API 23+） | 正常 |
| AC-10.6 | WHEN 调用 UIObserver.onNavDestinationSizeChange(callback) THEN 回调接收 NavDestination 尺寸变化事件（命名方法，API 23+） | 正常 |
| AC-10.7 | WHEN 调用 UIObserver.onNavDestinationSizeChangeByUniqueId(navigationUniqueId: number, callback) THEN 回调仅接收指定 uniqueId 的 NavDestination 尺寸变化（直接 number 参数，命名方法，API 23+） | 正常 |
| AC-10.8 | WHEN 调用 on('windowSizeLayoutBreakpointChange', callback) THEN 回调接收窗口布局断点变化事件，参数包含 widthBreakpoint 和 heightBreakpoint（API 22+） | 正常 |

### US-11: GestureListenerType 与全局手势监听（@since 20）

**作为** 应用开发者,
**我想要** 通过 addGlobalGestureListener / removeGlobalGestureListener 监听全局手势事件,
**以便** 在指定手势类型触发时执行拦截逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-11.1 | WHEN 调用 UIObserver.addGlobalGestureListener(type: GestureListenerType, option: GestureObserverConfigs, callback) THEN 注册全局手势监听（@since 20） | 正常 |
| AC-11.2 | WHEN 调用 UIObserver.removeGlobalGestureListener(type: GestureListenerType, callback?) THEN 移除全局手势监听 | 正常 |
| AC-11.3 | WHEN GestureListenerType = TAP(0) THEN 监听 Tap 手势 | 正常 |
| AC-11.4 | WHEN GestureListenerType = LONG_PRESS(1) THEN 监听长按手势 | 正常 |
| AC-11.5 | WHEN GestureListenerType = PAN(2) THEN 监听 Pan 手势 | 正常 |
| AC-11.6 | WHEN GestureListenerType = PINCH(3) THEN 监听捏合手势 | 正常 |
| AC-11.7 | WHEN GestureListenerType = SWIPE(4) THEN 监听滑动手势 | 正常 |
| AC-11.8 | WHEN GestureListenerType = ROTATION(5) THEN 监听旋转手势 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.18 | R-1~R-18 | 已有实现 | XTS | nav_destination_pattern.cpp, ui_observer_listener.cpp |
| AC-2.1~2.4 | R-19~R-22 | 已有实现 | XTS | nav_router_pattern.cpp |
| AC-3.1~3.8 | R-23~R-30 | 已有实现 | XTS | router_page_state handling |
| AC-4.1~4.6 | R-31~R-36 | 已有实现 | XTS | scroll_pattern.cpp |
| AC-5.1~5.3 | R-37~R-39 | 已有实现 | XTS | pipeline_context.cpp |
| AC-6.1~6.3 | R-40~R-42 | 已有实现 | XTS | pipeline_context.cpp |
| AC-7.1~7.8 | R-43~R-50 | 已有实现 | XTS | tab_content_pattern.cpp |
| AC-8.1~8.11 | R-51~R-61 | 已有实现 | XTS | gesture_observer.cpp, @ohos.arkui.UIContext.d.ts |
| AC-9.1~9.6 | R-62~R-67 | 已有实现 | 单测 | node_render_status_monitor.cpp |
| AC-10.1~10.8 | R-68~R-75 | 已有实现 | XTS | ui_observer_listener.cpp |
| AC-11.1~11.8 | R-76~R-83 | 已有实现 | XTS | gesture_event_uiobserver_ani_modifier.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | on('navDestinationUpdate', cb) global | 回调接收所有 Navigation 容器的 NavDestinationInfo | — | AC-1.1 |
| R-2 | 行为 | on('navDestinationUpdate', {navigationId}, cb) | 仅接收指定 navigationId 的通知 | navigationId 为分区 key | AC-1.2 |
| R-3 | 行为 | on('navDestinationUpdateByUniqueId', navigationUniqueId, cb) | 仅接收指定 navigationUniqueId 的通知 | 直接 number 参数，非 options 对象；@since 20 | AC-1.3 |
| R-4 | 行为 | NavDestination state = ON_SHOWN | NavDestinationInfo.state = 0 | @since 11 | AC-1.4 |
| R-5 | 行为 | NavDestination state = ON_HIDDEN | NavDestinationInfo.state = 1 | @since 11 | AC-1.5 |
| R-6 | 行为 | NavDestination state = ON_APPEAR | NavDestinationInfo.state = 2 | @since 12 | AC-1.6 |
| R-7 | 行为 | NavDestination state = ON_DISAPPEAR | NavDestinationInfo.state = 3 | @since 12 | AC-1.7 |
| R-8 | 行为 | NavDestination state = ON_WILL_SHOW | NavDestinationInfo.state = 4 | @since 12 | AC-1.8 |
| R-9 | 行为 | NavDestination state = ON_WILL_HIDE | NavDestinationInfo.state = 5 | @since 12 | AC-1.9 |
| R-10 | 行为 | NavDestination state = ON_WILL_APPEAR | NavDestinationInfo.state = 6 | @since 12 | AC-1.10 |
| R-11 | 行为 | NavDestination state = ON_WILL_DISAPPEAR | NavDestinationInfo.state = 7 | @since 12 | AC-1.11 |
| R-12 | 边界 | NavDestination state = ON_BACKPRESS | NavDestinationInfo.state = 100 | 跳号设计(值10-99预留给未来) | AC-1.12 |
| R-13 | 行为 | NavDestination state = ON_ACTIVE | NavDestinationInfo.state = 8 | @since 17 | AC-1.13 |
| R-14 | 行为 | NavDestination state = ON_INACTIVE | NavDestinationInfo.state = 9 | @since 17 | AC-1.14 |
| R-15 | 行为 | NavDestinationInfo 回调 | 包含 navigationId, name, state, index, param?, navDestinationId, uniqueId?, mode?, size? | API 版本渐进扩展 | AC-1.15 |
| R-16 | 行为 | NavDestinationInfo.mode | NavDestinationMode.DIALOG / STANDARD / STACK | @since 15 | AC-1.16 |
| R-17 | 边界 | NavDestinationInfo.uniqueId | NavDestination 组件的 number uniqueId | d.ts 注释说"NavDestination 组件"，非 Navigation 容器；@since 15 | AC-1.17 |
| R-18 | 行为 | NavDestinationInfo.size | NavDestination 的布局尺寸信息 | @since 23 | AC-1.18 |
| R-19 | 行为 | on('navDestinationSwitch', context, cb) | 回调接收 NavDestinationSwitchInfo | context 为 UIAbilityContext/UIContext | AC-2.1 |
| R-20 | 行为 | on('navDestinationSwitch', context, options, cb) | 仅接收指定 navigationId 的 NavDestinationSwitchInfo | NavDestinationSwitchObserverOptions | AC-2.2 |
| R-21 | 行为 | NavDestinationSwitchInfo 回调 | 包含 context, from, to, operation | — | AC-2.3 |
| R-22 | 边界 | NavBar 出现 | from/to 的 type 为 NavBar（string literal 'navBar'） | — | AC-2.4 |
| R-23 | 行为 | on('routerPageUpdate', UIAbilityContext, cb) | 仅接收该 UIAbility 的 RouterPageInfo | — | AC-3.1 |
| R-24 | 行为 | on('routerPageUpdate', UIContext, cb) | 仅接收该 UIContext 的 RouterPageInfo | — | AC-3.2 |
| R-25 | 行为 | RouterPage ABOUT_TO_APPEAR | RouterPageInfo.state = 0 | — | AC-3.3 |
| R-26 | 行为 | RouterPage ABOUT_TO_DISAPPEAR | RouterPageInfo.state = 1 | — | AC-3.4 |
| R-27 | 行为 | RouterPage ON_PAGE_SHOW | RouterPageInfo.state = 2 | — | AC-3.5 |
| R-28 | 行为 | RouterPage ON_PAGE_HIDE | RouterPageInfo.state = 3 | — | AC-3.6 |
| R-29 | 行为 | RouterPage ON_BACK_PRESS | RouterPageInfo.state = 4 | — | AC-3.7 |
| R-30 | 行为 | RouterPageInfo 回调 | 包含 context, index, name, path, state, pageId, size? | @since 11，size @since 23 | AC-3.8 |
| R-31 | 行为 | on('scrollEvent', cb) global | 回调接收所有 Scrollable 的 ScrollEventInfo | — | AC-4.1 |
| R-32 | 行为 | on('scrollEvent', {id}, cb) | 仅接收指定 id Scrollable 的通知 | — | AC-4.2 |
| R-33 | 行为 | Scrollable 开始滚动 | ScrollEventInfo.scrollEvent = SCROLL_START(0) | @since 12 | AC-4.3 |
| R-34 | 行为 | Scrollable 停止滚动 | ScrollEventInfo.scrollEvent = SCROLL_STOP(1) | @since 12 | AC-4.4 |
| R-35 | 行为 | ScrollEventInfo 回调 | 包含 id, uniqueId, scrollEvent, offset, axis? | axis @since 20 | AC-4.5 |
| R-36 | 行为 | ScrollEventInfo.axis | Axis.HORIZONTAL / Axis.VERTICAL | @since 20 | AC-4.6 |
| R-37 | 行为 | on('densityUpdate', UIContext, cb) | 仅接收该 UIContext 的 DensityInfo | — | AC-5.1 |
| R-38 | 行为 | DensityInfo 回调 | 包含 context(UIContext) 和 density(number) | — | AC-5.2 |
| R-39 | 边界 | densityUpdate 不传 UIContext | 使用当前 instanceId 隐式注册 | — | AC-5.3 |
| R-40 | 行为 | on('willDraw', UIContext, cb) | PipelineContext 每次即将绘制前回调 | void 回调 | AC-6.1 |
| R-41 | 行为 | on('didLayout', UIContext, cb) | PipelineContext 每次布局完成后回调 | void 回调 | AC-6.2 |
| R-42 | 边界 | willDraw/didLayout 不传 UIContext | 使用当前 instanceId 隐式注册 | — | AC-6.3 |
| R-43 | 行为 | on('tabContentUpdate', cb) global | 回调接收所有 Tab 的 TabContentInfo | — | AC-7.1 |
| R-44 | 行为 | on('tabContentUpdate', {id}, cb) | 仅接收指定 id Tab 的通知 | — | AC-7.2 |
| R-45 | 行为 | TabContent ON_SHOW | TabContentInfo.state = ON_SHOW(0) | — | AC-7.3 |
| R-46 | 行为 | TabContent ON_HIDE | TabContentInfo.state = ON_HIDE(1) | — | AC-7.4 |
| R-47 | 行为 | TabContentInfo 回调 | 包含 tabContentId, tabContentUniqueId, state, index, id, uniqueId, lastIndex? | lastIndex @since 22 | AC-7.5 |
| R-48 | 行为 | on('tabChange', cb) | 回调类型为 Callback\<TabContentInfo\>，无单独 TabChangeInfo 类型 | — | AC-7.6 |
| R-49 | 行为 | on('tabChange', {id}, cb) | 仅接收指定 id Tab 的通知 | — | AC-7.7 |
| R-50 | 行为 | Tab 切换回调 | TabContentInfo 包含 index（当前 Tab）和 lastIndex?（上一个 Tab，API 22+） | 非 newIndex/oldIndex | AC-7.8 |
| R-51 | 行为 | on('willClick', ClickEventListenerCallback) | 点击事件即将触发时回调 | 无 context 参数，UIObserver 实例方法 | AC-8.1 |
| R-52 | 行为 | on('didClick', ClickEventListenerCallback) | 点击事件完成后回调 | 无 context 参数 | AC-8.2 |
| R-53 | 行为 | ClickEventListenerCallback | (event: ClickEvent, node?: FrameNode) | — | AC-8.3 |
| R-54 | 行为 | on('willClick', GestureEventListenerCallback) | Tap 手势事件即将触发时回调 | 第二重载 | AC-8.4 |
| R-55 | 行为 | GestureEventListenerCallback | (event: GestureEvent, node?: FrameNode) | — | AC-8.5 |
| R-56 | 行为 | on('beforePanStart', PanListenerCallback) | Pan 手势即将开始时回调 | @since 19，无 context 参数 | AC-8.6 |
| R-57 | 行为 | on('beforePanEnd', PanListenerCallback) | Pan 手势即将结束时回调 | @since 19 | AC-8.7 |
| R-58 | 行为 | on('afterPanStart', PanListenerCallback) | Pan 手势已开始后回调 | @since 19 | AC-8.8 |
| R-59 | 行为 | on('afterPanEnd', PanListenerCallback) | Pan 手势已结束后回调 | @since 19 | AC-8.9 |
| R-60 | 行为 | PanListenerCallback | (event: GestureEvent, current: GestureRecognizer, node?: FrameNode) | 三参数，含 GestureRecognizer | AC-8.10 |
| R-61 | 行为 | addGlobalGestureListener | 通过 GestureListenerType 指定手势类型 | @since 20 | AC-8.11 |
| R-62 | 行为 | on('nodeRenderState', nodeIdentity, cb) | NodeRenderStatusMonitor 注册该节点监听器 | 最多 64 节点；NodeIdentity=string|number；@since 20 | AC-9.1 |
| R-63 | 行为 | 节点可见 | 回调 ABOUT_TO_RENDER_IN(0) | 全祖先满足三条件 | AC-9.2 |
| R-64 | 行为 | 节点不可见 | 回调 ABOUT_TO_RENDER_OUT(1) | 任一祖先不满足 | AC-9.3 |
| R-65 | 行为 | NodeIdentity 为 number | 按 FrameNode uniqueId 查找 | — | AC-9.4 |
| R-66 | 行为 | NodeIdentity 为 string | 按 FrameNode inspectorId 查找 | — | AC-9.5 |
| R-67 | 边界 | nodeRenderState 回调 | NodeRenderStateChangeCallback = (state, node?) 双参数 | 非 Callback\<NodeRenderState\> 单参数 | AC-9.6 |
| R-68 | 行为 | on('textChange', {id}, cb) | 仅接收指定 id 组件的 TextChangeEventInfo | @since 22 | AC-10.1 |
| R-69 | 行为 | TextChangeEventInfo 回调 | 包含 id, uniqueId, content | @since 22 | AC-10.2 |
| R-70 | 行为 | onSwiperContentUpdate(cb) | Swiper 组件内容更新事件 | 命名方法，非 on(type)；@since 22 | AC-10.3 |
| R-71 | 行为 | onRouterPageSizeChange(cb) | 路由页面尺寸变化事件 | 命名方法；@since 23 | AC-10.4 |
| R-72 | 行为 | onNavDestinationSizeChange(cb) | NavDestination 尺寸变化事件 | 命名方法；@since 23 | AC-10.5 |
| R-73 | 行为 | onNavDestinationSizeChangeByUniqueId(navigationUniqueId, cb) | 仅接收指定 uniqueId 的 NavDestination 尺寸变化 | 直接 number 参数，命名方法；@since 23 | AC-10.6 |
| R-74 | 行为 | on('windowSizeLayoutBreakpointChange', cb) | 窗口布局断点变化事件 | @since 22, 包含 widthBreakpoint + heightBreakpoint | AC-10.8 |
| R-75 | 边界 | tabChange 与 tabContentUpdate 回调类型不同 | tabChange 用 Callback\<TabContentInfo\>，tabContentUpdate 也用 Callback\<TabContentInfo\>，但 tabChange 的 lastIndex 字段有值 | — | AC-7.8 |
| R-76 | 行为 | addGlobalGestureListener | 注册全局手势监听 | @since 20 | AC-11.1 |
| R-77 | 行为 | removeGlobalGestureListener | 移除全局手势监听 | @since 20 | AC-11.2 |
| R-78 | 行为 | GestureListenerType.TAP | 枚举值 = 0 | @since 20 | AC-11.3 |
| R-79 | 行为 | GestureListenerType.LONG_PRESS | 枚举值 = 1 | @since 20 | AC-11.4 |
| R-80 | 行为 | GestureListenerType.PAN | 枚举值 = 2 | @since 20 | AC-11.5 |
| R-81 | 行为 | GestureListenerType.PINCH | 枚举值 = 3 | @since 20 | AC-11.6 |
| R-82 | 行为 | GestureListenerType.SWIPE | 枚举值 = 4 | @since 20 | AC-11.7 |
| R-83 | 行为 | GestureListenerType.ROTATION | 枚举值 = 5 | @since 20 | AC-11.8 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.3 NavDestination scope | XTS | global / navigationId / uniqueId(direct param) 三种 scope |
| VM-2 | AC-1.4~1.14 NavDestinationState 全值 | XTS | 10 个枚举值逐一触发验证 |
| VM-3 | AC-1.15~1.18 NavDestinationInfo 字段 | XTS | 各 API 版本字段逐步扩展 |
| VM-4 | AC-2.1~2.4 NavDestinationSwitch | XTS | context + options scope，NavBar('navBar') 识别 |
| VM-5 | AC-3.1~3.8 RouterPage | XTS | UIAbilityContext/UIContext scope，5 个枚举值 |
| VM-6 | AC-4.1~4.6 ScrollEvent | XTS | global / {id} scope，SCROLL_START/STOP |
| VM-7 | AC-5.1~5.3 DensityUpdate | XTS | UIContext scope，density 值 |
| VM-8 | AC-6.1~6.3 WillDraw/DidLayout | XTS | UIContext scope，void 回调 |
| VM-9 | AC-7.1~7.8 TabContent/TabChange | XTS | global / {id} scope；tabChange 用 TabContentInfo(index/lastIndex) |
| VM-10 | AC-8.1~8.11 GestureObserver | XTS | UIObserver 实例方法(无 context)，Click/Gesture 双重载，Pan 三参数，@since 19 |
| VM-11 | AC-9.1~9.6 NodeRenderState | 单测 | NodeIdentity direct param，双参数回调，IN=0/OUT=1 |
| VM-12 | AC-10.1~10.8 其他监听类型 | XTS | 命名方法(onSwiperContentUpdate等)，API 22/23 |
| VM-13 | AC-11.1~11.8 GestureListenerType | XTS | addGlobalGestureListener，6 枚举值，@since 20 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|----------|--------|-----------|----------|---------|
| uiObserver.on('navDestinationUpdate', cb) | Public | callback: Callback\<NavDestinationInfo\> | UnsubscribeCallback | 401 | NavDestination 状态变化监听（global） | AC-1.1 |
| uiObserver.on('navDestinationUpdate', {navigationId}, cb) | Public | navigationId: ResourceStr, callback | UnsubscribeCallback | 401 | NavDestination 状态变化监听（navigationId scope） | AC-1.2 |
| UIObserver.on('navDestinationUpdateByUniqueId', navigationUniqueId, cb) | Public | navigationUniqueId: number, callback | UnsubscribeCallback | 401 | NavDestination 状态变化监听（uniqueId scope, @since 20） | AC-1.3 |
| uiObserver.on('navDestinationSwitch', context, cb) | Public | context: UIAbilityContext \| UIContext, callback | UnsubscribeCallback | 401 | NavDestination 切换监听 | AC-2.1 |
| uiObserver.on('navDestinationSwitch', context, options, cb) | Public | context, options: {navigationId}, callback | UnsubscribeCallback | 401 | NavDestination 切换监听（navigationId scope） | AC-2.2 |
| uiObserver.on('routerPageUpdate', context, cb) | Public | context: UIAbilityContext \| UIContext, callback: Callback\<RouterPageInfo\> | UnsubscribeCallback | 401 | 路由页面状态监听 | AC-3.1~3.2 |
| uiObserver.on('scrollEvent', cb) | Public | callback: Callback\<ScrollEventInfo\> | UnsubscribeCallback | 401 | 滚动状态监听（global） | AC-4.1 |
| uiObserver.on('scrollEvent', {id}, cb) | Public | id: string, callback | UnsubscribeCallback | 401 | 滚动状态监听（id scope） | AC-4.2 |
| uiObserver.on('densityUpdate', UIContext, cb) | Public | UIContext, callback: Callback\<DensityInfo\> | UnsubscribeCallback | 401 | 屏幕密度变化监听 | AC-5.1 |
| uiObserver.on('willDraw', UIContext, cb) | Public | UIContext, callback: Callback\<void\> | UnsubscribeCallback | 401 | 即将绘制监听 | AC-6.1 |
| uiObserver.on('didLayout', UIContext, cb) | Public | UIContext, callback: Callback\<void\> | UnsubscribeCallback | 401 | 布局完成监听 | AC-6.2 |
| uiObserver.on('tabContentUpdate', cb) | Public | callback: Callback\<TabContentInfo\> | UnsubscribeCallback | 401 | Tab 内容页状态监听（global） | AC-7.1 |
| uiObserver.on('tabContentUpdate', {id}, cb) | Public | id: string, callback | UnsubscribeCallback | 401 | Tab 内容页状态监听（id scope） | AC-7.2 |
| uiObserver.on('tabChange', cb) | Public | callback: Callback\<TabContentInfo\> | UnsubscribeCallback | 401 | Tab 切换监听（global） | AC-7.6 |
| uiObserver.on('tabChange', {id}, cb) | Public | id: string, callback | UnsubscribeCallback | 401 | Tab 切换监听（id scope） | AC-7.7 |
| UIObserver.on('willClick', ClickEventListenerCallback) | Public | callback: ClickEventListenerCallback | void | — | 点击事件即将触发监听（UIObserver 实例方法） | AC-8.1 |
| UIObserver.on('willClick', GestureEventListenerCallback) | Public | callback: GestureEventListenerCallback | void | — | Tap 手势事件即将触发监听（第二重载） | AC-8.4 |
| UIObserver.on('didClick', ClickEventListenerCallback) | Public | callback: ClickEventListenerCallback | void | — | 点击事件完成监听 | AC-8.2 |
| UIObserver.on('beforePanStart', PanListenerCallback) | Public | callback: PanListenerCallback | void | — | Pan 手势即将开始监听（@since 19） | AC-8.6 |
| UIObserver.on('beforePanEnd', PanListenerCallback) | Public | callback: PanListenerCallback | void | — | Pan 手势即将结束监听（@since 19） | AC-8.7 |
| UIObserver.on('afterPanStart', PanListenerCallback) | Public | callback: PanListenerCallback | void | — | Pan 手势已开始监听（@since 19） | AC-8.8 |
| UIObserver.on('afterPanEnd', PanListenerCallback) | Public | callback: PanListenerCallback | void | — | Pan 手势已结束监听（@since 19） | AC-8.9 |
| UIObserver.on('nodeRenderState', nodeIdentity, cb) | Public | nodeIdentity: NodeIdentity(string \| number), callback: NodeRenderStateChangeCallback | UnsubscribeCallback | 401 | 节点渲染可见性监听（@since 20） | AC-9.1 |
| uiObserver.on('textChange', {id}, cb) | Public | id: string, callback: Callback\<TextChangeEventInfo\> | UnsubscribeCallback | 401 | 文本变化监听（API 22+） | AC-10.1 |
| UIObserver.onSwiperContentUpdate(cb) | Public | callback: Callback\<SwiperContentInfo\> | void | — | Swiper 内容更新监听（命名方法，API 22+） | AC-10.3 |
| UIObserver.onRouterPageSizeChange(cb) | Public | callback: Callback\<RouterPageInfo\> | void | — | 路由页面尺寸变化监听（命名方法，API 23+） | AC-10.5 |
| UIObserver.onNavDestinationSizeChange(cb) | Public | callback: Callback\<NavDestinationInfo\> | void | — | NavDestination 尺寸变化监听（命名方法，API 23+） | AC-10.6 |
| UIObserver.onNavDestinationSizeChangeByUniqueId(navigationUniqueId, cb) | Public | navigationUniqueId: number, callback: Callback\<NavDestinationInfo\> | void | — | NavDestination 尺寸变化监听（uniqueId scope, 命名方法，API 23+） | AC-10.7 |
| uiObserver.on('windowSizeLayoutBreakpointChange', cb) | Public | callback: Callback\<WindowSizeLayoutBreakpointInfo\> | UnsubscribeCallback | 401 | 窗口布局断点变化监听（API 22+） | AC-10.8 |
| UIObserver.addGlobalGestureListener(type, option, cb) | Public | type: GestureListenerType, option: GestureObserverConfigs, callback: GestureListenerCallback | void | — | 全局手势监听（@since 20） | AC-11.1 |
| UIObserver.removeGlobalGestureListener(type, cb?) | Public | type: GestureListenerType, callback?: GestureListenerCallback | void | — | 移除全局手势监听（@since 20） | AC-11.2 |

### 变更/废弃 API

| 原有 API | 变更类型 | 新 API | 迁移说明 |
|----------|----------|--------|----------|
| NavDestinationState (API 11: ON_SHOWN=0, ON_HIDDEN=1) | 变更（扩展枚举值） | NavDestinationState (API 12: +ON_APPEAR=2, ON_DISAPPEAR=3, ON_WILL_SHOW=4, ON_WILL_HIDE=5, ON_WILL_APPEAR=6, ON_WILL_DISAPPEAR=7, ON_BACKPRESS=100; API 17: +ON_ACTIVE=8, ON_INACTIVE=9) | 旧值 ON_SHOWN=0/ON_HIDDEN=1 不变，新增值向后兼容 |

## 接口规格

### 接口定义

**NavDestinationState（枚举）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enum NavDestinationState` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.4~1.14 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| ON_SHOWN | number | — | 0 | @since 11 |
| ON_HIDDEN | number | — | 1 | @since 11 |
| ON_APPEAR | number | — | 2 | @since 12 |
| ON_DISAPPEAR | number | — | 3 | @since 12 |
| ON_WILL_SHOW | number | — | 4 | @since 12 |
| ON_WILL_HIDE | number | — | 5 | @since 12 |
| ON_WILL_APPEAR | number | — | 6 | @since 12 |
| ON_WILL_DISAPPEAR | number | — | 7 | @since 12 |
| ON_BACKPRESS | number | — | 100 | @since 12，跳号设计 |
| ON_ACTIVE | number | — | 8 | @since 17 |
| ON_INACTIVE | number | — | 9 | @since 17 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | NavDestination 已显示 | state = ON_SHOWN(0) | AC-1.4 |
| 2 | NavDestination 已隐藏 | state = ON_HIDDEN(1) | AC-1.5 |
| 3 | NavDestination 已出现 | state = ON_APPEAR(2) | AC-1.6 |
| 4 | NavDestination 已消失 | state = ON_DISAPPEAR(3) | AC-1.7 |
| 5 | NavDestination 即将显示 | state = ON_WILL_SHOW(4) | AC-1.8 |
| 6 | NavDestination 即将隐藏 | state = ON_WILL_HIDE(5) | AC-1.9 |
| 7 | NavDestination 即将出现 | state = ON_WILL_APPEAR(6) | AC-1.10 |
| 8 | NavDestination 即将消失 | state = ON_WILL_DISAPPEAR(7) | AC-1.11 |
| 9 | 用户按下返回键 | state = ON_BACKPRESS(100) | AC-1.12 |
| 10 | NavDestination 已激活 | state = ON_ACTIVE(8) | AC-1.13 |
| 11 | NavDestination 已失活 | state = ON_INACTIVE(9) | AC-1.14 |

---

**RouterPageState（枚举）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enum RouterPageState` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.3~3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| ABOUT_TO_APPEAR | number | — | 0 | @since 11 |
| ABOUT_TO_DISAPPEAR | number | — | 1 | @since 11 |
| ON_PAGE_SHOW | number | — | 2 | @since 11 |
| ON_PAGE_HIDE | number | — | 3 | @since 11 |
| ON_BACK_PRESS | number | — | 4 | @since 11 |

---

**ScrollEventType（枚举）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enum ScrollEventType` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.3~4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| SCROLL_START | number | — | 0 | @since 12 |
| SCROLL_STOP | number | — | 1 | @since 12 |

---

**TabContentState（枚举）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enum TabContentState` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-7.3~7.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| ON_SHOW | number | — | 0 | @since 12 |
| ON_HIDE | number | — | 1 | @since 12 |

---

**NodeRenderState（枚举，@since 20）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enum NodeRenderState` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-9.2~9.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| ABOUT_TO_RENDER_IN | number | — | 0 | @since 20 |
| ABOUT_TO_RENDER_OUT | number | — | 1 | @since 20 |

---

**GestureListenerType（枚举，@since 20）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `const enum GestureListenerType` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-11.3~11.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| TAP | number | — | 0 | @since 20 |
| LONG_PRESS | number | — | 1 | @since 20 |
| PAN | number | — | 2 | @since 20 |
| PINCH | number | — | 3 | @since 20 |
| SWIPE | number | — | 4 | @since 20 |
| ROTATION | number | — | 5 | @since 20 |

## 兼容性声明

- **已有 API 行为变更:** 是 — NavDestinationState 在 API 12 扩展枚举值（从 2 值到 8+2 值），旧值 ON_SHOWN=0/ON_HIDDEN=1 不变，新增值向后兼容
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 11
- **API 版本号策略:** @since 标注每个新增枚举值和接口的版本号

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| NavDestinationState ON_BACKPRESS=100 跳号 | 值 10-99 预留给未来扩展 | AC-1.12 |
| NodeRenderStatusMonitor 64 限制 | 最多 64 节点，超限静默失败 | AC-9.1 |
| GestureObserver 双 static map | NAPI 和 ANI 各有独立全局手势回调 map | AC-8.11 |
| 各 on() 类型 scope 支持不同 | 见 design.md Context scope mapping | 全部 AC |
| NavDestinationState API 版本渐进扩展 | API 11→12→17 逐步追加枚举值 | AC-1.4~1.14 |
| 手势监听为 UIObserver 实例方法 | 无 context 参数，已通过 getUIContext() 限定 scope | AC-8.1~8.9 |
| 4 个命名方法不使用 on(type) 模式 | onSwiperContentUpdate/onRouterPageSizeChange/onNavDestinationSizeChange/onNavDestinationSizeChangeByUniqueId | AC-10.3~10.7 |
| nodeRenderState 直接参数 NodeIdentity | 非 options 对象；@since 20 | AC-9.1 |
| navDestinationUpdateByUniqueId 直接参数 | navigationUniqueId: number，非 options 对象；@since 20 | AC-1.3 |
| tabChange 回调类型为 TabContentInfo | 无单独 TabChangeInfo；index/lastIndex 非 newIndex/oldIndex | AC-7.8 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | HandleFunc 惰性注册，未使用 type 零开销 | 单测 | observer_handler.cpp |
| 内存 | 每个监听器约 1 UIObserverListener 对象 | 代码评审 | ui_observer_listener.h |
| 可测试性 | 各 on() type 可独立 mock Notify 触发 | 单测/XTS | — |
| 自动化维测 | 401 错误码覆盖所有非法参数场景 | XTS | — |
| 定界定位 | Scoped map 按 key 分区 | 代码评审 | — |

## 多设备适配声明

无差异 — Observer 功能在所有设备类型上行为一致。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | Observer 不涉及无障碍 | — |
| 大字体 | 否 | Observer 不涉及大字体 | — |
| 深色模式 | 否 | Observer 不涉及深色模式 | — |
| 多窗口/分屏 | 是 | 每个 UIContext 独立 instanceId | 多窗口监听器分区 |
| 多用户 | 否 | Observer 不涉及多用户 | — |
| 版本升级 | 是 | NavDestinationState 等枚举渐进扩展 | API 11→12→17→19→20→22→23 |
| 生态兼容 | 否 | Observer 无权限要求 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/interface_sdk-js"
    query: "@ohos.arkui.observer.d.ts and @ohos.arkui.UIContext.d.ts on/off function signatures, enums, and callback types"
  - repo: "openharmony/arkui_ace_engine"
    query: "UIObserverListener On* callback parameter construction for each on() type"
  - repo: "openharmony/arkui_ace_engine"
    query: "NavDestinationPattern NotifyNavigationStateChange trigger points and NavDestinationState mapping"
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollPattern NotifyScrollEvent trigger and ScrollEventType mapping"
  - repo: "openharmony/arkui_ace_engine"
    query: "TabContentPattern NotifyTabContentState and TabPattern NotifyTabChange trigger points"
  - repo: "openharmony/arkui_ace_engine"
    query: "GestureObserver AddGlobalGestureListener and Pan/Click/Tap callback static maps"
```

**关键文档：** `/interface/sdk-js/api/@ohos.arkui.observer.d.ts`, `/interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`, `/ace_engine/interfaces/napi/kits/observer/ui_observer_listener.cpp`, `/ace_engine/interfaces/ets/ani/observer/src/observer.cpp`
