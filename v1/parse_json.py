import json
with open('all_eval_results_summary.json', 'r') as f:
    data = json.load(f)

for item in data:
    if item['category'] == 'additive':
        print(json.dumps(item, indent=2))
        break

for item in data:
    if item['category'] == 'interpolation':
        print(json.dumps(item, indent=2))
        break

for item in data:
    if item['category'] == 'data_free':
        print(json.dumps(item, indent=2))
        break
