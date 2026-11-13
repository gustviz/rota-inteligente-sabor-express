"""Testes dos algoritmos de busca: A* e Dijkstra devem coincidir com o networkx (referência)."""
from itertools import permutations

import networkx as nx
import pytest

from busca import a_estrela, bfs, dfs, dijkstra
from grafo import Grafo, carregar_grafo


@pytest.fixture(scope="module")
def grafo():
    return carregar_grafo()


@pytest.mark.parametrize("peso", ["tempo_min", "distancia_km"])
def test_a_estrela_e_dijkstra_sao_otimos(grafo, peso):
    g_nx = grafo.para_networkx()
    for o, d in permutations(grafo.nos, 2):
        referencia = nx.shortest_path_length(g_nx, o, d, weight=peso)
        assert a_estrela(grafo, o, d, peso).custo == pytest.approx(referencia)
        assert dijkstra(grafo, o, d, peso).custo == pytest.approx(referencia)


def test_a_estrela_expande_no_maximo_o_mesmo_que_dijkstra(grafo):
    for o, d in permutations(grafo.nos, 2):
        assert a_estrela(grafo, o, d).nos_expandidos <= dijkstra(grafo, o, d).nos_expandidos


def test_heuristica_admissivel(grafo):
    """h(n) nunca pode superar o custo real até o destino."""
    for peso in ("tempo_min", "distancia_km"):
        h = grafo.heuristica(peso)
        for o, d in permutations(grafo.nos, 2):
            assert h(o, d) <= dijkstra(grafo, o, d, peso).custo + 1e-9


def test_bfs_usa_menor_numero_de_ruas(grafo):
    g_nx = grafo.para_networkx()
    for o, d in permutations(grafo.nos, 2):
        assert len(bfs(grafo, o, d).caminho) - 1 == nx.shortest_path_length(g_nx, o, d)


def test_caminhos_respeitam_mao_unica(grafo):
    for func in (bfs, dfs, dijkstra, a_estrela):
        for o, d in permutations(grafo.nos[:10], 2):
            caminho = func(grafo, o, d).caminho
            assert caminho[0] == o and caminho[-1] == d
            assert all(b in grafo.adj[a] for a, b in zip(caminho, caminho[1:]))


def test_destino_inalcancavel():
    g = Grafo()
    g.adicionar_no("A", 0, 0)
    g.adicionar_no("B", 1, 0)
    g.adicionar_aresta("A", "B", tempo_min=1.0, distancia_km=1.0, velocidade_kmh=40)  # mão única A -> B
    for func in (bfs, dfs, dijkstra, a_estrela):
        r = func(g, "B", "A")
        assert not r.encontrou and r.custo == float("inf")
