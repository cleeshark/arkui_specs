# 特性规格

> Func-07-04-15-Feat-01 If 条件组件：固化 A2UI 扩展协议条件组件 If 的契约——虚拟节点（不产生原生视图）按 `condition` 表达式求值选择 `childrenIf`/`childrenElse` 分支，支持 JS falsy 真值转换、`{{ ... }}` 表达式包裹、全局变量（`$__widthBreakpoint`/`$__colorMode`/`$__dataModel.*`）引用与断点/颜色模式/数据模型驱动的响应式分支切换。基准实现：`@arkui-genius/genui`（A2UIRender，native C++ `IfComponent`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | If 条件组件 |
| 特性编号 | Func-07-04-15-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 扩展协议 catalog `ohos.a2ui.extended.catalog` + 起始 API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-15 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/15-a2ui-extended-conditional-components/design.md` | Baselined |
| 组件实现（C++） | `genui/src/main/cpp/components/extended/if/IfComponent.cpp` | — |
| 组件声明（C++） | `genui/src/main/cpp/components/extended/if/IfComponent.h` | — |
| 工厂注册（C++） | `genui/src/main/cpp/components/extended/ExtendedComponentFactory.cpp` | — |
| 目录声明（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 表达式求值（C++） | `genui/src/main/cpp/expression/EvalResult.h`、`genui/src/main/cpp/expression/EvaluationContext.cpp` | — |
| 断点/颜色链路（ArkTS/C++） | `genui/src/main/ets/core/common/BreakpointUtils.ets`、`genui/src/main/ets/core/base/SurfaceControllerImpl.ets`、`genui/src/main/cpp/SurfaceManager.cpp` | — |
| 协议 Schema | `genui/src/main/resources/rawfile/schema/Extended/components/ExtendedIf.json` | — |
| 文档参考 | `render_docs/reference/extended-components/if.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 条件求值与分支选择

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `condition` 表达式声明条件渲染分支,
**以便** 求值为真时渲染 `childrenIf`、为假时渲染 `childrenElse`。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `condition` 为 `"true"`（或 `"{{ true }}"`） THEN `currentBranch_=true` 且子组件列表为 `childrenIf`（`IfComponent.cpp:295-298,595-607`） | 正常 |
| AC-1.2 | WHEN `condition` 为 `"false"` THEN `currentBranch_=false` 且子组件列表为 `childrenElse`（`IfComponent.cpp:295-298,595-607`） | 正常 |
| AC-1.3 | WHEN `condition` 为裸表达式（非 `{{ }}`，如 `"1 > 0"`） THEN 引擎自动包裹为 `{{ 1 > 0 }}` 求值为真（`IfComponent.cpp:488`） | 正常 |
| AC-1.4 | WHEN `condition` 已包裹 `{{ }}`（如 `"{{ 1 == 2 }}"`） THEN 直接求值为假并选择 else 分支（`IfComponent.cpp:488,510`） | 正常 |
| AC-1.5 | WHEN `condition` 求值为非布尔真值（如 number `42` 或非空字符串 `"hello"`） THEN 按 JS falsy 规则转 true 选择 if 分支（`EvalResult.h:194-210`） | 边界 |
| AC-1.6 | WHEN `condition` 求值为 falsy 非布尔值（number `0`、空字符串 `''`、`null`、`NaN`） THEN 转 false 选择 else 分支并上报 `INVALID_VALUE` 告警（`IfComponent.cpp:163-175,505-508`） | 异常 |

