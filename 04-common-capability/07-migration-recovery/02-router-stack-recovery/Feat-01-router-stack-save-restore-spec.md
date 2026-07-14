# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 路由栈保存与恢复机制 |
| 特性编号 | Func-04-07-02-Feat-01 |
| 所属 Epic | 路由栈恢复（04-07-02） |
| 优先级 | P1 |
| 目标版本 | API 14+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 较高（recoverable 标记过滤 + 惰性恢复 + 组件级状态 + 三场景 + 双模型差异） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | RouterOptions.recoverable?: boolean | since 14，默认 true；控制页面是否参与路由栈恢复序列化 |
| ADDED | NamedRouterOptions.recoverable?: boolean | since 14，默认 true；命名路由页面是否参与恢复 |
| ADDED | ContentInfoType RESOURCESCHEDULE_RECOVERY (3) | 资源调度杀进程恢复场景；recoverable=false 的页面被过滤 |
| ADDED | RestoreRouterStack 惰性恢复机制 | top 页立即加载，其余存入 restorePageStack_ (RouterRecoverRecord) |
| ADDED | RouterRecoverRecord 结构 | 记录 url/name/params/recoverable/componentInfo/destination |
| ADDED | RestorePageDestination 枚举 | TOP/BELLOW_TOP/BOTTOM，标记恢复页在栈中的插入位置 |
| ADDED | RecoverableManager 组件级状态持久化 | 注册 save callback，序列化为 componentInfo |
| ADDED | RecoverableView mixin OnSaveData() | 组件自定义状态保存回调 |
| ADDED | StartRestore 惰性恢复触发 | back() 到栈底 + restorePageStack_ 不空 → StartRestore |
| ADDED | ReplaceRecoverable 更新机制 | MovePageToFront 时更新 recoverable 标记 |
| MODIFIED | UIContentImpl.GetContentInfo | 支持 3 种 ContentInfoType 场景序列化 |
| MODIFIED | UIContentImpl.Restore | 接收序列化数据触发 RestoreRouterStack |
| MODIFIED | PageRouterManager.GetStackInfo | 按 ContentInfoType 过滤 recoverable=false 的页面 |
| MODIFIED | PageRouterManager.back() | 栈仅 1 页 + restorePageStack_ 非空 → StartRestore |

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| SDK Dynamic | `interface/sdk-js/api/@ohos.router.d.ts` (RouterOptions.recoverable since 14) |
| SDK Dynamic | `interface/sdk-js/api/@internal/component/ets/router.d.ts` (NamedRouterOptions.recoverable) |
| NAPI Source | `interfaces/napi/kits/router/js_router.cpp` (ParseRecoverable) |
| Core Source | `frameworks/bridge/declarative_frontend/ng/page_router_manager.h/.cpp` (GetStackInfo/RestoreRouterStack/StartRestore) |
| Core Source | `frameworks/core/components_ng/recoverable/recoverable_manager.h/.cpp` |
| Core Source | `adapter/ohos/entrance/ui_content_impl.cpp` (GetContentInfo/Restore) |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: recoverable 标记设置

作为应用开发者，我想要在路由跳转时通过 RouterOptions.recoverable 标记页面是否参与恢复，以便在资源调度杀进程等场景下排除临时或敏感页面。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN pushUrl/pushName 传入 RouterOptions.recoverable=true THEN 页面 EntryPageInfo.recoverable_=true，GetStackInfo 包含该页 | 正常 |
| AC-1.2 | WHEN pushUrl/pushName 传入 RouterOptions.recoverable=false THEN 页面 EntryPageInfo.recoverable_=false，GetStackInfo(RESOURCESCHEDULE_RECOVERY) 排除该页 | 正常 |
| AC-1.3 | WHEN 不传入 recoverable THEN 默认值为 true，页面参与恢复序列化 | 正常 |
| AC-1.4 | WHEN MovePageToFront 被调用 THEN 通过 ReplaceRecoverable 更新目标页 recoverable 标记 | 正常 |
| AC-1.5 | WHEN Force-split 并行页 THEN 并行页 recoverable 设置为 false | 边界 |
| AC-1.6 | WHEN recoverable 为非 boolean 类型 THEN ParseRecoverable 解析为默认 true | 边界 |

