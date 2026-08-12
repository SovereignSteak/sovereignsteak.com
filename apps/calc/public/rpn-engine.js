(function (root, factory) {
  const Engine = factory();
  if (typeof module === "object" && module.exports) module.exports = Engine;
  else root.RpnEngine = Engine;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const ALPHABETS = {
    2: "01",
    8: "01234567",
    10: "0123456789",
    16: "0123456789ABCDEF",
    58: "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz",
    64: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
  };

  class RpnEngine {
    constructor() {
      this.stack = [];
      this.stackBases = [];
      this.stackLeadingOnes = [];
      this.entry = null;
      this.angleMode = "rad";
      this.numberMode = "fp";
      this.base = 10;
      this.inputCleared = false;
      this.history = [];
    }

    snapshot() {
      return { stack: [...this.stack], stackBases: [...this.stackBases], stackLeadingOnes: [...this.stackLeadingOnes], entry: this.entry, angleMode: this.angleMode, numberMode: this.numberMode, base: this.base, inputCleared: this.inputCleared };
    }

    remember() {
      this.history.push(this.snapshot());
      if (this.history.length > 50) this.history.shift();
    }

    normalizeDigit(character, base = this.base) {
      if (base === 16) return character.toUpperCase();
      return character;
    }

    isValidDigit(character, base = this.base) {
      return typeof character === "string" && character.length === 1 && ALPHABETS[base].includes(this.normalizeDigit(character, base));
    }

    parseEntry(entry = this.entry, base = this.base, numberMode = this.numberMode) {
      if (entry === null) return null;
      if (base === 10) {
        if (numberMode === "int") {
          try { return BigInt(entry); } catch { throw new Error("INT mode requires a whole number"); }
        }
        const value = Number(entry);
        if (!Number.isFinite(value)) throw new Error("Invalid number");
        return value;
      }

      const negative = entry.startsWith("-");
      const digits = negative ? entry.slice(1) : entry;
      if (!digits) throw new Error("Invalid number");
      let value = 0n;
      for (const rawDigit of digits) {
        const digit = ALPHABETS[base].indexOf(this.normalizeDigit(rawDigit, base));
        if (digit < 0) throw new Error(`Invalid base-${base} digit`);
        value = value * BigInt(base) + BigInt(digit);
      }
      if (negative) value = -value;
      if (numberMode === "int") return value;
      const asNumber = Number(value);
      if (!Number.isSafeInteger(asNumber)) throw new Error("Use INT mode for values beyond the safe integer range");
      return asNumber;
    }

    formatRadix(value, base = this.base) {
      if (base === 10) return String(value);
      if (typeof value === "number" && !Number.isSafeInteger(value)) return String(value);
      const integer = typeof value === "bigint" ? value : BigInt(value);
      if (integer === 0n) return ALPHABETS[base][0];
      const negative = integer < 0n;
      let remaining = negative ? -integer : integer;
      let result = "";
      while (remaining > 0n) {
        result = ALPHABETS[base][Number(remaining % BigInt(base))] + result;
        remaining /= BigInt(base);
      }
      return negative ? `-${result}` : result;
    }

    formatValue(value, base = this.base, leadingOnes = 0) {
      if (base === 58 && leadingOnes > 0) {
        const negative = value < 0 || value < 0n;
        const magnitude = negative ? -value : value;
        if (magnitude === 0 || magnitude === 0n) return "1".repeat(leadingOnes);
        return `${negative ? "-" : ""}${"1".repeat(leadingOnes)}${this.formatRadix(magnitude, base)}`;
      }
      if (typeof value === "bigint") return this.formatRadix(value, base);
      if (base !== 10 && Number.isSafeInteger(value)) return this.formatRadix(value, base);
      const magnitude = Math.abs(value);
      if ((magnitude !== 0 && magnitude < 1e-9) || magnitude >= 1e12) return value.toExponential(10).replace(/\.0+e/, "e");
      return value.toPrecision(16).replace(/(?:\.0+|(?:(\.\d*?)0+))(?=e|$)/, "$1");
    }

    setBase(base) {
      const nextBase = Number(base);
      if (!ALPHABETS[nextBase]) throw new Error("Unsupported base");
      const entryValue = this.entry === null ? null : this.parseEntry();
      if (entryValue !== null && nextBase !== 10 && typeof entryValue === "number" && !Number.isSafeInteger(entryValue)) throw new Error("Non-integers require base 10");
      this.remember();
      this.base = nextBase;
      if (entryValue !== null) this.entry = this.formatValue(entryValue, nextBase);
    }

    effectiveStack() {
      return this.entry === null ? [...this.stack] : [...this.stack, this.parseEntry()];
    }

    inputCharacter(character) {
      if (!this.isValidDigit(character)) throw new Error(`Invalid base-${this.base} digit`);
      const digit = this.normalizeDigit(character);
      if (this.entry === null) {
        this.inputCleared = false;
        this.entry = digit;
      } else if (this.base === 10 && this.entry === "0") {
        this.entry = digit;
      } else if (this.entry.replace(/[.\-]/g, "").length < 64) {
        this.entry += digit;
      }
    }

    inputDigit(digit) { this.inputCharacter(digit); }

    decimal() {
      if (this.base !== 10 || this.numberMode === "int") throw new Error("Fractions require base 10 FP mode");
      if (this.entry === null) {
        this.inputCleared = false;
        this.entry = "0.";
      } else if (!this.entry.includes(".")) this.entry += ".";
    }

    backspace() {
      if (this.entry === null) return;
      this.entry = this.entry.slice(0, -1);
      if (this.entry === "" || this.entry === "-") {
        this.entry = null;
        this.inputCleared = false;
      }
    }

    commitEntry() {
      if (this.entry === null) return false;
      const leadingOnes = this.base === 58 ? (this.entry.replace(/^-/, "").match(/^1*/) ?? [""])[0].length : 0;
      this.stack.push(this.parseEntry());
      this.stackBases.push(this.base);
      this.stackLeadingOnes.push(leadingOnes);
      this.entry = null;
      return true;
    }

    enter() {
      this.remember();
      if (!this.commitEntry()) {
        this.stack.push(this.stack.at(-1) ?? 0);
        this.stackBases.push(this.stackBases.at(-1) ?? this.base);
        this.stackLeadingOnes.push(this.stackLeadingOnes.at(-1) ?? 0);
      }
      this.inputCleared = true;
    }

    push(value, displayBase = 10) {
      this.remember();
      this.commitEntry();
      this.stack.push(value);
      this.stackBases.push(displayBase);
      this.stackLeadingOnes.push(0);
      this.inputCleared = false;
    }

    binary(operation) {
      if (this.effectiveStack().length < 2) throw new Error("Two stack values are required");
      this.remember();
      this.commitEntry();
      const x = this.stack.pop();
      const y = this.stack.pop();
      const xBase = this.stackBases.pop();
      const yBase = this.stackBases.pop();
      this.stackLeadingOnes.pop();
      const yLeadingOnes = this.stackLeadingOnes.pop();

      if (operation === "baseConvert") {
        const targetBase = Number(x);
        if ((typeof x === "number" && !Number.isInteger(x)) || !ALPHABETS[targetBase]) return this.restoreFailedOperation(`Base must be one of ${Object.keys(ALPHABETS).join(", ")}`);
        if (typeof y === "number" && !Number.isSafeInteger(y)) return this.restoreFailedOperation("Only integers can use non-decimal bases");
        this.stack.push(y);
        this.stackBases.push(targetBase);
        this.stackLeadingOnes.push(targetBase === 58 && yBase === 58 ? yLeadingOnes : 0);
        this.inputCleared = false;
        return;
      }

      let result;
      if (this.numberMode === "int") {
        let integerX;
        let integerY;
        try {
          integerX = this.toBigInt(x);
          integerY = this.toBigInt(y);
        } catch (error) {
          return this.restoreFailedOperation(error.message);
        }
        if (operation === "+") result = integerY + integerX;
        if (operation === "-") result = integerY - integerX;
        if (operation === "*") result = integerY * integerX;
        if (operation === "/") {
          if (integerX === 0n) return this.restoreFailedOperation("Division by zero");
          result = integerY / integerX;
        }
        if (operation === "mod") {
          if (integerX === 0n) return this.restoreFailedOperation("Modulus by zero");
          result = integerY % integerX;
        }
        if (operation === "pow") {
          if (integerX < 0n || integerX > 100000n) return this.restoreFailedOperation("INT exponent must be between 0 and 100000");
          result = integerY ** integerX;
        }
        if (operation === "root") result = this.integerRoot(integerY, integerX);
        if (operation === "logBase") return this.restoreFailedOperation("Logarithms require FP mode");
      } else {
        const numberX = Number(x);
        const numberY = Number(y);
        if (operation === "+") result = numberY + numberX;
        if (operation === "-") result = numberY - numberX;
        if (operation === "*") result = numberY * numberX;
        if (operation === "/") result = numberY / numberX;
        if (operation === "mod") result = numberY % numberX;
        if (operation === "pow") result = numberY ** numberX;
        if (operation === "root") result = numberY < 0 && Number.isInteger(numberX) && Math.abs(numberX % 2) === 1 ? -(Math.abs(numberY) ** (1 / numberX)) : numberY ** (1 / numberX);
        if (operation === "logBase") result = Math.log(numberY) / Math.log(numberX);
      }
      this.finishOperation(result, yBase);
    }

    toBigInt(value) {
      if (typeof value === "bigint") return value;
      if (!Number.isSafeInteger(value)) throw new Error("INT mode requires whole, safely representable FP operands");
      return BigInt(value);
    }

    integerRoot(value, degree) {
      if (degree <= 0n) return this.restoreFailedOperation("Root degree must be positive");
      if (value < 0n) {
        if (degree % 2n === 0n) return this.restoreFailedOperation("Even root of a negative integer is invalid");
        return -this.integerRoot(-value, degree);
      }
      if (value < 2n || degree === 1n) return value;
      if (degree > BigInt(value.toString(2).length)) return 1n;
      let low = 1n;
      let high = value;
      while (low <= high) {
        const middle = (low + high) / 2n;
        const powered = middle ** degree;
        if (powered === value) return middle;
        if (powered < value) low = middle + 1n;
        else high = middle - 1n;
      }
      return high;
    }

    unary(operation) {
      if (this.effectiveStack().length < 1) throw new Error("A stack value is required");
      if (this.numberMode === "int") throw new Error("This function requires FP mode");
      this.remember();
      this.commitEntry();
      const x = Number(this.stack.pop());
      const xBase = this.stackBases.pop();
      this.stackLeadingOnes.pop();
      const angle = this.angleMode === "deg" ? x * Math.PI / 180 : x;
      const fromRadians = (value) => this.angleMode === "deg" ? value * 180 / Math.PI : value;
      const operations = {
        sin: () => Math.sin(angle),
        cos: () => Math.cos(angle),
        tan: () => Math.tan(angle),
        asin: () => fromRadians(Math.asin(x)),
        acos: () => fromRadians(Math.acos(x)),
        atan: () => fromRadians(Math.atan(x)),
        reciprocal: () => 1 / x,
        angleConvert: () => this.angleMode === "rad" ? x * 180 / Math.PI : x * Math.PI / 180
      };
      this.finishOperation(operations[operation](), xBase);
    }

    restoreFailedOperation(message) {
      const previous = this.history.pop();
      this.stack = previous.stack;
      this.stackBases = previous.stackBases;
      this.stackLeadingOnes = previous.stackLeadingOnes;
      this.entry = previous.entry;
      this.angleMode = previous.angleMode;
      this.numberMode = previous.numberMode;
      this.base = previous.base;
      this.inputCleared = previous.inputCleared;
      throw new Error(message);
    }

    finishOperation(value, displayBase = 10) {
      if (typeof value === "number" && !Number.isFinite(value)) {
        return this.restoreFailedOperation("Invalid result");
      }
      this.stack.push(value);
      this.stackBases.push(typeof value === "bigint" || Number.isSafeInteger(value) ? displayBase : 10);
      this.stackLeadingOnes.push(0);
      this.inputCleared = false;
    }

    sign() {
      if (this.entry !== null) {
        this.entry = this.entry.startsWith("-") ? this.entry.slice(1) : `-${this.entry}`;
        return;
      }
      if (!this.stack.length) return;
      this.remember();
      if (typeof this.stack[this.stack.length - 1] === "bigint") this.stack[this.stack.length - 1] = -this.stack[this.stack.length - 1];
      else this.stack[this.stack.length - 1] *= -1;
      this.stackLeadingOnes[this.stackLeadingOnes.length - 1] = 0;
      this.inputCleared = false;
    }

    drop() {
      if (this.entry === null && !this.stack.length) return;
      this.remember();
      if (this.entry !== null) this.entry = null;
      else {
        this.stack.pop();
        this.stackBases.pop();
        this.stackLeadingOnes.pop();
      }
      this.inputCleared = false;
    }

    swap() {
      if (this.effectiveStack().length < 2) throw new Error("Two stack values are required");
      this.remember();
      this.commitEntry();
      const x = this.stack.pop();
      const y = this.stack.pop();
      const xBase = this.stackBases.pop();
      const yBase = this.stackBases.pop();
      const xLeadingOnes = this.stackLeadingOnes.pop();
      const yLeadingOnes = this.stackLeadingOnes.pop();
      this.stack.push(x, y);
      this.stackBases.push(xBase, yBase);
      this.stackLeadingOnes.push(xLeadingOnes, yLeadingOnes);
      this.inputCleared = false;
    }

    clear() {
      if (!this.stack.length && this.entry === null) return;
      this.remember();
      this.stack = [];
      this.stackBases = [];
      this.stackLeadingOnes = [];
      this.entry = null;
      this.inputCleared = false;
    }

    toggleAngleMode() { this.angleMode = this.angleMode === "deg" ? "rad" : "deg"; }

    toggleNumberMode() {
      let entryValue = null;
      if (this.entry !== null) entryValue = this.parseEntry();
      const nextMode = this.numberMode === "fp" ? "int" : "fp";
      if (entryValue !== null && nextMode === "int" && !Number.isSafeInteger(entryValue)) throw new Error("INT mode requires a whole number");
      if (entryValue !== null && nextMode === "fp" && typeof entryValue === "bigint" && (entryValue > BigInt(Number.MAX_SAFE_INTEGER) || entryValue < BigInt(Number.MIN_SAFE_INTEGER))) {
        throw new Error("Entry is too large for lossless FP conversion");
      }
      this.remember();
      this.numberMode = nextMode;
      if (entryValue !== null) {
        const converted = nextMode === "int" ? BigInt(entryValue) : Number(entryValue);
        this.entry = this.formatValue(converted, this.base);
      }
    }

    undo() {
      const previous = this.history.pop();
      if (!previous) return;
      this.stack = previous.stack;
      this.stackBases = previous.stackBases;
      this.stackLeadingOnes = previous.stackLeadingOnes;
      this.entry = previous.entry;
      this.angleMode = previous.angleMode;
      this.numberMode = previous.numberMode;
      this.base = previous.base;
      this.inputCleared = previous.inputCleared;
    }

    replaceEntry(depth, text) {
      const cleaned = String(text).trim();
      if (!cleaned) throw new Error("Clipboard does not contain a number");
      if (depth === 0) {
        this.parseEntry(cleaned, this.base);
        this.entry = this.base === 16 ? cleaned.toUpperCase() : cleaned;
        this.inputCleared = false;
        return;
      }
      const index = this.stack.length - depth;
      if (index < 0 || index >= this.stack.length) throw new Error("Stack entry no longer exists");
      const entryBase = this.stackBases[index];
      const entryMode = typeof this.stack[index] === "bigint" ? "int" : "fp";
      const value = this.parseEntry(cleaned, entryBase, entryMode);
      this.remember();
      this.stack[index] = value;
      this.stackLeadingOnes[index] = entryBase === 58 ? (cleaned.replace(/^-/, "").match(/^1*/) ?? [""])[0].length : 0;
    }
  }

  return RpnEngine;
});
