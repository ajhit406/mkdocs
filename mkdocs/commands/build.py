# coding: utf-8
from __future__ import unicode_literals

import datetime
import functools
import logging
import os

import jinja2

from mkdocs.structure.files import get_files
from mkdocs.structure.nav import get_navigation
from mkdocs.structure.pages import build_pages
from mkdocs.structure.urls import get_relative_url, is_active
from mkdocs.utils import write_file, copy_file, clean_directory
import mkdocs

log = logging.getLogger(__name__)


def build(config, live_server=False, dump_json=False, clean_site_dir=False):
    """
    Perform a full site build.
    """
    if clean_site_dir:
        log.info("Cleaning site directory")
        clean_directory(config['site_dir'])
    if not live_server:
        log.info("Building documentation to directory: %s", config['site_dir'])
        if not clean_site_dir and site_directory_contains_stale_files(config['site_dir']):
            log.info("The directory contains stale files. Use --clean to remove them.")

    docs_files = get_files(config['docs_dir'])
    theme_files = get_files(config['theme_dir'][0])
    nav = get_navigation(config['pages'], docs_files)
    build_pages(docs_files)

    global_context = {
        'nav': nav,
        'extra': config['extra'],
        'site_name': config['site_name'],
        'build': {
            'mkdocs_version': mkdocs.__version__,
            'build_date_utc': datetime.datetime.utcnow(),
        },
        'media': {
            'extra_css': [file.input_path for file in docs_files.css_files()],
            'extra_javascript': [file.input_path for file in docs_files.javascript_files()]
        }
    }

    loader = jinja2.FileSystemLoader(config['theme_dir'])
    env = jinja2.Environment(loader=loader)
    template = env.get_template('base.html')

    for file in docs_files.documentation_pages():
        page = file.page
        context = {
            'page': page,
            'url': functools.partial(get_relative_url, from_path=file.input_path),
            'is_active': functools.partial(is_active, current_page=page)
        }
        context.update(global_context)
        output_content = template.render(context)
        output_path = os.path.join(config['site_dir'], file.output_path)
        write_file(output_content.encode('utf-8'), output_path)

    for file in theme_files.media_files() + docs_files.media_files():
        output_path = os.path.join(config['site_dir'], file.output_path)
        copy_file(file.full_input_path, output_path)


def site_directory_contains_stale_files(site_directory):
    """
    Check if the site directory contains stale files from a previous build.
    Right now the check returns true if the directory is not empty.
    A more sophisticated approach should be found to trigger only if there are
    files that won't be overwritten anyway.
    """
    if os.path.exists(site_directory):
        if os.listdir(site_directory):
            return True
    return False
