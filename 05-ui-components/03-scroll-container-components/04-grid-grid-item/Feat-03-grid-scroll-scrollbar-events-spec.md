# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Grid 滚动控制、滚动条与事件 |
| 特性编号 | Func-05-03-04-Feat-03 |
| 所属 Epic | Grid/GridItem 组件规格补录 |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 存量特性补录（lineage: new-on-legacy），本规格补录已有实现的行为。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | scrollBar(BarState) | 滚动条显示状态控制；API 10 默认值从 Off 变为 Auto |
| ADDED | scrollBarColor(Color|number|string|Resource) | 滚动条颜色；Resource overload @since 22 |
| ADDED | scrollBarWidth(number|string|Resource) | 滚动条宽度；Resource overload @since 26 |
| ADDED | scrollBarMargin(ScrollBarMargin) | 滚动条边距（继承 ScrollableCommonMethod @since 20） |
| ADDED | onScrollBarUpdate(ComputedBarAttribute) | 滚动条位置回调 @since 10 |
| ADDED | edgeEffect(EdgeEffect, EdgeEffectOptions) | 边缘效果 @since 10 |
| ADDED | nestedScroll(NestedScrollOptions) | 嵌套滚动配置 @since 10 |
| ADDED | enableScrollInteraction(boolean) | 滚动交互开关 @since 10 |
| ADDED | friction(number|Resource) | 滚动摩擦系数 @since 10 |
| ADDED | contentStartOffset/contentEndOffset | 内容偏移（继承 @since 22） |
| ADDED | clipContent(ContentClipMode|RectShape) | 内容裁剪模式（继承 @since 14） |
| ADDED | fadingEdge | 渐隐边缘效果（继承 @since 14） |
| ADDED | backToTop(boolean) | 双击回顶（继承 @since 15） |
| ADDED | enableScrollWithMouse | 鼠标滚动开关（继承 @since 26） |
| ADDED | autoAdjustScrollBarMargin | 滚动条边距自动调整（继承 @since 26） |
| ADDED | digitalCrownSensitivity(CrownSensitivity) | 表冠灵敏度（继承 @since 18，穿戴设备） |
| ADDED | flingSpeedLimit(number) | 惯性滚动速度上限 @since 11 |
| ADDED | Scroller 控制器方法集 | scrollToIndex/scrollEdge/scrollTo/scrollBy/scrollPage/fling/currentOffset/offset/isAtEnd/getItemRect/getItemIndex |
| ADDED | onScroll（DEPRECATED @since 12） | 滚动事件旧版，替代为 onDidScroll |
| ADDED | onDidScroll | 滚动事件新版 @since 12 |
| ADDED | onWillScroll | 滚动前拦截 @since 12（继承），@since 23（Grid 专属） |
| ADDED | onScrollFrameBegin | 滚动帧开始回调 @since 10，返回 ScrollResult |
| ADDED | onScrollStart | 滚动开始回调 @since 10 |
| ADDED | onScrollStop | 滚动停止回调 @since 10 |
| ADDED | onScrollIndex(first, last) | 滚动可见项索引回调 @since 7(first only)/10(first+last) |
| ADDED | onReachStart | 到达起始位置回调 @since 10 |
| ADDED | onReachEnd | 到达末尾位置回调 @since 10 |
| ADDED | onWillStartDragging/onWillStopDragging/onDidStopDragging | 拖拽生命周期回调 @since 20-21 |
| ADDED | onWillStartFling/onDidStopFling | 惯性滚动生命周期回调 @since 21 |

## 输入文档

- 需求基线：已有能力补录（无独立 requirement.md）
- 设计文档：`05-ui-components/03-scroll-container-components/04-grid-grid-item/design.md`
- 源码定位：`frameworks/core/components_ng/pattern/grid/`、`frameworks/core/components_ng/pattern/scrollable/`

## 用户故事

### US-1: 开发者控制滚动条外观与行为

作为 ArkUI 开发者，我想要配置 Grid 滚动条的显示状态、颜色、宽度、边距，以便滚动条视觉呈现与产品风格一致。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN scrollBar=BarState.Off THEN 滚动条不可见 | 正常 |
| AC-1.2 | WHEN scrollBar=BarState.Auto THEN 滚动条在用户交互时显示，静止时淡出 | 正常 |
| AC-1.3 | WHEN scrollBar=BarState.On THEN 滚动条常驻显示 | 正常 |
| AC-1.4 | WHEN scrollBar 未设置且 IsConfiguredScrollable()=true THEN 默认值=Auto（API ≥10） | 正常 |
| AC-1.5 | WHEN scrollBar 未设置且 IsConfiguredScrollable()=false THEN OnModifyDone 自动设 scrollBar(OFF) | 边界 |
| AC-1.6 | WHEN scrollBarColor='#ff0000' THEN 滚动条颜色为红色（默认 '#182431' 40%透明度） | 正常 |
| AC-1.7 | WHEN scrollBarColor 使用 Resource 类型 THEN @since 22 支持 Resource overload | 正常 |
| AC-1.8 | WHEN scrollBarWidth=8vp THEN 滚动条宽度为 8vp（默认 4vp） | 正常 |
| AC-1.9 | WHEN scrollBarWidth 使用 Resource 类型 THEN @since 26 支持 Resource overload | 正常 |
| AC-1.10 | WHEN scrollBarMargin={start:10vp, end:10vp} THEN 滚动条与容器边缘间距生效 | 正常 |
| AC-1.11 | WHEN onScrollBarUpdate 回调触发 THEN 回调参数 ComputedBarAttribute 包含 totalOffset 和 totalLength | 正常 |

### US-2: 开发者配置边缘效果与嵌套滚动

作为 ArkUI 开发者，我想要设置 edgeEffect 控制滚动到边界时的视觉反馈，以及 nestedScroll 配置嵌套滚动方向传递规则。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN edgeEffect=EdgeEffect.Spring THEN 滚动到边界时产生弹簧回弹效果 | 正常 |
| AC-2.2 | WHEN edgeEffect=EdgeEffect.Fade THEN 滚动到边界时内容渐隐 | 正常 |
| AC-2.3 | WHEN edgeEffect=EdgeEffect.None THEN 滚动到边界时无效果，直接停止 | 正常 |
| AC-2.4 | WHEN edgeEffect=EdgeEffect.Spring 且 canOverScroll=true THEN 支持弹性过度滚动 | 边界 |
| AC-2.5 | WHEN nestedScroll 设置 forward/backward 各方向的 NestedScrollMode THEN 嵌套滚动按配置传递 | 正常 |
| AC-2.6 | WHEN nestedScroll.forward=NestedScrollMode.PARENT_FIRST THEN 子 Grid 先将滚动事件传递给父容器 | 正常 |
| AC-2.7 | WHEN nestedScroll.backward=NestedScrollMode.SELF_FIRST THEN 子 Grid 先消耗自身滚动量，剩余传给父 | 正常 |

### US-3: 开发者配置滚动交互与摩擦系数

作为 ArkUI 开发者，我想要控制 enableScrollInteraction 开关和 friction 摩擦系数，以便在特定场景下禁用用户滚动或调整滚动减速速率。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN enableScrollInteraction=true THEN 用户可通过手势/鼠标滚动 Grid | 正常 |
| AC-3.2 | WHEN enableScrollInteraction=false THEN 用户手势/鼠标滚动不触发 Grid 滚动（默认 true） | 边界 |
| AC-3.3 | WHEN friction=0.7 THEN 滚动减速速率受摩擦系数影响（默认值因平台版本不同） | 正常 |
| AC-3.4 | WHEN friction 使用 Resource 类型 THEN 框架从资源加载摩擦系数 | 正常 |
| AC-3.5 | WHEN flingSpeedLimit=6000 THEN 惯性滚动最大速度为 6000vp/s（默认 9000vp/s） | 正常 |
| AC-3.6 | WHEN flingSpeedLimit=0 THEN 惯性滚动被完全禁用 | 边界 |

