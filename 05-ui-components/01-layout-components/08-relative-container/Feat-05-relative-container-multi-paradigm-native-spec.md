# 特性规格

> Func-05-01-08-Feat-05 RelativeContainer 多范式与原生接口兼容：补录 Dynamic、Static、Common 属性、Public Native options、内部 modifier、legacy 和版本边界。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | RelativeContainer 多范式与原生接口兼容 |
| 特性编号 | Func-05-01-08-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 9–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

RelativeContainer Dynamic 构造和基础 alignRules 自 API 9 可用；localized alignRules、guideline、barrier、chainMode 和 Public Native option 自 API 12 可用；chainWeight 自 API 14；Static 组件自 API 23，builder/Extendable 自 API 26。本 Feat 把 Native 证据纳入组件 API 兼容矩阵，不建立独立 NDK 功能域。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Dynamic/Common 表面规格 | API 9–23、Bridge set/reset 与属性通道 |
| ADDED | Static 表面规格 | API 23 构造/属性与 API 26 扩展 |
| ADDED | Public Native 规格 | NodeType、三类 option 生命周期和边界 |
| ADDED | 内部 modifier/legacy 风险 | 内部 ABI、getter 快照与旧管线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/08-relative-container/design.md` | 已补录 |
| ArkTS SDK | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts`、`common.d.ts`；`interface/sdk-js/api/arkui/component/relativeContainer.static.d.ets` | 已核对 |
| Public Native | `interfaces/native/native_node.h`、`interfaces/native/node_attributes/layout.h`、`interfaces/native/node/node_node_relative_container.cpp` | 已核对 |
| Modifier | `frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_dynamic_modifier.cpp`、`relative_container_static_modifier.cpp` | 已核对 |

## 用户故事

### US-1: 按版本使用 Dynamic/Common API

**作为** Dynamic ArkTS 开发者  
**我想要** 在正确 API level 使用容器和子项 Common 属性  
**以便** 避免把高版本声明用于低版本设备

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN API level>=9 THEN `RelativeContainer()` 与基础 `alignRules(AlignRuleOption)` 可见 | 正常 |
| AC-1.2 | WHEN API level>=11 THEN AlignRuleOption.bias 可见，auto/margin 新运行语义按版本生效 | 正常 |
| AC-1.3 | WHEN API level>=12 THEN localized alignRules、guideLine、barrier 和 chainMode 可见 | 正常 |
| AC-1.4 | WHEN API level>=14 THEN chainWeight/ChainWeightOptions 可见；API 23 起支持其 attributeModifier 动态配置 | 正常 |
| AC-1.5 | WHEN bridge 的 guideLine/barrier 输入为非数组、undefined 或 reset THEN 清空对应容器属性并触发后续 Measure | 边界 |
| AC-1.6 | WHEN 未找到专用 Public Dynamic `RelativeContainerModifier.d.ts` THEN 不得虚构独立 modifier class；增量配置只按已声明的 Common/attributeModifier 表面描述 | 边界 |

### US-2: 使用 Static RelativeContainer

**作为** Static ArkTS 开发者  
**我想要** 使用 Static 构造、属性、builder 和可扩展组件  
**以便** 在 Static 编译模型中获得同一布局能力

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN API level>=23 THEN Static RelativeContainer 类型、`guideLine`、`barrier`、attributeModifier 和构造可见 | 正常 |
| AC-2.2 | WHEN Static guideLine/barrier 收到有效数组 THEN 转换为 GuidelineInfo/BarrierInfo 并写 NG Property | 正常 |
| AC-2.3 | WHEN Static guideLine/barrier 收到 undefined 或转换失败 THEN 写空 vector，移除对应虚拟锚点 | 边界 |
| AC-2.4 | WHEN API level>=26 THEN `setRelativeContainerOptions()`、style builder overload 与 `ExtendableRelativeContainer` 可见 | 正常 |
| AC-2.5 | WHEN 调用 `setRelativeContainerOptions` THEN 因 RelativeContainer 无构造 options，generated 实现保持空操作且不改变 guide/barrier | 边界 |

### US-3: 管理 Public Native option 生命周期

**作为** ArkUI Native 开发者  
**我想要** 创建、设置、读取并销毁 guideline/barrier/alignment rule option  
**以便** 通过公开 C API 构造相对布局属性

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API>=12 THEN Public Native NodeType 包含 RelativeContainer，节点属性包含 guide line/barrier | 正常 |
| AC-3.2 | WHEN 调用 GuidelineOption/BarrierOption/AlignmentRuleOption Create THEN 返回由调用方持有的 option；WHEN 调用 Dispose THEN 释放其内存，null Dispose 安全返回 | 正常 |
| AC-3.3 | WHEN 使用合法 index/setter THEN 保存 id、direction、position/referencedId；getter 返回已保存值 | 正常 |
| AC-3.4 | WHEN option 为 null 或 index 越界 THEN setter no-op；getter 按实现返回空指针、默认枚举或数值 sentinel，不抛 C++ 异常 | 异常 |
| AC-3.5 | WHEN 设置 AlignmentRuleOption start/end/center/top/bottom/bias THEN 这些数据用于子项对齐规则，而非 RelativeContainer 自身 guide/barrier vector | 正常 |
| AC-3.6 | WHEN 调用方 Dispose option THEN 不得继续使用其指针；option 不由 FrameNode 自动接管生命周期 | 边界 |

