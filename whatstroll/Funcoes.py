from whatstroll import database, app
from whatstroll.Models import Solicitante, Requisicao, Alvo, Mensagens
import requests
from time import sleep

localhost = "http://localhost:3333"


def cadastro(numero_do_contato, tipo):
    if tipo == "solicitante":
        contato = Solicitante.query.filter_by(telefone_s=numero_do_contato).first()
        if not contato:
            novocontato = Solicitante(telefone_s=numero_do_contato)
            database.session.add(novocontato)
            database.session.commit()
    else:
        contato = Alvo.query.filter_by(telefone_a=numero_do_contato).first()
        if not contato:
            novocontato = Alvo(telefone_a=numero_do_contato)
            database.session.add(novocontato)
            database.session.commit()


def recepcionamensagem(response):
    if not response['body']['key']['fromMe']:
        numero_do_contato = response['body']['key']['remoteJid']
        cadastro(numero_do_contato, 'solicitante')
        alvoativo = verificardisponibilidade(numero_do_contato)
        if not alvoativo:
            tratativasolicitacao(response)
        else:
            status = verificartokenalvo(response, numero_do_contato)
            if status:
                enviodireto(numero_do_contato, 'TokenConfirmado')
            else:
                enviodireto(numero_do_contato, "SolicitacaoToken")
    return 'ok'


def verificartokenalvo(response, numero_do_contato):
    campomensagem = response['body']['message']
    if 'extendedTextMessage' in campomensagem:
        mensagemtexto = response['body']['message']['extendedTextMessage']['text']

    else:
        mensagemtexto = response['body']['message']['conversation']

    alvos = Requisicao.query.all()
    if alvos:
        for alvo in alvos:
            if alvo.qtd_mensagem > 0:
                if alvo.secret_key == mensagemtexto:


                    alvo.qtd_mensagem = 0
                    database.session.commit()
                    return True
    return False


def enviodireto(numero_do_contato, categoria):
    """
    Compremento de uma função que tem ligação com a função enviarmensagem(), porém de forma facilidata.
    Tem o intuito de pegar o numero direto da requisição e permitir o envio.

    Obs: As mensagens daqui so pode ser enviada caso a categoria exista no banco de dados, caso contrario, nao funciona.

    :param numero_do_contato: contato direto da requisição
    :param categoria: categoria correspondente ao banco de dados
    :return:
    """

    limite = numero_do_contato.index('@')
    telefone = numero_do_contato[:limite]
    mensagem = Mensagens.query.filter_by(categoria_mensagem=categoria).first()
    enviarmensagemtext(telefone, mensagem.mensagem_mensagem)


def enviodemensagemwhatsapp(numero_do_contato, mensagem):
    """
    Compremento de uma função que tem ligação com a função enviarmensagem(), porém de forma facilidata.
    Tem o intuito de pegar o numero direto da requisição e permitir o envio.

    Obs: As mensagens daqui so pode ser enviada caso a categoria exista no banco de dados, caso contrario, nao funciona.

    :param mensagem:
    :param numero_do_contato: contato direto da requisição
    :return:
    """

    limite = numero_do_contato.index('@')
    telefone = numero_do_contato[:limite]
    enviarmensagemtext(telefone, mensagem)


def verificardisponibilidade(tlf_dados_recebido):
    alvos = Requisicao.query.all()
    if alvos:
        for alvo in alvos:
            if alvo.qtd_mensagem > 0:
                if alvo.perfil_a.telefone_a == tlf_dados_recebido:
                    return True
    return False


def enviarmensagemtext(id_number, mensagem):
    """
    Essa função é responsavem por mandar mensagem para o whatsapp
    :param id_number: significa que esse paramentro recebe o telefone que irá receber a mensagem
    :param mensagem: significa que esse paramentro informa a mensagem a ser enviada
    :return:
    """

    url = f'{localhost}/message/text?key=ddd65'
    payload = {'id': id_number, 'message': mensagem}
    tentativas = 0
    while True:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 201:
            return {'mensagem': 'enviada'}
        if tentativas >= 3:
            return {'mensagem': 'não enviada'}
        tentativas += 1


def tratativasolicitacao(response):
    """
    Responsavel por fazer a separação de categoria,
    Se requisicoes for verdadeiro, significa que tem uma solicitação aberta
    Se não, ele vai criar uma nova.
    :param response:
    :return:
    """

    requisicoes = verificarrequisicoesandamento(response)
    if requisicoes['status']:
        solicitacaoemandamento(response, requisicoes)
    else:
        novasolicitacao(response)
    return {'status': 'ok'}


def novasolicitacao(response):
    numero_do_contato = response['body']['key']['remoteJid']

    usuario = Solicitante.query.filter_by(telefone_s=numero_do_contato).first()
    referencia = Solicitante.query.get(usuario.id_s)

    novarequisicao = Requisicao(perfil_s=referencia, status=True)
    database.session.add(novarequisicao)
    database.session.commit()
    requisicoes = verificarrequisicoesandamento(response)

    if requisicoes['status']:
        solicitacaoemandamento(response, requisicoes)
    return {'status': 'ok'}


def formatamensagem(campomensagem, response):
    if 'extendedTextMessage' in campomensagem:
        mensagemtexto = response['body']['message']['extendedTextMessage']['text']
    else:
        mensagemtexto = response['body']['message']['conversation']
    return mensagemtexto


def criarnovobanco():
    with app.app_context():
        database.create_all()
    return {'status': 'ok'}


