#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_map>

namespace {

struct HttpRequest {
  std::string method;
  std::string path;
  std::string body;
  std::unordered_map<std::string, std::string> headers;
};

struct HttpResponse {
  int status;
  std::string content_type;
  std::string body;
};

std::string trim(const std::string &value) {
  const auto start = value.find_first_not_of(" \t\r\n");
  if (start == std::string::npos) return "";
  const auto end = value.find_last_not_of(" \t\r\n");
  return value.substr(start, end - start + 1);
}

std::string read_request(int client_fd) {
  std::string buffer;
  buffer.reserve(4096);
  char chunk[2048];
  ssize_t received;
  size_t expected_length = 0;
  std::optional<size_t> header_end;
  while ((received = recv(client_fd, chunk, sizeof(chunk), 0)) > 0) {
    buffer.append(chunk, received);
    if (!header_end) {
      auto pos = buffer.find("\r\n\r\n");
      if (pos != std::string::npos) {
        header_end = pos;
        auto cl = buffer.find("Content-Length:");
        if (cl != std::string::npos) {
          auto line_end = buffer.find("\r\n", cl);
          auto raw = buffer.substr(cl + 15, line_end - (cl + 15));
          expected_length = static_cast<size_t>(std::strtoul(raw.c_str(), nullptr, 10));
        }
      }
    }
    if (header_end) {
      if (buffer.size() >= *header_end + 4 + expected_length) break;
    } else if (received < static_cast<ssize_t>(sizeof(chunk))) {
      break;
    }
    if (buffer.size() > 1'000'000) break;  // avoid runaway reads
  }
  return buffer;
}

HttpRequest parse_request(const std::string &raw) {
  HttpRequest req{};
  const auto header_end = raw.find("\r\n\r\n");
  const auto header_block = raw.substr(0, header_end);
  std::istringstream stream(header_block);
  std::string line;
  if (std::getline(stream, line)) {
    if (!line.empty() && line.back() == '\r') line.pop_back();
    std::istringstream first(line);
    first >> req.method >> req.path;
  }
  while (std::getline(stream, line)) {
    if (!line.empty() && line.back() == '\r') line.pop_back();
    auto sep = line.find(':');
    if (sep != std::string::npos) {
      auto key = trim(line.substr(0, sep));
      auto value = trim(line.substr(sep + 1));
      req.headers[key] = value;
    }
  }
  if (header_end != std::string::npos && header_end + 4 <= raw.size()) {
    req.body = raw.substr(header_end + 4);
  }
  return req;
}

std::string slurp(const std::filesystem::path &p) {
  std::ifstream file(p, std::ios::binary);
  if (!file.is_open()) return "";
  std::ostringstream oss;
  oss << file.rdbuf();
  return oss.str();
}

void persist(const std::filesystem::path &p, const std::string &payload) {
  std::filesystem::create_directories(p.parent_path());
  std::ofstream file(p, std::ios::binary | std::ios::trunc);
  file << payload;
}

std::string default_prompts_payload() {
  return R"({"message":"seed data unavailable","presets":[],"templates":[],"prompts":[],"settings":{"theme":"cyberpunk","autosave":true}})";
}

std::string default_settings_payload() {
  return R"({"theme":"cyberpunk","autosave":true,"save_target":"local+file"})";
}

std::string mime_type_for(const std::filesystem::path &p) {
  const auto ext = p.extension().string();
  if (ext == ".html") return "text/html; charset=utf-8";
  if (ext == ".js") return "application/javascript; charset=utf-8";
  if (ext == ".json") return "application/json; charset=utf-8";
  if (ext == ".css") return "text/css; charset=utf-8";
  if (ext == ".ts") return "text/plain; charset=utf-8";
  return "text/plain; charset=utf-8";
}

HttpResponse handle_api(const HttpRequest &req, const std::filesystem::path &data_dir) {
  if (req.path == "/api/prompts") {
    const auto prompts_path = data_dir / "prompts.json";
    if (req.method == "POST" || req.method == "PUT") {
      if (!req.body.empty()) {
        persist(prompts_path, req.body);
        return {200, "application/json", R"({"status":"saved"})"};
      }
      return {400, "application/json", R"({"error":"empty body"})"};
    }
    const auto body = std::filesystem::exists(prompts_path) ? slurp(prompts_path) : default_prompts_payload();
    return {200, "application/json", body};
  }

  if (req.path == "/api/settings") {
    const auto settings_path = data_dir / "settings.json";
    if (req.method == "POST" || req.method == "PUT") {
      if (!req.body.empty()) {
        persist(settings_path, req.body);
        return {200, "application/json", R"({"status":"settings updated"})"};
      }
      return {400, "application/json", R"({"error":"empty body"})"};
    }
    const auto body = std::filesystem::exists(settings_path) ? slurp(settings_path) : default_settings_payload();
    return {200, "application/json", body};
  }

  if (req.path == "/health") {
    return {200, "application/json", R"({"ok":true})"};
  }

  return {404, "application/json", R"({"error":"not found"})"};
}

std::filesystem::path resolve_static(const std::filesystem::path &web_root, const std::string &path) {
  auto requested = path == "/" ? "index.html" : path.substr(1);
  if (requested == "settings") requested = "settings.html";
  auto target = web_root / requested;
  std::error_code ec;
  auto canonical = std::filesystem::weakly_canonical(target, ec);
  if (ec || canonical.string().find(web_root.string()) != 0 || !std::filesystem::exists(canonical)) {
    return {};
  }
  return canonical;
}

HttpResponse serve_static(const std::filesystem::path &web_root, const std::string &path) {
  auto target = resolve_static(web_root, path);
  if (target.empty()) {
    return {404, "text/plain; charset=utf-8", "Not found"};
  }
  auto body = slurp(target);
  return {200, mime_type_for(target), body};
}

void send_response(int client_fd, const HttpResponse &res) {
  std::ostringstream oss;
  oss << "HTTP/1.1 " << res.status << " "
      << (res.status == 200 ? "OK" : (res.status == 404 ? "Not Found" : "Error")) << "\r\n";
  oss << "Content-Type: " << res.content_type << "\r\n";
  oss << "Access-Control-Allow-Origin: *\r\n";
  oss << "Access-Control-Allow-Methods: GET, POST, PUT, OPTIONS\r\n";
  oss << "Access-Control-Allow-Headers: Content-Type\r\n";
  oss << "Content-Length: " << res.body.size() << "\r\n";
  oss << "Connection: close\r\n\r\n";
  oss << res.body;
  const auto payload = oss.str();
  send(client_fd, payload.c_str(), payload.size(), 0);
}

int resolve_port() {
  if (const char *env = std::getenv("SETTINGS_PORT")) {
    return std::atoi(env);
  }
  return 8088;
}

}  // namespace

