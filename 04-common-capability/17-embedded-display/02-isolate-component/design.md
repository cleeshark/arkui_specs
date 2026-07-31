# 架构设计

> 嵌入显示能力-IsolateComponent 功能域的架构设计文档，补录已有实现。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-04-17-02 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | Feat-01 IsolateComponent 完整规格 |
| 复杂度 | 简单 |
| 目标版本 | Dynamic API 12（@dynamiconly）
| Owner | ArkUI SIG |
| 状态 | Baselined（已有实现补录） |

## 需求基线

| 项 | 内容 |
|----|------|
| 问题陈述 | 需要在 RestrictedWorker 中运行独立组件，实现 UI 隔离渲染 |
| 核心目标 | 提供 IsolateComponent 组件，通过 `IsolatedOptions` 传入 Want 和 RestrictedWorker，在隔离线程中渲染组件内容 |
| P0 AC | 正确创建 IsolateComponent；RestrictedWorker 中渲染组件；onError 回调正确触发 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 模块 | 当前职责 | 本 Feature 影响 |
|------|------|----------|-----------------|
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/isolated_component/isolated_pattern.h/cpp` | IsolatedPattern 核心逻辑 | 核心实现 |
| ace_engine | `frameworks/bridge/declarative_frontend/jsview/js_isolated_component.h/cpp` | JS 桥接 | 输入校验 |
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/ui_extension_model.h` | 抽象模型接口 | API 接口 |
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/ui_extension_model_ng.h/cpp` | NG 模型实现 | API 实现 |
| ace_engine | `frameworks/core/common/dynamic_component_renderer.h` | IsolatedInfo 结构体 | 数据结构 |
| ace_engine | `adapter/ohos/entrance/dynamic_component/dynamic_component_renderer_impl.h/cpp` | OHOS 渲染器实现 | 平台适配 |
| interface_sdk-js | `api/@internal/component/ets/isolated_component.d.ts` | SDK 类型定义 | 类型定义 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| JS Bridge | `js_isolated_component` | 解析 ArkTS 调用，解析 Want/Worker | 存量分析 |
| Model 层 | `ui_extension_model_ng` | `CreateIsolatedComponent` / `InitializeIsolatedComponent` | 存量分析 |
| Pattern 层 | `isolated_pattern` | 生命周期管理、Want→IsolatedInfo 解析、InitializeRender | 存量分析 |
| Renderer 层 | `dynamic_component_renderer_impl` | UIContent 创建、Worker 约束检查 | 存量分析 |

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | 涉及 JS Bridge → Model → Pattern → Renderer 单向调用 | 严格单向调用 | 代码评审 |
| OH-ARCH-API-LEVEL | @since 12, @systemapi, @dynamiconly | 仅动态范式支持 | API 评审 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| 性能 | 约束：每 Worker 最多 1 个 IsolateComponent，每 Worker 最多 4 个 DynamicComponent |
| 安全与权限 | @systemapi，仅系统应用可用 |
| 兼容性 | @dynamiconly，无 Static/Native 桥接 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 影响 |
|---------|------|----------|------|
| ADR-1 | IsolateComponent 的 API 范式 | 仅 @dynamiconly，无 Static/C-API 桥接 | 最简 API 表面 |
| ADR-2 | Worker 数量约束 | 每 Worker 最多 1 个 IsolateComponent（`WORKER_MAX_NUM=1`），每 Worker 最多 4 个 DynamicComponent（`DC_MAX_NUM_IN_WORKER=4`） | 防止资源耗尽 |

## 后续 Task 拆分

| Task ID | 目标 | 受影响文件 | 依赖 |
|---------|------|-----------|------|
| Feat-01 | IsolateComponent 完整规格 | Feat-01-isolate-component-spec.md | 无 |

## API 签名、Kit 与权限

| API 签名 | 类型 | Kit | d.ts 位置 | 权限要求 |
|----------|------|-----|-----------|----------|
| `IsolatedComponent(options: IsolatedOptions)` | System | ArkUI | `isolated_component.d.ts` | @systemapi |
| `IsolatedComponentAttribute.onError(callback: ErrorCallback)` | System | ArkUI | `isolated_component.d.ts` | @systemapi |

## 构建系统影响

无 — 已有实现。

## 详细设计

### IsolateComponent 创建流程

1. JS 桥接解析 `IsolatedOptions { want, worker }`
2. `UIExtensionModelNG::CreateIsolatedComponent` 创建 FrameNode
3. `InitializeIsolatedComponent` 解析 Want → `IsolatedInfo { abcPath, resourcePath, entryPoint, registerComponents }`
4. `DynamicComponentRendererImpl::CreateIsolatedContent` 在 RestrictedWorker 的 NativeEngine 中创建 UIContent
5. 约束检查：`WORKER_MAX_NUM=1` / `DC_MAX_NUM_IN_WORKER=4`

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| @dynamiconly 限制 | API | 中 | 无 Static/Native 桥接，仅动态范式可用 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认
- [x] 调用链层级分析完整
- [x] 适用架构规则已识别
- [x] 关键设计决策有理由和影响说明
- [x] 风险和开放问题有 Owner

**结论:** 通过（已有实现补录）