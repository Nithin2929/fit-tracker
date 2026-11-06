"""Export the Markdown final project report to a simple Word document."""

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "FINAL_PROJECT_REPORT.md"
OUTPUT = ROOT / "docs" / "FINAL_PROJECT_REPORT.docx"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ET.register_namespace("w", WORD_NS)
ET.register_namespace("r", REL_NS)


def _tag(name):
    return f"{{{WORD_NS}}}{name}"


def _paragraph(document, text, style=None):
    paragraph = ET.SubElement(document, _tag("p"))
    if style:
        properties = ET.SubElement(paragraph, _tag("pPr"))
        ET.SubElement(properties, _tag("pStyle"), {_tag("val"): style})
    run = ET.SubElement(paragraph, _tag("r"))
    value = ET.SubElement(run, _tag("t"))
    if text[:1].isspace() or text[-1:].isspace():
        value.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    value.text = text


def _document_xml():
    document = ET.Element(_tag("document"))
    body = ET.SubElement(document, _tag("body"))

    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith("# "):
            _paragraph(body, text[2:], "Title")
        elif text.startswith("## "):
            _paragraph(body, text[3:], "Heading1")
        elif text.startswith("### "):
            _paragraph(body, text[4:], "Heading2")
        elif text.startswith("- "):
            _paragraph(body, text[2:], "ListParagraph")
        elif text.startswith("```"):
            continue
        else:
            _paragraph(body, text)

    section = ET.SubElement(body, _tag("sectPr"))
    page_size = ET.SubElement(section, _tag("pgSz"))
    page_size.set(_tag("w"), "12240")
    page_size.set(_tag("h"), "15840")
    margins = ET.SubElement(section, _tag("pgMar"))
    for side in ("top", "right", "bottom", "left"):
        margins.set(_tag(side), "1440")
    return ET.tostring(document, encoding="utf-8", xml_declaration=True)


def main():
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""
    relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    document_relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""
    styles = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{WORD_NS}">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/><w:rPr><w:sz w:val="22"/></w:rPr>
    <w:pPr><w:spacing w:after="120"/></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="36"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
    <w:rPr><w:b/><w:sz w:val="28"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/><w:basedOn w:val="Normal"/>
    <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ListParagraph">
    <w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:ind w:left="360"/></w:pPr>
  </w:style>
</w:styles>"""

    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", content_types)
        package.writestr("_rels/.rels", relationships)
        package.writestr("word/document.xml", _document_xml())
        package.writestr("word/_rels/document.xml.rels", document_relationships)
        package.writestr("word/styles.xml", styles)

    print(f"Created {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
