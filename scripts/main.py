import re
import shutil
import tempfile
import subprocess
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


def ogm_chapters(file):
    with open(file, "r") as f:
        lines = f.readlines()

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
    xml_tree = ET.parse(file)
    xml_root = xml_tree.getroot()

    chapter_times = [elem.text for elem in xml_root.findall(".//ChapterAtom//ChapterTimeStart")]
    chapter_names = [elem.text for elem in xml_root.findall(".//ChapterAtom//ChapterString")]

    return chapter_times, chapter_names


def mkv_chapters(file):
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp_chapter_file = temp.name

    subprocess.run(["mkvextract", file, "chapters", temp_chapter_file])

    mkv_chapters_list = xml_chapters(temp_chapter_file)

    Path(temp_chapter_file).unlink()

    return mkv_chapters_list


def mediainfo_chapters():
    input_lines = []

    print('Enter/paste each line from the mediainfo result under "Menu"; enter empty line for completion:')

    while True:
        line = input().strip()
        if line:
            input_lines.append(line)
        else:
            break

    chapter_times = []
    chapter_names = []

    timecodePattern = re.compile(r"(\d\d:){2}\d\d\.\d{3}")
    splitPattern = re.compile(r"\s+: (\w{2,3})?:")

    for index, line in enumerate(input_lines, start=1):
        chapter_times.append(re.split(splitPattern, line, 1)[0])
        chapterName = re.split(splitPattern, line, 1)[-1]
        chapterIsTimecode = re.match(timecodePattern, chapterName)

        if chapterIsTimecode:
            chapter_names.append("Chapter " + f"{index:02d}")
        else:
            chapter_names.append(chapterName)

    return chapter_times, chapter_names


def mkv_writer(file, times_list, names_list):
    if len(times_list) != len(names_list):
        raise RuntimeError("Provided chapter inputs do not have the same number of chapters")

    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp_chapter_file = temp.name

    root = ET.Element("Chapters")
    tree = ET.ElementTree(root)
    elemEditionEntry = ET.SubElement(root, "EditionEntry")

    for index, timecode in enumerate(times_list):
        elemChapterAtom = ET.SubElement(elemEditionEntry, "ChapterAtom")
        ET.SubElement(elemChapterAtom, "ChapterTimeStart").text = timecode
        elemChapterDisplay = ET.SubElement(elemChapterAtom, "ChapterDisplay")
        ET.SubElement(elemChapterDisplay, "ChapterString").text = names_list[index]

    with open(temp_chapter_file, "wb") as f:
        f.write(
            '<?xml version="1.0"?>\n<!-- <!DOCTYPE Chapters SYSTEM "matroskachapters.dtd"> -->\n'.encode("utf-8-sig")
        )
        tree.write(f, xml_declaration=False, encoding="utf-8-sig")

    subprocess.run(["mkvpropedit", file, "--chapters", temp_chapter_file])

    Path(temp_chapter_file).unlink()


def path_validate(path):
    input_path = Path(path)

    if not input_path.is_file():
        raise RuntimeError(f"{input_path} is not a file")

    return str(input_path)


def main(args):
    input_mkv_path = path_validate(args.input)

    chapter_times_only = chapter_names_only = []

    if args.timecodes_mkv:
        chapter_times_only = mkv_chapters(input_mkv_path)[0]
    elif args.timecodes_mediainfo:
        print("For mediainfo containing correct timecodes:")
        chapter_times_only = mediainfo_chapters()[0]
    elif args.timecodes_xml_file:
        input_xml_path = path_validate(args.timecodes_xml_file)
        chapter_times_only = xml_chapters(input_xml_path)[0]
    elif args.timecodes_txt_file:
        input_txt_path = path_validate(args.timecodes_txt_file)
        chapter_times_only = ogm_chapters(input_txt_path)[0]

    if args.names_mkv:
        chapter_names_only = mkv_chapters(input_mkv_path)[1]
    elif args.names_mediainfo:
        print("For mediainfo containing correct names:")
        chapter_names_only = mediainfo_chapters()[1]
    elif args.names_xml_file:
        input_xml_path = path_validate(args.names_xml_file)
        chapter_names_only = xml_chapters(input_xml_path)[1]
    elif args.names_txt_file:
        input_txt_path = path_validate(args.names_txt_file)
        chapter_names_only = ogm_chapters(input_txt_path)[1]

    mkv_writer(input_mkv_path, chapter_times_only, chapter_names_only)


def cli():
    parser = argparse.ArgumentParser(description="Add/modify chapters in an MKV file")
    parser.add_argument("input", type=str, help="MKV file to manipulate")

    timecode_group = parser.add_mutually_exclusive_group(required=True)
    timecode_group.add_argument("--timecodes-mkv", "-tk", action="store_true", help="Use timecodes from input MKV file")
    timecode_group.add_argument(
        "--timecodes-mediainfo", "-tm", action="store_true", help="Use timecodes from Mediainfo"
    )
    timecode_group.add_argument("--timecodes-xml-file", "-tx", type=str, help="Use timecodes from input XML file")
    timecode_group.add_argument(
        "--timecodes-txt-file", "-tt", type=str, help="Use timecodes from input TXT file (OGM format only)"
    )

    chaptername_group = parser.add_mutually_exclusive_group(required=True)
    chaptername_group.add_argument("--names-mkv", "-nk", action="store_true", help="Use names from input MKV file")
    chaptername_group.add_argument("--names-mediainfo", "-nm", action="store_true", help="Use names from Mediainfo")
    chaptername_group.add_argument("--names-xml-file", "-nx", type=str, help="Use names from input XML file")
    chaptername_group.add_argument(
        "--names-txt-file", "-nt", type=str, help="Use names from input TXT file (OGM format only)"
    )

    args_namespace = parser.parse_args()

    if args_namespace.timecodes_mkv and args_namespace.names_mkv:
        parser.error("Cannot get both timecodes and names from MKV")

    main(args_namespace)


if __name__ == "__main__":
    if not shutil.which("mkvpropedit") or not shutil.which("mkvextract"):
        raise RuntimeError("Error: mkvpropedit and/or mkvextract not found in PATH")

    cli()
