# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Grid 固定行列与单轴滚动布局 |
| 特性编号 | Func-05-03-04-Feat-01 |
| 所属 Epic | Grid/GridItem 组件规格补录 |
| 优先级 | P0 |
| 目标版本 | API 7–22 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 存量特性补录（lineage: new-on-legacy），本规格补录已有实现的行为。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Grid 构造器与算法分发机制 | 6种布局算法的实例化判定逻辑 |
| ADDED | columnsTemplate/rowsTemplate 双模板→GridLayoutAlgorithm 固定网格 | columnsTemplate+rowsTemplate 同时设置 → 非滚动静态网格 |
| ADDED | columnsTemplate/rowsTemplate 单模板→GridScrollLayoutAlgorithm 单轴滚动网格 | 仅设置一个模板 → 可滚动 |
| ADDED | ItemFillPolicy 响应式列填充 | columnsTemplate(string) 与 ItemFillPolicy 互斥 |
| ADDED | columnsGap/rowsGap 间距属性 | 列间距和行间距 |
| ADDED | layoutDirection(GridDirection) 布局方向 | 仅在自适应模式下影响轴向；滚动模式下由模板决定 |
| ADDED | cachedCount 缓存预加载数量 | 含 show overload (API 14) |
| ADDED | syncLoad 同步加载控制 | 控制子项是否逐帧分批加载 |
| ADDED | alignItems(GridItemAlignment) 对齐方式 | DEFAULT=居中, STRETCH=填满格子 |

## 输入文档

- 需求基线：已有能力补录（无独立 requirement.md）
- 设计文档：`05-ui-components/03-scroll-container-components/04-grid-grid-item/design.md`
- 源码定位：`frameworks/core/components_ng/pattern/grid/`

## 用户故事

### US-1: 开发者使用双模板创建固定网格

作为 ArkUI 开发者，我想要同时设置 columnsTemplate 和 rowsTemplate 创建行列数固定的网格布局，以便所有子项在有限空间内完整展示且不需要滚动。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN columnsTemplate="1fr 1fr 1fr" 且 rowsTemplate="1fr 1fr" THEN Grid 实例化 GridLayoutAlgorithm，渲染为3列×2行的固定网格，所有子项可见，不可滚动 | 正常 |
| AC-1.2 | WHEN columnsTemplate 和 rowsTemplate 同时设置 THEN IsConfiguredScrollable()=false，滚动条状态自动设为 OFF | 正常 |
| AC-1.3 | WHEN 双模板模式下子项数量超出行列格子总数 THEN 多余子项溢出网格边界外，不自动增加行 | 边界 |
| AC-1.4 | WHEN columnsTemplate 设为空字符串 THEN 等效于未设置列模板，与 rowsTemplate 单独设置情况相同 → 水平滚动网格 | 边界 |

### US-2: 开发者使用单模板创建可滚动网格

作为 ArkUI 开发者，我想要仅设置 columnsTemplate（或 rowsTemplate）创建单轴可滚动网格，以便在有限列/行宽度下通过滚动查看更多内容。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 仅设置 columnsTemplate="1fr 1fr" THEN Grid 实例化 GridScrollLayoutAlgorithm（当无 GridLayoutOptions 时），轴向为 VERTICAL，垂直方向可滚动 | 正常 |
| AC-2.2 | WHEN 仅设置 rowsTemplate="1fr 1fr" THEN 轴向为 HORIZONTAL，水平方向可滚动 | 正常 |
| AC-2.3 | WHEN 单模板模式设置 layoutDirection=Column THEN layoutDirection 不改变轴向；轴向仍由模板决定（columnsTemplate→VERTICAL） | 边界 |
| AC-2.4 | WHEN 仅设置 ItemFillPolicy（无 columnsTemplate/rowsTemplate） THEN 视为"仅设置列模板"→ IsVertical()=true，垂直可滚动 | 正常 |

### US-3: 开发者使用 ItemFillPolicy 响应式列填充

