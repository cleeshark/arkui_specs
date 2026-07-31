# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Span 文本片段组件 |
| 特性编号 | Func-05-09-06-Feat-01 |
| 所属 Epic | Span 类组件规格补录 |
| 优先级 | P1 |
| 目标版本 | API 7（dynamic 基线）至 API 26（dynamic/static 增强） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Span 文本片段创建与文本内容规格 | 覆盖 `Span(value: string \| Resource)` 构造与 content 装配，dynamic @since 7 / static @since 23 |
| ADDED | Span 字体属性规格（fontColor/fontSize/fontStyle/fontWeight/fontFamily/font/letterSpacing/textCase/fontVariations） | 覆盖 FontStyle 三元组属性，逐 API 标注 @since 版本与参数形态变化 |
| ADDED | Span 装饰与行属性规格（decoration/lineHeight/textShadow/textBackgroundStyle/baselineOffset） | 覆盖 TextLineStyle 与背景/基线偏移属性 |
| ADDED | Span 事件规格（onClick 含 distanceThreshold overload/onHover） | 覆盖仅支持的两种通用事件，声明 onTouch/onKeyEvent/onGesture 不支持 |
| ADDED | Span 节点模型与 dirty 传播规格 | 覆盖 SpanNode(UINode+BaseSpan) 创建路径、SpanItem 数据模型、MarkTextDirty 父级重排机制 |

## 输入文档

| 类型 | 路径 |
|------|------|
| 设计文档 | `05-ui-components/09-text-components/06-span-components/design.md` |
| SDK dynamic | `interface/sdk-js/api/@internal/component/ets/span.d.ts` |
| SDK static | `interface/sdk-js/api/arkui/component/span.static.d.ets` |
| Modifier dynamic | `interface/sdk-js/api/arkui/SpanModifier.d.ts` |
| Modifier static | `interface/sdk-js/api/arkui/SpanModifier.static.d.ets` |
| 节点实现 | `frameworks/core/components_ng/pattern/text/span_node.h:388`（SpanItem）、`:889`（SpanNode）、`:772`（BaseSpan） |
| Model 实现 | `frameworks/core/components_ng/pattern/text/span_model.h:33`（SpanModel）、`span_model_ng.h:27`（SpanModelNG） |
| Bridge 实现 | `frameworks/bridge/declarative_frontend/jsview/js_span.h:30`（JSSpan）、`js_span.cpp` |
| 样式定义 | `frameworks/core/components_ng/pattern/text/text_styles.h:238`（FontStyle）、`:361`（TextLineStyle） |
| C-API NDK | `interfaces/native/native_node.h:59`（ARKUI_NODE_SPAN）、`:3161`（NODE_SPAN_CONTENT）、`:3217`（NODE_SPAN_FONT）、`:3232`（NODE_SPAN_FONT_WEIGHT）、`:3183`（NODE_SPAN_TEXT_BACKGROUND_STYLE）、`:3195`（NODE_SPAN_BASELINE_OFFSET） |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 插入带样式的文本片段

**作为** 应用开发者,
**我想要** 在 `Text` 组件下使用 `Span` 子组件声明一段带独立字体/装饰/行高的文本片段,
**以便** 同一行文本可分段应用不同样式而无需拆分为多个 Text。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 开发者在 `Text` 下声明 `Span('hello')` THEN 该 Span 节点以 `V2::SPAN_ETS_TAG` 挂载为 Text 子节点，其 SpanItem.content 被设置为 'hello'，并触发父级 Text 一次段落构建 | 正常 |
| AC-1.2 | WHEN 开发者传入 `Span($r('app.string.span_text'))`（Resource 类型） THEN Span 解析资源字符串后装入 SpanItem.content，资源解析失败时 content 为空串 | 正常 |
| AC-1.3 | WHEN `Span` 未挂在 `Text`/`RichEditor` 之下（如直接挂在 Column 下） THEN 该 Span 无父级 Paragraph 管线消费，不渲染任何内容（span 不可独立布局） | 边界 |

### US-2: 设置字体样式

