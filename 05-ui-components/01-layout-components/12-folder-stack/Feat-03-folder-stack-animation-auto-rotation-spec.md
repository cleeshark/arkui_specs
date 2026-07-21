# 特性规格

> Func-05-01-12-Feat-03 FolderStack 过渡动画、自动旋转与接口兼容：补录 enableAnimation、autoHalfFold 的默认值和生命周期，半折方向请求/恢复，以及 Dynamic/Static 构造、属性和 reset 语义。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FolderStack 过渡动画、自动旋转与接口兼容 |
| 特性编号 | Func-05-01-12-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 11–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

FolderStack 默认启用悬停转换动画和 `autoHalfFold`。进入/退出悬停时，Pattern 使用既有约 400ms spring 动画与延迟控制内部 Stack 过渡；在系统自动旋转关闭的场景，半折且 autoHalfFold=true 时临时请求 SENSOR 方向，并在退出半折、不可见或 disappear 时恢复。Dynamic API 11 起提供属性，Static API 23 起提供对应可 reset 属性，API 26 增加 options/style 扩展。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 默认过渡动画规格 | 覆盖 enableAnimation 默认 true、启停、最终态与快速切换 |
| ADDED | autoHalfFold 自动旋转规格 | 覆盖 SENSOR 请求、可见性、退出和方向恢复 |
| ADDED | Dynamic/Static 接口兼容规格 | 覆盖 API 11/18/23/26、undefined/reset 与构造 options |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/12-folder-stack/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/folderStack.static.d.ets` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_pattern.cpp` | 已核对 |
| Dynamic bridge | `frameworks/core/components_ng/pattern/folder_stack/bridge/arkts_native_folder_stack_bridge.cpp` | 已核对 |

> 本文档不改变系统旋转设置，只补录 FolderStack 对当前窗口的临时方向请求及恢复职责。

## 用户故事

### US-1: 控制悬停切换动画

**作为** 折叠屏界面开发者  
**我想要** 选择使用默认过渡动画或直接切换  
**以便** 在视觉连续性和即时响应之间取舍

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 未设置、输入按入口 reset 或显式设置 `enableAnimation(true)` THEN FolderStack 在符合条件的悬停进入/退出转换中使用既有默认动画 | 边界 |
| AC-1.2 | WHEN `enableAnimation(false)` THEN 悬停转换直接提交最终上下分区/普通 Stack 状态，不启动默认 spring 动画 | 正常 |
| AC-1.3 | WHEN 默认动画启动 THEN 使用实现既有约 400ms 时长、spring 曲线和必要延迟，不改变转换结束后的分区几何与事件快照 | 正常 |
| AC-1.4 | WHEN 动画进行中收到相反折叠状态、窗口变化或节点 disappear THEN 取消/收敛到最新合法最终态，不保留处于中间位置的孤立内部节点 | 边界 |
| AC-1.5 | WHEN 输入不是有效 boolean THEN Dynamic/Static 入口按 SDK 默认 true 或 reset 语义处理，不把未定义布尔写入属性 | 异常 |

### US-2: 半折时临时启用自动旋转

**作为** 系统自动旋转关闭的用户界面开发者  
**我想要** FolderStack 在半折悬停期间自动适配横向方向  
**以便** 悬停布局能够进入受支持姿态

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `autoHalfFold` 未设置/reset THEN 有效默认值为 true | 边界 |
| AC-2.2 | WHEN autoHalfFold=true、FolderStack 可见且设备进入 HALF_FOLD THEN Pattern 向当前窗口请求 SENSOR 方向，使半折场景可自动旋转 | 正常 |
| AC-2.3 | WHEN autoHalfFold=false THEN FolderStack 不因半折主动覆盖系统/应用当前方向，悬停是否成立按实际方向判定 | 正常 |
| AC-2.4 | WHEN 退出 HALF_FOLD、节点不可见/disappear 或属性从 true 改为 false THEN 恢复进入前/应用应有方向，不遗留 SENSOR 覆盖 | 边界 |
| AC-2.5 | WHEN 窗口/Pipeline/方向接口不可用 THEN 自动旋转路径安全退出，FolderStack 仍按当前方向完成普通或悬停布局 | 异常 |
| AC-2.6 | WHEN 反复进入/退出 HALF_FOLD THEN 方向请求与恢复保持幂等，每个生命周期最终恢复正确状态 | 边界 |

