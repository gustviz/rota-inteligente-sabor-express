"""Algoritmos de busca implementados do zero: BFS, DFS, Dijkstra e A*.

Todos devolvem um `ResultadoBusca` com o caminho, o custo (no peso escolhido),
a quantidade de nós expandidos e o tempo de execução — usados na comparação.
"""
import heapq
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class ResultadoBusca:
    algoritmo: str
    caminho: list = field(default_factory=list)
    custo: float = float("inf")
    nos_expandidos: int = 0
    tempo_ms: float = 0.0

    @property
    def encontrou(self):
        return bool(self.caminho)


def _reconstruir(pais, destino):
    caminho = [destino]
    while pais[caminho[-1]] is not None:
        caminho.append(pais[caminho[-1]])
    return caminho[::-1]


def _finalizar(nome, grafo, pais, destino, expandidos, inicio, peso):
    res = ResultadoBusca(nome, nos_expandidos=expandidos, tempo_ms=(time.perf_counter() - inicio) * 1000)
    if destino in pais:
        res.caminho = _reconstruir(pais, destino)
        res.custo = grafo.custo_caminho(res.caminho, peso)
    return res


def bfs(grafo, origem, destino, peso="tempo_min"):
    """Busca em largura: menor número de ruas (ignora o peso). O(V + E)."""
    inicio = time.perf_counter()
    pais, fila, expandidos = {origem: None}, deque([origem]), 0
    while fila:
        atual = fila.popleft()
        expandidos += 1
        if atual == destino:
            break
        for viz, _ in grafo.vizinhos(atual):
            if viz not in pais:
                pais[viz] = atual
                fila.append(viz)
    return _finalizar("BFS", grafo, pais, destino, expandidos, inicio, peso)


def dfs(grafo, origem, destino, peso="tempo_min"):
    """Busca em profundidade: devolve o primeiro caminho encontrado (sem garantia de ótimo). O(V + E)."""
    inicio = time.perf_counter()
    pais, pilha, visitados, expandidos = {origem: None}, [origem], set(), 0
    while pilha:
        atual = pilha.pop()
        if atual in visitados:
            continue
        visitados.add(atual)
        expandidos += 1
        if atual == destino:
            break
        for viz, _ in reversed(grafo.vizinhos(atual)):   # reversed: explora em ordem alfabética
            if viz not in visitados:
                pais[viz] = atual
                pilha.append(viz)
    return _finalizar("DFS", grafo, pais, destino, expandidos, inicio, peso)


def _busca_custo(nome, grafo, origem, destino, peso, h):
    """Núcleo comum de Dijkstra (h = 0) e A* (h = heurística). O((V + E) log V)."""
    inicio = time.perf_counter()
    g = {origem: 0.0}
    pais = {origem: None}
    fronteira = [(h(origem, destino), 0.0, origem)]
    fechados, expandidos = set(), 0
    while fronteira:
        _, custo, atual = heapq.heappop(fronteira)
        if atual in fechados:
            continue
        fechados.add(atual)
        expandidos += 1
        if atual == destino:
            break
        for viz, rua in grafo.vizinhos(atual):
            novo = custo + rua[peso]
            if novo < g.get(viz, float("inf")):
                g[viz], pais[viz] = novo, atual
                heapq.heappush(fronteira, (novo + h(viz, destino), novo, viz))
    if destino not in fechados:
        pais.pop(destino, None)
    return _finalizar(nome, grafo, pais, destino, expandidos, inicio, peso)


def dijkstra(grafo, origem, destino, peso="tempo_min"):
    """Custo uniforme: caminho ótimo explorando em todas as direções."""
    return _busca_custo("Dijkstra", grafo, origem, destino, peso, lambda a, b: 0.0)


def a_estrela(grafo, origem, destino, peso="tempo_min"):
    """A*: f(n) = g(n) + h(n). Com h admissível, o caminho é ótimo e expande menos nós que Dijkstra."""
    return _busca_custo("A*", grafo, origem, destino, peso, grafo.heuristica(peso))


ALGORITMOS = {"BFS": bfs, "DFS": dfs, "Dijkstra": dijkstra, "A*": a_estrela}
