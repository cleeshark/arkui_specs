# 特性规格

> Func-04-03-04-Feat-01 固化通用组件的鼠标光标控制、悬浮回调、悬浮效果和无障碍悬浮回调；点击、触摸和命中测试由相邻功能域承接。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 鼠标光标与悬浮效果 |
| 特性编号 | Func-04-03-04-Feat-01 |
| 所属 Epic | 无（既有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起，按 SDK 声明扩展至 API 20 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | Feat-01 职责范围 | 明确为鼠标光标与悬浮效果，包含无障碍悬浮回调；点击和触摸回调不再是本 Feat 的范围。 |

## 输入文档

- `design.md`
- `<OH_ROOT>/interface_sdk-js/api/@internal/component/ets/common.d.ts:6616-6655,20146-20281`
- `<OH_ROOT>/interface_sdk-js/api/arkui/component/common.static.d.ets:3256-3273,12072-12165`
- `<OH_ROOT>/frameworks/core/components_ng/base/view_abstract.cpp:3220-3229`
- `<OH_ROOT>/frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_common_bridge.cpp:5262-5273,8932-9313`

## 用户故事

### US-1: 在当前 UIContext 中控制鼠标光标

作为应用开发者，我想要在当前 `UIContext` 中设置或恢复鼠标光标，以便光标控制不跨越应用 UI 上下文。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 通过当前 `UIContext` 的 `cursorControl.setCursor` 设置光标 THEN SDK 声明的光标值由该 UIContext 的光标控制能力处理。 | 正常 |
| AC-1.2 | WHEN 通过当前 `UIContext` 的 `cursorControl.restoreDefault` 恢复光标 THEN 恢复该 UIContext 的默认光标。 | 正常 |
| AC-1.3 | WHEN 脱离关联 `UIContext` 使用光标控制能力 THEN 本 Feat 不定义跨 UIContext 的全局光标副作用。 | 边界 |

### US-2: 注册悬浮回调并配置悬浮效果

作为应用开发者，我想要在通用组件上注册悬浮和无障碍悬浮回调，并设置悬浮效果，以便依据既有输入与辅助功能通道更新界面反馈。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `onHover` 或 API 15 的 `onHoverMove` THEN 回调注册到组件的 `GestureEventHub` 路径。 | 正常 |
| AC-2.2 | WHEN 设置 `hoverEffect` THEN SDK 接受声明的 `HoverEffect` 值；未设置时本 Feat 不额外创建视觉效果。 | 正常 |
| AC-2.3 | WHEN 设置 `onAccessibilityHover` 或 API 20 的 `onAccessibilityHoverTransparent` THEN 对应无障碍悬浮回调成为组件事件配置；透明回调可由桥接清除。 | 正常 |
| AC-2.4 | WHEN 设备或无障碍服务未产生对应输入 THEN 注册本身不合成悬浮事件。 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-1 | SDK 审查 | `common.d.ts:6616-6655`; `common.static.d.ets:3256-3273` |
| AC-1.2 | R-2 | TASK-1 | SDK 审查 | `common.d.ts:6648-6655` |
| AC-1.3 | R-3 | TASK-1 | 架构审查 | `common.d.ts:6616-6620` |
| AC-2.1 | R-4 | TASK-1 | SDK/源码审查 | `view_abstract.cpp:3220-3229` |
| AC-2.2 | R-5 | TASK-1 | SDK 审查 | `common.d.ts:20254` |
| AC-2.3 | R-6 | TASK-1 | SDK/源码审查 | `common.d.ts:20226-20240`; `arkts_native_common_bridge.cpp:5262-5273` |
| AC-2.4 | R-7 | TASK-1 | 设备/架构审查 | SDK 事件模型 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 当前 `UIContext` 调用 `cursorControl.setCursor` | 应用 SDK 声明的光标控制 | 不推断跨 UIContext 影响 | AC-1.1 |
| R-2 | 恢复 | 当前 `UIContext` 调用 `restoreDefault` | 恢复默认光标 | 仅当前 UIContext | AC-1.2 |
| R-3 | 边界 | 缺少关联 UIContext | 本规格不定义全局光标状态 | UIContext 绑定是 SDK 使用边界 | AC-1.3 |
| R-4 | 行为 | 设置 `onHover/onHoverMove` | 回调进入 `GestureEventHub` 路径 | `onHoverMove` 为 API 15 | AC-2.1 |
| R-5 | 行为 | 设置 `hoverEffect` | 配置 SDK 声明的悬浮效果 | 实际呈现受输入设备能力影响 | AC-2.2 |
| R-6 | 行为 | 设置或清除无障碍悬浮回调 | 桥接配置对应回调 | 透明回调为 API 20 | AC-2.3 |
| R-7 | 边界 | 没有相应鼠标/悬浮/无障碍输入 | 不因注册而主动派发回调 | 系统输入能力为外部条件 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3 | SDK 审查 | `cursorControl` 的 UIContext 绑定、设置和恢复 API。 |
| VM-2 | AC-2.1~2.4 | SDK/源码审查 | 悬浮回调、效果与无障碍透明回调的版本和配置路径。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `cursorControl.setCursor/restoreDefault` | Public | 光标值/无参数 | SDK 声明值 | N/A | 在当前 UIContext 控制或恢复鼠标光标 | AC-1.1~1.3 |
| `onHover/onHoverMove/hoverEffect` | Public | 悬浮回调或效果值 | 链式对象 | N/A | 配置组件悬浮响应和反馈 | AC-2.1, AC-2.2 |
| `onAccessibilityHover*` | Public | 无障碍悬浮回调 | 链式对象 | N/A | 配置无障碍悬浮通道 | AC-2.3, AC-2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `onHoverMove` | 变更 | API 15 才可用 | 低版本使用 `onHover` 的进入/离开通知 | AC-2.1 |
| `onAccessibilityHoverTransparent` | 变更 | API 20 才可用 | 低版本使用 `onAccessibilityHover` | AC-2.3 |

