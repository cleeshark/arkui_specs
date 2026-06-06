# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | BUILD.gn 结构 |
| 特性编号 | Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | N/A（内部构建结构） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性补录 ace_engine 现有 BUILD.gn/gni 构建结构，包括 OpenHarmony 根构建入口、平台发现、全局 config、主库聚合、framework source_set、前端生成物、接口包、扩展组件、测试入口，以及 ArkUI-X Android/iOS adapter 参考构建。本文档只描述当前实现，不提出构建行为修改。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `specs/01-architecture/01-architecture-design/01-build-system/design.md` | 新增编译构建功能域基线设计。 |
| ADDED | `specs/01-architecture/01-architecture-design/01-build-system/Feat-01-build-gn-structure-spec.md` | 新增 BUILD.gn 结构规格。 |
| MODIFIED | `specs/index.md` | 注册 `01-01-01 编译构建` 与 Feat-01。 |
| REMOVED | 无 | 不删除任何现有规格或源码。 |

## 输入文档

- 规格索引：`specs/index.md`
- 设计文档：`specs/01-architecture/01-architecture-design/01-build-system/design.md`
- 新增知识库：`docs/architecture/Ace_Engine_Build_Architecture_Knowledge_Base_CN.md`
- 主要源码定位：
  - `<OH_ROOT>/build.sh`
  - `ace_config.gni`
  - `BUILD.gn`
  - `build/BUILD.gn`
  - `build/ace_lib.gni`
  - `adapter/ohos/build/platform.gni`
  - `adapter/ohos/build/config.gni`
  - `adapter/ohos/build/BUILD.gn`
  - `frameworks/base/BUILD.gn`
  - `frameworks/core/BUILD.gn`
  - `frameworks/bridge/BUILD.gn`
  - `frameworks/bridge/declarative_frontend/BUILD.gn`
  - `frameworks/bridge/arkts_frontend/arkoala_generator/BUILD.gn`
  - `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/BUILD.gn`
  - `interfaces/native/BUILD.gn`
  - `interfaces/napi/kits/BUILD.gn`
  - `interfaces/ets/BUILD.gn`
  - `advanced_ui_component/BUILD.gn`
  - `component_ext/BUILD.gn`
  - `test/unittest/BUILD.gn`
  - `test/benchmark/BUILD.gn`
  - `bundle.json`
- ArkUI-X 参考源码定位：
  - `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/ace_config.gni`
  - `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/platform.gni`
  - `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/config.gni`
  - `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/BUILD.gn`
  - `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/platform.gni`
  - `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/config.gni`
  - `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/BUILD.gn`

## 用户故事

### US-1: 识别平台发现和全局配置

作为 ArkUI 构建维护者，我想要明确 ace_engine 平台列表和全局编译配置的来源，以便新增平台或调整编译开关时能定位正确入口。

- AC-1.1 WHEN 读取 ace_engine 平台列表 THEN 应能追溯到 `ace_config.gni` 中 `ace_platforms` 初始化、adapter 扫描、`platform.gni` 导入和 ArkUI-X 过滤流程，证据为 `ace_config.gni:336-353`。
- AC-1.2 WHEN 读取全局编译配置 THEN 应能追溯到顶层 `BUILD.gn` 的 `ace_config`、`ace_test_config`、`ace_coverage_config`，证据为 `BUILD.gn:18-121`、`BUILD.gn:123-186`。
- AC-1.3 WHEN 判断 part/subsystem THEN 应使用 `ace_config.gni` 中的 `ace_engine_subsystem` 和 `ace_engine_part` 定义，证据为 `ace_config.gni:186-202`。
- AC-1.4 WHEN 从产品构建命令追溯到 ace_engine 构建图 THEN 应能识别 OpenHarmony 根 `build.sh` 的源码根定位、prebuilts 环境配置和 hb build 调用，证据为 `<OH_ROOT>/build.sh:47-55`、`<OH_ROOT>/build.sh:100-123`、`<OH_ROOT>/build.sh:208-214`。

