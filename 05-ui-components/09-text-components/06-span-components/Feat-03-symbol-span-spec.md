# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SymbolSpan 符号片段组件 |
| 特性编号 | Func-05-09-06-Feat-03 |
| 所属 Epic | Span 类组件规格补录 |
| 优先级 | P1 |
| 目标版本 | API 11（dynamic 基线）至 API 26（static 增强） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | SymbolSpan 创建与符号资源规格 | 覆盖 `SymbolSpan(value: Resource)` 构造，走 ArkTS-native SymbolSpanBridge + TS(arksymbolspan.ts)，复用 SpanNode(spanItemType=SYMBOL)，dynamic @since 11 / static @since 23 |
| ADDED | SymbolSpan 符号属性规格（fontSize/fontColor/fontWeight/effectStrategy/renderingStrategy） | 覆盖 SymbolStyle 五属性，逐 API 标注 @since |
| ADDED | SymbolSpan 事件与 NDK 缺失声明 | 覆盖"无通用事件支持"与"无独立 NDK 节点类型"契约 |

## 输入文档

| 类型 | 路径 |
|------|------|
| 设计文档 | `05-ui-components/09-text-components/06-span-components/design.md`（详细设计 `### SymbolSpan 符号片段（Feat-03）`） |
| SDK dynamic | `interface/sdk-js/api/@internal/component/ets/symbol_span.d.ts` |
| SDK static | `interface/sdk-js/api/arkui/component/symbolSpan.static.d.ets` |
| Modifier dynamic | `interface/sdk-js/api/arkui/SymbolSpanModifier.d.ts` |
| Modifier static | `interface/sdk-js/api/arkui/SymbolSpanModifier.static.d.ets` |
| 节点实现 | `frameworks/core/components_ng/pattern/text/span_node.h:889`（SpanNode，spanItemType=SYMBOL）、`:949`（spanItem_->spanItemType = SpanItemType::SYMBOL）、`:388`（SpanItem，持有 SymbolStyle unique_ptr）、`text_styles.h:315`（SymbolStyle） |
| Model 实现 | `frameworks/core/components_ng/pattern/text/span/symbol_span_model.h:32`（SymbolSpanModel）、`symbol_span_model_ng.h:25`（SymbolSpanModelNG）、`symbol_span_model_static.h`（SymbolSpanModelStatic） |
| Bridge 实现 | `frameworks/bridge/declarative_frontend/ark_direct_component/src/arksymbolspan.ts`（JSSymbolSpan，调用 `getUINativeModule().symbolSpan.*`） |
| ArkTS-native Bridge | `frameworks/core/components_ng/pattern/text/span/bridge/symbol_span/arkts_native_symbol_span_bridge.cpp`（SymbolSpanBridge::JsCreate/SetFontColor/SetFontSize/SetFontWeight/SetEffectStrategy/SetRenderingStrategy/SetId） |
| 符号 pattern（同族非 span） | `frameworks/core/components_ng/pattern/symbol/`（SymbolModel/SymbolEffectOptions/SymbolSourceInfo/SymbolType，被 SymbolStyle 复用） |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 插入符号片段

**作为** 应用开发者,
**我想要** 在 `Text` 组件下使用 `SymbolSpan` 子组件声明一个符号字形（symbol glyph）,
**以便** 文本行内可混合符号资源。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 开发者在 `Text` 下声明 `SymbolSpan($r('app.symbol.ohos_wifi'))` THEN 经 `arksymbolspan.ts` JSSymbolSpan → `getUINativeModule().symbolSpan.jsCreate` → C++ `SymbolSpanBridge::JsCreate` → `SymbolSpanModelNG::Create(unicode)`（`symbol_span_model_ng.h:27`）构造 `SpanNode`（tag `V2::SPAN_ETS_TAG`）并设 `spanItem_->spanItemType = SpanItemType::SYMBOL`（`span_node.h:949`），填充 `SymbolStyle` | 正常 |
| AC-1.2 | WHEN 传入的 Resource 不是合法符号资源 THEN 符号无法解析，片段不渲染符号（不崩溃） | 异常 |
| AC-1.3 | WHEN `SymbolSpan` 未挂在 Text/RichEditor 下 THEN 无父级 Paragraph 管线消费，不渲染 | 边界 |

