# 特性规格

> Func-07-04-01-Feat-01 消息类型与协议版本契约：固化 A2UI 服务端→客户端消息的四类消息体（`createSurface`/`updateComponents`/`updateDataModel`/`deleteSurface`）、单消息体约束（`messageCount!==1` 拒绝）、协议版本校验（ArkTS `CapabilitiesCore['v0.9']` + native 双层）、错误码双层映射（native 字符串 errorCode → `SurfaceErrorCode` 枚举）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 消息类型与协议版本契约 |
| 特性编号 | Func-07-04-01-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-01 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/01-protocol-core-message-model/design.md` | Baselined |
| 消息解析（ArkTS） | `genui/src/main/ets/core/base/A2UIMessage.ets` | — |
| 能力/版本（ArkTS） | `genui/src/main/ets/core/base/CapabilitiesCore.ets` | — |
| 错误码（ArkTS） | `genui/src/main/ets/interface/Types.ets` | — |
| 错误码（C++ 权威源） | `genui/src/main/cpp/SurfaceErrorCodes.h` | — |
| 消息格式参考（Docs） | `reference/messages.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 消息体类型识别与单消息体约束

**作为** 生成式 UI 宿主开发者,
**我想要** 渲染引擎识别 createSurface/updateComponents/updateDataModel/deleteSurface 四类消息,
**以便** 按消息类型正确分发处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 顶层 JSON 只含 `version` 与四键之一（`createSurface`/`updateComponents`/`updateDataModel`/`deleteSurface`） THEN `A2UIMessage.fromDSL` 返回非 null 的 `A2UIMessage`（`A2UIMessage.ets:69-96`） | 正常 |
| AC-1.2 | WHEN 顶层 JSON 同时含 2 个及以上消息体键 THEN `messageCount!==1`，`fromDSL` 返回 null 并打 `[A2UIMessage] message type is invalid` 错误日志（`A2UIMessage.ets:90-93`） | 异常 |
| AC-1.3 | WHEN 顶层 JSON 不含任何消息体键 THEN `messageCount===0`，`fromDSL` 返回 null（`A2UIMessage.ets:90-93`） | 异常 |
| AC-1.4 | WHEN `version` 字段缺失或非 string THEN `fromDSL` 返回 null 并打 `version is invalid` 日志（`A2UIMessage.ets:60-64`） | 异常 |

### US-2: 协议版本校验

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎只接受受支持的协议版本,
**以便** 拒绝不兼容的 A2UI 负载。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `version` 为 `"v0.9"` THEN `CapabilitiesCore.isSupportedA2UIProtocolVersion` 返回 true（`CapabilitiesCore.ets:28,82-84`） | 正常 |
| AC-2.2 | WHEN `version` 为不受支持值（如 `"v0.8"`/`"v1.0"`） THEN `isSupportedA2UIProtocolVersion` 返回 false（`CapabilitiesCore.ets:82-84`） | 边界 |
| AC-2.3 | WHEN `version` 值前后有空白（如 `" v0.9 "`） THEN `isSupportedA2UIProtocolVersion` 经 `trim` 后仍返回 true（`CapabilitiesCore.ets:83`） | 边界 |
| AC-2.4 | WHEN `version` 合法 THEN `CapabilitiesCore.resolveA2UIProtocolVersion` 返回 `version.trim()`；当 `version` 非受支持值则返回 null 并打 `Unsupported A2UI protocol version`（`CapabilitiesCore.ets:67-76`） | 正常 |
| AC-2.5 | WHEN `version` 为 undefined THEN `resolveA2UIProtocolVersion` 回落到默认版本 `"v0.9"`（`CapabilitiesCore.ets:69,78-80`） | 边界 |

### US-3: 消息体字段校验

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎校验消息体结构,
**以便** 非法结构在解析期被拦截。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 消息体自身非对象（null/数组/原始值） THEN `tryParseMessage` 返回 null 并打 `<key> body is invalid` 日志（`A2UIMessage.ets:104-108`） | 异常 |
| AC-3.2 | WHEN 消息体 `surfaceId` 缺失、非 string 或 trim 后为空 THEN `fromDSL` 返回 null 并打 `<key>.surfaceId is invalid`（`A2UIMessage.ets:111-115`） | 异常 |
| AC-3.3 | WHEN `updateComponents` 且 `components` 非数组 THEN `validateMessageBody` 返回 false（`A2UIMessage.ets:126-131`） | 异常 |
| AC-3.4 | WHEN `updateDataModel` 且 `path` 与 `value` 都缺失 THEN `validateMessageBody` 返回 false 并打 `requires path or value`（`A2UIMessage.ets:132-137`） | 异常 |
| AC-3.5 | WHEN `createSurface`/`deleteSurface` 无额外结构约束 THEN `validateMessageBody` 默认返回 true（`A2UIMessage.ets:138-139`） | 正常 |

