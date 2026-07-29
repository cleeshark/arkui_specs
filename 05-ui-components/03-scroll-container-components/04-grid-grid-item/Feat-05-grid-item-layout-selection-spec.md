# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | GridItem 布局与选择 |
| 特性编号 | Func-05-03-04-Feat-05 |
| 所属 Epic | Grid/GridItem 组件规格补录 |
| 优先级 | P0 |
| 目标版本 | API 7–22 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 存量特性补录（lineage: new-on-legacy），本规格补录已有实现的行为。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | GridItem 构造器与 GridItemOptions | @since 7 无参构造，@since 11 带 GridItemOptions 参数 |
| ADDED | GridItemStyle 枚举（NONE/PLAIN） | NONE=无圆角无动画，PLAIN=主题圆角+悬停/按压动画 |
| ADDED | rowStart/rowEnd/columnStart/columnEnd 跨行跨列属性 | @since 7，定义 GridItem 在网格中的起止位置 |
| ADDED | selectable/selected/onSelect 选择能力 | @since 8 selectable，@since 10 selected 双向绑定，@since 8 onSelect 回调 |
| ADDED | forceRebuild 属性 | @since 7，@since 9 已废弃 |
| ADDED | UpdateGridItemStyle() 运行时样式切换 | 动态修改 GridItemStyle |
| ADDED | 跨行跨列属性变更触发 ResetGridLayoutInfoAndMeasure | 父 Grid 重新布局 |

## 输入文档

- 需求基线：已有能力补录（无独立 requirement.md）
- 设计文档：`05-ui-components/03-scroll-container-components/04-grid-grid-item/design.md`
- 源码定位：`frameworks/core/components_ng/pattern/grid/grid_item_pattern.h/cpp`、`grid_item_layout_property.h`、`grid_item_model.h`、`grid_item_model_ng.h`

## 用户故事

### US-1: 开发者使用 GridItem 构造器指定样式

作为 ArkUI 开发者，我想要通过 GridItem 构造器传入 GridItemStyle，以便控制 GridItem 的外观风格（无边框无动画 vs 主题圆角+交互动画）。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN GridItem() 无参构造 THEN GridItemStyle 默认为 NONE | 正常 |
| AC-1.2 | WHEN GridItem({style: GridItemStyle.PLAIN}) THEN GridItemStyle=PLAIN，渲染主题圆角、悬停混色动画、按压混色动画 | 正常 |
| AC-1.3 | WHEN GridItem({style: GridItemStyle.NONE}) THEN 无圆角、无悬停/按压动画 | 正常 |
| AC-1.4 | WHEN 运行时调用 UpdateGridItemStyle(GridItemStyle.PLAIN) THEN GridItemStyle 从 NONE 切换为 PLAIN，后续渲染生效 | 正常 |

### US-2: 开发者使用跨行跨列属性定义 GridItem 位置

作为 ArkUI 开发者，我想要通过 rowStart/rowEnd/columnStart/columnEnd 定义 GridItem 在网格中的跨行跨列位置，以便实现不规则网格布局。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN rowStart=0, rowEnd=1, columnStart=0, columnEnd=2 THEN GridItem 跨越第0-1行、第0-2列（2行×3列），行跨度=1-0+1=2，列跨度=2-0+1=3 | 正常 |
| AC-2.2 | WHEN rowEnd < rowStart THEN 行跨度被 clamp 为最小值 1 | 边界 |
| AC-2.3 | WHEN columnEnd < columnStart THEN 列跨度被 clamp 为最小值 1 | 边界 |
| AC-2.4 | WHEN 修改任一跨行跨列属性 THEN 触发父 Grid 的 ResetGridLayoutInfoAndMeasure()，重新计算布局 | 正常 |
| AC-2.5 | WHEN 双模板静态网格模式下设置跨行跨列 THEN GridItem 精确定位到指定行列范围 | 正常 |
| AC-2.6 | WHEN 单模板滚动网格模式下设置跨行跨列 THEN 跨列属性影响列放置，跨行属性影响行归属 | 正常 |
| AC-2.7 | WHEN rowStart/rowEnd/columnStart/columnEnd 均未设置 THEN GridItem 按默认顺序流式排列 | 正常 |

### US-3: 开发者使用选择能力

