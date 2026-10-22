# assets

Arte, áudio e fontes do jogo. A pasta de cada recurso é dada pelo **uso**, não
pelo nome do arquivo: cada recurso foi atribuído à cena que o referencia, e o
que mais de uma cena usa ficou em `comum/`.

| pasta | o que guarda |
| --- | --- |
| `comum/` | usado por mais de uma cena: o player, o cenário compartilhado das fases, as caixas de diálogo, os checkpoints |
| `teresina/` `oeiras/` `parnaiba/` `campo_maior/` `srn/` | exclusivo da fase daquela cidade |
| `minigame_escavacao/` `minigame_navegacao/` `minigame_point_click/` | exclusivo de cada minigame |
| `quiz/` `mapa/` `menu/` `pre_select/` `pre_fase/` `introducao/` | exclusivo de cada tela |
| `fase1/` | cena `fase1`, que não é alcançável por nenhuma troca de cena nem é a cena inicial |
| `fontes/` `sons/` | por tipo, já que atravessam todas as cenas |
| `reserva/` | **fora do sistema de recursos** |

## Sobre `reserva/`

Guarda arte e áudio que a equipe produziu e que ainda não está ligado a nenhum
objeto: as árvores de São Raimundo Nonato, os botões de asset pack com estados
de hover e press, o mapa Tiled da escavação, peças de cenário.

Nada ali é declarado como recurso, então nada ali entra no build nem pesa no
download do aluno. É matéria-prima disponível, não lixo — o som de pulo ficou
nessa situação até ser ligado ao jogo.

`referencias/`, na raiz do repositório, cumpre papel parecido para fotografia e
arte-fonte de cenário.

## Por que o nome do recurso não acompanha o caminho

No GDevelop, objetos, cenas e eventos referenciam o **nome** do recurso; o
campo `file` é só onde o arquivo está. Por isso foi possível mover 599 arquivos
sem tocar em nenhuma referência, e por isso muitos nomes ainda carregam o
caminho antigo, às vezes com barra invertida herdada do Windows
(`assets\box_item_coletar_1.png`).

Renomeá-los exigiria atualizar toda referência em conjunto, numa única
passagem. Enquanto isso não for feito, o nome é um identificador, não um
caminho — e `tools/validar_projeto.py` cobra que todo `file` aponte para
arquivo existente.
