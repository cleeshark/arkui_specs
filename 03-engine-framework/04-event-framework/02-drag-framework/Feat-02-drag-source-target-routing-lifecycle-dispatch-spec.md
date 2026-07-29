# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 拖拽源目标路由与生命周期派发 |
| 特性编号 | Func-03-04-02-Feat-02 |
| 所属 Epic | 03-engine-framework / 04-event-framework / 02-drag-framework |
| 优先级 | P0 |
| 目标版本 | 存量实现补录；动态 API 8/10/12/15/20、静态 API 23 与 C 节点事件 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | Feat-02 存量行为规格 | 补录目标命中、事件派发、严格上报与取消/跨容器清理，不改动实现。 |

## 输入文档

- `specs/03-engine-framework/04-event-framework/02-drag-framework/design.md`
- `D:/arkui/gitCode/ArkUI/docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-universal-events-drag-drop.md`
- `D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@internal/component/ets/common.d.ts`
- `D:/arkui/gitCode/ArkUI/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h`

## 用户故事

### US-1: 目标命中与生命周期事件

作为拖拽目标组件开发者，我希望框架依据命中目标和目标切换派发正确的生命周期事件。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 指针位于 active、visible 且可接收落放的 FrameNode，THEN 框架按逆序子节点命中并将其作为候选目标。 | 正常 |
| AC-1.2 | WHEN 指针持续位于同一目标，THEN 框架派发 Move；WHEN 切换目标，THEN 先处理旧目标 Leave 再对新目标 Enter。 | 正常 |
| AC-1.3 | WHEN 父目标与子目标嵌套且指针移入子目标，THEN 默认保留父目标；严格上报开启时派发父目标 Leave。 | 边界 |
| AC-1.4 | WHEN `dragHitTestBlock` 阻断命中，THEN 该节点不得成为落放目标。 | 异常 |

### US-2: 拒绝、取消与跨容器清理

作为框架维护者，我希望无目标、数据拒绝、OUT/CANCEL 和跨容器切换不产生错误 Drop 回调或遗留状态。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 结束时无目标或目标不允许数据落入，THEN 不派发 `onDrop`，并重置拖拽状态。 | 异常 |
| AC-2.2 | WHEN 收到 OUT 或 PULL_CANCEL，THEN 对旧目标派发 Leave 并清理窗口级状态、摘要和速度信息。 | 恢复 |
| AC-2.3 | WHEN 拖拽在新容器收到 START，THEN 先清除旧容器的前目标，再在新容器重新命中。 | 边界 |
| AC-2.4 | WHEN 输入为鼠标且时间、距离变化均未达到阈值，THEN Move 可被限流；非鼠标不使用该限流条件。 | 边界 |

### US-3: 系统、手势与接口桥接

作为集成开发者，我希望区分系统事件主派发、手势代理模拟派发和 ArkTS/C 回调桥接。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN 系统 MMI 发送拖拽事件，THEN `PipelineContext::OnDragEvent` 更新指针状态并派发给 DragDropManager。 | 正常 |
| AC-3.2 | WHEN 手势起拖已成功，THEN `DragDropProxy` 模拟起拖后的 Manager Start/Move/End 入口，不替代系统事件主派发。 | 正常 |
| AC-3.3 | WHEN ArkTS 或 C 节点事件注册生命周期回调，THEN 桥接层向 EventHub 注册并按对应事件子类回调。 | 正常 |

## 验收追踪

| AC | 关联规则 | 关联Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.4 | R-1~R-3 | Feat-02 | Manager Host 测试 | `drag_drop_manager_test_ng_arch.cpp:1657` |
| AC-2.1~AC-2.4 | R-4~R-6 | Feat-02 | 无目标、取消、鼠标阈值测试 | `drag_drop_manager_test_ng_arch.cpp:653` |
| AC-3.1~AC-3.3 | R-7~R-8 | Feat-02 | 调用链和节点事件测试 | `pipeline_context.cpp:6248`；`node_drag_modifier.cpp:91` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 指针进入可见、active 的节点树 | 逆序遍历并在 paint rect 内选择可接收 drop 的目标 | `dragHitTestBlock` 阻断目标 | AC-1.1、AC-1.4 |
| R-2 | 行为 | 同目标移动或切换目标 | 同目标 Move；切换时旧目标 Leave、新目标 Enter | 父子嵌套默认不 Leave 父目标 | AC-1.2、AC-1.3 |
| R-3 | 边界 | strict reporting 开启且进入子目标 | 对父目标额外派发 Leave | 仅严格上报改变该父子规则 | AC-1.3 |
| R-4 | 异常 | end 时无命中目标或 `IsDropAllowed` 为 false | 不调用 Drop，重置拖拽状态 | 数据类型/force-disallow 都属于拒绝 | AC-2.1 |
| R-5 | 恢复 | OUT/PULL_CANCEL 或容器 START | Leave 旧目标并清理窗口数据；新容器先重置前目标 | OUT 不等同 StopDrag | AC-2.2、AC-2.3 |
| R-6 | 边界 | 鼠标 Move 的时间和距离均过小 | 限流该 Move；触摸等非鼠标继续处理 | 阈值由现有实现决定 | AC-2.4 |
| R-7 | 行为 | MMI 拖拽事件到达 | PipelineContext 承担系统事件主派发 | Proxy 不替代该路径 | AC-3.1、AC-3.2 |
| R-8 | 行为 | ArkTS/C 注册生命周期回调 | Bridge/EventHub 派发 Enter/Move/Leave/Drop/End | API 可用版本取决于前端/API 通道 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1~R-3 | DragDropManager Host 测试 | 命中、顺序、严格上报 |
| VM-2 | R-4~R-6 | Host 单元测试 | 拒绝、取消、跨容器、鼠标限流 |
| VM-3 | R-7~R-8 | bridge/集成测试 | Pipeline 主派发与 ArkTS/C 回调 |

