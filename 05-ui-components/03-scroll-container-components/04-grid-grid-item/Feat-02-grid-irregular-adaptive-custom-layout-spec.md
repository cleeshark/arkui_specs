# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Grid 不规则、自适应与自定义布局 |
| 特性编号 | Func-05-03-04-Feat-02 |
| 所属 Epic | Grid/GridItem 组件规格补录 |
| 优先级 | P0 |
| 目标版本 | API 8–23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 存量特性补录（lineage: new-on-legacy），本规格补录已有实现的行为。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | GridScrollWithOptionsLayoutAlgorithm 单行不规则布局 | GridLayoutOptions 配置下，仅 cross-axis 跨列的不规则项；使用 GetCrossStartAndSpan 计算位置 |
| ADDED | GridIrregularLayoutAlgorithm 多行不规则布局 | 项跨多行（main-axis）时触发；使用 gridMatrix_ 二维矩阵 + lineHeightMap_ + GridIrregularFiller 填充 |
| ADDED | irregular_ 标志判定逻辑 | 仅当项跨多行（main-axis span>1）时 irregular_=true；仅跨列不触发 |
| ADDED | GridAdaptiveLayoutAlgorithm 自适应布局 | 无模板时实例化；使用 cellLength/maxCount/minCount 计算行列数；不可滚动 |
| ADDED | GridCustomLayoutAlgorithm 自定义布局 | userDefined_=true 时实例化；需同时提供 onGetRectByIndex + onGetStartIndexByIndex + onGetStartIndexByOffset |
| ADDED | GridLayoutOptions 回调体系 | onGetIrregularSizeByIndex(@since 10)、onGetRectByIndex(@since 11)、onGetStartIndexByOffset/onGetStartIndexByIndex(@systemapi @since 23) |
| ADDED | layoutDirection 对自适应模式轴向选择 | GridDirection.Row→水平, Column→垂直；仅在自适应模式生效 |
| ADDED | C-API GridLayoutOptions 支持 | NODE_GRID_LAYOUT_OPTIONS(@since 22)；hardcodes regularSize=[1,1]；缺少 @systemapi 回调 |

## 输入文档

- 需求基线：已有能力补录（无独立 requirement.md）
- 设计文档：`05-ui-components/03-scroll-container-components/04-grid-grid-item/design.md`
- 源码定位：`frameworks/core/components_ng/pattern/grid/`

## 用户故事

### US-1: 开发者使用 GridLayoutOptions 创建单行跨列不规则网格

作为 ArkUI 开发者，我想要通过 GridLayoutOptions.irregularIndexes 和 onGetIrregularSizeByIndex 让某些子项跨越多列（但仍在同一行内），以便在滚动网格中实现跨列卡片效果。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN GridLayoutOptions.irregularIndexes=[2] 且 onGetIrregularSizeByIndex(2) 返回 [1,2]（跨2列）但 rowSpan=1 THEN irregular_=false，实例化 GridScrollWithOptionsLayoutAlgorithm | 正常 |
| AC-1.2 | WHEN GridScrollWithOptionsLayoutAlgorithm 处理跨列项 THEN GetCrossStartAndSpan() 返回该项的起始列和跨列数，该行后续项跳过被占用的列 | 正常 |
| AC-1.3 | WHEN 跨列项跨列数超过 crossCount（如3列网格中跨4列）THEN 跨列数被 clamp 到 crossCount | 边界 |
| AC-1.4 | WHEN irregularIndexes 包含的索引超出子项总数 THEN 该索引被忽略，不产生布局异常 | 边界 |
| AC-1.5 | WHEN regularSize=[2,1]（每项占2列1行）且无 irregularIndexes THEN 所有项按 regularSize 布局，实例化 GridScrollWithOptionsLayoutAlgorithm | 正常 |

### US-2: 开发者使用 GridLayoutOptions 创建多行不规则网格

作为 ArkUI 开发者，我想要让某些子项跨越多行（main-axis），以便实现大卡片占据多行的瀑布式布局。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN onGetIrregularSizeByIndex 某项返回 rowSpan>1（如 [2,1]）THEN UpdateIrregularFlag() 设置 irregular_=true，实例化 GridIrregularLayoutAlgorithm | 正常 |
| AC-2.2 | WHEN GridIrregularLayoutAlgorithm 执行布局 THEN 使用 gridMatrix_ 二维矩阵记录每个格子的占用状态，GridIrregularFiller 按行扫描填充 | 正常 |
| AC-2.3 | WHEN 多行不规则项跨越的行数超过当前已知行数 THEN lineHeightMap_ 自动扩展新行，行高按实际内容计算 | 正常 |
| AC-2.4 | WHEN 不规则项位置与已有项冲突（gridMatrix_ 对应位置已占用）THEN 不规则项推迟到下一个可用位置 | 边界 |
| AC-2.5 | WHEN onGetIrregularSizeByIndex 返回 [0,0] THEN 该项视为 regularSize，不触发不规则布局 | 边界 |
| AC-2.6 | WHEN onGetRectByIndex 已设置且同时有 onGetStartIndexByIndex+onGetStartIndexByOffset THEN userDefined_=true 优先，实例化 GridCustomLayoutAlgorithm 而非 GridIrregularLayoutAlgorithm | 边界 |

### US-3: 开发者使用无模板自适应网格布局

作为 ArkUI 开发者，我想要在不设置 columnsTemplate/rowsTemplate 的情况下，通过 cellLength/maxCount/minCount 控制网格的行列数，以便在有限空间内自适应排列子项。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN columnsTemplate 和 rowsTemplate 均未设置 THEN 实例化 GridAdaptiveLayoutAlgorithm | 正常 |
| AC-3.2 | WHEN layoutDirection=Row THEN 自适应网格主轴为水平，子项沿水平方向排列 | 正常 |
| AC-3.3 | WHEN layoutDirection=Column THEN 自适应网格主轴为垂直，子项沿垂直方向排列 | 正常 |
| AC-3.4 | WHEN cellLength 指定且 maxCount/minCount 未设置 THEN 按 cellLength 自动计算行列数 | 正常 |
| AC-3.5 | WHEN maxCount=3 且按 cellLength 计算出的列数>3 THEN 实际列数=3 | 正常 |
| AC-3.6 | WHEN minCount=2 且按 cellLength 计算出的列数<2 THEN 实际列数=2 | 正常 |
| AC-3.7 | WHEN 自适应网格子项数量超过可视区域 THEN 多余子项溢出，不自动增加行，不可滚动 | 边界 |
| AC-3.8 | WHEN layoutDirection=RowReverse THEN 子项沿水平方向排列但顺序反转 | 正常 |
| AC-3.9 | WHEN layoutDirection=ColumnReverse THEN 子项沿垂直方向排列但顺序反转 | 正常 |

