from whatstroll import app
from flask import request, jsonify
from whatstroll.Funcoes import recepcionamensagem, mensagememmassa


@app.route("/", methods=['GET', "POST"])
def recepcao():
    response = request.get_json()
    status = recepcionamensagem(response)
    mensagememmassa()
    return status



