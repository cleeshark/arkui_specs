# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | CalendarPicker 组件全量规格 |
| 特性编号 | Feat-01 |
| FuncID | 05-05-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 10 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | CalendarPicker 组件规格补录 | 覆盖 `CalendarPicker(options?)`、entry、弹窗、事件 |
| ADDED | 日期范围与禁用日期规格补录 | 覆盖 `selected/start/end/disabledDateRange/markToday` |
| ADDED | C API 规格补录 | 覆盖 `ARKUI_NODE_CALENDAR_PICKER`、`NODE_CALENDAR_PICKER_*`、事件 |

## 输入文档

- 设计文档: `arkui-specs/05-ui-components/05-picker-components/01-calendar-calendar-picker/design.md`
- KB 路由: `docs/pattern/calendar_picker/Calendar_Picker_Knowledge_Base.md`
- SDK 类型定义: `../../../interface/sdk-js/api/@internal/component/ets/calendar_picker.d.ts`, `../../../interface/sdk-js/api/arkui/component/calendarPicker.static.d.ets`
- 实现源码: `frameworks/core/components_ng/pattern/calendar_picker/`, `interfaces/native/native_node.h`

## 用户故事

### US-1: 创建入口与基础显示

**角色**: 应用开发者
**期望**: 我想要创建 CalendarPicker 并配置选中日期、入口样式和对齐方式
**价值**: 以便在页面内提供可点击的日期入口

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `CalendarPicker(options?: CalendarOptions)` THEN 创建 CalendarPicker entry，API 合同来自 `calendar_picker.d.ts:182`，实现创建入口节点见 `calendar_picker_model_ng.cpp:49` | 正常 |
| AC-1.2 | WHEN 设置 `hintRadius` 在 0.0 ~ 16.0 THEN 选中态背景按该半径显示；WHEN 为负数或大于 16 THEN 使用默认 16.0，SDK 约束见 `calendar_picker.d.ts:75` | 边界 |
| AC-1.3 | WHEN 设置 `edgeAlign(START/CENTER/END, offset)` THEN 弹窗相对 entry 对齐；WHEN RTL 布局 THEN START/END 翻转且 x offset 取反，源码见 `calendar_picker_pattern.cpp:223` | 正常 |
| AC-1.4 | WHEN 设置 `textStyle` THEN entry 文本颜色、字号、字重按 PickerTextStyle 生效，Model 写入见 `calendar_picker_model_ng.cpp:326` | 正常 |

### US-2: 日期范围与禁用日期

**角色**: 应用开发者
**期望**: 我想要限制 CalendarPicker 可选择日期范围并禁用部分日期
**价值**: 以便满足预约、日程等业务约束

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 未设置 `selected` THEN 使用当前系统日期；WHEN `selected` 超出 `start/end` THEN 调整到合法范围，SDK 约束见 `calendar_picker.d.ts:101`，Model 调整见 `calendar_picker_model_ng.cpp:776` | 边界 |
| AC-2.2 | WHEN 设置 `start/end` 且 start <= end THEN 可选范围限制为闭区间，SDK 约束见 `calendar_picker.d.ts:118` | 正常 |
| AC-2.3 | WHEN `disabledDateRange` 中任一区间缺少 start/end 或 end < start THEN 该区间不生效，SDK 说明见 `calendar_picker.d.ts:150`，解析策略见 `calendar_picker_utils.cpp:56` | 异常 |
| AC-2.4 | WHEN 键盘上下调整日期且中间存在 disabledDateRange THEN 跳过禁用日期，源码见 `picker_data.cpp:193` | 正常 |

### US-3: 弹窗交互与事件