**作为** 应用开发者,
**我想要** 通过 fontColor/fontSize/fontStyle/fontWeight/fontFamily/font/letterSpacing/textCase/fontVariations 设置 Span 片段的字体样式,
**以便** 该片段样式独立于同级其他 Span。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `.fontColor(Color.Red)` THEN SpanItem.fontStyle 的 TextColor 字段被设置为红色，重排后该片段文本以红色绘制 | 正常 |
| AC-2.2 | WHEN 调用 `.fontSize(20)` 或 `.fontSize('20vp')` 或 `.fontSize($r('app.size.f20'))` THEN FontStyle.FontSize 以对应数值/vp/Resource 写入，重排后片段字号改变 | 正常 |
| AC-2.3 | WHEN 调用 `.fontStyle(FontStyle.Italic)` THEN FontStyle.ItalicFontStyle 设为 ITALIC，片段以斜体绘制；默认 NORMAL | 正常 |
| AC-2.4 | WHEN 调用 `.fontWeight(FontWeight.Bold)` 或 `.fontWeight(700)` THEN FontStyle.FontWeight 被设置；API 20+ 传入 `Resource` 类型同样生效 | 正常 |
| AC-2.5 | WHEN 调用 `.fontFamily('sans-serif')` 或 `.fontFamily($r('app.font.family'))` THEN FontStyle.FontFamily 写入，片段应用指定字体族 | 正常 |
| AC-2.6 | WHEN 调用 `.font({ size: 16, weight: FontWeight.Bold, family: 'sans-serif', style: FontStyle.Italic })` THEN 一次性设置 size/weight/family/style 四项；API 24+ 可传 fontConfigs 重载 | 正常 |
| AC-2.7 | WHEN 调用 `.letterSpacing(2)` 或 `.letterSpacing($r('app.dim.ls'))`（API 20+ Resource） THEN FontStyle.LetterSpacing 写入，片段字间距改变 | 正常 |
| AC-2.8 | WHEN 调用 `.textCase(TextCase.UpperCase)` THEN FontStyle.TextCase 设为 UPPER_CASE，片段文本转大写绘制；默认 NONE | 正常 |
| AC-2.9 | WHEN 调用 `.fontVariations([{ axis: 'wght', value: 700 }])`（API 26+） THEN FontStyle.FontVariations 写入，可变字体轴被应用 | 正常 |
| AC-2.10 | WHEN 任一字体属性被设置 THEN 经 `DEFINE_SPAN_FONT_STYLE_ITEM` 宏触发 `RequestTextFlushDirty()`，父级 Text/RichEditor 被标记重排 | 正常 |
| AC-2.11 | WHEN 对同一属性先设值再调用 `.fontColor(undefined)` THEN 该属性被重置为继承/默认值，触发重排 | 边界 |

### US-3: 设置装饰、行高、阴影与背景

**作为** 应用开发者,
**我想要** 通过 decoration/lineHeight/textShadow/textBackgroundStyle/baselineOffset 设置片段的装饰与行级样式,
**以便** 片段可呈现下划线/删除线、自定义行高、文本阴影、背景色圆角与基线偏移。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 `.decoration({ type: TextDecorationType.Underline, color: Color.Black })` THEN FontStyle.TextDecoration/TextDecorationColor 写入，片段绘制下划线 | 正常 |
| AC-3.2 | WHEN 调用 `.lineHeight(30)` THEN TextLineStyle.LineHeight 写入，片段所在行以 30vp 行高排版 | 正常 |
| AC-3.3 | WHEN 调用 `.textShadow({ radius: 5, color: Color.Black, offsetX: 1, offsetY: 1 })`（API 11+） THEN FontStyle.TextShadow 写入，片段绘制文本阴影 | 正常 |
| AC-3.4 | WHEN 调用 `.textBackgroundStyle({ color: Color.Yellow, radius: 4 })`（API 11+ dynamic / 23 static） THEN BaseSpan 的 TextBackgroundStyle 写入，片段背景以黄色圆角矩形绘制 | 正常 |
| AC-3.5 | WHEN 调用 `.baselineOffset(10)`（API 11+ dynamic / 23 static） THEN BaseSpan 的 baselineOffset 写入，片段相对基线偏移 10vp | 正常 |
| AC-3.6 | WHEN `textBackgroundStyle.radius` 传入 `BorderRadiuses.TOP_START` 枚举 THEN 背景按指定圆角枚举绘制 | 边界 |

### US-4: 注册点击与悬停事件

