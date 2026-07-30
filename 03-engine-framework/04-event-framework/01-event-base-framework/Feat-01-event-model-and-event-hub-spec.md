# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 事件数据模型与节点事件中心 |
| 特性编号 | Func-03-04-01-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 8-23，当前主干 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

本规格补录 ArkUI 事件基础数据、事件目标快照和节点级事件中心的既有行为，覆盖 NG/Legacy 共存、Dynamic/Static ArkTS 与 Native C API。当前实现是规格基线，不引入新接口。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 存量事件模型规格 | 固化 Touch/Mouse/Axis/Key 通用字段、目标快照和 Native 包装行为 |
| ADDED | 节点事件中心规格 | 固化 EventHub、GestureEventHub、InputEventHub、FocusHub 的职责和生命周期 |
| ADDED | 版本差异说明 | 记录 Dynamic API 8-23、Static API 23 及 EventTarget.id 的版本边界 |

## 输入文档

- 需求基线：已有能力补录，无独立 requirement.md。
- 共享设计：`specs/03-engine-framework/04-event-framework/01-event-base-framework/design.md`。
- 核心实现：`frameworks/core/common/event_manager.h:106`、`frameworks/core/components_ng/event/event_hub.h:136`、`frameworks/core/components_ng/event/event_hub.cpp:145`。
- SDK 声明：`interface/sdk-js/api/@internal/component/ets/common.d.ts:7506,9261`、`interface/sdk-js/api/arkui/component/common.static.d.ets:3283,4527`。
- Native 声明：`interfaces/native/event/ui_input_event_impl.h:43`、`interfaces/native/ui_input_event.h:444`、`interfaces/native/native_key_event.h:488`。

## 用户故事

### US-1: 获得一致的基础事件对象

作为 ArkUI 组件和桥接层开发者，我希望不同输入类型共享可追踪的时间、设备、来源和目标信息，以便跨前端和 Native 通道保持一致的事件语义。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Dynamic ArkTS 回调接收基础事件 THEN 事件包含纳秒时间戳和按触发时几何信息构造的 target | 正常 |
| AC-1.2 | WHEN Static ArkTS API 23 回调接收基础事件 THEN EventTarget 与 BaseEvent 使用 Static 声明的强类型字段 | 正常 |
| AC-1.3 | WHEN Native 节点事件被转换 THEN Touch/Mouse/Axis/Key 被包装为对应类型的 ArkUI_UIInputEvent | 正常 |
| AC-1.4 | WHEN Dynamic 应用目标版本低于 API 15 THEN 不依赖 EventTarget.id；WHEN 目标版本不低于 API 15 THEN 可读取可选 id | 边界 |

### US-2: 通过节点事件中心管理监听和状态

作为组件实现者，我希望节点按需创建事件子中心，并以明确的生命周期和 enabled 语义管理回调，以便避免无事件节点的额外对象并保持兼容行为。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 节点首次请求 GestureEventHub、InputEventHub 或 FocusHub THEN EventHub 按需创建并复用该对象 | 正常 |
| AC-2.2 | WHEN节点触发 appear THEN 回调通过 UI task 异步执行；WHEN 节点触发 disappear THEN 回调在当前调用链同步执行 | 边界 |
| AC-2.3 | WHEN 内部流程临时修改 enabled THEN developerEnabled 保留开发者设定且 RestoreEnabled 可恢复该值 | 恢复 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1, AC-1.4 | R-1, R-2 | TASK-F1-1 | SDK 声明检查与桥接单测 | `event_hub.cpp:145`、`js_common_utils.cpp:48`、`common.d.ts:7506` |
| AC-1.2 | R-3 | TASK-F1-1 | Static 编译检查 | `common.static.d.ets:3283,4527` |
| AC-1.3 | R-4 | TASK-F1-2 | C API 单测 | `node_model.cpp:674-727`、`ui_input_event.cpp:77` |
| AC-2.1 | R-5 | TASK-F1-3 | EventHub 单测 | `event_hub.h:136` |
| AC-2.2 | R-6 | TASK-F1-3 | UI task 时序测试 | `event_hub.cpp:608,634` |
| AC-2.3 | R-7 | TASK-F1-3 | enabled 状态恢复测试 | `event_hub.cpp:1073` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用事件回调并请求 target | 从当前 GeometryNode 的 frame offset、size 和窗口偏移构造 EventTarget 快照 | target 是触发时快照，不是持续绑定对象 | AC-1.1 |
| R-2 | 边界 | Dynamic API 读取 EventTarget | area 始终按声明提供，id 仅作为可选字段暴露 | id 自 API 15；内部 target.type 不进入 Dynamic 公共对象 | AC-1.1, AC-1.4 |
| R-3 | 边界 | 使用 Static ArkTS 公共事件类型 | 使用 API 23 Static EventTarget/BaseEvent 声明 | Static 声明基线为 API 23 | AC-1.2 |
| R-4 | 行为 | Native 节点派发 Touch/Mouse/Axis/Key | node_model 按事件类型设置 ArkUI_UIInputEvent.eventType 和 inputEvent 指针 | getter 仅在支持的事件场景返回有效值 | AC-1.3 |
| R-5 | 行为 | 首次调用 EventHub 的 GetOrCreate 子中心 | 创建一次并由 EventHub 持有，后续返回同一对象 | 节点未使用的子中心不预创建 | AC-2.1 |
| R-6 | 边界 | 触发 appear 或 disappear | appear 投递 UI 异步任务；disappear 同步调用注册回调 | 节点销毁或回调为空时不调用 | AC-2.2 |
| R-7 | 恢复 | 内部禁用后调用 RestoreEnabled | enabled 恢复为 developerEnabled | SetEnabledInternal 不覆盖 developerEnabled | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, AC-1.4 | Dynamic ArkTS API/桥接单测 | target.area、可选 id、timestamp |
| VM-2 | AC-1.2 | Static ArkTS 编译用例 | API 23 强类型声明 |
| VM-3 | AC-1.3 | `linux_unittest_capi` | 各类 ArkUI_UIInputEvent 包装与 getter 场景约束 |
| VM-4 | AC-2.1 | EventHub 单元测试 | 子中心按需创建和复用 |
| VM-5 | AC-2.2, AC-2.3 | 生命周期与状态恢复测试 | 异步/同步次序、developer/internal enabled 分离 |

