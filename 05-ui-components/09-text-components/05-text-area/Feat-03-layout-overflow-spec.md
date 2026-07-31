# 特性规格

> Func-05-09-05-Feat-03 行布局与溢出截断：固化 textAlign、textOverflow/maxLines/minLines、minFontSize/maxFontSize/minFontScale/maxFontScale/heightAdaptivePolicy、wordBreak/lineBreakStrategy/ellipsisMode、horizontalScrolling、orphanCharOptimization/compressLeadingPunctuation/punctuationOverflow、textDirection、style(DEFAULT/INLINE) 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 行布局与溢出截断 (Line Layout & Overflow Truncation) |
| 特性编号 | Func-05-09-05-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 @since 7（textAlign）、@since 10（maxLines/style/barState）、@since 12（textOverflow/textIndent/minFontSize/maxFontSize/heightAdaptivePolicy/wordBreak/lineBreakStrategy）、@since 18（minFontScale/maxFontScale/halfLeading/ellipsisMode）、@since 20（autoCapitalizationMode/maxLines 重载）、@since 23（compressLeadingPunctuation/textDirection/includeFontPadding/fallbackLineSpacing）、@since 24（minLines/horizontalScrolling）；静态 @since 23 static |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | textAlign | JUSTIFY 对 TextInput 强制为 START；TextArea 支持 JUSTIFY |
| ADDED | textOverflow/maxLines/minLines | 截断仅当 textOverflow 非 DEFAULT 生效；maxLines 拆 MaxViewLines/NormalMaxViewLines/OverflowMode |
| ADDED | 自适应字号 minFontSize/maxFontSize/minFontScale/maxFontScale/heightAdaptivePolicy | 三策略 MAX_LINES_FIRST/MIN_FONT_SIZE_FIRST/LAYOUT_CONSTRAINT_FIRST |
| ADDED | wordBreak/lineBreakStrategy/ellipsisMode | 透传 Rosen 排版引擎 |
| ADDED | horizontalScrolling | pattern 成员存储；仅 TextArea+非 inline+无 voiceButton 生效 |
| ADDED | orphanCharOptimization/compressLeadingPunctuation/punctuationOverflow | bool 透传 Rosen |
| ADDED | textDirection | INHERIT→内容推导；AUTO→内容推导；LTR/RTL→显式 |
| ADDED | style(DEFAULT/INLINE) | paint 属性；INLINE 影响 overflow 默认/maxViewLines/counter |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/05-text-area/design.md` | Baselined |

---

## 用户故事

### US-1: 设置文本对齐

**作为** 应用开发者,
**我想要** 通过 textAlign 控制多行文本对齐方式,
**以便** 实现左对齐/居中/右对齐/两端对齐排版。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.textAlign(TextAlign.Start/Center/End)` THEN 文本按指定对齐，写 TextAlign（PROPERTY_UPDATE_MEASURE_SELF）（`text_field_model_ng.cpp:496`） | 正常 |
| AC-1.2 | WHEN TextArea 调用 `.textAlign(TextAlign.Justify)` THEN JUSTIFY 生效，末行按 Start 对齐（`text_field_layout_algorithm.cpp:260`） | 正常 |
| AC-1.3 | WHEN 未设置 textAlign THEN 默认 TextAlign.Start（`text_field_layout_algorithm.cpp:845`） | 异常 |

### US-2: 设置溢出与行数限制

