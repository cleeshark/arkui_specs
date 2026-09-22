# 特性规格

> Func-07-04-10-Feat-02 Column 组件：固化 A2UI 扩展协议布局容器 Column 的垂直排列语义——目录注册（`type='Column'`，C++ `ExtendedColumnComponent` 落 COLUMN 原生节点）、顶层私有属性 `itemMargin`（8.0vp 默认）经半间距 margin 施加、styles 特有样式 `justifyContent`/`alignItems` 枚举映射与非法回退、`children` 静态/模板二态解析与 Eager 展开、API<23 下 Row 子项的尾项间距兼容。基准实现：`@arkui-genius/genui`（full_render）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Column 组件 |
| 特性编号 | Func-07-04-10-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 扩展协议 Catalog v1.0.0（ohos.a2ui.extended.catalog） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 第二个 Feat，与 Feat-01 Row 共享 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/10-a2ui-extended-layout-components/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 组件实现（C++） | `genui/src/main/cpp/components/extended/ExtendedColumnComponent.{h,cpp}` | — |
| 组件工厂（C++） | `genui/src/main/cpp/components/extended/ExtendedComponentFactory.cpp` | — |
| 子列表解析（C++） | `genui/src/main/cpp/composition/ChildListParser.{h,cpp}` | — |
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（Column 段） | 契约 |
| 组件参考（Docs） | `reference/extended-components/column.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Column 目录注册与原生节点

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `component: "Column"` 识别为扩展原生垂直容器,
**以便** 服务端下发的 Column 组件被正确渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `allA2UIExtendedComponents()` 被调用 THEN 返回目录项包含 name=`Column`（`A2UIExtendedComponents.ets:33,52,194-204`） | 正常 |
| AC-1.2 | WHEN `ExtendedComponentFactory::CreateComponent("Column")` THEN 返回 `ExtendedColumnComponent`（`ExtendedComponentFactory.cpp:110`） | 正常 |
| AC-1.3 | WHEN 构造 THEN `CreateNode(A2UINodeType::COLUMN)`（`ExtendedColumnComponent.cpp:109-111`），`GetType()=="Column"`（`:113-116`） | 正常 |

### US-2: 子组件垂直间距（itemMargin）

**作为** 生成式 UI 宿主开发者,
**我想要** Column 在子组件之间施加垂直间距,
**以便** 相邻子组件保持可读的垂直间隔。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 未指定 itemMargin THEN `itemMargin_` 取 `DEFAULT_ITEM_MARGIN=8.0F`（`ExtendedColumnComponent.h:45`、`ExtendedColumnComponent.cpp:143-146`） | 正常 |
| AC-2.2 | WHEN 多子组件 THEN `ApplyItemMarginToChildren` 中间项上下各加 `halfMargin=itemMargin/2`（`ExtendedColumnComponent.cpp:260-280`） | 正常 |
| AC-2.3 | WHEN itemMargin 为负数或非法值 THEN 上报 `SCHEMA_ERROR_CODE_INVALID_VALUE` 并回退 8.0F（`ExtendedColumnComponent.cpp:236-244`） | 边界 |
| AC-2.4 | WHEN `justifyContent` 为三均分值 THEN `IsItemMarginDisabledByJustify` 使有效间距归 0（`ExtendedColumnComponent.cpp:84-88,231-234,260`） | 正常 |

### US-3: 主轴排列（justifyContent）枚举映射

**作为** 生成式 UI 宿主开发者,
**我想要** Column 沿垂直方向排列子组件,
**以便** 通过 `justifyContent` 控制子组件在主轴分布。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `justifyContent` 为 6 值 THEN `ResolveColumnJustify` 映射 `A2UIFlexAlignment`（`ExtendedColumnComponent.cpp:45-63`） | 正常 |
| AC-3.2 | WHEN 缺省或非法 THEN 回退 `"start"`（START）（`ExtendedColumnComponent.cpp:62,191-195`） | 边界 |
| AC-3.3 | WHEN `SetJustifyContent` 被调用 THEN 更新 `itemMarginDisabledByJustify_` 并落盘 `SetNodeColumnJustifyContent`（`ExtendedColumnComponent.cpp:229-234`） | 正常 |

### US-4: 交叉轴对齐（alignItems）枚举映射

**作为** 生成式 UI 宿主开发者,
**我想要** Column 沿水平方向对齐子组件,
**以便** 通过 `alignItems` 控制子组件起始/居中/末端对齐。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `alignItems` 为 `"start"`/`"center"`/`"end"` THEN `ResolveColumnAlign` 映射 START/CENTER/END（`ExtendedColumnComponent.cpp:65-77`） | 正常 |
| AC-4.2 | WHEN 缺省或非法 THEN 回退 `"start"`（`ExtendedColumnComponent.cpp:76,186-190`） | 边界 |
| AC-4.3 | WHEN `ApplyPrivateAttributes` THEN 初始 `SetAlignItems(START)`、`SetJustifyContent(START)`（`ExtendedColumnComponent.cpp:118-123`） | 正常 |

### US-5: 子组件列表解析与模板展开

**作为** 生成式 UI 宿主开发者,
**我想要** Column 支持静态 ID 数组与模板对象,
**以便** 既渲染固定集合又从数据列表动态生成子组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `children` 为数组/模板对象 THEN `CollectChildListDescriptor` 经 `ChildListParser::ParseChildren` 解析（`ExtendedColumnComponent.cpp:125-132`） | 正常 |
| AC-5.2 | WHEN 非法结构 THEN `ValidateComponentDescriptorSchema` 上报 warning（`ExtendedColumnComponent.cpp:157-162`） | 异常 |
| AC-5.3 | WHEN 模板展开 THEN `ExpandTemplateChildrenEager`（`ExtendedComponent.cpp:888`） | 正常 |

### US-6: 子项增删移动的间距重刷与恢复

**作为** 生成式 UI 宿主开发者,
**我想要** Column 子项增删移动时刷新间距并在移除时恢复 margin,
**以便** 避免间距叠加泄漏。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 新增/移动子项 THEN `OnAddChild/OnMoveChild` 调用 `ApplyItemMarginToChildren` 刷新（`ExtendedColumnComponent.cpp:198-209`） | 正常 |
| AC-6.2 | WHEN 移除子项 THEN `OnRemoveChild` 先 `RestoreCommonMarginForChild` 再刷新（`ExtendedColumnComponent.cpp:211-216`） | 正常 |
| AC-6.3 | WHEN 清空全部 THEN `RemoveAllChildren` 先 `RestoreCommonMarginForChildren`（`ExtendedColumnComponent.cpp:218-222`） | 正常 |
| AC-6.4 | WHEN API<23 且下一子项为 Row THEN 完整单项间距施加于前一子项（`useTrailingItemMargin`、`MIN_API_VERSION_NATIVE_ROW=23`、`IsRowChild`）（`ExtendedColumnComponent.cpp:33-43,272-279`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-2 | ArkTS 单测 + C++ UT | `A2UIExtendedComponents.ets:194-204`、`ExtendedColumnComponent.cpp:109-116` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2,R-6 | T-2 | C++ UT：半间距 margin | `ExtendedColumnComponent.cpp:246-282` |
| AC-3.1,AC-3.2,AC-3.3 | R-3,R-6 | T-2 | C++ UT：`ResolveColumnJustify` | `ExtendedColumnComponent.cpp:45-63` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-2 | C++ UT：`ResolveColumnAlign` | `ExtendedColumnComponent.cpp:65-77` |
| AC-5.1,AC-5.2,AC-5.3 | R-5 | T-2 | C++ UT：`ChildListParser` | `ExtendedColumnComponent.cpp:125-132` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4 | R-7 | T-2 | C++ UT：增删移动 | `ExtendedColumnComponent.cpp:198-297` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 创建 `Column` | 返回 COLUMN 原生节点组件，`GetType()=="Column"` | — | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | `itemMargin` 取非负数 | 半间距 margin 施加于子项上下 | 默认 8.0F | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 行为 | `justifyContent` 取 6 值 | 映射 `A2UIFlexAlignment` | 三均分值禁用间距 | AC-3.1,AC-3.2,AC-3.3 |
| R-4 | 边界 | `alignItems` 缺省或非法 | 回退 `start`（START） | 枚举三值 | AC-4.1,AC-4.2,AC-4.3 |
| R-5 | 异常 | `children` 非法结构 | 上报 schema warning | 空数组允许 | AC-5.1,AC-5.2,AC-5.3 |
| R-6 | 边界 | itemMargin 负数/非有限值 | 回退 8.0F 并上报 warning | 不回抛异常 | AC-2.3,AC-3.2 |
| R-7 | 行为 | 子项增删移动 | 刷新间距并在移除/清空时恢复 margin | API<23 Row 子项尾项间距 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测 + C++ UT | type/COLUMN 节点 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 itemMargin | C++ UT | 8.0 默认/半间距/回退 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 justify | C++ UT | 6 值/回退/禁用间距 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 align | C++ UT | start/center/end/回退 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 children | C++ UT | 静态/模板/非法 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 增删移动 | C++ UT | 间距刷新与 margin 恢复 |

## API 变更分析

> 存量补录，无新增/变更 Public API。组件经内部 `CatalogItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `createExtendedNativeCatalogItem('Column')`（内部） | 既有 | 目录项构造 | 不直接暴露给宿主 | AC-1.1 |
| `ExtendedColumnComponent::SetAlignItems/SetJustifyContent/SetItemMargin`（内部） | 既有 | 属性落盘 | 框架内部 | AC-3.3,AC-4.1 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ExtendedColumnComponent::GetPrivatePropertyDeclaration("itemMargin")`（`ExtendedColumnComponent.cpp:134-155`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `PropertyDeclaration CreateItemMarginPropertyDeclaration()` |
| 返回值 | `PropertyDeclaration` — type=NUMBER、fallbackNumber=8.0F |
| 开放范围 | 内部 |
| 错误码 | N/A（非法值上报 `SCHEMA_ERROR_CODE_INVALID_VALUE`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3 |

**`ResolveColumnJustify(justify)`（`ExtendedColumnComponent.cpp:45-63`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static A2UIFlexAlignment ResolveColumnJustify(const std::string& justify)` |
| 返回值 | `A2UIFlexAlignment` — 6 值映射，非法回退 START |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-3.1,AC-3.2 |

