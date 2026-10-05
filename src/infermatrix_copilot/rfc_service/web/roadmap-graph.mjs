/* Source diagrams supply layout context; tracking supplies work and state. */
export const roadmapSVGStyles = `
svg{font-family:system-ui,sans-serif;font-size:15px;color:#0f172a}
svg text{fill:#0f172a;font-family:system-ui,sans-serif;font-size:15px;text-anchor:middle}
svg .node rect,svg .node polygon,svg .node circle{fill:#f1f5f9;stroke:#64748b;stroke-width:2px}
svg .node.implemented rect{fill:#dcfce7;stroke:#15803d}
svg .node.accepted rect{fill:#bbf7d0;stroke:#166534;stroke-width:3px}
svg .node.partial rect{fill:#fef3c7;stroke:#b45309}
svg .node.in_progress rect{fill:#dbeafe;stroke:#2563eb}
svg .node.blocked rect{fill:#fee2e2;stroke:#dc2626}
svg .node.context rect{fill:#f8fafc;stroke:#94a3b8}
svg .flowchart-link,svg .edgePath .path{fill:none;stroke:#94a3b8;stroke-width:1.5px}
svg marker path{fill:#94a3b8;stroke:#94a3b8}
svg .edgeLabel rect,svg .labelBkg{fill:#fff}
svg .roadmap-actionable{cursor:pointer}
svg .roadmap-actionable:hover rect,svg .roadmap-actionable:focus rect{stroke-width:4px}
svg .roadmap-actionable:focus{outline:2px solid #2563eb;outline-offset:4px}
`;
export function graphModels(rfc) {
  const all = new Map((rfc.features || []).map(feature => [feature.id, feature]));
  const active = new Map([...all].filter(([, feature]) => !feature.dropped));
  const covered = new Set();
  const models = [];
  const body = String(rfc.body || "");
  for (const match of body.matchAll(/```mermaid\s*\n([\s\S]*?)```/g)) {
    if (!/^\s*(?:flowchart|graph)\s+(?:LR|RL|TD|TB|BT)\b/.test(match[1])) continue;
    const nodes = new Map(), edges = [];
    const add = (id, title) => {
      if (all.has(id) && !active.has(id)) return;
      if (!nodes.has(id)) nodes.set(id, {id, title: title || active.get(id)?.title || id, feature: active.get(id)});
      else if (title) nodes.get(id).title = title;
    };
    for (const line of match[1].split("\n")) {
      // Rebuild a limited flowchart grammar. Never execute source directives,
      // click callbacks, HTML, classes, or source-controlled Mermaid settings.
      if (/^\s*(?:%%|class|style|click|linkStyle|subgraph|end\b)/.test(line)) continue;
      for (const node of line.matchAll(/\b([A-Za-z_][\w-]*)\[([^\]\n]*)\]/g)) add(node[1], node[2].replace(/^"|"$/g, ""));
      const edge = line.match(/^\s*([A-Za-z_][\w-]*)(?:\[[^\]\n]*\])?\s*(-->|-\.->|==>)(?:\|([^|\n]*)\|)?\s*([A-Za-z_][\w-]*)(?:\[[^\]\n]*\])?\s*;?\s*$/);
      if (!edge) continue;
      const [, from, arrow, label, to] = edge;
      add(from); add(to);
      if (!nodes.has(from) || !nodes.has(to)) continue;
      // Preserve source layout relations unless an explicit dependency decision
      // has replaced them. Tracking can add prerequisites absent from the source.
      const override = active.get(to)?.overrides?.depends_on;
      if (active.has(from) && Array.isArray(override) && !override.includes(from)) continue;
      edges.push({from, to, dotted: arrow === "-.->", label: label || ""});
    }
    if (!nodes.size) continue;
    // Current dependencies supplement topology and explicit edits take priority.
    for (const node of [...nodes.values()]) if (node.feature) {
      covered.add(node.id);
      for (const dependency of node.feature.depends_on || []) if (active.has(dependency)) {
        add(dependency);
        covered.add(dependency);
        edges.push({from: dependency, to: node.id});
      }
    }
    const headings = [...body.slice(0, match.index).matchAll(/^#{1,6}\s+(.+)$/gm)];
    models.push({title: headings.at(-1)?.[1] || `依赖图 ${models.length + 1}`, nodes: [...nodes.values()], edges});
  }
  const tracks = new Map();
  for (const feature of active.values()) if (!covered.has(feature.id)) {
    const track = feature.track || "工作依赖";
    if (!tracks.has(track)) tracks.set(track, []);
    tracks.get(track).push(feature);
  }
  for (const [title, features] of tracks) {
    // Add work absent from source diagrams to its existing track where possible.
    const existing = models.find(model => model.nodes.some(node => node.feature?.track === title));
    const model = existing || {title, nodes: [], edges: []};
    for (const feature of features) {
      if (!model.nodes.some(node => node.id === feature.id)) model.nodes.push({id: feature.id, title: `${feature.id} ${feature.title}`, feature});
      for (const dependency of feature.depends_on || []) if (active.has(dependency)) {
        if (!model.nodes.some(node => node.id === dependency)) model.nodes.push({id: dependency, title: active.get(dependency).title, feature: active.get(dependency)});
        model.edges.push({from: dependency, to: feature.id});
      }
    }
    if (!existing) models.push(model);
  }
  return models;
}

export function graphSource(model, label) {
  const ids = new Map(model.nodes.map((node, index) => [node.id, `N${index}`]));
  const escape = text => String(text).replace(/&/g, "#amp;").replace(/"/g, "#quot;").replace(/</g, "#lt;").replace(/>/g, "#gt;").replace(/[\r\n]/g, " ");
  const lines = ["flowchart LR"];
  for (const node of model.nodes) {
    const feature = node.feature;
    const state = feature?.complete ? "accepted" : (feature?.implementation || feature?.state || "context");
    const style = ["accepted", "implemented", "partial", "in_progress", "blocked"].includes(state) ? state : feature ? "planned" : "context";
    const detail = feature ? `<br/>${escape(label(state))} · 验收：${escape(label(feature.acceptance || "pending"))}${feature.owner ? `<br/>负责人：${escape(feature.owner)}` : ""}` : "";
    lines.push(`${ids.get(node.id)}["${escape(node.title)}${detail}"]:::${style}`);
  }
  const seen = new Set();
  for (const edge of model.edges) {
    if (!ids.has(edge.from) || !ids.has(edge.to)) continue;
    const key = `${edge.from}\0${edge.to}`;
    if (seen.has(key)) continue;
    seen.add(key);
    lines.push(`${ids.get(edge.from)} ${edge.dotted ? "-.->" : "-->"}${edge.label ? `|"${escape(edge.label)}"|` : ""} ${ids.get(edge.to)}`);
  }
  return lines.join("\n");
}
