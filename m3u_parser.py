import re
from dataclasses import dataclass
from typing import Dict, List, Optional


EXTINF_RE = re.compile(r"^#EXTINF:.*", re.IGNORECASE)
TVG_ID_RE = re.compile(r'tvg-id="([^"]*)"', re.IGNORECASE)
ORIGIN_RE = re.compile(r"^#\s*ORIGEN:\s*(.+)$", re.IGNORECASE)


@dataclass
class ChannelBlock:
    tvg_id: Optional[str]
    origin_url: Optional[str]
    url_line_index: Optional[int]


def load_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.readlines()


def save_lines(path: str, lines: List[str]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.writelines(lines)


def parse_blocks(lines: List[str]) -> Dict[str, ChannelBlock]:
    blocks: Dict[str, ChannelBlock] = {}
    pending_origin: Optional[str] = None
    current_tvg_id: Optional[str] = None

    for index, raw_line in enumerate(lines):
        stripped = raw_line.strip()

        origin_match = ORIGIN_RE.match(stripped)
        if origin_match:
            pending_origin = origin_match.group(1).strip()
            continue

        if EXTINF_RE.match(stripped):
            tvg_match = TVG_ID_RE.search(raw_line)
            current_tvg_id = tvg_match.group(1).strip() if tvg_match else None
            continue

        if not stripped or stripped.startswith("#"):
            continue

        if current_tvg_id:
            blocks[current_tvg_id.lower()] = ChannelBlock(
                tvg_id=current_tvg_id,
                origin_url=pending_origin,
                url_line_index=index,
            )
        pending_origin = None
        current_tvg_id = None

    return blocks


def replace_channel_urls(path: str, updates: Dict[str, str]) -> List[str]:
    lines = load_lines(path)
    blocks = parse_blocks(lines)
    changed_channels: List[str] = []

    for tvg_id, new_url in updates.items():
        block = blocks.get(tvg_id.lower())
        if not block or block.url_line_index is None:
            continue

        old_line = lines[block.url_line_index]
        old_url = old_line.rstrip("\r\n").strip()
        clean_url = new_url.strip()
        if old_url == clean_url:
            continue

        if old_line.endswith("\r\n"):
            newline = "\r\n"
        elif old_line.endswith("\n"):
            newline = "\n"
        else:
            newline = ""

        lines[block.url_line_index] = clean_url + newline
        changed_channels.append(block.tvg_id or tvg_id)

    if changed_channels:
        save_lines(path, lines)

    return changed_channels