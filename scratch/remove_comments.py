import os
import tokenize
import io

def remove_comments_and_docstrings(source):
    io_obj = io.StringIO(source)
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    
    try:
        for tok in tokenize.generate_tokens(io_obj.readline):
            token_type = tok[0]
            token_string = tok[1]
            start_line, start_col = tok[2]
            end_line, end_col = tok[3]
            
            if start_line > last_lineno:
                last_col = 0
            if start_col > last_col:
                out += (" " * (start_col - last_col))
                
            if token_type == tokenize.COMMENT:
                pass
            elif token_type == tokenize.STRING:
                if prev_toktype != tokenize.INDENT and prev_toktype != tokenize.NEWLINE and start_col > 0:
                    out += token_string
            else:
                out += token_string
                
            prev_toktype = token_type
            last_col = end_col
            last_lineno = end_line
    except tokenize.TokenError:
        return source
        
    # Also clean up empty lines left behind
    lines = out.split('\n')
    cleaned_lines = [line for line in lines if line.strip() != '']
    return '\n'.join(cleaned_lines) + '\n'

files_to_clean = [
    'src/db/database.py',
    'src/db/models.py',
    'src/fl_client/dataset.py',
    'src/fl_client/model.py',
    'scripts/create_fl_splits.py',
    'scripts/init_db.py',
    'tests/unit/test_phase2_dataset.py',
    'tests/unit/test_phase2_model.py',
]

for fpath in files_to_clean:
    if not os.path.exists(fpath): continue
    with open(fpath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    cleaned = remove_comments_and_docstrings(source)
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(cleaned)

print('Cleaned comments from python files.')