**作为** 应用开发者,
**我想要** 通过 textOverflow/maxLines/minLines 控制文本溢出截断与行数,
**以便** 在有限空间内合理展示多行文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.textOverflow(TextOverflow.Ellipsis)` + `.maxLines(3)` THEN 超过 3 行时末尾显示省略号（截断仅当 textOverflow 非 DEFAULT 生效，`text_field_layout_algorithm.cpp:172-174`） | 正常 |
| AC-2.2 | WHEN 未设置 textOverflow THEN TextArea 默认 CLIP；INLINE+非 TextArea 默认 ELLIPSIS（`text_field_layout_algorithm.cpp:176-178`） | 异常 |
| AC-2.3 | WHEN textOverflow=Marquee THEN TextArea 强制为 CLIP（不支持 Marquee）；INLINE+非 TextArea 强制为 ELLIPSIS（`text_field_layout_algorithm.cpp:185-191`） | 边界 |
| AC-2.4 | WHEN 调用 `.maxLines(value, options)` THEN 拆写 MaxViewLines/NormalMaxViewLines/OverflowMode（`text_area_static_modifier.cpp:1055-1068`） | 正常 |
| AC-2.5 | WHEN maxLines=0 THEN 钳为 DEFAULT_MAX_VIEW_LINE=3（`text_field_model_static.cpp:272`） | 边界 |
| AC-2.6 | WHEN OverflowMode=Scroll 且 textOverflow 为 NONE/CLIP/DEFAULT THEN maxLines 无限（ShouldUseInfiniteMaxLines=true）（`text_field_layout_algorithm.cpp:1701`） | 正常 |
| AC-2.7 | WHEN 调用 `.minLines(value)` (@since 24) THEN 钳 value<=0 为 1（`text_field_model_static.cpp:1051`）；高度扩展经 paragraph measure | 正常 |
| AC-2.8 | WHEN ellipsisMode=Head/Middle 且 maxLines=1 THEN 生效；其他 maxLines 仅 Tail 生效（SDK NOTE） | 边界 |
| AC-2.9 | WHEN ellipsisMode 未设置或 overflow 非 ELLIPSIS THEN 不生效（`text_field_layout_algorithm.cpp:192-194`） | 边界 |

### US-3: 自适应字号

**作为** 应用开发者,
**我想要** 通过 heightAdaptivePolicy/minFontScale/maxFontScale 控制字号自适应缩放,
**以便** 文本在固定高度内自动适配显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.heightAdaptivePolicy(MAX_LINES_FIRST)` THEN maxLines 优先；超出则字号缩到 [minFontSize,maxFontSize]（`text_field_layout_algorithm.cpp:1318-1322`） | 正常 |
| AC-3.2 | WHEN 调用 `.heightAdaptivePolicy(MIN_FONT_SIZE_FIRST)` THEN minFontSize 优先；能一行则放大到最大可容纳字号（`text_field_layout_algorithm.cpp:1332-1336`） | 正常 |
| AC-3.3 | WHEN 调用 `.heightAdaptivePolicy(LAYOUT_CONSTRAINT_FIRST)` THEN 布局约束优先；超出则缩字号（`text_field_layout_algorithm.cpp:1325-1329`） | 正常 |
| AC-3.4 | WHEN 调用 `.minFontScale(value)` (@since 18) THEN 钳 std::clamp(value, 0.0f, 1.0f)（`text_field_model_static.cpp:814`） | 正常 |
| AC-3.5 | WHEN 调用 `.maxFontScale(value)` (@since 18) THEN 钳 std::max(value, 1.0f)（`text_field_model_static.cpp:823`） | 正常 |
| AC-3.6 | WHEN minFontScale<0 THEN 钳为 0；>1 THEN 钳为 1 | 边界 |
| AC-3.7 | WHEN maxFontScale<1 THEN 钳为 1 | 边界 |
| AC-3.8 | WHEN 自适应生效 THEN fontSize 不生效（字号由自适应算法决定） | 边界 |

### US-4: 换行与断词

