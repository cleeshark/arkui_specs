# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Hyperlink 拖拽/响应区域/状态视觉/导航 |
| 特性编号 | Func-05-09-09-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 7–11 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`09-hyperlink/design.md`
- 源码定位：`hyperlink_pattern.cpp:91–196/222–349`（EnableDrag/LinkToAddress/InitTouchEvent/OnHoverEvent/OnMouseEvent）、`hyperlink_model_ng.cpp:99–153`（SetDraggable/SetResponseRegion）、`hyperlink_theme.h:59–67`

## 用户故事

### US-1: 拖拽
作为开发者，我希望经 `draggable(true)` 支持拖拽链接到其他应用。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `draggable(true)` THEN EnableDrag 生成 DragDropInfo{url,title} + Udmf link record | 正常 |
| AC-1.2 | WHEN DefaultSupportDrag() THEN 返回 true（主题默认 draggable_=false） | 边界 |
| AC-1.3 | WHEN C-API `setHyperlinkDraggable`/`resetHyperlinkDraggable` THEN 下发/重置拖拽 | 正常 |

### US-2: 响应区域
作为开发者，我希望经 `responseRegion` 自定义点击响应区域。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `responseRegion(regions)`（modifier/C-API）THEN 设置响应区域 | 正常 |
| AC-2.2 | WHEN 未设 THEN 响应区域为整个 bounds | 边界 |
| AC-2.3 | WHEN C-API `setHyperlinkResponseRegion`/`setHyperlinkResponseRegionEnabled` THEN 下发/启用 | 正常 |

### US-3: 状态视觉
作为开发者，我希望链接随 hover/press/visited/disabled 呈现状态视觉。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 鼠标 hover THEN HAND_POINTING 光标 + UNDERLINE | 正常 |
| AC-3.2 | WHEN 按下 THEN textTouchedColor(0x19182431) + UNDERLINE | 正常 |
| AC-3.3 | WHEN 访问后 THEN textLinkedColor(0x66182431) + 访问装饰 | 正常 |
| AC-3.4 | WHEN disabled THEN opacity 混合 textDisabledColor | 正常 |

### US-4: 导航
作为开发者，我希望点击链接经 LinkToAddress 拉起能力。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 点击（非 preventDefault）THEN LinkToAddress→pipeline->HyperlinkStartAbility(address) | 正常 |
| AC-4.2 | WHEN isTouchPreventDefault_/IsPreventDefault() THEN 拦截不导航 | 边界 |
| AC-4.3 | WHEN PREVIEW 模式 THEN HyperlinkStartAbility 被跳过 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-HL-02 | 单测 | hyperlink_pattern.cpp:91 |
| AC-1.2 | R-2 | TASK-HL-02 | 单测 | hyperlink_pattern.h:37 |
| AC-1.3 | R-1 | TASK-HL-02 | C-API 单测 | hyperlink_dynamic_modifier.cpp |
| AC-2.1 | R-3 | TASK-HL-02 | 单测 | hyperlink_model_ng.cpp:129 |
| AC-2.2 | R-4 | TASK-HL-02 | 单测 | — |
| AC-2.3 | R-3 | TASK-HL-02 | C-API 单测 | hyperlink_dynamic_modifier.cpp |
| AC-3.1 | R-5 | TASK-HL-02 | 单测 | hyperlink_pattern.cpp:320 |
| AC-3.2 | R-5 | TASK-HL-02 | 单测 | hyperlink_pattern.cpp:240 |
| AC-3.3 | R-5 | TASK-HL-02 | 单测 | hyperlink_pattern.cpp:170 |
| AC-3.4 | R-6 | TASK-HL-02 | 单测 | hyperlink_pattern.cpp:125 |
| AC-4.1 | R-7 | TASK-HL-02 | 单测 | hyperlink_pattern.cpp:170 |
| AC-4.2 | R-8 | TASK-HL-02 | 单测 | hyperlink_pattern.cpp:281 |
| AC-4.3 | R-9 | TASK-HL-02 | 单测 | hyperlink_pattern.cpp:170 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | draggable(true)/setHyperlinkDraggable | EnableDrag 生成 Udmf link record {url,title} | — | AC-1.1,1.3 |
| R-2 | 边界 | DefaultSupportDrag() | 返回 true，主题默认 draggable_=false | — | AC-1.2 |
| R-3 | 行为 | responseRegion/setHyperlinkResponseRegion | 设置响应区域（3 重载） | — | AC-2.1,2.3 |
| R-4 | 边界 | 未设 responseRegion | 响应区域为整个 bounds | — | AC-2.2 |
| R-5 | 行为 | hover/press/visited 状态 | HAND_POINTING 光标+UNDERLINE；textTouchedColor/textLinkedColor | — | AC-3.1..3.3 |
| R-6 | 行为 | disabled | opacity 混合 textDisabledColor | — | AC-3.4 |
| R-7 | 行为 | 点击（非 preventDefault） | LinkToAddress→HyperlinkStartAbility(address) | — | AC-4.1 |
| R-8 | 边界 | isTouchPreventDefault_/IsPreventDefault() | 拦截不导航 | — | AC-4.2 |
| R-9 | 边界 | PREVIEW 模式 | HyperlinkStartAbility 跳过 | — | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 拖拽 | 单测 | Udmf record |
| VM-2 | R-3 响应区域 | 单测+C-API | 3 重载 |
| VM-3 | R-5 状态视觉 | 单测 | hover/press/visited |
| VM-4 | R-7 导航 | 单测 | HyperlinkStartAbility |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `draggable(value)` | Public（通用属性，Hyperlink 重导出） | boolean | this | 无 | 拖拽 @since 7/11 | AC-1.1 |
| `responseRegion(region)` | Public（modifier/C-API） | Array<Rectangle>\|Rectangle | this | 无 | 响应区域 | AC-2.1 |
| C-API `setHyperlinkDraggable`/`resetHyperlinkDraggable`/`setHyperlinkResponseRegion`/`resetHyperlinkResponseRegion`/`setHyperlinkResponseRegionEnabled` | System | KNode, ... | void | 无 | C-API 对应 | AC-1.3,2.3 |

## 接口规格

### 接口定义

**draggable(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `draggable(value: boolean): HyperlinkAttribute` |
| 返回值 | `HyperlinkAttribute` |
| 开放范围 | Public（通用属性复用） |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | false（主题默认） | true 启用拖拽 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | draggable(true) | EnableDrag + Udmf record | AC-1.1 |
| 2 | hover | 光标+UNDERLINE | AC-3.1 |
| 3 | 点击非拦截 | 导航 | AC-4.1 |
| 4 | preventDefault | 拦截 | AC-4.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** draggable/responseRegion 为通用属性 @since 7/11
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| HyperlinkPattern 继承 TextPattern | 状态视觉在 Pattern 分支 | AC-3.1..3.4 |
| pipeline->HyperlinkStartAbility | 导航统一入口 | AC-4.1 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 状态切换流畅 | 帧率测试 | — |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板 | 无差异 | — | — | — |
| 触摸设备 | hover 不可用 | press 状态为主 | 单测 | hyperlink_pattern.cpp |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 导航需无障碍触发 | AC-4.1 |

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
    query: "Hyperlink EnableDrag/Udmf/状态视觉/LinkToAddress"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/hyperlink.d.ts`
