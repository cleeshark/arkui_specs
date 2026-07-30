# 特性规格

> Func-05-09-03-Feat-02 搜索图标与取消按钮：覆盖 searchIcon(IconOptions/SymbolGlyphModifier)、cancelButton(CancelButtonOptions/CancelButtonSymbolOptions)、CancelButtonStyle 枚举语义、图标 Symbol/Image 分派、用户设色保护与深色模式更新、SVG 重染色限制、取消按钮点击清空+聚焦行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 搜索图标与取消按钮（Search Icon & Cancel Button） |
| 特性编号 | Func-05-09-03-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 10 起支持（searchIcon/cancelButton），API 12 新增 SymbolGlyphModifier，API 20 新增 crossplatform |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | searchIcon 属性规格 | 补录已有实现：searchIcon(IconOptions\|SymbolGlyphModifier) @since 10(Symbol @since 12) |
| ADDED | cancelButton 属性规格 | 补录已有实现：cancelButton(CancelButtonOptions\|CancelButtonSymbolOptions) @since 10(Symbol @since 12) |
| ADDED | CancelButtonStyle 枚举语义规格 | 补录已有实现：CONSTANT/INVISIBLE/INPUT @since 10 |
| ADDED | 图标 Symbol/Image 分派机制规格 | 补录已有实现：API≥12 + src空 + IsNeedSymbol → Symbol，否则 Image |
| ADDED | 用户设色保护与深色模式更新规格 | 补录已有实现：SearchIconColorSetByUser/CancelIconColorSetByUser/TextColorFlagByUser 门控 |

## 输入文档

- 需求基线：已有能力补录（无独立 requirement.md）
- 设计文档：`05-ui-components/09-text-components/03-search/design.md`（DESIGN-Func-05-09-03，Feat-02 增量合并）
- 源码定位：
  - 搜索图标：`frameworks/core/components_ng/pattern/search/search_pattern.cpp:2511`(CreateSearchIcon) `:2579`(CreateOrUpdateSymbol) `:2634`(CreateOrUpdateImage) `:2491`(InitSearchIconColorSize) `:2229`(OnIconColorConfigrationUpdate)
  - 搜索图标 Model：`search_model_ng.cpp:276`(SetSearchIconSize) `:285`(SetSearchIconColor) `:309`(SetSearchImageIcon) `:325`(SetSearchSymbolIcon) `:300`(SetSearchDefaultIcon)
  - 取消按钮创建：`search_model_ng.cpp:1265`(CreateCancelButton)
  - 取消图标：`search_pattern.cpp:2548`(CreateCancelIcon) `:2751`(SetCancelIconSize) `:2759`(SetCancelIconColor) `:2812`(SetCancelButtonStyle)
  - CancelButtonStyle 行为：`search_pattern.cpp:145`(UpdateCancelButtonStatus) `:225`(IsEventEnabled) `:116`(UpdateChangeEvent)
  - 取消按钮点击：`search_pattern.cpp:672`(InitCancelButtonClickEvent) `:857`(OnClickCancelButton)
  - 颜色模式更新：`search_pattern.cpp:2248`(OnSearchColorConfigrationUpdate) `:2285`(OnCancelColorConfigrationUpdate)
  - 布局：`search_layout_algorithm.cpp:299`(ImageMeasure) `:759`(LayoutSearchIcon) `:86`(CancelImageMeasure) `:120`(CancelButtonMeasure) `:873`(LayoutCancelButton) `:928`(LayoutCancelImage)
  - SDK：`interface/sdk-js/api/@internal/component/ets/search.d.ts`

## 用户故事

### US-1: 设置搜索图标样式（IconOptions）

