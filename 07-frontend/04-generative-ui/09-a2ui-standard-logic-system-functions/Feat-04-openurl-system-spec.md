# 特性规格

> Func-07-04-09-Feat-04 `openUrl` 函数：固化 A2UI 标准协议系统函数的契约。`openUrl` 为本地函数（`isInnerNative: false`），经 `FunctionBridge` 回 ArkTS 层执行，通过 `common.UIAbilityContext.startAbility` 以 `ohos.want.action.viewData` + `entity.system.browsable` 调起系统浏览器/应用选择器打开 URL。同步阶段校验 URL 非空与 hostContext 就绪（失败抛错→`LOCAL_FUNCTION` 3101）；调起为 fire-and-forget，异步失败仅日志。返回类型 `void`。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | openUrl 系统函数 |
| 特性编号 | Func-07-04-09-Feat-04 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-09 第四个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/09-a2ui-standard-logic-system-functions/design.md` | Baselined |
| 函数实现（ArkTS） | `genui/src/main/ets/core/functions/OpenUrlFunction.ets` | — |
| 函数桥接（ArkTS） | `genui/src/main/ets/core/functions/FunctionBridge.ets` | — |
| 函数桥接（C++） | `genui/src/main/cpp/functions/FunctionBridge.cpp` | — |
| 错误码（ArkTS） | `genui/src/main/ets/interface/Types.ets` | — |
| Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/openUrl.json` | — |
| 系统函数参考（Docs） | `reference/functions/system.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: openUrl 函数声明与注册

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎把 `openUrl` 注册为本地系统函数,
**以便** DSL 中以 `{ "call": "openUrl", ... }` 触发打开 URL。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 实例化 `openUrlFunction` THEN `asFunctionItem()` 返回 `{ name:'openUrl', isInnerNative:false, functionCall:createHandler() }`（`OpenUrlFunction.ets:30-37`） | 正常 |
| AC-1.2 | WHEN 汇总标准内置函数 THEN `openUrlFunction` 位于 `standardBuiltinFunctions` 数组首位（`A2UIBasicFunctions.ets:47`） | 正常 |
| AC-1.3 | WHEN 注入宿主上下文 THEN `setHostContext` 保存 `common.UIAbilityContext`（`OpenUrlFunction.ets:39-41`） | 正常 |
| AC-1.4 | WHEN 本地函数分发 THEN `openUrl` 不经 `NativeFunctionRegistry`（`NativeFunctionRegistry.cpp:66-86` 未注册 openUrl），经 `FunctionBridge.Invoke` 回 ArkTS | 正常 |

### US-2: URL 解析

**作为** 生成式 UI 宿主开发者,
**我想要** `openUrl` 解析 URL 入参,
**以便** 支持标准 `url` 参数名。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `args={url:"https://example.com"}` THEN `resolveUrl` 返回该字符串（`OpenUrlFunction.ets:77-90`） | 正常 |
| AC-2.2 | WHEN `args` 非对象或为 null THEN `resolveUrl` 返回空串（`OpenUrlFunction.ets:78-80`） | 异常 |
| AC-2.3 | WHEN `record['url']` 非 string 且 `record['uri']` 为 string THEN 回退使用 `uri`（`OpenUrlFunction.ets:82-85`） | 边界 |
| AC-2.4 | WHEN `record['url']` 与 `record['uri']` 均非 string THEN 返回空串（`OpenUrlFunction.ets:86-88`） | 异常 |

### US-3: 同步校验与抛错

**作为** 生成式 UI 宿主开发者,
**我想要** `openUrl` 在 URL 为空或宿主上下文未就绪时快速失败,
**以便** 非法调用被拦截并映射为稳定错误码。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `resolveUrl` 返回空串 THEN `execute` 抛出 `Error('openUrl requires a non-empty url')`（`OpenUrlFunction.ets:53-55`） | 异常 |
| AC-3.2 | WHEN `hostContext` 为 undefined THEN `execute` 抛出 `Error('host context is not ready')`（`OpenUrlFunction.ets:57-59`） | 异常 |
| AC-3.3 | WHEN `execute` 抛出异常 THEN `FunctionBridge.invokeLocalFunction` 捕获并返回 `errorCode=LOCAL_FUNCTION`（`FunctionBridge.ets:254-266`） | 异常 |
| AC-3.4 | WHEN 本地函数执行失败 THEN 错误码为 `SurfaceErrorCode.LOCAL_FUNCTION = 3101`（`Types.ets:107`） | 正常 |

### US-4: startAbility 调起

**作为** 生成式 UI 宿主开发者,
**我想要** `openUrl` 通过 want 调起系统浏览器/应用选择器,
**以便** URL 交由系统能力处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN URL 与 hostContext 就绪 THEN `startAbility` 以 `action:'ohos.want.action.viewData'`、`entities:['entity.system.browsable']`、`uri:url`、`parameters:{'ohos.ability.params.showDefaultPicker':true}` 调起（`OpenUrlFunction.ets:61-68`） | 正常 |
| AC-4.2 | WHEN `startAbility` 成功 THEN 记录 info 日志并返回 `undefined`（`OpenUrlFunction.ets:68-74`） | 正常 |
| AC-4.3 | WHEN `startAbility` 异步失败 THEN 仅记录 error 日志，不回流错误码（`OpenUrlFunction.ets:70-72`） | 异常 |

### US-5: schema 约束

**作为** 生成式 UI 宿主开发者,
**我想要** `openUrl` 的 DSL 结构受 schema 校验,
**以便** 非法 FunctionCall 在解析期被拦截。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `args.url` 缺失或非 string THEN schema 校验失败（`openUrl.json` `required:["url"]` + `type:"string"` + `format:"uri"`） | 异常 |
| AC-5.2 | WHEN `returnType` 非 `"void"` THEN schema 校验失败（`openUrl.json` `returnType: { const:"void" }`） | 异常 |
| AC-5.3 | WHEN `args` 含 `url` 之外的额外属性（如 `uri`）THEN schema 校验失败（`openUrl.json` `additionalProperties:false`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-4 | 静态比对：`asFunctionItem`/`standardBuiltinFunctions`/`NativeFunctionRegistry` | `OpenUrlFunction.ets:30-37`、`A2UIBasicFunctions.ets:47` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-4 | ArkTS 单测：`resolveUrl` url/uri/非对象 | `OpenUrlFunction.ets:77-90` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3,R-4 | T-4 | ArkTS 单测：空 URL/hostContext 缺失抛错 + 错误码 | `OpenUrlFunction.ets:53-59`、`Types.ets:107` |
| AC-4.1,AC-4.2,AC-4.3 | R-5,R-6 | T-4 | ohosTest + Mock hostContext：startAbility 调起与异步失败 | `OpenUrlFunction.ets:61-72` |
| AC-5.1,AC-5.2,AC-5.3 | R-7 | T-4 | 静态比对：`openUrl.json` | `openUrl.json` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `openUrl` 作为 FunctionCall 被解析 | 经 `FunctionBridge.Invoke` 回 ArkTS 执行 `openUrlFunction.execute` | `isInnerNative:false`，经 NAPI 回调 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | 解析 URL 入参 | 优先 `url`，回退 `uri`（非 string 返空） | 与 schema 禁 `uri` 存在落差（见 R-7） | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 异常 | URL 为空 | 抛错 → `LOCAL_FUNCTION`(3101) | 同步阶段拦截 | AC-3.1,AC-3.3,AC-3.4 |
| R-4 | 异常 | hostContext 未注入 | 抛错 → `LOCAL_FUNCTION`(3101) | 依赖 `setHostContext` 先行 | AC-3.2,AC-3.4 |
| R-5 | 行为 | URL 与 hostContext 就绪 | `startAbility(viewData+browsable+showDefaultPicker)` 调起 | 无显式权限声明 | AC-4.1,AC-4.2 |
| R-6 | 恢复 | `startAbility` 异步失败 | 仅 `console.error`，返回 undefined | fire-and-forget，不回流错误码 | AC-4.3 |
| R-7 | 异常 | schema 校验（url/returnType/额外属性） | 解析期拒绝 FunctionCall | `additionalProperties:false` 禁 `uri` | AC-5.1,AC-5.2,AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 声明与注册 | 静态比对 | isInnerNative=false/未注册 Native |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 URL 解析 | ArkTS 单测 | url/uri/非对象/非 string |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 同步抛错 | ArkTS 单测 | 空 URL/hostContext + 3101 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 startAbility | ohosTest | viewData/browsable/异步失败 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 schema | 静态比对 | openUrl.json 结构约束 |

## API 变更分析

> 存量补录，无新增/变更 Public API。`openUrl` 为内部内置系统函数（`InnerFunctionItem`）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 内置函数 `openUrl` | 既有 | DSL 系统动作（按钮 action 打开链接） | 不直接暴露为宿主 API，经 DSL FunctionCall 调用 | AC-1.1 |

> 契约位置：`genui/src/main/ets/core/functions/OpenUrlFunction.ets`；错误码 `LOCAL_FUNCTION`（`Types.ets:107`）。Kit：`@arkui-genius/genui`；权限：无显式声明（宿主需 `ohos.permission.INTERNET` 保证 URL 内容可达）。

## 接口规格

### 接口定义

**`openUrl`（FunctionCall 契约，`returnType: "void"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `private execute(args: LocalFunctionArgs, context: LocalFunctionContext): LocalFunctionResult`（经 `createHandler`/`FunctionBridge` 调起） |
| 返回值 | `undefined`（void） |
| 开放范围 | InnerApi（内置系统函数，DSL FunctionCall 触发） |
| 错误码 | `SurfaceErrorCode.LOCAL_FUNCTION = 3101`（URL 空 / hostContext 未就绪，同步抛错转错误码） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| url | string | 是 | — | 非空 string，schema `format:"uri"`；代码另支持 `uri` 作为回退名（schema 禁） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | url 非空且 hostContext 就绪 | startAbility 调起，返回 undefined | AC-4.1,AC-4.2 |
| 2 | url 为空 | 抛错 → LOCAL_FUNCTION(3101) | AC-3.1,AC-3.3 |
| 3 | hostContext 未就绪 | 抛错 → LOCAL_FUNCTION(3101) | AC-3.2,AC-3.4 |
| 4 | startAbility 异步失败 | 仅日志，返回 undefined | AC-4.3 |
| 5 | args 非对象/URL 非 string | resolveUrl 返空 → 抛错 | AC-2.2,AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9；`startAbility` 依赖 `common.UIAbilityContext`（API 20+ 上下文能力）。
- **API 版本号策略:** 函数语义由 schema（`openUrl.json`）与 `OpenUrlFunction` 共同固化；系统函数无 @since 标注需求。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 本地函数 | `isInnerNative:false`，经 `FunctionBridge` 回 ArkTS 执行（依赖 `startAbility`） | AC-1.1,AC-1.4 |
| 同步校验先行 | URL 空 / hostContext 未就绪在同步阶段抛错；异步失败不回流 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.3 |
| schema 与代码落差 | schema 禁 `uri`（`additionalProperties:false`），代码有 `uri` 回退 | AC-2.3,AC-5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 安全性 | 打开外部 URL 依赖系统浏览器/应用隔离，无内嵌 WebView | 代码评审 | `OpenUrlFunction.ets:61-68` |
| 可靠性 | 同步非法调用稳定返回 `LOCAL_FUNCTION`(3101)，不崩溃 | ArkTS 单测 | `OpenUrlFunction.ets:53-59` |
| 权限 | 无显式权限；URL 可达性依赖宿主 `ohos.permission.INTERNET` | 静态比对 | `entry/src/main/module.json5:5` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 调起结果依赖系统浏览器存在性 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 系统函数不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 是 | 打开 URL 由系统 `startAbility` 决定前台/分屏行为 | AC-4.1 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 函数语义随协议 v0.9 固化 | AC-5.1,AC-5.2,AC-5.3 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 系统函数 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: openUrl 系统函数
  作为 生成式 UI 宿主开发者
  我想要 openUrl 通过系统浏览器打开 URL
  以便 触发设备级打开链接动作

  Scenario: 正常打开 URL
    Given hostContext 已注入且 url 为 "https://example.com"
    When 调用 openUrlFunction.execute
    Then 以 action=viewData、entities=[browsable] 调起 startAbility
    And 返回 undefined

  Scenario: URL 为空抛错
    Given args 不含有效 url
    When 调用 openUrlFunction.execute
    Then 抛出 Error 并由 FunctionBridge 映射为 LOCAL_FUNCTION(3101)

  Scenario: hostContext 未就绪抛错
    Given hostContext 为 undefined
    When 调用 openUrlFunction.execute
    Then 抛出 Error 并由 FunctionBridge 映射为 LOCAL_FUNCTION(3101)
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-04 只覆盖 `openUrl`；`and`/`or`/`not` 归 Feat-01/02/03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "OpenUrlFunction execute resolveUrl startAbility viewData browsable showDefaultPicker"
  - repo: "GenerativeUI/A2UIRender"
    query: "FunctionBridge invokeLocalFunction LOCAL_FUNCTION 3101 错误码映射"
  - repo: "GenerativeUI/A2UIRender"
    query: "openUrl.json schema url uri additionalProperties void returnType"
```

**关键文档：** `genui/src/main/ets/core/functions/OpenUrlFunction.ets`、`genui/src/main/ets/core/functions/FunctionBridge.ets`、`genui/src/main/ets/interface/Types.ets`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/openUrl.json`