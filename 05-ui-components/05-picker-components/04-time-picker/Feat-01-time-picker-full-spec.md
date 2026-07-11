# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | TimePicker 组件全量规格 |
| 特性编号 | Feat-01 |
| FuncID | 05-05-04 |
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
| ADDED | TimePicker 组件规格补录 | 覆盖 hour/minute/second、12/24 小时、事件 |
| ADDED | 范围、循环和级联规格补录 | 覆盖 start/end/selected/loop/enableCascade |
| ADDED | C API 规格补录 | 覆盖 `ARKUI_NODE_TIME_PICKER` 与 `NODE_TIME_PICKER_*` |

## 输入文档

- 设计文档: `arkui-specs/05-ui-components/05-picker-components/04-time-picker/design.md`
- KB 路由: `docs/pattern/time_picker/Time_Picker_Knowledge_Base.md`
- SDK 类型定义: `../../../interface/sdk-js/api/@internal/component/ets/time_picker.d.ts`, `../../../interface/sdk-js/api/arkui/component/timePicker.static.d.ets`
- 实现源码: `frameworks/core/components_ng/pattern/time_picker/`, `interfaces/native/native_node.h`

## 用户故事

### US-1: 创建 TimePicker 并选择时间

**角色**: 应用开发者
**期望**: 我想要使用 TimePicker 选择小时、分钟和可选秒
**价值**: 以便在表单和闹钟场景中选择时间

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `TimePicker(options?: TimePickerOptions)` THEN 创建 hour/minute 列，SDK 合同见 `time_picker.d.ts:221`，Model 创建见 `timepicker_model_ng.cpp:62` | 正常 |
| AC-1.2 | WHEN 未设置 `useMilitaryTime` THEN 按系统时间格式显示；SDK 属性说明见 `time_picker.d.ts:273`，实现缓存见 `timepicker_row_pattern.h:816` | 正常 |
| AC-1.3 | WHEN `format=HOUR_MINUTE_SECOND` THEN 创建 second 列并在 result 中包含 second，SDK 枚举见 `time_picker.d.ts:85` | 正常 |
| AC-1.4 | WHEN 设置 `selected` THEN Pattern 调用 `AdjustTime` 后保存选中时间，源码见 `timepicker_row_pattern.cpp:1799` | 正常 |

### US-2: 范围、循环和级联

**角色**: 应用开发者
**期望**: 我想要限制可选时间范围并控制 AM/PM 联动
**价值**: 以便实现有效时间段选择

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 设置 `start/end` THEN 仅 hour/minute 影响范围，SDK 说明见 `time_picker.d.ts:165` | 正常 |
| AC-2.2 | WHEN `selected` 小于 start 或大于 end THEN 分别调整为 start 或 end，源码见 `timepicker_row_pattern.cpp:1807` | 边界 |
| AC-2.3 | WHEN 设置非默认 start/end THEN loop 不生效，SDK 说明见 `time_picker.d.ts:172` 和 `time_picker.d.ts:188` | 边界 |
| AC-2.4 | WHEN `useMilitaryTime(false)` 且 `loop(true)` 且 `enableCascade(true)` THEN AM/PM 可随小时跨 11/12 边界联动，SDK 说明见 `time_picker.d.ts:598` | 正常 |

### US-3: 样式、事件和 C API

