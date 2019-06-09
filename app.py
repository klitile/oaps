from datetime import time, datetime
import time
import smtplib
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import re
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
      default_limits=[]
)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI']  = 'sqlite:///shcool.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['MAX_CONTENT_LENGTH'] = 0.1 * 1024 * 1024
app.config['DEBUG'] = True

db = SQLAlchemy(app)
from model import *
from services import *

# 初始化db,并创建models中定义的表格
with app.app_context(): # 添加这一句，否则会报数据库找不到application和context错误
     db.init_app(app) # 初始化db
     db.create_all() # 创建所有未创建的table


@app.before_request
def before_request():
    addr = request.remote_addr
    ip = ipService.find_ip_by_ip(addr)
    if ip is None:
        ip = IP(addr=addr, is_blocked=0)
        ipService.insert(ip)
    elif ip.is_blocked == 1:
        os.abort(403)
'''
    导航栏：首页、发表文章
    关于主题：首页显示所有主题名称及增加主题功能
'''
def getelem(elem): return elem.title
@app.route('/')
def home():
    subjects = subjectService.find_all_subject()
    subjects.sort( key = getelem ,reverse=False)
    return render_template('home.html',subjects=subjects)

'''
    主题页面显示热门文章
'''
@app.route('/subject/<subject_id>')
def subject(subject_id):
    subject = subjectService.find_by_id(subject_id)
    articles = articleService.find_by_subject(subject.id)
    articles.reverse()
    particles = []
    for article in articles:
        if article.hided == 1:
            articles.remove(article)
            continue
        article.score=articleService.calPopularity(article)
        if article.score>=0.3 :
            particles.append(article)
    particles.sort(key=lambda item: item.score, reverse=True)
    return render_template('subject.html',subject=subject,articles = articles,particles=particles)

'''
    创建主题
'''
@app.route('/create_subject_page')
def create_subject():
    return render_template('create_subject.html')

sensitive_words = []
with open('sensitive_word.txt', 'r') as f:
    words = f.readlines()
    for word in words:
        sensitive_words.append(word.replace('\n', ''))

'''
    增加主题
'''
@app.route('/add_subject',methods=['POST'])
def add_subject():
    form = request.form
    title = form['title'].title()
    upperTitle = title.upper()
    for word in sensitive_words: #change all words to uppercase then check if their letter is same
        word = word.upper()
        print(word)
        print(title)
        if word in upperTitle:
            return 'contain inappropriate word(s)'
    subject = subjectService.find_by_title(title)
    if subject:
        return 'Subject has existed!<a href="/">back to home</a>'
    subject = Subject(title=title,description=form['description'])
    subjectService.insert(subject)
    return redirect('/')



'''
    进入文章发表页面
'''

@app.route('/post')
def postPage():
    return render_template('post.html')


# 处理邮件地址
def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


