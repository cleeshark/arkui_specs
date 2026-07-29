# 特性规格

> Func-04-03-11-Feat-05 自适应字体缩放：固化 minFontSize/maxFontSize/minFontScale/maxFontScale + HeightAdaptivePolicy + enableVariableFontWeight/enableDeviceFontWeightCategory（交叉引用 Feat-01）的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自适应字体缩放 (Adaptive Font Scaling) |
| 特性编号 | Func-04-03-11-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 minFontSize/maxFontSize；API 10 HeightAdaptivePolicy；API 12 minFontScale/maxFontScale + enableVariableFontWeight；API 18 适用于子组件/styled strings；API 23 static |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | minFontSize/maxFontSize 自适应字号行为规格 | @since 7；AdaptMinFontSize/AdaptMaxFontSize 存储 |
| ADDED | minFontScale/maxFontScale 缩放范围行为规格 | @since 12 dynamic / @since 23 static（公开 API，非内部） |
| ADDED | HeightAdaptivePolicy 3 策略行为规格 | @since 10；MAX_LINES_FIRST/MIN_FONT_SIZE_FIRST/LAYOUT_CONSTRAINT_FIRST |
| ADDED | 自适应算法（TextAdaptFontSizer）行为规格 | 二分搜索 + 线性递减；与 maxLines/overflow 交互 |
| ADDED | enableVariableFontWeight/enableDeviceFontWeightCategory 交叉引用 Feat-01 | 非重复详述，仅标注自适应场景下的交互 |
| ADDED | C-API NODE_TEXT_MIN/MAX_FONT_SIZE 行为规格 | @since 12 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/11-text-common-attributes/design.md` | Baselined |
| Feat-01 交叉引用 | `specs/04-common-capability/03-common-attributes/11-text-common-attributes/Feat-01-core-font-attributes-spec.md` | Baselined |

---

## 用户故事

### US-1: 设置自适应字号范围

**作为** 应用开发者,
**我想要** 通过 `.minFontSize(value)`/`.maxFontSize(value)` 设置自适应字号范围,
**以便** 文本根据容器大小在范围内自动调整字号。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.minFontSize(12).maxFontSize(24)` (API 7+) THEN AdaptMinFontSize=12fp, AdaptMaxFontSize=24fp；算法在 [12,24] 范围内 fitting | 正常 |
| AC-1.2 | WHEN 仅设置 minFontSize 未设置 maxFontSize THEN 自适应不生效（须配对使用） | 异常 |
| AC-1.3 | WHEN maxFontSize < minFontSize 或 minFontSize ≤ 0 THEN 自适应跳过，使用 fontSize 直接布局（text_adapt_font_sizer.cpp:25,71） | 异常 |
| AC-1.4 | WHEN min/max 均设置且自适应生效 THEN **显式 fontSize 被覆写**（textStyle.SetFontSize 在 [min,max] 范围内，text_adapt_font_sizer.cpp:35,48,61,79） | 边界 |
| AC-1.5 | WHEN min/max 未设置 THEN 直接使用 fontSize 布局（IsNeedAdaptFontSize 返回 false, text_adapt_font_sizer.cpp:139-145） | 正常 |
| AC-1.6 | WHEN 在 Text 设置 min/max font size THEN 写入 FontStyle::AdaptMinFontSize/AdaptMaxFontSize (Dimension, PROPERTY_UPDATE_MEASURE) | 正常 |
| AC-1.7 | WHEN 在 Button 设置 min/max font size THEN 写入 ButtonLayoutProperty::MinFontSize/MaxFontSize（PROPERTY_UPDATE_NORMAL），同步至内部 Text 子节点 AdaptMin/MaxFontSize（button_pattern.cpp:461-466） | 正常 |
| AC-1.8 | WHEN min/max font size 为负值 THEN JS bridge 回退 theme 默认值（js_text.cpp:752-753） | 异常 |
| AC-1.9 | WHEN API 18+ THEN min/max font size 也适用于子组件/styled strings（text.d.ts:178） | 边界 |

### US-2: 设置字号缩放范围