### US-2: condition 属性解析与告警

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎对缺失/非法 `condition` 给出可观测的 schema 告警并回落到安全分支,
**以便** 非法 DSL 不导致渲染崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `condition` 缺失 THEN 上报 `ERROR_CODE_REQUIRED_MISS` 并回落 childrenElse（`IfComponent.cpp:282-285`） | 异常 |
| AC-2.2 | WHEN `condition` 为空字符串 `""` THEN 上报 `ERROR_CODE_INVALID_VALUE` 并回落 childrenElse（`IfComponent.cpp:265-268`） | 边界 |
| AC-2.3 | WHEN `condition` 为 number 字面量（如 `0`/`42`） THEN 强转为表达式按 truthiness 求值（0→else、非 0→if）并上报 `ERROR_CODE_TYPE_MISMATCH`（`IfComponent.cpp:269-272`、`NumberToConditionExpression` `:192-203`） | 边界 |
| AC-2.4 | WHEN `condition` 为 bool/object/array 等非 string/number 类型 THEN 上报 `ERROR_CODE_TYPE_MISMATCH` 并回落 childrenElse（`IfComponent.cpp:273-281`） | 异常 |
| AC-2.5 | WHEN 组件类型查询 THEN `IfComponent::GetType()` 返回 `"If"`（`IfComponent.cpp:238-241`） | 正常 |

### US-3: 全局变量引用

**作为** 生成式 UI 宿主开发者,
**我想要** 在 condition 中引用 `$__widthBreakpoint`/`$__colorMode`/`$__dataModel.*` 全局变量,
**以便** 实现响应式布局与主题/数据驱动的分支切换。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `condition` 为 `$__widthBreakpoint == 'sm'` 且无主题上下文 THEN 默认断点 `"sm"`（`EvaluationContext.cpp:32`）使求值为真 | 正常 |
| AC-3.2 | WHEN `condition` 为 `$__colorMode == 'dark'` 且无主题上下文 THEN 默认颜色模式 `"light"`（`EvaluationContext.cpp:38`）使求值为假选择 else | 正常 |
| AC-3.3 | WHEN `condition` 引用 `$__dataModel.<path>`（如 `$__dataModel.showIf == true`） THEN 从 dataModel 读取路径值参与求值（`EvaluationContext.cpp:40-48`） | 正常 |
| AC-3.4 | WHEN `condition` 引用未知 `__` 前缀全局变量（如 `$__WindowBreakpoint`） THEN 上报 `EVAL_NO_GLOBAL_VARIABLE` 并求值为空串（falsy，选 else）（`EvaluationContext.cpp:50-57`） | 异常 |
| AC-3.5 | WHEN `condition` 引用旧别名 `$__WindowBreakpoint`（大写 W） THEN 视为未定义全局，选 else 分支（`IfComponentTest.cpp:785-799`） | 边界 |

### US-4: 响应式重求值与分支切换

**作为** 生成式 UI 宿主开发者,
**我想要** 断点/颜色模式/数据模型变化时条件自动重求值并切换分支,
**以便** 条件渲染随外部状态变化而更新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 断点变化（`OnConfigChange` 传入 LG 断点）且 condition 引用 `$__widthBreakpoint` THEN 重求值并切换到 lg 分支（`IfComponent.cpp:332-339,417-435`） | 正常 |
| AC-4.2 | WHEN 颜色模式变化（`OnConfigChange` 传入 DARK）且 condition 引用 `$__colorMode` THEN 重求值并切换到 dark 分支（`IfComponent.cpp:332-339,417-435`） | 正常 |
| AC-4.3 | WHEN dataModel 更新命中 condition 依赖（如 `/showIf`） THEN `OnDataUpdate` 触发重求值并切换分支（`IfComponent.cpp:341-369`） | 正常 |
| AC-4.4 | WHEN dataModel 更新不命中 condition 依赖 THEN 不重求值分支不变（`IfComponent.cpp:356-366`） | 边界 |
| AC-4.5 | WHEN property 为依赖的子串（如依赖 `flag` 收到 `flags`） THEN 不重求值（精确/点前缀/`$` 路径前缀匹配才生效）（`IfComponent.cpp:357-363`） | 边界 |
| AC-4.6 | WHEN 已初始化后重求值失败（结果 undefined） THEN 保持当前分支不变（`ReevaluateAndSwitch` 返回 `currentBranch_`）（`IfComponent.cpp:419-423`） | 恢复 |
| AC-4.7 | WHEN 数据模型尚未到达且 condition 引用 `$__dataModel`（首次求值） THEN 延迟求值不告警、保持默认分支，待 `UpdateDataModel` 后重求值切换（`IfComponent.cpp:177-190`） | 恢复 |