**`ResolveColumnAlign(align)`（`ExtendedColumnComponent.cpp:65-77`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static A2UIHorizontalAlignment ResolveColumnAlign(const std::string& align)` |
| 返回值 | `A2UIHorizontalAlignment` — START/CENTER/END，非法回退 START |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-4.1,AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| itemMargin | number | 否 | 8.0F | `[0,+inf)`，负数/非有限值回退默认 |
| justifyContent | string | 否 | `"start"` | 6 值枚举，非法回退 `start` |
| alignItems | string | 否 | `"start"` | `start/center/end`，非法回退 `start` |
| children | array/object | 否 | `[]` | 非空 ID 数组或 `{componentId,path}` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | itemMargin=8（默认） | 中间项上下各加 4vp margin | AC-2.2 |
| 2 | itemMargin=-1 | 回退 8vp 并上报 warning | AC-2.3 |
| 3 | justifyContent=`"spaceBetween"` | 主轴均分，间距归 0 | AC-2.4 |
| 4 | alignItems 非法 | 回退 start（START） | AC-4.2 |
| 5 | 移除子项 | 恢复该子项 margin 并刷新其余 | AC-6.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 Catalog v1.0.0；API<23 Row 子项走 `useTrailingItemMargin` 兼容（`ExtendedColumnComponent.cpp:33`）。
- **API 版本号策略:** 组件 schema 由 `schema/Extended/components/ExtendedColumn.json` 声明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 组件三件套 | 注册/实现/样式解析分层 | AC-1.1,AC-1.2,AC-1.3 |
| 半间距 margin | 间距经 margin 表达，方向垂直 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 枚举回退 | 非法 token 回退默认值 | AC-3.2,AC-4.2 |
| margin 恢复 | 移除/清空时恢复子项 margin | AC-6.2,AC-6.3 |
| API 兼容 | API<23 Row 子项尾项间距 | AC-6.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法值不崩溃，回退默认 | C++ UT | `ExtendedColumnComponent.cpp:79-82,236-244` |
| 性能 | 间距刷新为单次遍历子项 | C++ UT | `ExtendedColumnComponent.cpp:246-282` |
| 可测试性 | Resolve* 纯函数 | C++ UT | `ExtendedColumnComponent.cpp:45-77` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 布局语义与设备无关（断点不参与 Column） | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 子组件 accessibility 透传（通用属性归 overview） | `ExtendedComponent` 通用属性 |
| 大字体 | 否 | 布局容器不涉及字号 | — |
| 深色模式 | 否 | 阴影主题重应用由 `ExtendedComponent::OnConfigChange` 承接 | `ExtendedComponent.cpp:841-854` |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API<23/API≥23 间距兼容差异 | 兼容性声明 |
| 生态兼容 | 是 | A2UI 扩展协议 v1.0.0 Column 兼容 | `extended_catalog.json` Column 段 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Column 组件
  作为 生成式 UI 宿主开发者
  我想要 Column 垂直排列子组件并支持对齐/间距
  以便 正确渲染服务端下发的列布局

  Scenario: 静态子组件垂直排列
    Given DSL 组件为 {"component":"Column","id":"root","children":["a","b"]}
    When 引擎应用组件描述
    Then Column 创建原生 COLUMN 节点并按顺序挂载子组件 a、b

  Scenario: 非法 alignItems 回退默认
    Given DSL 组件为 {"component":"Column","styles":{"alignItems":"stretch"},"children":["a"]}
    When 引擎解析 alignItems
    Then alignItems 回退为 "start"

  Scenario Outline: justifyContent 枚举映射
    Given Column 组件 justifyContent 为 <token>
    When 引擎解析 justifyContent
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
- [x] 范围边界明确（Feat-02 做 Column 布局；通用属性归 overview）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "genui/full_render"
    query: "ExtendedColumnComponent itemMargin DEFAULT_ITEM_MARGIN 8.0 ApplyItemMarginToChildren 半间距 margin"
  - repo: "genui/full_render"
    query: "ExtendedColumnComponent ResolveColumnJustify ResolveColumnAlign SetAlignItems SetJustifyContent 枚举回退"
  - repo: "genui/full_render"
    query: "ExtendedColumnComponent OnAddChild OnRemoveChild RestoreCommonMargin MIN_API_VERSION_NATIVE_ROW 23 IsRowChild"
```

**关键文档：** `genui/src/main/cpp/components/extended/ExtendedColumnComponent.cpp`、`genui/src/main/cpp/components/extended/ExtendedColumnComponent.h`、`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`、`specification/extended/1.0.0/extended_catalog.json`