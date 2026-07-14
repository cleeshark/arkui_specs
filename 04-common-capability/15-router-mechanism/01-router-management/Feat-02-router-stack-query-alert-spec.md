# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 路由栈查询与弹窗拦截 |
| 特性编号 | Func-04-15-01-Feat-02 |
| 所属 Epic | 路由管理（04-15-01） |
| 优先级 | P1 |
| 目标版本 | API 8 ~ API 23+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（多查询 API + 弹窗拦截 + deprecated 链 + UIContext 双路径） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | getLength 返回类型 string | since 8，deprecated since 23→getStackSize；SDK 签名 string，NAPI 实现 int32→coerce_to_string |
| MODIFIED | getStackSize 返回类型 number | since 23，替代 getLength；NAPI 实现 int32→napi_create_int32 |
| MODIFIED | getState 返回 RouterState | since 8，deprecated since 18；index 从 1 起（自底向顶）；params since 12 |
| MODIFIED | getStateByIndex / getStateByUrl | since 12，deprecated since 18；按索引/按 URL 查询 RouterState |
| MODIFIED | getParams 返回 Object | since 8，deprecated since 18；返回当前栈顶页 params；insertPageProcessingType_ 影响取页逻辑 |
| MODIFIED | clear 清空栈 | since 8，deprecated since 18；保留栈顶页；restorePageStack_ 一并清空 |
| MODIFIED | showAlertBeforeBackPage 设置弹窗拦截 | since 9，deprecated since 18；EnableAlertOptions.message 为必填 string；错误码 401/100001 |
| MODIFIED | hideAlertBeforeBackPage 取消弹窗拦截 | since 9，deprecated since 18；清除当前页 alertCallback |
| MODIFIED | enableAlertBeforeBackPage / disableAlertBeforeBackPage | deprecated since 9；功能等同 showAlert/hideAlert |
| MODIFIED | UIContext.Router 实例级 API | since 10/11/12/23；clear/getLength/getStackSize/getState/getStateByIndex/getStateByUrl/getParams/showAlert/hideAlert |
| MODIFIED | recoverable 标记 | since 14；RouterOptions.recoverable 默认 true；影响栈恢复策略（非本 Feat 核心但影响 getState 查询范围） |

## 输入文档

- Design doc: `specs/04-common-capability/15-router-mechanism/01-router-management/design.md`
- SDK 类型定义: `@ohos.router.d.ts` (模块级 Dynamic)、`@ohos.arkui.UIContext.d.ts` (实例级)、`@ohos.router.static.d.ets` (静态级 since 23)
- 核心源码: `interfaces/napi/kits/router/js_router.cpp` (NAPI 绑定)、`frameworks/bridge/declarative_frontend/ng/page_router_manager.h/.cpp` (核心实现)

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 路由栈大小查询

作为应用开发者，我想要查询当前路由栈中页面数量，以便在栈深度接近上限(32)时提示用户或阻止进一步 push。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 调用 router.getLength() THEN 返回 string 类型的栈大小（最大"32"） | 正常 |
| AC-1.2 | WHEN 调用 UIContext.Router.getLength() THEN 返回 string 类型的栈大小（deprecated since 23） | 正常 |
| AC-1.3 | WHEN 调用 UIContext.Router.getStackSize() THEN 返回 number 类型的栈大小（最大 32） | 正常 |
| AC-1.4 | WHEN 栈为空 THEN getLength 返回 "0"、getStackSize 返回 0 | 边界 |
| AC-1.5 | WHEN 栈满 32 页 THEN getLength 返回 "32"、getStackSize 返回 32 | 边界 |
| AC-1.6 | WHEN delegate 未获取 THEN getLength/getStackSize 抛出 BusinessError 100001 | 异常 |
| AC-1.7 | WHEN 页面正在替换(isNewPageReplacing_) THEN GetStackSize 返回 size-1 | 边界 |
| AC-1.8 | WHEN DynamicExtender 模式下 THEN getLength/getStackSize 优先走 Dynamic 分支 | 正常 |

### US-2: 路由栈状态查询

