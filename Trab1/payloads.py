import json


class Payload:
    def toJson(self):
        return json.dumps(vars(self))

# Cliente


class Login(Payload):
    def __init__(self, username: str, porta: int):
        self.operacao = "login"
        self.username = username
        self.porta = porta


class Logoff(Payload):
    def __init__(self, username: str):
        self.operacao = "logoff"
        self.username = username


class GetLista(Payload):
    def __init__(self):
        self.operacao = "get_lista"


class Mensagem(Payload):
    def __init__(self, username, mensagem):
        self.username = username
        self.mensagem = mensagem

# Servidor


class LoginSucess(Payload):
    def __init__(self):
        self.operacao = "login"
        self.status = 200
        self.mensagem = "Login com sucesso"


class LoginError(Payload):
    def __init__(self, mensagemErro):
        self.operacao = "login"
        self.status = 400
        self.mensagem = mensagemErro


class LogoffSucess(Payload):
    def __init__(self):
        self.operacao = "logoff"
        self.status = 200
        self.mensagem = "Logoff com sucesso"


class LogoffError(Payload):
    def __init__(self):
        self.operacao = "logoff"
        self.status = 400
        self.mensagem = "Erro no Logoff"


class GetListaSucess(Payload):
    def __init__(self, listaClientes):
        self.operacao = "get_lista"
        self.status = 200
        self.clientes = listaClientes


class GetListaError(Payload):
    def __init__(self):
        self.operacao = "get_lista"
        self.status = 400
        self.clientes = "Erro ao obter a lista"
