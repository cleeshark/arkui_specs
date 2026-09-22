# 特性规格

> Func-07-04-16-Feat-06 `setDataModel` 函数：固化 A2UI 鸿蒙扩展协议数据操作函数 `setDataModel` 的语义——在 EventHandler 链中按 `path`（JSON Pointer）写入 `value` 到 DataModel 并触发绑定刷新。ArkTS 目录注册（`isInnerNative: true` + schema `setDataModel.json`），运行时分发走**动作注册表**（`NativeActionDispatcher → NativeActionRegistry` 的 `SetDataModelAction`，`BuiltInActions.cpp`）。`path` 为空仅 `LOG_WARN` 放弃；DataModel 惰性创建。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | setDataModel 数据动作函数 |
| 特性编号 | Func-07-04-16-Feat-06 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-16 第六个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/16-a2ui-extended-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/extended/CatalogActionFunctions.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 动作实现（C++） | `genui/src/main/cpp/components/actions/BuiltInActions.cpp` | — |
| 动作注册表（C++） | `genui/src/main/cpp/components/actions/NativeActionRegistry.cpp` | — |
| 动作分发（C++） | `genui/src/main/cpp/components/actions/ActionDispatcher.cpp`、`EventHandlerChainExecutor.cpp` | — |
| 数据模型（C++） | `genui/src/main/cpp/data/DataModel.h` | — |
| schema | `genui/src/main/resources/rawfile/schema/Extended/functions/setDataModel.json` | — |
| 函数参考（Docs） | `reference/functions/extension-functions.md`、`concepts/actions-and-functions.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `setDataModel` 注册为扩展协议数据操作函数,
**以便** DSL 的 `call="setDataModel"` 被引擎识别并受 schema 约束。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 构造 THEN `setDataModelFunction = new CatalogActionFunction('setDataModel', 'setDataModel.json')`（`CatalogActionFunctions.ets:44-45`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='setDataModel'` 且 `isInnerNative=true`（`CatalogActionFunctions.ets:30-37`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadExtendedFunctionSchema('setDataModel.json')`（`CatalogActionFunctions.ets:39-41`） | 正常 |
| AC-1.4 | WHEN 聚合扩展内置函数 THEN `setDataModel` 列入 `extendedCatalogFunctions`（`A2UIBasicFunctions.ets:68`） | 正常 |
| AC-1.5 | WHEN 动作注册 THEN `RegisterBuiltInActions` 注册 `"setDataModel" → SetDataModelAction`（`BuiltInActions.cpp:206`） | 正常 |

### US-2: 数据写入（正常）

**作为** 生成式 UI 宿主开发者,
**我想要** `setDataModel` 按 path 写入 value 并触发刷新,
**以便** 驱动绑定组件更新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `ctx.dataModel` 为 null THEN 惰性创建 `DataModel(ctx.surfaceId)`（`BuiltInActions.cpp:140-142`） | 正常 |
| AC-2.2 | WHEN `args.path` 为非空 string THEN `UpdateByPath(resolvedPath, value)` 写入（`BuiltInActions.cpp:144-157`） | 正常 |
| AC-2.3 | WHEN 写入成功 THEN `NotifyPathUpdate(resolvedPath)` 通知绑定组件（`BuiltInActions.cpp:158`） | 正常 |
| AC-2.4 | WHEN `args.value` 为任意 JSON 值（字面量/对象/数组/表达式结果） THEN 原样写入（`BuiltInActions.cpp:156`） | 正常 |

### US-3: 非法入参降级（异常/边界）

**作为** 生成式 UI 宿主开发者,
**我想要** `setDataModel` 在 path 为空时放弃写入,
**以便** 非法调用不污染数据模型。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `args.path` 非 string 或为空 THEN `LOG_WARN` 并返回（不写入、不通知）（`BuiltInActions.cpp:144-154`） | 异常 |
| AC-3.2 | WHEN `path` 为 string 但值为 `""` THEN 同样放弃写入（`resolvedPath.empty()` 分支，`BuiltInActions.cpp:150-154`） | 边界 |
| AC-3.3 | WHEN Surface 已销毁（无 dataModel 来源） THEN 链仍执行，但 `dataModel` 惰性新建后写入对无 surface 场景无效（`DispatchEventToHandlers` dataModel 为空时 `BuiltInActions.cpp:140-142` 新建） | 边界 |

### US-4: 分发路径与返回值

**作为** 生成式 UI 宿主开发者,
**我想要** `setDataModel` 经动作注册表分发且不产生返回值,
**以便** 明确其副作用动作语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 链内 `call="setDataModel"` THEN `NativeActionDispatcher::CanDispatch` 命中 `NativeActionRegistry`（`ActionDispatcher.cpp:26-35`） | 正常 |
| AC-4.2 | WHEN `setDataModel` 执行 THEN 返回 `JsonValue()`（无结果，不参与 `as` 局部变量回填）（`BuiltInActions.cpp:159`） | 正常 |
| AC-4.3 | WHEN `setDataModel` 不在 `NativeFunctionRegistry` THEN 不会经函数注册表分发（`NativeFunctionRegistry.cpp:66-86` 未含 setDataModel） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-6 | ArkTS 单测 + 静态比对 | `CatalogActionFunctions.ets:30-45`、`A2UIBasicFunctions.ets:68`、`BuiltInActions.cpp:206` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-6 | C++ UT：UpdateByPath/NotifyPathUpdate 副作用 | `BuiltInActions.cpp:138-159` |
| AC-3.1,AC-3.2,AC-3.3 | R-3 | T-6 | C++ UT：空 path 放弃 | `BuiltInActions.cpp:144-154` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-6 | C++ UT + 静态比对：动作注册表分发 | `ActionDispatcher.cpp:26-35`、`NativeFunctionRegistry.cpp:66-86` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='setDataModel'`、`isInnerNative=true`、schema `setDataModel.json`，动作注册表 `Register` | 双注册一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | path 非空 | 惰性建 DataModel → `UpdateByPath` + `NotifyPathUpdate` | value 任意 JSON 值 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 异常 | path 空/非 string | `LOG_WARN` 放弃写入、不通知 | 不抛错、无错误码 | AC-3.1,AC-3.2,AC-3.3 |
| R-4 | 行为 | 分发路径 | 经 `NativeActionRegistry`（非 `NativeFunctionRegistry`），返回空 `JsonValue` | 无返回值、不参与 `as` 回填 | AC-4.1,AC-4.2,AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema + 动作注册 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 数据写入 | C++ UT | UpdateByPath + NotifyPathUpdate |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 非法入参 | C++ UT | 空 path 放弃 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 分发路径 | C++ UT | 动作注册表 vs 函数注册表 |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。`setDataModel` 以 DSL `call` 暴露（inner-native，副作用动作）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `setDataModel`（DSL 数据动作函数） | 既有 | EventHandler 链数据写入 | 经 `A2UIBasicFunctions.extendedCatalogFunctions` 注册 + 动作注册表分发 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/Extended/functions/setDataModel.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`SetDataModelAction(args, ctx)`（动作 handler，`call="setDataModel"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `JsonValue SetDataModelAction(const JsonValue& args, EventHandlerChainExecutor::ExecutionContext& ctx)`（`BuiltInActions.cpp:138`） |
| 返回值 | `JsonValue()`（void，无结果） |
| 开放范围 | DSL 数据动作函数（inner-native） |
| 错误码 | N/A（非法 path 仅 `LOG_WARN`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-4.1,AC-4.2,AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| path | string | 是 | — | 非空 string（JSON Pointer）；schema `required:["path","value"]` |
| value | any | 是 | — | 任意 JSON 值或表达式结果 |
| returnType | string | 否 | `"void"` | 须为 `void` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | path 非空 | UpdateByPath + NotifyPathUpdate | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 2 | path 空/非 string | LOG_WARN 放弃 | AC-3.1,AC-3.2 |
| 3 | 链内分发 | 经 NativeActionRegistry，返回空 | AC-4.1,AC-4.2,AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否（仅运行时内存 DataModel，无持久化）。
- **最低支持版本:** A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20。
- **API 版本号策略:** schema 随版本加载（`schema/Extended/functions/setDataModel.json`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 动作注册表分发 | 经 `NativeActionRegistry`，非 `NativeFunctionRegistry` | AC-4.1,AC-4.3 |
| 无返回值 | 副作用动作，不参与 `as` 回填 | AC-4.2 |
| path 非空前置 | path 空静默放弃，不写不通知 | AC-3.1,AC-3.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 path 不抛异常、不污染模型 | C++ UT | `BuiltInActions.cpp:144-154` |
| 性能 | 单路径写入 + 定向通知，非全量刷新 | C++ UT | `BuiltInActions.cpp:157-158` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 数据写入逻辑设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 纯数据操作 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 是 | DataModel 按 surfaceId 隔离，写操作不跨 Surface | AC-2.1 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | 鸿蒙扩展协议数据操作函数 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: setDataModel 数据动作函数
  作为 生成式 UI 宿主开发者
  我想要 setDataModel 按 path 写入 DataModel 并触发刷新
  以便 驱动绑定组件更新

  Scenario: 正常写入
    Given Surface 存在 DataModel 且存在绑定 "/form/submitted"
    When 以 {"call":"setDataModel","args":{"path":"/form/submitted","value":true}} 执行
    Then DataModel 中 /form/submitted 更新为 true 且绑定组件收到通知

  Scenario: path 为空放弃
    Given 调用 setDataModel
    When args.path 为空串
    Then 不写入、不通知，仅 LOG_WARN
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（setDataModel 数据写入语义；绑定刷新归 07-04-21）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "BuiltInActions SetDataModelAction DataModel UpdateByPath NotifyPathUpdate path value"
  - repo: "GenerativeUI/A2UIRender"
    query: "CatalogActionFunctions setDataModelFunction setDataModel.json isInnerNative"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeActionDispatcher NativeActionRegistry RegisterBuiltInActions setDataModel 分发"
  - repo: "GenerativeUI/Docs"
    query: "setDataModel 数据操作函数 path value DataModel"
```

**关键文档：** `genui/src/main/ets/core/functions/extended/CatalogActionFunctions.ets`、`genui/src/main/cpp/components/actions/BuiltInActions.cpp`、`genui/src/main/cpp/data/DataModel.h`、`reference/functions/extension-functions.md`