## API 变更分析

### 新增 API

存量补录，不新增 API。当前外部契约为 `onDragEnter/Move/Leave/Drop/End` 和对应 C 节点事件。

| API名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `onDragEnter/onDragMove/onDragLeave` | Public | 拖拽事件回调 | 链式对象 | N/A | 目标生命周期事件；动态 API 8 | AC-1.2、AC-3.3 |
| `onDrop` | Public | `DragEvent` 或 API 15 回调/DropOptions | 链式对象 | N/A | 可接收时的落放事件 | AC-2.1、AC-3.3 |
| `onDragEnd` | Public | `DragEvent` | 链式对象 | N/A | 拖拽结束事件；动态 API 10 | AC-3.3 |

### 变更/废弃 API

| API名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| `onDrop(callback, dropOptions?)` | 变更 | 动态 API 15 引入回调重载 | 检查目标 SDK；静态 API 可用版本独立标注 | AC-3.3 |
| strict report | 变更 | API 12 影响父子目标 Leave 行为 | 开启后按严格父子顺序验证 | AC-1.3 |

## 接口规格

### 接口定义

**目标生命周期回调组**

| 属性 | 值 |
|---|---|
| 函数签名 | `onDragEnter/Move/Leave/Drop/End(callback)` |
| 返回值 | 链式组件对象 |
| 开放范围 | Public / Public C node event |
| 错误码 | N/A |
| 关联AC | AC-1.2、AC-2.1、AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| `callback` | 拖拽事件回调 | 是 | N/A | Drop 只在存在且允许的目标调用。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 目标切换 | Leave 后 Enter | AC-1.2 |
| 2 | 无目标或拒绝数据 | 不调用 Drop 并 reset | AC-2.1 |

## 兼容性声明

- **已有 API 行为变更:** 否；补录现有路由。动态 Enter/Move/Leave/Drop 为 API 8，End 为 API 10，Drop 重载为 API 15；静态 ArkTS/C 版本不同。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 以各通道 SDK `@since` 为准。
- **API 版本号策略:** API 12 strict report、API 15 Drop 重载、API 20 元数据差异在后续对外 Feat 中逐项声明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 系统主派发 | 系统 MMI 拖拽事件由 PipelineContext 派发至 Manager。 | AC-3.1 |
| Proxy 边界 | DragDropProxy 模拟已起拖后的 Manager 入口，不替代 PipelineContext。 | AC-3.2 |
| Drop 条件 | 命中和 `IsDropAllowed` 都是 Drop 的必要条件。 | AC-2.1 |
| 状态清理 | OUT/CANCEL/跨容器都须清理前目标和窗口状态。 | AC-2.2、AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 鼠标小位移/短间隔 Move 可按现有阈值限流 | Host 测试 | `drag_drop_manager.cpp:1040-1070` |
| 可靠性 | 无目标、拒绝、取消不遗留目标/摘要/速度状态 | Host 测试 | `drag_drop_manager.cpp:875-975` |
| 可测试性 | 命中、严格 Leave、取消可在 Host 观察 | gtest | `drag_drop_manager_test_ng_arch.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机/平板 | 非鼠标 Move 不使用鼠标限流 | 路由语义一致 | Host 测试 | `drag_drop_manager.cpp:1040` |
| 鼠标设备 | 小时间/距离 Move 限流 | 覆盖阈值边界 | Host 测试 | `drag_drop_manager_test_ng_arch.cpp:653` |
| 多窗口/容器 | OUT/START 清理并重新命中 | 覆盖窗口状态切换 | 集成/Host 测试 | `drag_drop_manager.cpp:875,977` |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 否 | 路由无新增无障碍语义。 | N/A |
| 深色模式 | 否 | 不改变预览视觉。 | N/A |
| 多窗口/分屏 | 是 | 容器/scene root 会影响命中和清理。 | AC-2.3 |
| 版本升级 | 是 | 动态/静态/C 生命周期接口版本不同。 | AC-3.3 |

## 行为场景（Gherkin）

```gherkin
Feature: 拖拽源目标路由与生命周期派发
  Scenario: 目标切换
    Given 指针位于一个可接收落放的目标
    When 指针移动到另一个目标
    Then 旧目标先收到 Leave
    And 新目标收到 Enter

  Scenario: 拒绝落放
    Given 结束位置无目标或目标拒绝当前数据
    When 系统派发结束
    Then 不调用 onDrop
    And DragDropManager 重置拖拽状态
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN 格式。
- [x] 覆盖系统派发、Proxy、目标路由和取消边界。
- [x] 每条规则关联至少一个 AC 和验证映射。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "PipelineContext OnDragEvent, DragDropManager hit test and lifecycle dispatch"
  - repo: "OpenHarmony/interface_sdk-js"
    query: "Common drag lifecycle callback API versions"
  - repo: "OpenHarmony/interface_sdk_c"
    query: "Node drag event callback contract"
```
