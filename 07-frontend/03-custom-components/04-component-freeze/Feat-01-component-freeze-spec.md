# 特性规格

> Func-07-03-04-Feat-01 自定义组件冻结机制：固化 `freezeWhenInactive` 配置（`@Component`/`@ComponentV2` options）、6 类冻结触发场景、V1 三态机（`DelayedNotifyChangesEnum`：do_not_delay/delay_none_pending/delay_notification_pending）暂存回放与 V2 实时检查（`isViewActive()`）差异、`activeCount_` 引用计数、配置继承（`isCompFreezeAllowed_`）、混用场景改进（API 18+）、BuilderNode `inheritFreezeOptions`（API 20+）、复用混用例外（上树后不触发 @Watch）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自定义组件冻结机制 |
| 特性编号 | Func-07-03-04-Feat-01 |
| 优先级 | P1 |
| 目标版本 | freezeWhenInactive API 11 起；混用场景改进 API 18 起；BuilderNode inheritFreezeOptions API 20 起；Repeat 缓存池冻结 API 18 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/03-custom-components/04-component-freeze/design.md` | Baselined |
| ViewPU（setActiveInternal） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts` | — |
| V1 三态机 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property_abstract.ts` | — |
| ViewV2（冻结） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_view.ts` | — |
| PUV2ViewBase（继承） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts` | — |
| V1 组件冻结指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-custom-components-freeze.md` | — |
| V2 组件冻结指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-custom-components-freezeV2.md` | — |

---

## 用户故事

### US-1: freezeWhenInactive 配置与冻结场景

**作为** 应用开发者,
**我想要** 用 `freezeWhenInactive: true` 配置冻结不可见组件,
**以便** 减少无效 UI 刷新，提升性能。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `@Component({ freezeWhenInactive: true })` 配置 THEN 组件进入 inactive 时暂停 UI 刷新与状态变更回调（@Watch/@Monitor） | 正常 |
| AC-1.2 | WHEN `@ComponentV2({ freezeWhenInactive: true })` 配置 THEN 同上，V2 用实时 `isViewActive()` 检查 | 正常 |
| AC-1.3 | WHEN 6 类冻结场景 THEN 组件为 inactive：①router 非栈顶不可见页面 ②TabContent 非当前显示 ③LazyForEach 缓存节点 ④Navigation 未显示 NavDestination ⑤组件复用进入复用池 ⑥混用场景 | 正常 |
| AC-1.4 | WHEN 组件 active/inactive 状态 THEN 不等同于其可见性；冻结仅适用于上述 6 类场景 | 边界 |
| AC-1.5 | WHEN Repeat 缓存池中的节点（API 18+）THEN 组件为 inactive（屏上节点为 active） | 正常 |
| AC-1.6 | WHEN 可仅给子组件单独设置 `freezeWhenInactive: true` THEN 父组件不冻结但子组件冻结 | 边界 |
| AC-1.7 | WHEN 页面生命周期 `OnPageShow` THEN 当前 Page 根节点设为 active（灭屏亮屏也会触发，影响 LazyForEach） | 正常 |

### US-2: V1 三态机暂存回放

**作为** 框架维护者,
**我想要** V1 冻结用三态机暂存状态变更并在激活时回放,
**以便** 冻结期间状态不丢失。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 组件 active（`do_not_delay`=0）THEN 状态变更立即通知 | 正常 |
| AC-2.2 | WHEN 组件进入 inactive（`setActiveInternal(false)`，`pu_view.ts:483-522`）THEN `delayedNotification_` 切换为 `delay_none_pending`(1) | 正常 |
| AC-2.3 | WHEN 组件 inactive 且状态变更 THEN `delayedNotification_` 切换为 `delay_notification_pending`(2)，暂存待处理 elmtId | 正常 |
| AC-2.4 | WHEN 组件继续 inactive 且继续变更 THEN 累积暂存更多 elmtId | 正常 |
| AC-2.5 | WHEN 组件由 inactive→active THEN `performDelayedUpdate` 统一回放暂存的 elmtId，重新刷新冻结期间的状态变量，@Watch 回调被再次调用 | 正常 |
| AC-2.6 | WHEN 组件 `delay_none_pending` 状态（inactive 但无变更）THEN 激活时无回放操作 | 边界 |

### US-3: V2 实时检查

**作为** 框架维护者,
**我想要** V2 冻结用实时 `isViewActive()` 检查（无三态机）,
**以便** V2 冻结更直接高效。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN V2 `isViewActive()`（`puv2_view_base.ts:760`）基于 `activeCount_ > 0` THEN 返回当前激活状态 | 正常 |
| AC-3.2 | WHEN V2 组件冻结期间状态变更 THEN 实时检查 `isViewActive()` 返回 false，不触发 UI 刷新/@Monitor | 正常 |
| AC-3.3 | WHEN V2 组件解冻（activeCount_ 从 0→1）THEN `performDelayedUpdate`（`v2_view.ts:920`）处理延迟的刷新 | 正常 |
| AC-3.4 | WHEN V2 组件冻结期间 @Computed/@Monitor THEN 不触发（实时检查拦截） | 边界 |
| AC-3.5 | WHEN V2 复用回收 `freezeRecycledComponent`（`v2_view.ts:312`）THEN `activeCount_--` 冻结 | 正常 |
| AC-3.6 | WHEN V2 复用解冻 `unfreezeReusedComponent`（`v2_view.ts:328`）THEN 回放 `elmtIdsDelayedUpdate_` 到 `elmtIdsChanged_` | 正常 |

### US-4: 配置继承与混用改进

**作为** 应用开发者,
**我想要** 子组件继承父组件冻结配置，并了解混用场景改进,
**以便** 简化配置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 子组件未设置 `freezeWhenInactive` THEN 继承父组件配置（`PUV2ViewBase.isCompFreezeAllowed_`，`puv2_view_base.ts:119`） | 正常 |
| AC-4.2 | WHEN API 17 及以下父组件解冻 THEN 解冻子组件所有节点（包括非屏上节点） | 边界 |
| AC-4.3 | WHEN API 18+ 父组件解冻 THEN 只解冻子组件的屏上节点（混用场景改进，减少不必要的刷新） | 边界 |
| AC-4.4 | WHEN API 20+ BuilderNode 配置 `inheritFreezeOptions: true` THEN BuilderNode 继承父组件冻结能力（API 20 前 BuilderNode 无法继承冻结） | 正常 |
| AC-4.5 | WHEN API 20 前 BuilderNode THEN 子组件无法被冻结，即使父组件开启冻结 | 边界 |

### US-5: 复用混用例外

**作为** 应用开发者,
**我想要** 了解冻结与复用混用时的特殊行为,
**以便** 正确预期回调触发。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 组件复用与冻结混用，子组件从复用池被复用（上树）THEN 重新标记为 active，但**不触发 @Watch 回调** | 边界 |
| AC-5.2 | WHEN 复用时执行脏节点刷新 THEN 包括冻结期间延迟刷新的变量绑定的系统组件，并清空脏节点列表 | 正常 |
| AC-5.3 | WHEN 解冻时判断冻结期间无变量改变 THEN 不触发 @Watch（复用已清空脏节点列表） | 边界 |
| AC-5.4 | WHEN 即使 `aboutToReuse` 中改值 THEN 解冻时同样不触发 @Watch（复用执行逻辑早于组件解冻） | 边界 |
| AC-5.5 | WHEN 组件复用与冻结混用原因 THEN 复用执行逻辑早于组件解冻：复用时执行脏节点刷新并清空脏节点列表，解冻时判断冻结期间无变量改变不触发 @Watch | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @Component 冻结 |
| AC-1.2 | US-1 | R-1 | 单元测试 @ComponentV2 冻结 |
| AC-1.3 | US-1 | R-2 | 单元测试 6 类场景 |
| AC-1.4 | US-1 | R-2 | 单元测试 active≠可见性 |
| AC-1.5 | US-1 | R-2 | 单元测试 Repeat 缓存池 |
| AC-1.6 | US-1 | R-3 | 单元测试 子组件单独冻结 |
| AC-1.7 | US-1 | R-4 | 单元测试 OnPageShow |
| AC-2.1~2.6 | US-2 | R-5 | 单元测试 V1 三态机 |
| AC-3.1~3.6 | US-3 | R-6 | 单元测试 V2 实时检查 |
| AC-4.1 | US-4 | R-3 | 单元测试 配置继承 |
| AC-4.2 | US-4 | R-7 | 单元测试 API 17 全解冻 |
| AC-4.3 | US-4 | R-7 | 单元测试 API 18 屏上解冻 |
| AC-4.4 | US-4 | R-8 | 单元测试 BuilderNode 继承 |
| AC-4.5 | US-4 | R-8 | 单元测试 API 20 前限制 |
| AC-5.1~5.5 | US-5 | R-9 | 单元测试 复用混用例外 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `freezeWhenInactive: true` | 组件 inactive 时暂停 UI 刷新与 @Watch/@Monitor 回调；V1 用三态机暂存回放；V2 用实时 `isViewActive()` 检查 | API 11+ | AC-1.1~AC-1.2 |
| R-2 | 行为 | 6 类冻结场景 | ①router 非栈顶 ②TabContent 非当前 ③LazyForEach 缓存 ④Navigation 未显示 ⑤组件复用回收 ⑥混用；Repeat 缓存池（API 18+）；active/inactive 不等同于可见性；仅适用于上述场景；可仅给子组件单独设置 | — | AC-1.3~AC-1.6 |
| R-3 | 行为 | 配置继承 | 子未设置则继承父（`isCompFreezeAllowed_`(119)） | — | AC-1.6, AC-4.1 |
| R-4 | 行为 | OnPageShow | 当前 Page 根节点设为 active（灭屏亮屏也触发，影响 LazyForEach） | — | AC-1.7 |
| R-5 | 行为 | V1 三态机 | `DelayedNotifyChangesEnum`：`do_not_delay`(0) 立即通知 / `delay_none_pending`(1) 冻结无待处理 / `delay_notification_pending`(2) 冻结有暂存；`setActiveInternal`(483-522) 驱动切换；状态变更暂存 elmtId；激活时 `performDelayedUpdate` 统一回放 @Watch 被再次调用 | V1 专属 | AC-2.1~AC-2.6 |
| R-6 | 行为 | V2 实时检查 | `isViewActive()`(760) 基于 `activeCount_ > 0`；冻结期间状态变更实时检查返回 false 不触发；解冻 `performDelayedUpdate`(920) 处理延迟刷新；复用回收 `freezeRecycledComponent`(312) activeCount_--；复用解冻 `unfreezeReusedComponent`(328) 回放延迟集 | V2 专属（无三态枚举） | AC-3.1~AC-3.6 |
| R-7 | 边界 | 混用场景改进 | API 17-：父解冻解冻子所有节点；API 18+：只解冻子屏上节点 | 版本差异 | AC-4.2~AC-4.3 |
| R-8 | 边界 | BuilderNode 继承 | API 20+ `inheritFreezeOptions: true` 继承父冻结；API 20 前 BuilderNode 无法继承 | API 20+ | AC-4.4~AC-4.5 |
| R-9 | 边界 | 复用混用例外 | 复用上树后重新标记 active 但**不触发 @Watch**；复用时脏节点刷新（含冻结期间延迟的）并清空；解冻时无变量改变不触发 @Watch；aboutToReuse 改值也不触发；原因：复用执行逻辑早于组件解冻 | 复用与冻结协同 | AC-5.1~AC-5.5 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v1_tests/` @Component 冻结 |
| VM-2 | AC-1.2 | 单元测试 | `v2_tests/` @ComponentV2 冻结 |
| VM-3 | AC-1.3 | 单元测试 | `v1_tests/` 6 类场景 |
| VM-4 | AC-1.4 | 单元测试 | `v1_tests/` active≠可见性 |
| VM-5 | AC-1.5 | 单元测试 | `v2_tests/` Repeat 缓存池 |
| VM-6 | AC-1.6 | 单元测试 | `v1_tests/` 子组件单独冻结 |
| VM-7 | AC-1.7 | 单元测试 | `v1_tests/` OnPageShow |
| VM-8 | AC-2.1 | 单元测试 | `v1_tests/` do_not_delay |
| VM-9 | AC-2.2 | 单元测试 | `v1_tests/` delay_none_pending |
| VM-10 | AC-2.3 | 单元测试 | `v1_tests/` delay_notification_pending |
| VM-11 | AC-2.4 | 单元测试 | `v1_tests/` 累积暂存 |
| VM-12 | AC-2.5 | 单元测试 | `v1_tests/` performDelayedUpdate 回放 |
| VM-13 | AC-2.6 | 单元测试 | `v1_tests/` delay_none_pending 无回放 |
| VM-14 | AC-3.1 | 单元测试 | `v2_tests/` isViewActive |
| VM-15 | AC-3.2 | 单元测试 | `v2_tests/` 冻结期间不触发 |
| VM-16 | AC-3.3 | 单元测试 | `v2_tests/` 解冻 performDelayedUpdate |
| VM-17 | AC-3.4 | 单元测试 | `v2_tests/` @Computed/@Monitor 不触发 |
| VM-18 | AC-3.5 | 单元测试 | `repeat_tests/` freezeRecycledComponent |
| VM-19 | AC-3.6 | 单元测试 | `repeat_tests/` unfreezeReusedComponent |
| VM-20 | AC-4.1 | 单元测试 | `v1_tests/` 配置继承 |
| VM-21 | AC-4.2 | 单元测试 | `v1_tests/` API 17 全解冻 |
| VM-22 | AC-4.3 | 单元测试 | `v2_tests/` API 18 屏上解冻 |
| VM-23 | AC-4.4 | 单元测试 | `v2_tests/` BuilderNode 继承 |
| VM-24 | AC-4.5 | 单元测试 | `v2_tests/` API 20 前限制 |
| VM-25 | AC-5.1 | 单元测试 | `repeat_tests/` 复用上树不触发 @Watch |
| VM-26 | AC-5.2 | 单元测试 | `repeat_tests/` 复用脏节点刷新 |
| VM-27 | AC-5.3 | 单元测试 | `repeat_tests/` 解冻无变量不触发 |
| VM-28 | AC-5.4 | 单元测试 | `repeat_tests/` aboutToReuse 改值 |
| VM-29 | AC-5.5 | 代码审查 | 复用执行逻辑早于解冻 |

