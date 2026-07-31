# 特性规格

> Func-04-09-01-Feat-03 焦点导航与遍历算法：固化键盘导航意图、事件路由、线性与空间寻焦、Tab/tabIndex、首尾遍历、自定义算法及跨 FocusView 边界行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 焦点导航与遍历算法 |
| 特性编号 | Func-04-09-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 当前 NG 实现；核心导航算法无 Target API 分支，按键点击路径存在 API 18 分支 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性定义 NG 焦点框架从非指针事件生成导航意图、沿当前焦点链路由事件、选择用户指定目标或默认算法、执行线性/空间/tabIndex 遍历，并在焦点组、TabStop、FocusView、focusWindowId 和 DynamicRender 边界处理导航的现有行为。

本特性只描述焦点域优先级和默认/恢复目标如何接入导航顺序，不重新定义其配置语义：焦点域、分组与优先级归 Feat-04；默认焦点及 FocusView 恢复归 Feat-05；焦点激活和视觉指示归 Feat-06；导航目标的最终请求与事务提交归 Feat-02。

## 本次变更范围（Delta）

> 历史规格补齐，当前实现即规格；发现的契约差异和测试缺口仅记录为风险，不在本次文档变更中修改产品代码。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 按键意图和事件处理顺序 | 补录方向键、Tab/Shift+Tab、Home/End、Enter/Space/Esc 的映射和 KeyProcessingMode 路由 |
| ADDED | 用户指定目标与 Tab 边界 | 补录 nextFocus 优先级、FocusView 首尾回退、focusWindowId/DynamicRender 运行时分支及 TabStop Enter/Esc |
| ADDED | 默认线性与首尾遍历 | 补录 LTR/RTL、无循环边界、Home/End、焦点组和 TryRequestFocus 接入顺序 |
| ADDED | tabIndex 正序遍历 | 补录候选收集、稳定升序、循环、首次 Shift+Tab 和祖先记忆传播 |
| ADDED | PROJECT_AREA 与自定义算法 | 补录投影准入、中心距离排序、Tab 两阶段寻焦和 Pattern 自定义回调 |
| ADDED | 导航风险基线 | 明确 nextFocus 契约差异、首次线性遍历不对称、全局/局部 RTL 差异和 Tab 状态复位风险 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/design.md` | Baselined |
| 焦点树状态模型 | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/Feat-01-focus-tree-node-state-model-spec.md` | Baselined |
| 请求与切换事务 | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/Feat-02-focus-request-clear-switch-transaction-spec.md` | Baselined |
| 公共焦点属性规格 | `specs/04-common-capability/03-common-attributes/03-basic-attributes/Feat-05-focus-attribute-spec.md:88-95,155-159` | 已核验，存在 nextFocus 失败语义差异 |
| 按键意图与事件路由 | `frameworks/core/components_ng/event/focus_event_handler.cpp:28-225`、`frameworks/core/components_ng/event/focus_hub.cpp:309-361` | 已核验 |
| 导航与遍历核心 | `frameworks/core/components_ng/event/focus_hub.cpp:1098-1524,2058-2108,2189-2327,2542-2770,3252-3328` | 已核验 |
| tabIndex 分发入口 | `frameworks/core/common/key_event_manager.cpp:536-550` | 已核验 |
| FocusView 步进状态 | `frameworks/core/components_ng/manager/focus/focus_manager.cpp:76-120` | 已核验 |
| 焦点导航 UT | `test/unittest/core/event/focus_core/`、`test/unittest/core/event/linear_focus_test.h` | 已核验 |

---

## 用户故事

### US-1: 将按键事件归一化并按配置路由

**作为** 焦点框架事件分发者，  
**我想要** 把键盘输入转换为确定的焦点意图并按 KeyProcessingMode 执行，  
**以便** 节点回调、祖先链和导航算法具有稳定顺序。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 输入不是 KEY、是 preIME 或 action 不是 DOWN THEN FocusIntension 为 NONE，不触发焦点导航 | 正常 |
| AC-1.2 | WHEN DPAD 方向键为 DOWN THEN 无论 pressedCodes 是否还含修饰键均映射为 UP/DOWN/LEFT/RIGHT；WHEN Tab/Home/End/Enter/Space 含非允许组合键 THEN 不按单键意图映射，只有 exactly Shift+Tab 映射为 SHIFT_TAB | 边界 |
| AC-1.3 | WHEN KeyIntention 为 SELECT、ESCAPE 或 HOME 且未被物理键映射覆盖 THEN 分别映射为 SELECT、ESC 或 HOME；其他 KeyIntention 返回 NONE | 正常 |
| AC-1.4 | WHEN HandleKeyEvent 执行普通 KEY 事件 THEN 内部回调和用户回调均被调用，再以两者逻辑或作为消费结果，不因内部回调返回 true 而跳过用户回调 | 正常 |
| AC-1.5 | WHEN KeyProcessingMode 为 FOCUS_NAVIGATION THEN 当前节点回调未消费后立即在当前焦点层执行 travel；WHEN 为 ANCESTOR_EVENT THEN 先完成当前到祖先的事件链，整链未消费后再递归执行 navigation | 正常 |
| AC-1.6 | WHEN FocusIntension 非 NONE 但 Pipeline 焦点未激活 THEN HandleFocusTravel 返回 false；WHEN TabJustTriggerOnKeyEvent=true THEN 滚动到历史索引并返回 false，不进入普通 travel | 边界 |

### US-2: 处理指定目标、Tab 边界和 TabStop 进入退出

**作为** 键盘导航用户，  
**我想要** 用户指定目标、Tab/Shift+Tab 和 Enter/Esc 按固定优先级工作，  
**以便** 能在普通树、FocusView 和 TabStop 容器间可预测地移动。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 当前意图在 nextStep_ 中存在且目标 ID/弱引用可解析并请求成功 THEN 直接消费事件，不执行默认 Tab、方向或首尾算法 | 正常 |
| AC-2.2 | WHEN nextStep_ 目标不存在、弱引用失效或 RequestFocusImmediately 返回 false THEN RequestUserNextFocus 返回 false，并继续执行该意图的默认算法 | 边界 |
| AC-2.3 | WHEN 普通 Tab/Shift+Tab 发生在焦点组内部 THEN RequestNextFocusOfKeyTab 直接返回 false；否则导航期间 Pipeline isFocusingByTab 置 true，普通收尾路径复位为 false | 正常 |
| AC-2.4 | WHEN 当前 FocusView 负责边界且内部 TAB/SHIFT_TAB 遍历失败、同时无 focusWindowId 和 DynamicRender 特殊分支 THEN TAB 从头、SHIFT_TAB 从尾调用 FocusToHeadOrTailChild | 边界 |
| AC-2.5 | WHEN focusWindowId 已设置且正向 TAB 到达边界 THEN 投递 50 ms UI 延迟任务处理窗口最后焦点并返回 false；WHEN DynamicRender 正向到边界或两类运行时反向到边界 THEN 立即尝试头/尾节点并返回 false | 边界 |
| AC-2.6 | WHEN 当前节点 tabStop=true 且 FocusType=SCOPE，SELECT/Enter 到达导航层 THEN 设置 isSwitchByEnter 和 FOCUS_TRAVEL，并调用 OnFocusScope(true) 进入子树；其他节点返回 false | 正常 |
| AC-2.7 | WHEN 当前节点是当前 FocusView 的焦点叶、不是 ViewRoot/FocusView 根，且边界内存在 tabStop 祖先 THEN ESC 使焦点退回最近 tabStop 祖先；否则返回 false | 正常 |

### US-3: 执行默认线性、首尾和焦点组遍历

**作为** 组件 Scope 和焦点组实现者，  
**我想要** 默认线性与首尾遍历遵循统一的候选接入顺序和边界，  
**以便** 不同组件复用同一导航机制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN RequestNextFocus 无法确认历史焦点仍为 current 或无法计算其相对矩形 THEN 返回 false，不调用默认或自定义候选算法 | 异常 |
| AC-3.2 | WHEN Pattern 未提供 getNextFocusNode 且 ScopeType 非 PROJECT_AREA THEN 使用 GoToNextFocusLinear；WHEN 轴向受限且方向键轴向不匹配 THEN 返回 IsArrowKeyStepOut 的结果 | 正常 |
| AC-3.3 | WHEN 线性遍历有有效历史游标 THEN 正向只搜索后继、反向只搜索前驱且到边界不循环；WHEN 无历史游标 THEN 游标先置首项，正向从第二项开始、反向立即边界失败 | 边界 |
| AC-3.4 | WHEN 线性 LEFT/RIGHT 判断前后方向 THEN 使用当前组件 LayoutDirection 覆盖后的 IsComponentDirectionRtl；TAB/SHIFT_TAB 的前后方向不被该局部方向翻转 | 正常 |
| AC-3.5 | WHEN Home/End 触发 THEN HOME 依次短路尝试 LEFT_END、UP_END，END 依次尝试 RIGHT_END、DOWN_END；仅非嵌套焦点组使用首尾后代规则 | 正常 |
| AC-3.6 | WHEN TryRequestFocus 处理 Tab 候选 THEN 依次尝试优先级子节点、指定首/尾子节点、矩形/历史接受和直接请求；WHEN 方向键进入非嵌套焦点组 THEN 将组作为原子节点直接请求 | 正常 |
| AC-3.7 | WHEN 方向键在焦点组中遍历失败且 arrowKeyStepOut=false THEN 返回 true 消费事件并阻止跳出；TAB/SHIFT_TAB 不受该封锁 | 边界 |

### US-4: 按 tabIndex 正序和循环遍历

**作为** 配置 tabIndex 的应用开发者，  
**我想要** 正 tabIndex 节点按稳定顺序形成独立遍历环，  
**以便** 键盘焦点顺序与配置一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 从主 View FocusHub 收集 tabIndex 节点 THEN 只加入 tabIndex>0 且 IsFocusableWholePath=true 的 NODE/SCOPE，并仅对 SCOPE 递归子焦点树 | 正常 |
| AC-4.2 | WHEN 候选列表非空 THEN 按 tabIndex 稳定升序排序；相同 tabIndex 保持焦点树收集顺序 | 正常 |
| AC-4.3 | WHEN 已记录且当前聚焦的 lastTabIndexNodeId 存在 THEN TAB 加一、Shift+Tab 减一并在两端取模循环 | 正常 |
| AC-4.4 | WHEN 没有有效 lastTabIndexNodeId THEN TAB 和首次 Shift+Tab 都选择排序后的索引 0，而不是由 Shift+Tab 从尾项开始 | 边界 |
| AC-4.5 | WHEN 目标 WeakPtr 失效、whole-path 不可聚焦或请求失败 THEN 本次 tabIndex 处理返回 false；WHEN 成功 THEN 把目标 FrameId 写入当前 Hub 及全部焦点祖先 | 恢复 |
| AC-4.6 | WHEN 目标为首次进入的 SCOPE 且存在 GROUP_DEFAULT 子节点 THEN 优先请求该子节点；GROUP_DEFAULT 的定义和选择规则由 Feat-05 承接 | 正常 |
| AC-4.7 | WHEN KeyEventManager 对 NG 主 View 分发 tabIndex 事件且 HandleFocusByTabIndex 返回 true THEN 事件被消费；否则继续后续普通按键/焦点导航分发 | 正常 |

### US-5: 执行空间、自定义和跨 FocusView 导航

**作为** Grid/List 等复杂组件及跨视图容器，  
**我想要** 通过 PROJECT_AREA 或 Pattern 自定义算法选择目标并保留 FocusView 边界语义，  
**以便** 几何布局和虚拟化组件能够接入统一焦点事务。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN PROJECT_AREA 枚举候选 THEN 排除空节点、自身、无 Geometry 和 IsFocusable=false 的节点，并只接纳移动方向上投影面积>0 的矩形 | 正常 |
| AC-5.2 | WHEN 方向键存在多个 PROJECT_AREA 候选 THEN 按变换后矩形中心欧氏距离平方取最小值；投影面积只用于准入，不参与排序；等距时保持先遍历候选 | 正常 |
| AC-5.3 | WHEN PROJECT_AREA 处理 TAB/SHIFT_TAB THEN 先按应用全局 RTL 映射为水平步长寻焦，失败后再执行纵向平移一个当前节点高度的换行模型，并按带符号距离最大值选择 | 边界 |
| AC-5.4 | WHEN Pattern 提供 getNextFocusNode THEN 每次移动前重新读取 ScopeFocusAlgorithm；只有回调返回 true 且输出 WeakPtr 可升级时才进入 TryRequestFocus，否则返回 IsArrowKeyStepOut | 正常 |
| AC-5.5 | WHEN 自定义算法返回可升级的 FocusHub THEN 当前实现不校验其一定属于当前 Scope 后代，直接交给 TryRequestFocus；目标不可聚焦时按请求失败处理 | 边界 |
| AC-5.6 | WHEN 首尾遍历遇到 TabStop、非嵌套焦点组、ScrollablePattern 或节点自定义 hook THEN 依次遵循原子停留、滚动到头尾并 FlushUITasks、hook 优先和 CHILD/AUTO 递归回退规则，不简化为直接取列表首尾项 | 正常 |
| AC-5.7 | WHEN 步进导航进入合法且不同的 FocusView THEN 调用 FocusViewShow(true) 更新视图栈，并因 isTriggerByStep=true 不写入“前一 FocusView”的恢复历史 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1, R-2 | TASK-SKELETON-F3-1 | UT | `focus_event_handler.cpp:28-81` |
| AC-1.4~1.6 | R-3~R-5 | TASK-SKELETON-F3-1 | UT + 时序审查 | `focus_event_handler.cpp:107-225`、`focus_hub.cpp:309-361` |
| AC-2.1~2.2 | R-6 | TASK-SKELETON-F3-2 | UT + 契约对照 | `focus_hub.cpp:1098-1148`、`Feat-05-focus-attribute-spec.md:93-95` |
| AC-2.3~2.5 | R-7, R-8 | TASK-SKELETON-F3-2 | 参数化 UT | `focus_hub.cpp:1150-1209,1251-1260` |
| AC-2.6~2.7 | R-9 | TASK-SKELETON-F3-2 | UT | `focus_hub.cpp:1212-1248` |
| AC-3.1~3.4 | R-10~R-12 | TASK-SKELETON-F3-3 | 参数化 UT | `focus_hub.cpp:1282-1453,1488-1524,3099-3116` |
| AC-3.5~3.7 | R-13~R-15 | TASK-SKELETON-F3-3 | UT | `focus_hub.cpp:1121-1144,1297-1407,1456-1475` |
| AC-4.1~4.7 | R-16~R-18 | TASK-SKELETON-F3-4 | KeyEventManager/Core UT | `key_event_manager.cpp:536-550`、`focus_hub.cpp:2273-2327,2542-2602` |
| AC-5.1~5.3 | R-19, R-20 | TASK-SKELETON-F3-5 | 几何参数化 UT | `focus_hub.cpp:2623-2729` |
| AC-5.4~5.5 | R-21 | TASK-SKELETON-F3-5 | 自定义算法 UT | `focus_hub.cpp:1282-1295,1343-1359,1517-1524` |
| AC-5.6~5.7 | R-22, R-23 | TASK-SKELETON-F3-5 | 集成 UT | `focus_hub.cpp:2732-2770,3252-3328`、`focus_manager.cpp:76-120` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 非指针事件进入 FocusEvent | 仅 KEY+DOWN+非 preIME 继续物理键映射（`focus_event_handler.cpp:28-36`） | 其他输入统一为 NONE | AC-1.1 |
| R-2 | 边界 | 解析组合键 | 方向键忽略额外 pressedCodes；普通键要求单键；exactly Shift+Tab 为唯一例外（`focus_event_handler.cpp:37-67`） | ESC 可由 KeyIntention 补充映射 | AC-1.2, AC-1.3 |
| R-3 | 行为 | 普通 KEY 到达当前 NODE | 先内部回调，再用户回调，两者都执行后合并结果（`focus_event_handler.cpp:183-205`） | redispatch 直接返回 false；preIME 走独立入口 | AC-1.4 |
| R-4 | 行为 | 根据 KeyProcessingMode 分发 | FOCUS_NAVIGATION 在当前层未消费后 travel；ANCESTOR_EVENT 在祖先链未消费后 navigation（`focus_event_handler.cpp:147-180`、`focus_hub.cpp:309-336`） | 模式改变时序，不关闭导航 | AC-1.5 |
| R-5 | 边界 | HandleFocusTravel 执行 | focus inactive 或 TabJustTriggerOnKeyEvent 时返回 false；正常路径临时写入 FocusManager current event（`focus_hub.cpp:339-361`） | TabJustTrigger 仍允许前序按键回调执行 | AC-1.6 |
| R-6 | 边界 | nextStep_ 存在当前意图 | 请求成功则最高优先级消费；解析/请求失败则继续默认算法（`focus_hub.cpp:1098-1148`） | 与公共属性规格“目标不存在则停留”存在文档差异 | AC-2.1, AC-2.2 |
| R-7 | 行为 | Tab/Shift+Tab 进入普通导航 | 焦点组内拒绝；组外置 isFocusingByTab 并执行 RequestNextFocus（`focus_hub.cpp:1150-1209`） | 普通收尾复位；特殊提前返回分支存在风险 | AC-2.3 |
| R-8 | 边界 | FocusView 内部 Tab 到达边界 | 普通容器头尾回退；focusWindowId 正向延迟 50 ms；DynamicRender/反向特殊分支立即尝试后返回 false（`focus_hub.cpp:1159-1209`） | Shift+Tab 无对应 50 ms 延迟 | AC-2.4, AC-2.5 |
| R-9 | 行为 | SELECT 或 ESC 进入导航 | SELECT 仅进入 tabStop SCOPE；ESC 仅从当前 FocusView 叶退到边界内最近 tabStop 祖先（`focus_hub.cpp:1212-1248`） | tabStop 属性声明归公共属性规格 | AC-2.6, AC-2.7 |
| R-10 | 异常 | RequestNextFocus 计算当前位置 | 历史焦点无效、非 current 或矩形计算失败时返回 false（`focus_hub.cpp:1282-1295,1488-1514`） | 不调用候选回调 | AC-3.1 |
| R-11 | 行为 | 默认非空间算法 | 轴向不匹配先判断 step-out，其他输入走线性遍历（`focus_hub.cpp:1331-1340`） | PROJECT_AREA 和自定义算法分流处理 | AC-3.2 |
| R-12 | 边界 | GoToNextFocusLinear 枚举候选 | 使用 lastWeakFocusNode 游标且不循环；无历史时首轮正向跳过首项、反向失败（`focus_hub.cpp:1409-1453`） | LEFT/RIGHT 使用组件局部 RTL | AC-3.3, AC-3.4 |
| R-13 | 行为 | Home/End 导航 | 按横向 END 步长优先、纵向 END 步长后备，非嵌套焦点组取首尾后代（`focus_hub.cpp:1121-1144,1297-1305`） | 非焦点组或嵌套组返回 false | AC-3.5 |
| R-14 | 行为 | TryRequestFocus 接收候选 | Tab priority child→specified child→rect/history→direct；方向键进入非嵌套组时直接请求组（`focus_hub.cpp:1456-1475`） | priority 定义归 Feat-04 | AC-3.6 |
| R-15 | 边界 | 焦点组方向键失败 | arrowKeyStepOut=false 时返回 true 消费并阻止出组（`focus_hub.cpp:1362-1371`） | Tab 不封锁 | AC-3.7 |
| R-16 | 行为 | 收集和排序 tabIndex | 仅 tabIndex>0 且 whole-path 可聚焦节点进入稳定升序列表（`focus_hub.cpp:2273-2282,2573-2581`） | 相同值保留收集顺序 | AC-4.1, AC-4.2 |
| R-17 | 边界 | 计算 tabIndex 目标 | 有记忆时按方向取模循环；无记忆时固定索引 0（`focus_hub.cpp:2542-2602`） | 首次 Shift+Tab 也从索引 0 开始 | AC-4.3, AC-4.4 |
| R-18 | 恢复 | 请求 tabIndex 目标 | 失效/不可聚焦/请求失败返回 false；成功向祖先传播 FrameId；首次 Scope 可接入 GROUP_DEFAULT（`focus_hub.cpp:2285-2327`） | NG 生产入口由 KeyEventManager 主 View 分发 | AC-4.5~4.7 |
| R-19 | 行为 | PROJECT_AREA 方向候选选择 | 投影面积>0 才准入，方向键按中心距离平方最小选择（`focus_hub.cpp:2623-2722`） | 投影面积不参与排序；等距先遍历者胜出 | AC-5.1, AC-5.2 |
| R-20 | 边界 | PROJECT_AREA Tab/Shift+Tab | 先用全局 RTL 水平映射，再用纵向平移与带符号最大距离执行换行（`focus_hub.cpp:1306-1318,2676-2722`） | 与线性算法的组件局部 RTL 来源不同 | AC-5.3 |
| R-21 | 边界 | Pattern 提供自定义 ScopeFocusAlgorithm | 每次移动前刷新；false/空 WeakPtr 按 step-out；有效目标直接 TryRequestFocus（`focus_hub.cpp:1282-1295,1343-1359,1517-1524`） | 当前不校验目标与 Scope 的结构归属 | AC-5.4, AC-5.5 |
| R-22 | 行为 | 获取首尾后代 | 先检查 whole-path/tab、loop、group、TabStop；Scrollable 先滚动并 Flush，再按 hook 与 CHILD/AUTO 规则递归（`focus_hub.cpp:3252-3328`） | Home/End 可穿透普通非嵌套组规则 | AC-5.6 |
| R-23 | 行为 | 步进进入新 FocusView | FocusViewShow(true) 更新栈，isTriggerByStep 抑制恢复历史写入（`focus_hub.cpp:2732-2770`、`focus_manager.cpp:76-120`） | 恢复链构造归 Feat-05 | AC-5.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | R-1~R-3, AC-1.1~1.4 | 参数化 UT | event type/action/preIME、方向键修饰键、单键限制及内部/用户回调均执行 |
| VM-2 | R-4~R-5, AC-1.5~1.6 | 事件链 UT | 两种 KeyProcessingMode、focus inactive、TabJustTrigger 与 current event 生命周期 |
| VM-3 | R-6, AC-2.1~2.2 | 契约对照 UT | nextFocus 成功短路、目标缺失/请求失败继续默认算法，以及公共规格差异 |
| VM-4 | R-7~R-8, AC-2.3~2.5 | Container/Pipeline UT | 普通 FocusView、focusWindowId 50 ms、DynamicRender、正反向返回值与 flag 复位 |
| VM-5 | R-9, AC-2.6~2.7 | TabStop 树 UT | Enter 进入 Scope、ESC 最近祖先、ViewRoot 与非叶边界 |
| VM-6 | R-10~R-12, AC-3.1~3.4 | 真实树参数化 UT | 矩形失败、线性前后向、首轮不对称、不循环及组件 LTR/RTL |
| VM-7 | R-13~R-15, AC-3.5~3.7 | 焦点组 UT | Home/End 短路、Priority→Specify→direct、非嵌套组与 arrowKeyStepOut |
| VM-8 | R-16~R-18, AC-4.1~4.7 | KeyEventManager/Core UT | 正值收集、相同值稳定顺序、首次 Shift+Tab、循环、WeakPtr 失效和祖先记忆 |
| VM-9 | R-19, AC-5.1~5.2 | 几何参数化 UT | 四方向、零面积、部分重叠、transform、等距及“投影大但中心远” |
| VM-10 | R-20, AC-5.3 | LTR/RTL 布局 UT | PROJECT_AREA 同行优先、换行候选顺序、全局 RTL 与局部方向不一致 |
| VM-11 | R-21, AC-5.4~5.5 | List/Grid 自定义算法 UT | 回调刷新、false、空/失效 WeakPtr、不可聚焦及跨 Scope 候选 |
| VM-12 | R-22~R-23, AC-5.6~5.7 | Scrollable/FocusView 集成 UT | 滚动后物化与 Flush、hook、TabStop/group、View 栈和恢复历史抑制 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| N/A | N/A | N/A | N/A | N/A | 已有焦点导航实现补录，不新增 ArkTS、System API、InnerAPI 或 C API | AC-1.1~5.7 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|---------|
| N/A | N/A | 无 API 变更或废弃 | 无需迁移 | AC-1.1~5.7 |

## 接口规格

### 接口定义

本特性不新增开放接口。以下内部入口用于限定当前导航语义，不构成 SDK 稳定性承诺。

**FocusHub::RequestNextFocusByKey**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool FocusHub::RequestNextFocusByKey(const FocusEvent& event)` |
| 返回值 | `bool` — 当前事件是否被用户指定目标、默认算法或焦点组边界消费 |
| 开放范围 | 框架内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1~3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| event | const FocusEvent& | 是 | 无 | intension 由 FocusEvent 归一化；NONE 或未支持意图返回 false |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | nextFocus 目标成功或失败 | Scenario 2 | AC-2.1, AC-2.2 |
| 2 | 线性、Home/End 或焦点组导航 | Scenario 3, Scenario 4 | AC-3.2~3.7 |