**作为** 应用开发者,
**我想要** 通过 wordBreak/lineBreakStrategy 控制断词与断行策略,
**以便** 多语言文本按预期换行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.wordBreak(BREAK_ALL)` THEN 词中间断行；默认 BREAK_WORD（`text_field_layout_algorithm.cpp:182`）；仅 TextArea 或 INLINE 生效 | 正常 |
| AC-4.2 | WHEN 调用 `.lineBreakStrategy(GREEDY)` THEN 默认 GREEDY（`text_field_layout_algorithm.cpp:846`）；仅在 wordBreak 非 BREAK_ALL 时生效 | 正常 |
| AC-4.3 | WHEN wordBreak 未设于非 TextArea 非 INLINE THEN 不生效 | 边界 |

### US-5: 水平滚动

**作为** 应用开发者,
**我想要** 通过 horizontalScrolling 启用文本水平滚动,
**以便** 长文本在不换行时可横向浏览。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.horizontalScrolling(true)` (@since 24) THEN 设 isHorizontalScrolling_（pattern 成员）；经动态桥 SetHorizontalScrolling 写入（`text_area_dynamic_modifier.cpp:2173`） | 正常 |
| AC-5.2 | WHEN horizontalScrolling=true 且 TextArea 且非 INLINE 且无 voiceButton THEN IsHorizontalScrollEnabled()=true（`text_field_pattern.h:1980-1982`） | 正常 |
| AC-5.3 | WHEN 非 TextArea 或 INLINE 或 voiceButton 模式 THEN horizontalScrolling 不生效 | 边界 |
| AC-5.4 | WHEN 水平滚动启用 THEN paragraph Layout(infinity) 后 Layout(longestLine)；autoWidth 被跳过（`text_field_layout_algorithm.cpp:638-651`） | 正常 |
| AC-5.5 | WHEN 静态版 SetHorizontalScrollingImpl 调用 THEN 桩函数为空 no-op（`text_area_static_modifier.cpp:995-1000`），实际经动态桥 | 边界 |

### US-6: 排版优化

**作为** 应用开发者,
**我想要** 通过 orphanCharOptimization/compressLeadingPunctuation/punctuationOverflow 控制排版微调,
**以便** 提升中文标点与孤行的排版质量。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.orphanCharOptimization(true)` (@since 26) THEN 写 OrphanCharOptimization，默认 false，传 Rosen orphanCharOptimization（`txt_paragraph.cpp:107`） | 正常 |
| AC-6.2 | WHEN 调用 `.compressLeadingPunctuation(true)` (@since 23) THEN 写 CompressLeadingPunctuation，默认 false，传 Rosen compressHeadPunctuation（`txt_paragraph.cpp:108`） | 正常 |
| AC-6.3 | WHEN 调用 `.punctuationOverflow(true)` (@since 26) THEN 写 PunctuationOverflow，默认 false，传 Rosen punctuationOverflow（`txt_paragraph.cpp:109`） | 正常 |

### US-7: 文本方向

**作为** 应用开发者,
**我想要** 通过 textDirection 控制文本方向,
**以便** 支持 LTR/RTL 及内容自动推导方向。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.textDirection(LTR/RTL)` (@since 23) THEN 显式方向生效（`text_field_model_ng.cpp:1295`） | 正常 |
| AC-7.2 | WHEN textDirection=INHERIT（默认） THEN 方向由布局方向推导；AUTO 则由内容推导（`paragraph_util.cpp:66-79`） | 正常 |
| AC-7.3 | WHEN 未设置 textDirection THEN 默认 INHERIT；主段落方向为内容推导（algorithm 成员 direction_=AUTO/textDirection_=INHERIT 从不重赋）（`text_field_layout_algorithm.h:177-178`） | 边界 |

### US-8: 设置样式（DEFAULT/INLINE）

