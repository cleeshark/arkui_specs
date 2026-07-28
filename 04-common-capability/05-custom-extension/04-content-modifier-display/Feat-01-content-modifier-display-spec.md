# 特性规格

> Func-04-05-04-Feat-01 信息展示类组件自定义内容：固化 DataPanel/Gauge/Progress/LoadingProgress/TextClock/TextTimer 六个展示组件的 contentModifier() 方法、Configuration 字段、triggerChange 回调、动态模块加载与 reset 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 信息展示类组件自定义内容 (ContentModifier for Display Components) |
| 特性编号 | Func-04-05-04-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 12 起支持动态版本 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/04-content-modifier-display/design.md` | Baselined |
| SDK API | `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | — |
| SDK 组件 | `docs/sdk/Component_API_Knowledge_Base_CN.md` | — |

---

## 用户故事

### US-1: DataPanel contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 DataPanel 设置自定义内容,
**以便** 自定义数据面板外观并保留数据展示语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `data_panel.d.ts:400` contentModifier() THEN DataPanelPattern 存储 makeFunc_ 并触发 FireBuilder | 正常 |
| AC-1.2 | WHEN BuildContentModifierNode 执行 THEN 从 DataPanelPaintProperty 读取 values 数组和 max（默认 100）构造 DataPanelConfiguration | 正常 |
| AC-1.3 | WHEN DataPanelConfiguration 定义于 `data_panel_model_ng.h:37` THEN 包含 values_(vector\<double\>) 和 maxValue_ 字段 | 边界 |

### US-2: Gauge contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 Gauge 设置自定义内容,
**以便** 自定义仪表盘外观并保留值范围语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `gauge.d.ts:440` contentModifier() THEN GaugePattern 存储 makeFunc_ 并触发 FireBuilder | 正常 |
| AC-2.2 | WHEN GaugeConfiguration 定义于 `gauge_model_ng.h:23` THEN 包含 value_/min_/max_ 字段 | 边界 |
| AC-2.3 | WHEN Gauge 值变更 THEN makeFunc_ 重新调用以更新 Configuration 快照 | 正常 |

### US-3: Progress contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 Progress 设置自定义内容,
**以便** 自定义进度条外观并保留进度值语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `progress.d.ts:881` contentModifier() THEN ProgressPattern 存储 makeFunc_ 并触发 FireBuilder | 正常 |
| AC-3.2 | WHEN ProgressConfiguration 定义于 `progress_date.h:110` THEN 包含 value_(默认 0) 和 total_(默认 100) 字段 | 边界 |
| AC-3.3 | WHEN ProgressConfiguration 构造 THEN value 默认为 0，total 默认为 100 | 边界 |

### US-4: LoadingProgress contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 LoadingProgress 设置自定义内容,
**以便** 自定义加载动画外观并保留启用状态语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `loading_progress.d.ts:160` contentModifier() THEN LoadingProgressPattern 存储 makeFunc_ 并触发 FireBuilder | 正常 |
| AC-4.2 | WHEN LoadingProgressConfiguration 定义于 `loading_progress_model_ng.h:28` THEN 包含 enableloading_ 字段（默认 true） | 边界 |
| AC-4.3 | WHEN enableLoading 默认为 true THEN Configuration 中 enableloading_ 默认为 true | 边界 |

### US-5: TextClock contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 TextClock 设置自定义内容,
**以便** 自定义时钟外观并保留时区与运行状态语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `text_clock.d.ts:457` contentModifier() THEN TextClockPattern 存储 makeFunc_ 并触发 FireBuilder | 正常 |
| AC-5.2 | WHEN TextClockConfiguration 定义于 `text_clock_model_ng.h:24` THEN 包含 timeZoneOffset_([-14,12])/started_(默认 true)/timeValue_ 字段 | 边界 |
| AC-5.3 | WHEN timeZoneOffset 超出 [-14,12] 范围 THEN 按系统约束处理 | 异常 |

