---
name: glossario
description: Use whenever you add, change or review acronyms in this dissertation (report/frontmatter/glossary.tex, \gls/\acrshort in the .tex files, the «Lista de Acrónimos»), before any PR that touches report/, or when the user asks to review the glossary ("glossário", "acrónimos", "siglas", "lista de acrónimos", "abreviaturas").
---

# glossario

The «Lista de Acrónimos» is graded under document structure: every acronym in
the text must be defined once, expanded on first use, used consistently and
listed. Missing, unused or wrongly expanded acronyms are visible mistakes.

Instructions are in English. Definitions and text are in **European
Portuguese, academic register**: load `revisao-pt-pt` before writing them.

`GC` below means `.agents/skills/glossario/scripts/gls-check` (run from the
repo root; not on `PATH`). It flattens `report/main.tex` at every `\input`, so
"first use" and enclosing environments (abstract, table, `\todo`) are those of
the PDF.

## Files

| File | Role |
|---|---|
| `report/frontmatter/glossary.tex` | the only place for `\newacronym` definitions (`DEFINITION-FILE`) |
| `report/**/*.tex` | uses: `\gls`, `\glspl`, `\Gls`, `\acrshort`, `\glsentryshort`, ... |
| `.agents/skills/glossario/nao-acronimos.txt` | allow-list: all-caps words that are **not** acronyms (names, IDs, units) |

## Procedure

1. Run `GC` (add `--quiet-info` for a short list). Exit codes: `0` clean;
   `3` warnings to decide; `1` errors; `2` bad input.
2. Fix every **error** (`UNDEFINED`, `DUPLICATE`, `HEADING`, `ABSTRACT`,
   `LONGPLURAL-USED`, and `PLANNED-FINAL` with `--final`). These produce wrong
   output in the PDF.
3. **Decide** every warning with the rules below, and record the decision in the
   file it belongs to: the definition, the text, the allow-list, or a
   `% previsto: …` marker. Never silence a warning without a reason.
4. Rebuild (`cd report && make docker`, 0 errors). In the PDF, check the
   «Lista de Acrónimos» and the first use of every acronym you touched
   (`pdftotext report/main.pdf - | grep -n "…"`).
5. Run `GC` again until it is `0`, or `3` with only justified warnings.
6. Review with `sol-loop` and then `council` (`AGENTS.md`, «Skills»). Review
   focus: the list holds exactly the acronyms used, expansions and plurals are
   right in PT-PT, and every warning decision is justified.
7. Report: definitions added/removed/changed, text replacements, allow-list
   additions, remaining warnings with their justification, and the review
   outcome.

## Rules

### When something is an acronym

- **Define** an acronym when it is used at least twice in the text, or when it is
  an established technical acronym that appears in a table or figure where
  space is short.
- **Planned use** (drafts only): a once-used, unused or not-yet-expanded acronym
  that a later chapter will clearly need may stay, with
  `% previsto: cap. 4 (avaliação)` at the end of its `\newacronym` line.
  - Name the chapter and the reason. A marker without a concrete planned use is
    not allowed.
  - Remove the marker as soon as the use exists (`PLANNED-STALE` tells you).
  - Markers are temporary: `GC --final` turns every remaining one into an error
    (`PLANNED-FINAL`), and CI runs it for final-version tags.
- **Table-only acronyms** (`% só-tabela: Tabela 1.1, vertentes`): an established
  acronym used only in table cells or figures may rely on the «Lista de
  Acrónimos» for its expansion. As soon as the prose mentions it, expand it
  there with `\gls` and remove the marker.
- **Used once, no planned use** (`SINGLE-USE`): write the term in full and
  delete the acronym.
- **Unused** (`UNUSED`): delete the definition. `glossaries` hides it anyway,
  but dead definitions mislead the next writer.
- **Not acronyms** (`CANDIDATE` → allow-list, with a comment saying why):
  - proper names written in capitals (EVIO, MOBI.E, OpenAlex);
  - benchmark and product names (BIRD, Spider);
  - official designations used as part of a name (*Regulamento (UE)*);
  - internal IDs (QI1, O3, P5);
  - SI units (MW, GWh).
- **Real acronyms the text uses without definition** (`CANDIDATE`, e.g.
  ARIMA, PICOC): define them.

### Using acronyms in the text

