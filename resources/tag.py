from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas import TagSchema, TagAndItem
from models import TagModel, StoreModel, ItemModel
from db import db
from sqlalchemy.exc import SQLAlchemyError

blp = Blueprint("tags", __name__, description = "Operations on tags")

@blp.route("/store/<string:store_id>/tag")
class TagsInStore(MethodView):
  @blp.response(200, TagSchema(many = True))
  def get(self, store_id):
    store = StoreModel.query.get_or_404(store_id)
    return store.tags.all()

  @blp.arguments(TagSchema)
  @blp.response(201, TagSchema)
  def post(self, tag_data, store_id):
    # if TagModel.query.filter(TagModel.store_id == store_id, TagModel.name == tag_data["name"]).first():
    #   abort(500, message = "Tag with that name already existed in that store")
    tag = TagModel(**tag_data, store_id = store_id)
    try:
      db.session.add(tag)
      db.session.commit()
    except SQLAlchemyError as e:
      abort(500, message = str(e))

    return tag

@blp.route("/tag/<string:tag_id>")
class Tag(MethodView):
  @blp.response(200, TagSchema)
  def get(self, tag_id):
    tag = TagModel.query.get_or_404(tag_id)
    return tag

  @blp.response(202, description="Delete a tag if no item is tagged with it", example = {"message":"tag deleted"})
  @blp.alt_response(404, description="Tag not fount")
  @blp.alt_response(
      400, 
      description="Returned if the tage is assgined to one or more items. In the case, the tag is not deleted"
    )
  def delete(self, tag_id):
    tag = TagModel.query.get_or_404(tag_id)

    if not tag.items:
      db.session.delete(tag)
      db.session.commit()
      return {"message":"Tag deleted"}


@blp.route("/item/<string:item_id>/tag/<string:tag_id>")
class LinkTagsToItem(MethodView):
  @blp.response(201, TagSchema)
  def post(self, item_id, tag_id):
    item = ItemModel.query.get_or_404(item_id)
    tag = TagModel.query.get_or_404(tag_id)
    if item.store_id != tag.store_id:
      abort(400, message = "Item and tag do not belong to the same store")

    item.tags.append(tag)

    try:
      db.session.add(item)
      db.session.commit()
    except SQLAlchemyError:
      abort(500, message = "Error occured")

    return tag

  class LinkTagsToItem(MethodView):
    @blp.response(200, TagAndItem)
    def delete(self, item_id, tag_id):
      item = ItemModel.query.get_or_404(item_id)
      tag = TagModel.query.get_or_404(tag_id)

      item.tags.remove(tag)

      try:
        db.session.add(item)
        db.session.commit()
      except SQLAlchemyError:
        abort(500, message = "Error occured")

      return {"message":"Item removed from tag", "item":item, "tag":tag}