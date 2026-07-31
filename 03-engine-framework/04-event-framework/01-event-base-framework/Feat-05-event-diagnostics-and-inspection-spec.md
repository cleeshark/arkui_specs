# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 事件诊断与维测 |
| 特性编号 | Func-03-04-01-Feat-05 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | 当前主干 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

本规格补录 EventTree、输入时间跟踪、Reporter 和 Inspector 事件采集的既有行为，包括主事件与 PostEvent 诊断域、Dump 输出、编译裁剪和容量边界。鼠标光标请求、VSync 仲裁及 MouseStyleManager 由 `Func-04-04-05-Feat-04 鼠标光标样式与自定义光标` 承载；多态样式由 `Func-04-03-07 样式属性` 承载。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | EventTree 诊断规格 | 固化 touch/axis/hitTest/gesture/smartGesture 快照与 Dump |
| ADDED | 输入时间跟踪规格 | 固化 sensor/process/dispatch 时间的有界记录 |
| ADDED | 编译裁剪规格 | 固化 ENABLE_INSPECTOR_EVENT_REPORTING 对采集路径的影响 |
| REMOVED | 鼠标光标请求规格 | 由 `04-common-capability/04-common-events/05-mouse-events/Feat-04-mouse-cursor-style-custom-cursor-spec.md` 承载 |

## 输入文档

- 共享设计：`specs/03-engine-framework/04-event-framework/01-event-base-framework/design.md`。
- 诊断模型：`frameworks/core/common/event_dump.h:34-162`。
- 容量和 Dump：`frameworks/core/common/event_dump.cpp:22-30,189-340,604-660`。
- EventManager 入口：`frameworks/core/common/event_manager.h:280-305,604-606`、`event_manager.cpp:1150,1201-1238,1589-1634,2563-2630,3161-3199`。
- 鼠标光标承接：`specs/04-common-capability/04-common-events/05-mouse-events/Feat-04-mouse-cursor-style-custom-cursor-spec.md`。
- 多态样式承接：`specs/04-common-capability/03-common-attributes/07-style-attributes/`。

## 用户故事

### US-1: 记录事件树和处理过程

作为事件问题定位开发者，我希望记录输入点、命中节点、手势识别器和智能手势结果，以便从一次交互还原命中与仲裁过程。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Touch DOWN 建立新交互轮次 THEN EventTree 记录 TouchPointSnapshot，并可在同一轮次追加 FrameNodeSnapshot 和 GestureSnapshot | 正常 |
| AC-1.2 | WHEN Axis BEGIN 建立轴事件轮次 THEN EventTree 记录 AxisSnapshot，并在 END/CANCEL 时更新活动 axis 标识 | 正常 |
| AC-1.3 | WHEN命中节点快照 nodeId 已存在 THEN不重复追加该节点；WHEN不存在且未达到节点上限 THEN追加快照 | 边界 |
| AC-1.4 | WHEN SmartGestureExecutionSnapshot 数量超过 5 THEN移除最旧记录并保留最近 5 条 | 边界 |
| AC-1.5 | WHEN PostEvent recognizer 执行处理 THEN过程写入 postEventTree_ 而不是主 eventTree_ | 正常 |

### US-2: 有界输出并支持产品裁剪