### US-4: 开发者使用自定义布局算法

作为 ArkUI 开发者，我想要通过 onGetRectByIndex 回调精确控制每个子项在网格中的位置和大小，并通过 onGetStartIndexByIndex/onGetStartIndexByOffset 支持滚动定位。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN GridLayoutOptions 同时包含 onGetStartIndexByIndex 和 onGetStartIndexByOffset THEN userDefined_=true，实例化 GridCustomLayoutAlgorithm | 正常 |
| AC-4.2 | WHEN 仅提供 onGetRectByIndex 但缺少 onGetStartIndexByIndex 或 onGetStartIndexByOffset THEN userDefined_=false，不实例化 GridCustomLayoutAlgorithm | 边界 |
| AC-4.3 | WHEN GridCustomLayoutAlgorithm 执行布局 THEN 调用 onGetRectByIndex(index) 获取每个子项的 {rowStart, rowSpan, columnStart, columnSpan}，按返回值定位 | 正常 |
| AC-4.4 | WHEN 滚动到指定 index THEN 调用 onGetStartIndexByIndex(index) 返回 GridStartLineInfo{startIndex, startLine, startOffset, totalOffset}，用于定位滚动起始位置 | 正常 |
| AC-4.5 | WHEN 按偏移量滚动 THEN 调用 onGetStartIndexByOffset(offset) 返回 GridStartLineInfo，用于计算可见区域起始项 | 正常 |
| AC-4.6 | WHEN onGetRectByIndex 返回的 rowStart/columnStart 为负值 THEN 视为无效位置，该子项不渲染 | 异常 |
| AC-4.7 | WHEN onGetRectByIndex 返回的 rowSpan/columnSpan 为0 THEN 视为无效尺寸，该子项不渲染 | 异常 |

### US-5: 开发者使用 C-API GridLayoutOptions

作为 C-API 开发者，我想要通过 NODE_GRID_LAYOUT_OPTIONS 创建不规则网格配置并设置到 Grid 组件上。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 调用 OH_ArkUI_GridLayoutOptions_Create() THEN 返回 ArkUI_GridLayoutOptions*，其中 regularSize 被 hardcode 为 [1,1] | 正常 |
| AC-5.2 | WHEN 调用 SetIrregularIndexes 设置不规则索引 THEN 后续通过 RegisterGetIrregularSizeByIndexCallback 可获取对应项尺寸 | 正常 |
| AC-5.3 | WHEN 调用 RegisterGetRectByIndexCallback 注册回调 THEN 自定义布局可通过 onGetRectByIndex 回调获取项位置 | 正常 |
| AC-5.4 | WHEN C-API 未提供 onGetStartIndexByOffset/onGetStartIndexByIndex 回调 THEN userDefined_=false，无法实例化 GridCustomLayoutAlgorithm | 边界 |
| AC-5.5 | WHEN C-API 调用者尝试设置 regularSize 为非 [1,1] THEN 设置无效，regularSize 仍为 [1,1] | 边界 |

### US-6: 开发者理解 irregular_ 标志的精确判定

