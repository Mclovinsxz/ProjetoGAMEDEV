#!/usr/bin/env python3
"""Testes do validador de projeto.

Monta projetos sintéticos mínimos em diretório temporário, injeta um defeito
por vez e confere que o validador reprova o que deve reprovar e aprova o que
deve aprovar. Sem dependência externa — roda com o Python da imagem.

Uso:
    python3 tools/teste_validar_projeto.py
"""

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validar_projeto as v


def montar_projeto(raiz, recursos, layout=None):
    """Escreve um projeto GDevelop mínimo e os arquivos de asset que ele cita."""
    projeto = {
        "firstLayout": "cena",
        "properties": {"name": "teste"},
        "resources": {"resources": recursos},
        "objects": [],
        "layouts": [],
    }
    with open(os.path.join(raiz, v.PROJETO), "w", encoding="utf-8") as f:
        json.dump(projeto, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.join(raiz, "layouts"), exist_ok=True)
    with open(os.path.join(raiz, "layouts", "cena.json"), "w", encoding="utf-8") as f:
        json.dump(layout if layout is not None else {"objects": []}, f, ensure_ascii=False, indent=2)


def criar_arquivo(raiz, caminho_rel):
    destino = os.path.join(raiz, caminho_rel)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + caminho_rel.encode())


def rodar(raiz, estrito=False):
    """Executa o validador e devolve (codigo_de_saida, relatorio)."""
    rel = v.Relatorio()
    docs = v.carregar_documentos(raiz)
    recursos = docs[0][1]["resources"]["resources"]
    declarados = {r["name"] for r in recursos}

    v.conferir_recursos_em_disco(raiz, recursos, rel)
    v.conferir_caminhos(recursos, rel)
    v.conferir_referencias(docs, declarados, rel)
    v.encontrar_recursos_sem_uso(docs, recursos, rel)
    v.encontrar_arquivos_sem_recurso(raiz, recursos, rel)
    v.encontrar_duplicatas(raiz, rel)

    if rel.erros:
        return 1, rel
    if estrito and rel.avisos:
        return 1, rel
    return 0, rel


RECURSO_OK = {"name": "heroi.png", "file": "assets/heroi.png", "kind": "image"}
LAYOUT_QUE_USA = {"objects": [{"name": "Heroi", "animations": [
    {"directions": [{"sprites": [{"image": "heroi.png"}]}]}]}]}


CASOS = []


def caso(nome):
    def dec(fn):
        CASOS.append((nome, fn))
        return fn
    return dec


@caso("projeto íntegro é aprovado sem erro nem aviso")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    montar_projeto(raiz, [RECURSO_OK], LAYOUT_QUE_USA)
    codigo, rel = rodar(raiz)
    assert codigo == 0, rel.erros
    assert not rel.erros, rel.erros
    assert not rel.avisos, rel.avisos


@caso("recurso apontando para arquivo inexistente reprova")
def _(raiz):
    montar_projeto(raiz, [RECURSO_OK], LAYOUT_QUE_USA)
    codigo, rel = rodar(raiz)
    assert codigo == 1
    assert any("arquivo inexistente" in e for e in rel.erros), rel.erros


@caso("referência a recurso não declarado reprova")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    layout = {"objects": [{"name": "Heroi", "animations": [
        {"directions": [{"sprites": [{"image": "fantasma.png"}]}]}]}]}
    montar_projeto(raiz, [RECURSO_OK], layout)
    codigo, rel = rodar(raiz)
    assert codigo == 1
    assert any("não declarado" in e and "fantasma.png" in e for e in rel.erros), rel.erros


@caso("caminho absoluto do Windows no nome do recurso reprova")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    recurso = {"name": r"G:\Meu Drive\projeto\heroi.png", "file": "assets/heroi.png", "kind": "image"}
    montar_projeto(raiz, [recurso])
    codigo, rel = rodar(raiz)
    assert codigo == 1
    assert any("caminho absoluto de máquina de autor" in e for e in rel.erros), rel.erros


@caso("separador do Windows no file do recurso reprova")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    recurso = {"name": "heroi.png", "file": r"assets\heroi.png", "kind": "image"}
    montar_projeto(raiz, [recurso], LAYOUT_QUE_USA)
    codigo, rel = rodar(raiz)
    assert codigo == 1
    assert any("separador de caminho do Windows" in e for e in rel.erros), rel.erros


@caso("barra invertida no nome do recurso é tolerada e só vira informação")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    recurso = {"name": r"assets\heroi.png", "file": "assets/heroi.png", "kind": "image"}
    layout = {"objects": [{"name": "Heroi", "animations": [
        {"directions": [{"sprites": [{"image": r"assets\heroi.png"}]}]}]}]}
    montar_projeto(raiz, [recurso], layout)
    codigo, rel = rodar(raiz)
    assert codigo == 0, rel.erros
    assert any("barra invertida" in i for i in rel.infos), rel.infos


