# 特性规格

> Func-05-09-03-Feat-01 组件构建与搜索按钮：覆盖 Search 组件构造、SearchOptions 初始化、searchButton 属性与 SearchButtonOptions、SearchNode 六槽位组合结构、分割线可见性联动与 SearchController 绑定路径。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组件构建与搜索按钮（Search Construction & Search Button） |
| 特性编号 | Func-05-09-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 8 起支持，API 10/12/18/20/23/26 有 API 新增或行为差异 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Search 构造与 SearchOptions 规格 | 补录已有实现：Search(options)/SearchOptions(value/placeholder/icon/controller) @since 8 |
| ADDED | searchButton 属性与 SearchButtonOptions 规格 | 补录已有实现：searchButton(value,option?) @since 8，SearchButtonOptions(fontSize/fontColor @since 10, autoDisable @since 18) |
| ADDED | SearchNode 六槽位组合结构规格 | 补录已有实现：TextField(0)/SearchImage(1)/CancelImage(2)/CancelButton(3)/Button(4)/Divider(5) |
| ADDED | SearchController 绑定路径规格 | 补录已有实现：Controller 从子节点 TextField 取出后回传 |

## 输入文档

- 需求基线：已有能力补录（无独立 requirement.md）
- 设计文档：`05-ui-components/09-text-components/03-search/design.md`（DESIGN-Func-05-09-03）
- 源码定位：
  - 构造：`frameworks/core/components_ng/pattern/search/search_model_ng.cpp:97`(Create) `:148`(CreateSearchNode)
  - 按钮属性：`frameworks/core/components_ng/pattern/search/search_model_ng.cpp:247`(SetSearchButton) `:397`(SetSearchButtonFontSize) `:415`(SetSearchButtonFontColor) `:422`(SetSearchButtonAutoDisable)
  - 可见性联动：`frameworks/core/components_ng/pattern/search/search_pattern.cpp:308`(OnModifyDone) `:379`(UpdateDivider)
  - 子节点结构：`frameworks/core/components_ng/pattern/search/search_node.h:135`(SearchNode) `:314-317`(槽位 id)
  - C-API：`frameworks/core/components_ng/pattern/search/bridge/search_dynamic_modifier.cpp:587`(SetSearchSearchButton)
  - SDK：`interface/sdk-js/api/@internal/component/ets/search.d.ts`

## 用户故事

### US-1: 创建 Search 组件

**作为** 应用开发者,
**我想要** 通过 `Search(options)` 创建搜索框并初始化 value/placeholder/icon/controller,
**以便** 快速构建搜索交互入口。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 开发者调用 `Search({ value: "abc" })` THEN 创建 SearchNode 组合节点，子文本框（slot 0）内容初始化为 "abc" | 正常 |
| AC-1.2 | WHEN 开发者调用 `Search({ placeholder: "请输入" })` THEN 子文本框占位符显示 "请输入" | 正常 |
| AC-1.3 | WHEN 开发者调用 `Search({ icon: "/path/icon.png" })` THEN 左侧搜索图标（slot 1）使用指定图片资源路径 | 正常 |
| AC-1.4 | WHEN 开发者调用 `Search()` 无参数 THEN 使用默认值创建：value 为空、placeholder 为空、icon 为主题默认图标 | 正常 |
| AC-1.5 | WHEN value 使用 `$$` 双向绑定（@since 10）或 `!!` 双向绑定（@since 18）THEN 文本框值与状态变量双向同步 | 边界 |
| AC-1.6 | WHEN value 传入非 string/Resource 的非法类型 THEN 忽略非法值，文本框内容保持空，不抛异常 | 异常 |

### US-2: 设置搜索按钮文本与可见性

