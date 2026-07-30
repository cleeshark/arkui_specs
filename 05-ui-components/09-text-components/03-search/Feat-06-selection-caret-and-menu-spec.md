# 特性规格

> Func-05-09-03-Feat-06 选择、光标与菜单：覆盖 copyOption/selectionMenuHidden/selectionMenuOptions(EditMenuOptions)/selectedBackgroundColor/selectedDragPreviewStyle/enableSelectedDataDetector/caretStyle(CaretStyle)/caretPosition 共 8 个属性。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 选择、光标与菜单（Selection, Caret & Menu） |
| 特性编号 | Func-05-09-03-Feat-06 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 8(caretPosition)、API 9(copyOption)、API 10(selectionMenuHidden/caretStyle)、API 12(selectedBackgroundColor/editMenuOptions)、API 22(enableSelectedDataDetector)、API 23(selectedDragPreviewStyle) |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 复制与选区菜单规格 | 补录：copyOption(@since 9)、selectionMenuHidden(@since 10)、editMenuOptions(@since 12) |
| ADDED | 选区背景与拖拽预览规格 | 补录：selectedBackgroundColor(@since 12)、selectedDragPreviewStyle(@since 23) |
| ADDED | 数据检测器规格 | 补录：enableSelectedDataDetector(@since 22) |
| ADDED | 光标样式与位置规格 | 补录：caretStyle(@since 10)、caretPosition(@since 8, Controller 方法) |

## 输入文档

- 设计文档：`design.md`（DESIGN-Func-05-09-03，Feat-06 增量合并）
- 源码定位：
  - 全委托子 TextField：`search_model_ng.cpp` 各 setter 经 `GetChildren().front()`
  - 状态位置：copyOption/selectionMenuHidden/selectedDragPreviewStyle→TextFieldLayoutProperty；selectedBackgroundColor/caretStyle→TextFieldPaintProperty；selectionMenuOptions/enableSelectedDataDetector→TextFieldPattern 运行时
  - caretStyle 拆分：`search_model_ng.cpp:208`(SetCaretWidth) `:221`(SetCaretColor)；C-API `search_dynamic_modifier.cpp:202`(SetSearchCaretStyle)
  - 数据检测器前置条件：`search.d.ts:627-628` 仅 CopyOptions=LocalDevice/CrossDevice 生效
  - SDK：`interface/sdk-js/api/@internal/component/ets/search.d.ts` + `text_common.d.ts`

## 用户故事

### US-1: 复制与选区菜单

**作为** 应用开发者,
**我想要** 控制文本复制能力与选区菜单的显隐及自定义,
**以便** 控制文本复制权限与选区菜单的显示。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 调用 `.copyOption(CopyOptions.LocalDevice)`（@since 9，默认） THEN 子 TextFieldLayoutProperty.CopyOptions=LocalDevice，触发 MEASURE | 正常 |
| AC-1.2 | WHEN 调用 `.copyOption(CopyOptions.None)` THEN 禁用复制/剪切/拖拽，仅保留粘贴/全选 | 正常 |
| AC-1.3 | WHEN 调用 `.selectionMenuHidden(true)`（@since 10，默认 false） THEN 子 TextFieldLayoutProperty.SelectionMenuHidden=true，触发 MEASURE，不弹选区菜单 | 正常 |
| AC-1.4 | WHEN 调用 `.editMenuOptions({ onCreateMenu, onMenuItemClick, onPrepare })`（@since 12） THEN 3 回调存于子 TextFieldPattern 运行时（OnSelectionMenuOptionsUpdate） | 正常 |
| AC-1.5 | WHEN onPrepareMenu 未设 THEN onPrepare 回调为空（@since 20 引入 onPrepareMenu） | 边界 |

### US-2: 选区背景与拖拽预览

