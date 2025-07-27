import os
import re
from lxml import etree

# === Adjust this path to your folder with XML files ===
input_folder = "/Users/sguhr/Downloads/Sound_in_Drama-main/20250727_manipulated_xml-files"
output_folder = os.path.join(input_folder, "cleaned")
os.makedirs(output_folder, exist_ok=True)

# Tags in which to remove inner line breaks
INLINE_TAGS = {"p", "stage", "l"}

def clean_xml_file(input_path, output_path):
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(input_path, parser)
    root = tree.getroot()

    # 1. Remove <pb n="..."/> elements
    for pb in root.xpath('.//pb'):
        pb.getparent().remove(pb)

    # 2. Remove <emph> but keep content
    for emph in root.xpath('.//emph'):
        parent = emph.getparent()
        index = parent.index(emph)
        # Insert children (or span if only text)
        for child in emph:
            parent.insert(index, child)
            index += 1
        if emph.text:
            if emph.getchildren():
                emph[0].text = emph.text + (emph[0].text or "")
            else:
                span = etree.Element("span")
                span.text = emph.text
                parent.insert(index, span)
                index += 1
        parent.remove(emph)

    # 3. Fix <stage>sagt ( → <stage>(sagt
    for stage in root.xpath('.//stage'):
        if stage.text:
            stage.text = re.sub(r'\bsagt\s*\(', r'(sagt ', stage.text, flags=re.IGNORECASE)

    # 4. Remove line breaks inside inline content tags
    for tag in INLINE_TAGS:
        for elem in root.xpath(f'.//{tag}'):
            if elem.text:
                elem.text = re.sub(r'\s*\n\s*', ' ', elem.text)
            for sub in elem:
                if sub.tail:
                    sub.tail = re.sub(r'\s*\n\s*', ' ', sub.tail)

    # Write output
    tree.write(output_path, encoding="utf-8", pretty_print=True, xml_declaration=True)

# === Process all .xml files in the folder ===
for filename in os.listdir(input_folder):
    if filename.endswith(".xml"):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        clean_xml_file(input_path, output_path)
        print(f"✅ Cleaned: {filename}")

print(f"\n🎉 All files processed. Cleaned versions saved to: {output_folder}")
