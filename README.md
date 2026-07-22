# Martina IG — Publicador na Nuvem (Semana 5)

Despertador na nuvem que publica os posts e stories do Instagram
@martina.investimentos nos horários certos, **sem depender do PC ligado**.

## Como funciona
- As mídias já estão hospedadas no site (`martinacorretora.com.br/ig/s5/`).
- O GitHub Actions dispara nos horários da Semana 5 (arquivo `.github/workflows/publicar.yml`).
- Cada disparo chama `publicar_nuvem.py <slot>`, que publica pela **API oficial** do Instagram.
- A chave do Instagram fica no segredo `IG_TOKEN` do repositório (Settings → Secrets → Actions).

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
