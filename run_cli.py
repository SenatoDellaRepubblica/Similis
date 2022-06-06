import getopt
import logging
import sys
import nltk
import config
import props
from logic.processor import process_json_dto
from logic.utils import set_log

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    set_log()

    # TODO: https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/index.xml
    # nltk.download()

    # ------- inserita per evitare errori di NLTK sulla inizializzazione -------------
    nltk.corpus.wordnet.ensure_loaded()
    # --------------------------------------------------------------------------------

    # Set della configurazione
    props.curr_dist_cfg = props.DistanceConfig(props.TF)
    # --------

    include_singleton = True

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:")
    except getopt.GetoptError:
        print('Controllare gli argomenti')
        print(config.usage_sample)
        sys.exit(2)

    print(config.logo)

    path_input = None
    path_output = None
    for opt, arg in opts:
        if opt == '-h':
            print(config.usage_sample)
            sys.exit(1)
        elif opt == "-i":
            path_input = arg
        elif opt == "-o":
            path_output = arg

    if path_input and path_output:
        with open(path_input, mode="r", encoding="utf8") as file:
            emends_string = file.read()
            logger.info(f'input len (emends_string) is: {len(emends_string)}')

            result = process_json_dto(emends_string, include_singleton=include_singleton, create_excel=True)
            # print(json.dumps(result, indent='\t'))
            with open(path_output, mode="w",
                      encoding="utf8") as file_output:
                file_output.write(str(result))

            logger.info(f"File JSON generato in: {path_output}")
    else:
        print('problemi negli argomenti')
        print(config.usage_sample)
        sys.exit(2)
