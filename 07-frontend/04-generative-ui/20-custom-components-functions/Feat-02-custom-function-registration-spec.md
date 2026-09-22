# 特性规格

> Func-07-04-20-Feat-02 自定义函数注册与调用：固化以 `ClientFunction{name,schemaProvider,functionCall}` 为注册单元的自定义函数契约、`FunctionCall=(params,context)=>A2UIValueType` 同步签名、`FunctionContext{resolver,onError}` 执行上下文、Catalog 同名覆盖语义，以及 C++ `FunctionBridge` → NAPI `registerInvokeLocalFunction` → ArkTS `FunctionBridge.invokeLocalFunction` 的双层桥接、schema 校验/参数规范化、返回类型校验与错误分发（`LOCAL_FUNCTION=3101`）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自定义函数注册与调用 |
| 特性编号 | Func-07-04-20-Feat-02 |
| 优先级 | P0 |
| 目标版本 | OpenHarmony API Version 13 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Func-07-04-20 第二个 Feat，共享功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/20-custom-components-functions/design.md` | Baselined |
| 函数注册契约（ArkTS） | `genui/src/main/ets/interface/ClientFunction.ets` | — |
| 目录注册接口（ArkTS） | `genui/src/main/ets/interface/Catalog.ets` | — |
| 目录实现（ArkTS） | `genui/src/main/ets/core/base/CatalogImpl.ets` | — |
| 内部函数项（ArkTS） | `genui/src/main/ets/core/base/FunctionItem.ets` | — |
| 函数桥（ArkTS） | `genui/src/main/ets/core/functions/FunctionBridge.ets` | — |
| 函数调用定义（ArkTS） | `genui/src/main/ets/core/types/FunctionCall.ets` | — |
| 函数桥（C++） | `genui/src/main/cpp/functions/FunctionBridge.cpp/.h` | — |
| 函数调用信息（C++） | `genui/src/main/cpp/functions/FunctionCallInfo.cpp/.h` | — |
| 函数结果（C++） | `genui/src/main/cpp/functions/FunctionResult.h` | — |
| 错误码（C++ 权威源） | `genui/src/main/cpp/SurfaceErrorCodes.h` | — |
| 开发者指南（Docs） | `guides/creating-custom-functions.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: ClientFunction 注册与查询

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `Catalog.addClientFunction` 注册自定义函数并支持移除/查询,
**以便** DSL 的 `FunctionCall.call` 字段能按名称命中函数实现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `addClientFunction` 传入合法 `ClientFunction`（name 非空、functionCall 存在）THEN 返回 true 并写入 `functionItems`（`CatalogImpl.ets:94-101`） | 正常 |
| AC-1.2 | WHEN `addClientFunction` 传入 name 为空或 null/undefined THEN `normalizeClientFunctionItem` 返回 undefined，返回 false（`CatalogImpl.ets:180-190`） | 异常 |
| AC-1.3 | WHEN 注册同名函数 THEN `functionItems.set` 覆盖旧定义（`CatalogImpl.ets:99`） | 正常 |
| AC-1.4 | WHEN `removeClientFunction` 传入已存在 name THEN 返回 true 并删除；不存在 name THEN 返回 false（`CatalogImpl.ets:103-109`） | 正常 |
| AC-1.5 | WHEN `hasClientFunction`/`getAllClientFunctionNames` 被调用 THEN 分别返回布尔判定与全部函数 name 列表（`CatalogImpl.ets:111-121`） | 正常 |

### US-2: FunctionCall 契约

**作为** 生成式 UI 宿主开发者,
**我想要** 用同步 `FunctionCall` 实现自定义函数,
**以便** 在函数调用处同步回填计算结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `FunctionCall` 类型被引用 THEN 其定义为 `(params: A2UIValueType, context: FunctionContext) => A2UIValueType`，同步返回（`interface/ClientFunction.ets:41`） | 正常 |
| AC-2.2 | WHEN `FunctionContext` 被注入 THEN 提供 `resolver`（解析嵌套动态值）与 `onError`（`FunctionErrorReporter`）两字段（`interface/ClientFunction.ets:26-36`） | 正常 |
| AC-2.3 | WHEN `FunctionErrorReporter` 被调用 THEN 类型为 `(errorMessage: string) => void`（`interface/ClientFunction.ets:21`） | 正常 |
| AC-2.4 | WHEN 函数 call 定义被读取 THEN `A2UIFunctionCall` 提供 `call`（必填）/`args`（可选）/`returnType`（可选，枚举含 string/number/boolean/array/object/any/void）三字段（`core/types/FunctionCall.ets:18-24,52-57`） | 正常 |

