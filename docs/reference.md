# Referência de Modelos DisSModel-CA

Esta seção detalha os modelos de Autômatos Celulares (CA) disponíveis no `dissmodel-ca`, seguindo o estilo de documentação do TerraME. Cada modelo mapeia a teoria ecológica ou física para implementações espaciais eficientes.

---

### Game of Life (Jogo da Vida)

**1. Descrição:**
Implementação do clássico Autômato Celular de John Conway. É um modelo determinístico que demonstra como padrões complexos podem emergir de regras locais extremamente simples, sendo Turing-completo.

**2. Estados:**
*   **0 - Dead (Morto):** Célula inativa.
*   **1 - Alive (Vivo):** Célula ativa.

**3. Vizinhança:**
Vizinhança de **Moore (Queen)**, considerando os 8 vizinhos imediatos (incluindo diagonais).

**4. Regras de Transição:**
As células sobrevivem ou morrem com base no número de vizinhos vivos:
*   Uma célula **viva** com menos de 2 ou mais de 3 vizinhos vivos **morre** (isolamento ou superpopulação).
*   Uma célula **viva** com 2 ou 3 vizinhos vivos **permanece viva**.
*   Uma célula **morta** com exatamente 3 vizinhos vivos **torna-se viva** (reprodução).

**5. Exemplo de Uso:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import GameOfLife

# Criar espaço celular 20x20
gdf = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})
env = Environment(end_time=50)

# Instanciar e inicializar com padrões aleatórios
ca = GameOfLife(gdf=gdf)
ca.initialize() # Preenchimento aleatório 60/40
```

---

### Fire Model (Modelo de Fogo)

**1. Descrição:**
Simulação espacial de propagação de incêndio florestal. O fogo se espalha de forma determinística em uma floresta contínua através do contato direto entre vizinhos.

**2. Estados:**
*   **0 - FOREST (Floresta):** Vegetação saudável que pode queimar.
*   **1 - BURNING (Queimando):** Célula em chamas, propaga o fogo.
*   **2 - BURNED (Queimado):** Área já consumida, não volta a queimar.

**3. Vizinhança:**
Vizinhança de **Von Neumann (Rook)**, considerando apenas os 4 vizinhos cardeais (Norte, Sul, Leste, Oeste).

**4. Regras de Transição:**
*   Uma célula em estado **BURNING** sempre se torna **BURNED** no próximo passo.
*   Uma célula **FOREST** torna-se **BURNING** se pelo menos um de seus vizinhos estiver **BURNING**.
*   Uma célula **BURNED** permanece **BURNED** indefinidamente.

**5. Exemplo de Uso:**
```python
from dissmodel_ca.models import FireModel, FireState

# Configuração com densidade inicial de fogo de 5%
fire = FireModel(gdf=gdf)
fire.setup(initial_fire_density=0.05)
fire.initialize()
```

---

### Probabilistic Forest Fire (Fogo Probabilístico)

**1. Descrição:**
Extensão do modelo de fogo básico que introduz processos estocásticos: combustão espontânea e regeneração da floresta. Isso cria um equilíbrio dinâmico entre o crescimento da floresta e os incêndios.

**2. Estados:**
Utiliza os mesmos estados do `FireModel`: **0 - FOREST**, **1 - BURNING**, **2 - BURNED**.

**3. Vizinhança:**
Vizinhança de **Moore (Queen)**.

**4. Regras de Transição:**
*   **FOREST → BURNING**: Ocorre se um vizinho estiver queimando OU por **combustão espontânea** (probabilidade `prob_combustion`).
*   **BURNING → BURNED**: Sempre ocorre após um passo de tempo.
*   **BURNED → FOREST**: Ocorre por **regeneração** (probabilidade `prob_regrowth`).

!!! info "Dinâmica Estocástica"
    Diferente do modelo básico, este modelo pode manter a simulação ativa indefinidamente devido à regeneração (`regrowth`), impedindo que o sistema atinja um estado final estático de "tudo queimado".

**5. Exemplo de Uso:**
```python
from dissmodel_ca.models import FireModelProb

