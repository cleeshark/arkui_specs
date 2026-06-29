# 特性规格

> Func-04-03-01-Feat-02 位置属性：固化 position/offset/markAnchor/align/direction 五个核心位置属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 位置属性 (Position Properties) |
| 特性编号 | Func-04-03-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 10/12/21 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/01-layout-attributes/design.md` | Baselined |
| Feat-01 尺寸属性规格 | `specs/04-common-capability/03-common-attributes/01-layout-attributes/Feat-01-size-properties-spec.md` | Baselined |

---

## 用户故事

### US-1: 绝对定位组件

**作为** 应用开发者,
**我想要** 通过 `.position()` 将组件定位到父容器内的指定位置,
**以便** 实现浮动按钮、徽标覆盖等需要脱离正常布局流的 UI 效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.position({x: value, y: value})` THEN 组件脱离正常布局流（outOfLayout），绘制位置为 parentPadding + selfMargin + position(x,y) | 正常 |
| AC-1.2 | WHEN 调用 `.position({x: value, y: value})` THEN 兄弟组件布局不受该组件影响（该组件不占据布局空间） | 正常 |
| AC-1.3 | WHEN value 为 number 类型 THEN 默认单位为 vp | 正常 |
| AC-1.4 | WHEN value 为 string 类型（如 '100px'、'50%'）THEN 按对应单位解析，百分比参照父组件内容区域尺寸 | 正常 |
| AC-1.5 | WHEN value 为 Resource 类型 THEN 从资源文件解析为对应长度值 | 正常 |
| AC-1.6 | WHEN value 为负数 THEN 允许负值（组件可超出父组件可视区域，向左/上偏移） | 异常 |
| AC-1.7 | WHEN 调用 `.position(undefined)` 且 API ≥ 12 THEN ResetPosition：清除 position 属性，组件回到正常布局流 | 异常 |
| AC-1.8 | WHEN 调用 `.position(undefined)` 且 API < 12 THEN SetPosition(0,0)：组件仍脱离布局流，定位在父容器左上角（parentPadding 偏移处） | 异常 |
| AC-1.9 | WHEN 组件同时设置了 position 和 offset THEN position 优先，offset 被忽略 | 正常 |
| AC-1.10 | WHEN 组件设置了 position 且父组件为 Row/Column/Flex THEN 首次设置 position 时，父组件标记 PROPERTY_UPDATE_MEASURE_SELF 以重新计算布局流中剩余子组件的位置 | 正常 |

### US-2: 边缘距离定位

**作为** 应用开发者,
**我想要** 通过 `.position({top, left, bottom, right})` 按边缘距离定位组件,
**以便** 从父容器的任意边缘进行定位（例如"距底部 10vp"）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.position({top: t, left: l})` THEN 组件绘制位置为 parentPaddingTop + selfMarginTop + t (Y 轴) 和 parentPaddingLeft + selfMarginLeft + l (X 轴) | 正常 |
| AC-2.2 | WHEN 调用 `.position({bottom: b})` 且未设置 top THEN 组件 Y 坐标 = parentHeight - selfHeight - parentPaddingBottom - selfMarginBottom - b | 异常 |
| AC-2.3 | WHEN 调用 `.position({right: r})` 且未设置 left THEN 组件 X 坐标 = parentWidth - selfWidth - parentPaddingRight - selfMarginRight - r | 异常 |
| AC-2.4 | WHEN 同时设置 top 和 bottom THEN top 优先，bottom 被忽略 | 正常 |
| AC-2.5 | WHEN 同时设置 left 和 right THEN left 优先，right 被忽略 | 正常 |
| AC-2.6 | WHEN 调用 `.position({top: t, left: l})` (edges 形式) THEN 组件在 Flex/Row/Column 布局中**不脱离布局流**（`frame_node.cpp:3021` 创建 LayoutWrapper 时仅基于 `HasPosition()` 设置 `outOfLayout_` 标志，不含 `HasPositionEdges()`）。组件仍参与 Flex 主轴分配，绘制位置通过 AdjustPaintRect 的 HasPositionEdges 分支单独计算。**注意**：`FrameNode::IsOutOfLayout()` 方法（`frame_node.h:1023`）检查 `HasPosition() \|\| HasPositionEdges()` 两者，与 LayoutWrapper 路径不一致——当前实现即规格，标注此差异 |
| AC-2.7 | WHEN 设置了 edges 形式的 position 后又设置了 x/y 形式的 position THEN x/y 形式生效，edges 被清除（两种形式互斥） | 正常 |
| AC-2.8 | WHEN 设置了 x/y 形式的 position 后又设置了 edges 形式的 position THEN edges 形式生效，x/y 被清除 | 正常 |

### US-3: 本地化边缘定位（RTL）

**作为** 应用开发者,
**我想要** 通过 `.position({start, end, top, bottom})` 使用方向感知的边缘定位,
**以便** 在 LTR 和 RTL 布局中自动镜像定位。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 布局方向为 LTR 且调用 `.position({start: s})` THEN start 映射为 left：组件 X = parentPaddingLeft + selfMarginLeft + s | 正常 |
| AC-3.2 | WHEN 布局方向为 RTL 且调用 `.position({start: s})` THEN start 映射为 right：组件 X = parentWidth - selfWidth - parentPaddingRight - selfMarginRight - s | 正常 |
| AC-3.3 | WHEN 布局方向为 LTR 且调用 `.position({end: e})` THEN end 映射为 right | 正常 |
| AC-3.4 | WHEN 布局方向为 RTL 且调用 `.position({end: e})` THEN end 映射为 left | 正常 |
| AC-3.5 | WHEN 使用 LocalizedEdges 形式（LengthMetrics 类型）THEN needPositionLocalizedEdges 标记为 true，方向变更时自动重新解析 start/end 到 left/right | 正常 |

### US-4: 相对偏移组件

**作为** 应用开发者,
**我想要** 通过 `.offset()` 在布局位置基础上追加偏移,
**以便** 微调组件位置而不影响布局流。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.offset({x: dx, y: dy})` THEN 组件绘制位置 = 布局计算位置 + offset(dx, dy) | 正常 |
| AC-4.2 | WHEN 设置 offset THEN 组件仍然参与正常布局流（outOfLayout=false），兄弟组件按 offset 不存在的方式布局 | 正常 |
| AC-4.3 | WHEN value 为 number 类型 THEN 默认单位为 vp | 正常 |
| AC-4.4 | WHEN value 为负数 THEN 允许负值（向左/上偏移） | 异常 |
| AC-4.5 | WHEN 调用 `.offset(undefined)` 或非法值 THEN 设置为 offset(0, 0)（不清除属性，仅归零） | 异常 |
| AC-4.6 | WHEN 调用 `.offset({x: dx, y: dy})` 且 API < 10 THEN offset 值自动叠加父组件 padding（offsetX += parentPaddingLeft, offsetY += parentPaddingTop） | 边界 |
| AC-4.7 | WHEN 调用 `.offset({x: dx, y: dy})` 且 API ≥ 10 THEN offset 纯粹相对布局计算位置，不叠加父组件 padding | 正常 |
| AC-4.8 | WHEN offset 值为百分比（如 '50%'）THEN 百分比参照父组件内容区域尺寸 | 正常 |

