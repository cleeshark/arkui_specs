# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 拖拽悬停监测 |
| 术语说明 | SpringLoading 指拖拽停留在目标节点后触发的延迟/周期回调状态机，不是物理弹簧动画效果。 |
| 特性编号 | Func-03-04-02-Feat-05 |
| 优先级 | P1 |
| 目标版本 | 存量实现；动态 API 20、静态 API 26.0.0 |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 拖拽悬停监测状态机和 API 边界 | 不涉及具体组件专用拖拽。 |

## 输入文档

- `specs/03-engine-framework/04-event-framework/02-drag-framework/design.md`
- `<OH_ROOT>/interface_sdk-js/api/@internal/component/ets/common.d.ts`

## 用户故事

### US-1: 拖拽悬停监测

作为拖拽目标开发者，我希望在悬停满足配置时接收 begin/update/end/cancel，并能终止或更新配置。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 目标注册悬停监测回调且收到 Enter/Move，THEN 创建检测器并按状态机通知。 | 正常 |
| AC-1.2 | WHEN 新目标、速度阈值、Leave 或拖拽结束发生，THEN 当前检测取消或重启并回到 IDLE。 | 边界 |
| AC-1.3 | WHEN 应用不提供配置，THEN 使用 still 500ms、update 100ms、3 次通知、finish 100ms。 | 正常 |
| AC-1.4 | WHEN 回调 abort 或更新配置，THEN 后续状态推进遵循终止或新配置。 | 恢复 |

## 验收追踪

| AC | 关联规则 | 关联Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.4 | R-1~R-4 | Feat-05 | Host spring-loading 测试 | `drag_drop_spring_loading_test_ng.cpp:348` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 目标注册 callback 且 Enter/Move | Manager 懒建 detector 并 NotifyMove | 无 callback 不启用 | AC-1.1 |
| R-2 | 行为 | 检测器满足停留/更新条件 | `IDLE → BEGIN → UPDATE/END/CANCEL → IDLE` | 状态由当前 target/速度/时间决定 | AC-1.1 |
| R-3 | 边界 | 未提供配置 | 使用 500ms/100ms/3/100ms 默认值 | 默认值是现有实现基线 | AC-1.3 |
| R-4 | 恢复 | 新目标、速度超限、Leave/End 或 abort | 取消/重启，或按回调新配置继续 | 不涉及 Text/TextField 专用模式 | AC-1.2、AC-1.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1~R-2 | Host 状态机测试 | begin/update/end/cancel |
| VM-2 | R-3~R-4 | Host 配置/abort 测试 | 默认值、更新、终止 |

## API 变更分析

### 新增 API

存量补录：`onDragSpringLoading(callback, configuration?)` 为 dynamic API 20；静态 ArkTS 为 26.0.0。

### 变更/废弃 API

无废弃 API；无公共 C API，对应 C/ANI 路径仅为内部实现。

## 接口规格

### 接口定义

| 接口 | 开放范围 | 参数约束 | 行为场景 |
|---|---|---|---|
| `onDragSpringLoading` | Public ArkTS | callback 可为 null；configuration 可选 | 注册/取消检测，AC-1.1 |
| `SpringLoadingContext.abort/updateConfiguration` | Public ArkTS | 仅回调上下文可调用 | 终止/更新，AC-1.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；dynamic API 20 与 static API 26.0.0 存在版本差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 以 SDK `@since` 为准。
- **API 版本号策略:** 不将具体组件内部文本拖拽作为公共 API 能力。

## 架构约束

| 关键约束 | 约束说明 | 影响AC |
|---|---|---|
| 启用边界 | 仅有客户 callback 的目标启用检测器。 | AC-1.1 |
| 通用边界 | 不包含 Text/TextField 等组件专用拖拽实现。 | AC-1.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 使用既有 still/update 间隔，避免每次 Move 无条件回调 | Host 测试 | `drag_drop_related_configuration.h:29` |

## 多设备适配声明

所有输入设备遵循相同的通用 detector；具体组件的设备差异不在本 Feat 范围。

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 多窗口/分屏 | 是 | target 切换会取消或重启检测。 | AC-1.2 |

## 行为场景（Gherkin）

```gherkin
Feature: 拖拽悬停监测
  Scenario: 悬停后终止
    Given 目标已注册悬停监测回调
    When 拖拽 Leave 或回调 abort
    Then 检测器进入 CANCEL 并回到 IDLE
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN。
- [x] 不含具体组件专用拖拽实现。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "DragDropSpringLoadingDetector and generic SpringLoadingContext lifecycle"
```
