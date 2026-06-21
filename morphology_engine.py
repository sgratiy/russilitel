import pymorphy3


class MorphologyEngine:
    """
    Thin wrapper around pymorphy3.

    Purpose:
    - centralize morphology access
    - provide one place for future ambiguity handling
    - provide safe inflection helpers
    """

    def __init__(self):
        self.morph = pymorphy3.MorphAnalyzer()

    # -----------------------------
    # BASIC ACCESS
    # -----------------------------

    def parse(self, word):
        """
        Return all parses from pymorphy3.
        """
        return self.morph.parse(word)

    def best_parse(self, word):
        """
        Return the most probable parse.
        """
        parses = self.morph.parse(word)

        if not parses:
            return None

        return parses[0]

    # -----------------------------
    # SIMPLE HELPERS
    # -----------------------------

    def normal_form(self, word):
        """
        Return lemma.
        """
        parsed = self.best_parse(word)

        if not parsed:
            return word

        return parsed.normal_form

    def is_known(self, word):
        """
        Is word known to pymorphy.
        """
        parsed = self.best_parse(word)

        if not parsed:
            return False

        return parsed.is_known

    # -----------------------------
    # INFLECTION
    # -----------------------------

    def inflect_safe(self, word, target_tag):
        """
        Try to inflect word into grammatical form
        described by target_tag.

        Returns:
            inflected word or None
        """

        parses = self.parse(word)

        if not parses:
            return None

        best_result = None
        best_score = -1

        for p in parses:
            try:
                inflected = p.inflect(target_tag.grammemes)

                if inflected and p.score > best_score:
                    best_result = inflected.word
                    best_score = p.score

            except Exception:
                pass

        return best_result