**作为** 应用开发者,
**我想要** 通过 style(DEFAULT/INLINE) 切换 TextArea 显示样式,
**以便** 在内联与默认模式下获得不同的溢出/行数/装饰行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `.style(TextContentStyle.Inline)` THEN 写 InputStyle=INLINE（paint 属性 PROPERTY_UPDATE_RENDER）（`text_field_model_ng.cpp:616`） | 正常 |
| AC-8.2 | WHEN INLINE 生效需满足 IsNormalInlineState()=InputStyle==INLINE 且 TextInputType 为 UNSPECIFIED/TEXT（`text_field_pattern.cpp:9360-9370`） | 正常 |
| AC-8.3 | WHEN INLINE 模式 THEN MaxViewLines 默认 3（INLINE_DEFAULT_VIEW_MAXLINE）；DEFAULT 模式 TextArea 无限行 | 边界 |
| AC-8.4 | WHEN INLINE 模式未设置 textOverflow THEN 默认 ELLIPSIS；DEFAULT 模式 TextArea 默认 CLIP（`text_field_layout_algorithm.cpp:176-178`） | 边界 |
| AC-8.5 | WHEN INLINE 模式 THEN counter/password-icon 装饰被抑制（`text_component_decorator.cpp:336,393`） | 正常 |
| AC-8.6 | WHEN INLINE 失焦 THEN MaxLines/PlaceholderMaxLines reset 为 1（`text_field_pattern.cpp:1930-1938`） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1~R-3 | TASK-03 | XTS textAlign | text_field_model_ng.cpp:496 |
| AC-2.1~2.9 | R-4~R-10 | TASK-03 | XTS overflow/maxLines | text_field_layout_algorithm.cpp:168-194 |
| AC-3.1~3.8 | R-11~R-15 | TASK-03 | XTS 自适应字号 | text_field_layout_algorithm.cpp:1317-1336 |
| AC-4.1~4.3 | R-16~R-17 | TASK-03 | XTS wordBreak/lineBreakStrategy | txt_paragraph.cpp:85,88 |
| AC-5.1~5.5 | R-18~R-20 | TASK-03 | XTS horizontalScrolling | text_field_pattern.h:1980-1982 |
| AC-6.1~6.3 | R-21~R-23 | TASK-03 | XTS 排版优化 | txt_paragraph.cpp:107-109 |
| AC-7.1~7.3 | R-24~R-26 | TASK-03 | XTS textDirection | paragraph_util.cpp:66-79 |
| AC-8.1~8.6 | R-27~R-31 | TASK-03 | XTS style | text_field_pattern.cpp:9360 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 textAlign | 写 TextAlign(MEASURE_SELF) | 默认 Start | AC-1.1,1.3 |
| R-2 | 行为 | TextArea+JUSTIFY | JUSTIFY 生效，末行 Start | — | AC-1.2 |
| R-3 | 边界 | 非 TextArea+JUSTIFY | 强制为 START | — | — |
| R-4 | 行为 | 设置 textOverflow 非 DEFAULT | 截断生效 | 仅非 DEFAULT 截断 | AC-2.1 |
| R-5 | 边界 | 未设 textOverflow | TextArea=CLIP；INLINE+非TextArea=ELLIPSIS | — | AC-2.2 |
| R-6 | 边界 | textOverflow=Marquee | TextArea=CLIP；INLINE+非TextArea=ELLIPSIS | TextArea 不支持 Marquee | AC-2.3 |
| R-7 | 行为 | 设置 maxLines(value,options) | 拆写 MaxViewLines/NormalMaxViewLines/OverflowMode | 0→3 | AC-2.4,2.5 |
| R-8 | 行为 | OverflowMode=Scroll+overflow 非 ELLIPSIS | maxLines 无限 | — | AC-2.6 |
| R-9 | 行为 | 设置 minLines | 钳 <=0 为 1；高度扩展 | @since 24 | AC-2.7 |
| R-10 | 边界 | ellipsisMode | 仅 overflow=ELLIPSIS 生效；Head/Middle 仅 maxLines=1 | 默认 TAIL | AC-2.8,2.9 |
| R-11 | 行为 | heightAdaptivePolicy=MAX_LINES_FIRST | maxLines 优先→缩字号 | 默认 | AC-3.1 |
| R-12 | 行为 | heightAdaptivePolicy=MIN_FONT_SIZE_FIRST | minFontSize 优先→放大 | — | AC-3.2 |
| R-13 | 行为 | heightAdaptivePolicy=LAYOUT_CONSTRAINT_FIRST | 约束优先→缩字号 | — | AC-3.3 |
| R-14 | 行为 | 设置 minFontScale | clamp[0,1] | @since 18 | AC-3.4,3.6 |
| R-15 | 行为 | 设置 maxFontScale | max(,1) | @since 18 | AC-3.5,3.7 |
| R-16 | 行为 | 设置 wordBreak | 传 Rosen；仅 TextArea/INLINE | 默认 BREAK_WORD | AC-4.1,4.3 |
| R-17 | 行为 | 设置 lineBreakStrategy | 传 Rosen；wordBreak 非 BREAK_ALL 时生效 | 默认 GREEDY | AC-4.2 |
| R-18 | 行为 | 设置 horizontalScrolling | 写 pattern 成员（动态桥） | @since 24 | AC-5.1 |
| R-19 | 边界 | IsHorizontalScrollEnabled | 仅 TextArea+非 INLINE+无 voiceButton | — | AC-5.2,5.3 |
| R-20 | 边界 | 静态 SetHorizontalScrollingImpl | 桩 no-op，实际经动态桥 | — | AC-5.5 |
| R-21 | 行为 | 设置 orphanCharOptimization | 传 Rosen orphanCharOptimization | 默认 false @since 26 | AC-6.1 |
| R-22 | 行为 | 设置 compressLeadingPunctuation | 传 Rosen compressHeadPunctuation | 默认 false @since 23 | AC-6.2 |
| R-23 | 行为 | 设置 punctuationOverflow | 传 Rosen punctuationOverflow | 默认 false @since 26 | AC-6.3 |
| R-24 | 行为 | 设置 textDirection LTR/RTL | 显式方向 | @since 23 | AC-7.1 |
| R-25 | 行为 | textDirection=INHERIT/AUTO | 内容推导方向 | 默认 INHERIT | AC-7.2 |
| R-26 | 边界 | 未设 textDirection | 主段落内容推导；algorithm 成员不重赋 | — | AC-7.3 |
| R-27 | 行为 | 设置 style=INLINE | 写 InputStyle(paint RENDER) | 需满足 IsNormalInlineState | AC-8.1,8.2 |
| R-28 | 边界 | INLINE 默认 MaxViewLines=3 | — | DEFAULT TextArea 无限 | AC-8.3 |
| R-29 | 边界 | INLINE 默认 overflow=ELLIPSIS | — | DEFAULT=CLIP | AC-8.4 |
| R-30 | 行为 | INLINE 抑制 counter/password 装饰 | — | — | AC-8.5 |
| R-31 | 边界 | INLINE 失焦 reset MaxLines=1 | — | — | AC-8.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|----------|----------|
| VM-1 | AC-1.x textAlign | XTS + Inspector | TextAlign 值；JUSTIFY 生效 |
| VM-2 | AC-2.x overflow/maxLines | XTS + 布局测量 | 截断行为；maxLines 拆写；Scroll 无限 |
| VM-3 | AC-3.x 自适应字号 | XTS + 布局测量 | 三策略字号缩放；clamp |
| VM-4 | AC-4.x wordBreak/lineBreakStrategy | XTS + Rosen | 断词/断行策略 |
| VM-5 | AC-5.x horizontalScrolling | XTS + 滚动验证 | 水平滚动；条件门控 |
| VM-6 | AC-6.x 排版优化 | XTS + Rosen | bool 透传 |
| VM-7 | AC-7.x textDirection | XTS + 布局 | 方向推导 |
| VM-8 | AC-8.x style | XTS + Inspector | INLINE/DEFAULT 行为差异 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| textAlign(value) | Public | TextAlign | this | 无 | 文本对齐 | AC-1.x |
| textOverflow(value) | Public | TextOverflow | this | 无 | 溢出模式 | AC-2.x |
| maxLines(value, options?) | Public | number, MaxLinesOptions? | this | 无 | 最大行数 | AC-2.x |
| minLines(lines) | Public | number | this | 无 | 最小行数 | AC-2.7 |
| minFontSize(value) | Public | number/string/Resource | this | 无 | 最小字号 | AC-3.x |
| maxFontSize(value) | Public | number/string/Resource | this | 无 | 最大字号 | AC-3.x |
| minFontScale(scale) | Public | number/Resource | this | 无 | 最小缩放 | AC-3.4 |
| maxFontScale(scale) | Public | number/Resource | this | 无 | 最大缩放 | AC-3.5 |
| heightAdaptivePolicy(value) | Public | TextHeightAdaptivePolicy | this | 无 | 自适应策略 | AC-3.x |
| wordBreak(value) | Public | WordBreak | this | 无 | 断词 | AC-4.x |
| lineBreakStrategy(strategy) | Public | LineBreakStrategy | this | 无 | 断行策略 | AC-4.x |
| ellipsisMode(mode) | Public | EllipsisMode | this | 无 | 省略模式 | AC-2.8 |
| horizontalScrolling(enabled) | Public | boolean | this | 无 | 水平滚动 | AC-5.x |
| orphanCharOptimization(enabled) | Public | boolean | this | 无 | 孤行优化 | AC-6.1 |
| compressLeadingPunctuation(enabled) | Public | boolean | this | 无 | 标点压缩 | AC-6.2 |
| punctuationOverflow(enabled) | Public | boolean | this | 无 | 标点溢出 | AC-6.3 |
| textDirection(direction) | Public | TextDirection | this | 无 | 文本方向 | AC-7.x |
| style(value) | Public | TextContentStyle | this | 无 | 样式 | AC-8.x |

