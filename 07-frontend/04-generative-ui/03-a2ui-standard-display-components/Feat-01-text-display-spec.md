# 特性规格

> Func-07-04-03-Feat-01 Text 组件：固化 A2UI 标准展示组件 Text 的契约——文本内容属性 `text`（必填，DynamicString）与文本样式提示属性 `variant`（h1~h5/caption/body 枚举，映射固定字号）。基准实现：`@arkui-genius/genui`（A2UIRender，native C++ `TextComponent`/`TextTheme`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Text 组件 |
| 特性编号 | Func-07-04-03-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 + 起始 API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-03 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/03-a2ui-standard-display-components/design.md` | Baselined |
| 组件实现（C++） | `genui/src/main/cpp/components/A2UI/text/TextComponent.cpp` | — |
| 主题映射（C++） | `genui/src/main/cpp/components/A2UI/text/TextTheme.cpp` | — |
| 目录声明（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIText.ets` | — |
| 协议 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/Text.json` | — |
| 文档参考 | `render_docs/reference/standard-components/text.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 文本内容显示

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `text` 属性声明 Text 组件的显示内容,
**以便** 在渲染引擎中正确显示文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `text` 为合法字符串（如 `"Hello"`） THEN 渲染节点文本内容为该字符串（`TextComponent.cpp:34-36`） | 正常 |
| AC-1.2 | WHEN `text` 为 DynamicString（DataBinding/FunctionCall 返回 string） THEN 引擎按动态值解析后显示（`allowDynamic=true`，`TextComponent.cpp:31`） | 正常 |
| AC-1.3 | WHEN `text` 缺省（descriptor 无 `text` 键） THEN 上报必填缺失警告（`ERROR_CODE_REQUIRED_MISS`）并回落默认空串（`TextComponent.cpp:64-67`、`Component.cpp:1364-1365`） | 异常 |
| AC-1.4 | WHEN `text` 为非 string 标量（如数字 `42` 或布尔 `true`） THEN 引擎经归一化强转字符串显示（`"42"`/`"true"`） | 边界 |

### US-2: 文本样式提示（variant）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `variant` 属性声明文本样式提示,
**以便** 引擎按标题/正文层级映射合适字号。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `variant` 为 `"h1"`/`"h2"`/`"h3"`/`"h4"`/`"h5"`/`"caption"`/`"body"` 之一 THEN 字号映射为 32/28/24/20/18/12/16（`TextTheme.cpp:22-28,52-73`） | 正常 |
| AC-2.2 | WHEN `variant` 缺省 THEN 回落默认 `"body"`（字号 16）（`TextComponent.cpp:43-45`） | 边界 |
| AC-2.3 | WHEN `variant` 为非法字符串（如 `"invalid"`） THEN 回落默认 `"body"`（字号 16）并记录枚举回落（`TextComponent.cpp:45`、`TextTheme.cpp:72`） | 边界 |
| AC-2.4 | WHEN `variant` 为 `"h3"` THEN 节点字号属性为 24.0（`TextComponentTddTest.cpp` 验证 `NODE_FONT_SIZE=24.0F`） | 正常 |

### US-3: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** Text 组件以 `component:"Text"` 注册到标准目录,
**以便** DSL 中的 Text 组件被正确路由到 native 渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 组件类型查询 THEN `TextComponent::GetType()` 返回 `"Text"`（`TextComponent.cpp:59-62`） | 正常 |
| AC-3.2 | WHEN 目录注册 THEN `A2UIText.asCatalogItem()` 以 `type='Text'` 加载 `components/Text.json` 并标记 `A2UI_STANDARD` + `markInnerNative(true)`（`A2UIText.ets:25-36`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1,R-2 | T-1 | C++ UT：`TextComponentTddTest` | `TextComponent.cpp:28-37,64-67` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-3,R-4 | T-1 | C++ UT：`TextComponentTddTest` + 静态映射比对 | `TextTheme.cpp:22-28,52-73` |
| AC-3.1,AC-3.2 | R-5 | T-1 | 静态比对：`GetType`/`asCatalogItem` | `TextComponent.cpp:59-62`、`A2UIText.ets:25-36` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `text` 为合法字符串 | `SetTextContent` 设置节点文本内容 | DynamicString 允许动态绑定 | AC-1.1,AC-1.2 |
| R-2 | 异常 | `text` 缺省 | 上报 `ERROR_CODE_REQUIRED_MISS` 并回落空串 | 必填属性 `{"text"}` | AC-1.3 |
| R-3 | 边界 | `variant` 非法或缺省 | 回落 `"body"`（字号 16） | 枚举集 {h1,h2,h3,h4,h5,caption,body} | AC-2.2,AC-2.3 |
| R-4 | 行为 | `variant` 为合法枚举 | 字号映射 32/28/24/20/18/12/16 | h1=32…body=16 | AC-2.1,AC-2.4 |
| R-5 | 行为 | 组件类型/目录 | 类型 `"Text"`，标准目录 + native 标记 | — | AC-3.1,AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 text 内容 | C++ UT | 字符串显示、必填警告、标量强转 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 variant 字号 | C++ UT + 静态映射比对 | 枚举字号映射与回落 |
| VM-3 | AC-3.1,AC-3.2 类型/目录 | 静态比对 | GetType 与目录注册标记 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `CatalogItem`（`A2UIText.asCatalogItem()`） | 既有 | 组件目录注册 | 不直接暴露给宿主 | AC-3.2 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIText.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**Text 组件特有属性（descriptor 属性契约，非函数 API）**

