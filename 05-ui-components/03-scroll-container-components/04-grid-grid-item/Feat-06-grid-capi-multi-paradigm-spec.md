# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Grid/GridItem C API 与多范式接口 |
| 特性编号 | Func-05-03-04-Feat-06 |
| 所属 Epic | Grid/GridItem 组件规格补录 |
| 优先级 | P1 |
| 目标版本 | API 12–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 存量特性补录（lineage: new-on-legacy），本规格补录已有实现的行为。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Grid C-API 属性枚举 NODE_GRID_* | columnsTemplate/rowsTemplate/gap/cachedCount/syncLoad/alignItems/layoutOptions/itemFillPolicy |
| ADDED | GridItem C-API 属性枚举 NODE_GRID_ITEM_* | rowStart/rowEnd/columnStart/columnEnd/selectable/selected |
| ADDED | GridLayoutOptions C-API 函数族 | Create/Dispose/SetIrregularIndexes/GetIrregularIndexes/RegisterGetIrregularSizeByIndex/RegisterGetRectByIndex |
| ADDED | ArkUI_GridItemSize / ArkUI_GridItemRect / ArkUI_GridItemAlignment / ArkUI_ItemFillPolicy C 类型 | C-API 专用结构体与枚举 |
| ADDED | Grid C-API 滚动公共属性透传 | ScrollableCommonMethod C-API 属性通过 Grid Modifier 设置 |
| ADDED | UIGridEvent 静态事件 API | setOnWillScroll/setOnDidScroll/setOnScrollIndex |
| ADDED | attributeModifier 多范式接口 | AttributeModifier<GridAttribute> \| AttributeModifier<CommonMethod> @since 23 |
| ADDED | GridCustomModifier / GridItemCustomModifier 动态 Modifier 结构体 | 拖拽与选择函数指针 |
| MODIFIED | C-API cachedCount .value[1].i32 show 参数 | @since 26 新增 show 字段，原 .value[0].i32 仅 count @since 12 |

## 输入文档

- 需求基线：已有能力补录（无独立 requirement.md）
- 设计文档：`05-ui-components/03-scroll-container-components/04-grid-grid-item/design.md`
- 源码定位：`frameworks/core/interfaces/native/node/grid_modifier.h/.cpp`, `interfaces/native/native_node.h`
- C-API 声明：`interfaces/native/node/grid_layout_option.h`

## 用户故事

### US-1: C-API 开发者使用 NODE_GRID_* 设置网格布局属性

作为 C-API 开发者，我想要通过 NODE_GRID_COLUMN_TEMPLATE 等 ArkUI_NodeAttribute 枚举设置 Grid 的列模板、间距、缓存等属性，以便在 Native 层构建网格布局。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 NODE_GRID_COLUMN_TEMPLATE(string) THEN Grid 的 columnsTemplate 属性被写入 GridLayoutProperty | 正常 |
| AC-1.2 | WHEN 设置 NODE_GRID_ROW_TEMPLATE(string) THEN Grid 的 rowsTemplate 属性被写入 GridLayoutProperty | 正常 |
| AC-1.3 | WHEN 设置 NODE_GRID_COLUMN_GAP(.value[0].f32 vp) THEN Grid 的 columnsGap 属性以 vp 单位写入 | 正常 |
| AC-1.4 | WHEN 设置 NODE_GRID_ROW_GAP(.value[0].f32 vp) THEN Grid 的 rowsGap 属性以 vp 单位写入 | 正常 |
| AC-1.5 | WHEN 设置 NODE_GRID_CACHED_COUNT(.value[0].i32 count) THEN cachedCount 属性写入，.value[1] 未使用（@since 12） | 正常 |
| AC-1.6 | WHEN 设置 NODE_GRID_CACHED_COUNT(.value[0].i32 count, .value[1].i32 show) THEN cachedCount(count, show) 属性写入（@since 26 新增 show 字段） | 正常 |
| AC-1.7 | WHEN 设置 NODE_GRID_SYNC_LOAD(.value[0].i32) THEN syncLoad 属性写入，0=false, 非0=true | 正常 |
| AC-1.8 | WHEN 设置 NODE_GRID_ALIGN_ITEMS(.value[0].i32 ArkUI_GridItemAlignment) THEN alignItems 属性写入，0=DEFAULT, 1=STRETCH | 正常 |
| AC-1.9 | WHEN 设置 NODE_GRID_LAYOUT_OPTIONS(.object ArkUI_GridLayoutOptions*) THEN GridLayoutOptions 对象指针被传递给 GridModelNG | 正常 |
| AC-1.10 | WHEN 设置 NODE_GRID_COLUMN_TEMPLATE_ITEMFILLPOLICY(.value[0].i32 ArkUI_ItemFillPolicy) THEN ItemFillPolicy 属性写入，-1=NONE, 0=DEFAULT, 1=SM1MD2LG3, 2=SM2MD3LG5 | 正常 |
| AC-1.11 | WHEN C-API 调用 GridLayoutOptions 的 Create/Dispose THEN 对象生命周期正常管理 | 正常 |
| AC-1.12 | WHEN C-API 调用 OH_ArkUI_GridLayoutOptions_SetIrregularIndexes THEN irregularIndexes 写入 GridLayoutOptions | 正常 |
| AC-1.13 | WHEN C-API 调用 OH_ArkUI_GridLayoutOptions_RegisterGetIrregularSizeByIndexCallback THEN 回调函数指针注册到 GridLayoutOptions | 正常 |
| AC-1.14 | WHEN C-API 调用 OH_ArkUI_GridLayoutOptions_RegisterGetRectByIndexCallback THEN 回调函数指针注册到 GridLayoutOptions | 正常 |

### US-2: C-API 开发者使用 NODE_GRID_ITEM_* 设置 GridItem 属性

作为 C-API 开发者，我想要通过 NODE_GRID_ITEM_ROW_START 等枚举设置 GridItem 的跨行/跨列/选择属性，以便在 Native 层构建不规则网格子项。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 NODE_GRID_ITEM_ROW_START(.value[0].i32) THEN GridItem 的 rowStart 属性被写入 | 正常 |
| AC-2.2 | WHEN 设置 NODE_GRID_ITEM_ROW_END(.value[0].i32) THEN GridItem 的 rowEnd 属性被写入 | 正常 |
| AC-2.3 | WHEN 设置 NODE_GRID_ITEM_COLUMN_START(.value[0].i32) THEN GridItem 的 columnStart 属性被写入 | 正常 |
| AC-2.4 | WHEN 设置 NODE_GRID_ITEM_COLUMN_END(.value[0].i32) THEN GridItem 的 columnEnd 属性被写入 | 正常 |
| AC-2.5 | WHEN 设置 NODE_GRID_ITEM_SELECTABLE(.value[0].i32) THEN GridItem 的 selectable 属性写入，0=false, 非0=true | 正常 |
| AC-2.6 | WHEN 设置 NODE_GRID_ITEM_SELECTED(.value[0].i32) THEN GridItem 的 selected 属性写入，0=false, 非0=true | 正常 |