作为 ArkUI 开发者，我想要使用 ItemFillPolicy 代替 columnsTemplate 字符串，以便根据屏幕宽度自动适配列数。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 columnsTemplate(string) THEN ItemFillPolicy 被自动 reset 为空（互斥） | 正常 |
| AC-3.2 | WHEN 设置 ItemFillPolicy=SM1MD2LG3 THEN columnsTemplate 被自动 reset 为空（互斥） | 正常 |
| AC-3.3 | WHEN ItemFillPolicy 设置后再设置 columnsTemplate THEN 最终生效的是 columnsTemplate，ItemFillPolicy 被清除 | 边界 |
| AC-3.4 | WHEN ItemFillPolicy=SM1MD2LG3 且屏幕宽度匹配 SM 断点 THEN 自动生成2列模板 | 正常 |

### US-4: 开发者配置间距和对齐

作为 ArkUI 开发者，我想要设置 columnsGap/rowsGap 控制网格单元格间距，以及 alignItems 控制子项在单元格内的对齐方式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN columnsGap=10vp, rowsGap=8vp, columnsTemplate="1fr 1fr 1fr", 宽度300vp THEN 每列宽度=(300-2×10)/3=93.33vp | 正常 |
| AC-4.2 | WHEN columnsGap 值超过可用空间 THEN gap 被 clamped 到 0 | 边界 |
| AC-4.3 | WHEN alignItems=DEFAULT 且子项尺寸小于格子 THEN 子项在格子内居中对齐 | 正常 |
| AC-4.4 | WHEN alignItems=STRETCH 且子项无 selfIdealSize THEN 子项在主轴方向填满整行高度 | 正常 |
| AC-4.5 | WHEN alignItems=STRETCH 且子项有 selfIdealSize.Height=50vp THEN 子项保持 50vp 高度不拉伸 | 边界 |

### US-5: 开发者配置缓存和加载策略

作为 ArkUI 开发者，我想要设置 cachedCount 控制预加载范围，以及 syncLoad 控制是否逐帧分批加载。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN cachedCount=2, crossCount=3(3列) THEN 在可见区域前后各缓存 2×3=6 个子项 | 正常 |
| AC-5.2 | WHEN cachedCount(count, show=true) THEN 缓存项可见地渲染（show=true） | 正常 |
| AC-5.3 | WHEN syncLoad=false 且帧预算耗尽 THEN 未测量子项延迟到下一帧 | 正常 |
| AC-5.4 | WHEN syncLoad=true THEN 所有子项在当前帧内完成测量 | 正常 |
| AC-5.5 | WHEN 滚动偏移发生变化 THEN syncLoad 临时强制为 true，确保滚动响应即时 | 边界 |

### US-6: 开发者使用 GridLayoutOptions 创建不规则网格

