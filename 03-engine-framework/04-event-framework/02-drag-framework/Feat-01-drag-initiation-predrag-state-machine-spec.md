# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 拖拽发起与预拖拽状态机 |
| 特性编号 | Func-03-04-02-Feat-01 |
| 所属 Epic | 03-engine-framework / 04-event-framework / 02-drag-framework |
| 优先级 | P0 |
| 目标版本 | 存量实现补录；覆盖 API 10、12、18、20 及当前静态 ArkTS API 23 入口 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | Feat-01 存量行为规格 | 不改变实现，仅将已存在的发起、预拖拽、异步放行和取消行为基线化。 |

## 输入文档

- `specs/03-engine-framework/04-event-framework/02-drag-framework/design.md`
- `docs/common/interaction/Drag_Drop_Knowledge_Base_CN.md`
- `<OH_ROOT>/docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-universal-events-drag-drop.md`
- `<OH_ROOT>/interface_sdk-js/api/@internal/component/ets/common.d.ts`
- `<OH_ROOT>/interface_sdk-js/api/@ohos.arkui.UIContext.d.ts`
- `<OH_ROOT>/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h`

## 用户故事

### US-1: 手势拖拽的预准备与起拖

作为应用开发者，我希望可观察组件从拖拽准备到成功起拖的状态，以便在合适的阶段准备数据和预览资源。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 可拖拽的非鼠标组件收到触摸命中，THEN 引擎进入 `IDLE → READY`，并安排预拖拽相关任务。 | 正常 |
| AC-1.2 | WHEN 触摸长按满足发起条件，THEN 状态机进入 `PRESS`，并在预览准备后派发 `READY_TO_TRIGGER_DRAG_ACTION`。 | 正常 |
| AC-1.3 | WHEN 调用系统 `InteractionInterface::StartDrag` 返回成功，THEN 状态机才进入 `MOVING`；Pan 开始本身不代表正式拖拽成功。 | 边界 |
| AC-1.4 | WHEN 鼠标触发拖拽，THEN 不要求触摸长按序列，Pan 起始可进入起拖处理。 | 正常 |

### US-2: 预拖拽状态、异步放行与取消

作为应用开发者，我希望能通过预拖拽状态和 `WAITING/READY` 控制数据未就绪时的起拖时机，并能得到明确的取消结果。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 预拖拽状态按有效次序推进，THEN `onPreDrag` 接收相应状态；`PREPARING_FOR_DRAG_DETECTION` 仅通知而不推进全局状态。 | 正常 |
| AC-2.2 | WHEN 状态重复、无效，或节点不可拖拽、文本拖拽、已在拖拽，THEN 正常预拖拽推进不发生，适用时回调 `ACTION_CANCELED_BEFORE_DRAG`。 | 异常 |
| AC-2.3 | WHEN `notifyDragStartRequest(WAITING)` 已登记异步回调，THEN 引擎安装 deadline；后续 `READY` 或 deadline 到期执行回调并清理 deadline。 | 正常 |
| AC-2.4 | WHEN 状态仍为 `WAITING` 但没有已登记的异步回调，THEN `READY` 不得伪造放行或覆盖等待状态。 | 边界 |
| AC-2.5 | WHEN 手势取消、起拖失败或必要预览资源缺失，THEN 引擎清理预览/计时器并执行相应取消或 `onDragEnd` 收尾路径。 | 恢复 |

### US-3: MSDP 接管后的边界

作为框架维护者，我希望区分 ArkUI 的起拖/落入职责与 MSDP 的真实拖拽会话职责，避免把手势结束误认为真实拖拽结束。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN ArkUI 组装 `DragData`，THEN 通过 `InteractionInterface::StartDrag` 将真实拖拽会话交给 MSDP，并传入 `GetDragCallback`。 | 正常 |
| AC-3.2 | WHEN MSDP 通过 `GetDragCallback` 通知结束，THEN ArkUI 在 UI 任务中派发 `onDragEnd`、执行框架收尾并通知发起状态机结束。 | 正常 |
| AC-3.3 | WHEN 菜单预览请求 restart drag，THEN ArkUI 清理识别器并复用常规起拖链；C `DragAction` 主动起拖则经独立适配入口进入 drag framework。 | 边界 |

