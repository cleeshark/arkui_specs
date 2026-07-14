# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 命名路由跳转与替换 |
| 特性编号 | Func-04-15-03-Feat-01 |
| 所属 Epic | 命名路由（04-15-03） |
| 优先级 | P1 |
| 目标版本 | API 10 ~ API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（命名路由→RouteMap查找+RouterMode分发+UIContext双路径+错误码100004） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | NamedRouterOptions (name: string, params?: Object) | since 10；Stage 模型专用；@crossplatform |
| MODIFIED | NamedRouterOptions.recoverable | since 14 dynamic；默认 true；SysCap ArkUI.Lite |
| MODIFIED | pushNamedRoute 4 overload | since 10；options+callback / options+Promise / options+mode+callback / options+mode+Promise；错误码 401/100001/100003/100004 |
| MODIFIED | replaceNamedRoute 4 overload | since 10；options+callback / options+Promise / options+mode+callback / options+mode+Promise；错误码 401/100001/100004 |
| MODIFIED | RouterMode.Standard/Single | since 9；Standard 常推新实例；Single 栈中同名页移栈顶；与 pushUrl/replaceUrl 共享同一 RouterMode enum |
| MODIFIED | 模块级 @ohos.router.pushNamedRoute/replaceNamedRoute | deprecated since 18→迁移至 UIContext.Router.pushNamedRoute/replaceNamedRoute |
| MODIFIED | UIContext.Router.pushNamedRoute/replaceNamedRoute | since 10 实例级；4 overload；最终调用同一 PageRouterManager |
| MODIFIED | NamedRouterOptions (static) | since 23 static；name: string, params?: Object, recoverable?: boolean |

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `specs/04-common-capability/15-router-mechanism/01-router-management/design.md` (RouterMode 分发策略、错误码体系) |
| SDK Dynamic | `interface/sdk-js/api/@ohos.router.d.ts` (模块级 NamedRouterOptions / pushNamedRoute / replaceNamedRoute) |
| SDK Instance | `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts` (UIContext.Router pushNamedRoute / replaceNamedRoute) |
| SDK Static | `interface/sdk-js/api/@ohos.router.static.d.ets` (NamedRouterOptions static) |
| NAPI Source | `interfaces/napi/kits/router/js_router.cpp` (JSPushNamedRoute / JSReplaceNamedRoute) |
| Core Source | `frameworks/bridge/declarative_frontend/ng/page_router_manager.h/.cpp` (PushPage / ReplacePage / RouteMap lookup) |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: pushNamedRoute 命名路由跳转

作为应用开发者，我想要通过命名路由名称跳转到指定页面，以便使用 RouteMap 中注册的路由名称进行导航而无需硬编码页面 URL。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 调用 router.pushNamedRoute({name:"myPage"}) THEN 在 RouteMap 中查找 name → 获取 page URL → PushPage 新实例入栈 | 正常 |
| AC-1.2 | WHEN 调用 router.pushNamedRoute({name:"myPage"}, callback) THEN 同 AC-1.1 且 callback 在跳转完成后回调 | 正常 |
| AC-1.3 | WHEN 调用 router.pushNamedRoute({name:"myPage"}, RouterMode.Standard) THEN 使用 Standard 模式，常推新实例 | 正常 |
| AC-1.4 | WHEN 调用 router.pushNamedRoute({name:"myPage"}, RouterMode.Single) THEN 使用 Single 模式，栈中同名 URL 页移栈顶 | 正常 |
| AC-1.5 | WHEN 调用 router.pushNamedRoute({name:"myPage"}, RouterMode.Single, callback) THEN 同 AC-1.4 且 callback 回调 | 正常 |
| AC-1.6 | WHEN 调用 UIContext.Router.pushNamedRoute THEN 同模块级行为，通过实例级 delegate 转发到 PageRouterManager | 正常 |
| AC-1.7 | WHEN 栈已满 32 页 THEN pushNamedRoute 抛出 BusinessError 100003（栈溢出） | 异常 |
| AC-1.8 | WHEN RouteMap 中未注册 name THEN pushNamedRoute 抛出 BusinessError 100004（命名路由不存在） | 异常 |
| AC-1.9 | WHEN options 参数缺失或非 object THEN pushNamedRoute 抛出 BusinessError 401 | 异常 |
| AC-1.10 | WHEN options.name 为非 string 类型 THEN pushNamedRoute 抛出 BusinessError 401 | 异常 |
| AC-1.11 | WHEN delegate 未获取 THEN pushNamedRoute 抛出 BusinessError 100001 | 异常 |
| AC-1.12 | WHEN pushNamedRoute 返回 Promise THEN 跳转成功 resolve(void)；跳转失败 reject(BusinessError) | 正常 |

### US-2: replaceNamedRoute 命名路由替换