**FocusHub::HandleFocusByTabIndex**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool FocusHub::HandleFocusByTabIndex(const KeyEvent& event)` |
| 返回值 | `bool` — tabIndex 列表是否成功请求目标并消费事件 |
| 开放范围 | 框架内部，由 `KeyEventManager::DispatchTabIndexEventNG` 调用 |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| event | const KeyEvent& | 是 | 无 | 仅 DOWN 的 Tab，或 directionalKeyFocus 开启时的方向键；TabJustTriggerOnKeyEvent 时返回 false |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | 首次或已有记忆的正反向 tabIndex 遍历 | Scenario Outline 5 | AC-4.1~4.7 |

**ScopeFocusAlgorithm::getNextFocusNode**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool getNextFocusNode(FocusStep, WeakPtr<FocusHub>, WeakPtr<FocusHub>&)` |
| 返回值 | `bool` — 是否给出候选；仍需输出 WeakPtr 可升级且 TryRequestFocus 成功 |
| 开放范围 | 框架内部 Pattern 扩展点 |
| 错误码 | N/A |
| 关联 AC | AC-5.4, AC-5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| step | FocusStep | 是 | 无 | 可为方向、Tab/Shift+Tab 或首尾步长，由组件 Pattern 决定支持范围 |
| current | WeakPtr<FocusHub> | 是 | 无 | 对应 Scope 的 lastWeakFocusNode，调用前必须可升级 |
| next | WeakPtr<FocusHub>& | 是 | 空 | success=true 时仍必须可升级；当前实现不强制属于当前 Scope |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | 自定义算法成功、失败或输出失效候选 | Scenario 7 | AC-5.4, AC-5.5 |

