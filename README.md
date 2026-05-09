# LangGraph Playground

Jira エスカレーション自動分析エージェントを小さく学びながら作るための実験用プロジェクトです。

## Step 1: LLM なしの最小グラフ

現在の `main.py` は、ダミー Jira チケット 1 件を LangGraph で処理します。

流れは次の通りです。

```text
START
  -> extract_evidence
  -> score_knowledge_gap
  -> score_authority_blocked
  -> judge_category
  -> assign_label
  -> END
```

実行:

```bash
uv run python main.py
```

Node の移り変わりを確認:

```bash
uv run python main.py --debug
```

この段階では OpenAI API や職場データは使いません。まず Node、Edge、State の感覚を掴むため、キーワードベースで `knowledge_gap` / `authority_blocked` / `mixed` / `unclear` を分類します。

次のステップでは、`score_knowledge_gap` と `score_authority_blocked` を LLM 判定ノードへ差し替えます。