作为产品维测和构建维护者，我希望诊断记录有固定容量、可输出文本/JSON，并能在发布配置中裁剪，以便控制内存和产品开销。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN EventTree 新增轮次后总数超过 5 THEN移除最旧轮次并保留最近 5 轮 | 边界 |
| AC-2.2 | WHEN单轮 touch/axis/gesture 数据超过各自上限 THEN按实现清理当前记录或拒绝无限追加 | 边界 |
| AC-2.3 | WHEN输入时间历史达到 2048 条 THEN清空历史、增加溢出计数并记录警告 | 恢复 |
| AC-2.4 | WHEN调用 EventTreeRecord::Dump THEN文本或 JSON 同时包含已记录的 touch、axis、smartGesture、hitTest 和 gesture 数据 | 正常 |
| AC-2.5 | WHEN未启用 ENABLE_INSPECTOR_EVENT_REPORTING THEN不编译或执行 EventManager 中受该宏保护的采集和 Reporter 路径，正常分发保持不变 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1, AC-1.2 | R-1, R-2 | TASK-F5-1 | EventTree touch/axis 单测 | `event_dump.cpp:189-263` |
| AC-1.3 | R-3 | TASK-F5-1 | FrameNodeSnapshot 去重测试 | `event_dump.cpp:265-298` |
| AC-1.4 | R-4 | TASK-F5-1 | smart gesture 容量测试 | `event_dump.cpp:322-330` |
| AC-1.5 | R-5 | TASK-F5-2 | PostEvent 诊断域测试 | `event_manager.cpp:1589-1634` |
| AC-2.1, AC-2.2 | R-6, R-7 | TASK-F5-3 | EventTree 极限容量测试 | `event_dump.cpp:22-30,191-315` |
| AC-2.3 | R-8 | TASK-F5-3 | 输入时间历史溢出测试 | `event_dump.cpp:624-640` |
| AC-2.4 | R-9 | TASK-F5-4 | 文本/JSON Dump 测试 | `event_dump.h:130-140`、`event_dump.cpp:604-622` |
| AC-2.5 | R-10 | TASK-F5-4 | 编译矩阵与输入回归 | `event_manager.cpp:1210-1238,2563-2571` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | TouchPoint 到达 EventTreeRecord | DOWN 创建/复用当前多指轮次，UP/CANCEL/PULL_UP/PULL_OUT_WINDOW 移除活动 finger，事件快照追加到当前轮次 | 同一 id 重复 DOWN 会丢弃当前异常轮次 | AC-1.1 |
| R-2 | 行为 | AxisEvent 到达 EventTreeRecord | BEGIN 创建或复用轮次并登记 axis id，END/CANCEL 移除活动 axis id | 同一 id 重复 BEGIN 会丢弃当前异常轮次 | AC-1.2 |
| R-3 | 边界 | AddFrameNodeSnapshot 收到 node | nodeId 已存在时返回；不存在且 hitTestTree 未达上限时追加 | 更新策略仅作用于已存在 nodeId | AC-1.3 |
| R-4 | 边界 | AddSmartGestureExecution 追加快照 | 队列超过 5 条时持续 pop_front | `MAX_SMART_GESTURE_EXECUTION_CNT=5` | AC-1.4 |
| R-5 | 行为 | 诊断类型为 POST_EVENT | recognizer procedure 和 target procedure 写入 postEventTree_ | 主事件继续写入 eventTree_ | AC-1.5 |
| R-6 | 边界 | 新事件轮次使 eventTreeList 超过 5 | erase begin 删除最旧轮次 | `MAX_EVENT_TREE_RECORD_CNT=5` | AC-2.1 |
| R-7 | 边界 | 单轮诊断记录增长 | touch down 上限 10、touch point 20、axis update 20、axis 20、gesture 100；超限按对应路径清理/停止追加 | 各类型独立计数 | AC-2.2 |
| R-8 | 恢复 | EventTouchInfoRecord history size 达到 2048 | dequeMaxCnt_ 加 1，清空 touchHistory_ 并记录警告 | `MAX_HISTORY_TOUCH_INFO_SIZE=2048` | AC-2.3 |
| R-9 | 行为 | 调用文本或 JSON Dump | 遍历 eventTreeList，并输出 touch、axis、smartGesture、hitTest、gesture 五类内容 | startNumber 用于跳过前序轮次 | AC-2.4 |
| R-10 | 行为 | 构建或运行 Inspector 采集路径 | 仅在 `ENABLE_INSPECTOR_EVENT_REPORTING` 开启时采集、上报和 Dump 受保护数据 | 宏关闭不改变事件命中和分发结果 | AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1 至 AC-1.4 | `event_dump_test_ng` | 轮次、活动 id、去重、smartGesture 队列 |
| VM-2 | AC-1.5 | PostEvent 交互测试 | 主 EventTree 与 postEventTree 隔离 |
| VM-3 | AC-2.1, AC-2.2, AC-2.3 | 容量边界测试 | 5/10/20/100/2048 精确边界和恢复 |
| VM-4 | AC-2.4 | Dump 文本/JSON 快照测试 | 五类诊断数据与 startNumber |
| VM-5 | AC-2.5 | Inspector 开关构建矩阵 | 宏关闭时输入回归、宏开启时采集可见 |

## API 变更分析

### 新增 API

无新增 Public/System API。EventTree、EventTouchInfoRecord 和 EventManager Dump 接口为既有 InnerApi。

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**EventTreeRecord::Dump（现有 InnerApi）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void Dump(dumpList/json, int32_t depth, int32_t startNumber = 0) const` |
| 返回值 | void，通过输出参数返回诊断数据 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.4 |

**EventManager::DumpEvent（现有 InnerApi）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void DumpEvent(NG::EventTreeType type, bool hasJson = false)` |
| 返回值 | void |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.5, AC-2.4, AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | EventTreeType | 是 | TOUCH | 选择主事件或 PostEvent 诊断树 |
| hasJson | bool | 否 | false | false 输出文本，true 输出 JSON |
| startNumber | int32_t | 否 | 0 | 小于 0 按调用方现有解析规则处理；非负值跳过对应数量轮次 |

