# Stage 6: Manuscript Materials

Publication materials for the Communication.

## Files

- **manuscript_digdisc.md** -- Main manuscript (Markdown source)
- **supplementary_digdisc.md** -- Supplementary information (Markdown source)
- **manuscript_digdisc.docx** -- Main manuscript (Word format)
- **supplementary_digdisc.docx** -- Supplementary information (Word format)
- **make_figures.py** -- Generates all figures (PNG + SVG)
- **make_docx.py** -- Generates DOCX files from manuscript content
- **figures/** -- Publication-quality figures

## Regenerating

```bash
conda activate vs_autoresearch
python make_figures.py     # Regenerate figures
python make_docx.py        # Regenerate DOCX files
```

Requires `matplotlib`, `numpy`, and `python-docx`.
