import html
import json
import logging
import uuid
from collections import OrderedDict
from tempfile import gettempdir
from typing import Dict, List

import xlsxwriter

import props as props
from db.beans import Emend
from logic.corpus import CorpusItem
from logic.utils import fat_cluster_to_id, id_to_fatcluster, \
    get_cluster_color_map

import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram

from similis_engine.similis_engine import SimilisEngine

logger = logging.getLogger(__name__)


def plot_dendrogram(linkage_matrix, label_list, file_path, method, threshold):
    plt.figure(figsize=(25, 50))
    plt.title(f'{method}_linkage_matrix')
    dendrogram(
        linkage_matrix,
        orientation='right',
        labels=label_list,
        leaf_font_size=12,
    )
    plt.axvline(x=threshold, c='grey', lw=1, linestyle='dashed')

    plt.savefig(file_path, dpi=200)  # save figure
    return


def get_cluster_dictionary(similis_engine, flat_clusters, corpus: List, idatto: int, verbose: bool = False) -> Dict:
    """
    Ottiene la clusterizzazione sotto forma di dizionario

    :param similis_engine:
    :param flat_clusters:
    :param corpus:
    :param idatto:
    :param verbose:
    :return:
    """
    c_dict = dict()
    fulltext_prefix = f'https://github.com/SenatoDellaRepubblica/AkomaNtosoBulkData/blob/master/Leg18/Atto{str(idatto).rjust(8, "0")}/emendc/'

    # cluster COMPACTNESS (0-100%) 0 per singleton
    cluster_compactness = similis_engine.get_cluster_compactness(props.curr_dist_cfg.threshold)

    for index in range(len(flat_clusters)):

        d = {
            'idatto': idatto,
            'index': corpus[index].index,
            'id_emend': corpus[index].id_emend,
            'id_testo': corpus[index].id_testo,
            'num_em': corpus[index].num_em,
            'ver_em': corpus[index].ver_em,
            'art': corpus[index].art,
            'testo_emend': corpus[index].testo_emend[:300] if not verbose else corpus[index].testo_emend,
            'vector': similis_engine.get_serialized_doctermvector(corpus[index].index),
            'compactness': cluster_compactness[flat_clusters[index]],
            'url': f'{fulltext_prefix}{str(corpus[index].id_testo).rjust(8, "0")}-em.akn.xml'
        }

        if flat_clusters[index] in c_dict:  # cluster già preso
            value = []
            if isinstance(c_dict[flat_clusters[index]], list):
                for val in tuple(c_dict[flat_clusters[index]]):
                    value.append(val)
            else:
                value.append(c_dict[flat_clusters[index]])
            # CUT TEXT[:300]
            value.append(d)
            c_dict[flat_clusters[index]] = value
        else:
            c_dict[flat_clusters[index]] = d

    # conversione per il problema delle chiavi numpy.intc -> int
    return {int(k): v for k, v in c_dict.items()}


def process_for_cluster_list(idatto, corpus_item_lists: List[CorpusItem] = None, verbose: bool = False) -> Dict:
    """
    processa un Atto per ottenere la clusterizzazione in formato lista

    :param corpus_item_lists:
    :param verbose:
    :param idatto:
    :return:
    """

    corpus = read_emend_list(corpus_item_lists)
    similis_engine = SimilisEngine([c.testo_emend for c in corpus], props.curr_dist_cfg.method)
    # linkage_matrix = similis_engine.get_linkage_matrix()
    flat_clusters = similis_engine.get_flat_clusters(props.curr_dist_cfg.threshold)
    # if verbose:
    #    plot_dendrogram(linkage_matrix, f'data/{idatto}_{METHOD}_full.png')

    cluster_dictionary = get_cluster_dictionary(similis_engine, flat_clusters, corpus, idatto, verbose)

    return cluster_dictionary


