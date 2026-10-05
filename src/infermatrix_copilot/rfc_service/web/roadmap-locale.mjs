/* Public language preference only; translated RFC text stays in session memory. */
let language = new URL(location.href).searchParams.get("lang");
try { language ||= localStorage.getItem("imrfc.language"); } catch {}
language = language === "en" ? "en" : "zh";
let interfaceStrings = {}, privateStrings = {}, templates = [], version = 0;
const originals = new WeakMap(), memo = new Map();
export const currentLanguage = () => language;
const escape = value => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function reset() {
  version += 1; memo.clear();
  templates = Object.entries(interfaceStrings).filter(([source]) => /⟪S\d+⟫/.test(source)).map(([source, translated]) => {
    const slots = [], parts = source.split(/(⟪S\d+⟫)/);
    return {pattern: new RegExp("^" + parts.map(part => {
      if (/^⟪S\d+⟫$/.test(part)) { slots.push(part); return "([\\s\\S]*?)"; }
      return escape(part);
    }).join("") + "$"), slots, translated};
  });
}

export function localizeText(value) {
  if (typeof value !== "string" || !value.trim()) return value;
  if (memo.has(value)) return memo.get(value);
  const key = value.trim();
  let result = privateStrings[key] || interfaceStrings[key];
  if (!result && language === "en") {
    for (const template of templates) {
      const match = key.match(template.pattern);
      if (!match) continue;
      result = template.translated;
      template.slots.forEach((slot, index) => { result = result.split(slot).join(localizeText(match[index + 1])); });
      break;
    }
  }
  const answer = result ? value.slice(0, value.indexOf(key)) + result + value.slice(value.indexOf(key) + key.length) : value;
  memo.set(value, answer);
  return answer;
}

export function setTranslations(snapshot, replace = true) {
  if (replace) privateStrings = {};
  if (snapshot?.language === language) Object.assign(privateStrings, snapshot.strings || {});
  reset(); applyLocale(document.body);
}

export function applyLocale(root) {
  if (!root) return;
  const visit = node => {
    if (node.nodeType === Node.TEXT_NODE) {
      if (node.parentElement?.closest("code,pre,textarea,input,[data-no-translate],#identity-name,#issued-secret")) return;
      let state = originals.get(node);
      if (!state || node.nodeValue !== state.applied) state = {source: node.nodeValue};
      state.applied = localizeText(state.source);
      originals.set(node, state);
      if (node.nodeValue !== state.applied) node.nodeValue = state.applied;
    } else if (node.nodeType === Node.ELEMENT_NODE && !node.closest("[data-no-translate]")) {
      let state = originals.get(node) || {};
      for (const name of ["placeholder", "aria-label", "title"]) {
        const value = node.getAttribute(name);
        if (value === null) continue;
        if (!state[name] || value !== state[name].applied) state[name] = {source: value};
        state[name].applied = localizeText(state[name].source);
        if (value !== state[name].applied) node.setAttribute(name, state[name].applied);
      }
      originals.set(node, state);
    }
  };
  visit(root);
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) visit(walker.currentNode);
}

export async function initializeLocale() {
  document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  const response = await fetch(`/roadmap-languages.json?language=${language}`, {cache: "no-store"});
  if (response.ok) interfaceStrings = (await response.json()).strings || {};
  reset(); applyLocale(document.body);
  document.querySelectorAll("[data-language]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.language === language)));
}

export async function changeLanguage(next) {
  language = next === "en" ? "en" : "zh";
  privateStrings = {};
  try { localStorage.setItem("imrfc.language", language); } catch {}
  const url = new URL(location.href); url.searchParams.set("lang", language); history.replaceState(null, "", url);
  await initializeLocale();
}

const observer = new MutationObserver(records => {
  const roots = new Set();
  for (const record of records) {
    if (record.type === "childList") for (const node of record.addedNodes) roots.add(node);
    else roots.add(record.target);
  }
  for (const root of roots) applyLocale(root);
});
observer.observe(document.body, {subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ["placeholder", "aria-label", "title"]});
setInterval(() => initializeLocale().catch(() => {}), 30000);