作为 ArkUI 开发者，我想要理解 irregular_ 标志何时为 true，以便正确选择布局算法。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN onGetIrregularSizeByIndex 返回的 rowSpan=1（即使 columnSpan>1）THEN irregular_=false，使用 GridScrollWithOptionsLayoutAlgorithm | 正常 |
| AC-6.2 | WHEN onGetIrregularSizeByIndex 返回的 rowSpan>1 THEN irregular_=true，使用 GridIrregularLayoutAlgorithm | 正常 |
| AC-6.3 | WHEN onGetRectByIndex 返回的 rowSpan>1（且无 onGetStartIndexByIndex+onGetStartIndexByOffset）THEN irregular_=true | 正常 |
| AC-6.4 | WHEN onGetIrregularSizeByIndex 某项返回 [1,1]（等于 regularSize）THEN 该项视为 regular 项，不影响 irregular_ 标志 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-GRID-02 | UT: GridScrollWithOptionsLayoutAlgorithm 实例化条件 | grid_pattern.cpp:111-149 |
| AC-1.2 | R-2 | TASK-GRID-02 | UT: GetCrossStartAndSpan 跨列定位 | grid_scroll_with_options_layout_algorithm.cpp |
| AC-1.3 | R-3 | TASK-GRID-02 | UT: 跨列数超过 crossCount 的 clamp | grid_scroll_with_options_layout_algorithm.cpp |
| AC-1.4 | R-4 | TASK-GRID-02 | UT: 超出索引的 irregularIndexes 被忽略 | grid_layout_property.cpp:138-161 |
| AC-1.5 | R-5 | TASK-GRID-02 | UT: regularSize-only 无 irregularIndexes | grid_pattern.cpp:96-99 |
| AC-2.1 | R-6 | TASK-GRID-02 | UT: UpdateIrregularFlag rowSpan>1 → irregular_=true | grid_layout_property.cpp:138-161 |
| AC-2.2 | R-7 | TASK-GRID-02 | UT: gridMatrix_ + GridIrregularFiller 填充 | grid_irregular_layout_algorithm.cpp |
| AC-2.3 | R-8 | TASK-GRID-02 | UT: lineHeightMap_ 自动扩展 | grid_irregular_layout_algorithm.cpp |
| AC-2.4 | R-9 | TASK-GRID-02 | UT: gridMatrix_ 冲突检测 | grid_irregular_layout_algorithm.cpp |
| AC-2.5 | R-10 | TASK-GRID-02 | UT: onGetIrregularSizeByIndex 返回 [0,0] | grid_layout_property.cpp:138-161 |
| AC-2.6 | R-11 | TASK-GRID-02 | UT: userDefined_ 优先于 irregular_ | grid_pattern.cpp:111-149 |
| AC-3.1 | R-12 | TASK-GRID-02 | UT: 无模板 → GridAdaptiveLayoutAlgorithm | grid_pattern.cpp:111-149 |
| AC-3.2 | R-13 | TASK-GRID-02 | UT: layoutDirection=Row → 水平轴 | grid_adaptive_layout_algorithm.cpp:22-100 |
| AC-3.3 | R-14 | TASK-GRID-02 | UT: layoutDirection=Column → 垂直轴 | grid_adaptive_layout_algorithm.cpp:22-100 |
| AC-3.4 | R-15 | TASK-GRID-02 | UT: cellLength 自动计算行列数 | grid_adaptive_layout_algorithm.cpp:22-100 |
| AC-3.5 | R-16 | TASK-GRID-02 | UT: maxCount 限制列数 | grid_adaptive_layout_algorithm.cpp:22-100 |
| AC-3.6 | R-17 | TASK-GRID-02 | UT: minCount 保底列数 | grid_adaptive_layout_algorithm.cpp:22-100 |
| AC-3.7 | R-18 | TASK-GRID-02 | UT: 自适应网格溢出项不可滚动 | grid_adaptive_layout_algorithm.cpp |
| AC-3.8 | R-19 | TASK-GRID-02 | UT: RowReverse 方向 | grid_adaptive_layout_algorithm.cpp:22-100 |
| AC-3.9 | R-20 | TASK-GRID-02 | UT: ColumnReverse 方向 | grid_adaptive_layout_algorithm.cpp:22-100 |
| AC-4.1 | R-21 | TASK-GRID-02 | UT: userDefined_ 需两个回调同时存在 | grid_layout_property.cpp:144-145 |
| AC-4.2 | R-22 | TASK-GRID-02 | UT: 缺少任一回调 → userDefined_=false | grid_layout_property.cpp:144-145 |
| AC-4.3 | R-23 | TASK-GRID-02 | UT: onGetRectByIndex 返回值定位 | grid_custom_layout_algorithm.cpp |
| AC-4.4 | R-24 | TASK-GRID-02 | UT: onGetStartIndexByIndex 返回 GridStartLineInfo | grid_custom_layout_algorithm.cpp |
| AC-4.5 | R-25 | TASK-GRID-02 | UT: onGetStartIndexByOffset 返回 GridStartLineInfo | grid_custom_layout_algorithm.cpp |
| AC-4.6 | R-26 | TASK-GRID-02 | UT: rowStart/columnStart 负值 → 不渲染 | grid_custom_layout_algorithm.cpp |
| AC-4.7 | R-27 | TASK-GRID-02 | UT: rowSpan/columnSpan=0 → 不渲染 | grid_custom_layout_algorithm.cpp |
| AC-5.1 | R-28 | TASK-GRID-02 | UT: C-API regularSize hardcode [1,1] | grid_model_ng.cpp:958-959 |
| AC-5.2 | R-29 | TASK-GRID-02 | UT: SetIrregularIndexes + RegisterGetIrregularSizeByIndexCallback | grid_layout_option.h |
| AC-5.3 | R-30 | TASK-GRID-02 | UT: RegisterGetRectByIndexCallback | grid_layout_option.h |
| AC-5.4 | R-31 | TASK-GRID-02 | UT: C-API 缺少 systemapi 回调 → userDefined_=false | interfaces/native/node/grid_layout_option.h |
| AC-5.5 | R-32 | TASK-GRID-02 | UT: C-API 设置 regularSize 无效 | grid_model_ng.cpp:958-959 |
| AC-6.1 | R-1, R-6 | TASK-GRID-02 | UT: rowSpan=1 columnSpan>1 → irregular_=false | grid_layout_property.cpp:138-161 |
| AC-6.2 | R-6 | TASK-GRID-02 | UT: rowSpan>1 → irregular_=true | grid_layout_property.cpp:138-161 |
| AC-6.3 | R-6, R-33 | TASK-GRID-02 | UT: onGetRectByIndex rowSpan>1 → irregular_=true | grid_layout_property.cpp:138-161 |
| AC-6.4 | R-34 | TASK-GRID-02 | UT: 返回 [1,1] 不影响 irregular_ | grid_layout_property.cpp:138-161 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GridLayoutOptions 存在且 irregular_=false 且 userDefined_=false | 实例化 GridScrollWithOptionsLayoutAlgorithm | HasLayoutOptions()=true 是前提 | AC-1.1 |
| R-2 | 行为 | GridScrollWithOptionsLayoutAlgorithm 处理跨列项 | GetCrossStartAndSpan() 返回 {crossStart, crossSpan}，该行后续项跳过被占用的列 | 跨列项在同一行内排列 | AC-1.2 |
| R-3 | 边界 | 跨列数 > crossCount | crossSpan 被 clamp 到 crossCount | 不允许跨列数超过总列数 | AC-1.3 |
| R-4 | 边界 | irregularIndexes 中索引 >= 子项总数 | 该索引被忽略 | UpdateIrregularFlag 遍历时检查有效性 | AC-1.4 |
| R-5 | 行为 | GridLayoutOptions 仅含 regularSize 且无 irregularIndexes | 实例化 GridScrollWithOptionsLayoutAlgorithm | 所有项按 regularSize 布局 | AC-1.5 |
| R-6 | 行为 | onGetIrregularSizeByIndex 或 onGetRectByIndex 返回 rowSpan>1 | irregular_=true，实例化 GridIrregularLayoutAlgorithm | UpdateIrregularFlag() 检查 main-axis span | AC-2.1, AC-6.2 |
| R-7 | 行为 | GridIrregularLayoutAlgorithm 执行布局 | 使用 gridMatrix_ 二维矩阵记录占用，GridIrregularFiller 按行扫描填充 | gridMatrix_[row][col] 存储项索引或 -1(空) | AC-2.2 |
| R-8 | 行为 | 不规则项跨行数超过当前已知行数 | lineHeightMap_ 自动扩展新行 | 行高按实际内容测量 | AC-2.3 |
| R-9 | 边界 | 不规则项位置与已有项冲突 | 不规则项推迟到下一个可用位置 | GridIrregularFiller 检查 gridMatrix_ 占用 | AC-2.4 |
| R-10 | 边界 | onGetIrregularSizeByIndex 返回 [0,0] | 该项视为 regularSize，不触发 irregular_ | rows=0 或 columns=0 视为无效 | AC-2.5 |
| R-11 | 行为 | userDefined_=true 且 irregular_=true | userDefined_ 优先，实例化 GridCustomLayoutAlgorithm | CreateLayoutAlgorithm 分发顺序: userDefined_ 先于 irregular_ | AC-2.6 |
| R-12 | 行为 | columnsTemplate 和 rowsTemplate 均未设置 | 实例化 GridAdaptiveLayoutAlgorithm | setColumns=false && setRows=false | AC-3.1 |
| R-13 | 行为 | 自适应模式 + layoutDirection=Row | 主轴为水平，子项沿水平排列 | IsVertical()=false | AC-3.2 |
| R-14 | 行为 | 自适应模式 + layoutDirection=Column | 主轴为垂直，子项沿垂直排列 | IsVertical()=true | AC-3.3 |
| R-15 | 行为 | cellLength 指定且 maxCount/minCount 未设置 | 按 cellLength 自动计算行列数: crossCount = floor(totalSize / (cellLength + gap)) | cellLength=0 时退化 | AC-3.4 |
| R-16 | 边界 | 计算出的 crossCount > maxCount | crossCount = maxCount | maxCount 限制列数上限 | AC-3.5 |
| R-17 | 边界 | 计算出的 crossCount < minCount | crossCount = minCount | minCount 保底列数下限 | AC-3.6 |
| R-18 | 边界 | 自适应网格子项数量超过可视区域 | 多余子项溢出，不自动增加行，不可滚动 | IsConfiguredScrollable()=false | AC-3.7 |
| R-19 | 行为 | 自适应模式 + layoutDirection=RowReverse | 主轴为水平，子项排列顺序反转 | 视觉顺序与数据顺序相反 | AC-3.8 |
| R-20 | 行为 | 自适应模式 + layoutDirection=ColumnReverse | 主轴为垂直，子项排列顺序反转 | 视觉顺序与数据顺序相反 | AC-3.9 |
| R-21 | 行为 | GridLayoutOptions 同时含 onGetStartIndexByIndex 和 onGetStartIndexByOffset | userDefined_=true，实例化 GridCustomLayoutAlgorithm | 两个回调都存在才触发 | AC-4.1 |
| R-22 | 边界 | 仅提供 onGetRectByIndex 但缺少 onGetStartIndexByIndex 或 onGetStartIndexByOffset | userDefined_=false，不实例化 GridCustomLayoutAlgorithm | 缺少任一回调无法支持滚动定位 | AC-4.2 |
| R-23 | 行为 | GridCustomLayoutAlgorithm 执行布局 | 调用 onGetRectByIndex(index) 获取 {rowStart, rowSpan, columnStart, columnSpan}，按返回值定位 | 每个项位置由回调决定 | AC-4.3 |
| R-24 | 行为 | 滚动到指定 index | 调用 onGetStartIndexByIndex(index) 返回 GridStartLineInfo{startIndex, startLine, startOffset, totalOffset} | @systemapi @since 23 | AC-4.4 |
| R-25 | 行为 | 按偏移量滚动 | 调用 onGetStartIndexByOffset(offset) 返回 GridStartLineInfo | @systemapi @since 23 | AC-4.5 |
| R-26 | 异常 | onGetRectByIndex 返回 rowStart<0 或 columnStart<0 | 该子项不渲染 | 无效位置 | AC-4.6 |
| R-27 | 异常 | onGetRectByIndex 返回 rowSpan=0 或 columnSpan=0 | 该子项不渲染 | 无效尺寸 | AC-4.7 |
| R-28 | 行为 | C-API 调用 OH_ArkUI_GridLayoutOptions_Create() | regularSize 被 hardcode 为 [1,1] | grid_model_ng.cpp:958-959 | AC-5.1 |
| R-29 | 行为 | C-API SetIrregularIndexes + RegisterGetIrregularSizeByIndexCallback | 后续通过回调获取对应项尺寸 | C-API 不规则网格配置 | AC-5.2 |
| R-30 | 行为 | C-API RegisterGetRectByIndexCallback | 自定义布局可通过回调获取项位置 | C-API 自定义布局 | AC-5.3 |
| R-31 | 边界 | C-API 未提供 onGetStartIndexByOffset/onGetStartIndexByIndex | userDefined_=false，无法实例化 GridCustomLayoutAlgorithm | C-API 缺少 @systemapi 回调 | AC-5.4 |
| R-32 | 边界 | C-API 调用者尝试设置 regularSize 为非 [1,1] | 设置无效，regularSize 仍为 [1,1] | C-API hardcode 不允许修改 | AC-5.5 |
| R-33 | 行为 | onGetRectByIndex 返回 rowSpan>1 且无 onGetStartIndexByIndex+onGetStartIndexByOffset | irregular_=true，实例化 GridIrregularLayoutAlgorithm | onGetRectByIndex 也参与 irregular_ 判定 | AC-6.3 |
| R-34 | 边界 | onGetIrregularSizeByIndex 返回 [1,1]（等于 regularSize） | 该项视为 regular 项，不影响 irregular_ 标志 | 只有超出 regularSize 的项才触发 irregular_ | AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | GridScrollWithOptionsLayoutAlgorithm 分发条件 | UT: CreateLayoutAlgorithm HasLayoutOptions 分支 | irregular_=false, userDefined_=false 时实例化 |
| VM-2 | 单行跨列定位 | UT: GetCrossStartAndSpan | 跨列项在同一行内正确定位 |
| VM-3 | GridIrregularLayoutAlgorithm 分发条件 | UT: UpdateIrregularFlag rowSpan>1 | irregular_=true 时实例化 |
| VM-4 | gridMatrix_ 填充 | UT: GridIrregularFiller::Fill | 二维矩阵占用状态正确 |
| VM-5 | lineHeightMap_ 扩展 | UT: 多行不规则项跨行时行高计算 | 行高按实际内容测量 |
| VM-6 | GridAdaptiveLayoutAlgorithm 分发条件 | UT: CreateLayoutAlgorithm 无模板分支 | setColumns=false && setRows=false |
| VM-7 | 自适应 cellLength/maxCount/minCount | UT: GridAdaptiveLayoutAlgorithm::Measure | 行列数计算受约束 |
| VM-8 | 自适应不可滚动 | UT: IsConfiguredScrollable()=false | 溢出项不触发滚动 |
| VM-9 | layoutDirection 轴向选择 | UT: GridAdaptiveLayoutAlgorithm IsVertical() | Row→水平, Column→垂直 |
| VM-10 | GridCustomLayoutAlgorithm 分发条件 | UT: CreateLayoutAlgorithm userDefined_ 分支 | 两个回调同时存在 |
| VM-11 | onGetRectByIndex 定位 | UT: GridCustomLayoutAlgorithm::Measure | 按 {rowStart, rowSpan, columnStart, columnSpan} 定位 |
| VM-12 | onGetStartIndexByIndex/Offset | UT: GridCustomLayoutAlgorithm 滚动定位 | GridStartLineInfo 返回值正确 |
| VM-13 | userDefined_ 优先于 irregular_ | UT: CreateLayoutAlgorithm 分发顺序 | userDefined_=true 时跳过 irregular_ 判断 |
| VM-14 | irregular_ 标志精确判定 | UT: UpdateIrregularFlag rowSpan vs columnSpan | rowSpan>1 才触发，columnSpan>1 不触发 |
| VM-15 | C-API regularSize hardcode | UT: GridModelNG C-API 路径 | regularSize 固定为 [1,1] |
| VM-16 | C-API 缺少 systemapi 回调 | UT: C-API GridLayoutOptions 回调注册 | 无 onGetStartIndexByOffset/OnGetStartIndexByIndex |

