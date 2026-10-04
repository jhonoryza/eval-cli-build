#!/usr/bin/env python3
"""Make Zed's eval-cli authenticate the zed.dev provider.

`headless.rs` builds `Client::production` but never calls `connect`, so the client stays
`SignedOut`. The cloud provider's `is_authenticated` is `!is_signed_out`
(`crates/language_models/src/provider/cloud.rs`), and `authenticate` returns early unless a
sign-in is already in flight, so eval-cli always reports "Provider zed.dev is not
authenticated" no matter how good the credentials on disk are.

This is the same call the editor makes at startup (`crates/zed/src/main.rs`):
`client.connect(true, cx)`, plus a bounded wait for the session before eval-cli inspects the
registry.

Fails loudly if an anchor is missing or ambiguous, so an upstream refactor stops the build
instead of silently shipping an unauthenticated binary.
"""

import pathlib
import sys

EDITS = [
    (
        "crates/eval_cli/src/headless.rs",
        "    let client = Client::production(cx);\n    cx.set_http_client(client.http_client());\n",
        "    let client = Client::production(cx);\n"
        "    cx.set_http_client(client.http_client());\n"
        "\n"
        "    // Establish the Zed session from the stored credentials. eval-cli never connected\n"
        "    // on its own, which left the client SignedOut and every provider unauthenticated.\n"
        "    let connect_client = client.clone();\n"
        "    cx.spawn(async move |cx| {\n"
        "        let _ = connect_client.connect(true, cx).await;\n"
        "    })\n"
        "    .detach();\n",
    ),
    (
        "crates/eval_cli/src/main.rs",
        "            let auth_tasks = cx.update(|cx| {\n",
        "            // The connect spawned in headless.rs runs in the background; give the session\n"
        "            // a chance to come up before asking providers whether they are authenticated.\n"
        "            {\n"
        "                let status = app_state.client.status();\n"
        "                let deadline = Instant::now() + Duration::from_secs(90);\n"
        "                while status.borrow().is_signed_out() && Instant::now() < deadline {\n"
        "                    cx.background_executor()\n"
        "                        .timer(Duration::from_millis(250))\n"
        "                        .await;\n"
        "                }\n"
        "            }\n"
        "\n"
        "            let auth_tasks = cx.update(|cx| {\n",
    ),
]


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    for relative, anchor, replacement in EDITS:
        path = root / relative
        text = path.read_text()
        if replacement in text:
            print(f"already patched: {relative}")
            continue
        count = text.count(anchor)
        if count != 1:
            print(f"{relative}: anchor found {count} times, expected 1", file=sys.stderr)
            print(f"  anchor: {anchor!r}", file=sys.stderr)
            return 1
        path.write_text(text.replace(anchor, replacement))
        print(f"patched: {relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())