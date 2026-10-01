"""
データフリーSST-Merge実行スクリプト

既存LoRAアダプターを読み込み、学習データなしでマージを実行
"""

import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import torch
from core.sst_merge_data_free import SSTMergeDataFree, save_merged_adapter, FIMCalculatorDataFree, GEVPSolver
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#####################################################
# 設定
#####################################################

# ベースモデル
model_id = "meta-llama/Llama-3.1-8B-Instruct"

# スクリプトの場所を基準に絶対パスを解決するヘルパー
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent

# 相対パスはプロジェクトルート基準で記述
adapter_base = project_root / "models/finetuned/adapters/FT_model"

# マージするアダプターのペア
merge_pairs = [
    # (Utility adapter, Safety adapter, output_name)
    (str(adapter_base / "A5_utility_meta_llama_3.1_8b_instruct_repliqa_r16_10ep_lr2e-4"),
     str(adapter_base / "A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4"),
     "A5_A7"),
    
    (str(adapter_base / "A6_utility_meta_llama_3.1_8b_instruct_alpaca_r16_10ep_lr2e-4"),
     str(adapter_base / "A7_safety_meta_llama_3.1_8b_instruct_r16_5ep_lr2e-4"),
     "A6_A7"),
]

# SST-Merge設定
k_values = [5,10,20,30,40,50]  # k値（データフリー版では命名用、将来的にtop-k ratioとして使用可能）
use_layerwise_options = [True,False]  # Layerwise重み調整: [False] or [True] or [False, True]
merge_mode_options = ["additive", "interpolation"]  # マージモード: "additive" or "interpolation"
alpha_values = [0.05,0.07,0.09,0.1,0.12,0.15,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]
use_gevp = True  # GEVP使用（Falseの場合はシンプルなTask Arithmetic風マージ）
top_k_ratio_options = [None]  # [None]=ソフトマスク, [0.3]=上位30%, 複数指定可能

# 出力ディレクトリ
output_adapter_dir = str(project_root / "models/merged/data_free/adapters/merge_model_data_free")
output_full_dir = str(project_root / "models/merged/data_free/full/merge_model_data_free_full")

# LoRAアダプターのパス  
adapter_dir = str(adapter_base)

#####################################################


def convert_adapter_to_full(
    adapter_path: str,
    output_path: str,
    base_model_id: str
) -> bool:
    """
    アダプターをフルモデルに変換
    
    Args:
        adapter_path: アダプターディレクトリパス
        output_path: 出力ディレクトリパス
        base_model_id: ベースモデルID
    
    Returns:
        成功したらTrue
    """
    try:
        logger.info(f"Loading base model: {base_model_id}")
        
        # ベースモデルをロード
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch.bfloat16,
            device_map='auto'
        )
        
        logger.info(f"Loading adapter from: {adapter_path}")
        
        # アダプターをロード
        model = PeftModel.from_pretrained(base_model, adapter_path)
        
        logger.info("Merging adapter into base model...")
        
        # アダプターをベースモデルにマージ
        model = model.merge_and_unload()
        
        # トークナイザーもロード
        tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        
        # 保存
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving full model to: {output_path}")
        model.save_pretrained(str(output_path))
        tokenizer.save_pretrained(str(output_path))
        
        logger.info(f"✓ Full model saved successfully")
        
        # メモリ解放
        del model
        del base_model
        torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert adapter to full model: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_adapter_weights(adapter_path: str) -> dict:
    """
    LoRAアダプターの重みを読み込み
    
    Args:
        adapter_path: アダプターディレクトリパス
    
    Returns:
        adapter_dict: LoRA重み辞書
    """
    from safetensors.torch import load_file
    
    # スクリプトの場所を基準に絶対パスに変換
    script_dir = Path(__file__).parent
    adapter_dir = (script_dir / adapter_path).resolve()
    
    # .binファイルを優先、なければ.safetensorsを読み込む
    adapter_bin = adapter_dir / "adapter_model.bin"
    adapter_safetensors = adapter_dir / "adapter_model.safetensors"
    
    if adapter_bin.exists():
        adapter_dict = torch.load(adapter_bin, map_location='cpu')
        logger.info(f"Loaded adapter from .bin: {adapter_path}")
    elif adapter_safetensors.exists():
        adapter_dict = load_file(str(adapter_safetensors))
        logger.info(f"Loaded adapter from .safetensors: {adapter_path}")
    else:
        raise FileNotFoundError(
            f"Adapter not found: neither {adapter_bin} nor {adapter_safetensors} exists"
        )
    
    logger.info(f"  Keys: {len(adapter_dict)}")
    
    return adapter_dict


