# SovereignSteak Calculator

An independent static Cloudflare Worker served at `calc.sovereignsteak.com`.

## Local development

```sh
npm install
npm run dev
```

## Deploy

```sh
npm run check
npm run deploy
```

The custom domain is declared in `wrangler.jsonc`. If deployment reports that
`calc.sovereignsteak.com` is already assigned, remove its existing manual DNS
record or detach it from the `sovereignsteak` Worker, then deploy again.
