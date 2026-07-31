# 特性规格

> Func-05-09-01-Feat-02 字体样式：固化 fontColor/fontSize/allowScale/fontWeight/fontFamily 五个字体样式属性的行为规格，包含主题默认值（穿戴与普通设备差异）、allowScale 与系统字号缩放交互、inspector 默认值与运行时不一致等关键行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 字体样式 (Font Style) |
| 特性编号 | Func-05-09-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 8 起支持（动态版），API 23 静态版，API 26 静态双签名 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | fontColor 字体颜色属性行为规格 | 含主题默认与 OnColorConfigurationUpdate |
| ADDED | fontSize 字号属性行为规格 | 含 fp 单位与不可百分比 |
| ADDED | allowScale 缩放开关行为规格 | 默认 true，与系统字号缩放交互 |
| ADDED | fontWeight 字重属性行为规格 | 含 number/枚举/字符串三态 |
| ADDED | fontFamily 字族属性行为规格 | 含卡片场景限制 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/01-marquee/design.md` | Baselined |

---

## 用户故事

### US-1: 设置字体颜色

**作为** 应用开发者,
**我想要** 通过 `.fontColor()` 设置跑马灯文本颜色,
**以便** 控制文本视觉呈现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.fontColor(value)` 且 value 为合法 ResourceColor THEN 文本以指定颜色渲染，存 MarqueeLayoutProperty::FontColor（`marquee_model_ng.cpp:110`） | 正常 |
| AC-1.2 | WHEN 未设置 fontColor THEN 运行时取 TextTheme::GetTextStyle().GetTextColor()（`marquee_pattern.cpp:963`），普通设备 `#182431` @ alpha 0.9，穿戴设备白色 @ 0.9 | 边界 |
| AC-1.3 | WHEN 颜色配置变更（OnColorConfigurationUpdate）THEN 覆盖为 MarqueeTheme::GetTextColor()（font_primary 无 alpha，`marquee_pattern.cpp:713-716`）并重启滚动 | 正常 |
| AC-1.4 | WHEN inspector 读取未设置的 fontColor THEN 显示 value_or(Color::BLACK)（`marquee_layout_property.h:94`），与运行时 TextTheme 默认不一致 | 异常 |

### US-2: 设置字号

**作为** 应用开发者,
**我想要** 通过 `.fontSize()` 设置跑马灯字号,
**以便** 控制文本大小。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.fontSize(value)` 且 value 为正数 number THEN 以 fp 为单位渲染（`marquee_model_ng.cpp:116` SetFontSize） | 正常 |
| AC-2.2 | WHEN value 为 string（如 `'16fp'`、`'20px'`）THEN 按对应单位解析渲染 | 正常 |
| AC-2.3 | WHEN value 为 Resource 类型 THEN 从资源文件解析字号 | 正常 |
| AC-2.4 | WHEN value 为百分比 THEN 不支持，被忽略 | 异常 |
| AC-2.5 | WHEN 未设置 fontSize THEN 运行时取 TextTheme 默认：普通设备 16.0fp，穿戴设备 15.0fp（`marquee_pattern.cpp:955`，`text_theme.cpp:34`） | 边界 |
| AC-2.6 | WHEN inspector 读取未设置的 fontSize THEN 显示 10.0_vp（`marquee_layout_property.h:93`），与运行时 16fp/15fp 不一致 | 异常 |

### US-3: 设置缩放开关

**作为** 应用开发者,
**我想要** 通过 `.allowScale()` 控制字号是否随系统字号缩放,
**以便** 在 fp 字号下控制是否响应系统字号设置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.allowScale(true)` 且 fontSize 为 fp 单位 THEN 字号随系统字号缩放（写入 MarqueeLayoutProperty 与文本子节点 TextLayoutProperty，`marquee_model_ng.cpp:94-102`） | 正常 |
| AC-3.2 | WHEN 调用 `.allowScale(false)` THEN fp 字号不随系统字号缩放，按固定值渲染 | 正常 |
| AC-3.3 | WHEN 未设置 allowScale THEN 默认 value_or(true) 即启用缩放（`marquee_model_ng.cpp:99,101`） | 边界 |
| AC-3.4 | WHEN allowScale 仅在 fontSize 为 fp 单位时生效 THEN px/vp 单位字号不受 allowScale 影响 | 边界 |
| AC-3.5 | WHEN 系统字号变更（OnFontScaleConfigurationUpdate）且 allowScale=true THEN 触发 StopMarqueeAnimation(playStatus) 重启滚动以适配新布局（`marquee_pattern.cpp:1227-1246`） | 正常 |
| AC-3.6 | WHEN inspector 读取未设置的 allowScale THEN 显示 false（`marquee_layout_property.h:92`），与运行时默认 true 不一致 | 异常 |

