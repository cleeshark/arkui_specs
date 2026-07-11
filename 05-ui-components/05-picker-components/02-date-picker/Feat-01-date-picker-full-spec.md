# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | DatePicker 组件全量规格 |
| 特性编号 | Feat-01 |
| FuncID | 05-05-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 8 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | DatePicker 组件规格补录 | 覆盖创建、年/月/日列、模式、事件 |
| ADDED | 范围、农历和循环规格补录 | 覆盖 start/end/selected/lunar/canLoop |
| ADDED | C API 规格补录 | 覆盖 `ARKUI_NODE_DATE_PICKER` 与 `NODE_DATE_PICKER_*` |

## 输入文档

- 设计文档: `arkui-specs/05-ui-components/05-picker-components/02-date-picker/design.md`
- KB 路由: `docs/pattern/picker/Date_Picker_Knowledge_Base.md`
- SDK 类型定义: `../../../interface/sdk-js/api/@internal/component/ets/date_picker.d.ts`, `../../../interface/sdk-js/api/arkui/component/datePicker.static.d.ets`
- 实现源码: `frameworks/core/components_ng/pattern/date_picker/`, `interfaces/native/native_node.h`

## 用户故事

### US-1: 创建 DatePicker 并选择日期

**角色**: 应用开发者
**期望**: 我想要使用 DatePicker 选择日期并接收变化事件
**价值**: 以便在表单和设置页中选择日期

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `DatePicker(options?: DatePickerOptions)` THEN 创建 DatePicker 节点和年/月/日列，SDK 合同见 `date_picker.d.ts:232`，Model 创建见 `datepicker_model_ng.cpp:67` | 正常 |
| AC-1.2 | WHEN 未设置 start/end THEN 默认范围为 1970-01-01 到 2100-12-31，SDK 见 `date_picker.d.ts:140` | 正常 |
| AC-1.3 | WHEN 设置 `selected` THEN Pattern 保存选中日期并刷新列，Model 写入见 `datepicker_model_ng.cpp:372` | 正常 |
| AC-1.4 | WHEN 滚动完成且刷新为 true THEN 触发 `onDateChange` 和兼容 `onChange` 路径，源码见 `datepicker_pattern.cpp:1351` | 正常 |

### US-2: 范围、模式和循环

**角色**: 应用开发者
**期望**: 我想要约束日期范围并控制列显示模式
**价值**: 以便限制可选日期并适配年月或月日场景

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `start > end` THEN 阳历和农历范围恢复默认 start/end，源码见 `datepicker_pattern.cpp:2844` 和 `datepicker_pattern.cpp:2869` | 异常 |
| AC-2.2 | WHEN 设置 `mode=YEAR_AND_MONTH` 或 `MONTH_AND_DAY` THEN 按 `DatePickerMode` 显示两列，SDK 枚举见 `date_picker.d.ts:82`，Model 写入见 `datepicker_model_ng.cpp:382` | 正常 |
| AC-2.3 | WHEN 设置 start/end 中任一范围 THEN `canLoop` 在 `OnModifyDone` 中强制按 false 处理，源码见 `datepicker_pattern.cpp:479` | 边界 |
| AC-2.4 | WHEN 设置 `canLoop(undefined)` THEN 使用默认 true；WHEN 有范围 THEN 仍按 AC-2.3 处理，SDK 默认见 `date_picker.d.ts:476` | 边界 |

### US-3: 农历、本地化和样式

