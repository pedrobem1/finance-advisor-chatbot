"use client";

import dynamic from "next/dynamic";

import type { ChartArtifact } from "./types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export function PriceChart({ chart }: { chart: ChartArtifact }) {
  return (
    <section className="chart-artifact" aria-label={`Grafico de ${chart.symbol}`}>
      <div className="chart-artifact__header">
        <span>{chart.symbol}</span>
        <span>{chart.period}</span>
      </div>
      <Plot
        data={chart.figure.data as Plotly.Data[]}
        layout={{
          ...chart.figure.layout,
          autosize: true,
          paper_bgcolor: "#15191e",
          plot_bgcolor: "#15191e",
          font: { color: "#e7edf3", family: "Inter, ui-sans-serif, system-ui" },
          margin: { l: 48, r: 20, t: 52, b: 42 }
        }}
        config={{ displayModeBar: false, responsive: true }}
        useResizeHandler
        style={{ width: "100%", height: "300px" }}
      />
    </section>
  );
}
