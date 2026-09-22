# 特性规格

> Func-07-04-26-Feat-01 错误码与异常行为契约：固化 `SurfaceErrorCode` 外层数字码枚举（`0`/`1001-1101`/`2001-2107`/`3001-3204`/`11001-11005`）与内层 `SchemaErrorCode` 字符串码双层分层、C++ `SurfaceErrorCodes.h` 与 ArkTS `Types.ets` 数值对齐、native 字符串 errorCode → ArkTS 枚举的手写映射链、以及运行时错误（runtimeError bridge）与多 Surface 策略错误。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 错误码与异常行为契约 |
| 特性编号 | Func-07-04-26-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-26 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/26-error-dfx/design.md` | Baselined |
| 错误码（ArkTS） | `genui/src/main/ets/interface/Types.ets` | — |
| 错误码（C++ 权威源） | `genui/src/main/cpp/SurfaceErrorCodes.h` | — |
| 内层字符串码（C++） | `genui/src/main/cpp/SchemaErrorCodes.h` | — |
| 错误码映射/异常分发（ArkTS） | `genui/src/main/ets/core/base/SurfaceControllerImpl.ets` | — |
| 阻断错误产生（C++） | `genui/src/main/cpp/NativeEntry.cpp` | — |
| 错误码参考（Docs） | `reference/errors.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: SurfaceErrorCode 外层数字码枚举契约

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎暴露稳定分段的 `SurfaceErrorCode` 枚举,
**以便** 宿主按错误码分类处理失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 处理成功 THEN `SurfaceErrorCode.NO_ERROR` 值为 0（`Types.ets:53`） | 正常 |
| AC-1.2 | WHEN Surface 未匹配/原生处理失败/协议版本不支持 THEN `NO_SURFACE_MATCHED=1001`/`NATIVE_PROCESS_FAILED=1002`/`UNSUPPORTED_PROTOCOL_VERSION=1003`（`Types.ets:56,59,62`） | 异常 |
| AC-1.3 | WHEN schema 解析段错误 THEN 错误码落在 `SCHEMA_DSL_EMPTY=2002`/`SCHEMA_JSON_PARSE_FAILED=2003`/`SCHEMA_ROOT_NOT_OBJECT=2004`（`Types.ets:74,77,80`） | 异常 |
| AC-1.4 | WHEN schema 校验段错误 THEN 错误码落在 `2101`（操作非法）~`2107`（版本非法）（`Types.ets:83-101`） | 异常 |
| AC-1.5 | WHEN action/local function/表达式错误 THEN `ACTION_NOT_REGISTER=3001`/`LOCAL_FUNCTION=3101`/`3201-3204`（`Types.ets:104-119`） | 异常 |
| AC-1.6 | WHEN 多 Surface 策略失败 THEN `MULTI_SURFACE_DISABLED=11001`~`MULTI_SURFACE_ALREADY_EXISTS=11005`（`Types.ets:122-134`） | 异常 |

### US-2: 双端错误码数值对齐

**作为** 引擎维护者,
**我想要** C++ 与 ArkTS 错误码数值一致,
**以便** 跨语言错误传递不产生歧义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 比对 schema 解析/校验段 THEN `SurfaceErrorCodes.h` 的 `SURFACE_RESULT_SCHEMA_*`（2002/2003/2004, 2101-2107）与 `Types.ets` 对应枚举数值一致（`SurfaceErrorCodes.h:29-40`） | 正常 |
| AC-2.2 | WHEN 比对 surface 操作段 THEN `SURFACE_RESULT_MULTI_SURFACE_*`（11001-11005）与 `Types.ets` 一致（`SurfaceErrorCodes.h:43-47`） | 正常 |
| AC-2.3 | WHEN 比对 runtime 回调段 THEN `SURFACE_ERROR_*`（1001-1004, 1101, 2001, 3001, 3101, 3201-3204）与 `Types.ets` 一致（`SurfaceErrorCodes.h:53-64`） | 正常 |
| AC-2.4 | WHEN 头文件注释指向同步目标 THEN `SurfaceErrorCodes.h:23-24` 声称与 `genui/src/main/ets/interface/SurfaceTypes.ets` 同步，但实际枚举定义在 `Types.ets`（`SurfaceTypes.ets` 仅 re-export） | 边界 |

### US-3: native 字符串 errorCode → 枚举映射

