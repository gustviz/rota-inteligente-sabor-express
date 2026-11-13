"""Métricas de avaliação: comparação dos algoritmos de busca e das rotas (baseline x otimizado)."""
from itertools import permutations

import pandas as pd

from busca import ALGORITMOS
from roteamento import expandir_rota


def comparar_algoritmos(grafo, peso="tempo_min", pares=None):
    """Roda os 4 algoritmos em todos os pares origem-destino e resume os resultados.

    - custo_medio: custo médio do caminho encontrado.
    - excesso_medio_pct: quanto o caminho é pior que o ótimo (Dijkstra), em %.
    - otimo_pct: em quantos % dos pares o algoritmo achou o caminho ótimo.
    - nos_expandidos_medio / tempo_medio_ms: esforço computacional.
    """
    pares = pares or list(permutations(grafo.nos, 2))
    linhas = []
    for o, d in pares:
        otimo = ALGORITMOS["Dijkstra"](grafo, o, d, peso).custo
        for nome, func in ALGORITMOS.items():
            r = func(grafo, o, d, peso)
            linhas.append({
                "algoritmo": nome, "origem": o, "destino": d, "custo": r.custo,
                "excesso_pct": (r.custo / otimo - 1) * 100, "otimo": abs(r.custo - otimo) < 1e-6,
                "nos_expandidos": r.nos_expandidos, "tempo_ms": r.tempo_ms,
            })
    detalhe = pd.DataFrame(linhas)
    resumo = detalhe.groupby("algoritmo", sort=False).agg(
        custo_medio=("custo", "mean"),
        excesso_medio_pct=("excesso_pct", "mean"),
        otimo_pct=("otimo", lambda s: s.mean() * 100),
        nos_expandidos_medio=("nos_expandidos", "mean"),
        tempo_medio_ms=("tempo_ms", "mean"),
    ).round(3).reset_index()
    return resumo, detalhe


def avaliar_rota(grafo, rota, matriz, pedidos_por_parada):
    """Métricas de uma rota: paradas, pedidos, tempo, distância e espera dos clientes."""
    caminho = expandir_rota(rota, matriz)
    tempo_acumulado, esperas = 0.0, []
    for a, b in zip(rota, rota[1:]):
        tempo_acumulado += grafo.custo_caminho(matriz[(a, b)][1], "tempo_min")
        esperas += [tempo_acumulado] * pedidos_por_parada.get(b, 0)
        pedidos_por_parada = {**pedidos_por_parada, b: 0}   # parada repetida não conta duas vezes
    return {
        "paradas": len(rota) - 2,
        "pedidos": len(esperas),
        "tempo_min": grafo.custo_caminho(caminho, "tempo_min"),
        "distancia_km": grafo.custo_caminho(caminho, "distancia_km"),
        "esperas": esperas,
    }


def resumir_cenario(nome, avaliacoes):
    """Agrega as rotas de todos os entregadores de um cenário."""
    esperas = [e for a in avaliacoes for e in a["esperas"]]
    return {
        "cenario": nome,
        "entregadores": len(avaliacoes),
        "pedidos": sum(a["pedidos"] for a in avaliacoes),
        "distancia_total_km": round(sum(a["distancia_km"] for a in avaliacoes), 2),
        "tempo_total_min": round(sum(a["tempo_min"] for a in avaliacoes), 2),
        "maior_rota_min": round(max(a["tempo_min"] for a in avaliacoes), 2),
        "espera_media_cliente_min": round(sum(esperas) / len(esperas), 2),
        "espera_maxima_cliente_min": round(max(esperas), 2),
    }


def ganho_percentual(baseline, otimizado, colunas):
    return {c: round((1 - otimizado[c] / baseline[c]) * 100, 1) for c in colunas}
