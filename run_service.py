import json
import logging.handlers
import os

from flask_cors import CORS
import nltk
from flask_restx._http import HTTPStatus
from numpy.distutils.fcompiler import str2bool

import props as props
import requests
from flask import Flask, request, Blueprint, url_for, Response
from flask_restx import Api, Resource

from logic.processor import process_json_dto
from logic.utils import set_log

"""
Run per servizio ReST che esegue calcolo di idAtto
"""

SWAGGER_UI_HTML = "swagger-ui.html"
SWAGGER_JSON = '/swagger.json'
http_methods = ['put', 'get', 'del', 'post', 'head']

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
blueprint = Blueprint('api', __name__, url_prefix='/')

# Swagger
api = Api(blueprint,
          title="Similis",
          description="Servizio",
          contact="Roberto Battistoni",
          version=props.app_version,
          contact_email="roberto.battistoni@senato.it",
          doc=f'/{SWAGGER_UI_HTML}')

# app.root_path = os.path.dirname(os.path.abspath(__file__))
app.register_blueprint(blueprint)

nsv_emends = api.namespace('similis/v1/emends', description='Emendamenti con i cluster annotati')
nsv_clusters = api.namespace('similis/v1/clusters', description='Cluster con gli emendamenti annotati')
nsv_general = api.namespace('similis/v1/misc', description='Metodi vari')


# parser = api.parser()
# parser.add_argument('ApiKey', location='headers')

@app.route("/v2/api-docs", methods=['GET'])
def get_doc():
    """
    Serve per la redirect della documentazione swagger
    """
    if request.method == 'GET':
        url = url_for(api.endpoint('specs'), _external=True)
        logger.debug(f"url: {url}")

        resp = requests.get(url, timeout=20)
        # excluded_headers = ['content - encoding', 'content - length', 'transfer - encoding', 'connection']
        excluded_headers = []
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if
                   name.lower() not in excluded_headers]

        json_dict = json.loads(resp.content)

        # Aggiunge le vendor extensions
        json_dict['info']['x-area'] = 'Testi'
        json_dict['info']['x-tipologia'] = 'Servizio'
        json_dict['info']['x-referente'] = 'Roberto Battistoni'

        # aggiungo il campo host
        try:
            json_dict[
                'host'] = f"{os.environ['EUREKA_INSTANCE_HOSTNAME']}:{os.environ['EUREKA_INSTANCE_NONSECUREPORT']}"
        except KeyError as e:
            logger.error("Problema nella variabile di ambiente EUREKA_INSTANCE_HOSTNAME")
            pass

        response = Response(json.dumps(json_dict), resp.status_code, headers)
        return response


@nsv_emends.route('/lista')
@nsv_emends.param('includesingleton', 'Se True include nell\'output i singleton')
@nsv_general.response(HTTPStatus.OK, "Computation done")
class ProcessRequestForEmendsFromJSON(Resource):
    """
    Richiamata dal GEM
    """

    def post(self):
        """
        Lista degli emendamenti con i cluster di appartenenza: utilizza il testo dal client o dal FS BGT sul server
        :return:
        """
        emends_string = request.form.get("emends")
        include_singleton = str2bool(request.args.get('includesingleton'))
        lista_emend = process_json_dto(emends_string, include_singleton=include_singleton)
        return Response(json.dumps(lista_emend), HTTPStatus.OK, mimetype="application/json")


@nsv_general.route('/config/method/<method>')
@nsv_general.param('method', 'tf-idf | tf | jaccard')
@nsv_general.response(HTTPStatus.OK, "Method set")
# @nsv_general.expect(parser)
class SetConfigMethod(Resource):

    def get(self, method: str):
        method = method.lower()
        if method == props.TF_IDF or method == props.TF or method == props.JACCARD:
            # Set della configurazione
            props.curr_dist_cfg = props.DistanceConfig(method)
            # --------

            return Response(f"Method set: {props.curr_dist_cfg.method}", HTTPStatus.OK)
        else:
            return Response("Unknown method", HTTPStatus.METHOD_NOT_ALLOWED)


def main():
    # ------- inserita per evitare errori di NLTK sulla inizializzazione -------------
    nltk.corpus.wordnet.ensure_loaded()
    # --------------------------------------------------------------------------------

    # Set della configurazione
    props.curr_dist_cfg = props.DistanceConfig(props.TF)
    # --------

    server_port = os.environ['SERVER_PORT']
    host = "0.0.0.0"

    # app.run(debug=True, host="0.0.0.0", port=5000, threaded = True, ssl_context=context)
    app.run(debug=False, host=host, port=server_port, threaded=True)


if __name__ == '__main__':
    set_log()
    main()