作为应用开发者，我想要查询当前页面或指定页面的路由状态(index/name/path/params)，以便获取页面信息用于 UI 显示或逻辑判断。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 router.getState() THEN 返回 RouterState{index,name,path,params}，index 从 1 起自底向顶 | 正常 |
| AC-2.2 | WHEN 调用 UIContext.Router.getState() THEN 返回 router.RouterState | 正常 |
| AC-2.3 | WHEN 调用 getStateByIndex(index) THEN 返回 RouterState | undefined；index 超范围返回 undefined | 正常 |
| AC-2.4 | WHEN 调用 getStateByUrl(url) THEN 返回 Array\<RouterState> 匹配 url 的所有页面状态 | 正常 |
| AC-2.5 | WHEN 页面正在替换 THEN getState.index 返回 size-1（而非 size） | 边界 |
| AC-2.6 | WHEN 栈为空 THEN getState 返回空 RouterState（index/name/path 为默认值） | 边界 |
| AC-2.7 | WHEN index 指向 restorePageStack_ 中页面 THEN getStateByIndex 返回恢复栈中 PageInfo 的 name/path/params | 边界 |
| AC-2.8 | WHEN DynamicExtender 模式 THEN getState/getStateByIndex/getStateByUrl 优先走 Dynamic 分支 | 正常 |

### US-3: 路由参数获取

作为应用开发者，我想要获取当前页面的路由参数，以便在目标页面中使用传递的数据。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 router.getParams() THEN 返回当前栈顶页的 params Object | 正常 |
| AC-3.2 | WHEN 调用 UIContext.Router.getParams() THEN 返回当前栈顶页的 params Object | 正常 |
| AC-3.3 | WHEN 当前页无 params THEN getParams 返回 undefined 或空 Object | 边界 |
| AC-3.4 | WHEN insertPageProcessingType_ 为 INSERT_BELLOW_TOP THEN getParams 返回栈顶下方页的 params | 边界 |
| AC-3.5 | WHEN insertPageProcessingType_ 为 INSERT_BOTTOM THEN getParams 返回栈底页的 params | 边界 |
| AC-3.6 | WHEN 栈为空 THEN getParams 返回空字符串（NAPI 层转为 undefined） | 边界 |

### US-4: 路由栈清空

作为应用开发者，我想要清空路由栈保留栈顶页，以便重置导航历史。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 调用 router.clear() THEN 清空 pageRouterStack_ 和 restorePageStack_，仅保留当前栈顶页 | 正常 |
| AC-4.2 | WHEN 调用 UIContext.Router.clear() THEN 同 AC-4.1 | 正常 |
| AC-4.3 | WHEN 栈仅 1 页 THEN clear 不执行任何操作（restorePageStack_ 清空，pageRouterStack_ 保持 1 页） | 边界 |
| AC-4.4 | WHEN delegate 未获取 THEN clear 抛出 BusinessError 100001 | 异常 |
| AC-4.5 | WHEN inRouterOpt_ 为 true THEN clear 异步投递 PostAsyncEvent | 边界 |

### US-5: 返回前弹窗拦截

