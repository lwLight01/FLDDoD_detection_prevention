import os
import glob
import re

files = glob.glob('src/**/*.py', recursive=True) + glob.glob('scripts/*.py')

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Shorten docstrings: """ ... """ -> keep only the first line of the docstring
    def shorten_docstring(match):
        doc = match.group(0)
        lines = doc.split('\n')
        if len(lines) > 2:
            return f'"""{lines[1].strip()}"""' if '"""' in lines[0] and len(lines[0].strip()) == 3 else f'"""{lines[0].replace('\"\"\"', '').strip()}"""'
        return doc
        
    # Python regex to find """ docstrings """
    content = re.sub(r'\"\"\"[\s\S]*?\"\"\"', shorten_docstring, content)
    
    # Remove # comments that are more than 1 line, or just keep the first line.
    # Actually, let's just leave single # comments alone, and remove the blocks of #
    content = re.sub(r'(#.*?\n\s*){2,}', r'# (Summary comment)\n', content)

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
print('Comments shortened.')
