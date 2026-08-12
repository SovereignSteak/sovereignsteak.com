const test = require("node:test");
const assert = require("node:assert/strict");
const RpnEngine = require("../public/rpn-engine.js");

function type(engine, value) {
  for (const character of String(value)) {
    if (character === ".") engine.decimal();
    else engine.inputDigit(character);
  }
}

test("performs binary operations in Y op X order", () => {
  const engine = new RpnEngine();
  type(engine, 10);
  engine.enter();
  type(engine, 4);
  engine.binary("-");
  assert.deepEqual(engine.stack, [6]);
});

test("Enter commits X and clears the input register", () => {
  const engine = new RpnEngine();
  type(engine, 7);
  engine.enter();
  assert.deepEqual(engine.stack, [7]);
  assert.equal(engine.entry, null);
  assert.equal(engine.inputCleared, true);
  type(engine, 3);
  assert.deepEqual(engine.effectiveStack(), [7, 3]);
});

test("preserves a trailing decimal in the live entry", () => {
  const engine = new RpnEngine();
  type(engine, 12);
  engine.decimal();
  assert.equal(engine.entry, "12.");
});

test("effective stack includes the number being entered", () => {
  const engine = new RpnEngine();
  type(engine, 12.5);
  assert.deepEqual(engine.effectiveStack(), [12.5]);
  assert.equal(engine.entry, "12.5");
});

test("scientific functions respect degree and radian modes", () => {
  const engine = new RpnEngine();
  engine.push(Math.PI / 6);
  engine.unary("sin");
  assert.ok(Math.abs(engine.stack.at(-1) - 0.5) < 1e-12);
  engine.clear();
  engine.toggleAngleMode();
  type(engine, 90);
  engine.unary("sin");
  assert.equal(engine.stack.at(-1), 1);
});

test("supports arbitrary powers and roots in Y op X order", () => {
  const engine = new RpnEngine();
  type(engine, 2);
  engine.enter();
  type(engine, 8);
  engine.binary("pow");
  assert.deepEqual(engine.stack, [256]);
  engine.clear();
  type(engine, 27);
  engine.enter();
  type(engine, 3);
  engine.binary("root");
  assert.deepEqual(engine.stack, [3]);
});

test("converts entry and display across supported bases", () => {
  const engine = new RpnEngine();
  type(engine, 255);
  engine.setBase(16);
  assert.equal(engine.entry, "FF");
  engine.enter();
  assert.equal(engine.formatValue(engine.stack.at(-1)), "FF");
  engine.setBase(2);
  assert.equal(engine.stackBases.at(-1), 16);
  assert.equal(engine.formatValue(engine.stack.at(-1), engine.stackBases.at(-1)), "FF");
});

test("base conversion retags Y with the base supplied in X", () => {
  const engine = new RpnEngine();
  type(engine, 255);
  engine.enter();
  type(engine, 16);
  engine.binary("baseConvert");
  assert.deepEqual(engine.stack, [255]);
  assert.deepEqual(engine.stackBases, [16]);
  assert.equal(engine.formatValue(engine.stack[0], engine.stackBases[0]), "FF");
});

test("clipboard replacement preserves stack depth and entry base", () => {
  const engine = new RpnEngine();
  engine.push(255, 16);
  assert.throws(() => engine.replaceEntry(1, "not-a-number"), /Invalid base-16 digit/);
  engine.replaceEntry(1, "10");
  assert.deepEqual(engine.stack, [16]);
  assert.deepEqual(engine.stackBases, [16]);
});

test("uses Bitcoin Base58 and RFC 4648 Base64 alphabets", () => {
  const engine = new RpnEngine();
  engine.push(57);
  engine.setBase(58);
  assert.equal(engine.formatValue(57), "z");
  engine.setBase(64);
  assert.equal(engine.formatValue(63), "/");
  assert.equal(engine.formatValue(64), "BA");
});

