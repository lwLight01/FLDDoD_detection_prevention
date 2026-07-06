import json

path = 'notebooks/04_shap_analysis.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb.get('cells', []):
    if cell['cell_type'] == 'code':
        new_source = []
        for line in cell.get('source', []):
            new_source.append(line)
            if 'shap_values = shap_values[0]' in line:
                # Add squeeze immediately after
                new_source.append('if len(shap_values.shape) == 3 and shap_values.shape[-1] == 1:\n')
                new_source.append('    shap_values = shap_values[:, :, 0]\n')
        cell['source'] = new_source

with open(path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Notebook shape fix applied.')