**作为** 生成式 UI 宿主开发者,
**我想要** native 处理失败统一映射为 `SurfaceErrorCode`,
**以便** 宿主收到稳定的枚举而非内部字符串。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `processResult.errorCode==='VERSION_INVALID'` THEN `handleReceiveMessage` 经 `recordSurfaceResult` 上报 `SCHEMA_VERSION_INVALID`（`SurfaceControllerImpl.ets:732-741`） | 异常 |
| AC-3.2 | WHEN `errorCode==='DSL_EMPTY'` THEN 上报 `SCHEMA_DSL_EMPTY` 并 `emitSchemaWarningsIfNeeded`（`SurfaceControllerImpl.ets:754-764`） | 异常 |
| AC-3.3 | WHEN `errorCode` 为 `JSON_PARSE_FAILED`/`ROOT_NOT_OBJECT`/`MESSAGE_OPERATION_INVALID`/`MESSAGE_MULTIPLE_BODIES`/`MESSAGE_BODY_INVALID`/`SURFACE_ID_MISSING`/`COMPONENTS_INVALID`/`CATALOG_ID_MISSING` THEN 逐一映射到对应 `SCHEMA_*` 枚举（`SurfaceControllerImpl.ets:765-844`） | 异常 |
| AC-3.4 | WHEN `errorCode==='SURFACE_NOT_FOUND'` 或 `processResult.surfaceResultCode===NO_SURFACE_MATCHED` THEN 上报 `NO_SURFACE_MATCHED`（`SurfaceControllerImpl.ets:845-855`） | 异常 |
| AC-3.5 | WHEN `isSurfacePolicyCode(surfaceResultCode)` 为真 THEN 走 `reportSurfacePolicyFailure`（`SurfaceControllerImpl.ets:856-862`） | 异常 |
| AC-3.6 | WHEN 其余未识别错误 THEN 兜底上报 `NATIVE_PROCESS_FAILED`（`SurfaceControllerImpl.ets:863-870`） | 异常 |
| AC-3.7 | WHEN `processResult` 为 null/undefined THEN 上报 `NATIVE_PROCESS_FAILED`（`SurfaceControllerImpl.ets:715-721`） | 边界 |

### US-4: 运行时错误分发（runtimeError bridge）

**作为** 生成式 UI 宿主开发者,
**我想要** 原生运行时错误（组件/动态值解析失败）以结构化字段回调,
**以便** 宿主定位失败组件与来源。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 原生运行时错误回调 THEN `RuntimeErrorDispatchBridge::Dispatch` 构造 `{renderId, surfaceId, componentId, errorCode, errorMessage, source}` 六字段（`RuntimeErrorDispatchBridge.cpp:105-110`） | 正常 |
| AC-4.2 | WHEN `errorCode<=0` THEN `handleNativeRuntimeError` 兜底为 `NATIVE_PROCESS_FAILED`（`SurfaceControllerImpl.ets:650`） | 边界 |
| AC-4.3 | WHEN `errorMessage` 为空 THEN 兜底为 `'native runtime error'`（`SurfaceControllerImpl.ets:651-652`） | 边界 |
| AC-4.4 | WHEN 本地函数执行失败 THEN `handleLocalFunctionError` 校验 surfaceId 归属后经 `reportError` 上报（`SurfaceControllerImpl.ets:613-647`） | 异常 |

### US-5: 内层 SchemaErrorCode 字符串码

**作为** 生成式 UI 宿主开发者,
**我想要** `SCHEMA_WARNING` 聚合负载内嵌内层字符串码,
**以便** 区分具体告警类型。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 必填缺失/非法值/类型不匹配/未定义字段/解析失败 THEN 内层字符串码为 `REQUIRED_MISS`/`INVALID_VALUE`/`TYPE_MISMATCH`/`UNDEFINED_FIELD`/`SCHEMA_PARSE_FAILED`（`SchemaErrorCodes.h:23-27`） | 正常 |
| AC-5.2 | WHEN 比对 ArkTS 枚举 THEN `SchemaErrorInfoManager.ets:16-23` 的 `SchemaErrorCode` 含上述五项加 `FUNCTION_SCHEMA_INVALID`（`SchemaErrorInfoManager.ets:22`） | 边界 |
| AC-5.3 | WHEN 比对 C++ 与 ArkTS 字符串码 THEN C++ `SchemaErrorCodes.h` 未定义 `FUNCTION_SCHEMA_INVALID` 常量（ArkTS 独有） | 边界 |

### US-6: 多 Surface 与策略错误

