# 特性规格

> Func-05-12-07-Feat-01 DynamicComponent完整规格：固化 DynamicComponent 创建流程、entryPoint/Worker 传递机制、DynamicComponentRenderer 同进程 Worker 线程渲染、onError 回调与 DCResultCode 错误码、嵌套与数量约束、以及 C-API 动态加载机制的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DynamicComponent完整规格 |
| 特性编号 | Func-05-12-07-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26.0.0+（@systemapi, @stagemodelonly） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | DynamicComponent 创建与选项规格 | 补录 DynamicComponent(options) 创建流程、DynamicOptions { entryPoint, worker, backgroundTransparent?, allowCrossProcessNesting?, allowOccupied? } 解析、DynamicComponentRenderer 在 Worker napi_env 上创建 UIContent 规格 |
| ADDED | onError 回调与错误码规格 | 补录 onError(ErrorCallback) 触发条件与 DCResultCode { DC_NO_ERRORS=0, DC_INTERNAL_ERROR=10011, DC_EXCEED_MAX_NUM_IN_WORKER=10012, DC_ONLY_RUN_ON_SCB=10013, DC_PARAM_ERROE=10014, DC_NOT_SUPPORT_UI_CONTENT_TYPE=10015, DC_WORKER_EXCEED_MAX_NUM=10016 } 错误码规格 |
| ADDED | 嵌套与数量约束规格 | 补录 CheckConstraint（不允许 DC 嵌套 DC）和 CheckDCMaxConstraintInWorker（每个 Worker 最多 4 个 DC）约束规格 |
| ADDED | C-API 动态加载规格 | 补录 DynamicModuleHelper 加载 libarkui_dynamiclayout.z.so 和 ArkUIDynamicLayoutModifier 函数表规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/07-dynamic-component/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 DynamicComponent 并通过 entryPoint/Worker 加载 UI 内容

**作为** 系统应用开发者,
**我想要** 通过 DynamicComponent(options) 创建组件并传入 entryPoint 和 Worker,
**以便** 在宿主页面中通过 Worker 线程渲染独立的 UI 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `DynamicComponent({ entryPoint: 'EntryAbility', worker: myWorker, backgroundTransparent: true })` THEN JSDynamicComponent::Create 解析 options → DynamicModelNG::Create 创建 DynamicNode（DynamicPattern）→ Worker::RegisterCallbackForWorkerEnv 注册回调 → Worker env 就绪后 InitializeDynamicComponent → DynamicComponentRenderer::Create(host, env, IsolatedInfo) → CreateContent 在 Worker napi_env 上创建 UIContent | 正常 |
| AC-1.2 | WHEN entryPoint 为空字符串 THEN DynamicPattern::InitializeDynamicComponent 检测 entryPoint.empty() → HandleErrorCallback(DC_PARAM_ERROE) → onError 回调收到 { code: 10014, name: 'paramError', message: 'Param error' } | 异常 |
| AC-1.3 | WHEN worker (runtime) 为 nullptr THEN DynamicPattern::InitializeDynamicComponent 检测 runtime==nullptr → HandleErrorCallback(DC_PARAM_ERROE) → onError 回调收到 { code: 10014, name: 'paramError', message: 'Param error' } | 异常 |
| AC-1.4 | WHEN backgroundTransparent 未设置 THEN 默认值为 true → DynamicComponentRenderer::SetBackgroundTransparent(true) | 正常 |
| AC-1.5 | WHEN allowCrossProcessNesting 设置为 true THEN UIExtensionConfig.allowCrossProcessNesting = true | 正常 |
| AC-1.6 | WHEN allowOccupied 设置为 true THEN DynamicPattern::SetAllowOccupied(true) → UIExtensionConfig.allowOccupied = true | 正常 |

### US-2: onError 回调与 DCResultCode 错误码