作为 ArkUI 开发者，我想要通过 GridLayoutOptions 指定 irregularIndexes 和 onGetIrregularSizeByIndex，以便某些子项跨越多列/多行。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN GridLayoutOptions 包含 irregularIndexes=[2,5] 且 index=2 的 sizeByIndex 返回 [1,2]（跨2列） THEN Grid 实例化 GridIrregularLayoutAlgorithm | 正常 |
| AC-6.2 | WHEN GridLayoutOptions 包含 onGetRectByIndex 且同时包含 onGetStartIndexByOffset+onGetStartIndexByIndex THEN userDefined_=true，实例化 GridCustomLayoutAlgorithm | 边界 |
| AC-6.3 | WHEN GridLayoutOptions 仅设置 regularSize=[2,3] 且无 irregularIndexes THEN 实例化 GridScrollWithOptionsLayoutAlgorithm（非自定义/非不规则） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1, R-2 | TASK-GRID-01 | UT: GridPattern::CreateLayoutAlgorithm 双模板分支 | grid_pattern.cpp:127-128 |
| AC-1.2 | R-2 | TASK-GRID-01 | UT: IsConfiguredScrollable() 双模板返回 false | grid_layout_property.cpp:72-78 |
| AC-1.3 | R-3 | TASK-GRID-01 | UT: 静态网格溢出项超出边界 | grid_layout_algorithm.cpp:277 |
| AC-1.4 | R-4 | TASK-GRID-01 | UT: 空模板字符串视为未设置 | grid_layout_property.h:64-69 |
| AC-2.1 | R-5 | TASK-GRID-01 | UT: 单模板垂直滚动 | grid_pattern.cpp:131, grid_scroll_layout_algorithm.cpp |
| AC-2.2 | R-6 | TASK-GRID-01 | UT: 单模板水平滚动 | grid_layout_property.h:72-78 |
| AC-2.3 | R-7 | TASK-GRID-01 | UT: layoutDirection 对滚动轴向无影响 | grid_pattern.cpp:256 |
| AC-2.4 | R-8 | TASK-GRID-01 | UT: ItemFillPolicy 视为列模板设置 | grid_layout_property.h:64 |
| AC-3.1 | R-9 | TASK-GRID-01 | UT: columnsTemplate reset ItemFillPolicy | grid_model_ng.cpp:129-138 |
| AC-3.2 | R-10 | TASK-GRID-01 | UT: ItemFillPolicy reset columnsTemplate | grid_model_ng.cpp:140-144 |
| AC-3.3 | R-9, R-10 | TASK-GRID-01 | UT: 互斥顺序测试 | grid_model_ng.cpp:129-144 |
| AC-3.4 | R-11 | TASK-GRID-01 | UT: ItemFillPolicy 断点映射 | grid_utils_modifier.h |
| AC-4.1 | R-12 | TASK-GRID-01 | UT: gap 从可用空间扣除 | templates_parser.cpp:370-371 |
| AC-4.2 | R-13 | TASK-GRID-01 | UT: gap clamp 到 0 | templates_parser.cpp:370-371 |
| AC-4.3 | R-14 | TASK-GRID-01 | UT: DEFAULT 对齐=居中 | grid_layout_algorithm.cpp:23-30 |
| AC-4.4 | R-15 | TASK-GRID-01 | UT: STRETCH 填满主轴 | grid_layout_base_algorithm.cpp:140-189 |
| AC-4.5 | R-16 | TASK-GRID-01 | UT: STRETCH 跳过有 selfIdealSize 的子项 | grid_layout_base_algorithm.cpp:174-176 |
| AC-5.1 | R-17 | TASK-GRID-01 | UT: cachedCount×crossCount | grid_scroll_layout_algorithm.h:204-207 |
| AC-5.2 | R-18 | TASK-GRID-01 | UT: show 参数控制缓存项可见性 | grid_scroll_layout_algorithm.cpp:2445-2469 |
| AC-5.3 | R-19 | TASK-GRID-01 | UT: syncLoad=false 分帧加载 | grid_scroll_layout_algorithm.cpp:807-810 |
| AC-5.4 | R-20 | TASK-GRID-01 | UT: syncLoad=true 一次性加载 | grid_scroll_layout_algorithm.cpp:74-75 |
| AC-5.5 | R-21 | TASK-GRID-01 | UT: 滚动时强制 syncLoad=true | grid_scroll_layout_algorithm.cpp:74-75 |
| AC-6.1 | R-22 | TASK-GRID-01 | UT: irregularIndexes → GridIrregularLayoutAlgorithm | grid_layout_property.cpp:138-161 |
| AC-6.2 | R-23 | TASK-GRID-01 | UT: onGetStartIndexByOffset+onGetStartIndexByIndex → userDefined | grid_layout_property.cpp:144-145 |
| AC-6.3 | R-24 | TASK-GRID-01 | UT: regularSize-only → GridScrollWithOptionsLayoutAlgorithm | grid_pattern.cpp:96-99 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | columnsTemplate 和 rowsTemplate 同时有值 | 实例化 GridLayoutAlgorithm | 空字符串视为未设置 | AC-1.1 |
| R-2 | 行为 | 双模板设置 | IsConfiguredScrollable()=false, 滚动条 OFF |  | AC-1.2 |
| R-3 | 边界 | 双模板模式子项数量 > rows×columns 格子数 | 多余子项溢出，不自动增加行 | 子项索引超出 gridCells_ 范围 | AC-1.3 |
| R-4 | 边界 | columnsTemplate="" (空字符串) | 等效于未设置列模板 | propColumnsTemplate_.value().empty() → columnsTemplateValid=false | AC-1.4 |
| R-5 | 行为 | 仅 columnsTemplate 有值 | 实例化滚动算法，轴=VERTICAL |  | AC-2.1 |
| R-6 | 行为 | 仅 rowsTemplate 有值 | 轴=HORIZONTAL，水平滚动 |  | AC-2.2 |
| R-7 | 边界 | 单模板模式 + layoutDirection=Column | layoutDirection 不改变轴向，轴仍=VERTICAL | 滚动模式下轴由模板决定 | AC-2.3 |
| R-8 | 行为 | 仅 ItemFillPolicy 有值 | IsVertical()=true（视为列模板设置） | propItemFillPolicy_.has_value() → columnsTemplateValid=true | AC-2.4 |
| R-9 | 行为 | 设置 columnsTemplate(string) | ItemFillPolicy 被 reset | ACE_RESET_LAYOUT_PROPERTY(ItemFillPolicy) | AC-3.1 |
| R-10 | 行为 | 设置 ItemFillPolicy(PresetFillType) | columnsTemplate 被 reset | ACE_RESET_LAYOUT_PROPERTY(ColumnsTemplate) | AC-3.2 |
| R-11 | 行为 | ItemFillPolicy=SM1MD2LG3 且屏幕匹配断点 | 自动生成对应列数模板 | SM→1列, MD→2列, LG→3列 | AC-3.4 |
| R-12 | 行为 | columnsGap=N vp, rowsGap=M vp | 从可用空间扣除 (cols-1)×N + (rows-1)×M 后分配给格子 | gap 在可用空间不足时被 clamp 到 0 | AC-4.1 |
| R-13 | 边界 | (N-1)×gap > 总可用空间 | gap 被设为 0.0 | templates_parser.cpp:370-371 | AC-4.2 |
| R-14 | 行为 | alignItems=DEFAULT, 子项尺寸 < 格子尺寸 | 子项居中对齐（OffsetByAlign 计算偏移） | 固定网格用 Center；滚动网格用 TOP_CENTER/CENTER_LEFT | AC-4.3 |
| R-15 | 行为 | alignItems=STRETCH, 子项无 selfIdealSize.MainSize | 子项 mainSize 被拉伸至行高/列宽 | AdjustChildrenHeight() 第二遍测量 | AC-4.4 |
| R-16 | 边界 | alignItems=STRETCH, 子项 selfIdealSize.MainSize 有值 | 子项保持 selfIdealSize，不拉伸 | GreatOrEqual(childFrameSize.MainSize, lineHeight) 时也跳过 | AC-4.5 |
| R-17 | 行为 | cachedCount=N | 在可见区域前后各缓存 N×crossCount 个子项 | N=0 → 仅渲染可见项；默认值由 UpdateDefaultCachedCount 自动调整（最大16） | AC-5.1 |
| R-18 | 行为 | cachedCount(N, show=true) | 缓存项同步预加载并可见渲染 | SyncPreload() 方法 | AC-5.2 |
| R-19 | 行为 | syncLoad=false 且 frame deadline 到达 | 未测量子项延迟到下一帧（measureInNextFrame_=true） | 仅在非滚动/非 scrollToIndex 场景生效 | AC-5.3 |
| R-20 | 行为 | syncLoad=true | 所有子项在当前帧内完成测量 | 默认值=true | AC-5.4 |
| R-21 | 边界 | syncLoad=false 但滚动偏移变化 | syncLoad 临时强制为 true | info_.currentOffset_ != info_.prevOffset_ | AC-5.5 |
| R-22 | 行为 | GridLayoutOptions.irregularIndexes 中某项 crossSpan >1 | irregular_=true, 实例化 GridIrregularLayoutAlgorithm | UpdateIrregularFlag() 检查 getSizeByIndex 返回值 | AC-6.1 |
| R-23 | 边界 | GridLayoutOptions 同时含 getStartIndexByIndex 和 getStartIndexByOffset | userDefined_=true, 实例化 GridCustomLayoutAlgorithm | 两个回调都存在才触发 | AC-6.2 |
| R-24 | 行为 | GridLayoutOptions 仅含 regularSize（无 irregular/自定义回调） | 实例化 GridScrollWithOptionsLayoutAlgorithm | HasLayoutOptions()=true, userDefined_=false, irregular_=false | AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | 算法分发机制 | UT: CreateLayoutAlgorithm 各分支 | 6种算法实例化条件覆盖 |
| VM-2 | 双模板静态网格 | UT: GridLayoutAlgorithm::Measure | 所有子项可见，不可滚动 |
| VM-3 | 单模板滚动网格 | UT: GridScrollLayoutAlgorithm | 轴向由模板决定 |
| VM-4 | ItemFillPolicy 互斥 | UT: GridModelNG::SetColumnsTemplate/SetItemFillPolicy | reset 顺序验证 |
| VM-5 | 间距计算 | UT: ParseArgsWithoutAutoFill | gap 扣除和 clamp |
| VM-6 | 对齐行为 | UT: OffsetByAlign + AdjustChildrenHeight | DEFAULT=居中, STRETCH=拉伸 |
| VM-7 | cachedCount 缓存范围 | UT: CalculateCachedCount | count×crossCount |
| VM-8 | syncLoad 分帧 | UT: syncLoad_ 条件判定 | frame deadline 强制 true |

