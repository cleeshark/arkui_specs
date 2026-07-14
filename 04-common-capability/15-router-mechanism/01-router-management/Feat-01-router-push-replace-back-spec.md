# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 路由跳转与替换 |
| 特性编号 | Func-04-15-01-Feat-01 |
| 所属 Epic | 路由管理（04-15-01） |
| 优先级 | P1 |
| 目标版本 | API 8 ~ API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 较高（多重载双栈+RouterMode+错误码+UIContext双路径+recoverable） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | pushUrl 4 个重载 | since 9，deprecated since 18→UIContext.Router.pushUrl；options+callback, options+Promise, options+mode+callback, options+mode+Promise |
| MODIFIED | replaceUrl 4 个重载 | since 9，deprecated since 18→UIContext.Router.replaceUrl；同 pushUrl 重载模式；错误码含 200002 |
| MODIFIED | back(options?) 返回上一页/指定页 | since 8，deprecated since 18→UIContext.Router.back；options.url 指定返回目标页；弹出页推入恢复栈 |
| MODIFIED | back(index, params?) 按索引返回 | since 12，deprecated since 18→UIContext.Router.back；index 1-based 自底向顶 |
| MODIFIED | RouterMode.Standard | since 9；常推新实例到栈顶 |
| MODIFIED | RouterMode.Single | since 9；栈中同名 URI 页移栈顶/未找到按 Standard |
| MODIFIED | RouterOptions.url | since 8，必填 string |
| MODIFIED | RouterOptions.params | since 8，可选 Object |
| MODIFIED | RouterOptions.recoverable | since 14，可选 boolean，默认 true；控制应用销毁后栈恢复 |
| MODIFIED | RouterState | since 8，deprecated since 18；index 1-based 自底向顶；params since 12 |
| MODIFIED | UIContext.Router 实例级 API | since 10/11/12；pushUrl/replaceUrl/back 同功能但绑定 UIAbility Context |
| MODIFIED | push（deprecated since 9） | 被 pushUrl 替代；无错误码返回 |
| MODIFIED | replace（deprecated since 9） | 被 replaceUrl 替代；无错误码返回 |

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `specs/04-common-capability/15-router-mechanism/01-router-management/design.md` |
| SDK Dynamic | `interface/sdk-js/api/@ohos.router.d.ts` (模块级 Dynamic) |
| SDK UIContext | `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts` (实例级 UIContext.Router) |
| SDK Static | `interface/sdk-js/api/@ohos.router.static.d.ets` (since 23) |
| NAPI 绑定 | `interfaces/napi/kits/router/js_router.cpp` |
| 核心实现 | `frameworks/bridge/declarative_frontend/ng/page_router_manager.h/.cpp` |
| 代理层 | `frameworks/bridge/declarative_frontend/ng/frontend_delegate_impl.cpp` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: pushUrl 路由跳转

作为应用开发者，我想要通过 pushUrl 将新页面推入路由栈，以便导航到目标页面，同时支持 Standard（常推新实例）和 Single（栈中同名页移栈顶）两种路由模式，以及 4 种重载形式（callback/Promise/mode+callback/mode+Promise）。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 调用 pushUrl({url: "pages/detail"}) 无 mode THEN 默认 RouterMode.Standard 推入新实例到栈顶 | 正常 |
| AC-1.2 | WHEN 调用 pushUrl({url}, RouterMode.Standard) THEN 常推新实例到栈顶，不检查栈中同名页 | 正常 |
| AC-1.3 | WHEN 调用 pushUrl({url}, RouterMode.Single) 且栈中存在同名 URI 页 THEN 距栈顶最近的同名页被移到栈顶（PopPageTo+PushPage） | 正常 |
| AC-1.4 | WHEN 调用 pushUrl({url}, RouterMode.Single) 且栈中不存在同名 URI 页 THEN 按 Standard 模式推入新实例 | 正常 |
| AC-1.5 | WHEN 调用 pushUrl(options, callback) THEN callback 在跳转完成后回调 | 正常 |
| AC-1.6 | WHEN 调用 pushUrl(options) THEN 返回 Promise\<void>，跳转成功 resolve，失败 reject BusinessError | 正常 |
| AC-1.7 | WHEN 调用 pushUrl(options, mode, callback) THEN callback 在跳转完成后回调 | 正常 |
| AC-1.8 | WHEN 调用 pushUrl(options, mode) THEN 返回 Promise\<void>，跳转成功 resolve，失败 reject BusinessError | 正常 |
| AC-1.9 | WHEN 调用 UIContext.Router.pushUrl THEN 行为与模块级 pushUrl 一致，但绑定 UIAbility Context | 正常 |
| AC-1.10 | WHEN pushUrl options.url 为空或不存在 THEN 抛出 BusinessError 100002（URI 错误） | 异常 |
| AC-1.11 | WHEN 栈已满 32 页 THEN pushUrl 抛出 BusinessError 100003（栈溢出） | 异常 |
| AC-1.12 | WHEN options 参数缺失或非 object THEN 抛出 BusinessError 401（参数错误） | 异常 |
| AC-1.13 | WHEN options.url 缺失 THEN 抛出 BusinessError 401（必填参数未指定） | 异常 |
| AC-1.14 | WHEN delegate 未获取 THEN 抛出 BusinessError 100001（内部错误） | 异常 |
| AC-1.15 | WHEN 栈已满 32 页且调用 Single 模式 pushUrl 同名页 THEN 不抛 100003（移栈顶不增加栈大小） | 边界 |
| AC-1.16 | WHEN pushUrl 成功 THEN params 传递到目标页面，目标页可通过 getParams() 获取 | 正常 |

### US-2: replaceUrl 路由替换

