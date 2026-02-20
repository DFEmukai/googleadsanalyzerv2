# Google Ads AI Agent - システム仕様書

## 1. システム概要

### 1.1 Google Ads AI Agentとは

Google Ads AI Agentは、Google広告アカウントの運用を自動化・最適化するためのAIエージェントシステムです。Claude AIを活用して広告パフォーマンスを分析し、改善提案を自動生成します。運用担当者は提案を確認・承認するだけで、実際の変更をGoogle Ads APIを通じて自動実行できます。

### 1.2 主な機能一覧

| 機能カテゴリ | 機能名 | 説明 |
|-------------|--------|------|
| **分析** | 週次自動分析 | 毎週月曜7時にGoogle Adsデータを取得し、AIが分析・提案を生成 |
| **ダッシュボード** | KPIサマリー | 費用・CV数・CPA・CTR・ROAS等の主要KPIを可視化 |
| | トレンドチャート | 週次KPI推移をグラフ表示 |
| | キャンペーン別 | キャンペーンごとの詳細KPIと日別トレンド |
| **改善提案** | 提案一覧 | カテゴリ・優先度別に改善提案を表示 |
| | 壁打ち機能 | Claude AIと提案内容について対話的に議論 |
| | 承認フロー | 提案の承認・却下・スケジュール実行 |
| | 自動実行 | 承認済み提案をGoogle Ads APIで自動反映 |
| | ロールバック | 実行後24時間以内なら元に戻せる |
| **効果測定** | 効果レポート | 実行前後のKPI比較で施策効果を可視化 |
| **通知** | Chatwork連携 | レポート・提案をChatworkに自動通知 |

---

## 2. アーキテクチャ

### 2.1 システム構成図

```
┌─────────────────────────────────────────────────────────────────┐
│                        フロントエンド                            │
│                    Next.js 15 (App Router)                      │
│                    Tailwind CSS + Recharts                      │
└─────────────────────────────────┬───────────────────────────────┘
                                  │ REST API
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        バックエンド                              │
│                      FastAPI (Python)                           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ APIルーター   │  │ スケジューラ  │  │ サービス層    │          │
│  │ (campaigns,  │  │ (APScheduler)│  │ (Analyzer,   │          │
│  │  proposals,  │  │              │  │  Executor,   │          │
│  │  reports)    │  │              │  │  Chatwork)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │  Google Ads API │    │   Claude API    │
│   (データベース)  │    │  (広告データ取得/ │    │  (AI分析/提案)   │
│                 │    │   変更実行)      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                              ┌────────┴────────┐
                                              ▼                 ▼
                                    ┌─────────────────┐  ┌──────────┐
                                    │  Chatwork API   │  │   壁打ち  │
                                    │  (通知/タスク)   │  │  チャット │
                                    └─────────────────┘  └──────────┘
```

### 2.2 バックエンド（FastAPI）

- **フレームワーク**: FastAPI 0.115+
- **言語**: Python 3.11+
- **ORM**: SQLAlchemy 2.0+ (非同期)
- **マイグレーション**: Alembic
- **スケジューラ**: APScheduler
- **HTTPクライアント**: httpx

**ディレクトリ構造**:
```
backend/app/
├── api/v1/          # APIエンドポイント定義
├── db/              # データベース接続・リポジトリ
├── models/          # SQLAlchemyモデル
├── schemas/         # Pydanticスキーマ（リクエスト/レスポンス）
├── services/        # ビジネスロジック
├── config.py        # 設定管理
└── main.py          # アプリケーションエントリポイント
```

### 2.3 フロントエンド（Next.js）

- **フレームワーク**: Next.js 15 (App Router)
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS
- **チャートライブラリ**: Recharts
- **アイコン**: Lucide React

**ディレクトリ構造**:
```
frontend/src/
├── app/             # ページコンポーネント
│   ├── dashboard/   # ダッシュボード
│   ├── campaigns/   # キャンペーン一覧・詳細
│   ├── proposals/   # 改善提案
│   └── reports/     # レポート
├── components/      # 共通コンポーネント
└── lib/             # ユーティリティ・型定義・API
```

### 2.4 データベース（PostgreSQL）

- **バージョン**: PostgreSQL 16
- **ドライバ**: asyncpg（非同期）
- **接続方式**: Cloud SQL Private IP（本番）/ localhost（開発）

### 2.5 外部連携

| サービス | 用途 | APIバージョン |
|---------|------|--------------|
| Google Ads API | 広告データ取得・変更実行 | v18 |
| Anthropic Claude API | AI分析・提案生成・壁打ち | claude-sonnet-4 |
| Chatwork API | 通知・タスク登録 | v2 |

