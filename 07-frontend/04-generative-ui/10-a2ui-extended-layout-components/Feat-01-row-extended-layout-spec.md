# 特性规格

> Func-07-04-10-Feat-01 Row 组件：固化 A2UI 扩展协议布局容器 Row 的水平排列语义——目录注册（`type='Row'`，API≥23 走 C++ `ExtendedRowComponent`（FLEX 原生节点），API<23 走 ArkTS `ExtendedRow`（Flex）兼容路径）、顶层私有属性 `itemMargin` 与 styles 特有样式 `justifyContent`/`alignItems`/`wrap` 的枚举映射与非法回退、`children` 静态 ID 数组/模板对象二态解析与 Eager 展开、16.0vp 默认子组件间距。基准实现：`@arkui-genius/genui`（full_render）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Row 组件 |
| 特性编号 | Func-07-04-10-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 扩展协议 Catalog v1.0.0（ohos.a2ui.extended.catalog） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-10 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/10-a2ui-extended-layout-components/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 组件实现（C++） | `genui/src/main/cpp/components/extended/ExtendedRowComponent.{h,cpp}` | — |
| 组件基类（C++） | `genui/src/main/cpp/components/extended/ExtendedComponent.{h,cpp}` | — |
| 组件工厂（C++） | `genui/src/main/cpp/components/extended/ExtendedComponentFactory.cpp` | — |
| ETS 兼容路径 | `genui/src/main/ets/core/components/extended/ExtendedRow.ets` | API<23 |
| 子列表解析（C++） | `genui/src/main/cpp/composition/ChildListParser.{h,cpp}` | — |
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（Row 段） | 契约 |
| 组件参考（Docs） | `reference/extended-components/row.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Row 目录注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `component: "Row"` 识别为扩展原生布局容器,
**以便** 服务端下发的 Row 组件经扩展 Catalog 被正确渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `allA2UIExtendedComponents()` 被调用 THEN 返回的目录项数组包含 name=`Row` 的目录项（`A2UIExtendedComponents.ets:28-45,194-204`） | 正常 |
| AC-1.2 | WHEN 构造 `Row` 目录项 THEN `createExtendedNativeSchema('Row')` 加载 `schema/Extended/components/ExtendedRow.json`（`A2UIExtendedComponents.ets:51,145-157`） | 正常 |
| AC-1.3 | WHEN `ExtendedComponentFactory::CreateComponent("Row")` 被调用 THEN 经 `GetShortName` 匹配返回 `ExtendedRowComponent` 实例（`ExtendedComponentFactory.cpp:79-90,111`） | 正常 |
| AC-1.4 | WHEN `ExtendedRowComponent` 构造 THEN `CreateNode(A2UINodeType::FLEX)` 创建原生 FLEX 节点（`ExtendedRowComponent.cpp:83`） | 正常 |
| AC-1.5 | WHEN `GetType()` 被调用 THEN 返回 `"Row"`（`ExtendedRowComponent.cpp:85-88`） | 正常 |

### US-2: 子组件水平间距（itemMargin）

**作为** 生成式 UI 宿主开发者,
**我想要** Row 在子组件之间施加水平间距,
**以便** 相邻子组件保持可读的水平间隔。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN Row 构造且未指定 itemMargin THEN `itemMargin_` 取 `DEFAULT_ITEM_MARGIN=16.0F`（`ExtendedRowComponent.h:40`、`ExtendedRowComponent.cpp:122-132`） | 正常 |
| AC-2.2 | WHEN itemMargin 为 `5` THEN `SetItemMargin` 将 `itemMargin_` 置 5 并经 `SetSpace` 落盘（`ExtendedRowComponent.cpp:251-259,276-283`） | 正常 |
| AC-2.3 | WHEN itemMargin 为负数或非法值 THEN 上报 `SCHEMA_ERROR_CODE_INVALID_VALUE` 并回退 `DEFAULT_ITEM_MARGIN`（`ExtendedRowComponent.cpp:251-259`、`NormalizeItemMargin` `:70-73`） | 边界 |
| AC-2.4 | WHEN 间距经 Flex space 表达 THEN `SetNodeFlexSpace(nativeView_, space, space/2.0F)`（main=space、cross=space/2）（`ExtendedRowComponent.cpp:282`） | 正常 |

### US-3: 主轴排列（justifyContent）枚举映射

**作为** 生成式 UI 宿主开发者,
**我想要** Row 沿水平方向排列子组件,
**以便** 通过 `justifyContent` 控制子组件在主轴分布。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `justifyContent` 为 `"start"`/`"center"`/`"end"` THEN `ResolveRowJustify` 分别返回 `START`/`CENTER`/`END`（`ExtendedRowComponent.cpp:28-46`） | 正常 |
| AC-3.2 | WHEN `justifyContent` 为 `"spaceAround"`/`"spaceBetween"`/`"spaceEvenly"` THEN 分别返回 `SPACE_AROUND`/`SPACE_BETWEEN`/`SPACE_EVENLY`（`ExtendedRowComponent.cpp:36-44`） | 正常 |
| AC-3.3 | WHEN `justifyContent` 缺省或为非法值 THEN 回退 `"start"`，映射为 `START`（`ExtendedRowComponent.cpp:141-145`、`:45`） | 边界 |
| AC-3.4 | WHEN `justifyContent` 为三个均分值 THEN `IsItemMarginDisabledByJustify` 返回 true，间距不施加（`ExtendedRowComponent.cpp:75-79`、`:271-274`） | 正常 |
| AC-3.5 | WHEN `justifyContent` 经 `ApplyFlexOptions` 落盘 THEN `SetNodeFlexOption` 以 `A2UIFlexAlignment` 传入（`ExtendedRowComponent.cpp:285-293`） | 正常 |

### US-4: 交叉轴对齐（alignItems）枚举映射

**作为** 生成式 UI 宿主开发者,
**我想要** Row 沿垂直方向对齐子组件,
**以便** 通过 `alignItems` 控制子组件顶部/居中/底部对齐。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `alignItems` 为 `"top"`/`"center"`/`"bottom"` THEN `ResolveRowAlign` 分别返回 `START`/`CENTER`/`END`（`ExtendedRowComponent.cpp:48-60`） | 正常 |
| AC-4.2 | WHEN `alignItems` 缺省或为非法值 THEN 回退 `"center"`，映射为 `CENTER`（`ExtendedRowComponent.cpp:157-162`、`:59`） | 边界 |
| AC-4.3 | WHEN styles 增量更新不含 `alignItems` THEN 保留当前样式态（`hasStyleAlignItems_` 逻辑，`ExtendedRowComponent.cpp:212-230`） | 边界 |

### US-5: 换行模式（wrap）

**作为** 生成式 UI 宿主开发者,
**我想要** Row 支持单行与多行布局,
**以便** 通过 `wrap` 控制子组件在空间不足时是否换行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `wrap` 为 `"wrap"` THEN `ResolveRowWrap` 返回 `WRAP`（`ExtendedRowComponent.cpp:62-68`） | 正常 |
| AC-5.2 | WHEN `wrap` 为 `"noWrap"` 或非法值 THEN 返回 `NO_WRAP`（`ExtendedRowComponent.cpp:67`、`ExtendedRowComponent.cpp:173-178`） | 边界 |
| AC-5.3 | WHEN `wrap` 经 `ApplyFlexOptions` 落盘 THEN 以 `A2UIFlexWrap` 传入 `SetNodeFlexOption`（`ExtendedRowComponent.cpp:291-292`） | 正常 |

### US-6: 子组件列表解析与模板展开

**作为** 生成式 UI 宿主开发者,
**我想要** Row 支持静态 ID 数组与模板对象两种子组件描述,
**以便** 既渲染固定集合又从数据列表动态生成子组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `children` 为字符串数组 THEN `ChildListParser::ParseChildren` 返回 `STATIC_IDS`（`ChildListParser.cpp`、`ExtendedComponent.cpp:872-879`） | 正常 |
| AC-6.2 | WHEN `children` 为含 `componentId`+`path` 的对象 THEN 返回 `TEMPLATE_PATH` | 正常 |
| AC-6.3 | WHEN `children` 为空/非法结构 THEN `ValidateChildListSchema` 上报 warning（`ExtendedRowComponent.cpp:182-187`） | 异常 |
| AC-6.4 | WHEN 模板 children 展开 THEN `ExpandTemplateChildrenEager` 遍历 path 实例化模板子组件（`ExtendedComponent.cpp:881-895`） | 正常 |
| AC-6.5 | WHEN `children` 为空数组 THEN `ChildListEmptyArrayPolicy::ALLOW` 允许渲染为空容器（`ExtendedRowComponent.cpp:184`） | 边界 |

### US-7: API<23 ETS 兼容路径

**作为** 生成式 UI 宿主开发者,
**我想要** Row 在 API<23 上使用 ETS 兼容实现,
**以便** 规避原生 FLEX 属性刷新清除 Root margin 的缺陷。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `deviceInfo.sdkApiVersion < 23` THEN `getExtendedCustomDefinitions` 追加 `createExtendedRowDefinition()`（`A2UIExtendedComponents.ets:177-182`） | 正常 |
| AC-7.2 | WHEN `ExtendedRow` 构建 THEN 使用 `Flex({direction: Row})` 且 `space:{main:itemMargin, cross:itemMargin/2}`（`ExtendedRow.ets:124-133`） | 正常 |
| AC-7.3 | WHEN `ExtendedRow` 解析枚举 THEN `resolveJustifyContent/resolveAlignItems/resolveWrap` 与 C++ 语义一致（`ExtendedRow.ets:266-313`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-1 | ArkTS 单测 + C++ UT：目录注册与节点创建 | `A2UIExtendedComponents.ets:194-204`、`ExtendedComponentFactory.cpp:111`、`ExtendedRowComponent.cpp:83` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2,R-6 | T-1 | C++ UT：`SetItemMargin`/`SetSpace` | `ExtendedRowComponent.cpp:122-132,251-283` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3,R-6 | T-1 | C++ UT：`ResolveRowJustify` | `ExtendedRowComponent.cpp:28-46` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-1 | C++ UT：`ResolveRowAlign` | `ExtendedRowComponent.cpp:48-60` |
| AC-5.1,AC-5.2,AC-5.3 | R-5 | T-1 | C++ UT：`ResolveRowWrap` | `ExtendedRowComponent.cpp:62-68` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 | R-7 | T-1 | C++ UT：`ChildListParser::ParseChildren` + ohosTest | `ChildListParser.cpp`、`ExtendedComponent.cpp:872-895` |
| AC-7.1,AC-7.2,AC-7.3 | R-8 | T-1 | ArkTS 单测：`ExtendedRow` | `ExtendedRow.ets:124-133,266-313` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 调用 `CreateComponent("Row")` | 返回 FLEX 原生节点的 `ExtendedRowComponent`，`GetType()=="Row"` | 短名匹配去前缀 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | `itemMargin` 取非负数 | 落盘 `SetNodeFlexSpace(space, space/2)` | 默认 16.0F | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 行为 | `justifyContent` 取 6 值 | 映射 `A2UIFlexAlignment` 对应枚举 | 三均分值禁用间距 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 边界 | `alignItems` 缺省或非法 | 回退 `center`（CENTER） | 枚举三值 top/center/bottom | AC-4.1,AC-4.2,AC-4.3 |
| R-5 | 边界 | `wrap` 缺省或非法 | 回退 `noWrap`（NO_WRAP） | 枚举两值 | AC-5.1,AC-5.2,AC-5.3 |
| R-6 | 边界 | itemMargin 负数/非有限值 | 回退默认 16.0F 并上报 warning | 不回抛异常 | AC-2.3,AC-3.4 |
| R-7 | 异常 | `children` 非法结构 | 上报 schema warning，空数组允许 | 静态数组/模板对象二态 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |
| R-8 | 行为 | API<23 创建 Row | 走 ArkTS `ExtendedRow`（Flex） | 语义与 C++ 一致 | AC-7.1,AC-7.2,AC-7.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 + C++ UT | type/短名/FLEX 节点 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 itemMargin | C++ UT | 16.0 默认/负数回退/space 半间距 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 justify | C++ UT | 6 值与三均分值禁用间距 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 align | C++ UT | top/center/bottom 与回退 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 wrap | C++ UT | noWrap/wrap 与回退 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 子列表 | C++ UT | 静态/模板/非法三态 |
| VM-7 | AC-7.1,AC-7.2,AC-7.3 ETS 兼容 | ArkTS 单测 | API<23 Flex 语义 |

## API 变更分析

> 存量补录，无新增/变更 Public API。组件经内部 `CatalogItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `createExtendedNativeCatalogItem('Row')`（内部） | 既有 | 目录项构造 | 不直接暴露给宿主 | AC-1.1,AC-1.2 |
| `ExtendedRowComponent::SetItemMargin/SetSpace/ApplyFlexOptions`（内部） | 既有 | 属性落盘 | 框架内部 | AC-2.2,AC-3.5 |
| `createExtendedRowDefinition()`（内部，API<23） | 既有 | ETS 兼容目录项 | 框架内部 | AC-7.1,AC-7.2,AC-7.3 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ExtendedRowComponent::GetPrivatePropertyDeclaration("itemMargin")`（`ExtendedRowComponent.cpp:122-132`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `PropertyDeclaration CreateItemMarginPropertyDeclaration()` |
| 返回值 | `PropertyDeclaration` — type=NUMBER、allowDynamic/allowExpression=true、fallbackNumber=16.0F |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（非法值经 `ReportExtendedSchemaWarning` 上报 `SCHEMA_ERROR_CODE_INVALID_VALUE`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3 |

**`ResolveRowJustify(justify)`（`ExtendedRowComponent.cpp:28-46`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static A2UIFlexAlignment ResolveRowJustify(const std::string& justify)` |
| 返回值 | `A2UIFlexAlignment` — START/CENTER/END/SPACE_AROUND/SPACE_BETWEEN/SPACE_EVENLY；非法回退 START |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3 |

