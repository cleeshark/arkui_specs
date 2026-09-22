# 特性规格

> Func-07-04-13-Feat-04 Web 扩展网页容器：固化鸿蒙扩展协议 `component: "Web"` 的行为——Web 为 ArkTS 自定义组件（经 `getExtendedCustomDefinitions` 注册），基于系统 `@kit.ArkWeb` 的 `Web({src, controller})` 渲染；`url` 支持静态字符串、表达式、路径绑定与函数调用（`resolveDynamicStringOptionValue`）；采用惰性加载（`updateUrl` 仅在「新 url 非空 且 旧 url 非空 且 不等」时调用 `loadUrlSafely`），`loadUrl` 异常被 try/catch 兜底不崩溃；`url` 缺失/解析失败回退空串（不主动加载）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Web 扩展网页容器 |
| 特性编号 | Func-07-04-13-Feat-04 |
| 优先级 | P1 |
| 目标版本 | API Version 20；鸿蒙扩展协议 1.0.0 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 与 Feat-01~03 并列，共享 Func-07-04-13 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/13-a2ui-extended-container-components/design.md` | Baselined |
| Web 自定义组件（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedWeb.ets` | — |
| 扩展 Catalog 聚合（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| Web 文档（Docs） | `reference/extended-components/web.md` | 理解辅助 |
| 组件 Schema | `genui/src/main/resources/rawfile/schema/Extended/components/ExtendedWeb.json` | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Web 组件注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别 `component: "Web"` 并注册为扩展自定义组件,
**以便** 在页面中嵌入 Web 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `createExtendedWebDefinition()` 被调用 THEN 返回 `type === 'Web'`、`builder` 与 `schemaProvider`（`ExtendedWeb.ets:129-138`，`EXTENDED_WEB_COMPONENT_TYPE` 于 `:31`） | 正常 |
| AC-1.2 | WHEN `schemaProvider` 被调用 THEN 加载 `schema/Extended/components/ExtendedWeb.json`（`ExtendedWeb.ets:130-132`） | 正常 |
| AC-1.3 | WHEN 扩展 Catalog 聚合 THEN `getExtendedCustomDefinitions` 将 `createExtendedWebDefinition()` 纳入（`A2UIExtendedComponents.ets:175`） | 正常 |
| AC-1.4 | WHEN `ExtendedWeb` 构建 THEN 使用 `@kit.ArkWeb` 的 `Web({ src: currentUrl, controller: webviewController })`（`ExtendedWeb.ets:21,44,70`） | 正常 |

### US-2: url 解析

**作为** 生成式 UI 宿主开发者,
**我想要** `url` 支持静态字符串与动态值,
**以便** 地址随数据模型/表达式/函数调用更新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `url` 为静态字符串 THEN `resolveDynamicStringOptionValue` 返回该串（`ExtendedWeb.ets:107`） | 正常 |
| AC-2.2 | WHEN `url` 为动态值（表达式/路径/函数调用） THEN 经 `resolveDynamicStringOptionValue(parsed['url'], attribute)` 解析（`ExtendedWeb.ets:107`） | 正常 |
| AC-2.3 | WHEN `parseCustomProps` 返回 undefined THEN `resolveOptions` 返回 `{ url: DEFAULT_WEB_URL }`（空串）（`ExtendedWeb.ets:100-105,32`） | 异常 |
| AC-2.4 | WHEN `url` 解析结果 undefined THEN 回退 `DEFAULT_WEB_URL`（空串）（`ExtendedWeb.ets:109-111`） | 边界 |

### US-3: url 惰性加载与异常保护

**作为** 生成式 UI 宿主开发者,
**我想要** 仅在必要时加载页面且加载失败不崩溃,
**以便** 避免空/重复加载并保证组件稳定。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 新 url 为空 或 旧 url 为空 或 新旧相等 THEN `updateUrl` 直接返回不加载（`ExtendedWeb.ets:62-64`） | 边界 |
| AC-3.2 | WHEN 新 url 非空 且 旧 url 非空 且 不等 THEN 调用 `loadUrlSafely(url)`（`ExtendedWeb.ets:66`） | 正常 |
| AC-3.3 | WHEN `loadUrlSafely` 调用 `webviewController.loadUrl(url)` 成功 THEN 打成功日志（`ExtendedWeb.ets:114-117`） | 正常 |
| AC-3.4 | WHEN `loadUrl` 抛异常 THEN catch 后打告警日志，不向上抛出（`ExtendedWeb.ets:114-121`） | 异常 |
| AC-3.5 | WHEN url 为空 THEN `Web` 以空 `src` 渲染，无额外 fallback 文案（`ExtendedWeb.ets:70`） | 边界 |