### US-4: 开发者使用继承的滚动辅助属性

作为 ArkUI 开发者，我想要使用 contentStartOffset/contentEndOffset、clipContent、fadingEdge、backToTop、enableScrollWithMouse、autoAdjustScrollBarMargin、digitalCrownSensitivity 等继承属性，以便实现更丰富的滚动体验。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN contentStartOffset=50vp THEN 滚动到起始位置时内容留有 50vp 偏移空间 | 正常 |
| AC-4.2 | WHEN contentEndOffset=50vp THEN 滚动到末尾位置时内容留有 50vp 偏移空间 | 正常 |
| AC-4.3 | WHEN clipContent=ContentClipMode.CLIP THEN 滚动区域外内容被裁剪 | 正常 |
| AC-4.4 | WHEN clipContent=RectShape{left:0, top:0, width:300, height:500} THEN 按指定矩形裁剪内容 | 正常 |
| AC-4.5 | WHEN fadingEdge=true THEN 滚动边缘内容渐隐 | 正常 |
| AC-4.6 | WHEN backToTop=true THEN 双击空白区域回滚到起始位置 | 正常 |
| AC-4.7 | WHEN enableScrollWithMouse=true THEN 鼠标滚轮可驱动 Grid 滚动 | 正常 |
| AC-4.8 | WHEN autoAdjustScrollBarMargin=true THEN 滚动条边距根据容器尺寸自动调整 | 正常 |
| AC-4.9 | WHEN digitalCrownSensitivity=CrownSensitivity.HIGH THEN 穿戴设备表冠灵敏度设为高 | 正常 |

### US-5: 开发者使用 Scroller 控制器驱动滚动

作为 ArkUI 开发者，我想要通过绑定 Scroller 控制器编程式控制 Grid 滚动位置、获取偏移量与子项信息。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN scroller.scrollToIndex(5) THEN Grid 滚动到第 5 个子项位置 | 正常 |
| AC-5.2 | WHEN scroller.scrollToIndex(5, true, GridAlignment.CENTER) THEN 平滑滚动到第 5 个子项且居中对齐 | 正常 |
| AC-5.3 | WHEN scroller.scrollToIndex 未指定 align THEN Grid 默认使用 GridAlignment.AUTO | 边界 |
| AC-5.4 | WHEN scroller.scrollEdge(EdgeType.TOP) THEN Grid 滚动到顶部 | 正常 |
| AC-5.5 | WHEN scroller.scrollTo({offset:200, smooth:true}) THEN 平滑滚动到偏移 200vp 位置 | 正常 |
| AC-5.6 | WHEN scroller.scrollBy(50, 0) THEN Grid 水平方向相对滚动 50vp | 正常 |
| AC-5.7 | WHEN scroller.scrollPage({next:true}) THEN Grid 向下滚动一页 | 正常 |
| AC-5.8 | WHEN scroller.fling(500) THEN 以速度 500 启动惯性滚动 | 正常 |
| AC-5.9 | WHEN scroller.currentOffset() THEN 返回当前偏移量 {xOffset, yOffset} | 正常 |
| AC-5.10 | WHEN scroller.offset() THEN 返回当前偏移量（@since 23 新增） | 正常 |
| AC-5.11 | WHEN scroller.isAtEnd() THEN 返回 boolean 表示是否到达末尾 | 正常 |
| AC-5.12 | WHEN scroller.getItemRect(3) THEN 返回第 3 个子项的 Rect {left, top, width, height} | 正常 |
| AC-5.13 | WHEN scroller.getItemIndex(100, 200) THEN 返回坐标 (100,200) 位置的子项索引 | 正常 |
| AC-5.14 | WHEN Grid 处于双模板模式（IsConfiguredScrollable()=false）THEN Scroller 方法不触发滚动 | 边界 |

### US-6: 开发者监听滚动事件

作为 ArkUI 开发者，我想要注册 onDidScroll、onWillScroll、onScrollFrameBegin、onScrollStart、onScrollStop、onScrollIndex 等回调，以便响应滚动状态变化。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN onDidScroll 注册 THEN 滚动过程中回调触发，参数为 (offset, state) | 正常 |
| AC-6.2 | WHEN onScroll 注册 THEN 滚动回调触发但该 API 自 @since 12 已 DEPRECATED，应使用 onDidScroll | 边界 |
| AC-6.3 | WHEN onWillScroll 注册 THEN 滚动前拦截回调触发，返回值可修改偏移量 | 正常 |
| AC-6.4 | WHEN onWillScroll 返回额外偏移量 THEN 实际滚动偏移 = 计算偏移 + 回调返回的额外偏移 | 正常 |
| AC-6.5 | WHEN onScrollFrameBegin 注册 THEN 每帧滚动前回调触发，返回 ScrollResult {offsetRemain} | 正常 |
| AC-6.6 | WHEN onScrollFrameBegin 返回 ScrollResult.offsetRemain=剩余偏移 THEN 该剩余量在后续帧继续消耗 | 正常 |
| AC-6.7 | WHEN onScrollStart 注册 THEN 滚动开始时回调触发 | 正常 |
| AC-6.8 | WHEN onScrollStop 注册 THEN 滚动停止时回调触发 | 正常 |
| AC-6.9 | WHEN onScrollIndex 注册 THEN 滚动过程中回调参数为 (firstVisibleItemIndex, lastVisibleItemIndex) | 正常 |
| AC-6.10 | WHEN onScrollIndex @since 7 版本 THEN 回调仅提供 first 参数（单参数版本） | 边界 |
| AC-6.11 | WHEN onReachStart 注册 THEN 滚动到起始位置时回调触发 | 正常 |
| AC-6.12 | WHEN onReachEnd 注册 THEN 滚动到末尾位置时回调触发 | 正常 |

### US-7: 开发者监听拖拽与惯性滚动生命周期

作为 ArkUI 开发者，我想要注册 onWillStartDragging、onWillStopDragging、onDidStopDragging、onWillStartFling、onDidStopFling 回调，以便精细控制拖拽和惯性滚动的交互阶段。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7.1 | WHEN onWillStartDragging 注册且用户开始拖拽 THEN 回调触发，返回 boolean 表示是否允许拖拽 | 正常 |
| AC-7.2 | WHEN onWillStartDragging 返回 false THEN 拖拽不启动，不产生滚动 | 边界 |
| AC-7.3 | WHEN onWillStopDragging 注册且用户停止拖拽 THEN 回调触发，返回 boolean 表示是否允许停止拖拽进入惯性 | 正常 |
| AC-7.4 | WHEN onDidStopDragging 注册 THEN 拖拽停止后回调触发 | 正常 |
| AC-7.5 | WHEN onWillStartFling 注册且即将开始惯性滚动 THEN 回调触发，返回 boolean 表示是否允许惯性 | 正常 |
| AC-7.6 | WHEN onWillStartFling 返回 false THEN 不启动惯性滚动 | 边界 |
| AC-7.7 | WHEN onDidStopFling 注册 THEN 惯性滚动停止后回调触发 | 正常 |

### US-8: onItemDragStart 禁用鼠标滚动

