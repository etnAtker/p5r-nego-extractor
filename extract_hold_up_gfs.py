"""Extract the main GFS payload from EPL files in a directory."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Sequence

GFS_MAGIC = b"GFS0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract the largest embedded GFS chunk from EPL files in a directory."
    )
    parser.add_argument(
        "--epl-dir",
        type=Path,
        required=True,
        help="Directory that contains .EPL files to scan.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/hold_up_icon_gfs"),
        help="Directory where extracted GFS files and the manifest will be written.",
    )
    return parser


def find_gfs_offsets(data: bytes) -> List[int]:
    offsets: List[int] = []
    start = 0
    while True:
        pos = data.find(GFS_MAGIC, start)
        if pos < 0:
            return offsets
        offsets.append(pos)
        start = pos + 1


def choose_main_chunk(data: bytes, offsets: Sequence[int]) -> tuple[int, bytes]:
    chunks = []
    for index, offset in enumerate(offsets):
        end = offsets[index + 1] if index + 1 < len(offsets) else len(data)
        chunks.append((offset, data[offset:end]))
    return max(chunks, key=lambda item: len(item[1]))


def iter_epl_files(epl_dir: Path) -> Iterable[Path]:
    yield from sorted(epl_dir.glob("*.EPL"))


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    epl_dir = args.epl_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_lines = ["source_epl\toutput_gfs\tgfs_offsets\tchosen_offset\tsize"]

    for epl_path in iter_epl_files(epl_dir):
        data = epl_path.read_bytes()
        offsets = find_gfs_offsets(data)

        if not offsets:
            manifest_lines.append(f"{epl_path}\t\t(no GFS0 found)\t\t{len(data)}")
            continue

        chosen_offset, chosen_chunk = choose_main_chunk(data, offsets)
        output_path = output_dir / f"{epl_path.stem}.gfs"
        output_path.write_bytes(chosen_chunk)

        joined_offsets = "|".join(str(offset) for offset in offsets)
        manifest_lines.append(
            f"{epl_path}\t{output_path}\t{joined_offsets}\t{chosen_offset}\t{len(chosen_chunk)}"
        )

    manifest_path = output_dir / "manifest.tsv"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