---

## 3. 機能詳細

### 3.1 ダッシュボード

#### 全体サマリー
- **表示項目**: 費用、CV数、CPA、CTR、ROAS、インプレッション（直近7日間）
- **シグナル表示**: 各KPIを緑（良好）/黄（注意）/赤（要対応）/青（情報）で色分け
- **前週比較**: 直近7日間と、その前の7日間（8日前〜14日前）を比較
- **トレンドチャート**: 直近7日間の日別KPI推移をグラフ表示（X軸に各日付を表示）

#### キャンペーン別ダッシュボード
- **キャンペーン情報**: 名前、ステータス、タイプ
- **KPIカード**: 費用、CV数、CPA、CTR、ROAS、インプレッション
- **日別トレンド**: CPA推移、CV数推移、費用推移、ROAS推移
- **期間選択**: 7日/14日/30日
- **関連提案**: このキャンペーンに対する改善提案一覧

### 3.2 キャンペーン一覧・詳細

- **一覧表示**: 全キャンペーンをテーブル形式で表示
- **ソート機能**: キャンペーン名、費用、CV数、CPA、CTR、ROASでソート可能
- **ステータス表示**: active（有効）、paused（停止中）、ended（終了）
- **クリック遷移**: 行クリックでキャンペーン別ダッシュボードへ遷移
- **フィルタリング**: 有効キャンペーンのみを分析対象に

### 3.3 週次レポート

- **自動生成**: 毎週月曜7:00 JSTに自動実行
- **分析期間**: 前週（月曜〜日曜）のパフォーマンスデータ
- **分析内容**:
  - パフォーマンス総括（費用、CV数、CPA、CTR、ROAS）
  - キャンペーン別パフォーマンス
  - 広告グループ別パフォーマンス
  - キーワードパフォーマンス（上位50件）
  - 検索語句レポート（上位50件）
  - デバイス別パフォーマンス
  - 時間帯・曜日別パフォーマンス
  - 地域別パフォーマンス
  - オークション分析（競合）
  - 広告文パフォーマンス

### 3.4 改善提案

#### 提案カテゴリ
| カテゴリ | 説明 | 実行方式 |
|---------|------|---------|
| keyword | キーワード追加・除外・入札調整 | 自動 |
| creative | 広告コピー（テキスト）改善 | 自動 |
| manual_creative | 画像・動画アセット改善 | 手動（Chatworkタスク） |
| targeting | ターゲティング改善 | 自動 |
| budget | 予算配分改善 | 自動 |
| bidding | 入札戦略改善 | 自動 |
| competitive_response | 競合対応 | 自動/手動 |

#### 優先度
- **high**: CPAが目標を大幅に超過、大きな機会損失、即座に対応が必要
- **medium**: 改善余地がある、効率化の機会、中期的な改善
- **low**: 微調整、テスト的な施策、長期的な改善

#### 壁打ち機能
- Claude AIと改善提案について対話的に議論
- 提案の根拠確認、代替案の検討、実装方法の相談が可能
- 会話履歴は提案ごとに保存

### 3.5 効果レポート

- **測定タイミング**: 提案実行後に自動でスナップショットを取得
- **比較期間**: 実行前7日間 vs 実行後7日間
- **比較項目**: 費用、CV数、CPA、CTR、ROAS、インプレッション、クリック、CV値
- **変化率表示**: 各KPIの変化率を算出して表示

### 3.6 承認フロー

#### ステータス遷移
```
pending（承認待ち）
    ├── approved（承認済み）→ executed（実行済み）
    │                              └── [24時間以内] ロールバック可能
    ├── rejected（却下）
    └── skipped（スキップ）
```

#### 承認オプション
- **即時実行**: 承認と同時にGoogle Ads APIで変更を実行
- **スケジュール実行**: 指定日時に自動実行
- **編集して承認**: 提案内容を編集してから承認

#### セーフガード機能
- 1回の承認で変更可能な件数上限（デフォルト: 10件）
- 予算変更率の上限（デフォルト: 20%）
- 実行前の警告表示

#### ロールバック
- 実行後24時間以内なら元の状態に戻せる
- ロールバック履歴を記録

### 3.7 Chatwork連携

- **レポート通知**: 週次レポート完了時にサマリーを送信
- **提案通知**: 改善提案の概要と優先度を通知
- **タスク登録**: manual_creative提案を担当者にタスク登録
- **メンション**: 指定したユーザーにメンション通知

### 3.8 週次スケジューラ

