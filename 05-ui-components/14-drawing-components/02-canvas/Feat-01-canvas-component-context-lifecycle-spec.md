# 特性规格

> Func-05-14-02-Feat-01 Canvas 组件、上下文与生命周期存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Canvas 组件、上下文与生命周期 |
| 特性编号 | Func-05-14-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

Canvas 将可见组件与 `CanvasRenderingContext2D` 或 `DrawingRenderingContext` 绑定，在尺寸确定后提供绘制表面。本特性覆盖构造、上下文独占绑定、尺寸限制、初始化/尺寸变化、可见性、生命周期事件以及立即和延迟两种命令执行路径。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 组件与上下文绑定 | 补录构造、独占关系与 CanvasParams 路径 |
| ADDED | 生命周期 | 补录 onReady、attach/detach、尺寸变化与清屏 |
| ADDED | 渲染模式 | 补录 immediate/deferred 分派和不可见状态 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/02-canvas/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/canvas.static.d.ets` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp` | 已核对 |
| RenderContext | `frameworks/core/components_ng/pattern/canvas/canvas_render_context_immediate.cpp` | 已核对 |

## 用户故事

### US-1: 建立可见绘制表面

**作为** 应用开发者  
**我想要** 将专属绘制上下文绑定到 Canvas  
**以便** 在组件尺寸确定后可靠绘制

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 以未被其他 Canvas 占用的 CanvasRenderingContext2D 或 DrawingRenderingContext 创建 Canvas THEN 组件建立一对一上下文绑定并创建 CanvasPattern | 正常 |
| AC-1.2 | WHEN context 为 null/undefined THEN Canvas 仍可创建，但不建立外部上下文绑定 | 边界 |
| AC-1.3 | WHEN 同一上下文被多个 Canvas 复用 THEN 后续绑定不应形成两个可独立绘制的有效表面 | 异常 |
| AC-1.4 | WHEN Canvas 实际宽或高超过 10000 px THEN 按 SDK 约束创建失败或不建立绘制表面 | 边界 |

### US-2: 按生命周期和可见性提交命令

