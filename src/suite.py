import random
import re
import shutil
import StringIO
import urllib2
import urlparse

from lxml import etree, html

from common import *


def download(url):
    robj = urllib2.urlopen(url)
    fobj = StringIO.StringIO()
    shutil.copyfileobj(robj, fobj)
    fobj.seek(0)
    robj.close()
    return fobj


def parse(fobj):
    def findall(selector, node):
        xpath = etree.XPath(selector)
        return xpath(node)

    def find(selector, node):
        result = findall(selector, node)
        if isinstance(result, list):
            return result[0]
        return result

    question_re = re.compile(r'^\d\.\s?')

    tree = html.parse(fobj)
    title = find('//h1[@class="title"]/text()', tree)
    topics = {}

    for topic_node in findall('//div[@id="main"]/div[not(@class)]', tree):
        topic = find(
            'substring-before(./*[1]/following-sibling::text()[1], "(")',
            topic_node)[1:].strip()
        topics[topic] = []
        for question_node in findall('./p', topic_node):

            # ['text\nwith\nnewlines\n', 'verse', 'verse', ..., 'text\nagain\n']
            question = '\n'.join(block.strip().replace('\n', ' ') for block in
                findall('./i/preceding-sibling::text()', question_node))
            question = question_re.sub('', question, count=1) # strip number

            answer = find('./i/following::text()[1]', question_node)
            topics[topic].append((question, answer))

    return { 'title': title, 'topics': topics }


def select(suite, count=5):
    topics = suite['topics']
    return { title: topics[title] for title in random.sample(topics, count) }
