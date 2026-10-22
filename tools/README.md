# tools

Ferramentas de manutenção do projeto. Rodam com o Python padrão, sem instalar
nada.

## `validar_projeto.py`

Portão de integridade do projeto GDevelop. É o que a CI roda a cada push e
pull request.

```bash
python3 tools/validar_projeto.py            # erros reprovam, avisos passam
python3 tools/validar_projeto.py --estrito  # avisos também reprovam
```

### Erros — reprovam o build

| Verificação | Por quê |
| --- | --- |
| Recurso declarado cujo arquivo não existe | O projeto não abre igual em outra máquina |
| Referência a recurso não declarado | Objeto, cena ou evento aponta para o nada |
| Caminho absoluto de máquina de autor (`G:\...`, UNC) | Vaza caminho pessoal e quebra fora daquela máquina |
| Separador do Windows ou caminho absoluto no campo `file` | Quebra em Linux e macOS |

### Avisos — passam, mas contam a sujeira

Recursos declarados sem uso, arquivos de asset em disco sem recurso declarado,
e arquivos idênticos byte a byte. Não quebram o jogo; pesam no repositório e no
download do jogador.

`--estrito` promove avisos a erros. A ideia é ligá-lo na CI depois que a
normalização de assets zerar essas contagens, para que não voltem a crescer.

### Como as referências são reconhecidas

`image`, `texture`, `font` e `atlasImage` sempre carregam nome de recurso —
toda string não vazia sob elas é cobrada. `atlasImage` fica nesse grupo porque
o GDevelop desambigua nome repetido acrescentando sufixo numérico à extensão
(`caverna.png2`), que um filtro por extensão descartaria.

`parameters` e `fontFamily` misturam recurso com string arbitrária: parâmetros
de evento carregam expressões e textos junto com nomes de áudio, e `fontFamily`
carrega tanto fonte de sistema (`Arial`) quanto recurso `.ttf`. Nelas, só os
valores com extensão de asset são cobrados.

`name` e `objectName` ficam de fora de propósito: carregam nomes de objeto, que
às vezes coincidem com nomes de recurso sem referenciá-los.

A varredura de recursos sem uso é deliberadamente permissiva — qualquer string
do projeto conta como uso. Um recurso só é apontado quando o nome não aparece
em lugar nenhum, o que torna a remoção segura.

## `teste_validar_projeto.py`

Suíte do validador. Monta projetos sintéticos em diretório temporário, injeta
um defeito por vez e confere que cada verificação pega o que deve pegar e
ignora o que deve ignorar.

```bash
python3 tools/teste_validar_projeto.py
```

## `normalizar_assets.py`

Funde cópias redundantes de asset e, opcionalmente, apaga arquivos que nenhum
recurso declara.

```bash
python3 tools/normalizar_assets.py --deduplicar --simular
python3 tools/normalizar_assets.py --deduplicar
```

Mexe só no campo `file` dos recursos, nunca no nome — nome é o que objetos,
cenas e eventos referenciam, então nada precisa ser atualizado junto.

Quadros de animação são preservados de propósito. Uma animação de espera de
sete quadros repete pixels entre quadros vizinhos como quadro de permanência:
são arquivos idênticos por intenção do artista. Fundi-los faria editar um
quadro alterar o outro, então grupos cujos membros convivem na mesma lista de
quadros ficam de fora.

`--remover-soltos` existe mas deve ser usado com cuidado: boa parte dos
arquivos sem recurso declarado é arte e áudio que a equipe produziu e ainda não
conectou (o som de pulo, as árvores de São Raimundo Nonato, o mapa Tiled da
escavação), não lixo.

## `conferir_build.py`

Confere que a exportação HTML5 saiu completa. Roda na CI depois do
`gdexporter`.

```bash
npx gdexporter@4.0.0-beta7 -p ProjetoGameDEv4.json -o build
python3 tools/conferir_build.py build
```

O `gdexporter` termina com sucesso mesmo quando uma cena deixa de compilar —
ela simplesmente não gera seu `code<N>.js`. Este script compara o número de
`code*.js` com o número de cenas declaradas, confere que o `index.html` saiu e
que o runtime veio junto, e reprova se faltar qualquer um.

## `comparar_build.py`

Prova que um refactor não mudou comportamento, comparando o código que o
GDevelop gera para cada cena antes e depois.

```bash
npx gdexporter@4.0.0-beta7 -p ProjetoGameDEv4.json -o build_antes   # antes da mudança
# ... faz a mudança ...
npx gdexporter@4.0.0-beta7 -p ProjetoGameDEv4.json -o build_depois
python3 tools/comparar_build.py build_antes build_depois
```

Compilar não prova equivalência — uma cena pode compilar e rodar diferente. O
código gerado prova.

A comparação ignora os identificadores opacos que o GDevelop emite:
`triggerOnce(N)`, `asyncCallbackN`, os ids do mapa de callbacks e os nomes
`userFunc0x<endereço>` dos blocos de JavaScript embutido. São tokens de
identidade derivados da ordem de alocação dos eventos, ou do endereço de
memória do objeto no exportador — reexportar o mesmo projeto sem mudança
nenhuma já os altera. O script os renumera na ordem de aparição antes de
comparar.

Uma diferença que sobrevive à renumeração é diferença de comportamento.
Verificado contra mutações deliberadas: constante de jogo alterada, nome de
objeto trocado e cena ausente são todas reprovadas.
