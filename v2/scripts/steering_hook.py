import builtins
import os
import sys

# 状態管理
_data_free_mode_enabled = False
_original_open = builtins.open

def _hooked_open(file, mode='r', *args, **kwargs):
    """
    組み込みの open 関数をフックし、Data-Free 設定時に実データセットファイルが
    読み込まれないか動的に監視・検証します。
    """
    filepath = os.path.abspath(str(file))
    if _data_free_mode_enabled:
        # data フォルダ内の JSON データセットへのアクセスを検知
        basename = os.path.basename(filepath)
        if "data" in filepath and (basename.endswith(".json") or "fpb" in basename or "advbench" in basename or "repliqa" in basename):
            raise ValueError(
                f"[Steering Hook Rule Violation] Data-Free マージ実行中に、実データセットファイル "
                f"({basename}) を読み込むことは仕様で禁止されています（Data Leakage の防止）。"
            )
    return _original_open(file, mode, *args, **kwargs)

# open 関数のフックを有効化
builtins.open = _hooked_open


def enable_data_free_monitoring():
    """
    Data-Free マージの実行開始時に呼び出し、データ漏洩の動的監視を有効化します。
    """
    global _data_free_mode_enabled
    _data_free_mode_enabled = True
    print("[Steering Hook] Data-Free 監視モードが有効になりました。実データへのアクセスを禁止します。")


def disable_data_free_monitoring():
    """
    監視モードを解除します。
    """
    global _data_free_mode_enabled
    _data_free_mode_enabled = False


def verify_base_model(model_name_or_path):
    """
    ベースモデルの妥当性を検証します。
    仕様上、メインモデルの Meta-Llama-3.1-8B-Instruct、
    およびクロス検証用の Mistral-7B-Instruct, Qwen2.5-7B-Instruct のみ許可します。
    ※ Llama-2-7B の実験のため、Llama-2-7B および関連する派生特化モデル（WizardMath, WizardCoder, Medalpaca）も追加で許可します。
    """
    allowed_main_models = {
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "meta-llama/Llama-2-7b-hf",
        "meta-llama/Llama-2-7b",
    }
    allowed_keywords = [
        "llama-3.1-8b", "llama3.1", "mistral-7b", "qwen2.5-7b",
        "llama-2-7b", "llama2", "wizardmath", "wizardcoder", "medalpaca"
    ]
    
    name_lower = model_name_or_path.lower()
    
    # 許可されるベースモデルとキーワードのいずれかが含まれているか検証
    is_main = any(m in model_name_or_path for m in allowed_main_models)
    is_keyword_match = any(kw in name_lower for kw in allowed_keywords)
    
    if not (is_main or is_keyword_match):
        raise ValueError(
            f"[Steering Hook Rule Violation] 仕様外のベースモデルが指定されています: {model_name_or_path}\n"
            f"メイン実験には Meta-Llama-3.1-8B-Instruct、クロス検証には Mistral-7B-Instruct または Qwen2.5-7B-Instruct を使用してください。"
        )
    print(f"[Steering Hook] ベースモデルの検証をパスしました: {model_name_or_path}")