> **SDK 交叉验证：** 均经 `textArea.static.d.ets` 与 `text_area.d.ts` 核对。

## 接口规格

### 接口定义

| 接口 | 签名概要 | 开放范围 | 关联 AC |
|------|----------|----------|---------|
| 布局对齐 | textAlign | Public | AC-1.x |
| 溢出截断 | textOverflow/maxLines/minLines/ellipsisMode | Public | AC-2.x |
| 自适应字号 | minFontSize/maxFontSize/minFontScale/maxFontScale/heightAdaptivePolicy | Public | AC-3.x |
| 断词断行 | wordBreak/lineBreakStrategy | Public | AC-4.x |
| 水平滚动 | horizontalScrolling | Public | AC-5.x |
| 排版优化 | orphanCharOptimization/compressLeadingPunctuation/punctuationOverflow | Public | AC-6.x |
| 文本方向 | textDirection | Public | AC-7.x |
| 样式 | style | Public | AC-8.x |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| maxLines | number | 是 | 无 | 0→3 |
| minLines | number | 是 | 1 | <=0→1 |
| minFontScale | number | 是 | 0 | clamp[0,1] |
| maxFontScale | number | 是 | INT32_MAX | max(,1) |
| ellipsisMode | EllipsisMode | 是 | TAIL | 仅 overflow=ELLIPSIS 生效 |
| horizontalScrolling | boolean | 是 | false | 仅 TextArea+非INLINE+无voiceButton |
| textDirection | TextDirection | 是 | INHERIT | — |
| style | TextContentStyle | 是 | DEFAULT | INLINE 需 type=UNSPECIFIED/TEXT |

