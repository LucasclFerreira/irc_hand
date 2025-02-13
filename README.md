
# Projeto Hand

Projeto Hand é uma aplicação Python para processamento geoespacial e cálculo dos valores HAND (Height Above Nearest Drainage). Através da integração com o Google Earth Engine (GEE) e utilizando dados de arquivos CSV ou Excel, a aplicação realiza as seguintes operações:

- **Carregamento e validação dos dados** de entrada.
- **Geocodificação** de endereços utilizando o Google Maps Geocoding API, com adição das colunas 'Latitude', 'Longitude' e 'geometry' no DataFrame.
- **Conversão para GeoDataFrame e para `ee.FeatureCollection`:** Os dados geocodificados são convertidos para um GeoDataFrame e, em seguida, para um objeto `ee.FeatureCollection` do Earth Engine.
- **Amostragem dos valores HAND:** Utiliza uma imagem pré-processada do GEE para amostrar os valores HAND.
- **Mapeamento dos valores HAND:** Os valores numéricos são convertidos para categorias descritivas (por exemplo, "Muito Baixo (> 25m)", "Baixo (10-25m)", etc.).
- **Salvamento dos resultados:** Os resultados finais são gravados em um arquivo CSV.

> **Observação:**  
> Diferentemente de um módulo instalável via pip, você receberá um arquivo ZIP contendo os seguintes arquivos:
> - `__init__.py`
> - `hand_application.py` (o script principal)
> - `.env` (arquivo de configuração para a chave da API do Google Maps e, opcionalmente, o projeto do Earth Engine)
> - `requirements.txt` (lista de dependências necessárias)

---

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Extração e Configuração](#extração-e-configuração)
- [Configuração do Google Earth Engine](#configuração-do-google-earth-engine)
- [Tutorial de Execução](#tutorial-de-execução)
- [Fluxo de Trabalho](#fluxo-de-trabalho)
- [Suporte e Contribuição](#suporte-e-contribuição)
- [Licença](#licença)

---

## Pré-requisitos

- **Python:** Versão 3.8 ou superior instalada no seu computador.
- **Google Earth Engine (GEE):** Conta no GEE para acessar os recursos do Earth Engine.
- **Pip:** Para instalação das dependências.
- **Utilitário para extração de ZIP:** Como WinRAR, 7-Zip, ou o utilitário nativo do seu sistema operacional.
- **Terminal/Prompt de Comando:** Para executar os comandos.

---

## Extração e Configuração

1. **Receba o Arquivo ZIP:**  
   Você receberá um arquivo (por exemplo, `projeto_hand.zip`) contendo os seguintes arquivos:
   - `__init__.py`
   - `hand_application.py`
   - `.env`
   - `requirements.txt`

2. **Extraia o Conteúdo:**  
   - **No Windows:** Clique com o botão direito no arquivo ZIP e selecione "Extrair Tudo..." ou utilize um programa como o 7-Zip.
   - **No macOS/Linux:** Clique duas vezes ou use o comando no terminal:
     ```bash
     unzip projeto_hand.zip
     ```
   Após a extração, uma nova pasta será criada com todos os arquivos listados.

3. **Instale as Dependências:**  
   Abra o terminal, navegue até a pasta extraída e execute:
   ```bash
   pip install -r requirements.txt
   ```
   Este comando instalará todas as bibliotecas necessárias para rodar a aplicação.

---

## Configuração do Google Earth Engine

Antes de executar o Projeto Hand, é necessário configurar sua conta no Google Earth Engine:

1. **Crie uma Conta no Google Earth Engine:**  
   Acesse [Google Earth Engine](https://earthengine.google.com/) e registre-se com sua conta Google.

2. **Instale a API do Earth Engine (se necessário):**
   ```bash
   pip install earthengine-api
   ```

3. **Autentique-se no Earth Engine:**  
   No terminal, execute:
   ```bash
   earthengine authenticate
   ```
   Siga as instruções e conceda as permissões necessárias.

4. **Configuração do Projeto (Opcional):**  
   - Abra o arquivo `.env` em um editor de texto.
   - Defina a variável `GOOGLE_API_KEY` com a sua chave da API do Google Maps.
   - Se desejar, defina também a variável `GOOGLE_CLOUD_PROJECT` com o nome do seu projeto do Earth Engine (por exemplo, `ee-paulomoraes`).  
     Caso contrário, se não definida, você poderá passar o nome do projeto via linha de comando durante a execução.

---

## Tutorial de Execução

Para uma pessoa leiga, siga os passos abaixo para extrair e executar o Projeto Hand:

1. **Extraia o Arquivo ZIP:**  
   - Localize o arquivo ZIP (por exemplo, `projeto_hand.zip`) em seu computador.
   - Clique com o botão direito e escolha a opção para extrair o conteúdo.
   - Guarde a pasta extraída em um local de sua preferência.

2. **Instale as Dependências:**  
   - Abra o Terminal ou Prompt de Comando.
   - Navegue até a pasta onde os arquivos foram extraídos. Por exemplo:
     ```bash
     cd caminho/para/a/pasta_extraida
     ```
   - Execute o seguinte comando para instalar as dependências:
     ```bash
     pip install -r requirements.txt
     ```

3. **Execute o Script via Linha de Comando:**  
   O script principal chama o método `run_from_cli()` para processar os dados. Para executá-lo, utilize o comando abaixo:
   - Se você já definiu o projeto no arquivo `.env`:
     ```bash
     python hand_application.py dados.csv endereco resultado.csv
     ```
   - Se você **não** definiu o projeto no arquivo `.env`, passe-o como quarto argumento:
     ```bash
     python hand_application.py dados.csv endereco resultado.csv seu-projeto-ee
     ```
   Onde:
   - `dados.csv` é o caminho para o arquivo de entrada (CSV ou Excel) contendo os dados.
   - `endereco` é o nome da coluna que contém os endereços a serem geocodificados.
   - `resultado.csv` é o caminho e nome do arquivo onde os resultados serão salvos.
   - `seu-projeto-ee` é o nome do seu projeto no Earth Engine (caso não esteja definido no arquivo `.env`).

4. **Verifique os Resultados:**  
   Após a execução, o script processará os dados e salvará os resultados no arquivo especificado. Abra o arquivo `resultado.csv` para visualizar os dados processados.

---

## Fluxo de Trabalho

1. **Carregamento dos Dados:**  
   O arquivo de entrada é lido e os dados são armazenados em um DataFrame.

2. **Geocodificação:**  
   Os endereços são geocodificados utilizando o Google Maps Geocoding API. Registros que não forem encontrados são descartados.

3. **Conversão para ee.FeatureCollection:**  
   O DataFrame é convertido para um GeoDataFrame e, em seguida, para uma `ee.FeatureCollection` necessária para a amostragem no Earth Engine.

4. **Amostragem dos Valores HAND:**  
   Uma imagem predefinida do Earth Engine é utilizada para amostrar os valores HAND nos pontos geocodificados.

5. **Mapeamento dos Valores:**  
   Os valores numéricos são convertidos em categorias descritivas.

6. **Salvamento dos Resultados:**  
   Os resultados finais são salvos em um arquivo CSV.

---

## Suporte e Contribuição

Se você tiver dúvidas, encontrar problemas ou desejar contribuir com melhorias, sinta-se à vontade para entrar em contato ou colaborar com o projeto.

---

## Licença

Este projeto é licenciado sob a Licença MIT. Consulte o arquivo LICENSE para mais detalhes.

