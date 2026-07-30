# 特性规格

> Func-05-09-03-Feat-04 自适应字号与文本描边着色：覆盖 minFontSize/maxFontSize、minFontScale/maxFontScale、strokeWidth/strokeColor/strokeJoinStyle、shaderStyle 共 8 个属性。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自适应字号与文本描边着色（Adaptive Font Size & Text Stroke/Shader） |
| 特性编号 | Func-05-09-03-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 12（minFontSize/maxFontSize）、API 18（minFontScale/maxFontScale）、API 20（strokeWidth/strokeColor）、API 26（strokeJoinStyle/shaderStyle） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 自适应字号规格 | 补录：minFontSize/maxFontSize(@since 12) |
| ADDED | 字体缩放范围规格 | 补录：minFontScale/maxFontScale(@since 18, crossplatform @since 20) |
| ADDED | 文本描边规格 | 补录：strokeWidth/strokeColor(@since 20)、strokeJoinStyle(@since 26) |
| ADDED | 文本着色器规格 | 补录：shaderStyle(@since 26) |

## 输入文档

- 设计文档：`design.md`（DESIGN-Func-05-09-03，Feat-04 增量合并）
- 源码定位：
  - 自适应字号：`search_model_ng.cpp:1938`(SetAdaptMinFontSize) `:1952`(SetAdaptMaxFontSize) → 子 TextFieldLayoutProperty
  - 字体缩放：`search_model_ng.cpp:1966`(SetMinFontScale) `:1978`(SetMaxFontScale) `:53`(MAX_FONT_SCALE=2.0)
  - 描边：`search_model_ng.cpp:2694`(SetStrokeWidth→SearchLayoutProperty:100) `:2707`(SetStrokeColor→SearchLayoutProperty:101) `:2768`(SetStrokeJoinStyle→子TextField)
  - 同步：`search_layout_algorithm.cpp:242-266`(UpdateFontFeature) `:254-265`(strokeColor 回退 text color)
  - 布局：`search_layout_algorithm.cpp:636-637`(CalculateMax/MinFontScale) `:54-84`
  - 静态：`search_model_static.cpp:447`(minFontScale clamp [0,1]) `:456`(maxFontScale max(1.0)) `:48`(MAX_FONT_SCALE=2.0)
  - SDK：`interface/sdk-js/api/@internal/component/ets/search.d.ts`

## 用户故事

### US-1: 自适应字号

**作为** 应用开发者,
**我想要** 设置文本框字号的自适应范围,
**以便** 文本在固定空间内自动适配显示。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 同时调用 `.minFontSize(12)` 和 `.maxFontSize(24)` THEN 子文本框 AdaptMinFontSize/AdaptMaxFontSize 设值 + HeightAdaptivePolicy=LAYOUT_CONSTRAINT_FIRST，触发 MEASURE | 正常 |
| AC-1.2 | WHEN 仅调用 `.minFontSize(12)` 不设 maxFontSize THEN 自适应不生效（须配对使用） | 边界 |
| AC-1.3 | WHEN minFontSize 或 maxFontSize ≤ 0 THEN 自适应不生效，使用 textFont.size 或默认 | 边界 |
| AC-1.4 | WHEN maxFontSize < minFontSize THEN 自适应不生效 | 边界 |
| AC-1.5 | WHEN 自适应生效 THEN fontSize 被忽略（自适应覆盖固定字号） | 正常 |

### US-2: 字体缩放范围

**作为** 应用开发者,
**我想要** 设置字体缩放的最小/最大比例,
**以便** 限制系统字体缩放的影响范围。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `.minFontScale(0.5)`（@since 18） THEN 子文本框 MinFontScale 设为 0.5（钳制到 [0,1]），触发 MEASURE | 正常 |
| AC-2.2 | WHEN 调用 `.maxFontScale(1.5)`（@since 18） THEN 子文本框 MaxFontScale 设为 1.5（下限 1.0，上限 2.0），触发 MEASURE | 正常 |
| AC-2.3 | WHEN minFontScale < 0 THEN 钳制为 0.0；> 1 THEN 钳制为 1.0 | 边界 |
| AC-2.4 | WHEN maxFontScale < 1 THEN 钳制为 1.0；> 2.0 THEN 钳制为 2.0（MAX_FONT_SCALE） | 边界 |
| AC-2.5 | WHEN 未设置 maxFontScale THEN 默认回退 pipeline->GetMaxAppFontScale() 钳制到 2.0 | 正常 |

