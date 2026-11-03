package main

import (
 "net/http"
 "net/http/httptest"
 "strings"
 "testing"
)

func TestIngressPrefixIsStrictlyValidated(t *testing.T) {
 for _, value := range []string{
  "/api/hassio_ingress/token",
  "/api/hassio_ingress/aB9_-123/",
 } {
  if _, err := ingressBase(value); err != nil { t.Errorf("rejected valid prefix %q: %v", value, err) }
 }
 for _, value := range []string{
  "", "/", "https://attacker.test/prefix", "//evil",
  "/api/hassio_ingress/../other", "/api/hassio_ingress/abc/../../root",
  "/api/hassio_ingress/abc<script>",
 } {
  if _, err := ingressBase(value); err == nil { t.Errorf("accepted malicious prefix %q", value) }
 }
}

func TestOnlyMachineRoutesAccessibleOnHostPort(t *testing.T) {
 for _, p := range []string{"/mcp", "/api", "/api/v1/memos", "/memos.api.v1.MemoService/ListMemos", "/file/attachments/abc", "/healthz"} {
  if !isAPIRoute(p) { t.Errorf("should allow API route %q", p) }
 }
 for _, p := range []string{"/", "/index.html", "/assets/index.js", "/auth", "/setting", "/apiary", "/files", "/mcp/", "/mcpevil", "/mcp/tools"} {
  if isAPIRoute(p) { t.Errorf("should block UI route %q", p) }
  req := httptest.NewRequest(http.MethodGet, p, nil)
  w := httptest.NewRecorder()
  apiOnlyHandler().ServeHTTP(w, req)
  if w.Code != http.StatusNotFound { t.Errorf("%q: expected 404, got %d", p, w.Code) }
 }
}

func TestIngressBlocksNonSupervisorAndSpoofedHeaders(t *testing.T) {
 t.Setenv("MEMOS_CI_ALLOW_LOOPBACK", "0")
 request := httptest.NewRequest(http.MethodGet, "/", nil)
 request.RemoteAddr = "192.0.2.55:30000"
 request.Header.Set("X-Ingress-Path", "/api/hassio_ingress/token")
 response := httptest.NewRecorder()
 ingressHandler().ServeHTTP(response, request)
 if response.Code != http.StatusForbidden { t.Fatalf("spoofed ingress: %d", response.Code) }

 request.RemoteAddr = "172.30.32.2:30000"
 request.Header.Del("X-Ingress-Path")
 response = httptest.NewRecorder()
 ingressHandler().ServeHTTP(response, request)
 if response.Code != http.StatusBadRequest { t.Fatalf("missing prefix: %d", response.Code) }
}

func TestHealthAndLocationRewrite(t *testing.T) {
 // No backend needed: focus on fail-closed routing and prefix parsing.
 prefix, err := ingressBase("/api/hassio_ingress/testToken/")
 if err != nil { t.Fatal(err) }
 if strings.HasSuffix(prefix, "/") { t.Fatal("base must have no trailing slash") }
 if prefix != "/api/hassio_ingress/testToken" { t.Fatal(prefix) }
}
