"""Agrupamento das entregas em zonas com K-Means (aprendizado não supervisionado).

Cada zona vira a rota de um entregador. O número de zonas (k) é escolhido assim:
1. k mínimo = ceil(paradas / capacidade) — nenhum entregador deve receber paradas demais;
2. entre k mínimo e k máximo, escolhe o k com maior coeficiente de silhueta
   (grupos compactos e bem separados). A inércia (método do cotovelo) também é registrada.
"""
import math

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

SEMENTE = 42


def avaliar_k(coordenadas, k_min=2, k_max=8):
    """Inércia e silhueta para cada k (base dos gráficos de cotovelo/silhueta)."""
    coordenadas = np.asarray(coordenadas)
    k_max = min(k_max, len(coordenadas) - 1)
    resultados = []
    for k in range(k_min, k_max + 1):
        modelo = KMeans(n_clusters=k, n_init=20, random_state=SEMENTE).fit(coordenadas)
        resultados.append({
            "k": k, "inercia": modelo.inertia_,
            "silhueta": silhouette_score(coordenadas, modelo.labels_),
        })
    return resultados


def escolher_k(coordenadas, capacidade=6, k_max=8):
    k_min = max(2, math.ceil(len(coordenadas) / capacidade))
    avaliacoes = avaliar_k(coordenadas, 2, max(k_max, k_min))
    candidatos = [a for a in avaliacoes if a["k"] >= k_min] or avaliacoes[-1:]
    melhor = max(candidatos, key=lambda a: a["silhueta"])
    return melhor["k"], avaliacoes


def agrupar(coordenadas, k):
    """Devolve (rótulo de cada ponto, centróides)."""
    modelo = KMeans(n_clusters=k, n_init=20, random_state=SEMENTE).fit(np.asarray(coordenadas))
    return modelo.labels_, modelo.cluster_centers_
