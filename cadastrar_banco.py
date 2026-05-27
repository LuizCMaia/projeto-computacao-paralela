import os
import sqlite3

        
# O arquivo do banco .db serpython processar_serial.pyá criado de forma automática na pasta
DB_FILE = "processador"
DIRETORIO_ENTRADA = "dados/entrada"

def popular_banco():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("[*] Criando tabela de inventário no SQLite...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventario_imagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_arquivo VARCHAR(255) NOT NULL,
        caminho_original TEXT NOT NULL,
        formato_original VARCHAR(10) NOT NULL,
        tamanho_bytes BIGINT,
        status_processamento VARCHAR(20) DEFAULT 'Pendente',
        tempo_execucao_ms REAL DEFAULT 0.0,
        data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    print("[*] Varrendo a pasta de imagens do Kaggle...")
    formatos_validos = ('.jpg', '.jpeg', '.png', '.webp')
    contador = 0
    
    for raiz, _, arquivos in os.walk(DIRETORIO_ENTRADA):
        for arquivo in arquivos:
            if arquivo.lower().endswith(formatos_validos):
                caminho_completo = os.path.abspath(os.path.join(raiz, arquivo))
                extensao = os.path.splitext(arquivo)[1].replace('.', '').upper()
                tamanho = os.path.getsize(caminho_completo)
                
                comando = """
                INSERT INTO inventario_imagens (nome_arquivo, caminho_original, formato_original, tamanho_bytes, status_processamento)
                VALUES (?, ?, ?, ?, 'Pendente');
                """
                cursor.execute(comando, (arquivo, caminho_completo, extensao, tamanho))
                contador += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"\n[+] Sucesso total! {contador} imagens cadastradas no arquivo '{DB_FILE}'.")

if __name__ == "__main__":
    popular_banco()