**作为** 应用开发者,
**我想要** 通过 `.minFontScale(scale)`/`.maxFontScale(scale)` 限制系统字体缩放范围,
**以便** 防止大字体场景下文本过大。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.minFontScale(0.8).maxFontScale(1.5)` (API 12+) THEN MinFontScale=0.8, MaxFontScale=1.5；系统字体缩放被 clamp 到 [0.8, 1.5] | 正常 |
| AC-2.2 | WHEN minFontScale < 0 THEN clamp 到 0（js_text.cpp:290） | 边界 |
| AC-2.3 | WHEN minFontScale > 1 THEN clamp 到 1 | 边界 |
| AC-2.4 | WHEN maxFontScale < 1 THEN clamp 到 1（js_text.cpp:305） | 边界 |
| AC-2.5 | WHEN maxFontScale 未设置 THEN 上限回退 pipeline->GetMaxAppFontScale()（系统默认，dimension.cpp:375） | 正常 |
| AC-2.6 | WHEN minFontScale/maxFontScale 生效 THEN fp→px 转换公式：fp × dipScale × clamp(envOrSystemFontScale, minFontScale, maxFontScale)（dimension.cpp:362-369） | 正常 |
| AC-2.7 | WHEN minFontScale/maxFontScale 是 **clamp 非乘法因子** THEN 不直接乘 fontSize，而是约束系统/环境字体缩放比例 | 边界 |
| AC-2.8 | WHEN 在 Button/SymbolGlyph/SecurityComponent 设置 min/max font scale THEN 支持（逐组件适用 7 组件） | 正常 |

### US-3: 设置高度自适应策略

**作为** 应用开发者,
**我想要** 通过 `.heightAdaptivePolicy(value)` 控制自适应策略,
**以便** 指定优先级（maxLines 优先 / minFontSize 优先 / 布局约束优先）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.heightAdaptivePolicy(TextHeightAdaptivePolicy.MAX_LINES_FIRST)` (API 10+) THEN 默认策略：先遵守 maxLines，超出则缩字号（text_layout_algorithm.cpp:268） | 正常 |
| AC-3.2 | WHEN 调用 `.heightAdaptivePolicy(MIN_FONT_SIZE_FIRST)` THEN 先 minFontSize：若一行能放下则从 min 二分增长到 max；否则保持 min（text_layout_algorithm.cpp:271, AdaptMaxFontSize 二分搜索） | 正常 |
| AC-3.3 | WHEN 调用 `.heightAdaptivePolicy(LAYOUT_CONSTRAINT_FIRST)` THEN 先布局约束：缩到 min 仍溢出则递减 maxLines 删除溢出行（text_layout_algorithm.cpp:275） | 正常 |
| AC-3.4 | WHEN 未设置 heightAdaptivePolicy THEN 默认 MAX_LINES_FIRST（text_layout_algorithm.cpp:266） | 正常 |
| AC-3.5 | WHEN LAYOUT_CONSTRAINT_FIRST 且 maxLines == UINT32_MAX THEN 通过 GetAdaptedMaxLines 用 AdaptMinFontSize 估算 maxLines（text_layout_algorithm.cpp:1166） | 边界 |
| AC-3.6 | WHEN LAYOUT_CONSTRAINT_FIRST THEN 循环递减 maxLines 并重试 BuildParagraph 直到高度 ≤ maxSize.Height()（text_layout_algorithm.cpp:1179-1203） | 正常 |

### US-4: 自适应算法行为

**作为** 应用开发者,
**我想要** 了解自适应字号算法的工作机制,
**以便** 正确配置 min/max font size + maxLines + policy。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN MAX_LINES_FIRST + 适应生效 THEN AdaptMinTextSize 线性递减：从 maxFontSize 开始，每次减 stepSize，直到不超 maxLines 或到 minFontSize（text_adapt_font_sizer.cpp:65-89） | 正常 |
| AC-4.2 | WHEN MIN_FONT_SIZE_FIRST THEN AdaptMaxFontSize 二分搜索：先试 minFontSize，若一行能放则二分 [min,max] 找最大可放下字号（text_adapt_font_sizer.cpp:19-63） | 正常 |
| AC-4.3 | WHEN 算法 fitting 时 DidExceedMaxLines 检查 THEN 判断 paragraph->DidExceedMaxLines() 或 height > maxSize.Height() 或 longestLine > maxSize.Width()（text_adapt_font_sizer.cpp:121-129） | 正常 |
| AC-4.4 | WHEN stepSize 未设置 THEN 默认 1.0_vp（text_adapt_font_sizer.cpp:102-112） | 正常 |
| AC-4.5 | WHEN 算法选择 LD vs BS THEN 若 step 非 px 且 exp2(stepCount/2 - 1) < stepCount 用 LD，否则 BS（text_layout_algorithm.cpp:947） | 边界 |
| AC-4.6 | WHEN min/max font size 转换为 px THEN 使用 ConvertToPxDistributeWithEnv(MinFontScale, MaxFontScale, AllowScale, EnvFontScale)（text_adapt_font_sizer.cpp:94-100） | 正常 |
| AC-4.7 | WHEN 算法覆写 fontSize THEN 显式 fontSize 在 fitting 期间被 textStyle.SetFontSize(Dimension(min/max/mid)) 覆写 | 边界 |

