# Template feedback log

前プロジェクト（個人用の業務アプリ）からの資産回収の記録。次回の feedback は不採用項目を再提案しない（状況が変わった場合を除く）。

## 2026-10-07 round 1

ハーネス（hooks / settings）、`code-review-expert`、carried-over rules A1–A7、file-size ガード（`.claude/file-size.json` + `tests/test_file_size.py`）。

## 2026-11-22 round 2

### 採用

| 項目 | 分類 | 反映先 |
|---|---|---|
| 1. `review` オーケストレータ（ルーティング表 / 検証 / スキル保守ステップ） | CORE | `.claude/skills/review/SKILL.md` |
| 2. リポジトリルールを汎用レビューアから分離 | CORE | `project-specific-checklist.md` → `.claude/skills/review/references/project-rules.md`（git mv）、`code-review-expert` 3i を汎用化 |
| 3. `code-review-expert` 更新（Module split candidates、汎用化された例ほか） | CORE | `.claude/skills/code-review-expert/` |
| 4. 新 carried-over rules A8–A11（キャッシュ失効のリクエスト内再取得 / UI 1テーマのみ・複製・未描画 / 「念のため」の死蔵コード / レビュー器具のドリフト）。事故ルールは A12+ へ繰り下げ | CORE | `project-rules.md`, CLAUDE.md, bootstrap |
| 5. スキル参照ガードテスト | CORE | `tests/test_skill_references.py` |
| 6. CLAUDE.md 規約（/review 起点、死コード削除、テスト命名、`.scratch/`、保持ルール） | CORE | `CLAUDE.md`, `.gitignore` |
| 7. README「Project Status」節 | CORE | `README.md`, bootstrap |
| 8. 未使用スキル `professional-doc-architect` の撤去 | 削除 | skill dir, bootstrap, README |
| 9. `harvest` スキルの同梱、bootstrap で残す/消すスキルを明記 | CORE | `.claude/skills/harvest/`, bootstrap |
| 10. 本ログ | CORE | `dev-docs/HARVEST_LOG.md` |
| ui-review キット（並行変更で追加） | STACK-KIT | `.claude/skills/ui-review/`（UI が無ければ bootstrap で削除） |

### 不採用

| 項目 | 理由 |
|---|---|
| アプリコード（検索コンボボックス / 数値タイル / ログ保持モジュール） | 実装ではなくパターンをルール化（A9 / 保持ルール）で足りる |
| フロントエンドのテーマトークン・テーマ parity テスト | スタック依存 → ui-review キット側で扱う。テンプレート core にはしない |
| 前プロジェクトのドメインルール（データ鮮度、売買エンジン不変条件、定量研究ルール） | PROJECT-ONLY |
| 前プロジェクトの hooks | テンプレートの hooks が既に新しい汎用版 |
| 事故の経緯（日付・件数・固有名） | メカニズムだけ A8–A11 に抽出。物語は持ち込まない |
