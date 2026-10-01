import json
import glob

base_file = glob.glob("/mnt/nas/home/hiromi/src/sst_v2/v3/results/vllm/debug_limit320/**/*diagonal_sst_main*alpha0.6*harmbench_safety.json", recursive=True)[0]
dare_file = glob.glob("/mnt/nas/home/hiromi/src/sst_v2/v3/results/vllm/debug_limit320/**/*dare*alpha0.6*harmbench_safety.json", recursive=True)[0]

with open(base_file, 'r') as f1, open(dare_file, 'r') as f2:
    d1 = json.load(f1)['results']
    d2 = json.load(f2)['results']

target_prompt = ""
for i in range(len(d1)):
    r1 = d1[i]['response']
    r2 = d2[i]['response']
    # base safe refusal, dare gibberish
    if "I cannot fulfill" in r1 or "I cannot assist" in r1 or "I am sorry" in r1 or "I apologize" in r1:
        if len(r2) > 0 and (r2.count(r2[:5]) > 3 or "[" in r2 or "{" in r2):
            target_prompt = d1[i]['prompt']
            break

print("Selected Prompt:", target_prompt)

files = glob.glob("/mnt/nas/home/hiromi/src/sst_v2/v3/results/vllm/debug_limit320/merged/**/*harmbench*.json", recursive=True)

found = {}
for f in files:
    with open(f, 'r') as fp:
        try:
            data = json.load(fp)
            if 'results' not in data: continue
            for item in data['results']:
                if item.get('prompt') == target_prompt:
                    model = data.get('model', f)
                    if "alpha0.6" not in model and "matena" not in model and "safemerge" not in model and "led" not in model:
                        continue
                    if "safety+math+code+medical" not in model and "safety+math" not in model:
                        continue
                    method = model.split("sst_merge_v3_main_")[1].split("_safety")[0] if "sst_merge" in model else model
                    if "dare" in model: method = "DARE"
                    elif "della" in model: method = "DELLA"
                    elif "diagonal_sst_main" in model: method = "Diagonal SST"
                    elif "ties" in model: method = "TIES"
                    elif "task_arithmetic" in model: method = "Task Arithmetic"
                    
                    found[method] = item['response']
                    break
        except:
            pass

print("| Method | Response |")
print("|---|---|")
for method, response in found.items():
    clean_resp = response.replace(chr(10), ' ')
    if len(clean_resp) > 300:
        clean_resp = clean_resp[:300] + "..."
    print(f"| {method} | {clean_resp} |")