**作为** 应用开发者,
**我想要** 通过 `searchIcon(IconOptions)` 配置搜索图标的尺寸、颜色与图片源,
**以便** 自定义搜索图标的视觉外观。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 调用 `.searchIcon({ size: 20 })` THEN 搜索图标（slot 1）尺寸设为 20，写入 SearchIconUDSize 触发 PROPERTY_UPDATE_MEASURE | 正常 |
| AC-1.2 | WHEN 调用 `.searchIcon({ color: Color.Red })` THEN 搜索图标颜色设为红色，标记 SearchIconColorSetByUser=true | 正常 |
| AC-1.3 | WHEN 调用 `.searchIcon({ src: "/path/icon.png" })` THEN 搜索图标使用指定图片路径（Image 路径，IMAGE_ETS_TAG） | 正常 |
| AC-1.4 | WHEN 调用 `.searchIcon({})` 空对象 THEN 使用主题默认值：size=16vp、color=浅色#99182431/深色#99ffffff、src 回退 SEARCH_SVG | 正常 |
| AC-1.5 | WHEN `size` 为百分比类型 THEN 忽略百分比设置（不支持百分比），使用默认值 | 边界 |
| AC-1.6 | WHEN `src` 为空或未设置 THEN 回退内置 SEARCH_SVG 资源（`search_pattern.cpp:2941-2947`） | 边界 |

### US-2: 设置搜索图标为 Symbol（SymbolGlyphModifier）

**作为** 应用开发者,
**我想要** 通过 `searchIcon(SymbolGlyphModifier)` 使用符号字体图标,
**以便** 使用符号字体替代位图图标。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `.searchIcon(SymbolGlyphModifier)` 且 API ≥ 12 且 `IsNeedSymbol()=true` 且无自定义 src THEN 创建 SYMBOL_ETS_TAG/TextPattern 节点，使用 `searchTheme->GetSearchSymbolId()` | 正常 |
| AC-2.2 | WHEN API < 12 或 `IsNeedSymbol()=false` 或有自定义 src THEN 回退 Image 路径（IMAGE_ETS_TAG/ImagePattern） | 边界 |
| AC-2.3 | WHEN SymbolGlyphModifier 传入 THEN 其 `symbolApply` 回调存储为 `searchIconSymbol_` lambda，在 symbol 节点创建后通过 `UpdateSymbolLayoutProperty` 应用 | 正常 |

### US-3: 设置取消按钮样式（CancelButtonOptions）

**作为** 应用开发者,
**我想要** 通过 `cancelButton(CancelButtonOptions)` 配置取消按钮的样式与图标,
**以便** 自定义取消按钮的样式与行为。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 `.cancelButton({ style: CancelButtonStyle.INPUT })` THEN 写入 CancelButtonStyle 属性（MEASURE），取消按钮按 INPUT 语义显示 | 正常 |
| AC-3.2 | WHEN 调用 `.cancelButton({ icon: { size: 16 } })` THEN 取消图标（slot 2）尺寸设为 16，写入 CancelButtonUDSize | 正常 |
| AC-3.3 | WHEN 调用 `.cancelButton({ icon: { color: Color.Red } })` THEN 取消图标颜色红色，标记 CancelIconColorSetByUser=true | 正常 |
| AC-3.4 | WHEN 调用 `.cancelButton({ icon: { src: "/path/cancel.png" } })` THEN 取消图标使用指定图片路径 | 正常 |

### US-4: 设置取消按钮为 Symbol（CancelButtonSymbolOptions）

**作为** 应用开发者,
**我想要** 通过 `cancelButton(CancelButtonSymbolOptions)` 使用符号字体作为取消图标,
**以便** 使用符号字体作为取消图标。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 调用 `.cancelButton({ icon: SymbolGlyphModifier })` 且 API ≥ 12 THEN 创建 SYMBOL_ETS_TAG 节点，使用 `searchTheme->GetCancelSymbolId()` | 正常 |
| AC-4.2 | WHEN 调用 `.cancelButton({ style: CancelButtonStyle.CONSTANT, icon: SymbolGlyphModifier })` THEN 取消按钮常显且使用 Symbol 图标 | 正常 |

### US-5: CancelButtonStyle 枚举行为

