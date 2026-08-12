(() => {
  const SIZE = 4;
  const SOLVED = [...Array(15)].map((_, index) => index + 1).concat(0);
  const board = document.getElementById("board");
  const movesDisplay = document.getElementById("moves");
  const timeDisplay = document.getElementById("time");
  const status = document.getElementById("puzzle-status");
  const cheatToggle = document.getElementById("cheat-toggle");
  const modeButtons = [...document.querySelectorAll("[data-mode]")];
  let tiles = [...SOLVED];
  let moves = 0;
  let startedAt = 0;
  let timer = null;
  let won = false;
  let cheatEnabled = false;
  let cheatPath = [];
  let solveRequest = 0;
  const solver = new Worker("/projects/fifteen/solver.js");

  const blank = document.createElement("button");
  blank.type = "button";
  blank.className = "blank";
  blank.setAttribute("aria-label", "Ask for a helpful move");
  blank.addEventListener("click", requestCheatMove);
  blank.addEventListener("pointerup", () => blank.blur());
  board.append(blank);

  const tileElements = new Map();
  for (let value = 1; value < 16; value += 1) {
    const tile = document.createElement("button");
    tile.type = "button";
    tile.className = "tile";
    tile.dataset.value = value;
    tile.setAttribute("aria-label", `Tile ${value}`);
    tile.innerHTML = `<span>${value}</span>`;
    const solvedIndex = value - 1;
    const imageHeightInTiles = SIZE * 1168 / 784;
    const cropInTiles = (imageHeightInTiles - SIZE) / 2;
    const imageColumn = solvedIndex % SIZE;
    const imageRow = Math.floor(solvedIndex / SIZE);
    tile.style.backgroundPosition = `${imageColumn * 100 / 3}% ${(imageRow + cropInTiles) * 100 / (imageHeightInTiles - 1)}%`;
    tile.addEventListener("click", () => slideToTile(value));
    tile.addEventListener("pointerup", () => tile.blur());
    tileElements.set(value, tile);
    board.append(tile);
  }

  function adjacentIndices(index) {
    const row = Math.floor(index / SIZE);
    const column = index % SIZE;
    const result = [];
    if (row > 0) result.push(index - SIZE);
    if (row < SIZE - 1) result.push(index + SIZE);
    if (column > 0) result.push(index - 1);
    if (column < SIZE - 1) result.push(index + 1);
    return result;
  }

  function render() {
    tiles.forEach((value, index) => {
      if (!value) return;
      const row = Math.floor(index / SIZE);
      const column = index % SIZE;
      tileElements.get(value).style.transform = `translate(${column * 100}%, ${row * 100}%)`;
    });
    const emptyIndex = tiles.indexOf(0);
    blank.style.transform = `translate(${(emptyIndex % SIZE) * 100}%, ${Math.floor(emptyIndex / SIZE) * 100}%)`;
  }

  function startClock() {
    if (startedAt) return;
    startedAt = Date.now();
    timer = window.setInterval(updateTime, 1000);
  }

  function updateTime() {
    const seconds = startedAt ? Math.floor((Date.now() - startedAt) / 1000) : 0;
    timeDisplay.textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  }

  function isSolved() { return tiles.every((value, index) => value === SOLVED[index]); }

  function completeMove() {
    moves += 1;
    movesDisplay.textContent = moves;
    render();
    if (isSolved()) {
      won = true;
      window.clearInterval(timer);
      updateTime();
      status.textContent = `Solved in ${moves} moves and ${timeDisplay.textContent}.`;
      status.classList.add("won");
    }
  }

  function invalidateCheatPath() {
    cheatPath = [];
    solveRequest += 1;
    board.classList.remove("thinking");
  }

  function slideToTile(value, fromCheat = false) {
    if (won) return;
    const tileIndex = tiles.indexOf(value);
    let emptyIndex = tiles.indexOf(0);
    const sameRow = Math.floor(tileIndex / SIZE) === Math.floor(emptyIndex / SIZE);
    const sameColumn = tileIndex % SIZE === emptyIndex % SIZE;
    if (!sameRow && !sameColumn) return;
    if (!fromCheat) invalidateCheatPath();

    const step = sameRow
      ? (tileIndex > emptyIndex ? 1 : -1)
      : (tileIndex > emptyIndex ? SIZE : -SIZE);
    startClock();

    while (emptyIndex !== tileIndex) {
      const nextIndex = emptyIndex + step;
      tiles[emptyIndex] = tiles[nextIndex];
      tiles[nextIndex] = 0;
      emptyIndex = nextIndex;
    }

    completeMove();
  }

  function moveTiles(direction, fromCheat = false) {
    const emptyIndex = tiles.indexOf(0);
    const row = Math.floor(emptyIndex / SIZE);
    const column = emptyIndex % SIZE;
    let tileIndex = -1;
    if (direction === "up" && row < SIZE - 1) tileIndex = emptyIndex + SIZE;
    if (direction === "down" && row > 0) tileIndex = emptyIndex - SIZE;
    if (direction === "left" && column < SIZE - 1) tileIndex = emptyIndex + 1;
    if (direction === "right" && column > 0) tileIndex = emptyIndex - 1;
    if (tileIndex >= 0) slideToTile(tiles[tileIndex], fromCheat);
  }

  function applyCheatPath() {
    if (!cheatPath.length || won) return;
    const direction = cheatPath[0];
    let count = 1;
    while (count < cheatPath.length && cheatPath[count] === direction && count < SIZE - 1) count += 1;
    const emptyIndex = tiles.indexOf(0);
    const offsets = { up: SIZE, down: -SIZE, left: 1, right: -1 };
    const tileIndex = emptyIndex + offsets[direction] * count;
    if (tileIndex < 0 || tileIndex >= tiles.length) {
      invalidateCheatPath();
      return;
    }
    cheatPath.splice(0, count);
    slideToTile(tiles[tileIndex], true);
    if (!won) status.textContent = cheatPath.length ? "Helpful move made. Click the blank again to continue." : "Helpful move made. I'll recalculate from here next time.";
  }

  function requestCheatMove() {
    if (!cheatEnabled || won || board.classList.contains("thinking")) return;
    if (cheatPath.length) {
      applyCheatPath();
      return;
    }
    const id = ++solveRequest;
    board.classList.add("thinking");
    status.textContent = "Thinking…";
    solver.postMessage({ id, board: tiles.slice() });
  }

  solver.addEventListener("message", (event) => {
    if (event.data.id !== solveRequest || !cheatEnabled) return;
    board.classList.remove("thinking");
    cheatPath = event.data.path;
    if (!cheatPath.length) {
      status.textContent = isSolved() ? "Already solved." : "I couldn't find a useful continuation quickly. Try again.";
      return;
    }
    applyCheatPath();
  });

  function newGame() {
    invalidateCheatPath();
    tiles = [...SOLVED];
    let emptyIndex = 15;
    let previousIndex = -1;
    for (let step = 0; step < 240; step += 1) {
      const choices = adjacentIndices(emptyIndex).filter((index) => index !== previousIndex);
      const nextIndex = choices[Math.floor(Math.random() * choices.length)];
      [tiles[emptyIndex], tiles[nextIndex]] = [tiles[nextIndex], tiles[emptyIndex]];
      previousIndex = emptyIndex;
      emptyIndex = nextIndex;
    }
    if (isSolved()) return newGame();
    moves = 0;
    startedAt = 0;
    won = false;
    window.clearInterval(timer);
    movesDisplay.textContent = "0";
    timeDisplay.textContent = "0:00";
    status.textContent = "Move tiles with WASD or arrow keys. Click any aligned tile to slide its row or column.";
    status.classList.remove("won");
    render();
  }

  document.getElementById("new-game").addEventListener("click", newGame);
  cheatToggle.addEventListener("click", () => {
    cheatEnabled = !cheatEnabled;
    invalidateCheatPath();
    board.classList.toggle("cheat", cheatEnabled);
    cheatToggle.setAttribute("aria-pressed", String(cheatEnabled));
    cheatToggle.textContent = `Cheat: ${cheatEnabled ? "on" : "off"}`;
    if (won) return;
    status.textContent = cheatEnabled
      ? "Click the highlighted blank for a helpful move. You can keep playing normally at any time."
      : "Move tiles with WASD or arrow keys. Click any aligned tile to slide its row or column.";
  });
  modeButtons.forEach((button) => button.addEventListener("click", () => {
    const mode = button.dataset.mode;
    board.classList.toggle("image", mode === "image");
    board.classList.toggle("numbers", mode === "numbers");
    modeButtons.forEach((candidate) => {
      const selected = candidate === button;
      candidate.classList.toggle("active", selected);
      candidate.setAttribute("aria-pressed", String(selected));
    });
  }));

  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    const directions = { w: "up", ArrowUp: "up", s: "down", ArrowDown: "down", a: "left", ArrowLeft: "left", d: "right", ArrowRight: "right" };
    const direction = directions[event.key] || directions[event.key.toLowerCase()];
    if (!direction) return;
    event.preventDefault();
    moveTiles(direction);
  });

  newGame();
})();
