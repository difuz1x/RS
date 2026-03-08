import grpc
import jwt

SECRET_KEY = "my-super-secret-key-which-is-32bytes!"
ALGORITHM  = "HS256"

PUBLIC_METHODS = [
    "/ClientManager.PingPong/connectClient",
    "/ClientManager.PingPong/disonnectClient",
    "/converter.CurrencyConverter/getExchangeRate",
]

ROLE_REQUIRED = {
    "/converter.CurrencyConverter/convertAmount":   "user",
    "/converter.CurrencyConverter/getRatesForBase": "admin",
}
class AuthInterceptor(grpc.ServerInterceptor):

    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method
        print(f"[INTERCEPTOR] {method}", flush=True)

        if method in PUBLIC_METHODS:
            return continuation(handler_call_details)

        metadata = dict(handler_call_details.invocation_metadata)
        auth_header = metadata.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            return self._abort(grpc.StatusCode.UNAUTHENTICATED, "Missing token")

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            return self._abort(grpc.StatusCode.UNAUTHENTICATED, "Token expired")
        except jwt.InvalidTokenError:
            return self._abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid token")

        required_role = ROLE_REQUIRED.get(method)
        if required_role:
            role = payload.get("role")
            if role != required_role and role != "admin":
                return self._abort(grpc.StatusCode.PERMISSION_DENIED, "Insufficient permissions")

        return continuation(handler_call_details)

    def _abort(self, code, details):
        def handler(request, context):
            context.abort(code, details)
        return grpc.unary_unary_rpc_method_handler(handler)