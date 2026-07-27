# 特性规格

> Func-05-14-03-Feat-01 OffscreenCanvas 离屏表面与上下文存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | OffscreenCanvas 离屏表面与上下文 |
| 特性编号 | Func-05-14-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

OffscreenCanvas 创建不进入 ArkUI 可见节点树的离屏像素表面，通过宽高、单位和 `getContext('2d')` 提供二维上下文。本特性规定离屏对象、表面归属与结构化转移后的 Detached 生命周期；共享 CanvasRenderer 绘制接口由 Canvas 各 Feat 作为规范源。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 离屏表面 | 构造、宽高、单位和尺寸更新 |
| ADDED | 上下文获取 | 2d 类型、settings、缓存/归属 |
| ADDED | 组件边界 | 无 FrameNode、onReady、生命周期和 analyzer |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/03-offscreen-canvas/design.md` | 并行补录 |
| SDK | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:3378-3496` | 已核对 |
| JS Binding | `frameworks/bridge/declarative_frontend/jsview/canvas/js_offscreen_canvas.cpp` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/canvas/offscreen_canvas_pattern.h` | 已核对 |
| Implementation | `frameworks/core/components_ng/pattern/canvas/offscreen_canvas_pattern.cpp` | 已核对 |

## 用户故事

### US-1: 创建独立离屏表面

**作为** 图形应用开发者  
**我想要** 在不创建可见组件的情况下分配画布  
**以便** 预渲染或在线程任务中准备图像

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 以有限 width/height 创建 OffscreenCanvas THEN 分配对应尺寸的独立离屏表面并暴露 width/height | 正常 |
| AC-1.2 | WHEN API 12 构造时指定 LengthMetricsUnit THEN 尺寸和上下文坐标使用固定单位模式，创建后不可动态切换 | 正常 |
| AC-1.3 | WHEN width/height 设置为新合法值 THEN 更新离屏表面尺寸并重建/清空与尺寸关联的像素内容 | 正常 |
| AC-1.4 | WHEN尺寸为 NaN/Infinity、负值或导致不可分配表面 THEN 构造/更新按 SDK 与实现规则拒绝或归一，不产生越界缓冲 | 异常 |

### US-2: 获取二维上下文并保持离屏边界

**作为** 应用开发者  
**我想要** 从离屏表面取得专属 2D context  
**以便** 使用 Canvas 绘图能力生成像素

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN API 10 调用 getContext('2d', settings?) THEN 返回绑定当前表面的 OffscreenCanvasRenderingContext2D | 正常 |
| AC-2.2 | WHEN contextType 不是字符串 `2d`，包括 null/undefined THEN 返回 undefined 且不创建上下文 | 边界 |
| AC-2.3 | WHEN settings 缺失或 null THEN 使用 RenderingContextSettings 默认值；合法 antialias 设置应用于非文本绘制 | 正常 |
| AC-2.4 | WHEN 使用 OffscreenCanvas THEN 不创建 FrameNode，不触发 Canvas onReady/onAttach/onDetach，也不提供 enable/start/stop analyzer | 边界 |
| AC-2.5 | WHEN 结构化转移请求作用于尚未 getContext 且未 Detached 的 OffscreenCanvas THEN 创建接收端对象并将源对象置 Detached；WHEN 源已有 rendering context 或已 Detached THEN 该转移以参数错误拒绝 | 边界 |
| AC-2.6 | WHEN 访问 Detached 源对象 THEN width/height getter 返回 0、setter 无操作，getContext/transferToImageBitmap 同步抛 BusinessError 103704；普通 transferToImageBitmap 快照本身不使源对象 Detached | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Offscreen 构造/尺寸源码审查与 UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:3378-3496`; `frameworks/bridge/declarative_frontend/jsview/canvas/js_offscreen_canvas.cpp:154-233,306-394` |
| AC-2.1~AC-2.6 | R-5~R-10 | 已有实现 | JS binding/context/detach 源码审查；UT 待补 | `frameworks/bridge/declarative_frontend/jsview/canvas/js_offscreen_canvas.cpp:85-151,236-303,403-475`; `frameworks/core/components_ng/pattern/canvas/offscreen_canvas_pattern.h:60-130` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 有限合法尺寸 | 分配离屏表面 | 不创建 UI 节点 | AC-1.1 |
| R-2 | 行为 | 指定 unit | 固定坐标单位模式 | API 12，创建后不变 | AC-1.2 |
| R-3 | 行为 | 合法尺寸更新 | 重建/清空尺寸相关表面 | context 关联同步 | AC-1.3 |
| R-4 | 异常 | 非有限/不可分配尺寸 | 拒绝或归一 | 防止缓冲溢出 | AC-1.4 |
| R-5 | 行为 | getContext('2d') | 返回离屏二维 context | API 10 | AC-2.1 |
| R-6 | 边界 | 非 `2d` 类型 | 返回 undefined | 不隐式降级 | AC-2.2 |
| R-7 | 边界 | settings 为空 | 使用默认配置 | 文本 AA 独立 | AC-2.3 |
| R-8 | 边界 | 离屏对象 | 不提供组件生命周期/分析 | 与可见 Canvas 分离 | AC-2.4 |
| R-9 | 边界 | 结构化转移 | 无 context 且未 Detached 时转移并 detach 源；否则参数错误 | 与图像快照 transferToImageBitmap 不同 | AC-2.5 |
| R-10 | 异常 | Detached 源对象 | width/height=0、setter no-op；getContext/transferToImageBitmap 抛 103704 | 不访问旧 Pattern/surface | AC-2.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | 尺寸与分配边界 UT | 单位、清屏、非有限和大尺寸 |
| VM-2 | AC-2.1~AC-2.3 | getContext 参数矩阵 | 类型、settings、上下文归属 |
| VM-3 | AC-2.4 | API/节点树审查 | 无 FrameNode/事件/analyzer |
| VM-4 | AC-2.5~AC-2.6 | 源码审查+待补 structured-clone/detach UT | 有 context 转移失败、源 Detached、0 尺寸/no-op setter 与 103704；当前未找到活跃覆盖 |

