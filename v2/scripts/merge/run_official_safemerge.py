import argparse
import sys
import os

# scripts フォルダをパスに追加して steering_hook をインポート
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import steering_hook

# third_party/SafeMERGE へのパスを追加
third_party_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../third_party/SafeMERGE'))
sys.path.append(third_party_dir)

try:
    from get_safemerge_model import get_safemerge
except ImportError as e:
    print(f"Error importing from official SafeMERGE repo: {e}")
    print(f"Make sure get_safemerge_model.py is in {third_party_dir}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Wrapper for official SafeMERGE")
    parser.add_argument("--base_model_id", type=str, required=True, help="Base model ID")
    parser.add_argument("--finetuned_model_id", type=str, required=True, help="Utility finetuned model (LoRA)")
    parser.add_argument("--safety_model_id", type=str, required=True, help="Safety finetuned model (LoRA)")
    parser.add_argument("--safelora_unaligned_model_id", type=str, required=True, help="Unaligned model for projection")
    parser.add_argument("--safelora_aligned_model_id", type=str, required=True, help="Aligned model for projection")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory to save merged LoRA")
    
    # 公式コードが他に引数を取る可能性があるため、parse_known_args を使用
    args, unknown = parser.parse_known_args()

    # 自動検証フックの呼び出し (一括チェック)
    steering_hook.verify_experiment_config(args)
    
    print("=== Running Official SafeMERGE ===")
    print(f"Base Model: {args.base_model_id}")
    print(f"Finetuned (Utility) LoRA: {args.finetuned_model_id}")
    print(f"Safety LoRA: {args.safety_model_id}")
    print(f"Unaligned Model: {args.safelora_unaligned_model_id}")
    print(f"Aligned Model: {args.safelora_aligned_model_id}")
    
    # 公式の関数を呼び出し
    merged_model = get_safemerge(args)
    
    print(f"=== Saving Merged Model to {args.output_dir} ===")
    os.makedirs(args.output_dir, exist_ok=True)
    merged_model.save_pretrained(args.output_dir)
    print("Done.")

if __name__ == "__main__":
    main()
