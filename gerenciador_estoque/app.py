from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

usuarios = {}

# Definindo uma chave secreta para sessão
app.secret_key = 'sua_chave_secreta_aqui'

# Usuários fictícios para autenticação
usuarios = {
    'admin': generate_password_hash('senha123')  # Senha hash para autenticação
}

chamados = []

class Chamado:
    id_counter = 1  # Contador para gerar IDs únicos

    def __init__(self, nome, setor, celular, acao, material=None, quantidade=None, problema=None, descricao=None):
        self.id = Chamado.id_counter  # Atribui o ID único ao chamado
        Chamado.id_counter += 1  # Incrementa o contador para o próximo ID
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
        return f"Chamado({self.id}, {self.nome}, {self.setor}, {self.acao}, {self.material})"

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


class EstoqueDePapel:
    def __init__(self):
        self.estoque = 0
        self.registros = []
        self.estoque_minimo = 10  # Quantidade mínima de resmas de papel

    def adicionar(self, quantidade):
        """Adiciona uma quantidade ao estoque de papel"""
        if quantidade > 0:
            self.estoque += quantidade
            return True  # Retorna True se a adição foi bem-sucedida
        return False  # Retorna False se a quantidade for inválida (<= 0)

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
        self.estoque = []  # Lista de toners no estoque
        self.registros = []  # Lista para registrar as retiradas de toner
        self.estoque_minimo = 5  # Quantidade mínima de toners

    def adicionar(self, marca, tipo, quantidade, validade):
        """Adiciona uma quantidade de toner ao estoque"""
        if quantidade > 0:
            toner = {
                'marca': marca,
                'tipo': tipo,
                'quantidade': quantidade,
                'validade': validade
            }
            self.estoque.append(toner)  # Adiciona o toner ao estoque
            return True  # Retorna True se a adição for bem-sucedida
        return False  # Retorna False se a quantidade for inválida (<= 0)

    def retirar(self, marca, tipo, quantidade, local):
        """Retira uma quantidade do estoque de toner, registrando a operação"""
        if quantidade > 0:
            for toner in self.estoque:
                if toner['marca'] == marca and toner['tipo'] == tipo:
                    if toner['quantidade'] >= quantidade:
                        toner['quantidade'] -= quantidade  # Subtrai a quantidade retirada do estoque
                        
                        # Registra a retirada
                        data_retirada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                        self.registros.append({
                            'data': data_retirada,
                            'marca': marca,
                            'tipo': tipo,
                            'quantidade': quantidade,
                            'local': local
                        })
                        return True  # Retorna True se a retirada for bem-sucedida
        return False  # Retorna False se não conseguir retirar a quantidade desejada

    def consultar(self):
        """Consulta o estoque atual de toners"""
        return self.estoque

    def registros_estoque(self):
        """Retorna os registros de movimentações do estoque de toner"""
        return self.registros

    def precisa_reposicao(self):
        """Verifica se o estoque de toner precisa ser reabastecido"""
        return len(self.estoque) <= self.estoque_minimo




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
solicitacoes_db = []

@app.route('/solicitacoes', methods=['GET', 'POST'])
def solicitacoes():
    if request.method == 'POST':
        tipo_impressao = request.form['tipo_impressao']
        plastificacao = 'plastificacao' in request.form
        encadernacao = 'encadernacao' in request.form
        refilagem = 'refilagem' in request.form
        solicitante = request.form['solicitante']
        departamento = request.form['departamento']

        # Se a opção "Não desejo impressão" for escolhida, quantidade não é necessária
        if tipo_impressao == 'nao_desejo_impressao':
            quantidade = None  # Não definimos a quantidade
        else:
            # Caso contrário, pegamos a quantidade
            quantidade = request.form.get('quantidade')
            if not quantidade or int(quantidade) <= 0:
                flash('Quantidade é obrigatória', 'danger')
                return redirect(url_for('solicitacoes'))  # Retorna com erro se a quantidade não for válida
            quantidade = int(quantidade)  # Converte para inteiro

        # Criar dicionário com a solicitação
        solicitacao = {
            'data': '2024-12-13',  # Você pode usar o datetime aqui para obter a data atual
            'tipo_impressao': tipo_impressao,
            'plastificacao': 'Sim' if plastificacao else 'Não',
            'encadernacao': 'Sim' if encadernacao else 'Não',
            'refilagem': 'Sim' if refilagem else 'Não',
            'quantidade': quantidade if quantidade else 'Não aplicável',
            'solicitante': solicitante,
            'departamento': departamento
        }

        # Armazenar a solicitação na lista (ou banco de dados)
        solicitacoes_db.append(solicitacao)

        # Exibir uma mensagem de sucesso
        flash('Solicitação registrada com sucesso!', 'success')

        # Redireciona para a página de solicitação para mostrar a tabela de dados
        return redirect(url_for('solicitacoes'))

    # Renderiza a página com as solicitações armazenadas na lista
    return render_template('solicitacoes.html', solicitacoes=solicitacoes_db)



#teste
@app.route('/')
def home():
    return render_template('principal.html')  # A primeira página a ser acessada é principal.html

@app.route('/index')
def index():
    if 'user' in session:  # Verifica se o usuário está logado
        return render_template('index.html')  # Redireciona para index.html
    else:
        return redirect(url_for('login'))  # Se não estiver logado, redireciona para login


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
    if 'user' not in session:  # Se o usuário não estiver logado
        return redirect(url_for('login'))  # Redireciona para a página de login

    # Se o usuário estiver autenticado, renderiza a página principal
    return render_template('principal.html')