作为应用开发者，我想要通过 replaceUrl 替换当前栈顶页为新页面，以便在不增加栈深度的情况下切换页面，当前页被销毁（不推入恢复栈），同时支持 4 种重载和 Standard/Single 两种路由模式。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 replaceUrl({url: "pages/home"}) 无 mode THEN 默认 RouterMode.Standard，弹出当前页（销毁）→推入新页到栈顶 | 正常 |
| AC-2.2 | WHEN 调用 replaceUrl({url}, RouterMode.Standard) THEN 弹出当前页（销毁，不推入 restorePageRouterStack_）→推入新页到栈顶 | 正常 |
| AC-2.3 | WHEN 调用 replaceUrl({url}, RouterMode.Single) 且栈中存在同名 URI 页 THEN 弹出当前页（销毁）→同名页移栈顶 | 正常 |
| AC-2.4 | WHEN 调用 replaceUrl({url}, RouterMode.Single) 且栈中不存在同名 URI 页 THEN 按 Standard 模式：弹出当前页→推入新页 | 正常 |
| AC-2.5 | WHEN 调用 replaceUrl(options, callback) THEN callback 在替换完成后回调 | 正常 |
| AC-2.6 | WHEN 调用 replaceUrl(options) THEN 返回 Promise\<void>，替换成功 resolve，失败 reject BusinessError | 正常 |
| AC-2.7 | WHEN 调用 replaceUrl(options, mode, callback) THEN callback 在替换完成后回调 | 正常 |
| AC-2.8 | WHEN 调用 replaceUrl(options, mode) THEN 返回 Promise\<void>，替换成功 resolve，失败 reject BusinessError | 正常 |
| AC-2.9 | WHEN 调用 UIContext.Router.replaceUrl THEN 行为与模块级 replaceUrl 一致，但绑定 UIAbility Context | 正常 |
| AC-2.10 | WHEN replaceUrl options.url 为空或不存在 THEN 抛出 BusinessError 200002（replace URI 错误，与 pushUrl 100002 不同） | 异常 |
| AC-2.11 | WHEN 栈仅 1 页且 replaceUrl THEN 替换成功（弹出原页销毁→推入新页，栈仍为 1 页） | 边界 |
| AC-2.12 | WHEN options 参数缺失或非 object THEN 抛出 BusinessError 401 | 异常 |
| AC-2.13 | WHEN options.url 缺失 THEN 抛出 BusinessError 401 | 异常 |
| AC-2.14 | WHEN delegate 未获取 THEN 抛出 BusinessError 100001 | 异常 |

### US-3: back 返回上一页/指定页

作为应用开发者，我想要通过 back 返回上一页或指定页面，以便回退导航历史。弹出页被推入恢复栈（可恢复），栈仅 1 页时 back 不执行。back 依赖 showAlertBeforeBackPage 弹窗拦截机制。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 back() 无参数 THEN 弹出栈顶页→推入 restorePageRouterStack_，显示栈顶下一页 | 正常 |
| AC-3.2 | WHEN 调用 back({url: "pages/index"}) THEN 返回到栈中距栈顶最近的指定 url 页，中间页全部弹出并推入恢复栈 | 正常 |
| AC-3.3 | WHEN 调用 back(index, params) (since 12) THEN 返回到栈中指定 index 的页面，index 为 1-based 自底向顶 | 正常 |
| AC-3.4 | WHEN 调用 back(index, params) (since 12) THEN params 传递到目标页面 | 正常 |
| AC-3.5 | WHEN 调用 UIContext.Router.back THEN 行为与模块级 back 一致，但绑定 UIAbility Context | 正常 |
| AC-3.6 | WHEN 栈仅 1 页 THEN back 不执行（防止清空栈） | 边界 |
| AC-3.7 | WHEN back({url}) 且栈中不存在指定 url THEN 应用不响应（不执行任何操作） | 边界 |
| AC-3.8 | WHEN 当前页设置了 showAlertBeforeBackPage THEN back 先弹 AlertDialog 确认→确认后执行 back→取消不执行 | 正常 |
| AC-3.9 | WHEN inRouterOpt_=true THEN back 异步投递 PostAsyncEvent | 边界 |
| AC-3.10 | WHEN back 成功 THEN 弹出页推入 restorePageRouterStack_（可恢复），非销毁 | 正常 |

### US-4: RouterMode 策略

作为应用开发者，我想要通过 RouterMode 枚值控制路由跳转策略，以便在 Standard（常推新实例）和 Single（栈中同名页移栈顶）之间选择合适的导航行为。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 使用 RouterMode.Standard THEN pushUrl/replaceUrl 常推新实例到栈顶，不检查栈中同名页 | 正常 |
| AC-4.2 | WHEN 使用 RouterMode.Single 且栈中存在同名 URI THEN 距栈顶最近的同名页移栈顶（PopPageTo+PushPage 重建） | 正常 |
| AC-4.3 | WHEN 使用 RouterMode.Single 且栈中不存在同名 URI THEN 按 Standard 行为推入新实例 | 正常 |
| AC-4.4 | WHEN 不指定 RouterMode THEN 默认为 RouterMode.Standard | 正常 |
| AC-4.5 | WHEN RouterMode.Single 找到同名页 THEN 移栈顶过程中中间页被弹出并推入恢复栈 | 正常 |

### US-5: 参数传递与 recoverable

作为应用开发者，我想要通过 RouterOptions.params 传递参数到目标页面，并通过 recoverable 标记控制页面栈在应用销毁后的恢复策略。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN pushUrl({url, params: {data: 123}}) THEN 目标页可通过 getParams() 获取 {data: 123} | 正常 |
| AC-5.2 | WHEN pushUrl({url, params: undefined}) THEN 目标页 getParams() 返回空 Object 或 undefined | 边界 |
| AC-5.3 | WHEN pushUrl({url, recoverable: true}) (since 14) THEN 页面标记为可恢复；应用销毁后恢复时仅恢复栈顶页，其余页在 back 时逐步恢复 | 正常 |
| AC-5.4 | WHEN pushUrl({url, recoverable: false}) (since 14) THEN 页面标记为不可恢复；应用销毁后不恢复该页 | 正常 |
| AC-5.5 | WHEN pushUrl({url}) 未指定 recoverable THEN 默认 recoverable=true | 正常 |
| AC-5.6 | WHEN replaceUrl({url, params}) THEN params 传递到替换后的新页面 | 正常 |
| AC-5.7 | WHEN back(index, params) (since 12) THEN params 传递到目标页面，覆盖原页面 params | 正常 |

