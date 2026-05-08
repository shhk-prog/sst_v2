import torch
import numpy as np

def compute_diagonal_fim(model, dataloader, num_samples=100):
    """
    対角Fisher情報行列（FIM）を計算する。
    model: ベースモデルに評価対象のLoRAを適用したモデル
    """
    model.eval()
    fim_diag = {name: torch.zeros_like(param) for name, param in model.named_parameters() if param.requires_grad}
    
    processed = 0
    for batch in dataloader:
        if processed >= num_samples:
            break
            
        model.zero_grad()
        outputs = model(**batch)
        # 次のトークン予測のクロスエントロピーLoss
        loss = outputs.loss
        
        # 勾配計算
        loss.backward()
        
        # 勾配の二乗をFIMの対角成分として累積
        for name, param in model.named_parameters():
            if param.requires_grad and param.grad is not None:
                fim_diag[name] += (param.grad.detach() ** 2)
        
        processed += batch["input_ids"].size(0)
        
    # サンプル数で割って期待値に
    for name in fim_diag:
        fim_diag[name] /= processed
        
    return fim_diag

def compute_sst_ratio(fim_h, fim_b, epsilon=1e-6):
    """
    SST比 (λ_i = F_h,i / F_b,i) を計算する
    """
    sst_ratio = {}
    for name in fim_h:
        if name in fim_b:
            sst_ratio[name] = fim_h[name] / (fim_b[name] + epsilon)
    return sst_ratio

def generate_topk_mask(sst_ratio_dict, k_percent):
    """
    SST比上位 k% のマスクを生成する
    """
    all_values = []
    for name, tensor in sst_ratio_dict.items():
        all_values.append(tensor.flatten())
    
    concatenated = torch.cat(all_values)
    k_index = int(len(concatenated) * (1 - k_percent / 100.0))
    if k_index >= len(concatenated):
        k_index = len(concatenated) - 1
        
    threshold = torch.kthvalue(concatenated, k_index).values.item()
    
    mask_dict = {}
    for name, tensor in sst_ratio_dict.items():
        mask_dict[name] = (tensor >= threshold).float()
        
    return mask_dict

def apply_sst_merge(base_model, theta_util, theta_safe, mask, alpha, method="interpolation"):
    """
    補間型または加算型でSST-Mergeを適用する。
    """
    merged_state_dict = {}
    for name in theta_util:
        if name in theta_safe and name in base_model and name in mask:
            delta_s = theta_safe[name] - base_model[name]
            
            if method == "interpolation":
                merged_state_dict[name] = theta_util[name] + alpha * (mask[name] * delta_s)
            elif method == "additive":
                masked_delta = mask[name] * delta_s
                norm = torch.norm(masked_delta)
                if norm > 0:
                    merged_state_dict[name] = theta_util[name] + alpha * (masked_delta / norm)
                else:
                    merged_state_dict[name] = theta_util[name]
        else:
            merged_state_dict[name] = theta_util[name]
            
    return merged_state_dict
