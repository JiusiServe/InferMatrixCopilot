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
  return collapseGroups(models, active, rfc.node_groups || []);
}

function aggregateGroup(group, members, groupByFeature) {
  const counts = {total: members.length, implemented: 0, accepted: 0, partial: 0,
    in_progress: 0, blocked: 0, planned: 0};
  for (const feature of members) {
    const state = feature.complete ? "implemented" : feature.implementation || feature.state || "planned";
    if (Object.hasOwn(counts, state) && state !== "total" && state !== "accepted") counts[state]++;
    else counts.planned++;
    if (feature.complete === true) counts.accepted++;
  }
  const complete = counts.accepted === counts.total;
  const implementation = counts.implemented === counts.total ? "implemented"
    : counts.implemented || counts.partial ? "partial"
    : counts.blocked ? "blocked" : counts.in_progress ? "in_progress" : "planned";
  const acceptance = complete ? "accepted"
    : members.some(feature => feature.acceptance === "failing") ? "failing" : "pending";
  const memberIds = new Set(members.map(feature => feature.id));
  const externalIds = key => [...new Set(members.flatMap(feature => feature[key] || [])
    .filter(id => !memberIds.has(id)).map(id => groupByFeature.get(id)?.id || id))];
  const shared = key => members.every(feature => feature[key] === members[0][key]) ? members[0][key] || "" : "";
  const feature = {id: group.id, title: group.title, implementation, acceptance, complete,
    counts, owner: shared("owner"), track: shared("track"), depends_on: externalIds("depends_on"),
    blockers: externalIds("blockers"), links: [...new Set(members.flatMap(feature => feature.links || []))]};
  return {id: group.id, title: `${group.title} (${members.length})`, group, members, counts, feature};
}

function collapseGroups(models, active, requested) {
  if (!Array.isArray(requested) || !requested.length) return models;
  const groupByFeature = new Map(), groups = new Map();
  const existingIds = new Set(models.flatMap(model => model.nodes.map(node => node.id)));
  for (const value of requested) {
    if (!value || typeof value.id !== "string" || !value.id || !Array.isArray(value.feature_ids)
        || groups.has(value.id) || existingIds.has(value.id)) continue;
    const ids = [...new Set(value.feature_ids)].filter(id => active.has(id));
    // Missing/deleted members cannot conceal active work. A single remaining
    // feature keeps its original node and operations; overlapping malformed
    // groups are ignored rather than arbitrarily hiding somebody's tasks.
    if (ids.length < 2 || ids.some(id => groupByFeature.has(id))) continue;
    const group = {...value, title: String(value.title || value.id), feature_ids: [...value.feature_ids]};
    groups.set(group.id, group);
    for (const id of ids) groupByFeature.set(id, group);
  }
  if (!groups.size) return models;
  // A group may cross several source diagrams and tracks. Join every affected
  // graph before replacing members, retaining each diagram's context/edges.
  const parents = models.map((_, index) => index);
  const root = index => parents[index] === index ? index : (parents[index] = root(parents[index]));
  for (const group of groups.values()) {
    const indices = models.flatMap((model, index) => model.nodes.some(node => groupByFeature.get(node.id)?.id === group.id) ? [index] : []);
    for (const index of indices.slice(1)) parents[root(index)] = root(indices[0]);
  }
  const components = new Map();
  models.forEach((model, index) => {
    const key = root(index);
    if (!components.has(key)) components.set(key, []);
    components.get(key).push(model);
  });
  const aggregate = new Map([...groups].map(([id, group]) => [id,
    aggregateGroup(group, [...active.values()].filter(feature => groupByFeature.get(feature.id)?.id === id), groupByFeature)]));
  return [...components.values()].map(component => {
    const nodes = new Map(), edges = [], seenEdges = new Set();
    for (const model of component) for (const node of model.nodes) {
      const group = groupByFeature.get(node.id);
      const replacement = group ? aggregate.get(group.id) : node;
      if (!nodes.has(replacement.id)) nodes.set(replacement.id, replacement);
    }
    for (const model of component) for (const edge of model.edges) {
      const from = groupByFeature.get(edge.from)?.id || edge.from;
      const to = groupByFeature.get(edge.to)?.id || edge.to;
      const key = JSON.stringify([from, to]);
      if (from === to || !nodes.has(from) || !nodes.has(to) || seenEdges.has(key)) continue;
      seenEdges.add(key); edges.push({...edge, from, to});
    }
    return {title: [...new Set(component.map(model => model.title))].join(" / "), nodes: [...nodes.values()], edges};
  });
}

export function graphSource(model, label, layoutOnly = false) {
  const ids = new Map(model.nodes.map((node, index) => [node.id, `N${index}`]));
  const entities = {"&": "#amp;", '"': "#quot;", "<": "#lt;", ">": "#gt;", "\\": "#92;", "#": "#35;"};
  const escape = text => String(text).replace(/[&"<>\\#]/g, char => entities[char])
    .replace(/[\x00-\x1f\x7f\u2028\u2029]/g, " ");
  const lines = ["flowchart LR"];
  for (const node of model.nodes) {
    const feature = node.feature;
    const state = feature?.complete ? "accepted" : (feature?.implementation || feature?.state || "context");
    const style = ["accepted", "implemented", "partial", "in_progress", "blocked"].includes(state) ? state : feature ? "planned" : "context";
    const counts = node.group && feature?.counts;
    const summary = counts ? `<br/>实现 ${counts.implemented}/${counts.total} · 验收 ${counts.accepted}/${counts.total}` : "";
    const detail = feature ? (layoutOnly ? "<br/>实现进度待更新 · 验收结果待确认<br/>负责人：等待工作认领" : `<br/>${escape(label(state))} · 验收：${escape(label(feature.acceptance || "pending"))}${summary}${feature.owner ? `<br/>负责人：${escape(feature.owner)}` : ""}`) : "";
    lines.push(`${ids.get(node.id)}["${escape(node.title)}${detail}"]:::${layoutOnly && feature ? "planned" : style}`);
  }
  const seen = new Set();
  for (const edge of model.edges) {
    if (!ids.has(edge.from) || !ids.has(edge.to)) continue;
    const key = JSON.stringify([edge.from, edge.to]);
    if (seen.has(key)) continue;
    seen.add(key);
    lines.push(`${ids.get(edge.from)} ${edge.dotted ? "-.->" : "-->"}${edge.label ? `|"${escape(edge.label)}"|` : ""} ${ids.get(edge.to)}`);
  }
  return lines.join("\n");
}
