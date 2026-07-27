# 特性规格

> Func-05-14-03-Feat-03 OffscreenCanvas 图像导出与转移存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | OffscreenCanvas 图像导出与转移 |
| 特性编号 | Func-05-14-03-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

本特性覆盖离屏表面通过 `toDataURL` 编码为字符串，以及通过 `transferToImageBitmap` 生成可供 Canvas/Pattern 使用的 ImageBitmap。两个接口均涉及表面快照、内存拷贝或资源转移，应保持格式默认、质量归一、空表面和失效资源的既有行为。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 数据 URL 导出 | png/jpeg/webp、质量和默认值 |
| ADDED | ImageBitmap 转移 | 最近渲染图像、对象生命周期和重复调用 |
| ADDED | 成本与失败边界 | 大表面拷贝、空/失效表面和资源回收 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/03-offscreen-canvas/design.md` | 并行补录 |
| SDK | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:3267-3496` | 已核对 |
| JS Binding | `frameworks/bridge/declarative_frontend/jsview/canvas/js_offscreen_canvas.cpp` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/canvas/offscreen_canvas_pattern.cpp` | 已核对 |
| Paint | `frameworks/core/components_ng/pattern/canvas/offscreen_canvas_paint_method.cpp` | 已核对 |

## 用户故事

### US-1: 编码离屏图像

**作为** 图形应用开发者  
**我想要** 将离屏结果导出为数据 URL  
**以便** 存储或传递编码图像

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN toDataURL 未传 type/quality THEN 以 image/png 和默认质量规则导出当前离屏表面 | 正常 |
| AC-1.2 | WHEN type 为 image/png、image/jpeg 或 image/webp 且 quality 在 [0,1] THEN 使用对应编码格式和质量返回 data URL | 正常 |
| AC-1.3 | WHEN type 无效，或 quality 为越界、undefined、null、NaN、Infinity THEN SDK 契约按默认类型/0.92 质量归一；当前 Dynamic 路径仅重置越界和 Infinity，NaN 会穿透并乘 100 传入 encoder，Static 路径会过滤特殊值 | 边界 |
| AC-1.4 | WHEN 表面为空、零尺寸、失效或编码失败 THEN 返回既有失败/空结果且不访问已释放像素 | 异常 |

### US-2: 转移最近绘制图像

**作为** 应用开发者  
**我想要** 将离屏像素生成 ImageBitmap  
**以便** 在 Canvas 中复用渲染结果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 非 Detached 的 OffscreenCanvas 或其 context 调用 transferToImageBitmap THEN 以最近完成绘制的表面创建具有匹配尺寸和像素的 ImageBitmap；该快照调用本身不使源 OffscreenCanvas Detached | 正常 |
| AC-2.2 | WHEN 生成的 ImageBitmap 作为 Canvas drawImage/Pattern 源 THEN 按 Canvas Feat-06/03 规则消费且不依赖原离屏对象仍挂载 UI 节点 | 正常 |
| AC-2.3 | WHEN 快照转移后继续对离屏 context 绘制或再次转移 THEN 按当前实现维持可用离屏表面/最新快照语义，不返回悬挂资源 | 边界 |
| AC-2.4 | WHEN 源表面不可用或资源分配失败 THEN 转移安全失败且不破坏既有有效 ImageBitmap 对象 | 异常 |
| AC-2.5 | WHEN OffscreenCanvas 已因结构化对象转移而 Detached THEN 其 transferToImageBitmap 与 getContext 同步抛 BusinessError 103704；width/height getter=0 且 setter no-op | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | SDK/源码审查；编码特殊值 UT 待补 | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:3290-3349`; `frameworks/bridge/declarative_frontend/jsview/canvas/js_canvas_renderer.cpp:1042-1048`; `frameworks/core/components_ng/pattern/canvas/custom_paint_util.cpp:31-41`; `frameworks/core/interfaces/native/implementation/canvas_renderer_peer_impl.cpp:1129-1141` |
| AC-2.1~AC-2.5 | R-5~R-9 | 已有实现 | 源码审查；bitmap/detach 生命周期 UT 待补 | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:3419-3485`; `frameworks/bridge/declarative_frontend/jsview/canvas/js_offscreen_canvas.cpp:85-108,236-303` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 缺省参数 | png+默认质量 | API 8 | AC-1.1 |
| R-2 | 行为 | 支持格式+合法质量 | 返回对应 data URL | quality 对 png 可无影响 | AC-1.2 |
| R-3 | 边界 | 非法格式/质量 | SDK 使用默认值；当前 Dynamic NaN quality 穿透 encoder | quality 默认 0.92 | AC-1.3 |
| R-4 | 异常 | 空/失效表面 | 安全失败/空结果 | 不读释放内存 | AC-1.4 |
| R-5 | 行为 | 有效最近表面 | 创建匹配 ImageBitmap 且不 detach 源 | 快照为最近结果 | AC-2.1 |
| R-6 | 行为 | bitmap 作为图像/Pattern | 沿用 Canvas 规则 | 不要求 UI 节点 | AC-2.2 |
| R-7 | 恢复 | 后续绘制/重复转移 | 产生最新有效结果 | 不悬挂 | AC-2.3 |
| R-8 | 异常 | 源/分配失败 | 安全失败 | 既有对象不受损 | AC-2.4 |
| R-9 | 异常 | 结构化转移后的 Detached 源 | transferToImageBitmap/getContext 抛 103704；尺寸为 0 且 setter no-op | 与普通 ImageBitmap 快照分离 | AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | 源码审查+待补 png/jpeg/webp 编码矩阵 | MIME、NaN/Infinity/越界质量、SDK 默认值与 Dynamic 偏差；现有相关 UT 未覆盖特殊值 |
| VM-2 | AC-1.4 | 空/零尺寸/失效表面 UT | 安全失败 |
| VM-3 | AC-2.1~AC-2.3, AC-2.5 | 待补 bitmap 像素往返/detach 生命周期 UT | 快照不 detach、重复转移、结构化 Detached 与 103704；当前未找到活跃覆盖 |
| VM-4 | AC-2.4 | 分配失败注入 | 资源完整性 |

## API 变更分析

### 新增 API

N/A；`toDataURL` 和 `transferToImageBitmap` 均为 API 8 既有能力。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

| 接口 | 签名 | 默认/约束 | 关联 AC |
|------|------|-----------|---------|
| 数据导出 | `toDataURL(type?: string, quality?: any): string` | png；quality 0.92 | AC-1.1~AC-1.4 |
| Context 转移 | `OffscreenCanvasRenderingContext2D.transferToImageBitmap()` | 最近绘制图像 | AC-2.1~AC-2.4 |
| Canvas 转移 | `OffscreenCanvas.transferToImageBitmap()` | 当前离屏表面 | AC-2.1~AC-2.4 |
| Detached 错误 | `OffscreenCanvas.getContext/transferToImageBitmap` | Detached 时 BusinessError 103704 | AC-2.5 |

## 兼容性声明

- **最低支持版本:** API 8。
- **支持编码:** image/png、image/jpeg、image/webp。
- **默认质量:** SDK 对非法/缺省/NaN/Infinity quality 使用 0.92；当前 Dynamic NaN 是已知偏差，Static 会过滤。
- **Detached:** 结构化对象转移后的源在 getContext/transferToImageBitmap 抛 103704；普通快照转移不 detach 源。
- **互操作:** ImageBitmap 消费规则由 Canvas Feat-06 和 Pattern 规则承接。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 表面快照 | 导出/转移读取最近完成的离屏表面 | AC-1.1, AC-2.1 |
| 拷贝成本 | toDataURL 明示涉及耗时内存拷贝，不宜高频调用 | AC-1.1 |
| 生命周期 | 返回 ImageBitmap 必须安全持有其像素资源 | AC-2.3, AC-2.4 |
| 对象状态 | ImageBitmap 快照与 OffscreenCanvas 结构化 Detached 是不同状态机 | AC-2.1, AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 避免逐帧 toDataURL；编码耗时随表面面积增长 | Benchmark | VM-1 |
| 内存 | 编码中间缓冲和 ImageBitmap 资源可回收 | 泄漏测试 | VM-3 |
| 安全 | 编码尺寸与缓冲长度防溢出 | Fuzz | AC-1.4 |
| 可靠性 | 重复快照不返回悬挂/旧尺寸资源；Detached 源稳定抛 103704 | 压力/生命周期测试 | AC-2.3, AC-2.5 |
| 可测试性 | 编码头、尺寸和像素可解码校验 | UT | VM-1, VM-3 |
| 定界定位 | 表面读取、编码、bitmap 创建可分层定位 | Trace | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 内存/CPU 较敏感 | 降低大图导出频率 | 性能测试 | VM-1 |
| 平板 | 大表面编码成本高 | 格式语义不变 | 大尺寸矩阵 | VM-1 |
| 折叠屏 | 无自动尺寸绑定 | 导出当前显式尺寸 | 集成测试 | AC-2.1 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 导出无 UI 语义 | VM-1 |
| 大字体 | 否 | 仅导出已绘制像素 | VM-1 |
| 深色模式 | 否 | 不自动修改像素 | AC-1.1 |
| 多窗口/分屏 | 否 | 不绑定窗口 | AC-2.1 |
| 版本升级 | 是 | 编码和 bitmap 互操作保持 | VM-1, VM-3 |
| 生态兼容 | 是 | MIME/默认质量保持 | AC-1.3 |

## Spec 自审清单

- [x] 编码格式、SDK 质量默认、Dynamic NaN 偏差覆盖
- [x] bitmap 最近结果、快照不 detach、结构化 Detached/103704 和生命周期覆盖
- [x] 拷贝/分配成本明确
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "OffscreenCanvas toDataURL transferToImageBitmap"
  - repo: "openharmony/interface_sdk-js"
    query: "OffscreenCanvas export image png jpeg webp"
```

**关键文档：** `05-ui-components/14-drawing-components/03-offscreen-canvas/design.md`
