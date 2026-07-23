# 特性规格

> Func-05-13-01-Feat-08 无障碍 provider：固化 OH_NativeXComponent_GetNativeAccessibilityProvider（@since 13）、OH_ArkUI_AccessibilityProvider_Create/Dispose（@since 20）、子树注册/注销/设置、session adapter、V2 provider map 追踪，及与 legacy NativeXComponent 路径互斥的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍 provider |
| 特性编号 | Func-05-13-01-Feat-08 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | OH_NativeXComponent_GetNativeAccessibilityProvider @since 13 / OH_ArkUI_AccessibilityProvider_Create @since 20 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | legacy provider 规格 | GetNativeAccessibilityProvider（since 13，返回 impl 持有 provider） |
| ADDED | V2 provider 规格 | OH_ArkUI_AccessibilityProvider_Create/Dispose（since 20，幂等，静态 map 追踪） |
| ADDED | 子树规格 | Register/Deregister/SetChildTree、session adapter |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/13-platform-components/01-xcomponent/design.md` | Baselined |

---

## 用户故事

### US-1: 获取 legacy 无障碍 provider（since 13）

**作为** NDK 开发者,
**我想要** 通过 OH_NativeXComponent 获取无障碍 provider,
**以便** 在 native 层接入无障碍。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `OH_NativeXComponent_GetNativeAccessibilityProvider(component, &handle)` 且 component/impl 非空 THEN *handle 指向 impl 持有的 provider，返回 SUCCESS(0) | 正常 |
| AC-1.2 | WHEN component 或 handle null 或 impl null THEN 返回 BAD_PARAMETER(-2) | 异常 |

### US-2: 创建/销毁 V2 provider（since 20）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `OH_ArkUI_AccessibilityProvider_Create(node)` 且未取 legacy native THEN 创建 provider、注册静态 map、ResetAndInitializeNodeHandleAccessibility，返回指针 | 正常 |
| AC-2.2 | WHEN 已存在 arkuiAccessibilityProvider_ THEN 返回缓存指针（幂等） | 边界 |
| AC-2.3 | WHEN 已取 legacy NativeXComponent（hasGotNativeXComponent_） THEN 返回 nullptr（互斥） | 边界 |
| AC-2.4 | WHEN `Dispose(provider)` 且 provider 匹配 THEN 从 map 移除、UninitializeAccessibility、delete；不匹配 no-op | 正常 |

### US-3: 子树注册/注销

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN OnRegister(windowId, treeId) THEN 创建 accessibilityProvider_、设 InnerProvider、建 sessionAdapter、RegisterInteractionOperationAsChildTree | 正常 |
| AC-3.2 | WHEN OnDeregister THEN 清 InnerProvider、置空 sessionAdapter/provider、DeregisterInteractionOperationAsChildTree | 正常 |
| AC-3.3 | WHEN OnSetChildTree(childWindowId, childTreeId) THEN 存 windowId_/treeId_ 并设到 AccessibilityProperty | 正常 |
| AC-3.4 | WHEN 重复 OnRegister（isReg_ 已 true） THEN 提前返回 true（幂等） | 边界 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.x | R-1, R-2 | 代码评审 | `native_interface_xcomponent.cpp:468-477` |
| AC-2.x | R-3~R-5 | 代码评审 | `xcomponent_pattern_v2.cpp:748-778` |
| AC-3.x | R-6~R-8 | 代码评审 | `xcomponent_pattern.cpp:1220-1294` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GetNativeAccessibilityProvider 非空 | 返回 impl 持有 provider，SUCCESS(0) | @since 13 | AC-1.1 |
| R-2 | 异常 | component/handle/impl null | BAD_PARAMETER(-2) | — | AC-1.2 |
| R-3 | 行为 | V2 Create 未取 legacy | 创建 provider、注册 map、初始化 node-handle a11y | @since 20 | AC-2.1 |
| R-4 | 边界 | 已存在 provider | 返回缓存（幂等） | — | AC-2.2 |
| R-5 | 边界 | hasGotNativeXComponent_ 已取 legacy | 返回 nullptr（互斥） | — | AC-2.3 |
| R-6 | 行为 | OnRegister | 创建 provider/sessionAdapter、RegisterChildTree | — | AC-3.1 |
| R-7 | 行为 | OnDeregister | 清 provider/sessionAdapter、DeregisterChildTree | — | AC-3.2 |
| R-8 | 行为 | OnSetChildTree / 重复 Register | 存 windowId/treeId；重复 isReg_ 守卫 | 幂等 | AC-3.3, AC-3.4 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.x, R-1~R-2 | 代码评审 | legacy provider 获取 |
| VM-2 | AC-2.x, R-3~R-5 | 代码评审 | V2 provider 幂等与互斥 |
| VM-3 | AC-3.x, R-6~R-8 | 代码评审 | 子树注册幂等 |

---

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| OH_NativeXComponent_GetNativeAccessibilityProvider | Public（NDK @since 13） | component, **handle | Result | 0/-2 | legacy provider | AC-1.1 |
| OH_ArkUI_AccessibilityProvider_Create | Public（NDK @since 20） | node | Provider* | nullptr on 互斥 | V2 provider | AC-2.1 |
| OH_ArkUI_AccessibilityProvider_Dispose | Public（NDK @since 20） | provider | void | — | 销毁 provider | AC-2.4 |

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

**OH_ArkUI_AccessibilityProvider_Create(node)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_AccessibilityProvider* OH_ArkUI_AccessibilityProvider_Create(ArkUI_NodeHandle node)` |
| 返回值 | ArkUI_AccessibilityProvider* — nullptr on 互斥/失败 |
| 开放范围 | Public（NDK） |
| 错误码 | INTERNAL_ERROR（内部） |
| 关联 AC | AC-2.1~2.3 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** legacy provider @since 13；V2 provider @since 20
- **互斥约束:** V2 provider 与 legacy NativeXComponent 路径互斥（hasGotNativeXComponent_）

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| V2 vs legacy 互斥 | hasGotNativeXComponent_ 时 V2 Create 返回 nullptr | AC-2.3 |
| V2 provider 幂等 | 重复 Create 返回缓存 | AC-2.2 |
| 静态 map 追踪 | provider→host WeakPtr 映射 | AC-2.1 |
| 子树注册幂等 | isReg_ 守卫 | AC-3.4 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | provider/子树注册可经 Mock AccessibilityManager 验证 | 单测 | `xcomponent_accessibility_child_tree_callback.cpp` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | 集成测试 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本 Feat 即无障碍 provider 能力 | 全部 AC |
| 多窗口/分屏 | 否 | provider 为单节点能力 | — |
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
    query: "XComponentAccessibilityProvider V2 幂等与 legacy NativeXComponent 互斥"
  - repo: "openharmony/ace_engine"
    query: "OnAccessibilityChildTreeRegister/Deregister 子树注册链路与 sessionAdapter"
```

**关键文档：** `native_interface_xcomponent.h:828-839,1230-1244`、`xcomponent_pattern_v2.cpp:711-794`、`xcomponent_pattern.cpp:1167-1294`
