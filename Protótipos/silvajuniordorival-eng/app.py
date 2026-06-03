# BACKEND (APP.PY) PARA SERVIR UMA API JSON
# PARA COMPATIBILIDADE MOBILE
@app.route('/api/obter-tokens- offline',methods=['POST'])
def api_obter_tokens_offline():
    dados = request.get_json()
    cpf_usuario = dados.get('cpf')

    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT cpf FROM usuarios WHERE cpf = %s",(cpf_usuario,))
    usuarios = cursor.fetchone()
    cursor.close()
    conexao.close()

    if not usuario:
        return {"erro": "Usuário não localizado"}, 404

        # Geração de lote 3 tokens sequenciais seguros com tempos de expiração diferentes
        # Para o utilizador poder gastar mesmo se etiver sem nenhuma internet
        lote_tokens = []
        agora = datetime.datetime.utcnow()

        for i in range(3):
            payload = {'cpf':usuario['cpf'],

            # O primeiro token vale por 5 minutos, oo segundo por 10, o terceiro por 15
            'exp':agora + datetime.timedelta(minutes=(i + 1) * 5)}

            token_jwt = jwt.encode(payload, app.config['SECRET_KEY'], algorithm= 'HS256')
            lote_tokens.append(token_jwt)

            return{"tokens": lote_tokens}, 200