## 兼容性声明

- **已有 API 行为变更:** 否；本次仅补录当前实现，但识别到公共焦点属性规格与内部实现对 nextFocus 失败后的行为描述不一致。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；导航游标、矩形、tabIndex 记忆和 FocusView 状态均为运行时数据。
- **最低支持版本:** 与 NG 焦点框架现有支持范围一致。
- **API 版本号策略:** 核心导航算法未发现 Target API 门控；按键触发点击在 API 18 存在焦点激活门槛分支，该点击行为归 Feat-06 邻接约束。
- **nextFocus 兼容风险:** `RequestUserNextFocus` 目标不存在或请求失败时返回 false，随后继续默认算法；不得据此实现承诺“始终停留当前节点”。
- **运行时容器差异:** focusWindowId、DynamicRender、全局 RTL 和组件局部 LayoutDirection 会改变边界或方向选择，但不改变公开 API 签名。
- **SDK 声明核验:** 当前 ace_engine 检出不含 `interface/sdk-js/api/` canonical SDK 类型目录；本特性无新增 API，不扩张仓内实现为新的公开契约。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 单一意图模型 | 所有普通键盘导航必须先归一化为 FocusIntension，再转换为 FocusStep | AC-1.1~1.3 |
| 事件与导航分层 | 节点/用户回调消费与祖先导航按 KeyProcessingMode 分层，不允许在组件中复制第二套分发链 | AC-1.4~1.6 |
| 事务复用 | 所有候选最终必须通过 RequestFocusImmediatelyInner 进入 Feat-02 的准入与 FocusGuard 事务 | AC-2.1, AC-3.6, AC-4.5, AC-5.5 |
| 状态模型复用 | 候选收集使用 Feat-01 的焦点树、whole-path 和历史弱引用，不建立独立所有权 | AC-3.1~3.4, AC-4.1 |
| 关注点分离 | priority/group 属性定义归 Feat-04，GROUP_DEFAULT/FocusView 恢复归 Feat-05，视觉激活归 Feat-06 | AC-3.6, AC-4.6, AC-5.7 |
| UI 线程与布局快照 | 几何、滚动 Flush、延迟窗口任务和 FocusView 栈更新必须在对应 Pipeline UI 上下文执行 | AC-2.5, AC-5.1~5.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|---------|------|
| 性能 | 单次线性、PROJECT_AREA 或 tabIndex 导航最多遍历当前 Scope 可达候选一次；不建立无界历史队列 | 源码审查 + 大树性能回归 | `focus_hub.cpp:1409-1453,2273-2282,2662-2729` |
| 功耗 | 普通导航不新增周期任务；仅 focusWindowId 正向 Tab 边界投递一次 50 ms UI 延迟任务 | 源码审查 | `focus_hub.cpp:1173-1187` |
| 内存 | 候选列表为调用期容器，历史与自定义目标使用 WeakPtr；不延长节点生命周期 | 源码审查 + 弱引用 UT | `focus_hub.cpp:1348-1355,2273-2327` |
| 安全 | 不新增权限、IPC 或敏感数据；用户 nextFocus ID 仅在允许的 Inspector 树中解析 | 架构审查 | `focus_hub.cpp:1098-1118` |
| 可靠性 | 所有空宿主、空 Geometry、失效 WeakPtr 和不可聚焦目标均有 false/回退结果 | 参数化 UT | VM-3, VM-6, VM-8~VM-11 |
| 可测试性 | 23 条规则全部映射 VM；容器边界、首轮不对称、RTL 和等距 tie 需要定向用例 | UT | VM-1~VM-12 |
| 自动化维测 | 保留意图、FocusStep、候选节点 ID、失败原因和返回值的 ACE_FOCUS 日志 | 日志回归 | `focus_hub.cpp:1287-1358,2297-2317,2672-2728` |
| 定界定位 | nextFocus、默认线性、PROJECT_AREA、自定义算法和 FocusView 回退可按调用阶段区分 | 日志 + 事件链审查 | VM-3, VM-6, VM-9~VM-12 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|---------|------|
| 手机 | 无设备类型差异 | 使用相同意图、线性、空间和 tabIndex 算法 | UT | 核心实现无设备类型分支 |
| 平板 | 多窗口场景可能设置 focusWindowId | 正向 Tab 边界按 50 ms 延迟任务转移，Shift+Tab 立即处理 | 多窗口集成测试 | `focus_hub.cpp:1173-1204` |
| 折叠屏 | 无折叠状态专用分支 | 展开/折叠后的实时 Geometry 参与 PROJECT_AREA，算法本身不缓存布局 | 布局变化回归 | `focus_hub.cpp:2665-2697` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 键盘焦点导航不替代无障碍焦点；Tab/方向顺序应与可访问性回归共同验证 | VM-6~VM-10 |
| 大字体 | 是 | 大字体改变 Geometry 时 PROJECT_AREA 以新矩形重新计算候选 | AC-5.1~5.3 |
| 深色模式 | 否 | 焦点框视觉由 Feat-06 定义 | N/A |
| 多窗口/分屏 | 是 | focusWindowId 与 FocusView 边界改变 Tab 转移时序 | AC-2.4, AC-2.5 |
| 多用户 | 否 | 无持久化和用户隔离数据 | N/A |
| 版本升级 | 是 | API 18 仅影响邻接点击路径；核心导航无 Target API 分支 | AC-1.6 |
| 生态兼容 | 是 | nextFocus 失败回退、首次 Shift+Tab 和 RTL 来源差异可能影响现有应用顺序 | AC-2.2, AC-3.3, AC-4.4, AC-5.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 焦点导航与遍历算法
  作为键盘与遥控器用户
  我想要焦点按确定的事件和候选规则移动
  以便在普通组件、焦点组和复杂布局中持续操作

  Scenario Outline: 按键意图归一化
    Given 输入事件类型为 <type> 动作为 <action> preIME 为 <preIme>
    When 按键为 <key> 且 pressedCodes 为 <codes>
    Then FocusIntension 为 <intension>

    Examples:
      | type | action | preIme | key | codes | intension |
      | KEY | DOWN | false | DPAD_LEFT | CTRL+DPAD_LEFT | LEFT |
      | KEY | DOWN | false | TAB | SHIFT+TAB | SHIFT_TAB |
      | KEY | UP | false | TAB | TAB | NONE |
      | KEY | DOWN | true | TAB | TAB | NONE |

  Scenario: 用户指定目标失败后回退默认算法
    Given 当前节点为意图 DOWN 配置了不存在的 nextFocus ID
    When 用户按下 DPAD_DOWN
    Then RequestUserNextFocus 返回 false
    And 系统继续执行 DOWN 的默认导航

  Scenario: 线性遍历到边界
    Given 当前 Scope 的历史焦点位于最后一个可聚焦子节点
    When 用户执行正向线性导航
    Then GoToNextFocusLinear 返回 false
    And 默认线性算法不循环到第一个节点

  Scenario: 焦点组阻止方向键跳出
    Given 当前 Scope 是焦点组且 arrowKeyStepOut 为 false
    When 方向键候选搜索失败
    Then 导航返回 true 消费事件
    And 焦点不跳出当前组

  Scenario Outline: tabIndex 循环与首次反向
    Given tabIndex 候选按值排序为 A B C
    And 当前记忆状态为 <memory>
    When 输入 <key>
    Then 请求目标为 <target>

    Examples:
      | memory | key | target |
      | 无 | TAB | A |
      | 无 | SHIFT_TAB | A |
      | A | SHIFT_TAB | C |
      | C | TAB | A |

  Scenario: PROJECT_AREA 方向键选择
    Given 两个候选均在移动方向上具有正投影面积
    And 候选 A 的中心距离小于候选 B
    When 执行方向键空间寻焦
    Then 选择候选 A
    And 不以投影面积大小排序

  Scenario: 自定义算法返回失效目标
    Given Pattern 的 getNextFocusNode 返回 true
    And 输出 WeakPtr 无法升级
    When 执行 RequestNextFocus
    Then 不调用无效目标
    And 返回 IsArrowKeyStepOut 的结果

  Scenario: focusWindowId 正向 Tab 到边界
    Given 当前 FocusView 内部正向 Tab 遍历失败
    And Pipeline 已设置 focusWindowId
    When 处理 Tab 边界
    Then 投递 50 ms UI 延迟任务
    And 当前同步调用返回 false
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（“快速”“稳定”“尽可能”等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）
- [x] 所有源码路径和行号来自当前检出；未把未来改进写成现行行为
- [x] 已明确 Feat-04/05/06 边界及 nextFocus 契约差异

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FocusEvent intention key processing mode and focus travel routing"
  - repo: "openharmony/arkui_ace_engine"
    query: "FocusHub linear tabIndex project area custom focus algorithm"
  - repo: "openharmony/arkui_ace_engine"
    query: "FocusView focusWindowId DynamicRender Tab boundary navigation"
```

**关键文档：** `frameworks/core/components_ng/event/focus_event_handler.cpp`、`frameworks/core/components_ng/event/focus_hub.cpp`、`frameworks/core/common/key_event_manager.cpp`、`frameworks/core/components_ng/manager/focus/focus_manager.cpp`
