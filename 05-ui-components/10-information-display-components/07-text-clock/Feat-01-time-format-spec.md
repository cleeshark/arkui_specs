# 特性规格

> Func-05-10-07-Feat-01 TextClock 时间显示与格式化：固化 TextClock 创建、默认格式、时区偏移、12/24 小时制、小时前导零和 Form 场景格式降级的行为规格。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 时间显示与格式化 |
| 特性编号 | Func-05-10-07-Feat-01 |
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
| Design | `05-ui-components/10-information-display-components/07-text-clock/design.md` | Baselined |
| Pattern | `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp` | 已实现 |
| LayoutProperty | `frameworks/core/components_ng/pattern/text_clock/text_clock_layout_property.h` | 已实现 |
| SDK | `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/text_clock.d.ts` | 已发布 |

## 用户故事

### US-1: 默认时间显示

**作为** 应用开发者  
**我想要** 创建 TextClock 后直接显示当前时间  
**以便** 在界面中展示系统时钟。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 创建 TextClock 且未设置 format THEN 按系统 12/24 小时制选择默认格式 | 正常 |
| AC-1.2 | WHEN 系统为 24 小时制 THEN 默认格式使用 24 小时制小时字段 | 正常 |
| AC-1.3 | WHEN 系统为 12 小时制 THEN 默认格式使用 12 小时制和 AM/PM 信息 | 正常 |

### US-2: 自定义格式

**作为** 应用开发者  
**我想要** 通过 `format()` 设置 TextClock 的时间显示格式  
**以便** 按业务场景展示日期、小时、分钟、秒或本地化时间文本。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置合法 format THEN 显示文本按该格式生成 | 正常 |
| AC-2.2 | WHEN format 资源随配置变化刷新 THEN TextClock 重新格式化显示文本 | 正常 |
| AC-2.3 | WHEN Form 场景 format 包含秒或毫秒字段 THEN 使用分钟级安全格式 | 边界 |

### US-3: 时区偏移

**作为** 应用开发者  
**我想要** 为 TextClock 设置时区偏移  
**以便** 在本地时区之外展示指定时区的当前时间。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 未设置 timeZoneOffset THEN 使用系统本地时区 | 正常 |
| AC-3.2 | WHEN 设置 timeZoneOffset THEN 当前时间按指定偏移换算后显示 | 正常 |
| AC-3.3 | WHEN timeZoneOffset 为 0 THEN 显示 UTC 基准时区时间 | 边界 |

### US-4: 小时前导零

**作为** 应用开发者  
**我想要** 控制小时字段是否显示前导零  
**以便** 让时间格式符合 12/24 小时制和页面排版要求。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN PrefixHour 为 AUTO THEN 按系统 12/24 小时制选择前导零策略 | 正常 |
| AC-4.2 | WHEN PrefixHour 指定显示前导零 THEN 小时字段不足两位时补零 | 正常 |
| AC-4.3 | WHEN PrefixHour 指定不显示前导零 THEN 小时字段保持自然位数 | 正常 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `text_clock_pattern.cpp`、`test/unittest/core/pattern/text_clock/` |
| AC-2.1 | R-2 | 源码审阅/单测 | `text_clock_pattern.cpp`、`text_clock_layout_property.h` |
| AC-3.1 | R-3 | 源码审阅/单测 | `text_clock_pattern.cpp`、`text_clock_layout_property.h` |
| AC-4.1 | R-4 | 源码审阅/单测 | `text_clock_pattern.cpp` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | 创建 TextClock | 根据系统制式生成默认时间文本 | 未设置 format 才使用默认 | AC-1.1 |
| R-2 | 行为 | 设置 format | 解析格式字符并刷新显示 | 资源变化需重新解析 | AC-2.1 |
| R-3 | 行为 | 设置 timeZoneOffset | 按偏移换算时间 | 未设置跟随本地时区 | AC-3.1 |
| R-4 | 行为 | 设置 PrefixHour | 控制小时字段前导零 | AUTO 依赖系统制式 | AC-4.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | 默认格式和系统 12/24 小时制 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp`、`test/unittest/core/pattern/text_clock/` |
| VM-2 | format 解析和资源刷新 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/text_clock/text_clock_layout_property.h`、`test/unittest/core/pattern/text_clock/` |
| VM-3 | 时区偏移 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp` |
| VM-4 | Form 场景格式降级 | 源码审阅 | `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| `TextClock(options)` | `TextClockOptions` | `TextClockAttribute` | 创建时钟组件并初始化时区/controller | AC-1.1 |
| `.format(value)` | `string/Resource` | `TextClockAttribute` | 设置时间格式 | AC-2.1 |
| `.hoursWest(value)` / `timeZoneOffset` | `number` | `TextClockAttribute` | 设置时区偏移 | AC-3.2 |

## 兼容性声明

| 维度 | 结论 |
|------|------|
| 公开 API | 不新增、不删除、不改变签名。 |
| 行为兼容 | 记录现有 12/24 小时制、时区和 Form 场景行为。 |

## 架构约束

- 格式化逻辑归属 Pattern，不在 Bridge 层生成显示文本。
- LayoutProperty 只保存格式和时区配置，不直接驱动计时任务。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 可靠性 | 无效或缺省配置走默认格式 | VM-1 |
| 国际化 | AM/PM、月份、星期等文本跟随本地化能力 | VM-2 |

## 多设备适配声明

无组件级设备差异；显示结果由系统时间、语言和布局约束决定。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 深色模式 | 否 | 本 Feat 不涉及颜色。 |
| 本地化 | 是 | 时间文本依赖语言和地区配置。 |
| 多窗口 | 是 | 重新布局不改变时间格式语义。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 默认格式显示当前时间
  Given 未设置 TextClock format
  When 组件创建完成
  Then TextClock 按系统 12/24 小时制显示当前时间
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-07-Feat-01`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp`
- `frameworks/core/components_ng/pattern/text_clock/text_clock_layout_property.h`
- `test/unittest/core/pattern/text_clock/`
