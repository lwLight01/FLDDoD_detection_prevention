import json

path = 'notebooks/04_shap_analysis.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb.get('cells', []):
    if cell['cell_type'] == 'code':
        for line in cell.get('source', []):
            if 'shap_values' in line:
                print(repr(line))
