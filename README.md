# agent-omoikane
AIエージェント技術を用いて、戦略立案、データ分析、課題解決など、様々なコンサルティング業務を自動化するシステムです。思兼神をモチーフに、高度な知性と判断力を実現します。

## ディレクトリ構造

```
agent-omoikane/
├── src/
│   ├── agents/
│   │   ├── manager/         # エージェントマネージャー
│   │   ├── strategist/      # 戦略立案エージェント
│   │   ├── analyst/         # データ分析エージェント
│   │   └── solver/          # 課題解決エージェント
│   ├── consulting/
│   │   ├── strategy/        # 戦略コンサルティング
│   │   ├── analysis/        # データ分析コンサルティング
│   │   └── problem_solving/ # 課題解決コンサルティング
│   ├── knowledge_graph/
│   │   ├── data/            # 知識グラフデータ
│   │   └── build.py         # 知識グラフ構築スクリプト
│   ├── llm/
│   │   ├── prompts/         # プロンプト管理
│   │   └── models/          # 大規模言語モデル管理
│   ├── modules/
│   ├── interface/           # ユーザーインターフェース
│   ├── utils/
│   └── main.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── knowledge/
├── models/
│   ├── trained/
│   └── checkpoints/
├── tests/                   # テストコード
├── docs/
├── requirements.txt
└── README.md
```
