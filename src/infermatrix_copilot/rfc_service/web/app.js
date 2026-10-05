/* Same-origin RFC client. Markdown uses a bundled parser with raw HTML disabled. */
import {graphModels, graphSource, roadmapSVGStyles} from "/roadmap-graph.mjs";
import {displayMarkdown} from "/roadmap-markdown-display.mjs";
import {projectRFC, outcomeModel} from "/roadmap-components.mjs";
import {currentLanguage, localizeText, setTranslations, applyLocale, initializeLocale, changeLanguage} from "/roadmap-locale.mjs";
const markdown = window.markdownit({html: false, linkify: true});
markdown.renderer.rules.image = (tokens, index) => markdown.utils.escapeHtml(tokens[index].content);

function markdownBody(text, sourceUrl = "") {
  const node = document.createElement("article");
  node.className = "markdown-body";
  // Only parser-generated HTML is inserted; source HTML is escaped by markdown-it.
  node.innerHTML = markdown.render(displayMarkdown(text || "暂无正文。"));
  const used = new Set();
  for (const heading of node.querySelectorAll("h1,h2,h3,h4,h5,h6")) {
    const slug = heading.textContent.toLowerCase().replace(/[^\p{L}\p{N}_\s-]/gu, "").replace(/\s/g, "-") || "section";
    let id = slug, suffix = 0;
    while (used.has(id)) id = `${slug}-${++suffix}`;
    used.add(id);
    heading.id = id;
  }
  for (const link of node.querySelectorAll("a")) {
    const href = link.getAttribute("href") || "";
    if (href.startsWith("#")) continue;
    try {
      const url = new URL(href, sourceUrl || location.href);
      if (!["https:", "http:"].includes(url.protocol)) throw new Error("Unsupported link");
      link.href = url.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    } catch { link.replaceWith(document.createTextNode(link.textContent)); }
  }
  return node;
}
const $ = (id) => document.getElementById(id);
const content = $("content");
let principal = null;
let repositories = [];
let routeSequence = 0;
let viewDirty = false;
let selectedTokenUser = "";
let noticeTimer;
let refreshCurrent = null;
const suggestionPages = new Map();
const SUGGESTIONS_PER_PAGE = 50;
let graphSerial = 0;
let mermaidPromise;
let featureDialog = null;
let activeGraphs = null;
let activeRFC = null;
let activeContent = null;
let activeEditor = null;
let busyOperations = 0;

function closeFeatureDialog() {
  if (featureDialog) { featureDialog.close(); featureDialog.remove(); featureDialog = null; }
}
function closeRFCEditor(discard = false) {
  if (!activeEditor) return;
  if (activeEditor.dialog.open) activeEditor.dialog.close();
  if (discard) { activeEditor.dialog.remove(); activeEditor = null; }
}
function rememberGraphViewport() {
  if (!activeGraphs?.wrapper.isConnected) return;
  activeGraphs.viewport = [...activeGraphs.wrapper.querySelectorAll(".roadmap-canvas")].map(canvas => [canvas.scrollLeft, canvas.scrollTop]);
}
function restoreGraphViewport() {
  const graphs = activeGraphs;
  if (!graphs?.viewport) return;
  const restore = () => {
    if (graphs !== activeGraphs || !graphs.wrapper.isConnected) return;
    graphs.wrapper.querySelectorAll(".roadmap-canvas").forEach((canvas, index) => {
      const position = graphs.viewport[index];
      if (position) { canvas.scrollLeft = position[0]; canvas.scrollTop = position[1]; }
    });
  };
  restore(); requestAnimationFrame(restore);
}

function openGraphTarget(graphs) {
  if (!graphs?.wrapper.isConnected || featureDialog) return;
  const target = new URLSearchParams(location.hash.split("?")[1] || "").get("feature");
  if (!target) return;
  for (const model of graphs.models) {
    const node = model.nodes.find(node => node.id === target && node.feature);
    if (node) { graphDetails(graphs.rfc, node, model); return; }
  }
}

function graphDetails(rfc, node, model) {
  closeFeatureDialog();
  const dialog = element("dialog", {class: "graph-details", "aria-label": `${node.title} 的工作详情`});
  featureDialog = dialog;
  const close = button("关闭", () => closeFeatureDialog());
  dialog.append(element("div", {class: "panel-title"}, element("h2", {}, node.title), close));
  if (node.feature) {
    const criteria = (rfc.criteria || []).filter(criterion => {
      const related = criterion.feature_ids || criterion.features || (criterion.feature_id ? [criterion.feature_id] : []);
      return !related.length || related.includes(node.id);
    });
    dialog.append(workPanel({...rfc, features: [node.feature]}, false), criteriaPanel({...rfc, criteria}));
  } else {
    dialog.append(element("p", {class: "muted"}, "这是路线图中的目标或上下文节点。选择关联工作以查看 PR、负责人和验收，或推进下一步。"));
    const neighbors = new Set(model.edges.filter(edge => edge.from === node.id || edge.to === node.id).flatMap(edge => [edge.from, edge.to]));
    const related = model.nodes.filter(candidate => candidate.feature && neighbors.has(candidate.id));
    for (const candidate of related) dialog.append(button(`${candidate.id} · ${candidate.feature.title}`, () => graphDetails(rfc, candidate, model)));
    if (!related.length) dialog.append(button("查看全部工作", () => {
      closeFeatureDialog();
      content.querySelector(".work-item")?.scrollIntoView({behavior: "smooth", block: "center"});
    }));
  }
  dialog.addEventListener("close", () => { dialog.remove(); if (featureDialog === dialog) featureDialog = null; });
  document.body.append(dialog);
  dialog.showModal();
  close.focus();
}
const labels = {
  draft: "草稿", proposed: "待评审", discussion: "讨论中", accepted: "已接受", rejected: "已拒绝",
  superseded: "已取代", planned: "待开始", ready: "就绪", active: "进行中", in_progress: "进行中",
  partial: "部分实现", partially_implemented: "部分实现", blocked: "受阻", review: "评审中",
  in_review: "评审中", merged: "已合并", implemented: "实现已落地", validating: "待验证", complete: "已完成",
  completed: "已完成", done: "已完成", dropped: "已移除", cancelled: "已取消", unknown: "未知",
  unverified: "未验证", pending: "待处理", passing: "通过", passed: "通过", failing: "未通过", failed: "失败",
  waived: "已豁免", stale: "需刷新", fresh: "已更新", current: "已更新", outcome_unknown: "结果待核对",
  running: "执行中", applied: "已应用", succeeded: "成功", uncertain: "结果待核对", enrolled: "已纳管",
  valid_token: "有效", revoked: "已撤销", expired: "已过期",
  reader: "可查看", contributor: "可贡献", maintainer: "可维护", local: "本地 Markdown",
  github: "GitHub", atomgit: "AtomGit", none: "无", not_started: "尚未开始", not_enrolled: "未纳管",
};

function element(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else if (value !== undefined && value !== null) node.setAttribute(key, String(value));
  }
  for (const child of children.flat()) {
    if (child === undefined || child === null) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}