def verify_experiment_config(args):
    """
    実験時のコマンドライン引数（args）や設定の統合検証を行います。
    ルール違反が検出された場合は ValueError を送出して強制終了します。
    """
    # 1. ベースモデルの検証
    model_name = getattr(args, "model_name_or_path", getattr(args, "base_model", getattr(args, "base_model_id", None)))
    if model_name:
        verify_base_model(model_name)
    else:
        raise ValueError("[Steering Hook Rule Violation] ベースモデル名 (model_name_or_path / base_model) が指定されていません。")
        
    # 2. 比較手法における公式 mergekit 実装の強制
    method = getattr(args, "method", getattr(args, "merge_method", None))
    if method:
        method_lower = method.lower()
        if method_lower in ["ties", "dare", "task_arithmetic", "task-arithmetic"]:
            impl = getattr(args, "implementation", getattr(args, "impl", "custom"))
            if impl not in {"mergekit", "official"}:
                raise ValueError(
                    f"[Steering Hook Rule Violation] 比較手法 ({method}) の実行には、独自カスタム実装コードではなく、"
                    f"公式 mergekit (implementation: 'mergekit' または 'official' を指定) を使用してください。"
                )

    # 3. Data-Free 時のデータ・キャッシュ統計遮断
    if method == "data_free_sst":
        forbidden_keys = [
            "utility_dataset_path",
            "safety_dataset_path",
            "fim_path",
            "cached_gradient_path",
            "cached_fisher_path",
        ]
        for key in forbidden_keys:
            if getattr(args, key, None):
                raise ValueError(
                    f"[Steering Hook Rule Violation] Data-Free SST の実行において、"
                    f"データセットまたは統計キャッシュへの参照 ({key}) を指定・使用することは禁止されています。"
                )
        # 動的open監視の有効化
        enable_data_free_monitoring()

    # 4. 評価データセットとFIM/学習データの重複（リーク）禁止検証
    eval_dataset = getattr(args, "eval_dataset_path", getattr(args, "eval_dataset", None))
    fim_dataset = getattr(args, "fim_dataset_path", getattr(args, "fim_dataset", None))
    training_dataset = getattr(args, "utility_dataset_path", getattr(args, "safety_dataset_path", None))
    
    if eval_dataset and fim_dataset:
        if os.path.abspath(eval_dataset) == os.path.abspath(fim_dataset):
            raise ValueError(
                f"[Steering Hook Rule Violation] FIM推定用のデータセットと評価用のデータセットが重複しています: {eval_dataset}\n"
                f"これらは完全に分離しなければなりません（データリークの禁止）。"
            )
    if eval_dataset and training_dataset:
        if os.path.abspath(eval_dataset) == os.path.abspath(training_dataset):
            raise ValueError(
                f"[Steering Hook Rule Violation] 学習用のデータセットと評価用のデータセットが重複しています: {eval_dataset}\n"
                f"これらは完全に分離しなければなりません（データリークの禁止）。"
            )


def verify_merge_method(method, config_file=None):
    """
    マージ手法の検証（レガシー互換用）。
    TIESやDAREなどの比較手法において、カスタムコードではなく公式 mergekit 経由で実行されているかを確認します。
    """
    method_lower = method.lower()
    
    # 比較手法の場合のチェック
    if method_lower in ["ties", "dare", "task_arithmetic", "task-arithmetic"]:
        if config_file is None or not os.path.exists(config_file):
            raise ValueError(
                f"[Steering Hook Rule Violation] 比較手法 ({method}) の実行には、独自カスタム実装コードではなく、"
                f"公式 mergekit (yaml 設定ファイル) を使用する必要があります。設定ファイルが指定されていないか、存在しません。"
            )
        
        with _original_open(config_file, "r") as f:
            content = f.read()
            if "merge_method:" not in content:
                raise ValueError(
                    f"[Steering Hook Rule Violation] 指定されたマージ設定ファイル ({config_file}) は、"
                    f"公式 mergekit の有効な設定フォーマットではありません。"
                )
        print(f"[Steering Hook] 比較手法の検証をパスしました (手法: {method}, 設定: {config_file})")


def verify_evaluation_outputs(output_texts, over_refusal_threshold=0.9):
    """
    評価実行時に、モデルが「推論崩壊」や「過剰拒絶」を起こしていないかを監視します。
    - 推論崩壊 (Inference Collapse): 同じ単語や文の繰り返し (バイグラムの重複度が高いなど)
    - 過剰拒絶 (Over-refusal): 応答テキストの大部分が定型的な拒否表現である
    """
    if not output_texts:
        return
    
    refusal_keywords = [
        "sorry", "i cannot", "i am unable", "i'm sorry", "against my guidelines",
        "申し訳ありません", "お答えできません", "ポリシーに反します"
    ]
    
    refused_count = 0
    total_samples = len(output_texts)
    
    for text in output_texts:
        text_lower = text.lower()
        if any(kw in text_lower for kw in refusal_keywords):
            refused_count += 1
            
        words = text_lower.split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.2:
                print(
                    f"[Steering Hook Warning] モデル出力に推論崩壊の兆候が見られます "
                    f"(ユニーク単語比率: {unique_ratio:.2f}). 出力例: \"{text[:100]}...\""
                )
                
    if total_samples > 0:
        refusal_rate = refused_count / total_samples
        if refusal_rate >= over_refusal_threshold:
            print(
                f"[Steering Hook Warning] モデル出力に過剰拒絶の兆候が見られます "
                f"(拒絶率: {refusal_rate*100:.1f}% >= 閾値 {over_refusal_threshold*100}%)."
            )
            
    print(f"[Steering Hook] 評価出力の監視が完了しました (サンプル数: {total_samples})")
