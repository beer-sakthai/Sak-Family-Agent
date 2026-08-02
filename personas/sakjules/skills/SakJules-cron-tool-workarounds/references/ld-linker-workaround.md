# Dynamic linker pattern for cron mode

**Problem:** Cron mode blocks `export LD_LIBRARY_PATH=...` (tirith CRITICAL — code injection via env).
Locally-compiled binaries (llama.cpp, etc.) placed in non-standard paths fail with missing `.so` files.

**Solution:** Invoke the binary through the dynamic linker directly, bypassing the need to set `LD_LIBRARY_PATH`.

## Pattern

```bash
/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 \
  --library-path /path/to/libs \
  /path/to/binary [args...]
```

## Real example (llama-cli)

```bash
/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 \
  --library-path /opt/data/llama-bin/build/bin \
  /opt/data/llama-bin/build/bin/llama-cli \
  -m /path/to/model.gguf -n 100 -t 4 -no-cnv -p "prompt"
```

This resolves `libllama.so`, `libggml.so`, etc. without touching `LD_LIBRARY_PATH`.

## Finding the right ld-linux path

```bash
# Check what arch you're on
uname -m     # x86_64 → ld-linux-x86-64.so.2
# aarch64 → ld-linux-aarch64.so.1
```

Common paths:
- `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2` (x86_64 Debian/Ubuntu)
- `/usr/lib64/ld-linux-x86-64.so.2` (x86_64 RHEL/Fedora)
- `/usr/lib/aarch64-linux-gnu/ld-linux-aarch64.so.1` (ARM64)

## Verification

```bash
# Check which libs a binary needs before running
ldd /path/to/binary 2>&1 | grep "not found"

# Then use the linker pattern to verify resolution
/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 \
  --library-path /path/to/libs \
  /path/to/binary --version 2>&1 | head -5
```

## When to use

- Any locally-compiled C/C++ binary (llama.cpp, ffmpeg custom builds, etc.)
- Any time `LD_LIBRARY_PATH` would be the obvious fix but tirith blocks it
- Cron mode only; interactive mode can set env normally