### US-5: enableVariableFontWeight/enableDeviceFontWeightCategory 交叉引用

**作为** 应用开发者,
**我想要** 了解自适应字号与变体字重的交互,
**以便** 正确组合使用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN EnableVariableFontWeight=true THEN 渲染时 fontWeightValue=VariableFontWeight 覆盖静态 FontWeight 派生值（详见 Feat-01 ADR-2, constants_converter.cpp:606-611） | 正常 |
| AC-5.2 | WHEN EnableVariableFontWeight=true 且未设 EnableDeviceFontWeightCategory（Text 默认）THEN 不应用 GetFontWeightScale() 设备字重缩放（constants_converter.cpp:621-623） | 边界 |
| AC-5.3 | WHEN EnableDeviceFontWeightCategory 显式 set true（Span/styledString）THEN 即使 EnableVariableFontWeight=true 也应用 GetFontWeightScale() 缩放（constants_converter.cpp:616-618） | 边界 |
| AC-5.4 | WHEN EnableDeviceFontWeightCategory 显式 set false THEN 不缩放（constants_converter.cpp:613-624 三态语义，详见 Feat-01 ADR-6） | 边界 |
| AC-5.5 | WHEN enableVariableFontWeight/enableDeviceFontWeightCategory 是 **FontSettingOptions/FontWeightConfigs 字段**（非独立公开方法）THEN 详见 Feat-01 规格，本 Feat 仅交叉引用 | 边界 |

### US-6: 通过 C-API 设置自适应字号

