# TokenSnare

## Server
` python3 tokensnare_server.py --host $ip --port 5000 `

## Cli

### Word
`python3 tokensnare_cli.py --type docx --output prueba_docx.docx --server $ip`
Tiene opciones como --title, --author, --content.

## Excel
Idem solo que sin content y con xlsx

## Epub
Funciona solo con calibre.

## PDF
Al abrir se lanza una solicitud explícita de conexión (no es tan silencioso) con visores como Adobe Crobat o Master PDF Editor 5 (disponible para linux). Si se niega la conexión la alerta no se levanta. CanaryToken se da cuenta aunque se bloquee la conexión porque igualmente se realiza una búsqueda DNS del servidor. No sirve esa alternativa si el servidor es local.

## Notas
- .docx, .xlsx y .epub funcionan con un tracking pixel, .pdf funciona con una OpenAction, una acción que al abrirse se conecta con el servidor.
- Estaría bueno guardar las alertas en un logging en lugar de una bd?
- Es inseguro porque un atacante puede borrar toda la bd, faltaría una api key (O que solo se pueda acceder a la información del servidor de manera local, pero esto impide que se pueda controlar a distancia). No creo que sea necesario para la demo.