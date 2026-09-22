# 特性规格

> Func-07-04-02-Feat-03 List 组件：固化 A2UI 标准可滚动列表容器 List 的语义——目录注册（`type='List'`、`A2UI_STANDARD`、`isInnerNative`）、私有属性 `direction`/`align` 的字符串 token→ArkUI 枚举映射与非法回退、`children` 静态 ID 数组（EAGER 包裹 `LIST_ITEM`）/模板对象（LAZY NodeAdapter 懒加载）二态渲染、`itemCount` 解析的缺省/异常策略。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | List 组件 |
| 特性编号 | Func-07-04-02-Feat-03 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性与 Feat-01/02 共享同一功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/02-a2ui-standard-layout-components/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIList.ets` | — |
| 组件实现（C++） | `genui/src/main/cpp/components/A2UI/list/ListComponent.{h,cpp}` | — |
| 主题（C++） | `genui/src/main/cpp/components/A2UI/list/ListTheme.{h,cpp}` | — |
| 子列表解析（C++） | `genui/src/main/cpp/composition/ChildListParser.{h,cpp}` | — |
| 组件 Schema | `specification/A2UI/v0_9/catalogs/basic/catalog.json`（List 段） | 契约 |
| 组件参考（Docs） | `reference/standard-components/list.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: List 目录注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `component: "List"` 识别为标准原生可滚动列表容器,
**以便** 服务端下发的 List 组件能被正确渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `A2UIList.asCatalogItem()` THEN 返回 `CatalogItem`，其 name 为 `'List'`（`A2UIList.ets:24,30-34`） | 正常 |
| AC-1.2 | WHEN 构造目录项 THEN `markCategory(A2UI_STANDARD)` 与 `markInnerNative(true)` 均被调用（`A2UIList.ets:33`） | 正常 |
| AC-1.3 | WHEN schemaProvider 以 version 参数被调用 THEN 经 `SchemaResourceLoader.loadA2UISchema(version, 'components/List.json')` 返回 List schema（`A2UIList.ets:26-28`） | 正常 |
| AC-1.4 | WHEN `A2UIBasicComponents.allA2UIBasicComponents()` 被调用 THEN 返回的目录项数组包含 `A2UIList.asCatalogItem()`（`A2UIBasicComponents.ets:48`） | 正常 |

### US-2: 列表方向（direction）枚举映射

**作为** 生成式 UI 宿主开发者,
**我想要** List 支持纵向/横向两种排列方向,
**以便** 服务端可指定列表项的滚动方向。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN descriptor 的 `direction` 为 `"vertical"` THEN `SetDirection(A2UIAxis::VERTICAL)` 落盘（`ListComponent.cpp:56-63`） | 正常 |
| AC-2.2 | WHEN `direction` 为 `"horizontal"` THEN `SetDirection(A2UIAxis::HORIZONTAL)`（`ListComponent.cpp:58-60`） | 正常 |
| AC-2.3 | WHEN `direction` 缺省或为非法值 THEN 使用 fallback 值 `"vertical"`（`ListComponent.cpp:53,55,57`） | 边界 |
| AC-2.4 | WHEN `children` 为模板对象且 `direction="vertical"` THEN 不改变懒加载路径，仍走 `SetupLazyAdapter`（`list.md:96-97`） | 正常 |

### US-3: 交叉轴对齐（align）枚举映射

**作为** 生成式 UI 宿主开发者,
**我想要** List 控制列表项在交叉轴的对齐,
**以便** 通过 `align` 属性对齐列表项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `align` 为 `"start"` THEN `SetAlign(A2UIListItemAlignment::START)`（`ListComponent.cpp:75-76`） | 正常 |
| AC-3.2 | WHEN `align` 为 `"center"` THEN `SetAlign(A2UIListItemAlignment::CENTER)`（`ListComponent.cpp:77-78`） | 正常 |
| AC-3.3 | WHEN `align` 为 `"end"` THEN `SetAlign(A2UIListItemAlignment::END)`（`ListComponent.cpp:79-80`） | 正常 |
| AC-3.4 | WHEN `align` 取非法值 THEN 走 else 分支回退 `SetAlign(START)`（`ListComponent.cpp:81-83`） | 边界 |
| AC-3.5 | WHEN `align` 缺省 THEN 使用 fallback 值 `"start"`（`ListComponent.cpp:70,72,74`） | 边界 |

