# 特性规格

> Func-07-02-01-Feat-04 @Provide/@Consume 跨层级同步：固化 `@Provide`（祖先注册，= `@State` + `addProvidedVar`）、`@Consume`（后代双向同步，经 `initializeConsume` 创建 `SynchedPropertyTwoWayPU`）、`findProvidePU__` 递归祖先链查找、别名与 `allowOverride` 冲突检测、BuildNode 复用重连三件套（`reconnectToConsume`/`disconnectedConsume`/`reInitializeConsume`）、API 20+ @Consume 默认值与跨 BuilderNode 配对行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @Provide/@Consume 跨层级同步 |
| 特性编号 | Func-07-02-01-Feat-04 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起支持；别名参数 API 9 起；`allowOverride`/Date 类型 API 11 起；Map/Set/联合类型 API 11 起；@Consume 默认值/跨 BuilderNode 配对 API 20 起；@Provide 重复 key 错误码 140114/@Consume 缺 @Provide 错误码 140112/Function ERROR API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| ViewPU（@Provide/@Consume 注册） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts` | — |
| SynchedPropertyTwoWayPU（@Consume 实现） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_two_way.ts` | — |
| @Provide/@Consume 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-provide-and-consume.md` | — |
| @Provide API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-provide.md` | — |
| @Consume API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-consume.md` | — |
| 状态管理错误码 | `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | — |

---

## 用户故事

### US-1: @Provide 祖先注册

**作为** 应用开发者,
**我想要** 用 `@Provide` 在祖先组件声明状态变量并向所有后代组件暴露,
**以便** 后代组件无需逐层传递即可通过 @Consume 获取该状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 祖先组件声明 `@Provide var: T = init` THEN 框架创建 `ObservedPropertyPU<T>` 包装变量，并经 `ViewPU.addProvidedVar`（`pu_view.ts:867-873`）将其注册到该组件的 provided 变量表 | 正常 |
| AC-1.2 | WHEN @Provide 注册时 THEN 同时保存变量名与别名（若提供）；后代 @Consume 匹配时任一一致即绑定 | 正常 |
| AC-1.3 | WHEN @Provide 变量变化 THEN 遍历更新依赖的系统组件（elmtId）和所有 @Consume 变量 | 正常 |
| AC-1.4 | WHEN @Provide 必须定义本地默认值 THEN 可从父组件传入非 `undefined` 类型变量（仅作初始值，后续不同步）；传入 `undefined` 时使用本地默认值 | 边界 |

### US-2: @Consume 递归查找与双向同步

**作为** 应用开发者,
**我想要** 用 `@Consume` 在后代组件声明变量，自动向上递归查找祖先的 @Provide 并建立双向同步,
**以便** 跨层级共享状态，无需逐层 props 传递。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 后代组件声明 `@Consume var: T` THEN 经 `ViewPU.initializeConsume`（`pu_view.ts:896-921`）创建 `SynchedPropertyTwoWayPU`，内部调用 `createSync`（line 916） | 正常 |
| AC-2.2 | WHEN @Consume 查找 @Provide THEN `findProvidePU__`（`pu_view.ts:879-883`）递归搜索：self → `parent_` → `__parentViewBuildNode__` | 正常 |
| AC-2.3 | WHEN @Consume 匹配到 @Provide THEN 优先以别名匹配，无别名则用变量名；建立祖先↔后代双向同步 | 正常 |
| AC-2.4 | WHEN @Consume 变量变化 THEN 调用 @Provide 的更新方法将数值同步回 @Provide | 正常 |
| AC-2.5 | WHEN API 20 前 @Consume 查找不到 @Provide THEN 抛 JS ERROR | 异常 |
| AC-2.6 | WHEN @Consume 在构造参数中传入初始化 THEN 编译期报错，不能在构造参数中传入初始化 | 异常 |

### US-3: 别名机制与冲突检测

