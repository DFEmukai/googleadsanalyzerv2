# GCPデプロイ手順書

Google Ads AI Agent を GCP にデプロイするための手順です。

## アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐
│  Cloud Run      │     │  Cloud Run      │
│  (Frontend)     │────▶│  (Backend)      │
│  Next.js        │     │  FastAPI        │
│  Port 3000      │     │  Port 8000      │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
              │ Cloud SQL  │ │Claude │ │ Google    │
              │ PostgreSQL │ │  API  │ │ Ads API   │
              └───────────┘ └───────┘ └───────────┘
                    ▲
                    │
              ┌─────┴─────┐
              │  Cloud     │ 毎週月曜 7:00 JST
              │  Scheduler │──▶ POST /api/v1/analysis/run
              └───────────┘
```

## 前提条件

- GCP プロジェクトが作成済み
- `gcloud` CLI がインストール・認証済み
- 以下の API が有効化済み:
  - Cloud Run API
  - Cloud Build API
  - Cloud SQL Admin API
  - Secret Manager API
  - Serverless VPC Access API
  - Cloud Scheduler API

```bash
# API有効化
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  vpcaccess.googleapis.com \
  cloudscheduler.googleapis.com
```

## Step 1: Cloud SQL セットアップ

### 1.1 インスタンス作成

```bash
# プロジェクトID設定
export PROJECT_ID=$(gcloud config get-value project)
export REGION=asia-northeast1

# Cloud SQL インスタンス作成（PostgreSQL 16）
gcloud sql instances create googleads-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=${REGION} \
  --storage-type=SSD \
  --storage-size=10GB \
  --network=default \
  --no-assign-ip
```

### 1.2 データベースとユーザー作成

```bash
# データベース作成
gcloud sql databases create googleads_analyzer \
  --instance=googleads-db

# ユーザー作成（パスワードは安全な値に変更してください）
gcloud sql users create appuser \
  --instance=googleads-db \
  --password=YOUR_SECURE_PASSWORD
```

### 1.3 プライベートIPの確認

```bash
gcloud sql instances describe googleads-db \
  --format="value(ipAddresses[0].ipAddress)"
```

## Step 2: VPC Connector 作成

Cloud Run から Cloud SQL（プライベートIP）に接続するために必要です。

```bash
gcloud compute networks vpc-access connectors create googleads-connector \
  --region=${REGION} \
  --range=10.8.0.0/28
```

## Step 3: Secret Manager に環境変数を登録

機密情報は Secret Manager で管理します。

```bash
# DATABASE_URL
echo -n "postgresql+asyncpg://appuser:YOUR_SECURE_PASSWORD@CLOUD_SQL_PRIVATE_IP:5432/googleads_analyzer" | \
  gcloud secrets create DATABASE_URL --data-file=-

# Google Ads API
echo -n "YOUR_DEVELOPER_TOKEN" | gcloud secrets create GOOGLE_ADS_DEVELOPER_TOKEN --data-file=-
echo -n "YOUR_CLIENT_ID" | gcloud secrets create GOOGLE_ADS_CLIENT_ID --data-file=-
echo -n "YOUR_CLIENT_SECRET" | gcloud secrets create GOOGLE_ADS_CLIENT_SECRET --data-file=-
echo -n "YOUR_REFRESH_TOKEN" | gcloud secrets create GOOGLE_ADS_REFRESH_TOKEN --data-file=-
echo -n "YOUR_CUSTOMER_ID" | gcloud secrets create GOOGLE_ADS_CUSTOMER_ID --data-file=-
echo -n "YOUR_LOGIN_CUSTOMER_ID" | gcloud secrets create GOOGLE_ADS_LOGIN_CUSTOMER_ID --data-file=-

# Claude API
echo -n "YOUR_ANTHROPIC_API_KEY" | gcloud secrets create ANTHROPIC_API_KEY --data-file=-

