# 特性规格

> Func-05-09-03-Feat-03 文本与占位排版：覆盖 textFont/placeholderFont/placeholderColor/fontColor/textAlign/letterSpacing/lineHeight/halfLeading/textIndent/fontFeature/decoration/dividerColor/includeFontPadding/fallbackLineSpacing/textDirection/compressLeadingPunctuation/enableAutoSpacing 共 17 个排版属性。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 文本与占位排版（Text & Placeholder Typography） |
| 特性编号 | Func-05-09-03-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 8 起支持（textFont/placeholderFont/placeholderColor），API 9（textAlign），API 10（fontColor），API 12（letterSpacing/lineHeight/halfLeading/textIndent/fontFeature/decoration），API 18（halfLeading），API 20（enableAutoSpacing），API 23（dividerColor/includeFontPadding/fallbackLineSpacing/textDirection/compressLeadingPunctuation） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 文本字体与颜色规格 | 补录：textFont(@since 8)、fontColor(@since 10)、textAlign(@since 9) |
| ADDED | 占位符样式规格 | 补录：placeholderFont(@since 8)、placeholderColor(@since 8) |
| ADDED | 字间距与行高规格 | 补录：letterSpacing/lineHeight(@since 12)、halfLeading(@since 18) |
| ADDED | 文本缩进与装饰规格 | 补录：textIndent/fontFeature/decoration(@since 12) |
| ADDED | 分割线颜色规格 | 补录：dividerColor(@since 23) |
| ADDED | 高级排版规格 | 补录：includeFontPadding/fallbackLineSpacing/textDirection/compressLeadingPunctuation(@since 23)、enableAutoSpacing(@since 20) |

## 输入文档

- 需求基线：已有能力补录（无独立 requirement.md）
- 设计文档：`05-ui-components/09-text-components/03-search/design.md`（DESIGN-Func-05-09-03，Feat-03 增量合并）
- 源码定位：
  - 实例/静态 Model setter：`frameworks/core/components_ng/pattern/search/search_model_ng.cpp`（textFont :528/1676、placeholderFont :478/1500、placeholderColor :437/1700、fontColor :553/1639、textAlign :672/1790、letterSpacing :1883/2063、lineHeight :2012/2074、halfLeading :2025/2086、textIndent :647/660、fontFeature :1867/1872、decoration :2097/2109、dividerColor :1896/1903、includeFontPadding :2940/2949、fallbackLineSpacing :2968/2977、textDirection :985/1002、compressLeadingPunctuation :2912/2921、enableAutoSpacing :2740/2749）
  - 属性袋：`search_layout_property.h:92-105`（仅 FontFeature:98 + DividerColorSetByUser:103 在 SearchLayoutProperty；其余存于子 TextFieldLayoutProperty/PaintProperty）
  - SDK：`interface/sdk-js/api/@internal/component/ets/search.d.ts`

## 用户故事

### US-1: 文本字体与颜色

**作为** 应用开发者,
**我想要** 配置搜索框文本的字体、颜色与对齐方式,
**以便** 自定义搜索框文本的视觉呈现。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 调用 `.textFont({ size: 16, weight: FontWeight.Bold, family: "sans-serif", style: FontStyle.Italic })` THEN 子文本框 TextFieldLayoutProperty 更新 FontSize/FontWeight/FontFamily/ItalicFontStyle，触发 PROPERTY_UPDATE_MEASURE | 正常 |
| AC-1.2 | WHEN 调用 `.fontColor(Color.Red)` THEN 子文本框 TextColor 设为红色 + TextColorFlagByUser=true，触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-1.3 | WHEN 调用 `.textAlign(TextAlign.Center)` THEN 子文本框 TextAlign 设为 Center + TextAlignChanged=true，触发 PROPERTY_UPDATE_MEASURE | 正常 |
| AC-1.4 | WHEN textAlign 设为 JUSTIFY THEN 行为等同 Start（SDK 明确标注） | 边界 |
| AC-1.5 | WHEN 未设置 textFont THEN 文本使用主题默认字号（手机 16fp，穿戴 18fp） | 正常 |
| AC-1.6 | WHEN 未设置 fontColor THEN 使用主题默认色 #FF182431（穿戴 #dbffffff） | 正常 |

