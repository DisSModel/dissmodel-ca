from dissmodel.geo import vector_grid
gdf = vector_grid(dimension=(3, 3), resolution=1, attrs={"state": 0})
for idx, row in gdf.iterrows():
    print(f"ID: {idx}, Centroid: {row.geometry.centroid.x}, {row.geometry.centroid.y}")