## API 变更分析

### 新增 API

> 本规格为存量补录，以下 API 已在 SDK 中存在。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| GridLayoutOptions.regularSize | Public | [number, number] | — | 无 | 正常项占用的行列数 (@since 10) | AC-1.1, AC-1.5 |
| GridLayoutOptions.irregularIndexes | Public | number[] | — | 无 | 不规则项索引列表 (@since 10) | AC-1.1, AC-2.1 |
| GridLayoutOptions.onGetIrregularSizeByIndex | Public | (index: number) => GridItemSize | GridItemSize | 无 | 不规则项尺寸回调 (@since 10) | AC-1.1, AC-2.1 |
| GridLayoutOptions.onGetRectByIndex | Public | (index: number) => GridItemRect | GridItemRect | 无 | 自定义项位置回调 (@since 11) | AC-4.3, AC-6.3 |
| GridLayoutOptions.onGetStartIndexByOffset | SystemAPI | (offset: number) => GridStartLineInfo | GridStartLineInfo | 无 | 按偏移量获取起始索引 (@systemapi @since 23) | AC-4.5 |
| GridLayoutOptions.onGetStartIndexByIndex | SystemAPI | (index: number) => GridStartLineInfo | GridStartLineInfo | 无 | 按索引获取起始行信息 (@systemapi @since 23) | AC-4.4 |
| GridDirection enum | Public | Row/Column/RowReverse/ColumnReverse | — | 无 | 网格布局方向 (@since 8) | AC-3.2–AC-3.9 |
| cellLength | Public | number | — | 无 | 自适应网格单元格长度 (@since 8) | AC-3.4 |
| maxCount | Public | number | — | 无 | 自适应网格最大行列数 (@since 8) | AC-3.5 |
| minCount | Public | number | — | 无 | 自适应网格最小行列数 (@since 8) | AC-3.6 |
| NODE_GRID_LAYOUT_OPTIONS | SystemAPI | — | ArkUI_NodeHandle | 无 | C-API GridLayoutOptions 节点 (@since 22) | AC-5.1 |
| OH_ArkUI_GridLayoutOptions_Create | SystemAPI | — | ArkUI_GridLayoutOptions* | 无 | C-API 创建 GridLayoutOptions (@since 22) | AC-5.1 |
| OH_ArkUI_GridLayoutOptions_Dispose | SystemAPI | ArkUI_GridLayoutOptions* | void | 无 | C-API 销毁 GridLayoutOptions (@since 22) | AC-5.1 |
| OH_ArkUI_GridLayoutOptions_SetIrregularIndexes | SystemAPI | ArkUI_GridLayoutOptions*, int32_t*, int32_t | void | 无 | C-API 设置不规则索引 (@since 22) | AC-5.2 |
| OH_ArkUI_GridLayoutOptions_RegisterGetIrregularSizeByIndexCallback | SystemAPI | ArkUI_GridLayoutOptions*, callback | void | 无 | C-API 注册尺寸回调 (@since 22) | AC-5.2 |
| OH_ArkUI_GridLayoutOptions_RegisterGetRectByIndexCallback | SystemAPI | ArkUI_GridLayoutOptions*, callback | void | 无 | C-API 注册位置回调 (@since 22) | AC-5.3 |

