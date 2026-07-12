# 特性规格

> Func-04-03-01-Feat-03 Flex 相关属性：固化 flexGrow/flexShrink/flexBasis/alignSelf/layoutWeight/displayPriority 六个 Flex 子项属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Flex 相关属性 (Flex Item Properties) |
| 特性编号 | Func-04-03-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 12 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/01-layout-attributes/design.md` | Baselined |

---

## 用户故事

### US-1: 按比例分配剩余空间（flexGrow）

**作为** 应用开发者,
**我想要** 通过 .flexGrow() 设置子组件在父容器剩余空间中的分配比例,
**以便** 实现弹性布局中子组件按比例占满剩余空间。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.flexGrow(value: number)` 设置正值 THEN 子组件在主轴剩余空间中按 value 占 totalGrow 的比例获得额外尺寸 | 正常 |
| AC-1.2 | WHEN value = 0（默认值）THEN 子组件不参与剩余空间分配，按自身内容尺寸布局 | 正常 |
| AC-1.3 | WHEN value 为负数 THEN JS 桥接层将 value Clamp 到 0，等效于 flexGrow(0) | 异常 |
| AC-1.4 | WHEN value 为 undefined 或 null THEN flexGrow 被设为 0.0（默认值） | 异常 |
| AC-1.5 | WHEN 多个子组件同时设置 flexGrow THEN 剩余空间 = 主轴总尺寸 - 所有子组件主轴尺寸之和，每个子组件获得 `remainSpace × (flexGrow / totalGrow)` 的额外空间 | 正常 |
| AC-1.6 | WHEN flexGrow 与 layoutWeight 同时存在且 totalFlexWeight > 0 THEN layoutWeight 模式优先，flexGrow 不生效（互斥优先级） | 异常 |

### US-2: 按比例收缩溢出空间（flexShrink）

**作为** 应用开发者,
**我想要** 通过 .flexShrink() 设置子组件在空间不足时的收缩比例,
**以便** 防止子组件溢出父容器。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.flexShrink(value: number)` 设置正值 THEN 子组件在主轴空间不足时按比例收缩：每个子组件收缩量 = `overflowSpace × (flexShrink × childMainSize) / totalShrink` | 边界 |
| AC-2.2 | WHEN 父容器为 Row/Column 且未显式设置 flexShrink THEN 默认值为 0（不收缩） | 正常 |
| AC-2.3 | WHEN 父容器为 Flex 且未显式设置 flexShrink THEN 默认值为 1（按比例收缩） | 正常 |
| AC-2.4 | WHEN value 为负数 THEN JS 桥接层调用 ResetFlexShrink() 重置属性 | 异常 |
| AC-2.5 | WHEN value 为 undefined 或 null THEN JS 桥接层调用 ResetFlexShrink() 重置属性（与 flexGrow undefined 仅设为 0 的行为不一致） | 异常 |
| AC-2.6 | WHEN flexShrink 被重置（Reset）THEN 恢复为容器默认值（Row/Column: 0, Flex: 1） | 正常 |

### US-3: 设置主轴基础尺寸（flexBasis）

**作为** 应用开发者,
**我想要** 通过 .flexBasis() 设置子组件在主轴上的初始尺寸,
**以便** 在 grow/shrink 分配之前确定子组件的基础大小。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.flexBasis(value: number)` THEN 子组件主轴初始尺寸设置为 value（单位 VP） | 正常 |
| AC-3.2 | WHEN 调用 `.flexBasis(value: string)`（如 '100px'）THEN 按对应单位解析 | 正常 |
| AC-3.3 | WHEN value 为 undefined、null 或无效类型 THEN flexBasis 设为 AUTO（由内容决定基础尺寸） | 异常 |
| AC-3.4 | WHEN value 为百分比（如 '50%'）THEN JS 桥接层和 C-API 层均将其转为 AUTO（flexBasis 不支持百分比） | 异常 |
| AC-3.5 | WHEN flexBasis 为 AUTO 或无效值 THEN 子组件使用自身内容尺寸作为主轴基础尺寸 | 异常 |
| AC-3.6 | WHEN flexBasis 为有效正值 THEN 在 FlexLayoutAlgorithm 中通过 `UpdateChildLayoutConstrainByFlexBasis` 将 flexBasis 转换为像素值并设置到 selfIdealSize 的主轴维度 | 正常 |
| AC-3.7 | WHEN 子组件为 Blank 且 Blank 的 selfIdealSize > flexBasis THEN flexBasis 不覆盖 selfIdealSize（Blank 特殊处理） | 边界 |

### US-4: 设置交叉轴对齐覆盖（alignSelf）

**作为** 应用开发者,
**我想要** 通过 .alignSelf() 单独设置某个子组件在交叉轴上的对齐方式,
**以便** 覆盖父容器设置的 alignItems 全局对齐。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.alignSelf(value: ItemAlign)` THEN 该子组件的交叉轴对齐使用 alignSelf 值，而非父容器的 alignItems | 正常 |
| AC-4.2 | WHEN value 为 ItemAlign.Auto（默认值）THEN 使用父容器的交叉轴对齐设置（不覆盖） | 正常 |
| AC-4.3 | WHEN value 为 ItemAlign.Start THEN 子组件在交叉轴起始端对齐 | 正常 |
| AC-4.4 | WHEN value 为 ItemAlign.Center THEN 子组件在交叉轴居中对齐 | 正常 |
| AC-4.5 | WHEN value 为 ItemAlign.End THEN 子组件在交叉轴末尾端对齐 | 正常 |
| AC-4.6 | WHEN value 为 ItemAlign.Stretch THEN 子组件在交叉轴方向拉伸至父容器交叉轴尺寸，触发二次测量（needSecondMeasure = true） | 正常 |
| AC-4.7 | WHEN value 为 ItemAlign.Baseline THEN 子组件按基线对齐，需要收集每个子组件的 baselineDistance 计算最大基线距离，交叉轴尺寸可能因此增大 | 边界 |
| AC-4.8 | WHEN value 为 undefined、null 或无效类型 THEN alignSelf 被设为 FlexAlign::AUTO | 异常 |
| AC-4.9 | WHEN value 超出有效范围（0-8）THEN C-API 层设为 FlexAlign::AUTO（`node_common_modifier.cpp:4944-4947`）；JS 层不处理（`js_view_abstract.cpp:3374` 仅在 0-8 范围内设置） | 边界 |

### US-5: 按权重分配剩余空间（layoutWeight）

**作为** 应用开发者,
**我想要** 通过 .layoutWeight() 设置子组件在 Row/Column/Flex 中的权重,
**以便** 简单快速地按比例分配父容器主轴空间。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.layoutWeight(value: number)` 设置正值 THEN 子组件在主轴上按权重分配剩余空间：`childSize = max(spacePerWeight × layoutWeight, 0)` | 边界 |
| AC-5.2 | WHEN value = 0（默认值）THEN 子组件不参与权重分配，按自身内容尺寸布局 | 正常 |
| AC-5.3 | WHEN value 为负数 THEN 布局算法中 `LessOrEqual(childLayoutWeight, 0.0)` 判断为 true，等效于 layoutWeight = 0 | 异常 |
| AC-5.4 | WHEN value 为 undefined THEN 继续以 value = 0.0 处理 | 异常 |
| AC-5.5 | WHEN API < 12 且 value 为 number THEN 值被解析为 int32_t（截断小数部分） | 边界 |
| AC-5.6 | WHEN API ≥ 12 且 value 为 number THEN 值被解析为 float（保留小数部分） | 正常 |
| AC-5.7 | WHEN layoutWeight 模式激活（totalFlexWeight > 0）THEN 布局算法跳过 flexGrow/flexShrink 模式，使用 weight 模式 | 边界 |
| AC-5.8 | WHEN weight 模式下子组件有 layoutWeight > 0 THEN 先测量 layoutWeight = 0 的子组件确定剩余空间，再按权重分配给 layoutWeight > 0 的子组件 | 边界 |

