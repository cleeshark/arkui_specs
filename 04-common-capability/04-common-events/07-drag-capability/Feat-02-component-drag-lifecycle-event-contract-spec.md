# 特性规格

## 概览

| 字段 | 内容 |
|---|---|
| 特性名称 | 组件拖拽生命周期与事件契约 |
| 特性编号 | Func-04-04-07-Feat-02 |
| 所属 Epic | 04-common-capability / 04-common-events / 07-drag-capability |
| 优先级 | P1 |
| 目标版本 | 动态 ArkTS API 8/10/12/15；静态 ArkTS API 23；C API API 12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 源/目标生命周期回调、事件对象和 C NodeEvent 提取契约 | 存量行为补录；数据和完成结果 API 分别由 Feat-03/Feat-06 承接。 |

## 输入文档

- `specs/04-common-capability/04-common-events/07-drag-capability/design.md`
- `<OH_ROOT>/interface_sdk-js/api/@internal/component/ets/common.d.ts:11371-11512,22461-22558,22718`
- `<OH_ROOT>/interface_sdk-js/api/arkui/component/common.static.d.ets:6390-6395,13109-13194,13247`
- `<OH_ROOT>/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h:195-249`
- `frameworks/core/pipeline_ng/pipeline_context.cpp:6248-6275`
- `frameworks/core/components_ng/manager/drag_drop/drag_drop_manager.cpp:1072-1085,1229-1289,1949-1974,3189-3201`
- `frameworks/core/components_ng/event/gesture_event_hub_drag.cpp:1289,1642-1697`

## 用户故事

### US-1: 监听源端生命周期

作为拖拽源开发者，我希望接收起拖、预拖拽和真实结束回调，以便准备预览并在系统会话结束后收尾。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 动态 ArkTS 注册 `onDragStart`，THEN API 8 契约允许回调返回 `CustomBuilder` 或 `DragItemInfo`。 | 正常 |
| AC-1.2 | WHEN 动态 ArkTS 注册 `onPreDrag`，THEN API 12 契约提供 `PreDragStatus`；静态 ArkTS API 23 允许 `undefined` 解除注册。 | 边界 |
| AC-1.3 | WHEN MSDP 通过 `GetDragCallback` 通知真实拖拽结束，THEN ArkUI 投递 UI 任务并派发源端 `onDragEnd`；手势 `actionEndTask` 不作为该结束信号。 | 正常 |

### US-2: 接收目标端 enter/move/leave/drop

作为落放目标开发者，我希望在合法目标中按现有顺序收到生命周期事件。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 目标注册 `onDrop` 且拖拽首次进入该目标，THEN Manager 派发 Enter；WHEN 后续命中同一目标，THEN 派发 Move。 | 正常 |
| AC-2.2 | WHEN 命中目标变更或拖拽离开当前目标，THEN Manager 先对上一目标派发 Leave，再对新目标派发 Enter；父子嵌套仅在严格上报时 Leave 父目标。 | 边界 |
| AC-2.3 | WHEN 目标未注册 `onDrop`，THEN ArkTS enter/move/leave 不作为有效目标事件；WHEN `onDrop` 使用 API 15 重载，THEN `DropOptions` 按 SDK 契约传入。 | 边界 |

### US-3: 从 C NodeEvent 读取生命周期上下文

作为 C API 开发者，我希望从拖拽 NodeEvent 取得 `ArkUI_DragEvent` 或预拖拽状态。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN C 回调收到有效拖拽 NodeEvent，THEN `OH_ArkUI_NodeEvent_GetDragEvent` 返回该事件对象；WHEN 事件无效或不属于拖拽，THEN 返回 null。 | 异常 |
| AC-3.2 | WHEN C 回调读取预拖拽 NodeEvent，THEN `OH_ArkUI_NodeEvent_GetPreDragStatus` 返回 C 枚举值；动态 ArkTS 的额外 preparing 状态不被 C 枚举静默伪造。 | 边界 |

