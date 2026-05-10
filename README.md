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

Jira チケットの内容を見て、エスカレーション理由を分類する小さな分析エージェントを作ります。

現在は、次の分類を扱います。

- `knowledge_gap`: 既存ドキュメントや調査で解決できた可能性がある
- `authority_blocked`: 権限やロール不足で担当者だけでは解決できなかった
- `mixed`: 知識不足と権限不足の両方の要素がある
- `unclear`: 判断材料が足りない

現時点では OpenAI API や職場データは使いません。まずはダミー Jira チケットとキーワードベースの判定で、LangGraph の基本構造を理解する段階です。

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

次のステップでは、`score_knowledge_gap` と `score_authority_blocked` を LLM 判定ノードへ差し替えます。

まずルールベースでデータの流れを理解してから、LLM に任せる部分を増やしていきます。

## プロジェクト構成

```text
.
├── main.py
├── escalation_analysis/
│   ├── graph.py
│   ├── io.py
│   ├── models.py
│   ├── rules.py
│   └── state.py
└── tickets/
```

`main.py` は CLI の入口です。分析の本体は `escalation_analysis/` に分けています。

- `models.py`: Jira チケットと分析結果のデータ定義
- `state.py`: LangGraph で共有する State の型定義
- `rules.py`: 証拠抽出、スコア計算、分類、ラベル付け
- `graph.py`: LangGraph の Node と Edge の組み立て
- `io.py`: JSON 入出力とダミーチケット

## 実行方法

実行コマンドは Git Bash を前提にしています。

```bash
uv run python main.py
```

JSON ファイルを指定して実行:

```bash
uv run python main.py --input tickets/sample_authority_blocked.json
```

Node の移り変わりを確認:

```bash
uv run python main.py --debug
```

JSON ファイルを指定して Node の移り変わりを確認:

```bash
uv run python main.py --input tickets/sample_authority_blocked.json --debug
```

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
