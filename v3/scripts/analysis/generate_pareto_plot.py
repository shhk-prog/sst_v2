import re
import matplotlib.pyplot as plt

filepath = "/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_vllm_hyo_latex.md"

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

data = {} # method -> {alpha: (safety_asr, utility)}

current_method = None
current_pattern = None

for line in lines:
    if line.startswith("% --- Alpha スイープ 集計 - Method: "):
        match = re.search(r"Method: (.*?), Pattern: (.*?) ---", line)
        if match:
            current_method = match.group(1)
            current_pattern = match.group(2)
            if current_pattern == "safety+math":
                if current_method not in data:
                    data[current_method] = []
    
    if current_pattern == "safety+math" and current_method:
        if line.startswith("vllm & safety+math &"):
            parts = [x.strip() for x in line.split("&")]
            if len(parts) > 6:
                alpha = parts[3]
                safety_str = parts[4].split("\\pm")[0].strip()
                utility_str = parts[5].split("\\pm")[0].strip()
                try:
                    safety = float(safety_str)
                    utility = float(utility_str)
                    if alpha != "N/A":
                        alpha_val = float(alpha)
                        data[current_method].append((alpha_val, safety, utility))
                    else:
                        data[current_method].append((0.0, safety, utility))
                except:
                    pass

# Plotting
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(10, 7))

method_names = {
    "diagonal_sst_main": "SST-Merge (Ours)",
    "data_free_sst_main": "Data-Free SST (Ours)",
    "ties": "TIES",
    "dare": "DARE",
    "della": "DELLA",
    "task_arithmetic": "Task Arithmetic",
    "matena_fisher": "Matena Fisher",
    "safemerge": "SafeMERGE",
    "led_merging": "LED-Merging",
    "mergealign": "MergeAlign",
    "Base": "Base Models"
}

colors = {
    "diagonal_sst_main": "#e74c3c",  # Red
    "data_free_sst_main": "#e67e22", # Orange
    "ties": "#3498db",             # Blue
    "dare": "#2ecc71",             # Green
    "della": "#9b59b6",            # Purple
    "task_arithmetic": "#7f8c8d",  # Grey
    "matena_fisher": "#34495e",    # Dark Blue
    "safemerge": "#e84393",        # Pink
    "led_merging": "#00cec9",      # Cyan
    "mergealign": "#2d3436"        # Black
}

markers = {
    "diagonal_sst_main": "o-",
    "data_free_sst_main": "s-",
    "ties": "^-",
    "dare": "v-",
    "della": "D-",
    "task_arithmetic": "x-",
}

def plot_methods(methods_to_plot, filename, title):
    fig, ax = plt.subplots(figsize=(10, 7))

    for method in methods_to_plot:
        points = data.get(method)
        if not points: continue
        label_name = method_names.get(method, method.replace("_", " "))
        
        if method in ["Base", "matena_fisher", "safemerge", "led_merging", "mergealign"]:
            # Single point
            safety = points[0][1]
            utility = points[0][2]
            ax.scatter([utility], [safety], label=label_name, color=colors.get(method, "black"), s=200, marker="*", zorder=5)
            continue

        points.sort(key=lambda x: x[0]) # sort by alpha
        
        alphas = [x[0] for x in points]
        safetys = [x[1] for x in points]
        utilities = [x[2] for x in points]
        
        fmt = markers.get(method, "o-")
        color = colors.get(method, "black")
        
        linewidth = 2.5
        markersize = 8
        
        ax.plot(utilities, safetys, fmt, label=label_name, color=color, linewidth=linewidth, markersize=markersize, alpha=0.9, zorder=4 if "sst" in method else 3)
        
        # Fill the area to visualize Pareto AUC
        if method != "Base":
            u_sorted = [0] + utilities + [utilities[-1]]
            s_sorted = [safetys[0]] + safetys + [100]
            ax.fill_between(u_sorted, s_sorted, 100, color=color, alpha=0.15, zorder=1)
        
        # annotate alphas
        if method != "Base":
            for a, s, u in points:
                if a in [0.2, 0.4, 0.6, 0.8, 1.0]:
                    ax.annotate(f"$\\alpha$={a}", (u, s), textcoords="offset points", xytext=(8, -12), ha='center', fontsize=9, color=color, fontweight='bold')

    ax.set_xlim(0, 15)
    ax.set_ylim(-2, 105)

    ax.annotate('Ideal Region\n(High Utility, Low ASR)', xy=(14, 2), xycoords='data',
                xytext=(10, 20), textcoords='data',
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8),
                horizontalalignment='center', verticalalignment='center',
                fontsize=11, fontweight='bold', color='#2c3e50',
                bbox=dict(boxstyle="round,pad=0.3", fc="#ecf0f1", ec="#bdc3c7", lw=1.5, alpha=0.8))

    ax.set_xlabel("Utility (GSM8K Acc %)", fontsize=13, fontweight='bold')
    ax.set_ylabel("Safety (Harmful ASR %)", fontsize=13, fontweight='bold')
    ax.set_title(title, fontsize=15, fontweight='bold', pad=15)

    ax.tick_params(axis='both', which='major', labelsize=11)
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=11, frameon=True, shadow=True, title="Merging Methods", title_fontsize=12)

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved {filename}")
    plt.close(fig)

# Generate individual plots for ALL methods
all_methods = [
    "diagonal_sst_main", "data_free_sst_main", "ties", "dare", 
    "della", "task_arithmetic", "matena_fisher", "safemerge", 
    "led_merging", "mergealign"
]

for baseline in all_methods:
    title_name = method_names.get(baseline, baseline.replace("_", " "))
    plot_methods([baseline, "Base"], 
                 f"/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/pareto_curve_{baseline}.png",
                 f"Pareto AUC: {title_name}")