## 验收追踪

| AC | 关联规则 | 关联Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.4 | R-1、R-2、R-3 | TASK-SKELETON-1 | Host 单元测试与状态机测试 | `drag_drop_initiating_state_*_test_ng.cpp` |
| AC-2.1~AC-2.5 | R-4、R-5、R-6 | TASK-SKELETON-1 | `DragEvent`、`DragDropManager` 单元测试 | `drag_event_test_ng.cpp:1069`；`new_drag_drop_manager_test_ng.cpp:1908` |
| AC-3.1~AC-3.3 | R-7、R-8 | TASK-SKELETON-1 | 调用链审查、集成回调测试 | `gesture_event_hub_drag.cpp:1289,1642` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 可拖拽节点收到触摸命中 | `IDLE` 记录输入并转入 `READY`；触摸安装长按、Pan 与预览长按任务 | 非鼠标与鼠标的识别器组合不同 | AC-1.1、AC-1.4 |
| R-2 | 行为 | 触摸长按和预览长按依次满足 | 状态按 `READY → PRESS → LIFTING` 推进；预拖拽通知由对应状态产生 | 仅系统起拖成功后转入 `MOVING` | AC-1.2、AC-1.3 |
| R-3 | 边界 | 鼠标 Pan 或触摸 `PRESS/LIFTING` Pan 发起起拖 | ArkUI 调用 `InteractionInterface::StartDrag`；成功后才通知状态机 `MOVING` | 返回非成功码时不得进入 `MOVING` | AC-1.3、AC-1.4 |
| R-4 | 行为 | 有效预拖拽状态被执行 | 对有效状态派发 `onPreDrag`；`PREPARING_FOR_DRAG_DETECTION` 仅通知 | 其它正常状态按实现推进全局状态 | AC-2.1 |
| R-5 | 异常 | 重复/无效状态，或节点不可拖拽、文本拖拽、已在拖拽 | 不执行正常预拖拽推进；无效/重复状态回退为取消通知 | `ACTION_CANCELED_BEFORE_DRAG` 仅在实现允许的回调路径可见 | AC-2.2、AC-2.5 |
| R-6 | 恢复 | `WAITING` 后收到 `READY` 或 deadline 到期 | 已登记回调时执行回调、移除 deadline 并复位；取消路径移除 deadline | 无回调时 `READY` 不覆盖 `WAITING` | AC-2.3、AC-2.4、AC-2.5 |
| R-7 | 行为 | ArkUI 需要开始系统拖拽 | `StartDrag` 接收 `DragData` 与 `GetDragCallback`；MSDP 负责真实会话 | ArkUI 不以 `actionEndTask` 作为真实拖拽结束依据 | AC-3.1、AC-3.2 |
| R-8 | 边界 | 菜单预览 restart 或 C `DragAction` 主动起拖 | restart 复用手势起拖链；C Action 经 native adapter/wrapper 独立接入 | 两种入口不得被描述为同一 `onPreDrag` 回调链 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1~R-3 | `drag_drop_initiating_state_machine_test_ng` | IDLE/READY/PRESS/LIFTING/MOVING 转换及输入差异 |
| VM-2 | R-4~R-5 | `drag_event_test_ng.cpp` | 有效状态序列、重复状态取消、不可拖拽与文本拖拽分支 |
| VM-3 | R-6 | `new_drag_drop_manager_test_ng.cpp` | WAITING、READY、deadline 和无回调边界 |
| VM-4 | R-7~R-8 | Host 集成/Mock InteractionInterface | MSDP 回调触发 `onDragEnd`，及 restart/主动入口边界 |

## API 变更分析

### 新增 API

存量能力补录，不新增 API 或 C ABI。下表列出本 Feat 需要保持的既有接口边界。

| API名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联AC |
|---|---|---|---|---|---|---|
| `onPreDrag` | Public | `Callback<PreDragStatus>` | 链式组件对象 | N/A | 观察起拖前状态；动态 ArkTS API 12 起 | AC-2.1、AC-2.2 |
| `DragController.notifyDragStartRequest` | Public | `WAITING` 或 `READY` | `void` | N/A | 协调异步起拖准备；动态 ArkTS API 18 起 | AC-2.3、AC-2.4 |
| `OH_ArkUI_NodeEvent_GetPreDragStatus` | Public C API | `ArkUI_NodeEvent*` | `ArkUI_PreDragStatus` | N/A | 从 C 节点事件读取预拖拽状态 | AC-2.1 |

