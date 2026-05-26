from dissmodel.geo import vector_grid, parse_idx
gdf = vector_grid(dimension=(3, 3), resolution=1, attrs={"state": 0})
idx = gdf.index[1] # '1-0'
print(f"Index: {idx}")
try:
    x, y = parse_idx(idx)
    print(f"Parsed: x={x}, y={y}")
except Exception as e:
    print(f"Error: {e}")
