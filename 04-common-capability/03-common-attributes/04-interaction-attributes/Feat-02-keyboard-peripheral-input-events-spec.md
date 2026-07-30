# 特性规格

> Func-04-03-04-Feat-02 固化通用组件的键盘、预输入法、轴事件、焦点轴和数字表冠回调契约。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 键盘与外设输入事件 |
| 特性编号 | Func-04-03-04-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起，扩展至 API 18 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 键盘与外设输入规格 | 补录既有 CommonMethod 回调。 |

## 输入文档

- `design.md`
- `interface/sdk-js/api/@internal/component/ets/common.d.ts:20293-20383`
- `interface/sdk-js/api/arkui/component/common.static.d.ets:12175-12225`
- `frameworks/core/components_ng/base/view_abstract.cpp:3329-3333,10224-10243`

## 用户故事

### US-1: 接收键盘和输入法前事件

作为应用开发者，我想要注册键盘与预输入法回调，以便消费或观察组件获得焦点后的按键输入。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 动态前端设置 API 7 `onKeyEvent` 普通回调 THEN SDK 使用 `KeyEvent => void` 签名。 | 正常 |
| AC-1.2 | WHEN 设置 API 15 `onKeyEvent` 消费型重载、`onKeyPreIme` 或 `onKeyEventDispatch` THEN 回调返回 boolean 并由 ViewAbstract 写入 FocusHub。 | 正常 |
| AC-1.3 | WHEN 静态前端设置 onKeyEvent THEN 使用其声明的消费型 `Callback<KeyEvent, boolean>`；不得将动态普通重载假定为静态契约。 | 边界 |

### US-2: 接收外设轴和表冠输入

作为外设应用开发者，我想要监听轴、焦点轴和数字表冠输入，以便按设备输入类型响应。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `onFocusAxisEvent` 或 `onAxisEvent` THEN SDK 分别使用 API 15/17 的 callback 类型。 | 正常 |
| AC-2.2 | WHEN 设置 `onDigitalCrown` THEN SDK 使用 API 18 的 Optional CrownEvent callback。 | 正常 |
| AC-2.3 | WHEN 设备未产生相应外设输入 THEN 注册不合成事件或改变焦点状态。 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-2 | SDK 审查 | `common.d.ts:20293` |
| AC-1.2 | R-2 | TASK-2 | 源码审查 | `view_abstract.cpp:3329-3333,10231-10243` |
| AC-1.3 | R-3 | TASK-2 | SDK 对照 | `common.static.d.ets:12175` |
| AC-2.1 | R-4 | TASK-2 | SDK 审查 | `common.d.ts:20371-20383` |
| AC-2.2 | R-5 | TASK-2 | SDK 审查 | `common.d.ts:20323` |
| AC-2.3 | R-6 | TASK-2 | 设备测试 | SDK 事件模型 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 动态 API 7 onKeyEvent 普通重载 | 回调接收 KeyEvent，不要求消费返回值 | 仅动态 SDK 声明 | AC-1.1 |
| R-2 | 行为 | 消费型 key/pre-IME/dispatch 回调有效 | ViewAbstract 获取 FocusHub 并保存回调 | boolean 用于回调契约 | AC-1.2 |
| R-3 | 边界 | 静态 onKeyEvent | 使用静态消费型签名 | 与动态普通重载不同 | AC-1.3 |
| R-4 | 行为 | 设置 focus-axis/axis 回调 | 注册 SDK 定义的外设回调 | since 分别为 15/17 | AC-2.1 |
| R-5 | 行为 | 设置数字表冠回调 | 使用 API 18 Optional callback | 无表冠设备不产生该输入 | AC-2.2 |
| R-6 | 边界 | 无对应外设输入 | 不凭注册主动触发回调 | 系统设备能力为外部输入 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3 | SDK/源码审查 | 动态/静态 onKeyEvent 差异和 FocusHub 路径。 |
| VM-2 | AC-2.1~2.3 | SDK/设备测试 | API since 和外设存在性边界。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `onKeyEvent/onKeyPreIme/onKeyEventDispatch` | Public | KeyEvent callback | 链式值 | N/A | 键盘/IME 回调 | AC-1.1~1.3 |
| `onFocusAxisEvent/onAxisEvent/onDigitalCrown` | Public | 外设事件 callback | 链式值 | N/A | 外设输入回调 | AC-2.1~2.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `onKeyEvent` | 变更 | API 15 增加消费型重载 | 静态使用消费型签名；动态按目标 API 选择重载 | AC-1.1~1.3 |
| `onDigitalCrown` | 变更 | API 18 新增 | 低版本不调用 | AC-2.2 |

## 接口规格

### 接口定义

**Keyboard callbacks**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onKeyEvent(callback)`、`onKeyPreIme(callback)`、`onKeyEventDispatch(callback)` |
| 返回值 | 动态 `T`；静态 `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.3 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | `Callback<KeyEvent, boolean>` 或动态普通 callback | 是 | 无 | 以 SDK 的 API 版本和前端形态为准。 |

**Peripheral callbacks**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onFocusAxisEvent`、`onAxisEvent`、`onDigitalCrown` |
| 返回值 | 链式值 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.3 |

## 兼容性声明

- **已有 API 行为变更:** 无；本文件补录已有行为。
- **配置文件格式变更:** 无。
- **数据存储格式变更:** 无。
- **最低支持版本:** Key API 7；pre-IME 12；dispatch/focus-axis 15；axis 17；digital crown 18。
- **API 版本号策略:** 静态和动态声明分别记录，不相互推断。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| FocusHub 归属 | 键盘和 dispatch 回调通过 FocusHub 保存 | AC-1.2 |
| 焦点前置 | 系统键盘分发依赖组件实际焦点状态 | AC-1.1~1.3 |
| 设备输入 | 轴/表冠事件依赖硬件和系统派发 | AC-2.1~2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 所有 API 具备 SDK/实现定位 | 静态审查 | 输入文档 |
| 兼容性 | 版本和前端差异显式声明 | SDK 对照 | `common*.d.ts` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 主要为软/硬键盘，通常无表冠 | API 保持一致 | 设备测试 | SDK 契约 |
| 平板 | 可能连接键盘或轴设备 | API 保持一致 | 设备测试 | SDK 契约 |
| 可穿戴 | 可产生数字表冠 | 仅 API 18+ 调用 | 设备测试 | SDK 契约 |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|------|------|------|----------|
| 无障碍 | 是 | 不改变既有键盘辅助行为 | AC-1.1 |
| 多窗口/分屏 | 是 | 焦点属于当前容器 | AC-1.2 |
| 版本升级 | 是 | 按 since 判断外设 API | AC-2.1, AC-2.2 |
| 深色模式 | 否 | 不影响输入路由 | 全部 |

## 行为场景（可选，Gherkin）

L1 规格已由接口行为表覆盖。

## Spec 自审清单

- [x] 无待定、TBD 或 TODO 占位符
- [x] 所有 AC 使用 WHEN/THEN 格式且可测试
- [x] 范围边界明确
- [x] 每条规则关联 AC
- [x] 规则具备可复现触发条件和可观察结果

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "CommonMethod keyboard pre-IME dispatch axis digital crown callbacks and FocusHub routing"
```