function statusValue(value) {
  if (value && typeof value === "object") return value.state || value.status || value.verdict || "unknown";
  return value || "unknown";
}
function translated(value) { const state = statusValue(value); return labels[state] || String(state); }
function badge(value) {
  const state = statusValue(value);
  const color = ["valid_token", "passing", "passed", "accepted", "applied", "succeeded", "fresh", "current", "merged"].includes(state) ? "green"
    : ["failed", "failing", "rejected", "error"].includes(state) ? "red"
    : ["blocked", "partial", "validating", "stale", "outcome_unknown", "unverified"].includes(state) ? "amber"
    : ["active", "in_progress", "running", "discussion", "review"].includes(state) ? "blue" : "";
  return element("span", {class: `badge ${color}`}, translated(state));
}
function readable(value) {
  if (value === undefined || value === null || value === "") return "—";
  return typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
}
function dateText(value) {
  if (!value) return "尚未同步";
  const date = new Date(typeof value === "number" ? value * 1000 : value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString(currentLanguage() === "en" ? "en-US" : "zh-CN", {hour12: false});
}
function notice(message, error = false) {
  clearTimeout(noticeTimer);
  $("notice").textContent = message;
  $("notice").className = `notice${error ? " error" : ""}`;
  $("notice").hidden = false;
  noticeTimer = setTimeout(() => { $("notice").hidden = true; }, error ? 9000 : 5000);
}
function signedOut() {
  closeFeatureDialog();
  closeRFCEditor(true);
  activeGraphs = null;
  activeRFC = null;
  activeContent = null;
  setTranslations(null);
  activeEditor = null;
  principal = null;
  repositories = [];
  selectedTokenUser = "";
  routeSequence += 1;
  refreshCurrent = null;
  suggestionPages.clear();
  content.replaceChildren();
  $("identity-name").textContent = "";
  $("issued-secret").value = "";
  if ($("secret-dialog").open) $("secret-dialog").close();
  $("app").hidden = true;
  $("login").hidden = false;
}
async function api(path, options = {}) {
  const response = await fetch(path, {credentials: "same-origin", cache: "no-store", ...options,
    headers: {"Accept": "application/json", ...(options.body ? {"Content-Type": "application/json"} : {}), ...options.headers}});
  let value;
  try { value = await response.json(); } catch { value = {}; }
  if (!response.ok) {
    if (response.status === 401 && principal) { signedOut(); notice("会话已失效，请重新登录。", true); }
    const error = new Error(value.error?.message || `请求失败（${response.status}）`);
    error.code = value.error?.code;
    throw error;
  }
  return value;
}
const compactActions = new Set(["rfcs.draft", "rfcs.import", "rfcs.update", "rfcs.work", "rfcs.decision", "rfcs.acl"]);
const action = (name, payload = {}) => api(`/api/v1/actions/${encodeURIComponent(name)}`, {method: "POST", body: JSON.stringify({...payload, ...((compactActions.has(name) || name === "rfcs.suggestions") ? {language: currentLanguage()} : {}), ...(compactActions.has(name) ? {view: "detail"} : {})})});
const getRFC = (id) => api(`/api/v1/rfcs/${encodeURIComponent(id)}?view=detail&language=${currentLanguage()}`);
async function applyRFCResult(result) {
  if (!principal || !result?.id || !result.features || !location.hash.startsWith(`#rfc/${encodeURIComponent(result.id)}`)) return route();
  closeFeatureDialog();
  viewDirty = false;
  const scroll = window.scrollY;
  rememberGraphViewport();
  content.replaceChildren(detailView(result));
  viewDirty = Boolean(activeEditor?.dirty);
  window.scrollTo(0, scroll);
  restoreGraphViewport();
}
function formData(form) { return Object.fromEntries(new FormData(form)); }
async function busy(button, callback) {
  busyOperations += 1;
  if (button) button.disabled = true;
  try { return await callback(); } catch (error) { notice(error.message, true); return null; }
  finally { busyOperations -= 1; if (button) button.disabled = false; }
}
function button(text, callback, className = "") {
  return element("button", {type: "button", class: className, onclick: (event) => busy(event.currentTarget, callback)}, text);
}
function select(name, choices, current = "", required = false) {
  const node = element("select", {name, ...(required ? {required: true} : {})});
  for (const choice of choices) {
    const [value, label] = Array.isArray(choice) ? choice : [choice, labels[choice] || choice];
    const option = element("option", {value}, label);
    option.selected = String(value) === String(current);
    node.append(option);
  }
  return node;
}
function input(name, placeholder = "", value = "", type = "text", required = false) {
  return element("input", {name, placeholder, value, type, ...(required ? {required: true} : {})});
}
function field(label, control, help = "", full = false) {
  const id = `field-${field.counter++}`;
  control.id = id;
  return element("div", {class: `field${full ? " full" : ""}`}, element("label", {for: id}, label), control,
    help ? element("p", {class: "help"}, help) : null);
}
field.counter = 0;
function panel(title, children, subtitle = "", actions = null) {
  return element("section", {class: "panel"}, element("div", {class: "panel-title"}, element("h2", {}, title), actions),
    subtitle ? element("p", {class: "panel-subtitle"}, subtitle) : null, children);
}
function heading(title, subtitle, actions = null) {
  return element("div", {class: "page-heading"}, element("div", {}, element("h1", {}, title), element("p", {}, subtitle)), actions);
}
function empty(title, description) { return element("div", {class: "empty"}, element("h3", {}, title), element("p", {}, description)); }
function safeLink(url, label = "查看来源 ↗") {
  try {
    const value = new URL(url);
    if (!["http:", "https:"].includes(value.protocol)) return null;
    return element("a", {href: value.href, target: "_blank", rel: "noopener noreferrer", class: "source-link"}, label);
  } catch { return null; }
}
function repoName(id) { return repositories.find((repo) => repo.id === id)?.name || id || "未指定仓库"; }
function repoChoices() { return repositories.map((repo) => [repo.id, repo.name || repo.id]); }
function canWrite(rfc) { return rfc.can_write ?? (principal.admin || ["contributor", "maintainer"].includes(rfc.role)); }
function canPublish(rfc) { return rfc.can_publish ?? (principal.admin || rfc.role === "maintainer"); }
function trackingLabel(rfc) {
  if (rfc.sync_status === "requires_reauthorization") return "追踪已暂停 · 需重新授权";
  if (rfc.sync_status === "different_writer") return "由其他工作空间维护";
  return rfc.enrolled ? "已纳管，定期刷新实现事实" : "草稿或尚未纳管";
}

async function signedIn(identity) {
  principal = identity;
  $("login").hidden = true;
  $("app").hidden = false;
  $("identity-name").textContent = identity.name || identity.user_id;
  $("admin-nav").hidden = !identity.admin;
  repositories = (await api("/api/v1/repositories")).repositories || [];
  await route();
}
$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  const token = $("login-token").value;
  $("login-token").value = "";
  $("login-error").hidden = true;
  button.disabled = true;
  try {
    const result = await api("/api/v1/session", {method: "POST", body: JSON.stringify({token})});
    await signedIn(result.principal);
  } catch (error) { $("login-error").textContent = error.message; $("login-error").hidden = false; }
  finally { button.disabled = false; }
});
$("logout").addEventListener("click", (event) => busy(event.currentTarget, async () => {
  await api("/api/v1/session", {method: "DELETE"});
  signedOut();
}));
$("close-secret").addEventListener("click", () => { $("issued-secret").value = ""; $("secret-dialog").close(); });
$("secret-dialog").addEventListener("close", () => {
  $("issued-secret").value = "";
  if (principal && ["#account", "#admin"].includes(location.hash)) route();
});
$("copy-secret").addEventListener("click", (event) => busy(event.currentTarget, async () => {
  if (navigator.clipboard) { await navigator.clipboard.writeText($("issued-secret").value); notice("已复制，请妥善保存。"); }
  else { $("issued-secret").select(); notice("请手动复制已选中的令牌。"); }
}));
content.addEventListener("input", () => { viewDirty = true; });
content.addEventListener("change", () => { viewDirty = true; });
window.addEventListener("hashchange", () => route());

async function route() {
  closeFeatureDialog();
  closeRFCEditor();
  if (!principal) return;
  const sequence = ++routeSequence;
  viewDirty = false;
  refreshCurrent = null;
  const hash = (location.hash.slice(1) || "dashboard").split("?")[0];
  const [page, id] = hash.split("/");
  const active = page === "rfc" ? "dashboard" : page === "import" ? "draft" : page;
  for (const link of document.querySelectorAll("[data-nav]")) link.classList.toggle("active", link.dataset.nav === active);
  $("breadcrumb").textContent = `${localizeText("工作空间")} / ${localizeText({dashboard: "进展总览", draft: "创建 RFC", import: "纳管已有 RFC", rfc: "RFC 详情", operations: "操作记录", account: "个人令牌", admin: "团队与权限"}[page] || "进展总览")}`;
  rememberGraphViewport();
  content.replaceChildren(element("div", {class: "loading"}, "正在读取工作空间…"));
  try {
    let view;
    if (page === "draft") view = draftView();
    else if (page === "import") view = importView();
    else if (page === "rfc" && id) view = detailView(await getRFC(decodeURIComponent(id)));
    else if (page === "operations") view = operationsView(await api("/api/v1/operations"));
    else if (page === "account") view = await accountView();
    else if (page === "admin" && principal.admin) view = await adminView();
    else view = dashboardView(await api(`/api/v1/rfcs?view=summary&language=${currentLanguage()}`));
    if (sequence === routeSequence && principal) {
      content.replaceChildren(view);
      applyLocale(content);
      if (page === "rfc") { restoreGraphViewport(); openGraphTarget(activeGraphs); }
    }
  } catch (error) {
    if (sequence === routeSequence && principal) content.replaceChildren(element("div", {class: "error-panel"}, error.message),
      element("div", {class: "actions"}, button("重新读取", route)));
  }
}

function dashboardView(data) {
  const list = data.rfcs || [];
  setTranslations(null);
  for (const rfc of list) setTranslations(rfc.translations, false);
  const wrapper = element("div");
  wrapper.append(heading("每个 RFC，都有下一步", "查看团队的计划、实现进展和等待验证的结果。",
    element("div", {class: "actions"}, button("刷新", route), element("a", {href: "#import", class: "badge blue"}, "纳管已有 RFC"), element("a", {href: "#draft", class: "primary badge"}, "＋ 创建 RFC"))));
  const accepted = list.filter((rfc) => ["accepted", "passed", "passing"].includes(statusValue(rfc.acceptance))).length;
  const validating = list.filter((rfc) => ["validating", "implemented", "merged", "partial"].includes(statusValue(rfc.implementation)) && !["accepted", "passed", "passing"].includes(statusValue(rfc.acceptance))).length;
  wrapper.append(element("div", {class: "stats"}, ...[["可访问 RFC", list.length], ["等待验证", validating], ["已验收", accepted]].map(([name, count]) => element("div", {class: "stat"}, element("span", {}, name), element("strong", {}, count)))));
  const search = input("search", "搜索 RFC 标题或编号");
  const repository = select("repository", [["", "所有可访问仓库"], ...repoChoices()]);
  const count = element("span", {class: "count"});
  const grid = element("div", {class: "rfc-grid"});
  function draw() {
    const matches = list.filter((rfc) => (!repository.value || repository.value === rfc.repo_id)
      && `${rfc.title} ${rfc.id}`.toLowerCase().includes(search.value.toLowerCase()));
    count.textContent = `${matches.length} 个 RFC`;
    grid.replaceChildren(...matches.map((rfc) => {
      const next = Array.isArray(rfc.next_actions) ? rfc.next_actions[0] : rfc.next_actions;
      return element("article", {class: "rfc-card"},
        element("div", {class: "card-meta"}, element("span", {}, repoName(rfc.repo_id)), badge(rfc.state || "draft")),
        element("h3", {}, element("a", {href: `#rfc/${encodeURIComponent(rfc.id)}`}, rfc.title || "未命名 RFC")),
        element("div", {class: "status-row"}, "实现", badge(rfc.implementation || "not_started"), "验收", badge(rfc.acceptance || "unverified")),
        element("p", {class: "small muted"}, next ? readable(next) : rfc.enrolled ? "纳管后按来源持续刷新。" : "预览方案后发布，并启用进展追踪。"),
        element("div", {class: "card-bottom"}, element("span", {}, rfc.enrolled ? trackingLabel(rfc) : "○ 尚未纳管"), element("span", {}, `${rfc.feature_count ?? rfc.features?.length ?? 0} 个工作项`)));
    }));
    if (!matches.length) grid.append(empty(list.length ? "没有匹配的 RFC" : "从第一个 RFC 开始", list.length ? "调整搜索条件或仓库范围。" : "选择一个仓库，写下问题和目标，生成可评审的方案。"));
  }
  search.addEventListener("input", draw);
  repository.addEventListener("change", draw);
  draw();
  wrapper.append(element("div", {class: "toolbar"}, search, repository, count), grid);
  refreshCurrent = () => route();
  return wrapper;
}