**作为** 应用开发者,
**我想要** 通过 onClick/onHover 为 Span 注册点击与悬停回调,
**以便** 用户点击或悬停特定文本片段时触发交互。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 调用 `.onClick((event: ClickEvent) => {})` THEN SpanItem 的 gesture 回调注册点击监听；用户点击该片段文本区域时回调触发，event 包含正确坐标 | 正常 |
| AC-4.2 | WHEN 调用 `.onClick(callback, 20)`（含 distanceThreshold overload） THEN 仅当点击移动距离 < 20vp 时回调触发 | 正常 |
| AC-4.3 | WHEN 调用 `.onHover((isHover: boolean, event) => {})` THEN 鼠标悬停/离开片段区域时回调触发，isHover 反映进入/离开状态 | 正常 |
| AC-4.4 | WHEN 对 Span 调用 `.onTouch()`/`.onKeyEvent()`/`.onGesture()` THEN 这些通用事件不被支持，不产生回调（dynamic 文档明确"通用事件仅支持 onClick/onHover"） | 异常 |

### US-5: 通过 AttributeModifier 动态修改样式

**作为** 应用开发者,
**我想要** 通过 `SpanModifier` 实现 `AttributeModifier<SpanAttribute>` 动态下发 Span 属性,
**以便** 可在运行时按状态切换片段样式。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 使用 `new SpanModifier()` 并实现 `applyNormalAttribute(instance: SpanAttribute)` THEN 通过 `attributeModifier(modifier)` 挂载后，instance 上设置的 font/fontColor 等属性被下发到 SpanNode | 正常 |
| AC-5.2 | WHEN SpanModifier 未实现 `applyNormalAttribute` THEN 该可选方法缺省，不影响 Span 默认属性 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-01 | XTS 用例 + 节点 tag 校验 | span_node.h:889/897 |
| AC-1.2 | R-2 | TASK-01 | XTS 资源解析用例 | js_span.cpp 资源分支 |
| AC-1.3 | R-3 | TASK-01 | 负向用例（无父 Text 不渲染） | multiple_paragraph_layout_algorithm.h:40 |
| AC-2.1 | R-4 | TASK-01 | XTS fontColor 用例 | text_styles.h FontStyle TextColor |
| AC-2.4 | R-7 | TASK-01 | XTS fontWeight/Resource 用例 | span.d.ts fontWeight @since 20 Resource |
| AC-2.6 | R-9 | TASK-01 | XTS font bundle 用例 | span.d.ts font overload @since 10/24 |
| AC-2.10 | R-16 | TASK-01 | dirty 标记校验 | span_node.h RequestTextFlushDirty |
| AC-3.4 | R-12 | TASK-01 | XTS textBackgroundStyle 用例 | span.d.ts TextBackgroundStyle @since 11 |
| AC-4.1 | R-17 | TASK-01 | XTS onClick 用例 | span.static.d.ets onClick overload |
| AC-4.4 | R-19 | TASK-01 | 负向用例（onTouch 无效） | span.d.ts 文档注释 |
| AC-5.1 | R-20 | TASK-01 | XTS SpanModifier 用例 | SpanModifier.d.ts @since 12 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 在 `Text`/`RichEditor` 下声明 `Span(value)` | 创建 SpanNode（tag `V2::SPAN_ETS_TAG`），SpanItem.content 装入 value，挂载为父级子节点 | value 为 `string` 或 `Resource` | AC-1.1 |
| R-2 | 行为 | `Span(value)` 传入 Resource | 解析资源字符串装入 content | 资源解析失败 content 为空串，不抛异常 | AC-1.2 |
| R-3 | 边界 | Span 未挂在 Text/RichEditor 下 | 不渲染（无父级 Paragraph 管线消费） | span 不可独立布局/绘制 | AC-1.3 |
| R-4 | 行为 | 调用 `.fontColor(ResourceColor)` | FontStyle.TextColor 写入，重排后片段以该色绘制 | ResourceColor 含 Color/Resource/number(rgb) | AC-2.1 |
| R-5 | 行为 | 调用 `.fontSize(number\|string\|Resource)` | FontStyle.FontSize 写入 | 负数/0 按 0 处理；string 须为合法 vp/px/fp | AC-2.2 |
| R-6 | 行为 | 调用 `.fontStyle(FontStyle)` | FontStyle.ItalicFontStyle 写入 ITALIC 或 NORMAL | 默认 NORMAL | AC-2.3 |
| R-7 | 行为 | 调用 `.fontWeight(number\|FontWeight\|ResourceStr)` | FontStyle.FontWeight 写入；API 20+ Resource 生效 | number 范围 100–900；FontWeight 枚举映射 | AC-2.4 |
| R-8 | 行为 | 调用 `.fontFamily(string\|Resource)` | FontStyle.FontFamily 写入 | 字体不存在时回退默认字体族 | AC-2.5 |
| R-9 | 行为 | 调用 `.font(Font)` 或 `.font(Font, FontConfigs)`（API 24+） | 一次性设置 size/weight/family/style | fontConfigs 控制可变字体配置 | AC-2.6 |
| R-10 | 行为 | 调用 `.letterSpacing(number\|ResourceStr)` | FontStyle.LetterSpacing 写入；API 20+ Resource 生效 | 负值收紧字距 | AC-2.7 |
| R-11 | 行为 | 调用 `.textCase(TextCase)` | FontStyle.TextCase 写入 UPPER/LOWER/NONE | 默认 NONE | AC-2.8 |
| R-11a | 行为 | 调用 `.fontVariations(Array<FontVariation>)`（API 26+） | FontStyle.FontVariations 写入 | 可变字体轴需字体支持 | AC-2.9 |
| R-12 | 行为 | 调用 `.textBackgroundStyle({ color, radius })`（API 11 dynamic / 23 static） | BaseSpan TextBackgroundStyle 写入，片段背景绘制 | radius 可为 Dimension 或 BorderRadiuses 枚举 | AC-3.4/3.6 |
| R-13 | 行为 | 调用 `.lineHeight(Length)`（API 10+） | TextLineStyle.LineHeight 写入 | =0 时按默认行高 | AC-3.2 |
| R-14 | 行为 | 调用 `.decoration({ type, color })` | FontStyle.TextDecoration/TextDecorationColor 写入 | type 枚举 Underline/LineThrough/Overline/None | AC-3.1 |
| R-15 | 行为 | 调用 `.textShadow(ShadowOptions \| Array<ShadowOptions>)`（API 11+） | FontStyle.TextShadow 写入 | radius/offset 负数按 0 处理 | AC-3.3 |
| R-15a | 行为 | 调用 `.baselineOffset(LengthMetrics)`（API 11 dynamic / 23 static） | BaseSpan baselineOffset 写入 | 负值下移 | AC-3.5 |
| R-16 | 行为 | 任一 Span 字体/行/装饰属性被设置 | 经 `DEFINE_SPAN_FONT_STYLE_ITEM`/`DEFINE_SPAN_TEXT_LINE_STYLE_ITEM` 宏触发 `RequestTextFlushDirty()`，父级 Text/RichEditor 标记重排 | dirty 传播链：SpanNode → BaseSpan::MarkTextDirty → 父级 | AC-2.10 |
| R-17 | 行为 | 调用 `.onClick(callback)` 或 `.onClick(callback, distanceThreshold)` | SpanItem gesture 回调注册；点击片段区域触发 | distanceThreshold>0 时移动超阈值不触发 | AC-4.1/4.2 |
| R-18 | 行为 | 调用 `.onHover(HoverCallback)` | 悬停/离开片段区域触发，isHover 反映状态 | 仅鼠标/触控笔悬停有效 | AC-4.3 |
| R-19 | 异常 | 对 Span 调用 onTouch/onKeyEvent/onGesture | 不支持，不产生回调 | dynamic 文档明确仅 onClick/onHover | AC-4.4 |
| R-20 | 行为 | 使用 `SpanModifier` 实现 `applyNormalAttribute` 并经 `attributeModifier` 挂载 | instance 上设置的属性下发到 SpanNode | applyNormalAttribute 为可选方法 | AC-5.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 Span 创建与挂载 | XTS：声明 Span 后检查 Text 子节点 tag | V2::SPAN_ETS_TAG 挂载 |
| VM-2 | AC-1.3 无父级不渲染 | 负向用例：Span 挂 Column 下不显示 | 无 Paragraph 消费 |
| VM-3 | AC-2.1~2.9 字体属性 | XTS：逐属性设值后截图比对 | FontStyle 字段写入 + 重排 |
| VM-4 | AC-2.10 dirty 传播 | 单测：设值后检查父级 dirty 标记 | RequestTextFlushDirty 调用 |
| VM-5 | AC-2.4 fontWeight Resource | XTS API20+：传入 Resource 生效 | @since 20 Resource 支持 |
| VM-6 | AC-2.6 font bundle/fontConfigs | XTS API24+：font(fontConfigs) 重载 | @since 24 overload |
| VM-7 | AC-2.9 fontVariations | XTS API26+：可变字体轴 | @since 26 |
| VM-8 | AC-3.1~3.6 装饰/行/阴影/背景/偏移 | XTS：逐属性设值后截图比对 | TextLineStyle/BaseSpan 字段 |
| VM-9 | AC-4.1~4.3 onClick/onHover | XTS：模拟点击/悬停事件 | 回调触发与坐标 |
| VM-10 | AC-4.4 onTouch 不支持 | 负向用例：onTouch 无回调 | 文档注释契约 |
| VM-11 | AC-5.1 SpanModifier | XTS：SpanModifier applyNormalAttribute | 属性下发 |

