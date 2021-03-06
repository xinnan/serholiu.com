#!/usr/bin/env python
# -*- coding: utf-8 -*-


class UserMixin(object):

    def get_user_by_id(self, id):
        user = self.db.get("SELECT * FROM users WHERE id = ?", int(id))
        return user

    def get_user_by_email(self, email):
        user = self.db.get("SELECT * FROM users WHERE email = ?", email)
        return user

    def update_user_salt(self, id, salt):
        user = self.get_user_by_id(id)
        if not user:
            return False
        self.db.execute("UPDATE users SET salt=? WHERE id=?;", salt, id)
        return True


class PostMixin(object):

    def get_post_by_id(self, id):
        post = self.db.get("SELECT * FROM posts WHERE id = ?", id)
        return post

    def get_post_by_slug(self, slug):
        post = self.db.get("SELECT * FROM posts WHERE slug = ?", slug)
        return post

    def get_posts_by_tag(self, tag):
        sql = """SELECT p.slug, p.title, p.published FROM posts AS p 
                   INNER JOIN tags AS t 
                   ON p.id = t.post_id 
                   WHERE t.name = ? 
                   ORDER BY p.published desc;
              """
        posts = self.db.query(sql, tag)
        return posts

    def get_posts_by_category(self, category):
        sql = """SELECT slug, title, published FROM posts
                 WHERE category = ?
                 ORDER BY published desc;
              """
        posts = self.db.query(sql, category)
        return posts

    def get_count_posts(self, count=None):
        if count:
            posts = self.db.query("SELECT * FROM posts ORDER BY published "
                                "DESC LIMIT ?;",count)
        else:
            posts = self.db.query("SELECT slug,title,published FROM posts ORDER BY published DESC;")
        return posts

    def create_new_post(self, **post):
        while 1:
            p = self.get_post_by_slug(post["slug"])
            if not p: break
            post["slug"] += "-2"

        sql = """INSERT INTO posts (title,slug,content,tags,category,published,comment)
                 VALUES (?,?,?,?,?,?,?);
              """
        post_id = self.db.execute(sql, post["title"], post["slug"], post["content"],
                              post["tags"], post["category"], post["published"], post['comment'])
        if post_id:
            tags = [tag.strip() for tag in post["tags"].split(",")]
            for tag in tags:
                self.db.execute("INSERT INTO tags (name,post_id) VALUES (?,?);", tag, post_id)
        return post_id

    def update_post_by_id(self, id, **post):
        sql = """UPDATE posts SET title=?,slug=?,content=?,tags=?,category=?,
                 published=?,comment=? WHERE id=?;
              """
        p = self.get_post_by_id(id)
        if p.tags != post["tags"]:
            has_new_tag = True
        else:
            has_new_tag = False
        self.db.execute(sql, post["title"], post["slug"], post["content"],
                     post["tags"], post["category"], post["published"],
                     post['comment'], id)
        if has_new_tag:
            new_tags = [tag.strip() for tag in post["tags"].split(",")]
            self.db.execute("DELETE FROM tags WHERE post_id=?;", id)
            for tag in new_tags:
                self.db.execute("INSERT INTO tags (name,post_id) VALUES (?,?);", tag, id)
        return True

    def delete_post_by_id(self, id):
        self.db.execute("DELETE FROM posts WHERE id=?;", id)
        self.db.execute("DELETE FROM tags WHERE post_id=?;", id)
        return True


    def get_next_prev_post(self, id):
        next = id + 1
        prev = id - 1
        count = 0
        while 1:
            next_post = self.db.get("SELECT slug,title FROM posts WHERE id=?;", next)
            if next_post: break
            # 100 是一估计量，当你发布文章又删除，造成 id 不连续，
            # 如果之间差值大过100,就无法得到正确结果
            if count > 100:
                next_post = None
                break
            next += 1
            count += 1

        while 1:
            if prev == 0:
                prev_post = None
                break
            prev_post = self.db.get("SELECT slug,title FROM posts WHERE id=?;", prev)
            if prev_post:
                break
            prev -= 1

        return {"next": next_post, "prev": prev_post}


class TagMixin(object):

    def get_all_tag_count(self, number=None):
        if number:
            sql = """SELECT name, COUNT(name) AS num FROM tags
                     GROUP BY name ORDER BY num DESC LIMIT ?;
                  """
            tags = self.db.query(sql, number)
        else:
            sql = """SELECT name, COUNT(name) AS num FROM tags
                     GROUP BY name ORDER BY num DESC;
                  """
            tags = self.db.query(sql)
        
        return tags