### US-3: 在 Dynamic 与 Static 范式间保持接口边界

**作为** 迁移 ArkUI 编程范式的开发者  
**我想要** 在对应 API 版本使用一致的 FolderStack 属性  
**以便** 不因构造方式改变动画和旋转结果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API 11+ Dynamic 设置 alignContent、enableAnimation、autoHalfFold 或 callbacks THEN bridge 解析后写入同一 FolderStack Property/EventHub/Pattern 状态 | 正常 |
| AC-3.2 | WHEN API 18+ 使用命名 `FolderStackOptions` 与命名事件 payload THEN 历史 API 11/12 能力继续可用，类型规范化不改变运行语义 | 边界 |
| AC-3.3 | WHEN API 23+ Static 设置 boolean/Alignment/callback 为 undefined THEN 执行对应 reset，boolean 恢复默认 true、Alignment 恢复 Center、callback 清除 | 正常 |
| AC-3.4 | WHEN API 26 Static 使用 `setFolderStackOptions` 或 style builder THEN 更新 options/属性同时复用同一内部节点和 Pattern，不重建应用子树状态 | 正常 |
| AC-3.5 | WHEN 在不支持的低 API level 编译 Static/API26 扩展调用 THEN SDK 可见性检查阻止使用，而不是运行时静默模拟该接口 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | 动画开关/快速切换 UT | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_pattern.cpp:28-31,210-249`; `frameworks/core/components_ng/pattern/folder_stack/folder_stack_layout_property.h:24-78`; `test/unittest/core/pattern/folder_stack/folder_stack_test_ng.cpp:1041-1093` |
| AC-2.1~AC-2.6 | R-6~R-11 | 已有实现 | Window 方向/生命周期 UT | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_pattern.cpp:82-98,258-305`; `test/unittest/core/pattern/folder_stack/folder_stack_test_ng.cpp:1850-1872` |
| AC-3.1~AC-3.5 | R-12~R-16 | 已有实现 | SDK 编译 + Dynamic/Static bridge UT | `frameworks/core/components_ng/pattern/folder_stack/bridge/arkts_native_folder_stack_bridge.cpp:44-118,232-287`; `frameworks/core/components_ng/pattern/folder_stack/bridge/folder_stack_static_modifier.cpp:26-130` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 边界 | animation 缺省/true/reset | 使用默认过渡动画 | 默认值 true | AC-1.1 |
| R-2 | 行为 | animation=false | 直接提交最终布局 | 不创建默认动画 | AC-1.2 |
| R-3 | 行为 | 默认动画执行 | 使用既有时长/spring/延迟并收敛到同一最终几何 | 事件语义不依赖中间帧 | AC-1.3 |
| R-4 | 恢复 | 动画中状态反转/窗口变化/disappear | 取消或更新目标并清理中间状态 | 以最新平台状态为准 | AC-1.4 |
| R-5 | 异常 | animation 输入非法 | 回退/reset true | 不写未定义布尔 | AC-1.5 |
| R-6 | 边界 | autoHalfFold 缺省/reset | 有效值 true | Property 默认 true | AC-2.1 |
| R-7 | 行为 | true + 可见 + HALF_FOLD | 请求 SENSOR 方向 | 仅当前窗口生命周期 | AC-2.2 |
| R-8 | 行为 | autoHalfFold=false | 不主动覆盖方向 | 按实际方向判定悬停 | AC-2.3 |
| R-9 | 恢复 | 退出半折/不可见/disappear/关闭属性 | 恢复方向 | 必须幂等 | AC-2.4, AC-2.6 |
| R-10 | 异常 | Window/Pipeline/方向接口为空 | 安全退出自动旋转 | 布局能力保留 | AC-2.5 |
| R-11 | 边界 | 快速反复半折 | 请求/恢复成对且最终状态正确 | 不累积覆盖层 | AC-2.6 |
| R-12 | 行为 | Dynamic 属性调用 | Bridge 写 Property/EventHub/Pattern | API 11/12 | AC-3.1 |
| R-13 | 边界 | API 18 类型规范化 | 保持历史运行行为 | 只改变类型声明形式 | AC-3.2 |
| R-14 | 恢复 | Static undefined | 对各属性执行对应 reset | API 23 | AC-3.3 |
| R-15 | 行为 | API 26 options/style | 更新共享节点而不重建应用子树 | Static only 扩展 | AC-3.4 |
| R-16 | 边界 | 低 API 使用高版本接口 | 编译期不可见 | 不做运行时模拟 | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | 动画时钟/内部节点 UT | 默认开、关闭、时长曲线、反向转换和非法值 |
| VM-2 | R-6~R-11, AC-2.1~AC-2.6 | Window orientation mock | SENSOR 请求、关闭、恢复、缺失接口和幂等 |
| VM-3 | R-12~R-15, AC-3.1~AC-3.4 | Dynamic/Static bridge UT | set/reset/options/style 与最终状态 |
| VM-4 | R-16, AC-3.5 | API level SDK 编译矩阵 | 11/12/18/23/26 可见性 |

