"""
录屏回放调试工具。
读取录屏文件，运行与正式程序相同的识别逻辑，将结果输出到终端。
无 UI，无 Tkinter，可在 Linux 上运行。

用法：
    python debug_replay.py recording.mp4
    python debug_replay.py recording.mp4 --speed 2.0
    python debug_replay.py recording.mp4 --start-frame 300
"""

import argparse
import sys
from threading import Event
from typing import Iterator

import cv2
import numpy as np
from loguru import logger

from config import REFERENCE_SIZE
from tracker import Counter, run


def video_frames(
    path: str, start_frame: int = 0, speed: float = 1.0
) -> Iterator[tuple[np.ndarray, float]]:
    """从视频文件逐帧读取，产出 (灰度图, scale)。
    scale 根据视频帧高度相对参考分辨率计算，与正式程序的 get_scale() 逻辑一致。
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        logger.error(f"无法打开视频文件: {path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scale = frame_h / REFERENCE_SIZE[1]

    logger.info(
        f"视频信息: {total} 帧, {fps:.1f} fps, 帧高 {frame_h}px, 模板缩放比例 {scale:.3f}"
    )

    # 跳帧：直接 seek 到指定位置，跳过前面不感兴趣的部分
    if start_frame > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        logger.info(f"跳转到第 {start_frame} 帧")

    frame_idx = start_frame
    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            logger.info("视频读取完毕")
            break

        # OpenCV 读出的是 BGR，直接转灰度即可（与正式程序的截图处理等价）
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        frame_idx += 1

        # 每 30 帧打印一次进度，避免日志刷屏
        if frame_idx % 30 == 0:
            logger.debug(f"当前帧: {frame_idx}/{total}")

        yield gray, scale

    cap.release()


def on_update(player, cards):
    """出牌回调：格式化输出到终端，供调试时快速浏览出牌记录。"""
    cards_str = ", ".join(f"{c.value}×{n}" for c, n in cards.items())
    print(f"  → {player.value} 出牌: {cards_str}")


def main():
    parser = argparse.ArgumentParser(description="记牌器录屏回放调试工具")
    parser.add_argument("video", help="录屏文件路径")
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="回放倍速（仅影响日志密度，不实际加速）",
    )
    parser.add_argument("--start-frame", type=int, default=0, help="从第几帧开始")
    args = parser.parse_args()

    counter = Counter()
    stop_event = Event()

    # 用视频帧迭代器替换实时截图，传入同一个 run() 函数
    frames = video_frames(args.video, start_frame=args.start_frame, speed=args.speed)

    logger.info(f"开始回放: {args.video}")
    try:
        run(frames, counter, stop_event, on_update=on_update)
    except StopIteration:
        pass
    except KeyboardInterrupt:
        logger.info("用户中断")

    # 回放结束后打印最终计牌结果
    print("\n====== 最终计牌结果 ======")
    print(f"{'牌':>6}  {'剩余':>4}  {'上家':>4}  {'下家':>4}")
    print("-" * 30)
    from card_types import Card as C

    for card in C:
        r = counter.remaining[card].get()
        l = counter.left[card].get()
        ri = counter.right[card].get()
        print(f"{card.value:>6}  {r:>4}  {l:>4}  {ri:>4}")

    print(f"\n总剩余: {counter.total_remaining}")
    from card_types import Player as P

    for player in P:
        print(f"{player.value} 总出牌: {counter.total_played[player]}")


if __name__ == "__main__":
    main()