作为 ArkUI 开发者，我想要了解当 Grid 处于编辑模式（onItemDragStart 注册）时，鼠标滚轮行为的变化。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-8.1 | WHEN onItemDragStart 注册 THEN GetIsAllowMouse() 返回 false，鼠标滚轮不触发滚动 | 正常 |
| AC-8.2 | WHEN onItemDragStart 未注册 THEN GetIsAllowMouse() 返回 true，鼠标滚轮可触发滚动 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-GRID-03 | UT: scrollBar(Off) | scrollable_pattern.cpp |
| AC-1.2 | R-2 | TASK-GRID-03 | UT: scrollBar(Auto) 淡出 | scroll_bar_modifier.cpp |
| AC-1.3 | R-3 | TASK-GRID-03 | UT: scrollBar(On) 常驻 | scrollable_pattern.cpp |
| AC-1.4 | R-4 | TASK-GRID-03 | UT: 默认值 Auto（API 10+） | grid_pattern.cpp:OnModifyDone |
| AC-1.5 | R-5 | TASK-GRID-03 | UT: 静态网格 scrollBar=OFF | grid_pattern.cpp:OnModifyDone |
| AC-1.6 | R-6 | TASK-GRID-03 | UT: scrollBarColor 设置 | scroll_bar_modifier.cpp |
| AC-1.7 | R-7 | TASK-GRID-03 | UT: Resource scrollBarColor | grid_model_ng.cpp |
| AC-1.8 | R-8 | TASK-GRID-03 | UT: scrollBarWidth 设置 | scroll_bar_modifier.cpp |
| AC-1.9 | R-9 | TASK-GRID-03 | UT: Resource scrollBarWidth | grid_model_ng.cpp |
| AC-1.10 | R-10 | TASK-GRID-03 | UT: scrollBarMargin | scrollable_common_method.cpp |
| AC-1.11 | R-11 | TASK-GRID-03 | UT: onScrollBarUpdate 回调 | scrollable_pattern.cpp |
| AC-2.1 | R-12 | TASK-GRID-03 | UT: EdgeEffect.Spring | scrollable_pattern.cpp |
| AC-2.2 | R-13 | TASK-GRID-03 | UT: EdgeEffect.Fade | scrollable_pattern.cpp |
| AC-2.3 | R-14 | TASK-GRID-03 | UT: EdgeEffect.None | scrollable_pattern.cpp |
| AC-2.4 | R-15 | TASK-GRID-03 | UT: Spring+canOverScroll | scrollable_pattern.cpp |
| AC-2.5 | R-16 | TASK-GRID-03 | UT: nestedScroll 配置 | scrollable_pattern.cpp |
| AC-2.6 | R-16 | TASK-GRID-03 | UT: PARENT_FIRST | nested_scroll_handler.cpp |
| AC-2.7 | R-16 | TASK-GRID-03 | UT: SELF_FIRST | nested_scroll_handler.cpp |
| AC-3.1 | R-17 | TASK-GRID-03 | UT: enableScrollInteraction=true | scrollable_pattern.cpp |
| AC-3.2 | R-18 | TASK-GRID-03 | UT: enableScrollInteraction=false 禁用手势 | scrollable_pattern.cpp |
| AC-3.3 | R-19 | TASK-GRID-03 | UT: friction 值影响减速 | scrollable_pattern.cpp |
| AC-3.4 | R-19 | TASK-GRID-03 | UT: Resource friction | scroll_model_ng.cpp |
| AC-3.5 | R-20 | TASK-GRID-03 | UT: flingSpeedLimit 限速 | scrollable_pattern.cpp |
| AC-3.6 | R-20 | TASK-GRID-03 | UT: flingSpeedLimit=0 禁用惯性 | scrollable_pattern.cpp |
| AC-4.1 | R-21 | TASK-GRID-03 | UT: contentStartOffset | scrollable_pattern.cpp |
| AC-4.2 | R-22 | TASK-GRID-03 | UT: contentEndOffset | scrollable_pattern.cpp |
| AC-4.3 | R-23 | TASK-GRID-03 | UT: clipContent CLIP | scrollable_pattern.cpp |
| AC-4.4 | R-24 | TASK-GRID-03 | UT: clipContent RectShape | scrollable_pattern.cpp |
| AC-4.5 | R-25 | TASK-GRID-03 | UT: fadingEdge | scrollable_pattern.cpp |
| AC-4.6 | R-26 | TASK-GRID-03 | UT: backToTop | scrollable_pattern.cpp |
| AC-4.7 | R-27 | TASK-GRID-03 | UT: enableScrollWithMouse | scrollable_pattern.cpp |
| AC-4.8 | R-28 | TASK-GRID-03 | UT: autoAdjustScrollBarMargin | scrollable_pattern.cpp |
| AC-4.9 | R-29 | TASK-GRID-03 | UT: digitalCrownSensitivity | scrollable_pattern.cpp |
| AC-5.1 | R-30 | TASK-GRID-03 | UT: scrollToIndex | grid_pattern.cpp |
| AC-5.2 | R-31 | TASK-GRID-03 | UT: scrollToIndex smooth+align | grid_pattern.cpp |
| AC-5.3 | R-32 | TASK-GRID-03 | UT: scrollToIndex 默认 AUTO | grid_pattern.cpp |
| AC-5.4 | R-33 | TASK-GRID-03 | UT: scrollEdge | scrollable_pattern.cpp |
| AC-5.5 | R-34 | TASK-GRID-03 | UT: scrollTo offset | scrollable_pattern.cpp |
| AC-5.6 | R-35 | TASK-GRID-03 | UT: scrollBy | scrollable_pattern.cpp |
| AC-5.7 | R-36 | TASK-GRID-03 | UT: scrollPage | scrollable_pattern.cpp |
| AC-5.8 | R-37 | TASK-GRID-03 | UT: fling velocity | scrollable_pattern.cpp |
| AC-5.9 | R-38 | TASK-GRID-03 | UT: currentOffset | scrollable_pattern.cpp |
| AC-5.10 | R-39 | TASK-GRID-03 | UT: offset @since 23 | scrollable_pattern.cpp |
| AC-5.11 | R-40 | TASK-GRID-03 | UT: isAtEnd | scrollable_pattern.cpp |
| AC-5.12 | R-41 | TASK-GRID-03 | UT: getItemRect | grid_pattern.cpp |
| AC-5.13 | R-42 | TASK-GRID-03 | UT: getItemIndex | grid_pattern.cpp |
| AC-5.14 | R-43 | TASK-GRID-03 | UT: 静态模式 Scroller 不触发 | grid_pattern.cpp |
| AC-6.1 | R-44 | TASK-GRID-03 | UT: onDidScroll 回调 | scrollable_pattern.cpp |
| AC-6.2 | R-45 | TASK-GRID-03 | UT: onScroll DEPRECATED 标注 | grid.d.ts |
| AC-6.3 | R-46 | TASK-GRID-03 | UT: onWillScroll 回调 | scrollable_pattern.cpp |
| AC-6.4 | R-47 | TASK-GRID-03 | UT: onWillScroll 返回额外偏移 | scrollable_pattern.cpp |
| AC-6.5 | R-48 | TASK-GRID-03 | UT: onScrollFrameBegin | scrollable_pattern.cpp |
| AC-6.6 | R-48 | TASK-GRID-03 | UT: ScrollResult offsetRemain | scrollable_pattern.cpp |
| AC-6.7 | R-49 | TASK-GRID-03 | UT: onScrollStart | scrollable_pattern.cpp |
| AC-6.8 | R-50 | TASK-GRID-03 | UT: onScrollStop | scrollable_pattern.cpp |
| AC-6.9 | R-51 | TASK-GRID-03 | UT: onScrollIndex | grid_pattern.cpp |
| AC-6.10 | R-51 | TASK-GRID-03 | UT: onScrollIndex 单参数版本 | grid.d.ts |
| AC-6.11 | R-52 | TASK-GRID-03 | UT: onReachStart | scrollable_pattern.cpp |
| AC-6.12 | R-53 | TASK-GRID-03 | UT: onReachEnd | scrollable_pattern.cpp |
| AC-7.1 | R-54 | TASK-GRID-03 | UT: onWillStartDragging 返回 true | scrollable_pattern.cpp |
| AC-7.2 | R-55 | TASK-GRID-03 | UT: onWillStartDragging 返回 false | scrollable_pattern.cpp |
| AC-7.3 | R-56 | TASK-GRID-03 | UT: onWillStopDragging | scrollable_pattern.cpp |
| AC-7.4 | R-57 | TASK-GRID-03 | UT: onDidStopDragging | scrollable_pattern.cpp |
| AC-7.5 | R-58 | TASK-GRID-03 | UT: onWillStartFling 返回 true | scrollable_pattern.cpp |
| AC-7.6 | R-59 | TASK-GRID-03 | UT: onWillStartFling 返回 false | scrollable_pattern.cpp |
| AC-7.7 | R-60 | TASK-GRID-03 | UT: onDidStopFling | scrollable_pattern.cpp |
| AC-8.1 | R-61 | TASK-GRID-03 | UT: onItemDragStart → GetIsAllowMouse=false | grid_pattern.cpp |
| AC-8.2 | R-62 | TASK-GRID-03 | UT: 无 onItemDragStart → GetIsAllowMouse=true | grid_pattern.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | scrollBar=Off | 滚动条不可见 |  | AC-1.1 |
| R-2 | 行为 | scrollBar=Auto | 滚动条交互时可见，静止后淡出 | 默认值（API ≥10）；API 7-9 默认为 Off | AC-1.2 |
| R-3 | 行为 | scrollBar=On | 滚动条常驻显示 |  | AC-1.3 |
| R-4 | 行为 | scrollBar 未设置 + IsConfiguredScrollable()=true | 默认 scrollBar=Auto | API 10+ 默认变更为 Auto | AC-1.4 |
| R-5 | 行为 | IsConfiguredScrollable()=false | OnModifyDone 自动设 scrollBar(OFF) | 双模板/自适应模式下不显示滚动条 | AC-1.5 |
| R-6 | 行为 | scrollBarColor=颜色值 | 滚动条颜色改变 | 默认 '#182431'（40%透明度） | AC-1.6 |
| R-7 | 行为 | scrollBarColor=Resource | 从资源加载颜色 | @since 22；之前版本仅支持 Color|number|string | AC-1.7 |
| R-8 | 行为 | scrollBarWidth=宽度值 | 滚动条宽度改变 | 默认 4vp | AC-1.8 |
| R-9 | 行为 | scrollBarWidth=Resource | 从资源加载宽度 | @since 26 | AC-1.9 |
| R-10 | 行为 | scrollBarMargin={start, end} | 滚动条与容器边缘间距 | 继承 ScrollableCommonMethod @since 20 | AC-1.10 |
| R-11 | 行为 | onScrollBarUpdate 回调注册 | 滚动时回调 ComputedBarAttribute{totalOffset, totalLength} | totalOffset=总偏移量, totalLength=总内容长度 | AC-1.11 |
| R-12 | 行为 | edgeEffect=Spring | 边界弹簧回弹 | 滚动超限后弹性回位 | AC-2.1 |
| R-13 | 行为 | edgeEffect=Fade | 边界渐隐 | 内容到达边界后渐隐效果 | AC-2.2 |
| R-14 | 行为 | edgeEffect=None | 边界无效果 | 滚动到边界直接停止 | AC-2.3 |
| R-15 | 行为 | EdgeEffect.Spring + canOverScroll=true | 支持弹性过度滚动 | EdgeEffectOptions.canOverScroll 控制 | AC-2.4 |
| R-16 | 行为 | nestedScroll 配置 | 嵌套滚动方向传递按 NestedScrollMode 执行 | PARENT_FIRST/SELF_ONLY/SELF_FIRST 三种模式 | AC-2.5, AC-2.6, AC-2.7 |
| R-17 | 行为 | enableScrollInteraction=true | 用户手势/鼠标可驱动滚动 | 默认 true | AC-3.1 |
| R-18 | 边界 | enableScrollInteraction=false | 手势/鼠标不驱动滚动，但 Scroller 编程式滚动不受影响 | 默认 true；设 false 仅禁用用户交互 | AC-3.2 |
| R-19 | 行为 | friction=数值 | 滚动减速速率受摩擦系数影响 | 默认值因平台版本不同；Resource 支持 | AC-3.3, AC-3.4 |
| R-20 | 行为 | flingSpeedLimit=数值 | 惯性滚动最大速度受限 | 默认 9000vp/s；0=禁用惯性 | AC-3.5, AC-3.6 |
| R-21 | 行为 | contentStartOffset=数值 | 滚动到起始位置时内容留偏移空间 | 继承 @since 22 | AC-4.1 |
| R-22 | 行为 | contentEndOffset=数值 | 滚动到末尾位置时内容留偏移空间 | 继承 @since 22 | AC-4.2 |
| R-23 | 行为 | clipContent=CLIP | 超出滚动区域的内容裁剪 | 继承 @since 14 | AC-4.3 |
| R-24 | 行为 | clipContent=RectShape | 按指定矩形裁剪内容 | 继承 @since 14 | AC-4.4 |
| R-25 | 行为 | fadingEdge=true | 滚动边缘渐隐 | 继承 @since 14 | AC-4.5 |
| R-26 | 行为 | backToTop=true | 双击空白区域回滚到起始 | 继承 @since 15 | AC-4.6 |
| R-27 | 行为 | enableScrollWithMouse=true | 鼠标滚轮驱动滚动 | 继承 @since 26 | AC-4.7 |
| R-28 | 行为 | autoAdjustScrollBarMargin=true | 滚动条边距自动调整 | 继承 @since 26 | AC-4.8 |
| R-29 | 行为 | digitalCrownSensitivity=值 | 穿戴设备表冠灵敏度 | 继承 @since 18；仅穿戴设备 | AC-4.9 |
| R-30 | 行为 | scroller.scrollToIndex(index) | 滚动到指定索引子项 | @since 7 | AC-5.1 |
| R-31 | 行为 | scroller.scrollToIndex(index, smooth, align) | 平滑滚动到指定子项并按 align 对齐 | smooth=false 为跳转；align=CENTER/START/END/AUTO | AC-5.2 |
| R-32 | 行为 | scroller.scrollToIndex 未指定 align | Grid 默认 align=GridAlignment.AUTO | List 默认 CENTER；Grid 默认 AUTO | AC-5.3 |
| R-33 | 行为 | scroller.scrollEdge(edge) | 滚动到指定边界 | EdgeType.TOP/BOTTOM/START/END | AC-5.4 |
| R-34 | 行为 | scroller.scrollTo({offset, smooth}) | 滚动到指定偏移位置 | @since 7 | AC-5.5 |
| R-35 | 行为 | scroller.scrollBy(dx, dy) | 相对滚动指定距离 | @since 9 | AC-5.6 |
| R-36 | 行为 | scroller.scrollPage({next/prev}) | 翻页滚动 | @since 9 | AC-5.7 |
| R-37 | 行为 | scroller.fling(velocity) | 以指定速度启动惯性滚动 | @since 12 | AC-5.8 |
| R-38 | 行为 | scroller.currentOffset() | 返回 {xOffset, yOffset} | @since 7 | AC-5.9 |
| R-39 | 行为 | scroller.offset() | 返回当前偏移量 | @since 23；与 currentOffset 功能相同但 API 独立 | AC-5.10 |
| R-40 | 行为 | scroller.isAtEnd() | 返回 boolean | @since 10 | AC-5.11 |
| R-41 | 行为 | scroller.getItemRect(index) | 返回 Rect{left, top, width, height} | @since 11 | AC-5.12 |
| R-42 | 行为 | scroller.getItemIndex(x, y) | 返回坐标位置的子项索引 | @since 14 | AC-5.13 |
| R-43 | 边界 | IsConfiguredScrollable()=false | Scroller 方法不触发滚动 | 双模板模式无溢出空间 | AC-5.14 |
| R-44 | 行为 | onDidScroll 注册 | 滚动中回调 (offset, state) | @since 12；替代 onScroll | AC-6.1 |
| R-45 | 边界 | onScroll 注册 | 回调触发但 API 已 DEPRECATED（@since 12） | 应迁移到 onDidScroll | AC-6.2 |
| R-46 | 行为 | onWillScroll 注册 | 滚动前回调触发 | @since 12 继承，@since 23 Grid 专属；返回值可修改偏移 | AC-6.3 |
| R-47 | 行为 | onWillScroll 返回额外偏移 | 实际偏移 = 计算偏移 + 回调返回偏移 | 返回值类型为 number | AC-6.4 |
| R-48 | 行为 | onScrollFrameBegin 注册 | 每帧滚动前回调，返回 ScrollResult{offsetRemain} | offsetRemain 为未消耗偏移量，后续帧继续使用 | AC-6.5, AC-6.6 |
| R-49 | 行为 | onScrollStart 注册 | 滚动开始回调 | @since 10 | AC-6.7 |
| R-50 | 行为 | onScrollStop 注册 | 滚动停止回调 | @since 10 | AC-6.8 |
| R-51 | 行为 | onScrollIndex 注册 | 回调 (first, last) | @since 7 仅 first；@since 10 first+last | AC-6.9, AC-6.10 |
| R-52 | 行为 | onReachStart 注册 | 到达起始位置回调 | @since 10 | AC-6.11 |
| R-53 | 行为 | onReachEnd 注册 | 到达末尾位置回调 | @since 10 | AC-6.12 |
| R-54 | 行为 | onWillStartDragging 返回 true | 拖拽启动 | @since 21；返回 boolean | AC-7.1 |
| R-55 | 边界 | onWillStartDragging 返回 false | 拖拽不启动 |  | AC-7.2 |
| R-56 | 行为 | onWillStopDragging 注册 | 拖拽停止前回调 | @since 20；返回 boolean | AC-7.3 |
| R-57 | 行为 | onDidStopDragging 注册 | 拖拽停止后回调 | @since 21 | AC-7.4 |
| R-58 | 行为 | onWillStartFling 返回 true | 惯性滚动启动 | @since 21；返回 boolean | AC-7.5 |
| R-59 | 边界 | onWillStartFling 返回 false | 不启动惯性滚动 |  | AC-7.6 |
| R-60 | 行为 | onDidStopFling 注册 | 惯性停止后回调 | @since 21 | AC-7.7 |
| R-61 | 行为 | onItemDragStart 注册 | GetIsAllowMouse()=false | 编辑模式下鼠标滚轮不触发滚动 | AC-8.1 |
| R-62 | 边界 | onItemDragStart 未注册 | GetIsAllowMouse()=true | 非编辑模式下鼠标滚轮正常触发 | AC-8.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | scrollBar 三种状态 | UT: scrollBar(Off/Auto/On) | 滚动条可见性控制 |
| VM-2 | scrollBarColor/scrollBarWidth/scrollBarMargin | UT: 属性设置与 Resource overload | 默认值、类型支持、版本门槛 |
| VM-3 | onScrollBarUpdate 回调 | UT: ComputedBarAttribute 参数 | totalOffset 和 totalLength 正确性 |
| VM-4 | 静态网格 scrollBar=OFF | UT: IsConfiguredScrollable()=false | OnModifyDone 自动禁用 |
| VM-5 | edgeEffect 三种模式 | UT: Spring/Fade/None + canOverScroll | 边界视觉效果 |
| VM-6 | nestedScroll 传递模式 | UT: PARENT_FIRST/SELF_ONLY/SELF_FIRST | 嵌套滚动方向传递 |
| VM-7 | enableScrollInteraction | UT: true/false 开关 | 用户交互禁用不影响编程式滚动 |
| VM-8 | friction 与 flingSpeedLimit | UT: 摩擦系数和速度限制 | 减速速率和惯性最大速度 |
| VM-9 | 继承辅助属性 | UT: contentStartOffset/contentEndOffset/clipContent/fadingEdge/backToTop/enableScrollWithMouse/autoAdjustScrollBarMargin/digitalCrownSensitivity | 各继承属性独立行为 |
| VM-10 | Scroller 控制器方法集 | UT: scrollToIndex/scrollEdge/scrollTo/scrollBy/scrollPage/fling/currentOffset/offset/isAtEnd/getItemRect/getItemIndex | 方法调用返回值和行为 |
| VM-11 | scrollToIndex 默认 align=AUTO | UT: Grid vs List align 默认值差异 | Grid 默认 AUTO |
| VM-12 | 静态模式 Scroller 不触发 | UT: 双模板下 Scroller 方法无效果 | IsConfiguredScrollable()=false 守卫 |
| VM-13 | onDidScroll / onScroll DEPRECATED | UT: onDidScroll 正常回调 + onScroll DEPRECATED 标注 | 版本迁移 |
| VM-14 | onWillScroll 偏移修改 | UT: onWillScroll 返回额外偏移 | 偏移叠加逻辑 |
| VM-15 | onScrollFrameBegin ScrollResult | UT: offsetRemain 剩余偏移 | 分帧消耗 |
| VM-16 | onScrollIndex 参数演进 | UT: first only / first+last | @since 7 vs @since 10 参数数量 |
| VM-17 | 拖拽与惯性生命周期回调 | UT: onWillStartDragging/onWillStopDragging/onDidStopDragging/onWillStartFling/onDidStopFling | 返回 boolean 控制 |
| VM-18 | onItemDragStart 禁用鼠标滚动 | UT: GetIsAllowMouse() 返回值 | 编辑模式鼠标交互守卫 |

