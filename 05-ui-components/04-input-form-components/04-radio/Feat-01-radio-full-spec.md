# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Radio 组件全量规格 |
| 特性编号 | Func-05-04-04-Feat-01 |
| FuncID | 05-04-04 |
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
| ADDED | Radio 组件 + checked/radioStyle/onChange 属性 | @since 8 |
| ADDED | radioStyle 复合样式 (indicatorColor/indicatorRadius) | @since 10 |
| ADDED | contentModifier 自定义渲染 | @since 12 |
| ADDED | indicatorType 枚举 (TICK/DOT/CUSTOM) | @since 12 |
| ADDED | indicatorBuilder 自定义指示器 | @since 12 |
| ADDED | C API: ARKUI_NODE_RADIO=18 + NODE_RADIO_* 属性集 | NDK |
| ADDED | Static API: radio.static.d.ets | @since 23 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/04-input-form-components/04-radio/design.md`
- **KB 路由**: `docs/kb/components/selector/radio.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/radio.d.ts`
  - Static: `<OH_ROOT>/interface/sdk-js/api/arkui/component/radio.static.d.ets`
  - Modifier: `<OH_ROOT>/interface/sdk-js/api/arkui/RadioModifier.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础单选交互

**角色**: 应用开发者
**期望**: 我想要使用 Radio 组件实现单选按钮
**价值**: 以便用户可以在一组选项中选择一个选项

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `Radio({ group: 'radioGroup', value: 'option1' })` THEN 显示单选按钮，初始为未选中状态 | 正常 |
| AC-1.2 | WHEN 用户点击 Radio THEN checked 状态变为 true，onChange 回调触发并携带 true | 正常 |
| AC-1.3 | WHEN 同组其他 Radio 被选中 THEN 当前 Radio 的 checked 自动变为 false，触发进出动画 | 正常 |
| AC-1.4 | WHEN Radio 处于 disabled 状态 THEN 点击不改变状态，不触发 onChange | 异常 |
| AC-1.5 | WHEN 通过 `.checked(true)` 程序化设置 THEN checked 为只读属性，设置不生效（通过交互或联动改变） | 边界 |

### US-2: 样式定制

**角色**: 应用开发者
**期望**: 我想要自定义 Radio 的选中指示器样式
**价值**: 以便匹配应用的设计语言

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 设置 `.radioStyle({ indicatorColor: Color.Red, indicatorRadius: 8 })` THEN 选中指示器颜色为红色、半径 8vp | 正常 |
| AC-2.2 | WHEN 未设置 radioStyle THEN 使用 RadioTheme 默认值（`radio_theme.h`） | 异常 |
| AC-2.3 | WHEN 设置 `.indicatorType(RadioIndicatorType.TICK)` THEN 选中指示器为勾选标记样式 | 正常 |
| AC-2.4 | WHEN 设置 `.indicatorType(RadioIndicatorType.DOT)` THEN 选中指示器为圆点样式（默认） | 正常 |

### US-3: 自定义指示器

**角色**: 应用开发者
**期望**: 我想要自定义 Radio 的选中指示器内容
**价值**: 以便实现超出标准样式的定制化需求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `.indicatorType(RadioIndicatorType.CUSTOM)` 并 `.indicatorBuilder(() => { Image($r('app.media.dot')) })` THEN 选中时显示自定义指示器内容 | 正常 |
| AC-3.2 | WHEN 设置 `.contentModifier(modifier)` THEN 组件通过 `RadioConfiguration { checked, enabled, triggerChange }` 回调自定义 Builder | 正常 |
| AC-3.3 | WHEN 调用 `triggerChange(true)` THEN 程序化切换 Radio 选中状态为 true | 正常 |
| AC-3.4 | WHEN ContentModifier 激活时 THEN Radio 跳过默认渲染，使用自定义 Builder 内容替代 | 正常 |
| AC-3.5 | WHEN 设置 indicatorBuilder 但未设置 indicatorType 为 CUSTOM THEN indicatorBuilder 不生效（仅 CUSTOM 类型时生效） | 边界 |