**作为** 生成式 UI 宿主开发者,
**我想要** 多 Surface 策略失败有独立错误码段,
**以便** 区分渲染错误与栈操作错误。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 单 Surface 控制器调用 `pop()` THEN 上报 `MULTI_SURFACE_EMPTY_STACK`（`SurfaceControllerImpl.ets:1006-1012`） | 异常 |
| AC-6.2 | WHEN `isSurfacePolicyCode` 判定 THEN 覆盖 `MULTI_SURFACE_DISABLED`/`MULTI_SURFACE_MAX_SURFACE_LIMIT_REACHED`/`MULTI_SURFACE_ALREADY_EXISTS` 三码（`SurfaceControllerImpl.ets:677-681`） | 异常 |
| AC-6.3 | WHEN C++ 侧还有 `SURFACE_RESULT_GESTURE_CONFLICT=12001`/`SURFACE_RESULT_ENGINE_ERROR=13001` 额外操作码 THEN ArkTS `Types.ets` 未定义对应枚举（`SurfaceErrorCodes.h:48-49`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1,R-2 | T-1 | 静态比对：`Types.ets` 枚举分段 | `Types.ets:51-135` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-1,R-3 | T-1 | 静态比对：`Types.ets` vs `SurfaceErrorCodes.h` | `SurfaceErrorCodes.h:23-64` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7 | R-4 | T-1 | ArkTS 单测：mock processMessage 返回各 errorCode | `SurfaceControllerImpl.ets:723-870` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-5 | T-1 | ArkTS 单测/C++ UT：runtimeError 分发 | `RuntimeErrorDispatchBridge.cpp:79-122` |
| AC-5.1,AC-5.2,AC-5.3 | R-6 | T-1 | 静态比对：`SchemaErrorCodes.h` vs `SchemaErrorInfoManager.ets` | `SchemaErrorCodes.h:23-27`、`SchemaErrorInfoManager.ets:16-23` |
| AC-6.1,AC-6.2,AC-6.3 | R-2,R-7 | T-1 | ArkTS 单测：`pop()`/策略判定 | `SurfaceControllerImpl.ets:677-681,1006-1012` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 错误码取值 | 外层数字码分段：0；1001-1101；2001-2107；3001-3204；11001-11005 | 数值稳定不重排 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-2.1,AC-2.2,AC-2.3 |
| R-2 | 异常 | 多 Surface 策略失败 | 上报 11001/11004/11005 等策略码 | 与渲染错误（2002 段）分类隔离 | AC-1.6,AC-6.1,AC-6.2,AC-6.3 |
| R-3 | 行为 | 双端错误码不一致 | C++ 与 ArkTS 数值必须一致 | 头文件注释指向 `SurfaceTypes.ets` 但实为 `Types.ets` | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-4 | 异常 | native 返回字符串 errorCode | if-else 链映射为 `SurfaceErrorCode` 枚举 | 未识别兜底 `NATIVE_PROCESS_FAILED` | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7 |
| R-5 | 恢复 | 运行时错误 errorCode/errorMessage 非法 | errorCode<=0→NATIVE_PROCESS_FAILED；message 空→默认文本 | 结构化六字段回调 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-6 | 行为 | schema 告警内层码 | 字符串码 `REQUIRED_MISS` 等五项 | ArkTS 多 `FUNCTION_SCHEMA_INVALID` | AC-5.1,AC-5.2,AC-5.3 |
| R-7 | 边界 | C++ 额外操作码 | `12001`/`13001` 仅 C++ 定义，ArkTS 无对应枚举 | 暂不经 ArkTS 枚举暴露 | AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6/AC-2.1,AC-2.2,AC-2.3,AC-2.4 错误码数值 | 静态比对 | Types.ets/SurfaceErrorCodes.h 数值一致、分段正确 |
| VM-2 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7 错误码映射 | ArkTS 单测 | 各字符串 errorCode → 枚举映射 + 兜底 |
| VM-3 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 运行时错误分发 | C++ UT + ArkTS 单测 | 六字段完整性、非法值兜底 |
| VM-4 | AC-5.1,AC-5.2,AC-5.3 内层字符串码 | 静态比对 | SchemaErrorCodes.h/SchemaErrorInfoManager.ets 差异 |
| VM-5 | AC-6.1,AC-6.2,AC-6.3 多 Surface 策略 | ArkTS 单测 | pop()/isSurfacePolicyCode 覆盖 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `SurfaceErrorCode`（公开枚举） | 既有 | 错误码分类 | 数值稳定，宿主按枚举处理 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |
| `ErrorCallback`（`(code, errorMsg)=>void`） | 既有 | 错误回调 | 错误码见本特性 AC | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7,AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| `SchemaWarningInfo`（`{code, errorMsg}`） | 既有 | 告警上报 | code 为 `SurfaceErrorCode` | AC-5.1,AC-5.2,AC-5.3 |

