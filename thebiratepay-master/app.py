'''
This is the main module
'''
import os

import requests
import re
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from datetime import datetime, timedelta


APP = Flask(__name__)
CORS(APP)
EMPTY_LIST = []

BASE_URL = os.getenv('BASE_URL', 'https://thepiratebay.org/')
JSONIFY_PRETTYPRINT_REGULAR = True
MIN_SEEDS = int(os.getenv('BIRATEPAY_MIN_SEEDS', '10'))  # Minimum seeds required for a torrent to be returned

# Translation table for sorting filters
sort_filters = {
    'title_asc': 1,
    'title_desc': 2,
    'time_desc': 3,
    'time_asc': 4,
    'size_desc': 5,
    'size_asc': 6,
    'seeds_desc': 7,
    'seeds_asc': 8,
    'leeches_desc': 9,
    'leeches_asc': 10,
    'uploader_asc': 11,
    'uploader_desc': 12,
    'category_asc': 13,
    'category_desc': 14
}


@APP.route('/', methods=['GET'])
def index():
    '''
    This is the home page and contains links to other API
    '''
    return render_template('index.html'), 200


@APP.route('/top/', methods=['GET'])
@APP.route('/top48h/', methods=['GET'])
def default_top():
    '''
    Returns default page with categories
    '''
    return render_template('top.html'), 200


@APP.route('/top/<int:cat>/', methods=['GET'])
def top_torrents(cat=0):
    '''
    Returns top torrents
    '''

    sort = request.args.get('sort')
    sort_arg = sort if sort in sort_filters else ''

    if cat == 0:
        url = BASE_URL + 'top/' + 'all/' + str(sort_arg)
    else:
        url = BASE_URL + 'top/' + str(cat) + '/' + str(sort_arg)
    return jsonify(parse_page(url, sort=sort_arg)), 200


@APP.route('/top48h/<int:cat>/', methods=['GET'])
def top48h_torrents(cat=0):
    '''
    Returns top torrents last 48 hrs
    '''

    sort = request.args.get('sort')
    sort_arg = sort if sort in sort_filters else ''

    if cat == 0:
        url = BASE_URL + 'top/48h' + 'all/'
    else:
        url = BASE_URL + 'top/48h' + str(cat)

    return jsonify(parse_page(url, sort=sort_arg)), 200


@APP.route('/recent/', methods=['GET'])
@APP.route('/recent/<int:page>/', methods=['GET'])
def recent_torrents(page=0):
    '''
    This function implements recent page of TPB
    '''
    sort = request.args.get('sort')
    sort_arg = sort if sort in sort_filters else ''

    url = BASE_URL + 'recent/' + str(page)
    return jsonify(parse_page(url, sort=sort_arg)), 200


@APP.route('/api-search/', methods=['GET'])
def api_search():
    url = BASE_URL + 's/?' + request.query_string.decode('utf-8')
    return jsonify(parse_page(url)), 200


@APP.route('/search/', methods=['GET'])
def default_search():
    '''
    Default page for search
    '''
    return 'No search term entered<br/>Format for search: /search/search_term/page_no(optional)/'


@APP.route('/search/<term>/', methods=['GET'])
@APP.route('/search/<term>/<int:page>/', methods=['GET'])
def search_torrents(term=None, page=0):
    '''
    Searches TPB using the given term. If no term is given, defaults to recent.
    '''

    sort = request.args.get('sort')
    sort_arg = sort_filters[request.args.get('sort')] if sort in sort_filters else ''

    url = BASE_URL + 'search/' + str(term) + '/' + str(page) + '/' + str(sort_arg)
    return jsonify(parse_page(url)), 200


