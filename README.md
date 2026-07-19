# GenAI Skill Assessment

生成AI技術者向けの**証拠ベース・スキル評価フレームワーク**と、個人採点／グループ集計のツールキットです。

「AIという確率的なシステムを、実務要件を満たす決定論的なシステムへ組み上げる能力」（Architect Track）を、成果物の再現性に基づいて測ります。

## ドキュメント

| ファイル | 内容 |
|---------|------|
| [outputs/genai-skill-framework-v2.html](outputs/genai-skill-framework-v2.html) / [.md](outputs/genai-skill-framework-v2.md) | **正本**（評価ベクトル・ルーブリック・運用原則） |
| [user-guide.html](user-guide.html) | 利用者ガイド（考え方・証拠の再現性・診断の進め方） |
| [outputs/sample-demo.html](outputs/sample-demo.html) | 個人結果HTMLのサンプル |

解釈が分かれた場合は正本を優先してください。

## 構成

1. **個人採点** — Claude Code スキル（対話専用）  
   - スキル定義: [`.claude/skills/genai-skill-assessment/SKILL.md`](.claude/skills/genai-skill-assessment/SKILL.md)  
   - 実績（証拠）を読み取り、到達度・証拠の再現性を採点  
   - 出力: `outputs/<subject>_<date>.html` と `data/results/<subject>_<date>.json`
2. **グループダッシュボード** — Python スクリプト（AI呼び出しなし）  
   - [`scripts/generate_dashboard.py`](scripts/generate_dashboard.py)  
   - `data/results/` の JSON を集計して HTML を生成

## 使い方（個人採点）

前提: [Claude Code](https://docs.anthropic.com/en/docs/claude-code) が使えること。

1. このリポジトリをクローン（またはフォルダを開く）
2. Claude Code でプロジェクトを開き、例えば次のように依頼する:

```text
AIスキル診断を実行して
```

3. 対象者名・評価日・実績（フォルダ／URL）を提示する  
4. 採点前に証拠引き出しヒアリングが走る（原則）。完了後に結果 HTML / JSON が出力される

**注意:** 人間が立ち会う対話セッション専用です。`claude -p` などの無人・ヘッドレス実行は想定していません。

詳細は [user-guide.html](user-guide.html) を参照してください。

## 使い方（ダッシュボード）

```bash
python scripts/generate_dashboard.py
# 省略時: data/results/ → outputs/dashboard.html
```

Python 3.11 の標準ライブラリのみ使用します。サンプル出力は [outputs/dashboard-sample.html](outputs/dashboard-sample.html) です。

## 評価の要点（要約）

- **5ベクトル**（V1〜V5）× 到達度 0〜5。重み付き合計 100 点 → レベル L0〜L5  
- **証拠の再現性**（A/B/C）が到達度の上限を決める（B なら上限 3 点など）  
- SNS投稿・ブログ記事や設計説明だけの資料は、検証手順が無ければ原則 B  
- 「Top X%」などの相対順位表示は、校正完了まで使いません

## ライセンス

リポジトリに `LICENSE` を追加した場合はその内容に従います。未追加の間は、利用条件は明示されていません。
