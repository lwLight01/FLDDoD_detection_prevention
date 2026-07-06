import json

file_path = "notebooks/01_eda_and_cleaning.ipynb"
with open(file_path, "r", encoding="utf-8") as f:
    notebook = json.load(f)

for cell in notebook["cells"]:
    if cell["cell_type"] == "code":
        new_source = []
        for line in cell["source"]:
            new_source.append(line.replace(
                "'Fwd PSH Flags': 'TCP Flags',",
                "'Fwd PSH Flags': 'TCP Flags',\n    'Init Fwd Win Bytes': 'Init_Win_bytes_forward',"
            ))
        cell["source"] = new_source

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)

print("Notebook updated successfully.")
