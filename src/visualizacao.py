"""Gráficos e mapas gerados pelo projeto (salvos em /outputs)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

CORES = ["#2a78d6", "#e8762c", "#2e9e5b", "#c23b5a", "#7b54c9", "#b08a1e", "#1aa3a3", "#6b6b6b"]
COR_RUA, COR_AVENIDA, COR_MAO_UNICA = "#c9ced6", "#8a93a3", "#d64545"


def _desenhar_base(ax, grafo, rotulos=True, destaque=None):
    pos = grafo.posicoes
    desenhadas = set()
    for a, vizinhos in grafo.adj.items():
        for b, rua in vizinhos.items():
            if (b, a) in desenhadas:
                continue
            desenhadas.add((a, b))
            (x1, y1), (x2, y2) = pos[a], pos[b]
            if rua["mao_unica"]:
                ax.annotate("", xy=(x2, y2), xytext=(x1, y1), zorder=1,
                            arrowprops=dict(arrowstyle="-|>", color=COR_MAO_UNICA, lw=1.2,
                                            shrinkA=7, shrinkB=7, mutation_scale=11))
            else:
                avenida = rua["tipo_via"] == "avenida"
                ax.plot([x1, x2], [y1, y2], color=COR_AVENIDA if avenida else COR_RUA,
                        lw=3 if avenida else 1.4, zorder=1, solid_capstyle="round")
    xs, ys = zip(*pos.values())
    ax.scatter(xs, ys, s=40, color="white", edgecolor="#555", zorder=3)
    x, y = pos["Centro"]
    ax.scatter([x], [y], s=320, marker="*", color="#f2b705", edgecolor="#333", zorder=6)
    if rotulos:
        for n, (x, y) in pos.items():
            ax.text(x, y - 0.22, n, fontsize=6.5, ha="center", va="top", color="#333", zorder=7)
    ax.set_aspect("equal")
    ax.set_xticks([]), ax.set_yticks([])
    for lado in ax.spines.values():
        lado.set_visible(False)


def _legenda_mapa(ax, extras=()):
    itens = [
        Line2D([], [], color=COR_AVENIDA, lw=3, label="Avenida (40 km/h)"),
        Line2D([], [], color=COR_RUA, lw=1.4, label="Rua (25 km/h)"),
        Line2D([], [], color=COR_MAO_UNICA, lw=1.2, label="Mão única (→)"),
        Line2D([], [], marker="*", color="#f2b705", markeredgecolor="#333", ms=13, lw=0,
               label="Restaurante Sabor Express"),
        *extras,
    ]
    ax.legend(handles=itens, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=3, fontsize=8, frameon=False)


def _salvar(fig, caminho):
    fig.savefig(caminho, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def mapa_grafo(grafo, caminho):
    fig, ax = plt.subplots(figsize=(10, 8.5))
    _desenhar_base(ax, grafo)
    ax.set_title(f"Grafo da região central — {len(grafo.nos)} bairros, {grafo.num_arestas()} arestas direcionadas",
                 fontsize=12)
    _legenda_mapa(ax)
    _salvar(fig, caminho)


def exemplo_busca(grafo, resultados, caminho):
    fig, eixos = plt.subplots(2, 2, figsize=(13, 11))
    for ax, r, cor in zip(eixos.flat, resultados, CORES):
        _desenhar_base(ax, grafo, rotulos=False)
        xs, ys = zip(*(grafo.posicoes[n] for n in r.caminho))
        ax.plot(xs, ys, color=cor, lw=4, alpha=0.85, zorder=4)
        ax.scatter([xs[0], xs[-1]], [ys[0], ys[-1]], s=110, color=cor, edgecolor="#222", zorder=5)
        ax.set_title(f"{r.algoritmo}: {r.custo:.1f} min | {len(r.caminho) - 1} ruas | "
                     f"{r.nos_expandidos} nós expandidos", fontsize=11)
    o, d = resultados[0].caminho[0], resultados[0].caminho[-1]
    fig.suptitle(f"Mesmo trajeto, quatro algoritmos: {o} → {d}", fontsize=14)
    _salvar(fig, caminho)


def comparacao_algoritmos(resumo, caminho):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    cores = CORES[:len(resumo)]
    ax1.bar(resumo.algoritmo, resumo.nos_expandidos_medio, color=cores)
    ax1.set_title("Nós expandidos (média)  ↓ melhor")
    ax2.bar(resumo.algoritmo, resumo.excesso_medio_pct, color=cores)
    ax2.set_title("Custo acima do ótimo (%, média)  ↓ melhor")
    for ax, col, fmt in ((ax1, "nos_expandidos_medio", "{:.1f}"), (ax2, "excesso_medio_pct", "{:.1f}%")):
        for i, v in enumerate(resumo[col]):
            ax.text(i, v, fmt.format(v), ha="center", va="bottom", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    _salvar(fig, caminho)


def escolha_k(avaliacoes, k_escolhido, caminho):
    ks = [a["k"] for a in avaliacoes]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.2))
    ax1.plot(ks, [a["inercia"] for a in avaliacoes], "o-", color=CORES[0])
    ax1.set_title("Método do cotovelo (inércia)")
    ax2.plot(ks, [a["silhueta"] for a in avaliacoes], "o-", color=CORES[1])
    ax2.set_title("Coeficiente de silhueta  ↑ melhor")
    for ax in (ax1, ax2):
        ax.axvline(k_escolhido, color="#888", ls="--", lw=1)
        ax.set_xlabel("k (número de zonas / entregadores)")
        ax.spines[["top", "right"]].set_visible(False)
    _salvar(fig, caminho)


def mapa_clusters(grafo, paradas, rotulos, centroides, pedidos_por_parada, caminho):
    fig, ax = plt.subplots(figsize=(10, 8.5))
    _desenhar_base(ax, grafo)
    for p, rot in zip(paradas, rotulos):
        x, y = grafo.posicoes[p]
        ax.scatter([x], [y], s=60 + 45 * pedidos_por_parada[p], color=CORES[rot], edgecolor="#222", zorder=5)
    for i, (cx, cy) in enumerate(centroides):
        ax.scatter([cx], [cy], marker="X", s=180, color=CORES[i], edgecolor="#222", zorder=6)
    extras = [Line2D([], [], marker="o", color=CORES[i], lw=0, ms=9, label=f"Zona {i + 1}")
              for i in range(len(centroides))]
    extras.append(Line2D([], [], marker="X", color="#555", lw=0, ms=10, label="Centróide"))
    ax.set_title("Zonas de entrega (K-Means) — tamanho do ponto = nº de pedidos", fontsize=12)
    _legenda_mapa(ax, extras)
    _salvar(fig, caminho)


def mapa_rotas(grafo, caminhos, titulos, caminho, titulo_geral):
    fig, eixos = plt.subplots(1, len(caminhos), figsize=(9 * len(caminhos), 8.5))
    for ax, rotas, titulo in zip(eixos, caminhos, titulos):
        _desenhar_base(ax, grafo, rotulos=False)
        for i, (paradas, trajeto) in enumerate(rotas):
            deslocamento = (i - len(rotas) / 2) * 0.04     # separa rotas que usam a mesma rua
            xs = [grafo.posicoes[n][0] + deslocamento for n in trajeto]
            ys = [grafo.posicoes[n][1] + deslocamento for n in trajeto]
            ax.plot(xs, ys, color=CORES[i], lw=2.6, alpha=0.85, zorder=4, label=f"Entregador {i + 1}")
            px, py = zip(*(grafo.posicoes[p] for p in paradas))
            ax.scatter(px, py, s=55, color=CORES[i], edgecolor="#222", zorder=5)
        ax.set_title(titulo, fontsize=12)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=4, fontsize=9, frameon=False)
    fig.suptitle(titulo_geral, fontsize=14, y=0.9)
    _salvar(fig, caminho)


def comparacao_cenarios(cenarios, caminho):
    """cenarios: lista de (rótulo curto, dicionário de resumo). O primeiro é o baseline e o último o otimizado."""
    metricas = [("distancia_total_km", "Distância total (km)"), ("tempo_total_min", "Tempo total (min)"),
                ("maior_rota_min", "Maior rota (min)"), ("espera_media_cliente_min", "Espera média do cliente (min)")]
    cores = ["#9aa3b0", "#c3c9d2", "#c3c9d2", CORES[2]]
    fig, eixos = plt.subplots(1, len(metricas), figsize=(19, 5))
    fig.subplots_adjust(wspace=0.3)
    for ax, (col, titulo) in zip(eixos, metricas):
        valores = [c[1][col] for c in cenarios]
        ax.bar(range(len(cenarios)), valores, color=cores[:len(cenarios)])
        ax.set_xticks(range(len(cenarios)), [c[0] for c in cenarios], fontsize=8)
        for i, v in enumerate(valores):
            ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
        ganho = (1 - valores[-1] / valores[0]) * 100
        ax.set_title(f"{titulo}\n{ganho:.1f}% menor que o manual", fontsize=10.5)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Manual (ordem de chegada) x Rota Inteligente (K-Means + A* + 2-opt)", fontsize=13, y=1.04)
    _salvar(fig, caminho)
