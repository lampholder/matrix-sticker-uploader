import io
import json
import glob

import argparse
import requests
import magic

parser = argparse.ArgumentParser()
parser.add_argument('--token', type=str)
parser.add_argument('--homeserver', type=str, default='https://matrix.org')
parser.add_argument('--thumbnail', action='store_true')
parser.add_argument('files', nargs='+')

args = parser.parse_args()

# Which files are we uploading?
files = []
for expression in args.files:
    expanded = glob.glob(expression)
    for f in expanded:
        files.append((f, magic.from_file(f, mime=True)))

report = []

def persist_thumbnail(homeserver, access_token, mimetype, original_mxc, height=100, width=100):
    mxc_id = original_mxc[6:]

    params = {'height': height,
              'width': width}

    request = requests.get(homeserver + '/_matrix/media/v1/thumbnail/' + mxc_id,
                           params=params,
                           stream=True)

    image = io.BytesIO()
    for chunk in request.iter_content(1024):
        image.write(chunk)
    image.seek(0)

    request = requests.post(homeserver + '/_matrix/media/v1/upload',
                            params={'access_token': access_token},
                            headers={'Content-type': mimetype},
                            data=image.read())

    return request.json()['content_uri']


for filename, mimetype in files:
    with open(filename, 'rb') as content_file:
        headers = {'Content-Type': mimetype}
        params = {'access_token': args.token,
                  'filename': filename}

        request = requests.post(args.homeserver + '/_matrix/media/v1/upload',
                                params=params,
                                headers=headers,
                                data=content_file.read())
        mxc = request.json()['content_uri']

        content_object = {'filename': filename,
                          'mxc': mxc,
                          'mimetype': mimetype}

        if args.thumbnail and mimetype.split('/')[0] == 'image':
            thumbnail_mxc = persist_thumbnail(args.homeserver,
                                              args.token,
                                              mimetype,
                                              mxc)

            content_object['thumbnail'] = thumbnail_mxc

        report.append(content_object)

print(json.dumps(report, indent=2))
