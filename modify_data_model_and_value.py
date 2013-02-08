from google.appengine.api import users
from google.appengine.ext import db

class Product(db.Expando):
  pass


query = db.GqlQuery("SELECT * FROM Product");
data=query.fetch(query.count(limit=None));

for p in data:
  p.sell_price=float(p.sell_price/1000);
  p.root_price=float(p.root_price/1000);

#db.put(data);