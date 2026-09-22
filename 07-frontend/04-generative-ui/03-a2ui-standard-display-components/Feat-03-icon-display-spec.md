# 特性规格

> Func-07-04-03-Feat-03 Icon 组件：固化 A2UI 标准展示组件 Icon 的契约——`name` 属性（预定义语义名或 `{path}` 对象）到系统符号资源的映射、非法/缺省 name 回落灰色占位符、主题模式（深/浅色）颜色分流。基准实现：`@arkui-genius/genui`（A2UIRender，ArkTS Custom 组件 `CustomIcon`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Icon 组件 |
| 特性编号 | Func-07-04-03-Feat-03 |
| 优先级 | P0 |
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
| 组件实现（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomIcon.ets` | — |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIBasicComponents.ets` | — |
| 协议 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/Icon.json` | — |
| 文档参考 | `render_docs/reference/standard-components/icon.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 图标名称解析与渲染

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `name` 属性声明图标,
**以便** 渲染引擎将语义名映射到系统符号资源并显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `name` 为内置语义名（如 `"home"`）THEN 映射到 `sys.symbol.house` 资源并渲染 `SymbolGlyph`（`CustomIcon.ets:73,254-261`） | 正常 |
| AC-1.2 | WHEN `name` 为 `{path:"..."}` 对象 THEN 按数据模型 path 解析图标名（schema `oneOf` 支持，`Icon.json:83-95`） | 正常 |
| AC-1.3 | WHEN `name` 为合成名 `"starHalf"` THEN 走 `COMPOSITE_ICON_MAP` 半星合成渲染（`CustomIcon.ets:113-115,204-213,297-342`） | 正常 |

### US-2: 非法/缺省 name 回落

**作为** 生成式 UI 宿主开发者,
**我想要** Icon 在 name 非法或缺省时稳定降级,
**以便** 不因非法输入导致渲染崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `name` 缺省（descriptor 无 name）THEN 回落默认 `"help"` 并渲染灰色占位符（`renderPlaceholder=true`）（`CustomIcon.ets:41,165-182`） | 边界 |
| AC-2.2 | WHEN `name` 为非法字符串（不在 55 内置名 + starHalf 中）THEN 回落灰色占位符（`INVALID_ICON_PLACEHOLDER_NAME`，`CustomIcon.ets:43,194-202`） | 异常 |
| AC-2.3 | WHEN 渲染占位符 THEN 显示 `borderRadius=4` 的主题占位色块（`CustomIcon.ets:48,280-294`） | 正常 |

### US-3: 主题模式颜色

**作为** 生成式 UI 宿主开发者,
**我想要** Icon 颜色随深色/浅色模式切换,
**以便** 图标在两种主题下均清晰可见。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `colorMode==DARK` THEN 图标颜色取暗色资源 `$r('app.color.custom_icon_dark')`（`CustomIcon.ets:49-50,148-150`） | 正常 |
| AC-3.2 | WHEN `colorMode!=DARK`（浅色/未定义）THEN 图标颜色取浅色资源 `$r('app.color.custom_icon_light')`（`CustomIcon.ets:49-50,148-150`） | 正常 |
| AC-3.3 | WHEN `colorMode==DARK` THEN 占位符取暗色占位资源 `$r('app.color.custom_icon_dark_placeholder')`（`CustomIcon.ets:47,152-154`） | 正常 |
| AC-3.4 | WHEN 自定义属性含 `color`（number）THEN 覆盖默认主题颜色（`CustomIcon.ets:367-377`） | 边界 |

### US-4: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** Icon 组件以 `component:"Icon"` 注册为标准目录 Custom 组件,
**以便** DSL 中的 Icon 组件被正确路由到 ArkTS Custom 渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 目录注册 THEN `createIconDefinition()` 以 `type='Icon'` 加载 `components/Icon.json`（`CustomIcon.ets:397-406`） | 正常 |
| AC-4.2 | WHEN 目录项 THEN `asCatalogItem()` 标记 `markInnerNative(false)`（Custom 组件）（`CustomIcon.ets:408-415`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1,R-2 | T-3 | ArkTS 单测：`resolveIconRenderState` | `CustomIcon.ets:52-115,156-233` |
| AC-2.1,AC-2.2,AC-2.3 | R-3 | T-3 | ArkTS 单测：非法/缺省 name | `CustomIcon.ets:165-202,280-294` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-4 | T-3 | ArkTS 单测：`resolveColor`/`resolveIconDefaultColorByThemeMode` | `CustomIcon.ets:148-154,367-377` |
| AC-4.1,AC-4.2 | R-5 | T-3 | 静态比对 | `CustomIcon.ets:397-415` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `name` 为内置语义名 | 映射 `ICON_RESOURCE_MAP` 渲染 `SymbolGlyph` | 55 个内置名 | AC-1.1 |
| R-2 | 行为 | `name` 为 `{path}` 对象或 `starHalf` | 数据模型解析 / 半星合成 | schema `oneOf`；合成 map 仅 starHalf | AC-1.2,AC-1.3 |
| R-3 | 异常 | `name` 缺省或非法 | 回落灰色占位符（radius=4 主题色块） | 默认 name=`help`；非法名回落占位 | AC-2.1,AC-2.2,AC-2.3 |
| R-4 | 行为 | 主题模式切换 | 图标/占位颜色按 DARK/浅色分流 | 覆盖：自定义 `color` number 优先 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-5 | 行为 | 目录注册 | type `"Icon"`，Custom 组件（markInnerNative false） | — | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 name 解析 | ArkTS 单测 | 资源映射、{path} 对象、starHalf 合成 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 回落 | ArkTS 单测 | 缺省/非法 name → 灰色占位符 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 主题颜色 | ArkTS 单测 | DARK/浅色分流、自定义 color 覆盖 |
| VM-4 | AC-4.1,AC-4.2 目录 | 静态比对 | type 与 markInnerNative(false) |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `createIconDefinition()` / `asCatalogItem()` | 既有 | Icon 目录注册 | 不直接暴露给宿主 | AC-4.1,AC-4.2 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/CustomIcon.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**Icon 组件特有属性（descriptor 属性契约，非函数 API）**

