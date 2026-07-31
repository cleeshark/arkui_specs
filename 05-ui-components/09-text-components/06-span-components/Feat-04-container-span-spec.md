# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ContainerSpan 容器片段组件 |
| 特性编号 | Func-05-09-06-Feat-04 |
| 所属 Epic | Span 类组件规格补录 |
| 优先级 | P2 |
| 目标版本 | API 11（dynamic 基线）至 API 23（static） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ContainerSpan 创建与嵌套模型规格 | 覆盖 `ContainerSpan(content_?: CustomBuilder)` 构造，经 JSContainerSpan → SpanModelNG::CreateContainSpan 构造 ContainerSpanNode（UINode+BaseSpan，非原子），dynamic @since 11 / static @since 23 |
| ADDED | ContainerSpan 背景属性规格 | 覆盖 textBackgroundStyle（唯一属性，继承 TextBackgroundStyle 定义） |
| ADDED | ContainerSpan 事件与 NDK 缺失声明 | 覆盖"无通用事件支持"与"无独立 NDK 节点类型"契约 |

## 输入文档

| 类型 | 路径 |
|------|------|
| 设计文档 | `05-ui-components/09-text-components/06-span-components/design.md`（详细设计 `### ContainerSpan 容器片段（Feat-04）`） |
| SDK dynamic | `interface/sdk-js/api/@internal/component/ets/container_span.d.ts` |
| SDK static | `interface/sdk-js/api/arkui/component/containerSpan.static.d.ets` |
| Modifier dynamic | `interface/sdk-js/api/arkui/ContainerSpanModifier.d.ts` |
| Modifier static | `interface/sdk-js/api/arkui/ContainerSpanModifier.static.d.ets` |
| 节点实现 | `frameworks/core/components_ng/pattern/text/span_node.h:1515`（ContainerSpanNode : UINode, BaseSpan，tag `V2::CONTAINER_SPAN_ETS_TAG`，非原子）、`:772`（BaseSpan，持有 TextBackgroundStyle） |
| Model 实现 | `frameworks/core/components_ng/pattern/text/span_model.h:72`（SpanModel::CreateContainSpan）、`span_model_ng.h:115`（SpanModelNG::CreateContainSpan）、`span_model_ng.h:116/117/118`（SetTextBackgroundStyle） |
| Bridge 实现 | `frameworks/bridge/declarative_frontend/jsview/js_container_span.h:28`（JSContainerSpan : JSContainerBase）、`js_container_span.cpp:26`（ParseTextBackgroundStyle+SetTextBackgroundStyle） |
| 背景定义 | `interface/sdk-js/api/@internal/component/ets/span.d.ts`（TextBackgroundStyle: color+radius，@since 11 dynamic） |
| C-API 实现 | `frameworks/core/interfaces/native/implementation/container_span_modifier.cpp`（GeneratedModifier::ContainerSpanModifier，ConstructImpl → SpanModelStatic::CreateContainerSpanNode） |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 插入容器片段分组子 span

**作为** 应用开发者,
**我想要** 在 `Text` 组件下使用 `ContainerSpan` 包裹多个子 Span/ImageSpan/SymbolSpan,
**以便** 同一容器内的子片段可共享背景样式并作为逻辑分组。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 开发者在 `Text` 下声明 `ContainerSpan(() => { Span('a'); Span('b') })` THEN 经 `JSContainerSpan::Create` → `SpanModel::GetInstance()->CreateContainSpan()` → `SpanModelNG::CreateContainSpan()`（`span_model_ng.h:115`）构造 `ContainerSpanNode`（`span_node.h:1515`，tag `V2::CONTAINER_SPAN_ETS_TAG`，继承 UINode+BaseSpan），非原子（可持有子 span），挂载为 Text 子节点 | 正常 |
| AC-1.2 | WHEN ContainerSpan 内声明多个子 Span/ImageSpan/SymbolSpan THEN 子片段作为 ContainerSpanNode 的子节点挂载，ContainerSpan 作为逻辑容器分组 | 正常 |
| AC-1.3 | WHEN `ContainerSpan` 未挂在 Text/RichEditor 下 THEN 无父级 Paragraph 管线消费，不渲染 | 边界 |
| AC-1.4 | WHEN ContainerSpanNode::MarkTextDirty 触发 THEN 委托 SpanNode::RequestTextFlushDirty 传播至父级 Text/RichEditor 重排 | 正常 |

### US-2: 设置背景

