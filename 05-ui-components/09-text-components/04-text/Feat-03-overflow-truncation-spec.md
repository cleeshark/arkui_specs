# 特性规格

> Func-05-09-04-Feat-03 溢出与截断：固化 textOverflow/maxLines/minLines/ellipsisMode/wordBreak/lineBreakStrategy/heightAdaptivePolicy/compressLeadingPunctuation/orphanCharOptimization/optimizeTrailingSpace/enableAutoSpacing 共 11 项溢出截断及排版优化属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 溢出与截断 (Overflow & Truncation) |
| 特性编号 | Func-05-09-04-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 10/11/12/18/20/22/23/24/26 有 API 新增 |
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

### US-1: 控制文本溢出行为

**作为** 应用开发者,
**我想要** 通过 `.textOverflow()` 控制文本超出容器时的显示方式,
**以便** 在有限空间内合理呈现长文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.textOverflow({ overflow: TextOverflow.Clip })` 且文本超出 maxLines 限制 THEN 超出部分被裁剪，不显示省略号 | 边界 |
| AC-1.2 | WHEN 调用 `.textOverflow({ overflow: TextOverflow.Ellipsis })` 且文本超出 maxLines 限制 THEN 超出部分被截断并在截断处显示省略号（U+2026） | 边界 |
| AC-1.3 | WHEN 调用 `.textOverflow({ overflow: TextOverflow.None })` THEN 行为与 Clip 相同（`constants.h:257-258`，NONE 和 CLIP 在排版引擎中行为一致） | 边界 |
| AC-1.4 | WHEN 调用 `.textOverflow({ overflow: TextOverflow.MARQUEE })` 且文本实际宽度超出容器宽度 THEN 文本以单行跑马灯形式滚动显示 | 边界 |
| AC-1.5 | WHEN 设置 TextOverflow.MARQUEE THEN 以下属性被隐式覆盖：maxLines 强制为 1、textIndent 强制为 0、文本中换行符替换为空格、copyOption 强制为 None（`text_layout_algorithm.cpp:1214-1217`, `text_pattern.cpp:2969-2970`） | 边界 |
| AC-1.6 | WHEN 设置 TextOverflow.MARQUEE 但文本实际宽度未超出容器宽度 THEN 不启动滚动动画，文本静态显示 | 边界 |
| AC-1.7 | WHEN 未设置 textOverflow THEN 使用默认值 TextOverflow.Clip（`text_model_ng.cpp:1319`） | 异常 |
| AC-1.8 | WHEN 通过 C-API ResetTextTextOverflow 重置 THEN 值重置为 TextOverflow.NONE（`node_text_modifier.cpp:1092`），与 ArkTS 默认值 Clip 存在语义差异 | 正常 |

### US-2: 限制文本最大行数

**作为** 应用开发者,
**我想要** 通过 `.maxLines()` 限制文本显示的最大行数,
**以便** 控制文本占用的垂直空间。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.maxLines(N)` 且 N 为正整数 THEN 文本最多显示 N 行 | 边界 |
| AC-2.2 | WHEN 未设置 maxLines THEN 默认值为 UINT32_MAX（无限制），文本自动换行直到内容结束（`text_model_ng.cpp:1283`） | 异常 |
| AC-2.3 | WHEN maxLines 值为 Infinity 字符串 THEN 按 UINT32_MAX 处理（`js_text.cpp:508`） | 边界 |
| AC-2.4 | WHEN 文本包含 SpanString 且 SpanString 有自身 maxLines 设置 THEN 组件 maxLines 被覆盖为 UINT32_MAX（由 SpanString 的 maxLines 生效），除非 IsTextMaxlinesFirst 为 true（`text_layout_algorithm.cpp:175-176`） | 边界 |
| AC-2.5 | WHEN maxLines 与 textOverflow.Ellipsis 配合使用 THEN 超出 maxLines 的文本被截断并显示省略号 | 边界 |

### US-3: 设置文本最小行数

