# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Checkbox/CheckboxGroup 组件全量规格 |
| 特性编号 | Func-05-04-02-Feat-01 |
| FuncID | 05-04-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 8 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 8 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Checkbox 组件 + select/selectedColor/onChange 属性 | @since 8 |
| ADDED | CheckboxGroup 组件 + selectAll/selectedColor/onChange 属性 | @since 8 |
| ADDED | Checkbox mark 复合样式 (strokeColor/size/strokeWidth) | @since 10 |
| ADDED | Checkbox unselectedColor 属性 | @since 10 |
| ADDED | CheckboxGroup unselectedColor 属性 | @since 10 |
| ADDED | Checkbox shape 属性 (Circle/ROUNDED_SQUARE/LINE) | @since 11 |
| ADDED | Checkbox contentModifier 自定义渲染 | @since 12 |
| ADDED | Checkbox indicatorBuilder 自定义指示器 | @since 12 |
| ADDED | CheckboxGroup checkboxShape 属性 | @since 12 |
| ADDED | C API: NODE_CHECKBOX_* 属性集 | NDK |
| ADDED | C API: ARKUI_NODE_CHECKBOX_GROUP=21 + NODE_CHECKBOX_GROUP_* | NDK @since 15 |
| ADDED | CheckboxGroup contentModifier 自定义渲染 | @since 21 |
| ADDED | Static API: checkbox.static.d.ets | @since 23 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/04-input-form-components/02-checkbox-checkbox-group/design.md`
- **KB 路由**: `docs/kb/components/selector/checkbox.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/checkbox.d.ts`
  - Static: `<OH_ROOT>/interface/sdk-js/api/arkui/component/checkbox.static.d.ets`
  - Modifier: `<OH_ROOT>/interface/sdk-js/api/arkui/CheckboxModifier.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础多选交互

**角色**: 应用开发者
**期望**: 我想要使用 Checkbox 组件实现多选框
**价值**: 以便用户可以在一组选项中选择多个选项

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `Checkbox({ name: 'option1', group: 'group1' })` THEN 显示复选框，初始为未选中状态 | 正常 |
| AC-1.2 | WHEN 用户点击 Checkbox THEN select 状态翻转，onChange 回调触发并携带新状态值 | 正常 |
| AC-1.3 | WHEN 设置 `.select(true)` THEN Checkbox 选中状态更新为 true | 正常 |
| AC-1.4 | WHEN select 使用 `$$` 双向绑定 THEN 组件状态与绑定变量保持同步 | 正常 |
| AC-1.5 | WHEN Checkbox 处于 disabled 状态 THEN 点击不改变状态，不触发 onChange | 异常 |

### US-2: Checkbox 样式定制

**角色**: 应用开发者
**期望**: 我想要自定义 Checkbox 的颜色、形状和选中标记
**价值**: 以便匹配应用的设计语言

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 设置 `.selectedColor(Color.Red)` THEN 选中时颜色为红色 | 正常 |
| AC-2.2 | WHEN 设置 `.unselectedColor('#33000000')` THEN 未选中时颜色为 0x33000000 | 正常 |
| AC-2.3 | WHEN 设置 `.mark({ strokeColor: Color.White, size: 16, strokeWidth: 2 })` THEN 选中标记颜色为白色、大小 16vp、线宽 2vp | 正常 |
| AC-2.4 | WHEN 设置 `.shape(CheckboxShape.ROUNDED_SQUARE)` THEN 形状为圆角方形 | 正常 |
| AC-2.5 | WHEN 未设置颜色属性 THEN 使用 CheckBoxTheme 默认值（`checkbox_theme_wrapper.h`） | 异常 |

### US-3: 自定义指示器

**角色**: 应用开发者
**期望**: 我想要自定义 Checkbox 的选中指示器
**价值**: 以便实现超出标准样式的定制化需求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `.indicatorBuilder(() => { Image($r('app.media.check')) })` THEN 选中时显示自定义指示器内容 | 正常 |
| AC-3.2 | WHEN 设置 `.contentModifier(modifier)` THEN 组件通过 `CheckboxConfiguration { isCheck, enabled, triggerChange }` 回调自定义 Builder | 正常 |
| AC-3.3 | WHEN 调用 `triggerChange(true)` THEN 程序化切换 Checkbox 选中状态为 true | 正常 |
| AC-3.4 | WHEN ContentModifier 激活时 THEN Checkbox 跳过默认渲染，使用自定义 Builder 内容替代 | 正常 |

