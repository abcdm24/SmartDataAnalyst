import azure.functions as func
from main import app
from azure.functions import AsgiMiddleware

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app_func.function_name(name="FastAPI")
@app_func.route(route="{*route}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
def main(req: func.HttpRequest, context: func.Context):
    return AsgiMiddleware(app).handle(req, context)