**作为** 应用开发者,
**我想要** 自定义选中文本背景色与拖拽预览样式,
**以便** 自定义选区与拖拽的视觉外观。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `.selectedBackgroundColor(Color.Red)`（@since 12） THEN 子 TextFieldPaintProperty.SelectedBackgroundColor=红色；未设透明度时默认 20% 透明度，触发 RENDER | 正常 |
| AC-2.2 | WHEN 未设 selectedBackgroundColor THEN 使用默认 20% 透明度 | 正常 |
| AC-2.3 | WHEN 调用 `.selectedDragPreviewStyle({ color: Color.Blue })`（@since 23） THEN 子 TextFieldLayoutProperty.SelectedDragPreviewStyle 设值(MEASURE)，拖拽时 dragBackgroundColor 用此值 | 正常 |
| AC-2.4 | WHEN selectedDragPreviewStyle 传 undefined THEN 回退主题默认色（浅色白/深色黑） | 边界 |

### US-3: 数据检测器

**作为** 应用开发者,
**我想要** 开启选中文本的实体识别,
**以便** 自动识别选中文本中的链接/邮箱等实体。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 `.enableSelectedDataDetector(true)`（@since 22，默认 true） THEN 子 TextFieldPattern.SetSelectDetectEnable(true)，运行时标志 | 正常 |
| AC-3.2 | WHEN enableSelectedDataDetector=true 且 CopyOptions=LocalDevice/CrossDevice THEN 识别所有实体类型 | 正常 |
| AC-3.3 | WHEN CopyOptions=None THEN enableSelectedDataDetector 不生效（前置条件：需 CopyOptions 非 None） | 边界 |
| AC-3.4 | WHEN enableSelectedDataDetector=false THEN 不进行实体识别 | 正常 |

### US-4: 光标样式与位置

