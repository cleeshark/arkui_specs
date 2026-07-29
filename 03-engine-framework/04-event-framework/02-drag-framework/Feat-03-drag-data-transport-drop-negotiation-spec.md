# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 拖拽数据传输与落放协商 |
| 特性编号 | Func-03-04-02-Feat-03 |
| 优先级 | P0 |
| 目标版本 | 存量实现；API 10/12/15/19/20/24 与静态 API 差异 |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 数据、UDMF、落放协商与延迟结束基线 | 不改变既有实现。 |

## 输入文档

- `specs/03-engine-framework/04-event-framework/02-drag-framework/design.md`
- `D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@internal/component/ets/common.d.ts`
- `D:/arkui/gitCode/ArkUI/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h`

## 用户故事

### US-1: 数据发布和目标准入

作为拖拽调用方，我希望发布 UDMF 数据或延迟加载参数，并仅向允许该数据类型的目标落放。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 源端设置 UnifiedData 或 DataLoadParams，THEN 框架生成 `udKey` 和摘要并传给拖拽框架。 | 正常 |
| AC-1.2 | WHEN 同一 DragEvent 调用 `setData`，THEN 延迟加载模式被清除；WHEN 调用 `setDataLoadParams`，THEN 使用延迟加载模式。 | 边界 |
| AC-1.3 | WHEN allowDrop 不匹配 UDMF 摘要或强制禁止，THEN 目标拒绝落放且不派发 Drop。 | 异常 |

### US-2: 数据获取、结果和延迟结束

作为落放目标，我希望按本地、禁用预取或远端路径取得数据，并能协商结果和异步结束。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 本地预取允许，THEN Drop 前读取 UDMF 数据；WHEN 禁用预取，THEN Drop 收到无预取 payload 的事件。 | 正常 |
| AC-2.2 | WHEN 数据是远端或未同步，THEN 后台重试获取后再回 UI 执行 Drop。 | 边界 |
| AC-2.3 | WHEN Drop 完成，THEN ArkUI 将 result/behavior 交给 `InteractionInterface::StopDrag`。 | 正常 |
| AC-2.4 | WHEN C API 在 Drop 阶段请求延迟结束，THEN 只能在最多 2 秒内通知结果并 Done；超时按失败默认收尾。 | 恢复 |

## 验收追踪

| AC | 关联规则 | 关联Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.3 | R-1~R-3 | Feat-03 | Host/UDMF mock | `drag_drop_func_wrapper.cpp:206` |
| AC-2.1~AC-2.4 | R-4~R-7 | Feat-03 | Host/C API 测试 | `drag_and_drop_test.cpp:1721` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 源端设置数据或加载参数 | 发布 UDMF 数据/延迟信息并生成摘要和 udKey | UDMF 持有实际数据 | AC-1.1 |
| R-2 | 边界 | setData 与 setDataLoadParams | 前者清延迟模式，后者启用延迟模式 | 后一次设置决定模式 | AC-1.2 |
| R-3 | 异常 | allowDrop 不匹配或 force-disallow | 拒绝 Drop、更新拒绝状态并 reset | 空 allowDrop/空摘要接受全部 | AC-1.3 |
| R-4 | 行为 | 本地允许预取 | 读取 UDMF 并带入 Drop 事件 | 读取失败事件标记未成功 | AC-2.1 |
| R-5 | 边界 | 禁用预取或远端数据 | 禁用预取直接 Drop；远端重试后投递 UI Drop | 预览平台 UDMF 无功能实现 | AC-2.1、AC-2.2 |
| R-6 | 行为 | Drop 回调返回结果/行为 | 调用 InteractionInterface.StopDrag | UNKNOWN 按现有同源规则默认 MOVE/COPY | AC-2.3 |
| R-7 | 恢复 | C Drop 请求 pending | 2 秒内 result/operation/animation/Done；超时失败默认收尾 | 仅 Drop phase 可请求 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1~R-3 | UDMF/Manager Host 测试 | 数据发布、类型过滤 |
| VM-2 | R-4~R-6 | Host/Interaction mock | 本地、远端、结果协商 |
| VM-3 | R-7 | C API 单元测试 | pending、通知、超时 |

## API 变更分析

### 新增 API

存量补录；涉及 `DragEvent.setData/getData/setResult/getResult`（dynamic API 10）、`startDataLoading`（15）、`setDataLoadParams`（20）和 C pending API（19，部分协商 API 24）。

### 变更/废弃 API

静态 ArkTS 的数据 API 从 API 23/26 起可用，必须与 dynamic API 的 10/15/20 分别标注。

## 接口规格

### 接口定义

| 接口 | 开放范围 | 参数约束 | 行为场景 |
|---|---|---|---|
| `DragEvent.setData/setDataLoadParams` | Public | 两者互斥，最后设置决定模式 | 发布即时/延迟数据，AC-1.1~1.2 |
| `DragEvent.startDataLoading` | Public | 仅 onDrop、需要有效 udKey | 异步数据获取，AC-2.1~2.2 |
| `OH_ArkUI_DragEvent_RequestDragEndPending` | Public C | 仅 Drop phase，最多 2 秒 | 延迟收尾，AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；记录 dynamic/static/C 的版本差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；数据由 UDMF 持有。
- **最低支持版本:** 以各 SDK `@since` 为准。
- **API 版本号策略:** 逐项标注 10/12/15/19/20/24 及静态 23/26。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| UDMF 边界 | ArkUI 传输 key/摘要，UDMF 持有数据。 | AC-1.1 |
| 协商边界 | ArkUI 将最终 result/behavior 交 InteractionInterface.StopDrag。 | AC-2.3 |
| pending 限制 | pending 仅 Drop phase 且受 deadline 约束。 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 可靠性 | pending 最多 2 秒并有默认收尾 | C API 测试 | `drag_drop_global_controller.cpp:194` |
| 性能 | 远端数据后台重试，不阻塞 UI Drop | Host/集成 | `drag_drop_manager.cpp:1438` |

## 多设备适配声明

远端/跨设备数据使用异步重试；预览平台 UDMF 无功能实现，测试不得把其当作 OHOS UDMF 行为。

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 多窗口/分屏 | 是 | 数据 key 和来源信息跨容器传递。 | AC-2.2 |
| 生态兼容 | 是 | UDMF/InteractionInterface 为系统边界。 | AC-1.1 |

## 行为场景（Gherkin）

```gherkin
Feature: 拖拽数据传输与落放协商
  Scenario: 类型不匹配
    Given 目标 allowDrop 不包含源 UDMF 摘要类型
    When 拖拽结束
    Then 不派发 Drop
    And 框架重置拖拽状态
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN。
- [x] 数据、协商、远端和 pending 边界均有规则与验证。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "UDMF transport, IsDropAllowed, remote data retrieval and drag end pending"
```