## 兼容性声明

- **已有 API 行为变更:** 否。textAlign JUSTIFY 对 TextInput 强制 START 是固有行为。horizontalScrolling 静态版 SetHorizontalScrollingImpl 为桩 no-op，实际经动态桥——风险项。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 动态 @since 7/10/12/18/23/24/26；静态 @since 23 static
- **API 版本号策略:** 同 Feat-02

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 截断条件 | 仅 textOverflow 非 DEFAULT 且设置 maxLines 时截断生效 | AC-2.1 |
| maxLines 拆写 | C-API 拆为 MaxViewLines/NormalMaxViewLines/OverflowMode | AC-2.4 |
| ShouldUseInfiniteMaxLines | OverflowMode=Scroll + overflow 非 ELLIPSIS → 无限 | AC-2.6 |
| IsHorizontalScrollEnabled 门控 | 仅 TextArea+非INLINE+无voiceButton | AC-5.2 |
| textDirection 不重赋 algorithm 成员 | 主段落方向内容推导 | AC-7.3 |
| style 为 paint 属性 | InputStyle 存 paint，PROPERTY_UPDATE_RENDER | AC-8.1 |
| INLINE 条件 | 需 type=UNSPECIFIED/TEXT | AC-8.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 自适应字号二分搜索缩放单帧完成 | XTS 帧率 | text_field_layout_algorithm.cpp:1303 |
| 性能 | horizontalScrolling paragraph Layout(infinity) 性能影响 | 性能测试 | text_field_layout_algorithm.cpp:640 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | textAlign/overflow 影响无障碍文本可读性 | AC-1.x,2.x |
| 大字体 | 是 | minFontScale/maxFontScale 限制系统字体缩放范围 | AC-3.4,3.5 |
| 深色模式 | 否 | 本 Feat 不涉及颜色 | — |
| 多窗口/分屏 | 是 | horizontalScrolling 水平滚动行为 | AC-5.x |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | minFontScale/maxFontScale/halfLeading/ellipsisMode @since 18；textDirection/compressLeadingPunctuation @since 23；minLines/horizontalScrolling @since 24；orphanCharOptimization/punctuationOverflow @since 26 | AC-3.4,5.1,6.1 |
| 生态兼容 | 是 | textDirection INHERIT/AUTO 依赖内容推导，跨语言文本可能方向不一致 | AC-7.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: TextArea 行布局与溢出截断
  作为 应用开发者
  我想要 控制对齐、溢出、行数、自适应字号、断词、方向、样式
  以便 多行文本精确排版

  Scenario Outline: textOverflow 默认值随 style 变化
    Given 未设置 textOverflow
    When style 为 <styleValue>
    Then textOverflow 默认为 <预期>

    Examples:
      | styleValue | 预期 |
      | DEFAULT | CLIP |
      | INLINE | ELLIPSIS |

  Scenario: maxLines + OverflowMode=Scroll 实现行数无限
    Given 设置 .maxLines(3, { overflowMode: OverflowMode.SCROLL }) 且 textOverflow 未设为 ELLIPSIS
    When 文本超过 3 行
    Then 不截断，文本可滚动（ShouldUseInfiniteMaxLines=true）

  Scenario: heightAdaptivePolicy 三策略
    Given 设置 minFontSize=10fp maxFontSize=20fp maxLines=3
    When 文本超出 3 行
    Then MAX_LINES_FIRST: 先截断到 3 行，再缩字号
    And MIN_FONT_SIZE_FIRST: 先用 minFontSize，再放大
    And LAYOUT_CONSTRAINT_FIRST: 先按约束，再缩字号
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "maxLines 为何拆为 MaxViewLines/NormalMaxViewLines/OverflowMode 三个属性"
  - repo: "openharmony/arkui_ace_engine"
    query: "horizontalScrolling 静态版 SetHorizontalScrollingImpl 为何是 no-op 桩"
  - repo: "openharmony/arkui_ace_engine"
    query: "textDirection 为何不重赋 algorithm 成员 direction_/textDirection_"
  - repo: "openharmony/arkui_ace_engine"
    query: "style INLINE 与 DEFAULT 在 overflow 默认值/maxViewLines/counter 上的行为差异"
```

**关键文档：** `specs/05-ui-components/09-text-components/05-text-area/design.md`（DESIGN-Func-05-09-05）；SDK `textArea.static.d.ets` / `text_area.d.ts`
