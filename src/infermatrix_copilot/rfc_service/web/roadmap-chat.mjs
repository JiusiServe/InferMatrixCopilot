import {currentLanguage, localizeText, applyLocale} from "/roadmap-locale.mjs";

const running = job => ["pending", "running"].includes(job.status);
const keyOf = value => JSON.stringify(value);
const label = value => localizeText(value);
const node = (tag, attrs = {}, ...children) => {
  const result = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") result.className = value;
    else if (key.startsWith("on")) result.addEventListener(key.slice(2), value);
    else if (value !== null && value !== undefined) result.setAttribute(key, String(value));
  }
  for (const child of children.flat()) if (child !== null && child !== undefined) result.append(child instanceof Node ? child : String(child));
  return result;
};
const control = (text, callback, className = "") => node("button", {type: "button", class: className, onclick: callback}, text);
const privateText = text => node("span", {"data-no-translate": ""}, String(text ?? ""));

// Same compact, sorted-key JSON as store.encode({title, body}). This also works
// on portable HTTP installations where WebCrypto is unavailable.
export function draftDigest(title, body) {
  return sha256(JSON.stringify({body: String(body || ""), title: String(title || "")}));
}
export function sha256(text) {
  const bytes = new TextEncoder().encode(text), size = Math.ceil((bytes.length + 9) / 64) * 64;
  const padded = new Uint8Array(size); padded.set(bytes); padded[bytes.length] = 128;
  const view = new DataView(padded.buffer), bitLength = bytes.length * 8;
  view.setUint32(size - 8, Math.floor(bitLength / 4294967296)); view.setUint32(size - 4, bitLength >>> 0);
  const primes = [], constants = [];
  for (let value = 2; constants.length < 64; value++) {
    if (primes.some(prime => prime * prime <= value && value % prime === 0)) continue;
    primes.push(value); constants.push(Math.floor((Math.cbrt(value) % 1) * 4294967296) >>> 0);
  }
  const hash = primes.slice(0, 8).map(prime => Math.floor((Math.sqrt(prime) % 1) * 4294967296) >>> 0);
  const rotate = (value, count) => (value >>> count) | (value << (32 - count));
  for (let offset = 0; offset < size; offset += 64) {
    const words = new Uint32Array(64);
    for (let index = 0; index < 16; index++) words[index] = view.getUint32(offset + index * 4);
    for (let index = 16; index < 64; index++) {
      const a = words[index - 15], b = words[index - 2];
      words[index] = words[index - 16] + (rotate(a, 7) ^ rotate(a, 18) ^ (a >>> 3)) + words[index - 7] + (rotate(b, 17) ^ rotate(b, 19) ^ (b >>> 10));
    }
    let [a, b, c, d, e, f, g, h] = hash;
    for (let index = 0; index < 64; index++) {
      const first = (h + (rotate(e, 6) ^ rotate(e, 11) ^ rotate(e, 25)) + ((e & f) ^ (~e & g)) + constants[index] + words[index]) >>> 0;
      const second = ((rotate(a, 2) ^ rotate(a, 13) ^ rotate(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0;
      h = g; g = f; f = e; e = (d + first) >>> 0; d = c; c = b; b = a; a = (first + second) >>> 0;
    }
    [a, b, c, d, e, f, g, h].forEach((value, index) => { hash[index] = (hash[index] + value) >>> 0; });
  }
  return hash.map(value => value.toString(16).padStart(8, "0")).join("");
}

export function eventText(event) {
  const data = event.data;
  if (typeof data === "string") return data;
  return data?.text ?? data?.delta ?? data?.content ?? data?.chunk ?? "";
}

/** One DOM root follows the editor; route updates never rebuild this controller. */
export function createChat({action, markdownBody, canEdit, getDraft, resolveSelection, onApply, refreshRFC, onSourceUpdate, onNotice, mount, launcher}) {
  const states = new Map();
  let owner = null, epoch = 0, context = null, current = null, collapsed = true, fullscreen = false, polling = null, timer;
  const root = node("aside", {id: "rfc-chat", class: "rfc-chat", "aria-label": "RFC 对话助手"});
  const title = node("h2", {}, "RFC 对话助手");
  const collapse = control("收起", () => setCollapsed(true), "quiet");
  const expand = control("全屏", () => { fullscreen = !fullscreen; layout(); }, "quiet");
  const languages = node("div", {class: "chat-languages", "data-no-translate": "", "aria-label": "Language / 语言"}, node("button", {type: "button", "data-language": "en"}, "EN"), node("button", {type: "button", "data-language": "zh"}, "中文"));
  const header = node("div", {class: "chat-heading"}, title, node("div", {class: "actions"}, languages, expand, collapse));
  const scope = node("div", {class: "chat-scope"});
  const threads = node("select", {"aria-label": "选择对话", onchange: () => switchThread(threads.value)});
  const newThread = control("新对话", () => perform(current, async state => {
    const result = await action("chat.create", {rfc_id: state.rfc.id});
    if (states.get(state.rfc.id) !== state) return;
    state.threads.unshift(result.thread); state.threadId = result.thread?.id || result.thread_id;
    state.snapshot = result; state.live.clear(); state.cursor = 0; state.previews.clear(); state.selection = null; state.earlier = []; state.historyMore = null;
    await load(state);
  }));
  const deleteThread = control("删除对话", () => {
    const state = current;
    if (!state?.threadId || !confirm(label("删除这段对话及其编辑建议？"))) return;
    perform(state, async () => {
      await action("chat.delete", {thread_id: state.threadId});
      state.threads = state.threads.filter(thread => thread.id !== state.threadId); state.threadId = state.threads[0]?.id || "";
      state.snapshot = {}; state.live.clear(); state.previews.clear(); state.cursor = 0; state.earlier = []; state.historyMore = null;
      if (state.threadId) await load(state); else render();
    });
  }, "quiet danger");
  const threadbar = node("div", {class: "chat-threads"}, threads, newThread, deleteThread);
  const selection = node("div", {class: "chat-selection"});
  const error = node("p", {class: "form-error chat-error", role: "alert", hidden: true});
  const log = node("div", {class: "chat-log", tabindex: "0", "aria-label": "对话与编辑建议"});
  const status = node("p", {class: "chat-status small muted", role: "status", "aria-live": "polite"});
  const input = node("textarea", {rows: "3", placeholder: "讨论方案，或说明希望修改的内容…", "aria-label": "发送给 RFC 助手的消息"});
  const draftHint = node("p", {class: "small muted chat-draft-hint"});
  const send = node("button", {type: "submit", class: "primary"}, "发送");
  const stop = control("停止生成", () => {
    const state = current, job = state?.snapshot.jobs?.find(running);
    if (job) perform(state, async () => absorb(state, await action("chat.cancel", {thread_id: state.threadId, job_id: job.id})));
  });
  const composer = node("form", {class: "chat-composer", onsubmit: event => { event.preventDefault(); sendMessage(); }}, draftHint, input, node("div", {class: "chat-compose-actions"}, node("span", {class: "small muted"}, "Enter 换行 · Ctrl/⌘ + Enter 发送"), stop, send));
  input.addEventListener("input", () => { if (current) current.input = input.value; renderControls(); });
  input.addEventListener("keydown", event => { if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); sendMessage(); } });
  log.addEventListener("scroll", () => { if (current) current.scroll = log.scrollTop; });
  root.addEventListener("keydown", event => { if (event.key === "Escape" && fullscreen) { event.preventDefault(); event.stopPropagation(); fullscreen = false; layout(); } });
  root.append(header, scope, threadbar, selection, error, log, status, composer); mount.append(root);
  launcher.addEventListener("click", () => { setCollapsed(!collapsed); if (!collapsed) input.focus(); });

  function layout() {
    root.hidden = !owner || collapsed;
    root.classList.toggle("chat-fullscreen", fullscreen);
    mount.classList.toggle("chat-open", Boolean(owner && !collapsed && root.parentElement === mount));
    document.getElementById("app")?.classList.toggle("has-chat", Boolean(owner && !collapsed && root.parentElement === mount));
    launcher.hidden = !owner || !collapsed || root.closest("dialog") !== null;
    launcher.setAttribute("aria-expanded", String(!collapsed));
    expand.textContent = label(fullscreen ? "退出全屏" : "全屏");
    applyLocale(root);
  }
  function setCollapsed(value) { collapsed = value; layout(); if (collapsed && !launcher.hidden) launcher.focus(); }
  function newState(rfc) {
    return {rfc, threads: [], threadId: "", snapshot: {}, cursor: 0, live: new Map(), phases: new Map(), previews: new Map(), selection: null, input: "", scroll: 0, busy: false, loaded: false, loading: false, error: "", fingerprint: "", sendKey: null, sendSignature: null, earlier: [], historyMore: null};
  }
  async function perform(state, callback) {
    if (!state || state.busy || !owner) return;
    const generation = epoch; state.busy = true; state.error = ""; render();
    try { await callback(state); }
    catch (failure) { if (generation === epoch) state.error = failure.message; }
    finally { if (generation === epoch) { state.busy = false; render(); schedule(); } }
  }
  function absorb(state, snapshot) {
    if (!snapshot || !owner || states.get(state.rfc.id) !== state) return;
    if (snapshot.messages) {
      const known = new Set([...state.earlier, ...snapshot.messages].map(message => message.id));
      state.earlier.push(...(state.snapshot.messages || []).filter(message => !known.has(message.id)));
    }
    state.snapshot = {...state.snapshot, ...snapshot};
    if (snapshot.thread) state.threadId = snapshot.thread.id;
    if (!state.cursor && Number.isInteger(snapshot.cursor) && !(snapshot.jobs || []).some(running)) state.cursor = snapshot.cursor;
    for (const message of snapshot.messages || []) if (message.role === "assistant" && message.job_id) state.live.delete(message.job_id);
    for (const job of snapshot.jobs || []) if (job.status === "succeeded") state.live.delete(job.id);
  }
  async function load(state) {
    const generation = epoch, threadId = state.threadId;
    if (!threadId) return;
    const snapshot = await action("chat.get", {thread_id: threadId, limit: 100});
    if (generation !== epoch || threadId !== state.threadId) return;
    absorb(state, snapshot); render(); schedule();
  }
  async function initialize(state) {
    if (state.loading || state.loaded) return;
    const generation = epoch; state.loading = true; render();
    try {
      const result = await action("chat.list", {rfc_id: state.rfc.id});
      if (generation !== epoch) return;
      state.threads = result.threads || []; state.threadId ||= state.threads[0]?.id || ""; state.loaded = true;
      if (state.threadId) await load(state);
    } catch (failure) { if (generation === epoch) state.error = failure.message; }
    finally { if (generation === epoch) { state.loading = false; render(); } }
  }
  async function switchThread(id) {
    const state = current;
    if (!state || state.busy || id === state.threadId) return;
    state.threadId = id; state.snapshot = {}; state.live.clear(); state.cursor = 0; state.previews.clear(); state.fingerprint = ""; state.earlier = []; state.historyMore = null;
    await perform(state, () => load(state));
  }
  async function sendMessage() {
    const state = current;
    if (!state || !context || context.id !== state.rfc.id || state.busy || state.snapshot.jobs?.some(running) || !input.value.trim()) return;
    state.input = input.value;
    const draft = getDraft(state.rfc.id), request = {message: state.input.trim(), language: currentLanguage(), expected_revision: state.rfc.revision};
    const selected = resolveSelection?.(state.rfc, state.selection, draft) ?? state.selection;
    if (selected) request.selection = selected;
    if (draft) { request.draft = {...draft, digest: draftDigest(draft.title, draft.body)}; request.draft_digest = request.draft.digest; }
    const signature = keyOf(request);
    if (signature !== state.sendSignature) { state.sendKey = null; state.sendSignature = signature; }
    state.sendKey ||= globalThis.crypto?.randomUUID?.() || `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    await perform(state, async () => {
      const generation = epoch;
      if (!state.threadId) {
        const created = await action("chat.create", {rfc_id: state.rfc.id});
        if (generation !== epoch) return;
        state.threadId = created.thread?.id || created.thread_id; if (created.thread) state.threads.unshift(created.thread);
      }
      const payload = {thread_id: state.threadId, ...request, idempotency_key: state.sendKey};
      const snapshot = await action("chat.send", payload);
      if (generation !== epoch) return;
      absorb(state, snapshot); state.input = ""; state.sendKey = state.sendSignature = null;
      if (current === state) input.value = "";
    });
  }
  function schedule() {
    clearTimeout(timer);
    if (owner && [...states.values()].some(state => state.snapshot.jobs?.some(running) || state.rfc.source_update?.status === "pending")) timer = setTimeout(poll, 1000);
  }
  async function poll() {
    if (polling === epoch || !owner) return;
    const generation = epoch; polling = generation;
    try {
      for (const state of states.values()) {
        if (!state.busy && state.rfc.source_update?.status === "pending" && refreshRFC) {
          const latest = await refreshRFC(state.rfc.id);
          if (generation !== epoch || states.get(state.rfc.id) !== state) return;
          state.rfc = latest;
          if (context?.id === latest.id) context = latest;
          await onSourceUpdate?.(latest); render();
        }
        if (!state.threadId || state.busy || !state.snapshot.jobs?.some(running)) continue;
        let page;
        do {
          const threadId = state.threadId;
          page = await action("chat.events", {thread_id: threadId, after: state.cursor, cursor: state.cursor, limit: 100});
          if (generation !== epoch || threadId !== state.threadId) break;
          for (const event of page.events || []) {
            if (event.id <= state.cursor) continue;
            if (/delta|chunk|token/.test(event.kind || "")) state.live.set(event.job_id, (state.live.get(event.job_id) || "") + eventText(event));
            if (["queued", "running", "generating", "context_read", "validating"].includes(event.kind)) state.phases.set(event.job_id, event.kind);
            state.cursor = Math.max(state.cursor, Number(event.id) || 0);
          }
          if (page.jobs) state.snapshot.jobs = page.jobs;
          if (page.job) state.snapshot.jobs = [page.job, ...(state.snapshot.jobs || []).filter(job => job.id !== page.job.id)];
          if (Number.isInteger(page.cursor)) state.cursor = Math.max(state.cursor, page.cursor);
          render();
        } while (generation === epoch && (page.events?.length || 0) === 100);
        if (generation !== epoch) return;
        await load(state);
      }
    } catch (failure) { if (generation === epoch && current) { current.error = failure.message; render(); } }
    finally { if (polling === generation) polling = null; if (generation === epoch) schedule(); }
  }
  function renderControls() {
    const state = current, usable = Boolean(owner && context && state?.rfc.id === context.id), active = state?.snapshot.jobs?.some(running), enabled = state?.snapshot.enabled !== false;
    input.disabled = !usable || state.loading || state.busy;
    send.disabled = !usable || !enabled || state.loading || state.busy || active || !input.value.trim();
    stop.hidden = !active; stop.disabled = Boolean(state?.busy);
    newThread.disabled = !usable || state.loading || state.busy || active;
    deleteThread.disabled = !state?.threadId || state.busy || active;
    threads.disabled = !usable || state.loading || state.busy;
    const draft = usable && getDraft(state.rfc.id);
    draftHint.textContent = label(!enabled ? "RFC 助手尚未配置，请联系管理员。" : draft ? "上下文包含尚未保存的编辑内容。" : usable ? "助手依据当前 RFC 与授权可见的工作记录回答。" : "选择一个 RFC 继续对话。");
  }
  function renderProposal(state, proposal) {
    const card = node("article", {class: "chat-proposal"});
    card.append(node("h3", {}, "编辑建议"), privateText(proposal.summary || proposal.reason || ""));
    const statuses = {applied: "已应用", rejected: "已拒绝", stale: "版本已变化，请重新生成"};
    if (statuses[proposal.status]) card.append(node("p", {class: "small muted"}, statuses[proposal.status]));
    const preview = state.previews.get(proposal.id);
    if (preview) {
      card.append(node("pre", {class: "chat-diff", "data-no-translate": "", tabindex: "0"}, typeof preview.diff === "string" ? preview.diff : JSON.stringify(preview.diff, null, 2)));
      if (preview.source_conflict) card.append(node("p", {class: "chat-source-conflict"}, "来源存在其他修改。应用会以已检查的候选版本更新当前来源，请逐项核对下面的来源差异。"));
      if (preview.source_diff) card.append(node("details", {open: ""}, node("summary", {}, "当前来源与候选版本的差异"), node("pre", {class: "chat-diff", "data-no-translate": "", tabindex: "0"}, preview.source_diff)));
      if (preview.plan_diff?.length) card.append(node("details", {open: ""}, node("summary", {}, "工作计划变更"), node("pre", {class: "chat-diff", "data-no-translate": ""}, preview.plan_diff.map(item => typeof item === "string" ? item : JSON.stringify(item, null, 2)).join("\n"))));
      if (preview.source_update) card.append(node("p", {class: "small muted"}, "应用会保存新版本，并排队更新来源；来源同步状态在 RFC 页面显示。"));
      const candidate = preview.candidate || {};
      card.append(node("p", {class: "small muted"}, node("span", {}, "基于版本"), " ", privateText(candidate.base_revision || preview.base_revision), " · ", privateText(preview.candidate_digest?.slice(0, 12))));
      const reason = node("input", {type: "text", placeholder: "修改原因（保存和来源更新的依据）", "aria-label": "应用建议的修改原因", value: preview.reason || ""});
      reason.addEventListener("input", () => { preview.reason = reason.value; });
      const apply = control(preview.source_update ? "应用并同步来源" : "应用并保存", () => applyProposal(state, proposal, preview), "primary");
      apply.disabled = state.busy || !canEdit(state.rfc) || proposal.status !== "proposed";
      card.append(reason, node("div", {class: "actions"}, apply));
    }
    if (proposal.status === "proposed") {
      const inspect = control(preview ? "重新检查差异" : "查看差异", () => perform(state, async () => {
        const draft = getDraft(state.rfc.id), payload = {thread_id: state.threadId, proposal_id: proposal.id};
        if (draft) payload.draft_digest = draftDigest(draft.title, draft.body);
        const result = await action("chat.proposals.preview", payload);
        if (states.get(state.rfc.id) === state) { state.previews.set(proposal.id, {...result, reason: result.proposal?.reason || proposal.reason || "", editorDigest: draft ? payload.draft_digest : null}); state.fingerprint = ""; }
      }));
      const reject = control("拒绝建议", () => perform(state, async () => { await action("chat.proposals.reject", {thread_id: state.threadId, proposal_id: proposal.id}); await load(state); }), "quiet");
      inspect.disabled = reject.disabled = state.busy;
      card.append(node("div", {class: "actions"}, inspect, reject));
      if (!canEdit(state.rfc)) card.append(node("p", {class: "small muted"}, "当前权限可以讨论；应用方案变更需要相应 RFC 编辑权限。"));
    }
    return card;
  }
  async function applyProposal(state, proposal, preview) {
    if (state.busy || !canEdit(state.rfc)) return;
    const draft = getDraft(state.rfc.id), digest = draft ? draftDigest(draft.title, draft.body) : null;
    const expectedDraft = preview.candidate?.draft_digest || preview.draft_digest || null;
    if (digest !== preview.editorDigest || (expectedDraft && digest !== expectedDraft)) {
      state.error = label("编辑内容已变化。保留当前输入，请重新生成建议并检查差异。"); render(); return;
    }
    if (!preview.reason?.trim()) { state.error = label("请填写修改原因，然后应用建议。"); render(); return; }
    if (!confirm(label(preview.source_update ? "应用已检查的差异，保存 RFC 新版本，并排队更新来源？" : "应用已检查的差异并保存 RFC 新版本？"))) return;
    await perform(state, async () => {
      const payload = {thread_id: state.threadId, proposal_id: proposal.id, candidate_digest: preview.candidate_digest, reason: preview.reason.trim()};
      if (expectedDraft) payload.draft_digest = expectedDraft;
      const result = await action("chat.proposals.apply", payload);
      if (states.get(state.rfc.id) !== state) return;
      state.previews.delete(proposal.id); state.fingerprint = "";
      if (result.id) { state.rfc = result; await onApply(result, {draftDigest: digest}); }
      onNotice?.(label(result.source_update ? "RFC 新版本已保存；来源更新已排队。" : "RFC 新版本已保存。"));
      await load(state);
    });
  }
  function render() {
    layout(); const state = current;
    scope.replaceChildren(...(context ? [privateText(context.title || context.id), node("span", {class: "chat-revision"}, " · ", node("span", {}, "版本"), " ", privateText(String(context.revision || "").slice(0, 10)))] : [node("span", {}, "选择一个 RFC 继续对话。") ]));
    const options = state?.threads || [];
    if (keyOf(options.map(thread => [thread.id, thread.title])) !== threads.dataset.options) {
      threads.dataset.options = keyOf(options.map(thread => [thread.id, thread.title]));
      threads.replaceChildren(...(options.length ? options.map(thread => node("option", {value: thread.id, "data-no-translate": ""}, thread.title || thread.id.slice(0, 12))) : [node("option", {value: ""}, "新对话")]));
    }
    threads.value = state?.threadId || "";
    if (document.activeElement !== input && input.value !== (state?.input || "")) input.value = state?.input || "";
    error.textContent = state?.error || ""; error.hidden = !state?.error;
    selection.replaceChildren();
    if (state?.selection && context?.id === state.rfc.id) selection.append(node("span", {}, "当前讨论："), privateText(state.selection.title || state.selection.label || state.selection.feature_id || state.selection.criterion_id || "RFC"), control("清除选择", () => { state.selection = null; render(); }, "quiet"));
    const snapshot = state?.snapshot || {}, active = snapshot.jobs?.find(running);
    const phases = {pending: "请求已排队…", queued: "请求已排队…", running: "正在读取 RFC 上下文…", context: "正在读取 RFC 上下文…", context_read: "正在读取 RFC 上下文…", reading: "正在读取 RFC 上下文…", generating: "助手正在生成回复…", validating: "正在校验编辑建议…"};
    status.textContent = label(state?.loading ? "正在读取对话…" : state?.busy ? "正在处理…" : active ? phases[state.phases.get(active.id) || active.phase || active.status] || "助手正在生成回复…" : "");
    const fingerprint = keyOf([snapshot.messages, snapshot.proposals, snapshot.jobs, state?.earlier.length, state?.historyMore, [...(state?.live || [])], [...(state?.previews || [])].map(([id, preview]) => [id, preview.candidate_digest]), state?.busy, state && canEdit(state.rfc), currentLanguage()]);
    if (state && state.fingerprint !== fingerprint) {
      const bottom = log.scrollHeight - log.scrollTop - log.clientHeight < 80;
      const scroll = state.scroll; state.fingerprint = fingerprint;
      const items = [];
      if (!snapshot.messages?.length && !state.live.size) items.push(node("p", {class: "chat-welcome muted"}, "选择一个内容分区或路线图节点，讨论方案并检查编辑建议。"));
      if (state.historyMore ?? snapshot.has_more ?? snapshot.messages_has_more) {
        const more = control("读取更早的消息", () => perform(state, async () => {
          const messages = [...state.earlier, ...(state.snapshot.messages || [])], first = messages[0];
          if (!first) return;
          const result = await action("chat.get", {thread_id: state.threadId, limit: 100, before: first.id});
          if (states.get(state.rfc.id) !== state) return;
          const known = new Set(messages.map(message => message.id));
          state.earlier = [...(result.messages || []).filter(message => !known.has(message.id)), ...state.earlier];
          state.historyMore = result.has_more ?? result.messages_has_more ?? false; state.fingerprint = "";
        }));
        more.disabled = state.busy; items.push(more);
      }
      const seen = new Set();
      for (const message of [...state.earlier, ...(snapshot.messages || [])]) {
        if (seen.has(message.id)) continue; seen.add(message.id);
        const body = markdownBody(message.content || "", state.rfc.source?.url); body.setAttribute("data-no-translate", "");
        items.push(node("article", {class: `chat-message chat-${message.role}`}, node("h3", {}, message.role === "user" ? "你" : "RFC 助手"), body));
      }
      for (const [jobId, text] of state.live) {
        const body = node("pre", {class: "chat-stream", "data-no-translate": ""}, text);
        items.push(node("article", {class: "chat-message chat-assistant", "data-job-id": jobId}, node("h3", {}, "RFC 助手"), body));
      }
      for (const proposal of [...(snapshot.proposals || [])].sort((left, right) => left.created - right.created || left.id.localeCompare(right.id))) items.push(renderProposal(state, proposal));
      for (const job of snapshot.jobs || []) if (["failed", "requires_reauthorization", "cancelled"].includes(job.status)) {
        const retry = control("重试", () => perform(state, async () => absorb(state, await action("chat.retry", {thread_id: state.threadId, job_id: job.id}))));
        retry.disabled = state.busy || Boolean(active);
        items.push(node("div", {class: "chat-job-error"}, node("span", {}, job.status === "cancelled" ? "生成已停止。" : job.status === "requires_reauthorization" ? "授权已变化，请重新登录后重试。" : "回复生成失败，可以重试。"), job.error ? privateText(job.error) : null, retry));
      }
      log.replaceChildren(...items); applyLocale(log);
      requestAnimationFrame(() => { if (current !== state) return; log.scrollTop = bottom ? log.scrollHeight : scroll; state.scroll = log.scrollTop; });
    }
    renderControls(); applyLocale(root);
  }
  return {
    root,
    session(identity) {
      if (identity?.user_id === owner) return;
      epoch++; owner = identity?.user_id || null; clearTimeout(timer); states.clear(); current = context = null; input.value = ""; log.replaceChildren(); collapsed = true; fullscreen = false; render();
    },
    context(rfc) {
      if (current) { current.input = input.value; current.scroll = log.scrollTop; }
      context = rfc || null;
      if (rfc && owner) { if (!states.has(rfc.id)) states.set(rfc.id, newState(rfc)); const next = states.get(rfc.id); if (current !== next) input.value = next.input; current = next; current.rfc = rfc; initialize(current); }
      render();
      schedule();
    },
    select(rfc, target) { this.context(rfc); current.selection = target; current.error = ""; setCollapsed(false); render(); input.focus(); },
    mount(target = mount) { target.append(root); layout(); },
    open() { setCollapsed(false); render(); },
    refresh: render,
    reset() { this.session(null); this.mount(); },
  };
}
