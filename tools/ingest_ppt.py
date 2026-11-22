#!/usr/bin/env python3
"""
课件摄取工具：把 PPTX / PDF 拆成可用的课程素材。

用法：
    python tools/ingest_ppt.py 课件.pptx 03-sta

产物（web/lessons/<id>/src/）：
    slides/sNNN.png   每页渲染图（PPTX 内嵌图片；无图页会标记）
    text.txt          逐页文字（有文字层时）
    outline.json      页号 → 标题/正文/是否有图
    REPORT.md         人来读的清单，用于编排章节与交互

说明：录屏型 PPT（每页只有一张截图）没有文字层，
需要视觉识别补文字；本脚本负责把素材切好，内容仍需人工/模型编排。
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def from_pptx(path, out):
    from pptx import Presentation
    from PIL import Image

    prs = Presentation(path)
    outline = []
    os.makedirs(os.path.join(out, "slides"), exist_ok=True)

    for i, slide in enumerate(prs.slides, 1):
        texts, img = [], None
        for sh in slide.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip():
                texts.append(sh.text_frame.text.strip())
            if sh.shape_type == 13 and img is None:  # PICTURE
                img = sh
        entry = {"page": i, "text": texts, "image": None}
        if img is not None:
            blob = img.image.blob
            ext = img.image.ext or "png"
            fn = "s%03d.%s" % (i, ext)
            fp = os.path.join(out, "slides", fn)
            with open(fp, "wb") as f:
                f.write(blob)
            try:
                im = Image.open(io.BytesIO(blob))
                entry["size"] = list(im.size)
                # 统一转 PNG，方便后续处理
                if ext.lower() not in ("png",):
                    im.convert("RGB").save(fp.rsplit(".", 1)[0] + ".png")
                    fn = fn.rsplit(".", 1)[0] + ".png"
            except Exception:
                pass
            entry["image"] = "slides/" + fn
        outline.append(entry)

    with open(os.path.join(out, "text.txt"), "w", encoding="utf-8") as f:
        for e in outline:
            f.write("=" * 60 + "\nPAGE %d\n" % e["page"])
            for t in e["text"]:
                f.write(t + "\n")
            if not e["text"]:
                f.write("(无文字层)\n")

    return {"slides": len(outline), "pages": outline}


def from_pdf(path, out):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.exit("需要 PyMuPDF：pip install pymupdf")
    doc = fitz.open(path)
    os.makedirs(os.path.join(out, "slides"), exist_ok=True)
    pages = []
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=140)
        fn = "s%03d.png" % i
        pix.save(os.path.join(out, "slides", fn))
        txt = page.get_text().strip()
        pages.append({"page": i, "text": [txt] if txt else [], "image": "slides/" + fn})
    with open(os.path.join(out, "text.txt"), "w", encoding="utf-8") as f:
        for e in pages:
            f.write("=" * 60 + "\nPAGE %d\n" % e["page"])
            f.write((e["text"][0] if e["text"] else "(无文字层)") + "\n")
    return {"slides": len(pages), "pages": pages}


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, lid = sys.argv[1], sys.argv[2]
    out = os.path.join(ROOT, "web", "lessons", lid, "src")
    os.makedirs(out, exist_ok=True)

    if src.lower().endswith((".pptx", ".ppt")):
        data = from_pptx(src, out)
    elif src.lower().endswith(".pdf"):
        data = from_pdf(src, out)
    else:
        sys.exit("只支持 .pptx / .pdf（其他素材请先转换）")

    json.dump(data, open(os.path.join(out, "outline.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    with_pic = sum(1 for p in data["pages"] if p["image"])
    with_txt = sum(1 for p in data["pages"] if p["text"])
    lines = ["# %s 素材概览" % lid, "",
             "- 总页数：%d" % data["slides"],
             "- 有图片：%d 页" % with_pic,
             "- 有文字层：%d 页" % with_txt, ""]
    if with_txt < data["slides"] * 0.3:
        lines.append("> 文字层很少，是截图型课件：需要逐页视觉识别后再编排内容。\n")
    for p in data["pages"]:
        head = (p["text"][0][:60] if p["text"] else "（无文字）").replace("\n", " ")
        lines.append("- p%03d %s" % (p["page"], head))
    open(os.path.join(out, "REPORT.md"), "w", encoding="utf-8").write("\n".join(lines))

    print("完成：%d 页，图片 %d 页，文字 %d 页" % (data["slides"], with_pic, with_txt))
    print("目录：", out)


if __name__ == "__main__":
    main()
