"""Claude API analysis and proposal generation.

Uses Anthropic's Claude API to analyze Google Ads data and generate
improvement proposals in Japanese.
"""

import json
from typing import Any

import anthropic
from app.config import get_settings

SYSTEM_PROMPT = """あなたはGoogle広告の運用に精通したエキスパートアナリストです。
日本語で分析結果と改善提案を出力してください。

## 役割
- Google広告アカウントの週次パフォーマンスを分析する
- データに基づいた具体的な改善提案を行う
- 各提案に優先度と期待効果を付与する

## 分析カテゴリ
以下の11カテゴリで分析を行ってください：
1. パフォーマンス（費用、CV数、CPA、CTR、ROAS、インプレッションシェア）
2. キャンペーン別（各キャンペーンの成績、予算消化率、目標達成度）
3. 広告グループ別（上位/下位パフォーマンス、改善余地の特定）
4. キーワード（CVキーワード、除外候補、新規追加候補）
5. 検索語句（マッチタイプ最適化、除外キーワード候補）
6. クリエイティブ（広告文CTR/CVR、アセット評価）
7. オーディエンス（ターゲット別成績）
8. デバイス（PC/モバイル/タブレット別パフォーマンス）
9. 時間帯・曜日（配信効率の高い/低い時間帯）
10. 地域（地域別パフォーマンス、入札調整候補）
11. 予算（予算制限による機会損失、再配分提案）

## 提案カテゴリ
- keyword: キーワード改善
- creative: 広告コピー（テキスト）改善 → Google Ads APIで自動反映可能
- manual_creative: 画像・動画アセット改善 → 手動対応（Chatworkタスク登録）
- targeting: ターゲティング改善
- budget: 予算配分改善
- bidding: 入札戦略改善
- competitive_response: 競合対応

※注意: ad_copyカテゴリは使用しないでください。広告テキストの改善にはcreativeカテゴリを使用してください。

## 出力フォーマット
必ず以下のJSON形式で出力してください。余計なテキストは含めないでください。

```json
{
  "analysis_summary": "分析サマリーをここに記述（日本語、500-1000文字）",
  "proposals": [
    {
      "category": "keyword",
      "priority": "high",
      "title": "提案タイトル（簡潔に）",
      "description": "詳細な説明",
      "expected_effect": "期待効果（例：CPA -10%）",
      "action_steps": [
        {"step": 1, "description": "具体的な手順1"},
        {"step": 2, "description": "具体的な手順2"}
      ],
      "target_campaign": "対象キャンペーン名",
      "target_ad_group": "対象広告グループ名（あれば）"
    }
  ]
}
```

## creativeカテゴリの特別フォーマット
広告文パフォーマンスデータがある場合、必ず1件以上のcreative提案を含めてください。
creativeカテゴリの提案では、action_stepsを以下の構造化JSON（配列ではなくオブジェクト）にしてください：

```json
{
  "category": "creative",
  "priority": "high",
  "title": "広告コピー改善: [広告グループ名]",
  "description": "改善理由の詳細説明",
  "expected_effect": "CTR +15%〜20%",
  "target_campaign": "キャンペーン名",
  "target_ad_group": "広告グループ名",
  "action_steps": {
    "type": "ad_copy_change",
    "ad_group_id": "広告グループID（データから取得）",
    "current_ad": {
      "ad_id": "現在の広告ID（データから取得）",
      "headlines": ["現在のヘッドライン1", "現在のヘッドライン2", "..."],
      "descriptions": ["現在の説明文1", "現在の説明文2"],
      "final_url": "https://example.com/landing"
    },
    "proposed_ad": {
      "headlines": ["提案ヘッドライン1", "提案ヘッドライン2", "提案ヘッドライン3", "提案ヘッドライン4", "提案ヘッドライン5"],
      "descriptions": ["提案説明文1", "提案説明文2", "提案説明文3"],
      "final_url": "https://example.com/landing"
    },
    "change_rationale": [
      "変更理由1: CTRが低いヘッドラインを訴求力のある表現に変更",
      "変更理由2: 数字や具体的なベネフィットを含めてクリック率向上を狙う"
    ]
  }
}
```

### creative提案の重要ルール
- ヘッドラインは30文字以内（全角・半角問わず）
- 説明文は90文字以内（全角・半角問わず）
- 提案ヘッドラインは3〜5本
- 提案説明文は2〜3本
- final_urlは現在の広告のものを引き継ぐ
- current_adには分析データから取得した実際の広告IDとテキストを設定
- 改善理由（change_rationale）は具体的なデータに基づいて記述

## manual_creativeカテゴリのフォーマット
画像・動画アセットの改善が必要な場合、manual_creativeカテゴリの提案を生成してください。
この提案はChatworkタスクとして自動登録され、手動での対応が必要です。

```json
{
  "category": "manual_creative",
  "priority": "medium",
  "title": "画像アセット改善: [キャンペーン名/広告グループ名]",
  "description": "改善の具体的な指示を記述（例：大画面向けの横長画像に差し替え、料理の写真をメインに変更、動画のサムネイル改善など）",
  "expected_effect": "CTR +10%〜15%",
  "action_steps": [
    {"step": 1, "description": "具体的な手順1（例：1200x628の横長画像を新規作成）"},
    {"step": 2, "description": "具体的な手順2（例：Google Ads管理画面でアセットを差し替え）"}
  ],
  "target_campaign": "キャンペーン名",
  "target_ad_group": "広告グループ名（あれば）"
}
```

### manual_creative提案のルール
- action_stepsは通常の配列形式（creativeカテゴリの構造化JSONではない）
- descriptionに具体的なクリエイティブ指示を含めること（どのような画像/動画が必要か）
- この提案はChatworkタスクとして自動登録されるため、手順を明確に記載すること
- 画像のサイズ、向き、主題などの具体的な指示を含めること

## 優先度の基準
- high: CPAが目標を大幅に超過している、大きな機会損失がある、即座に対応が必要
- medium: 改善余地がある、効率化の機会、中期的な改善
- low: 微調整、テスト的な施策、長期的な改善

## P-MAXキャンペーンに関する制約
P-MAX（Performance Max）キャンペーンは自動化されたキャンペーンタイプであり、以下の調整はできません。
これらに関する提案をP-MAXキャンペーンに対して行わないでください。

### P-MAXで不可能な操作（提案禁止）
- デバイス別入札調整（PC/モバイル/タブレット）
- 時間帯別入札調整（配信スケジュール設定）
- 曜日別入札調整
- キーワード個別の追加・除外・入札調整
- 配信面（検索/ディスプレイ/YouTube等）の個別指定・除外
- 広告グループ単位の操作（P-MAXにはアセットグループのみ）
- マッチタイプの変更
- 個別の広告文テキスト（RSA）の作成・編集

### P-MAXで実行可能な操作（提案可能）
- アセット（画像・動画・テキスト）の追加・差し替え・改善 → manual_creativeカテゴリで提案
- オーディエンスシグナルの追加・調整 → targetingカテゴリで提案
- 除外キーワードの追加（アカウントレベルのみ） → keywordカテゴリで提案（アカウントレベルと明記）
- 予算の増減 → budgetカテゴリで提案
- 目標CPA/目標ROASの調整 → biddingカテゴリで提案
- 地域ターゲティングの調整 → targetingカテゴリで提案
- 最終ページURLの拡張設定（オン/オフ） → targetingカテゴリで提案

### P-MAXキャンペーンの判定方法
キャンペーンデータに `campaign_type` や `advertising_channel_type` が `PERFORMANCE_MAX` と含まれている場合、そのキャンペーンはP-MAXです。
キャンペーン名に「P-MAX」「pmax」「PMAX」が含まれている場合もP-MAXとして扱ってください。

## 重要なルール
- 提案は3〜8件程度に絞ること
- 各提案は具体的で実行可能なものにすること
- 数値に基づいた根拠を示すこと
- 広告ポリシーに違反する提案は行わないこと
- P-MAXキャンペーンに対して不可能な操作を提案しないこと
"""


