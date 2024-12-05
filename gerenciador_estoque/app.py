from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Definindo uma chave secreta para sessão
app.secret_key = 'sua_chave_secreta_aqui'

# Usuários fictícios para autenticação
usuarios = {
    'admin': generate_password_hash('senha123')  # Senha hash para autenticação
}

chamados = []

class Chamado:
    def __init__(self, nome, setor, celular, acao, material=None, quantidade=None, problema=None, descricao=None):
        self.nome = nome
        self.setor = setor
        self.celular = celular
        self.acao = acao
        self.material = material
        self.quantidade = quantidade
        self.problema = problema
        self.descricao = descricao
        self.data = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    def __repr__(self):
        return f"Chamado({self.nome}, {self.setor}, {self.acao}, {self.material})"
    
# Função auxiliar para adicionar o chamado à lista global
def adicionar_chamado(chamado):
    """Adiciona um chamado à lista de chamados"""
    chamados.append(chamado)
    

# Classe que gerencia as solicitações de impressão
class SolicitacaoImpressao:
    def __init__(self):
        self.solicitacoes = []

    def adicionar(self, tipo_impressao, plastificacao, encadernacao, refilagem, quantidade, solicitante, departamento):
        """Adiciona uma nova solicitação ao sistema"""
        solicitacao = {
            'data': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'tipo_impressao': tipo_impressao,
            'plastificacao': plastificacao,
            'encadernacao': encadernacao,
            'refilagem': refilagem,
            'quantidade': quantidade,
            'solicitante': solicitante,
            'departamento': departamento
        }
        self.solicitacoes.append(solicitacao)

    def consultar(self):
        """Retorna todas as solicitações registradas"""
        return self.solicitacoes


# Classe para gerenciamento do estoque de papel
class EstoqueDePapel:
    def __init__(self):
        self.estoque = 0
        self.registros = []
        self.estoque_minimo = 10  # Quantidade mínima de resmas de papel

    def adicionar(self, quantidade):
        """Adiciona uma quantidade ao estoque de papel"""
        if quantidade > 0:
            self.estoque += quantidade

    def retirar(self, quantidade, local):
        """Retira uma quantidade do estoque de papel, registrando a operação"""
        if quantidade > 0 and quantidade <= self.estoque:
            self.estoque -= quantidade
            data_retirada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            self.registros.append({'data': data_retirada, 'quantidade': quantidade, 'local': local})
            return True
        return False

    def consultar(self):
        """Consulta o estoque atual de papel"""
        return self.estoque

    def registros_estoque(self):
        """Retorna os registros de movimentações do estoque de papel"""
        return self.registros

    def precisa_reposicao(self):
        """Verifica se o estoque de papel precisa ser reabastecido"""
        return self.estoque <= self.estoque_minimo


# Classe para gerenciamento do estoque de toner
class EstoqueDeToner:
    def __init__(self):
        self.estoque = {}
        self.registros = []
        self.estoque_minimo = 5  # Quantidade mínima de toner

    def adicionar(self, marca, tipo, quantidade, validade):
        """Adiciona uma quantidade de toner ao estoque"""
        if marca not in self.estoque:
            self.estoque[marca] = {}
        if tipo not in self.estoque[marca]:
            self.estoque[marca][tipo] = {'quantidade': 0, 'validade': validade}
        self.estoque[marca][tipo]['quantidade'] += quantidade

    def retirar(self, marca, tipo, quantidade, local):
        """Retira uma quantidade de toner do estoque, registrando a operação"""
        if marca in self.estoque and tipo in self.estoque[marca]:
            if self.estoque[marca][tipo]['quantidade'] >= quantidade:
                self.estoque[marca][tipo]['quantidade'] -= quantidade
                data_retirada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                self.registros.append({'data': data_retirada, 'marca': marca, 'tipo': tipo, 'quantidade': quantidade, 'local': local})
                return True
        return False

    def consultar(self):
        """Consulta o estoque de toner"""
        return self.estoque

    def registros_estoque(self):
        """Retorna os registros de movimentações de toner"""
        return self.registros

    def precisa_reposicao(self):
        """Verifica se algum toner no estoque precisa de reposição"""
        for marca in self.estoque.values():
            for tipo in marca.values():
                if tipo['quantidade'] <= self.estoque_minimo:
                    return True
        return False


# Função auxiliar para obter dados de estoque de papel e toner
def obter_dados_estoque():
    return {
        'estoque_papel': estoque_papel.consultar(),
        'registros_papel': estoque_papel.registros_estoque(),
        'estoque_toner': estoque_toner.consultar(),
        'registros_toner': estoque_toner.registros_estoque(),
        'precisa_reposicao_papel': estoque_papel.precisa_reposicao(),
        'precisa_reposicao_toner': estoque_toner.precisa_reposicao()
    }


# Instanciando objetos de estoque e solicitações
estoque_papel = EstoqueDePapel()
estoque_toner = EstoqueDeToner()
solicitacoes_impressao = SolicitacaoImpressao()


# Rota para visualizar e adicionar solicitações de impressão
@app.route('/solicitacoes', methods=['GET', 'POST'])
def solicitacoes():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        tipo_impressao = request.form['tipo_impressao']
        plastificacao = 'sim' if 'plastificacao' in request.form else 'não'
        encadernacao = 'sim' if 'encadernacao' in request.form else 'não'
        refilagem = 'sim' if 'refilagem' in request.form else 'não'
        quantidade = int(request.form['quantidade'])
        solicitante = request.form['solicitante']
        departamento = request.form['departamento']

        if quantidade <= 0:
            flash('A quantidade de cópias deve ser maior que zero.', 'danger')
            return redirect(url_for('solicitacoes'))

        solicitacoes_impressao.adicionar(tipo_impressao, plastificacao, encadernacao, refilagem, quantidade, solicitante, departamento)
        flash('Solicitação de impressão registrada com sucesso!', 'success')
        return redirect(url_for('solicitacoes'))

    return render_template('solicitacoes.html', solicitacoes=solicitacoes_impressao.consultar())

