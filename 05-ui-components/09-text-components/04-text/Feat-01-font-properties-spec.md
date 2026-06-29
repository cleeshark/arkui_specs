# 特性规格

> Func-05-09-04-Feat-01 字体属性与自适应字体：固化 font/fontSize/fontColor/fontWeight/fontFamily/fontStyle/fontFeature/fontVariations 八个核心字体属性以及 minFontSize/maxFontSize/minFontScale/maxFontScale/heightAdaptivePolicy 五个自适应字体属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 字体属性与自适应字体 (Font Properties & Adaptive Font) |
| 特性编号 | Func-05-09-04-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 10/12/26 有 API 新增 |
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

### US-1: 设置文本字号

**作为** 应用开发者,
**我想要** 通过 `.fontSize()` 设置 Text 组件的字号,
**以便** 控制文本的显示大小。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.fontSize(value)` 且 value 为正数 number THEN 文本以 value（单位 fp）渲染 | 正常 |
| AC-1.2 | WHEN value 为 string 类型（如 `'16fp'`、`'20px'`） THEN 按对应单位解析并渲染 | 正常 |
| AC-1.3 | WHEN value 为 Resource 类型 THEN 从资源文件解析为对应字号值 | 正常 |
| AC-1.4 | WHEN 未设置 fontSize 且未设置自适应字号 THEN 使用主题默认字号（通常 16fp） | 异常 |
| AC-1.5 | WHEN fontSize 与自适应字号（minFontSize/maxFontSize）同时设置且自适应生效 THEN fontSize 不生效，字号由自适应算法决定 | 异常 |

### US-2: 设置文本颜色

**作为** 应用开发者,
**我想要** 通过 `.fontColor()` 设置文本颜色,
**以便** 控制文本的视觉呈现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.fontColor(value)` 且 value 为合法 ResourceColor THEN 文本以指定颜色渲染 | 正常 |
| AC-2.2 | WHEN 未设置 fontColor THEN 使用主题默认颜色（`#e6182431`，穿戴设备 `#c5ffffff`） | 异常 |

### US-3: 设置文本字重

**作为** 应用开发者,
**我想要** 通过 `.fontWeight()` 设置文本字重,
**以便** 控制文本的粗细程度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.fontWeight(value)` 且 value 为 100~900 的 number THEN 文本以对应字重渲染 | 正常 |
| AC-3.2 | WHEN value 为 FontWeight 枚举（Normal/Bold/Bolder/Lighter/Medium/Regular） THEN 映射到对应数值字重 | 正常 |
| AC-3.3 | WHEN value 为合法字符串（`"400"`、`"bold"` 等） THEN 解析为对应字重 | 正常 |
| AC-3.4 | WHEN value 为非法字符串 THEN 使用默认值 FontWeight.Normal (400) | 异常 |
| AC-3.5 | WHEN 未设置 fontWeight THEN 使用默认值 FontWeight.Normal (400) | 异常 |
| AC-3.6 | WHEN 调用 `.fontWeight(weight, { enableVariableFontWeight: true })` (@since 12) 且 weight 为 100~900 THEN 使用可变字重渲染，字重值不受系统字重档位量化影响 | 正常 |
| AC-3.7 | WHEN 调用 `.fontWeight(weight, { enableVariableFontWeight: false })` 或不传 options THEN 字重受系统字重档位影响（量化到最近的预设档位） | 异常 |

### US-4: 设置字族

**作为** 应用开发者,
**我想要** 通过 `.fontFamily()` 设置文本使用的字族,
**以便** 使用指定字体渲染文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.fontFamily(value)` 且 value 为有效字族名 THEN 文本使用指定字族渲染 | 正常 |
| AC-4.2 | WHEN 指定字族不存在 THEN 回退到系统默认字族 | 异常 |
| AC-4.3 | WHEN value 为 Resource 类型 THEN 从资源文件解析字族名称 | 正常 |
| AC-4.4 | WHEN 在卡片（form）场景下设置 fontFamily THEN 仅 `HarmonyOS Sans` 字族生效，其他字族被忽略 | 正常 |

### US-5: 设置斜体

