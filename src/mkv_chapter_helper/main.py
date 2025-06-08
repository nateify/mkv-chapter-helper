import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from mkv_chapter_helper.processing import (
    chaptergrabber_xml_chapters,
    mediainfo_chapters,
    mediainfo_txt_chapters,
    mkv_chapters,
    ogm_chapters,
    xml_chapters,
)
from mkv_chapter_helper.utils import find_executable_path, path_validate


def mkv_writer(file, times_list, names_list, mkvpropedit_path):
    """Builds a Matroska XML chapter file and writes it to the MKV using mkvpropedit."""
    if len(times_list) != len(names_list):
        raise RuntimeError(
            f"Chapter timecodes ({len(times_list)}) and names ({len(names_list)}) must be equal in number."
        )

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".xml", encoding="utf-8-sig") as temp:
        temp_chapter_file = temp.name

        root = ET.Element("Chapters")
        tree = ET.ElementTree(root)
        elem_edition_entry = ET.SubElement(root, "EditionEntry")

        for index, timecode in enumerate(times_list):
            elem_chapter_atom = ET.SubElement(elem_edition_entry, "ChapterAtom")
            ET.SubElement(elem_chapter_atom, "ChapterTimeStart").text = timecode
            elem_chapter_display = ET.SubElement(elem_chapter_atom, "ChapterDisplay")
            ET.SubElement(elem_chapter_display, "ChapterString").text = names_list[index]

        temp.write('<?xml version="1.0"?>\n<!-- <!DOCTYPE Chapters SYSTEM "matroskachapters.dtd"> -->\n')
        tree.write(temp, xml_declaration=False, encoding="unicode")

    try:
        print(f"Running mkvpropedit on {Path(file).name}...")
        subprocess.run([str(mkvpropedit_path), file, "--chapters", temp_chapter_file], check=True, capture_output=True)
        print("Successfully wrote chapters to the MKV file.")
    except subprocess.CalledProcessError as e:
        print(f"Error running mkvpropedit:\n{e.stderr.decode('utf-8')}")
    finally:
        Path(temp_chapter_file).unlink()


def main(args):
    """Main application logic."""
    try:
        mkvpropedit_path = find_executable_path("mkvpropedit", args.mkvpropedit_path)
        mkvextract_path = find_executable_path("mkvextract", args.mkvextract_path)

        if not mkvpropedit_path:
            raise FileNotFoundError("mkvpropedit not found. Specify it with --mkvpropedit-path or add to PATH.")
        if not mkvextract_path:
            raise FileNotFoundError("mkvextract not found. Specify it with --mkvextract-path or add to PATH.")

        input_mkv_path = path_validate(args.input)

        # Define a cache for pasted input to avoid asking twice
        pasted_data_cache = None

        def get_pasted_data():
            nonlocal pasted_data_cache
            if pasted_data_cache is None:
                pasted_data_cache = mediainfo_chapters()
            return pasted_data_cache

        chapter_times = []
        if args.timecodes_from_source:
            chapter_times = mkv_chapters(input_mkv_path, mkvextract_path)[0]
        elif args.timecodes_from_mkv:
            chapter_times = mkv_chapters(path_validate(args.timecodes_from_mkv), mkvextract_path)[0]
        elif args.timecodes_from_mediainfo_paste:
            chapter_times = get_pasted_data()[0]
        elif args.timecodes_from_matroska_xml:
            chapter_times = xml_chapters(path_validate(args.timecodes_from_matroska_xml))[0]
        elif args.timecodes_from_ogm:
            chapter_times = ogm_chapters(path_validate(args.timecodes_from_ogm))[0]
        elif args.timecodes_from_mediainfo_file:
            chapter_times = mediainfo_txt_chapters(path_validate(args.timecodes_from_mediainfo_file))[0]
        elif args.timecodes_from_cg_xml:
            chapter_times = chaptergrabber_xml_chapters(path_validate(args.timecodes_from_cg_xml))[0]

        chapter_names = []
        if args.names_from_source:
            chapter_names = mkv_chapters(input_mkv_path, mkvextract_path)[1]
        elif args.names_from_mkv:
            chapter_names = mkv_chapters(path_validate(args.names_from_mkv), mkvextract_path)[1]
        elif args.names_from_mediainfo_paste:
            chapter_names = get_pasted_data()[1]
        elif args.names_from_matroska_xml:
            chapter_names = xml_chapters(path_validate(args.names_from_matroska_xml))[1]
        elif args.names_from_ogm:
            chapter_names = ogm_chapters(path_validate(args.names_from_ogm))[1]
        elif args.names_from_mediainfo_file:
            chapter_names = mediainfo_txt_chapters(path_validate(args.names_from_mediainfo_file))[1]
        elif args.names_from_cg_xml:
            chapter_names = chaptergrabber_xml_chapters(path_validate(args.names_from_cg_xml))[1]

        if args.test:
            print("The following chapters would be written:")

            output_dict = dict(zip(chapter_names, chapter_times, strict=False))

            print(json.dumps(output_dict, indent=2))
        else:
            mkv_writer(input_mkv_path, chapter_times, chapter_names, mkvpropedit_path)

    except (FileNotFoundError, RuntimeError, ValueError) as e:
        print(f"An error occurred: {e}")
