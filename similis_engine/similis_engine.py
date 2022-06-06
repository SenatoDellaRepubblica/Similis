from typing import List

import nltk
from nltk.stem.snowball import SnowballStemmer
import regex as re
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import pairwise_distances

from scipy.cluster.hierarchy import fcluster, linkage, leaders, maxdists
from scipy.spatial.distance import squareform

import logging

from props import COSINE, JACCARD, MAX_DF_COSINE, TF_IDF, TF

logger = logging.getLogger(__name__)


class SimilisEngine:

    def __init__(self, corpus, method):
        self.method = method
        self.corpus = corpus
        self.stemmed_stopwords = []
        self.stemmer = SnowballStemmer("italian")
        self._init_stopwords()
        self._cluster()

    def _tokenize_and_stem(self, text) -> List[str]:

        def tokenize() -> List[str]:
            alphanum_regex = re.compile(r'[\W+]', re.UNICODE)  # any non character
            tokens = alphanum_regex.sub(' ', text).lower().split()
            return tokens

        def stemmize(tokens: List[str]):

            def set_eccezione_stemmer() -> bool:
                """
                Eccezione introdotta per compensare l'errata stemmatizzazione
                """

                if t[:-1].lower() == 'letter':
                    stems.append('letter')
                    return True
                return False

            stems: List[str] = list()
            for t in tokens:
                if not set_eccezione_stemmer():
                    stems.append(self.stemmer.stem(t))

            return stems

        return stemmize(tokenize())

    def _init_stopwords(self):
        self.stopwords = nltk.corpus.stopwords.words('italian')
        self.stopwords.extend('<vir/> <vir> </vir> </vir><vir> '.split())
        for sword in self.stopwords:
            self.stemmed_stopwords.extend(self._tokenize_and_stem(sword))
        return

    def serialize_one_hot_vector(self, onehot_vector):
        df = pd.DataFrame(onehot_vector.T.todense(), index=self.onehot_vectorizer.get_feature_names(),
                          columns=["score"])
        df = df.loc[df.score > 0.0, :]
        ret = df.to_string().replace('\n', ' ').replace('score', '').replace('1.0', '')
        ret = re.sub(' +', ' ', ret)
        return ret

    def serialize_tfidf_vector(self, tfidf_vector):
        df = pd.DataFrame(tfidf_vector.T.todense(), index=self.tfidf_vectorizer.get_feature_names(), columns=["tfidf"])

        df = df.loc[df.tfidf > 0.0, :]
        df = df.sort_values(by=["tfidf"], ascending=False)
        ret = df.to_string().replace('\n', ', ').replace('tfidf, ', '')
        ret = re.sub(' +', ' ', ret).strip()
        return ret

    def _cluster(self):
        logger.info(f'STARTING CLUSTERING for "{self.method.upper()}"')
        if self.method == JACCARD:

            self.onehot_vectorizer = TfidfVectorizer(stop_words=set(self.stemmed_stopwords),
                                                     use_idf=False, tokenizer=self._tokenize_and_stem, binary=True,
                                                     norm=False)
            self.doc2term_matrix = self.onehot_vectorizer.fit_transform(self.corpus)  # fit the vectorizer to corpus

            # scipy distance metrics do not support sparse matrices.
            # DataConversionWarning: Data was converted to boolean for metric jaccard
            jacquard_distance_matrix = pairwise_distances(self.doc2term_matrix.astype(bool).todense(), metric=JACCARD)
            self.doc_similarity_matrix = 1 - jacquard_distance_matrix

            # https://stackoverflow.com/questions/36520043/triangle-vs-square-distance-matrix-for-hierarchical-clustering-python
            # https://github.com/scipy/scipy/issues/2614 (devo lanciarlo su condensed invece che su similarity matrix ?)
            # https://stackoverflow.com/questions/18952587/use-distance-matrix-in-scipy-cluster-hierarchy-linkage
            # squareform: Convert a vector-form distance vector to a square-form distance matrix, and vice-versa.
            self.linkage_matrix = linkage(squareform(jacquard_distance_matrix), method='complete')
        elif self.method == TF_IDF or self.method == TF:
            if self.method == TF_IDF:
                self.tfidf_vectorizer = TfidfVectorizer(max_df=MAX_DF_COSINE, stop_words=set(self.stemmed_stopwords),
                                                        use_idf=True, norm='l2',
                                                        tokenizer=self._tokenize_and_stem)
            elif self.method == TF:
                self.tfidf_vectorizer = TfidfVectorizer(max_df=MAX_DF_COSINE, stop_words=set(self.stemmed_stopwords),
                                                        use_idf=False, norm='l2',
                                                        tokenizer=self._tokenize_and_stem, ngram_range=(1, 1))

            self.doc2term_matrix = self.tfidf_vectorizer.fit_transform(self.corpus)  # fit the vectorizer to corpus
            cosine_distance_matrix = pairwise_distances(self.doc2term_matrix, metric=COSINE)  # 1 -
            self.doc_similarity_matrix = 1 - cosine_distance_matrix
            self.linkage_matrix = linkage(squareform(cosine_distance_matrix, checks=False), method='complete')
        else:
            raise Exception(f"Metodo non corretto {self.method}")

    def get_similarity_matrix(self):
        # return DOC2DOC similarity matrix
        return self.doc_similarity_matrix

    def get_linkage_matrix(self):
        return self.linkage_matrix

    def get_flat_clusters(self, threshold):
        # fcluster: ndarray
        # An array of length n. T[i] is the flat cluster number to which original observation i belongs.
        return fcluster(self.linkage_matrix, t=threshold, criterion='distance')

    def get_cluster_compactness(self, threshold):
        """
        Indice di compattezza del cluster
        :param threshold:
        :return:
        """

        # see: https://joernhees.de/blog/2015/08/26/scipy-hierarchical-clustering-and-dendrogram-tutorial/
        # see: https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.leaders.html
        # see: https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.maxdists.html

        T = fcluster(self.linkage_matrix, t=threshold, criterion='distance')
        L, M = leaders(self.linkage_matrix, T)

        # L: indice del sample, M indice del cluster a cui appartiene
        # (remember that indices 0-11 point to the 12 data points in X, whereas indices 12-22 point to the 11 rows of Z)

        max_dist = maxdists(self.linkage_matrix)
        # la distanza che mi serve è sul vettore maxdist all'indice leader-nsamples
        nsamples = len(self.corpus)

        compactness = dict()

        i = 0
        for index in L:
            if index < nsamples:
                # sono i cluster SINGLETON
                compactness[M[i]] = 0.0  # 1.0
            else:
                compactness[M[i]] = (1 - max_dist[index - nsamples]) * 100  # DISTANCE: max_dist[index-nsamples]

            i = i + 1

            # All indices idx >= len(X) actually refer to the cluster formed in Z[idx - len(X)].

        return compactness

    def get_next_merge_singleton(self, threshold):

        # see: https://joernhees.de/blog/2015/08/26/scipy-hierarchical-clustering-and-dendrogram-tutorial/
        # see: https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.leaders.html
        # see: https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.maxdists.html

        T = fcluster(self.linkage_matrix, t=threshold, criterion='distance')
        L, M = leaders(self.linkage_matrix, T)

        # L: indice del sample, M indice del cluster a cui appartiene
        # (remember that indices 0-11 point to the 12 data points in X, whereas indices 12-22 point to the 11 rows of Z)

        linkage_first_column = self.linkage_matrix[:, 0]
        linkage_second_column = self.linkage_matrix[:, 1]

        nsamples = len(self.corpus)

        next_merge = dict()

        i = 0
        for index in L:
            # analizzo what-if esclusivamente per i singleton (index<nsamples)
            if index < nsamples:
                # il campione singleton compare nella linkage matrix solo quando viene accorpato a qualcuno; 

                # 1) cerca il campione singleton nella prima o nella seconda colonna della Linkage Matrix
                find_column_1 = [k for k in range(len(linkage_first_column)) if
                                 abs(linkage_first_column[k] - L[i]) < 0.001]
                find_column_2 = [k for k in range(len(linkage_first_column)) if
                                 abs(linkage_second_column[k] - L[i]) < 0.001]

                if len(find_column_1) > 0:
                    get = find_column_1[0]
                    merge_with = int(self.linkage_matrix[get, 1])
                elif len(find_column_2) > 0:
                    get = find_column_2[0]
                    merge_with = int(self.linkage_matrix[get, 0])

                # 2) il singleton può essere accorpato con un altro singleton oppure con un cluster precedentemente formato
                # 3) se è un cluster precedentemente formato non è detto che sia fra i nostri cluster, dipende dalla soglia;
                #    lo è se quel cluster fa parte dei "leaders" per la nostra soglia
                if merge_with > nsamples:
                    find_leader = [idx for idx in range(len(L)) if abs(merge_with - L[idx]) < 0.001]
                    if len(find_leader) > 0:
                        merge_type = 'existing_cluster'
                        merge_with = M[find_leader[0]]
                    else:
                        merge_type = 'not_yet_existing_cluster'
                        merge_with = 'unknown'
                else:
                    merge_type = 'sample'
                    # merge_with rimane l'indice del sample trovato nella linkage_matrix

                merge_compactness = (1 - self.linkage_matrix[get, 2]) * 100

                next_merge_item = [merge_type, merge_with, merge_compactness]
                next_merge[L[i]] = next_merge_item

                # print(f'sample {L[i]} would go with {merge_type} {merge_with} with compactness {merge_compactness}')

            i += 1

        return next_merge

    def get_serialized_doctermvector(self, index):
        if self.method == JACCARD:
            return self.serialize_one_hot_vector(self.doc2term_matrix[index])
        elif self.method == TF_IDF or self.method == TF:
            return self.serialize_tfidf_vector(self.doc2term_matrix[index])
        else:
            return 'ERR'