### US-3: 文本描边

**作为** 应用开发者,
**我想要** 设置文本的描边宽度、颜色与连接样式,
**以便** 为搜索框文本添加描边视觉效果。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 `.strokeWidth(2)`（@since 20） THEN SearchLayoutProperty.StrokeWidth 设值(MEASURE)，默认 0（无描边） | 正常 |
| AC-3.2 | WHEN strokeWidth 单位为 px 且 < 0 THEN 实心文本；> 0 THEN 描边文本 | 边界 |
| AC-3.3 | WHEN 调用 `.strokeColor(Color.Red)`（@since 20） THEN SearchLayoutProperty.StrokeColor 设红色(MEASURE) | 正常 |
| AC-3.4 | WHEN 未设置 strokeColor THEN UpdateFontFeature 同步时回退到 text color（`search_layout_algorithm.cpp:261`） | 正常 |
| AC-3.5 | WHEN 调用 `.strokeJoinStyle(StrokeJoinStyle.ROUND)`（@since 26） THEN 子 TextFieldLayoutProperty.StrokeJoinStyle 设值 | 正常 |

### US-4: 文本着色器

**作为** 应用开发者,
**我想要** 设置文本的线性/径向渐变或颜色着色器,
**以便** 为搜索框文本应用线性/径向渐变着色。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 调用 `.shaderStyle(线性渐变)`（@since 26） THEN 子 TextFieldLayoutProperty.GradientShaderStyle 设值，先 reset ColorShaderStyle | 正常 |
| AC-4.2 | WHEN 调用 `.shaderStyle(径向渐变)` THEN GradientShaderStyle 设径向值 | 正常 |
| AC-4.3 | WHEN 调用 `.shaderStyle(颜色着色器)` THEN ColorShaderStyle 设值，先 reset GradientShaderStyle | 正常 |
| AC-4.4 | WHEN shaderStyle 传 undefined 或 Reset THEN 同时 reset GradientShaderStyle + ColorShaderStyle，触发 MEASURE_SELF | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-04 | UITest | search_model_ng.cpp:1938 SetAdaptMinFontSize |
| AC-1.2 | R-2 | TASK-04 | UITest | search.d.ts:993 须配对 |
| AC-1.3 | R-3 | TASK-04 | UITest | search.d.ts:998 ≤0 不生效 |
| AC-1.4 | R-3 | TASK-04 | UITest | search.d.ts:1021 max<min 不生效 |
| AC-1.5 | R-4 | TASK-04 | UITest | search.d.ts:996 fontSize 被忽略 |
| AC-2.1 | R-5 | TASK-04 | UITest | search_model_ng.cpp:1966 SetMinFontScale |
| AC-2.2 | R-5 | TASK-04 | UITest | search_model_ng.cpp:1978 SetMaxFontScale |
| AC-2.3 | R-6 | TASK-04 | UITest | search_model_static.cpp:447 clamp [0,1] |
| AC-2.4 | R-7 | TASK-04 | UITest | search_model_ng.cpp:1986 min(2.0) |
| AC-2.5 | R-8 | TASK-04 | UITest | search_layout_algorithm.cpp:66-68 |
| AC-3.1 | R-9 | TASK-04 | UITest | search_model_ng.cpp:2694 SetStrokeWidth→SearchLayoutProperty |
| AC-3.2 | R-10 | TASK-04 | UITest | search.d.ts:1415 px 语义 |
| AC-3.3 | R-11 | TASK-04 | UITest | search_model_ng.cpp:2707 SetStrokeColor |
| AC-3.4 | R-12 | TASK-04 | UITest | search_layout_algorithm.cpp:261 回退 text color |
| AC-3.5 | R-13 | TASK-04 | UITest | search_model_ng.cpp:2768 SetStrokeJoinStyle |
| AC-4.1 | R-14 | TASK-04 | UITest | search_model_ng.cpp:2797 SetGradientShaderStyle |
| AC-4.2 | R-14 | TASK-04 | UITest | 同上 |
| AC-4.3 | R-15 | TASK-04 | UITest | search_model_ng.cpp:2828 SetColorShaderStyle |
| AC-4.4 | R-16 | TASK-04 | UITest | search_model_ng.cpp:2840 ResetGradientShaderStyle |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|----------|----------|-----------|---------|
| R-1 | 行为 | minFontSize + maxFontSize 配对设置 | 子文本框 AdaptMinFontSize/AdaptMaxFontSize + HeightAdaptivePolicy=LAYOUT_CONSTRAINT_FIRST，触发 MEASURE | 须配对；存于子 TextFieldLayoutProperty | AC-1.1 |
| R-2 | 边界 | 仅设 minFontSize 或 maxFontSize 其一 | 自适应不生效 | SDK 约束：须配合使用 | AC-1.2 |
| R-3 | 边界 | minFontSize 或 maxFontSize ≤0，或 max < min | 自适应不生效，使用 textFont.size 或默认 | — | AC-1.3, AC-1.4 |
| R-4 | 行为 | 自适应生效时 | fontSize 被忽略 | 自适应覆盖固定字号 | AC-1.5 |
| R-5 | 行为 | minFontScale/maxFontScale 设置 | 子文本框 MinFontScale/MaxFontScale 设值，触发 MEASURE | minFontScale 钳[0,1]；maxFontScale 钳[1,2.0] | AC-2.1, AC-2.2 |
| R-6 | 边界 | minFontScale < 0 或 > 1 | 钳制为 0.0 或 1.0 | search_model_static.cpp:447 | AC-2.3 |
| R-7 | 边界 | maxFontScale < 1 或 > 2.0 | 钳制为 1.0 或 2.0（MAX_FONT_SCALE） | search_model_ng.cpp:1986 | AC-2.4 |
| R-8 | 行为 | 未设 maxFontScale | 回退 pipeline->GetMaxAppFontScale() 钳制到 2.0 | CalculateMaxFontScale | AC-2.5 |
| R-9 | 行为 | strokeWidth 设置 | SearchLayoutProperty.StrokeWidth 设值(MEASURE)，默认 0 | 存于 SearchLayoutProperty（非子节点） | AC-3.1 |
| R-10 | 边界 | strokeWidth 单位 px < 0 | 实心文本；> 0 描边文本 | SDK 语义 | AC-3.2 |
| R-11 | 行为 | strokeColor 设置 | SearchLayoutProperty.StrokeColor 设值(MEASURE) | 存于 SearchLayoutProperty | AC-3.3 |
| R-12 | 行为 | 未设 strokeColor | UpdateFontFeature 同步时回退到 text color | search_layout_algorithm.cpp:261 | AC-3.4 |
| R-13 | 行为 | strokeJoinStyle 设置（@since 26） | 子 TextFieldLayoutProperty.StrokeJoinStyle 设值 | 存于子节点（非 Search） | AC-3.5 |
| R-14 | 行为 | shaderStyle 设渐变（@since 26） | 子 TextFieldLayoutProperty.GradientShaderStyle 设值，先 reset ColorShaderStyle | 渐变与颜色互斥 | AC-4.1, AC-4.2 |
| R-15 | 行为 | shaderStyle 设颜色 | ColorShaderStyle 设值，先 reset GradientShaderStyle | 渐变与颜色互斥 | AC-4.3 |
| R-16 | 行为 | shaderStyle undefined/Reset | 同时 reset GradientShaderStyle + ColorShaderStyle，触发 MEASURE_SELF | — | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | US-1 自适应字号 | UITest | 验证配对约束；≤0/max<min 不生效；fontSize 被忽略 |
| VM-2 | US-2 字体缩放范围 | UITest | 验证 minFontScale [0,1] / maxFontScale [1,2.0] 钳制；默认回退 |
| VM-3 | US-3 文本描边 | UITest | 验证 strokeWidth/strokeColor 存于 SearchLayoutProperty；strokeColor 回退 text color；px 语义 |
| VM-4 | US-4 文本着色器 | UITest | 验证渐变/颜色互斥；Reset 清两者 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `minFontSize(value: number\|string\|Resource)` | Public | Dimension(fp) | SearchAttribute | 无 | 最小自适应字号 | AC-1.1..AC-1.5 |
| `maxFontSize(value: number\|string\|Resource)` | Public | Dimension(fp) | SearchAttribute | 无 | 最大自适应字号 | AC-1.1..AC-1.5 |
| `minFontScale(scale: Optional<number\|Resource>)` | Public | scale [0,1] | SearchAttribute | 无 | 最小字体缩放 | AC-2.1..AC-2.5 |
| `maxFontScale(scale: Optional<number\|Resource>)` | Public | scale [1,+∞) | SearchAttribute | 无 | 最大字体缩放 | AC-2.1..AC-2.5 |
| `strokeWidth(width: Optional<LengthMetrics>)` | Public | LengthMetrics | SearchAttribute | 无 | 描边宽度 | AC-3.1, AC-3.2 |
| `strokeColor(color: Optional<ResourceColor>)` | Public | ResourceColor | SearchAttribute | 无 | 描边颜色 | AC-3.3, AC-3.4 |
| `strokeJoinStyle(strokeJoinStyle: StrokeJoinStyle\|undefined)` | Public | StrokeJoinStyle | SearchAttribute | 无 | 描边连接样式 | AC-3.5 |
| `shaderStyle(shader: ShaderStyle\|undefined)` | Public | ShaderStyle | SearchAttribute | 无 | 文本着色器 | AC-4.1..AC-4.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 8 属性跨版本引入 | 变更 | @since 12/18/20/26 分批 | 低版本不支持 | 全部 AC |

