# 特性规格

> Func-05-09-04-Feat-02 行/段落布局：固化 lineHeight、lineSpacing、lineHeightMultiple、minLineHeight、maxLineHeight、halfLeading、fallbackLineSpacing、includeFontPadding 八个行高/行间距属性以及 textAlign、textVerticalAlign、textContentAlign、textIndent、baselineOffset、textDirection 六个对齐/缩进属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 行/段落布局 (Line & Paragraph Layout) |
| 特性编号 | Func-05-09-04-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持核心属性，API 12/20/22/23/24/26 有 API 新增 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/04-text/design.md` | Baselined |

---

## 用户故事

### US-1: 设置行高

**作为** 应用开发者,
**我想要** 通过 `.lineHeight()` 设置 Text 组件的行高,
**以便** 控制文本行与行之间的垂直间距。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.lineHeight(value)` 且 value 为正数 THEN 文本每行高度为 value（单位 fp），文本在行内垂直居中 | 正常 |
| AC-1.2 | WHEN value 为 string 类型（如 `'24fp'`、`'30px'`） THEN 按对应单位解析行高 | 正常 |
| AC-1.3 | WHEN value 为 Resource 类型 THEN 从资源文件解析为对应行高值 | 正常 |
| AC-1.4 | WHEN value ≤ 0 THEN 行高不受限制，字号自适应，使用排版引擎默认行高 | 正常 |
| AC-1.5 | WHEN 未设置 lineHeight THEN 使用排版引擎基于字号计算的默认行高 | 异常 |
| AC-1.6 | WHEN lineHeight 设置为正值 THEN TextLayoutAlgorithm 中 `hasHeightOverride_=true`，自适应 maxLines 计算基于 lineHeight 进行行数推断（`text_layout_algorithm.cpp:67-88`） | 边界 |

### US-2: 设置行间距

**作为** 应用开发者,
**我想要** 通过 `.lineSpacing()` 设置文本行间距,
**以便** 调整行与行之间的额外间距。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.lineSpacing(value)` 且 value 为 LengthMetrics 正值 THEN 行间距增加 value 对应的距离 | 正常 |
| AC-2.2 | WHEN value ≤ 0 THEN 行间距使用默认值 0（无额外间距） | 正常 |
| AC-2.3 | WHEN 调用 `.lineSpacing(value, { onlyBetweenLines: true })` (@since 20) THEN 仅在行与行之间生效，首行之前和末行之后不包含额外间距 | 正常 |
| AC-2.4 | WHEN 调用 `.lineSpacing(value)` 不传 options 或 `onlyBetweenLines` 为 false THEN 行间距对所有行生效（包括首行之前和末行之后） | 异常 |
| AC-2.5 | WHEN 通过 C API `NODE_TEXT_LINE_SPACING` 设置 THEN `.value[0].f32` 为行间距（fp 单位），不支持 onlyBetweenLines 参数（始终为 false） | 异常 |

### US-3: 设置行高倍数

**作为** 应用开发者,
**我想要** 通过 `.lineHeightMultiple()` (@since 22) 以倍数方式设置行高,
**以便** 按比例控制行高而非固定值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.lineHeightMultiple(value)` 且 value > 0 THEN 行高设为 基准行高 × value | 边界 |
| AC-3.2 | WHEN value ≤ 0 或 undefined THEN 倍数不生效，已设置的倍数被 Reset | 异常 |
| AC-3.3 | WHEN lineHeightMultiple 设置为正值 THEN JS Bridge 和静态版均会先将 lineHeight 强制设为 28px（`CalcDimension(DEFAULT_LINE_HEIGHT=28, DimensionUnit::PX)`），再设置倍数值（`js_text.cpp:647`、`text_model_static.cpp:539`） | 正常 |
| AC-3.4 | WHEN 通过 C API `NODE_TEXT_LINE_HEIGHT_MULTIPLE` 设置正值 THEN 同样先将 lineHeight reset 为默认值再设置倍数（`style_modifier.cpp:14083`） | 正常 |

### US-4: 设置最小行高

