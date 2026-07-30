# 特性规格

> Func-07-02-04-Feat-02 @Local/@Param/@Once/@Event 组件状态输入输出：固化 `@Local`（组件私有，必须本地初始化，V2 的 @State）、`@Param`（父→子单向，按引用传递，V2 的 @Prop）、`@Once`（修饰 @Param 仅首次同步）、`@Event`（子→父回调，默认空函数）、`!!` 双向绑定语法糖的行为规格与 V1 对应装饰器的范式差异。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @Local/@Param/@Once/@Event 组件状态输入输出 |
| 特性编号 | Func-07-02-04-Feat-02 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | API 12 起（ArkTS 卡片 API 23 起）；`!!` 系统组件参数双向绑定 API 18 起；`!!` 与 @Event 混用禁用 API 18 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/04-v2-component-state/design.md` | Draft |
| V2 装饰器定义 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts` | — |
| VariableUtilV2 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts` | — |
| @Local 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-local.md` | — |
| @Param 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-param.md` | — |
| @Once 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-once.md` | — |
| @Event 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-event.md` | — |
| `!!` 双向绑定指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-binding.md` | — |

---

## 用户故事

### US-1: @Local 组件私有状态

**作为** 应用开发者,
**我想要** 用 `@Local` 在 @ComponentV2 中声明组件私有状态变量（必须本地初始化，禁止外部传入）,
**以便** 该变量成为组件内部可观察状态，作为子组件 @Param 的数据源。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在 @ComponentV2 中声明 `@Local var: T = init` THEN `Local`（`v2_decorators.ts:72-76`）委托 `trackInternal` 安装 getter/setter | 正常 |
| AC-1.2 | WHEN @Local 变量未本地初始化 THEN 编译报错，必须本地初始化 | 异常 |
| AC-1.3 | WHEN 外部传入初始化 @Local（`Child({ local: this.x })`）THEN 编译报错，禁止外部传入初始化 | 异常 |
| AC-1.4 | WHEN @Local 装饰的 class/Object 属性变化 THEN 仅观测整体赋值，深度观测依赖 @ObservedV2+@Trace（Feat-02） | 边界 |
| AC-1.5 | WHEN @Local 在 @Component（非 V2）中使用 THEN 编译报错，仅在 @ComponentV2 中可用 | 异常 |

### US-2: @Param 父→子单向输入

**作为** 应用开发者,
**我想要** 用 `@Param` 在 @ComponentV2 中声明父→子单向输入变量（按引用传递，非深拷贝）,
**以便** 建立父到子的单向同步，避免 V1 @Prop 的深拷贝性能损耗。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 在 @ComponentV2 中声明 `@Param var: T` THEN `Param`（`v2_decorators.ts:92-119`）+ `VariableUtilV2.initParam`/`updateParam`（`v2_decorated_variables.ts:32/46`）建立父→子单向同步 | 正常 |
| AC-2.2 | WHEN @Param 复杂类型按引用传递 THEN 与 V1 @Prop 深拷贝不同，避免深拷贝性能损耗 | 正常 |
| AC-2.3 | WHEN 同时存在本地初值和外部传值 THEN 优先使用外部传值 | 边界 |
| AC-2.4 | WHEN 本地无初值且与 @Require 联用 THEN 强制要求外部传入初值 | 边界 |
| AC-2.5 | WHEN 子组件内直接修改 @Param 变量本身（无 @Once）THEN 编译报错，仅父组件可更新；但对象类型属性的修改允许且会同步回数据源 | 异常 |
| AC-2.6 | WHEN @Param 观测能力 THEN 仅观测自身，深度依赖 @Trace（Feat-02） | 边界 |

### US-3: @Once 仅首次同步修饰