**角色**: 应用开发者
**期望**: 我想要设置农历显示、本地化顺序和文本样式
**价值**: 以便满足本地化日期展示

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `lunar(true)` 且语言条件支持 THEN Pattern 使用农历列构建；阳历列构建源码见 `datepicker_pattern.cpp:2510`，农历列构建见 `datepicker_pattern.cpp:2440` | 正常 |
| AC-3.2 | WHEN 当前语言影响日期顺序 THEN Model 按 `DateTimeSequence` 设置列顺序，`ar` 语言设置 LTR，源码见 `datepicker_model_ng.cpp:78` | 正常 |
| AC-3.3 | WHEN 设置 `disappearTextStyle/textStyle/selectedTextStyle` THEN 三档文本样式写入 LayoutProperty，SDK 见 `date_picker.d.ts:307` | 正常 |
| AC-3.4 | WHEN 设置 `enableHapticFeedback` THEN Pattern 保存触觉反馈开关，Model 写入见 `datepicker_model_ng.cpp:400` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3 | TASK-DATE-PICKER-01 | UT | `test/unittest/core/pattern/picker/date_picker_test_ng.cpp:1` |
| AC-2.1 ~ AC-2.4 | R-4, R-5, R-6 | TASK-DATE-PICKER-01 | UT | `test/unittest/core/pattern/picker/date_picker_order_test.cpp:1` |
| AC-3.1 ~ AC-3.4 | R-7, R-8, R-9 | TASK-DATE-PICKER-01 | UT + 手工 | `test/unittest/core/pattern/picker/date_picker_test_tojson.cpp:1` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 创建 DatePicker | 创建年/月/日列并按语言顺序挂载 | showCount 来自 PickerTheme + buffer | AC-1.1 |
| R-2 | 行为 | 设置 selected | Pattern 保存选中日期并刷新 LayoutProperty | Date 受 start/end 约束 | AC-1.3 |
| R-3 | 行为 | 滚动结束 refresh=true | 触发事件，onChange 返回 DatePickerResult，onDateChange 返回 Date | `onChange` deprecated since 10 | AC-1.4 |
| R-4 | 异常 | start > end | 恢复默认范围 | 阳历和农历均处理 | AC-2.1 |
| R-5 | 行为 | 设置 DatePickerMode | 按 DATE/YEAR_AND_MONTH/MONTH_AND_DAY 控制列显示 | API since 18 | AC-2.2 |
| R-6 | 边界 | start/end 已设置 | canLoop 按 false 处理 | 用户设置 true 不覆盖范围约束 | AC-2.3, AC-2.4 |
| R-7 | 行为 | lunar=true 且语言支持 | 构建农历 year/month/day options | 不支持时回阳历路径 | AC-3.1 |
| R-8 | 行为 | 语言为不同 locale | 日期列顺序按 locale 调整 | `ar` 设置 LTR | AC-3.2 |
| R-9 | 行为 | 设置文本样式/haptic | 写入 LayoutProperty 或 Pattern 状态 | undefined 使用默认 | AC-3.3, AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | Core UT | 创建列、selected、事件 |
| VM-2 | AC-2.1 ~ AC-2.4 | Core UT | start/end、mode、canLoop |
| VM-3 | AC-3.1 ~ AC-3.4 | Core UT + 手工 | 农历、本地化、样式、haptic |
| VM-4 | C API 属性/事件 | C API UT | `date_picker_modifier_test.cpp` |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| N/A | N/A | N/A | N/A | N/A | 本次无新增 API，仅补录已有 API 规格 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `DatePickerAttribute.onChange` | 已废弃（since 10） | 仍可触发旧 DatePickerResult 回调 | 新代码使用 `onDateChange(Callback<Date>)` | AC-1.4 |

## 接口规格

### 接口定义