### US-4: RadioGroup 分组互斥

**角色**: 应用开发者
**期望**: 我想要使用 RadioGroup 实现分组内单选互斥
**价值**: 以便用户在同一组中只能选择一个选项

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 创建多个 Radio 并设置相同 group 名称 THEN 这些 Radio 属于同一分组，实现单选互斥 | 正常 |
| AC-4.2 | WHEN 分组内 Radio A 已选中，用户点击 Radio B THEN Radio A 自动取消选中，Radio B 变为选中 | 正常 |
| AC-4.3 | WHEN Radio B 被选中 THEN Radio A 的 onChange 回调被触发（参数为 false），Radio B 的 onChange 回调被触发（参数为 true） | 正常 |
| AC-4.4 | WHEN Radio 已选中 THEN 再次点击同一 Radio 不改变选中状态（Radio 选中后不可通过点击取消） | 边界 |

### US-5: 进出动画

**角色**: 终端用户
**期望**: 我想要在 Radio 选中/取消时看到自然的动画过渡
**价值**: 以便获得流畅的交互体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN Radio 被选中 THEN 选中指示器使用 InterpolatingSpring 弹簧动画从 0 缩放到完整尺寸 | 正常 |
| AC-5.2 | WHEN Radio 被取消选中（同组其他 Radio 被选中）THEN 选中指示器使用 InterpolatingSpring 弹簧动画从完整尺寸缩放到 0 | 正常 |
| AC-5.3 | WHEN Radio 处于 disabled 状态 THEN 不触发进出动画 | 异常 |

### US-6: 无障碍支持

**角色**: 辅助功能用户
**期望**: 我想要通过无障碍服务操作 Radio
**价值**: 以便在无法直接触摸屏幕时完成单选操作

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 无障碍服务查询 Radio THEN 报告 IsCheckable = true，IsChecked = 当前 checked 状态 | 正常 |
| AC-6.2 | WHEN 无障碍服务执行 ActionSelect THEN Radio checked 设为 true | 正常 |
| AC-6.3 | WHEN 无障碍服务执行 ActionSelect 选中同组其他 Radio THEN 当前 Radio 自动取消选中 | 正常 |

### US-7: C API / NDK 支持