## 接口规格

> L1+ 复杂度。以下仅列代表性接口。

### 接口定义

**strokeWidth(width: Optional<LengthMetrics>)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `strokeWidth(width: Optional<LengthMetrics>): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| width | LengthMetrics | 否 | 0（无描边） | px<0 实心；>0 描边；存于 SearchLayoutProperty(MEASURE) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设正值 | SearchLayoutProperty.StrokeWidth | AC-3.1 |
| 2 | px<0 | 实心文本 | AC-3.2 |
| 3 | px>0 | 描边文本 | AC-3.2 |
| 4 | 未设 | 默认 0 无描边 | AC-3.1 |

---

**strokeColor(color: Optional<ResourceColor>)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `strokeColor(color: Optional<ResourceColor>): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.3, AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| color | ResourceColor | 否 | 回退 text color | UpdateFontFeature 同步时回退 |

## 兼容性声明

- **已有 API 行为变更:** 是。8 属性跨 API 12-26 引入；minFontSize/maxFontSize 须配对且 ≤0/max<min 不生效；maxFontScale 硬钳制到 2.0（MAX_FONT_SCALE）；strokeColor 未设时回退 text color；shaderStyle 渐变与颜色互斥。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12（minFontSize/maxFontSize）
- **API 版本号策略:** @since 12/18/20/26 分批标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 存储分裂 | 8 属性中仅 strokeWidth/strokeColor 存于 SearchLayoutProperty(MEASURE)，其余 6 个存于子 TextFieldLayoutProperty | AC-3.1..AC-4.4 |
| strokeColor 回退 text color | UpdateFontFeature 同步时 strokeColor 未设则回退 text color（`search_layout_algorithm.cpp:261`） | AC-3.4 |
| fontScale 钳制 | minFontScale 钳[0,1]（static:447）；maxFontScale 钳[1,2.0]（ng:1986, static:456, MAX_FONT_SCALE=2.0） | AC-2.3, AC-2.4 |
| 自适应字号配对 | minFontSize/maxFontSize 须配对；单独不生效；≤0/max<min 不生效 | AC-1.2..AC-1.4 |
| shaderStyle 互斥 | 渐变与颜色着色器互斥（设一个先 reset 另一个） | AC-4.1..AC-4.4 |
| shaderStyle C-API 拆分 | C-API 拆为 5 字段（linearGradient/radialGradient/resetGradient/colorShaderColor/resetColorShaderColor） | AC-4.1..AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | fontScale 变更触发 MEASURE，参与 ConvertToPxDistributeWithEnv 影响图标/按钮/行高 | UITest | search_layout_algorithm.cpp:636-637 |
| 内存 | strokeWidth/strokeColor 存于 SearchLayoutProperty，经 UpdateFontFeature 同步至子 TextField | 内存分析 | search_layout_algorithm.cpp:254-265 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | maxFontScale 默认回退 pipeline->GetMaxAppFontScale() | — | UITest | search_layout_algorithm.cpp:68 |
| 平板/折叠屏 | 同手机 | 无差异 | UITest | — |
| 穿戴 | 同手机 | 无差异 | UITest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不影响无障碍 | — |
| 大字体 | 是 | minFontScale/maxFontScale 控制字体缩放范围；与适老化直接相关 | AC-2.1..AC-2.5 |
| 深色模式 | 是 | strokeColor 未设时回退 text color，深色模式随 text color 更新 | AC-3.4 |
| 多窗口/分屏 | 否 | 无特殊行为 | — |
| 多用户 | 否 | 无特殊行为 | — |
| 版本升级 | 是 | 8 属性跨 API 12-26 引入 | 全部 AC |
| 生态兼容 | 是 | 动态+静态+C-API 全覆盖；shaderStyle C-API 拆 5 字段 | 全部 AC |

