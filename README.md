# LangGraph Playground

Jira のエスカレーション済みチケットを読み込み、エスカレーション理由を分類する小さな Python / LangGraph プロジェクトです。

この実装はマルチエージェント構成ではありません。主目的は LangGraph の複雑なエージェント構成を見せることではなく、エスカレーション理由を実用的に分類することです。そのため、分類処理は単一の classifier node に寄せています。

## 分類カテゴリ

- `first_cs_improvable`: First-CS の確認、調査、判断を改善すれば次回対応できる可能性が高い
- `authority_blocked`: 権限、ロール、管理者操作が必要で First-CS だけでは対応できない
- `mixed`: First-CS 側の改善余地と権限不足の両方がある
- `unclear`: 判断に必要な根拠が不足している

## ワークフロー

通常のルールベース分類:

```text
START
  -> extract_evidence
  -> classify_escalation
  -> END
```

LLM を使う場合も、外から見えるワークフローは同じです。`classify_escalation` の中身だけが OpenAI structured output に切り替わります。

```text
START
  -> extract_evidence
  -> classify_escalation
  -> END
```

## プロジェクト構成

```text
.
├── main.py
├── escalation_analysis/
│   ├── graph.py
│   ├── io.py
│   ├── llm.py
│   ├── models.py
│   ├── rules.py
│   └── state.py
├── input/
│   └── .gitkeep
├── output/
│   └── .gitkeep
└── samples/
```

- `main.py`: CLI entry point
- `graph.py`: LangGraph workflow definition
- `rules.py`: ルールベースの分類器
- `llm.py`: OpenAI structured output による分類器
- `models.py`: Pydantic models
- `state.py`: LangGraph state
- `io.py`: JSON input/output

## 実行方法

Git Bash で実行します。

### Jira から入力 JSON を取得

定義済み JQL で Jira からチケットを取得し、`analysis` が扱う入力 JSON を作成します。

```bash
uv run python main.py fetch --project project_a
```

3つの定義済み project をまとめて取得する場合:

```bash
uv run python main.py fetch --project all
```

取得件数を指定する場合:

```bash
uv run python main.py fetch --project project_a --max-results 50
```

出力先を指定しない場合、リポジトリ直下の `input/` に `escalation_analysis_YYYYMMDD_HHMMSS.json` 形式で保存されます。生成された JSON は `.gitignore` で管理対象外になります。

### 更新予定 JSON を作成

入力 JSON を分析し、Jira に追加すべきラベル一覧を JSON ファイルへ書き出します。

```bash
uv run python main.py analysis
```

`fetch` で作成した入力ファイルを指定する場合:

```bash
uv run python main.py analysis \
  --input input/escalation_analysis_20260513_092153.json
```

管理対象のサンプルデータを指定する場合:

```bash
uv run python main.py analysis --sample first_cs_rebuild_missed
```

複数チケットを含む `records` 形式の JSON も指定できます。

```bash
uv run python main.py analysis --sample batch
```

出力先を指定しない場合、リポジトリ直下の `output/` に `escalation_analysis_YYYYMMDD_HHMMSS.json` 形式で保存されます。

node の遷移を確認する場合:

```bash
uv run python main.py analysis \
  --sample first_cs_rebuild_missed \
  --debug
```

LLM で分類する場合:

```bash
uv run python main.py analysis \
  --sample first_cs_rebuild_missed \
  --llm
```

LLM 実行には `.env` に `OPENAI_API_KEY` が必要です。

```env
OPENAI_API_KEY=sk-...
```

### Jira にラベルを書き込み

`analysis` で作成した JSON を使って、Jira にラベルを追加します。

```bash
uv run python main.py apply --input output/escalation_analysis_20260513_092153.json
```

Jira 書き込みには `.env` に `JIRA_BASE_URL` と `JIRA_ACCESS_TOKEN` が必要です。

```env
JIRA_BASE_URL=https://jira.example.local
JIRA_ACCESS_TOKEN=...
```

## 開発メモ

- Python 3.12 を前提にしています
- 依存関係管理には `uv` を使います
- 通常の確認では API token / credit を消費しないルールベース分類を優先します
- LLM を使う検証は、必要な場合だけ `analysis --llm` を付けて最小件数で実行します