### US-2: 路由栈保存序列化

作为系统开发者，我想要在 UIContentImpl.GetContentInfo 中按 ContentInfoType 场景序列化路由栈信息，以便在不同恢复场景下提供差异化的栈数据。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN ContentInfoType=CONTINUATION(1) THEN GetStackInfo 序列化全部页面，不受 recoverable 过滤 | 正常 |
| AC-2.2 | WHEN ContentInfoType=APP_RECOVERY(2) THEN GetStackInfo 序列化全部页面，不受 recoverable 过滤 | 正常 |
| AC-2.3 | WHEN ContentInfoType=RESOURCESCHEDULE_RECOVERY(3) THEN GetStackInfo 仅序列化 recoverable=true 的页面，recoverable=false 的页面被跳过 | 正常 |
| AC-2.4 | WHEN 栈为空 THEN GetStackInfo 返回空序列化数据 | 边界 |
| AC-2.5 | WHEN 栈中全部页面 recoverable=false 且 ContentInfoType=RESOURCESCHEDULE_RECOVERY THEN GetStackInfo 返回空数据 | 边界 |
| AC-2.6 | WHEN 栈中有混合 recoverable 页面且 ContentInfoType=RESOURCESCHEDULE_RECOVERY THEN 仅 recoverable=true 的页面序列化，保留栈顺序 | 正常 |
| AC-2.7 | WHEN GetStackInfo 序列化 THEN 每页包含 name/url/params/componentInfo 字段 | 正常 |
| AC-2.8 | WHEN 栈满 32 页 THEN GetStackInfo 仍正确序列化所有（recoverable=true 的）页面 | 边界 |

### US-3: 路由栈惰性恢复

作为系统开发者，我想要在 RestoreRouterStack 中仅立即加载栈顶页，其余存入 restorePageStack_ 惰性恢复，以便快速恢复用户可见页面同时降低冷启动开销。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN RestoreRouterStack 被调用 THEN 栈顶页(TOP destination)立即通过 RestorePageWithTargetInner 加载 | 正常 |
| AC-3.2 | WHEN RestoreRouterStack 被调用 THEN 非栈顶页存入 restorePageStack_ 作为 RouterRecoverRecord | 正常 |
| AC-3.3 | WHEN back() 且 pageRouterStack_ 仅剩 1 页且 restorePageStack_ 非空 THEN 触发 StartRestore 惰性恢复下一页 | 正常 |
| AC-3.4 | WHEN StartRestore 被触发 THEN 调用 RestorePageWithTargetInner(BELLOW_TOP) 将恢复页插入栈顶下方再弹出栈顶 | 正常 |
| AC-3.5 | WHEN restorePageStack_ 中有多个记录 THEN 每次 back 仅恢复 1 页（逐页惰性恢复） | 正常 |
| AC-3.6 | WHEN restorePageStack_ 为空 THEN back() 正常弹出栈顶页（不触发 StartRestore） | 正常 |
| AC-3.7 | WHEN RestoreRouterStack 传入空数据 THEN pageRouterStack_ 和 restorePageStack_ 均为空 | 边界 |
| AC-3.8 | WHEN RestoreRouterStack 传入仅 1 页数据 THEN 立即加载为栈顶页，restorePageStack_ 为空 | 边界 |
| AC-3.9 | WHEN RestoreRouterStack 接收 BOTTOM destination 页 THEN 该页被加载到栈底位置 | 正常 |

### US-4: 组件级状态持久化