## API 变更分析

### 新增 API

> 本规格为存量补录，以下 API 已在 SDK 中存在。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| scrollBar(BarState) | Public | BarState | GridAttribute | 无 | 滚动条状态 | AC-1.1–1.5 |
| scrollBarColor(Color|number|string|Resource) | Public | Color|number|string|Resource | GridAttribute | 无 | 滚动条颜色 | AC-1.6, AC-1.7 |
| scrollBarWidth(number|string|Resource) | Public | number|string|Resource | GridAttribute | 无 | 滚动条宽度 | AC-1.8, AC-1.9 |
| scrollBarMargin(ScrollBarMargin) | Public | ScrollBarMargin | GridAttribute | 无 | 滚动条边距 (@since 20) | AC-1.10 |
| onScrollBarUpdate(callback) | Public | (ComputedBarAttribute) => void | GridAttribute | 无 | 滚动条位置回调 (@since 10) | AC-1.11 |
| edgeEffect(EdgeEffect) | Public | EdgeEffect | GridAttribute | 无 | 边缘效果 (@since 10) | AC-2.1–2.3 |
| edgeEffect(EdgeEffect, EdgeEffectOptions) | Public | EdgeEffect, EdgeEffectOptions | GridAttribute | 无 | 边缘效果+选项 (@since 10) | AC-2.4 |
| nestedScroll(NestedScrollOptions) | Public | NestedScrollOptions | GridAttribute | 无 | 嵌套滚动 (@since 10) | AC-2.5–2.7 |
| enableScrollInteraction(boolean) | Public | boolean | GridAttribute | 无 | 滚动交互开关 (@since 10) | AC-3.1, AC-3.2 |
| friction(number|Resource) | Public | number|Resource | GridAttribute | 无 | 摩擦系数 (@since 10) | AC-3.3, AC-3.4 |
| flingSpeedLimit(number) | Public | number | GridAttribute | 无 | 惯性速度上限 (@since 11) | AC-3.5, AC-3.6 |
| contentStartOffset(number) | Public | number | GridAttribute | 无 | 内容起始偏移 (@since 22) | AC-4.1 |
| contentEndOffset(number) | Public | number | GridAttribute | 无 | 内容末尾偏移 (@since 22) | AC-4.2 |
| clipContent(ContentClipMode|RectShape) | Public | ContentClipMode|RectShape | GridAttribute | 无 | 内容裁剪 (@since 14) | AC-4.3, AC-4.4 |
| fadingEdge(FadingEdgeOptions) | Public | FadingEdgeOptions | GridAttribute | 无 | 渐隐边缘 (@since 14) | AC-4.5 |
| backToTop(boolean) | Public | boolean | GridAttribute | 无 | 双击回顶 (@since 15) | AC-4.6 |
| enableScrollWithMouse(boolean) | Public | boolean | GridAttribute | 无 | 鼠标滚动开关 (@since 26) | AC-4.7 |
| autoAdjustScrollBarMargin(boolean) | Public | boolean | GridAttribute | 无 | 滚动条边距自动调整 (@since 26) | AC-4.8 |
| digitalCrownSensitivity(CrownSensitivity) | Public | CrownSensitivity | GridAttribute | 无 | 表冠灵敏度 (@since 18) | AC-4.9 |
| Scroller.scrollToIndex | Public | index, smooth?, align?, options? | void | 无 | 滚动到指定项 (@since 7) | AC-5.1–5.3 |
| Scroller.scrollEdge | Public | EdgeType, options? | void | 无 | 滚动到边界 (@since 7) | AC-5.4 |
| Scroller.scrollTo | Public | ScrollToOptions | void | 无 | 滚动到偏移 (@since 7) | AC-5.5 |
| Scroller.scrollBy | Public | dx, dy | void | 无 | 相对滚动 (@since 9) | AC-5.6 |
| Scroller.scrollPage | Public | {next/prev} | void | 无 | 翻页 (@since 9) | AC-5.7 |
| Scroller.fling | Public | velocity | void | 无 | 惯性启动 (@since 12) | AC-5.8 |
| Scroller.currentOffset | Public | 无 | OffsetResult | 无 | 当前偏移 (@since 7) | AC-5.9 |
| Scroller.offset | Public | 无 | OffsetResult | 无 | 当前偏移 (@since 23) | AC-5.10 |
| Scroller.isAtEnd | Public | 无 | boolean | 无 | 是否到底 (@since 10) | AC-5.11 |
| Scroller.getItemRect | Public | index | RectResult | 无 | 子项矩形 (@since 11) | AC-5.12 |
| Scroller.getItemIndex | Public | x, y | number | 无 | 子项索引 (@since 14) | AC-5.13 |
| onScroll | Public | (offset, state) => void | GridAttribute | 无 | 滚动回调 (**DEPRECATED @since 12**) | AC-6.2 |
| onDidScroll | Public | (offset, state) => void | GridAttribute | 无 | 滚动回调 (@since 12) | AC-6.1 |
| onWillScroll | Public | (offset, state, source) => number | GridAttribute | 无 | 滚动前拦截 (@since 12, Grid @since 23) | AC-6.3, AC-6.4 |
| onScrollFrameBegin | Public | (offset) => ScrollResult | GridAttribute | 无 | 帧滚动回调 (@since 10) | AC-6.5, AC-6.6 |
| onScrollStart | Public | () => void | GridAttribute | 无 | 滚动开始 (@since 10) | AC-6.7 |
| onScrollStop | Public | () => void | GridAttribute | 无 | 滚动停止 (@since 10) | AC-6.8 |
| onScrollIndex | Public | (first, last) => void | GridAttribute | 无 | 可见项索引 (@since 7/10) | AC-6.9, AC-6.10 |
| onReachStart | Public | () => void | GridAttribute | 无 | 到达起始 (@since 10) | AC-6.11 |
| onReachEnd | Public | () => void | GridAttribute | 无 | 到达末尾 (@since 10) | AC-6.12 |
| onWillStartDragging | Public | () => boolean | GridAttribute | 无 | 拖拽拦截 (@since 21) | AC-7.1, AC-7.2 |
| onWillStopDragging | Public | () => boolean | GridAttribute | 无 | 拖拽停止拦截 (@since 20) | AC-7.3 |
| onDidStopDragging | Public | () => void | GridAttribute | 无 | 拖拽停止回调 (@since 21) | AC-7.4 |
| onWillStartFling | Public | () => boolean | GridAttribute | 无 | 惯性拦截 (@since 21) | AC-7.5, AC-7.6 |
| onDidStopFling | Public | () => void | GridAttribute | 无 | 惯性停止回调 (@since 21) | AC-7.7 |

