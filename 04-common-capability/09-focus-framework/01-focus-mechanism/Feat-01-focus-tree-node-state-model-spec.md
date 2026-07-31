# 特性规格

> Func-04-09-01-Feat-01 焦点树与节点状态模型：固化 NG 焦点节点的类型、宿主、树关系、可聚焦性、生命周期输入与 FreeNode 最终一致性行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 焦点树与节点状态模型 |
| 特性编号 | Func-04-09-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 当前 NG 实现；本特性范围内无 Target API 分支 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性定义 NG 焦点框架的基础状态模型，包括 `FocusType` / `FocusPattern` / `FocusState` / `FocusHub` 的初始化与宿主关系、由 UI 树投影得到的焦点树、NODE 与 SCOPE 的可聚焦判定、显式与隐式 focusable 的优先级、enabled/visible 等外部状态输入，以及 FreeNode 场景下属性状态与焦点清理副作用的最终一致性。

本特性不重复定义 `focusable`、`defaultFocus`、`focusBox` 等公共 ArkTS 属性契约；公共属性规格由 `Func-04-03-03-Feat-05` 承接。本特性也不展开焦点请求与切换事务、导航算法、焦点域优先级、FocusView 恢复和焦点视觉绘制。

## 本次变更范围（Delta）

> 历史规格补齐，当前实现即规格；发现的边界和测试缺口仅记录为风险，不改变产品代码行为。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 焦点节点类型与初始化模型 | 补录 DISABLE/NODE/SCOPE、FocusPattern 注入及 FocusHub 幂等创建行为 |
| ADDED | 焦点树投影模型 | 补录焦点父节点、Screen 边界、主树过滤、根节点和历史焦点叶节点行为 |
| ADDED | 可聚焦性判定模型 | 补录 NODE/SCOPE、SELF/AUTO/CHILD、祖先路径及 parentFocusable 规则 |
| ADDED | 状态优先级与生命周期输入 | 补录显式/隐式 focusable、enabled、visible 及双值 enabled 模型 |
| ADDED | FreeNode 最终一致性 | 补录状态立即生效、清焦副作用延后到挂主树执行的运行时差异 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/design.md` | Baselined |
| 公共焦点属性规格 | `specs/04-common-capability/03-common-attributes/03-basic-attributes/Feat-05-focus-attribute-spec.md` | Baselined |
| 类型与状态模型 | `frameworks/core/components_ng/event/focus_type.h:23-60`、`frameworks/core/components_ng/event/focus_state.h:31-96` | 已核验 |
| 焦点核心实现 | `frameworks/core/components_ng/event/focus_hub.h:157-299,385-465,845-885`、`frameworks/core/components_ng/event/focus_hub.cpp:60-113,217-306,736-1028,2234-2270` | 已核验 |
| 宿主与树关系 | `frameworks/core/components_ng/base/frame_node.cpp:1051-1054,4637-4684`、`frameworks/core/components_ng/base/ui_node.cpp:929-1017`、`frameworks/core/components_ng/event/event_hub.cpp:766-785,1073-1098` | 已核验 |
| FreeNode 多线程实现 | `frameworks/core/components_ng/event/focus_hub_multithread.cpp:22-57`、`frameworks/core/components_ng/base/ui_node_multi_thread.cpp:24-51,105-130` | 已核验 |
| 焦点 UT | `test/unittest/core/event/focus_core/focus_hub_test_ng.cpp`、`focus_hub_test_ng_branch_coverage_three.cpp`、`hierarchical_switching_test.cpp` | 已核验 |

---

## 用户故事

### US-1: 建立焦点节点状态模型

**作为** ArkUI 框架开发者，  
**我想要** 每个可参与焦点的 FrameNode 拥有类型明确、宿主可追溯且创建幂等的 FocusHub，  
**以便** 上层组件以统一模型参与焦点树和可聚焦性判定。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN Pattern 的 FocusType 为 NODE 或 SCOPE 且 FrameNode 完成 Pattern 初始化 THEN FrameNode 创建一个由 FocusPattern 初始化的 FocusHub | 正常 |
| AC-1.2 | WHEN Pattern 的 FocusType 为 DISABLE 且未显式请求 FocusHub THEN FrameNode 初始化阶段不创建 FocusHub；WHEN 后续调用 GetOrCreateFocusHub THEN 创建并缓存唯一实例 | 边界 |
| AC-1.3 | WHEN 同一 FrameNode 多次调用任一 GetOrCreateFocusHub 重载 THEN 返回首次缓存的 FocusHub，后续参数不重新配置已有实例 | 正常 |
| AC-1.4 | WHEN FocusState 持有有效 FrameNode 弱引用 THEN GetFrameNode 返回该 FrameNode；WHEN FrameNode 弱引用失效但 EventHub 宿主有效 THEN 从 EventHub 回取 FrameNode | 恢复 |
| AC-1.5 | WHEN FrameNode 与 EventHub 宿主均失效 THEN GetFrameNode 返回空、GetFrameName 返回 `NULL`、GetFrameId 返回 `-1`，且 IsEnabled 按默认 true 处理 | 边界 |

### US-2: 查询焦点树关系和历史焦点叶节点

**作为** 焦点框架调用方，  
**我想要** 从 UI 节点树得到稳定的焦点父子关系、根节点和历史焦点叶节点，  
**以便** 后续焦点事务与导航基于同一树语义执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 从节点向上查找焦点父节点且途中节点为 DISABLE 或非 FrameNode THEN 跳过该节点继续向上；WHEN 首个焦点节点为 SCOPE THEN 返回该 SCOPE | 正常 |
| AC-2.2 | WHEN 从节点向上查找焦点父节点且首个焦点节点为 NODE THEN 父链在该 NODE 处截断并返回空 | 边界 |
| AC-2.3 | WHEN 使用 boundary-aware 父链且向上遇到 Screen 节点 THEN 停止查找；WHEN 获取根 FocusHub THEN 使用非 boundary 父链持续上溯 | 边界 |
| AC-2.4 | WHEN 遍历子 FocusHub THEN 跳过未挂主树的子树；对 NODE/SCOPE 执行操作并停止向其内部递归，对 DISABLE/非 FrameNode 继续递归 | 正常 |
| AC-2.5 | WHEN GetFocusLeaf 沿 lastWeakFocusNode 链下钻 THEN 在当前候选不可聚焦、弱引用失效或 FocusDependence 为 SELF 时停止，并返回最后一个有效候选 | 恢复 |

### US-3: 判定节点和焦点路径是否可聚焦

**作为** 焦点请求、导航和恢复逻辑，  
**我想要** 使用统一且可组合的可聚焦性判定，  
**以便** 不可见、禁用或被祖先约束的节点不会进入后续焦点流程。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN FocusType 为 DISABLE THEN IsFocusable 和 IsChildFocusable 均返回 false | 正常 |
| AC-3.2 | WHEN FocusType 为 NODE THEN 仅当 focusable、parentFocusable、自身 enabled、自身可见且所有 FrameNode 祖先可见时 IsFocusableNode 返回 true | 正常 |
| AC-3.3 | WHEN 调用 IsChildFocusableNode THEN 仅校验本节点的 focusable、parentFocusable、enabled 和可见性，不重复扫描祖先可见性 | 边界 |
| AC-3.4 | WHEN FocusType 为 SCOPE 且基础 NODE 门槛通过 THEN SELF 或 AUTO 返回 true；CHILD 仅在至少一个投影子 FocusHub 可聚焦时返回 true | 正常 |
| AC-3.5 | WHEN 调用 IsFocusableWholePath THEN 对 Screen 边界内每个焦点祖先执行 IsFocusableNode 门槛校验，并对目标节点执行完整 NODE/SCOPE 判定 | 正常 |
| AC-3.6 | WHEN SCOPE 祖先为 CHILD 且其自身 NODE 门槛通过但不存在其他可聚焦子节点 THEN 该祖先不会单独阻断其目标后代的 whole-path 判定 | 边界 |

### US-4: 同步 focusable、enabled 和 visible 生命周期状态

**作为** 组件和框架内部状态管理逻辑，  
**我想要** 明确显式/隐式 focusable 优先级以及 enabled/visible 的真实状态源，  
**以便** 动态状态变化不会产生互相覆盖或缓存不一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 首次显式调用 SetFocusable THEN 标记显式设置；WHEN 后续以 isExplicit=false 写入 THEN 忽略该隐式写入 | 正常 |
| AC-4.2 | WHEN SCOPE 被隐式设置为可聚焦且当前 FocusDependence 为 CHILD THEN 将 FocusDependence 调整为 AUTO | 正常 |
| AC-4.3 | WHEN 查询 enabled 或 visible THEN FocusHub 实时读取 EventHub 和 FrameNode/祖先状态，不从 SetEnabled 或 SetShow 缓存状态 | 正常 |
| AC-4.4 | WHEN FocusType 切换为 DISABLE、focusable 切换为 false、收到 enabled=false 或 show=false 通知 THEN 触发 RemoveSelf；具体焦点清理与重分配事务由 Feat-02 定义 | 恢复 |
| AC-4.5 | WHEN EventHub::SetEnabled 被调用 THEN 同时更新生效值与开发者值；WHEN SetEnabledInternal 被调用 THEN 仅更新生效值；WHEN RestoreEnabled 被调用 THEN 恢复开发者值 | 正常 |
| AC-4.6 | WHEN SetParentFocusable(false) 被调用 THEN 本地 parentFocusable 门槛立即为 false；关闭后代 FocusView 的行为由 Feat-05 定义 | 正常 |

### US-5: 处理 FreeNode 的延迟焦点副作用

**作为** 多线程节点构建和挂树流程，  
**我想要** 将不安全的焦点树清理延后到节点挂入主树后执行，  
**以便** FreeNode 状态变化不在错误线程直接操作主焦点树。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN FreeNode 调用 SetFocusable(false) THEN focusable 状态立即变为 false，RemoveSelf 通过 FREE_NODE_CHECK 转为挂树后任务 | 正常 |
| AC-5.2 | WHEN FreeNode 转为非 Free 并执行 after-attach tasks THEN 延迟的 RemoveSelfExecuteFunction 在挂主树上下文中执行 | 恢复 |
| AC-5.3 | WHEN FreeNode 尚未挂入主树 THEN AnyChildFocusHub 遍历跳过该 off-main-tree 子树，该子树不参与 CHILD-SCOPE 可聚焦判定 | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.3 | R-1, R-2 | TASK-SKELETON-1 | UT + 源码审查 | `frame_node.cpp:1051-1054,4637-4684` |
| AC-1.4~1.5 | R-3 | TASK-SKELETON-1 | UT | `focus_hub_test_ng.cpp:52-127` |
| AC-2.1~2.4 | R-4, R-5 | TASK-SKELETON-2 | UT + 源码审查 | `ui_node.cpp:929-971`、`focus_hub.cpp:117-162` |
| AC-2.5 | R-6 | TASK-SKELETON-2 | UT | `hierarchical_switching_test.cpp:493-517` |
| AC-3.1~3.3 | R-7, R-8 | TASK-SKELETON-3 | UT | `focus_hub_test_ng.cpp:306-407`、`focus_hub_test_ng_branch_coverage_three.cpp:333-375` |
| AC-3.4 | R-9 | TASK-SKELETON-3 | UT | `focus_hub_test_ng_branch_coverage_three.cpp:383-420` |
| AC-3.5~3.6 | R-10 | TASK-SKELETON-3 | UT + 源码审查 | `focus_hub_test_ng_branch_coverage_three.cpp:821-855` |
| AC-4.1~4.2 | R-11 | TASK-SKELETON-4 | UT | `focus_hub_test_ng.cpp:336-371`、`focus_hub_test_ng_branch_coverage_two.cpp:301-305` |
| AC-4.3~4.6 | R-12, R-13 | TASK-SKELETON-4 | UT + 源码审查 | `focus_hub.cpp:736-742,959-998`、`event_hub.cpp:1073-1098` |
| AC-5.1~5.3 | R-14 | TASK-SKELETON-5 | 源码审查 + 补充 UT | `focus_hub_multithread.cpp:22-57`、`ui_node_multi_thread.cpp:105-130` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | FrameNode 初始化 Pattern | 仅当 `Pattern::GetFocusPattern().GetFocusType()` 非 DISABLE 时主动创建 FocusHub | DISABLE Pattern 可在后续显式调用时惰性创建 | AC-1.1, AC-1.2 |
| R-2 | 行为 | 首次或重复调用 `GetOrCreateFocusHub` | 首次创建并缓存在 `FrameNode::focusHub_`，后续返回同一实例 | EventHub 仅委托 FrameNode；后续重载参数不覆盖已有实例 | AC-1.2, AC-1.3 |
| R-3 | 恢复 | FocusState 获取宿主 FrameNode | 优先升级 `frameNode_`，失败后从 `eventHub_` 回取 | 两者均失效时返回空，名称 `NULL`、ID `-1`、enabled 默认 true | AC-1.4, AC-1.5 |
| R-4 | 行为 | 向上查询焦点父节点 | 跳过非 FrameNode 与 DISABLE，遇 SCOPE 返回，遇 NODE 截断 | boundary-aware 版本遇 Screen 截断 | AC-2.1~2.3 |
| R-5 | 边界 | 遍历子 FocusHub | 仅遍历主树节点；NODE/SCOPE 是投影节点，DISABLE/非 FrameNode 是透明容器 | off-main-tree 子树不参与判定 | AC-2.4, AC-5.3 |
| R-6 | 恢复 | 查询历史焦点叶节点 | 沿 `lastWeakFocusNode_` 弱引用链下钻并返回最后有效候选 | SELF、不可聚焦或弱引用失效时停止；不校验真实后代关系或环路 | AC-2.5 |
| R-7 | 行为 | `IsFocusable` / `IsChildFocusable` 按类型分派 | NODE 与 SCOPE 分别进入对应判定，DISABLE 返回 false | 不改变任何焦点状态 | AC-3.1 |
| R-8 | 行为 | NODE 可聚焦判定 | 同时满足 focusable、parentFocusable、enabled 和 visible | `IsFocusableNode` 扫描祖先可见性；`IsChildFocusableNode` 仅检查自身 | AC-3.2, AC-3.3 |
| R-9 | 行为 | SCOPE 可聚焦判定 | 先满足 NODE 门槛；SELF/AUTO 可由自身承接，CHILD 要求存在可聚焦投影子节点 | AUTO 不要求子节点存在 | AC-3.4 |
| R-10 | 边界 | whole-path 判定 | boundary-aware 父链中的祖先使用 `IsFocusableNode`，目标使用完整 `IsFocusable` 或自身 NODE 门槛 | Screen 为校验上界；祖先不执行 SCOPE 聚合判定 | AC-3.5, AC-3.6 |
| R-11 | 行为 | 显式或隐式修改 focusable | 显式写入锁定优先级；后续隐式写入被忽略；隐式可聚焦 SCOPE 的 CHILD 转为 AUTO | 相同值直接返回；false 引发的清焦事务归 Feat-02 | AC-4.1, AC-4.2 |
| R-12 | 行为 | 查询或通知 enabled/visible | 查询实时读取 EventHub/FrameNode；false 通知触发 RemoveSelf | FocusHub 的 SetEnabled/SetShow 不存储真实状态 | AC-4.3, AC-4.4 |
| R-13 | 恢复 | EventHub 内部临时修改 enabled | `SetEnabledInternal` 仅改生效值，`RestoreEnabled` 恢复开发者值 | `SetEnabled` 同时覆盖生效值和开发者值 | AC-4.5, AC-4.6 |
| R-14 | 恢复 | FreeNode 触发 RemoveSelf | 属性字段立即更新，焦点树清理通过 after-attach task 延迟执行 | 挂主树前存在短暂中间态；未挂主树节点被子焦点遍历排除 | AC-5.1~5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | R-1, R-2, AC-1.1~1.3 | UT | 非 DISABLE 主动创建、DISABLE 惰性创建、重复调用幂等 |
| VM-2 | R-3, AC-1.4~1.5 | UT | FrameNode/EventHub 双宿主回退及无宿主默认值 |
| VM-3 | R-4, AC-2.1~2.3 | UT | SCOPE 返回、NODE 截断、Screen boundary |
| VM-4 | R-5, AC-2.4, AC-5.3 | UT | 主树过滤及焦点树压缩投影 |
| VM-5 | R-6, AC-2.5 | UT | 历史弱引用链、失效节点、SELF 停止条件 |
| VM-6 | R-7~R-9, AC-3.1~3.4 | UT | NODE/SCOPE/DISABLE 与 SELF/AUTO/CHILD 判定矩阵 |
| VM-7 | R-10, AC-3.5~3.6 | UT | whole-path 上界及祖先 NODE 门槛语义 |
| VM-8 | R-11, AC-4.1~4.2 | UT | 显式覆盖隐式及 CHILD→AUTO 转换 |
| VM-9 | R-12, R-13, AC-4.3~4.6 | UT | enabled/visible 实时状态源和 EventHub 双值恢复 |
| VM-10 | R-14, AC-5.1~5.3 | UT + 线程场景审查 | FreeNode 状态立即生效、挂树后清理、off-main-tree 排除 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| N/A | 框架内部 | N/A | N/A | N/A | 已有内部实现补录，不新增 ArkTS、System API、InnerAPI 或 C-API | AC-1.1~5.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|---------|
| N/A | N/A | 无 API 变更或废弃 | 无需迁移 | AC-1.1~5.3 |

## 接口规格

### 接口定义

本特性不新增可开放接口。以下内部入口用于限定规格行为，不构成对外 API 承诺。

**FrameNode::GetOrCreateFocusHub**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<FocusHub> FrameNode::GetOrCreateFocusHub()` |
| 返回值 | `RefPtr<FocusHub>` — 当前 FrameNode 唯一的 FocusHub |
| 开放范围 | 框架内部 |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| N/A | N/A | N/A | N/A | 无参数；FrameNode 已完成基本构造 |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | 非 DISABLE Pattern 初始化 | Scenario 1 | AC-1.1 |
| 2 | DISABLE Pattern 后续请求 | Scenario 1 | AC-1.2, AC-1.3 |