### US-5: 边缘距离偏移

**作为** 应用开发者,
**我想要** 通过 `.offset({top, left, bottom, right})` 使用边缘方向偏移,
**以便** 按方向语义微调组件位置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.offset({top: t})` THEN 组件 Y 方向追加 +t 偏移 | 正常 |
| AC-5.2 | WHEN 调用 `.offset({left: l})` THEN 组件 X 方向追加 +l 偏移 | 正常 |
| AC-5.3 | WHEN 调用 `.offset({bottom: b})` 且未设置 top THEN 组件 Y 方向追加 -b 偏移（向上移动） | 异常 |
| AC-5.4 | WHEN 调用 `.offset({right: r})` 且未设置 left THEN 组件 X 方向追加 -r 偏移（向左移动） | 异常 |
| AC-5.5 | WHEN 同时设置 top 和 bottom THEN top 优先，bottom 被忽略 | 正常 |
| AC-5.6 | WHEN 同时设置 left 和 right THEN left 优先，right 被忽略 | 正常 |
| AC-5.7 | WHEN 设置了 edges 形式的 offset 后又设置了 x/y 形式的 offset THEN x/y 形式生效，edges 被清除（两种形式互斥） | 正常 |

### US-6: 本地化边缘偏移（RTL）

**作为** 应用开发者,
**我想要** 通过 `.offset({start, end, top, bottom})` 使用方向感知的偏移,
**以便** 在 LTR 和 RTL 布局中自动镜像偏移方向。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 布局方向为 LTR 且调用 `.offset({start: s})` THEN start 映射为 left，组件追加 +s 的 X 偏移 | 正常 |
| AC-6.2 | WHEN 布局方向为 RTL 且调用 `.offset({start: s})` THEN start 映射为 right，组件追加 -s 的 X 偏移 | 正常 |
| AC-6.3 | WHEN 布局方向为 LTR 且调用 `.offset({end: e})` THEN end 映射为 right，组件追加 -e 的 X 偏移 | 正常 |
| AC-6.4 | WHEN 布局方向为 RTL 且调用 `.offset({end: e})` THEN end 映射为 left，组件追加 +e 的 X 偏移 | 正常 |
| AC-6.5 | WHEN 使用 LocalizedEdges 形式 THEN needOffsetLocalizedEdges 标记为 true | 正常 |

### US-7: 锚点偏移

**作为** 应用开发者,
**我想要** 通过 `.markAnchor()` 调整组件的定位锚点,
**以便** 实现以组件内部某个点为基准的定位（如以中心点定位而非左上角）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.markAnchor({x: ax, y: ay})` THEN 组件绘制位置在最终计算时减去锚点偏移：finalX -= anchorX, finalY -= anchorY | 正常 |
| AC-7.2 | WHEN markAnchor 设置后 THEN 仅影响视觉绘制位置（paintRect），不影响布局盒（frameRect），兄弟组件按 markAnchor 不存在的方式布局 | 正常 |
| AC-7.3 | WHEN markAnchor 值为百分比 THEN 百分比参照组件自身尺寸（非父组件） | 正常 |
| AC-7.4 | WHEN markAnchor 与 position 同时设置 THEN 最终位置 = position 计算结果 - anchor | 正常 |
| AC-7.5 | WHEN markAnchor 与 offset 同时设置 THEN 最终位置 = 布局位置 + offset - anchor | 正常 |
| AC-7.6 | WHEN markAnchor 值为负数 THEN 允许负值（向相反方向偏移锚点） | 异常 |
| AC-7.7 | WHEN 调用 `.markAnchor(undefined)` 或非法值 THEN 设置为 markAnchor(0, 0) | 异常 |
| AC-7.8 | WHEN value 为 number 类型 THEN 默认单位为 vp | 正常 |

### US-8: 锚点本地化（RTL）

**作为** 应用开发者,
**我想要** 通过 `.markAnchor({start, top})` 使用方向感知的锚点,
**以便** 在 RTL 布局中自动镜像锚点方向。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 布局方向为 LTR 且调用 `.markAnchor({start: s, top: t})` THEN anchorX = s（正值，向右偏移锚点） | 正常 |
| AC-8.2 | WHEN 布局方向为 RTL 且调用 `.markAnchor({start: s, top: t})` THEN anchorX = -s（取反，向左偏移锚点） | 正常 |
| AC-8.3 | WHEN 使用 start 形式 THEN markAnchorStart_ 存储原始值，布局方向变更时自动重新解析 | 正常 |

### US-9: 内容对齐

**作为** 应用开发者,
**我想要** 通过 `.align()` 设置容器内子组件的对齐方式,
**以便** 控制子组件在容器内容区域中的位置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 调用 `.align(Alignment.TopStart)` THEN 子组件对齐到容器内容区域的左上角 | 正常 |
| AC-9.2 | WHEN 调用 `.align(Alignment.Center)` THEN 子组件对齐到容器内容区域的正中心 | 正常 |
| AC-9.3 | WHEN 调用 `.align(Alignment.BottomEnd)` THEN 子组件对齐到容器内容区域的右下角 | 正常 |
| AC-9.4 | WHEN 未设置 align THEN 默认对齐方式为 Alignment.Center | 异常 |
| AC-9.5 | WHEN 容器有多个子组件 THEN align 应用于每个子组件（所有子组件使用相同对齐方式） | 正常 |
| AC-9.6 | WHEN 子组件尺寸等于容器内容区域尺寸 THEN align 无可见效果（偏移为 0） | 正常 |
| AC-9.7 | WHEN 子组件为 outOfLayout（通过 position(x/y) 设置，不含 position(edges)）THEN align 不影响该子组件的位置 | 正常 |
| AC-9.8 | WHEN 调用 `.align(undefined)` 且 API ≥ 10 THEN 重置为默认值 Alignment.Center | 异常 |
| AC-9.9 | WHEN align 变更 THEN 触发 PROPERTY_UPDATE_LAYOUT（仅重新布局，不重新测量） | 正常 |