作为应用开发者，我想要在用户执行 back 操作前弹出确认对话框，以便防止误操作返回。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 调用 showAlertBeforeBackPage({message: "确认返回?"}) THEN 设置当前页 alertCallback，后续 back 先弹 AlertDialog | 正常 |
| AC-5.2 | WHEN 调用 UIContext.Router.showAlertBeforeBackPage THEN 同 AC-5.1 | 正常 |
| AC-5.3 | WHEN 用户点击 AlertDialog 确认按钮 THEN 执行 back 操作 | 正常 |
| AC-5.4 | WHEN 用户点击 AlertDialog 取消按钮 THEN 不执行 back 操作 | 正常 |
| AC-5.5 | WHEN 调用 hideAlertBeforeBackPage() THEN 清除当前页 alertCallback，back 不再弹窗 | 正常 |
| AC-5.6 | WHEN 调用 UIContext.Router.hideAlertBeforeBackPage() THEN 同 AC-5.5 | 正常 |
| AC-5.7 | WHEN options.message 为非 string 类型 THEN 抛出 BusinessError 401（参数类型错误） | 异常 |
| AC-5.8 | WHEN options 参数缺失或非 object THEN 抛出 BusinessError 401 | 异常 |
| AC-5.9 | WHEN delegate 未获取 THEN 抛出 BusinessError 100001 | 异常 |
| AC-5.10 | WHEN 栈为空 THEN showAlertBeforeBackPage 不执行（CHECK_NULL_VOID(currentPage)） | 边界 |
| AC-5.11 | WHEN 栈为空 THEN hideAlertBeforeBackPage 直接 return（pageRouterStack_.empty()） | 边界 |
| AC-5.12 | WHEN enableAlertBeforeBackPage 被调用 THEN 功能等同于 showAlertBeforeBackPage（deprecated since 9） | 正常 |
| AC-5.13 | WHEN disableAlertBeforeBackPage 被调用 THEN 功能等同于 hideAlertBeforeBackPage（deprecated since 9） | 正常 |
| AC-5.14 | WHEN DynamicExtender 模式 THEN showAlert/hideAlert 优先走 Dynamic 分支 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.8 | R-1 ~ R-5 | TASK-02 | 单测 getLength/getStackSize | `js_router.cpp:JSRouterGetLength` / `JSRouterGetStackSize` |
| AC-2.1 ~ AC-2.8 | R-6 ~ R-11 | TASK-02 | 单测 getState/getStateByIndex/getStateByUrl | `page_router_manager.cpp:742` / `766` / `817` |
| AC-3.1 ~ AC-3.6 | R-12 ~ R-16 | TASK-02 | 单测 getParams | `page_router_manager.cpp:904` |
| AC-4.1 ~ AC-4.5 | R-17 ~ R-21 | TASK-02 | 单测 clear | `page_router_manager.cpp:445` |
| AC-5.1 ~ AC-5.14 | R-22 ~ R-31 | TASK-02 | 单测 showAlert/hideAlert | `js_router.cpp:1009` / `page_router_manager.cpp:464` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 router.getLength() | 返回 string 类型栈大小，NAPI 先 int32 再 coerce_to_string | 最大 "32" | AC-1.1 |
| R-2 | 行为 | 调用 UIContext.Router.getStackSize() | 返回 number 类型栈大小(pageRouterStack_.size + restorePageStack_.size) | 最大 32 | AC-1.3 |
| R-3 | 边界 | 页面正在替换(isNewPageReplacing_=true) | GetStackSize 返回 size-1 | size 为 0 时 index <=1 不减 | AC-1.7 |
| R-4 | 边界 | 栈为空 | getLength 返回 "0"、getStackSize 返回 0 | 空栈不应发生正常流程 | AC-1.4 |
| R-5 | 异常 | delegate 未获取 | 抛出 BusinessError 100001 ("UI execution context not found") | NAPI 层 NapiThrow | AC-1.6 |
| R-6 | 行为 | 调用 getState() | 返回栈顶页 RouterState{index,name,path,params} | index = restoreStackSize + pageRouterStackSize；isNewPageReplacing_ 时 index-1 | AC-2.1 |
| R-7 | 行为 | 调用 getStateByIndex(index) | index ≤ restoreStackSize → 从 restoreStack 取；index > restoreStackSize → 从 pageRouterStack 取 | index 超范围返回 undefined | AC-2.3 |
| R-8 | 行为 | 调用 getStateByUrl(url) | 遍历 restoreStack + pageRouterStack，匹配 url 的页面收集为 Array | url 完全匹配 pageInfo.GetPageUrl() | AC-2.4 |
| R-9 | 边界 | 栈为空 | getState 返回空 RouterState | index/name/path 保持默认值 | AC-2.6 |
| R-10 | 边界 | index 指向恢复栈 | getStateByIndex 从 restorePageStack_ 取 PageInfo | restoreStack 中页面 params 为 JSON string | AC-2.7 |
| R-11 | 行为 | DynamicExtender 模式 | getState/getStateByIndex/getStateByUrl 优先走 Dynamic 分支 | ArkTS frontend type | AC-2.8 |
| R-12 | 行为 | 调用 getParams() | 返回当前栈顶页 params Object (EntryPageInfo::GetPageParams) | 默认取栈顶；insertPageProcessingType_ 影响取页逻辑 | AC-3.1 |
| R-13 | 边界 | insertPageProcessingType_=INSERT_BELLOW_TOP | getParams 返回栈顶下方页的 params | pageRouterStack_.size < 2 时返回 "" | AC-3.4 |
| R-14 | 边界 | insertPageProcessingType_=INSERT_BOTTOM | getParams 返回栈底页的 params | pageRouterStack_.empty() 时返回 "" | AC-3.5 |
| R-15 | 边界 | 当前页无 params | getParams 返回空 Object 或 undefined | NAPI ParseJSONParams 处理空字符串 | AC-3.3 |
| R-16 | 边界 | 栈为空 | getParams 返回 "" | NAPI 层转为 undefined/null | AC-3.6 |
| R-17 | 行为 | 调用 clear() | 清空 restorePageStack_ 和 pageRouterStack_，仅保留栈顶页 | StartClean() → swap + emplace_back(last) | AC-4.1 |
| R-18 | 边界 | 栈仅 1 页 | clear 不移除，仅清空 restorePageStack_ | pageRouterStack_.size()==1 时 restorePageStack_.clear() | AC-4.3 |
| R-19 | 异常 | delegate 未获取 | 抛出 BusinessError 100001 | NAPI 层 NapiThrow | AC-4.4 |
| R-20 | 边界 | inRouterOpt_=true | clear 异步投递 PostAsyncEvent | PostAsyncEvent + "ArkUIPageRouterClear" | AC-4.5 |
| R-21 | 行为 | UIContext.Router.clear() | 同模块级 clear，最终调用 PageRouterManager::Clear | 实例级通过 delegate 转发 | AC-4.2 |
| R-22 | 行为 | 调用 showAlertBeforeBackPage({message}) | 设置当前页 DialogProperties(content=message, autoCancel=false, buttons=[cancel,confirm]) + alertCallback | message 必填 | AC-5.1 |
| R-23 | 行为 | 用户点击 AlertDialog 确认按钮(successIndex!=0) | 执行 back → StartBack(ngBackTarget_) | onSuccess 回调判断 successIndex | AC-5.3 |
| R-24 | 行为 | 用户点击 AlertDialog 取消按钮(successIndex==0) | 不执行 back | onSuccess 回调 successIndex=0 | AC-5.4 |
| R-25 | 行为 | 调用 hideAlertBeforeBackPage() | 清除当前页 alertCallback=nullptr | pageInfo->SetAlertCallback(nullptr) | AC-5.5 |
| R-26 | 异常 | options 参数非 object | 抛出 BusinessError 401 | napi_typeof != napi_object → NapiThrow | AC-5.8 |
| R-27 | 异常 | options.message 非 string | 抛出 BusinessError 401 | napi_typeof != napi_string → NapiThrow | AC-5.7 |
| R-28 | 异常 | delegate 未获取 | 抛出 BusinessError 100001 | NapiThrow | AC-5.9 |
| R-29 | 边界 | 栈为空时 showAlert | 不执行（CHECK_NULL_VOID(currentPageNode)） | 空栈无 currentPage | AC-5.10 |
| R-30 | 边界 | 栈为空时 hideAlert | 直接 return（pageRouterStack_.empty()） | 不设置 alertCallback | AC-5.11 |
| R-31 | 行为 | enableAlertBeforeBackPage / disableAlertBeforeBackPage | 功能等同 showAlert / hideAlert（NAPI 绑定同一实现函数） | deprecated since 9；DECLARE_NAPI_FUNCTION("enableAlertBeforeBackPage", JSRouterEnableAlertBeforeBackPage) | AC-5.12/AC-5.13 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | getLength 返回 string | 单测：构建 N 页栈 → 调用 getLength → 验证返回 string 数字 | 类型为 string而非 number |
| VM-2 | getStackSize 返回 number | 单测：构建 N 页栈 → 调用 getStackSize → 验证返回 int32 | 类型为 number |
| VM-3 | GetStackSize 包含恢复栈 | 单测：back→pushUrl→调用 getStackSize → 验证包含 restoreStack size | 双栈合计 |
| VM-4 | getState.index 从 1 起 | 单测：构建 3 页栈 → getState → index=3 | 自底向顶 1-based |
| VM-5 | getStateByIndex 跨恢复栈 | 单测：back→getStateByIndex(1) → 返回恢复栈页面信息 | index ≤ restoreStackSize 分支 |
| VM-6 | getStateByUrl 多匹配 | 单测：pushUrl 同 URL 多次 → getStateByUrl → 返回 Array 长度 > 1 | 数组而非单值 |
| VM-7 | getParams 受 insertPageProcessingType_ 影响 | 单测：设置 INSERT_BELLOW_TOP → getParams 返回下方页 params | 非栈顶页 params |
| VM-8 | clear 仅保留栈顶 | 单测：构建 5 页栈 → clear → getStackSize=1 | restoreStack 也清空 |
| VM-9 | showAlert 弹窗确认→back | 单测：showAlert→模拟确认按钮→验证 back 执行 | successIndex!=0 |
| VM-10 | showAlert 弹窗取消→不 back | 单测：showAlert→模拟取消按钮→验证 back 不执行 | successIndex==0 |
| VM-11 | showAlert 401 错误码 | 单测：传入非 object 参数→捕获 BusinessError 401 | 参数校验 |
| VM-12 | hideAlert 清除 callback | 单测：showAlert→hideAlert→back 不弹窗 | alertCallback=nullptr |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| UIContext.Router.getStackSize() | Public (since 23) | 无 | number | N/A (delegate 缺失返回 0) | 返回路由栈大小(number 类型) | AC-1.3 |
| UIContext.Router.getStateByIndex(index) | Public (since 12) | index: number | RouterState | undefined | 401/无效 index | 按索引查询页面状态 | AC-2.3 |
| UIContext.Router.getStateByUrl(url) | Public (since 12) | url: string | Array\<RouterState> | 401/url 缺失 | 按 URL 查询页面状态 | AC-2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| router.getLength() | 废弃(since 23→getStackSize) | 返回 string 需转型 | 使用 UIContext.Router.getStackSize() 返回 number | AC-1.1 |
| UIContext.Router.getLength() | 废弃(since 23→getStackSize) | 同上 | 使用 UIContext.Router.getStackSize() | AC-1.2 |
| router.getState() | 废弃(since 18→UIContext.Router.getState) | 模块级 API 全部 deprecated | 使用 UIContext.Router.getState() | AC-2.1 |
| router.getStateByIndex() | 废弃(since 18→UIContext.Router.getStateByIndex) | 同上 | 使用 UIContext.Router.getStateByIndex() | AC-2.3 |
| router.getStateByUrl() | 废弃(since 18→UIContext.Router.getStateByUrl) | 同上 | 使用 UIContext.Router.getStateByUrl() | AC-2.4 |
| router.getParams() | 废弃(since 18→UIContext.Router.getParams) | 同上 | 使用 UIContext.Router.getParams() | AC-3.1 |
| router.clear() | 废弃(since 18→UIContext.Router.clear) | 同上 | 使用 UIContext.Router.clear() | AC-4.1 |
| router.showAlertBeforeBackPage() | 废弃(since 18→UIContext.Router.showAlertBeforeBackPage) | 同上 | 使用 UIContext.Router.showAlertBeforeBackPage() | AC-5.1 |
| router.hideAlertBeforeBackPage() | 废弃(since 18→UIContext.Router.hideAlertBeforeBackPage) | 同上 | 使用 UIContext.Router.hideAlertBeforeBackPage() | AC-5.5 |
| enableAlertBeforeBackPage() | 废弃(since 9→showAlertBeforeBackPage) | 名称不规范 | 使用 showAlertBeforeBackPage() | AC-5.12 |
| disableAlertBeforeBackPage() | 废弃(since 9→hideAlertBeforeBackPage) | 名称不规范 | 使用 hideAlertBeforeBackPage() | AC-5.13 |