### US-6: TextTimer contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 TextTimer 设置自定义内容,
**以便** 自定义计时器外观并保留计时状态语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `text_timer.d.ts:443` contentModifier() THEN TextTimerPattern 存储 makeFunc_ 并触发 FireBuilder | 正常 |
| AC-6.2 | WHEN TextTimerConfiguration 定义于 `text_timer_model_ng.h:24` THEN 包含 count_(默认 60000，max 86400000)/isCountDown_/started_/elapsedTime_/startTime_ 字段 | 边界 |
| AC-6.3 | WHEN count 超过 86400000 THEN 按最大值约束处理 | 异常 |

### US-7: 动态模块加载与 reset

**作为** 应用开发者,
**我想要** 重置 contentModifier 并了解动态模块加载机制,
**以便** 在运行时切换自定义内容与默认渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN makeFunc_ 为空 THEN FireBuilder 移除 contentModifierNode_ 并恢复默认渲染（`data_panel_pattern.cpp:93-96`） | 恢复 |
| AC-7.2 | WHEN 首次访问 contentModifier THEN GetDataPanelModifierWithCache 通过 DynamicModuleHelper 动态加载并缓存（`content_modifier_helper_accessor.cpp:132-147`） | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 data_panel_content_modifier_test_ng.cpp |
| AC-1.2 | US-1 | R-2 | 代码审查 data_panel_pattern.cpp:108-132 |
| AC-1.3 | US-1 | R-3 | 代码审查 data_panel_model_ng.h:37 |
| AC-2.1 | US-2 | R-4 | 单元测试 gauge_modifier_test_ng.cpp |
| AC-2.2 | US-2 | R-5 | 代码审查 gauge_model_ng.h:23 |
| AC-2.3 | US-2 | R-6 | 代码审查 gauge_pattern.cpp |
| AC-3.1 | US-3 | R-7 | 单元测试 progress_content_modifier_test_ng.cpp |
| AC-3.2 | US-3 | R-8 | 代码审查 progress_date.h:110 |
| AC-3.3 | US-3 | R-9 | 代码审查 progress.d.ts:893 |
| AC-4.1 | US-4 | R-10 | 单元测试 loading_progress_setbuilder_test_ng.cpp |
| AC-4.2 | US-4 | R-11 | 代码审查 loading_progress_model_ng.h:28 |
| AC-4.3 | US-4 | R-12 | 代码审查 loading_progress.d.ts:173 |
| AC-5.1 | US-5 | R-13 | 单元测试 text_clock_content_modifier_test_ng.cpp |
| AC-5.2 | US-5 | R-14 | 代码审查 text_clock_model_ng.h:24 |
| AC-5.3 | US-5 | R-15 | 代码审查 text_clock.d.ts:82 |
| AC-6.1 | US-6 | R-16 | 单元测试 text_timer_builder_test_ng.cpp |
| AC-6.2 | US-6 | R-17 | 代码审查 text_timer_model_ng.h:24 |
| AC-6.3 | US-6 | R-18 | 代码审查 text_timer.d.ts:96 |
| AC-7.1 | US-7 | R-19 | 代码审查 data_panel_pattern.cpp:93-96 |
| AC-7.2 | US-7 | R-20 | 代码审查 content_modifier_helper_accessor.cpp:132-147 |

## 规则定义

