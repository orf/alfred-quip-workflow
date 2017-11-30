# encoding: utf-8
import argparse
import sys
from workflow import Workflow, ICON_WARNING, web, notify, PasswordNotFound
import webbrowser

user_api = 'https://platform.quip.com/1/users/current'
folders_api = 'https://platform.quip.com/1/folders/'
threads_api = 'https://platform.quip.com/1/threads/'


def get_documents(api_key, logger):
    auth_headers = {'Authorization': 'Bearer {0}'.format(api_key)}
    user_response = web.get(user_api, headers=auth_headers).json()

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
    return [
        {'title': thread['thread']['title'],
         'link': thread['thread']['link'],
         'type': thread['thread']['type'],
         'id': thread['thread']['id']}
        for thread in document_data.values()
    ]


def main(wf):
    try:
        api_key = wf.get_password('quip_api_key')
    except PasswordNotFound:  # API key has not yet been set
        wf.logger.error('No password set')

    wf.cached_data('documents', lambda: get_documents(api_key, wf.logger), max_age=60 * 60 * 60)


if __name__ == u"__main__":
    wf = Workflow()
    sys.exit(wf.run(main))