### US-6: 废弃 API 迁移

作为应用开发者，我想要了解 push/replace 废弃 API 与 pushUrl/replaceUrl 新 API 的差异，以便完成存量代码迁移。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN 调用 push(options) (deprecated since 9) THEN 行为等同于 pushUrl(options) 但无错误码返回 | 正常 |
| AC-6.2 | WHEN 调用 replace(options) (deprecated since 9) THEN 行为等同于 replaceUrl(options) 但无错误码返回 | 正常 |
| AC-6.3 | WHEN 模块级 pushUrl/replaceUrl/back (deprecated since 18) THEN 迁移至 UIContext.Router.pushUrl/replaceUrl/back | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.16 | R-1 ~ R-15 | TASK-01 | 单测 + XTS | `js_router.cpp:JSPushUrl` / `page_router_manager.cpp:PushPage` |
| AC-2.1 ~ AC-2.14 | R-16 ~ R-27 | TASK-01 | 单测 + XTS | `js_router.cpp:JSReplaceUrl` / `page_router_manager.cpp:ReplacePage` |
| AC-3.1 ~ AC-3.10 | R-28 ~ R-37 | TASK-01 | 单测 + XTS | `js_router.cpp:JSBack` / `page_router_manager.cpp:PopPage` |
| AC-4.1 ~ AC-4.5 | R-38 ~ R-42 | TASK-01 | 单测 | `page_router_manager.cpp:PushPage` RouterMode 分发 |
| AC-5.1 ~ AC-5.7 | R-43 ~ R-49 | TASK-01 | 单测 | `page_router_manager.cpp:PushPage` params/recoverable |
| AC-6.1 ~ AC-6.3 | R-50 ~ R-52 | TASK-01 | 单测 | `js_router.cpp:JSPush` / `JSReplace` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | pushUrl(options) 无 mode | 默认 RouterMode.Standard → PushPage(url, params, RouterMode::STANDARD) | NAPI argc==1 分支 | AC-1.1 |
| R-2 | 行为 | pushUrl(options, RouterMode.Standard) | 常推新实例到栈顶 pageRouterStack_.push_back(pageInfo) | 不检查栈中同名页 | AC-1.2 |
| R-3 | 行为 | pushUrl(options, RouterMode.Single) + 栈中存在同名 URI | FindPageInStack → PopPageTo(index) 移除上方页 + PushPage 重新推入（移栈顶） | PopPageTo 弹出页推入恢复栈 | AC-1.3, AC-4.2, AC-4.5 |
| R-4 | 行为 | pushUrl(options, RouterMode.Single) + 栈中不存在同名 URI | 按 Standard 模式推入新实例 | 不抛 100003（栈大小不变） | AC-1.4, AC-4.3 |
| R-5 | 行为 | pushUrl(options, callback) | FrontendDelegate::Push(url, params, mode) + callback 回调 | NAPI argc==2 且 arg[1] 为 function | AC-1.5 |
| R-6 | 行为 | pushUrl(options) 返回 Promise | FrontendDelegate::Push + Promise resolve/reject | NAPI argc==1 → napi_create_promise | AC-1.6 |
| R-7 | 行为 | pushUrl(options, mode, callback) | FrontendDelegate::Push(url, params, mode) + callback | NAPI argc==3 | AC-1.7 |
| R-8 | 行为 | pushUrl(options, mode) 返回 Promise | FrontendDelegate::Push(url, params, mode) + Promise | NAPI argc==2 且 arg[1] 为 number | AC-1.8 |
| R-9 | 行为 | UIContext.Router.pushUrl | 同模块级 pushUrl，最终调用 PageRouterManager::PushPage | 实例级绑定 UIAbility Context | AC-1.9 |
| R-10 | 异常 | pushUrl options.url 为空或不存在 | 抛出 BusinessError 100002 ("Uri error") | URI 校验在 PageRouterManager 层 | AC-1.10 |
| R-11 | 异常 | pageRouterStack_.size() >= 32 | 抛出 BusinessError 100003 ("Page stack error. Too many pages are pushed.") | MAX_ROUTER_STACK_SIZE=32 硬限制 | AC-1.11 |
| R-12 | 异常 | options 参数缺失或非 object | 抛出 BusinessError 401 ("Parameter error") | NAPI napi_typeof != napi_object → NapiThrow | AC-1.12 |
| R-13 | 异常 | options.url 缺失 | 抛出 BusinessError 401 | url 为 RouterOptions 必填字段 | AC-1.13 |
| R-14 | 异常 | delegate 未获取 | 抛出 BusinessError 100001 ("Internal error") | NAPI 层 NapiThrow | AC-1.14 |
| R-15 | 边界 | 栈已满 32 + Single 模式 pushUrl 同名页 | 移栈顶不增加栈大小 → 不抛 100003 | PopPageTo + PushPage 净增 0 | AC-1.15 |
| R-16 | 行为 | replaceUrl(options) 无 mode | 默认 RouterMode.Standard → 弹出栈顶当前页（销毁）→ 推入新页 | 当前页不推入 restorePageRouterStack_ | AC-2.1 |
| R-17 | 行为 | replaceUrl(options, RouterMode.Standard) | StartReplace → PopPage(destroy) → PushPage(newUrl) | destroy=true 不推恢复栈 | AC-2.2 |
| R-18 | 行为 | replaceUrl(options, RouterMode.Single) + 栈中存在同名 URI | 弹出当前页（销毁）→ 同名页移栈顶 | 同名页在当前页之下 | AC-2.3 |
| R-19 | 行为 | replaceUrl(options, RouterMode.Single) + 栈中不存在同名 URI | 按 Standard 模式：弹出当前页→推入新页 | 同 R-16 | AC-2.4 |
| R-20 | 行为 | replaceUrl(options, callback) | FrontendDelegate::Replace(url, params, mode) + callback | NAPI argc==2 且 arg[1] 为 function | AC-2.5 |
| R-21 | 行为 | replaceUrl(options) 返回 Promise | FrontendDelegate::Replace + Promise resolve/reject | NAPI argc==1 → napi_create_promise | AC-2.6 |
| R-22 | 行为 | replaceUrl(options, mode, callback) | FrontendDelegate::Replace(url, params, mode) + callback | NAPI argc==3 | AC-2.7 |
| R-23 | 行为 | replaceUrl(options, mode) 返回 Promise | FrontendDelegate::Replace(url, params, mode) + Promise | NAPI argc==2 且 arg[1] 为 number | AC-2.8 |
| R-24 | 行为 | UIContext.Router.replaceUrl | 同模块级 replaceUrl，最终调用 PageRouterManager::ReplacePage | 实例级绑定 UIAbility Context | AC-2.9 |
| R-25 | 异常 | replaceUrl options.url 为空或不存在 | 抛出 BusinessError 200002 ("Uri error. The URI of the page to be used for replacement is incorrect or does not exist.") | replaceUrl 专用错误码 200002（非 100002） | AC-2.10 |
| R-26 | 边界 | 栈仅 1 页且 replaceUrl | 替换成功，弹出原页销毁→推入新页，栈仍为 1 页 | 不推入恢复栈 | AC-2.11 |
| R-27 | 异常 | replaceUrl options 参数缺失/非 object 或 url 缺失 | 抛出 BusinessError 401 | 同 pushUrl 参数校验逻辑 | AC-2.12, AC-2.13 |
| R-28 | 行为 | back() 无参数 | PopPage → 弹出页推入 restorePageRouterStack_ → 显示栈顶下一页 | 栈顶页不销毁，可恢复 | AC-3.1, AC-3.10 |
| R-29 | 行为 | back({url: "pages/index"}) | 搜索栈中距栈顶最近的指定 url 页 → PopPageTo 目标页上方所有页弹出并推入恢复栈 | url 不存在时不响应 | AC-3.2, AC-3.7 |
| R-30 | 行为 | back(index, params) (since 12) | 返回到 1-based index 指定页，中间页弹出推入恢复栈，params 传递到目标页 | index 超范围不响应 | AC-3.3, AC-3.4, AC-5.7 |
| R-31 | 行为 | UIContext.Router.back | 同模块级 back，最终调用 PageRouterManager::PopPage | 实例级绑定 UIAbility Context | AC-3.5 |
| R-32 | 边界 | pageRouterStack_.size() == 1 | back 不执行（防止清空栈） | CHECK_NULL_VOID 或直接 return | AC-3.6 |
| R-33 | 边界 | back({url}) 栈中不存在指定 url | 应用不响应，不执行任何操作 | 不弹窗不报错 | AC-3.7 |
| R-34 | 行为 | 当前页设置 showAlertBeforeBackPage | back 先弹 AlertDialog → 确认(successIndex!=0)执行 back → 取消(successIndex==0)不执行 | 依赖 Feat-02 showAlert 机制 | AC-3.8 |
| R-35 | 边界 | inRouterOpt_=true | back 异步投递 PostAsyncEvent | PostAsyncEvent + "ArkUIPageRouterBack" | AC-3.9 |
| R-36 | 行为 | 弹出页推入恢复栈 | back 后弹出页推入 restorePageRouterStack_（非销毁），可通过 back→pushUrl→back 恢复 | restorePageRouterStack_.push_back | AC-3.10 |
| R-37 | 异常 | delegate 未获取 | 抛出 BusinessError 100001 | 同 pushUrl | AC-3.6 补充 |
| R-38 | 行为 | RouterMode.Standard | pushUrl/replaceUrl 常推新实例，不检查栈中同名页 | 默认模式 | AC-4.1 |
| R-39 | 行为 | RouterMode.Single + 同名页存在 | FindPageInStack(url) → PopPageTo(foundIndex) + PushPage(url) | PopPageTo 弹出页推入恢复栈 | AC-4.2 |
| R-40 | 行为 | RouterMode.Single + 同名页不存在 | 按 Standard 行为推入新实例 | 不抛 100003 | AC-4.3 |
| R-41 | 行为 | 不指定 RouterMode | 默认 RouterMode.Standard | NAPI argc<=2 时 mode 默认 STANDARD | AC-4.4 |
| R-42 | 行为 | RouterMode.Single 移栈顶过程 | PopPageTo 弹出中间页全部推入 restorePageRouterStack_ | 中间页可恢复 | AC-4.5 |
| R-43 | 行为 | pushUrl({url, params}) | params 作为 napi_value 传递到目标页 → EntryPageInfo::SetPageParams | 目标页 getParams() 获取 | AC-5.1, AC-1.16 |
| R-44 | 边界 | pushUrl({url, params: undefined}) | 目标页 getParams() 返回空 Object 或 undefined | ParseJSONParams 处理空值 | AC-5.2 |
| R-45 | 行为 | pushUrl({url, recoverable: true}) (since 14) | PageInfo::SetRecoverable(true)；应用销毁恢复时仅恢复栈顶页，其余页 back 时逐步恢复 | 默认值 true | AC-5.3, AC-5.5 |
| R-46 | 行为 | pushUrl({url, recoverable: false}) (since 14) | PageInfo::SetRecoverable(false)；应用销毁后不恢复该页 | 不影响活跃栈操作 | AC-5.4 |
| R-47 | 行为 | replaceUrl({url, params}) | params 传递到替换后的新页面 | 同 pushUrl params 机制 | AC-5.6 |
| R-48 | 行为 | back(index, params) (since 12) | params 传递到目标页，覆盖原页面 params | params 作为 Object | AC-5.7 |
| R-49 | 边界 | DynamicExtender 模式 | pushUrl/replaceUrl/back 优先走 Dynamic 分支 | ArkTS frontend type | AC-1.9 补充 |
| R-50 | 行为 | push(options) (deprecated since 9) | 行为等同 pushUrl(options) 但无错误码返回，push 不支持 RouterMode 和 Promise | 无 callback/Promise 重载 | AC-6.1 |
| R-51 | 行为 | replace(options) (deprecated since 9) | 行为等同 replaceUrl(options) 但无错误码返回 | 同上 | AC-6.2 |
| R-52 | 行为 | 模块级 pushUrl/replaceUrl/back (deprecated since 18) | 迁移至 UIContext.Router.pushUrl/replaceUrl/back | NAPI 层两条路径最终调用同一 PageRouterManager | AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 ~ R-8 (pushUrl 4 重载) | 单测：4 种重载分别调用 → 验证 callback/Promise/mode 分发 | 重载分发逻辑 |
| VM-2 | R-2, R-3, R-4 (RouterMode Standard/Single) | 单测：构建栈有同名页 → pushUrl Single → 验证移栈顶；构建栈无同名页 → pushUrl Single → 验证 Standard 行为 | RouterMode 分发 |
| VM-3 | R-10 ~ R-14 (pushUrl 错误码) | 单测：空 url→100002；栈满→100003；非 object→401；url 缺失→401；delegate 缺失→100001 | 错误码覆盖 |
| VM-4 | R-15 (栈满+Single 同名页) | 单测：栈满 32→pushUrl Single 同名页→不抛 100003 | 边界：移栈顶不增栈 |
| VM-5 | R-16 ~ R-23 (replaceUrl 4 重载) | 单测：4 种重载分别调用 → 验证替换行为 | 重载分发+替换逻辑 |
| VM-6 | R-25, R-27 (replaceUrl 错误码) | 单测：空 url→200002；非 object→401 | 200002 专用错误码 |
| VM-7 | R-26 (栈仅 1 页 replaceUrl) | 单测：栈 1 页→replaceUrl→栈仍 1 页 | 边界：单页替换 |
| VM-8 | R-28 ~ R-36 (back 行为) | 单测：back()→弹出页推入恢复栈；back({url})→返回指定页；back(index,params)→按索引返回；栈 1 页→不执行 | 恢复栈+边界 |
| VM-9 | R-34 (back+showAlert 拦截) | 单测：showAlert→back→确认执行/取消不执行 | 依赖 Feat-02 |
| VM-10 | R-43 ~ R-48 (params/recoverable) | 单测：pushUrl params→目标页 getParams 验证；recoverable=true/false→恢复策略 | 参数传递+恢复标记 |
| VM-11 | R-50 ~ R-52 (废弃 API) | 单测：push/replace 调用→行为等同但无错误码 | deprecated 兼容 |

