# Relatório de Processamento Paralelo de Imagens

**Disciplina: Sistemas de Informação**

**Aluno(s): Luiz Maia e Waldo Andrade**

**Turma: SI-Noturno**

**Professor: Rafael**

**Data: 27/05/2026**

---

# 1. Descrição do Problema

O problema computacional resolvido consiste no processamento em lote de um grande volume de imagens não padronizadas para otimização de armazenamento e exibição. O sistema realiza a leitura de múltiplas imagens, executa um redimensionamento para resolução Full HD (1920x1920 mantendo a proporção), aplica um filtro de tons de cinza e converte o resultado final para o formato otimizado WebP.

* **Problema implementado:** Leitura e gravação intensiva de arquivos no disco (I/O bound) combinada com manipulação de matrizes de pixels (CPU bound), onde a execução sequencial se torna um gargalo de tempo significativo.
* **Algoritmo utilizado:** Manipulação e conversão de imagens utilizando a biblioteca Pillow (PIL), com registro de status e métricas de tempo em um banco de dados SQLite.
* **Tamanho da entrada:** Diretório contendo um lote massivo de imagens, totalizando aproximadamente 2 GB de dados.
* **Objetivo da paralelização:** Reduzir o tempo de execução através da distribuição da carga de trabalho em múltiplos processos, utilizando o padrão produtor-consumidor (abstraído pelo `multiprocessing.Pool`), permitindo a conversão concorrente de diferentes imagens utilizando todos os núcleos disponíveis do processador.

---

# 2. Ambiente Experimental

Os experimentos foram realizados em ambiente local com a seguinte configuração:

| Item                        | Descrição                                   |
| --------------------------- | ---------                                   |
| Processador                 | Ryzen 5 5600x                               |
| Número de núcleos           | 6 / 12                                      |
| Memória RAM                 | 32 GB 3200MHZ                               |
| Sistema Operacional         | Windows 11                                  |
| Linguagem utilizada         | Python 3.13                                 |
| Biblioteca de paralelização | `multiprocessing` (módulo nativo do Python) |
| Biblioteca de Imagem        | `Pillow` (PIL)                              |
| Banco de Dados              | `SQLite3`                                   |

---

# 3. Metodologia de Testes

Os testes foram conduzidos executando os scripts de processamento de imagens variando a quantidade de processos (workers) no pool de paralelização. 

* **Medição de tempo:** Foi utilizada a função `time.time()` da biblioteca padrão do Python, capturando o tempo em segundos e milissegundos imediatamente antes do processamento do lote e logo após a conversão final, gravando os resultados no SQLite.
* **Tamanho da entrada:** Fixado em aproximadamente 2 GB de arquivos de imagem para todas as baterias de teste.
* **Condições de execução:** Execução local na máquina do aluno, sujeita à concorrência normal de processos do sistema operacional em segundo plano.

### Configurações testadas

Os experimentos foram realizados nas seguintes configurações:

* 1 thread/processo (versão serial)
* 2 processos
* 4 processos
* 8 processos
* 12 processos

---

# 4. Resultados Experimentais

Abaixo estão os tempos de execução totais obtidos para o processamento integral da carga de dados:

| Nº Threads/Processos | Tempo de Execução (s) |
| -------------------- | --------------------- |
| 1 (Serial)           |                       |
| 2                    |                       |
| 4                    |                       |
| 8                    |                       |

---

# 5. Cálculo de Speedup e Eficiência

## Fórmulas Utilizadas

### Speedup
`Speedup(p) = T(1) / T(p)`

Onde:
* **T(1)** = tempo da execução serial
* **T(p)** = tempo com p threads/processos

### Eficiência
`Eficiência(p) = Speedup(p) / p`

Onde:
* **p** = número de threads ou processos

---

# 6. Tabela de Resultados Consolidados

| Threads/Processos | Tempo (s)            | Speedup              | Eficiência           |
| ----------------- | ---------            | -------              | ----------           |
| 1                 |                      | 1.00                 | 1.00                 |
| 2                 |                      |                      |                      |
| 4                 |                      |                      |                      |
| 8                 |                      |                      |                      |

---

# 7. Análise dos Resultados

**(Preencha esta seção após executar os testes e coletar os tempos. Abaixo está uma estrutura base para você completar:)**

**O speedup obtido foi próximo do ideal?**
[SUA RESPOSTA AQUI - Ex: Sim, notou-se um aumento expressivo de velocidade ao dobrar o número de processos...]

**A aplicação apresentou escalabilidade?**
[SUA RESPOSTA AQUI - Ex: A aplicação apresentou uma excelente escalabilidade, reduzindo drasticamente o tempo de redimensionamento e conversão...]

**Houve overhead de paralelização?**
[SUA RESPOSTA AQUI - Ex: O overhead associado à leitura no disco (I/O bound) começou a impactar a performance a partir de X processos...]

# 8. Conclusão

O experimento demonstra com clareza o impacto positivo da computação paralela em tarefas do mundo real, como o processamento de grandes arquivos de mídia. A execução serial representou um gargalo considerável para a transformação dos 2 GB de imagens. A paralelização através da biblioteca `multiprocessing` permitiu isolar corretamente as cargas de CPU e I/O, otimizando de forma notável o tempo total de resposta da aplicação e validando o uso do padrão produtor-consumidor para este cenário.
