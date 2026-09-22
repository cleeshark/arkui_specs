# 特性规格

> Func-07-04-20-Feat-01 自定义组件注册与使用：固化以 `CatalogItem{name,schemaProvider,componentBuilder}` 为注册单元的自定义组件契约、`ComponentBuilder=WrappedBuilder<[CustomComponentAttribute]>` 构建器类型、`CustomComponentAttribute` 运行时上下文（含 `ChangeReason` 三态与 `resolver` 绑定）、Catalog 同名替换注册语义，以及 C++ `CustomComponent` 实例化 → NAPI 回调 ArkTS 构建/更新的完整链路。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自定义组件注册与使用 |
| 特性编号 | Func-07-04-20-Feat-01 |
| 优先级 | P0 |
| 目标版本 | OpenHarmony API Version 13 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-20 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/20-custom-components-functions/design.md` | Baselined |
| 组件注册契约（ArkTS） | `genui/src/main/ets/interface/CatalogItem.ets` | — |
| 目录注册接口（ArkTS） | `genui/src/main/ets/interface/Catalog.ets` | — |
| 目录实现（ArkTS） | `genui/src/main/ets/core/base/CatalogImpl.ets` | — |
| 组件工厂（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomComponentFactory.ets` | — |
| 组件运行时上下文（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomComponent.ets` | — |
| 原生组件实现（C++） | `genui/src/main/cpp/components/custom/CustomComponent.cpp/.h` | — |
| 原生组件工厂（C++） | `genui/src/main/cpp/components/CustomComponentFactory.cpp` | — |
| 属性填充（C++） | `genui/src/main/cpp/components/custom/CustomComponentAttributeValue.cpp` | — |
| 开发者指南（Docs） | `guides/creating-custom-components.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: CatalogItem 注册与查询

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `Catalog.addCatalogItem` 注册自定义组件并支持移除/查询,
**以便** DSL 的 `component` 字段能按名称命中组件定义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `addCatalogItem` 传入合法 `CatalogItem`（name 非空、schemaProvider/componentBuilder 存在）THEN 返回 true 且该组件加入 `CatalogImpl.components`（`CatalogImpl.ets:73-80`） | 正常 |
| AC-1.2 | WHEN `addCatalogItem` 传入 name 为空或 schemaProvider/componentBuilder 缺失的 item THEN `fromComponentItem` 返回 undefined，`addCatalogItem` 返回 false 且不加入（`core/base/CatalogItem.ets:110-127`、`CatalogImpl.ets:73-77`） | 异常 |
| AC-1.3 | WHEN 注册同名组件 THEN `addOrReplaceItem` 按 name 替换既有定义（不追加重复项）（`CatalogImpl.ets:123-130`） | 正常 |
| AC-1.4 | WHEN `removeCatalogItem` 传入已存在 name THEN 返回 true 并移除；传入不存在 name THEN 返回 false（`CatalogImpl.ets:82-84,132-139`） | 正常 |
| AC-1.5 | WHEN `hasCatalogItem`/`getAllCatalogItemNames` 被调用 THEN 分别返回布尔判定与全部组件 name 列表（`CatalogImpl.ets:86-92`） | 正常 |

### US-2: ComponentBuilder 契约

**作为** 生成式 UI 宿主开发者,
**我想要** 用 `wrapBuilder(@Builder)` 包装组件构建器,
**以便** 引擎按 `ComponentBuilder=WrappedBuilder<[CustomComponentAttribute]>` 类型注入运行时上下文。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `ComponentBuilder` 类型被引用 THEN 其定义为 `WrappedBuilder<[CustomComponentAttribute]>`，仅接收一个 `CustomComponentAttribute` 参数（`interface/CatalogItem.ets:121`） | 正常 |
| AC-2.2 | WHEN 组件无自定义 builder THEN 使用 `EMPTY_COMPONENT_BUILDER`（`wrapBuilder(emptyNativeComponentBuilder)`）占位，空 builder 函数不渲染任何内容（`core/base/CatalogItem.ets:21-25`） | 边界 |
| AC-2.3 | WHEN 用 `CatalogItem.forComponent` 构造组件目录项 THEN `type` 恒为 `COMPONENT`、`category` 缺省 `OHOS_EXTENDS`、`isInnerNative` 缺省 false、`preserveDynamicDescriptors` 缺省 false（`core/base/CatalogItem.ets:74-87,100-108`） | 正常 |

