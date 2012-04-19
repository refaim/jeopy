import json
import os
import random
import shutil
import string
import StringIO
import urllib2
import urlparse
import zipfile

from lxml import etree

from common import *

def download(url):
    parsed = urlparse.urlparse(url)
    if parsed.netloc != 'db.chgk.info':
        raise JeopyError('Incorrect URL')

    if not url.endswith('/'):
         url += '/'
    url = urlparse.urljoin(url, 'fb2')

    robj = urllib2.urlopen(url)
    fobj = StringIO.StringIO()
    shutil.copyfileobj(robj, fobj)
    robj.close()

    archive = zipfile.ZipFile(fobj, 'r')
    if len(archive.namelist()) != 1:
        raise JeopyError('Wrong file count in the archive')
    fb2name = archive.namelist()[0]
    if os.path.splitext(fb2name)[1] != '.fb2':
        raise JeopyError('No fb2 files found in the archive')

    with archive.open(fb2name, 'rU') as fb2:

        def findall(selector, node):
            xpath = etree.XPath(selector, namespaces={
                'fb2': 'http://www.gribuser.ru/xml/fictionbook/2.0'
            })
            result = xpath(node)
            if not result:
                raise JeopyError(
                    'XML parse error, "%s" not found at node %s on line %d' %
                    (selector, node.tag, node.sourceline))
            return result

        def find(selector, node):
            return findall(selector, node)[0]

        tree = etree.parse(fb2)
        title = find('//fb2:book-title/text()', tree)
        body = find('//fb2:body', tree)
        sections = {}

        # rounds
        for section in findall('//fb2:section', body):
            sectitle = find('.//fb2:title/fb2:p/text()', section)
            sections[sectitle] = {}

            # questions / answers blocks
            for i, poem in enumerate(findall('//fb2:poem', section)):

                is_questions = (i + 1) % 2 != 0

                if is_questions:

                    delnum = lambda s: s.strip()[3:]

                    questions = []
                    rows = map(string.strip, findall('.//fb2:v/text()', poem))
                    blocktitle = rows[0]
                    for row in rows[1:]:
                        if row[0].isdigit():
                            questions.append(delnum(row))
                        else:
                            questions[-1] += u'\n' + row
                    if len(questions) < 5:
                        questions.append(delnum(poem.getnext().text))

                else:

                    answers = map(delnum, findall('.//fb2:v/text()', poem))
                    if len(answers) != 5:
                        raise JeopyError(
                            'Not enough answers at line %d' % poem.sourceline)

                    # save
                    sections[sectitle][blocktitle] = zip(questions, answers)

        suite = { title: sections }
    return suite

def select(suite, count=5):
    blocks = {}
    for sections in suite.itervalues():
        for section in sections.itervalues():
            for title, block in section.iteritems():
                blocks[title] = block
    return random.sample(blocks.items(), count)
