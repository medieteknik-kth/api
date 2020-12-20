from api.db import db

from flask import jsonify, request
from flask_restful import Resource

from api.models.page import Page, PageRevision, PageRevisionType
from api.resources.authentication import requires_auth

from slugify import slugify

class PageResource(Resource):
    def get(self, id):
        if id.isnumeric():
            page = Page.query.get(id)
        else:
            page = Page.query.filter(Page.slug==id).first_or_404()

        return jsonify(page.to_dict())
    
    @requires_auth
    def put(self, user, id):
        """
        Edits a page with id.
        ---
        tags:
            - Pages
        security:
            - authenticated: []
        parameters:
        - name: id
          in: query
          schema:
            type: integer
        - name: page
          in: body
          schema:
            type: object
            properties:
              title:
                type: string
              content_sv:
                type: string
              content_en:
                type: string
              published:
                type: boolean
        responses:
            200:
                description: OK
            400:
                description: Missing authentication token
            402:
                description: Not authenticated
        """

        page = Page.query.get(id)

        if user.is_admin or page.is_editable_by(user):
            revision = PageRevision()
            revision.revision_type = PageRevisionType.edited
            revision.author = user
            
            if not request.is_json:
                return {
                    "message": "Invalid request"
                }, 400

            keys = request.json.keys()
            if "title" in keys:
                revision.title = request.json["title"]
            if "content_sv" in keys:
                revision.content_sv = request.json["content_sv"]
            if "content_en" in keys:
                revision.content_en = request.json["content_en"]
            if "image" in keys:
                revision.image = request.json["image"]
            if "published" in keys:
                revision.published = request.json["published"]

            page.revisions.append(revision)

            db.session.add(revision)
            db.session.commit()
            return jsonify({"message": "OK"})
        else:
            return {
                "message": "Invalid user"
            }, 401
    
    @requires_auth
    def delete(self, id, user):
        """
        Deletes a page with id.
        ---
        tags:
            - Pages
        security:
            - authenticated: []
        parameters:
        - name: id
          in: query
          schema:
            type: integer
        responses:
            200:
                description: OK
            400:
                description: Missing authentication token
            402:
                description: Not authenticated
        """
        page = Page.query.id(id)
        revision = PageRevision()
        revision.revision_type = PageRevisionType.removed

        page.revisions.append(revision)
        db.session.add(revision)
        db.session.commit()
        return jsonify({message: "OK"})


class PageListResource(Resource):
    def get(self):
        """
        Returns a list of all pages.
        ---
        tags:
            - Pages
        responses:
            200:
                description: OK
        """
        pages = Page.query.all()
        data = [page.to_dict() for page in pages]
        return jsonify(data)
    
    @requires_auth
    def post(self, user):
        """
        Creates a new page with optional content.
        ---
        tags:
            - Pages
        security:
            - authenticated: []
        parameters:
        - name: page
          in: body
          schema:
            type: object
            properties:
              title:
                type: string
              content:
                type: string
              published:
                type: boolean
        responses:
            200:
                description: OK
            400:
                description: Missing authentication token
            402:
                description: Not authenticated
        """
        page = Page()
        revision = PageRevision()
        revision.revision_type = PageRevisionType.created
        revision.author = user

        keys = request.json.keys()
        
        if "title" in keys:
            revision.title = request.json["title"]
            page.slug = slugify(request.json["title"])
        if "content_sv" in keys:
            revision.content_sv = request.json["content_sv"]
        if "content_en" in keys:
            revision.content_en = request.json["content_en"]
        if "image" in keys:
            revision.image = request.json["image"]
        if "published" in keys:
            revision.published = request.json["published"]

        page.revisions.append(revision)

        db.session.add(revision)
        db.session.add(page)
        db.session.commit()
        return jsonify({"id": page.id})