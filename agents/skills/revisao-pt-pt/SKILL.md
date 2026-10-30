---
name: revisao-pt-pt
description: Use whenever you write, translate or review Portuguese text in this repo (report .tex, abstract, issues, PRs, releases, README, research notes), or when the user asks to correct spelling, grammar, style or register ("revê", "corrige", "ortografia", "gramática", "PT-PT", "português de Portugal", "registo académico").
---

# revisao-pt-pt

All Portuguese in this repo is **European Portuguese (PT-PT), academic
register, post-1990 spelling agreement (AO90)**, as used at ISEP. Brazilian
forms are errors here, even when correct in pt-BR. Some rules below are
**house preferences** for this dissertation (marked *preference*), not
grammar errors: apply them to our own prose, never to verbatim quotations.

Instructions are in English; the text you produce is PT-PT.

## Procedure

1. **Tool pass.** Start the local LanguageTool server once (text never
   leaves the machine; never use the public LanguageTool API, because
   drafts may contain confidential company information):

   ```bash
   docker start lt-evio 2>/dev/null || docker run -d --name lt-evio -p 127.0.0.1:8010:8010 erikvl87/languagetool
   for i in $(seq 60); do curl -sf --connect-timeout 2 --max-time 2 http://127.0.0.1:8010/v2/languages >/dev/null && break; sleep 2; done
   .agents/skills/revisao-pt-pt/scripts/lt-check report/ch1/chapter1.tex
   ```

   The first start takes ~20 s. If the server still does not answer after
   the loop (Docker down, container failed), do not retry forever: run

   ```bash
   .agents/skills/revisao-pt-pt/scripts/lt-check --no-lt report/ch1/chapter1.tex
   ```

   `lt-check` reads LaTeX/Markdown markup as markup and reports
   `file:line:col: [RULE] message | 'text' -> fix`. It adds checks that
   LanguageTool misses (`PTPT_*`). Spelling and foreign-word findings inside
   `\textit{}`/`\emph{}` are dropped, and Markdown tables and code are not
   checked by the tool. Portuguese you write inside table cells (e.g. the
   `sources.md` registry) still gets the manual checklist pass (step 3).
   With `--no-lt` only the extra checks run: say the LanguageTool pass was
   skipped.

   Exit codes: `0` no findings; `1` findings to judge (step 2); `2` usage
   error or server unreachable.

   Other options:
   - `--env NAME` checks only the text inside `\begin{NAME}…\end{NAME}`
     (e.g. `--env abstract` for the Resumo).
   - `--lang en-GB` checks British English instead, for the Abstract and the
     Extended Abstract only (skill `abstract`). The extra checks become
     `EN_*`: US spelling, *-ize*, contractions, first person, straight quotes
     and decimal commas. `EN_FIRST_PERSON` also hits Roman numerals
     («Phase I», «Table I»): ignore those.
   - LanguageTool's false-friend hints are off by default. `--falsos-amigos`
     turns them on.
2. **Judge every finding.** The tool is a hint, not an authority. Fix real
   errors; ignore false positives (proper names, citation placeholders,
   English inside `\textit{}`); add recurring project terms to
   `wordlist.txt`.
3. **Manual pass** with the checklist below — the tool does not catch
   register, clitic placement in every case, or anglicisms in context.
4. **Edit minimally.** Correct language, never content: do not change
   claims, numbers, citations, labels or meaning. If a sentence is unclear
   or a claim looks wrong, flag it instead of rewriting it.
5. **Rebuild** what you touched: `cd report && make docker` for the report,
   `make docker-resumo-alargado` for the Extended Abstract (both if both
   changed). Every build must have 0 errors.
6. **Review** with `sol-loop` and then `council` (`AGENTS.md`, «Skills»).
   Review focus: every correction is right in PT-PT academic register (AO90)
   and no correction changed the meaning.
7. **Report** a short list: `file:line — antes → depois (regra)`, plus what
   you flagged but did not change, and the review outcome.

## LaTeX safety

Never edit inside: command names, `\cite*{}`/`\ref{}`/`\label{}` keys, math,
`verbatim`/`lstlisting`, URLs, file paths, BibTeX fields (titles keep their
original language and spelling). Keep `~` before `\parencite`, `\ref`,
`\cite` and units. Use `\enquote{}` for quotations (renders «…»).

## Checklist

### Spelling (AO90, PT-PT)

- Silent consonants are dropped: *ação*, *ótimo*, *objetivo*, *direção*,
  *receção*, *perspetiva*.
- Pronounced consonants are kept: *facto*, *contacto*, *característica*.
- Where AO90 (Base IV 1.º c) allows two spellings (*setor*/*sector*,
  *carateres*/*caracteres*), pick one and use it throughout the document.
- Accents: *económico*, *académico*, *António*, *género*, *fenómeno*
  (not *econômico*, *acadêmico*).
- Months and seasons lowercase (*outubro*, *verão*); weekdays lowercase.
- Hyphenation per AO90: *autoavaliação*, *coautor*, *pré-processamento*,
  *semiautomático*, *bem-sucedido*.

### Vocabulary (pt-BR → PT-PT)

