# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 命令式 Popup API（openPopup / updatePopup / closePopup + PopupCommonOptions + ComponentContent + TargetInfo） |
| 特性编号 | Func-05-06-11-Feat-02 |
| FuncID | 05-06-11 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 18 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 18 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 命令式 API: openPopup / updatePopup / closePopup | @since 18 |
| ADDED | PopupCommonOptions 类型 | @since 18 |
| ADDED | PopupMaskType 枚举 | @since 18 |
| ADDED | PopupStateChangeCallback 类型 | @since 18 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/06-popup-components/11-popup/design.md`
- **KB 路由**: `docs/kb/components/overlay/bind_popup.md`
- **SDK 类型定义**:
  - Dynamic (命令式): `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 命令式 API（openPopup / updatePopup / closePopup）

**角色**: 应用开发者
**期望**: 我想要通过命令式 API 编程式地显示和管理气泡
**价值**: 以便在非声明式场景下控制气泡生命周期

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `UIContext.PromptAction.openPopup(options, target)` THEN 创建气泡并返回 Promise\<number\>（componentId）（@since 18） | 正常 |
| AC-1.2 | WHEN 调用 `updatePopup(componentId, options)` THEN 更新指定气泡的属性（@since 18） | 正常 |
| AC-1.3 | WHEN 调用 `closePopup(componentId)` THEN 关闭指定气泡（@since 18） | 正常 |
| AC-1.4 | WHEN openPopup 使用 ComponentContent THEN 气泡内容由 ComponentContent 驱动渲染 | 正常 |
| AC-1.5 | WHEN closePopup 传入不存在的 componentId THEN 不执行操作 | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1, R-2, R-3 | TASK-BIND-POPUP-02 | UT | 命令式 API 测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `popup_base_pattern.cpp` | openPopup 创建 ComponentContent + BubblePattern 节点，返回 componentId | @since 18 | AC-1.1 |
| R-2 | 行为 | `popup_base_pattern.cpp` | updatePopup 更新属性，closePopup 关闭指定气泡 | — | AC-1.2, AC-1.3 |
| R-3 | 异常 | `overlay_manager.cpp` | closePopup 传入不存在的 componentId，popupMap_.find 返回 end，不执行操作 | — | AC-1.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | 命令式 API 生命周期 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `UIContext.PromptAction.openPopup(options, target)` | Public | PopupCommonOptions, TargetInfo | Promise\<number\> | N/A | 命令式显示气泡 | AC-1.1, AC-1.4 | @since 18 |
| `UIContext.PromptAction.updatePopup(componentId, options)` | Public | number, PopupCommonOptions | void | N/A | 命令式更新气泡 | AC-1.2 | @since 18 |
| `UIContext.PromptAction.closePopup(componentId)` | Public | number | void | N/A | 命令式关闭气泡 | AC-1.3, AC-1.5 | @since 18 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| N/A | N/A | N/A | 本特性均为新增 API，无变更/废弃 | N/A |

> SDK 声明见 `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`。

## 接口规格

### 接口定义

**openPopup**

| 属性 | 值 |
|------|-----|
| 函数签名 | `openPopup(options: PopupCommonOptions, target: TargetInfo): Promise<number>` |
| 返回值 | `Promise<number>` — resolve 为 componentId |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options | PopupCommonOptions | 是 | — | 气泡属性集合（包含 placement / mask / autoCancel / popupColor 等声明式等价属性） |
| target | TargetInfo | 是 | — | 目标节点信息（componentId 或坐标） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | openPopup(options, target) | 创建气泡并返回 componentId | AC-1.1 |
| 2 | openPopup 使用 ComponentContent | 气泡内容由 ComponentContent 驱动渲染 | AC-1.4 |

---

**updatePopup**

| 属性 | 值 |
|------|-----|
| 函数签名 | `updatePopup(componentId: number, options: PopupCommonOptions): void` |
| 返回值 | `void` — 无返回值 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| componentId | number | 是 | — | openPopup 返回的气泡 ID |
| options | PopupCommonOptions | 是 | — | 需更新的气泡属性集合 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | updatePopup(validComponentId, options) | 更新指定气泡的属性 | AC-1.2 |

---

**closePopup**

| 属性 | 值 |
|------|-----|
| 函数签名 | `closePopup(componentId: number): void` |
| 返回值 | `void` — 无返回值 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.3, AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| componentId | number | 是 | — | openPopup 返回的气泡 ID；不存在时不执行操作 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | closePopup(validComponentId) | 关闭指定气泡 | AC-1.3 |
| 2 | closePopup(invalidComponentId) | 不执行操作 | AC-1.5 |

## 兼容性声明

- **已有 API 行为变更:** 是
  - API 18: 引入命令式 `openPopup` / `updatePopup` / `closePopup` 和 `PopupCommonOptions`
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 18
- **API 版本号策略:** openPopup / updatePopup / closePopup / PopupCommonOptions / PopupMaskType / PopupStateChangeCallback @since 18

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双 Pattern 架构 | PopupBasePattern 为命令式 API 提供基础，BubblePattern 继承共用渲染层 | AC-1.1 |
| ComponentContent 驱动 | 命令式 API 通过 ComponentContent 驱动气泡内容渲染，与声明式 CustomBuilder 等价 | AC-1.4 |
| popupMap_ 生命周期管理 | OverlayManager 通过 popupMap_ 管理命令式气泡的创建/更新/关闭生命周期 | AC-1.1 ~ AC-1.5 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 内存 | closePopup 后 popupMap_ 正确清理，无气泡节点泄漏 | UT | popupMap_ size |
| 安全 | 无安全相关接口 | N/A | — |
| 问题定位 | hilog 标签 ACE_OVERLAY / ACE_DIALOG 覆盖关键路径 | 代码审查 | — |
| 自动化维测 | DumpTree 支持命令式气泡节点树导出 | UT + Dump | 节点树 Dump |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 命令式 API 不涉及无障碍特性扩展，复用 bindPopup 的无障碍能力 | — |
| 大字体 | 否 | 命令式 API 不涉及字体缩放，气泡内容跟随 ComponentContent | — |
| 深色模式 | 否 | 命令式 API 不涉及颜色主题，复用 PopupCommonOptions 的颜色属性 | — |
| 多窗口/分屏 | 否 | 命令式 API 不涉及窗口管理，复用 bindPopup 的 showInSubWindow | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 18 引入命令式 openPopup / updatePopup / closePopup 和 PopupCommonOptions | AC-1.1 |
| 生态兼容 | 否 | 命令式 API 为 ArkTS 层接口，不涉及 C API | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "PopupBasePattern 命令式 openPopup/updatePopup/closePopup 实现"
  - repo: "openharmony/ace_engine"
    query: "OverlayManager ShowPopup/HidePopup popupMap_ 管理和命令式 API 生命周期"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`
- KB 路由: `docs/kb/components/overlay/bind_popup.md`
- 源码入口: `frameworks/core/components_ng/pattern/overlay/popup_base_pattern.cpp`, `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp`