**角色**: NDK 开发者
**期望**: 我想要通过 C API 控制 Radio 的状态、样式和分组
**价值**: 以便在 Native 层集成 Radio 组件

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 通过 `NODE_RADIO_CHECKED` 设置 `.value[0].i32 = 1` THEN Radio 选中状态为 true | 正常 |
| AC-7.2 | WHEN 通过 `NODE_RADIO_VALUE` 设置 `.string = "option1"` THEN Radio 的值标识为 "option1" | 正常 |
| AC-7.3 | WHEN 通过 `NODE_RADIO_GROUP` 设置 `.string = "radioGroup"` THEN Radio 关联到分组 "radioGroup" | 正常 |
| AC-7.4 | WHEN 通过 `NODE_RADIO_STYLE` 设置 indicatorColor 和 indicatorRadius THEN 选中指示器样式更新 | 正常 |
| AC-7.5 | WHEN 通过 `ARKUI_NODE_RADIO` (value=18) 创建节点 THEN Radio 节点创建成功 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.3 | R-1, R-2, R-3 | TASK-RADIO-01 | UT | `test/unittest/core/pattern/radio/` |
| AC-1.4 | R-11 | TASK-RADIO-01 | UT | disabled 状态测试 |
| AC-1.5 | R-2 | TASK-RADIO-01 | UT | checked 只读语义测试 |
| AC-2.1 ~ AC-2.4 | R-4, R-5, R-6 | TASK-RADIO-01 | UT | 样式和 indicatorType 测试 |
| AC-3.1 ~ AC-3.5 | R-7, R-8, R-9 | TASK-RADIO-01 | UT | indicatorBuilder 和 ContentModifier 测试 |
| AC-4.1 ~ AC-4.4 | R-3, R-10 | TASK-RADIO-01 | UT | 分组互斥测试 |
| AC-5.1 ~ AC-5.3 | R-12, R-11 | TASK-RADIO-01 | UT + 手工 | 进出动画验证 |
| AC-6.1 ~ AC-6.3 | R-13 | TASK-RADIO-01 | UT | 无障碍属性和操作测试 |
| AC-7.1 ~ AC-7.5 | R-14 | TASK-RADIO-01 | C API UT | capi_all_modifiers_test |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `radio_model_ng.cpp` | Radio 通过 RadioModelNG::Create() 创建节点，value 和 group 存入 RadioPaintProperty | — | AC-1.1 |
| R-2 | 行为 | `radio_pattern.cpp` | checked 为只读属性，通过 API 设置 checked 不生效；选中状态仅由点击交互或 RadioGroup 联动改变 | — | AC-1.2, AC-1.5 |
| R-3 | 行为 | `radio_pattern.cpp`, `radio_modifier.h` | 用户点击 Radio 时 checked 变为 true，调用 GroupManager::UpdateRadioGroupValue 通知同组其他 Radio 取消选中 | — | AC-1.3, AC-4.1 ~ AC-4.3 |
| R-4 | 行为 | `radio_paint_property.cpp` | radioStyle 复合属性封装 indicatorColor 和 indicatorRadius（@since 10） | — | AC-2.1 |
| R-5 | 恢复 | `radio_theme.h` | radioStyle 属性 Reset 时恢复到 RadioTheme 默认值 | — | AC-2.2 |
| R-6 | 行为 | `radio_paint_property.cpp` | indicatorType 设置选中指示器样式：TICK/DOT/CUSTOM（@since 12），默认 DOT | — | AC-2.3, AC-2.4 |
| R-7 | 行为 | `radio_pattern.cpp` | indicatorBuilder 通过 Builder 函数自定义选中指示器，仅在 indicatorType 为 CUSTOM 时生效（@since 12） | — | AC-3.1, AC-3.5 |
| R-8 | 行为 | `radio_pattern.cpp` | ContentModifier 激活时跳过默认渲染，通过 RadioConfiguration { checked, enabled, triggerChange } 回调自定义 Builder（@since 12） | triggerChange 程序化切换 | AC-3.2 ~ AC-3.4 |
| R-9 | 行为 | `radio_pattern.cpp` | triggerChange(true/false) 程序化切换 Radio 选中状态，触发分组互斥联动 | — | AC-3.3 |
| R-10 | 边界 | `radio_pattern.cpp` | Radio 选中后再次点击同一 Radio 不改变选中状态（不可通过点击取消选中） | — | AC-4.4 |
| R-11 | 异常 | `radio_pattern.cpp` | disabled 状态下点击不改变 checked 状态、不触发 onChange、不触发进出动画 | — | AC-1.4, AC-5.3 |
| R-12 | 行为 | `radio_modifier.h` | Radio 选中/取消时使用 InterpolatingSpring 弹簧动画：选中时指示器从 0 缩放到完整尺寸，取消时从完整尺寸缩放到 0 | — | AC-5.1, AC-5.2 |
| R-13 | 行为 | `radio_accessibility_property.cpp` | Radio 无障碍属性：IsCheckable=true，IsChecked=当前 checked 状态；ActionSelect 将 checked 设为 true | — | AC-6.1 ~ AC-6.3 |
| R-14 | 行为 | `radio_modifier.cpp`, `native_node.h` | C API: ARKUI_NODE_RADIO=18、NODE_RADIO_CHECKED (.value[0].i32 0/1)、NODE_RADIO_VALUE (.string)、NODE_RADIO_GROUP (.string)、NODE_RADIO_STYLE (复合属性 indicatorColor + indicatorRadius) | — | AC-7.1 ~ AC-7.5 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.3 | UT | Radio 选中交互 + 分组互斥联动 |
| VM-2 | AC-1.4, R-11 | UT | disabled 状态行为 |
| VM-3 | AC-1.5, R-2 | UT | checked 只读语义 |
| VM-4 | AC-2.1 ~ AC-2.4 | UT | radioStyle 和 indicatorType |
| VM-5 | AC-3.1 ~ AC-3.5 | UT | indicatorBuilder 和 ContentModifier 集成 |
| VM-6 | AC-4.1 ~ AC-4.4 | UT | 分组互斥完整链路 |
| VM-7 | AC-5.1 ~ AC-5.3 | UT + 手工 | 进出弹簧动画和 disabled 降级 |
| VM-8 | AC-6.1 ~ AC-6.3 | UT | 无障碍属性和操作 |
| VM-9 | AC-7.1 ~ AC-7.5 | C API UT | C API 属性设置 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC | @since |
|----------|---------|----------|--------|-----------|----------|---------|--------|
| Radio(options) | Public | group: string, value: string | RadioAttribute | N/A | 创建 Radio 组件 | AC-1.1 | 8 |
| RadioAttribute.checked(checked) | Public | boolean | RadioAttribute | N/A | 设置选中状态（只读） | AC-1.5 | 8 |
| RadioAttribute.radioStyle(value) | Public | RadioStyle | RadioAttribute | N/A | 选中指示器样式 | AC-2.1 | 10 |
| RadioAttribute.onChange(callback) | Public | (isChecked: boolean) => void | RadioAttribute | N/A | 选中状态变化回调 | AC-1.2 | 8 |
| RadioAttribute.contentModifier(modifier) | Public | ContentModifier<RadioConfiguration> | RadioAttribute | N/A | 自定义渲染 | AC-3.2 | 12 |
| RadioAttribute.indicatorType(value) | Public | RadioIndicatorType | RadioAttribute | N/A | 指示器类型 | AC-2.3, AC-2.4 | 12 |
| RadioAttribute.indicatorBuilder(builder) | Public | CustomBuilder | RadioAttribute | N/A | 自定义指示器 | AC-3.1 | 12 |
| NODE_RADIO_CHECKED | NDK/Public | .value[0].i32 | void | N/A | C API 选中状态 | AC-7.1 | NDK |
| NODE_RADIO_STYLE | NDK/Public | 复合属性 | void | N/A | C API 指示器样式 | AC-7.4 | NDK |
| NODE_RADIO_VALUE | NDK/Public | .string | void | N/A | C API 值标识 | AC-7.2 | NDK |
| NODE_RADIO_GROUP | NDK/Public | .string | void | N/A | C API 分组名称 | AC-7.3 | NDK |
| ARKUI_NODE_RADIO | NDK/Public | — | — | — | C API 节点类型=18 | AC-7.5 | NDK |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|---------|---------|
| 无 | — | — | — | — |

