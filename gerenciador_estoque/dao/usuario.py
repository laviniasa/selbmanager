import mysql.connector
from conection import Conection  # Importa a classe Usuario do arquivo modelo.py
from flask import Flask, jsonify


app = Flask(__name__)

class Usuarios:
    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.route('/usuarios')
def usuarios():
    # Estabelecer conexão com o banco de dados
    connection = Conection.get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Consulta SQL para pegar os dados
    cursor.execute('SELECT * FROM usuarios')
    
    # Obter os resultados
    usuarios = cursor.fetchall()
    
    # Fechar a conexão
    cursor.close()
    connection.close()
    
    # Retornar os dados em formato JSON
    return jsonify(usuarios)



if __name__ == '__main__':
    app.run(debug=True)
