# Relatório de Classificação de Imagens com Inteligência Artificial e Processamento Paralelo

**Disciplina: Sistemas de Informação** 

**Aluno(s): Luiz Maia e Waldo Andrade**

**Turma: SI-Noturno**

**Professor: Rafael**

**Data: 27/05/2026**

---

# 1. Descrição do Problema

O problema computacional resolvido consiste na classificação automatizada de um grande volume de imagens utilizando Inteligência Artificial. O sistema realiza a leitura de arquivos do disco e submete cada imagem a uma Rede Neural Convolucional (CNN) pré-treinada para identificar o objeto ou cenário presente na foto (ex: floresta, carros, animais), registrando o resultado em um banco de dados.

* **Problema implementado:** Inferência de rede neural (CPU bound), que exige intenso cálculo matemático e matricial para cada imagem processada. A execução sequencial deste tipo de algoritmo em grandes volumes de dados torna-se impraticável devido ao alto tempo de resposta.
* **Algoritmo utilizado:** Modelo `MobileNetV2` carregado através da biblioteca **TensorFlow / Keras**, com orquestração de fila e registro de resultados em banco de dados SQLite.
* **Tamanho da entrada:** Diretório contendo um lote massivo de imagens, totalizando aproximadamente 2 GB de dados.
* **Objetivo da paralelização:** Reduzir o tempo de execução instanciando o modelo de IA em múltiplos processos simultâneos. O padrão produtor-consumidor (via `multiprocessing.Pool`) foi adotado para distribuir a carga de inferência por todos os núcleos disponíveis do processador.

---

# 2. Ambiente Experimental

Os experimentos foram realizados em ambiente local com a seguinte configuração:

| Item                        | Descrição                                   |
| --------------------------- | ---------                                   |
| Processador                 | Ryzen 5 5600x                               |
| Número de núcleos           | 6/12                                        |
| Memória RAM                 | 32 GB RAM                                   |
| Sistema Operacional         | Windows 11                                  |
| Linguagem utilizada         | Python 3.13                                 |
| Biblioteca de IA            | `TensorFlow` (MobileNetV2)                  |
| Biblioteca de paralelização | `multiprocessing` (nativa)                  |
| Banco de Dados              | `SQLite3`                                   |

---

# 3. Metodologia de Testes

Os testes foram conduzidos executando os scripts de classificação variando a quantidade de processos (workers) no pool de paralelização. Foi implementada uma rotina de inicialização (`initializer` no Worker Pool) para garantir que a arquitetura da rede neural fosse carregada na memória apenas uma vez por núcleo, evitando estouro de memória RAM e overhead de I/O.

* **Medição de tempo:** Função `time.time()` capturando o timestamp imediatamente antes do envio das imagens para a IA e logo após a última previsão, gravando os resultados individuais no banco de dados.
* **Tamanho da entrada:** [Pasta com 2000 imagens para realização dos testes](https://drive.google.com/drive/folders/1gCmfQuZ5RQ8lw0qzeSrit-UQnHWA_J21?usp=drive_link)

### Configurações testadas

* 1 thread/processo (versão serial)
* 2 processos
* 4 processos
* 8 processos
* 12 processos
  
---

# 4. Resultados Experimentais

Abaixo estão os tempos de execução totais obtidos para a inferência da rede neural em toda a base de dados:

| Nº Threads/Processos | Tempo de Execução (s) |
| -------------------- | --------------------- |
| 1 (Serial)           |  13.337,52 segundos (Aprox. 3 horas e 42 minutos) |
|                      |                       |

Devido ao alto volume de dados (194.680 imagens) e à inviabilidade da execução sequencial em tempo hábil para a demonstração, o tempo total foi projetado com base em uma amostragem real de 1.000 registros, que levou 68,51 segundos no ambiente de testes. E depois multipliquei o tempo que demorou para 1000 registros e calculei como se fossem 194.680.

---

# 5. Cálculo de Speedup e Eficiência

### Speedup
`Speedup(p) = T(1) / T(p)`
*(Onde T(1) = tempo serial, T(p) = tempo paralelo)*

### Eficiência
`Eficiência(p) = Speedup(p) / p`
*(Onde p = número de threads ou processos)*

---

# 6. Tabela de Resultados Consolidados

| Threads/Processos | Tempo (s)            | Speedup              | Eficiência           |
| ----------------- | ---------            | -------              | ----------           |
| 1                 |  125.63              | 1.00                 | 1.00                 |
| 2                 |  69.65               | 1.80                 | 0.90                 |
| 4                 |  45.37               | 2.77                 | 0.69                 |
| 8                 |  36.47               | 3.44                 | 0.43                 |
| 12                |  39.95               | 3.14                 | 0.26                 |
---

# 7. Análise dos Resultados

**(Preencha após os testes)**

**O speedup obtido foi próximo do ideal?**
[Ex: Sim, o uso de múltiplos núcleos para cálculos matriciais de IA demonstrou um ganho expressivo...]

**A aplicação apresentou escalabilidade?**
[Ex: A aplicação escalou perfeitamente, provando que tarefas de machine learning se beneficiam imensamente de arquiteturas paralelas...]

**Houve overhead de paralelização?**
[Ex: O carregamento inicial do modelo do TensorFlow gerou um pequeno overhead (resolvido com o uso do initializer), mas irrisório em comparação ao ganho no tempo total de execução...]

# 8. Conclusão

O projeto provou com sucesso que a computação paralela é estritamente necessária para a aplicação de Inteligência Artificial e Visão Computacional no mundo real. A execução serial para análise matricial de 2 GB de dados demonstrou ser insustentável. Ao isolar a carga de trabalho de inferência (TensorFlow) em processos independentes gerenciados pelo Python, foi possível maximizar o uso da arquitetura multi-core do hardware e alcançar uma redução dramática no tempo de resposta do sistema.
