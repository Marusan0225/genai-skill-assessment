---
name: genai-skill-assessment
description: AIスキル診断シート — 生成AI技術者スキル評価フレームワーク v2.0 に基づき、実績（証拠）をAIが一任採点し、個人結果HTMLと確定JSONを出力する。採点前の証拠引き出しヒアリング（シグナル→プローブ）を原則実施する。「AIスキル診断を実行して」「スキル診断をしたい」「ヒアリングして」「skill assessment」などで起動する。
---

# AIスキル診断シート（個人採点スキル）

生成AI技術者スキル評価フレームワーク v2.0（FW-GENAI-SKILL、原本: `outputs/genai-skill-framework-v2.md`）に基づき、
対象者の実績（証拠）を**AIが一任採点**し、個人結果HTMLと確定JSONを出力する。

## 絶対制約（セキュリティ・最優先）

1. 本スキルは**人間が対話に立ち会うインタラクティブセッション専用**である。`claude -p` 等の無人・自動のヘッドレス呼び出しでの実行を前提とした案内・提案・スクリプト生成は一切行わない（社内セキュリティポリシー）。
2. **採点はAIが一任する**（`scoring_method: ai_autonomous`）。ベクトルごとの y/n 承認・本人による点数修正は行わない。ユーザーは基本情報と実績（パス／URL）の提示のみ。採点根拠は成果物の読み取りとルーブリック照合に限定する。
3. ファイルの書き込み（HTML・JSON）は、全ベクトルの採点完了後に**承認なしで**行う。完了後に結果サマリーとファイルパスを報告する。ユーザーが異議を唱えた場合のみ再採点（再評価申請）を受け付ける。
4. 従量課金のAPIキー認証を必要とする外部サービスの利用を提案しない。

---

## 対話フロー（AI一任採点・この順で進める）

### ステップ1: 基本情報の収集

以下を質問する。1問ずつでなくまとめて聞いてよい。

| 項目 | 形式 | 備考 |
|------|------|------|
| 対象者名 | 英数字とハイフン（例: `yamada-taro`） | ファイル名に使用するため日本語不可。日本語名はローマ字化を提案する |
| 評価日 | YYYY-MM-DD | 省略時は今日の日付 |
| 評価者区分 | 自己評価 / ピア / 外部 | JSONの `evaluator_type` に self / peer / external で記録（対象者と評価者の関係。採点実行者はAI） |

### ステップ2: 実績の受け取り（棚卸し）

実績フォルダ・ファイルパス・URLを受け取ったら、**採点に入る前に**「証拠の再現性 — ユーザー向け要点」（後述）を短く提示する。特に **HTMLガイド中心の提出**、**SNS投稿・ブログ記事のみ**、**URL追加でAになると誤解しそうな場合**は必ず明示する。

- 提示されたパス／URLの内容を**必ず読み取る**（ガイドHTMLだけでなく、記載されている一次ソースURL・デプロイ先・リポジトリ参照を抽出する）
- 各実績の**作成時期**（年月）を文書から確認する。不明ならユーザーに1回だけ確認してよい
- 実績が無いベクトルは「証拠の不在」として0点
- **会話・自己申告のみを根拠にした採点は禁止**（禁止事項④）

### ステップ2.5: 証拠引き出しヒアリング（原則実施）

読み取り直後、**採点の前に**「証拠引き出しヒアリング」を原則実施する（後述）。目的は提出可能な証拠の穴を埋めること。終了条件を満たしたら、またはユーザーが明示スキップしたら、ステップ3（全ベクトル採点）へ進む。

---

## 証拠の再現性 — ユーザー向け要点（採点前に必ず提示）

利用者ガイド `user-guide.html` §2 と同内容。採点開始前に次を要約して伝える（コピペ可）。

> **再現性（A/B/C）は到達度の上限を決めます。到達度（0〜5）とは別物です。**
>
> - **「第三者」**＝インターネット上の不特定一般ではない。**本人の申告以外**（採点AI・ピア・社内レビュアー）が手順どおり検証できるか。本ツールは**社内用** — 社内Git・社内wiki・VPN内デモ・ローカルパスも手順付きならA可（FW 7章）
> - **A（再現可能・上限5点）**: 検証用URL／ファイル＋手順のセット（**ガイドHTML内に記載可**）。リポジトリ、デモ、評価結果の数値ファイル等
> - **B（設計文書・上限3点）**: 設計説明だけのHTMLガイド、SNS投稿・ブログ記事。**検証URL・手順・数値記録が無い**場合
> - **C（記述のみ・上限2点）**: 箇条書きリスト、概要メモ
>
> **提出前チェック**: 各ベクトルで検証先＋手順があるか。AIがセッション内で読める形か（fetch不可のURLだけは不可）。

---

## 証拠引き出しヒアリング（分岐ロジック）

決め打ちの「質問1・質問2」は使わない。**シグナルを検知してプローブ型を選び、返答で盤面を更新し、次のプローブを決める**。目的は採点そのものではなく、**提出可能な証拠の穴を埋めること**（会話だけでの加点は禁止）。

### いつ起動するか（原則必須・例外でスキップ）

**既定は採点前に必ず回す**（ステップ2.5）。「ヒアリングして」の明示依頼は不要。診断開始＝ヒアリング込みが標準経路。

| 契機 | 振る舞い |
|------|---------|
| 通常の診断（実績受け取り後） | **原則開始**。読み取りでシグナルを立て、焦点ベクトルからプローブを回す |
| 再評価・追加証拠の提出後 | 変更のあったベクトル／最弱ベクトルを焦点に短く回す（原則実施） |
| ユーザーが明示スキップ | 「ヒアリングなしで採点」「スキップ」等 → 採点へ進んでよい（例外） |
| 証拠が明らかに揃っている | 全ベクトルに検証セット（URL/ファイル＋手順）があり、薄いシグナルが無い → **最短1ターン**（`P_board_confirm` のみ）で終了してよい。ゼロターン省略はユーザー明示スキップ時のみ |

### 絶対ルール

1. **会話・自己申告のみを採点根拠にしない**（禁止事項④）。ヒアリングで得た内容は「提出チェックリスト」と空表の下書きまで。点はファイル／URLが揃ってから付ける
2. **固定の質問番号リストを読み上げない**。毎回、現在のシグナル集合からプローブを1つ選ぶ
3. **商用APIの仮想月額見積もりを強制しない**。初期からクラウドAPIを対象外にしている場合は、その決定理由＋採用構成の追加コスト（¥0可）＋データ配置で足りる
4. 1ターンにプローブは原則1つ。続けて畳み掛けない
5. 最大 **6ターン**（プローブ6回）。超えたら打ち切り、その時点のチェックリストを渡す
6. 称賛・長いコーチングはしない（規格書トーン）

### 状態（内部で持つ・ユーザーに全部見せなくてよい）

| フィールド | 内容 |
|-----------|------|
| `focus_v` | 焦点ベクトル（既定: 重み付き点が最低のV。未採点なら証拠の薄さで推定） |
| `signals` | 下表のシグナルIDの集合（証拠読取＋直前の返答から更新） |
| `board` | 埋まってきた提出物メモ（ファイル名案・日付・有無） |
| `probes_used` | 使用済みプローブ型（同じ型の連続は避ける） |
| `turns` | 消費ターン数 |

### シグナル検出（証拠・発言から付与）

読めるもの・聞こえたものだけ付与する。推測で付けない。

| ID | 検知の目安 |
|----|-----------|
| `S_ops_log` | 監視／ログ／障害対応の記録・言及がある |
| `S_night_loop` | 夜間・無人・autorun・ループ常駐の言及／文書がある |
| `S_kill_switch` | 停止手段・リトライ上限・人間承認点の言及がある |
| `S_cost_zero_local` | ローカルLLM／既存サーバ／追加課金なしの方針がある |
| `S_api_out_of_scope` | 商用APIを初期から対象外にしている |
| `S_eval_missing` | 構造テストはあるが LLM品質の数値記録がない（V4薄い） |
| `S_demo_live` | 公開／デモURLがセッション内で生きている |
| `S_failure_story` | 失敗・停止・誤起動・手戻りのエピソードが出た |
| `S_file_path_ready` | 提出用の具体パス・ファイル名が言えた／書けた |

### プローブ型（質問文は状況に合わせて生成する・型だけ固定）