**作为** 系统应用开发者,
**我想要** 通过 onError 回调监听 DynamicComponent 加载错误,
**以便** 在错误发生时根据错误码执行相应处理逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN CheckConstraint 检测宿主 UIContentType 为 DYNAMIC_COMPONENT THEN HandleErrorCallback(DC_NOT_SUPPORT_UI_CONTENT_TYPE=10015) → onError 回调收到 { code: 10015, name: 'notSupportUIContentType', message: 'Not support uIContent type' } | 异常 |
| AC-2.2 | WHEN CheckConstraint 检测非 SceneBoardWindow 且 IsDebugDCEnabled=false THEN HandleErrorCallback(DC_ONLY_RUN_ON_SCB=10013) → onError 回调收到 { code: 10013, name: 'onlyRunOnSCB', message: 'DC only run on SCB' } | 异常 |
| AC-2.3 | WHEN CheckDCMaxConstraintInWorker 检测 Worker 内 DC 数量超过上限 THEN HandleErrorCallback(DC_EXCEED_MAX_NUM_IN_WORKER=10012) → onError 回调收到 { code: 10012, name: 'dcExceedMaxNumInWorker', message: 'Dc exceed max num in the worker' } | 异常 |
| AC-2.4 | WHEN CheckWorkerMaxConstraint 检测 Worker 总数量超过上限 THEN HandleErrorCallback(DC_WORKER_EXCEED_MAX_NUM=10016) → onError 回调收到 { code: 10016, name: 'exceedMaxNum', message: 'Workers exceed Max Num' } | 异常 |
| AC-2.5 | WHEN DynamicComponentRenderer 创建失败或内部错误 THEN HandleErrorCallback(DC_INTERNAL_ERROR=10011) → onError 回调收到 { code: 10011, name: 'internalError', message: 'Internal error' } | 异常 |
| AC-2.6 | WHEN 所有约束检查通过 THEN DC_NO_ERRORS(0) → DynamicComponentRenderer 正常创建并渲染 | 正常 |

### US-3: Worker 线程约束与嵌套限制

**作为** 系统应用开发者,
**我想要** 了解 DynamicComponent 的 Worker 线程约束和嵌套限制,
**以便** 正确规划 DynamicComponent 的使用场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 在已有 DynamicComponent 容器内创建新的 DynamicComponent THEN CheckConstraint 检测宿主 UIContentType=DYNAMIC_COMPONENT → DC_NOT_SUPPORT_UI_CONTENT_TYPE → 不创建 DynamicComponentRenderer | 边界 |
| AC-3.2 | WHEN 在 IsolateComponent 容器内创建 DynamicComponent THEN CheckConstraint 检测宿主 UIContentType=ISOLATED_COMPONENT → DC_NOT_SUPPORT_UI_CONTENT_TYPE → 不创建 DynamicComponentRenderer | 边界 |
| AC-3.3 | WHEN 在 SceneBoardWindow 环境下创建 DynamicComponent THEN CheckConstraint 返回 DC_NO_ERRORS → 正常创建 DynamicComponentRenderer | 正常 |
| AC-3.4 | WHEN 同一 Worker 内已有 4 个 DynamicComponent THEN CheckDCMaxConstraintInWorker 返回 false → DC_EXCEED_MAX_NUM_IN_WORKER → 不创建第 5 个 DynamicComponentRenderer | 边界 |
| AC-3.5 | WHEN 非 SceneBoardWindow 环境 + IsDebugDCEnabled=true THEN CheckConstraint 返回 DC_NO_ERRORS → 允许在非 SCB 环境调试 | 正常 |

### US-4: backgroundTransparent 与 allowOccupied 选项