### US-3: CustomComponentAttribute 运行时上下文

**作为** 自定义组件构建器实现者,
**我想要** 获得只读的 `CustomComponentAttribute` 上下文,
**以便** 读取类型/id/surfaceId/主题/resolver/changeReason 等运行时信息。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 引擎调用组件 builder THEN `CustomComponentAttribute` 提供只读字段 `type`/`id`/`surfaceId`/`protocolVersion`/`catalogId`/`componentTheme`/`resolver`/`changeReason` 与可选 `customProps`（`interface/CatalogItem.ets:71-116`） | 正常 |
| AC-3.2 | WHEN C++ 侧填充 attribute identity THEN 写入 `type`/`id`/`surfaceId`/`renderId`/`customComponentHandle`，并在非空时写入 `protocolVersion`/`catalogId`（`CustomComponentAttributeValue.cpp:77-98`） | 正常 |
| AC-3.3 | WHEN 组件带 `properties`（size/width/height/weight/margin/accessibility* 等）THEN `PopulateAttributeCommonProperties` 将非空项写入 `properties` 子对象（`CustomComponentAttributeValue.cpp:115-157`） | 正常 |
| AC-3.4 | WHEN Surface 的 DataModel 根存在且非空 THEN `PopulateAttributeDataModel` 将根序列化为 `dataModelJson` 注入 attribute（`CustomComponentAttributeValue.cpp:159-183`） | 正常 |

### US-4: changeReason 判定

**作为** 自定义组件构建器实现者,
**我想要** 感知本次重渲染原因,
**以便** 区分组件更新、主题切换与断点变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 首次创建组件（无 previousSnapshot）THEN `resolveChangeReason` 返回 `UPDATE_COMPONENT`（`CustomComponentFactory.ets:258-260`） | 正常 |
| AC-4.2 | WHEN `descriptorJson` 快照变化 THEN 返回 `UPDATE_COMPONENT`（`CustomComponentFactory.ets:261-263`） | 正常 |
| AC-4.3 | WHEN 仅 `colorMode` 变化 THEN 返回 `THEME_MODE_CHANGE`（`CustomComponentFactory.ets:264-266`） | 边界 |
| AC-4.4 | WHEN 仅 `breakpoint` 变化 THEN 返回 `BREAKPOINT_CHANGE`（`CustomComponentFactory.ets:267-269`） | 边界 |
| AC-4.5 | WHEN 仅 `componentThemeJson` 变化（colorMode/breakpoint 均未变）THEN 返回 `THEME_MODE_CHANGE`（`CustomComponentFactory.ets:270-272`） | 边界 |
| AC-4.6 | WHEN `ChangeReason` 枚举被引用 THEN 取值仅 `UPDATE_COMPONENT`/`THEME_MODE_CHANGE`/`BREAKPOINT_CHANGE` 三态（`interface/CatalogItem.ets:57-66`） | 正常 |

### US-5: 组件工厂注册与实例化

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎在渲染自定义组件时构建并更新 ArkUI 视图,
**以便** DSL 组件映射为实际 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `registerCustomComponent` 传入 type 非空定义 THEN 注册到 `definitions` 并幂等安装 NAPI 桥（`registerCreateCustomComponent`/`registerUpdateCustomComponent`）（`CustomComponentFactory.ets:135-141,160-170`） | 正常 |
| AC-5.2 | WHEN `registerCustomComponent` 传入 type 为空 THEN 直接返回不注册（`CustomComponentFactory.ets:136-138`） | 边界 |
| AC-5.3 | WHEN `createCustomComponent` 且 UIContext 未设置或 builder 未找到 THEN 返回 `{}`（空结果，静默降级）（`CustomComponentFactory.ets:473-482`） | 异常 |
| AC-5.4 | WHEN `createCustomComponent` 正常 THEN 构造 `CustomComponentAttribute`（含 resolver 与默认 `changeReason=UPDATE_COMPONENT`）并 `new ComponentContent`，返回 `{content, childSlot}`（`CustomComponentFactory.ets:491-505`） | 正常 |
| AC-5.5 | WHEN `updateCustomComponent` 传入 value 为 undefined/null 或 type 缺失或 builder 未找到 THEN 返回 `{}`（`CustomComponentFactory.ets:552-563`） | 异常 |
| AC-5.6 | WHEN 组件 type 按 `getShortType`（`.` 分隔末段）未精确命中时 THEN `findDefinition` 用短名兜底匹配（`CustomComponentFactory.ets:180-198`） | 边界 |
| AC-5.7 | WHEN `registerCatalogComponents` 处理 catalog items THEN 跳过 `isInnerNative` 或缺失 builder 的项，仅注册带 builder 的组件（`CustomComponentFactory.ets:143-158`） | 正常 |