### US-2: 识别主库和框架聚合关系

作为 ArkUI 构建维护者，我想要明确 `libace_compatible`、`libace`、`libace_static_*` 与 base/core/bridge 的依赖关系，以便定位主库构建失败或平台差异。

- AC-2.1 WHEN 读取主库构建入口 THEN `build/BUILD.gn` 应按 `ace_platforms` 为每个平台实例化 `libace_static_<platform>`，证据为 `build/BUILD.gn:20-37`。
- AC-2.2 WHEN 读取 OHOS 分离引擎库 THEN 仅 `current_os == "ohos"` 分支生成 `libace_engine_*`、debug engine、declarative engine 和 PA engine，证据为 `build/BUILD.gn:40-82`。
- AC-2.3 WHEN 读取 `libace_static` THEN 应看到固定 base 依赖，并按 `ohos_ng/is_arkui_x` 选择 NG bridge/core 或旧 bridge/core，证据为 `build/ace_lib.gni:32-75`。
- AC-2.4 WHEN 读取共享库输出 THEN `libace_compatible` 依赖 `libace_static_ohos`，可选 `libace` 依赖 `libace_static_ohos_ng`，证据为 `build/BUILD.gn:142-184`、`build/BUILD.gn:201-228`。

### US-3: 识别前端桥接和生成物依赖

作为 ArkUI 前端构建维护者，我想要明确 declarative、ArkTS static、JS 资源和 ABC 生成物如何进入 GN 图，以便修改生成链时不破坏增量构建。

- AC-3.1 WHEN 读取 bridge 构建入口 THEN 应能区分旧 bridge 和 NG bridge 模板及其依赖，证据为 `frameworks/bridge/BUILD.gn:18-56`、`frameworks/bridge/BUILD.gn:60-91`。
- AC-3.2 WHEN 读取 declarative 前端构建 THEN 应能看到 NG/旧 frontend source 的选择和 JS 资源 `action`/`gen_obj` 链，证据为 `frameworks/bridge/declarative_frontend/BUILD.gn:24-82`、`frameworks/bridge/declarative_frontend/BUILD.gn:111-187`。
- AC-3.3 WHEN 读取 static ArkTS 生成链 THEN 应能看到 SDK patch、generation.py、`idlize_gen`、`components_compile_abc` 和 `components_abc` 的依赖，证据为 `frameworks/bridge/arkts_frontend/arkoala_generator/BUILD.gn:70-143`、`frameworks/bridge/arkts_frontend/arkoala_generator/BUILD.gn:181-185`、`frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/BUILD.gn:176-195`。

### US-4: 识别接口、扩展组件和验证入口

作为 ArkUI 发布和测试维护者，我想要明确 NDK/NAPI/ANI、扩展组件、单测和 benchmark 如何挂到构建图，以便检查产物缺失或测试目标缺失。

- AC-4.1 WHEN 读取接口包构建 THEN 应能区分 NDK `ace_ndk`、NAPI `napi_group`、ANI `ace_ani_package`，证据为 `interfaces/native/BUILD.gn:17-30`、`interfaces/native/BUILD.gn:37-155`、`interfaces/napi/kits/BUILD.gn:53-101`、`interfaces/ets/BUILD.gn:18-59`。
- AC-4.2 WHEN 读取扩展组件构建 THEN 应能定位高级组件 group 和 component_ext group，证据为 `advanced_ui_component/BUILD.gn:42-89`、`component_ext/BUILD.gn:14-22`。
- AC-4.3 WHEN 读取验证 target THEN 应能定位 `unittest`、`linux_unittest_capi`、`run_linux_unittest_capi`、`benchmark`、`benchmark_linux`，证据为 `test/unittest/BUILD.gn:20-68`、`test/benchmark/BUILD.gn:17-40`。
- AC-4.4 WHEN 读取部件入口 THEN 应能在 `bundle.json` 中定位 `fwk_group`、`service_group` 和 `inner_kits`，证据为 `bundle.json:137-220`。