- **実行タイミング**: 毎週月曜 7:00 JST（設定変更可能）
- **処理内容**:
  1. Google Ads APIから前週のパフォーマンスデータを取得
  2. Claude AIでデータを分析し改善提案を生成
  3. レポートと提案をデータベースに保存
  4. 非アクティブキャンペーンの古い提案を自動スキップ
  5. 実行済み提案の効果測定スナップショットを収集
  6. Chatworkに通知を送信
- **ミスファイア対応**: 1時間以内なら遅延実行

### 3.9 キャンペーンフィルタリング

- **分析対象**: `ENABLED`（有効）ステータスのキャンペーンのみ
- **除外対象**: `PAUSED`（停止中）、`REMOVED`（削除済み）
- **提案フィルタ**: 非アクティブキャンペーンの提案は一覧から自動除外
- **クリーンアップ**: 週次分析時に古い提案を自動スキップ

### 3.10 提案クリーンアップ

#### 自動クリーンアップ
- 週次分析実行時に自動実行
- 対象: `pending`ステータスで、`target_campaign`が設定されており、
  そのキャンペーンが非アクティブまたは存在しない提案
- アクション: ステータスを`skipped`に変更

#### 手動クリーンアップ
- `POST /api/v1/proposals/cleanup` エンドポイントで実行
- `dry_run=true`: クリーンアップ対象のプレビュー
- `dry_run=false`: 実際にステータスを変更

---

## 4. APIエンドポイント一覧

### 4.1 ダッシュボード

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/dashboard/summary` | 直近7日間のKPIサマリーを取得（Google Ads APIからリアルタイム取得） |
| GET | `/api/v1/dashboard/trends` | 日別KPIトレンドデータを取得（days=1-30、デフォルト7日） |

### 4.2 キャンペーン

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/campaigns` | キャンペーン一覧を取得（フィルタ・ソート対応） |
| GET | `/api/v1/campaigns/{campaign_id}` | キャンペーン詳細を取得 |
| GET | `/api/v1/campaigns/{campaign_id}/dashboard` | キャンペーン別ダッシュボードを取得（days=1-90） |

### 4.3 レポート

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/reports` | 週次レポート一覧を取得（limit, offset） |
| GET | `/api/v1/reports/latest` | 最新の週次レポートを取得 |
| GET | `/api/v1/reports/{report_id}` | 特定のレポート詳細を取得 |

### 4.4 改善提案

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/proposals` | 提案一覧を取得（status, category, priority, report_idでフィルタ） |
| GET | `/api/v1/proposals/{proposal_id}` | 提案詳細を取得 |
| PATCH | `/api/v1/proposals/{proposal_id}/status` | 提案ステータスを更新 |
| POST | `/api/v1/proposals/{proposal_id}/approve` | 提案を承認（スケジュール・編集対応） |
| POST | `/api/v1/proposals/{proposal_id}/reject` | 提案を却下 |
| POST | `/api/v1/proposals/{proposal_id}/execute` | 承認済み提案を実行 |
| POST | `/api/v1/proposals/{proposal_id}/rollback` | 実行済み提案をロールバック |
| POST | `/api/v1/proposals/{proposal_id}/safeguard-check` | セーフガードチェック |
| POST | `/api/v1/proposals/{proposal_id}/chat` | 壁打ちチャット |
| GET | `/api/v1/proposals/{proposal_id}/chat/history` | チャット履歴を取得 |
| GET | `/api/v1/proposals/{proposal_id}/impact` | 効果レポートを取得 |
| POST | `/api/v1/proposals/cleanup` | 非アクティブキャンペーンの提案をスキップ（dry_run対応） |

### 4.5 分析

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/v1/analysis/run` | 手動で週次分析を実行（start_date, end_date指定可） |

### 4.6 Chatwork

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/chatwork/status` | Chatwork設定状況を確認 |
| POST | `/api/v1/chatwork/test` | テストメッセージを送信 |
| POST | `/api/v1/chatwork/notify/{report_id}` | 特定レポートの通知を送信 |

