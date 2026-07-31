# 特性规格

> Func-05-10-08-Feat-01 TextTimer 计时模式与格式化：固化正计时、倒计时、startTime、count 和 format 显示行为。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 计时模式与格式化 |
| 特性编号 | Func-05-10-08-Feat-01 |
| 所属 Epic | 信息展示组件 |
| 优先级 | P1 |
| 目标版本 | API 8-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

历史规格补齐，记录已有实现，不新增 API 或行为。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/10-information-display-components/08-text-timer/design.md` | Baselined |
| Pattern | `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp` | 已实现 |
| LayoutProperty | `frameworks/core/components_ng/pattern/texttimer/text_timer_layout_property.h` | 已实现 |
| Bridge | `frameworks/core/components_ng/pattern/texttimer/bridge/arkts_native_text_timer_bridge.cpp` | 已实现 |

## 用户故事

### US-1: 正计时模式

**作为** 应用开发者  
**我想要** 使用 TextTimer 展示正计时  
**以便** 在界面中展示从初始值开始递增的计时结果。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 创建 TextTimer 且 `isCountDown=false` THEN 从 startTime 或默认 0 开始正计时 | 正常 |
| AC-1.2 | WHEN startTime 大于 0 THEN 初始显示值包含 startTime 偏移 | 正常 |

### US-2: 倒计时模式

**作为** 应用开发者  
**我想要** 使用 TextTimer 展示倒计时  
**以便** 在界面中展示从指定时长递减到零的计时结果。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 创建 TextTimer 且 `isCountDown=true` THEN 从 count/inputCount 开始倒计时 | 正常 |
| AC-2.2 | WHEN 倒计时到达 0 THEN 停止继续递减 | 边界 |
| AC-2.3 | WHEN count 无效 THEN 使用默认倒计时时长 | 边界 |

### US-3: 格式化显示

**作为** 应用开发者  
**我想要** 通过 format 控制 TextTimer 的显示格式  
**以便** 按业务场景展示小时、分钟、秒和毫秒。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置合法 format THEN 计时文本按格式字符显示 | 正常 |
| AC-3.2 | WHEN 未设置 format THEN 使用默认 `HH:mm:ss.SS` 格式 | 正常 |
| AC-3.3 | WHEN format 无效 THEN 走默认格式或安全回退 | 边界 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `text_timer_pattern.cpp`、`test/unittest/core/pattern/text_timer/` |
| AC-2.1 | R-2 | 源码审阅/单测 | `text_timer_pattern.cpp`、`arkts_native_text_timer_bridge.cpp` |
| AC-3.1 | R-3 | 源码审阅/单测 | `text_timer_pattern.cpp`、`text_timer_layout_property.h` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | 正计时创建 | 从 startTime 或 0 开始累加 | startTime 缺省为 0 | AC-1.1 |
| R-2 | 行为 | 倒计时创建 | 从 count/inputCount 开始递减 | 到 0 后停止 | AC-2.1 |
| R-3 | 行为 | 设置 format | 按格式化规则生成文本 | 默认 `HH:mm:ss.SS` | AC-3.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | 正计时和 startTime | 源码审阅/单测 | `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp`、`test/unittest/core/pattern/text_timer/` |
| VM-2 | 倒计时和 count 边界 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/texttimer/bridge/arkts_native_text_timer_bridge.cpp` |
| VM-3 | format 显示 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/texttimer/text_timer_layout_property.h` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| `TextTimer(options)` | `isCountDown/count/controller` | `TextTimerAttribute` | 创建计时器 | AC-1.1, AC-2.1 |
| `.format(value)` | `string/Resource` | `TextTimerAttribute` | 设置计时文本格式 | AC-3.1 |

## 兼容性声明

不新增、不删除、不改变 TextTimer 公开 API。

## 架构约束

- Bridge 做参数校验，Pattern 维护计时状态。
- format 只影响显示文本，不改变真实计时方向。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 可靠性 | 无效 count/format 不导致崩溃 | VM-2, VM-3 |

## 多设备适配声明

无组件级设备差异。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 多窗口 | 是 | 重新布局不改变计时值。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 倒计时到达零后停止
  Given TextTimer 处于倒计时模式
  When 计时值到达 0
  Then TextTimer 停止继续递减
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-08-Feat-01`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp`
- `frameworks/core/components_ng/pattern/texttimer/text_timer_layout_property.h`
- `frameworks/core/components_ng/pattern/texttimer/bridge/arkts_native_text_timer_bridge.cpp`
