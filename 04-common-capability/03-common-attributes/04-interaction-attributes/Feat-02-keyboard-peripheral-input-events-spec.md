# 特性规格

> Func-04-03-04-Feat-02 固化通用组件的触摸响应热区、触摸控制和事件独占配置；不定义命中测试或手势裁决算法。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 触摸热区、触摸控制与事件独占 |
| 特性编号 | Func-04-03-04-Feat-02 |
| 所属 Epic | 无（既有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起，按 API 声明扩展至 API 15 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | Feat-02 职责范围 | 由键盘与外设回调调整为触摸热区、触摸控制和事件独占，以匹配通用交互属性功能域。 |

## 输入文档

- `design.md`
- `<OH_ROOT>/interface_sdk-js/api/@internal/component/ets/common.d.ts:18892-19015,24522-24534`
- `<OH_ROOT>/interface_sdk-js/api/arkui/component/common.static.d.ets:11592-11625,14185-14196`
- `<OH_ROOT>/frameworks/core/components_ng/base/view_abstract.cpp:3557-3583,9850-9861,9900-9909`
- `<OH_ROOT>/frameworks/core/components_ng/event/gesture_event_hub.cpp:1254-1256,1780-1813`

## 用户故事

### US-1: 配置触摸响应热区

作为应用开发者，我想要为通用组件设置触摸响应热区，以便组件可在声明的区域内参与触摸响应。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `responseRegion(value)` THEN SDK 声明的区域值被桥接到组件的响应区域配置。 | 正常 |
| AC-1.2 | WHEN 设置 `responseRegionList(regions)` THEN SDK 声明的高级区域列表被作为响应区域列表配置。 | 正常 |
| AC-1.3 | WHEN 未设置响应区域或传入空列表 THEN 本特性不合成热区；具体命中测试结果由既有框架流程决定。 | 边界 |

### US-2: 控制触摸参与和事件独占

作为应用开发者，我想要控制组件是否接收触摸以及是否独占事件，以便组合组件按既有的手势事件 Hub 语义工作。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `touchable(value)` THEN `ViewAbstract` 将触摸控制值写入 `GestureEventHub`。 | 正常 |
| AC-2.2 | WHEN 设置 `monopolizeEvents(monopolize)` THEN `ViewAbstract` 将独占标志写入 `GestureEventHub`。 | 正常 |
| AC-2.3 | WHEN `touchable` 为 `false` 或独占标志改变 THEN 本特性只规定对应 Hub 配置的写入，不扩展定义手势裁决、冒泡或命中测试算法。 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-2 | SDK/源码审查 | `common.d.ts:18892-18906`; `view_abstract.cpp:3557-3569` |
| AC-1.2 | R-2 | TASK-2 | SDK 审查 | `common.d.ts:18925-18940`; `common.static.d.ets:11612-11625` |
| AC-1.3 | R-3 | TASK-2 | 源码审查 | `gesture_event_hub.cpp:1780-1813` |
| AC-2.1 | R-4 | TASK-2 | SDK/源码审查 | `common.d.ts:18998-19015`; `view_abstract.cpp:3572-3576` |
| AC-2.2 | R-5 | TASK-2 | SDK/源码审查 | `common.d.ts:24522-24534`; `gesture_event_hub.cpp:1254-1256` |
| AC-2.3 | R-6 | TASK-2 | 架构审查 | `design.md` 的范围边界 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 `responseRegion(value)` | 将响应区域配置下行到通用组件事件路径 | 具体区域命中算法不属于本 Feat | AC-1.1 |
| R-2 | 行为 | 设置 `responseRegionList(regions)` | 按 SDK 声明记录高级响应区域列表 | 与单区域 API 的具体覆盖关系以既有实现为准 | AC-1.2 |
| R-3 | 边界 | 未设置区域或区域列表为空 | 不由本特性额外创建命中热区 | 不推断未配置时的命中结果 | AC-1.3 |
| R-4 | 行为 | 设置 `touchable(boolean)` | `ViewAbstract::SetTouchable` 写入 `GestureEventHub` | SDK 注释标注该 API 可由 `hitTestBehavior` 替代；本规格不改变既有 API | AC-2.1 |
| R-5 | 行为 | 设置 `monopolizeEvents(boolean)` | `ViewAbstract::SetMonopolizeEvents` 写入 `GestureEventHub` | 不定义其他组件的竞争与裁决细节 | AC-2.2 |
| R-6 | 边界 | 触摸开关或独占标志变更 | 仅保证配置路径可追溯 | 命中测试、手势识别和事件分发由相邻框架能力承接 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3 | SDK/源码审查 | 单区域、区域列表及未配置边界。 |
| VM-2 | AC-2.1~2.3 | SDK/源码审查 | `ViewAbstract` 至 `GestureEventHub` 的触摸和独占配置路径。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `responseRegion/responseRegionList` | Public | 区域或区域列表 | 链式对象 | N/A | 配置触摸响应热区 | AC-1.1~1.3 |
| `touchable` | Public | boolean | 链式对象 | N/A | 配置组件触摸参与 | AC-2.1 |
| `monopolizeEvents` | Public | boolean | 链式对象 | N/A | 配置组件事件独占标志 | AC-2.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `touchable` | 变更 | SDK 注释建议使用 `hitTestBehavior` | 采用替代 API 时遵循目标 SDK 的声明；本规格仍记录现有实现路径 | AC-2.1 |

