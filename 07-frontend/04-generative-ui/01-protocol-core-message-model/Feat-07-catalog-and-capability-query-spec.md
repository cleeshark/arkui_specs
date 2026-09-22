# 特性规格

> Func-07-04-01-Feat-07 Catalog 与能力查询：固化 `Catalog`/`CatalogItem`/`ClientFunction` 注册契约、`CatalogImpl` 归一化、`CatalogFactory.basic()/extended()/createCatalog()` 工厂、`CapabilitiesCore.getCapabilities()` 能力清单（协议版本/catalogId 集）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Catalog 与能力查询 |
| 特性编号 | Func-07-04-01-Feat-07 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Feat-07 承接 design.md Catalog/能力章节 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/01-protocol-core-message-model/design.md` | Baselined |
| Catalog 接口 | `genui/src/main/ets/interface/Catalog.ets` / `CatalogItem.ets` | — |
| Catalog 实现 | `genui/src/main/ets/core/base/CatalogImpl.ets` | — |
| 能力核心 | `genui/src/main/ets/core/base/CapabilitiesCore.ets` | — |
| Catalog（C++） | `genui/src/main/cpp/catalog/Catalog.cpp` / `Catalog.h` | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 组件定义注册

**作为** 生成式 UI 宿主开发者,
**我想要** 向 Catalog 注册自定义组件,
**以便** DSL 按名字引用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `addCatalogItem(item)` 且 item 合法 THEN 添加到组件列表（同名替换）（`CatalogImpl.ets:73-80,123-130`） | 正常 |
| AC-1.2 | WHEN `removeCatalogItem(name)` 命中 THEN 移除并返回 true（`CatalogImpl.ets:82-84`） | 正常 |
| AC-1.3 | WHEN `hasCatalogItem(name)` THEN 返回是否存在（`CatalogImpl.ets:86-88`） | 正常 |
| AC-1.4 | WHEN `getAllCatalogItemNames()` THEN 返回全部组件名（`CatalogImpl.ets:90-92`） | 正常 |
| AC-1.5 | WHEN item 为 null/undefined 或 name 为空 THEN `normalizeComponentItem` 返回 undefined（`CatalogImpl.ets:162-164`） | 边界 |

### US-2: 本地函数注册

**作为** 生成式 UI 宿主开发者,
**我想要** 向 Catalog 注册本地函数,
**以便** DSL 按名字调用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `addClientFunction(fn)` 且 fn 合法 THEN 加入函数映射（同名替换）（`CatalogImpl.ets:94-101`） | 正常 |
| AC-2.2 | WHEN `hasClientFunction(name)` 命中 THEN 返回 true（`CatalogImpl.ets:111-113`） | 正常 |
| AC-2.3 | WHEN 函数 schemaProvider 返回非完整函数 schema THEN 包一层 `{call,args,returnType}` 包装 schema（`CatalogImpl.ets:192-232`） | 正常 |
| AC-2.4 | WHEN schemaProvider 返回空串或完整 schema THEN 原样返回（`CatalogImpl.ets:194-196`） | 边界 |

### US-3: 工厂与目录 id

**作为** 生成式 UI 宿主开发者,
**我想要** 用工厂创建预置目录,
**以便** 快速接入标准/扩展协议。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `CatalogFactory.basic()` THEN 返回 basic catalog（`Factories.ets:32-34`） | 正常 |
| AC-3.2 | WHEN `CatalogFactory.extended()` THEN 返回 extended catalog（`Factories.ets:41-43`） | 正常 |
| AC-3.3 | WHEN `CatalogFactory.createCatalog(id, components, clientFunctions)` THEN 返回自定义目录（`Factories.ets:53-55`） | 正常 |
| AC-3.4 | WHEN `fromPublicOrEmpty` 传入非 CatalogImpl 实例 THEN 返回空 catalog 并打错误日志（`CatalogImpl.ets:46-52`） | 异常 |

### US-4: 能力清单

**作为** 生成式 UI 宿主开发者,
**我想要** 查询引擎支持的能力,
**以便** 运行时适配。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `getCapabilities()` THEN 返回 `supportedA2UIProtocolVersions=['v0.9']`、`supportedExtendedProtocolVersions`、`supportedCatalogIds=[basic, extended]`（`CapabilitiesCore.ets:55-65`） | 正常 |
| AC-4.2 | WHEN `getSupportedA2UIProtocolVersions()` THEN 返回 `['v0.9']` 副本（防外部篡改）（`CapabilitiesCore.ets:43-45`） | 正常 |
| AC-4.3 | WHEN basic catalogId THEN 值为 `https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json`（`CapabilitiesCore.ets:18`） | 正常 |
| AC-4.4 | WHEN extended catalogId THEN 值为 `ohos.a2ui.extended.catalog`（`CapabilitiesCore.ets:19`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-7 | ArkTS 单测：组件注册 | `CatalogImpl.ets:73-92` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-7 | ArkTS 单测：函数注册 | `CatalogImpl.ets:94-113` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-7 | ArkTS 单测：工厂 | `Factories.ets:32-55` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4 | T-7 | ArkTS 单测：能力清单 | `CapabilitiesCore.ets:18-65` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 组件注册 | 同名替换、删除/查询返回 bool | 非法项忽略 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | 函数注册 | 加入映射 + schema 包装 | 非完整 schema 才包装 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 行为 | 工厂创建 | basic/extended/自定义目录 | 非法实例返回空目录 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 行为 | 能力查询 | 返回协议版本/catalogId 清单 | 副本防篡改 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 组件注册 | ArkTS 单测 | 同名替换 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 函数注册 | ArkTS 单测 | schema 包装 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 工厂 | ArkTS 单测 | 预置目录 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 能力清单 | ArkTS 单测 | 常量值 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Catalog`（addCatalogItem/addClientFunction 等） | 既有 | 自定义组件/函数注册 | — | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| `CatalogFactory`/`SurfaceControllerFactory` | 既有 | 目录/控制器创建 | — | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

