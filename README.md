<h1 align="center" id="title">Plugin Curva de Nivel</h1>

<p id="description">Este plugin cria curvas de nível a partir de dados geomorfométricos do território brasileiro obtidos no portal TOPODATA do INPE.</p>

  
  
<h2>🧐 Funcionalidades: </h2>


*   Cria curvas de nível em todo território brasileiro a partir de uma área selecionada pelo usuário.
*   Permite definir o intervalo entre as curvas de nível.
*   Cria uma camada vetorial de linhas com simbologia, rótulos e máscara seguindo o padrão de cartas topográficas.
*   Permite utilizar Proxy com autenticação em redes privadas.

<h2>🛠️ Como usar:</h2>

<p>1. Selecione a área de interesse utilizando a ferramenta de seleção.</p>

<p>2. Defina o intervalo entre as curvas. O intervalo padrão é de 10 metros.</p>

<p>3. Escolha um perfil de autenticação de Proxy caso necessário. Para criar um novo perfil:<br>
  &nbsp;&nbsp;&nbsp;&nbsp;3.1   Clique no botão +.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;3.2   Escolha o tipo <i>Basic Authentication</i><br>
  &nbsp;&nbsp;&nbsp;&nbsp;3.3   Escolha um nome para o perfil.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;3.4   Entre com o nome do usuário.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;3.5   Entre com a senha.<br>
  &nbsp;&nbsp;&nbsp;&nbsp;3.6   Entre com o domínio e porta. Ex.: http://proxy.dpf.gov.br:8080</p>
  &nbsp;&nbsp;&nbsp;&nbsp;3.6   Clique em Salvar e escolha o perfil criado na lista.</p>

<h2>🍰 Desenvolvedor:</h2>
Daniel Hulshof Saint Martin
  
<h2>💻 Recursos e tecnologias utilizados nesse plugin:</h2>

*   Portal TOPODATA do INPE - http://www.dsr.inpe.br/topodata/
*   Biblioteca GDAL
*   PyQGIS
*   QGIS (testado nas versões 3.16 e superior)

<h2>🛡️ Licença:</h2>

Este projeto é distribuído sob a licença GPL-3.0