**DatePicker(options?: DatePickerOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `DatePicker(options?: DatePickerOptions): DatePickerAttribute` |
| 返回值 | `DatePickerAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-2.1, AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `start` | Date | 否 | 1970-01-01 | 1900-01-31 ~ 2100-12-31 |
| `end` | Date | 否 | 2100-12-31 | 1900-01-31 ~ 2100-12-31，start <= end |
| `selected` | Date | 否 | 当前系统日期 | 超出范围时按范围裁剪 |
| `mode` | DatePickerMode | 否 | DATE | API 18 起支持三种模式 |

**DatePickerAttribute 方法**

| 接口 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|---------|
| `lunar(value)` | boolean/Optional<boolean> | 控制农历显示 | AC-3.1 |
| `disappearTextStyle/textStyle/selectedTextStyle(style)` | PickerTextStyle/Optional | 设置三档文本样式 | AC-3.3 |
| `onChange(callback)` | `(DatePickerResult) => void` | 历史兼容事件，已废弃 | AC-1.4 |
| `onDateChange(callback)` | `Callback<Date>` | 推荐日期变化事件 | AC-1.4 |
| `enableHapticFeedback(enable)` | Optional<boolean> | 设置触觉反馈，硬件相关 | AC-3.4 |
| `canLoop(isLoop)` | Optional<boolean> | 设置循环，受 start/end 范围覆盖 | AC-2.3 |

**C API**

| 接口 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|---------|
| `ARKUI_NODE_DATE_PICKER` | node type | 创建 DatePicker native node | AC-1.1 |
| `NODE_DATE_PICKER_LUNAR/START/END/SELECTED/MODE/CAN_LOOP` | `ArkUI_AttributeItem` | 设置或读取属性 | AC-2.1, AC-2.2 |
| `NODE_DATE_PICKER_EVENT_ON_DATE_CHANGE` | event data year/month/day，month 为 0-based | 日期变化事件 | AC-1.4 |

## 兼容性声明

- **已有 API 行为变更:** 否，本次只补录已有实现。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** DatePicker dynamic API since 8；样式 API since 10；DatePickerMode/haptic since 18；canLoop since 20；static API since 23。
- **API 版本号策略:** 按 SDK `@since` 标注，`onChange` 保留 deprecated since 10 说明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 合同优先 | API 签名以 d.ts/static d.ets 为准 | AC-1.1 |
| Pattern 行为准线 | 范围、循环、农历、事件按源码记录 | AC-2.1, AC-3.1 |
| C API ABI 不变 | 只记录已有枚举和事件数据格式 | AC-1.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增滚轮刷新路径 | UT | 现有 Pattern |
| 功耗 | 无后台任务 | 代码审查 | 无源码变更 |
| 内存 | 列节点由 UI 树管理 | UT | RefPtr/UI 树 |
| 安全 | 不新增权限 | 代码审查 | ArkUI 本地组件 |
| 可靠性 | start/end 逆序恢复默认 | UT | R-4 |
| 可测试性 | AC 映射 UT/C API UT | 生成检查 | VM-1 ~ VM-4 |
| 自动化维测 | 复用 DatePicker UT | UT | `test/unittest/core/pattern/picker/` |
| 定界定位 | SDK/Bridge/Model/Pattern/C API 分层明确 | 代码审查 | design.md |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | portrait 默认行数按 PickerTheme | UT/手工 | `date_picker.d.ts:213` |
| 平板 | 横屏显示行数可能由系统配置决定 | SDK 提示横屏行数可变 | 手工 | `date_picker.d.ts:220` |
| 折叠屏 | 无额外差异 | 按窗口/方向走同一规则 | 手工 | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 列切换时更新 accessibility text | AC-1.1 |
| 大字体 | 是 | PickerTextStyle 支持字体大小 | AC-3.3 |
| 深色模式 | 是 | ResourceColor/Theme 跟随系统 | AC-3.3 |
| 多窗口/分屏 | 是 | window fullscreen 状态影响 Pattern 内部状态 | AC-1.1 |
| 多用户 | 否 | 无持久化数据 | N/A |
| 版本升级 | 是 | deprecated 和 since 边界需保持 | AC-1.4 |
| 生态兼容 | 是 | ArkTS 与 C API 双通道合同保持 | AC-1.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DatePicker 日期选择
  Scenario: 有范围时禁止循环
    Given DatePicker 设置 start 和 end
    When 开发者设置 canLoop(true)
    Then 滚轮在 Pattern 中按非循环处理

  Scenario: 选择日期触发事件
    Given DatePicker 设置 onDateChange
    When 用户滚动并停在新日期
    Then onDateChange 收到 Date
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
    query: "DatePicker DatePickerMode lunar canLoop onDateChange C API implementation"
```

**关键文档:** `docs/pattern/picker/Date_Picker_Knowledge_Base.md`

