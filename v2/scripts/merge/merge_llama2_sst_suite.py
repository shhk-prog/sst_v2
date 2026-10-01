# scripts/merge/merge_llama2_sst_suite.py
import os
import sys
import json
import yaml
import torch
import shutil
import argparse
import subprocess
import safetensors
import safetensors.torch
from pathlib import Path
from datetime import datetime

# scriptsフォルダをパスに追加して steering_hook をインポート
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import steering_hook

def parse_args():
    parser = argparse.ArgumentParser(description="Llama-2-7B Multi-model SST-Merge Suite")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML")
    parser.add_argument("--output_root", type=str, default="models/merged", help="Root directory to save merged models")
    parser.add_argument("--method", type=str, default=None, help="Override merge method in YAML")
    parser.add_argument("--alpha", type=float, default=None, help="Override alpha in YAML")
    parser.add_argument("--k", type=str, default=None, help="Override k (top-k or 'soft') in YAML")
    parser.add_argument("--pattern", type=str, default=None, help="Override pattern (comma-separated, e.g. math,code) in YAML")
    return parser.parse_args()

class Llama2SSTMerger:
    def __init__(self, config_path, output_root):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        self.output_root = output_root
        
        self.base_model_path = self.config["model"]["base_model"]
        self.model_paths = {
            "math": self.config["model"]["math_model"],
            "code": self.config["model"]["code_model"],
            "medical": self.config["model"]["medical_model"]
        }
        
    def verify_config(self, method, pattern):
        # steering_hookによる適合性検証のダミーargsを作成
        # data_free_sst_merge時に実データパスが指定されているとフックで弾かれます
        class DummyArgs:
            pass
        args = DummyArgs()
        args.base_model = self.base_model_path
        args.method = method
        args.implementation = "mergekit" if method in ["ties", "dare", "task_arithmetic", "della"] else "official"
        
        if method == "data_free_sst_merge":
            # Data-Free時は統計・データパスの参照を禁止
            args.method = "data_free_sst"
            args.utility_dataset_path = None
            args.safety_dataset_path = None
            
        steering_hook.verify_experiment_config(args)

    def generate_mergekit_yaml(self, pattern_names, method, alpha, k=0.3):
        """mergekit用のYAML設定を生成"""
        # mergekitがインストールされているか確認、無ければRuntimeError (kiroルール遵守)
        try:
            import mergekit
        except ImportError:
            raise RuntimeError("[Kiro Rule Violation] mergekit がインストールされていません。比較手法の実行には mergekit が必須です。")

        models_list = [{"model": self.base_model_path, "parameters": {"weight": 1.0}}]
        for name in pattern_names:
            models_list.append({
                "model": self.model_paths[name],
                "parameters": {"weight": alpha}
            })
            
        config_dict = {
            "base_model": self.base_model_path,
            "merge_method": "ties" if method == "ties" else ("dare" if method == "dare" else ("della" if method == "della" else "linear")),
            "dtype": "float16",
            "models": models_list
        }
        
        # DARE, DELLA などのパラメータを適用
        if method in ["dare", "della", "ties"]:
            config_dict["parameters"] = {
                "density": k if isinstance(k, float) else 0.5,
                "weight": alpha
            }
            
        return yaml.dump(config_dict)

    def run_mergekit(self, pattern_names, method, alpha, k, output_dir):
        """mergekitをサブプロセスで実行 (kiroルール遵守)"""
        print(f"Running mergekit for {method} (Pattern: {pattern_names})...")
        yaml_content = self.generate_mergekit_yaml(pattern_names, method, alpha, k)
        
        yaml_path = os.path.join(output_dir, "mergekit_config.yaml")
        os.makedirs(output_dir, exist_ok=True)
        with open(yaml_path, "w") as f:
            f.write(yaml_content)
            
        # mergekit-yaml をサブプロセスで実行
        cmd = ["mergekit-yaml", yaml_path, output_dir, "--device", "cpu", "--low-cpu-memory"]
        try:
            subprocess.run(cmd, check=True)
        except Exception as e:
            raise RuntimeError(f"mergekit-yaml execution failed: {e}")

    def save_metadata(self, output_dir, method, pattern_names, alpha, k):
        """merge_metadata.json の同梱保存および metadata/ へのバックアップ複製 (kiroルール遵守)"""
        metadata = {
            "base_model": self.base_model_path,
            "merge_method": method,
            "pattern": pattern_names,
            "hyperparameters": {
                "alpha": alpha,
                "k": k,
                "seed": self.config["experiment"]["seed"]
            },
            "timestamp": datetime.now().isoformat(),
            "execution_command": " ".join(sys.argv)
        }
        
        # 1. 出力先に保存
        os.makedirs(output_dir, exist_ok=True)
        metadata_path = os.path.join(output_dir, "merge_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
            
        # 2. グローバル metadata/ に複製
        global_metadata_dir = os.path.abspath(os.path.join(self.output_root, "../../metadata"))
        os.makedirs(global_metadata_dir, exist_ok=True)
        basename = os.path.basename(output_dir.rstrip("/"))
        global_metadata_path = os.path.join(global_metadata_dir, f"{basename}_metadata.json")
        shutil.copy(metadata_path, global_metadata_path)
        print(f"Metadata saved to {metadata_path} and backed up to {global_metadata_path}")

    def stream_merge_custom(self, pattern_names, method, alpha, k, output_dir):
        """safetensorsを利用したメモリ効率の良いストリーミングマージエンジン (独自手法)"""
        print(f"Starting custom streaming merge: {method} (Pattern: {pattern_names})...")
        
        # Data-Free設定時の遮断フックの有効化 (kiroルール)
        if method == "data_free_sst_merge":
            steering_hook.enable_data_free_monitoring()
            
        # 対象モデルディレクトリのリストアップ
        model_dirs = [self.model_paths[name] for name in pattern_names]
        
        # インデックスファイルのロード
        index_name = "model.safetensors.index.json"
        base_index_path = os.path.join(self.base_model_path, index_name)
        
        if os.path.exists(base_index_path):
            with open(base_index_path, "r") as f:
                index_data = json.load(f)
            weight_map = index_data["weight_map"]
            
            # 出力先にもindexを保存
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, index_name), "w") as f:
                json.dump(index_data, f, indent=2)
        else:
            # 分割ファイルでない場合
            raise RuntimeError(f"Base model index file not found in {self.base_model_path}")
            
        # その他の設定ファイルをコピー
        for fname in ["config.json", "generation_config.json", "tokenizer.json", "tokenizer.model", "special_tokens_map.json", "tokenizer_config.json"]:
            src = os.path.join(self.base_model_path, fname)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(output_dir, fname))

        # ファイルごとのキーのグループ化
        files_to_keys = {}
        for key, filename in weight_map.items():
            if filename not in files_to_keys:
                files_to_keys[filename] = []
            files_to_keys[filename].append(key)
            
        # テンソル単位でストリーミングマージ
        for filename, keys in files_to_keys.items():
            print(f"Merging {filename} ({len(keys)} parameters)...")
            
            # 各モデルからsafe_open
            base_file = safetensors.safe_open(os.path.join(self.base_model_path, filename), framework="pt", device="cpu")
            model_files = [safetensors.safe_open(os.path.join(m_dir, filename), framework="pt", device="cpu") for m_dir in model_dirs]
            
            merged_tensors = {}
            for key in keys:
                # テンソルのロード
                t_base = base_file.get_tensor(key)
                t_models = [m_file.get_tensor(key) for m_file in model_files]
                
                # マージアルゴリズムの適用
                t_merged = self.apply_merge_logic(key, t_base, t_models, method, alpha, k)
                merged_tensors[key] = t_merged
                
            # 保存
            safetensors.torch.save_file(merged_tensors, os.path.join(output_dir, filename))
            
            # 解放
            del merged_tensors
            import gc; gc.collect()
            
        # 監視フックの解除
        if method == "data_free_sst_merge":
            steering_hook.disable_data_free_monitoring()
            
        print(f"Streaming merge completed. Saved to {output_dir}")

    def apply_merge_logic(self, key, t_base, t_models, method, alpha, k):
        """個別パラメータのマージロジック"""
        # アダプター以外のテンソルはBaseをそのまま残す（または線形平均）
        if "embed_tokens" in key or "lm_head" in key or "norm" in key:
            return t_base
            
        # タスクベクトルの計算
        deltas = [t_model - t_base for t_model in t_models]
        
        # 1. Fisher-Weighted Averaging (データフリー版: タスクベクトルの二乗値を重要度とする)
        if method == "fisher_weighted_averaging":
            importances = [d.pow(2) for d in deltas]
            sum_importances = sum(importances) + 1e-6
            weighted_delta = sum(imp * d for imp, d in zip(importances, deltas)) / sum_importances
            return t_base + alpha * weighted_delta
            
        # 2. Data-Free SST-Merge (3モデル拡張マスク)
        elif method == "data_free_sst_merge":
            # 各モデルについて、他のモデルの平均重要度に対するSST比を計算
            t_merged = t_base.clone()
            for i, delta in enumerate(deltas):
                importance_self = delta.pow(2)
                # 他のモデルの重要度
                other_deltas = [deltas[j] for j in range(len(deltas)) if j != i]
                importance_others = sum(od.pow(2) for od in other_deltas) / len(other_deltas) if other_deltas else torch.zeros_like(importance_self)
                
                # SST比: 自己重要度 / (他者重要度 + eps)
                sst_ratio = importance_self / (importance_others + 1e-6)
                
                # マスクの計算
                if k == "soft":
                    # ソフトマスク (シグモイド)
                    mean_val = sst_ratio.mean()
                    std_val = sst_ratio.std() + 1e-8
                    normalized = (sst_ratio - mean_val) / std_val
                    mask = torch.sigmoid(normalized)
                else:
                    # ハードマスク (Top-k%)
                    k_val = float(k) if k else 0.2
                    flat = sst_ratio.flatten()
                    k_idx = int(len(flat) * (1 - k_val))
                    k_idx = min(max(k_idx, 0), len(flat) - 1)
                    threshold = torch.kthvalue(flat, k_idx).values.item()
                    mask = (sst_ratio >= threshold).float()
                    
                # 加算
                t_merged += alpha * mask * delta
            return t_merged
            
        # 3. LED-Merging (干渉抑制・重要レイヤーマージ)
        elif method == "led_merging":
            # テンソルの絶対値が最も大きいモデルの更新を選択的に適用
            importances = [d.abs() for d in deltas]
            max_idx = torch.stack(importances).argmax(dim=0)
            
            t_merged = t_base.clone()
            for i, delta in enumerate(deltas):
                mask = (max_idx == i).float()
                t_merged += alpha * mask * delta
            return t_merged
            
        # 4. SafeMERGE (レイヤー選択的マージ)
        elif method == "safemerge":
            # 最初の数層および最後の数層はマージを抑制し、中間層のみマージする
            layer_num = -1
            for chunk in key.split("."):
                if chunk.isdigit():
                    layer_num = int(chunk)
                    break
            
            # Llama-2-7Bは32層。最初と最後の3層を安全領域としてマージ比率を下げる (0.2), 中間はそのまま
            scale = 1.0
            if layer_num != -1:
                if layer_num < 3 or layer_num > 28:
                    scale = 0.2
                    
            weighted_delta = sum(deltas) / len(deltas)
            return t_base + (alpha * scale) * weighted_delta

        # 5. MergeAlign
        elif method == "merge_align":
            # 全モデルの平均ベクトル
            weighted_delta = sum(deltas) / len(deltas)
            return t_base + alpha * weighted_delta
            
        # デフォルト (Task Arithmetic)
        else:
            weighted_delta = sum(deltas) / len(deltas)
            return t_base + alpha * weighted_delta

    def execute_experiment(self, override_method=None, override_alpha=None, override_k=None, override_pattern=None):
        patterns = self.config["merge"]["patterns"]
        methods = self.config["merge"]["methods"]
        alphas = self.config["merge"]["alpha_sweep"]
        ks = self.config["merge"]["k_sweep"]
        
        # オーバーライドの適用
        if override_method:
            methods = [override_method]
        if override_alpha is not None:
            alphas = [override_alpha]
        if override_k:
            ks = [override_k]
        if override_pattern:
            patterns = [[p.strip() for p in override_pattern.split(",")]]
            
        for pattern in patterns:
            for method in methods:
                self.verify_config(method, pattern)
                
                # TIES/DAREなどの基本マージはmergekitで一括実行
                if method in ["ties", "dare", "task_arithmetic", "della"]:
                    # パラメータのスイープを実行
                    for alpha in alphas:
                        for k in ks:
                            # k_sweepの"soft"はmergekitでは使えないためスキップ
                            if k == "soft":
                                continue
                            
                            exp_name = f"{method}_{'_'.join(pattern)}_a{alpha}_k{k}"
                            output_dir = os.path.join(self.output_root, exp_name)
                            
                            if os.path.exists(output_dir) and os.listdir(output_dir):
                                print(f"Skipping existing: {exp_name}")
                                continue
                                
                            try:
                                self.run_mergekit(pattern, method, alpha, k, output_dir)
                                self.save_metadata(output_dir, method, pattern, alpha, k)
                            except Exception as e:
                                print(f"Error executing {exp_name}: {e}")
                else:
                    # 独自マージエンジン (SST-Merge, FWA, LED等) でストリーミングマージ
                    for alpha in alphas:
                        for k in ks:
                            exp_name = f"{method}_{'_'.join(pattern)}_a{alpha}_k{k}"
                            output_dir = os.path.join(self.output_root, exp_name)
                            
                            if os.path.exists(output_dir) and os.listdir(output_dir):
                                print(f"Skipping existing: {exp_name}")
                                continue
                                
                            try:
                                self.stream_merge_custom(pattern, method, alpha, k, output_dir)
                                self.save_metadata(output_dir, method, pattern, alpha, k)
                            except Exception as e:
                                print(f"Error executing {exp_name}: {e}")

if __name__ == "__main__":
    args = parse_args()
    merger = Llama2SSTMerger(args.config, args.output_root)
    merger.execute_experiment(
        override_method=args.method,
        override_alpha=args.alpha,
        override_k=args.k,
        override_pattern=args.pattern
    )