### US-2: 占位符样式

**作为** 应用开发者,
**我想要** 配置占位符文本的字体与颜色,
**以便** 区分占位态与输入态的文本样式。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `.placeholderFont({ size: 14 })` THEN 子文本框 PlaceholderFontSize 等更新，触发 PROPERTY_UPDATE_MEASURE | 正常 |
| AC-2.2 | WHEN 调用 `.placeholderColor(Color.Gray)` THEN 子文本框 PlaceholderTextColor 设为灰色 + PlaceholderColorFlagByUser=true | 正常 |
| AC-2.3 | WHEN 未设置 placeholderColor THEN 使用主题默认色 #99182431（穿戴 #99ffffff） | 正常 |
| AC-2.4 | WHEN 调用 placeholderColor Reset THEN 清除 PlaceholderTextColor + PlaceholderColorFlagByUser，触发 PROPERTY_UPDATE_MEASURE_SELF | 边界 |

### US-3: 字间距与行高

**作为** 应用开发者,
**我想要** 配置文本的字间距、行高与半行距,
**以便** 精细控制搜索框文本排版。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 `.letterSpacing(2)` THEN 子文本框 LetterSpacing 设为 2fp，触发 PROPERTY_UPDATE_MEASURE | 正常 |
| AC-3.2 | WHEN letterSpacing 为百分比或 0 THEN 使用默认值（SDK 约束） | 边界 |
| AC-3.3 | WHEN letterSpacing 为负值 THEN 压缩字间距 | 正常 |
| AC-3.4 | WHEN 调用 `.lineHeight(24)` THEN 子文本框 LineHeight 设为 24fp，触发 PROPERTY_UPDATE_MEASURE | 正常 |
| AC-3.5 | WHEN lineHeight ≤ 0 THEN 行高不受限，字号自适应 | 边界 |
| AC-3.6 | WHEN 调用 `.halfLeading(true)`（@since 18） THEN 子文本框 HalfLeading=true，默认 false | 正常 |

### US-4: 文本缩进与装饰

**作为** 应用开发者,
**我想要** 配置文本缩进、OpenType 字体特性与文本装饰线,
**以便** 启用高级排版特性与文本装饰效果。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 调用 `.textIndent(10)` THEN 子文本框 TextIndent 设为 10，触发 PROPERTY_UPDATE_MEASURE，默认 0 | 正常 |
| AC-4.2 | WHEN 调用 `.fontFeature('"ss01" on')`（@since 12） THEN **SearchLayoutProperty.FontFeature** 设值（唯一存于 Search 自身的排版属性），触发 PROPERTY_UPDATE_MEASURE | 正常 |
| AC-4.3 | WHEN 调用 `.decoration({ type: TextDecorationType.Underline, color: Color.Red, style: TextDecorationStyle.SOLID })` THEN 子文本框 TextDecoration/Color/Style 三属性更新，触发 PROPERTY_UPDATE_MEASURE | 正常 |
| AC-4.4 | WHEN 未设置 decoration THEN 默认 { type: None, color: Black, style: SOLID } | 正常 |

### US-5: 分割线颜色

**作为** 应用开发者,
**我想要** 配置搜索框分割线的颜色,
**以便** 自定义搜索框分割线的视觉外观。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 调用 `.dividerColor(Color.Red)`（@since 23） THEN 子 Divider 节点 DividerRenderProperty.DividerColor 设为红色 + SearchLayoutProperty.DividerColorSetByUser=true，触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-5.2 | WHEN 未设置 dividerColor THEN 使用主题默认色（浅色 0x33000000 / 深色 0x33FFFFFF），DividerColorSetByUser=false | 正常 |
| AC-5.3 | WHEN dividerColor Reset THEN SearchModelStatic 读取 SearchTheme::GetSearchDividerColor() 恢复主题色 | 边界 |

### US-6: 高级排版

