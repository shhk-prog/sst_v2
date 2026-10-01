import os
import sys
import pandas as pd

def parse_model_display_name(filename):
    """ファイル名から人間に読みやすいモデル・実験条件名をパースする。"""
    parts = filename.split('_')
    
    # 手法名
    method = "Unknown"
    for m in ["dare", "ties", "della", "task_arithmetic", "diagonal", "data_free", "led_merging", "matena_fisher", "safemerge", "mergealign"]:
        if m in filename:
            method = m.replace('_', ' ').upper()
            break
            
    # alpha値の抽出
    alpha = None
    for part in parts:
        if part.startswith("alpha"):
            try:
                alpha = float(part.replace("alpha", ""))
            except:
                pass
                
    if alpha is not None:
        return f"{method} (alpha={alpha})"
    else:
        # alpha がない単一マージ手法、またはベースモデル
        if "sst_merge" not in filename:
            return f"Base: {parts[0].capitalize()}"
        return method

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_tables.py <csv_path> <output_md_path>")
        sys.exit(1)
        
    csv_path = sys.argv[1]
    output_md_path = sys.argv[2]
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    
    # モデルの表示名を付与
    df['model_name'] = df['filename'].apply(parse_model_display_name)
    
    # 指標ごとのピボット処理
    # 行: model_name, ASR
    # 列: utility_domain (個別タスク名が入っている)
    # ASRとUtilityを統合するため、まずタスクごとの値をピボット
    
    # 1. ユーティリティ値のピボット
    df_pivot = df.pivot_table(index='model_name', columns='utility_domain', values='utility', aggfunc='mean')
    
    # 2. 安全性（ASR）をモデルごとに集計（タスクごとの平均値、あるいは各タスクごとの ASR を列として追加）
    # CSVでは safety_task ごとに asr が記録されているため、safety_task 別の ASR を列として切り出します
    df_safety = df.pivot_table(index='model_name', columns='safety_task', values='asr', aggfunc='mean')
    # 列名を分かりやすく変更
    df_safety = df_safety.rename(columns=lambda x: f"{x} (ASR↓)")
    
    # 3. 結合
    df_result = pd.concat([df_safety, df_pivot], axis=1)
    
    # 指標のフォーマット調整
    # PPL (perplexity) は元の正の値に戻す
    for col in df_result.columns:
        if 'ppl' in col:
            df_result[col] = df_result[col].apply(lambda x: abs(x) if pd.notna(x) else x)
            df_result = df_result.rename(columns={col: col.replace('ppl', 'PPL↓')})
            
    # %表記の指標にフォーマット (ASRや各精度タスク)
    percent_metrics = [
        "harmbench (ASR↓)", "jailbreakbench (ASR↓)", "strongreject (ASR↓)", "wildjailbreak (ASR↓)", "average (ASR↓)",
        "gsm8k", "minerva_math500", "humaneval", "mbpp", "medqa_4options", "pubmedqa", "ifeval", "mmlu", "alpaca_eval2"
    ]
    
    for col in df_result.columns:
        col_clean = col.lower()
        is_pct = any(p in col_clean for p in percent_metrics)
        if is_pct:
            # 0.0-1.0の範囲を%に、76.91のような値はそのまま%に
            df_result[col] = df_result[col].apply(
                lambda x: f"{x*100:.2f}%" if pd.notna(x) and x <= 1.0001 and x >= 0.0 else (f"{x:.2f}%" if pd.notna(x) else "-")
            )
        else:
            df_result[col] = df_result[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "-")
            
    # 列名を分かりやすく（高低の矢印付きで）リネーム
    friendly_names = {
        "harmbench (ASR↓)": "Harmbench (ASR↓ %)",
        "jailbreakbench (ASR↓)": "Jailbreakbench (ASR↓ %)",
        "strongreject (ASR↓)": "Strongreject (ASR↓ %)",
        "wildjailbreak (ASR↓)": "Wildjailbreak (ASR↓ %)",
        "average (ASR↓)": "Average Safety (ASR↓ %)",
        
        "gsm8k": "GSM8K (Flex EM↑ %)",
        "minerva_math500": "Minerva Math500 (Verify↑ %)",
        "alpaca_eval2": "Alpaca Eval 2 (LC Win Rate↑ %)",
        
        "inst_evol_code_PPL↓": "Evol-Instruct-Code (PPL↓)",
        "inst_evol_code": "Evol-Instruct-Code (Sim Score↑)",
        "humaneval": "HumanEval (Pass@1↑ %)",
        "mbpp": "MBPP (Pass@1↑ %)",
        
        "inst_medalpaca_PPL↓": "MedAlpaca (PPL↓)",
        "inst_medalpaca": "MedAlpaca (Sim Score↑)",
        "medqa_4options": "MedQA (Acc Norm↑ %)",
        "pubmedqa": "PubmedQA (Acc↑ %)",
        
        "ifeval": "IFEval (Strict Prompt Acc↑ %)",
        "mmlu": "MMLU (Acc↑ %)",
        
        "math": "Math Domain (Avg↑)",
        "code": "Code Domain (Avg↑)",
        "medical": "Medical Domain (Avg↑)",
        "general": "General Domain (Avg↑)",
        "average": "Overall Avg Utility (Avg↑)"
    }
    df_result = df_result.rename(columns=friendly_names)

    # 手法判定用の関数を定義し、method_group 列を追加
    def get_method_group(model_name):
        name_upper = str(model_name).upper()
        # 特徴的なキーワードでマッピング
        for m in ["DARE", "TIES", "DELLA", "TASK ARITHMETIC", "DIAGONAL", "DATA FREE", "LED MERGING", "MATENA FISHER", "SAFEMERGE", "MERGEALIGN"]:
            if m in name_upper:
                return m
        return "OTHER"

    df_result['method_group'] = df_result.index.to_series().apply(get_method_group)

    # 1. 全体の Markdown テーブルを生成
    df_all_print = df_result.drop(columns=['method_group'])
    md_table_all = df_all_print.to_markdown()

    # 2. 各マージ手法ごとにグループ化してテーブルを生成
    sub_tables = {}
    methods_in_data = df_result['method_group'].unique()
    for method in sorted(methods_in_data):
        df_sub = df_result[df_result['method_group'] == method].drop(columns=['method_group'])
        sub_tables[method] = df_sub.to_markdown()

    # 出力ファイルに書き込み (実行ごとの重複重複を避けるため "w" で上書き書き出し)
    output_dir = os.path.dirname(output_md_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(f"# 実験条件・詳細比較テーブル集計結果 ({os.path.basename(csv_path)})\n\n")
        
        f.write("## 1. 全モデル総合比較テーブル\n\n")
        f.write(md_table_all)
        f.write("\n\n---\n\n")
        
        f.write("## 2. マージ手法別詳細テーブル\n\n")
        for method, md_sub in sub_tables.items():
            f.write(f"### {method}\n\n")
            f.write(md_sub)
            f.write("\n\n")
        
    print(f"Successfully generated tables and wrote to {output_md_path}")

if __name__ == "__main__":
    main()