**作为** 应用开发者,
**我想要** 理解 CancelButtonStyle 三种枚举值的可见性语义,
**以便** 选择取消按钮的显示形态。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN `CancelButtonStyle.CONSTANT` THEN 取消按钮（slot 3）与取消图标（slot 2）始终可见：opacity=1.0、VISIBLE、enabled=true | 正常 |
| AC-5.2 | WHEN `CancelButtonStyle.INVISIBLE` THEN 取消按钮与图标始终隐藏：opacity=0.0、INVISIBLE（非 GONE，保留槽位空间）、enabled=false | 正常 |
| AC-5.3 | WHEN `CancelButtonStyle.INPUT` 且文本框内容非空 THEN 取消按钮与图标可见（opacity=1.0、VISIBLE、enabled） | 正常 |
| AC-5.4 | WHEN `CancelButtonStyle.INPUT` 且文本框内容为空 THEN 取消按钮与图标隐藏（opacity=0.0、INVISIBLE、disabled） | 正常 |
| AC-5.5 | WHEN 未设置 cancelButton style THEN 默认值为 `CancelButtonStyle.INPUT`（`search_layout_property.h:93` GetCancelButtonStyle value_or INPUT） | 边界 |

### US-6: 取消按钮点击行为

**作为** 应用开发者,
**我想要** 理解点击取消按钮的完整行为（清空文本+重新聚焦）,
**以便** 理解清空文本与重新聚焦的完整交互。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN 点击可见的取消按钮 THEN 调用 `textFieldPattern->ClearTextContent()` 清空文本框内容 | 正常 |
| AC-6.2 | WHEN 点击取消按钮 THEN 调用 `focusHub->RequestFocusImmediately()` 重新聚焦文本框，并触发 `HandleFocusEvent` | 正常 |
| AC-6.3 | WHEN 文本框处于拖拽中（`IsDragging()` 或 `IsHandleDragging()` 为 true）THEN 忽略取消按钮点击 | 异常 |

### US-7: 图标颜色与深色模式更新

