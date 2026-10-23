#!/usr/bin/env python3
"""Confere que a exportação HTML5 do jogo saiu completa.

O gdexporter termina com sucesso mesmo quando uma cena deixa de compilar, então
checar o código de saída dele não basta. Este script compara o que saiu no
diretório de build com o que o projeto declara.

Uso:
    python3 tools/conferir_build.py build
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validar_projeto as v


def main():
    if len(sys.argv) != 2:
        print("uso: conferir_build.py <diretorio_de_build>", file=sys.stderr)
        return 2

    build = sys.argv[1]
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    erros = []

    if not os.path.isdir(build):
        print(f"ERRO  diretório de build não existe: {build}", file=sys.stderr)
        return 1

    index = os.path.join(build, "index.html")
    if not os.path.isfile(index):
        erros.append("index.html não foi gerado")

    # Uma cena que não compila simplesmente não gera seu code<N>.js.
    with open(os.path.join(raiz, v.PROJETO), encoding="utf-8") as f:
        projeto = json.load(f)
    esperadas = len(projeto.get("layouts", []))
    compiladas = len(glob.glob(os.path.join(build, "code*.js")))
    if compiladas != esperadas:
        erros.append(f"cenas compiladas: {compiladas}, esperadas: {esperadas}")

    runtime = glob.glob(os.path.join(build, "*.js"))
    if len(runtime) < 10:
        erros.append(f"runtime incompleto: só {len(runtime)} arquivos .js no build")

    arquivos = sum(len(fs) for _, _, fs in os.walk(build))
    peso = sum(
        os.path.getsize(os.path.join(d, f))
        for d, _, fs in os.walk(build)
        for f in fs
    )

    print(f"cenas compiladas : {compiladas}/{esperadas}")
    print(f"arquivos no build: {arquivos}")
    print(f"peso do build    : {peso / 1024 / 1024:.1f} MB")

    if erros:
        print()
        for e in erros:
            print(f"ERRO  {e}")
        return 1

    print("\nbuild íntegro")
    return 0


if __name__ == "__main__":
    sys.exit(main())