test("matches Bitcoin Base58 integer vectors", () => {
  const engine = new RpnEngine();
  assert.equal(engine.formatValue(0x61n, 58), "2g");
  assert.equal(engine.formatValue(0x626262n, 58), "a3gV");
  assert.equal(engine.formatValue(0x636363n, 58), "aPEr");
});

test("preserves Bitcoin Base58 leading-zero byte markers", () => {
  const engine = new RpnEngine();
  engine.toggleNumberMode();
  engine.setBase(58);
  for (const digit of "1112") engine.inputCharacter(digit);
  engine.enter();
  assert.equal(engine.stack.at(-1), 1n);
  assert.equal(engine.stackLeadingOnes.at(-1), 3);
  assert.equal(engine.formatValue(engine.stack.at(-1), 58, engine.stackLeadingOnes.at(-1)), "1112");
  engine.replaceEntry(1, "1111");
  assert.equal(engine.stack.at(-1), 0n);
  assert.equal(engine.formatValue(engine.stack.at(-1), 58, engine.stackLeadingOnes.at(-1)), "1111");
});

test("computes arbitrary-base logarithms in Y log base X order", () => {
  const engine = new RpnEngine();
  type(engine, 8);
  engine.enter();
  type(engine, 2);
  engine.binary("logBase");
  assert.deepEqual(engine.stack, [3]);
});

test("inverse trig results follow the selected angle mode", () => {
  const engine = new RpnEngine();
  type(engine, 1);
  engine.unary("asin");
  assert.ok(Math.abs(engine.stack.at(-1) - Math.PI / 2) < 1e-12);
  engine.clear();
  engine.toggleAngleMode();
  type(engine, 1);
  engine.unary("asin");
  assert.equal(engine.stack.at(-1), 90);
});

test("converts between radians and degrees according to angle mode", () => {
  const engine = new RpnEngine();
  engine.push(Math.PI);
  engine.unary("angleConvert");
  assert.equal(engine.stack.at(-1), 180);
  engine.clear();
  engine.toggleAngleMode();
  engine.push(180);
  engine.unary("angleConvert");
  assert.equal(engine.stack.at(-1), Math.PI);
});

test("FP operations retain native double precision without result rounding", () => {
  const engine = new RpnEngine();
  engine.push(1);
  engine.push(3);
  engine.binary("/");
  assert.equal(engine.stack.at(-1), 1 / 3);
});

test("INT mode provides arbitrary-precision integer arithmetic and conversion", () => {
  const engine = new RpnEngine();
  engine.toggleNumberMode();
  type(engine, "123456789012345678901234567890");
  engine.enter();
  type(engine, 10);
  engine.binary("*");
  assert.equal(engine.stack.at(-1), 1234567890123456789012345678900n);
  assert.equal(engine.formatValue(engine.stack.at(-1), 16), "F951A9FA3A286C94F0E766C34");
});

test("INT division truncates and modulus returns the remainder", () => {
  const engine = new RpnEngine();
  engine.toggleNumberMode();
  engine.setBase(16);
  for (const digit of "DEADBEEF") engine.inputCharacter(digit);
  engine.enter();
  engine.inputCharacter("2");
  engine.binary("/");
  assert.equal(engine.formatValue(engine.stack.at(-1), 16), "6F56DF77");
  engine.clear();
  for (const digit of "DEADBEEF") engine.inputCharacter(digit);
  engine.enter();
  engine.inputCharacter("2");
  engine.binary("mod");
  assert.equal(engine.stack.at(-1), 1n);
});

test("invalid operations preserve the stack", () => {
  const engine = new RpnEngine();
  type(engine, 9);
  engine.enter();
  type(engine, 0);
  assert.throws(() => engine.binary("/"), /Invalid result/);
  assert.deepEqual(engine.effectiveStack(), [9, 0]);
});

test("undo restores the previous stack", () => {
  const engine = new RpnEngine();
  engine.push(2);
  engine.push(3);
  engine.binary("+");
  assert.deepEqual(engine.stack, [5]);
  engine.undo();
  assert.deepEqual(engine.stack, [2, 3]);
});