**作为** NDK 开发者,
**我想要** 通过 `setAttribute(NODE_TEXT_MIN/MAX_FONT_SIZE, item)` 设置自适应字号,
**以便** 在 C 代码中控制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `setAttribute(node, NODE_TEXT_MIN_FONT_SIZE, {value[0].f32: 12.0})` THEN 设置 minFontSize=12fp；支持 TEXT/TEXT_INPUT/TEXT_AREA | 正常 |
| AC-6.2 | WHEN 调用 `setAttribute(node, NODE_TEXT_MAX_FONT_SIZE, {value[0].f32: 24.0})` THEN 设置 maxFontSize=24fp；支持 TEXT/TEXT_INPUT/TEXT_AREA | 正常 |
| AC-6.3 | WHEN item.size == 0 THEN 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401)（style_modifier.cpp:9930-9931） | 异常 |
| AC-6.4 | WHEN 在不支持节点调用 THEN 静默 no-op 返回 NO_ERROR（converter 无 else 分支） | 边界 |
| AC-6.5 | WHEN 尝试设置 minFontScale/maxFontScale via C-API THEN **不存在 NODE_TEXT_MIN/MAX_FONT_SCALE 枚举**（C-API 缺口，仅 Button 有 NODE_BUTTON_MIN/MAX_FONT_SCALE @since 18） | 边界 |
| AC-6.6 | WHEN GetTextMinFontSize/GetTextMaxFontSize 在不支持节点调用 THEN 返回 stale 值（无 null guard，g_numberValues 残留） | 边界 |
| AC-6.7 | WHEN 通过 styled-string C-API 尝试自适应字号 THEN **无对应 OH_ARKUI_STYLEDSTRINGKEY**（FONT key 仅固定字号，无自适应） | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.9 | R-1~R-7 | 已有实现 | 单测 | `test/unittest/core/components_ng/text/` |
| AC-2.1~2.8 | R-8~R-13 | 已有实现 | 单测 | 同上 + `dimension_test` |
| AC-3.1~3.6 | R-14~R-17 | 已有实现 | 单测 | `text_layout_algorithm_test` |
| AC-4.1~4.7 | R-18~R-22 | 已有实现 | 单测 | `text_adapt_font_sizer_test` |
| AC-5.1~5.5 | R-23~R-26 | 已有实现 | 单测 | 详见 Feat-01 |
| AC-6.1~6.7 | R-27~R-31 | 已有实现 | 单测 | `test/unittest/interfaces/native_node_test.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 SetMinFontSize/SetMaxFontSize (API 7+) | AdaptMinFontSize/AdaptMaxFontSize 存为 Dimension（FP）；写入 FontStyle 组；触发 propNeedReCreateParagraph_=true | 须配对使用 | AC-1.1, AC-1.6 |
| R-2 | 异常 | 仅设 min 未设 max（或反之） | 自适应不生效 | text_style.h:944/957 "Must use with" | AC-1.2 |
| R-3 | 异常 | max < min 或 min ≤ 0 | 自适应跳过，使用 fontSize 直接布局 | text_adapt_font_sizer.cpp:25,71 | AC-1.3 |
| R-4 | 边界 | 自适应生效时 | 显式 fontSize 被覆写（textStyle.SetFontSize 在 [min,max] 范围） | 算法覆写 | AC-1.4, AC-4.7 |
| R-5 | 行为 | min/max 未设置 | 直接使用 fontSize 布局（IsNeedAdaptFontSize=false） | text_adapt_font_sizer.cpp:139-145 | AC-1.5 |
| R-6 | 行为 | Button min/max font size | 写入 ButtonLayoutProperty（NORMAL flag），同步至内部 Text 子节点 AdaptMin/MaxFontSize | button_pattern.cpp:461-466 | AC-1.7 |
| R-7 | 异常 | min/max 负值 | JS bridge 回退 theme 默认 | js_text.cpp:752-753 | AC-1.8 |
| R-8 | 行为 | 调用 SetMinFontScale/SetMaxFontScale (API 12+) | MinFontScale/MaxFontScale 存为 float；公开 API（非内部）；7 组件暴露 | range [0,1] / [1,+∞) | AC-2.1, AC-2.8 |
| R-9 | 边界 | minFontScale < 0 或 > 1 | clamp 到 [0,1] | js_text.cpp:290 | AC-2.2, AC-2.3 |
| R-10 | 边界 | maxFontScale < 1 | clamp 到 1 | js_text.cpp:305 | AC-2.4 |
| R-11 | 行为 | maxFontScale 未设置 | 上限回退 pipeline->GetMaxAppFontScale()（系统） | dimension.cpp:375 | AC-2.5 |
| R-12 | 行为 | fp→px 转换 | fp × dipScale × clamp(envOrSystemFontScale, minFontScale, maxFontScale) | dimension.cpp:362-369 | AC-2.6 |
| R-13 | 边界 | fontScale 是 clamp 非乘法 | 不直接乘 fontSize，约束系统/环境字体缩放比例 | ConvertToPxDistributeWithEnv | AC-2.7 |
| R-14 | 行为 | heightAdaptivePolicy=MAX_LINES_FIRST (API 10+, 默认) | 先遵守 maxLines，超出则缩字号（AdaptMinTextSize 线性递减） | text_layout_algorithm.cpp:268 | AC-3.1, AC-4.1 |
| R-15 | 行为 | heightAdaptivePolicy=MIN_FONT_SIZE_FIRST | 先 minFontSize：一行能放则二分增长到 max；否则保持 min（AdaptMaxFontSize 二分搜索） | text_layout_algorithm.cpp:271 | AC-3.2, AC-4.2 |
| R-16 | 行为 | heightAdaptivePolicy=LAYOUT_CONSTRAINT_FIRST | 先布局约束：缩到 min 仍溢出则递减 maxLines 删除溢出行 | text_layout_algorithm.cpp:275 | AC-3.3, AC-3.6 |
| R-17 | 行为 | 未设 heightAdaptivePolicy | 默认 MAX_LINES_FIRST | text_layout_algorithm.cpp:266 | AC-3.4 |
| R-18 | 行为 | MAX_LINES_FIRST 算法 | AdaptMinTextSize 线性递减：从 maxFontSize 每次减 stepSize，直到不超 maxLines 或到 min | text_adapt_font_sizer.cpp:65-89 | AC-4.1 |
| R-19 | 行为 | MIN_FONT_SIZE_FIRST 算法 | AdaptMaxFontSize 二分搜索：先试 min，若一行能放则二分 [min,max] 找最大 | text_adapt_font_sizer.cpp:19-63 | AC-4.2 |
| R-20 | 行为 | DidExceedMaxLines 检查 | paragraph->DidExceedMaxLines() 或 height > maxSize.Height() 或 longestLine > maxSize.Width() | text_adapt_font_sizer.cpp:121-129 | AC-4.3 |
| R-21 | 行为 | stepSize 默认 | 1.0_vp | text_adapt_font_sizer.cpp:102-112 | AC-4.4 |
| R-22 | 边界 | LD vs BS 选择 | step 非 px 且 exp2(stepCount/2-1) < stepCount 用 LD，否则 BS | text_layout_algorithm.cpp:947 | AC-4.5 |
| R-23 | 行为 | EnableVariableFontWeight=true | fontWeightValue=VariableFontWeight 覆盖静态派生值（详见 Feat-01 ADR-2） | constants_converter.cpp:606-611 | AC-5.1 |
| R-24 | 边界 | EnableVariableFontWeight=true 且未设 device category（Text 默认） | 不应用 GetFontWeightScale() | constants_converter.cpp:621-623 | AC-5.2 |
| R-25 | 边界 | EnableDeviceFontWeightCategory 显式 true（Span/styledString） | 即使 variable 启用也缩放 | constants_converter.cpp:616-618 | AC-5.3 |
| R-26 | 边界 | enableVariableFontWeight/enableDeviceFontWeightCategory 非独立方法 | FontSettingOptions/FontWeightConfigs 字段（详见 Feat-01） | 交叉引用 Feat-01 | AC-5.5 |
| R-27 | 行为 | C-API NODE_TEXT_MIN_FONT_SIZE set | value[0].f32 (fp)；支持 TEXT/TEXT_INPUT/TEXT_AREA | style_modifier.cpp:9928 | AC-6.1 |
| R-28 | 行为 | C-API NODE_TEXT_MAX_FONT_SIZE set | value[0].f32 (fp)；支持 TEXT/TEXT_INPUT/TEXT_AREA | style_modifier.cpp:9974 | AC-6.2 |
| R-29 | 异常 | C-API item.size == 0 | 返回 PARAM_INVALID (401) | style_modifier.cpp:9930 | AC-6.3 |
| R-30 | 边界 | C-API 无 NODE_TEXT_MIN/MAX_FONT_SCALE | fontScale 是 ArkTS 独有，无 C-API 对应（仅 Button 有 @since 18） | C-API 缺口 | AC-6.5 |
| R-31 | 边界 | C-API GetTextMinFontSize/GetTextMaxFontSize 不支持节点 | 返回 stale 值（无 null guard） | style_modifier.cpp:9947-9960 | AC-6.6 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-7, AC-1.1~1.9 | 单测 | min/max font size 配对 + 覆写 fontSize |
| VM-2 | R-8~R-13, AC-2.1~2.8 | 单测 | min/max font scale clamp + ConvertToPxDistributeWithEnv |
| VM-3 | R-14~R-17, AC-3.1~3.6 | 单测 | HeightAdaptivePolicy 3 策略 |
| VM-4 | R-18~R-22, AC-4.1~4.7 | 单测 | 自适应算法 LD/BS + DidExceedMaxLines |
| VM-5 | R-23~R-26, AC-5.1~5.5 | 单测 | enableVariableFontWeight 交叉引用 Feat-01 |
| VM-6 | R-27~R-31, AC-6.1~6.7 | 单测/native_node_test | C-API min/max font size + 缺口 |
| VM-7 | 全量 | XTS/集成 | 端到端自适应字号渲染 |

---

## API 变更分析

### 新增 API

**ArkTS 动态 API (TextAttribute)：**

| API 签名 | 开放范围 | @since | 关联 AC |
|----------|---------|--------|---------|
| `minFontSize(value: number \| string \| Resource): TextAttribute` | Public | 7 | AC-1.* |
| `maxFontSize(value: number \| string \| Resource): TextAttribute` | Public | 7 | AC-1.* |
| `minFontScale(scale: number \| Resource): TextAttribute` | Public | 12 | AC-2.* |
| `maxFontScale(scale: number \| Resource): TextAttribute` | Public | 12 | AC-2.* |
| `heightAdaptivePolicy(value: TextHeightAdaptivePolicy): TextAttribute` | Public | 10 | AC-3.* |

**逐组件适用性矩阵（动态 API）：**

| 组件 | minFontSize | maxFontSize | minFontScale | maxFontScale | heightAdaptivePolicy |
|------|-------------|-------------|---------------|---------------|----------------------|
| TextAttribute | ✓ (@since 7) | ✓ (@since 7) | ✓ (@since 12) | ✓ (@since 12) | ✓ (@since 10) |
| TextInputAttribute | ✓ | ✓ | ✓ | ✓ | ✓ |
| TextAreaAttribute | ✓ | ✓ | ✓ | ✓ | ✓ |
| SearchAttribute | ✓ | ✓ | ✓ | ✓ | ✗ |
| ButtonAttribute | ✗ | ✗ | ✓ (@since ?) | ✓ | ✓ (字段) |
| SecurityComponentAttribute | ✓ | ✓ | ✓ | ✓ | ✓ |
| SymbolGlyphAttribute | ✗ | ✗ | ✓ | ✓ | ✗ |

**TextHeightAdaptivePolicy 枚举（enums.d.ts:6230, @since 11）：**

| 成员 | 值 | 说明 |
|------|-----|------|
| MAX_LINES_FIRST | 0 | 先 maxLines 后缩字号（默认） |
| MIN_FONT_SIZE_FIRST | 1 | 先 minFontSize 二分增长 |
| LAYOUT_CONSTRAINT_FIRST | 2 | 先布局约束，递减 maxLines |

**C-API (NDK)：**

| 属性枚举 | 值 | 格式 | @since | 支持节点 | 关联 AC |
|----------|-----|------|--------|----------|---------|
| NODE_TEXT_MIN_FONT_SIZE | 1016 | value[0].f32 (fp) | 12 | TEXT/TEXT_INPUT/TEXT_AREA | AC-6.1 |
| NODE_TEXT_MAX_FONT_SIZE | 1017 | value[0].f32 (fp) | 12 | TEXT/TEXT_INPUT/TEXT_AREA | AC-6.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无变更/废弃 API | — |

---

## 接口规格

### 接口定义

**minFontSize / maxFontSize**

| 属性 | 值 |
|------|-----|
| 函数签名 | `minFontSize(value: number \| string \| Resource): TextAttribute` / `maxFontSize(...)` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number \| string \| Resource | 是 | theme 默认 (0) | fp 单位；须配对使用；max < min 或 ≤ 0 跳过自适应；负值回退 theme；自适应生效时覆写 fontSize |

---

**minFontScale / maxFontScale**

| 属性 | 值 |
|------|-----|
| 函数签名 | `minFontScale(scale: number \| Resource): TextAttribute` / `maxFontScale(...)` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| scale | number \| Resource | 是 | min: 0 / max: 系统默认 | min range [0,1]（<0→0, >1→1）；max range [1,+∞)（<1→1）；是 clamp 非乘法 |

---

**heightAdaptivePolicy**

| 属性 | 值 |
|------|-----|
| 函数签名 | `heightAdaptivePolicy(value: TextHeightAdaptivePolicy): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | TextHeightAdaptivePolicy | 是 | MAX_LINES_FIRST | 3 枚举值；控制 maxLines vs min/max font size vs 布局约束优先级 |

