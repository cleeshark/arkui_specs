# 特性规格

> Func-07-04-13-Feat-02 TabContent 扩展页签项：固化鸿蒙扩展协议 `component: "TabContent"` 的行为——TabContent 为 ArkTS 自定义组件，渲染时把 `title`/`icon`/`selectedSrc`/`tabType` 及私有 `styles.*` 归一化为 `ExtendedTabMetadata` 写入 `ExtendedTabsRegistry`（键 `surfaceId::componentId`），供 Tabs 页签栏消费；组件卸载时移除元数据。标题/图标支持静态与动态字符串（含 `{{...}}` 表达式、`__a2uiBindings` 路径绑定）；`tabType` 归一化为 `capsule`/`underline`（非法回退空串）；颜色须匹配 `#RRGGBB`/`#AARRGGBB`，数值样式非负，`fontWeight` 取 100~900（步长 100）或合法关键字。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TabContent 扩展页签项 |
| 特性编号 | Func-07-04-13-Feat-02 |
| 优先级 | P1 |
| 目标版本 | API Version 20；鸿蒙扩展协议 1.0.0 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 与 Feat-01 并列，共享 Func-07-04-13 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/13-a2ui-extended-container-components/design.md` | Baselined |
| TabContent 自定义组件（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedTabContent.ets` | — |
| 元数据注册表（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedTabsRegistry.ets` | — |
| 属性归一化（C++） | `genui/src/main/cpp/components/custom/CustomComponentTabContentValidation.cpp` | — |
| TabContent 文档（Docs） | `reference/extended-components/tab-content.md` | 理解辅助 |
| 组件 Schema | `genui/src/main/resources/rawfile/schema/Extended/components/ExtendedTabContent.json` | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: TabContent 组件注册

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别 `component: "TabContent"` 并注册为扩展自定义组件,
**以便** 作为 Tabs 的页签项被挂载。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `createExtendedTabContentDefinition()` 被调用 THEN 返回 `type === 'TabContent'`、`builder` 与 `schemaProvider`（`ExtendedTabContent.ets:368-373`，`EXTENDED_TAB_CONTENT_TYPE` 于 `:40`） | 正常 |
| AC-1.2 | WHEN `schemaProvider` 被调用 THEN 加载 `schema/Extended/components/ExtendedTabContent.json`（`ExtendedTabContent.ets:364-366`） | 正常 |
| AC-1.3 | WHEN 扩展 Catalog 聚合 THEN `getExtendedCustomDefinitions` 将 `createExtendedTabContentDefinition()` 纳入（`A2UIExtendedComponents.ets:172`） | 正常 |

### US-2: 元数据同步到 ExtendedTabsRegistry

**作为** 生成式 UI 宿主开发者,
**我想要** TabContent 把标题/图标/样式同步给 Tabs,
**以便** Tabs 页签栏按 TabContent 声明渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `aboutToAppear`/`onAttributeChange` 触发 THEN `syncMetadata` 读取 `title`/`icon`/`selectedSrc`/`tabType` 及 `styles.*` 组装 `ExtendedTabMetadata` 并 `updateMetadata`（`ExtendedTabContent.ets:111-117,145-170`） | 正常 |
| AC-2.2 | WHEN `attribute.id` 为空 THEN `syncMetadata` 直接返回不写入（`ExtendedTabContent.ets:146-148`） | 边界 |
| AC-2.3 | WHEN 元数据键 `${surfaceId}::${componentId}` 且 componentId 为空 THEN 键为空返回 null/undefined（`ExtendedTabsRegistry.ets:102-110`） | 边界 |
| AC-2.4 | WHEN 新旧元数据 `isSameMetadata` 完全一致 THEN `updateMetadata` 不写入不通知（`ExtendedTabsRegistry.ets:45-48,112-127`） | 边界 |
| AC-2.5 | WHEN `aboutToDisappear` 触发 THEN `removeMetadata(surfaceId, id)` 移除对应元数据（`ExtendedTabContent.ets:119-121`） | 正常 |

### US-3: 标题/图标/选中图标的动态解析

**作为** 生成式 UI 宿主开发者,
**我想要** title/icon/selectedSrc 支持静态与动态值,
**以便** 标题随数据模型/表达式更新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `title` 为静态字符串 THEN `resolveExtendedTabContentRuntimeStringValue` 原样返回（`ExtendedTabContent.ets:56-64`） | 正常 |
| AC-3.2 | WHEN 值为 `{{...}}` 表达式字符串 THEN 经 `resolveDynamicStringOptionValue` 解析（`isExtendedTabContentExpressionString` 于 `:51-54`） | 正常 |
| AC-3.3 | WHEN `__a2uiBindings` 含某 key 的路径字符串 THEN `resolveBoundStringValue` 经 `resolveDynamicStringPathOptionValue` 从数据模型取值（`ExtendedTabContent.ets:229-257`） | 正常 |
| AC-3.4 | WHEN 解析失败/缺失 THEN `readDynamicString` 回退 fallback（title/icon/selectedSrc 默认空串）（`ExtendedTabContent.ets:172-190,42-44`） | 异常 |
| AC-3.5 | WHEN `selectedSrc` 为空 THEN 运行时不单独覆盖选中态（回退显示 icon，见 Feat-01 `resolveIconSource`） | 边界 |

### US-4: tabType 归一化

**作为** 生成式 UI 宿主开发者,
**我想要** `tabType` 被归一化为合法枚举,
**以便** 非法值回退默认页签样式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `tabType` 为 `capsule` 或 `underline` THEN `normalizeExtendedTabTypeValue` 原样返回（`ExtendedTabContent.ets:66-74`） | 正常 |
| AC-4.2 | WHEN `tabType` 为其他字符串或 undefined THEN 返回 fallback（空串）（`ExtendedTabContent.ets:66-74,192-205`） | 边界 |
| AC-4.3 | WHEN C++ 侧归一化 `tabType` 非空且非 `underline`/`capsule` THEN 报 `INVALID_VALUE` 警告并重置（`CustomComponentTabContentValidation.cpp:83-99`） | 异常 |

### US-5: 私有 styles 归一化（颜色/数值/字重）

**作为** 生成式 UI 宿主开发者,
**我想要** 私有样式被校验归一化,
**以便** 非法样式被忽略或重置到协议默认。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 颜色（selectedColor 等 6 项）匹配 `#RRGGBB`/`#AARRGGBB` THEN `normalizeExtendedTabContentColorValue` 返回该值，否则返回 undefined（`ExtendedTabContent.ets:98-103`） | 正常 |
| AC-5.2 | WHEN 数值样式（fontSize/iconSize/space）非有限或 `< 0` THEN `normalizeExtendedTabContentMetricValue` 返回 undefined（`ExtendedTabContent.ets:76-81`） | 边界 |
| AC-5.3 | WHEN `fontWeight` 为 100~900 且步长 100 THEN `normalizeExtendedTabContentFontWeightValue` 返回数值（`ExtendedTabContent.ets:83-90`） | 正常 |
| AC-5.4 | WHEN `fontWeight` 为 `lighter/normal/regular/medium/bold/bolder` THEN 返回该关键字（`ExtendedTabContent.ets:91-94`） | 正常 |
| AC-5.5 | WHEN `fontWeight` 非法或缺失 THEN 回退默认 500（`DEFAULT_TAB_FONT_WEIGHT` 于 `:41`，`syncMetadata` 兜底于 `:165`） | 边界 |
| AC-5.6 | WHEN C++ 侧 styles 数值 `< 0` 或字符串非空校验失败 THEN 报 `INVALID_VALUE`/类型告警并移除该 style 项（`CustomComponentTabContentValidation.cpp:118-216`） | 异常 |

