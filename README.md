# eval-cli-build

CI-only repo. Builds Zed's headless agent harness and publishes it as an artifact.

Zed ships [`crates/eval_cli`](https://github.com/zed-industries/zed/tree/main/crates/eval_cli)
in source but never publishes a release binary for it. `eval-cli` runs Zed's real agent
loop (`NativeAgent` + `AcpThread`) without a GUI:

```sh
eval-cli --workdir /repo --model zed/<model> --instruction "..." --output-dir /tmp/run
```

## Build

Trigger `.github/workflows/build.yml`, then download the binary from the rolling
[`latest` release](https://github.com/jhonoryza/eval-cli-build/releases/tag/latest):

```sh
gh release download latest --repo jhonoryza/eval-cli-build -p eval-cli
chmod +x eval-cli
```

Workflow artifacts expire after 90 days; release assets do not, so `latest` is repointed at
every successful build on `main` and its notes record the Zed commit plus the binary's sha256.

The asset is a static `x86_64-unknown-linux-musl` binary, so it runs on any Linux distro.

## Why a repo

This machine cannot build it: Zed pulls in `gpui`, `languages` with `load-grammars`, and the
rest of the editor stack. A GitHub runner has the RAM and disk; this box has 1.9 GiB total.

## Consumers

- `paseo-zed-provider` (planned) — a Paseo provider plugin that drives `eval-cli` as a Paseo
  agent, with the Zed sign-in flow handled in the plugin's Node backend.