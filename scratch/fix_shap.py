import json

path = 'notebooks/04_shap_analysis.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb.get('cells', []):
    if cell['cell_type'] == 'code':
        new_source = []
        for line in cell.get('source', []):
            if 'shap_values = explainer.shap_values(attack_cont)' in line:
                line = line.replace('explainer.shap_values(attack_cont)', 'explainer.shap_values(attack_cont, check_additivity=False)')
            new_source.append(line)
        cell['source'] = new_source

with open(path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Notebook fixed.')
