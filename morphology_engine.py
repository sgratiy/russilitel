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

    def inflect_safe(self, word, source_tag):

        CASES = {
            'nomn', 'gent', 'datv',
            'accs', 'ablt', 'loct'
        }

        NUMBERS = {
            'sing', 'plur'
        }

        target_grams = source_tag.grammemes & (CASES | NUMBERS)

        parses = self.parse(word)

        for p in parses:
            inflected = p.inflect(target_grams)

            if inflected:
                return inflected.word

        return None