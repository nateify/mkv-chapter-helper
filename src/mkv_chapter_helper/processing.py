import re
import subprocess
import xml.etree.ElementTree as ET


def ogm_chapters(ogm_input, directmode=False):
    """Parses OGM chapter data from a file or a string."""
    if not directmode:
        with open(ogm_input) as f:
            lines = f.readlines()
    else:
        lines = ogm_input.splitlines()

    chapter_times = []
    chapter_names = []

    for line in lines:
        timecode_match = re.match(r"CHAPTER\d+=(.*)", line)
        name_match = re.match(r"CHAPTER\d+NAME=(.*)", line)

        if timecode_match:
            chapter_times.append(timecode_match.group(1).strip())
        elif name_match:
            chapter_names.append(name_match.group(1).strip())

    return chapter_times, chapter_names


def xml_chapters(file):
    """Parses chapters from a standard Matroska XML file."""
    xml_tree = ET.parse(file)
    xml_root = xml_tree.getroot()

    chapter_times = [elem.text for elem in xml_root.findall(".//ChapterAtom//ChapterTimeStart")]
    chapter_names = [elem.text for elem in xml_root.findall(".//ChapterAtom//ChapterString")]

    return chapter_times, chapter_names


def chaptergrabber_xml_chapters(file_path):
    """Parses chapters from a ChapterGrabber XML file."""
    xml_tree = ET.parse(file_path)
    xml_root = xml_tree.getroot()

    # Namespace may or may not be present
    ns = {"cg": "http://jvance.com/2008/ChapterGrabber"}
    chapters = xml_root.findall(".//cg:chapter", ns)
    if not chapters:
        chapters = xml_root.findall(".//chapter")

    chapter_times = []
    chapter_names = []

    for chapter_elem in chapters:
        time = chapter_elem.get("time")
        name = chapter_elem.get("name")
        if time and name is not None:
            # Normalize timestamp to HH:MM:SS.nnnnnnnnn for Matroska compatibility
            time_parts = time.split(".")
            base_time = time_parts[0]
            frac_seconds = time_parts[1] if len(time_parts) > 1 else ""
            normalized_time = f"{base_time}.{frac_seconds.ljust(9, '0')}"
            chapter_times.append(normalized_time)
            chapter_names.append(name)

    return chapter_times, chapter_names


def mkv_chapters(file, mkvextract_path):
    """Extracts chapters from an MKV file by calling mkvextract."""
    ogm_chapter_lines = subprocess.check_output(
        [mkvextract_path, file, "chapters", "-s"], universal_newlines=True, encoding="utf-8"
    )
    return ogm_chapters(ogm_chapter_lines, True)


def mediainfo_txt_chapters(file_path):
    """Parses chapters from the 'Menu' section of a MediaInfo TXT file."""
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    chapter_lines = []
    in_menu_section = False
    timecode_pattern = re.compile(r"^\d\d:\d\d:\d\d\.\d{3}")

    for line in lines:
        line_stripped = line.strip()
        if not in_menu_section:
            if line_stripped.lower() == "menu":
                in_menu_section = True
            continue

        if not line_stripped or not timecode_pattern.match(line_stripped):
            break  # Stop if we hit a blank line or a line not starting with a timecode

        chapter_lines.append(line_stripped)

    if not chapter_lines:
        raise ValueError(f"Could not find a 'Menu' section with valid chapters in {file_path}")

    chapter_times, chapter_names = _parse_mediainfo_lines(chapter_lines)
    return chapter_times, chapter_names


def mediainfo_chapters():
    """Parses chapters from multiline user input (pasted from MediaInfo)."""
    input_lines = []
    print('Enter/paste MediaInfo "Menu" content; enter an empty line to finish:')
    while True:
        try:
            line = input()
            if line:
                input_lines.append(line)
            else:
                break
        except EOFError:
            break

    return _parse_mediainfo_lines(input_lines)


def _parse_mediainfo_lines(lines):
    """Helper function to parse a list of MediaInfo chapter lines."""
    chapter_times = []
    chapter_names = []

    for index, line in enumerate(lines, start=1):
        parts = re.split(r"\s+:\s+", line.strip(), maxsplit=1)
        if len(parts) == 2:
            timecode, name_full = parts
            # Handle optional language prefix like 'en:'
            name_parts = name_full.split(":", 1)
            name = name_parts[1].strip() if len(name_parts) > 1 and len(name_parts[0]) == 2 else name_full.strip()

            # Use a default name if the name is just another timecode
            if re.match(r"(\d\d:){2}\d\d\.\d{3}", name):
                name = f"Chapter {index:02d}"

            chapter_times.append(timecode)
            chapter_names.append(name)

    return chapter_times, chapter_names