function draftView() {
  const wrapper = element("div");
  wrapper.append(heading("先写清问题，再开始推进", "生成草稿、检查方案，然后由你明确发布并纳管。", element("a", {href: "#import"}, "已有 RFC？导入并纳管 →")));
  const eligible = repositories.filter((repo) => principal.admin || ["contributor", "maintainer"].includes(repo.role));
  if (!eligible.length) {
    wrapper.append(empty("还没有可贡献的仓库", principal.admin ? "先在团队与权限中登记仓库，再开始创建 RFC。" : "请管理员为你授予仓库贡献权限。"));
    return wrapper;
  }
  const form = element("form");
  const body = element("textarea", {name: "body", placeholder: "可选：已有 RFC 正文。原始文本会被保留。", rows: 7});
  const submit = element("button", {type: "submit", class: "primary"}, "生成 RFC 草稿");
  form.append(element("div", {class: "form-grid"}, field("目标仓库", select("repo_id", eligible.map((repo) => [repo.id, repo.name]), eligible[0].id, true), "仅显示你有权限贡献的仓库。", true),
    field("RFC 标题", input("title", "例如：为模型服务增加可追踪的验收流程", "", "text", true), "用一句话描述具体变化。", true),
    field("问题与期望结果", element("textarea", {name: "goal", rows: 5, placeholder: "谁遇到了什么问题？完成后应该有哪些可观察的变化？"}), "草稿会保留未知问题，供评审时补充。", true),
    field("自动追踪范围", input("scope", "例如：调度、流式返回、延迟验证"), "自动关联限定在这个范围；模糊关联进入建议列表。", true),
    field("已有正文", body, "支持 Markdown；预览以安全的纯文本展示。", true)), element("div", {class: "actions"}, submit));
  const preview = element("div", {class: "preview-placeholder"}, "你的方案预览会出现在这里。\n先描述问题、目标和范围。");
  const right = panel("方案预览", preview, "草稿保存在工作空间；发布需要你的明确操作。");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    busy(submit, async () => {
      const data = formData(form);
      if (!data.body.trim()) delete data.body;
      const result = await action("rfcs.draft", data);
      preview.replaceChildren();
      preview.className = "stack";
      preview.append(element("h3", {}, result.title), markdownBody(result.body),
        element("div", {class: "status-row"}, badge("draft"), "已保存 · 尚未发布"),
        element("a", {href: `#rfc/${encodeURIComponent(result.id)}`}, "查看完整 RFC，并发布或纳管 →"));
      viewDirty = false;
      notice("RFC 草稿已保存。请检查方案和验收条件。");
    });
  });
  wrapper.append(element("div", {class: "draft-layout"}, panel("描述你的想法", form), right));
  return wrapper;
}

function importView() {
  const wrapper = element("div");
  wrapper.append(heading("保留原文，接入进展追踪", "先读取并预览已有 RFC，再明确纳管。GitHub、AtomGit 和本地 Markdown 均可接入。"));
  const eligible = repositories.filter((repo) => principal.admin || repo.role === "maintainer");
  if (!eligible.length) {
    wrapper.append(empty("需要仓库维护权限", "请管理员为你授予对应仓库的 maintainer 权限。"));
    return wrapper;
  }
  const form = element("form", {class: "stack"});
  const repository = select("repo_id", eligible.map((repo) => [repo.id, repo.name]), eligible[0].id);
  const kind = select("kind", [["issue", "Issue / RFC"], ["pr", "Pull Request"], ["file", "Markdown 文件"]]);
  const identifier = input("identifier", "GitHub 编号或 AtomGit 字符串 ID");
  const path = input("path", "相对仓库根目录的文件路径，例如 doc/RFC.md");
  const url = input("url", "可选：已有 RFC 的 HTTPS 链接");
  const scope = input("scope", "限定自动发现的关键词、功能或标签");
  const auto = element("input", {type: "checkbox", name: "auto_add"}); auto.checked = true;
  const submit = element("button", {type: "submit", class: "primary"}, "读取来源并预览");
  form.append(field("目标仓库", repository), field("来源类型", kind), field("来源编号", identifier), field("来源链接", url), field("本地文件", path), field("追踪范围", scope,
    "原始正文保持完整，进展和关联保存在独立追踪记录中。"), element("label", {class: "check-label"}, auto, "在范围内自动关联明确的实现证据"), submit);
  const preview = element("div", {class: "preview-placeholder"}, "读取已有 RFC 后，在这里核对原始内容。\n预览不会修改来源。");
  let reviewed = null;
  let saved = null;
  function sourceFields() {
    const repo = eligible.find((value) => value.id === repository.value);
    const local = repo.provider === "local";
    if (local) kind.value = "file";
    else if (kind.value === "file") kind.value = "issue";
    kind.disabled = local;
    path.disabled = !local; identifier.disabled = local; url.disabled = local;
  }
  repository.addEventListener("change", sourceFields); sourceFields();
  form.addEventListener("input", () => { reviewed = null; saved = null; preview.replaceChildren("来源或范围已调整，请重新预览。"); preview.className = "preview-placeholder"; });
  form.addEventListener("change", () => { reviewed = null; saved = null; preview.replaceChildren("来源或范围已调整，请重新预览。"); preview.className = "preview-placeholder"; });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    busy(submit, async () => {
      const repo = eligible.find((value) => value.id === repository.value);
      const source = {provider: repo.provider, repository: repo.external_name || repo.name, kind: kind.value};
      if (repo.provider === "local") source.path = path.value.trim();
      else {
        source.identifier = identifier.value.trim();
        if (url.value.trim()) {
          let parsed;
          try { parsed = new URL(url.value.trim()); } catch { throw new Error("请输入完整的 HTTPS 来源链接。"); }
          if (parsed.protocol !== "https:") throw new Error("来源链接需要使用 HTTPS。");
          source.url = parsed.href; source.host = parsed.hostname;
          if (!source.identifier) source.identifier = decodeURIComponent(parsed.pathname.split("/").filter(Boolean).at(-1) || "");
        }
      }
      reviewed = await action("sources.preview", {repo_id: repo.id, source});
      const enroll = button("明确纳管这个 RFC", async () => {
        if (!reviewed) throw new Error("来源已调整，请重新预览。");
        if (!confirm("确认纳管当前预览的 RFC，并按指定范围追踪实现进展？")) return;
        if (!saved) saved = await action("rfcs.draft", {repo_id: repo.id, title: reviewed.title || "导入的 RFC", body: reviewed.body, source: reviewed.source,
          scope: scope.value, auto_add: auto.checked});
        await operationNotice(await action("rfcs.enroll", {rfc_id: saved.id, content_digest: saved.content_digest, expected_revision: saved.revision,
          idempotency_key: crypto.randomUUID()}));
        location.hash = `rfc/${encodeURIComponent(saved.id)}`;
      }, "primary");
      preview.className = "stack";
      preview.replaceChildren(...[element("h3", {}, reviewed.title || "已有 RFC"), safeLink(reviewed.source?.url), markdownBody(reviewed.body, reviewed.source?.url),
        element("p", {class: "small muted"}, "纳管前会再次核对来源，期间发生的修改需要重新预览。"), enroll].filter(Boolean));
    });
  });
  wrapper.append(element("div", {class: "draft-layout"}, panel("选择已有来源", form), panel("原文预览", preview)));
  return wrapper;
}

