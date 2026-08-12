# SovereignSteak monorepo

Source for [sovereignsteak.com](https://sovereignsteak.com), its small projects, and published research.

## Layout

```text
apps/site/          sovereignsteak.com Cloudflare Worker and static assets
apps/calc/          calc.sovereignsteak.com RPN calculator Worker
research/koblitz-generators/   SECG Koblitz generator-selection study
```

Browser-only projects that are part of the main site live under
`apps/site/public/projects/`. Independently deployed applications live under `apps/`.
Research packages, including their reproducibility data, live under `research/`.

## Common commands

```sh
npm run dev                 # main site
npm run check               # main site, calculator, and research tests
npm run deploy              # main site
npm run deploy:calc         # calculator subdomain
npm run test:research       # Python exact-arithmetic tests
```

Each deployed application retains its own package file, lockfile, and Wrangler
configuration so it can also be developed independently.

## Secrets

No production secret belongs in this repository. Worker secrets are stored in
Cloudflare, and future CI credentials belong in GitHub Actions secrets. Local values
belong in ignored `.dev.vars` or `.env` files; commit only sanitized `.example` files.

## License

This repository is released under the [Zero-Clause BSD license](LICENSE). Code,
documentation, and research materials may be used, modified, and redistributed
without an attribution requirement, to the extent they are subject to copyright.
