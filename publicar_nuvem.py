# -*- coding: utf-8 -*-
"""
publicar_nuvem.py — publicador do Instagram da Martina que roda NA NUVEM (GitHub Actions).

Diferença pro publicador local: NÃO hospeda imagem nem faz deploy no Vercel.
As mídias já estão públicas no site (pasta /ig/s5/). Este script só chama a API
oficial do Instagram com as URLs prontas — por isso funciona sem PC ligado.

A chave do Instagram vem da variável de ambiente IG_TOKEN (segredo do GitHub).

Uso:
    python publicar_nuvem.py seg_meme            # publica o slot
    python publicar_nuvem.py stories_seg
    python publicar_nuvem.py seg_meme --dry-run  # monta mas NÃO publica (teste)
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

import requests

BASE_DIR = Path(__file__).resolve().parent
MANIFEST = json.loads((BASE_DIR / "manifest.json").read_text(encoding="utf-8"))

IG_USER_ID = os.environ.get("IG_USER_ID", "17841472047476831")
GRAPH_BASE = os.environ.get("IG_GRAPH_BASE", "https://graph.instagram.com/v21.0")
TOKEN = os.environ.get("IG_TOKEN", "").strip()


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


class IGError(Exception):
    pass


def _post(path, data):
    data = {**data, "access_token": TOKEN}
    r = requests.post(f"{GRAPH_BASE}/{path}", data=data, timeout=90)
    j = r.json()
    if "error" in j:
        raise IGError(j["error"].get("message", str(j["error"])))
    return j


def _get(path, params):
    params = {**params, "access_token": TOKEN}
    r = requests.get(f"{GRAPH_BASE}/{path}", params=params, timeout=90)
    j = r.json()
    if "error" in j:
        raise IGError(j["error"].get("message", str(j["error"])))
    return j


def _esperar_video(cid, timeout=240):
    inicio = time.time()
    while time.time() - inicio < timeout:
        st = _get(cid, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return True
        if code == "ERROR":
            raise IGError(f"Processamento do video falhou: {st.get('status')}")
        log(f"Processando video... ({code})")
        time.sleep(6)
    raise IGError("Tempo esgotado esperando o video processar.")


def _container_pronto(cid, timeout=90):
    """Espera o container ficar FINISHED antes de publicar (evita 'Media ID is not available')."""
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            st = _get(cid, {"fields": "status_code"})
            if st.get("status_code") == "FINISHED":
                return True
        except IGError:
            pass
        time.sleep(4)
    return False


def _publicar(cid):
    # o container pode levar alguns segundos pra ficar publicavel (stories/imagens inclusive)
    _container_pronto(cid)
    ultimo_erro = None
    for tentativa in range(6):
        try:
            mid = _post(f"{IG_USER_ID}/media_publish", {"creation_id": cid})["id"]
            log(f"PUBLICADO. media id = {mid}")
            return mid
        except IGError as e:
            ultimo_erro = e
            msg = str(e).lower()
            if "not available" in msg or "not ready" in msg or "media id" in msg:
                log(f"container ainda nao pronto (tentativa {tentativa+1}/6), aguardando 8s...")
                time.sleep(8)
                continue
            raise
    raise IGError(f"nao publicou apos varias tentativas: {ultimo_erro}")


def publicar_slot(nome, dry_run=False):
    slot = MANIFEST["slots"].get(nome)
    if not slot:
        raise IGError(f"slot desconhecido: {nome}. Validos: {', '.join(MANIFEST['slots'])}")
    base = MANIFEST["base_url"].rstrip("/")
    urls = [f"{base}/{a}" for a in slot["arquivos"]]
    tipo = slot["tipo"]
    legenda = slot.get("legenda", "")
    log(f"Slot '{nome}' | tipo={tipo} | {len(urls)} arquivo(s)")
    for u in urls:
        log(f"  midia: {u}")

    if tipo == "reel":
        cid = _post(f"{IG_USER_ID}/media",
                    {"video_url": urls[0], "media_type": "REELS", "caption": legenda})["id"]
        _esperar_video(cid)
        if dry_run:
            log(f"[DRY-RUN] reel montado, NAO publicado. container={cid}")
            return
        return _publicar(cid)

    if tipo == "story":
        publicados = []
        for u in urls:
            if u.lower().endswith((".mp4", ".mov")):
                cid = _post(f"{IG_USER_ID}/media",
                            {"video_url": u, "media_type": "STORIES"})["id"]
                _esperar_video(cid)
            else:
                cid = _post(f"{IG_USER_ID}/media",
                            {"image_url": u, "media_type": "STORIES"})["id"]
            if dry_run:
                log(f"[DRY-RUN] story montado, NAO publicado. container={cid}")
                continue
            publicados.append(_publicar(cid))
            time.sleep(3)  # respiro entre stories
        return publicados

    # feed / carrossel
    if len(urls) == 1:
        cid = _post(f"{IG_USER_ID}/media", {"image_url": urls[0], "caption": legenda})["id"]
    else:
        filhos = [_post(f"{IG_USER_ID}/media",
                        {"image_url": u, "is_carousel_item": "true"})["id"] for u in urls]
        cid = _post(f"{IG_USER_ID}/media",
                    {"media_type": "CAROUSEL", "children": ",".join(filhos),
                     "caption": legenda})["id"]
    if dry_run:
        log(f"[DRY-RUN] feed montado, NAO publicado. container={cid}")
        return
    return _publicar(cid)


def main():
    ap = argparse.ArgumentParser(description="Publicador do Instagram na nuvem")
    ap.add_argument("slot", help="nome do slot (ex: seg_meme, stories_seg)")
    ap.add_argument("--dry-run", action="store_true", help="monta mas NAO publica")
    args = ap.parse_args()

    if not TOKEN:
        log("ERRO: variavel IG_TOKEN vazia (configure o segredo no GitHub).")
        sys.exit(1)

    try:
        publicar_slot(args.slot, dry_run=args.dry_run)
        log("Concluido.")
    except IGError as e:
        log(f"ERRO: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
