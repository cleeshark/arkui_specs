# 特性规格

> Func-07-02-03-Feat-04 Environment 设备环境变量：固化 `Environment`（`sdk/environment.ts:23-197`，单例）的 6 个固定 key（`accessibilityEnabled`/`colorMode`/`fontScale`/`fontWeightScale`/`layoutDirection`/`languageCode`）、`envProp`→`AppStorage.setAndProp` 扇出、`onValueChanged`→`AppStorage.set` 扇出、单向语义（Environment → AppStorage → Component）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Environment 设备环境变量 |
| 特性编号 | Func-07-02-03-Feat-04 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | 大写 API（`EnvProp`/`EnvProps`/`Keys`）API 7 起 API 10 废弃；小写 API 10 起；`LayoutDirection.Auto` API 8 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 低 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| Environment | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/environment.ts` | — |
| Environment 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-environment.md` | — |
| 内置环境变量 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-environment-variables.md` | — |
| V1 应用级变量 API | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management.md` | — |

---

## 用户故事

### US-1: Environment 单例与 6 固定 key

**作为** 应用开发者,
**我想要** 用 Environment 单例查询设备环境变量,
**以便** 响应系统配置变化（颜色模式、字体大小等）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 应用启动 THEN 框架创建 Environment 单例（`environment.ts:23-197`），所有属性为不可变简单类型 | 正常 |
| AC-1.2 | WHEN Environment 6 固定 key THEN `accessibilityEnabled`(string)、`colorMode`(ColorMode)、`fontScale`(number)、`fontWeightScale`(number)、`layoutDirection`(LayoutDirection)、`languageCode`(string) | 正常 |
| AC-1.3 | WHEN `colorMode` 取值 THEN `LIGHT=0`/`DARK=1` | 正常 |
| AC-1.4 | WHEN `layoutDirection` 取值 THEN `LTR=0`/`RTL=1`/`Auto=2`（API 8+） | 正常 |

### US-2: envProp 扇出与单向语义

**作为** 应用开发者,
**我想要** 用 `envProp` 将环境变量写入 AppStorage,
**以便** 组件通过 @StorageProp 单向读取。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `envProp<S>(key, value)`(68-70，API 10+) THEN `envProp` 实例方法(118-158) 按开关查 6 固定 key 后端值，写入 AppStorage（`AppStorage.setAndProp` 扇出） | 正常 |
| AC-2.2 | WHEN 系统中查不到 key 值 THEN 用 `value` 作为默认值 | 正常 |
| AC-2.3 | WHEN AppStorage 已有同 key THEN `envProp` 返回 false 且不写入 | 边界 |
| AC-2.4 | WHEN Environment 与 UIContext 关联 THEN 必须在 UIContext 明确时才能调用（可用 `uiContext.runScopedTask`） | 边界 |
| AC-2.5 | WHEN 组件读取环境变量 THEN 应用 `@StorageProp`（单向），应用无法修改环境变量 | 边界 |

### US-3: envProps 批量与 onValueChanged 扇出

