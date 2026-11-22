---
name: init-project
description: "テンプレートから作った新規プロジェクトで最初に一度だけ実行する初期化。git / remote の整理、harvest の基準点記録、パッケージ名・プロジェクト名・作者の置換、CLAUDE.md / README / review ルーティング / file-size の穴埋め、テンプレート専用ファイルの削除、ロック再生成、検証までを一括で行い、最後にこのスキル自身を削除する。「このテンプレートで新しいプロジェクトを始めて」「プロジェクトを初期化して」「init して」「プロジェクト名を設定して」と言われたら使う。"
---

# Init Project

このリポジトリはテンプレートから作られた直後の状態。プレースホルダが複数ファイルに散っているので、手で直すと取りこぼす（A6: scattered registration）。この手順を上から順に実行し、最後に残骸ゼロを grep で証明する。テンプレート自身（`template_repository`）の中では実行しない — 手順 0 で止まる。

## 0. 前提を確認する

```bash
git rev-parse --show-toplevel 2>/dev/null || echo "NO GIT"
git remote -v
git log --oneline -1
basename "$(pwd)"
uv --version
```

- カレントが `template_repository` そのものなら**中止**して報告する（テンプレートを初期化すると全プロジェクトの出発点が壊れる）。
- git が無い（フォルダをコピーした）: `git init -b main`。
- `origin` がテンプレートのリポジトリを指している（clone した）: `git remote remove origin`。新しいリモートの作成・push は外部公開なのでユーザーに指示されたときだけ。
- `uv` が無ければ README の Install uv を案内して止まる。Python 本体は不要（`uv sync` が `.python-version` の版を自動取得する）。
- `.venv/` が既にあるなら削除する（フォルダごとコピーした場合、中身はテンプレート用: `pyvenv.cfg` の `prompt = your-package-name`、`Scripts/*.exe` に旧パスが埋め込まれている）。手順 6 の `uv sync` が作り直す。

## 1. 入力を確定する（不明なものだけ質問する）

| 項目 | 例 | 既定値 |
|---|---|---|
| プロジェクト表示名 | `Receipt Scanner` | フォルダ名から生成して確認 |
| 配布名 (kebab-case) | `receipt-scanner` | 表示名から生成 |
| パッケージ名 (snake_case) | `receipt_scanner` | 配布名から生成 |
| 一行説明 | — | — (必須) |
| コア成果（1文） | 「レシート写真から月別支出 CSV が出る」 | — (必須。CLAUDE.md の Smallest visible core) |
| 作者名 / email | — | `git config user.name` / `user.email` |
| GitHub ユーザー名 | — | `gh api user -q .login`（失敗したら質問） |
| ライセンス | MIT / なし（非公開） | MIT |
| 追加の技術スタック | FastAPI, React など | なし |
| UI の有無 | — | なし |
| 会話言語 | — | 日本語 |

## 2. harvest の基準点を記録する

`harvest`（完了時にテンプレートへ資産を戻す）は `.claude/harvest.json` の `last_feedback_commit` 以降の差分を見る。テンプレートの履歴を引き継いでいると、初回 harvest がテンプレート自身の中身を「このプロジェクトの成果」として再提案してしまう。

- 履歴を引き継いでいる（`git log` にテンプレートのコミットがある）: その時点の `HEAD` を記録する。
- 履歴が無い / 新規 `git init`: 記録不要（初回 = 全履歴で正しい）。
- テンプレートが `../template_repository` 以外にあるなら `template_path` も書く。

```json
{ "last_feedback_commit": "<HEAD sha>", "last_feedback_date": "<今日>", "template_path": "<省略可>" }
```

## 3. 置換する

```bash
git mv src/your_package src/<pkg>
```

次の置換を **grep で見つかった全ファイル** に適用する（`.venv/`, `.git/`, `uv.lock` は除外。uv.lock は手順 6 で再生成）:

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

ライセンス「なし」なら `LICENSE` を削除し、README のバッジと License 節、`pyproject.toml` の `license` を消す。

## 4. テンプレート専用ファイルを消す

