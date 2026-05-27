import os
import time
import sqlite3
import numpy as np

# Oculta mensagens de log do TensorFlow no terminal
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

DB_FILE = "processador.db"

def executar_serial():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Puxa as imagens pendentes
    cursor.execute("SELECT id, caminho_original FROM inventario_imagens WHERE status_processamento = 'Pendente' OR status_processamento IS NULL;")
    linhas = cursor.fetchall()
    
    if not linhas:
        print("[!] Nenhuma imagem pendente. Rode o 'cadastrar_banco.py' primeiro.")
        return

    print(f"[*] Iniciando CLASSIFICAÇÃO IA SERIAL de {len(linhas)} imagens...")
    print("[!] Carregando o modelo do TensorFlow (isso pode levar alguns segundos)...")
    
    # Importa e carrega o modelo uma única vez no início da execução
    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
    from tensorflow.keras.preprocessing import image
    
    # Força o uso estrito da CPU
    tf.config.set_visible_devices([], 'GPU')
    modelo_ia = MobileNetV2(weights='imagenet')
    
    resultados = []
    
    # Medição de tempo da versão serial
    tempo_inicio_global = time.time()
    
    for id_registro, caminho_entrada in linhas:
        inicio_individual = time.time()
        try:
            # Prepara a imagem e passa pela IA
            img = image.load_img(caminho_entrada, target_size=(224, 224))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)
            
            previsoes = modelo_ia.predict(x, verbose=0)
            resultado = decode_predictions(previsoes, top=1)[0][0]
            classificacao = resultado[1]
            
            tempo_gasto = (time.time() - inicio_individual) * 1000
            resultados.append((id_registro, f"Classe: {classificacao}", tempo_gasto))
        except Exception as e:
            resultados.append((id_registro, "Erro_IA", 0.0))
            
    tempo_total = time.time() - tempo_inicio_global
    print(f"\n[+] Classificação serial concluída em {tempo_total:.2f} segundos!")
    print(f"Tempo em minutos: {tempo_total / 60:.2f} minutos")
    
    print("[*] Gravando as classificações no banco de dados...")
    for id_reg, status, tempo_ms in resultados:
        cursor.execute(
            "UPDATE inventario_imagens SET status_processamento = ?, tempo_execucao_ms = ? WHERE id = ?;",
            (status, tempo_ms, id_reg)
        )
        
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    executar_serial()