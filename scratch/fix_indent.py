import glob

for path in glob.glob("src/**/*.py", recursive=True):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    changed = False
    for i in range(len(lines) - 1):
        if "# (Summary comment)" in lines[i]:
            indent = len(lines[i]) - len(lines[i].lstrip('\n').lstrip())
            next_line_stripped = lines[i+1].lstrip('\n').lstrip()
            
            if next_line_stripped and (len(lines[i+1]) - len(next_line_stripped)) < indent:
                lines[i+1] = (" " * indent) + next_line_stripped
                changed = True
                
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

print('Fixed indentation.')
