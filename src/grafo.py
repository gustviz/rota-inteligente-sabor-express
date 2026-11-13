"""Representação da cidade como grafo direcionado e ponderado.

- Nós    = bairros (com coordenadas x, y em km).
- Arestas = ruas, com dois pesos possíveis: 'tempo_min' (padrão) ou 'distancia_km'.
- Ruas de mão dupla viram duas arestas; ruas de mão única, apenas uma.
"""
import math
from pathlib import Path

import pandas as pd

PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"
PESOS_VALIDOS = ("tempo_min", "distancia_km")


class Grafo:
    def __init__(self):
        self.posicoes = {}   # bairro -> (x, y)
        self.adj = {}        # bairro -> {vizinho: {atributos da rua}}
        self.velocidade_maxima = 1.0

    def adicionar_no(self, nome, x, y):
        self.posicoes[nome] = (x, y)
        self.adj.setdefault(nome, {})

    def adicionar_aresta(self, origem, destino, **atributos):
        self.adj[origem][destino] = atributos
        self.velocidade_maxima = max(self.velocidade_maxima, atributos.get("velocidade_kmh", 0))

    def vizinhos(self, no):
        """Vizinhos em ordem alfabética (deixa BFS/DFS determinísticos)."""
        return sorted(self.adj[no].items())

    @property
    def nos(self):
        return list(self.posicoes)

    def num_arestas(self):
        return sum(len(v) for v in self.adj.values())

    def distancia_reta(self, a, b):
        return math.dist(self.posicoes[a], self.posicoes[b])

    def heuristica(self, peso):
        """Heurística admissível do A* para o peso escolhido.

        - distancia_km: distância em linha reta (nenhuma rua é mais curta que a reta).
        - tempo_min: linha reta percorrida na velocidade máxima, sem trânsito
          (nenhuma rua é mais rápida que isso).
        """
        if peso == "distancia_km":
            return lambda a, b: self.distancia_reta(a, b)
        if peso == "tempo_min":
            return lambda a, b: self.distancia_reta(a, b) / self.velocidade_maxima * 60
        raise ValueError(f"peso deve ser um de {PESOS_VALIDOS}")

    def custo_caminho(self, caminho, peso):
        return sum(self.adj[a][b][peso] for a, b in zip(caminho, caminho[1:]))

    def para_networkx(self):
        import networkx as nx
        g = nx.DiGraph()
        for n, (x, y) in self.posicoes.items():
            g.add_node(n, pos=(x, y))
        for a, viz in self.adj.items():
            for b, attrs in viz.items():
                g.add_edge(a, b, **attrs)
        return g


def carregar_grafo(pasta=PASTA_DADOS):
    pasta = Path(pasta)
    bairros = pd.read_csv(pasta / "bairros.csv")
    ruas = pd.read_csv(pasta / "ruas.csv")
    g = Grafo()
    for b in bairros.itertuples():
        g.adicionar_no(b.bairro, b.x_km, b.y_km)
    for r in ruas.itertuples():
        attrs = {
            "distancia_km": r.distancia_km, "tempo_min": r.tempo_min, "tipo_via": r.tipo_via,
            "velocidade_kmh": r.velocidade_kmh, "mao_unica": bool(r.mao_unica),
        }
        g.adicionar_aresta(r.origem, r.destino, **attrs)
        if not r.mao_unica:
            g.adicionar_aresta(r.destino, r.origem, **attrs)
    return g


def carregar_pedidos(pasta=PASTA_DADOS):
    return pd.read_csv(Path(pasta) / "pedidos.csv")
