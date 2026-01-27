#!/usr/bin/env python3
"""
PDF TABLE EXTRACTOR
(BORDERED + BORDERLESS)

Rules enforced:
1. Exactly ONE table per page
2. Bordered tables:
   - extracted by border lines only
   - multi-line cell content joined with "; "
   - stitched ONLY if no header row
3. Borderless tables:
   - extracted using proven alignment-based logic
   - NEVER stitched
4. Column names inferred ONLY if a header row is detected
"""

import re
from pathlib import Path
from collections import defaultdict
import pdfplumber
import pandas as pd


# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------
def make_unique(cols):
    seen = {}
    out = []
    for c in cols:
        base = str(c)
        if base in seen:
            seen[base] += 1
            out.append(f"{base}_{seen[base]}")
        else:
            seen[base] = 1
            out.append(base)
    return out


def normalize_cell_text(text):
    lines = [t.strip() for t in text.splitlines() if t.strip()]
    return "; ".join(lines)


def looks_like_header_row(row):
    joined = " ".join(c for c in row if c).strip()
    if not joined:
        return False
    letters = sum(ch.isalpha() for ch in joined)
    digits = sum(ch.isdigit() for ch in joined)
    return letters > 0 and digits / max(letters, 1) < 0.3


def merge_overlapping_columns(col_bounds, overlap_thresh=0.6):
    """
    Merge column bounds that largely overlap (duplicate vertical grid lines).
    """
    merged = []

    for x0, x1 in sorted(col_bounds):
        if not merged:
            merged.append([x0, x1])
            continue

        px0, px1 = merged[-1]
        overlap = max(0, min(x1, px1) - max(x0, px0))
        width = min(x1 - x0, px1 - px0)

        if width > 0 and overlap / width >= overlap_thresh:
            # merge
            merged[-1][0] = min(px0, x0)
            merged[-1][1] = max(px1, x1)
        else:
            merged.append([x0, x1])

    return [tuple(b) for b in merged]


def looks_like_data_row(cells):
    if not cells:
        return False
    first = (cells[0] or '').strip()
    if re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})$', first):
        return True
    if re.match(r'^\d+(?:\.\d+)?%?$', first):
        return True
    joined = ' '.join([c for c in cells if c])
    digits = sum(ch.isdigit() for ch in joined)
    return digits >= 2


def header_likeness(cells):
    joined = ' '.join([c for c in cells if c])
    if not joined:
        return 0.0
    letters = sum(ch.isalpha() for ch in joined)
    digits = sum(ch.isdigit() for ch in joined)
    if letters == 0:
        return 0.0
    return letters / (letters + digits + 1e-9)


def drop_sparse_columns_by_index(df, empty_thresh=0.9, data_only=True):
    if df is None or df.empty:
        return df, list(range(df.shape[1])) if df is not None else []
    base_df = df.iloc[1:, :] if data_only and df.shape[0] > 1 else df
    keep_idx = []
    for i in range(df.shape[1]):
        s = base_df.iloc[:, i].fillna('').astype(str).str.strip()
        if (s.eq('').mean()) < empty_thresh:
            keep_idx.append(i)
    return (df.iloc[:, keep_idx], keep_idx) if keep_idx else (df, list(range(df.shape[1])))