| 属性 | 值 |
|------|-----|
| 属性声明 | `CustomIcon.resolveIconRenderState`（`CustomIcon.ets:156-233`） |
| 必填属性 | `name`（`Icon.json:98-101` 声明 required） |
| 开放范围 | 协议 DSL（无 Public/System API） |
| 错误码 | 非法 name 走 schema warning；`Icon.json` 枚举约束 |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| name | string（enum）\| object{path} | 是 | `"help"`（缺省回落） | 55 内置名 + starHalf；非法回落占位符 |
| size（自定义） | number | 否 | `$r('app.float.custom_icon_size')` | 自定义属性，缺省用资源默认 |
| color（自定义） | number | 否 | 主题默认资源 | number 覆盖默认 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `name:"home"` | 渲染 `sys.symbol.house` | AC-1.1 |
| 2 | `name:"starHalf"` | 半星合成渲染 | AC-1.3 |
| 3 | `name` 缺省/非法 | 灰色占位符（radius=4） | AC-2.1,AC-2.2 |
| 4 | DARK 主题 | 暗色资源图标 | AC-3.1 |
| 5 | 自定义 `color:0xFF0000` | 覆盖主题色 | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9，起始 API Version 20。
- **API 版本号策略:** 协议 schema 版本由 `SchemaResourceLoader.loadA2UISchema(version, 'components/Icon.json')` 声明（`CustomIcon.ets:398-400`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| Custom 组件路径 | Icon 走 ArkTS Custom 渲染（`markInnerNative(false)`），无 C++ 实现 | AC-4.2 |
| 非法 name 降级 | 回落灰色占位符，非丢弃组件 | AC-2.1,AC-2.2,AC-2.3 |
| 主题颜色双端 | ArkTS 侧按 `ThemeMode` 显式分流，不依赖 native ThemeBase | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 name 不抛异常，回落占位符 | ArkTS 单测 | `CustomIcon.ets:156-233` |
| 可测试性 | `resolveIconRenderState` 为纯函数可单测 | ArkTS 单测 | `CustomIcon.ets:156-233` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 固定资源尺寸与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityText`/`accessibilityDescription` 透传（`CustomIcon.ets:270-271`） | AC-1.1,AC-1.2,AC-1.3 |
| 大字体 | 否 | 图标尺寸固定，不随字体缩放 | — |
| 深色模式 | 是 | 图标/占位颜色按 `ThemeMode` 分流 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 协议版本 v0.9 绑定 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 Icon 语义对齐 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Icon 组件
  作为 生成式 UI 宿主开发者
  我想要 通过 name 声明图标
  以便 渲染引擎映射系统符号资源显示

  Scenario: 内置图标渲染
    Given DSL 组件为 {"component":"Icon","id":"i1","name":"home"}
    When 解析渲染状态
    Then 资源为 sys.symbol.house，非占位符

  Scenario Outline: name 解析
    Given DSL 组件为 {"component":"Icon","id":"i1","name":<name>}
    When 解析渲染状态
    Then <结果>

    Examples:
      | name       | 结果          |
      | "starHalf" | 合成渲染      |
      | "invalid"  | 灰色占位符    |
      | (缺省)     | 灰色占位符    |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Icon 特有属性 name/size/color；通用属性归 07-04-18）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomIcon resolveIconRenderState ICON_RESOURCE_MAP COMPOSITE_ICON_MAP placeholder"
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomIcon resolveIconDefaultColorByThemeMode resolveIconPlaceholderColorByThemeMode ThemeMode DARK"
  - repo: "GenerativeUI/A2UIRender"
    query: "createIconDefinition asCatalogItem markInnerNative CustomComponentDefinition"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/CustomIcon.ets`、`genui/src/main/ets/core/components/A2UI/A2UIBasicComponents.ets`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/Icon.json`