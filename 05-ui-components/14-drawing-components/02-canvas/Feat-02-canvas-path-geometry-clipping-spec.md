# 特性规格

> Func-05-14-02-Feat-02 Canvas 路径几何与裁剪存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Canvas 路径几何与裁剪 |
| 特性编号 | Func-05-14-02-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

Canvas 通过 `CanvasPath`、当前路径和 `Path2D` 构造直线、曲线、圆弧、椭圆、矩形与圆角矩形，并按填充规则执行 fill、stroke 和 clip。本特性规定路径状态、独立路径对象、参数退化、裁剪栈及命中判定边界。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 路径构造 | begin/close、线段、曲线、圆弧和矩形 |
| ADDED | Path2D | 独立路径创建、复制、SVG 字符串和 addPath |
| ADDED | 填充与裁剪 | nonzero/evenodd、fill/stroke/clip 和命中测试 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/02-canvas/design.md` | 并行补录 |
| SDK | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:274-781,1598-1687` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp` | 已核对 |
| Tests | `test/unittest/core/pattern/canvas/` | 已核对 |

## 用户故事

### US-1: 构造和绘制路径

**作为** 图形应用开发者  
**我想要** 组合几何命令并复用 Path2D  
**以便** 绘制复杂轮廓

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 beginPath 后依次调用 moveTo/lineTo/curve/arc/ellipse/rect/roundRect THEN 当前路径按调用顺序构造并可被 fill 或 stroke 绘制 | 正常 |
| AC-1.2 | WHEN closePath 作用于存在子路径的当前路径 THEN 当前子路径闭合到起点；空路径调用保持安全无输出 | 边界 |
| AC-1.3 | WHEN 从空值、另一 Path2D 或合法 SVG path 字符串创建 Path2D THEN 形成独立可复用路径且不改写原对象 | 正常 |
| AC-1.4 | WHEN addPath 接收合法 Path2D 与变换矩阵 THEN 将变换后的源路径追加到目标路径 | 正常 |

### US-2: 裁剪和判定路径区域

**作为** 应用开发者  
**我想要** 按填充规则限制后续绘制并检测坐标关系  
**以便** 实现遮罩和交互区域

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN fill/clip 使用 nonzero 或 evenodd THEN 按指定填充规则确定内部区域，未传或非法规则按 nonzero 处理 | 正常 |
| AC-2.2 | WHEN clip 执行后继续绘制 THEN 输出限制在当前裁剪区与既有裁剪区的交集内，直至 restore 恢复 | 正常 |
| AC-2.3 | WHEN 非 roundRect 几何参数含 NaN/Infinity THEN 当前命令按对应 SDK 规则忽略或退化，不污染后续合法路径命令 | 异常 |
| AC-2.4 | WHEN isPointInPath/isPointInStroke 接收合法点和可选 Path2D THEN 返回该点与指定路径填充区/描边区的关系 | 正常 |
| AC-2.5 | WHEN roundRect radii 为 null/undefined THEN 按 0 处理；WHEN 半径为负、数组为空或数组项数超过 4 THEN 同步抛出 BusinessError 103701，且不追加该 roundRect 命令 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Path/Path2D UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:274-781`; `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp:226-727` |
| AC-2.1~AC-2.5 | R-5~R-9 | 已有实现 | clip/hit-test UT；roundRect parser 测试待补 | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:601-624,1598-1687,2490-2602`; `frameworks/bridge/declarative_frontend/jsview/canvas/js_canvas_util.cpp:44-80`; `frameworks/bridge/declarative_frontend/jsview/canvas/js_canvas_renderer.cpp:1408-1416` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | beginPath+几何命令 | 重建当前路径并顺序追加 | 坐标使用 context 单位 | AC-1.1 |
| R-2 | 边界 | closePath | 闭合当前子路径 | 空路径无操作 | AC-1.2 |
| R-3 | 行为 | 构造 Path2D | 创建独立路径 | SVG 字符串需可解析 | AC-1.3 |
| R-4 | 行为 | addPath+matrix | 变换并追加副本 | 不改源路径 | AC-1.4 |
| R-5 | 行为 | fill/clip | 使用指定 fillRule | 默认 nonzero | AC-2.1 |
| R-6 | 行为 | clip | 与当前 clip 求交并入状态栈 | restore 可回退 | AC-2.2 |
| R-7 | 异常 | 非 roundRect 几何参数非有限 | 按对应 API 忽略或退化当前命令 | 后续命令可继续 | AC-2.3 |
| R-8 | 行为 | point hit-test | 返回布尔关系 | 坐标与当前变换一致 | AC-2.4 |
| R-9 | 异常 | roundRect radii 负值、空数组或超过 4 项 | 同步抛 BusinessError 103701 | null/undefined 按 0；失败命令不追加 | AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.2 | 路径几何 UT | 子路径、闭合、曲线和圆角 |
| VM-2 | AC-1.3~AC-1.4 | Path2D 复制/变换 UT | 独立性和 SVG 解析 |
| VM-3 | AC-2.1~AC-2.5 | clip/fill/hit-test UT+待补 roundRect parser/XTS | 规则、交集、非有限值及 103701；现有多个 CanvasPath accessor 用例为 DISABLED |

## API 变更分析

### 新增 API

N/A；基础路径 API 自 API 8、`roundRect` 自 API 20 均为已有能力。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

| 接口组 | 代表签名 | 约束 | 关联 AC |
|--------|----------|------|---------|
| CanvasPath | `moveTo/lineTo/bezierCurveTo/quadraticCurveTo/arc/arcTo/ellipse/rect` | 非有限值按对应 SDK 无效/退化 | AC-1.1, AC-2.3 |
| roundRect | `roundRect(x, y, w, h, radii?)` | null/undefined 半径为 0；负值、空数组、数组>4 抛 103701 | AC-1.1, AC-2.5 |
| Path2D | `constructor(path?)`; `addPath(path, transform?)` | 独立路径 | AC-1.3~AC-1.4 |
| 绘制/裁剪 | `fill(path?, rule?)`; `stroke(path?)`; `clip(path?, rule?)` | rule=nonzero/evenodd | AC-2.1~AC-2.2 |
| 命中测试 | `isPointInPath`; `isPointInStroke` | 返回 boolean | AC-2.4 |

## 兼容性声明

- **最低支持版本:** API 8。
- **版本节点:** cross-platform API 10；`roundRect` API 20；Static API 23。
- **已有行为变化:** 圆角矩形自 API 20 可用，并具有 BusinessError 103701 参数契约；基础路径行为保持。
- **数据与配置格式变更:** 否。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 路径隔离 | 当前路径、Path2D 及 Offscreen 当前路径相互独立 | AC-1.3 |
| 命令模式 | 路径操作经 CanvasRenderContext immediate/deferred 路径提交 | AC-1.1 |
| 裁剪状态 | clip 是绘制状态的一部分，由 save/restore 管理 | AC-2.2 |
| 错误边界 | roundRect radii 的参数错误同步抛 103701，不按普通非有限几何静默忽略 | AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 路径成本随命令数和曲线细分增长 | Benchmark | VM-1 |
| 内存 | Path2D 生命周期独立且复制不悬挂 | 生命周期 UT | VM-2 |
| 安全 | 普通非有限参数不进入底层非法几何；roundRect 错误参数在 parser 层抛 103701 | Fuzz/XTS | AC-2.3, AC-2.5 |
| 可靠性 | 空路径、空 clip 和 restore 安全 | 边界 UT | VM-3 |
| 可测试性 | 几何边界可像素和布尔双断言 | UT | VM-1~VM-3 |
| 定界定位 | SDK→Bridge→CanvasPaintMethod 路径可追踪 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 默认密度坐标 | 使用 context 单位换算 | 截图测试 | AC-1.1 |
| 平板 | 路径规模可能更大 | fillRule 结果不变 | 大路径测试 | AC-2.1 |
| 折叠屏 | 尺寸变化后应用重建路径 | 不隐式缩放历史像素 | 折叠测试 | Feat-01 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 路径不自动生成语义节点 | VM-1 |
| 大字体 | 否 | 本 Feat 不含文本 | VM-1 |
| 深色模式 | 否 | 几何不决定颜色 | AC-1.1 |
| 多窗口/分屏 | 是 | 重绘后几何按新尺寸构造 | Feat-01 |
| 版本升级 | 是 | API 20 roundRect 需门控 | VM-1 |
| 生态兼容 | 是 | fillRule 与 Path2D 语义保持 | AC-2.1 |

## Spec 自审清单

- [x] 当前路径、Path2D、裁剪状态边界明确
- [x] 非有限值与空路径覆盖
- [x] roundRect 版本、radii 归一与 103701 错误契约明确
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "CanvasPath Path2D clip isPointInPath"
  - repo: "openharmony/interface_sdk-js"
    query: "CanvasPath roundRect API 20"
```

**关键文档：** `05-ui-components/14-drawing-components/02-canvas/design.md`
