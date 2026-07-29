# 特性规格

## 概览

| 字段 | 内容 |
|---|---|
| 特性名称 | 落放完成、反馈与延迟结束 |
| 特性编号 | Func-04-04-07-Feat-06 |
| 所属 Epic | 04-common-capability / 04-common-events / 07-drag-capability |
| 优先级 | P1 |
| 目标版本 | 动态 ArkTS API 10/26.0.0；静态 ArkTS API 23/26.0.0；C API API 12/19/24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 落放结果/行为、默认和自定义动画、延迟结束、结果通知、完成通知及跟手形变中断 | 对已有 ArkTS/C API、GlobalController 和 Manager 行为补录，不改变实现。 |

## 输入文档

- `specs/04-common-capability/04-common-events/07-drag-capability/design.md`
- `D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@internal/component/ets/common.d.ts:10670-10675,11504,11580-11605,11676-11684`
- `D:/arkui/gitCode/ArkUI/interface_sdk-js/api/arkui/component/common.static.d.ets:6439-6449,6566-6572`
- `D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@ohos.arkui.UIContext.d.ts:3622-3625`
- `D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@ohos.arkui.UIContext.static.d.ets:2765-2768`
- `D:/arkui/gitCode/ArkUI/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h:225,237-345,952-1033`
- `interfaces/native/event/drag_and_drop_impl.cpp:925-1005`
- `frameworks/core/components_ng/manager/drag_drop/drag_drop_func_wrapper.cpp:404-444`
- `frameworks/core/components_ng/manager/drag_drop/drag_drop_global_controller.cpp:224-340`

## 用户故事

### US-1: 在落放时表达结果、行为和动画反馈

作为落放目标开发者，我希望在当前 `DragEvent` 上设置结果、copy/move 意图和自定义动画，以便系统和源端得到一致的落放反馈。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 动态 ArkTS API 10 设置 `DragResult` 和 `DragBehavior`，THEN behavior 仅表达 copy/move 意图和徽标显示，不定义实际数据处理；结果/行为供源端结束回调使用。 | 正常 |
| AC-1.2 | WHEN 动态 `useCustomDropAnimation` 为 true 且在 `onDrop` 中注册自定义动画，THEN 回调有效；WHEN 未置 true 或不在 `onDrop` 中调用，THEN 不产生该自定义动画效果。 | 边界 |
| AC-1.3 | WHEN 静态 ArkTS API 23 设置 `useCustomDropAnimation` 或自定义动画回调，THEN 使用静态 SDK 合同，不以动态 API 的调用时机或签名静默替代。 | 兼容 |
| AC-1.4 | WHEN C API API 12 调用 `DisableDefaultDropAnimation`，THEN 有效 event 写入自定义动画标记；WHEN event 为空，THEN 返回 `PARAM_INVALID`。 | 异常 |

### US-2: 延迟落放结束并回写最终决定

作为需要异步确认落放的 C API 开发者，我希望在 onDrop 阶段申请有限时延迟、使用请求 ID 通知最终结果/操作/动画并显式完成，以便系统等待既有异步处理流程。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN C API API 19 在 drop 阶段调用 `RequestDragEndPending`，THEN 获得 request ID；延迟最大等待时间为 2 秒。 | 正常 |
| AC-2.2 | WHEN 使用与申请相同的 request ID 调用 `NotifyDragResult`、`NotifySuggestedDropOperation`、`NotifyDisableDefaultDropAnimation` 或 `NotifyDragEndPendingDone`，THEN 写回相应最终决定；完成通知执行既有 stop callback 并复位 pending 状态。 | 正常 |
| AC-2.3 | WHEN request ID 不匹配或调用不在 onDrop 阶段，THEN 不接受通知；C adapter 向调用方返回 `ARKUI_ERROR_CODE_DRAG_DROP_OPERATION_NOT_ALLOWED`。 | 异常 |
| AC-2.4 | WHEN `NotifySuggestedDropOperation` 的 operation 不是 COPY 或 MOVE，THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 异常 |

### US-3: 控制跟手形变的待执行动画

作为 UIContext 使用者，我希望在 API 26.0.0 调用跟手形变中断接口，以便及时消费待执行的落放动画。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN 动态或静态 UIContext API 26.0.0 调用 `interruptFollowHandMorphDropAnimation()`，THEN 返回 boolean 表示是否存在并消费了待执行回调。 | 正常 |
| AC-3.2 | WHEN 有待执行跟手形变回调，THEN 中断接口消费并执行该回调；WHEN 不存在待执行回调，THEN 返回 false。 | 边界 |