async function operationNotice(result) {
  const operation = result.operation || result;
  const id = result.operation_id || operation.id;
  if (!id) { notice("操作已完成。"); return; }
  notice(`操作已进入队列：${id}。可在操作记录中查看结果。`);
}
function graphTooltip(feature) {
  return `${localizeText(feature.title)}\n${localizeText("实现")}：${localizeText(translated(feature.implementation || feature.state))}\n${localizeText("验收")}：${localizeText(translated(feature.acceptance))}\n${localizeText("负责人")}：${feature.owner || localizeText("待认领")}`;
}
function updateGraphNodes(graphs) {
  for (const entry of graphs.entries) {
    const model = graphs.models[entry.index];
    model.nodes.forEach((node, index) => {
      const group = entry.groups[index];
      if (!group || !node.feature) return;
      const feature = node.feature;
      const state = feature.complete ? "accepted" : feature.implementation || feature.state || "planned";
      const signature = JSON.stringify([feature.title, state, feature.acceptance, feature.owner]);
      if (group.getAttribute("data-live-view") === signature) return;
      group.setAttribute("data-live-view", signature);
      group.classList.remove("planned", "accepted", "implemented", "partial", "in_progress", "blocked");
      group.classList.add(["accepted", "implemented", "partial", "in_progress", "blocked"].includes(state) ? state : "planned");
      for (const span of group.querySelectorAll("text .text-outer-tspan")) {
        if (span.textContent.includes("实现进度待更新")) span.setAttribute("data-graph-meta", "state");
        if (span.textContent.includes("负责人：等待工作认领")) span.setAttribute("data-graph-meta", "owner");
        if (span.getAttribute("data-graph-meta") === "state") span.textContent = `${localizeText(state === "accepted" ? "已验收" : translated(state))} · ${localizeText("验收")}：${localizeText(translated(feature.acceptance || "pending"))}`;
        if (span.getAttribute("data-graph-meta") === "owner") {
          const owner = feature.owner || "待认领";
          span.textContent = `${localizeText("负责人")}：${feature.owner || localizeText("待认领")}`;
          const width = owner.length > 20 ? (group.querySelector("rect")?.getBBox().width || 300) : Infinity;
          while (owner.length > 20 && span.getComputedTextLength() > width - 26 && span.textContent.length > 8) span.textContent = span.textContent.slice(0, -2) + "…";
        }
      }
      group.querySelector("title").textContent = graphTooltip(feature);
    });
  }
}
function enableGraphPanning(canvas) {
  let drag = null;
  canvas.addEventListener("pointerdown", event => {
    if (!event.isPrimary || event.button !== 0 || event.target.closest(".roadmap-actionable,a,button")) return;
    drag = {id: event.pointerId, x: event.clientX, y: event.clientY, left: canvas.scrollLeft, top: canvas.scrollTop};
    canvas.setPointerCapture(event.pointerId);
    canvas.classList.add("is-panning");
    event.preventDefault();
  });
  canvas.addEventListener("pointermove", event => {
    if (!drag || drag.id !== event.pointerId) return;
    canvas.scrollLeft = drag.left + drag.x - event.clientX;
    canvas.scrollTop = drag.top + drag.y - event.clientY;
    event.preventDefault();
  });
  const stop = event => {
    if (!drag || drag.id !== event.pointerId) return;
    drag = null;
    canvas.classList.remove("is-panning");
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
  };
  for (const type of ["pointerup", "pointercancel", "lostpointercapture"]) canvas.addEventListener(type, stop);
}
function dependencyGraph(rfc) {
  const models = graphModels(rfc);
  for (const model of models) {
    model.title = localizeText(model.title);
    for (const node of model.nodes) node.title = localizeText(node.title);
    for (const edge of model.edges) edge.label = localizeText(edge.label || "");
  }
  const sources = models.map(model => graphSource(model, translated, true));
  const signature = JSON.stringify(models.map((model, index) => [model.title, sources[index]]));
  if (activeGraphs?.rfc.id === rfc.id && activeGraphs.signature === signature && activeGraphs.entries.length === models.length) {
    activeGraphs.rfc = rfc;
    activeGraphs.models = models;
    updateGraphNodes(activeGraphs);
    return activeGraphs.wrapper;
  }
  if (!models.length) return empty("没有依赖关系", "添加工作项后，依赖图会自动生成。");
  const wrapper = element("div", {class: "roadmap-graphs"});
  const graphs = {rfc, models, signature, wrapper, entries: []};
  activeGraphs = graphs;
  for (const [modelIndex, model] of models.entries()) {
    const canvas = element("div", {class: "graph roadmap-canvas"}, element("p", {class: "muted"}, "正在绘制路线图…"));
    canvas.setAttribute("tabindex", "0");
    canvas.setAttribute("aria-label", `${model.title}：拖动空白区域平移，点击节点查看详情`);
    enableGraphPanning(canvas);
    const controls = element("div", {class: "actions"});
    const legend = element("div", {class: "graph-legend"}, ...["planned", "in_progress", "partial", "implemented", "accepted"].map(state => element("span", {class: `graph-key ${state}`}, state === "accepted" ? "已验收" : translated(state))));
    const section = element("section", {class: "roadmap-track"}, element("div", {class: "panel-title"}, element("h3", {}, model.title), controls), legend, canvas);
    wrapper.append(section);
    if (!mermaidPromise) mermaidPromise = import("/roadmap-mermaid.js").then(({default: mermaid}) => {
      mermaid.initialize({startOnLoad: false, securityLevel: "strict", theme: "base", htmlLabels: false, suppressErrorRendering: true,
        flowchart: {htmlLabels: false, useMaxWidth: false, wrappingWidth: 320}, themeVariables: {fontFamily: "system-ui,sans-serif", fontSize: "15px", lineColor: "#94a3b8"}});
      return mermaid;
    }).catch(error => { mermaidPromise = null; throw error; });
    const serial = ++graphSerial;
    mermaidPromise.then(async mermaid => {
      if (!canvas.isConnected) return;
      const {svg} = await mermaid.render(`rfc-graph-${serial}`, sources[modelIndex]);
      if (!canvas.isConnected) return;
      const parsed = new DOMParser().parseFromString(svg, "text/html");
      const drawing = document.importNode(parsed.querySelector("svg"), true);
      // All styling is in our same-origin stylesheet, preserving the strict CSP.
      drawing.querySelectorAll("style,script,foreignObject").forEach(node => node.remove());
      for (const node of [drawing, ...drawing.querySelectorAll("*")]) {
        node.removeAttribute("style");
        for (const attribute of [...node.attributes]) if (attribute.name.toLowerCase().startsWith("on")) node.removeAttribute(attribute.name);
      }
      drawing.setAttribute("role", "group");
      drawing.setAttribute("aria-label", `${model.title}：点击工作节点查看详情和操作`);
      const width = drawing.viewBox.baseVal.width;
      let scale = 1;
      drawing.setAttribute("width", String(width));
      drawing.removeAttribute("height");
      canvas.replaceChildren(drawing);
      const groups = [];
      model.nodes.forEach((node, index) => {
        const group = [...drawing.querySelectorAll("g.node")].find(candidate => candidate.id.startsWith(`flowchart-N${index}-`));
        if (!group) return;
        groups[index] = group;
        group.setAttribute("role", "button");
        group.setAttribute("tabindex", "0");
        group.setAttribute("data-feature-id", node.feature ? node.id : "");
        group.setAttribute("aria-label", `${node.title}：${localizeText("查看")}${localizeText(node.feature ? "工作详情、关联 PR 和可用操作" : "关联工作")}`);
        group.classList.add("roadmap-actionable");
        const open = event => { event.preventDefault(); const current = graphs.models[modelIndex]; graphDetails(graphs.rfc, current.nodes[index], current); };
        group.addEventListener("click", open);
        group.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") open(event); });
        const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
        title.textContent = node.feature ? graphTooltip(node.feature) : node.title;
        group.prepend(title);
      });
      graphs.entries.push({index: modelIndex, groups});
      updateGraphNodes(graphs);
      const zoom = delta => { scale = Math.max(.4, Math.min(2.5, scale + delta)); drawing.setAttribute("width", String(width * scale)); };
      const minus = button("−", () => zoom(-.2)); minus.setAttribute("aria-label", `${model.title} 缩小`);
      const plus = button("＋", () => zoom(.2)); plus.setAttribute("aria-label", `${model.title} 放大`);
      controls.append(minus, plus, button("重置", () => { scale = 1; drawing.setAttribute("width", String(width)); canvas.scrollLeft = canvas.scrollTop = 0; }), button("下载 SVG", () => {
        const exported = drawing.cloneNode(true);
        const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
        style.textContent = roadmapSVGStyles;
        exported.prepend(style);
        // The downloaded artifact links to authorized tasks instead of inert callbacks.
        for (const group of exported.querySelectorAll("[data-feature-id]")) {
          const id = group.getAttribute("data-feature-id");
          group.removeAttribute("tabindex");
          if (!id) continue;
          const anchor = document.createElementNS("http://www.w3.org/2000/svg", "a");
          anchor.setAttribute("href", `${location.origin}/roadmap#rfc/${encodeURIComponent(graphs.rfc.id)}?feature=${encodeURIComponent(id)}`);
          anchor.setAttribute("target", "_blank");
          group.replaceWith(anchor); anchor.append(group);
        }
        const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(exported)], {type: "image/svg+xml"}));
        const anchor = element("a", {href: url, download: `${rfc.namespace || rfc.id}-${serial}.svg`});
        anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      }));
      const target = new URLSearchParams(location.hash.split("?")[1] || "").get("feature");
      if (target && !featureDialog) {
        const node = model.nodes.find(node => node.id === target && node.feature);
        if (node) graphDetails(rfc, node, model);
      }
    }).catch(error => {
      if (!canvas.isConnected) return;
      canvas.replaceChildren(element("p", {class: "error-panel"}, `图表暂时无法绘制：${error.message}。下方工作列表仍可操作。`));
    });
  }
  return wrapper;
}

