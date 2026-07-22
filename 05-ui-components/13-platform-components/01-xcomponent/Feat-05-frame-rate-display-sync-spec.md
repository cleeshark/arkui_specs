# 特性规格

> Func-05-13-01-Feat-05 帧率与显示同步（DisplaySync）：固化 OH_NativeXComponent_SetExpectedFrameRateRange / RegisterOnFrameCallback / UnregisterOnFrameCallback（@since 11）及节点 API 变体（@since 20）、ExpectedRateRange 校验、DisplaySync 派发的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 帧率与显示同步（DisplaySync） |
| 特性编号 | Func-05-13-01-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | NDK @since 11 / 节点 API @since 20 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 帧率范围规格 | ExpectedRateRange{min,max,expected} 校验 min<=max && expected∈[min,max] |
| ADDED | 回调规格 | SetExpectedFrameRateRange、RegisterOnFrameCallback(timestamp,targetTimestamp)、Unregister |
| ADDED | 节点 API 变体规格 | OH_ArkUI_XComponent_* @since 20（仅 V2 + HasGotNativeXComponent 守卫） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/13-platform-components/01-xcomponent/design.md` | Baselined |

---

## 用户故事

### US-1: 设置期望帧率范围

**作为** NDK 开发者,
**我想要** 通过 SetExpectedFrameRateRange 设定期望刷新率,
**以便** 平滑特定内容（如视频/动画）的帧率。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `SetExpectedFrameRateRange(component, &range)` 且 min<=max 且 expected∈[min,max] THEN 存储 RateRange、触发回调、返回 SUCCESS(0) | 正常 |
| AC-1.2 | WHEN range 不满足 min<=max 或 expected 越界 THEN 返回 BAD_PARAMETER(-2) | 异常 |
| AC-1.3 | WHEN component/range/callback 为 null THEN 返回 BAD_PARAMETER(-2) | 异常 |
| AC-1.4 | WHEN 帧率生效 THEN displaySync_ 经 NotifyXComponentExpectedFrameRate 通知 | 正常 |

### US-2: 注册/注销帧回调

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `RegisterOnFrameCallback(component, cb)` THEN 存储 cb、返回 SUCCESS；cb(component, timestamp, targetTimestamp) 每帧派发 | 正常 |
| AC-2.2 | WHEN `UnregisterOnFrameCallback(component)` THEN 清除 cb、DelFromPipelineOnContainer、返回 SUCCESS | 正常 |

### US-3: 节点 API 变体（@since 20）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `OH_ArkUI_XComponent_SetExpectedFrameRateRange(node, range)` 且 native 已取出 THEN 返回 PARAM_INVALID（HasGotNativeXComponent 守卫） | 边界 |
| AC-3.2 | WHEN 节点 API 在 V2 pattern 上且未取 native THEN 调 SetExpectedRateRange 返回 NO_ERROR | 正常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.x | R-1~R-3 | C-API 单测 | `native_interface_xcomponent_impl.cpp:254-270` |
| AC-2.x | R-4 | 代码评审 | `xcomponent_pattern.cpp:1858-1891` |
| AC-3.x | R-5 | 代码评审 | `xcomponent_model_ng.cpp:707-743` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | SetExpectedFrameRateRange 且 min<=max, expected∈[min,max] | 存储 RateRange、触发回调、SUCCESS(0) | @since 11 | AC-1.1 |
| R-2 | 异常 | range 不满足约束 | BAD_PARAMETER(-2) | — | AC-1.2 |
| R-3 | 异常 | component/range/cb null | BAD_PARAMETER(-2) | — | AC-1.3 |
| R-4 | 行为 | Register/Unregister OnFrameCallback | 存储/清除、经 displaySync_ 派发；cb(timestamp,targetTimestamp) | @since 11 | AC-2.x |
| R-5 | 边界 | 节点 API（@since 20）HasGotNativeXComponent 已取 | 返回 PARAM_INVALID | 仅 V2 pattern | AC-3.x |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.x, R-1~R-3 | C-API 单测 | RateRange 校验 |
| VM-2 | AC-2.x, R-4 | 代码评审 | 帧回调派发 |
| VM-3 | AC-3.x, R-5 | 代码评审 | 节点 API 守卫 |

---

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| OH_NativeXComponent_SetExpectedFrameRateRange | Public（NDK @since 11） | component, ExpectedRateRange* | Result | 0/-2 | 设帧率范围 | AC-1.1 |
| OH_ArkUI_XComponent_SetExpectedFrameRateRange | Public（NDK @since 20） | node, range | ArkUI_ErrorCode | 0/401 | 节点变体 | AC-3.2 |

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

**OH_NativeXComponent_SetExpectedFrameRateRange(component, range)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_NativeXComponent_Result SetExpectedFrameRateRange(OH_NativeXComponent*, OH_NativeXComponent_ExpectedRateRange*)` |
| 返回值 | Result — 0=SUCCESS, -2=BAD_PARAMETER |
| 开放范围 | Public（NDK） |
| 错误码 | SUCCESS(0), BAD_PARAMETER(-2) |
| 关联 AC | AC-1.1~1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| range.min | int32 | 是 | — | min<=max |
| range.max | int32 | 是 | — | max>=min |
| range.expected | int32 | 是 | — | expected∈[min,max] |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** OH_NativeXComponent_* @since 11；OH_ArkUI_XComponent_* @since 20
- **API 版本号策略:** NDK since 11；节点 API since 20（V2 + HasGotNativeXComponent 守卫）

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| RateRange 三约束 | min<=max && expected∈[min,max] | AC-1.2 |
| 节点 API 守卫 | HasGotNativeXComponent 时拒绝 | AC-3.1 |
| DisplaySync 派发 | 经 UIXComponentDisplaySync 加入管线 | AC-1.4 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 帧率设置应平滑生效，无量化指标 | 集成测试 | `xcomponent_pattern.cpp` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 实际帧率受设备刷新能力限制 | — | 集成测试 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | since 11 vs since 20 双 API | 兼容性声明 |
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
    query: "SetExpectedRateRange 校验与 DisplaySync 派发链路"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_XComponent 节点帧率 API HasGotNativeXComponent 守卫"
```

**关键文档：** `native_interface_xcomponent.h/.cpp`、`native_interface_xcomponent_impl.cpp:254-291`、`xcomponent_pattern.cpp:1844-1891`
