"""Gera os dados sintéticos (e reprodutíveis) da região central atendida pela Sabor Express.

Saídas em /data:
- bairros.csv : nós do grafo (bairros) com coordenadas em km.
- ruas.csv    : arestas (ruas) com distância, tipo de via, trânsito, tempo e sentido.
- pedidos.csv : pedidos de um horário de pico (almoço).

Uso: python src/gerar_dados.py [--seed 42] [--pedidos 40]
"""
import argparse
import math
import random
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "data"

NOMES = [
    "Vila Nova", "Jardim das Flores", "Bela Vista", "Boa Esperança", "São José", "Santa Luzia",
    "Vila Rica", "Alto da Serra", "Parque das Águas", "Jardim América", "Vila Operária", "Nova Aurora",
    "Morada do Sol", "Recanto Verde", "Centro", "Jardim Primavera", "Vila Esperança", "Bairro Industrial",
    "Cidade Alta", "Cidade Baixa", "Vila do Porto", "Jardim Europa", "Santa Rita", "São Pedro",
    "Vila Real", "Monte Alegre", "Bosque", "Campo Belo", "Vista Alegre", "Planalto",
]
LINHAS, COLUNAS = 5, 6          # grade 5 x 6 = 30 bairros
ESPACO_KM = 1.2                 # distância média entre bairros vizinhos
LINHA_AVENIDA, COLUNA_AVENIDA = 2, 2   # avenidas que cruzam o Centro
VELOCIDADE = {"avenida": 40.0, "rua": 25.0}   # km/h
VELOCIDADE_MAXIMA = max(VELOCIDADE.values())


def gerar_bairros(rng):
    linhas = []
    for i, nome in enumerate(NOMES):
        r, c = divmod(i, COLUNAS)
        x = c * ESPACO_KM + rng.uniform(-0.3, 0.3)
        y = (LINHAS - 1 - r) * ESPACO_KM + rng.uniform(-0.3, 0.3)
        linhas.append({"bairro": nome, "x_km": round(x, 3), "y_km": round(y, 3), "linha": r, "coluna": c})
    return pd.DataFrame(linhas)


def _fortemente_conexo(nomes, arestas):
    """Verifica se todo bairro alcança todos os outros (respeitando mão única)."""
    adj = {n: set() for n in nomes}
    for a in arestas:
        adj[a["origem"]].add(a["destino"])
        if not a["mao_unica"]:
            adj[a["destino"]].add(a["origem"])
    for adj_usada in (adj, {n: {o for o in nomes if n in adj[o]} for n in nomes}):
        visitados, pilha = {nomes[0]}, [nomes[0]]
        while pilha:
            for v in adj_usada[pilha.pop()]:
                if v not in visitados:
                    visitados.add(v)
                    pilha.append(v)
        if len(visitados) != len(nomes):
            return False
    return True


def gerar_ruas(bairros, rng):
    pos = {b.bairro: (b.x_km, b.y_km) for b in bairros.itertuples()}
    grade = {(b.linha, b.coluna): b.bairro for b in bairros.itertuples()}
    centro = pos["Centro"]
    candidatas = []
    for (r, c), nome in grade.items():
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            viz = grade.get((r + dr, c + dc))
            if viz is None:
                continue
            diagonal = dr != 0 and dc != 0
            if diagonal and rng.random() > 0.25:      # poucas ruas diagonais
                continue
            if not diagonal and rng.random() < 0.08:  # algumas ruas inexistentes (praças, rios...)
                continue
            avenida = (dr == 0 and r == LINHA_AVENIDA) or (dc == 0 and c == COLUNA_AVENIDA)
            candidatas.append((nome, viz, avenida))

    for _ in range(100):
        arestas = []
        for a, b, avenida in candidatas:
            reta = math.dist(pos[a], pos[b])
            distancia = reta * rng.uniform(1.05, 1.35)          # ruas não são linhas retas
            tipo = "avenida" if avenida else "rua"
            meio = ((pos[a][0] + pos[b][0]) / 2, (pos[a][1] + pos[b][1]) / 2)
            perto_centro = math.dist(meio, centro) < 1.8
            transito = round(rng.uniform(1.4, 1.8) if perto_centro else rng.uniform(1.0, 1.25), 2)
            tempo = distancia / VELOCIDADE[tipo] * 60 * transito
            mao_unica = tipo == "rua" and rng.random() < 0.15
            if mao_unica and rng.random() < 0.5:
                a, b = b, a
            arestas.append({
                "origem": a, "destino": b, "distancia_km": round(distancia, 3), "tipo_via": tipo,
                "velocidade_kmh": VELOCIDADE[tipo], "fator_transito": transito,
                "tempo_min": round(tempo, 2), "mao_unica": mao_unica,
            })
        if _fortemente_conexo(list(pos), arestas):
            return pd.DataFrame(arestas)
    raise RuntimeError("Não foi possível gerar um grafo fortemente conexo.")


def gerar_pedidos(bairros, rng, quantidade):
    destinos = [n for n in bairros.bairro if n != "Centro"]   # o restaurante fica no Centro
    pedidos = []
    for i in range(quantidade):
        minutos = 11 * 60 + 30 + rng.randint(0, 59)   # pico do almoço: 11:30 às 12:29
        pedidos.append({"bairro": rng.choice(destinos), "horario": f"{minutos // 60:02d}:{minutos % 60:02d}"})
    pedidos.sort(key=lambda p: p["horario"])
    return pd.DataFrame(
        [{"pedido_id": f"P{i + 1:03d}", **p} for i, p in enumerate(pedidos)],
        columns=["pedido_id", "horario", "bairro"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--pedidos", type=int, default=40)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    PASTA_DADOS.mkdir(exist_ok=True)
    bairros = gerar_bairros(rng)
    ruas = gerar_ruas(bairros, rng)
    pedidos = gerar_pedidos(bairros, rng, args.pedidos)
    bairros.to_csv(PASTA_DADOS / "bairros.csv", index=False)
    ruas.to_csv(PASTA_DADOS / "ruas.csv", index=False)
    pedidos.to_csv(PASTA_DADOS / "pedidos.csv", index=False)
    print(f"{len(bairros)} bairros, {len(ruas)} ruas ({int(ruas.mao_unica.sum())} de mão única), "
          f"{len(pedidos)} pedidos salvos em {PASTA_DADOS.relative_to(RAIZ)}/")


if __name__ == "__main__":
    main()