**作为** 平台维护者,
**我想要** 规格文档化用户设色保护机制与深色模式颜色更新行为,
**以便** 理解用户设色保护与深色模式颜色更新机制。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-7.1 | WHEN 用户未设置图标颜色且系统切换深色模式 THEN `OnIconColorConfigrationUpdate` 自动更新搜索/取消图标颜色为主题新值 | 正常 |
| AC-7.2 | WHEN 用户已设置图标颜色（SearchIconColorSetByUser/CancelIconColorSetByUser=true）且系统切换深色模式 THEN 不覆盖用户颜色，保持用户设定 | 正常 |
| AC-7.3 | WHEN Image 图标（IMAGE_ETS_TAG）颜色更新且源为 SVG THEN 更新 ImageSourceInfo 填充色 + ImageRenderProperty SVG 填充色 | 正常 |
| AC-7.4 | WHEN Image 图标颜色更新且源非 SVG（光栅图） THEN 不重染色（无法对光栅图重新着色） | 边界 |
| AC-7.5 | WHEN Symbol 图标颜色更新且用户未设 TextColorFlagByUser THEN 更新 SymbolColorList；若已设则跳过 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-4 | TASK-02 | UITest | search_model_ng.cpp:281 SearchIconUDSize |
| AC-1.2 | R-5 | TASK-02 | UITest | search_model_ng.cpp:314 SearchIconColorSetByUser |
| AC-1.3 | R-1 | TASK-02 | UITest | search_pattern.cpp:2522 SetSearchImageIconOptions |
| AC-1.4 | R-7 | TASK-02 | UITest | search.d.ts:582 默认值 |
| AC-1.5 | R-6 | TASK-02 | 单测 | search.d.ts:368 不支持百分比 |
| AC-1.6 | R-7 | TASK-02 | UITest | search_pattern.cpp:2941 SEARCH_SVG 回退 |
| AC-2.1 | R-2 | TASK-02 | UITest | search_pattern.cpp:2518-2520 Symbol 分派 |
| AC-2.2 | R-3 | TASK-02 | UITest | search_pattern.cpp:2521 Image 回退 |
| AC-2.3 | R-8 | TASK-02 | UITest | search_pattern.cpp:3017 searchIconSymbol_ 回调 |
| AC-3.1 | R-10 | TASK-02 | UITest | search_model_ng.cpp:349 CancelButtonStyle |
| AC-3.2 | R-11 | TASK-02 | UITest | search_model_ng.cpp:378 CancelButtonUDSize |
| AC-3.3 | R-11 | TASK-02 | UITest | search_model_ng.cpp:373 CancelIconColorSetByUser |
| AC-3.4 | R-11 | TASK-02 | UITest | search_pattern.cpp:2864 UpdateSrc |
| AC-4.1 | R-2 | TASK-02 | UITest | search_pattern.cpp:2557 CreateOrUpdateSymbol(CANCEL) |
| AC-4.2 | R-10, R-2 | TASK-02 | UITest | 同上 |
| AC-5.1 | R-12 | TASK-02 | UITest | search_pattern.cpp:227 CONSTANT |
| AC-5.2 | R-13 | TASK-02 | UITest | search_pattern.cpp:174 INVISIBLE |
| AC-5.3 | R-14 | TASK-02 | UITest | search_pattern.cpp:228 INPUT+非空 |
| AC-5.4 | R-14 | TASK-02 | UITest | search_pattern.cpp:228 INPUT+空 |
| AC-5.5 | R-15 | TASK-02 | UITest | search_layout_property.h:93 默认 INPUT |
| AC-6.1 | R-16 | TASK-02 | UITest | search_pattern.cpp:868 ClearTextContent |
| AC-6.2 | R-16 | TASK-02 | UITest | search_pattern.cpp:877 RequestFocusImmediately |
| AC-6.3 | R-17 | TASK-02 | UITest | search_pattern.cpp:865-866 拖拽守卫 |
| AC-7.1 | R-18 | TASK-02 | UITest | search_pattern.cpp:2229 OnIconColorConfigrationUpdate |
| AC-7.2 | R-19 | TASK-02 | UITest | search_pattern.cpp:2271 ColorSetByUser 守卫 |
| AC-7.3 | R-20 | TASK-02 | UITest | search_pattern.cpp:2273-2278 SVG 重染色 |
| AC-7.4 | R-20 | TASK-02 | UITest | search_pattern.cpp:2273 IsSvg 守卫 |
| AC-7.5 | R-21 | TASK-02 | UITest | search_pattern.cpp:2261 TextColorFlagByUser 守卫 |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|----------|----------|-----------|---------|
| R-1 | 行为 | `searchIcon(IconOptions)` 传入含 src 的对象 | 走 Image 路径：`SetSearchImageIconOptions(IconOptions(src))` + `CreateOrUpdateImage(SEARCH_IMAGE_INDEX)` | src 为空时回退 SEARCH_SVG | AC-1.3 |
| R-2 | 行为 | `searchIcon(SymbolGlyphModifier)` 且 API≥12 且 IsNeedSymbol()=true 且无自定义 src | 走 Symbol 路径：`CreateOrUpdateSymbol(SEARCH_IMAGE_INDEX)` 创建 SYMBOL_ETS_TAG/TextPattern，使用 `searchTheme->GetSearchSymbolId()` | 三条件须同时满足 | AC-2.1, AC-4.1 |
| R-3 | 边界 | API<12 或 IsNeedSymbol()=false 或有自定义 src | 回退 Image 路径（IMAGE_ETS_TAG/ImagePattern） | — | AC-2.2 |
| R-4 | 行为 | `IconOptions.size = N` | 写入 `SearchLayoutProperty.SearchIconUDSize`(MEASURE)，布局算法 `ImageMeasure` 用 `min(UDSize, searchHeight_)` | 不支持百分比 | AC-1.1 |
| R-5 | 行为 | `IconOptions.color = C` | 写入 `searchImageIconOptions_.color`；若 has_value 则 `SearchIconColorSetByUser=true`，否则 reset | Image 路径才设此标志 | AC-1.2 |
| R-6 | 边界 | `IconOptions.size` 为百分比 | 忽略百分比设置 | SDK 注明 "cannot be set in percentage" | AC-1.5 |
| R-7 | 行为 | `IconOptions.src` 为空或未设 | `UpdateImageIconProperties` 回退 `InternalResource::SEARCH_SVG` + `IconTheme::GetIconPath` | — | AC-1.4, AC-1.6 |
| R-8 | 行为 | `SymbolGlyphModifier.symbolApply` 回调 | 存储为 `SearchLayoutProperty.searchIconSymbol_` lambda，symbol 节点创建后经 `UpdateSymbolLayoutProperty` 调用应用 | lambda 不参与 Clone/Reset | AC-2.3 |
| R-9 | 行为 | `cancelButton(CancelButtonOptions)` 传入对象 | 经 `SetCancelImageIcon` 解包 IconOptions 各字段（size/color/src），条件性应用 has_value 字段 | — | AC-3.2..AC-3.4 |
| R-10 | 行为 | `CancelButtonOptions.style = S` 或 `CancelButtonSymbolOptions.style = S` | 写入 `SearchLayoutProperty.CancelButtonStyle`(MEASURE)，并调用 `UpdateChangeEvent` 重新评估可见性 | 触发重布局 | AC-3.1, AC-4.2 |
| R-11 | 行为 | `CancelButtonOptions.icon = { size/color/src }` | size→CancelButtonUDSize(MEASURE)；color→cancelImageIconOptions + CancelIconColorSetByUser；src→UpdateSrc | — | AC-3.2..AC-3.4 |
| R-12 | 行为 | `CancelButtonStyle.CONSTANT` | `IsEventEnabled` 返回 true：opacity=1.0、VISIBLE、enabled=true | 始终可见 | AC-5.1 |
| R-13 | 行为 | `CancelButtonStyle.INVISIBLE` | `IsEventEnabled` 返回 false：opacity=0.0、INVISIBLE（非 GONE）、disabled=false | 保留槽位空间 | AC-5.2 |
| R-14 | 行为 | `CancelButtonStyle.INPUT` | `IsEventEnabled` 返回 `!textValue.empty()`：文本非空→可见，文本空→隐藏(INVISIBLE) | — | AC-5.3, AC-5.4 |
| R-15 | 边界 | 未设置 cancelButton style | 默认 `CancelButtonStyle.INPUT`（`GetCancelButtonStyle().value_or(INPUT)`） | — | AC-5.5 |
| R-16 | 行为 | 点击可见取消按钮 | `ClearTextContent()` 清空文本 + `RequestFocusImmediately()` 重新聚焦 + `HandleFocusEvent` + 无障碍 REQUEST_FOCUS 事件 | 同时清空和聚焦 | AC-6.1, AC-6.2 |
| R-17 | 异常 | 文本框拖拽中（IsDragging/IsHandleDragging）点击取消按钮 | `CHECK_NULL_VOID` 守卫中断，忽略点击 | — | AC-6.3 |
| R-18 | 行为 | 用户未设图标颜色 + 深色模式切换 | `OnIconColorConfigrationUpdate` 更新图标颜色为主题新值（Symbol 用 SymbolColorList，Image SVG 用 fillColor） | — | AC-7.1 |
| R-19 | 行为 | 用户已设图标颜色 + 深色模式切换 | `*ColorSetByUser` 标志守卫，不覆盖用户颜色 | Symbol 用 TextColorFlagByUser | AC-7.2 |
| R-20 | 边界 | Image 图标颜色更新 + 源为 SVG | 更新 ImageSourceInfo.SetFillColor + ImageRenderProperty.UpdateSvgFillColor；非 SVG 则不重染色 | 仅 SVG 可重染色 | AC-7.3, AC-7.4 |
| R-21 | 行为 | Symbol 图标颜色更新 + 用户未设 TextColorFlagByUser | 更新 SymbolColorList；若 TextColorFlagByUser=true 则跳过 | — | AC-7.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | US-1 searchIcon(IconOptions) | UITest | 验证 size/color/src 写入与默认回退；百分比忽略 |
| VM-2 | US-2 searchIcon(SymbolGlyphModifier) | UITest | 验证 Symbol/Image 分派条件；symbolApply 回调应用 |
| VM-3 | US-3 cancelButton(CancelButtonOptions) | UITest | 验证 style/icon size/color/src 写入 |
| VM-4 | US-4 cancelButton(CancelButtonSymbolOptions) | UITest | 验证 Symbol 取消图标创建 |
| VM-5 | US-5 CancelButtonStyle 语义 | UITest | 验证 CONSTANT/INVISIBLE/INPUT 三态可见性与 INVISIBLE 保留空间 |
| VM-6 | US-6 取消按钮点击行为 | UITest | 验证清空+聚焦；拖拽守卫 |
| VM-7 | US-7 颜色与深色模式 | UITest | 验证用户设色保护；SVG 重染色限制；Symbol TextColorFlagByUser 门控 |