## 接口规格

### 接口定义

**鼠标光标控制**

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIContext.cursorControl.setCursor(cursor)`；`UIContext.cursorControl.restoreDefault()` |
| 返回值 | 以目标 SDK 声明为准 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.3 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| cursor | SDK 声明的光标类型 | setCursor 时是 | 无 | 控制能力与当前 UIContext 绑定。 |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 `setCursor` | 设置当前 UIContext 的光标 | AC-1.1 |
| 2 | 调用 `restoreDefault` | 恢复当前 UIContext 的默认光标 | AC-1.2 |

**悬浮与无障碍悬浮**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onHover(event)`、`onHoverMove(event)`、`hoverEffect(value)`、`onAccessibilityHover(callback)`、`onAccessibilityHoverTransparent(callback)` |
| 返回值 | 动态前端 `T`；静态前端 `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.4 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event / callback | SDK 声明的 Callback | 是 | 无 | 以具体 API 的 SDK 签名为准。 |
| value | HoverEffect | 是 | 无 | 呈现由既有渲染和输入能力决定。 |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效设置悬浮回调 | 回调注册到既有事件路径 | AC-2.1 |
| 2 | 有效设置效果 | 配置视觉反馈 | AC-2.2 |
| 3 | 有无障碍悬浮输入 | 触发对应已注册回调 | AC-2.3, AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 无；本文档只调整 Feat-01 的规格归属。
- **配置文件格式变更:** 无。
- **数据存储格式变更:** 无。
- **最低支持版本:** 基础悬浮 API 以 API 7 起的 SDK 声明为准；`onHoverMove` 为 API 15，透明无障碍悬浮回调为 API 20。
- **API 版本号策略:** 动态与静态声明分别以 `common.d.ts`、`common.static.d.ets` 为准。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| UIContext 边界 | 光标控制与当前 UIContext 绑定 | AC-1.1~1.3 |
| Hub 分层 | 悬浮回调经 `GestureEventHub` 保存 | AC-2.1 |
| 外部输入 | 鼠标、悬浮能力和无障碍服务决定事件是否产生 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 每个 API 都有 SDK 声明和实现定位 | 静态审查 | 输入文档路径 |
| 生态兼容 | 不将 UIContext 作用域扩展为进程全局 | SDK 对照 | `common.d.ts:6616-6620` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 悬浮可能依赖外接设备或辅助服务 | API 语义一致 | 设备测试 | SDK 契约 |
| 平板 | 可接入鼠标或触控笔 | 光标与悬浮遵循当前 UIContext | 设备测试 | SDK 契约 |
| 折叠屏 | 折叠状态不改变注册语义 | API 语义一致 | 设备测试 | SDK 契约 |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|------|------|------|----------|
| 无障碍 | 是 | 提供独立无障碍悬浮回调通道 | AC-2.3 |
| 多窗口/分屏 | 是 | 光标控制按当前 UIContext 隔离 | AC-1.1~1.3 |
| 深色模式 | 否 | 不改变事件注册语义 | 全部 |
| 版本升级 | 是 | API 15/20 能力按 since 调用 | AC-2.1, AC-2.3 |

## 行为场景（可选，Gherkin）

L1 规格已由接口定义中的行为场景表覆盖，不重复使用 Gherkin。

## Spec 自审清单

- [x] 无待定、TBD 或 TODO 占位符
- [x] 所有 AC 使用 WHEN/THEN 格式且可测试
- [x] 范围覆盖鼠标光标、悬浮效果和无障碍悬浮
- [x] 每条规则关联 AC
- [x] 规则具备可复现触发条件和可观察结果

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "UIContext cursorControl hover effect accessibility hover and GestureEventHub routing"
```
