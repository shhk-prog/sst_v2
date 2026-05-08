"""
補間型SST-Mergeモデルの評価スクリプト

評価対象:
- ./merge_model_interpolation/ 内のモデル
- 命名規則: *_sst_interp_* で始まるモデル

出力先:
- ./merge_eval_interpolation/
"""

import os
import subprocess
import sys
import re
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#####################################################
# 設定
#####################################################
gpu_num = input("gpu num:")

model_dir = Path("../../models/merged/interpolation/full/merge_model_interpolation")
output_dir = Path("../../eval/merged/interpolation")
output_dir.mkdir(parents=True, exist_ok=True)

# 評価スクリプト
eval_scripts = {
    "jailbreak": "merge_jailbreak_eval.py",
    "alpaca": "merge_alpaca_eval.py",
    "repliqa": "merge_repliqa_eval.py",
}
#####################################################


def get_eval_type(model_name: str) -> str:
    """モデル名から評価タイプを判定"""
    if "A5_A7" in model_name:
        return "repliqa"
    elif "A6_A7" in model_name:
        return "alpaca"
    else:
        return "unknown"


def check_eval_exists(output_dir: Path, model_name: str, eval_type: str) -> bool:
    """評価結果が既に存在するかチェック"""
    output_file = output_dir / f"{model_name}_{eval_type}_eval_results.json"
    return output_file.exists()


def create_temp_eval_script(script_path: str, model_path: str, gpu_num: str, output_dir: str) -> str:
    """一時的な評価スクリプトを作成（merged_model_pathとoutput_dirを書き換え）"""
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # gpu numの入力部分をスキップ
    content = content.replace(
        'num = input("gpu num:")',
        f'num = "{gpu_num}"'
    )
    
    # merged_model_pathを書き換え
    content = re.sub(
        r'merged_model_path\s*=\s*"[^"]*"',
        f'merged_model_path = "{model_path}"',
        content
    )
    
    # output_dirを書き換え
    content = re.sub(
        r'output_dir\s*=\s*"[^"]*"',
        f'output_dir = "{output_dir}"',
        content
    )
    
    # 一時ファイルに保存
    temp_script = script_path.replace('.py', '_temp.py')
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return temp_script


def run_eval_script(script_path: str, model_path: str, gpu_num: str, output_dir: str) -> bool:
    """評価スクリプトを実行"""
    temp_script = create_temp_eval_script(script_path, model_path, gpu_num, str(output_dir))
    
    try:
        result = subprocess.run(
            [sys.executable, temp_script],
            capture_output=True,
            text=True,
            timeout=3600  # 1時間タイムアウト
        )
        
        if result.returncode == 0:
            logger.info(f"Script output:\n{result.stdout[-500:]}")  # 最後の500文字
            return True
        else:
            logger.error(f"Script error:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("Script timed out")
        return False
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        return False
    finally:
        # 一時ファイルを削除
        try:
            os.remove(temp_script)
        except:
            pass


def main():
    logger.info("="*70)
    logger.info("Evaluating SST-Merge (Interpolation Mode) Models")
    logger.info(f"Model directory: {model_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("="*70)
    
    # モデルを検索
    models = []
    for model_path in model_dir.iterdir():
        if model_path.is_dir() and "_sst_interp_" in model_path.name:
            if (model_path / "config.json").exists():
                models.append(model_path)
    
    models.sort(key=lambda x: x.name)
    logger.info(f"Found {len(models)} interpolation models to evaluate")
    
    # 統計
    completed = 0
    failed = 0
    skipped = 0
    
    # 各モデルを評価
    for model_path in models:
        model_name = model_path.name
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Model: {model_name}")
        logger.info("="*60)
        
        # 評価タイプを判定
        eval_type = get_eval_type(model_name)
        if eval_type == "unknown":
            logger.warning(f"Unknown eval type for {model_name}, skipping")
            skipped += 1
            continue
        
        # Utility評価のチェック
        utility_exists = check_eval_exists(output_dir, model_name, eval_type)
        jailbreak_exists = check_eval_exists(output_dir, model_name, "jailbreak")
        
        if utility_exists and jailbreak_exists:
            logger.info(f"[SKIP] All evaluations exist for {model_name}")
            skipped += 1
            continue
        
        # Utility評価
        if not utility_exists:
            script = eval_scripts[eval_type]
            logger.info(f"Running {script} for {model_name}...")
            
            success = run_eval_script(script, str(model_path), gpu_num, str(output_dir))
            if success:
                logger.info(f"[OK] {eval_type} eval completed")
            else:
                logger.error(f"[FAIL] {eval_type} eval failed")
                failed += 1
        else:
            logger.info(f"[SKIP] {eval_type} eval already exists")
        
        # Jailbreak評価
        if not jailbreak_exists:
            script = eval_scripts["jailbreak"]
            logger.info(f"Running {script} for {model_name}...")
            
            success = run_eval_script(script, str(model_path), gpu_num, str(output_dir))
            if success:
                logger.info(f"[OK] jailbreak eval completed")
            else:
                logger.error(f"[FAIL] jailbreak eval failed")
                failed += 1
        else:
            logger.info(f"[SKIP] Jailbreak eval already exists")
        
        completed += 1
    
    # サマリー
    logger.info("\n" + "="*70)
    logger.info("EVALUATION SUMMARY")
    logger.info("="*70)
    logger.info(f"Total models: {len(models)}")
    logger.info(f"Completed: {completed}")
    logger.info(f"Skipped: {skipped}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Results: {output_dir}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