### US-6: 设置布局显示优先级（displayPriority）

**作为** 应用开发者,
**我想要** 通过 .displayPriority() 设置子组件的布局优先级,
**以便** 在空间不足时按优先级决定哪些子组件可见、哪些被隐藏。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.displayPriority(value: number)` THEN 子组件获得对应的显示优先级（内部存储为 displayIndex） | 正常 |
| AC-6.2 | WHEN 开发者从未调用 `.displayPriority()` THEN 属性为 unset（std::optional 无值），布局算法使用 `value_or(1)` 作为默认优先级（`flex_layout_algorithm.cpp:320`）。这意味着未设置 displayPriority 的子组件默认优先级为 1，不会被优先淘汰 | 异常 |
| AC-6.3 | WHEN 多个子组件有不同 displayPriority THEN 布局算法按优先级从高到低依次处理 | 正常 |
| AC-6.4 | WHEN 空间不足以容纳所有子组件 THEN 优先级较低的子组件被隐藏（SetActive(false)），frameSize 设为 {0, 0} | 正常 |
| AC-6.5 | WHEN value 为 undefined 或 null THEN API ≥ 12 时 JS 桥接层显式调用 `SetDisplayIndex(0)` 将属性设为 0（`js_view_abstract.cpp:3262-3263`），此时布局算法 `value_or(1)` 不生效，实际使用 0。**注意**：这与"从未设置"（算法 fallback 到 1）的语义不同——`displayPriority(undefined)` 使组件成为最低优先级 | 异常 |
| AC-6.6 | WHEN value 为负数 THEN 值直接传递给 SetDisplayIndex（无验证），负优先级组件与未设置（priority=1）的组件相比更容易被淘汰 | 异常 |
| AC-6.7 | WHEN displayPriority 与 layoutWeight 同时使用 THEN displayPriority 仍生效，优先级较低的子组件在 weight 分配前即被排除 | 正常 |
| AC-6.8 | WHEN 通过 C-API 调用 `ResetDisplayPriority` THEN displayIndex 被设为 0（`DEFAULT_DISPLAY_PRIORITY`，`node_common_modifier.cpp:107`），与 JS undefined 行为一致 | 异常 |

---

## 验收追溯

| AC编号 | US ID | 关联业务规则 | 验证手段 |
|-------|-------|-------------|----------|
| AC-1.1 || R-4 | 单元测试 / XTS | 正常 |
| AC-1.2 || R-5 | 单元测试 | 正常 |
| AC-1.3 || R-25 | 单元测试 / XTS | 正常 |
| AC-1.4 || R-26 | 单元测试 | 正常 |
| AC-1.5 || R-6 | 集成测试 | 正常 |
| AC-1.6 || R-1, ADR-F3-1 | 集成测试 | 正常 |
| AC-2.1 || R-7 | 单元测试 / XTS | 正常 |
| AC-2.2 || R-8, ADR-F3-2 | 单元测试 | 正常 |
| AC-2.3 || R-8, ADR-F3-2 | 单元测试 | 正常 |
| AC-2.4 || R-27 | 单元测试 | 正常 |
| AC-2.5 || R-28, ADR-F3-3 | 单元测试 | 正常 |
| AC-2.6 || R-8 | 单元测试 | 正常 |
| AC-3.1 || R-9 | 单元测试 / XTS | 正常 |
| AC-3.2 || R-9 | 单元测试 | 正常 |
| AC-3.3 || R-29 | 单元测试 | 正常 |
| AC-3.4 || R-30, ADR-F3-4 | 单元测试 | 正常 |
| AC-3.5 || R-10 | 单元测试 | 正常 |
| AC-3.6 || R-11 | 代码评审 | 正常 |
| AC-3.7 || R-12 | 单元测试 | 正常 |
| AC-4.1 || R-13 | 单元测试 / XTS | 正常 |
| AC-4.2 || R-14 | 单元测试 | 正常 |
| AC-4.3 || R-13 | 单元测试 | 正常 |
| AC-4.4 || R-13 | 单元测试 | 正常 |
| AC-4.5 || R-13 | 单元测试 | 正常 |
| AC-4.6 || R-15, ADR-F3-5 | 集成测试 | 正常 |
| AC-4.7 || R-16, ADR-F3-5 | 集成测试 | 正常 |
| AC-4.8 || R-31 | 单元测试 | 正常 |
| AC-4.9 || R-32 | 单元测试 | 正常 |
| AC-5.1 || R-17 | 单元测试 / XTS | 正常 |
| AC-5.2 || R-18 | 单元测试 | 正常 |
| AC-5.3 || R-33 | 单元测试 | 正常 |
| AC-5.4 || R-34 | 单元测试 | 正常 |
| AC-5.5 || R-19, ADR-F3-4 | 单元测试 | 正常 |
| AC-5.6 || R-19, ADR-F3-4 | 单元测试 | 正常 |
| AC-5.7 || R-1, ADR-F3-1 | 集成测试 | 正常 |
| AC-5.8 || R-20 | 集成测试 | 正常 |
| AC-6.1 || R-21 | 单元测试 | 正常 |
| AC-6.2 || R-21 | 单元测试 | 正常 |
| AC-6.3 || R-22 | 集成测试 | 正常 |
| AC-6.4 || R-23 | 集成测试 | 正常 |
| AC-6.5 || R-35 | 单元测试 | 正常 |
| AC-6.6 || R-37 | 单元测试 | 正常 |
| AC-6.7 || R-24 | 集成测试 | 正常 |
| AC-6.8 || R-21 | 单元测试 | 正常 |
| AC-1.1 || R-4 | SpecTest HostPreview | 正常 |
| AC-1.2 || R-5 | SpecTest HostPreview | 正常 |
| AC-1.5 || R-6 | SpecTest HostPreview | 正常 |
| AC-2.1 || R-7 | SpecTest HostPreview | 正常 |
| AC-2.2 || R-8 | SpecTest HostPreview | 正常 |
| AC-2.3 || R-8 | SpecTest HostPreview | 正常 |
| AC-3.1 || R-9 | SpecTest HostPreview | 正常 |
| AC-4.1, AC-4.5 | US-4 | R-13 | SpecTest HostPreview |
| AC-4.4 || R-13 | SpecTest HostPreview | 正常 |
| AC-4.6 || R-15 | SpecTest HostPreview | 正常 |
| AC-5.1 || R-17 | SpecTest HostPreview | 正常 |
| AC-6.3, AC-6.4 | US-6 | R-22, R-23 | SpecTest HostPreview |

### SpecTest 用例追溯

| Case ID | 对应 AC |
|---------|---------|
| case-001-flex-grow-basic | AC-1.1 |
| case-002-flex-grow-ratio | AC-1.1, AC-1.5 |
| case-003-flex-shrink-basic | AC-2.1 |
| case-004-flex-basis-basic | AC-3.1 |
| case-005-layout-weight-basic | AC-5.1 |
| case-006-align-self-basic | AC-4.1, AC-4.5 |
| case-001-flex-grow-zero-default | AC-1.2 |
| case-002-row-flex-shrink-default | AC-2.2 |
| case-003-flex-flex-shrink-default | AC-2.3 |
| case-004-align-self-stretch | AC-4.6 |
| case-005-align-self-center | AC-4.4 |
| case-006-display-priority-basic | AC-6.3, AC-6.4 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | **layoutWeight 与 flexGrow 互斥优先级**：当 totalFlexWeight > 0 时，布局算法进入 weight 模式，跳过 grow/shrink 模式。layoutWeight 存储在 MagicItemProperty，flexGrow 存储在 FlexItemProperty，二者存储层独立但布局消费互斥（`flex_layout_algorithm.cpp:619-629`） | — | — |
| R-2 | 行为 | — | 所有 Flex 子项属性变更均触发 `PROPERTY_UPDATE_MEASURE`，导致所属组件在下一帧重新进入测量管线 | — | — |
| R-3 | 行为 | — | Flex 子项属性仅在有 Flex/Row/Column 父容器时才有布局效果，在其他容器中设置不影响布局（但属性仍被存储） | — | — |
| R-4 | 行为 | — | flexGrow 空间分配公式：`childExtraSpace = remainSpace × (childFlexGrow / totalGrow)`，其中 `totalGrow = Σ(flexGrow)`（仅计算正值）（`flex_layout_algorithm.cpp:850-854`） | — | — |
| R-5 | 行为 | — | flexGrow 默认值为 0.0，表示不参与剩余空间分配（`flex_layout_algorithm.cpp:724`） | — | — |
| R-6 | 行为 | — | 当剩余空间 > 0 且 totalGrow > 0 时进入 grow 模式；当剩余空间 < 0 且 totalShrink > 0 时进入 shrink 模式（`flex_layout_algorithm.cpp:887-929`） | — | — |
| R-7 | 行为 | — | flexShrink 空间收缩公式：`childShrinkSpace = overflowSpace × (childFlexShrink × childMainSize) / totalShrink`，注意收缩量与子组件自身尺寸成正比（`flex_layout_algorithm.cpp:850-854`） | — | — |
| R-8 | 行为 | — | flexShrink 默认值因父容器类型而异：Row/Column（isLinearLayoutFeature_=true）默认 0.0，Flex 默认 1.0。该逻辑由 `isLinearLayoutFeature_` 标志控制（`flex_layout_algorithm.cpp:723`） | — | — |
| R-9 | 行为 | — | flexBasis 支持 VP/PX/FP/LPX 单位，不支持百分比和 calc()。设置后通过 `UpdateChildLayoutConstrainByFlexBasis` 将值转换为像素并写入 selfIdealSize 的主轴维度（`flex_layout_algorithm.cpp:126-155`） | — | — |
| R-10 | 行为 | — | flexBasis 为 AUTO 或无效值时，子组件使用自身内容尺寸作为主轴基础尺寸，flexBasis 不参与约束构建（`flex_layout_algorithm.cpp:135-136`） | — | — |
| R-11 | 行为 | — | flexBasis 像素转换使用 `Dimension::ConvertToPx()`，不使用 CalcLength 的百分比参照系（因为不支持百分比）（`flex_layout_algorithm.cpp:150-154`） | — | — |
| R-12 | 行为 | — | Blank 组件特殊处理：当 Blank 的 selfIdealSize > flexBasis 时，flexBasis 不覆盖 selfIdealSize（`flex_layout_algorithm.cpp:138-148`） | — | — |
| R-13 | 行为 | — | alignSelf 覆盖父容器的交叉轴对齐设置。有效值通过 ItemAlign 枚举（ArkTS）或 FlexAlign 枚举（C++/C-API）指定，二者值域相同（0-5 对应 Auto/Start/Center/End/Stretch/Baseline） | — | — |
| R-14 | 行为 | — | alignSelf 为 Auto 时使用父容器交叉轴对齐（crossAxisAlign_），等效于未设置 alignSelf（`flex_layout_algorithm.cpp:1605-1616`） | — | — |
| R-15 | 行为 | — | alignSelf:STRETCH 触发二次测量：首先按正常尺寸测量，然后将交叉轴约束更新为父容器交叉轴尺寸，设置 `needSecondMeasure = true`（`flex_layout_algorithm.cpp:836-839`） | — | — |
| R-16 | 行为 | — | alignSelf:BASELINE 需要收集每个子组件的 baselineDistance，计算 maxBaselineDistance。交叉轴位置 = `maxBaselineDistance - selfBaselineDistance`（`flex_layout_algorithm.cpp:206-219, 1458-1464`） | — | — |
| R-17 | 行为 | — | layoutWeight 空间分配公式：`childSize = max(spacePerWeight × childLayoutWeight, 0.0f)`，其中 `spacePerWeight = remainedMainAxisSize / totalFlexWeight`（`flex_layout_algorithm.cpp:476, 492`） | — | — |
| R-18 | 行为 | — | layoutWeight 默认值为 0.0，不参与权重分配。存储在 MagicItemProperty 而非 FlexItemProperty（`magic_layout_property.h:27`） | — | — |
| R-19 | 行为 | — | layoutWeight API < 12 解析为 int32_t（截断小数），API ≥ 12 解析为 float（保留小数）。影响 string 和 number 两种输入形式（`js_view_abstract.cpp:2827-2851`） | — | — |
| R-20 | 行为 | — | weight 模式下测量顺序：先测量 layoutWeight = 0 的子组件确定 consumedSize，再计算 remainSpace = mainAxisSize - consumedSize，最后按权重分配给 layoutWeight > 0 的子组件（`flex_layout_algorithm.cpp:414-548`） | — | — |
| R-21 | 行为 | — | displayPriority 值直接存储为 FlexItemProperty 中的 DisplayIndex（int32_t）。属性类型为 `std::optional<int32_t>`，未设置时无值。布局算法使用 `GetDisplayIndex().value_or(1)` 作为 fallback（`flex_layout_algorithm.cpp:320`），注意 ViewAbstract::GetDisplayIndex 的 getter 使用 `value_or(0)`（`view_abstract.cpp:10254-10260`），两条路径默认值不同 | — | — |
| R-22 | 行为 | — | 布局算法按 displayPriority 从高到低遍历（`magicNodes_.rbegin()`），高优先级子组件优先分配空间（`flex_layout_algorithm.cpp:414-468`） | — | — |
| R-23 | 行为 | — | 当空间不足以容纳所有优先级的子组件时，较低优先级的子组件被 SetActive(false)，frameSize 设为 {0, 0}（`flex_layout_algorithm.cpp:MeasureInPriorityMode`） | — | — |
| R-24 | 行为 | — | displayPriority 与 layoutWeight 交互：displayPriority 先筛选可见子组件，再在可见子组件中应用 layoutWeight 分配。displayPriority 影响每一行的 magicNodeWeights_ 累计（`flex_layout_algorithm.cpp:260-280`） | — | — |
| R-25 | 异常 | — | flexGrow 负值被 JS 桥接层 Clamp 到 0（`js_view_abstract.cpp:3233`）；C-API 层同样 Clamp 到 0（`node_common_modifier.cpp:4991-4992`） | — | — |
| R-26 | 异常 | — | flexGrow undefined/null 被设为 0.0（默认值），不触发属性重置（`js_view_abstract.cpp:3224-3227`） | — | — |
| R-27 | 异常 | — | flexShrink 负值触发 `ResetFlexShrink()`，属性被清除恢复为容器默认值（`js_view_abstract.cpp:3249-3251`） | — | — |
| R-28 | 异常 | — | flexShrink undefined/null 触发 `ResetFlexShrink()`，与 flexGrow undefined 仅设 0 的行为不一致（`js_view_abstract.cpp:3244-3246`）。这是历史实现差异，当前实现即规格 | — | — |
| R-29 | 异常 | — | flexBasis undefined/null/无效类型被设为 AUTO（`js_view_abstract.cpp:3209-3210`） | — | — |
| R-30 | 异常 | — | flexBasis 百分比值在 JS 桥接层和 C-API 层均被转为 AUTO（`js_view_abstract.cpp:3212-3214`, `node_common_modifier.cpp:5099-5101`） | — | — |
| R-31 | 异常 | — | alignSelf undefined/null/无效类型被设为 FlexAlign::AUTO（`js_view_abstract.cpp:3369`） | — | — |
| R-32 | 异常 | — | alignSelf 值超出 [0, 8] 范围时，JS 桥接层忽略该值不设置，C-API 层设为 AUTO（`js_view_abstract.cpp:3374`, `node_common_modifier.cpp:4944-4947`） | — | — |
| R-33 | 异常 | — | layoutWeight 负值无验证，直接传递。布局算法中 `LessOrEqual(childLayoutWeight, 0.0)` 判断为 true，等效于 0（`flex_layout_algorithm.cpp:489`） | — | — |
| R-34 | 异常 | — | layoutWeight undefined 时继续以 value = 0.0 处理；null 时 CheckJSCallbackInfo 返回 false 且 IsUndefined 为 false，直接 return 不设置（`js_view_abstract.cpp:2833-2835`） | — | — |
| R-35 | 异常 | — | displayPriority undefined/null 在 API ≥ 12 时显式调用 `SetDisplayIndex(0)` 将属性设为 0（`js_view_abstract.cpp:3262-3263`）。**注意**：此行为与"从未调用 displayPriority"（属性 unset，布局 fallback 到 1）语义不同——undefined 使组件成为最低优先级（0 < 1） | — | — |
| R-36 | 异常 | — | displayPriority 属性存在 getter/algorithm 默认值不一致：`ViewAbstract::GetDisplayIndex` 使用 `value_or(0)`（`view_abstract.cpp:10254-10260`），布局算法使用 `value_or(1)`（`flex_layout_algorithm.cpp:320`）。当前实现即规格，下游测试应按消费路径分别断言 | — | — |
| R-37 | 异常 | — | displayPriority 负值无验证，直接传递给 SetDisplayIndex（`js_view_abstract.cpp:3267`） | — | — |
| R-38 | 恢复 | — | flexGrow 设置后可通过 `.flexGrow(undefined)` 恢复为默认值 0.0（但不清除属性，仅设值） | — | — |
| R-39 | 恢复 | — | flexShrink 设置后可通过 `.flexShrink(undefined)` 或 `.flexShrink(负值)` 完全重置（ResetFlexShrink 清除属性） | — | — |
| R-40 | 恢复 | — | flexBasis 设置后可通过 `.flexBasis(undefined)` 恢复为 AUTO | — | — |
| R-41 | 恢复 | — | alignSelf 设置后可通过 `.alignSelf(undefined)` 或 `.alignSelf(ItemAlign.Auto)` 恢复为 AUTO（跟随父容器） | — | — |
| R-42 | 恢复 | — | layoutWeight 设置后可通过 `.layoutWeight(undefined)` 以 value = 0.0 处理 | — | — |
| R-43 | 恢复 | — | displayPriority 设置后可通过 `.displayPriority(undefined)` 在 API ≥ 12 恢复为 0 | — | — |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 flexGrow (AC-1.1~1.6) | 单元测试 + XTS | 剩余空间按比例分配；undefined 重置；与 layoutWeight 互斥 |
| VM-2 | US-2 flexShrink (AC-2.1~2.6) | 单元测试 + XTS | 溢出空间按比例收缩；Row/Flex 默认值差异；C API Reset |
| VM-3 | US-3 flexBasis (AC-3.1~3.7) | 单元测试 + XTS + 代码评审 | 主轴基础尺寸；字符串/undefined/百分比（拒绝→AUTO）处理 |
| VM-4 | US-4 alignSelf (AC-4.1~4.9) | 单元测试 + XTS | 交叉轴对齐覆盖；STRETCH 二次测量；BASELINE 对齐；越界→AUTO |
| VM-5 | US-5 layoutWeight (AC-5.1~5.8) | 单元测试 + XTS | 按权重分配；API 12 int/float 类型差异；与 flexGrow 互斥 |
| VM-6 | US-6 displayPriority (AC-6.1~6.8) | 单元测试 + C API | 显示优先级；空间淘汰；undefined/负值处理；C API Reset |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 验证位置/用例 |
|-------|----------|--------------|
| AC-1.1 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (flexGrow 分配) |
| AC-1.2 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (flexGrow=0) |
| AC-1.3 | XTS | `test/xts/acts/arkui/ace_c_arkui_test/entry/src/main/cpp/flex/commonattrs_flexgrow_test.cpp` |
| AC-1.4 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (undefined) |
| AC-1.5 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (多子组件) |
| AC-1.6 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_first_part.cpp` (layoutWeight+flexGrow) |
| AC-2.1 | XTS | `test/xts/acts/arkui/ace_c_arkui_test/entry/src/main/cpp/flex/commonattrs_flexshrink_test.cpp` |
| AC-2.2 | 单元测试 | `test/unittest/core/pattern/linear_layout/linear_layout_new_test_ng.cpp` (Row 默认) |
| AC-2.3 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (Flex 默认) |
| AC-2.4 | 单元测试 | `test/unittest/capi/modifiers/flex_modifier_test.cpp` (ResetFlexShrink) |
| AC-2.5 | 单元测试 | `test/unittest/capi/modifiers/flex_modifier_test.cpp` (undefined→Reset) |
| AC-2.6 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (Reset 恢复) |
| AC-3.1 | XTS | `test/xts/acts/arkui/ace_c_arkui_test/entry/src/main/cpp/flex/commonattrs_flexbasis_test.cpp` |
| AC-3.2 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (字符串) |
| AC-3.3 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (undefined) |
| AC-3.4 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (百分比→AUTO) |
| AC-3.5 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (AUTO) |
| AC-3.6 | 代码评审 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:126-155` |
| AC-3.7 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_second_part.cpp` (Blank) |
| AC-4.1 | XTS | `test/xts/acts/arkui/ace_c_arkui_test/entry/src/main/cpp/flex/commonattrs_alignself_test.cpp` |
| AC-4.2 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_third_part.cpp` (Auto) |
| AC-4.3 ~ AC-4.5 | XTS | `test/xts/acts/arkui/ace_c_arkui_test/entry/src/main/cpp/flex/commonattrs_alignself_test.cpp` |
| AC-4.6 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_third_part.cpp` (STRETCH) |
| AC-4.7 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_third_part.cpp` (BASELINE) |
| AC-4.8 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_third_part.cpp` (undefined) |
| AC-4.9 | 单元测试 | `test/unittest/capi/modifiers/flex_modifier_test.cpp` (越界→AUTO) |
| AC-5.1 | XTS | `test/xts/acts/arkui/ace_c_arkui_test/entry/src/main/cpp/flex/commonattrs_layoutweight_test.cpp` |
| AC-5.2 | 单元测试 | `test/unittest/core/pattern/linear_layout/linear_layout_new_test_ng.cpp` (weight=0) |
| AC-5.3 | 单元测试 | `test/unittest/core/pattern/linear_layout/linear_layout_new_test_ng.cpp` (负值) |
| AC-5.4 | 单元测试 | `test/unittest/core/pattern/linear_layout/linear_layout_new_test_ng.cpp` (undefined) |
| AC-5.5 | 单元测试 | `test/unittest/core/pattern/linear_layout/linear_layout_new_test_ng.cpp` (API<12 int) |
| AC-5.6 | 单元测试 | `test/unittest/core/pattern/linear_layout/linear_layout_new_test_ng.cpp` (API≥12 float) |
| AC-5.7 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_first_part.cpp` (互斥) |
| AC-5.8 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_first_part.cpp` (测量顺序) |
| AC-6.1 | 单元测试 | `test/unittest/capi/modifiers/flex_modifier_test.cpp` (SetDisplayPriority) |
| AC-6.2 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_first_part.cpp` (未设置 fallback=1) |
| AC-6.3 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_first_part.cpp` (低优先级隐藏) |
| AC-6.4 | 单元测试 | `test/unittest/capi/modifiers/flex_modifier_test.cpp` (undefined API12) |
| AC-6.5 | 单元测试 | `test/unittest/capi/modifiers/flex_modifier_test.cpp` (负值) |
| AC-6.6 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_first_part.cpp` (priority+weight) |
| AC-6.7 | 单元测试 | `test/unittest/core/pattern/flex/flex_new_test_ng_first_part.cpp` (priority+weight) |
| AC-6.8 | 单元测试 | `test/unittest/capi/modifiers/flex_modifier_test.cpp` (ResetDisplayPriority) |

---

## API 变更分析

### 新增 API

| API 签名 | 参数类型 | 默认值 | @since | 说明 |
|----------|----------|--------|--------|------|
| `flexGrow(value: number \| undefined): this` | `number` | 0 | API 7 (static API 23) | 设置剩余空间分配比例 |
| `flexShrink(value: number \| undefined): this` | `number` | Row/Column: 0, Flex: 1 | API 7 (static API 23) | 设置空间不足时收缩比例 |
| `flexBasis(value: number \| string \| undefined): this` | `number \| string` | auto | API 7 (static API 23) | 设置主轴基础尺寸 |
| `alignSelf(value: ItemAlign \| undefined): this` | `ItemAlign` | Auto | API 7 (static API 23) | 设置交叉轴对齐覆盖 |
| `layoutWeight(value: number \| string \| undefined): this` | `number \| string` | 0 | API 7 (static API 23) | 设置权重布局比例 |
| `displayPriority(value: number \| undefined): this` | `number` | unset（布局 fallback=1, getter=0） | API 7 | 设置显示优先级。undefined 在 API 12+ 显式设为 0 |

**C-API (NDK) 接口：**

> **注意**：以下枚举名属于 `ArkUI_NodeAttributeType`（`native_node.h:177`），为隐式自增枚举（仅 `NODE_WIDTH = 0` 显式赋值），具体数值随版本变化，不可硬编码。应始终使用枚举名引用。

| 枚举名 | 参数类型 | Setter | Resetter | Getter | 定义位置 |
|--------|----------|--------|----------|--------|----------|
| `NODE_ALIGN_SELF` | `ArkUI_Int32` (FlexAlign) | `SetAlignSelf` | `ResetAlignSelf` (设为 AUTO) | `GetAlignSelf → ArkUI_Int32` | `native_node.h:1373` |
| `NODE_FLEX_GROW` | `ArkUI_Float32` | `SetFlexGrow` | `ResetFlexGrow` (设为 0.0) | `GetFlexGrow → ArkUI_Float32` | `native_node.h:1385` |
| `NODE_FLEX_SHRINK` | `ArkUI_Float32` | `SetFlexShrink` | `ResetFlexShrink` (ACE_RESET) | `GetFlexShrink → ArkUI_Float32` | `native_node.h:1397` |
| `NODE_FLEX_BASIS` | `ArkUIStringAndFloat*` | `SetFlexBasis` | `ResetFlexBasis` (设为 AUTO) | `GetFlexBasis → ArkUI_Float32` | `native_node.h:1409` |
| `NODE_LAYOUT_WEIGHT` | `ArkUI_Int32` | `SetLayoutWeight` | `ResetLayoutWeight` (设为 0) | `GetLayoutWeight → ArkUI_Float32` | `native_node.h:1499` |
| `NODE_DISPLAY_PRIORITY` | `ArkUI_Int32` | `SetDisplayPriority` | `ResetDisplayPriority` (设为 0) | `GetDisplayPriority → ArkUI_Int32` | `native_node.h:1511` |

**C-API 参数详情：**

- `NODE_ALIGN_SELF`: `ArkUI_AttributeItem { .value[0].i32 = flexAlignValue }`，有效范围 0-8，超出设为 AUTO
- `NODE_FLEX_GROW`: `ArkUI_AttributeItem { .value[0].f32 = flexGrow }`，负值 Clamp 到 0
- `NODE_FLEX_SHRINK`: `ArkUI_AttributeItem { .value[0].f32 = flexShrink }`，负值触发 ResetFlexShrink
- `NODE_FLEX_BASIS`: `ArkUI_AttributeItem { .value[0].f32 = numberValue, .string = "stringExpr" }`，通过 `ArkUIStringAndFloat` 传递，字符串优先于数值
- `NODE_LAYOUT_WEIGHT`: `ArkUI_AttributeItem { .value[0].i32 = weight }`，直接设置无验证
- `NODE_DISPLAY_PRIORITY`: `ArkUI_AttributeItem { .value[0].i32 = priority }`，直接设置无验证

**关联类型定义：**

```typescript
// ArkTS 枚举
enum ItemAlign {
  Auto = 0,     // 跟随父容器
  Start = 1,    // 交叉轴起始端
  Center = 2,   // 交叉轴居中
  End = 3,      // 交叉轴末尾端
  Stretch = 4,  // 交叉轴拉伸
  Baseline = 5  // 基线对齐
}

