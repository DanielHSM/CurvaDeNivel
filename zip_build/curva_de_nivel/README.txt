Plugin Curva de Nivel

Este plugin cria curvas de nível a partir de dados geomorfométricos do território brasileiro obtidos no portal TOPODATA do INPE.

🧐 Funcionalidades:
Cria curvas de nível em todo território brasileiro a partir de uma área selecionada pelo usuário.
Permite definir o intervalo entre as curvas de nível.
Possui três opções de suavização para criar curvas de nível mais limpas.
Cria uma camada vetorial de linhas com simbologia, rótulos e máscara seguindo o padrão das cartas topográficas.
Permite utilizar Proxy com autenticação em redes privadas.

🛠️ Como usar:
1. Selecione a área de interesse utilizando a ferramenta de seleção.

2. Defina o intervalo entre as curvas. O intervalo padrão é de 10 metros.

3. Escolha o nível de suavização. O padrão é nível médio.

4. Escolha um perfil de autenticação de Proxy caso necessário. Para criar um novo perfil:
    4.1 Clique no botão +.
    4.2 Escolha o tipo Basic Authentication
    4.3 Escolha um nome para o perfil.
    4.4 Entre com o nome do usuário.
    4.5 Entre com a senha.
    4.6 Entre com o domínio e porta. Ex.: http://proxy.dpf.gov.br:8080
    4.7 Clique em Salvar e escolha o perfil criado na lista de perfis.

5. Clique em Executar. O plugin criará uma camada vetorial temporária com o resultado.

🍰 Sobre o Desenvolvedor:
Daniel Hulshof Saint Martin é Agente de Polícia Federal, atualmente lotado no Grupo de Bombas e Explosivos - GBE, em Brasília/DF. Atua também como professor da Academia Nacional de Polícia, na cadeira de de Orientação e Navegação do Serviço de Ensino Operacional.

💻 Recursos e tecnologias utilizados nesse plugin:
Portal TOPODATA do INPE - http://www.dsr.inpe.br/topodata/
Smooth-Contours - https://github.com/MathiasGroebe/Smooth-Contours
Biblioteca GDAL - https://gdal.org/en/latest/
PyQGIS
QGIS

🛡️ Licença:
Este projeto é distribuído sob a licença GPL-3.0