**作为** 应用开发者,
**我想要** 通过 `searchButton(value)` 设置搜索按钮文本，并控制按钮与分割线的可见性,
**以便** 在搜索场景下提供明确的提交入口与视觉分割。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `.searchButton("搜索")` 非空文本 THEN 右侧搜索按钮（slot 4）显示文本 "搜索"，按钮与分割线（slot 5）均 VISIBLE，按钮 enabled | 正常 |
| AC-2.2 | WHEN 未调用 `.searchButton()` THEN 搜索按钮与分割线均 GONE（不可见，不占位） | 正常 |
| AC-2.3 | WHEN 调用 `.searchButton("")` 空字符串且 API ≥ 18 THEN SearchButton 布局属性被 RESET，按钮 GONE、disabled、opacity=0.0 | 边界 |
| AC-2.4 | WHEN 调用 `.searchButton("")` 空字符串且 API < 18 THEN SearchButton 布局属性不被 RESET（保留 disabled 状态），行为与 API ≥ 18 存在差异 | 边界 |
| AC-2.5 | WHEN 点击可见的搜索按钮 THEN 触发 `onSubmit` 回调，附带当前文本框内容，并执行 `TextOverflow::ELLIPSIS` 溢出策略 | 正常 |

### US-3: 配置搜索按钮样式

**作为** 应用开发者,
**我想要** 通过 `SearchButtonOptions` 配置搜索按钮的字号与颜色,
**以便** 自定义搜索按钮的视觉样式。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `SearchButtonOptions.fontSize = 18` THEN 按钮文字字号设为 18，触发 PROPERTY_UPDATE_MEASURE 重布局 | 正常 |
| AC-3.2 | WHEN `SearchButtonOptions.fontColor = Color.Red` THEN 按钮文字颜色设为红色，标记 fontColorSetByUser=true | 正常 |
| AC-3.3 | WHEN 未设置 fontSize/fontColor THEN 使用主题默认值：fontSize=16fp（穿戴 18fp）、fontColor=#ff3f97e9，isTheme=true | 正常 |
| AC-3.4 | WHEN fontSize 为百分比类型 THEN 忽略百分比设置（不支持百分比），使用默认值 | 边界 |

### US-4: 配置搜索按钮自动禁用

**作为** 应用开发者,
**我想要** 通过 `autoDisable` 控制文本框为空时是否自动禁用搜索按钮,
**以便** 防止用户在无搜索内容时误触发空搜索。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN `autoDisable=true`（@since 18）且文本框内容为空 THEN 搜索按钮禁用（disabled） | 正常 |
| AC-4.2 | WHEN `autoDisable=true` 且文本框有内容 THEN 搜索按钮启用 | 正常 |
| AC-4.3 | WHEN `autoDisable=false`（默认）THEN 搜索按钮启用状态仅由 searchButton 文本是否非空控制，不因文本框内容变化而禁用 | 正常 |
| AC-4.4 | WHEN 未设置 autoDisable THEN 默认 false，且 autoDisable 参与文本框宽度计算（仅在 enabled \|\| autoDisable 时扣减按钮宽度） | 边界 |

### US-5: 组件组合结构与分割线联动

**作为** 平台维护者,
**我想要** 规格文档化 SearchNode 的六槽位组合结构及分割线与搜索按钮的可见性耦合关系,
**以便** 理解组件内部组合架构与可见性耦合关系。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN Search 创建完成 THEN SearchNode(GroupNode) 包含 6 个固定槽位子节点：TextField(0)/SearchImage(1)/CancelImage(2)/CancelButton(3)/Button(4)/Divider(5) | 正常 |
| AC-5.2 | WHEN searchButton 属性有值 THEN Divider(slot 5) 可见性为 VISIBLE（与 Button 共用同一谓词） | 正常 |
| AC-5.3 | WHEN searchButton 属性无值 THEN Divider(slot 5) 可见性为 GONE，不独立显示分割线 | 正常 |
| AC-5.4 | WHEN 搜索按钮可见（enabled 或 autoDisable）THEN 文本框宽度扣减 `buttonWidth + dividerWidth + 2*dividerSideSpace` | 正常 |

### US-6: 绑定 SearchController

