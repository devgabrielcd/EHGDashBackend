# src/common/middleware/session_meta.py
from datetime import datetime, timezone

def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # pega o primeiro IP (mais à esquerda)
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

class SessionMetaMiddleware:
    """
    Salva IP, user-agent e last_seen na sessão do usuário autenticado.
    Isso alimenta /api/users/<id>/sessions/ (o endpoint já lê 'ip' e 'ua').
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resp = self.get_response(request)

        try:
            # só se a sessão existir e o usuário estiver autenticado
            if getattr(request, "user", None) and request.user.is_authenticated:
                sess = request.session
                ua = request.META.get("HTTP_USER_AGENT", "Unknown")
                ip = _client_ip(request)
                touched = False

                if sess.get("ua") != ua:
                    sess["ua"] = ua
                    touched = True
                if sess.get("ip") != ip:
                    sess["ip"] = ip
                    touched = True

                # last_seen para depuração
                sess["last_seen"] = datetime.now(timezone.utc).isoformat()
                if touched:
                    sess.save()
        except Exception:
            pass

        return resp