**角色**: 终端用户
**期望**: 我想要点击入口打开日历并选择日期
**价值**: 以便完成日期选择操作

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 点击 entry 的日期区域 THEN 调用 `ShowDialog` 打开日历弹窗，源码见 `calendar_picker_pattern.cpp:381` 和 `calendar_picker_pattern.cpp:520` | 正常 |
| AC-3.2 | WHEN 设置 `markToday(true)` THEN 弹窗数据携带 markToday，Model 设置见 `calendar_picker_model_ng.cpp:888`，ShowDialog 传参见 `calendar_picker_pattern.cpp:520` | 正常 |
| AC-3.3 | WHEN 选择日期 THEN 触发 `onChange(callback: Date)`，SDK 合同见 `calendar_picker.d.ts:288`，事件路径见 `calendar_picker_pattern.cpp:489` | 正常 |
| AC-3.4 | WHEN 使用 C API 监听 `NODE_CALENDAR_PICKER_EVENT_ON_CHANGE` THEN event data 返回 year/month/day，声明见 `interfaces/native/native_node.h:11093` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3 | TASK-CALENDAR-PICKER-01 | UT | `test/unittest/core/pattern/calendar_picker/calendar_picker_pattern_test_ng.cpp:620` |
| AC-2.1 ~ AC-2.4 | R-4, R-5, R-6 | TASK-CALENDAR-PICKER-01 | UT | `test/unittest/core/pattern/calendar_picker/calendar_picker_pattern_test.cpp:158` |
| AC-3.1 ~ AC-3.4 | R-7, R-8, R-9 | TASK-CALENDAR-PICKER-01 | UT + C API UT | `test/unittest/core/pattern/calendar_picker/calendar_dialog_view_test_ng.cpp:158`, `test/unittest/capi/modifiers/calendar_picker_modifier_test.cpp:144` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `CalendarPicker(options?)` | 创建 CalendarPicker entry 和日期文本子节点 | API since 10 dynamic, since 23 static | AC-1.1 |
| R-2 | 边界 | `hintRadius` 为 0、0~16、负数、大于 16 | 0 为直角，0~16 为圆角，非法使用默认 16 | [0.0, 16.0] | AC-1.2 |
| R-3 | 行为 | `edgeAlign` 在 RTL 下设置 START/END | 对齐方向翻转，x offset 取反 | RTL 仅影响水平方向 | AC-1.3 |
| R-4 | 边界 | `selected` 超出 `start/end` | 调整到合法范围 | Date 0001-01-01 ~ 5000-12-31 | AC-2.1 |
| R-5 | 异常 | disabled range 缺 start/end 或 end < start | 该区间不生效 | 不影响其他合法区间 | AC-2.3 |
| R-6 | 行为 | 键盘加减日期遇到禁用区间 | 跳过所有禁用日期 | 仅对合法 disabledDateRange 生效 | AC-2.4 |
| R-7 | 行为 | 点击 entry | 打开 CalendarDialog，已有弹窗时不重复创建 | 弹窗尺寸受窗口约束 | AC-3.1 |
| R-8 | 行为 | 选择日期 | 触发 ArkTS `onChange(Date)` | 双向绑定状态变化不触发 onChange | AC-3.3 |
| R-9 | 行为 | C API 事件触发 | 返回 year/month/day 三个 u32 数据 | `NODE_CALENDAR_PICKER_EVENT_ON_CHANGE` | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | Core UT | entry 创建、hintRadius、edgeAlign、textStyle |
| VM-2 | AC-2.1 ~ AC-2.4 | Core UT | start/end/selected/disabledDateRange |
| VM-3 | AC-3.1 ~ AC-3.3 | Core UT + 手工 | 弹窗打开、markToday、事件 |
| VM-4 | AC-3.4 | C API UT | C API event data 格式 |

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