> **统一规则表。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `data_panel.d.ts:400` | DataPanel contentModifier 设置 makeFunc_ 并触发 FireBuilder | @since 12 | AC-1.1 |
| R-2 | 行为 | `data_panel_pattern.cpp:108-132` | BuildContentModifierNode 读取 values/max 构造 Configuration 并调用 makeFunc_ | values 默认 {0.0f}, max 默认 100 | AC-1.2 |
| R-3 | 边界 | `data_panel_model_ng.h:37` | DataPanelConfiguration 包含 values_(vector\<double\>&) 和 maxValue_ | — | AC-1.3 |
| R-4 | 行为 | `gauge.d.ts:440` | Gauge contentModifier 设置 makeFunc_ 并触发 FireBuilder | @since 12 | AC-2.1 |
| R-5 | 边界 | `gauge_model_ng.h:23` | GaugeConfiguration 包含 value_/min_/max_ | — | AC-2.2 |
| R-6 | 行为 | `gauge_pattern.cpp` | Gauge 值变更时 makeFunc_ 重新调用更新 Configuration 快照 | — | AC-2.3 |
| R-7 | 行为 | `progress.d.ts:881` | Progress contentModifier 设置 makeFunc_ 并触发 FireBuilder | @since 12 | AC-3.1 |
| R-8 | 边界 | `progress_date.h:110` | ProgressConfiguration 包含 value_/total_ | — | AC-3.2 |
| R-9 | 边界 | `progress.d.ts:893` | value 默认 0，total 默认 100 | — | AC-3.3 |
| R-10 | 行为 | `loading_progress.d.ts:160` | LoadingProgress contentModifier 设置 makeFunc_ 并触发 FireBuilder | @since 12 | AC-4.1 |
| R-11 | 边界 | `loading_progress_model_ng.h:28` | LoadingProgressConfiguration 包含 enableloading_ | — | AC-4.2 |
| R-12 | 边界 | `loading_progress.d.ts:173` | enableLoading 默认 true | — | AC-4.3 |
| R-13 | 行为 | `text_clock.d.ts:457` | TextClock contentModifier 设置 makeFunc_ 并触发 FireBuilder | @since 12 | AC-5.1 |
| R-14 | 边界 | `text_clock_model_ng.h:24` | TextClockConfiguration 包含 timeZoneOffset_/started_/timeValue_ | timeZoneOffset 范围 [-14,12], started 默认 true | AC-5.2 |
| R-15 | 异常 | `text_clock.d.ts:82` | timeZoneOffset 超出 [-14,12] 时按系统约束处理 | — | AC-5.3 |
| R-16 | 行为 | `text_timer.d.ts:443` | TextTimer contentModifier 设置 makeFunc_ 并触发 FireBuilder | @since 12 | AC-6.1 |
| R-17 | 边界 | `text_timer_model_ng.h:24` | TextTimerConfiguration 包含 count_/isCountDown_/started_/elapsedTime_/startTime_ | count 默认 60000, max 86400000 | AC-6.2 |
| R-18 | 异常 | `text_timer.d.ts:96` | count 超过 86400000 时按最大值约束处理 | — | AC-6.3 |
| R-19 | 恢复 | `data_panel_pattern.cpp:93-96` | makeFunc_ 为空时 FireBuilder 移除 contentModifierNode_ 恢复默认 | — | AC-7.1 |
| R-20 | 行为 | `content_modifier_helper_accessor.cpp:132-147` | GetDataPanelModifierWithCache 通过 DynamicModuleHelper 动态加载，std::call_once 缓存 | — | AC-7.2 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 DataPanel (AC-1.1~1.3) | 单元测试 + 代码审查 | DataPanelConfiguration 字段；BuildContentModifierNode 流程 |
| VM-2 | US-2 Gauge (AC-2.1~2.3) | 单元测试 + 代码审查 | GaugeConfiguration 字段；值变更快照更新 |
| VM-3 | US-3 Progress (AC-3.1~3.3) | 单元测试 + 代码审查 | ProgressConfiguration 字段；默认值 |
| VM-4 | US-4 LoadingProgress (AC-4.1~4.3) | 单元测试 + 代码审查 | LoadingProgressConfiguration 字段；默认值 |
| VM-5 | US-5 TextClock (AC-5.1~5.3) | 单元测试 + 代码审查 | TextClockConfiguration 字段；时区范围约束 |
| VM-6 | US-6 TextTimer (AC-6.1~6.3) | 单元测试 + 代码审查 | TextTimerConfiguration 字段；count 范围约束 |
| VM-7 | US-7 动态加载/reset (AC-7.1~7.2) | 代码审查 | makeFunc_ 为空恢复默认；动态模块加载缓存 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 单元测试 | `test/unittest/core/pattern/data_panel/data_panel_content_modifier_test_ng.cpp` |
| AC-1.2 | 代码审查 | `frameworks/core/components_ng/pattern/data_panel/data_panel_pattern.cpp:108-132` |
| AC-1.3 | 代码审查 | `frameworks/core/components_ng/pattern/data_panel/data_panel_model_ng.h:37` |
| AC-2.1 | 单元测试 | `test/unittest/core/pattern/gauge/gauge_modifier_test_ng.cpp` |
| AC-2.2 | 代码审查 | `frameworks/core/components_ng/pattern/gauge/gauge_model_ng.h:23` |
| AC-2.3 | 代码审查 | `frameworks/core/components_ng/pattern/gauge/gauge_pattern.cpp` |
| AC-3.1 | 单元测试 | `test/unittest/core/pattern/progress/progress_content_modifier_test_ng.cpp` |
| AC-3.2 | 代码审查 | `frameworks/core/components_ng/pattern/progress/progress_date.h:110` |
| AC-3.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/progress.d.ts:893` |
| AC-4.1 | 单元测试 | `test/unittest/core/pattern/loading_progress/loading_progress_setbuilder_test_ng.cpp` |
| AC-4.2 | 代码审查 | `frameworks/core/components_ng/pattern/loading_progress/loading_progress_model_ng.h:28` |
| AC-4.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/loading_progress.d.ts:173` |
| AC-5.1 | 单元测试 | `test/unittest/core/pattern/text_clock/text_clock_content_modifier_test_ng.cpp` |
| AC-5.2 | 代码审查 | `frameworks/core/components_ng/pattern/text_clock/text_clock_model_ng.h:24` |
| AC-5.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/text_clock.d.ts:82` |
| AC-6.1 | 单元测试 | `test/unittest/core/pattern/text_timer/text_timer_builder_test_ng.cpp` |
| AC-6.2 | 代码审查 | `frameworks/core/components_ng/pattern/text_timer/text_timer_model_ng.h:24` |
| AC-6.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/text_timer.d.ts:96` |
| AC-7.1 | 代码审查 | `frameworks/core/components_ng/pattern/data_panel/data_panel_pattern.cpp:93-96` |
| AC-7.2 | 代码审查 | `frameworks/bridge/declarative_frontend/arkts_native/content_modifier_helper_accessor.cpp:132-147` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/` 各组件 d.ts

#### 各组件 contentModifier 方法

| 组件 | 方法签名 | d.ts 行 | @since |
|------|----------|---------|--------|
| DataPanel | `contentModifier(modifier: ContentModifier<DataPanelConfiguration>): DataPanelAttribute` | data_panel.d.ts:400 | 12 |
| Gauge | `contentModifier(modifier: ContentModifier<GaugeConfiguration>): GaugeAttribute` | gauge.d.ts:440 | 12 |
| Progress | `contentModifier(modifier: ContentModifier<ProgressConfiguration>): ProgressAttribute` | progress.d.ts:881 | 12 |
| LoadingProgress | `contentModifier(modifier: ContentModifier<LoadingProgressConfiguration>): LoadingProgressAttribute` | loading_progress.d.ts:160 | 12 |
| TextClock | `contentModifier(modifier: ContentModifier<TextClockConfiguration>): TextClockAttribute` | text_clock.d.ts:457 | 12 |
| TextTimer | `contentModifier(modifier: ContentModifier<TextTimerConfiguration>): TextTimerAttribute` | text_timer.d.ts:443 | 12 |

#### Configuration 类型定义

| Configuration | 字段 | 回调 | d.ts 行 |
|---------------|------|------|---------|
| DataPanelConfiguration | values: number[], maxValue: number | — | data_panel.d.ts:244 |
| GaugeConfiguration | value: number, min: number, max: number | — | gauge.d.ts:196 |
| ProgressConfiguration | value: number(默认0), total: number(默认100) | — | progress.d.ts:893 |
| LoadingProgressConfiguration | enableLoading: boolean(默认true) | — | loading_progress.d.ts:173 |
| TextClockConfiguration | timeZoneOffset: number([-14,12]), started: boolean(默认true), timeValue: Date | — | text_clock.d.ts:82 |
| TextTimerConfiguration | count: number(默认60000,max86400000), isCountDown: boolean, started: boolean, elapsedTime: number | — | text_timer.d.ts:96 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | 所有展示组件 contentModifier 动态版本首次引入 | 新增能力，无兼容性问题 | — |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 三层架构 | ContentModifier（基类）-Configuration（状态快照）-Pattern（apply 机制）三层分离 |
| Configuration 只读快照 | Configuration 字段为构建时快照，trigger 回调触发原生行为后需重新构建 Configuration |
| 动态模块加载 | ContentModifier 实现通过 DynamicModuleHelper 动态加载，std::call_once 保证单次 |
| 节点挂载位置 | contentModifierNode_ 挂载到 host 子节点位置 0，保留组件行为框架 |
| 时间字段重建 | TextClock timeValue 和 TextTimer elapsedTime 变更触发 makeFunc_ 重新调用 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | BuildContentModifierNode 在属性变更时调用，开销应保持 O(1) |
| 可调试性 | 动态模块加载失败时回退默认渲染，不中断应用 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 无障碍 | ContentModifier 自定义内容由开发者负责无障碍属性设置 |
| 大字体 | 无差异，自定义内容由开发者控制布局 |
| 深色模式 | 无差异，自定义内容颜色由开发者控制 |
| 多窗口分屏 | 无差异 |
| 多用户 | 无差异 |
| 版本升级 | 是，API 12 版本演进引入展示组件 contentModifier |
| 生态兼容 | 是，动态模块加载需 DynamicModuleHelper 支持 |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 业务规则/功能规则/异常规则/恢复契约编号连续且可追溯到源码
- [x] API 变更分析基于真实 SDK 定义文件（各组件 d.ts）
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/base/modifier.h` | ContentModifier 基类（onDraw/AttachProperty/SetContentChange） |
| `frameworks/core/components_ng/pattern/data_panel/data_panel_pattern.cpp` | DataPanel Pattern apply 机制（FireBuilder/BuildContentModifierNode） |
| `frameworks/core/components_ng/pattern/data_panel/data_panel_model_ng.h` | DataPanelConfiguration（values_/maxValue_） |
| `frameworks/core/components_ng/pattern/gauge/gauge_model_ng.h` | GaugeConfiguration（value_/min_/max_） |
| `frameworks/core/components_ng/pattern/progress/progress_date.h` | ProgressConfiguration（value_/total_） |
| `frameworks/core/components_ng/pattern/loading_progress/loading_progress_model_ng.h` | LoadingProgressConfiguration（enableloading_） |
| `frameworks/core/components_ng/pattern/text_clock/text_clock_model_ng.h` | TextClockConfiguration（timeZoneOffset_/started_/timeValue_） |
| `frameworks/core/components_ng/pattern/text_timer/text_timer_model_ng.h` | TextTimerConfiguration（count_/isCountDown_/started_/elapsedTime_/startTime_） |
| `frameworks/bridge/declarative_frontend/arkts_native/content_modifier_helper_accessor.cpp` | ContentModifierDataPanelImpl + 动态加载缓存 |
| `frameworks/core/components_ng/pattern/data_panel/bridge/data_panel_content_modifier_helper.h` | C-API GENERATED 结构体 |
| `interface/sdk-js/api/@internal/component/ets/data_panel.d.ts` | DataPanel SDK API 定义 |
| `interface/sdk-js/api/@internal/component/ets/gauge.d.ts` | Gauge SDK API 定义 |
| `interface/sdk-js/api/@internal/component/ets/progress.d.ts` | Progress SDK API 定义 |
| `interface/sdk-js/api/@internal/component/ets/loading_progress.d.ts` | LoadingProgress SDK API 定义 |
| `interface/sdk-js/api/@internal/component/ets/text_clock.d.ts` | TextClock SDK API 定义 |
| `interface/sdk-js/api/@internal/component/ets/text_timer.d.ts` | TextTimer SDK API 定义 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/data_panel/data_panel_content_modifier_test_ng.cpp` | DataPanel ContentModifier 单元测试 |
| `test/unittest/core/pattern/progress/progress_content_modifier_test_ng.cpp` | Progress ContentModifier 单元测试 |
| `test/unittest/core/pattern/text_clock/text_clock_content_modifier_test_ng.cpp` | TextClock ContentModifier 单元测试 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | SDK API 知识库 |
| `docs/sdk/Component_API_Knowledge_Base_CN.md` | 组件 API 知识库 |