**作为** 应用开发者,
**我想要** 自定义光标宽度/颜色并编程控制光标位置,
**以便** 自定义光标外观并编程控制光标位置。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 调用 `.caretStyle({ width: '3vp', color: Color.Red })`（@since 10） THEN C-API SetSearchCaretStyle 内部分发为 SetCaretWidth(MEASURE)+SetCaretColor(RENDER)，存于子 TextFieldPaintProperty | 正常 |
| AC-4.2 | WHEN caretStyle 仅设 width 不设 color THEN ResetSearchCaretColor 保留宽度，重置颜色为主题默认 #007DFF | 边界 |
| AC-4.3 | WHEN 未设 caretStyle THEN 默认 width=2vp、color=#007DFF | 正常 |
| AC-4.4 | WHEN 调用 `controller.caretPosition(5)`（@since 8） THEN 委托 SearchPattern.HandleCaretPosition→子 TextFieldPattern.SetCaretPosition(5) | 正常 |
| AC-4.5 | WHEN caretPosition < 0 THEN 定位至 0；> 文本长度 THEN 定位至末尾 | 边界 |
| AC-4.6 | WHEN SetCaretColor 设色 THEN CaretColorFlagByUser=true，保护用户色不被主题覆盖 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-06 | UITest | search_model_ng.cpp:687 SetCopyOption |
| AC-1.2 | R-1 | TASK-06 | UITest | search.d.ts:912 None 禁用 |
| AC-1.3 | R-2 | TASK-06 | UITest | search_model_ng.cpp:760 SetSelectionMenuHidden |
| AC-1.4 | R-3 | TASK-06 | UITest | search_model_ng.cpp:894 SetSelectionMenuOptions |
| AC-1.5 | R-3 | TASK-06 | UITest | text_common.d.ts:1450 onPrepare @since 20 |
| AC-2.1 | R-4 | TASK-06 | UITest | search_model_ng.cpp:504 SetSelectedBackgroundColor |
| AC-2.2 | R-4 | TASK-06 | UITest | search.d.ts:690 20%透明度 |
| AC-2.3 | R-5 | TASK-06 | UITest | search_model_ng.cpp:3042 SetSelectedDragPreviewStyle |
| AC-2.4 | R-5 | TASK-06 | UITest | search.d.ts:1525 主题默认 |
| AC-3.1 | R-6 | TASK-06 | UITest | search_model_ng.cpp:2464 SetSelectDetectEnable |
| AC-3.2 | R-6 | TASK-06 | UITest | search.d.ts:625 全实体类型 |
| AC-3.3 | R-7 | TASK-06 | UITest | search.d.ts:627 前置条件 |
| AC-3.4 | R-6 | TASK-06 | UITest | 同上 |
| AC-4.1 | R-8 | TASK-06 | UITest | search_dynamic_modifier.cpp:202 SetSearchCaretStyle |
| AC-4.2 | R-9 | TASK-06 | UITest | search_dynamic_modifier.cpp:1957 ResetSearchCaretColor |
| AC-4.3 | R-8 | TASK-06 | UITest | search.d.ts:705 默认 |
| AC-4.4 | R-10 | TASK-06 | UITest | search_model_ng.cpp:1479 SetCaretPosition |
| AC-4.5 | R-10 | TASK-06 | UITest | search.d.ts:55 边界 |
| AC-4.6 | R-8 | TASK-06 | UITest | search_model_ng.cpp:230 CaretColorFlagByUser |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|----------|----------|-----------|---------|
| R-1 | 行为 | `copyOption(CopyOptions)` 设置 | 子 TextFieldLayoutProperty.CopyOptions 设值(MEASURE) | 默认 LocalDevice；None 禁用复制/剪切/拖拽 | AC-1.1, AC-1.2 |
| R-2 | 行为 | `selectionMenuHidden(bool)` 设置 | 子 TextFieldLayoutProperty.SelectionMenuHidden 设值(MEASURE) | 默认 false；true 不弹选区菜单 | AC-1.3 |
| R-3 | 行为 | `editMenuOptions(EditMenuOptions)` 设置 | 3 回调存于子 TextFieldPattern 运行时(OnSelectionMenuOptionsUpdate) | 非属性；onPrepare @since 20 | AC-1.4, AC-1.5 |
| R-4 | 行为 | `selectedBackgroundColor(Color)` 设置 | 子 TextFieldPaintProperty.SelectedBackgroundColor 设值(RENDER)；未设透明度默认 20% | 默认 20% 透明度 | AC-2.1, AC-2.2 |
| R-5 | 行为 | `selectedDragPreviewStyle(SelectedDragPreviewStyle)` 设置（@since 23） | 子 TextFieldLayoutProperty.SelectedDragPreviewStyle 设值(MEASURE)；拖拽时 dragBackgroundColor 用此值 | undefined→主题默认 | AC-2.3, AC-2.4 |
| R-6 | 行为 | `enableSelectedDataDetector(bool)` 设置（@since 22） | 子 TextFieldPattern.SetSelectDetectEnable 设运行时标志 | 默认 true；非属性 | AC-3.1, AC-3.2, AC-3.4 |
| R-7 | 边界 | CopyOptions=None 时 enableSelectedDataDetector | 不生效（前置条件：需 CopyOptions 非 None） | search.d.ts:627 | AC-3.3 |
| R-8 | 行为 | `caretStyle(CaretStyle)` 设置（@since 10） | C-API SetSearchCaretStyle 分发为 SetCaretWidth(MEASURE)+SetCaretColor(RENDER)；颜色设时 CaretColorFlagByUser=true | 存于子 TextFieldPaintProperty；默认 width=2vp/color=#007DFF | AC-4.1, AC-4.3, AC-4.6 |
| R-9 | 边界 | caretStyle 仅设 width 不设 color | ResetSearchCaretColor 保留宽度，重置颜色 | search_dynamic_modifier.cpp:1957 | AC-4.2 |
| R-10 | 行为 | `controller.caretPosition(N)` 设置（@since 8） | 委托 SearchPattern.HandleCaretPosition→子 TextFieldPattern.SetCaretPosition(N) | N<0→0；N>长度→末尾；非属性，命令式调用 | AC-4.4, AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | US-1 复制与选区菜单 | UITest | 验证 copyOption None 禁用；selectionMenuHidden；editMenuOptions 3 回调运行时存储 |
| VM-2 | US-2 选区背景与拖拽预览 | UITest | 验证 selectedBackgroundColor 20% 默认透明度；selectedDragPreviewStyle 主题回退 |
| VM-3 | US-3 数据检测器 | UITest | 验证 enableSelectedDataDetector 前置条件(CopyOptions 非 None) |
| VM-4 | US-4 光标样式与位置 | UITest | 验证 caretStyle 拆分 SetCaretWidth+SetCaretColor；仅 width 保留；caretPosition 边界 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `copyOption(value: CopyOptions)` | Public | CopyOptions 枚举 | SearchAttribute | 无 | 复制能力 | AC-1.1..AC-1.2 |
| `selectionMenuHidden(value: boolean)` | Public | boolean | SearchAttribute | 无 | 选区菜单隐藏 | AC-1.3 |
| `editMenuOptions(editMenu: EditMenuOptions)` | Public | EditMenuOptions{onCreateMenu/onMenuItemClick/onPrepare} | SearchAttribute | 无 | 自定义选区菜单 | AC-1.4..AC-1.5 |
| `selectedBackgroundColor(value: ResourceColor)` | Public | ResourceColor | SearchAttribute | 无 | 选区背景色 | AC-2.1..AC-2.2 |
| `selectedDragPreviewStyle(value: SelectedDragPreviewStyle\|undefined)` | Public | SelectedDragPreviewStyle{color} | SearchAttribute | 无 | 拖拽预览样式 | AC-2.3..AC-2.4 |
| `enableSelectedDataDetector(enable: boolean\|undefined)` | Public | boolean | SearchAttribute | 无 | 实体识别 | AC-3.1..AC-3.4 |
| `caretStyle(value: CaretStyle)` | Public | CaretStyle{width/color} | SearchAttribute | 无 | 光标样式 | AC-4.1..AC-4.3, AC-4.6 |
| `SearchController.caretPosition(value: number)` | Public | number | void | 无 | 光标位置(Controller 方法) | AC-4.4..AC-4.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 8 属性跨版本引入 | 变更 | @since 8/9/10/12/22/23 分批 | 低版本不支持 | 全部 AC |
| enableSelectedDataDetector 前置条件 | 变更 | @since 22，需 CopyOptions 非 None | 需配合 copyOption 使用 | AC-3.3 |

