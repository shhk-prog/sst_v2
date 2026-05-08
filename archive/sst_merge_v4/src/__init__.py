"""
SST-Merge V4: Complete Pipeline for Safety-Utility Trade-off Optimization

Components:
- data_loader: RepliQA, Jailbreak datasets
- lora_trainer: LoRA Fine-Tuning for A5 (Utility) and A7 (Safety)
- sst_merge_v4: SST-Merge implementation with GEVP
- baseline_merge: TIES, DARE, Task Arithmetic via mergekit
- evaluator: Jailbreak resistance and Utility evaluation
"""

from .data_loader import DataLoaderFactory
from .lora_trainer import LoRATrainerV4
from .sst_merge_v4 import SSTMergeV4
from .baseline_merge import BaselineMerger
from .evaluator import Evaluator

__all__ = [
    'DataLoaderFactory',
    'LoRATrainerV4', 
    'SSTMergeV4',
    'BaselineMerger',
    'Evaluator'
]
