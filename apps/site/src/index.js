const MAX_BODY_BYTES = 16_384;
const SUCCESS_MESSAGE = "Thanks—your message has been sent.";

function response(message, status = 200) {
  return Response.json({ message }, {
    status,
    headers: {
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff"
    }
  });
}

async function readLimitedBody(request) {
  const declaredLength = Number(request.headers.get("Content-Length") ?? 0);
  if (declaredLength > MAX_BODY_BYTES) throw new Error("too_large");
  if (!request.body) return "";

  const reader = request.body.getReader();
  const chunks = [];
  let total = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > MAX_BODY_BYTES) {
      await reader.cancel();
      throw new Error("too_large");
    }
    chunks.push(value);
  }

  const body = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(body);
}

function cleanSingleLine(value, limit) {
  return String(value ?? "").replace(/[\r\n\t]+/g, " ").trim().slice(0, limit);
}

function isValidEmail(value) {
  return value.length <= 254 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

async function verifyTurnstile(token, request, env) {
  const expectedHostnames = new Set(
    String(env.TURNSTILE_HOSTNAMES ?? "")
      .split(",")
      .map((hostname) => hostname.trim())
      .filter(Boolean)
  );

  if (typeof token !== "string" || token.length === 0 || token.length > 2_048 || expectedHostnames.size === 0) return false;

  let result;
  try {
    const verification = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      signal: AbortSignal.timeout(10_000),
      body: new URLSearchParams({
        secret: env.TURNSTILE_SECRET,
        response: token,
        remoteip: request.headers.get("CF-Connecting-IP") ?? ""
      })
    });
    if (!verification.ok) return false;
    result = await verification.json();
  } catch {
    return false;
  }

  return result.success === true && result.action === "contact" && expectedHostnames.has(result.hostname);
}

async function handleContact(request, env) {
  if (request.method !== "POST") return response("Method not allowed.", 405);
  if (!request.headers.get("Content-Type")?.startsWith("application/x-www-form-urlencoded")) {
    return response("Unsupported form encoding.", 415);
  }

  const requestUrl = new URL(request.url);
  const origin = request.headers.get("Origin");
  if (!origin || new URL(origin).hostname !== requestUrl.hostname) return response("Request rejected.", 403);

  let body;
  try {
    body = await readLimitedBody(request);
  } catch {
    return response("The message is too large.", 413);
  }

  const form = new URLSearchParams(body);
  if (form.get("website")) return response(SUCCESS_MESSAGE);

  const turnstileIsValid = await verifyTurnstile(form.get("cf-turnstile-response"), request, env);
  if (!turnstileIsValid) return response("Verification failed. Please try again.", 403);

  const startedAt = Number(form.get("started_at"));
  const elapsed = Date.now() - startedAt;
  if (!Number.isFinite(startedAt) || elapsed < 1_500 || elapsed > 7_200_000) return response("Please reload the form and try again.", 400);

  const name = cleanSingleLine(form.get("name"), 100);
  const email = cleanSingleLine(form.get("email"), 254);
  const subject = cleanSingleLine(form.get("subject"), 160);
  const message = String(form.get("message") ?? "").trim().slice(0, 5_000);

  if (!isValidEmail(email) || subject.length < 3 || message.length < 10) {
    return response("Please provide a valid email, subject, and message.", 400);
  }
  if (!env.CONTACT_TO) return response("Contact delivery is not configured yet.", 503);

  const text = [
    "New message from sovereignsteak.com",
    "",
    `Name: ${name || "Not provided"}`,
    `Email: ${email}`,
    `Subject: ${subject}`,
    "",
    message
  ].join("\n");

  try {
    await env.EMAIL.send({
      to: env.CONTACT_TO,
      from: { email: "contact@sovereignsteak.com", name: "SovereignSteak Contact" },
      replyTo: email,
      subject: `[SovereignSteak] ${subject}`,
      text
    });
  } catch (error) {
    console.error(JSON.stringify({ event: "contact_email_failed", code: error?.code ?? "unknown" }));
    return response("The message could not be sent. Please try again later.", 502);
  }

  return response(SUCCESS_MESSAGE);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/contact") return handleContact(request, env);
    if (url.pathname.startsWith("/api/")) return response("Not found.", 404);
    return env.ASSETS.fetch(request);
  }
};
