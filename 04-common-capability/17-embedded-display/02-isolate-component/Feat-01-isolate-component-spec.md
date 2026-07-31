# 特性规格

> Func-04-17-02-Feat-01 IsolateComponent 完整规格：固化 IsolateComponent 组件的创建、事件、约束和渲染流程。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | IsolateComponent 完整规格 |
| 特性编号 | Func-04-17-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 12（@dynamiconly，无 Static 版本） |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 简单 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | IsolateComponent 创建行为规格 | 补录 IsolatedOptions 解析、Want→IsolatedInfo 转换 |
| ADDED | onError 回调行为规格 | 补录错误码 10001/10002 及触发条件 |
| ADDED | Worker 约束检查行为规格 | 补录 WORKER_MAX_NUM=1 / DC_MAX_NUM_IN_WORKER=4 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/17-embedded-display/02-isolate-component/design.md` | Baselined |
| SDK | `interface_sdk-js/api/@internal/component/ets/isolated_component.d.ts` | `@since 12` |

---

## 用户故事

### US-1: 创建隔离组件

**作为** 系统应用开发者,
**我想要** 通过 `IsolatedComponent()` 创建在 RestrictedWorker 中运行的隔离组件,
**以便** 在独立线程中渲染 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `IsolatedComponent({want: wantObj, worker: restrictedWorker})` 传入合法的 Want 和 RestrictedWorker THEN 创建 IsolatedPattern，解析 Want→IsolatedInfo，在 Worker 的 NativeEngine 中创建 UIContent 并渲染 | 正常 |
| AC-1.2 | WHEN IsolatedComponent 创建后 THEN 支持 width/height/backgroundColor 三个通用属性（继承 CommonMethod） | 正常 |
| AC-1.3 | WHEN 未传入 want 或 want 格式非法 THEN 触发 `onError(10001, "paramError")` | 异常 |
| AC-1.4 | WHEN RestrictedWorker 创建失败 THEN 触发 `onError(10002, "restrictedWorkerError")` | 异常 |

### US-2: 监听错误事件

**作为** 系统应用开发者,
**我想要** 通过 `.onError()` 监听 IsolateComponent 的错误,
**以便** 在组件创建失败时进行降级处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 注册 `.onError((err) => { console.log(err.code) })` THEN 组件创建失败时回调被触发，err.code 为 10001 或 10002 | 正常 |
| AC-2.2 | WHEN 未注册 onError 且组件创建失败 THEN 静默失败，无崩溃 | 边界 |

### US-3: Worker 约束检查

**作为** 框架,
**我想要** 限制每个 Worker 中的 IsolateComponent 数量,
**以便** 防止资源耗尽。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 同一 Worker 中已存在 1 个 IsolateComponent THEN 不再允许创建新的 IsolateComponent（`WORKER_MAX_NUM = 1`） | 边界 |
| AC-3.2 | WHEN 同一 Worker 中已存在 4 个 DynamicComponent THEN 不再允许创建新的 DynamicComponent（`DC_MAX_NUM_IN_WORKER = 4`） | 边界 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 单元测试 | `isolated_pattern.cpp` |
| AC-1.2 | R-1 | 单元测试 | `js_isolated_component.cpp` |
| AC-1.3 | R-2 | 单元测试 | `FireOnErrorCallbackOnUI` |
| AC-1.4 | R-2 | 单元测试 | 同上 |
| AC-2.1 | R-2 | 单元测试 | `JsOnError` |
| AC-2.2 | R-2 | 单元测试 | 静默失败 |
| AC-3.1 | R-3 | 单元测试 | `dynamic_component_renderer_impl.cpp` |
| AC-3.2 | R-3 | 单元测试 | 同上 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 调用 `IsolatedComponent({want, worker})` | 创建 IsolatedPattern，解析 Want→IsolatedInfo（abcPath/resourcePath/entryPoint/registerComponents），在 Worker NativeEngine 中创建 UIContent | 仅支持 width/height/backgroundColor 通用属性；@dynamiconly，无 Static/Native 桥接 | AC-1.1, AC-1.2 |
| R-2 | 异常 | 创建过程中发生错误 | `onError` 回调被触发，错误码 10001（paramError）或 10002（restrictedWorkerError） | 无 onError 回调时静默失败 | AC-1.3, AC-1.4, AC-2.1, AC-2.2 |
| R-3 | 边界 | Worker 中 IsolateComponent/DynamicComponent 数量达到上限 | 拒绝创建新组件 | `WORKER_MAX_NUM=1`，`DC_MAX_NUM_IN_WORKER=4` | AC-3.1, AC-3.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.4 | 单元测试 | 创建流程 + 错误码 |
| VM-2 | AC-2.1 ~ AC-2.2 | 单元测试 | onError 回调 |
| VM-3 | AC-3.1 ~ AC-3.2 | 单元测试 | Worker 约束 |

---

## API 变更分析

N/A — 已有实现补录。

### 现有 API 清单

| API | 签名 | @since | 标签 |
|-----|------|--------|------|
| `IsolatedComponent` | `(options: IsolatedOptions) => IsolatedComponentAttribute` | 12 | @systemapi, @dynamiconly |
| `IsolatedComponentAttribute.onError` | `(callback: ErrorCallback) => IsolatedComponentAttribute` | 12 | @systemapi, @dynamiconly |

**IsolatedOptions:**
```typescript
interface IsolatedOptions {
  want: Want;
  worker: RestrictedWorker;
}
```

## 接口规格

### IsolatedComponent

| 属性 | 值 |
|------|-----|
| 函数签名 | `IsolatedComponent(options: IsolatedOptions): IsolatedComponentAttribute` |
| 开放范围 | System |
| 错误码 | 10001 (paramError), 10002 (restrictedWorkerError) |
| 关联 AC | AC-1.1 ~ AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 约束条件 |
|------|------|------|---------|
| options.want | Want | 是 | 合法 Want 对象 |
| options.worker | RestrictedWorker | 是 | 有效的 RestrictedWorker 实例 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入合法 Want + Worker | 创建 UIContent 并渲染 | AC-1.1 |
| 2 | Want 格式非法 | onError(10001) | AC-1.3 |
| 3 | Worker 创建失败 | onError(10002) | AC-1.4 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** @dynamiconly，无 Static 版本

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| 仅 @dynamiconly | 无 Static/Native/C-API 桥接 | 全部 AC |
| Worker 约束 | 每 Worker 最多 1 个 IsolateComponent | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 性能 | 每 Worker 最多 1 个 IsolateComponent | 代码审查 |
| 可靠性 | 失败时 onError 回调或静默失败 | 单元测试 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 |
|------|--------|------|
| 版本升级 | 是 | @since 12 |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "IsolatedPattern 中 Want→IsolatedInfo 的解析逻辑和 InitializeRender 流程"
  - repo: "openharmony/arkui_ace_engine"
    query: "DynamicComponentRendererImpl 中 WORKER_MAX_NUM 和 DC_MAX_NUM_IN_WORKER 的约束检查"
```