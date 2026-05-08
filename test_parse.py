import json
with open('all_eval_results_summary.json', 'r') as f:
    data = json.load(f)

for item in data:
    if item.get('category') == 'sst_merge' and 'A6_A7' in item.get('filename', ''):
        print("SST-Merge Sample:")
        print(json.dumps(item, indent=2))
        break

for item in data:
    if item.get('category') == 'sst_data_free' and 'A6_A7' in item.get('filename', ''):
        print("Data-Free Sample:")
        print(json.dumps(item, indent=2))
        break

