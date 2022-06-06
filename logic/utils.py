import logging
import logging.handlers
import random
import props

logger = logging.getLogger(__name__)


def print_non_singleton_clusters_to_TSV(cluster_dict, corpus, file_path):
    """
    Stampa i cluster (non singleton) in un file TSV
    :param cluster_dict:
    :param corpus:
    :param file_path:
    :return:
    """
    header = f"clusterID\tdocID\ttext\tvector\tshowFullText\turl"
    non_singleton_cluster_document = 0
    cluster_num = 0
    with open(file_path, 'w', encoding='utf-8') as file1:
        file1.write(header + "\n")
        for key, value in cluster_dict.items():
            if isinstance(value, list):  # print only non singleton
                cluster_num = cluster_num + 1
                for val in tuple(value):
                    line = f'{key}\t{val}'
                    non_singleton_cluster_document += 1
                    file1.write(line + "\n")

    print(
        f'CLUSTERIZATION - Hierarchical clustering "{props.curr_dist_cfg.method.upper()}"\t - found: {len(cluster_dict)} clusters (including singleton) using THRESHOLD: {props.curr_dist_cfg.threshold}')
    print(
        f'CLUSTERIZATION - Hierarchical clustering "{props.curr_dist_cfg.method.upper()}"\t - non-singleton cluster num: {cluster_num}\t - non-singleton clustered docs: {non_singleton_cluster_document} on {len(corpus)}')
    print(f'Done WRITING cluster "{props.curr_dist_cfg.method.upper()}" output file: "{file_path}"')


def set_log():
    """
    Imposta le caratteristiche del log
    :return:
    """
    format = '%(asctime)s - %(levelname)s - %(message)s (%(name)s)'
    datefmt = '%Y/%m/%d %H:%M:%S'
    logging.basicConfig(datefmt=datefmt, format=format,
                        level=logging.INFO if props.logging_level == 'INFO' else logging.DEBUG)
    formatter = logging.Formatter(fmt=format, datefmt=datefmt)
    # Console Handler
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    consoleHandler.setFormatter(formatter)
    # add the handler to the root logger
    # logging.getLogger().addHandler(consoleHandler)
    # File Handler
    filehandler = logging.handlers.RotatingFileHandler(filename="log/log.txt", maxBytes=1024 * 1024 * 5,
                                                       backupCount=5)
    filehandler.setFormatter(formatter)
    filehandler.setLevel(logging.DEBUG)
    # Memory Handler
    memoryhandler = logging.handlers.MemoryHandler(1024, logging.ERROR, filehandler)
    logging.getLogger().addHandler(memoryhandler)


def limit_char(string_list):
    ret_list = []

    # getting length of list
    length = len(string_list)
    for i in range(length):
        if len(string_list[i]) > 32000:
            ret_list.append(string_list[i][:32000])
        else:
            ret_list.append(string_list[i])

    return ret_list


def get_random_color() -> str:
    def r():
        return random.randint(0, 255)

    return f'#{r():02x}{r():02x}{r():02x}'


def cluster_to_id(flat_clusters, csv_dataframe):
    cluster2id_dict = {}
    for index in range(len(flat_clusters)):

        id_doc = csv_dataframe.iloc[index]["fileNum"]
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


def fat_cluster_to_id(cluster2id_dict):
    fat_cluster_2_id_dict = {}
    for key, value in cluster2id_dict.items():
        if isinstance(value, list):
            fat_cluster_2_id_dict[key] = value
    return fat_cluster_2_id_dict


def id_to_fatcluster(cluster2id_dict):
    id2cluster_dict = {}
    for key, value in cluster2id_dict.items():
        if isinstance(value, list):
            for val in tuple(value):
                id2cluster_dict[val] = key
        else:
            singleton_key = -1
            id2cluster_dict[value] = singleton_key
    return id2cluster_dict


def get_cluster_color_map(fatcluster_to_id_dict):
    cluster2color_dict = {}
    cluster_id = fatcluster_to_id_dict.keys()
    for item in cluster_id:
        picked_color = get_random_color()
        while picked_color in cluster2color_dict.values():
            picked_color = get_random_color()
        cluster2color_dict[item] = picked_color
    return cluster2color_dict