# ------------------------------------------------------------------
# Bordered tables (unchanged logic from last version)
# ------------------------------------------------------------------
def extract_bordered_table(page, table):

    raw_col_bounds = [(c.bbox[0], c.bbox[2]) for c in table.columns]
    col_bounds = merge_overlapping_columns(raw_col_bounds)
    # col_bounds = [(c.bbox[0], c.bbox[2]) for c in table.columns]
    ncols = len(col_bounds)

    row_tops = sorted({round(c[1], 1) for c in table.cells})
    grid = [[""] * ncols for _ in row_tops]

    for bbox in table.cells:
        x0, y0, x1, y1 = bbox
        cropped = page.crop(bbox)
        words = cropped.extract_words(x_tolerance=2, y_tolerance=3)

        lines = defaultdict(list)
        for w in words:
            key = round(w["top"] / 3) * 3
            lines[key].append(w)

        content = []
        for k in sorted(lines):
            row = sorted(lines[k], key=lambda w: w["x0"])
            content.append(" ".join(w["text"] for w in row))

        text = normalize_cell_text("\n".join(content))
        row_idx = min(range(len(row_tops)), key=lambda i: abs(row_tops[i] - y0))

        for col_idx, (cx0, cx1) in enumerate(col_bounds):
            if x0 < cx1 and x1 > cx0:
                if not grid[row_idx][col_idx] and text:
                    grid[row_idx][col_idx] = text

    grid = [r for r in grid if any(v.strip() for v in r)]
    return grid


# ------------------------------------------------------------------
# BORDERLESS TABLE LOGIC 
# ------------------------------------------------------------------

def text_content_bbox(page, pad=5):
    words = page.extract_words(x_tolerance=2, y_tolerance=2)
    if not words:
        return None
    x0 = min(w['x0'] for w in words) - pad
    x1 = max(w['x1'] for w in words) + pad
    top = min(w['top'] for w in words) - pad
    bottom = max(w['bottom'] for w in words) + pad
    return (x0, top, x1, bottom)


def group_rows(words, y_tol=3):
    rows = []
    for w in sorted(words, key=lambda d: d['top']):
        for r in rows:
            if abs(w['top'] - r['top']) <= y_tol:
                r['words'].append(w)
                break
        else:
            rows.append({'top': w['top'], 'words': [w]})
    for r in rows:
        r['words'] = sorted(r['words'], key=lambda d: d['x0'])
    return rows


def split_row_into_cells(row_words, gap=25):
    if not row_words:
        return []
    cells = []
    cur = [row_words[0]]
    for prev, w in zip(row_words, row_words[1:]):
        if w['x0'] - prev['x1'] > gap:
            cells.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        cells.append(cur)
    return cells


def cluster_centers(xs, min_gap=45):
    xs = sorted(xs)
    if not xs:
        return []
    clusters = [[xs[0]]]
    for x in xs[1:]:
        if x - clusters[-1][-1] > min_gap:
            clusters.append([x])
        else:
            clusters[-1].append(x)
    return [sum(c) / len(c) for c in clusters]


def _is_noise_header_footer(line: str) -> bool:
    """Filter recurring page header/footer noise."""
    if not line:
        return True
    s = line.strip()
    return bool(re.search(r"(velonetic\s+page\s+\d+|copyright|all\s+rights\s+reserved)", s, re.I))


def extract_title_lines_above(page, x0, x1, bottom_y,
                             max_up=180, y_tol=3,
                             line_gap=45, first_line_gap=70, max_lines=4):
    """    Extract title lines immediately above a borderless table.

    We crop a band above the table/header and take the closest title block
    lines above it, filtering out page headers/footers.

    Notes
    -----
    * Borderless tables often have a title block separated from the column
      header by a larger vertical gap. Defaults are therefore more tolerant.
    * The crop band may include the column header row itself (e.g.
      'Signed Line Syndicate ...'). If we see that header line, we treat it
      as the boundary and continue scanning upward rather than stopping.
    """
    if bottom_y is None:
        return []

    # Nudge the crop boundary slightly upward to reduce the chance of
    # including the header line, but keep it robust to rounding.
    bottom_y_adj = max(0, bottom_y - 0.5)
    top_y = max(0, bottom_y_adj - max_up)

    region = page.crop((x0, top_y, x1, bottom_y_adj))
    words = region.extract_words(x_tolerance=2, y_tolerance=2)
    if not words:
        return []

    rows = group_rows(words, y_tol=y_tol)

    line_items = []
    for r in rows:
        txt = " ".join(w["text"] for w in r["words"]).strip()
        if txt and not _is_noise_header_footer(txt):
            line_items.append((r["top"], txt))

    if not line_items:
        return []

    title = []
    last_top = bottom_y_adj

    for t, txt in sorted(line_items, key=lambda x: x[0], reverse=True):
        if (bottom_y_adj - t) > max_up:
            continue

        # If we hit the table column header row, skip it and keep moving up.
        if re.search(r"\bSigned\s+Line\b", txt) and re.search(r"\bSyndicate\b", txt):
            last_top = t
            if title:
                break
            continue

        allowed_gap = first_line_gap if not title else line_gap
        if (last_top - t) > allowed_gap:
            break

        # Titles typically contain letters; stop if not
        if sum(ch.isalpha() for ch in txt) == 0:
            break

        title.append(txt)
        last_top = t
        if len(title) >= max_lines:
            break

    return list(reversed(title))