def parse_page(url, sort=None):
    '''
    This function parses the page and returns list of torrents
    '''
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.text
    except Exception as e:  # Broad except so the service keeps running even if upstream fails
        return []
    soup = BeautifulSoup(data, 'lxml')
    table_present = soup.find('table', {'id': 'searchResult'})
    if table_present is None:
        # Attempt fallback via apibay JSON API when HTML table missing
        fallback = apibay_fallback(url)
        if fallback:
            return fallback
        return EMPTY_LIST
    titles = parse_titles(soup)
    links = parse_links(soup)
    magnets = parse_magnet_links(soup)
    times, sizes, uploaders = parse_description(soup)
    seeders, leechers = parse_seed_leech(soup)
    cat, subcat = parse_cat(soup)
    torrents = []
    for torrent in zip(titles, magnets, times, sizes, uploaders, seeders, leechers, cat, subcat, links):
        try:
            seeds_val = int(torrent[5])
        except Exception:
            seeds_val = 0
        if seeds_val < MIN_SEEDS:
            continue
        torrents.append({
            'title': torrent[0],
            'magnet': torrent[1],
            'time': convert_to_date(torrent[2]),
            'size': convert_to_bytes(torrent[3]),
            'uploader': torrent[4],
            'seeds': seeds_val,
            'leeches': int(torrent[6]) if str(torrent[6]).isdigit() else 0,
            'category': torrent[7],
            'subcat': torrent[8],
            'id': torrent[9],
        })

    if sort:
        sort_params = sort.split('_')
        torrents = sorted(torrents, key=lambda k: k.get(sort_params[0]), reverse=sort_params[1].upper() == 'DESC')

    return torrents