**作为** 应用开发者,
**我想要** 用 `envProps` 批量注入环境变量，并响应系统配置变化,
**以便** 在系统配置变化时自动刷新 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `envProps(props)`(80-86，API 10+) THEN 批量注入（`EnvPropsOptions` 数组） | 正常 |
| AC-3.2 | WHEN 系统环境变量变化 THEN `onValueChanged(key, value)`(183-190) 触发 → `AppStorage.set` 扇出到所有 @StorageProp | 正常 |
| AC-3.3 | WHEN `keys()`(100-102，API 10+) THEN 返回所有环境变量 key | 正常 |
| AC-3.4 | WHEN 未调 `envProp` 直接用 AppStorage 读环境变量 THEN 无法获取值；建议应用启动时调用 | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 单例创建 |
| AC-1.2 | US-1 | R-2 | 单元测试 6 固定 key |
| AC-1.3 | US-1 | R-2 | 单元测试 colorMode |
| AC-1.4 | US-1 | R-2 | 单元测试 layoutDirection |
| AC-2.1 | US-2 | R-3 | 单元测试 envProp 扇出 |
| AC-2.2 | US-2 | R-3 | 单元测试 默认值 |
| AC-2.3 | US-2 | R-3 | 单元测试 已有 key 返回 false |
| AC-2.4 | US-2 | R-4 | 单元测试 UIContext 关联 |
| AC-2.5 | US-2 | R-3 | 单元测试 单向 @StorageProp |
| AC-3.1 | US-3 | R-5 | 单元测试 envProps |
| AC-3.2 | US-3 | R-3 | 单元测试 onValueChanged 扇出 |
| AC-3.3 | US-3 | R-5 | 单元测试 keys |
| AC-3.4 | US-3 | R-4 | 单元测试 未调 envProp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Environment 单例 | 应用启动时框架创建单例（`environment.ts:23-197`），所有属性为不可变简单类型 | 与 UIContext 关联 | AC-1.1 |
| R-2 | 行为 | 6 固定 key | `accessibilityEnabled`(string)、`colorMode`(ColorMode `LIGHT=0`/`DARK=1`)、`fontScale`(number)、`fontWeightScale`(number)、`layoutDirection`(LayoutDirection `LTR=0`/`RTL=1`/`Auto=2` API 8+)、`languageCode`(string) | 内置环境变量 | AC-1.2~AC-1.4 |
| R-3 | 行为 | `envProp<S>(key, value)`(68-70/118-158，API 10+) / `onValueChanged`(183-190) | `envProp` 按开关查 6 固定 key 后端值，写入 `AppStorage.setAndProp` 扇出；查不到用 `value` 默认；AppStorage 已有同 key 返回 false；系统变化 `onValueChanged` → `AppStorage.set` 扇出；单向（Environment → AppStorage → Component，应用无法修改，组件用 @StorageProp 单向读取） | 单向流 | AC-2.1~AC-2.3, AC-2.5, AC-3.2 |
| R-4 | 边界 | UIContext 关联与调用时机 | Environment 与 UIContext 关联，必须 UIContext 明确时才能调用（`uiContext.runScopedTask`）；未调 envProp 直接用 AppStorage 读环境变量无法获取值；建议应用启动时调用 | — | AC-2.4, AC-3.4 |
| R-5 | 行为 | `envProps(props)`(80-86，API 10+) / `keys()`(100-102) | `envProps` 批量注入；`keys` 返回所有环境变量 key | — | AC-3.1, AC-3.3 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 代码审查 | `environment.ts:23-197` 单例 |
| VM-2 | AC-1.2 | 单元测试 | `common_tests/` 6 固定 key |
| VM-3 | AC-1.3 | 单元测试 | `common_tests/` colorMode |
| VM-4 | AC-1.4 | 单元测试 | `common_tests/` layoutDirection |
| VM-5 | AC-2.1 | 单元测试 | `common_tests/` envProp 扇出 |
| VM-6 | AC-2.2 | 单元测试 | `common_tests/` 默认值 |
| VM-7 | AC-2.3 | 单元测试 | `common_tests/` 已有 key 返回 false |
| VM-8 | AC-2.4 | 单元测试 | `common_tests/` UIContext 关联 |
| VM-9 | AC-2.5 | 单元测试 | `common_tests/` 单向 @StorageProp |
| VM-10 | AC-3.1 | 单元测试 | `common_tests/` envProps |
| VM-11 | AC-3.2 | 单元测试 | `common_tests/` onValueChanged 扇出 |
| VM-12 | AC-3.3 | 单元测试 | `common_tests/` keys |
| VM-13 | AC-3.4 | 单元测试 | `common_tests/` 未调 envProp |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `Environment` | `sdk/environment.ts:23-197` | 设备环境单例 |
| `envProp`（实例） | `sdk/environment.ts:118-158` | 按 6 固定 key 查后端，扇出 AppStorage |
| `envProps` | `sdk/environment.ts:80-86/160-168` | 批量注入 |
| `onValueChanged` | `sdk/environment.ts:183-190` | 系统变化 → AppStorage.set 扇出 |
| `keys` | `sdk/environment.ts:100-102/170-181` | 查询所有 key |
| `configureBackend` | `sdk/environment.ts:38-40` | 配置 IEnvironmentBackend |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | 大写 API（EnvProp/EnvProps/Keys）+ 内置环境变量 ColorMode/LayoutDirection 引入 | 设备环境 | 无需迁移 |
| API 8 | `LayoutDirection.Auto=2` 新增 | 布局方向扩展 | 无需迁移 |
| API 10 | 小写 API 引入（大写废弃） | API 风格统一 | 改用小写 API |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 单例 | Environment 是应用启动时框架创建的单例，与 UIContext 关联 |
| 单向流 | Environment → AppStorage → Component；应用无法修改环境变量，组件用 @StorageProp 单向读取 |
| 6 固定 key | 仅支持 6 个固定 key，不支持自定义环境变量 |
| 扇出经 AppStorage | envProp → AppStorage.setAndProp；onValueChanged → AppStorage.set |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/environment.ts:23-197` | `Environment` 设备环境单例 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/environment.ts:118-158` | `envProp` 实例方法（按 6 固定 key 开关） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/environment.ts:183-190` | `onValueChanged` 系统变化扇出 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | Environment 行为回归测试 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/env_tests/` | Environment/@Env 相关测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-environment.md` | Environment 指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-environment-variables.md` | 内置环境变量 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management.md` | V1 应用级变量 API 参考 |