## 验收追踪

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.3 | R-1、R-2 | Feat-02 | SDK/Interaction mock | `common.d.ts:22461,22558,22718`; `gesture_event_hub_drag.cpp:1289,1642-1697` |
| AC-2.1~AC-2.3 | R-3、R-4 | Feat-02 | Manager Host 单测 | `common.d.ts:22464-22543`; `drag_drop_manager.cpp:1072-1085,3189-3201` |
| AC-3.1、AC-3.2 | R-5 | Feat-02 | C NodeEvent 单测 | `drag_and_drop.h:195-211` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 注册源端 onDragStart/onPreDrag/onDragEnd | 按动态/静态 SDK 签名保存回调；静态回调可传 undefined | 动态 API 8/10/12 与静态 API 23 分别适用 | AC-1.1、AC-1.2 |
| R-2 | 行为 | `GetDragCallback` 收到系统结束通知 | 投递 UI 任务后派发 onDragEnd 并复位状态机 | 不把 gesture `actionEndTask` 当真实拖拽结束 | AC-1.3 |
| R-3 | 行为 | 有效目标注册 onDrop 且系统事件到达 Manager | 同目标 Move；新目标 Leave 旧目标后 Enter 新目标；结束时按目标/数据条件处理 Drop | 系统入口是 PipelineContext，不是 DragDropProxy | AC-2.1、AC-2.2 |
| R-4 | 边界 | 目标没有 onDrop，或父子目标切换 | enter/move/leave 依赖 onDrop；严格上报才对父目标 Leave；API 15 onDrop 重载可接收 DropOptions | 不把无目标/不允许数据推断为有效 Drop | AC-2.2、AC-2.3 |
| R-5 | 异常 | C 从 NodeEvent 提取拖拽事件/预拖拽状态 | 无效或非拖拽事件返回 null；预拖拽返回 C 枚举可表达值 | C 枚举与动态 ArkTS preparing 状态存在不对称 | AC-3.1、AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1、R-2 | SDK 对照、Interaction mock | 版本、解除注册、真实结束边界 |
| VM-2 | R-3、R-4 | DragDropManager Host 单测 | Enter/Move/Leave/Drop 顺序和 strict reporting |
| VM-3 | R-5 | C NodeEvent 单测 | 事件指针、预拖拽枚举和无效输入 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `onDragStart/Enter/Move/Leave/Drop/End/onPreDrag` | Public ArkTS | 回调；`onDrop` API 15 可选 DropOptions | 当前组件 | N/A | 源端/目标端生命周期监听 | AC-1.1~AC-2.3 |
| `OH_ArkUI_NodeEvent_GetDragEvent/GetPreDragStatus` | Public C API | `ArkUI_NodeEvent*` | 事件指针/C 枚举 | 无效事件返回 null | 读取 C 生命周期上下文 | AC-3.1、AC-3.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| `onDrop` | 变更 | 动态 API 15 增加 `OnDragEventCallback, DropOptions?` 重载 | 旧回调保持 API 8 契约；按 SDK 版本选择重载 | AC-2.3 |
| 生命周期回调 | 变更 | 静态 API 23 允许 undefined，动态版本与引入时点不同 | 不以静态可空性改写动态 API | AC-1.2、AC-2.3 |
| `PreDragStatus` | 变更 | 动态 ArkTS 与 C 枚举不对称 | 保留差异；不扩展既有 C ABI | AC-3.2 |

## 接口规格

### 接口定义

| 接口组 | 开放范围 | 参数约束 | 行为场景 |
|---|---|---|---|
| 源端 `onDragStart/onPreDrag/onDragEnd` | Public ArkTS | 返回预览仅适用于 onDragStart；静态回调可 undefined | 起拖准备、预拖拽状态和 MSDP 结束，AC-1.1~AC-1.3 |
| 目标端 `onDragEnter/onDragMove/onDragLeave/onDrop` | Public ArkTS | 有效目标事件依赖 onDrop；API 15 可传 DropOptions | 目标路由和落放，AC-2.1~AC-2.3 |
| C NodeEvent getters | Public C API | NodeEvent 必须是相应拖拽事件 | 提取事件或预拖拽状态，AC-3.1、AC-3.2 |

## 兼容性声明

- **已有 API 行为变更:** 否；补录 API 8/10/12/15/23 与 C API 12 的既有差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 动态目标/起拖回调 API 8、onDragEnd API 10、onPreDrag API 12、onDrop 重载 API 15、静态 API 23、C NodeEvent API 12。
- **API 版本号策略:** 每个回调以 SDK @since 为准；C `PreDragStatus` 不补写动态 ArkTS 独有值。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 系统派发入口 | MMI 事件经 PipelineContext 分发 Manager，Proxy 仅模拟起拖后路径。 | AC-2.1、AC-2.2 |
| onDrop 前提 | 目标端 enter/move/leave 的公开契约以 onDrop 绑定为前提。 | AC-2.3 |
| 真实结束边界 | 只有 GetDragCallback 代表系统拖拽结束。 | AC-1.3 |
| 数据职责分离 | C DragEvent 的数据/结果读写由 Feat-03/Feat-06 承接。 | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 可靠性 | 无效 NodeEvent 不返回可用 DragEvent 指针。 | C 单测 | `drag_and_drop.h:195-211` |
| 可测试性 | 回调顺序可由 Manager Host 测试观察。 | Host 单测 | `drag_drop_manager.cpp:1072-1085,1949-1974` |

## 多设备适配声明

所有设备使用相同生命周期契约；多窗口/显示器的事件路由和坐标由 `03-04-02/Feat-06` 承接，不在本 Feat 定义差异。

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 多窗口/分屏 | 是 | 目标路由遵从当前容器事件链。 | AC-2.1、AC-2.2 |
| 版本升级 | 是 | 回调版本和动态/静态可空性差异显式声明。 | AC-1.1~AC-2.3 |
| 生态兼容 | 是 | C 仅从 NodeEvent 提取其可表达状态。 | AC-3.1、AC-3.2 |

## 行为场景（Gherkin）

```gherkin
Feature: 组件拖拽生命周期
  Scenario: 目标切换
    Given 旧目标和新目标均已绑定 onDrop
    When 系统拖拽移动到新目标
    Then 旧目标先收到 Leave
    And 新目标收到 Enter

  Scenario: 真实源端结束
    Given ArkUI 已通过 InteractionInterface 发起系统拖拽
    When GetDragCallback 收到结束通知
    Then UI 任务派发 onDragEnd
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN，且可独立验证。
- [x] 覆盖动态/静态 ArkTS、C NodeEvent、派发顺序和版本差异。
- [x] 每个 AC 至少关联一条规则和一种验证方式。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "DragDropManager lifecycle dispatch and GestureEventHub GetDragCallback end boundary"
```
