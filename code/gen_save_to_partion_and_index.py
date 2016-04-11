from __future__ import unicode_literals
from nltk.tokenize import PunktWordTokenizer as WordTokenizer
import random
import pprint
import scipy.sparse
import time
import itertools
import sys
import pickle
import helper

tokenizer = WordTokenizer()
int2tags = \
['TAG',\
'Affected_Food_Product',\
'Produced_Location',\
'Distributed_Location']
#Consumer_Brand
#Adulterant(s)
tags2int = \
{'TAG':0,\
'Affected_Food_Product':1, \
'Produced_Location':2, \
'Distributed_Location':3 }
int2citationFeilds = ['Authors', 'Date', 'Title', 'Source']
generic = ["city", "centre", "county", "street", "road", "and", "in", "town", "village"]


def filterArticles(articles):
    relevant_articles = {}
    count = 0
    correct = [0] * len(int2tags)
    gold_num = [0] * len(int2tags)
    helper.load_constants()
    print "Num incidents", len(incidents)
    print "Num unfilitered articles", len(articles)
    for incident_id in incidents.keys():
        incident = incidents[incident_id]
        if not 'citations' in incident:
            continue
        for citation_ind, citation in enumerate(incident['citations']):
            saveFile = "../data/raw_data/"+ incident_id+"_"+str(citation_ind)+".raw"
            if not saveFile in articles:
                continue
            count +=1
            article = articles[saveFile]
            for ent in int2tags:
                if not ent in incident:
                    continue
                gold = incident[ent]

                if ent in ['Affected_Food_Product']:
                    gold_list = gold.split(';')
                elif ent in ["Produced_Location", "Distributed_Location"]:
                    country = gold.split(',')
                    gold_list = gold.split(',')
                else:
                    gold_list = [gold]

                for g in gold_list:
                    g = g.lower().strip()
                    if g in ['', 'none', 'unknown', "0"]:
                        continue
                    clean_g = g.encode("ascii", "ignore")
                    clean_tokens = []
                    for c in tokenizer.tokenize(article):
                        try:
                            clean_tokens.append(c.encode("ascii", "ignore"))
                        except Exception, e:
                            pass
                    clean_article = " ".join(clean_tokens)
                    if clean_g in clean_article.lower():
                        if not saveFile in relevant_articles:
                            relevant_articles[saveFile] = clean_article.lower()
                        if False:
                            print clean_g
                            ind = clean_article.lower().index(clean_g)
                            print clean_article[max(0, ind - 100): min(len(clean_article), ind + 100)]
                        correct[tags2int[ent]] += 1
                gold_num[tags2int[ent]] += 1

    pickle.dump(downloaded_articles, open('EMA_filtered_articles.p', 'wb'))
                    
    oracle_scores = [(correct[i]*1./gold_num[i], int2tags[i]) if gold_num[i] > 100 else 0 for i in range(len(int2tags))]
    print "num articles is", len(relevant_articles)
    return relevant_articles, oracle_scores

def cleanEnts(ent_tokens):
    ascii_tokens = asciiEnts(ent_tokens)
    result = [x.strip().lower() if (not x in generic and x.isalpha()) else "" for x in ascii_tokens]
    return result

def asciiEnts(ent_tokens):
    ascii_tokens = []
    for en in ent_tokens:
        try:
            ascii_tokens.append(en.encode("ascii", "ignore").lower())
        except Exception, e:
            # print "that should not be possible"
            # print en
            ascii_tokens.append(en)
            pass
    return ascii_tokens

def cleanIdent(out_ident, tmp):
    cleaned_identifier = out_ident
    try:
        tmp.write(cleaned_identifier + '\n')
    except Exception, e:
        new_ident = ""
        for c in cleaned_identifier:
            try:
                new_ident += c.encode("ascii", "ignore")
            except Exception, e:
                new_ident += ""
        cleaned_identifier = new_ident;
    return cleaned_identifier

