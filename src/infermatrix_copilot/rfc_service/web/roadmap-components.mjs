import {displayMarkdown} from "./roadmap-markdown-display.mjs";

/* Classification is a display projection; it never changes the source or tracking model. */
export const sectionRules = [
  {category: "supplement", claim: "historical", pattern: /histor(?:y|ical)|timeline|(?:delivery|release|status|progress)\s+(?:snapshot|update)|live\s+pr\s+status|delivery\s+and\s+next\s+steps|(?:执行|交付|发布)顺序|历史|时间线|快照|交付进展|当前\s*pr\s*状态/i},
  {category: "scope", pattern: /non[ -]?goals?|out[ -]of[ -]scope|scope|非目标|不(?:在|包括|包含).*范围|范围|边界/i},
  {category: "goals", pattern: /(?:^|\b)(?:goals?|objectives?|expected\s+outcomes?)(?:\b|$)|目标|预期成果|期望结果/i},
  {category: "risks", pattern: /risks?|open\s+(?:questions?|issues?)|unresolved|feedback\s+period|风险|未决|开放问题|反馈期/i},
  {category: "references", pattern: /related\s+work|references?|resources?|bibliography|参考|相关工作|相关资料/i},
  {category: "acceptance", pattern: /acceptance|success\s+criteria|validation\s+criteria|验收|成功标准/i},
  {category: "design", claim: "source", pattern: /performance|benchmark|measurement|estimat(?:e|ion)|measured|experiment\s+plan|性能|测量|估算|基准|实验计划/i},
  {category: "design", pattern: /design|architectur|alternatives?|models?|execution\s+semantics|(?:proposed\s+)?solution|approach|implementation\s+details|pr\s+review\s+contract|事实与依据|备选|方案|设计|模型|架构|执行语义|评审契约/i},
  {category: "overview", pattern: /(?:^|\b)(?:topic|summary|overview|motivation|background|problem)(?:\b|$)|概述|摘要|背景|动机|问题/i},
  {category: "work", pattern: /feature\s+roadmap|(?:implementation|work)\s+plan|工作计划|工作拆分|工作轨道|实现计划|功能路线图/i},
];

const categories = ["overview", "goals", "scope", "design", "risks", "references", "supplement", "acceptance"];

function classification(title, parent, featureHeading = true) {
  if (parent?.featureId) return {category: "work", claim: parent.claim, featureId: parent.featureId};
  const feature = featureHeading && title.match(/^([A-Za-z][A-Za-z0-9_-]*)[.、:]\s+(.+)/);
  if (feature) return {category: "work", claim: "source", featureId: feature[1]};
  // A historical section stays historical even when a child is named "Goals".
  if (parent?.claim === "historical") return {category: "supplement", claim: "historical", featureId: null};
  // Domain headings inside goals or acceptance must not become model/design claims.
  if (["goals", "scope", "risks", "references", "acceptance"].includes(parent?.category)) {
    return {category: parent.category, claim: parent.claim, featureId: null};
  }
  const rule = sectionRules.find(rule => rule.pattern.test(title));
  return {category: rule?.category || parent?.category || "supplement", claim: rule?.claim || parent?.claim || null, featureId: null};
}

function commentLines(lines, tokens) {
  const fenced = new Set();
  for (const token of tokens) if (["fence", "code_block"].includes(token.type) && token.map) {
    for (let line = token.map[0]; line < token.map[1]; line += 1) fenced.add(line);
  }
  const hidden = new Set();
  for (let index = 0; index < lines.length; index += 1) {
    if (fenced.has(index) || !/^ {0,3}(?:\\)?<!--/.test(lines[index])) continue;
    let end = index;
    while (end < lines.length && !lines[end].includes("-->")) end += 1;
    if (end < lines.length && !lines[end].slice(lines[end].indexOf("-->") + 3).trim()) {
      for (let line = index; line <= end; line += 1) hidden.add(line);
      index = end;
    }
  }
  return hidden;
}

/** Project original Markdown into exclusive fragments with 1-based source spans. */
export function projectRFC(body, markdownParser) {
  const source = String(body || ""), lines = source.split(/\r?\n/);
  const tokens = markdownParser.parse(source, {});
  const comments = commentLines(lines, tokens);
  const suppressed = new Set(comments);
  // Match the graph module's source grammar; other diagrams remain readable code.
  for (const token of tokens) if (token.type === "fence" && token.markup[0] === "`" && /^mermaid\s*$/.test(token.info) &&
      /^\s*(?:flowchart|graph)\s+(?:LR|RL|TD|TB|BT)\b/.test(token.content) && token.map) {
    for (let line = token.map[0]; line < token.map[1]; line += 1) suppressed.add(line);
  }
  const headings = [];
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (token.type !== "heading_open" || token.level !== 0 || !token.map || comments.has(token.map[0])) continue;
    const inline = tokens[index + 1];
    const title = (inline.children || []).map(child => child.type === "image" ? child.content : child.content || "").join("").trim();
    headings.push({title, level: Number(token.tag.slice(1)), start: token.map[0], contentStart: token.map[1]});
  }
  const result = Object.fromEntries(categories.map(category => [category, []]));
  result.tree = [];
  result.featureSections = Object.create(null);
  const stack = [];
  const clean = (start, end) => displayMarkdown(lines.slice(start, end).map((line, offset) => suppressed.has(start + offset) ? "" : line).join("\n")).trim();
  const preambleEnd = headings[0]?.start ?? lines.length;
  const preamble = clean(0, preambleEnd);
  if (preamble) {
    const fragment = {id: "section-preamble", title: "概述", level: 0, startLine: 1, endLine: preambleEnd, markdown: preamble, category: "overview", claim: null, featureId: null, parentId: null, children: []};
    result.overview.push(fragment); result.tree.push(fragment);
  }
  headings.forEach((heading, index) => {
    while (stack.length && stack.at(-1).level >= heading.level) stack.pop();
    const parent = stack.at(-1), next = headings[index + 1];
    const assignment = classification(heading.title, parent, heading.level >= 3);
    const fragment = {id: `section-${heading.start + 1}`, title: heading.title, level: heading.level,
      startLine: heading.start + 1, endLine: next?.start ?? lines.length,
      markdown: clean(heading.contentStart, next?.start ?? lines.length),
      ...assignment, parentId: parent?.id || null, children: []};
    if (parent) parent.children.push(fragment); else result.tree.push(fragment);
    stack.push(fragment);
    // Heading containers have no duplicated body; empty containers remain in the tree.
    if (!fragment.markdown) return;
    if (fragment.featureId) {
      (result.featureSections[fragment.featureId] ||= []).push(fragment);
    } else if (fragment.category === "work") {
      result.supplement.push({...fragment, category: "supplement"});
    } else {
      result[fragment.category].push(fragment);
    }
  });
  // Tree spans include descendants while fragment spans remain exclusive.
  const finish = nodes => nodes.forEach(node => {
    finish(node.children);
    node.subtreeEndLine = node.children.at(-1)?.subtreeEndLine ?? node.endLine;
  });
  finish(result.tree);
  return result;
}