### US-6: 内容区渲染与生命周期

**作为** 生成式 UI 宿主开发者,
**我想要** TabContent 内容区渲染槽位并按主题设置背景,
**以便** 页签内容正确呈现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `attribute.slot !== undefined` THEN `ContentSlot(slot)` 渲染内容（`ExtendedTabContent.ets:124-127`） | 正常 |
| AC-6.2 | WHEN 组件构建 THEN `onClick`/`onAppear` 各派发对应事件（`ExtendedTabContent.ets:129-134`） | 正常 |
| AC-6.3 | WHEN 深浅色模式 THEN 内容区背景色浅色 `#FFFFFF`、深色 `#171E2B`（`resolveContentAreaBackgroundColor`，`ExtendedTabContent.ets:352-356,46-47`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-2 | ArkTS 静态比对：定义 + Catalog 聚合 | `ExtendedTabContent.ets:364-373`、`A2UIExtendedComponents.ets:168-183` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-2 | ArkTS 单测：元数据同步/去重/移除 | `ExtendedTabContent.ets:111-170`、`ExtendedTabsRegistry.ets:40-127` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-2 | ArkTS 单测：动态字符串/绑定解析 | `ExtendedTabContent.ets:51-64,172-257` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-2 | ArkTS/C++ 归一化 | `ExtendedTabContent.ets:66-74`、`CustomComponentTabContentValidation.cpp:83-99` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 | R-5 | T-2 | ArkTS/C++ 归一化 | `ExtendedTabContent.ets:76-103,263-304`、`CustomComponentTabContentValidation.cpp:118-216` |
| AC-6.1,AC-6.2,AC-6.3 | R-6 | T-2 | ArkTS 单测：内容区渲染 | `ExtendedTabContent.ets:123-143,352-356` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | descriptor `component=="TabContent"` | 注册为 ArkTS 扩展自定义组件 | 经 `getExtendedCustomDefinitions` 聚合 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | 元数据同步 | 出现/更新写入，卸载移除；同值去重不通知 | 键 `surfaceId::componentId` | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 边界 | title/icon/selectedSrc 解析 | 静态/表达式/绑定三态，失败回退空串 | `{{...}}` 表达式、`__a2uiBindings` | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 边界 | tabType 归一化 | capsule/underline 合法，其余回退空串 | 非空且非合法 C++ 侧报错重置 | AC-4.1,AC-4.2,AC-4.3 |
| R-5 | 边界 | 私有 styles 归一化 | 颜色 hex 校验、数值非负、字重 100~900 步长 100 或关键字 | 非法移除/忽略，fontWeight 默认 500 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 |
| R-6 | 行为 | 内容区渲染 | ContentSlot + 事件 + 深浅色背景 | 槽位缺失不渲染 | AC-6.1,AC-6.2,AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 注册/识别 | 静态比对 | type='TabContent'、schemaProvider、Catalog 聚合 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 元数据同步 | ArkTS 单测 | 写入/去重/移除、键构造 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 动态解析 | ArkTS 单测 | 静态/表达式/绑定三态 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 tabType | ArkTS/C++ 归一化 | capsule/underline 合法值 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 私有样式 | ArkTS/C++ 归一化 | hex 颜色、非负数、字重 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3 内容区 | ArkTS 单测 | ContentSlot、事件、背景色 |

