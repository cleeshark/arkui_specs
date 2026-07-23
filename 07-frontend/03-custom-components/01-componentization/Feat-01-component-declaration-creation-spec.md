# 特性规格

> Func-07-03-01-Feat-01 @Component/@ComponentV2 自定义组件声明与创建：固化 `@Component`（V1）/`@ComponentV2`（V2）装饰 struct 声明自定义组件、`build()` 方法描述 UI、`@Entry` 装饰根组件、`@Require` 强制构造传参、组件树构建管线（`observeComponentCreation`/`observeComponentCreation2`）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @Component/@ComponentV2 自定义组件声明与创建 |
| 特性编号 | Func-07-03-01-Feat-01 |
| 优先级 | P0 |
| 目标版本 | @Component/@Entry API 7 起；@Require API 11 起；@ComponentV2 API 12 起 |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/03-custom-components/01-componentization/design.md` | Baselined |
| ViewPU | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts` | — |
| ViewV2 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_view.ts` | — |
| PUV2ViewBase | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts` | — |
| UpdateFuncRecord | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_updatefunc.ts` | — |
| 创建自定义组件指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-create-custom-components.md` | — |
| @Component API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-custom-component-decorator-component.md` | — |
| @ComponentV2 API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-custom-component-decorator-componentv2.md` | — |

---

## 用户故事

### US-1: @Component/@ComponentV2 声明与 build 方法

**作为** 应用开发者,
**我想要** 用 `@Component`/`@ComponentV2` 装饰 struct 声明自定义组件，通过 `build()` 方法描述 UI,
**以便** 将 UI 拆分为可复用、可组合、状态隔离的组件单元。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `@Component struct MyComp` 声明自定义组件 THEN 框架为其创建 `ViewPU` 基类实例（`pu_view.ts:59-1667`），状态隔离 | 正常 |
| AC-1.2 | WHEN `@ComponentV2 struct MyComp`（API 12+）声明 V2 自定义组件 THEN 创建 `ViewV2` 基类实例（`v2_view.ts:47-1334`），配套 V2 装饰器 | 正常 |
| AC-1.3 | WHEN 组件 `build()` 方法执行 THEN 通过 `observeComponentCreation2`（`pu_view.ts:1089-1179`）注册 elmtId 与更新函数到 `UpdateFuncRecord`（`puv2_updatefunc.ts:51-160`） | 正常 |
| AC-1.4 | WHEN 组件 build 执行 THEN `currentlyRenderedElmtIdStack_` 维护当前渲染栈，注册 `UpdateFuncRecord` 到 `updateFuncByElmtId`，注册 elmtId→View 到 `UINodeRegisterProxy.ElementIdToOwningViewPU_` | 正常 |
| AC-1.5 | WHEN 自定义组件可以嵌套使用 THEN 父组件 build 中引用子组件，子组件有独立作用域 | 正常 |

### US-2: @Entry 根组件

**作为** 应用开发者,
**我想要** 用 `@Entry` 装饰根组件,
**以便** 标记组件树的入口节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `@Entry struct MyPage` 声明根组件 THEN 该组件作为页面/组件树根节点，框架自动管理其生命周期 | 正常 |
| AC-2.2 | WHEN `@Entry` 可接收 `LocalStorage` 参数（`@Entry(storage)`）THEN 注入 LocalStorage 到组件树（详见 07-02-03 V1 应用内） | 正常 |
| AC-2.3 | WHEN `@Entry({ useSharedStorage: true })`（API 10+）THEN 通过 `getSharedLocalStorage` 跨页面共享 LocalStorage | 边界 |

### US-3: @Require 强制传参

**作为** 应用开发者,
**我想要** 用 `@Require`（API 11+）强制父组件构造时传参,
**以便** 避免运行时因缺少必传参数导致异常。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `@Require @Param var: T` 或 `@Require @State var: T` 声明 THEN 父组件必须构造时传入该参数 | 正常 |
| AC-3.2 | WHEN 父组件未传入 @Require 变量 THEN 编译报错 | 异常 |
| AC-3.3 | WHEN @Require 与 @Prop 联用（API 11+）THEN 必须父组件构造传参 | 边界 |

