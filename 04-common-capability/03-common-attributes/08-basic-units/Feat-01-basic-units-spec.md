# 特性规格

> Func-04-03-08-Feat-01 基础单位：固化 vp/fp/px/lpx/percent/Dimension/Length 类型、单位换算、资源解析与字体缩放钳位行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 基础单位 (Basic Units) |
| 特性编号 | Func-04-03-08-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 10 模板字面量类型引入 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | vp/fp/px/lpx/percent/Dimension 单位换算与资源解析行为 | 补录基础度量单位行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/08-basic-units/design.md` | Baselined |
| SDK API | `interface/sdk-js/api/@internal/component/ets/units.d.ts` | — |

---

## 用户故事

### US-1: 单位换算

**作为** 应用开发者,
**我想要** 使用 vp/fp/px/lpx/percent 不同单位设置尺寸,
**以便** 适配不同屏幕密度与字体偏好。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 单位为 PX 或 NONE THEN ConvertToPx 返回 value（原始物理像素） | 正常 |
| AC-1.2 | WHEN 单位为 VP THEN ConvertToPx 返回 value * dipScale | 正常 |
| AC-1.3 | WHEN 单位为 FP THEN ConvertToPx 返回 value * fpScale * vpScale（FP = VP * fontScale） | 正常 |
| AC-1.4 | WHEN 单位为 LPX THEN ConvertToPx 返回 value * lpxScale（logicScale） | 正常 |
| AC-1.5 | WHEN 单位为 PERCENT THEN NormalizeToPx 返回 value * parentLength | 边界 |
| AC-1.6 | WHEN dipScale 计算时 THEN dipScale = density / viewScale | 边界 |

### US-2: Dimension 构造与默认值

**作为** 应用开发者,
**我想要** 构造 Dimension 对象并了解默认值,
**以便** 正确设置尺寸属性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 无参构造 Dimension() THEN value=0.0, unit=PX | 边界 |
| AC-2.2 | WHEN FromString 解析空字符串或未知单位 THEN 默认单位为 FP | 边界 |
| AC-2.3 | WHEN FromString 解析 "50%" THEN 值除以 100 存储 | 正常 |
| AC-2.4 | WHEN operator/ 除数为 0(NEAR_ZERO) THEN 返回默认 Dimension{} | 异常 |

### US-3: 资源解析（$r/$rawfile）

**作为** 应用开发者,
**我想要** 通过 $r 引用资源设置尺寸,
**以便** 实现多语言/多密度自适应。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN ParseJsDimension 收到 number THEN 构造 CalcDimension(num, defaultUnit) | 正常 |
| AC-3.2 | WHEN ParseJsDimension 收到 string THEN 通过 StringUtils::StringToCalcDimension 解析 | 正常 |
| AC-3.3 | WHEN ParseJsDimension 收到 Resource 对象 THEN CompleteResourceObjectInner 解析 $r 资源 | 正常 |
| AC-3.4 | WHEN 资源类型为 FLOAT THEN 返回原始像素值（"true pixel value"） | 边界 |

### US-4: 字体缩放钳位

**作为** 系统开发者,
**我想要** 字体缩放被钳位到 [0, maxAppFontScale],
**以便** 防止过大字体破坏布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN fontScale 默认 THEN fontScale_=1.0f | 边界 |
| AC-4.2 | WHEN maxAppFontScale 默认 THEN maxAppFontScale_=INT32_MAX | 边界 |
| AC-4.3 | WHEN 字体缩放生效 THEN std::clamp(fontScale, 0.0f, maxAppFontScale_) | 正常 |

### US-5: CalcDimension 与 CalcLength

**作为** 应用开发者,
**我想要** 使用 calc() 表达式设置尺寸,
**以便** 实现复杂计算布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN CalcDimension 构造 THEN calcvalue_ 存储表达式字符串，unit=CALC | 正常 |
| AC-5.2 | WHEN CalcLength::NormalizeToPx THEN 支持 RPN 表达式向量计算 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 dimension.cpp:37-47 |
| AC-1.2 | US-1 | R-2 | 代码审查 dimension.cpp:58-65 |
| AC-1.3 | US-1 | R-3 | 代码审查 dimension.cpp:67-74 |
| AC-1.4 | US-1 | R-4 | 代码审查 dimension.cpp:76-83 |
| AC-1.5 | US-1 | R-5 | 代码审查 dimension.h:450-471 |
| AC-1.6 | US-1 | R-6 | 代码审查 pipeline_base.cpp:552-561 |
| AC-2.1 | US-2 | R-7 | 代码审查 dimension.h:94 |
| AC-2.2 | US-2 | R-8 | 代码审查 dimension.h:428 |
| AC-2.3 | US-2 | R-9 | 代码审查 dimension.h:443 |
| AC-2.4 | US-2 | R-19 | 代码审查 dimension.h:277-279 |
| AC-3.1 | US-3 | R-10 | 代码审查 js_view_abstract.cpp:6742-6744 |
| AC-3.2 | US-3 | R-11 | 代码审查 js_view_abstract.cpp:6746-6748 |
| AC-3.3 | US-3 | R-12 | 代码审查 js_view_abstract.cpp:6757-6780 |
| AC-3.4 | US-3 | R-13 | 代码审查 js_view_abstract.cpp:6643 |
| AC-4.1 | US-4 | R-14 | 代码审查 pipeline_base.h:1700 |
| AC-4.2 | US-4 | R-15 | 代码审查 pipeline_base.h:1828 |
| AC-4.3 | US-4 | R-16 | 代码审查 dimension.cpp clamp |
| AC-5.1 | US-5 | R-17 | 代码审查 calc_dimension.h |
| AC-5.2 | US-5 | R-18 | 代码审查 calc_length.h:53-54 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 单位 PX/NONE | ConvertToPx 返回 value | `dimension.cpp:37-47` | AC-1.1 |
| R-2 | 行为 | 单位 VP | ConvertToPx 返回 value * dipScale | `dimension.cpp:58-65` | AC-1.2 |
| R-3 | 行为 | 单位 FP | ConvertToPx 返回 value * fpScale * vpScale | `dimension.cpp:67-74` | AC-1.3 |
| R-4 | 行为 | 单位 LPX | ConvertToPx 返回 value * lpxScale | `dimension.cpp:76-83` | AC-1.4 |
| R-5 | 边界 | 单位 PERCENT | NormalizeToPx 返回 value * parentLength | 需非负 parentLength `dimension.h:450-471` | AC-1.5 |
| R-6 | 边界 | dipScale 计算 | dipScale = density / viewScale | `pipeline_base.cpp:552-561` | AC-1.6 |
| R-7 | 边界 | Dimension() 默认 | value=0.0, unit=PX | `dimension.h:94` | AC-2.1 |
| R-8 | 边界 | FromString 空字符串/未知单位 | 默认单位 FP | `dimension.h:428` | AC-2.2 |
| R-9 | 行为 | FromString "50%" | 值除以 100 存储 | `dimension.h:443` | AC-2.3 |
| R-10 | 行为 | ParseJsDimension 收到 number | 构造 CalcDimension(num, defaultUnit) | `js_view_abstract.cpp:6742-6744` | AC-3.1 |
| R-11 | 行为 | ParseJsDimension 收到 string | StringUtils::StringToCalcDimension | `js_view_abstract.cpp:6746-6748` | AC-3.2 |
| R-12 | 行为 | ParseJsDimension 收到 Resource | CompleteResourceObjectInner 解析 $r | `js_view_abstract.cpp:6757-6780` | AC-3.3 |
| R-13 | 边界 | 资源类型 FLOAT | 返回原始像素值 | `js_view_abstract.cpp:6643` | AC-3.4 |
| R-14 | 边界 | fontScale 默认 | fontScale_=1.0f | `pipeline_base.h:1700` | AC-4.1 |
| R-15 | 边界 | maxAppFontScale 默认 | maxAppFontScale_=INT32_MAX | `pipeline_base.h:1828` | AC-4.2 |
| R-16 | 行为 | 字体缩放生效 | std::clamp(fontScale, 0.0f, maxAppFontScale_) | `dimension.cpp` | AC-4.3 |
| R-17 | 行为 | CalcDimension 构造 | calcvalue_ 存储表达式，unit=CALC | `calc_dimension.h` | AC-5.1 |
| R-18 | 行为 | CalcLength::NormalizeToPx | 支持 RPN 表达式向量 | `calc_length.h:53-54` | AC-5.2 |
| R-19 | 异常 | operator/ 除数为 0 | 返回默认 Dimension{} | NEAR_ZERO `dimension.h:277-279` | AC-2.4 |
| R-20 | 异常 | ConvertTo* 时 pipeline 为 null | 返回 0.0 | `dimension.cpp` 各 ConvertTo* | AC-1.1 |
| R-21 | 行为 | operator== | NearEqual 比较 value + unit 相等 | `dimension.h:150-158` | AC-2.1 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 单位换算 (AC-1.1~1.6) | 代码审查 | PX/VP/FP/LPX/PERCENT 公式；dipScale 计算 |
| VM-2 | US-2 Dimension 构造 (AC-2.1~2.4) | 代码审查 | 默认值；FromString；异常除零 |
| VM-3 | US-3 资源解析 (AC-3.1~3.4) | 代码审查 | number/string/Resource 分支；FLOAT 像素 |
| VM-4 | US-4 字体缩放 (AC-4.1~4.3) | 代码审查 | fontScale/maxAppFontScale 默认；clamp |
| VM-5 | US-5 CalcDimension (AC-5.1~5.2) | 代码审查 | CALC 表达式；RPN |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/base/geometry/dimension.cpp:37-47` |
| AC-1.2 | 代码审查 | `frameworks/base/geometry/dimension.cpp:58-65` |
| AC-1.3 | 代码审查 | `frameworks/base/geometry/dimension.cpp:67-74` |
| AC-1.4 | 代码审查 | `frameworks/base/geometry/dimension.cpp:76-83` |
| AC-1.5 | 代码审查 | `interfaces/inner_api/ace_kit/include/ui/base/geometry/dimension.h:450-471` |
| AC-1.6 | 代码审查 | `frameworks/core/pipeline/pipeline_base.cpp:552-561` |
| AC-2.1 | 代码审查 | `interfaces/inner_api/ace_kit/include/ui/base/geometry/dimension.h:94` |
| AC-2.2 | 代码审查 | `interfaces/inner_api/ace_kit/include/ui/base/geometry/dimension.h:428` |
| AC-2.3 | 代码审查 | `interfaces/inner_api/ace_kit/include/ui/base/geometry/dimension.h:443` |
| AC-2.4 | 代码审查 | `interfaces/inner_api/ace_kit/include/ui/base/geometry/dimension.h:277-279` |
| AC-3.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:6742-6744` |
| AC-3.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:6746-6748` |
| AC-3.3 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:6757-6780` |
| AC-3.4 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:6643` |
| AC-4.1 | 代码审查 | `frameworks/core/pipeline/pipeline_base.h:1700` |
| AC-4.2 | 代码审查 | `frameworks/core/pipeline/pipeline_base.h:1828` |
| AC-4.3 | 代码审查 | `frameworks/base/geometry/dimension.cpp` |
| AC-5.1 | 代码审查 | `interfaces/inner_api/ace_kit/include/ui/base/geometry/calc_dimension.h` |
| AC-5.2 | 代码审查 | `interfaces/inner_api/ace_kit/include/ui/properties/ng/calc_length.h:53-54` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/units.d.ts`

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `type Length = string \| number \| Resource` | Public | — | Length | N/A | 通用长度类型(@since 7) | AC-2.1~2.4 |
| `type VP = \`${number}vp\` \| number` | Public | — | VP | N/A | vp 单位(@since 10) | AC-1.2 |
| `type FP = \`${number}fp\`` | Public | — | FP | N/A | fp 单位(@since 10) | AC-1.3 |
| `type PX = \`${number}px\`` | Public | — | PX | N/A | px 单位(@since 10) | AC-1.1 |
| `type LPX = \`${number}lpx\`` | Public | — | LPX | N/A | lpx 单位(@since 10) | AC-1.4 |
| `type Dimension = PX \| VP \| FP \| LPX \| Percentage \| Resource` | Public | — | Dimension | N/A | 联合类型(@since 10) | AC-1.1~1.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无变更/废弃 API | — |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | Length 类型(number\|string\|Resource) | — | — |
| API 9 | form 支持 | — | — |
| API 10 | PX/VP/FP/LPX/Percentage/Dimension 模板字面量类型引入；crossplatform | 类型更严格 | 旧版本 string 宽松 |
| API 11 | atomicservice 支持 | — | — |
| API 18 | crossplatform 扩展 | — | — |
| API 23 | form 支持 PX/VP/FP/LPX | — | — |

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| DimensionUnit 枚举 | INVALID/NONE/PX/VP/FP/PERCENT/LPX/AUTO/CALC | AC-1.1~1.5 |
| Pipeline 缩放参数 | dipScale/fontScale/viewScale/lpxScale 集中管理 | AC-1.6, AC-4.1~4.3 |
| PERCENT 依赖 parentLength | NormalizeToPx 需显式传入父容器尺寸 | AC-1.5 |
| 字体缩放钳位 | clamp(fontScale, 0, maxAppFontScale) | AC-4.3 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 换算 O(1) | 代码审查 | dimension.cpp |
| 可调试性 | ToString 输出 "100vp"/"50%" 等 | 代码审查 | dimension.h:392-412 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | dipScale 随设备密度 | — | — |
| 平板 | 无差异 | dipScale 随设备密度 | — | — |
| 折叠屏 | 无差异 | dipScale 随设备密度 | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 无差异 | — |
| 大字体 | 是 | FP 受 fontScale 影响，钳位到 maxAppFontScale | AC-1.3, AC-4.3 |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 7/10 类型差异 | 兼容性声明 |
| 生态兼容 | 否 | 无差异 | — |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `interfaces/inner_api/ace_kit/include/ui/base/geometry/dimension.h` | Dimension 类与 DimensionUnit 枚举 |
| `frameworks/base/geometry/dimension.cpp` | 单位换算实现 |
| `interfaces/inner_api/ace_kit/include/ui/base/geometry/calc_dimension.h` | CalcDimension(CALC) |
| `interfaces/inner_api/ace_kit/include/ui/properties/ng/calc_length.h` | NG::CalcLength |
| `frameworks/core/pipeline/pipeline_base.h/.cpp` | dipScale/fontScale/viewScale |
| `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | ParseJsDimension 系列 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `interface/sdk-js/api/@internal/component/ets/units.d.ts` | Length/VP/FP/PX/LPX/Percentage/Dimension 类型定义 |
