# 特性规格

> Func-07-04-02-Feat-01 Row 组件：固化 A2UI 标准布局容器 Row 的水平排列语义——目录注册（`type='Row'`、`A2UI_STANDARD`、`isInnerNative`）、私有属性 `align`/`justify` 的字符串 token→ArkUI 枚举映射与非法回退、`children` 静态 ID 数组/模板对象二态解析与 Eager 展开、16.0vp 默认子组件间距。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Row 组件 |
| 特性编号 | Func-07-04-02-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-02 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/02-a2ui-standard-layout-components/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIRow.ets` | — |
| 组件实现（C++） | `genui/src/main/cpp/components/A2UI/row/RowComponent.{h,cpp}` | — |
| 主题/枚举解析（C++） | `genui/src/main/cpp/components/A2UI/row/RowTheme.{h,cpp}` | — |
| 子列表解析（C++） | `genui/src/main/cpp/composition/ChildListParser.{h,cpp}` | — |
| 组件 Schema | `specification/A2UI/v0_9/catalogs/basic/catalog.json`（Row 段） | 契约 |
| 组件参考（Docs） | `reference/standard-components/row.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Row 目录注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `component: "Row"` 识别为标准原生布局容器,
**以便** 服务端下发的 Row 组件能被正确渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `A2UIRow.asCatalogItem()` THEN 返回 `CatalogItem`，其 name 为 `'Row'`（`A2UIRow.ets:25,31-35`） | 正常 |
| AC-1.2 | WHEN 构造目录项 THEN `markCategory(A2UI_STANDARD)` 与 `markInnerNative(true)` 均被调用，即 category=0、isInnerNative=true（`A2UIRow.ets:34`） | 正常 |
| AC-1.3 | WHEN schemaProvider 以 version 参数被调用 THEN 经 `SchemaResourceLoader.loadA2UISchema(version, 'components/Row.json')` 返回 Row schema（`A2UIRow.ets:27-29`） | 正常 |
| AC-1.4 | WHEN `A2UIBasicComponents.allA2UIBasicComponents()` 被调用 THEN 返回的目录项数组包含 `A2UIRow.asCatalogItem()`（`A2UIBasicComponents.ets:44`） | 正常 |

### US-2: 交叉轴对齐（align）枚举映射

**作为** 生成式 UI 宿主开发者,
**我想要** Row 沿垂直方向对齐子组件,
**以便** 通过 `align` 属性控制子组件顶部/居中/底部对齐。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN descriptor 的 `align` 为 `"start"` THEN `RowTheme::ResolveAlignItems` 返回 `A2UIVerticalAlignment::TOP`（`RowTheme.cpp:49-51`），并经 `SetAlignItems` 落盘（`RowComponent.cpp:39,68-71`） | 正常 |
| AC-2.2 | WHEN `align` 为 `"center"` THEN 返回 `A2UIVerticalAlignment::CENTER`（`RowTheme.cpp:52-54`） | 正常 |
| AC-2.3 | WHEN `align` 为 `"end"` THEN 返回 `A2UIVerticalAlignment::BOTTOM`（`RowTheme.cpp:55-57`） | 正常 |
| AC-2.4 | WHEN `align` 缺省或为非法值 THEN 使用 fallback 值 `"start"`，映射为 `TOP`（`RowComponent.cpp:35,37`、`RowTheme.cpp:58-59`） | 边界 |

### US-3: 主轴排列（justify）枚举映射

**作为** 生成式 UI 宿主开发者,
**我想要** Row 沿水平方向排列子组件,
**以便** 通过 `justify` 控制子组件在主轴的分布。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `justify` 为 `"start"`/`"center"`/`"end"` THEN `ResolveJustifyContent` 分别返回 `START`/`CENTER`/`END`（`RowTheme.cpp:64-72`） | 正常 |
| AC-3.2 | WHEN `justify` 为 `"spaceAround"`/`"spaceBetween"`/`"spaceEvenly"` THEN 分别返回 `SPACE_AROUND`/`SPACE_BETWEEN`/`SPACE_EVENLY`（`RowTheme.cpp:73-81`） | 正常 |
| AC-3.3 | WHEN `justify` 缺省或为非法值 THEN 使用 fallback 值 `"start"`，映射为 `START`（`RowComponent.cpp:47,49`、`RowTheme.cpp:82-83`） | 边界 |
| AC-3.4 | WHEN `justify` 合法 THEN 经 `SetJustifyContent` 调用 `ArkUINodeApiAdapter::SetNodeRowJustifyContent` 落盘（`RowComponent.cpp:73-76`） | 正常 |

### US-4: 子组件列表解析与模板展开