## API 变更分析

### 新增 API

> 本特性为已有能力补录，API 签名见 SDK；以下列 open 范围与 d.ts 位置。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|--------|
| `Span(value: string \| Resource)` dynamic @since 7 / static @since 23 | Public | value: 文本内容 | SpanAttribute | N/A | 创建文本片段 | AC-1.1 |
| `SpanAttribute.fontColor(ResourceColor)` @since 7 | Public | ResourceColor | SpanAttribute | N/A | 设文本色 | AC-2.1 |
| `SpanAttribute.fontSize(number\|string\|Resource)` @since 7 | Public | 字号 | SpanAttribute | N/A | 设字号 | AC-2.2 |
| `SpanAttribute.fontStyle(FontStyle)` @since 7 | Public | 斜体枚举 | SpanAttribute | N/A | 设斜体 | AC-2.3 |
| `SpanAttribute.fontWeight(number\|FontWeight\|ResourceStr)` @since 7（param shape changed @since 20，Resource @since 20） | Public | 字重 | SpanAttribute | N/A | 设字重 | AC-2.4 |
| `SpanAttribute.fontFamily(string\|Resource)` @since 7 | Public | 字体族 | SpanAttribute | N/A | 设字体族 | AC-2.5 |
| `SpanAttribute.font(Font)` @since 10 / `font(Font, FontConfigs)` @since 24 | Public | Font bundle | SpanAttribute | N/A | 一次性设字体 | AC-2.6 |
| `SpanAttribute.letterSpacing(number\|ResourceStr)` @since 7（Resource @since 20） | Public | 字间距 | SpanAttribute | N/A | 设字间距 | AC-2.7 |
| `SpanAttribute.textCase(TextCase)` @since 7 | Public | 大小写枚举 | SpanAttribute | N/A | 设大小写 | AC-2.8 |
| `SpanAttribute.fontVariations(Array<FontVariation>)` @since 26 | Public | 可变字体轴 | SpanAttribute | N/A | 设可变字体 | AC-2.9 |
| `SpanAttribute.decoration(DecorationStyleInterface)` @since 7（DecorationStyleInterface @since 12） | Public | 装饰 | SpanAttribute | N/A | 设装饰线 | AC-3.1 |
| `SpanAttribute.lineHeight(Length)` @since 10 | Public | 行高 | SpanAttribute | N/A | 设行高 | AC-3.2 |
| `SpanAttribute.textShadow(ShadowOptions\|Array<ShadowOptions>)` @since 11 | Public | 阴影 | SpanAttribute | N/A | 设文本阴影 | AC-3.3 |
| `BaseSpan.textBackgroundStyle(TextBackgroundStyle)` @since 11 dynamic / 23 static | Public | 背景 color+radius | T(SpanAttribute) | N/A | 设片段背景 | AC-3.4 |
| `BaseSpan.baselineOffset(LengthMetrics)` @since 12 dynamic / 23 static | Public | 基线偏移 | T(SpanAttribute) | N/A | 设基线偏移 | AC-3.5 |
| `SpanAttribute.onClick(Callback<ClickEvent>)` @since 7 / `onClick(Callback<ClickEvent>, distanceThreshold)` @since 7 | Public | 回调+可选阈值 | SpanAttribute | N/A | 注册点击 | AC-4.1/4.2 |
| `SpanAttribute.onHover(HoverCallback)` @since 7 | Public | 悬停回调 | SpanAttribute | N/A | 注册悬停 | AC-4.3 |
| `SpanAttribute.attributeModifier(AttributeModifier<SpanAttribute>)` @since 12 dynamic / 23 static | Public | modifier | SpanAttribute | N/A | 挂载动态属性 | AC-5.1 |
| `class SpanModifier extends SpanAttribute implements AttributeModifier<SpanAttribute>` @since 12 dynamic / 23 static | Public | — | SpanModifier | N/A | 动态属性载体 | AC-5.1 |
| NDK `ARKUI_NODE_SPAN` 节点创建 + `NODE_SPAN_CONTENT`(@3161)/`NODE_SPAN_FONT`(@3217)/`NODE_SPAN_FONT_WEIGHT`(@3232)/`NODE_SPAN_TEXT_BACKGROUND_STYLE`(@3183)/`NODE_SPAN_BASELINE_OFFSET`(@3195) 属性枚举 | Public | C-API | ArkUI_NodeHandle | N/A | NDK 创建/设属性 | AC-1.1/2.4/3.4/3.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `SpanAttribute.fontWeight` 参数形态 | 变更 | API 20 param shape changed，支持 Resource | 旧 number/FontWeight 调用仍兼容；Resource 需 API 20+ | AC-2.4 |
| `SpanAttribute.letterSpacing` 参数形态 | 变更 | API 20 支持 Resource | 旧 number 调用兼容；Resource 需 API 20+ | AC-2.7 |
| `SpanAttribute.decoration` 参数类型 | 变更 | API 12 由 object 改为 DecorationStyleInterface | 旧 object 调用兼容；widget 场景 style 字段不可用 | AC-3.1 |
| `SpanAttribute.font` overload | 变更 | API 24 增 fontConfigs 重载 | 旧 font(Font) 调用兼容 | AC-2.6 |
| `SpanItem::children`（C++ 内部） | 废弃 | 不再使用内嵌 children 链 | span 平铺于父级 list | — |