### US-4: 设置字重

**作为** 应用开发者,
**我想要** 通过 `.fontWeight()` 设置跑马灯字重,
**以便** 控制文本粗细。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN value 为 100~900 的 number（步长 100）THEN 文本以对应数值字重渲染（`marquee_model_ng.cpp:126` SetFontWeight） | 正常 |
| AC-4.2 | WHEN value 为 FontWeight 枚举（Normal/Bold/Bolder/Lighter/Medium/Regular）THEN 映射到对应数值字重 | 正常 |
| AC-4.3 | WHEN value 为合法字符串（`"400"`、`"bold"` 等）THEN 解析为对应字重 | 正常 |
| AC-4.4 | WHEN value 过大导致文本被裁剪 THEN 按字体能力裁剪渲染（SDK 注释 marquee.d.ts:248-253） | 边界 |
| AC-4.5 | WHEN 未设置 fontWeight THEN 默认 FontWeight::NORMAL (400)（`marquee_pattern.cpp:957`） | 边界 |
| AC-4.6 | WHEN inspector 读取未设置的字重 THEN 显示 NORMAL（`marquee_layout_property.h:96-97`），与运行时一致 | 正常 |

### US-5: 设置字族

**作为** 应用开发者,
**我想要** 通过 `.fontFamily()` 设置跑马灯字族,
**以便** 使用指定字体渲染文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.fontFamily(value)` 且 value 为有效字族名 THEN 文本使用指定字族渲染（`marquee_model_ng.cpp:135` SetFontFamily） | 正常 |
| AC-5.2 | WHEN 指定字族不存在 THEN 回退到系统默认字族 HarmonyOS Sans | 异常 |
| AC-5.3 | WHEN value 为 Resource 类型 THEN 从资源文件解析字族名称 | 正常 |
| AC-5.4 | WHEN 未设置 fontFamily THEN 文本子节点字族被 reset（`marquee_pattern.cpp:958-962`），使用 HarmonyOS Sans | 边界 |
| AC-5.5 | WHEN 在卡片（form）场景下设置 fontFamily THEN 仅 HarmonyOS Sans 字族生效，其他字族被忽略（SDK 注释 marquee.d.ts:264-270） | 正常 |
| AC-5.6 | WHEN inspector 读取未设置的字族 THEN 显示 "HarmonyOS Sans"（`marquee_layout_property.h:99-102`），与运行时一致 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-02 | UI 测试 | marquee_model_ng.cpp:110 |
| AC-1.2 | R-2 | TASK-02 | 主题测试 | marquee_pattern.cpp:963 |
| AC-1.3 | R-3 | TASK-02 | 深色模式测试 | marquee_pattern.cpp:713-716 |
| AC-1.4 | R-9 | TASK-02 | inspector 测试 | marquee_layout_property.h:94 |
| AC-2.1 | R-4 | TASK-02 | UI 测试 | marquee_model_ng.cpp:116 |
| AC-2.2 | R-4 | TASK-02 | UI 测试 | marquee_model_ng.cpp:116 |
| AC-2.3 | R-4 | TASK-02 | 资源测试 | marquee_model_ng.cpp:116 |
| AC-2.4 | R-5 | TASK-02 | 单测 | marquee_model_ng.cpp:116 |
| AC-2.5 | R-6 | TASK-02 | 主题测试 | marquee_pattern.cpp:955 |
| AC-2.6 | R-9 | TASK-02 | inspector 测试 | marquee_layout_property.h:93 |
| AC-3.1 | R-7 | TASK-02 | 大字体测试 | marquee_model_ng.cpp:94-102 |
| AC-3.2 | R-7 | TASK-02 | 大字体测试 | marquee_model_ng.cpp:94-102 |
| AC-3.3 | R-8 | TASK-02 | 单测 | marquee_model_ng.cpp:99,101 |
| AC-3.4 | R-7 | TASK-02 | 单测 | marquee_model_ng.cpp:94-102 |
| AC-3.5 | R-10 | TASK-02 | 大字体测试 | marquee_pattern.cpp:1227-1246 |
| AC-3.6 | R-9 | TASK-02 | inspector 测试 | marquee_layout_property.h:92 |
| AC-4.1 | R-11 | TASK-02 | UI 测试 | marquee_model_ng.cpp:126 |
| AC-4.2 | R-11 | TASK-02 | UI 测试 | marquee_model_ng.cpp:126 |
| AC-4.3 | R-11 | TASK-02 | UI 测试 | marquee_model_ng.cpp:126 |
| AC-4.4 | R-12 | TASK-02 | 边界测试 | marquee.d.ts:248-253 |
| AC-4.5 | R-13 | TASK-02 | 单测 | marquee_pattern.cpp:957 |
| AC-4.6 | R-9 | TASK-02 | inspector 测试 | marquee_layout_property.h:96-97 |
| AC-5.1 | R-14 | TASK-02 | UI 测试 | marquee_model_ng.cpp:135 |
| AC-5.2 | R-15 | TASK-02 | 异常测试 | marquee_model_ng.cpp:135 |
| AC-5.3 | R-14 | TASK-02 | 资源测试 | marquee_model_ng.cpp:135 |
| AC-5.4 | R-16 | TASK-02 | 单测 | marquee_pattern.cpp:958-962 |
| AC-5.5 | R-17 | TASK-02 | 卡片测试 | marquee.d.ts:264-270 |
| AC-5.6 | R-9 | TASK-02 | inspector 测试 | marquee_layout_property.h:99-102 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 调用 `.fontColor(value)` 合法 ResourceColor | 存 MarqueeLayoutProperty::FontColor，文本以指定颜色渲染 | ACE_UPDATE_LAYOUT_PROPERTY | AC-1.1 |
| R-2 | 边界 | 未设置 fontColor | 运行时取 TextTheme GetTextColor() = font_primary @ 0.9 alpha | 普通 #182431 / 穿戴白色 | AC-1.2 |
| R-3 | 行为 | OnColorConfigurationUpdate 触发 | 覆盖为 MarqueeTheme::GetTextColor()（无 alpha）并 StopMarqueeAnimation 重启 | 颜色配置变更 | AC-1.3 |
| R-4 | 行为 | 调用 `.fontSize(value)` | 正数 number→fp；string→按单位；Resource→资源解析 | 不可百分比 | AC-2.1, AC-2.2, AC-2.3 |
| R-5 | 异常 | fontSize 为百分比 | 不支持，被忽略 | marquee_model_ng.cpp:116 | AC-2.4 |
| R-6 | 边界 | 未设置 fontSize | 运行时取 TextTheme 默认：普通 16.0fp / 穿戴 15.0fp | text_theme.cpp:34 | AC-2.5 |
| R-7 | 行为 | allowScale 设置 | true→fp 随系统字号缩放；false→固定值；写入 MarqueeLayoutProperty 与文本子节点 | 仅 fp 生效 | AC-3.1, AC-3.2, AC-3.4 |
| R-8 | 边界 | 未设置 allowScale | 默认 value_or(true) 启用缩放 | marquee_model_ng.cpp:99,101 | AC-3.3 |
| R-9 | 异常 | inspector 读取未设置的字体属性 | fontColor→BLACK；fontSize→10vp；allowScale→false | 与运行时默认不一致 | AC-1.4, AC-2.6, AC-3.6, AC-4.6, AC-5.6 |
| R-10 | 行为 | OnFontScaleConfigurationUpdate 且 allowScale=true | StopMarqueeAnimation(playStatus) 重启滚动适配新布局 | 系统字号变更 | AC-3.5 |
| R-11 | 行为 | `.fontWeight(value)` | number 100-900 步长 100；枚举映射；合法字符串解析 | 默认 Normal(400) | AC-4.1, AC-4.2, AC-4.3 |
| R-12 | 边界 | fontWeight 过大 | 按字体能力裁剪渲染 | SDK 注释 | AC-4.4 |
| R-13 | 边界 | 未设置 fontWeight | 默认 FontWeight::NORMAL (400) | marquee_pattern.cpp:957 | AC-4.5 |
| R-14 | 行为 | `.fontFamily(value)` | 有效字族名渲染；Resource 解析 | marquee_model_ng.cpp:135 | AC-5.1, AC-5.3 |
| R-15 | 异常 | 指定字族不存在 | 回退系统默认 HarmonyOS Sans | marquee_model_ng.cpp:135 | AC-5.2 |
| R-16 | 边界 | 未设置 fontFamily | 文本子节点字族 reset，使用 HarmonyOS Sans | marquee_pattern.cpp:958-962 | AC-5.4 |
| R-17 | 行为 | 卡片场景设置 fontFamily | 仅 HarmonyOS Sans 生效，其他忽略 | SDK 注释 marquee.d.ts:264-270 | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|----------|----------|
| VM-1 | AC-1.1, AC-1.2, AC-1.3 | UI 测试 + 主题测试 + 深色模式测试 | fontColor 默认值与颜色配置重启 |
| VM-2 | AC-1.4, AC-2.6, AC-3.6 | inspector 测试 | inspector 默认值不一致 |
| VM-3 | AC-2.1 ~ AC-2.5 | UI 测试 + 主题测试 | fontSize 单位与默认值 |
| VM-4 | AC-3.1 ~ AC-3.5 | 大字体测试 | allowScale 与系统字号缩放交互 |
| VM-5 | AC-4.1 ~ AC-4.6 | UI 测试 + 边界测试 | fontWeight 三态与裁剪 |
| VM-6 | AC-5.1 ~ AC-5.6 | UI 测试 + 卡片测试 | fontFamily 与卡片限制 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|----------|----------|---------|
| `.fontColor(value: ResourceColor)` (动态) | Public | ResourceColor | MarqueeAttribute | 无 | 字体颜色 | AC-1.1 |
| `.fontSize(value: Length)` (动态) | Public | Length | MarqueeAttribute | 无 | 字号 | AC-2.1 |
| `.allowScale(value: boolean)` (动态) | Public | boolean | MarqueeAttribute | 无 | 缩放开关 | AC-3.1 |
| `.fontWeight(value: number\|FontWeight\|string)` (动态) | Public | number\|FontWeight\|string | MarqueeAttribute | 无 | 字重 | AC-4.1 |
| `.fontFamily(value: string\|Resource)` (动态) | Public | string\|Resource | MarqueeAttribute | 无 | 字族 | AC-5.1 |
| 静态版同名属性 (静态, @since 23) | Public | 同上 | MarqueeAttribute | 无 | 静态版 | 全部 |

> API 签名、d.ts 位置见 design.md。SDK 声明 `api/@internal/component/ets/marquee.d.ts:202-293`（动态）、`api/arkui/component/marquee.static.d.ets`（静态）。

## 接口规格

### 接口定义

**fontColor / fontSize / allowScale / fontWeight / fontFamily**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontColor(value: ResourceColor): MarqueeAttribute` 等 5 个 |
| 返回值 | `MarqueeAttribute` — 属性链 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-5.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| fontColor | ResourceColor | 否 | TextTheme font_primary @ 0.9 | OnColorConfigurationUpdate 覆盖无 alpha |
| fontSize | Length | 否 | 16.0fp 普通 / 15.0fp 穿戴 | 不可百分比；number→fp |
| allowScale | boolean | 否 | true | 仅 fp 生效；写入文本子节点 |
| fontWeight | number\|FontWeight\|string | 否 | Normal(400) | number 100-900 步长 100 |
| fontFamily | string\|Resource | 否 | HarmonyOS Sans | 卡片仅 HarmonyOS Sans |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 未设置任何字体属性 | TextTheme 默认值（fontColor/fontSize/fontWeight） | AC-1.2, AC-2.5, AC-4.5 |
| 2 | allowScale=true 且系统字号变更 | 字号缩放并重启滚动 | AC-3.5 |
| 3 | 颜色配置变更 | OnColorConfigurationUpdate 覆盖为 MarqueeTheme 无 alpha 颜色 | AC-1.3 |
| 4 | 卡片场景 fontFamily | 仅 HarmonyOS Sans | AC-5.5 |

