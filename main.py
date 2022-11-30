from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/portfolio')
def port():
    return render_template('portfolio.html')


@app.route('/sv')
def sv_one():
    style = 'style.scc'
    score = 0
    return render_template('index_main.html', style=style, sc=score)


if __name__ == '__main__':
    app.run(debug=True)

