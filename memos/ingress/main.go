// Memos Home Assistant ingress adapter and standalone browser/API listener.
// The official Memos binary remains the only application backend.
package main

import (
 "context"
 "encoding/json"
 "errors"
 "fmt"
 "html"
 "log"
 "net"
 "net/http"
 "net/http/httputil"
 "net/url"
 "os"
 "os/exec"
 "os/signal"
 "path"
 "regexp"
 "strings"
 "syscall"
 "time"
)

const (
 backendURL = "http://127.0.0.1:5231"
 webRoot = "/opt/memos-web"
 supervisorIP = "172.30.32.2"
)
var ingressPattern = regexp.MustCompile("^/api/hassio_ingress/[A-Za-z0-9_-]+/?$")

func isSupervisor(remote string) bool {
 host, _, err := net.SplitHostPort(remote)
 if err != nil { return false }
 ip := net.ParseIP(host)
 if ip == nil { return false }
 if ip.Equal(net.ParseIP(supervisorIP)) { return true }
 return os.Getenv("MEMOS_CI_ALLOW_LOOPBACK") == "1" && ip.IsLoopback()
}

func ingressBase(header string) (string, error) {
 if !ingressPattern.MatchString(header) || strings.Contains(header, "..") {
  return "", errors.New("missing or invalid X-Ingress-Path")
 }
 return strings.TrimRight(header, "/"), nil
}

func isAPIRoute(p string) bool {
 return p == "/mcp" ||
  p == "/api" || strings.HasPrefix(p, "/api/") ||
  p == "/memos.api" || strings.HasPrefix(p, "/memos.api.") ||
  p == "/file" || strings.HasPrefix(p, "/file/") ||
  p == "/healthz"
}

func newBackendProxy(prefix string) http.Handler {
 target, err := url.Parse(backendURL)
 if err != nil { panic(err) }
 proxy := httputil.NewSingleHostReverseProxy(target)
 proxy.FlushInterval = -1
 originalDirector := proxy.Director
 proxy.Director = func(request *http.Request) {
  originalDirector(request)
  request.Header.Del("X-Ingress-Path")
  request.Header.Del("X-Remote-User-Id")
  request.Header.Del("X-Remote-User-Name")
  request.Header.Del("X-Remote-User-Display-Name")
 }
 if prefix != "" {
  proxy.ModifyResponse = func(response *http.Response) error {
   if location := response.Header.Get("Location"); strings.HasPrefix(location, "/") && !strings.HasPrefix(location, "//") {
    response.Header.Set("Location", prefix+location)
   }
   cookies := response.Cookies()
   if len(cookies) > 0 {
    response.Header.Del("Set-Cookie")
    for _, cookie := range cookies {
     if cookie.Path == "/" || cookie.Path == "" { cookie.Path = prefix + "/" }
     response.Header.Add("Set-Cookie", cookie.String())
    }
   }
   return nil
  }
 }
 proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
  log.Printf("Memos backend unavailable: %v", err)
  http.Error(w, "Memos backend unavailable", http.StatusBadGateway)
 }
 return proxy
}

// Relative Vite assets, basename-aware Router and Connect client remove the
// need to rewrite minified JS. Only the HTML needs a dynamic ingress prefix.
func ingressHTML(prefix string) ([]byte, error) {
 body, err := os.ReadFile(webRoot + "/index.html")
 if err != nil { return nil, err }
 js, err := json.Marshal(prefix)
 if err != nil { return nil, err }
 bootstrap := "<base href=\"" + html.EscapeString(prefix+"/") + "\">" +
  "<script>window.__MEMOS_INGRESS_BASE__=" + string(js) + ";</script>"
 rewritten := strings.ReplaceAll(string(body), "href=\"/", "href=\""+prefix+"/")
 rewritten = strings.ReplaceAll(rewritten, "src=\"/", "src=\""+prefix+"/")
 if !strings.Contains(rewritten, "<head>") {
  return nil, errors.New("Memos frontend has no <head> to initialize ingress")
 }
 return []byte(strings.Replace(rewritten, "<head>", "<head>"+bootstrap, 1)), nil
}

