from gensim.models import FastText
from gensim.models.fasttext import load_facebook_model

# load the .bin file
ft = load_facebook_model("cc.de.300.bin")


def get_synonym(word: str) -> str | None:
    try:
        neighbors = ft.wv.most_similar(word, topn=20)
        # neighbors = [("Produktion", 0.87), ...]
        neighbors = [i for i in neighbors if i[0].lower() != word.lower()]
        return sorted(neighbors, key=lambda x: x[1], reverse=True)[0]
    except KeyError:
        return None
    return None


print(get_synonym("Instrument"))