作为应用开发者，我想要通过 RecoverableManager 注册组件状态保存回调，以便恢复时能还原组件内部状态（如选中项、滚动位置等）。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN RecoverableManager 注册 save callback THEN 在 GetStackInfo 时遍历当前页所有注册回调并收集 componentInfo | 正常 |
| AC-4.2 | WHEN RecoverableView mixin 实现 OnSaveData() THEN 返回的自定义状态数据被序列化到 componentInfo 字段 | 正常 |
| AC-4.3 | WHEN 页面无注册 RecoverableManager callback THEN componentInfo 字段为空 | 边界 |
| AC-4.4 | WHEN 恢复页面 THEN componentInfo 从 RouterRecoverRecord 中取出用于组件状态还原 | 正常 |
| AC-4.5 | WHEN 页面 recoverable=false THEN 该页的 RecoverableManager callback 不被调用（页面整体跳过） | 正常 |
| AC-4.6 | WHEN 多个组件在同一页注册 callback THEN componentInfo 包含所有组件的状态数据（按注册顺序合并） | 正常 |

### US-5: FA/Stage 双模型兼容

作为系统开发者，我想要确保路由栈保存与恢复在 Stage (NG) 和 FA (旧管线) 双模型下行为一致或差异明确，以便维护兼容性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN NG 管线(Stage 模型) THEN GetStackInfo 完整支持 recoverable 过滤 + RecoverableManager + 惰性恢复 | 正常 |
| AC-5.2 | WHEN FA 旧管线 THEN GetStackInfo 无 per-page recoverable 过滤，所有页面均序列化 | 正常 |
| AC-5.3 | WHEN FA 旧管线 THEN restorePageStack_ 和 RouterRecoverRecord 仍可用 | 正常 |
| AC-5.4 | WHEN NG 管线 + DynamicExtender 模式 THEN GetStackInfo/RestoreRouterStack 优先走 Dynamic 分支 | 正常 |
| AC-5.5 | WHEN 跨模型序列化数据 THEN NG 恢复管线兼容 FA 序列化格式（无 recoverable 字段时默认 true） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.6 | R-1 ~ R-6 | TASK-01 | 单测 ParseRecoverable/ReplaceRecoverable | `js_router.cpp:ParseRecoverable` / `page_router_manager.cpp:ReplaceRecoverable` |
| AC-2.1 ~ AC-2.8 | R-7 ~ R-14 | TASK-02 | 单测 GetStackInfo 三场景 | `page_router_manager.cpp:GetStackInfo` / `ui_content_impl.cpp:GetContentInfo` |
| AC-3.1 ~ AC-3.9 | R-15 ~ R-23 | TASK-03 | 单测 RestoreRouterStack/StartRestore | `page_router_manager.cpp:RestoreRouterStack` / `StartRestore` |
| AC-4.1 ~ AC-4.6 | R-24 ~ R-29 | TASK-04 | 单测 RecoverableManager/RecoverableView | `recoverable_manager.cpp:SaveData` |
| AC-5.1 ~ AC-5.5 | R-30 ~ R-34 | TASK-05 | 单测 FA/Stage 双模型 | `page_router_manager.cpp:GetStackInfo` (FA 分支) |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | pushUrl 传入 recoverable=true | EntryPageInfo.recoverable_=true；GetStackInfo 包含该页 | 默认值 true | AC-1.1 |
| R-2 | 行为 | pushUrl 传入 recoverable=false | EntryPageInfo.recoverable_=false；RESOURCESCHEDULE_RECOVERY 场景排除该页 | 仅 RESOURCESCHEDULE_RECOVERY 过滤 | AC-1.2 |
| R-3 | 行为 | 不传入 recoverable | ParseRecoverable 默认设为 true | JS undefined → true | AC-1.3 |
| R-4 | 行为 | MovePageToFront 被调用 | ReplaceRecoverable 更新目标页 recoverable 标记 | 并行页场景 | AC-1.4 |
| R-5 | 边界 | Force-split 并行页 | 并行页 recoverable 设为 false | SplitPage→ReplaceRecoverable(false) | AC-1.5 |
| R-6 | 边界 | recoverable 为非 boolean | ParseRecoverable 解析为默认 true | napi_typeof ≠ napi_boolean → true | AC-1.6 |
| R-7 | 行为 | ContentInfoType=CONTINUATION | GetStackInfo 序列化全部页面，不按 recoverable 过滤 | 跨设备迁移需要完整栈 | AC-2.1 |
| R-8 | 行为 | ContentInfoType=APP_RECOVERY | GetStackInfo 序列化全部页面，不按 recoverable 过滤 | 崩溃恢复需要完整栈 | AC-2.2 |
| R-9 | 行为 | ContentInfoType=RESOURCESCHEDULE_RECOVERY | 仅序列化 recoverable=true 的页面；recoverable=false 的页面跳过 | 资源调度杀进程，过滤临时页 | AC-2.3 |
| R-10 | 边界 | 栈为空 | GetStackInfo 返回空序列化数据 | 无页可序列化 | AC-2.4 |
| R-11 | 边界 | 全部 recoverable=false + RESOURCESCHEDULE_RECOVERY | 返回空数据 | 所有页面被过滤 | AC-2.5 |
| R-12 | 行为 | 混合 recoverable 页面 + RESOURCESCHEDULE_RECOVERY | 仅 recoverable=true 页序列化，保留栈内顺序 | recoverable=false 页跳过但顺序不变 | AC-2.6 |
| R-13 | 行为 | GetStackInfo 序列化单页 | 包含 name/url/params/componentInfo 字段 | EntryPageInfo 序列化格式 | AC-2.7 |
| R-14 | 边界 | 栈满 32 页 | GetStackInfo 正确序列化所有 recoverable=true 的页面 | 序列化无上限限制（栈有 32 上限） | AC-2.8 |
| R-15 | 行为 | RestoreRouterStack 被调用 | 栈顶页 (RestorePageDestination=TOP) 立即通过 RestorePageWithTargetInner(TOP) 加载 | 立即恢复用户可见页 | AC-3.1 |
| R-16 | 行为 | RestoreRouterStack 被调用 | 非栈顶页存入 restorePageStack_ 作为 RouterRecoverRecord | destination=BELLOW_TOP/BOTTOM | AC-3.2 |
| R-17 | 行为 | back() + pageRouterStack_ 仅 1 页 + restorePageStack_ 非空 | 触发 StartRestore 惰性恢复 | 检测条件：size()==1 && !restorePageStack_.empty() | AC-3.3 |
| R-18 | 行为 | StartRestore 被触发 | RestorePageWithTargetInner(BELLOW_TOP)：插入恢复页到栈顶下方再弹出栈顶 | BELLOW_TOP 恢复策略 | AC-3.4 |
| R-19 | 行为 | restorePageStack_ 有多条记录 | 每次 back 仅恢复 1 条 RouterRecoverRecord | 逐页惰性恢复 | AC-3.5 |
| R-20 | 边界 | restorePageStack_ 为空 | back() 正常弹出栈顶页，不触发 StartRestore | restorePageStack_.empty() | AC-3.6 |
| R-21 | 边界 | RestoreRouterStack 传入空数据 | pageRouterStack_ 和 restorePageStack_ 均为空 | 空恢复数据 | AC-3.7 |
| R-22 | 边界 | RestoreRouterStack 仅 1 页数据 | 立即加载为栈顶页，restorePageStack_ 为空 | 单页恢复无需惰性 | AC-3.8 |
| R-23 | 行为 | BOTTOM destination 页恢复 | RestorePageWithTargetInner(BOTTOM) 加载到栈底位置 | 栈底恢复策略 | AC-3.9 |
| R-24 | 行为 | RecoverableManager 注册 save callback | GetStackInfo 时遍历当前页注册回调并收集 componentInfo | 每页独立 RecoverableManager | AC-4.1 |
| R-25 | 行为 | RecoverableView OnSaveData() | 返回的自定义状态数据序列化到 componentInfo 字段 | JSON 格式 | AC-4.2 |
| R-26 | 边界 | 页面无注册 RecoverableManager callback | componentInfo 字段为空 | 无状态数据 | AC-4.3 |
| R-27 | 行为 | 恢复页面 | componentInfo 从 RouterRecoverRecord 中取出用于组件状态还原 | OnRestoreData 反序列化 | AC-4.4 |
| R-28 | 行为 | 页面 recoverable=false | RecoverableManager callback 不被调用 | 页面整体跳过 | AC-4.5 |
| R-29 | 行为 | 多组件同页注册 callback | componentInfo 包含所有组件状态数据，按注册顺序合并 | 合并序列化 | AC-4.6 |
| R-30 | 行为 | NG 管线 (Stage 模型) | 完整支持 recoverable 过滤 + RecoverableManager + 惰性恢复 | 全功能 | AC-5.1 |
| R-31 | 行为 | FA 旧管线 | 无 per-page recoverable 过滤，所有页面均序列化 | 简化序列化 | AC-5.2 |
| R-32 | 行为 | FA 旧管线 | restorePageStack_ 和 RouterRecoverRecord 仍可用 | 共享恢复机制 | AC-5.3 |
| R-33 | 行为 | NG + DynamicExtender | GetStackInfo/RestoreRouterStack 优先走 Dynamic 分支 | ArkTS frontend | AC-5.4 |
| R-34 | 边界 | 跨模型序列化数据兼容 | 无 recoverable 字段时默认 true | FA→NG 兼容 | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | recoverable 标记默认 true | 单测：pushUrl 不传 recoverable → GetStackInfo(RESOURCESCHEDULE_RECOVERY) 包含该页 | 默认行为 |
| VM-2 | recoverable=false 过滤 | 单测：pushUrl(recoverable=false) → GetStackInfo(RESOURCESCHEDULE_RECOVERY) 不包含该页；GetStackInfo(CONTINUATION) 包含 | 三场景差异 |
| VM-3 | 惰性恢复 TOP/BELLOW_TOP | 单测：RestoreRouterStack(3 页数据) → 仅栈顶加载，其余存 restorePageStack_；back → StartRestore | 逐页恢复 |
| VM-4 | RecoverableManager componentInfo | 单测：注册 save callback → GetStackInfo 包含 componentInfo；恢复 → 组件状态还原 | 状态持久化 |
| VM-5 | FA 旧管线无 recoverable 过滤 | 单测：FA 管线 GetStackInfo → 全部页序列化 | 双模型差异 |
| VM-6 | restorePageStack_ 清空时机 | 单测：clear() → restorePageStack_ 清空；RestoreRouterStack 空 → 两个栈均为空 | 恢复栈管理 |
| VM-7 | GetStackInfo 三场景序列化格式 | 单测：构建 3 页栈 → 分别调用 GetStackInfo(CONTINUATION/APP_RECOVERY/RESOURCESCHEDULE_RECOVERY) → 验证序列化数据 | 场景差异化 |
| VM-8 | StartRestore BELLOW_TOP 策略 | 单测：RestoreRouterStack(2 页) → 栈顶加载 → back → StartRestore → 恢复页在栈顶下方 → 弹出栈顶 | 插入位置 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| RouterOptions.recoverable | Public (since 14) | boolean (可选) | — | — | 控制页面是否参与恢复序列化 | AC-1.1, AC-1.2, AC-1.3 |
| NamedRouterOptions.recoverable | Public (since 14) | boolean (可选) | — | — | 命名路由页面是否参与恢复 | AC-1.1, AC-1.2, AC-1.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| UIContentImpl.GetContentInfo | MODIFIED (since 14) | 增加 ContentInfoType=RESOURCESCHEDULE_RECOVERY 场景 | 无需迁移 | AC-2.3 |
| UIContentImpl.Restore | MODIFIED (since 14) | 支持惰性恢复 | 无需迁移 | AC-3.1 |
| PageRouterManager.back() | MODIFIED (since 14) | 增加 StartRestore 触发条件 | 无需迁移 | AC-3.3 |

