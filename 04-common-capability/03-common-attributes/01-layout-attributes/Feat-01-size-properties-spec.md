# 特性规格

> Func-04-03-01-Feat-01 尺寸属性：固化 width/height/size/constraintSize/padding/margin 六个核心尺寸属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 尺寸属性 (Size Properties) |
| 特性编号 | Func-04-03-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 12/15 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/01-layout-attributes/design.md` | Baselined |

---

## 用户故事

### US-1: 设置组件固定宽高

**作为** 应用开发者,
**我想要** 通过 .width() 和 .height() 设置组件的固定宽高,
**以便** 精确控制组件在页面中的布局尺寸。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.width(value: Length)` 设置宽度 THEN 组件渲染宽度等于 value 转换为像素后的值（受 constraintSize 约束） | 边界 |
| AC-1.2 | WHEN 调用 `.height(value: Length)` 设置高度 THEN 组件渲染高度等于 value 转换为像素后的值（受 constraintSize 约束） | 边界 |
| AC-1.3 | WHEN value 为 number 类型 THEN 默认单位为 vp | 正常 |
| AC-1.4 | WHEN value 为 string 类型（如 '100px'、'50%'、'calc(100vp - 20px)'）THEN 按对应单位解析 | 正常 |
| AC-1.5 | WHEN value 为 Resource 类型 THEN 从资源文件解析为对应长度值 | 正常 |
| AC-1.6 | WHEN value 为 undefined THEN 重置为默认尺寸（MATCH_CONTENT），等效于未设置 | 异常 |
| AC-1.7 | WHEN value 为负数且 API ≥ 12 THEN 重置为默认尺寸（等同 undefined 行为） | 异常 |
| AC-1.8 | WHEN value 为负数且 API < 12 THEN 值被 Clamp 到 0 | 异常 |
| AC-1.9 | WHEN value 为 0 THEN 组件宽度/高度为 0，组件不可见但存在于布局树中 | 正常 |

### US-2: 通过 size 同时设置宽高

**作为** 应用开发者,
**我想要** 通过 `.size({width, height})` 一次性设置宽高,
**以便** 减少代码量。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.size({width: w, height: h})` THEN 等效于同时调用 `.width(w).height(h)` | 正常 |
| AC-2.2 | WHEN SizeOptions 中仅设置 width 而 height 为 undefined THEN 设置宽度，同时高度被清除（ClearWidthOrHeight）回退到默认行为（因 JsSize 内部对缺失字段调用 JsHeight(undefined) 触发清除逻辑） | 异常 |
| AC-2.3 | WHEN SizeOptions 中仅设置 height 而 width 为 undefined THEN 设置高度，同时宽度被清除（ClearWidthOrHeight）回退到默认行为（因 JsSize 内部对缺失字段调用 JsWidth(undefined) 触发清除逻辑） | 异常 |

### US-3: 设置尺寸约束范围

**作为** 应用开发者,
**我想要** 通过 `.constraintSize()` 设置组件的最小/最大宽高约束,
**以便** 在响应式布局中限制组件尺寸范围。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `constraintSize({minWidth, maxWidth, minHeight, maxHeight})` THEN 组件最终渲染尺寸被约束在 [min, max] 范围内 | 边界 |
| AC-3.2 | WHEN 同时设置 width(100) 和 constraintSize({maxWidth: 50}) THEN 最终宽度为 50（selfIdealSize 被 Clamp 到 maxWidth） | 边界 |
| AC-3.3 | WHEN 同时设置 width(20) 和 constraintSize({minWidth: 50}) THEN 最终宽度为 50（selfIdealSize 被 Clamp 到 minWidth） | 边界 |
| AC-3.4 | WHEN constraintSize 中 minWidth > maxWidth THEN 以 minWidth 为准（min 优先于 max） | 边界 |
| AC-3.5 | WHEN constraintSize 各字段为 undefined THEN 对应维度不设约束（使用父节点传递的约束） | 异常 |
| AC-3.6 | WHEN 调用 constraintSize(undefined) THEN 重置所有约束 | 异常 |

### US-4: 设置组件内边距

**作为** 应用开发者,
**我想要** 通过 `.padding()` 设置组件的内边距,
**以便** 控制内容与组件边框之间的间距。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.padding(value: Length)` THEN 四个方向均设置为 value | 正常 |
| AC-4.2 | WHEN 调用 `.padding({top, right, bottom, left})` THEN 分别设置四个方向的内边距 | 正常 |
| AC-4.3 | WHEN 调用 `.padding(value: LocalizedPadding)` (API 12+) THEN 使用 start/end 替代 left/right，支持 RTL 布局 | 正常 |
| AC-4.4 | WHEN padding 设置后，组件无显式 width/height THEN 组件内容区缩小，总尺寸由内容+padding 决定（MATCH_CONTENT 模式） | 正常 |
| AC-4.5 | WHEN padding 设置后，组件有显式 width THEN 内容区 = width - paddingLeft - paddingRight（border-box 模型） | 正常 |
| AC-4.6 | WHEN padding + border > 显式 width THEN 组件 selfIdealSize 自动扩展到 padding + border 之和（CheckBorderAndPadding） | 边界 |
| AC-4.7 | WHEN padding 值为负数 THEN 值被 Clamp 到 0 | 异常 |
| AC-4.8 | WHEN padding 值为 undefined 或部分方向缺失 THEN 非 Localized 路径（top/right/bottom/left）执行全量替换——未传方向被清除为无值（nullopt）；Localized 路径（start/end）仅更新已传方向，未传方向保留原值 | 异常 |

