from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Classe para gerenciamento de resmas de papel
class EstoqueDePapel:
    def __init__(self):
        self.estoque = 0
        self.registros = []
        self.estoque_minimo = 10

    def adicionar_papel_ao_estoque(self, quantidade):
        """Adiciona resmas ao estoque"""
        if quantidade > 0:
            self.estoque += quantidade

    def retirar_papel_do_estoque(self, quantidade, local):
        """Retira resmas do estoque, subtraindo da quantidade"""
        if quantidade > 0 and quantidade <= self.estoque:
            self.estoque -= quantidade
            data_retirada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            self.registros.append({'data': data_retirada, 'quantidade': quantidade, 'local': local})
            return True
        return False

    def consultar_estoque(self):
        return self.estoque

    def consultar_registros(self):
        return self.registros

    def precisa_reposicao(self):
        return self.estoque <= self.estoque_minimo


# Classe para gerenciamento de toner
class EstoqueDeToner:
    def __init__(self):
        self.estoque = {}
        self.registros = []
        self.estoque_minimo = 5

    def adicionar_toner_ao_estoque(self, marca, tipo, quantidade, validade):
        """Adiciona toner ao estoque"""
        if marca not in self.estoque:
            self.estoque[marca] = {}
        if tipo not in self.estoque[marca]:
            self.estoque[marca][tipo] = {'quantidade': 0, 'validade': validade}
        self.estoque[marca][tipo]['quantidade'] += quantidade

    def retirar_toner_do_estoque(self, marca, tipo, quantidade, local):
        """Retira toner do estoque"""
        if marca in self.estoque and tipo in self.estoque[marca]:
            if self.estoque[marca][tipo]['quantidade'] >= quantidade:
                self.estoque[marca][tipo]['quantidade'] -= quantidade
                data_retirada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                self.registros.append({'data': data_retirada, 'marca': marca, 'tipo': tipo, 'quantidade': quantidade, 'local': local})
                return True
        return False

    def consultar_estoque(self):
        return self.estoque

    def consultar_registros(self):
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
        'estoque_papel': estoque_papel.consultar_estoque(),
        'registros_papel': estoque_papel.consultar_registros(),
        'estoque_toner': estoque_toner.consultar_estoque(),
        'registros_toner': estoque_toner.consultar_registros(),
        'precisa_reposicao_papel': estoque_papel.precisa_reposicao(),
        'precisa_reposicao_toner': estoque_toner.precisa_reposicao()
    }

@app.route('/')
def index():
    dados_estoque = obter_dados_estoque()
    return render_template('index.html', **dados_estoque)

@app.route('/adicionar_papel', methods=['POST'])
def adicionar_papel():
    quantidade = int(request.form['quantidade'])
    estoque_papel.adicionar_papel_ao_estoque(quantidade)
    mensagem = f"{quantidade} resmas de papel foram adicionadas ao estoque!"
    
    dados_estoque = obter_dados_estoque()
    return render_template('index.html', **dados_estoque, mensagem_adicao=mensagem)

@app.route('/retirar_papel', methods=['POST'])
def retirar_papel():
    quantidade = int(request.form['quantidade'])
    local = request.form['local']
    
    if not estoque_papel.retirar_papel_do_estoque(quantidade, local):
        dados_estoque = obter_dados_estoque()
        return render_template('index.html', **dados_estoque, erro_papel="Estoque insuficiente!")
    
    mensagem_retirada = f"{quantidade} resmas de papel foram retiradas do estoque."
    dados_estoque = obter_dados_estoque()
    return render_template('index.html', **dados_estoque, mensagem_retirada=mensagem_retirada)

@app.route('/adicionar_toner', methods=['POST'])
def adicionar_toner():
    marca = request.form['marca']
    tipo = request.form['tipo']
    quantidade = int(request.form['quantidade'])
    validade = request.form['validade']
    
    estoque_toner.adicionar_toner_ao_estoque(marca, tipo, quantidade, validade)
    return redirect(url_for('index'))

@app.route('/retirar_toner', methods=['POST'])
def retirar_toner():
    marca = request.form['marca']
    tipo = request.form['tipo']
    quantidade = int(request.form['quantidade'])
    local = request.form['local']
    
    if not estoque_toner.retirar_toner_do_estoque(marca, tipo, quantidade, local):
        dados_estoque = obter_dados_estoque()
        return render_template('index.html', **dados_estoque, erro_toner="Estoque de toner insuficiente!")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
