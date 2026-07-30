# 特性规格

> Func-02-01-04-Feat-03 预览器 SDK 与资源打包存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 预览器 SDK 与资源打包 |
| 特性编号 | Func-02-01-04-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 当前 preview SDK 构建路径 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 资源提取 | SystemResources HAP/index/value 到预览资源目录 |
| ADDED | 运行模块 | NAPI、ABC、共享库和字体/证书复制 |
| ADDED | 条件输出 | 标准系统、macOS、TV/穿戴资源路径 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `02-cross-platform/01-platform-adapter/04-previewer-platform-adapter/design.md` | 已核对 |
| SDK build | `adapter/preview/sdk/BUILD.gn` | 已核对 |
| NAPI metadata | `interfaces/napi/kits/napi_lib.gni` | 已核对 |

## 用户故事

### US-1: 准备预览运行资源

**作为** 预览器 SDK 构建维护者
**我想要** 提取并复制系统资源到目标预览目录
**以便** 预览运行时可解析所需资源

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 构建系统资源 THEN `get_system_resource` 从 SystemResources HAP 输出资源目录，`extra_system_resource` 生成资源值文件 | 正常 |
| AC-1.2 | WHEN 为标准系统复制资源 THEN 输出到 `previewer/common` | 正常 |
| AC-1.3 | WHEN 为非标准系统复制 TV/穿戴资源 THEN macOS 使用预置 rich resources，其他平台使用提取资源并输出到 tv_resources/wearable_resources | 边界 |

### US-2: 准备预览运行模块和库

**作为** 预览器 SDK 构建维护者
**我想要** 将 NAPI、ABC 和共享库放到约定位置
**以便** 预览器可按既有 requireNapi 与模块加载路径运行

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 复制 NAPI 模块 THEN 依据 prefix 输出到 `previewer/common/bin/module` 及其子目录 | 正常 |
| AC-2.2 | WHEN 复制 ArkTS ABC/组件模块 THEN 输出到 `previewer/common/bin/module/arkui` 对应目录 | 正常 |
| AC-2.3 | WHEN 输出共享库 THEN 复制 NAPI 依赖及 ICU/Skia 配置；WHEN Windows THEN 额外复制 curl cacert | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1~AC-1.3 | R-1~R-3 | 已有实现 | GN 输出清单 | `sdk/BUILD.gn:47-65,415-461` |
| AC-2.1~AC-2.3 | R-4~R-6 | 已有实现 | 模块/库目录检查 | `sdk/BUILD.gn:73-132,134-390` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 系统资源 action 执行 | 先提取 HAP 资源并生成 value 文件 | inputs/outputs 由 GN 定义 | AC-1.1 |
| R-2 | 行为 | 标准系统资源复制 | 输出到 previewer/common | 路径固定 | AC-1.2 |
| R-3 | 边界 | 非标准系统 TV/穿戴 | mac 使用预置资源，其余使用提取资源 | 设备类型决定输出目录 | AC-1.3 |
| R-4 | 行为 | 遍历 napi_modules | 按 prefix 复制动态库 | 模块目录匹配 requireNapi 基路径 | AC-2.1 |
| R-5 | 行为 | ABC/组件复制 | 输出 arkui 和 components 子目录 | 仅现有 deps/outputs | AC-2.2 |
| R-6 | 边界 | 共享库复制 | 附带 ICU/Skia 配置，Windows 加 cacert | 平台/Skia 版本条件 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | GN action 输出检查 | 资源来源和目录 |
| VM-2 | AC-2.1~AC-2.3 | 预览器目录清单 | 模块、ABC、库和条件文件 |

## API 变更分析

### 新增 API

N/A；内部打包能力，不新增公开 API。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

N/A；接口为内部 GN action/copy target 及其输出契约。

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 当前 preview SDK 构建路径。
- **API 版本号策略:** N/A。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 输出路径 | 模块目录必须匹配预览器加载约定 | AC-2.1, AC-2.2 |
| 资源条件 | 标准系统/macOS/设备类型分支不得合并 | AC-1.2, AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可构建性 | action 输入/输出可追溯 | GN check | sdk/BUILD.gn |
| 可维护性 | 输出目录由 copy target 显式定义 | 文件清单 | sdk/BUILD.gn |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 标准系统 | 输出 previewer/common | 系统资源路径 | GN check | sdk BUILD |
| TV | 输出 tv_resources | 非标准分支 | GN check | sdk BUILD |
| 穿戴 | 输出 wearable_resources | 非标准分支 | GN check | sdk BUILD |

## 全局特性影响

| 特性 | 是否适用 | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | 模块清单和 Skia 配置需回归 | VM-2 |
| 生态兼容 | 是 | requireNapi 基路径不可改变 | AC-2.1 |

## 行为场景（可选，Gherkin）

内部打包路径由接口规格和 AC 覆盖。

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 资源、模块和平台条件边界明确
- [x] AC、规则与 VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "adapter preview sdk BUILD.gn NAPI ABC system resource"
```

**关键文档：** `adapter/preview/sdk/BUILD.gn`
