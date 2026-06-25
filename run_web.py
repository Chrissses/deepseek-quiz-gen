"""Web 模式启动脚本。用法: python run_web.py，然后浏览器访问 http://localhost:8000"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.web:app", host="127.0.0.1", port=8000, reload=True)
