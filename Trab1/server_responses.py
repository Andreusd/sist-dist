LOGIN_SUCCESS = {"operacao": "login",
                 "status": 200, "mensagem": "Login com sucesso"}

LOGIN_ERROR = {'operacao': 'login',
               'status': 400, 'mensagem': 'Username em Uso'}

LOGOFF_SUCCESS = {"operacao": "logoff",
                  "status": 200, "mensagem": "Logoff com sucesso"}

LOGOFF_ERROR = {"operacao": "logoff",
                "status": 400, "mensagem": "Erro no Logoff"}


def GET_LISTA_SUCESS(lista_clientes): return {"operacao": "get_lista",
                                              "status": 200, "clientes": lista_clientes}


GET_LISTA_ERROR = {"operacao": "get_lista",
                   "status": 400, "mensagem": "Erro ao obter a lista"}
