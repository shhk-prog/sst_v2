"""
環境設定モジュール

親ディレクトリ（src/.env）から環境変数を読み込みます。
このファイルを他のスクリプトからインポートして使用してください。

使用例:
    from src.utils.env_setup import setup_env
    setup_env()
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def setup_env():
    """
    src/.envから環境変数を読み込む
    
    プロジェクトの親ディレクトリ（src/）にある.envファイルを読み込み、
    環境変数として設定します。
    """
    # SST_merge/src/utils/env_setup.py -> SST_merge -> src
    env_path = Path(__file__).resolve().parent.parent.parent.parent / '.env'
    
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️ Environment file not found: {env_path}")
        print("   Please create src/.env with required API keys.")
    
    # 必須の環境変数をチェック
    required_vars = ['HUGGINGFACE_TOKEN', 'HF_TOKEN']
    found_hf = any(os.getenv(var) for var in required_vars)
    
    if not found_hf:
        print("⚠️ Warning: HUGGINGFACE_TOKEN/HF_TOKEN not set")
    
    return found_hf


def get_hf_token():
    """HuggingFace tokenを取得"""
    return os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")


def get_openai_key():
    """OpenAI API keyを取得"""
    return os.getenv("OPENAI_API_KEY")


def get_wandb_key():
    """WandB API keyを取得"""
    return os.getenv("WANDB_API_KEY")


# モジュールインポート時に自動的に環境設定を読み込む
setup_env()