## API 变更分析

### 新增 API

> 已有实现补录，无新增 API。以下列出 Feat-01 涉及的 Public API 签名供 spec 参考。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| push(options) | 废弃(since 9→pushUrl) | 无错误码返回 | 替换为 pushUrl(options): Promise\<void> 支持 Promise 错误处理 | AC-6.1 |
| replace(options) | 废弃(since 9→replaceUrl) | 无错误码返回 | 替换为 replaceUrl(options): Promise\<void> | AC-6.2 |
| router.pushUrl (模块级) | 废弃(since 18→UIContext.Router) | 全局单例 | 使用 this.getUIContext().getRouter().pushUrl() | AC-1.9, AC-6.3 |
| router.replaceUrl (模块级) | 废弃(since 18→UIContext.Router) | 同上 | 使用 UIContext.Router.replaceUrl() | AC-2.9, AC-6.3 |
| router.back (模块级) | 废弃(since 18→UIContext.Router) | 同上 | 使用 UIContext.Router.back() | AC-3.5, AC-6.3 |

## 接口规格

### 接口定义

**pushUrl(options, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pushUrl(options: RouterOptions, callback: AsyncCallback<void>): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 9, deprecated since 18→UIContext.Router.pushUrl) |
| 错误码 | 401 (参数错误), 100001 (内部错误), 100002 (URI错误), 100003 (栈溢出) |
| 关联 AC | AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | RouterOptions | 是 | 无 | 必须为 object；url 必填 |
| options.url | string | 是 | 无 | 目标页面 URI |
| options.params | Object | 否 | undefined | 传递到目标页面的数据 |
| options.recoverable | boolean | 否 | true (since 14) | 控制应用销毁后栈恢复策略 |
| callback | AsyncCallback\<void> | 是 | 无 | 跳转完成后回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | PushPage(url, params, RouterMode::STANDARD) + callback 回调 | AC-1.5 |
| 2 | options 非 object | 抛出 BusinessError 401 | AC-1.12 |
| 3 | url 缺失 | 抛出 BusinessError 401 | AC-1.13 |
| 4 | url 不存在 | 抛出 BusinessError 100002 | AC-1.10 |
| 5 | 栈满 32 | 抛出 BusinessError 100003 | AC-1.11 |
| 6 | delegate 未获取 | 抛出 BusinessError 100001 | AC-1.14 |

