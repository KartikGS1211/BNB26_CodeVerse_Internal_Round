# CreatorAi frontend

CreatorAi is a frontend-only creator operating system for moving from an idea to a script, mapped footage, editable short-form clips, exports, publishing, and performance insights.

## Run locally

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The root route redirects to the dashboard. The primary demo project is `/studio/grow-creator`.

## Mock mode

`NEXT_PUBLIC_USE_MOCK=true` is the default. Every data call goes through `src/lib/api.ts`, which returns typed demo data from the single source at `src/mocks/demo.ts` after a realistic 400–900 ms delay. Uploading, rendering, scheduling, search, assistant commands, and editor actions are simulated locally.

Place a roughly two-minute demo video at `public/demo/sample.mp4` to enable the HTML5 video previews. The interface and editor remain usable without it.

## Connect a real backend

Set the following values in `.env.local`:

```bash
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The frontend will use `fetch` against the API URL without component changes. Implement the endpoints and payloads documented in [`../../docs/API_CONTRACT.md`](../../docs/API_CONTRACT.md).

## Validate

```bash
npm run lint
npm run build
```