**作为** 生成式 UI 宿主开发者,
**我想要** Row 支持静态 ID 数组与模板对象两种子组件描述,
**以便** 既渲染固定集合又从数据列表动态生成子组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `children` 为字符串数组 THEN `ChildListParser::ParseChildren` 返回 `ChildListType::STATIC_IDS` 并收集非空子组件 id（`ChildListParser.cpp:66-75`） | 正常 |
| AC-4.2 | WHEN `children` 为含 `componentId` 与 `path` 的对象 THEN 返回 `ChildListType::TEMPLATE_PATH`（`ChildListParser.cpp:78-87`） | 正常 |
| AC-4.3 | WHEN `children` 为空/非法结构 THEN 返回 `ChildListType::INVALID`（`ChildListParser.cpp:90`） | 异常 |
| AC-4.4 | WHEN `children` 为模板对象 THEN `ExpandTemplateChildren` 调用 `ExpandTemplateChildrenEager` 遍历 path 数组实例化模板子组件（`RowComponent.cpp:149-153`、`Component.h:198`） | 正常 |
| AC-4.5 | WHEN `children` 为数组中的空字符串项 THEN 该项被过滤不进入 staticChildIds（`ChildListParser.cpp:70-73`） | 边界 |

### US-5: 子组件间距管理

**作为** 生成式 UI 宿主开发者,
**我想要** Row 在子组件之间施加默认间距,
**以便** 相邻子组件保持可读的水平间隔。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN Row 组件构造 THEN `spacing_` 取 `RowTheme::GetDefaultSpace()` 即 `ROW_DEFAULT_SPACE=16.0F`（`RowComponent.cpp:24`、`RowTheme.cpp:22,86-89`） | 正常 |
| AC-5.2 | WHEN 仅 1 个子组件 THEN `CalculateChildSpacing` 返回 start=end=0，不施加间距 margin（`Component.cpp:1503-1505`） | 边界 |
| AC-5.3 | WHEN 多子组件 THEN 中间项左右各施加 `spacing_/2`，首项仅右侧、末项仅左侧（`Component.cpp:1507-1514`） | 正常 |
| AC-5.4 | WHEN 间距作用于 Row 子组件 THEN `ApplyMarginToChild` 以水平方向施加（`SetMargin(0, end, 0, start)`）（`RowComponent.cpp:96-103`） | 正常 |
| AC-5.5 | WHEN 新增/移动/移除子组件 THEN `RefreshSpacingOnChildAdded/Moved`/`ClearChildSpacing` 刷新相邻项间距（`RowComponent.cpp:78-94`、`Component.cpp:1532-1562`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-1 | ArkTS 单测：目录项注册 | `A2UIRow.ets:25-35`、`A2UIBasicComponents.ets:44` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2,R-5 | T-1 | C++ UT：`RowTheme::ResolveAlignItems` | `RowTheme.cpp:47-60` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3,R-5 | T-1 | C++ UT：`RowTheme::ResolveJustifyContent` | `RowTheme.cpp:62-84` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-4 | T-1 | C++ UT：`ChildListParser::ParseChildren` | `ChildListParser.cpp:62-92` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-6 | T-1 | ohosTest：`dynamic/row/DynamicRowItemMargin` | `Component.cpp:1498-1530` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 调用 `asCatalogItem()` | 返回 name=`Row`、`A2UI_STANDARD`、`isInnerNative=true` 的目录项 | 仅内部注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | `align` 取值为 `start/center/end` | 映射为 `A2UIVerticalAlignment` 的 TOP/CENTER/BOTTOM | 枚举三值 | AC-2.1,AC-2.2,AC-2.3 |
| R-3 | 行为 | `justify` 取值为 6 种合法值 | 映射为 `A2UIFlexAlignment` 对应枚举 | 枚举六值 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 异常 | `children` 为非法结构 | `ParseChildren` 返回 INVALID | 空数组/非数组非对象均 INVALID | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| R-5 | 边界 | `align`/`justify` 缺省或非法 token | 回退默认 `"start"` | 非法 token 不回抛异常 | AC-2.4,AC-3.3 |
| R-6 | 行为 | 子组件增删移动 | 间距按 `spacing_=16.0` 半间距刷新 | 单子组件不施加 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 目录注册 | ArkTS 单测 | type/类别/原生标记 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 align 映射 | C++ UT | start/center/end 与回退 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 justify 映射 | C++ UT | 6 值与回退 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 子列表解析 | C++ UT | 静态/模板/非法三态 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 间距 | ohosTest | 16.0 半间距与刷新 |

## API 变更分析