### US-4: 生命周期与属性变更触发更新

**作为** 生成式 UI 宿主开发者,
**我想要** 组件出现与属性变更时重新解析 url,
**以便** 数据模型更新驱动页面刷新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `aboutToAppear` 触发 THEN 调用 `updateUrl`（`ExtendedWeb.ets:46-49`） | 正常 |
| AC-4.2 | WHEN `onAttributeChange`（`@Watch` 属性变更）触发 THEN 调用 `updateUrl`（`ExtendedWeb.ets:51-54`） | 正常 |
| AC-4.3 | WHEN `updateUrl` 解析新 url 且满足加载条件 THEN `currentUrl` 先更新为 url（`ExtendedWeb.ets:59-60`） | 正常 |

### US-5: 事件与无障碍

**作为** 生成式 UI 宿主开发者,
**我想要** Web 组件支持点击/出现事件与无障碍分组,
**以便** 事件派发与无障碍访问一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `onClick`/`onAppear` 触发 THEN 各经 `dispatchComponentEvent` 派发（`ExtendedWeb.ets:71-76`） | 正常 |
| AC-5.2 | WHEN 构建 THEN `accessibilityGroup(true)` 且 `accessibilityText`/`accessibilityDescription` 下发（`ExtendedWeb.ets:77-79`） | 正常 |
| AC-5.3 | WHEN `resolveExtendedWebLayoutWeight` 且 `properties.weight > 0` THEN 返回 weight，否则 0（`ExtendedWeb.ets:34-37`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-4 | ArkTS 静态比对：定义 + 渲染 | `ExtendedWeb.ets:21,31,70,129-138`、`A2UIExtendedComponents.ets:168-183` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-4 | ArkTS 单测：url 解析 | `ExtendedWeb.ets:88-112` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-4 | ArkTS 单测：惰性加载/异常保护 | `ExtendedWeb.ets:56-67,114-121` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-4 | ArkTS 单测：生命周期触发 | `ExtendedWeb.ets:46-54` |
| AC-5.1,AC-5.2,AC-5.3 | R-5 | T-4 | ArkTS 单测：事件/无障碍 | `ExtendedWeb.ets:34-37,71-79` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | descriptor `component=="Web"` | 注册为 ArkTS 扩展自定义组件，`@kit.ArkWeb` 渲染 | 经 `getExtendedCustomDefinitions` 聚合 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 边界 | url 解析 | 静态/动态解析，失败/缺失回退空串 | `DEFAULT_WEB_URL=''` | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 边界 | url 惰性加载 | 仅新非空、旧非空、且不等时加载 | 异常 try/catch 兜底 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 行为 | 生命周期触发 | 出现/属性变更均 `updateUrl` | `@Watch` 属性变更 | AC-4.1,AC-4.2,AC-4.3 |
| R-5 | 行为 | 事件/无障碍 | onClick/onAppear 派发 + accessibilityGroup | weight>0 才生效 | AC-5.1,AC-5.2,AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 注册/识别 | 静态比对 | type='Web'、schemaProvider、@kit.ArkWeb |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 url 解析 | ArkTS 单测 | 静态/动态/缺失回退 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 惰性加载 | ArkTS 单测 | 加载条件、异常保护 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 生命周期 | ArkTS 单测 | aboutToAppear/onAttributeChange |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 事件/无障碍 | ArkTS 单测 | onClick/onAppear/accessibilityGroup |

## API 变更分析