def apibay_fallback(original_url: str):
    """Fallback to apibay.org JSON API if primary scrape fails.

    original_url example: https://thepiratebay.org/search/naked gun/0/7
    We only attempt fallback for search URLs.
    """
    try:
        # Only proceed if it's a search pattern we recognize
        if '/search/' not in original_url:
            return []
        # Extract term between '/search/' and the next '/'
        after = original_url.split('/search/', 1)[1]
        term = after.split('/')[0]
        if not term:
            return []
        term_decoded = requests.utils.unquote(term)
        api_url = f"https://apibay.org/q.php?q={requests.utils.quote(term_decoded)}&cat=0"
        r = requests.get(api_url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or not data:
            return []
        torrents = []
        for item in data:
            if not isinstance(item, dict):
                continue
            name = item.get('name')
            info_hash = item.get('info_hash')
            if not name or not info_hash:
                continue
            # Build magnet link
            magnet = (
                f"magnet:?xt=urn:btih:{info_hash}&dn={requests.utils.quote(name)}"
            )
            # Seeds / leeches
            try:
                seeds = int(item.get('seeders') or 0)
                leeches = int(item.get('leechers') or 0)
            except ValueError:
                seeds = 0
                leeches = 0
            # Size as int bytes
            try:
                size_bytes = int(item.get('size') or 0)
            except ValueError:
                size_bytes = 0
            # Added (epoch) -> datetime
            added_epoch = item.get('added')
            try:
                added_dt = datetime.utcfromtimestamp(int(added_epoch)) if added_epoch else datetime.utcnow()
            except Exception:
                added_dt = datetime.utcnow()
            if seeds >= MIN_SEEDS:
                torrents.append({
                    'title': name,
                    'magnet': magnet,
                    'time': added_dt,
                    'size': size_bytes,
                    'uploader': item.get('username'),
                    'seeds': seeds,
                    'leeches': leeches,
                    'category': item.get('category'),
                    'subcat': '',
                    'id': item.get('id') or info_hash,
                    'fallback': 'apibay'
                })
        # Sort by seeds descending to mimic typical sort preference
        torrents.sort(key=lambda t: t.get('seeds', 0), reverse=True)
        return torrents
    except Exception:
        return []


def parse_magnet_links(soup):
    '''
    Returns list of magnet links from soup
    '''
    magnets = soup.find('table', {'id': 'searchResult'}).find_all('a', href=True)
    magnets = [magnet['href'] for magnet in magnets if 'magnet' in magnet['href']]
    return magnets


def parse_titles(soup):
    '''
    Returns list of titles of torrents from soup
    '''
    titles = soup.find_all(class_='detLink')
    titles[:] = [title.get_text() for title in titles]
    return titles


def parse_links(soup):
    '''
    Returns list of links of torrents from soup
    '''
    links = soup.find_all('a', class_='detLink', href=True)
    links[:] = [link['href'] for link in links]
    return links


def parse_description(soup):
    '''
    Returns list of time, size and uploader from soup
    '''
    description = soup.find_all('font', class_='detDesc')
    description[:] = [desc.get_text().split(',') for desc in description]
    times, sizes, uploaders = map(list, zip(*description))
    times[:] = [time.replace(u'\xa0', u' ').replace('Uploaded ', '') for time in times]
    sizes[:] = [size.replace(u'\xa0', u' ').replace(' Size ', '') for size in sizes]
    uploaders[:] = [uploader.replace(' ULed by ', '') for uploader in uploaders]
    return times, sizes, uploaders


def parse_seed_leech(soup):
    '''
    Returns list of numbers of seeds and leeches from soup
    '''
    slinfo = soup.find_all('td', {'align': 'right'})
    seeders = slinfo[::2]
    leechers = slinfo[1::2]
    seeders[:] = [seeder.get_text() for seeder in seeders]
    leechers[:] = [leecher.get_text() for leecher in leechers]
    return seeders, leechers


def parse_cat(soup):
    '''
    Returns list of category and subcategory
    '''
    cat_subcat = soup.find_all('center')
    cat_subcat[:] = [c.get_text().replace('(', '').replace(')', '').split() for c in cat_subcat]
    cat = [cs[0] for cs in cat_subcat]
    subcat = [' '.join(cs[1:]) for cs in cat_subcat]
    return cat, subcat


def convert_to_bytes(size_str):
    '''
    Converts torrent sizes to a common count in bytes.
    '''
    size_data = size_str.split()

    multipliers = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB']

    size_magnitude = float(size_data[0])
    multiplier_exp = multipliers.index(size_data[1])
    size_multiplier = 1024 ** multiplier_exp if multiplier_exp > 0 else 1

    return size_magnitude * size_multiplier


def convert_to_date(date_str):
    '''
    Converts the dates into a proper standardized datetime.
    '''
    date_format = None

    if re.search(r'^[0-9]+ min(s)? ago$', date_str.strip()):
        minutes_delta = int(date_str.split()[0])
        torrent_dt = datetime.now() - timedelta(minutes=minutes_delta)
        date_str = '{}-{}-{} {}:{}'.format(torrent_dt.year, torrent_dt.month, torrent_dt.day, torrent_dt.hour, torrent_dt.minute)
        date_format = '%Y-%m-%d %H:%M'

    elif re.search(r'^[0-9]*-[0-9]*\s[0-9]+:[0-9]+$', date_str.strip()):
        today = datetime.today()
        date_str = '{}-'.format(today.year) + date_str
        date_format = '%Y-%m-%d %H:%M'
    
    elif re.search(r'^Today\s[0-9]+\:[0-9]+$', date_str):
        today = datetime.today()
        date_str = date_str.replace('Today', '{}-{}-{}'.format(today.year, today.month, today.day))
        date_format = '%Y-%m-%d %H:%M'
    
    elif re.search(r'^Y-day\s[0-9]+\:[0-9]+$', date_str):
        today = datetime.today() - timedelta(days=1)
        date_str = date_str.replace('Y-day', '{}-{}-{}'.format(today.year, today.month, today.day))
        date_format = '%Y-%m-%d %H:%M'

    else:
        date_format = '%m-%d %Y'

    return datetime.strptime(date_str, date_format)


@APP.route('/health', methods=['GET'])
def health():
    """Simple health endpoint for readiness checks."""
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    # Prefer BIRATEPAY_PORT then PORT env vars, default 5055
    port = int(os.getenv('BIRATEPAY_PORT') or os.getenv('PORT') or '5055')
    # Bind only to localhost by default for safety; adjust if remote access desired
    APP.run(host='127.0.0.1', port=port)