func serveWeb(w http.ResponseWriter, r *http.Request, prefix string) {
 clean := path.Clean("/" + r.URL.Path)
 info, err := os.Stat(webRoot + clean)
 if err == nil && !info.IsDir() && clean != "/index.html" {
  http.ServeFile(w, r, webRoot+clean)
  return
 }
 if path.Ext(clean) != "" && clean != "/index.html" {
  http.NotFound(w, r)
  return
 }
 body, err := ingressHTML(prefix)
 if err != nil {
  log.Printf("Failed to render ingress index: %v", err)
  http.Error(w, "Memos UI unavailable", http.StatusInternalServerError)
  return
 }
 w.Header().Set("Content-Type", "text/html; charset=utf-8")
 w.Header().Set("Cache-Control", "no-store")
 w.Header().Set("X-Content-Type-Options", "nosniff")
 w.WriteHeader(http.StatusOK)
 _, _ = w.Write(body)
}

func ingressHandler() http.Handler {
 return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
  if !isSupervisor(r.RemoteAddr) {
   http.Error(w, "Home Assistant ingress only", http.StatusForbidden)
   return
  }
  prefix, err := ingressBase(r.Header.Get("X-Ingress-Path"))
  if err != nil {
   http.Error(w, "Invalid ingress path", http.StatusBadRequest)
   return
  }
  if strings.HasPrefix(r.URL.Path, prefix+"/") {
   r = r.Clone(r.Context())
   r.URL.Path = strings.TrimPrefix(r.URL.Path, prefix)
   r.URL.RawPath = ""
  }
  if isAPIRoute(r.URL.Path) {
   newBackendProxy(prefix).ServeHTTP(w, r)
   return
  }
  serveWeb(w, r, prefix)
 })
}

func standaloneHandler() http.Handler {
 proxy := newBackendProxy("")
 return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
  if isAPIRoute(r.URL.Path) {
   proxy.ServeHTTP(w, r)
   return
  }
  serveWeb(w, r, "")
 })
}

func startServer(ctx context.Context, server *http.Server, failures chan<- error) {
 go func() {
  err := server.ListenAndServe()
  if err != nil && !errors.Is(err, http.ErrServerClosed) {
   select {
   case failures <- err:
   case <-ctx.Done():
   }
  }
 }()
}

func run() error {
 ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
 defer stop()
 memos := exec.Command("/usr/local/memos/memos",
  "--data", "/data", "--addr", "127.0.0.1", "--port", "5231",
  "--config-dir", "/etc/memos/config")
 memos.Stdout, memos.Stderr = os.Stdout, os.Stderr
 if err := memos.Start(); err != nil {
  return fmt.Errorf("start upstream Memos: %w", err)
 }
 ingress := &http.Server{Addr: "0.0.0.0:8099", Handler: ingressHandler(), ReadHeaderTimeout: 15*time.Second}
 api := &http.Server{Addr: "0.0.0.0:5230", Handler: standaloneHandler(), ReadHeaderTimeout: 15*time.Second}
 failed := make(chan error, 2)
 exited := make(chan error, 1)
 go func() { exited <- memos.Wait() }()
 startServer(ctx, ingress, failed)
 startServer(ctx, api, failed)
 log.Print("Memos gateway: HA ingress 8099; standalone web/API/MCP 5230; backend loopback 5231")
 var result error
 select {
 case result = <-exited:
  if result == nil { result = errors.New("upstream Memos exited unexpectedly") }
 case result = <-failed:
 case <-ctx.Done():
 }
 shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
 defer cancel()
 _ = ingress.Shutdown(shutdownCtx)
 _ = api.Shutdown(shutdownCtx)
 if memos.ProcessState == nil {
  _ = memos.Process.Signal(syscall.SIGTERM)
  select {
  case <-exited:
  case <-time.After(10 * time.Second):
   _ = memos.Process.Kill()
   <-exited
  }
 }
 return result
}

func main() {
 if err := run(); err != nil { log.Fatal(err) }
}
