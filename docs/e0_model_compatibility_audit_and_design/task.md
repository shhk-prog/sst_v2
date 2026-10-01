# Task: E0 モデル互換性監査および研究設計 (E0 Model Compatibility Audit & Research Design)

## 概要
コミット `f5fd784e25224e6f8aede6667430c99c6da7ddd8` によりコード監査ループが完了した。
次のフェーズとして、「E0の検査基準を単に緩める」のではなく、「どの不整合が致命的で、どれが正規化可能かを実証する監査」を実施し、研究設計としての4分類を明確化する。

## 不整合対象一覧
1. **Math (WizardLMTeam/WizardMath-7B-V1.0)**:
   - `max_position_embeddings`: 4096 vs 2048
   - `vocab_size`: 32000 vs 32001
2. **Code (vanillaOVO/WizardCoder-Python-7B-V1.0)**:
   - `max_position_embeddings`: 4096 vs 16384
   - `rope_theta`: 10000 vs 1000000
   - `vocab_size`: 32000 vs 32001
   - `bos_token_id`: 1 vs 2
3. **Safety (v3/models/temp_safety_full_seed42, safety_lora_seed42)**:
   - `vocab_size`: 32001
   - `max_position_embeddings`: 4096
   - `rope_theta`: 10000.0

## タスクリスト
- [x] Hugging Face キャッシュおよびローカルモデルの実態調査（Config, Tokenizer, 重みテンソル Shape）
- [x] 各差分の 4 分類（重み空間マージ不可能 / Config差だがテンソル対応 / トークナイザ正規化可能 / モデル入替必要）の数理的・実証的分析
- [x] ドキュメント（`task.md`, `implementation_plan.md`, `walkthrough.md`）の作成
- [x] 監査結果と次期研究方針のユーザーへの体系的提案
