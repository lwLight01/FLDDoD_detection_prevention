import json

path = 'notebooks/04_shap_analysis.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb.get('cells', []):
    if cell['cell_type'] == 'code':
        new_source = []
        for line in cell.get('source', []):
            if 'base_values=explainer.expected_value' in line:
                new_source.append('    base_values=explainer.expected_value[0] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value,\n')
            else:
                new_source.append(line)
        cell['source'] = new_source

with open(path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Notebook waterfall plot fixed on disk.')