## 接口规格

### 接口定义

**getLength**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getLength(): string` |
| 返回值 | `string` — 路由栈页面数量（最大"32"） |
| 开放范围 | Public (since 8, deprecated since 23→getStackSize) |
| 错误码 | 100001 (delegate 未获取) |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 无参数 | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 栈有 N 页 | 返回 std::to_string(N)，NAPI coerce_to_string | AC-1.1 |
| 2 | delegate 未获取 | 抛出 BusinessError 100001 | AC-1.6 |
| 3 | DynamicExtender 模式 | 优先走 GetLengthFromDynamicExtender | AC-1.8 |

**getStackSize**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getStackSize(): number` |
| 返回值 | `number` — 路由栈页面数量（最大 32） |
| 开放范围 | Public (since 23) |
| 错误码 | delegate 缺失时返回 0（不抛错） |
| 关联 AC | AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 无参数 | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 栈有 N 页 | 返回 N (int32)，包含 pageRouterStack_ + restorePageStack_ | AC-1.3 |
| 2 | 页面正在替换 | 返回 N-1 | AC-1.7 |
| 3 | delegate 缺失 | 返回 0（不抛 BusinessError） | AC-1.6 |
| 4 | DynamicExtender 模式 | 优先走 GetStackSizeFromDynamicExtender | AC-1.8 |