## API 变更分析

### 新增 API

> 补录已有 Public API。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `searchIcon(value: IconOptions \| SymbolGlyphModifier)` | Public | IconOptions{size/color/src}(@since 10) 或 SymbolGlyphModifier(@since 12) | SearchAttribute | 无 | 设置搜索图标样式 | AC-1.1..AC-2.3 |
| `cancelButton(value: CancelButtonOptions \| CancelButtonSymbolOptions)` | Public | CancelButtonOptions{style/icon}(@since 10) 或 CancelButtonSymbolOptions{style/icon:SymbolGlyphModifier}(@since 12) | SearchAttribute | 无 | 设置取消按钮样式与图标 | AC-3.1..AC-4.2 |
| `enum CancelButtonStyle { CONSTANT, INVISIBLE, INPUT }` | Public | — | — | 无 | 取消按钮显示模式枚举 | AC-5.1..AC-5.5 |
| `interface IconOptions { size?: Length, color?: ResourceColor, src?: ResourceStr }` | Public | — | — | 无 | 图标选项 | AC-1.1..AC-1.6 |
| `interface CancelButtonOptions { style?: CancelButtonStyle, icon?: IconOptions }` | Public | — | — | 无 | 取消按钮选项（Image 图标） | AC-3.1..AC-3.4 |
| `interface CancelButtonSymbolOptions { style?: CancelButtonStyle, icon?: SymbolGlyphModifier }` | Public | — | — | 无 | 取消按钮选项（Symbol 图标） | AC-4.1, AC-4.2 |
| C-API `setSearchSearchIcon`/`setSearchCancelButton`/`setSearchSymbol`/`setCancelSymbolButton`/`setSearchDefaultIcon`/`setJsSearchDefaultCancelButton` | InnerApi | — | void | 无 | C-ABI 图标/取消按钮写入 | AC-1.1..AC-4.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `searchIcon` value 类型 | 变更 | @since 10 为 IconOptions，@since 12 新增 SymbolGlyphModifier 联合类型 | API < 12 不支持 SymbolGlyphModifier | AC-2.1, AC-2.2 |
| `cancelButton` value 类型 | 变更 | @since 10 为 object/CancelButtonOptions，@since 12 新增 CancelButtonSymbolOptions | API < 12 不支持 Symbol 取消图标 | AC-4.1 |

