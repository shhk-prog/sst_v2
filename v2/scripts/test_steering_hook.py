import unittest
import os
import sys

# scripts フォルダをパスに追加
sys.path.append(os.path.dirname(__file__))
import steering_hook

class DummyArgs:
    """テスト用の引数オブジェクト"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class TestSteeringHook(unittest.TestCase):
    
    def setUp(self):
        # 各テストの開始時に監視状態をリセット
        steering_hook.disable_data_free_monitoring()

    def test_verify_base_model_approved(self):
        # 許可されたベースモデル名（正常系）
        try:
            steering_hook.verify_base_model("meta-llama/Meta-Llama-3.1-8B-Instruct")
            steering_hook.verify_base_model("mistralai/Mistral-7B-Instruct-v0.3")
            steering_hook.verify_base_model("Qwen/Qwen2.5-7B-Instruct")
            steering_hook.verify_base_model("meta-llama/Llama-2-7b-hf")
            steering_hook.verify_base_model("WizardLMTeam/WizardMath-7B-V1.0")
            steering_hook.verify_base_model("vanillaOVO/WizardCoder-Python-7B-V1.0")
            steering_hook.verify_base_model("medalpaca/medalpaca-7b")
        except ValueError as e:
            self.fail(f"許可されているモデル名でエラーが発生しました: {e}")

    def test_verify_base_model_disallowed(self):
        # 許可されていないベースモデル名（異常系）
        with self.assertRaises(ValueError) as context:
            steering_hook.verify_base_model("gpt-2")
        self.assertIn("仕様外のベースモデルが指定されています", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            steering_hook.verify_base_model("tiiuae/falcon-7b-instruct")
        self.assertIn("仕様外のベースモデルが指定されています", str(context.exception))

    def test_verify_experiment_config_valid(self):
        # 正常な設定の場合、例外が発生しないこと
        args = DummyArgs(
            base_model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            method="diagonal_sst",
            utility_dataset_path="data/utility_fpb.json",
            eval_dataset_path="data/mmlu_eval.json"
        )
        try:
            steering_hook.verify_experiment_config(args)
        except ValueError as e:
            self.fail(f"正常な実験構成でエラーが発生しました: {e}")

    def test_verify_experiment_config_invalid_model(self):
        # 許可されていないモデルの場合にエラー
        args = DummyArgs(
            base_model="dummy-gpt-model",
            method="diagonal_sst"
        )
        with self.assertRaises(ValueError) as context:
            steering_hook.verify_experiment_config(args)
        self.assertIn("仕様外のベースモデルが指定されています", str(context.exception))

    def test_verify_experiment_config_custom_baseline_disallowed(self):
        # 比較手法（ties）で mergekit 以外の実装（custom）が指定された場合にエラー
        args = DummyArgs(
            base_model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            method="ties",
            implementation="custom"  # カスタムコードは禁止
        )
        with self.assertRaises(ValueError) as context:
            steering_hook.verify_experiment_config(args)
        self.assertIn("公式 mergekit (implementation: 'mergekit' または 'official' を指定) を使用してください", str(context.exception))

    def test_verify_experiment_config_data_free_leakage(self):
        # Data-Free 設定なのに実データが引数に入っている場合にエラー
        args = DummyArgs(
            base_model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            method="data_free_sst",
            utility_dataset_path="data/utility_fpb.json" # カンニング
        )
        with self.assertRaises(ValueError) as context:
            steering_hook.verify_experiment_config(args)
        self.assertIn("データセットまたは統計キャッシュへの参照", str(context.exception))

    def test_verify_experiment_config_data_overlap(self):
        # FIM/学習データと評価データセットが重複（同一）の場合にエラー（データリーク防止）
        args = DummyArgs(
            base_model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            method="diagonal_sst",
            eval_dataset_path="data/eval_dataset.json",
            utility_dataset_path="data/eval_dataset.json" # 重複
        )
        with self.assertRaises(ValueError) as context:
            steering_hook.verify_experiment_config(args)
        self.assertIn("これらは完全に分離しなければなりません", str(context.exception))

    def test_data_free_leakage_monitoring_enabled(self):
        # 監視が有効な場合、data/ 配下の JSON ファイルを open すると ValueError が発生する
        steering_hook.enable_data_free_monitoring()
        
        test_file = "data_test_temp.json"
        filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data", test_file))
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with self.assertRaises(ValueError) as context:
            with open(filepath, "w") as f:
                f.write('{"test": 1}')
        self.assertIn("Data-Free マージ実行中に、実データセットファイル", str(context.exception))
        
        # 監視を解除してテスト後片付け
        steering_hook.disable_data_free_monitoring()
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == "__main__":
    unittest.main()