**作为** 应用开发者,
**我想要** 用别名区分同名 @Provide，并防止祖先链重复定义,
**以便** 灵活命名并避免冲突。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN @Provide 提供别名参数（`@Provide('myKey') var: T`）THEN 后代 @Consume 用同别名匹配 | 正常 |
| AC-3.2 | WHEN @Provide 使用 `ProvideOptions`（`allowOverride`，API 11+）THEN 允许重写同名 @Provide（覆盖祖先） | 正常 |
| AC-3.3 | WHEN 祖先链上存在重复 key 的 @Provide 且未设置 `allowOverride` THEN 运行时错误；API 23+ 返回错误码 140114 | 异常 |
| AC-3.4 | WHEN @Provide/@Consume 参数 key 非 string 类型 THEN 编译期报错 | 异常 |

### US-4: BuildNode 复用重连

**作为** 框架维护者,
**我想要** BuildNode 复用时 @Consume 正确重连 @Provide,
**以便** 复用组件的跨层级同步正确恢复。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN BuildNode 挂载时 THEN `reconnectToConsume` 查找真实 @Provide 并建立连接 | 正常 |
| AC-4.2 | WHEN BuildNode 脱离/找不到 @Provide 时 THEN `disconnectedConsume` 兜底使用默认值 | 正常 |
| AC-4.3 | WHEN 全局复用场景 THEN `reInitializeConsume` 全量重初始化 @Consume 连接 | 正常 |

### US-5: @Consume 默认值与跨 BuilderNode（API 20+）