**作为** 应用开发者,
**我想要** 通过 textBackgroundStyle 设置容器片段的背景色与圆角,
**以便** 容器分组可呈现背景视觉边界。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `.textBackgroundStyle({ color: Color.Yellow, radius: 4 })`（API 11 dynamic / 23 static） THEN 经 `JSContainerSpan::ParseTextBackgroundStyle`（`js_container_span.cpp:30`）解析后调用 `SpanModel::GetInstance()->SetTextBackgroundStyle`（`:27`）→ `SpanModelNG::SetTextBackgroundStyleByBaseSpan`（`span_model_ng.h:118`）写入 BaseSpan 的 TextBackgroundStyle，容器背景以黄色圆角矩形绘制 | 正常 |
| AC-2.2 | WHEN `textBackgroundStyle.color` 为 undefined THEN 背景色透明（不绘制） | 边界 |
| AC-2.3 | WHEN `textBackgroundStyle.radius` 传入 `BorderRadiuses.TOP_START` 枚举 THEN 背景按指定圆角枚举绘制 | 边界 |

### US-3: 确认不支持通用事件

**作为** 应用开发者,
**我想要** 了解 ContainerSpan 不支持任何通用事件,
**以便** 不在 ContainerSpan 上注册无效事件回调。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 对 ContainerSpan 调用 `.onClick()`/`.onHover()`/`.onTouch()` 等通用事件 THEN 不支持，不产生回调（dynamic/static 文档明确"通用事件不支持"） | 异常 |
| AC-3.2 | WHEN 对 ContainerSpan 调用 `.attributeModifier(modifier)`（API 12 dynamic / 23 static） THEN 仅 ContainerSpanAttribute 声明的 textBackgroundStyle 经 modifier 下发 | 正常 |

### US-4: 确认无独立 NDK 节点类型

