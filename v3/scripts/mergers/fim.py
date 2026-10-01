import os
import json
from datetime import datetime
import torch
from tqdm import tqdm

from mergers.utils import is_target_weight, get_model_short_name, write_json


def estimate_fim(model, dataset_path, sample_size, tokenizer, device):
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"FIM dataset not found: {dataset_path}")

    model.eval()
    fim = {}
    target_params = []

    for name, param in model.named_parameters():
        if is_target_weight(name):
            target_params.append((name, param))
            fim[name] = torch.zeros_like(param.detach(), dtype=torch.float32, device="cpu")

    if not target_params:
        raise RuntimeError("No target parameters found for FIM estimation.")

    print(f"Reading FIM dataset from {dataset_path}...")

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = data[:sample_size]

    if not data:
        raise ValueError(f"No FIM samples loaded from {dataset_path}")

    for _, param in target_params:
        param.requires_grad = True

    count = 0

    for item in tqdm(data, desc="Estimating FIM"):
        if "prompt" not in item or "response" not in item:
            continue

        text = f"<s>[INST] {item['prompt']} [/INST] {item['response']}</s>"

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        ).to(device)

        labels = inputs["input_ids"].clone()
        loss = model(**inputs, labels=labels).loss
        loss.backward()

        with torch.no_grad():
            for name, param in target_params:
                if param.grad is not None:
                    fim[name] += param.grad.detach().float().cpu() ** 2

        model.zero_grad(set_to_none=True)
        count += 1

    if count == 0:
        raise ValueError(f"No valid FIM samples processed from {dataset_path}")

    for name in fim:
        fim[name] /= count

    return fim


def build_fim_cache_path(args, config, kind, domain, model_path, sample_size):
    os.makedirs(args.fim_cache_dir, exist_ok=True)

    model_short = get_model_short_name(
        kind=kind,
        domain=domain,
        model_path=model_path,
        config=config,
    )

    domain_part = domain if domain is not None else "all"

    filename = (
        f"{kind}_{domain_part}_{model_short}"
        f"_n{sample_size}_seed{args.seed}.pt"
    )

    return os.path.join(args.fim_cache_dir, filename)


def load_or_estimate_fim(
    model,
    dataset_path,
    sample_size,
    tokenizer,
    device,
    args,
    config,
    kind,
    domain,
    model_path=None,
):
    cache_path = build_fim_cache_path(
        args=args,
        config=config,
        kind=kind,
        domain=domain,
        model_path=model_path,
        sample_size=sample_size,
    )

    meta_path = cache_path.replace(".pt", ".json")

    use_cache = not args.no_fim_cache

    if use_cache and not args.overwrite_fim_cache and os.path.exists(cache_path):
        print(f"Loading cached FIM: {cache_path}")
        return torch.load(cache_path, map_location="cpu", weights_only=False)

    print(f"Estimating FIM: kind={kind}, domain={domain}, n={sample_size}, seed={args.seed}")
    print(f"FIM cache will be saved to: {cache_path}")

    fim = estimate_fim(
        model=model,
        dataset_path=dataset_path,
        sample_size=sample_size,
        tokenizer=tokenizer,
        device=device,
    )

    if use_cache:
        tmp_path = cache_path + ".tmp"
        torch.save(fim, tmp_path)
        os.replace(tmp_path, cache_path)

        metadata = {
            "kind": kind,
            "domain": domain,
            "model_path": model_path,
            "dataset_path": dataset_path,
            "sample_size": sample_size,
            "seed": args.seed,
            "cache_path": cache_path,
            "timestamp": datetime.now().isoformat(),
        }
        write_json(meta_path, metadata)

        print(f"Saved FIM cache: {cache_path}")
        print(f"Saved FIM metadata: {meta_path}")

    return fim


def get_fim_tensor(fim, name, like_tensor):
    if fim is None or name not in fim:
        return torch.zeros_like(like_tensor)
    return fim[name].to(device=like_tensor.device, dtype=like_tensor.dtype)