**作为** 应用开发者,
**我想要** 通过 `.minLineHeight()` (@since 22) 设置行高下限,
**以便** 确保行高不小于指定值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.minLineHeight(value)` 且 value 为 LengthMetrics 正值 THEN 实际行高不低于 value | 正常 |
| AC-4.2 | WHEN value < 0 THEN 按 0 处理（C API 层：`style_modifier.cpp:14165` 将负值设为 0 并返回错误码） | 异常 |
| AC-4.3 | WHEN value 为 undefined THEN 该属性不限制行高 | 异常 |

### US-5: 设置最大行高

**作为** 应用开发者,
**我想要** 通过 `.maxLineHeight()` (@since 22) 设置行高上限,
**以便** 确保行高不超过指定值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.maxLineHeight(value)` 且 value 为 LengthMetrics 正值 THEN 实际行高不超过 value | 边界 |
| AC-5.2 | WHEN value < 0 THEN 按 0 处理（C API 层同 minLineHeight） | 边界 |
| AC-5.3 | WHEN value 为 undefined THEN 该属性不限制行高 | 异常 |

### US-6: 控制半行距

**作为** 应用开发者,
**我想要** 通过 `.halfLeading()` (@since 12) 控制是否启用半行距分配,
**以便** 在行高大于字号时将多余空间平均分配到行顶和行底。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.halfLeading(true)` THEN 启用半行距分配，多余行高空间平均分配到行顶和行底 | 正常 |
| AC-6.2 | WHEN 调用 `.halfLeading(false)` 或未设置 THEN 不启用半行距 | 异常 |
| AC-6.3 | WHEN 组件级设置存在 THEN 组件级设置覆盖 `module.json5` 全局设置 | 正常 |
| AC-6.4 | WHEN 未在组件上设置 halfLeading THEN 使用 `pipeline->GetHalfLeading()` 的全局默认值（`multiple_paragraph_layout_algorithm.cpp:186`），而非硬编码 false | 正常 |

### US-7: 启用回退字体行间距

**作为** 应用开发者,
**我想要** 通过 `.fallbackLineSpacing()` (@since 23) 控制回退字体是否参与行间距计算,
**以便** 在使用多字体时避免行重叠。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.fallbackLineSpacing(true)` THEN 回退字体的 ascent/descent 参与行间距计算，防止行重叠 | 异常 |
| AC-7.2 | WHEN 调用 `.fallbackLineSpacing(false)` 或未设置 THEN 回退字体不额外影响行间距 | 异常 |

### US-8: 控制字体内边距

**作为** 应用开发者,
**我想要** 通过 `.includeFontPadding()` (@since 23) 控制是否在行顶和行底添加额外空间,
**以便** 兼容需要额外字体内边距的布局场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `.includeFontPadding(true)` THEN 布局在行顶和行底添加额外内边距以容纳字符的最大上升/下降 | 边界 |
| AC-8.2 | WHEN 调用 `.includeFontPadding(false)` 或未设置 THEN 不添加额外内边距 | 异常 |

### US-9: 设置文本水平对齐

**作为** 应用开发者,
**我想要** 通过 `.textAlign()` 设置文本的水平对齐方式,
**以便** 控制文本在组件宽度内的排列位置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 调用 `.textAlign(TextAlign.Start)` THEN 文本起始边对齐（LTR 为左对齐，RTL 为右对齐） | 正常 |
| AC-9.2 | WHEN 调用 `.textAlign(TextAlign.Center)` THEN 文本居中对齐 | 正常 |
| AC-9.3 | WHEN 调用 `.textAlign(TextAlign.End)` THEN 文本末端对齐 | 正常 |
| AC-9.4 | WHEN 调用 `.textAlign(TextAlign.JUSTIFY)` THEN 文本两端对齐；需配合 `wordBreak` 使用；最后一行仍按起始边对齐 | 正常 |
| AC-9.5 | WHEN 未设置 textAlign THEN 默认 `TextAlign.Start`（穿戴设备默认 `TextAlign.Center`） | 异常 |
| AC-9.6 | WHEN 传入非法枚举值 THEN API ≥ 12 时回退到 `TextAlign.Start`（默认值 0），API < 12 时不生效 | 异常 |

### US-10: 设置文本垂直对齐

**作为** 应用开发者,
**我想要** 通过 `.textVerticalAlign()` (@since 20) 设置文本的垂直对齐方式,
**以便** 控制文本在行内的垂直位置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 调用 `.textVerticalAlign(TextVerticalAlign.BASELINE)` 或未设置 THEN 文本基线对齐（默认行为） | 异常 |
| AC-10.2 | WHEN 调用 `.textVerticalAlign(TextVerticalAlign.TOP)` THEN 文本顶部对齐 | 正常 |
| AC-10.3 | WHEN 调用 `.textVerticalAlign(TextVerticalAlign.CENTER)` THEN 文本垂直居中 | 正常 |
| AC-10.4 | WHEN 调用 `.textVerticalAlign(TextVerticalAlign.BOTTOM)` THEN 文本底部对齐 | 正常 |
| AC-10.5 | WHEN 在 ArkTS 静态版中使用 textVerticalAlign THEN 该属性在静态版 Model 层缺失实现（`text_model_static.cpp` 未包含 SetTextVerticalAlign），属性设置可能不生效 | 异常 |