> 截至当前版本，Radio 未发现任何 @deprecated 或 @useinstead 标注的 API。

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
- **API 版本号策略:** 基础 API @since 8，radioStyle @since 10，contentModifier/indicatorType/indicatorBuilder @since 12，Static API @since 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 组件化 SO | Radio 已组件化为独立 SO（libarkui_radio.z.so），通过 RadioDynamicModule 入口 | AC-1.1 |
| GroupManager 互斥 | Radio 通过 GroupManager::UpdateRadioGroupValue 实现分组互斥，同组其他 Radio 自动取消选中 | AC-1.3, AC-4.1 ~ AC-4.3 |
| checked 只读 | checked 为只读属性，通过 API 设置不生效；选中状态仅由交互或联动改变 | AC-1.5 |
| InterpolatingSpring 动画 | 进出动画使用固定弹簧参数，开发者无法自定义 | AC-5.1, AC-5.2 |
| C API 节点类型 | ARKUI_NODE_RADIO=18 | AC-7.5 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 进出弹簧动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | ContentModifier 自定义节点在组件销毁时释放 | UT + Dump | 节点树 Dump |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | GroupManager 在动态增删 Radio 时不崩溃，分组互斥正确 | UT | radio 单测 |
| 问题定位 | hilog 标签覆盖关键路径（状态切换、分组互斥） | 代码审查 | — |

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
| 无障碍 | 是 | Radio 实现 IsCheckable/IsChecked/ActionSelect，ActionSelect 选中时触发分组互斥 | AC-6.1 ~ AC-6.3 |
| 大字体 | 是 | Radio 尺寸跟随系统字体缩放 | — |
| 深色模式 | 是 | 颜色属性通过 ResourceColor 支持主题跟随 | AC-2.1, AC-2.2 |
| 多窗口/分屏 | 否 | Radio 无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 12 新增 indicatorType/indicatorBuilder/contentModifier；需在文档中明确 | AC-2.3, AC-3.1, AC-3.2 |
| 生态兼容 | 是 | C API 属性子集限制需在 NDK 文档中明确 | AC-7.1 ~ AC-7.5 |

