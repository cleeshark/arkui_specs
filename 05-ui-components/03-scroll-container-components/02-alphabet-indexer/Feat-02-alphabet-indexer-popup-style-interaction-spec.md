# 特性规格

## 概述

| 特性名称 | 特性编号 | 所属 Epic | 优先级 | 目标版本 | SIG 归属 | 状态 | 复杂度 |
|----------|----------|-----------|--------|----------|----------|------|--------|
| AlphabetIndexer Popup样式与交互 | Feat-02 | 无 | P1 | API 7 ~ 12+ | ArkUI SIG | Baselined（已有实现补录） | 标准 |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/02-alphabet-indexer/design.md` |
| SDK Dynamic | `interface/sdk-js/api/@internal/component/ets/alphabet_indexer.d.ts` |
| SDK Static | `interface/sdk-js/api/arkui/component/alphabetIndexer.static.d.ets` |
| Pattern Source | `frameworks/core/components_ng/pattern/indexer/indexer_pattern.cpp` |
| PaintProperty | `frameworks/core/components_ng/pattern/indexer/indexer_paint_property.h` |
| LayoutAlgorithm | `frameworks/core/components_ng/pattern/indexer/indexer_layout_algorithm.cpp` |
| Theme | `frameworks/core/components_ng/pattern/indexer/indexer_theme.h` |

## 用户故事

### US-1: 配置 Popup 弹出面板外观

作为**应用开发者**，我想要**配置 Popup 弹出面板的文本颜色、背景色、字体和圆角**，以便**弹出面板与应用设计风格一致**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 usingPopup(true) THEN 触摸/滑动索引项时弹出面板显示 | 正常 |
| AC-1.2 | WHEN 设置 usingPopup(false) THEN 不显示弹出面板 | 正常 |
| AC-1.3 | WHEN 设置 popupColor(#FF0000) THEN 弹出面板选中项文本颜色变为红色 | 正常 |
| AC-1.4 | WHEN 设置 popupBackground(#000000) THEN 弹出面板背景色变为黑色 | 正常 |
| AC-1.5 | WHEN 设置 popupSelectedColor(#00FF00) THEN 弹出面板选中项文本颜色变为绿色 | 正常 |
| AC-1.6 | WHEN 设置 popupUnselectedColor(#888888) THEN 弹出面板未选中项文本颜色变为灰色 | 正常 |
| AC-1.7 | WHEN 设置 popupItemBackgroundColor(#DDDDDD) THEN 弹出面板未选中项背景色变为浅灰 | 正常 |
| AC-1.8 | WHEN 设置 popupFont({size:16, weight:FontWeight.Bold}) THEN 弹出面板选中项字体变为 16fp 加粗 | 正常 |
| AC-1.9 | WHEN 设置 popupItemFont({size:12}) THEN 弹出面板未选中项字体变为 12fp | 正常 |
| AC-1.10 | WHEN 不设置 Popup 颜色属性 THEN 使用主题默认值（popupSelectedColor=0xff007dff, popupUnselectedColor=0xff182431, popupItemBackground=0xff33007dff, popupBackground=API<12=0xffffffff/API>=12=0x66808080） | 正常 |

### US-2: 配置 Popup 定位与圆角

作为**应用开发者**，我想要**配置 Popup 的位置偏移、圆角和模糊效果**，以便**精确控制弹出面板的视觉效果**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 popupPosition({x:100, y:200}) THEN 弹出面板相对于默认位置偏移 (100vp, 200vp) | 正常 |
| AC-2.2 | WHEN 不设置 popupPosition THEN 弹出面板使用默认位置（X=60vp, Y=48vp），并根据 alignStyle+RTL 计算实际坐标 | 正常 |
| AC-2.3 | WHEN 设置 popupItemBorderRadius(20) THEN 弹出面板内每个字母项圆角变为 20vp | 正常 |
| AC-2.4 | WHEN 设置 itemBorderRadius(4) THEN 索引条内每个索引项圆角变为 4vp（API >= 12 生效） | 正常 |
| AC-2.5 | WHEN 不设置 popupItemBorderRadius THEN 弹出面板字母项默认圆角 24vp (BUBBLE_ITEM_RADIUS) | 正常 |
| AC-2.6 | WHEN 不设置 itemBorderRadius THEN API>=12 索引项默认圆角 8vp (INDEXER_ITEM_DEFAULT_RADIUS)；API<12 使用 theme hoverRadiusSize | 正常 |
| AC-2.7 | WHEN 设置 popupBackgroundBlurStyle(BlurStyle.COMPONENT_REGULAR) THEN 弹出面板背景应用 COMPONENT_REGULAR 模糊效果 | 正常 |
| AC-2.8 | WHEN 不设置 popupBackgroundBlurStyle THEN 默认 BlurStyle.COMPONENT_REGULAR | 正常 |
| AC-2.9 | WHEN 设置 popupTitleBackground(#FF0000) THEN 弹出面板标题区域背景色变为红色（API >= 12） | 正常 |
| AC-2.10 | WHEN Popup 整体圆角 THEN 默认 28vp (BUBBLE_RADIUS)；可通过 setPopupItemBorderRadius 同时设置 PopupBorderRadius | 正常 |
| AC-2.11 | WHEN 索引条整体圆角 THEN 默认 12vp (INDEXER_DEFAULT_RADIUS)；可通过 setItemBorderRadius 同时设置 IndexerBorderRadius | 正常 |

### US-3: Popup 交互事件

作为**应用开发者**，我想要**通过 onRequestPopupData 和 onPopupSelect 回调实现弹出面板数据联动**，以便**用户选择弹出项时联动列表滚动**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 用户触摸某索引项且 usingPopup=true THEN 弹出面板显示，onRequestPopupData 回调触发请求该索引对应的 popup 数据列表 | 正常 |
| AC-3.2 | WHEN onRequestPopupData 返回 ["A1","A2","A3"] THEN 弹出面板显示 3 个子项 | 正常 |
| AC-3.3 | WHEN onRequestPopupData 返回空数组或 undefined THEN 弹出面板不显示子项列表 | 边界 |
| AC-3.4 | WHEN 用户选择弹出面板中某子项 THEN onPopupSelect 回调触发，参数为该子项的索引 | 正常 |
| AC-3.5 | WHEN onRequestPopupData 返回超过 5 项（折叠态超过 3 项）THEN 仅显示前 5/3 项，超出部分截断 | 边界 |
| AC-3.6 | WHEN Popup 显示期间索引项变更 THEN 弹出面板内容随 onRequestPopupData 新返回值更新 | 正常 |

### US-4: selected 属性与触觉反馈

作为**应用开发者**，我想要**动态更新选中索引并控制触觉反馈**，以便**实现外部联动和自定义交互体验**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 动态设置 selected(5) THEN 索引条视觉选中第 5 项，onSelect 不触发 | 正常 |
| AC-4.2 | WHEN 设置 enableHapticFeedback(true) THEN 索引项选中时触发触觉振动反馈 | 正常 |
| AC-4.3 | WHEN 设置 enableHapticFeedback(false) THEN 禁用触觉振动反馈 | 正常 |
| AC-4.4 | WHEN 不设置 enableHapticFeedback THEN 默认启用触觉反馈 (true) | 正常 |
| AC-4.5 | WHEN selected 超出有效索引范围 THEN selected 被钳位到最大有效索引 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-02 | 可视化 + 单测 | usingPopup=true |
| AC-1.2 | R-2 | TASK-02 | 可视化 + 单测 | usingPopup=false |
| AC-1.3 | R-3 | TASK-02 | 可视化 | SetPopupColor |
| AC-1.4 | R-4 | TASK-02 | 可视化 | SetPopupBackground |
| AC-1.5 | R-5 | TASK-02 | 可视化 | SetPopupSelectedColor |
| AC-1.6 | R-6 | TASK-02 | 可视化 | SetPopupUnselectedColor |
| AC-1.7 | R-7 | TASK-02 | 可视化 | SetPopupItemBackground |
| AC-1.8 | R-8 | TASK-02 | 可视化 | SetPopupFont |
| AC-1.9 | R-9 | TASK-02 | 可视化 | SetPopupItemFont |
| AC-1.10 | R-10 | TASK-02 | 主题检查 | Popup 默认值 |
| AC-2.1 | R-11 | TASK-02 | 测试 | SetPopupPosition |
| AC-2.2 | R-12 | TASK-02 | 测试 + RTL | 默认 popup 位置 |
| AC-2.3 | R-13 | TASK-02 | 可视化 | SetPopupItemBorderRadius |
| AC-2.4 | R-14 | TASK-02 | 可视化 | SetItemBorderRadius |
| AC-2.5 | R-15 | TASK-02 | 主题检查 | 默认 24vp |
| AC-2.6 | R-16 | TASK-02 | API 12 测试 | 默认圆角分支 |
| AC-2.7 | R-17 | TASK-02 | 可视化 | SetPopupBackgroundBlurStyle |
| AC-2.8 | R-18 | TASK-02 | 主题检查 | 默认 BlurStyle |
| AC-2.9 | R-19 | TASK-02 | 可视化 | SetPopupTitleBackground |
| AC-2.10 | R-20 | TASK-02 | 主题检查 | BUBBLE_RADIUS |
| AC-2.11 | R-21 | TASK-02 | 主题检查 | INDEXER_DEFAULT_RADIUS |
| AC-3.1 | R-22 | TASK-02 | 事件回调测试 | onRequestPopupData |
| AC-3.2 | R-23 | TASK-02 | 可视化 + 回调测试 | popup 数据列表 |
| AC-3.3 | R-24 | TASK-02 | 测试 | 空数据 |
| AC-3.4 | R-25 | TASK-02 | 事件回调测试 | onPopupSelect |
| AC-3.5 | R-26 | TASK-02 | 边界测试 | 最大 item 数 |
| AC-3.6 | R-27 | TASK-02 | 测试 | popup 动态更新 |
| AC-4.1 | R-28 | TASK-02 | 测试 | selected 属性 |
| AC-4.2 | R-29 | TASK-02 | 触觉反馈测试 | enableHapticFeedback=true |
| AC-4.3 | R-30 | TASK-02 | 触觉反馈测试 | enableHapticFeedback=false |
| AC-4.4 | R-31 | TASK-02 | 默认值检查 | 默认 true |
| AC-4.5 | R-32 | TASK-02 | 边界测试 | selected 钳位 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 usingPopup(true) | 触摸/滑动索引项时弹出面板显示 | Popup 通过 IsPopup 布尔属性控制 RenderContext visibility | AC-1.1 |
| R-2 | 行为 | 设置 usingPopup(false) | 不显示弹出面板 | 默认 usingPopup=false | AC-1.2 |
| R-3 | 行为 | 设置 popupColor(value) | 弹出面板选中项文本颜色设为 value | 存 PaintProperty；SetByUser=true（仅 LayoutProperty 内 popupColor 的 ByUser flag） | AC-1.3 |
| R-4 | 行为 | 设置 popupBackground(value) | 弹出面板背景色设为 value | 存 PaintProperty；API<12 默认 0xffffffff，API>=12 默认 0x66808080 | AC-1.4 |
| R-5 | 行为 | 设置 popupSelectedColor(value) | 弹出面板选中项文本颜色设为 value | 存 PaintProperty；SetByUser=true | AC-1.5 |
| R-6 | 行为 | 设置 popupUnselectedColor(value) | 弹出面板未选中项文本颜色设为 value | 存 PaintProperty；SetByUser=true | AC-1.6 |
| R-7 | 行为 | 设置 popupItemBackgroundColor(value) | 弹出面板未选中项背景色设为 value | 存 PaintProperty；SetByUser=true | AC-1.7 |
| R-8 | 行为 | 设置 popupFont({size, weight, family, style}) | 弹出面板选中项字体更新 | 仅影响弹出面板选中项 | AC-1.8 |
| R-9 | 行为 | 设置 popupItemFont({size, weight}) | 弹出面板未选中项字体大小和粗细更新 | popupItemFont 仅设置 fontSize + fontWeight（SDK 不提供完整 Font） | AC-1.9 |
| R-10 | 行为 | 不设置 Popup 颜色/字体属性 | 使用 IndexerTheme 默认值 | popupSelectedColor=0xff007dff, popupUnselectedColor=0xff182431, popupItemBackground=0xff33007dff | AC-1.10 |
| R-11 | 行为 | 设置 popupPosition({x, y}) | Popup 位置偏移量写入 LayoutProperty 的 PopupPositionX/PopupPositionY | PopupPositionX/Y 存 LayoutProperty；PROPERTY_UPDATE_LAYOUT | AC-2.1 |
| R-12 | 行为 | 不设置 popupPosition | 默认 X=60vp (BUBBLE_POSITION_X), Y=48vp (BUBBLE_POSITION_Y)；实际坐标由 alignStyle+RTL+popupHorizontalSpace 共同决定 | GetPositionOfPopupNode() 计算 | AC-2.2 |
| R-13 | 行为 | 设置 popupItemBorderRadius(value) | 弹出面板字母项圆角设为 value vp；同时设置 Popup 整体圆角（PopupBorderRadius） | 存 PaintProperty；PROPERTY_UPDATE_MEASURE；默认 24vp | AC-2.3 |
| R-14 | 行为 | 设置 itemBorderRadius(value) | 索引项圆角设为 value vp；同时设置索引条整体圆角（IndexerBorderRadius） | API >= 12 生效；存 PaintProperty；默认 8vp | AC-2.4 |
| R-15 | 行为 | 不设置 popupItemBorderRadius | 默认 24vp (BUBBLE_ITEM_RADIUS) | 主题常量 | AC-2.5 |
| R-16 | 行为 | 不设置 itemBorderRadius + API >= 12 | 默认 8vp (INDEXER_ITEM_DEFAULT_RADIUS) | 主题常量 | AC-2.6 |
| R-16b | 行为 | 不设置 itemBorderRadius + API < 12 | 使用 theme hoverRadiusSize | Pattern 条件分支 | AC-2.6 |
| R-17 | 行为 | 设置 popupBackgroundBlurStyle(value) | 弹出面板背景应用对应 BlurStyle 模糊效果 | 存 PaintProperty；SetByUser=true | AC-2.7 |
| R-18 | 行为 | 不设置 popupBackgroundBlurStyle | 默认 BlurStyle.COMPONENT_REGULAR | 主题默认 | AC-2.8 |
| R-19 | 行为 | 设置 popupTitleBackground(value) | 弹出面板标题区域背景色设为 value | since API 12；存 PaintProperty；SetByUser=true | AC-2.9 |
| R-20 | 行为 | Popup 整体圆角默认 | 28vp (BUBBLE_RADIUS) | 通过 PopupBorderRadius 属性控制 | AC-2.10 |
| R-21 | 行为 | 索引条整体圆角默认 | 12vp (INDEXER_DEFAULT_RADIUS) | 通过 IndexerBorderRadius 属性控制 | AC-2.11 |
| R-22 | 行为 | 用户触摸索引项 + usingPopup=true | onRequestPopupData 回调触发，参数=当前选中索引 | 回调返回 string 数组作为 popup 子项数据 | AC-3.1 |
| R-23 | 行为 | onRequestPopupData 返回 ["A1","A2","A3"] | 弹出面板显示 3 个子项 | 子项使用 popupItemFont/popupUnselectedColor/popupItemBackgroundColor 渲染 | AC-3.2 |
| R-24 | 边界 | onRequestPopupData 返回空数组或 undefined | 弹出面板不显示子项列表 | Pattern 内判断数据长度 | AC-3.3 |
| R-25 | 行为 | 用户选择弹出面板子项 | onPopupSelect 回调触发，参数=子项索引 | 索引为 popup 数据数组的下标 | AC-3.4 |
| R-26 | 边界 | onRequestPopupData 返回超过 5 项（折叠态 3 项） | 仅显示前 INDEXER_BUBBLE_MAXSIZE=5 项（折叠态 3 项） | INDEXER_BUBBLE_MAXSIZE_COLLAPSED_API_TWELVE=3 | AC-3.5 |
| R-27 | 行为 | Popup 显示期间索引项变更 | 弹出面板内容随 onRequestPopupData 新返回值更新 | UpdateBubbleView 重建 popup | AC-3.6 |
| R-28 | 行为 | 动态设置 selected(index) | 视觉选中状态更新，onSelect 不触发 | SetSelected 写入 LayoutProperty | AC-4.1 |
| R-29 | 行为 | enableHapticFeedback=true | 索引项选中时触发 HapticFeedback | Pattern 内 selectedChangedForHaptic_ flag | AC-4.2 |
| R-30 | 行为 | enableHapticFeedback=false | 禁用触觉振动反馈 | 不调用 PostHapticFeedbackEvent | AC-4.3 |
| R-31 | 行为 | 不设置 enableHapticFeedback | 默认 true (GetEnableHapticFeedback().value_or(true)) | 自 API 12 起 | AC-4.4 |
| R-32 | 边界 | selected >= arrayValue.length | selected 钳位到 arrayValue.length-1 | 与 Feat-01 R-4 一致 | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 ~ R-2 | 可视化 + 单测 | usingPopup 开关 |
| VM-2 | R-3 ~ R-9 | 可视化 + 单测 | Popup 颜色/字体设置 |
| VM-3 | R-10 | 主题检查 | Popup 默认值 |
| VM-4 | R-11 ~ R-12 | 测试 + RTL | Popup 定位 |
| VM-5 | R-13 ~ R-21 | 可视化 + API 12 测试 | 圆角与模糊 |
| VM-6 | R-22 ~ R-27 | 事件回调测试 | Popup 交互事件 |
| VM-7 | R-28 ~ R-32 | 测试 | selected 属性与触觉反馈 |

## API 变更分析

### 新增 API

> 已有实现补录，无新增 API。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| popupItemFont | SDK 变更 | popupItemFont 的 Font 参数在 static API 中完整（size/weight/family/style），但在 dynamic API 中实际只使用 fontSize + fontWeight | 使用完整 Font 参数传入，dynamic 管线内部仅处理 size 和 weight | AC-1.9 |

## 接口规格

### 接口定义

**usingPopup(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `usingPopup(value: boolean): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7) |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | boolean | 是 | false | true 时触摸/滑动触发 popup |

