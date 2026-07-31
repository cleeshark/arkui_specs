# 特性规格

> Func-04-17-01-Feat-04 DynamicComponent：固化 DynamicComponent 的创建、约束和渲染机制。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DynamicComponent |
| 特性编号 | Func-04-17-01-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 10+；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | DynamicComponent 创建行为 | 补录 DynamicPattern 创建 + DynamicParam 参数 |
| ADDED | Placeholder 机制 | 补录 5 种 Placeholder 类型枚举 |
| ADDED | Worker 约束 | 补录 DC_MAX_NUM_IN_WORKER = 4 约束 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/17-embedded-display/01-ui-extension/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 DynamicComponent

**作为** 应用开发者,
**我想要** 通过 `DynamicComponent(options)` 创建动态组件,
**以便** 在 Worker 中动态加载和渲染组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `DynamicComponent({entryPoint: "main", workerId: "w1"})` THEN 创建 DynamicPattern，使用 DynamicParam 初始化 | 正常 |
| AC-1.2 | WHEN 设置 `backgroundTransparent: true` THEN 组件背景透明 | 正常 |
| AC-1.3 | WHEN 设置 `isReportFrameEvent: true` THEN 启用帧事件上报 | 正常 |

### US-2: Placeholder 状态管理

**作为** 框架,
**我想要** 在不同状态下显示不同的 Placeholder,
**以便** 在组件加载/旋转/折叠时提供视觉反馈。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 组件未初始化 THEN 显示 `initPlaceholder`（PlaceholderType::INIT） | 正常 |
| AC-2.2 | WHEN 组件旋转 THEN 显示 `rotationPlaceholder`（PlaceholderType::ROTATION） | 正常 |
| AC-2.3 | WHEN 组件折叠展开 THEN 显示 `foldToExpandPlaceholder`（PlaceholderType::FOLD_TO_EXPAND） | 正常 |
| AC-2.4 | WHEN 组件状态未定义 THEN 显示 `undefinedPlaceholder`（PlaceholderType::UNDEFINED） | 正常 |

### US-3: Worker 约束检查

**作为** 框架,
**我想要** 限制每个 Worker 中的 DynamicComponent 数量,
**以便** 防止资源耗尽。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 同一 Worker 中 DynamicComponent 数量达到 4 个 THEN 拒绝创建新的 DynamicComponent | 边界 |
| AC-3.2 | WHEN 组件创建失败 THEN `onError` 回调被触发 | 异常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 单元测试 | `dynamic_pattern.cpp` |
| AC-1.2 | R-1 | 单元测试 | `backgroundTransparent` |
| AC-1.3 | R-1 | 单元测试 | `isReportFrameEvent` |
| AC-2.1 | R-2 | 单元测试 | PlaceholderType::INIT |
| AC-2.2 | R-2 | 单元测试 | PlaceholderType::ROTATION |
| AC-2.3 | R-2 | 单元测试 | PlaceholderType::FOLD_TO_EXPAND |
| AC-2.4 | R-2 | 单元测试 | PlaceholderType::UNDEFINED |
| AC-3.1 | R-3 | 单元测试 | `dynamic_component_manager.cpp` |
| AC-3.2 | R-3 | 单元测试 | onError |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 调用 `DynamicComponent(options)` | 创建 DynamicPattern，解析 DynamicParam（workerId/entryPoint/backgroundTransparent） | SessionType = DYNAMIC_COMPONENT (4) | AC-1.1 ~ AC-1.3 |
| R-2 | 行为 | 组件状态变化 | 根据 PlaceholderType 枚举显示对应 Placeholder | 5 种 Placeholder：INIT/ROTATION/FOLD_TO_EXPAND/UNDEFINED/NONE | AC-2.1 ~ AC-2.4 |
| R-3 | 边界 | Worker 中 DynamicComponent 数量达到上限 | 拒绝创建，触发 onError | `DC_MAX_NUM_IN_WORKER = 4` | AC-3.1, AC-3.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.3 | 单元测试 | DynamicComponent 创建 |
| VM-2 | AC-2.1 ~ AC-2.4 | 单元测试 | Placeholder 状态切换 |
| VM-3 | AC-3.1 ~ AC-3.2 | 单元测试 | Worker 约束 |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

### DynamicComponent 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entryPoint | string | 是 | 入口点名 |
| workerId | string | 是 | Worker ID |
| backgroundTransparent | boolean | 否 | 背景透明 |
| isReportFrameEvent | boolean | 否 | 启用帧事件上报 |

### PlaceholderType 枚举

| 值 | 说明 |
|----|------|
| INIT | 初始加载占位 |
| ROTATION | 旋转占位 |
| FOLD_TO_EXPAND | 折叠展开占位 |
| UNDEFINED | 未定义状态占位 |
| NONE | 无占位 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 10

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 性能 | 每 Worker 最多 4 个 DynamicComponent | 代码审查 |

## 多设备适配声明

| 设备类型 | 行为差异 | 说明 |
|----------|---------|------|
| 折叠屏 | 使用 foldToExpandPlaceholder | 折叠/展开状态切换 |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "DynamicPattern 中 DynamicParam 的解析和 Worker 约束检查"
```