@caso("fonte de sistema em fontFamily não é cobrada como recurso")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    layout = {"objects": [
        {"name": "Texto", "fontFamily": "Arial"},
        {"name": "Heroi", "animations": [{"directions": [{"sprites": [{"image": "heroi.png"}]}]}]},
    ]}
    montar_projeto(raiz, [RECURSO_OK], layout)
    codigo, rel = rodar(raiz)
    assert codigo == 0, rel.erros


@caso("fonte .ttf ausente em fontFamily é cobrada")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    layout = {"objects": [{"name": "Texto", "fontFamily": "sumida.ttf"}]}
    montar_projeto(raiz, [RECURSO_OK], layout)
    codigo, rel = rodar(raiz)
    assert codigo == 1
    assert any("sumida.ttf" in e for e in rel.erros), rel.erros


@caso("áudio ausente em parâmetro de evento é cobrado")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    layout = {"objects": [], "events": [{"type": "BuiltinAudio::PlaySound",
                                         "parameters": ["", "assets/sons/sumido.wav", "", "", ""]}]}
    montar_projeto(raiz, [RECURSO_OK], layout)
    codigo, rel = rodar(raiz)
    assert codigo == 1
    assert any("sumido.wav" in e for e in rel.erros), rel.erros


@caso("texto comum em parâmetro de evento não é cobrado")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    layout = {"objects": [], "events": [{"type": "BuiltinCommonInstructions::Standard",
                                         "parameters": ["Variable(pontos) > 10", "Teresina", "3"]}]}
    montar_projeto(raiz, [RECURSO_OK], LAYOUT_QUE_USA)
    codigo, rel = rodar(raiz)
    assert codigo == 0, rel.erros


@caso("sufixo numérico na extensão sobrevive ao filtro (caverna.png2)")
def _(raiz):
    criar_arquivo(raiz, "assets/caverna.png")
    recurso = {"name": "assets/caverna.png2", "file": "assets/caverna.png", "kind": "image"}
    layout = {"objects": [{"name": "Mapa", "atlasImage": "assets/caverna.png2"}]}
    montar_projeto(raiz, [recurso], layout)
    codigo, rel = rodar(raiz)
    assert codigo == 0, rel.erros


@caso("atlasImage apontando para recurso inexistente reprova")
def _(raiz):
    criar_arquivo(raiz, "assets/caverna.png")
    recurso = {"name": "assets/caverna.png2", "file": "assets/caverna.png", "kind": "image"}
    layout = {"objects": [{"name": "Mapa", "atlasImage": "assets/outra.png9"}]}
    montar_projeto(raiz, [recurso], layout)
    codigo, rel = rodar(raiz)
    assert codigo == 1
    assert any("outra.png9" in e for e in rel.erros), rel.erros


@caso("recurso declarado sem uso vira aviso, não erro")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    montar_projeto(raiz, [RECURSO_OK])
    codigo, rel = rodar(raiz)
    assert codigo == 0, rel.erros
    assert any("sem uso" in a for a in rel.avisos), rel.avisos


@caso("modo estrito reprova com aviso")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    montar_projeto(raiz, [RECURSO_OK])
    codigo, rel = rodar(raiz, estrito=True)
    assert codigo == 1
    assert not rel.erros, rel.erros


@caso("arquivo em disco sem recurso declarado vira aviso")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    criar_arquivo(raiz, "assets/sobra.png")
    montar_projeto(raiz, [RECURSO_OK], LAYOUT_QUE_USA)
    codigo, rel = rodar(raiz)
    assert codigo == 0, rel.erros
    assert any("sobra.png" in a for a in rel.avisos), rel.avisos


@caso("arquivos idênticos byte a byte viram aviso de duplicata")
def _(raiz):
    criar_arquivo(raiz, "assets/heroi.png")
    shutil.copy(os.path.join(raiz, "assets/heroi.png"), os.path.join(raiz, "assets/heroi2.png"))
    montar_projeto(raiz, [RECURSO_OK], LAYOUT_QUE_USA)
    codigo, rel = rodar(raiz)
    assert codigo == 0, rel.erros
    assert any("idênticos byte a byte" in a for a in rel.avisos), rel.avisos


def main():
    falhas = 0
    for nome, fn in CASOS:
        raiz = tempfile.mkdtemp(prefix="teste_validador_")
        try:
            fn(raiz)
        except AssertionError as e:
            falhas += 1
            print(f"FALHOU  {nome}\n        {e}")
        except Exception as e:  # defeito no próprio teste
            falhas += 1
            print(f"ERRO    {nome}\n        {type(e).__name__}: {e}")
        else:
            print(f"ok      {nome}")
        finally:
            shutil.rmtree(raiz, ignore_errors=True)

    print(f"\n{len(CASOS) - falhas}/{len(CASOS)} casos passaram")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