**作为** 应用开发者,
**我想要** 通过 `.minLines()` (@since 22) 设置文本的最小显示行数,
**以便** 确保文本区域在内容较少时仍保持足够的高度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.minLines(N)` 且 N ≥ 1 THEN 文本框高度至少容纳 N 行，不足 N 行时自动扩展高度 | 正常 |
| AC-3.2 | WHEN minLines > maxLines THEN minLines 被钳位到 maxLines 值（`multiple_paragraph_layout_algorithm.cpp:1154`） | 边界 |
| AC-3.3 | WHEN minLines 为 0 或未设置 THEN 不限制最小行数，高度由内容决定（默认值 0，`text_model_ng.cpp:32`） | 异常 |
| AC-3.4 | WHEN minLines 为负值或非数字 THEN 调用 ResetMinLines 清除属性（`js_text.cpp:524`） | 正常 |
| AC-3.5 | WHEN minLines 生效 THEN 仅影响组件 Frame 高度（扩展），不改变 Paragraph 布局本身（`multiple_paragraph_layout_algorithm.cpp:1145-1189`） | 正常 |

### US-4: 控制省略号位置

**作为** 应用开发者,
**我想要** 通过 `.ellipsisMode()` (@since 11) 控制省略号出现的位置,
**以便** 实现头部省略、中部省略或尾部省略效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.ellipsisMode(EllipsisMode.END)` THEN 省略号出现在文本末尾（默认行为） | 正常 |
| AC-4.2 | WHEN 调用 `.ellipsisMode(EllipsisMode.START)` THEN 省略号出现在文本开头 | 正常 |
| AC-4.3 | WHEN 调用 `.ellipsisMode(EllipsisMode.CENTER)` THEN 省略号出现在文本中间位置（分割比例 TEXT_SPLIT_RATIO=0.6，`txt_paragraph.cpp:33`） | 正常 |
| AC-4.4 | WHEN 调用 `.ellipsisMode(EllipsisMode.MULTILINE_START)` (@since 24) THEN 省略号出现在多行文本块的开头 | 正常 |
| AC-4.5 | WHEN 调用 `.ellipsisMode(EllipsisMode.MULTILINE_CENTER)` (@since 24) THEN 省略号出现在多行文本块的中间 | 正常 |
| AC-4.6 | WHEN ellipsisMode 设置了任意值但 textOverflow 不是 Ellipsis THEN ellipsisMode 不生效（省略号字符仅在 `textOverflow == TextOverflow.ELLIPSIS` 时注入，`txt_paragraph.cpp:93-95`） | 异常 |
| AC-4.7 | WHEN ellipsisMode 为 CENTER THEN Paragraph 缓存失效，每次布局强制重建（`text_layout_algorithm.cpp:315`） | 正常 |
| AC-4.8 | WHEN 未设置 ellipsisMode THEN 默认值为 EllipsisMode.END（C++ 内部名 TAIL，`text_style.h:662`） | 异常 |

### US-5: 控制断词策略

**作为** 应用开发者,
**我想要** 通过 `.wordBreak()` (@since 11) 控制文本的断词策略,
**以便** 优化不同语言文本的换行效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.wordBreak(WordBreak.NORMAL)` THEN 按照默认 Unicode 断行规则换行 | 正常 |
| AC-5.2 | WHEN 调用 `.wordBreak(WordBreak.BREAK_ALL)` THEN 允许在任意两个字符之间断行（包括字母中间） | 正常 |
| AC-5.3 | WHEN 调用 `.wordBreak(WordBreak.BREAK_WORD)` THEN 优先在词边界断行，仅在单词过长无法放入一行时才拆词（默认值，`text_style.h:655`） | 边界 |
| AC-5.4 | WHEN 调用 `.wordBreak(WordBreak.HYPHENATION)` (@since 18) THEN 在支持连字符断词的语言中按音节断行并插入连字符 | 正常 |
| AC-5.5 | WHEN 未设置 wordBreak THEN 默认值为 WordBreak.BREAK_WORD（`node_text_modifier.cpp:1610`） | 异常 |

### US-6: 控制换行质量策略

**作为** 应用开发者,
**我想要** 通过 `.lineBreakStrategy()` (@since 12) 控制换行算法的质量级别,
**以便** 在排版质量与性能之间做出权衡。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.lineBreakStrategy(LineBreakStrategy.GREEDY)` THEN 使用贪心算法逐行填充，每行尽可能放更多内容（默认行为） | 正常 |
| AC-6.2 | WHEN 调用 `.lineBreakStrategy(LineBreakStrategy.HIGH_QUALITY)` THEN 使用全局优化算法选择断行点，可能插入连字符以获得更均匀的行宽 | 正常 |
| AC-6.3 | WHEN 调用 `.lineBreakStrategy(LineBreakStrategy.BALANCED)` THEN 尝试使各行宽度尽可能均匀分配 | 正常 |
| AC-6.4 | WHEN 未设置 lineBreakStrategy THEN 默认值为 LineBreakStrategy.GREEDY（`text_style.h:666`） | 异常 |