### US-11: 设置文本内容整体垂直对齐

**作为** 应用开发者,
**我想要** 通过 `.textContentAlign()` (@since 21) 设置文本内容块整体的垂直对齐方式,
**以便** 当文本内容高度小于组件高度时，控制内容块在垂直方向的位置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-11.1 | WHEN 调用 `.textContentAlign(TextContentAlign.TOP)` THEN 文本内容块顶部对齐 | 正常 |
| AC-11.2 | WHEN 调用 `.textContentAlign(TextContentAlign.CENTER)` THEN 文本内容块垂直居中 | 正常 |
| AC-11.3 | WHEN 调用 `.textContentAlign(TextContentAlign.BOTTOM)` THEN 文本内容块底部对齐 | 正常 |
| AC-11.4 | WHEN 未设置或传入非法值 THEN ArkTS 动态版默认 `CENTER`；ArkTS 静态版默认 `TOP`（`text.static.d.ets` 文档标注 `TOP`） | 异常 |
| AC-11.5 | WHEN textContentAlign 属性变更 THEN 触发 `PROPERTY_UPDATE_LAYOUT`（而非 `PROPERTY_UPDATE_MEASURE`），仅重新布局不触发重新测量 | 正常 |

### US-12: 设置首行缩进

**作为** 应用开发者,
**我想要** 通过 `.textIndent()` (@since 10) 设置段落首行缩进,
**以便** 控制每段文本第一行的缩进距离。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-12.1 | WHEN 调用 `.textIndent(value)` 且 value 为正数 Length THEN 首行缩进 value 对应的距离 | 正常 |
| AC-12.2 | WHEN value 为负数 THEN 首行产生反向缩进（缩进到行首之前，允许负值，不做钳位） | 异常 |
| AC-12.3 | WHEN value 为 0 或未设置 THEN 无首行缩进 | 异常 |
| AC-12.4 | WHEN value 通过 Resource 引用 THEN 从资源文件解析缩进值 | 正常 |

### US-13: 设置基线偏移

**作为** 应用开发者,
**我想要** 通过 `.baselineOffset()` 设置文本基线偏移量,
**以便** 微调文本在垂直方向的位置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-13.1 | WHEN 调用 `.baselineOffset(value)` 且 value > 0 THEN 文本内容向上偏移 value 对应的距离 | 边界 |
| AC-13.2 | WHEN value < 0 THEN 文本内容向下偏移 | 边界 |
| AC-13.3 | WHEN value 为 0 或未设置 THEN 无基线偏移（默认值 0） | 异常 |
| AC-13.4 | WHEN baselineOffset 设置了非零值 THEN `\|baselineOffset\|` 参与内容高度计算，加入段落总高度（`text_layout_algorithm.cpp:230`） |
| AC-13.5 | WHEN value 为百分比字符串 THEN 使用默认值（百分比不支持） | 异常 |

### US-14: 设置文本方向