function timestamp(value) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = typeof value === "number" || (typeof value === "string" && /^[+-]?\d+(?:\.\d+)?$/.test(value));
  const parsed = numeric ? Number(value) * (Math.abs(Number(value)) < 1e12 ? 1000 : 1) : Date.parse(value);
  return Number.isFinite(parsed) ? parsed : null;
}

const evidenceTimestamp = evidence => timestamp(evidence.recorded_at ?? evidence.verified_at ?? evidence.at);

function currentEvidence(criterion) {
  return (criterion.evidence || []).filter(evidence => evidence && typeof evidence === "object" && !evidence.stale && evidence.revision && evidence.environment)
    .sort((a, b) => (evidenceTimestamp(b) ?? 0) - (evidenceTimestamp(a) ?? 0));
}

/** Outcomes are authorized tracking facts, never performance claims in the prose. */
export function outcomeModel(rfc, projection) {
  const features = (rfc.features || []).filter(feature => !feature.dropped);
  const criteria = rfc.criteria || [];
  const implementation = {total: features.length, implemented: 0, partial: 0, inProgress: 0, blocked: 0, planned: 0};
  for (const feature of features) {
    const state = feature.implementation || feature.state || "planned";
    const key = state === "in_progress" ? "inProgress" : ["implemented", "partial", "blocked"].includes(state) ? state : "planned";
    implementation[key] += 1;
  }
  const acceptance = {total: criteria.length, passed: 0, failed: 0, unverified: 0, waived: 0};
  const verified = [];
  for (const criterion of criteria) {
    const evidence = currentEvidence(criterion);
    const verdict = criterion.verdict;
    if (verdict === "passing" && evidence.length) {
      acceptance.passed += 1;
      verified.push({criterionId: criterion.id, featureId: criterion.feature_ids?.find(id => features.some(feature => feature.id === id)) || null,
        title: criterion.title, evidence: evidence[0], verifiedAt: evidenceTimestamp(evidence[0]) === null ? null : new Date(evidenceTimestamp(evidence[0])).toISOString()});
    } else if (verdict === "failing") acceptance.failed += 1;
    else if (verdict === "waived") acceptance.waived += 1;
    else acceptance.unverified += 1;
  }
  verified.sort((a, b) => (timestamp(b.verifiedAt) ?? 0) - (timestamp(a.verifiedAt) ?? 0));
  const next = [], seen = new Set();
  const add = item => { const key = `${item.kind}:${item.id}`; if (!seen.has(key)) { seen.add(key); next.push(item); } };
  for (const feature of features) if (feature.blockers?.length || (feature.implementation || feature.state) === "blocked") {
    add({kind: "feature", id: feature.id, featureId: feature.id, criterionId: null, title: feature.title,
      reason: feature.blockers?.length ? `等待：${feature.blockers.join("、")}` : "工作被阻塞"});
  }
  for (const criterion of [...criteria].sort((a, b) => Number(b.verdict === "failing") - Number(a.verdict === "failing"))) {
    if (criterion.verdict === "waived" || (criterion.verdict === "passing" && currentEvidence(criterion).length)) continue;
    add({kind: "criterion", id: criterion.id, featureId: criterion.feature_ids?.find(id => features.some(feature => feature.id === id)) || null,
      criterionId: criterion.id, title: criterion.title, reason: criterion.verdict === "failing" ? "验收未通过，需修复并重新验证" : "补充当前版本与环境的验收证据"});
  }
  for (const feature of features) if ((feature.implementation || feature.state) !== "implemented") {
    add({kind: "feature", id: feature.id, featureId: feature.id, criterionId: null, title: feature.title, reason: "推进剩余实现工作"});
  }
  if (!features.length && !criteria.length) add({kind: "work", id: "work", featureId: null, criterionId: null, title: "补充工作拆分与验收标准", reason: "当前 RFC 尚未建立可验证的工作计划"});
  return {goals: projection.goals, implementation, acceptance, verified: verified.slice(0, 3), next: next.slice(0, 3)};
}
