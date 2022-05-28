LoginSucess = {"operacao": "login",
               "status": 200, "mensagem": "Login com sucesso"}


def LoginError(mensagemErro): return {'operacao': 'login',
                                      'status': 400, 'mensagem': mensagemErro}


LogoffSucess = {"operacao": "logoff",
                "status": 200, "mensagem": "Logoff com sucesso"}

LogoffError = {"operacao": "logoff",
               "status": 400, "mensagem": "Erro no Logoff"}


def GetListaSucess(listaClientes): return {"operacao": "get_lista",
                                           "status": 200, "clientes": listaClientes}


GetListaError = {"operacao": "get_lista",
                 "status": 400, "mensagem": "Erro ao obter a lista"}
