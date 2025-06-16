# ProjectWork_AEQUITAS_AKKODIS

## Generazione della documentazione con Sphinx

Per generare la documentazione in formato HTML tramite Sphinx, esegui il comando:

```bash
sphinx-build -b html docs docs/_build/html
```

Questo comando costruisce la documentazione presente nella cartella `docs` e la salva in `docs/_build/html`.

Per visualizzarla nel browser, puoi aprire direttamente il file `index.html` generato:

```bash
start docs/_build/html/index.html
```

Per pubblicare la documentazione su github copiare la build da `docs/_build/html` a `docs`:
```bash
xcopy docs\_build\html\* docs\ /E /Y /I
```