### US-4: CheckboxGroup 分组管理

**角色**: 应用开发者
**期望**: 我想要使用 CheckboxGroup 管理一组 Checkbox 的联动
**价值**: 以便实现全选/部分选中/全不选的分组管理

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 创建 `CheckboxGroup({ group: 'group1' })` 并将多个 Checkbox 的 group 设为 'group1' THEN CheckboxGroup 管理这些 Checkbox 的联动 | 正常 |
| AC-4.2 | WHEN 分组内所有 Checkbox 均选中 THEN CheckboxGroup 的 onChange 回调 status 为 SelectStatus.All | 正常 |
| AC-4.3 | WHEN 分组内部分 Checkbox 选中 THEN status 为 SelectStatus.Part | 正常 |
| AC-4.4 | WHEN 分组内所有 Checkbox 均未选中 THEN status 为 SelectStatus.None | 正常 |
| AC-4.5 | WHEN 设置 `.selectAll(true)` THEN 分组内所有 Checkbox 选中状态设为 true | 正常 |

### US-5: CheckboxGroup 样式定制

**角色**: 应用开发者
**期望**: 我想要统一设置分组内所有 Checkbox 的样式
**价值**: 以便保持分组内视觉一致性

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 设置 CheckboxGroup `.selectedColor(Color.Red)` THEN 分组内所有 Checkbox 的选中颜色为红色 | 正常 |
| AC-5.2 | WHEN 设置 CheckboxGroup `.unselectedColor('#33000000')` THEN 分组内所有 Checkbox 的未选中颜色为 0x33000000 | 正常 |
| AC-5.3 | WHEN 设置 CheckboxGroup `.mark({ strokeColor: Color.White, size: 16 })` THEN 分组内所有 Checkbox 的选中标记样式为白色、大小 16vp | 正常 |
| AC-5.4 | WHEN 设置 CheckboxGroup `.checkboxShape(CheckboxShape.ROUNDED_SQUARE)` THEN 分组内所有 Checkbox 的形状为圆角方形 | 正常 |

### US-6: CheckboxGroup ContentModifier

**角色**: 应用开发者
**期望**: 我想要使用 ContentModifier 自定义 CheckboxGroup 的渲染
**价值**: 以便实现超出标准样式的分组定制化需求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 设置 CheckboxGroup `contentModifier(modifier)` THEN 组件通过 `CheckboxGroupConfiguration { selectedItems, status, enabled, triggerChange }` 回调自定义 Builder | 正常 |
| AC-6.2 | WHEN 调用 `triggerChange(['item1', 'item2'])` THEN 分组内名为 'item1' 和 'item2' 的 Checkbox 选中，其余取消选中 | 正常 |
| AC-6.3 | WHEN ContentModifier 激活时 THEN CheckboxGroup 跳过默认渲染，使用自定义 Builder 内容替代 | 正常 |

### US-7: C API 支持 (Checkbox)

**角色**: NDK 开发者
**期望**: 我想要通过 C API 控制 Checkbox 的状态和样式
**价值**: 以便在 Native 层集成 Checkbox 组件

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 通过 `NODE_CHECKBOX_SELECT` 设置 `.value[0].i32 = 1` THEN Checkbox 选中状态为 true | 正常 |
| AC-7.2 | WHEN 通过 `NODE_CHECKBOX_SELECTED_COLOR` 设置 `.value[0].u32 = 0xFFFF0000` THEN 选中颜色为红色 | 正常 |
| AC-7.3 | WHEN 通过 `NODE_CHECKBOX_UNSELECTED_COLOR` 设置颜色 THEN 未选中颜色更新 | 正常 |
| AC-7.4 | WHEN 通过 `NODE_CHECKBOX_SHAPE` 设置 `.value[0].i32 = 1` THEN 形状为 ROUNDED_SQUARE (0=Circle, 1=ROUNDED_SQUARE, 2=LINE) | 正常 |
| AC-7.5 | WHEN 注册 `NODE_CHECKBOX_ON_CHANGE` 回调 THEN 状态变化时 `.data[0].i32` 返回 1（选中）或 0（未选中） | 正常 |