| 型ID | ねらい | 開き方の例（文言は固定しない） |
|------|--------|------------------------------|
| `P_failure_night` | 運用の実在を引き出す | 「止めた夜／止められなかった夜」を1本だけ語ってもらう |
| `P_ops_artifact` | 監視・ログ・障害の提出物を特定 | いま残っている記録の場所・形式・直近の日付を聞く |
| `P_night_run` | 夜間ループの再現条件 | 起動条件・止め方・翌朝の確認を、手順として言えるか聞く |
| `P_cost_decision` | コスト根拠（仮想API月額は禁止） | 対象外にした理由／追加コストの実績（¥0可）／データ配置を空表で埋める |
| `P_eval_metric` | V4の一段上げ | 稼働中の成果物で測れる指標を1つ選び、CSV列を一緒に決める |
| `P_repro_path` | 再現性Aの穴埋め | 検証セットに書くURLまたはパス＋手順の一文を確定させる |
| `P_board_confirm` | 終了前の収束 | 盤面（提出物リスト）を読み上げ、過不足だけ確認する |

### 分岐（次プローブの選び方）

毎ターン、上から見て**最初に当てはまる規則を1つ**適用する。該当なしなら `P_board_confirm` で終了に向かう。

1. `turns >= 6` → 終了（チェックリスト出力）
2. `focus_v == V4` かつ `S_eval_missing` かつ `P_eval_metric` 未使用 → `P_eval_metric`
3. `S_night_loop` かつ `P_night_run` 未使用 → `P_night_run`
4. `S_ops_log` かつ `P_ops_artifact` 未使用 → `P_ops_artifact`
5. `S_failure_story` が無い かつ （`S_ops_log` または `S_night_loop`）かつ `P_failure_night` 未使用 → `P_failure_night`
6. （`S_cost_zero_local` または `S_api_out_of_scope` または focus が V5）かつ `P_cost_decision` 未使用 → `P_cost_decision`
7. 再現手順が盤面に無い → `P_repro_path`
8. それ以外 → `P_board_confirm` → 終了

同じ型を連続で選ばない。返答で新しいシグナルが付いたら、次ターンで規則をやり直す。

### ターンの型（毎回この順）

```
[盤面の一行] focus=V? / 埋まってきた提出物
[プローブ1つ] 型に沿った問い（決め打ち番号なし）
[聴取] ユーザー返答
[更新] signals と board を更新。必要なら「提出ファイル名案」をその場で1行書く
```

### コスト空表（`P_cost_decision` 用・商用API月額列は置かない）

ヒアリング中に次を一緒に埋める（埋まらなくても圧をかけない）。

| 項目 | 記入 |
|------|------|
| クラウドAPI | 対象外にした時期と理由（初期方針ならその旨） |
| 採用構成 | ローカルサーバ／ローカルLLM／自前アプリ 等 |
| 月次の追加従量課金 | 実績（¥0 可） |
| データ配置 | 社内完結／外部送信の有無 |

### 終了条件と出力

次を満たしたらヒアリング終了（全部埋まらなくてもターン上限で終了可）。

- `P_board_confirm` を1回終えた、または `turns == 6`
- 終了時に必ず出すもの:
  1. **提出チェックリスト**（ベクトル別・ファイル／パス／不足）
  2. 埋まっている空表・CSV列案（あれば）
  3. 「ファイルを置いたら再評価して、とパスを指定」と案内
- 終了後は原則そのままステップ3の採点へ進む（追加ファイルを置く時間が必要なら、パス指定のうえ再評価を案内してよい）

### 開始時の一言（コピペ可）

> 採点の前に、証拠の穴を埋める短いヒアリングを行います（原則）。決め打ちの質問リストは使いません。いま見えている穴から、その都度ひとつだけ聞きます。話した内容だけでは点数は付けず、提出ファイルの形に落とすのがゴールです。スキップする場合は「ヒアリングなしで採点」と言ってください。

---

### ステップ3: 全ベクトル採点（AI一任）

ヒアリング終了（または明示スキップ）後、V1〜V5を順に、以下を**AIが自律的に**実行して確定する（途中でユーザーに y/n を求めない）。

1. ルーブリック照合で到達度案（0〜5）を作る
2. **「証拠の再現性の運用基準」**（後述）に従い A/B/C を判定する（甘いA判定を避ける）
3. 鮮度区分を判定し、減衰を適用する
4. 決定論的ルールをこの順で適用し、到達度に上限をかける
5. 4点以上を付ける場合のみ、ステップ4の文書深掘りを実施する。B/C 証拠のみのベクトルは**4点以上を付けない**

採点中の思考は省略してよい。確定後、**結果サマリー表**（5ベクトル＋合計＋レベル）を1回提示する。

### ステップ4: 文書深掘り（4点以上を付ける場合・必須）

4点以上を検討するベクトルについて、**成果物の記述のみ**から設計判断の整合を確認する（ユーザーへの質問はしない）。

- 設計判断の根拠が文書・コード・手順に**明示されているか**を確認する
- 確認できない・矛盾する場合は3点以下に下げる
- 実施した場合のみ JSONの `deep_dive_done` を `true` にする

### ステップ5: 合計・レベル判定

全ベクトル確定後、機械的に計算する（「スコア計算」参照）。

### ステップ6: 個人結果HTMLの生成

「HTML出力仕様」に従い `outputs/{対象者名}_{評価日}.html` を生成する。**承認を待たず書き込む。**

### ステップ7: 確定JSONの保存

「JSON出力仕様」に従い `data/results/{対象者名}_{評価日}.json` を保存する。**承認を待たず書き込む。**

### ステップ8: 完了報告

以下を報告して終了する。

- 結果サマリー（合計・レベル・各ベクトル到達度と証拠の再現性）
- 生成した2ファイルのパス
- 再評価を希望する場合は追加証拠の提示で依頼できる旨
- チーム比較: JSONを共有フォルダに集約し `python scripts/generate_dashboard.py`
- 組織展開時は FW 6.2 に従い**評価者2名の独立採点**を推奨（本スキルのAI一任は個人向け自己位置把握用）

---

## 証拠の再現性の運用基準（採点時に厳守）

FW 2章の A/B/C 定義に加え、以下で判定する。**設計説明だけのHTMLガイドは原則 B**。ただしガイド**内に**検証用URL・手順・評価結果の数値がセットで書いてあり、採点セッションで確認できるなら **A** とする。

**「第三者」**＝不特定の外部公開者ではなく、**本人の申告以外の検証主体**（採点AI・ピア評価者・社内レビュアー）。本スキルは社内運用を前提とし、**社内非公開の成果物も等級Aとして認める**（FW 7章2項）。

| 判定 | 条件（いずれかを満たす） |
|------|------------------------|
| **A（再現可能）** | (1) 動作確認できるURL（デプロイ・API・Hugging Face Spaces・**社内/VPN内デモ** 等）＋再現手順が同一成果物群（**ガイドHTML内記載可**）に記載、(2) リポジトリURL（**社内Git可**）＋README/手順で評価者が再現可能、(3) 評価・テスト結果の**数値記録ファイル**（CSV/JSON/レポート）＋再現手順。**採点AIがセッション内で内容を確認できること** |
| **B（設計文書）** | アーキテクチャ設計書、比較検討記事、**検証URL・手順・数値記録が無いHTMLガイド**、SNS投稿・ブログ記事 |
| **C（記述のみ）** | 概要ブログ、箇条書きリスト、判断理由・再現手順がないメモ |

**JSON/HTML の `evidence` 配列の書き方**:
- **必ず一次ソースを優先**して列挙する（デプロイURL、リポジトリURL、SNS・ブログ記事URL 等）
- ローカルガイドHTMLは補助として `実績/...` パスでよいが、A判定の根拠にする場合は同配列内に動作確認URLまたはリポジトリURLを**必ず1件以上**含める
- URLは `https://...` 形式。相対パスはガイド類のみ

**組織向け（任意・FW 6.2）**: チーム可視化・人事参考情報として使う場合は、AI一任採点に加え**評価者2名の独立採点**と乖離2点以上のキャリブレーションを実施する。本スキル単体では代替しない。

---

## ルーブリック（フレームワーク3章より転記・変更禁止）

重み: V1=25% / V2=25% / V3=20% / V4=15% / V5=15%（合計100点満点）。根拠と計算式はフレームワーク3章および結果HTML「重みと重み付き点」を参照（`重み付き点 = 到達度 × 重み(%) ÷ 5`）

### V1: Context Engineering — コンテキスト設計力（25%）

**定義**: 業務要件・ドメイン知識・タスク状態を、LLMが最も正確に解釈できる形に翻訳・構造化・配置できる能力。**ビジネス要件をAIシステム要件に翻訳できる力を含む。**

