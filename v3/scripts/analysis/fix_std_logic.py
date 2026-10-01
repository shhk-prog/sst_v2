import os

file_path = "/mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_flmsec_hyo.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

repl1 = """                mean_val = float(np.mean(seed_vals))
                std_val = float(np.std(seed_vals, ddof=1)) if len(seed_vals) > 1 else 0.0
                agg_metrics[m_name] = (mean_val, std_val)"""

repl1_new = """                mean_val = float(np.mean(seed_vals))
                if len(seed_vals) > 1:
                    std_val = float(np.std(seed_vals, ddof=1))
                    agg_metrics[m_name] = (mean_val, std_val)
                else:
                    agg_metrics[m_name] = mean_val"""

content = content.replace(repl1, repl1_new)

repl2 = """                mean_val = float(np.mean(vals))
                std_val = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
                agg_metrics[k] = (mean_val, std_val)"""

repl2_new = """                mean_val = float(np.mean(vals))
                if len(vals) > 1:
                    std_val = float(np.std(vals, ddof=1))
                    agg_metrics[k] = (mean_val, std_val)
                else:
                    agg_metrics[k] = mean_val"""
content = content.replace(repl2, repl2_new)


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("generate_flmsec_hyo.py std logic updated successfully.")