**作为** 应用开发者,
**我想要** 配置高级排版属性（字体内边距、回退行距、文本方向、标点压缩、自动间距）,
**以便** 控制字体内边距、行距回退与文本方向等排版细节。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN 调用 `.includeFontPadding(true)`（@since 23） THEN 子文本框 IncludeFontPadding=true，默认 false（不添加首末行间距） | 正常 |
| AC-6.2 | WHEN 调用 `.fallbackLineSpacing(true)`（@since 23） THEN 子文本框 FallbackLineSpacing=true，默认 false；仅当行高 < 实际文本高度时生效 | 正常 |
| AC-6.3 | WHEN 调用 `.textDirection(TextDirection.RTL)`（@since 23） THEN 子文本框 TextDirection 设为 RTL；undefined 时跟随组件布局方向（DEFAULT） | 正常 |
| AC-6.4 | WHEN 调用 `.compressLeadingPunctuation(true)`（@since 23） THEN 子文本框 CompressLeadingPunctuation=true，默认 false（不压缩） | 正常 |
| AC-6.5 | WHEN 调用 `.enableAutoSpacing(true)`（@since 20） THEN 子文本框 EnableAutoSpacing=true，默认 false（中英文自动间距） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-03 | UITest | search_model_ng.cpp:528 SetTextFont |
| AC-1.2 | R-2 | TASK-03 | UITest | search_model_ng.cpp:553 SetTextColor |
| AC-1.3 | R-3 | TASK-03 | UITest | search_model_ng.cpp:672 SetTextAlign |
| AC-1.4 | R-4 | TASK-03 | UITest | search.d.ts:942 JUSTIFY=Start |
| AC-1.5 | R-5 | TASK-03 | UITest | search.d.ts:739 默认 |
| AC-1.6 | R-5 | TASK-03 | UITest | search.d.ts:562 默认 #FF182431 |
| AC-2.1 | R-6 | TASK-03 | UITest | search_model_ng.cpp:478 SetPlaceholderFont |
| AC-2.2 | R-7 | TASK-03 | UITest | search_model_ng.cpp:437 SetPlaceholderColor |
| AC-2.3 | R-5 | TASK-03 | UITest | search.d.ts:716 默认 #99182431 |
| AC-2.4 | R-8 | TASK-03 | UITest | search_model_ng.cpp:461 ResetPlaceholderColor |
| AC-3.1 | R-9 | TASK-03 | UITest | search_model_ng.cpp:1883 SetLetterSpacing |
| AC-3.2 | R-10 | TASK-03 | UITest | search.d.ts:1125 百分比/0→默认 |
| AC-3.3 | R-9 | TASK-03 | UITest | search.d.ts:1135 负值压缩 |
| AC-3.4 | R-11 | TASK-03 | UITest | search_model_ng.cpp:2012 SetLineHeight |
| AC-3.5 | R-12 | TASK-03 | UITest | search.d.ts:1148 ≤0 自适应 |
| AC-3.6 | R-13 | TASK-03 | UITest | search_model_ng.cpp:2025 SetHalfLeading |
| AC-4.1 | R-14 | TASK-03 | UITest | search_model_ng.cpp:647 SetTextIndent |
| AC-4.2 | R-15 | TASK-03 | UITest | search_model_ng.cpp:1867 SetFontFeature→SearchLayoutProperty |
| AC-4.3 | R-16 | TASK-03 | UITest | search_model_ng.cpp:2097 SetTextDecoration |
| AC-4.4 | R-5 | TASK-03 | UITest | search.d.ts:1111 默认 |
| AC-5.1 | R-17 | TASK-03 | UITest | search_model_ng.cpp:1903 SetDividerColor |
| AC-5.2 | R-5 | TASK-03 | UITest | search.d.ts:1454 主题默认 |
| AC-5.3 | R-18 | TASK-03 | UITest | search_model_static.cpp:436 GetSearchDividerColor |
| AC-6.1 | R-19 | TASK-03 | UITest | search_model_ng.cpp:2940 SetIncludeFontPadding |
| AC-6.2 | R-20 | TASK-03 | UITest | search_model_ng.cpp:2968 SetFallbackLineSpacing |
| AC-6.3 | R-21 | TASK-03 | UITest | search_model_ng.cpp:985 SetTextDirection |
| AC-6.4 | R-22 | TASK-03 | UITest | search_model_ng.cpp:2912 SetCompressLeadingPunctuation |
| AC-6.5 | R-23 | TASK-03 | UITest | search_model_ng.cpp:2740 SetEnableAutoSpacing |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|----------|----------|-----------|---------|
| R-1 | 行为 | `textFont(Font)` 设置 | 子文本框 TextFieldLayoutProperty 更新 FontSize/ItalicFontStyle/FontWeight/Family + PreferredTextLineHeightNeedToUpdate(true)，触发 MEASURE | 写入子节点而非 SearchLayoutProperty | AC-1.1 |
| R-2 | 行为 | `fontColor(Color)` 设置 | 子文本框 TextColor + TextColorFlagByUser=true，触发 RENDER | 写入子 TextFieldLayoutProperty+PaintProperty | AC-1.2 |
| R-3 | 行为 | `textAlign(TextAlign)` 设置 | 子文本框 TextAlign + TextAlignChanged=true，触发 MEASURE | JUSTIFY 行为等同 Start | AC-1.3, AC-1.4 |
| R-4 | 边界 | textAlign=JUSTIFY | 行为等同 Start | SDK 明确标注 | AC-1.4 |
| R-5 | 行为 | 未设置 textFont/fontColor/placeholderColor/decoration/dividerColor | 使用主题默认值 | 各属性默认值见 SDK | AC-1.5, AC-1.6, AC-2.3, AC-4.4, AC-5.2 |
| R-6 | 行为 | `placeholderFont(Font)` 设置 | 子文本框 PlaceholderFontSize 等更新 + PreferredPlaceholderLineHeightNeedToUpdate(true)，触发 MEASURE | 写入子节点 | AC-2.1 |
| R-7 | 行为 | `placeholderColor(Color)` 设置 | 子文本框 PlaceholderTextColor + PlaceholderColorFlagByUser=true，触发 MEASURE | 写入子 TextFieldLayoutProperty+PaintProperty | AC-2.2 |
| R-8 | 边界 | `placeholderColor` Reset | 清除 PlaceholderTextColor + PlaceholderColorFlagByUser，触发 MEASURE_SELF | 实例 Reset 用 MEASURE_SELF | AC-2.4 |
| R-9 | 行为 | `letterSpacing(Dimension)` 设置非零非百分比 | 子文本框 LetterSpacing 设值，触发 MEASURE | 单位 fp；负值压缩；应用于每个字符含行尾 | AC-3.1, AC-3.3 |
| R-10 | 边界 | letterSpacing 为百分比或 0 | 使用默认值 | SDK 约束 | AC-3.2 |
| R-11 | 行为 | `lineHeight(Dimension)` 设置正值 | 子文本框 LineHeight 设值，触发 MEASURE | 单位 fp | AC-3.4 |
| R-12 | 边界 | lineHeight ≤ 0 | 行高不受限，字号自适应 | 与常规数值语义不同 | AC-3.5 |
| R-13 | 行为 | `halfLeading(bool)` 设置（@since 18） | 子文本框 HalfLeading 设值，触发 MEASURE | 默认 false | AC-3.6 |
| R-14 | 行为 | `textIndent(Dimension)` 设置 | 子文本框 TextIndent 设值，触发 MEASURE | 默认 0 | AC-4.1 |
| R-15 | 行为 | `fontFeature(string)` 设置（@since 12） | **SearchLayoutProperty.FontFeature** 设值（唯一存于 Search 自身的排版属性），触发 MEASURE | 写入 Search 而非子节点 | AC-4.2 |
| R-16 | 行为 | `decoration(TextDecorationOptions)` 设置 | 子文本框 TextDecoration/Color/Style 三属性更新，触发 MEASURE | 单个 SDK 属性拆为 3 个内部 setter | AC-4.3 |
| R-17 | 行为 | `dividerColor(Color)` 设置（@since 23） | 子 Divider 节点 DividerRenderProperty.DividerColor + SearchLayoutProperty.DividerColorSetByUser=true，触发 RENDER | 分裂存储：标志在 Search + 颜色在子 Divider | AC-5.1 |
| R-18 | 边界 | `dividerColor` Reset/空值 | SearchModelStatic 读取 SearchTheme::GetSearchDividerColor() 恢复主题色 + 重置标志 | 唯一在静态层查主题的排版 API | AC-5.3 |
| R-19 | 行为 | `includeFontPadding(bool)` 设置（@since 23） | 子文本框 IncludeFontPadding 设值 | 默认 false | AC-6.1 |
| R-20 | 行为 | `fallbackLineSpacing(bool)` 设置（@since 23） | 子文本框 FallbackLineSpacing 设值 | 默认 false；仅行高<实际文本高度时生效 | AC-6.2 |
| R-21 | 行为 | `textDirection(TextDirection)` 设置（@since 23） | 子文本框 TextDirection 设值；undefined 跟随组件布局方向(DEFAULT) | Reset 用 MEASURE_SELF | AC-6.3 |
| R-22 | 行为 | `compressLeadingPunctuation(bool)` 设置（@since 23） | 子文本框 CompressLeadingPunctuation 设值 | 默认 false | AC-6.4 |
| R-23 | 行为 | `enableAutoSpacing(bool)` 设置（@since 20） | 子文本框 EnableAutoSpacing 设值 | 默认 false；中英文自动间距 | AC-6.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | US-1 文本字体与颜色 | UITest | 验证 textFont/fontColor/textAlign 写入子 TextFieldLayoutProperty；JUSTIFY=Start |
| VM-2 | US-2 占位符样式 | UITest | 验证 placeholderFont/placeholderColor 写入子节点；Reset 语义 |
| VM-3 | US-3 字间距与行高 | UITest | 验证 letterSpacing 百分比/0→默认；lineHeight ≤0 自适应；halfLeading |
| VM-4 | US-4 缩进与装饰 | UITest | 验证 textIndent/decoration 写入子节点；fontFeature 写入 SearchLayoutProperty |
| VM-5 | US-5 分割线颜色 | UITest | 验证 dividerColor 分裂存储；Reset 读取主题色 |
| VM-6 | US-6 高级排版 | UITest | 验证 5 个高级排版属性默认 false 与写入子节点 |

