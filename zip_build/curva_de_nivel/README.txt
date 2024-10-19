Plugin Curva de Nivel

Este plugin cria curvas de nível a partir de dados geomorfométricos do território brasileiro obtidos no portal TOPODATA do INPE.

🧐 Funcionalidades:
Cria curvas de nível em todo território brasileiro a partir de uma área selecionada pelo usuário.
Permite definir o intervalo entre as curvas de nível.
Cria uma camada vetorial de linhas com simbologia, rótulos e máscara seguindo o padrão das cartas topográficas.
Permite utilizar Proxy com autenticação em redes privadas.

🛠️ Como usar:
1. Selecione a área de interesse utilizando a ferramenta de seleção.

2. Defina o intervalo entre as curvas. O intervalo padrão é de 10 metros.

3. Escolha um perfil de autenticação de Proxy caso necessário. Para criar um novo perfil:
    3.1 Clique no botão +.
    3.2 Escolha o tipo Basic Authentication
    3.3 Escolha um nome para o perfil.
    3.4 Entre com o nome do usuário.
    3.5 Entre com a senha.
    3.6 Entre com o domínio e porta. Ex.: http://proxy.dpf.gov.br:8080
    3.6 Clique em Salvar e escolha o perfil criado na lista de perfis.

🍰 Desenvolvedor:
Daniel Hulshof Saint Martin

💻 Recursos e tecnologias utilizados nesse plugin:
Portal TOPODATA do INPE - http://www.dsr.inpe.br/topodata/
Biblioteca GDAL
PyQGIS
QGIS (testado nas versões 3.16 e superior)

🛡️ Licença:
Este projeto é distribuído sob a licença GPL-3.0