### US-8: C API 支持 (CheckboxGroup)

**角色**: NDK 开发者
**期望**: 我想要通过 C API 控制 CheckboxGroup 的状态和样式
**价值**: 以便在 Native 层集成 CheckboxGroup 组件

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 通过 `ARKUI_NODE_CHECKBOX_GROUP` (since 15) 创建节点 THEN CheckboxGroup 节点创建成功 | 正常 |
| AC-8.2 | WHEN 通过 `NODE_CHECKBOX_GROUP_SELECT_ALL` 设置 `.value[0].i32 = 1` THEN 分组内所有 Checkbox 选中 | 正常 |
| AC-8.3 | WHEN 通过 `NODE_CHECKBOX_GROUP_SELECTED_COLOR` 设置颜色 THEN 分组内所有 Checkbox 的选中颜色更新 | 正常 |
| AC-8.4 | WHEN 注册 `NODE_CHECKBOX_GROUP_ON_CHANGE` 回调 THEN 状态变化时回调携带变化的 Checkbox 名称和分组状态 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3 | TASK-CHECKBOX-01 | UT | `test/unittest/core/pattern/checkbox/` |
| AC-1.5 | R-14 | TASK-CHECKBOX-01 | UT | disabled 状态测试 |
| AC-2.1 ~ AC-2.5 | R-4, R-5, R-6, R-7 | TASK-CHECKBOX-01 | UT | Checkbox 样式属性测试 |
| AC-3.1 ~ AC-3.4 | R-8, R-9 | TASK-CHECKBOX-01 | UT | indicatorBuilder 和 ContentModifier 测试 |
| AC-4.1 ~ AC-4.5 | R-10, R-11, R-12 | TASK-CHECKBOX-01 | UT | CheckboxGroup 分组管理测试 |
| AC-5.1 ~ AC-5.4 | R-13 | TASK-CHECKBOX-01 | UT | CheckboxGroup 样式测试 |
| AC-6.1 ~ AC-6.3 | R-9 | TASK-CHECKBOX-01 | UT | CheckboxGroup ContentModifier 测试 |
| AC-7.1 ~ AC-7.5 | R-15 | TASK-CHECKBOX-01 | C API UT | capi_all_modifiers_test |
| AC-8.1 ~ AC-8.4 | R-16 | TASK-CHECKBOX-01 | C API UT | capi_all_modifiers_test |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `checkbox_model_ng.cpp` | Checkbox 通过 CheckBoxModelNG::Create() 创建节点，name 和 group 存入 CheckBoxPaintProperty | — | AC-1.1 |
| R-2 | 行为 | `checkbox_pattern.cpp` | 用户点击 Checkbox 翻转 select 状态并触发 onChange 回调 | — | AC-1.2 |
| R-3 | 行为 | `checkbox_model_ng.cpp`, SDK checkbox.d.ts | select 支持 `$$` 双向绑定（Dynamic API） | — | AC-1.4 |
| R-4 | 行为 | `checkbox_paint_property.cpp` | selectedColor 设置选中时颜色；unselectedColor 设置未选中时颜色（@since 10） | — | AC-2.1, AC-2.2 |
| R-5 | 行为 | `checkbox_paint_property.cpp` | mark 复合属性封装 strokeColor/size/strokeWidth（@since 10） | — | AC-2.3 |
| R-6 | 行为 | `checkbox_paint_property.cpp` | shape 属性设置 Checkbox 形状：Circle/ROUNDED_SQUARE/LINE（@since 11） | — | AC-2.4 |
| R-7 | 恢复 | `checkbox_theme_wrapper.h` | 颜色/标记属性 Reset 时恢复到 CheckBoxTheme 默认值 | — | AC-2.5 |
| R-8 | 行为 | `checkbox_pattern.cpp` | indicatorBuilder 通过 Builder 函数自定义选中指示器，仅替换选中标记部分（@since 12） | — | AC-3.1 |
| R-9 | 行为 | `checkbox_pattern.cpp` | ContentModifier 激活时跳过默认渲染，通过 CheckboxConfiguration { isCheck, enabled, triggerChange } 回调自定义 Builder（@since 12） | triggerChange 程序化切换 | AC-3.2 ~ AC-3.4, AC-6.1 ~ AC-6.3 |
| R-10 | 行为 | `checkboxgroup_pattern.cpp`, `checkboxgroup_model_ng.cpp` | CheckboxGroup 通过 GroupManager 管理分组联动，子 Checkbox 通过 name 属性关联 | — | AC-4.1 |
| R-11 | 行为 | `checkboxgroup_pattern.cpp` | SelectStatus 计算规则：所有选中=All，部分选中=Part，全部未选中=None | SelectStatus 枚举 | AC-4.2 ~ AC-4.4 |
| R-12 | 行为 | `checkboxgroup_pattern.cpp` | selectAll(true) 将分组内所有 Checkbox 选中设为 true；selectAll(false) 设为 false | — | AC-4.5 |
| R-13 | 行为 | `checkboxgroup_pattern.cpp` | CheckboxGroup 的 selectedColor/unselectedColor/mark/checkboxShape 属性应用到分组内所有 Checkbox | — | AC-5.1 ~ AC-5.4 |
| R-14 | 异常 | `checkbox_pattern.cpp` | disabled 状态下点击不改变 select 状态、不触发 onChange | — | AC-1.5 |
| R-15 | 行为 | `node_checkbox_modifier.cpp`, `native_node.h` | C API: NODE_CHECKBOX_SELECT (.value[0].i32 0/1)、NODE_CHECKBOX_SELECTED_COLOR (.value[0].u32 0xARGB)、NODE_CHECKBOX_UNSELECTED_COLOR、NODE_CHECKBOX_SHAPE (.value[0].i32 0~2)、NODE_CHECKBOX_ON_CHANGE (.data[0].i32 1/0) | ARKUI_NODE_CHECKBOX=11 | AC-7.1 ~ AC-7.5 |
| R-16 | 行为 | `checkboxgroup_modifier.cpp`, `native_node.h` | C API: ARKUI_NODE_CHECKBOX_GROUP=21（@since 15）、NODE_CHECKBOX_GROUP_SELECT_ALL/SELECTED_COLOR/UNSELECTED_COLOR/ON_CHANGE | — | AC-8.1 ~ AC-8.4 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | Checkbox 选中交互 + 双向绑定 |
| VM-2 | AC-1.5, R-14 | UT | disabled 状态行为 |
| VM-3 | AC-2.1 ~ AC-2.5 | UT | Checkbox 样式属性与默认值 |
| VM-4 | AC-3.1 ~ AC-3.4 | UT | indicatorBuilder 和 ContentModifier 集成 |
| VM-5 | AC-4.1 ~ AC-4.5 | UT | CheckboxGroup 分组联动 + SelectStatus |
| VM-6 | AC-5.1 ~ AC-5.4 | UT | CheckboxGroup 样式应用 |
| VM-7 | AC-6.1 ~ AC-6.3 | UT | CheckboxGroup ContentModifier |
| VM-8 | AC-7.1 ~ AC-7.5 | C API UT | Checkbox C API 属性和事件 |
| VM-9 | AC-8.1 ~ AC-8.4 | C API UT | CheckboxGroup C API 属性和事件 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC | @since |
|----------|---------|----------|--------|-----------|----------|---------|--------|
| Checkbox(options) | Public | name, group, indicator | CheckboxAttribute | N/A | 创建 Checkbox | AC-1.1 | 8 |
| CheckboxAttribute.select(value) | Public | boolean | CheckboxAttribute | N/A | 设置选中状态 | AC-1.3 | 8 |
| CheckboxAttribute.selectedColor(value) | Public | ResourceColor | CheckboxAttribute | N/A | 选中颜色 | AC-2.1 | 8 |
| CheckboxAttribute.unselectedColor(value) | Public | ResourceColor | CheckboxAttribute | N/A | 未选中颜色 | AC-2.2 | 10 |
| CheckboxAttribute.mark(value) | Public | MarkStyle | CheckboxAttribute | N/A | 选中标记样式 | AC-2.3 | 10 |
| CheckboxAttribute.shape(value) | Public | CheckboxShape | CheckboxAttribute | N/A | 形状 | AC-2.4 | 11 |
| CheckboxAttribute.onChange(callback) | Public | (value: boolean) => void | CheckboxAttribute | N/A | 状态变化回调 | AC-1.2 | 8 |
| CheckboxAttribute.contentModifier(modifier) | Public | ContentModifier<CheckboxConfiguration> | CheckboxAttribute | N/A | 自定义渲染 | AC-3.2 | 12 |
| CheckboxAttribute.indicatorBuilder(builder) | Public | CustomBuilder | CheckboxAttribute | N/A | 自定义指示器 | AC-3.1 | 12 |
| CheckboxGroup(options) | Public | group | CheckboxGroupAttribute | N/A | 创建 CheckboxGroup | AC-4.1 | 8 |
| CheckboxGroupAttribute.selectAll(value) | Public | boolean | CheckboxGroupAttribute | N/A | 全选 | AC-4.5 | 8 |
| CheckboxGroupAttribute.selectedColor(value) | Public | ResourceColor | CheckboxGroupAttribute | N/A | 分组选中颜色 | AC-5.1 | 8 |
| CheckboxGroupAttribute.unselectedColor(value) | Public | ResourceColor | CheckboxGroupAttribute | N/A | 分组未选中颜色 | AC-5.2 | 10 |
| CheckboxGroupAttribute.mark(value) | Public | MarkStyle | CheckboxGroupAttribute | N/A | 分组标记样式 | AC-5.3 | 10 |
| CheckboxGroupAttribute.checkboxShape(value) | Public | CheckboxShape | CheckboxGroupAttribute | N/A | 分组形状 | AC-5.4 | 12 |
| CheckboxGroupAttribute.onChange(callback) | Public | (name: string, status: SelectStatus) => void | CheckboxGroupAttribute | N/A | 分组状态变化回调 | AC-4.2 ~ AC-4.4 | 8 |
| CheckboxGroupAttribute.contentModifier(modifier) | Public | ContentModifier<CheckboxGroupConfiguration> | CheckboxGroupAttribute | N/A | 分组自定义渲染 | AC-6.1 | 21 |
| NODE_CHECKBOX_SELECT | NDK/Public | .value[0].i32 | void | N/A | C API 选中状态 | AC-7.1 | NDK |
| NODE_CHECKBOX_SELECTED_COLOR | NDK/Public | .value[0].u32 | void | N/A | C API 选中颜色 | AC-7.2 | NDK |
| NODE_CHECKBOX_UNSELECTED_COLOR | NDK/Public | .value[0].u32 | void | N/A | C API 未选中颜色 | AC-7.3 | NDK |
| NODE_CHECKBOX_SHAPE | NDK/Public | .value[0].i32 | void | N/A | C API 形状 | AC-7.4 | NDK |
| NODE_CHECKBOX_ON_CHANGE | NDK/Public | 回调 .data[0].i32 | void | N/A | C API 状态变化事件 | AC-7.5 | NDK |
| ARKUI_NODE_CHECKBOX_GROUP | NDK/Public | — | — | — | C API 分组节点类型 | AC-8.1 | 15 |
| NODE_CHECKBOX_GROUP_SELECT_ALL | NDK/Public | .value[0].i32 | void | N/A | C API 全选 | AC-8.2 | 15 |
| NODE_CHECKBOX_GROUP_SELECTED_COLOR | NDK/Public | .value[0].u32 | void | N/A | C API 分组选中颜色 | AC-8.3 | 15 |
| NODE_CHECKBOX_GROUP_ON_CHANGE | NDK/Public | 回调 | void | N/A | C API 分组状态变化事件 | AC-8.4 | 15 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|---------|---------|
| 无 | — | — | — | — |