### US-3: 函数查找与运行时覆盖

**作为** 宿主开发者,
**我想要** `FunctionBridge.register` 支持运行时函数覆盖,
**以便** 无需改 Catalog 即可替换函数实现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `FunctionBridge.register(name, handler)` 且 name 非空 THEN 写入 `registeredFunctionOverrides`，标记 `isInnerNative=false`（`FunctionBridge.ets:100-127`） | 正常 |
| AC-3.2 | WHEN `FunctionBridge.register` 且 name 为空 THEN 直接返回不注册（`FunctionBridge.ets:101-103`） | 边界 |
| AC-3.3 | WHEN `findCatalogFunctionItem` 被调用 THEN 先查 `registeredFunctionOverrides`，未命中再经 `SurfaceControllerImpl.getControllerByRenderId` 查 catalog 的 `functions` 列表（`FunctionBridge.ets:307-329`） | 正常 |
| AC-3.4 | WHEN `FunctionBridge.install` 被调用 THEN 幂等注册 `registerInvokeLocalFunction`（经 NAPI `registerInvokeLocalFunction`）与 `registerLocale`（`FunctionBridge.ets:54-90`） | 正常 |

### US-4: 函数调用与 schema 校验

**作为** 引擎实现者,
**我想要** 在函数执行前做 schema 校验与参数规范化,
**以便** 非法入参快速失败并规范化动态值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `invokeLocalFunction` schema 校验失败 THEN 返回 `success=false` 且 errorCode=`LOCAL_FUNCTION`（3101）（`FunctionBridge.ets:191-197`） | 异常 |
| AC-4.2 | WHEN `request.normalizeOnly===true` THEN 返回 `success=true` + `normalizedArgs`/`normalizedReturnType`，不执行函数体（`FunctionBridge.ets:203-211`） | 正常 |
| AC-4.3 | WHEN 函数未注册或 `isInnerNative` 或无 `functionCall` THEN 返回 `LOCAL_FUNCTION` 失败并 `notifyLocalFunctionError`（`FunctionBridge.ets:213-218`） | 异常 |
| AC-4.4 | WHEN 函数正常执行 THEN `functionCall(args, context)` 同步调用，`args` 为规范化后参数，`context.resolver`/`context.onError` 就绪（`FunctionBridge.ets:223-253`） | 正常 |

### US-5: 返回类型校验与错误分发

**作为** 引擎实现者,
**我想要** 校验函数返回值类型并统一分发错误,
**以便** 类型不匹配与业务异常均可被宿主捕获。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 返回值类型与 `normalizedReturnType` 不匹配 THEN 返回 `LOCAL_FUNCTION` 失败，错误信息含 `returned mismatched value for type`（`FunctionBridge.ets:242-248`） | 异常 |
| AC-5.2 | WHEN 函数执行抛出异常且未 onError 上报 THEN 捕获并返回 `LOCAL_FUNCTION` 失败（`FunctionBridge.ets:254-266`） | 异常 |
| AC-5.3 | WHEN `context.onError` 被调用 THEN 经 `notifyLocalFunctionError` 分发给所有已注册 listener；无 listener 时打 warn 日志（`FunctionBridge.ets:276-305`） | 正常 |
| AC-5.4 | WHEN `validateReturnType` 处理 `void` THEN 要求返回值为 `undefined`；`any` 恒通过（`FunctionBridge.ets:377-398`） | 边界 |
| AC-5.5 | WHEN 调用 `invoke` 且 `functionCall.call` 为空 THEN 直接返回 undefined（`FunctionBridge.ets:136-138`） | 边界 |

