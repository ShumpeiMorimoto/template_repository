---
name: bootstrap-project
description: "テンプレートから新規プロジェクトを初期化する。パッケージ名・プロジェクト名・作者の置換、CLAUDE.md の穴埋め、サンプルコードの整理、ロック再生成、検証までを一括で行い、最後にこのスキル自身を削除する。「このテンプレートで新しいプロジェクトを始めて」「プロジェクト名を設定して」「テンプレートを初期化して」と言われたら使う。"
---

# Bootstrap Project

このリポジトリはテンプレート。プレースホルダが複数ファイルに散っているので、手で直すと取りこぼす（A6: scattered registration）。この手順で機械的に置換し、最後に残骸ゼロを grep で証明する。

## 1. 入力を確定する（不明なものだけ質問する）

| 項目 | 例 | 既定値 |
|---|---|---|
| プロジェクト表示名 | `Receipt Scanner` | — (必須) |
| 配布名 (kebab-case) | `receipt-scanner` | 表示名から生成 |
| パッケージ名 (snake_case) | `receipt_scanner` | 配布名から生成 |
| 一行説明 | — | — (必須) |
| 作者名 / email | — | `git config user.name` / `user.email` |
| GitHub ユーザー名 | — | `gh api user -q .login`（失敗したら質問） |
| 追加の技術スタック | FastAPI, React など | なし |
| サンプルコード | 残す / 最小化 | 最小化 |

## 2. 置換する

```bash
git mv src/your_package src/<pkg>
```

次の置換を **grep で見つかった全ファイル** に適用する（`.venv/`, `.git/`, `uv.lock` は除外。uv.lock は手順 4 で再生成）:

| 置換前 | 置換後 |
|---|---|
| `your_package` | `<pkg>` |
| `your-package-name` | `<dist>` |
| `your-repo-name` | `<dist>` |
| `yourusername` | `<github user>` |
| `Project Name` / `<Project Name>` | `<表示名>` |
| `A brief description of your project` / `A brief, compelling description ...` | `<一行説明>` |
| `Your Name` / `your.email@example.com` | 作者名 / email |
| `Copyright (c) 2026` | `Copyright (c) <今年>` |

## 3. 中身を埋める

- `CLAUDE.md`: 先頭の `<!-- TEMPLATE: ... -->` を削除。Tech Stack / Naming / Domain Knowledge の `<...>` を埋めるか行ごと削除。
- `README.md`: Features / Usage / Configuration / Roadmap をプロジェクトに合わせるか削除。`AI-assisted development` 節は残す。
- `.claude/skills/code-review-expert/references/project-specific-checklist.md`: タイトルのプロジェクト名だけ置換。A1–A6 は残す。
- `.env.example`: 必要な環境変数名を並べる（値は空のまま）。
- サンプルコードを最小化する場合: `core.py` / `utils.py` / `examples/example.py` を削除し、`tests/test_core.py` を `import <pkg>` するだけのスモークテストにする。**テストを 0 件にしない**（pytest は 0 件で exit 5 になり CI が落ちる）。
- 技術スタックを足した場合: 依存は `uv add`、開発ツールは `uv add --dev`。フロントエンド等を足したら `.github/workflows/test-build.yml` にジョブを追加。
- 不要なスキル（`drawio`, `professional-doc-architect` など）はユーザーに確認して削除。

## 4. 検証する

```bash
uv lock && uv sync
uv run ruff check . && uv run ruff format --check . && uv run ty check . && uv run pytest
# 残骸ゼロの証明 — 出力が空であること
grep -rnI 'your_package\|your-package-name\|your-repo-name\|yourusername\|Project Name\|Your Name\|your\.email' \
  --exclude-dir=.venv --exclude-dir=.git --exclude-dir=bootstrap-project .
```

grep がヒットしたら直して再実行。全て緑になるまで次に進まない。

## 5. 片付ける

- このスキルのディレクトリ `.claude/skills/bootstrap-project/` を削除する（初期化は一度きり）。
- `git init` 済みでなければ実行。コミットはユーザーに指示されたときだけ。
- 最後に、変更したファイル一覧と、埋めずに残した `<...>` 箇所をユーザーに報告する。
