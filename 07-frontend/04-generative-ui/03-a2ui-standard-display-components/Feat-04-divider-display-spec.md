# 特性规格

> Func-07-04-03-Feat-04 Divider 组件：固化 A2UI 标准展示组件 Divider 的契约——分割线方向 `axis`（horizontal/vertical）与主题模式（深/浅色）颜色分流。基准实现：`@arkui-genius/genui`（A2UIRender，ArkTS Custom 组件 `CustomDivider`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Divider 组件 |
| 特性编号 | Func-07-04-03-Feat-04 |
| 优先级 | P1 |
| 目标版本 | A2UI 原生协议 v0.9 + 起始 API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 沿用 07-04-03 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/03-a2ui-standard-display-components/design.md` | Baselined |
| 组件实现（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomDivider.ets` | — |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIBasicCustomComponents.ets` | — |
| 协议 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/Divider.json` | — |
| 文档参考 | `render_docs/reference/standard-components/divider.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 分割线方向（axis）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `axis` 属性声明分割线方向,
**以便** 在水平/垂直内容块之间渲染合适方向的分割线。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `axis` 为 `"horizontal"` THEN 渲染水平分割线（`Divider().vertical(false)`）（`CustomDivider.ets:56-57`） | 正常 |
| AC-1.2 | WHEN `axis` 为 `"vertical"` THEN 渲染垂直分割线（`Divider().vertical(true)`）（`CustomDivider.ets:56-57`） | 正常 |
| AC-1.3 | WHEN `axis` 缺省或非法 THEN 回落默认 `"horizontal"`（`CustomDivider.ets:125-133`） | 边界 |

### US-2: 主题模式颜色

**作为** 生成式 UI 宿主开发者,
**我想要** Divider 颜色随深色/浅色模式切换,
**以便** 分割线在两种主题下均清晰可见。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `colorMode==DARK` THEN 分割线颜色为 `0x33FFFFFF`（`CustomDivider.ets:36-37,40-42`） | 正常 |
| AC-2.2 | WHEN `colorMode!=DARK`（浅色/未定义）THEN 分割线颜色为 `0x33000000`（`CustomDivider.ets:36-37,40-42`） | 正常 |

### US-3: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** Divider 组件以 `component:"Divider"` 注册为标准目录 Custom 组件,
**以便** DSL 中的 Divider 组件被正确路由到 ArkTS Custom 渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 目录注册 THEN `createDividerDefinition()` 以 `type='Divider'` 加载 `components/Divider.json`（`CustomDivider.ets:143-153`） | 正常 |
| AC-3.2 | WHEN 目录项 THEN `asCatalogItem()` 标记 `markInnerNative(false)`（`CustomDivider.ets:155-162`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1,R-2 | T-4 | ArkTS 单测：`resolveOptionsForSchemaWarning` | `CustomDivider.ets:112-135` |
| AC-2.1,AC-2.2 | R-3 | T-4 | ArkTS 单测：`resolveDividerColorByThemeMode` | `CustomDivider.ets:36-42` |
| AC-3.1,AC-3.2 | R-4 | T-4 | 静态比对 | `CustomDivider.ets:143-162` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `axis` 为 horizontal/vertical | 渲染对应方向分割线（vertical 布尔映射） | 枚举 {horizontal, vertical} | AC-1.1,AC-1.2 |
| R-2 | 边界 | `axis` 缺省或非法 | 回落 `"horizontal"` | 默认 horizontal | AC-1.3 |
| R-3 | 行为 | 主题模式切换 | 颜色 DARK=0x33FFFFFF，浅色=0x33000000 | 0x33 透明度常量 | AC-2.1,AC-2.2 |
| R-4 | 行为 | 目录注册 | type `"Divider"`，Custom 组件（markInnerNative false） | — | AC-3.1,AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 axis | ArkTS 单测 | 方向映射、缺省/非法回落 |
| VM-2 | AC-2.1,AC-2.2 主题颜色 | ArkTS 单测 | DARK/浅色常量 |
| VM-3 | AC-3.1,AC-3.2 目录 | 静态比对 | type 与 markInnerNative(false) |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `createDividerDefinition()` / `asCatalogItem()` | 既有 | Divider 目录注册 | 不直接暴露给宿主 | AC-3.1,AC-3.2 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/CustomDivider.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**Divider 组件特有属性（descriptor 属性契约，非函数 API）**

| 属性 | 值 |
|------|-----|
| 属性声明 | `CustomDivider.resolveOptionsForSchemaWarning`（`CustomDivider.ets:112-135`） |
| 必填属性 | 无（`Divider.json:26-28` 仅 required `component`） |
| 开放范围 | 协议 DSL（无 Public/System API） |
| 错误码 | 非法 axis 走 schema warning（`normalizeEnumStringProperty` 回落） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-2.1,AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| axis | string（enum） | 否 | `"horizontal"` | 枚举 {horizontal, vertical}，非法回落 horizontal |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `axis:"horizontal"` | 水平分割线（vertical=false） | AC-1.1 |
| 2 | `axis:"vertical"` | 垂直分割线（vertical=true） | AC-1.2 |
| 3 | `axis` 缺省/非法 | 回落 horizontal | AC-1.3 |
| 4 | DARK 主题 | 颜色 0x33FFFFFF | AC-2.1 |
| 5 | 浅色主题 | 颜色 0x33000000 | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9，起始 API Version 20。
- **API 版本号策略:** 协议 schema 版本由 `SchemaResourceLoader.loadA2UISchema(version, 'components/Divider.json')` 声明（`CustomDivider.ets:143-145`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| Custom 组件路径 | Divider 走 ArkTS Custom 渲染（`markInnerNative(false)`），无 C++ 实现 | AC-3.2 |
| axis 枚举回落 | 非法/缺省回落 horizontal，不报错仅回落 | AC-1.3 |
| 主题颜色双端 | ArkTS 侧按 `ThemeMode` 显式分流 | AC-2.1,AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 axis 不抛异常，回落 horizontal | ArkTS 单测 | `CustomDivider.ets:112-135` |
| 可测试性 | `resolveOptionsForSchemaWarning` 为纯函数可单测 | ArkTS 单测 | `CustomDivider.ets:112-135` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 分割线颜色/方向与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityText`/`accessibilityDescription` 透传（`CustomDivider.ets:69-70`） | AC-1.1,AC-1.2,AC-1.3 |
| 大字体 | 否 | 分割线无文本，不涉及 | — |
| 深色模式 | 是 | 分割线颜色按 `ThemeMode` 分流 | AC-2.1,AC-2.2 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 协议版本 v0.9 绑定 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 Divider 语义对齐 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Divider 组件
  作为 生成式 UI 宿主开发者
  我想要 通过 axis 声明分割线方向与主题颜色
  以便 渲染引擎正确显示分割线

  Scenario: 方向解析
    Given DSL 组件为 {"component":"Divider","id":"d1","axis":"vertical"}
    When 解析分割线选项
    Then 渲染垂直分割线（vertical=true）

  Scenario Outline: axis 回落
    Given DSL 组件为 {"component":"Divider","id":"d1","axis":<axis>}
    When 解析分割线选项
    Then 方向为 <direction>

    Examples:
      | axis          | direction  |
      | "vertical"    | vertical   |
      | "invalid"     | horizontal |
      | (缺省)        | horizontal |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Divider 特有属性 axis；strokeWidth/color 归 07-04-11 扩展域 ExtendedDivider）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomDivider resolveOptionsForSchemaWarning axis normalizeEnumStringProperty"
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomDivider resolveDividerColorByThemeMode DIVIDER_LIGHT_COLOR DIVIDER_DARK_COLOR"
  - repo: "GenerativeUI/A2UIRender"
    query: "createDividerDefinition asCatalogItem markInnerNative CustomComponentDefinition"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/CustomDivider.ets`、`genui/src/main/ets/core/components/A2UI/A2UIBasicCustomComponents.ets`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/Divider.json`