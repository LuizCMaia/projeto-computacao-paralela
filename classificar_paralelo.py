import os
import time
import sqlite3
import numpy as np
from multiprocessing import Pool, cpu_count

# Oculta mensagens de log do TensorFlow no terminal para ficar limpo
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

DB_FILE = "processador.db"

# Variável global que vai guardar o modelo de IA na memória de cada núcleo
modelo_ia = None

def inicializar_worker():
    """
    Função executada apenas uma vez por núcleo da CPU ao iniciar o processo.
    Carrega o modelo de IA na memória de forma eficiente.
    """
    global modelo_ia
    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
    
    # Força o uso estrito da CPU para os núcleos não brigarem pela placa de vídeo
    tf.config.set_visible_devices([], 'GPU')
    
    # Baixa/Carrega o modelo pré-treinado do Google
    modelo_ia = MobileNetV2(weights='imagenet')

def classificar_imagem_task(payload):
    """
    Função paralela: Analisa a imagem e diz o que tem nela.
    """
    global modelo_ia
    id_registro, caminho_entrada = payload
    inicio_individual = time.time()
    
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
    
    try:
        # 1. Prepara a imagem para o formato que a IA exige (224x224 pixels)
        img = image.load_img(caminho_entrada, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        
        # 2. A Inteligência Artificial faz a previsão
        previsoes = modelo_ia.predict(x, verbose=0)
        
        # 3. Pega o nome do item com maior probabilidade (Top 1)
        # O decode retorna uma lista, pegamos a descrição (label) que está na posição 1
        resultado = decode_predictions(previsoes, top=1)[0][0]
        classificacao = resultado[1] 
        
        tempo_gasto = (time.time() - inicio_individual) * 1000
        return id_registro, f"Classe: {classificacao}", tempo_gasto
        
    except Exception as e:
        return id_registro, f"Erro_IA", 0.0

if __name__ == "__main__":
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, caminho_original FROM inventario_imagens WHERE status_processamento = 'Pendente';")
    linhas = cursor.fetchall()
    
    if not linhas:
        print("[!] Nenhuma imagem pendente. Rode o 'cadastrar_banco.py' primeiro.")
        exit()
        
    nucleos = cpu_count()
    print(f"[*] Iniciando CLASSIFICAÇÃO COM IA de {len(linhas)} imagens usando {nucleos} núcleos...")
    print("[!] O TensorFlow pode demorar alguns segundos para inicializar os workers. Aguarde...\n")
    
    tempo_inicio_global = time.time()
    
    # Inicia o pool passando a função de inicialização
    with Pool(processes=nucleos, initializer=inicializar_worker) as pool:
        resultados = pool.map(classificar_imagem_task, linhas)
        
    tempo_total = time.time() - tempo_inicio_global
    print(f"\n[+] Classificação IA paralela concluída em {tempo_total:.2f} segundos!")
    
    print("[*] Gravando as classificações no banco de dados...")
    for id_reg, status, tempo_ms in resultados:
        cursor.execute(
            "UPDATE inventario_imagens SET status_processamento = ?, tempo_execucao_ms = ? WHERE id = ?;",
            (status, tempo_ms, id_reg)
        )
        
    conn.commit()
    cursor.close()
    conn.close()
    print("[+] Banco atualizado! Use um programa como o 'DB Browser for SQLite' para ver o nome do que ele achou nas fotos.")