"""Lista os slots do manifest que ja passaram do horario HOJE (horario de SP) e ainda nao
estao em publicados.json. Usado pelo disparo de hora em hora: se o GitHub atrasar ou pular um
horario, o proximo disparo pega o que ficou pra tras — e nada sai duplicado.

Uso: python pendentes_hoje.py                   -> imprime um slot por linha, em ordem de horario
     python pendentes_hoje.py --marcar SLOT STATUS  -> registra o slot em publicados.json
"""
import json
import sys
from datetime import datetime, timedelta, timezone

SP = timezone(timedelta(hours=-3))
MANIFEST = "manifest.json"
PUBLICADOS = "publicados.json"


def carregar_publicados():
    try:
        with open(PUBLICADOS, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def pendentes():
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)
    slots = manifest.get("slots", manifest)
    publicados = carregar_publicados()
    agora = datetime.now(SP)
    devidos = []
    for nome, slot in slots.items():
        if not isinstance(slot, dict) or nome in publicados:
            continue
        try:
            quando = datetime.strptime(slot.get("quando", ""), "%Y-%m-%d %H:%M (SP)").replace(tzinfo=SP)
        except ValueError:
            continue  # "publicacao manual" e afins nao entram no automatico
        if quando.date() == agora.date() and quando <= agora:
            devidos.append((quando, nome))
    return [nome for _, nome in sorted(devidos)]


def marcar(slot, status):
    publicados = carregar_publicados()
    publicados[slot] = {"status": status, "em": datetime.now(SP).strftime("%Y-%m-%d %H:%M")}
    with open(PUBLICADOS, "w", encoding="utf-8") as f:
        json.dump(publicados, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--marcar":
        marcar(sys.argv[2], sys.argv[3])
    else:
        print("\n".join(pendentes()))
