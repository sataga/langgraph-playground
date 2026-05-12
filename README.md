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
└── tickets/
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

```bash
uv run python main.py
```

入力ファイルを指定する場合:

```bash
uv run python main.py --input tickets/sample_escalated_first_cs_rebuild_missed.json
```

node の遷移を確認する場合:

```bash
uv run python main.py --debug
```

LLM で分類する場合:

```bash
uv run python main.py --llm
```

LLM 実行には `.env` に `OPENAI_API_KEY` が必要です。

```env
OPENAI_API_KEY=sk-...
```

## 開発メモ

- Python 3.12 を前提にしています
- 依存関係管理には `uv` を使います
- 通常の確認では API token / credit を消費しないルールベース分類を優先します
- LLM を使う検証は、必要な場合だけ `--llm` を付けて最小件数で実行します
