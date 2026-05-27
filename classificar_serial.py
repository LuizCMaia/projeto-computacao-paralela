import os
import time
import numpy as np

# Oculta mensagens de log do TensorFlow no terminal
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

DIRETORIO_ENTRADA = "dados"
LIMITE_IMAGENS = 1000

def executar_serial_direto():
    caminhos_imagens = []
    formatos_validos = ('.jpg', '.jpeg', '.png', '.webp')
    
    print(f"[*] Varrendo a pasta '{DIRETORIO_ENTRADA}' em busca de imagens...")
    
    # Faz a leitura direta das pastas no disco (sem banco de dados)
    for raiz, _, arquivos in os.walk(DIRETORIO_ENTRADA):
        for arquivo in arquivos:
            if arquivo.lower().endswith(formatos_validos):
                caminhos_imagens.append(os.path.join(raiz, arquivo))
                # Para de procurar assim que bater o limite da amostragem
                if len(caminhos_imagens) >= LIMITE_IMAGENS:
                    break
        if len(caminhos_imagens) >= LIMITE_IMAGENS:
            break

    if not caminhos_imagens:
        print("[!] Nenhuma imagem encontrada nas pastas.")
        return

    print(f"[*] Encontradas {len(caminhos_imagens)} imagens para amostragem.")
    print("[!] Carregando o modelo do TensorFlow (isso pode levar alguns segundos)...")
    
    # Importa e carrega o modelo uma única vez no início
    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
    from tensorflow.keras.preprocessing import image
    
    # Força o uso estrito da CPU (1 núcleo na versão serial)
    tf.config.set_visible_devices([], 'GPU')
    modelo_ia = MobileNetV2(weights='imagenet')
    
    print(f"\n[*] Iniciando CLASSIFICAÇÃO IA SERIAL direto do disco...")
    
    # Medição de tempo exata
    tempo_inicio_global = time.time()
    
    for caminho in caminhos_imagens:
        try:
            # Prepara a imagem e passa pela IA
            img = image.load_img(caminho, target_size=(224, 224))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)
            
            # Faz a previsão (não vamos salvar o resultado, apenas executar a carga)
            previsoes = modelo_ia.predict(x, verbose=0)
            resultado = decode_predictions(previsoes, top=1)[0][0]
            
        except Exception as e:
            pass # Ignora imagens corrompidas e segue o loop
            
    tempo_total = time.time() - tempo_inicio_global
    print(f"\n[+] Classificação serial concluída em {tempo_total:.2f} segundos!")
    print(f"Tempo em minutos: {tempo_total / 60:.2f} minutos")

if __name__ == "__main__":
    executar_serial_direto()
