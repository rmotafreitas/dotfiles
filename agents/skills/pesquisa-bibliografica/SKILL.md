---
name: pesquisa-bibliografica
description: Use whenever you search for, verify, register, summarise or cite any source for this dissertation (papers, reports, legislation, statistics, company or market pages), run the literature-search protocol, or do snowballing ("pesquisa", "fontes", "artigos", "referências", "snowballing", "cascata", "estado da arte", "estudo de mercado").
---

# pesquisa-bibliografica

Every source in this repo must be real, verified and registered. A wrong or
invented reference hurts the grade more than a missing one. When in doubt,
mark it `por verificar` and say so.

Instructions are in English. Everything you write into the repo (registry
rows, summaries, report text) is in **European Portuguese, academic
register**: load `revisao-pt-pt` before writing prose.

`VB` below means `.agents/skills/pesquisa-bibliografica/scripts/verify-bib`
(run from the repo root; it is not on `PATH`).

## Files

| File | Role |
|---|---|
| `research/protocolo-pesquisa.md` | PICOC, search strings per database, filters, inclusion/exclusion criteria |
| `research/search-log.csv` | one row per search actually run (replaces the old «Registo de pesquisas» table in `sources.md`, which only points here) |
| `research/sources.md` | registry of every source (ID, key, URL/DOI, type, rank, found via, status, verified, used in) |
| `research/snowball-qi*.md` | per-QI cascade detail (contribution, numbers, limitations, gaps) |
| `report/mainbibliography.bib` | BibTeX, same key as the registry |
| `.agents/skills/pesquisa-bibliografica/scripts/verify-bib` | checks DOIs (Crossref, then DataCite) and URLs |

If one of these is missing, create it from the structure of the others; do
not invent a new layout.

Dates: ISO `AAAA-MM-DD` in the CSV and in the `.bib` (`urldate`, `date`);
`dd/mm/aaaa` everywhere else (`sources.md`, Markdown, report), matching the
existing rows.

## 1. Run a protocol search

1. Use the exact string for that database from `protocolo-pesquisa.md`. If
   you change it, change the protocol first and say why.
2. `search-log.csv` has exactly this header (9 columns; create the file
   with it if it does not exist):

   ```
   data,base,query,filtros,resultados,triagem_titulo,triagem_resumo,incluidos,notas
   ```
3. As soon as the database returns, append one row with `data`, `base`,
   `query`, `filtros` and `resultados` filled and `triagem_titulo`,
   `triagem_resumo`, `incluidos` **empty** (`notas` optional). Fill each
   screening count in the same row when that stage is finished. Empty means
   "not yet known"; `0` means an observed zero. Never estimate a count.
4. Always write with Python's `csv` module (queries contain commas and `"`).
   Append a row (9 values):

   ```bash
   python3 -c 'import csv,sys; csv.writer(open("research/search-log.csv","a",newline="")).writerow(sys.argv[1:])' \
     2026-11-03 Scopus '("electric vehicle" OR EV) AND forecasting' '2020-2026; EN' 412 '' '' '' ''
   ```

   To update a row, read the whole file with `csv.reader`, change that row,
   and rewrite the file with `csv.writer`; never edit the CSV by hand.
5. Screen title → abstract → full text with the protocol's criteria. Record
   an exclusion reason in `sources.md` › Fontes excluídas only for candidates
   you opened; counts alone go in the log.

Access rules:

- Scopus, IEEE Xplore and Web of Science need the user's ISEP/b-on login.
  Use the browser session the user logged into; never ask for passwords.
- Google Scholar, RECIPP, RCAAP and the CORE aggregator (core.ac.uk) block
  or rate-limit scripts. Do not scrape them, do not loop requests, and never
  bypass a CAPTCHA, Cloudflare or "not a bot" page. If blocked, stop, write
  `bloqueado` in `notas`, and use an allowed route (OpenAlex, Crossref,
  Semantic Scholar API, publisher pages, arXiv) or ask the user to open it.
- Keep request rates low (≤1 request/second to any one host).

## 2. Snowballing cascade (adapted from Wohlin 2014)

Wohlin's procedure screens **every** reference and citation of every paper
in the start set, iterating until nothing new appears. This repo uses a
lighter *cascade*: one chosen paper per step. When you describe it in the
report, call it «cascata adaptada de Wohlin (2014)» and state the deviation.

1. Seed: pick one favourite paper for the QI — peer reviewed, on target,
   strong method, ideally a recent survey or benchmark. Log the query that
   found it.
2. Backward: read its whole reference list. Forward: read the papers that
   cite it (Semantic Scholar/OpenAlex "cited by"; Google Scholar only by
   hand). Note how many you screened in the cascade file.
3. Choose the next favourite from those, and repeat. Every new paper records
   `Encontrada via`: `seed (<base>: <query>)`, `backward de P3` or
   `forward de T2`. Never claim a link you did not see in a reference list
   or citing paper.
4. Prefer the peer-reviewed version over the preprint; cite the preprint
   only if no reviewed version exists, and say so.
5. Stop a branch when new papers add nothing to the QI. Draw the chain in
   `sources.md` › Snowballing.

## 3. Verify before registering

```bash
.agents/skills/pesquisa-bibliografica/scripts/verify-bib report/mainbibliography.bib --keys <key>
```