## API 变更分析

### 新增 API

> 本规格为存量补录，以下 API 已在 SDK 中存在。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| Grid(scroller?, layoutOptions?) | Public | Scroller, GridLayoutOptions | GridAttribute | 无 | Grid 构造器 | AC-1.1, AC-2.1 |
| columnsTemplate(string) | Public | string | GridAttribute | 无 | 列模板字符串 | AC-1.1 |
| columnsTemplate(string\|ItemFillPolicy) | Public | string\|ItemFillPolicy | GridAttribute | 无 | 列模板或响应式填充 (@since 22) | AC-3.1 |
| rowsTemplate(string) | Public | string | GridAttribute | 无 | 行模板字符串 | AC-1.1 |
| columnsGap(Length) | Public | Length | GridAttribute | 无 | 列间距 | AC-4.1 |
| rowsGap(Length) | Public | Length | GridAttribute | 无 | 行间距 | AC-4.1 |
| cachedCount(number) | Public | number | GridAttribute | 无 | 缓存预加载行数 | AC-5.1 |
| cachedCount(number, boolean) | Public | number, boolean | GridAttribute | 无 | 缓存数量+可见标志 (@since 14) | AC-5.2 |
| layoutDirection(GridDirection) | Public | GridDirection | GridAttribute | 无 | 布局方向 (@since 8) | AC-2.3 |
| alignItems(GridItemAlignment) | Public | GridItemAlignment | GridAttribute | 无 | 对齐方式 (@since 12) | AC-4.3 |
| syncLoad(boolean) | Public | boolean | GridAttribute | 无 | 同步加载 (@since 20) | AC-5.3 |
| GridLayoutOptions | Public | regularSize, irregularIndexes?, onGetIrregularSizeByIndex?, onGetRectByIndex? | — | 无 | 不规则网格配置 (@since 10) | AC-6.1 |