**角色**: 应用开发者
**期望**: 我想要设置 TimePicker 样式并监听时间变化
**价值**: 以便做业务联动和 Native 集成

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置三档 PickerTextStyle THEN 写入布局属性，SDK 见 `time_picker.d.ts:336` | 正常 |
| AC-3.2 | WHEN 设置 `dateTimeOptions` THEN hour/minute/second 前导 0 规则更新，Model 写入见 `timepicker_model_ng.cpp:297` | 正常 |
| AC-3.3 | WHEN 滚动动画完成 THEN 触发 `onChange(TimePickerResult)`，SDK 见 `time_picker.d.ts:479`，EventHub 绑定见 `timepicker_model_ng.cpp:329` | 正常 |
| AC-3.4 | WHEN 选项进入选中区域 THEN 触发 `onEnterSelectedArea`，SDK 见 `time_picker.d.ts:515` | 正常 |
| AC-3.5 | WHEN 使用 C API 监听 `NODE_TIME_PICKER_EVENT_ON_CHANGE` THEN event data 返回 hour/minute，声明见 `interfaces/native/native_node.h:11058` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3 | TASK-TIME-PICKER-01 | UT | `test/unittest/core/pattern/time_picker/time_picker_test_ng.cpp:1` |
| AC-2.1 ~ AC-2.4 | R-4, R-5, R-6 | TASK-TIME-PICKER-01 | UT | `test/unittest/core/pattern/time_picker/time_picker_display_12hour_test_ng.cpp:1` |
| AC-3.1 ~ AC-3.5 | R-7, R-8, R-9 | TASK-TIME-PICKER-01 | UT + C API UT | `test/unittest/capi/modifiers/time_picker_modifier_test.cpp:1` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 创建 TimePicker | 创建 hour/minute 列，format 含秒时创建 second 列 | showCount 来自 PickerTheme + buffer | AC-1.1, AC-1.3 |
| R-2 | 行为 | 未设置 useMilitaryTime | 使用系统时间格式 | SDK interface 注释“默认 24 小时”存在表述差异，记录为风险 | AC-1.2 |
| R-3 | 行为 | 设置 selected | `AdjustTime` 后保存 | 秒列存在时 second 可见 | AC-1.4 |
| R-4 | 行为 | 设置 start/end | 按 hour/minute 限制 options | seconds 不参与范围判断 | AC-2.1 |
| R-5 | 边界 | selected 超出范围 | 小于 start 返回 start，大于 end 返回 end | 闭区间 | AC-2.2 |
| R-6 | 边界 | start/end 为非默认 | loop/cascade 不按无限循环处理 | SDK 说明 start/end 会让 loop 不生效 | AC-2.3, AC-2.4 |
| R-7 | 行为 | 设置 dateTimeOptions | 更新前导 0 配置并标记刷新 | 仅 hour/minute/second 配置 | AC-3.2 |
| R-8 | 行为 | 滚动进入选中区或结束 | 分别触发 onEnterSelectedArea / onChange | onChange 不由双向绑定变量触发 | AC-3.3, AC-3.4 |
| R-9 | 行为 | C API 事件触发 | 返回 hour/minute 两个 i32 数据 | C API 不返回 second | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | Core UT | 创建、12/24、秒列、selected |
| VM-2 | AC-2.1 ~ AC-2.4 | Core UT | start/end、loop、cascade |
| VM-3 | AC-3.1 ~ AC-3.4 | Core UT | 样式、dateTimeOptions、事件 |
| VM-4 | AC-3.5 | C API UT | C API event data 格式 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| N/A | N/A | N/A | N/A | N/A | 本次无新增 API，仅补录已有 API 规格 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| N/A | N/A | 本次无 API 声明变更或废弃 | N/A | AC-1.1 |

## 接口规格

### 接口定义