### US-3: C-API 开发者使用 ScrollableCommonMethod 属性控制 Grid 滚动

作为 C-API 开发者，我想要通过 Grid 的 Modifier 设置 scrollBarMode/scrollBarColor/scrollBarWidth/edgeEffect/nestedScroll/friction/enableScrollInteraction 等滚动公共属性。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 NODE_SCROLL_BAR_MODE THEN Grid 的 scrollBarMode 属性被写入 | 正常 |
| AC-3.2 | WHEN 设置 scrollBarColor/scrollBarWidth/edgeEffect/nestedScroll/friction/enableScrollInteraction THEN 通过 ScrollableCommonMethod C-API 透传到 Grid | 正常 |

### US-4: 静态 API 开发者使用 UIGridEvent 注册滚动事件

作为 ArkUI 静态 API 开发者，我想要通过 UIGridEvent（继承 UIScrollableCommonEvent）注册 onWillScroll/onDidScroll/onScrollIndex 事件回调。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 调用 UIGridEvent::setOnWillScroll THEN onWillScroll 回调注册到 GridPattern，滚动前触发 | 正常 |
| AC-4.2 | WHEN 调用 UIGridEvent::setOnDidScroll THEN onDidScroll 回调注册到 GridPattern，滚动后触发 | 正常 |
| AC-4.3 | WHEN 调用 UIGridEvent::setOnScrollIndex THEN onScrollIndex 回调注册到 GridPattern，滚动到新行/列时触发 | 正常 |

### US-5: ArkTS 开发者使用 attributeModifier 动态修改 Grid 属性

作为 ArkTS 开发者，我想要通过 AttributeModifier<GridAttribute> 或 AttributeModifier<CommonMethod> 动态修改 Grid 的属性，以便根据状态变化实时更新 Grid 外观。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 传入 AttributeModifier<GridAttribute> THEN Grid 的 applyAttributeModifier 调用 GridAttribute 专属 Modifier | 正常 |
| AC-5.2 | WHEN 传入 AttributeModifier<CommonMethod> THEN Grid 的 applyAttributeModifier 调用 CommonMethod 通用 Modifier | 正常 |
| AC-5.3 | WHEN AttributeModifier 的 applyNormalAttribute 返回新属性值 THEN Grid 在下一帧重新测量布局 | 正常 |

### US-6: 内部 Modifier 属性仅在 internal 修饰符中可用