### US-5: 识别 ArkUI-X adapter 参考构建

作为 ArkUI-X 构建维护者，我想要明确 Android/iOS adapter 如何接入 ace_engine 构建图并输出平台产物，以便分析跨平台构建差异时不会只依据 OpenHarmony 仓内 adapter 下结论。

- AC-5.1 WHEN 读取 ArkUI-X 平台发现 THEN 应能看到 Android/iOS adapter 仅在对应 `target_os` 下声明平台，并通过 `cross_platform_support = true` 接入 ArkUI-X `ace_platforms`，证据为 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/ace_config.gni:332-354`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/platform.gni:16-28`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/platform.gni:16-28`。
- AC-5.2 WHEN 读取 ArkUI-X 平台 config THEN Android config 应声明 `ANDROID_PLATFORM`、`NG_BUILD`、`SK_BUILD_FOR_ANDROID`、`CROSS_PLATFORM` 并指向 `adapter/android/build:libarkui_android`；iOS config 应声明 `IOS_PLATFORM`、`NG_BUILD`、`PANDA_TARGET_IOS`、`SK_BUILD_FOR_IOS`、`CROSS_PLATFORM` 并指向 `adapter/ios/build:arkui_ios`，证据为 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/config.gni:14-64`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/config.gni:14-80`。
- AC-5.3 WHEN 读取 ArkUI-X 主产物 THEN Android 应能定位 `libarkui_android` 对 `libace_static_android`、`ace_kit`、`ace_static_ndk` 等依赖，iOS 应能定位 `arkui_ios` 和组合后的 `libarkui_ios.framework`，证据为 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/BUILD.gn:25-55`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/BUILD.gn:26-97`。
- AC-5.4 WHEN 读取跨平台组件库 THEN 应能区分 OHOS `libarkui_*`、ArkUI-X Android `arkui_*` shared library 和 ArkUI-X iOS `libarkui_*.framework` 的产物形态，证据为 `adapter/ohos/build/BUILD.gn:18-78`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/BUILD.gn:140-202`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/BUILD.gn:256-320`。

## 验收追溯

| AC ID | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 | BR-1, FR-1 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `ace_config.gni:336-353` |
| AC-1.2 | BR-1, FR-2 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `BUILD.gn:18-186` |
| AC-1.3 | BR-1, FR-3 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `ace_config.gni:186-202` |
| AC-1.4 | BR-1, FR-15 | TASK-BUILD-STRUCTURE-2 | 源码审查 | `<OH_ROOT>/build.sh:47-55`, `<OH_ROOT>/build.sh:100-123`, `<OH_ROOT>/build.sh:208-214` |
| AC-2.1 | BR-2, FR-4 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `build/BUILD.gn:20-37` |
| AC-2.2 | BR-2, FR-5 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `build/BUILD.gn:40-82` |
| AC-2.3 | BR-2, FR-6 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `build/ace_lib.gni:32-75` |
| AC-2.4 | BR-2, FR-7 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `build/BUILD.gn:142-228` |
| AC-3.1 | BR-3, FR-8 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `frameworks/bridge/BUILD.gn:18-91` |
| AC-3.2 | BR-3, FR-9 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `frameworks/bridge/declarative_frontend/BUILD.gn:24-187` |
| AC-3.3 | BR-3, FR-10 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `frameworks/bridge/arkts_frontend/arkoala_generator/BUILD.gn:70-185`, `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/BUILD.gn:176-195` |
| AC-4.1 | BR-4, FR-11 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `interfaces/native/BUILD.gn:17-155`, `interfaces/napi/kits/BUILD.gn:53-101`, `interfaces/ets/BUILD.gn:18-59` |
| AC-4.2 | BR-4, FR-12 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `advanced_ui_component/BUILD.gn:42-89`, `component_ext/BUILD.gn:14-22` |
| AC-4.3 | BR-5, FR-13 | TASK-BUILD-STRUCTURE-1 | 源码审查 | `test/unittest/BUILD.gn:20-68`, `test/benchmark/BUILD.gn:17-40` |
| AC-4.4 | BR-4, FR-14 | TASK-BUILD-STRUCTURE-1 | JSON 校验、源码审查 | `bundle.json:137-220` |
| AC-5.1 | BR-6, FR-16 | TASK-BUILD-STRUCTURE-2 | 源码审查 | `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/ace_config.gni:332-354`, `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/platform.gni:16-28`, `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/platform.gni:16-28` |
| AC-5.2 | BR-6, FR-17 | TASK-BUILD-STRUCTURE-2 | 源码审查 | `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/config.gni:14-64`, `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/config.gni:14-80` |
| AC-5.3 | BR-6, FR-18 | TASK-BUILD-STRUCTURE-2 | 源码审查 | `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/BUILD.gn:25-55`, `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/BUILD.gn:26-97` |
| AC-5.4 | BR-6, FR-19 | TASK-BUILD-STRUCTURE-2 | 源码审查 | `adapter/ohos/build/BUILD.gn:18-78`, `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/BUILD.gn:140-202`, `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/BUILD.gn:256-320` |

## 业务规则

- BR-1 全局构建变量、part/subsystem、平台列表必须以 `ace_config.gni` 和顶层 `BUILD.gn` 为入口，不能从单个子模块 BUILD.gn 反推全局构建语义。
- BR-2 主库输出必须经由 `build/BUILD.gn` 和 `build/ace_lib.gni` 的聚合模板描述，不能把 core、bridge、base 的 source_set 当作最终发布库。
- BR-3 前端生成物必须作为 GN target 参与依赖图，declarative JS、Arkoala IDL、static ABC 均需要记录 action/source_set/copy 链路。
- BR-4 接口包、扩展组件和部件入口必须同时检查 BUILD.gn 与 `bundle.json`，其中 `bundle.json` 负责 OpenHarmony 部件分组和 inner kit 元数据。
- BR-5 构建结构验证以可执行目标和构建入口为准，单测/benchmark 入口由 `test/unittest/BUILD.gn` 和 `test/benchmark/BUILD.gn` 定义。
- BR-6 ArkUI-X Android/iOS 构建分析必须查看 ArkUI-X 仓同相对目录下的 `adapter/{android,ios}/build`，不能只依据 OpenHarmony 仓内 `adapter/ohos` 和 `adapter/preview` 判断平台覆盖。

## 功能规则

- FR-1 `ace_platforms` 通过扫描 `adapter/` 并导入各 adapter 的 `platform.gni` 形成，ArkUI-X 仅接受声明 `cross_platform_support` 的平台，见 `ace_config.gni:336-353`。
- FR-2 顶层 `ace_config` 注入 include_dirs、defines、cflags、PGO/coverage/平台差异，见 `BUILD.gn:18-121`。
- FR-3 `ace_engine_subsystem` 固定为 `arkui`；`ace_engine_part` 在 standard system 下为 `ace_engine`，ArkUI-X 下为 `ace_engine_cross`，其他场景为 `ace_engine_full`，见 `ace_config.gni:186-202`。
- FR-4 `build/BUILD.gn` 对每个 `ace_platforms` 项生成 `libace_static_<platform>`，见 `build/BUILD.gn:20-37`。
- FR-5 分离 engine 库只在 OHOS 构建分支生成，且受 `use_build_in_js_engine`、`js_engines`、`have_debug`、`js_pa_support` 控制，见 `build/BUILD.gn:40-82`。
- FR-6 `libace_static` 固定依赖 `frameworks/base:ace_base_$platform`，并按 NG/ArkUI-X 与旧模式选择 bridge/core，见 `build/ace_lib.gni:32-75`。
- FR-7 `libace_compatible` 和可选 `libace` 是共享库输出层；ASan 或未启用 `ace_engine_feature_enable_libace` 时 `libace` 为 fake group，见 `build/BUILD.gn:201-232`。
- FR-8 `framework_bridge` 和 `framework_bridge_ng` 是前端 bridge 聚合模板，并按 `ace_platforms` 实例化，见 `frameworks/bridge/BUILD.gn:18-114`。
- FR-9 declarative 前端通过平台条件选择 NG/旧 source，并通过 `action` 与 `gen_obj` 把 JS 资源纳入 native 构建，见 `frameworks/bridge/declarative_frontend/BUILD.gn:24-187`。
- FR-10 静态 ArkTS 生成链通过 `idlize_gen` 暴露生成依赖，通过 `components_compile_abc` 和 `components_abc` 产出 static ABC，见 `frameworks/bridge/arkts_frontend/arkoala_generator/BUILD.gn:181-185`、`frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/BUILD.gn:176-195`。
- FR-11 NDK、NAPI、ANI 输出分别由 `ace_ndk`、`napi_group`、`ace_ani_package` 聚合，见 `interfaces/native/BUILD.gn:37-155`、`interfaces/napi/kits/BUILD.gn:91-101`、`interfaces/ets/BUILD.gn:18-59`。
- FR-12 高级组件和扩展组件分别由 `advanced_ui_component` 与 `component_ext` group 聚合，见 `advanced_ui_component/BUILD.gn:70-89`、`component_ext/BUILD.gn:14-22`。
- FR-13 单测和 benchmark 分别由 `unittest`、`linux_unittest_capi`、`benchmark`、`benchmark_linux` 等 group/action 聚合，见 `test/unittest/BUILD.gn:20-68`、`test/benchmark/BUILD.gn:23-40`。
- FR-14 `bundle.json` 的 `group_type` 与 `inner_kits` 定义部件级入口和头文件暴露，见 `bundle.json:137-220`。
- FR-15 OpenHarmony 根 `build.sh` 先定位包含 `.gn` 的源码根，再设置 prebuilts Python/Node/OHPM PATH，最后调用 `build/hb/main.py build`，见 `<OH_ROOT>/build.sh:47-55`、`<OH_ROOT>/build.sh:100-123`、`<OH_ROOT>/build.sh:208-214`。
- FR-16 ArkUI-X Android/iOS adapter 在 `target_os` 匹配时声明平台，并以 `cross_platform_support = true` 通过 ArkUI-X `ace_config.gni` 过滤，见 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/ace_config.gni:332-354`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/platform.gni:16-28`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/platform.gni:16-28`。
- FR-17 ArkUI-X Android/iOS 平台 config 通过 defines、feature flags、`platform_deps` 和 `libace_target` 承接平台差异，见 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/config.gni:14-64`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/config.gni:14-80`。
- FR-18 ArkUI-X Android 主产物为 `libarkui_android`，iOS 主产物为 `arkui_ios` 并组合为 `libarkui_ios.framework`，见 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/BUILD.gn:25-55`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/BUILD.gn:26-97`。
- FR-19 OHOS、ArkUI-X Android、ArkUI-X iOS 的组件库打包形态不同：OHOS 使用 `libarkui_*` 共享库，Android 使用 `arkui_*` shared library，iOS 使用 `libarkui_*.framework`，见 `adapter/ohos/build/BUILD.gn:18-78`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/BUILD.gn:140-202`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/BUILD.gn:256-320`。

