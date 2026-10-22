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
