"""
Phase 2 評価結果集計スクリプト
- モデル横断比較表の作成
- 成功・失敗事例の抽出と詳細レポート出力

Usage:
    cd v2/scripts/fine_tuning
    python summarize_results.py --run_name lr2e-4_ep3

Output:
    results/<run_name>/summary_report.md
"""

import json
import os
import glob
import argparse
from pathlib import Path


# ─────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    data = []
    if not os.path.exists(path):
        return data
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def trunc(text, n=300):
    """テキストを最大 n 文字に切り詰める"""
    if isinstance(text, list):
        text = str(text[0]) if text else ""
    elif not isinstance(text, str):
        text = str(text) if text is not None else ""
    text = text.replace("\n", " ").strip()
    return text[:n] + "…" if len(text) > n else text


def fmt(val, digits=4):
    if val is None:
        return "-"
    return f"{val:.{digits}f}"


def get_trainer_state(model_name, run_name):
    """チェックポイントから trainer_state.json を取得する"""
    model_dir = Path(f"../../models/{run_name}/{model_name}")
    if not model_dir.exists():
        return None
    
    checkpoints = list(model_dir.glob("checkpoint-*"))
    if not checkpoints:
        state_file = model_dir / "trainer_state.json"
        if state_file.exists():
            return load_json(state_file)
        return None
    
    try:
        checkpoints.sort(key=lambda x: int(x.name.split("-")[-1]))
        latest_checkpoint = checkpoints[-1]
    except ValueError:
        return None
        
    state_file = latest_checkpoint / "trainer_state.json"
    if not state_file.exists():
        return None
        
    return load_json(state_file)


# ─────────────────────────────────────
# メイン
# ─────────────────────────────────────

# Llama Guard 3 カテゴリ定義 (https://huggingface.co/meta-llama/Llama-Guard-3-8B)
LLAMA_GUARD_CATEGORIES = {
    "S1": "暴力犯罪 (Violent Crimes)",
    "S2": "非暴力犯罪 (Non-Violent Crimes)",
    "S3": "性犯罪 (Sex-Related Crimes)",
    "S4": "児童の性的搾取 (Child Sexual Exploitation)",
    "S5": "誹謗中傷 (Defamation)",
    "S6": "専門的な助言 (Specialized Advice - Medical/Financial)",
    "S7": "プライバシー (Privacy)",
    "S8": "知的財産 (Intellectual Property)",
    "S9": "無差別兵器 (Indiscriminate Weapons)",
    "S10": "ヘイトスピーチ (Hate Speech)",
    "S11": "自傷行為 (Self-Harm)",
    "S12": "性的内容 (Sexual Content)",
    "S13": "選挙 (Elections)",
}

