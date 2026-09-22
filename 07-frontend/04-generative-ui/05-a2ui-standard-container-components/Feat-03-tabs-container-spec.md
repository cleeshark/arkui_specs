# 特性规格

> Func-07-04-05-Feat-03 Tabs 页签：固化 A2UI 标准协议 Tabs 组件的行为——Tabs 为纯 ArkTS 自定义组件（`markInnerNative(false)`），基于系统 `Tabs`/`TabContent`/`ContentSlot` 渲染；`tabs` 数组（`minItems=1`）每项 `title`/`child` 均必填，动态标题经 `DynamicValueResolver` 解析；品牌色存在时页签指示器与选中文字用品牌色；unknown field 经签名去重后派发 schema warning。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Tabs 页签 |
| 特性编号 | Func-07-04-05-Feat-03 |
| 优先级 | P1 |
| 目标版本 | API Version 20；A2UI 标准协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 与 Feat-01/Feat-02 并列，共享 Func-07-04-05 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/05-a2ui-standard-container-components/design.md` | Baselined |
| Tabs 自定义组件（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomTabs.ets` | — |
| 自定义组件工厂（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomComponentFactory.ets` | — |
| Tabs 文档（Docs） | `reference/standard-components/tabs.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Tabs 类目注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别 `component: "Tabs"` 并注册为自定义组件,
**以便** 通过标准协议声明页签容器。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `createTabsDefinition` 被调用 THEN 返回 `type=='Tabs'` 且带 `customTabsBuilder` 与 schemaProvider（`CustomTabs.ets:361-367`） | 正常 |
| AC-1.2 | WHEN `asCatalogItem` 被调用 THEN 经 `CatalogItem.forComponent` 注册并 `markInnerNative(false)`（`CustomTabs.ets:369-375`） | 正常 |
| AC-1.3 | WHEN schemaProvider 被调用 THEN 加载 `components/Tabs.json`（`CustomTabs.ets:357-359`） | 正常 |
| AC-1.4 | WHEN 工厂判断类型 THEN `isTabsType` 取短类型 `=== 'Tabs'`（`CustomComponentFactory.ets:200-201`） | 正常 |

### US-2: Tabs 页签数组归一化

**作为** 生成式 UI 宿主开发者,
**我想要** `tabs` 数组被归一化为页签定义,
**以便** 正确渲染每个页签。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `customProps` 非对象或为数组/null THEN `normalizeTabsDefinitions` 返回空数组（`CustomTabs.ets:193-196`） | 异常 |
| AC-2.2 | WHEN `tabs` 合法 THEN `normalizeObjectArrayProperty` 以 `TABS_COMPONENT_NAME="Tabs"`、`minItems=1`（`TABS_MIN_ITEMS`）归一化（`CustomTabs.ets:202-210`） | 正常 |
| AC-2.3 | WHEN 每项解析 THEN `title` 经 `normalizeDynamicStringProperty`、`child` 经 `normalizeNonEmptyStringProperty` 均必填（`CustomTabs.ets:218-234`） | 正常 |
| AC-2.4 | WHEN `child` 归一化结果为空/缺失 THEN `normalizedChild ?? ''` 回退为空串（`CustomTabs.ets:227-235`） | 边界 |
| AC-2.5 | WHEN 解析抛异常 THEN catch 后打 `console.error` 并返回空数组（`CustomTabs.ets:243-249`） | 异常 |

### US-3: Tabs 声明式渲染

**作为** 生成式 UI 宿主开发者,
**我想要** 每个页签渲染标题与内容,
**以便** 用户切换页签查看不同内容视图。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `build` 执行 THEN 使用 `Tabs({ index: currentIndex })` 声明容器（`CustomTabs.ets:96-97`） | 正常 |
| AC-3.2 | WHEN 页签有 `slot` 且 child 非空 THEN `ContentSlot(tab.slot)` 渲染内容；无 slot 则渲染 `Text('Loading...')` 占位（`CustomTabs.ets:100-107`） | 正常 |
| AC-3.3 | WHEN `barMode` 设置 THEN 使用 `BarMode.Fixed`、`animationDuration(200)`（`CustomTabs.ets:135-136`） | 正常 |
| AC-3.4 | WHEN 页签切换 THEN `.onChange` 更新 `currentIndex`（`CustomTabs.ets:137-139`） | 正常 |

### US-4: 品牌色与通用属性