The script is a first filter, not the verification. A source is verified
only when **you** opened its DOI or official page and saw that authors,
title, venue and year match the `.bib` entry.

| Script status | Meaning | What to do |
|---|---|---|
| `OK` (Crossref/DataCite) | title, first author and year match (a one-year gap is tolerated: online-first vs issue year) | Check the venue and the year you cite, then `sim (Crossref\|DataCite, dd/mm/aaaa)` |
| `OK-URL` | the page loads (HTTP 2xx); metadata **not** checked — search pages and homepages also load | Open it; confirm title, author and date on that page, then `sim (URL, dd/mm/aaaa)`; otherwise `não` |
| `MISMATCH` | the Crossref/DataCite record disagrees with the `.bib` (title, first author or year), or the `.bib` lacks author/year | Fix the `.bib` from the publisher record, never the other way round |
| `NOT-FOUND` | DOI unknown to Crossref and DataCite, or URL 404 | Open `https://doi.org/<doi>`; if it does not resolve to the same work, the source is `não` verified and must not be cited |
| `UNREACHABLE` | site blocks scripts (401/403/429), is down (5xx) or network failed | Check by hand in a browser: `sim (manual, dd/mm/aaaa)` |
| `MISSING-ID` | no `doi`/`url` (books, manuals) | Find a DOI/URL if one exists; else check by hand (library catalogue, publisher): `sim (manual, dd/mm/aaaa)` |
| `ERROR` | key missing, bad input, server error | Fix the input or retry later |

- Numbers you quote (accuracy, %, counts) must come from a table or sentence
  you read in the paper. If you could not read it, mark the number
  `por verificar` in the registry and do not put it in the report.
- Rankings: SJR quartile (scimagojr.com) for journals, CORE rank
  (portal.core.edu.au — not the core.ac.uk aggregator) for conferences, with
  the ranking year. Unknown is a valid value; a guessed rank is not.

Before any PR that touches the report, run

```bash
.agents/skills/pesquisa-bibliografica/scripts/verify-bib report/mainbibliography.bib --cited report
```

Every line must be `OK`, or `OK-URL`/`UNREACHABLE`/`MISSING-ID` with a
matching `sim (…)` manual check already recorded in `sources.md`. The script
does not read `sources.md`: for each such key, open its row (`grep -n "KEY"
research/sources.md`) and confirm the `sim (…)`. Exit codes:
`0` all `OK`; `3` only manual checks pending; `1` a hard problem
(`MISMATCH`, `NOT-FOUND`, `ERROR`); `2` bad input.

## 4. Register

Add the row to `sources.md` in the right table:

- IDs: `P#` forecasting (QI1), `T#` natural language / Text-to-SQL (QI2),
  `M#` method, `C#` context (statistics, legislation, company), `S#` existing
  solutions / market. Never reuse an ID.
- BibTeX key for **new** entries: `firstauthorYEARword`, lowercase ASCII
  (`kim2021charging`). Never rename existing keys (citations would break).
- BibTeX: full author list from the publisher (`and others` only when the
  publisher itself truncates); protect acronyms in titles with braces
  (`{LLM}`); `doi` when there is one, else `url`; `@online` entries need
  `url` and `urldate`.
- The `.bib` and `sources.md` share the key. Verification status lives only
  in `sources.md`.

## 5. Grey literature

News, company websites, consultancy reports, blogs and vendor docs (`C#`,
`S#`) may support context and the market study only. Never use them as
evidence for a scientific claim, never as the only support for a number
when a primary source exists, and prefer the primary source (e.g. a
regulator's own data over a newspaper quoting it). Company self-descriptions
describe the company, nothing more.

## 6. Delegating research

If the user asks for other agents (e.g. a Sol cascade), each brief must say:
**read-only — do not create, edit or delete files, do not commit, do not
start subagents**; give the QI, known seeds, this method, and the required
output (citation, DOI/URL, found via, rank, citation count with source and
date, contribution with numbers, limitation, BibTeX). Treat their output as
candidates: verify every item yourself (section 3) before registering.
Codex Sol and Luna are always read-only in this repo.

## 7. Writing about sources

- Summaries and report text: PT-PT academic (`revisao-pt-pt`), impersonal.
- Synthesise across papers (evidence → limitation → gap → QI), do not list
  papers one by one.
- Cite with `\parencite{}` / `\textcite{}`; every factual sentence that is
  not common knowledge has a citation.
- Disclose AI assistance in the report's «Utilização de conteúdo gerado por
  IA» section; never cite an AI tool as a source.

## 8. Review

End every run with `sol-loop` and then `council` on what it changed (`AGENTS.md`, «Skills»). Review focus: every new source is real and says what the text claims, numbers match the source, and the registry, `.bib` and `search-log.csv` agree.

## Done when

- Every new source has a registry row, a `.bib` entry and a verification
  status.
- Every search run is in `search-log.csv`, with no estimated counts.
- The `--cited report` check meets the rule at the end of section 3.
- The final review is done, or reported as incomplete (`AGENTS.md`, «Skills»; section 8). When another skill runs this one, its review covers this step.
- Report: what you searched, what you added (IDs), what is `por verificar`,
  and what is blocked on the user (logins, manual checks).
