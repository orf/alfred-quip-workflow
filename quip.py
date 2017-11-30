# encoding: utf-8
import argparse
import sys
from workflow import Workflow, ICON_WARNING, ICON_INFO, web, notify, PasswordNotFound, ICON_WEB
import webbrowser
from workflow.background import run_in_background, is_running

parser = argparse.ArgumentParser()
parser.add_argument('--setkey', dest='apikey', action='store_true')
parser.add_argument('query', nargs='?', default=None)


def main(wf):
    args = parser.parse_args(wf.args)
    if args.apikey:
        if not args.query:
            webbrowser.open('https://marvelapp.quip.com/dev/token')
            return 0

        wf.save_password('quip_api_key', args.query)
        notify.notify('Quip API key set')
        return 0

    try:
        wf.get_password('quip_api_key')
    except PasswordNotFound:  # API key has not yet been set
        wf.add_item('No API key set.',
                    'Please use setquipkey to set your Quip API key.',
                    valid=False,
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    threads = wf.cached_data('documents', None, max_age=0)

    if not wf.cached_data_fresh('documents', max_age=60 * 60 * 60):
        cmd = ['/usr/bin/python', wf.workflowfile('quip-update.py')]
        run_in_background('update', cmd)

    if is_running('update'):
        wf.add_item('Getting documents from Quip',
                    valid=False,
                    icon=ICON_INFO)

    if args.query and threads:
        threads = wf.filter(args.query, threads, key=lambda item: item['title'], min_score=20)

    if not threads:  # we have no data to show, so show a warning and stop
        wf.add_item('No threads found', icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    for thread in threads:
        wf.add_item(title=thread['title'], arg=thread['link'],
                    uid=thread['id'], icon=ICON_WEB, valid=True)

    wf.send_feedback()


if __name__ == u"__main__":
    wf = Workflow()
    sys.exit(wf.run(main))
