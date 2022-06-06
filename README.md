# Similis #

[![License](https://img.shields.io/badge/license-GPL3-green)](https://.../LICENSE)
[![Build](https://img.shields.io/badge/build-1.0-yellowgreen)](https://github.com/SenatoDellaRepubblica/Similis)

Similis è un software per il calcolo della similitudine tra emendamenti del Senato della Repubblica. 
Sviluppato dal Servizio dell'Informatica del Senato della Repubblica.

## Getting started ##

Similis è invocabile attraverso interfaccia REST (Flask) o a linea di comando fornendo il file JSON con gli emendamenti.

Per eseguire il parser:

1. Assicurarsi di aver installato Python >= 3.9
2. Checkout del progetto
    `git clone https://github.com/SenatoDellaRepubblica/Similis.git && cd Similis`
3. Installazione delle librerire richieste mediante pip per Python3
    `pip3 install -r requirements.txt`
4. Per eseguire l'interfaccia Web (sono necessarie delle variabili di ambiente)
   * `SERVER_PORT=127.0.0.1`
   * `python3 run_service.py`
5. Per eseguire il parser a riga di comando
   `python3 run_cli.py -h`

## Autore ##

Senato della Repubblica - Servizio dell'Informatica

## Licenza ##

CC BY 3.0