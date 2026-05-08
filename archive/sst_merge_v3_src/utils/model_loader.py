"""
モデルロードとLoRA管理モジュール

Mistral-7B、Llama-3.1-8B-Instruct、Qwen2.5-14B-Instructをサポート。
H100 4枚での分散実行に対応。

使用方法:
    from src.utils.model_loader import ModelLoader
    
    loader = ModelLoader(model_name="mistralai/Mistral-7B-v0.1", device_map="auto")
    model, tokenizer = loader.load_model()
"""

import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, LoraConfig, get_peft_model
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# .envファイルから環境変数を読み込み
try:
    from dotenv import load_dotenv
    # 親ディレクトリの.envを検索
    env_paths = [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",  # src/.env
        Path(__file__).parent.parent.parent / ".env",  # SST_merge2/.env
        Path(__file__).parent.parent.parent.parent / ".env",  # src/.env (workspace root)
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

# Hugging Face認証（gatedモデル用）
hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
if hf_token:
    try:
        from huggingface_hub import login
        login(token=hf_token, add_to_git_credential=False)
    except Exception:
        pass

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    モデルロードとLoRA管理
    
    サポートモデル:
    - Mistral-7B-v0.1
    - Llama-3.1-8B-Instruct
    - Qwen2.5-14B-Instruct
    
    Args:
        model_name: モデル名またはパス
        device_map: デバイスマッピング（"auto"で自動分散）
        torch_dtype: データ型（デフォルト: bfloat16）
        use_flash_attention: Flash Attention 2を使用するか
    """
    
    # サポートされているモデルの設定
    SUPPORTED_MODELS = {
        "mistral-7b": "mistralai/Mistral-7B-v0.1",
        "mistral-7b-v0.2": "mistralai/Mistral-7B-Instruct-v0.2",
        "llama-3.1-8b": "meta-llama/Llama-3.1-8B-Instruct",
        "qwen-2.5-14b": "Qwen/Qwen2.5-14B-Instruct",
    }
    
    def __init__(
        self,
        model_name: str,
        device_map: str = "auto",
        torch_dtype: torch.dtype = torch.bfloat16,
        use_flash_attention: bool = True,
        load_in_8bit: bool = False,
        load_in_4bit: bool = False
    ):
        # モデル名のエイリアス解決
        if model_name in self.SUPPORTED_MODELS:
            self.model_name = self.SUPPORTED_MODELS[model_name]
        else:
            self.model_name = model_name
        
        self.device_map = device_map
        self.torch_dtype = torch_dtype
        self.use_flash_attention = use_flash_attention
        self.load_in_8bit = load_in_8bit
        self.load_in_4bit = load_in_4bit
        
        logger.info(
            f"ModelLoader initialized: model={self.model_name}, "
            f"device_map={device_map}, dtype={torch_dtype}"
        )
    
    def load_model(self) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        モデルとトークナイザーをロード
        
        Returns:
            model: ロードされたモデル
            tokenizer: トークナイザー
        """
        logger.info(f"Loading model: {self.model_name}")
        
        # トークナイザーのロード
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        
        # パディングトークンの設定
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # モデルのロード設定
        model_kwargs = {
            "device_map": self.device_map,
            "torch_dtype": self.torch_dtype,
            "trust_remote_code": True,
        }
        
        # Flash Attention 2の設定
        if self.use_flash_attention:
            try:
                model_kwargs["attn_implementation"] = "flash_attention_2"
                logger.info("Using Flash Attention 2 for faster inference")
            except Exception as e:
                logger.warning(
                    f"Flash Attention 2 is not available: {e}. "
                    "Falling back to standard attention. "
                    "To install: pip install flash-attn --no-build-isolation"
                )
                self.use_flash_attention = False
        
        # 量子化の設定
        if self.load_in_8bit:
            model_kwargs["load_in_8bit"] = True
        elif self.load_in_4bit:
            model_kwargs["load_in_4bit"] = True
        
        # モデルのロード
        try:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            logger.info(f"✓ Model loaded successfully: {self.model_name}")
            
            # モデル情報を表示
            num_params = sum(p.numel() for p in model.parameters())
            logger.info(f"  Total parameters: {num_params / 1e9:.2f}B")
            logger.info(f"  Device map: {model.hf_device_map if hasattr(model, 'hf_device_map') else 'N/A'}")
            
        except Exception as e:
            logger.error(f"✗ Failed to load model: {e}")
            raise
        
        return model, tokenizer
    
    @staticmethod
    def _get_default_target_modules(model: AutoModelForCausalLM) -> List[str]:
        """
        モデルタイプに応じたデフォルトのtarget_modulesを取得
        
        Args:
            model: ベースモデル
            
        Returns:
            target_modules: ターゲットモジュールのリスト
        """
        # モデルの全モジュール名を取得
        module_names = set()
        for name, _ in model.named_modules():
            if '.' in name:
                module_names.add(name.split('.')[-1])
        
        # GPT2系モデル
        if 'c_attn' in module_names:
            return ["c_attn", "c_proj"]
        
        # Llama/Mistral/Qwen系モデル
        elif 'q_proj' in module_names:
            return ["q_proj", "v_proj", "k_proj", "o_proj"]
        
        # その他のモデル（デフォルト）
        else:
            logger.warning(f"Unknown model architecture. Using default target modules.")
            return ["q_proj", "v_proj", "k_proj", "o_proj"]
    
    def create_lora_adapter(
        self,
        model: AutoModelForCausalLM,
        lora_config: Optional[LoraConfig] = None,
        target_modules: Optional[List[str]] = None
    ) -> PeftModel:
        """
        LoRAアダプタを作成
        
        Args:
            model: ベースモデル
            lora_config: LoRA設定(Noneの場合はデフォルト)
            target_modules: ターゲットモジュール(Noneの場合は自動検出)
            
        Returns:
            peft_model: LoRAアダプタ付きモデル
        """
        if lora_config is None:
            # target_modulesが指定されていない場合は自動検出
            if target_modules is None:
                target_modules = self._get_default_target_modules(model)
                logger.info(f"Auto-detected target modules: {target_modules}")
            
            # デフォルトのLoRA設定
            lora_config = LoraConfig(
                r=16,
                lora_alpha=32,
                target_modules=target_modules,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM"
            )
        
        logger.info(f"Creating LoRA adapter: r={lora_config.r}, alpha={lora_config.lora_alpha}")
        
        peft_model = get_peft_model(model, lora_config)
        
        # 学習可能パラメータ数を表示
        trainable_params = sum(p.numel() for p in peft_model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in peft_model.parameters())
        
        logger.info(f"  Trainable parameters: {trainable_params / 1e6:.2f}M ({100 * trainable_params / total_params:.2f}%)")
        
        return peft_model
    
    def load_lora_adapter(
        self,
        model: AutoModelForCausalLM,
        adapter_path: str
    ) -> PeftModel:
        """
        既存のLoRAアダプタをロード
        
        Args:
            model: ベースモデル
            adapter_path: アダプタのパス
            
        Returns:
            peft_model: LoRAアダプタ付きモデル
        """
        logger.info(f"Loading LoRA adapter from: {adapter_path}")
        
        try:
            peft_model = PeftModel.from_pretrained(model, adapter_path)
            logger.info(f"✓ LoRA adapter loaded successfully")
            return peft_model
        except Exception as e:
            logger.error(f"✗ Failed to load LoRA adapter: {e}")
            raise
    
    def save_lora_adapter(
        self,
        peft_model: PeftModel,
        output_path: str
    ):
        """
        LoRAアダプタを保存
        
        Args:
            peft_model: LoRAアダプタ付きモデル
            output_path: 保存先パス
        """
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving LoRA adapter to: {output_path}")
        
        try:
            peft_model.save_pretrained(output_path)
            logger.info(f"✓ LoRA adapter saved successfully")
        except Exception as e:
            logger.error(f"✗ Failed to save LoRA adapter: {e}")
            raise
    
    def load_lora_from_directory(
        self,
        model: AutoModelForCausalLM,
        adapter_dir: str
    ) -> PeftModel:
        """
        ダウンロード済みのLoRAアダプタをロード（Phase 2実装）
        
        Args:
            model: ベースモデル
            adapter_dir: アダプタディレクトリ（例: lora_adapters/mistral-7b/safety）
            
        Returns:
            peft_model: LoRAアダプタ付きモデル
        """
        adapter_path = Path(adapter_dir)
        
        if not adapter_path.exists():
            raise FileNotFoundError(f"Adapter directory not found: {adapter_dir}")
        
        logger.info(f"Loading LoRA from directory: {adapter_dir}")
        
        try:
            # メタデータを確認
            metadata_file = adapter_path / 'metadata.json'
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"  Adapter type: {metadata.get('adapter_type', 'unknown')}")
                logger.info(f"  Description: {metadata.get('description', 'N/A')}")
            
            # LoRAアダプタをロード
            peft_model = PeftModel.from_pretrained(model, str(adapter_path))
            logger.info(f"✓ LoRA loaded successfully from {adapter_dir}")
            
            return peft_model
            
        except Exception as e:
            logger.error(f"✗ Failed to load LoRA from directory: {e}")
            raise
    
    def extract_lora_parameters(
        self,
        peft_model: PeftModel
    ) -> Dict[str, torch.Tensor]:
        """
        LoRAパラメータを抽出（Phase 3実装）
        
        Args:
            peft_model: LoRAアダプタ付きモデル
            
        Returns:
            lora_params: LoRAパラメータの辞書
        """
        logger.info("Extracting LoRA parameters...")
        
        lora_params = {}
        
        for name, param in peft_model.named_parameters():
            if 'lora' in name.lower():
                lora_params[name] = param.detach().clone()
        
        logger.info(f"  Extracted {len(lora_params)} LoRA parameters")
        
        # パラメータサイズの計算
        total_params = sum(p.numel() for p in lora_params.values())
        logger.info(f"  Total LoRA parameters: {total_params / 1e6:.2f}M")
        
        return lora_params
    
    def load_multiple_loras(
        self,
        model: AutoModelForCausalLM,
        adapter_dirs: List[str]
    ) -> List[Dict[str, torch.Tensor]]:
        """
        複数のLoRAアダプタをロードしてパラメータを抽出
        
        Args:
            model: ベースモデル
            adapter_dirs: アダプタディレクトリのリスト
            
        Returns:
            lora_params_list: LoRAパラメータのリスト
        """
        logger.info(f"Loading {len(adapter_dirs)} LoRA adapters...")
        
        lora_params_list = []
        
        for i, adapter_dir in enumerate(adapter_dirs):
            logger.info(f"\nLoading adapter {i+1}/{len(adapter_dirs)}")
            
            # LoRAをロード
            peft_model = self.load_lora_from_directory(model, adapter_dir)
            
            # パラメータを抽出
            lora_params = self.extract_lora_parameters(peft_model)
            lora_params_list.append(lora_params)
            
            # メモリ解放
            del peft_model
            torch.cuda.empty_cache()
        
        logger.info(f"\n✓ All {len(adapter_dirs)} LoRA adapters loaded and extracted")
        
        return lora_params_list
    
    @staticmethod
    def get_model_info(model_name: str) -> Dict[str, any]:
        """
        モデル情報を取得
        
        Args:
            model_name: モデル名
            
        Returns:
            info: モデル情報
        """
        info = {
            "mistral-7b": {
                "full_name": "mistralai/Mistral-7B-v0.1",
                "parameters": "7B",
                "context_length": 8192,
                "recommended_vram": "16GB",
            },
            "llama-3.1-8b": {
                "full_name": "meta-llama/Llama-3.1-8B-Instruct",
                "parameters": "8B",
                "context_length": 8192,
                "recommended_vram": "18GB",
            },
            "qwen-2.5-14b": {
                "full_name": "Qwen/Qwen2.5-14B-Instruct",
                "parameters": "14B",
                "context_length": 32768,
                "recommended_vram": "32GB",
            }
        }
        
        return info.get(model_name, {})


def test_model_loader():
    """ModelLoaderの簡易テスト"""
    logger.info("Testing ModelLoader...")
    
    # 小規模モデルでテスト（GPT-2）
    loader = ModelLoader(
        model_name="gpt2",
        device_map="auto",
        torch_dtype=torch.float32
    )
    
    model, tokenizer = loader.load_model()
    
    # テスト入力
    text = "Hello, world!"
    inputs = tokenizer(text, return_tensors="pt")
    
    logger.info(f"Test input: {text}")
    logger.info(f"Input IDs shape: {inputs['input_ids'].shape}")
    
    # LoRAアダプタの作成
    peft_model = loader.create_lora_adapter(model)
    
    logger.info("ModelLoader test completed successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_model_loader()