### 变更/废弃 API

| API名称 | 变更类型 | 影响场景 | 迁移指引 | 关联AC |
|---|---|---|---|---|
| `PreDragStatus.PREPARING_FOR_DRAG_DETECTION` | 变更 | 动态 ArkTS API 18 引入该额外通知状态 | C API 使用者不可依赖同名 C 枚举；该 C 枚举当前未暴露该值 | AC-2.1 |
| `DragController.notifyDragStartRequest` | 变更 | 动态 API 18、静态 API 23 才有该入口 | 按运行时/静态 API 可用版本防护调用 | AC-2.3 |

## 接口规格

### 接口定义

**`onPreDrag`**

| 属性 | 值 |
|---|---|
| 函数签名 | `onPreDrag(callback: Callback<PreDragStatus>): T` |
| 返回值 | `T`，当前组件以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联AC | AC-2.1、AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| `callback` | `Callback<PreDragStatus>` | 是 | N/A | 鼠标拖拽不触发；状态值以 SDK 定义为准。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联AC |
|---|---|---|---|
| 1 | 触摸预拖拽任务达到有效阶段 | 回调得到对应 `PreDragStatus` | AC-2.1 |
| 2 | 重复或无效预拖拽状态 | 不产生正常推进；适用时通知取消状态 | AC-2.2 |

**`DragController.notifyDragStartRequest`**