> d.ts 位置：`genui/src/main/ets/interface/Types.ets`、`genui/src/main/ets/interface/SurfaceController.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`SurfaceControllerImpl.handleReceiveMessage(dsl)`（内部，`SurfaceControllerImpl.ets:701`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `private handleReceiveMessage(dsl: string): void` |
| 返回值 | `void` — 经 `onError(code, msg)` 副作用上报 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | `SurfaceErrorCode` 全枚举（映射链 `:723-870`） |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7 |

**`RuntimeErrorDispatchBridge::Dispatch(...)`（`RuntimeErrorDispatchBridge.cpp:79`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool Dispatch(int32_t renderId, const std::string& surfaceId, const std::string& componentId, int32_t errorCode, const std::string& errorMessage, const std::string& source) const` |
| 返回值 | `bool` — 分发是否成功（无回调注册返回 false） |
| 开放范围 | 内部（C++ → ArkTS 回调） |
| 错误码 | `errorCode` 由 native 传入 |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| errorCode | int32_t | 是 | — | 正数有效；≤0 时 ArkTS 兜底 `NATIVE_PROCESS_FAILED` |
| errorMessage | string | 是 | `'native runtime error'`（空时） | 空时兜底默认文本 |
| surfaceId | string | 否 | `''` | 本地函数错误时须非空才上报 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `processResult.success!==true` 且 `errorCode==='DSL_EMPTY'` | 上报 `SCHEMA_DSL_EMPTY` | AC-3.2 |
| 2 | `errorCode==='SURFACE_NOT_FOUND'` | 上报 `NO_SURFACE_MATCHED` | AC-3.4 |
| 3 | 未识别 errorCode | 兜底 `NATIVE_PROCESS_FAILED` | AC-3.6 |
| 4 | runtimeError errorCode<=0 | 兜底 `NATIVE_PROCESS_FAILED` | AC-4.2 |
| 5 | 单 Surface `pop()` | 上报 `MULTI_SURFACE_EMPTY_STACK` | AC-6.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 错误码数值稳定；`SurfaceErrorCodes.h:23-24` 注释要求与 ArkTS 枚举保持同步（风险 RISK-1/RISK-2）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 错误码双层 | 外层数字码 + 内层字符串码，各司其职 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-5.1,AC-5.2,AC-5.3 |
| 数值对齐 | Types.ets 与 SurfaceErrorCodes.h 一致 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 手写映射链 | 新增错误码须同步补 if-else 分支 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7 |
| 阻断 vs 告警 | 阻断错误中断渲染，告警不中断 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-5.1,AC-5.2,AC-5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不抛异常，统一返回错误码 | ArkTS 单测 | `SurfaceControllerImpl.ets:723-870` |
| 可测试性 | 错误码映射链可逐分支 mock 单测 | ArkTS 单测 | `SurfaceControllerImpl.ets:701-893` |
| 定界定位 | 运行时错误携带 componentId/source 定位信息 | C++ UT | `RuntimeErrorDispatchBridge.cpp:105-110` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 错误码契约设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 错误码契约层不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 多 Surface 策略错误见 AC-6.1,AC-6.2,AC-6.3 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 错误码数值稳定，新增码向后兼容 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 错误码与异常行为契约
  作为 生成式 UI 宿主开发者
  我想要 引擎按分层错误码上报失败
  以便 宿主按错误码分类处理

  Scenario: DSL 为空字符串
    Given 宿主已 registerErrorCallback
    When 调用 handleMessage("")
    Then onError 收到 code=SCHEMA_DSL_EMPTY(2002)

  Scenario: Surface 未找到
    Given Surface "missing" 不存在
    When 发送 updateComponents 且 surfaceId="missing"
    Then onError 收到 code=NO_SURFACE_MATCHED(1001)

  Scenario Outline: 阻断错误映射
    Given native processMessage 返回 errorCode=<nativeCode>
    When handleReceiveMessage 处理失败
    Then onError 收到 code=<surfaceCode>

    Examples:
      | nativeCode               | surfaceCode |
      | VERSION_INVALID          | SCHEMA_VERSION_INVALID(2107) |
      | JSON_PARSE_FAILED        | SCHEMA_JSON_PARSE_FAILED(2003) |
      | MESSAGE_MULTIPLE_BODIES  | SCHEMA_MESSAGE_MULTIPLE_BODIES(2102) |
      | SURFACE_ID_MISSING       | SCHEMA_SURFACE_ID_MISSING(2104) |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（错误码契约归本 Feat；告警收集/冲刷归 Feat-02；打点归 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceErrorCode 枚举 SurfaceErrorCodes.h Types.ets 数值对齐 分段"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceControllerImpl.handleReceiveMessage native errorCode 字符串映射 if-else 链"
  - repo: "GenerativeUI/A2UIRender"
    query: "RuntimeErrorDispatchBridge SchemaErrorCode 内层字符串码 FUNCTION_SCHEMA_INVALID"
```

**关键文档：** `genui/src/main/ets/interface/Types.ets`、`genui/src/main/cpp/SurfaceErrorCodes.h`、`genui/src/main/cpp/SchemaErrorCodes.h`、`genui/src/main/ets/core/base/SurfaceControllerImpl.ets`、`genui/src/main/cpp/NativeEntry.cpp`