# 特性规格

> Func-05-14-02-Feat-03 Canvas 绘制样式与合成存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Canvas 绘制样式与合成 |
| 特性编号 | Func-05-14-02-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性覆盖 Canvas 填充、描边、渐变、图案、线型、阴影、透明度、合成模式、滤镜和抗锯齿等绘制状态，以及矩形和路径绘制对这些状态的消费规则。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 填充和描边样式 | Color/Gradient/Pattern、线帽、连接、虚线 |
| ADDED | 合成效果 | alpha、composite、shadow、filter、antialias |
| ADDED | 渐变与图案对象 | 线性/径向/锥形渐变、色标与重复模式 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/02-canvas/design.md` | 并行补录 |
| SDK | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:190-273,782-935,1373-1930,2200-2415` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp` | 已核对 |
| Paint | `frameworks/core/components_ng/pattern/canvas/canvas_paint_method.cpp` | 已核对 |

## 用户故事

### US-1: 配置填充和描边

**作为** 图形应用开发者  
**我想要** 用颜色、渐变或图案设置画刷和画笔  
**以便** 获得一致的视觉样式

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN fillStyle/strokeStyle 设置为合法颜色、CanvasGradient 或 CanvasPattern THEN 后续 fill/fillRect 或 stroke/strokeRect 使用对应样式 | 正常 |
| AC-1.2 | WHEN 创建线性、径向或 API 10 锥形渐变并添加合法色标 THEN 按色标偏移和颜色插值绘制 | 正常 |
| AC-1.3 | WHEN colorStop 为 null/undefined THEN 忽略本次添加；WHEN offset 越界、Infinity 或颜色无效 THEN 按 SDK 使该渐变无效；WHEN offset=NaN THEN 按 SDK 抛参数异常；WHEN API 20 混用不同 ColorSpace THEN 抛 BusinessError 103701 | 异常 |
| AC-1.4 | WHEN CanvasPattern 使用 repeat/repeat-x/repeat-y/no-repeat THEN 图像按指定重复方向填充；无效源不输出像素 | 正常 |
| AC-1.5 | WHEN Dynamic colorStop 收到越界 offset/非法颜色 THEN 当前实现先清空全部既有 stop 并写入两个透明 stop；NaN 可穿透存储；WHEN Static 使用 ColorMetrics stop THEN 当前 visitor 为 no-op；这些属于 SDK 实现偏差 | 异常 |

### US-2: 控制描边和像素合成

**作为** 应用开发者  
**我想要** 配置线型、阴影、透明度与合成模式  
**以便** 构建可预测的叠加效果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 lineWidth/lineCap/lineJoin/miterLimit 和 lineDash THEN 后续描边消费当前合法线型状态 | 正常 |
| AC-2.2 | WHEN Dynamic globalAlpha 为有限越界值 THEN SDK 要求钳制到 [0,1]；API<18 的 NaN/Infinity 可污染后续绘制，API>=18 非有限赋值无效；WHEN Static globalAlpha 越界或非有限 THEN SDK 要求该次赋值无效 | 边界 |
| AC-2.3 | WHEN globalCompositeOperation 为支持值 THEN 新旧像素按对应 Porter-Duff/扩展模式合成，无效值保留有效默认/既有状态 | 正常 |
| AC-2.4 | WHEN 设置 shadow、filter 或抗锯齿 THEN 后续绘制应用当前状态；RenderingContextSettings 的抗锯齿不替代 API 24 文本 antialias 属性 | 边界 |
| AC-2.5 | WHEN 当前 Dynamic 实现接收有限越界 globalAlpha THEN 未按 SDK 钳制而直接保存；WHEN Static 实现接收有限越界值 THEN 当前实现钳制，非有限值被过滤；两条实现均需作为各自 SDK 偏差记录 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-4, R-9 | 已有实现 | SDK/源码审查+待补偏差 UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:190-273,782-935,1690-1855`; `frameworks/bridge/declarative_frontend/jsview/canvas/js_canvas_gradient.cpp:50-104` |
| AC-2.1~AC-2.5 | R-5~R-8, R-10 | 已有实现 | SDK/源码审查+API 17/18/Static UT 待补 | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:1373-1497,2060-2305`; `frameworks/bridge/declarative_frontend/jsview/canvas/js_canvas_renderer.cpp:178-185,1108-1113`; `frameworks/core/interfaces/native/implementation/canvas_renderer_peer_impl.cpp:175-183,738-750` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 合法 fill/stroke style | 更新对应画刷/画笔 | 属性写入影响后续命令 | AC-1.1 |
| R-2 | 行为 | 合法 gradient+stops | 创建并使用插值着色 | conic 自 API 10 | AC-1.2 |
| R-3 | 异常 | SDK colorStop 非法输入 | null/undefined 忽略；越界/Infinity/非法色使渐变无效；NaN 抛参数异常；混合 ColorSpace 抛 103701 | 外部契约以 SDK 为准 | AC-1.3 |
| R-4 | 行为 | pattern+repeat | 按方向平铺源图 | 无效源不绘制 | AC-1.4 |
| R-5 | 行为 | 合法线型属性 | 更新描边状态 | lineWidth 须合法 | AC-2.1 |
| R-6 | 边界 | globalAlpha 越界/非有限 | Dynamic 有限越界 clamp，非有限以 API 18 分界；Static 非法赋值无效 | SDK 契约按范式拆分 | AC-2.2 |
| R-7 | 行为 | 合法 composite | 按指定方式合成 | 默认 source-over | AC-2.3 |
| R-8 | 行为 | shadow/filter/AA | 后续命令使用状态 | 文本 AA 单独控制 | AC-2.4 |
| R-9 | 异常 | 当前实现处理非法 colorStop | Dynamic 清旧 stop/写透明 stop且 NaN 穿透；Static ColorMetrics no-op | 与 SDK 偏离，不能声称保留既有 stop | AC-1.5 |
| R-10 | 异常 | 当前实现处理 globalAlpha | Dynamic 有限越界不 clamp；Static 有限越界 clamp、非有限过滤 | 两范式均与各自 SDK 契约存在偏差 | AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.5 | 源码审查+待补 gradient/XTS | 旧 stop 破坏、NaN、Infinity、ColorMetrics 与混合 ColorSpace 103701；现有活跃 UT 未覆盖这些偏差 |
| VM-2 | AC-2.1 | 描边几何 UT | cap/join/dash/miter |
| VM-3 | AC-2.2~AC-2.5 | 待补 Dynamic API 17/18 与 Static 参数化 UT | SDK 契约、有限越界与非有限实现偏差、模式、阴影和 AA |

## API 变更分析

### 新增 API

N/A；本次记录 API 8 起样式能力、API 10 锥形渐变及 API 24 antialias 等已有接口。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

| 接口组 | 代表接口 | 默认/约束 | 关联 AC |
|--------|----------|-----------|---------|
| 画刷/画笔 | `fillStyle`, `strokeStyle` | 合法 Color/Gradient/Pattern | AC-1.1 |
| 渐变/图案 | `createLinearGradient/createRadialGradient/createConicGradient/createPattern` | 色标 SDK 契约含无效渐变、NaN 参数异常与混合 ColorSpace 103701 | AC-1.2~AC-1.5 |
| 线型 | `lineWidth/lineCap/lineJoin/miterLimit/setLineDash` | 写入绘制状态 | AC-2.1 |
| 合成 | `globalAlpha/globalCompositeOperation/shadow*/filter/antialias` | Dynamic 与 Static alpha 非法处理契约不同 | AC-2.2~AC-2.5 |

## 兼容性声明

- **最低支持版本:** API 8。
- **版本节点:** 锥形渐变 API 10；ColorMetrics 渐变 API 20；Static API 23；antialias 属性 API 24。
- **行为分界:** Dynamic globalAlpha 非有限值在 API 18 前后处理不同；Static 越界赋值无效。当前 Dynamic/Static 实现各有偏差。
- **配置与数据格式变更:** 否。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 状态快照 | 绘制命令消费提交时对应的画笔/画刷状态 | AC-1.1, AC-2.1 |
| 对象生命周期 | Gradient/Pattern 由 context 对象转换为底层着色资源 | AC-1.2, AC-1.4 |
| 后端一致性 | immediate/deferred 必须产生等价合法像素结果 | AC-2.3 |
| SDK 优先 | colorStop/globalAlpha 的对外契约按 Dynamic/Static SDK；实现差异不得反写为统一契约 | AC-1.3, AC-1.5, AC-2.2, AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 阴影、滤镜和复杂渐变按像素面积受控 | 性能矩阵 | VM-1 |
| 内存 | Pattern 源和渐变色标生命周期安全 | 生命周期 UT | VM-1 |
| 安全 | Dynamic colorStop NaN 与 globalAlpha 非法值当前可穿透状态，需专项 Fuzz | 待补 Fuzz | AC-1.5, AC-2.5 |
| 可靠性 | Dynamic 非法 colorStop 会破坏旧 stop；实现偏差应可复现且不被误报为契约 | 回归/XTS | VM-1, VM-3 |
| 可测试性 | 结果可通过目标像素/容差断言 | 金图测试 | VM-1~VM-3 |
| 定界定位 | 属性设置与绘制命令可分别 Trace | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 常规密度 | 颜色和合成语义一致 | 金图 | VM-1 |
| 平板 | 大面积滤镜成本更高 | 保持像素语义 | 性能测试 | VM-3 |
| 折叠屏 | 重绘面积变化 | 状态不因窗口变化隐式改变 | 折叠测试 | Feat-01 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 样式不产生语义 | VM-1 |
| 大字体 | 否 | 文本另由 Feat-05 覆盖 | VM-1 |
| 深色模式 | 是 | 应用可在重绘时切换颜色 | AC-1.1 |
| 多窗口/分屏 | 是 | 重绘后样式保持 | Feat-01 |
| 版本升级 | 是 | API 18/20/24 行为需回归 | VM-3 |
| 生态兼容 | 是 | 默认 source-over 等历史语义保持 | AC-2.3 |

## Spec 自审清单

- [x] 画刷、画笔、渐变、图案和合成覆盖
- [x] colorStop 的 SDK 契约、103701 与 Dynamic/Static 实现偏差明确
- [x] Dynamic/Static globalAlpha 契约及各自实现偏差明确
- [x] 文本 antialias 边界明确
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Canvas fillStyle gradient pattern globalCompositeOperation antialias"
  - repo: "openharmony/interface_sdk-js"
    query: "Canvas globalAlpha API 18 conic gradient antialias 24"
```

**关键文档：** `05-ui-components/14-drawing-components/02-canvas/design.md`