def process_for_cluster_excel(idatto, corpus_item_lists: List[CorpusItem] = None, verbose: bool = False) -> bytes:
    """
    processa un Atto per ottenere la clusterizzazione in formato lista

    :param corpus_item_lists:
    :param verbose:
    :param idatto:
    :return:
    """

    def cluster_to_id(flat_clusters, corpus):

        cluster2id_dict = {}
        for index in range(len(flat_clusters)):

            # TOD: id_doc è l'id_emendamento
            id_doc = corpus[index].id_emend
            if flat_clusters[index] in cluster2id_dict:  # cluster già preso
                value = []
                if isinstance(cluster2id_dict[flat_clusters[index]], list):
                    for val in tuple(cluster2id_dict[flat_clusters[index]]):
                        value.append(val)
                else:
                    value.append(cluster2id_dict[flat_clusters[index]])
                value.append(id_doc)
                cluster2id_dict[flat_clusters[index]] = value
            else:
                cluster2id_dict[flat_clusters[index]] = id_doc
        return cluster2id_dict

    def create_excel_grid(similis_engine, id_to_fatcluster_dict, cluster_color_map, fatcluster_to_id_dict,
                          corpus) -> str:

        def corpus_by_articolo() -> Dict:
            """
            Raggruppa in una dictionary per articolo
            :return:
            """
            d = dict()
            for c in corpus:
                # caso in cui non è specificato l'articolo: lo prende dal numero emendamento
                if not c.art:
                    art = c.num_em.split('.', 1)[0]
                else:
                    art = c.art.rsplit('/', 1)[0]
                if d.get(art) is None:
                    d[art] = list()
                d[art].append(c)

            return d

        tmp_file = f'{gettempdir()}/{idatto}-{str(uuid.uuid4().hex)}.xlsx'
        workbook = xlsxwriter.Workbook(tmp_file)

        worksheet1 = workbook.add_worksheet()
        worksheet1.name = "Art - id (cluster)"
        worksheet2 = workbook.add_worksheet()
        worksheet2.name = "Art - num (cluster)"
        worksheet4 = workbook.add_worksheet()
        worksheet4.name = "Elenco Cluster"
        worksheet3 = workbook.add_worksheet()
        worksheet3.name = "Legenda Cluster"

        # WORKSHEET 1,2: cluster per articolo (con id_emend, num_emend e id_cluster)
        groub_by_article = corpus_by_articolo()

        column = 0
        for num_art, value in groub_by_article.items():

            # raggruppa emendamenti per Articolo modificato e ordina per id
            emends_by_article = sorted(value, key=lambda x: x.num_em)

            # ordered_amendment_content_list = limit_char([i.testo_emend for i in emends_by_article])
            ordered_emend_list = [(i.id_emend, i.num_em) for i in emends_by_article]

            # Set the property of the column
            worksheet1.set_column(column, column, 20)
            worksheet2.set_column(column, column, 20)

            # ROW 1
            worksheet1.write(0, column, f'Art: {num_art}')
            worksheet2.write(0, column, f'Art: {num_art}')

            for k in range(len(ordered_emend_list)):
                id_emend = ordered_emend_list[k][0]
                num_emend = ordered_emend_list[k][1]
                # text = ordered_amendment_content_list[k]
                cell_format = workbook.add_format()
                cluster_num = id_to_fatcluster_dict[id_emend]
                if cluster_num != -1:
                    cell_color = cluster_color_map[cluster_num]
                    cluster_label = f'({cluster_num})'
                else:
                    cell_color = 'white'
                    cluster_label = ''

                cell_format.set_bg_color(cell_color)
                worksheet1.write(k + 1, column, f'{id_emend} {cluster_label}', cell_format)
                worksheet2.write(k + 1, column, f'{num_emend} {cluster_label}', cell_format)

            column += 1

        # WORKSHEET 3: legenda cluster ordinata per cardinalità del cluster
        worksheet3.write(0, 0, f'Cluster ID')
        worksheet3.write(0, 1, f'ID Emend ->')

        cluster2length_dict = {}
        for item in fatcluster_to_id_dict.keys():
            cluster2length_dict[item] = len(fatcluster_to_id_dict[item])

        row_count = 1
        for clusterId, length in sorted(cluster2length_dict.items(), key=lambda x: x[1], reverse=True):
            cell_format = workbook.add_format()
            cell_format.set_bg_color(cluster_color_map[clusterId])
            worksheet3.write(row_count, 0, f'Cluster ID: {clusterId} (len={length})', cell_format)
            col_count = 1
            for item in fatcluster_to_id_dict[clusterId]:
                worksheet3.write(row_count, col_count, f'ID_EM: {item}', cell_format)
                col_count += 1
            row_count += 1

        # WORKSHEET 4: elenco emendamenti per cluster
        cluster_dictionary = get_cluster_dictionary(similis_engine, flat_clusters, corpus, idatto, verbose)

        worksheet4.write(0, 0, f'Cluster ID')
        worksheet4.write(0, 1, f'Cluster Compactness')

        worksheet4.write(0, 2, f'Art')
        worksheet4.write(0, 3, f'NumEm')

        worksheet4.write(0, 4, f'IdEm')

        worksheet4.write(0, 5, f'Testo')
        worksheet4.write(0, 6, f'Cluster Bean')
        worksheet4.set_column(5, 5, 200)

        row = 1
        for key, value in OrderedDict(sorted(cluster_dictionary.items())).items():
            cell_format = workbook.add_format()
            # print(f'key: {key} value: {value}')

            if not isinstance(value, List):  # se il cluster contiene un solo elemento
                cell_format.set_bg_color('white')
                worksheet4.write(row, 0, key, cell_format)

                # aggiungi cluster COMPACTNESS % (0 per singleton)
                worksheet4.write(row, 1, f'{value["compactness"]:.2f}')
                worksheet4.write(row, 2, value['art'])
                worksheet4.write(row, 3, value['num_em'])
                worksheet4.write(row, 4, value['id_emend'])
                worksheet4.write(row, 5, value['testo_emend'])
                worksheet4.write(row, 6, str(value))
                row += 1
            else:  # Se il cluster contiene più elementi
                cell_format.set_bg_color(cluster_color_map[key])
                for v in value:
                    worksheet4.write(row, 0, key, cell_format)

                    # aggiungi cluster COMPACTNESS %
                    worksheet4.write(row, 1, f'{v["compactness"]:.2f}')

                    worksheet4.write(row, 2, v['art'])
                    worksheet4.write(row, 3, v['num_em'])
                    worksheet4.write(row, 4, v['id_emend'])
                    worksheet4.write(row, 5, v['testo_emend'])
                    worksheet4.write(row, 6, str(v))
                    row += 1

        workbook.close()

        return tmp_file

    corpus = read_emend_list(corpus_item_lists)
    similis_engine = SimilisEngine([c.testo_emend for c in corpus], props.curr_dist_cfg.method)
    flat_clusters = similis_engine.get_flat_clusters(props.curr_dist_cfg.threshold)

    # log_what_if_clustering(corpus, similis_engine)
    # plot_my_dendrogram(corpus, idatto, similis_engine)

    # Generazione del file Excel
    cluster_to_id_dict = cluster_to_id(flat_clusters, corpus)
    fatcluster_to_id_dict = fat_cluster_to_id(cluster_to_id_dict)
    cluster_color_map = get_cluster_color_map(fatcluster_to_id_dict)
    id_to_fatcluster_dict = id_to_fatcluster(cluster_to_id_dict)

    tmp_file = create_excel_grid(similis_engine, id_to_fatcluster_dict, cluster_color_map, fatcluster_to_id_dict,
                                 corpus=corpus)

    with open(tmp_file, "rb") as file:
        bytes_content = file.read()
        logger.info(f"Excel generato in: {tmp_file}")

    return bytes_content


