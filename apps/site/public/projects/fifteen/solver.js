const SIZE = 4;
const GOAL = "123456789abcdef0";
const OPPOSITE = { up: "down", down: "up", left: "right", right: "left" };

class MinHeap {
  constructor() { this.items = []; }
  push(node) {
    const items = this.items;
    items.push(node);
    let index = items.length - 1;
    while (index > 0) {
      const parent = (index - 1) >> 1;
      if (items[parent].score <= node.score) break;
      items[index] = items[parent];
      index = parent;
    }
    items[index] = node;
  }
  pop() {
    const items = this.items;
    const root = items[0];
    const last = items.pop();
    if (items.length && last) {
      let index = 0;
      while (true) {
        let child = index * 2 + 1;
        if (child >= items.length) break;
        if (child + 1 < items.length && items[child + 1].score < items[child].score) child += 1;
        if (items[child].score >= last.score) break;
        items[index] = items[child];
        index = child;
      }
      items[index] = last;
    }
    return root;
  }
  get length() { return this.items.length; }
}

function encode(board) { return board.map((value) => value.toString(16)).join(""); }

function heuristic(board) {
  let distance = 0;
  for (let index = 0; index < board.length; index += 1) {
    const value = board[index];
    if (!value) continue;
    const goal = value - 1;
    distance += Math.abs(Math.floor(index / SIZE) - Math.floor(goal / SIZE));
    distance += Math.abs(index % SIZE - goal % SIZE);
  }

  let conflicts = 0;
  for (let row = 0; row < SIZE; row += 1) {
    for (let left = 0; left < SIZE; left += 1) {
      const a = board[row * SIZE + left];
      if (!a || Math.floor((a - 1) / SIZE) !== row) continue;
      for (let right = left + 1; right < SIZE; right += 1) {
        const b = board[row * SIZE + right];
        if (b && Math.floor((b - 1) / SIZE) === row && a > b) conflicts += 2;
      }
    }
  }
  for (let column = 0; column < SIZE; column += 1) {
    for (let top = 0; top < SIZE; top += 1) {
      const a = board[top * SIZE + column];
      if (!a || (a - 1) % SIZE !== column) continue;
      for (let bottom = top + 1; bottom < SIZE; bottom += 1) {
        const b = board[bottom * SIZE + column];
        if (b && (b - 1) % SIZE === column && a > b) conflicts += 2;
      }
    }
  }
  return distance + conflicts;
}

function neighbors(node) {
  const blank = node.blank;
  const row = Math.floor(blank / SIZE);
  const column = blank % SIZE;
  const candidates = [];
  if (row < SIZE - 1) candidates.push([blank + SIZE, "up"]);
  if (row > 0) candidates.push([blank - SIZE, "down"]);
  if (column < SIZE - 1) candidates.push([blank + 1, "left"]);
  if (column > 0) candidates.push([blank - 1, "right"]);
  return candidates.filter(([, direction]) => direction !== OPPOSITE[node.direction]).map(([tileIndex, direction]) => {
    const board = node.board.slice();
    board[blank] = board[tileIndex];
    board[tileIndex] = 0;
    return { board, blank: tileIndex, direction };
  });
}

function pathTo(node) {
  const path = [];
  while (node.parent) {
    path.push(node.direction);
    node = node.parent;
  }
  return path.reverse();
}

function solve(initial, budgetMs = 350) {
  const deadline = performance.now() + budgetMs;
  const startH = heuristic(initial);
  const start = { board: initial, blank: initial.indexOf(0), direction: null, parent: null, g: 0, h: startH, score: startH * 1.65 };
  const open = new MinHeap();
  const costs = new Map([[encode(initial), 0]]);
  open.push(start);
  let best = start;
  let expanded = 0;

  while (open.length && performance.now() < deadline && expanded < 180000) {
    const node = open.pop();
    const key = encode(node.board);
    if (costs.get(key) !== node.g) continue;
    if (key === GOAL) return { path: pathTo(node), complete: true, expanded };
    if (node.h < best.h || (node.h === best.h && node.g < best.g)) best = node;
    expanded += 1;

    for (const next of neighbors(node)) {
      const nextKey = encode(next.board);
      const g = node.g + 1;
      if ((costs.get(nextKey) ?? Infinity) <= g) continue;
      const h = heuristic(next.board);
      const child = { ...next, parent: node, g, h, score: g + h * 1.65 };
      costs.set(nextKey, g);
      open.push(child);
    }
  }
  return { path: pathTo(best), complete: false, expanded };
}

self.addEventListener("message", (event) => {
  const { id, board } = event.data;
  try {
    self.postMessage({ id, ...solve(board) });
  } catch {
    self.postMessage({ id, path: [], complete: false, expanded: 0 });
  }
});
