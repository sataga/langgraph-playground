# リポジトリガイドライン

## 基本方針

- ユーザーとの会話は日本語で行う
- 技術説明も日本語で行う
- 簡潔かつ実践的に回答する
- まず最小構成で動く正常系を完成させる
- 正常系を先に完成させた後、主要な異常系を確認する
- 異常系では、原因が追えるエラーメッセージとログを残す
- premature optimization を避ける
- 修正時は既存コードのスタイルを優先する
- 無関係なリファクタリングをしない

## シェルとトラブルシューティング

- ユーザーは普段 PowerShell ではなく Git Bash を利用している
- Codex の内部作業では、確認プロンプトを減らすため PowerShell を優先して使う
- ユーザーに提示する実行コマンド、README の例、トラブルシューティング手順は Git Bash 前提を優先する
- Git Bash 固有の再現確認が必要な場合のみ Git Bash を使う
- Windows 固有の操作が必要な場合のみ PowerShell の例をユーザー向けに補足する
- Python 実行や依存関係操作は `uv` を優先する
- Codex の内部確認で Git Bash が権限確認を繰り返す場合、読み取り専用の調査には PowerShell を使ってよい
- その場合でも、ユーザーに提示する実行コマンドや手順は Git Bash 形式を優先する

Git Bash での基本コマンド:

```bash
uv run python main.py
uv run python -m pytest
```

## プロジェクト構成とモジュール整理

このリポジトリは小規模な Python 3.12 プロジェクトです。現在のエントリーポイントはリポジトリルートの `main.py` です。プロジェクトメタデータは `pyproject.toml` にあり、Python バージョンは `.python-version` で固定されています。

プロジェクトが大きくなったら、テストファイルは `tests/` ディレクトリに配置してください。アプリケーションが単一スクリプトを超えて成長した場合は、再利用可能なコードを `langgraph_playground/` のようなパッケージディレクトリへ移し、`main.py` は薄い CLI または起動用ラッパーとして保ちます。

## ビルド、テスト、開発コマンド

- `uv run python main.py`: 現在のアプリケーションエントリーポイントを実行します
- `uv add <package>`: 依存関係を追加します
- `uv run python -m pytest`: pytest 追加後にテストを実行します

未宣言のパッケージを import するのではなく、依存関係は `pyproject.toml` に追加してください。

## コーディングスタイルと命名規則

コード、識別子、コメントは英語で記述します。標準的な Python スタイルを使用します。インデントは 4 スペース、関数と変数は `snake_case`、クラスは `PascalCase`、定数は大文字の名前にしてください。

公開関数やモジュール境界をまたぐコードには、型ヒントを優先して付けてください。テストからモジュールを import しやすいように、副作用のある処理は `if __name__ == "__main__":` の下に置きます。

## Python

- `uv` を使用する
- Python 3.12 を前提とする
- `pydantic` と typed state を優先する
- dataclass より pydantic model を優先する
- 過剰な抽象化を避け、シンプルで読みやすい実装を優先する

## LangGraph / LLM 実装方針

- LLM/API 呼び出しは token とクレジットを消費するため、必要最小限にする
- 通常の動作確認では `--llm` を付けず、ルールベース版や fake、mock、compile check を優先する
- どうしても実 API の疎通や LLM 出力確認が必要な場合だけ、理由を明確にして `--llm` で検証する
- 実 API を使う検証は最小件数、短い入力、安価なモデルで行う
- 小さな node に分割し、1 node 1 responsibility を優先する
- prompt は関数や定数として分離する
- state mutation は最小限にし、暗黙的な state 更新を避ける
- graph の分岐条件は明示的に書く
- structured output を優先し、LLM 出力は pydantic で検証する
- retry で問題を隠蔽しない
- failure reason をログへ残す
- magic number や hidden rule を避ける

## OpenAI / LangChain 方針

- 不要な LangChain abstraction を増やさない
- まず OpenAI SDK と LangGraph を優先する
- 本当に必要になるまで callback や custom middleware を増やさない
- prompt chain より状態遷移を重視する
- wrapper を増やしすぎず、小規模ではシンプルな構成を維持する

## ログ方針

- `print` より `logging` を優先する
- node の開始と終了をログへ出力する
- エラー時は context を含める
- LLM 入出力は必要に応じて確認可能にする
- API key、secret、`.env` の値はログへ出力しない

## テスト方針

まだテストフレームワークは設定されていません。テストを追加する場合、プロジェクトで別のフレームワークを採用しない限り `pytest` を使用してください。テストは `tests/` 配下に置き、ファイル名は `test_*.py` にします。

テストでは、グラフの振る舞い、状態遷移、外部連携を重点的に確認します。まず正常系を優先してテストし、その後に入力不備、外部 API 失敗、LLM 出力不正など主要な異常系を追加します。node 単位でテスト可能にし、ユニットテストでは実 API や LLM を呼び出さず、fixture、fake、mock を使用してください。

## コミットとプルリクエストの方針

このリポジトリにはまだコミットがないため、既存のコミット規約はありません。コミットメッセージは `Add graph runner entry point` や `Configure pytest` のように、簡潔で命令形の文にしてください。

プルリクエストには、短い概要、変更理由、テスト結果、セットアップや設定に関する注意点を含めてください。関連 issue がある場合はリンクします。

## セキュリティと設定の注意

シークレット、API キー、値が入ったローカル環境ファイルはコミットしないでください。`.env` はローカル専用として扱い、バージョン管理に含めません。必要がある場合でも、値ではなく環境変数名だけを参照してください。

仮想環境、ビルド成果物、キャッシュはバージョン管理に含めません。`.gitignore` には少なくとも `.env`、`.venv/`、`__pycache__/`、`.pytest_cache/` を含めます。

ファイル削除や破壊的操作の前には確認してください。

## 推奨ライブラリ

優先度:

1. standard library
2. pydantic
3. OpenAI SDK
4. LangGraph
5. 必要最低限の追加ライブラリ

依存関係は最小限に保ちます。

## 非推奨

- 巨大 node
- 過剰 abstraction
- hidden side effect
- implicit state mutation
- premature optimization
- unnecessary async
- unnecessary design pattern
- deeply nested graph
- 巨大 prompt に全責務を押し込む設計

## PR 作成方針

- PR のタイトルと本文は日本語で作成する
- PR 本文には、変更概要、変更理由、テスト結果、セットアップや設定の注意点を含める
- テスト結果には、実際に実行したコマンドと得られた主要ログを可能な限り記載する
- LLM/API を使った検証を行った場合は、実行コマンド、対象入力、結果概要、token/credit 消費に関する注意を記載する
- LLM/API を使わずに検証した場合も、その理由と代替確認方法を記載する
