/* ==========================================================================
   FitTrack — charts.js
   Renders the six analytics charts as inline SVG.

   Data comes from a JSON payload produced by Flask (app.analytics) and stored
   in <script type="application/json" data-chart-source>. Nothing is hardcoded
   here: if a series is empty the chart shows a friendly empty state.
   ========================================================================== */

(function () {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const source = document.querySelector("[data-chart-source]");
  if (!source) return;

  let payload;
  try {
    payload = JSON.parse(source.textContent);
  } catch (error) {
    return;
  }
  if (!payload) return;

  const EMPTY_MESSAGE =
    "No recorded data yet. Add a record and this chart will update automatically.";

  function svgElement(name, attributes) {
    const element = document.createElementNS(SVG_NS, name);
    Object.entries(attributes || {}).forEach(([key, value]) => {
      element.setAttribute(key, String(value));
    });
    return element;
  }

  function addText(parent, x, y, text, options) {
    const opts = options || {};
    const node = svgElement("text", {
      x: x,
      y: y,
      "font-size": opts.size || 8,
      fill: opts.fill || "#94a3b8",
      "text-anchor": opts.anchor || "middle",
      "font-family": "Inter, system-ui, sans-serif",
    });
    if (opts.rotate) {
      node.setAttribute("transform", `rotate(${opts.rotate} ${x} ${y})`);
    }
    node.textContent = text;
    parent.appendChild(node);
    return node;
  }

  function shortLabel(label) {
    const text = String(label || "");
    const dateMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (dateMatch) return `${dateMatch[2]}-${dateMatch[3]}`;
    return text.length > 10 ? `${text.slice(0, 9)}…` : text;
  }

  function renderEmpty(container) {
    container.textContent = "";
    const message = document.createElement("p");
    message.className = "chart-empty";
    message.textContent = EMPTY_MESSAGE;
    container.appendChild(message);
  }

  function renderChart(container, config) {
    if (!config || !config.has_data || !config.labels || !config.labels.length) {
      renderEmpty(container);
      return;
    }

    const width = 340;
    const height = 180;
    const padding = { top: 16, right: 12, bottom: 34, left: 34 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;

    const series = (config.series || []).filter(
      (item) => item && Array.isArray(item.values)
    );
    if (!series.length) {
      renderEmpty(container);
      return;
    }

    const values = series.flatMap((item) =>
      item.values.map((value) => Number(value) || 0)
    );
    let maximum = Math.max(...values, 0);
    if (maximum <= 0) {
      renderEmpty(container);
      return;
    }
    maximum *= 1.12;

    const svg = svgElement("svg", {
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      "aria-label": config.series.map((item) => item.name).join(", "),
      class: "chart-svg",
    });

    // Horizontal grid lines and value labels.
    for (let step = 0; step <= 3; step += 1) {
      const value = (maximum / 3) * step;
      const y = padding.top + plotHeight - (value / maximum) * plotHeight;
      svg.appendChild(
        svgElement("line", {
          x1: padding.left,
          y1: y,
          x2: width - padding.right,
          y2: y,
          stroke: "#1f2a37",
          "stroke-width": 0.7,
        })
      );
      addText(svg, padding.left - 4, y + 3, Math.round(value), {
        anchor: "end",
        size: 7,
      });
    }

    const pointCount = config.labels.length;
    const stepX = pointCount > 1 ? plotWidth / (pointCount - 1) : plotWidth;
    const colors = ["#22d3ee", "#a78bfa", "#34d399", "#fbbf24"];

    if (config.type === "bar") {
      const groupWidth = plotWidth / pointCount;
      const barWidth = Math.max(4, Math.min(26, groupWidth * 0.62));
      series.forEach((item, seriesIndex) => {
        item.values.forEach((value, index) => {
          const numeric = Number(value) || 0;
          const barHeight = (numeric / maximum) * plotHeight;
          const x =
            padding.left +
            groupWidth * index +
            (groupWidth - barWidth) / 2 +
            seriesIndex * 1.5;
          const y = padding.top + plotHeight - barHeight;
          const rect = svgElement("rect", {
            x: x,
            y: y,
            width: Math.max(2, barWidth),
            height: Math.max(0.5, barHeight),
            rx: 2,
            fill: colors[seriesIndex % colors.length],
            opacity: 0.9,
          });
          const title = svgElement("title", {});
          title.textContent = `${config.labels[index]}: ${numeric} ${item.name}`;
          rect.appendChild(title);
          svg.appendChild(rect);
        });
      });
    } else {
      series.forEach((item, seriesIndex) => {
        const points = item.values.map((value, index) => {
          const numeric = Number(value) || 0;
          const x = padding.left + stepX * index;
          const y = padding.top + plotHeight - (numeric / maximum) * plotHeight;
          return [x, y, numeric];
        });
        const pathData = points
          .map((point, index) => `${index === 0 ? "M" : "L"}${point[0]},${point[1]}`)
          .join(" ");
        svg.appendChild(
          svgElement("path", {
            d: pathData,
            fill: "none",
            stroke: colors[seriesIndex % colors.length],
            "stroke-width": 2,
            "stroke-linejoin": "round",
            "stroke-linecap": "round",
          })
        );
        points.forEach((point, index) => {
          const circle = svgElement("circle", {
            cx: point[0],
            cy: point[1],
            r: 2.4,
            fill: colors[seriesIndex % colors.length],
          });
          const title = svgElement("title", {});
          title.textContent = `${config.labels[index]}: ${point[2]} ${item.name}`;
          circle.appendChild(title);
          svg.appendChild(circle);
        });
      });
    }

    // X-axis labels, thinned out so they never overlap.
    const labelStep = Math.max(1, Math.ceil(pointCount / 6));
    config.labels.forEach((label, index) => {
      if (index % labelStep !== 0 && index !== pointCount - 1) return;
      const x =
        config.type === "bar"
          ? padding.left + (plotWidth / pointCount) * (index + 0.5)
          : padding.left + stepX * index;
      addText(svg, x, height - padding.bottom + 14, shortLabel(label), {
        size: 7,
      });
    });

    // Legend.
    const legend = document.createElement("div");
    legend.className = "chart-legend";
    series.forEach((item, index) => {
      const entry = document.createElement("span");
      entry.className = "chart-legend-item";
      const swatch = document.createElement("span");
      swatch.className = "chart-swatch";
      swatch.style.background = colors[index % colors.length];
      entry.appendChild(swatch);
      entry.appendChild(document.createTextNode(item.name));
      legend.appendChild(entry);
    });

    container.textContent = "";
    container.appendChild(svg);
    container.appendChild(legend);
  }

  document.querySelectorAll("[data-chart-key]").forEach((container) => {
    const key = container.getAttribute("data-chart-key");
    renderChart(container, payload[key]);
  });
})();