function rfcContent(rfc) {
  const key = JSON.stringify([rfc.id, rfc.body, rfc.source?.url]);
  if (activeContent?.key !== key) {
    const projection = projectRFC(rfc.body || "", markdown);
    const sections = new Map();
    const visit = nodes => { for (const node of nodes) { sections.set(node.id, node); visit(node.children || []); } };
    visit(projection.tree);
    activeContent = {key, projection, sections, nodes: new Map()};
  }
  return activeContent;
}

function sourceSection(rfc, section, lazy = false, namespace = "page") {
  const cache = rfcContent(rfc);
  const key = `${namespace}:${section.id}:${lazy}`;
  if (cache.nodes.has(key)) return cache.nodes.get(key);
  const note = section.claim === "historical" ? "历史记录 · 来源陈述" : section.claim === "source" ? "来源陈述 · 验证结论见验收记录" : "";
  const holder = element(lazy ? "details" : "section", {class: "source-section", "data-source-section": section.id, "data-source-start": section.startLine, "data-source-end": section.endLine});
  const parent = cache.sections.get(section.parentId);
  holder.append(element(lazy ? "summary" : "h3", {}, section.title || "说明", note ? element("span", {class: "badge amber"}, note) : null));
  if (parent && parent.level > 1) holder.append(element("span", {class: "source-context small muted"}, parent.title));
  const draw = () => {
    if (holder.querySelector(".rfc-component-body")) return;
    const body = element("div", {class: "rfc-component-body"}, markdownBody(section.markdown, rfc.source?.url));
    holder.append(body);
  };
  if (lazy) holder.addEventListener("toggle", () => { if (holder.open) draw(); });
  else draw();
  cache.nodes.set(key, holder);
  return holder;
}

function componentSections(rfc, sections, placeholder, lazy = false, namespace = "page") {
  const wrapper = element("div", {class: "component-sections"});
  const nonempty = (sections || []).filter(section => section.markdown?.trim());
  for (const section of nonempty) wrapper.append(sourceSection(rfc, section, lazy || section.markdown.length > 1800, namespace));
  if (!nonempty.length) wrapper.append(element("p", {class: "muted small"}, placeholder));
  return wrapper;
}

function locateRFCItem(kind, id) {
  const attribute = kind === "criterion" ? "data-criterion-id" : "data-feature-id";
  const target = id ? content.querySelector(`${kind === "criterion" ? ".criterion" : ".work-item"}[${attribute}="${CSS.escape(id)}"]`) : null;
  const node = target || content.querySelector(kind === "criterion" ? "#rfc-acceptance" : "#rfc-work");
  node?.scrollIntoView({behavior: "smooth", block: "center"});
  if (node) { node.setAttribute("tabindex", "-1"); node.focus({preventScroll: true}); }
}

function outcomePanel(rfc, projection) {
  const outcome = outcomeModel(rfc, projection);
  const goalList = element("ul", {class: "outcome-goals"});
  const goalText = (outcome.goals || []).flatMap(section => markdown.parse(displayMarkdown(section.markdown || ""), {}).filter(token => token.type === "inline").map(token => token.children?.map(child => child.content).join("") || token.content)).filter(Boolean);
  for (const goal of goalText.slice(0, 3)) {
    const localized = localizeText(goal);
    goalList.append(element("li", {}, button(localized.length > 220 ? localized.slice(0, 219) + "…" : localized, () => content.querySelector("#rfc-goals")?.scrollIntoView({behavior: "smooth"}), "text-action")));
  }
  if (!goalList.children.length) goalList.append(element("li", {class: "muted"}, "尚未声明明确目标，请在 RFC 中补充。"));
  const counts = element("div", {class: "outcome-counts"},
    element("div", {}, element("label", {}, "实现已落地"), element("strong", {}, `${outcome.implementation.implemented} / ${outcome.implementation.total}`), element("p", {class: "small muted"}, "合并和实现记录，验收单独确认。")),
    element("div", {}, element("label", {}, "验收通过"), element("strong", {}, `${outcome.acceptance.passed} / ${outcome.acceptance.total}`), element("p", {class: "small muted"}, `${outcome.acceptance.failed} 项未通过 · ${outcome.acceptance.waived} 项已豁免`)));
  const verified = element("div", {class: "outcome-evidence"});
  for (const item of outcome.verified) verified.append(element("article", {}, button(item.title, () => locateRFCItem("criterion", item.criterionId), "text-action"), evidenceLines(item.evidence),
    element("p", {class: "small muted"}, `版本 ${item.evidence.revision} · ${item.evidence.environment} · ${dateText(item.verifiedAt)}`)));
  if (!outcome.verified.length) verified.append(element("p", {class: "small muted"}, "暂无带有效验证证据的已验收成果。"));
  const next = element("div", {class: "outcome-next"});
  for (const item of outcome.next) {
    const control = button(item.title, () => locateRFCItem(item.criterionId ? "criterion" : "feature", item.criterionId || item.featureId || item.id), "text-action");
    if (item.reason) control.append(" · ", element("span", {}, item.reason));
    next.append(control);
  }
  if (!outcome.next.length) next.append(element("p", {class: "small muted"}, rfc.complete ? "当前工作与验收均已完成。" : "补充可跟踪的工作和验收条件。"));
  const result = panel("成果（Outcome）", element("div", {class: "outcome-grid"},
    element("div", {}, element("h3", {}, "预期目标"), goalList), element("div", {}, element("h3", {}, "实际进展"), counts),
    element("div", {}, element("h3", {}, "最近验证成果"), verified), element("div", {}, element("h3", {}, "未达标项与下一步"), next)),
    "目标来自 RFC；实际成果依据当前实现记录与验证证据。", element("div", {class: "status-row"}, badge(rfc.state), badge(rfc.implementation), badge(rfc.acceptance)));
  result.id = "rfc-outcome"; result.classList.add("rfc-outcome");
  return result;
}

function openRFCEditor(rfc) {
  if (!canWrite(rfc) || (rfc.enrolled && !canPublish(rfc))) return;
  if (activeEditor && (activeEditor.id !== rfc.id || (!activeEditor.dirty && (activeEditor.body !== rfc.body || activeEditor.title !== rfc.title)))) closeRFCEditor(true);
  if (!activeEditor) {
    const dialog = element("dialog", {class: "rfc-editor", "aria-label": "编辑 RFC"});
    const form = element("form", {class: "stack"});
    const saveError = element("p", {class: "form-error", role: "alert", hidden: true});
    form.append(field("标题", input("title", "RFC 标题", rfc.title || "", "text", true)), field("RFC 正文", element("textarea", {name: "body", rows: 18}, rfc.body || "")),
      field("修改原因", input("reason", "说明方案变更及需要重新验证的部分", "", "text", rfc.enrolled)), saveError, element("button", {type: "submit", class: "primary"}, "保存新版本"));
    const state = {id: rfc.id, body: rfc.body, title: rfc.title, revision: rfc.revision, dirty: false, dialog};
    activeEditor = state;
    dialog.append(element("div", {class: "panel-title"}, element("h2", {}, "编辑 RFC"), button("关闭编辑器", () => dialog.close())), element("p", {class: "small muted"}, "编辑保留完整源文档；页面展示由其内容组件生成。关闭窗口会保留未提交输入。"), form);
    const markDirty = () => { state.dirty = true; viewDirty = true; };
    form.addEventListener("input", markDirty); form.addEventListener("change", markDirty);
    form.addEventListener("submit", event => {
      event.preventDefault();
      busy(form.querySelector("button[type=submit]"), async () => {
        const current = activeRFC?.id === state.id ? activeRFC : rfc;
        const revision = current.body === state.body && current.title === state.title ? current.revision : state.revision;
        saveError.hidden = true;
        let result;
        try { result = await action("rfcs.update", {...formData(form), rfc_id: state.id, expected_revision: revision}); }
        catch (error) { saveError.textContent = error.message; saveError.hidden = false; throw error; }
        state.dirty = false; closeRFCEditor(true); notice("新版本已保存。"); await applyRFCResult(result);
      });
    });
    document.body.append(dialog);
  }
  activeEditor.dialog.showModal();
  activeEditor.dialog.querySelector("input")?.focus();
}