def merge_and_save_full_model(
    base_model_id: str,
    merged_adapter: dict,
    output_path: str
):
    """
    マージされたアダプターをベースモデルに統合して保存
    
    Args:
        base_model_id: ベースモデルID
        merged_adapter: マージされたアダプター
        output_path: 出力パス
    """
    logger.info(f"\nLoading base model: {base_model_id}")
    
    # ベースモデルとトークナイザーを読み込み
    model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=torch.bfloat16,
        device_map='cpu'
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    
    # PEFTモデルとして保存（adapter_model.binとして）
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    torch.save(merged_adapter, output_path / "adapter_model.bin")
    
    # adapter_config.jsonも必要（既存アダプターからコピー）
    # ここでは簡略化のためスキップ
    
    logger.info(f"Merged adapter saved to: {output_path}")


def main():
    logger.info("="*70)
    logger.info("Data-Free SST-Merge Execution")
    logger.info("="*70)
    
    # 統計情報
    total_tasks = len(merge_pairs) * len(k_values) * len(use_layerwise_options) * len(top_k_ratio_options) * len(alpha_values)
    completed = 0
    
    logger.info(f"\nTotal configurations: {total_tasks}")
    logger.info(f"  Pairs: {len(merge_pairs)}")
    logger.info(f"  k values: {k_values}")
    logger.info(f"  Layerwise options: {use_layerwise_options}")
    logger.info(f"  Top-k ratio options: {top_k_ratio_options}")
    logger.info(f"  Alpha values: {len(alpha_values)}")
    
    for utility_path, safety_path, pair_name in merge_pairs:
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing pair: {pair_name}")
        logger.info(f"  Utility: {utility_path}")
        logger.info(f"  Safety: {safety_path}")
        logger.info(f"{'='*70}")
        
        # Step 1: アダプター読み込み
        try:
            utility_adapter = load_adapter_weights(utility_path)
            safety_adapter = load_adapter_weights(safety_path)
        except FileNotFoundError as e:
            logger.error(f"Skipping {pair_name}: {e}")
            continue
        
        # Step 2: FIMとGEVPの事前計算（最適化: ループ外で1回だけ実行）
        logger.info(f"\nOptimization: Pre-computing FIM and GEVP for {pair_name}...")
        
        # FIM計算
        fim_calc = FIMCalculatorDataFree()
        logger.info("Computing Utility FIM (data-free)...")
        F_benign = fim_calc.compute_fim_from_lora(utility_adapter)
        logger.info("Computing Safety FIM (data-free)...")
        F_harm = fim_calc.compute_fim_from_lora(safety_adapter)
        
        # GEVP解法
        eigenvalues = None
        gevp_solver = None
        if use_gevp:
            gevp_solver = GEVPSolver()
            logger.info("Solving GEVP...")
            eigenvalues, _ = gevp_solver.solve_gevp_diagonal(F_harm, F_benign)
        
        # マスクのキャッシュ (top_k_ratio -> mask)
        mask_cache = {}

        # Step 3: 各設定の組み合わせでマージ
        for merge_mode in merge_mode_options:
            for k in k_values:
                for use_layerwise in use_layerwise_options:
                    for top_k_ratio_base in top_k_ratio_options:
                        # k値をtop_k_ratioに変換（k%のパラメータを選択）
                        if top_k_ratio_base is None:
                            top_k_ratio = k / 100.0
                        else:
                            top_k_ratio = top_k_ratio_base
                        
                        # マスクの取得または計算（キャッシュ利用）
                        mask = None
                        if use_gevp and top_k_ratio is not None:
                            if top_k_ratio not in mask_cache:
                                logger.info(f"Computing safety mask for top_k_ratio={top_k_ratio}...")
                                mask_cache[top_k_ratio] = gevp_solver.compute_safety_mask(eigenvalues, top_k_ratio)
                            mask = mask_cache[top_k_ratio]
                        
                        for alpha in alpha_values:
                            logger.info(f"\n{'-'*60}")
                            logger.info(f"mode={merge_mode}, k={k}, layerwise={use_layerwise}, top_k={top_k_ratio}, α={alpha}")
                            logger.info(f"{'-'*60}")
                            
                            # 出力パス生成
                            output_name = f"{pair_name}_data_free"
                            if merge_mode == "interpolation":
                                output_name += "_interp"
                            output_name += f"_k{k}"
                            if use_layerwise:
                                output_name += "_lw"
                            output_name += f"_a{alpha}"
                            if top_k_ratio is not None:
                                output_name += f"_topk{int(top_k_ratio*100)}"
                        
                            # スクリプトの場所を基準に絶対パスに変換
                            script_dir = Path(__file__).parent
                            adapter_output = (script_dir / output_adapter_dir / output_name).resolve()
                            full_output = (script_dir / output_full_dir / output_name).resolve()
                            
                            # 既存モデルのチェック
                            adapter_exists = adapter_output.exists() and ((adapter_output / "adapter_model.bin").exists() or (adapter_output / "adapter_model.safetensors").exists())
                            full_exists = full_output.exists() and (full_output / "config.json").exists()
                            
                            if adapter_exists and full_exists:
                                logger.info(f"[SKIP] Both adapter and full model already exist: {output_name}")
                                completed += 1
                                continue
                            
                            # SST-Merge実行（最適化: 事前計算データを渡す）
                            sst_merge = SSTMergeDataFree(
                                safety_weight=alpha,
                                use_gevp=use_gevp,
                                top_k_ratio=top_k_ratio,
                                use_layerwise=use_layerwise,
                                merge_mode=merge_mode
                            )

                            merged_adapter = sst_merge.merge(
                                utility_adapter, 
                                safety_adapter,
                                f_benign=F_benign,
                                f_harm=F_harm,
                                eigenvalues=eigenvalues,
                                mask=mask
                            )
                            
                            # Step 1: アダプターを保存
                            if not adapter_exists:
                                utility_path_abs = (script_dir / utility_path).resolve()
                                save_merged_adapter(merged_adapter, adapter_output, str(utility_path_abs))
                                logger.info(f"✓ Adapter saved: {output_name}")
                            else:
                                logger.info(f"[SKIP] Adapter already exists: {output_name}")
                                config_file = adapter_output / "adapter_config.json"
                                if not config_file.exists():
                                    logger.warning(f"adapter_config.json not found in existing adapter, copying from source...")
                                    utility_path_abs = (script_dir / utility_path).resolve()
                                    source_config = utility_path_abs / "adapter_config.json"
                                    if source_config.exists():
                                        import shutil
                                        shutil.copy(source_config, config_file)
                                        logger.info(f"✓ Copied adapter_config.json to existing adapter")
                                    else:
                                        logger.error(f"Cannot find adapter_config.json in source: {utility_path_abs}")

                            # Step 2: フルモデルに変換
                            if not full_exists:
                                logger.info(f"Converting adapter to full model: {output_name}")
                                success = convert_adapter_to_full(
                                    str(adapter_output),
                                    str(full_output),
                                    model_id
                                )
                                
                                if success:
                                    logger.info(f"✓ Full model saved: {output_name}")
                                    completed += 1
                                else:
                                    logger.error(f"✗ Full model conversion failed: {output_name}")
                            else:
                                logger.info(f"[SKIP] Full model already exists: {output_name}")
                                completed += 1
    
    logger.info("\n" + "="*70)
    logger.info(f"Data-Free SST-Merge completed!")
    logger.info(f"  Total configurations: {total_tasks}")
    logger.info(f"  Completed: {completed}")
    logger.info(f"  Adapter output: {output_adapter_dir}")
    logger.info(f"  Full model output: {output_full_dir}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