> **注意:** recoverable 标记和恢复机制均为框架内部行为，开发者仅需在 RouterOptions 中设置 recoverable 字段；save/restore 生命周期由框架自动调度，无显式 save/restore 公共 API。

## 接口规格

### RouterOptions.recoverable

| 属性 | 值 |
|------|-----|
| 函数签名 | `recoverable?: boolean` (RouterOptions 属性) |
| 返回值 | — (属性) |
| 开放范围 | Public (since 14) |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2, AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| recoverable | boolean | 否 | true | true=参与恢复；false=RESOURCESCHEDULE_RECOVERY 场景排除 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | recoverable=true | 页面参与所有场景恢复序列化 | AC-1.1 |
| 2 | recoverable=false | RESOURCESCHEDULE_RECOVERY 场景排除该页；CONTINUATION/APP_RECOVERY 场景仍包含 | AC-1.2 |
| 3 | 不传入 recoverable | 默认 true | AC-1.3 |
| 4 | 传入非 boolean | ParseRecoverable 默认 true | AC-1.6 |
| 5 | MovePageToFront | ReplaceRecoverable 更新标记 | AC-1.4 |

### NamedRouterOptions.recoverable

| 属性 | 值 |
|------|-----|
| 函数签名 | `recoverable?: boolean` (NamedRouterOptions 属性) |
| 返回值 | — (属性) |
| 开放范围 | Public (since 14) |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2, AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| recoverable | boolean | 否 | true | 命名路由页面是否参与恢复；语义同 RouterOptions.recoverable |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | pushNamedRouter recoverable=true | 命名路由页面参与恢复序列化 | AC-1.1 |
| 2 | pushNamedRouter recoverable=false | RESOURCESCHEDULE_RECOVERY 场景排除该命名路由页 | AC-1.2 |
| 3 | 不传入 recoverable | 默认 true | AC-1.3 |