fire_prob = FireModelProb(gdf=gdf)
# Configura 0.1% de chance de fogo espontâneo e 10% de chance de regeneração
fire_prob.setup(prob_combustion=0.001, prob_regrowth=0.1)
```

---

### Interspecific Competition (Competição Interespecífica)

**1. Descrição:**
Modelo baseado no trabalho de Silvertown et al. (1992), simulando a competição espacial entre cinco espécies de gramíneas. É um modelo de substituição onde vizinhos tentam "invadir" o espaço uns dos outros.

**2. Estados:**
Cinco espécies discretas:
*   **0 - LOLIUM** (*Lolium perenne*)
*   **1 - AGROSTIS** (*Agrostis stolonifera*)
*   **2 - HOLCUS** (*Holcus lanatus*)
*   **3 - POA** (*Poa trivialis*)
*   **4 - CYNOSURUS** (*Cynosurus cristatus*)

**3. Vizinhança:**
Vizinhança de **Von Neumann (Rook)**.

**4. Regras de Transição:**
A cada passo, a espécie de uma célula pode ser substituída por uma espécie vizinha. A probabilidade de invasão depende de:
*   A fração de vizinhos pertencentes à espécie invasora.
*   A taxa de invasão experimental (matriz de probabilidade) da espécie invasora contra a espécie ocupante atual.

**5. Exemplo de Uso:**
```python
from dissmodel_ca.models import InterspecificCompetition

# Inicia com o arranjo espacial 'ModelA' (faixas horizontais)
ic = InterspecificCompetition(gdf=gdf, displacement="ModelA")
ic.initialize()
```

---

### Anneal (Recozimento)

**1. Descrição:**
Variante da regra de votação majoritária que produz regiões suaves e arredondadas (blobs). É frequentemente usado para simular segregação espacial ou limpeza de ruído em imagens.

**2. Estados:**
*   **0 - L (Esquerda):** Estado A.
*   **1 - R (Direita):** Estado B.

**3. Vizinhança:**
Vizinhança de **Moore (Queen)**.

**4. Regras de Transição:**
Conta-se o número de células no estado **L** entre os vizinhos e a própria célula (total de 9 células):
*   Soma ≤ 3 → **R**
*   Soma == 4 → **L**
*   Soma == 5 → **R**
*   Soma ≥ 6 → **L**

---

### Growth (Crescimento)

**1. Descrição:**
Modelo estocástico que simula o crescimento espacial a partir de uma semente central. Útil para modelar expansão urbana simplificada ou colonização biológica.

**2. Estados:**
*   **0 - EMPTY (Vazio):** Célula disponível para colonização.
*   **1 - ALIVE (Vivo):** Célula colonizada.

**3. Vizinhança:**
Vizinhança de **Moore (Queen)**.

**4. Regras de Transição:**
*   Células **ALIVE** nunca morrem.
*   Células **EMPTY** tornam-se **ALIVE** com uma probabilidade `probability` se tiverem **pelo menos um** vizinho vivo.

---

### Solid Diffusion (Difusão em Sólidos)

**1. Descrição:**
Simula a difusão atômica através do mecanismo de lacunas (vacancies). Dois tipos de átomos se misturam conforme as lacunas se movem aleatoriamente pelo reticulado cristalino.

**2. Estados:**
*   **0 - ATOM1:** Átomo do tipo 1.
*   **1 - ATOM2:** Átomo do tipo 2.
*   **2 - VACANCY:** Espaço vazio no cristal.

**3. Vizinhança:**
Vizinhança de **Moore (Queen)**.

**4. Regras de Transição:**
Este modelo usa uma atualização **sequencial aleatória** em vez de síncrona:
*   Cada lacuna (`VACANCY`) escolhe aleatoriamente um vizinho que não seja lacuna.
*   A lacuna e o átomo vizinho trocam de posição.

!!! note "Conservação de Massa"
    A atualização sequencial é necessária aqui para garantir que nenhum átomo seja criado ou destruído durante a troca, o que ocorreria em uma atualização puramente síncrona.

---

### Wolfram (Regras Elementares 1D)

**1. Descrição:**
Implementa as regras elementares de Stephen Wolfram. Embora o autômato seja unidimensional, ele é visualizado em 2D, onde cada linha representa uma geração sucessiva.

**2. Estados:**
*   **0:** Inativo.
*   **1:** Ativo.

**3. Vizinhança:**
Vizinhança linear (Célula acima-esquerda, acima-centro, acima-direita).

**4. Regras de Transição:**
A nova célula na linha $t$ depende da configuração de 3 células na linha $t-1$. Existem 256 regras possíveis (ex: Regra 30, Regra 90, Regra 110).

---

### Snow (Acúmulo de Neve)

**1. Descrição:**
Simula a queda e o acúmulo de neve em uma grade vertical. Flocos de neve caem do topo e se movem para baixo até atingirem o chão ou outro floco.

**2. Estados:**
*   **0 - EMPTY:** Ar vazio.
*   **1 - SNOW:** Floco de neve.

**3. Regras de Transição:**
*   Novos flocos surgem no topo com probabilidade `probability`.
*   Flocos se movem uma célula para baixo se o espaço estiver vazio.
*   Flocos param (acumulam) se houver o fundo da grade ou outro floco abaixo.