> 存量补录，无新增/变更公开 ArkTS/C-API。本节列出受影响组件协议。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Web` 扩展组件协议（`url`） | 既有 | 网页内容嵌入 | url 支持静态/动态值 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3,AC-5.1,AC-5.2,AC-5.3 |
| `ExtendedWeb`（内部 ArkTS 组件） | 既有 | 网页渲染/加载 | 不直接暴露给宿主 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3 |

> Schema 位置：`genui/src/main/resources/rawfile/schema/Extended/components/ExtendedWeb.json`（required `["component", "url"]`，properties `["component", "url"]`）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`createExtendedWebDefinition()`（`ExtendedWeb.ets:129`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `createExtendedWebDefinition(): CustomComponentDefinition` |
| 返回值 | `CustomComponentDefinition` — 含 `type/builder/schemaProvider` |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2 |

**`ExtendedWeb.updateUrl()`（内部，`ExtendedWeb.ets:56`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `private updateUrl(): void` |
| 返回值 | `void` |
| 开放范围 | 内部 |
| 错误码 | N/A（loadUrl 异常经 try/catch 兜底） |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| url | string/dynamic | 否（schema 标必填，运行时容忍缺失） | `''` | 静态/表达式/路径/函数调用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | url 静态字符串 | 以该地址渲染 | AC-2.1 |
| 2 | url 动态值变化 | 满足条件时加载新地址 | AC-3.2,AC-4.3 |
| 3 | url 缺失/解析失败 | 回退空串，不加载 | AC-2.3,AC-2.4,AC-3.5 |
| 4 | 首次出现（旧 url 空） | 不主动加载（惰性） | AC-3.1,AC-4.1 |
| 5 | loadUrl 抛异常 | 告警日志，不崩溃 | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API Version 20；鸿蒙扩展协议 1.0.0。
- **API 版本号策略:** 组件协议经 JSON Schema 约束；无 `@since` 标注差异。
- **Schema 与运行时不一致:** `ExtendedWeb.json` 要求 `url` 必填（`required:["component","url"]`），运行时容忍缺失回退空串（`ExtendedWeb.ets:110`）——见 RISK-2。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| ArkTS 自定义组件 | Web 走 ArkTS 而非 native（`getExtendedCustomDefinitions` 注册） | AC-1.1,AC-1.2,AC-1.3 |
| 惰性加载 | 仅新非空 + 旧非空 + 变化时加载 | AC-3.1,AC-3.2,AC-3.3 |
| 异常保护 | loadUrl 异常 try/catch 兜底不崩溃 | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 url/加载异常不崩溃，回退空 src 或告警 | ArkTS 单测 | `ExtendedWeb.ets:114-121` |
| 性能 | 空/重复 url 不触发加载 | ArkTS 单测 | `ExtendedWeb.ets:62-64` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 系统 Web 通用能力 | ohosTest | `ExtendedWeb.ets:69-86` |
| 平板 | 无差异 | 同上 | ohosTest | 同上 |
| 折叠屏 | 无差异 | 同上 | ohosTest | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityGroup(true)` + `accessibilityText`/`accessibilityDescription` | AC-5.2 |
| 大字体 | 否 | 不涉及（Web 内容自身控制） | — |
| 深色模式 | 否 | 组件默认背景色不随主题切换（见 web.md） | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API Version 20；扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | 鸿蒙扩展协议组件 | 概述 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Web 扩展网页容器
  作为 生成式 UI 宿主开发者
  我想要 通过 url 嵌入网页内容
  以便 页面内展示 Web 内容且加载失败不崩溃

  Scenario: 静态 url 渲染
    Given DSL 含 {"component":"Web","id":"w","url":"https://example.com"}
    When 引擎渲染 Web
    Then 以 https://example.com 为 src 渲染 Web 视图

  Scenario: url 动态更新触发加载
    Given url 绑定 { "path": "/webState/url" } 且数据从 a.com 变为 b.com
    When 属性更新触发 updateUrl
    Then 调用 loadUrl(b.com)

  Scenario Outline: url 边界处理
    Given Web 声明 <what>
    When 解析/加载 url
    Then <expected>

    Examples:
      | what | expected |
      | url 缺失 | 回退空串，不加载 |
      | url 为空串 | 以空 src 渲染 |
      | loadUrl 抛异常 | 告警日志，不崩溃 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（扩展 Web 容器 url 加载语义；WebView 内部能力不涉及）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedWeb updateUrl resolveUrl resolveOptions loadUrlSafely url 惰性加载"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedWeb build Web webviewController accessibilityGroup onClick onAppear"
  - repo: "GenerativeUI/A2UIRender"
    query: "createExtendedWebDefinition schemaProvider ExtendedWeb.json required url"
```

**关键文档：** `genui/src/main/ets/core/components/extended/ExtendedWeb.ets`、`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`、`genui/src/main/resources/rawfile/schema/Extended/components/ExtendedWeb.json`