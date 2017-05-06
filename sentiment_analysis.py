'''
@author: Team12

'''
import re,math, itertools
import nltk.classify.util
from nltk.classify import NaiveBayesClassifier
from nltk.collocations import BigramCollocationFinder
from nltk.probability import FreqDist, ConditionalFreqDist
from nltk.metrics import BigramAssocMeasures


# predict unlabeled data
def predict(classifier, sentence):
    sentence = simplify_tweet(sentence)
    words = re.findall(r"[\w']+|[.,!?;]", sentence.rstrip())
    words = finding_best_words(words)
    return classifier.classify(words)


# train a classifier using the best features selected
def ta_classifier():
    global stopWordsLsit
    stopWords = open("stop-word-list.txt", "r")

    stopWordsall = stopWords.read()

    stopWordsLsit = stopWordsall.split()

    global bestWords

    basicClassifier(bigram_words)
    
    featureScore = scores()
    
    bestWords = best_words(featureScore)
    
    return advancedCl(advanced_bigram_words)


def scores():
    posWords = []
    negWords = []
    with open('pos.txt', 'r') as posSentences:
        for i in posSentences:
            posWord = re.findall(r"[\w']+|[.,!?;]", i.rstrip())
            posWord = bigram_words(posWord, score_fn=BigramAssocMeasures.chi_sq, n=1000)
            posWords.append(posWord)
    with open('neg.txt', 'r') as negSentences:
        for i in negSentences:
            negWord = re.findall(r"[\w']+|[.,!?;]", i.rstrip())
            negWord = bigram_words(negWord, score_fn=BigramAssocMeasures.chi_sq, n=1000)
            negWords.append(negWord)
    posWords = list(itertools.chain(*posWords))
    negWords = list(itertools.chain(*negWords))

    word_fd = FreqDist()
    cond_word_fd = ConditionalFreqDist()
    for word in posWords:
        word_fd[word] += 1
        cond_word_fd['pos'][word] += 1
    for word in negWords:
        word_fd[word] += 1
        cond_word_fd['neg'][word] += 1

    # finds the number of positive and negative words, as well as the total number of words
    pos_word_count = cond_word_fd['pos'].N()
    neg_word_count = cond_word_fd['neg'].N()
    total_word_count = pos_word_count + neg_word_count

    # builds dictionary of word scores based on chi-squared test
    featureScore = {}
    for word, freq in word_fd.items():
        pos_score = BigramAssocMeasures.chi_sq(cond_word_fd['pos'][word], (freq, pos_word_count), total_word_count)
        neg_score = BigramAssocMeasures.chi_sq(cond_word_fd['neg'][word], (freq, neg_word_count), total_word_count)
        featureScore[word] = pos_score + neg_score

    return featureScore


def best_words(word_scores):
    best_vals = sorted(word_scores.items(), key=lambda w:w[1], reverse=True)[:15000]
    bestWords = set([w for w, s in best_vals])
    return bestWords

def bag_of_words(words):
    return dict([(word, True) for word in words])

def finding_best_words(words):
    return dict([(word, True) for word in words if word in bestWords])
    

def bigram_words(words, score_fn=BigramAssocMeasures.chi_sq, n=1000):
    bigram_finder = BigramCollocationFinder.from_words(words)
    bigrams = bigram_finder.nbest(score_fn, n)
    return (words + bigrams)

def advanced_bigram_words(words, score_fn=BigramAssocMeasures.chi_sq, n=1000):
    bigram_finder = BigramCollocationFinder.from_words(words)
    bigrams = bigram_finder.nbest(score_fn, n)
    return finding_best_words(words + bigrams)


def basicClassifier(featureExtraction):
    posFeatures = []
    negFeatures = []
    
    with open('pos.txt','r') as posText:
        for i in posText:
            posWord = re.findall(r"[\w']+|[.,!?;]", i.rstrip())
            posWord = [bag_of_words(bigram_words(posWord, score_fn=BigramAssocMeasures.chi_sq, n=1000)),'pos']
            posFeatures.append(posWord)
    
    with open('neg.txt','r') as negText:
        for i in negText:
            negWord = re.findall(r"[\w']+|[.,!?;]", i.rstrip())
            negWord = [bag_of_words(bigram_words(negWord, score_fn=BigramAssocMeasures.chi_sq, n=1000)),'neg']
            negFeatures.append(negWord)
    

def advancedCl(advanced_bigram_words):
    posFeatures = []
    negFeatures = []
    
    with open('pos.txt','r') as posText:
        for i in posText:
            posWord = re.findall(r"[\w']+|[.,!?;]", i.rstrip())
            posWord = [advanced_bigram_words(posWord, score_fn=BigramAssocMeasures.chi_sq, n=1000),'pos']
            posFeatures.append(posWord)
    
    with open('neg.txt','r') as negText:
        for i in negText:
            negWord = re.findall(r"[\w']+|[.,!?;]", i.rstrip())
            negWord = [advanced_bigram_words(negWord, score_fn=BigramAssocMeasures.chi_sq, n=1000),'neg']
            negFeatures.append(negWord)
    posCutoff = int(math.floor(len(posFeatures)*3/4))
    negCutoff = int(math.floor(len(negFeatures)*3/4))
    trainFeatures = posFeatures[:posCutoff] + negFeatures[:negCutoff]
    testFeatures = posFeatures[posCutoff:] + negFeatures[negCutoff:]
    
    cl = NaiveBayesClassifier.train(trainFeatures)
    print(nltk.classify.util.accuracy(cl, testFeatures))
    
    return cl


def simplify_tweet(original_tweet):
    new_tweet = re.sub('@[a-zA-Z0-9:_\(\)]+\s', '', original_tweet).lower()
    new_tweet = re.sub(
        '((http|ftp|https)://)(([a-zA-Z0-9\._-]+\.[a-zA-Z]{2,6})|([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}))(:[0-9]{1,4})*(/[a-zA-Z0-9\&%_\./-~-]*)?',
        '', new_tweet)
    new_tweet = re.sub('[^a-zA-z\n\t ]', '', new_tweet)
    new_tweet = re.sub('(\[|\])', '', new_tweet)
    new_tweet= ' '.join([word for word in new_tweet.split() if word not in stopWordsLsit])
    return new_tweet


    
def main():
    
    global bestWords
    
    basicClassifier(bigram_words)
    
    featureScore = scores()
    
    bestWords = best_words(featureScore)
    
    advancedCl(advanced_bigram_words)
    
            

if __name__ == '__main__':
    main()