## API 变更分析

### 新增 API

N/A；OffscreenCanvas 自 API 8，`getContext` 自 API 10，单位构造自 API 12，均为已有能力。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

| 接口 | 签名摘要 | 约束 | 关联 AC |
|------|----------|------|---------|
| 构造 | `new OffscreenCanvas(width, height[, unit])` | 尺寸有限；unit 创建后固定 | AC-1.1~AC-1.4 |
| 尺寸 | `width`, `height` | 更新时重建/清空表面 | AC-1.3 |
| 上下文 | `getContext('2d', options?)` | 非 2d 返回 undefined | AC-2.1~AC-2.3 |
| Detached 对象 | `width/height/getContext/transferToImageBitmap` | getter=0、setter no-op；后两者抛 103704 | AC-2.5~AC-2.6 |

## 兼容性声明

- **最低支持版本:** API 8。
- **版本节点:** `getContext` API 10；LengthMetricsUnit API 12。
- **形态边界:** OffscreenCanvas 不是 ArkUI 组件，不参与 FrameNode、onReady、attach/detach 或 analyzer。
- **对象转移边界:** 结构化转移可将无 context 的源对象置 Detached；ImageBitmap 快照 API 不等价于该对象转移。
- **ServiceExtensionAbility:** SDK 明示不支持 OffscreenCanvas，建议使用 graphics drawing 模块。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 独立 Pattern | OffscreenCanvas 由独立 OffscreenCanvasPattern/离屏表面承载 | AC-1.1 |
| 无节点树 | 不拥有 CanvasPattern 的可见组件生命周期 | AC-2.4 |
| 共享规则源 | CanvasRenderer 的路径、样式、状态、文本和像素规则引用 Func-05-14-02 | AC-2.1 |
| Detached 状态 | 只有结构化对象转移使源 Detached；后续访问遵守 0/no-op/103704 矩阵 | AC-2.5, AC-2.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 离屏任务可减少主线程可见组件负载，但绘制成本仍随像素/命令增长 | Benchmark | VM-1 |
| 内存 | 表面约随宽*高增长，尺寸变更释放旧资源 | 泄漏/压力测试 | AC-1.3 |
| 安全 | 尺寸乘法和缓冲分配防溢出 | Fuzz | AC-1.4 |
| 可靠性 | getContext 非法类型不产生半初始化对象；Detached 对象不复用旧 surface | UT | VM-2, VM-4 |
| 可测试性 | 表面尺寸和导出像素可验证 | UT | VM-1 |
| 定界定位 | JS binding→OffscreenPattern→PaintMethod 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 内存较紧 | 控制离屏表面尺寸 | 压力测试 | AC-1.4 |
| 平板 | 可用更大表面 | 语义不变、成本增大 | 性能矩阵 | VM-1 |
| 折叠屏 | 无自动组件重布局 | 应用显式更新离屏尺寸 | 集成测试 | AC-1.3 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 无 UI 节点 | AC-2.4 |
| 大字体 | 否 | 共享文本规则见 Canvas Feat-05 | AC-2.1 |
| 深色模式 | 否 | 应用显式重绘 | AC-1.1 |
| 多窗口/分屏 | 否 | 不自动绑定窗口尺寸 | AC-1.3 |
| 版本升级 | 是 | API 8/10/12 门控需回归 | VM-1, VM-2 |
| 生态兼容 | 是 | 非 2d 返回 undefined 保持 | AC-2.2 |

## Spec 自审清单

- [x] 离屏表面、单位、尺寸更新、结构化转移与 Detached/103704 覆盖
- [x] 与可见 Canvas 的节点/生命周期边界明确
- [x] 共享 CanvasRenderer 规格只引用不重复定义
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "OffscreenCanvasPattern getContext size unit"
  - repo: "openharmony/interface_sdk-js"
    query: "OffscreenCanvas API 8 10 12"
```

**关键文档：** `05-ui-components/14-drawing-components/03-offscreen-canvas/design.md`