## API 变更分析

> 本文档仅补录已有接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `enableAnimation(value: boolean)` | Public Dynamic | true/false | `FolderStackAttribute` | N/A | API 11 控制默认过渡动画 | AC-1.1~AC-1.5 |
| `autoHalfFold(value: boolean)` | Public Dynamic | true/false | `FolderStackAttribute` | N/A | API 11 控制半折自动旋转 | AC-2.1~AC-2.6 |
| Static `enableAnimation(value?)` / `autoHalfFold(value?)` | Public Static | boolean/undefined | `this` | N/A | API 23 设置/reset | AC-1.1~AC-3.3 |
| `setFolderStackOptions(options?)` | Public Static | FolderStackOptions | `this` | N/A | API 26 更新构造参数 | AC-3.4 |
| Static style `FolderStack(style, content_?)` | Public Static | attribute/content builders | `FolderStackAttribute` | N/A | API 26 样式构造 | AC-3.4, AC-3.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | API 18 匿名对象规范化、API 23/26 新范式表面 | 按目标 API level 选择接口 | AC-3.2~AC-3.5 |

## 接口规格

### 接口定义

**enableAnimation(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic `(value: boolean): FolderStackAttribute`；Static `(value: boolean \| undefined): this` |
| 返回值 | 当前 FolderStack 属性对象 |
| 开放范围 | Public、Stage 模型；Dynamic API 11，Static API 23 |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.5 |

**autoHalfFold(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic `(value: boolean): FolderStackAttribute`；Static `(value: boolean \| undefined): this` |
| 返回值 | 当前 FolderStack 属性对象 |
| 开放范围 | Public、Stage 模型；Dynamic API 11，Static API 23 |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| enableAnimation | boolean | Dynamic 是；Static 可 undefined | true | undefined/invalid 走入口默认或 reset |
| autoHalfFold | boolean | Dynamic 是；Static 可 undefined | true | 仅半折、可见且 Window 可用时请求方向 |

## 兼容性声明

- **已有 API 行为变更:** 否；默认 true、API 版本和临时方向恢复行为按存量实现保留。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；动画和方向覆盖不持久化。
- **最低支持版本:** Dynamic 属性 API 11；Static API 23；Static options/style API 26。
- **API 版本号策略:** canonical SDK 的 dynamic/static/staticonly 标记为准。

| 版本 | 契约 | 证据 |
|------|------|------|
| API 11 | enableAnimation/autoHalfFold Dynamic | `interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts:195-227` |
| API 18 | 命名 options 和事件类型 | `interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts:31-136` |
| API 23 | Static 属性、构造和 reset | `interface/sdk-js/api/arkui/component/folderStack.static.d.ets:105-157,227-242` |
| API 26 | setFolderStackOptions/style builder | `interface/sdk-js/api/arkui/component/folderStack.static.d.ets:158-178,244-258` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 最终态一致 | animation 只影响过渡，不改变最终区域/事件 | AC-1.2~AC-1.4 |
| 临时方向覆盖 | autoHalfFold 不修改系统持久设置，退出必须恢复 | AC-2.2~AC-2.6 |
| 生命周期绑定 | 动画和方向请求不得晚于节点可见/附着生命周期 | AC-1.4, AC-2.4 |
| 多范式共享状态 | Dynamic/Static 都落到同一 Property/Pattern | AC-3.1~AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 动画复用现有 Pipeline；关闭时不创建默认动画 | 帧率/trace | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_pattern.cpp:210-249` |
| 功耗 | 不在非半折或不可见状态持续请求 SENSOR/动画帧 | 状态功耗测试 | AC-2.2~AC-2.4 |
| 内存 | 动画/方向状态随 Pattern 生命周期释放 | 生命周期/泄漏测试 | AC-1.4, AC-2.4 |
| 安全 | 不修改系统持久设置，不新增权限 | 代码审查 | Window mock |
| 可靠性 | 快速折叠、反向动画、离树和接口缺失最终可恢复 | 压力/故障注入 | AC-1.4, AC-2.4~AC-2.6 |
| 可测试性 | 动画时钟、窗口方向和 API level 可注入 | UT/SDK 编译 | VM-1~VM-4 |
| 自动化维测 | 可 trace 动画目标、方向请求与恢复原因 | hilog/trace | Pattern |
| 定界定位 | 区分 Property 默认值、Pattern 动画、Window 方向和 Bridge reset | 源码追溯 | `design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 非折叠设备不触发 autoHalfFold | 属性可设置但无半折副作用 | 直板机测试 | AC-2.2 |
| 平板 | 无半折姿态 | 动画只在实际 hover 转换发生 | 多窗口测试 | AC-1.1~AC-1.3 |
| 折叠屏 | 支持时执行悬停动画和临时旋转 | 覆盖半折、展开、不可见和方向关闭 | 真机姿态矩阵 | AC-1.1~AC-2.6 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 动画不改变最终语义树；关闭动画仍保留完整布局 | AC-1.2, AC-1.3 |
| 大字体 | 是 | 动画最终态使用当前测量结果 | AC-1.3 |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 是 | 非全窗口可退出 hover，并需取消动画/恢复方向 | AC-1.4, AC-2.4 |
| 多用户 | 否 | 无持久用户状态 | N/A |
| 版本升级 | 是 | API 11/18/23/26 和 reset 默认值需回归 | AC-3.1~AC-3.5 |
| 生态兼容 | 是 | 默认 true 与方向恢复是稳定行为 | AC-1.1, AC-2.1, AC-2.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: FolderStack 动画与自动旋转
  Scenario: 默认动画进入悬停
    Given enableAnimation 未设置
    When FolderStack 从普通状态进入合法 hover
    Then 使用既有 spring 过渡
    And 动画结束后上下区域与无动画路径相同

  Scenario: 关闭动画直接切换
    Given enableAnimation 为 false
    When hover 状态变化
    Then 不启动默认动画
    And 直接提交最新最终布局

  Scenario: 半折方向恢复
    Given autoHalfFold 为 true且系统自动旋转关闭
    When 可见 FolderStack 进入 HALF_FOLD
    Then 当前窗口请求 SENSOR
    When FolderStack disappear
    Then 恢复原方向且不遗留 SENSOR 覆盖
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖默认动画、autoHalfFold 和接口版本兼容
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] 系统旋转持久设置和 NDK 明确不在范围内

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FolderStack enableAnimation autoHalfFold SENSOR orientation restore spring animation"
  - repo: "openharmony/interface_sdk-js"
    query: "FolderStack enableAnimation autoHalfFold static setFolderStackOptions API 11 23 26"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/folderStack.static.d.ets`
- 架构设计：`05-ui-components/01-layout-components/12-folder-stack/design.md`
