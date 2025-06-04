from flask import Flask, render_template
import sqlite3

app = Flask(__name__)


# 路由解析：通过用户访问的路径，匹配相应函数
@app.route('/')
def index():
    return render_template("index.html")


# 返回首页
@app.route('/index')
def home():
    return render_template("index.html")

# 热力图
@app.route('/hotmap')
def hotmap():
    return render_template("hotmap.html")

# 产品交易折柱图
@app.route('/trade')
def trade():
    return render_template("trade.html")

# 交易商饼状图
@app.route('/piemap')
def piemap():
    return render_template("piemap.html")

# 最大回撤率轮播图
@app.route('/wheel')
def wheel():
    return render_template("wheel.html")

# 交易喜好正负柱状图
@app.route('/like')
def like():
    return render_template("like.html")


if __name__ == '__main__':
    app.run(debug=True)