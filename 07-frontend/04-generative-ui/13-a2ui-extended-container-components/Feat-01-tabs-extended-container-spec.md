# 特性规格

> Func-07-04-13-Feat-01 Tabs 扩展页签容器：固化鸿蒙扩展协议 `component: "Tabs"` 的行为——Tabs 为 ArkTS 自定义组件（经 `getExtendedCustomDefinitions` 注册，`A2UIExtendedComponents.ets:174`），基于系统 `Tabs`/`TabContent`/`ContentSlot` 渲染；子项按「显式 `children` → 动态模板 → 命名槽位 `tab-*`」三来源解析；`tabIndex` 非负整数校验并裁剪到 `[0, len-1]`（越界派发去重告警）；`barPosition`/`vertical`/`scrollable` 动态解析；`onChange` 同时支持事件与函数调用派发。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Tabs 扩展页签容器 |
| 特性编号 | Func-07-04-13-Feat-01 |
| 优先级 | P0 |
| 目标版本 | API Version 20；鸿蒙扩展协议 1.0.0 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-13 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/13-a2ui-extended-container-components/design.md` | Baselined |
| Tabs 自定义组件（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedTabs.ets` | — |
| 扩展 Catalog 聚合（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 元数据注册表（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedTabsRegistry.ets` | — |
| 属性归一化（C++） | `genui/src/main/cpp/components/custom/CustomComponentTabsValidation.cpp` | — |
| 子项预构建（C++） | `genui/src/main/cpp/components/custom/ExtendedTabsPrebuildHelper.cpp` | — |
| Tabs 文档（Docs） | `reference/extended-components/tabs.md` | 理解辅助 |
| 组件 Schema | `genui/src/main/resources/rawfile/schema/Extended/components/ExtendedTabs.json` | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Tabs 组件注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别 `component: "Tabs"` 并注册为扩展 Catalog 自定义组件,
**以便** 通过扩展协议声明页签容器。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `createExtendedTabsDefinition()` 被调用 THEN 返回 `type === 'Tabs'`、`builder` 与 `schemaProvider` 三字段（`ExtendedTabs.ets:1013-1018`，`EXTENDED_TABS_TYPE` 于 `:42`） | 正常 |
| AC-1.2 | WHEN `schemaProvider` 被调用 THEN 经 `SchemaResourceLoader.loadSchema` 加载 `schema/Extended/components/ExtendedTabs.json`（`ExtendedTabs.ets:1009-1011`） | 正常 |
| AC-1.3 | WHEN 扩展 Catalog 聚合 THEN `getExtendedCustomDefinitions` 将 `createExtendedTabsDefinition()` 纳入返回数组（`A2UIExtendedComponents.ets:168-183`；`:174` 显式列出） | 正常 |
| AC-1.4 | WHEN `allA2UIExtendedComponents` 执行 THEN 对每个自定义定义 `CustomComponentFactory.registerCustomComponent` 并 `createCatalogItemFromDefinition`（`A2UIExtendedComponents.ets:200-203`） | 正常 |

### US-2: 页签子项三来源解析

**作为** 生成式 UI 宿主开发者,
**我想要** Tabs 从显式 children、动态模板或命名槽位解析子项,
**以便** 支持静态声明、数据驱动模板与运行时槽位注入。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `children` 为字符串 id 数组 THEN `resolveChildrenFromChildren` 按序生成 `childId` + `slotKey=tab-<i>`（`ExtendedTabs.ets:536-549`） | 正常 |
| AC-2.2 | WHEN `children` 为模板对象 `{componentId,path}` THEN 按 path 解析数据数组，childId 为 `<path><componentId>:<index>:<componentId>`（`ExtendedTabs.ets:551-575`，`buildExtendedTabsTemplateInstanceChildId` 于 `:123-129`） | 正常 |
| AC-2.3 | WHEN 无显式 `children` 且解析结果为空 THEN 回落 `resolveChildrenFromSlots` 取 `tab-*` 槽位键，按 `tab-<n>` 数值顺序排序（`ExtendedTabs.ets:508-510,578-623`） | 边界 |
| AC-2.4 | WHEN 无显式 `children` THEN `filterNonTabContentChildren` 仅保留「有元数据 / 有槽位 / 已识别 TabContent」的子项（`ExtendedTabs.ets:511-513,636-673`） | 边界 |
| AC-2.5 | WHEN `children` 为模板但 path 指向非数组或缺失 THEN `resolveArrayByPath` 返回空数组（`ExtendedTabs.ets:699-739`） | 异常 |

### US-3: tabIndex 动态解析与范围裁剪

**作为** 生成式 UI 宿主开发者,
**我想要** `tabIndex` 被校验并裁剪到有效范围,
**以便** 非法/越界索引不破坏渲染且可观测告警。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `tabIndex` 为非负整数字面量 THEN `normalizeExtendedTabsIndexValue` 原样返回（`ExtendedTabs.ets:112-117`） | 正常 |
| AC-3.2 | WHEN `tabIndex` 为 undefined/非有限/非整数/负数 THEN `normalizeExtendedTabsIndexValue` 返回 fallback（当前值）（`ExtendedTabs.ets:112-117`） | 边界 |
| AC-3.3 | WHEN `tabIndex >= 子项数` THEN `normalizeExtendedTabsIndexForItemCount` 裁剪到 `len-1` 且 `shouldReportWarning=true`（`ExtendedTabs.ets:131-150`） | 边界 |
| AC-3.4 | WHEN 子项数为 0 THEN `resolvedIndex` 回退 0 且 `shouldReportWarning=false`（`ExtendedTabs.ets:135-141`） | 边界 |
| AC-3.5 | WHEN 有显式 tabIndex 且越界 THEN `dispatchTabIndexRangeWarning` 按 `${value}:${count}` 签名去重，派发 `SchemaErrorCode.INVALID_VALUE` 告警（`ExtendedTabs.ets:484-488,786-793`，`dispatchExtendedTabsIndexRangeWarning` 于 `:152-174`） | 异常 |
| AC-3.6 | WHEN 相同越界签名重复出现 THEN `lastInvalidTabIndexSignature` 命中直接返回，不重复告警（`ExtendedTabs.ets:787-791`） | 边界 |

### US-4: Tabs 声明式渲染与外观

**作为** 生成式 UI 宿主开发者,
**我想要** Tabs 按 `vertical`/`barPosition`/`scrollable` 及深色模式渲染,
**以便** 页签栏方向、位置与主题与声明一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `tabItems.length > 0` THEN 声明系统 `Tabs` + `ForEach` 生成 `TabContent`/`ContentSlot`，`.tabBar(buildTabBar)`（`ExtendedTabs.ets:370-379`） | 正常 |
| AC-4.2 | WHEN `tabItems.length === 0` THEN 不渲染 Tabs 主体（无系统 Tabs 声明，`ExtendedTabs.ets:370` 分支不进入） | 边界 |
| AC-4.3 | WHEN `barPosition` 为 `end` THEN `resolveBarPosition` 返回 `BarPosition.End`；非 `end`/缺省返回 `BarPosition.Start`（`ExtendedTabs.ets:849-862`） | 正常 |
| AC-4.4 | WHEN `vertical`/`scrollable` 缺省 THEN `resolveVertical` 返回 false、`resolveScrollable` 返回 true（`ExtendedTabs.ets:795-811`） | 边界 |
| AC-4.5 | WHEN 深色模式 THEN 选中/未选中/页签栏背景使用深色默认值（`#F4F8FF`/`#DADDE2`/`#000000`），浅色用 `#1F64FF`/`#182431`/`#FFFFFF`（`ExtendedTabs.ets:43-48,449-464,813-815`） | 正常 |

