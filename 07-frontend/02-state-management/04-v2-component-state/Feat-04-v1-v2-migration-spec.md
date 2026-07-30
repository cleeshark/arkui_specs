# 特性规格

> Func-07-02-04-Feat-04 V1↔V2 迁移与混用规则：固化 V1→V2 装饰器迁移对应表、V1/V2 混用规则（API 19 前严格/API 19+ 解禁）、V1/V2 混用永久约束。桥接 API（`enableV2Compatibility`/`makeV1Observed`）详见 07-02-07 辅助接口生命周期/复用/冻结详见 07-03-02/03/04。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | V1↔V2 迁移与混用规则 |
| 特性编号 | Func-07-02-04-Feat-04 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | V2 装饰器 API 12 起；V1/V2 混用解禁 API 19 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/04-v2-component-state/design.md` | Baselined |
| V1→V2 迁移概述 | `docs/zh-cn/application-dev/ui/state-management/arkts-v1-v2-migration.md` | — |
| V1/V2 更新机制差异 | `docs/zh-cn/application-dev/ui/state-management/arkts-v1-v2-update-difference.md` | — |
| V1/V2 混用指导（API 19+） | `docs/zh-cn/application-dev/ui/state-management/arkts-v1-v2-mixusage.md` | — |
| V1/V2 混用指导（API 19 前） | `docs/zh-cn/application-dev/ui/state-management/arkts-v1-v2-mixusage-before-api-version.md` | — |

---

## 用户故事

### US-1: V1→V2 装饰器迁移对应

**作为** 应用开发者,
**我想要** 明确 V1 装饰器到 V2 装饰器的迁移对应关系,
**以便** 将 V1 组件逐步迁移到 V2。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN V1→V2 组件装饰器迁移 THEN @Component→@ComponentV2 | 正常 |
| AC-1.2 | WHEN V1→V2 组件内状态迁移 THEN @State(无外部初始化)→@Local；@State(需外部初始化)→@Param+@Once | 正常 |
| AC-1.3 | WHEN V1→V2 父子同步迁移 THEN @Prop→@Param（引用传递替代深拷贝）；@Link→@Param+@Event（显式双向替代框架封装双向） | 正常 |
| AC-1.4 | WHEN V1→V2 数据对象迁移 THEN @Observed→@ObservedV2；@ObjectLink→@ObservedV2+@Trace（无需逐层拆解）；@Track→@Trace | 正常 |
| AC-1.5 | WHEN V1→V2 跨层同步迁移 THEN @Provide/@Consume→@Provider/@Consumer | 正常 |
| AC-1.6 | WHEN V1→V2 监听迁移 THEN @Watch→@Monitor（路径感知 + before/now/path） | 正常 |
| AC-1.7 | WHEN V1→V2 存储迁移 THEN LocalStorage→@ObservedV2+@Trace；AppStorage→AppStorageV2；PersistentStorage→PersistenceV2；Environment→Ability 接口（详见 07-06 响应式环境变量） | 正常 |
| AC-1.8 | WHEN V1→V2 更新机制差异 THEN V1 同步通知（事件触发→@Watch 同步→标脏→VSync）变为 V2 异步调度（事件触发→Promise 微任务→@Computed→@Monitor→标脏→VSync） | 边界 |

### US-2: V1/V2 混用规则

**作为** 应用开发者,
**我想要** 明确 V1/V2 混用的约束与规则,
**以便** 在迁移过渡期正确处理 V1/V2 混用场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN API 19 前 V1 组件中使用 V2 装饰器 THEN 编译报错（V1 自定义组件中不可使用 V2 装饰器） | 异常 |
| AC-2.2 | WHEN API 19 前 V1 状态变量传给 V2 组件 THEN 仅限简单类型（boolean/number/enum/string/undefined/null）；复杂类型（class/Array/Map/Set/Date）编译报错 | 边界 |
| AC-2.3 | WHEN API 19 前 V2 状态变量传给 V1 组件 THEN 仅 @State/@Prop/@Provide 接收；不支持 built-in 类型 Array/Set/Map/Date（编译报错） | 边界 |
| AC-2.4 | WHEN API 19 前 @ObservedV2+@Trace 实例在 V1 中使用 THEN 可独立使用，但不能与 V1 状态变量装饰器联用 | 边界 |
| AC-2.5 | WHEN API 19+ V1/V2 混用 THEN 减少约束，提供 `enableV2Compatibility`/`makeV1Observed` 桥接 API（详见 07-02-07 辅助接口） | 正常 |
| AC-2.6 | WHEN V1/V2 混用永久约束（API 19+ 仍生效）THEN V1 装饰器不能与 @ObservedV2 一起使用；V2→V1 不支持用装饰器接收 @ObservedV2 装饰的 class | 边界 |
| AC-2.7 | WHEN built-in 类型（Array/Map/Set/Date）跨范式传递 THEN 建议同时调用 `enableV2Compatibility` + `makeV1Observed` 避免双重代理（详见 07-02-07） | 边界 |
| AC-2.8 | WHEN 多个装饰器装饰同一变量 THEN 不允许（@Watch/@Once/@Require 除外） | 异常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1~1.8 | US-1 | R-1 | 代码审查 迁移对应表 |
| AC-2.1 | US-2 | R-2 | 编译期校验 |
| AC-2.2~2.3 | US-2 | R-2 | 编译期校验 |
| AC-2.4 | US-2 | R-2 | 编译期校验 |
| AC-2.5 | US-2 | R-3 | 单元测试 桥接 API |
| AC-2.6 | US-2 | R-4 | 编译期校验 |
| AC-2.7 | US-2 | R-3 | 单元测试 built-in 双重代理 |
| AC-2.8 | US-2 | R-4 | 编译期校验 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | V1→V2 迁移 | @Component→@ComponentV2、@State(无外部)→@Local、@State(需外部)→@Param+@Once、@Prop→@Param（引用传递）、@Link→@Param+@Event（显式双向）、@Observed→@ObservedV2、@ObjectLink→@ObservedV2+@Trace（无需逐层拆解）、@Track→@Trace、@Provide/@Consume→@Provider/@Consumer、@Watch→@Monitor（路径+前后值）；存储：LocalStorage→@ObservedV2+@Trace、AppStorage→AppStorageV2、PersistentStorage→PersistenceV2、Environment→Ability 接口（详见 07-06 响应式环境变量）；更新机制从同步通知变为异步调度 | V1 同步 vs V2 异步 | AC-1.1~AC-1.8 |
| R-2 | 边界 | API 19 前 V1/V2 混用 | 严格校验：V1 组件中不可使用 V2 装饰器（编译报错）；V1 状态变量传 V2 仅限简单类型（boolean/number/enum/string/undefined/null），复杂类型编译报错；V2 状态变量传 V1 仅 @State/@Prop/@Provide 接收，不支持 built-in；@ObservedV2+@Trace 可独立在 V1 中使用但不能与 V1 状态变量装饰器联用 | API 19 前严格 | AC-2.1~AC-2.4 |
| R-3 | 行为 | API 19+ V1/V2 混用 | 减少约束，提供 `enableV2Compatibility`/`makeV1Observed` 桥接 API（详见 07-02-07）；built-in 类型跨范式传递建议同时调用两者避免双重代理 | 桥接 API 详见 07-02-07 | AC-2.5, AC-2.7 |
| R-4 | 边界 | V1/V2 混用永久约束 | V1 装饰器不能与 @ObservedV2 一起使用；V2→V1 不支持用装饰器接收 @ObservedV2 装饰的 class；多个装饰器不允许装饰同一变量（@Watch/@Once/@Require 除外） | API 19+ 仍生效 | AC-2.6, AC-2.8 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1~1.8 | 代码审查 | 迁移对应表 + 更新机制差异 |
| VM-2 | AC-2.1 | 编译期校验 | ArkTS 编译器 V1 中禁 V2 装饰器 |
| VM-3 | AC-2.2~2.3 | 编译期校验 | ArkTS 编译器 类型限制 |
| VM-4 | AC-2.4 | 编译期校验 | ArkTS 编译器 @ObservedV2 限制 |
| VM-5 | AC-2.5 | 单元测试 | `v2_tests/` 桥接 API（详见 07-02-07） |
| VM-6 | AC-2.6 | 编译期校验 | ArkTS 编译器 永久约束 |
| VM-7 | AC-2.7 | 单元测试 | `v2_tests/` built-in 双重代理 |
| VM-8 | AC-2.8 | 编译期校验 | ArkTS 编译器 多装饰器 |

---

## 核心类与机制清单

本 spec 为迁移指导性质，核心机制由以下域覆盖：

| 机制 | 归属 |
|------|------|
| enableV2Compatibility / makeV1Observed | 07-02-07 Feat-01（辅助接口） |
| @ComponentV2 生命周期/复用/冻结 | 07-03-02/03/04（自定义组件） |
| V2 装饰器语义 | 07-02-04 Feat-01~03 + 07-02-05 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | V2 装饰器引入（@ObservedV2/@Trace/@Local/@Param 等），V1/V2 并存 | V1/V2 范式隔离 | 无需迁移 |
| API 19 | V1/V2 混用解禁（`enableV2Compatibility`/`makeV1Observed`） | 减少混用约束 | 详见 07-02-07 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| V1/V2 范式隔离 | V1 属性包装对象 vs V2 getter/setter + ObserveV2 单例；不能装饰同一变量 |
| API 19 分水岭 | API 19 前严格校验；API 19+ 提供桥接 API 减少约束 |
| 永久约束 | V1 装饰器不能与 @ObservedV2 一起使用（API 19+ 仍生效） |
| 更新机制差异 | V1 同步通知 vs V2 异步调度（Promise.resolve.then 合并） |
| 桥接 API 归属 | enableV2Compatibility/makeV1Observed 详见 07-02-07 |
| 生命周期/复用/冻结归属 | 自定义组件机制详见 07-03-02/03/04 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 迁移对应表为静态映射无运行时开销；混用规则为编译期校验无运行时开销 |
| 可调试性 | V1/V2 更新机制差异可通过 DFX trace 观察同步 vs 异步通知路径 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| V1/V2 共存 | 本 spec 的迁移对应表与混用规则是 V1→V2 渐进迁移的核心参考 |
| 辅助接口协同 | 桥接 API（enableV2Compatibility/makeV1Observed）详见 07-02-07 |
| 自定义组件协同 | 生命周期/复用/冻结的 V1↔V2 差异详见 07-03-02/03/04 |

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

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-v1-v2-migration.md` | V1→V2 迁移概述 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-v1-v2-update-difference.md` | V1/V2 更新机制差异 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-v1-v2-mixusage.md` | V1/V2 混用指导（API 19+） |
| `docs/zh-cn/application-dev/ui/state-management/arkts-v1-v2-mixusage-before-api-version.md` | V1/V2 混用指导（API 19 前） |