### US-4: 区分 Public Native 与内部 modifier/legacy

**作为** 接口维护者  
**我想要** 明确公开 C API、内部 Arkoala/CJ 表和旧 Pipeline  
**以便** 规格不扩大开放范围且能定位兼容风险

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN NG dynamic modifier 设置 guideline 且同时给 start/end THEN start 优先；reset 同时移除 ResourceObject 并清属性 | 正常 |
| AC-4.2 | WHEN 请求 CJUI RelativeContainer modifier THEN 得到内部 guide/barrier set/get/reset 槽位；该表不作为 Public C header | 正常 |
| AC-4.3 | WHEN 使用 legacy Pipeline THEN 通过 classic RelativeContainerModelImpl 走兼容路径，NG 的拓扑/缓存细节不自动承诺给 legacy | 边界 |
| AC-4.4 | WHEN 内部 GetGuideLine/GetBarrier 跨节点或在更新后调用 THEN 函数静态快照可能陈旧，该事实只列风险，不改变 Public Native getter 契约 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.6 | R-1~R-6 | 已有实现 | Dynamic SDK level compile + Bridge UT | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:21-465`；`interface/sdk-js/api/@internal/component/ets/common.d.ts:19894-19915,23128-23177` |
| AC-2.1~AC-2.5 | R-7~R-11 | 已有实现 | Static SDK compile + generated UT | `interface/sdk-js/api/arkui/component/relativeContainer.static.d.ets:23-383`；`frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_static_modifier.cpp:20-150` |
| AC-3.1~AC-3.6 | R-12~R-16 | 已有实现 | Native option/node UT | `interfaces/native/native_node.h:124-141,9186-9207`；`interfaces/native/node_attributes/layout.h:263-675`；`interfaces/native/node/node_node_relative_container.cpp:23-409` |
| AC-4.1~AC-4.4 | R-17~R-20 | 已有实现 | NG/CJ/legacy/risk UT | `frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_dynamic_modifier.cpp:49-268` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | API level>=9 编译 Dynamic 基础表面 |RelativeContainer 和基础 alignRules 可见 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:21-43`；`interface/sdk-js/api/@internal/component/ets/common.d.ts:5458-5565,23128-23142` | AC-1.1 |
| R-2 | 行为 | API level>=11 使用 bias/auto/margin |bias 声明可见，运行时启用新自适应与锚距语义 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:5556-5565`；`interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:431-452` | AC-1.2 |
| R-3 | 行为 | API level>=12 编译 localized/guide/barrier/chain |相应 overload、属性、类型可见 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:45-421`；`interface/sdk-js/api/@internal/component/ets/common.d.ts:23143-23177` | AC-1.3 |
| R-4 | 行为 | API level>=14/23 使用 chainWeight |14 可声明；23 可通过 attributeModifier 动态配置 | `interface/sdk-js/api/@internal/component/ets/units.d.ts:3531-3565`；`interface/sdk-js/api/@internal/component/ets/common.d.ts:19894-19915` | AC-1.4 |
| R-5 | 恢复 |Dynamic bridge 收到非数组/undefined/reset guide/barrier |设置空列表或执行 reset，Model 属性触发 Measure | `frameworks/core/components_ng/pattern/relative_container/bridge/arkts_native_relative_container_bridge.cpp:195-262,289-423` | AC-1.5 |
| R-6 | 边界 |检查 Public Dynamic modifier 声明 |无专用 RelativeContainerModifier.d.ts，不生成该 class 规格 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:366-422` | AC-1.6 |
| R-7 | 行为 | API level>=23 编译 Static RelativeContainer |Static 类型/属性/构造/attributeModifier 可见 | `interface/sdk-js/api/arkui/component/relativeContainer.static.d.ets:23-331` | AC-2.1 |
| R-8 | 行为 |Static guide/barrier 数组转换成功 |写入 GuidelineInfo/BarrierInfo vector | `frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_static_modifier.cpp:47-92,113-138` | AC-2.2 |
| R-9 | 恢复 |Static optional 不存在或转换失败 |写空 vector 清除属性 | `frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_static_modifier.cpp:113-138` | AC-2.3 |
| R-10 | 行为 | API level>=26 编译 Static 扩展 |set options、builder、Extendable 可见 | `interface/sdk-js/api/arkui/component/relativeContainer.static.d.ets:267-383` | AC-2.4 |
| R-11 | 边界 |调用 setRelativeContainerOptions |generated 实现为空操作，因为容器没有 options | `frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_static_modifier.cpp:106-110` | AC-2.5 |
| R-12 | 行为 | API>=12 使用 Public Native 类型 |NodeType 含 RelativeContainer，属性含 guide line/barrier | `interfaces/native/native_node.h:124-141,9186-9207` | AC-3.1 |
| R-13 | 行为 |Create/Dispose Native option |Create 分配 option；Dispose 释放，null 安全返回 | `interfaces/native/node/node_node_relative_container.cpp:23-36,104-117,181-194` | AC-3.2, AC-3.6 |
| R-14 | 行为 |合法 option/index set/get |按 header 声明保存并返回 guideline/barrier 字段 | `interfaces/native/node_attributes/layout.h:263-448`；`interfaces/native/node/node_node_relative_container.cpp:38-179` | AC-3.3 |
| R-15 | 异常 |Native option null 或 index 越界 |setter return；getter 返回实现 sentinel/空值，不抛异常 | `interfaces/native/node/node_node_relative_container.cpp:38-179,196-409` | AC-3.4 |
| R-16 | 行为 |设置 AlignmentRuleOption |保存 start/end/center/top/bottom 和 horizontal/vertical bias | `interfaces/native/node_attributes/layout.h:450-675`；`interfaces/native/node/node_node_relative_container.cpp:181-409` | AC-3.5 |
| R-17 | 行为 |NG dynamic guideline 同时有 start/end 或 reset |set 取 start；reset 删除资源对象并清 guideline | `frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_dynamic_modifier.cpp:49-83,148-160` | AC-4.1 |
| R-18 | 行为 |请求 CJUI RelativeContainer modifier |返回内部 guide/barrier set/get/reset 表 | `frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_dynamic_modifier.cpp:255-268` | AC-4.2 |
| R-19 | 边界 |当前 Pipeline 为 legacy |使用 legacy modifier/model 槽位，不把 NG 细节跨管线归一 | `frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_dynamic_modifier.cpp:163-239` | AC-4.3 |
| R-20 | 异常 |内部 GetGuideLine/GetBarrier 多次跨节点调用 |函数静态 vector 只在首次调用初始化，存在陈旧快照风险 | `frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_dynamic_modifier.cpp:109-145` | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-6, AC-1.1~AC-1.6 | API 9/11/12/14/20/23 compile + Bridge UT |可见性、reset、无专用 Dynamic modifier |
| VM-2 | R-7~R-11, AC-2.1~AC-2.5 | API 22/23/25/26 Static compile |数组/undefined、空 options、builder/Extendable |
| VM-3 | R-12~R-16, AC-3.1~AC-3.6 | Native C UT/XTS |NodeType、Create/Dispose、set/get、null/index、所有权 |
| VM-4 | R-17~R-20, AC-4.1~AC-4.4 | NG/CJ/legacy/risk UT |start 优先、资源 reset、内部槽位、getter 快照 |

## API 变更分析

> Public Native 接口属于 RelativeContainer 组件现有表面；本轮不创建独立 NDK 功能域。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| Dynamic RelativeContainer/Common APIs | Public |容器、align/guide/barrier/chain |属性对象/当前组件 | N/A | API 9–14 Dynamic 能力 | AC-1.1~AC-1.6 |
| Static RelativeContainer APIs | Public |guide/barrier/options/builder |RelativeContainerAttribute | N/A | API 23/26 Static 能力 | AC-2.1~AC-2.5 |
| `OH_ArkUI_GuidelineOption_*` | Public C API |size/id/axis/start/end/index |pointer/field/void | N/A | API 12 guideline option 生命周期 | AC-3.2~AC-3.4 |
| `OH_ArkUI_BarrierOption_*` | Public C API |size/id/direction/reference/index |pointer/field/void | N/A | API 12 barrier option 生命周期 | AC-3.2~AC-3.4 |
| `OH_ArkUI_AlignmentRuleOption_*` | Public C API |anchor/alignment/bias |pointer/field/void | N/A | API 12 child alignment option | AC-3.2~AC-3.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| Static RelativeContainer 扩展 | 变更 |API 26 使用 builder/Extendable |低版本使用 API 23 构造与 attributeModifier | AC-2.4 |
| 无废弃 API | 无 |无接口移除 |无需迁移 | AC-1.1~AC-4.4 |

## 接口规格

### 接口定义

**ArkTS RelativeContainer**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RelativeContainer(): RelativeContainerAttribute` / Static `RelativeContainer(content_?)` |
| 返回值 | RelativeContainerAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| guideLine | Array<GuideLineStyle>/undefined |否 |空 |API 12 Dynamic / API 23 Static |
| barrier |两种 BarrierStyle array/undefined |否 |空 |API 12 Dynamic / API 23 Static |
| content_ | CustomBuilder |否 |空 |Static 容器内容 |

