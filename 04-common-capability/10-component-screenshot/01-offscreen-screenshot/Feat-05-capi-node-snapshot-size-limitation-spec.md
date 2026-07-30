# 特性规格

> Func-04-10-01-Feat-05 固化 NDK 节点同步截图、SnapshotOptions 所有权及尺寸限制查询。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | C API 节点截图与尺寸限制 |
| 特性编号 | Func-04-10-01-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 节点截图 API 15；尺寸限制 API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | NDK 节点截图与 Options 生命周期 | 补录既有 C API。 |

## 输入文档

- `design.md`
- `interfaces/native/native_node.h:14090-14129`
- `interfaces/native/native_type.h:3570-3635`
- `interfaces/native/node/node_component_snapshot.cpp:37-103`

## 用户故事

### US-1: 同步捕获 NodeHandle

作为 NDK 开发者，我想要同步取得节点 PixelMap，以便在原生代码中处理截图。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `OH_ArkUI_GetNodeSnapshot(node, options, pixelmap)` 且节点在树上并已渲染 THEN 返回成功并输出系统创建的 PixelMap。 | 正常 |
| AC-1.2 | WHEN node/options/out 参数无效 THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-1.3 | WHEN 捕获失败或超时 THEN 返回内部错误或 `ARKUI_ERROR_CODE_COMPONENT_SNAPSHOT_TIMEOUT`，不得把空 PixelMap 当成功。 | 异常 |

### US-2: 管理选项和尺寸限制

作为 NDK 开发者，我想要创建、配置、释放 Options 并查询最大截图尺寸，以便避免资源泄漏和超限。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 创建 SnapshotOptions THEN 使用完成后必须调用 Destroy。 | 恢复 |
| AC-2.2 | WHEN 设置 scale THEN `scale <= 0` 返回参数错误。 | 边界 |
| AC-2.3 | WHEN 设置色彩或动态范围 THEN API 23 传入具体 mode 与 isAuto；无效 options 返回参数错误。 | 异常 |
| AC-2.4 | WHEN 调用 API 26 `OH_ArkUI_GetNodeSnapshotSizeLimitation` THEN 输出 maxWidth/maxHeight 或返回参数错误。 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1~R-3 | TASK-5 | 头文件/实现审查 | `native_node.h:14090-14105`; `node_component_snapshot.cpp:88-103` |
| AC-2.1 | R-4 | TASK-5 | 头文件审查 | `native_type.h:3570-3586` |
| AC-2.2 | R-5 | TASK-5 | 实现审查 | `node_component_snapshot.cpp:54-64` |
| AC-2.3 | R-6 | TASK-5 | 头文件审查 | `native_type.h:3600-3635` |
| AC-2.4 | R-7 | TASK-5 | 头文件审查 | `native_node.h:14108-14129` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 已渲染节点调用 GetNodeSnapshot | 同步输出 PixelMap 和成功码 | API 15 | AC-1.1 |
| R-2 | 异常 | 参数为空/无效 | 返回 PARAM_INVALID | 调用方检查返回码 | AC-1.2 |
| R-3 | 异常 | 捕获失败/超时 | 返回 INTERNAL_ERROR 或 SNAPSHOT_TIMEOUT | PixelMap 不代表成功 | AC-1.3 |
| R-4 | 恢复 | Options 使用完成 | 调用 Destroy 释放 | Create/Destroy 成对 | AC-2.1 |
| R-5 | 边界 | scale <= 0 | SetScale 返回 PARAM_INVALID | 仅正 scale 合法 | AC-2.2 |
| R-6 | 行为 | 设置 color/dynamic range | 配置具体 mode/isAuto，非法 options 返回错误 | API 23 | AC-2.3 |
| R-7 | 行为 | 查询尺寸限制 | 输出最大宽高 | API 26 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3 | C API 单测/头文件审查 | 成功、参数错误、超时。 |
| VM-2 | AC-2.1~2.4 | C API 单测/实现审查 | 所有权、正 scale、API 23/26。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `OH_ArkUI_GetNodeSnapshot` | Public C API | node/options/out pixelmap | int32_t | NO_ERROR/PARAM_INVALID/INTERNAL/TIMEOUT | 节点同步截图 | AC-1.1~1.3 |
| `OH_ArkUI_Create/DestroySnapshotOptions` | Public C API | 无/options | handle/void | 创建可能 null | Options 生命周期 | AC-2.1 |
| `OH_ArkUI_SnapshotOptions_Set*` | Public C API | options/scale/mode/isAuto | int32_t | PARAM_INVALID | 配置截图 | AC-2.2, AC-2.3 |
| `OH_ArkUI_GetNodeSnapshotSizeLimitation` | Public C API | width/height out | int32_t | NO_ERROR/PARAM_INVALID | 尺寸限制 | AC-2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 色彩/动态范围 Options | 变更，API 23 | 高级输出配置 | 低版本仅使用 scale/default | AC-2.3 |
| 尺寸限制查询 | 变更，API 26 | 输出上限预检 | 低版本无此查询 | AC-2.4 |

## 接口规格

### 接口定义

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_GetNodeSnapshot(ArkUI_NodeHandle, ArkUI_SnapshotOptions*, OH_PixelmapNative**)` |
| 返回值 | ArkUI_ErrorCode |
| 开放范围 | Public C API |
| 错误码 | NO_ERROR、PARAM_INVALID、INTERNAL_ERROR、COMPONENT_SNAPSHOT_TIMEOUT |
| 关联 AC | AC-1.1~1.3 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | ArkUI_NodeHandle | 是 | 无 | 必须在树上且已渲染。 |
| options | ArkUI_SnapshotOptions* | 否 | null 使用默认 | 非 null 必须由 Create 获得并最终 Destroy。 |
| pixelmap | OH_PixelmapNative** | 是 | 无 | 成功后调用方负责 Release。 |

## 兼容性声明

- **已有 API 行为变更:** 无。
- **配置文件格式变更:** 无。
- **数据存储格式变更:** 无。
- **最低支持版本:** C 节点截图/Options API 15；色彩/HDR API 23；尺寸限制 API 26。
- **API 版本号策略:** C API 使用返回码和显式资源释放，不等同 ArkTS Promise 契约。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 资源所有权 | PixelMap 与 Options 均由调用方按 C API 规则释放 | AC-1.1, AC-2.1 |
| 同步调用 | GetNodeSnapshot 是同步接口 | AC-1.1~1.3 |
| 输出状态 | 节点挂树和渲染状态为前置条件 | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 内存 | 每个成功 PixelMap 最终 Release | C API 单测 | `native_node.h:14090-14094` |
| 可测试性 | 错误码和所有权可通过 C API 检查 | 单测/审查 | 输入文档 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 尺寸上限和输出由实际平台决定 | API 26 查询真实上限 | 设备测试 | native_node.h |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|------|------|------|----------|
| 多窗口 | 是 | NodeHandle 属于实际 UI 树 | AC-1.1 |
| 深色/HDR | 是 | C Options API 23 可配置 | AC-2.3 |
| 版本升级 | 是 | API 23/26 按 since 使用 | AC-2.3, AC-2.4 |

## 行为场景（可选，Gherkin）

L1 规格由 C 接口参数、返回码和资源约束表覆盖。

## Spec 自审清单

- [x] 无待定、TBD 或 TODO 占位符
- [x] 所有 AC 使用 WHEN/THEN 格式且可测试
- [x] C API 所有权和同步错误码明确
- [x] 所有规则关联 AC

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "OH_ArkUI_GetNodeSnapshot SnapshotOptions ownership scale color dynamic range size limitation"
```