### 变更/废弃 API

无新增变更或废弃。

## 接口规格

### 接口定义

**GridLayoutOptions.regularSize**

| 属性 | 值 |
|------|-----|
| 函数签名 | `regularSize: [number, number]` |
| 返回值 | `[number, number]` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| regularSize | [number, number] | 否 | [1, 1] | [rows, columns]；rows≥1, columns≥1；C-API hardcode 为 [1,1] |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | regularSize=[2,1] | 每个正常项占2行1列 | AC-1.5 |
| 2 | regularSize=[0,0] | 视为无效，退化为 [1,1] | 边界 |
| 3 | C-API 调用 | regularSize 固定为 [1,1]，设置无效 | AC-5.5 |

---

**GridLayoutOptions.irregularIndexes**

| 属性 | 值 |
|------|-----|
| 函数签名 | `irregularIndexes: number[]` |
| 返回值 | `number[]` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| irregularIndexes | number[] | 否 | [] | 索引值 ≥0；超出子项总数的索引被忽略 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | irregularIndexes=[2,5] | 索引2和5的项使用 onGetIrregularSizeByIndex 返回的尺寸 | AC-1.1 |
| 2 | irregularIndexes=[] | 无不规则项，按 regularSize 布局 | AC-1.5 |
| 3 | irregularIndexes 包含超出子项总数的索引 | 该索引被忽略 | AC-1.4 |

