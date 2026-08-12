const engine = new RpnEngine();
const calculator = document.querySelector(".calculator");
const stackList = document.querySelector("#stack");
const stackToggle = document.querySelector("#stack-toggle");
const angleMode = document.querySelector("#angle-mode");
const numberMode = document.querySelector("#number-mode");
const baseSelect = document.querySelector("#base-select");
const status = document.querySelector("#status");
const shortcuts = document.querySelector("#shortcuts");
const shortcutsToggle = document.querySelector("#shortcuts-toggle");
let showFullStack = false;

function render() {
  const rows = [
    { value: engine.entry ?? "", base: engine.base, label: "0", depth: 0 },
    ...engine.stack.slice().reverse().map((value, index) => ({
      value,
      base: engine.stackBases[engine.stack.length - 1 - index],
      leadingOnes: engine.stackLeadingOnes[engine.stack.length - 1 - index],
      label: String(index + 1),
      depth: index + 1
    }))
  ];

  const visible = showFullStack ? rows : rows.slice(0, 4);
  stackList.replaceChildren();

  visible.forEach((item, index) => {
    const row = document.createElement("li");
    const level = document.createElement("span");
    const number = document.createElement("output");
    const base = document.createElement("span");
    const actions = document.createElement("span");
    level.className = "stack-level";
    level.textContent = item.label;
    number.textContent = typeof item.value === "string" ? item.value : engine.formatValue(item.value, item.base, item.leadingOnes);
    base.className = "entry-base";
    base.textContent = `b${item.base}`;
    actions.className = "entry-actions";
    actions.innerHTML = `<button type="button" data-clipboard="copy" data-depth="${item.depth}" title="Copy row ${item.label}">Copy</button><button type="button" data-clipboard="paste" data-depth="${item.depth}" title="Replace row ${item.label} from clipboard">Paste</button>`;
    row.className = index === 0 ? "active" : "";
    row.append(level, number, base, actions);
    stackList.append(row);
  });

  stackToggle.hidden = rows.length <= 4;
  stackToggle.textContent = showFullStack ? "Show four" : `Show all (${rows.length})`;
  stackToggle.setAttribute("aria-expanded", String(showFullStack));
  angleMode.textContent = engine.angleMode.toUpperCase();
  angleMode.setAttribute("aria-label", `Angle mode: ${engine.angleMode === "deg" ? "degrees" : "radians"}`);
  numberMode.textContent = engine.numberMode.toUpperCase();
  numberMode.setAttribute("aria-label", `Numeric mode: ${engine.numberMode === "fp" ? "floating point" : "arbitrary-precision integer"}`);
  const angleConvert = document.querySelector('[data-unary="angleConvert"]');
  angleConvert.textContent = engine.angleMode === "rad" ? "rad→deg" : "deg→rad";
  angleConvert.title = engine.angleMode === "rad" ? "Convert radians to degrees" : "Convert degrees to radians";
  baseSelect.value = String(engine.base);
  document.querySelectorAll("[data-number]").forEach((button) => {
    button.disabled = !engine.isValidDigit(button.dataset.number);
  });
  document.querySelector('[data-action="decimal"]').disabled = engine.base !== 10 || engine.numberMode === "int";
  document.querySelectorAll("[data-fp-only]").forEach((button) => {
    button.disabled = engine.numberMode === "int";
  });
}

function perform(action) {
  status.textContent = "";
  try { action(); } catch (error) { status.textContent = error.message; }
  render();
}

calculator.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button || button.dataset.clipboard) return;
  if (button.dataset.number !== undefined) perform(() => engine.inputDigit(button.dataset.number));
  if (button.dataset.binary) perform(() => engine.binary(button.dataset.binary));
  if (button.dataset.unary) perform(() => engine.unary(button.dataset.unary));
  if (button.dataset.action === "decimal") perform(() => engine.decimal());
  if (button.dataset.action === "enter") perform(() => engine.enter());
  if (button.dataset.action === "clear") perform(() => engine.clear());
  if (button.dataset.action === "drop") perform(() => engine.drop());
  if (button.dataset.action === "swap") perform(() => engine.swap());
  if (button.dataset.action === "undo") perform(() => engine.undo());
  if (button.dataset.action === "pi") perform(() => engine.push(Math.PI));
  if (button.dataset.action === "e") perform(() => engine.push(Math.E));
  if (button.dataset.action === "sign") perform(() => engine.sign());
});

angleMode.addEventListener("click", () => perform(() => engine.toggleAngleMode()));
numberMode.addEventListener("click", () => perform(() => engine.toggleNumberMode()));
baseSelect.addEventListener("change", () => {
  perform(() => engine.setBase(baseSelect.value));
  baseSelect.blur();
});
stackToggle.addEventListener("click", () => { showFullStack = !showFullStack; render(); });
shortcutsToggle.addEventListener("click", () => {
  const opening = shortcuts.hidden;
  shortcuts.hidden = !opening;
  shortcutsToggle.setAttribute("aria-expanded", String(opening));
  shortcutsToggle.textContent = opening ? "Hide keyboard help" : "Keyboard help";
});

document.addEventListener("keydown", (event) => {
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.target.matches("select")) return;
  const key = event.key;
  let action = null;
  const digitTakesPriority = engine.isValidDigit(key);
  if (digitTakesPriority) action = () => engine.inputCharacter(key);
  else if (key === "." || key === ",") action = () => engine.decimal();
  else if (["+", "-", "*", "/"].includes(key)) action = () => engine.binary(key);
  else if (key === "%") action = () => engine.binary("mod");
  else if (key === "Enter" || key === "=") action = () => engine.enter();
  else if (key === "Backspace") action = () => engine.backspace();
  else if (key === "Delete") action = () => engine.drop();
  else if (key === "Escape") action = () => engine.clear();
  else if (key === "^") action = () => engine.binary("pow");
  else if (key === "_") action = () => engine.sign();
  if (!action) return;
  event.preventDefault();
  perform(action);
});

stackList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-clipboard]");
  if (!button) return;
  const depth = Number(button.dataset.depth);
  const row = button.closest("li");
  try {
    if (button.dataset.clipboard === "copy") {
      await navigator.clipboard.writeText(row.querySelector("output").textContent);
      status.textContent = `Copied row ${depth}`;
    } else {
      const text = await navigator.clipboard.readText();
      engine.replaceEntry(depth, text);
      status.textContent = `Replaced row ${depth}`;
      render();
    }
  } catch (error) {
    status.textContent = error.message || "Clipboard access was denied";
  }
});

render();