**作为** 应用开发者,
**我想要** 通过 `.textDirection()` (@since 23) 显式设置文本排列方向,
**以便** 控制文本的书写和阅读方向。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-14.1 | WHEN 调用 `.textDirection(TextDirection.LTR)` THEN 文本从左到右排列 | 正常 |
| AC-14.2 | WHEN 调用 `.textDirection(TextDirection.RTL)` THEN 文本从右到左排列 | 正常 |
| AC-14.3 | WHEN 调用 `.textDirection(TextDirection.AUTO)` THEN 根据文本内容自动判断方向 | 正常 |
| AC-14.4 | WHEN 未设置或设为 undefined THEN 重置为继承（`TextDirection::INHERIT`），从父组件或系统获取方向 | 异常 |
| AC-14.5 | WHEN textDirection 属性变更 THEN 触发 `PROPERTY_UPDATE_MEASURE_SELF`（仅自身重新测量，不级联子组件） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-6, R-1 | N/A（存量） | 单测 | `test/unittest/core/pattern/text/` |
| AC-2.1~2.5 | R-7, R-8, R-21 | N/A | 单测 | 同上 |
| AC-3.1~3.4 | R-9, R-2, R-22 | N/A | 单测 | 同上 |
| AC-4.1~4.3 | R-10, R-23 | N/A | 单测 | 同上 |
| AC-5.1~5.3 | R-11, R-23 | N/A | 单测 | 同上 |
| AC-6.1~6.4 | R-12, R-3 | N/A | 单测 | 同上 |
| AC-7.1~7.2 | R-13 | N/A | 单测 | 同上 |
| AC-8.1~8.2 | R-14 | N/A | 单测 | 同上 |
| AC-9.1~9.6 | R-15, R-24 | N/A | 单测 | 同上 |
| AC-10.1~10.5 | R-16, R-4 | N/A | 单测 | 同上 |
| AC-11.1~11.5 | R-17, R-4, R-5 | N/A | 单测 | 同上 |
| AC-12.1~12.4 | R-18 | N/A | 单测 | 同上 |
| AC-13.1~13.5 | R-19, R-1 | N/A | 单测 | 同上 |
| AC-14.1~14.5 | R-20 | N/A | 单测 | 同上 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | lineHeight > 0 时 `hasHeightOverride_=true`（`text_style.h:809`） | lineHeight 正值启用"高度覆盖"模式，影响自适应 maxLines 的行数推断 | — | AC-1.6, AC-13.4 |
| R-2 | 行为 | JS Bridge（`js_text.cpp:647`）、Static 版（`text_model_static.cpp:539`）、C API（`style_modifier.cpp:14083`）三条路径均如此 | lineHeightMultiple 与 lineHeight 隐式耦合：设置 lineHeightMultiple 时会先将 lineHeight 强制设为 28px（DEFAULT_LINE_HEIGHT） | — | AC-3.3, AC-3.4 |
| R-3 | 行为 | 组件未设置时从 `pipeline->GetHalfLeading()` 取值（`multiple_paragraph_layout_algorithm.cpp:186`），而非硬编码 false | halfLeading 默认值来源于 PipelineContext 全局配置 | — | AC-6.4 |
| R-4 | 行为 | 动态版 `text_model_ng.cpp:1307` 默认 `TextContentAlign::CENTER`；静态版 `text.static.d.ets` 标注默认 `TOP` | textContentAlign 动态版默认 CENTER、静态版默认 TOP | — | AC-11.4, AC-10.5 |
| R-5 | 行为 | 变更仅触发重新布局，不触发重新测量（`text_layout_property.h:166`），与大多数属性的 PROPERTY_UPDATE_MEASURE 行为不同 | textContentAlign 使用 PROPERTY_UPDATE_LAYOUT 而非 PROPERTY_UPDATE_MEASURE | — | AC-11.5 |
| R-6 | 行为 | 设置有效值（number/string/Resource） | `lineHeight` 设置行高，单位 fp | `TextLayoutProperty` → TextLineStyle::propLineHeight（`text_styles.h:360`） | AC-1.1~1.6 |
| R-7 | 行为 | 设置 LengthMetrics 正值 | `lineSpacing` 设置行间距 | `TextLayoutProperty` → TextLineStyle::propLineSpacing（`text_styles.h:376`） | AC-2.1~2.2 |
| R-8 | 行为 | options.onlyBetweenLines = true (@since 20) | `lineSpacing` + `onlyBetweenLines` 模式 | `TextLayoutProperty` → TextLineStyle::propIsOnlyBetweenLines（`text_styles.h:377`） | AC-2.3~2.4 |
| R-9 | 行为 | 设置正值 double (@since 22) | `lineHeightMultiple` 设置行高倍数 | `TextLayoutProperty` → propLineHeightMultiply（WITHOUT_GROUP，`text_layout_property.h:194`） | AC-3.1~3.4 |
| R-10 | 行为 | 设置 LengthMetrics 正值 (@since 22) | `minLineHeight` 设置行高下限 | `TextLayoutProperty` → propMinimumLineHeight（WITHOUT_GROUP，`text_layout_property.h:195`） | AC-4.1~4.3 |
| R-11 | 行为 | 设置 LengthMetrics 正值 (@since 22) | `maxLineHeight` 设置行高上限 | `TextLayoutProperty` → propMaximumLineHeight（WITHOUT_GROUP，`text_layout_property.h:196`） | AC-5.1~5.3 |
| R-12 | 行为 | 设置 boolean (@since 12) | `halfLeading` 启用半行距分配 | `TextLayoutProperty` → TextLineStyle::propHalfLeading（`text_styles.h:380`） | AC-6.1~6.4 |
| R-13 | 行为 | 设置 boolean (@since 23) | `fallbackLineSpacing` 启用回退字体行间距 | `TextLayoutProperty` → propFallbackLineSpacing（WITHOUT_GROUP TEXT，`text_layout_property.h:200`） | AC-7.1~7.2 |
| R-14 | 行为 | 设置 boolean (@since 23) | `includeFontPadding` 启用字体内边距 | `TextLayoutProperty` → propIncludeFontPadding（WITHOUT_GROUP TEXT，`text_layout_property.h:199`） | AC-8.1~8.2 |
| R-15 | 行为 | 设置 TextAlign 枚举 | `textAlign` 设置水平对齐方式 | `TextLayoutProperty` → TextLineStyle::propTextAlign（`text_styles.h:365`） | AC-9.1~9.6 |
| R-16 | 行为 | 设置 TextVerticalAlign 枚举 (@since 20) | `textVerticalAlign` 设置行内垂直对齐 | `TextLayoutProperty` → TextLineStyle::propTextVerticalAlign（`text_styles.h:366`） | AC-10.1~10.5 |
| R-17 | 行为 | 设置 TextContentAlign 枚举 (@since 21) | `textContentAlign` 设置内容块垂直对齐 | `TextLayoutProperty` → TextLineStyle::propTextContentAlign（`text_styles.h:387`） | AC-11.1~11.5 |
| R-18 | 行为 | 设置 Length 值 (@since 10) | `textIndent` 设置首行缩进 | `TextLayoutProperty` → TextLineStyle::propTextIndent（`text_styles.h:371`） | AC-12.1~12.4 |
| R-19 | 行为 | 设置 number/ResourceStr 值 | `baselineOffset` 设置基线偏移 | `TextLayoutProperty` → TextLineStyle::propBaselineOffset（`text_styles.h:363`） | AC-13.1~13.5 |
| R-20 | 行为 | 设置 TextDirection 枚举 (@since 23) | `textDirection` 设置文本方向 | `TextLayoutProperty` → TextLineStyle::propTextDirection（`text_styles.h:388`） | AC-14.1~14.5 |
| R-21 | 异常 | 传入负值 LengthMetrics | lineSpacing 负值处理 | JS Bridge 层 Reset 为默认值 0；C API 层 Reset 为默认且返回错误码 | AC-2.2 |
| R-22 | 异常 | 传入 ≤ 0 的值 | lineHeightMultiple 负值处理 | JS Bridge 调用 `ResetLineHeightMultiply()`；C API 先 resetMultiply 再返回错误码 | AC-3.2 |
| R-23 | 异常 | 传入负值 LengthMetrics | minLineHeight/maxLineHeight 负值处理 | JS Bridge 调用 Reset；C API 设为 0 并返回错误码 | AC-4.2, AC-5.2 |
| R-24 | 异常 | 传入超出 [0, 5] 范围的枚举值 | textAlign 非法枚举值 | API ≥ 12 时回退到 `TextAlign.Start`（0）；API < 12 时不生效（`js_text.cpp:560-568`） | AC-9.6 |
| R-25 | 异常 | 传入百分比字符串 | baselineOffset 百分比值 | 使用默认值 0（百分比不支持） | AC-13.5 |
| R-26 | 异常 | 传入超出 [0, 3] 范围的值 | textDirection 非法枚举值 | C API 调用 resetTextDirection 并返回错误码（`style_modifier.cpp:13673-13686`）；JS Bridge 调用 `ResetTextDirection()` | AC-14.4 |
| R-27 | 异常 | 传入非布尔类型参数 | halfLeading 非布尔值 | 设为 false（`js_text.cpp:1326-1337`） | AC-6.2 |
| R-28 | 恢复 | TextLineStyle 属性组懒初始化——行布局属性组在首次设置任一行属性时通过 `GetOrCreateTextLineStyle()` 创建 | 未设置任何行布局属性时属性组为 null，各属性按默认值渲染 | 等同于全部使用默认值 | — |
| R-29 | 恢复 | lineHeightMultiple 被 Reset 时 lineHeight 不会自动恢复 | Reset lineHeightMultiple 仅清除倍数属性 | lineHeight 仍保持先前被隐式设为 28px 的值（如果是通过 lineHeightMultiple 间接设置的） | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-6 (lineHeight) | 单测 | 正值/零值/负值/字符串/Resource 各场景行高渲染正确 |
| VM-2 | R-7, R-8 (lineSpacing + onlyBetweenLines) | 单测 | 正值生效、负值回退、onlyBetweenLines 模式差异 |
| VM-3 | R-9 (lineHeightMultiple) | 单测 | 倍数生效、负值 Reset、对 lineHeight 的隐式副作用 |
| VM-4 | R-10, R-11 (minLineHeight/maxLineHeight) | 单测 | 正值夹紧、负值处理、undefined Reset |
| VM-5 | R-12 (halfLeading) | 单测 | 启用/禁用半行距；pipeline 全局默认值传播 |
| VM-6 | R-13, R-14 (fallbackLineSpacing/includeFontPadding) | 单测 | 布尔值生效、多组件类型共享实现 |
| VM-7 | R-15 (textAlign) | 单测 | 六种对齐方式各自生效、JUSTIFY 配合 wordBreak、非法值回退 |
| VM-8 | R-16 (textVerticalAlign) | 单测 | 四种垂直对齐方式、静态版缺失情况 |
| VM-9 | R-17 (textContentAlign) | 单测 | 三种内容对齐方式、PROPERTY_UPDATE_LAYOUT 验证 |
| VM-10 | R-18 (textIndent) | 单测 | 正值/负值/零值/Resource 各场景 |
| VM-11 | R-19 (baselineOffset) | 单测 | 正/负偏移、内容高度计算影响、百分比回退 |
| VM-12 | R-20 (textDirection) | 单测 | LTR/RTL/AUTO/INHERIT 各方向、PROPERTY_UPDATE_MEASURE_SELF 验证 |