### GetStackInfo (内部)

| 属性 | 值 |
|------|-----|
| 函数签名 | `GetStackInfo(ContentInfoType type): string` |
| 返回值 | `string` — 序列化路由栈 JSON |
| 开放范围 | Internal (framework) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 ~ AC-2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | ContentInfoType | 是 | 无 | 1=CONTINUATION, 2=APP_RECOVERY, 3=RESOURCESCHEDULE_RECOVERY |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | type=CONTINUATION | 序列化全部页面 | AC-2.1 |
| 2 | type=APP_RECOVERY | 序列化全部页面 | AC-2.2 |
| 3 | type=RESOURCESCHEDULE_RECOVERY | 仅序列化 recoverable=true 页面 | AC-2.3 |
| 4 | 栈为空 | 返回空数据 | AC-2.4 |
| 5 | 全部 recoverable=false + type=3 | 返回空数据 | AC-2.5 |

### RestoreRouterStack (内部)

| 属性 | 值 |
|------|-----|
| 函数签名 | `RestoreRouterStack(const std::string& contentInfo): void` |
| 返回值 | `void` |
| 开放范围 | Internal (framework) |
| 错误码 | N/A |
| 关联 AC | AC-3.1 ~ AC-3.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| contentInfo | string | 是 | 无 | GetStackInfo 序列化输出的 JSON 字符串 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 多页数据 | 栈顶页立即加载，其余存 restorePageStack_ | AC-3.1, AC-3.2 |
| 2 | 仅 1 页数据 | 立即加载栈顶页 | AC-3.8 |
| 3 | 空数据 | 两个栈均为空 | AC-3.7 |
| 4 | BOTTOM destination 页 | 加载到栈底 | AC-3.9 |