作为应用开发者，我想要通过命名路由名称替换当前页面，以便在导航时销毁当前页并加载新页面。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 router.replaceNamedRoute({name:"myPage"}) THEN 在 RouteMap 中查找 name → 获取 page URL → ReplacePage 替换栈顶 | 正常 |
| AC-2.2 | WHEN 调用 router.replaceNamedRoute({name:"myPage"}, callback) THEN 同 AC-2.1 且 callback 在替换完成后回调 | 正常 |
| AC-2.3 | WHEN 调用 router.replaceNamedRoute({name:"myPage"}, RouterMode.Standard) THEN Standard 模式替换栈顶 | 正常 |
| AC-2.4 | WHEN 调用 router.replaceNamedRoute({name:"myPage"}, RouterMode.Single) THEN Single 模式替换栈顶 | 正常 |
| AC-2.5 | WHEN 调用 router.replaceNamedRoute({name:"myPage"}, RouterMode.Single, callback) THEN 同 AC-2.4 且 callback 回调 | 正常 |
| AC-2.6 | WHEN 调用 UIContext.Router.replaceNamedRoute THEN 同模块级行为，通过实例级 delegate 转发 | 正常 |
| AC-2.7 | WHEN RouteMap 中未注册 name THEN replaceNamedRoute 抛出 BusinessError 100004 | 异常 |
| AC-2.8 | WHEN options 参数缺失或非 object THEN replaceNamedRoute 抛出 BusinessError 401 | 异常 |
| AC-2.9 | WHEN options.name 为非 string 类型 THEN replaceNamedRoute 抛出 BusinessError 401 | 异常 |
| AC-2.10 | WHEN delegate 未获取 THEN replaceNamedRoute 抛出 BusinessError 100001 | 异常 |
| AC-2.11 | WHEN replaceNamedRoute 返回 Promise THEN 替换成功 resolve(void)；失败 reject(BusinessError) | 正常 |

### US-3: RouterMode 策略与命名路由

作为应用开发者，我想要理解 RouterMode.Standard 和 RouterMode.Single 在命名路由中的行为差异，以便正确选择路由模式。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN pushNamedRoute mode=Standard THEN 无论栈中是否存在同名 URL 页，始终推入新实例 | 正常 |
| AC-3.2 | WHEN pushNamedRoute mode=Single 且栈中存在同名 URL 页 THEN 将栈中最近的同名 URL 页移至栈顶（PopPageTo+PushPage） | 正常 |
| AC-3.3 | WHEN pushNamedRoute mode=Single 且栈中不存在同名 URL 页 THEN 按 Standard 模式推入新实例 | 正常 |
| AC-3.4 | WHEN replaceNamedRoute mode=Standard THEN 替换栈顶页为新实例 | 正常 |
| AC-3.5 | WHEN replaceNamedRoute mode=Single 且栈中存在同名 URL 页 THEN 替换栈顶为栈中同名 URL 页 | 正常 |
| AC-3.6 | WHEN 不指定 RouterMode THEN 默认使用 RouterMode.Standard | 正常 |
| AC-3.7 | WHEN Single 模式查找同名 URL 页 THEN URL 来自 RouteMapItem 的 action/src 字段解析后的完整页面路径 | 正常 |

### US-4: 参数传递与 recoverable

作为应用开发者，我想要通过 NamedRouterOptions.params 传递参数到目标页面，并通过 recoverable 控制页面栈恢复策略。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN pushNamedRoute({name:"myPage", params:{key:"value"}}) THEN 目标页面通过 getParams() 获取 {key:"value"} | 正常 |
| AC-4.2 | WHEN pushNamedRoute params 为 undefined THEN 目标页面 getParams() 返回空 Object | 边界 |
| AC-4.3 | WHEN replaceNamedRoute({name:"myPage", params:{key:"value"}}) THEN 替换页通过 getParams() 获取 {key:"value"} | 正常 |
| AC-4.4 | WHEN pushNamedRoute({name:"myPage", recoverable:true}) THEN 页面推入时标记 recoverable_=true（默认行为） | 正常 |
| AC-4.5 | WHEN pushNamedRoute({name:"myPage", recoverable:false}) THEN 页面推入时标记 recoverable_=false；应用销毁后不恢复该页 | 正常 |
| AC-4.6 | WHEN 不指定 recoverable THEN 默认 recoverable=true | 正常 |
| AC-4.7 | WHEN recoverable=false 的页面被 back 弹出 THEN 不推入 restorePageRouterStack_（直接销毁） | 边界 |

### US-5: UIContext.Router 命名路由双路径