**Native option groups**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_GuidelineOption_*` / `OH_ArkUI_BarrierOption_*` / `OH_ArkUI_AlignmentRuleOption_*` |
| 返回值 |Create 返回 option pointer；getter 返回字段；setter/Dispose 返回 void |
| 开放范围 | Public C API |
| 错误码 | N/A；使用 no-op/sentinel 边界 |
| 关联 AC | AC-3.1~AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| option |对应 ArkUI_*Option* |是 |无 |Create 后、Dispose 前有效 |
| index | int32_t |数组 option 必填 |无 |0<=index<size |
| id/value | const char*/枚举/float |按 setter 必填 |实现默认/sentinel |ID 生命周期由 option 保存 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 |按 API level 使用 Dynamic/Static |接口可见并写共享 NG 属性 | AC-1.1~AC-2.5 |
| 2 |Native 正常生命周期 |Create→set/get→Dispose | AC-3.1~AC-3.3, AC-3.5, AC-3.6 |
| 3 |Native null/越界 |no-op 或 sentinel，不抛异常 | AC-3.4 |
| 4 |内部/legacy 通道 |保持 InnerApi 与风险边界 | AC-4.1~AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 是；能力按 API 11/12/14/20/23/26 累加，未移除旧接口。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** RelativeContainer API 9；Public Native options API 12。
- **API 版本号策略:** Dynamic 9/11/12/14/20/23，Static 23/26，Native C 12。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| canonical 来源 |ArkTS/Public Native 签名分别取 interface/sdk-js 与 interfaces/native | AC-1.1~AC-3.6 |
|共享 NG 模型 |正常 Dynamic/Static/Native 节点属性最终进入同一 RelativeContainer/child Property | AC-1.5, AC-2.2, AC-3.5 |
|所有权分离 |Native option 由调用方 Create/Dispose，FrameNode 不接管 | AC-3.2, AC-3.6 |
|接口分级 |CJ/Arkoala/legacy 是内部实现，不扩大 Public 表 | AC-4.2, AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 |转换不增加布局复杂度 |Trace | VM-1~VM-3 |
| 功耗 |无后台任务/IPC |代码审查 | VM-4 |
| 内存 |Native option 一一 Dispose |ASan/UT | AC-3.2, AC-3.6 |
| 安全 |调用方负责指针有效期 |XTS | AC-3.4, AC-3.6 |
| 可靠性 |空值/越界走清空、no-op 或 sentinel |fuzz | AC-1.5, AC-2.3, AC-3.4 |
| 可测试性 |版本×范式×生命周期矩阵 |SDK/UT | VM-1~VM-4 |
| 自动化维测 |复用拓扑/循环 Dump |Dump | Feat-02 AC-3.3 |
| 定界定位 |区分 Public/InnerApi/legacy |设计审查 | `05-ui-components/01-layout-components/08-relative-container/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 |无差异 |同一 API level/Native ABI |SDK/Native UT | AC-1.1~AC-3.6 |
| 平板 |无差异 |转换后共享 NG 算法 |通道对照 | AC-2.2, AC-3.5 |
| 折叠屏 |无差异 |尺寸不改变 option 生命周期 |集成测试 | AC-3.6 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 |仅定义接口通道 |
| 大字体 | 否 |不改变字体 |
| 深色模式 | 否 |不涉及颜色 |
| 多窗口/分屏 | 是 |共享 Measure 适配窗口 | AC-1.5, AC-2.2 |
| 多用户 | 否 |无持久状态 |
| 版本升级 | 是 |各 API level 需回归 | AC-1.1~AC-2.5, AC-3.1 |
| 生态兼容 | 是 |Public/InnerApi 边界与 option 所有权稳定 | AC-3.2~AC-4.4 |

## 行为场景（可选，Gherkin）

详见接口规格行为索引与 VM-1~VM-4。

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可独立测试
- [x] Dynamic、Static、Public Native、InnerApi、legacy 边界明确
- [x] Native 证据并入本 Feat，未创建独立 NDK 域
- [x]每个 AC 与规则、VM 双向追溯
- [x]静态快照等实现偏差只列风险，不改写 Public 契约

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RelativeContainer dynamic static modifier Native GuidelineOption BarrierOption AlignmentRuleOption"
  - repo: "openharmony/interface_sdk-js"
    query: "RelativeContainer static ExtendableRelativeContainer API 23 26"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/relative_container.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/relativeContainer.static.d.ets`
- Public Native：`interfaces/native/node_attributes/layout.h`
- 共享设计：`05-ui-components/01-layout-components/08-relative-container/design.md`
