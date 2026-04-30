# Temporary app.py to clear the 10021 error
async def on_fetch(request, env):
    import json
    return Response(
        json.dumps({"status": "Build System Reset Success"}),
        status=200,
        headers={"Content-Type": "application/json"}
    )