## 行为场景（Gherkin）

```gherkin
Feature: Search 自适应字号与文本描边着色
  作为应用开发者
  我想要配置字号自适应范围与文本描边/着色器
  以便适配不同屏幕与视觉风格

  Scenario Outline: 自适应字号配对约束
    Given Search 组件已创建
    When 调用 minFontSize(<min>) 和 maxFontSize(<max>)
    Then 自适应 <result>

    Examples:
      | min | max | result |
      | 12 | 24 | 生效 |
      | 12 | (未设) | 不生效 |
      | (未设) | 24 | 不生效 |
      | 0 | 24 | 不生效 |
      | 24 | 12 | 不生效 |

  Scenario Outline: fontScale 钳制
    Given Search 组件已创建
    When 调用 <api>(<input>)
    Then 实际值为 <clamped>

    Examples:
      | api | input | clamped |
      | minFontScale | -0.5 | 0.0 |
      | minFontScale | 0.5 | 0.5 |
      | minFontScale | 1.5 | 1.0 |
      | maxFontScale | 0.5 | 1.0 |
      | maxFontScale | 1.5 | 1.5 |
      | maxFontScale | 3.0 | 2.0 |

  Scenario: strokeColor 回退 text color
    Given Search 组件已创建且 fontColor 为红色
    When 调用 strokeWidth(2) 但未设 strokeColor
    Then UpdateFontFeature 同步时 strokeColor 回退为红色（text color）

  Scenario: shaderStyle 渐变与颜色互斥
    Given Search 组件已创建且已设渐变着色器
    When 调用 shaderStyle(颜色着色器)
    Then GradientShaderStyle 被 reset
    And ColorShaderStyle 设为新值
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
    query: "strokeWidth/strokeColor 存于 SearchLayoutProperty 而其余 6 个描边/着色器属性存于子 TextFieldLayoutProperty 的存储分裂"
  - repo: "openharmony/arkui_ace_engine"
    query: "UpdateFontFeature 同步 strokeColor 未设时回退 text color 的逻辑"
  - repo: "openharmony/arkui_ace_engine"
    query: "minFontScale 钳[0,1] / maxFontScale 钳[1,2.0] (MAX_FONT_SCALE) 的双重钳制"
  - repo: "openharmony/arkui_ace_engine"
    query: "minFontSize/maxFontSize 配对约束与 ≤0/max<min 不生效语义"
  - repo: "openharmony/interface_sdk-js"
    query: "search.d.ts 中 8 个自适应/描边/着色器属性的 @since 与约束"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/search.d.ts`；`frameworks/core/components_ng/pattern/search/search_model_ng.cpp`；`search_layout_algorithm.cpp`；`design.md`(DESIGN-Func-05-09-03)