def cleanBody(body, tmp):
    cleanBody = body
    try:
        tmp.write(cleaned_body + '\n')
    except Exception, e:
        new_body = ""
        for c in cleaned_identifier:
            try:
                new_body += c.encode("ascii", "ignore")
            except Exception, e:
                new_body += ""
        cleaned_body = new_body
    return cleanBody




def getTags(article, ents):
    tags = []
    for i, token in enumerate(article):
        labels = []
        token = token.lower().strip()
        for j in range(len(ents)):
            ent = ents[j]

            if "|" in ent:
                ent_set = ent.split("|")
                for possible_ent in ent_set:
                    possible_ents = tokenizer.tokenize(possible_ent)
                    clean_possible_ents = cleanEnts(possible_ents)
                    if token in clean_possible_ents:
                        ind = asciiEnts(possible_ents).index(token)
                        context = article[ max(0,i-ind): min(len(article), i + len(possible_ents)- ind)]
                        if False:
                            print "clean_ents", "tokens"
                            print clean_possible_ents
                            print "**"
                            print cleanEnts(context)
                            print "-------"
                        if clean_possible_ents == cleanEnts(context):
                            labels.append(j+1)
                            break
            else:
                ent_tokens = tokenizer.tokenize(ent)
                if len(ent_tokens) > 1:
                    cleaned_ent_tokens = cleanEnts(ent_tokens)
                    if token in cleaned_ent_tokens:
                        ind = asciiEnts(ent_tokens).index(token)
                        context = article[ max(0,i-ind): min(len(article), i + len(ent_tokens)- ind)]
                        if False:
                            print "clean_ents_tokens", "tokens"
                            print cleaned_ent_tokens
                            print "**"
                            print cleanEnts(context)
                            print "-------"
                        if cleaned_ent_tokens == cleanEnts(context):
                            labels.append(j+1)
                else:
                    try:
                        if cleanEnts([ent]) == cleanEnts([token]):
                            labels.append(j+1)
                    except Exception, e:
                        pass

        label = 0
        if len(labels) > 0:
            label = random.choice(labels)
        tags.append(label)
    return tags

        