### US-4: 组件树构建管线

**作为** 框架维护者,
**我想要** 组件创建时经 `observeComponentCreation2` 注册 elmtId 与更新函数,
**以便** dirty 重渲染时按 elmtId 查找更新函数。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 组件创建时 `observeComponentCreation2` 执行 THEN elmtId 入 `currentlyRenderedElmtIdStack_`，注册 `UpdateFuncRecord` 到 `updateFuncByElmtId` | 正常 |
| AC-4.2 | WHEN V1 使用 `observeComponentCreation`（旧版）vs `observeComponentCreation2`（现代版）THEN 前者无 classObject，后者有 `_componentName`/`_popFunc` | 边界 |
| AC-4.3 | WHEN `UpdateFuncRecord` 持有 `updateFunc`/`classObject_`/`node` THEN 提供 `getUpdateFunc`/`getClassObject`/`getPopFunc`，If/Else 分支切换时 `isPending_`/`isChanged_` 暂存 | 正常 |

---

### US-5: 组件创建边界与异常

**作为** 应用开发者,
**我想要** 了解组件创建的边界约束与常见异常,
**以便** 避免误用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `build()` 中修改状态变量 THEN `viewPropertyHasChanged` 检测到 `isRenderInProgress` 并输出错误日志 "State variable has changed during render!" | 异常 |
| AC-5.2 | WHEN 自定义组件嵌套使用 THEN 无嵌套深度硬限制，但过深嵌套影响性能（建议合理拆分） | 边界 |
| AC-5.3 | WHEN 同一页面有多个 `@Entry` THEN 编译报错（每个页面只有一个 @Entry 根组件） | 异常 |
| AC-5.4 | WHEN `build()` 方法为空 THEN 编译报错（build 不能为空） | 异常 |
| AC-5.5 | WHEN 组件 build 中引用自身（递归）THEN 需通过条件终止（如 if/else），否则无限递归导致栈溢出 | 异常 |
| AC-5.6 | WHEN `@ComponentV2` struct 中使用 V1 状态变量装饰器（@State/@Prop/@Link）THEN V1/V2 不应混用；跨范式传递需 `enableV2Compatibility`（详见 07-02-04） | 边界 |
| AC-5.7 | WHEN `observeComponentCreation`（旧版）vs `observeComponentCreation2`（现代版）THEN 前者无 classObject，后者有 `_componentName`/`_popFunc`；新组件默认使用 observeComponentCreation2 | 边界 |
| AC-5.8 | WHEN 组件 build 完成后 THEN `currentlyRenderedElmtIdStack_` 弹出当前 elmtId；子组件先于父组件完成 build | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @Component 创建 |
| AC-1.2 | US-1 | R-1 | 单元测试 @ComponentV2 创建 |
| AC-1.3 | US-1 | R-2 | 代码审查 observeComponentCreation2 |
| AC-1.4 | US-1 | R-2 | 单元测试 elmtId 栈 |
| AC-1.5 | US-1 | R-1 | 单元测试 嵌套组件 |
| AC-2.1 | US-2 | R-3 | 单元测试 @Entry |
| AC-2.2 | US-2 | R-3 | 单元测试 @Entry(storage) |
| AC-2.3 | US-2 | R-3 | 单元测试 useSharedStorage |
| AC-3.1 | US-3 | R-4 | 单元测试 @Require |
| AC-3.2 | US-3 | R-4 | 编译期校验 |
| AC-3.3 | US-3 | R-4 | 单元测试 @Require+@Prop |
| AC-4.1 | US-4 | R-2 | 单元测试 UpdateFuncRecord 注册 |
| AC-4.2 | US-4 | R-2 | 代码审查 observeComponentCreation vs 2 |
| AC-4.3 | US-4 | R-2 | 单元测试 isPending/isChanged |
| AC-5.1 | US-5 | R-5 | 单元测试 build 中修改抛错 |
| AC-5.2 | US-5 | R-6 | 性能测试 嵌套深度 |
| AC-5.3 | US-5 | R-7 | 编译期校验 多 @Entry |
| AC-5.4 | US-5 | R-7 | 编译期校验 空 build |
| AC-5.5 | US-5 | R-6 | 单元测试 递归引用 |
| AC-5.6 | US-5 | R-8 | 编译期校验 V1/V2 混用 |
| AC-5.7 | US-5 | R-2 | 代码审查 observeComponentCreation vs 2 |
| AC-5.8 | US-5 | R-2 | 单元测试 build 完成顺序 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | @Component/@ComponentV2 声明 struct | @Component 创建 ViewPU（`pu_view.ts:59-1667`）；@ComponentV2 创建 ViewV2（`v2_view.ts:47-1334`）；状态隔离，组件可嵌套；V1/V2 共享 PUV2ViewBase（`puv2_view_base.ts:63-1517`） | @ComponentV2 API 12+ | AC-1.1~AC-1.5 |
| R-2 | 行为 | 组件创建管线 | `observeComponentCreation2`（`pu_view.ts:1089-1179`）注册 elmtId 入 `currentlyRenderedElmtIdStack_`，注册 `UpdateFuncRecord`（`puv2_updatefunc.ts:51-160`）到 `updateFuncByElmtId`，注册 elmtId→View 到 UINodeRegisterProxy；UpdateFuncRecord 持有 updateFunc/classObject_/node，If/Else 用 isPending_/isChanged_ 暂存 | observeComponentCreation（旧版无 classObject）vs observeComponentCreation2 | AC-1.3~AC-1.4, AC-4.1~AC-4.3 |
| R-3 | 行为 | @Entry 根组件 | 标记组件树入口；可接收 LocalStorage 参数注入组件树；useSharedStorage（API 10+）跨页面共享 LocalStorage | LocalStorage 详见 07-02-03 | AC-2.1~AC-2.3 |
| R-4 | 行为 | @Require（API 11+） | 强制父组件构造时传入该参数，否则编译报错；可与 @Param/@State/@Prop 联用 | API 11+ | AC-3.1~AC-3.3 |
| R-5 | 异常 | build 中修改状态变量 | `viewPropertyHasChanged` 检测到 `isRenderInProgress` 并输出错误日志 "State variable has changed during render!"；需移到事件回调/生命周期/aboutToAppear | 常见误用 | AC-5.1 |
| R-6 | 边界 | 组件嵌套与递归 | 无嵌套深度硬限制但过深影响性能；build 中引用自身需条件终止（如 if/else）否则栈溢出 | — | AC-5.2, AC-5.5 |
| R-7 | 异常 | 编译期约束 | 每页只有一个 @Entry（多 @Entry 编译报错）；build 不能为空（空 build 编译报错） | — | AC-5.3~AC-5.4 |
| R-8 | 边界 | V1/V2 范式隔离 | @ComponentV2 struct 中使用 V1 状态变量装饰器（@State/@Prop/@Link）不应混用；跨范式传递需 enableV2Compatibility（详见 07-02-04） | — | AC-5.6 |
| R-9 | 行为 | 组件作用域隔离 | 每个自定义组件有独立状态作用域；状态变量不跨组件共享（除非经 @Prop/@Link/@Provide/@Consume 同步）；build 完成后 `currentlyRenderedElmtIdStack_` 弹出当前 elmtId，子先于父完成 | — | AC-1.5, AC-5.8 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v1_tests/` @Component 创建 |
| VM-2 | AC-1.2 | 单元测试 | `v2_tests/` @ComponentV2 创建 |
| VM-3 | AC-1.3 | 代码审查 | `pu_view.ts:1089-1179` observeComponentCreation2 |
| VM-4 | AC-1.4 | 单元测试 | `common_tests/` elmtId 栈 |
| VM-5 | AC-1.5 | 单元测试 | `v1_tests/` 嵌套组件 |
| VM-6 | AC-2.1 | 单元测试 | `v1_tests/` @Entry |
| VM-7 | AC-2.2 | 单元测试 | `common_tests/` @Entry(storage) |
| VM-8 | AC-2.3 | 单元测试 | `common_tests/` useSharedStorage |
| VM-9 | AC-3.1 | 单元测试 | `v1_tests/` @Require |
| VM-10 | AC-3.2 | 编译期校验 | ArkTS 编译器 |
| VM-11 | AC-3.3 | 单元测试 | `v1_tests/` @Require+@Prop |
| VM-12 | AC-4.1 | 单元测试 | `common_tests/` UpdateFuncRecord |
| VM-13 | AC-4.2 | 代码审查 | `pu_view.ts` observeComponentCreation vs 2 |
| VM-14 | AC-4.3 | 单元测试 | `common_tests/` isPending/isChanged |
| VM-15 | AC-5.1 | 单元测试 | `v1_tests/` build 中修改抛错 |
| VM-16 | AC-5.2 | 性能测试 | 嵌套深度性能 |
| VM-17 | AC-5.3 | 编译期校验 | ArkTS 编译器 多 @Entry |
| VM-18 | AC-5.4 | 编译期校验 | ArkTS 编译器 空 build |
| VM-19 | AC-5.5 | 单元测试 | `v1_tests/` 递归引用 |
| VM-20 | AC-5.6 | 编译期校验 | ArkTS 编译器 V1/V2 混用 |
| VM-21 | AC-5.7 | 代码审查 | `pu_view.ts` observeComponentCreation vs 2 |
| VM-22 | AC-5.8 | 单元测试 | `common_tests/` build 完成顺序 |

---

## 兼容性声明

| API 版本 | 行为差异 | 迁移指导 |
|----------|----------|----------|
| API 7 | @Component/@Entry 引入 | 无需迁移 |
| API 11 | @Require 引入 | 无需迁移 |
| API 12 | @ComponentV2 引入 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 声明式 UI | @Component/@ComponentV2 装饰 struct，build() 方法描述 UI |
| 状态隔离 | 每个自定义组件有独立状态作用域 |
| V1/V2 共享 PUV2ViewBase | ViewPU（V1）与 ViewV2（V2）继承同一 PUV2ViewBase |
| 组件树管线 | observeComponentCreation2 注册 elmtId + UpdateFuncRecord |
| build 中禁修改状态 | build 中修改状态变量抛错（isRenderInProgress 检测） |
| V1/V2 范式隔离 | @ComponentV2 中不应使用 V1 状态变量装饰器 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 组件创建/注册无额外开销；UpdateFuncRecord 查询为 O(1) Map 查找；嵌套过深影响性能（建议合理拆分） |
| 可调试性 | `this.debugInfoViewHierarchy(true)` 输出组件树；`this.debugInfoUpdateFuncByElmtId(true)` 输出更新函数；DFX trace 含组件名/elmtId |
| 可观测性 | `hidumper -s WindowManagerService -a "-viewHierarchy"` 查询组件树；Inspector 显示组件结构 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 状态管理 | 组件是状态变量的载体；状态变量行为详见 07-02 状态管理 |
| 生命周期 | 组件创建/销毁触发生命周期回调（07-03-02） |
| 复用 | 组件可被 @Reusable/@ReusableV2 标记为可复用（07-03-03） |
| 冻结 | 组件可配置 freezeWhenInactive 冻结（07-03-04） |
| 渲染控制 | build() 方法中使用 if/else/ForEach/LazyForEach/Repeat（07-05） |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 标准组件创建 | — | 单元测试 | — |
| 平板 | Split 模式下组件可跨分屏 | 组件树适配 | 单元测试 | — |
| 折叠屏 | 折叠/展开时组件重建 | — | 单元测试 | — |
| 穿戴 | 小屏场景组件一致 | — | 单元测试 | — |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC
- [x] 规则编号连续且可追溯到源码
- [x] 所有源码引用包含 file 信息

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:59-1667` | `ViewPU` V1 视图基类 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:1089-1179` | `observeComponentCreation2` 组件创建 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_view.ts:47-1334` | `ViewV2` V2 视图基类 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts:63-1517` | `PUV2ViewBase` V1/V2 共享 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_updatefunc.ts:51-160` | `UpdateFuncRecord` 更新函数记录 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-create-custom-components.md` | 创建自定义组件 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-custom-component-decorator-component.md` | @Component API 参考 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-custom-component-decorator-componentv2.md` | @ComponentV2 API 参考 |