### US-5: 设置组件外边距

**作为** 应用开发者,
**我想要** 通过 `.margin()` 设置组件的外边距,
**以便** 控制组件与其他组件之间的间距。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.margin(value: Length)` THEN 四个方向均设置为 value | 正常 |
| AC-5.2 | WHEN 调用 `.margin({top, right, bottom, left})` THEN 分别设置四个方向的外边距 | 正常 |
| AC-5.3 | WHEN 调用 `.margin(value: LocalizedMargin)` (API 12+) THEN 使用 start/end 替代 left/right，支持 RTL 布局 | 正常 |
| AC-5.4 | WHEN margin 设置后 THEN 父级传递给本节点的约束 maxSize 扣除 margin 后再传递 | 边界 |
| AC-5.5 | WHEN margin 设置后 THEN 父级传递给本节点的 percentReference 扣除 margin 后再传递 | 正常 |
| AC-5.6 | WHEN margin 为百分比 THEN 百分比参照父节点对应轴的 percentReference | 正常 |
| AC-5.7 | WHEN margin 值为负数 THEN 允许负值（负 margin 是合法的，组件向对应方向偏移） | 异常 |
| AC-5.8 | WHEN margin 值为 undefined 或部分方向缺失 THEN 非 Localized 路径（top/right/bottom/left）执行全量替换——未传方向被清除为无值（nullopt）；Localized 路径（start/end）仅更新已传方向，未传方向保留原值 | 异常 |

### US-6: 百分比尺寸

**作为** 应用开发者,
**我想要** 通过百分比设置组件尺寸（如 `.width('50%')`）,
**以便** 实现相对于父组件的响应式布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `.width('50%')` THEN 宽度 = 父节点 contentConstraint 的 percentReference.width × 0.5 | 正常 |
| AC-6.2 | WHEN 父节点未设置显式宽度且非 MATCH_PARENT THEN percentReference.width 可能为 0，子组件百分比宽度结果为 0 | 异常 |
| AC-6.3 | WHEN 父节点设置了 padding THEN percentReference 基于父节点 contentConstraint（已扣除 padding 和 border） | 正常 |
| AC-6.4 | WHEN 父节点设置了 margin（用于本节点）THEN percentReference 在 UpdateLayoutConstraint 中已扣除 margin | 正常 |

### US-7: calc() 表达式

**作为** 应用开发者,
**我想要** 通过 calc() 表达式设置尺寸（如 `.width('calc(100% - 20vp)')`）,
**以便** 在一个表达式中混合百分比和固定值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 使用 calc() 表达式 THEN 支持 +、-、*、/ 四则运算 | 正常 |
| AC-7.2 | WHEN 表达式混合单位（如 `calc(100vp - 20px)`）THEN 各部分按各自单位转换为 px 后计算 | 正常 |
| AC-7.3 | WHEN 表达式包含百分比（如 `calc(100% - 20vp)`）THEN 百分比部分使用 percentReference 转换 | 正常 |
| AC-7.4 | WHEN calc() 计算结果为负数 THEN NormalizeToPx 返回 false（值无效），该维度按未设置处理 | 异常 |

### US-8: LayoutPolicy (API 15+)

**作为** 应用开发者,
**我想要** 通过 LayoutPolicy 控制组件的尺寸策略,
**以便** 明确组件应匹配父容器还是包裹内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN `.width(LayoutPolicy.matchParent)` THEN 组件宽度匹配父容器可用宽度 | 正常 |
| AC-8.2 | WHEN `.width(LayoutPolicy.wrapContent)` THEN 组件宽度包裹内容（MATCH_CONTENT） | 正常 |
| AC-8.3 | WHEN `.width(LayoutPolicy.fixAtIdealSize)` THEN 解除 maxSize 限制，组件按 selfIdealSize 渲染（若有） | 边界 |
| AC-8.4 | WHEN 同时设置 `.width(100)` 后再设置 `.width(LayoutPolicy.matchParent)` THEN LayoutPolicy 生效，数值尺寸被清除 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.9 | R-1, R-2, R-7~R-10, R-25~R-27 | 已有实现 | 单测/XTS | `test/unittest/core/layout/` |
| AC-2.1~2.3 | R-11 | 已有实现 | 单测 | 同上 |
| AC-3.1~3.6 | R-3, R-12~R-14 | 已有实现 | 单测 | 同上 |
| AC-4.1~4.8 | R-4, R-15~R-18, R-28 | 已有实现 | 单测 | 同上 |
| AC-5.1~5.8 | R-5, R-19~R-21 | 已有实现 | 单测 | 同上 |
| AC-6.1~6.4 | R-6, R-22 | 已有实现 | 单测 | 同上 |
| AC-7.1~7.4 | R-23 | 已有实现 | 单测 | 同上 |
| AC-8.1~8.4 | R-24 | 已有实现 | 单测 | 同上 |
| AC-1.1, AC-1.2, AC-1.3, AC-1.9 | R-1, R-2, R-7~R-10 | SpecTest 回填用例 | HostPreview | 见 SpecTest用例追溯 表格 |
| AC-3.2, AC-3.3 | R-3, R-12~R-14 | SpecTest 回填用例 | HostPreview | 见 SpecTest用例追溯 表格 |
| AC-4.1, AC-4.5 | R-4, R-15~R-18 | SpecTest 回填用例 | HostPreview | 见 SpecTest用例追溯 表格 |
| AC-6.1 | R-6, R-22 | SpecTest 回填用例 | HostPreview | 见 SpecTest用例追溯 表格 |

### SpecTest 用例追溯

| Case ID | 对应 AC |
|---------|---------|
| case-001-width-height-basic | AC-1.1, AC-1.2, AC-1.3 |
| case-002-width-height-basic | AC-1.1, AC-1.2, AC-1.3 |
| case-003-width-height-zero | AC-1.9 |
| case-004-click-update-size | AC-1.1, AC-1.2 |
| case-001-constraint-max-width | AC-3.2 |
| case-002-constraint-min-width | AC-3.3 |
| case-003-padding-basic | AC-4.1, AC-4.5 |
| case-004-percent-width | AC-6.1 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 适用于所有 FrameNode | 所有组件均继承 CommonMethod，支持 width/height/size/constraintSize/padding/margin 属性 | — | AC-1.1~AC-5.8 |
| R-2 | 行为 | 所有接受 Length 参数的属性 | Length 类型支持 number(vp)、string('100px'/'50%'/'calc()')、Resource 三种形式 | — | AC-1.3~1.5 |
| R-3 | 行为 | selfIdealSize 被 Clamp 到 [min, max] | constraintSize 的 min/max 约束优先于 width/height 的 selfIdealSize | — | AC-3.2, AC-3.3 |
| R-4 | 行为 | padding+border 是 width/height 的一部分 | 组件采用 border-box 模型：width/height 包含 padding 和 border | — | AC-4.5 |
| R-5 | 行为 | margin 减少本节点的可用布局空间 | margin 从父级约束中扣除后传递给本节点 | — | AC-5.4, AC-5.5 |
| R-6 | 行为 | 父节点需要有确定尺寸 | 百分比参照系为父节点 contentConstraint 中的 percentReference（等于父节点 parentIdealSize 减去 padding 和 border） | — | AC-6.1~6.4 |
| R-7 | 行为 | 传入 number 类型 | width(number) 默认单位为 vp，转换为像素：px = value × vpScale | CalcLength | AC-1.3 |
| R-8 | 行为 | 传入 string 类型 | width(string) 根据后缀解析单位：'px'→PX, 'vp'→VP, 'fp'→FP, 'lpx'→LPX, '%'→PERCENT, 'calc()'→CALC | CalcLength | AC-1.4 |
| R-9 | 行为 | 任何尺寸属性变更 | 设置 width/height 触发 PROPERTY_UPDATE_MEASURE 标记，下一帧对脏节点执行 Measure | LayoutProperty | AC-1.1 |
| R-10 | 行为 | 调用 SetWidth 时保留已有 height | width/height 存储在 calcLayoutConstraint_->selfIdealSize 中，设置其中一个维度时保留另一维度的值 | MeasureProperty | AC-1.1, AC-1.2 |
| R-11 | 行为 | 调用 SetSize | size({width, height}) 内部分别调用 JsWidth 和 JsHeight；任一字段缺失（undefined）时该维度会被清除（ClearWidthOrHeight），而非保留原值 | MeasureProperty | AC-2.1~2.3 |
| R-12 | 行为 | 调用 SetConstraintSize | constraintSize 的四个字段分别存储在 calcLayoutConstraint_->minSize 和 maxSize 中 | MeasureProperty | AC-3.1 |
| R-13 | 行为 | Measure 阶段 | CheckSelfIdealSize 阶段执行 Clamp：selfIdealSize.width = clamp(selfIdealSize.width, minSize.width, maxSize.width) | LayoutConstraintF | AC-3.2, AC-3.3 |
| R-14 | 行为 | min > max 边界条件 | constraintSize 中 minWidth > maxWidth 时，Clamp 结果等于 minSize（min 优先） | LayoutConstraintF | AC-3.4 |
| R-15 | 行为 | 调用 SetPadding | padding(Length) 四个方向设置相同值；padding(Padding) 分别设置四个方向 | PaddingProperty | AC-4.1, AC-4.2 |
| R-16 | 行为 | 负值输入 | padding 值为负数时 Clamp 到 0 | PaddingProperty | AC-4.7 |
| R-17 | 行为 | padding+border > 显式宽度 | CheckBorderAndPadding：若 padding+border 总宽度 > selfIdealSize.width，则 selfIdealSize.width 扩展为 padding+border 总宽度 | LayoutConstraintF | AC-4.6 |
| R-18 | 行为 | Measure 阶段 | UpdateContentConstraint：contentConstraint = layoutConstraint 减去 padding 和 border | LayoutConstraintF | AC-4.5 |
| R-19 | 行为 | 调用 SetMargin | margin(Length) 四个方向设置相同值；margin(Margin) 分别设置四个方向 | MarginProperty | AC-5.1, AC-5.2 |
| R-20 | 行为 | 负值输入 | margin 允许负值（不做 Clamp），负 margin 导致组件向对应方向偏移 | MarginProperty | AC-5.7 |
| R-21 | 行为 | Measure 阶段 | UpdateLayoutConstraint 阶段：parentConstraint.maxSize -= margin; parentConstraint.percentReference -= margin | LayoutConstraintF | AC-5.4, AC-5.5 |
| R-22 | 行为 | PERCENT 单位 | 百分比转换：NormalizeToPx 将 PERCENT 类型 CalcLength 按 value × percentReference 转换为像素 | CalcLength | AC-6.1 |
| R-23 | 行为 | CALC 单位 | calc() 表达式通过 StringExpression::CalculateExp 计算，支持 +、-、*、/ 运算和混合单位 | CalcLength | AC-7.1~7.3 |
| R-24 | 行为 | 调用 width(LayoutPolicy) (API 15+) | LayoutPolicy 通过 layoutPolicy_ 存储，枚举值为 NO_MATCH/MATCH_PARENT/WRAP_CONTENT/FIX_AT_IDEAL_SIZE | LayoutPolicyProperty | AC-8.1~8.4 |
| R-25 | 异常 | width/height 传入负值且 target API ≥ 12 | 负值重置（API ≥ 12） | ClearWidthOrHeight：清除 selfIdealSize 对应维度，回退到默认行为（MATCH_CONTENT） | AC-1.7 |
| R-26 | 异常 | width/height 传入负值且 target API < 12 | 负值 Clamp（API < 12） | 值被 Clamp 到 0.0 | AC-1.8 |
| R-27 | 异常 | width/height 传入 undefined | undefined 重置 | ClearWidthOrHeight + 重置 LayoutPolicy 为 NO_MATCH | AC-1.6 |
| R-28 | 异常 | padding 传入负值 | padding 负值 Clamp | 值被 Clamp 到 0 | AC-4.7 |
| R-29 | 异常 | CalcLength 内部 Dimension 值为 NaN | NaN 输入 | NormalizeToPx 返回 false（NaN >= 0 为 false），该维度按未设置处理 | — |
| R-30 | 异常 | CalcLength 内部 Dimension 值为 Infinity | Infinity 输入 | NormalizeToPx 返回 true（Infinity >= 0 为 true），值被接受为 selfIdealSize | — |
| R-31 | 异常 | 父节点未设置显式尺寸，percentReference 为 0 | 百分比参照为 0 | 百分比计算结果为 0，组件对应维度为 0 | AC-6.2 |
| R-32 | 异常 | calc() 表达式计算结果 < 0 | calc() 结果为负 | NormalizeToPx 返回 false（result >= 0 失败），该维度按未设置处理 | AC-7.4 |
| R-33 | 异常 | 传入极小负值如 -0.0005 | 负值阈值精度 | LessNotEqual 阈值为 -0.001，-0.0005 不被视为负值（不触发 R-25/R-26），被当作有效值 0 附近处理 | — |
| R-34 | 恢复 | NormalizeToPx 转换失败（返回 false） | 对应维度不设置 selfIdealSize（保持 std::nullopt） | 组件该维度按 MATCH_CONTENT 或父约束决定 | — |
| R-35 | 恢复 | 负值触发 ClearWidthOrHeight | 清除 selfIdealSize 对应维度 + 重置 LayoutPolicy 为 NO_MATCH | 组件回退到未设置该维度的状态 | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-7, AC-1.3 | 单测 | number 类型 → vp 单位转换正确 |
| VM-2 | R-8, AC-1.4 | 单测 | string 类型解析各单位正确 |
| VM-3 | R-13, AC-3.2~3.4 | 单测 | constraintSize Clamp 逻辑正确 |
| VM-4 | R-17, AC-4.6 | 单测 | CheckBorderAndPadding 扩展逻辑 |
| VM-5 | R-21, AC-5.4~5.5 | 单测 | margin 扣除约束传播 |
| VM-6 | R-22, AC-6.1~6.4 | 单测 | 百分比参照系正确 |
| VM-7 | R-23, AC-7.1~7.4 | 单测 | calc() 表达式计算正确 |
| VM-8 | R-25~R-27 | 单测 | 负值/undefined 处理正确（区分 API 版本） |
| VM-9 | R-24, AC-8.1~8.4 | 单测 | LayoutPolicy 生效 |
| VM-10 | 全量 | XTS/集成 | 端到端布局渲染尺寸正确 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `width(value: Length): T` | Public | 设置组件宽度 | `common.d.ts:24330` | 7 | - |
| `width(widthValue: Length \| LayoutPolicy): T` | Public | 设置宽度或布局策略 | `common.d.ts:24346` | 15 | - |
| `height(value: Length): T` | Public | 设置组件高度 | `common.d.ts:24388` | 7 | - |
| `height(heightValue: Length \| LayoutPolicy): T` | Public | 设置高度或布局策略 | `common.d.ts:24404` | 15 | - |
| `size(value: SizeOptions): T` | Public | 同时设置宽高 | `common.d.ts:24591` | 7 | - |
| `constraintSize(value: ConstraintSizeOptions): T` | Public | 设置尺寸约束范围 | `common.d.ts:24639` | 7 | - |
| `padding(value: Padding \| Length): T` | Public | 设置内边距 | `common.d.ts:24817` | 7 | - |
| `padding(value: Padding \| Length \| LocalizedPadding): T` | Public | 设置内边距（支持 RTL） | `common.d.ts:24817` | 12 | - |
| `margin(value: Margin \| Length): T` | Public | 设置外边距 | `common.d.ts:24885` | 7 | - |
| `margin(value: Margin \| Length \| LocalizedMargin): T` | Public | 设置外边距（支持 RTL） | `common.d.ts:24885` | 12 | - |

**C-API (NDK) 接口：**

| 属性枚举 | 值格式 | 功能 | @since |
|----------|--------|------|--------|
| `NODE_WIDTH = 0` | `.value[0].f32` (vp) | 设置宽度 | 12 |
| `NODE_HEIGHT` | `.value[0].f32` (vp) | 设置高度 | 12 |
| `NODE_SIZE` | `.value[0].f32` (width vp), `.value[1].f32` (height vp) | 同时设置宽高 | 12 |
| `NODE_CONSTRAINT_SIZE` | `.value[0~3].f32` (minW, maxW, minH, maxH, vp) | 设置约束 | 12 |
| `NODE_WIDTH_PERCENT` | `.value[0].f32` (0~1) | 百分比宽度 | 12 |
| `NODE_HEIGHT_PERCENT` | `.value[0].f32` (0~1) | 百分比高度 | 12 |
| `NODE_PADDING` | `.value[0~3].f32` (top, right, bottom, left, vp) | 设置内边距 | 12 |
| `NODE_MARGIN` | `.value[0~3].f32` (top, right, bottom, left, vp) | 设置外边距 | 12 |
| `NODE_WIDTH_LAYOUTPOLICY = 105` | `.value[0].i32` (ArkUI_LayoutPolicy) | 宽度布局策略 | 21 |
| `NODE_HEIGHT_LAYOUTPOLICY = 106` | `.value[0].i32` (ArkUI_LayoutPolicy) | 高度布局策略 | 21 |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `Length` | `string \| number \| Resource` | `units.d.ts:97` |
| `SizeOptions` | `{ width?: Length; height?: Length }` | `units.d.ts:2967` |
| `ConstraintSizeOptions` | `{ minWidth?: Length; maxWidth?: Length; minHeight?: Length; maxHeight?: Length }` | `units.d.ts:2783` |
| `LayoutPolicy` | `{ matchParent, wrapContent, fixAtIdealSize }` | `common.d.ts:12801` (API 15) |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

---

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:**
  - **API 12**: 负值 width/height 从 Clamp 到 0 变更为 ClearWidthOrHeight（重置为默认）。此变更通过 `GreatOrEqualTargetAPIVersion(PlatformVersion::VERSION_TWELVE)` 守护
  - **API 12**: padding/margin 新增 LocalizedPadding/LocalizedMargin 重载（新增，不影响旧调用）
  - **API 15**: width/height 新增 LayoutPolicy 重载（新增重载，不破坏旧签名）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** @since 7 为基础，@since 12 和 @since 15 标注新增重载

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| CalcLength 延迟转换 | 尺寸值以 CalcLength 存储，仅在 Measure 阶段转换为像素 | AC-1.1, AC-6.1, AC-7.1 |
| border-box 模型 | selfIdealSize 包含 padding+border | AC-4.5, AC-4.6 |
| 单向依赖 | API 层 → Property 层 → Layout 算法层，不可反向 | 全部 |
| PROPERTY_UPDATE_MEASURE | 任何尺寸属性变更仅标记脏，不立即重新测量 | R-9 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次 width/height 设置 + 标记脏 < 1μs；Measure 管线中 UpdateLayoutConstraint < 10μs | benchmark | — |
| 内存 | MeasureProperty 使用 std::optional<CalcSize> 避免无用分配；LayoutConstraintF 为栈上值类型 | hidumper | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | N/A | 尺寸属性不直接影响无障碍语义 | — |
| 大字体 | 是 | FP 单位（字体像素）随系统字体缩放比例变化，CalcLength 转换时使用 fpScale | width/height 使用 FP 单位时受大字体影响 |
| 深色模式 | N/A | 尺寸属性与颜色无关 | — |
| 多窗口/分屏 | 是 | 窗口尺寸变化导致 parentConstraint 变化，触发子树重新 Measure | 所有百分比尺寸、MATCH_PARENT 策略 |
| 多用户 | N/A | 尺寸属性无用户态差异 | — |
| 版本升级 | 是 | API 12 负值行为变更、API 15 LayoutPolicy 新增——需通过 API 版本守护 | AC-1.7, AC-1.8, AC-8.1~8.4 |
| 生态兼容 | 是 | C-API (NDK) 提供等效接口，行为应与 ArkTS 一致 | 全部 C-API 属性 |

---

## 行为场景

```gherkin
Feature: 尺寸属性
  作为 应用开发者
  我想要 通过声明式 API 控制组件的宽度、高度、约束尺寸、内边距和外边距
  以便 实现精确的 UI 布局

  # ─── width / height 基础 ─────────────────────────

  Scenario: 设置固定宽高（vp）
    Given 一个 Column 容器宽 300vp 高 500vp
    And 一个 Text 子组件
    When 设置 Text.width(100).height(50)
    Then Text 渲染宽度为 100vp 对应的像素值
    And Text 渲染高度为 50vp 对应的像素值

  Scenario: 设置百分比宽度
    Given 一个 Column 容器宽 300vp
    And 一个 Text 子组件
    When 设置 Text.width('50%')
    Then Text 渲染宽度为 150vp 对应的像素值

  Scenario: 设置像素宽度
    Given 一个 Text 子组件
    When 设置 Text.width('200px')
    Then Text 渲染宽度为 200 物理像素

  Scenario: width 传入 undefined 重置
    Given 一个 Text 子组件已设置 width(100)
    When 设置 Text.width(undefined)
    Then Text 宽度重置为 MATCH_CONTENT（按内容决定宽度）

  Scenario: width 传入负值（API >= 12）
    Given 目标 API 版本 >= 12
    And 一个 Text 子组件
    When 设置 Text.width(-50)
    Then Text 宽度重置为 MATCH_CONTENT（等同 undefined）

  Scenario: width 传入负值（API < 12）
    Given 目标 API 版本 < 12
    And 一个 Text 子组件
    When 设置 Text.width(-50)
    Then Text 宽度被 Clamp 到 0

  Scenario: width 传入 0
    Given 一个 Text 子组件
    When 设置 Text.width(0)
    Then Text 渲染宽度为 0（不可见但存在于布局树）

  # ─── size ────────────────────────────────────────

  Scenario: 通过 size 同时设置宽高
    Given 一个 Text 子组件
    When 设置 Text.size({width: 100, height: 50})
    Then Text 渲染宽度为 100vp 对应像素值
    And Text 渲染高度为 50vp 对应像素值

  Scenario: size 仅设置一个维度
    Given 一个 Text 子组件已设置 width(200)
    When 设置 Text.size({height: 50})
    Then Text 高度变为 50vp
    And Text 宽度被清除（ClearWidthOrHeight），回退为 MATCH_CONTENT 默认行为
    # 注意：JsSize 内部对缺失的 width 字段调用 JsWidth(undefined)，触发清除逻辑

  # ─── constraintSize ─────────────────────────────

  Scenario: constraintSize 限制最大宽度
    Given 一个 Text 子组件
    When 设置 Text.width(200).constraintSize({maxWidth: 100})
    Then Text 最终宽度为 100（selfIdealSize 被 Clamp 到 maxWidth）

  Scenario: constraintSize 限制最小宽度
    Given 一个 Text 子组件
    When 设置 Text.width(20).constraintSize({minWidth: 50})
    Then Text 最终宽度为 50（selfIdealSize 被 Clamp 到 minWidth）

  Scenario: constraintSize minWidth > maxWidth
    Given 一个 Text 子组件
    When 设置 Text.constraintSize({minWidth: 100, maxWidth: 50})
    Then Clamp 结果以 minWidth(100) 为准

  # ─── padding ─────────────────────────────────────

  Scenario: padding 统一值
    Given 一个 Text 子组件设置 width(100).height(80)
    When 设置 Text.padding(10)
    Then 内容区宽度为 80vp（100 - 10 - 10）
    And 内容区高度为 60vp（80 - 10 - 10）

  Scenario: padding 超过显式宽度
    Given 一个 Text 子组件
    When 设置 Text.width(50).padding({left: 30, right: 30})
    Then 组件 selfIdealSize 宽度扩展到 60（padding 总宽度）
    And 内容区宽度为 0

  Scenario: padding 四方向分别设置
    Given 一个 Container 子组件
    When 设置 Container.padding({top: 10, right: 20, bottom: 30, left: 40})
    Then 上内边距 10vp、右内边距 20vp、下内边距 30vp、左内边距 40vp

  # ─── margin ──────────────────────────────────────

  Scenario: margin 减少可用空间
    Given 一个 Column 容器宽 300vp
    And 一个子组件设置 width('100%').margin({left: 20, right: 20})
    When 布局执行
    Then 子组件 percentReference 为 260vp（300 - 20 - 20）
    And 子组件宽度为 260vp

  Scenario: 负 margin
    Given 一个子组件设置 margin({left: -10})
    When 布局执行
    Then 组件向左偏移 10vp

  # ─── calc() 表达式 ────────────────────────────────

  Scenario: calc 混合百分比和固定值
    Given 一个 Column 容器宽 300vp
    And 一个子组件
    When 设置子组件 .width('calc(100% - 40vp)')
    Then 子组件宽度为 260vp（300 × 100% - 40）

  # ─── LayoutPolicy (API 15+) ──────────────────────

  Scenario: LayoutPolicy matchParent
    Given 目标 API 版本 >= 15
    And 一个 Column 容器宽 300vp
    And 一个子组件
    When 设置子组件 .width(LayoutPolicy.matchParent)
    Then 子组件宽度为 300vp

  Scenario: LayoutPolicy 覆盖固定值
    Given 一个子组件已设置 width(100)
    When 再设置 .width(LayoutPolicy.matchParent)
    Then LayoutPolicy 生效，之前的 width(100) 被清除
    And 子组件宽度匹配父容器

  # ─── 属性交互 ────────────────────────────────────

  Scenario Outline: 约束管线执行顺序
    Given 一个组件设置了 <属性组合>
    When Measure 阶段约束管线执行
    Then 按照以下优先级决定最终尺寸：
      | 步骤 | 操作 |
      | 1 | 父约束 - margin = 本节点可用约束 |
      | 2 | CheckCalcLayoutConstraint: CalcLength → px |
      | 3 | CheckSelfIdealSize: Clamp(selfIdeal, min, max) |
      | 4 | CheckBorderAndPadding: max(selfIdeal, padding+border) |
      | 5 | CheckAspectRatio: 如有 aspectRatio 进一步约束 |

    Examples:
      | 属性组合 |
      | width(100).constraintSize({maxWidth:80}).padding(5) |
      | width('50%').margin(10).constraintSize({minWidth:100}) |
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（width/height/size/constraintSize/padding/margin 六个属性；不含 flex*/aspectRatio/layoutWeight/expandSafeArea/pixelRound/onSizeChange）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "CommonMethod width height size constraintSize padding margin layout properties implementation"
  - repo: "openharmony/ace_engine"
    query: "LayoutProperty UpdateLayoutConstraint CheckCalcLayoutConstraint constraint pipeline"
  - repo: "openharmony/ace_engine"
    query: "CalcLength NormalizeToPx unit conversion"
```

**关键文档：**
- SDK API 知识库：`docs/sdk/ArkUI_SDK_API_Knowledge_Base.md`
- 架构设计：`specs/04-common-capability/03-common-attributes/01-layout-attributes/design.md`
