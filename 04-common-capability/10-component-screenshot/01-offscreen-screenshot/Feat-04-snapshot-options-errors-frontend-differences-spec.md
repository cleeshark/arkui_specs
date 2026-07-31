# 特性规格

> Func-04-10-01-Feat-04 固化 SnapshotOptions、离屏异常以及动态/静态 ArkTS 可空性差异。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 截图选项、错误码与跨前端差异 |
| 特性编号 | Func-04-10-01-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 12 起，色彩/HDR API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | SnapshotOptions 与异常规格 | 补录既有参数和错误处理。 |

## 输入文档

- `design.md`
- `interface/sdk-js/api/@ohos.arkui.componentSnapshot.d.ts:71-491`
- `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/src/ani/native/componentSnapshot/componentSnapshot_module.cpp:451-532`
- `interfaces/napi/kits/component_snapshot/js_component_snapshot.cpp:473-487,564-566,760-761`

## 用户故事

### US-1: 配置截图输出

作为应用开发者，我想要配置 scale、渲染完成等待、区域、色彩与动态范围，以便取得所需的 PixelMap。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 传入 SnapshotOptions THEN 支持 API 12 scale/waitUntilRenderFinished、API 15 region、API 23 colorMode/dynamicRangeMode。 | 正常 |
| AC-1.2 | WHEN region 使用 left/right 或 start/end 形式 THEN SDK 接受 SnapshotRegion 或 LocalizedSnapshotRegion 联合类型。 | 正常 |
| AC-1.3 | WHEN 离屏 Builder 或 Content options 的 colorMode/dynamicRangeMode `isAuto=true` THEN 静态与 NAPI 实现报告该配置不支持。 | 异常 |

### US-2: 处理跨前端接口差异

作为跨前端应用开发者，我想要了解静态与动态返回类型差异，以便正确检查截图结果。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 动态 API 返回 Promise 截图 THEN SDK 声明为 Promise<PixelMap>。 | 正常 |
| AC-2.2 | WHEN 静态 API 的 create/get unique/range Promise 形态可返回 null THEN 规格保留 `| null`，不改写为必有 PixelMap。 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-4 | SDK 审查 | `componentSnapshot.d.ts:418-491` |
| AC-1.2 | R-2 | TASK-4 | SDK/NAPI 审查 | `componentSnapshot.d.ts:71-230`; `js_component_snapshot.cpp:323-404` |
| AC-1.3 | R-3 | TASK-4 | ANI/NAPI 审查 | `componentSnapshot_module.cpp:464-471,494-502,525-532` |
| AC-2.1 | R-4 | TASK-4 | SDK 审查 | `UIContext.d.ts:4077,4184-4185` |
| AC-2.2 | R-5 | TASK-4 | SDK 对照 | `UIContext.static.d.ets:3104-3223` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 传入 SnapshotOptions | 解析 scale、wait、region、color/HDR | 字段按 since 可用 | AC-1.1 |
| R-2 | 行为 | region 为物理或本地化边 | 接受联合类型并解析坐标字段 | API 15 | AC-1.2 |
| R-3 | 异常 | 离屏 create 的任一 isAuto=true | 报告 auto 不支持错误 | 不静默降级 | AC-1.3 |
| R-4 | 行为 | 动态 Promise 调用 | 声明为 Promise<PixelMap> | 失败经 Promise/callback 传递 | AC-2.1 |
| R-5 | 边界 | 静态 Promise 调用 | 保留 `Promise<PixelMap> | null` | 以 static.d.ets 为契约 | AC-2.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3 | SDK/ANI/NAPI 审查 | Options since、region、isAuto 异常。 |
| VM-2 | AC-2.1~2.2 | 动态/静态 SDK 对照 | Promise 可空性。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `SnapshotOptions` | Public | scale/wait/region/color/HDR | 配置对象 | 160004 等不支持配置 | 截图输出配置 | AC-1.1~1.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| region | 变更，API 15 | 区域截图 | 低版本不传 region | AC-1.2 |
| colorMode/dynamicRangeMode | 变更，API 23 | 色彩/HDR 输出 | 离屏路径避免 isAuto=true | AC-1.3 |

## 接口规格

### 接口定义

| 属性 | 值 |
|------|-----|
| 函数签名 | `SnapshotOptions{scale, waitUntilRenderFinished, region, colorMode, dynamicRangeMode}` |
| 返回值 | 作为 get/create 的可选参数 |
| 开放范围 | Public；部分色彩枚举受 SDK SysCap 约束 |
| 错误码 | 离屏 isAuto 支持错误、超时/内部错误由调用 API 报告 |
| 关联 AC | AC-1.1~2.2 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| scale/wait | number/boolean | 否 | SDK 默认 | API 12。 |
| region | SnapshotRegionType | 否 | 无 | API 15，物理或本地化边。 |
| colorMode/dynamicRangeMode | Options | 否 | SDK 默认 | API 23；离屏 isAuto 不能为 true。 |

## 兼容性声明

- **已有 API 行为变更:** 无。
- **配置文件格式变更:** 无。
- **数据存储格式变更:** 无。
- **最低支持版本:** Options API 12；region 15；色彩/HDR 23。
- **API 版本号策略:** 动态严格 Promise 与静态可空 Promise 均保留。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 自动模式限制 | 离屏 ANI/NAPI 明确拒绝 isAuto=true | AC-1.3 |
| 外部环境 | 节点色彩空间、动态范围、密度影响最终输出 | AC-1.1 |
| 前端契约 | 以各自 d.ts/d.ets 为准 | AC-2.1, AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可靠性 | 不支持的 isAuto 必须显式失败 | ANI/NAPI 审查 | 输入文档 |
| 可测试性 | 每个 Options 版本边界可静态检查 | SDK 审查 | `componentSnapshot.d.ts` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 色彩、HDR、scale 结果受显示和节点环境影响 | 接口字段不变 | 设备测试 | Options 契约 |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|------|------|------|----------|
| 深色模式 | 是 | 会影响待捕获内容，不改变 Options 语义 | AC-1.1 |
| 版本升级 | 是 | API 15/23 字段须按 since 使用 | AC-1.1, AC-1.2 |
| 生态兼容 | 是 | 动态/静态 Promise 差异显式保留 | AC-2.1, AC-2.2 |

## 行为场景（可选，Gherkin）

L1 规格已由参数约束和异常规则覆盖。

## Spec 自审清单

- [x] 无待定、TBD 或 TODO 占位符
- [x] 所有 AC 使用 WHEN/THEN 格式且可测试
- [x] isAuto 异常与前端差异明确
- [x] 所有规则关联 AC

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "SnapshotOptions region color mode dynamic range isAuto offscreen errors dynamic static differences"
```
