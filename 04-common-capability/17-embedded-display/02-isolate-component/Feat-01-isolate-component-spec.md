# 特性规格

> Func-04-17-02-Feat-01 跨线程隔离渲染：固化 IsolateComponent 的 RestrictedWorker 隔离渲染、Want→IsolatedInfo 转换和 Worker 约束机制。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 跨线程隔离渲染 |
| 特性编号 | Func-04-17-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 12（@dynamiconly，无 Static 版本） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 跨线程隔离渲染机制 | 补录 IsolateComponent 在 RestrictedWorker 中独立渲染的流程 |
| ADDED | Want→IsolatedInfo 转换 | 补录跨线程传递的组件信息解析（abcPath/resourcePath/entryPoint） |
| ADDED | Worker 隔离约束 | 补录 WORKER_MAX_NUM=1 的严格隔离限制 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/17-embedded-display/02-isolate-component/design.md` | Baselined |

---

## 用户故事

### US-1: RestrictedWorker 隔离渲染

**作为** 框架,
**我想要** 通过 `IsolateComponent` 在 RestrictedWorker 中独立渲染组件,
**以便** 实现 UI 的线程级隔离，防止隔离组件影响主线程稳定性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 宿主调用 `IsolateComponent({want, worker: restrictedWorker})` THEN 框架创建 `IsolatedPattern`，解析 Want 为 `IsolatedInfo`（abcPath/resourcePath/entryPoint/registerComponents），在 RestrictedWorker 的 NativeEngine 中创建独立的 UIContent 并渲染 | 正常 |
| AC-1.2 | WHEN 隔离组件渲染后 THEN 渲染结果通过 Surface 回传主线程显示，隔离组件的构建和布局在主线程之外独立执行 | 正常 |
| AC-1.3 | WHEN Want 格式非法或无法解析为 IsolatedInfo THEN 触发 `onError(10001, "paramError")` | 异常 |
| AC-1.4 | WHEN RestrictedWorker 创建失败 THEN 触发 `onError(10002, "restrictedWorkerError")` | 异常 |

### US-2: Worker 隔离约束

**作为** 框架,
**我想要** 限制每个 Worker 中的 IsolateComponent 数量,
**以便** 保证严格的线程隔离，防止资源竞争。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 同一 Worker 中已存在 1 个 IsolateComponent THEN 拒绝创建新的 IsolateComponent（`WORKER_MAX_NUM = 1`） | 边界 |
| AC-2.2 | WHEN 同一 Worker 中 DynamicComponent 数量达到 4 个 THEN 拒绝创建新 DynamicComponent（`DC_MAX_NUM_IN_WORKER = 4`），IsolateComponent 和 DynamicComponent 共享 Worker 资源池 | 边界 |

### US-3: 隔离线程异常处理

**作为** 宿主进程,
**我想要** 通过 `onError` 感知隔离线程的异常,
**以便** 在隔离组件渲染失败时进行降级。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 隔离线程发生异常 THEN `onError` 回调触发，携带错误码（10001 或 10002） | 异常 |
| AC-3.2 | WHEN 未注册 onError 且隔离线程异常 THEN 静默失败，宿主进程不崩溃 | 边界 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 集成测试 | `isolated_pattern.cpp` → `IsolatedInfo` |
| AC-1.2 | R-1 | 集成测试 | Surface 回传 |
| AC-1.3 | R-2 | 集成测试 | `FireOnErrorCallbackOnUI` |
| AC-1.4 | R-2 | 集成测试 | 同上 |
| AC-2.1 | R-3 | 单元测试 | `dynamic_component_renderer_impl.cpp` |
| AC-2.2 | R-3 | 单元测试 | 同上 |
| AC-3.1 | R-2 | 集成测试 | onError |
| AC-3.2 | R-2 | 集成测试 | 静默失败 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 宿主创建 `IsolateComponent` 节点 | 创建 `IsolatedPattern`，解析 Want → `IsolatedInfo`（abcPath/resourcePath/entryPoint/registerComponents），通过 `DynamicComponentRendererImpl::CreateIsolatedContent` 在 RestrictedWorker 的 NativeEngine 中创建独立 UIContent | SessionType = ISOLATED_COMPONENT (5)；@dynamiconly，无 Static/Native 桥接 | AC-1.1, AC-1.2 |
| R-2 | 异常 | 隔离渲染过程中发生错误 | `onError` 回调触发：错误码 10001（paramError，Want 解析失败）或 10002（restrictedWorkerError，Worker 创建失败） | 未注册 onError 时静默失败，宿主不崩溃 | AC-1.3, AC-1.4, AC-3.1, AC-3.2 |
| R-3 | 边界 | Worker 中 IsolateComponent/DynamicComponent 数量达到上限 | `DynamicComponentSafeManager` 检查约束：`WORKER_MAX_NUM=1`（每 Worker 最多 1 个 IsolateComponent），`DC_MAX_NUM_IN_WORKER=4`（每 Worker 最多 4 个 DynamicComponent） | IsolateComponent 和 DynamicComponent 共享 Worker 资源池，约束独立计算 | AC-2.1, AC-2.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.4 | 集成测试 | 跨线程隔离渲染：Want→IsolatedInfo→UIContent 创建 |
| VM-2 | AC-2.1 ~ AC-2.2 | 单元测试 | Worker 隔离约束 |
| VM-3 | AC-3.1 ~ AC-3.2 | 集成测试 | 隔离线程异常处理 |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

### 跨线程隔离渲染架构

```
宿主主线程                                   RestrictedWorker 线程
  IsolatedPattern                           DynamicComponentRendererImpl
    ├─ 解析 IsolatedOptions                    ├─ 创建 NativeEngine
    │   ├─ want → IsolatedInfo                 ├─ 创建 UIContent
    │   │   ├─ abcPath                        ├─ 执行 Build/Layout
    │   │   ├─ resourcePath                   ├─ 渲染到 Surface
    │   │   ├─ entryPoint                     └─ Surface 回传主线程
    │   │   └─ registerComponents
    │   └─ worker → RestrictedWorker
    └─ Worker 约束检查
        ├─ WORKER_MAX_NUM = 1
        └─ DC_MAX_NUM_IN_WORKER = 4
```

### IsolateComponent 与 DynamicComponent 机制对比

| 机制 | IsolateComponent | DynamicComponent |
|------|-----------------|-----------------|
| 运行环境 | RestrictedWorker（隔离线程） | Worker 线程 |
| 隔离级别 | 严格隔离（每 Worker 最多 1 个） | 共享 Worker（每 Worker 最多 4 个） |
| 通信方式 | Surface 回传 | Surface 回传 |
| API 范式 | @dynamiconly | Dynamic + Static |
| 生命周期事件 | 仅 onError | 有限事件 |
| 通用属性 | width/height/backgroundColor | 无限制 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** Dynamic API 12（@dynamiconly，无 Static 版本）
- **API 版本号策略:** 以 SDK `.d.ts` 为 API 契约

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| 严格线程隔离 | 每 Worker 最多 1 个 IsolateComponent，保证隔离线程不共享资源 | AC-2.1 |
| @dynamiconly | 无 Static/Native/C-API 桥接，仅动态范式可用 | 全部 AC |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 性能 | 隔离线程渲染不影响主线程帧率 | 集成测试 |
| 可靠性 | 隔离线程崩溃不影响宿主进程 | 集成测试 |

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
    query: "IsolatedPattern 中 Want→IsolatedInfo 的解析和 CreateIsolatedContent 的跨线程 UIContent 创建流程"
```