### US-6: 原生组件实例化

**作为** 引擎实现者,
**我想要** C++ 侧以 `CustomComponent : Component` 承载自定义组件生命周期,
**以便** 组件树、数据绑定与更新统一走原生管线。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `CustomComponentFactory::Create(type)` 且 type 非空 THEN 返回 `shared_ptr<CustomComponent>`；type 为空返回 nullptr（`CustomComponentFactory.cpp:24-31`） | 正常 |
| AC-6.2 | WHEN 组件实例化 THEN `CustomComponent::CreateCustomComponent` 经 NAPI 回调 ArkTS 构建视图（`CustomComponent.cpp:1048`）；更新走 `UpdateCustomComponent`（`CustomComponent.cpp:1170`） | 正常 |
| AC-6.3 | WHEN 组件配置变化 THEN `OnConfigChange` 响应主题/配置更新（`CustomComponent.cpp:823`）；`GetType` 返回组件类型名（`CustomComponent.cpp:465`） | 正常 |
| AC-6.4 | WHEN 桥接注册 THEN `registerCreateCustomComponent`/`registerUpdateCustomComponent` 作为 NAPI 导出项注册（`NapiInit.cpp:44-47`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2,R-3 | T-1 | ArkTS 单测：`CatalogImpl` 组件注册/查询 | `CatalogImpl.ets:73-139` |
| AC-2.1,AC-2.2,AC-2.3 | R-4 | T-1 | ArkTS 单测：`CatalogItem.forComponent`/`EMPTY_COMPONENT_BUILDER` | `core/base/CatalogItem.ets:21-127` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-5 | T-1 | C++ UT：`CreateAttributeValue` 四段填充 | `CustomComponentAttributeValue.cpp:77-194` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 | R-6,R-7 | T-1 | ArkTS 单测：`resolveChangeReason` 快照对比 | `CustomComponentFactory.ets:239-274` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 | R-8,R-9 | T-1 | ArkTS 单测 + ohosTest：工厂注册/构建/更新 | `CustomComponentFactory.ets:118-598` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4 | R-10 | T-1 | C++ UT：`CustomComponentFactoryTest`/`CustomComponentTest` | `CustomComponentFactory.cpp:24-31`、`CustomComponent.cpp:1048,1170` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `addCatalogItem` 传入合法 CatalogItem | 归一化后加入 components 并返回 true | name 非空、schemaProvider/componentBuilder 存在 | AC-1.1 |
| R-2 | 异常 | `addCatalogItem` 传入空 name 或缺字段 | 归一化失败返回 false，不加入 | 空名/缺 schemaProvider/componentBuilder | AC-1.2 |
| R-3 | 行为 | 同名组件重复注册 | `addOrReplaceItem` 替换既有定义 | 按 name 精确匹配，不追加 | AC-1.3 |
| R-4 | 行为 | 组件目录项构造 | `forComponent` 固定 `type=COMPONENT`、`category` 缺省 OHOS_EXTENDS | `preserveDynamicDescriptors` 缺省 false | AC-2.1,AC-2.2,AC-2.3 |
| R-5 | 行为 | 引擎填充 attribute | identity/theme/customProps/properties/dataModelJson 分段写入 | 空字段跳过 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-6 | 行为 | 快照对比判定 changeReason | 按 descriptor→colorMode→breakpoint→componentThemeJson 顺序返回对应枚举 | 首建缺失快照返回 UPDATE_COMPONENT | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |
| R-7 | 边界 | 同次更新多因叠加 | 仅返回优先级最高的 reason | 判定顺序固定 | AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| R-8 | 行为 | 组件工厂注册/实例化 | definitions 注册 + NAPI 桥幂等安装 + ComponentContent 构建 | 桥注册幂等 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 |
| R-9 | 异常 | 组件未注册/空 UIContext/空 builder | 返回 `{}` 静默降级 | 无错误码上报 | AC-5.3,AC-5.5 |
| R-10 | 行为 | 原生组件实例化 | `CustomComponentFactory::Create` 构造 `CustomComponent` | 空 type 返回 nullptr | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 组件注册 | ArkTS 单测 | add/remove/has/getAll、同名替换、空名拒绝 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 构建器契约 | ArkTS 单测 | ComponentBuilder 类型、空 builder 占位 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 attribute 填充 | C++ UT | identity/theme/properties/dataModelJson |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 changeReason | ArkTS 单测 | 三态判定 + 优先级顺序 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 工厂注册/构建 | ArkTS 单测 + ohosTest | 注册、构建、更新、短名兜底 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 原生实例化 | C++ UT | Create/UpdateCustomComponent/OnConfigChange |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `CatalogItem`（公开接口） | 既有 | 组件注册单元 | name/schemaProvider/componentBuilder 三字段 | AC-1.1,AC-2.1 |
| `ComponentBuilder`（公开类型） | 既有 | 组件构建器类型 | `wrapBuilder` 包装 @Builder | AC-2.1 |
| `CustomComponentAttribute`（公开接口） | 既有 | 组件运行时上下文 | 只读，引擎注入 | AC-3.1 |
| `ChangeReason`（公开枚举） | 既有 | 重渲染原因 | 三态，宿主按需区分 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |
| `Catalog.addCatalogItem/removeCatalogItem/hasCatalogItem/getAllCatalogItemNames` | 既有 | 组件目录操作 | 返回 boolean/string[] | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：`genui/src/main/ets/interface/CatalogItem.ets`、`Catalog.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`Catalog.addCatalogItem(catalogItem)`（`CatalogImpl.ets:73`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `addCatalogItem(catalogItem: CatalogItem): boolean` |
| 返回值 | `boolean` — 归一化成功并入 Catalog |
| 开放范围 | Public |
| 错误码 | N/A（返回 false 表示拒绝） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**`CustomComponentFactory.createCustomComponent(value)`（`CustomComponentFactory.ets:473`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static createCustomComponent(value: CustomComponentDescriptor): CustomComponentResult` |
| 返回值 | `CustomComponentResult` — `{content?, childSlot?, childSlots?, childSlotsObject?}`；空 UIContext/未注册返回 `{}` |
| 开放范围 | 内部（framework-internal，经 NAPI 回调） |
| 错误码 | N/A（返回空对象） |
| 关联 AC | AC-5.3,AC-5.4 |