> 截至当前版本，Checkbox/CheckboxGroup 未发现任何 @deprecated 或 @useinstead 标注的 API。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** 基础 API @since 8，unselectedColor/mark @since 10，shape @since 11，contentModifier/indicatorBuilder/checkboxShape @since 12，ARKUI_NODE_CHECKBOX_GROUP C API @since 15，CheckboxGroup contentModifier @since 21，Static API @since 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 组件化 SO | Checkbox 已组件化为独立 SO（libarkui_checkbox.z.so），CheckboxGroup 共享同一 SO | AC-1.1, AC-4.1 |
| GroupManager 联动 | CheckboxGroup 通过 GroupManager 管理分组联动，子 Checkbox 通过 name 关联 | AC-4.1 ~ AC-4.5 |
| ToggleCheckBox 继承 | ToggleCheckBoxPattern 继承 CheckBoxPattern，行为委托 | — |
| C API 节点类型 | ARKUI_NODE_CHECKBOX=11，ARKUI_NODE_CHECKBOX_GROUP=21（since 15） | AC-7.1, AC-8.1 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Checkbox 选中状态切换帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | ContentModifier 自定义节点在组件销毁时释放 | UT + Dump | 节点树 Dump |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | GroupManager 在动态增删 Checkbox 时不崩溃 | UT | checkbox 单测 |
| 问题定位 | hilog 标签覆盖关键路径（状态切换、分组联动） | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

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
| 无障碍 | 是 | Checkbox 实现 IsCheckable/IsChecked/ActionSelect/ActionClearSelection；CheckboxGroup 报告分组状态 | AC-1.2 |
| 大字体 | 是 | Checkbox 尺寸跟随系统字体缩放，shape 属性支持自定义 | AC-2.4 |
| 深色模式 | 是 | 颜色属性通过 ResourceColor 支持主题跟随 | AC-2.1, AC-2.5 |
| 多窗口/分屏 | 否 | 无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 15 新增 ARKUI_NODE_CHECKBOX_GROUP C API；API 21 新增 CheckboxGroup ContentModifier | AC-8.1, AC-6.1 |
| 生态兼容 | 是 | C API 属性子集限制需在 NDK 文档中明确 | AC-7.1 ~ AC-8.4 |

