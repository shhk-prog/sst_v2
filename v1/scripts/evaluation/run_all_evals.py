"""
全マージモデルを評価するスクリプト

merge_modelフォルダ内の全モデルを評価:
- A5_A7 → merge_repliqa_eval.py + merge_jailbreak_eval.py
- A6_A7 → merge_alpaca_eval.py + merge_jailbreak_eval.py

既存の評価スクリプトを呼び出して実行します。
既存の評価結果はスキップ。
"""

import os
import subprocess
import sys
from pathlib import Path
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#####################################################
# 設定
#####################################################
gpu_num = input("gpu num:")

merge_model_dir = "../../models/merged/interpolation/full/merge_model_interpolation"
#"../../models/merged/sst_merge/full/merge_model"
#"../../models/merged/interpolation/full/merge_model_interpolation"
#"../../models/merged/data_free/full/merge_model_data_free_full"

output_dir = "../../eval/merged/interpolation"
#"../../eval/merged/sst_merge/merge_eval"
#"../../eval/merged/interpolation"
#"../../eval/merged/data_free"

# 評価対象のパターン (正規表現)

target_patterns = [
    r"A5_A7_.*",
    r"A6_A7_.*",
]

# 評価スクリプトのパス（main関数内で絶対パスに変換）
eval_script_names = {
    "repliqa": "merge_repliqa_eval.py",
    "alpaca": "merge_alpaca_eval.py",
    "jailbreak": "merge_jailbreak_eval.py",
}
#####################################################


def get_eval_type(model_name: str) -> str:
    """モデル名から評価タイプを判定"""
    if model_name.startswith("A5_A7"):
        return "repliqa"
    elif model_name.startswith("A6_A7"):
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
    # 正規表現でmerged_model_path = "..." の部分を置換
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
    temp_script = create_temp_eval_script(script_path, model_path, gpu_num, output_dir)
    
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
    logger.info("Run All Evaluations")
    logger.info("="*70)
    
    # スクリプトの場所を基準に絶対パスに変換
    script_dir = Path(__file__).parent
    output_base = (script_dir / output_dir).resolve()
    output_base.mkdir(parents=True, exist_ok=True)
    
    # Evaluation scriptsを絶対パスで構築
    eval_scripts = {
        key: str(script_dir / script_name)
        for key, script_name in eval_script_names.items()
    }
    
    # マージモデル一覧を取得
    merge_model_path = (script_dir / merge_model_dir).resolve()
    model_dirs = [d for d in merge_model_path.iterdir() if d.is_dir()]
    
    # パターンでフィルタ
    target_models = []
    for model_dir in model_dirs:
        model_name = model_dir.name
        for pattern in target_patterns:
            if re.match(pattern, model_name):
                target_models.append(model_dir)
                break
    
    # アルファベット順にソート
    target_models.sort(key=lambda x: x.name)
    
    logger.info(f"Found {len(target_models)} models to evaluate")
    for m in target_models:
        logger.info(f"  - {m.name}")
    
    # 統計
    completed = 0
    skipped = 0
    failed = 0
    
    for model_dir in target_models:
        model_name = model_dir.name
        model_path = str(model_dir)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Evaluating: {model_name}")
        logger.info("="*60)
        
        # 評価タイプを判定
        eval_type = get_eval_type(model_name)
        if eval_type == "unknown":
            logger.warning(f"Unknown eval type for {model_name}, skipping")
            skipped += 1
            continue
        
        # Utility評価のチェック
        utility_exists = check_eval_exists(output_base, model_name, eval_type)
        jailbreak_exists = check_eval_exists(output_base, model_name, "jailbreak")
        
        if utility_exists and jailbreak_exists:
            logger.info(f"[SKIP] All evaluations exist for {model_name}")
            skipped += 1
            continue
        
        # Utility評価
        if not utility_exists:
            script = eval_scripts[eval_type]
            logger.info(f"Running {script} for {model_name}...")
            
            success = run_eval_script(script, model_path, gpu_num, str(output_base))
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
            
            success = run_eval_script(script, model_path, gpu_num, str(output_base))
            if success:
                logger.info(f"[OK] jailbreak eval completed")
            else:
                logger.error(f"[FAIL] jailbreak eval failed")
                failed += 1
        else:
            logger.info(f"[SKIP] Jailbreak eval already exists")
        
        completed += 1
    
    # 結果サマリー
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)
    logger.info(f"Total models:  {len(target_models)}")
    logger.info(f"Completed:     {completed}")
    logger.info(f"Skipped:       {skipped}")
    logger.info(f"Failed:        {failed}")
    logger.info(f"Output dir:    {output_base}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