def prepend_title_rows(df: pd.DataFrame, title_lines, header_row=None):
    """Prepend title lines (and optionally the table header row) above the extracted table.

    For borderless tables we want the output ordered as:
      title lines (each as a separate row)
      header row (e.g. 'Signed Line', 'Syndicate', ...)
      data rows

    Title lines are placed in the first column and the remaining columns are blank.
    """
    if df is None or df.empty:
        return df

    cols = list(df.columns)
    out_frames = []

    if title_lines:
        pad = [""] * max(len(cols) - 1, 0)
        title_rows = [[t] + pad for t in title_lines]
        out_frames.append(pd.DataFrame(title_rows, columns=cols))

    if header_row is not None:
        hr = list(header_row) + [""] * max(0, len(cols) - len(header_row))
        hr = hr[:len(cols)]
        out_frames.append(pd.DataFrame([hr], columns=cols))

    out_frames.append(df)
    return pd.concat(out_frames, ignore_index=True)
def extract_borderless_from_bbox(page, bbox):
    x0, top, x1, bottom = bbox
    cropped = page.crop((x0, top, x1, bottom))
    words = cropped.extract_words(x_tolerance=2, y_tolerance=2)
    H = page.height
    words = [w for w in words if w['top'] > 50 and w['bottom'] < H - 50]
    if len(words) < 8:
        return None

    rows = group_rows(words, y_tol=3)

    row_cells = []
    for r in rows:
        cells = split_row_into_cells(r['words'], gap=25)
        cell_text = [' '.join(w['text'] for w in c).strip() for c in cells]
        row_cells.append({'top': r['top'], 'cells': cell_text, 'cell_words': cells})

    body = [rc for rc in row_cells if len(rc['cells']) >= 2 and looks_like_data_row(rc['cells'])]
    if len(body) < 2:
        return None

    xs = []
    for rc in body:
        for cell in rc['cell_words']:
            if cell:
                xs.append(cell[0]['x0'])
    centers = cluster_centers(xs, min_gap=45)
    if len(centers) < 2:
        return None

    def col_idx(w):
        return int(min(range(len(centers)), key=lambda i: abs(w['x0'] - centers[i])))

    matrix = []
    tops = []
    for r in rows:
        buckets = defaultdict(list)
        for w in r['words']:
            buckets[col_idx(w)].append(w)
        row = [''] * len(centers)
        for i in range(len(centers)):
            ws = sorted(buckets.get(i, []), key=lambda d: d['x0'])
            if ws:
                row[i] = ' '.join(w['text'] for w in ws).strip()
        if any(c.strip() for c in row):
            matrix.append(row)
            tops.append(r['top'])

    body_tops = [rc['top'] for rc in body]
    first_data_top = min(body_tops) if body_tops else None

    ymin = min(body_tops) - 25
    ymax = max(body_tops) + 5

    sub_pairs = [(r, t) for r, t in zip(matrix, tops) if ymin <= t <= ymax]
    sub = [r for r, t in sub_pairs]
    sub_tops = [t for r, t in sub_pairs]

    if len(sub) < 2:
        sub = matrix

    data_ix = None
    for i, r in enumerate(sub):
        if looks_like_data_row(r):
            data_ix = i
            break
    header = None
    header_row = None
    if data_ix is not None and data_ix > 0:
        cand = sub[data_ix - 1]
        if (not looks_like_data_row(cand)) and (header_likeness(cand) > 0.65):
            header = cand
            header_row = cand
            sub = sub[data_ix:]

    header_top = None
    if data_ix is not None and data_ix > 0 and header is not None:
        header_top = sub_tops[data_ix - 1]

    # Extract table title lines from the band immediately above the table/header
    title_bottom = header_top if header_top is not None else first_data_top
    title_lines = extract_title_lines_above(page, x0, x1, title_bottom)

    # Keep simple column names for borderless output. When title lines exist we will
    # write CSV with header=False, and include the detected header row as a row.
    cols = make_unique([f'Column{i+1}' for i in range(len(sub[0]))])
    df = pd.DataFrame(sub, columns=cols)
    df = df.apply(lambda col: col.astype(str).str.strip())

    df, _ = drop_sparse_columns_by_index(df, empty_thresh=0.9, data_only=False)
    df = df[df.apply(lambda r: sum(v != '' and v.lower() != 'nan' for v in r) >= 2, axis=1)].reset_index(drop=True)
    if df.shape[0] < 2 or df.shape[1] < 2:
        return None

    meta = {
        'bbox': (float(x0), float(top), float(x1), float(bottom)),
        'n_rows': int(df.shape[0]),
        'n_cols': int(df.shape[1]),
        'has_header': header_row is not None,
 'header_row': header_row,
        'title_lines': title_lines,
    }
    return df, meta


