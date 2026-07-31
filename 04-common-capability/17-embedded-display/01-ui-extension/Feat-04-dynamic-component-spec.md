# 特性规格

> Func-04-17-01-Feat-04 跨线程动态组件加载：固化 DynamicComponent 的跨线程 Worker 加载、Placeholder 状态机和 Worker 数量约束机制。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 跨线程动态组件加载 |
| 特性编号 | Func-04-17-01-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 10+；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 跨线程 Worker 加载机制 | 补录 DynamicComponent 在 Worker 线程中加载和渲染组件的流程 |
| ADDED | Worker 数量约束 | 补录 DC_MAX_NUM_IN_WORKER=4 的并发限制 |
| ADDED | 跨线程 Placeholder 状态机 | 补录动态组件加载期间的 Placeholder 状态切换 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/17-embedded-display/01-ui-extension/design.md` | Baselined |

---

## 用户故事

### US-1: 跨线程组件加载

**作为** 框架,
**我想要** 通过 `DynamicComponent` 在指定 Worker 线程中加载和渲染组件,
**以便** 将组件构建和渲染从主线程卸载到 Worker 线程，避免阻塞 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 宿主调用 `DynamicComponent({entryPoint: "main", workerId: "w1"})` THEN 框架创建 `DynamicPattern`，解析 `DynamicParam`（workerId/entryPoint/backgroundTransparent），SessionType 为 `DYNAMIC_COMPONENT` (4) | 正常 |
| AC-1.2 | WHEN DynamicComponent 在 Worker 线程中加载组件 THEN 组件的构建（Build）和布局（Layout）在 Worker 线程执行，渲染结果通过 Surface 回传到主线程显示 | 正常 |
| AC-1.3 | WHEN 设置 `backgroundTransparent: true` THEN Worker 线程渲染的 Surface 背景透明，宿主内容可见 | 正常 |

### US-2: Worker 线程约束

**作为** 框架,
**我想要** 限制每个 Worker 线程中的 DynamicComponent 数量,
**以便** 防止单个 Worker 线程资源耗尽影响系统稳定性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 同一 Worker 线程中已存在 4 个 DynamicComponent THEN 拒绝创建新的 DynamicComponent（`DC_MAX_NUM_IN_WORKER = 4`） | 边界 |
| AC-2.2 | WHEN Worker 线程创建失败或组件加载失败 THEN `onError` 回调触发，宿主可感知 | 异常 |

### US-3: 跨线程 Placeholder 状态机

**作为** 框架,
**我想要** 在 Worker 线程加载组件期间显示 Placeholder,
**以便** 在组件未就绪时提供视觉反馈。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN Worker 线程正在加载组件 THEN 显示 `initPlaceholder` | 正常 |
| AC-3.2 | WHEN 组件加载完成且首次渲染 THEN Placeholder 移除，显示真实内容 | 正常 |
| AC-3.3 | WHEN Worker 线程加载异常 THEN 进入 UNDEFINED 状态，显示 `undefinedPlaceholder` | 异常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 集成测试 | `dynamic_pattern.cpp` |
| AC-1.2 | R-1 | 集成测试 | Worker 线程渲染管线 |
| AC-1.3 | R-1 | 集成测试 | Surface 透明 |
| AC-2.1 | R-2 | 单元测试 | `dynamic_component_manager.cpp` |
| AC-2.2 | R-2 | 集成测试 | onError |
| AC-3.1 | R-3 | 集成测试 | Placeholder 状态机 |
| AC-3.2 | R-3 | 集成测试 | 首次渲染 |
| AC-3.3 | R-3 | 集成测试 | 异常状态 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 宿主创建 `DynamicComponent` 节点 | 创建 `DynamicPattern`，解析 `DynamicParam`（workerId 指定目标 Worker 线程，entryPoint 指定入口点），通过 `DynamicComponentRendererImpl` 在 Worker 线程的 NativeEngine 中创建 UIContent 并渲染 | SessionType = DYNAMIC_COMPONENT (4)；组件构建和布局在 Worker 线程执行，渲染 Surface 回传主线程 | AC-1.1 ~ AC-1.3 |
| R-2 | 边界 | 同一 Worker 线程中 DynamicComponent 数量达到 4 个 | `DynamicComponentSafeManager` 检查 `DC_MAX_NUM_IN_WORKER = 4` 约束，拒绝创建新组件，触发 onError | 约束检查在 `DynamicComponentRendererImpl` 中执行 | AC-2.1, AC-2.2 |
| R-3 | 行为 | Worker 线程组件加载中 | 按 Placeholder 状态机显示：INIT（加载中）→ NONE（加载完成）/ UNDEFINED（加载失败） | 与跨进程 UIExtension 共享 PlaceholderType 枚举 | AC-3.1 ~ AC-3.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.3 | 集成测试 | 跨线程 Worker 加载：构建/布局/渲染管线 |
| VM-2 | AC-2.1 ~ AC-2.2 | 单元测试 | Worker 数量约束 |
| VM-3 | AC-3.1 ~ AC-3.3 | 集成测试 | Placeholder 状态机 |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

### 跨线程加载架构

```
宿主主线程                                   Worker 线程
  DynamicPattern                            DynamicComponentRendererImpl
    ├─ DynamicParam 解析                      ├─ 创建 UIContent
    │   ├─ workerId → 目标 Worker             ├─ 执行 Build/Layout
    │   ├─ entryPoint → 入口点                ├─ 渲染到 Surface
    │   └─ backgroundTransparent              └─ Surface 回传主线程
    └─ Placeholder 状态机
```

### DynamicComponent 与 UIExtensionComponent 机制对比

| 机制 | DynamicComponent | UIExtensionComponent |
|------|-----------------|---------------------|
| 运行环境 | Worker 线程（同进程） | 远程 Ability（跨进程） |
| 通信方式 | Surface 回传 | IPC 通道 + Proxy |
| 数量约束 | 每 Worker 最多 4 个 | 无硬限制 |
| Placeholder | 支持 | 支持 |
| 生命周期事件 | 有限（onError） | 完整（7 个事件） |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** Dynamic API 10；Static API 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| Worker 线程隔离 | 组件构建和布局在 Worker 线程执行，不与主线程共享状态 | AC-1.2 |
| 每 Worker 最多 4 个 | `DC_MAX_NUM_IN_WORKER = 4` 硬约束 | AC-2.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 性能 | Worker 线程加载不阻塞主线程 UI | 集成测试 |
| 可靠性 | Worker 线程异常时主线程不崩溃 | 集成测试 |

## 多设备适配声明

无差异。

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "DynamicComponentRendererImpl 中 Worker 线程 UIContent 创建和 Surface 回传流程"
```