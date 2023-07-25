import os
import subprocess

from bottle import redirect, request, route, run, template
from parser.content_parser import execute_ansiblelint
from parser.downloader import Downloader
from parser.report import filetype_summary, module_summary, generate_graphviz_dot_file

RESULT = None
APP_WORK_DIR = os.getenv('APP_WORK_DIR', '../work')

@route('/')
def index():
    return template('lint.tpl')

@route('/files')
def files():
    return template('files.tpl', files=RESULT['files']) if RESULT else redirect('/')

@route('/matches')
def matches():
    return template('matches.tpl', matches=RESULT['matches']) if RESULT else redirect('/')

@route('/analysis-filetype-summary')
def analysis_filetype_summary():
    return template('filetype_summary.tpl', summary=filetype_summary(RESULT)) if RESULT else redirect('/')

@route('/analysis-module-summary')
def analysis_module_summary():
    return template('module_summary.tpl', summary=module_summary(RESULT)) if RESULT else redirect('/')

@route('/analysis-dependency-graph')
def analysis_dependency_graph():
    dot_file = os.path.join(APP_WORK_DIR, 'dependency.dot')
    svg_file = os.path.join(APP_WORK_DIR, 'dependency.svg')
    generate_graphviz_dot_file(dot_file, RESULT)
    subprocess.run(['dot', '-Tsvg', dot_file, '-o', svg_file])
    with open(svg_file, 'rb') as svg:
        svg_data = svg.read()
    # Hack to insert an SVG in a template
    template_str = f'''% include("head.tpl")
<div class="container">
  <div class="row">
    {svg_data}
  </div>
</div>
    '''
    return template(template_str)

@route('/run', method='POST')
def run_ansible_lint():
    forms = request.forms
    repo_name = Downloader(APP_WORK_DIR, forms.get("clear_work_dir")).extract(forms.get("url"))

    global RESULT
    RESULT = execute_ansiblelint(['-v', repo_name], work_dir=APP_WORK_DIR)
    return redirect('/files' if RESULT else '/')

run(host='localhost', port=8080)