作为应用开发者，我想要了解模块级与实例级命名路由 API 的差异，以便在多 Ability 场景下正确使用实例级路由。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 调用 @ohos.router.pushNamedRoute (模块级) THEN deprecated since 18；最终调用当前 Stage Activity 的 PageRouterManager | 正常 |
| AC-5.2 | WHEN 调用 this.getUIContext().getRouter().pushNamedRoute (实例级) THEN 绑定到特定 UIAbility Context 的 PageRouterManager | 正常 |
| AC-5.3 | WHEN 调用 @ohos.router.replaceNamedRoute (模块级) THEN deprecated since 18；同 AC-5.1 | 正常 |
| AC-5.4 | WHEN 调用 this.getUIContext().getRouter().replaceNamedRoute (实例级) THEN 绑定到特定 UIAbility Context | 正常 |
| AC-5.5 | WHEN 多 Ability 场景 THEN 模块级作用于当前 Activity 全局栈；实例级绑定特定 Ability Context 栈 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.12 | R-1 ~ R-12 | TASK-01 | 单测 pushNamedRoute | `js_router.cpp:JSPushNamedRoute` |
| AC-2.1 ~ AC-2.11 | R-13 ~ R-22 | TASK-01 | 单测 replaceNamedRoute | `js_router.cpp:JSReplaceNamedRoute` |
| AC-3.1 ~ AC-3.7 | R-23 ~ R-29 | TASK-01 | 单测 RouterMode | `page_router_manager.cpp:PushPage/ReplacePage` |
| AC-4.1 ~ AC-4.7 | R-30 ~ R-36 | TASK-01 | 单测 params/recoverable | `page_router_manager.cpp` |
| AC-5.1 ~ AC-5.5 | R-37 ~ R-41 | TASK-01 | 双路径对比 | `js_router.cpp` + `page_router_manager.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | pushNamedRoute(options): Promise | RouteMap 查找 name → 获取 page URL → PushPage(RouterMode::STANDARD) → Promise resolve(void) | 默认 RouterMode.Standard | AC-1.1, AC-1.12 |
| R-2 | 行为 | pushNamedRoute(options, callback) | 同 R-1 + AsyncCallback 回调 | callback 在跳转完成时调用 | AC-1.2 |
| R-3 | 行为 | pushNamedRoute(options, mode): Promise | RouteMap 查找 name → PushPage(mode) → Promise | mode 决定 Standard/Single | AC-1.3, AC-1.4 |
| R-4 | 行为 | pushNamedRoute(options, mode, callback) | 同 R-3 + AsyncCallback 回调 | 3 参数重载 | AC-1.5 |
| R-5 | 行为 | UIContext.Router.pushNamedRoute | 通过实例级 delegate 转发到 PageRouterManager | 多 Ability 场景隔离栈 | AC-1.6 |
| R-6 | 异常 | 栈满 32 页 | 抛出 BusinessError 100003 ("Page stack error. Too many pages are pushed.") | pageRouterStack_.size() >= MAX_ROUTER_STACK_SIZE(32) | AC-1.7 |
| R-7 | 异常 | RouteMap 中 name 不存在 | 抛出 BusinessError 100004 ("Named route error. The named route does not exist.") | FA model: route_map.json; Stage model: module.json5 routerMap | AC-1.8 |
| R-8 | 异常 | options 参数缺失或非 object | 抛出 BusinessError 401 | napi_typeof != napi_object → NapiThrow | AC-1.9 |
| R-9 | 异常 | options.name 非 string | 抛出 BusinessError 401 | napi_typeof != napi_string → NapiThrow | AC-1.10 |
| R-10 | 异常 | delegate 未获取 | 抛出 BusinessError 100001 ("Internal error / UI execution context not found") | NAPI 层 NapiThrow | AC-1.11 |
| R-11 | 行为 | pushNamedRoute Promise 成功 | resolve(void) | 无额外返回值 | AC-1.12 |
| R-12 | 行为 | pushNamedRoute Promise 失败 | reject(BusinessError) | BusinessError 包含 code + message | AC-1.12 |
| R-13 | 行为 | replaceNamedRoute(options): Promise | RouteMap 查找 name → 获取 page URL → ReplacePage(RouterMode::STANDARD) → Promise | 替换栈顶，当前页销毁 | AC-2.1, AC-2.11 |
| R-14 | 行为 | replaceNamedRoute(options, callback) | 同 R-13 + AsyncCallback 回调 | callback 在替换完成时调用 | AC-2.2 |
| R-15 | 行为 | replaceNamedRoute(options, mode): Promise | RouteMap 查找 name → ReplacePage(mode) → Promise | mode 决定 Standard/Single | AC-2.3, AC-2.4 |
| R-16 | 行为 | replaceNamedRoute(options, mode, callback) | 同 R-15 + AsyncCallback 回调 | 3 参数重载 | AC-2.5 |
| R-17 | 行为 | UIContext.Router.replaceNamedRoute | 通过实例级 delegate 转发到 PageRouterManager | 同 pushNamedRoute 实例级路径 | AC-2.6 |
| R-18 | 异常 | RouteMap 中 name 不存在(replaceNamedRoute) | 抛出 BusinessError 100004 | 同 R-7 | AC-2.7 |
| R-19 | 异常 | options 参数缺失或非 object(replaceNamedRoute) | 抛出 BusinessError 401 | 同 R-8 | AC-2.8 |
| R-20 | 异常 | options.name 非 string(replaceNamedRoute) | 抛出 BusinessError 401 | 同 R-9 | AC-2.9 |
| R-21 | 异常 | delegate 未获取(replaceNamedRoute) | 抛出 BusinessError 100001 | 同 R-10 | AC-2.10 |
| R-22 | 行为 | replaceNamedRoute 不抛 100003 | replaceNamedRoute 替换栈顶，栈大小不变，不触发栈溢出 | 与 pushNamedRoute 差异 | AC-2.1 |
| R-23 | 行为 | RouterMode.Standard + pushNamedRoute | 常推新实例，不检查栈中同名 URL | pageRouterStack_.push_back(pageInfo) | AC-3.1 |
| R-24 | 行为 | RouterMode.Single + pushNamedRoute 且栈中存在同名 URL | PopPageTo(index) + PushPage → 移栈顶 | URL 来自 RouteMapItem 的 action/src 解析 | AC-3.2, AC-3.7 |
| R-25 | 行为 | RouterMode.Single + pushNamedRoute 且栈中不存在同名 URL | 按 Standard 模式推入 | fallback 行为 | AC-3.3 |
| R-26 | 行为 | RouterMode.Standard + replaceNamedRoute | 弹出栈顶 → 推入新实例 | 当前页销毁 | AC-3.4 |
| R-27 | 行为 | RouterMode.Single + replaceNamedRoute 且栈中存在同名 URL | 替换栈顶为栈中同名 URL 页 | Single 模式下 replace 行为 | AC-3.5 |
| R-28 | 行为 | 不指定 RouterMode | 默认 RouterMode.Standard | NAPI 参数数量=1 或 2(options+callback) 时默认 Standard | AC-3.6 |
| R-29 | 行为 | Single 模式 URL 匹配 | URL 来自 RouteMapItem 的 action/src 字段解析后的完整页面路径 | FA model: src; Stage model: action; buildType 判断 | AC-3.7 |
| R-30 | 行为 | pushNamedRoute params 传递 | params 写入 PageInfo.params_；目标页面通过 getParams() 获取 | params?: Object 可选 | AC-4.1 |
| R-31 | 边界 | params 为 undefined | 目标页面 getParams() 返回空 Object | NAPI ParseJSONParams 处理 | AC-4.2 |
| R-32 | 行为 | replaceNamedRoute params 传递 | params 写入替换页 PageInfo.params_ | 同 pushNamedRoute params 机制 | AC-4.3 |
| R-33 | 行为 | recoverable=true (since 14) | PageInfo.SetRecoverable(true)；应用销毁后恢复栈顶页 | 默认值 true | AC-4.4, AC-4.6 |
| R-34 | 行为 | recoverable=false (since 14) | PageInfo.SetRecoverable(false)；应用销毁后不恢复该页 | SysCap: SystemCapability.ArkUI.ArkUI.Lite | AC-4.5 |
| R-35 | 边界 | recoverable=false + back | 页面不推入 restorePageRouterStack_；直接销毁 | 与 recoverable=true 的 back 行为差异 | AC-4.7 |
| R-36 | 行为 | 默认 recoverable=true | 不指定 recoverable 时 SetRecoverable(true) | since 14 引入 | AC-4.6 |
| R-37 | 行为 | 模块级 pushNamedRoute deprecated since 18 | @ohos.router.pushNamedRoute 标记 @deprecated since 18 → @useinstead ohos.arkui.UIContext.Router#pushNamedRoute | 存量代码需迁移 | AC-5.1 |
| R-38 | 行为 | 实例级 UIContext.Router.pushNamedRoute | 绑定特定 UIAbility Context 的 PageRouterManager | 多 Ability 隔离 | AC-5.2 |
| R-39 | 行为 | 模块级 replaceNamedRoute deprecated since 18 | @ohos.router.replaceNamedRoute 标记 @deprecated since 18 → @useinstead ohos.arkui.UIContext.Router#replaceNamedRoute | 存量代码需迁移 | AC-5.3 |
| R-40 | 行为 | 实例级 UIContext.Router.replaceNamedRoute | 绑定特定 UIAbility Context 的 PageRouterManager | 多 Ability 隔离 | AC-5.4 |
| R-41 | 行为 | 多 Ability 路由栈隔离 | 模块级作用于当前 Activity 全局栈；实例级绑定特定 Ability Context | 两条路径最终调用同一 PageRouterManager 类但不同实例 | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 ~ R-4 | 单测 pushNamedRoute 4 overload | RouteMap 查找→PushPage 调用路径 |
| VM-2 | R-5, R-38, R-40 | 单测 UIContext.Router | 实例级 delegate 转发 |
| VM-3 | R-6, R-7, R-8, R-9, R-10 | 单测 pushNamedRoute 错误码 | 401/100001/100003/100004 |
| VM-4 | R-13 ~ R-16 | 单测 replaceNamedRoute 4 overload | RouteMap 查找→ReplacePage 调用路径 |
| VM-5 | R-18, R-19, R-20, R-21 | 单测 replaceNamedRoute 错误码 | 401/100001/100004 |
| VM-6 | R-23 ~ R-29 | 单测 RouterMode 分发 | Standard vs Single 行为差异 |
| VM-7 | R-30 ~ R-36 | 单测 params/recoverable | 参数传递与恢复标记 |
| VM-8 | R-37 ~ R-41 | 单测双路径对比 | deprecated 标记与实例级路径 |

## API 变更分析

### 新增 API

> 已有实现补录，无新增 API。以下列出当前全部 Public API 签名供 spec 参考。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| pushNamedRoute(options, callback) | Public (since 10, deprecated since 18) | NamedRouterOptions + AsyncCallback | void | 401/100001/100003/100004 | 命名路由跳转+回调 | AC-1.1, AC-1.2 |
| pushNamedRoute(options) | Public (since 10, deprecated since 18) | NamedRouterOptions | Promise<void> | 401/100001/100003/100004 | 命名路由跳转+Promise | AC-1.1, AC-1.12 |
| pushNamedRoute(options, mode, callback) | Public (since 10, deprecated since 18) | NamedRouterOptions + RouterMode + AsyncCallback | void | 401/100001/100003/100004 | 命名路由跳转+模式+回调 | AC-1.3~AC-1.5 |
| pushNamedRoute(options, mode) | Public (since 10, deprecated since 18) | NamedRouterOptions + RouterMode | Promise<void> | 401/100001/100003/100004 | 命名路由跳转+模式+Promise | AC-1.3, AC-1.4 |
| replaceNamedRoute(options, callback) | Public (since 10, deprecated since 18) | NamedRouterOptions + AsyncCallback | void | 401/100001/100004 | 命名路由替换+回调 | AC-2.1, AC-2.2 |
| replaceNamedRoute(options) | Public (since 10, deprecated since 18) | NamedRouterOptions | Promise<void> | 401/100001/100004 | 命名路由替换+Promise | AC-2.1, AC-2.11 |
| replaceNamedRoute(options, mode, callback) | Public (since 10, deprecated since 18) | NamedRouterOptions + RouterMode + AsyncCallback | void | 401/100001/100004 | 命名路由替换+模式+回调 | AC-2.3~AC-2.5 |
| replaceNamedRoute(options, mode) | Public (since 10, deprecated since 18) | NamedRouterOptions + RouterMode | Promise<void> | 401/100001/100004 | 命名路由替换+模式+Promise | AC-2.3, AC-2.4 |
| UIContext.Router.pushNamedRoute (4 overload) | Public (since 10/11) | 同模块级 | 同模块级 | 401/100001/100003/100004 | 实例级命名路由跳转 | AC-1.6 |
| UIContext.Router.replaceNamedRoute (4 overload) | Public (since 10/11) | 同模块级 | 同模块级 | 401/100001/100004 | 实例级命名路由替换 | AC-2.6 |
| NamedRouterOptions | Public (since 10) | name: string; params?: Object; recoverable?: boolean | — | — | 命名路由选项 | AC-4.1~AC-4.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| @ohos.router.pushNamedRoute (4 overload) | 废弃(since 18) | 模块级命名路由跳转 | 使用 UIContext.Router.pushNamedRoute | AC-5.1 |
| @ohos.router.replaceNamedRoute (4 overload) | 废弃(since 18) | 模块级命名路由替换 | 使用 UIContext.Router.replaceNamedRoute | AC-5.3 |
| NamedRouterOptions.recoverable | 新增(since 14) | 命名路由页面恢复标记 | since 14 默认 true | AC-4.4, AC-4.5 |

## 接口规格

### 接口定义

**NamedRouterOptions**

| 属性 | 值 |
|------|-----|
| 函数签名 | `interface NamedRouterOptions { name: string; params?: Object; recoverable?: boolean; }` |
| 开放范围 | Public (since 10, recoverable since 14, static since 23) |
| 错误码 | N/A |
| 关联 AC | AC-4.1 ~ AC-4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| name | string | 是 | 无 | 命名路由名称；对应 RouteMap 中注册的 name |
| params | Object | 否 | undefined | 传递到目标页面的数据；目标页通过 getParams() 获取 |
| recoverable | boolean | 否 | true | since 14；控制应用销毁后页面栈恢复；SysCap: ArkUI.Lite |

---

**pushNamedRoute(options, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pushNamedRoute(options: NamedRouterOptions, callback: AsyncCallback<void>): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 10, deprecated since 18→UIContext.Router.pushNamedRoute) |
| 错误码 | 401 (参数), 100001 (内部), 100003 (栈溢出), 100004 (命名路由不存在) |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | NamedRouterOptions | 是 | 无 | options.name 必填 string |
| callback | AsyncCallback<void> | 是 | 无 | 跳转完成回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | RouteMap 查找 name → PushPage(Standard) → callback(void) | AC-1.2 |
| 2 | name 不存在于 RouteMap | 抛出 BusinessError 100004 | AC-1.8 |
| 3 | options 非 object | 抛出 BusinessError 401 | AC-1.9 |
| 4 | name 非 string | 抛出 BusinessError 401 | AC-1.10 |
| 5 | 栈满 32 | 抛出 BusinessError 100003 | AC-1.7 |
| 6 | delegate 未获取 | 抛出 BusinessError 100001 | AC-1.11 |

---

**pushNamedRoute(options)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pushNamedRoute(options: NamedRouterOptions): Promise<void>` |
| 返回值 | `Promise<void>` |
| 开放范围 | Public (since 10, deprecated since 18→UIContext.Router.pushNamedRoute) |
| 错误码 | 401, 100001, 100003, 100004 |
| 关联 AC | AC-1.1, AC-1.12 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | NamedRouterOptions | 是 | 无 | 同上 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | RouteMap 查找 name → PushPage(Standard) → resolve(void) | AC-1.1 |
| 2 | 跳转失败 | reject(BusinessError) | AC-1.12 |
| 3 | 默认 RouterMode | 无 mode 参数时使用 Standard | AC-3.6 |

