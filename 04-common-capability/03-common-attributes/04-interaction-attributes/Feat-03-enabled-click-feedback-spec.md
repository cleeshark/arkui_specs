# 特性规格

> Func-04-03-04-Feat-03 固化 `enabled`、`clickEffect` 与点击声音反馈的通用组件行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组件可用性与点击反馈 |
| 特性编号 | Func-04-03-04-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起，扩展至 API 24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | enabled 与点击反馈规格 | 补录既有实现。 |

## 输入文档

- `design.md`
- `interface/sdk-js/api/@internal/component/ets/common.d.ts:22281-22430`
- `interface/sdk-js/api/arkui/component/common.static.d.ets:13025-13095`
- `frameworks/core/components_ng/base/view_abstract.cpp:3255-3267,10002-10021`

## 用户故事

### US-1: 控制组件可用性

作为应用开发者，我想要设置组件 enabled 状态，以便统一控制事件和焦点参与。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `enabled(true|false)` THEN ViewAbstract 将值先写入 EventHub，再写入 FocusHub。 | 正常 |
| AC-1.2 | WHEN `enabled(false)` THEN 本特性不只描述点击效果；事件和焦点 Hub 均接收 false。 | 边界 |
| AC-1.3 | WHEN 静态前端未传 enabled 值 THEN 静态 SDK 允许 `undefined`，行为以桥接实际参数解析为准。 | 边界 |

### US-2: 设置点击视觉和声音反馈

作为应用开发者，我想要配置点击视觉与声音反馈，以便提供符合交互预期的响应。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 API 10 `clickEffect(value|null)` THEN SDK 接受 ClickEffect 或 null。 | 正常 |
| AC-2.2 | WHEN 使用 API 18 Optional clickEffect 形式 THEN `undefined` 也是 SDK 支持的输入。 | 边界 |
| AC-2.3 | WHEN 设置 API 24 `enableClickSoundEffect` THEN 值通过 FrameNode 点击声音配置路径保存。 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-3 | 源码审查 | `view_abstract.cpp:3255-3267` |
| AC-1.2 | R-2 | TASK-3 | 源码审查 | `event_hub.cpp:1083-1089` |
| AC-1.3 | R-3 | TASK-3 | SDK 对照 | `common.static.d.ets:13025` |
| AC-2.1 | R-4 | TASK-3 | SDK 审查 | `common.d.ts:22397` |
| AC-2.2 | R-5 | TASK-3 | SDK 审查 | `common.d.ts:22415` |
| AC-2.3 | R-6 | TASK-3 | 源码/SDK 审查 | `view_abstract.cpp:10011-10021` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 enabled(boolean) | EventHub 与 FocusHub 都得到同一 enabled 值 | 写入顺序由 ViewAbstract 固化 | AC-1.1 |
| R-2 | 边界 | enabled=false | 事件和焦点两个维度均设置为 false | 非单一视觉属性 | AC-1.2 |
| R-3 | 边界 | 静态传入 undefined | 静态 SDK 接受可选参数 | 不将其推断为动态签名 | AC-1.3 |
| R-4 | 行为 | clickEffect 为 ClickEffect 或 null | API 10 视觉反馈配置生效 | 返回链式对象 | AC-2.1 |
| R-5 | 边界 | clickEffect 为 undefined | 采用 API 18 Optional 重载 | 低版本不使用该形态 | AC-2.2 |
| R-6 | 行为 | 设置 enableClickSoundEffect | FrameNode 保存声音反馈开关 | API 24 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3 | SDK/源码审查 | EventHub、FocusHub 双写与静态可选值。 |
| VM-2 | AC-2.1~2.3 | SDK/源码审查 | clickEffect 两个版本形态、声音反馈路径。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `enabled(boolean)` | Public | enabled | 链式值 | N/A | 设置事件和焦点可用性 | AC-1.1~1.3 |
| `clickEffect` | Public | ClickEffect/null/Optional | 链式值 | N/A | 设置点击视觉反馈 | AC-2.1, AC-2.2 |
| `enableClickSoundEffect` | Public | boolean/undefined | 链式值 | N/A | 设置点击声音反馈 | AC-2.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `clickEffect(Optional)` | 变更 | API 18 扩展 undefined | API <18 使用 ClickEffect 或 null | AC-2.2 |
| `enableClickSoundEffect` | 变更 | API 24 新增 | 低版本不调用 | AC-2.3 |

## 接口规格

### 接口定义

**enabled**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enabled(value: boolean)`；静态为 `boolean | undefined` |
| 返回值 | 链式 `T`/`this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.3 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | boolean / static optional | 动态是 | SDK 未声明 | false 同步禁用 EventHub 与 FocusHub。 |

**Click feedback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `clickEffect(value)`、`enableClickSoundEffect(enabled)` |
| 返回值 | 链式 `T`/`this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.3 |

## 兼容性声明

- **已有 API 行为变更:** 无；为存量能力补录。
- **配置文件格式变更:** 无。
- **数据存储格式变更:** 无。
- **最低支持版本:** enabled API 7；clickEffect API 10；Optional clickEffect API 18；点击声音 API 24。
- **API 版本号策略:** SDK 动态/静态定义分别为准。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双 Hub 同步 | SetEnabled 的 EventHub 写入先于 FocusHub | AC-1.1, AC-1.2 |
| 反馈保存 | 声音开关经 FrameNode 路径保存 | AC-2.3 |
| 外部环境 | 是否实际播放声音受设备音频状态影响，注册语义不变 | AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 双 Hub 行为可检查 | 单元/源码审查 | `view_abstract.cpp` |
| 可访问性 | enabled 同步焦点可用性 | 代码审查 | `view_abstract.cpp:3264-3267` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 点击声音受静音/音量影响 | 配置保存语义一致 | 设备测试 | FrameNode 路径 |
| 平板 | 行为一致 | 无差异 | 设备测试 | SDK 契约 |
| 折叠屏 | 行为一致 | 无差异 | 设备测试 | SDK 契约 |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|------|------|------|----------|
| 无障碍 | 是 | enabled 同步 FocusHub | AC-1.1 |
| 深色模式 | 是 | clickEffect 视觉呈现由现有主题处理，本规格不改色值 | AC-2.1 |
| 多窗口/分屏 | 是 | 当前容器内 Hub 独立保存 | AC-1.1 |
| 生态兼容 | 是 | 版本扩展按 since 使用 | AC-2.2, AC-2.3 |

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
    query: "ViewAbstract enabled EventHub FocusHub click effect and click sound effect"
```