作为 ArkUI 开发者，我想要通过 selectable/selected/onSelect 控制 GridItem 的选择状态，以便实现多选或单选网格场景。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN selectable=true THEN GridItem 可被点击选中，触发 onSelect(isSelected=true) | 正常 |
| AC-3.2 | WHEN selectable=false THEN GridItem 不可被点击选中，当前已选中状态被取消 | 正常 |
| AC-3.3 | WHEN selected=true（初始值） THEN GridItem 初始渲染为选中态 | 正常 |
| AC-3.4 | WHEN selected 支持 $$ 双向绑定 THEN 用户点击选中后绑定变量自动更新为 true，代码修改变量后 GridItem 选中状态同步更新 | 正常 |
| AC-3.5 | WHEN onSelect 回调触发 THEN 回调参数 isSelected 反映当前选中状态 | 正常 |
| AC-3.6 | WHEN SetSelectable(false) 且 GridItem 当前为选中态 THEN 选中态被取消，MarkIsSelected(false) 触发 FireSelectChangeEvent | 边界 |
| AC-3.7 | WHEN MarkIsSelected 被调用 THEN FireSelectChangeEvent 同时触发 selectChangeEvent_ 和 onSelect_ | 正常 |

### US-4: 开发者使用 forceRebuild 属性

作为 ArkUI 开发者，我想要了解 forceRebuild 属性的废弃行为，以便在迁移代码时避免使用。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN forceRebuild=true THEN 该属性自 API 9 起废弃，不再产生实际效果 | 边界 |
| AC-4.2 | WHEN forceRebuild=false THEN 该属性自 API 9 起废弃，不再产生实际效果 | 边界 |

### US-5: 开发者使用 GridItemStyle NONE 和 PLAIN 的交互差异