# Chatwork API（オプション）
echo -n "YOUR_CHATWORK_API_TOKEN" | gcloud secrets create CHATWORK_API_TOKEN --data-file=-
echo -n "YOUR_CHATWORK_ROOM_ID" | gcloud secrets create CHATWORK_ROOM_ID --data-file=-
echo -n "YOUR_CHATWORK_ASSIGNEE_ID" | gcloud secrets create CHATWORK_ASSIGNEE_ID --data-file=-
echo -n "YOUR_CHATWORK_MENTION_ID" | gcloud secrets create CHATWORK_MENTION_ID --data-file=-
```

### Cloud Build サービスアカウントに権限付与

```bash
# Cloud Run デプロイ権限
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Secret Manager アクセス権限（Cloud Run サービスアカウント）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 4: 初回デプロイ

### 4.1 バックエンドを先にデプロイ

```bash
# バックエンドのイメージをビルド＆プッシュ
gcloud builds submit ./backend \
  --tag gcr.io/$PROJECT_ID/googleads-backend

# バックエンドをCloud Runにデプロイ
gcloud run deploy googleads-backend \
  --image gcr.io/$PROJECT_ID/googleads-backend \
  --region ${REGION} \
  --platform managed \
  --port 8000 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --timeout 300 \
  --vpc-connector googleads-connector \
  --set-secrets "\
DATABASE_URL=DATABASE_URL:latest,\
GOOGLE_ADS_DEVELOPER_TOKEN=GOOGLE_ADS_DEVELOPER_TOKEN:latest,\
GOOGLE_ADS_CLIENT_ID=GOOGLE_ADS_CLIENT_ID:latest,\
GOOGLE_ADS_CLIENT_SECRET=GOOGLE_ADS_CLIENT_SECRET:latest,\
GOOGLE_ADS_REFRESH_TOKEN=GOOGLE_ADS_REFRESH_TOKEN:latest,\
GOOGLE_ADS_CUSTOMER_ID=GOOGLE_ADS_CUSTOMER_ID:latest,\
GOOGLE_ADS_LOGIN_CUSTOMER_ID=GOOGLE_ADS_LOGIN_CUSTOMER_ID:latest,\
ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,\
CHATWORK_API_TOKEN=CHATWORK_API_TOKEN:latest,\
CHATWORK_ROOM_ID=CHATWORK_ROOM_ID:latest,\
CHATWORK_ASSIGNEE_ID=CHATWORK_ASSIGNEE_ID:latest,\
CHATWORK_MENTION_ID=CHATWORK_MENTION_ID:latest" \
  --set-env-vars "\
FRONTEND_URL=https://googleads-frontend-XXXXX-an.a.run.app,\
DASHBOARD_URL=https://googleads-frontend-XXXXX-an.a.run.app,\
MAX_CHANGES_PER_APPROVAL=10,\
MAX_BUDGET_CHANGE_PCT=20.0,\
ROLLBACK_WINDOW_HOURS=24" \
  --allow-unauthenticated
```

### 4.2 バックエンドURLを取得

```bash
export BACKEND_URL=$(gcloud run services describe googleads-backend \
  --region ${REGION} \
  --format="value(status.url)")
echo "Backend URL: ${BACKEND_URL}"
```

### 4.3 フロントエンドをデプロイ

```bash
# フロントエンドのイメージをビルド（バックエンドURLを注入）
gcloud builds submit ./frontend \
  --tag gcr.io/$PROJECT_ID/googleads-frontend \
  --substitutions="_NEXT_PUBLIC_API_URL=${BACKEND_URL}"

# ※ 上記ではbuild-argが使えないため、Dockerfileのbuild-arg経由で注入
# 以下のコマンドでローカルビルド＆プッシュも可能：
docker build -t gcr.io/$PROJECT_ID/googleads-frontend \
  --build-arg NEXT_PUBLIC_API_URL=${BACKEND_URL} \
  ./frontend
docker push gcr.io/$PROJECT_ID/googleads-frontend

# フロントエンドをCloud Runにデプロイ
gcloud run deploy googleads-frontend \
  --image gcr.io/$PROJECT_ID/googleads-frontend \
  --region ${REGION} \
  --platform managed \
  --port 3000 \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --allow-unauthenticated
```

### 4.4 バックエンドのFRONTEND_URLを更新

```bash
export FRONTEND_URL=$(gcloud run services describe googleads-frontend \
  --region ${REGION} \
  --format="value(status.url)")

gcloud run services update googleads-backend \
  --region ${REGION} \
  --update-env-vars "\
FRONTEND_URL=${FRONTEND_URL},\
DASHBOARD_URL=${FRONTEND_URL}"
```

