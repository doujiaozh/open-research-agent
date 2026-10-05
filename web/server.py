# -*- coding: utf-8 -*-

import sys, os, json, queue, threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler, HTTPServer

from agent.loop import run_agent



HERE = os.path.dirname(os.path.abspath(__file__))

MIME = {".html": "text/html; charset=utf-8",

        ".json": "application/json; charset=utf-8",

        ".js": "application/javascript; charset=utf-8",

        ".css": "text/css; charset=utf-8"}



BACKENDS = {

    "zhipu":       ("https://open.bigmodel.cn/api/paas/v4",       "glm-4-flash"),

    "intern":      ("https://discovery-api.intern-ai.org.cn/v1",  "deepseek-v4-flash-0731"),

    "deepseek":    ("https://api.deepseek.com/v1",                "deepseek-chat"),

    "siliconflow": ("https://api.siliconflow.cn/v1",              "Qwen/Qwen2.5-7B-Instruct"),

    "moonshot":    ("https://api.moonshot.cn/v1",                 "kimi-k2.6"),

    "openai":      ("https://api.openai.com/v1",                  "gpt-4o-mini"),

}





class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):

        pass



    def do_GET(self):

        path = self.path.split("?")[0]

        if path == "/":

            path = "/index.html"

        fp = os.path.join(HERE, path.lstrip("/"))

        if os.path.isfile(fp):

            with open(fp, "rb") as f:

                data = f.read()

            ext = os.path.splitext(fp)[1]

            self.send_response(200)

            self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))

            self.send_header("Content-Length", str(len(data)))

            self.send_header("Cache-Control", "no-cache")

            self.end_headers()

            self.wfile.write(data)

        else:

            self.send_response(404)

            self.end_headers()



    def do_POST(self):

        if self.path != "/research":

            self.send_response(404)

            self.end_headers()

            return

        length = int(self.headers.get("Content-Length", "0"))

        body = self.rfile.read(length).decode("utf-8")

        data = json.loads(body)

        topic = data.get("topic", "").strip()

        user_key = data.get("api_key", "").strip()

        backend = data.get("backend", "").strip()



        if not topic:

            self._json_error("empty topic")

            return



        # 临时覆盖环境变量

        old_key = os.environ.get("OPENAI_API_KEY", "")

        old_backend = os.environ.get("BACKEND", "")

        old_url = os.environ.get("OPENAI_BASE_URL", "")

        old_model = os.environ.get("MODEL", "")



        if user_key:

            os.environ["OPENAI_API_KEY"] = user_key

        if backend:

            os.environ["BACKEND"] = backend

            # 清掉可能残留的覆盖

            if "OPENAI_BASE_URL" in os.environ:

                del os.environ["OPENAI_BASE_URL"]

            if "MODEL" in os.environ:

                del os.environ["MODEL"]

            # 重新加载 llm 模块的环境变量

            for m in list(sys.modules.keys()):

                if m.startswith("agent.llm"):

                    del sys.modules[m]



        try:

            self.send_response(200)

            self.send_header("Content-Type", "text/event-stream; charset=utf-8")

            self.send_header("Cache-Control", "no-cache")

            self.send_header("X-Accel-Buffering", "no")

            self.end_headers()



            q = queue.Queue()



            def on_event(t, d):

                q.put({"type": t, "data": d})



            def runner():

                try:

                    run_agent(topic, auto_confirm=True, on_event=on_event)

                except Exception as e:

                    q.put({"type": "error", "data": {"message": str(e)}})

                finally:

                    q.put(None)



            t = threading.Thread(target=runner)

            t.daemon = True

            t.start()



            while True:

                item = q.get()

                if item is None:

                    break

                payload = "data: " + json.dumps(item, ensure_ascii=False) + "\n\n"

                self.wfile.write(payload.encode("utf-8"))

                self.wfile.flush()

            self.wfile.write(b"data: [DONE]\n\n")

            self.wfile.flush()

        finally:

            # 恢复环境变量

            os.environ["OPENAI_API_KEY"] = old_key

            if old_backend:

                os.environ["BACKEND"] = old_backend

            else:

                os.environ.pop("BACKEND", None)

            if old_url:

                os.environ["OPENAI_BASE_URL"] = old_url

            if old_model:

                os.environ["MODEL"] = old_model

            for m in list(sys.modules.keys()):

                if m.startswith("agent.llm"):

                    del sys.modules[m]



    def _json_error(self, msg):

        body = json.dumps({"error": msg}, ensure_ascii=False).encode("utf-8")

        self.send_response(400)

        self.send_header("Content-Type", "application/json; charset=utf-8")

        self.send_header("Content-Length", str(len(body)))

        self.end_headers()

        self.wfile.write(body)





if __name__ == "__main__":

    port = int(os.environ.get("PORT", "8000"))

    print("Open http://127.0.0.1:%d" % port)

    try:

        HTTPServer(("0.0.0.0", port), Handler).serve_forever()

    except KeyboardInterrupt:

        print("bye")