| 点 | 行動基準（ツール非依存） |
|----|------------------------|
| 0 | プロンプトの試行錯誤のみ。設計の記録がない |
| 1 | 基本的なプロンプト技法（例示提示・段階的推論の誘導）を意図的に使い分けている |
| 2 | 長大な入力に対する分割・要約・優先順位付けの戦略を設計し、文書化している |
| 3 | コンテキストの構造的劣化（中間情報の欠落等）を予見した階層的コンテキスト設計を実装している |
| 4 | ドメイン固有のコンテキストスキーマ（構造化された仕様記述形式）を定義し、再現可能な形で運用している |
| 5 | 複数エージェント間の状態受け渡し規約を設計・実装し、要件の翻訳から状態設計まで一貫した方法論として文書化している |

**必須の採点観点**: 曖昧な業務要件を「入力・状態・出力・例外」に分解した実績があるか。「作らない／単純な解で済ませる」判断をした記録があるか。

### V2: Agentic System Design — エージェントシステム設計力（25%）

**定義**: 自律型AIエージェント（単一・複数）を、安全に稼働を継続し、実務品質で動くシステムとして設計できる能力。**セキュリティと出力品質（UI/UX含む）の制御を含む。**

| 点 | 行動基準（ツール非依存） |
|----|------------------------|
| 0 | チャットUIの利用のみ |
| 1 | ノーコード／ローコード基盤で基本的なワークフローを構築できる |
| 2 | ツール呼び出し（外部API・検索・計算）を組み込んだエージェントを構築している |
| 3 | 複数ツールを連携させたエージェントを構築し、失敗時のフォールバックを設計している |
| 4 | 複数エージェントの役割分担（計画・実行・検証等）を設計し、暴走防止（ループ上限・状態機械・人間の承認点）を実装している |
| 5 | 本番相当のエージェントシステムを、安全機構・権限設計・出力品質制御を含む一貫した設計文書とともに構築・運用している |

**必須の採点観点（3点以上を付ける場合に確認）**:
- **セキュリティ**: プロンプトインジェクション対策、エージェントに与える権限の最小化を考慮しているか
- **出力品質・UI制御**: 生成させたUIや文書が実務品質か。デザイン原則・出力規約を事前に明文化してエージェントに与えているか

### V3: Retrieval & Knowledge Architecture — 知識アーキテクチャ設計力（20%）

**定義**: ドメイン知識・文書・データを、システムが使える形に整え、課題に応じた参照方法を設計できる能力。**RAG（ベクトル検索）に限定しない**（キーワード・ハイブリッド・再ランキング・長文コンテキスト直接投入、「検索基盤を作らない」判断を含む）。重要なのは要否と適正レベルの判断であり、複雑な検索基盤を構築したこと自体は加点しない。**

| 点 | 行動基準（ツール非依存） |
|----|------------------------|
| 0 | 知識参照の仕組みを構築した実績がない |
| 1 | 文書を分割してベクトル検索する基本構成を構築している |
| 2 | メタデータ設計・フィルタリングにより検索対象を制御している |
| 3 | 課題特性に応じて検索方式（キーワード・ベクトル・ハイブリッド・再ランキング・長文コンテキスト直接投入）を**比較検討し、根拠をもって選定**している |
| 4 | 複雑な文書（図表・数式・多階層構造）に対するパース・インデックス戦略を設計し、精度を定量比較している |
| 5 | ドメイン全体の知識構造（階層・関係性・鮮度）を設計し、検索精度の改善を数値で実証している。「検索基盤を作らない」判断を含む最適化ができている |

**注意**: 3点の「長文コンテキスト直接投入で十分と判断した」ケースは、根拠が示されていれば複雑なRAG構築と同等に評価する。
**必須の採点観点（3点以上を付ける場合に確認）**: 方式選定の根拠が実績に含まれているか。

### V4: Evaluation & Observability — 評価・観測能力（15%）

**定義**: AI（確率的に振る舞うシステム）の出力品質を数値で捉え、劣化の原因を「プロンプト／検索データ／モデル／インフラ」に切り分けて改善できる能力。

| 点 | 行動基準（ツール非依存） |
|----|------------------------|
| 0 | 目視確認のみ |
| 1 | 良否判定の基準を決めて手動評価している |
| 2 | テストケース集（想定入力と期待出力）を作成・維持している |
| 3 | 忠実性・関連性等の指標を定義し、計測している |
| 4 | 自動評価パイプラインを構築し、変更のたびに回帰評価している |
| 5 | 評価結果に基づいて原因を峻別し、改善前後の数値比較を伴う改善サイクルを文書化・公開している |

### V5: Production & LLMOps — 本番構築・運用能力（15%）

**定義**: AIシステムを本番で動かし続けられる能力。**インフラ構築だけではない**（環境の分離・再現、推論基盤との結合、コストとデータのリスク判断、監視・障害対応・コスト管理の継続運用を含む）。

| 点 | 行動基準（ツール非依存） |
|----|------------------------|
| 0 | ブラウザ上のサービス利用のみ |
| 1 | API呼び出しを含むスクリプトをローカルで実行できる |
| 2 | コンテナ技術で依存関係を分離した開発環境を構築・文書化している |
| 3 | ローカル推論環境とデータベースを構築し、アプリケーションと結合している |
| 4 | モデル選定（商用API vs OSS）・量子化・インフラ構成を、**コスト試算とデータ漏洩リスク評価を根拠に**選定している |
| 5 | 監視・ログ・障害対応・コスト管理を含む運用を継続し、その記録を文書化している |

**必須の採点観点（4点以上を付ける場合に確認）**: 月次コストの試算根拠、データの置き場所（ローカル／クラウド）の選定理由が文書に含まれているか。

**ツール例（参考・非拘束）**: コンテナ=Docker等 / ローカル推論=Ollama, vLLM等 / ベクトルDB=Qdrant, Chroma等 / 評価=Ragas, LangSmith, Phoenix等 / ワークフロー=Dify, LangGraph等。ツールは陳腐化するため、採点はあくまで行動基準で行う。

---

## 決定論的ルール（AIの裁量で緩めない・この順で適用）

ルーブリック照合で作った到達度案に対し、以下を**この順序で**適用する。適用した場合は必ず警告として明示する。

### 1. 鮮度ルール（3段階・最初に適用）

実績の作成時期（評価日からの経過）で**証拠等級を減衰させる**。上限点の適用（ルール2）は必ず減衰後の等級で行う。

| 実績の時期 | 扱い |
|-----------|------|
| 直近12ヶ月 | 等級どおり満額 |
| 12〜24ヶ月 | 等級を1段階下げる（A→B、B→C。Cはそのまま） |
| 24ヶ月超 | 参考扱い。そのベクトルの上限2点 |

**鮮度の例外**: 陳腐化の遅いスキル領域（コンテナによる環境分離、ネットワーク・権限設計、評価指標の設計思想など）に限り、評価者の判断で12〜24ヶ月の実績を満額扱いにできる。例外の適用はAIが提案してよいが**決定はユーザー**が行い、理由をJSONに記録する。逆に、モデル・ツールの特定バージョンに強く依存する実績は12ヶ月以内でも等級を下げてよい（同様に理由を記録）。

### 2. 証拠の再現性による上限点（鮮度減衰後の等級で適用）

JSONフィールド名は `evidence_grade`（値は `A` / `B` / `C` のみ。中間等級は設けない）。
**表示・説明では「証拠の再現性」と呼ぶ**（「等級」だけだと到達度と混同しやすい）。到達度＝ルーブリック上の0〜5（JSON: `raw_score`）、証拠の再現性＝成果物の検証しやすさ。両者は独立である。

| 記号 | 表示名 | 定義 | そのベクトルの上限点 |
|------|--------|------|---------------------|
| A | 再現可能 | 本人の申告以外（AI・ピア・社内レビュアー）が手順どおり検証できる成果物。社内非公開可。コード＋データ＋手順、動くシステム、定量的計測結果 | 5点 |
| B | 設計文書 | 「なぜその設計にしたか」の判断・トレードオフが記述された文書 | 3点 |
| C | 記述のみ | やったことの記述はあるが、判断理由も再現性もないもの | 2点 |

### 3. 必須観点チェック（未達なら上限をかける）

| ベクトル | 条件 | チェック内容 | 未達時の扱い |
|---------|------|------------|------------|
| V2 | 3点以上を付ける場合 | セキュリティ（インジェクション対策・権限最小化）と出力品質・UI制御の両方が確認できるか | 確認できなければ上限2点。警告に理由を明記 |
| V3 | 3点以上を付ける場合 | 検索方式の選定根拠が示されているか | 示されなければ上限2点。警告に理由を明記 |
| V5 | 4点以上を付ける場合 | コスト試算根拠・データ配置の選定理由が文書に含まれるか | 含まれなければ上限3点。警告に理由を明記 |