## 兼容性声明

- **已有 API 行为变更:** 是。fontColor/fontSize/allowScale 的 inspector 默认值（BLACK/10vp/false）与运行时默认值（font_primary/16fp/true）不一致（`marquee_layout_property.h:92-94` vs `marquee_pattern.cpp:955-963`）。规格以运行时行为为准。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8（动态版）；静态版需 API 23
- **API 版本号策略:** @since 标注。API 8 起 5 属性均支持；静态版 @since 23；静态双签名 @since 26.1

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 字体默认值来源 | NG pattern 从 TextTheme（非 MarqueeTheme）取默认 | AC-1.2, AC-2.5 |
| allowScale 双写 | 写入 MarqueeLayoutProperty 与文本子节点 TextLayoutProperty | AC-3.1, AC-3.4 |
| OnColorConfigurationUpdate 覆盖 | 覆盖为 MarqueeTheme 无 alpha 颜色并重启 | AC-1.3 |
| inspector 默认值不一致 | fontColor/fontSize/allowScale inspector 与运行时默认不同 | AC-1.4, AC-2.6, AC-3.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 字体属性变更触发 PROPERTY_UPDATE_MEASURE 重布局 | 性能测试 | marquee_layout_property.h:121-124 |
| 可靠性 | 系统字号变更 allowScale=true 时重启滚动 | 集成测试 | marquee_pattern.cpp:1227-1246 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | fontSize 默认 16.0fp，fontColor #182431 | — | 主题测试 | text_theme.cpp:34 |
| 穿戴 | fontSize 默认 15.0fp，fontColor 白色 | 主题差异 | 主题测试 | wearable/float.json:68, color.json:40 |
| 卡片 | fontFamily 仅 HarmonyOS Sans | 限制 | 卡片测试 | marquee.d.ts:264-270 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 文本内容随 fontColor/fontSize 可访问 | marquee_accessibility_property.cpp |
| 大字体 | 是 | allowScale 默认 true，fp 随系统字号缩放并重启 | AC-3.5 |
| 深色模式 | 是 | fontColor 默认 font_primary，深色切换走 OnColorConfigurationUpdate | AC-1.3 |
| 多窗口/分屏 | 否 | 无字体相关差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 静态版需 API 23 | SDK 声明 |
| 生态兼容 | 是 | Cangjie FFI 支持 fontColor/fontSize/allowScale/fontWeight/fontFamily | cj_marquee_ffi.h:27-31 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Marquee 字体默认值为何从 TextTheme 而非 MarqueeTheme 取，OnColorConfigurationUpdate 又覆盖为 MarqueeTheme 无 alpha 颜色"
  - repo: "openharmony/arkui_ace_engine"
    query: "Marquee allowScale 为何同时写入 MarqueeLayoutProperty 与文本子节点 TextLayoutProperty"
```

**关键文档：** design.md（`specs/05-ui-components/09-text-components/01-marquee/design.md`）；SDK 声明 `api/@internal/component/ets/marquee.d.ts:202-293`
