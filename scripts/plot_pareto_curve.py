import re
import matplotlib.pyplot as plt
import pandas as pd

def parse_markdown_table(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the Appendix table for safety+math
    match = re.search(r'#### ドメインパターン: `safety\+math` \(比較表: Alpha=0\.6 / 単一実行手法含む\)\n\n(.*?)\n\n###', content, re.DOTALL)
    if not match:
        print("Table not found!")
        return None

    table_text = match.group(1).strip()
    lines = table_text.split('\n')
    
    header = [h.strip() for h in lines[0].split('|')[1:-1]]
    
    data = []
    for line in lines[2:]:
        row = [cell.strip() for cell in line.split('|')[1:-1]]
        if len(row) == len(header):
            data.append(row)

    df = pd.DataFrame(data, columns=header)
    return df

def clean_percent(x):
    if x == '-' or x == 'N/A':
        return None
    try:
        # Extract the mean value before the ± sign
        val = x.split('±')[0].strip().replace('%', '')
        return float(val)
    except:
        return None

def plot_pareto(df, output_path):
    # We want X = GSM8K (%), Y = Harmful ASR (%)
    # In table: 'GSM8K (%)', 'HarmBench (ASR↓ %)' or 'Safety Ave [Harmful Content] (ASR↓ %)'
    # Let's use 'GSM8K (%)' and 'Safety Ave [Harmful Content] (ASR↓ %)'
    
    df['Utility'] = df['GSM8K (%)'].apply(clean_percent)
    df['Safety_ASR'] = df['Safety Ave [Harmful Content] (ASR↓ %)'].apply(clean_percent)
    
    df = df.dropna(subset=['Utility', 'Safety_ASR'])
    
    plt.figure(figsize=(10, 7))
    
    methods = df['Method'].unique()
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x', 'X', 'd', '|', '_']
    
    for i, method in enumerate(methods):
        method_df = df[df['Method'] == method]
        plt.scatter(method_df['Utility'], method_df['Safety_ASR'], 
                    label=method, marker=markers[i % len(markers)], s=100)
        
        # Add labels for alpha if available
        for _, row in method_df.iterrows():
            alpha = row['Alpha']
            if alpha != 'N/A' and method in ['diagonal_sst_main', 'data_free_sst_main', 'task_arithmetic']:
                plt.annotate(f"$\\alpha={alpha}$", (row['Utility'], row['Safety_ASR']), 
                             xytext=(5, 5), textcoords='offset points', fontsize=8)

    plt.title('Pareto Frontier (safety+math): GSM8K vs Harmful ASR')
    plt.xlabel('Utility: GSM8K Accuracy (%) -> Better')
    plt.ylabel('Safety: Harmful Content ASR (%) -> Better (Lower is safer)')
    
    # Invert Y axis so that lower ASR (better safety) is higher up, 
    # making the top-right the ideal Pareto optimal point.
    plt.gca().invert_yaxis()
    
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Saved plot to {output_path}")

if __name__ == "__main__":
    paper_path = "/mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/secure-merge_統一比較評価論文_改訂版.md"
    df = parse_markdown_table(paper_path)
    if df is not None:
        plot_pareto(df, "/mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI/pareto_curve.png")