**作为** 应用开发者,
**我想要** 通过 `.fontStyle()` 控制文本是否斜体,
**以便** 实现斜体排版效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.fontStyle(FontStyle.Italic)` THEN 文本以斜体渲染 | 正常 |
| AC-5.2 | WHEN 调用 `.fontStyle(FontStyle.Normal)` 或未设置 THEN 文本以正体渲染 | 异常 |

### US-6: 使用复合 font 接口

**作为** 应用开发者,
**我想要** 通过 `.font()` 一次性设置字号、字重、字族、斜体,
**以便** 简化多属性设置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.font({ size, weight, family, style })` THEN 各字段分别生效，未指定字段保持已有值或默认值（`text_model_ng.cpp:118` — 仅在 `has_value()` 时调用对应 setter） | 正常 |
| AC-6.2 | WHEN 调用 `.font(fontValue, options)` (@since 12) 且 `options.enableVariableFontWeight` 为 true THEN 可变字重生效 | 正常 |
| AC-6.3 | WHEN 通过 C API `NODE_TEXT_FONT` 设置 THEN `.string` 为字族（逗号分隔）、`.value[0].f32` 为字号(fp)、`.value[1]?.i32` 为字重(ArkUI_FontWeight)、`.value[2]?.i32` 为斜体(ArkUI_FontStyle) | 正常 |

### US-7: 设置 OpenType 字体特性