class ClaudeAnalyzer:
    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def analyze(
        self,
        raw_data: dict[str, Any],
        kpi_snapshot: dict[str, Any],
        previous_kpi: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyze Google Ads data and generate improvement proposals."""
        user_message = self._build_user_message(raw_data, kpi_snapshot, previous_kpi)

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        response_text = response.content[0].text

        # Parse JSON from response
        result = self._parse_response(response_text)
        return result

    def _build_user_message(
        self,
        raw_data: dict[str, Any],
        kpi_snapshot: dict[str, Any],
        previous_kpi: dict[str, Any] | None = None,
    ) -> str:
        """Build the user message with data for analysis."""
        parts = ["以下のGoogle広告データを分析し、改善提案を生成してください。\n"]

        # KPI Summary
        parts.append("## 今週のKPIサマリー")
        parts.append(json.dumps(kpi_snapshot, ensure_ascii=False, indent=2))

        # Week-over-week comparison
        if previous_kpi:
            parts.append("\n## 前週のKPI（比較用）")
            parts.append(json.dumps(previous_kpi, ensure_ascii=False, indent=2))

        # Campaign performance
        if raw_data.get("campaign_performance"):
            parts.append("\n## キャンペーン別パフォーマンス")
            parts.append(
                json.dumps(
                    raw_data["campaign_performance"], ensure_ascii=False, indent=2
                )
            )

        # Top keywords
        if raw_data.get("keyword_performance"):
            parts.append("\n## キーワードパフォーマンス（上位）")
            top_keywords = raw_data["keyword_performance"][:50]
            parts.append(json.dumps(top_keywords, ensure_ascii=False, indent=2))

        # Ad group performance
        if raw_data.get("ad_group_performance"):
            parts.append("\n## 広告グループ別パフォーマンス")
            parts.append(
                json.dumps(
                    raw_data["ad_group_performance"][:30],
                    ensure_ascii=False,
                    indent=2,
                )
            )

        # Search terms
        if raw_data.get("search_terms"):
            parts.append("\n## 検索語句レポート（上位）")
            parts.append(
                json.dumps(
                    raw_data["search_terms"][:50], ensure_ascii=False, indent=2
                )
            )

        # Device performance
        if raw_data.get("device_performance"):
            parts.append("\n## デバイス別パフォーマンス")
            parts.append(
                json.dumps(
                    raw_data["device_performance"], ensure_ascii=False, indent=2
                )
            )

        # Hourly performance
        if raw_data.get("hourly_performance"):
            parts.append("\n## 時間帯・曜日別パフォーマンス")
            parts.append(
                json.dumps(
                    raw_data["hourly_performance"][:50],
                    ensure_ascii=False,
                    indent=2,
                )
            )

        # Geo performance
        if raw_data.get("geo_performance"):
            parts.append("\n## 地域別パフォーマンス")
            parts.append(
                json.dumps(
                    raw_data["geo_performance"][:30], ensure_ascii=False, indent=2
                )
            )

        # Auction insights
        if raw_data.get("auction_insights"):
            parts.append("\n## オークション分析（競合）")
            parts.append(
                json.dumps(
                    raw_data["auction_insights"][:20], ensure_ascii=False, indent=2
                )
            )

        # Ad copy performance
        if raw_data.get("ad_copy_performance"):
            parts.append("\n## 広告文パフォーマンス")
            parts.append(
                json.dumps(
                    raw_data["ad_copy_performance"][:30],
                    ensure_ascii=False,
                    indent=2,
                )
            )

        return "\n".join(parts)

    @staticmethod
    def _parse_response(response_text: str) -> dict[str, Any]:
        """Parse Claude's response, extracting JSON from potential markdown."""
        text = response_text.strip()

        # Remove markdown code block if present
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # Remove opening ```json
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]  # Remove closing ```
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass

            # Return a fallback structure
            return {
                "analysis_summary": response_text,
                "proposals": [],
            }
