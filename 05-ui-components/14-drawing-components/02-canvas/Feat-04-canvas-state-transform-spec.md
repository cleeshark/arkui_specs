# 特性规格

> Func-05-14-02-Feat-04 Canvas 状态栈与几何变换存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Canvas 状态栈与几何变换 |
| 特性编号 | Func-05-14-02-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

本特性规定 Canvas 绘制状态的 `save`/`restore`、图层保存、复位以及二维矩阵的 translate、scale、rotate、transform、setTransform、resetTransform 和查询行为。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 状态栈 | save/restore、空栈、saveLayer |
| ADDED | 变换 | 平移、缩放、旋转、矩阵叠加和覆盖 |
| ADDED | 复位与查询 | reset/resetTransform/getTransform |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/02-canvas/design.md` | 并行补录 |
| SDK | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:2416-2428,2603-2883` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp` | 已核对 |
| RenderContext | `frameworks/core/components_ng/pattern/canvas/canvas_render_context_deferred.cpp` | 已核对 |

## 用户故事

### US-1: 保存和恢复绘制状态

**作为** 图形应用开发者  
**我想要** 临时修改样式、裁剪和矩阵后恢复  
**以便** 隔离局部绘制效果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 save THEN 当前变换、裁剪和可保存绘制属性压入状态栈 | 正常 |
| AC-1.2 | WHEN 状态栈非空时调用 restore THEN 弹出并恢复最近一次保存状态，遵循后进先出 | 正常 |
| AC-1.3 | WHEN 空状态栈调用 restore THEN 安全无操作且当前有效状态不变 | 边界 |
| AC-1.4 | WHEN API 12 调用 saveLayer THEN 建立离屏图层承接后续绘制并在恢复时按当前合成规则合回 | 正常 |

### US-2: 组合与重置几何矩阵

**作为** 应用开发者  
**我想要** 组合或覆盖当前二维变换  
**以便** 以局部坐标绘制对象

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN translate/scale/rotate 接收有限参数 THEN 当前变换按调用顺序组合，影响后续几何命令 | 正常 |
| AC-2.2 | WHEN transform 接收合法矩阵 THEN 与当前矩阵相乘；setTransform 则以给定矩阵覆盖当前矩阵 | 正常 |
| AC-2.3 | WHEN resetTransform 调用 THEN 当前变换恢复为单位矩阵，但其他绘制状态保持 | 正常 |
| AC-2.4 | WHEN 矩阵参数包含 NaN/Infinity 或对象字段非法 THEN 当前变换不应用该非法操作且后续合法命令可继续 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | state stack/layer UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:2416-2428,2835-2883`; `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp:226-727` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | matrix 参数化 UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:2603-2820` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | save | 压入完整可保存状态 | 不复制像素内容 | AC-1.1 |
| R-2 | 行为 | restore 且非空 | 恢复栈顶 | LIFO | AC-1.2 |
| R-3 | 边界 | restore 且空 | 无操作 | 不下溢 | AC-1.3 |
| R-4 | 行为 | saveLayer | 建离屏层并在恢复时合成 | API 12 | AC-1.4 |
| R-5 | 行为 | translate/scale/rotate | 后乘/组合当前矩阵 | 参数须有限 | AC-2.1 |
| R-6 | 行为 | transform/setTransform | 分别叠加/覆盖矩阵 | 顺序可观测 | AC-2.2 |
| R-7 | 行为 | resetTransform | 设单位矩阵 | 不清其他样式 | AC-2.3 |
| R-8 | 异常 | 非有限矩阵 | 忽略当前操作 | 保持可恢复状态 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | 嵌套 save/restore UT | LIFO 和空栈 |
| VM-2 | AC-1.4 | saveLayer 像素合成 UT | 图层边界与恢复 |
| VM-3 | AC-2.1~AC-2.4 | 矩阵几何 UT | 组合顺序、覆盖、复位、非法值 |

## API 变更分析

### 新增 API

N/A；`saveLayer`、单位配置和 reset 相关能力自 API 12 起为已有接口。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

| 接口组 | 代表签名 | 行为 | 关联 AC |
|--------|----------|------|---------|
| 状态栈 | `save()`; `restore()`; `saveLayer()` | LIFO/离屏图层 | AC-1.1~AC-1.4 |
| 基础变换 | `translate(x,y)`; `scale(x,y)`; `rotate(angle)` | 组合当前矩阵 | AC-2.1 |
| 矩阵 | `transform(...)`; `setTransform(...)`; `getTransform()` | 叠加/覆盖/查询 | AC-2.2 |
| 复位 | `resetTransform()`; `reset()` | 复位矩阵/上下文 | AC-2.3 |

## 兼容性声明

- **最低支持版本:** API 8。
- **版本节点:** saveLayer/reset 与 LengthMetricsUnit 相关能力 API 12；Static API 23。
- **已有 API 行为变更:** 否，版本新增按门控可用。
- **数据与配置格式变更:** 否。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 状态原子性 | save/restore 操作必须与绘制命令保持顺序 | AC-1.1, AC-1.2 |
| 后端一致性 | immediate/deferred 变换顺序及结果一致 | AC-2.1, AC-2.2 |
| Path 边界 | 当前变换影响路径命令；resetTransform 不清空已有路径对象 | AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | saveLayer 额外表面分配按图层面积受控 | 性能测试 | VM-2 |
| 内存 | 深状态栈和离屏层释放无泄漏 | 压力测试 | VM-1, VM-2 |
| 安全 | 空栈 restore 和非有限矩阵不越界 | Fuzz | AC-1.3, AC-2.4 |
| 可靠性 | immediate/deferred 状态序列等价 | 对照 UT | VM-3 |
| 可测试性 | getTransform 可直接断言矩阵结果 | UT | VM-3 |
| 定界定位 | 状态命令可在队列和后端分别定位 | Trace | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 常规图层规模 | 矩阵语义一致 | UT | VM-3 |
| 平板 | saveLayer 面积可能更大 | 监测内存和耗时 | 性能测试 | VM-2 |
| 折叠屏 | 尺寸变化后重新绘制 | 状态不跨清屏错误复用 | 折叠测试 | Feat-01 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 矩阵不生成语义 | VM-3 |
| 大字体 | 否 | 文本另行覆盖 | VM-3 |
| 深色模式 | 否 | 状态栈仅保存当前颜色值 | AC-1.1 |
| 多窗口/分屏 | 是 | 尺寸变化后由应用重建状态 | Feat-01 |
| 版本升级 | 是 | API 12 saveLayer 需门控 | VM-2 |
| 生态兼容 | 是 | 变换组合顺序保持 | AC-2.2 |

## Spec 自审清单

- [x] save/restore/空栈/saveLayer 覆盖
- [x] 矩阵叠加、覆盖、复位和非法值覆盖
- [x] immediate/deferred 等价约束明确
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Canvas save restore saveLayer transform resetTransform"
  - repo: "openharmony/interface_sdk-js"
    query: "Canvas transform saveLayer API 12"
```

**关键文档：** `05-ui-components/14-drawing-components/02-canvas/design.md`
