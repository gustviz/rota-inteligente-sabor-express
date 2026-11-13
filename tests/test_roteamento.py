"""Testes do roteamento com múltiplas paradas e do agrupamento."""
from itertools import permutations

import pytest

from agrupamento import agrupar, escolher_k
from grafo import carregar_grafo
from roteamento import custo_rota, dois_opt, expandir_rota, matriz_custos, vizinho_mais_proximo

PARADAS = ["Vila Nova", "Planalto", "Santa Luzia", "Vila Real", "Bosque", "Jardim América"]


@pytest.fixture(scope="module")
def cenario():
    grafo = carregar_grafo()
    return grafo, matriz_custos(grafo, ["Centro"] + PARADAS)


def test_rota_visita_todas_as_paradas_e_volta(cenario):
    _, matriz = cenario
    rota = dois_opt(vizinho_mais_proximo("Centro", PARADAS, matriz), matriz)
    assert rota[0] == rota[-1] == "Centro"
    assert sorted(rota[1:-1]) == sorted(PARADAS)


def test_dois_opt_nunca_piora(cenario):
    _, matriz = cenario
    inicial = vizinho_mais_proximo("Centro", PARADAS, matriz)
    assert custo_rota(dois_opt(inicial, matriz), matriz) <= custo_rota(inicial, matriz)


def test_rota_otimizada_proxima_do_otimo(cenario):
    """Com 6 paradas dá para testar todas as 720 ordens (força bruta)."""
    _, matriz = cenario
    otimo = min(custo_rota(["Centro", *p, "Centro"], matriz) for p in permutations(PARADAS))
    heuristica = custo_rota(dois_opt(vizinho_mais_proximo("Centro", PARADAS, matriz), matriz), matriz)
    assert heuristica <= otimo * 1.10


def test_caminho_expandido_e_valido(cenario):
    grafo, matriz = cenario
    rota = vizinho_mais_proximo("Centro", PARADAS, matriz)
    caminho = expandir_rota(rota, matriz)
    assert all(b in grafo.adj[a] for a, b in zip(caminho, caminho[1:]))
    assert grafo.custo_caminho(caminho, "tempo_min") == pytest.approx(custo_rota(rota, matriz))


def test_kmeans_respeita_k_minimo_da_capacidade():
    grafo = carregar_grafo()
    coords = [grafo.posicoes[n] for n in grafo.nos]
    k, _ = escolher_k(coords, capacidade=6)
    assert k >= 5
    rotulos, centroides = agrupar(coords, k)
    assert len(set(rotulos)) == k == len(centroides)
