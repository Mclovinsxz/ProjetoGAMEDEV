#!/usr/bin/env python3
"""Compara duas exportações do jogo para provar que um refactor não mudou comportamento.

Compilar não prova equivalência: uma cena pode compilar e rodar diferente. O
que prova é comparar o código que o GDevelop gera para cada cena antes e
depois da mudança.

A comparação precisa ignorar os identificadores opacos que o GDevelop emite —
`triggerOnce(N)`, `asyncCallbackN`, os ids do mapa de callbacks e os nomes
`userFunc0x<endereço>` dos blocos de JavaScript embutido. São tokens de
identidade derivados da ordem de alocação dos eventos, ou literalmente do
endereço de memória do objeto no exportador, não de semântica: o valor só
precisa ser único dentro da cena. Reexportar o projeto os muda sem que nada no
jogo mude. Este script renumera esses ids na ordem em que aparecem, em cada
arquivo, e só então compara.

Uma diferença que sobrevive à renumeração é uma diferença de comportamento.

A renumeração é por ordem de aparição, então uma mudança que *acrescenta* um
identificador desloca a ordinal de todos os seguintes. O diff real aparece
junto com esse ruído de deslocamento. Ao revisar uma mudança intencional, as
linhas que só trocam `<IDn>` por `<IDm>` são ruído; as demais são a mudança.

Uso:
    python3 tools/comparar_build.py build_antes build_depois
"""

import difflib
import glob
import os
import re
import sys

# Contextos em que o valor capturado é identificador opaco, não valor de jogo.
PADROES_DE_ID = [
    re.compile(r"triggerOnce\((\d+)\)"),
    re.compile(r"asyncCallback(\d+)"),
    re.compile(r"idToCallbackMap\.set\((\d+),"),
    re.compile(r",\s*(\d+),\s*asyncObjectsList\)"),
    re.compile(r"userFunc(0x[0-9a-f]+)"),
]


def normalizar(texto):
    """Renumera os identificadores opacos na ordem de primeira aparição."""
    encontrados = []
    for padrao in PADROES_DE_ID:
        for m in padrao.finditer(texto):
            valor = m.group(1)
            if valor not in encontrados:
                encontrados.append(valor)

    # Do mais longo para o mais curto, para que um id não seja prefixo de outro.
    for indice, valor in enumerate(sorted(encontrados, key=len, reverse=True)):
        ordem = encontrados.index(valor)
        texto = texto.replace(valor, f"<ID{ordem}>")
    return texto


def main():
    if len(sys.argv) != 3:
        print("uso: comparar_build.py <build_antes> <build_depois>", file=sys.stderr)
        return 2

    antes, depois = sys.argv[1], sys.argv[2]
    nomes = sorted(
        {os.path.basename(p) for p in glob.glob(os.path.join(antes, "code*.js"))}
        | {os.path.basename(p) for p in glob.glob(os.path.join(depois, "code*.js"))}
    )
    if not nomes:
        print("ERRO  nenhum code*.js encontrado nos dois diretórios", file=sys.stderr)
        return 1

    iguais, mudaram, faltando = [], [], []
    for nome in nomes:
        pa, pd = os.path.join(antes, nome), os.path.join(depois, nome)
        if not (os.path.isfile(pa) and os.path.isfile(pd)):
            faltando.append(nome)
            continue
        with open(pa, encoding="utf-8", errors="replace") as f:
            a = normalizar(f.read())
        with open(pd, encoding="utf-8", errors="replace") as f:
            b = normalizar(f.read())
        (iguais if a == b else mudaram).append((nome, a, b))

    print(f"cenas comparadas    : {len(nomes)}")
    print(f"  equivalentes      : {len(iguais)}")
    print(f"  com diferença     : {len(mudaram)}")
    print(f"  ausentes num lado : {len(faltando)}")

    for nome in faltando:
        print(f"\nERRO  {nome} existe só em um dos builds")

    for nome, a, b in mudaram:
        print(f"\n--- diferença de comportamento em {nome} ---")
        linhas = list(difflib.unified_diff(
            a.splitlines(), b.splitlines(), fromfile=f"antes/{nome}", tofile=f"depois/{nome}", lineterm="", n=1))
        for linha in linhas[:40]:
            print(linha)
        if len(linhas) > 40:
            print(f"... e mais {len(linhas) - 40} linhas")

    if mudaram or faltando:
        print("\nreprovado: o código gerado mudou")
        return 1
    print("\naprovado: código gerado equivalente em todas as cenas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