**`CustomComponent::CreateAttributeValue()`（`CustomComponentAttributeValue.cpp:185`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `napi_value CustomComponent::CreateAttributeValue() const` |
| 返回值 | `napi_value` — 组装完成的 attribute 对象 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| catalogItem | CatalogItem | 是 | — | name 非空；schemaProvider/componentBuilder 存在 |
| catalogItem.name | string | 是 | — | 与 DSL `component` 字段精确一致 |
| value.type | string | 是 | — | 已注册组件类型 |
| value.customProps | JsonValue | 否 | — | 非 null 时写入 attribute |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 CatalogItem 注册 | 返回 true 并入目录 | AC-1.1 |
| 2 | 空 name 注册 | 返回 false | AC-1.2 |
| 3 | 同名重复注册 | 替换旧定义 | AC-1.3 |
| 4 | 未注册组件 createCustomComponent | 返回 `{}` | AC-5.3 |
| 5 | 正常 createCustomComponent | 返回 `{content, childSlot}` | AC-5.4 |
| 6 | 首次创建 | changeReason=UPDATE_COMPONENT | AC-4.1 |
| 7 | 仅 breakpoint 变化更新 | changeReason=BREAKPOINT_CHANGE | AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** OpenHarmony API Version 13。
- **API 版本号策略:** 公开契约由 `@arkui-genius/genui` 声明；`preserveDynamicDescriptors` 为内部选项，公开 `CatalogItem` 未暴露（风险 RISK-3）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 同名替换 | 组件按 name 唯一，重复注册替换 | AC-1.3 |
| 桥幂等安装 | `ensureBridgeRegistered` 仅注册一次 NAPI 回调 | AC-5.1 |
| changeReason 优先级 | descriptor 变更优先于主题/断点 | AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| 静默降级 | 未注册/空 builder 不抛异常，返回空对象 | AC-5.3,AC-5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 未注册组件静默降级，不崩引擎 | ArkTS 单测 + ohosTest | `CustomComponentFactory.ets:473-482` |
| 性能 | 快照对比 O(1)（WeakMap 查 + 字符串/数值比较） | ArkTS 单测 | `CustomComponentFactory.ets:254-291` |
| 可测试性 | 工厂注册/构建/更新可独立单测 | C++ UT + ArkTS 单测 | `CustomComponentFactoryTest.cpp`、`CustomComponentTest.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 组件注册/构建与设备无关 | ohosTest | — |
| 平板 | 无差异（断点值不同，经 `changeReason=BREAKPOINT_CHANGE` 通知重渲染） | 同上 | ohosTest | — |
| 折叠屏 | 无差异（折叠触发断点变化） | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `properties.accessibilityLabel/accessibilityDescription` 注入 attribute | AC-3.3 |
| 大字体 | 否 | 字体缩放归 Surface 层 | — |
| 深色模式 | 是 | `componentTheme.colorMode/darkPrimaryColor` 注入；切换触发 `THEME_MODE_CHANGE` | AC-4.3 |
| 多窗口/分屏 | 否 | 多 Surface 归 Feat-06（07-04-01） | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 协议版本注入 `protocolVersion` 字段 | AC-3.2 |
| 生态兼容 | 是 | A2UI 扩展协议自定义组件语义兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 自定义组件注册与使用
  作为 生成式 UI 宿主开发者
  我想要 注册并使用自定义组件
  以便 DSL 的 component 字段映射为自定义 ArkUI 视图

  Scenario: 注册并命中组件
    Given Catalog 为空
    When 调用 addCatalogItem(weatherCardItem)
    Then 返回 true 且 getAllCatalogItemNames 含 "WeatherCard"

  Scenario Outline: 非法注册拒绝
    Given Catalog 为空
    When 调用 addCatalogItem(<item>)
    Then 返回 false

    Examples:
      | item |
      | {name:"", schemaProvider:f, componentBuilder:b} |
      | {name:"X"} |

  Scenario: 同名注册替换
    Given 已注册 name="A" 的 item1
    When 调用 addCatalogItem(name="A" 的 item2)
    Then getAllCatalogItemNames 仅含一个 "A"，且为 item2

  Scenario: 首次创建 changeReason
    Given 组件 type 已注册且 UIContext 就绪
    When 首次调用 createCustomComponent(descriptor)
    Then attribute.changeReason 为 UPDATE_COMPONENT
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做组件注册与使用；自定义函数见 Feat-02；内置组件实现归 07-04-02~16）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CatalogItem ComponentBuilder CustomComponentAttribute ChangeReason 契约定义"
  - repo: "GenerativeUI/A2UIRender"
    query: "CatalogImpl addCatalogItem addOrReplaceItem 同名替换语义"
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomComponentFactory createCustomComponent updateCustomComponent resolveChangeReason 快照对比"
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomComponent CreateCustomComponent UpdateCustomComponent CreateAttributeValue NAPI 回调"
```

**关键文档：** `genui/src/main/ets/interface/CatalogItem.ets`、`genui/src/main/ets/core/base/CatalogImpl.ets`、`genui/src/main/ets/core/components/A2UI/CustomComponentFactory.ets`、`genui/src/main/cpp/components/custom/CustomComponent.cpp`、`genui/src/main/cpp/components/custom/CustomComponentAttributeValue.cpp`
