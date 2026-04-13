from __future__ import annotations
import geopandas as gpd
from matplotlib.colors import ListedColormap

from dissmodel.core          import Environment
from dissmodel.geo           import vector_grid
from dissmodel.executor      import ModelExecutor, ExperimentRecord
from dissmodel.executor.cli  import run_cli
from dissmodel_ca.models     import GameOfLife
from dissmodel.io            import load_dataset, save_dataset # Importe o load original se quiser suporte a arquivo

class GameOfLifeExecutor(ModelExecutor):
    name = "game_of_life_vector"

    def load(self, record: ExperimentRecord) -> gpd.GeoDataFrame:
        """
        Prepara o dado: ou carrega um arquivo real ou gera a grade sintética.
        """
        uri = record.source.uri
        
        if uri == "synthetic":
            grid_size = record.parameters.get("grid_size", 20)
            record.add_log(f"Generating synthetic {grid_size}x{grid_size} grid")
            return vector_grid(dimension=(grid_size, grid_size), resolution=1, attrs={"state": 0})
        
        # Opcional: Se quiser permitir carregar um mapa inicial de um arquivo
        gdf, checksum = load_dataset(uri)
        record.source.checksum = checksum
        return gdf

    def validate(self, record: ExperimentRecord) -> None:
        if record.parameters.get("grid_size", 20) <= 0:
            raise ValueError("grid_size must be > 0")

    def run(self, data: gpd.GeoDataFrame, record: ExperimentRecord) -> gpd.GeoDataFrame:
        """
        Agora o 'data' já vem preenchido pelo load() ali de cima.
        """
        params = record.parameters
        steps  = params.get("end_time", 10)
        
        env = Environment(start_time=0, end_time=steps)
        model = GameOfLife(gdf=data) # 'data' é o GDF vindo do load
        model.initialize()

        if params.get("interactive", False):
            from dissmodel.visualization import Map
            cmap = ListedColormap(["white", "black"])
            Map(gdf=data, plot_params={"column": "state", "cmap": cmap, "ec": "gray"})

        env.run()
        return data

    def save(self, result: gpd.GeoDataFrame, record: ExperimentRecord) -> ExperimentRecord:
        # Gera um nome automático se não for passado --output
        uri = record.output_path or f"results/gol_{record.experiment_id[:8]}.gpkg"
        checksum = save_dataset(result, uri)
        
        record.output_path = uri
        record.output_sha256 = checksum
        record.status = "completed"
        return record

if __name__ == "__main__":
    run_cli(GameOfLifeExecutor)