**CalendarPicker(options?: CalendarOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `CalendarPicker(options?: CalendarOptions): CalendarPickerAttribute` |
| 返回值 | `CalendarPickerAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-2.1, AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `hintRadius` | number/Resource | 否 | 16.0 | 0.0 ~ 16.0；非法使用默认 |
| `selected` | Date | 否 | 当前系统日期 | 0001-01-01 ~ 5000-12-31，超出范围时调整 |
| `start/end` | Date | 否 | 0001-01-01 / 5000-12-31 | start <= end |
| `disabledDateRange` | DateRange[] | 否 | 空 | 区间 start/end 有效且 start <= end |

**CalendarPickerAttribute 方法**

| 接口 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|---------|
| `edgeAlign(alignType, offset?)` | alignType 默认 END，offset 默认 `{dx:0, dy:0}` | 控制弹窗相对 entry 对齐，RTL 翻转 START/END | AC-1.3 |
| `textStyle(style)` | PickerTextStyle，可 Optional | 设置 entry 文本样式，undefined 使用默认 | AC-1.4 |
| `onChange(callback)` | `Callback<Date>` 或 Optional | 日期选择后触发，undefined 不使用回调 | AC-3.3 |
| `markToday(enabled)` | boolean | 控制弹窗是否高亮当天 | AC-3.2 |

**C API**

| 接口 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|---------|
| `ARKUI_NODE_CALENDAR_PICKER` | node type | 创建 CalendarPicker native node | AC-1.1 |
| `NODE_CALENDAR_PICKER_HINT_RADIUS/SELECTED/START/END/DISABLED_DATE_RANGE/MARK_TODAY` | `ArkUI_AttributeItem` | 设置或读取 CalendarPicker 属性 | AC-1.2, AC-2.2, AC-2.3 |
| `NODE_CALENDAR_PICKER_EVENT_ON_CHANGE` | event data year/month/day | 日期变化事件 | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否，本次只补录已有实现。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** CalendarPicker dynamic API since 10；start/end Optional since 18；disabledDateRange/markToday since 19；static API since 23。
- **API 版本号策略:** 按 SDK `@since` 标注，C API 按 `native_node.h` 注释记录。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 为外部合同 | API 签名以 `calendar_picker.d.ts` / static d.ets 为准 | AC-1.1 |
| Pattern 为行为准线 | 弹窗、键盘、RTL、事件以 Pattern 源码为准 | AC-1.3, AC-3.1 |
| C API 不改 ABI | 仅记录已有 `native_node.h` 枚举 | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 打开弹窗和日期切换不新增额外耗时路径 | 手工/UT | 现有 Pattern/Dialog 流程 |
| 功耗 | 无新增后台任务 | 代码审查 | 无新增源码 |
| 内存 | 弹窗关闭后 UI 节点由 UI 树释放 | UT | RefPtr/UI 树 |
| 安全 | 不新增权限或跨进程输入 | 代码审查 | 本地 UI 组件 |
| 可靠性 | 非法日期区间按默认/忽略策略恢复 | UT | R-4, R-5 |
| 可测试性 | AC 均映射 UT/C API UT | 生成检查 | VM-1 ~ VM-4 |
| 自动化维测 | 复用现有 UT 目标 | UT | `calendar_picker_test_ng` |
| 定界定位 | API/Bridge/Model/Pattern/C API 分层证据明确 | 代码审查 | design.md |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | entry + dialog | 手工/UT | `calendar_picker_pattern.cpp:381` |
| 平板 | 弹窗宽度受窗口限制 | CalendarPickerDialog 最小宽度由 SDK 说明 | 手工 | `calendar_picker.d.ts:330` |
| 折叠屏 | 无额外差异 | 多窗口按弹窗布局约束 | 手工 | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Pattern 提供 accessibility text | AC-1.1 |
| 大字体 | 是 | textStyle 使用 PickerTextStyle | AC-1.4 |
| 深色模式 | 是 | ResourceColor/Theme 跟随系统主题 | AC-1.4 |
| 多窗口/分屏 | 是 | 弹窗受窗口宽度约束 | AC-3.1 |
| 多用户 | 否 | 无用户数据持久化 | N/A |
| 版本升级 | 是 | API 18/19/23/26 边界需保持 | AC-2.2 |
| 生态兼容 | 是 | ArkTS 与 C API 双通道保持现有合同 | AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: CalendarPicker 日期选择
  Scenario: 选择非禁用日期
    Given CalendarPicker 设置 start/end 和 disabledDateRange
    When 用户打开弹窗并选择一个合法日期
    Then entry 显示该日期
    And onChange 回调收到 Date

  Scenario: 键盘跳过禁用日期
    Given disabledDateRange 覆盖当前日期的下一天
    When 用户按向上键增加日期
    Then 选中日期跳过禁用日期
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
    query: "CalendarPicker CalendarOptions disabledDateRange edgeAlign onChange C API implementation"
```

**关键文档:** `docs/pattern/calendar_picker/Calendar_Picker_Knowledge_Base.md`

