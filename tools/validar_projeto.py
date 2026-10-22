#!/usr/bin/env python3
"""Valida a integridade do projeto GDevelop de Piauí: Crônicas do Tempo.

Confere que todo recurso declarado existe em disco, que toda referência a
recurso feita por objetos, cenas e eventos aponta para um recurso declarado, e
que nenhum caminho absoluto de máquina de autor vazou para o repositório.

Reporta ainda, como aviso, a sujeira que não quebra o jogo mas pesa nele:
recursos declarados sem uso, arquivos em disco sem recurso, e arquivos
duplicados byte a byte.

Uso:
    python3 tools/validar_projeto.py            # erros reprovam, avisos passam
    python3 tools/validar_projeto.py --estrito  # avisos também reprovam
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

PROJETO = "ProjetoGameDEv4.json"
PASTAS_DE_DOCUMENTOS = ("layouts", "externalEvents", "eventsFunctionsExtensions", "externalLayouts")

# Chaves cujo valor é sempre o nome de um recurso. Levantadas a partir do
# próprio projeto: toda string não vazia sob elas casa com um recurso
# declarado. "name" e "objectName" ficam de fora de propósito — carregam nomes
# de objeto, que por vezes coincidem com nomes de recurso sem referenciá-los.
#
# "atlasImage" fica aqui, e não entre as chaves filtradas abaixo, porque o
# GDevelop desambigua nome repetido acrescentando um sufixo numérico à
# extensão ("caverna.png2"), o que escaparia do filtro por extensão.
CHAVES_DE_REFERENCIA = ("image", "texture", "font", "atlasImage")

# Chaves que misturam referência a recurso com string arbitrária: "parameters"
# carrega expressões, textos e números de evento junto com nomes de áudio, e
# "fontFamily" carrega tanto fonte de sistema ("Arial") quanto recurso .ttf.
# Nelas, só são cobrados os valores com cara de arquivo.
CHAVES_FILTRADAS = ("parameters", "fontFamily")
EXTENSOES_DE_ASSET = (".png", ".jpg", ".jpeg", ".ttf", ".otf", ".wav", ".mp3", ".ogg", ".glb", ".tmj")

# Arquivos em disco que contam como asset para a varredura de órfãos.
#
# Duas pastas ficam fora dela de propósito, por guardarem material que o jogo
# não carrega: "referencias" tem as fotos e a arte-fonte que a equipe de design
# usa para reautorar os fundos, e "assets/reserva" tem arte e áudio prontos que
# ainda não foram ligados a nenhum objeto — o som de pulo ficou ali até ser
# usado, por exemplo.
#
# Deixá-las de fora é o que mantém o aviso útil: um arquivo apontado como sem
# recurso passa a significar que alguém deixou um asset numa pasta de conteúdo
# sem declará-lo, que é acionável, em vez de repetir centenas de arquivos
# guardados de propósito.
EXTENSOES_VARRIDAS = EXTENSOES_DE_ASSET
PASTAS_IGNORADAS = {
    ".git", ".github", "docs", "tools", "referencias",
    os.path.join("assets", "reserva"), ".claude-flow", ".swarm",
}

UNIDADE_DE_DISCO = re.compile(r"^[A-Za-z]:[\\/]")


class Relatorio:
    def __init__(self):
        self.erros = []
        self.avisos = []
        self.infos = []

    def erro(self, msg):
        self.erros.append(msg)

    def aviso(self, msg):
        self.avisos.append(msg)

    def info(self, msg):
        self.infos.append(msg)


def carregar_documentos(raiz):
    """Devolve [(rotulo, dado)] com o projeto e todo documento auxiliar."""
    docs = []
    caminho = os.path.join(raiz, PROJETO)
    with open(caminho, encoding="utf-8") as f:
        docs.append((PROJETO, json.load(f)))
    for pasta in PASTAS_DE_DOCUMENTOS:
        dir_ = os.path.join(raiz, pasta)
        if not os.path.isdir(dir_):
            continue
        for nome in sorted(os.listdir(dir_)):
            if not nome.endswith(".json"):
                continue
            with open(os.path.join(dir_, nome), encoding="utf-8") as f:
                docs.append((f"{pasta}/{nome}", json.load(f)))
    return docs


def percorrer(no, chave=None):
    """Gera (chave_pai, string) para toda string do documento."""
    if isinstance(no, dict):
        for k, v in no.items():
            yield from percorrer(v, k)
    elif isinstance(no, list):
        for v in no:
            yield from percorrer(v, chave)
    elif isinstance(no, str):
        yield chave, no


def parece_asset(valor):
    return valor.lower().endswith(EXTENSOES_DE_ASSET)


def podar(raiz, atual, pastas):
    """Tira da varredura as pastas ignoradas, por nome simples ou caminho."""
    mantidas = []
    for p in pastas:
        rel = os.path.relpath(os.path.join(atual, p), raiz)
        if p in PASTAS_IGNORADAS or rel in PASTAS_IGNORADAS:
            continue
        mantidas.append(p)
    pastas[:] = mantidas


def conferir_recursos_em_disco(raiz, recursos, rel):
    for r in recursos:
        arquivo = r.get("file")
        if not arquivo:
            continue
        if not os.path.exists(os.path.join(raiz, arquivo)):
            rel.erro(f"recurso {r['name']!r} aponta para arquivo inexistente: {arquivo}")


def conferir_caminhos(recursos, rel):
    for r in recursos:
        nome, arquivo = r.get("name", ""), r.get("file", "")
        for campo, valor in (("name", nome), ("file", arquivo)):
            if UNIDADE_DE_DISCO.match(valor) or valor.startswith("\\\\"):
                rel.erro(f"caminho absoluto de máquina de autor em {campo} do recurso {nome!r}: {valor}")
        if "\\" in arquivo:
            rel.erro(f"recurso {nome!r} usa separador de caminho do Windows em file: {arquivo}")
        if os.path.isabs(arquivo):
            rel.erro(f"recurso {nome!r} usa caminho absoluto em file: {arquivo}")

    com_barra = sum(1 for r in recursos if "\\" in r.get("name", ""))
    if com_barra:
        rel.info(
            f"{com_barra} nomes de recurso contêm barra invertida herdada do Windows. "
            "Funcionam, mas renomeá-los exige atualizar toda referência em conjunto."
        )


def conferir_referencias(docs, declarados, rel):
    """Toda referência a recurso precisa ter recurso declarado."""
    for rotulo, doc in docs:
        if rotulo == PROJETO:
            doc = dict(doc)
            doc["resources"] = {"resources": []}
        for chave, valor in percorrer(doc):
            if not valor:
                continue
            if chave in CHAVES_DE_REFERENCIA or (chave in CHAVES_FILTRADAS and parece_asset(valor)):
                if valor not in declarados:
                    rel.erro(f"{rotulo}: {chave} referencia recurso não declarado: {valor!r}")


def encontrar_recursos_sem_uso(docs, recursos, rel):
    """Varredura permissiva: qualquer string do projeto conta como uso.

    Over-matching aqui é de propósito. Um recurso só é apontado como sem uso
    quando o nome não aparece em lugar nenhum, o que torna a remoção segura.
    """
    usados = set()
    for rotulo, doc in docs:
        if rotulo == PROJETO:
            doc = dict(doc)
            doc["resources"] = {"resources": []}
        usados.update(valor for _, valor in percorrer(doc))

    sem_uso = [r["name"] for r in recursos if r["name"] not in usados]
    for nome in sem_uso:
        rel.aviso(f"recurso declarado sem uso: {nome!r}")
    return sem_uso


def encontrar_arquivos_sem_recurso(raiz, recursos, rel):
    declarados = {os.path.normpath(r["file"]) for r in recursos if r.get("file")}
    orfaos = []
    for atual, pastas, arquivos in os.walk(raiz):
        podar(raiz, atual, pastas)
        for nome in arquivos:
            if not nome.lower().endswith(EXTENSOES_VARRIDAS):
                continue
            rel_path = os.path.normpath(os.path.relpath(os.path.join(atual, nome), raiz))
            if rel_path not in declarados:
                orfaos.append(rel_path)
    for caminho in sorted(orfaos):
        rel.aviso(f"arquivo em disco sem recurso declarado: {caminho}")
    return orfaos


def encontrar_duplicatas(raiz, rel):
    por_hash = defaultdict(list)
    for atual, pastas, arquivos in os.walk(raiz):
        podar(raiz, atual, pastas)
        for nome in arquivos:
            if not nome.lower().endswith(EXTENSOES_VARRIDAS):
                continue
            caminho = os.path.join(atual, nome)
            with open(caminho, "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
            por_hash[digest].append(os.path.relpath(caminho, raiz))

    grupos = [sorted(v) for v in por_hash.values() if len(v) > 1]
    for grupo in sorted(grupos):
        rel.aviso("arquivos idênticos byte a byte: " + ", ".join(grupo))
    return grupos


def main():
    p = argparse.ArgumentParser(description="Valida a integridade do projeto GDevelop.")
    p.add_argument("--estrito", action="store_true", help="trata avisos como erros")
    p.add_argument("--raiz", default=".", help="raiz do projeto (padrão: diretório atual)")
    args = p.parse_args()

    raiz = os.path.abspath(args.raiz)
    rel = Relatorio()

    try:
        docs = carregar_documentos(raiz)
    except json.JSONDecodeError as e:
        print(f"ERRO: JSON inválido — {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1

    projeto = docs[0][1]
    recursos = projeto["resources"]["resources"]
    declarados = {r["name"] for r in recursos}

    conferir_recursos_em_disco(raiz, recursos, rel)
    conferir_caminhos(recursos, rel)
    conferir_referencias(docs, declarados, rel)
    sem_uso = encontrar_recursos_sem_uso(docs, recursos, rel)
    orfaos = encontrar_arquivos_sem_recurso(raiz, recursos, rel)
    duplicatas = encontrar_duplicatas(raiz, rel)

    print(f"documentos analisados : {len(docs)}")
    print(f"recursos declarados   : {len(recursos)}")
    print(f"recursos sem uso      : {len(sem_uso)}")
    print(f"arquivos sem recurso  : {len(orfaos)}")
    print(f"grupos de duplicatas  : {len(duplicatas)}")
    print()

    for msg in rel.infos:
        print(f"INFO  {msg}")
    for msg in rel.avisos:
        print(f"AVISO {msg}")
    for msg in rel.erros:
        print(f"ERRO  {msg}")

    if rel.erros:
        print(f"\nreprovado: {len(rel.erros)} erro(s)")
        return 1
    if args.estrito and rel.avisos:
        print(f"\nreprovado em modo estrito: {len(rel.avisos)} aviso(s)")
        return 1
    if rel.avisos:
        print(f"\naprovado com {len(rel.avisos)} aviso(s)")
    else:
        print("\naprovado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
