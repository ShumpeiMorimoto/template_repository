# Stack kits

Optional pieces for stacks the template core does not assume. Copy what the project needs during bootstrap; the rest disappears with the bootstrap skill. Each kit is a skeleton: replace every `<...>` and run it once before relying on it.

## 1. Server process — smoke workflow

Use when the project runs a long-lived process (API, bot, worker with a health endpoint). Unit tests with mocks pass while the real entry point fails to boot (config read at import time, a broken wire contract), so CI boots it with NO credentials and asserts the contracts everything else depends on.

`.github/workflows/smoke.yml`:

```yaml
name: Smoke

on:
  workflow_dispatch:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v7
      with:
        enable-cache: true

    - name: Set up Python
      run: uv python install

    - name: Install dependencies
      run: uv sync --locked

    - name: Boot the real entry point (no credentials, scratch state)
      env:
        <STATE_DIR_ENV_VAR>: /tmp/app-state
      run: |
        <start command> &
        echo $! > server.pid

    - name: Wait for health
      run: |
        for i in $(seq 1 30); do
          if curl -fsS <health URL> > /tmp/health.json; then exit 0; fi
          sleep 1
        done
        echo "not healthy within 30s"
        exit 1

    - name: Assert the contracts everything depends on
      run: |
        <assert the health payload>
        <exercise the main create / connect path>
        <assert bundled data loads>

    - name: Stop
      if: always()
      run: |
        if [ -f server.pid ]; then kill "$(cat server.pid)" || true; fi
```

Rule that comes with it: anything needing a credential fails at request time, never at import time.

## 2. JS without a build step — syntax gate

Use when the UI is plain ES modules served as files (no bundler, no type checker): a syntax error is otherwise found only in the browser. Plain `node --check file.js` parses the file as CommonJS and exits 0 on an ES module with a syntax error; the stdin form with `--input-type=module` is the one that parses it.

Use the SAME command in the commit hook (`.claude/hooks/check-lint.sh`, over the staged files) and in CI, and recurse into subdirectories in both:

```bash
git ls-files '<ui_dir>/**/*.js' '<ui_dir>/*.js' | while IFS= read -r f; do
  node --input-type=module --check < "$f" || { echo "syntax error: $f"; exit 1; }
done
```

## 3. Static files served by the app — no hand-maintained cache busting

Use when the app serves its own JS / CSS. Version query strings (`app.js?v=12`) are a hand-maintained list: a split or renamed file leaves a stale version and browsers keep old code. Serve static assets with `Cache-Control: no-cache` plus ETag revalidation, and pin it with two tests:

- a scan of the static tree that fails on `\.(js|css)\?v=` (skip vendored directories);
- a request test: the asset has `cache-control: no-cache`, and a second request with `If-None-Match` returns 304.
