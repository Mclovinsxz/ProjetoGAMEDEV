# Diagnóstico Técnico — Piauí: Crônicas do Tempo

Levantamento feito sobre o estado atual do repositório, cruzado com o escopo
descrito na apresentação institucional do projeto.

## 1. O que o jogo é hoje

Plataforma educacional em GDevelop 5 (`com.unipGameDev.cronicasDoPiaui`), com o
objetivo de ensinar história do Piauí para alunos do Ensino Fundamental.

O loop pedagógico definido no projeto é:

> o jogador coleta informações ao longo das fases, e essas informações são
> usadas para responder um quiz dinâmico.

Estrutura implementada:

| Bloco | Cenas |
| --- | --- |
| Entrada | `tela-inicial`, `introduo`, `tela-de-instruo`, `tela-de-configurao` |
| Navegação | `tela_mapa_selecao_cidade` |
| Briefing por cidade | `pre_select_fase_*` (Teresina, Oeiras, Parnaíba, Campo Maior, SRN) |
| Plataforma | `fase_plataforma_*` (as mesmas 5 cidades) |
| Minigames | `minigame_escavacao`, `minigame_clickpoint_teresina`, `aquatico` |
| Avaliação | `quiz_game` |

Configuração de projeto: 1920x1080, `scaleMode: nearest`, `pixelsRounding: true`,
60 FPS, landscape. A base para pixel art já está correta.

O player é um objeto global com quatro comportamentos encadeados:
`PlatformerObjectBehavior`, `AdvancedJump`, `PlatformerCharacterAnimator` e
`SmoothCamera`.

Progresso é controlado por cinco variáveis globais booleanas
(`teresina_concluida`, `oeiras_concluida`, `parnaiba_concluida`,
`camporMaior_concluida`, `srn_concluida`) mais `cidade_atual`.

## 2. Problemas medidos

### 2.1 Recursos quebrados — 23 ocorrências (crítico)

23 dos 746 recursos declarados apontam para arquivos que não existem no
repositório. Entre eles, cinco têm **caminho absoluto do Windows da máquina de
um autor** gravado como nome do recurso:

```
G:\Meu Drive\Aespi\Projeto de extensão\...\box_item_coletar_2.png
G:\Meu Drive\Aespi\Projeto de extensão\...\pixelart.ttf
```

E quatro usam separador de caminho do Windows no nome do recurso
(`assets\player_run_1.png`), o que quebra em Linux e macOS.

Impacto: o projeto não é reproduzível fora da máquina original. Sprites de
corrida do player e a caixa de item coletado — ou seja, o feedback visual
central do loop de coleta — estão entre os ausentes.

### 2.2 Duplicação de lógica — 65% das fases

As cinco cenas de plataforma têm 38 a 40 eventos de topo cada. Comparando por
hash estrutural, **26 eventos são idênticos em pelo menos 4 das 5 cenas**, de
um total de 80 eventos distintos no conjunto.

Na prática: a mesma lógica de coleta, diálogo, morte, respawn e transição foi
copiada cinco vezes. Qualquer correção de regra de jogo precisa ser aplicada
cinco vezes, manualmente, sem garantia de consistência.

### 2.3 Assets — 569 PNGs, 85 MB, 95 pares duplicados

- **95 pares de arquivos byte a byte idênticos** com nomes diferentes
  (`catedral_oeiras.png` = `catedral_oeiras2.png` = `catedral_oeiras3.png`,
  `dialogue_box.png` = `dialogue_box2.png`, etc.).
- **28 arquivos em disco não referenciados** por nenhum recurso.
- Assets espalhados na raiz do repositório, sem hierarquia.

### 2.4 Resolução inconsistente — quebra o estilo pixel art

Distribuição do lado maior dos 569 PNGs:

| Lado maior | Arquivos |
| --- | --- |
| ate 32 px | 94 |
| ate 64 px | 122 |
| ate 128 px | 114 |
| ate 256 px | 112 |
| ate 512 px | 62 |
| ate 1024 px | 40 |
| acima de 1024 px | 25 |

Os 25 arquivos acima de 1024 px são fotografias e mapas redimensionados, não
pixel art:

```
10.0 MB  5000x5000  teresina pi.png
 4.8 MB  2048x1365  01-ChicoRasta_FormacoesRochosas_SerraDaCapivara...png
 1.4 MB  2835x2835  mapa_piaui_teresina_oeiras.png   (6 variações quase iguais)
```

Misturar sprites de 16 px com fundos fotográficos de 2835 px na mesma cena
produz o efeito oposto ao pretendido: a arte não lê como pixel art, lê como
imagem borrada ao lado de imagem nítida.

## 3. Decisão de motor: manter GDevelop

Avaliado o porte para outro motor. **Recomendação: não portar.**

### Por que não