## Step 5: Cloud Scheduler 設定

毎週月曜日 7:00 JST に週次分析を実行するジョブを作成します。

```bash
# サービスアカウント作成（Cloud Scheduler用）
gcloud iam service-accounts create scheduler-sa \
  --display-name="Cloud Scheduler Service Account"

# Cloud Run 呼び出し権限を付与
gcloud run services add-iam-policy-binding googleads-backend \
  --region=${REGION} \
  --member="serviceAccount:scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Cloud Scheduler ジョブ作成
gcloud scheduler jobs create http weekly-analysis \
  --location=${REGION} \
  --schedule="0 7 * * 1" \
  --time-zone="Asia/Tokyo" \
  --uri="${BACKEND_URL}/api/v1/analysis/run" \
  --http-method=POST \
  --oidc-service-account-email="scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --oidc-token-audience="${BACKEND_URL}" \
  --attempt-deadline=600s
```

## Step 6: CI/CDパイプライン（Cloud Build）

以降のデプロイは `cloudbuild.yaml` を使用できます。

```bash
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions="\
_REGION=${REGION},\
_BACKEND_URL=${BACKEND_URL},\
_VPC_CONNECTOR=googleads-connector"
```

> **注意**: Cloud Build経由のデプロイでは Secret Manager の設定は初回デプロイ時のものが保持されます。
> シークレットの変更は `gcloud run services update` で行ってください。

## 環境変数一覧

| 変数名 | 説明 | 管理方法 |
|---|---|---|
| `DATABASE_URL` | PostgreSQL接続URL | Secret Manager |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads開発者トークン | Secret Manager |
| `GOOGLE_ADS_CLIENT_ID` | OAuth クライアントID | Secret Manager |
| `GOOGLE_ADS_CLIENT_SECRET` | OAuth クライアントシークレット | Secret Manager |
| `GOOGLE_ADS_REFRESH_TOKEN` | OAuthリフレッシュトークン | Secret Manager |
| `GOOGLE_ADS_CUSTOMER_ID` | Google Ads顧客ID | Secret Manager |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | MCC ログインID | Secret Manager |
| `ANTHROPIC_API_KEY` | Claude API キー | Secret Manager |
| `CHATWORK_API_TOKEN` | Chatwork APIトークン | Secret Manager |
| `CHATWORK_ROOM_ID` | Chatwork通知ルームID | Secret Manager |
| `CHATWORK_ASSIGNEE_ID` | Chatworkタスク担当者ID | Secret Manager |
| `CHATWORK_MENTION_ID` | Chatworkメンション先ID | Secret Manager |
| `FRONTEND_URL` | フロントエンドURL（CORS用） | 環境変数 |
| `DASHBOARD_URL` | ダッシュボードURL（Chatwork用） | 環境変数 |
| `MAX_CHANGES_PER_APPROVAL` | 1回の承認で最大変更数 | 環境変数 |
| `MAX_BUDGET_CHANGE_PCT` | 予算変更の最大%  | 環境変数 |
| `ROLLBACK_WINDOW_HOURS` | ロールバック可能時間 | 環境変数 |
| `NEXT_PUBLIC_API_URL` | バックエンドURL（フロントエンド用） | ビルド時ARG |

## トラブルシューティング

### ログの確認

```bash
# バックエンドログ
gcloud run services logs read googleads-backend --region=${REGION} --limit=50

# フロントエンドログ
gcloud run services logs read googleads-frontend --region=${REGION} --limit=50
```

### ヘルスチェック

```bash
curl ${BACKEND_URL}/api/v1/health
```

### マイグレーションエラー

Cloud SQL への接続に失敗する場合:
1. VPC Connector が正しく設定されているか確認
2. Cloud SQL のプライベートIPが DATABASE_URL に正しく設定されているか確認
3. Cloud SQL のユーザー/パスワードが正しいか確認

### Cloud Scheduler が動作しない場合

```bash
# ジョブのステータス確認
gcloud scheduler jobs describe weekly-analysis --location=${REGION}

# 手動実行テスト
gcloud scheduler jobs run weekly-analysis --location=${REGION}
```