'''
    处理文章上传
'''
@app.route('/upload', methods=['POST'])
@limiter.limit("2 per minute")
def upload():
    form = request.form
    for blank in form:
        if form[blank]=='': return "Blank can't be empty!"
    if re.match(r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$',form['email']) == None:
        return "Wrong email address format!"
    file = request.files['pdf'].read()
    filename = request.files['pdf'].filename
    split = filename.split('.')
    if len(split) != 2 or split[1] != 'pdf':
        return 'unsupported file type'
    for content in form:
        #print(content)
        if content=='pdf':continue
        for word in sensitive_words:
            if word in form[content]:
                return 'contain inappropriate word(s)'
    filename = request.files['pdf'].filename
    email = form['email']
    user = userService.find_by_email(email)
    if user is None:
        user = User(email=email)
        userService.insert(user)
    #判断是否被拉黑

    subject = subjectService.find_by_title(form['subject'])
    if subject is None:
        return '<h2>There is no such subject, ' \
               'please create the subject first.</h2><a href="/">back to home</a>'

    #验证码
    nextid = articleService.nextId()
    article = Article(title=form['title'],
                      postTime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                      abstract=form['abstract'],
                      highlight_part=form['highlight'],
                      subject_id=subject.id,
                      user_id=user.id,
                      dl_link="static/"+str(nextid)+".pdf")
    articleService.insert(article)
    new_filename = "static/"+str(nextid)+".pdf"
    # 存储文件到本地
    newFile = open(new_filename,"wb")
    newFile.write(file)
    newFile.close()
    # 发送邮件
    msg = MIMEText('hanks for posting article.If you are sure that you haven\'t post any articles in OAPS, please contact <a href="mailto:2912607882@qq.com">2912607882@qq.com</a> to delete it.', 'html', 'utf-8')
    msg['From'] = _format_addr('2912607882@qq.com')
    msg['To'] = _format_addr(email)
    msg['Subject'] = Header('[OAPS]', 'utf-8').encode()
    server = smtplib.SMTP('smtp.qq.com', 25)
    server.set_debuglevel(1)
    server.login('2912607882@qq.com', '***') # TODO 输入密码
    server.sendmail('2912607882@qq.com', [email], msg.as_string())
    server.quit()
    return redirect('/article/' + str(article.id))

'''
    显示文章细节信息
'''
@app.route('/article/<article_id>')
def article(article_id):
    article = articleService.find_by_id(article_id)
    user = userService.find_by_id(article.user_id)
    ip = ipService.find_ip_by_ip(request.remote_addr)
    aip = ipService.find_aip_both(article_id,ip.id)
    comments = commentService.find_by_articleid(article_id)
    comments.reverse()
    if aip is None:#第一次访问
        aip = ArticleIp(ip_id=ip.id,article_id=article_id,vote_state=0)
        ipService.insert(aip)
        articleService.addAccess(article)
    return render_template('article.html',article = article,user=user,comments=comments,flag=0)

@app.route('/manage/article/<article_id>')
def manage_article(article_id):
    article = articleService.find_by_id(article_id)
    user = userService.find_by_id(article.user_id)
    ip = ipService.find_ip_by_ip(request.remote_addr)
    aip = ipService.find_aip_both(article_id,ip.id)
    comments = commentService.find_by_articleid(article_id)
    comments.reverse()
    if aip is None:#第一次访问
        aip = ArticleIp(ip_id=ip.id,article_id=article_id,vote_state=0)
        ipService.insert(aip)
        articleService.addAccess(article)
    return render_template('article.html',article = article,user=user,comments=comments,flag=1)
'''
    文章点赞
'''
@app.route('/upvote/<article_id>')
def article_upvote(article_id):
    ip = ipService.find_ip_by_ip(request.remote_addr)
    articleService.upvote(article_id,ip.id)
    return 'vote successfully!'
'''
    文章差评
'''
@app.route('/downvote/<article_id>')
def article_downvote(article_id):
    ip = ipService.find_ip_by_ip(request.remote_addr)
    articleService.downvote(article_id, ip.id)
    return 'vote successfully!'
'''
    文章评论
'''
@app.route('/<article_id>/comment',methods=['POST'])
@limiter.limit("2 per minute")
def article_comment(article_id):
    article = articleService.find_by_id(article_id)
    form = request.form
    email = form['email']
    for content in form:
        for word in sensitive_words:
            if word in form[content]:
                return 'contain inappropriate word(s)'
    user = userService.find_by_email(email)
    if user is None:
        user = User(email=email)
    comment = Comment(user_id=user.id,email=email,article_id=article_id,content=form['content'],postTime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    commentService.insert(comment)
    articleService.addComment(article)
    ip = ipService.find_ip_by_ip(request.remote_addr)
    cip = ipService.find_cip_by_both(comment.id,ip.id)
    if cip is None:
        ipService.insert(CommentIp(ip_id=ip.id,comment_id=comment.id,vote_state=0))
    return redirect('/article/' + article_id)

@app.route('/cupvote/<comment_id>')
def cupvote(comment_id):
    ip = ipService.find_ip_by_ip(request.remote_addr)
    commentService.upvote(comment_id, ip.id)
    return 'vote successfully!'

@app.route('/cdownvote/<comment_id>')
def cdownvote(comment_id):
    ip = ipService.find_ip_by_ip(request.remote_addr)
    commentService.downvote(comment_id, ip.id)
    return 'vote successfully!'

'''
    作者页面
'''
@app.route('/author',methods=['POST'])
def author_find():
    form = request.form
    email = form['email']
    user = userService.find_by_email(email)
    if user is None:
        return "Author doesn't exist~!"
    articles = articleService.find_by_user(user.id)
    for article in articles:
        article.score=articleService.calPopularity(article)
        if article.hided==1:
            articles.remove(article)
            continue
    comments = commentService.find_by_userid(user.id)
    return render_template('author.html',user=user,articles=articles,comments=comments)

'''
    搜索页面
'''
@app.route('/search')
def search():
    content = request.args['content']
    articles = articleService.search(content)
    #print(articles.size())
    comments = commentService.search(content)
    return render_template('search_result.html',articles=articles,comments=comments)


@app.route('/donate')
def donate():
    return render_template('donate.html')

'''
    管理员页面
'''
@app.route('/manage')
def manage():
    return render_template('manage.html')

@app.route('/psw_change',methods=['POST'])
def psw_manage():
    form = request.form
    psw = passwordService.get_password()
    oldpsw = form['old']
    if oldpsw!=psw.psw: return "wrong old password!"
    psw.psw = form['new']
    passwordService.change(psw)
    return render_template('manage.html')

@app.route('/hide_article',methods=['POST'])
def hide_article():
    form= request.form
    psw = passwordService.get_password()
    aid = form['aid']
    input_psw = form['psw']
    if(input_psw!=psw.psw): return "wrong password!"
    article = articleService.find_by_id(int(aid))
    if article.hided == 1:article.hided=0
    else: article.hided =1
    articleService.commit()
    return render_template('manage.html')

@app.route('/delete_article',methods=['POST'])
def delet_article():
    form = request.form
    psw = passwordService.get_password()
    aid = form['aid']
    input_psw = form['psw']
    if(input_psw!=psw.psw): return "Wrong password!"
    article = articleService.find_by_id(int(aid))
    if(article==None): return "Article doesn't exist!"
    articleService.delete(article)
    return render_template('manage.html')

@app.route('/manage/cdelete/<comment_id>',methods=['POST'])
def cdelete(comment_id):
    form = request.form
    psw = passwordService.get_password()
    input_psw = form['psw']
    if (input_psw != psw.psw): return "wrong password!"
    comment = commentService.find_by_id(comment_id)
    commentService.delete(comment)
    return redirect('/article/'+str(comment.article_id))


if __name__ == '__main__':
    app.run()
