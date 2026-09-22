# 特性规格

> Func-07-04-10-Feat-05 Grid 组件：固化 A2UI 扩展协议布局容器 Grid 的网格布局语义——目录注册（`type='Grid'`，C++ `ExtendedGridComponent` 落 GRID 原生节点）、styles 特有样式 `columnsTemplate`/`rowsTemplate`（`fr` token 或响应式断点对象）与 `columnsGap`/`rowsGap` 枚举映射与非法回退、断点驱动的默认列模板（2/3/5 列）、EAGER/LAZY 双态与网格项高度策略。基准实现：`@arkui-genius/genui`（full_render）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Grid 组件 |
| 特性编号 | Func-07-04-10-Feat-05 |
| 优先级 | P0 |
| 目标版本 | A2UI 扩展协议 Catalog v1.0.0（ohos.a2ui.extended.catalog） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 第五个 Feat，与 Feat-01 Row 共享 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/10-a2ui-extended-layout-components/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 组件实现（C++） | `genui/src/main/cpp/components/extended/ExtendedGridComponent.{h,cpp}` | — |
| 网格主题（C++） | `genui/src/main/cpp/components/extended/ExtendedGridTheme.{h,cpp}` | — |
| 懒加载适配器（C++） | `genui/src/main/cpp/composition/GridAdapterNode.h` | — |
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（Grid 段） | 契约 |
| 组件参考（Docs） | `reference/extended-components/grid.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Grid 目录注册与原生节点

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `component: "Grid"` 识别为扩展原生网格容器,
**以便** 服务端下发的 Grid 组件被正确渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `allA2UIExtendedComponents()` THEN 返回目录项含 name=`Grid`（`A2UIExtendedComponents.ets:36,55,194-204`） | 正常 |
| AC-1.2 | WHEN `CreateComponent("Grid")` THEN 返回 `ExtendedGridComponent`（`ExtendedComponentFactory.cpp:113`） | 正常 |
| AC-1.3 | WHEN 构造 THEN `CreateNode(A2UINodeType::GRID)` 且 `columnsTemplateConfig_.mode=THEME_DEFAULT`，`GetType()=="Grid"`（`ExtendedGridComponent.cpp:265-278`） | 正常 |

### US-2: 列模板（columnsTemplate）

**作为** 生成式 UI 宿主开发者,
**我想要** Grid 配置列数与列宽,
**以便** 通过 `columnsTemplate` 控制网格列布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `columnsTemplate` 为合法 `fr` 字符串（如 `"1fr 1fr"`）THEN `IsSupportedGridTemplate` 返回 true（`ExtendedGridComponent.cpp:136-171`） | 正常 |
| AC-2.2 | WHEN 为响应式对象 `{xs,sm,md,lg,xl}` THEN `ParseTemplateConfig` 解析为 `RESPONSIVE` 态（`ExtendedGridComponent.cpp:736-775`） | 正常 |
| AC-2.3 | WHEN 为空/非字符串/非法 THEN 回退默认（`ResolveGridTemplateOrDefault` `:186-196`、`DEFAULT_GRID_TEMPLATE="1fr"` `:40`） | 边界 |
| AC-2.4 | WHEN 未显式配置 THEN `ApplyColumnsTemplateForContext` 走 `THEME_DEFAULT` 应用主题列模板（`ExtendedGridComponent.cpp:676-698`） | 正常 |
| AC-2.5 | WHEN 落盘 THEN `SetNodeGridColumnTemplate`（`ExtendedGridComponent.cpp:796-802`） | 正常 |

### US-3: 行模板（rowsTemplate）

**作为** 生成式 UI 宿主开发者,
**我想要** Grid 配置行数与行高,
**以便** 通过 `rowsTemplate` 控制网格行布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `rowsTemplate` 为合法 `fr` 字符串 THEN 经 `ParseTemplateConfig` 解析为 `FIXED` 态（`ExtendedGridComponent.cpp:739-743`） | 正常 |
| AC-3.2 | WHEN 未显式配置 THEN `ApplyRowsTemplateForContext` 在 RESET/THEME_DEFAULT 态保持行不动（`ExtendedGridComponent.cpp:700-721`） | 正常 |
| AC-3.3 | WHEN 落盘 THEN `SetNodeGridRowTemplate`（`ExtendedGridComponent.cpp:804-810`） | 正常 |
| AC-3.4 | WHEN rowsTemplate 变化 THEN `RefreshGridItemHeightPolicies` 刷新高度策略（`ExtendedGridComponent.cpp:515-534,828-837`） | 正常 |

### US-4: 行列间距（columnsGap/rowsGap）

**作为** 生成式 UI 宿主开发者,
**我想要** Grid 配置行列间距,
**以便** 通过 `columnsGap`/`rowsGap` 控制网格项间隔。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `columnsGap` 为非负数 THEN `SetColumnsGap` 经 `SetNodeGridColumnGap` 落盘（`ExtendedGridComponent.cpp:812-818`） | 正常 |
| AC-4.2 | WHEN `rowsGap` 为非负数 THEN `SetRowsGap` 经 `SetNodeGridRowGap` 落盘（`ExtendedGridComponent.cpp:820-826`） | 正常 |
| AC-4.3 | WHEN 为负数 THEN `NormalizeGridGap` 归 0.0F（`ExtendedGridComponent.cpp:131-134`） | 边界 |
| AC-4.4 | WHEN 未配置 THEN 默认 0.0F（`ExtendedGridComponent.cpp:347-348,535-544`） | 正常 |

### US-5: 子列表展开与懒加载

**作为** 生成式 UI 宿主开发者,
**我想要** Grid 支持静态数组（EAGER）与模板对象（LAZY 懒加载）,
**以便** 兼顾固定网格与大数据量网格。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN EAGER 模式 `OnAddChild` THEN 为每子项包裹 `GRID_ITEM` 节点并施加高度策略（`ExtendedGridComponent.cpp:592-614,173-184`） | 正常 |
| AC-5.2 | WHEN 模板 children THEN `ExpandTemplateChildren` 走 `SetupLazyAdapter`（`GridAdapterNode`），失败回退 EAGER（`ExtendedGridComponent.cpp:301-339,649-665`） | 正常 |
| AC-5.3 | WHEN 模板缺失/数据路径不存在 THEN 空网格处理（`PrepareGridAdapterConfig` `:216-261`） | 异常 |
| AC-5.4 | WHEN 移除/清空 THEN `DetachGridItemNode` 释放 `GRID_ITEM` 节点（`ExtendedGridComponent.cpp:667-674,844-853`） | 正常 |

### US-6: 断点驱动的默认列模板与尺寸监听

**作为** 生成式 UI 宿主开发者,
**我想要** Grid 根据窗口宽度切换列数,
**以便** 大屏展示多列网格。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 断点为 XS/SM THEN `GetColumnsTemplate()` 返回 `"1fr 1fr"`（2 列）（`ExtendedGridTheme.cpp:54-58`） | 正常 |
| AC-6.2 | WHEN 断点为 MD THEN 返回 `"1fr 1fr 1fr"`（3 列）（`ExtendedGridTheme.cpp:59-61`） | 正常 |
| AC-6.3 | WHEN 断点为 LG/XL THEN 返回 `"1fr 1fr 1fr 1fr 1fr"`（5 列）（`ExtendedGridTheme.cpp:62-65`） | 正常 |
| AC-6.4 | WHEN 宽度变化跨越断点 THEN `HandleSizeChange` 更新断点并 `OnConfigChange` 重应用模板（`ExtendedGridComponent.cpp:555-590,469-477`） | 正常 |
| AC-6.5 | WHEN 响应式对象未配当前断点 THEN `ResolveResponsiveTemplate` 先向小断点再向大断点查找（`ExtendedGridComponent.cpp:777-794`） | 边界 |

### US-7: 网格项高度策略

**作为** 生成式 UI 宿主开发者,
**我想要** Grid 网格项在未配 rowsTemplate 时按内容高度包裹,
**以便** 保持可滚动的自适应行高。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN rowsTemplate 未显式配置 THEN `ShouldGridItemsWrapContentHeight()` 返回 true（`ExtendedGridComponent.cpp:839-842`） | 正常 |
| AC-7.2 | WHEN 高度策略为包裹 THEN `ApplyGridItemHeightPolicy` 设 `WRAP_CONTENT`（`ExtendedGridComponent.cpp:173-184`） | 正常 |
| AC-7.3 | WHEN rowsTemplate 显式配置 THEN 非包裹态，`ResetNodeHeightLayoutPolicy`（`ExtendedGridComponent.cpp:178-180`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-5 | ArkTS 单测 + C++ UT | `A2UIExtendedComponents.ets:194-204`、`ExtendedGridComponent.cpp:265-278` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-5 | C++ UT：`IsSupportedGridTemplate`/`ParseTemplateConfig` | `ExtendedGridComponent.cpp:136-171,736-775` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-5 | C++ UT | `ExtendedGridComponent.cpp:700-721` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4 | T-5 | C++ UT：`NormalizeGridGap` | `ExtendedGridComponent.cpp:131-134` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4 | R-5 | T-5 | C++ UT + ohosTest | `ExtendedGridComponent.cpp:301-339,592-614` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 | R-6 | T-5 | C++ UT：`ExtendedGridTheme` | `ExtendedGridTheme.cpp:54-69` |
| AC-7.1,AC-7.2,AC-7.3 | R-7 | T-5 | C++ UT | `ExtendedGridComponent.cpp:839-842` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 创建 `Grid` | 返回 GRID 原生节点组件，columnsTemplate 默认 THEME_DEFAULT | — | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 边界 | `columnsTemplate` 非法/空 | 回退 `"1fr"`；未配置走主题默认 | `fr` token 仅数字.fr | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 行为 | `rowsTemplate` 未配置 | 保持行不动（避免切静态布局） | RESET/THEME_DEFAULT 态 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 边界 | `columnsGap`/`rowsGap` 负数 | 归 0.0F | 默认 0 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-5 | 行为 | 模板 children 数据缺失 | 空网格/回退 EAGER，不崩溃 | 包裹 GRID_ITEM | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| R-6 | 行为 | 断点变化 | 2/3/5 列默认模板 + 响应式查找 | 宽度跨越断点 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |
| R-7 | 行为 | rowsTemplate 未配置 | 网格项 WRAP_CONTENT 高度 | 显式 rowsTemplate 则非包裹 | AC-7.1,AC-7.2,AC-7.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测 + C++ UT | type/GRID 节点 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 columnsTemplate | C++ UT | fr token/响应式/回退 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 rowsTemplate | C++ UT | 保持行不动 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 gap | C++ UT | 负数归 0 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 懒加载 | C++ UT + ohosTest | GridAdapterNode/包裹 GRID_ITEM |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 断点模板 | C++ UT | 2/3/5 列 |
| VM-7 | AC-7.1,AC-7.2,AC-7.3 高度策略 | C++ UT | WRAP_CONTENT |

## API 变更分析

> 存量补录，无新增/变更 Public API。组件经内部 `CatalogItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `createExtendedNativeCatalogItem('Grid')`（内部） | 既有 | 目录项构造 | 不直接暴露给宿主 | AC-1.1 |
| `ExtendedGridComponent::SetColumnsTemplate/SetRowsTemplate/SetColumnsGap/SetRowsGap`（内部） | 既有 | 属性落盘 | 框架内部 | AC-2.5,AC-3.3,AC-4.1,AC-4.2 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`IsSupportedGridTemplate(templateValue)`（`ExtendedGridComponent.cpp:159-171`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool IsSupportedGridTemplate(const std::string& templateValue)` |
| 返回值 | `bool` — 全部 token 为合法 `fr` 且至少一个 token |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**`ParseTemplateConfig(value, config)`（`ExtendedGridComponent.cpp:736-775`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool ParseTemplateConfig(const JsonValue& value, GridTemplateConfig& config)` |
| 返回值 | `bool` — 解析成功；字符串→FIXED、对象→RESPONSIVE |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.2,AC-3.1 |