### 4.7 ヘルスチェック

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/health` | ヘルスチェック（status, version, next_scheduled_analysis） |

---

## 5. データベーススキーマ

### 5.1 campaigns（キャンペーン）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| campaign_id | VARCHAR | UNIQUE, INDEX | Google Ads キャンペーンID |
| campaign_name | VARCHAR | NOT NULL | キャンペーン名 |
| campaign_type | ENUM | NOT NULL | search, display, pmax, video |
| status | ENUM | NOT NULL, DEFAULT 'active' | active, paused, ended |
| first_seen_at | TIMESTAMP | NOT NULL | 初回検出日時 |
| last_seen_at | TIMESTAMP | NOT NULL | 最終更新日時 |
| ended_at | TIMESTAMP | NULLABLE | 終了日時 |
| created_at | TIMESTAMP | NOT NULL | レコード作成日時 |

### 5.2 weekly_reports（週次レポート）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| week_start_date | DATE | NOT NULL | 週開始日（月曜） |
| week_end_date | DATE | NOT NULL | 週終了日（日曜） |
| raw_data | JSONB | NULLABLE | パフォーマンスデータ |
| analysis_summary | TEXT | NULLABLE | 分析サマリー |
| kpi_snapshot | JSONB | NULLABLE | KPIスナップショット |
| created_at | TIMESTAMP | NOT NULL | レコード作成日時 |

### 5.3 improvement_proposals（改善提案）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| report_id | UUID | FK → weekly_reports.id | 親レポート |
| category | ENUM | NOT NULL | 提案カテゴリ |
| priority | ENUM | NOT NULL | 優先度 |
| title | TEXT | NOT NULL | タイトル |
| description | TEXT | NULLABLE | 詳細説明 |
| expected_effect | TEXT | NULLABLE | 期待効果 |
| action_steps | JSONB | NULLABLE | 実行ステップ |
| target_campaign | VARCHAR | NULLABLE | 対象キャンペーン名 |
| target_ad_group | VARCHAR | NULLABLE | 対象広告グループ名 |
| status | ENUM | NOT NULL, DEFAULT 'pending' | ステータス |
| created_at | TIMESTAMP | NOT NULL | レコード作成日時 |

### 5.4 proposal_executions（提案実行履歴）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| proposal_id | UUID | FK → improvement_proposals.id | 親提案 |
| executed_at | TIMESTAMP | NOT NULL | 実行日時 |
| executed_by | VARCHAR | NULLABLE | 実行者 |
| execution_notes | TEXT | NULLABLE | 実行メモ |
| actual_changes | JSONB | NULLABLE | 実際の変更内容 |

### 5.5 proposal_results（提案結果）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| proposal_id | UUID | FK → improvement_proposals.id | 親提案 |
| measured_at | TIMESTAMP | NOT NULL | 測定日時 |
| measurement_period | VARCHAR | NULLABLE | 測定期間 |
| before_metrics | JSONB | NULLABLE | 実行前KPI |
| after_metrics | JSONB | NULLABLE | 実行後KPI |
| effect_summary | TEXT | NULLABLE | 効果サマリー |
| effect_percentage | NUMERIC(10,2) | NULLABLE | 効果率 |
| ai_evaluation | TEXT | NULLABLE | AI評価 |

### 5.6 proposal_conversations（壁打ち会話）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| proposal_id | UUID | FK (CASCADE) | 親提案 |
| role | ENUM | NOT NULL | user, assistant |
| content | TEXT | NOT NULL | メッセージ内容 |
| created_at | TIMESTAMP | NOT NULL | 送信日時 |

### 5.7 proposal_snapshots（KPIスナップショット）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| proposal_id | UUID | FK (CASCADE) | 親提案 |
| snapshot_type | ENUM | NOT NULL | before, after |
| campaign_id | VARCHAR | NULLABLE | キャンペーンID |
| cost | NUMERIC(12,2) | NULLABLE | 費用 |
| conversions | NUMERIC(10,2) | NULLABLE | CV数 |
| cpa | NUMERIC(10,2) | NULLABLE | CPA |
| ctr | NUMERIC(8,4) | NULLABLE | CTR |
| roas | NUMERIC(10,2) | NULLABLE | ROAS |
| impressions | NUMERIC(12,0) | NULLABLE | インプレッション |
| clicks | NUMERIC(12,0) | NULLABLE | クリック数 |
| conversion_value | NUMERIC(12,2) | NULLABLE | CV値 |
| period_start | DATE | NOT NULL | 期間開始日 |
| period_end | DATE | NOT NULL | 期間終了日 |
| created_at | TIMESTAMP | NOT NULL | レコード作成日時 |

### 5.8 auction_insights（オークション分析）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| report_id | UUID | FK → weekly_reports.id | 親レポート |
| competitor_domain | VARCHAR | NOT NULL | 競合ドメイン |
| impression_share | NUMERIC(5,4) | NULLABLE | インプレッションシェア |
| overlap_rate | NUMERIC(5,4) | NULLABLE | 重複率 |
| position_above_rate | NUMERIC(5,4) | NULLABLE | 上位表示率 |
| top_of_page_rate | NUMERIC(5,4) | NULLABLE | ページ上部表示率 |
| outranking_share | NUMERIC(5,4) | NULLABLE | 優位表示シェア |

---

## 6. 環境変数一覧

### 6.1 データベース

| 変数名 | 説明 | 例 |
|--------|------|-----|
| DATABASE_URL | PostgreSQL接続URL | postgresql+asyncpg://user:pass@host:5432/db |

### 6.2 Google Ads API

| 変数名 | 説明 | 例 |
|--------|------|-----|
| GOOGLE_ADS_DEVELOPER_TOKEN | 開発者トークン | XXXXXXXXXXXXXXXX |
| GOOGLE_ADS_CLIENT_ID | OAuth クライアントID | xxx.apps.googleusercontent.com |
| GOOGLE_ADS_CLIENT_SECRET | OAuth クライアントシークレット | GOCSPX-xxxxx |
| GOOGLE_ADS_REFRESH_TOKEN | OAuthリフレッシュトークン | 1//xxxxxx |
| GOOGLE_ADS_CUSTOMER_ID | 広告アカウントID | 1234567890 |
| GOOGLE_ADS_LOGIN_CUSTOMER_ID | MCCアカウントID（任意） | 1234567890 |

### 6.3 Claude API

| 変数名 | 説明 | 例 |
|--------|------|-----|
| ANTHROPIC_API_KEY | Anthropic APIキー | sk-ant-xxxxx |

### 6.4 Chatwork API

| 変数名 | 説明 | 例 |
|--------|------|-----|
| CHATWORK_API_TOKEN | Chatwork APIトークン | xxxxx |
| CHATWORK_ROOM_ID | 通知先ルームID | 123456789 |
| CHATWORK_ASSIGNEE_ID | タスク担当者ID | 123456 |
| CHATWORK_MENTION_ID | メンション対象ID | 123456 |

### 6.5 アプリケーション設定

| 変数名 | 説明 | デフォルト |
|--------|------|----------|
| FRONTEND_URL | フロントエンドURL（CORS用） | http://localhost:3000 |
| DASHBOARD_URL | ダッシュボードURL（Chatwork通知用） | http://localhost:3000 |
| MAX_CHANGES_PER_APPROVAL | 1回の承認での最大変更件数 | 10 |
| MAX_BUDGET_CHANGE_PCT | 予算変更上限（%） | 20.0 |
| ROLLBACK_WINDOW_HOURS | ロールバック可能時間 | 24 |

### 6.6 フロントエンド

| 変数名 | 説明 | 例 |
|--------|------|-----|
| NEXT_PUBLIC_API_URL | バックエンドAPIのURL | http://localhost:8000 |

---

## 7. デプロイ情報

### 7.1 Render上のサービス構成

| サービス | タイプ | プラン | 説明 |
|---------|--------|--------|------|
| googleads-backend | Web Service | Free | FastAPI バックエンド |
| googleads-frontend | Static Site | Free | Next.js フロントエンド |
| googleads-db | PostgreSQL | Free | データベース |

### 7.2 URL

| 環境 | サービス | URL |
|------|---------|-----|
| 本番 | バックエンド（Render） | https://googleads-backend-7v2o.onrender.com |
| 本番 | バックエンド（カスタムドメイン） | https://sbpads-api.dfe.jp |
| 本番 | フロントエンド | https://googleads-frontend-xxxx.onrender.com |

### 7.3 GCPデプロイ構成（代替）

| サービス | 構成 | 説明 |
|---------|------|------|
| Cloud Run | Backend | FastAPIアプリ（512Mi, 1vCPU） |
| Cloud Run | Frontend | Next.jsアプリ（256Mi, 1vCPU） |
| Cloud SQL | PostgreSQL 16 | データベース（Private IP） |
| Cloud Scheduler | Cron | 週次分析トリガー（月曜7:00 JST） |
| Secret Manager | - | 認証情報管理 |
| VPC Connector | - | Cloud Run → Cloud SQL接続 |

### 7.4 スケジューラ設定

- **APScheduler（アプリ内蔵）**: `CronTrigger(day_of_week='mon', hour=7, minute=0, timezone='Asia/Tokyo')`
- **Cloud Scheduler**: `0 7 * * 1`（毎週月曜7:00 JST）

---

## 更新履歴

| 日付 | バージョン | 内容 |
|------|-----------|------|
| 2026-02-19 | 1.1.0 | キャンペーンフィルタリング、提案クリーンアップ機能追加 |
| 2026-02-19 | 1.0.0 | 初版作成 |
