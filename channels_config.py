from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ChannelConfig:
    tvg_id: str
    display_name: str
    origin_url: str
    expected_hosts: Tuple[str, ...]
    preferred_hosts: Tuple[str, ...] = ()
    embed_urls: Tuple[str, ...] = ()
    wait_after_load_ms: int = 12000
    navigation_timeout_ms: int = 45000


CHANNELS = (
    ChannelConfig(
        tvg_id="Telefuturo.py@SD",
        display_name="Telefuturo",
        origin_url="https://www.telefuturo.com.py/envivo",
        expected_hosts=("desdeparaguay.net", "copacotf.desdeparaguay.net"),
        preferred_hosts=("copacotf.desdeparaguay.net",),
        wait_after_load_ms=20000,
    ),
    ChannelConfig(
        tvg_id="Trece.py@SD",
        display_name="Trece",
        origin_url="https://www.dailymotion.com/embed/video/x8w6m0h",
        expected_hosts=("dmcdn.net", "dailymotion.com"),
        preferred_hosts=("dmcdn.net",),
    ),
    ChannelConfig(
        tvg_id="Unicanal.py@SD",
        display_name="Unicanal",
        origin_url="https://www.dailymotion.com/embed/video/x8w6m0i",
        expected_hosts=("dmcdn.net", "dailymotion.com"),
        preferred_hosts=("dmcdn.net",),
    ),
    ChannelConfig(
        tvg_id="ESPN.py@SD",
        display_name="ESPN",
        origin_url="https://tele-libre.click/en-vivo/stream-01.php",
        expected_hosts=("streamtpday.xyz", "tele-libre.click"),
        preferred_hosts=("streamtpday.xyz",),
        embed_urls=(
            "https://tele-libre.click/en-vivo/espn/embed2.php",
            "https://tele-libre.click/en-vivo/espn/embed3.php",
        ),
    ),
    ChannelConfig(
        tvg_id="ESPN2.py@SD",
        display_name="ESPN2",
        origin_url="https://tele-libre.click/en-vivo/stream-02.php",
        expected_hosts=("streamtpday.xyz", "tele-libre.click"),
        preferred_hosts=("streamtpday.xyz",),
        embed_urls=(
            "https://tele-libre.click/en-vivo/espn-2/embed2.php",
            "https://tele-libre.click/en-vivo/espn-2/embed3.php",
        ),
    ),
)


CHANNELS_BY_ID = {channel.tvg_id.lower(): channel for channel in CHANNELS}