**FocusHub::IsFocusable**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool FocusHub::IsFocusable()` |
| 返回值 | `bool` — 节点按当前类型和实时外部状态是否可聚焦 |
| 开放范围 | 框架内部 |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| N/A | N/A | N/A | N/A | 判定依赖 FocusType、FocusDependence、宿主状态和焦点树 |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | NODE 判定 | Scenario Outline 2 | AC-3.1~3.3 |
| 2 | SCOPE 判定 | Scenario Outline 3 | AC-3.4 |
| 3 | whole-path 判定 | Scenario 4 | AC-3.5, AC-3.6 |

## 兼容性声明

- **已有 API 行为变更:** 否；本次仅补录当前实现行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；焦点状态仅存在于运行时对象。
- **最低支持版本:** 与 NG 焦点框架现有支持范围一致。
- **API 版本号策略:** 本特性核心方法未发现 Target API/Container 版本分支，不新增 `@since`；相邻的按键与激活版本差异由 Feat-03/Feat-06 承接。
- **运行时兼容性:** FrameNode 为当前 FocusHub 持有者，EventHub 弱宿主构造保留为内部迁移兼容入口；FreeNode 与普通节点共享状态规则，但焦点树副作用采用挂树后最终一致性。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| FrameNode 单一持有 | FocusHub 缓存在 `FrameNode::focusHub_`，EventHub 不建立第二份所有权 | AC-1.1~1.4 |
| 焦点树投影 | 焦点关系必须通过 UINode 的焦点父链和主树过滤计算，不得直接等同于普通父子树 | AC-2.1~2.4 |
| 弱引用历史链 | lastWeakFocusNode 不拥有子 FocusHub，仅作为历史路径提示 | AC-2.5 |
| 实时状态源 | enabled/visible 读取 EventHub/FrameNode，FocusHub 不复制真实状态 | AC-3.2, AC-4.3~4.5 |
| 线程隔离 | FreeNode 不直接执行主焦点树清理，必须通过 after-attach task 串行化 | AC-5.1~5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|---------|------|
| 性能 | 单次父链/可见性判定随当前树深度线性增长，不引入额外全局扫描 | 源码审查 + 性能回归 | `focus_hub.cpp:811-856,2234-2270` |
| 功耗 | 无新增周期任务、定时器或后台唤醒 | 源码审查 | 无新增实现 |
| 内存 | 每个 FrameNode 最多缓存一个 FocusHub；父子历史关系使用弱引用 | UT + 源码审查 | `frame_node.cpp:4637-4684`、`focus_state.h:90-96` |
| 安全 | 不新增权限、跨进程边界或敏感数据处理 | 架构审查 | 框架内进程内状态模型 |
| 可靠性 | 宿主失效返回确定默认值；FreeNode 清理采用挂树后任务 | UT + 线程场景审查 | AC-1.5、AC-5.1~5.3 |
| 可测试性 | 每条核心规则至少映射一个 VM；Screen/off-main-tree/环路风险需单独覆盖 | UT | VM-1~VM-10 |
| 自动化维测 | 保留焦点树 dump 能力，不新增埋点格式 | 回归检查 | `focus_hub.cpp:364-476` |
| 定界定位 | FrameName/FrameId 在宿主失效时返回 `NULL`/-1，日志不解引用失效宿主 | UT | AC-1.5 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|---------|------|
| 手机 | 无差异 | 使用相同 NG 焦点树与状态模型 | UT | 核心实现无设备分支 |
| 平板 | 无差异 | 使用相同 NG 焦点树与状态模型 | UT | 核心实现无设备分支 |
| 折叠屏 | 无差异 | 窗口/页面切换行为由后续 Feat 承接，本特性状态模型一致 | 集成测试 | 核心实现无设备分支 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 无障碍焦点是独立状态；本特性仅提供普通焦点节点基础模型，不合并两类状态 | 焦点节点宿主生命周期 |
| 大字体 | 否 | 不涉及布局尺寸和字体度量 | N/A |
| 深色模式 | 否 | 焦点视觉颜色由 Feat-06 承接 | N/A |
| 多窗口/分屏 | 是 | Screen boundary 决定 whole-path 校验上界；窗口焦点事务由 Feat-02/Feat-05 承接 | AC-2.3, AC-3.5 |
| 多用户 | 否 | 无持久化和用户态数据 | N/A |
| 版本升级 | 是 | 核心规则无 Target API 分支，升级不得改变既有投影与判定语义 | 兼容性回归 |
| 生态兼容 | 是 | 公共焦点属性行为依赖本模型，但 API 表面契约保持不变 | `Func-04-03-03-Feat-05` |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 焦点树与节点状态模型
  作为 ArkUI 焦点框架调用方
  我想要稳定的焦点节点、树关系和可聚焦性模型
  以便后续焦点事务和导航得到一致输入

  Scenario: FocusHub 创建与复用
    Given FrameNode 已绑定一个 FocusType 为 NODE 的 Pattern
    When FrameNode 完成 Pattern 初始化并重复调用 GetOrCreateFocusHub
    Then FrameNode 仅创建一个 FocusHub
    And 每次调用都返回同一实例

  Scenario Outline: NODE 可聚焦矩阵
    Given FocusHub 的 FocusType 为 NODE
    When focusable 为 <focusable> 且 parentFocusable 为 <parent> 且 enabled 为 <enabled> 且 visible 为 <visible>
    Then IsFocusableNode 返回 <result>

    Examples:
      | focusable | parent | enabled | visible | result |
      | true | true | true | true | true |
      | false | true | true | true | false |
      | true | false | true | true | false |
      | true | true | false | true | false |
      | true | true | true | false | false |

  Scenario Outline: SCOPE 依赖模式
    Given FocusHub 的 FocusType 为 SCOPE 且基础 NODE 门槛通过
    When FocusDependence 为 <dependence> 且存在可聚焦子节点为 <hasChild>
    Then IsFocusableScope 返回 <result>

    Examples:
      | dependence | hasChild | result |
      | SELF | false | true |
      | AUTO | false | true |
      | CHILD | true | true |
      | CHILD | false | false |

  Scenario: Screen 边界内的整路径判定
    Given 目标 FocusHub 位于一个可聚焦 SCOPE 下且该 SCOPE 位于 Screen 下
    When 调用 IsFocusableWholePath
    Then 仅检查 Screen 边界内的焦点祖先 NODE 门槛
    And 最终对目标执行完整类型判定

  Scenario: FreeNode 延迟清焦
    Given FocusHub 的宿主 FrameNode 为 FreeNode
    When 调用 SetFocusable(false)
    Then focusable 字段立即为 false
    And RemoveSelf 清理被加入挂主树后任务
    When 节点挂入主树并执行 after-attach tasks
    Then 延迟的焦点清理执行
```

## Spec 自审清单

- [x] 无未关闭占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确，已排除 Feat-02~Feat-06 行为
- [x] 无“快速”“稳定”“尽可能”等不可验证要求
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查
- [x] 框架内部能力未虚构 ArkTS SDK 或 C-API 契约
- [x] Target API 扫描结论和 FreeNode 运行时差异已记录

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "NG FocusHub 的 FocusType、FocusPattern、FocusState 与 FrameNode 所有权模型"
  - repo: "openharmony/arkui_ace_engine"
    query: "焦点树投影、可聚焦性 whole-path 判定与 FreeNode 挂树后任务"
```

**关键文档：** `frameworks/core/components_ng/event/focus_hub.h`、`frameworks/core/components_ng/event/focus_hub.cpp`、`frameworks/core/components_ng/base/ui_node.cpp`