### US-10: 本地化对齐（RTL）

**作为** 应用开发者,
**我想要** 通过本地化对齐字符串（如 'top_start'、'center'）设置方向感知对齐,
**以便** 在 RTL 布局中自动镜像对齐方向。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 使用本地化对齐字符串（IsMirrorable=true）且布局方向为 RTL THEN TOP_START 映射为 TOP_RIGHT（而非 TOP_LEFT） | 正常 |
| AC-10.2 | WHEN 使用数字枚举（IsMirrorable=false）THEN 不进行 RTL 镜像，TOP_LEFT 始终为左上角 | 正常 |
| AC-10.3 | WHEN 布局方向为 RTL 且使用本地化对齐 THEN LEFT 映射为 RIGHT，RIGHT 映射为 LEFT，CENTER 保持不变 | 正常 |

### US-11: 布局方向控制

**作为** 应用开发者,
**我想要** 通过 `.direction()` 控制组件的布局方向,
**以便** 在 RTL 语言环境中正确排列 UI 组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-11.1 | WHEN 调用 `.direction(Direction.Ltr)` 且父组件为 Row/Flex(ROW) THEN 子组件从左到右排列 | 正常 |
| AC-11.2 | WHEN 调用 `.direction(Direction.Rtl)` 且父组件为 Row/Flex(ROW) THEN 子组件从右到左排列 | 正常 |
| AC-11.3 | WHEN 调用 `.direction(Direction.Rtl)` 且父组件为 Column THEN 子组件排列方向不受影响（Column 主轴为垂直方向） | 正常 |
| AC-11.4 | WHEN 调用 `.direction(Direction.Auto)` THEN 方向解析为系统语言环境：RTL 语言环境解析为 RTL，否则解析为 LTR | 正常 |
| AC-11.5 | WHEN direction 为 AUTO 且父组件设置了 direction(RTL) THEN 本组件的 AUTO 仍然解析为系统语言环境，**不继承**父组件的 direction 设置（⚠️ 重要：AUTO 不等于 INHERIT） | 正常 |
| AC-11.6 | WHEN direction 变更 THEN 触发 PROPERTY_UPDATE_MEASURE（需要重新测量，因为子组件排列方向变化） | 正常 |
| AC-11.7 | WHEN 调用 `.direction(undefined)` 且 API ≥ 10 THEN 重置为 Direction.Auto | 异常 |
| AC-11.8 | WHEN direction(RTL) 设置后 THEN 影响所有使用 start/end 的本地化属性：position edges、offset edges、markAnchor start、localized alignment | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.10 | R-1, R-2, R-13~R-17, R-46~R-48 | 已有实现 | 单测/XTS | `test/unittest/core/` |
| AC-2.1~2.8 | R-3, R-18~R-21 | 已有实现 | 单测 | 同上 |
| AC-3.1~3.5 | R-4, R-22~R-23 | 已有实现 | 单测 | 同上 |
| AC-4.1~4.8 | R-5, R-24~R-27, R-49~R-50 | 已有实现 | 单测 | 同上 |
| AC-5.1~5.7 | R-6, R-28~R-30 | 已有实现 | 单测 | 同上 |
| AC-6.1~6.5 | R-7, R-31 | 已有实现 | 单测 | 同上 |
| AC-7.1~7.8 | R-8, R-32~R-35 | 已有实现 | 单测 | 同上 |
| AC-8.1~8.3 | R-9, R-36 | 已有实现 | 单测 | 同上 |
| AC-9.1~9.9 | R-10, R-37~R-40 | 已有实现 | 单测 | 同上 |
| AC-10.1~10.3 | R-11, R-41 | 已有实现 | 单测 | 同上 |
| AC-11.1~11.8 | R-12, R-42~R-45, R-51 | 已有实现 | 单测 | 同上 |
| AC-1.1, AC-1.2, AC-1.3 | R-1, R-2, R-13~R-17 | SpecTest 回填用例 | HostPreview | 见 SpecTest用例追溯 表格 |
| AC-4.1, AC-4.2 | R-5, R-24~R-27 | SpecTest 回填用例 | HostPreview | 见 SpecTest用例追溯 表格 |
| AC-7.1 | R-8, R-32~R-35 | SpecTest 回填用例 | HostPreview | 见 SpecTest用例追溯 表格 |
| AC-2.2, AC-2.3 | R-3, R-18~R-21 | SpecTest 回填用例 | HostPreview | 见 SpecTest用例追溯 表格 |
| AC-9.1, AC-9.2, AC-9.3, AC-9.4 | R-10, R-37~R-40 | SpecTest 回填用例 | HostPreview | 见 SpecTest用例追溯 表格 |

### SpecTest 用例追溯

