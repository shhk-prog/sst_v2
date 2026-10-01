"""
Mergers module for Secure Merge v4
"""

from mergers.base_merger import BaseMerger
from mergers.linear_patch import LinearPatchMerger
from mergers.task_arithmetic import TaskArithmeticMerger
from mergers.ties_merger import TIESMerger
from mergers.dare_merger import DAREMerger
from mergers.della_merger import DELLAMerger
from mergers.fisher_merger import FisherMerger
from mergers.safemerge import SafeMergeMerger
from mergers.led_merger import LEDMerger
from mergers.mergealign import MergeAlignMerger
from mergers.proposed_intervention_merge import ProposedInterventionMerger

MERGER_REGISTRY = {
    "linear": LinearPatchMerger,
    "linear_safety_patch": LinearPatchMerger,
    "task_arithmetic": TaskArithmeticMerger,
    "ties": TIESMerger,
    "dare": DAREMerger,
    "della": DELLAMerger,
    "fisher": FisherMerger,
    "fisher_weighted": FisherMerger,
    "safemerge": SafeMergeMerger,
    "led": LEDMerger,
    "led_merging": LEDMerger,
    "mergealign": MergeAlignMerger,
    "proposed": ProposedInterventionMerger,
    "proposed_intervention_merge": ProposedInterventionMerger,
}


def get_merger(name: str, **kwargs) -> BaseMerger:
    key = name.lower()
    if key not in MERGER_REGISTRY:
        raise ValueError(f"Unknown merger '{name}'. Available: {list(MERGER_REGISTRY.keys())}")
    return MERGER_REGISTRY[key](**kwargs)