作为 ArkUI 开发者，我想要了解 NONE 和 PLAIN 两种样式在交互行为上的差异，以便选择合适的样式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN GridItemStyle=NONE 且鼠标悬停 THEN 无悬停动画效果 | 正常 |
| AC-5.2 | WHEN GridItemStyle=PLAIN 且鼠标悬停 THEN 悬停混色动画（hover blend animation） | 正常 |
| AC-5.3 | WHEN GridItemStyle=NONE 且鼠标按下 THEN 无按压动画效果 | 正常 |
| AC-5.4 | WHEN GridItemStyle=PLAIN 且鼠标按下 THEN 按压混色动画（press blend animation） | 正常 |
| AC-5.5 | WHEN GridItemStyle=PLAIN THEN 渲染主题圆角（borderRadius 取主题值） | 正常 |
| AC-5.6 | WHEN GridItemStyle=NONE THEN 无圆角（borderRadius=0） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-GRIDITEM-05 | UT: GridItem 无参构造默认 style=NONE | grid_item_model_ng.cpp |
| AC-1.2 | R-2 | TASK-GRIDITEM-05 | UT: GridItemOptions style=PLAIN 渲染圆角和动画 | grid_item_pattern.cpp |
| AC-1.3 | R-3 | TASK-GRIDITEM-05 | UT: GridItemStyle=NONE 无圆角无动画 | grid_item_pattern.cpp |
| AC-1.4 | R-4 | TASK-GRIDITEM-05 | UT: UpdateGridItemStyle 运行时切换 | grid_item_pattern.cpp UpdateGridItemStyle |
| AC-2.1 | R-5 | TASK-GRIDITEM-05 | UT: rowStart/rowEnd/columnStart/columnEnd 跨行跨列计算 | grid_item_layout_property.h |
| AC-2.2 | R-6 | TASK-GRIDITEM-05 | UT: rowEnd < rowStart 时跨度 clamp=1 | grid_item_layout_property.h |
| AC-2.3 | R-7 | TASK-GRIDITEM-05 | UT: columnEnd < columnStart 时跨度 clamp=1 | grid_item_layout_property.h |
| AC-2.4 | R-8 | TASK-GRIDITEM-05 | UT: 修改跨行跨列触发 ResetGridLayoutInfoAndMeasure | grid_item_layout_property.h |
| AC-2.5 | R-9 | TASK-GRIDITEM-05 | UT: 双模板静态网格跨行跨列定位 | grid_layout_algorithm.cpp |
| AC-2.6 | R-10 | TASK-GRIDITEM-05 | UT: 单模板滚动网格跨行跨列影响列放置 | grid_scroll_layout_algorithm.cpp |
| AC-2.7 | R-11 | TASK-GRIDITEM-05 | UT: 无跨行跨列属性时流式排列 | grid_scroll_layout_algorithm.cpp |
| AC-3.1 | R-12 | TASK-GRIDITEM-05 | UT: selectable=true 点击选中 | grid_item_pattern.cpp SetSelectable |
| AC-3.2 | R-13 | TASK-GRIDITEM-05 | UT: selectable=false 取消选中 | grid_item_pattern.cpp SetSelectable |
| AC-3.3 | R-14 | TASK-GRIDITEM-05 | UT: selected=true 初始选中态 | grid_item_model_ng.cpp |
| AC-3.4 | R-15 | TASK-GRIDITEM-05 | UT: selected $$ 双向绑定 | grid_item_model_ng.cpp Bindable&lt;boolean&gt; |
| AC-3.5 | R-16 | TASK-GRIDITEM-05 | UT: onSelect 回调参数 isSelected | grid_item_pattern.cpp FireSelectChangeEvent |
| AC-3.6 | R-17 | TASK-GRIDITEM-05 | UT: SetSelectable(false) 取消已选中项 | grid_item_pattern.cpp SetSelectable |
| AC-3.7 | R-18 | TASK-GRIDITEM-05 | UT: FireSelectChangeEvent 触发 selectChangeEvent_ 和 onSelect_ | grid_item_pattern.cpp FireSelectChangeEvent |
| AC-4.1 | R-19 | TASK-GRIDITEM-05 | UT: forceRebuild=true 废弃无效果 | grid_item_model_ng.cpp |
| AC-4.2 | R-19 | TASK-GRIDITEM-05 | UT: forceRebuild=false 废弃无效果 | grid_item_model_ng.cpp |
| AC-5.1 | R-20 | TASK-GRIDITEM-05 | UT: NONE 悬停无动画 | grid_item_pattern.cpp |
| AC-5.2 | R-21 | TASK-GRIDITEM-05 | UT: PLAIN 悬停混色动画 | grid_item_pattern.cpp |
| AC-5.3 | R-22 | TASK-GRIDITEM-05 | UT: NONE 按压无动画 | grid_item_pattern.cpp |
| AC-5.4 | R-23 | TASK-GRIDITEM-05 | UT: PLAIN 按压混色动画 | grid_item_pattern.cpp |
| AC-5.5 | R-24 | TASK-GRIDITEM-05 | UT: PLAIN 主题圆角 | grid_item_pattern.cpp |
| AC-5.6 | R-25 | TASK-GRIDITEM-05 | UT: NONE 无圆角 | grid_item_pattern.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GridItem() 无参构造 | GridItemStyle 默认 NONE | style 未传入时 propGridItemStyle_ 无值，按 NONE 处理 | AC-1.1 |
| R-2 | 行为 | GridItemOptions.style=PLAIN | 渲染主题 borderRadius、hover blend、press blend | borderRadius 取主题配置值 | AC-1.2 |
| R-3 | 行为 | GridItemStyle=NONE | 无 borderRadius、无 hover/press 动画 | 默认值 | AC-1.3 |
| R-4 | 行为 | UpdateGridItemStyle() 调用 | 动态修改 GridItemStyle，后续渲染生效 | 修改后触发重新布局 | AC-1.4 |
| R-5 | 行为 | rowStart/rowEnd/columnStart/columnEnd 设置 | 跨度 = End - Start + 1，最小值为 1 | Start/End 均为 0-based 索引 | AC-2.1 |
| R-6 | 边界 | rowEnd < rowStart | 行跨度 clamp 为 1 | 跨度 = max(1, rowEnd - rowStart + 1) | AC-2.2 |
| R-7 | 边界 | columnEnd < columnStart | 列跨度 clamp 为 1 | 跨度 = max(1, columnEnd - columnStart + 1) | AC-2.3 |
| R-8 | 行为 | 修改 rowStart/rowEnd/columnStart/columnEnd 任一属性 | 触发父 Grid 的 ResetGridLayoutInfoAndMeasure() | 属性 setter 中调用 ResetGridLayoutInfoAndMeasure | AC-2.4 |
| R-9 | 行为 | 双模板静态网格 + 跨行跨列属性 | GridItem 精确定位到指定行列范围 | 静态网格中 span 由属性直接决定 | AC-2.5 |
| R-10 | 行为 | 单模板滚动网格 + 跨行跨列属性 | 跨列影响列放置，跨行影响行归属 | 滚动网格中 columnSpan 影响 crossCount 计算 | AC-2.6 |
| R-11 | 行为 | 无跨行跨列属性 | GridItem 按默认顺序流式排列 | span 默认为 1×1 | AC-2.7 |
| R-12 | 行为 | selectable=true 且用户点击 GridItem | GridItem 进入选中态，触发 onSelect(isSelected=true) | 依赖 SelectableItemPattern 选中逻辑 | AC-3.1 |
| R-13 | 行为 | selectable=false | GridItem 不可被选中；若当前已选中则取消选中态 | SetSelectable(false) 调用 MarkIsSelected(false) | AC-3.2 |
| R-14 | 行为 | selected=true 初始值 | GridItem 初始渲染为选中态 | 通过 Bindable&lt;boolean&gt; 传入初始值 | AC-3.3 |
| R-15 | 行为 | selected 支持 $$ 双向绑定 | 用户交互修改选中状态 → 绑定变量自动更新；代码修改变量 → 选中状态同步更新 | Bindable&lt;boolean&gt; 机制 | AC-3.4 |
| R-16 | 行为 | onSelect 回调触发 | 回调参数 isSelected 反映当前选中状态 | isSelected=true 表示选中，false 表示取消选中 | AC-3.5 |
| R-17 | 边界 | SetSelectable(false) 且当前为选中态 | MarkIsSelected(false) 被调用，FireSelectChangeEvent 触发 | 取消选中同时触发事件 | AC-3.6 |
| R-18 | 行为 | MarkIsSelected 被调用 | FireSelectChangeEvent 同时触发 selectChangeEvent_ 和 onSelect_ | 两个回调独立触发 | AC-3.7 |
| R-19 | 废弃 | forceRebuild=true/false | API 9 起废弃，不再产生实际效果 | 保留属性定义但不影响行为 | AC-4.1, AC-4.2 |
| R-20 | 行为 | GridItemStyle=NONE + 鼠标悬停 | 无悬停动画 | 不注册 hover 回调 | AC-5.1 |
| R-21 | 行为 | GridItemStyle=PLAIN + 鼠标悬停 | 悬停混色动画（hover blend animation） | 动画由主题配置驱动 | AC-5.2 |
| R-22 | 行为 | GridItemStyle=NONE + 鼠标按下 | 无按压动画 | 不注册 press 回调 | AC-5.3 |
| R-23 | 行为 | GridItemStyle=PLAIN + 鼠标按下 | 按压混色动画（press blend animation） | 动画由主题配置驱动 | AC-5.4 |
| R-24 | 行为 | GridItemStyle=PLAIN | 渲染主题 borderRadius | borderRadius 取主题值 | AC-5.5 |
| R-25 | 行为 | GridItemStyle=NONE | 无 borderRadius（borderRadius=0） | 默认行为 | AC-5.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | GridItem 构造器与 GridItemStyle | UT: GridItemModelNG 构造分支 | NONE/PLAIN 默认值和显式设置 |
| VM-2 | UpdateGridItemStyle 运行时切换 | UT: GridItemPattern::UpdateGridItemStyle | 动态修改后重新渲染 |
| VM-3 | rowStart/rowEnd/columnStart/columnEnd 跨度计算 | UT: GridItemLayoutProperty span 计算 | 跨度 = End-Start+1，clamp 最小 1 |
| VM-4 | 跨行跨列触发 ResetGridLayoutInfoAndMeasure | UT: 属性 setter 调用链 | 修改任一属性触发父 Grid 重布局 |
| VM-5 | selectable/selected 选择能力 | UT: GridItemPattern::SetSelectable/MarkIsSelected | 选中态切换和事件触发 |
| VM-6 | selected $$ 双向绑定 | UT: Bindable&lt;boolean&gt; 机制 | 交互→变量更新，变量→状态同步 |
| VM-7 | onSelect 回调 | UT: FireSelectChangeEvent | selectChangeEvent_ 和 onSelect_ 均触发 |
| VM-8 | GridItemStyle NONE/PLAIN 交互差异 | UT: hover/press 动画分支 | NONE 无动画，PLAIN 有动画 |
| VM-9 | forceRebuild 废弃行为 | UT: forceRebuild 属性无实际效果 | API 9+ 废弃验证 |