## 接口规格

> L1+ 复杂度。以下仅列代表性接口。

### 接口定义

**caretStyle(value: CaretStyle)** — 单 SDK 属性拆双 setter

| 属性 | 值 |
|------|-----|
| 函数签名 | `caretStyle(value: CaretStyle): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1..AC-4.3, AC-4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.width | Length | 否 | 2vp | C-API 分发为 SetCaretWidth(MEASURE) |
| value.color | ResourceColor | 否 | #007DFF | C-API 分发为 SetCaretColor(RENDER)；仅 width 时 ResetSearchCaretColor 保留宽度 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设 width+color | SetCaretWidth+SetCaretColor | AC-4.1 |
| 2 | 仅设 width | 保留宽度，重置颜色 | AC-4.2 |
| 3 | 未设 | 默认 2vp/#007DFF | AC-4.3 |
| 4 | 设 color | CaretColorFlagByUser=true | AC-4.6 |

---

**enableSelectedDataDetector(enable: boolean|undefined)** — 前置条件

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableSelectedDataDetector(enable: boolean\|undefined): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1..AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enable | boolean | 否 | true | 仅 CopyOptions=LocalDevice/CrossDevice 时生效；存于 TextFieldPattern 运行时 |

## 兼容性声明

- **已有 API 行为变更:** 是。8 属性跨 API 8-23 引入；enableSelectedDataDetector 需 CopyOptions 非 None 前置条件；caretStyle 单 SDK 属性拆双内部 setter（SetCaretWidth+SetCaretColor），仅 width 时 ResetSearchCaretColor 保留宽度；selectedBackgroundColor 未设透明度默认 20%；selectionMenuOptions 3 回调存运行时非属性。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8（caretPosition）
- **API 版本号策略:** @since 8/9/10/12/22/23 分批标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 全委托子节点 | 8 个 API 全部委托子 TextField（TextFieldLayoutProperty/PaintProperty/Pattern），零个存于 SearchLayoutProperty；CaretUDWidth 声明但 caretStyle setter 不写入 | 全部 AC |
| 菜单回调运行时存储 | selectionMenuOptions 3 回调存于 TextFieldPattern 运行时非 layout property；C-API 分 3 个 *CallbackUpdate 方法 | AC-1.4 |
| 数据检测器前置条件 | enableSelectedDataDetector 仅 CopyOptions=LocalDevice/CrossDevice 时生效 | AC-3.3 |
| caretStyle 拆分 | 单 SDK 属性拆 SetCaretWidth(MEASURE)+SetCaretColor(RENDER) 双内部 setter | AC-4.1 |
| caretColor 用户色保护 | SetCaretColor 设色时 CaretColorFlagByUser=true | AC-4.6 |
| selectedBackgroundColor 20% 默认透明度 | 未设透明度时 C-API 自动 20% | AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | copyOption/selectionMenuHidden 变更触发 MEASURE；selectedBackgroundColor/caretColor 变更触发 RENDER | UITest | search_model_ng.cpp:696/769/513/231 |
| 可测试性 | copyOption/selectionMenuHidden/caretStyle 经子 TextField 属性暴露 | Inspector dump | text_field_layout_property.h:312/321 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 全部属性支持 | — | UITest | — |
| 平板/折叠屏 | 同手机 | 无差异 | UITest | — |
| 穿戴 | 同手机 | 无差异 | UITest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不影响无障碍 | — |
| 大字体 | 否 | 不直接涉及 | — |
| 深色模式 | 是 | selectedDragPreviewStyle 未设时回退主题色（浅白/深黑）；caretColor 未设时主题色 | AC-2.4, AC-4.3 |
| 多窗口/分屏 | 否 | 无特殊行为 | — |
| 多用户 | 否 | 无特殊行为 | — |
| 版本升级 | 是 | 8 属性跨 API 8-23 引入 | 全部 AC |
| 生态兼容 | 是 | 动态+静态+C-API 全覆盖 | 全部 AC |

## 行为场景（Gherkin）

```gherkin
Feature: Search 选择、光标与菜单
  作为应用开发者
  我想要控制文本选择、光标与选区菜单
  以便提供一致的编辑交互

  Scenario Outline: copyOption 能力
    Given Search 组件已创建
    When 调用 .copyOption(<option>)
    Then 复制/剪切/拖拽 <result>

    Examples:
      | option | result |
      | LocalDevice | 允许 |
      | CrossDevice | 允许跨设备 |
      | None | 禁用(仅粘贴/全选) |

  Scenario: enableSelectedDataDetector 前置条件
    Given Search 组件已创建且 enableSelectedDataDetector = true
    When copyOption = <copyOpt>
    Then 实体识别 <result>

    Examples:
      | copyOpt | result |
      | LocalDevice | 生效 |
      | CrossDevice | 生效 |
      | None | 不生效 |

  Scenario: caretStyle 仅设 width
    Given Search 组件已创建
    When 调用 .caretStyle({ width: '3vp' }) 不设 color
    Then ResetSearchCaretColor 保留宽度 3vp
    And 颜色重置为主题默认 #007DFF

  Scenario: caretPosition 边界
    Given Search 组件已创建且文本内容为 "hello"
    When 调用 controller.caretPosition(<pos>)
    Then 光标定位至 <result>

    Examples:
      | pos | result |
      | 2 | 2 |
      | -1 | 0 |
      | 100 | 5(末尾) |
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
    query: "8 个选择/光标/菜单 API 全部委托子 TextField 而非 SearchLayoutProperty"
  - repo: "openharmony/arkui_ace_engine"
    query: "selectionMenuOptions 3 回调存于 TextFieldPattern 运行时而非 layout property"
  - repo: "openharmony/arkui_ace_engine"
    query: "enableSelectedDataDetector 仅 CopyOptions 非 None 时生效的前置条件"
  - repo: "openharmony/arkui_ace_engine"
    query: "caretStyle 单 SDK 属性拆 SetCaretWidth+SetCaretColor 双 setter 与 ResetSearchCaretColor 保留宽度"
  - repo: "openharmony/interface_sdk-js"
    query: "search.d.ts + text_common.d.ts 中 8 个选择/光标/菜单属性的 @since/默认/约束"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/search.d.ts`；`frameworks/core/components_ng/pattern/search/search_model_ng.cpp`；`design.md`(DESIGN-Func-05-09-03)