**作为** 应用开发者,
**我想要** API 20+ 为 @Consume 设置默认值，并支持跨 BuilderNode 配对,
**以便** 在 @Provide 缺失时优雅降级，且支持更灵活的组件树结构。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN API 20+ @Consume 设置默认值且匹配到 @Provide THEN 优先用 @Provide 值 | 正常 |
| AC-5.2 | WHEN API 20+ @Consume 设置默认值且未匹配到 @Provide THEN 用默认值创建临时数据源，不抛错 | 正常 |
| AC-5.3 | WHEN API 20+ 跨 BuilderNode 配对（配置 `enableProvideConsumeCrossing: true`）THEN BuilderNode 内 @Consume 需设置默认值；上树后向上查找 @Provide 建立双向同步 | 正常 |
| AC-5.4 | WHEN 跨 BuilderNode 配对类型不一致 THEN 运行时错误（包括类实例构造函数不同的判断） | 异常 |
| AC-5.5 | WHEN BuilderNode 下树后 THEN @Consume 断开与 @Provide 连接并恢复默认值；若值有变化则回调 @Watch 方法 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @Provide 注册 |
| AC-1.2 | US-1 | R-2 | 单元测试 变量名/别名保存 |
| AC-1.3 | US-1 | R-3 | 单元测试 @Provide 变化通知 |
| AC-1.4 | US-1 | R-1 | 单元测试 本地默认值 |
| AC-2.1 | US-2 | R-4 | 单元测试 initializeConsume |
| AC-2.2 | US-2 | R-5 | 单元测试 findProvidePU__ 递归 |
| AC-2.3 | US-2 | R-2 | 单元测试 别名/变量名匹配 |
| AC-2.4 | US-2 | R-4 | 单元测试 @Consume→@Provide 同步 |
| AC-2.5 | US-2 | R-6 | 单元测试 缺 @Provide 抛错 |
| AC-2.6 | US-2 | R-7 | 编译期校验 |
| AC-3.1 | US-3 | R-2 | 单元测试 别名匹配 |
| AC-3.2 | US-3 | R-8 | 单元测试 allowOverride |
| AC-3.3 | US-3 | R-9 | 单元测试 重复 key 错误 |
| AC-3.4 | US-3 | R-10 | 编译期校验 |
| AC-4.1 | US-4 | R-11 | 单元测试 reconnectToConsume |
| AC-4.2 | US-4 | R-11 | 单元测试 disconnectedConsume |
| AC-4.3 | US-4 | R-11 | 单元测试 reInitializeConsume |
| AC-5.1 | US-5 | R-12 | 单元测试 @Provide 优先 |
| AC-5.2 | US-5 | R-12 | 单元测试 默认值降级 |
| AC-5.3 | US-5 | R-13 | 单元测试 跨 BuilderNode |
| AC-5.4 | US-5 | R-14 | 单元测试 类型不一致错误 |
| AC-5.5 | US-5 | R-13 | 单元测试 下树恢复默认值 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 祖先组件声明 `@Provide var: T = init` | 创建 `ObservedPropertyPU<T>` 包装变量，经 `ViewPU.addProvidedVar`（`pu_view.ts:867-873`）注册到 provided 变量表；@Provide 必须定义本地默认值；父组件传入非 `undefined` 仅作初始值，后续不同步 | = @State + addProvidedVar | AC-1.1, AC-1.4 |
| R-2 | 行为 | @Provide 注册 / @Consume 匹配 | @Provide 同时保存变量名与别名；@Consume 优先以别名匹配，无别名则用变量名；任一一致即绑定 | 别名参数为 string | AC-1.2, AC-2.3, AC-3.1 |
| R-3 | 行为 | @Provide 变量变化 | 遍历更新依赖的系统组件（elmtId）和所有 @Consume 变量 | — | AC-1.3 |
| R-4 | 行为 | 后代组件声明 `@Consume var: T` | `ViewPU.initializeConsume`（`pu_view.ts:896-921`）创建 `SynchedPropertyTwoWayPU`，调用 `createSync`（line 916）；@Consume 变量变化时调用 @Provide 更新方法同步回 @Provide；祖先↔后代双向同步 | @Consume 复用 @Link 双向同步机制（Feat-03 R-7） | AC-2.1, AC-2.4 |
| R-5 | 行为 | @Consume 查找 @Provide | `findProvidePU__`（`pu_view.ts:879-883`）递归搜索：self → `parent_` → `__parentViewBuildNode__` | 祖先链断裂则找不到 | AC-2.2 |
| R-6 | 异常 | API 20 前 @Consume 查找不到 @Provide | 抛 JS ERROR；API 23+ 返回错误码 140112（`@Consume missing @Provide property with name or default value`） | API 20+ 有默认值则降级 | AC-2.5 |
| R-7 | 异常 | @Consume 在构造参数中传入初始化 | 编译期报错，不能在构造参数中传入初始化 | — | AC-2.6 |
| R-8 | 行为 | @Provide 使用 `ProvideOptions`（`allowOverride`，API 11+） | 允许重写同名 @Provide，覆盖祖先链上的同名 @Provide | allowOverride 为 API 11+ | AC-3.2 |
| R-9 | 异常 | 祖先链存在重复 key @Provide 且未设置 `allowOverride` | 运行时错误；API 23+ 返回错误码 140114（`duplicate @Provide property`） | `addProvidedVar` 递归检查祖先链防冲突 | AC-3.3 |
| R-10 | 异常 | @Provide/@Consume 参数 key 非 string 类型 | 编译期报错 | key 必须 string | AC-3.4 |
| R-11 | 行为 | BuildNode 复用 @Consume 重连 | `reconnectToConsume`（挂载时找真实 @Provide）、`disconnectedConsume`（脱离/找不到时兜底默认值）、`reInitializeConsume`（全局复用时全量重初始化）三件套协同 | 与 @Link 复用重连（Feat-03 R-14）协同 | AC-4.1~AC-4.3 |
| R-12 | 行为 | API 20+ @Consume 设置默认值 | 匹配到 @Provide 优先用 @Provide 值；未匹配用默认值创建临时数据源，不抛错 | API 20+ | AC-5.1, AC-5.2 |
| R-13 | 行为 | API 20+ 跨 BuilderNode 配对 | 配置 `enableProvideConsumeCrossing: true`；BuilderNode 上树前构造节点，内 @Consume 需设默认值；上树后向上查找 @Provide 建立双向同步；BuilderNode 下树后 @Consume 断开并恢复默认值，值有变化则回调 @Watch | API 20+ | AC-5.3, AC-5.5 |
| R-14 | 异常 | 跨 BuilderNode 配对类型不一致 | 运行时错误（包括类实例构造函数不同的判断） | 类型必须严格一致 | AC-5.4 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v1_tests/` @Provide 注册 |
| VM-2 | AC-1.2 | 单元测试 | `v1_tests/` 变量名/别名保存 |
| VM-3 | AC-1.3 | 单元测试 | `v1_tests/` @Provide 变化通知 |
| VM-4 | AC-1.4 | 单元测试 | `v1_tests/` 本地默认值 |
| VM-5 | AC-2.1 | 单元测试 | `v1_tests/` initializeConsume |
| VM-6 | AC-2.2 | 代码审查 | `pu_view.ts:879-883` findProvidePU__ 递归 |
| VM-7 | AC-2.3 | 单元测试 | `v1_tests/` 别名/变量名匹配 |
| VM-8 | AC-2.4 | 单元测试 | `v1_tests/` @Consume→@Provide 同步 |
| VM-9 | AC-2.5 | 单元测试 | `v1_tests/` 缺 @Provide 抛错 |
| VM-10 | AC-2.6 | 编译期校验 | ArkTS 编译器 构造参数初始化拒绝 |
| VM-11 | AC-3.1 | 单元测试 | `v1_tests/` 别名匹配 |
| VM-12 | AC-3.2 | 单元测试 | `v1_tests/` allowOverride |
| VM-13 | AC-3.3 | 单元测试 | `v1_tests/` 重复 key 错误码 140114 |
| VM-14 | AC-3.4 | 编译期校验 | ArkTS 编译器 key 类型校验 |
| VM-15 | AC-4.1 | 单元测试 | `v1_tests/` reconnectToConsume |
| VM-16 | AC-4.2 | 单元测试 | `v1_tests/` disconnectedConsume |
| VM-17 | AC-4.3 | 单元测试 | `v1_tests/` reInitializeConsume |
| VM-18 | AC-5.1 | 单元测试 | `v1_tests/` @Provide 优先 |
| VM-19 | AC-5.2 | 单元测试 | `v1_tests/` 默认值降级 |
| VM-20 | AC-5.3 | 单元测试 | `v1_tests/` 跨 BuilderNode |
| VM-21 | AC-5.4 | 单元测试 | `v1_tests/` 类型不一致错误 |
| VM-22 | AC-5.5 | 单元测试 | `v1_tests/` 下树恢复默认值 |

---

## 错误码规格

| 错误码 | 触发条件 | 错误信息 | 起始版本 |
|--------|----------|----------|----------|
| 140112 | @Consume 缺失对应的 @Provide（无默认值时） | `@Consume missing @Provide property with name or default value. Fail to resolve @Consume.` | API 23 |
| 140114 | 声明重复 key 的 @Provide（未设置 allowOverride） | `duplicate @Provide property. Property with this name is provided by one of the ancestor Views already.` | API 23 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `addProvidedVar<T>()` | `pu_view.ts:867-873` | @Provide 注册到组件 provided 变量表，递归检查祖先链防冲突 |
| `findProvidePU__()` | `pu_view.ts:879-883` | @Consume 递归查找 @Provide（self→parent→BuildNode） |
| `initializeConsume<T>()` | `pu_view.ts:896-921` | @Consume 初始化，调用 `createSync`（line 916）创建 `SynchedPropertyTwoWayPU` |
| `reconnectToConsume`/`disconnectedConsume`/`reInitializeConsume` | `pu_view.ts` | BuildNode 复用 @Consume 重连三件套 |
| `SynchedPropertyTwoWayPU<C>` | `pu_synced_property_two_way.ts:23-292` | @Consume 双向同步实现（复用 @Link 机制） |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | @Provide/@Consume 引入，祖先↔后代跨层级双向同步 | 跨层级状态共享 | 无需迁移 |
| API 9 | 别名参数支持（`@Provide('key')`/`@Consume('key')`） | 别名命名 | 无需迁移 |
| API 10 | 新增 `Date` 类型支持 | Date 跨层级同步 | 无需迁移 |
| API 11 | 新增 `Map`/`Set`/联合类型；`ProvideOptions.allowOverride` | 允许重写同名 @Provide | 无需迁移 |
| API 20 | @Consume 支持默认值；跨 BuilderNode 配对（`enableProvideConsumeCrossing`） | @Consume 优雅降级 + 跨树配对 | 无需迁移 |
| API 23 | @Provide 重复 key 返回错误码 140114；@Consume 缺 @Provide 返回错误码 140112；Function 编译期 ERROR | 错误码规范化 | 处理新增错误码 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 跨层级双向 | @Provide/@Consume 建立祖先↔后代双向同步，通过变量名或别名绑定；无需逐层 props 传递 |
| 祖先链递归查找 | `findProvidePU__` 递归 self→parent→BuildNode；祖先链断裂则找不到 |
| 冲突检测 | `addProvidedVar` 递归检查祖先链防重复 key；`allowOverride`（API 11+）允许覆盖 |
| BuildNode 复用重连 | `reconnectToConsume`/`disconnectedConsume`/`reInitializeConsume` 三件套保证复用时跨层级同步正确恢复 |
| @Consume 复用 @Link 机制 | @Consume 经 `initializeConsume` 创建 `SynchedPropertyTwoWayPU`，复用 @Link 的双向同步与防循环机制（Feat-03） |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | `findProvidePU__` 递归祖先链查找，深度取决于组件树层级；@Provide 变化时遍历所有 @Consume 订阅者 |
| 可调试性 | 断点建议：`addProvidedVar`、`findProvidePU__`、`initializeConsume`、`reconnectToConsume`；日志关键字：`@Consume`、`@Provide` |
| 可观测性 | `hidumper -s WindowManagerService -a "-stateVariables -viewId=N"` 查询 @Provide/@Consume 配对状态 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 跨层级状态共享 | @Provide/@Consume 是 ArkUI 跨层级状态共享的核心机制，避免 prop drilling |
| 组件复用协同 | BuildNode 复用时 @Consume 经重连三件套恢复跨层级同步（与 @Link 复用重连协同，Feat-03） |
| V2 对比 | V2 的 `@Provider`/`@Consumer`（07-02-04）采用弱引用 + `connectConsumer2Provider`，语义类似但实现不同 |
| @Watch 监听基础 | @Provide/@Consume 变量可叠加 @Watch 装饰器监听变化回调（Feat-06）；跨 BuilderNode 下树恢复默认值时若值有变化也回调 @Watch |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:867-873` | `addProvidedVar` @Provide 注册 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:879-883` | `findProvidePU__` 递归查找 @Provide |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:896-921` | `initializeConsume` @Consume 初始化（调用 `createSync` line 916） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts` | `reconnectToConsume`/`disconnectedConsume`/`reInitializeConsume` BuildNode 复用重连三件套 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_two_way.ts:23-292` | `SynchedPropertyTwoWayPU` @Consume 双向同步实现（复用 @Link 机制） |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` | @Provide/@Consume 注册、查找、双向同步、复用重连回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-provide-and-consume.md` | @Provide/@Consume 开发指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-provide.md` | @Provide API 参考 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-consume.md` | @Consume API 参考 |
| `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | 错误码 140112/140114 |