## API 变更分析

### 新增 API

> 本规格为存量补录，以下 API 已在 SDK 中存在。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| GridItem(value?: GridItemOptions) | Public | GridItemOptions? | GridItemAttribute | 无 | GridItem 构造器 (@since 7 无参, @since 11 带参) | AC-1.1, AC-1.2 |
| GridItemOptions | Public | {style?: GridItemStyle} | — | 无 | GridItem 构造参数 (@since 11) | AC-1.2 |
| GridItemStyle | Public | NONE=0, PLAIN=1 | — | 无 | GridItem 样式枚举 (@since 11) | AC-1.2, AC-1.3 |
| rowStart(value: number) | Public | number | GridItemAttribute | 无 | 起始行号 (@since 7) | AC-2.1 |
| rowEnd(value: number) | Public | number | GridItemAttribute | 无 | 结束行号 (@since 7) | AC-2.1 |
| columnStart(value: number) | Public | number | GridItemAttribute | 无 | 起始列号 (@since 7) | AC-2.1 |
| columnEnd(value: number) | Public | number | GridItemAttribute | 无 | 结束列号 (@since 7) | AC-2.1 |
| forceRebuild(value: boolean) | Public | boolean | GridItemAttribute | 无 | 强制重建 (@since 7, DEPRECATED since 9) | AC-4.1 |
| selectable(value: boolean) | Public | boolean | GridItemAttribute | 无 | 是否可选中 (@since 8) | AC-3.1 |
| selected(value: boolean) | Public | boolean | GridItemAttribute | 无 | 选中状态，支持 $$ 双向绑定 (@since 10) | AC-3.3, AC-3.4 |
| onSelect(callback: (isSelected: boolean) => void) | Public | callback | GridItemAttribute | 无 | 选中状态变更回调 (@since 8) | AC-3.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 说明 | 关联 AC |
|----------|----------|------|---------|
| forceRebuild(boolean) | 废弃 | @since 9 起废弃，不再产生实际效果 | AC-4.1, AC-4.2 |