### 变更/废弃 API

无新增变更或废弃。columnsTemplate(string\|ItemFillPolicy) 是 @since 22 新增 overload，不影响原有 string 版本。

## 接口规格

### 接口定义

**Grid 构造器**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Grid(scroller?: Scroller, layoutOptions?: GridLayoutOptions): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| scroller | Scroller | 否 | undefined | 绑定滚动控制器 |
| layoutOptions | GridLayoutOptions | 否 | undefined | 仅在单模板模式生效；双模板模式下 layoutOptions 被忽略 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | scroller+layoutOptions 同时传入 | layoutOptions 传递给 GridLayoutProperty | AC-6.1 |
| 2 | layoutOptions 无 irregularIndexes | 实例化 GridScrollWithOptionsLayoutAlgorithm | AC-6.3 |

---

**columnsTemplate**

| 属性 | 值 |
|------|-----|
| 函数签名 | `columnsTemplate(value: string): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 7) |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | "1fr"（空字符串时） | 支持 fr/px/%/auto/repeat(auto-fill/auto-fit/auto-stretch) 语法；空字符串视为未设置；设置时自动 reset ItemFillPolicy |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value="1fr 1fr 1fr" | 解析为3列等宽分配 | AC-1.1 |
| 2 | value="" (空) | 存储为 "1fr" 默认值；columnsTemplateValid 取决于是否非空 | AC-1.4 |
| 3 | 先设 ItemFillPolicy 再设 columnsTemplate | columnsTemplate 生效，ItemFillPolicy 被 reset | AC-3.1 |

---

**columnsTemplate(string \| ItemFillPolicy)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `columnsTemplate(value: string \| ItemFillPolicy): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string \| ItemFillPolicy | 是 | — | string 时同上；ItemFillPolicy 时自动 reset columnsTemplate |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | ItemFillPolicy={fillType: SM1MD2LG3} | 根据断点自动生成列数 | AC-3.4 |
| 2 | 先设 columnsTemplate(string) 再设 ItemFillPolicy | ItemFillPolicy 生效，columnsTemplate(string) 被 reset | AC-3.2 |

