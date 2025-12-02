# TokenSnare
Generador y servidor de honeytokens. Permite crear documentos con trackers e iniciar un servidor que registra los hits.

## Ejecutar la aplicación
Se utiliza docker compose para ejecutar a la vez el servidor y poder crear honeytokens vía CLI.
```bash
docker compose up
```
Se puede agregar -d para correr en segundo plano.

Recordar crear la carpeta honeyTokens con el usuario del equipo para permitir que el contenedor pueda escribir.
Si la crea el daemon de docker se crea como root.

Una vez que está corriendo el servidor, se puede ejecutar la herramienta CLI de generación de honeytokens:
```bash
docker compose exec app python tokensnare_cli.py --type pdf --output test.pdf --description test
```

Para detener el servidor, utilizar Ctrl+C o:
```bash
docker compose down
```

Para el HoneyToken binario se incluyen los templates de linux y windows por comodidad, 
pero se pueden regenerar con docker sin necesidad de instalar Go a partir del stub.go utilizando los comandos:
```bash
docker run --rm -v "$PWD":/usr/src/myapp -w /usr/src/myapp -e GOOS=windows -e GOARCH=amd64 golang:alpine go build -ldflags "-H=windowsgui -s -w" -o template_win.exe stub.go

docker run --rm -v "$PWD":/usr/src/myapp -w /usr/src/myapp -e GOOS=linux -e GOARCH=amd64 golang:alpine go build -ldflags "-s -w" -o template_linux stub.go
```

# Modo "manual"
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
