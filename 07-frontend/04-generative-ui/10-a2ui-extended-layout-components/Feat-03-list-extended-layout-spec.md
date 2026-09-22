# 特性规格

> Func-07-04-10-Feat-03 List 组件：固化 A2UI 扩展协议布局容器 List 的可滚动列表语义——目录注册（`type='List'`，C++ `ExtendedListComponent` 落 LIST 原生节点）、顶层私有属性 `space`（默认 0vp，负数回退 0）、styles 特有样式 `listDirection`/`scrollBar`/`nestedScroll` 枚举映射与非法回退、`onReachStart`/`onReachEnd` 事件、EAGER/LAZY 双态与断点驱动的 lanes 默认值。基准实现：`@arkui-genius/genui`（full_render）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | List 组件 |
| 特性编号 | Func-07-04-10-Feat-03 |
| 优先级 | P0 |
| 目标版本 | A2UI 扩展协议 Catalog v1.0.0（ohos.a2ui.extended.catalog） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 第三个 Feat，与 Feat-01 Row 共享 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/10-a2ui-extended-layout-components/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 组件实现（C++） | `genui/src/main/cpp/components/extended/ExtendedListComponent.{h,cpp}` | — |
| 列表主题（C++） | `genui/src/main/cpp/components/extended/ExtendedListTheme.{h,cpp}` | — |
| 懒加载适配器（C++） | `genui/src/main/cpp/composition/ListAdapterNode.h` | — |
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（List 段） | 契约 |
| 组件参考（Docs） | `reference/extended-components/list.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: List 目录注册与原生节点

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `component: "List"` 识别为扩展原生可滚动容器,
**以便** 服务端下发的 List 组件被正确渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `allA2UIExtendedComponents()` THEN 返回目录项含 name=`List`（`A2UIExtendedComponents.ets:34,53,194-204`） | 正常 |
| AC-1.2 | WHEN `CreateComponent("List")` THEN 返回 `ExtendedListComponent`（`ExtendedComponentFactory.cpp:114`） | 正常 |
| AC-1.3 | WHEN 构造 THEN `CreateNode(A2UINodeType::LIST)`，`GetType()=="List"`（`ExtendedListComponent.cpp:208,216-219`） | 正常 |

### US-2: 子组件间距（space）

**作为** 生成式 UI 宿主开发者,
**我想要** List 在子项主轴方向施加间距,
**以便** 控制列表项间隔。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 未指定 space THEN `fallbackNumber=0.0`，间距为 0（`ExtendedListComponent.cpp:308-313`） | 正常 |
| AC-2.2 | WHEN space 为非负数 THEN `SetSpace` 经 `SetNodeListSpace` 落盘（`ExtendedListComponent.cpp:608-615`） | 正常 |
| AC-2.3 | WHEN space 为负数/非有限值 THEN 上报 `SCHEMA_ERROR_CODE_INVALID_VALUE` 并回退 0.0F（`ExtendedListComponent.cpp:608-615`、`NormalizeListSpace` `:101-104`） | 边界 |
| AC-2.4 | WHEN `ApplyPrivateAttributes` THEN 初始方向 VERTICAL、滚动条 AUTO、nestedScroll selfFirst/selfFirst（`ExtendedListComponent.cpp:279-287`） | 正常 |

### US-3: 排列方向（listDirection）

**作为** 生成式 UI 宿主开发者,
**我想要** List 支持纵向与横向排列,
**以便** 通过 `listDirection` 控制滚动方向。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `listDirection` 为 `"horizontal"` THEN `ResolveListDirection` 返回 `HORIZONTAL`（`ExtendedListComponent.cpp:93-99`） | 正常 |
| AC-3.2 | WHEN `listDirection` 缺省或非法 THEN 返回 `VERTICAL`（`ExtendedListComponent.cpp:98,414-418`） | 边界 |
| AC-3.3 | WHEN 落盘 THEN `SetNodeListDirection`（`ExtendedListComponent.cpp:622-625`） | 正常 |

### US-4: 滚动条（scrollBar）

**作为** 生成式 UI 宿主开发者,
**我想要** List 控制滚动条显示与否,
**以便** 通过 `scrollBar` 控制滚动条状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `scrollBar` 为 `"off"`/`"on"` THEN `ResolveScrollBar` 返回 OFF/ON（`ExtendedListComponent.cpp:106-115`） | 正常 |
| AC-4.2 | WHEN 缺省或其他值 THEN 返回 AUTO（`ExtendedListComponent.cpp:114,419-423`） | 边界 |
| AC-4.3 | WHEN 落盘 THEN `SetNodeScrollBarDisplayMode`（`ExtendedListComponent.cpp:627-630`） | 正常 |

### US-5: 嵌套滚动（nestedScroll）

**作为** 生成式 UI 宿主开发者,
**我想要** List 配置嵌套滚动模式,
**以便** 控制自身与父滚动容器的联动。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `nestedScroll` 为 `"selfOnly"`/`"selfFirst"`/`"parentFirst"`/`"paraller"` THEN `ResolveNestedScrollMode` 映射对应枚举（`ExtendedListComponent.cpp:117-132`） | 正常 |
| AC-5.2 | WHEN 缺省或非法 THEN 回退 `selfFirst`（`ExtendedListComponent.cpp:131,426-428`） | 边界 |
| AC-5.3 | WHEN `nestedScroll` 为对象 THEN 分别解析 `scrollForward`/`scrollBackward`（`ApplyNestedScrollValueOrDefault` `:431-455`） | 正常 |
| AC-5.4 | WHEN 落盘 THEN `SetNodeScrollNestedScroll`（`ExtendedListComponent.cpp:632-635`） | 正常 |

### US-6: 滚动边界事件（onReachStart/onReachEnd）

**作为** 生成式 UI 宿主开发者,
**我想要** List 在滚动到边界时触发事件,
**以便** 实现加载更多等交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 配置 `onReachStart` 处理器 THEN `RegisterComponentSpecificListeners` 注册 `SCROLL_ON_REACH_START`（`ExtendedListComponent.cpp:457-463`） | 正常 |
| AC-6.2 | WHEN 配置 `onReachEnd` 处理器 THEN 注册 `SCROLL_ON_REACH_END`（`ExtendedListComponent.cpp:465-469`） | 正常 |
| AC-6.3 | WHEN 未配置 THEN 不注册对应监听（`std::function<void()>` 空） | 边界 |

### US-7: 子列表展开与懒加载

**作为** 生成式 UI 宿主开发者,
**我想要** List 支持静态数组（EAGER）与模板对象（LAZY 懒加载）,
**以便** 兼顾固定集合与大数据量列表。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN EAGER 模式 `OnAddChild` THEN 为每子项包裹 `LIST_ITEM` 节点（`ExtendedListComponent.cpp:513-534`） | 正常 |
| AC-7.2 | WHEN 模板 children THEN `ExpandTemplateChildren` 走 `SetupLazyAdapter`（`ListAdapterNode`）（`ExtendedListComponent.cpp:244-277`） | 正常 |
| AC-7.3 | WHEN 模板缺失/数据路径不存在 THEN 空列表处理（`PrepareAdapterConfig` `:145-190`） | 异常 |
| AC-7.4 | WHEN 移除/清空 THEN `RemoveListItemNode` 释放 `LIST_ITEM` 节点（`ExtendedListComponent.cpp:569-587`） | 正常 |

### US-8: 断点驱动的 lanes 默认值

**作为** 生成式 UI 宿主开发者,
**我想要** List 根据窗口宽度切换列数,
**以便** 大屏展示多列列表。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 断点为 XS/SM THEN `GetLanes()` 返回 1（单列）（`ExtendedListTheme.cpp:54-58`） | 正常 |
| AC-8.2 | WHEN 断点为 MD THEN 返回 2（`ExtendedListTheme.cpp:59-61`） | 正常 |
| AC-8.3 | WHEN 断点为 LG/XL THEN 返回 3（`ExtendedListTheme.cpp:62-65`） | 正常 |
| AC-8.4 | WHEN 宽度变化跨越断点 THEN `HandleSizeChange` 更新断点并 `OnConfigChange` 重应用 lanes（`ExtendedListComponent.cpp:476-511,296-303`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-3 | ArkTS 单测 + C++ UT | `A2UIExtendedComponents.ets:194-204`、`ExtendedListComponent.cpp:208` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-3 | C++ UT：`SetSpace` | `ExtendedListComponent.cpp:608-615` |
| AC-3.1,AC-3.2,AC-3.3 | R-3 | T-3 | C++ UT：`ResolveListDirection` | `ExtendedListComponent.cpp:93-99` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-3 | C++ UT：`ResolveScrollBar` | `ExtendedListComponent.cpp:106-115` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4 | R-5 | T-3 | C++ UT：`ResolveNestedScrollMode` | `ExtendedListComponent.cpp:117-132` |
| AC-6.1,AC-6.2,AC-6.3 | R-6 | T-3 | C++ UT + ohosTest | `ExtendedListComponent.cpp:457-474` |
| AC-7.1,AC-7.2,AC-7.3,AC-7.4 | R-7 | T-3 | C++ UT + ohosTest | `ExtendedListComponent.cpp:244-277,513-587` |
| AC-8.1,AC-8.2,AC-8.3,AC-8.4 | R-8 | T-3 | C++ UT：`ExtendedListTheme` | `ExtendedListTheme.cpp:54-69` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 创建 `List` | 返回 LIST 原生节点组件，`GetType()=="List"` | — | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 边界 | `space` 负数/非有限值 | 回退 0.0F 并上报 warning | 默认 0 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 边界 | `listDirection` 缺省/非法 | 回退 vertical | 枚举两值 | AC-3.1,AC-3.2,AC-3.3 |
| R-4 | 边界 | `scrollBar` 缺省/非法 | 回退 auto | 枚举三值 | AC-4.1,AC-4.2,AC-4.3 |
| R-5 | 边界 | `nestedScroll` 缺省/非法 | 回退 selfFirst（双向） | 保留 `paraller` token | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| R-6 | 行为 | 配置边界事件 | 注册对应监听，未配置不注册 | 事件无数据 | AC-6.1,AC-6.2,AC-6.3 |
| R-7 | 行为 | 模板 children 数据缺失 | 空列表/空 adapter，不崩溃 | EAGER 包裹 LIST_ITEM | AC-7.1,AC-7.2,AC-7.3,AC-7.4 |
| R-8 | 行为 | 断点变化 | 按 XS/SM=1、MD=2、LG/XL=3 更新 lanes | 宽度跨越断点触发 | AC-8.1,AC-8.2,AC-8.3,AC-8.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测 + C++ UT | type/LIST 节点 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 space | C++ UT | 默认 0/负数回退 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 listDirection | C++ UT | vertical/horizontal |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 scrollBar | C++ UT | off/auto/on |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 nestedScroll | C++ UT | 4 值与对象双态 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3 边界事件 | ohosTest | reach 触发链 |
| VM-7 | AC-7.1,AC-7.2,AC-7.3,AC-7.4 懒加载 | C++ UT + ohosTest | NodeAdapter/包裹 LIST_ITEM |
| VM-8 | AC-8.1,AC-8.2,AC-8.3,AC-8.4 lanes | C++ UT | 断点列数 |

## API 变更分析

> 存量补录，无新增/变更 Public API。组件经内部 `CatalogItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `createExtendedNativeCatalogItem('List')`（内部） | 既有 | 目录项构造 | 不直接暴露给宿主 | AC-1.1 |
| `ExtendedListComponent::SetSpace/SetLanes/SetListDirection/SetScrollBar/SetNestedScroll`（内部） | 既有 | 属性落盘 | 框架内部 | AC-2.2,AC-3.3,AC-5.4 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ExtendedListComponent::GetPrivatePropertyDeclaration("space")`（`ExtendedListComponent.cpp:305-316`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `PropertyDeclaration CreateSpacePropertyDeclaration()` |
| 返回值 | `PropertyDeclaration` — type=NUMBER、fallbackNumber=0.0 |
| 开放范围 | 内部 |
| 错误码 | N/A（非法值上报 `SCHEMA_ERROR_CODE_INVALID_VALUE`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3 |

**`ResolveListDirection(direction)`（`ExtendedListComponent.cpp:93-99`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static A2UIAxis ResolveListDirection(const std::string& direction)` |
| 返回值 | `A2UIAxis` — HORIZONTAL/VERTICAL，非法回退 VERTICAL |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-3.1,AC-3.2 |

