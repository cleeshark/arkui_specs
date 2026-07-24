# 特性规格

> Func-05-14-03-Feat-02 OffscreenCanvas 离屏二维绘制上下文存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | OffscreenCanvas 离屏二维绘制上下文 |
| 特性编号 | Func-05-14-03-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

`OffscreenCanvasRenderingContext2D` 继承 `CanvasRenderer` 的二维绘制契约，但绑定 OffscreenCanvasPattern 并直接面向离屏表面。本特性区分“不同 OffscreenCanvas 表面相互隔离”与“同一 OffscreenCanvas 重复 getContext 所得 wrapper 共享 Pattern/绘制状态”，并规定与可见 Canvas 的边界。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 共享绘制契约 | 引用 Canvas Feat-02~Feat-06，不重复定义 API |
| ADDED | 离屏上下文归属 | 不同表面隔离；同一表面的多个 wrapper 共享 Pattern/状态 |
| ADDED | 适用性差异 | 无可见性队列、onReady、FrameNode 和分析能力 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/03-offscreen-canvas/design.md` | 并行补录 |
| Shared specs | `05-ui-components/14-drawing-components/02-canvas/Feat-02-canvas-path-geometry-clipping-spec.md` 等 | 已核对 |
| SDK | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:1373-2942,3267-3377` | 已核对 |
| JS Binding | `frameworks/bridge/declarative_frontend/jsview/canvas/js_offscreen_rendering_context.cpp` | 已核对 |
| Paint | `frameworks/core/components_ng/pattern/canvas/offscreen_canvas_paint_method.cpp` | 已核对 |

## 用户故事

### US-1: 在离屏上下文复用二维绘制契约

**作为** 图形应用开发者  
**我想要** 在 OffscreenCanvas 使用熟悉的 CanvasRenderer API  
**以便** 复用路径、样式、文本和图像绘制逻辑

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 离屏 context 调用 CanvasPath、fill/stroke/clip、样式与合成 API THEN 遵守 Func-05-14-02-Feat-02/03 的共同规则并输出到离屏表面 | 正常 |
| AC-1.2 | WHEN 调用 save/restore/transform、文本或图像像素 API THEN 分别遵守 Canvas Feat-04/05/06 的规则，状态属于其 OffscreenCanvasPattern；同一表面的其他 wrapper 可观察该共享状态 | 正常 |
| AC-1.3 | WHEN 使用 API 10 锥形渐变、API 12 unit/saveLayer/reset、API 18 letterSpacing、API 20 roundRect 等接口 THEN 按各自 since 版本门控；roundRect 的负半径、空 radii 数组或超过 4 项仍同步抛 103701 | 边界 |
| AC-1.4 | WHEN 共享 API 收到非有限参数、失效图像、空状态栈或非法 roundRect radii THEN 采用被引用 Canvas Feat 的逐项异常/恢复规则，不因离屏路径放宽校验 | 异常 |

### US-2: 隔离离屏与可见 Canvas 状态