## API 变更分析

### 新增 API

> 补录已有 Public API。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `textFont(value?: Font)` | Public | Font{size/weight/family/style} | SearchAttribute | 无 | 文本字体 | AC-1.1 |
| `placeholderFont(value?: Font)` | Public | 同上 | SearchAttribute | 无 | 占位符字体 | AC-2.1 |
| `placeholderColor(value: ResourceColor)` | Public | ResourceColor | SearchAttribute | 无 | 占位符颜色 | AC-2.2 |
| `fontColor(value: ResourceColor)` | Public | ResourceColor | SearchAttribute | 无 | 文本颜色 | AC-1.2 |
| `textAlign(value: TextAlign)` | Public | TextAlign | SearchAttribute | 无 | 文本对齐 | AC-1.3 |
| `letterSpacing(value: number\|string\|Resource)` | Public | Dimension(fp) | SearchAttribute | 无 | 字间距 | AC-3.1..AC-3.3 |
| `lineHeight(value: number\|string\|Resource)` | Public | Dimension(fp) | SearchAttribute | 无 | 行高 | AC-3.4, AC-3.5 |
| `halfLeading(halfLeading: Optional<boolean>)` | Public | boolean | SearchAttribute | 无 | 半行距 | AC-3.6 |
| `textIndent(value: Dimension)` | Public | Dimension | SearchAttribute | 无 | 文本缩进 | AC-4.1 |
| `fontFeature(value: string)` | Public | string(OpenType 格式) | SearchAttribute | 无 | OpenType 字体特性 | AC-4.2 |
| `decoration(value: TextDecorationOptions)` | Public | {type/color/style} | SearchAttribute | 无 | 文本装饰线 | AC-4.3 |
| `dividerColor(color: Optional<ColorMetrics>)` | Public | ColorMetrics | SearchAttribute | 无 | 分割线颜色 | AC-5.1..AC-5.3 |
| `includeFontPadding(include: Optional<boolean>)` | Public | boolean | SearchAttribute | 无 | 字体内边距 | AC-6.1 |
| `fallbackLineSpacing(enabled: Optional<boolean>)` | Public | boolean | SearchAttribute | 无 | 回退行距 | AC-6.2 |
| `textDirection(direction: TextDirection\|undefined)` | Public | TextDirection | SearchAttribute | 无 | 文本方向 | AC-6.3 |
| `compressLeadingPunctuation(enabled: Optional<boolean>)` | Public | boolean | SearchAttribute | 无 | 标点压缩 | AC-6.4 |
| `enableAutoSpacing(enabled: Optional<boolean>)` | Public | boolean | SearchAttribute | 无 | 自动间距 | AC-6.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 多个属性 @since 跨版本 | 变更 | textFont/placeholderFont/placeholderColor @since 8；textAlign @since 9；fontColor @since 10；letterSpacing/lineHeight/textIndent/fontFeature/decoration @since 12；halfLeading @since 18；enableAutoSpacing @since 20；dividerColor/includeFontPadding/fallbackLineSpacing/textDirection/compressLeadingPunctuation @since 23 | 低版本不支持对应属性 | 全部 AC |