## API 变更分析

> 存量补录，无新增/变更公开 ArkTS/C-API。本节列出受影响组件协议。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `TabContent` 扩展组件协议（`title`/`icon`/`selectedSrc`/`tabType`/`children`，私有 `styles.*`） | 既有 | 页签项声明 | 与标准协议 TabContent 区分（catalogId 判别） | AC-1.1,AC-1.2,AC-1.3,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-6.1,AC-6.2,AC-6.3 |
| `ExtendedTabContent`（内部 ArkTS 组件） | 既有 | 元数据同步 | 不直接暴露给宿主 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |

> Schema 位置：`genui/src/main/resources/rawfile/schema/Extended/components/ExtendedTabContent.json`（required `["component"]`，properties 含 `title`/`icon`/`selectedSrc`/`tabType` + `styles.*`）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`createExtendedTabContentDefinition()`（`ExtendedTabContent.ets:368`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `createExtendedTabContentDefinition(): CustomComponentDefinition` |
| 返回值 | `CustomComponentDefinition` — 含 `type/builder/schemaProvider` |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2 |

**`ExtendedTabsRegistry.updateMetadata(surfaceId, componentId, metadata)`（`ExtendedTabsRegistry.ets:40`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static updateMetadata(surfaceId: string, componentId: string, metadata: ExtendedTabMetadata): void` |
| 返回值 | `void` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| title | string/dynamic | 否 | `""` | 静态/表达式/绑定 |
| icon | string/dynamic | 否 | `""` | 静态/表达式/绑定 |
| selectedSrc | string/dynamic | 否 | `""` | 空则回退 icon |
| tabType | string/dynamic | 否 | `""` | `capsule`/`underline`/空串 |
| styles.selectedColor | string/dynamic | 否 | 未设置 | `#RRGGBB`/`#AARRGGBB` |
| styles.fontSize | number/dynamic | 否 | 16 | 非负 |
| styles.fontWeight | number/string | 否 | 500 | 100~900 步长 100 或关键字 |
| styles.iconSize | number/dynamic | 否 | 16 | 非负 |
| styles.space | number/dynamic | 否 | 0 | 非负 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 组件出现 | 写入元数据并通知 Tabs | AC-2.1 |
| 2 | 元数据与上次一致 | 不写入不通知 | AC-2.4 |
| 3 | 组件卸载 | 移除元数据 | AC-2.5 |
| 4 | tabType 非法 | 回退空串（C++ 侧告警） | AC-4.2,AC-4.3 |
| 5 | fontWeight 非法 | 回退 500 | AC-5.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API Version 20；鸿蒙扩展协议 1.0.0。
- **API 版本号策略:** 组件协议经 JSON Schema 约束；无 `@since` 标注差异。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 元数据解耦 | TabContent 只写元数据，Tabs 读元数据渲染，二者异步创建仍对齐 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| 键隔离 | 元数据键含 surfaceId 隔离多 Surface | AC-2.3 |
| 归一化 | 颜色/数值/字重非法一律回退协议默认 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法标题/样式不崩溃，回退默认 | ArkTS 单测 | `ExtendedTabContent.ets:172-190,263-304` |
| 性能 | 元数据同值去重（`isSameMetadata`）避免冗余通知 | ArkTS 单测 | `ExtendedTabsRegistry.ets:45-48,112-127` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 系统 Tabs/TabContent 通用能力 | ohosTest | `ExtendedTabContent.ets:123-143` |
| 平板 | 无差异 | 同上 | ohosTest | 同上 |
| 折叠屏 | 无差异 | 同上 | ohosTest | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityText`/`accessibilityDescription` 下发 | `ExtendedTabContent.ets:135-136` |
| 大字体 | 否 | 标题字号可经 styles.fontSize 控制 | — |
| 深色模式 | 是 | 内容区背景深浅色分支（`#FFFFFF`/`#171E2B`） | AC-6.3 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API Version 20；扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | 鸿蒙扩展协议组件 | 概述 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: TabContent 扩展页签项
  作为 生成式 UI 宿主开发者
  我想要 TabContent 提供页签标题/图标/样式
  以便 Tabs 页签栏按声明渲染

  Scenario: 元数据同步与移除
    Given TabContent 组件出现并声明 title/icon/tabType
    When 引擎渲染该 TabContent
    Then ExtendedTabsRegistry 含该组件元数据；卸载后移除

  Scenario: 动态标题解析
    Given DSL 含 {"component":"TabContent","id":"t","title":{"path":"/title"}} 且 /title="首页"
    When syncMetadata 解析 title
    Then 元数据 title 为 "首页"

  Scenario Outline: 非法私有样式回退
    Given TabContent 声明 <style>
    When 归一化私有样式
    Then <expected>

    Examples:
      | style | expected |
      | styles.selectedColor="red" | 颜色被忽略 |
      | styles.fontSize=-1 | 数值被忽略 |
      | styles.fontWeight=450 | 字重回退 500 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（扩展 TabContent 页签项语义；页签栏最终视觉归 Feat-01 Tabs）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTabContent syncMetadata readDynamicString readTabType styles 归一化"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTabsRegistry updateMetadata removeMetadata getMetadata isSameMetadata buildMetadataKey"
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomComponentTabContentValidation NormalizeExtendedTabContentProperty tabType styles fontWeight 颜色校验"
```

**关键文档：** `genui/src/main/ets/core/components/extended/ExtendedTabContent.ets`、`genui/src/main/ets/core/components/extended/ExtendedTabsRegistry.ets`、`genui/src/main/cpp/components/custom/CustomComponentTabContentValidation.cpp`