## 行为场景（Gherkin）

```gherkin
Feature: Radio 组件
  作为应用开发者
  我想要使用 Radio 组件实现单选交互
  以便在一组选项中实现互斥选择

  Scenario: Radio 点击选中
    Given Radio 组件以 checked=false 创建
    When 用户点击 Radio
    Then checked 变为 true
    And onChange 回调被触发，参数为 true
    And 选中指示器使用 InterpolatingSpring 弹簧动画进入

  Scenario: 分组互斥
    Given 两个 Radio 属于同一 group，Radio A 已选中
    When 用户点击 Radio B
    Then Radio B checked 变为 true
    And Radio A checked 变为 false
    And Radio A onChange 回调被触发，参数为 false
    And Radio A 选中指示器使用弹簧动画退出

  Scenario: Radio 选中后再次点击
    Given Radio 已选中 (checked=true)
    When 用户点击同一 Radio
    Then checked 保持 true（不可通过点击取消选中）

  Scenario: Disabled 状态
    Given Radio 组件以 enabled=false 创建
    When 用户点击 Radio
    Then checked 状态不变
    And onChange 不触发
    And 不触发进出动画

  Scenario: indicatorType 设置
    Given 设置 .indicatorType(RadioIndicatorType.TICK)
    Then 选中指示器为勾选标记样式

  Scenario: indicatorBuilder 自定义指示器
    Given 设置 .indicatorType(RadioIndicatorType.CUSTOM)
    And 设置 .indicatorBuilder(() => { Image($r('app.media.dot')) })
    When Radio 被选中
    Then 显示自定义指示器内容

  Scenario: indicatorBuilder 未设置 CUSTOM 类型时不生效
    Given 设置 .indicatorType(RadioIndicatorType.DOT) (非 CUSTOM)
    And 设置 .indicatorBuilder(builder)
    When Radio 被选中
    Then indicatorBuilder 不生效，显示默认 DOT 样式

  Scenario: ContentModifier 自定义渲染
    Given Radio 设置了 contentModifier
    When ContentModifier 激活
    Then 默认渲染被自定义 Builder 替换
    And 通过 RadioConfiguration { checked, enabled, triggerChange } 回调

  Scenario: C API 设置选中状态
    Given 通过 C API 创建 ARKUI_NODE_RADIO 节点
    When 设置 NODE_RADIO_CHECKED = 1
    Then Radio 选中状态为 true

  Scenario: 无障碍操作
    Given Radio 组件已创建
    When 无障碍服务执行 ActionSelect
    Then Radio checked 设为 true
    And 同组其他 Radio 自动取消选中
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
    query: "Radio GroupManager 分组互斥机制和 UpdateRadioGroupValue 调用链"
  - repo: "openharmony/ace_engine"
    query: "Radio indicatorType/indicatorBuilder 自定义指示器集成"
  - repo: "openharmony/ace_engine"
    query: "Radio InterpolatingSpring 进出弹簧动画参数和触发条件"
  - repo: "openharmony/ace_engine"
    query: "Radio C API radio_modifier 属性委托实现"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/radio.d.ts`
- KB 路由: `docs/kb/components/selector/radio.md`
- 源码入口: `frameworks/core/components_ng/pattern/radio/radio_pattern.cpp`