| Case ID | 对应 AC |
|---------|---------|
| case-001-position-xy-basic | AC-1.1, AC-1.2, AC-1.3 |
| case-002-position-out-of-layout | AC-1.1, AC-1.2 |
| case-003-offset-basic | AC-4.1, AC-4.2 |
| case-004-mark-anchor-basic | AC-7.1 |
| case-001-align-default-center | AC-9.2, AC-9.4 |
| case-002-align-top-start | AC-9.1 |
| case-003-align-bottom-end | AC-9.3 |
| case-004-position-bottom-right | AC-2.2, AC-2.3 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 适用于所有 FrameNode | 所有组件均继承 CommonMethod，支持 position/offset/markAnchor/align/direction 属性 | — | AC-1.1~AC-11.8 |
| R-2 | 行为 | FrameNode::IsOutOfLayout 检查两者，但 LayoutWrapper::outOfLayout_ 仅由 HasPosition 设置 | position(x/y) 使组件脱离正常布局流（outOfLayout=true），类似 CSS position:absolute；position(edges) 在 Flex/Row/Column 中不脱离布局流（LayoutWrapper 路径差异） | — | AC-1.1, AC-1.2, AC-2.6 |
| R-3 | 行为 | Position 和 PositionEdges 互斥存储，后设置覆盖前设置 | position 支持三种互斥的输入形式：x/y 坐标、edges 边缘距离、localizedEdges 本地化边缘 | — | AC-2.7, AC-2.8 |
| R-4 | 行为 | LTR: start→left, end→right; RTL: start→right, end→left | 本地化边缘（start/end）根据布局方向解析为物理方向（left/right） | — | AC-3.1~3.4 |
| R-5 | 行为 | offset 不影响兄弟组件布局 | offset 保持组件在正常布局流中（outOfLayout=false），是布局后的位移 | — | AC-4.1, AC-4.2 |
| R-6 | 行为 | 同时设置时，top 生效 bottom 忽略，left 生效 right 忽略 | offset edges 中 top/left 优先于 bottom/right | — | AC-5.5, AC-5.6 |
| R-7 | 行为 | 依赖 CheckPositionOrOffsetLocalizedEdges | offset 本地化边缘遵循与 position 相同的 start/end → left/right 映射规则 | — | AC-6.1~6.4 |
| R-8 | 行为 | 兄弟组件按 markAnchor 不存在的方式布局 | markAnchor 仅影响视觉绘制位置（paintRect），不影响布局盒（frameRect） | — | AC-7.2 |
| R-9 | 行为 | CheckMarkAnchorPosition: RTL 时 x = -start | markAnchor 的 start 形式在 RTL 方向下取反 | — | AC-8.1, AC-8.2 |
| R-10 | 行为 | 应用于 BoxLayoutAlgorithm::PerformLayout 中的每个子组件 | align 控制容器内所有子组件的对齐方式 | — | AC-9.5 |
| R-11 | 行为 | 使用 GetAlignPositionWithDirection 进行镜像 | 本地化对齐（IsMirrorable=true）在 RTL 方向下镜像 LEFT↔RIGHT | — | AC-10.1~10.3 |
| R-12 | 行为 | GetNonAutoLayoutDirection 读取 AceApplicationInfo::IsRightToLeft() | direction(AUTO) 解析为系统语言环境，不继承父组件 direction | — | AC-11.4, AC-11.5 |
| R-13 | 行为 | 调用 SetPosition | position(x/y) 存储在 RenderContext::RenderPositionProperty::Position，设置时清除 PositionEdges | RenderContext | AC-1.1, AC-2.7 |
| R-14 | 行为 | 修改 position 值 | position 变更不直接触发 PropertyChangeFlag，而是通过 OnPositionUpdate 回调调用 SetPositionToRSNode 更新渲染树 | RenderContext | AC-1.1 |
| R-15 | 行为 | 子组件从 inFlow → outOfLayout 切换 | 首次设置 position 时，CheckIfParentNeedMarkDirty 标记父组件（Row/Column/Flex）为 PROPERTY_UPDATE_MEASURE_SELF | FrameNode | AC-1.10 |
| R-16 | 行为 | \ | FrameNode::IsOutOfLayout() 返回 HasPosition() \ | HasPositionEdges()，不检查 HasOffset | 布局算法判断是否跳过子组件 |
| R-17 | 行为 | AdjustPaintRect 渲染阶段 | position(x/y) 计算公式：paintRect.X = parentPaddingLeft + selfMarginLeft + position.x - anchorX; Y 轴同理 | RosenRenderContext | AC-1.1 |
| R-18 | 行为 | 调用 SetPositionEdges | position(edges) 存储在 RenderContext::RenderPositionProperty::PositionEdges，设置时清除 Position | RenderContext | AC-2.6, AC-2.8 |
| R-19 | 行为 | GetRectOffsetWithPositionEdges | edges 定位中 top 优先于 bottom：当 top 有值时忽略 bottom | RosenRenderContext | AC-2.4 |
| R-20 | 行为 | GetRectOffsetWithPositionEdges | edges 定位中 left 优先于 right：当 left 有值时忽略 right | RosenRenderContext | AC-2.5 |
| R-21 | 行为 | GetRectOffsetWithPositionEdges | bottom/right 定位公式：Y = parentH - selfH - parentPaddingBottom - selfMarginBottom - edges.bottom | RosenRenderContext | AC-2.2, AC-2.3 |
| R-22 | 行为 | 设置 LocalizedEdges 时和方向变更时 | CheckPositionOrOffsetLocalizedEdges 将 start/end 根据 layoutDirection 映射为 left/right | ViewAbstract | AC-3.1~3.4 |
| R-23 | 行为 | 使用 LocalizedEdges 形式设置 position | needPositionLocalizedEdges_ 标记存储在 LayoutProperty 中，用于标识是否需要方向感知重新解析 | LayoutProperty | AC-3.5 |
| R-24 | 行为 | 调用 SetOffset | offset(x/y) 存储在 RenderContext::RenderPositionProperty::Offset，设置时清除 OffsetEdges | RenderContext | AC-4.1, AC-5.7 |
| R-25 | 行为 | AdjustPaintRect 渲染阶段 | offset 计算公式：paintRect.X = layoutX + offset.x - anchorX; Y 轴同理 | RosenRenderContext | AC-4.1 |
| R-26 | 行为 | MinPlatformVersion < 10 | API < 10: offset 叠加父 padding：offset += OffsetT(parentPaddingLeft, parentPaddingTop) | RosenRenderContext | AC-4.6 |
| R-27 | 行为 | MinPlatformVersion ≥ 10 | API ≥ 10: offset 不叠加父 padding，纯粹相对布局位置 | RosenRenderContext | AC-4.7 |
| R-28 | 行为 | GetRectOffsetWithOffsetEdges | offset edges 中 top 转为正 Y 偏移，bottom 转为负 Y 偏移 | RosenRenderContext | AC-5.1, AC-5.3 |
| R-29 | 行为 | GetRectOffsetWithOffsetEdges | offset edges 中 left 转为正 X 偏移，right 转为负 X 偏移 | RosenRenderContext | AC-5.2, AC-5.4 |
| R-30 | 行为 | GetRectOffsetWithOffsetEdges | offset edges 中 top 优先于 bottom，left 优先于 right | RosenRenderContext | AC-5.5, AC-5.6 |
| R-31 | 行为 | 使用 LocalizedEdges 形式设置 offset | needOffsetLocalizedEdges_ 标记存储在 LayoutProperty 中 | LayoutProperty | AC-6.5 |
| R-32 | 行为 | 调用 MarkAnchor | markAnchor 存储在 RenderContext::RenderPositionProperty::Anchor，类型为 OffsetT<Dimension> | RenderContext | AC-7.1 |
| R-33 | 行为 | AdjustPaintRect 中所有定位分支 | markAnchor 以减法应用于最终位置：finalX -= anchorX, finalY -= anchorY | RosenRenderContext | AC-7.1 |
| R-34 | 行为 | AdjustPaintRect 获取 anchor 时 | markAnchor 百分比参照组件自身尺寸（rect.Width()/rect.Height()），非父组件尺寸 | RosenRenderContext | AC-7.3 |
| R-35 | 行为 | RenderContext 回调 | markAnchor 变更触发 OnAnchorUpdate → SetPositionToRSNode，不触发 PROPERTY_UPDATE_MEASURE/LAYOUT | RosenRenderContext | AC-7.2 |
| R-36 | 行为 | CheckMarkAnchorPosition(layoutDirection) | markAnchor start 形式：LTR 时 x = start，RTL 时 x = -start | LayoutProperty | AC-8.1, AC-8.2 |
| R-37 | 行为 | 调用 SetAlign | align 存储在 LayoutProperty::PositionProperty::Alignment（枚举）或 LocalizedAlignment（字符串） | LayoutProperty | AC-9.1~9.3 |
| R-38 | 行为 | UpdateAlignment | align 变更触发 PROPERTY_UPDATE_LAYOUT（不触发 MEASURE） | LayoutProperty | AC-9.9 |
| R-39 | 行为 | Layout 阶段 | BoxLayoutAlgorithm::PerformLayout 使用 GetAlignPosition 计算子组件偏移：offset.X = (1 + horizontal) * (parentW - childW) / 2 | BoxLayoutAlgorithm | AC-9.1~9.3 |
| R-40 | 行为 | 未设置 align 时 | align 默认值为 Alignment::CENTER（horizontal=0, vertical=0） | BoxLayoutAlgorithm | AC-9.4 |
| R-41 | 行为 | 布局阶段读取对齐方式 | IsMirrorable=true 时使用 LocalizedAlignment 字符串映射；IsMirrorable=false 时直接使用 Alignment 枚举 | BoxLayoutAlgorithm | AC-10.1, AC-10.2 |
| R-42 | 行为 | 调用 SetLayoutDirection | direction 存储在 LayoutProperty::layoutDirection_（std::optional<TextDirection>） | LayoutProperty | AC-11.1~11.4 |
| R-43 | 行为 | UpdateLayoutDirection | direction 变更触发 PROPERTY_UPDATE_MEASURE | LayoutProperty | AC-11.6 |
| R-44 | 行为 | 解析 AUTO 值 | GetNonAutoLayoutDirection: AUTO → AceApplicationInfo::IsRightToLeft() ? RTL : LTR | LayoutProperty | AC-11.4 |
| R-45 | 行为 | Flex/Row 布局 | direction(RTL) 影响 FlexLayoutAlgorithm::IsStartTopLeft：FlexDirection::ROW 时 RTL 导致子组件从右到左排列 | FlexLayoutAlgorithm | AC-11.1, AC-11.2 |
| R-46 | 异常 | position 传入 undefined/非法值且 target API ≥ 12 | position(undefined) 重置（API ≥ 12） | ResetPosition：清除 Position 和 PositionEdges，组件回到布局流（outOfLayout=false） | AC-1.7 |
| R-47 | 异常 | position 传入 undefined/非法值且 target API < 12 | position(undefined) 归零（API < 12） | SetPosition(0.0_vp, 0.0_vp)：组件仍脱离布局流，定位在 (0,0) | AC-1.8 |
| R-48 | 异常 | ResetPosition 且父组件为 Column/Row/Flex/Stack | ResetPosition 时的父组件标记 | 子节点标记 PROPERTY_UPDATE_MEASURE（因为子组件从 outOfLayout 回到布局流） | AC-1.7 |
| R-49 | 异常 | offset 传入 undefined/非法值 | offset(undefined) 归零 | SetOffset(0.0_vp, 0.0_vp)：offset 始终保持属性存在，仅归零 | AC-4.5 |
| R-50 | 异常 | API < 10 环境下设置 offset | offset API < 10 包含父 padding | offset 值自动叠加父组件 padding(left, top) | AC-4.6 |
| R-51 | 异常 | 子组件 direction 为 AUTO 且父组件为 RTL | direction AUTO 不继承 | 子组件 AUTO 解析为系统语言环境，不继承父组件 RTL | AC-11.5 |
| R-52 | 异常 | markAnchor 传入 undefined/非法值 | markAnchor(undefined) 归零 | MarkAnchor(0.0_vp, 0.0_vp)：锚点归零 | AC-7.7 |
| R-53 | 恢复 | position(undefined) API ≥ 12 | ResetPosition 清除属性 | 组件回到正常布局流，由父容器布局算法决定位置 | — |
| R-54 | 恢复 | offset(undefined) | SetOffset(0, 0) | 组件无额外偏移，按布局计算位置渲染 | — |
| R-55 | 恢复 | markAnchor(undefined) | MarkAnchor(0, 0) | 锚点归零，不影响位置 | — |
| R-56 | 恢复 | align(undefined) API ≥ 10 | 重置为 Alignment::CENTER | 子组件居中对齐 | — |
| R-57 | 恢复 | direction(undefined) API ≥ 10 | 重置为 TextDirection::AUTO | 方向解析为系统语言环境 | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-13~R-17, AC-1.1~1.10 | 单测 | position x/y 定位正确、outOfLayout 生效 |
| VM-2 | R-18~R-21, AC-2.1~2.8 | 单测 | position edges 定位正确、top/left 优先级 |
| VM-3 | R-22~R-23, AC-3.1~3.5 | 单测 | LocalizedEdges start/end 方向映射正确 |
| VM-4 | R-24~R-27, AC-4.1~4.8 | 单测 | offset 偏移正确、API 版本差异 |
| VM-5 | R-28~R-30, AC-5.1~5.7 | 单测 | offset edges 正/负偏移方向正确 |
| VM-6 | R-31, AC-6.1~6.5 | 单测 | offset LocalizedEdges 方向映射正确 |
| VM-7 | R-32~R-35, AC-7.1~7.8 | 单测 | markAnchor 减法应用、不影响布局盒 |
| VM-8 | R-36, AC-8.1~8.3 | 单测 | markAnchor start RTL 取反 |
| VM-9 | R-37~R-40, AC-9.1~9.9 | 单测 | align 对齐计算公式正确、默认 CENTER |
| VM-10 | R-41, AC-10.1~10.3 | 单测 | 本地化对齐 RTL 镜像正确 |
| VM-11 | R-42~R-45, AC-11.1~11.8 | 单测 | direction 影响 Flex/Row 排列、AUTO 解析 |
| VM-12 | R-46~R-47 | 单测 | position undefined 处理（区分 API 版本） |
| VM-13 | 全量 | XTS/集成 | 端到端布局位置渲染正确 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | @since | 权限要求 |
|----------|------|------|--------|----------|
| `position(value: Position \| Edges \| LocalizedEdges \| undefined): T` | Public | 设置绝对定位 | 7 | - |
| `offset(value: Position \| Edges \| LocalizedEdges \| undefined): T` | Public | 设置相对偏移 | 7 | - |
| `markAnchor(value: Position \| LocalizedPosition \| undefined): T` | Public | 设置锚点偏移 | 7 | - |
| `align(alignment: Alignment \| undefined): T` | Public | 设置内容对齐 | 7 | - |
| `direction(value: Direction): T` | Public | 设置布局方向 | 7 | - |

