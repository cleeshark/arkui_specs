# 特性规格

> Func-04-03-04-Feat-01 固化通用组件的点击、触摸、鼠标、悬停及无障碍悬停回调与反馈效果。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 指针、悬停与无障碍悬停事件 |
| 特性编号 | Func-04-03-04-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起，扩展至 API 20 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 指针、悬停与无障碍悬停规格 | 补录既有 CommonMethod 行为，不修改实现。 |

## 输入文档

- `design.md`
- `interface/sdk-js/api/@internal/component/ets/common.d.ts:20146-20281`
- `interface/sdk-js/api/arkui/component/common.static.d.ets:12072-12165`
- `frameworks/core/components_ng/base/view_abstract.cpp:3099-3239`

## 用户故事

### US-1: 注册指针与悬停回调

作为应用开发者，我想要在通用组件上注册指针与悬停回调，以便根据用户输入更新应用状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `onClick`、`onTouch` 或 `onMouse` 回调 THEN 动态桥将回调交给 `ViewAbstract` 对应 SetOn 方法。 | 正常 |
| AC-1.2 | WHEN 设置 `onHover` 或 API 15 的 `onHoverMove` THEN 回调被注册到组件的 GestureEventHub。 | 正常 |
| AC-1.3 | WHEN `onClick` 使用 API 12 的 `distanceThreshold` 重载 THEN SDK 以该数值作为重载参数传入；未使用重载时保持基础 click 签名。 | 边界 |

### US-2: 接收无障碍悬停和反馈效果

作为辅助功能用户，我想要组件报告无障碍悬停，并允许应用设置悬停效果，以便获得可感知的焦点反馈。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `onAccessibilityHover` THEN API 12 动态/静态声明的回调成为组件事件配置。 | 正常 |
| AC-2.2 | WHEN 设置 API 20 `onAccessibilityHoverTransparent` THEN 动态桥可设置或清除透明悬停回调。 | 正常 |
| AC-2.3 | WHEN 设置 `hoverEffect` THEN SDK 接受 HoverEffect 值；未设置时不由本特性额外创建效果。 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-1 | 代码与 SDK 审查 | `arkts_native_common_bridge.cpp:8932-9313,9855-9884` |
| AC-1.2 | R-2 | TASK-1 | 代码与 SDK 审查 | `view_abstract.cpp:3220-3229` |
| AC-1.3 | R-3 | TASK-1 | SDK 审查 | `common.d.ts:20146-20183` |
| AC-2.1 | R-4 | TASK-1 | SDK 审查 | `common.d.ts:20226-20240` |
| AC-2.2 | R-5 | TASK-1 | 代码审查 | `arkts_native_common_bridge.cpp:5262-5273` |
| AC-2.3 | R-6 | TASK-1 | SDK 审查 | `common.d.ts:20254` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 onClick/onTouch/onMouse 回调 | Bridge 调用 ViewAbstract，回调由组件 Hub 保存 | 回调为可选值 | AC-1.1 |
| R-2 | 行为 | 设置 onHover/onHoverMove | ViewAbstract 将悬停回调写入 GestureEventHub 路径 | onHoverMove 为 API 15 | AC-1.2 |
| R-3 | 边界 | 使用 onClick(callback, distanceThreshold) | 采用 API 12 重载参数 | 基础重载自 API 7 | AC-1.3 |
| R-4 | 行为 | 设置 onAccessibilityHover | 注册 API 12 无障碍悬停回调 | 不等同于普通 onHover | AC-2.1 |
| R-5 | 恢复 | 清除透明无障碍悬停回调 | Bridge 向 ViewAbstract 设置空回调 | API 20 | AC-2.2 |
| R-6 | 行为 | 设置 hoverEffect | 配置 HoverEffect 值 | 效果实际呈现受设备输入能力影响 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3 | SDK/桥接审查 | 回调与 distanceThreshold 重载。 |
| VM-2 | AC-2.1~2.3 | SDK/桥接审查 | 无障碍 API 版本、清除路径与反馈配置。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `onClick/onTouch/onMouse` | Public | 各自 Event Callback | `T`/`this` | N/A | 注册基础指针回调 | AC-1.1 |
| `onHover/onHoverMove/hoverEffect` | Public | Hover callback 或 effect | `T`/`this` | N/A | 注册悬停回调或视觉反馈 | AC-1.2, AC-2.3 |
| `onAccessibilityHover*` | Public | Accessibility callback | `T`/`this` | N/A | 注册无障碍悬停 | AC-2.1, AC-2.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `onHoverMove` | 变更 | API 15 才可用 | 低版本使用 onHover 的进入/离开通知 | AC-1.2 |
| `onAccessibilityHoverTransparent` | 变更 | API 20 才可用 | 低版本使用 onAccessibilityHover | AC-2.2 |