// C++ 枚举（C-API 使用）
enum class FlexAlign {
  AUTO = 0, FLEX_START = 1, CENTER = 2, FLEX_END = 3,
  STRETCH = 4, BASELINE = 5, SPACE_BETWEEN = 6,
  SPACE_AROUND = 7, SPACE_EVENLY = 8
}
```

**映射关系：** ItemAlign 值域 (0-5) 与 FlexAlign 前 6 个值一一对应。C-API 接受 0-8（含 SPACE_BETWEEN/AROUND/EVENLY），但 alignSelf 仅对 0-5 有效（6-8 对交叉轴对齐无实际意义）。

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指引 |
|----------|----------|------|----------|
| API < 12 | layoutWeight 解析为 int32_t（截断小数） | 小数权重被截断（如 1.5 → 1） | 迁移到 API 12+ 后 float 精度生效，需验证布局结果是否变化 |
| API ≥ 12 | layoutWeight 解析为 float（保留小数） | 支持非整数权重 | 无需迁移 |
| API < 12 | displayPriority(undefined/null) 不设置，保持原值 | 无显式重置方式 | API 12+ 可通过 undefined 重置为 0 |
| API ≥ 12 | displayPriority(undefined/null) 设 displayIndex 为 0 | 可通过 undefined 重置 | 新增能力，不破坏旧代码 |
| 全版本 | flexGrow undefined 设为 0，flexShrink undefined 触发 Reset | 两者 reset 策略不一致 | 已固化行为，不建议修改。开发者应对两个属性使用一致的 reset 语义 |
| 全版本 | flexShrink 默认值因父容器而异（Row/Column: 0, Flex: 1） | 从 Row/Column 迁移到 Flex 时默认行为变化 | 显式设置 flexShrink 值以避免容器差异 |

## 架构约束

| 约束 ID | 约束描述 |
|----------|----------|
| ARCH-F3-1 | Flex 子项属性存储分两层：flexGrow/flexShrink/flexBasis/alignSelf/displayIndex 存储在 FlexItemProperty（`flex_property.h:256-260`），layoutWeight 存储在 MagicItemProperty（`magic_layout_property.h:27`）。两层均由 LayoutProperty 持有 |
| ARCH-F3-2 | 所有 Flex 子项属性变更均标记 `PROPERTY_UPDATE_MEASURE`，无法降级为 LAYOUT 或 NONE |
| ARCH-F3-3 | FlexLayoutAlgorithm 同时处理 Flex/Row/Column 三种容器，通过 `isLinearLayoutFeature_` 标志区分 LinearLayout（Row/Column）和标准 Flex 的默认行为差异 |
| ARCH-F3-4 | WrapLayoutAlgorithm 仅支持 flexGrow，不支持 flexShrink 和 layoutWeight |

## 非功能性需求

| 维度 | 要求 | 说明 |
|------|------|------|
| 性能 | Flex 属性变更不应导致全树重测量 | PROPERTY_UPDATE_MEASURE 仅标记当前节点为脏，不会向上传播。但 Flex 容器的 grow/shrink 分配需要重新计算所有兄弟的尺寸 |
| 内存 | FlexItemProperty 为 optional 存储，未设置时不占用额外空间 | FlexItemProperty 由 LayoutProperty 持有，采用 lazy-init |
| 精度 | 浮点权重计算误差不应导致可见像素偏差 | spacePerFlex 使用 float 运算，最终结果经过 PixelGridRound |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 影响范围 | 说明 |
|----------|------|
| Flex 容器 | Flex/Row/Column 容器布局算法消费子组件的 Flex 属性 |
| FlexWrap 容器 | FlexWrap 容器仅消费 flexGrow，不消费 flexShrink/layoutWeight |
| 其他容器 | Stack/Grid/List 等容器不消费 Flex 子项属性（属性被存储但不影响布局） |
| 性能监控 | Flex 属性变更触发 Measure，可能影响帧率 |

---

## 行为场景

### 场景 1: flexGrow 分配剩余空间

```
场景 1: 三个子组件按 1:2:1 分配剩余空间
  Given 一个 Flex 容器，主轴尺寸 400px
    And 子组件 A 内容尺寸 50px, flexGrow(1)
    And 子组件 B 内容尺寸 50px, flexGrow(2)
    And 子组件 C 内容尺寸 50px, flexGrow(1)
  When FlexLayoutAlgorithm 执行布局
  Then remainSpace = 400 - 50 - 50 - 50 = 250
    And totalGrow = 1 + 2 + 1 = 4
    And A 尺寸 = 50 + 250×(1/4) = 112.5
    And B 尺寸 = 50 + 250×(2/4) = 175
    And C 尺寸 = 50 + 250×(1/4) = 112.5