### US-6: C++ 双层桥接

**作为** 引擎实现者,
**我想要** C++ 侧授权校验并回调 ArkTS 执行函数,
**以便** 函数调用与 catalog 授权统一走原生管线。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `FunctionBridge::Invoke` 且 catalog 未注册该函数 THEN `ValidateInvokeTarget` 返回 false 并 `DispatchUnknownLocalFunctionError`（`functions/FunctionBridge.cpp:219-239`） | 异常 |
| AC-6.2 | WHEN bridge 有效且 catalog 授权通过 THEN 构造 request `{renderId,surfaceId,componentId,functionName,args,returnType}` 回调 ArkTS（`functions/FunctionBridge.cpp:260-283`） | 正常 |
| AC-6.3 | WHEN `RegisterInvokeLocalFunction` 被调用 THEN 释放旧 ref 后创建新 `napi_ref`（幂等替换）（`functions/FunctionBridge.cpp:404-425`） | 正常 |
| AC-6.4 | WHEN 函数返回值/参数嵌套深度超过 `MAX_NAPI_TO_JSON_DEPTH=32` THEN `NapiValueToJsonValue` 返回空 JsonValue（`functions/FunctionBridge.cpp:39,202-205`） | 边界 |
| AC-6.5 | WHEN `RegisterInvokeLocalFunction` 作为 NAPI 导出被注册 THEN `NapiInit.cpp` 声明该导出项（`NapiInit.cpp:36-37`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2,R-3 | T-2 | ArkTS 单测：`CatalogImpl` 函数注册/查询 | `CatalogImpl.ets:94-190` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-4 | T-2 | ArkTS 单测：`FunctionCall`/`FunctionCall.ets` schema | `interface/ClientFunction.ets:21-61`、`core/types/FunctionCall.ets:18-57` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-5,R-6 | T-2 | ArkTS 单测：`FunctionBridge.register/install/findCatalogFunctionItem` | `FunctionBridge.ets:54-127,307-329` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-7,R-8 | T-2 | ArkTS 单测 + ohosTest：`invokeLocalFunction` | `FunctionBridge.ets:177-253` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-9,R-10 | T-2 | ArkTS 单测：`validateReturnType`/`notifyLocalFunctionError` | `FunctionBridge.ets:242-398` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 | R-11 | T-2 | C++ UT：`FunctionBridge` 授权/桥接 | `functions/FunctionBridge.cpp:219-425` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `addClientFunction` 传入合法 ClientFunction | 归一化后写入 `functionItems` 并返回 true | name 非空、functionCall 存在 | AC-1.1 |
| R-2 | 异常 | `addClientFunction` 传入空 name/null | 归一化失败返回 false | 空名/空 item | AC-1.2 |
| R-3 | 行为 | 同名函数重复注册 | `functionItems.set` 覆盖旧定义 | 按 name 精确匹配，覆盖 | AC-1.3 |
| R-4 | 行为 | 函数执行 | `FunctionCall` 同步返回 `A2UIValueType`，`FunctionContext` 提供 resolver/onError | 同步签名 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-5 | 行为 | 函数查找 | `registeredFunctionOverrides` 优先于 catalog | 覆盖优先 | AC-3.3 |
| R-6 | 行为 | 运行时覆盖 | `FunctionBridge.register` 写入 override（`isInnerNative=false`） | 空名拒绝 | AC-3.1,AC-3.2 |
| R-7 | 异常 | schema 校验失败 | 返回 `LOCAL_FUNCTION` 失败 | 校验/规范化先行 | AC-4.1 |
| R-8 | 异常 | 函数未注册/无 functionCall | 返回 `LOCAL_FUNCTION` 并分发错误 | `isInnerNative` 视为不可执行 | AC-4.3 |
| R-9 | 异常 | 返回值类型不匹配 | 返回 `LOCAL_FUNCTION` 失败 | `void` 要求 undefined；`any` 恒通过 | AC-5.1,AC-5.4 |
| R-10 | 恢复 | 函数抛异常/onError 上报 | 捕获并 `notifyLocalFunctionError` 分发，无 listener 打 warn | 异常不抛向 C++ | AC-5.2,AC-5.3 |
| R-11 | 行为 | C++ 双层桥接 | `ValidateInvokeTarget` 授权 → NAPI 回调 ArkTS → 类型/深度约束 | 深度上限 32 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 函数注册 | ArkTS 单测 | add/remove/has/getAll、同名覆盖、空名拒绝 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 FunctionCall 契约 | ArkTS 单测 | 同步签名、FunctionContext、返回类型枚举 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 函数查找/覆盖 | ArkTS 单测 | override 优先、install 幂等 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 调用与校验 | ArkTS 单测 + ohosTest | normalizeOnly、未注册失败、规范化参数 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 类型/错误 | ArkTS 单测 | validateReturnType、异常捕获、错误分发 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 C++ 桥 | C++ UT | 授权校验、request 构造、深度上限 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `ClientFunction`（公开接口） | 既有 | 函数注册单元 | name/schemaProvider/functionCall 三字段 | AC-1.1 |
| `FunctionCall`（公开类型） | 既有 | 函数实现签名 | 同步 `(params, context) => A2UIValueType` | AC-2.1 |
| `FunctionContext`（公开接口） | 既有 | 函数执行上下文 | resolver + onError | AC-2.2 |
| `FunctionErrorReporter`（公开类型） | 既有 | 错误上报回调 | `(errorMessage) => void` | AC-2.3 |
| `Catalog.addClientFunction/removeClientFunction/hasClientFunction/getAllClientFunctionNames` | 既有 | 函数目录操作 | 返回 boolean/string[] | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：`genui/src/main/ets/interface/ClientFunction.ets`、`Catalog.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`Catalog.addClientFunction(clientFunction)`（`CatalogImpl.ets:94`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `addClientFunction(clientFunction: ClientFunction): boolean` |
| 返回值 | `boolean` — 归一化成功并入 Catalog |
| 开放范围 | Public |
| 错误码 | N/A（返回 false 表示拒绝） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**`FunctionBridge.invokeLocalFunction(request)`（`FunctionBridge.ets:177`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static invokeLocalFunction(request: LocalFunctionRequest): LocalFunctionResponse` |
| 返回值 | `LocalFunctionResponse` — `{success, returnType, value?, normalizedArgs?, normalizedReturnType?, errorCode?, errorMessage?}` |
| 开放范围 | 内部（framework-internal，经 NAPI 回调） |
| 错误码 | `SurfaceErrorCode.LOCAL_FUNCTION`（3101） |
| 关联 AC | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-5.1,AC-5.2 |