**getState**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getState(): RouterState` |
| 返回值 | `RouterState { index: number; name: string; path: string; params: Object }` |
| 开放范围 | Public (since 8, deprecated since 18→UIContext.Router.getState) |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 无参数 | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 栈有 N 页 | index = restoreSize + pageRouterSize；isNewPageReplacing_ 时 index-1；name/path 从 pageUrl 解析 | AC-2.1 |
| 2 | 栈为空 | 返回空 RouterState（index/name/path 为默认值） | AC-2.6 |
| 3 | 页面正在替换 | index = size-1 | AC-2.5 |
| 4 | DynamicExtender 模式 | 优先走 GetStateFromDynamicExtender | AC-2.8 |

**getStateByIndex**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getStateByIndex(index: number): RouterState | undefined` |
| 返回值 | `RouterState | undefined` |
| 开放范围 | Public (since 12, deprecated since 18→UIContext.Router.getStateByIndex) |
| 错误码 | 401 (index 参数错误) |
| 关联 AC | AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| index | number | 是 | 无 | 1-based；index ≤ 0 或 > stackSize 返回 undefined |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | index ≤ restoreStackSize | 从 restorePageStack_ 取 PageInfo → 返回 RouterState | AC-2.7 |
| 2 | index > restoreStackSize 且 ≤ totalSize | 从 pageRouterStack_ 取 → 返回 RouterState | AC-2.3 |
| 3 | index 超范围 | 返回 undefined | AC-2.3 |
| 4 | DynamicExtender 模式 | 优先走 GetStateByIndexFromDynamicExtender | AC-2.8 |