**TimePicker(options?: TimePickerOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TimePicker(options?: TimePickerOptions): TimePickerAttribute` |
| 返回值 | `TimePickerAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `selected` | Date | 否 | 当前系统时间 | 超出 start/end 时裁剪 |
| `format` | TimePickerFormat | 否 | HOUR_MINUTE | HOUR_MINUTE 或 HOUR_MINUTE_SECOND |
| `start` | Date | 否 | 00:00:00 | 仅 hour/minute 生效 |
| `end` | Date | 否 | 23:59:59 | 仅 hour/minute 生效 |

**TimePickerAttribute 方法**

| 接口 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|---------|
| `useMilitaryTime(value)` | boolean/Optional | 设置 24 小时或 12 小时显示 | AC-1.2 |
| `loop(value)` | boolean/Optional | 设置循环，受 start/end 约束 | AC-2.3 |
| `dateTimeOptions(value)` | DateTimeOptions/Optional | 设置前导 0 | AC-3.2 |
| `onChange(callback)` | TimePickerResult callback | 滚动结束后触发 | AC-3.3 |
| `onEnterSelectedArea(callback)` | TimePickerResult callback | 选项进入选中区时触发 | AC-3.4 |
| `enableHapticFeedback/enableCascade(...)` | boolean/Optional | 设置触觉反馈和 AM/PM 联动 | AC-2.4 |

**C API**

| 接口 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|---------|
| `ARKUI_NODE_TIME_PICKER` | node type | 创建 TimePicker native node | AC-1.1 |
| `NODE_TIME_PICKER_SELECTED/START/END/USE_MILITARY_TIME/ENABLE_CASCADE` | `ArkUI_AttributeItem` | 设置或读取属性 | AC-2.1 |
| `NODE_TIME_PICKER_EVENT_ON_CHANGE` | event data hour/minute | 时间变化事件 | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否，本次只补录已有实现。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** TimePicker dynamic API since 8；TimePickerFormat since 11；dateTimeOptions/haptic since 12；start/end/cascade/Optional 重载 since 18；static API since 23。
- **API 版本号策略:** 按 SDK `@since` 标注；SDK 创建说明和实际默认 12/24 表述差异作为风险记录。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 合同优先 | API 签名以 d.ts/static d.ets 为准 | AC-1.1 |
| Pattern 行为准线 | 12/24、范围、级联、事件以源码为准 | AC-2.2, AC-2.4 |
| C API 不改 ABI | 只记录已有枚举和事件数据格式 | AC-3.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增列刷新路径 | UT | 现有 Pattern |
| 功耗 | 无后台任务 | 代码审查 | 无源码变更 |
| 内存 | 列节点由 UI 树管理 | UT | RefPtr/UI 树 |
| 安全 | haptic 权限按 SDK 提示由应用声明 | 代码审查 | `time_picker.d.ts:541` |
| 可靠性 | selected 超范围可恢复 | UT | R-5 |
| 可测试性 | AC 映射 UT/C API UT | 生成检查 | VM-1 ~ VM-4 |
| 自动化维测 | 复用 TimePicker UT | UT | `test/unittest/core/pattern/time_picker/` |
| 定界定位 | SDK/Bridge/Model/Pattern/C API 分层明确 | 代码审查 | design.md |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | portrait 默认显示行数按 PickerTheme | UT/手工 | `time_picker.d.ts:202` |
| 平板 | 横屏行数可能由系统配置决定 | SDK 提示横屏行数可变 | 手工 | `time_picker.d.ts:209` |
| 折叠屏 | 无额外差异 | 按窗口/方向走同一规则 | 手工 | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | TimePicker 有 accessibility UT | AC-1.1 |
| 大字体 | 是 | PickerTextStyle 支持字体大小 | AC-3.1 |
| 深色模式 | 是 | ResourceColor/Theme 跟随系统 | AC-3.1 |
| 多窗口/分屏 | 是 | 行数和布局受方向/窗口影响 | AC-1.1 |
| 多用户 | 否 | 无持久化数据 | N/A |
| 版本升级 | 是 | since 边界需保持 | AC-1.3 |
| 生态兼容 | 是 | ArkTS 与 C API 双通道合同保持 | AC-3.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: TimePicker 时间选择
  Scenario: selected 超出时间范围
    Given TimePicker 设置 start 和 end
    When selected 小于 start
    Then 当前选中时间调整为 start

  Scenario: 秒列显示
    Given format 为 HOUR_MINUTE_SECOND
    When TimePicker 构建完成
    Then hour、minute、second 三列可见
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
    query: "TimePicker TimePickerFormat start end loop enableCascade onChange C API implementation"
```

**关键文档:** `docs/pattern/time_picker/Time_Picker_Knowledge_Base.md`