function detailView(rfc) {
  activeRFC = rfc;
  setTranslations(rfc.translations);
  const wrapper = element("div");
  const source = rfc.source || {};
  const fresh = rfc.freshness || {};
  const projection = rfcContent(rfc).projection;
  if (activeEditor?.id === rfc.id && (!canWrite(rfc) || (rfc.enrolled && !canPublish(rfc)))) closeRFCEditor(true);
  const actions = element("div", {class: "actions"}, button("刷新", route));
  const sourceLink = safeLink(source.url);
  if (sourceLink) actions.append(sourceLink);
  if (canWrite(rfc) && (!rfc.enrolled || canPublish(rfc))) actions.append(button("编辑 RFC", () => openRFCEditor(activeRFC)));
  if (canPublish(rfc) && rfc.enrolled) actions.append(button("同步来源", async () => { await operationNotice(await action("rfcs.sync", {rfc_id: rfc.id})); await route(); }));
  actions.append(button("导出", async () => {
    const data = await api(`/api/v1/rfcs/${encodeURIComponent(rfc.id)}/export`);
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type: "application/json"}));
    const link = element("a", {href: url, download: `rfc-${rfc.id}.json`});
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }));
  wrapper.append(heading(rfc.title || "未命名 RFC", `${repoName(rfc.repo_id)} · ${rfc.id}`, actions));
  const translation = rfc.translations;
  if (translation?.enabled && (translation.pending || translation.failed)) wrapper.append(element("p", {class: "translation-status small muted", role: "status"},
    element("span", {}, "翻译同步中"), `：${translation.ready}/${translation.total} · `,
    element("span", {}, "未完成内容暂时显示原文。"), translation.failed ? element("span", {}, `${translation.failed} `, element("span", {}, "项稍后重试。")) : null));
  if (rfc.sync_status === "requires_reauthorization") {
    const warning = element("div", {class: "warning"}, "自动追踪已暂停：原授权已失效，需要维护者重新授权后才能继续同步。 ");
    if (canPublish(rfc)) warning.append(button("重新授权追踪", async () => {
      if (!confirm("确认使用当前个人授权，继续追踪这个 RFC？")) return;
      await operationNotice(await action("rfcs.enroll", {rfc_id: rfc.id, content_digest: rfc.content_digest, expected_revision: rfc.revision})); await route();
    }));
    wrapper.append(warning);
  } else if (rfc.sync_status === "different_writer") {
    wrapper.append(element("div", {class: "warning"}, "这个 RFC 由另一个工作空间维护。当前工作空间可以查看记录；请在负责维护的工作空间进行同步。"));
  }
  if (fresh.state === "stale" || fresh.error || fresh.stale) wrapper.append(element("div", {class: "warning"}, "来源状态尚未确认，请谨慎使用当前进展。", fresh.error ? ` ${readable(fresh.error)}` : ""));
  const navigation = element("nav", {class: "rfc-section-nav", "aria-label": "RFC 内容分区"});
  for (const [id, title] of [["outcome", "成果"], ["goals", "目标与范围"], ["work", "路线图与工作"], ["design", "方案与设计"], ["acceptance", "验收与证据"], ["references", "风险与参考"]]) {
    navigation.append(button(title, () => content.querySelector(`#rfc-${id}`)?.scrollIntoView({behavior: "smooth", block: "start"}), "quiet"));
  }
  wrapper.append(navigation, outcomePanel(rfc, projection));
  const publish = element("div", {class: "actions"});
  if (canPublish(rfc) && !source.provider && !rfc.published) publish.append(button("明确发布并纳管", async () => {
    if (!confirm("确认把当前预览内容发布到所选仓库，并启用进展追踪？")) return;
    const result = await action("rfcs.publish", {rfc_id: rfc.id, content_digest: rfc.content_digest, expected_revision: rfc.revision, post: true, idempotency_key: crypto.randomUUID()});
    await operationNotice(result); await route();
  }, "primary"));
  if (canPublish(rfc) && source.provider && !rfc.enrolled) publish.append(button("启用进展追踪", async () => {
    if (!confirm("确认纳管这个 RFC，并在设定范围内自动关联实现证据？")) return;
    await operationNotice(await action("rfcs.enroll", {rfc_id: rfc.id, content_digest: rfc.content_digest, expected_revision: rfc.revision})); await route();
  }));
  const metadata = element("div", {class: "status-row"}, safeLink(source.url), element("span", {}, `版本 ${String(rfc.revision || 1).slice(0, 10)}`), element("span", {}, `最后核验：${dateText(fresh.verification || fresh.last_verified_at || fresh.last_verified || fresh.checked_at)}`));
  const goals = panel("目标与范围", element("div", {class: "stack"}, metadata,
    componentSections(rfc, [...projection.overview, ...projection.goals, ...projection.scope], "尚未声明问题、目标和范围。"), publish));
  goals.id = "rfc-goals";
  const work = element("section", {id: "rfc-work", class: "rfc-workspace"}, panel("交互路线图", dependencyGraph(rfc), "拖动空白区域平移；点击节点查看工作与证据。实现与验收分别显示。"), workPanel(rfc));
  const design = panel("方案与设计", componentSections(rfc, projection.design, "尚未补充方案与设计。", true));
  design.id = "rfc-design";
  const acceptance = element("section", {id: "rfc-acceptance", class: "rfc-workspace"}, element("div", {class: "split"}, criteriaPanel(rfc), element("div", {}, suggestionsPanel(rfc), canPublish(rfc) ? decisionPanel(rfc) : null)));
  if (projection.acceptance?.length) acceptance.append(panel("验收说明", componentSections(rfc, projection.acceptance, "", true)));
  const references = panel("风险与参考", element("div", {class: "stack"},
    componentSections(rfc, [...projection.risks, ...projection.references], "尚未补充风险与参考资料。", true),
    element("h3", {}, "补充资料与历史记录"), componentSections(rfc, projection.supplement, "暂无补充资料。", true)));
  references.id = "rfc-references";
  wrapper.append(goals, work, design, acceptance, references);
  if (principal.admin) wrapper.append(rfcAccessPanel(rfc));
  refreshCurrent = async () => {
    const latest = await getRFC(rfc.id);
    if (viewDirty || featureDialog || activeEditor?.dialog.open || busyOperations) return;
    if (location.hash.startsWith(`#rfc/${encodeURIComponent(rfc.id)}`) && JSON.stringify(latest) !== JSON.stringify(activeRFC)) await applyRFCResult(latest);
  };
  return wrapper;
}

function workPanel(rfc, allowAdd = true) {
  const list = element("div", {class: "item-list"});
  const tracks = new Map();
  for (const feature of rfc.features || []) {
    const track = feature.track || "工作";
    if (allowAdd && !tracks.has(track)) {
      const group = element("section", {class: "work-track", "data-work-track": track}, element("h3", {}, track));
      tracks.set(track, group); list.append(group);
    }
    const links = element("div", {class: "item-detail"});
    for (const link of feature.links || []) {
      const url = typeof link === "string" ? link : link.url;
      const label = typeof link === "string" ? link : `${link.identifier || link.id || "实现来源"} · ${translated(link.state || "unknown")}`;
      const anchor = safeLink(url, label);
      links.append(anchor || element("span", {}, readable(link)), element("br"));
    }
    const operations = element("div", {class: "item-actions"});
    const update = async (values) => { await applyRFCResult(await action("rfcs.work", {rfc_id: rfc.id, op: "update", feature_id: feature.id, feature: values})); };
    if (!feature.dropped && !feature.owner) operations.append(button("认领", async () => {
      await applyRFCResult(await action("rfcs.work", {rfc_id: rfc.id, op: "claim", feature_id: feature.id, reason: "工作台自主认领"}));
    }));
    else if (!feature.dropped && canPublish(rfc)) operations.append(button("更改负责人", async () => {
      const owner = prompt("负责人名称或用户 ID", feature.owner);
      if (owner === null || !owner.trim()) return;
      const reason = prompt("负责人调整的依据");
      if (reason !== null && reason.trim()) {
        await applyRFCResult(await action("rfcs.work", {rfc_id: rfc.id, op: "update", feature_id: feature.id, feature: {owner: owner.trim()}, reason}));
      }
    }));
    if (!feature.dropped) {
      const state = select("work_state", ["planned", "in_progress", "implemented"], feature.state || "planned");
      state.setAttribute("aria-label", `${feature.title || feature.id} 的工作状态`);
      operations.append(state, button("记录工作状态", () => update({state: state.value})));
    }
    if (canPublish(rfc)) operations.append(button(feature.dropped ? "恢复" : "移除", async () => {
      const reason = prompt(feature.dropped ? "恢复原因" : "移除原因（会保留历史）");
      if (reason === null || !reason.trim()) return;
      await applyRFCResult(await action("rfcs.work", {rfc_id: rfc.id, op: feature.dropped ? "restore" : "drop", feature_id: feature.id, reason}));
    }, feature.dropped ? "" : "danger"));
    const historical = historicalClaims(rfc, feature);
    const cache = rfcContent(rfc);
    const descriptions = cache.projection.featureSections[feature.id] || [];
    const descriptionKey = `feature:${feature.id}:${allowAdd ? "work" : "dialog"}`;
    let description = cache.nodes.get(descriptionKey) || null;
    if (!description && descriptions.length) {
      description = element("details", {class: "work-description"}, element("summary", {}, "RFC 描述"));
      description.addEventListener("toggle", () => {
        if (description.open && !description.querySelector(".component-sections")) description.append(componentSections(rfc, descriptions, "", false, descriptionKey));
      });
      cache.nodes.set(descriptionKey, description);
    }
    (allowAdd ? tracks.get(track) : list).append(element("article", {class: "work-item", "data-feature-id": feature.id}, element("div", {class: "item-heading"}, element("h4", {}, feature.title || feature.id), badge(feature.dropped ? "dropped" : feature.implementation || feature.state || "planned")),
      element("div", {class: "item-detail"}, `${feature.id} · 负责人：${feature.owner || "待认领"}`, element("br"), `依赖：${(feature.depends_on || []).join("、") || "无"}`), historical, links, description, canWrite(rfc) ? operations : null));
  }
  if (!(rfc.features || []).length) list.append(empty("还没有工作项", "把方案拆分成有负责人和依赖的工作。"));
  const form = element("form", {class: "inline-form"});
  form.append(element("h4", {}, "添加工作项"), element("div", {class: "form-grid"},
    field("编号", input("id", "例如 E1", "", "text", true)), field("标题", input("title", "具体工作", "", "text", true)),
    field("负责人", input("owner", "用户 ID 或名称")), field("依赖编号", input("depends_on", "逗号分隔，例如 E1,E2")),
    field("实现链接", input("link", "PR 或实现来源 URL"), "明确的实现链接用于刷新进展。", true)), element("div", {class: "actions"}, element("button", {type: "submit"}, "添加工作项")));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    busy(form.querySelector("button"), async () => {
      const data = formData(form);
      const feature = {id: data.id.trim(), title: data.title.trim(), owner: data.owner.trim(), depends_on: data.depends_on.split(/[,，]/).map((id) => id.trim()).filter(Boolean), state: "planned", links: data.link.trim() ? [data.link.trim()] : []};
      await applyRFCResult(await action("rfcs.work", {rfc_id: rfc.id, op: "add", feature}));
    });
  });
  return panel("工作项与负责人", element("div", {}, list, canPublish(rfc) && allowAdd ? form : null));
}