def plot_my_dendrogram(corpus, idatto, similis_engine):
    # use CORPUS INDEX as Dendrogram label
    label_list = list()
    index = 0
    for value in corpus:
        label_list.append(index)
        index = index + 1
    # use id_emend as Dendrogram label
    label_list = [value.id_emend for value in corpus]
    # DENDROGRAM
    plot_dendrogram(similis_engine.get_linkage_matrix(), label_list, f'./log/{idatto}-{props.curr_dist_cfg.method}.png',
                    props.curr_dist_cfg.method, props.curr_dist_cfg.threshold)


def log_what_if_clustering(corpus, similis_engine):
    """
    Stima il what if per il clustering
    :param corpus:
    :param similis_engine:
    :return:
    """

    next_merge = similis_engine.get_next_merge_singleton(props.curr_dist_cfg.threshold)
    # LOG
    for key, value in next_merge.items():
        if value[0] == 'sample':
            next = corpus[value[1]].id_emend
        else:
            next = value[1]
        logger.debug(f'sample id_em {corpus[key].id_emend} would go with {value[0]} {next} with compactness {value[2]}')


def read_emend_list(corpus_item_lists: List[CorpusItem] = None) -> List:
    """
    Legge la lista degli emendamenti relativi all'atto

    :param corpus_item_lists:
    :return:
    """

    corpus = corpus_item_lists

    # rimuove i NBSP e li sostituisce con spazi
    for c in corpus:
        c.testo_emend = c.testo_emend.replace('\xa0', ' ')

    logger.info(f"Corpus di {len(corpus)} elementi")
    if len(corpus) <= 0:
        raise Exception("Corpus vuoto! Controllare i parametri di input.")

    return corpus


def map_to_emend_with_clusters(emend_dict: dict) -> List:
    """
    trasforma la dictionary di cluster ed emendamenti in lista di
    emendamenti con indicazione del cluster

    :param emend_dict:
    :return:
    """
    lista_emend = list()

    def processa_elemento():
        emend['id_cluster'] = k_cluster
        lista_emend.append(emend)

    # ristruttura la lista organizzando i cluster per emendamento
    for k_cluster, v in emend_dict.items():
        if isinstance(v, List):
            # processa emendamenti in lista
            for emend in v:
                processa_elemento()
        else:
            # processa il singolo elemento
            emend = v
            processa_elemento()
    # ordina la lista per id_emend
    lista_emend.sort(key=lambda x: x['id_emend'])
    return lista_emend


def process_json_dto(emends_string: str, include_singleton: bool = False, create_excel: bool = False) -> List:
    """
    Processa un JSON di emendamenti
    """

    def get_cluster_list_for_corpus():
        """
        processa i cluster passandogli gli emendamenti
        """

        d = process_for_cluster_list(0, corpus_list, verbose=False)
        process_for_cluster_excel(0, corpus_list, verbose=True) if create_excel else None

        if include_singleton:
            d = {k: v for k, v in d.items()}
        else:
            d = {k: v for k, v in d.items() if isinstance(v, List)}

        return d

    emends = json.loads(emends_string)
    corpus_list = list()
    index = 0
    for e in emends:

        # Testo preso dal server o no (per maggiore solidità si prende il testo sempre dal client/json di input
        tp = None
        te = Emend.cleanhtml(html.unescape(e['testo_emend']))

        corpus_list.append(
            CorpusItem(index,
                       e['idatto'],
                       e['id_emend'],
                       e['id_testo'],
                       None,
                       e['art'],
                       e['num_em'],
                       e['ver_em'] if 'ver_em' in e else "",
                       te,
                       tp))
        index += 1

    return map_to_emend_with_clusters(get_cluster_list_for_corpus())