---

**popupColor(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupColor(value: ResourceColor): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7) |
| 错误码 | N/A |
| 关联 AC | AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor | 是 | 0xff007dff | Popup 选中项文本颜色 |

---

**popupBackground(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupBackground(value: ResourceColor): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7) |
| 错误码 | N/A |
| 关联 AC | AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor | 是 | API<12: 0xffffffff, API>=12: 0x66808080 | Popup 整体背景色 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | API < 12, 不设置 popupBackground | 默认纯白 0xffffffff | AC-1.10 |
| 2 | API >= 12, 不设置 popupBackground | 默认半透明灰 0x66808080 | AC-1.10 |

---

**popupSelectedColor(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupSelectedColor(value: ResourceColor): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 10) |
| 错误码 | N/A |
| 关联 AC | AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor | 是 | 0xff007dff | Popup 选中项文本颜色；存 PaintProperty |

---

**popupUnselectedColor(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupUnselectedColor(value: ResourceColor): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 10) |
| 错误码 | N/A |
| 关联 AC | AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor | 是 | 0xff182431 | Popup 未选中项文本颜色 |

---

**popupItemBackgroundColor(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupItemBackgroundColor(value: ResourceColor): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 10) |
| 错误码 | N/A |
| 关联 AC | AC-1.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor | 是 | 0xff33007dff | Popup 未选中项背景色 |