**作为** 框架维护者  
**我想要** 不同离屏表面使用独立 Pattern 和路径状态
**以便** 避免跨表面命令串扰

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 在 OffscreenCanvasRenderingContext2D 调用 beginPath 等当前路径 API THEN 仅修改该离屏 context 路径，不影响 CanvasRenderingContext2D 或 Path2D 对象 | 正常 |
| AC-2.2 | WHEN 离屏 context 提交绘制命令 THEN OffscreenCanvasPaintMethod 在离屏表面执行，不等待可见 Canvas 的帧可见性或 CanvasPattern Flush | 正常 |
| AC-2.3 | WHEN 创建多个不同 OffscreenCanvas 对象 THEN 各自 Pattern、尺寸、状态栈、资源和像素结果相互隔离 | 正常 |
| AC-2.4 | WHEN 应用尝试使用 Canvas 专属 onReady、attach/detach、FrameNode 或 analyzer 能力 THEN Offscreen context 不提供这些接口 | 边界 |
| AC-2.5 | WHEN 对同一 OffscreenCanvas 重复调用 getContext('2d') THEN 每次可创建不同 JS wrapper，但均绑定同一 offscreenCanvasPattern/OffscreenCanvasPaintMethod 和绘制状态/表面；owner 指针更新为最新 wrapper，后续 resize 绑定可能受其影响 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Canvas/Offscreen 对照 UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:1373-2942,3267-3377` |
| AC-2.1~AC-2.5 | R-5~R-9 | 已有实现 | 源码审查+待补多对象/同对象多 wrapper UT | `frameworks/bridge/declarative_frontend/jsview/canvas/js_offscreen_rendering_context.cpp:97-164`; `frameworks/bridge/declarative_frontend/jsview/canvas/js_offscreen_canvas.cpp:403-475`; `frameworks/core/components_ng/pattern/canvas/offscreen_canvas_pattern.h:125-130` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 路径/样式 API | 遵守 Canvas Feat-02/03 | 输出目标改为离屏表面 | AC-1.1 |
| R-2 | 行为 | 状态/文本/图像 API | 遵守 Canvas Feat-04/05/06 | 状态归所属离屏 Pattern | AC-1.2 |
| R-3 | 边界 | 后续版本 API | 按 since 门控；roundRect 参数错误抛 103701 | 不提前暴露 | AC-1.3 |
| R-4 | 异常 | 非法共享 API 输入 | 复用 Canvas 异常规则 | 不放宽校验 | AC-1.4 |
| R-5 | 行为 | 当前路径命令 | 只改所属离屏 Pattern 当前路径 | Path2D/visible context 仍独立 | AC-2.1 |
| R-6 | 行为 | 提交离屏命令 | 由 OffscreenPaintMethod 执行 | 无可见性队列 | AC-2.2 |
| R-7 | 行为 | 多个 OffscreenCanvas 表面 | Pattern/状态/资源/像素独立 | 不跨对象串扰 | AC-2.3 |
| R-8 | 边界 | Canvas 组件专属能力 | 不暴露 | 无 FrameNode | AC-2.4 |
| R-9 | 边界 | 同一 OffscreenCanvas 多次 getContext | 不同 wrapper 共享同一 Pattern/PaintMethod/状态/表面，owner 更新为最新 wrapper | 不具备 context 级隔离 | AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.2 | Canvas/Offscreen 金图对照 | 共同绘制语义 |
| VM-2 | AC-1.3~AC-1.4 | API 版本/非法值矩阵 | since 门控和共同异常规则 |
| VM-3 | AC-2.1~AC-2.3, AC-2.5 | 源码审查+待补归属矩阵 UT | visible/不同 OffscreenCanvas 隔离；同一对象多 wrapper 状态共享与 owner/resize 影响 |
| VM-4 | AC-2.4 | SDK 表面审查 | 无组件专属 API |

## API 变更分析

### 新增 API

N/A；本特性确认 `OffscreenCanvasRenderingContext2D extends CanvasRenderer` 的存量契约。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

| 接口组 | 规范源 | 离屏差异 | 关联 AC |
|--------|--------|----------|---------|
| Path/Style | Canvas Feat-02/03 | 独立当前路径和离屏目标 | AC-1.1, AC-2.1 |
| State/Text/Image | Canvas Feat-04/05/06 | 状态属于离屏 context | AC-1.2 |
| 构造 | `new OffscreenCanvasRenderingContext2D(width,height,settings?,unit?)` | 不同对象独立表面；unit API 12 | AC-1.3, AC-2.3 |
| 同对象重复获取 | `offscreenCanvas.getContext('2d')` | wrapper 不同但共享 Pattern/PaintMethod/状态 | AC-2.5 |
| 离屏专属 | `toDataURL`; `transferToImageBitmap` | 见 Feat-03 | AC-2.2 |

## 兼容性声明

- **最低支持版本:** API 8。
- **版本节点:** `getContext`/锥形渐变 API 10；unit/saveLayer/reset API 12；letterSpacing API 18；roundRect API 20。
- **形态边界:** 不具备 Canvas 组件 API 12 analyzer、API 13 lifecycle/FrameNode、API 23 CanvasParams/Static 构造语义。
- **共享规范:** CanvasRenderer 新增接口若 SDK 明示继承适用，则沿用 Canvas 对应 Feat 的版本与规则。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 独立 Pattern | 共享 API 表面不等于共享 CanvasPattern | AC-2.2 |
| 路径隔离 | Offscreen 当前路径不影响 visible context/Path2D | AC-2.1 |
| 单一规则源 | 公共绘制语义以 Canvas Feat-02~06 为准 | AC-1.1~AC-1.4 |
| 归属粒度 | 隔离单位是 OffscreenCanvas/Pattern，不是每次 getContext 创建的 JS wrapper | AC-2.3, AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 离屏绘制不依赖可见帧 Flush，成本仍随命令和表面规模增长 | Benchmark | AC-2.2 |
| 内存 | 不同表面资源独立；同表面多个 wrapper 共享 Pattern 且 owner 指向最新 wrapper | 泄漏/生命周期测试 | AC-2.3, AC-2.5 |
| 安全 | 共享异常规则完整适用 | Fuzz | AC-1.4 |
| 可靠性 | 共同 API 在两类 context 像素等价 | 对照金图 | VM-1 |
| 可测试性 | Pattern 可独立构造和验证 | UT | VM-3 |
| 定界定位 | JS context→OffscreenPattern→PaintMethod 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 内存受限 | 控制表面/状态规模 | 压力测试 | VM-3 |
| 平板 | 大离屏绘制 | 共同 API 像素语义一致 | 金图 | VM-1 |
| 折叠屏 | 无自动布局 | 由应用显式调整尺寸 | 集成测试 | Feat-01 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 无节点语义 | AC-2.4 |
| 大字体 | 是 | Canvas Feat-05 规则适用，但无自动系统布局 | AC-1.2 |
| 深色模式 | 是 | 应用显式更新样式并重绘 | AC-1.1 |
| 多窗口/分屏 | 否 | 不绑定可见窗口 | AC-2.2 |
| 版本升级 | 是 | 共享 API since 与离屏适用性需同时回归 | VM-2 |
| 生态兼容 | 是 | 当前路径隔离保持 | AC-2.1 |

## Spec 自审清单

- [x] 共享契约引用而非重复定义
- [x] 不同表面隔离与同一表面多 wrapper 共享边界明确
- [x] Canvas 专属生命周期/分析能力排除
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "OffscreenCanvasRenderingContext2D OffscreenCanvasPaintMethod path isolation"
  - repo: "openharmony/interface_sdk-js"
    query: "OffscreenCanvasRenderingContext2D extends CanvasRenderer"
```

**关键文档：** `05-ui-components/14-drawing-components/03-offscreen-canvas/design.md`
