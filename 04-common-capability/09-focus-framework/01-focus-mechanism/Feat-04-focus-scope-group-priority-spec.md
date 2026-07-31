# 特性规格

> Func-04-09-01-Feat-04 焦点域、分组与优先级：固化焦点域注册、焦点组边界、优先节点排序、历史接入和生命周期清理行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 焦点域、分组与优先级 |
| 特性编号 | Func-04-09-01-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 当前 NG 实现；公共属性与 C API 自 API 23 提供 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性定义 `focusScopeId`、`focusScopePriority` 在 NG 焦点框架中的运行时模型，包括 FocusManager 的域注册表、Scope 与优先节点的互斥角色、PRIOR/PREVIOUS 的列表顺序、优先候选选择、焦点组与嵌套组边界，以及节点移除、FocusView 关闭和 FreeNode 场景的注册清理。

本特性不重复定义公共属性的声明语法；公共 ArkTS/C 属性契约由 `Func-04-03-03-Feat-05` 承接。Tab/方向/Home/End 如何调用优先节点归 Feat-03，FocusView 恢复目标归 Feat-05，最终请求事务归 Feat-02。

## 本次变更范围（Delta）

> 历史规格补齐，当前实现即规格；重复注册、旧映射残留等可疑行为仅作为风险记录。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 焦点域注册与唯一性 | 补录 FocusManager 以 ID 保存 Scope 弱引用和优先节点列表的行为 |
| ADDED | 焦点组与方向键边界 | 补录 isGroup、arrowKeyStepOut、嵌套组及 FocusView 截断语义 |
| ADDED | PRIOR/PREVIOUS 优先级 | 补录枚举值、前插/后插顺序、后代及 whole-path 过滤 |
| ADDED | 优先历史接入 | 补录首次进入、已有历史、普通 Scope、非嵌套 Group 和同步按 ID 请求的差异 |
| ADDED | 生命周期与多线程清理 | 补录清空属性、节点移除、FocusView 关闭及 FreeNode after-attach 注册 |
| ADDED | 前端与 C API 参数差异 | 补录动态、静态和 Style Modifier 的默认值与非法输入降级 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/design.md` | Baselined |
| 焦点导航规格 | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/Feat-03-focus-navigation-traversal-algorithm-spec.md` | Baselined |
| 公共焦点属性规格 | `specs/04-common-capability/03-common-attributes/03-basic-attributes/Feat-05-focus-attribute-spec.md:88-100,416-451` | 已核验 |
| 焦点域模型 | `frameworks/core/components_ng/event/focus_hub.h:85-89,667-700,877-881` | 已核验 |
| 焦点域实现 | `frameworks/core/components_ng/event/focus_hub.cpp:2773-3055` | 已核验 |
| 注册表实现 | `frameworks/core/components_ng/manager/focus/focus_manager.h:87,305-309,375`、`focus_manager.cpp:329-395` | 已核验 |
| 动态/静态前端 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:13480-13520`、`engine/jsi/nativeModule/arkts_native_common_bridge.cpp:11042-11112`、`frameworks/core/components_ng/base/view_abstract_model_static.cpp:1827-1845` | 已核验 |
| Native 属性入口 | `interfaces/native/node/style_modifier.cpp:1813-1902`、`interfaces/native/native_type.h:1337-1349` | 已核验 |
| 多线程实现 | `frameworks/core/components_ng/event/focus_hub_multithread.cpp:59-90` | 已核验 |

## 用户故事

### US-1: 配置和撤销焦点域

**作为** 焦点属性调用方，  
**我想要** 使用 ID 建立唯一焦点域并配置分组边界，  
**以便** 多个节点能够按同一域参与优先选择。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN FocusType 不是 SCOPE 时调用 SetFocusScopeId THEN 不修改 scope ID、isFocusScope、isGroup 或 arrowKeyStepOut | 边界 |
| AC-1.2 | WHEN SCOPE 使用非空且未被有效 Scope 占用的 ID THEN FocusManager 注册该 Scope，并设置 isFocusScope=true、isGroup 和 arrowKeyStepOut | 正常 |
| AC-1.3 | WHEN同一有效 Scope 以相同 ID 重设分组参数 THEN注册返回重复，但仍更新该 Scope 的 isGroup 和 arrowKeyStepOut，保留原 ID | 正常 |
| AC-1.4 | WHEN其他有效 Scope 使用已占用 ID THEN注册失败，调用节点不成为该 ID 的 Scope；若调用节点原本是其他有效 Scope，仅更新其现有分组参数 | 边界 |
| AC-1.5 | WHEN SCOPE 设置空 ID THEN移除当前 ID 的 Scope 注册，清空 ID，并复位 isFocusScope=false、isGroup=false、arrowKeyStepOut=true | 恢复 |
| AC-1.6 | WHEN动态前端缺少 focusScopeId 参数 THEN不调用设置；WHEN首参非 string THEN按空 ID 处理；isGroup 和 arrowKeyStepOut 非 bool 时分别使用 false 和 true | 异常 |

### US-2: 维护域注册表和优先节点列表

**作为** FocusManager，  
**我想要** 将 Scope 与优先节点按 ID 组织在同一注册项中，  
**以便** 两者可按任意先后顺序创建和销毁。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN AddFocusScope 的 ID 不存在 THEN创建 `{scopeWeak, emptyList}`；WHEN条目存在但 scopeWeak 已失效 THEN替换 Scope 并保留优先列表 | 正常 |
| AC-2.2 | WHEN条目中存在有效 Scope THEN AddFocusScope 返回 false且不替换现有 Scope | 边界 |
| AC-2.3 | WHEN RemoveFocusScope 时优先列表为空 THEN删除整个条目；WHEN列表非空 THEN仅清空 Scope 弱引用并保留列表 | 恢复 |
| AC-2.4 | WHEN优先节点在 Scope 之前注册 THEN创建 scopeWeak 为空的条目；WHEN后续 Scope 注册 THEN填充 Scope 并保留列表 | 正常 |
| AC-2.5 | WHEN移除优先节点后 Scope 为空且列表变空 THEN删除条目；WHEN列表仍有节点或 Scope 有效 THEN保留条目 | 恢复 |

### US-3: 设置和选择 PRIOR/PREVIOUS 节点

**作为** 焦点域实现者，  
**我想要** 对域内候选设置首次优先或恢复优先，  
**以便** 初次进入和返回域时选择不同目标。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN节点自身已是 Focus Scope 时调用 SetFocusScopePriority THEN拒绝设置并保留原角色 | 边界 |
| AC-3.2 | WHEN priority=PRIOR(2000) THEN设置 PRIOR 并追加到列表尾；WHEN priority=PREVIOUS(3000) THEN设置 PREVIOUS 并插入列表头 | 正常 |
| AC-3.3 | WHEN priority 不是 2000 或 3000 THEN设置 AUTO(0)，并在同 ID 的旧状态非 AUTO 时移除该节点的所有匹配列表项 | 边界 |
| AC-3.4 | WHEN scope ID 变更或清空 THEN从旧 ID 列表移除节点；清空时同时将 priority 复位 AUTO | 恢复 |
| AC-3.5 | WHEN查找优先候选 THEN按列表顺序跳过失效 WeakPtr，并仅返回当前 Scope 的结构后代且 IsFocusableWholePath=true 的首个节点 | 正常 |
| AC-3.6 | WHEN同时存在 PREVIOUS 和 PRIOR 候选 THEN最近一次插入的 PREVIOUS 位于最前；若无 PREVIOUS，则最早插入的 PRIOR 优先 | 正常 |
| AC-3.7 | WHEN对同一 ID 重复设置非 AUTO 优先级 THEN当前实现可在列表中保留重复 WeakPtr；候选查找仍返回首个有效匹配 | 边界 |

### US-4: 将优先节点接入 Scope 历史和导航

**作为** Scope 聚焦与导航逻辑，  
**我想要** 按当前历史状态接入优先节点，  
**以便** 不覆盖正常历史恢复，同时支持焦点组原子行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN Scope 没有 lastWeakFocusNode 且存在有效优先候选 THEN将候选到 Scope 的整条 lastWeakFocusNode 链写入，并接受优先子节点 | 正常 |
| AC-4.2 | WHEN普通 Scope 已有历史节点 THEN AcceptFocusOfPriorityChild 返回 false，不以 PRIOR 覆盖历史 | 边界 |
| AC-4.3 | WHEN非嵌套焦点组已有历史节点 THEN尝试把历史改写为 PREVIOUS 候选，并返回 true；即使没有 PREVIOUS 候选也保持组被接受 | 边界 |
| AC-4.4 | WHEN OnFocusScope 首次进入且有优先候选 THEN优先请求该候选；失败后才进入组件自定义节点和普通历史/树序遍历 | 正常 |
| AC-4.5 | WHEN PREVIOUS 候选等于当前历史节点 THEN RequestFocusByPriorityInScope 直接请求该节点；WHEN普通 Scope 已有其他历史节点 THEN返回 false继续后续恢复链 | 正常 |
| AC-4.6 | WHEN同步按 ID 请求目标属于含 PREVIOUS 候选的 Scope THEN在 Flush 前尝试将 Scope 历史指向 PREVIOUS 节点 | 正常 |

### US-5: 应用焦点组和生命周期边界

**作为** 复杂组件与页面容器，  
**我想要** 焦点组边界、注册清理和多线程行为保持一致，  
**以便** 节点销毁或跨视图时不误用失效域。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN节点自身或祖先是非嵌套焦点组 THEN IsInFocusGroup 返回 true；WHEN向上遇到 FocusView THEN停止搜索并返回 false | 边界 |
| AC-5.2 | WHEN焦点组存在任一焦点组祖先 THEN IsNestingFocusGroup 返回 true；非 group 节点始终返回 false | 正常 |
| AC-5.3 | WHEN非嵌套焦点组 arrowKeyStepOut=false 且方向导航失败 THEN由 Feat-03 消费事件并阻止出组；Tab 不受该标志封锁 | 正常 |
| AC-5.4 | WHEN节点 RemoveSelf、FocusView 关闭或显式移除域配置 THEN移除对应 Scope 或优先节点注册；Scope 有优先列表时保留空 Scope 条目 | 恢复 |
| AC-5.5 | WHEN FreeNode 设置/清理 focusScopeId 或 priority THEN不立即修改 FocusManager，挂主树后通过 after-attach UI 任务执行普通注册逻辑 | 边界 |
| AC-5.6 | WHEN公共 C 属性收到非法 bool、非法 priority 或非法 size THEN返回参数错误，并按入口规则复位为默认 group=false、arrowKeyStepOut=true 或 AUTO | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-4 | TASK-SKELETON-F4-1 | Core/Manager UT | `focus_hub.cpp:2773-2805`、`focus_manager.cpp:329-355` |
| AC-1.6 | R-5 | TASK-SKELETON-F4-1 | 前端参数 UT | `js_view_abstract.cpp:13480-13501` |
| AC-2.1~2.5 | R-6~R-8 | TASK-SKELETON-F4-2 | FocusManager UT | `focus_manager.cpp:329-395` |
| AC-3.1~3.4 | R-9~R-11 | TASK-SKELETON-F4-3 | Core UT | `focus_hub.cpp:2823-2861` |
| AC-3.5~3.7 | R-12 | TASK-SKELETON-F4-3 | 真实树与列表 UT | `focus_hub.cpp:2897-2950`、`focus_manager.cpp:357-369` |
| AC-4.1~4.3 | R-13, R-14 | TASK-SKELETON-F4-4 | Scope/Group UT | `focus_hub.cpp:2883-2895,2985-3007` |
| AC-4.4~4.6 | R-15, R-16 | TASK-SKELETON-F4-4 | 聚焦入口 UT | `focus_hub.cpp:1727-1758,2952-3039,2488-2507` |
| AC-5.1~5.3 | R-17 | TASK-SKELETON-F4-5 | 导航边界 UT | `focus_hub.cpp:2863-2880,3042-3055,1362-1371` |
| AC-5.4~5.6 | R-18~R-20 | TASK-SKELETON-F4-5 | 生命周期/FreeNode/C API UT | `focus_manager.cpp:182-203`、`focus_hub_multithread.cpp:59-90`、`style_modifier.cpp:1813-1885` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 边界 | 非 SCOPE 设置 focusScopeId | 不修改域状态（`focus_hub.cpp:2773-2779`） | FocusHub 可存在但角色不变 | AC-1.1 |
| R-2 | 行为 | SCOPE 设置新非空 ID | 先向 FocusManager 注册，成功后设置 ID、Scope、group、step-out（`focus_hub.cpp:2780-2805`） | 同一 Pipeline 内有效 Scope ID 唯一 | AC-1.2 |
| R-3 | 边界 | AddFocusScope 返回重复 | 当前节点已是有效 Scope 时只更新 group/step-out；其他节点不抢占 ID（`focus_hub.cpp:2791-2799`） | 更换 ID 前不主动移除旧 Scope 映射 | AC-1.3, AC-1.4 |
| R-4 | 恢复 | focusScopeId 为空 | 移除当前 Scope 注册并复位 ID/group/step-out（`focus_hub.cpp:2781-2789`） | 默认 arrowKeyStepOut=true | AC-1.5 |
| R-5 | 异常 | 动态前端参数缺失或类型错误 | 缺参不调用；非 string 首参变空 ID；可选 bool 使用 false/true 默认（`js_view_abstract.cpp:13480-13501`） | 静态前端 optional 同样落默认值 | AC-1.6 |
| R-6 | 行为 | FocusManager 添加/移除 Scope | 新建或替换失效 Scope；有效 Scope 拒绝替换（`focus_manager.cpp:329-355`） | 优先列表与 Scope 弱引用共用同一 ID 条目 | AC-2.1~2.3 |
| R-7 | 行为 | 添加优先节点 | PREVIOUS push_front，PRIOR push_back；无条目时创建空 Scope 条目（`focus_manager.cpp:357-370`） | 列表元素为 WeakPtr | AC-2.4, AC-3.2, AC-3.6 |
| R-8 | 恢复 | 移除优先节点 | 删除所有等于目标的列表项；Scope 无效且列表空时删条目（`focus_manager.cpp:372-395`） | Get 列表不清理失效 WeakPtr | AC-2.5 |
| R-9 | 边界 | Scope 自身设置 priority | 拒绝并保留状态（`focus_hub.cpp:2823-2830`） | Scope 与优先节点角色互斥 | AC-3.1 |
| R-10 | 行为 | priority 为 2000/3000 | 映射 PRIOR/PREVIOUS 并按尾/头插入（`focus_hub.cpp:2844-2853`） | 枚举固定 AUTO=0/PRIOR=2000/PREVIOUS=3000 | AC-3.2 |
| R-11 | 恢复 | priority 非 2000/3000、ID 清空或变更 | 复位 AUTO并按条件从旧列表移除（`focus_hub.cpp:2832-2860`） | 重复非 AUTO 设置不会先移除同 ID 旧项 | AC-3.3, AC-3.4, AC-3.7 |
| R-12 | 行为 | Scope 查找优先节点 | 按列表顺序选首个有效、结构后代且 whole-path 可聚焦节点（`focus_hub.cpp:2897-2950`） | 跨 Scope 或不可聚焦候选跳过 | AC-3.5~3.7 |
| R-13 | 行为 | 无历史 Scope 接受优先节点 | 写入候选到 Scope 的完整历史链并返回 true（`focus_hub.cpp:2883-2895,2985-2999`） | 候选请求仍由 Feat-02 准入 | AC-4.1 |
| R-14 | 边界 | 已有历史 Scope 接受优先节点 | 普通 Scope 返回 false；非嵌套 group 尝试 PREVIOUS并无条件返回 true（`focus_hub.cpp:3000-3006`） | Group 可能在无 PREVIOUS 时保留原历史 | AC-4.2, AC-4.3 |
| R-15 | 行为 | OnFocusScope 进入子树 | priority 请求先于组件 custom 和普通树序（`focus_hub.cpp:1727-1758,3009-3039`） | 普通 Scope 已有其他历史时 priority 可不接管 | AC-4.4, AC-4.5 |
| R-16 | 行为 | 同步按 ID 请求 | Flush 前调用 SetLastWeakFocusNodeToPreviousNode（`focus_hub.cpp:2488-2507,2952-2967`） | 仅 PREVIOUS 候选改写历史 | AC-4.6 |
| R-17 | 边界 | 判断 group/nesting/step-out | 非嵌套 group 在 FocusView 边界内生效；嵌套 group 不作为外层原子组（`focus_hub.cpp:2863-2880,3042-3055`） | 导航消费规则归 Feat-03 | AC-5.1~5.3 |
| R-18 | 恢复 | 节点移除或 FocusView 关闭 | 按 Scope/priority 角色清理注册（`focus_hub.cpp:2807-2821`、`focus_manager.cpp:182-203`） | Scope 有列表时保留空 Scope 条目 | AC-5.4 |
| R-19 | 边界 | FreeNode 修改域配置 | PostAfterAttachMainTreeTask 后执行普通逻辑（`focus_hub_multithread.cpp:59-90`） | attach 前 Manager 不可见新配置 | AC-5.5 |
| R-20 | 异常 | Native Style Modifier 参数非法 | 返回参数错误，并按属性入口执行默认复位（`style_modifier.cpp:1813-1885`） | C 枚举自 API 23 提供 | AC-5.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | R-1~R-5, AC-1.1~1.6 | 参数化 UT | NODE/SCOPE、空/重复/更换 ID、可选 bool 与动态/静态默认值 |
| VM-2 | R-6~R-8, AC-2.1~2.5 | FocusManager UT | Scope/priority 任意创建顺序、弱引用失效、空条目保留与删除 |
| VM-3 | R-9~R-12, AC-3.1~3.7 | 真实树 UT | 枚举值、前插/后插、重复设置、跨树、whole-path 和失效 WeakPtr |
| VM-4 | R-13~R-16, AC-4.1~4.6 | Scope 聚焦 UT | 无历史、普通历史、Group 历史、PREVIOUS 恢复及同步按 ID |
| VM-5 | R-17, AC-5.1~5.3 | Group 导航 UT | 自身/祖先/嵌套组、FocusView 截断和 arrowKeyStepOut |
| VM-6 | R-18~R-19, AC-5.4~5.5 | 生命周期/多线程 UT | RemoveSelf、FocusViewClose、Free→attach 前后注册表 |
| VM-7 | R-20, AC-5.6 | Native API UT | size=0/1/2、非法 bool、非法枚举、空 string 与 reset |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| N/A | N/A | N/A | N/A | N/A | 已有 API 23 焦点域能力补录，不新增 API | AC-1.1~5.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|---------|
| N/A | N/A | 无 API 变更或废弃 | 无需迁移 | AC-1.1~5.6 |

## 接口规格

### 接口定义

当前检出不含 canonical SDK 类型目录；以下签名依据仓内动态前端类型和实现核验，并以公共焦点属性规格为发布契约参考。

**focusScopeId**

| 属性 | 值 |
|------|-----|
| 函数签名 | `focusScopeId(id: string, isGroup?: boolean, arrowStepOut?: boolean): T` |
| 返回值 | `T` — 链式组件属性 |
| 开放范围 | Public，API 23 |
| 错误码 | ArkTS 无同步错误码；Native Style Modifier 返回参数错误 |
| 关联 AC | AC-1.1~1.6, AC-5.3, AC-5.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| id | string | 是 | 无 | 空字符串撤销 Scope；同 Pipeline 有效 Scope ID 唯一 |
| isGroup | boolean | 否 | false | true 标记焦点组 |
| arrowStepOut | boolean | 否 | true | false 仅阻止非 Tab 方向键跳出非嵌套组 |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | 注册、重复、撤销 Scope | Scenario Outline 1 | AC-1.1~1.5 |
| 2 | Group 方向键边界 | Scenario 4 | AC-5.1~5.3 |

**focusScopePriority**

| 属性 | 值 |
|------|-----|
| 函数签名 | `focusScopePriority(scopeId: string, priority?: FocusPriority): T` |
| 返回值 | `T` — 链式组件属性 |
| 开放范围 | Public，API 23 |
| 错误码 | ArkTS 无同步错误码；Native Style Modifier 返回参数错误 |
| 关联 AC | AC-3.1~4.6, AC-5.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| scopeId | string | 是 | 无 | 可在 Scope 注册前设置；空字符串移除优先配置 |
| priority | FocusPriority | 否 | AUTO(0) | 仅 AUTO=0、PRIOR=2000、PREVIOUS=3000 |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | PRIOR/PREVIOUS 排序和选择 | Scenario Outline 2 | AC-3.1~3.7 |
| 2 | 初次进入和历史恢复 | Scenario 3 | AC-4.1~4.6 |

## 兼容性声明

- **已有 API 行为变更:** 否；本次仅补录当前实现。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；域表和优先列表仅存在于 Pipeline FocusManager。
- **最低支持版本:** `focusScopeId`、`focusScopePriority` 及 `ArkUI_FocusPriority` 自 API 23 提供。
- **API 版本号策略:** 不新增 `@since`；核心域算法无 Target API 分支。
- **前端差异:** 动态前端首参非 string 的 `focusScopeId` 会转为空 ID；静态前端 optional 缺失也落空 ID。动态 `focusScopePriority` 仅在参数长度恰为 2 且第二项为 number 时读取 priority。
- **注册兼容风险:** Scope 从非空 ID A 改为新 ID B 前不会主动移除 A 映射；重复设置非 AUTO priority 可能累积重复 WeakPtr。
- **SDK 核验:** canonical `interface/sdk-js/api/` 未随当前检出提供，签名标记为未经 canonical d.ts/d.ets 验证。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Pipeline 级唯一注册 | 一个有效 focusScopeId 最多关联一个 Scope WeakPtr | AC-1.2~1.5, AC-2.1~2.3 |
| 角色互斥 | 同一 FocusHub 不能同时作为 Focus Scope 和 priority node | AC-3.1 |
| 弱引用所有权 | FocusManager 不延长 Scope 或优先节点生命周期 | AC-2.1~2.5, AC-3.5 |
| 结构后代过滤 | priority 候选必须是当前 Scope 后代且 whole-path 可聚焦 | AC-3.5 |
| 导航关注点分离 | Feat-04 固定优先选择，Feat-03 固定调用顺序，Feat-02提交事务 | AC-4.1~4.6, AC-5.3 |
| UI 主树注册 | FreeNode 通过 after-attach 任务更新 FocusManager | AC-5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|---------|------|
| 性能 | 域注册表平均 O(1) 查找；单次候选选择至多线性扫描对应 ID 的优先列表 | 源码审查 + 大列表回归 | `focus_manager.cpp:329-395`、`focus_hub.cpp:2924-2950` |
| 功耗 | 属性设置不触发周期任务；FreeNode 每次设置最多追加一个 after-attach 任务 | 源码审查 | `focus_hub_multithread.cpp:59-90` |
| 内存 | Scope 和候选均使用 WeakPtr；条目可在 Scope/列表均空时释放 | 生命周期 UT | VM-2, VM-6 |
| 安全 | 不新增权限、IPC 或敏感数据；ID 仅作为 Pipeline 内注册键 | 架构审查 | `focus_manager.h:87` |
| 可靠性 | 失效候选跳过，节点移除和 View 关闭执行注册清理 | UT | VM-2~VM-6 |
| 可测试性 | 20 条规则全部映射 VM；更换 ID、重复 priority 和 FreeNode 时序需定向补充 | UT | VM-1~VM-7 |
| 自动化维测 | DumpFocusScopeTree/JSON 输出 GroupId、ScopeId、priority 和 step-out | Dump 回归 | `focus_hub.cpp:418-453,3119-3212` |
| 定界定位 | 重复 Scope ID 输出 ACE_FOCUS warning；无候选返回 false | 日志检查 | `focus_hub.cpp:2791-2799,2924-2950` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|---------|------|
| 手机 | 无差异 | 使用相同 Pipeline 域表 | UT | 核心实现无设备类型分支 |
| 平板 | 多窗口各 Pipeline 独立 | 相同 ID 可在不同 FocusManager 中分别注册 | 多窗口测试 | 域表为 FocusManager 成员 |
| 折叠屏 | 无折叠状态分支 | 展开/折叠不改变注册和 priority 顺序 | 状态切换回归 | 核心实现无设备分支 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 焦点组会改变键盘可达边界，需与无障碍遍历共同回归 | AC-5.1~5.3 |
| 大字体 | 否 | 不读取字体或 Geometry | N/A |
| 深色模式 | 否 | 不涉及视觉绘制 | N/A |
| 多窗口/分屏 | 是 | 每个 Pipeline 独立维护 Scope ID 与优先列表 | AC-2.1~2.5 |
| 多用户 | 否 | 无持久化用户数据 | N/A |
| 版本升级 | 是 | API 23 枚举值和默认参数不得变化 | AC-1.6, AC-3.2~3.3, AC-5.6 |
| 生态兼容 | 是 | 重复 ID、重复 priority 和 PREVIOUS 优先顺序影响现有应用焦点恢复 | AC-1.3~1.4, AC-3.6~3.7 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 焦点域、分组与优先级
  作为 ArkUI 应用和组件开发者
  我想要按域组织焦点候选并控制首次与恢复目标
  以便复杂组件获得可预测的键盘焦点顺序

  Scenario Outline: 注册和撤销 Scope
    Given 当前节点 FocusType 为 <type>
    When 设置 focusScopeId 为 <id> isGroup 为 <group> arrowStepOut 为 <stepOut>
    Then isFocusScope 为 <isScope>
    And 注册结果为 <registered>

    Examples:
      | type | id | group | stepOut | isScope | registered |
      | SCOPE | scopeA | false | true | true | true |
      | NODE | scopeA | true | false | false | false |
      | SCOPE | 空字符串 | true | false | false | false |

  Scenario Outline: 优先级列表顺序
    Given Scope scopeA 已注册
    When依次设置候选 A 为 <priorityA> 候选 B 为 <priorityB>
    Then列表首个有效候选为 <first>

    Examples:
      | priorityA | priorityB | first |
      | PRIOR | PRIOR | A |
      | PRIOR | PREVIOUS | B |
      | PREVIOUS | PREVIOUS | B |

  Scenario: 普通 Scope 保留已有历史
    Given普通 Scope 已有历史节点 H
    And域内存在 PRIOR 候选 P
    When Scope 再次接受焦点
    Then优先接入返回 false
    And后续恢复流程仍可请求 H

  Scenario: 焦点组阻止方向键跳出
    Given当前节点位于非嵌套 group 且 arrowKeyStepOut 为 false
    When方向导航未找到组内候选
    Then事件被消费
    And焦点不跳出当前组

  Scenario: FreeNode 延迟注册
    Given节点处于 FreeNode 状态
    When设置 focusScopeId 或 focusScopePriority
    Then attach 前 FocusManager 注册表不变
    And挂主树执行 after-attach 任务后注册生效
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表满足可复现、可观测、边界值、关联 AC 和无冲突要求
- [x] 可疑实现仅作为风险记录，未写成修复方案

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FocusManager focusHubScopeMap focus scope priority list"
  - repo: "openharmony/arkui_ace_engine"
    query: "FocusHub SetFocusScopeId AcceptFocusOfPriorityChild PREVIOUS PRIOR"
  - repo: "openharmony/arkui_ace_engine"
    query: "focusScopeId focusScopePriority API 23 bridge native modifier"
```

**关键文档：** `frameworks/core/components_ng/event/focus_hub.cpp`、`frameworks/core/components_ng/manager/focus/focus_manager.cpp`、`interfaces/native/node/style_modifier.cpp`