作为框架内部开发者，我想要确认 NODE_GRID_EDIT_MODE / NODE_GRID_MULTI_SELECTABLE / NODE_GRID_LAYOUT_DIRECTION 仅存在于 internal modifier 中，无公开 C-API 属性 ID。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN 查询 native_node.h 中 NODE_GRID_EDIT_MODE THEN 该枚举仅存在于 GridCustomModifier（internal），无公开 ArkUI_NodeAttribute ID | 边界 |
| AC-6.2 | WHEN 查询 native_node.h 中 NODE_GRID_MULTI_SELECTABLE THEN 该枚举仅存在于 GridCustomModifier（internal），无公开 ArkUI_NodeAttribute ID | 边界 |
| AC-6.3 | WHEN 查询 NODE_GRID_LAYOUT_DIRECTION THEN 该属性仅在 internal modifier 中定义，无公开属性枚举 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-GRID-06 | UT: NODE_GRID_COLUMN_TEMPLATE string→columnsTemplate | grid_modifier.cpp:SetColumnsTemplate |
| AC-1.2 | R-2 | TASK-GRID-06 | UT: NODE_GRID_ROW_TEMPLATE string→rowsTemplate | grid_modifier.cpp:SetRowsTemplate |
| AC-1.3 | R-3 | TASK-GRID-06 | UT: NODE_GRID_COLUMN_GAP f32→columnsGap(vp) | grid_modifier.cpp:SetColumnsGap |
| AC-1.4 | R-4 | TASK-GRID-06 | UT: NODE_GRID_ROW_GAP f32→rowsGap(vp) | grid_modifier.cpp:SetRowsGap |
| AC-1.5 | R-5 | TASK-GRID-06 | UT: NODE_GRID_CACHED_COUNT i32→cachedCount | grid_modifier.cpp:SetCachedCount |
| AC-1.6 | R-5 | TASK-GRID-06 | UT: NODE_GRID_CACHED_COUNT i32+i32→cachedCount(count,show) | grid_modifier.cpp:SetCachedCount |
| AC-1.7 | R-6 | TASK-GRID-06 | UT: NODE_GRID_SYNC_LOAD i32→syncLoad | grid_modifier.cpp:SetSyncLoad |
| AC-1.8 | R-7 | TASK-GRID-06 | UT: NODE_GRID_ALIGN_ITEMS i32→alignItems | grid_modifier.cpp:SetAlignItems |
| AC-1.9 | R-8 | TASK-GRID-06 | UT: NODE_GRID_LAYOUT_OPTIONS object→GridLayoutOptions | grid_modifier.cpp:SetLayoutOptions |
| AC-1.10 | R-9 | TASK-GRID-06 | UT: NODE_GRID_COLUMN_TEMPLATE_ITEMFILLPOLICY i32→ItemFillPolicy | grid_modifier.cpp:SetItemFillPolicy |
| AC-1.11 | R-10 | TASK-GRID-06 | UT: GridLayoutOptions Create/Dispose 生命周期 | grid_layout_option.h |
| AC-1.12 | R-11 | TASK-GRID-06 | UT: SetIrregularIndexes 写入 | grid_layout_option.h |
| AC-1.13 | R-12 | TASK-GRID-06 | UT: RegisterGetIrregularSizeByIndexCallback 回调注册 | grid_layout_option.h |
| AC-1.14 | R-13 | TASK-GRID-06 | UT: RegisterGetRectByIndexCallback 回调注册 | grid_layout_option.h |
| AC-2.1 | R-14 | TASK-GRID-06 | UT: NODE_GRID_ITEM_ROW_START i32→rowStart | grid_item_modifier.cpp |
| AC-2.2 | R-15 | TASK-GRID-06 | UT: NODE_GRID_ITEM_ROW_END i32→rowEnd | grid_item_modifier.cpp |
| AC-2.3 | R-16 | TASK-GRID-06 | UT: NODE_GRID_ITEM_COLUMN_START i32→columnStart | grid_item_modifier.cpp |
| AC-2.4 | R-17 | TASK-GRID-06 | UT: NODE_GRID_ITEM_COLUMN_END i32→columnEnd | grid_item_modifier.cpp |
| AC-2.5 | R-18 | TASK-GRID-06 | UT: NODE_GRID_ITEM_SELECTABLE i32→selectable | grid_item_modifier.cpp |
| AC-2.6 | R-19 | TASK-GRID-06 | UT: NODE_GRID_ITEM_SELECTED i32→selected | grid_item_modifier.cpp |
| AC-3.1 | R-20 | TASK-GRID-06 | UT: NODE_SCROLL_BAR_MODE→Grid scrollBarMode | scrollable_modifier.cpp |
| AC-3.2 | R-21 | TASK-GRID-06 | UT: ScrollableCommonMethod 属性透传到 Grid | grid_modifier.cpp 继承 |
| AC-4.1 | R-22 | TASK-GRID-06 | UT: UIGridEvent::setOnWillScroll 注册回调 | grid_static_modifier.cpp |
| AC-4.2 | R-23 | TASK-GRID-06 | UT: UIGridEvent::setOnDidScroll 注册回调 | grid_static_modifier.cpp |
| AC-4.3 | R-24 | TASK-GRID-06 | UT: UIGridEvent::setOnScrollIndex 注册回调 | grid_static_modifier.cpp |
| AC-5.1 | R-25 | TASK-GRID-06 | UT: AttributeModifier<GridAttribute> apply | grid_model_ng.cpp |
| AC-5.2 | R-26 | TASK-GRID-06 | UT: AttributeModifier<CommonMethod> apply | grid_model_ng.cpp |
| AC-5.3 | R-27 | TASK-GRID-06 | UT: applyNormalAttribute→重新测量 | grid_pattern.cpp |
| AC-6.1 | R-28 | TASK-GRID-06 | 代码审查: GridCustomModifier internal only | grid_modifier.h |
| AC-6.2 | R-28 | TASK-GRID-06 | 代码审查: GridCustomModifier internal only | grid_modifier.h |
| AC-6.3 | R-28 | TASK-GRID-06 | 代码审查: layoutDirection 仅 internal modifier | grid_modifier.h |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | C-API 设置 NODE_GRID_COLUMN_TEMPLATE | string 值写入 columnsTemplate 属性 | 空字符串视为未设置 | AC-1.1 |
| R-2 | 行为 | C-API 设置 NODE_GRID_ROW_TEMPLATE | string 值写入 rowsTemplate 属性 | 空字符串视为未设置 | AC-1.2 |
| R-3 | 行为 | C-API 设置 NODE_GRID_COLUMN_GAP | .value[0].f32 以 vp 单位写入 columnsGap | 非负浮点数 | AC-1.3 |
| R-4 | 行为 | C-API 设置 NODE_GRID_ROW_GAP | .value[0].f32 以 vp 单位写入 rowsGap | 非负浮点数 | AC-1.4 |
| R-5 | 行为 | C-API 设置 NODE_GRID_CACHED_COUNT | .value[0].i32 为 count；.value[1].i32 为 show（@since 26） | @since 12 仅 count；@since 26 新增 show 字段 | AC-1.5, AC-1.6 |
| R-6 | 行为 | C-API 设置 NODE_GRID_SYNC_LOAD | .value[0].i32: 0=false, 非0=true | 同 ArkTS boolean 映射 | AC-1.7 |
| R-7 | 行为 | C-API 设置 NODE_GRID_ALIGN_ITEMS | .value[0].i32 映射 ArkUI_GridItemAlignment: 0=DEFAULT, 1=STRETCH | 枚举值范围 0–1 | AC-1.8 |
| R-8 | 行为 | C-API 设置 NODE_GRID_LAYOUT_OPTIONS | .object 为 ArkUI_GridLayoutOptions*，传递给 GridModelNG::SetGridLayoutOptions | regularSize 硬编码为 [1,1]，用户指定无效 | AC-1.9 |
| R-9 | 行为 | C-API 设置 NODE_GRID_COLUMN_TEMPLATE_ITEMFILLPOLICY | .value[0].i32 映射 ArkUI_ItemFillPolicy: -1=NONE, 0=DEFAULT, 1=SM1MD2LG3, 2=SM2MD3LG5 | 与 columnsTemplate(string) 互斥 | AC-1.10 |
| R-10 | 行为 | C-API 调用 OH_ArkUI_GridLayoutOptions_Create | 返回新 ArkUI_GridLayoutOptions* 指针 | 需配套 Dispose 释放 | AC-1.11 |
| R-11 | 行为 | C-API 调用 OH_ArkUI_GridLayoutOptions_SetIrregularIndexes | irregularIndexes 数组写入 GridLayoutOptions | 需配套 RegisterGetIrregularSizeByIndexCallback | AC-1.12 |
| R-12 | 行为 | C-API 调用 OH_ArkUI_GridLayoutOptions_RegisterGetIrregularSizeByIndexCallback | 回调函数指针注册，返回 ArkUI_GridItemSize {rowSpan, columnSpan} | rowSpan/columnSpan ≥1 | AC-1.13 |
| R-13 | 行为 | C-API 调用 OH_ArkUI_GridLayoutOptions_RegisterGetRectByIndexCallback | 回调函数指针注册，返回 ArkUI_GridItemRect {rowStart, columnStart, rowSpan, columnSpan} | rowStart/columnStart ≥0; rowSpan/columnSpan ≥1 | AC-1.14 |
| R-14 | 行为 | C-API 设置 NODE_GRID_ITEM_ROW_START | .value[0].i32 写入 GridItem rowStart | ≥0 整数 | AC-2.1 |
| R-15 | 行为 | C-API 设置 NODE_GRID_ITEM_ROW_END | .value[0].i32 写入 GridItem rowEnd | ≥0 整数 | AC-2.2 |
| R-16 | 行为 | C-API 设置 NODE_GRID_ITEM_COLUMN_START | .value[0].i32 写入 GridItem columnStart | ≥0 整数 | AC-2.3 |
| R-17 | 行为 | C-API 设置 NODE_GRID_ITEM_COLUMN_END | .value[0].i32 写入 GridItem columnEnd | ≥0 整数 | AC-2.4 |
| R-18 | 行为 | C-API 设置 NODE_GRID_ITEM_SELECTABLE | .value[0].i32: 0=false, 非0=true | 同 ArkTS boolean 映射 | AC-2.5 |
| R-19 | 行为 | C-API 设置 NODE_GRID_ITEM_SELECTED | .value[0].i32: 0=false, 非0=true | 同 ArkTS boolean 映射 | AC-2.6 |
| R-20 | 行为 | C-API 设置 NODE_SCROLL_BAR_MODE | 通过 ScrollableCommonMethod Modifier 透传到 Grid | Grid 继承 ScrollableCommonMethod | AC-3.1 |
| R-21 | 行为 | C-API 设置 scrollBarColor/scrollBarWidth/edgeEffect/nestedScroll/friction/enableScrollInteraction | 通过 ScrollableCommonMethod Modifier 函数族透传到 Grid | 所有滚动公共属性均在 Grid 上可用 | AC-3.2 |
| R-22 | 行为 | UIGridEvent::setOnWillScroll 注册回调 | 回调在滚动动作发生前触发 | 继承 UIScrollableCommonEvent | AC-4.1 |
| R-23 | 行为 | UIGridEvent::setOnDidScroll 注册回调 | 回调在滚动动作发生后触发 | 继承 UIScrollableCommonEvent | AC-4.2 |
| R-24 | 行为 | UIGridEvent::setOnScrollIndex 注册回调 | 回调在滚动到新行/列索引时触发 | 仅在 Grid/WaterFlow 等网格组件可用 | AC-4.3 |
| R-25 | 行为 | AttributeModifier<GridAttribute> apply | GridAttribute 专属 Modifier 被应用 | @since 23 | AC-5.1 |
| R-26 | 行为 | AttributeModifier<CommonMethod> apply | CommonMethod 通用 Modifier 被应用 | @since 23 | AC-5.2 |
| R-27 | 行为 | applyNormalAttribute 返回新属性值 | 触发 Grid dirty flag，下一帧重新测量布局 | 属性差异检测机制 | AC-5.3 |
| R-28 | 边界 | NODE_GRID_EDIT_MODE/MULTI_SELECTABLE/LAYOUT_DIRECTION | 仅存在于 GridCustomModifier（internal），无公开 ArkUI_NodeAttribute ID | 开发者不可通过公共 C-API 设置 | AC-6.1, AC-6.2, AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | Grid C-API 属性枚举 | UT: grid_modifier.cpp 各 Set 方法 | string/i32/f32/object 类型正确映射 |
| VM-2 | GridItem C-API 属性枚举 | UT: grid_item_modifier.cpp 各 Set 方法 | rowStart/rowEnd/columnStart/columnEnd/selectable/selected |
| VM-3 | GridLayoutOptions C-API 函数族 | UT: grid_layout_option.h Create/Dispose/Set/Register | 对象生命周期、回调注册正确性 |
| VM-4 | ArkUI_GridItemAlignment/ItemFillPolicy 枚举映射 | UT: 枚举值→ArkTS 常量对照 | DEFAULT=0/STRETCH=1; NONE=-1/DEFAULT=0/SM1MD2LG3=1/SM2MD3LG5=2 |
| VM-5 | C-API cachedCount show 字段 | UT: .value[0] count, .value[1] show | @since 12 仅 count, @since 26 新增 show |
| VM-6 | C-API regularSize 硬编码偏差 | UT: grid_model_ng.cpp:958-959 | C-API 调用者 regularSize 设置被忽略，始终 [1,1] |
| VM-7 | C-API 缺少 onGetStartIndexByOffset/onGetStartIndexByIndex | 代码审查: grid_layout_option.h 无此函数 | @systemapi 回调未在 C-API 公开 |
| VM-8 | ScrollableCommonMethod C-API 透传 | UT: grid_modifier.cpp 继承链 | scrollBarMode/Color/Width/edgeEffect/nestedScroll/friction |
| VM-9 | UIGridEvent 静态事件 | UT: grid_static_modifier.cpp 回调注册 | onWillScroll/onDidScroll/onScrollIndex |
| VM-10 | attributeModifier 多范式 | UT: GridModelNG::SetAttributeModifier | GridAttribute/CommonMethod 双分支 |
| VM-11 | GridCustomModifier/GridItemCustomModifier 内部结构 | 代码审查: grid_modifier.h | 拖拽/选择函数指针仅在 internal |
| VM-12 | DynamicModuleHelper 加载模式 | UT: libarkui_grid.z.so 动态加载 | C-API 通过 DynamicModuleHelper 调用 Grid Modifier |