---

**pushNamedRoute(options, mode, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pushNamedRoute(options: NamedRouterOptions, mode: RouterMode, callback: AsyncCallback<void>): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 10, deprecated since 18) |
| 错误码 | 401, 100001, 100003, 100004 |
| 关联 AC | AC-1.3 ~ AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | NamedRouterOptions | 是 | 无 | 同上 |
| mode | RouterMode (Standard/Single) | 是 | 无 | 决定路由模式 |
| callback | AsyncCallback<void> | 是 | 无 | 跳转完成回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | mode=Standard | 常推新实例 → callback(void) | AC-1.3 |
| 2 | mode=Single + 栈中存在同名 URL | 移栈顶 → callback(void) | AC-1.4, AC-3.2 |
| 3 | mode=Single + 栈中不存在同名 URL | 按 Standard 推入 → callback(void) | AC-1.4, AC-3.3 |

---

**pushNamedRoute(options, mode)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pushNamedRoute(options: NamedRouterOptions, mode: RouterMode): Promise<void>` |
| 返回值 | `Promise<void>` |
| 开放范围 | Public (since 10, deprecated since 18) |
| 错误码 | 401, 100001, 100003, 100004 |
| 关联 AC | AC-1.3, AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | NamedRouterOptions | 是 | 无 | 同上 |
| mode | RouterMode | 是 | 无 | Standard/Single |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | mode=Standard | PushPage(Standard) → resolve(void) | AC-3.1 |
| 2 | mode=Single + 栈中同名 URL | PopPageTo+PushPage → resolve(void) | AC-3.2 |
| 3 | mode=Single + 栈中无同名 URL | Standard 推入 → resolve(void) | AC-3.3 |

---

**replaceNamedRoute(options, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `replaceNamedRoute(options: NamedRouterOptions, callback: AsyncCallback<void>): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 10, deprecated since 18→UIContext.Router.replaceNamedRoute) |
| 错误码 | 401, 100001, 100004 |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | NamedRouterOptions | 是 | 无 | 同上 |
| callback | AsyncCallback<void> | 是 | 无 | 替换完成回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | RouteMap 查找 name → ReplacePage(Standard) → callback(void) | AC-2.2 |
| 2 | name 不存在 | 抛出 BusinessError 100004 | AC-2.7 |
| 3 | options 非 object | 抛出 BusinessError 401 | AC-2.8 |
| 4 | name 非 string | 抛出 BusinessError 401 | AC-2.9 |
| 5 | delegate 未获取 | 抛出 BusinessError 100001 | AC-2.10 |

