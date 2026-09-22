# 特性规格

> Func-07-04-10-Feat-04 Stack 组件：固化 A2UI 扩展协议布局容器 Stack 的层叠布局语义——目录注册（`type='Stack'`，C++ `ExtendedStackComponent` 落 STACK 原生节点）、styles 特有样式 `alignContent` 九值枚举映射与非法回退（默认 `center`）、`children` 静态/模板二态解析与 Eager 展开。基准实现：`@arkui-genius/genui`（full_render）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Stack 组件 |
| 特性编号 | Func-07-04-10-Feat-04 |
| 优先级 | P0 |
| 目标版本 | A2UI 扩展协议 Catalog v1.0.0（ohos.a2ui.extended.catalog） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 第四个 Feat，与 Feat-01 Row 共享 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/10-a2ui-extended-layout-components/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 组件实现（C++） | `genui/src/main/cpp/components/extended/ExtendedStackComponent.{h,cpp}` | — |
| 子列表解析（C++） | `genui/src/main/cpp/composition/ChildListParser.{h,cpp}` | — |
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（Stack 段） | 契约 |
| 组件参考（Docs） | `reference/extended-components/stack.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Stack 目录注册与原生节点

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `component: "Stack"` 识别为扩展原生层叠容器,
**以便** 服务端下发的 Stack 组件被正确渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `allA2UIExtendedComponents()` THEN 返回目录项含 name=`Stack`（`A2UIExtendedComponents.ets:35,54,194-204`） | 正常 |
| AC-1.2 | WHEN `CreateComponent("Stack")` THEN 返回 `ExtendedStackComponent`（`ExtendedComponentFactory.cpp:112`） | 正常 |
| AC-1.3 | WHEN 构造 THEN `CreateNode(A2UINodeType::STACK)`，`GetType()=="Stack"`（`ExtendedStackComponent.cpp:58-65`） | 正常 |

### US-2: 层叠对齐（alignContent）

**作为** 生成式 UI 宿主开发者,
**我想要** Stack 控制子组件的对齐方式,
**以便** 通过 `alignContent` 定位层叠子项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `alignContent` 为 `"topStart"`/`"top"`/`"topEnd"` THEN `ResolveStackAlignContent` 返回对应九值枚举（`ExtendedStackComponent.cpp:24-54`） | 正常 |
| AC-2.2 | WHEN 为 `"start"`/`"center"`/`"end"`/`"bottomStart"`/`"bottom"`/`"bottomEnd"` THEN 返回对应枚举 | 正常 |
| AC-2.3 | WHEN 缺省或非法 THEN 回退 `center`（CENTER）（`ExtendedStackComponent.cpp:53,110-115`） | 边界 |
| AC-2.4 | WHEN `ApplyPrivateAttributes` THEN 初始 `SetAlignContent(CENTER)`（`ExtendedStackComponent.cpp:67-71`） | 正常 |
| AC-2.5 | WHEN 落盘 THEN `SetNodeStackAlignContent`（`ExtendedStackComponent.cpp:118-121`） | 正常 |

### US-3: 子组件列表解析与模板展开

**作为** 生成式 UI 宿主开发者,
**我想要** Stack 支持静态 ID 数组与模板对象,
**以便** 既渲染固定层叠集合又从数据列表动态生成层。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `children` 为数组/模板对象 THEN 经 `ValidateChildListSchema` 校验（`ExtendedStackComponent.cpp:73-78`） | 正常 |
| AC-3.2 | WHEN 非法结构 THEN 上报 schema warning | 异常 |
| AC-3.3 | WHEN 模板展开 THEN `ExpandTemplateChildrenEager`（`ExtendedStackComponent.cpp:98-102`） | 正常 |

### US-4: 无私有属性（仅基类委托）

**作为** 生成式 UI 宿主开发者,
**我想要** Stack 复用扩展组件基类的通用属性与 styles,
**以便** Stack 只声明特有 `alignContent` 样式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `GetPrivatePropertyDeclaration(name)` 被调用 THEN 直接委托 `ExtendedComponent::GetPrivatePropertyDeclaration`（`ExtendedStackComponent.cpp:93-96`） | 正常 |
| AC-4.2 | WHEN `styles.alignContent` 被样式校验 THEN `ValidateComponentSpecificStylesSchema` 校验九值（`ExtendedStackComponent.cpp:80-84`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-4 | ArkTS 单测 + C++ UT | `A2UIExtendedComponents.ets:194-204`、`ExtendedStackComponent.cpp:58-65` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-4 | C++ UT：`ResolveStackAlignContent` | `ExtendedStackComponent.cpp:24-54` |
| AC-3.1,AC-3.2,AC-3.3 | R-3 | T-4 | C++ UT：`ChildListParser` | `ExtendedStackComponent.cpp:73-78,98-102` |
| AC-4.1,AC-4.2 | R-4 | T-4 | C++ UT | `ExtendedStackComponent.cpp:80-96` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 创建 `Stack` | 返回 STACK 原生节点组件，`GetType()=="Stack"` | — | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 边界 | `alignContent` 缺省/非法 | 回退 `center`（CENTER） | 九值枚举 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 异常 | `children` 非法结构 | 上报 schema warning，空数组允许 | 静态数组/模板二态 | AC-3.1,AC-3.2,AC-3.3 |
| R-4 | 行为 | 无私有属性声明 | 委托基类通用属性 | 仅 alignContent 特有样式 | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测 + C++ UT | type/STACK 节点 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 alignContent | C++ UT | 九值映射与回退 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 children | C++ UT | 静态/模板/非法 |
| VM-4 | AC-4.1,AC-4.2 私有属性 | C++ UT | 基类委托 |

## API 变更分析

> 存量补录，无新增/变更 Public API。组件经内部 `CatalogItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `createExtendedNativeCatalogItem('Stack')`（内部） | 既有 | 目录项构造 | 不直接暴露给宿主 | AC-1.1 |
| `ExtendedStackComponent::SetAlignContent`（内部） | 既有 | 属性落盘 | 框架内部 | AC-2.4,AC-2.5 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ResolveStackAlignContent(alignContent)`（`ExtendedStackComponent.cpp:24-54`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static A2UIAlignment ResolveStackAlignContent(const std::string& alignContent)` |
| 返回值 | `A2UIAlignment` — TOP_START/TOP/TOP_END/START/CENTER/END/BOTTOM_START/BOTTOM/BOTTOM_END，非法回退 CENTER |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3 |