## 接口规格

### 接口定义

**Span 构造**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Span(value: string \| Resource): SpanAttribute`（dynamic @since 7）/ `Span(value: string \| Resource): SpanAttribute`（static @since 23，@ComponentBuilder） |
| 返回值 | `SpanAttribute` — 属性链式载体 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string \| Resource | 是 | 无 | Resource 解析失败时 content 为空串 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 在 Text 下声明 Span('hello') | 创建 SpanNode，content='hello'，挂载为子节点 | AC-1.1 |
| 2 | 传入 Resource 字符串 | 解析资源装入 content | AC-1.2 |
| 3 | 未挂 Text/RichEditor | 不渲染 | AC-1.3 |

**fontColor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontColor(value: ResourceColor \| undefined): SpanAttribute`（dynamic @since 7 / static @since 23） |
| 返回值 | SpanAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceColor \| undefined | 否（undefined 重置） | 继承/默认色 | Color/Resource/number(rgb) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | fontColor(Color.Red) | TextColor=红，重排红色绘制 | AC-2.1 |
| 2 | fontColor(undefined) | 重置为默认色，重排 | AC-2.11 |

> 其余属性（fontSize/fontStyle/fontWeight/fontFamily/font/letterSpacing/textCase/fontVariations/decoration/lineHeight/textShadow/textBackgroundStyle/baselineOffset/onClick/onHover）接口规格结构同上，参数约束与行为场景见规则定义 R-4~R-19，为节省篇幅不逐条展开；code-gen 可由规则定义表直接消费。