### US-5: 页签栏项渲染（图标/标题/下划线/胶囊）

**作为** 生成式 UI 宿主开发者,
**我想要** 每个页签项按元数据渲染图标、标题与选中态视觉,
**以便** 页签栏呈现正确的选中/未选中区分。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 选中态且 `selectedSrc` 非空 THEN `resolveIconSource` 返回 `selectedSrc`，否则返回 `icon`（`ExtendedTabs.ets:240-245`） | 正常 |
| AC-5.2 | WHEN `tabType === 'capsule'` THEN `resolveExtendedTabsBorderRadius` 返回 18，否则返回 0（`ExtendedTabs.ets:119-121`） | 边界 |
| AC-5.3 | WHEN `tabType === 'underline'` THEN 渲染下划线，宽度经 `resolveUnderlineWidth` 估算（下限 20vp 上限 240vp）（`ExtendedTabs.ets:254-257,285-313`） | 正常 |
| AC-5.4 | WHEN 深色模式且 underline 类型 THEN 标题色强制 `#FFFFFF`（`ExtendedTabs.ets:247-251`） | 边界 |
| AC-5.5 | WHEN 点击页签且 `currentIndex !== index` THEN 更新 `currentIndex` 并 `dispatchComponentEvent('onClick')`（`ExtendedTabs.ets:228-233`） | 正常 |

### US-6: onChange 事件与函数调用派发

