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

## 2026-11-22 round 3（pull mode: テンプレート側から兄弟プロジェクト3件を棚卸し）

基準点（次回の pull はここから差分を見る）: プロジェクトA（ビルド無し JS のシミュレーション）`7485275` / プロジェクトB（FastAPI + WebSocket + 素の ES modules のサーバーアプリ）`3a41299` / プロジェクトC（設計フェーズ、コード無し）`aa799e8`。ソース側リポジトリには何も書いていない。ほかの兄弟リポジトリ（旧テンプレ派生・練習用・単一スクリプト）は回収対象なし。

### 採用

| 項目 | 出所 | 分類 | 反映先 |
|---|---|---|---|
| 1. エージェント規律フック v2（`[OPUS: reason]` タグ必須、フッターにトークン節約 / 約80回で引き継ぎ / 自分の PID だけ停止 / 作業ツリーを動かす git 禁止 / ネットワークで個人情報を送らない） | A | CORE | `.claude/hooks/require-agent-model.py`, `CLAUDE.md`, `review` スキル |
| 2. 返答言語の Stop フック + `"language"` 設定 | A | CORE | `.claude/hooks/require-japanese.py`, `.claude/settings.json`, bootstrap（日本語以外なら削除） |
| 3. `.mcp.json` の Read deny（トークン直書きの実例あり） | B, C | CORE | `.claude/settings.json` |
| 4. secret フックに JWT 形式を追加 | B | CORE | `.claude/hooks/check-secrets.sh` |
| 5. `node_modules/` | A | CORE | `.gitignore` |
| 6. carried-over rules A12–A18（キャッシュのキーが書き込み経路の片方だけ / 実装の定数を写した自己確認テスト / 同じ問いに2つの述語 / 確定前の値への検査 / 失敗を通常の戻り値で返す / 従量課金呼び出しの reserve→commit→release / CWD 相対の書き込み状態）。事故ルールは A19+ へ繰り下げ | A, B | CORE | `project-rules.md`, `CLAUDE.md`, bootstrap, `review` |
| 7. A1 追補（旧コード比較は worktree / テスト選択は grep で）、A5 追補（新しいガードは実データで発火回数を数える） | A | CORE | `project-rules.md` |
| 8. 汎用チェックリスト行: NaN 伝播、不在からの推論・分割/複製・ロールバック後の ID 再利用・引数を並べ直すラッパー、マシン状態依存テスト、開発機の資格情報/状態に依存するテスト、不変条件と監視値の分離、URL クエリの資格情報・生の例外文・denylist ペイロード、バックグラウンドタスクの参照/失敗ログ/取消 | A, B | CORE | `code-review-expert/references/`（code-quality / testing-quality / security / observability） |
| 9. 進め方: 最小の見える核を先に作る（A と C で独立に同じ教訓）、見積もりは実測から、一括削除の前にタグ | A, C | CORE | `CLAUDE.md` |
| 10. タスク台帳の構成（進行中 / 確定済みの判断、計画はファイルに置く） | A, C | CORE | `dev-docs/README.md` |
| 11. UI: 状態変化のトランジション、後出しパネルの高さ予約、`[hidden]` が `display:` に負ける、ヘッドレスの reduced-motion | B | STACK-KIT | `.claude/skills/ui-review/SKILL.md` |
| 12. スタックキット: サーバーの smoke ワークフロー、ビルド無し JS の構文ゲート、静的ファイルの no-cache ガード | B | STACK-KIT | `.claude/skills/bootstrap-project/references/stack-kits.md` |
| 13. `harvest` に pull mode を追記 | — | CORE | `.claude/skills/harvest/SKILL.md` |
| 14. lint フックも `--no-verify` でバイパス可（secret フックと揃える） | B, C | CORE | `.claude/hooks/check-lint.sh` |
| 15. 承認済みの作業内の選択は推奨案を採って止まらない | A | CORE | `CLAUDE.md` |
| 16. 未使用スキル `drawio` の撤去（3件とも使用形跡なし） | A, B, C | 削除 | skill dir, bootstrap, README |
| 17. secret フックの誤検知修正: コードファイルでは「名前=値」検査をしない（引用符なしの右辺は式であり、リテラルは元々対象外） | 検証中に発見 | 修正 | `.claude/hooks/check-secrets.sh` |

### 不採用

| 項目 | 理由 |
|---|---|
| secret フックへの `DATABASE_URL` 追加 | 秘密を含まない値（ローカル DB の URL）やドキュメントの例示が多く、名前だけの検査では誤検知が増える |
| 自動隔離フィクスチャ（資格情報 env の除去・状態ディレクトリ差し替え） | 状態ディレクトリとシングルトンがプロジェクト固有。`allow_network` の統合テストと衝突する。チェックリスト行で扱う |
| 生成物の再ビルドフック、Node の CI ジョブ、Dockerfile / `.dockerignore` | 該当スタックでしか使えず、必要時に書く方が安い（Dockerfile は品質面の注意点もあり） |
| テスト環境と本番ランタイムでデータ表現が違う | 「実際のエントリポイントで動かす」検証ルールで足りる |
| 完了判定の分母（全員回答待ち） | ドメイン色が強く、汎用化すると A14 と重なる |
| パイロットの合否基準、スキーマ凍結とマイグレーション、後回しインフラ表、試作置き場の規約、乱数シード固定フィクスチャ | 設計段階の計画であって事故の裏付けが無い / テンプレートは最初から一式を同梱している |
| サブエージェントへのバッチ投入・プロンプトキャッシュ維持 | 大量コンテンツ生成に限った話 |
| デザインブリーフ必須、効果音、ゲーム固有の UI 規則 | PROJECT-ONLY |
| 各プロジェクトのドメイン規則・事故の経緯・領域別 `CLAUDE.md`・テストスイート用ランナー群 | PROJECT-ONLY |
| 3件の旧 hooks / 旧 `code-review-expert` | テンプレート側が新しい（差分はテンプレートの改善のみ） |