```

### 场景 2: flexShrink 在 Flex 中收缩

```
场景 2: 子组件超出 Flex 容器时按 shrink 收缩
  Given 一个 Flex 容器，主轴尺寸 200px
    And 子组件 A 内容尺寸 150px, flexShrink(1)
    And 子组件 B 内容尺寸 150px, flexShrink(2)
  When FlexLayoutAlgorithm 执行布局
  Then overflow = 150 + 150 - 200 = 100
    And totalShrink = 1×150 + 2×150 = 450
    And A 收缩 = 100×(1×150)/450 = 33.3, 最终 116.7
    And B 收缩 = 100×(2×150)/450 = 66.7, 最终 83.3
```

### 场景 3: Row 中 flexShrink 默认不收缩

```
场景 3: Row 容器中子组件超出但不收缩
  Given 一个 Row 容器，主轴尺寸 200px
    And 子组件 A 内容尺寸 150px（未设置 flexShrink）
    And 子组件 B 内容尺寸 150px（未设置 flexShrink）
  When LinearLayoutAlgorithm 执行布局
  Then A 和 B 的 flexShrink 默认值均为 0（isLinearLayoutFeature_=true）
    And totalShrink = 0，不触发收缩
    And A 和 B 保持 150px，溢出容器
```

### 场景 4: layoutWeight 与 flexGrow 互斥

```
场景 4: layoutWeight 模式优先于 flexGrow
  Given 一个 Row 容器，主轴尺寸 300px
    And 子组件 A layoutWeight(1), flexGrow(2)
    And 子组件 B layoutWeight(2), flexGrow(1)
  When FlexLayoutAlgorithm 执行布局
  Then totalFlexWeight = 1 + 2 = 3 > 0
    And 进入 weight 模式，flexGrow 被忽略
    And A 尺寸 = 300×(1/3) = 100
    And B 尺寸 = 300×(2/3) = 200