**getStateByUrl**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getStateByUrl(url: string): Array<RouterState>` |
| 返回值 | `Array<RouterState>` — 匹配 url 的所有页面状态 |
| 开放范围 | Public (since 12, deprecated since 18→UIContext.Router.getStateByUrl) |
| 错误码 | 401 (url 参数错误) |
| 关联 AC | AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| url | string | 是 | 无 | 页面完整 URL，完全匹配 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | url 匹配多页 | 遍历 restoreStack + pageRouterStack → 返回 Array | AC-2.4 |
| 2 | url 不匹配 | 返回空 Array | AC-2.4 |
| 3 | DynamicExtender 模式 | 优先走 GetStateByUrlFromDynamicExtender | AC-2.8 |

**getParams**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getParams(): Object` |
| 返回值 | `Object` — 当前页路由参数 |
| 开放范围 | Public (since 8, deprecated since 18→UIContext.Router.getParams) |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 无参数 | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常流程 | 返回栈顶页 EntryPageInfo::GetPageParams | AC-3.1 |
| 2 | INSERT_BELLOW_TOP | 返回栈顶下方页 params | AC-3.4 |
| 3 | INSERT_BOTTOM | 返回栈底页 params | AC-3.5 |
| 4 | 栈为空 | 返回 ""（NAPI 层转为 undefined） | AC-3.6 |
| 5 | DynamicExtender 模式 | 优先走 GetParamsFromDynamicExtender | AC-3.2 |

**clear**