**`ResolveNestedScrollMode(mode)`（`ExtendedListComponent.cpp:117-132`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static A2UIScrollNestedMode ResolveNestedScrollMode(const std::string& mode)` |
| 返回值 | `A2UIScrollNestedMode` — SELF_ONLY/SELF_FIRST/PARENT_FIRST/PARALLEL，非法回退 SELF_FIRST |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-5.1,AC-5.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| space | number | 否 | 0.0 | `[0,+inf)`，负数/非有限值回退 0 |
| listDirection | string | 否 | `"vertical"` | `vertical/horizontal`，非法回退 vertical |
| scrollBar | string | 否 | `"auto"` | `off/auto/on`，非法回退 auto |
| nestedScroll | string/object | 否 | `selfFirst` | 4 值或 `{scrollForward,scrollBackward}` |
| onReachStart/onReachEnd | EventHandler[] | 否 | — | 事件数据无 |
| children | array/object | 否 | `[]` | 非空 ID 数组或 `{componentId,path}` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | space=-5 | 间距 0vp 并上报 warning | AC-2.3 |
| 2 | listDirection=`"horizontal"` | 横向排列 | AC-3.1 |
| 3 | scrollBar=`"on"` | 常驻滚动条 | AC-4.1 |
| 4 | nestedScroll=`{scrollForward:"selfOnly",scrollBackward:"parentFirst"}` | 双向分别配置 | AC-5.3 |
| 5 | 滚动到末尾 | 触发 onReachEnd 链 | AC-6.2 |
| 6 | 模板 path 非数组 | 空列表处理 | AC-7.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 Catalog v1.0.0；size change 事件 API<21 用 `ON_AREA_CHANGE`，否则 `ON_SIZE_CHANGE`（`ExtendedListComponent.cpp:470-473`）。
- **API 版本号策略:** 组件 schema 由 `schema/Extended/components/ExtendedList.json` 声明；`nestedScroll` 枚举 token `paraller`（拼写异常）作为契约保留（RISK-2）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 组件三件套 | 注册/实现/样式解析分层 | AC-1.1,AC-1.2,AC-1.3 |
| 枚举回退 | 非法 token 回退默认值 | AC-3.2,AC-4.2,AC-5.2 |
| EAGER/LAZY 双态 | 静态数组 EAGER、模板 LAZY | AC-7.1,AC-7.2,AC-7.3,AC-7.4 |
| 断点 lanes | 宽度驱动列数，非 DSL 属性 | AC-8.1,AC-8.2,AC-8.3,AC-8.4 |
| 嵌套滚动 token | 保留 `paraller` 拼写 | AC-5.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法值/data 缺失不崩溃 | C++ UT | `ExtendedListComponent.cpp:145-190,608-615` |
| 性能 | 模板列表懒加载（NodeAdapter） | ohosTest | `ExtendedListComponent.cpp:244-264` |
| 可测试性 | Resolve* 纯函数 | C++ UT | `ExtendedListComponent.cpp:93-132` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机（XS/SM） | lanes=1 | 单列 | C++ UT | `ExtendedListTheme.cpp:54-58` |
| 平板（MD） | lanes=2 | 双列 | C++ UT | `ExtendedListTheme.cpp:59-61` |
| 折叠屏/大屏（LG/XL） | lanes=3 | 三列 | C++ UT | `ExtendedListTheme.cpp:62-65` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 子组件 accessibility 透传 | 通用属性归 overview |
| 大字体 | 否 | 列表容器不涉及字号 | — |
| 深色模式 | 否 | 阴影主题重应用由 `ExtendedComponent::OnConfigChange` 承接 | `ExtendedComponent.cpp:841-854` |
| 多窗口/分屏 | 是 | 宽度变化触发断点 lanes 刷新 | `ExtendedListComponent.cpp:476-511` |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | size change 事件 API 版本分派 | 兼容性声明 |
| 生态兼容 | 是 | A2UI 扩展协议 v1.0.0 List 兼容 | `extended_catalog.json` List 段 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: List 组件
  作为 生成式 UI 宿主开发者
  我想要 List 可滚动排列子组件并支持方向/滚动条/嵌套滚动
  以便 正确渲染服务端下发的列表布局

  Scenario: 负数 space 回退默认
    Given DSL 组件为 {"component":"List","space":-5,"children":["a","b"]}
    When 引擎解析 space
    Then space 回退为 0vp

  Scenario: 模板对象懒加载
    Given DSL 组件为 {"component":"List","children":{"componentId":"tpl","path":"/items"}}
    When 引擎展开模板
    Then List 走 LAZY NodeAdapter 懒加载

  Scenario Outline: nestedScroll 枚举映射
    Given List 组件 nestedScroll 为 <token>
    When 引擎解析 nestedScroll
    Then 映射为 <mode> 落盘

    Examples:
      | token       | mode         |
      | selfOnly    | SELF_ONLY    |
      | selfFirst   | SELF_FIRST   |
      | parentFirst | PARENT_FIRST |
      | paraller    | PARALLEL     |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做 List 布局；通用属性归 overview）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "genui/full_render"
    query: "ExtendedListComponent space listDirection scrollBar nestedScroll ResolveNestedScrollMode paraller 枚举回退"
  - repo: "genui/full_render"
    query: "ExtendedListComponent SetupLazyAdapter ListAdapterNode OnAddChild LIST_ITEM 懒加载"
  - repo: "genui/full_render"
    query: "ExtendedListTheme GetLanes Breakpoint lanes 断点列数 HandleSizeChange"
```

**关键文档：** `genui/src/main/cpp/components/extended/ExtendedListComponent.cpp`、`genui/src/main/cpp/components/extended/ExtendedListTheme.cpp`、`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`、`specification/extended/1.0.0/extended_catalog.json`