if __name__ == "__main__":

    tmp   = open('../data/tagged_data/EMA2/tmp.2.tag', 'w')
    train = open('../data/tagged_data/EMA2/train.2.tag', 'w') ##This is EMA on the server
    dev = open('../data/tagged_data/EMA2/dev.2.tag', 'w')
    test = open('../data/tagged_data/EMA2/test.2.tag', 'w')

    idents_split = pickle.load(open('identifier_to_train_dev_test_partition_and_index.p', 'rb'))

    suspects = {'Black Pepper,Eastern Europe| Ukraine,Eastern Europe| Ukraine':('train',333), \
    'ground beef| Ground Pork,Eastern Europe| Russia,Eastern Europe| Russia': ('train', 146),\
     'Fresh meat products,Eastern Europe| Russia,Eastern Europe| Russia':('test', 94) }
    incidents = pickle.load(open('EMA_dump.p', 'rb'))
    downloaded_articles = pickle.load(open('EMA_downloaded_articles_dump.p.server', 'rb'))

    saveBuffer={}
    indices = {'train': 0, 'dev':0, 'test':0}
    files = {'train': train, 'dev': dev, 'test': test}

    partion_to_ident = {'train': [], 'dev':[], 'test':[] }
    for ident in idents_split.keys():
        articles = idents_split[ident]
        if len(articles) >1:
            print articles
        for part, index in articles:
            if part == 'train':
                if index == 146 or index == 333:
                    print part, index, ident
            if part == 'test':
                if index == 94:
                    print ident
            partion_to_ident[part].append(ident)



    write_buffer = {}
    for partion in indices.keys():
        idents = partion_to_ident[partion]

        print partion, len(idents)
        raw_input()
        write_buffer[partion] = [0]* len(idents)

    refilter = False
    if refilter:
        relevant_articles, unfilitered_scores = filterArticles(downloaded_articles)
        pprint.pprint(unfilitered_scores)
    else:
        relevant_articles = pickle.load(open('EMA_filtered_articles.p.server', 'rb'))

    ratios = {}
    correct = [0] * (len(int2tags)-1)
    count = 0
    count_writes = 0
    count_nopes = 0
    for ind, incident_id in enumerate(incidents.keys()):
        print ind,'/',len(incidents.keys())
        incident = incidents[incident_id]
        if not 'citations' in incident:
            continue
        ents = []
        for ent in int2tags[1:]:
                if ent in incident:
                    gold = incident[ent].encode('ascii', 'ignore')
                    if ent in ['Affected_Food_Product']:
                        gold_list = gold.split(';')
                    elif ent in ["Produced_Location", "Distributed_Location"]:
                        gold_list = []
                        locations =  gold.split(',')
                        for loc in locations:
                            gold_list += loc.split(';')
                    else:
                        gold_list = [gold]
                    ents.append("|".join(gold_list))
                else:
                    ents.append('')
        # pprint.pprint(ents)
        for citation_ind, citation in enumerate(incident['citations']):
            title = incident['citations'][citation_ind]['Title']
            saveFile = "../data/raw_data/"+ incident_id+"_"+str(citation_ind)+".raw"
            if not saveFile in relevant_articles:
                continue
            article = relevant_articles[saveFile]
            #raw_input()
            tokens = tokenizer.tokenize(article)[:1000]
            
            tags = getTags(tokens, ents)
            correct_pass = [0] * (len(int2tags)-1)
            for ent_ind in range(1,len(int2tags)):
                if ent_ind in tags:
                    correct_pass[ent_ind - 1] += 1

            if sum(correct_pass) < 1 :
                continue

            for c_i, c in enumerate(correct_pass):
                correct[c_i] += c
            count += 1
            # pprint.pprint(correct_pass)
            if ','.join(ents) in suspects:
                ennts = ','.join(ents)
                p, i = suspects[ennts]
                # saveBuffer[saveFile] = [("", i)]
                write_buffer[p][i] = ("","",saveFile)
            out_ident = ','.join(ents) + ", " + title

            cleaned_identifier = cleanIdent(out_ident, tmp)

            if not cleaned_identifier in idents_split:
                count_nopes +=1
                continue

            occurances = idents_split[cleaned_identifier]

            tagged_body = ""
            # for token, tag in zip(tokens, tags):
            #     try:
            #         tagged_body += token + "_" + int2tags[tag] + " "
            #     except Exception, e:
            #         tagged_body += ""
            # cleaned_body = cleanBody(tagged_body, tmp)

            for partion, index in occurances:
                # print partion, index
                write_buffer[partion][index] = (cleaned_identifier, tagged_body, saveFile)
                count_writes += 1
                indices[partion] += 1

    count_skip = 0
    for part in write_buffer:
        for i, data in enumerate(write_buffer[part]):
            if data == 1:
                count_skip += 1
                continue
            saveFile = data[2]
            print saveFile

            if saveFile in saveBuffer:
                saveBuffer[saveFile].append((part, i))
            else:
                saveBuffer[saveFile] = [(part, i)]

    ratios =[(correct[i] * 1. / count, int2tags[i+1]) for i in range(len(correct))]
    pprint.pprint(ratios)

    print "nopes:", count_nopes
    for key in indices.keys():
        fails = sum([w == 0 for w in write_buffer[key]])
        print key, "fails",fails

    print 'indices', indices
    print "saveBuffer"
    pprint.pprint( saveBuffer)
    print "sumbuffer len"
    print sum([ len(saveBuffer[f]) for f in saveBuffer ])
    print 'len write buffer'
    print sum([len(write_buffer[t]) for t in ["train", "test", "dev"] ])
    # assert len(saveBuffer) == sum([len(write_buffer[t]) for t in ["train", "test", "dev"] ])

    # pickle.dump(saveBuffer, open('saveFileToPartitionAndIndex','wb'))
    assert sum([ len(saveBuffer[f]) for f in saveBuffer ]) == sum([len(write_buffer[t]) for t in ["train", "test", "dev"] ])

    train.close()
    dev.close()
    test.close()