**作为** 应用开发者,
**我想要** 用 `@Once` 修饰 `@Param`，使其仅首次同步后不再随数据源变化,
**以便** 实现一次性外部传入后本地可控的状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `@Once` 与 `@Param` 联用 THEN `Once`（`v2_decorators.ts:133-137`）设置 `deco2='@Once'` 元信息，`VariableUtilV2.updateParam` 跳过 `deco2 === '@Once'` 的后续同步 | 正常 |
| AC-3.2 | WHEN @Once 单独使用（无 @Param）THEN 编译报错，必须与 @Param 联用 | 异常 |
| AC-3.3 | WHEN @Once 配合 @Param THEN 可在本地修改 @Param 变量值，效果近似 @Local，但仍能接收外部初始值 | 正常 |
| AC-3.4 | WHEN @Param 与 @Once 顺序不同 THEN 顺序不影响功能（@Param 必须先注册 V2_DECO_META） | 边界 |

### US-4: @Event 子→父回调

**作为** 应用开发者,
**我想要** 用 `@Event` 在子组件声明回调方法，向父组件传递变化,
**以便** 与 @Param 配合实现双向同步（V1 @Link 的显式拆解）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 在 @ComponentV2 中声明 `@Event callback: () => void` THEN `Event`（`v2_decorators.ts:153-156`）装饰，无 `trackInternal` | 正常 |
| AC-4.2 | WHEN @Event 未本地初始化且未外部传入 THEN 自动生成空函数 `() => {}` 作为默认回调 | 正常 |
| AC-4.3 | WHEN @Event 本地有默认值 THEN 使用本地；外部传入时优先外部 | 边界 |
| AC-4.4 | WHEN @Event 装饰非函数变量 THEN 不报错但无意义 | 边界 |
| AC-4.5 | WHEN 子组件调用 @Event 后父组件数据源变化 THEN 父组件变化是同步立即生效；但父→子的回传是异步（渲染前同步回子组件），调用 @Event 后立即读子组件 @Param 仍是旧值 | 边界 |

### US-5: !! 双向绑定语法糖

