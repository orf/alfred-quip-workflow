# encoding: utf-8
import argparse
import sys
from workflow import Workflow, ICON_WARNING, ICON_INFO, notify, PasswordNotFound
from workflow.workflow import ICON_ROOT
import os
import webbrowser
from workflow.background import run_in_background, is_running

parser = argparse.ArgumentParser()
parser.add_argument('--setkey', dest='apikey', action='store_true')
parser.add_argument('query', nargs='?', default=None)

import sqlite3


ICON_DOCUMENT = os.path.join(ICON_ROOT, 'ClippingText.icns')


def main(wf):
    if wf.update_available:
        # Add a notification to top of Script Filter results
        wf.add_item('New version available',
                    'Action this item to install the update',
                    autocomplete='workflow:update',
                    icon=ICON_INFO)

    args = parser.parse_args(wf.args)
    if args.apikey:
        if not args.query:
            webbrowser.open('https://quip.com/dev/token')
            return 0

        wf.save_password('quip_api_key', args.query)
        notify.notify('Quip API key set')
        return 0

    try:
        wf.get_password('quip_api_key')
    except PasswordNotFound:  # API key has not yet been set
        wf.add_item('No API key set.',
                    'Please use set-quip-key to set your Quip API key.',
                    valid=False,
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    cached_threads = wf.cached_data('documents', None, max_age=0)

    if not wf.cached_data_fresh('documents', max_age=60 * 60):
        cmd = ['/usr/bin/python', wf.workflowfile('quip-update.py')]
        run_in_background('update', cmd)

    if is_running('update'):
        wf.add_item('Updating documents from Quip',
                    valid=False,
                    icon=ICON_INFO)
    if args.query:
        # Yes, this really shouldn't be re-creating the database each time, but hey-ho. Seems fast enough
        query = args.query.lower().strip() + '*'
        db = sqlite3.connect(':memory:')

        cursor = db.cursor()
        cursor.execute('CREATE VIRTUAL TABLE threads USING fts5(id, title, link, text)')
        cursor.executemany('INSERT INTO threads (id, title, link, text) VALUES (?, ?, ?, ?)',
                           [
                               (result['id'], result['title'], result['link'], result['text'])
                               for result in (cached_threads or [])
                           ])
        cursor.execute('''SELECT id, title, link,
                            snippet(threads, 3, '', '', '', 10) as text_highlight
                          FROM threads
                          WHERE threads MATCH ?
                          ORDER BY bm25(threads, 0, 1.0, 0, 0.5)
                          LIMIT 15''', (query,))
        threads = cursor.fetchall()
        # wf.logger.info(threads2)
        # threads = wf.filter(query, threads, key=lambda item: item['title'], min_score=20)

        if not threads:  # we have no data to show, so show a warning and stop
            wf.add_item('No documents found', icon=ICON_WARNING)
            wf.send_feedback()
            return 0

        for (id, title, link, snippet) in threads:
            wf.add_item(title=title, arg=link,
                        quicklookurl=link,
                        subtitle=snippet,
                        icon=ICON_DOCUMENT,
                        uid=id, valid=True)
    else:
        wf.add_item('Enter a search term', valid=False, icon=ICON_INFO)

    wf.send_feedback()


if __name__ == u"__main__":
    wf = Workflow(normalization='NFD', update_settings={
        'github_slug': 'orf/alfred-quip-workflow',
        'frequency': 1,
    })
    sys.exit(wf.run(main))