### US-4: DSL 解析与空串处理

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎对输入 DSL 做合法性检查,
**以便** 空串/非 JSON/根非对象快速失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 输入 dsl trim 后为空串 THEN `fromDSL` 返回 null 并打 `dsl is empty` 日志（`A2UIMessage.ets:41-44`） | 边界 |
| AC-4.2 | WHEN 输入 dsl 非合法 JSON（`JSON.parse` 抛出） THEN 捕获异常返回 null 并打 `fromDSL JSON.parse FAIL`（`A2UIMessage.ets:47-52`） | 异常 |
| AC-4.3 | WHEN JSON 根节点非对象（数组/标量） THEN `isValidJsonObject` 为 false，返回 null 并打 `root json must be an object`（`A2UIMessage.ets:54-57,143-145`） | 边界 |
| AC-4.4 | WHEN dsl 非空合法 JSON 且根为对象 THEN 进入版本与消息体校验流程 | 正常 |

### US-5: 错误码契约

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎暴露稳定的错误码枚举,
**以便** 宿主根据错误码分类处理失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 处理成功 THEN `SurfaceErrorCode.NO_ERROR` 值为 0（`Types.ets:53`） | 正常 |
| AC-5.2 | WHEN 协议版本不受支持 THEN `SurfaceErrorCode.UNSUPPORTED_PROTOCOL_VERSION` 值为 1003（`Types.ets:62`） | 异常 |
| AC-5.3 | WHEN schema 解析段错误 THEN 错误码落在 `2002`（DSL 空）/`2003`（JSON 解析失败）/`2004`（根非对象）/`2101`（操作非法）/`2102`（多消息体）/`2103`（消息体非法）/`2104`（缺 surfaceId）/`2105`（components 非法）/`2106`（缺 catalogId）/`2107`（版本非法）（`Types.ets:74-101`） | 异常 |
| AC-5.4 | WHEN C++ 侧错误码常量与 ArkTS 枚举一致 THEN `SurfaceErrorCodes.h` 与 `Types.ets` 数值对齐（`SurfaceErrorCodes.h:23-64`） | 正常 |
| AC-5.5 | WHEN `SurfaceErrorCode` 与 native 字符串 errorCode 映射不一致 THEN 见 Feat-02（handleMessage 映射） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1,R-2 | T-1 | ArkTS 单测：`A2UIMessage.fromDSL` 四类消息 | `A2UIMessage.ets:69-96` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-3,R-4 | T-1 | ArkTS 单测：`CapabilitiesCore` 版本校验 | `CapabilitiesCore.ets:67-84` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-5,R-6 | T-1 | ArkTS 单测：`tryParseMessage`/`validateMessageBody` | `A2UIMessage.ets:98-141` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-7 | T-1 | ArkTS 单测：空串/非法 JSON/根非对象 | `A2UIMessage.ets:40-57` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-8 | T-1 | 静态比对：`Types.ets` vs `SurfaceErrorCodes.h` | `Types.ets:51-135`、`SurfaceErrorCodes.h:23-64` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 顶层 JSON 含消息体键 | 识别 `A2UIMessageType`（CREATE_SURFACE=0/UPDATE_COMPONENTS=1/UPDATE_DATA_MODEL=2/DELETE_SURFACE=3） | 仅四类槽位 | AC-1.1 |
| R-2 | 异常 | 消息体键计数 ≠ 1 | `fromDSL` 返回 null | 多 body 或零 body 均拒绝 | AC-1.2,AC-1.3 |
| R-3 | 行为 | version 非 string 或非受支持 | `fromDSL` 返回 null | 支持集 `['v0.9']` | AC-1.4,AC-2.1,AC-2.2 |
| R-4 | 边界 | version 带首尾空白 | trim 后校验 | `resolveA2UIProtocolVersion` 返回 trim 值 | AC-2.3,AC-2.4,AC-2.5 |
| R-5 | 异常 | 消息体 body 非对象 | `tryParseMessage` 返回 null | 对象判定排 null/数组/标量 | AC-3.1 |
| R-6 | 异常 | updateComponents/updateDataModel 结构非法 | `validateMessageBody` 返回 false | components 须数组；path/value 至少其一 | AC-3.3,AC-3.4 |
| R-7 | 边界 | dsl 空/非法 JSON/根非对象 | `fromDSL` 返回 null | 空串优先于 JSON.parse | AC-4.1,AC-4.2,AC-4.3 |
| R-8 | 行为 | 错误码 | ArkTS 枚举与 C++ 常量数值对齐 | 2002-2107 schema 段 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 消息体识别 | ArkTS 单测 | 四类消息、单 body 约束 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 版本校验 | ArkTS 单测 | v0.9、trim、缺省回落 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 字段校验 | ArkTS 单测 | body 对象、surfaceId、components/path/value |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 DSL 解析 | ArkTS 单测 | 空串、非法 JSON、根非对象 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 错误码 | 静态比对 | Types.ets/SurfaceErrorCodes.h 数值一致 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `A2UIMessageType`（内部枚举） | 既有 | 消息类型分发 | 不直接暴露给宿主 | AC-1.1 |
| `SurfaceErrorCode`（公开枚举） | 既有 | 错误码分类 | 数值稳定，宿主按枚举处理 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

