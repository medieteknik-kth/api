from flask import jsonify, session, request, make_response
from flask_restful import Resource
from sqlalchemy import or_, and_, cast
from datetime import datetime
import json

from api.db import db

from sqlalchemy import and_, exc
from api.models.post import Post
from api.models.post_tag import PostTag
from api.models.user import User
from api.models.committee import Committee
from api.resources.authentication import requires_auth
from api.utility.storage import upload_b64_image

import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict
import uuid

from api.resources.common import parseBoolean

SAVE_FOLDER = os.path.join(os.getcwd(), "api", "static", "posts")
IMAGE_PATH = "static/posts/"
IMAGE_COL = "header_image"
ISO_DATE_DEF = "%Y-%m-%dT%H:%M:%S.%fZ"

class PostResource(Resource):
    def get(self, id):
        """
        Returns a post by id.
        ---
        tags:
            - Posts
        parameters:
        - name: id
          in: query
          schema:
            type: integer
        responses:
            200:
                description: OK
        """   
        post = Post.query.get_or_404(id)
        return jsonify(post.to_dict())

    @requires_auth
    def put(self, id, user):
        """
        Edits a post by id.
        ---
        tags:
            - Posts
        security:
            - authenticated: []
        parameters:
        - name: id
          in: query
          schema:
            type: integer
        - name: post
          in: body
          schema:
            type: object
            properties:
              committee_id:
                type: number   
              header_image:
                type: string
                format: binary
              title:
                type: string
              title_en:
                type: string
              body:
                type: string
              body_en:
                type: string
              scheduled_date:
                type: string
                format: date-time
              draft:
                type: boolean
              tags:
                type: array
                items:
                    type: integer
        responses:
            200:
                description: OK
            400:
                description: Missing authentication token
            401:
                description: Not authenticated
            404:
                description: Did not find post with id
        """
        post = Post.query.get_or_404(id)
        post_user = (user.id == post.user_id)

        committee_member = False
        if(not post_user): 
            for post_term in user.post_terms:
                if((post_term.post.committee_id == post.committee_id) and (post_term.start_date < datetime.today() < post_term.end_date)):
                    committee_member = True
        data = request.json

        if user.is_admin or post_user or committee_member:
            if data.get("title"):
              title = data.get("title")
              if title.get('se'):
                post.title = title.get('se')
              if title.get('en'):
                post.title_en = title.get('en')
            if data.get("body"):
              body = data.get("body")
              if body.get('se'):
                post.body = body.get('se')
              if title.get('en'):
                post.body_en = body.get('en')
            if data.get('date'):
              post.date = data.get('date')
            if data.get('scheduled_date'):
              post.scheduled_date = data.get('scheduled_date')
            if data.get('draft'):
              post.draft = data.get('draft')
            if data.get('header_image'):
              post.header_image = upload_b64_image(data.get('header_image'))
            if data.get('committee_id'):
              post.committee_id = data.get('committee_id')
            if data.get('tags'):
              post.tags = data.get('tags')
            
            db.session.commit()
            return make_response(jsonify(success=True))
        else:
            return make_response(jsonify(success=False, error=str(error)), 401)
    
    @requires_auth
    def delete(self, id, user):
        post = Post.query.get_or_404(id)
        db.session.delete(post)
        db.session.commit()
        return jsonify({"message": "ok"})
        
class PostListResource(Resource): 
    def get(self):
        """
        Returns a list of all posts.
        ---
        tags:
            - Posts
        responses:
            200:
                description: OK
        """
        show_unpublished = request.args.get('showUnpublished', False, type=bool)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('perPage', 20, type=int)

        data = []
        total_count = 0

        ## TODO: Only show unpublished if logged in
        if show_unpublished:
          posts = Post.query.order_by(Post.date.desc()).paginate(page=page, per_page=per_page)
          data = [post.to_dict() for post in posts.items]
          total_count = posts.total
        else:
          scheduled_condition = [Post.scheduled_date <= datetime.now(), Post.scheduled_date == None]
          posts = Post.query.filter(
            and_(
              Post.draft == False,
              or_(*scheduled_condition)
            )).order_by(
              Post.scheduled_date.desc(),
              Post.date.desc()
            ).paginate(page=page, per_page=per_page)
          data = [post.to_dict() for post in posts.items]
          total_count = posts.total
        return jsonify({"data": data, "totalCount": total_count})
    
    @requires_auth
    def post(self, user):
        """
        Adds a new post.
        ---
        tags:
            - Posts
        security:
            - authenticated: []
        parameters:
        - name: id
          in: query
          schema:
            type: integer
        - name: post
          in: body
          schema:
            type: object
            properties:
              committee_id:
                type: number   
              header_image:
                type: string
                format: binary
              title:
                type: string
              title_en:
                type: string
              body:
                type: string
              body_en:
                type: string
              scheduled_date:
                type: string
                format: date-time
              draft:
                type: boolean
              tags:
                type: array
                items:
                    type: integer
        responses:
            200:
                description: OK
            400:
                description: Missing authentication token
            402:
                description: Not authenticated
        """
        data = request.json

        if user.id:
            post = Post()
            post.user_id = user.id

            if data.get("title"):
              title = data.get("title")
              if title.get('se'):
                post.title = title.get('se')
              if title.get('en'):
                post.title_en = title.get('en')
            if data.get("body"):
              body = data.get("body")
              if body.get('se'):
                post.body = body.get('se')
              if title.get('en'):
                post.body_en = body.get('en')
            if data.get('date'):
              post.date = data.get('date')
            if data.get('scheduled_date'):
              post.scheduled_date = data.get('scheduled_date')
            if data.get('draft'):
              post.draft = data.get('draft')
            if data.get('header_image'):
              post.header_image = upload_b64_image(data.get('header_image'))
            if data.get('committee_id'):
              post.committee_id = data.get('committee_id')
            if data.get('tags'):
              post.tags = data.get('tags')

            db.session.add(post)
            db.session.commit()
            return make_response(jsonify(success=True, id=post.id))
        else:
            return make_response(jsonify(success=False, error=str(error)), 403)

def parseBoolean(string):
    d = {'true': True, 'false': False}
    return d.get(string, string)

def add_cols(data, post, request):
    dynamic_cols = ["committee_id", "title", "body", "title_en", "body_en"]
    date_cols = ["scheduled_date"]
    boolean_cols = ["draft"]

    for col in dynamic_cols: 
        if data.get(col):
            setattr(post, col, data.get(col))

    for col in date_cols: 
      if data.get(col):
          setattr(post, col, datetime.strptime(data.get(col), ISO_DATE_DEF))

    for col in boolean_cols: 
      if data.get(col):
          setattr(post, col, parseBoolean(data.get(col)))

    if IMAGE_COL in request.files:
        image = request.files[IMAGE_COL]
        post.header_image = upload_image(image)
    
    if data.get("tags"):
        tags = json.loads(data["tags"])
        for tag_id in tags:
            post.tags.append(PostTag.query.get(tag_id))


def save_image(image, path):
    local_path = ""
    ALLOWED_EXTENTIONS = [".png", ".jpg", ".jpeg"]
    original_filename, extension = os.path.splitext(secure_filename(image.filename))
    filename = str(uuid.uuid4()) + extension
    if extension in ALLOWED_EXTENTIONS:
        path = os.path.join(path, filename)
        local_path = os.path.join(SAVE_FOLDER, filename)
        image.save(local_path)
        return path
    else:
        raise "you can only upload .png or .jpg-files."