---

**pushUrl(options)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pushUrl(options: RouterOptions): Promise<void>` |
| 返回值 | `Promise<void>` |
| 开放范围 | Public (since 9, deprecated since 18→UIContext.Router.pushUrl) |
| 错误码 | 401, 100001, 100002, 100003 |
| 关联 AC | AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | RouterOptions | 是 | 无 | 同上 |
| options.url | string | 是 | 无 | 目标页面 URI |
| options.params | Object | 否 | undefined | 传递到目标页面的数据 |
| options.recoverable | boolean | 否 | true (since 14) | 控制栈恢复策略 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | PushPage(url, params, RouterMode::STANDARD) + Promise resolve | AC-1.6 |
| 2 | 默认 RouterMode | mode=Standard | AC-1.1 |
| 3 | 跳转失败 | Promise reject BusinessError | AC-1.6 |
| 4 | params 传递 | 目标页 getParams() 获取 params | AC-1.16, AC-5.1 |
| 5 | recoverable=true (since 14) | PageInfo::SetRecoverable(true) | AC-5.3 |
| 6 | recoverable=false (since 14) | PageInfo::SetRecoverable(false) | AC-5.4 |

---

**pushUrl(options, mode, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pushUrl(options: RouterOptions, mode: RouterMode, callback: AsyncCallback<void>): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 9, deprecated since 18→UIContext.Router.pushUrl) |
| 错误码 | 401, 100001, 100002, 100003 |
| 关联 AC | AC-1.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | RouterOptions | 是 | 无 | 同上 |
| mode | RouterMode | 是 | 无 | Standard 或 Single |
| callback | AsyncCallback\<void> | 是 | 无 | 跳转完成后回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | mode=Standard | 常推新实例到栈顶 | AC-1.2, AC-4.1 |
| 2 | mode=Single + 栈中存在同名 URI | 移栈顶（PopPageTo+PushPage） | AC-1.3, AC-4.2 |
| 3 | mode=Single + 栈中不存在同名 URI | 按 Standard 推入 | AC-1.4, AC-4.3 |
| 4 | 栈满 32 + Single 同名页 | 不抛 100003（移栈顶净增 0） | AC-1.15 |

---

**pushUrl(options, mode)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pushUrl(options: RouterOptions, mode: RouterMode): Promise<void>` |
| 返回值 | `Promise<void>` |
| 开放范围 | Public (since 9, deprecated since 18→UIContext.Router.pushUrl) |
| 错误码 | 401, 100001, 100002, 100003 |
| 关联 AC | AC-1.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | RouterOptions | 是 | 无 | 同上 |
| mode | RouterMode | 是 | 无 | Standard 或 Single |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | mode=Standard | 常推新实例 + Promise resolve | AC-1.2 |
| 2 | mode=Single + 同名页 | 移栈顶 + Promise resolve | AC-1.3 |
| 3 | mode=Single + 无同名页 | Standard 推入 + Promise resolve | AC-1.4 |
| 4 | 跳转失败 | Promise reject BusinessError | AC-1.8 |

