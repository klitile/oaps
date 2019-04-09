from app import db


class Article(db.Model):
    __tablename__ = 'article'
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.Text)
    user_id = db.Column(db.Text,db.ForeignKey('user.id'))
    subject_id = db.Column(db.Integer,db.ForeignKey('subject.id'))
    abstract = db.Column(db.Text)
    highlight_part = db.Column(db.Text)
    postTime = db.Column(db.Text)
    accessNum = db.Column(db.Integer,default=0)
    commentNum = db.Column(db.Integer,default=0)
    upvoteNum = db.Column(db.Integer,default=0)
    downvoteNum = db.Column(db.Integer,default=0)
    hided = db.Column(db.Integer,default=0)
    dl_link = db.Column(db.Text)
    comments = db.relationship('Comment')
    user = db.relationship('User', lazy='subquery')



    def __str__(self):
        return self.title+' '+str(self.postTime)


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey('user.id'))
    email = db.Column(db.Text)
    article_id = db.Column(db.Integer,db.ForeignKey('article.id'))
    content = db.Column(db.Text)
    score = 0
    postTime = db.Column(db.Text)
    accessNum = db.Column(db.Integer,default=0)
    commentNum = db.Column(db.Integer,default=0)
    upvoteNum = db.Column(db.Integer,default=0)
    downvoteNum = db.Column(db.Integer,default=0)


class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    articles = db.relationship('Article')

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text)
    articles = db.relationship('Article')
    comments = db.relationship('Comment')


#拉黑，是否点过赞
class IP(db.Model):#id和addr有什么不一样？
    __tablename__ = 'ip'
    id = db.Column(db.Integer, primary_key=True)
    addr = db.Column(db.Text)
    is_blocked = db.Column(db.Integer,default=0)


class CommentIp(db.Model):
    __tablename__ = 'comment_ip'
    ip_id = db.Column(db.Integer,primary_key=True)
    comment_id = db.Column(db.Integer,db.ForeignKey('comment.id'),primary_key=True)
    vote_state = db.Column(db.Integer,default=0)


class ArticleIp(db.Model):
    __tablename__ = 'article_ip'
    ip_id = db.Column(db.Integer, primary_key=True)#是否可以不用加外键
    article_id = db.Column(db.Integer,db.ForeignKey('article.id'),primary_key=True)
    vote_state = db.Column(db.Integer, default=0)

class Password(db.Model):
    __tablename__ = 'password'
    id = db.Column(db.Integer,primary_key=True)
    psw  = db.Column(db.Text)


if __name__ == "__main__":
    db.drop_all()
    db.create_all()