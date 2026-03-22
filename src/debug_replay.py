"""
录屏回放调试工具。
读取录屏文件，运行与正式程序相同的识别逻辑，将结果输出到终端。
无 UI，无 Tkinter，可在 Linux 上运行。

用法：
    python debug_replay.py recording.mp4
    python debug_replay.py recording.mp4 --sample-interval 0.5
    python debug_replay.py recording.mp4 --start-time 1:30 --end-time 5:00
"""

import argparse
import sys
from pathlib import Path
from threading import Event
from typing import Iterator

import cv2
import numpy as np
from loguru import logger

from capture import region_to_pixels
from config import LOG_RETENTION, REGIONS, TEMPLATE_SCALE
import tracker
from tracker import Counter, run


# ---------------------------------------------------------------------------
# 日志初始化
# ---------------------------------------------------------------------------

logger.remove()


def video_frames(
    path: str, start_frame: int = 0, end_frame: int = 0, sample_interval: float = 0.0
) -> Iterator[tuple[np.ndarray, float, tuple[int, int, int, int]]]:
    """从视频文件逐帧读取，产出 (灰度图, scale, window_rect)。
    window_rect 用视频的实际分辨率构造为 (0, 0, width, height)，
    region_to_pixels 直接用录制时的分辨率做坐标转换，无需任何 fallback。
    scale 使用 config.yaml 中的 TEMPLATE_SCALE，与正式程序一致。
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        logger.error(f"无法打开视频文件: {path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    window_rect = (0, 0, w, h)  # 视频帧坐标从 (0,0) 起，宽高即录制分辨率
    stop_at = end_frame if end_frame > 0 else total
    if sample_interval > 0:
        logger.info(f"采样间隔: {sample_interval}s（每 {max(1, round(sample_interval * fps))} 帧取一帧）")

    logger.info(
        f"视频信息: {total} 帧, {fps:.1f} fps, 分辨率 {w}x{h}, 模板缩放比例 {TEMPLATE_SCALE:.3f}"
    )

    # 跳帧：直接 seek 到指定位置，跳过前面不感兴趣的部分
    if start_frame > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        logger.info(f"跳转到第 {start_frame} 帧")

    step = max(1, round(sample_interval * fps)) if sample_interval > 0 else 1
    frame_idx = start_frame
    while frame_idx < stop_at:
        ret, frame_bgr = cap.read()
        if not ret:
            logger.info("视频读取完毕")
            break

        # 跳过中间帧：顺序读取比 seek 快得多
        if (frame_idx - start_frame) % step != 0:
            frame_idx += 1
            continue

        # OpenCV 读出的是 BGR，直接转灰度即可（与正式程序的截图处理等价）
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        logger.debug(f"当前帧: {frame_idx}/{total}")

        yield gray, TEMPLATE_SCALE, window_rect

        frame_idx += 1

    cap.release()


def parse_timestamp(ts: str, fps: float) -> int:
    """将时间戳字符串（秒数或 MM:SS 或 HH:MM:SS）转换为帧号。"""
    parts = ts.split(":")
    try:
        if len(parts) == 1:
            seconds = float(parts[0])
        elif len(parts) == 2:
            seconds = int(parts[0]) * 60 + float(parts[1])
        else:
            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except ValueError:
        logger.error(f"无法解析时间戳: {ts}，格式应为秒数、MM:SS 或 HH:MM:SS")
        sys.exit(1)
    return round(seconds * fps)


def dump_regions(video_path: str, output_path: str, frame_index: int = 0, timestamp: str = "") -> None:
    """读取视频指定帧，在上面画出所有 REGIONS 的矩形框，保存为图片。"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"无法打开视频文件: {video_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    if timestamp:
        frame_index = parse_timestamp(timestamp, fps)
        logger.info(f"时间戳 {timestamp} → 第 {frame_index} 帧（{fps:.1f} fps）")

    if frame_index > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

    ret, frame_bgr = cap.read()
    cap.release()
    if not ret:
        logger.error("无法读取第一帧")
        sys.exit(1)

    h, w = frame_bgr.shape[:2]
    window_rect = (0, 0, w, h)

    # 每个区域用不同颜色，循环使用
    colors = [
        (0, 255, 0), (0, 0, 255), (255, 0, 0),
        (0, 255, 255), (255, 0, 255), (255, 165, 0),
        (128, 0, 128), (0, 128, 128),
    ]

    for i, region_name in enumerate(REGIONS):
        x1, y1, x2, y2 = region_to_pixels(region_name, window_rect)
        color = colors[i % len(colors)]
        cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame_bgr, region_name, (x1, max(y1 - 6, 12)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA,
        )

    cv2.imwrite(output_path, frame_bgr)
    logger.info(f"区域示意图已保存到: {output_path}")


def make_on_update(counter):
    def on_update(player, cards):
        cards_str = ", ".join(f"{c.value}×{n}" for c, n in cards.items())
        remaining_str = "  ".join(
            f"{c.value}:{counter.remaining[c].get()}"
            for c in counter.remaining
            if counter.remaining[c].get() < 4
        )
        logger.info(f"{player.value} 出牌: {cards_str} | 剩余: {remaining_str} （共{counter.total_remaining}张）")
    return on_update


def main():
    parser = argparse.ArgumentParser(description="记牌器录屏回放调试工具")
    parser.add_argument("video", help="录屏文件路径")
    parser.add_argument("--start-frame", type=int, default=0, help="从第几帧开始")
    parser.add_argument("--start-time", metavar="TIME", help="开始时间戳（秒数、MM:SS 或 HH:MM:SS），优先于 --start-frame")
    parser.add_argument("--end-frame", type=int, default=0, help="到第几帧结束（默认播放到结尾）")
    parser.add_argument("--end-time", metavar="TIME", help="结束时间戳（秒数、MM:SS 或 HH:MM:SS），优先于 --end-frame")
    parser.add_argument("--sample-interval", type=float, default=0.0, metavar="SECONDS", help="每隔多少秒取一帧（默认逐帧）")
    parser.add_argument("--quiet", action="store_true", help="压制像素未变的 DEBUG 日志")
    parser.add_argument("--log-level", default="INFO", metavar="LEVEL", help="日志级别：TRACE/DEBUG/INFO/WARNING/ERROR（默认 INFO）")
    parser.add_argument(
        "--dump-regions",
        metavar="OUTPUT",
        help="将指定帧加上区域框后保存为图片（如 regions.png），保存后直接退出",
    )
    parser.add_argument(
        "--dump-frame",
        type=int,
        default=0,
        metavar="FRAME",
        help="--dump-regions 使用的帧编号（默认为第 0 帧）",
    )
    parser.add_argument(
        "--dump-time",
        metavar="TIME",
        help="--dump-regions 使用的时间戳，格式为秒数、MM:SS 或 HH:MM:SS（优先于 --dump-frame）",
    )
    args = parser.parse_args()

    level = args.log_level.upper()
    _quiet_filter = (lambda r: "像素未变" not in r["message"]) if args.quiet else None
    logger.add(sys.stderr, level=level, filter=_quiet_filter)

    _log_dir = Path(__file__).parent / "logs"
    _log_dir.mkdir(exist_ok=True)
    logger.add(
        _log_dir / "debug_{time:YYYY-MM-DD}.log",
        level=level,
        filter=_quiet_filter,
        retention=f"{LOG_RETENTION} days",
        rotation="00:00",
    )

    if args.dump_regions:
        dump_regions(args.video, args.dump_regions, args.dump_frame, args.dump_time or "")
        return

    # 录屏回放不需要 sleep，patch 掉避免浪费时间
    tracker.sleep = lambda _: None

    import tkinter as tk
    _root = tk.Tk()
    _root.withdraw()  # 隐藏窗口，仅用于满足 tk.IntVar 的依赖

    counter = Counter()
    stop_event = Event()

    def print_result():
        from card_types import Card as C, Player as P
        lines = ["====== 本局计牌结果 ======", f"{'牌':>6}  {'剩余':>4}  {'上家':>4}  {'下家':>4}", "-" * 30]
        for card in C:
            r = counter.remaining[card].get()
            l = counter.left[card].get()
            ri = counter.right[card].get()
            lines.append(f"{card.value:>6}  {r:>4}  {l:>4}  {ri:>4}")
        lines.append(f"总剩余: {counter.total_remaining}")
        for player in P:
            lines.append(f"{player.value} 总出牌: {counter.total_played[player]}")
        logger.info("\n" + "\n".join(lines))

    _original_reset = counter.reset
    def _reset_with_print():
        if any(v > 0 for v in counter.total_played.values()):
            print_result()
        _original_reset()
    counter.reset = _reset_with_print

    # 解析开始/结束时间戳（需要先探一下 fps）
    cap_probe = cv2.VideoCapture(args.video)
    probe_fps = cap_probe.get(cv2.CAP_PROP_FPS) or 30
    cap_probe.release()

    start_frame = parse_timestamp(args.start_time, probe_fps) if args.start_time else args.start_frame
    end_frame = parse_timestamp(args.end_time, probe_fps) if args.end_time else args.end_frame

    # 用视频帧迭代器替换实时截图，传入同一个 run() 函数
    frames = video_frames(args.video, start_frame=start_frame, end_frame=end_frame, sample_interval=args.sample_interval)

    logger.info(f"开始回放: {args.video}")
    try:
        run(frames, counter, stop_event, on_update=make_on_update(counter))
    except StopIteration:
        pass
    except KeyboardInterrupt:
        logger.info("用户中断")

    pass


if __name__ == "__main__":
    main()