### US-7: 高度自适应策略与溢出的交互

**作为** 应用开发者,
**我想要** 通过 `.heightAdaptivePolicy()` (@since 10) 控制文本在高度约束下的自适应行为,
**以便** 在固定高度容器内合理显示文本。

> 注：heightAdaptivePolicy 的基础行为已在 Feat-01 (AC-9.4~9.6) 中规格化。本 US 补充其与溢出截断属性的交互行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN heightAdaptivePolicy 为 LAYOUT_CONSTRAINT_FIRST 且 maxLines 为 UINT32_MAX THEN 从 `GetAdaptedMaxLines()` 计算得出约束高度可容纳的最大行数（`text_layout_algorithm.cpp:67-88`） | 边界 |
| AC-7.2 | WHEN heightAdaptivePolicy 为 LAYOUT_CONSTRAINT_FIRST THEN 在约束高度内循环减少 maxLines 直到内容适配，textOverflow 模式在最终段落中仍然生效（`text_layout_algorithm.cpp:1179-1203`） | 边界 |
| AC-7.3 | WHEN heightAdaptivePolicy 为 MIN_FONT_SIZE_FIRST THEN 先缩小字号到 minFontSize，再根据 maxLines 限制截断（`text_layout_algorithm.cpp:1145-1153`） | 边界 |
| AC-7.4 | WHEN 未设置 heightAdaptivePolicy THEN 默认值为 MAX_LINES_FIRST（`text_model_ng.cpp:1352`） | 异常 |

### US-8: 压缩行首标点

**作为** 应用开发者,
**我想要** 通过 `.compressLeadingPunctuation()` (@since 23) 压缩行首的全角标点符号,
**以便** 优化中文排版中行首标点的视觉对齐效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `.compressLeadingPunctuation(true)` THEN 行首的全角开括号/引号等标点被压缩为半宽显示（`txt_paragraph.cpp:108` → Rosen `compressHeadPunctuation`） | 正常 |
| AC-8.2 | WHEN 调用 `.compressLeadingPunctuation(false)` 或未设置 THEN 行首标点保持全角宽度（默认 false，`text_style.h:684`） | 异常 |

### US-9: 孤字优化

**作为** 应用开发者,
**我想要** 通过 `.orphanCharOptimization()` (@since 26) 避免最后一行出现单个孤立字符,
**以便** 提升多行文本的排版美观度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 调用 `.orphanCharOptimization(true)` THEN 排版引擎调整断行策略，避免最后一行仅包含一个孤立字符（`txt_paragraph.cpp:107` → Rosen `orphanCharOptimization`） | 正常 |
| AC-9.2 | WHEN 调用 `.orphanCharOptimization(false)` 或未设置 THEN 不进行孤字优化（默认 false，`text_style.h:682`） | 异常 |

### US-10: 尾部空格优化

**作为** 应用开发者,
**我想要** 通过 `.optimizeTrailingSpace()` (@since 20) 控制尾部空白字符是否计入行宽,
**以便** 避免行尾不可见空格导致的意外宽度扩展。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 调用 `.optimizeTrailingSpace(true)` THEN 尾部空白字符不计入行宽度测量（`txt_paragraph.cpp:106` → Rosen `isTrailingSpaceOptimized`） | 正常 |
| AC-10.2 | WHEN 调用 `.optimizeTrailingSpace(false)` 或未设置 THEN 尾部空白字符计入行宽度（默认 false，`text_style.h:673`） | 异常 |