### US-5: 分支子组件解析与挂载

**作为** 生成式 UI 宿主开发者,
**我想要** 分支子组件按 id 可靠解析并挂载到正确位置,
**以便** 条件渲染的子树正确显示并复用状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `childrenIf` 非数组（如字符串） THEN 上报 `ERROR_CODE_TYPE_MISMATCH` 并作为空分支处理（`IfComponent.cpp:439-447`） | 异常 |
| AC-5.2 | WHEN `childrenIf`/`childrenElse` 含非字符串元素 THEN 跳过该元素上报 `ERROR_CODE_TYPE_MISMATCH`，其余合法 id 继续挂载（`IfComponent.cpp:450-460`） | 边界 |
| AC-5.3 | WHEN 分支子组件 id 在 components 中不存在 THEN 上报 `ERROR_CODE_UNDEFINED_FIELD` 并跳过该 id（`IfComponent.cpp:638-651`） | 异常 |
| AC-5.4 | WHEN 分支切换 THEN 子组件按 id 复用同一指针（不销毁重建）（`IfComponent.cpp:653-657`、`ReconcileBranchChildren`） | 正常 |
| AC-5.5 | WHEN 同一 id 同时出现在 `childrenIf` 与 `childrenElse` THEN 该子组件恒挂载（两分支共享）（`IfComponentTest.cpp:609-628`） | 边界 |
| AC-5.6 | WHEN If 为虚拟节点挂载子组件 THEN 子组件经最近含原生节点的祖先 InsertChildAt/RemoveChild（passthrough）（`IfComponent.cpp:371-404`） | 正常 |
| AC-5.7 | WHEN 选中分支未声明或为空数组 THEN 不挂载任何子组件（`IfComponent.cpp:600-603`） | 边界 |