### 变更/废弃 API

| API 名称 | 变更类型 | 说明 | 关联 AC |
|----------|----------|------|---------|
| onScroll | DEPRECATED | @since 12 标注 DEPRECATED，应迁移到 onDidScroll | AC-6.2 |
| scrollBar 默认值 | 行为变更 | API 7-9 默认 Off → API 10+ 默认 Auto | AC-1.4 |

## 接口规格

### 接口定义

**scrollBar**

| 属性 | 值 |
|------|-----|
| 函数签名 | `scrollBar(value: BarState): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 7) |
| 错误码 | N/A |
| 关联 AC | AC-1.1–1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | BarState (Off=0/Auto=1/On=2) | 是 | Auto（API ≥10）/ Off（API <10） | 双模板模式 OnModifyDone 自动设为 Off |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value=Off | 滚动条不可见 | AC-1.1 |
| 2 | value=Auto | 交互时可见，静止后淡出 | AC-1.2 |
| 3 | value=On | 常驻显示 | AC-1.3 |
| 4 | IsConfiguredScrollable()=false | OnModifyDone 设 scrollBar(OFF) | AC-1.5 |

---

**scrollBarColor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `scrollBarColor(value: Color | number | string | Resource): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 7, Resource @since 22) |
| 错误码 | N/A |
| 关联 AC | AC-1.6, AC-1.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | Color | number | string | Resource | 是 | '#182431'（40%透明度） | Resource 类型 @since 22 |