## 接口规格

### 接口定义

**searchIcon(value: IconOptions | SymbolGlyphModifier)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `searchIcon(value: IconOptions \| SymbolGlyphModifier): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1..AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value(IconOptions) | IconOptions | 是 | — | size 不支持百分比；src 空回退 SEARCH_SVG |
| value.size | Length | 否 | 16vp(穿戴 16vp) | 不支持百分比 |
| value.color | ResourceColor | 否 | 浅色#99182431/深色#99ffffff | 设色后深色模式不覆盖 |
| value.src | ResourceStr | 否 | SEARCH_SVG 内置 | — |
| value(SymbolGlyphModifier) | SymbolGlyphModifier | 是 | — | @since 12；API<12 回退 Image |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | IconOptions 含 src | Image 路径 | AC-1.3 |
| 2 | SymbolGlyphModifier + API≥12 + 无 src + IsNeedSymbol | Symbol 路径 | AC-2.1 |
| 3 | API<12 或非 symbol | 回退 Image | AC-2.2 |
| 4 | src 空 | 回退 SEARCH_SVG | AC-1.6 |
| 5 | size 百分比 | 忽略 | AC-1.5 |

---

**cancelButton(value: CancelButtonOptions | CancelButtonSymbolOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `cancelButton(value: CancelButtonOptions \| CancelButtonSymbolOptions): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1..AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.style | CancelButtonStyle | 否 | INPUT | CONSTANT/INVISIBLE/INPUT |
| value.icon(IconOptions) | IconOptions | 否 | 主题默认 | size 不支持百分比 |
| value.icon(SymbolGlyphModifier) | SymbolGlyphModifier | 否 | — | @since 12；CancelButtonSymbolOptions 专用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | style=CONSTANT | 始终可见 | AC-5.1 |
| 2 | style=INVISIBLE | 始终隐藏(INVISIBLE) | AC-5.2 |
| 3 | style=INPUT+文本非空 | 可见 | AC-5.3 |
| 4 | style=INPUT+文本空 | 隐藏(INVISIBLE) | AC-5.4 |
| 5 | 点击取消按钮 | 清空+聚焦 | AC-6.1, AC-6.2 |