---

**popupFont(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupFont(value: Font): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7) |
| 错误码 | N/A |
| 关联 AC | AC-1.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value.size | number \| Resource | 否 | theme popup text size | Popup 选中项字体大小 |
| value.weight | FontWeight \| number \| string | 否 | FontWeight.Normal | Popup 选中项字体粗细 |
| value.family | string \| Resource | 否 | theme default | Popup 选中项字体族 |
| value.style | FontStyle | 否 | FontStyle.Normal | Popup 选中项字体风格 |

---

**popupItemFont(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupItemFont(value: Font): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 10) |
| 错误码 | N/A |
| 关联 AC | AC-1.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value.size | number \| Resource | 否 | theme default | Popup 未选中项字体大小 |
| value.weight | FontWeight \| number \| string | 否 | FontWeight.Normal | Popup 未选中项字体粗细 |

**注意**: dynamic 管线内部仅处理 size 和 weight（`indexer_model_ng.cpp:SetFontSize + SetFontWeight`）；static 管线处理完整 Font。

---

**popupPosition(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupPosition(value: Position): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 8) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value.x | Length | 否 | 0 (relative to default position) | 写入 PopupPositionX |
| value.y | Length | 否 | 0 (relative to default position) | 写入 PopupPositionY |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | popupPosition({x:100, y:200}) | Popup 基准位置偏移 100vp(X) + 200vp(Y) | AC-2.1 |
| 2 | 不设置 popupPosition | 默认 X=60vp, Y=48vp；加上 alignStyle/RTL/popupHorizontalSpace 计算最终位置 | AC-2.2 |