### US-2: 设置字号、颜色与字重

**作为** 应用开发者,
**我想要** 通过 fontSize/fontColor/fontWeight 设置符号片段的字号、颜色列表与字重,
**以便** 符号片段可按设计规格呈现。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `.fontSize(24)` 或 `.fontSize('24vp')` 或 `.fontSize($r('app.size.f24'))` THEN `SymbolSpanModelNG::SetFontSize`（`symbol_span_model_ng.h:29`）写入 SymbolStyle 符号字号，重排后符号尺寸改变 | 正常 |
| AC-2.2 | WHEN 调用 `.fontColor([Color.Red, Color.Blue])`（Array<ResourceColor>） THEN `SymbolSpanModelNG::SetFontColor`（`:31`）写入符号颜色列表，符号按策略着色 | 正常 |
| AC-2.3 | WHEN 调用 `.fontWeight(FontWeight.Bold)` 或 `.fontWeight(700)` THEN `SymbolSpanModelNG::SetFontWeight`（`:30`）写入字重；API 26+ 可传 ResourceStr+fontWeightConfigs 重载 | 正常 |
| AC-2.4 | WHEN `fontColor` 数组长度与渲染策略所需颜色数不匹配 THEN 按 renderingStrategy 默认规则取色（多余忽略/不足补默认） | 边界 |

### US-3: 控制渲染与动效策略

**作为** 应用开发者,
**我想要** 通过 renderingStrategy/effectStrategy 控制符号的多层渲染策略与动效策略,
**以便** 符号可呈现单层/多层效果与动效播放。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 `.renderingStrategy(SymbolRenderingStrategy.SINGLE)` THEN `SymbolSpanModelNG::SetSymbolRenderingStrategy`（`symbol_span_model_ng.h:32`）写入渲染策略，符号按单层/多层策略渲染 | 正常 |
| AC-3.2 | WHEN 调用 `.effectStrategy(SymbolEffectStrategy.PULSE)` THEN `SymbolSpanModelNG::SetSymbolEffect`（`:33`）写入动效策略，符号按动效策略播放 | 正常 |
| AC-3.3 | WHEN 未设置 renderingStrategy/effectStrategy THEN 符号按默认策略渲染，无动效 | 边界 |

### US-4: 确认不支持通用事件

**作为** 应用开发者,
**我想要** 了解 SymbolSpan 不支持任何通用事件（onClick/onHover/onTouch 等）,
**以便** 不在 SymbolSpan 上注册无效事件回调。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 对 SymbolSpan 调用 `.onClick()`/`.onHover()`/`.onTouch()` 等通用事件 THEN 不支持，不产生回调（dynamic/static 文档明确"通用事件不支持"） | 异常 |
| AC-4.2 | WHEN 对 SymbolSpan 调用 `.attributeModifier(modifier)`（API 12 dynamic / 23 static） THEN 仅 SymbolSpanAttribute 声明的 fontSize/fontColor/fontWeight/effectStrategy/renderingStrategy 经 modifier 下发 | 正常 |

### US-5: 确认无独立 NDK 节点类型