## 兼容性声明

- **已有 API 行为变更:** 是。`searchIcon`/`cancelButton` 在 API 12 新增 SymbolGlyphModifier 联合类型（API<12 不支持 Symbol 图标，回退 Image）；`CancelButtonStyle.INVISIBLE` 使用 `VisibleType::INVISIBLE`（非 GONE），保留槽位布局空间。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（searchIcon/cancelButton）；API 12（SymbolGlyphModifier）
- **API 版本号策略:** searchIcon/cancelButton @since 10 dynamic / @since 23 static；SymbolGlyphModifier 重载 @since 12；CancelButtonStyle @since 10。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Symbol/Image 三条件分派 | API≥12 + src空 + IsNeedSymbol() → Symbol；否则 Image。分派在 CreateSearchIcon/CreateCancelIcon 中决定 | AC-2.1, AC-2.2 |
| CancelButtonStyle INVISIBLE 用 INVISIBLE 非 GONE | 隐藏时保留槽位空间，不参与 GONE 折叠 | AC-5.2 |
| 用户设色保护 | *ColorSetByUser/TextColorFlagByUser 标志门控深色模式颜色更新 | AC-7.1, AC-7.2 |
| SVG 重染色限制 | Image 图标颜色更新仅对 SVG 源生效，非 SVG 不重染 | AC-7.3, AC-7.4 |
| 取消按钮+图标分离布局 | 取消按钮(slot3)为透明 CIRCLE Button，取消图标(slot2)独立居中于按钮内；LayoutCancelButton 读 autoDisable 相对搜索按钮定位 | AC-5.1..AC-5.5 |
| symbolApply lambda 不参与 Clone/Reset | searchIconSymbol_/cancelIconSymbol_ 存于 SearchLayoutProperty 但不在 ACE property group 宏中，不克隆不重置 | AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 图标节点变更触发 PROPERTY_UPDATE_MEASURE，单帧内完成重布局 | UITest 帧率 | search_layout_algorithm.cpp ImageMeasure/CancelImageMeasure |
| 内存 | Symbol/Image 节点互斥创建（ReplaceChild），同一槽位仅一个节点 | 内存分析 | search_pattern.cpp:2625 ReplaceChild |
| 可靠性 | HasSearchIconNodeCreated/HasCancelIconNodeCreated 守卫保证幂等创建 | 单测 | search_node.h:150,165 |
| 可测试性 | CancelButtonStyle/CancelButtonUDSize/SearchIconUDSize 经 SearchLayoutProperty 暴露，支持 Inspector 检查 | Inspector dump | search_layout_property.h:93-96 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 图标默认 16vp | — | UITest | search.d.ts:582 |
| 平板 | 同手机 | 无差异 | UITest | — |
| 折叠屏 | 同手机 | 无差异 | UITest | — |
| 穿戴 | 图标默认 16vp | — | UITest | search.d.ts:580 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 取消按钮点击触发 REQUEST_FOCUS_FOR_ACCESSIBILITY_NOT_INTERRUPT 无障碍事件 | AC-6.2 |
| 大字体 | 是 | 图标尺寸受 minFontScale/maxFontScale 约束（Feat-04）；Symbol 图标随 fontScale 缩放 | AC-1.1 |
| 深色模式 | 是 | 图标颜色深色模式自动更新（用户未设色时）；用户设色后保护 | AC-7.1..AC-7.5 |
| 多窗口/分屏 | 否 | 无特殊行为 | — |
| 多用户 | 否 | 无特殊行为 | — |
| 版本升级 | 是 | API 10→12 SymbolGlyphModifier 新增；API 12 前仅 Image | AC-2.1, AC-2.2 |
| 生态兼容 | 是 | 动态(@since 10/12) + 静态(@since 23) + C-API 修饰符 + Cangjie FFI | 全部 AC |

