"""Rota Inteligente — Sabor Express.

Fluxo completo:
1. Carrega o grafo da cidade e os pedidos do horário de pico.
2. Compara BFS, DFS, Dijkstra e A* em todos os pares de bairros.
3. Agrupa as entregas em zonas com K-Means (uma zona por entregador).
4. Monta a rota de cada entregador (A* + vizinho mais próximo + 2-opt).
5. Compara com o cenário manual (pedidos na ordem de chegada) e salva tabelas e gráficos em /outputs.

Uso: python src/main.py [--peso tempo_min|distancia_km] [--capacidade 6] [--origem X --destino Y]
"""
import argparse
import math
from collections import Counter
from pathlib import Path

import pandas as pd

import visualizacao as vis
from agrupamento import agrupar, escolher_k
from busca import ALGORITMOS
from grafo import PESOS_VALIDOS, carregar_grafo, carregar_pedidos
from metricas import avaliar_rota, comparar_algoritmos, ganho_percentual, resumir_cenario
from roteamento import expandir_rota, matriz_custos, planejar_rota, rota_em_ordem

RAIZ = Path(__file__).resolve().parent.parent
SAIDAS = RAIZ / "outputs"
DEPOSITO = "Centro"


def secao(titulo):
    print(f"\n{'=' * 70}\n{titulo}\n{'=' * 70}")


