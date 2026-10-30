# Martina IG + TikTok — Publicador na Nuvem

Despertador na nuvem que publica os posts, stories (só IG) e reels do Instagram
@martina.investimentos e do TikTok @martina.one.imoveis nos horários certos,
**sem depender do PC ligado**.

## Como funciona
- As mídias já estão hospedadas no site (`martinacorretora.com.br/ig/...`).
- O GitHub Actions dispara nos horários certos (arquivo `.github/workflows/publicar.yml`).
- Cada disparo chama `publicar_nuvem.py <slot>` (Instagram) e, se o slot for `feed` ou `reel`
  (não `story`), também `publicar_tiktok.py <slot>` — mesmo manifest.json, mesma mídia.
- Chaves nos segredos do repositório (Settings → Secrets → Actions): `IG_TOKEN` e
  `TIKTOK_ACCESS_TOKEN`.

## TikTok — modo sandbox
Enquanto o app "Martina Automação" não passar por **Submit for review** no TikTok Developer,
todo post sai com `privacy_level=SELF_ONLY` — só a própria Rosana vê, não fica público.
O `TIKTOK_ACCESS_TOKEN` vale só **1 dia**; é renovado localmente 1x/dia por
`Martina_Posts_Instagram/renovar_token_tiktok.py` (usa o `refresh_token`, válido 365 dias e
que o TikTok rotaciona a cada uso — por isso o script salva o novo refresh_token local
a cada renovação).

## Testar sem publicar
GitHub → aba **Actions** → "Publicar Instagram (Semana 5)" → **Run workflow** →
escolha o slot e deixe *dry_run = true*. Ele monta o post mas não publica.

## Slots (Semana 5 · 27/07 a 02/08)
| Slot | Tipo | Quando (SP) |
|---|---|---|
| stories_seg | story | 27/07 09:00 |
| seg_meme | feed | 27/07 12:00 |
| stories_ter | story | 28/07 09:00 |
| stories_qua | story | 29/07 09:00 |
| qua_hottake | feed (carrossel) | 29/07 12:00 |
| stories_qui | story | 30/07 09:00 |
| stories_sex | story | 31/07 09:00 |
| sex_reel | reel | 31/07 12:00 |
| stories_sab | story | 01/08 09:00 |
| stories_dom | story | 02/08 09:00 |

## Atenção — chave (token)
O `IG_TOKEN` vale ~60 dias (renovar até ~2026-09-19). Para semanas futuras,
gerar/renovar e atualizar o segredo `IG_TOKEN`.