> d.ts 位置：`genui/src/main/ets/interface/Types.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`A2UIMessage.fromDSL(dsl)`（内部，`A2UIMessage.ets:40`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static fromDSL(dsl: string): A2UIMessage | null` |
| 返回值 | `A2UIMessage` — 解析成功；`null` — 空串/非法 JSON/根非对象/版本非法/多消息体 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（返回 null） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

**`CapabilitiesCore.isSupportedA2UIProtocolVersion(version)`（`CapabilitiesCore.ets:82`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static isSupportedA2UIProtocolVersion(version: string): boolean` |
| 返回值 | `boolean` — 是否属于 `['v0.9']`（trim 后） |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| dsl | string | 是 | — | 非空合法 JSON 对象 |
| version | string | 是（消息顶层） | `"v0.9"`（`resolveA2UIProtocolVersion` 缺省回落） | 取值 `['v0.9']` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | dsl 为空串 | 返回 null | AC-4.1 |
| 2 | dsl 非法 JSON | 返回 null | AC-4.2 |
| 3 | 根非对象 | 返回 null | AC-4.3 |
| 4 | version 非受支持 | 返回 null | AC-2.2,AC-1.4 |
| 5 | 多消息体 | 返回 null | AC-1.2 |
| 6 | 合法单消息体 | 返回 A2UIMessage | AC-1.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 协议版本由 `CapabilitiesCore['v0.9']` 声明；native 侧 `SurfaceContext.h` 常量须保持同步（风险 RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 单消息体 | 顶层仅四键之一，多 body 拒绝 | AC-1.2,AC-1.3 |
| 双层版本校验 | ArkTS 快速失败 + native 权威拦截 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| 错误码数值对齐 | Types.ets 与 SurfaceErrorCodes.h 一致 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不抛异常，统一返回 null/错误码 | ArkTS 单测 | `A2UIMessage.ets:47-52` |
| 性能 | JSON.parse 失败快速返回 | ArkTS 单测 | `A2UIMessage.ets:47-52` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 消息解析与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 消息模型层不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 多 Surface 见 Feat-06 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 协议版本校验（仅 v0.9） | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 消息类型与协议版本契约
  作为 生成式 UI 宿主开发者
  我想要 引擎识别四类消息并校验协议版本
  以便 非法负载快速失败

  Scenario: 单消息体解析成功
    Given DSL 为 {"version":"v0.9","updateComponents":{"surfaceId":"main","components":[]}}
    When 调用 A2UIMessage.fromDSL
    Then 返回非 null，type=UPDATE_COMPONENTS

  Scenario Outline: 非法负载拒绝
    Given DSL 为 <payload>
    When 调用 A2UIMessage.fromDSL
    Then 返回 null

    Examples:
      | payload |
      | "" |
      | "not-json" |
      | "[1,2,3]" |
      | {"version":"v0.8","createSurface":{"surfaceId":"main","catalogId":"x"}} |
      | {"version":"v0.9","createSurface":{},"deleteSurface":{"surfaceId":"main"}} |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做消息模型与版本；handleMessage 错误码映射见 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 4 项质量检查（可复现/可观测/边界值/关联AC）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "A2UIMessage.fromDSL 四类消息体 版本校验 单消息体约束"
  - repo: "GenerativeUI/A2UIRender"
    query: "CapabilitiesCore SUPPORTED_A2UI_PROTOCOL_VERSIONS v0.9 isSupportedA2UIProtocolVersion"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceErrorCode 枚举 SurfaceErrorCodes.h 数值对齐 schema 错误码段"
```

**关键文档：** `genui/src/main/ets/core/base/A2UIMessage.ets`、`genui/src/main/ets/core/base/CapabilitiesCore.ets`、`genui/src/main/ets/interface/Types.ets`、`genui/src/main/cpp/SurfaceErrorCodes.h`