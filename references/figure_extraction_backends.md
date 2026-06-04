# Figure Extraction Backends

The skill should not rely on naive screenshots as the primary figure extraction method. Use the following order.

## Default Local Backend

Use Poppler tools already available on many TeX/academic machines:

1. `pdftoppm` renders pages at high DPI.
2. `pdftotext -bbox-layout` locates caption text and page coordinates.
3. `scripts/crop_pdf_figures_by_caption.py` crops the visual region adjacent to the caption and constrained to the same column.
4. `scripts/crop_pdf_regions.py` uses seed-aware edge cleanup for manual crops, removing neighboring body text, page headers, and caption fragments when they are not connected to the intended figure seed.
5. `scripts/figure_quality_validator.py` checks resolution, contrast, whitespace, likely incomplete crops, and likely neighboring body text.

This backend is lightweight and works without network or Java.

## Optional External Backends

### PDFFigures2

Repository: https://github.com/allenai/pdffigures2

Best fit for this skill. It is built for scholarly PDFs and extracts figures, tables, captions, caption boxes, and figure boxes. If installed, use it before manual cropping.

Suggested use:

```bash
sbt "runMain org.allenai.pdffigures2.FigureExtractorBatchCli /path/to/pdf_dir -s stat_file.json -m /figure/image/output/prefix -d /figure/data/output/prefix"
```

### GROBID

Repository: https://github.com/grobidOrg/grobid

Useful when the workflow needs structured TEI/XML, document segmentation, figure/table metadata, and coordinates. It is heavier than PDFFigures2 but more general for scholarly document understanding.

### PyMuPDF

Docs: https://pymupdf.readthedocs.io/en/latest/recipes-images.html

Useful for precise page rendering and clip rendering when Python dependencies are available. It supports high-DPI page pixmaps and clipped rendering, which is a cleaner alternative to rendering a full page and then cropping.

### LayoutParser

Project: https://layout-parser.github.io/

Useful for future ML-based layout detection. It offers pretrained document layout models and layout data structures, but it introduces heavier dependencies and model management.

## Policy

- Prefer caption-aware crops over component expansion.
- Never batch-apply connected-component expansion to all figures in a two-column paper.
- If a crop includes body text, page headers, or neighboring figures, mark it as failed and re-crop.
- Keep final crops as separate image objects in PPTX, not as full-page screenshots.