# ------------------------------------------------------------------
# Main extraction
# -------
def extract_pdf(pdf_path: Path, out_dir: Path):
    out_dir.mkdir(exist_ok=True)
    table_idx = 0
    current_df = None
    current_columns = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):

            tables = page.find_tables(
                table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 3,
                    "join_tolerance": 3,
                }
            )

            # Prefer bordered if it exists
            if tables:
                grid = extract_bordered_table(page, tables[0])
                has_header = looks_like_header_row(grid[0])

                if has_header:
                    if current_df is not None:
                        current_df.to_csv(out_dir / f"{pdf_path.stem}_table_{table_idx:03d}.csv", index=False)
                    table_idx += 1
                    current_columns = grid[0]
                    current_df = pd.DataFrame(grid[1:], columns=current_columns)
                else:
                    df_append = pd.DataFrame(grid, columns=current_columns or [f"Column{i+1}" for i in range(len(grid[0]))])
                    current_df = pd.concat([current_df, df_append], ignore_index=True) if current_df is not None else df_append
            else:
                page_tables = page.find_tables(
                    table_settings={
                        'vertical_strategy': 'text',
                        'horizontal_strategy': 'text',
                        'snap_tolerance': 3,
                        'join_tolerance': 3,
                        'intersection_tolerance': 3,
                        'edge_min_length': 3,
                        'min_words_vertical': 1,
                        'min_words_horizontal': 1,
                    }
                )

                res = None
                if page_tables:
                    # normal case: bbox found
                    res = extract_borderless_from_bbox(page, page_tables[0].bbox)
                else:
                    tight_bbox = text_content_bbox(page)
                    if tight_bbox:
                        res = extract_borderless_from_bbox(page, tight_bbox)

                if res is not None:
                    df, meta = res
                    df = prepend_title_rows(df, meta.get('title_lines') if isinstance(meta, dict) else None, meta.get('header_row') if isinstance(meta, dict) else None)
                    table_idx += 1
                    df.to_csv(
                        out_dir / f"{pdf_path.stem}_table_{table_idx:03d}.csv",
                        index=False,
                    )

    if current_df is not None:
        current_df.to_csv(out_dir / f"{pdf_path.stem}_table_{table_idx:03d}.csv", index=False)


# ------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, default=Path("tables_out"))
    args = parser.parse_args()

    extract_pdf(args.pdf, args.out)
    print("Extraction complete.")
