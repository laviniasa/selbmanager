from flask import Flask, jsonify
import mysql.connector
from logging import FileHandler,WARNING


app = Flask(__name__)

file_handler = FileHandler('errorlog.txt')
file_handler.setLevel(WARNING)


class Conection:
    def __init__(self):
        self.__init__

# Configuração da conexão MySQL
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',     # Endereço do servidor MySQL
        user='root',   # Nome do usuário MySQL
        password='', # Senha do MySQL
        database='test', # Nome do banco de dados
    )
    return connection

@app.route('/')
def home():
    return 'Bem-vindo à aplicação Flask com MySQL!'


if __name__ == '__main__':
    app.run(debug=True)
