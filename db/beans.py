# -*- coding: utf-8 -*-
import html
import logging
from pathlib import Path
import re
from typing import Optional

logger = logging.getLogger(__name__)


class Fase(object):
    """
    Una Fase come struttura
    """

    def __init__(self, id_fase, num_atto):
        self.id_fase = id_fase
        self.num_atto = num_atto


class Emend(object):
    """
    Un emendamento come struttura
    """

    _pTestoem = re.compile(r'<TESTOEM[^>]*>(?P<TESTO>.+?)</TESTOEM>', flags=re.S | re.I)

    @staticmethod
    def cleanhtml(raw_html):
        cleanr = re.compile('<.*?>', flags=re.S | re.I)
        return re.sub(cleanr, ' ', raw_html)

    def __init__(self,
                 fs_emend_path,
                 idoggtratt,
                 idtestoatto,
                 idemend,
                 tipo,
                 tipoem,
                 numem,
                 verem,
                 nota_numem,
                 esito):

        self.valido = True
        self.valido_html = True
        self.valido_xml = True

        self.fs_emend_path = fs_emend_path
        self.idemend = idemend
        self.idtestoatto = idtestoatto
        self.idoggtratt = idoggtratt
        self.tipo = tipo
        self.tipoem = tipoem
        self.numem = numem.strip()
        self.nota_numem = nota_numem
        self.esito = esito

        # serve solo per il debug in una exception
        self._path_testo = self.fs_emend_path + \
                           r"/{0}/{1:08d}/{2:08d}" \
                               .format(self.tipo.capitalize(),
                                       self.idoggtratt,
                                       self.idtestoatto)

        # ricava l'articolo a partire dal numero emendamento

        if self.numem[:1] == 'G':
            # ex: G/1766/102/5 -> G/1766/102
            self.art = self.numem.rsplit('/', 1)[0]
        else:
            # ex: 1.1 -> 1
            self.art = self.numem.split('.', 1)[0]

        self.verem = verem

    def leggi_testo(self) -> Optional[str]:
        path = self.fs_emend_path + fr"/{self.tipo.capitalize()}/{self.idoggtratt:08d}/{self.idtestoatto:08d}.htm"
        try:

            # with Path(path).open(mode='r', encoding='iso-8859-1', errors="ignore") as handle:
            #    if match := re.search(self._pTestoem, handle.read()):
            #        return Emend._cleanhtml(html.unescape(match.group('TESTO')))

            return Emend.leggi_testo_from_path(path)

        except FileNotFoundError:
            logger.error(
                f'Errore nella lettura del file: {path} - ID_OGG_TRATT: {self.idoggtratt}, ID_EMEND: {self.idemend}, ID_TESTO: {self.idtestoatto},')
            # True se c'è il timestamp, False se non c'è, None se c'è stata un'eccezione di lettura del file

        return None

    @staticmethod
    def leggi_testo_from_path(path: str):
        with Path(path).open(mode='r', encoding='iso-8859-1', errors="ignore") as handle:
            if match := re.search(Emend._pTestoem, handle.read()):
                return Emend.cleanhtml(html.unescape(match.group('TESTO')))