| 属性 | 值 |
|---|---|
| 函数签名 | `notifyDragStartRequest(requestStatus: DragStartRequestStatus): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联AC | AC-2.3、AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| `requestStatus` | `WAITING \| READY` | 是 | N/A | `READY` 仅在已保存异步回调时执行放行；版本可用性需检查。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联AC |
|---|---|---|---|
| 1 | 已保存异步回调后设置 `WAITING` 再设置 `READY` | 回调执行且 deadline 被清理 | AC-2.3 |
| 2 | 无异步回调时设置 `READY` | 不覆盖既有等待状态 | AC-2.4 |

**`OH_ArkUI_NodeEvent_GetPreDragStatus`**

| 属性 | 值 |
|---|---|
| 函数签名 | `ArkUI_PreDragStatus OH_ArkUI_NodeEvent_GetPreDragStatus(ArkUI_NodeEvent* nodeEvent)` |
| 返回值 | `ArkUI_PreDragStatus` |
| 开放范围 | Public C API |
| 错误码 | N/A；非预拖拽事件或空事件返回 `UNKNOWN` |
| 关联AC | AC-2.1、AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| `nodeEvent` | `ArkUI_NodeEvent*` | 是 | N/A | 必须是 `NODE_ON_PRE_DRAG` 对应的有效节点事件。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联AC |
|---|---|---|---|
| 1 | C 预拖拽节点事件 | 返回事件 `data[0]` 中的状态 | AC-2.1 |
| 2 | 空、错误类别或无 origin 事件 | 返回 `UNKNOWN` | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文件补录当前实现。动态 ArkTS 已在 API 18 增加 `PREPARING_FOR_DRAG_DETECTION`，C `ArkUI_PreDragStatus` 当前不含该枚举值，作为兼容风险记录。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 引擎内部状态机无新增版本门槛；`onPreDrag` 动态 API 12、`notifyDragStartRequest` 动态 API 18/静态 API 23。
- **API 版本号策略:** 以 `interface_sdk-js` 和 `interface_sdk_c` 的 `@since` 为外部契约；内部实现仅作为行为证据。

## 架构约束

| 关键约束 | 约束说明 | 影响AC |
|---|---|---|
| 状态机边界 | `DragDropInitiatingStateMachine` 只管理起拖前后状态；真实系统拖拽由 `InteractionInterface` 管理。 | AC-1.3、AC-3.1 |
| 回调线程 | MSDP 回调经 TaskExecutor 投递到 UI 线程后才执行 ArkUI 结束回调。 | AC-3.2 |
| 计时器清理 | cancel、READY 放行和 deadline 到期都必须移除 deadline。 | AC-2.3、AC-2.5 |
| API 不对称 | ArkTS 与 C 的可见预拖拽枚举集合不同，不得假设枚举一一对应。 | AC-2.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 触摸预拖拽使用现有 350ms、50ms、500ms、800ms 调度参数 | 状态机/行为测试 | `drag_event.cpp:373-383,795-825,924-973` |
| 可靠性 | 起拖失败、取消和 deadline 后不遗留预览或 timer | Host 单元测试 | `drag_event.cpp:647-780` |
| 可测试性 | 每个状态转换与 WAITING/READY 均可在 Host 测试中观察 | Host gtest | `drag_event_test_ng.cpp:1069` |
| 安全 | 真实拖拽会话由 InteractionInterface/MSDP 边界管理 | 集成测试与接口 Mock | `gesture_event_hub_drag.cpp:1289` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 触摸走长按/预览状态机 | 覆盖触摸输入与手势取消 | Host 状态机测试 | `drag_drop_event.cpp:218-263` |
| 平板 | 与手机同属触摸路径 | 无独立实现差异 | Host 状态机测试 | 同上 |
| 折叠屏 | 本 Feat 无折叠态专用分支 | 无差异 | 代码审查 | 起拖链无折叠态判断 |
| 鼠标设备 | 主要经 Pan 起拖，`onPreDrag` 不触发 | 覆盖鼠标路径 | Host/组件测试 | `common.d.ts:22701-22718` |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 本 Feat 未新增无障碍语义；拖拽状态不得由无障碍路径推断。 | AC-1.1 |
| 大字体 | 否 | 起拖状态机无字体度量分支。 | N/A |
| 深色模式 | 否 | 预览视觉样式由后续 Feat-04 覆盖。 | N/A |
| 多窗口/分屏 | 是 | 真实会话及窗口可见性由 InteractionInterface/MSDP 协作。 | AC-3.1 |
| 多用户 | 否 | 本 Feat 无用户隔离实现分支。 | N/A |
| 版本升级 | 是 | 记录 API 12/18/23 的预拖拽与放行差异。 | AC-2.1、AC-2.3 |
| 生态兼容 | 是 | C 枚举缺少动态 API 的 preparing 状态，必须降级处理。 | AC-2.1 |

## 行为场景（Gherkin）

```gherkin
Feature: 拖拽发起与预拖拽状态机
  作为 ArkUI 拖拽调用方
  我希望在真实拖拽开始前获得可控、可取消的准备阶段
  以便正确准备数据、预览和结束回调

  Scenario: 系统拖拽成功后才进入移动态
    Given 一个可拖拽的触摸组件已进入 PRESS 或 LIFTING
    When Pan 发起且 InteractionInterface.StartDrag 返回成功
    Then 起拖状态机进入 MOVING
    And MSDP 获得真实拖拽会话的结束回调

  Scenario: 异步数据准备放行
    Given 拖拽管理器已经保存异步起拖回调
    When 调用 notifyDragStartRequest(WAITING) 后调用 READY
    Then 回调执行并移除 deadline timer

  Scenario: MSDP 完成真实拖拽
    Given StartDrag 已将 GetDragCallback 注册给 MSDP
    When MSDP 调用该回调
    Then ArkUI 在 UI 线程调用 onDragEnd 并通知发起状态机结束
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN 格式，且可独立验证。
- [x] 范围边界明确：覆盖起拖与预拖拽；目标路由、数据协商、预览视觉细节由后续 Feat 承接。
- [x] AC、规则和验证映射相互关联。
- [x] 规则逐项给出可复现触发、可观察结果、边界和关联 AC。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "DragDropInitiatingStateMachine, DragEventActuator, GestureEventHub and InteractionInterface start/end callback chain"
  - repo: "OpenHarmony/interface_sdk-js"
    query: "onPreDrag, PreDragStatus and DragController.notifyDragStartRequest version contracts"
  - repo: "OpenHarmony/interface_sdk_c"
    query: "ArkUI_PreDragStatus and OH_ArkUI_NodeEvent_GetPreDragStatus contract"
```
