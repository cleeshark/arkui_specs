# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Hyperlink 键盘无障碍与多前端 C-API 桥 |
| 特性编号 | Func-05-09-09-Feat-03 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 7–11 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`09-hyperlink/design.md`
- 源码定位：`hyperlink_pattern.h:42–53`（GetFocusPattern/UpdatePropertyImpl/OnInjectionEvent）、`hyperlink_pattern.cpp:298–318/420–433`（OnKeyEvent/OnInjectionEvent）、`hyperlink_layout_property.h:55–87`（ToJsonValue/ToTreeJson）、`arkoala_api.h:25799`、`hyperlink_dynamic_modifier.cpp:212–266`

## 用户故事

### US-1: 键盘激活
作为开发者，我希望经键盘 KEY_SPACE/KEY_ENTER 激活链接。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 按下 KEY_SPACE 或 KEY_ENTER THEN 激活链接（等价点击→LinkToAddress） | 正常 |
| AC-1.2 | WHEN 链接获焦 THEN GetFocusPattern 返回 {NODE, true, OUTER_BORDER} | 正常 |

### US-2: 注入事件
作为开发者/测试，我希望经 OnInjectionEvent 注入点击。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `OnInjectionEvent({"cmd":"click"})` THEN 触发点击→LinkToAddress | 正常 |

### US-3: 多前端 C-API 桥
作为开发者，我希望在动态/静态 ArkTS、CJ、C-API 多前端配置 Hyperlink。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 动态 ArkTS 经 ArkHyperlink.ts/hyperlink_modifier.ts THEN 下发到 HyperlinkModelNG | 正常 |
| AC-3.2 | WHEN 静态 ArkTS 经 hyperlink.ets 生成的 modifier THEN 走静态路径 | 正常 |
| AC-3.3 | WHEN C-API 经 GENERATED_ArkUIHyperlinkModifier（construct/setHyperlinkOptions/setColor）+ 动态 ArkUIHyperlinkModifier（color/draggable/responseRegion/createFrameNode/pop）THEN 下发 | 正常 |
| AC-3.4 | WHEN CJ 经 CJUIHyperlinkModifier（color/draggable）THEN 下发 | 正常 |

### US-4: 序列化
作为开发者/工具，我希望经 ToJsonValue/ToTreeJson 序列化 Hyperlink。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN ToJsonValue THEN 输出 content/color/address（color 含 API 18 分支） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-HL-03 | 单测 | hyperlink_pattern.cpp:298 |
| AC-1.2 | R-2 | TASK-HL-03 | 单测 | hyperlink_pattern.h:42 |
| AC-2.1 | R-3 | TASK-HL-03 | 单测 | hyperlink_pattern.cpp:420 |
| AC-3.1 | R-4 | TASK-HL-03 | 单测 | ArkHyperlink.ts |
| AC-3.2 | R-4 | TASK-HL-03 | 单测 | hyperlink.ets |
| AC-3.3 | R-4 | TASK-HL-03 | C-API 单测 | arkoala_api.h:25799 |
| AC-3.4 | R-4 | TASK-HL-03 | 单测 | hyperlink_dynamic_modifier.cpp:254 |
| AC-4.1 | R-5 | TASK-HL-03 | 单测 | hyperlink_layout_property.h:55 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | KEY_SPACE/KEY_ENTER | 激活链接→LinkToAddress | — | AC-1.1 |
| R-2 | 行为 | 获焦 | GetFocusPattern={NODE,true,OUTER_BORDER} | — | AC-1.2 |
| R-3 | 行为 | OnInjectionEvent({"cmd":"click"}) | 触发点击→LinkToAddress | — | AC-2.1 |
| R-4 | 行为 | 多前端配置 | 统一下发到 HyperlinkModelNG | 路径差异在 bridge | AC-3.1..3.4 |
| R-5 | 行为 | ToJsonValue/ToTreeJson | 序列化 content/color/address（API 18 色分支） | — | AC-4.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 键盘激活 | 单测 | KEY_SPACE/ENTER |
| VM-2 | R-3 注入 | 单测 | cmd click |
| VM-3 | R-4 多前端 | 单测+C-API | 统一下发 |
| VM-4 | R-5 序列化 | 单测 | API 18 分支 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| C-API `GENERATED_ArkUIHyperlinkModifier`（construct/setHyperlinkOptions/setColor） | System | KNode, ... | ptr/void | 无 | 静态 C-API modifier | AC-3.3 |
| C-API 动态 `ArkUIHyperlinkModifier`（create/setHyperlinkColor/reset/setHyperlinkDraggable/reset/setHyperlinkResponseRegion/reset/setHyperlinkResponseRegionEnabled/createHyperlinkFrameNode/pop） | System | KNode, ... | void | 无 | 动态 C-API modifier | AC-3.3 |
| CJ `CJUIHyperlinkModifier`（color/draggable） | System | KNode, ... | void | 无 | CJ modifier | AC-3.4 |
| OnInjectionEvent({"cmd":"click"}) | InnerApi | command | bool | 无 | 测试注入 | AC-2.1 |

## 接口规格

### 接口定义

**OnInjectionEvent(command)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool OnInjectionEvent(const std::string& command)` |
| 返回值 | `bool` — 是否处理 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| command | string(JSON) | 是 | — | {"cmd":"click"} |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | cmd=click | 触发点击 | AC-2.1 |
| 2 | 键盘 ENTER | 激活 | AC-1.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** Hyperlink 组件 @since 7/11；C-API modifier @since 11/12
- **API 版本号策略:** 全量 @since 标注；无独立 C-API 节点类型，仅 modifier（记风险）

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 无独立 NODE_HYPERLINK | 仅 modifier 模式 | AC-3.3 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 注入/键盘可单测 | 单测 | hyperlink_pattern.cpp |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板 | 键盘激活为主 | — | — | — |
| 触摸设备 | 点击为主 | — | — | — |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 键盘激活+焦点框 | AC-1.1,1.2 |

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
    query: "Hyperlink 键盘激活/注入/多前端 modifier 桥"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/hyperlink.d.ts`
