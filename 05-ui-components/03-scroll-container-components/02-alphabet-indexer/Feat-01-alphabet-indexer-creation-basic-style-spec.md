# 特性规格

## 概述

| 特性名称 | 特性编号 | 所属 Epic | 优先级 | 目标版本 | SIG 归属 | 状态 | 复杂度 |
|----------|----------|-----------|--------|----------|----------|------|--------|
| AlphabetIndexer 创建与基础样式 | Feat-01 | 无 | P1 | API 7 ~ 12+ | ArkUI SIG | Baselined（已有实现补录） | 标准 |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/02-alphabet-indexer/design.md` |
| SDK Dynamic | `interface/sdk-js/api/@internal/component/ets/alphabet_indexer.d.ts` |
| SDK Static | `interface/sdk-js/api/arkui/component/alphabetIndexer.static.d.ets` |
| SDK Modifier | `interface/sdk-js/api/arkui/AlphabetIndexerModifier.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/indexer/indexer_pattern.cpp` |
| LayoutProperty | `frameworks/core/components_ng/pattern/indexer/indexer_layout_property.h` |
| Theme | `frameworks/core/components_ng/pattern/indexer/indexer_theme.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 创建索引条

作为**应用开发者**，我想要**通过 arrayValue 和 selected 参数创建 AlphabetIndexer 组件**，以便**为长列表提供字母索引导航**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 传入 arrayValue=["A","B","C"] 且 selected=0 THEN 组件创建成功，第 0 项（"A"）为选中状态 | 正常 |
| AC-1.2 | WHEN 传入 arrayValue 为空数组 THEN 组件创建成功，不显示任何索引项 | 边界 |
| AC-1.3 | WHEN 传入 selected 超出 arrayValue 长度 THEN selected 被钳位到最大有效索引 | 边界 |
| AC-1.4 | WHEN 传入 selected 为负数 THEN selected 被钳位到 0 | 边界 |
| AC-1.5 | WHEN 动态更新 arrayValue（增加/减少项）THEN 索引条重新构建并根据 autoCollapse 规则重新折叠 | 正常 |

### US-2: 配置索引条外观