---

**popupItemBorderRadius(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupItemBorderRadius(value: number): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 12) |
| 错误码 | N/A |
| 关联 AC | AC-2.3, AC-2.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | number | 是 | 24vp (BUBBLE_ITEM_RADIUS) | 同时设置 PopupBorderRadius（默认 28vp） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | popupItemBorderRadius(20) | Popup 字母项圆角 20vp + Popup 整体圆角 20vp | AC-2.3 |
| 2 | 不设置 | 字母项默认 24vp + 整体默认 28vp | AC-2.5, AC-2.10 |

---

**itemBorderRadius(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `itemBorderRadius(value: number): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 12) |
| 错误码 | N/A |
| 关联 AC | AC-2.4, AC-2.11 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | number | 是 | 8vp (INDEXER_ITEM_DEFAULT_RADIUS) | 同时设置 IndexerBorderRadius（默认 12vp）；API >= 12 生效 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | itemBorderRadius(4), API >= 12 | 索引项圆角 4vp + 索引条整体圆角 4vp | AC-2.4 |
| 2 | API < 12, 不设置 | 使用 theme hoverRadiusSize | AC-2.6 |

---

**popupBackgroundBlurStyle(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupBackgroundBlurStyle(value: BlurStyle): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 12) |
| 错误码 | N/A |
| 关联 AC | AC-2.7, AC-2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | BlurStyle | 是 | COMPONENT_REGULAR | 存 PaintProperty；SetByUser=true |

---

**popupTitleBackground(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `popupTitleBackground(value: ResourceColor): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 12) |
| 错误码 | N/A |
| 关联 AC | AC-2.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor | 是 | theme popupTitleBackground | 存 PaintProperty；SetByUser=true |