**作为** 应用开发者,
**我想要** 了解 SymbolSpan 无独立 NDK 节点类型,
**以便** C-API 场景下经 styled-string 或 ArkTS 组件使用符号片段。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN NDK 枚举查找 `ARKUI_NODE_SYMBOL_SPAN` THEN 不存在该枚举值（仅 Span/ImageSpan/CustomSpan 有 NDK 节点类型） | 边界 |
| AC-5.2 | WHEN NDK 场景需符号片段 THEN 经 styled-string（ArkUI_SpanItem/ArkUI_StyledString，归属 FuncID 05-09-10）或 ArkTS 组件暴露 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-03 | XTS + 节点校验 | symbol_span_model_ng.h:27, span_node.h:949 |
| AC-1.2 | R-2 | TASK-03 | 负向用例（非法符号资源） | SymbolSourceInfo 解析 |
| AC-1.3 | R-3 | TASK-03 | 负向用例（无父 Text） | multiple_paragraph_layout_algorithm.h:40 |
| AC-2.1 | R-4 | TASK-03 | XTS fontSize 用例 | symbol_span_model_ng.h:29 |
| AC-2.2 | R-5 | TASK-03 | XTS fontColor 用例 | symbol_span_model_ng.h:31 |
| AC-2.3 | R-6 | TASK-03 | XTS fontWeight/26 overload | symbol_span_model_ng.h:30 |
| AC-3.1 | R-7 | TASK-03 | XTS renderingStrategy | symbol_span_model_ng.h:32 |
| AC-3.2 | R-8 | TASK-03 | XTS effectStrategy | symbol_span_model_ng.h:33 |
| AC-4.1 | R-9 | TASK-03 | 负向用例（onClick 无效） | symbol_span.d.ts 文档注释 |
| AC-5.1 | R-10 | TASK-03 | NDK 枚举缺失校验 | native_node.h 无 ARKUI_NODE_SYMBOL_SPAN |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 在 Text 下声明 `SymbolSpan(value: Resource)` | 经 arksymbolspan.ts → SymbolSpanBridge::JsCreate → SymbolSpanModelNG::Create(unicode) 构造 SpanNode，spanItemType=SYMBOL，填充 SymbolStyle | value 为符号 Resource | AC-1.1 |
| R-2 | 异常 | 传入非合法符号 Resource | 符号无法解析，片段不渲染符号，不崩溃 | SymbolSourceInfo 解析失败静默 | AC-1.2 |
| R-3 | 边界 | SymbolSpan 未挂 Text/RichEditor | 不渲染（无父级 Paragraph 管线） | span 不可独立布局 | AC-1.3 |
| R-4 | 行为 | 调用 `.fontSize(number\|string\|Resource)` | SymbolSpanModelNG::SetFontSize 写入 SymbolStyle 符号字号 | 负数/0 按 0 处理 | AC-2.1 |
| R-5 | 行为 | 调用 `.fontColor(Array<ResourceColor>)` | SymbolSpanModelNG::SetFontColor 写入符号颜色列表 | 数组长度与 renderingStrategy 不匹配按默认取色 | AC-2.2/2.4 |
| R-6 | 行为 | 调用 `.fontWeight(number\|FontWeight\|string)` 或 API 26 `fontWeight(number\|FontWeight\|ResourceStr, fontWeightConfigs)` | SymbolSpanModelNG::SetFontWeight 写入字重 | API 26 增 ResourceStr+fontWeightConfigs 重载 | AC-2.3 |
| R-7 | 行为 | 调用 `.renderingStrategy(SymbolRenderingStrategy)` | SymbolSpanModelNG::SetSymbolRenderingStrategy 写入渲染策略 | 默认单层 | AC-3.1/3.3 |
| R-8 | 行为 | 调用 `.effectStrategy(SymbolEffectStrategy)` | SymbolSpanModelNG::SetSymbolEffect 写入动效策略 | 默认无动效 | AC-3.2/3.3 |
| R-9 | 异常 | 对 SymbolSpan 调用 onClick/onHover/onTouch 等通用事件 | 不支持，不产生回调 | dynamic/static 文档明确通用事件不支持 | AC-4.1 |
| R-10 | 边界 | NDK 查找 ARKUI_NODE_SYMBOL_SPAN | 不存在该枚举；SymbolSpan 仅经 ArkTS 组件或 styled-string 暴露 | NDK 通道不覆盖 SymbolSpan | AC-5.1/5.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 SymbolSpan 创建 | XTS：声明 SymbolSpan 后检查 spanItemType=SYMBOL | span_node.h:949 |
| VM-2 | AC-1.2 非法符号资源 | 负向用例：非法 Resource 不崩溃 | SymbolSourceInfo |
| VM-3 | AC-1.3 无父级不渲染 | 负向用例：SymbolSpan 挂 Column 不显示 | 无 Paragraph 消费 |
| VM-4 | AC-2.1~2.4 fontSize/fontColor/fontWeight | XTS：逐属性截图比对 | SymbolSpanModelNG Set 方法 |
| VM-5 | AC-3.1~3.3 renderingStrategy/effectStrategy | XTS：渲染/动效策略 | symbol_span_model_ng.h:32/33 |
| VM-6 | AC-4.1 通用事件不支持 | 负向用例：onClick 无回调 | 文档注释契约 |
| VM-7 | AC-5.1 NDK 节点类型缺失 | 枚举查找：无 ARKUI_NODE_SYMBOL_SPAN | native_node.h |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|--------|
| `SymbolSpan(value: Resource)` dynamic @since 11 / static @since 23 | Public | 符号资源 | SymbolSpanAttribute | N/A | 创建符号片段 | AC-1.1 |
| `SymbolSpanAttribute.fontSize(number\|string\|Resource)` @since 11 | Public | 字号 | SymbolSpanAttribute | N/A | 设符号字号 | AC-2.1 |
| `SymbolSpanAttribute.fontColor(Array<ResourceColor>)` @since 11 | Public | 颜色列表 | SymbolSpanAttribute | N/A | 设符号颜色 | AC-2.2 |
| `SymbolSpanAttribute.fontWeight(number\|FontWeight\|string)` @since 11 / `fontWeight(number\|FontWeight\|ResourceStr, fontWeightConfigs)` @since 26 | Public | 字重 | SymbolSpanAttribute | N/A | 设符号字重 | AC-2.3 |
| `SymbolSpanAttribute.effectStrategy(SymbolEffectStrategy)` @since 11 | Public | 动效策略 | SymbolSpanAttribute | N/A | 设动效 | AC-3.2 |
| `SymbolSpanAttribute.renderingStrategy(SymbolRenderingStrategy)` @since 11 | Public | 渲染策略 | SymbolSpanAttribute | N/A | 设渲染策略 | AC-3.1 |
| `SymbolSpanAttribute.attributeModifier(AttributeModifier<SymbolSpanAttribute>)` @since 12 dynamic / 23 static | Public | modifier | SymbolSpanAttribute | N/A | 挂载动态属性 | AC-4.2 |
| `class SymbolSpanModifier extends SymbolSpanAttribute implements AttributeModifier<SymbolSpanAttribute>` @since 12 dynamic / 23 static（constructor `SymbolSpanModifier(src?: Resource)`） | Public | — | SymbolSpanModifier | N/A | 动态属性载体（带可选符号源构造） | AC-4.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `SymbolSpanAttribute.fontWeight` overload | 变更 | API 26 增 ResourceStr+fontWeightConfigs 重载 | 旧 number/FontWeight/string 调用兼容 | AC-2.3 |
| `SymbolSpanAttribute.fontColor` crossplatform | 变更 | API 20 dynamic 增 @crossplatform 标记 | 跨平台场景需 API 20+ | AC-2.2 |

