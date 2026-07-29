# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Hyperlink 链接配置与颜色样式 |
| 特性编号 | Func-05-09-09-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 7–18 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`09-hyperlink/design.md`
- 源码定位：`hyperlink_model_ng.cpp:23/60–97`（Create/SetColor/SetTextStyle）、`hyperlink_layout_property.h:66/89–90`（Color/Address + API 18 色分支）、`hyperlink_theme.h`

## 用户故事

### US-1: 链接构造
作为开发者，我希望经 `Hyperlink(address, content)` 构造超链接。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `Hyperlink(address, content?)` THEN 创建 HYPERLINK_ETS_TAG 节点 + HyperlinkPattern + SetTextStyle @since 7/11 | 正常 |
| AC-1.2 | WHEN content 为空 THEN 兜底用 address 作为显示文本 | 边界 |
| AC-1.3 | WHEN C-API `setHyperlinkOptions(address, content?)` THEN 设置 Address/Content | 正常 |

### US-2: 颜色
作为开发者，我希望经 `color(value)` 设置链接颜色。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `color(value)`（@since 7/11）THEN 写入 TextColor/Color/ForegroundColor（MEASURE） | 正常 |
| AC-2.2 | WHEN 未设 color 且 API≥18 THEN 主题派生 HyperlinkTheme::GetTextColor()（0xff007dff 蓝） | 正常 |
| AC-2.3 | WHEN 未设 color 且 API<18 THEN 硬编码 Color::BLUE | 边界 |
| AC-2.4 | WHEN color 用 Resource THEN 资源态注册 | 正常 |

### US-3: 继承 Text 样式
作为开发者，我希望复用 Text 的 fontSize/fontWeight/fontFamily/textDecoration 等样式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置继承 Text 样式 THEN 经 HyperlinkLayoutProperty（继承 TextLayoutProperty）生效 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-HL-01 | 单测 | hyperlink_model_ng.cpp:23 |
| AC-1.2 | R-2 | TASK-HL-01 | 单测 | hyperlink_model_ng.cpp:67 |
| AC-1.3 | R-1 | TASK-HL-01 | C-API 单测 | arkoala_api.h:25802 |
| AC-2.1 | R-3 | TASK-HL-01 | 单测 | hyperlink_model_ng.cpp:60 |
| AC-2.2 | R-4 | TASK-HL-01 | 单测 | hyperlink_layout_property.h:66 |
| AC-2.3 | R-4 | TASK-HL-01 | 单测 | hyperlink_layout_property.h:66 |
| AC-2.4 | R-3 | TASK-HL-01 | 单测 | hyperlink_dynamic_modifier.cpp 资源路径 |
| AC-3.1 | R-5 | TASK-HL-01 | 单测 | hyperlink_layout_property.h:30 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | 构造 Hyperlink(address, content?) 或 setHyperlinkOptions | 创建节点 + 写 Address/Content（@since 7/11） | address string\|Resource | AC-1.1,1.3 |
| R-2 | 边界 | content 为空 | 兜底用 address 作显示文本 | — | AC-1.2 |
| R-3 | 行为 | color(value) | 写 TextColor/Color/ForegroundColor（MEASURE）；Resource 注册 | value Color/number/string/Resource | AC-2.1,2.4 |
| R-4 | 行为 | 未设 color | API≥18 主题派生 0xff007dff；API<18 硬编码 BLUE | — | AC-2.2,2.3 |
| R-5 | 行为 | 继承 Text 样式 | 经继承 TextLayoutProperty 生效 | — | AC-3.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 构造 | 单测 | tag + Pattern |
| VM-2 | R-4 默认色分支 | 单测 | API 18 分支 |
| VM-3 | R-3 color | 单测 | 三色字段 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `Hyperlink(address, content?)` | Public | string\|Resource, string\|Resource? | HyperlinkAttribute | 无 | 构造 @since 7/11 | AC-1.1 |
| `color(value)` | Public | Color\|number\|string\|Resource | this | 无 | 颜色 @since 7/11 | AC-2.1 |
| 静态 `setHyperlinkOptions(address, content?)` | Public | string\|Resource, string\|Resource? | this | 无 | 设置链接选项 | AC-1.3 |
| C-API `setHyperlinkColor`/`resetHyperlinkColor`/`setHyperlinkOptions` | System | KNode, color/address | void | 无 | 颜色/选项下发 | AC-2.1,1.3 |

## 接口规格

### 接口定义

**Hyperlink(address, content?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Hyperlink(address: string \| Resource, content?: string \| Resource): HyperlinkAttribute` |
| 返回值 | `HyperlinkAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| address | string\|Resource | 是 | — | URL/地址；空触发 R-2 兜底 |
| content | string\|Resource | 否 | 兜底 address | 显示文本 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 全参 | 创建节点 | AC-1.1 |
| 2 | content 空 | 兜底 address | AC-1.2 |
| 3 | 未设 color API≥18 | 主题蓝 | AC-2.2 |
| 4 | 未设 color API<18 | 硬编码 BLUE | AC-2.3 |

## 兼容性声明
- **已有 API 行为变更:** 否（但 API 18 默认色派生分支为行为变化，标兼容性）
- **最低支持版本:** constructor/color @since 7（atomicservice @since 11）
- **API 版本号策略:** 全量 @since 标注；API 18 默认色分支标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| HyperlinkLayoutProperty 继承 TextLayoutProperty | 复用 Text 排版 | AC-3.1 |
| Color MEASURE | 颜色变更重测 | AC-2.1 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 构造/颜色可单测 | 单测 | hyperlink_model_ng.cpp |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 深色模式 | 是 | 颜色随主题（API 18+） | AC-2.2 |

## Spec 自审清单
- [x] 无占位符
- [x] AC 用 WHEN/THEN
- [x] 范围明确
- [x] 无模糊表述
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项检查

## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Hyperlink 构造/默认色 API 18 分支"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/hyperlink.d.ts`