---

**onRequestPopupData(callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onRequestPopupData(callback: OnAlphabetIndexerRequestPopupDataCallback): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 8) |
| 错误码 | N/A |
| 关联 AC | AC-3.1~AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | `(index: number) => Array<string>` / `(index: int) => Array<string>` (static) | 否 | undefined | 回调返回 popup 子项数据 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 触摸索引项 + usingPopup=true | 回调触发，参数=选中索引 | AC-3.1 |
| 2 | 回调返回 ["A1","A2","A3"] | 显示 3 个子项 | AC-3.2 |
| 3 | 回调返回空数组 | 不显示子项列表 | AC-3.3 |
| 4 | 回调返回 > 5 项 | 截断为前 5 项（折叠态 3 项） | AC-3.5 |
| 5 | 索引项变更期间 popup 显示 | 新回调返回值更新 popup 内容 | AC-3.6 |

---

**onPopupSelect(callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onPopupSelect(callback: OnAlphabetIndexerPopupSelectCallback): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 8) |
| 错误码 | N/A |
| 关联 AC | AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | `(index: number) => void` / `(index: int) => void` (static) | 否 | undefined | index 为 popup 子项在数据数组中的下标 |

---

**selected(index)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `selected(index: number): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 8) |
| 错误码 | N/A |
| 关联 AC | AC-4.1, AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| index | number / int \| Bindable<int> (static) | 是 | 0 (from constructor) | 超出范围被钳位；不触发 onSelect |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 动态设置 selected(5) | 视觉选中第 5 项，onSelect 不触发 | AC-4.1 |
| 2 | selected >= arrayValue.length | 钳位到 length-1 | AC-4.5 |

---

**enableHapticFeedback(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableHapticFeedback(value: boolean): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 12) |
| 错误码 | N/A |
| 关联 AC | AC-4.2~AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | boolean | 是 | true | 存 LayoutProperty；PROPERTY_UPDATE_MEASURE |

## 兼容性声明

- **已有 API 行为变更:** 是 — API 12 多项默认值/行为变更（popupBackground 颜色变化、itemBorderRadius 从 theme→8vp、popup 折叠态最大 item 数 4→3）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7 (基础属性) / API 8 (popupPosition/onSelect/onRequestPopupData/onPopupSelect/selected) / API 10 (popupSelectedColor/popupUnselectedColor/popupItemBackgroundColor/popupItemFont) / API 11 (autoCollapse) / API 12 (popupItemBorderRadius/itemBorderRadius/popupBackgroundBlurStyle/popupTitleBackground/enableHapticFeedback/START/END)
- **API 版本号策略:** Dynamic @since 从 7~12 递增；Static @since 23；NDK Arc @since 26.1.0

### API 12 Popup 相关行为差异

| 差异项 | API < 12 | API >= 12 |
|--------|-----------|-----------|
| popupBackground 默认色 | 0xffffffff (纯白) | 0x66808080 (半透明灰) |
| popup 折叠态最大 item 数 | 4 (INDEXER_BUBBLE_MAXSIZE_COLLAPSED) | 3 (INDEXER_BUBBLE_MAXSIZE_COLLAPSED_API_TWELVE) |
| popup item 尺寸 | 无专门尺寸 | 48vp (BUBBLE_ITEM_SIZE) |
| popup 标题背景 | 无 popupTitleBackground 属性 | popupTitleBackground 属性可用 |
| popup 模糊 | 无 popupBackgroundBlurStyle 属性 | popupBackgroundBlurStyle 属性可用 |
| popupItemBorderRadius | 无 | 属性可用 |
| itemBorderRadius | 无（使用 theme hoverRadiusSize） | 属性可用（默认 8vp） |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Popup 样式存 PaintProperty | popupSelectedColor/popupUnselectedColor/popupItemBackground/popupBackground/popupTitleBackground/popupBackgroundBlurStyle 存 PaintProperty，触发 PROPERTY_UPDATE_RENDER | AC-1.3~AC-1.7, AC-2.7~AC-2.9 |
| Popup 圆角存 PaintProperty | popupItemBorderRadius/itemBorderRadius/PopupBorderRadius/IndexerBorderRadius 存 PaintProperty，触发 PROPERTY_UPDATE_MEASURE | AC-2.3, AC-2.4 |
| Popup 定位存 LayoutProperty | PopupPositionX/Y/PopupHorizontalSpace/IsPopup 存 LayoutProperty，触发 PROPERTY_UPDATE_LAYOUT | AC-2.1, AC-2.2 |
| popupItemFont dynamic 管线仅处理 size + weight | `indexer_model_ng.cpp` SetPopupItemFont 仅调用 SetFontSize + SetFontWeight | AC-1.9 |
| popupItemBorderRadius/itemBorderRadius 同时设置两个圆角 | `setPopupItemBorderRadius(value)` 同时设置 PopupBorderRadius 和 PopupItemBorderRadius；`setItemBorderRadius(value)` 同时设置 IndexerBorderRadius 和 ItemBorderRadius | AC-2.10, AC-2.11 |
| NDK C-API 仅 Arc 变体 | 线性 AlphabetIndexer 无 NDK 入口 | 不影响 ArkTS 属性规格 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Popup 显示延迟 < 2 帧 | 帧率监控 | ShowBubble 同步执行 |
| 功耗 | N/A | N/A | 静态组件 |
| 内存 | Popup 节点 < 1KB | 内存分析 | Popup 子树 FrameNode 数量固定 |
| 安全 | 无权限要求 | SDK 检查 | 无 ohos.permission |
| 可靠性 | onRequestPopupData 返回空数组不崩溃 | 单测 | R-24 |
| 可测试性 | Popup 属性可通过 Modifier 测试 | C-API 单测 | alphabet_indexer_modifier_test.cpp |
| 自动化维测 | Popup 属性可从 InspectorFilter 导出 | DevTools | ToJsonValue |
| 定界定位 | Popup 定位公式可从 LayoutAlgorithm 导出 | 日志 | GetPositionOfPopupNode |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 标准行为 | 标准测试 | 默认 |
| 平板 | Popup 默认位置可能偏大 | 可通过 popupPosition/popupHorizontalSpace 调整 | 可视化验证 | 无特殊逻辑 |
| 折叠屏 | 折叠态空间变化影响 Popup 定位 | LayoutAlgorithm 根据 indexerWidth 计算 Popup X 坐标 | 折叠/展开测试 | GetPositionOfPopupNode |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Popup 子项未提供独立 AccessibilityProperty；Popup 整体通过父节点 IsPopup 属性控制 | AC-1.1（popup 显示/隐藏） |
| 大字体 | 是 | popupFont/popupItemFont 可配置字体大小 | AC-1.8, AC-1.9 |
| 深色模式 | 是 | Popup 颜色属性通过 SetByUser 机制控制暗色覆盖；popupSelectedColor/popupUnselectedColor/popupItemBackground/popupTitleBackground 的 ByUser 在 LayoutProperty 中（popupColor 的 ByUser 也在 LayoutProperty） | AC-1.10 |
| 多窗口/分屏 | 是 | Popup 定位基于 indexerWidth 计算，窗口尺寸变化影响定位 | AC-2.2 |
| 多用户 | 否 | 无用户隔离逻辑 | N/A |
| 版本升级 | 是 | API 12 Popup 默认值/行为差异需兼容 | 兼容性声明 |
| 生态兼容 | 否 | 无第三方生态依赖 | N/A |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [ ] 范围边界明确（做什么/不做什么清晰）
- [ ] 无语义模糊表述（"快速""稳定""尽可能"等）
- [ ] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [ ] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "AlphabetIndexer Popup 弹出面板样式属性（popupColor/popupBackground/popupSelectedColor/popupUnselectedColor/popupItemBackgroundColor/popupFont/popupItemFont）、Popup 定位算法（GetPositionOfPopupNode/IsPopupAtLeft）、Popup 圆角/模糊/标题背景、Popup 交互事件（onRequestPopupData/onPopupSelect）、selected 属性、enableHapticFeedback 触觉反馈、API 12 行为差异"
```

**关键文档:** `interface/sdk-js/api/@internal/component/ets/alphabet_indexer.d.ts`, `frameworks/core/components_ng/pattern/indexer/indexer_pattern.cpp`, `frameworks/core/components_ng/pattern/indexer/indexer_paint_property.h`, `frameworks/core/components_ng/pattern/indexer/indexer_layout_algorithm.cpp`, `frameworks/core/components_ng/pattern/indexer/indexer_theme.h`