@app.route('/')
def index():
    # Passando os dados de estoque com a função
    return render_template('index.html', **obter_dados_estoque())

@app.route('/chamado', methods=['GET'])
def chamado():
    # Exibe o formulário para abrir um chamado
    return render_template('chamado.html')

@app.route('/processar_chamado', methods=['POST'])
def processar_chamado():
    # Pegando os dados do formulário
    nome = request.form.get('nome')
    setor = request.form.get('setor')
    celular = request.form.get('celular')
    acao = request.form.get('acao')

    # Coletando as informações adicionais dependendo da ação escolhida
    chamado = None

    if acao == 'solicitar_material':
        material = request.form.get('material')
        quantidade = request.form.get('quantidade') if 'quantidade' in request.form else None
        chamado = Chamado(nome=nome, setor=setor, celular=celular, acao=acao, material=material, quantidade=quantidade)

    elif acao == 'relatar_problema':
        problema = request.form.get('problema')
        descricao = request.form.get('descricao') if 'descricao' in request.form else None
        chamado = Chamado(nome=nome, setor=setor, celular=celular, acao=acao, problema=problema, descricao=descricao)

    # Armazenando o chamado na sessão temporariamente
    session['chamado'] = {
        'nome': chamado.nome,
        'setor': chamado.setor,
        'celular': chamado.celular,
        'acao': chamado.acao,
        'material': chamado.material,
        'quantidade': chamado.quantidade,
        'problema': chamado.problema,
        'descricao': chamado.descricao
    }

    # Flash message para informar sucesso
    flash('Chamado enviado com sucesso, aguarde para ser atendido!', 'success')

    # Redireciona para a página principal
    return redirect(url_for('principal'))





@app.route('/visualizar')
def visualizar():
    # Recuperando o chamado da sessão
    chamado_data = session.get('chamado')

    if chamado_data:
        chamado = Chamado(**chamado_data)
        adicionar_chamado(chamado)  # Adiciona o chamado na lista global

        # Após adicionar, remover o chamado da sessão para evitar duplicação
        session.pop('chamado', None)

    # Exibe a lista de chamados e mensagens de flash
    return render_template('visualizar.html', chamados=chamados)




@app.route('/principal')
def principal():
    # Verifica se o usuário está autenticado na sessão
    if 'user' not in session:
        return redirect(url_for('login'))  # Se o usuário não estiver autenticado, redireciona para o login

    # Se o usuário estiver autenticado, renderiza a página principal
    return render_template('principal.html')



# Rota para login do usuário
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in usuarios and check_password_hash(usuarios[username], password):
            session['user'] = username
            return redirect(url_for('index'))

        flash("Usuário ou senha incorretos!", 'danger')
        return render_template('login.html')

    return render_template('login.html')


# Rota para logout do usuário
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# Rota para adicionar resmas de papel ao estoque
@app.route('/adicionar_papel', methods=['POST'])
def adicionar_papel():
    quantidade = int(request.form['quantidade'])
    estoque_papel.adicionar(quantidade)
    #flash(f"{quantidade} resmas de papel adicionadas ao estoque!", 'success')
    return redirect(url_for('index'))


# Rota para retirar resmas de papel do estoque
@app.route('/retirar_papel', methods=['POST'])
def retirar_papel():
    quantidade = int(request.form['quantidade'])
    local = request.form['local']

    if not estoque_papel.retirar(quantidade, local):
        flash("Estoque insuficiente para retirar o papel!", 'danger')
        return redirect(url_for('index'))

    flash(f"{quantidade} resmas de papel retiradas do estoque.", 'success')
    return redirect(url_for('index'))


@app.route('/adicionar_toner', methods=['POST'])
def adicionar_toner():
    marca = request.form['marca']
    tipo = request.form['tipo']
    quantidade = int(request.form['quantidade'])
    validade = request.form['validade']

    # Adiciona o toner ao estoque
    estoque_toner.adicionar(marca, tipo, quantidade, validade)
    
    flash('Toner adicionado com sucesso!', 'success')

    # Recupera a lista de todos os toners registrados
    toners = estoque_toner.consultar()

    # Redireciona para a página de índice, passando as informações de toner
    return render_template('index.html', toners=toners, **obter_dados_estoque())


# Rota para retirar toner do estoque
@app.route('/retirar_toner', methods=['POST'])
def retirar_toner():
    marca = request.form['marca']
    tipo = request.form['tipo']
    quantidade = int(request.form['quantidade'])
    local = request.form['local']

    if not estoque_toner.retirar(marca, tipo, quantidade, local):
        flash("Estoque insuficiente para retirar o toner!", 'danger')
        return redirect(url_for('index'))

    flash('Toner retirado com sucesso!', 'success')
    return redirect(url_for('index'))


# Rota para cadastro de novos usuários
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("As senhas não correspondem!", 'danger')
            return render_template('signup.html')

        if username in usuarios:
            flash("Usuário já existe!", 'danger')
            return render_template('signup.html')

        usuarios[username] = generate_password_hash(password)
        flash("Usuário criado com sucesso!", 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


if __name__ == '__main__':
    app.run(debug=True)