### US-11: CJK-拉丁自动间距

**作为** 应用开发者,
**我想要** 通过 `.enableAutoSpacing()` (@since 20) 自动在 CJK 字符和拉丁字母/数字之间插入间距,
**以便** 改善中英文混排的可读性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-11.1 | WHEN 调用 `.enableAutoSpacing(true)` THEN CJK 字符和相邻的拉丁字母/数字之间自动插入细间距（`txt_paragraph.cpp:96` → Rosen `enableAutoSpace`） | 正常 |
| AC-11.2 | WHEN 调用 `.enableAutoSpacing(false)` 或未设置 THEN 不自动插入间距（默认 false，`text_style.h:687`） | 异常 |
| AC-11.3 | WHEN enableAutoSpacing 属性变更 THEN 触发 PROPERTY_UPDATE_MEASURE 重新测量（`text_layout_property.h:183`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.8 | R-7, R-1, R-2, R-18, R-19 | N/A（存量） | 单测 | `test/unittest/core/pattern/text/` |
| AC-2.1~2.5 | R-8, R-2 | N/A | 单测 | 同上 |
| AC-3.1~3.5 | R-9, R-3 | N/A | 单测 | 同上 |
| AC-4.1~4.8 | R-10, R-4, R-20 | N/A | 单测 | 同上 |
| AC-5.1~5.5 | R-11 | N/A | 单测 | 同上 |
| AC-6.1~6.4 | R-12 | N/A | 单测 | 同上 |
| AC-7.1~7.4 | R-13, R-5 | N/A | 单测 | 同上 |
| AC-8.1~8.2 | R-14 | N/A | 单测 | 同上 |
| AC-9.1~9.2 | R-15 | N/A | 单测 | 同上 |
| AC-10.1~10.2 | R-16 | N/A | 单测 | 同上 |
| AC-11.1~11.3 | R-17 | N/A | 单测 | 同上 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ArkTS getter 返回 `TextOverflow::CLIP`（`text_model_ng.cpp:1319`）；C-API Reset 重置为 `TextOverflow::NONE`（`node_text_modifier.cpp:1092`）；两者在排版引擎中行为相同 | textOverflow 的 ArkTS 默认值（Clip）与 C-API Reset 值（NONE）不一致 | — | AC-1.7, AC-1.8 |
| R-2 | 行为 | maxLines 默认 UINT32_MAX（无限制），无限行数下文本不会溢出 | textOverflow 的 Clip/Ellipsis/None 模式需要配合 maxLines 才能观察到溢出截断效果 | — | AC-1.1, AC-1.2, AC-2.5 |
| R-3 | 行为 | `minLines = std::min(minLines, maxLines)`（`multiple_paragraph_layout_algorithm.cpp:1154`） | minLines 与 maxLines 的钳位关系：minLines ≤ maxLines | — | AC-3.2 |
| R-4 | 行为 | C++: HEAD/MIDDLE/TAIL/MULTILINE_HEAD/MULTILINE_MIDDLE；ArkTS: START/CENTER/END/MULTILINE_START/MULTILINE_CENTER（`text_enums.h:64-70`，`utils.h:622-633`） | ellipsisMode 的 C++ 内部枚举名与 ArkTS API 名不一致 | — | AC-4.1~4.5 |
| R-5 | 行为 | 循环减少 maxLines 直到文本高度适配约束（`text_layout_algorithm.cpp:1179-1203`） | heightAdaptivePolicy 在 LAYOUT_CONSTRAINT_FIRST 模式下会动态减少 maxLines | — | AC-7.1, AC-7.2 |
| R-6 | 行为 | 其他 10 项属性在 TextLineStyle 组内；enableAutoSpacing 直接存储在 TextLayoutProperty 上（`text_layout_property.h:183`） | enableAutoSpacing 使用 WITHOUT_GROUP 宏独立存储，不走 TextLineStyle 组传播链路 | — | AC-11.3 |
| R-7 | 行为 | 设置 TextOverflow 枚举值 | `textOverflow` 设置文本溢出行为 | `TextLayoutProperty` → TextLineStyle::propTextOverflow（`text_styles.h` TextLineStyle 组） | AC-1.1~1.8 |
| R-8 | 行为 | 设置正整数值 | `maxLines` 限制文本最大行数 | `TextLayoutProperty` → TextLineStyle::propMaxLines | AC-2.1~2.5 |
| R-9 | 行为 | 设置正整数值 | `minLines` 设置文本最小行数 (@since 22) | `TextLayoutProperty::propMinLines`（WITHOUT_GROUP，`text_layout_property.h:191`） | AC-3.1~3.5 |
| R-10 | 行为 | 设置 EllipsisMode 枚举值，需配合 textOverflow=Ellipsis | `ellipsisMode` 控制省略号位置 (@since 11) | `TextLayoutProperty` → TextLineStyle::propEllipsisMode | AC-4.1~4.8 |
| R-11 | 行为 | 设置 WordBreak 枚举值 | `wordBreak` 设置断词策略 (@since 11) | `TextLayoutProperty` → TextLineStyle::propWordBreak | AC-5.1~5.5 |
| R-12 | 行为 | 设置 LineBreakStrategy 枚举值 | `lineBreakStrategy` 设置换行质量策略 (@since 12) | `TextLayoutProperty` → TextLineStyle::propLineBreakStrategy | AC-6.1~6.4 |
| R-13 | 行为 | 设置 TextHeightAdaptivePolicy 枚举值 | `heightAdaptivePolicy` 控制高度自适应策略 (@since 10) | `TextLayoutProperty` → TextLineStyle::propHeightAdaptivePolicy | AC-7.1~7.4 |
| R-14 | 行为 | 设置 boolean | `compressLeadingPunctuation` 压缩行首标点 (@since 23) | `TextLayoutProperty` → TextLineStyle::propCompressLeadingPunctuation | AC-8.1~8.2 |
| R-15 | 行为 | 设置 boolean | `orphanCharOptimization` 孤字优化 (@since 26) | `TextLayoutProperty` → TextLineStyle::propOrphanCharOptimization | AC-9.1~9.2 |
| R-16 | 行为 | 设置 boolean | `optimizeTrailingSpace` 尾部空格优化 (@since 20) | `TextLayoutProperty` → TextLineStyle::propOptimizeTrailingSpace | AC-10.1~10.2 |
| R-17 | 行为 | 设置 boolean | `enableAutoSpacing` CJK-拉丁自动间距 (@since 20) | `TextLayoutProperty::propEnableAutoSpacing_`（WITHOUT_GROUP，`text_layout_property.h:183`） | AC-11.1~11.3 |
| R-18 | 异常 | JS 层传入非数字或超出 TEXT_OVERFLOWS 数组范围 | textOverflow 非法值处理 | 使用默认值 TextOverflow.NONE（`js_text.cpp:365`） | AC-1.7 |
| R-19 | 异常 | 文本实际宽度 ≤ 容器宽度 | TextOverflow.MARQUEE 文本未溢出 | 不启动跑马灯动画，文本静态显示（`text_paint_method.cpp:110`） | AC-1.6 |
| R-20 | 异常 | ellipsisMode 已设置但 textOverflow ≠ Ellipsis | ellipsisMode 无前置条件 | ellipsisMode 存储但不生效（省略号字符不注入） | AC-4.6 |
| R-21 | 异常 | 传入 ≤ 0 的值 | maxLines 为 0 或负值 | C-API 按 UINT32_MAX 处理；JS 层按 0 处理可能导致不显示文本 | AC-2.2 |
| R-22 | 异常 | 传入负值或非数字 | minLines 非法值 | 调用 ResetMinLines 清除属性（`js_text.cpp:524`） | AC-3.4 |
| R-23 | 异常 | C-API 传入超出 WORD_BREAK_TYPES 大小的值 | wordBreak 超出范围 | 回退到默认值 BREAK_WORD（index 2，`node_text_modifier.cpp:1610`） | AC-5.5 |
| R-24 | 异常 | JS 层传入非数字或超出范围 | lineBreakStrategy 非法值 | 回退到默认值 GREEDY（`js_text.cpp:408,412,417`） | AC-6.4 |
| R-25 | 恢复 | TextOverflow.MARQUEE 跑马灯动画运行中组件失焦 | 若 MarqueeStartPolicy=ON_FOCUS，暂停动画；重新获焦后恢复（`text_content_modifier.cpp:1875-1889`） | 动画从暂停位置（或起始位置，取决于 MarqueeUpdatePolicy）继续 | — |
| R-26 | 恢复 | 属性组懒初始化——TextLineStyle 属性组在首次设置任一行样式属性时通过 `GetOrCreateTextLineStyle()` 创建 | 未设置任何行样式属性时属性组为 null，各属性按主题默认值渲染 | 等同于全部使用主题默认值 | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-7 (textOverflow) | 单测 | Clip/Ellipsis/None 截断行为正确；MARQUEE 单行滚动 |
| VM-2 | R-8 (maxLines) | 单测 | 行数限制生效；与 textOverflow 配合正确 |
| VM-3 | R-9 (minLines) | 单测 | 高度扩展正确；与 maxLines 钳位关系正确 |
| VM-4 | R-10 (ellipsisMode) | 单测 | START/CENTER/END 省略号位置正确；MULTILINE 变体多行生效 |
| VM-5 | R-11 (wordBreak) | 单测 | NORMAL/BREAK_ALL/BREAK_WORD/HYPHENATION 断词行为正确 |
| VM-6 | R-12 (lineBreakStrategy) | 单测 | GREEDY/HIGH_QUALITY/BALANCED 换行质量差异可观察 |
| VM-7 | R-13 (heightAdaptivePolicy) | 单测 | 三种策略下 maxLines 和字号调整行为正确 |
| VM-8 | R-14~R-17 (排版优化属性) | 单测 | 各属性设置/重置/默认值行为正确 |
| VM-9 | R-1 (默认值分歧) | 单测 | 验证 ArkTS 和 C-API 两条路径的默认值差异 |

