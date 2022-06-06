class CorpusItem:
    """
    Classe che definisce un item del Corpus
    """

    def __init__(self, index, id_atto, id_emend, id_testo, tipo_testo, art, num_em, ver_em, testo_emend,
                 testo_path=None):
        """

        :param index:
        :param id_atto:
        :param id_emend:
        :param id_testo:
        :param tipo_testo:
        :param art:
        :param num_em:
        :param ver_em: versione dell'emendamento (ex: Testo 2)
        :param testo_emend:
        """

        self.index = index
        self.id_atto = id_atto
        self.id_emend = id_emend
        self.id_testo = id_testo
        self.tipo_testo = tipo_testo
        self.art = art
        self.num_em = num_em
        self.ver_em = ver_em

        # Se non c'è il testo per qualche motivo ci mette uno spazio
        self.testo_emend = testo_emend if testo_emend else " "

        # Popolato opzionalmente
        self.testo_path = testo_path

    def __str__(self):
        return f'id_atto:{self.id_atto}|id_emend:{self.id_emend}|id_testo:{self.id_testo}|tipo_testo:{self.tipo_testo}|art:{self.art}|num_em:{self.num_em}|ver_em:{self.ver_em} '

    def __repr__(self):
        return str(self)
