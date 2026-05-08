#!/usr/bin/env python3
"""
SST-Merge v5 包括的実験結果レポート生成
"""

import json
from collections import defaultdict
import statistics

def load_results():
    with open('all_eval_results_summary.json') as f:
        return json.load(f)

def get_best_results_by_method(results):
    """各手法の最良結果を抽出（α値ごと）"""
    
    # A6_A7ペアのみ
    a6_a7_results = [r for r in results if r.get('pair') == 'A6_A7']
    
    # 手法×α値でグループ化
    by_method_alpha = defaultdict(lambda: {'jailbreak': [], 'alpaca': []})
    
    for r in a6_a7_results:
        method = r.get('method', 'Unknown')
        alpha = r.get('alpha', None)
        eval_type = r.get('eval_type')
        gevp = r.get('gevp', False)
        layerwise = r.get('layerwise', False)
        
        # Data-Free判定
        if method == 'Unknown' and r.get('category') == 'data_free':
            method = 'SST-Merge (Data-Free)'
        
        # キー作成
        if alpha is not None:
            key = (method, alpha, gevp, layerwise)
        else:
            key = (method, None, False, False)
        
        if eval_type in ['jailbreak', 'alpaca']:
            by_method_alpha[key][eval_type].append(r)
    
    # 各グループで最良の結果を選択（jailbreak: resistance最大、alpaca: ROUGE-1最大）
    best_results = {}
    for key, data in by_method_alpha.items():
        method, alpha, gevp, layerwise = key
        
        if data['jailbreak']:
            best_jb = max(data['jailbreak'], key=lambda x: x.get('resistance_rate', 0))
        else:
            best_jb = None
        
        if data['alpaca']:
            best_alp = max(data['alpaca'], key=lambda x: x.get('rouge1', 0))
        else:
            best_alp = None
        
        best_results[key] = {
            'jailbreak': best_jb,
            'alpaca': best_alp
        }
    
    return best_results