**作为** 系统应用开发者,
**我想要** 通过 backgroundTransparent 和 allowOccupied 选项控制 DynamicComponent 的渲染行为,
**以便** 调整 DynamicComponent 的透明背景和占位显示策略。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 backgroundTransparent=false THEN DynamicComponentRenderer::SetBackgroundTransparent(false) → DC 渲染背景不透明 | 正常 |
| AC-4.2 | WHEN 设置 backgroundTransparent=true（默认）THEN DynamicComponentRenderer::SetBackgroundTransparent(true) → DC 渲染背景透明 | 正常 |
| AC-4.3 | WHEN 设置 allowOccupied=true THEN DynamicPattern::SetAllowOccupied(true) → DC 允许占位显示 | 正常 |
| AC-4.4 | WHEN 设置 allowOccupied=false（默认）THEN DynamicPattern::SetAllowOccupied(false) → DC 不占位显示 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1, R-2, R-3, R-4, R-5, R-6 | 已有实现 | 代码评审 | `js_dynamic_component.cpp`, `dynamic_pattern.cpp` |
| AC-2.1~2.6 | R-7, R-8, R-9, R-10, R-11, R-12 | 已有实现 | 代码评审 | `dynamic_pattern.cpp:123-152` |
| AC-3.1~3.5 | R-7, R-9, R-13, R-14, R-15 | 已有实现 | 代码评审 | `dynamic_pattern.cpp:155-198` |
| AC-4.1~4.4 | R-16, R-17 | 已有实现 | 代码评审 | `dynamic_pattern.cpp`, `dynamic_component_renderer_impl.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `DynamicComponent(options)` 被调用 | JSDynamicComponent::Create 解析 options → DynamicModelNG::Create(config) 创建 DynamicNode（sessionType=DYNAMIC_COMPONENT=4）→ 设置默认宽高 10vp | 默认宽高为 DYNAMIC_COMPONENT_MIN_WIDTH/HEIGHT(10vp) | AC-1.1 |
| R-2 | 行为 | Worker::RegisterCallbackForWorkerEnv 回调触发 | ContainerScope 设置 instanceId → PostTask 到 UI 线程 → DynamicModelNG::InitializeDynamicComponent(frameNode, '', '', entryPoint, env) | env 为 Worker 的 napi_env | AC-1.1 |
| R-3 | 行为 | DynamicPattern::InitializeDynamicComponent(entryPoint, runtime) | 若 entryPoint 非空且 runtime 非空 → 存 curDynamicInfo_.entryPoint → InitializeRender(runtime) | — | AC-1.1 |
| R-4 | 异常 | entryPoint 为空 | HandleErrorCallback(DC_PARAM_ERROE) → FireOnErrorCallbackOnUI(10014, 'paramError', 'Param error') | entryPoint.empty() 检查在 InitializeDynamicComponent 入口 | AC-1.2 |
| R-5 | 异常 | runtime (Worker napi_env) 为 nullptr | HandleErrorCallback(DC_PARAM_ERROE) → FireOnErrorCallbackOnUI(10014, 'paramError', 'Param error') | worker==nullptr 检查在 JS Bridge 层和 Pattern 层 | AC-1.3 |
| R-6 | 行为 | backgroundTransparent 选项解析 | 默认 true；JSDynamicComponent::Create 解析 backgroundTransparentValue→ToBoolean → UIExtensionConfig.backgroundTransparent | — | AC-1.4 |
| R-7 | 异常 | CheckConstraint: 宿主 UIContentType 为 DYNAMIC_COMPONENT 或 ISOLATED_COMPONENT | HandleErrorCallback(DC_NOT_SUPPORT_UI_CONTENT_TYPE=10015) → 不创建 DynamicComponentRenderer | 不允许 DC 嵌套 DC | AC-2.1, AC-3.1, AC-3.2 |
| R-8 | 异常 | CheckConstraint: 非 SceneBoardWindow + IsDebugDCEnabled=false | HandleErrorCallback(DC_ONLY_RUN_ON_SCB=10013) → 不创建 DynamicComponentRenderer | 仅 SCB 环境允许（debug 模式除外） | AC-2.2 |
| R-9 | 异常 | CheckDCMaxConstraintInWorker: Worker 内 DC 数量超过上限(4) | HandleErrorCallback(DC_EXCEED_MAX_NUM_IN_WORKER=10012) → 不创建 DynamicComponentRenderer | 上限为 4 | AC-2.3, AC-3.4 |
| R-10 | 异常 | CheckWorkerMaxConstraint: Worker 总数量超过上限 | HandleErrorCallback(DC_WORKER_EXCEED_MAX_NUM=10016) → 不创建 DynamicComponentRenderer | — | AC-2.4 |
| R-11 | 异常 | DynamicComponentRenderer 创建失败或内部错误 | HandleErrorCallback(DC_INTERNAL_ERROR=10011) | — | AC-2.5 |
| R-12 | 行为 | 所有约束检查通过 | CheckConstraint → DC_NO_ERRORS → InitializeRender → DynamicComponentRenderer::Create → CreateContent → 正常渲染 | — | AC-2.6 |
| R-13 | 行为 | SceneBoardWindow 环境下创建 DC | CheckConstraint → DC_NO_ERRORS → 正常创建 | — | AC-3.3 |
| R-14 | 行为 | IsDebugDCEnabled=true（persist.ace.debug.dc.enabled=true）+ 非 SCB 环境 | CheckConstraint → DC_NO_ERRORS → 允许调试 | 仅用于开发调试 | AC-3.5 |
| R-15 | 边界 | SessionType = DYNAMIC_COMPONENT = 4 | UIExtensionConfig.sessionType 固定为 DYNAMIC_COMPONENT(4) | 枚举值不可变更 | AC-1.1 |
| R-16 | 行为 | backgroundTransparent 设置 | DynamicComponentRenderer::SetBackgroundTransparent(value) → 控制渲染背景透明度 | 默认 true | AC-4.1, AC-4.2 |
| R-17 | 行为 | allowOccupied 设置 | DynamicPattern::SetAllowOccupied(value) → 控制 DC 占位显示策略 | 默认 false | AC-4.3, AC-4.4 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, R-1, R-2, R-3 | 代码评审 | DynamicComponent 创建流程完整性（JSDynamicComponent→Model→Pattern→Worker→Renderer） |
| VM-2 | AC-1.2, R-4 | 代码评审 | 空 entryPoint 的错误处理 |
| VM-3 | AC-1.3, R-5 | 代码评审 | null Worker 的错误处理 |
| VM-4 | AC-2.1~2.5, R-7~R-11 | 代码评审 | DCResultCode 错误码映射完整性 |
| VM-5 | AC-3.1, AC-3.2, R-7 | 代码评审 | DC 嵌套约束检查 |
| VM-6 | AC-3.4, R-9 | 代码评审 | Worker 内 DC 数量上限检查 |
| VM-7 | AC-4.1~4.4, R-16, R-17 | 代码评审 | backgroundTransparent/allowOccupied 选项解析 |

---

## API 变更分析

### 新增 API

| API 签名 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `DynamicComponent(options: DynamicOptions)` | System (@systemapi) | entryPoint, worker, backgroundTransparent?, allowCrossProcessNesting?, allowOccupied? | DynamicComponentAttribute | 10011-10016 | 创建动态组件 | AC-1.1 |
| `onError(callback: ErrorCallback)` | System (@systemapi) | ErrorCallback (code, name, message) | DynamicComponentAttribute | N/A | 错误回调 | AC-2.1~2.5 |
| `DynamicOptions` | System (@systemapi) | entryPoint: string, worker: Worker | — | — | 创建选项类型 | AC-1.1 |

**C-API (NDK) 接口：**

| Modifier 类型 | 获取方式 | 功能 | 说明 |
|---------------|----------|------|------|
| ArkUIDynamicLayoutModifier | `NodeModifier::GetDynamicLayoutModifier()`（DynamicModuleHelper 动态加载 libarkui_dynamiclayout.z.so） | DynamicComponent 的 C-API 操作入口 | 非 static modifier 直接编译；通过动态加载获取函数表 |

**Static ArkTS API (.d.ets)：**

| API 签名 | 开放范围 | 入参概要 | 返回值 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|----------|---------|
| `DynamicComponent(worker: EAWorker | undefined, entryPoint: string, options?: DynamicComponentOptions)` | System (@systemapi) | workerId, entryPoint, backgroundTransparent? | DynamicComponentAttribute | Static 范式构造重载 1 | AC-1.1 |
| `DynamicComponent(entryPoint: string, options?: DynamicComponentOptions)` | System (@systemapi) | entryPoint, backgroundTransparent? | DynamicComponentAttribute | Static 范式构造重载 2 | AC-1.1 |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `DynamicOptions` | `{ entryPoint: string, worker: Worker, backgroundTransparent?: boolean, allowCrossProcessNesting?: boolean, allowOccupied?: boolean }` | `dynamic_component.d.ts` |
| `DCResultCode` | `{ DC_NO_ERRORS=0, DC_INTERNAL_ERROR=10011, DC_EXCEED_MAX_NUM_IN_WORKER=10012, DC_ONLY_RUN_ON_SCB=10013, DC_PARAM_ERROE=10014, DC_NOT_SUPPORT_UI_CONTENT_TYPE=10015, DC_WORKER_EXCEED_MAX_NUM=10016 }` | `dynamic_pattern.h` |
| `DynamicParam` (static) | `{ workerId: int32_t, entryPoint: string, backgroundTransparent: bool }` | `dynamic_param.h` |
| `IsolatedInfo` | `{ abcPath, resourcePath, entryPoint, registerComponents }` | `dynamic_component_renderer.h` |
| `UIExtensionConfig` | `{ sessionType, backgroundTransparent, allowCrossProcessNesting, allowOccupied }` | `ui_extension_model_ng.h` |

### 变更/废弃 API

无变更/废弃 API。

---

## 接口规格

### 接口定义 — DynamicComponent(options: DynamicOptions)

| 属性 | 值 |
|------|-----|
| 函数签名 | `DynamicComponentAttribute DynamicComponent(DynamicOptions options)` |
| 返回值 | `DynamicComponentAttribute` — 组件属性对象 |
| 开放范围 | System (@systemapi, @stagemodelonly) |
| 错误码 | DCResultCode: 10011-10016 |
| 关联 AC | AC-1.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | DynamicOptions | 是 | — | entryPoint 非空，worker 非 null |
| options.entryPoint | string | 是 | — | 非空字符串；空字符串触发 DC_PARAM_ERROE |
| options.worker | Worker (@ohos.worker) | 是 | — | 非 null；null 触发 DC_PARAM_ERROE |
| options.backgroundTransparent | boolean | 否 | true | 控制渲染背景透明度 |
| options.allowCrossProcessNesting | boolean | 否 | false | 控制跨进程嵌套行为 |
| options.allowOccupied | boolean | 否 | false | 控制占位显示策略 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | entryPoint 非空，worker 非 null，所有约束通过 | 创建 DynamicPattern → Worker RegisterCallback → InitializeDynamicComponent → DynamicComponentRenderer::Create → CreateContent | AC-1.1 |
| 2 | entryPoint 为空字符串 | 不创建 Renderer → onError(DC_PARAM_ERROE=10014) | AC-1.2 |
| 3 | worker 为 null | 不创建 Renderer → onError(DC_PARAM_ERROE=10014) | AC-1.3 |

### 接口定义 — onError(callback: ErrorCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `DynamicComponentAttribute onError(ErrorCallback callback)` |
| 返回值 | `DynamicComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A（回调传递错误码） |
| 关联 AC | AC-2.1~2.5 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | ErrorCallback (error: { code: number, name: string, message: string }) => void | 是 | — | error.code 为 DCResultCode 值 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 宿主 UIContentType 为 DYNAMIC_COMPONENT/ISOLATED_COMPONENT | callback({ code: 10015, name: 'notSupportUIContentType', message: 'Not support uIContent type' }) | AC-2.1 |
| 2 | 非 SCB 环境 + IsDebugDCEnabled=false | callback({ code: 10013, name: 'onlyRunOnSCB', message: 'DC only run on SCB' }) | AC-2.2 |
| 3 | Worker 内 DC 数量超过 4 | callback({ code: 10012, name: 'dcExceedMaxNumInWorker', message: 'Dc exceed max num in the worker' }) | AC-2.3 |
| 4 | Worker 总数量超过上限 | callback({ code: 10016, name: 'exceedMaxNum', message: 'Workers exceed Max Num' }) | AC-2.4 |
| 5 | Renderer 创建失败 | callback({ code: 10011, name: 'internalError', message: 'Internal error' }) | AC-2.5 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 26
- **API 版本号策略:** @since 26.0.0 标注，@systemapi + @stagemodelonly

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| DynamicComponent 为 @systemapi + @stagemodelonly | 仅系统应用在 Stage 模型下可使用 | AC-1.1 |
| 不允许 DC 嵌套 DC（DC_NOT_SUPPORT_UI_CONTENT_TYPE） | CheckConstraint 检查 UIContentType 阻止嵌套 | AC-3.1, AC-3.2 |
| 每个 Worker 最多 4 个 DynamicComponent | CheckDCMaxConstraintInWorker 强制上限 | AC-3.4 |
| 仅 SceneBoardWindow 环境下正常运行（DC_ONLY_RUN_ON_SCB） | 非调试模式下非 SCB 环境拒绝创建 | AC-2.2, AC-3.3 |
| DynamicComponentRenderer 在 Worker napi_env 上创建 UIContent | 同进程多线程渲染，不跨进程 | AC-1.1 |
| C-API 通过 DynamicModuleHelper 动态加载 | libarkui_dynamiclayout.z.so 独立可加载模块 | 全 AC |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | DynamicComponentRenderer 初始化延迟由 Worker 启动时间和 UIContent 创建时间决定，不设量化指标 | 集成测试 | dynamic_pattern.cpp |
| 安全 | @systemapi 限制系统应用使用；@stagemodelonly 限制 Stage 模型 | API 评审 | dynamic_component.d.ts |
| 可靠性 | Worker 线程异常不影响宿主页面渲染 | 单测 | dynamic_pattern.cpp |
| 可测试性 | onError 回调可通过 Mock DynamicComponentRenderer 和约束检查验证 | 单测 | dynamic_pattern.cpp |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | 无差异 | — | 集成测试 | — |
| 折叠屏 | DynamicComponentRenderer 需响应折叠状态变化更新 viewport | 需监听 display 变化 | 集成测试 | dynamic_component_renderer_impl.cpp |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | DynamicPattern 继承 PlatformAccessibilityBase，支持 AccessibilitySessionAdapterIsolatedComponent | AC-1.1 |
| 大字体 | 否 | Worker 线程独立渲染，大字体设置由 Worker 内 UIContent 自行处理 | — |
| 深色模式 | 否 | Worker 线程独立渲染，深色模式由 Worker 内 UIContent 自行处理 | — |
| 多窗口/分屏 | 是 | DynamicComponentRenderer 需响应分屏尺寸变化 | AC-1.1 |
| 多用户 | 否 | DynamicComponent 同进程运行 | — |
| 版本升级 | 否 | API 26 起新组件 | — |
| 生态兼容 | 是 | @systemapi 限制系统应用使用 | AC-1.1 |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：创建/选项/onError/约束/C-API；不做什么：LazyDynamicLayout、Worker 创建方式）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "DynamicPattern CheckConstraint 嵌套约束 DC_NOT_SUPPORT_UI_CONTENT_TYPE 完整逻辑"
  - repo: "openharmony/ace_engine"
    query: "DynamicComponentRenderer 在 Worker napi_env 上创建 UIContent 的完整流程"
  - repo: "openharmony/ace_engine"
    query: "DCResultCode 错误码映射 HandleErrorCallback FireOnErrorCallback"
  - repo: "openharmony/ace_engine"
    query: "DynamicModuleHelper 加载 libarkui_dynamiclayout.z.so ArkUIDynamicLayoutModifier 函数表获取机制"
```

**关键文档：**
- Pattern 层：`frameworks/core/components_ng/pattern/ui_extension/dynamic_component/dynamic_pattern.h`
- Renderer 层：`frameworks/core/common/dynamic_component_renderer.h`
- Renderer 实现：`adapter/ohos/entrance/dynamic_component/dynamic_component_renderer_impl.h`
- JS Bridge：`frameworks/bridge/declarative_frontend/jsview/js_dynamic_component.cpp`
- Static Model：`frameworks/core/components_ng/pattern/ui_extension/dynamic_component/dynamic_model_static.h`
- Dynamic Param：`frameworks/core/components_ng/pattern/ui_extension/dynamic_component/dynamic_param.h`
- C-API bridge：`frameworks/core/components_ng/pattern/dynamiclayout/bridge/dynamic_layout_dynamic_module.h`