**作为** 生成式 UI 宿主开发者,
**我想要** 品牌色与布局/无障碍属性作用于 Tabs,
**以便** 页签视觉与宿主主题一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 存在品牌色 THEN 页签 `SubTabBarStyle` 指示器与选中文字用品牌色（`CustomTabs.ets:98-116`） | 正常 |
| AC-4.2 | WHEN 无品牌色 THEN 页签仅 `tabBar(tab.title)`，无自定义指示器/选中色（`CustomTabs.ets:118-131`） | 边界 |
| AC-4.3 | WHEN 未选中或无品牌色 THEN `resolveTabsSelectedTextColor` 回退 `$r('app.color.custom_text_primary')`，指示器回退透明 `0x00000000`（`CustomTabs.ets:56-76`） | 边界 |
| AC-4.4 | WHEN 组件带通用属性 THEN `.layoutWeight`/`.margin`/`.accessibilityText`/`.accessibilityDescription` 下发（`CustomTabs.ets:140-143`） | 正常 |

### US-5: 动态标题解析与 unknown field 告警

**作为** 生成式 UI 宿主开发者,
**我想要** 动态标题被解析、未知字段被告警,
**以便** 标题随数据模型更新、非法配置被提示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 页签 `title` 为动态值 THEN `resolveDynamicString` 经 `DynamicValueResolver.resolveString` 解析（`CustomTabs.ets:339-349`） | 正常 |
| AC-5.2 | WHEN 动态标题解析抛异常 THEN 回退 `String(definition.titleValue)` 并打 `console.error`（`CustomTabs.ets:314-318`） | 异常 |
| AC-5.3 | WHEN 出现 unknown field THEN 根白名单 `["tabs"]`、项白名单 `["title","child"]` 校验并派发 warning（`CustomTabs.ets:53-54,253-305`） | 边界 |
| AC-5.4 | WHEN 未知字段签名与上次一致 THEN 跳过重复告警（`CustomTabs.ets:274-296`） | 边界 |

### US-6: 页签内容槽位关联

**作为** 生成式 UI 宿主开发者,
**我想要** 页签内容与槽位正确关联,
**以便** 内容组件渲染到对应页签。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `resolveTabItems` 执行 THEN 按归一化定义生成 `TabItem`，slotKey 为 `tab-<i>`（`CustomTabs.ets:236-240,307-337`） | 正常 |
| AC-6.2 | WHEN `slots` 为 `Map` 或对象 THEN 按 `slotKey` 取 `NodeContent` 槽位（`CustomTabs.ets:319-325`） | 正常 |
| AC-6.3 | WHEN 取槽位抛异常 THEN 打 `console.error` 并回退 `undefined`（`CustomTabs.ets:321-328`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-3 | ArkTS 静态比对：定义 + 工厂 | `CustomTabs.ets:357-375`、`CustomComponentFactory.ets:200-201` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-3 | ArkTS 单测：归一化 | `CustomTabs.ets:189-251` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-3 | ArkTS 单测：build 渲染 | `CustomTabs.ets:96-144` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4 | T-3 | ArkTS 单测：品牌色/通用属性 | `CustomTabs.ets:56-76,140-143` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4 | R-5 | T-3 | ArkTS 单测：动态标题 + 告警去重 | `CustomTabs.ets:253-349` |
| AC-6.1,AC-6.2,AC-6.3 | R-6 | T-3 | ArkTS 单测：槽位关联 | `CustomTabs.ets:307-337` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | descriptor `component=="Tabs"` | 注册为 ArkTS 自定义组件渲染 | `markInnerNative(false)` | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 边界 | `tabs` 数组归一化 | 至少 1 项，每项 title/child 必填 | 非对象/空返回空数组 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 行为 | build 渲染 | `Tabs`/`TabContent`/`ContentSlot` 声明式渲染 | `BarMode.Fixed`、动画 200ms | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 边界 | 品牌色存在与否 | 有品牌色用自定义指示器/选中色；无则默认 | 未选中回退默认资源/透明 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-5 | 异常 | 动态标题解析失败/未知字段 | 回退字面量/派发 warning 并去重 | 白名单 `["tabs"]`、`["title","child"]` | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| R-6 | 行为 | 槽位关联 | 按 `tab-<i>` 取 `NodeContent` 槽位 | 槽位缺失渲染 Loading 占位 | AC-6.1,AC-6.2,AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 类目/工厂 | 静态比对 | 类型、innerNative=false、isTabsType |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 归一化 | ArkTS 单测 | minItems、title/child 必填 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 声明渲染 | ArkTS 单测 | Tabs/TabContent/ContentSlot |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 品牌色 | ArkTS 单测 | 品牌色指示器/选中色/回退 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 动态标题+告警 | ArkTS 单测 | 动态解析、告警去重 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3 槽位关联 | ArkTS 单测 | slotKey 与 NodeContent |

