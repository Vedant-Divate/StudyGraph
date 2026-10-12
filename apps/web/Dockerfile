# Multi-arch: node:22-alpine ships amd64 + arm64.
FROM node:22-alpine AS deps

RUN corepack enable
WORKDIR /srv/web

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS build
RUN corepack enable
WORKDIR /srv/web
COPY --from=deps /srv/web/node_modules ./node_modules
COPY . .
RUN pnpm build && pnpm prune --prod

FROM node:22-alpine AS runner
WORKDIR /srv/web
ENV NODE_ENV=production
COPY --from=build /srv/web/package.json ./
COPY --from=build /srv/web/node_modules ./node_modules
COPY --from=build /srv/web/.next ./.next
COPY --from=build /srv/web/public ./public
COPY --from=build /srv/web/next.config.mjs ./
EXPOSE 3000
CMD ["node", "/srv/web/node_modules/next/dist/bin/next", "start"]