## 接口规格

### 接口定义

**GridItem 构造器**

| 属性 | 值 |
|------|-----|
| 函数签名 | `GridItem(value?: GridItemOptions): GridItemAttribute` |
| 返回值 | `GridItemAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | GridItemOptions | 否 | undefined | @since 11；未传入时 GridItemStyle 默认 NONE |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | GridItem() 无参构造 | GridItemStyle=NONE | AC-1.1 |
| 2 | GridItem({style: GridItemStyle.PLAIN}) | GridItemStyle=PLAIN，渲染圆角和交互动画 | AC-1.2 |
| 3 | GridItem({style: GridItemStyle.NONE}) | GridItemStyle=NONE，无圆角无动画 | AC-1.3 |

---

**GridItemOptions**

| 属性 | 值 |
|------|-----|
| 类型 | `interface GridItemOptions` |
| 开放范围 | Public (@since 11) |
| 关联 AC | AC-1.2 |

**属性约束**

| 属性 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| style | GridItemStyle | 否 | NONE | NONE=0, PLAIN=1 |

---

**GridItemStyle**

| 属性 | 值 |
|------|-----|
| 类型 | `enum GridItemStyle` |
| 开放范围 | Public (@since 11) |
| 关联 AC | AC-1.2, AC-1.3 |

**枚举值**

| 枚举值 | 数值 | 说明 |
|--------|------|------|
| NONE | 0 | 无圆角，无悬停/按压动画 |
| PLAIN | 1 | 主题圆角，悬停混色动画，按压混色动画 |

---

**rowStart**

| 属性 | 值 |
|------|-----|
| 函数签名 | `rowStart(value: number): GridItemAttribute` |
| 返回值 | `GridItemAttribute` |
| 开放范围 | Public (@since 7) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | — | 0-based 行索引；与 rowEnd 配合计算行跨度；修改触发 ResetGridLayoutInfoAndMeasure |

---

**rowEnd**

| 属性 | 值 |
|------|-----|
| 函数签名 | `rowEnd(value: number): GridItemAttribute` |
| 返回值 | `GridItemAttribute` |
| 开放范围 | Public (@since 7) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | — | 0-based 行索引；行跨度 = rowEnd - rowStart + 1（最小 1）；修改触发 ResetGridLayoutInfoAndMeasure |

---

**columnStart**

| 属性 | 值 |
|------|-----|
| 函数签名 | `columnStart(value: number): GridItemAttribute` |
| 返回值 | `GridItemAttribute` |
| 开放范围 | Public (@since 7) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | — | 0-based 列索引；与 columnEnd 配合计算列跨度；修改触发 ResetGridLayoutInfoAndMeasure |

---

**columnEnd**

| 属性 | 值 |
|------|-----|
| 函数签名 | `columnEnd(value: number): GridItemAttribute` |
| 返回值 | `GridItemAttribute` |
| 开放范围 | Public (@since 7) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | — | 0-based 列索引；列跨度 = columnEnd - columnStart + 1（最小 1）；修改触发 ResetGridLayoutInfoAndMeasure |

---

**forceRebuild**

| 属性 | 值 |
|------|-----|
| 函数签名 | `forceRebuild(value: boolean): GridItemAttribute` |
| 返回值 | `GridItemAttribute` |
| 开放范围 | Public (@since 7, DEPRECATED since 9) |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | — | 自 API 9 起废弃，不再产生实际效果 |

---

**selectable**

| 属性 | 值 |
|------|-----|
| 函数签名 | `selectable(value: boolean): GridItemAttribute` |
| 返回值 | `GridItemAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | false | true=可选中；false=不可选中，若当前已选中则取消选中态 |