## 行为场景（Gherkin）

```gherkin
Feature: Search 搜索图标与取消按钮
  作为应用开发者
  我想要配置搜索图标和取消按钮样式
  以便提供一致的搜索交互视觉

  Scenario Outline: searchIcon 的 Symbol/Image 分派
    Given Search 组件已创建
    When 调用 searchIcon(<iconType>) 且 API 版本为 <apiVersion>
    Then 搜索图标节点类型为 <nodeType>

    Examples:
      | iconType | apiVersion | nodeType |
      | IconOptions | 10 | IMAGE_ETS_TAG |
      | SymbolGlyphModifier | 12 | SYMBOL_ETS_TAG |
      | SymbolGlyphModifier | 11 | IMAGE_ETS_TAG |

  Scenario: CancelButtonStyle 三态可见性
    Given Search 组件已创建且 cancelButton style = <style>
    When 文本框内容为 "<content>"
    Then 取消按钮可见性为 <visibility> 且 opacity 为 <opacity>

    Examples:
      | style | content | visibility | opacity |
      | CONSTANT | "abc" | VISIBLE | 1.0 |
      | CONSTANT | "" | VISIBLE | 1.0 |
      | INVISIBLE | "abc" | INVISIBLE | 0.0 |
      | INVISIBLE | "" | INVISIBLE | 0.0 |
      | INPUT | "abc" | VISIBLE | 1.0 |
      | INPUT | "" | INVISIBLE | 0.0 |

  Scenario: 用户设色保护深色模式
    Given Search 组件已创建且用户已设置搜索图标颜色为红色
    When 系统切换至深色模式
    Then 搜索图标颜色保持红色（不覆盖）
    And SearchIconColorSetByUser 标志为 true

  Scenario: 取消按钮点击清空并重新聚焦
    Given Search 组件已创建且文本框内容为 "abc"
    When 用户点击可见的取消按钮
    Then 文本框内容被清空
    And 焦点重新回到文本框
    And 无障碍 REQUEST_FOCUS 事件触发

  Scenario: 拖拽中点击取消按钮被忽略
    Given Search 组件已创建且文本框处于拖拽状态
    When 用户点击取消按钮
    Then 点击被忽略，文本不被清空
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "CreateSearchIcon/CreateCancelIcon 如何按 API 版本+src+IsNeedSymbol 三条件分派 Symbol/Image 图标"
  - repo: "openharmony/arkui_ace_engine"
    query: "CancelButtonStyle CONSTANT/INVISIBLE/INPUT 的 IsEventEnabled 判定与 INVISIBLE(非GONE) 槽位保留"
  - repo: "openharmony/arkui_ace_engine"
    query: "SearchIconColorSetByUser/CancelIconColorSetByUser 标志如何门控深色模式图标颜色更新"
  - repo: "openharmony/arkui_ace_engine"
    query: "Image 图标 SVG 重染色限制（imageSourceInfo.IsSvg 守卫）"
  - repo: "openharmony/arkui_ace_engine"
    query: "OnClickCancelButton 同时 ClearTextContent + RequestFocusImmediately 的完整行为"
  - repo: "openharmony/interface_sdk-js"
    query: "search.d.ts 中 searchIcon/cancelButton/CancelButtonStyle/IconOptions 的 @since 版本与联合类型演变"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/search.d.ts`；`frameworks/core/components_ng/pattern/search/search_pattern.cpp`；`design.md`(DESIGN-Func-05-09-03)