---

**replaceUrl(options, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `replaceUrl(options: RouterOptions, callback: AsyncCallback<void>): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 9, deprecated since 18→UIContext.Router.replaceUrl) |
| 错误码 | 401, 100001, 200002 |
| 关联 AC | AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | RouterOptions | 是 | 无 | 必须为 object；url 必填 |
| callback | AsyncCallback\<void> | 是 | 无 | 替换完成后回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | PopPage(destroy=true) + PushPage(newUrl) + callback 回调 | AC-2.5 |
| 2 | url 不存在 | 抛出 BusinessError 200002（replaceUrl 专用错误码） | AC-2.10 |
| 3 | options 非 object | 抛出 BusinessError 401 | AC-2.12 |
| 4 | delegate 未获取 | 抛出 BusinessError 100001 | AC-2.14 |

---

**replaceUrl(options)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `replaceUrl(options: RouterOptions): Promise<void>` |
| 返回值 | `Promise<void>` |
| 开放范围 | Public (since 9, deprecated since 18→UIContext.Router.replaceUrl) |
| 错误码 | 401, 100001, 200002 |
| 关联 AC | AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | RouterOptions | 是 | 无 | 同上 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | PopPage(destroy) + PushPage(newUrl) + Promise resolve | AC-2.6 |
| 2 | 栈仅 1 页 | 替换成功，栈仍 1 页 | AC-2.11 |
| 3 | url 不存在 | Promise reject BusinessError 200002 | AC-2.10 |
| 4 | params 传递 | 替换后新页 getParams() 获取 params | AC-5.6 |

---

**replaceUrl(options, mode, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `replaceUrl(options: RouterOptions, mode: RouterMode, callback: AsyncCallback<void>): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 9, deprecated since 18→UIContext.Router.replaceUrl) |
| 错误码 | 401, 100001, 200002 |
| 关联 AC | AC-2.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | RouterOptions | 是 | 无 | 同上 |
| mode | RouterMode | 是 | 无 | Standard 或 Single |
| callback | AsyncCallback\<void> | 是 | 无 | 替换完成后回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | mode=Standard | PopPage(destroy) + PushPage(newUrl) + callback | AC-2.2 |
| 2 | mode=Single + 同名页 | PopPage(destroy) + 同名页移栈顶 + callback | AC-2.3 |
| 3 | mode=Single + 无同名页 | 按 Standard 替换 + callback | AC-2.4 |

---

**replaceUrl(options, mode)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `replaceUrl(options: RouterOptions, mode: RouterMode): Promise<void>` |
| 返回值 | `Promise<void>` |
| 开放范围 | Public (since 9, deprecated since 18→UIContext.Router.replaceUrl) |
| 错误码 | 401, 100001, 200002 |
| 关联 AC | AC-2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | RouterOptions | 是 | 无 | 同上 |
| mode | RouterMode | 是 | 无 | Standard 或 Single |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | mode=Standard | PopPage(destroy) + PushPage + Promise resolve | AC-2.2 |
| 2 | mode=Single + 同名页 | 同名页移栈顶 + Promise resolve | AC-2.3 |
| 3 | mode=Single + 无同名页 | Standard 替换 + Promise resolve | AC-2.4 |
| 4 | 替换失败 | Promise reject BusinessError | AC-2.8 |

---

**back(options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `back(options?: RouterOptions): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 8, deprecated since 18→UIContext.Router.back) |
| 错误码 | 100001 (delegate 未获取) |
| 关联 AC | AC-3.1, AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | RouterOptions | 否 | undefined | 不传则返回上一页；url 指定返回目标页 |
| options.url | string | 否 | undefined | 栈中不存在指定 url 则不响应 |
| options.params | Object | 否 | undefined | since 12；传递到目标页 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | back() 无参数 | 弹出栈顶页→推入恢复栈→显示下一页 | AC-3.1, AC-3.10 |
| 2 | back({url}) | 返回栈中距栈顶最近的指定 url 页 | AC-3.2 |
| 3 | 栈仅 1 页 | 不执行（防止清空栈） | AC-3.6 |
| 4 | url 不存在 | 不响应 | AC-3.7 |
| 5 | showAlert 已设置 | 先弹 AlertDialog 确认 | AC-3.8 |
| 6 | inRouterOpt_=true | 异步投递 PostAsyncEvent | AC-3.9 |

---

**back(index, params?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `back(index: number, params?: Object): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 12, deprecated since 18→UIContext.Router.back) |
| 错误码 | 401 (index 参数错误) |
| 关联 AC | AC-3.3, AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| index | number | 是 | 无 | 1-based 自底向顶；超范围不响应 |
| params | Object | 否 | undefined | 传递到目标页 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 返回到指定 index 页，中间页弹出推入恢复栈 | AC-3.3 |
| 2 | params 传递 | params 覆盖目标页原 params | AC-3.4, AC-5.7 |
| 3 | index 超范围 | 不响应 | AC-3.3 |
| 4 | 栈仅 1 页 | 不执行 | AC-3.6 |

