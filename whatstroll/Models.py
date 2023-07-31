from whatstroll import database
from datetime import datetime


class Solicitante(database.Model):
    id_s = database.Column(database.Integer, primary_key=True)
    telefone_s = database.Column(database.String, nullable=False, unique=True)
    datacadastro = database.Column(database.DateTime, default=datetime.now)


class Alvo(database.Model):
    id_a = database.Column(database.Integer, primary_key=True)
    telefone_a = database.Column(database.String, nullable=False, unique=True)
    datacadastro = database.Column(database.DateTime, default=datetime.now)


class Requisicao(database.Model):
    id_r = database.Column(database.Integer, primary_key=True)
    mensagem_s = database.Column(database.String, nullable=False, default='N')
    secret_key = database.Column(database.String, nullable=False, default='N')
    qtd_mensagem = database.Column(database.Integer, nullable=False, default=0)
    status = database.Column(database.Boolean, nullable=False, default=True)
    # envio_de_mensagem = database.Column(database.Boolean, nullable=False, default=True)
    datacadastro = database.Column(database.DateTime, default=datetime.now)
    id_s = database.Column(database.Integer, database.ForeignKey('solicitante.id_s'))
    perfil_s = database.relationship("Solicitante", backref="requisicao")
    id_a = database.Column(database.Integer, database.ForeignKey('alvo.id_a'))
    perfil_a = database.relationship("Alvo", backref="requisicao")
    m_solic_numero = database.Column(database.Boolean, nullable=False, default=False)
    m_infor_numero = database.Column(database.Boolean, nullable=False, default=False)
    m_solic_mensagem = database.Column(database.Boolean, nullable=False, default=False)
    m_infor_mensagem = database.Column(database.Boolean, nullable=False, default=False)
    m_solic_quantidade = database.Column(database.Boolean, nullable=False, default=False)
    m_infor_quantidade = database.Column(database.Boolean, nullable=False, default=False)
    m_solic_token = database.Column(database.Boolean, nullable=False, default=False)
    m_infor_token = database.Column(database.Boolean, nullable=False, default=False)



class Mensagens(database.Model):
    id_m = database.Column(database.Integer, primary_key=True)
    categoria_mensagem = database.Column(database.String, unique=True, nullable=False)
    mensagem_mensagem = database.Column(database.String, nullable=False)

