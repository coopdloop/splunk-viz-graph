"""
Visualization module for vendor coverage analysis and data export.
"""

import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any
import json
from pathlib import Path


class VendorVisualizer:
    """Visualizer for vendor product analysis and gap coverage."""

    def __init__(self, style: str = "default"):
        """
        Initialize the visualizer.

        Args:
            style: Visualization style ('default', 'dark', 'presentation')
        """
        self.style = style
        self._setup_style()

    def _setup_style(self):
        """Setup visualization style and colors."""
        if self.style == "dark":
            plt.style.use("dark_background")
            self.color_palette = [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
                "#8c564b",
                "#e377c2",
                "#7f7f7f",
                "#bcbd22",
                "#17becf",
            ]
        elif self.style == "presentation":
            self.color_palette = [
                "#2E86AB",
                "#A23B72",
                "#F18F01",
                "#C73E1D",
                "#592E83",
                "#048A81",
                "#7209B7",
                "#E26D5C",
                "#472D30",
                "#723D46",
            ]
        else:
            self.color_palette = plt.cm.Set3.colors

    def create_vendor_distribution_pie(
        self, vendor_data: pd.DataFrame, title: str = "Vendor Distribution"
    ) -> go.Figure:
        """
        Create a pie chart showing vendor distribution.

        Args:
            vendor_data: DataFrame with vendor information
            title: Chart title

        Returns:
            Plotly pie chart figure
        """
        if vendor_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            fig.update_layout(title=title)
            return fig

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=vendor_data["vendor_product"],
                    values=vendor_data["count"],
                    hole=0.3,
                    textinfo="label+percent",
                    textposition="outside",
                    marker=dict(colors=self.color_palette),
                    hovertemplate="<b>%{label}</b><br>Events: %{value}<br>Percentage: %{percent}<extra></extra>",
                )
            ]
        )

        fig.update_layout(
            title={"text": title, "x": 0.5, "xanchor": "center", "font": {"size": 18}},
            font=dict(size=12),
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        return fig

    def create_gap_analysis_chart(
        self, gap_data: pd.DataFrame, title: str = "Vendor Coverage Gap Analysis"
    ) -> go.Figure:
        """
        Create a bar chart showing vendor coverage gaps.

        Args:
            gap_data: DataFrame with gap analysis data
            title: Chart title

        Returns:
            Plotly bar chart figure
        """
        if gap_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No gap analysis data available",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            fig.update_layout(title=title)
            return fig

        # Color mapping for status
        color_map = {"Present": "#2ca02c", "Missing": "#d62728", "Partial": "#ff7f0e"}

        colors = [color_map.get(status, "#7f7f7f") for status in gap_data["status"]]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=gap_data["vendor_product"],
                    y=gap_data["event_count"],
                    marker_color=colors,
                    text=gap_data["status"],
                    textposition="auto",
                    hovertemplate="<b>%{x}</b><br>Status: %{text}<br>Events: %{y}<br>Percentage: %{customdata}%<extra></extra>",
                    customdata=gap_data["percentage"],
                )
            ]
        )

        fig.update_layout(
            title={"text": title, "x": 0.5, "xanchor": "center", "font": {"size": 18}},
            xaxis_title="Vendors",
            yaxis_title="Event Count",
            font=dict(size=12),
            xaxis_tickangle=-45,
        )

        # Add annotations for missing vendors
        for i, row in gap_data.iterrows():
            if row["status"] == "Missing":
                fig.add_annotation(
                    x=row["vendor_product"],
                    y=0,
                    text="MISSING",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="red",
                    ax=0,
                    ay=-30,
                )

        return fig

    def create_category_breakdown(
        self, vendor_data: pd.DataFrame, title: str = "Vendor Categories"
    ) -> go.Figure:
        """
        Create a horizontal bar chart showing vendor categories.

        Args:
            vendor_data: DataFrame with vendor and category information
            title: Chart title

        Returns:
            Plotly horizontal bar chart
        """
        if vendor_data.empty or "category" not in vendor_data.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No category data available",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            fig.update_layout(title=title)
            return fig

        category_counts = (
            vendor_data.groupby("category")["count"].sum().sort_values(ascending=True)
        )

        fig = go.Figure(
            data=[
                go.Bar(
                    y=category_counts.index,
                    x=category_counts.values,
                    orientation="h",
                    marker_color=self.color_palette[: len(category_counts)],
                    hovertemplate="<b>%{y}</b><br>Events: %{x}<extra></extra>",
                )
            ]
        )

        fig.update_layout(
            title={"text": title, "x": 0.5, "xanchor": "center", "font": {"size": 18}},
            xaxis_title="Event Count",
            yaxis_title="Categories",
            font=dict(size=12),
            height=max(400, len(category_counts) * 40),
        )

        return fig

    def create_timeline_analysis(
        self, timeline_data: pd.DataFrame, title: str = "Vendor Activity Timeline"
    ) -> go.Figure:
        """
        Create a timeline chart showing vendor activity over time.

        Args:
            timeline_data: DataFrame with time-based vendor data
            title: Chart title

        Returns:
            Plotly line chart
        """
        if timeline_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No timeline data available",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            fig.update_layout(title=title)
            return fig

        fig = go.Figure()

        vendors = timeline_data["vendor_product"].unique()

        for i, vendor in enumerate(vendors):
            vendor_data = timeline_data[timeline_data["vendor_product"] == vendor]
            fig.add_trace(
                go.Scatter(
                    x=vendor_data["timestamp"],
                    y=vendor_data["count"],
                    mode="lines+markers",
                    name=vendor,
                    line=dict(color=self.color_palette[i % len(self.color_palette)]),
                    hovertemplate="<b>%{fullData.name}</b><br>Time: %{x}<br>Events: %{y}<extra></extra>",
                )
            )

        fig.update_layout(
            title={"text": title, "x": 0.5, "xanchor": "center", "font": {"size": 18}},
            xaxis_title="Time",
            yaxis_title="Event Count",
            font=dict(size=12),
            hovermode="x unified",
        )

        return fig

    def create_summary_dashboard(
        self,
        vendor_data: pd.DataFrame,
        gap_data: pd.DataFrame,
        summary_stats: Dict[str, Any],
    ) -> go.Figure:
        """
        Create a comprehensive dashboard with multiple visualizations.

        Args:
            vendor_data: DataFrame with vendor information
            gap_data: DataFrame with gap analysis
            summary_stats: Dictionary with summary statistics

        Returns:
            Plotly dashboard figure with subplots
        """
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Vendor Distribution",
                "Gap Analysis",
                "Category Breakdown",
                "Summary Stats",
            ),
            specs=[
                [{"type": "domain"}, {"type": "xy"}],
                [{"type": "xy"}, {"type": "table"}],
            ],
        )

        # Vendor Distribution Pie Chart (top-left)
        if not vendor_data.empty:
            fig.add_trace(
                go.Pie(
                    labels=vendor_data["vendor_product"][:10],  # Top 10 vendors
                    values=vendor_data["count"][:10],
                    name="Distribution",
                ),
                row=1,
                col=1,
            )

        # Gap Analysis Bar Chart (top-right)
        if not gap_data.empty:
            colors = [
                "red" if status == "Missing" else "green"
                for status in gap_data["status"]
            ]
            fig.add_trace(
                go.Bar(
                    x=gap_data["vendor_product"],
                    y=gap_data["event_count"],
                    marker_color=colors,
                    name="Gaps",
                ),
                row=1,
                col=2,
            )

        # Category Breakdown (bottom-left)
        if not vendor_data.empty and "category" in vendor_data.columns:
            category_counts = vendor_data.groupby("category")["count"].sum()
            fig.add_trace(
                go.Bar(
                    x=category_counts.index, y=category_counts.values, name="Categories"
                ),
                row=2,
                col=1,
            )

        # Summary Stats Table (bottom-right)
        stats_table = [
            ["Total Vendors", summary_stats.get("total_vendors", 0)],
            ["Total Events", summary_stats.get("total_events", 0)],
            ["Top Vendor", summary_stats.get("top_vendor", "N/A")],
            ["Unknown %", f"{summary_stats.get('unknown_percentage', 0):.1f}%"],
        ]

        fig.add_trace(
            go.Table(
                header=dict(values=["Metric", "Value"], fill_color="lightblue"),
                cells=dict(values=list(zip(*stats_table)), fill_color="white"),
            ),
            row=2,
            col=2,
        )

        fig.update_layout(
            title_text="Vendor Analysis Dashboard", showlegend=False, height=800
        )

        return fig

    def export_to_csv(
        self, data: pd.DataFrame, filename: str, output_dir: str = "exports"
    ) -> str:
        """
        Export data to CSV format.

        Args:
            data: DataFrame to export
            filename: Output filename (without extension)
            output_dir: Output directory

        Returns:
            Path to exported file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        file_path = output_path / f"{filename}.csv"
        data.to_csv(file_path, index=False)

        return str(file_path)

    def export_to_json(
        self, data: pd.DataFrame, filename: str, output_dir: str = "exports"
    ) -> str:
        """
        Export data to JSON format.

        Args:
            data: DataFrame to export
            filename: Output filename (without extension)
            output_dir: Output directory

        Returns:
            Path to exported file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        file_path = output_path / f"{filename}.json"

        # Convert DataFrame to JSON with proper formatting
        json_data = {
            "metadata": {
                "export_timestamp": pd.Timestamp.now().isoformat(),
                "total_records": len(data),
                "columns": list(data.columns),
            },
            "data": data.to_dict("records"),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, default=str)

        return str(file_path)

    def export_chart_html(
        self, fig: go.Figure, filename: str, output_dir: str = "exports"
    ) -> str:
        """
        Export Plotly chart to HTML file.

        Args:
            fig: Plotly figure
            filename: Output filename (without extension)
            output_dir: Output directory

        Returns:
            Path to exported file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        file_path = output_path / f"{filename}.html"
        fig.write_html(str(file_path))

        return str(file_path)

    def create_matplotlib_summary(
        self, vendor_data: pd.DataFrame, figsize: tuple = (15, 10)
    ) -> plt.Figure:
        """
        Create a matplotlib-based summary visualization.

        Args:
            vendor_data: DataFrame with vendor information
            figsize: Figure size tuple

        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle("Vendor Analysis Summary", fontsize=16, fontweight="bold")

        if vendor_data.empty:
            for ax in axes.flat:
                ax.text(
                    0.5,
                    0.5,
                    "No data available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
            return fig

        # Top 10 vendors pie chart
        top_vendors = vendor_data.head(10)
        axes[0, 0].pie(
            top_vendors["count"],
            labels=top_vendors["vendor_product"],
            autopct="%1.1f%%",
        )
        axes[0, 0].set_title("Top 10 Vendors Distribution")

        # Vendor counts bar chart
        axes[0, 1].bar(
            range(len(top_vendors)),
            top_vendors["count"],
            color=self.color_palette[: len(top_vendors)],
        )
        axes[0, 1].set_title("Event Count by Vendor")
        axes[0, 1].set_xticks(range(len(top_vendors)))
        axes[0, 1].set_xticklabels(
            top_vendors["vendor_product"], rotation=45, ha="right"
        )

        # Category distribution
        if "category" in vendor_data.columns:
            category_counts = vendor_data.groupby("category")["count"].sum()
            axes[1, 0].barh(range(len(category_counts)), category_counts.values)
            axes[1, 0].set_title("Events by Category")
            axes[1, 0].set_yticks(range(len(category_counts)))
            axes[1, 0].set_yticklabels(category_counts.index)

        # Summary statistics
        axes[1, 1].axis("off")
        stats_text = f"""
        Total Vendors: {len(vendor_data)}
        Total Events: {vendor_data['count'].sum():,}
        Top Vendor: {vendor_data.iloc[0]['vendor_product']}
        Top Vendor Events: {vendor_data.iloc[0]['count']:,}
        """
        axes[1, 1].text(
            0.1,
            0.5,
            stats_text,
            transform=axes[1, 1].transAxes,
            fontsize=12,
            verticalalignment="center",
        )
        axes[1, 1].set_title("Summary Statistics")

        plt.tight_layout()
        return fig