| 属性 | 值 |
|------|-----|
| 属性声明 | `TextComponent::GetPrivatePropertyDeclaration`（`TextComponent.cpp:25-57`） |
| 必填属性 | `text`（`GetComponentDirectRequiredPropertyKeys`，`TextComponent.cpp:64-67`） |
| 开放范围 | 协议 DSL（无 Public/System API） |
| 错误码 | schema warning `2001`（`SURFACE_ERROR_SCHEMA_WARNING`）；缺必填 `ERROR_CODE_REQUIRED_MISS` |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| text | DynamicString | 是 | `""` | 任意字符串；缺省/非法回落 |
| variant | string（enum） | 否 | `"body"` | 枚举 {h1,h2,h3,h4,h5,caption,body}，非法回落 body |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `text:"Hello"` | 节点文本内容 "Hello" | AC-1.1 |
| 2 | `text` 缺省 | schema warning + 空串 | AC-1.3 |
| 3 | `text:42` | 强转 "42" | AC-1.4 |
| 4 | `variant:"h3"` | 字号 24.0 | AC-2.1,AC-2.4 |
| 5 | `variant` 缺省/非法 | 字号 16（body） | AC-2.2,AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9，起始 API Version 20。
- **API 版本号策略:** 协议 schema 版本由 `SchemaResourceLoader.loadA2UISchema(version, 'components/Text.json')` 声明（`A2UIText.ets:27-29`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 必填属性 text | 缺省上报必填警告并回落默认 | AC-1.3 |
| variant 枚举回落 | 非法枚举回落 body，不报错仅回落 | AC-2.2,AC-2.3 |
| native 组件路径 | Text 走 C++ 属性管线，非 Custom 组件 | AC-3.1,AC-3.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法/缺省属性不抛异常，统一回落默认 + schema warning | C++ UT | `Component.cpp:1352-1372` |
| 性能 | 属性应用为单次节点 API 调用 | C++ UT | `TextComponent.cpp:69-73` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 固定字号与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 走通用 `accessibility` 属性（归 07-04-18），本域不扩展 | — |
| 大字体 | 否 | variant 字号为硬编码常量，不随系统字体缩放（RISK-5） | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 深色模式 | 否 | Text 无颜色特有属性 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 协议版本 v0.9 绑定 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 Text 语义对齐 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Text 组件
  作为 生成式 UI 宿主开发者
  我想要 通过 text/variant 声明文本与样式
  以便 渲染引擎正确显示文本

  Scenario: 文本内容显示
    Given DSL 组件为 {"component":"Text","id":"t1","text":"Hello"}
    When 应用 descriptor
    Then 节点文本内容为 "Hello"

  Scenario Outline: variant 字号映射
    Given DSL 组件为 {"component":"Text","id":"t1","text":"X","variant":<variant>}
    When 应用 descriptor
    Then 节点字号为 <size>

    Examples:
      | variant | size |
      | h1      | 32.0 |
      | h3      | 24.0 |
      | body    | 16.0 |
      | invalid | 16.0 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Text 特有属性 text/variant；通用属性归 07-04-18）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "TextComponent GetPrivatePropertyDeclaration text variant PropertyDeclaration"
  - repo: "GenerativeUI/A2UIRender"
    query: "TextTheme ResolveFontSize H1_H5 CAPTION BODY font size mapping"
  - repo: "GenerativeUI/A2UIRender"
    query: "Component ValidateComponentDirectRequiredProperties ERROR_CODE_REQUIRED_MISS"
```

**关键文档：** `genui/src/main/cpp/components/A2UI/text/TextComponent.cpp`、`genui/src/main/cpp/components/A2UI/text/TextTheme.cpp`、`genui/src/main/ets/core/components/A2UI/A2UIText.ets`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/Text.json`