## API 变更分析

> 存量补录，无新增/变更公开 ArkTS/C-API。本节列出受影响组件协议。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Tabs` 组件协议（`component`/`tabs[]`，项含 `title`/`child`） | 既有 | 页签容器声明 | tabs 至少 1 项，title/child 必填 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| `CustomTabs`（内部 ArkTS 组件） | 既有 | 页签渲染 | 不直接暴露给宿主 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

> Schema 位置：`components/Tabs.json`（经 `CustomTabs.ets:358` 加载）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`CustomTabs.normalizeTabsDefinitions()`（内部，`CustomTabs.ets:189`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `normalizeTabsDefinitions(): NormalizedTabDefinition[]` |
| 返回值 | `NormalizedTabDefinition[]` — 归一化页签定义（titleValue/child/slotKey） |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（经 schema warning 提示） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |

**`CustomTabs.resolveTabItems()`（`CustomTabs.ets:307`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `resolveTabItems(): TabItem[]` |
| 返回值 | `TabItem[]` — 含 title/child/slot 的页签列表 |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-6.1,AC-6.2,AC-6.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| tabs | array(object) | 是 | — | `minItems=1`，每项为对象 |
| tabs[].title | string/DynamicString | 是 | `""` | 非空（normalize 必填） |
| tabs[].child | string | 是 | `""`（缺失回退空串） | 非空组件 id |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | tabs 合法（≥1 项） | 归一化并渲染页签 | AC-2.2,AC-3.1 |
| 2 | tabs 缺失/空/非对象 | 返回空数组，无法创建 | AC-2.1 |
| 3 | 存在品牌色 | 指示器/选中文字用品牌色 | AC-4.1 |
| 4 | 无品牌色 | 默认 tabBar 标题 | AC-4.2 |
| 5 | 动态标题解析失败 | 回退字面量 | AC-5.2 |
| 6 | 未知字段 | 派发 warning（去重） | AC-5.3,AC-5.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API Version 20（`tabs.md:6`）。
- **API 版本号策略:** 组件协议经 JSON Schema 约束；无 `@since` 标注差异。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| ArkTS 自定义组件 | Tabs 走 ArkTS（`markInnerNative(false)`）而非 native | AC-1.2 |
| 数组最小值 | tabs 至少 1 项 | AC-2.2 |
| title/child 必填 | 每项均必填，缺失校验不通过 | AC-2.3,AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 解析异常不崩溃，回退空数组/字面量 | ArkTS 单测 | `CustomTabs.ets:243-249,314-318` |
| 性能 | 归一化经签名去重避免重复计算与告警 | ArkTS 单测 | `CustomTabs.ets:179-187,274-296` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 系统 Tabs 通用能力 | ohosTest | `CustomTabs.ets:96-144` |
| 平板 | 无差异 | 同上 | ohosTest | 同上 |
| 折叠屏 | 无差异 | 同上 | ohosTest | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityText`/`accessibilityDescription` 下发 | AC-4.4 |
| 大字体 | 否 | 不涉及（标题为任意字符串） | — |
| 深色模式 | 否 | 未选中文字用 `$r('app.color.custom_text_primary')` 资源 | AC-4.3 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API Version 20 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 标准组件协议 | 概述 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Tabs 页签
  作为 生成式 UI 宿主开发者
  我想要 通过 tabs 数组渲染页签
  以便 在不同内容视图间切换

  Scenario: 渲染单个页签
    Given DSL 含 {"component":"Tabs","id":"t1","tabs":[{"title":"Single Tab","child":"content1"}]}
    When 引擎渲染 Tabs
    Then 渲染一个 TabContent 且标题为 "Single Tab"

  Scenario: 多页签切换
    Given tabs 数组含多项
    When 用户点击某页签
    Then onChange 更新 currentIndex 并渲染对应内容

  Scenario Outline: 非法 tabs 拒绝
    Given Tabs 描述符 <what>
    When 归一化 tabs
    Then 返回空数组（无法创建页签）

    Examples:
      | what                  |
      | tabs 缺失             |
      | tabs 为空数组         |
      | tabs 项缺失 title     |
      | tabs 项缺失 child     |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Tabs 页签容器语义；动态字符串底层解析归数据域）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomTabs normalizeTabsDefinitions normalizeObjectArrayProperty minItems title child"
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomTabs build Tabs TabContent ContentSlot BarMode.Fixed 品牌色 SubTabBarStyle"
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomComponentFactory isTabsType getTabsCount Tabs 自定义组件注册"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/CustomTabs.ets`、`genui/src/main/ets/core/components/A2UI/CustomComponentFactory.ets`