---

**scrollBarWidth**

| 属性 | 值 |
|------|-----|
| 函数签名 | `scrollBarWidth(value: number | string | Resource): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 7, Resource @since 26) |
| 错误码 | N/A |
| 关联 AC | AC-1.8, AC-1.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | string | Resource | 是 | 4vp | Resource 类型 @since 26 |

---

**scrollBarMargin**

| 属性 | 值 |
|------|-----|
| 函数签名 | `scrollBarMargin(value: ScrollBarMargin): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-1.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ScrollBarMargin | 是 | — | 继承自 ScrollableCommonMethod |

---

**onScrollBarUpdate**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onScrollBarUpdate(callback: (barAttribute: ComputedBarAttribute) => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-1.11 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (ComputedBarAttribute) => void | 是 | — | ComputedBarAttribute 含 totalOffset(number) 和 totalLength(number) |

---

**edgeEffect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `edgeEffect(value: EdgeEffect, options?: EdgeEffectOptions): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-2.1–2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | EdgeEffect (Spring/Fade/None) | 是 | None |  |
| options | EdgeEffectOptions | 否 | — | canOverScroll: boolean |

---

**nestedScroll**

| 属性 | 值 |
|------|-----|
| 函数签名 | `nestedScroll(value: NestedScrollOptions): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-2.5–2.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | NestedScrollOptions | 是 | — | forward: {default: SELF_ONLY}; backward: {default: SELF_ONLY} |

---

**enableScrollInteraction**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableScrollInteraction(value: boolean): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | true | false 时仅禁用用户交互，Scroller 编程式滚动不受影响 |

---

**friction**

| 属性 | 值 |
|------|-----|
| 函数签名 | `friction(value: number | Resource): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-3.3, AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | Resource | 是 | 因平台版本不同 | 值越大减速越快；默认值由 GetDefaultFriction() 决定 |

---

**flingSpeedLimit**

| 属性 | 值 |
|------|-----|
| 函数签名 | `flingSpeedLimit(value: number): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 11) |
| 错误码 | N/A |
| 关联 AC | AC-3.5, AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | 9000vp/s | 0 禁用惯性；负值视为无效 |