**`FunctionBridge::Invoke(renderId,surfaceId,componentId,functionCall)`（`functions/FunctionBridge.cpp:427`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool FunctionBridge::Invoke(int32_t renderId, const std::string& surfaceId, const std::string& componentId, const std::shared_ptr<FunctionCallInfo>& functionCall) const` |
| 返回值 | `bool` — 发起调用是否成功 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（授权失败经 RuntimeError 分发） |
| 关联 AC | AC-6.1,AC-6.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| clientFunction | ClientFunction | 是 | — | name 非空；functionCall 存在 |
| clientFunction.name | string | 是 | — | 与 DSL `FunctionCall.call` 完整一致，区分大小写 |
| functionCall.call | string | 是 | — | 非空 |
| functionCall.returnType | string | 否 | `any`/schema 默认 `boolean` | string/number/boolean/array/object/any/void |
| context.onError | FunctionErrorReporter | 否 | — | 空消息归一化为 `local function reported error` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 ClientFunction 注册 | 返回 true 并入目录 | AC-1.1 |
| 2 | 空 name 注册 | 返回 false | AC-1.2 |
| 3 | 同名重复注册 | 覆盖旧定义 | AC-1.3 |
| 4 | schema 校验失败 | 返回 LOCAL_FUNCTION 失败 | AC-4.1 |
| 5 | normalizeOnly=true | 返回规范化参数与类型，不执行 | AC-4.2 |
| 6 | 函数未注册调用 | 返回 LOCAL_FUNCTION 并分发错误 | AC-4.3 |
| 7 | 返回值类型不匹配 | 返回 LOCAL_FUNCTION 失败 | AC-5.1 |
| 8 | 执行抛异常 | 捕获并分发错误 | AC-5.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** OpenHarmony API Version 13。
- **API 版本号策略:** 公开契约由 `@arkui-genius/genui` 声明；catalog 函数 schema 包装逻辑 `wrapClientFunctionSchemaProvider` 对非完整 schema 自动补齐 `call/args/returnType`（`CatalogImpl.ets:192-232`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 同步语义 | `FunctionCall` 同步返回，异步结果走后续消息 | AC-2.1 |
| 同名覆盖 | catalog 与 override 均按 name 唯一 | AC-1.3,AC-3.3 |
| override 优先 | `registeredFunctionOverrides` 优先于 catalog | AC-3.3 |
| 校验先行 | schema 校验/规范化先于函数体执行 | AC-4.1,AC-4.2 |
| 深度上限 | NAPI→Json 转换深度上限 32 | AC-6.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 函数异常捕获，不向 C++ 抛异常 | ArkTS 单测 | `FunctionBridge.ets:254-266` |
| 性能 | 函数查找 override Map O(1)，catalog 线性扫描 | ArkTS 单测 | `FunctionBridge.ets:307-329` |
| 可测试性 | 函数桥/校验/类型校验独立单测 + ohosTest | ohosTest | `FunctionCallCustom.test.ets` |
| 定界定位 | 错误统一 `LOCAL_FUNCTION=3101` + console.error | 静态比对 | `SurfaceErrorCodes.h:60`、`Types.ets:107` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 函数注册/调用与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 函数层不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 函数层不涉及（组件侧经 changeReason 处理，见 Feat-01） | — |
| 多窗口/分屏 | 否 | 多 Surface 归 Feat-06（07-04-01） | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 错误码/返回类型枚举稳定 | AC-2.4 |
| 生态兼容 | 是 | A2UI 扩展协议 FunctionCall 语义兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 自定义函数注册与调用
  作为 生成式 UI 宿主开发者
  我想要 注册并调用自定义函数
  以便 DSL 的 FunctionCall 同步计算业务结果

  Scenario: 注册并调用函数
    Given catalog.addClientFunction(calculateTaxFunction) 返回 true
    When DSL 含 {"call":"calculateTax","args":{"price":100,"rate":0.13},"returnType":"string"}
    Then 返回 "13.00"

  Scenario: 未注册函数调用失败
    Given catalog 未注册 "unknownFn"
    When DSL 含 {"call":"unknownFn"}
    Then 返回 success=false 且 errorCode=3101

  Scenario Outline: 返回类型不匹配
    Given catalog 注册 returnType <type> 的函数返回 <value>
    When 调用 invokeLocalFunction
    Then success 为 <success>

    Examples:
      | type    | value   | success |
      | number  | "abc"   | false   |
      | void    | undefined | true  |
      | any     | 123     | true    |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做函数注册与调用；自定义组件见 Feat-01；内置函数实现归 07-04-08/09/16）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ClientFunction FunctionCall FunctionContext FunctionErrorReporter 契约定义"
  - repo: "GenerativeUI/A2UIRender"
    query: "CatalogImpl addClientFunction wrapClientFunctionSchemaProvider 同名覆盖"
  - repo: "GenerativeUI/A2UIRender"
    query: "FunctionBridge invokeLocalFunction validateReturnType notifyLocalFunctionError 查找逻辑"
  - repo: "GenerativeUI/A2UIRender"
    query: "FunctionBridge::Invoke ValidateInvokeTarget registerInvokeLocalFunction NAPI 桥接"
```

**关键文档：** `genui/src/main/ets/interface/ClientFunction.ets`、`genui/src/main/ets/core/base/CatalogImpl.ets`、`genui/src/main/ets/core/functions/FunctionBridge.ets`、`genui/src/main/ets/core/types/FunctionCall.ets`、`genui/src/main/cpp/functions/FunctionBridge.cpp`、`genui/src/main/cpp/SurfaceErrorCodes.h`