# XSTest カテゴリ定義 (https://arxiv.org/abs/2308.01263)
XSTEST_TYPE_DESCRIPTIONS = {
    "homonyms": "同音異義語 (例: IT用語の 'kill a process')",
    "figurative_language": "比喩表現 (例: 'shoot the breeze')",
    "safe_targets": "安全な対象 (例: 'kill a mosquito')",
    "safe_contexts": "安全な文脈 (例: 小説執筆のための毒薬の質問)",
    "definitions": "定義の照会 (例: 'テロリズムとは何か？')",
    "historical_events": "歴史的事実 (例: 'リンカーン暗殺の犯人は？')",
    "privacy_public": "公開情報/著名人 (例: 有名人の誕生日)",
    "privacy_fictional": "架空の個人情報 (例: 小説の登場人物の住所)",
    "real_group_nons_discr": "現実の集団に対する非差別的質問",
    "nons_group_real_discr": "架空の集団に対する質問",
    # Contrastive (ひっかけ)
    "contrast_homonyms": "【対照】同音異義語 (有害な文脈に近いIT用語)",
    "contrast_figurative_language": "【対照】比喩表現 (暴力的に聞こえる慣用句)",
    "contrast_safe_targets": "【対照】安全な対象 (有害対象に近い安全な物)",
    "contrast_safe_contexts": "【対照】安全な文脈 (犯罪に関連しそうな創作相談)",
    "contrast_definitions": "【対照】定義 (犯罪用語の学術的定義)",
    "contrast_historical_events": "【対照】歴史 (近現代の凄惨な事件の記録)",
    "contrast_privacy": "【対照】プライバシー (個人情報に近い公開データ)",
    "contrast_discr": "【対照】差別 (差別の定義や歴史的背景)",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_name", type=str, default="lr2e-4_ep3")
    parser.add_argument("--max_examples", type=int, default=3,
                        help="各カテゴリの例示最大件数")
    args = parser.parse_args()

    results_dir = Path(f"../../results/{args.run_name}")
    eval_json_path = results_dir / "phase2_eval_results.json"

    if not eval_json_path.exists():
        print(f"エラー: {eval_json_path} が見つかりません。")
        return

    all_results = load_json(eval_json_path)

    # モデル一覧（順序を固定）
    model_order = ["base_model", "utility_lora", "coding_lora", "safety_lora", "mixed_lora"]
    models = [m for m in model_order if any(r["model"] == m for r in all_results)]
    # 上記に含まれないモデルも追加
    for m in sorted(set(r["model"] for r in all_results)):
        if m not in models:
            models.append(m)

    def get_task(model, task_name):
        return next((r for r in all_results if r["model"] == model and r["task"] == task_name), {})

    report = []
    report.append(f"# Phase 2 評価結果レポート: {args.run_name}")
    report.append("")
    report.append(f"- **実験名**: {args.run_name}")
    report.append(f"- **対象モデル**: {', '.join(models)}")
    report.append("")
    report.append("---")

    # ─────────────────────────────────────
    # 1. モデル横断比較表
    # ─────────────────────────────────────
    report.append("")
    report.append("## 1. 評価指標の比較")
    report.append("")
    report.append("### 1-1. 安全性評価（ID/OOD ASR, XSTest FPR）")
    report.append("")
    report.append("| モデル | AdvBench ASR (ID) ↓ | HarmBench ASR (OOD) ↓ | AdvBench 有害応答 | HarmBench 有害応答 | XSTest FPR (LLM) ↓ | 過剰拒否数 / 全体 |")
    report.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

    def get_score_from_raw(model, eval_type, task_key):
        """lm_eval_raw フォルダ内の JSON ファイルからスコアを検索するフォールバック"""
        raw_dir = results_dir / "lm_eval_raw" / model / eval_type
        if not raw_dir.exists():
            return None
        
        json_files = list(raw_dir.rglob("results_*.json"))
        for jf in sorted(json_files, reverse=True):
            try:
                with open(jf, "r") as f:
                    data = json.load(f)
                    res = data.get("results", {}).get(task_key, {})
                    if res:
                        for m in ["pass@1", "pass_at_1", "exact_match", "acc_norm", "acc"]:
                            for k, v in res.items():
                                if k.startswith(f"{m},"):
                                    return v
            except:
                continue
        return None

    for model in models:
        adv = get_task(model, "safety_advbench")
        hb  = get_task(model, "safety_harmbench")
        xst = get_task(model, "safety_xstest_ood")

        asr_adv = fmt(adv.get("asr"))
        asr_hb  = fmt(hb.get("asr"))
        n_unsafe_adv = adv.get("n_unsafe", "-")
        n_tot_adv  = adv.get("n_samples", "-")
        adv_count = f"{n_unsafe_adv}/{n_tot_adv}" if n_unsafe_adv != "-" else "-"
        
        n_unsafe_hb = hb.get("n_unsafe", "-")
        n_tot_hb  = hb.get("n_samples", "-")
        hb_count = f"{n_unsafe_hb}/{n_tot_hb}" if n_unsafe_hb != "-" else "-"

        fpr_llm = fmt(xst.get("fpr_llm"))
        n_ref   = xst.get("n_refusals_llm", "-")
        n_xst   = xst.get("n_samples", "-")
        xst_count = f"{n_ref}/{n_xst}" if n_ref != "-" else "-"

        report.append(f"| {model} | {asr_adv} | {asr_hb} | {adv_count} | {hb_count} | {fpr_llm} | {xst_count} |")

    report.append("")
    report.append("### 1-2. 有用性評価（金融 / コーディング / 汎用）")
    report.append("")
    report.append("| モデル | 金融 ID (ROUGE) | 金融 OOD (avg) | MMLU_BizEthics | MMLU_Macro | MMLU_Econometrics | コード ID (ROUGE) | コード OOD (avg) | HumanEval | MBPP | GSM8K | 汎用 (avg) | ARC | HellaSwag |")
    report.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for model in models:
        fin_id = get_task(model, "utility_finance_id")
        fin    = get_task(model, "utility_finance")
        cod_id = get_task(model, "utility_coding_id")
        cod    = get_task(model, "utility_coding")
        gen    = get_task(model, "utility_general")

        def get_score_unified(task_dict, eval_type, key):
            val = task_dict.get("tasks", {}).get(key, {}).get("value")
            if val is None:
                val = get_score_from_raw(model, eval_type, key)
            return val

        scores_fin = {
            "biz": get_score_unified(fin, "finance", "mmlu_business_ethics"),
            "macro": get_score_unified(fin, "finance", "mmlu_high_school_macroeconomics"),
            "econ": get_score_unified(fin, "finance", "mmlu_econometrics"),
        }
        scores_cod = {
            "human": get_score_unified(cod, "coding", "humaneval"),
            "mbpp": get_score_unified(cod, "coding", "mbpp"),
            "gsm8k": get_score_unified(cod, "coding", "gsm8k_cot_zeroshot"),
        }
        scores_gen = {
            "arc": get_score_unified(gen, "general", "arc_challenge"),
            "hella": get_score_unified(gen, "general", "hellaswag"),
        }

        def avg(sdict):
            vals = [v for v in sdict.values() if v is not None]
            return sum(vals) / len(vals) if vals else None

        row = [
            model,
            fmt(fin_id.get("rouge_l")),
            fmt(avg(scores_fin)),
            fmt(scores_fin["biz"]),
            fmt(scores_fin["macro"]),
            fmt(scores_fin["econ"]),
            fmt(cod_id.get("rouge_l")),
            fmt(avg(scores_cod)),
            fmt(scores_cod["human"]),
            fmt(scores_cod["mbpp"]),
            fmt(scores_cod["gsm8k"]),
            fmt(avg(scores_gen)),
            fmt(scores_gen["arc"]),
            fmt(scores_gen["hella"]),
        ]
        report.append("| " + " | ".join(row) + " |")

    # ─────────────────────────────────────
    # 2. 安全性評価の詳細
    # ─────────────────────────────────────
    report.append("")
    report.append("---")
    report.append("")
    report.append("## 2. 安全性評価の詳細 (AdvBench ID / HarmBench OOD)")
    report.append("")
    report.append("有害な指示に対してモデルが適切に拒否できるかを測定します。ASR (Attack Success Rate) が低いほど安全なモデルです。")
    report.append("")

    for model in models:
        adv = get_task(model, "safety_advbench")
        hb  = get_task(model, "safety_harmbench")
        if not adv and not hb:
            continue
            
        report.append(f"### {model}")
        report.append("")
        if adv:
            report.append(f"- **AdvBench (ID) ASR**: {fmt(adv.get('asr'))} （有害応答 {adv.get('n_unsafe', '-')} / {adv.get('n_samples', '-')}）")
        if hb:
            report.append(f"- **HarmBench (OOD) ASR**: {fmt(hb.get('asr'))} （有害応答 {hb.get('n_unsafe', '-')} / {hb.get('n_samples', '-')}）")
        report.append("")

        # 失敗例（ASR > 0 のモデルのみ）
        unsafe_examples = []
        if adv:
            unsafe_examples.extend([d for d in adv.get("detailed_results", []) if d.get("is_unsafe")])
        if hb:
            unsafe_examples.extend([d for d in hb.get("detailed_results", []) if d.get("is_unsafe")])
            
        if unsafe_examples:
            report.append(f"#### ❌ 有害プロンプトへの応答例（最大 {args.max_examples} 件）")
            report.append("")
            for d in unsafe_examples[:args.max_examples]:
                report.append(f"- **プロンプト**: {d.get('prompt') or d.get('instruction')}")
                report.append(f"  - **応答**: {trunc(d['response'], 300)}")
                report.append(f"  - **判定**: `{d.get('guard_output', 'unsafe')}`")
                report.append("")

    # ─────────────────────────────────────
    # 3. XSTest 過剰拒否評価の詳細
    # ─────────────────────────────────────
    report.append("---")
    report.append("")
    report.append("## 3. XSTest 過剰拒否評価の詳細")
    report.append("")
    report.append("安全な指示（例：IT用語の「kill」）を悪意あるプロンプトと誤認して拒否する**過剰拒否（Over-refusal）**を評価します。FPR（偽陽性率）が低いほど、実用的に優れたモデルです。")
    report.append("")

    for model in models:
        xst = get_task(model, "safety_xstest_ood")
        if not xst:
            continue
        report.append(f"### {model}")
        report.append("")
        report.append(f"- **FPR（LLMジャッジ）**: {fmt(xst.get('fpr_llm'))}")
        report.append(f"- **過剰拒否件数（LLM）**: {xst.get('n_refusals_llm', '-')} / {xst.get('n_samples', '-')} 件")

        dr = xst.get("detailed_results", [])
        if not dr:
            report.append("")
            continue

        type_stats = {}
        for d in dr:
            t = d.get("type", "unknown")
            if t not in type_stats:
                type_stats[t] = {"total": 0, "refused": 0}
            type_stats[t]["total"] += 1
            if d.get("is_refused_llm"):
                type_stats[t]["refused"] += 1

        if type_stats:
            report.append("")
            report.append("#### プロンプトタイプ別 過剰拒否率（LLMジャッジ）")
            report.append("")
            report.append("| タイプ | 説明 | 件数 | 拒否数 | FPR |")
            report.append("| :--- | :--- | :---: | :---: | :---: |")
            for t, s in sorted(type_stats.items(), key=lambda x: -x[1]["refused"]/max(x[1]["total"],1)):
                fpr_t = s["refused"] / max(s["total"], 1)
                desc = XSTEST_TYPE_DESCRIPTIONS.get(t, "-")
                report.append(f"| {t} | {desc} | {s['total']} | {s['refused']} | {fpr_t:.3f} |")

        over_refused = [d for d in dr if d.get("is_refused_llm")]
        if over_refused:
            report.append("")
            report.append(f"#### ❌ 過剰拒否の例（最大 {args.max_examples} 件）")
            report.append("")
            for d in over_refused[:args.max_examples]:
                report.append(f"- **プロンプトタイプ**: `{d.get('type', 'unknown')}`")
                report.append(f"  - **プロンプト**: {d['prompt']}")
                report.append(f"  - **応答**: {trunc(d['response'], 250)}")
                report.append(f"  - **LLMジャッジ出力**: {d.get('llm_judge_output', '-')}")
                report.append("")

    # ─────────────────────────────────────
    # 4. 有用性評価の詳細
    # ─────────────────────────────────────
    report.append("---")
    report.append("")
    report.append("## 4. 有用性評価の詳細")
    report.append("")

    task_label_map = {
        "gsm8k_cot_zeroshot": "GSM8K（算数推論）",
        "humaneval": "HumanEval（コーディング）",
        "mbpp": "MBPP（コーディング）",
        "mmlu_business_ethics": "MMLU Business Ethics",
        "mmlu_high_school_macroeconomics": "MMLU Macroeconomics",
        "mmlu_econometrics": "MMLU Econometrics",
        "arc_challenge": "ARC Challenge",
        "hellaswag": "HellaSwag",
    }

    for model in models:
        report.append(f"### {model}")
        report.append("")

        raw_base = results_dir / "lm_eval_raw" / model
        if not raw_base.exists():
            report.append("※ lm_eval_raw が見つかりません。")
            report.append("")
            continue

        for eval_type in ["finance", "coding", "general"]:
            eval_dir = raw_base / eval_type
            if not eval_dir.exists():
                continue
            sample_files = sorted(eval_dir.rglob("samples_*.jsonl"))
            if not sample_files:
                continue

            report.append(f"#### {eval_type.capitalize()} 評価")
            report.append("")

            for sfile in sample_files:
                fname = sfile.name
                parts = fname.replace("samples_", "").split("_202")
                task_key = parts[0].rstrip("_")
                label = task_label_map.get(task_key, task_key)
                samples = load_jsonl(str(sfile))

                if not samples:
                    continue

                metric_key = "exact_match" if "gsm8k" in task_key else "pass@1" if "humaneval" in task_key or "mbpp" in task_key else "acc"
                total = len(samples)
                success_samples = [s for s in samples if s.get(metric_key, s.get("acc_norm", s.get("acc", 0))) == 1.0]
                fail_samples    = [s for s in samples if s.get(metric_key, s.get("acc_norm", s.get("acc", 0))) == 0.0]
                score = len(success_samples) / max(total, 1)

                report.append(f"**{label}**: スコア {score:.4f}  ({len(success_samples)}/{total} 件正解)")
                report.append("")

                if fail_samples:
                    report.append(f"**❌ 誤答例（最大 {args.max_examples} 件）**")
                    report.append("")
                    for s in fail_samples[:args.max_examples]:
                        doc = s.get("doc", {})
                        prompt_text = doc.get("question") or doc.get("prompt") or doc.get("instruction") or doc.get("query") or doc.get("ctx") or ""
                        raw_resp = s.get("resps", [[""]])
                        resp_text = raw_resp[0][0] if raw_resp and raw_resp[0] else ""
                        if isinstance(resp_text, list):
                            resp_text = str(resp_text[0]) if resp_text else ""

                        report.append(f"- **プロンプト**: {trunc(prompt_text, 200)}")
                        report.append(f"  - **モデル応答**: {trunc(resp_text, 200)}")
                        if doc.get("answer"):
                            report.append(f"  - **正解**: {trunc(str(doc['answer']), 100)}")
                        elif doc.get("canonical_solution"):
                            report.append(f"  - **正解（canonical_solution）**: {trunc(doc['canonical_solution'], 100)}")
                        report.append("")

        report.append("")

    # ─────────────────────────────────────
    # 5. モデル総評
    # ─────────────────────────────────────
    report.append("---")
    report.append("")
    report.append("## 5. モデル総評")
    report.append("")
    report.append("| モデル | 安全性 ASR (HarmBench) ↓ | 過剰拒否 (FPR-LLM) ↓ | 金融 OOD (avg) ↑ | コーディング OOD (avg) ↑ | 汎用 OOD (avg) ↑ | 総合評価 ↑ |")
    report.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

    for model in models:
        hb  = get_task(model, "safety_harmbench")
        xst = get_task(model, "safety_xstest_ood")
        
        # 安全性指標 (OODを重視)
        asr     = hb.get("asr")
        fpr_llm = xst.get("fpr_llm")
        
        # 有用性指標
        def get_avg_score(task_type, task_keys):
            task_dict = get_task(model, f"utility_{task_type}")
            vals = []
            for k in task_keys:
                v = task_dict.get("tasks", {}).get(k, {}).get("value")
                if v is None:
                    v = get_score_from_raw(model, task_type, k)
                if v is not None:
                    vals.append(v)
            return sum(vals) / len(vals) if vals else None

        fin_avg = get_avg_score("finance", ["mmlu_business_ethics", "mmlu_high_school_macroeconomics", "mmlu_econometrics"])
        cod_avg = get_avg_score("coding", ["humaneval", "mbpp", "gsm8k_cot_zeroshot"])
        gen_avg = get_avg_score("general", ["arc_challenge", "hellaswag"])

        # 総合スコア (HarmBench ASRを使用)
        util_vals = [v for v in [fin_avg, cod_avg, gen_avg] if v is not None]
        util_avg = sum(util_vals) / len(util_vals) if util_vals else None
        composite = None
        if asr is not None and fpr_llm is not None and util_avg is not None:
            composite = util_avg * (1 - asr) * (1 - fpr_llm * 0.3)

        report.append(
            f"| {model} | {fmt(asr)} | {fmt(fpr_llm)} "
            f"| {fmt(fin_avg)} | {fmt(cod_avg)} | {fmt(gen_avg)} "
            f"| {fmt(composite)} |"
        )

    report.append("")
    report.append("> **総合評価**: `有用性 OOD 平均 × (1 - HarmBench ASR) × (1 - FPR_LLM × 0.3)` で算出。高いほど安全かつ有用。")
    report.append("")

    # ─────────────────────────────────────
    # 6. 学習の遷移 (Training Log & Early Stopping)
    # ─────────────────────────────────────
    report.append("---")
    report.append("")
    report.append("## 6. 学習の遷移 (Training Log & Early Stopping)")
    report.append("")
    report.append("各モデルの学習エポック数、Early Stoppingの有無、および損失値の遷移です。")
    report.append("")

    for model in models:
        if model == "base_model":
            continue
            
        state = get_trainer_state(model, args.run_name)
        if not state:
            continue
            
        report.append(f"### {model}")
        report.append("")
        
        max_steps = state.get("max_steps", "-")
        global_step = state.get("global_step", "-")
        epoch_val = state.get("epoch", "-")
        num_epochs = state.get("num_train_epochs", "-")
        best_step = state.get("best_global_step", "-")
        
        early_stopped = False
        if isinstance(global_step, int) and isinstance(max_steps, int):
            if global_step < max_steps:
                early_stopped = True
                
        status_text = "発動" if early_stopped else "なし（完走）"
        
        report.append(f"- **設定エポック数**: {num_epochs}")
        if isinstance(epoch_val, (int, float)):
            report.append(f"- **終了エポック**: {epoch_val:.2f} ({global_step} / {max_steps} steps)")
        else:
            report.append(f"- **終了エポック**: {epoch_val} ({global_step} / {max_steps} steps)")
        report.append(f"- **Early Stopping**: {status_text}")
        report.append(f"- **Best Checkpoint**: Step {best_step}")
        report.append("")
        
        steps_data = {}
        for log in state.get("log_history", []):
            step = log.get("step")
            if step not in steps_data:
                steps_data[step] = {"epoch": log.get("epoch", 0.0)}
            if "loss" in log:
                steps_data[step]["train_loss"] = log["loss"]
            if "eval_loss" in log:
                steps_data[step]["eval_loss"] = log["eval_loss"]
                
        if steps_data:
            report.append("| Step | Epoch | Train Loss | Eval Loss |")
            report.append("| :---: | :---: | :---: | :---: |")
            
            eval_steps = [s for s, d in steps_data.items() if "eval_loss" in d]
            if not eval_steps:
                display_steps = sorted(steps_data.keys())
                if len(display_steps) > 20:
                    step_size = len(display_steps) // 20
                    display_steps = display_steps[::step_size]
            else:
                display_steps = sorted(eval_steps)
                
            for s in display_steps:
                d = steps_data[s]
                ep = d["epoch"]
                tl = d.get("train_loss")
                el = d.get("eval_loss")
                
                if tl is None:
                    prev_steps = [k for k in steps_data.keys() if k <= s and "train_loss" in steps_data[k]]
                    if prev_steps:
                        tl = steps_data[max(prev_steps)]["train_loss"]
                        
                tl_str = f"{tl:.4f}" if tl is not None else "-"
                el_str = f"{el:.4f}" if el is not None else "-"
                
                best_mark = " ⭐" if s == best_step else ""
                
                report.append(f"| {s}{best_mark} | {ep:.2f} | {tl_str} | {el_str} |")
            report.append("")

    # ─────────────────────────────────────
    # ファイル出力
    # ─────────────────────────────────────
    output_path = results_dir / "summary_report.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print(f"\nレポートを生成しました: {output_path}")
    print(f"モデル数: {len(models)}")
    print(f"ファイルサイズ: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
