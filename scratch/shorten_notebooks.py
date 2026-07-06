import json
import glob

notebooks = glob.glob('notebooks/*.ipynb')

for nb_path in notebooks:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
        
    for cell in nb.get('cells', []):
        if cell['cell_type'] == 'markdown':
            # Shorten markdown cell to just its first non-empty line
            source = cell.get('source', [])
            if not source:
                continue
            
            # Find first line that has text
            first_line = ''
            for line in source:
                if line.strip():
                    first_line = line
                    break
                    
            if first_line:
                cell['source'] = [first_line.strip() + '\n']
        
        elif cell['cell_type'] == 'code':
            # Remove long comment blocks in code cells too
            source = cell.get('source', [])
            new_source = []
            for line in source:
                if line.strip().startswith('#'):
                    # Keep it if it's the first comment, or just skip
                    pass
                else:
                    new_source.append(line)
            cell['source'] = new_source

    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

print('Notebook markdown shortened.')