---

**Scroller 控制器方法集**

| 方法 | 签名 | @since | 返回值 | 关联 AC |
|------|------|--------|--------|---------|
| scrollToIndex | `scrollToIndex(value: number, smooth?: boolean, align?: GridAlignment, options?: ScrollToOptions): void` | 7 | void | AC-5.1–5.3 |
| scrollEdge | `scrollEdge(value: EdgeType, options?: ScrollEdgeOptions): void` | 7 | void | AC-5.4 |
| scrollTo | `scrollTo(options: ScrollToOptions): void` | 7 | void | AC-5.5 |
| scrollBy | `scrollBy(dx: number, dy: number): void` | 9 | void | AC-5.6 |
| scrollPage | `scrollPage(value: {next: boolean} | {prev: boolean}): void` | 9 | void | AC-5.7 |
| fling | `fling(velocity: number): void` | 12 | void | AC-5.8 |
| currentOffset | `currentOffset(): OffsetResult` | 7 | {xOffset, yOffset} | AC-5.9 |
| offset | `offset(): OffsetResult` | 23 | {xOffset, yOffset} | AC-5.10 |
| isAtEnd | `isAtEnd(): boolean` | 10 | boolean | AC-5.11 |
| getItemRect | `getItemRect(index: number): RectResult` | 11 | {left, top, width, height} | AC-5.12 |
| getItemIndex | `getItemIndex(x: number, y: number): number` | 14 | number (-1 if not found) | AC-5.13 |

**scrollToIndex 参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | — | 子项索引；超出范围无效 |
| smooth | boolean | 否 | false | true=平滑滚动，false=跳转 |
| align | GridAlignment | 否 | AUTO | Grid 默认 AUTO（不同于 List 默认 CENTER） |
| options | ScrollToOptions | 否 | — | 含 animate 参数 |

---

**onDidScroll**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onDidScroll(callback: (offset: number, state: ScrollState) => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 12) |
| 错误码 | N/A |
| 关联 AC | AC-6.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (number, ScrollState) => void | 是 | — | ScrollState: IDLE=0/SCROLL=1/FLING=2 |

---

**onWillScroll**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onWillScroll(callback: (offset: number, state: ScrollState, source: ScrollSource) => number): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 12 继承, Grid 专属 @since 23) |
| 错误码 | N/A |
| 关联 AC | AC-6.3, AC-6.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (number, ScrollState, ScrollSource) => number | 是 | — | 返回值为额外偏移量；返回 0 表示不修改 |

---

**onScrollFrameBegin**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onScrollFrameBegin(callback: (offset: number) => ScrollResult): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-6.5, AC-6.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (number) => ScrollResult | 是 | — | ScrollResult 含 offsetRemain: number |

---