## API 变更分析

> 本特性为存量规格，记录各 API 的引入版本和当前签名。API 签名、d.ts 位置、权限等实现细节见 design.md。

### 新增 API

| API 名称 | 引入版本 | 类型 | 功能描述 | 关联 AC |
|----------|----------|------|----------|---------|
| `lineHeight(value: number\|string\|Resource)` | @since 7 | Public | 设置行高 | AC-1.1 |
| `lineSpacing(value: LengthMetrics)` | @since 12 | Public | 设置行间距 | AC-2.1 |
| `lineSpacing(value: LengthMetrics, options?: LineSpacingOptions)` | @since 20 | Public | 设置行间距（含 onlyBetweenLines 选项） | AC-2.3 |
| `lineHeightMultiple(value: number\|undefined)` | @since 22 | Public | 设置行高倍数 | AC-3.1 |
| `minLineHeight(value: LengthMetrics\|undefined)` | @since 22 | Public | 设置最小行高 | AC-4.1 |
| `maxLineHeight(value: LengthMetrics\|undefined)` | @since 22 | Public | 设置最大行高 | AC-5.1 |
| `halfLeading(halfLeading: boolean)` | @since 12 | Public | 控制半行距分配 | AC-6.1 |
| `fallbackLineSpacing(enabled: Optional<boolean>)` | @since 23 | Public | 启用回退字体行间距 | AC-7.1 |
| `includeFontPadding(include: Optional<boolean>)` | @since 23 | Public | 控制字体内边距 | AC-8.1 |
| `textAlign(value: TextAlign)` | @since 7 | Public | 设置水平对齐 | AC-9.1 |
| `textVerticalAlign(textVerticalAlign: Optional<TextVerticalAlign>)` | @since 20 | Public | 设置行内垂直对齐 | AC-10.1 |
| `textContentAlign(textContentAlign: Optional<TextContentAlign>)` | @since 21 | Public | 设置内容块垂直对齐 | AC-11.1 |
| `textIndent(value: Length)` | @since 10 | Public | 设置首行缩进 | AC-12.1 |
| `baselineOffset(value: number\|ResourceStr)` | @since 7 | Public | 设置基线偏移 | AC-13.1 |
| `textDirection(direction: TextDirection\|undefined)` | @since 23 | Public | 设置文本方向 | AC-14.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `letterSpacing(value)` | @since 20 参数类型扩展为 `number\|ResourceStr` | value 从 `number\|string` 扩展为 `number\|ResourceStr` | 兼容变更，无需迁移 | N/A（不在本 Feat 范围内） |
| `baselineOffset(value)` | @since 20 参数类型扩展为 `number\|ResourceStr` | value 从 `number\|string` 扩展为 `number\|ResourceStr` | 兼容变更，无需迁移 | AC-13.1 |
| `textOverflow(options)` | @since 18 参数类型变更为 `TextOverflowOptions` | 从 `{overflow: TextOverflow}` 变更为 `TextOverflowOptions` | 兼容变更 | N/A（不在本 Feat 范围内） |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否 — 本 Feat 覆盖的 14 个属性无跨版本行为变更
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（lineHeight/textAlign/baselineOffset）；API 10（textIndent）；API 12（lineSpacing/halfLeading）；API 20（lineSpacing overload/textVerticalAlign）；API 21（textContentAlign）；API 22（lineHeightMultiple/minLineHeight/maxLineHeight）；API 23（fallbackLineSpacing/includeFontPadding/textDirection）
- **API 版本号策略:** 各 API 按 `@since` 标注引入版本；`baselineOffset` @since 20 扩展参数类型

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| TextLineStyle 属性组懒初始化 | 行布局属性组通过 `unique_ptr<TextLineStyle>` 懒创建（`text_layout_property.h:143`），lineHeight/lineSpacing/textAlign/textIndent/baselineOffset/textDirection 等存储在同一组实例中 | 全部 |
| lineHeightMultiple/minLineHeight/maxLineHeight 存储在 WITHOUT_GROUP | 这三个属性不在 TextLineStyle 组内，而是作为 TextLayoutProperty 的直接字段存储（`text_layout_property.h:194-196`），使用独立的 optional 字段 | AC-3.1~3.4, AC-4.1~4.3, AC-5.1~5.3 |
| fallbackLineSpacing/includeFontPadding 也在 WITHOUT_GROUP | 同上（`text_layout_property.h:199-200`），且使用 `ACE_DEFINE_TEXT_PROPERTY_ITEM_WITHOUT_GROUP` 宏（额外设置 `propNeedReCreateParagraph_=true`） | AC-7.1~7.2, AC-8.1~8.2 |
| textContentAlign 使用 PROPERTY_UPDATE_LAYOUT | 与其他属性的 PROPERTY_UPDATE_MEASURE 不同，textContentAlign 变更仅触发布局不触发测量 | AC-11.5 |
| textDirection/halfLeading/paragraphSpacing 使用 PROPERTY_UPDATE_MEASURE_SELF | 这些属性变更仅触发自身重新测量，不级联到子组件 | AC-14.5, AC-6.1 |
| lineHeightMultiple 隐式修改 lineHeight | 设置 lineHeightMultiple 时会先将 lineHeight 设为 28px，属性间存在耦合 | AC-3.3, AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 行布局属性变更触发 `PROPERTY_UPDATE_MEASURE`（或 `MEASURE_SELF`/`LAYOUT`），仅脏节点重新测量/布局 | benchmark | `test/benchmark/` |

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
| 无障碍 | 是 | lineHeight/lineSpacing 影响大字体模式下的行间距；halfLeading 影响行距分配 | AC-1.1, AC-2.1, AC-6.1 |
| 大字体 | 是 | 行高和行间距随字号缩放而变化 | AC-1.1~1.6, AC-2.1~2.5 |
| 深色模式 | N/A | 行布局属性不涉及颜色变化 | — |
| 多窗口/分屏 | N/A | 行布局属性不受窗口模式影响 | — |
| 多用户 | N/A | — | — |
| 版本升级 | 是 | API 20 lineSpacing 新增 onlyBetweenLines；API 22 新增 lineHeightMultiple/minLineHeight/maxLineHeight；API 23 新增 fallbackLineSpacing/includeFontPadding/textDirection | AC-2.3, AC-3.1, AC-7.1, AC-8.1, AC-14.1 |
| 生态兼容 | N/A | — | — |