**C-API (NDK) 接口：**

| 属性枚举 | 值格式 | 功能 | @since |
|----------|--------|------|--------|
| `NODE_POSITION` | `.value[0].f32` (x vp), `.value[1].f32` (y vp) | 设置 x/y 绝对定位 | 12 |
| `NODE_POSITION_EDGES = 107` | `.object` (ArkUI_PositionEdges) | 设置 edges 绝对定位 | 21 |
| `NODE_OFFSET` | `.value[0].f32` (x vp), `.value[1].f32` (y vp) | 设置 x/y 偏移 | 12 |
| `NODE_MARK_ANCHOR` | `.value[0].f32` (x vp), `.value[1].f32` (y vp) | 设置锚点 | 12 |
| `NODE_ALIGNMENT` | `.value[0].i32` (ArkUI_Alignment) | 设置对齐方式 | 12 |
| `NODE_DIRECTION` | `.value[0].i32` (ArkUI_Direction) | 设置布局方向 | 12 |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `Position` | `{ x?: Length; y?: Length }` | `common.d.ts` |
| `Edges` | `{ top?: Dimension; left?: Dimension; bottom?: Dimension; right?: Dimension }` | `common.d.ts` |
| `LocalizedEdges` | `{ top?: LengthMetrics; start?: LengthMetrics; bottom?: LengthMetrics; end?: LengthMetrics }` | `common.d.ts` |
| `LocalizedPosition` | `{ start?: LengthMetrics; top?: LengthMetrics }` | `common.d.ts` |
| `Alignment` | `enum { TOP_START=0, TOP=1, TOP_END=2, START=3, CENTER=4, END=5, BOTTOM_START=6, BOTTOM=7, BOTTOM_END=8 }` | `common.d.ts` |
| `Direction` | `enum { Ltr, Rtl, Auto }` | `common.d.ts` |
| `ArkUI_Alignment` | C enum, 9 values | `native_type.h:446` |
| `ArkUI_Direction` | `{ LTR=0, RTL=1, AUTO=3 }` (注意 AUTO=3 非 2) | `native_type.h:1790` |
| `ArkUI_PositionEdges` | `{ top, left, bottom, right }` (ArkUI_OptionalFloat) | `node_extened.h:109` |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

