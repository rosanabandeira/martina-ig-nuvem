# -*- coding: utf-8 -*-
"""
publicar_tiktok.py — publicador do TikTok da Martina (@martina.one.imoveis) que roda NA NUVEM
(GitHub Actions), espelhando o publicar_nuvem.py do Instagram.

Reusa o MESMO manifest.json do IG: so publica slots tipo "reel" (video) e "feed" (carrossel de
foto -> TikTok PHOTO post). Stories NAO vao pro TikTok (decisao da Rosana).

A chave vem da variavel de ambiente TIKTOK_ACCESS_TOKEN (segredo do GitHub, renovado 1x/dia
pelo renovar_token_tiktok.py local, porque o access_token do TikTok só dura 1 dia).

Enquanto o app estiver em modo SANDBOX, o post só aparece pra conta autorizada (Rosana) —
nao fica publico. Produção exige "Submit for review" no TikTok Developer.

Uso:
    python publicar_tiktok.py s14_sex30_roi_reel            # publica o slot
    python publicar_tiktok.py s14_sex30_roi_reel --dry-run  # monta mas NAO publica
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

API_BASE = "https://open.tiktokapis.com/v2"
TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "").strip()

# Enquanto o app nao passar por "Submit for review", todo post so pode ser SELF_ONLY
# (so a propria Rosana ve). Trocar para PUBLIC_TO_EVERYONE depois da aprovacao.
PRIVACY_LEVEL = os.environ.get("TIKTOK_PRIVACY_LEVEL", "SELF_ONLY")


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


class TikTokError(Exception):
    pass


def _headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    }


def _post(path, body):
    r = requests.post(f"{API_BASE}{path}", headers=_headers(), json=body, timeout=90)
    j = r.json()
    err = j.get("error", {})
    if err.get("code") not in (None, "ok"):
        raise TikTokError(f"{err.get('code')}: {err.get('message')}")
    return j.get("data", {})


def _status(publish_id):
    return _post("/post/publish/status/fetch/", {"publish_id": publish_id})


def _esperar_processar(publish_id, timeout=240):
    inicio = time.time()
    while time.time() - inicio < timeout:
        st = _status(publish_id)
        status = st.get("status")
        if status == "PUBLISH_COMPLETE":
            return st
        if status == "FAILED":
            raise TikTokError(f"Publicacao falhou: {st}")
        log(f"Processando... ({status})")
        time.sleep(6)
    raise TikTokError("Tempo esgotado esperando o post processar.")


def publicar_slot(nome, dry_run=False):
    slot = MANIFEST["slots"].get(nome)
    if not slot:
        raise TikTokError(f"slot desconhecido: {nome}")
    tipo = slot["tipo"]
    if tipo not in ("reel", "feed"):
        raise TikTokError(f"slot '{nome}' e tipo '{tipo}' -- TikTok so publica reel/feed (nao story)")

    base = MANIFEST["base_url"].rstrip("/")
    urls = [a if a.startswith("http") else f"{base}/{a}" for a in slot["arquivos"]]
    legenda = slot.get("legenda", "")[:2200]  # limite de caption do TikTok

    log(f"Slot '{nome}' | tipo={tipo} | {len(urls)} arquivo(s) | privacy={PRIVACY_LEVEL}")
    for u in urls:
        log(f"  midia: {u}")

    if dry_run:
        log("[DRY-RUN] nao chama a API do TikTok. Body que seria enviado:")
        if tipo == "reel":
            log(json.dumps({"post_info": {"title": legenda, "privacy_level": PRIVACY_LEVEL},
                             "source_info": {"source": "PULL_FROM_URL", "video_url": urls[0]}},
                            ensure_ascii=False))
        else:
            log(json.dumps({"post_info": {"title": legenda, "privacy_level": PRIVACY_LEVEL},
                             "source_info": {"source": "PULL_FROM_URL", "photo_images": urls,
                                              "photo_cover_index": 0},
                             "post_mode": "DIRECT_POST", "media_type": "PHOTO"},
                            ensure_ascii=False))
        return

    if tipo == "reel":
        data = _post("/post/publish/video/init/", {
            "post_info": {
                "title": legenda,
                "privacy_level": PRIVACY_LEVEL,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000,
            },
            "source_info": {"source": "PULL_FROM_URL", "video_url": urls[0]},
        })
    else:
        data = _post("/post/publish/content/init/", {
            "post_info": {
                "title": legenda,
                "privacy_level": PRIVACY_LEVEL,
                "disable_comment": False,
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_images": urls,
                "photo_cover_index": 0,
            },
            "post_mode": "DIRECT_POST",
            "media_type": "PHOTO",
        })

    publish_id = data.get("publish_id")
    if not publish_id:
        raise TikTokError(f"resposta sem publish_id: {data}")
    log(f"publish_id={publish_id}, aguardando processar...")
    st = _esperar_processar(publish_id)
    log(f"PUBLICADO no TikTok. publish_id={publish_id}")
    return st


def main():
    ap = argparse.ArgumentParser(description="Publicador do TikTok na nuvem")
    ap.add_argument("slot", help="nome do slot (mesmo nome usado no publicar_nuvem.py do IG)")
    ap.add_argument("--dry-run", action="store_true", help="monta mas NAO publica")
    args = ap.parse_args()

    if not TOKEN and not args.dry_run:
        log("ERRO: variavel TIKTOK_ACCESS_TOKEN vazia (configure o segredo no GitHub).")
        sys.exit(1)

    try:
        publicar_slot(args.slot, dry_run=args.dry_run)
        log("Concluido.")
    except TikTokError as e:
        log(f"ERRO: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