---

**selected**

| 属性 | 值 |
|------|-----|
| 函数签名 | `selected(value: boolean): GridItemAttribute` |
| 返回值 | `GridItemAttribute` |
| 开放范围 | Public (@since 10) |
| 错误码 | N/A |
| 关联 AC | AC-3.3, AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | false | 支持 $$ 双向绑定（Bindable&lt;boolean&gt;）；true=选中态，false=未选中态 |

---

**onSelect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onSelect(callback: (isSelected: boolean) => void): GridItemAttribute` |
| 返回值 | `GridItemAttribute` |
| 开放范围 | Public (@since 8) |
| 错误码 | N/A |
| 关联 AC | AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | (isSelected: boolean) => void | 是 | — | isSelected=true 表示选中，false 表示取消选中；FireSelectChangeEvent 同时触发 selectChangeEvent_ 和 onSelect_ |

## 兼容性声明

- **已有 API 行为变更:** 否。所有 API 行为为存量补录，无新增行为变更。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** @since 标注按各 API 最早引入版本；forceRebuild 自 API 9 起废弃

- **SDK vs 源码偏差风险:**
  - GridItemOptions 和 GridItemStyle 枚举 @since 11 引入，但构造器 @since 7 已存在无参版本 — 旧版本代码无需修改
  - forceRebuild 在 SDK 中仍保留声明但标记 @deprecated，源码中不再产生实际效果
  - selected @since 10 支持 $$ 双向绑定，@since 8–9 仅支持单向设置

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| GridItemPattern 继承 SelectableItemPattern | 选择能力由 SelectableItemPattern 提供，MarkIsSelected/FireSelectChangeEvent 在基类中 | AC-3.1–AC-3.7 |
| 跨行跨列属性触发 ResetGridLayoutInfoAndMeasure | setter 中调用 ResetGridLayoutInfoAndMeasure，父 Grid 重新布局 | AC-2.4 |
| 跨度计算 clamp 最小值 1 | 跨度 = max(1, End - Start + 1)，防止非法跨度 | AC-2.2, AC-2.3 |
| GridItemStyle 影响 hover/press 动画注册 | NONE 不注册动画回调，PLAIN 注册 hover blend 和 press blend | AC-5.1–AC-5.6 |
| selected 双向绑定依赖 Bindable&lt;boolean&gt; | @since 10 支持 $$，@since 8–9 仅单向 | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 跨行跨列属性变更触发重布局 <16ms | 帧时间采集 | Trace 打点 |
| 性能 | GridItemStyle 切换动画帧率 ≥55fps | Perf 组网测试 | Jank 检测 |
| 内存 | selectable 选中状态不额外占用内存 | Dump 机制 | SelectableItemPattern |
| 可测试性 | SetSelectable/MarkIsSelected/FireSelectChangeEvent 可独立 UT | Mock GridItemPattern | grid_item_pattern.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | GridItemStyle=PLAIN 圆角取主题值，折叠态变化不影响 | 圆角跟随主题 | 主题适配测试 | — |
| 穿戴 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | GridItem 语义节点含 rowStart/columnStart 等位置信息和选中状态 | 辅助技术读取网格位置和选中态 |
| 大字体 | 是 | GridItem 内容区受大字体影响，但跨行跨列范围不变 | 大字体适配 |
| 深色模式 | 是 | GridItemStyle=PLAIN 的 hover/press blend 动画颜色跟随主题深浅色 | 深色模式适配 |
| 多窗口/分屏 | 否 | GridItem 属性不随窗口尺寸变化 | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | forceRebuild @since 9 废弃，selected @since 10 双向绑定 | 低版本兼容 |
| 生态兼容 | 否 | — | — |

## 行为场景（Gherkin）

```gherkin
Feature: GridItem 布局与选择
  作为 ArkUI 开发者
  我想要通过 GridItem 的跨行跨列属性和选择能力控制网格项的行为
  以便实现不规则布局和可交互的网格场景

  Scenario: GridItemStyle=PLAIN 渲染圆角和交互动画
    Given GridItem 构造时传入 {style: GridItemStyle.PLAIN}
    When GridItem 渲染完成
    Then borderRadius 取主题配置值
    And 鼠标悬停时触发 hover blend animation
    And 鼠标按下时触发 press blend animation

  Scenario: GridItemStyle=NONE 无圆角无动画
    Given GridItem 构造时传入 {style: GridItemStyle.NONE}
    When GridItem 渲染完成
    Then borderRadius=0
    And 鼠标悬停时无动画效果
    And 鼠标按下时无动画效果

  Scenario: 跨行跨列属性定义 GridItem 位置
    Given GridItem 设置 rowStart=0, rowEnd=1, columnStart=0, columnEnd=2
    When Grid 计算布局
    Then GridItem 行跨度 = 1 - 0 + 1 = 2
    And GridItem 列跨度 = 2 - 0 + 1 = 3

  Scenario Outline: 跨度 clamp 最小值
    Given GridItem 设置 rowStart=<start>, rowEnd=<end>
    When Grid 计算行跨度
    Then 行跨度 = max(1, <end> - <start> + 1) = <span>

    Examples:
      | start | end | span |
      | 0     | 1   | 2    |
      | 2     | 1   | 1    |
      | 0     | 0   | 1    |

  Scenario: 修改跨行跨列属性触发父 Grid 重布局
    Given GridItem 已设置 rowStart=0, rowEnd=0
    When 开发者调用 rowEnd(1)
    Then 触发父 Grid 的 ResetGridLayoutInfoAndMeasure()
    And Grid 重新计算布局

  Scenario: selectable=false 取消已选中项
    Given GridItem selectable=true 且当前为选中态
    When 开发者调用 selectable(false)
    Then MarkIsSelected(false) 被调用
    And FireSelectChangeEvent 触发
    And onSelect 回调参数 isSelected=false

  Scenario: selected $$ 双向绑定
    Given GridItem 设置 selected($$isSelected)
    When 用户点击 GridItem 选中
    Then $$isSelected 绑定变量自动更新为 true
    When 代码修改 $$isSelected = false
    Then GridItem 选中状态同步更新为未选中

  Scenario: MarkIsSelected 触发双重回调
    Given GridItem 设置了 onSelect 回调
    And GridItem 注册了 selectChangeEvent_
    When MarkIsSelected 被调用
    Then FireSelectChangeEvent 同时触发 selectChangeEvent_ 和 onSelect_
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
    query: "GridItemPattern 继承 SelectableItemPattern 选择能力 (grid_item_pattern.h/cpp)"
  - repo: "openharmony/ace_engine"
    query: "GridItemLayoutProperty rowStart rowEnd columnStart columnEnd ResetGridLayoutInfoAndMeasure (grid_item_layout_property.h)"
  - repo: "openharmony/ace_engine"
    query: "GridItemModelNG 构造器 GridItemOptions GridItemStyle (grid_item_model_ng.h)"
  - repo: "openharmony/ace_engine"
    query: "GridItemStyle NONE PLAIN hover blend press blend animation (grid_item_pattern.cpp)"
  - repo: "openharmony/ace_engine"
    query: "FireSelectChangeEvent selectChangeEvent_ onSelect_ (grid_item_pattern.cpp)"
```

**关键文档：**
- SDK 动态 API: `interface/sdk-js/api/@internal/component/ets/gridItem.d.ts`
- SDK 静态 API: `interface/sdk-js/api/arkui/component/gridItem.static.d.ets`
- C-API: `interfaces/native/native_node.h` (NODE_GRID_ITEM_ROW_START 等)
- 源码入口: `frameworks/core/components_ng/pattern/grid/grid_item_pattern.h/cpp`、`grid_item_layout_property.h`、`grid_item_model.h`、`grid_item_model_ng.h`