## API 变更分析

### 新增 API

无新增 API。本规格记录既有 Dynamic/Static ArkTS EventTarget、BaseEvent 以及 Native UIInputEvent。

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**EventTarget / BaseEvent（现有公共类型）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `interface EventTarget`；`interface BaseEvent` |
| 返回值 | N/A，事件回调参数类型 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2, AC-1.4 |

**ArkUI_UIInputEvent getter（现有 C API）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_UIInputEvent_GetType/GetAction/GetEventTime/GetDeviceId(...)` |
| 返回值 | 对应事件字段；不支持场景返回接口定义的无效值并记录状态 |
| 开放范围 | Public |
| 错误码 | 依具体 getter，为无效值或 ArkUI_ErrorCode |
| 关联 AC | AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| event | `const ArkUI_UIInputEvent*` | 是 | 无 | 不得为空，且 eventType 必须属于 getter 支持场景 |

行为索引：正常事件对象见 VM-1/VM-3；版本边界见 VM-2；生命周期行为见 VM-5。

## 兼容性声明

- **已有 API 行为变更:** 否；记录现有差异：Dynamic EventTarget.id 自 API 15，Static 事件类型自 API 23。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic BaseEvent/EventTarget 为 API 8；Static 基线为 API 23。
- **API 版本号策略:** 保持 SDK 现有 `@since` 标注，不新增版本号。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 节点事件归口 | NG 节点事件监听统一归 EventHub 及其子中心管理 | AC-2.1 |
| 多态样式边界 | EventHub 与 StateStyleManager 的状态样式集成由 Func-04-03-07 样式属性承载 | AC-2.1 |
| 桥接不泄漏内部类型 | 内部 EventTarget.type 不应被假定为公共 ArkTS 字段 | AC-1.1, AC-1.4 |
| Native 场景校验 | C API getter 必须按 UIInputEvent 类型检查支持范围 | AC-1.3 |
| Legacy 共存 | EventManager 同时维持 NG 和旧管线分发入口，不改变旧行为 | AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 未使用的 EventHub 子中心不创建 | 对象生命周期单测 | `event_hub.h:136` |
| 内存 | EventTarget 仅保存回调所需快照字段，不暴露 FrameNode 所有权 | 代码审查 | `event_hub.cpp:145` |
| 安全 | Native getter 对空指针和不支持事件类型执行校验 | C API 异常用例 | `ui_input_event.cpp:77` |
| 可靠性 | 内部 enabled 临时变更可恢复开发者配置 | 状态恢复测试 | `event_hub.cpp:1073` |
| 可测试性 | Dynamic、Static、Native 三通道分别验证 | 编译与单测 | SDK 声明及 C API 测试 |
| 定界定位 | 事件类型、设备和时间字段可用于输入链路定位 | Dump/日志检查 | `event_manager.h:106` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无结构差异 | 坐标按对应窗口和显示屏计算 | 触摸测试 | EventTarget/BaseEvent |
| 平板 | 支持鼠标、触摸和多窗口目标信息 | targetDisplayId 可选 | 鼠标与跨屏测试 | `common.d.ts:9481` |
| 折叠屏 | 折叠状态变化不改变事件对象结构 | 使用触发时几何快照 | 展开/折叠回归 | `event_hub.cpp:145` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | AccessibilityHover 等事件复用基础事件语义 | AC-1.1 |
| 大字体 | 否 | 不改变事件数据结构 | - |
| 深色模式 | 否 | 不影响事件模型 | - |
| 多窗口/分屏 | 是 | target 的窗口偏移和 targetDisplayId 必须对应事件发生窗口 | AC-1.1 |
| 多用户 | 否 | 无持久化用户数据 | - |
| 版本升级 | 是 | 需遵守 API 15 与 API 23 边界 | AC-1.2, AC-1.4 |
| 生态兼容 | 是 | 保留 Legacy 与 Dynamic 既有行为 | AC-1.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 事件数据模型与节点事件中心
  Scenario: 构造事件目标快照
    Given 节点已完成布局并注册触摸回调
    When 输入事件命中该节点
    Then 回调 target.area 使用事件触发时的节点几何信息
    And Dynamic API 15 及以上可读取可选 target.id

  Scenario: EventHub 生命周期时序
    Given 节点同时注册 onAppear 和 onDisappear
    When 节点进入再离开主树
    Then onAppear 通过 UI task 异步执行
    And onDisappear 在离开调用链同步执行
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则满足可复现、可观测、边界明确、关联 AC、无冲突要求

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "EventHub EventTarget BaseEvent lifecycle enabled Dynamic Static Native UIInputEvent"
```

**关键文档：** `design.md`、SDK `common.d.ts`、`common.static.d.ets`、`interfaces/native/ui_input_event.h`。
