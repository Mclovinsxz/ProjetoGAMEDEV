#!/usr/bin/env python3
"""Normaliza os assets do projeto: remove cópias redundantes e arquivos soltos.

Duas operações, cada uma podendo rodar sozinha:

    --deduplicar   funde arquivos byte a byte idênticos num só, repontando os
                   recursos que apontavam para as cópias
    --remover-soltos
                   apaga arquivos de asset que nenhum recurso declara

Nenhuma mexe em nome de recurso, só no campo `file`. Nome é o que objetos,
cenas e eventos referenciam, então mantê-lo intacto garante que nada quebra.

Quadros de animação são preservados de propósito. Uma animação de espera com
sete quadros costuma repetir pixels entre quadros vizinhos — são arquivos
idênticos por intenção do artista, não por descuido. Fundi-los faria com que
editar um quadro alterasse o outro, então grupos cujos membros convivem na
mesma lista de quadros ficam de fora.

Uso:
    python3 tools/normalizar_assets.py --deduplicar --simular
    python3 tools/normalizar_assets.py --deduplicar
    python3 tools/normalizar_assets.py --remover-soltos
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validar_projeto as v


def carregar_projeto(raiz):
    with open(os.path.join(raiz, v.PROJETO), encoding="utf-8") as f:
        return json.load(f)


def gravar_projeto(raiz, projeto):
    with open(os.path.join(raiz, v.PROJETO), "w", encoding="utf-8") as f:
        json.dump(projeto, f, ensure_ascii=False, indent=2)
        f.write("\n")


def pares_de_quadros_vizinhos(docs, arquivo_por_nome):
    """Pares de arquivos que aparecem como quadros distintos da mesma animação."""
    pares = set()

    def varrer(no):
        if isinstance(no, dict):
            sprites = no.get("sprites")
            if isinstance(sprites, list):
                quadros = [s.get("image") for s in sprites if isinstance(s, dict) and s.get("image")]
                for i, a in enumerate(quadros):
                    for b in quadros[i + 1:]:
                        fa, fb = arquivo_por_nome.get(a), arquivo_por_nome.get(b)
                        if fa and fb and fa != fb:
                            pares.add(frozenset((fa, fb)))
            for val in no.values():
                varrer(val)
        elif isinstance(no, list):
            for val in no:
                varrer(val)

    for _, doc in docs:
        varrer(doc)
    return pares


def escolher_canonico(grupo, declarados):
    """Preferência: arquivo declarado como recurso, depois dentro de assets/, depois caminho curto."""
    def pontuar(caminho):
        n = os.path.normpath(caminho)
        return (n not in declarados, not n.startswith("assets" + os.sep), len(n), n)
    return min(grupo, key=pontuar)


def deduplicar(raiz, simular):
    projeto = carregar_projeto(raiz)
    recursos = projeto["resources"]["resources"]
    declarados = {os.path.normpath(r["file"]) for r in recursos if r.get("file")}
    arquivo_por_nome = {r["name"]: os.path.normpath(r["file"]) for r in recursos if r.get("file")}

    docs = v.carregar_documentos(raiz)
    vizinhos = pares_de_quadros_vizinhos(docs, arquivo_por_nome)

    grupos = v.encontrar_duplicatas(raiz, v.Relatorio())

    fundidos, preservados = [], []
    for grupo in grupos:
        normalizado = [os.path.normpath(p) for p in grupo]
        eh_animacao = any(
            frozenset((a, b)) in vizinhos
            for i, a in enumerate(normalizado)
            for b in normalizado[i + 1:]
        )
        (preservados if eh_animacao else fundidos).append(normalizado)

    redirecionamento = {}
    a_remover = []
    for grupo in fundidos:
        canonico = escolher_canonico(grupo, declarados)
        for caminho in grupo:
            if caminho != canonico:
                redirecionamento[caminho] = canonico
                a_remover.append(caminho)

    repontados = 0
    for r in recursos:
        atual = os.path.normpath(r.get("file", ""))
        if atual in redirecionamento:
            r["file"] = redirecionamento[atual].replace(os.sep, "/")
            repontados += 1

    print(f"grupos idênticos           : {len(grupos)}")
    print(f"  preservados (animação)   : {len(preservados)}")
    print(f"  fundidos                 : {len(fundidos)}")
    print(f"recursos repontados        : {repontados}")
    print(f"arquivos a remover         : {len(a_remover)}")
    economia = sum(os.path.getsize(os.path.join(raiz, p)) for p in a_remover if os.path.exists(os.path.join(raiz, p)))
    print(f"espaço recuperado          : {economia / 1024 / 1024:.1f} MB")

    if simular:
        print("\nsimulação, nada foi gravado")
        return 0

    gravar_projeto(raiz, projeto)
    for caminho in a_remover:
        destino = os.path.join(raiz, caminho)
        if os.path.exists(destino):
            os.remove(destino)
    print("\naplicado")
    return 0


def remover_soltos(raiz, simular):
    projeto = carregar_projeto(raiz)
    recursos = projeto["resources"]["resources"]
    soltos = v.encontrar_arquivos_sem_recurso(raiz, recursos, v.Relatorio())

    peso = sum(os.path.getsize(os.path.join(raiz, p)) for p in soltos)
    print(f"arquivos sem recurso declarado: {len(soltos)}")
    print(f"espaço recuperado             : {peso / 1024 / 1024:.1f} MB")
    for caminho in sorted(soltos):
        print(f"  {caminho}")

    if simular:
        print("\nsimulação, nada foi removido")
        return 0

    for caminho in soltos:
        os.remove(os.path.join(raiz, caminho))
    print("\naplicado")
    return 0


def main():
    p = argparse.ArgumentParser(description="Normaliza os assets do projeto.")
    p.add_argument("--deduplicar", action="store_true", help="funde arquivos byte a byte idênticos")
    p.add_argument("--remover-soltos", action="store_true", help="apaga assets que nenhum recurso declara")
    p.add_argument("--simular", action="store_true", help="mostra o que faria sem gravar nada")
    p.add_argument("--raiz", default=".", help="raiz do projeto (padrão: diretório atual)")
    args = p.parse_args()

    if not (args.deduplicar or args.remover_soltos):
        p.error("escolha ao menos uma operação: --deduplicar ou --remover-soltos")

    raiz = os.path.abspath(args.raiz)
    codigo = 0
    if args.deduplicar:
        codigo |= deduplicar(raiz, args.simular)
    if args.remover_soltos:
        if args.deduplicar:
            print()
        codigo |= remover_soltos(raiz, args.simular)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
