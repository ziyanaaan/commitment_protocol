from fastapi.responses import JSONResponse

def value_error_handler(_, exc: ValueError):
    return JSONResponse(
        status_code=409,
        content={"error": str(exc)},
    )