---

**RouterMode**

| 属性 | 值 |
|------|-----|
| 类型 | enum |
| 开放范围 | Public (since 9) |
| 关联 AC | AC-4.1 ~ AC-4.5 |

**枚举值**

| 枚举成员 | 值 | 说明 | 关联 AC |
|----------|-----|------|---------|
| Standard | 0 | 默认模式：常推新实例到栈顶 | AC-4.1 |
| Single | 1 | 单例模式：栈中同名 URI 页移栈顶 | AC-4.2, AC-4.3 |

---

**RouterOptions**

| 属性 | 值 |
|------|-----|
| 类型 | interface |
| 开放范围 | Public (since 8, params since 8, recoverable since 14) |
| 关联 AC | AC-5.1 ~ AC-5.7 |

**属性约束**

| 属性 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| url | string | 是 | 无 | 目标页面 URI；支持绝对路径和 "/"（首页） |
| params | Object | 否 | undefined | 传递到目标页面的数据 |
| recoverable | boolean | 否 | true | since 14；控制应用销毁后栈恢复策略 |

---

**RouterState**

| 属性 | 值 |
|------|-----|
| 类型 | interface |
| 开放范围 | Public (since 8, params since 12, deprecated since 18) |
| 关联 AC | AC-5.1（params 通过 getState 传递） |

**属性约束**

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| index | number | 是 | 栈中页面索引，从 1 起自底向顶 |
| name | string | 是 | 当前页面文件名 |
| path | string | 是 | 当前页面路径 |
| params | Object | 是 | since 12；页面传递参数 |

---

**push (deprecated since 9)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `push(options: RouterOptions): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 8, deprecated since 9→pushUrl) |
| 错误码 | 无（无错误码返回机制） |
| 关联 AC | AC-6.1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 行为等同 pushUrl(options)，但无错误码返回 | AC-6.1 |

---

**replace (deprecated since 9)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `replace(options: RouterOptions): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 8, deprecated since 9→replaceUrl) |
| 错误码 | 无 |
| 关联 AC | AC-6.2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 行为等同 replaceUrl(options)，但无错误码返回 | AC-6.2 |

## 兼容性声明

- **已有 API 行为变更:** 否，所有行为均为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** pushUrl/replaceUrl since 9；back since 8；back(index,params) since 12；RouterMode since 9；recoverable since 14；UIContext.Router pushUrl/replaceUrl/back since 10/11/12；模块级 API deprecated since 18→UIContext.Router；push/replace deprecated since 9

### 错误码差异