## 异常/豁免规则

- EX-1 如果 adapter 未导出 `platforms` 或 platform 缺少 `name`，当前 `ace_config.gni` 流程不会把该 platform 加入 `ace_platforms`，见 `ace_config.gni:347-353`。
- EX-2 ArkUI-X 构建下，即使 adapter 声明 platform，也必须满足 `platform.cross_platform_support` 才会加入 `ace_platforms`，见 `ace_config.gni:349-351`。
- EX-3 `current_platform` 只在 `use_mingw_win`、`use_mac`、`use_linux` 场景按 host 类平台赋值，不表示 OHOS 平台选择，见 `ace_config.gni:360-367`。
- EX-4 `framework_bridge` 在 `build_ohos_sdk || is_arkui_x` 时移除 `arkts_frontend` 依赖，见 `frameworks/bridge/BUILD.gn:46-48`；NG bridge 在 ArkUI-X 下也移除该依赖，见 `frameworks/bridge/BUILD.gn:82-84`。
- EX-5 `ace_bridge_engine` 模板断言 `platform` 只能是 `ohos` 或 `ohos_ng`，见 `build/ace_lib.gni:111-112`。
- EX-6 非 ArkUI-X 场景定义 NDK headers 和 `libace_ndk_rom`；ArkUI-X 场景改走 `ace_static_ndk` source_set，见 `interfaces/native/BUILD.gn:17-30`、`interfaces/native/BUILD.gn:157-179`。
- EX-7 ArkUI-X adapter 即使存在于参考仓，也只有在 `target_os` 分别等于 `android` 或 `ios` 时才向 `platforms` 追加平台，见 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/platform.gni:18-28`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/platform.gni:18-28`。
- EX-8 OpenHarmony 仓内 `adapter/ohos/build/platform.gni` 在 `is_arkui_x` 下不会声明 OHOS standard 平台，见 `adapter/ohos/build/platform.gni:19-20`。

