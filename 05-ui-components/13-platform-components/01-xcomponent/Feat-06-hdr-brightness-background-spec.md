# 特性规格

> Func-05-13-01-Feat-06 HDR 亮度与背景色：固化 SetHdrBrightness（含 HdrType）、HDR 背景色（ColorSpace/BT2020/HEADROOM）、SDR ratio 的行为规格，及按类型/版本的可用性差异。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | HDR 亮度与背景色 |
| 特性编号 | Func-05-13-01-Feat-06 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | SURFACE 背景色需 API≥11；HdrType/HDR 背景色随版本演进 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | HdrBrightness 规格 | SetHdrBrightness(value[, hdrtype])，clamp[0,1]，SURFACE-only |
| ADDED | HDR 背景色规格 | WithColorSpace / ForHDR(colorSpace,{r,g,b,a,headRoom}) |
| ADDED | SDR ratio 规格 | touch/size SDR ratio 读取与应用 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/13-platform-components/01-xcomponent/design.md` | Baselined |

---

## 用户故事

### US-1: 设置 HDR 亮度

**作为** 应用开发者,
**我想要** 通过 SetHdrBrightness 调整 HDR 显示亮度,
**以便** 呈现 HDR 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `SetHdrBrightness(value)` 且 type=SURFACE THEN clamp[0,1] 写入 hdrBrightness_，设 renderContext HDRBrightness；非 SURFACE 类型 no-op | 正常 |
| AC-1.2 | WHEN value 非数字 THEN 默认 1.0f | 边界 |
| AC-1.3 | WHEN 提供 hdrtype THEN 用 HdrType(DEFAULT=0/AIHDR=1) 设 HDRBrightness(v,type)；未提供（INVALID=-1）时用无 type 重载 | 正常 |
| AC-1.4 | WHEN reset THEN HdrBrightness(1.0f)（默认 1.0, DEFAULT） | 正常 |

### US-2: 设置 HDR 背景色

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN SetBackgroundColor 且颜色含 headroom THEN 走 ForHDR(colorSpace,{r,g,b,a,headRoom}) | 正常 |
| AC-2.2 | WHEN 颜色不含 headroom THEN 走 WithColorSpace(value,colorSpace)（DISPLAY_P3→P3，否则 SRGB） | 正常 |
| AC-2.3 | WHEN reset 背景色 THEN SURFACE→Color::BLACK；TEXTURE/NODE→Color::TRANSPARENT | 边界 |
| AC-2.4 | WHEN type=COMPONENT THEN 背景色 setter no-op；type=SURFACE 需 API≥11（IsBackGroundColorAvailable） | 边界 |

### US-3: SDR ratio

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN OnSurfaceCreated/Changed 且 SDR ratio 未初始化 THEN UpdateSdrRatioIfNeed 从全局 SDR_RATIOS 读取（XCOMPONENT_TOUCH/XCOMPONENT_SIZE，缺失用 RATIO_DEFAULT） | 正常 |
| AC-3.2 | WHEN 报告尺寸到 native impl THEN 乘以 xcomponentSizeSdrRatio_ | 正常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.x | R-1~R-3 | 代码评审 | `xcomponent_pattern.cpp:2599-2618` |
| AC-2.x | R-4~R-6 | 代码评审 | `xcomponent_dynamic_modifier.cpp:100-151` |
| AC-3.x | R-7 | 代码评审 | `xcomponent_pattern.cpp:2717-2738` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | SetHdrBrightness SURFACE | clamp[0,1] 写 hdrBrightness_，设 renderContext | 非 SURFACE no-op | AC-1.1 |
| R-2 | 边界 | value 非数字 | 默认 1.0f | INVALID_HDR_TYPE=-1 | AC-1.2 |
| R-3 | 行为 | hdrtype 提供/未提供 | 有 type 用 HdrBrightness(v,HdrType)；无 type 用单参重载；reset→1.0 | HdrType DEFAULT=0/AIHDR=1 | AC-1.3, AC-1.4 |
| R-4 | 行为 | 背景色含 headroom | ForHDR(colorSpace,{r,g,b,a,headRoom}) | — | AC-2.1 |
| R-5 | 行为 | 背景色不含 headroom | WithColorSpace(value,colorSpace) | P3/SRGB | AC-2.2 |
| R-6 | 边界 | reset 背景色 / type 可用性 | SURFACE→BLACK；TEXTURE/NODE→TRANSPARENT；COMPONENT no-op；SURFACE 需 API≥11 | — | AC-2.3, AC-2.4 |
| R-7 | 行为 | SDR ratio 未初始化 | 从全局 SDR_RATIOS 读 TOUCH/SIZE，缺失用 RATIO_DEFAULT；报告尺寸乘 size ratio | 互斥保护 | AC-3.x |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.x, R-1~R-3 | 代码评审 | HdrBrightness clamp 与 HdrType |
| VM-2 | AC-2.x, R-4~R-6 | 代码评审 | HDR 背景色分流与 reset 默认值 |
| VM-3 | AC-3.x, R-7 | 代码评审 | SDR ratio 读取与应用 |

---

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| SetHdrBrightness | Public | value[, hdrtype] | XComponentAttribute | N/A | HDR 亮度 | AC-1.1 |
| SetBackgroundColor(HDR) | Public | Color/ColorSpace | XComponentAttribute | N/A | HDR 背景色 | AC-2.1 |

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

**SetHdrBrightness(value[, hdrtype])**

| 属性 | 值 |
|------|-----|
| 函数签名 | `XComponentAttribute SetHdrBrightness(float value)` / `SetHdrBrightness(float value, HdrType type)` |
| 返回值 | XComponentAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | float | 是 | 1.0 | clamp[0,1] |
| hdrtype | HdrType | 否 | INVALID(-1)/DEFAULT(0) | DEFAULT=0, AIHDR=1 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** SURFACE 背景色 API≥11；TEXTURE/NODE 背景色始终可用
- **按类型可用性:** HdrBrightness 仅 SURFACE；背景色 COMPONENT 不可用

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| HdrBrightness SURFACE-only | 类型守卫 | AC-1.1 |
| 背景色 IsBackGroundColorAvailable | COMPONENT 不可用；SURFACE 需 API≥11 | AC-2.4 |
| SDR ratio 全局表 | 缺失用 RATIO_DEFAULT | AC-3.1 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | HDR 亮度/背景色设置应即时生效 | 集成测试 | `xcomponent_pattern.cpp` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | HDR 效果受设备显示能力限制 | — | 集成测试 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 深色模式 | 否 | HDR 独立于深色模式 | — |
| 其余 | 否 | — | — |

---

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN
- [x] 范围边界明确
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "XComponent HdrBrightness clamp 与 HdrType、HDR 背景色 ForHDR/WithColorSpace 分流"
  - repo: "openharmony/ace_engine"
    query: "SDR ratio 全局表 UpdateSdrRatioIfNeed"
```

**关键文档：** `xcomponent_dynamic_modifier.cpp:100-151,491-494,1385-1401`、`xcomponent_pattern.cpp:2599-2618,2717-2738`