**`ResolveResponsiveTemplate(config, context)`（`ExtendedGridComponent.cpp:777-794`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static std::string ResolveResponsiveTemplate(const GridTemplateConfig& config, const ThemeContext& context)` |
| 返回值 | `std::string` — 当前断点或邻近断点的模板；无则 `"1fr"` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-6.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| columnsTemplate | string/object | 否 | 断点驱动（2/3/5 列） | `fr` token 或 `{xs,sm,md,lg,xl}`，非法回退 `"1fr"` |
| rowsTemplate | string/object | 否 | 未配置（保持行不动） | 同上 |
| columnsGap | number | 否 | 0.0F | `[0,+inf)`，负数归 0 |
| rowsGap | number | 否 | 0.0F | `[0,+inf)`，负数归 0 |
| children | array/object | 否 | `[]` | 非空 ID 数组或 `{componentId,path}` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | columnsTemplate=`"1fr 2fr 1fr"` | 三列权重 1:2:1 | AC-2.1 |
| 2 | columnsTemplate 非法 | 回退 `"1fr"` | AC-2.3 |
| 3 | rowsTemplate 未配置 | 保持行不动 + 网格项 WRAP_CONTENT | AC-3.2,AC-7.1 |
| 4 | columnsGap=-1 | 归 0vp | AC-4.3 |
| 5 | 模板 path 非数组 | 空网格处理 | AC-5.3 |
| 6 | 断点 LG | 默认 5 列模板 | AC-6.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 Catalog v1.0.0；size change 事件 API<21 用 `ON_AREA_CHANGE`（`ExtendedGridComponent.cpp:547-553`）。
- **API 版本号策略:** 组件 schema 由 `schema/Extended/components/ExtendedGrid.json` 声明；`columnsTemplate` 默认值存在文档分歧（`grid.md:235` 标注 `"1fr"`，实现为断点驱动 2/3/5 列），以代码为准（RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 组件三件套 | 注册/实现/样式解析分层 | AC-1.1,AC-1.2,AC-1.3 |
| fr token 校验 | 仅支持 `数字.fr`，非法回退 | AC-2.1,AC-2.2,AC-2.3 |
| rowsTemplate 缺省 | 保持行不动，避免静态布局 | AC-3.2 |
| EAGER/LAZY 双态 | 静态数组 EAGER、模板 LAZY，失败回退 EAGER | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| 断点默认列 | 宽度驱动 2/3/5 列 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |
| 高度策略 | rowsTemplate 缺省时 WRAP_CONTENT | AC-7.1,AC-7.2,AC-7.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法模板/gap/data 缺失不崩溃 | C++ UT | `ExtendedGridComponent.cpp:131-134,186-196,216-261` |
| 性能 | 模板网格懒加载（GridAdapterNode） | ohosTest | `ExtendedGridComponent.cpp:301-339` |
| 可测试性 | fr token 校验/响应式查找纯函数 | C++ UT | `ExtendedGridComponent.cpp:136-171,777-794` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机（XS/SM） | 默认 2 列 | `"1fr 1fr"` | C++ UT | `ExtendedGridTheme.cpp:54-58` |
| 平板（MD） | 默认 3 列 | `"1fr 1fr 1fr"` | C++ UT | `ExtendedGridTheme.cpp:59-61` |
| 折叠屏/大屏（LG/XL） | 默认 5 列 | `"1fr 1fr 1fr 1fr 1fr"` | C++ UT | `ExtendedGridTheme.cpp:62-65` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 子组件 accessibility 透传 | 通用属性归 overview |
| 大字体 | 否 | 网格容器不涉及字号 | — |
| 深色模式 | 否 | 阴影主题重应用由 `ExtendedComponent::OnConfigChange` 承接 | `ExtendedComponent.cpp:841-854` |
| 多窗口/分屏 | 是 | 宽度变化触发断点列模板刷新 | `ExtendedGridComponent.cpp:555-590` |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | size change 事件 API 版本分派 | 兼容性声明 |
| 生态兼容 | 是 | A2UI 扩展协议 v1.0.0 Grid 兼容 | `extended_catalog.json` Grid 段 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Grid 组件
  作为 生成式 UI 宿主开发者
  我想要 Grid 网格排列子组件并支持行列模板/间距
  以便 正确渲染服务端下发的网格布局

  Scenario: 静态子组件网格排列
    Given DSL 组件为 {"component":"Grid","id":"root","children":["a","b","c","d"]}
    When 引擎应用组件描述
    Then Grid 创建原生 GRID 节点并包裹 GRID_ITEM 挂载子组件

  Scenario: 非法 columnsTemplate 回退默认
    Given DSL 组件为 {"component":"Grid","styles":{"columnsTemplate":"not_a_template"},"children":["a"]}
    When 引擎解析 columnsTemplate
    Then columnsTemplate 回退为 "1fr"

  Scenario Outline: 断点默认列模板
    Given Grid 未显式配置 columnsTemplate 且断点为 <bp>
    When 引擎解析主题上下文
    Then 应用 <template>

    Examples:
      | bp | template                    |
      | XS | 1fr 1fr                     |
      | SM | 1fr 1fr                     |
      | MD | 1fr 1fr 1fr                 |
      | LG | 1fr 1fr 1fr 1fr 1fr         |
      | XL | 1fr 1fr 1fr 1fr 1fr         |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-05 做 Grid 布局；通用属性归 overview）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "genui/full_render"
    query: "ExtendedGridComponent columnsTemplate rowsTemplate IsSupportedGridTemplate ParseTemplateConfig 响应式断点"
  - repo: "genui/full_render"
    query: "ExtendedGridComponent SetupLazyAdapter GridAdapterNode OnAddChild GRID_ITEM 高度策略 wrapContent"
  - repo: "genui/full_render"
    query: "ExtendedGridTheme GetColumnsTemplate Breakpoint 2/3/5 列 HandleSizeChange"
```

**关键文档：** `genui/src/main/cpp/components/extended/ExtendedGridComponent.cpp`、`genui/src/main/cpp/components/extended/ExtendedGridTheme.cpp`、`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`、`specification/extended/1.0.0/extended_catalog.json`