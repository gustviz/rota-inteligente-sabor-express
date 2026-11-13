"""Roteamento com múltiplas paradas: menor caminho passando por vários pontos de entrega.

1. Matriz de custos: A* entre todos os pares (restaurante + paradas).
   É assimétrica por causa das ruas de mão única.
2. Rota inicial: heurística do vizinho mais próximo.
3. Melhoria: 2-opt (inverte trechos da rota enquanto o custo total diminuir).
A rota sai do restaurante e volta para ele.
"""
from busca import a_estrela


def matriz_custos(grafo, pontos, peso="tempo_min"):
    """{(a, b): (custo, caminho)} para todo par de pontos distintos."""
    matriz = {}
    for a in pontos:
        for b in pontos:
            if a != b:
                r = a_estrela(grafo, a, b, peso)
                matriz[(a, b)] = (r.custo, r.caminho)
    return matriz


def custo_rota(rota, matriz):
    return sum(matriz[(a, b)][0] for a, b in zip(rota, rota[1:]))


def vizinho_mais_proximo(deposito, paradas, matriz):
    rota, restantes = [deposito], set(paradas)
    while restantes:
        proximo = min(restantes, key=lambda p: (matriz[(rota[-1], p)][0], p))
        rota.append(proximo)
        restantes.remove(proximo)
    return rota + [deposito]


def dois_opt(rota, matriz):
    """Melhoria local 2-opt. Recalcula o custo completo (necessário em grafos assimétricos)."""
    melhor, melhor_custo = rota[:], custo_rota(rota, matriz)
    melhorou = True
    while melhorou:
        melhorou = False
        for i in range(1, len(melhor) - 2):
            for j in range(i + 1, len(melhor) - 1):
                candidata = melhor[:i] + melhor[i:j + 1][::-1] + melhor[j + 1:]
                custo = custo_rota(candidata, matriz)
                if custo < melhor_custo - 1e-9:
                    melhor, melhor_custo, melhorou = candidata, custo, True
    return melhor


def planejar_rota(deposito, paradas, matriz, otimizar=True):
    rota = vizinho_mais_proximo(deposito, paradas, matriz)
    return dois_opt(rota, matriz) if otimizar else rota


def rota_em_ordem(deposito, paradas, matriz):
    """Rota 'manual' (baseline): visita as paradas na ordem de chegada dos pedidos."""
    return [deposito] + list(paradas) + [deposito]


def expandir_rota(rota, matriz):
    """Converte a sequência de paradas no caminho completo, bairro a bairro."""
    caminho = [rota[0]]
    for a, b in zip(rota, rota[1:]):
        caminho += matriz[(a, b)][1][1:]
    return caminho
