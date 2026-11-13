# Roteiro do vídeo pitch (~3 minutos)

Dica: grave a tela com o README e a pasta `outputs/` abertos. Cada bloco traz **o que mostrar** e **o que falar**.
Velocidade de fala natural: ~140 palavras por minuto.

---

## 1. O problema (0:00 – 0:30)

**Mostrar:** título do README.

**Falar:**
> "A Sabor Express é um delivery da região central que sofre com atrasos no horário de pico. Hoje as rotas são decididas pela experiência de cada entregador: eles cruzam a cidade, gastam mais combustível e o cliente espera demais. Meu objetivo foi usar algoritmos de Inteligência Artificial para sugerir rotas melhores."

## 2. Como modelei a cidade (0:30 – 0:55)

**Mostrar:** `outputs/mapa_grafo.png`.

**Falar:**
> "Representei a cidade como um grafo: 30 bairros são os nós e as ruas são as arestas. O peso de cada rua é o tempo de viagem, que considera a distância, se é rua ou avenida e o trânsito, que é mais pesado perto do Centro. As setas vermelhas são ruas de mão única, então o grafo é direcionado. O restaurante é a estrela no Centro."

## 3. Busca do menor caminho (0:55 – 1:35)

**Mostrar:** `outputs/exemplo_busca.png` e depois `outputs/comparacao_algoritmos.png`.

**Falar:**
> "Para ir de um ponto a outro, implementei do zero quatro algoritmos. O BFS acha o caminho com menos ruas, mas ignora o tempo. O DFS pega o primeiro caminho que encontra, e chega a ser três vezes pior. O Dijkstra e o A* sempre acham o caminho mais rápido. A diferença é que o A* usa uma heurística, a distância em linha reta até o destino, para ir direto na direção certa. Testando todos os 870 pares de bairros, o A* achou o ótimo em 100% dos casos expandindo 29% menos nós que o Dijkstra. Por isso o A* é o motor das rotas."

## 4. Agrupamento e rotas (1:35 – 2:15)

**Mostrar:** `outputs/clusters.png`, depois rodar `python src/main.py` no terminal por alguns segundos.

**Falar:**
> "No pico chegam 40 pedidos. Em vez de distribuir por ordem de chegada, uso o K-Means para dividir as entregas em zonas próximas, uma por entregador. O número de zonas foi escolhido pela capacidade de cada entregador e pelo coeficiente de silhueta, e deu quatro. Dentro de cada zona, monto a rota começando pelo vizinho mais próximo e melhorando com o 2-opt, que inverte trechos enquanto a rota encurtar. O A* calcula o custo entre cada par de paradas."

## 5. Resultados e próximos passos (2:15 – 3:00)

**Mostrar:** `outputs/rotas_manual_vs_otimizado.png` e `outputs/comparacao_cenarios.png`.

**Falar:**
> "À esquerda, o cenário manual: os entregadores atravessam a cidade inteira. À direita, a Rota Inteligente: cada um fica na sua região. A distância total caiu de 247 para 59 quilômetros, 76% a menos, e a espera média do cliente caiu de 83 para 21 minutos. Separando as técnicas, o agrupamento é o que mais contribui, e junto com o roteamento o ganho é máximo.
> As limitações são o mapa fictício e o trânsito fixo. Os próximos passos seriam usar mapas reais, trânsito em tempo real e zonas com limite de capacidade, como faz o sistema ORION da UPS. Obrigado!"

---

**Checklist antes de publicar:** vídeo com no máximo 4 minutos · postado no YouTube (pode ser não listado) · link enviado para avaliação.