## 恢复契约

- RC-1 当新增平台未出现在构建图中时，应先检查 `adapter/<platform>/build/platform.gni` 是否被 `build/search.py` 扫描到、是否导出 `platforms`、是否包含 `platform.name`，对应流程见 `ace_config.gni:338-353`。
- RC-2 当 `libace` 未生成共享库时，应检查 `is_asan` 和 `ace_engine_feature_enable_libace`；条件不满足时当前实现生成 fake group，见 `build/BUILD.gn:201-232`。
- RC-3 当前端生成物缺失时，应检查对应 `action` 的 outputs、deps 与输入文件，例如 state management JS 输出见 `frameworks/bridge/declarative_frontend/BUILD.gn:111-132`，static ABC 输出见 `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/BUILD.gn:176-195`。
- RC-4 当部件打包缺少 framework 或 service 入口时，应检查 `bundle.json` 的 `component.build.group_type`，见 `bundle.json:137-151`。
- RC-5 当 ArkUI-X Android/iOS 平台没有进入构建图时，应先检查对应 `target_os`、`cross_platform_support` 和 `config.gni` 导入是否满足，见 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/platform.gni:18-28`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/platform.gni:18-28`。
- RC-6 当 ArkUI-X 组件库产物缺失时，应按平台检查 `component_modules` 展开和 `libace_target` 指向，Android 见 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/BUILD.gn:140-202`，iOS 见 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/BUILD.gn:256-320`。

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, AC-1.2, AC-1.3 | 源码审查 | 平台发现、全局 config、part/subsystem 来源。 |
| VM-2 | AC-2.1, AC-2.2, AC-2.3, AC-2.4 | 源码审查、目标构建 | 主库聚合与 NG/旧框架分支。 |
| VM-3 | AC-3.1, AC-3.2, AC-3.3 | 源码审查、增量构建 | bridge 模板、JS object、IDL 生成、ABC 输出。 |
| VM-4 | AC-4.1, AC-4.2, AC-4.4 | 源码审查、`python3 -m json.tool bundle.json` | 接口包、扩展组件、部件元数据。 |
| VM-5 | AC-4.3 | 目标构建 | 单测和 benchmark 入口解析。 |
| VM-6 | AC-1.4 | 源码审查 | OpenHarmony 根构建入口、prebuilts 环境和 hb build 调用。 |
| VM-7 | AC-5.1, AC-5.2, AC-5.3, AC-5.4 | 源码审查 | ArkUI-X Android/iOS 平台注入、config、主产物和组件库打包形态。 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| 无 | N/A | 本 Feature 不新增 ArkTS、C API、NAPI 或 ABI。 | AC-1.1 至 AC-5.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| 无 | N/A | AC-1.1 至 AC-5.4 |