---

**GridLayoutOptions.onGetIrregularSizeByIndex**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onGetIrregularSizeByIndex: (index: number) => GridItemSize` |
| 返回值 | `GridItemSize { rows: number, columns: number }` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| index | number | 是 | — | 项索引，≥0 |
| 返回值.rows | number | — | 1 | 行跨数；rows>1 触发 irregular_=true |
| 返回值.columns | number | — | 1 | 列跨数；columns>1 不触发 irregular_ |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 返回 [1,2]（rowSpan=1, colSpan=2） | 跨列但同行，irregular_=false，使用 GridScrollWithOptionsLayoutAlgorithm | AC-1.1 |
| 2 | 返回 [2,1]（rowSpan=2, colSpan=1） | 跨行，irregular_=true，使用 GridIrregularLayoutAlgorithm | AC-2.1 |
| 3 | 返回 [0,0] | 视为 regularSize，不影响 irregular_ | AC-2.5 |
| 4 | 返回 [1,1]（等于 regularSize） | 视为 regular 项 | AC-6.4 |

---

**GridLayoutOptions.onGetRectByIndex**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onGetRectByIndex: (index: number) => GridItemRect` |
| 返回值 | `GridItemRect { rowStart: number, rowSpan: number, columnStart: number, columnSpan: number }` |
| 开放范围 | Public (@since 11) |
| 错误码 | N/A |
| 关联 AC | AC-4.3, AC-6.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| index | number | 是 | — | 项索引，≥0 |
| 返回值.rowStart | number | — | -1 | 起始行；<0 时子项不渲染 |
| 返回值.rowSpan | number | — | 1 | 行跨数；=0 时子项不渲染 |
| 返回值.columnStart | number | — | -1 | 起始列；<0 时子项不渲染 |
| 返回值.columnSpan | number | — | 1 | 列跨数；=0 时子项不渲染 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 返回 {rowStart:0, rowSpan:2, columnStart:0, columnSpan:2} | 子项占2行2列，从(0,0)开始 | AC-4.3 |
| 2 | 返回 rowStart<0 或 columnStart<0 | 子项不渲染 | AC-4.6 |
| 3 | 返回 rowSpan=0 或 columnSpan=0 | 子项不渲染 | AC-4.7 |
| 4 | 返回 rowSpan>1 且无 onGetStartIndexByIndex+onGetStartIndexByOffset | irregular_=true，使用 GridIrregularLayoutAlgorithm | AC-6.3 |

---

**GridLayoutOptions.onGetStartIndexByIndex**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onGetStartIndexByIndex: (index: number) => GridStartLineInfo` |
| 返回值 | `GridStartLineInfo { startIndex: number, startLine: number, startOffset: number, totalOffset: number }` |
| 开放范围 | SystemAPI (@since 23) |
| 错误码 | N/A |
| 关联 AC | AC-4.1, AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| index | number | 是 | — | 项索引，≥0 |
| 返回值.startIndex | number | — | 0 | 起始项索引 |
| 返回值.startLine | number | — | 0 | 起始行号 |
| 返回值.startOffset | number | — | 0.0 | 起始偏移量 |
| 返回值.totalOffset | number | — | 0.0 | 总偏移量 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 滚动到指定 index | 调用此回调获取 GridStartLineInfo，用于定位滚动起始位置 | AC-4.4 |
| 2 | 此回调与 onGetStartIndexByOffset 同时存在 | userDefined_=true | AC-4.1 |

---

**GridLayoutOptions.onGetStartIndexByOffset**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onGetStartIndexByOffset: (offset: number) => GridStartLineInfo` |
| 返回值 | `GridStartLineInfo { startIndex: number, startLine: number, startOffset: number, totalOffset: number }` |
| 开放范围 | SystemAPI (@since 23) |
| 错误码 | N/A |
| 关联 AC | AC-4.1, AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| offset | number | 是 | — | 滚动偏移量，≥0 |
| 返回值 | GridStartLineInfo | — | — | 同 onGetStartIndexByIndex |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 按偏移量滚动 | 调用此回调获取 GridStartLineInfo，用于计算可见区域起始项 | AC-4.5 |
| 2 | 此回调与 onGetStartIndexByIndex 同时存在 | userDefined_=true | AC-4.1 |

---

**GridDirection enum**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enum GridDirection { Row, Column, RowReverse, ColumnReverse }` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-3.2–AC-3.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | GridDirection | 是 | Row | 仅在自适应模式（无模板）下影响轴向；滚动模式下由模板决定 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 自适应模式 + Row | 主轴=水平，IsVertical()=false | AC-3.2 |
| 2 | 自适应模式 + Column | 主轴=垂直，IsVertical()=true | AC-3.3 |
| 3 | 自适应模式 + RowReverse | 主轴=水平，子项顺序反转 | AC-3.8 |
| 4 | 自适应模式 + ColumnReverse | 主轴=垂直，子项顺序反转 | AC-3.9 |
| 5 | 滚动模式 + layoutDirection | layoutDirection 不改变轴向 | AC-3.2（边界） |

---

**cellLength / maxCount / minCount**

| 属性 | 值 |
|------|-----|
| 函数签名 | `cellLength(value: number): GridAttribute` / `maxCount(value: number): GridAttribute` / `minCount(value: number): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-3.4–AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| cellLength | number | 是 | — | 单元格长度，≥0；=0 时退化为1列 |
| maxCount | number | 是 | — | 最大行列数，≥1；限制计算出的 crossCount 上限 |
| minCount | number | 是 | — | 最小行列数，≥1；限制计算出的 crossCount 下限 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | cellLength=100vp, 宽度300vp, gap=0 | crossCount=floor(300/100)=3 | AC-3.4 |
| 2 | cellLength=50vp, 宽度300vp, maxCount=3 | crossCount=min(floor(300/50), 3)=3 | AC-3.5 |
| 3 | cellLength=200vp, 宽度300vp, minCount=2 | crossCount=max(floor(300/200), 2)=2 | AC-3.6 |