```

### 场景 5: flexBasis 设置基础尺寸

```
场景 5: flexBasis 覆盖内容尺寸
  Given 一个 Flex 容器，主轴尺寸 400px
    And 子组件 A 内容尺寸 50px, flexBasis(100)
    And 子组件 B 内容尺寸 50px, flexGrow(1)
  When FlexLayoutAlgorithm 执行布局
  Then A 的主轴初始尺寸为 100px（flexBasis 覆盖内容尺寸）
    And remainSpace = 400 - 100 - 50 = 250
    And B 获得 250px 额外空间（flexGrow=1, totalGrow=1）
    And A 最终 100px, B 最终 300px
```

### 场景 6: flexBasis 拒绝百分比

```
场景 6: flexBasis 设置百分比值
  Given 开发者调用 .flexBasis('50%')
  When JS 桥接层解析参数
  Then 解析成功但 Unit 为 PERCENT
    And 被转换为 DimensionUnit::AUTO
    And 子组件使用内容尺寸作为基础尺寸
```

### 场景 7: alignSelf(STRETCH) 二次测量

```
场景 7: alignSelf(STRETCH) 拉伸子组件
  Given 一个 Flex 容器，交叉轴尺寸 200px（水平方向为主轴）
    And 子组件 A 内容高度 50px, alignSelf(ItemAlign.Stretch)
  When FlexLayoutAlgorithm 执行布局
  Then 第一次测量 A 高度为 50px
    And GetSelfAlign 返回 FlexAlign::STRETCH
    And 交叉轴约束被更新为 200px
    And needSecondMeasure = true
    And 第二次测量 A 高度为 200px