## 验收追踪

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.4 | R-1、R-2 | Feat-06 | SDK/C API 单测 | `common.d.ts:10670-10675,11504,11676-11684`; `drag_and_drop.h:225` |
| AC-2.1~AC-2.4 | R-3~R-5 | Feat-06 | C adapter/GlobalController Host 单测 | `drag_and_drop.h:952-1033`; `drag_drop_func_wrapper.cpp:404-444` |
| AC-3.1~AC-3.2 | R-6 | Feat-06 | UIContext/GlobalController Host 单测 | `UIContext.d.ts:3622-3625`; `drag_drop_global_controller.cpp:300-340` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 在 `DragEvent` 上设置 result、behavior 或 custom drop animation | result/behavior 写入当前事件；COPY/MOVE 只表达用户可见意图和源端反馈；自定义动画需满足公开 API 前置条件 | 不将 behavior 推断为真实 UDMF 数据处理 | AC-1.1、AC-1.2、AC-1.3 |
| R-2 | 异常 | C 设置默认落放动画开关且 event 有效/为空 | 有效 event 写入 `useCustomDropAnimation`；空 event 返回 `PARAM_INVALID` | API 12 C setter 与 C API 24 的 pending 后通知不是同一入口 | AC-1.4 |
| R-3 | 行为 | C API 19 在 onDrop 阶段申请 pending | 分配递增 request ID、保存 ID，系统最多等待 2 秒 | 非 onDrop 阶段不创建可用请求 | AC-2.1 |
| R-4 | 行为 | 使用匹配 ID 发送 result/operation/animation/完成通知 | GlobalController 保存对应值；完成通知执行 stop callback 并重置 pending 状态 | operation 仅 COPY/MOVE；API 24 的动画通知受其版本约束 | AC-2.2、AC-2.4 |
| R-5 | 异常 | request ID 不匹配或通知不在 onDrop 阶段 | Wrapper 返回失败，C adapter 转换为 `DRAG_DROP_OPERATION_NOT_ALLOWED` | Header 的“不生效”在现有实现中表现为该错误码 | AC-2.3 |
| R-6 | 边界 | UIContext 调用 API 26.0.0 的跟手形变中断 | 消费并执行待执行回调后返回 true；无回调返回 false | “中断”不是丢弃回调，而是立即消费执行 | AC-3.1、AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1、R-2 | SDK/C API 单测 | result/behavior 意图边界、自定义动画前置和空 event。 |
| VM-2 | R-3~R-5 | GlobalController/adapter Host 单测 | drop-phase、2 秒、ID 匹配、错误码、完成回调。 |
| VM-3 | R-6 | UIContext/GlobalController Host 单测 | pending 回调消费、执行和无回调 false。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `DragEvent.setResult/getResult`、`dragBehavior`、`useCustomDropAnimation`/custom callback | Public ArkTS | result、behavior、布尔值、动画回调 | 当前事件/void | N/A | API 10 落放结果与自定义反馈。 | AC-1.1~AC-1.3 |
| `OH_ArkUI_DragEvent_DisableDefaultDropAnimation` | Public C API | event、disable | `int32_t` | `PARAM_INVALID` | API 12 对当前事件禁用默认落放动画。 | AC-1.4 |
| C pending request/result/operation/done 组 | Public C API | event/ID、result、operation | `int32_t` | `PARAM_INVALID`、`DRAG_DROP_OPERATION_NOT_ALLOWED` | API 19 延迟完成和最终结果反馈。 | AC-2.1~AC-2.4 |
| `OH_ArkUI_NotifyDisableDefaultDropAnimation` | Public C API | ID、disable | `int32_t` | `PARAM_INVALID`、`DRAG_DROP_OPERATION_NOT_ALLOWED` | API 24 pending 后的动画开关通知。 | AC-2.2、AC-2.3 |
| `UIContext.interruptFollowHandMorphDropAnimation` | Public ArkTS | 无 | boolean | N/A | API 26.0.0 消费待执行跟手形变动画。 | AC-3.1、AC-3.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| C pending animation 通知 | 变更 | API 24 才可通过 request ID 通知默认动画开关 | API 19–23 仅使用 request/result/operation/done 的可用子集。 | AC-2.2 |
| 跟手形变中断 | 变更 | 动态/静态 API 26.0.0 新增 | 低版本不调用；按 boolean 处理有无待执行回调。 | AC-3.1 |

## 接口规格

### 接口定义

**ArkTS `DragEvent` 落放反馈组**

| 属性 | 值 |
|---|---|
| 函数签名 | `setResult(result)`、`getResult()`、`dragBehavior`、`useCustomDropAnimation`、custom drop animation callback |
| 返回值 | 按具体 API 返回当前事件、result 或 void |
| 开放范围 | Public ArkTS |
| 错误码 | N/A |
| 关联 AC | AC-1.1、AC-1.2、AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| behavior | `DragBehavior` | 否 | COPY | 仅 COPY/MOVE 意图和徽标反馈，不决定实际数据处理。 |
| customDropAnimation | `Callback<void>` | 使用时是 | N/A | 动态 API 中仅 onDrop 且 `useCustomDropAnimation` 为 true 时有效。 |

**C pending completion 组**