| 属性 | 值 |
|------|-----|
| 函数签名 | `clear(): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 8, deprecated since 18→UIContext.Router.clear) |
| 错误码 | 100001 (delegate 未获取) |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 无参数 | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 栈 > 1 页 | StartClean → 保留栈顶，清空 restoreStack | AC-4.1 |
| 2 | 栈 == 1 页 | 仅清空 restoreStack | AC-4.3 |
| 3 | delegate 未获取 | 抛出 BusinessError 100001 | AC-4.4 |
| 4 | inRouterOpt_=true | PostAsyncEvent 异步投递 | AC-4.5 |

**showAlertBeforeBackPage**

| 属性 | 值 |
|------|-----|
| 函数签名 | `showAlertBeforeBackPage(options: EnableAlertOptions): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 9, deprecated since 18→UIContext.Router.showAlertBeforeBackPage) |
| 错误码 | 401 (参数错误), 100001 (内部错误/delegate未获取) |
| 关联 AC | AC-5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options | EnableAlertOptions | 是 | 无 | 必须为 object |
| options.message | string | 是 | 无 | 弹窗显示内容 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 设置当前页 DialogProperties + alertCallback；后续 back 先弹 AlertDialog | AC-5.1 |
| 2 | 确认按钮 | successIndex != 0 → StartBack(ngBackTarget_) | AC-5.3 |
| 3 | 取消按钮 | successIndex == 0 → 不执行 back | AC-5.4 |
| 4 | options 非 object | 抛出 BusinessError 401 | AC-5.8 |
| 5 | message 非 string | 抛出 BusinessError 401 | AC-5.7 |
| 6 | delegate 未获取 | 抛出 BusinessError 100001 | AC-5.9 |
| 7 | 栈为空 | 不执行（CHECK_NULL_VOID） | AC-5.10 |
| 8 | DynamicExtender 模式 | 优先走 ShowAlertBeforeBackPageExtender | AC-5.14 |

**hideAlertBeforeBackPage**

| 属性 | 值 |
|------|-----|
| 函数签名 | `hideAlertBeforeBackPage(): void` |
| 返回值 | `void` |
| 开放范围 | Public (since 9, deprecated since 18→UIContext.Router.hideAlertBeforeBackPage) |
| 错误码 | 100001 (delegate 未获取) |
| 关联 AC | AC-5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 无参数 | — | — | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 清除当前页 alertCallback=nullptr | AC-5.5 |
| 2 | 栈为空 | 直接 return | AC-5.11 |
| 3 | delegate 未获取 | 抛出 BusinessError 100001 | AC-5.9 |
| 4 | DynamicExtender 模式 | 优先走 HideAlertBeforeBackPageExtender | AC-5.14 |

## 兼容性声明