**onScrollStart / onScrollStop**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onScrollStart(callback: () => void): GridAttribute` / `onScrollStop(callback: () => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-6.7, AC-6.8 |

---

**onScrollIndex**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onScrollIndex(callback: (first: number, last: number) => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 7 first only, @since 10 first+last) |
| 错误码 | N/A |
| 关联 AC | AC-6.9, AC-6.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (first: number, last?: number) => void | 是 | — | API 7 仅 first 参数；API 10 first+last |

---

**onReachStart / onReachEnd**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onReachStart(callback: () => void): GridAttribute` / `onReachEnd(callback: () => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-6.11, AC-6.12 |

---

**onWillStartDragging / onWillStopDragging / onDidStopDragging**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onWillStartDragging(callback: () => boolean): GridAttribute` / `onWillStopDragging(callback: () => boolean): GridAttribute` / `onDidStopDragging(callback: () => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 20-21) |
| 错误码 | N/A |
| 关联 AC | AC-7.1–7.4 |

**参数约束**

| 回调 | 版本 | 返回值 | 说明 |
|------|------|--------|------|
| onWillStartDragging | @since 21 | boolean | true=允许拖拽，false=拒绝拖拽 |
| onWillStopDragging | @since 20 | boolean | true=允许停止拖拽 |
| onDidStopDragging | @since 21 | void | 拖拽停止后通知 |

---

**onWillStartFling / onDidStopFling**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onWillStartFling(callback: () => boolean): GridAttribute` / `onDidStopFling(callback: () => void): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 21) |
| 错误码 | N/A |
| 关联 AC | AC-7.5–7.7 |

**参数约束**

| 回调 | 返回值 | 说明 |
|------|--------|------|
| onWillStartFling | boolean | true=允许惯性，false=拒绝惯性 |
| onDidStopFling | void | 惯性停止后通知 |

## 兼容性声明

- **已有 API 行为变更:** scrollBar 默认值从 Off（API 7-9）变为 Auto（API 10+），属于行为变更但与平台版本绑定
- **DEPRECATED API:** onScroll 自 @since 12 标注 DEPRECATED，应迁移到 onDidScroll；onScroll 在 API <12 仍可使用
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 各 API 按 @since 标注最早引入版本；Resource overload 在后续版本引入

- **SDK vs 源码偏差风险:**
  - Grid scrollToIndex 默认 align=AUTO（不同于 List 的 CENTER）— 此差异需在 API 文档中标注
  - onScrollIndex 参数数量因 API 版本不同（@since 7 仅 first, @since 10 first+last）— 回调签名在 SDK 中统一为双参数，@since 7 版本 last 参数未使用
  - onItemDragStart 注册后 GetIsAllowMouse()=false — 此行为影响鼠标滚轮交互，需在文档标注与编辑模式的交互关系

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Grid 继承 ScrollablePattern | 所有滚动基础设施由 ScrollablePattern 提供，Grid 在 OnModifyDone 中初始化滚动手势、滚动条、边缘效果、事件 | AC-1.1–8.2 |
| IsConfiguredScrollable()=false 禁用滚动 | 双模板/自适应模式 OnModifyDone 设 scrollBar(OFF)，Scroller 方法不触发滚动 | AC-1.5, AC-5.14 |
| scrollToIndex 默认 align=AUTO | Grid 与 List 默认对齐不同，Grid 使用 AUTO | AC-5.3 |
| onScroll DEPRECATED | @since 12 标注废弃，应迁移到 onDidScroll | AC-6.2 |
| enableScrollInteraction=false 仅禁用用户交互 | 不影响 Scroller 编程式滚动 | AC-3.2 |
| onItemDragStart 禁用鼠标滚动 | 编辑模式下 GetIsAllowMouse()=false | AC-8.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 滚动事件回调帧耗时 <2ms | Trace 打点 | ScrollablePattern 事件处理 |
| 性能 | scrollToIndex 平滑滚动帧率 ≥55fps | Perf 组网测试 | Jank 检测 |
| 性能 | 惯性滚动减速符合 friction 计算 | 运动学公式验证 | friction 参数推导 |
| 内存 | 滚动条渲染节点开销 <1KB | Dump 机制 | ScrollBar Modifier |
| 可测试性 | Scroller 各方法可独立 UT | Mock ScrollablePattern | scrollable_pattern.cpp |
| 可测试性 | 滚动事件回调参数可验证 | Event 参数断言 | grid_pattern.cpp 事件注册 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | scrollBar Auto 模式下手指触摸显示 | 触摸交互 | 手动测试 | — |
| 平板 | enableScrollWithMouse 控制鼠标滚轮 | @since 26 | 鼠标交互测试 | — |
| 穿戴 | digitalCrownSensitivity 表冠灵敏度 | 仅穿戴设备 @since 18 | 穿戴专项测试 | — |
| 2in1/PC | enableScrollWithMouse 默认行为不同 | 非触屏设备鼠标为默认交互 | 鼠标滚轮测试 | — |
| 鸿蒙慧联 | friction 默认值可能不同 | 平台版本差异 | 各平台默认值采集 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 滚动事件可辅助技术读取滚动位置；scrollBar 提供视觉反馈 | 辅助技术读取滚动偏移 |
| 大字体 | 否 | scrollBarWidth/scrollBarColor 不受大字体影响 | — |
| 深色模式 | 是 | scrollBarColor 默认 '#182431' 在深色模式下需适配 | 滚动条颜色适配 |
| 多窗口/分屏 | 是 | 嵌套滚动配置在分屏下影响父子容器滚动传递 | 分屏嵌套滚动 |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | scrollBar 默认值变更（API 10）；onScroll DEPRECATED（API 12）；Resource overload 逐步引入 | 版本兼容 |
| 生态兼容 | 否 | — | — |

## 行为场景（Gherkin）

```gherkin
Feature: Grid 滚动控制与滚动条
  作为 ArkUI 开发者
  我想要配置滚动条外观、边缘效果和滚动交互
  以便滚动行为和视觉符合产品需求

  Scenario: 滚动条三种状态
    Given Grid 为可滚动模式（IsConfiguredScrollable()=true）
    When 开发者设置 scrollBar(Off)
    Then 滚动条不可见
    When 开发者设置 scrollBar(Auto)
    Then 滚动条交互时可见，静止时淡出
    When 开发者设置 scrollBar(On)
    Then 滚动条常驻显示

  Scenario: 静态网格自动禁用滚动条
    Given Grid 为双模板模式（IsConfiguredScrollable()=false）
    When OnModifyDone 执行
    Then scrollBar 自动设为 OFF
    And 滚动手势不被注册

  Scenario: 边缘效果三种模式
    When 开发者设置 edgeEffect(Spring)
    Then 滚动到边界时弹簧回弹
    When 开发者设置 edgeEffect(Fade)
    Then 滚动到边界时内容渐隐
    When 开发者设置 edgeEffect(None)
    Then 滚动到边界时无效果

  Scenario: 嵌套滚动 PARENT_FIRST
    Given Grid 作为子容器嵌套在父 Scroll 内
    And nestedScroll.forward=PARENT_FIRST
    When 用户向下滚动且子 Grid 未到边界
    Then 滚动事件先传递给父 Scroll
    And 父 Scroll 消耗后剩余量传递给子 Grid

  Scenario: enableScrollInteraction 禁用用户交互
    Given enableScrollInteraction=false
    When 用户通过手势尝试滚动
    Then Grid 不响应手势滚动
    When 开发者通过 Scroller.scrollToIndex(5)
    Then Grid 编程式滚动仍然生效

  Scenario Outline: Scroller 控制器方法
    Given Grid 为可滚动模式且 scroller 已绑定
    When 开发者调用 <method>
    Then <expected_behavior>

    Examples:
      | method | expected_behavior |
      | scrollToIndex(5) | 滚动到第5个子项，align=AUTO |
      | scrollToIndex(5, true, CENTER) | 平滑滚动到第5项居中 |
      | scrollEdge(TOP) | 滚动到顶部 |
      | scrollBy(50, 0) | 水平滚动50vp |
      | currentOffset() | 返回当前偏移{xOffset, yOffset} |
      | isAtEnd() | 返回是否到底的boolean |
      | getItemRect(3) | 返回第3个子项矩形 |
      | getItemIndex(100, 200) | 返回坐标位置子项索引 |

  Scenario: onWillScroll 偏移修改
    Given onWillScroll 注册回调返回 50
    When 滚动计算偏移为 200
    Then 实际滚动偏移 = 200 + 50 = 250

  Scenario: onScrollFrameBegin 剩余偏移
    Given onScrollFrameBegin 返回 ScrollResult{offsetRemain=100}
    And 当前帧消耗偏移=300，总偏移=400
    Then 300 在当前帧消耗
    And 100 作为 offsetRemain 在后续帧继续消耗

  Scenario: onScrollIndex 参数演进
    Given API 版本 = 7
    When onScrollIndex 回调触发
    Then 回调参数仅含 first
    Given API 版本 ≥ 10
    When onScrollIndex 回调触发
    Then 回调参数含 first 和 last

  Scenario: onItemDragStart 禁用鼠标滚动
    Given onItemDragStart 回调已注册（编辑模式）
    When GetIsAllowMouse() 被调用
    Then 返回 false，鼠标滚轮不触发滚动
```

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [ ] 范围边界明确（做什么/不做什么清晰）
- [ ] 无语义模糊表述（"快速""稳定""尽可能"等）
- [ ] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [ ] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "Grid ScrollablePattern OnModifyDone 滚动基础设施初始化 (grid_pattern.cpp)"
  - repo: "openharmony/ace_engine"
    query: "scrollBar/scrollBarColor/scrollBarWidth 滚动条属性设置 (scroll_bar_modifier.cpp)"
  - repo: "openharmony/ace_engine"
    query: "edgeEffect/nestedScroll/enableScrollInteraction/friction 滚动控制 (scrollable_pattern.cpp)"
  - repo: "openharmony/ace_engine"
    query: "Scroller scrollToIndex/scrollEdge/scrollTo/scrollBy/scrollPage/fling 控制器方法 (scrollable_pattern.cpp)"
  - repo: "openharmony/ace_engine"
    query: "onDidScroll/onWillScroll/onScrollFrameBegin/onScrollStart/onScrollStop 滚动事件 (scrollable_pattern.cpp)"
  - repo: "openharmony/ace_engine"
    query: "onWillStartDragging/onWillStopDragging/onDidStopDragging/onWillStartFling/onDidStopFling 拖拽与惯性回调 (scrollable_pattern.cpp)"
  - repo: "openharmony/ace_engine"
    query: "onItemDragStart 禁用鼠标滚动 GetIsAllowMouse (grid_pattern.cpp)"
```

**关键文档：**
- SDK 动态 API: `interface/sdk-js/api/@internal/component/ets/grid.d.ts`
- SDK 静态 API: `interface/sdk-js/api/arkui/component/grid.static.d.ets`
- 源码入口: `frameworks/core/components_ng/pattern/grid/grid_pattern.h/.cpp`
- 滚动基础设施: `frameworks/core/components_ng/pattern/scrollable/scrollable_pattern.h/.cpp`
- 滚动条修饰器: `frameworks/core/components_ng/pattern/scroll_bar/scroll_bar_modifier.h/.cpp`