作为**应用开发者**，我想要**配置索引条的文本颜色、选中颜色、背景色、字体和尺寸**，以便**匹配应用设计风格**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 color(#FF0000) THEN 未选中项文本颜色变为红色 | 正常 |
| AC-2.2 | WHEN 设置 selectedColor(#00FF00) THEN 选中项文本颜色变为绿色 | 正常 |
| AC-2.3 | WHEN 设置 selectedBackgroundColor(#0000FF) THEN 选中项背景色变为蓝色 | 正常 |
| AC-2.4 | WHEN 设置 font({size:12, weight:FontWeight.Bold}) THEN 未选中项字体变为 12fp 加粗 | 正常 |
| AC-2.5 | WHEN 设置 selectedFont({size:14, weight:FontWeight.Normal}) THEN 选中项字体变为 14fp 正常粗细 | 正常 |
| AC-2.6 | WHEN 设置 itemSize(24) THEN 每个索引项尺寸变为 24vp | 正常 |
| AC-2.7 | WHEN 不设置任何颜色属性 THEN 使用主题默认值（color=0x99182431, selectedColor=0xff007dff, selectedBackgroundColor=0x33007dff） | 正常 |
| AC-2.8 | WHEN 设置颜色属性后再切换暗色模式 THEN SetByUser=true 的属性保留用户值；SetByUser=false 的属性使用暗色主题新值 | 正常 |

### US-3: 配置对齐与折叠

作为**应用开发者**，我想要**配置索引条的 Popup 对齐方向和自动折叠策略**，以便**在不同布局和 RTL 环境下正确显示**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 alignStyle(IndexerAlign.END) THEN LTR 环境下 Popup 在右侧，RTL 环境下在左侧 | 正常 |
| AC-3.2 | WHEN 设置 alignStyle(IndexerAlign.START) THEN LTR 环境下 Popup 在左侧，RTL 环境下在右侧 | 正常 |
| AC-3.3 | WHEN 设置 alignStyle(IndexerAlign.LEFT) THEN Popup 固定在左侧，不受 RTL 影响 | 正常 |
| AC-3.4 | WHEN 设置 alignStyle(IndexerAlign.RIGHT) THEN Popup 固定在右侧，不受 RTL 影响 | 正常 |
| AC-3.5 | WHEN 设置 alignStyle(IndexerAlign.END, offset=8vp) THEN Popup 位置附加 8vp 水平偏移量 | 正常 |
| AC-3.6 | WHEN 设置 autoCollapse(true) 且数组长度 > 13 THEN 索引条使用 7+1 折叠模式（6 组 + 星号首项） | 正常 |
| AC-3.7 | WHEN 设置 autoCollapse(true) 且数组长度 10~13 THEN 索引条使用 5+1 折叠模式（4 组） | 正常 |
| AC-3.8 | WHEN 设置 autoCollapse(true) 且数组长度 ≤ 9 THEN 索引条不折叠（NONE 模式），全部显示 | 正常 |
| AC-3.9 | WHEN 设置 autoCollapse(false) THEN 索引条显示全部项，不折叠 | 正常 |
| AC-3.10 | WHEN 触摸折叠组首项（圆点）THEN collapsedIndex_ 设为 0，选中组内第一项 | 正常 |
| AC-3.11 | WHEN 在折叠组内滑动 THEN collapsedIndex_ 根据滑动偏移量计算组内子索引 | 正常 |

### US-4: 索引选择交互

作为**应用开发者**，我想要**通过 onSelect 回调接收用户选择索引的通知**，以便**联动外部列表滚动到对应位置**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 用户触摸某索引项 THEN onSelect 回调触发，参数为该项索引 | 正常 |
| AC-4.2 | WHEN 用户滑动跨越多个索引项 THEN onSelect 连续触发，每次参数为当前项索引 | 正常 |
| AC-4.3 | WHEN selected 属性被动态更新 THEN onSelect 不触发（仅视觉更新） | 正常 |
| AC-4.4 | WHEN 调用 onSelected（已废弃 since 8）THEN 行为与 onSelect 一致（源码层共享同一 native 路径） | 正常 |
| AC-4.5 | WHEN 同时设置 onSelected 和 onSelect THEN 后设置的回调生效（两者最终写入同一 EventHub 字段） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1, R-2 | TASK-01 | 单测 + 可视化 | IndexerModelNG::Create |
| AC-1.2 | R-3 | TASK-01 | 单测 | BuildArrayValueItems 空数组 |
| AC-1.3 | R-4 | TASK-01 | 单测 | selected 钳位 |
| AC-1.4 | R-5 | TASK-01 | 单测 | selected 钳位 |
| AC-1.5 | R-6 | TASK-01 | 单测 | InitArrayValue |
| AC-2.1 | R-7 | TASK-01 | 单测 + 可视化 | SetColor |
| AC-2.2 | R-8 | TASK-01 | 单测 + 可视化 | SetSelectedColor |
| AC-2.3 | R-9 | TASK-01 | 单测 + 可视化 | SetSelectedBackgroundColor |
| AC-2.4 | R-10 | TASK-01 | 单测 + 可视化 | SetFont |
| AC-2.5 | R-11 | TASK-01 | 单测 + 可视化 | SetSelectedFont |
| AC-2.6 | R-12 | TASK-01 | 单测 + 可视化 | SetItemSize |
| AC-2.7 | R-13 | TASK-01 | 可视化 + Theme 检查 | 默认值 |
| AC-2.8 | R-14, R-15 | TASK-01 | 暗色模式切换测试 | SetByUser 机制 |
| AC-3.1 | R-16 | TASK-01 | RTL 测试 | IsPopupAtLeft |
| AC-3.2 | R-17 | TASK-01 | RTL 测试 | IsPopupAtLeft |
| AC-3.3 | R-18 | TASK-01 | 测试 | IsPopupAtLeft |
| AC-3.4 | R-19 | TASK-01 | 测试 | IsPopupAtLeft |
| AC-3.5 | R-20 | TASK-01 | 测试 | offset 参数 |
| AC-3.6 | R-21 | TASK-01 | 测试 + 可视化 | 7+1 模式 |
| AC-3.7 | R-22 | TASK-01 | 测试 + 可视化 | 5+1 模式 |
| AC-3.8 | R-23 | TASK-01 | 测试 + 可视化 | NONE 模式 |
| AC-3.9 | R-24 | TASK-01 | 测试 | autoCollapse=false |
| AC-3.10 | R-25 | TASK-01 | 测试 | collapsedIndex_ |
| AC-3.11 | R-26 | TASK-01 | 测试 | collapsedIndex_ 滑动 |
| AC-4.1 | R-27 | TASK-01 | 事件回调测试 | FireOnSelect |
| AC-4.2 | R-28 | TASK-01 | 事件回调测试 | MoveIndexByOffset |
| AC-4.3 | R-29 | TASK-01 | 测试 | selected 属性更新 |
| AC-4.4 | R-30 | TASK-01 | 测试 + spec 注明偏差 | onSelected vs onSelect |
| AC-4.5 | R-31 | TASK-01 | 测试 | 同时设置 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 传入 arrayValue 和 selected 创建 AlphabetIndexer | 创建 FrameNode，写入 LayoutProperty | arrayValue 不能为 null（SDK 无 optional） | AC-1.1 |
| R-2 | 行为 | 传入 selected=0 且 arrayValue=["A","B","C"] | 初始选中项为索引 0（"A"） | selected 默认值 0 | AC-1.1 |
| R-3 | 边界 | 传入 arrayValue=[]（空数组） | 组件创建成功，itemCount_=0，不显示索引项 | 空数组不触发崩溃 | AC-1.2 |
| R-4 | 边界 | 传入 selected >= arrayValue.length | selected 被钳位到 arrayValue.length-1 | 若 arrayValue 为空则 selected=0 | AC-1.3 |
| R-5 | 边界 | 传入 selected < 0 | selected 被钳位到 0 | Pattern 内 `max(0, min(selected, itemCount-1))` | AC-1.4 |
| R-6 | 行为 | 动态更新 arrayValue（SetArrayValue） | 触发 InitArrayValue → BuildArrayValueItems → 根据 autoCollapse 重建折叠 | PROPERTY_UPDATE_MEASURE 触发重布局 | AC-1.5 |
| R-7 | 行为 | 设置 color(value) | 未选中项文本颜色设为 value，SetByUser=true | value 支持 ResourceColor (Color/string/Resource)；默认 0x99182431 | AC-2.1 |
| R-8 | 行为 | 设置 selectedColor(value) | 选中项文本颜色设为 value，SetByUser=true | 默认 0xff007dff (API<12) / 0xff254ff7 | AC-2.2 |
| R-9 | 行为 | 设置 selectedBackgroundColor(value) | 选中项背景色设为 value，SetByUser=true | 默认 0x33007dff (opacity 0.1) | AC-2.3 |
| R-10 | 行为 | 设置 font({size, weight, family, style}) | 未选中项字体更新 | 仅影响未选中项；selectedFont 独立 | AC-2.4 |
| R-11 | 行为 | 设置 selectedFont({size, weight, family, style}) | 选中项字体更新 | 仅影响选中项 | AC-2.5 |
| R-12 | 行为 | 设置 itemSize(value) | 索引项尺寸设为 value vp | 默认 16vp；PROPERTY_UPDATE_MEASURE；itemSize=0 时无法正常显示 | AC-2.6 |
| R-13 | 行为 | 不设置颜色/字体属性 | 使用 IndexerTheme 默认值 | color=0x99182431, selectedColor=0xff007dff, selectedBackgroundColor=0x33007dff | AC-2.7 |
| R-14 | 行为 | 暗色模式切换 + SetByUser=true 的属性 | 保留用户设置值，不被暗色主题覆盖 | 仅 LayoutProperty 内 10 个颜色属性有 ByUser 机制 | AC-2.8 |
| R-15 | 行为 | 暗色模式切换 + SetByUser=false 的属性 | 使用暗色主题新默认值 | OnColorConfigurationUpdate() 读取 theme 新值 | AC-2.8 |
| R-16 | 行为 | alignStyle=END + LTR | Popup 在索引条右侧 | 默认对齐；offset=undefined 时 popupPosition 使用默认值 | AC-3.1 |
| R-17 | 行为 | alignStyle=START + LTR | Popup 在索引条左侧 | START/END since API 12 | AC-3.2 |
| R-18 | 行为 | alignStyle=LEFT | Popup 固定在左侧，不受 RTL 影响 | LEFT/RIGHT since API 7 | AC-3.3 |
| R-19 | 行为 | alignStyle=RIGHT | Popup 固定在右侧，不受 RTL 影响 | LEFT/RIGHT since API 7 | AC-3.4 |
| R-20 | 行为 | alignStyle(value, offset) | Popup 定位附加 offset 水平偏移 | offset since API 10；写入 PopupHorizontalSpace | AC-3.5 |
| R-21 | 行为 | autoCollapse=true + fullArraySize > 13 + 空间充足 | 7+1 模式：6 组 + 星号/井号 | ApplySevenPlusOneMode | AC-3.6 |
| R-22 | 行为 | autoCollapse=true + fullArraySize 10~13 或空间不足 | 5+1 模式：4 组 | ApplyFivePlusOneMode | AC-3.7 |
| R-23 | 行为 | autoCollapse=true + fullArraySize ≤ 9 | NONE 模式：全显示 | INDEXER_NINE_CHARACTERS_CHECK=9 | AC-3.8 |
| R-24 | 行为 | autoCollapse=false | 显示全部项，不折叠 | arrayValue_ = fullArrayValue_ | AC-3.9 |
| R-25 | 行为 | 触摸折叠组圆点项 | collapsedIndex_ = 0，选中组内第一项 | FireOnSelect(baseIndex + 0) | AC-3.10 |
| R-26 | 行为 | 滑动进入折叠组 | collapsedIndex_ = floor(yOffset / itemHeight_in_group) | 每组内 itemHeight = itemHeight_ / collapsedItemNums_[groupIndex] | AC-3.11 |
| R-27 | 行为 | 触摸某索引项 | onSelect 回调触发，参数=该项在 ActualArrayValue 中的索引 | fromPress=true 时 collapsedIndex_ 重置为 0 | AC-4.1 |
| R-28 | 行为 | 滑动跨越多个索引项 | onSelect 连续触发，每项触发一次 | MoveIndexByOffset 遍历 | AC-4.2 |
| R-29 | 行为 | 动态更新 selected 属性 | 视觉选中状态更新，onSelect 不触发 | SetSelected 写入 LayoutProperty | AC-4.3 |
| R-30 | 行为 | 调用 onSelected（deprecated since 8） | 行为与 onSelect 完全一致 | 源码: AlphabetIndexerBridge::SetOnSelected → setOnIndexerSelect → SetOnSelected（与 SetOnSelect 同路径） | AC-4.4 |
| R-31 | 边界 | 同时设置 onSelected 和 onSelect | 后设置的回调生效，覆盖前一个 | EventHub.onSelectedEvent_ 是单回调字段，不支持多回调 | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 ~ R-5 | 单元测试 | 构造参数钳位与空数组处理 |
| VM-2 | R-6 | 单元测试 + 可视化 | 动态更新 arrayValue 重建折叠 |
| VM-3 | R-7 ~ R-12 | 单元测试 + 可视化 | 颜色/字体/itemSize 设置与默认值 |
| VM-4 | R-13 | 主题检查 | 不设置属性时的默认值验证 |
| VM-5 | R-14 ~ R-15 | 暗色模式切换测试 | SetByUser 机制在暗色模式下的行为 |
| VM-6 | R-16 ~ R-20 | RTL 测试 | Popup 方向 + offset 偏移 |
| VM-7 | R-21 ~ R-26 | 可视化 + 单元测试 | 折叠模式选择 + collapsedIndex_ |
| VM-8 | R-27 ~ R-31 | 事件回调测试 | onSelect/onSelected 触发时机与参数 |

## API 变更分析

### 新增 API

> 已有实现补录，无新增 API。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| onSelected(callback) | 废弃（since 8） | 旧代码使用 onSelected | 替换为 onSelect；源码层两者行为一致 | AC-4.4, AC-4.5 |

## 接口规格

### 接口定义

**AlphabetIndexer(options)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `AlphabetIndexer(options: AlphabetIndexerOptions): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` — 索引条属性修饰器 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options.arrayValue | `Array<string>` | 是 | N/A | 空数组合法（无索引项显示） |
| options.selected | `number` / `int \| Bindable<int>` | 是 | N/A | 超出范围被钳位到有效索引 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常传入 arrayValue=["A".."Z"], selected=0 | 创建成功，初始选中 "A" | AC-1.1 |
| 2 | arrayValue=[], selected=0 | 创建成功，无索引项 | AC-1.2 |
| 3 | selected > arrayValue.length-1 | selected 钳位到 length-1 | AC-1.3 |
| 4 | selected < 0 | selected 钳位到 0 | AC-1.4 |

---

**color(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `color(value: ResourceColor): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor (Color/string/Resource) | 是 | 0x99182431 | 设置后 SetByUser=true；支持 undefined（static API） |

---

**selectedColor(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `selectedColor(value: ResourceColor): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7) |
| 错误码 | N/A |
| 关联 AC | AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor | 是 | 0xff007dff | SetByUser=true |

---

**selectedBackgroundColor(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `selectedBackgroundColor(value: ResourceColor): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7) |
| 错误码 | N/A |
| 关联 AC | AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor | 是 | 0x33007dff (opacity 0.1) | SetByUser=true |

---

**font(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `font(value: Font): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7) |
| 错误码 | N/A |
| 关联 AC | AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value.size | number \| Resource | 否 | theme default | fontSize |
| value.weight | FontWeight \| number \| string | 否 | FontWeight.Normal | 字体粗细 |
| value.family | string \| Resource | 否 | theme default | 字体族 |
| value.style | FontStyle | 否 | FontStyle.Normal | 字体风格 |

---

**selectedFont(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `selectedFont(value: Font): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7) |
| 错误码 | N/A |
| 关联 AC | AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value.size | number \| Resource | 否 | theme select text size | 选中项字体大小 |
| value.weight | FontWeight \| number \| string | 否 | FontWeight.Medium | 选中项字体粗细 |
| value.family | string \| Resource | 否 | theme default | 选中项字体族 |
| value.style | FontStyle | 否 | FontStyle.Normal | 选中项字体风格 |

---

**itemSize(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `itemSize(value: string \| number): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7) |
| 错误码 | N/A |
| 关联 AC | AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | string \| number \| double (static) | 是 | 16vp | value=0 时索引条不可见；PROPERTY_UPDATE_MEASURE |

---

**alignStyle(value, offset?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `alignStyle(value: IndexerAlign, offset?: Length): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 7, offset since 10) |
| 错误码 | N/A |
| 关联 AC | AC-3.1~AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | IndexerAlign (Left/Right/START/END) | 是 | END | START/END since API 12 |
| offset | Length | 否 | undefined | 写入 PopupHorizontalSpace |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | alignStyle=END, LTR | Popup 在右侧 | AC-3.1 |
| 2 | alignStyle=END, RTL | Popup 在左侧 | AC-3.1 |
| 3 | alignStyle=START, LTR | Popup 在左侧 | AC-3.2 |
| 4 | alignStyle=START, RTL | Popup 在右侧 | AC-3.2 |
| 5 | alignStyle=LEFT | Popup 固定左侧，不受 RTL | AC-3.3 |
| 6 | alignStyle=RIGHT | Popup 固定右侧，不受 RTL | AC-3.4 |
| 7 | alignStyle=END, offset=8vp | Popup 位置附加 8vp 偏移 | AC-3.5 |

---

**autoCollapse(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `autoCollapse(value: boolean): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 11) |
| 错误码 | N/A |
| 关联 AC | AC-3.6~AC-3.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | boolean | 是 | true | false 时显示全部项 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | autoCollapse=true, arraySize > 13, 空间充足 | 7+1 模式 | AC-3.6 |
| 2 | autoCollapse=true, arraySize 10~13 | 5+1 模式 | AC-3.7 |
| 3 | autoCollapse=true, arraySize ≤ 9 | NONE 模式 | AC-3.8 |
| 4 | autoCollapse=false | 全部显示 | AC-3.9 |

---

**onSelect(callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onSelect(callback: OnAlphabetIndexerSelectCallback): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (since 8) |
| 错误码 | N/A |
| 关联 AC | AC-4.1~AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | `(index: number) => void` / `(index: int) => void` (static) | 否 | undefined | 与 onSelected 共享 EventHub 字段 |

---

**onSelected(callback)** (deprecated since 8)

| 属性 | 值 |
|------|-----|
| 函数签名 | `onSelected(callback: (index: number) => void): AlphabetIndexerAttribute` |
| 返回值 | `AlphabetIndexerAttribute` |
| 开放范围 | Public (deprecated since 8, replaced by onSelect) |
| 错误码 | N/A |
| 关联 AC | AC-4.4, AC-4.5 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 单独调用 onSelected | 行为与 onSelect 完全一致 | AC-4.4 |
| 2 | 同时设置 onSelected + onSelect | 后设置者生效，覆盖前者 | AC-4.5 |

## 兼容性声明

- **已有 API 行为变更:** 是 — API 12 多项默认值/行为变更（详见"API 12 行为差异"章节）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** Dynamic API @since 标注从 7 开始；Static API @since 23；NDK Arc 变体 @since 26.1.0

### API 12 行为差异

| 差异项 | API < 12 | API >= 12 |
|--------|-----------|-----------|
| 垂直 padding | 2vp (INDEXER_PADDING_TOP) | 4vp (INDEXER_PADDING_TOP_API_TWELVE) |
| 选中项圆角 | theme hoverRadiusSize | itemBorderRadius 默认 8vp |
| 正常态圆角 | 0 | 8vp (INDEXER_ITEM_DEFAULT_RADIUS) |
| Popup 背景 | 0xffffffff (纯白) | 0x66808080 (半透明灰) |
| Popup 折叠态最大 item 数 | 4 | 3 |
| START/END 对齐 | 不支持 | 支持 (IndexerAlign.START/END) |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 属性存储分层 | 基础样式存 LayoutProperty（NORMAL/MEASURE dirty flag），Popup 样式存 PaintProperty（RENDER dirty flag） | 全部 AC |
| SetByUser 机制仅覆盖 LayoutProperty 内 10 个颜色属性 | PaintProperty 内 popupSelectedColor/popupUnselectedColor/popupItemBackground/popupTitleBackground 无 SetByUser | AC-2.8 |
| onSelected/onSelect 共享 EventHub 单回调字段 | 后设置覆盖前设置，不支持多回调 | AC-4.5 |
| NDK C-API 仅 Arc 变体 | 线性 AlphabetIndexer 无 NDK 入口 | 不影响 ArkTS 属性规格 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | onSelect 回调延迟 < 1 帧 | 帧率监控 | IndexerPattern::FireOnSelect 同步回调 |
| 功耗 | N/A | N/A | 静态组件，无持续功耗 |
| 内存 | 索引条内存 < 2KB/100项 | 内存分析 | LayoutProperty 存储 vector<string> |
| 安全 | 无权限要求 | SDK 检查 | 无 ohos.permission |
| 可靠性 | 空数组/负索引不崩溃 | 单测 | R-3, R-5 |
| 可测试性 | 全部属性可通过 Modifier 测试 | C-API 单测 | alphabet_indexer_modifier_test.cpp |
| 自动化维测 | DumpInfo 支持属性导出 | hilog | IndexerPattern::DumpInfo |
| 定界定位 | 属性名可从 InspectorFilter 导出 | DevTools | ToJsonValue |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 标准行为 | 标准测试 | 默认 |
| 平板 | itemSize 默认 16vp 可能偏小 | 建议增大 itemSize | 可视化验证 | 无特殊逻辑 |
| 折叠屏 | 折叠态可用高度变化触发折叠模式重算 | StartCollapseDelayTask 1ms 后重布局 | 折叠/展开测试 | OnDirtyLayoutWrapperSwap |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | AccessibilityProperty 提供 GetCollectionItemCounts/GetCurrentIndex/GetText；ScrollForward/ScrollBackward 动作支持 | AC-4.1（选中变化触发无障碍事件） |
| 大字体 | 是 | font/selectedFont 可配置字体大小；默认值来自 theme | AC-2.4, AC-2.5 |
| 深色模式 | 是 | SetByUser 机制控制颜色属性在暗色模式下的覆盖策略 | AC-2.8 |
| 多窗口/分屏 | 是 | 可用高度变化触发折叠模式重算 | AC-3.6~AC-3.9 |
| 多用户 | 否 | 无用户隔离逻辑 | N/A |
| 版本升级 | 是 | API 12 行为差异需兼容 | 兼容性声明 |
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
    query: "AlphabetIndexer IndexerPattern 属性存储分层、AutoCollapse 折叠算法、SetByUser 机制、Popup 对齐与 RTL、API 12 行为差异、onSelected/onSelect 废弃处理、NDK C-API Arc 变体"
```

**关键文档:** `interface/sdk-js/api/@internal/component/ets/alphabet_indexer.d.ts`, `frameworks/core/components_ng/pattern/indexer/indexer_pattern.cpp`, `frameworks/core/components_ng/pattern/indexer/indexer_layout_property.h`, `frameworks/core/components_ng/pattern/indexer/indexer_theme.h`