**作为** 图形应用开发者  
**我想要** 在表面准备好后绘制并在生命周期变化时得到通知  
**以便** 避免对无效表面执行命令

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN API<10 且 frame/content 的尺寸或 offset 变化 THEN reset 表面、更新上下文尺寸并触发 onReady；WHEN API>=10 THEN 仅 frame/content 尺寸变化且 pixel-grid-round size 确实变化时执行 reset/onReady，纯位置变化不触发 | 边界 |
| AC-2.2 | WHEN 使用 deferred 上下文 THEN 绘制命令无条件入队，可见渲染阶段才 Flush；隐藏期间当前实现没有队列上限或清理策略，每累计 100000 条仅记录日志/统计事件 | 边界 |
| AC-2.3 | WHEN Canvas 使用 immediate 上下文 THEN 命令直接作用于当前表面；组件隐藏时清理录制状态且不积压不可执行命令 | 边界 |
| AC-2.4 | WHEN Dynamic API 13 注册 onAttach/onDetach 或 Static 注册 onAttach/offAttach/onDetach/offDetach THEN 组件挂载状态变化按各自接口形态通知且注销后不再回调 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Canvas Pattern/Model 源码审查与 UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:3605-3735`; `frameworks/core/components_ng/pattern/canvas/bridge/arkts_native_canvas_bridge.cpp:214-235`; `frameworks/bridge/declarative_frontend/jsview/canvas/js_rendering_context.cpp:402-408` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | 源码审查+API 9/10/隐藏压力测试 | `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp:139-200,1094-1109`; `frameworks/core/components_ng/pattern/canvas/canvas_render_context_immediate.cpp:21-40`; `frameworks/core/components_ng/pattern/canvas/canvas_render_context_deferred.cpp:30-60` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 合法且空闲 context | 建立组件、Pattern、context 一对一绑定 | context 不可共享 | AC-1.1 |
| R-2 | 边界 | context 为空 | 创建无外部 context 的 Canvas | 不解引用空对象 | AC-1.2 |
| R-3 | 异常 | context 重复绑定 | 拒绝形成第二个有效绑定 | 保持首个表面一致性 | AC-1.3 |
| R-4 | 边界 | 任一维度>10000 px | 不创建有效绘制表面 | SDK 硬上限 | AC-1.4 |
| R-5 | 边界 | 初始化/几何变化 | API<10 的尺寸或 offset 变化均 reset/onReady；API>=10 仅尺寸且 pixel-grid-round size 变化时执行 | 纯 offset 在 API 10 是版本分界 | AC-2.1 |
| R-6 | 边界 | deferred 命令 | 无条件入队，可见帧 Flush | 隐藏队列无上限/清理；100000 的倍数仅告警 | AC-2.2 |
| R-7 | 行为 | immediate 模式 | 直接执行当前命令 | 隐藏时清录制状态 | AC-2.3 |
| R-8 | 行为 | attach/detach | 按范式注册/注销回调 | Dynamic 与 Static 签名不同 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | Canvas 创建与绑定 UT | 空值、复用、尺寸上限 |
| VM-2 | AC-2.1 | API 9/10 onReady/Geometry 参数化测试 | 尺寸、pixel-grid-round size 与纯 offset 变化 |
| VM-3 | AC-2.2~AC-2.3 | immediate/deferred 隐藏压力测试 | 无条件入队、可见 Flush、100000 告警与 immediate 隐藏行为 |
| VM-4 | AC-2.4 | 源码审查+待补 Dynamic/Static 生命周期 UT | 注册、通知与注销；现有多项 accessor 用例为 DISABLED |

## API 变更分析

### 新增 API

N/A，本次补录 Canvas API 8 至 API 26 的现有能力。

### 变更/废弃 API

N/A；Dynamic `on/off` 与 Static 独立注册/注销函数是并存接口，不相互替代。

## 接口规格

### 接口定义

| 接口 | 签名摘要 | 开放范围 | 关联 AC |
|------|----------|----------|---------|
| Canvas | `Canvas(context?)`; `Canvas(context, imageAIOptions)`; `Canvas(params)` | Public | AC-1.1~AC-1.4 |
| onReady | `onReady(callback)` | Public | AC-2.1 |
| 生命周期 | Dynamic `on/off`; Static `onAttach/offAttach/onDetach/offDetach` | Public | AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| context | CanvasRenderingContext2D / DrawingRenderingContext | 否 | 未绑定 | 不得由多个 Canvas 共享 |
| params.unit | LengthMetricsUnit | 否 | DEFAULT | API 23，创建后不可修改 |
| callback | 回调 | 视接口 | 无 | 注销后不得继续触发 |

## 兼容性声明

- **已有 API 行为变更:** 是；API 23 引入 CanvasParams 立即绘制路径，须与历史 deferred 路径分别保持。
- **最低支持版本:** API 8。
- **版本节点:** API 12 DrawingRenderingContext/分析参数，API 13 FrameNode 生命周期，API 23 CanvasParams/Static，API 26 Builder。
- **数据与配置格式变更:** 否。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 节点归属 | 可见 Canvas 由 CanvasPattern 持有表面和生命周期 | AC-1.1, AC-2.1 |
| 双执行模式 | immediate 直接执行，deferred 记录后 Flush，不得混为同一队列语义 | AC-2.2, AC-2.3 |
| 一对一绑定 | context 不得跨 Canvas 共享 | AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 超过 8000 px 的 CPU 绘制需视为高成本，最大尺寸 10000 px | 尺寸性能矩阵 | SDK CanvasRenderer/Canvas 注释 |
| 内存 | 不可见 deferred 高频调用当前可无界积压；100000 条只告警而不丢弃/清理 | 隐藏压力测试/风险跟踪 | AC-2.2 |
| 可靠性 | 尺寸变化后旧像素清除且 context 尺寸一致 | UT | VM-2 |
| 安全 | 空 context 与重复绑定不产生悬挂访问 | Fuzz/UT | VM-1 |
| 可测试性 | 两类 RenderContext 可独立注入验证 | UT | VM-3 |
| 定界定位 | SDK→Bridge/Model→Pattern→RenderContext 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 常规像素规模 | 遵守尺寸和可见性规则 | UI 测试 | VM-1~VM-3 |
| 平板 | 大画布更易进入 CPU 高成本区 | 覆盖 8000/10000 px 边界 | 性能测试 | AC-1.4 |
| 折叠屏 | 尺寸/offset 变化频繁 | 按 API 9/10 几何触发矩阵决定 reset/onReady | 折叠态测试 | AC-2.1 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Canvas 不自动推导内部像素语义 | AC-1.1 |
| 大字体 | 否 | 由文本绘制 Feat 单独覆盖 | VM-1 |
| 深色模式 | 是 | 重绘时由应用更新颜色 | AC-2.1 |
| 多窗口/分屏 | 是 | 尺寸变化触发清屏和 onReady | AC-2.1 |
| 版本升级 | 是 | immediate/deferred 与范式差异需回归 | VM-3, VM-4 |
| 生态兼容 | 是 | 历史 context 构造路径保持 | AC-1.1 |

## Spec 自审清单

- [x] Canvas/context 一对一关系和尺寸上限明确
- [x] immediate/deferred 执行差异及隐藏 deferred 无界积压风险明确
- [x] Dynamic/Static 生命周期差异明确
- [x] AC、规则、VM 双向追溯
- [x] 未提出新产品能力

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "CanvasPattern immediate deferred onReady lifecycle"
  - repo: "openharmony/interface_sdk-js"
    query: "Canvas CanvasParams onReady API 8 13 23"
```

**关键文档：** `05-ui-components/14-drawing-components/02-canvas/design.md`
