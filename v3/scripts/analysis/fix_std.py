import os

file_path = "/mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_flmsec_hyo.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix format_latex_val so that it doesn't print \pm 0.00 if std is 0.00 ? No, usually we want \pm 0.00.
# Wait, "seed別には標準偏差が入らないように" -> format_latex_val is receiving a tuple even for seed-specific values?
# Let's check aggregate_main
repl3 = """            s_score = float(np.mean(s_harmful)) if s_harmful else None
            s_orig_score = float(np.mean(s_orig)) if s_orig else None
            s_cond_score = float(np.mean(s_cond)) if s_cond else None
            s_vrr_score = float(np.mean(s_vrr)) if s_vrr else None
            s_vsr_score = float(np.mean(s_vsr)) if s_vsr else None
            m_score = float(np.mean(m_vals)) if m_vals else None
            c_score = float(np.mean(c_vals)) if c_vals else None
            med_score = float(np.mean(med_vals)) if med_vals else None
            g_score = float(np.mean(g_vals)) if g_vals else None"""

# In the original generate_flmsec_hyo.py, are seed specific metrics tuples?
# They are float(np.mean(...)) so they are floats.
# Then why would seed別 have \pm? 
# Maybe format_latex_val is outputting \pm for floats? No, `elif isinstance(val, (int, float)): return f"{val:.2f}"`.
