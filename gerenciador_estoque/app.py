from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Definindo uma chave secreta para sessão
app.secret_key = 'sua_chave_secreta_aqui'

# Usuários fictícios para autenticação
usuarios = {
    'admin': generate_password_hash('senha123')
}

# Classe para gerenciamento de resmas de papel
class EstoqueDePapel:
    def __init__(self):
        self.estoque = 0
        self.registros = []
        self.estoque_minimo = 10

    def adicionar(self, quantidade):
        if quantidade > 0:
            self.estoque += quantidade

    def retirar(self, quantidade, local):
        if quantidade > 0 and quantidade <= self.estoque:
            self.estoque -= quantidade
            data_retirada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            self.registros.append({'data': data_retirada, 'quantidade': quantidade, 'local': local})
            return True
        return False

    def consultar(self):
        return self.estoque

    def registros_estoque(self):
        return self.registros

    def precisa_reposicao(self):
        return self.estoque <= self.estoque_minimo


# Classe para gerenciamento de toner
class EstoqueDeToner:
    def __init__(self):
        self.estoque = {}
        self.registros = []
        self.estoque_minimo = 5

    def adicionar(self, marca, tipo, quantidade, validade):
        if marca not in self.estoque:
            self.estoque[marca] = {}
        if tipo not in self.estoque[marca]:
            self.estoque[marca][tipo] = {'quantidade': 0, 'validade': validade}
        self.estoque[marca][tipo]['quantidade'] += quantidade

    def retirar(self, marca, tipo, quantidade, local):
        if marca in self.estoque and tipo in self.estoque[marca]:
            if self.estoque[marca][tipo]['quantidade'] >= quantidade:
                self.estoque[marca][tipo]['quantidade'] -= quantidade
                data_retirada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                self.registros.append({'data': data_retirada, 'marca': marca, 'tipo': tipo, 'quantidade': quantidade, 'local': local})
                return True
        return False

    def consultar(self):
        return self.estoque

    def registros_estoque(self):
        return self.registros

    def precisa_reposicao(self):
        for marca in self.estoque.values():
            for tipo in marca.values():
                if tipo['quantidade'] <= self.estoque_minimo:
                    return True
        return False


# Instanciando objetos de estoque
estoque_papel = EstoqueDePapel()
estoque_toner = EstoqueDeToner()

def obter_dados_estoque():
    """Função auxiliar para obter dados de estoque de papel e toner"""
    return {
        'estoque_papel': estoque_papel.consultar(),
        'registros_papel': estoque_papel.registros_estoque(),
        'estoque_toner': estoque_toner.consultar(),
        'registros_toner': estoque_toner.registros_estoque(),
        'precisa_reposicao_papel': estoque_papel.precisa_reposicao(),
        'precisa_reposicao_toner': estoque_toner.precisa_reposicao()
    }

@app.route('/')
def index():
    if 'user' not in session:
        print("Usuário não autenticado, redirecionando para login...")
        return redirect(url_for('login'))

    dados_estoque = obter_dados_estoque()
    print(f"Dados de estoque: {dados_estoque}")
    return render_template('index.html', **dados_estoque)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifique se o usuário e a senha estão corretos (exemplo simples)
        if username == 'admin' and password == 'senha123':
                session['user'] = username  # Garanta que a sessão está sendo configurada
                return redirect(url_for('index'))  # Redireciona para a página principal
        else:
            # Se a autenticação falhar, exibe a mensagem de erro
            mensagem_erro = "Usuário ou senha incorretos!"
            return render_template('login.html', mensagem_erro=mensagem_erro)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/adicionar_papel', methods=['GET', 'POST'])
def adicionar_papel():
    if request.method == 'POST':
        quantidade = int(request.form['quantidade'])
        estoque_papel.adicionar(quantidade)
        flash(f"{quantidade} resmas de papel adicionadas ao estoque!", 'success')
        return redirect(url_for('index'))
    return render_template('adicionar_papel.html')

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
    
    estoque_toner.adicionar(marca, tipo, quantidade, validade)
    flash('Toner adicionado com sucesso!', 'success')
    return redirect(url_for('index'))

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

# Adicionando a rota de signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash("As senhas não coincidem!", 'danger')
            return redirect(url_for('signup'))
        
        if username in usuarios:
            flash("Usuário já existe!", 'danger')
            return redirect(url_for('signup'))
        
        usuarios[username] = generate_password_hash(password)
        flash(f"Usuário {username} cadastrado com sucesso!", 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Definindo o endpoint dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)