### US-4: 静态子组件（EAGER 包裹 LIST_ITEM）

**作为** 生成式 UI 宿主开发者,
**我想要** List 在静态子组件模式下用原生 LIST_ITEM 包裹每个子项,
**以便** 列表项结构符合 ArkUI List 语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `children` 为字符串数组且 mode=EAGER THEN 每个子组件被 `CreateNode(LIST_ITEM)` 包裹后加入列表（`ListComponent.cpp:236-248`） | 正常 |
| AC-4.2 | WHEN `listItems_` 非空 THEN `RemoveAllChildren` 逐项 `RemoveChild`+`DisposeNode` 并清空（`ListComponent.cpp:265-280`） | 正常 |
| AC-4.3 | WHEN List 析构 THEN 残留 `listItems_` 被逐项 `DisposeNode` 释放（`ListComponent.cpp:29-38`） | 异常 |
| AC-4.4 | WHEN 子组件在 LAZY 模式加入 THEN `OnAddChild` 跳过包裹（因子组件由 LazyForEach 创建）（`ListComponent.cpp:238-242`） | 边界 |

### US-5: 模板子组件（LAZY NodeAdapter 懒加载）

**作为** 生成式 UI 宿主开发者,
**我想要** List 在模板对象模式下用 NodeAdapter 懒加载渲染,
**以便** 大数据量列表按需渲染而不全量展开。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `children` 为含 `componentId`+`path` 的模板对象 THEN `ExpandTemplateChildren` 构建 `LazyAdapterConfig` 并 `SetupLazyAdapter`（`ListComponent.cpp:209-234`） | 正常 |
| AC-5.2 | WHEN 模板 componentId 在 descriptor store 中不存在 THEN 打 WARN 并返回 false（不建 adapter）（`ListComponent.cpp:215-221`） | 异常 |
| AC-5.3 | WHEN `SetupLazyAdapter` 创建新 adapter THEN `SetLazyMode(true)`+`SetAdapterNode` 应用 `NODE_LIST_NODE_ADAPTER`（`ListComponent.cpp:186-201`、`:105-125`） | 正常 |
| AC-5.4 | WHEN adapter 已存在 THEN 走 `ReloadAllItems()` 重建而非重复建 adapter（`ListComponent.cpp:199-201`） | 正常 |

### US-6: itemCount 解析与缺省/异常策略