**作为** 应用开发者,
**我想要** 了解 ContainerSpan 无独立 NDK 节点类型,
**以便** C-API 场景下经 styled-string 或 ArkTS 组件使用容器片段。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN NDK 枚举查找 `ARKUI_NODE_CONTAINER_SPAN` THEN 不存在该枚举值（仅 Span/ImageSpan/CustomSpan 有 NDK 节点类型） | 边界 |
| AC-4.2 | WHEN NDK 经 generated modifier `container_span_modifier.cpp` 创建 THEN `ConstructImpl` 调用 `SpanModelStatic::CreateContainerSpanNode`，但公共 NDK 节点类型枚举不暴露独立值 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-04 | XTS + 节点 tag 校验 | span_model_ng.h:115, span_node.h:1515 |
| AC-1.2 | R-2 | TASK-04 | XTS：多子 span 挂载 | ContainerSpanNode 非原子 |
| AC-1.3 | R-3 | TASK-04 | 负向用例（无父 Text） | multiple_paragraph_layout_algorithm.h:40 |
| AC-1.4 | R-4 | TASK-04 | dirty 传播校验 | span_node.h:1515 MarkTextDirty |
| AC-2.1 | R-5 | TASK-04 | XTS textBackgroundStyle 用例 | js_container_span.cpp:30/27, span_model_ng.h:118 |
| AC-3.1 | R-6 | TASK-04 | 负向用例（onClick 无效） | container_span.d.ts 文档注释 |
| AC-4.1 | R-7 | TASK-04 | NDK 枚举缺失校验 | native_node.h 无 ARKUI_NODE_CONTAINER_SPAN |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 在 Text 下声明 `ContainerSpan(content_)` | 经 JSContainerSpan::Create → SpanModelNG::CreateContainSpan 构造 ContainerSpanNode（UINode+BaseSpan，tag CONTAINER_SPAN_ETS_TAG，非原子），挂载为 Text 子节点 | content_ 为可选 CustomBuilder | AC-1.1 |
| R-2 | 行为 | ContainerSpan 内声明子 Span/ImageSpan/SymbolSpan | 子片段作为 ContainerSpanNode 子节点挂载，形成逻辑分组 | 子片段仍各自独立样式 | AC-1.2 |
| R-3 | 边界 | ContainerSpan 未挂 Text/RichEditor | 不渲染（无父级 Paragraph 管线） | span 不可独立布局 | AC-1.3 |
| R-4 | 行为 | ContainerSpanNode 属性/子节点变更触发 MarkTextDirty | 委托 SpanNode::RequestTextFlushDirty 传播至父级 Text/RichEditor 重排 | dirty 传播链：ContainerSpanNode → 父级 | AC-1.4 |
| R-5 | 行为 | 调用 `.textBackgroundStyle({ color, radius })`（API 11 dynamic / 23 static） | 经 ParseTextBackgroundStyle → SetTextBackgroundStyleByBaseSpan 写入 BaseSpan TextBackgroundStyle，容器背景绘制 | color 为 undefined 时透明；radius 可为 Dimension 或 BorderRadiuses | AC-2.1/2.2/2.3 |
| R-6 | 异常 | 对 ContainerSpan 调用 onClick/onHover/onTouch 等通用事件 | 不支持，不产生回调 | dynamic/static 文档明确通用事件不支持 | AC-3.1 |
| R-7 | 边界 | NDK 查找 ARKUI_NODE_CONTAINER_SPAN | 不存在该枚举；ContainerSpan 仅经 ArkTS 组件或 styled-string 暴露 | NDK 通道不覆盖 ContainerSpan | AC-4.1/4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ContainerSpan 创建 | XTS：声明后检查 ContainerSpanNode tag | V2::CONTAINER_SPAN_ETS_TAG |
| VM-2 | AC-1.2 多子 span 分组 | XTS：ContainerSpan 内多子片段挂载 | 非原子节点 |
| VM-3 | AC-1.3 无父级不渲染 | 负向用例：ContainerSpan 挂 Column 不显示 | 无 Paragraph 消费 |
| VM-4 | AC-1.4 dirty 传播 | 单测：子 span 变更触发父级重排 | MarkTextDirty 委托 |
| VM-5 | AC-2.1~2.3 textBackgroundStyle | XTS：背景色/圆角/枚举截图比对 | SetTextBackgroundStyleByBaseSpan |
| VM-6 | AC-3.1 通用事件不支持 | 负向用例：onClick 无回调 | 文档注释契约 |
| VM-7 | AC-4.1 NDK 节点类型缺失 | 枚举查找：无 ARKUI_NODE_CONTAINER_SPAN | native_node.h |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|--------|
| `ContainerSpan(content_?: CustomBuilder)` dynamic @since 11 / static @since 23 | Public | 可选内容构建器 | ContainerSpanAttribute | N/A | 创建容器片段 | AC-1.1 |
| `ContainerSpanAttribute.textBackgroundStyle(TextBackgroundStyle)` @since 11 dynamic / 23 static | Public | 背景 color+radius | ContainerSpanAttribute | N/A | 设容器背景 | AC-2.1 |
| `ContainerSpanAttribute.attributeModifier(AttributeModifier<ContainerSpanAttribute>)` @since 12 dynamic / 23 static | Public | modifier | ContainerSpanAttribute | N/A | 挂载动态属性 | AC-3.2 |
| `class ContainerSpanModifier extends ContainerSpanAttribute implements AttributeModifier<ContainerSpanAttribute>` @since 12 dynamic / 23 static | Public | — | ContainerSpanModifier | N/A | 动态属性载体 | AC-3.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `ContainerSpanAttribute` @noninterop | 变更 | API 12 dynamic 增 @noninterop 标记 | 非跨组件交互场景不受影响 | — |

## 接口规格

### 接口定义