---

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:**
  - **API 10**: offset 不再自动叠加父组件 padding。API < 10 的 offset 值包含 parentPadding(left, top)，API ≥ 10 的 offset 纯粹相对布局位置。通过 `PipelineBase::GetCurrentContext()->GetMinPlatformVersion() < PLATFORM_VERSION_TEN` 守护
  - **API 10**: align(undefined) 和 direction(undefined) 重置为默认值。API < 10 行为未定义
  - **API 12**: position(undefined) 从 SetPosition(0,0)（仍脱离布局流）变更为 ResetPosition（回到布局流）。通过 `GreatOrEqualTargetAPIVersion(PlatformVersion::VERSION_TWELVE)` 守护。**此变更影响重大——同一组件在不同 API 版本下 position(undefined) 后的布局行为完全不同**
  - **API 12**: position/offset 的维度解析从 ParseJsDimension 升级为 ParseJsDimensionNG（更严格的参数校验）
  - **API 21**: C-API 新增 NODE_POSITION_EDGES 枚举和 ArkUI_PositionEdges 结构体
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** @since 7 为基础，@since 12 标注 C-API 新增，@since 21 标注 edges C-API

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| position/offset/markAnchor 存储在 RenderContext | 不参与约束计算管线，仅影响最终绘制位置。变更不触发 Measure | AC-1.1, AC-4.1, AC-7.1 |
| align 存储在 LayoutProperty | 参与 Layout 阶段计算，变更触发 PROPERTY_UPDATE_LAYOUT（不触发 Measure） | AC-9.9 |
| direction 存储在 LayoutProperty | 变更触发 PROPERTY_UPDATE_MEASURE（需要重新测量） | AC-11.6 |
| Position 和 PositionEdges 互斥存储 | 设置 x/y 形式时清除 edges 形式，反之亦然 | AC-2.7, AC-2.8 |
| Offset 和 OffsetEdges 互斥存储 | 同上 | AC-5.7 |
| outOfLayout 检查路径不一致 | FrameNode::IsOutOfLayout() 检查 HasPosition \|\| HasPositionEdges，但 LayoutWrapper 创建时（frame_node.cpp:3021）仅基于 HasPosition 设置 outOfLayout_ 标志。Flex 算法读 LayoutWrapper 路径，因此 position(edges) 在 Flex/Row/Column 中实际不脱离布局流 | AC-1.2, AC-2.6, AC-4.2 |
| 绘制优先级 position > offset | AdjustPaintRect 按 position → positionEdges → offset → offsetEdges 顺序判断 | AC-1.9 |
| markAnchor 不影响布局盒 | 仅修改 paintRect，不修改 frameRect | AC-7.2 |
| direction(AUTO) 不继承 | 每个组件独立解析 AUTO，读取系统语言环境 | AC-11.5 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | position/offset/markAnchor 变更不触发 Measure 管线，仅更新 RS 节点 bounds（O(1) 操作） | benchmark | — |
| 性能 | align 变更仅触发 Layout（不触发 Measure），减少不必要的测量 | benchmark | — |
| 内存 | RenderPositionProperty 使用 std::optional 避免无用分配 | hidumper | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | position 脱离布局流后组件仍在辅助功能树中，但屏幕位置可能与逻辑顺序不一致 | position 定位的组件 |
| RTL/国际化 | 是 | direction(RTL) 影响 Row/Flex 排列方向、position/offset/markAnchor 的 start/end 映射、align 的 LEFT↔RIGHT 镜像 | 全部本地化属性 |
| 大字体 | 是 | position/offset 使用 FP 单位时受大字体缩放影响 | FP 单位场景 |
| 深色模式 | N/A | 位置属性与颜色无关 | — |
| 多窗口/分屏 | 是 | 窗口尺寸变化导致 parentConstraint 变化，影响 position/offset 百分比计算和 edges 定位 | 百分比值场景 |
| 版本升级 | 是 | API 10 offset padding 行为变更、API 12 position(undefined) 重置行为变更——需通过 API 版本守护 | AC-1.7, AC-1.8, AC-4.6, AC-4.7 |
| 生态兼容 | 是 | C-API (NDK) 提供等效接口，行为应与 ArkTS 一致 | 全部 C-API 属性 |
| 动画 | 是 | position/offset/markAnchor 可参与属性动画（存储在 RenderContext，通过 RS 节点属性动画驱动） | 动画场景 |