def verificarrequisicoesandamento(response):
    """
    Verifica se tem solicitaçoes em andamento!

    Quando retorna verdadeiro, significa que tem um requisição em andamento, caso contrario não existe solicitação
    :param response:
    :return:
    """

    numero_do_contato = response['body']['key']['remoteJid']
    requisicoesabertas = Requisicao.query.filter_by(status=True).all()
    if requisicoesabertas:
        for solicitacao in requisicoesabertas:
            if numero_do_contato in solicitacao.perfil_s.telefone_s:
                return {'status': True, "id_solicitacao": solicitacao.id_r}

    return {'status': False, "id_solicitacao": False}


def solicitacaoemandamento(response, requisicoes):
    campomensagem = response['body']['message']
    mensagem = formatamensagem(campomensagem, response)
    solicitacao = Requisicao.query.filter_by(id_r=requisicoes['id_solicitacao']).first()

    if not solicitacao.m_infor_numero:
        solicitanumero(mensagem, solicitacao)
        return

    elif not solicitacao.m_infor_mensagem:
        solicitamensagem(mensagem, solicitacao)
        return

    elif not solicitacao.m_infor_quantidade:
        solicitaqtt(mensagem, solicitacao)
        return

    elif not solicitacao.m_infor_token:
        solicitacaotoken(mensagem, solicitacao)
        return


def solicitanumero(mensagemtexto, solicitacao):
    if not solicitacao.m_solic_numero:
        enviodireto(solicitacao.perfil_s.telefone_s, 'SolicitacaoNumero')
        solicitacao.m_solic_numero = True
        buscasolicitante = Solicitante.query.filter_by(telefone_s=solicitacao.perfil_s.telefone_s).first()
        referencia = Solicitante.query.get(buscasolicitante.id_s)
        solicitacao.perfil_s = referencia
        database.session.commit()

    else:
        numero = ""
        for digito in mensagemtexto:
            if digito.isnumeric():
                numero += digito
        if 12 <= len(numero) <= 13:
            if len(numero) == 12:
                telefone = numero + "@s.whatsapp.net"
            else:
                telefone = numero[:4] + numero[5:] + "@s.whatsapp.net"
            cadastro(telefone, 'alvo')
            buscaalvo = Alvo.query.filter_by(telefone_a=telefone).first()
            referencia = Alvo.query.get(buscaalvo.id_a)
            solicitacao.perfil_a = referencia
            solicitacao.m_infor_numero = True
            database.session.commit()
            solicitamensagem(mensagemtexto, solicitacao)
        else:
            enviodireto(solicitacao.perfil_s.telefone_s, 'NumeroInvalido')


def solicitamensagem(mensagemtexto, solicitacao):
    if not solicitacao.m_solic_mensagem:
        enviodireto(solicitacao.perfil_s.telefone_s, 'SolicitacaoMensagem')
        solicitacao.m_solic_mensagem = True
        database.session.commit()

    else:
        solicitacao.mensagem_s = mensagemtexto
        solicitacao.m_infor_mensagem = True
        database.session.commit()
        solicitaqtt(mensagemtexto, solicitacao)


def solicitaqtt(mensagemtexto, solicitacao):
    if not solicitacao.m_solic_quantidade:
        enviodireto(solicitacao.perfil_s.telefone_s, 'SolicitaQuantidade')
        solicitacao.m_solic_quantidade = True
        database.session.commit()

    else:
        quantidade = ''
        for digito in mensagemtexto:
            if digito.isnumeric():
                quantidade += digito
        if 10 <= int(quantidade) <= 100:
            solicitacao.m_infor_quantidade = True
            solicitacao.qtd_mensagem = int(quantidade)
            database.session.commit()
            solicitacaotoken(mensagemtexto, solicitacao)
        else:
            enviodireto(solicitacao.perfil_s.telefone_s, 'QuantidadeInvalida')


def solicitacaotoken(mensagemtexto, solicitacao):
    if not solicitacao.m_solic_token:
        enviodireto(solicitacao.perfil_s.telefone_s, 'SolicitacaoSenha')
        solicitacao.m_solic_token = True
        database.session.commit()

    else:
        while len(mensagemtexto) < 6:
            mensagemtexto = f"0{mensagemtexto}"
        senhatoken = mensagemtexto[:6].upper()
        solicitacao.m_infor_token = True
        solicitacao.secret_key = senhatoken
        solicitacao.status = True
        database.session.commit()
        numero_do_contato = solicitacao.perfil_s.telefone_s
        limite = numero_do_contato.index('@')
        telefone = numero_do_contato[:limite]
        enviarmensagemtext(telefone, f"Seu token é: {senhatoken}")
        enviodireto(solicitacao.perfil_s.telefone_s, 'MensagemFinal')


def mensagememmassa():
    def verificarquantidade(objeto):
        status = Requisicao.query.filter_by(id_r=objeto).first()
        # print(status, 'envio')
        return status

    solicitacoesgerais = Requisicao.query.filter_by(status=True).all()

    if solicitacoesgerais:
        for solicitacao in solicitacoesgerais:
            if solicitacao.m_infor_token:
                solicitacao.status = False
                database.session.commit()
                for envio in range(solicitacao.qtd_mensagem):
                    quantidadeenvio = verificarquantidade(solicitacao.id_r)
                    if quantidadeenvio.qtd_mensagem > 0:
                        enviodemensagemwhatsapp(solicitacao.perfil_a.telefone_a, solicitacao.mensagem_s)
                        solicitacao.qtd_mensagem -= 1
                        database.session.commit()
                        quantidadeenvio = verificarquantidade(solicitacao.id_r)
                        if quantidadeenvio.qtd_mensagem == 0:
                            solicitacao.status = False
                            database.session.commit()