---

**rowsTemplate**

| 属性 | 值 |
|------|-----|
| 函数签名 | `rowsTemplate(value: string): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 7) |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | — | 同 columnsTemplate 语法 |

---

**columnsGap / rowsGap**

| 属性 | 值 |
|------|-----|
| 函数签名 | `columnsGap(value: Length): GridAttribute` / `rowsGap(value: Length): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 7) |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | Length | 是 | 0_vp | 非负；超出可用空间时被 clamp 到 0 |

---

**layoutDirection**

| 属性 | 值 |
|------|-----|
| 函数签名 | `layoutDirection(value: GridDirection): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | GridDirection (Row/Column/RowReverse/ColumnReverse) | 是 | Row | 仅在自适应模式（无模板）下影响轴向；滚动模式下由模板决定轴向 |

---

**cachedCount**

| 属性 | 值 |
|------|-----|
| 函数签名 | `cachedCount(value: number): GridAttribute` / `cachedCount(count: number, show: boolean): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 7, show @since 14) |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value / count | number | 是 | 自动(最大16) | 非负整数；内部乘以 crossCount |
| show | boolean | 否 | false | 缓存项是否可见渲染 |

---

**syncLoad**

| 属性 | 值 |
|------|-----|
| 函数签名 | `syncLoad(enable: boolean): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enable | boolean | 是 | true | 滚动时临时强制为 true |

---

**alignItems**

| 属性 | 值 |
|------|-----|
| 函数签名 | `alignItems(alignment: GridItemAlignment): GridAttribute` |
| 返回值 | `GridAttribute` |
| 开放范围 | Public (@since 12) |
| 错误码 | N/A |
| 关联 AC | AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| alignment | GridItemAlignment | 是 | DEFAULT | DEFAULT=居中；STRETCH=填满格子（跳过有 selfIdealSize 的子项） |

## 兼容性声明

- **已有 API 行为变更:** 否。columnsTemplate(string\|ItemFillPolicy) 是新增 overload(@since 22)，不影响原 string 版本。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** @since 标注按各 API 最早引入版本；新增 overload 标注引入版本

- **SDK vs 源码偏差风险:**
  - C-API GridLayoutOptions hardcodes regularSize=[1,1]（grid_model_ng.cpp:958-959），SDK 允许用户指定 regularSize — 此偏差需在兼容性表标注
  - C-API 缺少 onGetStartIndexByOffset/onGetStartIndexByIndex 回调（@systemapi），SDK 有此功能 — C-API 未实现

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| columnsTemplate/ItemFillPolicy 互斥 | 设置一个自动 reset 另一个（grid_model_ng.cpp:129-144） | AC-3.1, AC-3.2 |
| 滚动模式轴由模板决定 | layoutDirection 不改变滚动轴向 | AC-2.3 |
| cachedCount 内部乘法 | 用户指定行数×crossCount=实际缓存项数 | AC-5.1 |
| gap clamp | gap 超出可用空间时被设为 0 | AC-4.2 |
| DEFAULT=居中 | 不是"不处理"，而是居中对齐 | AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 双模板网格布局 <16ms | 帧时间采集 | Trace 打点 |
| 性能 | 单模板滚动帧率 ≥55fps | Perf 组网测试 | Jank 检测 |
| 内存 | cachedCount 缓存项数量受控（≤16×crossCount） | Dump 机制 | GridPattern::UpdateDefaultCachedCount |
| 可测试性 | CreateLayoutAlgorithm 各分支可独立 UT | Mock GridLayoutProperty | grid_pattern.cpp:111-149 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | ItemFillPolicy 断点阈值不同 | SM/MD/LG 断点宽度不同 | 断点配置测试 | — |
| 折叠屏 | 折叠态变化触发 ItemFillPolicy 重新计算 | 折叠状态回调 | 折叠适配测试 | — |
| 穿戴 | digitalCrownSensitivity（滚动模式继承 ScrollableCommonMethod） | API 18+ | 穿戴专项测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | GridItem 语义节点含 rowStart/columnStart 等位置信息 | 辅助技术读取网格位置 |
| 大字体 | 是 | STRETCH 模式下大字体导致行高增加，子项自动拉伸 | 大字体适配 |
| 深色模式 | 否 | Grid 无颜色属性，深色模式由子项决定 | — |
| 多窗口/分屏 | 是 | ItemFillPolicy 响应式列数在分屏时自动调整 | 分屏重布局 |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | columnsTemplate(string\|ItemFillPolicy) @since 22 新增 overload | 低版本设备不支持 ItemFillPolicy |
| 生态兼容 | 否 | — | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Grid 布局算法分发
  作为 ArkUI 开发者
  我想要根据模板和选项配置选择正确的布局算法
  以便网格呈现预期的布局行为

  Scenario: 双模板 → 固定网格
    Given columnsTemplate="1fr 1fr 1fr"
    And rowsTemplate="1fr 1fr"
    When Grid 执行 CreateLayoutAlgorithm()
    Then 实例化 GridLayoutAlgorithm
    And IsConfiguredScrollable() = false
    And 滚动条状态 = OFF

  Scenario: 单模板 → 滚动网格
    Given columnsTemplate="1fr 1fr"
    And rowsTemplate 未设置
    When Grid 执行 CreateLayoutAlgorithm()
    Then 实例化 GridScrollLayoutAlgorithm
    And 轴向 = VERTICAL

  Scenario: columnsTemplate 与 ItemFillPolicy 互斥
    Given ItemFillPolicy 已设置为 SM1MD2LG3
    When 开发者调用 columnsTemplate("1fr 1fr 1fr")
    Then ItemFillPolicy 被 reset 为空
    And columnsTemplate="1fr 1fr 1fr" 生效

  Scenario Outline: 间距计算
    Given columnsTemplate="<template>"
    And columnsGap=<gap>vp
    And Grid 宽度=<width>vp
    When ParseArgsWithoutAutoFill 执行解析
    Then 每列宽度 = (<width> - (<cols>-1)×<gap>) / <cols>

    Examples:
      | template | gap | width | cols |
      | "1fr 1fr 1fr" | 10 | 300 | 3 |
      | "1fr 1fr" | 0 | 200 | 2 |
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
    query: "columnsTemplate/ItemFillPolicy 互斥逻辑 (grid_model_ng.cpp)"
  - repo: "openharmony/ace_engine"
    query: "Grid 模板字符串解析 (templates_parser.cpp ParseArgsWithoutAutoFill)"
  - repo: "openharmony/ace_engine"
    query: "Grid alignItems DEFAULT=居中, STRETCH=填满 (grid_layout_base_algorithm.cpp AdjustChildrenHeight)"
```

**关键文档：**
- SDK 动态 API: `interface/sdk-js/api/@internal/component/ets/grid.d.ts`
- SDK 静态 API: `interface/sdk-js/api/arkui/component/grid.static.d.ets`
- C-API: `interfaces/native/native_node.h` (NODE_GRID_COLUMN_TEMPLATE 等)
- 源码入口: `frameworks/core/components_ng/pattern/grid/`