**作为** 应用开发者,
**我想要** 通过 `SearchOptions.controller` 绑定控制器，以编程方式控制光标与选区,
**以便** 编程式控制光标与选区。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN 传入 controller 参数 THEN JS 侧 SearchController（JSTextEditableController）与从子节点 TextField 取出的内部 TextFieldController 绑定 | 正常 |
| AC-6.2 | WHEN 未传入 controller THEN 内部 Controller 仍从子节点 TextFieldPattern 取出并由 SearchPattern 持有，但不暴露给 JS | 正常 |
| AC-6.3 | WHEN 调用 `controller.caretPosition(5)` THEN 委托至 SearchPattern::HandleCaretPosition，转发至子 TextFieldPattern 定位光标至 5 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-2 | TASK-01 | 单测/UITest | search_model_ng.cpp:1091 InitValueText |
| AC-1.2 | R-3 | TASK-01 | 单测/UITest | search_model_ng.cpp:1095 UpdatePlaceholder |
| AC-1.3 | R-4 | TASK-01 | UITest | search_pattern.cpp:2511 CreateSearchIcon |
| AC-1.4 | R-5 | TASK-01 | UITest | search_model_ng.cpp:148 CreateSearchNode |
| AC-1.5 | R-6 | TASK-01 | UITest | search.d.ts:271 value $$ since 10 |
| AC-1.6 | R-7 | TASK-01 | 单测 | arkts_native_search_bridge.cpp:470 ParseJsString 守卫 |
| AC-2.1 | R-8 | TASK-01 | UITest | search_pattern.cpp:330 VISIBLE |
| AC-2.2 | R-9 | TASK-01 | UITest | search_pattern.cpp:330 GONE |
| AC-2.3 | R-10 | TASK-01 | UITest | search_model_ng.cpp:268 ACE_RESET |
| AC-2.4 | R-11 | TASK-01 | UITest | search_model_ng.cpp:267 版本守卫 |
| AC-2.5 | R-12 | TASK-01 | UITest | search_pattern.cpp:845 FireOnSubmit |
| AC-3.1 | R-13 | TASK-01 | UITest | search_model_ng.cpp:411 SearchButtonFontSize |
| AC-3.2 | R-14 | TASK-01 | UITest | search_model_ng.cpp:1614 updateFontColorToLayoutProp |
| AC-3.3 | R-15 | TASK-01 | UITest | search.d.ts:551 默认值 |
| AC-3.4 | R-16 | TASK-01 | 单测 | search.d.ts:413 不支持百分比 |
| AC-4.1 | R-17 | TASK-01 | UITest | search_model_ng.cpp:431 updateAutoDisableToLayoutProp |
| AC-4.2 | R-18 | TASK-01 | UITest | 同上 |
| AC-4.3 | R-19 | TASK-01 | UITest | search.d.ts:441 default false |
| AC-4.4 | R-19 | TASK-01 | UITest | search_layout_algorithm.cpp:224 |
| AC-5.1 | R-1 | TASK-01 | 源码检查 | search_model_ng.cpp:47-52 槽位常量 |
| AC-5.2 | R-20 | TASK-01 | UITest | search_pattern.cpp:390 Divider VISIBLE |
| AC-5.3 | R-20 | TASK-01 | UITest | search_pattern.cpp:390 Divider GONE |
| AC-5.4 | R-21 | TASK-01 | UITest | search_layout_algorithm.cpp:224-227 |
| AC-6.1 | R-22 | TASK-01 | UITest | arkts_native_search_bridge.cpp:517 SetController |
| AC-6.2 | R-22 | TASK-01 | 源码检查 | search_model_ng.cpp:195 SetSearchController |
| AC-6.3 | R-23 | TASK-01 | UITest | search_pattern.cpp:715-718 HandleCaretPosition |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|----------|----------|-----------|---------|
| R-1 | 行为 | 调用 `SearchModelNG::Create`/`CreateSearchNode` | 创建 SearchNode(GroupNode) 含 6 固定槽位子节点 | 槽位索引 0-5 固定；子节点 lazy 创建但全部在 CreateSearchNode 时构建 | AC-5.1 |
| R-2 | 行为 | `Search({ value: "x" })` 传入非空 value | `pattern->InitValueText(value)` 将 value 写入子 TextField(slot 0) 内容 | value 类型为 string(@since 8-19) 或 ResourceStr(@since 20) | AC-1.1 |
| R-3 | 行为 | `Search({ placeholder: "p" })` 传入 placeholder | `textFieldLayoutProperty->UpdatePlaceholder(placeholder)` 写入子文本框占位符 | placeholder 类型 string(@since 8-9) 或 ResourceStr(@since 10) | AC-1.2 |
| R-4 | 行为 | `Search({ icon: "/p" })` 传入 icon 路径 | `pattern->CreateSearchIcon(src)` 使用指定路径创建搜索图标(slot 1) | icon 类型为 string；空/undefined 使用主题默认图标 | AC-1.3 |
| R-5 | 行为 | `Search()` 无参数构造 | value/placeholder 为空，icon 为主题默认，controller 从子节点取出但不绑定 JS | — | AC-1.4 |
| R-6 | 边界 | value 使用 `$$`(@since 10) 或 `!!`(@since 18) 双向绑定 | 文本框值与状态变量双向同步 | 仅动态 API 支持；静态 API 使用 Bindable<string> | AC-1.5 |
| R-7 | 异常 | value 传入非 string/Resource 非法类型 | `ParseJsString` 守卫失败，忽略非法值，value 保持空，不抛异常 | — | AC-1.6 |
| R-8 | 行为 | `.searchButton("非空")` 设置非空按钮文本 | Button(slot 4) visibility=VISIBLE、enabled=true、opacity=1.0；Divider(slot 5) visibility=VISIBLE | SearchButton 属性写入触发 PROPERTY_UPDATE_MEASURE | AC-2.1 |
| R-9 | 行为 | 未调用 `.searchButton()` | Button(slot 4) visibility=GONE；Divider(slot 5) visibility=GONE | 谓词为 `searchButton.has_value()` | AC-2.2 |
| R-10 | 边界 | `.searchButton("")` 空字符串且 API ≥ 18 | `ACE_RESET_LAYOUT_PROPERTY(SearchButton)` 重置属性，Button GONE、disabled、opacity=0.0 | 版本守卫 `GreatOrEqualAPITargetVersion(VERSION_EIGHTEEN)` | AC-2.3 |
| R-11 | 边界 | `.searchButton("")` 空字符串且 API < 18 | SearchButton 属性不被 RESET，Button disabled 但属性保留 | 与 R-10 构成版本差异，属兼容性风险 | AC-2.4 |
| R-12 | 行为 | 点击可见搜索按钮 | `OnClickButtonAndImage` → `SearchEventHub::FireOnSubmit(text, event)` 触发 onSubmit；TextOverflow::ELLIPSIS | 按钮文本溢出时省略 | AC-2.5 |
| R-13 | 行为 | `SearchButtonOptions.fontSize = N` | 写入 `SearchLayoutProperty.SearchButtonFontSize`(MEASURE) + button modifier `updateFontSizeToLayoutProp` | 不支持百分比；触发重布局 | AC-3.1 |
| R-14 | 行为 | `SearchButtonOptions.fontColor = C` | button modifier `updateFontColorToLayoutProp(C)` + `updateFontColorFlagByUserToLayoutProp(true)` + `SetIsSearchButtonUsingThemeColor(isTheme)` | isTheme=true 时后续主题更新可覆盖 | AC-3.2 |
| R-15 | 行为 | 未设置 fontSize/fontColor | fontSize 默认 16fp（穿戴 18fp），fontColor 默认 #ff3f97e9，isTheme=true | 默认值来自 SearchTheme | AC-3.3 |
| R-16 | 边界 | fontSize 为百分比类型 | 忽略百分比设置，使用默认值 | SDK 注明 "cannot be set in percentage" | AC-3.4 |
| R-17 | 行为 | `autoDisable=true`（@since 18）且文本框为空 | 搜索按钮 disabled | autoDisable 经 `updateAutoDisableToLayoutProp` 写入 Button 子节点 | AC-4.1 |
| R-18 | 行为 | `autoDisable=true` 且文本框有内容 | 搜索按钮 enabled | — | AC-4.2 |
| R-19 | 行为 | `autoDisable=false`（默认）或未设置 | 按钮启用状态仅由 searchButton 文本控制；autoDisable=false 时不因文本框空而禁用 | autoDisable 参与 CalculateTextFieldWidth 宽度扣减判断 | AC-4.3, AC-4.4 |
| R-20 | 行为 | UpdateDivider 执行 | Divider(slot 5) visibility = `searchButton.has_value() ? VISIBLE : GONE`，与 Button 共用同一谓词 | 分割线不独立于按钮显示 | AC-5.2, AC-5.3 |
| R-21 | 行为 | 按钮可见（enabled 或 autoDisable）时 CalculateTextFieldWidth | 文本框宽度扣减 `buttonWidth + dividerWidth + 2*dividerSideSpace` | 仅当 `searchButtonEvent->IsEnabled() \|\| needToDisable` 时扣减 | AC-5.4 |
| R-22 | 行为 | 传入 controller 或未传入 | Controller 从子节点 TextFieldPattern 的 TextFieldController 取出（`search_model_ng.cpp:195`），JS 侧 JSTextEditableController 在 JsCreate(:517)/SetSearchInitialize(:437) 后绑定 | Controller 不作为 Create 参数，而是从子节点回传 | AC-6.1, AC-6.2 |
| R-23 | 行为 | 调用 `controller.caretPosition(n)` | `InitSearchController` 委托 `searchController_->SetCaretPosition` → `HandleCaretPosition(n)` → 子 TextFieldPattern 定位光标 | n 为整数 | AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | US-1 构造与 SearchOptions | UITest | 验证 value/placeholder/icon 正确流入子节点；空参默认值 |
| VM-2 | US-2 searchButton 可见性 | UITest | 验证 Button+Divider VISIBLE/GONE 联动；空文本版本差异 |
| VM-3 | US-2 按钮点击 onSubmit | UITest | 验证点击触发 FireOnSubmit 并附带文本内容 |
| VM-4 | US-3 SearchButtonOptions 样式 | UITest | 验证 fontSize/fontColor 写入与默认值；百分比忽略 |
| VM-5 | US-4 autoDisable 语义 | UITest | 验证 autoDisable=true/false 对 enabled 状态与宽度扣减的影响 |
| VM-6 | US-5 六槽位结构与分割线耦合 | 源码检查+UITest | 验证 6 子节点槽位；Divider 与 Button 谓词一致 |
| VM-7 | US-6 Controller 绑定与委托 | UITest | 验证 Controller 从子节点取出；caretPosition 委托至子 TextField |