---

## 枚举规格

### DelayedNotifyChangesEnum（V1 冻结三态机）

| 常量 | 值 | 说明 | 来源 |
|------|-----|------|------|
| do_not_delay | 0 | 组件激活，状态变更立即通知 | `pu_observed_property_abstract.ts` |
| delay_none_pending | 1 | 组件冻结，暂无待处理变更 | `pu_observed_property_abstract.ts` |
| delay_notification_pending | 2 | 组件冻结且有暂存变更，激活时 performDelayedUpdate 统一回放 | `pu_observed_property_abstract.ts` |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `setActiveInternal` | `pu_view.ts:483-522` | V1 active/inactive 切换，驱动三态机 |
| `DelayedNotifyChangesEnum` | `pu_observed_property_abstract.ts` | V1 冻结三态枚举 |
| `performDelayedUpdate` | `pu_view.ts` / `v2_view.ts:920` | V1/V2 激活时延迟刷新回放 |
| `isViewActive()` | `puv2_view_base.ts:760` | V2 实时激活状态检查 |
| `isCompFreezeAllowed_` | `puv2_view_base.ts:119` | freezeWhenInactive 配置继承 |
| `activeCount_` | `puv2_view_base.ts:104` | API 18+ 引用计数 |
| `freezeRecycledComponent` | `v2_view.ts:312` | V2 复用回收冻结 |
| `unfreezeReusedComponent` | `v2_view.ts:328` | V2 复用解冻 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 11 | freezeWhenInactive 引入 | 组件冻结 | 无需迁移 |
| API 18 | 混用改进（只解冻屏上节点）；Repeat 缓存池冻结 | 行为变化 | 注意混用场景 |
| API 20 | BuilderNode inheritFreezeOptions | BuilderNode 继承冻结 | 配置 inheritFreezeOptions |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| active/inactive ≠ 可见性 | 冻结仅适用于 6 类场景；active/inactive 不等同于组件可见性 |
| V1 三态暂存回放 | V1 用 DelayedNotifyChangesEnum 暂存变更，激活时 performDelayedUpdate 回放 |
| V2 实时检查 | V2 用 isViewActive() 实时检查，无三态枚举 |
| 配置继承 | 子未设置则继承父 isCompFreezeAllowed_ |
| 混用改进 | API 17- 全节点解冻 / API 18+ 屏上节点解冻 |
| 复用混用例外 | 复用上树不触发 @Watch（复用早于解冻） |
| @ComponentV2 不支持 LazyForEach | @ComponentV2 不支持 LazyForEach 缓存节点冻结（与 @Component 差异） |
| 与状态管理交叉 | 状态变量冻结行为（@Watch 延迟/@State 暂存）详见 07-02-01 Feat-06 / 07-02-04 Feat-04 |
| 与生命周期交叉 | activeCount_ 与 @ComponentActive/@Inactive 协同详见 07-03-02 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 冻结避免不可见组件的无效刷新；V1 三态暂存有内存开销；V2 实时检查更高效 |
| 可调试性 | `hidumper -s WindowManagerService -a "-inactiveComponents"` 查询非激活组件；`-dirtyElementIds` 查询 dirty；日志：`delays @Watch function while component is frozen` |
| 可观测性 | DFX trace 含冻结/解冻事件；Inspector 显示 active/inactive 状态 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 自定义组件体系 | 冻结与组件化（07-03-01）、生命周期（07-03-02）、复用（07-03-03）协同 |
| 状态管理 | 状态变量冻结行为（@Watch 延迟、@State 暂存）与 07-02 交叉 |
| 组件复用 | 回收期间冻结 + 复用混用例外与 07-03-03 协同 |
| LazyForEach/Repeat | 缓存节点冻结与 07-05 渲染控制协同 |
| Navigation/TabContent | 容器场景触发冻结 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 标准冻结 | — | 单元测试 | — |
| 平板 | Split 模式下非活动分屏的组件冻结 | activeCount_ 适配 | 单元测试 | — |
| 折叠屏 | 折叠时非可见区域组件冻结 | — | 单元测试 | — |
| 穿戴 | 小屏列表场景冻结频繁 | capacity 合理设置 | 性能测试 | — |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 规则编号连续且可追溯到源码
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file 信息
- [x] 变更范围 Delta 明确标注为已有实现补录

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:483-522` | `setActiveInternal` V1 active/inactive 切换 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property_abstract.ts` | `DelayedNotifyChangesEnum` V1 三态枚举 + `enableDelayedNotification`/`moveElmtIdsForDelayedUpdate` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_view.ts:312-340` | `freezeRecycledComponent`/`unfreezeReusedComponent` V2 复用冻结/解冻 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_view.ts:920` | `performDelayedUpdate` V2 延迟刷新 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts:104` | `activeCount_` 引用计数 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts:119` | `isCompFreezeAllowed_` 配置继承 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts:760` | `isViewActive()` V2 实时检查 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` | V1 冻结三态机/6 类场景/配置继承 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | V2 实时检查/BuilderNode 继承 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/repeat_tests/` | 复用混用例外 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-custom-components-freeze.md` | V1 组件冻结指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-custom-components-freezeV2.md` | V2 组件冻结指南 |