```

### 场景 8: alignSelf(BASELINE) 基线对齐

```
场景 8: 多个子组件基线对齐
  Given 一个 Flex 容器（水平方向），交叉轴尺寸足够大
    And 子组件 A 高度 80px, baselineDistance 60px, alignSelf(ItemAlign.Baseline)
    And 子组件 B 高度 40px, baselineDistance 30px, alignSelf(ItemAlign.Baseline)
  When FlexLayoutAlgorithm 执行布局
  Then maxBaselineDistance = max(60, 30) = 60
    And A 交叉轴位置 = 60 - 60 = 0
    And B 交叉轴位置 = 60 - 30 = 30
```

### 场景 9: displayPriority 空间淘汰

```
场景 9: 空间不足时低优先级子组件被隐藏
  Given 一个 Flex 容器，主轴尺寸 200px
    And 子组件 A 尺寸 120px, displayPriority(2)
    And 子组件 B 尺寸 120px, displayPriority(1)
  When FlexLayoutAlgorithm 执行布局
  Then 按 displayPriority 从高到低处理
    And A（优先级 2）先分配 120px，剩余 80px
    And B（优先级 1）需要 120px > 80px
    And B 被设为 SetActive(false), frameSize = {0, 0}
```

### 场景 10: layoutWeight API 12 类型差异

```
场景 10: API < 12 layoutWeight 小数截断
  Given 应用目标 API 版本 < 12
    And 开发者调用 .layoutWeight(1.5)
  When JS 桥接层解析参数
  Then 值被解析为 int32_t, 结果为 1

