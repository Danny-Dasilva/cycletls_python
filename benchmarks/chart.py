"""Visualization functions for benchmark results."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List


def plot_benchmark_multi(df: pd.DataFrame, filename: str = "benchmark_results.jpg") -> None:
    """
    Generate multi-subplot bar charts comparing benchmark results.

    Args:
        df: DataFrame with columns: library, version, session_type, payload_size,
            requests, wall_time, cpu_time, req_per_sec
        filename: Output filename for the chart
    """
    # Separate main sessions (sync/async) from threaded sessions
    main_sessions = df[~df['session_type'].str.contains('threaded', na=False)]

    if main_sessions.empty:
        print("No data to plot")
        return

    # Get unique values
    sizes = sorted(main_sessions['payload_size'].unique())
    session_types = sorted(main_sessions['session_type'].unique())

    # Plot main sessions
    _plot_main_sessions(main_sessions, sizes, session_types, filename)


def _plot_main_sessions(
    df: pd.DataFrame,
    sizes: List[str],
    session_types: List[str],
    filename: str,
) -> None:
    """Generate plots for non-threaded sessions."""
    n_session_types = len(session_types)

    # Create figure with subplots (one per session type)
    fig, axes = plt.subplots(
        n_session_types, 1,
        figsize=(14, 6 * n_session_types),
        squeeze=False
    )
    axes = axes.flatten()

    # Color map for different payload sizes
    colors = plt.cm.Set3(np.linspace(0, 1, len(sizes)))

    for idx, session_type in enumerate(session_types):
        ax = axes[idx]
        session_data = df[df['session_type'] == session_type]

        if session_data.empty:
            continue

        # Get unique libraries for this session type
        libraries = sorted(session_data['library'].unique())

        # Prepare data for grouped bar chart
        x = np.arange(len(libraries))
        width = 0.8 / len(sizes) if sizes else 0.8

        # Plot bars for each payload size
        for size_idx, size in enumerate(sizes):
            size_data = session_data[session_data['payload_size'] == size]

            # Get req/sec for each library
            req_per_sec_values = []
            for lib in libraries:
                lib_data = size_data[size_data['library'] == lib]
                if not lib_data.empty:
                    req_per_sec_values.append(lib_data['req_per_sec'].values[0])
                else:
                    req_per_sec_values.append(0)

            # Plot bars
            offset = width * (size_idx - len(sizes) / 2 + 0.5)
            bars = ax.bar(
                x + offset,
                req_per_sec_values,
                width,
                label=f'{size}',
                color=colors[size_idx],
                alpha=0.8
            )

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.,
                        height,
                        f'{int(height)}',
                        ha='center',
                        va='bottom',
                        fontsize=8
                    )

        # Customize subplot
        ax.set_xlabel('Library', fontsize=12, fontweight='bold')
        ax.set_ylabel('Requests per Second', fontsize=12, fontweight='bold')
        ax.set_title(
            f'Benchmark Results - {session_type.replace("_", " ").title()}',
            fontsize=14,
            fontweight='bold'
        )
        ax.set_xticks(x)
        ax.set_xticklabels(libraries, rotation=45, ha='right')
        ax.legend(title='Payload Size', loc='upper left')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Set y-axis to start from 0
        ax.set_ylim(bottom=0)

    # Adjust layout
    plt.tight_layout()

    # Save figure
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Chart saved to {filename}")
    plt.close()


def plot_comparison_chart(
    df: pd.DataFrame,
    filename: str = "comparison.jpg",
    metric: str = "req_per_sec",
    title: str = "Library Performance Comparison"
) -> None:
    """
    Generate a simple comparison chart for a specific metric.

    Args:
        df: DataFrame with benchmark results
        filename: Output filename
        metric: Metric to plot (wall_time, cpu_time, or req_per_sec)
        title: Chart title
    """
    if df.empty:
        print("No data to plot")
        return

    # Group by library and calculate mean for the metric
    grouped = df.groupby('library')[metric].mean().sort_values(ascending=False)

    # Create bar chart
    fig, ax = plt.subplots(figsize=(12, 6))

    bars = ax.bar(
        range(len(grouped)),
        grouped.values,
        color=plt.cm.viridis(np.linspace(0, 1, len(grouped))),
        alpha=0.8
    )

    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, grouped.values)):
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            value,
            f'{value:.2f}',
            ha='center',
            va='bottom',
            fontsize=10
        )

    # Customize chart
    ax.set_xlabel('Library', fontsize=12, fontweight='bold')
    ylabel = {
        'req_per_sec': 'Requests per Second',
        'wall_time': 'Wall Time (seconds)',
        'cpu_time': 'CPU Time (seconds)'
    }.get(metric, metric)
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(grouped)))
    ax.set_xticklabels(grouped.index, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Set y-axis to start from 0
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Comparison chart saved to {filename}")
    plt.close()


def plot_cycletls_focus(
    df: pd.DataFrame,
    filename: str = "cycletls_comparison.jpg"
) -> None:
    """
    Generate a chart focused on CycleTLS performance vs other libraries.

    Args:
        df: DataFrame with benchmark results
        filename: Output filename
    """
    if df.empty or 'cycletls' not in df['library'].values:
        print("No CycleTLS data to plot")
        return

    # Get CycleTLS data
    cycletls_data = df[df['library'] == 'cycletls']
    other_data = df[df['library'] != 'cycletls']

    # Calculate average req/sec for each library
    cycletls_avg = cycletls_data['req_per_sec'].mean()
    other_avgs = other_data.groupby('library')['req_per_sec'].mean().sort_values(ascending=False)

    # Prepare data for plotting
    libraries = ['cycletls'] + list(other_avgs.index)
    values = [cycletls_avg] + list(other_avgs.values)

    # Create colors (highlight CycleTLS)
    colors = ['#ff6b6b'] + ['#4ecdc4'] * len(other_avgs)

    # Create bar chart
    fig, ax = plt.subplots(figsize=(14, 7))

    bars = ax.bar(range(len(libraries)), values, color=colors, alpha=0.8)

    # Add value labels
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            value,
            f'{value:.0f}',
            ha='center',
            va='bottom',
            fontsize=10,
            fontweight='bold'
        )

    # Customize chart
    ax.set_xlabel('Library', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Requests per Second', fontsize=12, fontweight='bold')
    ax.set_title('CycleTLS Performance vs Other Libraries', fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(libraries)))
    ax.set_xticklabels(libraries, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(bottom=0)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#ff6b6b', label='CycleTLS'),
        Patch(facecolor='#4ecdc4', label='Other Libraries')
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"CycleTLS comparison chart saved to {filename}")
    plt.close()
