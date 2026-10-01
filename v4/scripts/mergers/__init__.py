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


import inspect

def get_merger(name: str, **kwargs) -> BaseMerger:
    key = name.lower()
    if key not in MERGER_REGISTRY:
        raise ValueError(f"Unknown merger '{name}'. Available: {list(MERGER_REGISTRY.keys())}")
    cls = MERGER_REGISTRY[key]
    sig = inspect.signature(cls.__init__)
    # Filter kwargs to only those accepted by cls.__init__ (or all if **kwargs is present)
    has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    if has_var_keyword:
        filtered = kwargs
    else:
        accepted = set(sig.parameters.keys())
        filtered = {k: v for k, v in kwargs.items() if k in accepted}
    return cls(**filtered)