## API 变更分析

### 新增 API

> 本规格为存量补录，以下 API 已在 SDK 中存在。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| NODE_GRID_COLUMN_TEMPLATE | Public (C-API) | string | — | N/A | 设置列模板 | AC-1.1 |
| NODE_GRID_ROW_TEMPLATE | Public (C-API) | string | — | N/A | 设置行模板 | AC-1.2 |
| NODE_GRID_COLUMN_GAP | Public (C-API) | .value[0].f32 vp | — | N/A | 设置列间距 | AC-1.3 |
| NODE_GRID_ROW_GAP | Public (C-API) | .value[0].f32 vp | — | N/A | 设置行间距 | AC-1.4 |
| NODE_GRID_CACHED_COUNT | Public (C-API) | .value[0].i32 count | — | N/A | 设置缓存数量 (@since 12) | AC-1.5 |
| NODE_GRID_CACHED_COUNT | Public (C-API) | .value[0].i32 count, .value[1].i32 show | — | N/A | 设置缓存数量+可见标志 (@since 26) | AC-1.6 |
| NODE_GRID_SYNC_LOAD | Public (C-API) | .value[0].i32 | — | N/A | 设置同步加载 | AC-1.7 |
| NODE_GRID_ALIGN_ITEMS | Public (C-API) | .value[0].i32 ArkUI_GridItemAlignment | — | N/A | 设置对齐方式 | AC-1.8 |
| NODE_GRID_LAYOUT_OPTIONS | Public (C-API) | .object ArkUI_GridLayoutOptions* | — | N/A | 设置布局选项 | AC-1.9 |
| NODE_GRID_COLUMN_TEMPLATE_ITEMFILLPOLICY | Public (C-API) | .value[0].i32 ArkUI_ItemFillPolicy | — | N/A | 设置响应式列填充 | AC-1.10 |
| OH_ArkUI_GridLayoutOptions_Create() | Public (C-API) | 无 | ArkUI_GridLayoutOptions* | N/A | 创建布局选项对象 | AC-1.11 |
| OH_ArkUI_GridLayoutOptions_Dispose(options) | Public (C-API) | ArkUI_GridLayoutOptions* | void | N/A | 释放布局选项对象 | AC-1.11 |
| OH_ArkUI_GridLayoutOptions_SetIrregularIndexes(options, indexes, count) | Public (C-API) | options*, int32_t*, int32_t | void | N/A | 设置不规则项索引 | AC-1.12 |
| OH_ArkUI_GridLayoutOptions_GetIrregularIndexes(options, count) | Public (C-API) | options*, int32_t* | int32_t* | N/A | 获取不规则项索引 | AC-1.12 |
| OH_ArkUI_GridLayoutOptions_RegisterGetIrregularSizeByIndexCallback(options, callback) | Public (C-API) | options*, callback fn | void | N/A | 注册不规则尺寸回调 | AC-1.13 |
| OH_ArkUI_GridLayoutOptions_RegisterGetRectByIndexCallback(options, callback) | Public (C-API) | options*, callback fn | void | N/A | 注册自定义位置回调 | AC-1.14 |
| NODE_GRID_ITEM_ROW_START | Public (C-API) | .value[0].i32 | — | N/A | 设置 GridItem 行起始 | AC-2.1 |
| NODE_GRID_ITEM_ROW_END | Public (C-API) | .value[0].i32 | — | N/A | 设置 GridItem 行结束 | AC-2.2 |
| NODE_GRID_ITEM_COLUMN_START | Public (C-API) | .value[0].i32 | — | N/A | 设置 GridItem 列起始 | AC-2.3 |
| NODE_GRID_ITEM_COLUMN_END | Public (C-API) | .value[0].i32 | — | N/A | 设置 GridItem 列结束 | AC-2.4 |
| NODE_GRID_ITEM_SELECTABLE | Public (C-API) | .value[0].i32 | — | N/A | 设置 GridItem 可选择 | AC-2.5 |
| NODE_GRID_ITEM_SELECTED | Public (C-API) | .value[0].i32 | — | N/A | 设置 GridItem 已选中 | AC-2.6 |
| UIGridEvent::setOnWillScroll | Public (静态 API) | callback | void | N/A | 注册滚动前事件 | AC-4.1 |
| UIGridEvent::setOnDidScroll | Public (静态 API) | callback | void | N/A | 注册滚动后事件 | AC-4.2 |
| UIGridEvent::setOnScrollIndex | Public (静态 API) | callback | void | N/A | 注册滚动索引事件 | AC-4.3 |
| GridAttribute.attributeModifier | Public | AttributeModifier<GridAttribute> \| AttributeModifier<CommonMethod> | GridAttribute | N/A | 动态属性修改 (@since 23) | AC-5.1, AC-5.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 说明 | 关联 AC |
|----------|----------|------|---------|
| NODE_GRID_CACHED_COUNT | 扩展 | @since 26 新增 .value[1].i32 show 字段，原 @since 12 仅 .value[0].i32 count | AC-1.6 |