### 4. 採点時の禁止事項（フレームワーク5章）

1. 証拠等級A（鮮度減衰後）がないベクトルに4点以上を付けない
2. 深掘り確認（ステップ4）を実施せずに4点以上を付けない
3. 根拠資料が空欄のまま点を付けない（実績の提示がないベクトルは0点とし「証拠の不在」と記録する）
4. 会話・自己申告のみを根拠に採点しない

---

## スコア計算・レベル判定

- ベクトルの重み付き点 = 到達度 × 重み(%) ÷ 5（例: V1到達度3 → 3 × 25 ÷ 5 = 15.0点）。小数第1位まで保持。÷5 は到達度0〜5を重み％の満点寄与へ正規化するため
- 合計点 = 5ベクトルの重み付き点の和（0〜100、小数第1位まで）
- 重みの数値根拠（中核 V1/V2=25、実務 V3=20、支援 V4/V5=15）は結果HTMLと FW 3章に記載。個人結果では必ず同節を出力する
- レベル判定は**合計点を四捨五入した整数**で以下の帯に照合する

| スコア | レベル | 呼称 |
|--------|--------|------|
| 85〜100 | L5 | Principal Architect |
| 70〜84 | L4 | Architect |
| 55〜69 | L3 | Systems Practitioner |
| 40〜54 | L2 | Application Builder |
| 25〜39 | L1 | Foundation |
| 0〜24 | L0 | Entry |

- 「Top X%」等のパーセンタイル表示は**使用しない**（フレームワーク4章の凍結方針）
- 「次の一手」は、重み付き点が最も低いベクトル（同点なら重みの大きい方を優先）を焦点にし、**コーチング4段**で書く（フレームワーク6.2章の「証拠の再現性Aを1つ作る」を中核に据える）。強み活用・称賛・複数選択肢の併記はしない
  1. **焦点** — 最弱ベクトルと、なぜそこを次に取るか（事実ベース、1〜2文）
  2. **現状** — いま確認できている事実のみ（不足点の指摘。他ベクトルの強みへの橋渡しは書かない）
  3. **90日の一手** — 小さく具体的な実験を1つだけ（対象プロダクト・成果物名・頻度が分かる水準）
  4. **完了の定義** — 何が揃えば「できた」か（証拠の再現性A相当の判定基準を明示）
  5. **振り返り質問** — 完了後に自分へ問う質問を1つ（任意だが原則入れる）
- **次の壁の見分け（よくある取り違え）** — 主たる次の一手の**後**に、条件を満たすときだけ付ける任意節。行動の優先順位は変えず、「4点で満足しがちな取り違え」を1〜2本だけ示す
  - **出力条件**: 到達度ちょうど **4** のベクトルが1つ以上あるとき（5は対象外。0〜3のみのときは節ごと省略）
  - **本数**: 最大 **2** 本。候補が3つ以上なら重みの大きい順。同点なら V番号の小さい方
  - **書き方**（各本とも同じ型。称賛・パーセンタイル・「上位○％」は禁止）:
    1. **よくある取り違え** — 「〜があれば5相当」と思われがちな誤解を1文
    2. **本当の5** — 行動基準5が要求する見分けを1〜2文（証拠の言葉で）
    3. **振り返り質問** — 自分で境界を判定できる質問を1つ
  - **辞書を起点にする**（下記）。対象者の実績に合わせて具体名を1つ足してよいが、他ベクトルを足して合成しない
  - 並行で成果物を作る場合は「任意・再評価時」と明記し、主たる90日の一手と競合させない

#### 次の壁の見分け — 取り違え辞書（4→5）

| V | よくある取り違え | 本当の5（見分け） |
|---|----------------|------------------|
| V1 | ドメイン固有スキーマやフォルダ規約を運用し、エージェントも複数いる → 5相当 | エージェント間で渡す**状態の契約**（必須フィールド・禁止・承認・違反時）を設計・実装し、要件翻訳から状態設計まで**一本の方法論**として文書化しているか |
| V2 | 役割分担・承認点・ループ上限・検査ゲートがある → 本番相当で5 | 安全・権限・出力品質を含む設計が、**単一の本番相当システムとして継続運用された記録**まで一体になっているか（設計図の羅列ではない） |
| V3 | 複雑文書のパースや精度の定量比較をした → 5 | ドメイン全体の知識構造を設計し改善を数値実証しているか。あわせて**「検索基盤を作らない」判断**を含む最適化ができているか |
| V4 | 自動評価パイプラインや回帰評価がある → 5 | 評価結果から原因を峻別し、**改善前後の数値比較を伴う改善サイクル**を文書化・公開しているか |
| V5 | コスト試算とデータリスクを根拠に構成を選んだ → 5 | 監視・ログ・障害対応・コスト管理を**継続運用し、その記録を文書化**しているか（選定メモだけでは不足） |

---

## JSON出力仕様

保存先: `data/results/{対象者名}_{評価日}.json`（UTF-8、例: `data/results/yamada-taro_2026-07-18.json`）

```json
{
  "framework_version": "2.0",
  "subject": "yamada-taro",
  "assessment_date": "2026-07-18",
  "evaluator_type": "self",
  "scoring_method": "ai_autonomous",
  "total_score": 62.0,
  "level": "L3",
  "level_name": "Systems Practitioner",
  "vectors": {
    "V1": {
      "name": "Context Engineering",
      "raw_score": 3,
      "weight": 25,
      "weighted_score": 15.0,
      "evidence_grade": "A",
      "freshness": "within_12m",
      "freshness_exception": { "applied": false, "reason": "" },
      "mandatory_checks": null,
      "deep_dive_done": false,
      "rationale": "階層的コンテキスト設計の実装が確認できる（...）",
      "evidence": ["https://github.com/example/repo"]
    },
    "V2": {
      "name": "Agentic System Design",
      "raw_score": 0,
      "weight": 25,
      "weighted_score": 0.0,
      "evidence_grade": null,
      "freshness": null,
      "freshness_exception": { "applied": false, "reason": "" },
      "mandatory_checks": { "security": false, "output_quality": false },
      "deep_dive_done": false,
      "rationale": "証拠の不在（実績の提示なし）",
      "evidence": []
    },
    "V3": {
      "name": "Knowledge Architecture",
      "raw_score": 3,
      "weight": 20,
      "weighted_score": 12.0,
      "evidence_grade": "B",
      "freshness": "12_to_24m",
      "freshness_exception": { "applied": false, "reason": "" },
      "mandatory_checks": { "method_selection_rationale": true },
      "deep_dive_done": false,
      "rationale": "検索方式の比較検討と選定根拠が設計書に記述されている（...）",
      "evidence": ["docs/architecture/search-design.md"]
    },
    "V4": { "...": "V1と同様の構造。mandatory_checks は null" },
    "V5": { "...": "V2と同様の構造。mandatory_checks は { \"cost_risk_rationale\": true|false }" }
  },
  "ceiling_insights": [
    {
      "vector": "V1",
      "from_score": 4,
      "misread": "よくある取り違え（到達度4のときのみ。無ければキー省略可）",
      "actual_n1": "行動基準5の見分け",
      "reflect": "振り返り質問"
    }
  ],
  "notes": "特記事項（スコープ外の強み等）"
}
```

### フィールド規約

| フィールド | 値 |
|-----------|-----|
| evaluator_type | `self`（自己評価） / `peer`（ピア） / `external`（外部）。対象者と評価者の関係 |
| scoring_method | `ai_autonomous`（AI一任採点・本スキル標準） |
| raw_score | 0〜5 の整数（全ルール適用後の確定値）。**表示名は「到達度」**（総合レベル L0〜L5 とは別） |
| weighted_score | raw_score × weight ÷ 5（小数第1位） |
| evidence_grade | `A` / `B` / `C`。**鮮度減衰後**の証拠の再現性を記録（表示名: 再現可能／設計文書／記述のみ）。証拠なしは `null` |
| freshness | `within_12m` / `12_to_24m` / `over_24m`。証拠なしは `null` |
| mandatory_checks | V2: security / output_quality、V3: method_selection_rationale、V5: cost_risk_rationale。V1・V4は `null` |
| deep_dive_done | 文書深掘りを実施したら `true`（4点以上のベクトルのみ。AI一任モードではユーザー質問なし） |
| evidence | **一次ソースURLを優先**（デプロイURL・リポジトリ・公開記事）。ガイドHTMLパスは補助可。raw_score≥1 なら1件以上 |
| ceiling_insights | **任意**。到達度4のベクトル向け「次の壁の見分け」（最大2件）。該当なしならキー省略または `[]` |

