def Login(username: str, porta: int) -> dict: return {"operacao": "login",
                                                      "username": username, "porta": porta}


def Logoff(username): return {"operacao": "logoff",
                              "username": username}


GetLista = {"operacao": "get_lista"}


def Mensagem(username, mensagem): return {
    "username": username, "mensagem": mensagem}