- **已有 API 行为变更:** 否，所有行为均为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 标注按实际引入版本：getLength since 8，getStackSize since 23，getStateByIndex/getStateByUrl since 12，showAlert/hideAlert since 9，UIContext.Router 栈查询 since 10/23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双栈合计 | getStackSize/getState.index 包含 pageRouterStack_ + restorePageStack_ | AC-1.3, AC-2.1 |
| 栈上限 32 | 所有栈查询 API 最大值 32 | AC-1.5 |
| 1-based index | RouterState.index 从 1 起自底向顶 | AC-2.1 |
| DynamicExtender 优先 | ArkTS frontend 下优先走 Dynamic 分支 | AC-1.8, AC-2.8, AC-5.14 |
| insertPageProcessingType_ 影响 getParams | 页面插入状态影响 getParams 取页逻辑 | AC-3.4, AC-3.5 |
| 模块级 deprecated since 18 | 所有模块级 API 标记 deprecated→UIContext.Router | AC-1.1, AC-2.1, AC-3.1, AC-4.1, AC-5.1, AC-5.5 |
| enableAlert/disableAlert deprecated since 9 | NAPI 绑定同一实现函数 | AC-5.12, AC-5.13 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 栈查询 API < 1ms | 单测计时 | getLength/getState/getParams 同步调用 |
| 安全 | 无权限要求 | SDK .d.ts 验证 | SysCap: SystemCapability.ArkUI.ArkUI.Full/Lite |
| 可靠性 | 错误码体系完整（401/100001） | 错误码覆盖 | @ohos.router.d.ts JSDoc |
| 可测试性 | DynamicExtender Mock 可隔离 | Mock 策略 | TryGet*FromDynamicIfNeeded 分支 |
| 自动化维测 | 栈大小日志 | hilog | TAG_LOGI(AceLogTag::ACE_ROUTER) |
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
| 无障碍 | 否 | 栈查询和弹窗拦截无无障碍特殊处理 | — |
| 大字体 | 否 | AlertDialog message 使用系统 DialogTheme | — |
| 深色模式 | 否 | AlertDialog 使用系统主题 | — |
| 多窗口/分屏 | 是 | UIContext.Router 绑定特定 Ability Context，多窗口各自独立栈 | 多 Ability 场景 |
| 多用户 | 否 | Router 为单 Ability 内栈管理 | — |
| 版本升级 | 是 | 模块级 deprecated since 18→迁移至 UIContext.Router | 存量代码迁移 |
| 生态兼容 | 是 | getLength string→getStackSize number 类型变更需注意 | 跨版本兼容 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 路由栈查询与弹窗拦截
  作为应用开发者
  我想要查询路由栈状态和拦截返回操作
  以便管理导航历史和防止误操作

  Scenario: getLength 返回 string 类型栈大小
    Given 路由栈中有 5 个页面
    When 调用 router.getLength()
    Then 返回值类型为 string
    And 返回值为 "5"

  Scenario: getStackSize 返回 number 类型栈大小
    Given 路由栈中有 5 个页面
    When 调用 UIContext.Router.getStackSize()
    Then 返回值类型为 number
    And 返回值为 5

  Scenario: getStackSize 包含恢复栈
    Given 路由栈中有 3 个页面且恢复栈中有 1 个页面
    When 调用 getStackSize()
    Then 返回值为 4

  Scenario: getState 返回栈顶页状态
    Given 路由栈中有 3 个页面，栈顶为 PageC
    When 调用 router.getState()
    Then 返回 RouterState
    And index 为 3
    And name 和 path 为 PageC 的信息

  Scenario: getStateByIndex 查询恢复栈页面
    Given 恢复栈中有 2 个页面(PageA index=1, PageB index=2)，活跃栈有 1 个(PageC index=3)
    When 调用 getStateByIndex(1)
    Then 返回 PageA 的 RouterState

  Scenario: showAlert 弹窗拦截返回
    Given 调用 showAlertBeforeBackPage({message: "确认返回?"})
    When 用户点击确认按钮
    Then 执行 back 操作返回上一页

  Scenario: showAlert 弹窗取消返回
    Given 调用 showAlertBeforeBackPage({message: "确认返回?"})
    When 用户点击取消按钮
    Then 不执行 back 操作，停留在当前页

  Scenario: hideAlert 取消弹窗拦截
    Given 已调用 showAlertBeforeBackPage 设置弹窗拦截
    When 调用 hideAlertBeforeBackPage()
    Then 后续 back 不弹出确认对话框

  Scenario Outline: showAlert 参数校验
    Given 调用 showAlertBeforeBackPage(options)
    When options 类型为 <type>
    Then 抛出 BusinessError <code>

    Examples:
      | type | code |
      | 非object | 401 |
      | message非string | 401 |

  Scenario: clear 清空栈
    Given 路由栈中有 5 个页面
    When 调用 router.clear()
    Then 栈仅剩栈顶页面
    And 恢复栈也清空
    And getStackSize() 返回 1
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
    query: "PageRouterManager 双栈管理 getLength/getStackSize/getState/getStateByIndex/getStateByUrl/getParams/clear/EnableAlertBeforeBackPage/DisableAlertBeforeBackPage 实现细节"
  - repo: "openharmony/ace_engine"
    query: "js_router.cpp NAPI 绑定 JSRouterGetLength/JSRouterGetStackSize/JSRouterGetState/JSRouterGetParams/JSRouterClear/JSRouterEnableAlertBeforeBackPage/JSRouterDisableAlertBeforeBackPage 参数校验和错误码映射"
```

**关键文档：** `@ohos.router.d.ts` (Dynamic SDK)、`@ohos.arkui.UIContext.d.ts` (实例级 SDK)、`@ohos.router.static.d.ets` (Static SDK since 23)、`page_router_manager.h/.cpp` (核心实现)、`js_router.cpp` (NAPI 绑定)、`frontend_delegate_impl.cpp` (代理层)