**`ResolveRowAlign(align)`（`ExtendedRowComponent.cpp:48-60`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static A2UIItemAlignment ResolveRowAlign(const std::string& align)` |
| 返回值 | `A2UIItemAlignment` — START/CENTER/END；非法回退 CENTER |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-4.1,AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| itemMargin | number | 否 | 16.0F | `[0,+inf)`，负数/非有限值回退默认 |
| justifyContent | string | 否 | `"start"` | 6 值枚举，非法回退 `start` |
| alignItems | string | 否 | `"center"` | `top/center/bottom`，非法回退 `center` |
| wrap | string | 否 | `"noWrap"` | `noWrap/wrap`，非法回退 `noWrap` |
| children | array/object | 否 | `[]` | 非空 ID 数组或 `{componentId,path}` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | itemMargin=5 | 子项水平间距 5vp，cross 间距 2.5vp | AC-2.2 |
| 2 | itemMargin=-1 | 回退 16vp 并上报 warning | AC-2.3 |
| 3 | justifyContent=`"spaceBetween"` | 主轴均分，itemMargin 不生效 | AC-3.4 |
| 4 | alignItems 非法 | 回退 center（CENTER） | AC-4.2 |
| 5 | wrap=`"wrap"` | 多行布局 | AC-5.1 |
| 6 | children 为模板对象 | Eager 展开模板子组件 | AC-6.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 Catalog v1.0.0；API<23 时 Row 走 ETS 兼容路径（`A2UIExtendedComponents.ets:179`），API≥23 走 C++ FLEX 原生路径。
- **API 版本号策略:** 组件 schema 由 `schema/Extended/components/ExtendedRow.json` 声明；双实现并存（RISK-4），语义需保持一致。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 组件三件套 | 注册/实现/样式解析分层，职责单一 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| 枚举回退 | 非法 token 一律回退默认值，不抛异常 | AC-3.3,AC-4.2,AC-5.2 |
| Flex space 半间距 | 间距经 `SetNodeFlexSpace(space, space/2)` 表达 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 子列表二态 | children 仅支持静态数组/模板对象，其余 warning | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |
| 双实现一致 | API<23 ETS 与 API≥23 C++ 语义对齐 | AC-7.1,AC-7.2,AC-7.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法枚举 token/itemMargin 不崩溃，回退默认值 | C++ UT | `ExtendedRowComponent.cpp:45,59,67,70-73` |
| 性能 | 模板展开为 Eager 遍历，无懒加载 | ohosTest | `ExtendedComponent.cpp:881-895` |
| 可测试性 | Resolve* 枚举映射为纯函数 | C++ UT | `ExtendedRowComponent.cpp:28-79` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 布局语义与设备无关（断点不参与 Row 布局） | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 子组件 accessibility 透传（通用属性归 overview） | `ExtendedRow.ets:147-148` |
| 大字体 | 否 | 布局容器不涉及字号 | — |
| 深色模式 | 否 | 阴影主题重应用由 `ExtendedComponent::OnConfigChange` 承接 | `ExtendedComponent.cpp:841-854` |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API<23 / API≥23 双路径 | 兼容性声明 |
| 生态兼容 | 是 | A2UI 扩展协议 v1.0.0 Row 兼容 | `extended_catalog.json` Row 段 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Row 组件
  作为 生成式 UI 宿主开发者
  我想要 Row 水平排列子组件并支持对齐/间距/换行
  以便 正确渲染服务端下发的行布局

  Scenario: 静态子组件水平排列
    Given DSL 组件为 {"component":"Row","id":"root","children":["a","b"]}
    When 引擎应用组件描述
    Then Row 创建原生 FLEX 节点并按顺序挂载子组件 a、b

  Scenario: 非法 alignItems 回退默认
    Given DSL 组件为 {"component":"Row","styles":{"alignItems":"stretch"},"children":["a"]}
    When 引擎解析 alignItems
    Then alignItems 回退为 "center"

  Scenario Outline: justifyContent 枚举映射
    Given Row 组件 justifyContent 为 <token>
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
- [x] 范围边界明确（Feat-01 做 Row 布局；通用属性归 overview，模板语义归 07-04-17）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "genui/full_render"
    query: "A2UIExtendedComponents allA2UIExtendedComponents Row createExtendedRowDefinition API<23 ETS 兼容"
  - repo: "genui/full_render"
    query: "ExtendedRowComponent ResolveRowJustify ResolveRowAlign ResolveRowWrap itemMargin SetNodeFlexSpace 枚举回退"
  - repo: "genui/full_render"
    query: "ExtendedComponentFactory GetShortName RegisterBuiltInComponents Row 短名匹配"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`、`genui/src/main/ets/core/components/extended/ExtendedRow.ets`、`genui/src/main/cpp/components/extended/ExtendedRowComponent.cpp`、`genui/src/main/cpp/components/extended/ExtendedComponentFactory.cpp`、`specification/extended/1.0.0/extended_catalog.json`