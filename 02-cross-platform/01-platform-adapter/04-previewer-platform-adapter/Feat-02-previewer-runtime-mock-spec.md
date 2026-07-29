# 特性规格

> Func-02-01-04-Feat-02 预览器运行入口与平台服务替身存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 预览器运行入口与平台服务替身 |
| 特性编号 | Func-02-01-04-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 当前 preview adapter |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 预览视图与事件 | 表面变化、鼠标/轴/触摸与渲染后端分支 |
| ADDED | 平台替身 | Ability/Stage Context、Inspector、OSAL 预览实现 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `02-cross-platform/01-platform-adapter/04-previewer-platform-adapter/design.md` | 已核对 |
| View | `adapter/preview/entrance/ace_view_preview.cpp` | 已核对 |
| Events | `adapter/preview/entrance/event_dispatcher.cpp` | 已核对 |
| Context mock | `adapter/preview/external/ability/context.cpp` | 已核对 |

## 用户故事

### US-1: 在预览器承载视图和输入

**作为** 预览器宿主
**我想要** 创建视图并转发表面与输入事件
**以便** ArkUI 页面在桌面预览环境中响应交互

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 创建 AceViewPreview THEN 按当前 event runner、platform thread 与 Rosen 开关创建线程模型 | 正常 |
| AC-1.2 | WHEN 表面尺寸变化 THEN 保存宽高并调用已注册 view change callback | 正常 |
| AC-1.3 | WHEN 收到 mouse/axis/touch THEN 转发对应回调；WHEN touch 类型 UNKNOWN THEN 返回 false 且不继续转发 | 边界 |
| AC-1.4 | WHEN ENABLE_ROSEN_BACKEND 定义 THEN 使用 RS draw delegate；否则保留 Flutter scene fallback | 边界 |

### US-2: 使用预览平台服务替身

**作为** 预览器运行环境
**我想要** 从工程目录创建 Stage 或 FA Context mock
**以便** 页面可读取预览所需的模块配置而不依赖真实系统服务

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN isStage 为 true/false THEN 分别读取 module.json/config.json 并创建 StageContext/FaContext | 正常 |
| AC-2.2 | WHEN 配置文件无法打开 THEN 记录告警并返回 null | 异常 |
| AC-2.3 | WHEN 在 Windows 或非 Windows 构建 Context 路径 THEN 使用对应分隔符拼接文件路径 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Preview runtime UT | `ace_view_preview.cpp:23-101`; `event_dispatcher.cpp:130-170` |
| AC-2.1~AC-2.3 | R-5~R-7 | 已有实现 | 文件/Context mock UT | `external/ability/context.cpp:23-53` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 创建预览 View | 构造线程模型并保持 instanceId | 线程参数来自宿主 | AC-1.1 |
| R-2 | 行为 | 表面尺寸变化 | 回调接收宽高和原因 | 无回调时安全返回 | AC-1.2 |
| R-3 | 边界 | 任一输入事件 | 转发有效事件；UNKNOWN touch 拒绝 | 不伪造事件类型 | AC-1.3 |
| R-4 | 边界 | Rosen 宏切换 | 选择 RS 或 Flutter draw delegate | 编译期路径 | AC-1.4 |
| R-5 | 行为 | Stage/FA 创建 | 读取相应 JSON 并 Parse | 仅预览 mock | AC-2.1 |
| R-6 | 异常 | 文件不可读取 | 返回 null 并记录告警 | 不创建半初始化 Context | AC-2.2 |
| R-7 | 边界 | 路径拼接 | Windows 用反斜杠，其他用斜杠 | 平台宏决定 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | fake surface/input | 事件和后端分支 |
| VM-2 | AC-2.1~AC-2.3 | 临时 JSON 文件 | Stage/FA、失败和分隔符 |

## API 变更分析

### 新增 API

N/A；内部预览入口和 mock，不新增公开 API。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

N/A；内部 C++ 运行时适配，行为由 AC 和规则定义约束。

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否；只读取既有 module.json/config.json。
- **数据存储格式变更:** 否。
- **最低支持版本:** 当前 preview adapter。
- **API 版本号策略:** N/A。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 预览替身定界 | Context mock 不等同真机 AbilityRuntime | AC-2.1~AC-2.3 |
| 后端分支 | Rosen/Flutter 由编译宏决定 | AC-1.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可靠性 | 未知 touch 和文件缺失安全返回 | UT | View/Context 源码 |
| 可测试性 | 输入、表面和 JSON 文件可独立伪造 | UT | VM-1, VM-2 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| Windows 桌面 | Context 使用反斜杠 | 平台宏路径分支 | UT | context.cpp |
| Linux/macOS 桌面 | Context 使用斜杠 | 非 Windows 分支 | UT | context.cpp |

## 全局特性影响

| 特性 | 是否适用 | 结论 | 关联场景 |
|------|--------|------|----------|
| 多窗口/分屏 | 是 | 表面变化经 View callback 传递 | AC-1.2 |
| 生态兼容 | 是 | 保持 preview mock 与真机服务边界 | AC-2.1 |

## 行为场景（可选，Gherkin）

运行路径由接口规格和 AC 覆盖。

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 后端分支和 mock 边界明确
- [x] AC、规则与 VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "adapter preview AceViewPreview EventDispatcher Context mock"
```

**关键文档：** `adapter/preview/entrance/ace_view_preview.cpp`