**作为** 生成式 UI 宿主开发者,
**我想要** List 懒加载项数在数据未就绪时优雅降级,
**以便** 流式数据延迟到达时不崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `templatePath` 为相对路径（不以 `/` 开头） THEN `ResolveLazyAdapterItemCount` 返回 0（运行期解析）（`ListComponent.cpp:146-151`） | 边界 |
| AC-6.2 | WHEN `dataModel` 为 null THEN 返回 `std::nullopt`，`SetupLazyAdapter` 提前返回不建 adapter（`ListComponent.cpp:153-157`、`:132-134`） | 异常 |
| AC-6.3 | WHEN path 在 data model 中未找到 THEN 经 `DynamicValueResolver::ReportMissingPath(DEFER_UNTIL_DATA_UPDATE)` 上报并返回 0（空 adapter）（`ListComponent.cpp:159-170`） | 异常 |
| AC-6.4 | WHEN path 对应数据非数组 THEN 返回 0（空 adapter）（`ListComponent.cpp:172-177`） | 边界 |
| AC-6.5 | WHEN path 为合法数组 THEN 返回 `GetArraySize()` 作为 itemCount（`ListComponent.cpp:179-181`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-3 | ArkTS 单测：目录项注册 | `A2UIList.ets:24-34`、`A2UIBasicComponents.ets:48` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2,R-6 | T-3 | ohosTest：`dynamic/list/DynamicListListDirection` | `ListComponent.cpp:48-64` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3,R-6 | T-3 | C++ UT/ohosTest：align 映射 | `ListComponent.cpp:65-85` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4 | T-3 | ohosTest：`entry/src/test/List.test.ets` | `ListComponent.cpp:236-248,265-280` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4 | R-5 | T-3 | ohosTest：模板列表懒加载 | `ListComponent.cpp:184-234` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 | R-7 | T-3 | C++ UT：`ResolveLazyAdapterItemCount` | `ListComponent.cpp:144-182` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 调用 `asCatalogItem()` | 返回 name=`List`、`A2UI_STANDARD`、`isInnerNative=true` 的目录项 | 仅内部注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | `direction` 取值为 `vertical/horizontal` | 映射为 `A2UIAxis` 的 VERTICAL/HORIZONTAL | 枚举二值 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 行为 | `align` 取值为 `start/center/end` | 映射为 `A2UIListItemAlignment` 的 START/CENTER/END | 枚举三值 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 行为 | EAGER 模式加入子组件 | 每个子组件包裹 `LIST_ITEM` 节点 | LAZY 模式跳过包裹 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-5 | 行为 | 模板 children 展开 | 构建 `LazyAdapterConfig` 并应用 NodeAdapter | 模板不存在返回 false | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| R-6 | 边界 | `direction`/`align` 缺省或非法 token | 回退默认 `vertical`/`start` | 非法 token 不回抛异常 | AC-2.3,AC-3.4,AC-3.5 |
| R-7 | 恢复 | itemCount 无法确定 | 相对路径→0、dataModel null→放弃、path 未找到/非数组→空 adapter | 流式数据延迟到达不崩溃 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 目录注册 | ArkTS 单测 | type/类别/原生标记 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 direction 映射 | ohosTest | vertical/horizontal 与回退 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 align 映射 | C++ UT | start/center/end 与回退 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 EAGER 包裹 LIST_ITEM | ohosTest | LIST_ITEM 包裹与释放 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 LAZY NodeAdapter | ohosTest | 懒加载 adapter 应用 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 itemCount 解析 | C++ UT | 相对路径/空模型/缺路径/非数组/正常 |

## API 变更分析

> 存量补录，无新增/变更 Public API。组件经内部 `CatalogItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `A2UIList.asCatalogItem()`（内部） | 既有 | 目录项构造 | 不直接暴露给宿主 | AC-1.1,AC-1.2,AC-1.3 |
| `ListComponent::SetDirection/SetAlign/SetLazyMode/SetupLazyAdapter`（内部） | 既有 | 属性落盘与懒加载 | 框架内部 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-5.1,AC-5.2,AC-5.3,AC-5.4 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIList.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`A2UIList.asCatalogItem()`（内部，`A2UIList.ets:30`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static asCatalogItem(): CatalogItem` |
| 返回值 | `CatalogItem` — name=`List`、category=`A2UI_STANDARD`、isInnerNative=true |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**`ListComponent::ResolveLazyAdapterItemCount(config)`（`ListComponent.h:93`、`ListComponent.cpp:144`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `std::optional<int32_t> ResolveLazyAdapterItemCount(const LazyAdapterConfig& config) const` |
| 返回值 | `optional<int32_t>` — 相对路径/缺路径/非数组→0；dataModel null→nullopt；正常→数组大小 |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |

**`ListComponent::SetupLazyAdapter(config)`（`ListComponent.h:56`、`ListComponent.cpp:127`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void SetupLazyAdapter(const LazyAdapterConfig& config)` |
| 返回值 | `void` — 配置 NodeAdapter 或静默返回（itemCount 不可用） |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-6.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| direction | string | 否 | `"vertical"` | 取值 `vertical`/`horizontal`，非法回退 `vertical` |
| align | string | 否 | `"start"` | 取值 `start`/`center`/`end`，非法回退 `start` |
| children | array/object | 是 | — | 非空 ID 数组或 `{componentId,path}` |
| LazyAdapterConfig.templatePath | string | 是 | — | 绝对路径（`/` 开头）或相对路径（延迟解析） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | direction=`"vertical"` | 纵向列表 | AC-2.1 |
| 2 | direction=`"horizontal"` | 横向列表 | AC-2.2 |
| 3 | direction 非法/缺省 | 回退 vertical | AC-2.3 |
| 4 | align=`"center"` | 交叉轴居中 | AC-3.2 |
| 5 | children 静态数组 + EAGER | 包裹 LIST_ITEM 渲染 | AC-4.1 |
| 6 | children 模板对象 | LAZY NodeAdapter 渲染 | AC-5.1 |
| 7 | templatePath 相对路径 | itemCount=0 延迟解析 | AC-6.1 |
| 8 | dataModel null | 放弃建 adapter | AC-6.2 |
| 9 | path 未找到/非数组 | 空 adapter + missing path 上报 | AC-6.3,AC-6.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** 组件 schema 由 `components/List.json` 声明；EAGER↔LAZY 模式切换非对称（`SetLazyMode(false)` 不回收 adapter），标注于 RISK-4。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 组件三件套 | 注册/实现/主题三层落地，职责单一 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| 双态渲染 | EAGER 包裹 LIST_ITEM；LAZY 用 NodeAdapter | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| 枚举回退 | 非法 token 一律回退默认值，不抛异常 | AC-2.3,AC-3.4 |
| 缺省优雅降级 | itemCount 不可用时不崩溃，空 adapter/放弃 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 数据模型未就绪时优雅降级不崩溃 | C++ UT | `ListComponent.cpp:153-177` |
| 性能 | LAZY 模式按需渲染（NodeAdapter），避免全量展开 | ohosTest | `ListComponent.cpp:105-125` |
| 内存 | 析构/RemoveAllChildren 释放全部 listItems_ | ohosTest | `ListComponent.cpp:29-38,265-280` |
| 可测试性 | `ResolveLazyAdapterItemCount` 为纯函数 | C++ UT | `ListComponent.cpp:144-182` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 列表方向/对齐与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 断点主题重应用归 07-04-23 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 列表项 accessibility 透传（归 07-04-18） | `Component.cpp:1566` |
| 大字体 | 否 | 列表容器不涉及字号 | — |
| 深色模式 | 否 | 主题重应用为空实现（RISK-3） | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 协议 v0.9 组件 schema | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 List 兼容 | `catalog.json:376-422` |

## 行为场景（可选，Gherkin）

```gherkin
Feature: List 组件
  作为 生成式 UI 宿主开发者
  我想要 List 可滚动渲染列表项并支持懒加载
  以便 高效呈现同类数据

  Scenario: 静态列表项渲染
    Given DSL 组件为 {"component":"List","id":"demo","children":["item3","item4"]}
    When 引擎应用组件描述
    Then 每个子组件被原生 LIST_ITEM 包裹后加入 List

  Scenario: 模板懒加载数据未就绪
    Given List children 为 {"componentId":"tpl","path":"/items"} 且数据模型尚未包含 /items
    When 引擎展开模板子组件
    Then 空 adapter 建立并上报 missing path，不崩溃

  Scenario Outline: direction 枚举映射
    Given List 组件 direction 为 <token>
    When 引擎解析 direction 属性
    Then 映射为 <axis> 落盘

    Examples:
      | token      | axis       |
      | vertical   | VERTICAL   |
      | horizontal | HORIZONTAL |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做 List 列表布局；通用属性归 07-04-18，模板/数据绑定归 07-04-17/21）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "A2UIList.asCatalogItem List 组件目录注册 markCategory markInnerNative"
  - repo: "GenerativeUI/A2UIRender"
    query: "ListComponent SetDirection SetAlign SetLazyMode SetupLazyAdapter NodeAdapter 懒加载"
  - repo: "GenerativeUI/A2UIRender"
    query: "ListComponent ResolveLazyAdapterItemCount 相对路径 defer 空 adapter DEFER_UNTIL_DATA_UPDATE"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/A2UIList.ets`、`genui/src/main/cpp/components/A2UI/list/ListComponent.cpp`、`genui/src/main/cpp/components/A2UI/list/ListTheme.cpp`、`genui/src/main/cpp/composition/ChildListParser.cpp`、`specification/A2UI/v0_9/catalogs/basic/catalog.json`