function historicalClaims(rfc, feature) {
  const claims = [...(feature.historical_claims || []), ...(rfc.historical_claims || []).filter((claim) => (claim.feature || claim.feature_id) === feature.id)];
  if (!claims.length) return null;
  const wrapper = element("div", {class: "item-detail historical-claims"}, element("span", {class: "badge amber"}, "历史认领（待确认身份）"));
  const seen = new Set();
  for (const claim of claims) {
    const key = claim.id || `${claim.login || claim.name}:${claim.created_at || ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    wrapper.append(element("div", {}, claim.login || claim.name || "历史记录", claim.note ? ` · ${claim.note}` : ""));
  }
  return wrapper;
}

function evidenceLines(evidence) {
  const wrapper = element("div", {class: "item-detail"});
  const records = Array.isArray(evidence) ? evidence : evidence ? [evidence] : [];
  for (const record of records) {
    if (typeof record === "string") wrapper.append(safeLink(record, record) || element("span", {}, record));
    else {
      const link = safeLink(record.url || record.source?.url, record.title || record.url || "证据来源 ↗");
      if (link) wrapper.append(link);
      wrapper.append(element("span", {}, record.note || record.summary || record.reason || readable(record)));
      if (record.stale) wrapper.append(badge("stale"));
    }
  }
  if (!records.length) wrapper.append("尚未记录验证证据。");
  return wrapper;
}
function criteriaPanel(rfc) {
  const list = element("div", {class: "item-list"});
  for (const criterion of rfc.criteria || []) {
    const form = element("form", {class: "inline-form"});
    form.append(element("div", {class: "form-grid"}, field("验证结论", select("verdict", ["pending", "passing", "failing", "waived"], criterion.verdict || "pending")),
      field("证据链接", input("url", "测试、报告或讨论链接")), field("验证版本", input("verification_revision", "例如：实现提交 SHA 或发布版本"), "填写实际接受验证的实现版本。", true), field("验证环境", input("environment", "例如：Linux · GPU 型号 · 模型版本"), "通过时需要记录验证环境。", true),
      field("验证依据", input("reason", "说明结果或豁免理由"), "验收证据将关联当前 RFC 版本。", true)), element("button", {type: "submit"}, "记录验收结论"));
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      busy(form.querySelector("button"), async () => {
        const data = formData(form);
        const payload = {rfc_id: rfc.id, kind: "criterion", criterion_id: criterion.id, verdict: data.verdict, reason: data.reason};
        if (data.url || data.verification_revision || data.environment) payload.evidence = {url: data.url, note: data.reason, revision: data.verification_revision, environment: data.environment};
        await applyRFCResult(await action("rfcs.decision", payload));
      });
    });
    const details = element("details", {}, element("summary", {}, "更新验收"), form);
    list.append(element("article", {class: "criterion", "data-criterion-id": criterion.id}, element("div", {class: "item-heading"}, element("h4", {}, criterion.title || criterion.id), badge(criterion.verdict || "pending")),
      evidenceLines(criterion.evidence), canPublish(rfc) ? details : null));
  }
  if (!(rfc.criteria || []).length) list.append(empty("验收条件待补充", "编辑 RFC 时明确可验证的条件与证据。"));
  return panel("验收条件", list, "PR 合并不会自动通过验收。");
}
function suggestionsPanel(rfc) {
  const list = element("div", {class: "item-list"});
  let total = rfc.suggestion_counts?.proposed || 0;
  let page = Math.min(suggestionPages.get(rfc.id) || 0, Math.max(0, Math.ceil(total / SUGGESTIONS_PER_PAGE) - 1));
  let sequence = 0;
  const count = element("span", {class: "small muted", "aria-live": "polite"});
  const previous = element("button", {type: "button", onclick: () => { page -= 1; draw(); }}, "上一页");
  const next = element("button", {type: "button", onclick: () => { page += 1; draw(); }}, "下一页");
  const pagination = element("div", {class: "actions suggestion-pagination"}, count, previous, next);
  function updateControls(loading = false) {
    const pages = Math.max(1, Math.ceil(total / SUGGESTIONS_PER_PAGE));
    count.textContent = `${total} 条待确认 · 第 ${page + 1} / ${pages} 页${loading ? " · 读取中…" : ""}`;
    previous.disabled = loading || page === 0;
    next.disabled = loading || page >= pages - 1;
    previous.hidden = next.hidden = total <= SUGGESTIONS_PER_PAGE;
  }
  async function draw() {
    const current = ++sequence;
    updateControls(true);
    list.replaceChildren(element("p", {class: "small muted"}, "正在读取这一页建议…"));
    try {
      const result = await action("rfcs.suggestions", {rfc_id: rfc.id, offset: page * SUGGESTIONS_PER_PAGE, limit: SUGGESTIONS_PER_PAGE, status: "proposed"});
      if (current !== sequence || !list.isConnected || !principal) return;
      total = result.total;
      setTranslations(result.translations, false);
      const last = Math.max(0, Math.ceil(total / SUGGESTIONS_PER_PAGE) - 1);
      if (page > last) { page = last; return draw(); }
      suggestionPages.set(rfc.id, page);
      list.replaceChildren();
      for (const suggestion of result.suggestions || []) {
        list.append(element("article", {class: "suggestion"}, element("h4", {}, suggestion.title || suggestion.feature?.title || "待确认的关联"),
          element("p", {class: "small muted"}, suggestion.reason || suggestion.explanation || "请核对这个实现是否属于当前 RFC。"), evidenceLines(suggestion.evidence),
          canPublish(rfc) ? element("div", {class: "item-actions"}, ...["accepted", "rejected"].map(verdict => button(verdict === "accepted" ? "接受建议" : "拒绝", async () => {
            const reason = prompt(verdict === "accepted" ? "接受依据" : "拒绝原因（相同建议不会重复出现）");
            if (reason === null || !reason.trim()) return;
            await applyRFCResult(await action("rfcs.decision", {rfc_id: rfc.id, kind: "suggestion", suggestion_id: suggestion.id, verdict, reason}));
          }, verdict === "rejected" ? "danger" : ""))) : null));
      }
      if (!total) list.append(element("p", {class: "small muted"}, "暂无需要确认的建议。明确关联在范围内自动更新，模糊关联留待你判断。"));
      updateControls();
    } catch (error) {
      if (current === sequence && list.isConnected) {
        list.replaceChildren(element("p", {class: "error-panel"}, error.message), button("重试读取这一页", draw));
        updateControls();
      }
    }
  }
  if (total) draw();
  else { updateControls(); list.append(element("p", {class: "small muted"}, "暂无需要确认的建议。")); }
  return panel("待确认建议", element("div", {class: "stack"}, pagination, list));
}

function decisionPanel(rfc) {
  const form = element("form", {class: "stack"});
  form.append(field("RFC 决策", select("verdict", ["draft", "discussion", "accepted", "rejected", "superseded"], rfc.state || "draft")), field("决策依据", input("reason", "记录评审结论或后续 RFC")), element("button", {type: "submit"}, "记录 RFC 决策"));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    busy(form.querySelector("button"), async () => { await applyRFCResult(await action("rfcs.decision", {rfc_id: rfc.id, kind: "rfc", ...formData(form)})); });
  });
  return panel("评审决策", form, "接受方案表示方向获批，验收完成单独记录。");
}
function rfcAccessPanel(rfc) {
  const form = element("form", {class: "stack"});
  const restricted = element("input", {type: "checkbox", name: "restricted"});
  restricted.checked = Boolean(rfc.restricted);
  form.append(element("label", {class: "check-label"}, restricted, "仅向指定用户开放这个 RFC"),
    field("RFC 授权", element("textarea", {name: "grants", rows: 3, placeholder: '{"用户 ID": "reader"}'}, JSON.stringify(rfc.grants || rfc.acl || {}, null, 2)), "角色：reader、contributor、maintainer。工作空间管理员仍可管理。"), element("button", {type: "submit"}, "保存 RFC 权限"));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    busy(form.querySelector("button"), async () => {
      let grants;
      try { grants = JSON.parse(form.elements.grants.value); } catch { throw new Error("RFC 授权必须是有效的 JSON 对象。"); }
      await action("rfcs.acl", {rfc_id: rfc.id, restricted: restricted.checked, grants}); notice("RFC 权限已更新。"); await route();
    });
  });
  return panel("RFC 访问范围", form);
}

function operationsView(data) {
  const wrapper = element("div");
  wrapper.append(heading("每次操作，都有记录", "发布、纳管与同步会记录执行状态；结果不明时先核对来源。", element("div", {class: "actions"}, button("刷新", route))));
  const operations = data.operations || [];
  if (!operations.length) { wrapper.append(empty("暂无操作", "发布、纳管或同步 RFC 后，执行结果会显示在这里。")); return wrapper; }
  const table = element("table", {}, element("thead", {}, element("tr", {}, ...["操作", "RFC", "状态", "时间", "结果"].map((name) => element("th", {}, name)))));
  const body = element("tbody");
  for (const operation of operations) {
    const state = operation.state || operation.status;
    const recovery = ["failed", "uncertain"].includes(state) && (principal.admin || repositories.find((repo) => repo.id === operation.repo_id)?.role === "maintainer")
      ? button("核对并重试", async () => {
        if (!confirm("重试会先核对已有结果，避免重复发布。确认恢复这个操作？")) return;
        await action("operations.retry", {operation_id: operation.id}); notice("恢复操作已进入队列。"); await route();
      }) : null;
    body.append(element("tr", {}, element("td", {}, operation.action || operation.kind || "操作", element("div", {class: "mono muted"}, operation.id)),
      element("td", {}, operation.rfc_id ? element("a", {href: `#rfc/${encodeURIComponent(operation.rfc_id)}`}, operation.rfc_id) : "—"), element("td", {}, badge(state)),
      element("td", {}, dateText(operation.updated || operation.updated_at || operation.created || operation.created_at)), element("td", {}, operation.error || readable(operation.result), recovery)));
  }
  table.append(body);
  wrapper.append(panel("执行记录", element("div", {class: "table-wrap"}, table)));
  refreshCurrent = () => route();
  return wrapper;
}