- V1〜V5の5キーは**常に全て出力**する（実績なしでも raw_score: 0 で出力）
- 集計スクリプトは `subject` / `assessment_date` / `total_score` / `level` / `vectors.*.raw_score` / `weighted_score` / `evidence_grade` を再計算せずに使用するため、AI採点結果と完全に一致させること

---

## HTML出力仕様

保存先: `outputs/{対象者名}_{評価日}.html`（1ファイル完結・外部JS依存なし）

### デザイン原則（`outputs/genai-skill-framework-v2.html` のデザイン言語を継承・逸脱禁止）

- 「診断結果を突き返す規格書」— 感情的な励まし文言・装飾・絵文字・グラデーション・根拠のない称賛は使わない
- 配色・フォントは下のテンプレートのCSSトークンをそのまま使う（藍 #2b3a8f は単色アクセント。ダークモード非対応）
- 主役はスコア横バー（L0〜L5）1つ。レーダーチャート・証拠の再現性バッジは副次要素として控えめに配置する
- 生成後、以下を自己チェックする: グラデーション不使用／絵文字不使用／角丸多用なし／煽り・称賛文言なし／数値と根拠で語る文体

### テンプレート

以下のテンプレートの `{{...}}` を実データで置換して出力する。V1〜V5の繰り返し部分は5ベクトル分展開する。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AIスキル診断結果 — {{SUBJECT}}（{{DATE}}）</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+JP:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --paper:#f6f6f3; --surface:#ffffff;
  --ink:#1c1e22; --ink-soft:#4b4f57; --ink-faint:#8a8e96;
  --rule:#dcdcd6; --rule-strong:#b9b9b0;
  --accent:#2b3a8f; --accent-soft:#e8eaf6;
  --caution:#8f5a2b; --caution-soft:#f6efe6;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
  --sans:'IBM Plex Sans JP',-apple-system,'Hiragino Kaku Gothic ProN','Noto Sans JP',sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sans);background:var(--paper);color:var(--ink);font-size:15px;line-height:1.85;-webkit-font-smoothing:antialiased}