int main() {
  const std::filesystem::path web_root = std::filesystem::current_path() / "web";
  const std::filesystem::path data_root = std::filesystem::current_path() / "data";

  const int port = resolve_port();
  int server_fd = socket(AF_INET, SOCK_STREAM, 0);
  if (server_fd == -1) {
    std::cerr << "Failed to create socket\n";
    return 1;
  }

  int opt = 1;
  setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt));

  sockaddr_in address{};
  address.sin_family = AF_INET;
  address.sin_addr.s_addr = INADDR_ANY;
  address.sin_port = htons(port);

  if (bind(server_fd, reinterpret_cast<sockaddr *>(&address), sizeof(address)) < 0) {
    std::cerr << "Bind failed on port " << port << "\n";
    close(server_fd);
    return 1;
  }
  if (listen(server_fd, 10) < 0) {
    std::cerr << "Listen failed\n";
    close(server_fd);
    return 1;
  }

  std::cout << "Settings server listening on http://localhost:" << port << "\n";

  while (true) {
    sockaddr_in client_addr{};
    socklen_t client_len = sizeof(client_addr);
    int client_fd = accept(server_fd, reinterpret_cast<sockaddr *>(&client_addr), &client_len);
    if (client_fd < 0) {
      continue;
    }

    const auto raw = read_request(client_fd);
    if (raw.empty()) {
      close(client_fd);
      continue;
    }
    const auto req = parse_request(raw);

    if (req.method == "OPTIONS") {
      send_response(client_fd, {204, "text/plain", ""});
      close(client_fd);
      continue;
    }

    HttpResponse res;
    if (req.path.rfind("/api/", 0) == 0 || req.path == "/health") {
      res = handle_api(req, data_root);
    } else {
      res = serve_static(web_root, req.path);
    }

    send_response(client_fd, res);
    close(client_fd);
  }
  close(server_fd);
  return 0;
}