1. **O motor foi escolhido pela composição da equipe, não por acaso.** O projeto
   tem três times — Negócio, Design e Dev — e a apresentação registra GDevelop
   como escolha deliberada para "facilitar a criação de jogos para pessoas que
   não têm experiência em programação". Portar para Godot ou Phaser transfere
   100% da manutenção para o time Dev. Em projeto acadêmico com rotatividade de
   turma, isso é o fim da manutenção.

2. **Nenhum problema medido acima é culpa do motor.** Recursos quebrados, lógica
   copiada cinco vezes, assets duplicados e resolução inconsistente existiriam
   igualmente em Godot ou Phaser. O porte não corrige nenhum deles e custa a
   reescrita de 21 cenas e 746 recursos.

3. **O teto técnico do GDevelop ainda não foi atingido.** A apresentação já
   registra uso de JavaScript customizado e extensões. O projeto usa 10
   extensões. Tudo que falta — câmera melhor, coyote time, feedback de UI,
   gerenciamento de estado — cabe dentro do GDevelop.

### Se o porte fosse obrigatório

| Opção | Viabilidade | Observação |
| --- | --- | --- |
| **Godot 4** | Melhor destino técnico | Melhor 2D pixel-perfect do mercado, exporta web/desktop/mobile. Porém: 21 cenas refeitas à mão, zero reaproveitamento dos eventos. |
| **Phaser 3 + TypeScript** | Único com caminho semi-automático | O projeto já é JSON declarativo; dá para escrever conversor de `layouts/*.json` para scene config. Mas os eventos (a lógica real) não convertem — reescrita manual mesmo assim. |
| **Unity** | Descartado | Overkill para 2D, build web pesado, licenciamento. |

Estimativa: porte ~6 a 10 semanas de desenvolvimento para chegar à paridade
atual. Refatoração dentro do GDevelop: ~2 semanas para um resultado visível
melhor que o atual.

## 4. Direção de arte: pixel art em duas camadas

O requisito tem duas metades que parecem conflitar: precisa ser **didático**
(legível para criança em sala de aula, muitas vezes em projetor) e precisa ter
**traço de pixel** (dinâmico, divertido). A solução é não resolver as duas na
mesma camada.

### Camada mundo — pixel art

Referência Pokémon FireRed (GBA): resolução nativa 240x160, tiles de 8x8
agrupados em metatiles de 16x16, personagem de overworld 16x32, paleta de 16
cores por bloco.

Adaptação para este projeto:

| Parâmetro | Valor |
| --- | --- |
| Resolução virtual de autoria | **480x270** |
| Escala de apresentação | **4x inteiro, nearest** → 1920x1080 |
| Tile | 16x16 |
| Personagem | 32x32 (2 tiles de altura) |
| Paleta | 32 a 48 cores por cena, definida antes de desenhar |

480x270 é o único valor que dá escala inteira exata para 1080p (×4) e para 720p
(×2.66 — não inteiro, mas o alvo é 1080p). Escala inteira é o que diferencia
pixel art nítida de pixel art borrada.

### Camada UI — legibilidade

Texto de quiz, diálogo, nome de monumento e instrução **não** devem ser
renderizados na camada pixelada escalada. Devem ser renderizados em 1920x1080
nativo, com fonte bitmap legível em tamanho confortável.

Motivo: o gargalo didático é a leitura. Fonte pixelada de 8 px escalada 4x em
projetor de sala de aula, com criança do Fundamental lendo de 5 metros, é
ilegível. A moldura da caixa de diálogo pode e deve ser pixel art — o texto
dentro dela, não.

GDevelop suporta isso nativamente: as cenas já usam camadas separadas
(`background` existe nas cinco fases de plataforma). Basta mais uma camada de UI
sem zoom aplicado.

### Fundos fotográficos

Os 25 arquivos acima de 1024 px precisam ser reautorados ou reprocessados:
downsample para a grade de 480x270 com nearest neighbor e redução de paleta.
Fotografia escalada não vira pixel art — vira fotografia pequena.

## 5. Ordem de trabalho proposta

Da maior relação resultado/custo para a menor:

1. **Corrigir os 23 recursos quebrados.** Sem isso, o build não é confiável em
   nenhuma máquina. Remover os caminhos absolutos do Windows.
2. **Extrair a lógica comum das 5 fases** para uma extensão de eventos
   compartilhada. Elimina a manutenção quíntupla.
3. **Normalizar os assets:** deduplicar os 95 pares, remover os 28 órfãos,
   organizar em `assets/<dominio>/`.
4. **Estabelecer a grade de pixel art** (480x270, tiles 16, player 32) e a
   camada de UI legível.
5. **Melhorar o game feel do movimento:** coyote time, jump buffer, aceleração e
   atrito ajustados, feedback de pouso.
6. **Passar UX nas telas:** estados de hover/press/disabled nos botões, feedback
   de coleta, progresso visível no mapa, acessibilidade de contraste.
7. **Reautorar os fundos fotográficos** na grade definida.