---

## 兼容性声明

- **已有 API 行为变更:**
  - **API 7**: minFontSize/maxFontSize
  - **API 10**: heightAdaptivePolicy
  - **API 12**: minFontScale/maxFontScale（公开 API，非内部）；enableVariableFontWeight via FontSettingOptions
  - **API 18**: min/max font size 适用于子组件/styled strings
  - **API 23 static**: 静态范式全部（@since 23 static）
  - **API 24**: enableDeviceFontWeightCategory via FontWeightConfigs
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（min/maxFontSize）；API 10（heightAdaptivePolicy）；API 12（min/maxFontScale + C-API NODE_TEXT_MIN/MAX_FONT_SIZE）
- **API 版本号策略:** @since 7/10/12/18/23/24 标注

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| minFontScale/maxFontScale 是公开 API | 非内部；@since 12 dynamic / @since 23 static；7 组件暴露 | AC-2.1, AC-2.8 |
| 算法覆写 fontSize | 自适应生效时显式 fontSize 在 [min,max] 内被覆写 | AC-1.4, AC-4.7 |
| min/max 必须配对 | max < min 或 min ≤ 0 跳过自适应 | AC-1.3 |
| HeightAdaptivePolicy 3 策略 | MAX_LINES_FIRST（线性递减）/ MIN_FONT_SIZE_FIRST（二分增长）/ LAYOUT_CONSTRAINT_FIRST（递减 maxLines） | AC-3.1~3.3 |
| fontScale 是 clamp 非乘法 | fp × dipScale × clamp(envOrSystemFontScale, min, max) | AC-2.6, AC-2.7 |
| C-API min/maxFontSize 有 / fontScale 缺 | NODE_TEXT_MIN/MAX_FONT_SIZE 存在；NODE_TEXT_MIN/MAX_FONT_SCALE 不存在（C-API 缺口） | AC-6.1, AC-6.5 |
| styled-string 无自适应 + Get stale 风险 | OH_ARKUI_STYLEDSTRINGKEY 无自适应键；GetTextMinFontSize 不支持节点返回 stale | AC-6.6, AC-6.7 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 自适应 fitting 算法 < 5ms（典型场景）；二分搜索 O(log(stepCount)) | benchmark | — |
| 内存 | AdaptMin/MaxFontSize 用 Dimension；Min/MaxFontScale 用 float | hidumper | — |
| 可靠性 | min/max 不配对时跳过自适应（不崩溃）；负值回退 theme | 集成测试 | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |
| 穿戴 | 默认值差异可能存在 | text_theme 默认 | 文档标注 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 自适应字号影响可读性 | — |
| 大字体 | 是 | min/maxFontScale 直接约束系统字体缩放范围 | AC-2.1 |
| 深色模式 | 否 | 与颜色无关 | — |
| 多窗口/分屏 | 是 | 窗口尺寸变化触发自适应 fitting 重算 | AC-3.3, AC-3.6 |
| 多用户 | 否 | 无用户态差异 | — |
| 版本升级 | 是 | API 7/10/12/18/23/24 版本差异须通过 API 版本守护 | AC-1.9, AC-2.1, AC-3.1 |
| 生态兼容 | 是 | C-API（NODE_TEXT_MIN/MAX_FONT_SIZE）应与 ArkTS 一致；fontScale 无 C-API 是已知缺口 | AC-6.* |