def cenario_manual(pedidos, k):
    """Baseline: divide os pedidos, na ordem de chegada, em k lotes consecutivos."""
    tamanho = math.ceil(len(pedidos) / k)
    lotes = []
    for i in range(0, len(pedidos), tamanho):
        bairros = list(pedidos.bairro.iloc[i:i + tamanho])
        lotes.append((list(dict.fromkeys(bairros)), Counter(bairros)))   # remove paradas repetidas
    return lotes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--peso", choices=PESOS_VALIDOS, default="tempo_min", help="peso a minimizar")
    parser.add_argument("--capacidade", type=int, default=6, help="máximo desejado de paradas por entregador")
    parser.add_argument("--origem", default="Vila Nova", help="origem do exemplo de busca")
    parser.add_argument("--destino", default="Planalto", help="destino do exemplo de busca")
    args = parser.parse_args()
    SAIDAS.mkdir(exist_ok=True)
    unidade = "min" if args.peso == "tempo_min" else "km"

    # 1. Dados ---------------------------------------------------------------
    grafo = carregar_grafo()
    pedidos = carregar_pedidos()
    secao("1. DADOS")
    print(f"Grafo: {len(grafo.nos)} bairros, {grafo.num_arestas()} arestas direcionadas | "
          f"Pedidos: {len(pedidos)} | Restaurante: {DEPOSITO} | Peso otimizado: {args.peso}")
    vis.mapa_grafo(grafo, SAIDAS / "mapa_grafo.png")

    # 2. Algoritmos de busca -------------------------------------------------
    secao(f"2. BUSCA: {args.origem} -> {args.destino}")
    exemplo = [f(grafo, args.origem, args.destino, args.peso) for f in ALGORITMOS.values()]
    for r in exemplo:
        print(f"{r.algoritmo:9s} custo={r.custo:6.2f} {unidade} | ruas={len(r.caminho) - 1:2d} | "
              f"expandidos={r.nos_expandidos:2d} | {' -> '.join(r.caminho)}")
    vis.exemplo_busca(grafo, exemplo, SAIDAS / "exemplo_busca.png")

    resumo, _ = comparar_algoritmos(grafo, args.peso)
    print(f"\nComparação em todos os {len(grafo.nos) * (len(grafo.nos) - 1)} pares origem-destino:")
    print(resumo.to_string(index=False))
    resumo.to_csv(SAIDAS / "comparacao_algoritmos.csv", index=False)
    vis.comparacao_algoritmos(resumo, SAIDAS / "comparacao_algoritmos.png")

    # 3. Agrupamento (K-Means) -----------------------------------------------
    secao("3. AGRUPAMENTO DAS ENTREGAS (K-MEANS)")
    pedidos_por_parada = Counter(pedidos.bairro)
    paradas = sorted(pedidos_por_parada)
    coords = [grafo.posicoes[p] for p in paradas]
    k, avaliacoes = escolher_k(coords, capacidade=args.capacidade)
    print(f"{len(paradas)} paradas distintas | k mínimo pela capacidade = "
          f"{math.ceil(len(paradas) / args.capacidade)}")
    for a in avaliacoes:
        print(f"  k={a['k']}: inércia={a['inercia']:7.2f} silhueta={a['silhueta']:.3f}"
              f"{'  <- escolhido' if a['k'] == k else ''}")
    rotulos, centroides = agrupar(coords, k)
    vis.escolha_k(avaliacoes, k, SAIDAS / "escolha_k.png")
    vis.mapa_clusters(grafo, paradas, rotulos, centroides, pedidos_por_parada, SAIDAS / "clusters.png")

    # 4. Rotas otimizadas ----------------------------------------------------
    secao("4. ROTAS OTIMIZADAS (A* + VIZINHO MAIS PRÓXIMO + 2-OPT)")
    matriz = matriz_custos(grafo, [DEPOSITO] + paradas, args.peso)
    linhas_rotas, otimizadas, desenho_otimizado = [], [], []
    for z in range(k):
        zona = [p for p, r in zip(paradas, rotulos) if r == z]
        rota = planejar_rota(DEPOSITO, zona, matriz)
        aval = avaliar_rota(grafo, rota, matriz, pedidos_por_parada)
        otimizadas.append(aval)
        desenho_otimizado.append((zona, expandir_rota(rota, matriz)))
        print(f"Entregador {z + 1}: {aval['pedidos']:2d} pedidos, {aval['tempo_min']:5.1f} min, "
              f"{aval['distancia_km']:5.2f} km | {' -> '.join(rota)}")
        linhas_rotas.append({"entregador": z + 1, "cenario": "otimizado", "sequencia": " -> ".join(rota),
                             **{c: round(aval[c], 2) for c in ("paradas", "pedidos", "tempo_min", "distancia_km")}})

    # 5. Baseline x otimizado ------------------------------------------------
    secao("5. CENÁRIO MANUAL x ROTA INTELIGENTE")
    manuais, so_roteamento, desenho_manual = [], [], []
    for i, (lote, contagem) in enumerate(cenario_manual(pedidos, k)):
        rota = rota_em_ordem(DEPOSITO, lote, matriz)
        aval = avaliar_rota(grafo, rota, matriz, dict(contagem))
        manuais.append(aval)
        desenho_manual.append((lote, expandir_rota(rota, matriz)))
        linhas_rotas.append({"entregador": i + 1, "cenario": "manual", "sequencia": " -> ".join(rota),
                             **{c: round(aval[c], 2) for c in ("paradas", "pedidos", "tempo_min", "distancia_km")}})
        so_roteamento.append(avaliar_rota(grafo, planejar_rota(DEPOSITO, lote, matriz), matriz, dict(contagem)))
    pd.DataFrame(linhas_rotas).to_csv(SAIDAS / "rotas.csv", index=False)

    # Estudo de ablação: zonas K-Means, mas visitando na ordem de chegada dos pedidos
    primeiro_pedido = {b: i for i, b in reversed(list(enumerate(pedidos.bairro)))}
    so_agrupamento = []
    for z in range(k):
        zona = sorted((p for p, r in zip(paradas, rotulos) if r == z), key=primeiro_pedido.get)
        so_agrupamento.append(avaliar_rota(grafo, rota_em_ordem(DEPOSITO, zona, matriz), matriz, pedidos_por_parada))

    base = resumir_cenario("manual (ordem de chegada)", manuais)
    otim = resumir_cenario("rota inteligente", otimizadas)
    colunas = ["distancia_total_km", "tempo_total_min", "maior_rota_min",
               "espera_media_cliente_min", "espera_maxima_cliente_min"]
    ganhos = {"cenario": "redução manual -> inteligente (%)", "entregadores": "", "pedidos": "",
              **ganho_percentual(base, otim, colunas)}
    rot = resumir_cenario("só roteamento (lotes por chegada + 2-opt)", so_roteamento)
    agr = resumir_cenario("só agrupamento (K-Means + ordem de chegada)", so_agrupamento)
    tabela = pd.DataFrame([base, rot, agr, otim, ganhos])
    print(tabela.to_string(index=False))
    tabela.to_csv(SAIDAS / "metricas_manual_vs_otimizado.csv", index=False)
    vis.comparacao_cenarios([("Manual", base), ("Só\nrotas", rot), ("Só\nzonas", agr),
                             ("Rota\nInteligente", otim)], SAIDAS / "comparacao_cenarios.png")
    vis.mapa_rotas(grafo, [desenho_manual, desenho_otimizado],
                   [f"Manual — {base['distancia_total_km']:.1f} km, {base['tempo_total_min']:.0f} min",
                    f"Rota Inteligente — {otim['distancia_total_km']:.1f} km, {otim['tempo_total_min']:.0f} min"],
                   SAIDAS / "rotas_manual_vs_otimizado.png", f"Rotas dos {k} entregadores")

    print(f"\nArquivos gerados em {SAIDAS.relative_to(RAIZ)}/:")
    for arq in sorted(SAIDAS.iterdir()):
        print(f"  - {arq.name}")


if __name__ == "__main__":
    main()