### US-6: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** If 以 `component:"If"` 注册到扩展目录并加载 schema,
**以便** DSL 中的 If 组件被正确路由到 native 渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 工厂注册 THEN `ExtendedComponentFactory::RegisterBuiltInComponents` 注册 `"If"` → `IfComponent`（`ExtendedComponentFactory.cpp:126`） | 正常 |
| AC-6.2 | WHEN 目录声明 THEN `A2UIExtendedComponents` 以 `If` 加入 `EXTENDED_NATIVE_COMPONENT_NAMES` 并映射 `ExtendedIf.json`（`A2UIExtendedComponents.ets:44,63`） | 正常 |
| AC-6.3 | WHEN schema 校验 THEN `ExtendedIf.json` 声明 `component.const="If"` 且 `required` 含 `component`/`id`/`condition`（`ExtendedIf.json:8-10,34-38`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1,R-2,R-3 | T-1 | C++ UT | `IfComponentTest.cpp`（should_selectIfBranch_when_conditionTrue 等） |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-4,R-5 | T-1 | C++ UT（告警回调计数） | `IfComponentTest.cpp`（should_dispatchSchemaWarning_*） |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-6 | T-1 | C++ UT + 静态映射比对 | `IfComponentTest.cpp:589-799`、`EvaluationContext.cpp:26-72` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7 | R-7,R-8,R-9 | T-1 | C++ UT | `IfComponentTest.cpp`（should_reevaluate_*/should_switchBranch_*） |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 | R-10,R-11 | T-1 | C++ UT | `IfComponentTest.cpp`（passthrough / reconcile 系列） |
| AC-6.1,AC-6.2,AC-6.3 | R-12 | T-1 | 静态比对 | `ExtendedComponentFactory.cpp:126`、`A2UIExtendedComponents.ets:44,63`、`ExtendedIf.json` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `condition` 求值为 true（布尔或 falsy 规则转真） | 选择 childrenIf 分支，`childListDescriptor` 置 STATIC_IDS if 列表 | 表达式经 `{{ }}` 包裹求值 | AC-1.1,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | `condition` 求值为 false | 选择 childrenElse 分支 | — | AC-1.2 |
| R-3 | 异常 | `condition` 求值为 falsy 非布尔（0/''/null/NaN） | 转 false 选 else 并上报 `INVALID_VALUE` | 仅非布尔 falsy 才告警 | AC-1.6 |
| R-4 | 异常 | `condition` 缺失 | 上报 `REQUIRED_MISS` 并回落 else | 必填属性 | AC-2.1 |
| R-5 | 边界 | `condition` 为空串 / 非 string/number 类型 | 空串→`INVALID_VALUE` 回落 else；bool/object/array→`TYPE_MISMATCH` 回落 else | — | AC-2.2,AC-2.4 |
| R-6 | 行为 | `condition` 引用全局变量（`$__widthBreakpoint`/`$__colorMode`/`$__dataModel.*`） | 按 `EvaluationContext::ResolveVariable` 解析；未知 `__` 全局 → 空串（falsy） | 无主题上下文时断点/颜色回落 `sm`/`light` | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-7 | 行为 | 断点/颜色模式变化（`OnConfigChange`）或依赖命中数据更新（`OnDataUpdate`） | `ReevaluateAndSwitch` 重求值并按结果切换分支 | 依赖匹配：精确 / `变量.` 前缀 / `$path` 前缀 | AC-4.1,AC-4.2,AC-4.3,AC-4.5 |
| R-8 | 恢复 | 已初始化后重求值失败 | 保持当前分支不变（不抖动） | 仅初始化后 | AC-4.6 |
| R-9 | 恢复 | 首次求值引用 `$__dataModel` 且数据未就绪 | 延迟求值，不告警，待数据更新重求值 | 依赖 `HasReceivedDataModelUpdate` | AC-4.7,AC-4.4 |
| R-10 | 异常 | `childrenIf`/`childrenElse` 非数组 / 含非字符串 / id 不存在 | 分别上报 `TYPE_MISMATCH`/`TYPE_MISMATCH`/`UNDEFINED_FIELD` 并跳过无效项 | 其他合法 id 继续挂载 | AC-5.1,AC-5.2,AC-5.3 |
| R-11 | 行为 | 分支切换或挂载 | 子组件按 id 复用同一指针；虚拟节点经祖先 InsertChildAt/RemoveChild | 同 id 双分支恒挂载 | AC-5.4,AC-5.5,AC-5.6,AC-5.7 |
| R-12 | 行为 | 组件类型/目录 | 类型 `"If"`，native 工厂 + 扩展目录注册 + schema 校验 | — | AC-6.1,AC-6.2,AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 条件求值与分支 | C++ UT | 真值转换、`{{}}` 包裹、falsy 告警 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 condition 解析与告警 | C++ UT（告警回调计数） | 缺失/空串/number/非法类型告警码 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 全局变量 | C++ UT + 静态比对 | 断点/颜色/数据模型/未知全局解析 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7 响应式重求值 | C++ UT | OnConfigChange/OnDataUpdate 依赖匹配与失败保持 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 分支挂载 | C++ UT | passthrough 挂载、id 复用、非数组跳过 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3 类型/目录 | 静态比对 | GetType 与工厂/目录/schema 注册 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `CatalogItem`（`A2UIExtendedComponents.allA2UIExtendedComponents()` 内 `If` 项） | 既有 | 扩展目录注册 | 不直接暴露给宿主 | AC-6.2 |
| `ExtendedComponentFactory::RegisterBuiltInComponents()`（`"If"`） | 既有 | native 工厂路由 | 不直接暴露给宿主 | AC-6.1 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**If 条件组件特有属性（descriptor 属性契约，非函数 API）**