## 接口规格

### 接口定义

**SymbolSpan 构造**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SymbolSpan(value: Resource): SymbolSpanAttribute`（dynamic @since 11 / static @since 23，@ComponentBuilder） |
| 返回值 | `SymbolSpanAttribute`（dynamic extends CommonMethod；static 独立 interface 不继承 CommonMethod） |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | Resource | 是 | 无 | 须为合法符号资源；非法时不渲染不崩溃 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 在 Text 下声明 SymbolSpan($r) | 构造 SpanNode(spanItemType=SYMBOL)，填充 SymbolStyle | AC-1.1 |
| 2 | 传入非合法符号资源 | 不渲染符号，不崩溃 | AC-1.2 |
| 3 | 未挂 Text/RichEditor | 不渲染 | AC-1.3 |

> fontSize/fontColor/fontWeight/effectStrategy/renderingStrategy 接口规格结构同 Span Feat-01 范式，参数约束与行为场景见规则定义 R-4~R-8。

## 兼容性声明

- **已有 API 行为变更:** 是。`fontWeight` API 26 增 ResourceStr+fontWeightConfigs 重载；`fontColor` API 20 dynamic 增 @crossplatform 标记。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 11（dynamic）/ API 23（static）
- **API 版本号策略:** 逐 API 标注 `@since`；dynamic 与 static 双态分别标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SymbolSpan 复用 SpanNode(SYMBOL 类型) | 不存在独立 SymbolSpanNode；走 SymbolSpanModelNG::Create 构造 SpanNode 并设 spanItemType | AC-1.1 |
| SymbolSpan 必须挂载于 Text/RichEditor | 复用父级 Paragraph 管线 | AC-1.3 |
| 无通用事件支持 | onClick/onHover/onTouch 等均不支持（dynamic/static 文档明确） | AC-4.1 |
| 无独立 NDK 节点类型 | NDK 通道不覆盖；仅经 ArkTS 组件或 styled-string 暴露 | AC-5.1 |
| static SymbolSpanAttribute 不继承 CommonMethod | static 模式无通用属性/事件继承 | AC-4.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 符号资源解析+渲染耗时 ≤ 同等 SymbolGlyph | 帧率/trace | SymbolSpanModelNG 复用 symbol pattern |
| 内存 | SymbolStyle unique_ptr 懒初始化 | 内存 profile | span_node.h symbolStyle unique_ptr |
| 可靠性 | 非法符号资源不崩溃 | 异常用例 | SymbolSourceInfo 解析 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | 符号自适应由父级处理 | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 符号片段经父级 Text 暴露无障碍语义 | 父级 Text accessibility |
| 大字体 | 是 | fontSize 经系统字体缩放 | SymbolStyle FontSizeScale |
| 深色模式 | 是 | fontColor 支持主题资源 | Array<ResourceColor> |
| 多窗口/分屏 | 否 | 符号片段行为随父级 Text | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | API 11→26 多版本演进 | 兼容性声明 |
| 生态兼容 | 是 | dynamic/static 双态并存；@crossplatform @since 20 | static @since 23 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: SymbolSpan 符号片段
  作为 ArkUI 应用开发者
  我想要 在 Text 中插入符号字形片段
  以便 文本行内混合符号资源

  Scenario: 在 Text 下创建 SymbolSpan
    Given Text 组件已挂载
    When 开发者声明 SymbolSpan($r('app.symbol.wifi'))
    Then 经 arksymbolspan.ts → SymbolSpanBridge::JsCreate → SymbolSpanModelNG::Create
    And 构造 SpanNode，spanItemType=SYMBOL
    And 填充 SymbolStyle

  Scenario: 传入非合法符号资源
    Given Text 组件已挂载
    When 开发者声明 SymbolSpan($r('app.string.not_symbol'))
    Then 符号无法解析
    And 片段不渲染符号，不崩溃

  Scenario Outline: SymbolSpan 符号属性
    Given SymbolSpan 已创建
    When 调用 <方法>(<参数>)
    Then SymbolSpanModelNG::Set<方法> 写入
    And 符号按 <效果> 呈现

    Examples:
      | 方法 | 参数 | 效果 |
      | fontSize | 24 | 符号尺寸改变 |
      | fontColor | [Red,Blue] | 符号按颜色列表着色 |
      | renderingStrategy | SINGLE | 单层渲染 |
      | effectStrategy | PULSE | 脉冲动效 |

  Scenario: 通用事件不支持
    Given SymbolSpan 已创建
    When 对 SymbolSpan 调用 onClick(callback)
    Then 不支持，不产生回调
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
    query: "SymbolSpanModelNG::Create 如何构造 SpanNode 并设 spanItemType=SYMBOL 与填充 SymbolStyle"
  - repo: "openharmony/arkui_ace_engine"
    query: "SymbolSpanBridge ArkTS-native 属性注册（JsCreate/SetFontColor/SetFontSize 等）与动态模块加载"
  - repo: "openharmony/arkui_ace_engine"
    query: "arksymbolspan.ts JSSymbolSpan 如何调用 getUINativeModule().symbolSpan.* 下发属性"
  - repo: "openharmony/interface_sdk-js"
    query: "symbol_span.d.ts 与 symbolSpan.static.d.ets 的 dynamic/static 差异与通用事件不支持声明"
  - repo: "openharmony/arkui_ace_engine"
    query: "SymbolSpanModifier 如何经 constructor(src?: Resource) 与 applyNormalAttribute 下发符号属性"
```

**关键文档：** design.md；SDK `symbol_span.d.ts`/`symbolSpan.static.d.ets`；`SymbolSpanModifier.d.ts`
