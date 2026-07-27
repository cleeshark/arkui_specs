# 特性规格

> Func-05-14-02-Feat-05 Canvas 文本绘制与度量存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Canvas 文本绘制与度量 |
| 特性编号 | Func-05-14-02-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性覆盖 Canvas 的字体、字距、文本对齐、基线、方向、抗锯齿、填充/描边文本和 TextMetrics 度量。文本绘制消费当前样式与矩阵，但不产生 ArkUI 文本组件或自动无障碍语义。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 文本状态 | font、align、baseline、direction、letterSpacing、antialias |
| ADDED | 文本绘制 | fillText、strokeText 和 maxWidth |
| ADDED | 文本度量 | measureText 与 TextMetrics 字段 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/02-canvas/design.md` | 并行补录 |
| SDK | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:936-1012,1373-1497,2306-2490` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp` | 已核对 |
| Tests | `test/unittest/core/pattern/canvas/` | 已核对 |

## 用户故事

### US-1: 绘制可控文本

**作为** 图形应用开发者  
**我想要** 在画布坐标中设置字体和排版属性  
**以便** 绘制与几何内容对齐的文字

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN font、textAlign、textBaseline、direction 设置为支持值 THEN 后续 fillText/strokeText 使用对应字体和锚点布局 | 正常 |
| AC-1.2 | WHEN fillText/strokeText 接收合法文本、坐标和可选 maxWidth THEN 在当前变换、画刷/画笔和合成状态下绘制 | 正常 |
| AC-1.3 | WHEN 坐标或 maxWidth 为 NaN/Infinity，或 font 字符串不可解析 THEN 当前调用按 SDK 规则忽略或回退默认字体，不阻断后续绘制 | 异常 |
| AC-1.4 | WHEN API 18 设置合法 letterSpacing THEN 字符间距按单位和正负值生效；PERCENT/FP/LPX 等不支持输入按无效值处理 | 边界 |

### US-2: 度量文本并控制抗锯齿

**作为** 应用开发者  
**我想要** 在绘制前获取文本边界并选择文本抗锯齿  
**以便** 实现精确排版

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN measureText 接收字符串 THEN 返回与当前 font/letterSpacing/direction 一致的 TextMetrics，不在画布上产生像素 | 正常 |
| AC-2.2 | WHEN 读取 TextMetrics THEN width 和实现支持的 actual/font/em/hanging/alphabetic/ideographic 等边界字段反映度量结果 | 正常 |
| AC-2.3 | WHEN API 24 设置文本 antialias 属性 THEN 后续文本使用该抗锯齿设置；RenderingContextSettings.antialias 仍只控制非文本绘制 | 边界 |
| AC-2.4 | WHEN 文本为空字符串 THEN 绘制不产生字形但 measureText 返回有效零宽或字体边界结果，且不异常 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | text paint 参数化 UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:1373-1497,2306-2490` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | TextMetrics/AA UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:936-1012,2491-2550`; `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp:226-727` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 合法文本属性 | 更新排版状态 | 非法值回退/忽略 | AC-1.1 |
| R-2 | 行为 | fillText/strokeText | 在给定锚点绘制 | maxWidth 可选 | AC-1.2 |
| R-3 | 异常 | 非有限坐标/非法 font | 忽略当前绘制或回退 | 后续调用可继续 | AC-1.3 |
| R-4 | 行为 | letterSpacing | 按合法单位写入字距 | API 18，禁用单位无效 | AC-1.4 |
| R-5 | 行为 | measureText | 返回度量且不绘制 | 使用当前文本状态 | AC-2.1 |
| R-6 | 行为 | TextMetrics 字段 | 返回实现支持边界 | 单位随 context | AC-2.2 |
| R-7 | 行为 | text antialias | 控制后续文本 AA | API 24，与 settings 分离 | AC-2.3 |
| R-8 | 边界 | 空字符串 | 无字形且安全度量 | 不异常 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | 字体/对齐/基线像素 UT | 锚点、maxWidth、非法值 |
| VM-2 | AC-1.4 | API 17/18 字距矩阵 | 单位、负值、小数 |
| VM-3 | AC-2.1~AC-2.4 | TextMetrics 与 AA UT | 无副作用、字段、空串、API 24 |

## API 变更分析

### 新增 API

N/A；文本绘制和度量自 API 8，letterSpacing 自 API 18，文本 antialias 自 API 24，均为已有能力。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

| 接口组 | 代表接口 | 默认/约束 | 关联 AC |
|--------|----------|-----------|---------|
| 文本状态 | `font`, `textAlign`, `textBaseline`, `direction` | 合法枚举/字体字符串 | AC-1.1 |
| 绘制 | `fillText(text,x,y,maxWidth?)`; `strokeText(...)` | 坐标有限 | AC-1.2~AC-1.3 |
| 字距/AA | `letterSpacing`; `antialias` | API 18/API 24 | AC-1.4, AC-2.3 |
| 度量 | `measureText(text): TextMetrics` | 无绘制副作用 | AC-2.1~AC-2.2 |

## 兼容性声明

- **最低支持版本:** API 8。
- **版本节点:** letterSpacing API 18；TextMetrics 字段随版本增强；文本 antialias API 24。
- **已有行为变化:** 新版本属性未设置时保持历史默认排版和文本抗锯齿行为。
- **数据与配置格式变更:** 否。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 排版依赖 | 文本由底层字体/段落度量能力支持，不创建 TextPattern | AC-1.2, AC-2.1 |
| 单位一致 | 字体、字距和坐标统一受 context 单位模式约束 | AC-1.4 |
| AA 分离 | 文本 antialias 与 RenderingContextSettings.antialias 分离 | AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 字体匹配和 glyph 生成可缓存，不在空串上产生无用绘制 | Benchmark | VM-3 |
| 内存 | TextMetrics 不持有失效 Canvas 表面 | 生命周期 UT | VM-3 |
| 安全 | 非法 font/非有限坐标不进入底层危险路径 | Fuzz | AC-1.3 |
| 可靠性 | measureText 与实际绘制在容差内一致 | 对照测试 | VM-1, VM-3 |
| 可测试性 | metrics 数值和像素结果均可断言 | UT/金图 | VM-1~VM-3 |
| 定界定位 | 文本状态、排版、绘制阶段可分层定位 | Trace | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 常规密度和字体缩放 | Canvas 字体不自动继承组件排版 | 字体矩阵 | AC-1.1 |
| 平板 | 更长文本行 | maxWidth 和度量规则不变 | 长文本测试 | AC-1.2 |
| 折叠屏 | 重绘时可重新排版 | 度量使用当前 context | 折叠测试 | AC-2.1 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Canvas 文本不自动产生可访问文本节点，应用需补充语义 | AC-1.2 |
| 大字体 | 是 | font 由应用设置，不自动随系统 Text 组件规则调整 | AC-1.1 |
| 深色模式 | 是 | 应用需更新 fill/strokeStyle 并重绘 | AC-1.2 |
| 多窗口/分屏 | 是 | 重新度量和绘制 | AC-2.1 |
| 版本升级 | 是 | API 18/24 属性需回归 | VM-2, VM-3 |
| 生态兼容 | 是 | 旧排版默认保持 | AC-1.1 |

## Spec 自审清单

- [x] 绘制、排版、度量和空串边界覆盖
- [x] letterSpacing 单位限制明确
- [x] 两类抗锯齿设置边界明确
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Canvas fillText measureText TextMetrics letterSpacing antialias"
  - repo: "openharmony/interface_sdk-js"
    query: "Canvas text API 18 24"
```

**关键文档：** `05-ui-components/14-drawing-components/02-canvas/design.md`
