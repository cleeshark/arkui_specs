# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | GestureStyle 手势 |
| 特性编号 | Func-05-09-10-Feat-06 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`10-attributed-string/design.md`
- 源码定位：`span_object.h:280`（GestureSpan）、`js_span_object.cpp`（JSGestureSpan→"GestureStyle"）、`styled_string.d.ts:746/769`

## 用户故事

### US-1: 手势
作为开发者，我希望经 `GestureStyle` 为区间附加 onClick/onLongPress 手势。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `new GestureStyle({onClick?, onLongPress?})`（@since 12）THEN 创建 GestureSpan | 正常 |
| AC-1.2 | WHEN 点击区间 THEN span 级命中测试触发 onClick | 正常 |
| AC-1.3 | WHEN 长按区间 THEN 触发 onLongPress | 正常 |
| AC-1.4 | WHEN onClick/onLongPress 均未设 THEN 不响应手势 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-AS-06 | 单测 | span_object.h:280 |
| AC-1.2 | R-2 | TASK-AS-06 | 单测 | styled_string.d.ts:769 |
| AC-1.3 | R-2 | TASK-AS-06 | 单测 | — |
| AC-1.4 | R-3 | TASK-AS-06 | 单测 | — |

## 觅则定义

| 觅则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | GestureStyle({onClick?,onLongPress?}) | 创建 GestureSpan（@since 12） | 均可选 | AC-1.1 |
| R-2 | 行为 | 点击/长按区间 | span 级命中测试触发回调 | — | AC-1.2,1.3 |
| R-3 | 边界 | onClick/onLongPress 均未设 | 不响应手势 | — | AC-1.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 创建 | 单测 | GestureSpan |
| VM-2 | R-2 命中 | 单测 | span 级命中 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class GestureStyle` + `GestureStyleInterface` | Public | onClick?/onLongPress? | 实例 | 无 | 手势 @since 12 | AC-1.1 |

## 接口规格

### 接口定义

**GestureStyle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `class GestureStyle { onClick?: Callback<ClickEvent>; onLongPress?: Callback<GestureEvent> }` |
| 返回值 | 实例 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| onClick | Callback<ClickEvent> | 否 | — | 均未设触发 R-3 |
| onLongPress | Callback<GestureEvent> | 否 | — | 同上 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 点击 | onClick | AC-1.2 |
| 2 | 长按 | onLongPress | AC-1.3 |
| 3 | 均未设 | 不响应 | AC-1.4 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** GestureStyle @since 12
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SpanType=GESTURE=100 | span_object.h:40 | AC-1.1 |
| span 级命中测试 | 区间内触发 | AC-1.2 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 命中测试无明显开销 | 性能测试 | — |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 触摸设备 | 主交互 | — | — | — |
| 鼠标设备 | 点击为主 | — | — | — |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 手势区间需无障碍可触达 | AC-1.2 |

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
    query: "GestureSpan span 级命中测试"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/styled_string.d.ts`
