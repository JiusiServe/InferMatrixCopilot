/* Hide standalone source comments without enabling source HTML or changing drafts. */
export function displayMarkdown(source) {
  const lines = String(source).split(/\r?\n/);
  const output = [];
  let fence = null;
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const marker = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
    if (fence) {
      output.push(line);
      if (marker && marker[1][0] === fence.character && marker[1].length >= fence.length && !marker[2].trim()) fence = null;
      continue;
    }
    if (marker && (marker[1][0] !== "`" || !marker[2].includes("`"))) {
      fence = {character: marker[1][0], length: marker[1].length};
      output.push(line);
      continue;
    }
    if (/^ {0,3}(?:\\)?<!--/.test(line)) {
      let end = index;
      while (end < lines.length && !lines[end].includes("-->")) end += 1;
      if (end < lines.length && !lines[end].slice(lines[end].indexOf("-->") + 3).trim()) {
        // A blank line also separates the preceding Markdown table from following prose.
        output.push("");
        index = end;
        continue;
      }
    }
    output.push(line);
  }
  return output.join("\n");
}
