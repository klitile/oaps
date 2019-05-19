from app import db
from model import *


class SubjectService:
    '''
        1.获取所有的主题
        2.通过主题的名称获取主题
        3.通过id获取主题
    '''
    def find_all_subject(self):
        subjects = Subject.query.all()
        return subjects

    def find_by_title(self,title):
        subjects = Subject.query.filter_by(title=title).first()
        return subjects

    def find_by_id(self,id):
        subject = Subject.query.filter_by(id=id).first()
        return subject

    def insert(self,subject):
        db.session.add(subject)
        db.session.commit()

class ArticleService:
    def commit(self):
        db.session.commit()

    def delete(self,article):
        db.session.delete(article)
        db.session.commit()

    def calPopularity(self,article):
        return article.upvoteNum/max((article.upvoteNum+article.downvoteNum),1)*(article.accessNum*0.3+article.commentNum*0.7)

    def addAccess(self,article):
        article.accessNum+=1
        db.session.commit()

    def addComment(self,article):
        article.commentNum+=1
        db.session.commit()

    def find_all_article(self):
        articles = Article.query.all()
        return articles

    def find_by_title(self,title):
        article = Article.query.filter_by(title=title).first()
        return article

    def find_by_id(self,id):
        article = Article.query.filter_by(id=id).first()
        return article

    def find_by_subject(self,subject_id):
        articles = Article.query.filter_by(subject_id=subject_id).all()
        return articles

    # 考虑名称是否有用错
    def find_by_user(self,user_id):
        articles = Article.query.filter_by(user_id=user_id).all()
        return articles

    def insert(self,article):
        db.session.add(article)
        db.session.flush()
        db.session.commit()
        print("addArticle:"+str(article.id))
        return str(article.id)

    #返回当前最大id
    def nextId(self):
        return db.session.query(db.func.max(Article.id)).one()[0]+1

    #点赞,0-默认，1-点赞，2-差评
    def upvote(self,article_id,ip_id):
        aip = ipService.find_aip_both(article_id,ip_id)
        article = articleService.find_by_id(article_id)
        if aip.vote_state == 1:
            aip.vote_state = 0
            article.upvoteNum -= 1
        elif aip.vote_state == 0:
            aip.vote_state = 1
            article.upvoteNum += 1
        else:#原先是差评的情况
            aip.vote_state = 1
            article.upvoteNum += 1
            article.downvoteNum -= 1
        db.session.commit()

    def downvote(self,article_id,ip_id):
        aip = ipService.find_aip_both(article_id, ip_id)
        article = articleService.find_by_id(article_id)
        if aip.vote_state == 2:
            aip.vote_state = 0
            article.downvoteNum -= 1
        elif aip.vote_state == 0:
            aip.vote_state = 2
            article.downvoteNum += 1
        else:  # 原先是好评的情况
            aip.vote_state = 2
            article.upvoteNum -= 1
            article.downvoteNum += 1
        db.session.commit()

    def search(self, content):
        articles=[]
        articles.extend(Article.query.filter(Article.title.like('%%%s%%' % content)).all())
        articles.extend(Article.query.filter(Article.abstract.like('%%%s%%' % content)).all())
        articles.extend(Article.query.filter(Article.highlight_part.like('%%%s%%' % content)).all())
        rec=[]
        result=[]
        for article in articles: #remove the repeat articles
            if article.id not in rec:
                rec.append(article.id)
                result.append(article)

        return  result


class UserService:
    def find_by_id(self,user_id):
        user = User.query.filter_by(id=user_id).first()
        return user

    def find_by_email(self,email):
        user = User.query.filter_by(email=email).first()
        return user

    def insert(self,user):
        db.session.add(user)
        db.session.commit()


class IPService:
    def find_ip_by_ip(self,addr):
        ip = IP.query.filter_by(addr=addr).first()
        return ip

    def insert(self,ip):
        db.session.add(ip)
        db.session.commit()

    def find_aip_by_ipid(self,ip_id):
        aip = ArticleIp.query.filter_by(ip_id=ip_id).first()
        return aip

    def find_aip_both(self,article_id,ip_id):
        aip = ArticleIp.query.filter_by(article_id=article_id, ip_id=ip_id).first()
        return aip

    def find_cip_by_ipid(self,ip_id):
        cip = CommentIp.query.filter_by(ip_id=ip_id).first()
        return cip

    def find_cip_by_both(self,comment_id,ip_id):
        return CommentIp.query.filter_by(comment_id=comment_id,ip_id=ip_id).first()


class CommentService:
    def delete(self,comment):
        db.session.delete(comment)
        db.session.commit()

    def find_by_id(self,comment_id):
        return Comment.query.filter_by(id=comment_id).first()

    def find_by_articleid(self,article_id):
        return Comment.query.filter_by(article_id=article_id).all()
    def find_by_userid(self,user_id):
        return Comment.query.filter_by(user_id=user_id).all()

    def insert(self,comment):
        db.session.add(comment)
        db.session.commit()

    #点赞,0-默认，1-点赞，2-差评
    def upvote(self,comment_id,ip_id):
        cip = ipService.find_cip_by_both(comment_id,ip_id)
        comment = commentService.find_by_id(comment_id)
        if cip.vote_state == 1:
            cip.vote_state = 0
            comment.upvoteNum -= 1
        elif cip.vote_state == 0:
            cip.vote_state = 1
            comment.upvoteNum += 1
        else:#原先是差评的情况
            cip.vote_state = 1
            comment.upvoteNum += 1
            comment.downvoteNum -= 1
        db.session.commit()

    def downvote(self,comment_id,ip_id):
        cip = ipService.find_cip_by_both(comment_id, ip_id)
        comment = commentService.find_by_id(comment_id)
        if cip.vote_state == 2:
            cip.vote_state = 0
            comment.downvoteNum -= 1
        elif cip.vote_state == 0:
            cip.vote_state = 2
            comment.downvoteNum += 1
        else:  # 原先是好评的情况
            cip.vote_state = 2
            comment.upvoteNum -= 1
            comment.downvoteNum += 1
        db.session.commit()

    def search(self, content):
        return Comment.query.filter(Comment.content.like('%%%s%%' % content)).all()

class PasswordService:
    def change(self,password):
        db.session.commit()

    def get_password(self):
        return Password.query.first()

subjectService = SubjectService()
articleService = ArticleService()
userService = UserService()
ipService = IPService()
commentService = CommentService()
passwordService = PasswordService()