行为索引：记录行为见 VM-1/VM-2；容量和恢复见 VM-3；输出与编译裁剪见 VM-4/VM-5。

## 兼容性声明

- **已有 API 行为变更:** 否；鼠标光标内容从本文档移除，现有鼠标事件 Feat-04 保持权威归属。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否，诊断记录只在内存中有界保留。
- **最低支持版本:** InnerApi 随当前引擎主干。
- **API 版本号策略:** 不适用 Public `@since`。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 诊断旁路 | EventTree/Reporter 只观察和记录，不改变命中、分发或仲裁结果 | 全部 AC |
| 处理域隔离 | 主事件与 PostEvent 使用独立 EventTreeRecord | AC-1.5 |
| 诊断有界 | EventTree、gestureMap、smartGesture 和 touch history 必须遵守固定容量 | AC-1.4, AC-2.1, AC-2.2, AC-2.3 |
| 编译特性隔离 | Inspector 采集由编译宏控制，宏关闭不得影响正常输入 | AC-2.5 |
| 相邻能力边界 | 鼠标光标归 Func-04-04-05-Feat-04，多态样式归 Func-04-03-07 | 全部 AC |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 诊断关闭构建不执行受宏保护的采集；开启时所有记录容器有界 | 构建矩阵/性能对照 | `event_manager.cpp:1210` |
| 内存 | EventTree 最多 5 轮、smartGesture 最多 5 条、touch history 达 2048 后清空 | 容量单测 | `event_dump.cpp:22-30,329-330,630-633` |
| 可靠性 | 重复 DOWN/BEGIN 或记录超限时清理异常轮次，不影响后续新轮次 | 异常序列测试 | `event_dump.cpp:191-245` |
| 可测试性 | touch/axis/hitTest/gesture/smartGesture 可独立构造 | 单元测试 | EventDump tests |
| 自动化维测 | 支持文本和 JSON Dump，可按 startNumber 选择轮次 | Dump 测试 | `event_dump.cpp:604-622` |
| 定界定位 | 输入时间记录包含 sensor/process/dispatch 三阶段时间 | Dump 检查 | `event_dump.h:147-159` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | Touch 诊断数据更常见 | 多指记录在同一 EventTree 轮次 | 多指测试 | AC-1.1 |
| 平板 | Touch、Mouse 转换事件和 Axis 诊断并存 | 按实际输入类型记录 | 鼠标滚轮/触摸测试 | AC-1.2 |
| 折叠屏 | 多窗口和显示区域变化不改变容量规则 | 每个 EventManager 持有自身诊断树 | 窗口迁移测试 | AC-1.5 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 诊断不得改变无障碍事件处理，仅记录可观察状态 | AC-2.5 |
| 大字体 | 否 | 不影响诊断数据结构 | - |
| 深色模式 | 否 | 不影响诊断数据结构 | - |
| 多窗口/分屏 | 是 | 各容器/EventManager 的诊断记录相互隔离 | AC-1.5 |
| 多用户 | 否 | 无持久化用户数据 | - |
| 版本升级 | 否 | 既有 InnerApi 行为补录 | - |
| 生态兼容 | 是 | Inspector 宏关闭不改变应用事件行为 | AC-2.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 事件诊断与维测
  Scenario: EventTree 有界记录
    Given EventTree 已保存 5 轮事件
    When 新一轮 Touch DOWN 建立事件树
    Then 删除最旧轮次
    And 仍只保留最近 5 轮

  Scenario: PostEvent 诊断隔离
    Given 主事件树和 PostEvent 事件树均已创建
    When PostEvent recognizer 处理 Touch 事件
    Then procedure 仅追加到 postEventTree
    And 主 eventTree 不追加该 procedure
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 范围边界明确，鼠标光标由 Func-04-04-05-Feat-04 承载
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则满足 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "EventTree EventTreeRecord EventTouchInfoRecord DumpEvent Reporter inspector reporting capacity PostEvent"
  - repo: "openharmony/arkui_ace_engine"
    query: "Func-04-04-05-Feat-04 MouseStyleManager cursor VSync ownership boundary"
```

**关键文档：** `design.md`、`event_dump.h`、`event_dump.cpp`、`event_manager.cpp`、鼠标事件 `Feat-04-mouse-cursor-style-custom-cursor-spec.md`。
