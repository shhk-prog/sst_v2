MERGEKIT_METHODS = ["ties", "dare", "task_arithmetic", "della"]
PROPOSED_METHODS = ["diagonal_sst", "data_free_sst"]
CUSTOM_BASELINES = ["fisher_weighted", "matena_fisher"]
SPECIAL_BASELINES = ["mergealign", "safemerge", "led_merging"]

TARGET_MODULE_KEYWORDS = [
    "q_proj",
    "v_proj",
    "k_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]

MERGEKIT_METHOD_MAP = {
    "ties": "ties",
    "dare": "dare_ties",
    "task_arithmetic": "linear",
    "della": "della",
}

LAYER_PRIOR_CHOICES = [
    "uniform",
    "sin",
    "linear",
    "reverse_linear",
    "exp",
]

FIM_REQUIRED_METHODS = ["diagonal_sst", "fisher_weighted", "matena_fisher"]
