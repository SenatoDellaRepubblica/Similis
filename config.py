import props

logo = fr"""
   _____ _           _ ___     
  / ___/(_)___ ___  (_) (_)____
  \__ \/ / __ `__ \/ / / / ___/
 ___/ / / / / / / / / / (__  ) 
/____/_/_/ /_/ /_/_/_/_/____/  
                                  
Similis - v. {props.app_version}
"""

usage_sample = fr"""
uso: run_cli.py
[-i <input file or directory>]  : file di input
[-o <output dir>]               : directory di output (opzionale)
[-h]                            : print this help

Esempi di invocazione:

-i input.json -o c:\outdir
-o c:\outdir < type c:\articolato.txt 
-i c:\mydir\articolato.txt > c:\articolato.txt
"""