**作为** 应用开发者,
**我想要** 用 `!!` 语法糖简化 @Param+@Event 的双向绑定写法,
**以便** 父组件 `Child({ value: this.x!! })` 自动生成 @Event 回调。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 自定义组件场景 `Star({ value: this.value!! })` THEN 等价于 `Star({ value: this.value, $value: (val) => { this.value = val } })`，需子组件声明对应 `@Param value` + `@Event $value` | 正常 |
| AC-5.2 | WHEN API 18+ 系统组件参数双向绑定（bindMenu/TextInput/Slider 等系统组件）THEN 变量后加 `!!` 使 TS 变量与系统组件内部状态同步 | 正常 |
| AC-5.3 | WHEN `!!` 用于多层父子组件传递 THEN 不支持（仅单层） | 边界 |
| AC-5.4 | WHEN API 18+ `!!` 与 @Event 混用 THEN 编译报错 | 异常 |
| AC-5.5 | WHEN 三个或更多 `!`（如 `!!!`）THEN 不支持双向绑定 | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @Local trackInternal |
| AC-1.2 | US-1 | R-2 | 编译期校验 |
| AC-1.3 | US-1 | R-2 | 编译期校验 |
| AC-1.4 | US-1 | R-3 | 单元测试 深度观测依赖 @Trace |
| AC-1.5 | US-1 | R-4 | 编译期校验 |
| AC-2.1 | US-2 | R-5 | 单元测试 @Param 单向同步 |
| AC-2.2 | US-2 | R-5 | 单元测试 引用传递 |
| AC-2.3 | US-2 | R-5 | 单元测试 外部优先 |
| AC-2.4 | US-2 | R-6 | 编译期校验 |
| AC-2.5 | US-2 | R-7 | 编译期校验 |
| AC-2.6 | US-2 | R-3 | 单元测试 观测仅自身 |
| AC-3.1 | US-3 | R-8 | 单元测试 @Once 仅首次 |
| AC-3.2 | US-3 | R-9 | 编译期校验 |
| AC-3.3 | US-3 | R-8 | 单元测试 本地修改 |
| AC-3.4 | US-3 | R-8 | 单元测试 顺序无关 |
| AC-4.1 | US-4 | R-10 | 单元测试 @Event 装饰 |
| AC-4.2 | US-4 | R-10 | 单元测试 默认空函数 |
| AC-4.3 | US-4 | R-10 | 单元测试 优先级 |
| AC-4.4 | US-4 | R-11 | 单元测试 非函数无效 |
| AC-4.5 | US-4 | R-12 | 单元测试 异步回传 |
| AC-5.1 | US-5 | R-13 | 单元测试 !! 自定义组件 |
| AC-5.2 | US-5 | R-13 | 单元测试 !! 系统组件 |
| AC-5.3 | US-5 | R-13 | 单元测试 不支持多层 |
| AC-5.4 | US-5 | R-14 | 编译期校验 |
| AC-5.5 | US-5 | R-13 | 单元测试 !!! 不支持 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 在 @ComponentV2 中声明 `@Local var: T = init` | `Local`（`v2_decorators.ts:72-76`）委托 `trackInternal` 安装 getter/setter；@Local 是 V2 的 @State，作为子组件 @Param 的数据源 | 必须本地初始化 | AC-1.1 |
| R-2 | 异常 | @Local 未本地初始化 或 外部传入初始化 | 编译报错：必须本地初始化；禁止外部传入初始化（`Child({ local: this.x })` 非法） | 与 @State（允许外部初始化）差异 | AC-1.2, AC-1.3 |
| R-3 | 行为 | @Local/@Param 装饰的 class/Object | 仅观测整体赋值；深度观测依赖 @ObservedV2+@Trace（Feat-02）；@Local/@Param 观测能力仅限自身 | 第一层为观察边界 | AC-1.4, AC-2.6 |
| R-4 | 异常 | @Local 在 @Component（非 V2）中使用 | 编译报错，仅在 @ComponentV2 中可用 | V2 装饰器限定 @ComponentV2 | AC-1.5 |
| R-5 | 行为 | 在 @ComponentV2 中声明 `@Param var: T` | `Param`（`v2_decorators.ts:92-119`）+ `VariableUtilV2.initParam`/`updateParam`（`v2_decorated_variables.ts:32/46`）建立父→子单向同步；复杂类型按引用传递（vs V1 @Prop 深拷贝）；同时存在本地初值和外部传值时优先外部 | 数据源必须为 @Local 或 @Param 状态变量 | AC-2.1~AC-2.3 |
| R-6 | 边界 | @Param 本地无初值且与 @Require 联用 | 强制要求外部传入初值（对应 V1 @Require 能力） | @Require 来自 V1 | AC-2.4 |
| R-7 | 异常 | 子组件内直接修改 @Param 变量本身（无 @Once） | 编译报错，仅父组件可更新；但对象类型属性的修改允许且会同步回数据源 | @Param 本身只读，属性可改 | AC-2.5 |
| R-8 | 行为 | `@Once` 与 `@Param` 联用 | `Once`（`v2_decorators.ts:133-137`）设置 `deco2='@Once'` 元信息，`VariableUtilV2.updateParam` 跳过 `deco2 === '@Once'` 的后续同步；仅初始化同步一次，后续数据源变化不再同步；@Param 与 @Once 顺序无关（@Param 必须先注册 V2_DECO_META）；配合 @Once 后可在本地修改 @Param 变量值，效果近似 @Local | @Once 不能单独使用 | AC-3.1, AC-3.3, AC-3.4 |
| R-9 | 异常 | @Once 单独使用（无 @Param） | 编译报错，必须与 @Param 联用 | — | AC-3.2 |
| R-10 | 行为 | 在 @ComponentV2 中声明 `@Event callback: () => void` | `Event`（`v2_decorators.ts:153-156`）装饰，无 `trackInternal`；未本地初始化且未外部传入时自动生成空函数 `() => {}` 作为默认回调；本地有默认值用本地，外部传入优先外部；@Event 是规范约束，表示组件输出，与 @Param 配合实现双向同步 | @Event 装饰非函数变量不报错但无意义 | AC-4.1~AC-4.3 |
| R-11 | 边界 | @Event 装饰非函数变量 | 不报错但无意义 | @Event 应装饰回调方法 | AC-4.4 |
| R-12 | 边界 | 子组件调用 @Event 后父组件数据源变化 | 父组件变化同步立即生效；父→子回传异步（渲染前同步回子组件）；调用 @Event 后立即读子组件 @Param 仍是旧值 | V2 异步调度的体现 | AC-4.5 |
| R-13 | 行为 | `!!` 双向绑定语法糖 | 自定义组件：`Star({ value: this.value!! })` 等价于 `Star({ value: this.value, $value: (val) => { this.value = val } })`，需子组件声明 `@Param value` + `@Event $value`；API 18+ 系统组件参数双向绑定（bindMenu/TextInput/Slider 等）；不支持多层父子传递；三个或更多 `!` 不支持；变量需被 @State/@Local 等状态装饰器装饰才触发 UI 刷新 | API 12 自定义组件；API 18 系统组件 | AC-5.1~AC-5.3, AC-5.5 |
| R-14 | 异常 | API 18+ `!!` 与 @Event 混用 | 编译报错 | API 18+ 禁止混用 | AC-5.4 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v2_tests/` @Local trackInternal |
| VM-2 | AC-1.2 | 编译期校验 | ArkTS 编译器 未初始化报错 |
| VM-3 | AC-1.3 | 编译期校验 | ArkTS 编译器 外部传入报错 |
| VM-4 | AC-1.4 | 单元测试 | `v2_tests/` 深度观测依赖 @Trace |
| VM-5 | AC-1.5 | 编译期校验 | ArkTS 编译器 @Component 拒绝 |
| VM-6 | AC-2.1 | 单元测试 | `v2_tests/` @Param 单向同步 |
| VM-7 | AC-2.2 | 单元测试 | `v2_tests/` 引用传递 |
| VM-8 | AC-2.3 | 单元测试 | `v2_tests/` 外部优先 |
| VM-9 | AC-2.4 | 编译期校验 | ArkTS 编译器 @Require 强制 |
| VM-10 | AC-2.5 | 编译期校验 | ArkTS 编译器 @Param 本身只读 |
| VM-11 | AC-2.6 | 单元测试 | `v2_tests/` 观测仅自身 |
| VM-12 | AC-3.1 | 单元测试 | `v2_tests/` @Once 仅首次 |
| VM-13 | AC-3.2 | 编译期校验 | ArkTS 编译器 @Once 单独拒绝 |
| VM-14 | AC-3.3 | 单元测试 | `v2_tests/` 本地修改 |
| VM-15 | AC-3.4 | 单元测试 | `v2_tests/` 顺序无关 |
| VM-16 | AC-4.1 | 单元测试 | `v2_tests/` @Event 装饰 |
| VM-17 | AC-4.2 | 单元测试 | `v2_tests/` 默认空函数 |
| VM-18 | AC-4.3 | 单元测试 | `v2_tests/` 优先级 |
| VM-19 | AC-4.4 | 单元测试 | `v2_tests/` 非函数无效 |
| VM-20 | AC-4.5 | 单元测试 | `v2_tests/` 异步回传 |
| VM-21 | AC-5.1 | 单元测试 | `v2_tests/` !! 自定义组件 |
| VM-22 | AC-5.2 | 单元测试 | `v2_tests/` !! 系统组件 |
| VM-23 | AC-5.3 | 单元测试 | `v2_tests/` 不支持多层 |
| VM-24 | AC-5.4 | 编译期校验 | ArkTS 编译器 !! 与 @Event 混用拒绝 |
| VM-25 | AC-5.5 | 单元测试 | `v2_tests/` !!! 不支持 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `Local` | `v2_decorators.ts:72-76` | @Local 装饰器，委托 trackInternal |
| `Param` | `v2_decorators.ts:92-119` | @Param 装饰器，建立父→子单向 |
| `Once` | `v2_decorators.ts:133-137` | @Once 修饰 @Param 仅首次同步 |
| `Event` | `v2_decorators.ts:153-156` | @Event 装饰器，默认 () => {} |
| `VariableUtilV2` | `v2_decorated_variables.ts:24-86` | @Param 运行时：`initParam`(32)/`updateParam`(46)/`resetParam`(75) |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | @Local/@Param/@Once/@Event 引入；`!!` 自定义组件双向绑定 | V2 组件状态输入输出 | V1 @State→@Local；V1 @Prop→@Param；V1 @Link→@Param+@Event |
| API 12 | @Param 按引用传递（V1 @Prop 深拷贝） | 避免深拷贝性能损耗 | 注意引用语义变化 |
| API 18 | `!!` 扩展支持系统组件参数双向绑定；`!!` 与 @Event 混用禁用 | 更多场景可用 `!!` | 避免与 @Event 混用 |
| API 23 | @Local/@Param/@Once/@Event 支持 ArkTS 卡片 | 卡片可用 V2 装饰器 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| @Local 必须本地初始化 | @Local 必须本地初始化，禁止外部传入；与 @State（允许外部初始化）差异 |
| @Param 单向引用 | @Param 父→子单向，按引用传递（vs V1 @Prop 深拷贝）；@Param 本身只读，对象属性可改且同步回源 |
| @Once 修饰 @Param | @Once 必须与 @Param 联用，仅首次同步；单独使用编译报错 |
| @Event 显式双向 | @Event 与 @Param 配合实现双向同步（V1 @Link 的显式拆解）；默认 () => {} |
| `!!` 语法糖 | `!!` 自动生成 @Event 回调；不支持多层；API 18+ 禁与 @Event 混用 |
| 仅 @ComponentV2 | @Local/@Param/@Once/@Event 仅在 @ComponentV2 中可用 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | @Param 按引用传递避免 V1 @Prop 深拷贝开销；@Event 无 trackInternal 无依赖收集开销 |
| 可调试性 | @Param 断点：`VariableUtilV2.initParam`/`updateParam`；@Event 检查默认空函数 |
| 可观测性 | `UIUtils.canBeObserved`(API 23+) 返回 @Param/@Local 装饰器信息 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| V2 组件通信基础 | @Local/@Param/@Event 是 @ComponentV2 组件状态输入输出的核心机制；@Local 是 @Param 的数据源 |
| @Computed/@Monitor 基础 | @Local/@Param/@Provider/@Consumer/@Computed 可被 @Monitor 监听（Feat-04） |
| V1 对比 | @Local 对应 @State；@Param 对应 @Prop；@Param+@Event 对应 @Link；@Once 修饰 @Param 实现一次性同步 |
| @ReusableV2 重置 | 复用时 @Local 用初始值，@Param/@Event 有外部用外部否则用初始值（Feat-06） |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:72-76` | `Local` @Local 装饰器 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:92-119` | `Param` @Param 装饰器 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:133-137` | `Once` @Once 装饰器 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:153-156` | `Event` @Event 装饰器 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts:24-86` | `VariableUtilV2` @Param 运行时（initParam/updateParam/resetParam） |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | @Local/@Param/@Once/@Event 行为回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-local.md` | @Local 开发指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-param.md` | @Param 开发指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-once.md` | @Once 开发指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-event.md` | @Event 开发指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-binding.md` | `!!` 双向绑定指南 |