## 接口规格

### 接口定义

**触摸响应热区**

| 属性 | 值 |
|------|-----|
| 函数签名 | `responseRegion(value)`；`responseRegionList(regions)` |
| 返回值 | 动态前端 `T`；静态前端 `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.3 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | SDK 声明的响应区域值 | 是 | 无 | 使用目标 SDK 对应 API 的区域类型。 |
| regions | SDK 声明的区域列表 | 是 | 无 | 列表语义以 SDK 声明为准。 |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置区域或区域列表 | 配置进入已有通用组件事件路径 | AC-1.1, AC-1.2 |
| 2 | 未设置或空列表 | 不增加额外命中算法语义 | AC-1.3 |

**触摸控制与事件独占**

| 属性 | 值 |
|------|-----|
| 函数签名 | `touchable(value: boolean)`；`monopolizeEvents(monopolize: boolean)` |
| 返回值 | 动态前端 `T`；静态前端 `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.3 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value / monopolize | boolean | 是 | 无 | 只配置 `GestureEventHub` 既有状态，不定义裁决算法。 |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 `touchable` | 设置触摸控制状态 | AC-2.1 |
| 2 | 调用 `monopolizeEvents` | 设置事件独占状态 | AC-2.2 |
| 3 | 状态为 false 或发生变化 | 由既有事件系统消费配置 | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 无；本文档将 Feat-02 的规格范围调整为既有的触摸交互 API。
- **配置文件格式变更:** 无。
- **数据存储格式变更:** 无。
- **最低支持版本:** `responseRegion`、`touchable` 以对应 SDK 的 since 声明为准；`responseRegionList` 和 `monopolizeEvents` 按其 SDK 声明使用。
- **API 版本号策略:** 动态与静态声明分别以 `common.d.ts`、`common.static.d.ets` 为准，不由内部 C++ 签名推断。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 契约优先 | 外部 API 名称、参数和 since 以 SDK 声明为准 | 全部 |
| Hub 配置落点 | 触摸控制和独占状态由 `ViewAbstract` 写入 `GestureEventHub` | AC-2.1, AC-2.2 |
| 边界归属 | 命中测试和手势裁决不在本 Feat 定义 | AC-1.3, AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 所有 API 可定位到 SDK 与 Hub 配置路径 | 静态审查 | 输入文档路径 |
| 生态兼容 | 不把 `touchable` 的 SDK 替代说明误写为删除现有实现 | SDK 对照 | `common.d.ts:18998-19015` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 以触摸输入为主 | API 语义一致 | 设备测试 | SDK 契约 |
| 平板 | 可能同时有触摸与鼠标 | 本 Feat 只规定触摸配置 | 设备测试 | SDK 契约 |
| 折叠屏 | 折叠状态不改变 API 配置语义 | API 语义一致 | 设备测试 | SDK 契约 |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|------|------|------|----------|
| 无障碍 | 是 | 本 Feat 不改变独立无障碍事件语义 | 全部 |
| 多窗口/分屏 | 是 | 配置归属当前组件及其事件 Hub | AC-2.1, AC-2.2 |
| 深色模式 | 否 | 不改变触摸配置 | 全部 |
| 版本升级 | 是 | 按各 API 的 SDK since 调用 | 全部 |

## 行为场景（可选，Gherkin）

L1 规格已由接口定义中的行为场景表覆盖，不重复使用 Gherkin。

## Spec 自审清单

- [x] 无待定、TBD 或 TODO 占位符
- [x] 所有 AC 使用 WHEN/THEN 格式且可测试
- [x] 范围覆盖触摸热区、触摸控制和事件独占
- [x] 每条规则关联 AC
- [x] 规则具备可复现触发条件和可观察结果

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "ViewAbstract responseRegion touchable monopolizeEvents GestureEventHub configuration"
```