## 兼容性声明

- **已有 API 行为变更:** 否。本 Feature 只补录现有 BUILD.gn 结构，不改变 ArkTS、C API、NAPI、ANI 或运行时行为。
- **配置文件格式变更:** 否。不修改 BUILD.gn/gni 或 bundle.json 格式。
- **数据存储格式变更:** 否。
- **最低支持版本:** N/A（内部构建结构补录）。
- **API 版本号策略:** N/A。外部 API 版本不受影响。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 平台发现集中在 `ace_config.gni` | 新平台通过 adapter 的 `platform.gni` 进入 `ace_platforms`，见 `ace_config.gni:336-353`。 | AC-1.1 |
| 根构建入口在 OpenHarmony 根目录 | `build.sh` 负责源码根定位、prebuilts 环境和 hb build 调用，不属于 ace_engine 子目录 BUILD.gn，见 `<OH_ROOT>/build.sh:47-55`、`<OH_ROOT>/build.sh:100-123`、`<OH_ROOT>/build.sh:208-214`。 | AC-1.4 |
| 主库聚合集中在 `build/` | `build/BUILD.gn` 生成共享库和静态聚合 target，`build/ace_lib.gni` 选择 base/core/bridge 依赖，见 `build/BUILD.gn:20-84`、`build/ace_lib.gni:20-131`。 | AC-2.1 至 AC-2.4 |
| 生成物显式声明输入输出 | JS、IDL、ABC 生成均通过 GN target 声明 outputs/deps，见 `frameworks/bridge/declarative_frontend/BUILD.gn:111-187`、`frameworks/bridge/arkts_frontend/arkoala_generator/BUILD.gn:94-143`。 | AC-3.2, AC-3.3 |
| 部件入口由 `bundle.json` 承接 | `bundle.json` 的 `group_type` 和 `inner_kits` 补充 BUILD.gn 以外的部件元数据，见 `bundle.json:137-220`。 | AC-4.4 |
| ArkUI-X 平台差异由 adapter 承接 | ArkUI-X Android/iOS 在参考仓同相对目录下通过 `platform.gni`、`config.gni` 和平台 BUILD.gn 定义平台、宏和产物，见 `<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/platform.gni:16-28`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/config.gni:14-64`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/android/build/BUILD.gn:25-55`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/platform.gni:16-28`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/config.gni:14-80`、`<ARKUI_X_ROOT>/foundation/arkui/ace_engine/adapter/ios/build/BUILD.gn:26-97`。 | AC-5.1 至 AC-5.4 |
| 不修改公共 API 或依赖 | 本补录不新增 BUILD.gn deps、不修改接口签名、不手工编辑 generated 文件。 | AC-1.1 至 AC-5.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不引入新增构建步骤，不改变现有增量构建输入输出。 | 文档差异审查。 | 本次只更新 `design.md` 和 Feat-01 规格文档。 |
| 内存 | 不改变编译器、链接器和生成脚本内存占用。 | 文档差异审查。 | 无 BUILD.gn 变更。 |
| 安全 | 不新增外部依赖、权限或运行时入口。 | 文档差异审查。 | API 变更分析为空。 |
| 可靠性 | 所有构建结构结论可由 file:line 追溯。 | 源码审查。 | 本文 AC、FR、EX、RC 引用现有源码行和 ArkUI-X 参考源码行。 |
| 问题定位 | 根构建入口、主库、前端生成物、接口包、测试入口和 ArkUI-X adapter 均给出定位路径。 | 源码审查。 | US-1 至 US-5。 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不改变运行时无障碍实现。 | N/A |
| 大字体 | 否 | 不改变组件布局和文本行为。 | N/A |
| 深色模式 | 否 | 不改变主题或渲染行为。 | N/A |
| 多窗口/分屏 | 否 | 不改变运行时窗口行为。 | N/A |
| 多用户 | 否 | 不改变运行时账户或数据隔离。 | N/A |
| 版本升级 | 是 | 记录当前构建结构，帮助后续升级保持 target、adapter 和 bundle 入口兼容。 | AC-2.1 至 AC-5.4 |
| 生态兼容 | 是 | NDK/NAPI/ANI、bundle 入口和 ArkUI-X Android/iOS 产物形态不变，补录有助于发布产物核对。 | AC-4.1, AC-4.4, AC-5.3, AC-5.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: BUILD.gn 结构
  作为 ArkUI 构建维护者
  我想要追溯 ace_engine 构建图的入口、聚合和输出
  以便定位构建失败和评估后续构建变更

  Scenario: 平台列表从 adapter 发现
    Given 维护者打开 ace_config.gni
    When 检查 ace_platforms 的赋值过程
    Then 能看到 adapter 目录扫描、platform.gni 导入和 platform.name 过滤
    And ArkUI-X 场景额外要求 cross_platform_support

  Scenario: 根构建入口进入部件构建图
    Given 维护者打开 OpenHarmony 根目录 build.sh
    When 检查源码根定位、prebuilts 环境配置和 hb build 调用
    Then 能看到 build.sh 从包含 .gn 的源码根启动构建
    And 非 ohos-sdk 构建会追加 prebuilt sdk 参数后调用 build/hb/main.py build

  Scenario: 主库聚合选择 NG 或旧框架
    Given 维护者打开 build/BUILD.gn 和 build/ace_lib.gni
    When 检查 libace_static 模板和 libace_compatible/libace 目标
    Then 能看到 libace_static_<platform> 按 ace_platforms 实例化
    And ohos_ng 或 ArkUI-X 分支依赖 NG bridge/core
    And 旧模式分支依赖旧 bridge/core

  Scenario: 前端生成物进入 GN 依赖图
    Given 维护者打开 declarative_frontend 和 arkoala_generator 的 BUILD.gn
    When 检查 action、gen_obj、idlize_gen 和 components_compile_abc
    Then 能看到 JS、IDL 和 static ABC 的 declared outputs
    And dependent target 通过 deps/public_deps 追踪这些生成物

  Scenario: 发布和测试入口可定位
    Given 维护者打开 interfaces、advanced_ui_component、component_ext、test 和 bundle.json
    When 检查 group、shared_library、unittest、benchmark 和 group_type
    Then 能定位 NDK/NAPI/ANI 包、扩展组件、单测、benchmark 和部件入口

  Scenario: ArkUI-X Android 和 iOS adapter 接入构建图
    Given 维护者打开 ArkUI-X adapter/android/build 和 adapter/ios/build
    When 检查 platform.gni、config.gni 和 BUILD.gn
    Then 能看到 Android 和 iOS 按 target_os 注入 cross_platform_support 平台
    And 能定位 libarkui_android、arkui_ios、libarkui_ios.framework 及组件库 package 形态
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/foundation_arkui_ace_engine"
    query: "ace_engine BUILD.gn platform discovery libace_static aggregation"
  - repo: "OpenHarmony/foundation_arkui_ace_engine"
    query: "declarative_frontend arkoala_generator idlize_gen static abc BUILD.gn"
  - repo: "OpenHarmony/foundation_arkui_ace_engine"
    query: "interfaces native napi ets bundle.json unittest benchmark build targets"
  - repo: "ArkUI-X/foundation_arkui_ace_engine"
    query: "adapter android ios platform.gni config.gni libarkui_android arkui_ios component frameworks"
```

**关键文档：** `specs/01-architecture/01-architecture-design/01-build-system/design.md`