**作为** 应用开发者,
**我想要** 通过 `.fontFeature()` (@since 12) 设置 OpenType 特性标签,
**以便** 启用连字、风格替代集等高级排版能力。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.fontFeature("ss01 on")` THEN 激活 `ss01` 风格替代集 | 正常 |
| AC-7.2 | WHEN 设置多个特性（逗号分隔，如 `"ss01 on, liga off"`） THEN 各特性独立生效 | 正常 |
| AC-7.3 | WHEN 调用 `.fontFeature("normal")` 或未设置 THEN 使用字体默认 OpenType 特性 | 异常 |
| AC-7.4 | WHEN 通过 C API `NODE_TEXT_FONT_FEATURE` 设置 THEN `.string` 传入 OpenType 特性字符串 | 正常 |

### US-8: 设置可变字体轴

**作为** 应用开发者,
**我想要** 通过 `.fontVariations()` (@since 26.0.0) 设置可变字体的轴参数,
**以便** 精确控制可变字体的视觉表现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `.fontVariations([{ axis: 'wght', value: 600 }])` 且字体支持该轴 THEN 文本以对应轴值渲染 | 正常 |
| AC-8.2 | WHEN 指定的轴标签在当前字体中不支持 THEN 该轴设置被忽略，不影响其他轴 | 异常 |
| AC-8.3 | WHEN FontVariation 类型来源为 `@ohos.graphics.text` 模块 THEN 参数类型在 `text_common.d.ts:1056` 定义为 `import('../api/@ohos.graphics.text').default.FontVariation` | 正常 |

### US-9: 自适应字号

**作为** 应用开发者,
**我想要** 设置 `minFontSize`/`maxFontSize` 和 `heightAdaptivePolicy`，让文本在有限空间内自动调整字号,
**以便** 在不同屏幕尺寸下合理显示内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 同时设置 `minFontSize`、`maxFontSize` 并配合 `maxLines` 或布局约束 THEN 文本字号在 [minFontSize, maxFontSize] 范围内自适应缩放 | 边界 |
| AC-9.2 | WHEN 仅设置 `minFontSize` 未设置 `maxFontSize`（或反之）且无 `maxLines`/布局约束配合 THEN 自适应字号不生效，静默回退到 fontSize（无错误提示） | 异常 |
| AC-9.3 | WHEN `minFontSize` 或 `maxFontSize` ≤ 0 THEN 自适应字号不生效，使用 `fontSize` 值 | 异常 |
| AC-9.4 | WHEN `heightAdaptivePolicy` 为 `MAX_LINES_FIRST`（默认值） THEN 优先满足 maxLines 限制；超出布局约束时在 [minFontSize, maxFontSize] 范围内缩小字号 | 边界 |
| AC-9.5 | WHEN `heightAdaptivePolicy` 为 `MIN_FONT_SIZE_FIRST` THEN 优先使用 minFontSize；若单行可容纳则尝试增大字号至 maxFontSize | 边界 |
| AC-9.6 | WHEN `heightAdaptivePolicy` 为 `LAYOUT_CONSTRAINT_FIRST` THEN 优先满足布局约束；超出时缩小字号；缩至 minFontSize 仍超出则裁剪多余行 | 边界 |
| AC-9.7 | WHEN 自适应字号生效 THEN `fontSize` 设置不生效（自适应优先） | 异常 |
| AC-9.8 | WHEN API ≥ 18 THEN minFontSize/maxFontSize 对子组件和 StyledString 也生效，自适应字号应用于未单独设置字号的部分 | 边界 |

### US-10: 字体缩放范围控制

**作为** 应用开发者,
**我想要** 通过 `minFontScale`/`maxFontScale` (@since 12) 限制系统字体缩放对文本的影响范围,
**以便** 在大字体/无障碍模式下保持合理的文本尺寸。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 调用 `.minFontScale(0.5)` 且系统字体缩放低于 0.5 THEN 文本实际缩放比例不低于 0.5 | 正常 |
| AC-10.2 | WHEN 调用 `.maxFontScale(2.0)` 且系统字体缩放高于 2.0 THEN 文本实际缩放比例不超过 2.0 | 边界 |
| AC-10.3 | WHEN `minFontScale` < 0 THEN 按 0 处理 | 边界 |
| AC-10.4 | WHEN `minFontScale` > 1 THEN 按 1 处理 | 边界 |
| AC-10.5 | WHEN `maxFontScale` < 1 THEN 按 1 处理 | 边界 |
| AC-10.6 | WHEN 异常值（非数字） THEN 设置不生效，保持默认行为 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-4, R-2 | N/A（存量） | 单测 | `test/unittest/core/pattern/text/` |
| AC-2.1~2.2 | R-5 | N/A | 单测 | 同上 |
| AC-3.1~3.7 | R-6, R-7, R-3 | N/A | 单测 | 同上 |
| AC-4.1~4.4 | R-8, R-20, R-1 | N/A | 单测 | 同上 |
| AC-5.1~5.2 | R-9 | N/A | 单测 | 同上 |
| AC-6.1~6.3 | R-10 | N/A | 单测 | 同上 |
| AC-7.1~7.4 | R-11 | N/A | 单测 | 同上 |
| AC-8.1~8.3 | R-12 | N/A | 单测 | 同上 |
| AC-9.1~9.8 | R-13~R-17, R-2, R-22 | N/A | 单测 | 同上 |
| AC-10.1~10.6 | R-18, R-19 | N/A | 单测 | 同上 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | form 场景（`text.d.ts` @form 标注） | 卡片场景仅支持 `HarmonyOS Sans` 字族 | — | AC-4.4 |
| R-2 | 行为 | 需 minFontSize + maxFontSize + (maxLines 或布局约束) 三方配合 | 自适应字号与固定字号互斥：自适应生效时 fontSize 不生效 | — | AC-1.5, AC-9.7 |
| R-3 | 行为 | ArkTS 存入 EnableVariableFontWeight + VariableFontWeight；C API 仅存入 VariableFontWeight | enableVariableFontWeight 双路径：ArkTS 通过 FontSettingOptions 传入，C API 使用独立的 NODE_IMMUTABLE_FONT_WEIGHT 属性 | — | AC-3.6, AC-3.7 |
| R-4 | 行为 | 设置有效正数值（number/string/Resource） | `fontSize` 设置文本字号，单位 fp | `TextLayoutProperty` → FontStyle::propFontSize (`text_styles.h:239`) | AC-1.1~1.4 |
| R-5 | 行为 | 设置合法 ResourceColor | `fontColor` 设置文本颜色 | `TextLayoutProperty` → FontStyle::propTextColor (`text_styles.h:240`) | AC-2.1~2.2 |
| R-6 | 行为 | 设置 100~900 数值、FontWeight 枚举或合法字符串 | `fontWeight` 设置文本字重 | `TextLayoutProperty` → FontStyle::propFontWeight (`text_styles.h:243`) | AC-3.1~3.5 |
| R-7 | 行为 | options.enableVariableFontWeight = true | `fontWeight` + FontSettingOptions 启用可变字重 | `TextLayoutProperty` → FontStyle::propEnableVariableFontWeight + propVariableFontWeight (`text_styles.h:245-246`) | AC-3.6~3.7 |
| R-8 | 行为 | 设置字族名称字符串或 Resource | `fontFamily` 设置字族 | `TextLayoutProperty` → FontStyle::propFontFamily (`text_styles.h:248`) | AC-4.1~4.4 |
| R-9 | 行为 | 设置 FontStyle 枚举 | `fontStyle` 设置斜体 | `TextLayoutProperty` → FontStyle::propItalicFontStyle (`text_styles.h:242`) | AC-5.1~5.2 |
| R-10 | 行为 | 传入 Font 对象（`text_model_ng.cpp:118`） | `font()` 复合设置，内部分解为独立 setter 调用 | FontSize + FontWeight + FontFamily + ItalicFontStyle | AC-6.1~6.3 |
| R-11 | 行为 | 传入特性标签字符串 | `fontFeature` 设置 OpenType 特性 (@since 12) | `TextLayoutProperty` → FontStyle::propFontFeature (`text_styles.h:249`) | AC-7.1~7.4 |
| R-12 | 行为 | 传入 FontVariation 数组 | `fontVariations` 设置可变字体轴 (@since 26.0.0) | `TextLayoutProperty` → FontStyle::propFontVariations (`text_styles.h:250`) | AC-8.1~8.3 |
| R-13 | 行为 | 正数值 | `minFontSize` 设置自适应最小字号 | `TextLayoutProperty` → FontStyle::propAdaptMinFontSize (`text_styles.h:254`) | AC-9.1 |
| R-14 | 行为 | 正数值 | `maxFontSize` 设置自适应最大字号 | `TextLayoutProperty` → FontStyle::propAdaptMaxFontSize (`text_styles.h:255`) | AC-9.1 |
| R-15 | 行为 | MAX_LINES_FIRST / MIN_FONT_SIZE_FIRST / LAYOUT_CONSTRAINT_FIRST | `heightAdaptivePolicy` 选择自适应策略 | `TextLayoutProperty` → TextLineStyle::propHeightAdaptivePolicy (`text_styles.h:378`) | AC-9.4~9.6 |
| R-16 | 行为 | minFontSize 或 maxFontSize ≤ 0 | 自适应字号无效值处理 | 回退至 fontSize | AC-9.3 |
| R-17 | 行为 | 需 minFontSize + maxFontSize + (maxLines 或布局约束) 同时具备 | 自适应字号三方配合要求 | 缺少任一条件自适应不生效 | AC-9.2 |
| R-18 | 行为 | 值域 [0, 1]，< 0 按 0，> 1 按 1 | `minFontScale` 限制缩放下限 (@since 12) | `TextLayoutProperty` → FontStyle::propMinFontScale | AC-10.1, AC-10.3~10.4 |
| R-19 | 行为 | 值域 [1, +∞)，< 1 按 1 | `maxFontScale` 限制缩放上限 (@since 12) | `TextLayoutProperty` → FontStyle::propMaxFontScale | AC-10.2, AC-10.5 |
| R-20 | 异常 | fontFamily 指定的字族不存在 | 无效字族回退 | 回退到系统默认字族（静默，无错误提示） | AC-4.2 |
| R-21 | 异常 | 传入非法字符串（非数字、非枚举名） | 无效 fontWeight 字符串 | 使用默认值 FontWeight.Normal (400) | AC-3.4 |
| R-22 | 异常 | 仅设置 minFontSize 未设置 maxFontSize 或 maxLines/布局约束 | 自适应字号缺少配合属性 | 自适应不生效，静默回退到 fontSize（无错误提示） | AC-9.2 |
| R-23 | 异常 | fontVariations 指定了当前字体不支持的轴标签 | 不支持的可变字体轴 | 该轴设置被忽略，不影响其他轴 | AC-8.2 |
| R-24 | 异常 | 非数字输入 | minFontScale/maxFontScale 异常值 | 设置不生效，保持默认行为 | AC-10.6 |
| R-25 | 恢复 | 属性组懒初始化——FontStyle 属性组在首次设置任一字体属性时通过 `GetOrCreateFontStyle()` 创建 | 未设置任何字体属性时属性组为 null，各属性按主题默认值渲染 | 等同于全部使用主题默认值 | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-4~R-9 (核心字体属性) | 单测 | 各属性设置后渲染结果与设置值一致 |
| VM-2 | R-10 (font 复合) | 单测 | 未指定字段不覆盖已有值 |
| VM-3 | R-11~R-12 (fontFeature/fontVariations) | 单测 | OpenType 特性生效、不支持的轴被忽略 |
| VM-4 | R-13~R-17 (自适应字号) | 单测 | 三方配合条件、策略优先级、无效值回退 |
| VM-5 | R-18~R-19 (fontScale) | 单测 | 系统缩放越界时夹紧到范围边界 |
| VM-6 | R-3 (enableVariableFontWeight 双路径) | 单测 | ArkTS 和 C API 两条路径均可启用可变字重 |

## API 变更分析

> 本特性为存量规格，记录各 API 的引入版本和当前签名。API 签名、d.ts 位置、权限等实现细节见 design.md。

### 新增 API

| API 名称 | 引入版本 | 类型 | 功能描述 | 关联 AC |
|----------|----------|------|----------|---------|
| `font(value: Font)` | @since 7 | Public | 复合设置字号/字重/字族/斜体 | AC-6.1 |
| `font(fontValue: Font, options?: FontSettingOptions)` | @since 12 | Public | 复合设置 + 可变字重选项 | AC-6.2 |
| `fontColor(value: ResourceColor)` | @since 7 | Public | 设置文本颜色 | AC-2.1 |
| `fontSize(value: number\|string\|Resource)` | @since 7 | Public | 设置文本字号 | AC-1.1 |
| `fontWeight(value: number\|FontWeight\|ResourceStr)` | @since 7 | Public | 设置文本字重 | AC-3.1 |
| `fontWeight(weight, options?: FontSettingOptions)` | @since 12 | Public | 设置字重 + 可变字重选项 | AC-3.6 |
| `fontFamily(value: string\|Resource)` | @since 7 | Public | 设置字族 | AC-4.1 |
| `fontStyle(value: FontStyle)` | @since 7 | Public | 设置斜体 | AC-5.1 |
| `fontFeature(value: string)` | @since 12 | Public | 设置 OpenType 特性 | AC-7.1 |
| `fontVariations(fontVariations: Array<FontVariation>)` | @since 26.0.0 | Public | 设置可变字体轴 | AC-8.1 |
| `minFontSize(value: number\|string\|Resource)` | @since 7 | Public | 设置自适应最小字号 | AC-9.1 |
| `maxFontSize(value: number\|string\|Resource)` | @since 7 | Public | 设置自适应最大字号 | AC-9.1 |
| `minFontScale(scale: number\|Resource)` | @since 12 | Public | 限制字体缩放下限 | AC-10.1 |
| `maxFontScale(scale: number\|Resource)` | @since 12 | Public | 限制字体缩放上限 | AC-10.2 |
| `heightAdaptivePolicy(value: TextHeightAdaptivePolicy)` | @since 10 | Public | 选择自适应策略 | AC-9.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `fontWeight(value)` | @since 20 参数类型扩展为 ResourceStr | value 从 `number\|FontWeight\|string` 扩展为 `number\|FontWeight\|ResourceStr` | 兼容变更，无需迁移 | AC-3.1 |
| `minFontSize`/`maxFontSize` | @since 18 行为变更 | 对子组件和 StyledString 也生效 | 兼容扩展，仅影响未单独设置字号的子内容 | AC-9.8 |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 是 — `minFontSize`/`maxFontSize` 自 API 18 起对子组件和 StyledString 生效（之前仅对 Text 自身文本生效）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（核心字体属性）；API 10（heightAdaptivePolicy）；API 12（fontFeature/FontSettingOptions/minFontScale/maxFontScale）；API 26（fontVariations）
- **API 版本号策略:** 各 API 按 `@since` 标注引入版本；`fontWeight` @since 20 扩展参数类型；`minFontSize`/`maxFontSize` @since 18 扩展影响范围

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 属性组懒初始化 | FontStyle 属性组通过 `unique_ptr<FontStyle>` 懒创建（`text_layout_property.h:119`），所有核心字体属性共享同一组实例。未设置的属性为 `std::optional` 空值，与"设为默认值"有语义区别 | 全部 |
| heightAdaptivePolicy 跨属性组存储 | heightAdaptivePolicy 存储在 TextLineStyle 属性组（`text_styles.h:378`），而非 FontStyle 属性组，尽管逻辑上与自适应字号关联 | AC-9.4~9.6 |
| 自适应字号三方配合 | 自适应字号需 minFontSize + maxFontSize + (maxLines 或布局约束) 同时具备才生效，缺少任一条件静默不生效 | AC-9.1~9.2 |
| font() 仅对 Text 自身生效 | `font()` 和带 FontSettingOptions 的 `fontWeight()` 仅影响 Text 组件，不继承到 Span 等子组件 | AC-6.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 字体属性变更触发 `PROPERTY_UPDATE_MEASURE`，仅脏节点重新测量 | benchmark | `test/benchmark/` |

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
| 无障碍 | 是 | `minFontScale`/`maxFontScale` 直接服务于大字体无障碍场景 | AC-10.1~10.6 |
| 大字体 | 是 | 同上；自适应字号可配合大字体模式自动调整 | AC-9.1~9.8 |
| 深色模式 | N/A | fontColor 可由主题切换，但字体属性本身不涉及模式切换逻辑 | — |
| 多窗口/分屏 | N/A | 字体属性不受窗口模式影响 | — |
| 多用户 | N/A | — | — |
| 版本升级 | 是 | API 18 minFontSize/maxFontSize 扩展到子组件；API 12 新增多个 API | AC-9.8 |
| 生态兼容 | N/A | — | — |

## 行为场景（Gherkin）

```gherkin
Feature: Text 字体属性与自适应字体
  作为应用开发者
  我想要通过声明式 API 控制 Text 组件的字体样式和自适应行为
  以便精确控制文本在不同场景下的视觉呈现

  Scenario: 基本字号设置
    Given 一个 Text 组件
    When 调用 .fontSize(20)
    Then 文本以 20fp 字号渲染

  Scenario: font 复合 API 部分设置
    Given 一个已设置 .fontWeight(700) 的 Text 组件
    When 调用 .font({ size: 24 }) 仅指定 size 字段
    Then 字号变为 24fp
    And 字重保持 700 不被覆盖

  Scenario: 可变字重启用
    Given 一个 Text 组件
    When 调用 .fontWeight(350, { enableVariableFontWeight: true })
    Then 文本以 350 可变字重渲染，不量化到 300 或 400 档位

  Scenario: 自适应字号三方配合生效
    Given 一个 Text 组件，设置了 maxLines(3) 和固定高度约束
    When 同时设置 .minFontSize(10) 和 .maxFontSize(24)
    Then 文本字号在 [10fp, 24fp] 范围内自适应，使内容在约束内完整显示

  Scenario: 自适应字号缺少配合条件
    Given 一个 Text 组件，未设置 maxLines 且无固定高度约束
    When 仅设置 .minFontSize(10)
    Then 自适应字号不生效，文本使用 fontSize 或主题默认字号

  Scenario: 字体缩放范围限制
    Given 系统字体缩放设置为 3.0
    When Text 组件设置 .maxFontScale(2.0)
    Then 文本实际缩放比例为 2.0，不超过上限

  Scenario Outline: heightAdaptivePolicy 策略行为
    Given 一个 Text 组件，设置 minFontSize=10, maxFontSize=24, maxLines=2
    When heightAdaptivePolicy 为 <policy>
    Then <behavior>

    Examples:
      | policy                  | behavior                                           |
      | MAX_LINES_FIRST         | 优先满足 2 行限制，超约束时缩小字号                      |
      | MIN_FONT_SIZE_FIRST     | 优先用 10fp，单行可容则增大字号至 24fp                   |
      | LAYOUT_CONSTRAINT_FIRST | 优先满足布局约束，超约束缩小字号，缩至 10fp 仍超则裁剪行     |

  Scenario: C API 复合字体属性
    Given 通过 C API 创建 Text 节点
    When 通过 NODE_TEXT_FONT 设置 .string="HarmonyOS Sans", .value[0].f32=16.0, .value[1].i32=ARKUI_FONT_WEIGHT_BOLD
    Then 文本以 HarmonyOS Sans 字族、16fp 字号、粗体渲染

  Scenario: 无效字族回退
    Given 一个 Text 组件
    When 调用 .fontFamily("NonExistentFont")
    Then 文本使用系统默认字族渲染
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
    query: "Text 组件字体属性存储和布局触发机制"
  - repo: "openharmony/interface_sdk-js"
    query: "Text 组件 font/fontSize/fontWeight API 签名和版本变更"
```

**关键文档：**
- SDK 动态版声明: `interface/sdk-js/api/@internal/component/ets/text.d.ts`
- SDK 静态版声明: `interface/sdk-js/api/arkui/component/text.static.d.ets`
- C API 枚举定义: `interfaces/native/native_node.h`
