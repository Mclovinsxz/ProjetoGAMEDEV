# Custo de adotar uma grade de pixel art

Levantamento do que o item 4 custa de fato, medido sobre o projeto, para que a
decisão de grade seja tomada com o número na mão.

## 1. O ponto de partida não é neutro

Antes de falar em redesenhar arte, três medições mostram que o jogo **hoje**
já não renderiza pixel art de forma consistente.

### Zoom de câmera não inteiro

As cinco fases de plataforma executam `ZoomCamera 1.4`. Com fator 1,4 cada
pixel do sprite é reamostrado: alguns viram um pixel de tela, outros viram
dois. É o que produz o tremor e a borda irregular típicos de pixel art
escalada fora de múltiplo inteiro.

Isso vale para a arte atual, qualquer que seja a resolução dela. Nenhuma
mudança de asset conserta enquanto o zoom for 1,4.

### Maioria das instâncias em escala não inteira

Das 468 instâncias posicionadas nas cinco fases, **291 (62%) estão em escala
não inteira**. As mais frequentes:

| escala (L × A) | instâncias |
| --- | --- |
| 1,0 × 1,0 | 177 |
| 1,51 × 1,5 | 44 |
| 0,77 × 1,0 | 22 |
| 1,0 × 1,03 | 14 |
| 0,58 × 0,58 | 10 |
| 0,64 × 0,64 | 8 |

### O próprio player

Sprite nativo de 100×100, posicionado em todas as cinco fases com
`customSize` em **112 × 103** — escala 1,12 × 1,03, nem inteira nem uniforme
entre largura e altura. Com o zoom de 1,4, o player chega à tela em 157 × 144.

## 2. Inventário de arte

347 imagens distintas são usadas como quadro de sprite no jogo.

| lado maior | arquivos | peso | o que precisa |
| --- | --- | --- | --- |
| até 32 px | 56 | 0,1 MB | já serve |
| 33 a 64 px | 80 | 0,0 MB | já serve |
| 65 a 128 px | 84 | 0,2 MB | reduzir ~2× |
| 129 a 256 px | 42 | 0,2 MB | reduzir ~4× |
| 257 a 512 px | 36 | 2,0 MB | reduzir ~8× |
| acima de 512 px | 49 | 26,1 MB | reautorar |

- **136 (39%)** já estão na escala de pixel art.
- **162 (46%)** podem ser reduzidas com nearest e ajuste de paleta.
- **49 (14%)** precisam ser redesenhadas: são fotografia e arte vetorial
  grande, de `teresina pi.png` em 5000×5000 aos monumentos entre 600 e 2000 px.

Reduzir não é automático: baixar de 256 px para 32 px com nearest costuma
exigir retoque à mão para a silhueta continuar legível. Conte as 162 como
trabalho de retoque, não de conversão em lote.

## 3. Geometria que acompanha a mudança de grade

Mudar a resolução virtual reescala o mundo, e o mundo está escrito em dois
lugares:

- **1188 instâncias** posicionadas em todas as cenas do jogo
- **274 parâmetros de evento** que são número literal — coordenadas de
  respawn (`x = 4280`, `y = 840`), deslocamento de câmera (`player.X()+400`),
  limites e forças

Dividir a grade por 4 significa dividir esses dois conjuntos por 4.

## 4. As opções, com o custo de cada uma

### A — Grade 480×270, escala 4× (Fire Red de verdade)

Resolução do jogo em 480×270, zoom 1, canvas escalado 4× com nearest para
1920×1080. Tiles de 16, player de 32×32.

- Arte: 49 reautoradas, 162 retocadas, e as 136 restantes revistas para caírem
  na grade de 16
- Geometria: 1188 instâncias e 274 números divididos por 4
- Fidelidade ao FireRed: alta

É refazer a arte do jogo. Entrega o estilo pedido na forma mais pura e é, de
longe, o mais caro.

### B — Grade 960×540, escala 2×

Tiles de 32, player de 64×64.

- Arte: 49 reautoradas, ~78 retocadas (as acima de 256 px); tudo até 128 px já
  serve
- Geometria: dividida por 2
- Fidelidade: traço mais fino que o FireRed, ainda claramente pixel art

Aproveita os 220 arquivos que já estão em 128 px ou menos. Custa cerca de
metade de A.

### C — Consistência de pixel sem mudar a grade

Mantém 1920×1080 e a arte atual. Corrige só o que quebra a nitidez: zoom
inteiro e as 291 instâncias em escala não inteira.

- Arte nova: **nenhuma**
- Geometria: as 291 instâncias, mais revisão de enquadramento

O porém: trocar o zoom muda o que cabe na tela. Hoje, com 1,4, a área visível
é de 1371×771 unidades de mundo. Com zoom 1 passa a 1920×1080 e o jogador vê
além dos limites da fase; com zoom 2 cai para 960×540 e aperta demais. Ou seja,
C não é só ajuste numérico: exige revisar limites de câmera e enquadramento das
cinco fases.

### D — Primeiro a camada de UI, a grade depois

A metade didática do requisito — texto legível para criança em projetor — não
depende da grade do mundo. Pode ser feita agora:

- Camada de UI em 1080p nativo, fora do zoom da câmera
- Fonte legível em tamanho confortável para leitura a distância
- Moldura de caixa de diálogo continua pixel art; o texto dentro, não

Arte nova: nenhuma. Não mexe em instância nem em coordenada. E é o item que
resolve o gargalo de sala de aula, que é o objetivo do projeto.

## 5. Recomendação

**D agora, B como alvo.**

D entrega o ganho pedagógico — que é a razão de existir do projeto — sem
custo de arte e sem tocar na geometria. B é o alvo realista para o traço de
pixel: aproveita os 220 arquivos que já estão em 128 px ou menos, contra os
136 que A aproveitaria, e corta pela metade o retoque.

A só compensa se a fidelidade ao FireRed for requisito, e não preferência.

C, isolada, é a pior relação custo/benefício: exige revisar o enquadramento
das cinco fases sem entregar nem a legibilidade de D nem o traço de B.
