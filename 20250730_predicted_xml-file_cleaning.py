import os
import re
from lxml import etree
import spacy

# === Load spaCy German model ===
nlp = spacy.load("de_core_news_sm")

# === Paths ===
input_folder = "/Users/sguhr/Desktop/20250729_prediction_output"
output_folder = os.path.join(input_folder, "postprocessed")
os.makedirs(output_folder, exist_ok=True)

# === Stoplist (case-insensitive matching) ===
one_word_stoplist = {
    "und", "Und", "in", "weil", "da", "wie", "so", "auch", "schon", "die", "Der", "Die", "der", "Das", "das", "auf die Achsel", "wann", "er", "Er", "Sie", "sie", "In", "neben die", "seine Rumpelkammer", "Lampen", "denke"
}
sound_tags = {"character_sound", "ambient_sound"}

def append_tail_to_prev(prev_elem, tail_text):
    """Append tail_text to prev_elem's tail or text."""
    if tail_text:
        if prev_elem.tail:
            prev_elem.tail += tail_text
        elif prev_elem.text:
            prev_elem.text += tail_text
        else:
            prev_elem.tail = tail_text

def merge_adjacent_sound_tags(parent):
    """Merge consecutive <sound> tags of same type if separated by comma/space."""
    i = 0
    while i < len(parent) - 1:
        current = parent[i]
        next_elem = parent[i + 1]
        if (
            isinstance(current, etree._Element) and
            isinstance(next_elem, etree._Element) and
            current.tag == next_elem.tag and
            current.tag in sound_tags
        ):
            # Only merge if tail of current is empty or only whitespace/comma
            if (current.tail is None or re.fullmatch(r"[\s,]*", current.tail)):
                current.text = (current.text or '') + ' ' + (next_elem.text or '')
                # Append the tail of next_elem to current's tail (preserving text)
                append_tail_to_prev(current, next_elem.tail)
                parent.remove(next_elem)
                continue  # stay at the same index to check for more merges
        i += 1

def clean_one_word_sound_tags(parent):
    for elem in list(parent):
        if elem.tag in sound_tags:
            text = (elem.text or '').strip()
            doc = nlp(text)
            if (
                len(doc) == 1 and
                (text.lower() in {w.lower() for w in one_word_stoplist} or
                 doc[0].pos_ in {"PRON", "DET", "PART", "SCONJ", "INTJ"} or
                 len(text) < 4)
            ):
                prev = elem.getprevious()
                if prev is not None:
                    append_tail_to_prev(prev, elem.tail)
                else:
                    if parent.text:
                        parent.text += (elem.tail or '')
                    else:
                        parent.tail = (parent.tail or '') + (elem.tail or '')
                parent.remove(elem)


def prefer_longer_annotation(parent):
    """Remove shorter of two adjacent different-type sound annotations."""
    children = list(parent)
    i = 0
    while i < len(children) - 1:
        e1 = children[i]
        e2 = children[i + 1]
        if (
            isinstance(e1, etree._Element) and isinstance(e2, etree._Element) and
            e1.tag in sound_tags and e2.tag in sound_tags and e1.tag != e2.tag
        ):
            len1 = len((e1.text or "").strip())
            len2 = len((e2.text or "").strip())
            to_remove = e1 if len1 < len2 else e2
            if to_remove.getparent() is parent:
                prev = to_remove.getprevious()
                if prev is not None:
                    append_tail_to_prev(prev, to_remove.tail)
                else:
                    if parent.text:
                        parent.text += (to_remove.tail or '')
                    else:
                        if parent.tail:
                            parent.tail += (to_remove.tail or '')
                        else:
                            parent.tail = to_remove.tail
                parent.remove(to_remove)
                children = list(parent)
                continue
        i += 1

def remove_nested_sound_annotations_in_speaker(speaker):
    """Remove sound tags from within <speaker>."""
    for child in list(speaker):
        if child.tag in sound_tags:
            prev = child.getprevious()
            if prev is not None:
                append_tail_to_prev(prev, child.tail)
            else:
                if speaker.text:
                    speaker.text += (child.tail or '')
                else:
                    if speaker.tail:
                        speaker.tail += (child.tail or '')
                    else:
                        speaker.tail = child.tail
            speaker.remove(child)
    # Avoid removing text inside speaker.text arbitrarily:
    # Remove only tags if they exist as elements, not raw strings
    # So comment out regex substitution on speaker.text:
    # if speaker.text:
    #     speaker.text = re.sub(r'<.*?>', '', speaker.text).strip()

