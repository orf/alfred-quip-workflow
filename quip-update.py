# encoding: utf-8
import sys
from workflow import Workflow, web, PasswordNotFound, notify

user_api = 'https://platform.quip.com/1/users/current'
folders_api = 'https://platform.quip.com/1/folders/'
threads_api = 'https://platform.quip.com/1/threads/'

from HTMLParser import HTMLParser


class Parser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.text = []

    def handle_data(self, data):
        data = data.strip()
        if data:
            self.text.append(' '.join(d.strip().lower() for d in data.split(' ') if d.strip()))


def get_documents(wf, api_key, logger):
    auth_headers = {'Authorization': 'Bearer {0}'.format(api_key)}
    user_response = web.get(user_api, headers=auth_headers)

    if user_response.status_code != 200:
        wf.delete_password('quip_api_key')
        notify.notify('Quip API key incorrect, please re-set')
    else:
        user_response = user_response.json()

    folders = user_response['group_folder_ids'] + [user_response['private_folder_id']]
    documents = set()

    while folders:
        logger.info('{0} folders left'.format(len(folders)))
        folder_ids = ','.join(folders)
        folder_responses = web.get(folders_api, {'ids': folder_ids}, headers=auth_headers).json()
        folders = []

        for folder_info in folder_responses.values():
            children = folder_info['children']
            documents.update({child['thread_id'] for child in children if child.get('thread_id')})
            folders.extend(child['folder_id'] for child in children if child.get('folder_id'))

    logger.info('Fetching {0} documents'.format(len(documents)))
    document_ids = ','.join(documents)
    document_data = web.get(threads_api, {'ids': document_ids}, headers=auth_headers).json()

    results = []

    for thread in document_data.values():
        parser = Parser()
        result = {'title': thread['thread']['title'],
                  'link': thread['thread']['link'],
                  'type': thread['thread']['type'],
                  'id': thread['thread']['id']}

        parser.feed(thread.get('html', ''))
        result['text'] = wf.decode(' '.join(parser.text))
        results.append(result)

    return results


def main(wf):
    try:
        api_key = wf.get_password('quip_api_key')
    except PasswordNotFound:  # API key has not yet been set
        wf.logger.error('No password set')
        return

    wf.cache_data('documents', get_documents(wf, api_key, wf.logger))


if __name__ == u"__main__":
    wf = Workflow(normalization='NFD')
    sys.exit(wf.run(main))