## 接口规格

### 接口定义

**`CatalogFactory.basic()/extended()/createCatalog()`（`Factories.ets:32-55`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static basic(): Catalog` / `static extended(): Catalog` / `static createCatalog(id, components, clientFunctions): Catalog` |
| 返回值 | `Catalog` |
| 开放范围 | Public（ArkTS） |
| 错误码 | N/A |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3 |

**`CapabilitiesCore.getCapabilities()`（`CapabilitiesCore.ets:55`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static getCapabilities(): CapabilityManifestCore` |
| 返回值 | `CapabilityManifestCore` — 协议版本/catalogId 清单 |
| 开放范围 | 内部 |
| 关联 AC | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 注册同名组件 | 替换旧定义 | AC-1.1 |
| 2 | 非完整函数 schema | 包装 call/args/returnType | AC-2.3 |
| 3 | 查询能力 | 返回 v0.9 + 双 catalogId | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 无新增 API。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 目录单源 | CatalogImpl 归一化组件/函数 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 能力常量双端同步 | CapabilitiesCore vs SurfaceContext.h | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 安全 | 能力清单副本防篡改 | ArkTS 单测 | `CapabilitiesCore.ets:43-45` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | — | ohosTest | — |
| 平板 | 无差异 | — | ohosTest | — |
| 折叠屏 | 无差异 | — | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | — | — |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | 协议版本能力查询 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| 生态兼容 | 是 | basic/extended catalogId 常量 | AC-4.3,AC-4.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Catalog 与能力查询
  作为 生成式 UI 宿主开发者
  我想要 注册组件/函数并查询能力
  以便 运行时适配与扩展

  Scenario: 同名组件替换
    Given Catalog 已注册 name="Text"
    When 再次 addCatalogItem(name="Text")
    Then 替换旧定义而非重复添加

  Scenario: 能力清单查询
    Given CapabilitiesCore
    When getCapabilities()
    Then 返回 supportedA2UIProtocolVersions=["v0.9"] 与双 catalogId
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（自定义组件/函数语义归 07-04-20）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过质量检查

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CatalogImpl addCatalogItem addClientFunction schema 包装 normalizeComponentItem"
  - repo: "GenerativeUI/A2UIRender"
    query: "CapabilitiesCore getCapabilities supportedCatalogIds A2UI_BASIC_CATALOG_ID A2UI_EXTENDED_CATALOG_ID"
  - repo: "GenerativeUI/A2UIRender"
    query: "CatalogFactory basic extended createCatalog SurfaceControllerFactory"
```

**关键文档：** `genui/src/main/ets/core/base/CatalogImpl.ets`、`genui/src/main/ets/core/base/CapabilitiesCore.ets`、`genui/src/main/ets/interface/Factories.ets`、`genui/src/main/cpp/catalog/Catalog.cpp`