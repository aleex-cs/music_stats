import os
import tempfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patheffects as pe
from matplotlib.animation import FFMpegWriter

TOP_N = 10
FRAMES_PER_PERIOD = 30   # frames per period = 1 second per month at 30fps
FPS = 30
HOLD_FRAMES = 90         # hold ~3s at the end
Y_SMOOTH = 0.25          # how fast bars slide to new rank (0-1, higher = faster)

PALETTE = [
    "#FF4B4B", "#FF8C42", "#FFD166", "#06D6A0", "#118AB2",
    "#8338EC", "#FB5607", "#3A86FF", "#FF006E", "#38B000",
    "#FFBE0B", "#7400B8", "#80B918", "#023E8A", "#E63946",
    "#4CC9F0", "#F72585", "#4361EE", "#7209B7", "#560BAD",
]


def generate_bar_race(
    df_all: pd.DataFrame,
    period_col: str,
    entity_col: str,
    minutes_col: str,
    title: str,
    progress_callback=None,
) -> bytes:
    # ── 1. Pivot & cumulative ─────────────────────────────────────────────────
    pivot = (
        df_all
        .groupby([period_col, entity_col])[minutes_col]
        .sum()
        .unstack(fill_value=0)
    )
    ordered_periods = df_all[period_col].drop_duplicates().tolist()
    pivot = pivot.reindex(ordered_periods, fill_value=0).fillna(0)
    cum = pivot.cumsum()

    entities = cum.columns.tolist()
    entity_colors = {e: PALETTE[i % len(PALETTE)] for i, e in enumerate(entities)}
    max_val = float(cum.values.max()) if cum.values.max() > 0 else 1.0

    # ── 2. Build frame values (linear interpolation = constant growth rate) ───
    periods = cum.index.tolist()
    frame_values = []   # list of (pd.Series of values, period_label)

    for i, period in enumerate(periods):
        curr = cum.iloc[i]
        if i < len(periods) - 1:
            nxt = cum.iloc[i + 1]
            for f in range(FRAMES_PER_PERIOD):
                t = f / FRAMES_PER_PERIOD   # linear — no easing
                frame_values.append((curr + (nxt - curr) * t, period))
        else:
            for _ in range(HOLD_FRAMES):
                frame_values.append((curr, period))

    total_frames = len(frame_values)

    # ── 3. Figure setup ───────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 7.5))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")
    plt.subplots_adjust(left=0.02, right=0.86, top=0.90, bottom=0.08)

    # ── 4. Smooth Y position state (persists across frames) ───────────────────
    # Initialise all entities at their starting rank (bottom = high rank number)
    initial_vals = cum.iloc[0]
    initial_order = initial_vals.sort_values(ascending=False).index.tolist()
    y_pos = {e: float(initial_order.index(e)) for e in entities}

    def draw_frame(values_series: pd.Series, period_label: str):
        # Target rank: sorted by current value descending → rank 0 = top
        sorted_desc = values_series.sort_values(ascending=False).index.tolist()
        target_rank = {e: float(i) for i, e in enumerate(sorted_desc)}

        # Smoothly slide each entity toward its target rank
        for e in entities:
            if e not in y_pos:
                y_pos[e] = target_rank.get(e, float(TOP_N))
            else:
                y_pos[e] += (target_rank[e] - y_pos[e]) * Y_SMOOTH

        ax.clear()
        ax.set_facecolor("#0d1117")

        # Only draw entities currently in the visible top N window
        # Visible = y_pos < TOP_N + 1 (a little buffer for sliding in/out)
        visible = [e for e in entities if y_pos[e] < TOP_N + 0.5]

        for e in visible:
            val = float(values_series.get(e, 0))
            y = TOP_N - 1 - y_pos[e]   # flip: rank 0 → top of chart

            color = entity_colors.get(e, "#aaaaaa")
            ax.barh(y, val, color=color, height=0.72,
                    edgecolor="none", alpha=0.93, zorder=3)

            # Value label right of bar
            ax.text(
                val + max_val * 0.008, y,
                f"{val:,.0f} min",
                va="center", ha="left", color="white",
                fontsize=9, fontweight="bold",
                path_effects=[pe.withStroke(linewidth=2, foreground="#0d1117")],
                zorder=4,
            )

            # Entity name inside/left of bar
            label_x = max(val - max_val * 0.008, max_val * 0.008)
            ax.text(
                label_x, y,
                e,
                va="center", ha="right", color="white",
                fontsize=9.5, fontweight="bold",
                path_effects=[pe.withStroke(linewidth=2.5, foreground="#0d1117")],
                zorder=4,
            )

        ax.set_xlim(0, max_val * 1.18)
        ax.set_ylim(-0.6, TOP_N - 0.4)
        ax.set_yticks([])
        ax.tick_params(axis="x", colors="#666666", labelsize=8)
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#2a2a2a")
        ax.xaxis.set_tick_params(length=0)
        ax.xaxis.grid(True, color="#1a2030", linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)

        # Watermark period label
        ax.text(0.97, 0.04, period_label,
                transform=ax.transAxes, ha="right", va="bottom",
                color="#ffffff", fontsize=30, fontweight="bold",
                alpha=0.15, zorder=1)

        fig.suptitle(title, color="white", fontsize=14,
                     fontweight="bold", x=0.44, y=0.97)

    def animate(idx):
        vals, lbl = frame_values[idx]
        draw_frame(vals, lbl)
        if progress_callback:
            progress_callback(idx + 1, total_frames)

    # ── 5. Render ─────────────────────────────────────────────────────────────
    anim_obj = animation.FuncAnimation(
        fig, animate, frames=total_frames, interval=1000 / FPS
    )
    writer = FFMpegWriter(
        fps=FPS, bitrate=3000,
        extra_args=["-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "20"],
    )

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        anim_obj.save(tmp_path, writer=writer, dpi=130)
        plt.close(fig)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)