### StartRestore (内部)

| 属性 | 值 |
|------|-----|
| 函数签名 | `StartRestore(): void` |
| 返回值 | `void` |
| 开放范围 | Internal (framework) |
| 错误码 | N/A |
| 关联 AC | AC-3.3, AC-3.4, AC-3.5 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | back() + pageRouterStack_ 仅 1 页 + restorePageStack_ 非空 | RestorePageWithTargetInner(BELLOW_TOP) | AC-3.3, AC-3.4 |
| 2 | restorePageStack_ 有多条记录 | 仅恢复 1 页 | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否，RouterOptions.recoverable 为新增可选属性，默认 true 保持向后兼容
- **配置文件格式变更:** 否
- **数据存储格式变更:** 是，GetStackInfo 序列化格式新增 recoverable 和 componentInfo 字段；FA→NG 兼容（缺失字段默认 true）
- **最低支持版本:** API 14 (recoverable 属性)；GetStackInfo/RestoreRouterStack 内部机制 API 8+ 可用但无 recoverable 过滤
- **API 版本号策略:** RouterOptions.recoverable since 14；NamedRouterOptions.recoverable since 14；GetStackInfo/RestoreRouterStack 内部接口无 @since 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双栈结构 | pageRouterStack_ (活跃栈) + restorePageStack_ (惰性恢复栈) | AC-3.1, AC-3.2, AC-3.3 |
| 栈上限 32 | 活跃栈上限 32；恢复栈无硬上限 | AC-2.8 |
| recoverable 仅影响 RESOURCESCHEDULE_RECOVERY | CONTINUATION/APP_RECOVERY 场景不过滤 | AC-2.1, AC-2.2, AC-2.3 |
| 惰性恢复逐页触发 | 每次 back 仅恢复 1 页，非一次性全栈恢复 | AC-3.5 |
| RecoverableManager 页级隔离 | 每页独立 RecoverableManager，页面销毁时注销 | AC-4.1, AC-4.5 |
| FA 管线简化 | FA 不支持 per-page recoverable 过滤 | AC-5.2 |
| DynamicExtender 优先 | ArkTS frontend 下优先走 Dynamic 分支 | AC-5.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | GetStackInfo 序列化 < 5ms (32 页栈) | 单测计时 | page_router_manager.cpp |
| 性能 | RestoreRouterStack 栈顶页加载 < 1s | 端到端测试 | UIContentImpl.Restore |
| 安全 | recoverable=false 的敏感数据不泄露到 RESOURCESCHEDULE_RECOVERY 序列化 | 单测验证过滤 | GetStackInfo(RESOURCESCHEDULE_RECOVERY) 排除 recoverable=false 页 |
| 可靠性 | 惰性恢复逐页触发，不会一次性恢复导致内存峰值 | 内存监控 | restorePageStack_ 逐条恢复 |
| 可测试性 | RecoverableManager Mock 可隔离 | Mock 策略 | save callback 注册/注销 |
| 自动化维测 | 恢复栈日志 | hilog | TAG_LOGI(AceLogTag::ACE_ROUTER) "RestoreRouterStack"/"StartRestore" |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | recoverable 过滤 + 惰性恢复 | XTS | CONTINUATION 跨设备迁移 |
| 平板 | 无差异 | 同上 | XTS | 同上 |
| 折叠屏 | 无差异 | 同上 | XTS | 同上 |
| 穿戴 | FA 管线 | 无 recoverable 过滤 | XTS | FA 简化序列化 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 恢复机制为框架内部行为，无无障碍特殊处理 | — |
| 大字体 | 否 | 恢复机制无 UI 层影响 | — |
| 深色模式 | 否 | 恢复机制无主题相关行为 | — |
| 多窗口/分屏 | 是 | UIContentImpl 绑定特定 Ability Context，多窗口各自独立恢复 | 多 Ability 场景 |
| 多用户 | 否 | Router 为单 Ability 内栈管理 | — |
| 版本升级 | 是 | API 14 新增 recoverable 属性，之前版本无此字段 | 跨版本兼容 |
| 生态兼容 | 是 | FA→NG 序列化格式兼容（缺失 recoverable 默认 true） | 跨模型兼容 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 路由栈保存与恢复机制
  作为系统开发者
  我想要在进程被杀或迁移时保存路由栈并在重启后恢复
  以便用户返回应用时能看到之前浏览的页面

  Scenario: recoverable=true 页面参与恢复序列化
    Given 路由栈中有 PageA(recoverable=true) 和 PageB(recoverable=true)
    When 系统调用 GetStackInfo(RESOURCESCHEDULE_RECOVERY)
    Then 序列化数据包含 PageA 和 PageB

  Scenario: recoverable=false 页面被过滤
    Given 路由栈中有 PageA(recoverable=true) 和 TempPage(recoverable=false)
    When 系统调用 GetStackInfo(RESOURCESCHEDULE_RECOVERY)
    Then 序列化数据仅包含 PageA

  Scenario: CONTINUATION 场景不过滤
    Given 路由栈中有 PageA(recoverable=true) 和 TempPage(recoverable=false)
    When 系统调用 GetStackInfo(CONTINUATION)
    Then 序列化数据包含 PageA 和 TempPage

  Scenario: 惰性恢复栈顶页立即加载
    Given 恢复数据包含 PageA(BOTTOM)、PageB(BELLOW_TOP)、PageC(TOP)
    When RestoreRouterStack 被调用
    Then PageC 立即加载为栈顶页
    And PageB 和 PageA 存入 restorePageStack_

  Scenario: back 触发惰性恢复
    Given 活跃栈仅 PageC，restorePageStack_ 有 PageB
    When 用户执行 back 操作
    Then PageB 通过 StartRestore 惰性恢复到栈顶下方
    And PageC 被弹出

  Scenario: clear 清空恢复栈
    Given 活跃栈有 PageC，restorePageStack_ 有 PageB 和 PageA
    When 调用 router.clear()
    Then restorePageStack_ 被清空
    And 活跃栈仅剩 PageC

  Scenario: RecoverableManager 状态持久化
    Given PageC 注册了 RecoverableManager save callback
    When 系统调用 GetStackInfo
    Then 序列化数据包含 PageC 的 componentInfo

  Scenario Outline: recoverable 默认值
    Given pushUrl 传入 recoverable=<input>
    Then EntryPageInfo.recoverable_=<expected>

    Examples:
      | input | expected |
      | true | true |
      | false | false |
      | 未传入 | true |
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
    query: "PageRouterManager GetStackInfo/RestoreRouterStack/StartRestore/ReplaceRecoverable recoverable 标记过滤与惰性恢复实现细节"
  - repo: "openharmony/ace_engine"
    query: "js_router.cpp ParseRecoverable RouterOptions.recoverable/NamedRouterOptions.recoverable NAPI 解析与默认值处理"
  - repo: "openharmony/ace_engine"
    query: "RecoverableManager RecoverableView OnSaveData 组件级状态持久化 componentInfo 序列化与恢复"
  - repo: "openharmony/ace_engine"
    query: "UIContentImpl GetContentInfo/Restore ContentInfoType CONTINUATION/APP_RECOVERY/RESOURCESCHEDULE_RECOVERY 三场景序列化差异"
```

**关键文档：** `@ohos.router.d.ts` (RouterOptions.recoverable since 14)、`page_router_manager.h/.cpp` (GetStackInfo/RestoreRouterStack/StartRestore)、`js_router.cpp` (ParseRecoverable)、`recoverable_manager.h/.cpp` (RecoverableManager)、`ui_content_impl.cpp` (GetContentInfo/Restore)