## 接口规格

> 17 个 API 均为 Public、无错误码。参数约束与默认值见规则定义表与 SDK @since 标注。L1+ 复杂度，以下仅列代表性接口定义。

### 接口定义

**fontFeature(value: string)** — 唯一存于 SearchLayoutProperty 的排版属性

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontFeature(value: string): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | — | 格式 `normal \| <feature-tag-value>`；写入 SearchLayoutProperty.FontFeature(MEASURE) |

---

**dividerColor(color: Optional<ColorMetrics>)** — 分裂存储的排版属性

| 属性 | 值 |
|------|-----|
| 函数签名 | `dividerColor(color: Optional<ColorMetrics>): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1..AC-5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| color | ColorMetrics | 否 | 主题色(浅色 0x33000000/深色 0x33FFFFFF) | 空值→SearchModelStatic 读 SearchTheme::GetSearchDividerColor() |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置颜色 | 子 Divider DividerColor + SearchLayoutProperty.DividerColorSetByUser=true，RENDER | AC-5.1 |
| 2 | 未设置 | 主题默认色，DividerColorSetByUser=false | AC-5.2 |
| 3 | Reset | 读取 SearchTheme::GetSearchDividerColor() 恢复 | AC-5.3 |

## 兼容性声明

- **已有 API 行为变更:** 是。17 个属性跨 API 8-23 引入；letterSpacing 百分比/0 使用默认值（非常规数值语义）；lineHeight ≤0 自适应字号（非常规语义）；textAlign JUSTIFY 等同 Start；dividerColor 分裂存储（标志在 Search + 颜色在子 Divider）。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8（textFont/placeholderFont/placeholderColor）
- **API 版本号策略:** 按 SDK @since 标注（8/9/10/12/18/20/23）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 排版属性存于子节点 | 17 个中 15 个存于子 TextFieldLayoutProperty/PaintProperty，仅 fontFeature 存于 SearchLayoutProperty；dividerColor 分裂存储 | 全部 AC |
| dirty-flag 不对称 | placeholderColor/fontColor 实例与 FrameNode 重载 dirty flag 不一致（MEASURE vs RENDER vs MEASURE_SELF） | AC-2.4 |
| letterSpacing 特殊值 | 百分比或 0 → 默认值；负值压缩 | AC-3.2, AC-3.3 |
| lineHeight 特殊值 | ≤0 → 不受限自适应 | AC-3.5 |
| dividerColor 主题默认 | 唯一在 SearchModelStatic 读主题色的排版 API | AC-5.3 |
| textDirection 命名分裂 | C-API 用 setSearchDirection，ArkTS 用 setTextDirection | AC-6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 排版属性变更触发 MEASURE/RENDER，单帧内完成 | UITest 帧率 | search_model_ng.cpp 各 setter MarkDirtyNode |
| 内存 | 属性存于子节点 TextFieldLayoutProperty，SearchLayoutProperty 仅含 fontFeature + DividerColorSetByUser 标志 | 内存分析 | search_layout_property.h:92-105 |
| 可测试性 | fontFeature/DividerColorSetByUser 经 SearchLayoutProperty 暴露；其余经子 TextField 属性暴露 | Inspector dump | search_layout_property.h:98,103 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | textFont 默认 16fp，fontColor #FF182431，placeholderColor #99182431 | — | UITest | search.d.ts:739,562,716 |
| 平板 | 同手机 | 无差异 | UITest | — |
| 折叠屏 | 同手机 | 无差异 | UITest | — |
| 穿戴 | textFont 默认 18fp，fontColor #dbffffff，placeholderColor #99ffffff | 默认值不同 | UITest | search.d.ts:739,562,716 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 排版属性不影响无障碍语义 | — |
| 大字体 | 是 | textFont/fontFeature 受 minFontScale/maxFontScale 约束（Feat-04） | AC-1.1 |
| 深色模式 | 是 | fontColor/placeholderColor/dividerColor 未设色时深色模式自动更新主题色 | AC-1.6, AC-2.3, AC-5.2 |
| 多窗口/分屏 | 否 | 无特殊行为 | — |
| 多用户 | 否 | 无特殊行为 | — |
| 版本升级 | 是 | 17 属性跨 API 8-23 持续引入 | 全部 AC |
| 生态兼容 | 是 | 动态+静态+C-API 修饰符全覆盖 | 全部 AC |

## 行为场景（Gherkin）

```gherkin
Feature: Search 文本与占位排版
  作为应用开发者
  我想要配置搜索框文本与占位符的排版样式
  以便提供一致的文本视觉

  Scenario Outline: 排版属性写入目标节点
    Given Search 组件已创建
    When 调用 .<api>(<value>)
    Then 属性写入 <target> 并触发 <flag>

    Examples:
      | api | value | target | flag |
      | textFont | {size:16} | 子 TextFieldLayoutProperty | MEASURE |
      | fontColor | Color.Red | 子 TextFieldLayoutProperty+PaintProperty | RENDER |
      | fontFeature | '"ss01" on' | SearchLayoutProperty | MEASURE |
      | dividerColor | Color.Red | 子 DividerRenderProperty + SearchLayoutProperty(标志) | RENDER |

  Scenario: letterSpacing 特殊值
    Given Search 组件已创建
    When 调用 .letterSpacing(<value>)
    Then 字间距 <result>

    Examples:
      | value | result |
      | 2 | 2fp 间距 |
      | 0 | 默认值 |
      | "50%" | 默认值 |
      | -1 | 压缩 |

  Scenario: lineHeight 特殊值
    Given Search 组件已创建
    When 调用 .lineHeight(<value>)
    Then 行高 <result>

    Examples:
      | value | result |
      | 24 | 24fp |
      | 0 | 不受限自适应 |
      | -1 | 不受限自适应 |

  Scenario: textAlign JUSTIFY 等同 Start
    Given Search 组件已创建
    When 调用 .textAlign(TextAlign.JUSTIFY)
    Then 文本对齐行为等同 TextAlign.Start

  Scenario: dividerColor Reset 恢复主题色
    Given Search 组件已创建且用户曾设置 dividerColor 为红色
    When 调用 dividerColor Reset
    Then SearchModelStatic 读取 SearchTheme::GetSearchDividerColor() 恢复主题色
    And DividerColorSetByUser 重置为 false
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
    query: "17 个排版属性中 15 个存于子 TextFieldLayoutProperty 而非 SearchLayoutProperty 的存储架构"
  - repo: "openharmony/arkui_ace_engine"
    query: "fontFeature 为何唯一存于 SearchLayoutProperty(FontFeature:98) 而非子文本框"
  - repo: "openharmony/arkui_ace_engine"
    query: "dividerColor 分裂存储：DividerColorSetByUser(bool,SearchLayoutProperty) + 颜色(子 DividerRenderProperty)"
  - repo: "openharmony/arkui_ace_engine"
    query: "placeholderColor/fontColor 实例与 FrameNode 重载 dirty flag 不对称（MEASURE vs RENDER vs MEASURE_SELF）"
  - repo: "openharmony/interface_sdk-js"
    query: "search.d.ts 中 17 个排版属性的 @since 版本与默认值/约束"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/search.d.ts`；`frameworks/core/components_ng/pattern/search/search_model_ng.cpp`；`search_layout_property.h`；`design.md`(DESIGN-Func-05-09-03)