## 行为场景（Gherkin）

```gherkin
Feature: Checkbox/CheckboxGroup 组件
  作为应用开发者
  我想要使用 Checkbox 和 CheckboxGroup 组件实现多选交互
  以便在表单中管理选项选择

  Scenario: Checkbox 点击切换
    Given Checkbox 组件以 select=false 创建
    When 用户点击 Checkbox
    Then select 变为 true
    And onChange 回调被触发，参数为 true

  Scenario: Checkbox disabled 状态
    Given Checkbox 组件以 enabled=false 创建
    When 用户点击 Checkbox
    Then select 状态不变
    And onChange 不触发

  Scenario: Checkbox shape 设置
    Given 设置 .shape(CheckboxShape.ROUNDED_SQUARE)
    Then Checkbox 形状为圆角方形

  Scenario: CheckboxGroup 全选
    Given CheckboxGroup 管理三个 Checkbox，初始均未选中
    When 设置 .selectAll(true)
    Then 三个 Checkbox 均选中
    And onChange 回调 status 为 SelectStatus.All

  Scenario: CheckboxGroup 部分选中
    Given CheckboxGroup 管理三个 Checkbox
    When 用户选中其中一个 Checkbox
    Then onChange 回调 status 为 SelectStatus.Part

  Scenario: CheckboxGroup 全不选
    Given CheckboxGroup 管理三个 Checkbox，初始均选中
    When 用户取消选中所有 Checkbox
    Then onChange 回调 status 为 SelectStatus.None

  Scenario: ContentModifier 自定义渲染
    Given Checkbox 设置了 contentModifier
    When ContentModifier 激活
    Then 默认渲染被自定义 Builder 替换
    And 通过 CheckboxConfiguration { isCheck, enabled, triggerChange } 回调

  Scenario: C API 设置选中状态
    Given 通过 C API 创建 ARKUI_NODE_CHECKBOX 节点
    When 设置 NODE_CHECKBOX_SELECT = 1
    Then Checkbox 选中状态为 true
    And NODE_CHECKBOX_ON_CHANGE 事件触发

  Scenario: C API CheckboxGroup 全选
    Given 通过 C API 创建 ARKUI_NODE_CHECKBOX_GROUP 节点
    When 设置 NODE_CHECKBOX_GROUP_SELECT_ALL = 1
    Then 分组内所有 Checkbox 选中
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
  - repo: "openharmony/ace_engine"
    query: "Checkbox/CheckboxGroup GroupManager 分组联动机制和 SelectStatus 计算"
  - repo: "openharmony/ace_engine"
    query: "Checkbox contentModifier/indicatorBuilder 自定义渲染集成"
  - repo: "openharmony/ace_engine"
    query: "Checkbox/CheckboxGroup C API node_checkbox_modifier/checkboxgroup_modifier 实现"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/checkbox.d.ts`
- KB 路由: `docs/kb/components/selector/checkbox.md`
- 源码入口: `frameworks/core/components_ng/pattern/checkbox/checkbox_pattern.cpp`