**ContainerSpan 构造**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ContainerSpan(content_?: CustomBuilder): ContainerSpanAttribute`（dynamic @since 11 / static @since 23，@ComponentBuilder） |
| 返回值 | `ContainerSpanAttribute`（dynamic/static 均不继承 CommonMethod/BaseSpan，独立类） |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| content_ | CustomBuilder | 否 | 无（空容器） | 子 span 在构建器内声明 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 在 Text 下声明 ContainerSpan(() => {Span('a')}) | 构造 ContainerSpanNode，子 Span 挂为子节点 | AC-1.1/1.2 |
| 2 | content_ 省略 | 构造空 ContainerSpanNode | AC-1.1 |
| 3 | 未挂 Text/RichEditor | 不渲染 | AC-1.3 |

**textBackgroundStyle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `textBackgroundStyle(style: TextBackgroundStyle): ContainerSpanAttribute`（dynamic @since 11 / static @since 23） |
| 返回值 | ContainerSpanAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| style.color | ResourceColor | 否 | 透明 | undefined 时透明不绘制 |
| style.radius | Dimension \| BorderRadiuses | 否 | 0 | 枚举指定四角不同圆角 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | textBackgroundStyle({color:Yellow, radius:4}) | 容器背景黄色圆角矩形 | AC-2.1 |
| 2 | color 为 undefined | 背景透明 | AC-2.2 |
| 3 | radius 为 BorderRadiuses 枚举 | 按指定圆角枚举绘制 | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 是。`ContainerSpanAttribute` API 12 dynamic 增 @noninterop 标记。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 11（dynamic）/ API 23（static）
- **API 版本号策略:** 逐 API 标注 `@since`；dynamic 与 static 双态分别标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ContainerSpan 必须挂载于 Text/RichEditor | 复用父级 Paragraph 管线 | AC-1.3 |
| ContainerSpanNode 为非原子 UINode | 可持有子 span；自身继承 UINode+BaseSpan（非 FrameNode） | AC-1.1/1.2 |
| 无通用事件支持 | onClick/onHover/onTouch 等均不支持（dynamic/static 文档明确） | AC-3.1 |
| 无独立 NDK 节点类型 | NDK 通道不覆盖；仅经 ArkTS 组件或 styled-string 暴露 | AC-4.1 |
| static/dynamic 均不继承 CommonMethod | 无通用属性继承 | AC-3.1 |
| 唯一属性为 textBackgroundStyle | 不支持 baselineOffset（与 Span/ImageSpan 不同） | AC-2.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 容器片段 dirty 传播耗时 ≤ 同等 Span | 帧率/trace | MarkTextDirty 委托 |
| 内存 | ContainerSpanNode 复用 BaseSpan，不重复持有 TextBackgroundStyle | 内存 profile | span_node.h:1515 |
| 可靠性 | 空容器不崩溃 | 边界用例 | content_ 省略路径 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | 容器自适应由父级 Text 处理 | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 容器片段经父级 Text 暴露无障碍语义 | 父级 Text accessibility |
| 大字体 | 否 | 容器本身无字体属性 | — |
| 深色模式 | 是 | textBackgroundStyle.color 支持主题资源 | ResourceColor |
| 多窗口/分屏 | 否 | 容器片段行为随父级 Text | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | API 11→23 演进 | 兼容性声明 |
| 生态兼容 | 是 | dynamic/static 双态并存 | static @since 23 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: ContainerSpan 容器片段
  作为 ArkUI 应用开发者
  我想要 在 Text 中插入容器片段分组子 span
  以便 同一容器内子片段共享背景样式

  Scenario: 在 Text 下创建 ContainerSpan 包裹子 Span
    Given Text 组件已挂载
    When 开发者声明 ContainerSpan(() => { Span('a'); Span('b') })
    Then 经 JSContainerSpan::Create → SpanModelNG::CreateContainSpan
    And 构造 ContainerSpanNode（CONTAINER_SPAN_ETS_TAG，非原子）
    And 子 Span('a')/Span('b') 挂为子节点

  Scenario: 为 ContainerSpan 设置背景
    Given ContainerSpan 已创建
    When 调用 .textBackgroundStyle({ color: Color.Yellow, radius: 4 })
    Then 经 ParseTextBackgroundStyle → SetTextBackgroundStyleByBaseSpan
    And 容器背景以黄色圆角矩形绘制

  Scenario: 通用事件不支持
    Given ContainerSpan 已创建
    When 对 ContainerSpan 调用 onClick(callback)
    Then 不支持，不产生回调

  Scenario: NDK 无独立节点类型
    Given NDK 场景
    When 查找 ARKUI_NODE_CONTAINER_SPAN 枚举
    Then 不存在该枚举
    And 容器片段仅经 ArkTS 组件或 styled-string 暴露
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
    query: "SpanModelNG::CreateContainSpan 如何构造 ContainerSpanNode（UINode+BaseSpan，非原子）并挂载子 span"
  - repo: "openharmony/arkui_ace_engine"
    query: "JSContainerSpan::ParseTextBackgroundStyle 如何解析 color/radius 并经 SetTextBackgroundStyleByBaseSpan 下发"
  - repo: "openharmony/arkui_ace_engine"
    query: "ContainerSpanNode::MarkTextDirty 如何委托 SpanNode::RequestTextFlushDirty 传播至父级"
  - repo: "openharmony/interface_sdk-js"
    query: "container_span.d.ts 与 containerSpan.static.d.ets 的 ContainerSpanAttribute 不继承 CommonMethod 的契约"
  - repo: "openharmony/arkui_ace_engine"
    query: "container_span_modifier.cpp GeneratedModifier::ConstructImpl 如何经 SpanModelStatic::CreateContainerSpanNode 创建"
```

**关键文档：** design.md；SDK `container_span.d.ts`/`containerSpan.static.d.ets`；`ContainerSpanModifier.d.ts`