| pt-BR | PT-PT |
|---|---|
| usuário | utilizador |
| arquivo (computer file) | ficheiro — but *arquivo* as a collection or place (*arquivo histórico*) is correct |
| tela | ecrã |
| equipe / time | equipa |
| registro, registrar | registo, registar |
| planejamento, planejar | planeamento, planear |
| banco de dados | base de dados |
| aplicativo, (o) celular | aplicação, telemóvel (but *rede celular* is correct) |
| deletar, checar, rodar (código) | eliminar/apagar, verificar, executar |
| gerenciar, gerenciamento | gerir, gestão |
| pesquisador | investigador |
| treinamento | treino (modelos) / formação (pessoas) |
| em nível de | ao nível de («no âmbito de»); *a nível* only with an adjective (*a nível mundial*) |

### Grammar

- *Preference*: *estar a* + infinitive (*está a analisar*), not *estar* +
  gerund (*está analisando*). The gerund form also exists in some European
  Portuguese varieties, but standard written PT-PT uses *estar a*. Gerunds with
  *ir*/*vir*/*andar* (*vai aumentando*, *vem crescendo*) are standard PT-PT
  with a gradual meaning: do not replace them.
- **Clitics**: enclisis by default (*Pretende-se avaliar*, *Considera-se
  que*); proclisis after negation, most subordinators, relatives and some
  adverbs (*não se verifica*, *que se pretende*, *já se observou*). Never
  start a sentence with a clitic pronoun (*Se pretende avaliar…* ✗ when *se*
  is the pronoun); *Se* as a conditional conjunction (*Se pretende avaliar o
  modelo, …*) is correct — judge from context. Mesoclisis or a
  rewrite in the future/conditional (*realizar-se-á* or *será realizado*).
- **Crase**: *à*/*às* for *a* + article *a(s)* (*devido à*, *face à*,
  *relativamente às*) and *àquele(s)*, *àquela(s)*, *àquilo* for *a* +
  demonstrative; never before masculine nouns or verbs.
- Agreement (number/gender) across long noun phrases and with
  percentages: *28% dos inquiridos referiram*.
- *onde* only for places; for abstract contexts use *em que*/*no qual*.
- *através de* for a medium or crossing, not as a vague "by"
  (*recorrendo a*, *por meio de*, *com base em*).

### Academic register

- Impersonal voice: *propõe-se*, *pretende-se*, *foi realizado*,
  *o presente trabalho*. No *eu*, no informal *nós*, no *você*, no *a gente*.
- Precise verbs instead of *fazer*/*ter*/*usar* where natural:
  *realizar*, *elaborar*, *dispor de*, *utilizar*.
- No colloquialisms or intensifiers (*muito*, *bastante*, *enorme*,
  *achar que*); hedge claims that the evidence does not fully support
  (*sugere*, *indica*, *é plausível que*).
- One idea per sentence; avoid sentences over ~35 words.
- Avoid starting three consecutive sentences with the same word.

### Anglicisms and terminology

- Use the established Portuguese term, with the English original in
  italics and parentheses on first use only:
  *aprendizagem automática* (*machine learning*), *conjunto de dados*
  (*dataset*), *desempenho* (*performance*), *afinação* (*fine-tuning*),
  *modelo de linguagem de grande escala* (*Large Language Model*),
  *painel de indicadores* (*dashboard*), *variável explicativa* (*feature*).
- Keep in English, always in `\textit{}`, terms with no settled Portuguese
  equivalent: *benchmark*, *prompt*, *pipeline*, *framework*, *stack*,
  *logs*, *snowballing*, *Text-to-SQL* (proper name, no italics).
- Acronyms: expand in Portuguese where one exists; give the English
  original in the prose on first use, not inside the acronym. Acronyms do
  not take a plural *-s* in PT-PT (*os LLM*, *os KPI*), and the long plural
  must be written out, or `glossaries` appends an *s* to the whole phrase:

  ```latex
  \newacronym[shortplural={LLM},longplural={modelos de linguagem de grande escala}]
    {LLM}{LLM}{modelo de linguagem de grande escala}
  ```

### Typography and numbers

- Decimal comma (*28,5*), thousands with a thin space (`12\,860`).
  Percentages: `28,5\%` or `28,5~\%` — pick one and be consistent.
- Dates `dd/mm/aaaa` or *29 de outubro de 2026*.
- Quotation marks «…» (`\enquote{}`); inner quotes “…”.
- Dashes: en dash for ranges (`2020--2025`), em dash for parenthesis
  (`---`), no spaces around en dashes in ranges.
- Units with a non-breaking space: `200~MWh`, `30~dias`.

## When in doubt

Look it up instead of guessing, and cite the authority in your report:

- Ciberdúvidas da Língua Portuguesa — https://ciberduvidas.iscte-iul.pt
- Dicionário Priberam (set to *Português Europeu, pós-AO*) — https://dicionario.priberam.org
- Infopédia (Porto Editora) — https://www.infopedia.pt
- Portal da Língua Portuguesa / Vocabulário Ortográfico do Português — http://www.portaldalinguaportuguesa.org

## Done when

- `lt-check` shows no unexplained finding on the **lines you changed**
  (pre-existing findings elsewhere are out of scope unless asked).
- The manual checklist was applied, and the PDF builds with 0 errors.
- The final review is done, or reported as incomplete (`AGENTS.md`, «Skills»; step 6). When another skill runs this one, its review covers this step.
- You reported the corrections and anything flagged but left unchanged.
