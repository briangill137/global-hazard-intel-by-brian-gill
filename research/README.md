# Research Assets

This folder contains an IEEE-style conference paper scaffold for Global Hazard Intel.

Files:

- `paper.tex` - main paper source
- `references.bib` - bibliography entries

Compile example:

```bash
pdflatex paper.tex
bibtex paper
pdflatex paper.tex
pdflatex paper.tex
```

The document uses `IEEEtran` conference style and includes diagrams through TikZ.