## 接口规格

### 接口定义

**Pointer and hover callbacks**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onClick(event[, distanceThreshold])`、`onTouch(event)`、`onMouse(event)`、`onHover(event)`、`onHoverMove(event)` |
| 返回值 | 链式 `T`（动态）或 `this`（静态） |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.3 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | Callback | 是 | 无 | 回调依据具体 API 接收 Click/Touch/Mouse/HoverEvent。 |
| distanceThreshold | number/double | 否 | SDK 未声明默认值 | 仅 onClick API 12 重载。 |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|----------|
| 1 | 回调有效 | 桥接注册至通用 View 事件路径 | AC-1.1, AC-1.2 |
| 2 | 使用阈值重载 | 使用 SDK 定义的第二参数 | AC-1.3 |

**Accessibility hover and effect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onAccessibilityHover(callback)`、`onAccessibilityHoverTransparent(callback)`、`hoverEffect(value)` |
| 返回值 | 链式 `T`/`this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.3 |

## 兼容性声明

- **已有 API 行为变更:** 无；本文件补录已有行为。
- **配置文件格式变更:** 无。
- **数据存储格式变更:** 无。
- **最低支持版本:** 基础 pointer API 为 API 7，`onHoverMove` API 15，透明无障碍悬停 API 20。
- **API 版本号策略:** 动态与静态声明分别以 `common.d.ts`、`common.static.d.ets` 为准。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Hub 分层 | 指针与悬停通过 GestureEventHub 路径保存 | AC-1.1, AC-1.2 |
| 外部输入 | 指针设备、悬停能力和无障碍服务决定系统是否产生对应事件 | AC-1.1~2.3 |
| 边界归属 | 命中测试/手势仲裁不在本 Feat 定义 | 全部 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 每个 API 具备 SDK 声明和桥接定位 | 静态审查 | 输入文档路径 |
| 生态兼容 | 动态/静态签名分别记录 | SDK 对照 | `common*.d.ts` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 触摸为主要输入，悬停取决于外设 | API 保持一致 | 设备测试 | SDK 契约 |
| 平板 | 可接鼠标/触控笔产生悬停或鼠标事件 | API 保持一致 | 设备测试 | SDK 契约 |
| 折叠屏 | 折叠状态不改变注册语义 | API 保持一致 | 设备测试 | SDK 契约 |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|------|------|------|----------|
| 无障碍 | 是 | 无障碍悬停提供独立回调通道 | AC-2.1, AC-2.2 |
| 深色模式 | 否 | 不改变事件注册 | 全部 |
| 多窗口/分屏 | 是 | 事件由当前组件容器分发 | AC-1.1 |
| 版本升级 | 是 | API 15/20 功能须按 since 调用 | AC-1.2, AC-2.2 |

## 行为场景（可选，Gherkin）

L1 规格已在接口定义的行为场景表中覆盖，不重复使用 Gherkin。

## Spec 自审清单

- [x] 无待定、TBD 或 TODO 占位符
- [x] 所有 AC 使用 WHEN/THEN 格式且可测试
- [x] 范围边界明确
- [x] 每条规则关联 AC
- [x] 规则具备可复现触发条件和可观察结果

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "CommonMethod pointer hover accessibility hover callback routing through ViewAbstract and GestureEventHub"
```