**作为** 生成式 UI 宿主开发者,
**我想要** 页签切换触发 onChange 事件或绑定的函数调用,
**以便** 宿主或数据模型感知当前页变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 用户切换页签 THEN `onChange` 更新 `currentIndex` 并强制 `tabItems.slice()` 重建（`ExtendedTabs.ets:387-391`） | 正常 |
| AC-6.2 | WHEN `currentIndex` 变化且 `enableOnChangeDispatch` 且与 `lastDispatchedIndex` 不同 THEN `dispatchOnChange` 派发 `onChange` 事件 payload `{ index }`（`ExtendedTabs.ets:358-367,908-912`） | 正常 |
| AC-6.3 | WHEN `onChange` 同时为函数调用对象（含 `call` 或 `functionCall.call`） THEN `dispatchOnChangeFunctionCall` 经 `DynamicValueResolver.resolveValue` 执行（`ExtendedTabs.ets:914-950`） | 正常 |
| AC-6.4 | WHEN 函数调用 args 缺省 THEN `mergeOnChangeFunctionArgs` 注入 `index` 与 `value` 两个参数（`ExtendedTabs.ets:984-996`） | 边界 |
| AC-6.5 | WHEN 首次渲染时 `lastDispatchedIndex` 已初始化为 `currentIndex` 且 `enableOnChangeDispatch` 置 true 于 `aboutToAppear` THEN 初始化不误派发 onChange（`ExtendedTabs.ets:331-340`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-1 | ArkTS 静态比对：定义 + Catalog 聚合 | `ExtendedTabs.ets:1009-1018`、`A2UIExtendedComponents.ets:168-204` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-1 | ArkTS 单测：子项三来源解析 | `ExtendedTabs.ets:504-739` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 | R-3 | T-1 | ArkTS 单测 + C++ 归一化 | `ExtendedTabs.ets:112-174,466-502`、`CustomComponentTabsValidation.cpp:58-73` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-4 | T-1 | ArkTS 单测：渲染与主题 | `ExtendedTabs.ets:369-407,449-464,813-862` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-5 | T-1 | ArkTS 单测：页签栏项渲染 | `ExtendedTabs.ets:176-314` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 | R-6 | T-1 | ArkTS 单测：onChange 派发 | `ExtendedTabs.ets:331-367,908-996` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | descriptor `component=="Tabs"` | 注册为 ArkTS 扩展自定义组件渲染 | 经 `getExtendedCustomDefinitions` 聚合 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 边界 | 子项解析 | 显式 children → 模板 → 槽位三来源，无 children 过滤非 TabContent | 空/非数组返回空列表 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 边界 | tabIndex 非负整数校验 + 裁剪 | 非法回退当前值；越界裁剪到 `len-1` 并告警去重 | 告警签名 `${value}:${count}` | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| R-4 | 行为 | 声明式渲染 + 主题 | vertical/scrollable/barPosition 动态解析；深浅色默认值分支 | 无子项不渲染 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| R-5 | 行为 | 页签栏项渲染 | 图标选中态回退、capsule 圆角 18、underline 宽度估算 | 下划线宽 20~240vp | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |
| R-6 | 行为 | onChange 派发 | 事件 payload `{index}` + 可选函数调用 | 初始化不误派发；重复索引不派发 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 注册/识别 | 静态比对 | type='Tabs'、schemaProvider、Catalog 聚合 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 子项三来源 | ArkTS 单测 | 数组/模板/槽位、过滤逻辑 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 tabIndex 裁剪 | ArkTS 单测 + C++ UT | 非法回退、越界裁剪、告警去重 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 声明式渲染 | ArkTS 单测 | vertical/barPosition/scrollable/深色默认值 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 页签栏项 | ArkTS 单测 | 图标/胶囊/下划线/选中态 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 onChange | ArkTS 单测 | 事件 + 函数调用、初始化不误派发 |

## API 变更分析