## API 变更分析

> 本特性为存量规格，记录各 API 的引入版本和当前签名。API 签名、d.ts 位置、权限等实现细节见 design.md。

### 新增 API

| API 名称 | 引入版本 | 类型 | 功能描述 | 关联 AC |
|----------|----------|------|----------|---------|
| `textOverflow(options: TextOverflowOptions)` | @since 7 | Public | 控制文本溢出行为 | AC-1.1~1.8 |
| `maxLines(value: number)` | @since 7 | Public | 限制最大行数 | AC-2.1~2.5 |
| `minLines(minLines: Optional<number>)` | @since 22 | Public | 设置最小行数 | AC-3.1~3.5 |
| `ellipsisMode(value: EllipsisMode)` | @since 11 | Public | 控制省略号位置 | AC-4.1~4.8 |
| `wordBreak(value: WordBreak)` | @since 11 | Public | 控制断词策略 | AC-5.1~5.5 |
| `lineBreakStrategy(strategy: LineBreakStrategy)` | @since 12 | Public | 控制换行质量策略 | AC-6.1~6.4 |
| `heightAdaptivePolicy(value: TextHeightAdaptivePolicy)` | @since 10 | Public | 控制高度自适应策略 | AC-7.1~7.4 |
| `compressLeadingPunctuation(enabled: Optional<boolean>)` | @since 23 | Public | 压缩行首标点 | AC-8.1~8.2 |
| `orphanCharOptimization(enabled: Optional<boolean>)` | @since 26 | Public | 孤字优化 | AC-9.1~9.2 |
| `optimizeTrailingSpace(optimize: Optional<boolean>)` | @since 20 | Public | 尾部空格优化 | AC-10.1~10.2 |
| `enableAutoSpacing(enabled: Optional<boolean>)` | @since 20 | Public | CJK-拉丁自动间距 | AC-11.1~11.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `textOverflow(options)` | @since 18 参数类型变更为 `TextOverflowOptions` | 从 `{overflow: TextOverflow}` 变更为 `TextOverflowOptions` | 兼容变更，无需迁移 | AC-1.1 |
| `EllipsisMode` 枚举 | @since 24 新增 `MULTILINE_START`, `MULTILINE_CENTER` | 新增枚举值，不影响现有代码 | 兼容扩展 | AC-4.4, AC-4.5 |
| `WordBreak` 枚举 | @since 18 新增 `HYPHENATION` | 新增枚举值，不影响现有代码 | 兼容扩展 | AC-5.4 |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否 — 所有属性行为与初始版本保持一致
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（textOverflow/maxLines）；API 10（heightAdaptivePolicy）；API 11（ellipsisMode/wordBreak）；API 12（lineBreakStrategy）；API 20（optimizeTrailingSpace/enableAutoSpacing）；API 22（minLines）；API 23（compressLeadingPunctuation）；API 24（EllipsisMode.MULTILINE_*）；API 26（orphanCharOptimization）
- **API 版本号策略:** 各 API 按 `@since` 标注引入版本；枚举扩展为兼容性新增

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| textOverflow + maxLines 配合 | textOverflow 的 Clip/Ellipsis/None 模式需要 maxLines 有限值才能观察到截断效果 | AC-1.1~1.3, AC-2.5 |
| ellipsisMode 前置条件 | ellipsisMode 仅在 textOverflow=Ellipsis 时生效；省略号字符（U+2026）仅在该条件下注入到 Rosen TypographyStyle | AC-4.6 |
| MARQUEE 模式隐式覆盖 | TextOverflow.MARQUEE 自动强制 maxLines=1、textIndent=0、换行符→空格、copyOption=None | AC-1.5 |
| minLines 独立存储 | minLines 使用 WITHOUT_GROUP 宏（不在 TextLineStyle 组内），仅影响 Frame 高度，不影响 Paragraph 布局 | AC-3.5 |
| enableAutoSpacing 独立存储 | enableAutoSpacing 使用 WITHOUT_GROUP 宏独立存储，不走 TextLineStyle 属性组的传播链路 | AC-11.3 |
| 排版引擎委托 | wordBreak/lineBreakStrategy/ellipsisMode/compressLeadingPunctuation/orphanCharOptimization/optimizeTrailingSpace/enableAutoSpacing 的实际排版逻辑均委托给 Rosen 排版引擎，ACE 仅负责属性传递 | 全部 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 11 项属性变更均触发 `PROPERTY_UPDATE_MEASURE`，仅脏节点重新测量；EllipsisMode.CENTER 强制 Paragraph 重建（性能代价高于其他模式） | benchmark | `test/benchmark/` |
| 性能 | marqueeOptions 属性变更仅触发 `PROPERTY_UPDATE_RENDER`（不重建 Paragraph） | benchmark | 同上 |

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
| 无障碍 | 是 | MARQUEE 跑马灯对屏幕阅读器不友好，需确保文本可通过无障碍 API 完整获取 | AC-1.4 |
| 大字体 | 是 | 大字体模式下更容易触发溢出截断，heightAdaptivePolicy 可配合调整 | AC-7.1~7.4 |
| 深色模式 | N/A | 溢出截断行为不受模式影响 | — |
| 多窗口/分屏 | 是 | 窗口尺寸变化可能改变文本容器宽度，触发溢出/截断状态变化 | AC-1.1~1.6, AC-2.1 |
| 多用户 | N/A | — | — |
| 版本升级 | 是 | API 18 新增 HYPHENATION/TextOverflowOptions 类型变更；API 24 新增 MULTILINE_* EllipsisMode | AC-5.4, AC-4.4~4.5 |
| 生态兼容 | N/A | — | — |