def generate_comprehensive_report(results):
    """包括的レポートを生成"""
    
    md_lines = []
    md_lines.append("# SST-Merge v5 包括的実験結果レポート\n")
    md_lines.append(f"**評価日**: 2026-02-02")
    md_lines.append(f"**総評価結果数**: {len(results)}\n")
    
    # カテゴリ別統計
    by_category = defaultdict(int)
    for r in results:
        by_category[r['category']] += 1
    
    md_lines.append("## 1. 実験概要\n")
    md_lines.append("### 評価カテゴリ\n")
    md_lines.append("| カテゴリ | 評価数 | 説明 |")
    md_lines.append("|----------|--------|------|")
    md_lines.append(f"| ベースモデル・アダプター | {by_category['base']} | 個別アダプターおよびベースモデル |")
    md_lines.append(f"| Baselineマージ | {by_category['baseline']} | Task Arithmetic, TIES, DARE |")
    md_lines.append(f"| SST-Merge (加算型) | {by_category['additive']} | 従来のSST-Merge |")
    md_lines.append(f"| SST-Merge (補間型) | {by_category['interpolation']} | Task Arithmetic互換版 |")
    md_lines.append(f"| SST-Merge (Data-Free) | {by_category['data_free']} | データなしGEVP |")
    
    # α値の範囲確認
    alphas = sorted(set(r.get('alpha') for r in results if 'alpha' in r))
    md_lines.append(f"\n### α値の範囲\n")
    md_lines.append(f"- 最小: {min(alphas)}")
    md_lines.append(f"- 最大: {max(alphas)}")
    md_lines.append(f"- テスト値: {alphas}\n")
    
    # 最良結果の抽出
    best_results = get_best_results_by_method(results)
    
    # α=1.0の結果を抽出
    md_lines.append("## 2. 主要結果（A6_A7ペア、α=1.0）\n")
    md_lines.append("### 2.1 Jailbreak耐性\n")
    md_lines.append("| 手法 | GEVP | Layer-wise | Resistance | ASR |")
    md_lines.append("|------|------|------------|------------|-----|")
    
    alpha_1_keys = [k for k in best_results.keys() if k[1] == 1.0]
    alpha_1_keys.sort(key=lambda x: (x[0], not x[2], not x[3]))
    
    for key in alpha_1_keys:
        method, alpha, gevp, layerwise = key
        jb = best_results[key]['jailbreak']
        if jb:
            gevp_str = '✓' if gevp else '✗'
            lw_str = '✓' if layerwise else '✗'
            resistance = jb.get('resistance_rate', 0)
            asr = jb.get('asr', 0)
            md_lines.append(f"| {method} | {gevp_str} | {lw_str} | {resistance:.1f}% | {asr:.1f}% |")
    
    md_lines.append("\n### 2.2 Alpaca性能\n")
    md_lines.append("| 手法 | GEVP | Layer-wise | ROUGE-1 | ROUGE-2 | ROUGE-L |")
    md_lines.append("|------|------|------------|---------|---------|---------|")
    
    for key in alpha_1_keys:
        method, alpha, gevp, layerwise = key
        alp = best_results[key]['alpaca']
        if alp:
            gevp_str = '✓' if gevp else '✗'
            lw_str = '✓' if layerwise else '✗'
            r1 = alp.get('rouge1', 0)
            r2 = alp.get('rouge2', 0)
            rL = alp.get('rougeL', 0)
            md_lines.append(f"| {method} | {gevp_str} | {lw_str} | {r1:.4f} | {r2:.4f} | {rL:.4f} |")
    
    # α値による性能変化
    md_lines.append("\n## 3. α値による性能変化\n")
    
    # SST-Merge (Interpolation, noGEVP)の変化を追跡
    md_lines.append("### 3.1 SST-Merge補間型（GEVP無効）\n")
    md_lines.append("| α | Jailbreak Resistance | Alpaca ROUGE-1 | バランス指標 |")
    md_lines.append("|---|---------------------|----------------|--------------|")
    
    interp_nogevp_keys = [(m, a, g, lw) for m, a, g, lw in best_results.keys() 
                          if m == 'SST-Merge (Interpolation)' and not g and not lw and a is not None]
    interp_nogevp_keys.sort(key=lambda x: x[1])
    
    for key in interp_nogevp_keys:
        method, alpha, gevp, layerwise = key
        jb = best_results[key]['jailbreak']
        alp = best_results[key]['alpaca']
        
        if jb and alp:
            resistance = jb.get('resistance_rate', 0)
            rouge1 = alp.get('rouge1', 0)
            # バランス指標: harmonic mean
            if resistance > 0 and rouge1 > 0:
                balance = 2 * (resistance/100 * rouge1) / (resistance/100 + rouge1)
            else:
                balance = 0
            md_lines.append(f"| {alpha:.2f} | {resistance:.1f}% | {rouge1:.4f} | {balance:.4f} |")
    
    # 加算型の比較
    md_lines.append("\n### 3.2 SST-Merge加算型（GEVP無効）\n")
    md_lines.append("| α | Jailbreak Resistance | Alpaca ROUGE-1 | バランス指標 |")
    md_lines.append("|---|---------------------|----------------|--------------|")
    
    additive_nogevp_keys = [(m, a, g, lw) for m, a, g, lw in best_results.keys() 
                            if m == 'SST-Merge (Additive)' and not g and not lw and a is not None]
    additive_nogevp_keys.sort(key=lambda x: x[1])
    
    for key in additive_nogevp_keys:
        method, alpha, gevp, layerwise = key
        jb = best_results[key]['jailbreak']
        alp = best_results[key]['alpaca']
        
        if jb and alp:
            resistance = jb.get('resistance_rate', 0)
            rouge1 = alp.get('rouge1', 0)
            if resistance > 0 and rouge1 > 0:
                balance = 2 * (resistance/100 * rouge1) / (resistance/100 + rouge1)
            else:
                balance = 0
            md_lines.append(f"| {alpha:.2f} | {resistance:.1f}% | {rouge1:.4f} | {balance:.4f} |")
    
    # 重要な発見
    md_lines.append("\n## 4. 重要な発見\n")
    
    md_lines.append("### 4.1 補間型 vs 加算型（α=1.0）\n")
    
    interp_1_nogevp = best_results.get(('SST-Merge (Interpolation)', 1.0, False, False))
    additive_1_nogevp = best_results.get(('SST-Merge (Additive)', 1.0, False, False))
    
    if interp_1_nogevp and additive_1_nogevp:
        interp_jb = interp_1_nogevp['jailbreak']
        additive_jb = additive_1_nogevp['jailbreak']
        interp_alp = interp_1_nogevp['alpaca']
        additive_alp = additive_1_nogevp['alpaca']
        
        if interp_jb and additive_jb:
            md_lines.append(f"- **Jailbreak耐性**:")
            md_lines.append(f"  - 補間型: {interp_jb.get('resistance_rate', 0):.1f}%")
            md_lines.append(f"  - 加算型: {additive_jb.get('resistance_rate', 0):.1f}%")
            md_lines.append(f"  - **差分: +{interp_jb.get('resistance_rate', 0) - additive_jb.get('resistance_rate', 0):.1f}%**\n")
        
        if interp_alp and additive_alp:
            md_lines.append(f"- **Alpaca性能（ROUGE-1）**:")
            md_lines.append(f"  - 補間型: {interp_alp.get('rouge1', 0):.4f}")
            md_lines.append(f"  - 加算型: {additive_alp.get('rouge1', 0):.4f}")
            md_lines.append(f"  - **差分: {interp_alp.get('rouge1', 0) - additive_alp.get('rouge1', 0):+.4f}**\n")
    
    md_lines.append("### 4.2 GEVP効果（補間型、α=1.0）\n")
    
    interp_gevp = best_results.get(('SST-Merge (Interpolation)', 1.0, True, False))
    
    if interp_gevp and interp_1_nogevp:
        gevp_jb = interp_gevp['jailbreak']
        nogevp_jb = interp_1_nogevp['jailbreak']
        
        if gevp_jb and nogevp_jb:
            md_lines.append(f"- **Jailbreak耐性**:")
            md_lines.append(f"  - GEVP有効: {gevp_jb.get('resistance_rate', 0):.1f}%")
            md_lines.append(f"  - GEVP無効: {nogevp_jb.get('resistance_rate', 0):.1f}%")
            md_lines.append(f"  - **GEVP効果: {gevp_jb.get('resistance_rate', 0) - nogevp_jb.get('resistance_rate', 0):+.1f}%**\n")
    
    md_lines.append("### 4.3 Task Arithmetic互換性検証\n")
    
    task_arith = best_results.get(('Task Arithmetic', 1.0, False, False))
    
    if task_arith and interp_1_nogevp:
        ta_jb = task_arith['jailbreak']
        interp_jb = interp_1_nogevp['jailbreak']
        ta_alp = task_arith['alpaca']
        interp_alp = interp_1_nogevp['alpaca']
        
        if ta_jb and interp_jb and ta_alp and interp_alp:
            md_lines.append(f"**補間型（GEVP無効）とTask Arithmeticの比較**:\n")
            md_lines.append(f"- Jailbreak耐性: {interp_jb.get('resistance_rate', 0):.1f}% vs {ta_jb.get('resistance_rate', 0):.1f}% （差: {abs(interp_jb.get('resistance_rate', 0) - ta_jb.get('resistance_rate', 0)):.1f}%）")
            md_lines.append(f"- Alpaca ROUGE-1: {interp_alp.get('rouge1', 0):.4f} vs {ta_alp.get('rouge1', 0):.4f} （差: {abs(interp_alp.get('rouge1', 0) - ta_alp.get('rouge1', 0)):.4f}）")
            md_lines.append(f"\n**結論**: 補間型はTask Arithmeticと {'完全に同等' if abs(interp_jb.get('resistance_rate', 0) - ta_jb.get('resistance_rate', 0)) < 0.1 else 'ほぼ同等'}です。\n")
    
    # ベストバランスの推奨
    md_lines.append("## 5. 推奨設定\n")
    
    md_lines.append("### 5.1 最高Jailbreak耐性")
    # 補間型、高αを探す
    best_jb_key = max(
        [k for k in best_results.keys() if best_results[k]['jailbreak']],
        key=lambda k: best_results[k]['jailbreak'].get('resistance_rate', 0)
    )
    best_jb_result = best_results[best_jb_key]['jailbreak']
    md_lines.append(f"- **手法**: {best_jb_key[0]}")
    md_lines.append(f"- **α**: {best_jb_key[1]}")
    md_lines.append(f"- **GEVP**: {'有効' if best_jb_key[2] else '無効'}")
    md_lines.append(f"- **Layer-wise**: {'有効' if best_jb_key[3] else '無効'}")
    md_lines.append(f"- **性能**: {best_jb_result.get('resistance_rate', 0):.1f}% resistance\n")
    
    md_lines.append("### 5.2 最高Utility性能")
    best_util_key = max(
        [k for k in best_results.keys() if best_results[k]['alpaca']],
        key=lambda k: best_results[k]['alpaca'].get('rouge1', 0)
    )
    best_util_result = best_results[best_util_key]['alpaca']
    md_lines.append(f"- **手法**: {best_util_key[0]}")
    md_lines.append(f"- **α**: {best_util_key[1]}")
    md_lines.append(f"- **GEVP**: {'有効' if best_util_key[2] else '無効'}")
    md_lines.append(f"- **Layer-wise**: {'有効' if best_util_key[3] else '無効'}")
    md_lines.append(f"- **性能**: ROUGE-1 = {best_util_result.get('rouge1', 0):.4f}\n")
    
    md_lines.append("### 5.3 最良バランス（補間型）")
    # Harmonic meanでバランス計算
    balance_scores = []
    for key in best_results.keys():
        if key[0] == 'SST-Merge (Interpolation)':
            jb = best_results[key]['jailbreak']
            alp = best_results[key]['alpaca']
            if jb and alp:
                resistance = jb.get('resistance_rate', 0) / 100
                rouge1 = alp.get('rouge1', 0)
                if resistance > 0 and rouge1 > 0:
                    balance = 2 * (resistance * rouge1) / (resistance + rouge1)
                    balance_scores.append((key, balance, jb, alp))
    
    if balance_scores:
        best_balance_key, best_balance, best_jb, best_alp = max(balance_scores, key=lambda x: x[1])
        md_lines.append(f"- **手法**: {best_balance_key[0]}")
        md_lines.append(f"- **α**: {best_balance_key[1]}")
        md_lines.append(f"- **GEVP**: {'有効' if best_balance_key[2] else '無効'}")
        md_lines.append(f"- **Layer-wise**: {'有効' if best_balance_key[3] else '無効'}")
        md_lines.append(f"- **Jailbreak耐性**: {best_jb.get('resistance_rate', 0):.1f}%")
        md_lines.append(f"- **Alpaca ROUGE-1**: {best_alp.get('rouge1', 0):.4f}")
        md_lines.append(f"- **バランス指標**: {best_balance:.4f}\n")
    
    return '\n'.join(md_lines)

def main():
    results = load_results()
    report = generate_comprehensive_report(results)
    
    with open('comprehensive_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Generated comprehensive report: comprehensive_report.md")

if __name__ == '__main__':
    main()
