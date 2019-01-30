import os
from configparser import ConfigParser

from sanic import Sanic
from sanic import response
from sanic_session import Session
from sanic_jinja2 import SanicJinja2
from sanic.exceptions import NotFound


LESSON_ROOT = os.environ.get('LESSON_ROOT')
if not LESSON_ROOT:
    raise ValueError('$LESSON_ROOT not set')

if not os.path.exists(LESSON_ROOT):
    raise ValueError('$LESSON_ROOT {}')

app = Sanic()
Session(app)

jinja = SanicJinja2(app)
#
# Specify the package name, if templates/ dir is inside module
# jinja = SanicJinja2(app, pkg_name='sanicapp')
# or use customized templates path
# jinja = SanicJinja2(app, pkg_name='sanicapp', pkg_path='other/templates')
# or setup later
# jinja = SanicJinja2()
# jinja.init_app(app)

@app.route('/')
@jinja.template('index.html')  # decorator method is staticmethod
async def index(request):
    request['flash']('success message', 'success')
    request['flash']('info message', 'info')
    request['flash']('warning message', 'warning')
    request['flash']('error message', 'error')
    return {'greetings': 'Hello, sanic!'}

@app.route('/lesson/<lesson>/download/images/<vendor>/<filename>')
async def download_image(request, lesson, vendor, filename):

    lesson_dir = os.path.join(LESSON_ROOT, lesson)
    if not os.path.exists(lesson_dir):
        raise NotFound('Lession {} does not exist'.format(lesson))

    download_fn = os.path.join(lesson_dir, 'images', vendor, filename)
    if not os.path.exists(download_fn):
        raise NotFound('Download filename {} does not exist'.format(download_fn))
    return await response.file(download_fn)

@app.route('/lesson/<lesson>/download/<filename>')
async def download_pdf(request, lesson, filename):

    lesson_dir = os.path.join(LESSON_ROOT, lesson)
    if not os.path.exists(lesson_dir):
        raise NotFound('Lession {} does not exist'.format(lesson))

    download_fn = os.path.join(lesson_dir, filename)
    if not os.path.exists(download_fn):
        raise NotFound('Download filename {} does not exist'.format(download_fn))
    return await response.file(download_fn)


@app.route('/lesson/<lesson>')
@jinja.template('lesson.html')  # decorator method is staticmethod
async def index(request, lesson):
    lesson_dir = os.path.join(LESSON_ROOT, lesson)
    if not os.path.exists(lesson_dir):
        raise NotFound('Lession {} does not exist'.format(lesson))
    print(lesson)

    conversion_ini = os.path.join(lesson_dir, 'conversion.ini')
    readme_fn = os.path.join(lesson_dir, 'README.rst')
    readme = None
    if os.path.exists(readme_fn):
        readme = open(readme_fn).read()

    pdfs = list()
    comp = dict()
    mode = 'html'
    category = 'intro'
    if os.path.exists(conversion_ini):
        CP = ConfigParser()
        CP.read(conversion_ini)
        if CP.has_option('common', 'mode'):
            mode = CP.get('common', 'mode')
        if CP.has_option('common', 'category'):
            category = CP.get('common', 'category')

        for section in CP.sections():
            if section not in ('PDFreactor', 'PrinceXML', 'Vivliostyle', 'Antennahouse'):
                continue

            pdf_file = CP.get(section, 'pdf')
            status = CP.get(section, 'status')
            message = CP.get(section, 'message')

            generated_pdf = os.path.join(lesson_dir, pdf_file)
            if not os.path.exists(generated_pdf):
                print('--> No PDF file {}'.format(generated_pdf))

            image_directory  = os.path.join(lesson_dir, 'images', section.lower())
            images = []
            if os.path.exists(image_directory):
                images = sorted(os.listdir(image_directory))
                if not images:
                    print('--> No images found in {}'.format(image_directory))
                images = [image for image in images if not image.startswith('thumb-')]

            pdfs.append(dict(name=section, pdf_file=pdf_file, status=status, message=message, images=images))
            comp[section] = dict(name=section, pdf_file=pdf_file, status=status, message=message)

        has_css = os.path.exists(os.path.join(lesson_dir, 'styles.css'))

        params = dict(
            name=lesson,
            pdfs=pdfs,
            has_css=has_css,
            mode=mode
            )

    return dict(params=params) 

if __name__ == '__main__':
    app.static('/static', './static')
    app.run(host='0.0.0.0', port=8000, debug=True)