## API 变更分析

### 新增 API

> 补录已有 Public API，非实际新增。开放范围均为 Public。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `Search(options?: SearchOptions): SearchAttribute` | Public | options.value?: ResourceStr(@since 8/20)、options.placeholder?: ResourceStr(@since 8/10)、options.icon?: string(@since 8)、options.controller?: SearchController(@since 8) | SearchAttribute | 无 | 创建搜索框组件 | AC-1.1..AC-1.6 |
| `searchButton(value: ResourceStr, option?: SearchButtonOptions): SearchAttribute` | Public | value: ResourceStr(@since 8, string→ResourceStr @since 20)、option.fontSize?: Length(@since 10)、option.fontColor?: ResourceColor(@since 10)、option.autoDisable?: Boolean(@since 18, default false) | SearchAttribute | 无 | 设置搜索按钮文本与样式 | AC-2.1..AC-4.4 |
| `SearchController`（extends TextContentControllerBase） | Public | constructor(): SearchController(@since 8) | — | 无 | 搜索框控制器 | AC-6.1..AC-6.3 |
| `SearchModifier extends SearchAttribute implements AttributeModifier<SearchAttribute>` | Public | applyNormalAttribute?(instance: SearchAttribute): void(@since 12) | — | 无 | 动态属性修饰符 | AC-3.1..AC-4.4 |
| 静态 `Search(options?: SearchOptions): SearchAttribute`（@since 23） | Public | 同动态签名（value: string\|Bindable<string>） | SearchAttribute | 无 | 静态 API 等价构造 | AC-1.1..AC-1.4 |
| 静态 `searchButton(value: string\|undefined, option?: SearchButtonOptions\|undefined)`（@since 23） | Public | 同动态 | SearchAttribute | 无 | 静态 API 等价设置 | AC-2.1..AC-4.4 |
| C-API `setSearchSearchButton(node, value, fontColor, imageIconRes, isThemeColor, isJsView)` | InnerApi | ArkUISearchButtonOptionsStruct 打包 value/sizeValue/sizeUnit/autoDisable + Color + bool | void | 无 | C-ABI 捆绑式按钮属性写入 | AC-2.1..AC-4.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `searchButton` value 参数类型 | 变更 | API 8-19 为 string，API 20 起为 ResourceStr | string 仍兼容；Resource 类型需 API ≥ 20 | AC-2.1 |
| `SearchOptions.value` 类型 | 变更 | API 8-19 为 ?string，API 20 起为 ?ResourceStr | string 仍兼容 | AC-1.1 |
| `SearchOptions.placeholder` 类型 | 变更 | API 8-9 为 string，API 10 起为 ?ResourceStr | string 仍兼容 | AC-1.2 |
| `searchButton("")` 空文本行为 | 变更 | API ≥ 18 RESET 属性致 GONE；API < 18 不 RESET | 应用应在 API ≥ 18 上验证空文本按钮消失行为 | AC-2.3, AC-2.4 |
| `SearchButtonOptions.autoDisable` | 新增 | @since 18 引入，API < 18 无此属性 | API < 18 忽略 autoDisable 设置 | AC-4.1..AC-4.4 |