def has_finite_verb_between(text):
    """Detect finite verbs between two phrases using spaCy."""
    doc = nlp(text)
    return any(t.pos_ == "VERB" and "Fin" in t.morph.get("VerbForm") for t in doc)

def deduplicate_adjacent_sound_tags_only_if_similar(parent):
    """Remove short duplicate tags only if no verb separates them."""
    children = list(parent)
    i = 0
    while i < len(children) - 1:
        e1 = children[i]
        e2 = children[i + 1]
        if (
            isinstance(e1, etree._Element) and isinstance(e2, etree._Element) and
            e1.tag in sound_tags and e2.tag in sound_tags and e1.tag == e2.tag
        ):
            middle_text = (e1.tail or '') + (e2.text or '')
            if not has_finite_verb_between(middle_text):
                len1 = len((e1.text or '').strip())
                len2 = len((e2.text or '').strip())
                to_remove = e1 if len1 < len2 else e2
                if to_remove.getparent() is parent:
                    prev = to_remove.getprevious()
                    if prev is not None:
                        append_tail_to_prev(prev, to_remove.tail)
                    else:
                        if parent.text:
                            parent.text += (to_remove.tail or '')
                        else:
                            if parent.tail:
                                parent.tail += (to_remove.tail or '')
                            else:
                                parent.tail = to_remove.tail
                    parent.remove(to_remove)
                    children = list(parent)
                    continue
        i += 1

def merge_disjoint_sound_phrases(parent, tagname="ambient_sound"):
    """Merge sound phrases across short interleaving tails."""
    children = list(parent)
    i = 0
    while i < len(children) - 2:
        current = children[i]
        next_ = children[i + 2]
        middle = children[i + 1]
        if (
            isinstance(current, etree._Element) and current.tag == tagname and
            isinstance(next_, etree._Element) and next_.tag == tagname and
            not isinstance(middle, etree._Element)
        ):
            tail = (current.tail or '') + (middle or '') + (next_.text or '')
            if not re.search(r'[.!?]', tail):
                current.text = (current.text or '') + ' ' + tail.strip()
                current.tail = next_.tail or ''
                # Remove middle text node and next_ element
                del children[i + 1:i + 3]
                parent[:] = children
                continue
        i += 1

def annotate_ambient_phrases(parent):
    """Wrap full ambient-sound phrases like 'Die Geräusche ...' in <ambient_sound>."""
    if parent.tag not in {"p", "stage"} or not parent.text:
        return
    pattern = r'(Die Geräusche[^<.]{10,300}?(?:vernehmlich|hörbar|zu hören|deutlich gewesen|laut gewesen))'
    def replacer(match):
        phrase = match.group(1)
        return f'<ambient_sound>{phrase}</ambient_sound>'
    if "<ambient_sound>" not in parent.text:
        parent.text = re.sub(pattern, replacer, parent.text, flags=re.IGNORECASE)

def process_file(input_path, output_path):
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(input_path, parser)
    root = tree.getroot()
    for elem in root.iter():
        merge_adjacent_sound_tags(elem)
        clean_one_word_sound_tags(elem)
        prefer_longer_annotation(elem)
        deduplicate_adjacent_sound_tags_only_if_similar(elem)
        merge_disjoint_sound_phrases(elem, tagname="ambient_sound")
        annotate_ambient_phrases(elem)
    for speaker in root.xpath(".//speaker"):
        remove_nested_sound_annotations_in_speaker(speaker)
    tree.write(output_path, encoding="utf-8", pretty_print=True, xml_declaration=True)

# === Process all files ===
for filename in sorted(os.listdir(input_folder)):
    if filename.endswith(".xml"):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        process_file(input_path, output_path)
        print(f"✅ Processed: {filename}")

print(f"\n🎉 All files postprocessed and saved to: {output_folder}")