| 属性 | 值 |
|------|-----|
| 属性声明 | `IfComponent::GetPrivatePropertyDeclaration`（`IfComponent.cpp:312-322`） |
| 必填属性 | `condition`（schema `ExtendedIf.json:34-38`） |
| 开放范围 | 协议 DSL（无 Public/System API） |
| 错误码 | schema warning `ERROR_CODE_REQUIRED_MISS`/`ERROR_CODE_INVALID_VALUE`/`ERROR_CODE_TYPE_MISMATCH`/`ERROR_CODE_UNDEFINED_FIELD`（`IfComponent.cpp:44-47`） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7,AC-6.1,AC-6.2,AC-6.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| condition | string（Expression） | 是 | — | `{{ ... }}` 或裸表达式；引用 `$__widthBreakpoint`/`$__colorMode`/`$__dataModel.*`；数字字面量按 truthiness 强转 |
| childrenIf | string[] | 否 | `[]` | 每元素为同 components 内组件 id；非字符串元素跳过 |
| childrenElse | string[] | 否 | `[]` | 每元素为同 components 内组件 id；非字符串元素跳过 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `condition:"{{ true }}"` | 挂载 childrenIf | AC-1.1 |
| 2 | `condition:"0"` | 选 else 并告 INVALID_VALUE | AC-1.6 |
| 3 | `condition` 缺失 | REQUIRED_MISS + else | AC-2.1 |
| 4 | `condition:42`（number） | truthiness true 选 if + TYPE_MISMATCH | AC-2.3 |
| 5 | `condition:"$__widthBreakpoint == 'sm'"` | 默认断点 sm → if | AC-3.1 |
| 6 | 断点切到 LG | 重求值切到 lg 分支 | AC-4.1 |
| 7 | dataModel 更新 `/showIf=false` | 切到 else 分支 | AC-4.3 |
| 8 | `childrenIf:"not-array"` | TYPE_MISMATCH + 空分支 | AC-5.1 |
| 9 | `childrenIf:["missingChild"]` | UNDEFINED_FIELD + 跳过 | AC-5.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 catalog `ohos.a2ui.extended.catalog`，起始 API Version 20。
- **API 版本号策略:** 协议 schema 版本由 `SchemaResourceLoader.loadSchema('schema/Extended/components/ExtendedIf.json')` 声明（`A2UIExtendedComponents.ets:145-158`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 虚拟节点 | If 不产生原生视图（`CreateArkUINode` 返回 true），不支持样式/事件/accessibility | AC-5.6 |
| 必填属性 condition | 缺失上报 `REQUIRED_MISS` 并回落 else | AC-2.1 |
| JS falsy 真值语义 | 统一经 `EvalResult::AsBool` 转换 | AC-1.5,AC-1.6 |
| 响应式重求值 | 断点/颜色/数据模型经 `OnConfigChange`/`OnDataUpdate` 驱动 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7 |
| 分支子组件复用 | 按 id 复用指针，切换不销毁 | AC-5.4,AC-5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法/缺省 condition 与分支不抛异常，统一回落 else/空分支 + schema warning | C++ UT | `IfComponent.cpp:254-463` |
| 性能 | 条件求值 + 分支切换为单次表达式求值 + 原生节点增减 | C++ UT | `IfComponent.cpp:417-435` |
| 可测试性 | `IfComponentTest`/`IfComponentIntegrationTest` 覆盖求值、切换、passthrough | C++ UT | `IfComponentTest.cpp`、`IfComponentIntegrationTest.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 有差异（宽度影响 `$__widthBreakpoint` 求值） | 断点分桶 `<320 XS`/`<600 SM`/`<840 MD`/`<1440 LG`/否则 `XL`（`BreakpointUtils.ets:19-33`） | C++ UT + ohosTest | `IfComponentTest.cpp:759-783` |
| 平板 | 有差异（同手机，宽度更大倾向 MD/LG/XL） | 同上 | C++ UT + ohosTest | — |
| 折叠屏 | 有差异（展开/折叠宽度变化触发断点切换重渲染） | 同上 | C++ UT + ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | If 为虚拟节点不支持 accessibility（`IfComponent.cpp:308,310`） | — |
| 大字体 | 否 | If 本身无字号，字体缩放归组件样式域 | — |
| 深色模式 | 是 | `$__colorMode` 参与条件求值，颜色模式切换触发重求值 | AC-3.2,AC-4.2 |
| 多窗口/分屏 | 是 | 窗口宽度变化经断点更新触发 `$__widthBreakpoint` 重求值 | AC-3.1,AC-4.1 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 catalog 绑定（`ohos.a2ui.extended.catalog`） | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 扩展协议 If 条件组件语义对齐 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: If 条件组件
  作为 生成式 UI 宿主开发者
  我想要 通过 condition 表达式声明条件渲染分支
  以便 求值为真渲染 childrenIf、为假渲染 childrenElse

  Scenario: 静态条件选择 if 分支
    Given DSL 组件为 {"component":"If","id":"if1","condition":"{{ true }}","childrenIf":["a"],"childrenElse":["b"]}
    When 应用 descriptor
    Then childListDescriptor.staticChildIds 为 ["a"]

  Scenario: 条件缺失回落 else
    Given DSL 组件为 {"component":"If","id":"if1","childrenIf":["a"],"childrenElse":["b"]}
    When 应用 descriptor
    Then 上报 ERROR_CODE_REQUIRED_MISS 警告且选中 else 分支

  Scenario Outline: 真值转换
    Given DSL 组件为 {"component":"If","id":"if1","condition":<cond>,"childrenIf":["a"],"childrenElse":["b"]}
    When 应用 descriptor
    Then 选中分支为 <branch>

    Examples:
      | cond      | branch |
      | "42"      | if     |
      | "0"       | else   |
      | "''"      | else   |
      | "'hi'"    | if     |
      | "null"    | else   |

  Scenario: 断点切换重渲染
    Given DSL 组件 condition 为 "$__widthBreakpoint == 'lg'"
    And 当前断点为 SM
    When 断点更新为 LG（OnConfigChange）
    Then 分支切换到 childrenIf
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（If 的 condition/childrenIf/childrenElse 契约；样式/事件/accessibility 归不涉及项）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "IfComponent ApplyComponentSpecificAttributes condition childrenIf childrenElse ParseStringArray"
  - repo: "GenerativeUI/A2UIRender"
    query: "IfComponent EvaluateCondition truthiness EvalResult AsBool ShouldReportInvalidFalsyConditionResult"
  - repo: "GenerativeUI/A2UIRender"
    query: "IfComponent ReevaluateAndSwitch OnDataUpdate OnConfigChange SelectBranch ReconcileBranchChildren passthrough"
  - repo: "GenerativeUI/A2UIRender"
    query: "EvaluationContext ResolveVariable __widthBreakpoint __colorMode __dataModel SurfaceManager UpdateBreakpoint NotifyThemeChange"
```

**关键文档：** `genui/src/main/cpp/components/extended/if/IfComponent.cpp`、`genui/src/main/cpp/components/extended/if/IfComponent.h`、`genui/src/main/cpp/expression/EvalResult.h`、`genui/src/main/cpp/expression/EvaluationContext.cpp`、`genui/src/main/cpp/SurfaceManager.cpp`、`genui/src/main/ets/core/base/SurfaceControllerImpl.ets`、`genui/src/main/ets/core/common/BreakpointUtils.ets`、`genui/src/main/resources/rawfile/schema/Extended/components/ExtendedIf.json`、`render_docs/reference/extended-components/if.md`