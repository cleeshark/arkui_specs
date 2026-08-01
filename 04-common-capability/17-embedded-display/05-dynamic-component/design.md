# 架构设计

> 嵌入显示能力-DynamicComponent 功能域的架构设计文档。DynamicComponent 是跨线程动态组件加载机制，在 Worker 线程中加载和渲染组件，与跨进程的 UIExtension 机制不同。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-04-17-05 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | Feat-01 跨线程动态组件加载 |
| 复杂度 | 标准 |
| 目标版本 | Dynamic API 10+ |
| Owner | ArkUI SIG |
| 状态 | Baselined（已有实现补录） |

## 需求基线

| 项 | 内容 |
|----|------|
| 问题陈述 | 需要在 Worker 线程中动态加载和渲染组件，将组件构建和布局从主线程卸载 |
| 核心目标 | 提供 DynamicComponent 跨线程加载机制，包含 Worker 线程 UIContent 创建、Surface 回传和数量约束 |
| P0 AC | Worker 线程中正确加载组件；Surface 渲染结果回传主线程；Worker 数量约束生效 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 模块 | 当前职责 | 本 Feature 影响 |
|------|------|----------|-----------------|
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/dynamic_component/dynamic_pattern.h/cpp` | DynamicPattern 核心逻辑 | 核心实现 |
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/dynamic_component/dynamic_model.h/cpp` | DynamicModelNG | API 实现 |
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/dynamic_component/dynamic_component_manager.h/cpp` | DynamicComponentSafeManager 数量约束 | 约束管理 |
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/ui_extension_model.h` | 抽象模型接口 | 共享接口 |
| ace_engine | `adapter/ohos/entrance/dynamic_component/dynamic_component_renderer_impl.h/cpp` | OHOS 渲染器实现 | 平台适配 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| JS Bridge | ArkTS Dynamic bindings | 解析 DynamicParam | 存量分析 |
| Model 层 | `dynamic_model_ng` | 创建 DynamicPattern | 存量分析 |
| Pattern 层 | `dynamic_pattern` | 生命周期管理、Worker 线程启动 | 存量分析 |
| Renderer 层 | `dynamic_component_renderer_impl` | Worker 线程 UIContent 创建、Surface 回传 | 存量分析 |
| Manager 层 | `dynamic_component_manager` | 数量约束检查 | 存量分析 |

### 与 UIExtension 的机制差异

| 维度 | DynamicComponent | UIExtensionComponent |
|------|-----------------|---------------------|
| 运行环境 | Worker 线程（同进程） | 远程 Ability（跨进程） |
| 通信方式 | Surface 回传 | IPC 通道 + Proxy |
| 数量约束 | 每 Worker 最多 4 个 | 无硬限制 |
| 生命周期事件 | 有限（onError） | 完整（7 个事件） |

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | 涉及 JS Bridge → Model → Pattern → Renderer | 严格单向调用 | 代码评审 |
| OH-ARCH-API-LEVEL | Dynamic API 10+ | 按 @since 版本标注 | API 评审 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| 性能 | 约束：每 Worker 最多 4 个 DynamicComponent |
| 兼容性 | Dynamic + Static 双范式 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 影响 |
|---------|------|----------|------|
| ADR-1 | DynamicComponent 是否属于 UIExtension 体系 | 独立机制：虽共享 ui_extension 目录结构，但机制本质不同（同进程跨线程 vs 跨进程） | 独立 FuncID |
| ADR-2 | Worker 线程数量约束 | 每 Worker 最多 4 个 DynamicComponent（DC_MAX_NUM_IN_WORKER=4） | 防止资源耗尽 |

## 后续 Task 拆分

| Task ID | 目标 | 受影响文件 | 依赖 |
|---------|------|-----------|------|
| Feat-01 | 跨线程动态组件加载 | Feat-01-dynamic-component-spec.md | 无 |

## API 签名、Kit 与权限

| API 签名 | 类型 | Kit |
|----------|------|-----|
| `DynamicComponent(options: DynamicOptions)` | System | ArkUI |

## 构建系统影响

无 — 已有实现。

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| Worker 线程崩溃影响 | 架构 | 中 | DynamicComponentSafeManager 监控 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认
- [x] 调用链层级分析完整
- [x] 关键设计决策有理由和影响说明

**结论:** 通过（已有实现补录）