## 接口规格

### Grid C-API 属性枚举

**NODE_GRID_COLUMN_TEMPLATE**

| 属性 | 值 |
|------|-----|
| 枚举值 | NODE_GRID_COLUMN_TEMPLATE |
| 数据类型 | string (ArkUI_NodeAttributeType_STRING) |
| 开放范围 | Public (@since 12) |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value="1fr 1fr 1fr" | columnsTemplate 写入 GridLayoutProperty | AC-1.1 |
| 2 | value="" (空) | columnsTemplate 视为未设置 | AC-1.1 |

---

**NODE_GRID_ROW_TEMPLATE**

| 属性 | 值 |
|------|-----|
| 枚举值 | NODE_GRID_ROW_TEMPLATE |
| 数据类型 | string (ArkUI_NodeAttributeType_STRING) |
| 开放范围 | Public (@since 12) |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

---

**NODE_GRID_COLUMN_GAP / NODE_GRID_ROW_GAP**

| 属性 | 值 |
|------|-----|
| 枚举值 | NODE_GRID_COLUMN_GAP / NODE_GRID_ROW_GAP |
| 数据类型 | .value[0].f32 (vp 单位) |
| 开放范围 | Public (@since 12) |
| 错误码 | N/A |
| 关联 AC | AC-1.3, AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| .value[0].f32 | float32 (vp) | 是 | 0.0 | 非负；超出可用空间时 clamp 到 0 |

---

**NODE_GRID_CACHED_COUNT**

| 属性 | 值 |
|------|-----|
| 枚举值 | NODE_GRID_CACHED_COUNT |
| 数据类型 | .value[0].i32 count; .value[1].i32 show (@since 26) |
| 开放范围 | Public (count @since 12; show @since 26) |
| 错误码 | N/A |
| 关联 AC | AC-1.5, AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| .value[0].i32 | int32 (count) | 是 | 自动(最大16) | ≥0；内部乘以 crossCount |
| .value[1].i32 | int32 (show) | 否 | 0 (false) | @since 26; 0=false, 非0=true |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 仅设置 .value[0] (API <26) | cachedCount(count) 写入 | AC-1.5 |
| 2 | 设置 .value[0]+.value[1] (API ≥26) | cachedCount(count, show) 写入 | AC-1.6 |

---

**NODE_GRID_SYNC_LOAD**

