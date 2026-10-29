# From Choices to Sums

**Connections to OpenAI's Subset-Sum Algorithms**

Jonathan R. Landers · October 28, 2026 · Working draft

[Read HTML](From_Choices_to_Sums.html) · [Four-page PDF](From_Choices_to_Sums.pdf) ·
[LaTeX source](From_Choices_to_Sums.tex)

The note follows one question: which information lets us resolve many subset
choices together? It develops the deficiency connection to Note V, explains
compatible records and OpenAI's modular checksum, and connects those ideas to
Note VII's reusable geometric table. A derived algorithm combines distinct
exceptional sums with the shared table and gives an explicit runtime bound.
The exposition uses the repository's saved results on support selection,
exact completion and avoided table construction.

## Sources

The repository material was read at commit
`4e880b7698e24d8f5ec60347b1c46d847a78e6cd`.
The OpenAI source was read at commit
`7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a` of
[openai/math](https://github.com/openai/math/tree/7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a).
The paper's external manuscript links use that fixed revision.
[SOURCES.json](SOURCES.json) records the exact source paths and local hashes.

The combined algorithm and its bound are a mathematical derivation from the
existing support and table constructions. The empirical paragraphs report
the saved Note V and VII studies. The original
[connections handoff](SUBSET_SUM_OPENAI_CONNECTIONS.md) supplies a longer reading map.

## Rebuild

From the repository root:

```powershell
python build_papers.py --paper connections
python tools/check_links.py
```

The build runs LaTeX twice, enforces a maximum of four PDF pages, and generates
the matching HTML from the same manuscript. Scratch files go under
`.build/latex/openai-connections/`. The dependencies are the repository's
existing `pdflatex` and `pandoc` tools.
