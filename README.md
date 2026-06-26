# ArkUI Specs

ArkUI Specs 是 ArkUI `ace_engine` 特性规格仓库，用于维护功能域、特性规格、索引和 HostPreview 规格用例。

## 目录

```text
arkui-specs/
├── 01-architecture/          # 架构通用设计规格
├── 03-engine-framework/      # 引擎框架层规格
├── 04-common-capability/     # 通用能力层规格
├── 05-ui-components/         # 组件层规格
├── registry/                 # 功能域与特性注册表
├── tools/                    # 索引与站点生成工具
├── site/                     # Docusaurus 站点工程
├── spec-test/                # HostPreview 规格用例工程
├── previewer/                # Previewer 完整包归档
└── index.md                  # 生成的规格总索引
```

## 规格索引

规格总入口是 [index.md](index.md)。该文件由 `registry/` 生成，不应手动编辑。

注册表：

- [registry/functions.yaml](registry/functions.yaml)：功能域 FuncID 源数据
- [registry/features.yaml](registry/features.yaml)：特性 FeatID 源数据

修改注册表或规格路径后执行：

```bash
python3 tools/generate_index.py
python3 tools/generate_index.py --check
python3 tools/generate_site.py
```

## HostPreview 规格用例

`spec-test/` 是可运行的 HostPreview + Inspector 规格用例工程，用于验证 ArkUI 行为并生成 case 级报告和汇总报告。

详细说明见：

- [spec-test/README.md](spec-test/README.md)
- [spec-test/docs/HostPreview_Test_Framework_Design.md](spec-test/docs/HostPreview_Test_Framework_Design.md)

基本运行：

```bash
cd spec-test
./tools/host_preview/run_feature.sh --openharmony-root /path/to/openharmony
```

按 suite 或 case 运行：

```bash
./tools/host_preview/run_feature.sh --suite-id suite-01-width-height-basic --openharmony-root /path/to/openharmony
./tools/host_preview/run_feature.sh --case-id case-001-width-height-basic --openharmony-root /path/to/openharmony
```

## Previewer 完整包

仓库提供 Previewer 完整包归档：

```text
previewer/previewer-20260625.tar.gz
```

该文件通过 Git LFS 管理。首次拉取仓库后如本地没有实际内容，执行：

```bash
git lfs pull
```

开箱即用流程：

```bash
mkdir -p previewer/runtime
tar -xzf previewer/previewer-20260625.tar.gz -C previewer/runtime

cd spec-test
PREVIEWER_BIN="$(pwd)/../previewer/runtime/previewer/common/bin" \
./tools/host_preview/run_feature.sh --openharmony-root /path/to/openharmony
```

`PREVIEWER_BIN` 指向包含 `Previewer` 和 `PreviewerCLI` 的目录，优先级高于 SDK 和 OpenHarmony 根目录下的 Previewer。

## 环境要求

- Python 3
- OpenHarmony SDK 与 Node，用于构建 `spec-test` HAP
- Git LFS，用于拉取 `previewer/*.tar.gz`
- `Xvfb` / `xvfb-run`，用于 HostPreview 无头显示运行

常见 Xvfb 安装命令：

```bash
# Ubuntu/Debian
sudo apt-get install xvfb

# openEuler/CentOS/RHEL
sudo yum install xorg-x11-server-Xvfb
```

## 站点生成

`site/` 是 Docusaurus 站点工程。站点导航和文档输入由注册表生成。

本地生成站点输入：

```bash
python3 tools/generate_index.py --check
python3 tools/generate_site.py
```

本地构建站点：

```bash
cd site
npm ci
npm run build
```