# Rota para login do usuário
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifica se o usuário existe e se a senha está correta
        if username in usuarios and check_password_hash(usuarios[username], password):
            session['user'] = username  # Armazena o nome de usuário na sessão
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('index'))  # Redireciona para index.html após o login
        else:
            flash('Usuário ou senha inválidos!', 'danger')  # Mensagem de erro
            return render_template('login.html')  # Exibe novamente a página de login com a mensagem de erro
    
    return render_template('login.html')  # Exibe o formulário de login se for um GET




# Rota para logout do usuário
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/adicionar_papel', methods=['POST'])
def adicionar_papel():
    quantidade = int(request.form['quantidade'])

    if estoque_papel.adicionar(quantidade):
        flash(f"{quantidade} resmas de papel adicionadas ao estoque.", 'success')
    else:
        flash("Erro ao adicionar papel ao estoque.", 'danger')

    return redirect(url_for('index'))


@app.route('/retirar_papel', methods=['POST'])
def retirar_papel():
    try:
        # Obtém os dados do formulário
        quantidade = int(request.form['quantidade'])
        local = request.form['local']

        # Verifica se a quantidade é válida (positiva)
        if quantidade <= 0:
            flash("A quantidade de papel a ser retirada deve ser maior que zero.", 'danger')
            return redirect(url_for('index'))

        # Tenta retirar a quantidade do estoque
        if not estoque_papel.retirar(quantidade, local):
            flash("Estoque insuficiente para retirar o papel!", 'danger')
            return redirect(url_for('index'))

        # Exibe a mensagem de sucesso
        flash(f"{quantidade} resmas de papel retiradas do estoque.", 'success')
        return redirect(url_for('index'))

    except ValueError:
        # Caso o valor da quantidade não seja um número válido
        flash("Por favor, insira um número válido para a quantidade de papel.", 'danger')
        return redirect(url_for('index'))


@app.route('/adicionar_toner', methods=['POST'])
def adicionar_toner():
    marca = request.form['marca']
    tipo = request.form['tipo']
    quantidade = int(request.form['quantidade'])
    validade = request.form['validade']  # Validando o campo de data

    if estoque_toner.adicionar(marca, tipo, quantidade, validade):  # Chama o método de adicionar no estoque
        flash(f"{quantidade} toners da marca {marca} adicionados ao estoque.", 'success')  # Exibe sucesso
    else:
        flash("Erro ao adicionar toner ao estoque.", 'danger')  # Exibe erro se falhou

    return redirect(url_for('index'))  # Redireciona de volta para a página principal



@app.route('/retirar_toner', methods=['POST'])
def retirar_toner():
    marca = request.form['marca']
    tipo = request.form['tipo']
    quantidade = int(request.form['quantidade'])
    local = request.form['local']

    if estoque_toner.retirar(marca, tipo, quantidade, local):
        flash(f"{quantidade} toners da marca {marca} retirados do estoque.", 'success')
    else:
        flash("Erro ao retirar toner do estoque.", 'danger')

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

@app.route('/excluir_chamado/<int:id>', methods=['POST'])
def excluir_chamado(id):
    # Encontra o chamado pelo ID
    chamado = next((ch for ch in chamados if ch.id == id), None)

    if chamado:
        chamados.remove(chamado)  # Remove da lista
        flash('Chamado excluído com sucesso!', 'success')
    else:
        flash('Chamado não encontrado.', 'error')

    return redirect(url_for('visualizar'))

@app.route('/cadastrar')
def cadastrar():
    if 'user' not in session or session['user'] != 'admin':  # Verifica se o usuário está logado e é o 'admin'
        flash('Acesso negado. Você não tem permissão para acessar essa página.', 'danger')
        return redirect(url_for('index'))  # Redireciona para a página principal ou qualquer outra página
    return render_template('cadastrar.html')

# Rota para cadastrar novos usuários
@app.route('/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Verifica se as senhas são iguais
        if password != confirm_password:
            flash("As senhas não coincidem!", 'danger')
            return render_template('cadastrar_usuario.html')

        # Verifica se o usuário já existe
        if username in usuarios:
            flash("Usuário já existe!", 'danger')
            return render_template('cadastrar_usuario.html')

        # Armazenando o usuário com a senha criptografada
        usuarios[username] = generate_password_hash(password)
        
        flash("Usuário cadastrado com sucesso!", 'success')
        return redirect(url_for('login'))  # Redireciona para a tela de login

    return render_template('cadastrar_usuario.html')

# Rota para alteração de senha
@app.route('/alterar_senha', methods=['POST'])
def alterar_senha():
    username = session.get('user')  # Assume que o usuário está logado
    if not username:
        flash("Você precisa estar logado para alterar a senha.", 'danger')
        return redirect(url_for('login'))

    old_password = request.form['old_password']
    new_password = request.form['new_password']
    confirm_new_password = request.form['confirm_new_password']
    
    # Verifica se a senha antiga está correta
    if not check_password_hash(usuarios[username], old_password):
        flash("Senha antiga incorreta.", 'danger')
        return redirect(url_for('index'))

    # Verifica se a nova senha e a confirmação coincidem
    if new_password != confirm_new_password:
        flash("As novas senhas não coincidem.", 'danger')
        return redirect(url_for('index'))

    # Atualiza a senha (exemplo usando hash de senha)
    usuarios[username] = generate_password_hash(new_password)
    flash("Senha alterada com sucesso!", 'success')
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
