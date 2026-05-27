import os
import time
import sqlite3
from PIL import Image, ImageOps

# 🎯 Aponta para o banco correto em português que tem os dados de 10MB
DB_FILE = "processador"
DIRETORIO_SAIDA = "dados/saida"
LARGURA_ALVO = 1920

# A mesma função de vocês, mas adaptada para rodar sequencial
def processar_imagem_serial(payload):
    id_registro, caminho_entrada = payload
    try:
        nome_base = os.path.splitext(os.path.basename(caminho_entrada))[0]
        caminho_final = os.path.join(DIRETORIO_SAIDA, f"{nome_base}.webp")
        
        inicio_individual = time.time()
        
        with Image.open(caminho_entrada) as img:
            img.thumbnail((LARGURA_ALVO, LARGURA_ALVO))
            img = ImageOps.grayscale(img)
            img.save(caminho_final, formato="WEBP", quality=80)
            
        fim_individual = time.time()
        tempo_ms = (fim_individual - inicio_individual) * 1000
        return id_registro, "processado", tempo_ms
    except Exception as e:
        return id_registro, f"erro: {str(e)}", 0

if __name__ == "__main__":
    # Conecta no banco para pegar as imagens
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 🔥 BUSCA ATUALIZADA: Puxa o status 'Pendente' que o cadastrar_banco usou!
    cursor.execute("SELECT id, caminho_original FROM inventario_imagens WHERE status_processamento = 'Pendente' OR status_processamento IS NULL;")
    linhas = cursor.fetchall()
    
    if not linhas:
        print("Nenhuma imagem para processar.")
        conn.close()
        exit()

    print(f"Iniciando processamento SERIAL de {len(linhas)} imagens...")
    
    # ⏱️ MEDIÇÃO DE TEMPO DA VERSÃO SERIAL
    tempo_inicio_global = time.time()
    
    resultados = []
    # Loop 'for' tradicional: processa uma por uma, sequencialmente
    for linha in linhas:
        resultado = processar_imagem_serial(linha)
        resultados.append(resultado)
    tempo_total = time.time() - tempo_inicio_global
    # ───────────────────────────────────────────────────

    print(f"\n[+] Processamento serial concluído em {tempo_total:.2f} segundos!")
    print(f"Tempo em minutos: {tempo_total / 60:.2f} minutos")

    # Grava os resultados de volta no SQLite
    print("[*] Gravando métricas de tempo e performance no banco de dados...")
    for id_reg, status, tempo_ms in resultados:
        cursor.execute(
            "UPDATE inventario_imagens SET status_processamento = ?, tempo_execucao_ms = ? WHERE id = ?;",
            (status, tempo_ms, id_reg)
        )
        
    conn.commit()
    cursor.close()
    conn.close()
    print("[+] Banco de dados atualizado com sucesso!")