---

## 行为场景

```gherkin
Feature: 位置属性
  作为 应用开发者
  我想要 通过声明式 API 控制组件的绝对定位、相对偏移、锚点、对齐方式和布局方向
  以便 实现精确的 UI 布局定位

  # ─── position 基础 ─────────────────────────────────

  Scenario: 设置绝对定位（x/y）
    Given 一个 Stack 容器宽 300vp 高 500vp
    And 一个 Text 子组件
    When 设置 Text.position({x: 10, y: 20})
    Then Text 绘制位置 X = parentPaddingLeft + selfMarginLeft + 10vp
    And Text 绘制位置 Y = parentPaddingTop + selfMarginTop + 20vp
    And Text 脱离布局流，不影响其他子组件的布局位置

  Scenario: position 脱离布局流
    Given 一个 Column 容器
    And 三个 Text 子组件 A、B、C
    When Text B 设置 .position({x: 0, y: 0})
    Then A 和 C 按正常 Column 布局排列（B 不占据空间）
    And B 定位在 Column 左上角

  Scenario: position(undefined) 重置（API >= 12）
    Given 目标 API 版本 >= 12
    And 一个 Text 子组件已设置 position({x: 10, y: 20})
    When 设置 Text.position(undefined)
    Then Text 回到正常布局流（outOfLayout=false）
    And 兄弟组件按 Text 存在于布局流的方式重新排列

  Scenario: position(undefined) 归零（API < 12）
    Given 目标 API 版本 < 12
    And 一个 Text 子组件已设置 position({x: 10, y: 20})
    When 设置 Text.position(undefined)
    Then Text 仍脱离布局流
    And Text 定位在 (0, 0)

  # ─── position edges 定位 ─────────────────────────────

  Scenario: position(edges) 在 Flex 中不脱离布局流
    Given 一个 Row 容器，宽 300vp
    And 子组件 A 宽 100vp
    And 子组件 B 宽 100vp, 设置 .position({top: 10, left: 20})
    And 子组件 C 宽 100vp
    When Row 布局算法执行
    Then B 仍参与 Row 主轴分配（不脱离布局流）
    And A、B、C 各占 100vp（B 未被跳过）
    And B 的绘制位置通过 AdjustPaintRect 的 HasPositionEdges 分支计算

  Scenario: 从底部右侧定位
    Given 一个 Stack 容器宽 300vp 高 500vp
    And 一个 Button 子组件宽 80vp 高 40vp
    When 设置 Button.position({bottom: 10, right: 10})
    Then Button 绘制 Y = 500 - 40 - 10 = 450vp（距底部 10vp）
    And Button 绘制 X = 300 - 80 - 10 = 210vp（距右侧 10vp）

  Scenario: top 优先于 bottom
    Given 一个 Stack 容器高 500vp
    And 一个 Text 子组件
    When 设置 Text.position({top: 10, bottom: 20})
    Then Text 绘制 Y = parentPaddingTop + selfMarginTop + 10（top 生效）
    And bottom 值被忽略

  Scenario: edges 和 x/y 互斥
    Given 一个 Text 子组件已设置 .position({x: 10, y: 20})
    When 再设置 .position({top: 5, left: 5})
    Then edges 形式生效，x/y 形式被清除
    And Text 按 edges 定位

  # ─── position 本地化（RTL）────────────────────────

  Scenario: LocalizedEdges 在 LTR 下
    Given 布局方向为 LTR
    And 一个 Text 子组件
    When 设置 Text.position({start: 10, top: 20})（使用 LengthMetrics）
    Then start 映射为 left：Text X = parentPaddingLeft + selfMarginLeft + 10vp

  Scenario: LocalizedEdges 在 RTL 下
    Given 布局方向为 RTL
    And 一个容器宽 300vp 内有一个 Text 子组件宽 80vp
    When 设置 Text.position({start: 10, top: 20})（使用 LengthMetrics）
    Then start 映射为 right：Text X = 300 - 80 - parentPaddingRight - selfMarginRight - 10vp

  # ─── offset 基础 ─────────────────────────────────

  Scenario: 设置相对偏移
    Given 一个 Column 容器
    And 一个 Text 子组件正常布局位置为 (0, 100)
    When 设置 Text.offset({x: 10, y: -5})
    Then Text 绘制位置为 (10, 95)
    And Text 仍占据布局位置 (0, 100)（兄弟组件不受影响）

  Scenario: offset 不脱离布局流
    Given 一个 Column 容器
    And 三个 Text 子组件 A、B、C
    When Text B 设置 .offset({x: 50, y: 0})
    Then A、B、C 在 Column 中的布局位置不变
    And B 的视觉渲染位置向右偏移 50vp

  Scenario: offset API < 10 包含父 padding
    Given 目标最低 API 版本 < 10
    And 一个容器设置了 padding(20)
    And 一个子组件正常布局位置为 (0, 0)
    When 子组件设置 .offset({x: 10, y: 10})
    Then 实际偏移 = offset + parentPadding = (30, 30)

  Scenario: offset API >= 10 不含父 padding
    Given 目标最低 API 版本 >= 10
    And 一个容器设置了 padding(20)
    And 一个子组件正常布局位置为 (0, 0)
    When 子组件设置 .offset({x: 10, y: 10})
    Then 实际偏移 = offset = (10, 10)（不叠加 padding）

  # ─── offset edges ─────────────────────────────────

  Scenario: offset bottom 为负方向偏移
    Given 一个 Text 子组件
    When 设置 Text.offset({bottom: 10})
    Then Text 向上偏移 10vp（Y 方向 -10）

  Scenario: offset right 为负方向偏移
    Given 一个 Text 子组件
    When 设置 Text.offset({right: 10})
    Then Text 向左偏移 10vp（X 方向 -10）

  # ─── markAnchor ─────────────────────────────────

  Scenario: markAnchor 偏移锚点
    Given 一个 Stack 容器
    And 一个 Text 子组件设置 .position({x: 100, y: 100}).markAnchor({x: 50, y: 50})
    When 布局执行
    Then Text 绘制 X = position计算结果 - 50
    And Text 绘制 Y = position计算结果 - 50
    And 相当于以 Text 内 (50, 50) 位置为基准进行定位

  Scenario: markAnchor 不影响布局
    Given 一个 Column 容器
    And 一个 Text 子组件设置 .markAnchor({x: 100, y: 0})
    When 布局执行
    Then Text 在 Column 中的布局位置不变
    And Text 的视觉渲染位置向左偏移 100vp
    And 兄弟组件不受影响

  Scenario: markAnchor 百分比参照自身
    Given 一个 Text 子组件宽 200vp 高 100vp
    When 设置 .markAnchor({x: '50%', y: '50%'})
    Then anchorX = 200 * 50% = 100vp
    And anchorY = 100 * 50% = 50vp
    And 相当于以组件中心为锚点

  Scenario: markAnchor RTL start 取反
    Given 布局方向为 RTL
    And 一个 Text 子组件
    When 设置 .markAnchor({start: 50, top: 0})
    Then anchorX = -50（RTL 下 start 取反）
    And Text 视觉位置向右偏移 50vp（因为 -(-50) = +50）

  # ─── align ─────────────────────────────────

  Scenario: 默认居中对齐
    Given 一个 Stack 容器宽 300vp 高 300vp
    And 一个 Text 子组件宽 100vp 高 50vp
    When 未设置 align
    Then Text 水平居中：X = (300 - 100) / 2 = 100vp
    And Text 垂直居中：Y = (300 - 50) / 2 = 125vp

  Scenario: 左上角对齐
    Given 一个 Stack 容器宽 300vp 高 300vp
    And 一个 Text 子组件宽 100vp 高 50vp
    When 设置 Stack.align(Alignment.TopStart)
    Then Text X = 0
    And Text Y = 0

  Scenario: 右下角对齐
    Given 一个 Stack 容器宽 300vp 高 300vp
    And 一个 Text 子组件宽 100vp 高 50vp
    When 设置 Stack.align(Alignment.BottomEnd)
    Then Text X = 300 - 100 = 200vp
    And Text Y = 300 - 50 = 250vp

  Scenario: align 对 outOfLayout 子组件无效
    Given 一个 Stack 容器设置 .align(Alignment.BottomEnd)
    And 一个 Text 子组件设置 .position({x: 0, y: 0})
    When 布局执行
    Then Text 按 position 定位在 (0, 0)，align 不影响其位置

  Scenario: align RTL 镜像
    Given 布局方向为 RTL
    And 一个 Stack 容器宽 300vp
    And 一个 Text 子组件宽 100vp
    When 使用本地化对齐字符串 'top_start'（IsMirrorable=true）
    Then top_start 在 RTL 下映射为 TOP_RIGHT
    And Text X = 300 - 100 = 200vp（右对齐）

  # ─── direction ─────────────────────────────────

  Scenario: Row RTL 反向排列
    Given 一个 Row 容器设置 .direction(Direction.Rtl)
    And 三个子组件 A(宽100)、B(宽100)、C(宽100)
    When 布局执行
    Then 排列顺序从右到左：C(最左) → B(中间) → A(最右)

  Scenario: Column 不受 direction 影响
    Given 一个 Column 容器设置 .direction(Direction.Rtl)
    And 三个子组件 A、B、C
    When 布局执行
    Then 排列顺序仍为从上到下：A(顶部) → B(中间) → C(底部)

  Scenario: direction AUTO 解析
    Given 系统语言环境为 LTR
    And 一个 Row 容器设置 .direction(Direction.Auto)
    When 布局执行
    Then 子组件从左到右排列（AUTO 解析为 LTR）

  Scenario: direction AUTO 不继承父组件
    Given 系统语言环境为 LTR
    And 一个外层 Column 设置 .direction(Direction.Rtl)
    And 内层 Row 设置 .direction(Direction.Auto)
    When 内层 Row 布局执行
    Then 内层 Row 子组件从左到右排列（AUTO 解析为系统 LTR，不继承外层 RTL）

  # ─── 属性交互 ─────────────────────────────────

  Scenario: position + offset 同时设置
    Given 一个 Text 子组件
    When 设置 .position({x: 10, y: 20}).offset({x: 5, y: 5})
    Then position 优先生效，offset 被忽略
    And Text 绘制位置由 position 决定

  Scenario: position + markAnchor 组合
    Given 一个 Stack 容器
    And 一个 Text 子组件宽 100vp 高 50vp
    When 设置 .position({x: 150, y: 250}).markAnchor({x: 50, y: 25})
    Then Text 绘制 X = position结果 - 50（以 Text 水平中心定位）
    And Text 绘制 Y = position结果 - 25（以 Text 垂直中心定位）

  Scenario: offset + markAnchor 组合
    Given 一个 Text 子组件布局位置为 (100, 200)
    When 设置 .offset({x: 10, y: 10}).markAnchor({x: 5, y: 5})
    Then Text 绘制 X = 100 + 10 - 5 = 105
    And Text 绘制 Y = 200 + 10 - 5 = 205

  Scenario: direction 影响 position start/end
    Given 一个容器设置 .direction(Direction.Rtl)
    And 一个子组件设置 .position({start: 10, top: 0})
    When 布局执行
    Then start 映射为 right（因为 RTL）
    And 子组件从右侧边缘定位
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（position/offset/markAnchor/align/direction 五个属性；不含 alignSelf/alignRules/aspectRatio/zIndex/layoutWeight/expandSafeArea/pixelRound）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致
- [x] API 版本行为差异全部标注（API 10 offset padding、API 12 position reset）
- [x] 存储层次差异标注（RenderContext vs LayoutProperty）
- [x] direction AUTO 不继承行为已重点标注
- [x] position/offset 互斥存储形式已标注

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "position offset markAnchor align direction layout position properties"
  - repo: "openharmony/ace_engine"
    query: "RenderPositionProperty AdjustPaintRect SetPositionToRSNode paint rect calculation"
  - repo: "openharmony/ace_engine"
    query: "IsOutOfLayout outOfLayout Flex layout algorithm skip children"
  - repo: "openharmony/ace_engine"
    query: "CheckPositionOrOffsetLocalizedEdges RTL start end direction"
  - repo: "openharmony/ace_engine"
    query: "BoxLayoutAlgorithm PerformLayout align GetAlignPosition"
```

**关键文档：**
- SDK API 知识库：`docs/sdk/ArkUI_SDK_API_Knowledge_Base.md`
- 架构设计：`specs/04-common-capability/03-common-attributes/01-layout-attributes/design.md`
- 尺寸属性规格：`specs/04-common-capability/03-common-attributes/01-layout-attributes/Feat-01-size-properties-spec.md`