---

**replaceNamedRoute(options)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `replaceNamedRoute(options: NamedRouterOptions): Promise<void>` |
| 返回值 | `Promise<void>` |
| 开放范围 | Public (since 10, deprecated since 18) |
| 错误码 | 401, 100001, 100004 |
| 关联 AC | AC-2.1, AC-2.11 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | NamedRouterOptions | 是 | 无 | 同上 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | ReplacePage(Standard) → resolve(void) | AC-2.1 |
| 2 | 替换失败 | reject(BusinessError) | AC-2.11 |
| 3 | 不抛 100003 | replace 不增加栈大小 | AC-2.1 |

---

**replaceNamedRoute(options, mode, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `replaceNamedRoute(options: NamedRouterOptions, mode: RouterMode, callback: AsyncCallback<void>): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 10, deprecated since 18) |
| 错误码 | 401, 100001, 100004 |
| 关联 AC | AC-2.3 ~ AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | NamedRouterOptions | 是 | 无 | 同上 |
| mode | RouterMode | 是 | 无 | Standard/Single |
| callback | AsyncCallback<void> | 是 | 无 | 替换完成回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | mode=Standard | ReplacePage(Standard) → callback(void) | AC-2.3, AC-3.4 |
| 2 | mode=Single | ReplacePage(Single) → callback(void) | AC-2.4, AC-2.5 |

---

**replaceNamedRoute(options, mode)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `replaceNamedRoute(options: NamedRouterOptions, mode: RouterMode): Promise<void>` |
| 返回值 | `Promise<void>` |
| 开放范围 | Public (since 10, deprecated since 18) |
| 错误码 | 401, 100001, 100004 |
| 关联 AC | AC-2.3, AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | NamedRouterOptions | 是 | 无 | 同上 |
| mode | RouterMode | 是 | 无 | Standard/Single |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | mode=Standard | ReplacePage(Standard) → resolve(void) | AC-3.4 |
| 2 | mode=Single + 栈中同名 URL | 替换栈顶为同名 URL 页 → resolve(void) | AC-3.5 |

---

**RouterMode**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enum RouterMode { Standard, Single }` |
| 开放范围 | Public (since 9) |
| 错误码 | N/A |
| 关联 AC | AC-3.1 ~ AC-3.7 |

**枚举值约束**

| 枚举值 | 值 | 说明 | 约束 |
|--------|-----|------|------|
| Standard | 0 | 常推新实例 | pushNamedRoute/replaceNamedRoute 默认 |
| Single | 1 | 栈中同名 URL 页移栈顶；不存在时 fallback Standard | URL 来自 RouteMapItem |

---

**UIContext.Router.pushNamedRoute / replaceNamedRoute**

| 属性 | 值 |
|------|-----|
| 函数签名 | 同模块级 4 overload（pushNamedRoute + replaceNamedRoute） |
| 开放范围 | Public (since 10/11) |
| 错误码 | 同模块级（pushNamedRoute: 401/100001/100003/100004；replaceNamedRoute: 401/100001/100004） |
| 关联 AC | AC-5.2, AC-5.4 |

**行为差异**

| # | 对比维度 | 模块级 | 实例级 | 关联 AC |
|---|----------|--------|--------|---------|
| 1 | deprecated | since 18 | 无 deprecated | AC-5.1, AC-5.3 |
| 2 | 作用域 | 当前 Stage Activity 全局栈 | 特定 UIAbility Context 栈 | AC-5.5 |
| 3 | 核心调用 | 同一 PageRouterManager | 同一 PageRouterManager（不同实例） | AC-5.2 |

## 兼容性声明

- **已有 API 行为变更:** 否，所有行为均为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10
- **API 版本号策略:** NamedRouterOptions since 10 (模块级/实例级)；recoverable since 14；模块级 deprecated since 18；static since 23

### 命名路由配置模型差异

| 配置维度 | FA 模型 | Stage 模型 |
|----------|---------|------------|
| 配置文件 | `route_map.json` | `module.json5` routerMap 字段 |
| RouteMapItem 字段 | name, src(page path), buildType | name, action(page path), buildType |
| 配置位置 | 应用根目录 resources/base/profile/ | module.json5 内 routerMap 数组 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| RouteMap 查找前置 | pushNamedRoute/replaceNamedRoute 先查 RouteMap 获取 page URL，再调用 PushPage/ReplacePage | AC-1.1, AC-2.1 |
| RouterMode 共享 | pushNamedRoute/replaceNamedRoute 使用同一 RouterMode enum (Standard/Single)，行为与 pushUrl/replaceUrl 一致 | AC-3.1~AC-3.7 |
| 栈上限 32 | pushNamedRoute 栈满抛 100003；replaceNamedRoute 不增加栈大小，不抛 100003 | AC-1.7, R-22 |
| 100004 命名路由不存在 | name 在 RouteMap 中无匹配项；FA 和 Stage 模型各自查找配置文件 | AC-1.8, AC-2.7 |
| 模块级 deprecated since 18 | pushNamedRoute/replaceNamedRoute 模块级标记 deprecated→UIContext.Router | AC-5.1, AC-5.3 |
| recoverable since 14 | NamedRouterOptions.recoverable 默认 true；SysCap ArkUI.Lite | AC-4.4~AC-4.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | RouteMap 查找 < 1ms | 单测计时 | hash map 查找 O(1) |
| 安全 | 无权限要求 | SDK .d.ts 验证 | SysCap: SystemCapability.ArkUI.ArkUI.Full |
| 可靠性 | 错误码体系完整(401/100001/100003/100004) | 错误码覆盖 | @ohos.router.d.ts JSDoc |
| 可测试性 | RouteMap Mock 可隔离 | Mock 策略 | 配置文件注入 |
| 自动化维测 | 栈操作日志 | hilog | TAG_LOGI(AceLogTag::ACE_ROUTER) |
| 定界定位 | NAPI 错误码映射 | 错误码检查 | NapiThrow + ERROR_CODE_* |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 栈上限 32 | XTS | @crossplatform since 10/11 |
| 平板 | 无差异 | 同上 | XTS | @crossplatform |
| 折叠屏 | 无差异 | 同上 | XTS | @crossplatform |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 命名路由跳转与替换无无障碍特殊处理 | — |
| 大字体 | 否 | 路由操作无 UI 样式影响 | — |
| 深色模式 | 否 | 路由操作无 UI 样式影响 | — |
| 多窗口/分屏 | 是 | UIContext.Router 绑定特定 Ability Context，多窗口各自独立栈 | AC-5.5 |
| 多用户 | 否 | Router 为单 Ability 内栈管理 | — |
| 版本升级 | 是 | 模块级 deprecated since 18→迁移至 UIContext.Router | AC-5.1, AC-5.3 |
| 生态兼容 | 是 | FA model route_map.json vs Stage model module.json5 配置差异 | AC-1.8 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 命名路由跳转与替换
  作为应用开发者
  我想要通过命名路由名称跳转或替换页面
  以便使用 RouteMap 注册的路由名称进行导航

  Scenario: pushNamedRoute Standard 模式跳转
    Given RouteMap 中注册了名为 "myPage" 的路由
    And 路由栈中有 2 个页面
    When 调用 router.pushNamedRoute({name: "myPage"})
    Then 在 RouteMap 中查找 "myPage" 获取 page URL
    And 按 Standard 模式推入新实例到栈顶
    And 栈大小变为 3

  Scenario: pushNamedRoute Single 模式同名页移栈顶
    Given RouteMap 中注册了名为 "myPage" 的路由，对应 URL "pages/myPage"
    And 路由栈中已存在 "pages/myPage" 页面
    When 调用 router.pushNamedRoute({name: "myPage"}, RouterMode.Single)
    Then 将栈中最近的 "pages/myPage" 页面移至栈顶
    And 栈大小不变

  Scenario: pushNamedRoute Single 模式无同名页 fallback
    Given RouteMap 中注册了名为 "newPage" 的路由
    And 路由栈中不存在 "newPage" 对应 URL 的页面
    When 调用 router.pushNamedRoute({name: "newPage"}, RouterMode.Single)
    Then 按 Standard 模式推入新实例

  Scenario: pushNamedRoute 栈溢出
    Given 路由栈已满 32 页
    When 调用 router.pushNamedRoute({name: "myPage"})
    Then 抛出 BusinessError 100003

  Scenario: pushNamedRoute 命名路由不存在
    Given RouteMap 中未注册 "unknownRoute"
    When 调用 router.pushNamedRoute({name: "unknownRoute"})
    Then 抛出 BusinessError 100004

  Scenario Outline: pushNamedRoute 参数校验
    When 调用 pushNamedRoute(options)
    Then 抛出 BusinessError <code>

    Examples:
      | condition | code |
      | options 为 undefined | 401 |
      | options.name 为数字 | 401 |
      | delegate 未获取 | 100001 |

  Scenario: replaceNamedRoute Standard 模式替换
    Given RouteMap 中注册了名为 "myPage" 的路由
    And 路由栈中有 2 个页面
    When 调用 router.replaceNamedRoute({name: "myPage"})
    Then 替换栈顶页为 "myPage" 对应页面
    And 栈大小保持 2

  Scenario: replaceNamedRoute 命名路由不存在
    Given RouteMap 中未注册 "unknownRoute"
    When 调用 router.replaceNamedRoute({name: "unknownRoute"})
    Then 抛出 BusinessError 100004

  Scenario: pushNamedRoute params 传递
    Given RouteMap 中注册了名为 "detail" 的路由
    When 调用 router.pushNamedRoute({name: "detail", params: {id: 42}})
    Then 目标页面通过 getParams() 获取 {id: 42}

  Scenario: pushNamedRoute recoverable=false
    When 调用 router.pushNamedRoute({name: "myPage", recoverable: false})
    Then PageInfo 标记 recoverable_=false
    And 应用销毁后不恢复该页面
```

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
    query: "NamedRouterOptions pushNamedRoute replaceNamedRoute RouteMap查找 RouterMode分发 命名路由100004错误码 js_router.cpp JSPushNamedRoute JSReplaceNamedRoute page_router_manager PushPage ReplacePage"
  - repo: "openharmony/ace_engine"
    query: "route_map.json module.json5 routerMap RouteMapItem name action src buildType FA模型 Stage模型 命名路由配置"
```

**关键文档：** `@ohos.router.d.ts` (Dynamic SDK)、`@ohos.arkui.UIContext.d.ts` (实例级 SDK)、`@ohos.router.static.d.ets` (Static SDK since 23)、`js_router.cpp` (NAPI 绑定)、`page_router_manager.h/.cpp` (核心实现)
