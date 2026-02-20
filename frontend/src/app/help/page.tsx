"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

type SectionProps = {
  title: string;
  id: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
};

function Section({ title, id, children, defaultOpen = false }: SectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-border">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between py-4 text-left text-lg font-semibold hover:text-signal-blue"
        id={id}
      >
        {title}
        {isOpen ? (
          <ChevronDown className="h-5 w-5" />
        ) : (
          <ChevronRight className="h-5 w-5" />
        )}
      </button>
      {isOpen && <div className="pb-6 text-muted-foreground">{children}</div>}
    </div>
  );
}

function Table({
  headers,
  rows,
}: {
  headers: string[];
  rows: string[][];
}) {
  return (
    <div className="my-4 overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border bg-card">
            {headers.map((header, i) => (
              <th key={i} className="px-4 py-2 text-left font-semibold">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-border">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-2">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function HelpPage() {
  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-2 text-3xl font-bold">操作説明書</h1>
      <p className="mb-8 text-muted-foreground">
        Google Ads AI Agent - ユーザーガイド（バージョン 1.0）
      </p>

      {/* 目次 */}
      <div className="mb-8 rounded-lg bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold">目次</h2>
        <nav className="space-y-2">
          <a href="#section-1" className="block text-signal-blue hover:underline">
            1. はじめに
          </a>
          <a href="#section-2" className="block text-signal-blue hover:underline">
            2. ダッシュボードの見方
          </a>
          <a href="#section-3" className="block text-signal-blue hover:underline">
            3. キャンペーン一覧・詳細の使い方
          </a>
          <a href="#section-4" className="block text-signal-blue hover:underline">
            4. 改善提案の確認・壁打ち・承認方法
          </a>
          <a href="#section-5" className="block text-signal-blue hover:underline">
            5. 週次レポートの見方
          </a>
          <a href="#section-6" className="block text-signal-blue hover:underline">
            6. 分析実行ボタンの使い方
          </a>
          <a href="#section-7" className="block text-signal-blue hover:underline">
            7. 効果レポートの見方
          </a>
          <a href="#section-faq" className="block text-signal-blue hover:underline">
            よくある質問（FAQ）
          </a>
        </nav>
      </div>

      {/* セクション1: はじめに */}
      <Section title="1. はじめに" id="section-1" defaultOpen={true}>
        <div className="space-y-4">
          <h3 className="text-base font-semibold text-white">1.1 Google Ads AI Agentとは</h3>
          <p>
            Google Ads AI Agentは、Google広告アカウントの運用を支援するAIツールです。
            以下の機能を提供します：
          </p>
          <ul className="ml-6 list-disc space-y-1">
            <li><strong>自動分析</strong>: 週次でGoogle広告のパフォーマンスを分析</li>
            <li><strong>改善提案</strong>: AIが具体的な改善アクションを提案</li>
            <li><strong>承認ワークフロー</strong>: 提案を確認・承認・実行</li>
            <li><strong>効果測定</strong>: 施策実行後の効果を自動計測</li>
          </ul>
        </div>
      </Section>

      {/* セクション2: ダッシュボードの見方 */}
      <Section title="2. ダッシュボードの見方" id="section-2">
        <div className="space-y-6">
          <div>
            <h3 className="mb-2 text-base font-semibold text-white">2.1 ダッシュボード画面</h3>
            <p>
              サイドバーの「ダッシュボード」をクリックするか、トップページにアクセスすると
              ダッシュボードが表示されます。
            </p>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">2.2 KPIサマリーカード</h3>
            <p className="mb-2">
              画面上部に表示される6つのカードで、<strong>直近7日間</strong>の主要KPIを確認できます。
            </p>
            <Table
              headers={["KPI", "説明", "計算方法"]}
              rows={[
                ["費用", "広告費用の合計", "7日間の合計"],
                ["CV数", "コンバージョン数", "7日間の合計"],
                ["CPA", "獲得単価", "総費用 ÷ 総CV数"],
                ["CTR", "クリック率", "総クリック ÷ 総インプレッション × 100"],
                ["ROAS", "広告費用対効果", "総CV価値 ÷ 総費用"],
                ["インプレッション", "表示回数", "7日間の合計"],
              ]}
            />
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">2.3 シグナル（色）の意味</h3>
            <p className="mb-2">各KPIカードの色は、前週との比較に基づいて表示されます：</p>
            <Table
              headers={["色", "意味", "説明"]}
              rows={[
                ["🟢 緑", "良好", "前週より改善"],
                ["🟡 黄", "注意", "前週と同程度"],
                ["🔴 赤", "要対応", "前週より悪化"],
                ["🔵 青", "情報", "中立的な指標（費用、インプレッションなど）"],
              ]}
            />
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">2.4 前週比較</h3>
            <p>各KPIカードには以下の情報が表示されます：</p>
            <ul className="ml-6 list-disc space-y-1">
              <li><strong>現在値</strong>: 直近7日間の値</li>
              <li><strong>前週値</strong>: 8日前〜14日前の値</li>
              <li><strong>変化率</strong>: （現在値 - 前週値）÷ 前週値 × 100%</li>
              <li><strong>矢印</strong>: ↑（増加）または ↓（減少）</li>
            </ul>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">2.5 トレンドグラフ</h3>
            <p className="mb-2">画面下部には、<strong>直近7日間の日別推移</strong>がグラフで表示されます：</p>
            <ul className="ml-6 list-disc space-y-1">
              <li><strong>X軸</strong>: 日付（例: 02-13, 02-14, 02-15...）</li>
              <li><strong>Y軸</strong>: 各KPIの値</li>
              <li><strong>グラフ種類</strong>: CPA推移、CV数推移、費用推移、ROAS推移</li>
            </ul>
          </div>
        </div>
      </Section>

      {/* セクション3: キャンペーン一覧・詳細 */}
      <Section title="3. キャンペーン一覧・詳細の使い方" id="section-3">
        <div className="space-y-6">
          <div>
            <h3 className="mb-2 text-base font-semibold text-white">3.1 キャンペーン一覧画面</h3>
            <p className="mb-2">
              サイドバーの「キャンペーン」をクリックすると、キャンペーン一覧が表示されます。
            </p>
            <Table
              headers={["項目", "説明"]}
              rows={[
                ["ステータス", "🟢 有効 / 🟡 停止中 / ⚫ 終了"],
                ["キャンペーン名", "Google広告のキャンペーン名"],
                ["タイプ", "search / display / pmax / video"],
                ["費用", "期間内の広告費用"],
                ["CV", "コンバージョン数"],
                ["CPA", "獲得単価"],
                ["CTR", "クリック率"],
                ["ROAS", "広告費用対効果"],
              ]}
            />
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">ソート機能</h3>
            <p>テーブルのヘッダーをクリックすると、その項目でソートできます。</p>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">3.2 キャンペーン詳細画面</h3>
            <p>一覧でキャンペーン行をクリックすると、詳細ダッシュボードが表示されます。</p>
            <ul className="ml-6 mt-2 list-disc space-y-1">
              <li><strong>KPIカード</strong>: そのキャンペーンの直近7日間のKPI</li>
              <li><strong>日別トレンドグラフ</strong>: 期間内の日別パフォーマンス推移</li>
              <li><strong>期間選択</strong>: 7日間 / 14日間 / 30日間</li>
              <li><strong>関連提案</strong>: このキャンペーンに対する改善提案</li>
            </ul>
          </div>
        </div>
      </Section>

      {/* セクション4: 改善提案 */}
      <Section title="4. 改善提案の確認・壁打ち・承認方法" id="section-4">
        <div className="space-y-6">
          <div>
            <h3 className="mb-2 text-base font-semibold text-white">4.1 改善提案一覧画面</h3>
            <p className="mb-2">
              サイドバーの「改善提案」をクリックすると、改善提案一覧が表示されます。
            </p>
            <Table
              headers={["フィルター", "選択肢"]}
              rows={[
                ["ステータス", "すべて / 承認待ち / 承認済み / 実行済み / 却下 / スキップ"],
                ["カテゴリ", "すべて / キーワード / クリエイティブ / 手動クリエイティブ / ターゲティング / 予算 / 入札 / 競合対応"],
                ["優先度", "すべて / 高 / 中 / 低"],
              ]}
            />
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">4.2 提案カードの見方</h3>
            <ul className="ml-6 list-disc space-y-1">
              <li><strong>優先度バッジ</strong>: 🔴高 / 🟡中 / 🟢低</li>
              <li><strong>カテゴリバッジ</strong>: keyword / creative / budget など</li>
              <li><strong>タイトル</strong>: 提案の概要</li>
              <li><strong>対象</strong>: キャンペーン名・広告グループ名</li>
              <li><strong>期待効果</strong>: 実行した場合の予測効果</li>
            </ul>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">4.3 壁打ちチャット機能</h3>
            <p className="mb-2">提案について疑問がある場合、AIと対話して検討できます。</p>
            <ol className="ml-6 list-decimal space-y-1">
              <li>提案カードを展開</li>
              <li>「Claudeと壁打ち」ボタンをクリック</li>
              <li>チャットウィンドウが表示される</li>
              <li>質問やコメントを入力して送信</li>
            </ol>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">4.4 提案の承認方法</h3>
            <Table
              headers={["ボタン", "動作"]}
              rows={[
                ["承認して実行", "提案を承認し、即座にGoogle Adsに反映"],
                ["承認のみ", "提案を承認（後で手動実行）"],
                ["却下", "提案を却下（理由入力可）"],
                ["スキップ", "一時的に保留（後で再検討）"],
              ]}
            />
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">4.5 ロールバック</h3>
            <p>
              実行後<strong>24時間以内</strong>であれば、変更を元に戻せます。
              ステータスフィルターで「実行済み」を選択し、「ロールバック」ボタンをクリックしてください。
            </p>
          </div>
        </div>
      </Section>

      {/* セクション5: 週次レポート */}
      <Section title="5. 週次レポートの見方" id="section-5">
        <div className="space-y-6">
          <div>
            <h3 className="mb-2 text-base font-semibold text-white">5.1 レポート一覧画面</h3>
            <p className="mb-2">
              サイドバーの「週次レポート」をクリックすると、週次レポート一覧が表示されます。
            </p>
            <Table
              headers={["項目", "説明"]}
              rows={[
                ["期間", "レポート対象週（例: 2024/02/12 - 2024/02/18）"],
                ["作成日", "レポートが生成された日時"],
                ["提案数", "このレポートに含まれる改善提案の数"],
                ["費用", "週間の総費用"],
                ["CV数", "週間のコンバージョン数"],
                ["CPA", "週間のCPA"],
              ]}
            />
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">5.2 レポート詳細画面</h3>
            <p>レポート行をクリックすると、詳細が表示されます：</p>
            <ul className="ml-6 mt-2 list-disc space-y-1">
              <li><strong>分析サマリー</strong>: AIによる週次パフォーマンスの分析結果</li>
              <li><strong>KPIスナップショット</strong>: 週間の主要KPI</li>
              <li><strong>改善提案一覧</strong>: このレポートから生成された改善提案</li>
            </ul>
          </div>
        </div>
      </Section>

      {/* セクション6: 分析実行ボタン */}
      <Section title="6. 分析実行ボタンの使い方" id="section-6">
        <div className="space-y-6">
          <div>
            <h3 className="mb-2 text-base font-semibold text-white">6.1 手動分析の実行</h3>
            <p className="mb-2">
              通常、分析は毎週月曜7:00に自動実行されますが、任意のタイミングで手動実行することもできます。
            </p>
            <ol className="ml-6 list-decimal space-y-1">
              <li>ダッシュボードまたはレポート画面を開く</li>
              <li>「分析を実行」ボタンをクリック</li>
              <li>確認ダイアログが表示される</li>
              <li>「実行」ボタンをクリック</li>
              <li>分析が開始される（数分かかる場合があります）</li>
              <li>完了すると新しいレポートが作成される</li>
            </ol>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">6.2 分析の所要時間</h3>
            <p>分析には以下の処理が含まれるため、完了まで数分かかります：</p>
            <ol className="ml-6 mt-2 list-decimal space-y-1">
              <li>Google Ads APIからデータ取得</li>
              <li>Claude AIによる分析</li>
              <li>改善提案の生成</li>
              <li>データベースへの保存</li>
              <li>Chatwork通知（設定時）</li>
            </ol>
          </div>
        </div>
      </Section>

      {/* セクション7: 効果レポート */}
      <Section title="7. 効果レポートの見方" id="section-7">
        <div className="space-y-6">
          <div>
            <h3 className="mb-2 text-base font-semibold text-white">7.1 効果レポートとは</h3>
            <p>
              実行した改善提案の効果を測定するレポートです。
              実行前後のKPIを比較して、施策の効果を可視化します。
            </p>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">7.2 確認方法</h3>
            <ol className="ml-6 list-decimal space-y-1">
              <li>改善提案一覧で「実行済み」フィルターを選択</li>
              <li>効果を確認したい提案を展開</li>
              <li>「効果レポート」ボタンをクリック</li>
            </ol>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">7.3 比較期間</h3>
            <Table
              headers={["期間", "説明"]}
              rows={[
                ["Before（実行前）", "提案実行前の7日間"],
                ["After（実行後）", "提案実行後の7日間"],
              ]}
            />
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">7.4 変化率の見方</h3>
            <ul className="ml-6 list-disc space-y-1">
              <li><strong>プラス（＋）</strong>: 数値が増加</li>
              <li><strong>マイナス（－）</strong>: 数値が減少</li>
              <li><strong className="text-signal-green">緑色</strong>: 改善方向への変化（例: CPAが減少、ROASが増加）</li>
              <li><strong className="text-signal-red">赤色</strong>: 悪化方向への変化（例: CPAが増加、ROASが減少）</li>
            </ul>
          </div>
        </div>
      </Section>

      {/* FAQ */}
      <Section title="よくある質問（FAQ）" id="section-faq">
        <div className="space-y-6">
          <div>
            <h3 className="mb-2 text-base font-semibold text-white">
              Q1: データが更新されていないようです
            </h3>
            <p>
              A: Google Ads APIのデータは最大24時間の遅延があります。
              また、当日分のデータは不完全な場合があります。翌日に再度確認してください。
            </p>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">
              Q2: 提案を間違えて実行してしまいました
            </h3>
            <p>
              A: 実行から24時間以内であれば、「ロールバック」機能で元に戻せます。
              24時間を過ぎた場合は、Google広告管理画面から手動で修正してください。
            </p>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">
              Q3: 壁打ちチャットの履歴は保存されますか？
            </h3>
            <p>
              A: はい、提案ごとにチャット履歴が保存されます。
              次回アクセス時も過去の会話を確認できます。
            </p>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">
              Q4: 週次レポートが生成されていません
            </h3>
            <p>A: 以下を確認してください：</p>
            <ul className="ml-6 mt-2 list-disc space-y-1">
              <li>Google Ads APIの認証情報が正しく設定されているか</li>
              <li>Anthropic APIキーが有効か</li>
              <li>サーバーが正常に稼働しているか</li>
            </ul>
          </div>

          <div>
            <h3 className="mb-2 text-base font-semibold text-white">
              Q5: 手動クリエイティブ提案はどう対応すればよいですか？
            </h3>
            <p>
              A: 手動クリエイティブ提案は、画像や動画の作成が必要なため自動実行できません。
              Chatworkタスクとして登録されるので、担当者が手動で対応してください。
            </p>
          </div>
        </div>
      </Section>

      {/* フッター */}
      <div className="mt-8 rounded-lg bg-card p-6 text-center text-muted-foreground">
        <p>
          問題が発生した場合や、ご質問がある場合は、システム管理者にお問い合わせください。
        </p>
      </div>
    </div>
  );
}