---

**C-API: OH_ArkUI_GridLayoutOptions_Create / Dispose / SetIrregularIndexes / RegisterGetIrregularSizeByIndexCallback / RegisterGetRectByIndexCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_GridLayoutOptions* OH_ArkUI_GridLayoutOptions_Create()` / `void OH_ArkUI_GridLayoutOptions_Dispose(ArkUI_GridLayoutOptions*)` / `void OH_ArkUI_GridLayoutOptions_SetIrregularIndexes(ArkUI_GridLayoutOptions*, int32_t*, int32_t)` / `void OH_ArkUI_GridLayoutOptions_RegisterGetIrregularSizeByIndexCallback(ArkUI_GridLayoutOptions*, callback)` / `void OH_ArkUI_GridLayoutOptions_RegisterGetRectByIndexCallback(ArkUI_GridLayoutOptions*, callback)` |
| 开放范围 | SystemAPI (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-5.1–AC-5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options | ArkUI_GridLayoutOptions* | 是 | — | 由 Create 创建；Dispose 后不可再使用 |
| indexes | int32_t* | 是 | — | 不规则索引数组 |
| count | int32_t | 是 | — | 索引数组长度 |
| callback | 函数指针 | 是 | — | 尺寸/位置回调函数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 Create | 返回 ArkUI_GridLayoutOptions*，regularSize=[1,1] | AC-5.1 |
| 2 | 调用 SetIrregularIndexes | 设置不规则索引，后续通过回调获取尺寸 | AC-5.2 |
| 3 | 调用 RegisterGetRectByIndexCallback | 注册位置回调 | AC-5.3 |
| 4 | C-API 无 onGetStartIndexByOffset/OnGetStartIndexByIndex | userDefined_=false | AC-5.4 |
| 5 | 尝试修改 regularSize | 设置无效，仍为 [1,1] | AC-5.5 |

## 兼容性声明

- **已有 API 行为变更:** 否。所有 API 为存量补录。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8（cellLength/maxCount/minCount/GridDirection），API 10（GridLayoutOptions），API 11（onGetRectByIndex），API 22（C-API GridLayoutOptions），API 23（onGetStartIndexByOffset/onGetStartIndexByIndex @systemapi）
- **API 版本号策略:** @since 标注按各 API 最早引入版本

- **SDK vs 源码偏差风险:**
  - C-API GridLayoutOptions hardcodes regularSize=[1,1]（grid_model_ng.cpp:958-959），SDK 允许用户指定 regularSize — 此偏差需在兼容性表标注
  - C-API 缺少 onGetStartIndexByOffset/onGetStartIndexByIndex 回调（@systemapi），SDK 有此功能 — C-API 未实现
  - irregular_ 标志仅由 rowSpan>1 触发，columnSpan>1 不触发 — 此行为与开发者直觉（"跨列即不规则"）可能不符

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 6种算法分发 | CreateLayoutAlgorithm() 按条件级联判断：无模板→自适应, 双模板→固定, 单模板→[userDefined→自定义, irregular→不规则, options→滚动+选项, else→滚动] | AC-1.1, AC-2.1, AC-3.1, AC-4.1 |
| userDefined_ 优先于 irregular_ | CreateLayoutAlgorithm 分发顺序: userDefined_ 先于 irregular_ 判断 | AC-2.6, AC-4.1 |
| irregular_ 仅由 rowSpan>1 触发 | columnSpan>1 不触发 irregular_=true，使用 GridScrollWithOptionsLayoutAlgorithm | AC-1.1, AC-6.1 |
| 自适应网格不可滚动 | GridAdaptiveLayoutAlgorithm 的 IsConfiguredScrollable()=false | AC-3.7 |
| GridCustomLayoutAlgorithm 需两个回调同时存在 | onGetStartIndexByIndex + onGetStartIndexByOffset 缺一不可 | AC-4.1, AC-4.2 |
| C-API regularSize hardcode [1,1] | C-API 调用者无法修改 regularSize | AC-5.1, AC-5.5 |
| C-API 缺少 systemapi 回调 | C-API 无法使用 onGetStartIndexByOffset/onGetStartIndexByIndex | AC-5.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | GridIrregularLayoutAlgorithm gridMatrix_ 填充 <16ms | 帧时间采集 | Trace 打点 |
| 性能 | GridCustomLayoutAlgorithm 布局 <16ms | 帧时间采集 | Trace 打点 |
| 性能 | 自适应网格 Measure <8ms | 帧时间采集 | Trace 打点 |
| 内存 | gridMatrix_ 大小受 crossCount×mainCount 约束 | Dump 机制 | grid_irregular_layout_algorithm.cpp |
| 可测试性 | CreateLayoutAlgorithm 各分支可独立 UT | Mock GridLayoutProperty | grid_pattern.cpp:111-149 |
| 可测试性 | UpdateIrregularFlag 判定逻辑可独立 UT | Mock onGetIrregularSizeByIndex/onGetRectByIndex | grid_layout_property.cpp:138-161 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 自适应网格 cellLength 按 vp 计算 | cellLength=100vp 在不同宽度手机上列数不同 | 多分辨率测试 | — |
| 平板 | 自适应网格列数更多 | cellLength 不变但宽度更大 → crossCount 更大 | 平板专项测试 | — |
| 折叠屏 | 折叠态变化触发自适应网格重新计算 | cellLength/maxCount/minCount 重新计算行列数 | 折叠适配测试 | — |
| 穿戴 | 不规则网格因屏幕较小可能无法完整显示跨行跨列项 | 不规则项超出可视区域时被裁剪 | 穿戴专项测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | GridItem 语义节点含 rowStart/columnStart/rowSpan/columnSpan 等位置信息 | 辅助技术读取不规则项位置 |
| 大字体 | 是 | 不规则项跨行时行高受大字体影响，lineHeightMap_ 按实际内容计算 | 大字体适配 |
| 深色模式 | 否 | Grid 无颜色属性，深色模式由子项决定 | — |
| 多窗口/分屏 | 是 | 自适应网格 cellLength/maxCount/minCount 在分屏时重新计算 | 分屏重布局 |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | onGetStartIndexByOffset/onGetStartIndexByIndex @systemapi @since 23 | 低版本设备不支持 |
| 生态兼容 | 否 | — | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Grid 不规则、自适应与自定义布局算法分发
  作为 ArkUI 开发者
  我想要根据 GridLayoutOptions 和模板配置选择正确的布局算法
  以便网格呈现预期的布局行为

  Scenario: GridLayoutOptions 单行跨列 → GridScrollWithOptionsLayoutAlgorithm
    Given GridLayoutOptions.irregularIndexes=[2]
    And onGetIrregularSizeByIndex(2) 返回 [1,2]
    And columnsTemplate="1fr 1fr 1fr"
    When Grid 执行 CreateLayoutAlgorithm()
    Then irregular_=false
    And 实例化 GridScrollWithOptionsLayoutAlgorithm

  Scenario: GridLayoutOptions 多行跨行 → GridIrregularLayoutAlgorithm
    Given GridLayoutOptions.irregularIndexes=[2]
    And onGetIrregularSizeByIndex(2) 返回 [2,1]
    And columnsTemplate="1fr 1fr 1fr"
    When Grid 执行 CreateLayoutAlgorithm()
    Then irregular_=true
    And 实例化 GridIrregularLayoutAlgorithm

  Scenario: 无模板 → GridAdaptiveLayoutAlgorithm
    Given columnsTemplate 未设置
    And rowsTemplate 未设置
    And layoutDirection=Column
    When Grid 执行 CreateLayoutAlgorithm()
    Then 实例化 GridAdaptiveLayoutAlgorithm
    And IsVertical()=true
    And IsConfiguredScrollable()=false

  Scenario: 自定义布局 → GridCustomLayoutAlgorithm
    Given GridLayoutOptions 含 onGetStartIndexByIndex
    And GridLayoutOptions 含 onGetStartIndexByOffset
    And columnsTemplate="1fr 1fr 1fr"
    When Grid 执行 CreateLayoutAlgorithm()
    Then userDefined_=true
    And 实例化 GridCustomLayoutAlgorithm

  Scenario: userDefined_ 优先于 irregular_
    Given GridLayoutOptions 含 onGetStartIndexByIndex 和 onGetStartIndexByOffset
    And onGetIrregularSizeByIndex 某项返回 rowSpan>1
    When Grid 执行 CreateLayoutAlgorithm()
    Then 实例化 GridCustomLayoutAlgorithm
    And 不实例化 GridIrregularLayoutAlgorithm

  Scenario: 自适应网格 cellLength/maxCount/minCount
    Given cellLength=100vp
    And maxCount=3
    And minCount=2
    And Grid 宽度=250vp
    When GridAdaptiveLayoutAlgorithm 执行 Measure
    Then crossCount=floor(250/100)=2
    And minCount=2 不触发下限提升
    And maxCount=3 不触发上限截断

  Scenario: C-API regularSize hardcode
    Given C-API 调用 OH_ArkUI_GridLayoutOptions_Create()
    When 获取 regularSize
    Then regularSize=[1,1]
    And 后续设置 regularSize 无效

  Scenario: 不规则项 gridMatrix_ 填充
    Given GridIrregularLayoutAlgorithm 布局
    And 3列网格
    And index=2 的项跨2行2列
    When GridIrregularFiller 执行填充
    Then gridMatrix_[0][0] 被该项占用
    And gridMatrix_[0][1] 被该项占用
    And gridMatrix_[1][0] 被该项占用
    And gridMatrix_[1][1] 被该项占用
    And 后续项跳过已占用格子
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
    query: "Grid 6种布局算法分发机制 (grid_pattern.cpp CreateLayoutAlgorithm)"
  - repo: "openharmony/ace_engine"
    query: "Grid irregular_ 标志判定逻辑 (grid_layout_property.cpp UpdateIrregularFlag)"
  - repo: "openharmony/ace_engine"
    query: "GridIrregularLayoutAlgorithm gridMatrix_ + GridIrregularFiller 填充 (grid_irregular_layout_algorithm.cpp)"
  - repo: "openharmony/ace_engine"
    query: "GridScrollWithOptionsLayoutAlgorithm GetCrossStartAndSpan 单行跨列 (grid_scroll_with_options_layout_algorithm.cpp)"
  - repo: "openharmony/ace_engine"
    query: "GridAdaptiveLayoutAlgorithm cellLength/maxCount/minCount 自适应 (grid_adaptive_layout_algorithm.cpp)"
  - repo: "openharmony/ace_engine"
    query: "GridCustomLayoutAlgorithm userDefined_ onGetRectByIndex/getStartIndexByIndex/getStartIndexByOffset (grid_custom_layout_algorithm.cpp)"
  - repo: "openharmony/ace_engine"
    query: "C-API GridLayoutOptions regularSize hardcode [1,1] (grid_model_ng.cpp)"
```

**关键文档：**
- SDK 动态 API: `interface/sdk-js/api/@internal/component/ets/grid.d.ts`
- SDK 静态 API: `interface/sdk-js/api/arkui/component/grid.static.d.ets`
- C-API: `interfaces/native/native_node.h` (NODE_GRID_LAYOUT_OPTIONS), `interfaces/native/node/grid_layout_option.h`
- 源码入口: `frameworks/core/components_ng/pattern/grid/`
- 关键源码: `grid_pattern.cpp:111-149` (CreateLayoutAlgorithm), `grid_layout_property.cpp:138-161` (UpdateIrregularFlag), `grid_layout_options.h` (GridLayoutOptions/GridItemSize/GridItemRect/GridStartLineInfo)