| API | 错误码范围 | 说明 |
|-----|-----------|------|
| pushUrl | 401, 100001, 100002, 100003 | 100002 为 URI 错误；100003 为栈溢出 |
| replaceUrl | 401, 100001, 200002 | 200002 为 replace 专用 URI 错误（与 pushUrl 100002 不同） |
| back | 401 (back(index,params) since 12), 100001 | back(options) 无 401 |
| push (deprecated) | 无 | 无错误码返回 |
| replace (deprecated) | 无 | 无错误码返回 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双栈管理 | pageRouterStack_（活跃栈）+ restorePageRouterStack_（恢复栈）；back 弹出页推入恢复栈；pushUrl 时恢复栈同名页先弹出 | AC-1.3, AC-2.2, AC-3.10 |
| 栈上限 32 | MAX_ROUTER_STACK_SIZE=32 硬限制；超过抛 100003 | AC-1.11 |
| RouterMode 分发 | Standard 常推；Single 搜索栈→移栈顶/Standard 推入 | AC-4.1 ~ AC-4.5 |
| replaceUrl 不推入恢复栈 | 当前页销毁（destroy=true），不推入 restorePageRouterStack_ | AC-2.2, AC-2.11 |
| back 栈仅 1 页不执行 | 防止清空栈 | AC-3.6 |
| 1-based index | RouterState.index 和 back(index) 均从 1 起自底向顶 | AC-3.3 |
| NAPI 4-overload 分发 | JSPushUrl/JSReplaceUrl 根据 argc 和 arg 类型分发 | AC-1.5 ~ AC-1.8, AC-2.5 ~ AC-2.8 |
| 模块级 deprecated since 18 | 所有模块级 API 标记 deprecated→UIContext.Router | AC-1.9, AC-2.9, AC-3.5, AC-6.3 |
| DynamicExtender 优先 | ArkTS frontend 下优先走 Dynamic 分支 | R-49 |
| 错误码体系区分 | pushUrl 使用 100002（URI 错误）；replaceUrl 使用 200002（replace URI 错误） | AC-1.10, AC-2.10 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | pushUrl/replaceUrl 页面创建 < 500ms | 帧率监控 | PageRouterManager::PushPage/ReplacePage |
| 安全 | 无权限要求 | SDK .d.ts 验证 | SysCap: SystemCapability.ArkUI.ArkUI.Full/Lite |
| 可靠性 | 错误码体系完整（401/100001/100002/100003/200002） | 错误码覆盖 | @ohos.router.d.ts JSDoc |
| 可靠性 | 栈上限 32 硬限制保证内存可控 | 栈大小检查 | pageRouterManager.cpp:PushPage |
| 可测试性 | DynamicExtender Mock 可隔离 | Mock 策略 | TryGet*FromDynamicIfNeeded 分支 |
| 自动化维测 | 路由操作日志 | hilog | TAG_LOGI(AceLogTag::ACE_ROUTER) |
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
| 无障碍 | 否 | 路由跳转无无障碍特殊处理 | — |
| 大字体 | 否 | 路由跳转不涉及字体 | — |
| 深色模式 | 否 | 路由跳转不涉及颜色 | — |
| 多窗口/分屏 | 是 | UIContext.Router 绑定特定 Ability Context，多窗口各自独立栈 | 多 Ability 场景 |
| 多用户 | 否 | Router 为单 Ability 内栈管理 | — |
| 版本升级 | 是 | 模块级 deprecated since 18→迁移至 UIContext.Router；push/replace deprecated since 9 | 存量代码迁移 |
| 生态兼容 | 是 | push→pushUrl/replace→replaceUrl 无错误码差异需注意 | 跨版本兼容 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 路由跳转与替换
  作为应用开发者
  我想要通过 pushUrl/replaceUrl/back 管理路由栈
  以便在页面之间导航和回退

  Scenario: pushUrl Standard 模式推入新实例
    Given 路由栈中有 3 个页面(PageA, PageB, PageC)
    When 调用 pushUrl({url: "pages/detail"}, RouterMode.Standard)
    Then 栈顶新增 PageDetail
    And 路由栈大小变为 4

  Scenario: pushUrl Single 模式移栈顶
    Given 路由栈中有 3 个页面(PageA, PageB, PageA)
    When 调用 pushUrl({url: "pages/pageA"}, RouterMode.Single)
    Then 栈中距栈顶最近的 PageA 移到栈顶
    And 路由栈大小不变（仍为 3）

  Scenario: pushUrl Single 模式未找到同名页
    Given 路由栈中有 3 个页面(PageA, PageB, PageC)
    When 调用 pushUrl({url: "pages/detail"}, RouterMode.Single)
    Then 按 Standard 模式推入新实例
    And 路由栈大小变为 4

  Scenario: pushUrl 栈溢出
    Given 路由栈中有 32 个页面
    When 调用 pushUrl({url: "pages/new"})
    Then 抛出 BusinessError 100003

  Scenario: pushUrl 栈满 Single 同名页不溢出
    Given 路由栈中有 32 个页面且栈中包含 "pages/detail"
    When 调用 pushUrl({url: "pages/detail"}, RouterMode.Single)
    Then 移栈顶成功
    And 不抛出 100003

  Scenario: replaceUrl 替换当前页
    Given 路由栈中有 3 个页面(PageA, PageB, PageC)
    When 调用 replaceUrl({url: "pages/home"})
    Then PageC 被销毁（不推入恢复栈）
    And PageHome 推入栈顶
    And 路由栈大小变为 3

  Scenario: replaceUrl 栈仅 1 页
    Given 路由栈中有 1 个页面(PageA)
    When 调用 replaceUrl({url: "pages/home"})
    Then PageA 被销毁
    And PageHome 推入栈顶
    And 路由栈大小仍为 1

  Scenario: replaceUrl URI 错误码 200002
    Given 路由栈中有 2 个页面
    When 调用 replaceUrl({url: "pages/nonexistent"})
    Then 抛出 BusinessError 200002

  Scenario: back 返回上一页
    Given 路由栈中有 3 个页面(PageA, PageB, PageC)
    When 调用 back()
    Then PageC 弹出并推入恢复栈
    And 显示 PageB

  Scenario: back 返回指定页
    Given 路由栈中有 4 个页面(PageA, PageB, PageC, PageD)
    When 调用 back({url: "pages/pageA"})
    Then PageD/PageC/PageB 弹出推入恢复栈
    And 显示 PageA

  Scenario: back 栈仅 1 页不执行
    Given 路由栈中有 1 个页面(PageA)
    When 调用 back()
    Then 不执行任何操作

  Scenario: back 指定 url 不存在
    Given 路由栈中有 3 个页面(PageA, PageB, PageC)
    When 调用 back({url: "pages/nonexistent"})
    Then 不响应

  Scenario: back showAlert 拦截
    Given 已调用 showAlertBeforeBackPage({message: "确认返回?"})
    When 调用 back()
    Then 弹出 AlertDialog
    When 用户点击确认按钮
    Then 执行 back 返回上一页

  Scenario: back 按索引返回
    Given 路由栈中有 4 个页面
    When 调用 back(1, {data: "home"})
    Then 返回到栈底页面
    And params 传递到目标页

  Scenario: pushUrl 参数传递
    When 调用 pushUrl({url: "pages/detail", params: {id: 123}})
    Then 目标页 getParams() 返回 {id: 123}

  Scenario: recoverable 默认 true
    When 调用 pushUrl({url: "pages/detail"})
    Then recoverable 默认为 true
    And 应用销毁后栈顶页可恢复

  Scenario: recoverable 为 false
    When 调用 pushUrl({url: "pages/detail", recoverable: false})
    Then 应用销毁后该页不恢复

  Scenario Outline: pushUrl 错误码
    When 调用 pushUrl(options) 且 options 为 <type>
    Then 抛出 BusinessError <code>

    Examples:
      | type | code |
      | 非object | 401 |
      | url缺失 | 401 |
      | url不存在 | 100002 |
      | delegate缺失 | 100001 |
      | 栈满32 | 100003 |

  Scenario Outline: replaceUrl 错误码
    When 调用 replaceUrl(options) 且 options.url 为 <type>
    Then 抛出 BusinessError <code>

    Examples:
      | type | code |
      | 非object | 401 |
      | url缺失 | 401 |
      | url不存在 | 200002 |
      | delegate缺失 | 100001 |
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
    query: "PageRouterManager 双栈管理 pushUrl/replaceUrl/back RouterMode 分发、错误码 401/100001/100002/100003/200002、params/recoverable 传递、NAPI 4-overload 分发 JSPushUrl/JSReplaceUrl/JSBack"
  - repo: "openharmony/ace_engine"
    query: "js_router.cpp NAPI 绑定 JSPushUrl/JSReplaceUrl/JSBack 参数解析和错误码映射、UIContext.Router 实例级方法绑定"
```

**关键文档：** `@ohos.router.d.ts` (Dynamic SDK)、`@ohos.arkui.UIContext.d.ts` (实例级 SDK)、`@ohos.router.static.d.ets` (Static SDK since 23)、`page_router_manager.h/.cpp` (核心实现)、`js_router.cpp` (NAPI 绑定)、`frontend_delegate_impl.cpp` (代理层)