## 行为场景（Gherkin）

```gherkin
Feature: Text 行/段落布局
  作为应用开发者
  我想要通过声明式 API 控制 Text 组件的行高、行间距、对齐、缩进和基线偏移
  以便精确控制文本在不同场景下的排版布局

  Scenario: 基本行高设置
    Given 一个 Text 组件
    When 调用 .lineHeight(24)
    Then 文本每行高度为 24fp，文本在行内垂直居中

  Scenario: 行高为零或负值
    Given 一个 Text 组件
    When 调用 .lineHeight(0) 或 .lineHeight(-10)
    Then 行高不受限制，使用排版引擎默认行高

  Scenario: 行间距正值设置
    Given 一个多行 Text 组件
    When 调用 .lineSpacing(LengthMetrics.vp(8))
    Then 行与行之间增加 8vp 的额外间距

  Scenario: lineSpacing onlyBetweenLines 模式
    Given 一个多行 Text 组件
    When 调用 .lineSpacing(LengthMetrics.vp(8), { onlyBetweenLines: true })
    Then 仅行与行之间有 8vp 额外间距，首行之前和末行之后无额外间距

  Scenario: lineHeightMultiple 隐式修改 lineHeight
    Given 一个 Text 组件，已设置 .lineHeight(40)
    When 调用 .lineHeightMultiple(1.5)
    Then lineHeight 被隐式重置为 28px
    And 实际行高为 28px × 1.5 = 42px

  Scenario: lineHeightMultiple 重置后 lineHeight 不恢复
    Given 一个 Text 组件，已通过 .lineHeightMultiple(1.5) 隐式设置 lineHeight=28px
    When lineHeightMultiple 被 Reset（设为 undefined）
    Then lineHeight 仍为 28px，不会自动恢复到之前的值

  Scenario: minLineHeight 和 maxLineHeight 夹紧
    Given 一个 Text 组件，设置 .minLineHeight(LengthMetrics.fp(20)) 和 .maxLineHeight(LengthMetrics.fp(30))
    When 排版引擎计算出的自然行高为 16fp
    Then 实际行高被夹紧为 20fp（minLineHeight）

  Scenario: halfLeading 全局默认值传播
    Given module.json5 中 halfLeading 配置为 true
    And Text 组件未设置 .halfLeading()
    When 文本渲染
    Then halfLeading 从 PipelineContext 全局配置获取，行为等同 .halfLeading(true)

  Scenario Outline: textAlign 对齐方式
    Given 一个 Text 组件，文本宽度小于组件宽度
    When 调用 .textAlign(<align>)
    Then 文本按 <behavior> 对齐

    Examples:
      | align                | behavior                    |
      | TextAlign.Start      | 起始边对齐（LTR 左/RTL 右）  |
      | TextAlign.Center     | 居中对齐                    |
      | TextAlign.End        | 末端对齐                    |
      | TextAlign.JUSTIFY    | 两端对齐，末行起始边对齐      |

  Scenario: textVerticalAlign 静态版缺失
    Given 使用 ArkTS 静态版开发
    When 设置 .textVerticalAlign(TextVerticalAlign.CENTER)
    Then 属性可能不生效（text_model_static.cpp 未包含 SetTextVerticalAlign 实现）

  Scenario: textContentAlign 默认值差异
    Given 一个 Text 组件，未设置 textContentAlign
    When 在 ArkTS 动态版中渲染
    Then 文本内容块默认垂直居中（CENTER）
    When 在 ArkTS 静态版中渲染
    Then 文本内容块默认顶部对齐（TOP）

  Scenario: baselineOffset 影响内容高度
    Given 一个 Text 组件
    When 调用 .baselineOffset(10)
    Then 文本向上偏移 10fp
    And 组件内容高度 = 段落高度 + |baselineOffset| = 段落高度 + 10fp

  Scenario: textDirection 显式设置
    Given 一个 Text 组件，内容为阿拉伯文
    When 调用 .textDirection(TextDirection.RTL)
    Then 文本从右到左排列

  Scenario: textIndent 负值缩进
    Given 一个 Text 组件
    When 调用 .textIndent(-20)
    Then 首行产生 -20fp 的反向缩进（首行起始位置在组件左边界之前）

  Scenario: C API lineSpacing 不支持 onlyBetweenLines
    Given 通过 C API 创建 Text 节点
    When 通过 NODE_TEXT_LINE_SPACING 设置 .value[0].f32=8.0
    Then 行间距为 8fp，isOnlyBetweenLines 始终为 false

  Scenario: fallbackLineSpacing 防止行重叠
    Given 一个 Text 组件，主字体为拉丁字体，部分内容回退到中文字体
    When 调用 .fallbackLineSpacing(true)
    Then 回退字体的 ascent/descent 参与行间距计算，行不重叠
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
    query: "Text 组件行高、行间距、对齐属性的存储和布局触发机制"
  - repo: "openharmony/interface_sdk-js"
    query: "Text 组件 lineHeight/lineSpacing/textAlign/baselineOffset API 签名和版本变更"
```

**关键文档：**
- SDK 动态版声明: `interface/sdk-js/api/@internal/component/ets/text.d.ts`
- SDK 静态版声明: `interface/sdk-js/api/arkui/component/text.static.d.ets`
- C API 枚举定义: `interfaces/native/native_node.h`
- TextLineStyle 属性组: `frameworks/core/components_ng/pattern/text/text_styles.h:359-390`
- TextLayoutProperty: `frameworks/core/components_ng/pattern/text/text_layout_property.h`