main{max-width:900px;margin:0 auto;background:var(--surface);border-left:1px solid var(--rule);border-right:1px solid var(--rule)}
.page{padding:56px 56px 96px}
header.doc-head{border-bottom:2px solid var(--ink);padding-bottom:32px}
.doc-head .eyebrow{display:flex;justify-content:space-between;align-items:center;font-family:var(--mono);font-size:11px;letter-spacing:.16em;color:var(--ink-faint);margin-bottom:22px}
.doc-head .eyebrow .ver{color:var(--accent);border:1px solid var(--accent);padding:3px 10px;letter-spacing:.1em;font-weight:500}
h1{font-size:26px;font-weight:700;line-height:1.45;margin-bottom:6px}
.doc-head .subtitle{font-size:14px;color:var(--ink-soft)}
table.meta{width:100%;border-collapse:collapse;margin-top:28px;font-size:13px}
table.meta th,table.meta td{text-align:left;padding:9px 14px;border:1px solid var(--rule);vertical-align:top}
table.meta th{width:132px;background:var(--paper);font-weight:500;font-family:var(--mono);font-size:11px;letter-spacing:.06em;color:var(--ink-soft)}
section{padding-top:52px}
section + section{border-top:1px solid var(--rule);margin-top:52px}
h2{display:flex;align-items:baseline;gap:14px;font-size:20px;font-weight:700;margin-bottom:22px}
h2 .sec-n{font-family:var(--mono);font-size:13px;font-weight:600;color:var(--surface);background:var(--accent);padding:2px 9px;flex-shrink:0;transform:translateY(-2px)}
p{margin-bottom:14px}
table.data{width:100%;border-collapse:collapse;margin:14px 0 20px;font-size:13px;line-height:1.7}
table.data th{background:var(--ink);color:var(--surface);font-weight:500;text-align:left;padding:8px 12px;font-size:12px}
table.data td{padding:9px 12px;border:1px solid var(--rule);vertical-align:top}
table.data tr:nth-child(even) td{background:var(--paper)}
table.data th.num,table.data td.num{font-family:var(--mono);font-size:12px;white-space:nowrap;text-align:center}
td.pt{font-family:var(--mono);font-weight:600;text-align:center;width:64px;color:var(--accent);background:var(--accent-soft)!important}
.grade{display:inline-block;font-family:var(--mono);font-weight:600;font-size:12px;width:22px;height:22px;line-height:22px;text-align:center;border:1.5px solid currentColor;border-radius:2px;vertical-align:middle}
.grade.a{color:var(--accent)}.grade.b{color:var(--caution)}.grade.c{color:var(--ink-faint)}
.grade-label{font-family:var(--sans);font-size:12px;font-weight:500;margin-left:6px;color:var(--ink-soft);vertical-align:middle}
.note{border-left:3px solid var(--accent);background:var(--accent-soft);padding:14px 18px;margin:16px 0 20px;font-size:13.5px;line-height:1.8}
.note.warn{border-left-color:var(--caution);background:var(--caution-soft)}
.note .note-label{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;font-weight:600;color:var(--accent);display:block;margin-bottom:4px}
.note.warn .note-label{color:var(--caution)}
.coach{margin:16px 0 8px;border-top:1px solid var(--rule)}
.coach-step{padding:16px 0;border-bottom:1px solid var(--rule)}
.coach-step:last-child{border-bottom:none}
.coach-step .step-label{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;font-weight:600;color:var(--accent);display:block;margin-bottom:6px}
.coach-step p{margin:0;font-size:13.5px;line-height:1.8;color:var(--ink)}
.coach-step p.meta{font-size:12px;color:var(--ink-faint);margin-bottom:8px}
/* スコアスケール（主役要素） */
.score-scale{margin:26px 0 8px;position:relative;padding-top:26px}
.score-scale .marker{position:absolute;top:0;transform:translateX(-50%);text-align:center;font-family:var(--mono);font-size:12px;font-weight:600;color:var(--accent);line-height:1.2}
.score-scale .marker::after{content:"▼";display:block;font-size:10px}
.score-scale .bar{display:flex;height:44px;border:1px solid var(--rule-strong)}
.score-scale .band{position:relative;display:flex;flex-direction:column;justify-content:center;padding:0 8px;border-right:1px solid rgba(255,255,255,.55);color:#fff;overflow:hidden}
.score-scale .band:last-child{border-right:none}
.score-scale .band .lv{font-family:var(--mono);font-size:11px;font-weight:600;line-height:1.3}
.score-scale .band .nm{font-size:10px;line-height:1.3;white-space:nowrap;opacity:.92}
.score-scale .ticks{display:flex;font-family:var(--mono);font-size:10px;color:var(--ink-faint);margin-top:4px}
/* レーダーチャート（副次要素） */
.radar-wrap{display:flex;gap:32px;align-items:flex-start;flex-wrap:wrap;margin:20px 0}
.radar-wrap svg{flex-shrink:0}
.radar-wrap .legend{font-size:13px;flex:1;min-width:240px}
.radar-wrap .legend dl{margin:0 0 12px;display:grid;grid-template-columns:36px 1fr;gap:6px 10px;line-height:1.55}
.radar-wrap .legend dt{font-family:var(--mono);font-size:12px;font-weight:600;color:var(--accent)}
.radar-wrap .legend dd{margin:0;color:var(--ink-soft)}
.radar-wrap .legend dd strong{display:block;color:var(--ink);font-weight:600;font-size:13px}
/* レベル基準解説（控えめな表） */
table.lv-legend{width:100%;border-collapse:collapse;margin:22px 0 8px;font-size:12px;line-height:1.7;color:var(--ink-soft)}
table.lv-legend th{background:var(--paper);color:var(--ink-faint);font-weight:500;text-align:left;padding:5px 10px;font-size:11px;font-family:var(--mono);letter-spacing:.06em;border:1px solid var(--rule)}
table.lv-legend td{padding:5px 10px;border:1px solid var(--rule);vertical-align:top}
table.lv-legend td.lv-range,table.lv-legend td.lv-id{font-family:var(--mono);font-size:11px;white-space:nowrap}
table.lv-legend td.lv-id{color:var(--accent);font-weight:600}
table.lv-legend td.lv-name{white-space:nowrap}
table.lv-legend tr.current td{background:var(--accent-soft)}
table.lv-legend tr.current td:first-child{border-left:3px solid var(--accent)}
table.data tr.current td{background:var(--accent-soft)!important}
table.data tr.current td:first-child{border-left:3px solid var(--accent);font-weight:600}
table.data td.score-n{font-family:var(--mono);font-size:12px;width:36px;text-align:center;white-space:nowrap}
h3.rubric-h{font-size:15.5px;font-weight:600;margin:28px 0 10px;color:var(--ink)}
p.rubric-lede{font-size:13.5px;color:var(--ink-soft);margin-bottom:14px}
@media print{
  body{background:#fff}
  main{border:none}
  .page{padding:0}
  section{break-inside:avoid-page}
}
</style>
</head>
<body>
<main>
<div class="page">

<header class="doc-head">
  <div class="eyebrow">
    <span>SKILL ASSESSMENT REPORT — ARCHITECT TRACK</span>
    <span class="ver">FW v2.0</span>
  </div>
  <h1>AIスキル診断結果</h1>
  <div class="subtitle">生成AI技術者スキル評価フレームワーク v2.0 に基づく証拠採点</div>
  <table class="meta">
    <tr><th>SUBJECT</th><td>{{SUBJECT}}</td></tr>
    <tr><th>DATE</th><td>{{DATE}}</td></tr>
    <tr><th>EVALUATOR</th><td>{{EVALUATOR_TYPE_JA}}</td></tr>
    <tr><th>RESULT</th><td><strong>{{TOTAL_SCORE}} / 100 — {{LEVEL}}（{{LEVEL_NAME}}）</strong></td></tr>
  </table>
</header>

<section>
  <h2><span class="sec-n">1</span>総合スコア</h2>
  <div class="score-scale">
    <div class="marker" style="left:{{TOTAL_PCT}}%">{{TOTAL_SCORE}}</div>
    <div class="bar">
      <div class="band" style="flex:25;background:#b9bcc4"><span class="lv">L0</span><span class="nm">Entry</span></div>
      <div class="band" style="flex:15;background:#9aa2b3"><span class="lv">L1</span><span class="nm">Foundation</span></div>
      <div class="band" style="flex:15;background:#7c88a6"><span class="lv">L2</span><span class="nm">App Builder</span></div>
      <div class="band" style="flex:15;background:#5d6d9c"><span class="lv">L3</span><span class="nm">Practitioner</span></div>
      <div class="band" style="flex:15;background:#404f96"><span class="lv">L4</span><span class="nm">Architect</span></div>
      <div class="band" style="flex:16;background:#2b3a8f"><span class="lv">L5</span><span class="nm">Principal</span></div>
    </div>
    <div class="ticks">
      <span style="flex:25">0</span><span style="flex:15">25</span><span style="flex:15">40</span><span style="flex:15">55</span><span style="flex:15">70</span><span style="flex:16">85&nbsp;&nbsp;—&nbsp;&nbsp;100</span>
    </div>
  </div>
  <!-- レベル基準解説（フレームワーク4章より転記・変更禁止）。判定されたレベルの<tr>にのみ class="current" を付ける -->
  <table class="lv-legend">
    <tr><th>スコア</th><th>Lv</th><th>呼称</th><th>状態の説明</th></tr>
    <tr><td class="lv-range">85〜100</td><td class="lv-id">L5</td><td class="lv-name">Principal Architect</td><td>方法論を確立し、組織の標準を設計できる。全ベクトルで等級A証拠を持つ</td></tr>
    <tr><td class="lv-range">70〜84</td><td class="lv-id">L4</td><td class="lv-name">Architect</td><td>複雑なシステムを一貫した設計判断のもとで構築・指揮できる</td></tr>
    <tr><td class="lv-range">55〜69</td><td class="lv-id">L3</td><td class="lv-name">Systems Practitioner</td><td>標準的なエージェント／検索システムを自力で構築でき、一部領域で設計判断を示せる</td></tr>
    <tr><td class="lv-range">40〜54</td><td class="lv-id">L2</td><td class="lv-name">Application Builder</td><td>既存の枠組みに沿ったAIアプリケーションを構築できる</td></tr>
    <tr><td class="lv-range">25〜39</td><td class="lv-id">L1</td><td class="lv-name">Foundation</td><td>AI活用の基礎を実務に適用している。システム構築はこれから</td></tr>
    <tr><td class="lv-range">0〜24</td><td class="lv-id">L0</td><td class="lv-name">Entry</td><td>評価可能な実績が未蓄積（能力の否定ではなく、証拠の不在を意味する）</td></tr>
  </table>
  <p style="font-family:var(--mono);font-size:12px;color:var(--ink-faint)">※「Top X%」等の相対表記は校正完了まで使用しない（フレームワーク4章）</p>
</section>

<section>
  <h2><span class="sec-n">2</span>ベクトル別スコア</h2>
  <table class="data">
    <tr><th style="width:44px">V</th><th>ベクトル</th><th class="num" style="width:76px">到達度</th><th class="num" style="width:56px">重み</th><th class="num" style="width:104px">重み付き点</th><th style="width:128px">証拠の再現性</th><th style="width:110px">鮮度</th></tr>
    <!-- V1〜V5 を繰り返し -->
    <tr>
      <td class="num">{{V_ID}}</td><td>{{V_NAME}}</td>
      <td class="pt">{{RAW}} / 5</td><td class="num">{{WEIGHT}}%</td><td class="num">{{WEIGHTED}}</td>
      <td style="white-space:nowrap"><span class="grade {{GRADE_LOWER}}">{{GRADE}}</span><span class="grade-label">{{GRADE_LABEL}}</span></td><td>{{FRESHNESS_JA}}</td>
    </tr>
    <!-- 繰り返しここまで -->
    <tr><td colspan="4" style="text-align:right;font-weight:600">合計</td><td class="pt">{{TOTAL_SCORE}}</td><td colspan="2"></td></tr>
  </table>
  <p style="font-family:var(--mono);font-size:12px;color:var(--ink-faint);margin:8px 0 0;line-height:1.65">到達度（0〜5）。各点の意味は§3「到達度の採点基準」。証拠の再現性＝成果物の検証しやすさ（A 再現可能／B 設計文書／C 記述のみ）。<strong style="color:var(--ink-soft)">両者は独立</strong> — 到達度が高くても再現性Bなら<b>上限3点</b>（4点以上不可）。</p>
  <div class="note" style="margin-top:10px">
    <span class="note-label">再現性の判定（提出時の取り違え注意）</span>
    <ul style="margin:6px 0 0;padding-left:1.2em;font-size:13px;line-height:1.6;color:var(--ink-soft)">
      <li><b>A</b>: 検証用URL／ファイル＋手順（社内限定可・ガイド内記載可）。採点AIがセッション内で確認できること</li>
      <li><b>B</b>: 設計説明だけのガイド、SNS投稿・ブログ記事（検証先・手順・評価結果の数値なし）</li>
      <li>詳細: 配布物 <code>user-guide.html</code> §2「提出前チェックリスト」</li>
    </ul>
  </div>


  <h3 class="rubric-h">重みと重み付き点</h3>
  <p class="rubric-lede">合計100点は次式で決まる（フレームワーク3章）。</p>
  <table class="data">
    <tr><th style="width:28%">項目</th><th>内容</th></tr>
    <tr><td>計算式</td><td><code>重み付き点 = 到達度 × 重み(%) ÷ 5</code>（小数第1位）。例: 到達度4・重み25% → 4 × 25 ÷ 5 = <strong>20.0</strong></td></tr>
    <tr><td>合計</td><td>V1〜V5の重み付き点の和（0〜100）</td></tr>
    <tr><td>÷5 の意味</td><td>到達度は0〜5。到達度5のとき、そのベクトルの重み％がそのまま満点寄与になるように正規化する（V1なら最大25.0点）</td></tr>
  </table>
  <table class="data" style="margin-top:14px">
    <tr><th style="width:44px">V</th><th>重み</th><th class="num">到達度5のときの満点寄与</th><th>数値根拠（なぜこの重みか）</th></tr>
    <tr><td class="num">V1</td><td class="num">25%</td><td class="num">25.0</td><td rowspan="2">Architect Trackの中核。コンテキスト設計とエージェント構造の質に、他軸の成果が従属するため最重視</td></tr>
    <tr><td class="num">V2</td><td class="num">25%</td><td class="num">25.0</td></tr>
    <tr><td class="num">V3</td><td class="num">20%</td><td class="num">20.0</td><td>実務価値への直結度は高いが、中核2軸の従属側として一段軽くした</td></tr>
    <tr><td class="num">V4</td><td class="num">15%</td><td class="num">15.0</td><td rowspan="2">設計を検証・運用可能にする支援的性格。合計への寄与上限は V1/V2 より小さい</td></tr>
    <tr><td class="num">V5</td><td class="num">15%</td><td class="num">15.0</td></tr>
  </table>
  <p style="font-size:12.5px;color:var(--ink-soft);margin-top:10px;line-height:1.7">重み 25/25/20/15/15 はパイロット前の仮設定（FW 7章）。運用データに基づき改訂され得る。詳細は正本 <code>genai-skill-framework-v2</code> 3章「重みの根拠」。</p>

  <div class="radar-wrap">
    <svg width="400" height="380" viewBox="0 0 400 380" role="img" aria-label="5ベクトルのレーダーチャート">
      <!-- グリッド（到達度1〜5の五角形） -->
      <polygon points="200,172 226.6,191.3 216.5,222.7 183.5,222.7 173.4,191.3" fill="none" stroke="#dcdcd6" stroke-width="1"/>
      <polygon points="200,144 253.3,182.7 232.9,245.3 167.1,245.3 146.7,182.7" fill="none" stroke="#dcdcd6" stroke-width="1"/>
      <polygon points="200,116 279.9,174.0 249.4,268.0 150.6,268.0 120.1,174.0" fill="none" stroke="#dcdcd6" stroke-width="1"/>
      <polygon points="200,88 306.5,165.4 265.9,290.6 134.1,290.6 93.5,165.4" fill="none" stroke="#dcdcd6" stroke-width="1"/>
      <polygon points="200,60 333.1,156.7 282.3,313.3 117.7,313.3 66.9,156.7" fill="none" stroke="#b9b9b0" stroke-width="1.5"/>
      <!-- 軸線 -->
      <line x1="200" y1="200" x2="200" y2="60" stroke="#dcdcd6"/>
      <line x1="200" y1="200" x2="333.1" y2="156.7" stroke="#dcdcd6"/>
      <line x1="200" y1="200" x2="282.3" y2="313.3" stroke="#dcdcd6"/>
      <line x1="200" y1="200" x2="117.7" y2="313.3" stroke="#dcdcd6"/>
      <line x1="200" y1="200" x2="66.9" y2="156.7" stroke="#dcdcd6"/>
      <!-- スコア多角形（座標は下の計算式で算出して置換） -->
      <polygon points="{{RADAR_POINTS}}" fill="rgba(43,58,143,.14)" stroke="#2b3a8f" stroke-width="2"/>
      <!-- 軸ラベル -->
      <text x="200" y="46" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="12" fill="#4b4f57">V1</text>
      <text x="348" y="152" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="12" fill="#4b4f57">V2</text>
      <text x="290" y="332" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="12" fill="#4b4f57">V3</text>
      <text x="110" y="332" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="12" fill="#4b4f57">V4</text>
      <text x="52" y="152" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="12" fill="#4b4f57">V5</text>
    </svg>
    <div class="legend">
      <dl>
        <dt>V1</dt><dd><strong>Context Engineering — コンテキスト設計力</strong>要件をLLMが解釈しやすい形に翻訳・構造化できる</dd>
        <dt>V2</dt><dd><strong>Agentic System Design — エージェント設計力</strong>安全に稼働を続け、実務品質で動くエージェントを設計できる</dd>
        <dt>V3</dt><dd><strong>Knowledge Architecture — 知識アーキテクチャ</strong>課題に合わせて知識の参照方法を設計できる（RAGに限らない）</dd>
        <dt>V4</dt><dd><strong>Evaluation &amp; Observability — 評価・観測</strong>AIの出力品質を数値で捉え、劣化原因を切り分けて改善できる</dd>
        <dt>V5</dt><dd><strong>Production &amp; LLMOps — 本番・運用</strong>AIシステムを本番で動かし続けられる（コスト・リスク含む。インフラ構築だけではない）</dd>
      </dl>
      <p style="font-size:12px;color:var(--ink-faint)">外周＝到達度5。グリッドは到達度1刻み。</p>
    </div>
  </div>
</section>

<section>
  <h2><span class="sec-n">3</span>到達度の採点基準</h2>
  <h3 class="rubric-h">到達度0〜5の行動基準</h3>
  <p class="rubric-lede">各ベクトルの到達度は次の行動基準で決まる（フレームワーク3章・ツール非依存）。<strong>いまの到達度の行</strong>を強調表示する（生成時は該当行に <code>class="current"</code> と「← 今回」を付ける）。到達には証拠の再現性上限もかかる（Bなら上限3点）。</p>
  <table class="data">
    <tr><th colspan="2">V1 Context Engineering — コンテキスト設計力</th></tr>
    <tr><th class="num" style="width:56px;background:var(--ink)">到達度</th><th style="background:var(--ink)">行動基準</th></tr>
    <tr><td class="score-n">0</td><td>プロンプトの試行錯誤のみ。設計の記録がない</td></tr>
    <tr><td class="score-n">1</td><td>基本的なプロンプト技法（例示提示・段階的推論の誘導）を意図的に使い分けている</td></tr>
    <tr><td class="score-n">2</td><td>長大な入力に対する分割・要約・優先順位付けの戦略を設計し、文書化している</td></tr>
    <tr><td class="score-n">3</td><td>コンテキストの構造的劣化（中間情報の欠落等）を予見した階層的コンテキスト設計を実装している</td></tr>
    <tr><td class="score-n">4</td><td>ドメイン固有のコンテキストスキーマ（構造化された仕様記述形式）を定義し、再現可能な形で運用している</td></tr>
    <tr><td class="score-n">5</td><td>複数エージェント間の状態受け渡し規約を設計・実装し、要件の翻訳から状態設計まで一貫した方法論として文書化している</td></tr>
  </table>
  <table class="data">
    <tr><th colspan="2">V2 Agentic System Design — エージェント設計力</th></tr>
    <tr><th class="num" style="width:56px;background:var(--ink)">到達度</th><th style="background:var(--ink)">行動基準</th></tr>
    <tr><td class="score-n">0</td><td>チャットUIの利用のみ</td></tr>
    <tr><td class="score-n">1</td><td>ノーコード／ローコード基盤で基本的なワークフローを構築できる</td></tr>
    <tr><td class="score-n">2</td><td>ツール呼び出し（外部API・検索・計算）を組み込んだエージェントを構築している</td></tr>
    <tr><td class="score-n">3</td><td>複数ツールを連携させたエージェントを構築し、失敗時のフォールバックを設計している</td></tr>
    <tr><td class="score-n">4</td><td>複数エージェントの役割分担（計画・実行・検証等）を設計し、暴走防止（ループ上限・状態機械・人間の承認点）を実装している</td></tr>
    <tr><td class="score-n">5</td><td>本番相当のエージェントシステムを、安全機構・権限設計・出力品質制御を含む一貫した設計文書とともに構築・運用している</td></tr>
  </table>
  <table class="data">
    <tr><th colspan="2">V3 Knowledge Architecture — 知識アーキテクチャ</th></tr>
    <tr><th class="num" style="width:56px;background:var(--ink)">到達度</th><th style="background:var(--ink)">行動基準</th></tr>
    <tr><td class="score-n">0</td><td>知識参照の仕組みを構築した実績がない</td></tr>
    <tr><td class="score-n">1</td><td>文書を分割してベクトル検索する基本構成を構築している</td></tr>
    <tr><td class="score-n">2</td><td>メタデータ設計・フィルタリングにより検索対象を制御している</td></tr>
    <tr><td class="score-n">3</td><td>課題特性に応じて検索方式（キーワード・ベクトル・ハイブリッド・再ランキング・長文コンテキスト直接投入）を比較検討し、根拠をもって選定している</td></tr>
    <tr><td class="score-n">4</td><td>複雑な文書（図表・数式・多階層構造）に対するパース・インデックス戦略を設計し、精度を定量比較している</td></tr>
    <tr><td class="score-n">5</td><td>ドメイン全体の知識構造（階層・関係性・鮮度）を設計し、検索精度の改善を数値で実証している。「検索基盤を作らない」判断を含む最適化ができている</td></tr>
  </table>
  <table class="data">
    <tr><th colspan="2">V4 Evaluation & Observability — 評価・観測</th></tr>
    <tr><th class="num" style="width:56px;background:var(--ink)">到達度</th><th style="background:var(--ink)">行動基準</th></tr>
    <tr><td class="score-n">0</td><td>目視確認のみ</td></tr>
    <tr><td class="score-n">1</td><td>良否判定の基準を決めて手動評価している</td></tr>
    <tr><td class="score-n">2</td><td>テストケース集（想定入力と期待出力）を作成・維持している</td></tr>
    <tr><td class="score-n">3</td><td>忠実性・関連性等の指標を定義し、計測している</td></tr>
    <tr><td class="score-n">4</td><td>自動評価パイプラインを構築し、変更のたびに回帰評価している</td></tr>
    <tr><td class="score-n">5</td><td>評価結果に基づいて原因を峻別し、改善前後の数値比較を伴う改善サイクルを文書化・公開している</td></tr>
  </table>
  <table class="data">
    <tr><th colspan="2">V5 Production & LLMOps — 本番・運用</th></tr>
    <tr><th class="num" style="width:56px;background:var(--ink)">到達度</th><th style="background:var(--ink)">行動基準</th></tr>
    <tr><td class="score-n">0</td><td>ブラウザ上のサービス利用のみ</td></tr>
    <tr><td class="score-n">1</td><td>API呼び出しを含むスクリプトをローカルで実行できる</td></tr>
    <tr><td class="score-n">2</td><td>コンテナ技術で依存関係を分離した開発環境を構築・文書化している</td></tr>
    <tr><td class="score-n">3</td><td>ローカル推論環境とデータベースを構築し、アプリケーションと結合している</td></tr>
    <tr><td class="score-n">4</td><td>モデル選定（商用API vs OSS）・量子化・インフラ構成を、コスト試算とデータ漏洩リスク評価を根拠に選定している</td></tr>
    <tr><td class="score-n">5</td><td>監視・ログ・障害対応・コスト管理を含む運用を継続し、その記録を文書化している</td></tr>
  </table>
</section>

<section>
  <h2><span class="sec-n">4</span>採点理由と根拠資料</h2>
  <!-- V1〜V5 を繰り返し -->
  <table class="data">
    <tr><th colspan="2">{{V_ID}} {{V_NAME}} — {{RAW}} / 5</th></tr>
    <tr><td style="width:132px;background:var(--paper);font-family:var(--mono);font-size:11px">採点理由</td><td>{{RATIONALE}}</td></tr>
    <tr><td style="background:var(--paper);font-family:var(--mono);font-size:11px">根拠資料</td><td>{{EVIDENCE_LIST}}</td></tr>
    <tr><td style="background:var(--paper);font-family:var(--mono);font-size:11px">確認事項</td><td>深掘り確認: {{DEEP_DIVE_JA}} ／ 必須観点: {{MANDATORY_JA}} ／ 鮮度例外: {{EXCEPTION_JA}}</td></tr>
  </table>
  <!-- 繰り返しここまで -->
</section>

<section>
  <h2><span class="sec-n">5</span>警告・適用ルール</h2>
  <!-- 警告がある場合のみ .note.warn を列挙。ない場合は「適用された上限・減衰はない」と1行記す -->
  <div class="note warn">
    <span class="note-label">WARNING</span>
    {{WARNING_TEXT}}
  </div>
</section>

<section>
  <h2><span class="sec-n">6</span>次の一手</h2>
  <p>重み付き点が最も低いベクトルを焦点に、次の四半期で<strong>証拠の再現性A（再現可能な成果物）を1つ作る</strong>（フレームワーク6.2章）。以下はコーチング形式の行動設計である。</p>
  <div class="coach">
    <div class="coach-step">
      <span class="step-label">1 · 焦点</span>
      <p class="meta">対象: {{LOWEST_V_ID}} {{LOWEST_V_NAME}}（重み付き点 {{LOWEST_WEIGHTED}}）</p>
      <p>{{COACH_FOCUS}}</p>
    </div>
    <div class="coach-step">
      <span class="step-label">2 · 現状</span>
      <p>{{COACH_REALITY}}</p>
    </div>
    <div class="coach-step">
      <span class="step-label">3 · 90日の一手</span>
      <p>{{COACH_ACTION}}</p>
    </div>
    <div class="coach-step">
      <span class="step-label">4 · 完了の定義</span>
      <p>{{COACH_DONE}}</p>
    </div>
    <div class="coach-step">
      <span class="step-label">振り返り質問</span>
      <p>{{COACH_REFLECT}}</p>
    </div>
  </div>
  {{CEILING_INSIGHTS_HTML}}
  <p style="margin-top:40px;padding-top:20px;border-top:1px solid var(--rule);font-family:var(--mono);font-size:11px;color:var(--ink-faint);letter-spacing:.08em">
    FW-GENAI-SKILL v2.0 ／ 本結果は本人に全項目開示・再評価申請可・処遇査定には直接使用しない（HR運用原則）
  </p>
</section>

</div>
</main>
</body>
</html>
```

### 置換の規則

| プレースホルダ | 値 |
|---------------|-----|
| `{{TOTAL_PCT}}` | 合計点をそのまま%として使用（0〜100） |
| `{{RADAR_POINTS}}` | 5点の座標を空白区切りで連結。各ベクトルの座標は `x = 200 + 28 × 到達度 × cosθ`、`y = 200 + 28 × 到達度 × sinθ`（小数第1位）。cosθ/sinθ: V1=(0, -1)、V2=(0.951, -0.309)、V3=(0.588, 0.809)、V4=(-0.588, 0.809)、V5=(-0.951, -0.309)。到達度0は中心 (200,200) |
| `{{GRADE}}` / `{{GRADE_LOWER}}` | 証拠の再現性の記号（A/B/C）とその小文字（a/b/c）。証拠なしは `—` とし class を付けない |
| `{{GRADE_LABEL}}` | 記号に対応する表示名。A→再現可能／B→設計文書／C→記述のみ。証拠なしは空文字 |
| `{{FRESHNESS_JA}}` | 12ヶ月以内 / 12〜24ヶ月 / 24ヶ月超 / —（証拠なし） |
| `{{WARNING_TEXT}}` | 証拠の再現性による上限・鮮度減衰・必須観点未達・深掘り未実施・証拠不在の適用内容を列挙。複数あれば .note.warn を複数出力 |
| `{{EVIDENCE_LIST}}` | URL はリンク（`<a href>`）、パスはそのまま。複数は `<br>` 区切り |
| `{{LOWEST_V_ID}}` / `{{LOWEST_V_NAME}}` / `{{LOWEST_WEIGHTED}}` | 重み付き点が最低のベクトル（同点なら重みの大きい方） |
| `{{COACH_FOCUS}}` | 焦点: なぜそのベクトルを次にするか（1〜2文。称賛・強み活用は書かない） |
| `{{COACH_REALITY}}` | 現状: 確認できた事実と不足（事実のみ） |
| `{{COACH_ACTION}}` | 90日の一手: 具体的な実験を1つだけ |
| `{{COACH_DONE}}` | 完了の定義: 証拠の再現性A相当と判断できる条件 |
| `{{COACH_REFLECT}}` | 振り返り質問を1つ |
| `{{CEILING_INSIGHTS_HTML}}` | 到達度4のベクトルが無いときは**空文字**。あるときは下記「次の壁の見分け」HTMLブロック（最大2本） |

`{{CEILING_INSIGHTS_HTML}}` の出力形（該当時）:

```html
  <h3 class="rubric-h" style="margin-top:36px">次の壁の見分け（よくある取り違え）</h3>
  <p class="rubric-lede">主たる次の一手の優先順位は変えない。到達度4のベクトルについて、「できたつもり」になりやすい取り違えと、行動基準5の見分けだけを示す（任意・再評価時）。</p>
  <div class="coach">
    <div class="coach-step">
      <span class="step-label">{{CEILING_V_ID}} · よくある取り違え</span>
      <p class="meta">いまの到達度 4 → 次の壁は 5</p>
      <p>{{CEILING_MISREAD}}</p>
    </div>
    <div class="coach-step">
      <span class="step-label">{{CEILING_V_ID}} · 本当の5</span>
      <p>{{CEILING_ACTUAL}}</p>
    </div>
    <div class="coach-step">
      <span class="step-label">{{CEILING_V_ID}} · 振り返り質問</span>
      <p>{{CEILING_REFLECT}}</p>
    </div>
    <!-- 2本目がある場合は同じ3ステップを繰り返す -->
  </div>
```

JSON には任意で `ceiling_insights` 配列を付けてよい（無くても可）:

```json
"ceiling_insights": [
  {
    "vector": "V1",
    "from_score": 4,
    "misread": "…",
    "actual_n1": "…",
    "reflect": "…"
  }
]
```

### 生成後の自己チェック（必須）

1. 主役（スコア横バー）1つ＋副次（レーダー・バッジ）の構成が守られているか
2. グラデーション・絵文字・称賛文言・ダークモードが混入していないか
3. 表示数値がJSONと完全に一致しているか
4. 「次の壁の見分け」が条件（到達度4）を満たすときだけ出ており、主たる次の一手より前に置いていないか。パーセンタイル表現が混入していないか
5. ブラウザ表示確認をユーザーに依頼したか