| 属性 | 值 |
|---|---|
| 函数签名 | `RequestDragEndPending(event, &id)`、`NotifyDragResult(id, result)`、`NotifySuggestedDropOperation(id, operation)`、`NotifyDragEndPendingDone(id)`；API 24 `NotifyDisableDefaultDropAnimation(id, disable)` |
| 返回值 | `int32_t` |
| 开放范围 | Public C API |
| 错误码 | `PARAM_INVALID`、`DRAG_DROP_OPERATION_NOT_ALLOWED` |
| 关联 AC | AC-2.1~AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| event | `ArkUI_DragEvent*` | 请求时是 | N/A | 必须在 onDrop 阶段的有效 event 上请求。 |
| requestIdentify | `int32_t` | 是 | N/A | 必须等于 Request 返回的当前 ID；不匹配不接受。 |
| operation | `ArkUI_DropOperation` | operation 通知时是 | N/A | 仅 COPY/MOVE；其他值 `PARAM_INVALID`。 |

**`UIContext.interruptFollowHandMorphDropAnimation`**

| 属性 | 值 |
|---|---|
| 函数签名 | `interruptFollowHandMorphDropAnimation(): boolean` |
| 返回值 | true 表示消费并执行待执行回调；false 表示不存在可消费回调 |
| 开放范围 | Public ArkTS |
| 错误码 | N/A |
| 关联 AC | AC-3.1、AC-3.2 |

## 兼容性声明

- **已有 API 行为变更:** 否；补录动态 API 10/26.0.0、静态 API 23/26.0.0 与 C API 12/19/24 的既有行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；pending ID 和最终反馈仅在既有 GlobalController 的会话状态中保存。
- **最低支持版本:** ArkTS 结果/动画 API 10；静态自定义动画 API 23；C event 动画 API 12、pending API 19、pending 动画通知 API 24；跟手中断 API 26.0.0。
- **API 版本号策略:** 逐项以 canonical SDK/C header 的 `@since` 为准；C pending 与 ArkTS 自定义动画不被视为同一 API。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| onDrop 阶段边界 | C pending 的申请和全部通知仅在 GlobalController 标记的 onDrop 阶段生效。 | AC-2.1、AC-2.3 |
| request ID 一致性 | 只有当前 pending ID 可以更新 result、operation、动画或完成请求。 | AC-2.2、AC-2.3 |
| 结果与数据职责分离 | behavior 是 UI/结果反馈，不控制 UDMF 实际数据处理。 | AC-1.1 |
| 动画消费语义 | 跟手中断立即执行保存回调而非丢弃回调。 | AC-3.1、AC-3.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 可靠性 | pending 最长等待 2 秒，完成或失败后清理待处理状态。 | GlobalController Host 单测 | `drag_and_drop.h:952-956`; `drag_drop_global_controller.cpp:254-294` |
| 可测试性 | phase、ID、operation 和 stop callback 均有独立可观测结果。 | C adapter/Host 单测 | `drag_drop_func_wrapper.cpp:404-444` |
| 性能 | 自定义动画回调只承载动画逻辑，避免无关工作影响落放表现。 | SDK/性能测试 | `common.d.ts:11679-11684` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 无本 Feat 特有 API 差异 | 结果和 pending ID 合同一致。 | Host/设备集成测试 | `drag_drop_func_wrapper.cpp:404-444` |
| 平板 | 无本 Feat 特有 API 差异 | 多窗口落放路由由 `03-04-02/Feat-06` 承接。 | 多窗口集成测试 | `drag_drop_global_controller.cpp:254-294` |
| 折叠屏 | 无本 Feat 特有 API 差异 | 跟手动画消费不因显示形态改变。 | 多显示器集成测试 | `drag_drop_global_controller.cpp:336-340` |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 多窗口/分屏 | 是 | pending 回调由当前拖拽会话的 GlobalController 管理，窗口路由不在本 Feat 定义。 | AC-2.1、AC-2.2 |
| 版本升级 | 是 | API 10/12/19/23/24/26.0.0 差异需逐项保留。 | AC-1.1~AC-3.2 |
| 生态兼容 | 是 | C 错误码和 ArkTS 自定义动画回调分别维持既有合同。 | AC-1.2、AC-1.4、AC-2.3 |

## 行为场景（Gherkin）

```gherkin
Feature: 落放完成、反馈与延迟结束
  Scenario: 使用匹配 ID 完成延迟落放
    Given 当前处于 onDrop 阶段且已申请 pending request ID
    When 使用该 ID 通知最终 result 后调用 NotifyDragEndPendingDone
    Then 保存的 stop callback 被执行
    And pending 状态被复位

  Scenario: 非法的 delayed operation
    Given 当前 pending request ID 有效
    When NotifySuggestedDropOperation 传入 COPY/MOVE 之外的值
    Then 返回 ARKUI_ERROR_CODE_PARAM_INVALID

  Scenario: 消费待执行跟手形变
    Given GlobalController 保存了跟手形变回调
    When UIContext 调用 interruptFollowHandMorphDropAnimation
    Then 该回调被执行
    And 方法返回 true
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN，且可独立验证。
- [x] 覆盖动态/静态 ArkTS、C API、结果/行为、动画、延迟结束、错误码和系统回调。
- [x] 每个 AC 至少关联一条规则和一种验证方式。
- [x] 每条规则满足可复现、可观测、边界明确、关联 AC 和不冲突要求。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "Drag result behavior custom drop animation deferred drag end pending and follow-hand morph interruption"
```