async function accountView() {
  const result = await api(`/api/v1/tokens?user_id=${encodeURIComponent(principal.user_id)}`);
  const wrapper = element("div");
  wrapper.append(heading("管理你的个人令牌", "为 Copilot 和命令行签发令牌，或撤销不再使用的访问凭据。", element("div", {class: "actions"}, button("刷新", route))),
    tokensPanel(result.tokens || [], [[principal.user_id, principal.name || principal.user_id]], true));
  return wrapper;
}

async function adminView() {
  selectedTokenUser ||= principal.user_id;
  const [usersResult, tokensResult, settings] = await Promise.all([api("/api/v1/users"), api(`/api/v1/tokens?user_id=${encodeURIComponent(selectedTokenUser)}`), action("service.settings")]);
  const users = usersResult.users || [];
  const tokens = tokensResult.tokens || [];
  const wrapper = element("div");
  wrapper.append(heading("团队在明确的范围内协作", "为具体用户签发令牌，并授予仓库或 RFC 的访问权限。", element("div", {class: "actions"}, button("刷新", route))));
  const userForm = element("form", {class: "stack"});
  const admin = element("input", {type: "checkbox", name: "admin"});
  userForm.append(field("姓名", input("name", "用户姓名", "", "text", true)), element("label", {class: "check-label"}, admin, "工作空间管理员"), element("button", {type: "submit"}, "添加用户"));
  userForm.addEventListener("submit", (event) => { event.preventDefault(); busy(userForm.querySelector("button"), async () => {
    await action("users.create", {name: userForm.elements.name.value, admin: admin.checked}); notice("用户已创建。"); await route();
  }); });
  const userTable = element("table", {}, element("thead", {}, element("tr", {}, ...["用户", "角色", "状态", "操作"].map((name) => element("th", {}, name)))));
  const userBody = element("tbody");
  for (const user of users) userBody.append(element("tr", {}, element("td", {}, user.name, element("div", {class: "mono muted"}, user.id || user.user_id)),
    element("td", {}, user.admin ? "管理员" : "成员"), element("td", {}, user.enabled === false || user.enabled === 0 ? "已停用" : "有效"), element("td", {},
      button(user.enabled === false || user.enabled === 0 ? "启用" : "停用", async () => {
        if (!confirm(`确认更改 ${user.name} 的访问状态？`)) return;
        await action("users.update", {user_id: user.id || user.user_id, enabled: user.enabled === false || user.enabled === 0}); await route();
      }, "danger"))));
  userTable.append(userBody);
  const userChoices = users.map((user) => [user.id || user.user_id, user.name]);
  const repoForm = element("form", {class: "stack"});
  repoForm.append(field("仓库名称", input("name", "团队可识别的名称", "", "text", true)), field("来源", select("provider", ["github", "atomgit", ["local", "本地 Git / Markdown"]])),
    field("外部仓库", input("external_name", "owner/repository 或 AtomGit 项目标识")), field("本地根目录", input("root", "本地来源：服务可访问且已授权的目录")),
    element("button", {type: "submit"}, "登记仓库"));
  repoForm.addEventListener("submit", (event) => { event.preventDefault(); busy(repoForm.querySelector("button"), async () => {
    const payload = formData(repoForm); if (!payload.external_name.trim()) delete payload.external_name; if (!payload.root.trim()) delete payload.root;
    await action("repositories.create", payload); repositories = (await api("/api/v1/repositories")).repositories || []; notice("仓库已登记。"); await route();
  }); });
  const grantForm = element("form", {class: "stack"});
  grantForm.append(field("用户", select("user_id", userChoices)), field("仓库", select("repo_id", repoChoices())), field("权限", select("role", ["reader", "contributor", "maintainer", ["none", "撤销授权"]])), element("button", {type: "submit"}, "保存仓库授权"));
  grantForm.addEventListener("submit", (event) => { event.preventDefault(); busy(grantForm.querySelector("button"), async () => {
    const payload = formData(grantForm); if (payload.role === "none") payload.role = "";
    await action("grants.set", payload); notice("仓库授权已更新。");
  }); });
  wrapper.append(panel("用户", element("div", {class: "table-wrap"}, userTable)));
  wrapper.append(element("div", {class: "admin-grid"}, panel("添加成员", userForm), panel("仓库访问范围", grantForm), panel("登记仓库", repoForm), tokensPanel(tokens, userChoices)));
  wrapper.append(serviceSettingsPanel(settings));
  return wrapper;
}

function serviceSettingsPanel(settings) {
  const form = element("form", {class: "stack"});
  const interval = input("sync_seconds", "3600", settings.sync_seconds ?? 3600, "number", true);
  interval.min = "60"; interval.max = "86400"; interval.step = "1";
  const additions = input("default_max_auto_additions", "5", settings.default_max_auto_additions ?? 5, "number", true);
  additions.min = "0"; additions.max = "100"; additions.step = "1";
  form.append(element("div", {class: "form-grid"}, field("同步间隔（秒）", interval, "60–86400 秒；后台按这个间隔检查已纳管的 RFC。"),
    field("新 RFC 默认自动新增上限", additions, "0–100 项；已有 RFC 的范围与上限保持各自设置。")),
    element("div", {class: "status-row"}, element("span", {}, "成员访问：仅限管理员授权"),
      element("span", {}, `已配置来源：${(settings.configured_providers || []).map((name) => labels[name] || name).join("、") || "暂无"}`)),
    element("div", {class: "actions"}, element("button", {type: "submit", class: "primary"}, "保存服务设置")));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    busy(form.querySelector("button"), async () => {
      await action("service.configure", {sync_seconds: Number(interval.value), default_max_auto_additions: Number(additions.value)});
      notice("服务设置已更新。"); await route();
    });
  });
  return panel("服务设置", form);
}

function tokensPanel(tokens, choices, ownOnly = false) {
  const list = element("div", {class: "item-list"});
  for (const token of tokens) list.append(element("div", {class: "work-item"}, element("div", {class: "item-heading"}, element("span", {class: "mono"}, token.id || token.token_id),
    badge(token.revoked || token.revoked_at ? "revoked" : "valid_token")), element("p", {class: "item-detail"}, `用户：${token.user_id} · 到期：${dateText(token.expires || token.expires_at)}`),
    !token.revoked && !token.revoked_at ? button("撤销令牌", async () => {
      if (!confirm("撤销后，该令牌及其关联会话将失效。继续？")) return;
      await action("tokens.revoke", {token_id: token.id || token.token_id}); await route();
    }, "danger") : null));
  const form = element("form", {class: "inline-form stack"});
  const user = select("user_id", choices, ownOnly ? principal.user_id : selectedTokenUser);
  if (ownOnly) user.disabled = true;
  else user.addEventListener("change", async () => { selectedTokenUser = user.value; await route(); });
  form.append(field("对应用户", user, ownOnly ? "此页面仅管理你自己的令牌。" : "切换用户可查看、撤销该用户的令牌。"), field("有效天数", input("expires_days", "30", "30", "number", true)), element("button", {type: "submit"}, "签发个人令牌"));
  form.addEventListener("submit", (event) => { event.preventDefault(); busy(form.querySelector("button"), async () => {
    const data = formData(form);
    const result = await action("tokens.create", {user_id: ownOnly ? principal.user_id : data.user_id, expires_days: Number(data.expires_days)});
    $("issued-secret").value = result.token || result.secret || "";
    $("secret-dialog").showModal();
  }); });
  return panel("个人令牌", element("div", {}, list, form), "原始令牌只在创建时显示；撤销同时结束相关会话。");
}

setInterval(async () => {
  if (!principal || document.hidden || viewDirty || featureDialog || busyOperations || $("secret-dialog").open || !refreshCurrent) return;
  try { await refreshCurrent(); } catch (error) { if (principal) notice(`刷新未完成：${error.message}`, true); }
}, 30000);

document.querySelectorAll("[data-language]").forEach(control => control.addEventListener("click", async () => {
  await changeLanguage(control.dataset.language);
  if (principal) await route();
}));
await initializeLocale();
try { await signedIn(await api("/api/v1/me")); }
catch { signedOut(); }
