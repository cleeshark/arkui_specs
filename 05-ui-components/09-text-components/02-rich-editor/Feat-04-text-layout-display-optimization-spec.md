# 特性规格

> Func-05-09-02-Feat-04 文本排版与显示优化：固化 RichEditor 组件 11 个 `RichEditorAttribute` 排版属性的行为规格，涵盖中西文自动间距（`enableAutoSpacing`）、标点压缩与悬挂（`compressLeadingPunctuation`/`punctuationOverflow`）、字体内边距与回退行距（`includeFontPadding`/`fallbackLineSpacing`）、孤字优化（`orphanCharOptimization`）、水平滚动与单行模式（`horizontalScrolling`/`singleLine`）、撤销样式（`undoStyle`）、内容长度与行数限制（`maxLength`/`maxLines`），重点记录属性在 Pattern 成员变量、LayoutProperty 层级、ParagraphStyle 构建管道中的存储与消费路径。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 文本排版与显示优化 (Text Layout & Display Optimization) |
| 特性编号 | Func-05-09-02-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 10+（`maxLength`/`maxLines`），API 20+（`enableAutoSpacing`），API 23+（`compressLeadingPunctuation`/`includeFontPadding`/`fallbackLineSpacing`），API 26+（`punctuationOverflow`/`orphanCharOptimization`/`horizontalScrolling`） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐 11 个排版属性行为规格 | 固化 Bridge → ModelNG → Pattern → LayoutProperty 全链路调用关系与属性更新标志 |
| MODIFIED | 补齐属性存储位置分层说明 | 部分存 `TextLayoutProperty` 基类，部分在 `TextLineStyle` 属性组，部分仅存 Pattern 成员 |
| MODIFIED | 补齐 `paragraphCache_.Clear()` 副作用 | 排版属性变更均触发段落缓存清除，部分额外触发 `MarkDirtyNode(PROPERTY_UPDATE_MEASURE)` |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/02-rich-editor/design.md` | 已创建 |
| SDK 声明 | `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/richEditor.ets` | 已存在 |

---

## 用户故事

### US-1: 中西文自动间距控制

**作为** 应用开发者, **我想要** 通过 `enableAutoSpacing` 控制 CJK 与拉丁字符间的自动间距, **以便** 在混合文本场景下获得更自然的排版效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `enableAutoSpacing(true)` THEN Bridge `SetEnableAutoSpacing` 解析布尔参数调用 `setRichEditorEnableAutoSpacing`，非布尔则 reset（`arkts_native_rich_editor_bridge.cpp:2939-2956`） | 正常 |
| AC-1.2 | WHEN ModelNG `SetEnableAutoSpacing(enabled)` 执行 THEN 调用 `ACE_UPDATE_LAYOUT_PROPERTY(EnableAutoSpacing)` 并 `pattern->SetEnableAutoSpacing(enabled)`（`rich_editor_model_ng.cpp:923-931`） | 正常 |
| AC-1.3 | WHEN Pattern `SetEnableAutoSpacing` 值变化 THEN 设置 `isEnableAutoSpacing_` 并 `paragraphCache_.Clear()`（`rich_editor_pattern.cpp:14597-14603`） | 正常 |
| AC-1.4 | WHEN 布局构建 TextStyle THEN 从 `GetEnableAutoSpacingValue(false)` 读取并设置到 TextStyle（`multiple_paragraph_layout_algorithm.cpp:189`） | 正常 |

### US-2: 标点压缩与悬挂处理

**作为** 应用开发者, **我想要** 通过 `compressLeadingPunctuation` 和 `punctuationOverflow` 控制标点压缩与悬挂, **以便** 获得更紧凑的排版。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `compressLeadingPunctuation(true)` (@since 23) THEN Bridge → ModelNG 写 LayoutProperty（TextLineStyle 组）+ Pattern Set + `paragraphCache_.Clear()`（`bridge:2971-2988`, `model_ng:969-977`, `pattern:14623-14629`） | 正常 |
| AC-2.2 | WHEN 调用 `punctuationOverflow(true)` (@since 26) THEN 同 AC-2.1 模式，属性定义在 `text_layout_property.h:176`（`bridge:3003-3020`, `model_ng:987-995`, `pattern:14636-14642`） | 正常 |
| AC-2.3 | WHEN ParagraphStyle 构建 THEN `paragraph_util.cpp:45-46` 将 `CompressLeadingPunctuation` 和 `PunctuationOverflow` 写入段落样式结构体 | 正常 |
| AC-2.4 | WHEN 传入非布尔值 THEN Bridge 调用 reset 恢复默认 false | 边界 |

### US-3: 字体内边距与回退行距控制

**作为** 应用开发者, **我想要** 通过 `includeFontPadding` 和 `fallbackLineSpacing` 控制行高计算, **以便** 在不同字体场景下获得精确行高。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `includeFontPadding(true)` (@since 23) THEN Pattern Set → `GetContentHost()->MarkDirtyNode(PROPERTY_UPDATE_MEASURE)` + `paragraphCache_.Clear()`（`pattern:15027-15036`） | 正常 |
| AC-3.2 | WHEN 调用 `fallbackLineSpacing(true)` (@since 23) THEN 同 AC-3.1 模式（`pattern:15043-15052`） | 正常 |
| AC-3.3 | WHEN 布局构建 TextStyle THEN `multiple_paragraph_layout_algorithm.cpp:201-202` 从布局属性读取并设置到 TextStyle | 正常 |
| AC-3.4 | WHEN 属性变更检测 THEN `text_pattern.cpp:8999-9000` 检测值变化以决定是否触发重新布局 | 边界 |

### US-4: 孤字优化

**作为** 应用开发者, **我想要** 通过 `orphanCharOptimization` 防止孤立字符, **以便** 获得更符合排版规范的段落显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `orphanCharOptimization(true)` (@since 26) THEN Bridge → ModelNG 写 LayoutProperty（TextLineStyle 组）+ Pattern Set + `paragraphCache_.Clear()`（`bridge:3247-3264`, `model_ng:913-921`, `pattern:14610-14616`） | 正常 |
| AC-4.2 | WHEN 布局构建 THEN `paragraph_util.cpp:44` 写入 ParagraphStyle，`multiple_paragraph_layout_algorithm.cpp:200` 写入 TextStyle — 双消费路径 | 正常 |

### US-5: 水平滚动与单行模式

**作为** 应用开发者, **我想要** 通过 `horizontalScrolling` 启用水平滚动、通过 `singleLine` 强制单行显示, **以便** 控制滚动方向和显示模式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `horizontalScrolling(true)` (@since 26) THEN Pattern Set `isHorizontalScrolling_` + `needResetScrollBar_` + `MarkDirtyNode(MEASURE)` + `paragraphCache_.Clear()`，不写 LayoutProperty（`pattern:10962-10973`） | 正常 |
| AC-5.2 | WHEN `InitScrollablePattern` 且 `isHorizontalScrolling_` 为 true THEN 调用 `HandleFreeScroll`；否则 `HandleFixedScroll`（`pattern:10857-10861`） | 正常 |
| AC-5.3 | WHEN 调用 `singleLine(true)` THEN ModelNG `ACE_UPDATE_LAYOUT_PROPERTY(SingleLine)` 写入 LayoutProperty（`model_ng:1245-1248`），属性定义 `rich_editor_layout_property.h:33` | 正常 |
| AC-5.4 | WHEN `InitScrollablePattern` THEN 从 `GetSingleLineValue(false)` 读取，与 `barDisplayMode_` 共同决定滚动模式（`pattern:10849-10855`） | 正常 |
| AC-5.5 | WHEN 未设置 `singleLine`/`horizontalScrolling` 或传非布尔 THEN Bridge 调用 reset 恢复默认 false（`pattern.h:1483`） | 边界 |

### US-6: 撤销样式控制

**作为** 应用开发者, **我想要** 通过 `undoStyle` 控制撤销是否保留样式, **以便** 执行样式感知的撤销。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `undoStyle(KEEP_STYLE)` THEN Bridge 解析数字参数（`CLEAR_STYLE=0, KEEP_STYLE=1`，`rich_editor_model.h:379`）调用 `setRichEditorUndoStyle`（`bridge:3099-3116`） | 正常 |
| AC-6.2 | WHEN Pattern `SetSupportStyledUndo(enabled)` 执行 THEN `CHECK_NULL_VOID(!isSpanStringMode_)` → `ClearOperationRecords()` → 设置 `isStyledUndoSupported_` → 重建 `undoManager_`（`pattern:680-687`） | 正常 |
| AC-6.3 | WHEN SpanString 模式 THEN `SetSupportStyledUndo` 被跳过，`IsSupportStyledUndo()` 返回 `isSpanStringMode_ || isStyledUndoSupported_` 始终为 true（`pattern:15078-15080`） | 边界 |

### US-7: 内容长度与行数限制

**作为** 应用开发者, **我想要** 通过 `maxLength` 限制内容长度、通过 `maxLines` 限制行数, **以便** 控制内容容量和显示区域。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `maxLength(N)` (N≥0) THEN Bridge 解析数字，Infinity→`INT32_MAX`，负值→reset（`bridge:2564-2593`） | 正常 |
| AC-7.2 | WHEN `SetMaxLength` 非 `INT_MAX` THEN 调用 `DeleteToMaxLength` 截断现有内容（`pattern:14553-14560`） | 正常 |
| AC-7.3 | WHEN 添加 Span/粘贴 THEN 检查 `GetTextContentLength() >= maxLength_.value_or(INT_MAX)`，超限截断或拒绝（`pattern:1091, 1338, 1448, 1826, 5552, 6068`） | 边界 |
| AC-7.4 | WHEN 调用 `maxLines(N)` (N>0) THEN ModelNG `SetMaxLinesHeight(FLT_MAX)` + `SetMaxLines(value)` + `ACE_UPDATE_LAYOUT_PROPERTY(MaxLines)`（`model_ng:902-911`） | 正常 |
| AC-7.5 | WHEN 布局构建 ParagraphStyle THEN `style.maxLines = textStyle.GetMaxLines()`（`rich_editor_layout_algorithm.cpp:725`） | 正常 |
| AC-7.6 | WHEN 未设置 `maxLength`/`maxLines` THEN 默认 `INT_MAX`/`INT32_MAX`（`pattern.h:1463, 1444`） | 边界 |

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1, R-2 | N/A（存量） | 代码审查 | `bridge:2939-2956`, `model_ng:923-931`, `pattern:14597-14603` |
| AC-2.1~2.4 | R-3, R-4 | N/A | 代码审查 | `bridge:2971-3020`, `model_ng:969-995`, `paragraph_util:44-46` |
| AC-3.1~3.4 | R-5, R-6 | N/A | 代码审查 | `pattern:15027-15052`, `text_pattern:8999-9000` |
| AC-4.1~4.2 | R-3, R-7 | N/A | 代码审查 | `bridge:3247-3264`, `model_ng:913-921`, `paragraph_util:44` |
| AC-5.1~5.5 | R-8, R-9, R-10 | N/A | 代码审查 | `bridge:3214-3296`, `model_ng:1245-1300`, `pattern:10849-10861` |
| AC-6.1~6.3 | R-11, R-12 | N/A | 代码审查 | `bridge:3099-3116`, `rich_editor_model.h:379`, `pattern:680-687` |
| AC-7.1~7.6 | R-13, R-14, R-15 | N/A | 代码审查 | `bridge:2564-2628`, `pattern:14553-14584`, `model_ng:902-911` |

---

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `enableAutoSpacing(boolean)` (@since 20) | Bridge → ModelNG 写 LayoutProperty（`TextLayoutProperty:209`）+ Pattern Set + `paragraphCache_.Clear()` | undefined/非布尔→reset，默认 false | AC-1.1~1.4 |
| R-2 | 行为 | 布局阶段消费 `EnableAutoSpacing` | `multiple_paragraph_layout_algorithm.cpp:189` 从 `GetEnableAutoSpacingValue(false)` 设置到 TextStyle | — | AC-1.4 |
| R-3 | 行为 | 调用 `compressLeadingPunctuation`/`punctuationOverflow`/`orphanCharOptimization` (@since 23/26/26) | Bridge → ModelNG 写 LayoutProperty（TextLineStyle 组：`text_layout_property.h:174-176`）+ Pattern Set + `paragraphCache_.Clear()`；非布尔→reset | 这三个属性均存 TextLineStyle 属性组，PROPERTY_UPDATE_MEASURE | AC-2.1~2.4, AC-4.1 |
| R-4 | 行为 | ParagraphStyle 构建消费标点与孤字属性 | `paragraph_util.cpp:44-46` 将 `OrphanCharOptimization`/`CompressLeadingPunctuation`/`PunctuationOverflow` 写入段落样式；`multiple_paragraph_layout_algorithm.cpp:200` 写入 TextStyle | 孤字优化有 ParagraphStyle + TextStyle 双消费路径 | AC-2.3, AC-4.2 |
| R-5 | 行为 | 调用 `includeFontPadding`/`fallbackLineSpacing` (@since 23) | Pattern Set → `MarkDirtyNode(PROPERTY_UPDATE_MEASURE)` on ContentHost + `paragraphCache_.Clear()` | 比纯缓存清除多触发 Measure；属性定义 `text_layout_property.h:226-227` | AC-3.1~3.2 |
| R-6 | 边界 | `IncludeFontPadding`/`FallbackLineSpacing` 属性变更检测 | `text_pattern.cpp:8999-9000` 检测值变化决定是否重新布局 | — | AC-3.4 |
| R-7 | 行为 | 调用 `orphanCharOptimization` 布局消费 | `paragraph_util.cpp:44` 写 ParagraphStyle + `multiple_paragraph_layout_algorithm.cpp:200` 写 TextStyle | 双消费路径 | AC-4.2 |
| R-8 | 行为 | 调用 `horizontalScrolling(boolean)` (@since 26) | Pattern Set `isHorizontalScrolling_` + `needResetScrollBar_` + `MarkDirtyNode(MEASURE)` on Host + `paragraphCache_.Clear()`；不写 LayoutProperty | 仅存 Pattern 成员（`pattern.h:1481`） | AC-5.1 |
| R-9 | 行为 | `InitScrollablePattern` 根据 `isHorizontalScrolling_` 分支 | true → `HandleFreeScroll`；false → `HandleFixedScroll` | `pattern:10857-10861` | AC-5.2 |
| R-10 | 行为 | 调用 `singleLine(boolean)` | Bridge → ModelNG `ACE_UPDATE_LAYOUT_PROPERTY(SingleLine)` 写入 LayoutProperty；影响 `InitScrollablePattern` 滚动模式 | 属性定义 `rich_editor_layout_property.h:33`，默认 false（`pattern.h:1483`） | AC-5.3~5.5 |
| R-11 | 行为 | 调用 `undoStyle(UndoStyle)` | Bridge 解析数字（0=CLEAR_STYLE, 1=KEEP_STYLE，`rich_editor_model.h:379`）→ Pattern `SetSupportStyledUndo` | — | AC-6.1 |
| R-12 | 边界 | SpanString 模式下 `undoStyle` | `SetSupportStyledUndo` 被 `CHECK_NULL_VOID(!isSpanStringMode_)` 跳过；`IsSupportStyledUndo()` 始终返回 true | SpanString 模式强制支持样式撤销（`pattern:680-687, 15078-15080`） | AC-6.3 |
| R-13 | 边界 | `maxLength` 传入负值 | Bridge 调用 reset 恢复 `INT_MAX`；未设置时 `maxLength_` 为 `std::nullopt` | `bridge:2586-2589`，默认 `nullopt`（`pattern.h:1463`） | AC-7.1, AC-7.6 |
| R-14 | 行为 | `SetMaxLength` 非 `INT_MAX` + `SetMaxLines` | maxLength → `DeleteToMaxLength` 截断现有内容（`pattern:14553-14560`）；maxLines → `SetMaxLinesHeight(FLT_MAX)` + `SetMaxLines` + 写 LayoutProperty（`model_ng:902-911`） | maxLines 默认 `INT32_MAX`（`pattern.h:1444`） | AC-7.2, AC-7.4 |
| R-15 | 行为 | 添加 Span/粘贴时检查 `maxLength` | `GetTextContentLength() >= maxLength_.value_or(INT_MAX)` → 截断（`CalculateTruncationLength`）或拒绝；IME 配置 `config.maxLength` | 检查点：AddTextSpan/ImageSpan/SymbolSpan/PlaceholderSpan/Paste（`pattern:1091, 1338, 1448, 1826, 5552, 6068`） | AC-7.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.4 | 代码审查 | Bridge 参数解析、LayoutProperty 写入、paragraphCache 清除、TextStyle 消费 |
| VM-2 | AC-2.1~2.4 | 代码审查 | TextLineStyle 属性组存储、ParagraphStyle 构建消费 |
| VM-3 | AC-3.1~3.4 | 代码审查 | MarkDirtyNode 触发、属性变更检测、TextStyle 消费 |
| VM-4 | AC-4.1~4.2 | 代码审查 | ParagraphStyle 和 TextStyle 双消费路径 |
| VM-5 | AC-5.1~5.5 | 代码审查 | 自由滚动 vs 固定滚动分支、LayoutProperty 存储 |
| VM-6 | AC-6.1~6.3 | 代码审查 | SpanString 模式约束、撤销历史清除、undoManager 重建 |
| VM-7 | AC-7.1~7.6 | 代码审查 | 截断行为、多检查点、ParagraphStyle maxLines 消费 |

## API 变更分析

> 本特性为存量规格补录，记录各 API 的引入版本和当前签名。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `enableAutoSpacing(enable)` | Public (@since 20) | boolean \| undefined | `this` | N/A | CJK 与拉丁字符自动间距 | AC-1.1~1.4 |
| `compressLeadingPunctuation(enable)` | Public (@since 23) | boolean \| undefined | `this` | N/A | 行首标点压缩 | AC-2.1~2.4 |
| `punctuationOverflow(enable)` | Public (@since 26) | boolean \| undefined | `this` | N/A | 标点悬挂溢出 | AC-2.1~2.4 |
| `includeFontPadding(enable)` | Public (@since 23) | boolean \| undefined | `this` | N/A | 字体内边距控制 | AC-3.1~3.4 |
| `fallbackLineSpacing(enable)` | Public (@since 23) | boolean \| undefined | `this` | N/A | 回退行距控制 | AC-3.1~3.4 |
| `orphanCharOptimization(enable)` | Public (@since 26) | boolean \| undefined | `this` | N/A | 孤字优化 | AC-4.1~4.2 |
| `horizontalScrolling(enabled)` | Public (@since 26) | boolean \| undefined | `this` | N/A | 水平滚动 | AC-5.1~5.2 |
| `singleLine(value)` | Public | boolean \| undefined | `this` | N/A | 单行模式 | AC-5.3~5.5 |
| `undoStyle(style)` | Public | UndoStyle \| undefined | `this` | N/A | 撤销样式 | AC-6.1~6.3 |
| `maxLength(value)` | Public (@since 10) | int32 \| undefined | `this` | N/A | 最大内容长度 | AC-7.1~7.6 |
| `maxLines(value)` | Public (@since 10) | int32 \| undefined | `this` | N/A | 最大行数 | AC-7.1~7.6 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

| 接口 | 开放范围 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|----------|---------|
| `enableAutoSpacing` | Public (@since 20) | `enable`: boolean，默认 undefined | 布尔→写 LayoutProperty + Pattern + `paragraphCache_.Clear()`；undefined→reset | AC-1.1~1.4 |
| `compressLeadingPunctuation` | Public (@since 23) | `enable`: boolean | 布尔→写 TextLineStyle 组 + Pattern + `paragraphCache_.Clear()`；非布尔→reset | AC-2.1~2.4 |
| `punctuationOverflow` | Public (@since 26) | `enable`: boolean | 同 `compressLeadingPunctuation` 模式 | AC-2.1~2.4 |
| `includeFontPadding` | Public (@since 23) | `enable`: boolean | 布尔→写 LayoutProperty + Pattern + `MarkDirtyNode(MEASURE)` + `paragraphCache_.Clear()` | AC-3.1~3.4 |
| `fallbackLineSpacing` | Public (@since 23) | `enable`: boolean | 同 `includeFontPadding` 模式 | AC-3.1~3.4 |
| `orphanCharOptimization` | Public (@since 26) | `enable`: boolean | 布尔→写 TextLineStyle + Pattern + `paragraphCache_.Clear()`；双消费（ParagraphStyle+TextStyle） | AC-4.1~4.2 |
| `horizontalScrolling` | Public (@since 26) | `enabled`: boolean | 布尔→Pattern `isHorizontalScrolling_` + `needResetScrollBar_` + `MarkDirtyNode(MEASURE)` + `paragraphCache_.Clear()`；不写 LayoutProperty | AC-5.1~5.2 |
| `singleLine` | Public | `value`: boolean | 布尔→写 LayoutProperty SingleLine；影响 `InitScrollablePattern` | AC-5.3~5.5 |
| `undoStyle` | Public | `style`: UndoStyle（0=CLEAR, 1=KEEP） | 数字→Pattern `SetSupportStyledUndo`：清除历史+重建 undoManager；SpanString 模式跳过 | AC-6.1~6.3 |
| `maxLength` | Public (@since 10) | `value`: int32≥0 | N≥0→`DeleteToMaxLength` 截断+存储；负值→reset；Infinity→INT32_MAX | AC-7.1~7.6 |
| `maxLines` | Public (@since 10) | `value`: int32>0 | N>0→`SetMaxLines`+`SetMaxLinesHeight(FLT_MAX)`+LayoutProperty；≤0→JsView 设 Infinity，非 JsView reset | AC-7.1~7.6 |

---

## 兼容性声明

- **已有 API 行为变更:** 是 — API 20/23/26 逐步引入新排版属性
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（`maxLength`/`maxLines`），API 20（`enableAutoSpacing`），API 23（`compressLeadingPunctuation`/`includeFontPadding`/`fallbackLineSpacing`），API 26（`punctuationOverflow`/`orphanCharOptimization`/`horizontalScrolling`）
- **API 版本号策略:** 各属性按 `@since` 标注独立引入版本；低版本调用高版本属性时不生效

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 属性存储三层分布 | `EnableAutoSpacing`/`IncludeFontPadding`/`FallbackLineSpacing` 在 `TextLayoutProperty` 基类；`OrphanCharOptimization`/`CompressLeadingPunctuation`/`PunctuationOverflow`/`MaxLines` 在 `TextLineStyle` 属性组；`SingleLine` 在 `RichEditorLayoutProperty` | AC-1.2, AC-2.1, AC-3.1, AC-4.1, AC-5.3 |
| 部分属性仅存 Pattern | `horizontalScrolling`/`undoStyle`/`maxLength` 不写入 LayoutProperty | AC-5.1, AC-6.2, AC-7.2 |
| 排版属性变更均触发 `paragraphCache_.Clear()` | 确保下次布局重新构建 Paragraph | AC-1.3, AC-2.1, AC-3.1, AC-4.1, AC-5.1 |
| `includeFontPadding`/`fallbackLineSpacing`/`horizontalScrolling` 额外触发 Measure | 除清缓存外还调用 `MarkDirtyNode(PROPERTY_UPDATE_MEASURE)` | AC-3.1, AC-5.1 |
| `undoStyle` 受模式约束 | `SetSupportStyledUndo` 仅非 SpanString 模式生效，SpanString 模式强制支持 | AC-6.3 |
| `maxLength` 变更触发内容截断 | `SetMaxLength` 非 `INT_MAX` 时立即调用 `DeleteToMaxLength` | AC-7.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 排版属性变更触发 `paragraphCache_.Clear()` | 代码审查 | `pattern:14601, 14614, 14627, 14640, 15034, 15050, 10971` |
| 可靠性 | `maxLength` 变更通过 `DeleteToMaxLength` 保证内容不超限 | 代码审查 | `pattern:14555-14556` |
| 可测试性 | 所有属性通过 Inspector JSON 可观测 | 代码审查 | `pattern:11581-11595` |

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
| 无障碍 | 是 | 排版属性影响文本可读性 | AC-1.4, AC-4.2 |
| 大字体 | 是 | `includeFontPadding`/`fallbackLineSpacing` 影响行高，大字体下效果显著 | AC-3.1~3.3 |
| 深色模式 | 否 | 不涉及颜色主题 | — |
| 多窗口/分屏 | 否 | 不涉及窗口模式 | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | API 20/23/26 逐步引入新属性 | AC-1.1, AC-2.1, AC-4.1, AC-5.1 |
| 生态兼容 | 是 | `enableAutoSpacing` 涉及 CJK 与拉丁文间距 | AC-1.1~1.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RichEditor 文本排版与显示优化
  作为应用开发者
  我想要控制 RichEditor 的排版细节和显示行为
  以便在不同场景下获得最佳的文本呈现效果

  Scenario: 排版属性变更触发段落缓存清除
    Given RichEditor 已渲染文本内容
    When 调用任一排版属性（enableAutoSpacing/compressLeadingPunctuation 等）并值变化
    Then paragraphCache_ 被清除
    And includeFontPadding/fallbackLineSpacing/horizontalScrolling 额外触发 MarkDirtyNode(MEASURE)
    And 下次布局重新构建 Paragraph

  Scenario: 撤销样式在 SpanString 模式下的约束
    Given RichEditor 处于 SpanString 模式
    When 调用 undoStyle(KEEP_STYLE)
    Then SetSupportStyledUndo 被 CHECK_NULL_VOID(!isSpanStringMode_) 跳过
    And IsSupportStyledUndo() 始终返回 true

  Scenario: maxLength 截断已有内容
    Given RichEditor 已有 100 字符内容
    When 调用 maxLength(50)
    Then DeleteToMaxLength(50) 被调用
    And 超出 50 字符的内容被截断
    And 后续 AddTextSpan 检查 GetTextContentLength() >= 50 时拒绝插入
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（11 个排版属性行为规格，不含 span 内容操作、选择交互、输入法连接细节）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "RichEditor text layout properties: enableAutoSpacing, compressLeadingPunctuation, punctuationOverflow, includeFontPadding, fallbackLineSpacing, orphanCharOptimization storage in TextLayoutProperty and RichEditorLayoutProperty"
  - repo: "openharmony/ace_engine"
    query: "RichEditor horizontalScrolling, singleLine, undoStyle, maxLength, maxLines Pattern member variables and Set implementations"
  - repo: "openharmony/ace_engine"
    query: "RichEditor paragraphCache Clear and MarkDirtyNode PROPERTY_UPDATE_MEASURE side effects for layout property changes"
```

**关键文档：**
- SDK 生成声明: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/richEditor.ets`（RichEditorAttribute 接口，行 1273-1418）
- 布局属性定义: `frameworks/core/components_ng/pattern/text/text_layout_property.h`（TextLayoutProperty 基类）
- 布局属性定义: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_layout_property.h`（RichEditorLayoutProperty）
- 段落样式构建: `frameworks/core/components_ng/pattern/text/paragraph_util.cpp`
- UndoStyle 枚举: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_model.h:379`
