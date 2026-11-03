# Rebuild the frontend from the exact upstream release so React Router,
# Connect RPC, attachments, and SSE can use Home Assistant's ingress prefix.
FROM node:24-alpine AS frontend
ARG MEMOS_WEB_TAG=26.11.0
RUN apk add --no-cache curl tar && npm install --global pnpm@11.0.1
RUN set -eux; \
    mkdir -p /src; \
    curl -fsSL --retry 3 \
      "https://codeload.github.com/usememos/memos/tar.gz/refs/tags/${MEMOS_WEB_TAG}" \
      -o /tmp/memos-src.tar.gz; \
    tar -xzf /tmp/memos-src.tar.gz --strip-components=1 -C /src; \
    rm /tmp/memos-src.tar.gz
COPY patch-web.mjs /tmp/patch-web.mjs
RUN node /tmp/patch-web.mjs
RUN cd /src/web && \
    pnpm install --frozen-lockfile && \
    pnpm exec vite build --mode release --base=./ --outDir=../server/frontend/dist --emptyOutDir && \
    test -s /src/server/frontend/dist/index.html

FROM --platform=$BUILDPLATFORM golang:1.27-alpine AS gateway
ARG TARGETOS
ARG TARGETARCH
WORKDIR /src
COPY ingress/main.go main.go
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} go build -trimpath -ldflags="-s -w" -o /out/ha-memos-gateway main.go

# Keep the unmodified official Memos binary and database migrations.
FROM neosmemo/memos:26.11.0
RUN apk add --no-cache python3
COPY --from=frontend /src/server/frontend/dist /opt/memos-web
COPY --from=gateway /out/ha-memos-gateway /usr/local/bin/ha-memos-gateway
COPY configure-memos.py /usr/local/lib/configure-memos.py
COPY run.sh /run.sh
RUN chmod 0755 /run.sh /usr/local/bin/ha-memos-gateway
EXPOSE 5230
ENTRYPOINT ["/run.sh"]