> 存量补录，无新增/变更公开 ArkTS/C-API。本节列出受影响组件协议。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Tabs` 扩展组件协议（`barPosition`/`children`/`vertical`/`scrollable`/`tabIndex`，事件 `onChange`） | 既有 | 扩展页签容器声明 | 与标准协议 Tabs 区分（catalogId 判别） | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |
| `ExtendedTabs`（内部 ArkTS 组件） | 既有 | 页签栏渲染 | 不直接暴露给宿主 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

> Schema 位置：`genui/src/main/resources/rawfile/schema/Extended/components/ExtendedTabs.json`（required `["component"]`，properties 含 `barPosition`/`children`/`vertical`/`scrollable`/`tabIndex`/`onChange`）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`createExtendedTabsDefinition()`（`ExtendedTabs.ets:1013`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `createExtendedTabsDefinition(): CustomComponentDefinition` |
| 返回值 | `CustomComponentDefinition` — 含 `type/builder/schemaProvider` |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**`normalizeExtendedTabsIndexForItemCount(value, itemCount)`（`ExtendedTabs.ets:131`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `normalizeExtendedTabsIndexForItemCount(value: number, itemCount: number): ExtendedTabsIndexRangeResult` |
| 返回值 | `ExtendedTabsIndexRangeResult` — `resolvedIndex` + `shouldReportWarning` + `warningMessage` |
| 开放范围 | 内部 |
| 错误码 | N/A（经 schema warning 提示） |
| 关联 AC | AC-3.3,AC-3.4,AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| tabIndex | number/dynamic | 否 | 当前值（`currentIndex`） | 非负整数；越界裁剪到 `[0, len-1]` |
| barPosition | string/dynamic | 否 | `start` | 取值 `start`/`end` |
| vertical | dynamic boolean | 否 | `false` | 解析结果须 boolean |
| scrollable | dynamic boolean | 否 | `true` | 解析结果须 boolean |
| children | array/template | 否 | `[]` | 数组 id 或 `{componentId,path}` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | children 为 id 数组 | 按序生成页签项 | AC-2.1 |
| 2 | children 为模板对象 | 按数据数组展开模板子项 | AC-2.2 |
| 3 | 无显式 children | 回落槽位并过滤非 TabContent | AC-2.3,AC-2.4 |
| 4 | tabIndex 越界 | 裁剪 + 去重告警 | AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| 5 | 深色模式 | 深色默认颜色 | AC-4.5 |
| 6 | 用户切换页签 | onChange 事件/函数调用 | AC-6.1,AC-6.2,AC-6.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API Version 20；鸿蒙扩展协议 1.0.0。
- **API 版本号策略:** 组件协议经 JSON Schema 约束；无 `@since` 标注差异。与标准协议 Tabs（07-04-05）按 `catalogId` 区分。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| ArkTS 自定义组件 | Tabs 走 ArkTS 而非 native（`getExtendedCustomDefinitions` 注册） | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| 子项三来源 | 显式 children 优先于槽位，无显式时过滤 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| 索引裁剪 | 非负整数 + 裁剪到 `[0, len-1]`，告警去重 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 tabIndex/barPosition 不崩溃，回退默认并告警 | ArkTS 单测 | `ExtendedTabs.ets:112-174,849-862` |
| 性能 | tabIndex 越界告警经签名去重避免重复计算 | ArkTS 单测 | `ExtendedTabs.ets:786-793` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 系统 Tabs 通用能力 | ohosTest | `ExtendedTabs.ets:369-407` |
| 平板 | 无差异 | 同上 | ohosTest | 同上 |
| 折叠屏 | 无差异 | 同上 | ohosTest | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityText`/`accessibilityDescription` 下发 | `ExtendedTabs.ets:395-396` |
| 大字体 | 否 | 标题字号可经 styles 控制，无内置大字体分支 | — |
| 深色模式 | 是 | 深浅色默认值分支（选中/未选中/页签栏背景） | AC-4.5 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API Version 20；扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | 鸿蒙扩展协议组件 | 概述 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Tabs 扩展页签容器
  作为 生成式 UI 宿主开发者
  我想要 通过 Tabs 声明页签容器并切换页签
  以便 在不同内容视图间切换

  Scenario: 静态 children 渲染页签
    Given DSL 含 {"component":"Tabs","id":"t1","children":["c1","c2"]} 且 c1/c2 为 TabContent
    When 引擎渲染 Tabs
    Then 渲染 2 个页签且默认激活第 0 个

  Scenario: tabIndex 越界裁剪
    Given Tabs 含 3 个 TabContent 且 tabIndex=5
    When syncTabsState 解析 tabIndex
    Then 激活第 2 个页签并派发 INVALID_VALUE 告警

  Scenario Outline: 子项来源
    Given Tabs 描述符 <what>
    When 解析子项
    Then <expected>

    Examples:
      | what | expected |
      | children 为 id 数组 | 生成对应页签 |
      | children 为模板对象 | 按数据数组展开 |
      | 无 children 仅有 tab-0/tab-1 槽位 | 按槽位生成页签 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（扩展 Tabs 容器语义；动态值底层解析归数据/表达式域）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTabs syncTabsState resolveChildrenFromChildren resolveChildrenFromSlots normalizeExtendedTabsIndexForItemCount"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTabs build Tabs TabContent ContentSlot barPosition vertical scrollable 深色默认值"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTabs onChange dispatchOnChange resolveOnChangeFunctionCall functionCall index value"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTabsPrebuildHelper PrebuildExtendedTabsChildren 静态/模板子项预构建 递归防护"
```

**关键文档：** `genui/src/main/ets/core/components/extended/ExtendedTabs.ets`、`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`、`genui/src/main/cpp/components/custom/ExtendedTabsPrebuildHelper.cpp`