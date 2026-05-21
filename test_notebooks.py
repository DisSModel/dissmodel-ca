import json
import glob
import ast

for nb_file in glob.glob("examples/notebooks/*.ipynb"):
    with open(nb_file, 'r') as f:
        nb = json.load(f)
    print(f"Testing {nb_file}...")
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            source = "".join(cell.get("source", []))
            try:
                # remove magics if any
                clean_source = "\n".join([line for line in source.split('\n') if not line.startswith('%')])
                ast.parse(clean_source)
            except SyntaxError as e:
                print(f"  SyntaxError in cell: {e}")
                print(f"  Source:\n{clean_source}")

print("Done.")
