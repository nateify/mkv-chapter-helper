import argparse

from mkv_chapter_helper.main import main


def cli():
    parser = argparse.ArgumentParser(description="Add/modify chapters in an MKV file")
    parser.add_argument("input", type=str, help="MKV file to be modified")

    timecode_group = parser.add_argument_group("Timecode source (one is required)")
    timecode_src = timecode_group.add_mutually_exclusive_group(required=True)
    timecode_src.add_argument(
        "-tS", "--timecodes-from-source", action="store_true", help="Use timecodes from the input MKV file"
    )
    timecode_src.add_argument(
        "-tM", "--timecodes-from-mkv", metavar="FILE", help="Use timecodes from a different MKV file"
    )
    timecode_src.add_argument(
        "-tX", "--timecodes-from-matroska-xml", metavar="FILE", help="Use timecodes from a Matroska XML file"
    )
    timecode_src.add_argument(
        "-tC", "--timecodes-from-cg-xml", metavar="FILE", help="Use timecodes from a ChapterGrabber XML file"
    )
    timecode_src.add_argument(
        "-tO", "--timecodes-from-ogm", metavar="FILE", help="Use timecodes from an OGM chapter TXT file"
    )
    timecode_src.add_argument(
        "-tI", "--timecodes-from-mediainfo-file", metavar="FILE", help="Use timecodes from a MediaInfo TXT report file"
    )
    timecode_src.add_argument(
        "-tP",
        "--timecodes-from-mediainfo-paste",
        action="store_true",
        help="Use timecodes from pasted MediaInfo menu content",
    )

    name_group = parser.add_argument_group("Chapter name source (one is required)")
    name_src = name_group.add_mutually_exclusive_group(required=True)
    name_src.add_argument(
        "-nS", "--names-from-source", action="store_true", help="Use chapter names from the input MKV file"
    )
    name_src.add_argument("-nM", "--names-from-mkv", metavar="FILE", help="Use chapter names from a different MKV file")
    name_src.add_argument(
        "-nX", "--names-from-matroska-xml", metavar="FILE", help="Use chapter names from a Matroska XML file"
    )
    name_src.add_argument(
        "-nC", "--names-from-cg-xml", metavar="FILE", help="Use chapter names from a ChapterGrabber XML file"
    )
    name_src.add_argument(
        "-nO", "--names-from-ogm", metavar="FILE", help="Use chapter names from an OGM chapter TXT file"
    )
    name_src.add_argument(
        "-nI", "--names-from-mediainfo-file", metavar="FILE", help="Use chapter names from a MediaInfo TXT report file"
    )
    name_src.add_argument(
        "-nP",
        "--names-from-mediainfo-paste",
        action="store_true",
        help="Use chapter names from pasted MediaInfo menu content",
    )

    tool_path_group = parser.add_argument_group("Tool paths (optional)")
    tool_path_group.add_argument("--mkvpropedit-path", metavar="PATH", help="Path to the mkvpropedit executable")
    tool_path_group.add_argument("--mkvextract-path", metavar="PATH", help="Path to the mkvextract executable")

    parser.add_argument("--test", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.timecodes_from_source and args.names_from_source:
        parser.error("Cannot use the source MKV for both timecodes and names, this would result in no change.")

    main(args)


if __name__ == "__main__":
    cli()