- `dev-docs/HARVEST_LOG.md`（テンプレートが受け取った資産の記録。harvest はテンプレート側に書くので、プロジェクトには不要）と、`dev-docs/README.md` のその行。
- README の `Contributing` 節（個人プロジェクト。外部貢献を受けるなら残す）。
- UI が無い: `.claude/skills/ui-review/` を削除し、`review` のルーティング表から `ui-review` の行（コメント例を含む）と README の該当行を消す。
- 会話言語が日本語以外: `.claude/hooks/require-japanese.py`、`.claude/settings.json` の `Stop` フックと `"language"` を削除し、`CLAUDE.md` の Language 行を直す。
- **残すスキル**: `harvest`、`review`（+ `code-review-expert`）は必ず残す。

## 5. 中身を埋める

- `CLAUDE.md`: 先頭の `<!-- TEMPLATE: ... -->` を削除。Tech Stack / Naming / Domain Knowledge の `<...>` を埋めるか行ごと削除。
- **コード構成を決める（必須）**: 採用スタックに合わせて `CLAUDE.md` の `## Code organization` 直下に次を書く。(1) 初期ディレクトリ/モジュール構成、(2) 「新しいコードの置き場所」表（機能種別 → ディレクトリ/ファイル）、(3) モジュール機構（このスタックでファイル同士がどう import / 登録し合うか。例: Python は package + `__init__.py`、素の JS は script 読み込み順 / ES modules、など）。
- `.claude/file-size.json` の `max_bytes` / `max_lines` / `include` / `exclude` / `doc_globs` をスタックに合わせる（既定は Python 向け: 49152 B / 600 行 / doc 40960 B。長行になりがちな言語は行数を 0 にしてバイトだけで測る）。`tests/file_size_allow.json` は `{}` のまま。
- `README.md`: Features / Usage / Roadmap をプロジェクトに合わせるか削除。`AI-assisted development` 節は残し、表の `init-project` 行を消す。`## Project Status` を `active — <現状>` で埋める。
- `dev-docs/PROJECT_TODO.md` を作る（形式は `dev-docs/README.md`）。「進行中」の先頭にコア成果の最小版を置く。
- `.claude/skills/review/references/project-rules.md`: タイトルのプロジェクト名だけ置換。A1–A18 は残す（事故ルールは A19+ に追記）。
- **`review` のルーティング表を埋める**: `.claude/skills/review/SKILL.md` の表を採用スタックに合わせる（`src/**` などのパス → `code-review-expert`、独自の不変条件を持つ領域は専門スキル行を追加）。`<area>/**` の例示行は使わなければ削除。UI があるなら `ui-review` のコメント行を有効化する。
- `.env.example`: 必要な環境変数名を並べる（値は空のまま）。
- `tests/test_package_imports.py`（`import <pkg>` だけのスモークテスト）は実テストが入るまで残す。**テストを 0 件にしない**（pytest は 0 件で exit 5 になり CI が落ちる）。
- 技術スタックを足した場合: 依存は `uv add`、開発ツールは `uv add --dev`。フロントエンド等を足したら `.github/workflows/test-build.yml` にジョブを追加。サーバープロセス / ビルド無しの JS / 静的ファイル配信があるなら `references/stack-kits.md` の該当キットを展開する（このスキルと一緒に消えるので、使うものは今コピーする）。

## 6. 検証する

```bash
uv lock && uv sync
uv run ruff check . && uv run ruff format --check . && uv run ty check . && uv run pytest   # file-size / skill-reference ガードを含む
# 残骸ゼロの証明 — 出力が空であること
grep -rnI 'your_package\|your-package-name\|your-repo-name\|yourusername\|Project Name\|Your Name\|your\.email\|HARVEST_LOG' \
  --exclude-dir=.venv --exclude-dir=.git --exclude-dir=init-project .
grep -nE 'YYYY-MM|init-project' README.md CLAUDE.md
```

grep がヒットしたら直して再実行。全て緑になるまで次に進まない。

## 7. 片付ける

- このスキルのディレクトリ `.claude/skills/init-project/` を削除し、`tests/test_skill_references.py` の `SKIPPED_SKILLS` から `init-project` を外す（初期化は一度きり）。外した後にもう一度 `uv run pytest`。
- コミットはユーザーに指示されたときだけ。
- 最後に、変更したファイル一覧、手順 0 で行った git / remote の操作、埋めずに残した `<...>` 箇所をユーザーに報告する。
