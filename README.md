# LangGraph Playground

Jira エスカレーション自動分析エージェントを、小さなステップで学びながら作るための実験用プロジェクトです。

目的は、いきなり本格的な AI エージェントを作ることではありません。まずは LangGraph の基本である Node、Edge、State の感覚を掴み、少しずつ LLM 判定や外部連携へ広げていきます。

## このリポジトリで学ぶこと

- LangGraph で処理の流れをグラフとして組み立てる
- typed state を使って、ノード間で受け渡すデータを明確にする
- Pydantic で入力データと分析結果の形を定義する
- 小さなルールベース実装から始めて、後から LLM ノードへ置き換える
- `main.py` を薄く保ち、分析ロジックを役割ごとのモジュールに分ける

## 作ろうとしているもの

エスカレーション済みの Jira チケットの内容を見て、そのエスカレーション理由を分類する小さな分析エージェントを作ります。

現在は、次の分類を扱います。

- `knowledge_gap`: 次回からは一次受付で対応できる見込みがある
- `authority_blocked`: 権限やロール不足で一次受付だけでは解決できなかった
- `mixed`: 知識不足と権限不足の両方の要素がある
- `unclear`: 判断材料が足りない

現在は、ダミー Jira チケットを使って次の 2 通りの実装を試せます。

- ルールベース版: キーワード判定で分類する
- LLM 使用版: OpenAI API を使ってチケット本文を解析し、Pydantic の結果形式で受け取る

職場データは使いません。まずはサンプル JSON で、LangGraph の基本構造と LLM ノードの差し替え方を理解する段階です。

## 学習ステップ

### Step 1: LLM なしの最小グラフ

ダミー Jira チケット 1 件を LangGraph で処理し、キーワードベースで分類します。

現在のグラフの流れは次の通りです。

```text
START
  -> extract_evidence
  -> score_knowledge_gap
  -> score_authority_blocked
  -> judge_category
  -> assign_label
  -> END
```

### Step 2: LLM 判定ノードへ置き換える

`--llm` を付けると、`score_knowledge_gap`、`score_authority_blocked`、`judge_category`、`assign_label` の代わりに、LLM 判定ノード `analyze_with_llm` を使います。

LLM 使用版の流れは次の通りです。

```text
START
  -> extract_evidence
  -> analyze_with_llm
  -> END
```

LLM の出力は `AnalysisResult` に合わせた structured output として受け取り、`category`、`label`、`confidence`、`reason`、`evidence` を返します。
まずルールベースでデータの流れを理解してから、同じ入力を LLM 版で実行して結果の違いを見ると学びやすいです。

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

`main.py` は CLI の入口です。分析の本体は `escalation_analysis/` に分けています。

- `models.py`: Jira チケットと分析結果のデータ定義
- `state.py`: LangGraph で共有する State の型定義
- `rules.py`: 証拠抽出、スコア計算、分類、ラベル付け
- `llm.py`: OpenAI API を使った LLM 判定ノード
- `graph.py`: LangGraph の Node と Edge の組み立て
- `io.py`: JSON 入出力とダミーチケット

## LLM 使用版の準備

LLM 使用版を動かすには OpenAI API key が必要です。ChatGPT Plus とは別に、OpenAI Platform 側の API key と API クレジットを使います。

リポジトリ直下に `.env` を作り、次のように API key を保存します。

```env
OPENAI_API_KEY=sk-...
```

`.env` は `.gitignore` に含めています。API key は README、チケット JSON、GitHub issue、チャットなどに貼らないでください。

課金を抑えるため、最初は OpenAI Platform の billing で次の状態にしておくと安全です。

- credit balance は少額から始める
- auto recharge は off にする
- usage をこまめに確認する

デフォルトモデルは `gpt-5-nano` です。分類や要約向けの安価なモデルとして、学習用途の初期値にしています。

## 実行方法

実行コマンドは Git Bash を前提にしています。

```bash
uv run python main.py
```

JSON ファイルを指定して実行:

```bash
uv run python main.py --input tickets/sample_escalated_vm_metadata_corruption.json
```

```bash
uv run python main.py --input tickets/sample_escalated_first_cs_rebuild_missed.json
```

Node の移り変わりを確認:

```bash
uv run python main.py --debug
```

JSON ファイルを指定して Node の移り変わりを確認:

```bash
uv run python main.py --input tickets/sample_escalated_vm_metadata_corruption.json --debug
```

### LLM 使用版を実行

OpenAI API を呼び出す場合は `--llm` を付けます。

```bash
uv run python main.py --llm
```

JSON ファイルを指定して LLM 版を実行:

```bash
uv run python main.py --input tickets/sample_escalated_vm_metadata_corruption.json --llm
```

```bash
uv run python main.py --input tickets/sample_escalated_first_cs_rebuild_missed.json --llm
```

LLM ノードの入出力を確認:

```bash
uv run python main.py --llm --debug
```

モデルを明示して実行:

```bash
uv run python main.py --llm --model gpt-5-nano
```

`--llm` を付けない限り API は呼び出されません。ルールベース版と LLM 版を比較するときは、同じ `--input` に対して両方を実行します。

## Windows 環境構築

このリポジトリでは、ユーザー向けの操作例は Git Bash を前提にします。
一方で、PowerShell も内部確認や Windows 設定で使うため、日本語ファイルが文字化けしにくいように UTF-8 設定を入れておくと扱いやすくなります。

### WinGet の確認

Windows 11 や新しい Windows 10 では、通常 `winget` が利用できます。

```powershell
winget --version
```

`winget` が見つからない場合は、Microsoft Store の「アプリ インストーラー」を更新してください。

### GitHub CLI のインストール

PR 作成や GitHub 操作には `gh` を使います。

```powershell
winget install --id GitHub.cli
```

インストール後は、新しいターミナルを開いて確認します。

```bash
gh --version
gh auth login
```

### ripgrep のインストール

コード検索には `rg` を使います。`grep` より高速で、`.gitignore` も考慮してくれます。

```powershell
winget install --id BurntSushi.ripgrep.MSVC
```

インストール後は、新しいターミナルを開いて確認します。

```bash
rg --version
```

### PowerShell の UTF-8 設定

PowerShell で日本語ファイルを読むときに文字化けを避けるため、profile に UTF-8 設定を追加します。

profile の場所を確認します。

```powershell
$PROFILE
```

profile ファイルがなければ作成して開きます。

```powershell
New-Item -ItemType File -Path $PROFILE -Force
notepad $PROFILE
```

次の内容を追記します。

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$PSDefaultParameterValues["Get-Content:Encoding"] = "utf8"
$PSDefaultParameterValues["Set-Content:Encoding"] = "utf8"
$PSDefaultParameterValues["Add-Content:Encoding"] = "utf8"
$PSDefaultParameterValues["Out-File:Encoding"] = "utf8"
```

profile の読み込み時に `running scripts is disabled on this system` と表示される場合は、現在のユーザーだけ実行ポリシーを変更します。

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

その後、新しい PowerShell を開き直します。