## 行为场景（Gherkin）

```gherkin
Feature: Text 溢出与截断
  作为应用开发者
  我想要通过声明式 API 控制 Text 组件的溢出截断和排版优化行为
  以便精确控制文本在空间受限场景下的视觉呈现

  Scenario: 基本省略号截断
    Given 一个 Text 组件，内容为超长文本
    When 设置 .maxLines(2) 和 .textOverflow({ overflow: TextOverflow.Ellipsis })
    Then 文本最多显示 2 行
    And 超出部分截断并在末尾显示省略号

  Scenario: 裁剪模式
    Given 一个 Text 组件，内容为超长文本
    When 设置 .maxLines(1) 和 .textOverflow({ overflow: TextOverflow.Clip })
    Then 文本最多显示 1 行
    And 超出部分被裁剪，无省略号

  Scenario: 跑马灯模式
    Given 一个 Text 组件，内容宽度超出容器宽度
    When 设置 .textOverflow({ overflow: TextOverflow.MARQUEE })
    Then 文本以单行滚动显示
    And maxLines 被强制为 1
    And textIndent 被强制为 0

  Scenario: 跑马灯内容未溢出
    Given 一个 Text 组件，内容宽度未超出容器宽度
    When 设置 .textOverflow({ overflow: TextOverflow.MARQUEE })
    Then 文本静态显示，不启动滚动动画

  Scenario Outline: 省略号位置控制
    Given 一个 Text 组件，设置 maxLines(1) 和 textOverflow(Ellipsis)
    When ellipsisMode 为 <mode>
    Then 省略号出现在 <position>

    Examples:
      | mode              | position              |
      | EllipsisMode.START | 文本开头               |
      | EllipsisMode.CENTER| 文本中间（分割比 0.6） |
      | EllipsisMode.END   | 文本末尾（默认）        |

  Scenario: ellipsisMode 前置条件不满足
    Given 一个 Text 组件，设置 maxLines(2)
    When textOverflow 为 Clip 且 ellipsisMode 为 START
    Then 省略号不显示，ellipsisMode 不生效

  Scenario Outline: 断词策略
    Given 一个 Text 组件，内容为英文长单词
    When wordBreak 为 <strategy>
    Then <behavior>

    Examples:
      | strategy              | behavior                          |
      | WordBreak.NORMAL      | 在默认 Unicode 断行点换行           |
      | WordBreak.BREAK_ALL   | 允许在字母中间断行                  |
      | WordBreak.BREAK_WORD  | 优先在词边界断行（默认）             |
      | WordBreak.HYPHENATION  | 按音节断行并插入连字符               |

  Scenario: minLines 高度扩展
    Given 一个 Text 组件，内容仅一行文字
    When 设置 .minLines(3)
    Then 组件高度至少可容纳 3 行
    And 文本仍然只显示 1 行

  Scenario: minLines 被 maxLines 钳位
    Given 一个 Text 组件
    When 设置 .maxLines(2) 和 .minLines(5)
    Then minLines 实际值被钳位为 2

  Scenario: LAYOUT_CONSTRAINT_FIRST 动态减行
    Given 一个 Text 组件，设置固定高度约束和 maxLines(UINT32_MAX)
    When heightAdaptivePolicy 为 LAYOUT_CONSTRAINT_FIRST
    Then 从约束高度计算最大可容纳行数
    And 循环减少行数直到内容适配高度约束

  Scenario: CJK-拉丁自动间距
    Given 一个 Text 组件，内容为 "Hello你好World"
    When 设置 .enableAutoSpacing(true)
    Then "Hello" 和 "你" 之间以及 "好" 和 "World" 之间自动插入细间距

  Scenario: 行首标点压缩
    Given 一个 Text 组件，某行以 "「" 开头
    When 设置 .compressLeadingPunctuation(true)
    Then 行首 "「" 被压缩为半宽显示
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
    query: "Text 组件溢出截断属性存储和布局触发机制"
  - repo: "openharmony/interface_sdk-js"
    query: "Text 组件 textOverflow/ellipsisMode/wordBreak API 签名和版本变更"
```

**关键文档：**
- SDK 动态版声明: `interface/sdk-js/api/@internal/component/ets/text.d.ts`
- SDK 静态版声明: `interface/sdk-js/api/arkui/component/text.static.d.ets`
- C API 枚举定义: `interfaces/native/native_node.h`
- C API 类型定义: `interfaces/native/native_type.h`