- Use `\gls{KEY}` (plural `\glspl`, sentence start `\Gls`) in prose; never type
  the short form (`RAW`) or the long form (`MANUAL-LONG`) by hand. Exceptions:
  - quotations;
  - bibliography titles;
  - the Resumo and Abstract, which always write the term in full (skill `abstract`; `MANUAL-LONG` skips them);
  - a long form you deliberately write out because the acronym is not needed (then delete the acronym).
- **Titles and captions** are moving arguments: they also go to the table of
  contents, the lists of figures and tables, and the PDF bookmarks.
  - Use `\glsentryshort{KEY}` there: no first-use expansion, no hyperlink.
  - Never use `\gls` (`HEADING`: the expansion lands in the ToC and the first use breaks).
  - Avoid `\acrshort` (`HEADING-LINK`). In section titles its link breaks the
    PDF bookmarks; in captions it adds links and extra index entries to the
    lists of figures and tables.
  - `\glsentryshort` does not add the entry to the list. If the acronym appears
    nowhere else, add `\glsadd{KEY}` in the text (`NOT-INDEXED`).
- **Abstracts** (`ABSTRACT`): no acronym command in the Resumo or Abstract
  (skill `abstract`). They must stand alone, so write terms in full. `GC` does
  not read the Extended Abstract (`resumo-alargado.tex`, not part of
  `main.tex`): there `abs-check` forbids acronym commands, and spelling out an
  acronym on first use is a manual check.
- **Table cells and figure contents** (`FIRST-USE-IN-FLOAT`): use `\acrshort`.
  It is not a moving argument, and it adds the entry to the list without
  expanding it.
  - Floats move, so an expansion inside them may appear out of reading order.
  - Every acronym must be expanded once in the prose with `\gls`
    (`NEVER-EXPANDED`), unless it is marked `% só-tabela:` or `% previsto:`.
- **First use inside `\todo{}`** (`FIRST-USE-IN-TODO`): acceptable in drafts.
  Re-check when the placeholder is replaced, because in the final build the
  first use moves to the next occurrence.

### Writing definitions

```latex
\newacronym[shortplural={LLM},longplural={modelos de linguagem de grande escala}]
  {LLM}{LLM}{modelo de linguagem de grande escala}
```

- **Key** = short form, ASCII (`SaaS`, `B2B`); alphabetical order by short form
  (`ORDER`).
- **Long form in Portuguese** when an established term exists
  (*erro absoluto médio*, *inteligência artificial*), in lowercase for common
  nouns. Use capitals only for proper names (institutions, regulations:
  *Regulamento Geral sobre a Proteção de Dados*).
- **English-only names** (methods, frameworks, standards with no established
  Portuguese name): the long form is the original in `\textit{}` (`PRISMA` →
  `\textit{Preferred Reporting Items for Systematic Reviews and Meta-Analyses}`).
  When a Portuguese name is also in use (e.g. *modelo autorregressivo integrado
  de médias móveis* for ARIMA), choose one deliberately and keep it. Never put «PT (EN)» inside the long form: the first use prints
  «PT (EN) (SIGLA)», nested parentheses. If the English original of a
  Portuguese expansion helps, give it in the prose.
- **Plurals (PT-PT)**: set `shortplural` equal to the short form for **every**
  acronym (*os LLM*, *os ARIMA*, never *os LLMs*) (`PLURAL`).
  - For multi-word common nouns, also write `longplural` in full
    (`LONGPLURAL`). Without it, the first `\glspl` (and every
    `\acrlongpl`/`\acrfullpl`) prints «…escalas» (`LONGPLURAL-USED`).
  - Proper names need no `longplural`.
- **Verify expansions** you are not sure of in an authoritative source: the
  standard, the original paper, the official title of a law, Priberam or
  Infopédia. If you cite it, follow `pesquisa-bibliografica`.
- One acronym, one meaning: never reuse a short form for two concepts
  (`DUPLICATE`).

## Done when

- `GC` has no errors, and every remaining warning has a recorded decision
  (allow-list comment, marker, or a reason in your report).
- For the submitted version (`make docker-final`, final `v*` tag), `GC --final`
  has no errors: no `% previsto:` markers remain.
- The PDF builds with 0 errors, and the «Lista de Acrónimos» shows exactly the
  acronyms used, correctly expanded, in alphabetical order.
- The final review is done, or reported as incomplete (`AGENTS.md`, «Skills»; step 6). When another skill runs this one, its review covers this step.
- You reported what changed and why.