> 存量补录，无新增/变更 Public API。组件经内部 `CatalogItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `A2UIRow.asCatalogItem()`（内部） | 既有 | 目录项构造 | 不直接暴露给宿主 | AC-1.1,AC-1.2,AC-1.3 |
| `RowComponent::SetAlignItems/SetJustifyContent`（内部） | 既有 | 属性落盘 | 框架内部 | AC-2.1,AC-3.4 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIRow.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`A2UIRow.asCatalogItem()`（内部，`A2UIRow.ets:31`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static asCatalogItem(): CatalogItem` |
| 返回值 | `CatalogItem` — name=`Row`、category=`A2UI_STANDARD`、isInnerNative=true |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**`RowTheme::ResolveAlignItems(align)`（`RowTheme.h:37`、`RowTheme.cpp:47`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static A2UIVerticalAlignment ResolveAlignItems(const std::string& align)` |
| 返回值 | `A2UIVerticalAlignment` — TOP/CENTER/BOTTOM；非法 token 回退 TOP |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |

**`RowTheme::ResolveJustifyContent(justify)`（`RowTheme.h:38`、`RowTheme.cpp:62`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static A2UIFlexAlignment ResolveJustifyContent(const std::string& justify)` |
| 返回值 | `A2UIFlexAlignment` — START/CENTER/END/SPACE_AROUND/SPACE_BETWEEN/SPACE_EVENLY；非法 token 回退 START |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| align | string | 否 | `"start"` | 取值 `start`/`center`/`end`，非法回退 `start` |
| justify | string | 否 | `"start"` | 取值 6 种，非法回退 `start` |
| children | array/object | 是 | — | 非空 ID 数组或 `{componentId,path}` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | align=`"start"` | 交叉轴顶部对齐（TOP） | AC-2.1 |
| 2 | align=`"center"` | 交叉轴居中对齐（CENTER） | AC-2.2 |
| 3 | align=`"end"` | 交叉轴底部对齐（BOTTOM） | AC-2.3 |
| 4 | align 缺省/非法 | 回退 TOP | AC-2.4 |
| 5 | justify=`"spaceBetween"` | 主轴 SPACE_BETWEEN 分布 | AC-3.2 |
| 6 | justify 非法 | 回退 START | AC-3.3 |
| 7 | children 为数组 | 静态子组件集合 | AC-4.1 |
| 8 | children 为模板对象 | Eager 展开模板子组件 | AC-4.4 |
| 9 | children 非法 | INVALID（schema warning） | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** 组件 schema 由 `components/Row.json` 声明；`align` 默认值存在文档分歧（`row.md:154` 标注 `"center"`，`catalog.json:313` 与代码 `RowComponent.cpp:35` 均为 `"start"`），以代码与 catalog 为准（RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 组件三件套 | 注册/实现/主题三层落地，职责单一 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| 枚举回退 | 非法 token 一律回退默认值，不抛异常 | AC-2.4,AC-3.3 |
| 间距半间距 | 间距经 margin 半间距表达，方向由子类决定 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |
| 子列表二态 | children 仅支持静态数组/模板对象，其余 INVALID | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法枚举 token 不崩溃，回退默认值 | C++ UT | `RowTheme.cpp:58-59,82-83` |
| 性能 | 模板展开为 Eager 遍历，无懒加载 | ohosTest | `RowComponent.cpp:149-153` |
| 可测试性 | 枚举映射/子列表解析为纯函数 | C++ UT | `RowTheme.cpp`、`ChildListParser.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 布局语义与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 断点主题重应用归 07-04-23 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 子组件 accessibility 透传（归 07-04-18） | `Component.cpp:1566` |
| 大字体 | 否 | 布局容器不涉及字号 | — |
| 深色模式 | 否 | 主题重应用为空实现（RISK-3） | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 协议 v0.9 组件 schema | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 Row 兼容 | `catalog.json:272-323` |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Row 组件
  作为 生成式 UI 宿主开发者
  我想要 Row 水平排列子组件并支持对齐/间距
  以便 正确渲染服务端下发的行布局

  Scenario: 静态子组件水平排列
    Given DSL 组件为 {"component":"Row","id":"root","children":["a","b"]}
    When 引擎应用组件描述
    Then Row 创建原生 ROW 节点并按顺序挂载子组件 a、b

  Scenario: 非法 align 回退默认
    Given DSL 组件为 {"component":"Row","align":"stretch","children":["a"]}
    When 引擎解析 align 属性
    Then align 回退为 "start"，子组件顶部对齐

  Scenario Outline: justify 枚举映射
    Given Row 组件 justify 为 <token>
    When 引擎解析 justify 属性
    Then 映射为 <alignment> 落盘

    Examples:
      | token        | alignment      |
      | start        | START          |
      | center       | CENTER         |
      | end          | END            |
      | spaceAround  | SPACE_AROUND   |
      | spaceBetween | SPACE_BETWEEN  |
      | spaceEvenly  | SPACE_EVENLY   |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做 Row 布局；通用属性归 07-04-18，模板语义归 07-04-17）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "A2UIRow.asCatalogItem Row 组件目录注册 markCategory markInnerNative"
  - repo: "GenerativeUI/A2UIRender"
    query: "RowComponent RowTheme ResolveAlignItems ResolveJustifyContent 枚举映射回退"
  - repo: "GenerativeUI/A2UIRender"
    query: "ChildListParser ParseChildren STATIC_IDS TEMPLATE_PATH Row 子组件间距 spacing 16.0"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/A2UIRow.ets`、`genui/src/main/cpp/components/A2UI/row/RowComponent.cpp`、`genui/src/main/cpp/components/A2UI/row/RowTheme.cpp`、`genui/src/main/cpp/composition/ChildListParser.cpp`、`specification/A2UI/v0_9/catalogs/basic/catalog.json`