**`ExtendedStackComponent::SetAlignContent(alignment)`（`ExtendedStackComponent.cpp:118-121`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void SetAlignContent(A2UIAlignment alignment)` |
| 返回值 | void — 经 `SetNodeStackAlignContent` 落盘 |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| alignContent | string | 否 | `"center"` | 九值枚举，非法回退 center |
| children | array/object | 否 | `[]` | 非空 ID 数组或 `{componentId,path}` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | alignContent=`"topEnd"` | 子项对齐顶部尾端（TOP_END） | AC-2.1 |
| 2 | alignContent 非法 | 回退 center（CENTER） | AC-2.3 |
| 3 | 构造未指定 alignContent | 默认 center（CENTER） | AC-2.4 |
| 4 | children 为模板对象 | Eager 展开层叠模板 | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 Catalog v1.0.0。
- **API 版本号策略:** 组件 schema 由 `schema/Extended/components/ExtendedStack.json` 声明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 组件三件套 | 注册/实现/样式解析分层 | AC-1.1,AC-1.2,AC-1.3 |
| 枚举回退 | 非法 token 回退默认 center | AC-2.3 |
| 子列表二态 | children 仅支持静态数组/模板对象 | AC-3.1,AC-3.2,AC-3.3 |
| 无私有属性 | 仅 alignContent 特有样式，其余委托基类 | AC-4.1,AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 alignContent 不崩溃，回退 center | C++ UT | `ExtendedStackComponent.cpp:53` |
| 性能 | Eager 展开层叠子项 | ohosTest | `ExtendedStackComponent.cpp:98-102` |
| 可测试性 | ResolveStackAlignContent 纯函数 | C++ UT | `ExtendedStackComponent.cpp:24-54` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 层叠语义与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 子组件 accessibility 透传 | 通用属性归 overview |
| 大字体 | 否 | 层叠容器不涉及字号 | — |
| 深色模式 | 否 | 阴影主题重应用由 `ExtendedComponent::OnConfigChange` 承接 | `ExtendedComponent.cpp:841-854` |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 否 | 无差异 | — |
| 生态兼容 | 是 | A2UI 扩展协议 v1.0.0 Stack 兼容 | `extended_catalog.json` Stack 段 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Stack 组件
  作为 生成式 UI 宿主开发者
  我想要 Stack 层叠排列子组件并支持对齐
  以便 正确渲染服务端下发的层叠布局

  Scenario: 静态子组件层叠
    Given DSL 组件为 {"component":"Stack","id":"root","children":["bg","title"]}
    When 引擎应用组件描述
    Then Stack 创建原生 STACK 节点并按顺序层叠挂载 bg、title

  Scenario: 非法 alignContent 回退默认
    Given DSL 组件为 {"component":"Stack","styles":{"alignContent":"invalid"},"children":["a"]}
    When 引擎解析 alignContent
    Then alignContent 回退为 "center"

  Scenario Outline: alignContent 枚举映射
    Given Stack 组件 alignContent 为 <token>
    When 引擎解析 alignContent
    Then 映射为 <alignment> 落盘

    Examples:
      | token       | alignment   |
      | topStart    | TOP_START   |
      | top         | TOP         |
      | topEnd      | TOP_END     |
      | start       | START       |
      | center      | CENTER      |
      | end         | END         |
      | bottomStart | BOTTOM_START|
      | bottom      | BOTTOM      |
      | bottomEnd   | BOTTOM_END  |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-04 做 Stack 布局；通用属性归 overview）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "genui/full_render"
    query: "ExtendedStackComponent ResolveStackAlignContent alignContent 九值枚举 回退 center"
  - repo: "genui/full_render"
    query: "ExtendedStackComponent SetAlignContent SetNodeStackAlignContent ApplyPrivateAttributes"
  - repo: "genui/full_render"
    query: "ExtendedStackComponent ExpandTemplateChildrenEager ChildListParser STACK 层叠"
```

**关键文档：** `genui/src/main/cpp/components/extended/ExtendedStackComponent.cpp`、`genui/src/main/cpp/components/extended/ExtendedStackComponent.h`、`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`、`specification/extended/1.0.0/extended_catalog.json`