| 属性 | 值 |
|------|-----|
| 枚举值 | NODE_GRID_SYNC_LOAD |
| 数据类型 | .value[0].i32 |
| 开放范围 | Public (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-1.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| .value[0].i32 | int32 | 是 | 1 (true) | 0=false, 非0=true |

---

**NODE_GRID_ALIGN_ITEMS**

| 属性 | 值 |
|------|-----|
| 枚举值 | NODE_GRID_ALIGN_ITEMS |
| 数据类型 | .value[0].i32 (ArkUI_GridItemAlignment) |
| 开放范围 | Public (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-1.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| .value[0].i32 | ArkUI_GridItemAlignment | 是 | 0 (DEFAULT) | 0=DEFAULT(居中), 1=STRETCH(填满) |

---

**NODE_GRID_LAYOUT_OPTIONS**

| 属性 | 值 |
|------|-----|
| 枚举值 | NODE_GRID_LAYOUT_OPTIONS |
| 数据类型 | .object (ArkUI_GridLayoutOptions*) |
| 开放范围 | Public (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-1.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| .object | ArkUI_GridLayoutOptions* | 是 | null | 需先调用 OH_ArkUI_GridLayoutOptions_Create；C-API regularSize 硬编码为 [1,1] |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | .object=null | 无 layoutOptions 设置 | AC-1.9 |
| 2 | .object=有效指针 | GridLayoutOptions 传递给 GridModelNG::SetGridLayoutOptions | AC-1.9 |
| 3 | .object 含 irregularIndexes | 实例化 GridIrregularLayoutAlgorithm（同 ArkTS 行为） | AC-1.9 |

---

**NODE_GRID_COLUMN_TEMPLATE_ITEMFILLPOLICY**

| 属性 | 值 |
|------|-----|
| 枚举值 | NODE_GRID_COLUMN_TEMPLATE_ITEMFILLPOLICY |
| 数据类型 | .value[0].i32 (ArkUI_ItemFillPolicy) |
| 开放范围 | Public (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-1.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| .value[0].i32 | ArkUI_ItemFillPolicy | 是 | 0 (DEFAULT) | -1=NONE, 0=DEFAULT, 1=SM1MD2LG3, 2=SM2MD3LG5 |

---

### GridLayoutOptions C-API 函数族

**OH_ArkUI_GridLayoutOptions_Create / Dispose**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_GridLayoutOptions* OH_ArkUI_GridLayoutOptions_Create()` |
| 函数签名 | `void OH_ArkUI_GridLayoutOptions_Dispose(ArkUI_GridLayoutOptions* options)` |
| 开放范围 | Public (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-1.11 |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Create() | 返回新 ArkUI_GridLayoutOptions* 指针，regularSize 初始化为 {1,1} | AC-1.11 |
| 2 | Dispose(options) | 释放 options 指针内存 | AC-1.11 |
| 3 | Dispose(null) | 安全返回（空指针保护） | AC-1.11 |

---

**OH_ArkUI_GridLayoutOptions_SetIrregularIndexes / GetIrregularIndexes**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void OH_ArkUI_GridLayoutOptions_SetIrregularIndexes(ArkUI_GridLayoutOptions* options, int32_t* indexes, int32_t count)` |
| 函数签名 | `int32_t* OH_ArkUI_GridLayoutOptions_GetIrregularIndexes(ArkUI_GridLayoutOptions* options, int32_t* count)` |
| 开放范围 | Public (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-1.12 |

---

**OH_ArkUI_GridLayoutOptions_RegisterGetIrregularSizeByIndexCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void OH_ArkUI_GridLayoutOptions_RegisterGetIrregularSizeByIndexCallback(ArkUI_GridLayoutOptions* options, ArkUI_GridItemSize (*)(int32_t index))` |
| 开放范围 | Public (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-1.13 |

**回调返回值约束**

| 字段 | 类型 | 约束 |
|------|------|------|
| rowSpan | int32 | ≥1 |
| columnSpan | int32 | ≥1 |

---

**OH_ArkUI_GridLayoutOptions_RegisterGetRectByIndexCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void OH_ArkUI_GridLayoutOptions_RegisterGetRectByIndexCallback(ArkUI_GridLayoutOptions* options, ArkUI_GridItemRect (*)(int32_t index))` |
| 开放范围 | Public (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-1.14 |

**回调返回值约束**

| 字段 | 类型 | 约束 |
|------|------|------|
| rowStart | int32 | ≥0 |
| columnStart | int32 | ≥0 |
| rowSpan | int32 | ≥1 |
| columnSpan | int32 | ≥1 |

---

### C 类型定义

**ArkUI_GridItemSize**

| 属性 | 值 |
|------|-----|
| 类型 | struct |
| 开放范围 | Public (@since 22) |

| 字段 | 类型 | 说明 |
|------|------|------|
| rowSpan | int32 | 行跨度（≥1） |
| columnSpan | int32 | 列跨度（≥1） |

---

**ArkUI_GridItemRect**

| 属性 | 值 |
|------|-----|
| 类型 | struct |
| 开放范围 | Public (@since 22) |

| 字段 | 类型 | 说明 |
|------|------|------|
| rowStart | int32 | 行起始位置（≥0） |
| columnStart | int32 | 列起始位置（≥0） |
| rowSpan | int32 | 行跨度（≥1） |
| columnSpan | int32 | 列跨度（≥1） |

---

**ArkUI_GridItemAlignment**

| 属性 | 值 |
|------|-----|
| 类型 | enum |
| 开放范围 | Public (@since 22) |

| 枚举值 | 数值 | 说明 |
|--------|------|------|
| ARKUI_GRID_ITEM_ALIGNMENT_DEFAULT | 0 | 居中对齐 |
| ARKUI_GRID_ITEM_ALIGNMENT_STRETCH | 1 | 填满格子 |

---

**ArkUI_ItemFillPolicy**

| 属性 | 值 |
|------|-----|
| 类型 | enum |
| 开放范围 | Public (@since 22) |

| 枚举值 | 数值 | 说明 |
|--------|------|------|
| ARKUI_ITEM_FILL_POLICY_NONE | -1 | 无响应式填充 |
| ARKUI_ITEM_FILL_POLICY_DEFAULT | 0 | 默认填充（BREAKPOINT_DEFAULT） |
| ARKUI_ITEM_FILL_POLICY_SM1MD2LG3 | 1 | SM=1列, MD=2列, LG=3列 |
| ARKUI_ITEM_FILL_POLICY_SM2MD3LG5 | 2 | SM=2列, MD=3列, LG=5列 |

---

### GridItem C-API 属性枚举

**NODE_GRID_ITEM_ROW_START / NODE_GRID_ITEM_ROW_END / NODE_GRID_ITEM_COLUMN_START / NODE_GRID_ITEM_COLUMN_END**

| 属性 | 值 |
|------|-----|
| 枚举值 | NODE_GRID_ITEM_ROW_START / ROW_END / COLUMN_START / COLUMN_END |
| 数据类型 | .value[0].i32 |
| 开放范围 | Public (@since 12) |
| 错误码 | N/A |
| 关联 AC | AC-2.1–AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| .value[0].i32 | int32 | 是 | -1 (未设置) | ≥0 整数；-1 表示不设置跨行/跨列 |

---

**NODE_GRID_ITEM_SELECTABLE / NODE_GRID_ITEM_SELECTED**

| 属性 | 值 |
|------|-----|
| 枚举值 | NODE_GRID_ITEM_SELECTABLE / SELECTED |
| 数据类型 | .value[0].i32 |
| 开放范围 | Public (@since 12) |
| 错误码 | N/A |
| 关联 AC | AC-2.5, AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| .value[0].i32 | int32 | 是 | 0 (false) | 0=false, 非0=true |

---

### UIGridEvent 静态事件 API

| 属性 | 值 |
|------|-----|
| 类名 | UIGridEvent (继承 UIScrollableCommonEvent) |
| 开放范围 | Public (implementation/ 层) |
| 错误码 | N/A |
| 关联 AC | AC-4.1–AC-4.3 |

| 方法 | 参数 | 说明 |
|------|------|------|
| setOnWillScroll | callback(ScrollInfo) | 滚动前回调 |
| setOnDidScroll | callback(ScrollInfo) | 滚动后回调 |
| setOnScrollIndex | callback(firstIndex: number) | 滚动到新索引回调 |

---

### attributeModifier 接口

| 属性 | 值 |
|------|-----|
| 函数签名 | `attributeModifier(modifier: AttributeModifier<GridAttribute> \| AttributeModifier<CommonMethod>): GridAttribute` |
| 开放范围 | Public (@since 23) |
| 错误码 | N/A |
| 关联 AC | AC-5.1, AC-5.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| modifier | AttributeModifier<GridAttribute> \| AttributeModifier<CommonMethod> | 是 | — | GridAttribute Modifier 可修改 Grid 专属属性；CommonMethod Modifier 仅可修改公共属性 |

## 兼容性声明

- **已有 API 行为变更:** 否。NODE_GRID_CACHED_COUNT 新增 .value[1].i32 show 字段(@since 26)为扩展，不影响 @since 12 仅使用 .value[0] 的行为。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12 (C-API)
- **API 版本号策略:** @since 标注按各 API 最早引入版本

- **SDK vs C-API 偏差:**
  - C-API regularSize 硬编码为 [1,1]（grid_model_ng.cpp:958-959），ArkTS 允许用户指定 regularSize — C-API 调用者设置的 regularSize 无效
  - C-API 缺少 onGetStartIndexByOffset/onGetStartIndexByIndex 回调（@systemapi），ArkTS GridLayoutOptions 有此功能 — C-API 未覆盖
  - NODE_GRID_EDIT_MODE / NODE_GRID_MULTI_SELECTABLE / NODE_GRID_LAYOUT_DIRECTION 仅存在于 internal modifier，无公开 C-API 属性 ID — 开发者不可通过公共 C-API 设置编辑模式/多选/布局方向

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| DynamicModuleHelper 加载模式 | C-API 通过 libarkui_grid.z.so 动态加载 Grid Modifier 函数 | VM-12 |
| C-API regularSize 硬编码 | grid_model_ng.cpp:958-959 hardcodes regularSize=[1,1] | AC-1.9, VM-6 |
| C-API 缺少 @systemapi 回调 | onGetStartIndexByOffset/onGetStartIndexByIndex 未在 C-API 公开 | VM-7 |
| 两级 Modifier 架构 | static (implementation/) 和 dynamic (node/) 两个 Modifier 层级 | VM-11 |
| GridCustomModifier 结构体 | 含拖拽函数指针（onDragStart/onDragEnter/onDragLeave/onDragDrop/onDragEnd），仅 internal | AC-6.1, AC-6.2 |
| GridItemCustomModifier 结构体 | 含拖拽管理器+选择查询函数指针，仅 internal | AC-6.1 |
| UIGridEvent 继承链 | UIGridEvent extends UIScrollableCommonEvent，共享滚动事件注册机制 | AC-4.1–AC-4.3 |
| ScrollableCommonMethod C-API 透传 | Grid C-API 继承 ScrollableCommonMethod Modifier，滚动属性无需独立枚举 | AC-3.1, AC-3.2 |
| attributeModifier 双分支 | GridAttribute 和 CommonMethod 两种 Modifier 类型，GridAttribute 分支可修改 Grid 专属属性 | AC-5.1, AC-5.2 |

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | C-API 属性设置单次调用 <0.1ms | Perf 测试 | grid_modifier.cpp Set 方法 |
| 性能 | GridLayoutOptions Create/Dispose <0.01ms | Perf 测试 | grid_layout_option.h |
| 内存 | ArkUI_GridLayoutOptions 对象占用 <256 bytes | 内存分析 | grid_layout_option.h struct |
| 可测试性 | 每个 NODE_GRID_* 属性可独立 UT | Mock GridLayoutProperty | grid_modifier.cpp |
| 可测试性 | GridLayoutOptions 函数族可独立 UT | Mock ArkUI_GridLayoutOptions | grid_layout_option.h |
| 安全性 | GridLayoutOptions Dispose 防止 double-free | 空指针保护 | OH_ArkUI_GridLayoutOptions_Dispose |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | ItemFillPolicy SM1MD2LG3 断点阈值不同 | SM/MD/LG 断点宽度与 ArkTS 一致 | 断点配置测试 | — |
| 折叠屏 | C-API ItemFillPolicy 响应式列数随折叠态变化 | 与 ArkTS ItemFillPolicy 行为一致 | 折叠适配测试 | — |
| 穿戴 | digitalCrownSensitivity 通过 ScrollableCommonMethod C-API 设置 | API 18+ | 穿戴专项测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | GridItem C-API 设置的 rowStart/columnStart 等信息传递给语义节点 | 辅助技术读取网格位置 |
| 大字体 | 是 | STRETCH 模式下大字体导致行高增加，C-API 与 ArkTS 行为一致 | 大字体适配 |
| 深色模式 | 否 | Grid C-API 无颜色属性 | — |
| 多窗口/分屏 | 是 | ItemFillPolicy C-API 响应式列数在分屏时自动调整 | 分屏重布局 |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | NODE_GRID_CACHED_COUNT .value[1] show @since 26 新增；低版本仅 count | 版本兼容 |
| 生态兼容 | 否 | — | — |

## 行为场景（Gherkin）

```gherkin
Feature: Grid/GridItem C API 属性设置
  作为 C-API 开发者
  我想要通过 NODE_GRID_* 枚举设置 Grid 属性
  以便在 Native 层构建网格布局

  Scenario: 设置列模板字符串
    Given 一个 Grid ArkUI_NodeHandle
    When 调用 ArkUI_NodeAttribute 设置 NODE_GRID_COLUMN_TEMPLATE value="1fr 1fr 1fr"
    Then Grid 的 columnsTemplate 属性被写入 "1fr 1fr 1fr"
    And Grid 实例化对应的布局算法

  Scenario: 设置间距
    Given 一个 Grid ArkUI_NodeHandle
    When 调用 ArkUI_NodeAttribute 设置 NODE_GRID_COLUMN_GAP .value[0].f32=10.0
    And 调用 ArkUI_NodeAttribute 设置 NODE_GRID_ROW_GAP .value[0].f32=8.0
    Then columnsGap=10.0vp, rowsGap=8.0vp 写入 GridLayoutProperty

  Scenario: 设置缓存数量
    Given 一个 Grid ArkUI_NodeHandle
    When 调用 ArkUI_NodeAttribute 设置 NODE_GRID_CACHED_COUNT .value[0].i32=5
    Then cachedCount=5 写入
    And .value[1] 未使用 (API <26)

  Scenario: 设置缓存数量+可见标志
    Given API 版本 ≥26
    And 一个 Grid ArkUI_NodeHandle
    When 调用 ArkUI_NodeAttribute 设置 NODE_GRID_CACHED_COUNT .value[0].i32=5 .value[1].i32=1
    Then cachedCount(5, true) 写入

  Scenario: 设置布局选项
    Given OH_ArkUI_GridLayoutOptions_Create() 返回有效指针 options
    And options 设置 irregularIndexes=[2,5]
    And options 注册 GetIrregularSizeByIndex callback
    When 调用 ArkUI_NodeAttribute 设置 NODE_GRID_LAYOUT_OPTIONS .object=options
    Then GridLayoutOptions 传递给 GridModelNG
    And 实例化 GridIrregularLayoutAlgorithm

  Scenario: C-API regularSize 硬编码偏差
    Given OH_ArkUI_GridLayoutOptions_Create() 返回有效指针 options
    When 任何尝试设置 regularSize
    Then grid_model_ng.cpp:958-959 硬编码 regularSize=[1,1]
    And 用户设置的 regularSize 值被忽略

  Scenario: internal modifier 属性不可公开访问
    Given 查询 native_node.h 中 NODE_GRID_EDIT_MODE
    Then 该属性仅存在于 GridCustomModifier 结构体
    And 无公开 ArkUI_NodeAttribute 枚举 ID
    And 开发者不可通过公共 C-API 设置编辑模式

Feature: GridLayoutOptions C-API 函数族
  作为 C-API 开发者
  我想要创建和管理 GridLayoutOptions 对象
  以便配置不规则网格

  Scenario: 创建和释放布局选项对象
    When 调用 OH_ArkUI_GridLayoutOptions_Create()
    Then 返回有效 ArkUI_GridLayoutOptions* 指针
    And regularSize 初始化为 {rowSpan=1, columnSpan=1}

    When 调用 OH_ArkUI_GridLayoutOptions_Dispose(options)
    Then options 内存被释放

    When 调用 OH_ArkUI_GridLayoutOptions_Dispose(null)
    Then 安全返回（空指针保护）

  Scenario: 注册不规则尺寸回调
    Given options = OH_ArkUI_GridLayoutOptions_Create()
    When 调用 OH_ArkUI_GridLayoutOptions_RegisterGetIrregularSizeByIndexCallback(options, callback)
    Then callback 函数指针注册到 options
    And callback 返回 ArkUI_GridItemSize {rowSpan, columnSpan}

  Scenario: 注册自定义位置回调
    Given options = OH_ArkUI_GridLayoutOptions_Create()
    When 调用 OH_ArkUI_GridLayoutOptions_RegisterGetRectByIndexCallback(options, callback)
    Then callback 函数指针注册到 options
    And callback 返回 ArkUI_GridItemRect {rowStart, columnStart, rowSpan, columnSpan}

Feature: UIGridEvent 静态事件
  作为 ArkUI 静态 API 开发者
  我想要通过 UIGridEvent 注册滚动事件
  以便监听网格滚动行为

  Scenario: 注册 onWillScroll 回调
    Given 一个 Grid 节点
    When 调用 UIGridEvent::setOnWillScroll(callback)
    Then callback 在滚动动作发生前触发
    And callback 参数为 ScrollInfo

  Scenario: 注册 onScrollIndex 回调
    Given 一个 Grid 节点
    When 调用 UIGridEvent::setOnScrollIndex(callback)
    Then callback 在滚动到新行/列索引时触发
    And callback 参数为 firstIndex: number

Feature: attributeModifier 多范式接口
  作为 ArkTS 开发者
  我想要通过 AttributeModifier 动态修改 Grid 属性

  Scenario: 使用 GridAttribute Modifier
    Given 一个 Grid 组件
    When 传入 AttributeModifier<GridAttribute>
    Then Grid 的 applyAttributeModifier 调用 GridAttribute 专属 Modifier
    And 可修改 columnsTemplate/cachedCount/alignItems 等 Grid 专属属性

  Scenario: 使用 CommonMethod Modifier
    Given 一个 Grid 组件
    When 传入 AttributeModifier<CommonMethod>
    Then Grid 的 applyAttributeModifier 调用 CommonMethod 通用 Modifier
    And 仅可修改 width/height/visibility 等公共属性
```

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [ ] 范围边界明确（做什么/不做什么清晰）
- [ ] 无语义模糊表述（"快速""稳定""尽可能"等）
- [ ] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [ ] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）
- [ ] C-API 与 ArkTS 行为偏差已标注（regularSize 硬编码、@systemapi 回调缺失、internal modifier）
- [ ] VM 映射覆盖所有规则和关键偏差点

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "Grid C-API DynamicModuleHelper 加载模式 (libarkui_grid.z.so)"
  - repo: "openharmony/ace_engine"
    query: "Grid Modifier C-API 属性设置 (grid_modifier.cpp NODE_GRID_*)"
  - repo: "openharmony/ace_engine"
    query: "GridItem Modifier C-API 属性设置 (grid_item_modifier.cpp NODE_GRID_ITEM_*)"
  - repo: "openharmony/ace_engine"
    query: "GridLayoutOptions C-API 函数族 (grid_layout_option.h Create/Dispose/Set/Register)"
  - repo: "openharmony/ace_engine"
    query: "C-API regularSize 硬编码偏差 (grid_model_ng.cpp:958-959)"
  - repo: "openharmony/ace_engine"
    query: "UIGridEvent 静态事件注册 (grid_static_modifier.cpp setOnWillScroll/setOnDidScroll/setOnScrollIndex)"
  - repo: "openharmony/ace_engine"
    query: "GridCustomModifier/GridItemCustomModifier internal 结构体 (grid_modifier.h)"
  - repo: "openharmony/ace_engine"
    query: "attributeModifier GridAttribute/CommonMethod 多范式 (grid_model_ng.cpp)"
```

**关键文档：**
- C-API 声明: `interfaces/native/native_node.h` (NODE_GRID_COLUMN_TEMPLATE 等)
- C-API Modifier: `frameworks/core/interfaces/native/node/grid_modifier.h/.cpp`, `grid_item_modifier.h/.cpp`
- GridLayoutOptions: `interfaces/native/node/grid_layout_option.h`
- 静态事件: `frameworks/core/components_ng/pattern/grid/implementation/grid_static_modifier.cpp`
- ArkTS attributeModifier: `interface/sdk-js/api/@internal/component/ets/grid.d.ts`, `grid.static.d.ets`
- 源码入口: `frameworks/core/components_ng/pattern/grid/`