## 接口规格

### 接口定义

**Search(options?: SearchOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Search(options?: SearchOptions): SearchAttribute` |
| 返回值 | `SearchAttribute` — 组件属性链 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1..AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options.value | ResourceStr | 否 | 空 | string(@since 8-19)/ResourceStr(@since 20)；支持 $$(since 10)/!!(since 18) |
| options.placeholder | ResourceStr | 否 | 空 | string(@since 8-9)/?ResourceStr(@since 10) |
| options.icon | string | 否 | 主题默认图标 | 图片资源路径；非法路径使用默认 |
| options.controller | SearchController | 否 | 内部自动创建 | 从子节点 TextField 取出；传入则绑定 JS 侧 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入非空 value | 子 TextField 内容初始化为 value | AC-1.1 |
| 2 | 传入 placeholder | 子 TextField 占位符为 placeholder | AC-1.2 |
| 3 | 传入 icon 路径 | 搜索图标使用指定路径 | AC-1.3 |
| 4 | 无参数 | 全部默认值 | AC-1.4 |
| 5 | value 为 $$ 双向绑定 | 双向同步 | AC-1.5 |
| 6 | value 为非法类型 | 忽略，保持空 | AC-1.6 |

---

**searchButton(value: ResourceStr, option?: SearchButtonOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `searchButton(value: ResourceStr, option?: SearchButtonOptions): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1..AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceStr | 是 | — | string(@since 8-19)/ResourceStr(@since 20)；空字符串有版本差异行为 |
| option.fontSize | Length | 否 | 16fp(穿戴 18fp) | 不支持百分比 |
| option.fontColor | ResourceColor | 否 | #ff3f97e9 | — |
| option.autoDisable | Boolean | 否 | false | @since 18；API < 18 忽略 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 非空 | Button+Divider VISIBLE、enabled | AC-2.1 |
| 2 | 未调用 | Button+Divider GONE | AC-2.2 |
| 3 | value="" API≥18 | RESET 属性，GONE | AC-2.3 |
| 4 | value="" API<18 | 不 RESET，disabled | AC-2.4 |
| 5 | 点击可见按钮 | FireOnSubmit | AC-2.5 |
| 6 | fontSize=百分比 | 忽略 | AC-3.4 |

---

**SearchController**

| 属性 | 值 |
|------|-----|
| 函数签名 | `class SearchController extends TextContentControllerBase` |
| 返回值 | — |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1..AC-6.3 |

**参数约束**

| 方法 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| caretPosition(value) | number | 是 | — | 整数；委托至子 TextField |
| stopEditing() | — | — | — | @since 10 |
| setTextSelection(start, end, options?) | number, number, SelectionOptions? | 是 | — | @since 12 |

## 兼容性声明

- **已有 API 行为变更:** 是。`searchButton("")` 空文本行为在 API 18 存在版本差异（API≥18 RESET 属性致 GONE，API<18 不 RESET）；`value`/`placeholder` 类型在 API 10/20 从 string 扩展为 ResourceStr（向后兼容）；`autoDisable` 为 API 18 新增属性。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** 动态 API @since 8 起，静态 API @since 23 起，SearchModifier @since 12。各属性按实际引入版本标注 @since。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 六槽位固定索引 | SearchNode 子节点索引 0-5 固定，不可重排；新增子节点类型需分配新索引 | AC-5.1 |
| 分割线与按钮可见性耦合 | Divider 可见性严格绑定 searchButton.has_value()，不可独立设置 | AC-5.2, AC-5.3 |
| Controller 从子节点回传 | Controller 非 Create 参数，必须从子 TextFieldPattern 取出；不可外部注入原生 Controller | AC-6.1, AC-6.2 |
| SearchButton 属性触发 MEASURE | SearchButton/SearchButtonFontSize 均标记 PROPERTY_UPDATE_MEASURE，变更触发重布局 | AC-2.1, AC-3.1 |
| C-API 捆绑式写入 | searchButton 四子属性经单一 setSearchSearchButton 打包传递，无独立 C-API 槽位 | AC-2.1..AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | searchButton 变更触发 PROPERTY_UPDATE_MEASURE，单次重布局应在 1 帧内完成 | UITest 帧率 | search_layout_algorithm.cpp Measure |
| 内存 | 6 子节点一次性创建，无动态增删（仅 visibility 切换），内存占用稳定 | 内存分析 | search_model_ng.cpp:148 CreateSearchNode |
| 可靠性 | 子节点 lazy id 分配保证幂等创建（Has*Node 守卫） | 单测 | search_node.h:160 HasDividerNode |
| 可测试性 | SearchButton 属性经 ToJsonValue 输出，支持 Inspector 检查 | Inspector dump | search_layout_property.h:69 PutExtAttr |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 搜索按钮默认字号 16fp | — | UITest | search.d.ts:551 |
| 平板 | 同手机 | 无差异 | UITest | — |
| 折叠屏 | 同手机 | 无差异 | UITest | — |
| 穿戴 | 搜索按钮默认字号 18fp | 默认值不同 | UITest | search.d.ts:544 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Search 提供 accessibility actions（SetAccessibilityAction），搜索按钮作为子节点继承无障碍语义 | 后续 Feat 可补充 |
| 大字体 | 是 | searchButtonFontSize 受 minFontScale/maxFontScale 约束（Feat-04）；按钮文字支持自适应 | AC-3.1 |
| 深色模式 | 是 | fontColor 未设时 isTheme=true，主题切换自动更新颜色；OnColorConfigurationUpdate 处理 | AC-3.2, AC-3.3 |
| 多窗口/分屏 | 否 | Search 无多窗口特殊行为 | — |
| 多用户 | 否 | 无多用户特殊行为 | — |
| 版本升级 | 是 | API 8→26 持续演进，空文本行为在 API 18 有差异，autoDisable 在 API 18 新增 | AC-2.3, AC-2.4, AC-4.1 |
| 生态兼容 | 是 | 动态 API(@since 8) 与静态 API(@since 23) 双范式；C-API 修饰符(@since 12) 与 Cangjie FFI | 全部 AC |

## 行为场景（Gherkin）

```gherkin
Feature: Search 组件构建与搜索按钮
  作为应用开发者
  我想要创建搜索框并配置搜索按钮
  以便提供搜索交互入口

  Scenario: 创建带初始值的搜索框
    Given 应用已启动
    When 调用 Search({ value: "abc", placeholder: "请输入" })
    Then SearchNode 创建完成，包含 6 个子节点槽位
    And 子文本框(slot 0)内容为 "abc"
    And 子文本框(slot 0)占位符为 "请输入"
    And 搜索按钮(slot 4)与分割线(slot 5)均为 GONE

  Scenario: 设置非空搜索按钮显示按钮与分割线
    Given Search 组件已创建
    When 调用 .searchButton("搜索")
    Then 搜索按钮(slot 4)可见性为 VISIBLE 且 enabled
    And 分割线(slot 5)可见性为 VISIBLE
    And 搜索按钮文本为 "搜索"

  Scenario: 空文本搜索按钮在 API 18+ 消失
    Given Search 组件已创建且 API 版本 >= 18
    When 调用 .searchButton("")
    Then SearchButton 布局属性被 RESET
    And 搜索按钮(slot 4)可见性为 GONE
    And 分割线(slot 5)可见性为 GONE

  Scenario: 空文本搜索按钮在 API 18 以下保留 disabled
    Given Search 组件已创建且 API 版本 < 18
    When 调用 .searchButton("")
    Then SearchButton 布局属性不被 RESET
    And 搜索按钮保持 disabled 状态

  Scenario Outline: autoDisable 控制按钮启用状态
    Given Search 组件已创建且 autoDisable = <autoDisable>
    When 文本框内容为 <content>
    Then 搜索按钮 enabled 状态为 <expected>
    And 文本框宽度扣减计算使用 <widthCalc>

    Examples:
      | autoDisable | content | expected | widthCalc |
      | true | "" | false | 扣减(autoDisable) |
      | true | "x" | true | 扣减(enabled) |
      | false | "" | true | 不扣减 |
      | false | "x" | true | 扣减(enabled) |

  Scenario: 点击搜索按钮触发 onSubmit
    Given Search 组件已创建且 .searchButton("搜索") 已设置
    When 用户点击搜索按钮
    Then onSubmit 回调被触发
    And 回调参数包含当前文本框内容

  Scenario: Controller 从子节点绑定
    Given Search 组件已创建且传入 controller 参数
    When JsCreate 执行完成
    Then 内部 TextFieldController 从子 TextFieldPattern(slot 0) 取出
    And JS 侧 JSTextEditableController 与该 Controller 绑定
    When 调用 controller.caretPosition(5)
    Then 光标定位委托至子 TextFieldPattern
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SearchModelNG::CreateSearchNode 如何创建 6 个子节点槽位，value/placeholder/icon 如何流入子节点"
  - repo: "openharmony/arkui_ace_engine"
    query: "SearchPattern::OnModifyDone 如何根据 searchButton 属性联动 Button 与 Divider 可见性"
  - repo: "openharmony/arkui_ace_engine"
    query: "searchButton 空文本在 API 18 前后的 ACE_RESET_LAYOUT_PROPERTY 版本守卫差异"
  - repo: "openharmony/arkui_ace_engine"
    query: "SearchController 如何从子节点 TextFieldPattern 取出并向上回传至 JS 侧 JSTextEditableController"
  - repo: "openharmony/interface_sdk-js"
    query: "search.d.ts 中 SearchOptions/SearchButtonOptions/SearchController 的 @since 版本与类型演变"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/search.d.ts`；`frameworks/core/components_ng/pattern/search/search_model_ng.cpp`；`frameworks/core/components_ng/pattern/search/search_pattern.cpp`；`design.md`(DESIGN-Func-05-09-03)
