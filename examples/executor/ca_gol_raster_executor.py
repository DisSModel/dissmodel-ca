from __future__ import annotations

import os
from dissmodel.core import Environment
from dissmodel.geo import raster_grid
from dissmodel.executor import ModelExecutor, ExperimentRecord
from dissmodel.executor.cli import run_cli
from dissmodel_ca.models.game_of_life_raster import GameOfLife
from dissmodel.io import load_dataset, save_dataset

class GameOfLifeRasterExecutor(ModelExecutor):
    """
    Executor para a versão Raster do Game of Life.
    Otimizado para grandes matrizes NumPy.
    """
    
    name = "game_of_life_raster"

    def load(self, record: ExperimentRecord):
        """Prepara o RasterBackend."""
        uri = record.source.uri
        
        if uri == "synthetic":
            # Pegamos dimensões dos parâmetros ou usamos 1000x1000 como padrão
            rows = record.parameters.get("rows", 1000)
            cols = record.parameters.get("cols", 1000)
            record.add_log(f"Generating synthetic raster grid: {rows}x{cols}")
            return raster_grid(rows=rows, cols=cols, attrs={"state": 0})
        
        # Se for um arquivo (ex: .tif), carregamos via IO
        backend, checksum = load_dataset(uri, format="raster")
        record.source.checksum = checksum
        return backend

    def validate(self, record: ExperimentRecord) -> None:
        if record.parameters.get("rows", 1000) <= 0:
            raise ValueError("rows must be > 0")

    def run(self, data, record: ExperimentRecord):
        """'data' aqui é o RasterBackend injetado pelo load()."""
        params = record.parameters
        steps  = params.get("end_time", 10)
        
        env = Environment(start_time=0, end_time=steps)
        gol = GameOfLife(backend=data)
        gol.initialize()

        # O RasterMap já suporta o modo interativo via variável de ambiente
        # ou podemos forçar aqui se o parâmetro 'interactive' for passado.
        if params.get("interactive", False) or os.environ.get("RASTER_MAP_INTERACTIVE"):
            from dissmodel.visualization.raster_map import RasterMap
            RasterMap(
                backend   = data,
                band      = "state",
                color_map = {0: "#ffffff", 1: "#000000"},
                labels    = {0: "dead", 1: "alive"},
                title     = f"Game of Life Raster - Step {steps}",
            )

        record.add_log(f"Running raster simulation for {steps} steps...")
        env.run()
        return data

    def save(self, result, record: ExperimentRecord) -> ExperimentRecord:
        """Salva o resultado como GeoTIFF."""
        # Se não houver output_path, gera um padrão .tif
        uri = record.output_path or f"results/gol_raster_{record.experiment_id[:8]}.tif"
        
        # O save_dataset detecta que é raster e salva como GeoTIFF
        checksum = save_dataset(result, uri)
        
        record.output_path = uri
        record.output_sha256 = checksum
        record.status = "completed"
        return record

if __name__ == "__main__":
    run_cli(GameOfLifeRasterExecutor)