---

## 行为场景

```gherkin
Feature: 自适应字体缩放
  作为 应用开发者
  我想要 通过 min/max font size + min/max font scale + heightAdaptivePolicy 控制文本自适应
  以便 文本在不同容器/字体缩放下合理调整

  # ─── min/maxFontSize ─────────────────────────────

  Scenario: 设置自适应字号范围
    Given 一个 Text 组件 maxLines=3
    When 调用 .minFontSize(12).maxFontSize(24)
    Then 算法在 [12, 24] 范围内 fitting，找到不超 maxLines 的最大字号

  Scenario: min/max 不配对不生效
    Given 一个 Text 组件
    When 仅调用 .minFontSize(12)
    Then 自适应不生效，使用 fontSize 直接布局

  Scenario: max < min 跳过自适应
    Given 一个 Text 组件
    When 调用 .minFontSize(24).maxFontSize(12)
    Then 自适应跳过，使用 fontSize 直接布局

  Scenario: 自适应覆写 fontSize
    Given 一个 Text 组件已 .fontSize(20)
    When 调用 .minFontSize(12).maxFontSize(24)
    Then fitting 期间 fontSize 被覆写为 [12,24] 内的值

  Scenario: Button min/max 同步子 Text
    Given 一个 Button 组件
    When 调用 .minFontSize(10).maxFontSize(20)
    Then 写入 ButtonLayoutProperty
    And 同步至内部 Text 子节点 AdaptMin/MaxFontSize

  # ─── min/maxFontScale ────────────────────────────

  Scenario: 限制字体缩放范围
    Given 一个 Text 组件
    When 调用 .minFontScale(0.8).maxFontScale(1.5)
    Then 系统字体缩放被 clamp 到 [0.8, 1.5]
    And fp→px 转换：fp × dipScale × clamp(envFontScale, 0.8, 1.5)

  Scenario: minFontScale 越界 clamp
    Given 一个 Text 组件
    When 调用 .minFontScale(-0.5)
    Then clamp 到 0
    When 调用 .minFontScale(2.0)
    Then clamp 到 1

  Scenario: maxFontScale 未设置回退系统
    Given 一个 Text 组件未设 maxFontScale
    Then 上限回退 pipeline->GetMaxAppFontScale()

  Scenario: fontScale 是 clamp 非乘法
    Given 一个 Text 组件 fontSize=16fp
    When 调用 .minFontScale(0.8).maxFontScale(1.5) 且系统字体缩放=2.0
    Then 实际缩放=clamp(2.0, 0.8, 1.5)=1.5
    And px = 16 × dipScale × 1.5（不是 16 × 2.0）

  # ─── HeightAdaptivePolicy ────────────────────────

  Scenario: MAX_LINES_FIRST（默认）
    Given 一个 Text 组件 maxLines=3
    When 调用 .heightAdaptivePolicy(MAX_LINES_FIRST)
    Then 先遵守 maxLines=3，超出则从 maxFontSize 线性递减到 minFontSize

  Scenario: MIN_FONT_SIZE_FIRST
    Given 一个 Text 组件
    When 调用 .heightAdaptivePolicy(MIN_FONT_SIZE_FIRST)
    Then 先试 minFontSize 一行能否放下；能则二分增长到 max；否则保持 min

  Scenario: LAYOUT_CONSTRAINT_FIRST
    Given 一个 Text 组件 maxLines=UINT32_MAX
    When 调用 .heightAdaptivePolicy(LAYOUT_CONSTRAINT_FIRST)
    Then 先缩到 min 仍溢出则递减 maxLines 删除溢出行
    And maxLines=UINT32_MAX 时用 GetAdaptedMaxLines 估算

  # ─── 自适应算法 ──────────────────────────────────

  Scenario: 二分搜索（MIN_FONT_SIZE_FIRST）
    Given 一个 Text 组件 minFontSize=12, maxFontSize=24, stepSize=1
    When 算法 fitting
    Then 先试 12（一行能否放下）
    And 若能则二分 [12,24] 找最大可放下字号

  Scenario: 线性递减（MAX_LINES_FIRST）
    Given 一个 Text 组件 minFontSize=12, maxFontSize=24
    When 算法 fitting
    Then 从 24 开始每次减 stepSize，直到不超 maxLines 或到 12

  Scenario: DidExceedMaxLines 检查
    Given 一个 Text 组件 fitting 中
    When 检查是否超限
    Then paragraph->DidExceedMaxLines() 或 height > maxSize.Height() 或 longestLine > maxSize.Width()

  # ─── enableVariableFontWeight 交叉引用 ───────────

  Scenario: 变体字重不影响自适应字号
    Given 一个 Text 组件 .fontWeight(550, {enableVariableFontWeight: true})
    When 调用 .minFontSize(12).maxFontSize(24)
    Then 自适应字号算法正常工作
    And 渲染时 wght=550（由 Feat-01 ADR-2 决定，与自适应独立）

  Scenario: EnableDeviceFontWeightCategory 三态（交叉引用 Feat-01）
    Given 一个 Text 组件 EnableVariableFontWeight=true
    When 未设 EnableDeviceFontWeightCategory（Text 默认）
    Then 不应用 GetFontWeightScale()（constants_converter.cpp:621-623）

  # ─── C-API ──────────────────────────────────────

  Scenario: C-API 设置 min/max font size
    Given 一个 ARKUI_NODE_TEXT 节点
    When 调用 setAttribute(node, NODE_TEXT_MIN_FONT_SIZE, {value[0].f32: 12.0})
    And 调用 setAttribute(node, NODE_TEXT_MAX_FONT_SIZE, {value[0].f32: 24.0})
    Then minFontSize=12fp, maxFontSize=24fp

  Scenario: C-API 无 fontScale 枚举
    When 尝试 setAttribute(node, NODE_TEXT_MIN_FONT_SCALE, ...)
    Then 枚举不存在（C-API 缺口，仅 Button 有 @since 18）

  Scenario: C-API 不支持节点 stale 风险
    Given 一个 ARKUI_NODE_BUTTON 节点
    When 调用 getAttribute(node, NODE_TEXT_MIN_FONT_SIZE)
    Then 返回 stale 值（g_numberValues 残留，无 null guard）

  Scenario: styled-string 无自适应字号
    When 尝试通过 OH_ArkUI_SpanStyle 设置 min/max font size
    Then OH_ARKUI_STYLEDSTRINGKEY 无自适应键（FONT key 仅固定字号）
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（覆盖 minFontSize/maxFontSize/minFontScale/maxFontScale/heightAdaptivePolicy + enableVariableFontWeight/enableDeviceFontWeightCategory 交叉引用；不含 fontSize/fontColor/fontWeight/fontStyle/fontFamily（Feat-01）、decoration/textCase（Feat-02）、letterSpacing/lineHeight/baselineOffset（Feat-03）、textShadow/fontFeature/fontVariations（Feat-04））
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "TextLayoutProperty FontStyle AdaptMinFontSize AdaptMaxFontSize MinFontScale MaxFontScale"
  - repo: "openharmony/ace_engine"
    query: "TextAdaptFontSizer AdaptMaxFontSize AdaptMinFontSize binary search linear decrease DidExceedMaxLines"
  - repo: "openharmony/ace_engine"
    query: "text_layout_algorithm BuildParagraph BuildParagraphAdaptUseMinFontSize BuildParagraphAdaptUseLayoutConstraint HeightAdaptivePolicy"
  - repo: "openharmony/ace_engine"
    query: "Dimension ConvertToPxDistributeWithEnv minFontScale maxFontScale clamp font scale"
  - repo: "openharmony/ace_engine"
    query: "style_modifier.cpp SetTextMinFontSize SetTextMaxFontSize NODE_TEXT_MIN_FONT_SIZE NODE_TEXT_MAX_FONT_SIZE"
  - repo: "openharmony/ace_engine"
    query: "enableVariableFontWeight enableDeviceFontWeightCategory constants_converter FontWeightScale 交叉引用 Feat-01"
```

**关键文档：**
- 架构设计：`specs/04-common-capability/03-common-attributes/11-text-common-attributes/design.md`
- Feat-01 交叉引用：`specs/04-common-capability/03-common-attributes/11-text-common-attributes/Feat-01-core-font-attributes-spec.md`
- SDK 类型定义：`interface/sdk-js/api/@internal/component/ets/text.d.ts`、`enums.d.ts`、`text_common.d.ts`
- C-API：`interfaces/native/native_node.h`