## 兼容性声明

- **已有 API 行为变更:** 是。`fontWeight` 参数形态 API 20 变化（支持 Resource）；`letterSpacing` API 20 支持 Resource；`decoration` 参数类型 API 12 改为 DecorationStyleInterface（widget 场景 style 字段不可用）；`font` API 24 增 fontConfigs 重载；`fontVariations` API 26 新增。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（dynamic）/ API 23（static）
- **API 版本号策略:** 逐 API 标注 `@since`；dynamic 与 static 双态分别标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Span 必须挂载于 Text/RichEditor | span 不可独立布局/绘制，无父级 Paragraph 管线则不渲染 | AC-1.3 |
| 属性变更经 RequestTextFlushDirty 传播 | DEFINE_SPAN_FONT/TEXT_LINE_STYLE_ITEM 宏触发父级重排 | AC-2.10 |
| 仅 onClick/onHover 通用事件 | onTouch/onKeyEvent/onGesture 不支持 | AC-4.4 |
| static 模式 SpanAttribute 不显式继承 BaseSpan | static 文件直接声明 textBackgroundStyle/baselineOffset；dynamic 经 BaseSpan<T> 继承 | AC-3.4/3.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单 span 属性设置触发重排耗时 ≤ 同等 Text 整体重排 | 帧率/trace | RequestTextFlushDirty 增量标记 |
| 内存 | SpanItem 三元组 unique_ptr 懒初始化 | 内存 profile | span_node.h fontStyle/textLineStyle unique_ptr |
| 可靠性 | 资源解析失败不崩溃 | 异常用例 | js_span.cpp 资源分支 |
| 可测试性 | 节点 tag/SpanItem 字段可观测 | XTS/Inspector | V2::SPAN_ETS_TAG |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | 文本自适应由父级 Text 处理 | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | span 文本经父级 Text 暴露无障碍语义；Span 本身无独立无障碍属性 | 父级 Text accessibility |
| 大字体 | 是 | fontSize 经系统字体缩放 | FontStyle FontSizeScale |
| 深色模式 | 是 | fontColor/textBackgroundStyle color 支持主题资源 | ResourceColor |
| 多窗口/分屏 | 否 | span 行为随父级 Text | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | API 7→26 多版本演进，逐 API @since 标注 | 兼容性声明 |
| 生态兼容 | 是 | dynamic/static 双态并存 | static @since 23 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Span 文本片段
  作为 ArkUI 应用开发者
  我想要 在 Text 中声明带独立样式的文本片段
  以便 同一行文本分段应用不同样式

  Scenario: 在 Text 下创建 Span
    Given Text 组件已挂载
    When 开发者声明 Span('hello')
    Then SpanNode 以 V2::SPAN_ETS_TAG 挂载为 Text 子节点
    And SpanItem.content 被设为 'hello'
    And 父级 Text 触发一次段落构建

  Scenario: Span 未挂载于 Text
    Given Column 组件已挂载
    When 开发者声明 Span('orphan')
    Then 该 Span 无父级 Paragraph 管线消费
    And 不渲染任何内容

  Scenario Outline: Span 字体属性下发
    Given Text 下已声明 Span
    When 调用 <方法>(<参数>)
    Then FontStyle.<字段> 被写入
    And 父级 Text 被标记重排

    Examples:
      | 方法 | 参数 | 字段 |
      | fontColor | Color.Red | TextColor |
      | fontSize | 20 | FontSize |
      | fontStyle | FontStyle.Italic | ItalicFontStyle |
      | letterSpacing | 2 | LetterSpacing |

  Scenario: 点击事件触发
    Given Span 已注册 onClick(callback)
    When 用户点击片段文本区域
    Then callback 触发，event 含正确坐标

  Scenario: 点击移动超阈值不触发
    Given Span 已注册 onClick(callback, 20)
    When 用户点击后移动 30vp
    Then callback 不触发
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SpanNode 如何通过 DEFINE_SPAN_FONT_STYLE_ITEM 宏生成属性访问器并触发 RequestTextFlushDirty"
  - repo: "openharmony/arkui_ace_engine"
    query: "SpanItem 三元组 FontStyle/TextLineStyle/SymbolStyle 的字段定义与资源管理"
  - repo: "openharmony/arkui_ace_engine"
    query: "MultipleParagraphLayoutAlgorithm::UpdateParagraphBySpan 如何消费 SpanItem 列表构建 Paragraph"
  - repo: "openharmony/interface_sdk-js"
    query: "span.d.ts 与 span.static.d.ets 的 dynamic/static 双态 API 差异与 @since 版本"
  - repo: "openharmony/arkui_ace_engine"
    query: "SpanModifier 如何实现 AttributeModifier<SpanAttribute> 的 applyNormalAttribute 下发"
```

**关键文档：** design.md（`05-ui-components/09-text-components/06-span-components/design.md`）；SDK `span.d.ts`/`span.static.d.ets`；`SpanModifier.d.ts`