场景 10b: API ≥ 12 layoutWeight 保留小数
  Given 应用目标 API 版本 ≥ 12
    And 开发者调用 .layoutWeight(1.5)
  When JS 桥接层解析参数
  Then 值被解析为 float, 结果为 1.5
```

### 场景 11: flexShrink undefined 重置行为

```
场景 11: flexShrink(undefined) 触发 Reset
  Given 子组件已设置 .flexShrink(2)
  When 开发者调用 .flexShrink(undefined)
  Then JS 桥接层调用 ViewAbstractModel::ResetFlexShrink()
    And FlexShrink 属性被清除（propFlexShrink.reset()）
    And 恢复为容器默认值（Row/Column: 0, Flex: 1）

场景 11b: flexGrow(undefined) 仅设为 0
  Given 子组件已设置 .flexGrow(2)
  When 开发者调用 .flexGrow(undefined)
  Then JS 桥接层将 value 设为 0.0
    And 调用 ViewAbstractModel::SetFlexGrow(0.0)
    And 属性未被清除，FlexGrow 仍有值（0.0）
```

---

## Spec 自审清单

- [x] 概述表完整（Feature ID、版本、Owner、状态）
- [x] 输入文档引用 design.md
- [x] 6 个用户故事覆盖所有属性
- [x] 每个 US 有编号完整的 AC（AC-X.Y 格式）
- [x] 验收追溯表覆盖所有 AC
- [x] 业务规则含 ADR-F3-1（互斥优先级）和 ADR-F3-2（默认值差异）
- [x] 功能规则有 file:line 引用
- [x] 异常规则覆盖所有边界输入
- [x] 恢复契约覆盖所有属性的 reset 方式
- [x] 验证映射覆盖所有 AC
- [x] API 变更分析包含 ArkTS 和 C-API 双通道
- [x] 兼容性声明包含 API 12 行为差异
- [x] 行为场景使用 Gherkin 格式，覆盖所有关键 AC
- [x] 无 fabricated AC（所有行为来自源码）
- [x] 所有源引用使用 file:line 格式

---

## context-references

### 源码引用

| 文件 | 行号 | 说明 |
|------|------|------|
| `frameworks/core/components_ng/property/flex_property.h` | 36-308 | FlexItemProperty 类定义，包含 FlexGrow/FlexShrink/AlignSelf/FlexBasis/DisplayIndex |
| `frameworks/core/components_ng/property/magic_layout_property.h` | 26-34 | MagicItemProperty 结构，包含 LayoutWeight |
| `frameworks/core/components_ng/base/view_abstract.h` | 197, 509-513, 860, 1087 | Flex 属性 API 声明 |
| `frameworks/core/components_ng/base/view_abstract.cpp` | 8205-8243, 9402-9449, 10239-10250 | Flex 属性 Set/Get 实现 |
| `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | 2827-2853, 3207-3268, 3364-3377 | JS 桥接层参数解析 |
| `frameworks/core/components_ng/layout/layout_property.cpp` | 1647-1718 | Flex 属性 Update 方法（触发 PROPERTY_UPDATE_MEASURE） |
| `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.h` | 27-53, 66-69, 180 | FlexItemProperties/MagicLayoutNode/BaselineProperties 结构 |
| `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 126-155 | UpdateChildLayoutConstrainByFlexBasis |
| `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 260-280 | AddElementIntoMagicNodes |
| `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 414-548 | Weight 模式测量（First/Second/FinalMeasureInWeightMode） |
| `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 619-629 | 模式选择（weight > priority > grow/shrink） |
| `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 717-732 | UpdateFlexProperties（grow/shrink 累加） |
| `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 784-929 | SecondaryMeasureByProperty（空间分配） |
| `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 836-839 | STRETCH 二次测量触发 |
| `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 1605-1616 | GetSelfAlign（alignSelf 解析） |
| `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 1439-1468 | SetCrossPos（交叉轴位置计算） |
| `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp` | 723-774 | Wrap 容器 flexGrow 支持（无 shrink/weight） |
| `frameworks/core/components_ng/pattern/linear_layout/linear_layout_algorithm.h` | 29-41 | LinearLayoutAlgorithm 继承 FlexLayoutAlgorithm，设置 isLinearLayoutFeature_ |
| `interfaces/native/native_node.h` | 1373, 1385, 1397, 1409, 1499 | C-API 枚举定义 |
| `frameworks/core/interfaces/native/node/node_common_modifier.cpp` | 4755-4774, 4938-5003, 5092-5114 | C-API Setter/Resetter/Getter |
| `frameworks/core/interfaces/native/node/node_common_modifier.cpp` | 8103-8130 | C-API Getter 函数 |
| `frameworks/core/interfaces/native/node/node_common_modifier.cpp` | 11479-11509 | C-API 注册（ArkUICommonModifier） |
| `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | — | SDK API 文档交叉验证 |

### Design 文档引用

| 章节 | 说明 |
|------|------|
| design.md → 关键设计决策 → ADR-F3-1 | layoutWeight 与 flexGrow 互斥优先级 |
| design.md → 关键设计决策 → ADR-F3-2 | flexShrink 默认值因父容器而异 |
| design.md → 关键设计决策 → ADR-F3-3 | undefined 重置行为不一致 |
| design.md → 关键设计决策 → ADR-F3-4 | flexBasis 拒绝百分比 + API 12 类型差异 |
| design.md → 关键设计决策 → ADR-F3-5 | STRETCH/BASELINE 二次测量 |
| design.md → 关键设计决策 → ADR-F3-6 | displayPriority 布局淘汰机制 |
