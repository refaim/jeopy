# -*- coding: utf-8 -*-

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
        return findall(selector, node)[0]

    def apply_regexp(regexp, string):
        match = regexp.match(string)
        if not match:
            raise JeopyError((u'Unable to apply regexp "%s" to string "%s"' %
                (regexp.pattern, string)).encode('cp1251'))
        return match.group(1).strip()

    topic_re = re.compile(r'([^\(]+)')
    question_re = re.compile(r'\d+\.(.+)')

    tree = html.parse(fobj)
    title = find('//h1[@class="title"]/text()', tree)
    topics = {}

    for topic_node in findall('//div[@id="main"]/div[not(@class)]', tree):
        topic = apply_regexp(topic_re,
            find('./*[1]/following-sibling::text()[1]', topic_node)[1:])
        topics[topic] = []
        for question_node in findall('./p', topic_node):
            question_parts = findall('./i/preceding-sibling::text()', question_node)
            question_parts = 'dummy'.join(map(unicode.strip, question_parts))
            question_parts = ' '.join(question_parts.splitlines())
            question = apply_regexp(question_re,
                question_parts.replace('dummy', '\n'))
            answer = find('./i/following::text()[1]', question_node)
            topics[topic].append((question, answer))

    return { 'title': title, 'topics': topics }


def select(suite, count=5):
    topics = suite['topics']
    return { title: topics[title] for title in random.sample(topics, count) }
