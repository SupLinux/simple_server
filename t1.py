from wsgiref.simple_server import make_server
from webob import Request,Response
from webob.dec import wsgify
from webob.exc import HTTPNotFound
import logging
import re
FORMAT = "%(astime)s %(threadName)s %(thread)d %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)

class AttrDict:

    def __init__(self, d:dict):
        self.__dict__.update(d if isinstance(d, dict) else {})

    def __setattr__(self, key, value):
        raise NotImplementedError

    def __repr__(self):
        return "{}".format(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

class Router:
    def __init__(self, prefix:str=""):
        self.__prefix = prefix
        self.__routertable = []

    def route(self, methods, pattern):
        def wrapper(handler):
            self.__routertable.append(
                (tuple(map(lambda x:x.upper(), methods)),
                 re.compile(pattern),
                 handler)
            )
            return handler
        return wrapper

    def get(self, pattern):
        return self.route("GET", pattern)

    def post(self, pattern):
        return self.route("POST", pattern)

    def match(self, request):
        path = request.path
        if not path.startswith(self.__prefix):
            return None
        for methods, pattern, handler in self.__routertable:
            if request.method in methods or not methods:
                matcher = pattern.match(path.replace(self.__prefix, "", 1))
                if matcher:
                    request.groups = matcher.groups()
                    request.groupdict = AttrDict(matcher.groupdict())
                    response = handler(request)
                    return response


idx = Router()


@idx.get(r"^/$")
def indexhandler(request:Request):
    return "<h1><center>index</center></h1>"
py = Router("/python")


@py.route(r"^/$", "GET")
@py.get(r"^/(?P<id>\d+)$")
def pythonhandler(request:Request):
    return "<h1><center>python {}</center></h1>".format(request.groupdict.id)

class App:
    ROUTERS = []

    @classmethod
    def register(cls, *routers):
        for router in routers:
            cls.ROUTERS.append(router)

    @wsgify
    def __call__(self, request:Request):
        for router in self.ROUTERS:
            response = router.match(request)
            if response:
                return response
        raise HTTPNotFound("<h1>该网页被外星人劫持</h1>")
App.register(idx, py)

if __name__ == "__main__":
    httpd = make_server("0.0.0.0", 9000, App())
    try:
        httpd.serve_forever()
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        print("stop")
        httpd.server_close()