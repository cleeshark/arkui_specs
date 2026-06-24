# ArkUI Spec Registry

`registry/functions.yaml` is the source of truth for FuncID registration.
`registry/features.yaml` is the source of truth for registered FeatID entries.

Do not register historical candidate feature points here until the corresponding
spec work starts and the feature scope is clear.

Update flow:

1. Add or edit FuncID records in `registry/functions.yaml`.
2. Add or edit FeatID records in `registry/features.yaml` only for formally registered specs.
3. Run `python3 tools/generate_index.py`.
4. Run `python3 tools/generate_index.py --check` before committing.
