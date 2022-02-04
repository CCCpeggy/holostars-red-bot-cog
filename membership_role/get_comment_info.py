"""
Reference: youtube-comment-downloader
Link: https://github.com/egbertbouman/youtube-comment-downloader

The MIT License (MIT)

Copyright (c) 2015 Egbert Bouman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import requests
import json
import re

YOUTUBE_VIDEO_URL = 'https://www.youtube.com/watch?v={youtube_id}'
YOUTUBE_VIDEO_URL_INCLUDE_COMMENT = 'https://www.youtube.com/watch?v={youtube_id}&lc={comment_id}'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
YT_CFG_RE = r'ytcfg\.set\s*\(\s*({.+?})\s*\)\s*;'
YT_INITIAL_DATA_RE = r'(?:window\s*\[\s*["\']ytInitialData["\']\s*\]|ytInitialData)\s*=\s*({.+?})\s*;\s*(?:var\s+meta|</script|\n)'

def regex_search(text, pattern, group=1, default=None):
    match = re.search(pattern, text)
    return match.group(group) if match else default
    
def search_dict(partial, search_key):
    stack = [partial]
    while stack:
        current_item = stack.pop()
        if isinstance(current_item, dict):
            for key, value in current_item.items():
                if key == search_key:
                    yield value
                else:
                    stack.append(value)
        elif isinstance(current_item, list):
            for value in current_item:
                stack.append(value)

def ajax_request(session, endpoint, ytcfg, retries=5, sleep=20):
    url = 'https://www.youtube.com' + endpoint['commandMetadata']['webCommandMetadata']['apiUrl']
    data = {'context': ytcfg['INNERTUBE_CONTEXT'],
            'continuation': endpoint['continuationCommand']['token']}

    for _ in range(retries):
        response = session.post(url, params={'key': ytcfg['INNERTUBE_API_KEY']}, json=data)
        if response.status_code == 200:
            return response.json()
        if response.status_code in [403, 413]:
            return {}
        else:
            time.sleep(sleep)

def get_comment_info(video_id, channel_id=None, comment_id=None):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT

    if comment_id:
        response = session.get(YOUTUBE_VIDEO_URL_INCLUDE_COMMENT.format(youtube_id=video_id, comment_id=comment_id))
    else:
        response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=video_id))
    
    if 'uxe=' in response.request.url:
        session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
        response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=video_id))

    html = response.text
    ytcfg = json.loads(regex_search(html, YT_CFG_RE, default=''))
    if not ytcfg:
        return # Unable to extract configuration

    data = json.loads(regex_search(html, YT_INITIAL_DATA_RE, default=''))

    section = next(search_dict(data, 'itemSectionRenderer'), None)
    renderer = next(search_dict(section, 'continuationItemRenderer'), None) if section else None
    if not renderer:
        # Comments disabled?
        return
    continuations = [renderer['continuationEndpoint']]
    while continuations:
        continuation = continuations.pop()
        response = ajax_request(session, continuation, ytcfg)

        if not response:
            break
        if list(search_dict(response, 'externalErrorMessage')):
            raise RuntimeError('Error returned from server: ' + next(search_dict(response, 'externalErrorMessage')))

        actions = list(search_dict(response, 'reloadContinuationItemsCommand')) + \
                  list(search_dict(response, 'appendContinuationItemsAction'))
        for action in actions:
            for item in action.get('continuationItems', []):
                if action['targetId'] == 'comments-section':
                    # Process continuations for comments and replies.
                    continuations[:0] = [ep for ep in search_dict(item, 'continuationEndpoint')]
                if action['targetId'].startswith('comment-replies-item') and 'continuationItemRenderer' in item:
                    # Process the 'Show more replies' button
                    continuations.append(next(search_dict(item, 'buttonRenderer'))['command'])

        for comment in list(search_dict(response, 'commentRenderer')):
            author_channel_id = comment['authorEndpoint']['browseEndpoint'].get('browseId', '')
            if not channel_id or author_channel_id == channel_id:
                if not comment_id or comment_id == comment['commentId']:
                    if len(list(search_dict(comment, 'tooltip'))) > 0:
                        return {
                            "comment_id": comment['commentId'],
                            "text": ''.join([c['text'] for c in comment['contentText'].get('runs', [])]),
                            "author": comment.get('authorText', {}).get('simpleText', ''),
                            "photo": comment['authorThumbnail']['thumbnails'][-1]['url'],
                        }
                    return False
    return None
            # print()
            # print(''.join([c['text'] for c in comment['contentText'].get('runs', [])]))


if __name__ == "__main__":
    data = get_comment_info("d-XSkvEVg20", channel_id="UCAe4Mp23H_Mc3w1yZOCR-uA")
    print(data)
    data = get_comment_info("d-XSkvEVg20", channel_id="UCsR4jiCU0tPEk8-jRv02aVg")
    print(data)
    data = get_comment_info("d-XSkvEVg20", channel_id="UCqoW8wtwI20rmtr69UItpvw")
    print(data)
    data = get_comment_info("d-XSkvEVg20", channel_id="UCqoW8wtwI20rmtr69UItpvw", comment_id="UgxdD71L8GQ-eLLC4y94AaABAg")
    print(data)
    data = get_comment_info("d-XSkvEVg20", comment_id="UgxdD71L8GQ-eLLC4y94AaABAg")
    print(data)
    